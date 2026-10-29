from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from sim.bots import (
    AccelerationistBot,
    AdaptiveBalancedBot,
    BaseBot,
    Phase3ActionPlan,
    RecklessSaboteurBot,
    SecOpsTurtleBot,
    VentureGreedBot,
)
from sim.config import CubeColor, DieColor, EndGameReason, GameConfig, ShieldColor
from sim.engine import EndGameResult, GameEngine, GameState, PlayerState
from sim.entities import (
    AbilityStatus,
    ArchetypeCard,
    ArchetypeCode,
    Die,
    VariantCard,
    VersionCard,
    create_colored_die,
    create_white_die,
)

if TYPE_CHECKING:
    from web.controller.core import GameController


def get_action_capabilities(controller: GameController, player_id: int) -> Dict[str, Any]:
    """Calculates valid action flags for the specified player given current state."""
    if player_id not in controller.player_meta or controller.engine is None:
        return {}

    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]
    is_active = (player_id == controller.active_player_index)
    is_eliminated = player.is_patient_zero

    # Available patch tokens: held tokens + any patches showing on kept unlocked rolled faces minus spent_from_kept
    kept_patches = 0
    if meta.get("rolled_pool"):
        locked = set(meta.get("locked_reroll_indices", []))
        for i, d in enumerate(meta["rolled_pool"]):
            if i not in locked and d.current_face and d.current_face.patches > 0:
                kept_patches += d.current_face.patches
    avail_patches = player.patches + max(0, kept_patches - meta.get("spent_from_kept", 0))

    can_roll = (controller.phase == 1 and not meta["has_rolled"] and not is_eliminated)
    already_hired = meta.get("hired_contractors", 0)
    max_contractors = controller.state.config.contractor_max_hire
    if already_hired < max_contractors:
        next_contractor_cost = controller.state.config.get_contractor_cost_for_hire(1, already_hired=already_hired)
    else:
        next_contractor_cost = None

    can_hire_contractors = (
        controller.phase == 1
        and not meta["has_rolled"]
        and not is_eliminated
        and already_hired < max_contractors
        and controller.state.contractor_supply > 0
        and next_contractor_cost is not None
        and player.money >= next_contractor_cost
    )
    active_ver = controller.state.active_version.version_str if (controller.state and controller.state.active_version) else None
    ability_avail = player.is_ability_available(active_ver) if active_ver else player.is_ability_available()

    # Consultancy Archetype Capabilities
    is_operator = bool(player.archetype and player.archetype.code == ArchetypeCode.OPERATOR)
    can_operator = bool(
        controller.phase == 1
        and not meta["has_rolled"]
        and not is_eliminated
        and is_operator
        and ability_avail
        and already_hired < max_contractors
        and controller.state.contractor_supply > 0
    )

    is_prodigy = bool(player.archetype and player.archetype.code == ArchetypeCode.PRODIGY)
    is_phreaker = bool(player.archetype and player.archetype.code == ArchetypeCode.PHREAKER)
    can_phreaker = bool(
        controller.phase == 3
        and is_active
        and not is_eliminated
        and is_phreaker
        and ability_avail
        and len(player.unpatched_dice) > 0
    )

    is_cipher = bool(player.archetype and player.archetype.code == ArchetypeCode.CIPHER)
    can_cipher_buy = {}
    for color in [DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW, DieColor.PURPLE]:
        base_cost = 4 if color in (DieColor.RED, DieColor.GREEN, DieColor.PURPLE) else 5
        disc_cost = max(0, base_cost - 2)
        can_cipher_buy[color.value] = bool(
            controller.phase == 3
            and is_active
            and not is_eliminated
            and is_cipher
            and ability_avail
            and meta["purchases_this_turn"] < controller.state.config.max_market_purchases_per_turn
            and controller.state.market.get(color, 0) > 0
            and player.money >= disc_cost
        )
    can_cipher_dirty = bool(
        controller.phase == 3
        and is_active
        and not is_eliminated
        and is_cipher
        and ability_avail
        and not meta["dirty_income_taken_this_turn"]
        and player.secrets > controller.state.config.dirty_income_secret_cost
    )

    is_acoustic = bool(player.archetype and player.archetype.code == ArchetypeCode.ACOUSTIC)
    can_acoustic = bool(
        not is_eliminated
        and is_acoustic
        and ability_avail
        and controller.last_compile_result is not None
        and any(
            controller.last_compile_result.get("exited_cubes", {}).get(c.value, 0) > 0
            for c in [CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN]
        )
    )

    is_spook = bool(player.archetype and player.archetype.code == ArchetypeCode.SPOOK)
    can_spook = bool(
        not is_eliminated
        and is_spook
        and ability_avail
        and controller.last_compile_result is not None
    )

    rolled_pool = meta.get("rolled_pool", [])
    can_prodigy = bool(
        controller.phase == 1
        and meta["has_rolled"]
        and not meta["has_committed"]
        and not is_eliminated
        and is_prodigy
        and (meta.get("prodigy_active", False) or ability_avail)
        and meta.get("rerolls_remaining", 0) > 0
        and len(rolled_pool) > 0
    )
    can_reroll = (
        controller.phase == 1
        and meta["has_rolled"]
        and not meta["has_committed"]
        and not is_eliminated
        and meta.get("rerolls_remaining", 0) > 0
        and (
            any(not getattr(d, "is_locked", False) for d in rolled_pool)
            or (is_prodigy and (meta.get("prodigy_active", False) or ability_avail) and len(rolled_pool) > 0)
        )
    )
    can_debug_unlock = (
        controller.phase == 1
        and meta["has_rolled"]
        and not meta["has_committed"]
        and not is_eliminated
        and player.patches > 0
        and any(getattr(d, "is_locked", False) for d in rolled_pool)
    )
    can_hotfix = (controller.phase == 1 and meta["has_rolled"] and not meta["has_committed"] and avail_patches > 0 and not is_eliminated)
    can_commit = (controller.phase == 1 and meta["has_rolled"] and not meta["has_committed"] and not is_eliminated)
    can_compile = (controller.phase == 2 and controller.subphase == "ready_for_compile")

    patch_cost = controller.state.config.patch_cash_cost
    can_patch_cash = (
        controller.phase == 3
        and is_active
        and not is_eliminated
        and len(player.unpatched_dice) > 0
        and player.money >= patch_cost
    )
    can_patch_token = (
        controller.phase == 3
        and is_active
        and not is_eliminated
        and len(player.unpatched_dice) > 0
        and player.patches >= controller.state.config.patch_token_cost
    )
    can_dirty = (
        controller.phase == 3
        and is_active
        and not is_eliminated
        and not meta["dirty_income_taken_this_turn"]
        and player.secrets > controller.state.config.dirty_income_secret_cost
        and len(player.ready_dice) >= 1
    )
    can_end_turn = (controller.phase == 3 and is_active and not is_eliminated)

    # Market purchase availability per color
    can_buy = {}
    for color in [DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW, DieColor.PURPLE]:
        cost = 4 if color in (DieColor.RED, DieColor.GREEN, DieColor.PURPLE) else 5
        can_buy[color.value] = (
            controller.phase == 3
            and is_active
            and not is_eliminated
            and meta["purchases_this_turn"] < controller.state.config.max_market_purchases_per_turn
            and controller.state.market.get(color, 0) > 0
            and player.money >= cost
        )

    # Star actions
    can_star = {
        "B2": bool(
            controller.phase == 3
            and is_active
            and player.b2_available
            and player.money >= controller.state.config.b2_secret_cost
            and player.secrets < controller.state.config.b2_secret_cap
        ),
        "Y1": bool(controller.phase == 3 and is_active and player.y1_available and player.money >= 6 and player.secrets < 10),
        "P1": bool(controller.phase == 3 and is_active and player.p1_available),
        "P3": bool(
            controller.phase == 3
            and is_active
            and player.p3_available is not None
            and player.money >= controller.state.config.p3_cube_cash_cost
        ),
    }

    return {
        "can_roll": can_roll,
        "can_hire_contractors": can_hire_contractors,
        "next_contractor_cost": next_contractor_cost,
        "can_reroll": can_reroll,
        "can_debug_unlock": can_debug_unlock,
        "can_hotfix": can_hotfix,
        "can_commit": can_commit,
        "can_compile": can_compile,
        "can_buy": can_buy,
        "can_patch_cash": can_patch_cash,
        "can_patch_token": can_patch_token,
        "can_dirty_income": can_dirty,
        "can_star": can_star,
        "can_end_turn": can_end_turn,
        # Archetype capabilities
        "can_operator": can_operator,
        "can_prodigy": can_prodigy,
        "can_phreaker": can_phreaker,
        "can_cipher_buy": can_cipher_buy,
        "can_cipher_dirty": can_cipher_dirty,
        "can_acoustic": can_acoustic,
        "can_spook": can_spook,
    }

