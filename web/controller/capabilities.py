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
from sim.entities import has_company_override, has_signature_protocol, legacy_bridge_enabled
from sim.entities import (
    AbilityStatus,
    ArchetypeCard,
    ArchetypeCode,
    CompanyCode,
    WhiteHatCode,
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

    # Company Institutional Overrides & Operative Protocol Capabilities
    is_operator = has_company_override(player, CompanyCode.MERIDIAN, legacy_bridge_enabled(controller))
    can_operator = bool(
        controller.phase == 1
        and not meta["has_rolled"]
        and not is_eliminated
        and is_operator
        and ability_avail
        and already_hired < max_contractors
        and controller.state.contractor_supply > 0
    )

    is_prodigy = has_company_override(player, CompanyCode.HELIX, legacy_bridge_enabled(controller))
    is_phreaker = has_company_override(player, CompanyCode.OMNIDYNE, legacy_bridge_enabled(controller))
    is_phreaker_white_hat = has_signature_protocol(player, WhiteHatCode.PHREAKER, legacy_bridge_enabled(controller))
    pending_grad = (getattr(controller, "pending_graduation", {}) or {}).get(player_id)
    # Omnidyne Magnetic Splice: Phase 5 step 1 (Emergency Hotfix & Magnetic Splice)
    can_phreaker = bool(
        controller.phase == 5
        and pending_grad is not None
        and not is_eliminated
        and is_phreaker
        and pending_grad.get("splice_available", False)
    )
    can_splice = can_phreaker
    can_hotfix_bypass = bool(controller.phase == 5 and pending_grad is not None and pending_grad.get("hotfix_available", False))
    can_choose_graduates = bool(controller.phase == 5 and controller.subphase == "choose_graduates" and pending_grad is not None)
    in_income = bool(
        controller.phase == 3 and controller.subphase == "confirm_income"
        and not meta.get("income_confirmed", False) and not is_eliminated
    )
    purple_in_prod = any(
        (d.effective_face or d.current_face) is not None
        and (d.effective_face or d.current_face).is_star
        and (d.effective_face or d.current_face).star_code == "PURPLE_STAR"
        for d in player.in_production_dice
    )
    # Phreaker Jumper Diagnostics / Spook Burn Notice: Phase 3 Income (Purple ★ still In Production, OQ-2)
    can_phreaker_diagnostics = bool(in_income and is_phreaker_white_hat and purple_in_prod)
    is_spook_white_hat = has_signature_protocol(player, WhiteHatCode.SPOOK, legacy_bridge_enabled(controller))
    can_spook_burn = bool(in_income and is_spook_white_hat and purple_in_prod)

    is_cipher = has_company_override(player, CompanyCode.PROMETHEUS, legacy_bridge_enabled(controller))
    can_cipher_buy = {}
    for color in [DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW, DieColor.PURPLE]:
        if color == DieColor.PURPLE:
            base_cost = player.get_purple_reserve_cost() if hasattr(player, "get_purple_reserve_cost") else (
                getattr(player.white_hat, "reserve_cost", 4) if getattr(player, "white_hat", None) else 4
            )
            has_stock = getattr(player, "personal_purple_reserve", 0) > 0
        else:
            base_cost = controller.state.get_market_die_cost(color) if hasattr(controller.state, "get_market_die_cost") else (
                4 if color in (DieColor.RED, DieColor.GREEN) else 5
            )
            has_stock = controller.state.market.get(color, 0) > 0

        disc_cost = max(0, base_cost - controller.state.config.cipher_market_discount)
        can_cipher_buy[color.value] = bool(
            controller.phase == 6
            and is_active
            and not is_eliminated
            and is_cipher
            and ability_avail
            and meta["purchases_this_turn"] < controller.state.config.max_market_purchases_per_turn
            and has_stock
            and player.money >= disc_cost
        )
    can_cipher_cash = bool(
        controller.phase == 6
        and is_active
        and not is_eliminated
        and is_cipher
        and ability_avail
    )
    can_cipher_dirty = can_cipher_cash

    is_acoustic = has_company_override(player, CompanyCode.AEGIS, legacy_bridge_enabled(controller))
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

    is_spook = has_company_override(player, CompanyCode.DTO, legacy_bridge_enabled(controller))
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
    can_hotfix = (controller.phase == 1 and meta["has_rolled"] and not meta["has_committed"] and avail_patches > 0 and not is_eliminated)
    can_commit = (controller.phase == 1 and meta["has_rolled"] and not meta["has_committed"] and not is_eliminated)
    can_compile = (controller.phase == 2 and controller.subphase == "ready_for_compile")

    can_confirm_income = bool(
        controller.phase == 3 and controller.subphase == "confirm_income"
        and not meta.get("income_confirmed", False) and not is_eliminated
    )
    can_confirm_attacks = bool(
        controller.phase == 4 and controller.subphase == "confirm_attacks" and not is_eliminated
        and player_id not in (getattr(controller, "attack_resolved_pids", set()) or set())
    )
    can_patch_cash = False
    can_patch_token = (
        controller.phase == 6
        and not can_confirm_income
        and is_active
        and not is_eliminated
        and len(player.unpatched_dice) > 0
        and player.patches >= controller.state.config.patch_token_cost
    )
    can_dirty = bool(
        controller.state.config.dirty_income_enabled
        and controller.phase == 6
        and not can_confirm_income
        and is_active
        and not is_eliminated
        and not meta["dirty_income_taken_this_turn"]
        and player.secrets > controller.state.config.dirty_income_secret_cost
        and len(player.ready_dice) >= 1
    )
    can_system_reboot = False
    can_fast_patch = False
    can_end_turn = (controller.phase == 6 and not can_confirm_income and is_active and not is_eliminated)

    # Market purchase availability per color
    can_buy = {}
    for color in [DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW, DieColor.PURPLE]:
        if color == DieColor.PURPLE:
            cost = player.get_purple_reserve_cost() if hasattr(player, "get_purple_reserve_cost") else (
                getattr(player.white_hat, "reserve_cost", 4) if getattr(player, "white_hat", None) else 4
            )
            has_stock = getattr(player, "personal_purple_reserve", 0) > 0
        else:
            cost = controller.state.get_market_die_cost(color) if hasattr(controller.state, "get_market_die_cost") else (
                4 if color in (DieColor.RED, DieColor.GREEN) else 5
            )
            has_stock = controller.state.market.get(color, 0) > 0

        can_buy[color.value] = bool(
            controller.phase == 6
            and not can_confirm_income
            and is_active
            and not is_eliminated
            and meta["purchases_this_turn"] < controller.state.config.max_market_purchases_per_turn
            and has_stock
            and player.money >= cost
        )
    can_buy_purple_reserve = bool(can_buy.get("purple", False))

    # Star actions
    can_star = {
        "B2": bool(
            controller.phase == 6
            and not can_confirm_income
            and is_active
            and player.b2_available
            and player.money >= controller.state.config.b2_secret_cost
            and (
                controller.state.config.b2_secret_cap is None
                or player.secrets < controller.state.config.b2_secret_cap
            )
        ),
        "Y1": bool(controller.phase == 6 and not can_confirm_income and is_active and player.y1_available and player.money >= 6),
        "P1": bool(controller.phase == 6 and not can_confirm_income and is_active and player.p1_available),
        "P3": bool(
            controller.phase == 6
            and not can_confirm_income
            and is_active
            and player.p3_available is not None
            and player.money >= controller.state.config.p3_cube_cash_cost
        ),
    }

    # Hardware Upgrade Tracks & Cryptographic Patents (v0.29.0)
    triage_cost = player.get_track_upgrade_cost("TRIAGE") if hasattr(player, "get_track_upgrade_cost") else None
    release_cost = player.get_track_upgrade_cost("RELEASE") if hasattr(player, "get_track_upgrade_cost") else None
    pipeline_cost = player.get_track_upgrade_cost("PIPELINE") if hasattr(player, "get_track_upgrade_cost") else None
    defense_cost = player.get_track_upgrade_cost("DEFENSE") if hasattr(player, "get_track_upgrade_cost") else None
    patent_track_cost = player.get_track_upgrade_cost("PATENT") if hasattr(player, "get_track_upgrade_cost") else None
    patent_cost = player.get_patent_cost() if hasattr(player, "get_patent_cost") else 4
    research_avail = getattr(player, "research_tokens", player.patches)

    can_upgrade_track = {
        "triage": bool(
            controller.phase == 6
            and not can_confirm_income
            and is_active
            and not is_eliminated
            and getattr(player, "triage_level", 0) < 2
            and triage_cost is not None
            and research_avail >= triage_cost
        ),
        "release": bool(
            controller.phase == 6
            and not can_confirm_income
            and is_active
            and not is_eliminated
            and getattr(player, "release_level", 0) < 2
            and release_cost is not None
            and research_avail >= release_cost
        ),
        "pipeline": bool(
            controller.phase == 6
            and not can_confirm_income
            and is_active
            and not is_eliminated
            and getattr(player, "pipeline_level", 0) < 2
            and pipeline_cost is not None
            and research_avail >= pipeline_cost
        ),
        "defense": bool(
            controller.phase == 6
            and not can_confirm_income
            and is_active
            and not is_eliminated
            and getattr(player, "defense_level", 0) < 2
            and defense_cost is not None
            and research_avail >= defense_cost
        ),
        "patent": bool(
            controller.phase == 6
            and not can_confirm_income
            and is_active
            and not is_eliminated
            and getattr(player, "patent_level", 0) < 2
            and patent_track_cost is not None
            and research_avail >= patent_track_cost
        ),
    }

    can_file_patent = bool(
        controller.phase == 6
        and not can_confirm_income
        and is_active
        and not is_eliminated
        and research_avail >= patent_cost
    )

    upgrade_track_costs = {
        "triage": triage_cost,
        "release": release_cost,
        "pipeline": pipeline_cost,
        "defense": defense_cost,
        "patent": patent_track_cost,
    }

    if can_confirm_income:
        can_phreaker = False
        can_cipher_buy = {color.value: False for color in [DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW, DieColor.PURPLE]}
        can_cipher_dirty = False

    return {
        "can_roll": can_roll,
        "can_hire_contractors": can_hire_contractors,
        "next_contractor_cost": next_contractor_cost,
        "can_reroll": can_reroll,
        "can_hotfix": can_hotfix,
        "can_commit": can_commit,
        "can_compile": can_compile,
        "can_confirm_income": can_confirm_income,
        "can_confirm_attacks": can_confirm_attacks,
        "can_aegis_echo": bool(
            can_confirm_attacks
            and ((((getattr(controller, "last_attack_result", None) or {}).get("threat_summary") or {}).get(player_id) or {})
                 .get("aegis", {}).get("available", False))
        ),
        "can_choose_graduates": can_choose_graduates,
        "can_splice": can_splice,
        "can_hotfix_bypass": can_hotfix_bypass,
        "can_spook_burn": can_spook_burn,
        "can_buy": can_buy,
        "can_buy_purple_reserve": can_buy_purple_reserve,
        "can_patch_cash": can_patch_cash,
        "can_patch_token": can_patch_token,
        "can_dirty_income": can_dirty,
        "can_fast_patch": can_fast_patch,
        "can_system_reboot": can_system_reboot,
        "can_star": can_star,
        "can_upgrade_track": can_upgrade_track,
        "upgrade_track_costs": upgrade_track_costs,
        "can_file_patent": can_file_patent,
        "patent_cost": patent_cost,
        "can_end_turn": can_end_turn,
        # Archetype capabilities
        "can_operator": can_operator,
        "can_prodigy": can_prodigy,
        "can_phreaker": can_phreaker,
        "can_phreaker_diagnostics": can_phreaker_diagnostics,
        "can_cipher_buy": can_cipher_buy,
        "can_cipher_dirty": can_cipher_dirty,
        "can_acoustic": can_acoustic,
        "can_spook": can_spook,
    }

