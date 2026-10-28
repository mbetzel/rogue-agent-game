"""Phase 3: Corporate Operations (Clockwise Turns)."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from sim.config import CubeColor, DieColor, ShieldColor
from sim.entities import ArchetypeCode, create_colored_die

if TYPE_CHECKING:
    from sim.engine.core import GameEngine
    from sim.engine.state import PlayerState


def execute_phase_3(engine: GameEngine) -> None:
    if engine.state.game_over or all(p.is_patient_zero for p in engine.state.players):
        return

    num_players = len(engine.state.players)
    patch_cash_cost = engine.state.config.patch_cash_cost

    for offset in range(num_players):
        idx = (engine.state.first_player_index + offset) % num_players
        player = engine.state.players[idx]

        if player.is_patient_zero:
            continue

        plan = player.bot.take_phase3_actions(player, engine.state, engine.rng)
        active_ver = engine.state.active_version.version_str

        # Hook Phase 3: The Phreaker (Magnetic Splice) - patch up to 2 worn dice for free
        if (
            plan.use_phreaker_ability
            and player.archetype is not None
            and player.archetype.code == ArchetypeCode.PHREAKER
            and player.is_ability_available(active_ver)
        ):
            free_patches = min(2, len(player.unpatched_dice))
            for _ in range(free_patches):
                patched_die = player.unpatched_dice.pop(0)
                player.ready_dice.append(patched_die)
            if free_patches > 0:
                player.mark_ability_used(active_ver)

        # Hook Phase 3: The Cipher (Algorithmic Arbitrage) - Mode 1: Discounted Colored Die from Market ($2 discount)
        cipher_discount_applied = False
        if (
            plan.use_cipher_ability
            and plan.cipher_mode in ("BUY_FREE_DIE", 1)
            and plan.cipher_free_die_color is not None
            and player.archetype is not None
            and player.archetype.code == ArchetypeCode.CIPHER
            and player.is_ability_available(active_ver)
        ):
            free_color = plan.cipher_free_die_color
            normal_cost = 4 if free_color in (DieColor.RED, DieColor.GREEN, DieColor.PURPLE) else 5
            discounted_cost = max(0, normal_cost - engine.state.config.cipher_market_discount)
            if engine.state.market.get(free_color, 0) > 0 and player.money >= discounted_cost:
                player.money -= discounted_cost
                engine.state.market[free_color] -= 1
                new_die = create_colored_die(
                    color=free_color,
                    die_id=engine.state.next_die_id,
                    variant_card=engine.state.variant_cards.get(free_color),
                )
                engine.state.next_die_id += 1
                player.ready_dice.append(new_die)
                player.mark_ability_used(active_ver)
                cipher_discount_applied = True

        # Hook Phase 3: The Cipher (Algorithmic Arbitrage) - Mode 2: Dirty Income without Backlash
        is_cipher_dirty_income = (
            plan.use_cipher_ability
            and plan.cipher_mode == "DIRTY_INCOME"
            and player.archetype is not None
            and player.archetype.code == ArchetypeCode.CIPHER
            and player.is_ability_available(active_ver)
        )

        # 1. Dirty Income ("Monetize the Rogue Agent" — Limit 1x per turn)
        # Preconditions: secrets > dirty_income_secret_cost and at least 1 ready die for Backlash (unless Cipher)
        if (
            plan.take_dirty_income
            and player.secrets > engine.state.config.dirty_income_secret_cost
            and (is_cipher_dirty_income or len(player.ready_dice) >= 1)
        ):
            player.secrets -= engine.state.config.dirty_income_secret_cost
            player.money += engine.state.config.dirty_income_cash
            engine.state.staging_cup[CubeColor.BLACK] = (
                engine.state.staging_cup.get(CubeColor.BLACK, 0)
                + engine.state.config.dirty_income_black_cubes
            )
            if is_cipher_dirty_income:
                # Skip Technical Debt Backlash demotion!
                player.mark_ability_used(active_ver)
            else:
                # Technical Debt Backlash: demote 1 Ready die to Unpatched
                backlash_idx = plan.dirty_income_backlash_die_index
                if not (0 <= backlash_idx < len(player.ready_dice)):
                    backlash_idx = 0
                backlash_die = player.ready_dice.pop(backlash_idx)
                player.unpatched_dice.append(backlash_die)
            player.total_dirty_income_taken += 1

        # 2. Star Special Actions in Phase 3 (Guarded by Phase 1 eligibility)
        if plan.use_b2_secret and player.b2_available:
            if (
                player.money >= engine.config.b2_secret_cost
                and player.secrets < engine.config.b2_secret_cap
            ):
                player.money -= engine.config.b2_secret_cost
                player.secrets = min(engine.config.b2_secret_cap, player.secrets + 1)
                player.b2_available = False

        if plan.use_y1_secret and player.y1_available:
            # Reverses +$4 from P1 and pays $2 for +1 Secret (net -$2)
            if player.money >= 6 and player.secrets < 10:
                player.money -= 6
                player.secrets = min(10, player.secrets + 1)
                player.y1_available = False

        if (
            plan.p1_cube_choice in (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN)
            and player.p1_available
        ):
            engine.state.staging_cup[plan.p1_cube_choice] = (
                engine.state.staging_cup.get(plan.p1_cube_choice, 0) + 1
            )
            player.p1_available = False

        if (
            plan.p3_cube_choice in (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN)
            and player.p3_available is not None
        ):
            # Must match the color that P3 blocked and player must afford cash cost!
            if plan.p3_cube_choice.value == player.p3_available.value:
                if player.money >= engine.config.p3_cube_cash_cost:
                    player.money -= engine.config.p3_cube_cash_cost
                    engine.state.staging_cup[plan.p3_cube_choice] = (
                        engine.state.staging_cup.get(plan.p3_cube_choice, 0) + 1
                    )
                    player.p3_available = None

        # 3. Patching Worn-Out Dice (Unlimited)
        for patch_action in plan.patch_actions:
            if len(player.unpatched_dice) == 0:
                break
            idx = patch_action.get("die_index", 0)
            if not isinstance(idx, int) or not (0 <= idx < len(player.unpatched_dice)):
                idx = 0

            use_cash = bool(patch_action.get("use_cash", False))
            if use_cash:
                if player.money >= patch_cash_cost:
                    player.money -= patch_cash_cost
                    patched_die = player.unpatched_dice.pop(idx)
                    player.ready_dice.append(patched_die)
            else:
                if player.patches >= engine.state.config.patch_token_cost:
                    player.patches -= engine.state.config.patch_token_cost
                    patched_die = player.unpatched_dice.pop(idx)
                    player.ready_dice.append(patched_die)

        # 4. Market Purchases (Limit 2 dice per turn)
        purchased_count = 1 if cipher_discount_applied else 0
        for color in plan.market_purchases:
            if purchased_count >= engine.state.config.max_market_purchases_per_turn:
                break
            cost = 4 if color in (DieColor.RED, DieColor.GREEN, DieColor.PURPLE) else 5
            if engine.state.market.get(color, 0) > 0 and player.money >= cost:
                player.money -= cost
                engine.state.market[color] -= 1
                purchased_count += 1
                new_die = create_colored_die(
                    color=color,
                    die_id=engine.state.next_die_id,
                    variant_card=engine.state.variant_cards.get(color),
                )
                engine.state.next_die_id += 1
                player.ready_dice.append(new_die)

        # Cap patch tokens
        player.patches = min(player.patches, engine.state.config.max_patch_tokens)

    # Advance First Player marker clockwise
    engine.state.first_player_index = (engine.state.first_player_index + 1) % num_players

