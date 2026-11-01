"""Phase 3: Operations & Pipeline Prep (v0.22.0 Canonical)."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from sim.config import CubeColor, DieColor, ShieldColor
from sim.entities import ArchetypeCode, create_colored_die
from sim.engine.state import ProductionRole

if TYPE_CHECKING:
    from sim.engine.core import GameEngine
    from sim.engine.state import PlayerState
    from sim.entities import Die


def collect_player_production_income(engine: GameEngine, player: PlayerState, plan: Any) -> None:
    """Part 3A Step 1: Collect income from ALL dice remaining in in_production_dice."""
    dice_to_glitch: List[Die] = []

    for die in list(player.in_production_dice):
        eff = die.effective_face or die.current_face
        if not eff or eff.is_glitch:
            continue

        # Resource outputs from printed face
        player.money += eff.money
        player.patches += eff.patches
        player.secrets += eff.secrets

        if eff.is_star:
            if eff.star_code == "Y2":
                # Cloud Monopoly: +$2, plus +$1 per different colored module die owned (max +$5)
                count = len({d.color for d in player.colored_dice})
                total_payout = min(engine.config.y2_max_payout, engine.config.y2_base_payout + count)
                bonus = total_payout - eff.money
                player.money += max(0, bonus)
            elif eff.star_code == "Y3":
                # Proprietary Training: move die to glitched_dice after collecting secret
                dice_to_glitch.append(die)

    for die in dice_to_glitch:
        if die in player.in_production_dice:
            player.in_production_dice.remove(die)
            die.production_role = None
            player.glitched_dice.append(die)


def execute_phase_3(engine: GameEngine) -> None:
    """Executes Phase 3 Operations & Pipeline Prep per RULES.md Section 4."""
    if engine.state.game_over or all(p.is_patient_zero for p in engine.state.players):
        return

    num_players = len(engine.state.players)

    # -------------------------------------------------------------------------
    # Part 3A: Operations Turns (Clockwise)
    # -------------------------------------------------------------------------
    for offset in range(num_players):
        idx = (engine.state.first_player_index + offset) % num_players
        player = engine.state.players[idx]

        if player.is_patient_zero:
            continue

        plan = player.bot.take_phase3_actions(player, engine.state, engine.rng)
        active_ver = engine.state.active_version.version_str

        # 1. Collect Income from ALL surviving dice in in_production_dice
        collect_player_production_income(engine, player, plan)

        # 1b. Dirty Income (Optional, once per turn)
        if (
            plan.take_dirty_income
            and engine.config.dirty_income_enabled
            and not getattr(engine.state, "is_final_round", False)
            and player.secrets > engine.config.dirty_income_secret_cost
            and len(player.ready_dice) >= 1
        ):
            player.money += engine.config.dirty_income_cash
            player.secrets -= engine.config.dirty_income_secret_cost
            engine.state.staging_cup[CubeColor.BLACK] = (
                engine.state.staging_cup.get(CubeColor.BLACK, 0)
                + engine.config.dirty_income_black_cubes
            )
            player.total_dirty_income_taken += 1
            b_idx = plan.dirty_income_backlash_die_index
            if b_idx is not None and 0 <= b_idx < len(player.ready_dice):
                demoted = player.ready_dice.pop(b_idx)
            else:
                demoted = player.ready_dice.pop(0)
            player.glitched_dice.append(demoted)

        # 2. Archetype Ability: The Cipher (Algorithmic Arbitrage)
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
                player.ready_for_release_dice.append(new_die)
                player.mark_ability_used(active_ver)
                cipher_discount_applied = True

        is_cipher_cash = (
            plan.use_cipher_ability
            and plan.cipher_mode in ("CASH", "ARBITRAGE_CASH", "DIRTY_INCOME")
            and player.archetype is not None
            and player.archetype.code == ArchetypeCode.CIPHER
            and player.is_ability_available(active_ver)
            and not cipher_discount_applied
        )
        if is_cipher_cash:
            player.money += engine.state.config.cipher_arbitrage_cash
            player.mark_ability_used(active_ver)

        # 3. Star Special Actions in Phase 3 (Guarded by Phase 1 eligibility)
        if plan.use_b2_secret and player.b2_available:
            if (
                player.money >= engine.config.b2_secret_cost
                and (engine.config.b2_secret_cap is None or player.secrets < engine.config.b2_secret_cap)
            ):
                player.money -= engine.config.b2_secret_cost
                player.secrets += 1
                player.b2_available = False

        if plan.use_y1_secret and player.y1_available:
            # Reverses +$4 from P1 and pays $2 for +1 Secret (net -$2)
            if player.money >= 6:
                player.money -= 6
                player.secrets += 1
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
            if plan.p3_cube_choice.value == player.p3_available.value:
                if player.money >= engine.config.p3_cube_cash_cost:
                    player.money -= engine.config.p3_cube_cash_cost
                    engine.state.staging_cup[plan.p3_cube_choice] = (
                        engine.state.staging_cup.get(plan.p3_cube_choice, 0) + 1
                    )
                    player.p3_available = None

        # 4. Market Purchases (Limit 2 dice per turn; deliver directly to ready_for_release_dice)
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
                player.ready_for_release_dice.append(new_die)

    # -------------------------------------------------------------------------
    # Part 3B: Pipeline Prep & End-of-Round Staging (Simultaneous)
    # -------------------------------------------------------------------------
    for player in engine.state.players:
        if player.is_patient_zero:
            continue

        active_ver = engine.state.active_version.version_str

        # 1. Fast-Patching & Phreaker Magnetic Splice
        # Hook: The Phreaker (Magnetic Splice) — moves 1 die from glitched_dice directly to ready_for_release_dice for free
        if (
            player.archetype is not None
            and player.archetype.code == ArchetypeCode.PHREAKER
            and player.is_ability_available(active_ver)
            and player.glitched_dice
        ):
            # Prioritize colored dice over gray dice
            best_idx = max(
                range(len(player.glitched_dice)),
                key=lambda i: (
                    1 if player.glitched_dice[i].color != DieColor.GRAY else 0,
                    getattr(player.glitched_dice[i], "cost", 0),
                ),
            )
            phreaker_die = player.glitched_dice.pop(best_idx)
            phreaker_die.production_role = None
            phreaker_die.is_locked = False
            phreaker_die.chosen_choice_index = None
            phreaker_die.current_face = None
            player.ready_for_release_dice.append(phreaker_die)
            player.mark_ability_used(active_ver)

        # Bot Fast-Patch Decision: spend 1 🔧 per die to move from glitched_dice to scanned_dice
        fast_patches = player.bot.choose_fast_patches(player, engine.state, engine.rng)
        if fast_patches and player.patches > 0 and player.glitched_dice:
            # Sort indices descending so removal doesn't shift earlier indices
            valid_indices = sorted(
                {idx for idx in fast_patches if 0 <= idx < len(player.glitched_dice)},
                reverse=True,
            )
            for f_idx in valid_indices:
                if player.patches <= 0 or f_idx >= len(player.glitched_dice):
                    break
                p_die = player.glitched_dice.pop(f_idx)
                p_die.production_role = None
                p_die.is_locked = False
                p_die.chosen_choice_index = None
                p_die.current_face = None
                player.scanned_dice.append(p_die)
                player.patches -= 1
                player.total_fast_patches += 1

        # 2. Scanned Graduation: all dice in scanned_dice graduate to ready_for_release_dice
        for s_die in player.scanned_dice:
            s_die.production_role = None
            s_die.is_locked = False
            s_die.chosen_choice_index = None
            s_die.current_face = None
            player.ready_for_release_dice.append(s_die)
        player.scanned_dice.clear()

        # 3. Production Return: all surviving in_production_dice return to ready_for_release_dice
        for p_die in player.in_production_dice:
            p_die.production_role = None
            p_die.is_locked = False
            p_die.chosen_choice_index = None
            p_die.current_face = None
            player.ready_for_release_dice.append(p_die)
        player.in_production_dice.clear()

        # 4. Conveyor Shift: all remaining glitched_dice shift into scanned_dice
        for g_die in player.glitched_dice:
            g_die.production_role = None
            g_die.is_locked = False
            g_die.chosen_choice_index = None
            g_die.current_face = None
            player.scanned_dice.append(g_die)
        player.glitched_dice.clear()

        # 5. Patch Token Cap: discard unspent patches in excess of 3 🔧
        player.patches = min(player.patches, 3)

    # 6. Pass Lead Consultant Marker clockwise
    engine.state.first_player_index = (engine.state.first_player_index + 1) % num_players

