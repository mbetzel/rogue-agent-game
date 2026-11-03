"""Phase 3: Operations & Pipeline Prep (v0.22.0 Canonical)."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from sim.config import CubeColor, DieColor, ShieldColor
from sim.entities import ArchetypeCode, CompanyCode, WhiteHatCode, Face, create_colored_die
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
            elif eff.star_code == "PURPLE_STAR":
                # Operative Protocol Resolution for Income Timing
                is_acoustic = bool(
                    (player.white_hat and player.white_hat.code == WhiteHatCode.ACOUSTIC)
                    or (player.archetype and player.archetype.code == ArchetypeCode.ACOUSTIC)
                )
                is_cipher = bool(
                    (player.white_hat and player.white_hat.code == WhiteHatCode.CIPHER)
                    or (player.archetype and player.archetype.code == ArchetypeCode.CIPHER)
                )
                is_spook = bool(
                    (player.white_hat and player.white_hat.code == WhiteHatCode.SPOOK)
                    or (player.archetype and player.archetype.code == ArchetypeCode.SPOOK)
                )
                if is_acoustic:
                    # The Acoustic (Resonance Sensor): +$1 per unique cube color in Exit Tray (R, B, G, K; max +$4)
                    exited = getattr(engine.state, "last_exited_cubes", None)
                    if not exited:
                        exited = getattr(engine.state.tower, "last_exited_cubes", {})
                    unique_colors = len({c for c, count in exited.items() if count > 0})
                    player.money += min(4, unique_colors)
                elif is_cipher:
                    # The Cipher (Algorithmic Parity): Phase 3 Income: +$2
                    player.money += 2
                elif is_spook:
                    # The Spook (Burn Notice): Base Phase 3 Ops: +$2
                    player.money += 2

    for die in dice_to_glitch:
        if die in player.in_production_dice:
            player.in_production_dice.remove(die)
            die.production_role = None
            player.glitched_dice.append(die)


def resolve_spook_burn_notice(
    engine: GameEngine,
    player: PlayerState,
    die_id: int,
) -> bool:
    """Spook Face 6 Protocol (Burn Notice):
    Permanently returns 1 owned colored die to market to gain +1 Corporate Secret.
    """
    target_die: Optional[Die] = None
    for zone in (player.in_production_dice, player.glitched_dice, player.scanned_dice, player.ready_for_release_dice):
        for d in zone:
            if d.die_id == die_id and d.color not in (DieColor.GRAY, DieColor.WHITE):
                target_die = d
                zone.remove(d)
                break
        if target_die:
            break

    if not target_die:
        return False

    if target_die.color in engine.state.market:
        engine.state.market[target_die.color] += 1
    # If Purple, die is scrapped and not returned to market
    player.secrets += 1
    return True


def resolve_phreaker_jumper_diagnostics(
    engine: GameEngine,
    player: PlayerState,
    die_id: Optional[int] = None,
    rng: Optional[random.Random] = None,
    forced_face: Optional[Face] = None,
) -> Optional[Face]:
    """Phreaker Face 6 Protocol (Jumper Diagnostics):
    Rolls 1 die currently in Under Development; harvests rolled cash/patches; die remains in place.
    """
    ud_dice = player.under_development_dice
    if not ud_dice:
        return None

    target_die = None
    if die_id is not None:
        target_die = next((d for d in ud_dice if d.die_id == die_id), None)
    if target_die is None:
        target_die = ud_dice[0]

    if forced_face is not None:
        target_die.current_face = forced_face
        face = forced_face
    else:
        roll_rng = rng or engine.rng
        face = target_die.roll(roll_rng)

    if face and not face.is_glitch and not face.is_star:
        player.money += face.money
        player.patches += face.patches
    return face


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

        # 2. Institutional Override: The Prometheus Foundation (Algorithmic Arbitrage)
        prometheus_discount_applied = False
        is_prometheus = bool(
            (player.company and player.company.code == CompanyCode.PROMETHEUS)
            or (player.archetype and player.archetype.code == ArchetypeCode.CIPHER)
        ) and player.is_ability_available(active_ver)
        use_prom = bool(getattr(plan, "use_prometheus_override", False) or getattr(plan, "use_cipher_ability", False))
        prom_mode = getattr(plan, "prometheus_mode", None) or getattr(plan, "cipher_mode", None)
        prom_color = getattr(plan, "prometheus_discount_die_color", None) or getattr(plan, "cipher_free_die_color", None)

        if (
            use_prom
            and prom_mode in ("BUY_FREE_DIE", "DISCOUNT", 1)
            and prom_color is not None
            and is_prometheus
        ):
            free_color = prom_color
            if free_color == DieColor.PURPLE:
                normal_cost = player.get_purple_reserve_cost()
            else:
                normal_cost = engine.state.get_market_die_cost(free_color)
            discounted_cost = max(0, normal_cost - engine.state.config.cipher_market_discount)
            if free_color == DieColor.PURPLE:
                if player.personal_purple_reserve > 0 and player.money >= discounted_cost:
                    player.money -= discounted_cost
                    player.personal_purple_reserve -= 1
                    new_die = create_colored_die(
                        color=DieColor.PURPLE,
                        die_id=engine.state.next_die_id,
                        reserve_cost=player.get_purple_reserve_cost(),
                    )
                    engine.state.next_die_id += 1
                    player.ready_for_release_dice.append(new_die)
                    player.mark_ability_used(active_ver)
                    prometheus_discount_applied = True
            elif engine.state.market.get(free_color, 0) > 0 and player.money >= discounted_cost:
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
                prometheus_discount_applied = True

        is_prom_cash = (
            use_prom
            and prom_mode in ("CASH", "ARBITRAGE_CASH", "DIRTY_INCOME")
            and is_prometheus
            and not prometheus_discount_applied
        )
        if is_prom_cash:
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

        # Operative Protocol Face 6 Resolution in Phase 3A (Spook & Phreaker)
        has_purple_star = any(
            (d.effective_face or d.current_face)
            and (d.effective_face or d.current_face).is_star
            and (d.effective_face or d.current_face).star_code == "PURPLE_STAR"
            for d in player.in_production_dice
        )
        if has_purple_star:
            is_spook = bool(
                (player.white_hat and player.white_hat.code == WhiteHatCode.SPOOK)
                or (player.archetype and player.archetype.code == ArchetypeCode.SPOOK)
            )
            is_phreaker = bool(
                (player.white_hat and player.white_hat.code == WhiteHatCode.PHREAKER)
                or (player.archetype and player.archetype.code == ArchetypeCode.PHREAKER)
            )
            if is_spook and plan.spook_burn_die_id is not None:
                resolve_spook_burn_notice(engine, player, plan.spook_burn_die_id)
            elif is_phreaker and player.under_development_dice:
                diag_id = plan.phreaker_diagnostics_die_id
                if diag_id is None:
                    diag_id = player.bot.choose_phreaker_jumper_diagnostics(player, engine.state, engine.rng)
                if diag_id is not None:
                    resolve_phreaker_jumper_diagnostics(engine, player, diag_id, engine.rng)

        # 4. Market Purchases (Limit 2 dice per turn; deliver directly to ready_for_release_dice)
        purchased_count = 1 if prometheus_discount_applied else 0
        purchases_list = list(plan.market_purchases)
        if plan.buy_purple_reserve and DieColor.PURPLE not in purchases_list:
            purchases_list.append(DieColor.PURPLE)

        for color in purchases_list:
            if purchased_count >= engine.state.config.max_market_purchases_per_turn:
                break

            if color == DieColor.PURPLE:
                cost = player.get_purple_reserve_cost()
                if player.personal_purple_reserve > 0 and player.money >= cost:
                    player.money -= cost
                    player.personal_purple_reserve -= 1
                    purchased_count += 1
                    new_die = create_colored_die(
                        color=DieColor.PURPLE,
                        die_id=engine.state.next_die_id,
                        reserve_cost=cost,
                    )
                    engine.state.next_die_id += 1
                    player.ready_for_release_dice.append(new_die)
            else:
                cost = engine.state.get_market_die_cost(color)
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

        # 5. Terminal Mat Track Upgrades (INV-UPGRADE-TRACK-01)
        upgrades = getattr(plan, "track_upgrades", [])
        for track in upgrades:
            cost = player.get_track_upgrade_cost(track)
            if cost is not None and player.research_tokens >= cost:
                player.upgrade_track(track)

        # 6. Cryptographic Patent Filings (INV-PATENT-CONV-01)
        patent_filings = getattr(plan, "patent_filings", 0)
        while patent_filings > 0:
            cost = player.get_patent_cost()
            if player.research_tokens >= cost:
                player.file_patent()
                patent_filings -= 1
            else:
                break

    # -------------------------------------------------------------------------
    # Part 3B: Pipeline Prep & End-of-Round Staging (Simultaneous)
    # -------------------------------------------------------------------------
    for player in engine.state.players:
        if player.is_patient_zero:
            continue

        active_ver = engine.state.active_version.version_str

        # 1. Hotfix Capabilities (Omnidyne Magnetic Splice & Emergency Hotfix)
        # Hook: Omnidyne Systems (Magnetic Splice) — moves 1 die from glitched_dice directly to ready_for_release_dice for free
        is_omnidyne = bool(
            (player.company and player.company.code == CompanyCode.OMNIDYNE)
            or (player.archetype and player.archetype.code == ArchetypeCode.PHREAKER)
        ) and player.is_ability_available(active_ver)
        if (
            is_omnidyne
            and player.glitched_dice
        ):
            target_id = player.bot.choose_omnidyne_override(player, engine.state, engine.rng)
            chosen_idx = None
            if target_id is not None:
                for i, d in enumerate(player.glitched_dice):
                    if d.die_id == target_id:
                        chosen_idx = i
                        break
            if chosen_idx is None:
                # Prioritize colored dice over gray dice
                chosen_idx = max(
                    range(len(player.glitched_dice)),
                    key=lambda i: (
                        1 if player.glitched_dice[i].color != DieColor.GRAY else 0,
                        getattr(player.glitched_dice[i], "cost", 0),
                    ),
                )
            omnidyne_die = player.glitched_dice.pop(chosen_idx)
            omnidyne_die.production_role = None
            omnidyne_die.is_locked = False
            omnidyne_die.chosen_choice_index = None
            omnidyne_die.current_face = None
            player.ready_for_release_dice.append(omnidyne_die)
            player.mark_ability_used(active_ver)

        # Emergency Hotfix (Level 2 Pipeline Track - INV-UPGRADE-TRACK-01)
        if getattr(player, "has_emergency_hotfix", False) and player.glitched_dice:
            hotfix_idx = max(
                range(len(player.glitched_dice)),
                key=lambda i: (
                    1 if player.glitched_dice[i].color != DieColor.GRAY else 0,
                    getattr(player.glitched_dice[i], "cost", 0),
                ),
            )
            h_die = player.glitched_dice.pop(hotfix_idx)
            h_die.production_role = None
            h_die.is_locked = False
            h_die.chosen_choice_index = None
            h_die.current_face = None
            player.ready_for_release_dice.append(h_die)

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

        # 2. Scanned Graduation (Release Bandwidth - INV-PIPE-GRAD-01):
        # Move up to player.release_bandwidth dice from scanned_dice to ready_for_release_dice
        grad_count = min(len(player.scanned_dice), player.release_bandwidth)
        for _ in range(grad_count):
            s_die = player.scanned_dice.pop(0)
            s_die.production_role = None
            s_die.is_locked = False
            s_die.chosen_choice_index = None
            s_die.current_face = None
            player.ready_for_release_dice.append(s_die)

        # 3. Conveyor Shift / Triage (Triage Bandwidth - INV-PIPE-TRIAGE-01):
        # Move up to player.triage_bandwidth dice from glitched_dice into scanned_dice
        triage_count = min(len(player.glitched_dice), player.triage_bandwidth)
        for _ in range(triage_count):
            g_die = player.glitched_dice.pop(0)
            g_die.production_role = None
            g_die.is_locked = False
            g_die.chosen_choice_index = None
            g_die.current_face = None
            player.scanned_dice.append(g_die)

        # 4. Production Return: all surviving in_production_dice return to ready_for_release_dice
        for p_die in player.in_production_dice:
            p_die.production_role = None
            p_die.is_locked = False
            p_die.chosen_choice_index = None
            p_die.current_face = None
            player.ready_for_release_dice.append(p_die)
        player.in_production_dice.clear()

        # 5. Patch Token Cap Removed: Research tokens are uncapped (INV-RESEARCH-UNCAPPED-01)

    # 6. Pass Lead Consultant Marker clockwise
    engine.state.first_player_index = (engine.state.first_player_index + 1) % num_players

