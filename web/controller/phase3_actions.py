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
from sim.engine.phase3_ops import (
    collect_player_production_income,
    resolve_phreaker_jumper_diagnostics,
    resolve_spook_burn_notice,
)
from sim.engine.state import ProductionRole
from sim.entities import (
    AbilityStatus,
    ArchetypeCard,
    ArchetypeCode,
    CompanyCode,
    Die,
    VariantCard,
    VersionCard,
    WhiteHatCode,
    create_colored_die,
    create_white_die,
)

if TYPE_CHECKING:
    from web.controller.core import GameController


def confirm_income(
    controller: GameController,
    player_id: int,
    glitch_die_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """Confirms compile results and income, resolving human green malware glitch selections, harvesting production income, and moving surviving dice to scanned_dice."""
    if controller.phase != 3:
        raise ValueError(f"Cannot confirm income in phase {controller.phase}")
    if player_id not in controller.player_meta:
        raise ValueError(f"Invalid player_id {player_id}")

    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]
    if player.is_patient_zero:
        raise ValueError(f"Player {player_id} is eliminated")

    pending_green = getattr(player, "pending_unblocked_green", 0)
    selected_ids = list(glitch_die_ids) if glitch_die_ids is not None else []

    if pending_green > 0:
        glitched_count = 0
        for die_id in selected_ids:
            if glitched_count >= pending_green:
                break
            # 1. Check contractor dice
            matching_contractor = next((d for d in player.contractor_dice if d.die_id == die_id), None)
            if not matching_contractor and any(d.die_id == die_id and d.color == DieColor.WHITE for d in player.in_production_dice):
                matching_contractor = next(d for d in player.in_production_dice if d.die_id == die_id and d.color == DieColor.WHITE)

            if matching_contractor:
                if matching_contractor in player.contractor_dice:
                    player.contractor_dice.remove(matching_contractor)
                if matching_contractor in player.in_production_dice:
                    player.in_production_dice.remove(matching_contractor)
                controller.state.contractor_supply += 1
                glitched_count += 1
                controller.event_log.append(
                    f"{meta['name']} sacrificed White Contractor die to absorb Green malware."
                )
                continue

            # 2. Check in_production_dice
            matching_prod = next((d for d in player.in_production_dice if d.die_id == die_id), None)
            if matching_prod:
                player.in_production_dice.remove(matching_prod)
                # Remove from shield slot visual tracking if present
                for slot_color in ["red", "blue", "green"]:
                    if slot_color in meta.get("shield_slots", {}):
                        meta["shield_slots"][slot_color] = [d for d in meta["shield_slots"][slot_color] if d.die_id != die_id]
                matching_prod.production_role = None
                matching_prod.is_locked = False
                matching_prod.chosen_choice_index = None
                matching_prod.current_face = None
                player.glitched_dice.append(matching_prod)
                glitched_count += 1
                controller.event_log.append(
                    f"{meta['name']} moved {matching_prod.color.value.capitalize()} Die to Glitched Box due to Green malware."
                )
                continue

            # 3. Check destruction fallback from Under Development / Ready
            matching_fallback = next((d for d in (player.glitched_dice + player.scanned_dice + player.ready_for_release_dice) if d.die_id == die_id), None)
            if matching_fallback:
                if matching_fallback in player.glitched_dice:
                    player.glitched_dice.remove(matching_fallback)
                elif matching_fallback in player.scanned_dice:
                    player.scanned_dice.remove(matching_fallback)
                elif matching_fallback in player.ready_for_release_dice:
                    player.ready_for_release_dice.remove(matching_fallback)
                glitched_count += 1
                controller.event_log.append(
                    f"{meta['name']} destroyed {matching_fallback.color.value.capitalize()} Die from Under Development due to Green malware fallback."
                )
                continue

        # If user didn't select enough dice (or selected none, e.g. API fallback), auto-select remainder
        remaining_needed = pending_green - glitched_count
        if remaining_needed > 0:
            for _ in range(remaining_needed):
                if player.contractor_dice:
                    player.contractor_dice.pop(0)
                    controller.state.contractor_supply += 1
                elif player.in_production_dice:
                    def glitch_sort_key(d: Die) -> Tuple[int, int, int]:
                        role = getattr(d, "production_role", None)
                        is_shield = 0 if role in (ProductionRole.RED_SHIELD, ProductionRole.BLUE_SHIELD, ProductionRole.GREEN_SHIELD) else 1
                        is_gray = 0 if d.color == DieColor.GRAY else 1
                        return (is_shield, is_gray, getattr(d, "cost", 0))
                    target_die = min(player.in_production_dice, key=glitch_sort_key)
                    player.in_production_dice.remove(target_die)
                    for slot_color in ["red", "blue", "green"]:
                        if slot_color in meta.get("shield_slots", {}):
                            meta["shield_slots"][slot_color] = [d for d in meta["shield_slots"][slot_color] if d.die_id != target_die.die_id]
                    target_die.production_role = None
                    target_die.is_locked = False
                    target_die.chosen_choice_index = None
                    target_die.current_face = None
                    player.glitched_dice.append(target_die)
                elif player.glitched_dice:
                    player.glitched_dice.pop(0)
                elif player.scanned_dice:
                    player.scanned_dice.pop(0)
                elif player.ready_for_release_dice:
                    player.ready_for_release_dice.pop(0)
                else:
                    player.unfulfilled_destructions += 1

        player.pending_unblocked_green = 0

    # Contractor expiration for this player
    controller.state.contractor_supply += len(player.contractor_dice)
    player.contractor_dice.clear()
    player.hired_contractor_count = 0
    for wd in [d for d in player.in_production_dice if d.color == DieColor.WHITE]:
        player.in_production_dice.remove(wd)
        controller.state.contractor_supply += 1

    # Harvest production income from surviving in_production_dice if not already collected
    if not meta.get("income_collected_this_turn", False):
        collect_player_production_income(controller.engine, player, None)
        meta["income_collected_this_turn"] = True
        controller.event_log.append(
            f"{meta['name']} harvested delayed income from active production modules."
        )

    # Move all surviving in_production_dice to scanned_dice for all players
    for pid, p in enumerate(controller.state.players):
        if p.is_patient_zero:
            continue
        p_meta = controller.player_meta[pid]
        p_meta["shield_slots"] = {"red": [], "blue": [], "green": []}

        for die in list(p.in_production_dice):
            die.production_role = None
            die.is_locked = False
            die.chosen_choice_index = None
            die.current_face = None
            p.scanned_dice.append(die)
        p.in_production_dice.clear()

    controller.subphase = "player_turn"
    controller.event_log.append(
        "Production income confirmed; all operational modules transferred to CI/CD pipeline (Scanned Box)."
    )

    # Now advance clockwise queue starting with First Player
    advance_phase3_turns(controller)
    return controller.get_full_state()


def advance_phase3_turns(controller: GameController) -> None:
    """Processes Phase 3 turns clockwise, automatically executing bots until a human turn or round end."""
    while controller.phase3_turn_queue:
        next_pid = controller.phase3_turn_queue[0]
        player = controller.state.players[next_pid]
        meta = controller.player_meta[next_pid]

        # Skip eliminated players
        if player.is_patient_zero:
            controller.phase3_turn_queue.pop(0)
            controller.event_log.append(f"{meta['name']} is Patient Zero (eliminated, skipping Phase 3).")
            continue

        # If human player's turn: stop and wait for interactive actions
        if meta["is_human"]:
            controller.active_player_index = next_pid
            meta["purchases_this_turn"] = 0
            meta["dirty_income_taken_this_turn"] = False
            if not meta.get("income_collected_this_turn", False):
                collect_player_production_income(controller.engine, player, None)
                meta["income_collected_this_turn"] = True
                controller.event_log.append(
                    f"{meta['name']} collected delayed income from active production modules."
                )
            return

        # Bot player turn: execute automatically
        controller.active_player_index = next_pid
        controller.phase3_turn_queue.pop(0)
        execute_bot_phase3(controller, player, meta)

    # All players have finished Phase 3 -> complete round cleanup
    controller._complete_round()



def execute_bot_phase3(controller: GameController, player: PlayerState, meta: Dict[str, Any]) -> None:
    """Executes Phase 3 plan for a single bot player."""
    plan: Phase3ActionPlan = player.bot.take_phase3_actions(player, controller.state, controller.engine.rng)

    # 1. Collect Delayed Income from all surviving dice in in_production_dice (v0.22.0 Canonical)
    collect_player_production_income(controller.engine, player, plan)
    meta["income_collected_this_turn"] = True
    controller.event_log.append(
        f"{meta['name']} (Bot) collected delayed income from active production modules."
    )

    # Bot Fast-Patching in Under Development
    fast_patches = player.bot.choose_fast_patches(player, controller.state, controller.engine.rng)
    if fast_patches and player.patches > 0 and player.glitched_dice:
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

    # Corporate Override: Omnidyne (Magnetic Splice - v0.22.0: Glitched Box directly to Ready for Release)
    has_omnidyne = bool(
        (player.company and player.company.code == CompanyCode.OMNIDYNE)
        or (player.archetype and player.archetype.code == ArchetypeCode.PHREAKER)
    )
    if (
        (plan.use_omnidyne_override or plan.use_phreaker_ability)
        and has_omnidyne
        and player.is_ability_available()
        and player.glitched_dice
    ):
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
        player.mark_ability_used()
        controller.event_log.append(
            f"{meta['name']} (Bot) used Omnidyne Magnetic Splice: spliced 1 die directly to Ready for Release for free."
        )

    # Corporate Override: Prometheus (Algorithmic Arbitrage)
    cipher_used = False
    has_prometheus = bool(
        (player.company and player.company.code == CompanyCode.PROMETHEUS)
        or (player.archetype and player.archetype.code == ArchetypeCode.CIPHER)
    )
    if (
        (plan.use_prometheus_override or plan.use_cipher_ability)
        and has_prometheus
        and player.is_ability_available()
    ):
        p_mode = plan.prometheus_mode or plan.cipher_mode
        p_color = plan.prometheus_discount_die_color or plan.cipher_free_die_color
        if p_mode in ("BUY_FREE_DIE", 1) and p_color is not None:
            free_color = p_color
            normal_cost = 4 if free_color in (DieColor.RED, DieColor.GREEN, DieColor.PURPLE) else 5
            discounted_cost = max(0, normal_cost - controller.state.config.cipher_market_discount)
            if free_color == DieColor.PURPLE:
                if player.personal_purple_reserve > 0 and player.money >= discounted_cost:
                    player.money -= discounted_cost
                    player.personal_purple_reserve -= 1
                    meta["purchases_this_turn"] += 1
                    new_die = create_colored_die(
                        color=DieColor.PURPLE,
                        die_id=controller.state.next_die_id,
                    )
                    controller.state.next_die_id += 1
                    player.ready_dice.append(new_die)
                    player.mark_ability_used()
                    cipher_used = True
                    controller.event_log.append(
                        f"{meta['name']} (Bot) used Prometheus Algorithmic Arbitrage: Purple Die from Reserve at ${discounted_cost}."
                    )
            elif controller.state.market.get(free_color, 0) > 0 and player.money >= discounted_cost:
                player.money -= discounted_cost
                controller.state.market[free_color] -= 1
                meta["purchases_this_turn"] += 1
                new_die = create_colored_die(
                    color=free_color,
                    die_id=controller.state.next_die_id,
                    variant_card=controller.state.variant_cards.get(free_color),
                )
                controller.state.next_die_id += 1
                player.ready_dice.append(new_die)
                player.mark_ability_used()
                cipher_used = True
                controller.event_log.append(
                    f"{meta['name']} (Bot) used Prometheus Algorithmic Arbitrage: {free_color.value.capitalize()} Die at ${discounted_cost}."
                )
        elif p_mode in ("DIRTY_INCOME", 2):
            if player.secrets > controller.state.config.dirty_income_secret_cost:
                player.secrets -= controller.state.config.dirty_income_secret_cost
                player.money += controller.state.config.dirty_income_cash
                controller.state.staging_cup[CubeColor.BLACK] = (
                    controller.state.staging_cup.get(CubeColor.BLACK, 0)
                    + controller.state.config.dirty_income_black_cubes
                )
                player.total_dirty_income_taken += 1
                player.mark_ability_used()
                cipher_used = True
                controller.event_log.append(
                    f"{meta['name']} (Bot) used Prometheus Algorithmic Arbitrage: Backlash-free Dirty Income."
                )

    # 1. Dirty Income
    if (
        not (cipher_used and plan.cipher_mode in ("DIRTY_INCOME", 2))
        and plan.take_dirty_income
        and player.secrets > controller.state.config.dirty_income_secret_cost
        and len(player.ready_dice) >= 1
    ):
        player.secrets -= controller.state.config.dirty_income_secret_cost
        player.money += controller.state.config.dirty_income_cash
        controller.state.staging_cup[CubeColor.BLACK] = (
            controller.state.staging_cup.get(CubeColor.BLACK, 0)
            + controller.state.config.dirty_income_black_cubes
        )
        backlash_idx = plan.dirty_income_backlash_die_index
        if not (0 <= backlash_idx < len(player.ready_dice)):
            backlash_idx = 0
        demoted = player.ready_dice.pop(backlash_idx)
        player.unpatched_dice.append(demoted)
        meta["rolled_pool"] = [
            d for d in meta.get("rolled_pool", []) if d.die_id != demoted.die_id
        ]
        player.total_dirty_income_taken += 1
        controller.event_log.append(f"{meta['name']} (Bot) took Dirty Income: +$3, -1 Secret, +1 Black Cube.")

    # 2. Star Special Actions
    if plan.use_b2_secret and player.b2_available:
        cost = controller.state.config.b2_secret_cost
        cap = controller.state.config.b2_secret_cap
        if player.money >= cost and (cap is None or player.secrets < cap):
            player.money -= cost
            player.secrets += 1
            player.b2_available = False
            controller.event_log.append(f"{meta['name']} (Bot) used B2 Deep R&D: +1 Secret for ${cost}.")

    if plan.use_y1_secret and player.y1_available:
        if player.money >= 6:
            player.money -= 6
            player.secrets += 1
            player.y1_available = False
            controller.event_log.append(f"{meta['name']} (Bot) used Y1 Algorithmic Trading: +1 Secret for $6.")

    if plan.p1_cube_choice in (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN) and player.p1_available:
        controller.state.staging_cup[plan.p1_cube_choice] = controller.state.staging_cup.get(plan.p1_cube_choice, 0) + 1
        player.p1_available = False

    if plan.p3_cube_choice in (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN) and player.p3_available:
        if plan.p3_cube_choice.value == player.p3_available.value:
            p3_cost = controller.state.config.p3_cube_cash_cost
            if player.money >= p3_cost:
                player.money -= p3_cost
                controller.state.staging_cup[plan.p3_cube_choice] = controller.state.staging_cup.get(plan.p3_cube_choice, 0) + 1
                player.p3_available = None

    # 3. Patching
    patch_cash_cost = controller.state.config.patch_cash_cost
    for patch_act in plan.patch_actions:
        if not player.unpatched_dice:
            break
        idx = patch_act.get("die_index", 0)
        if not isinstance(idx, int) or not (0 <= idx < len(player.unpatched_dice)):
            idx = 0
        use_cash = bool(patch_act.get("use_cash", False))

        if use_cash:
            if player.money >= patch_cash_cost:
                player.money -= patch_cash_cost
                patched = player.unpatched_dice.pop(idx)
                player.ready_dice.append(patched)
        else:
            if player.patches >= controller.state.config.patch_token_cost:
                player.patches -= controller.state.config.patch_token_cost
                patched = player.unpatched_dice.pop(idx)
                player.ready_dice.append(patched)

    # White Hat Protocol Face 6 Resolution in Phase 3A (Spook & Phreaker)
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
            if resolve_spook_burn_notice(controller.engine or controller, player, plan.spook_burn_die_id):
                controller.event_log.append(
                    f"{meta['name']} (Bot) executed Spook Burn Notice on die {plan.spook_burn_die_id}."
                )
        elif is_phreaker and player.under_development_dice:
            diag_id = plan.phreaker_diagnostics_die_id
            if diag_id is None:
                diag_id = player.bot.choose_phreaker_jumper_diagnostics(player, controller.state, controller.rng)
            if diag_id is not None:
                face = resolve_phreaker_jumper_diagnostics(controller.engine or controller, player, diag_id, controller.rng)
                if face:
                    controller.event_log.append(
                        f"{meta['name']} (Bot) executed Phreaker Jumper Diagnostics: rolled '{face.name}'."
                    )

    # 4. Market Purchases
    purchases = meta.get("purchases_this_turn", 0)
    purchases_list = list(plan.market_purchases)
    if plan.buy_purple_reserve and DieColor.PURPLE not in purchases_list:
        purchases_list.append(DieColor.PURPLE)

    for color in purchases_list:
        if purchases >= controller.state.config.max_market_purchases_per_turn:
            break
        if color == DieColor.PURPLE:
            cost = player.get_purple_reserve_cost() if hasattr(player, "get_purple_reserve_cost") else 4
            if player.personal_purple_reserve > 0 and player.money >= cost:
                player.money -= cost
                player.personal_purple_reserve -= 1
                purchases += 1
                meta["purchases_this_turn"] = meta.get("purchases_this_turn", 0) + 1
                new_die = create_colored_die(
                    color=DieColor.PURPLE,
                    die_id=controller.state.next_die_id,
                    reserve_cost=cost,
                )
                controller.state.next_die_id += 1
                player.ready_dice.append(new_die)
                controller.event_log.append(f"{meta['name']} (Bot) procured Purple Die from Personal Reserve.")
        else:
            cost = controller.state.get_market_die_cost(color) if hasattr(controller.state, "get_market_die_cost") else (
                4 if color in (DieColor.RED, DieColor.GREEN) else 5
            )
            if controller.state.market.get(color, 0) > 0 and player.money >= cost:
                player.money -= cost
                controller.state.market[color] -= 1
                purchases += 1
                meta["purchases_this_turn"] = meta.get("purchases_this_turn", 0) + 1
                new_die = create_colored_die(
                    color=color,
                    die_id=controller.state.next_die_id,
                    variant_card=controller.state.variant_cards.get(color),
                )
                controller.state.next_die_id += 1
                player.ready_dice.append(new_die)
                controller.event_log.append(f"{meta['name']} (Bot) bought {color.value.capitalize()} Die.")

    # 5. Terminal Mat Track Upgrades (INV-UPGRADE-TRACK-01)
    upgrades = getattr(plan, "track_upgrades", [])
    for track in upgrades:
        cost = player.get_track_upgrade_cost(track)
        if cost is not None and player.research_tokens >= cost:
            player.upgrade_track(track)
            controller.event_log.append(f"{meta['name']} (Bot) upgraded {str(track).capitalize()} track.")

    # 6. Cryptographic Patent Filings (INV-PATENT-CONV-01)
    patent_filings = getattr(plan, "patent_filings", 0)
    while patent_filings > 0:
        cost = player.get_patent_cost()
        if player.research_tokens >= cost:
            player.file_patent()
            controller.event_log.append(f"{meta['name']} (Bot) filed Cryptographic Patent (+1 Secret).")
            patent_filings -= 1
        else:
            break



def buy_die(
    controller: GameController,
    player_id: int,
    color_str: str,
    use_cipher_ability: bool = False,
    use_prometheus_override: bool = False,
) -> Dict[str, Any]:
    if controller.subphase == "confirm_income":
        confirm_income(controller, player_id)

    if player_id != controller.active_player_index:
        raise ValueError(f"Not player {player_id}'s turn (current: {controller.active_player_index})")

    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]

    if player.is_patient_zero:
        raise ValueError("Eliminated players cannot perform operations")
    if meta["purchases_this_turn"] >= controller.state.config.max_market_purchases_per_turn:
        raise ValueError(f"Purchase limit reached ({controller.state.config.max_market_purchases_per_turn} dice per turn)")

    color = DieColor(color_str.lower())
    if color == DieColor.PURPLE:
        base_cost = player.get_purple_reserve_cost() if hasattr(player, "get_purple_reserve_cost") else (
            getattr(player.white_hat, "reserve_cost", 4) if getattr(player, "white_hat", None) else 4
        )
    else:
        base_cost = controller.state.get_market_die_cost(color) if hasattr(controller.state, "get_market_die_cost") else (
            4 if color in (DieColor.RED, DieColor.GREEN) else 5
        )

    cost = base_cost
    use_discount = use_cipher_ability or use_prometheus_override
    if use_discount:
        has_prometheus = bool(
            (player.company and player.company.code == CompanyCode.PROMETHEUS)
            or (player.archetype and player.archetype.code == ArchetypeCode.CIPHER)
        )
        if not has_prometheus:
            raise ValueError("Player does not have the Prometheus company override or Cipher archetype")
        if not player.is_ability_available():
            raise ValueError("Prometheus/Cipher ability is not available")
        cost = max(0, base_cost - controller.state.config.cipher_market_discount)

    if color == DieColor.PURPLE:
        # INV-PURPLE-03: Purchase from Personal Reserve
        if player.personal_purple_reserve <= 0:
            raise ValueError(f"Personal Purple Reserve is depleted (remaining: {player.personal_purple_reserve})")
        if player.money < cost:
            raise ValueError(f"Insufficient funds: Purple Reserve die costs ${cost}, but player only has ${player.money}")

        player.money -= cost
        player.personal_purple_reserve -= 1
        meta["purchases_this_turn"] += 1

        new_die = create_colored_die(
            color=DieColor.PURPLE,
            die_id=controller.state.next_die_id,
            reserve_cost=player.get_purple_reserve_cost() if hasattr(player, "get_purple_reserve_cost") else 4,
        )
        controller.state.next_die_id += 1
        player.ready_for_release_dice.append(new_die)

        if use_discount:
            player.mark_ability_used()
            controller.event_log.append(
                f"{meta['name']} used Prometheus Algorithmic Arbitrage to procure a Purple Specialist Die from Personal Reserve for ${cost}! (Reserve remaining: {player.personal_purple_reserve})."
            )
        else:
            controller.event_log.append(
                f"{meta['name']} procured a Purple Specialist Die from Personal Reserve for ${cost}. (Reserve remaining: {player.personal_purple_reserve})."
            )
        return controller.get_full_state()

    if controller.state.market.get(color, 0) <= 0:
        raise ValueError(f"Market stock for {color.value} is depleted")
    if player.money < cost:
        raise ValueError(f"Insufficient funds: die costs ${cost}, but player only has ${player.money}")

    player.money -= cost
    controller.state.market[color] -= 1
    meta["purchases_this_turn"] += 1

    new_die = create_colored_die(
        color=color,
        die_id=controller.state.next_die_id,
        variant_card=controller.state.variant_cards.get(color),
    )
    controller.state.next_die_id += 1
    player.ready_dice.append(new_die)

    if use_discount:
        player.mark_ability_used()
        controller.event_log.append(
            f"{meta['name']} used Prometheus Algorithmic Arbitrage to acquire a {color.value.capitalize()} Die at a ${controller.state.config.cipher_market_discount} discount (${cost})! (Stock remaining: {controller.state.market[color]})."
        )
    else:
        controller.event_log.append(
            f"{meta['name']} purchased a {color.value.capitalize()} Die for ${cost}. (Stock remaining: {controller.state.market[color]})."
        )
    return controller.get_full_state()


def spook_burn(
    controller: GameController,
    player_id: int,
    die_id: int,
) -> Dict[str, Any]:
    """Human action: Spook burns 1 owned colored die for +1 Secret."""
    if controller.subphase == "confirm_income":
        confirm_income(controller, player_id)

    if player_id != controller.active_player_index:
        raise ValueError(f"Not player {player_id}'s turn (current: {controller.active_player_index})")

    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]

    if player.is_patient_zero:
        raise ValueError("Eliminated players cannot perform operations")
    has_spook = bool(
        (player.white_hat and player.white_hat.code == WhiteHatCode.SPOOK)
        or (player.archetype and player.archetype.code == ArchetypeCode.SPOOK)
    )
    if not has_spook:
        raise ValueError("Player does not have the Spook white hat dossier or archetype")

    success = resolve_spook_burn_notice(controller.engine or controller, player, die_id)
    if not success:
        raise ValueError(f"Colored die {die_id} not found among owned dice to burn")

    controller.event_log.append(
        f"{meta['name']} executed Spook Burn Notice, burning die {die_id} to market for +1 Corporate Secret."
    )
    return controller.get_full_state()


def phreaker_diagnostics(
    controller: GameController,
    player_id: int,
    die_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Human action: Phreaker rolls 1 die in Under Development for diagnostics."""
    if controller.subphase == "confirm_income":
        confirm_income(controller, player_id)

    if player_id != controller.active_player_index:
        raise ValueError(f"Not player {player_id}'s turn (current: {controller.active_player_index})")

    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]

    if player.is_patient_zero:
        raise ValueError("Eliminated players cannot perform operations")
    has_phreaker = bool(
        (player.white_hat and player.white_hat.code == WhiteHatCode.PHREAKER)
        or (player.archetype and player.archetype.code == ArchetypeCode.PHREAKER)
    )
    if not has_phreaker:
        raise ValueError("Player does not have the Phreaker white hat dossier or archetype")

    face = resolve_phreaker_jumper_diagnostics(controller.engine or controller, player, die_id, controller.rng)
    if face is None:
        raise ValueError("No dice available in Under Development for diagnostics")

    controller.event_log.append(
        f"{meta['name']} executed Phreaker Jumper Diagnostics, rolling face '{face.name}' (money: +${face.money}, patches: +{face.patches} 🔧)."
    )
    return controller.get_full_state()



def patch_die(controller: GameController, player_id: int, die_index: int, use_cash: bool) -> Dict[str, Any]:
    """Human action: patches an unpatched die back to the ready zone."""
    if controller.phase != 3:
        raise ValueError(f"Cannot patch dice in phase {controller.phase}")
    if player_id != controller.active_player_index:
        raise ValueError(f"Not player {player_id}'s turn (current: {controller.active_player_index})")

    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]

    if player.is_patient_zero:
        raise ValueError("Eliminated players cannot perform operations")
    if not (0 <= die_index < len(player.unpatched_dice)):
        raise ValueError(f"Invalid die_index {die_index} in unpatched zone (size: {len(player.unpatched_dice)})")

    if use_cash:
        raise ValueError("Cash patching has been abolished in v0.22.0. Use Fast-Patch with 1 🔧.")

    if player.patches < controller.state.config.patch_token_cost:
        raise ValueError(f"Insufficient patch tokens: costs {controller.state.config.patch_token_cost} 🔧, player has {player.patches} 🔧")
    player.patches -= controller.state.config.patch_token_cost
    cost_desc = "1 🔧 token"

    patched_die = player.unpatched_dice.pop(die_index)
    player.ready_dice.append(patched_die)
    meta["rolled_pool"] = [
        d for d in meta.get("rolled_pool", []) if d.die_id != patched_die.die_id
    ]

    controller.event_log.append(
        f"{meta['name']} patched {patched_die.color.value.capitalize()} Die using {cost_desc}."
    )
    return controller.get_full_state()



def take_cipher_arbitrage(
    controller: GameController,
    player_id: int,
) -> Dict[str, Any]:
    """Executes Prometheus Algorithmic Arbitrage mode 2: immediate cash arbitrage payout."""
    if controller.phase != 3:
        raise ValueError(f"Cannot use Prometheus/Cipher ability in phase {controller.phase}")
    if player_id != controller.active_player_index:
        raise ValueError(f"Not player {player_id}'s turn (current: {controller.active_player_index})")

    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]

    if player.is_patient_zero:
        raise ValueError("Eliminated players cannot perform operations")
    has_prometheus = bool(
        (player.company and player.company.code == CompanyCode.PROMETHEUS)
        or (player.archetype and player.archetype.code == ArchetypeCode.CIPHER)
    )
    if not has_prometheus:
        raise ValueError("Player does not have the Prometheus company override or Cipher archetype")
    if not player.is_ability_available():
        raise ValueError("Prometheus/Cipher ability is not available")

    player.money += controller.state.config.cipher_arbitrage_cash
    player.mark_ability_used()
    controller.event_log.append(
        f"{meta['name']} used Prometheus Algorithmic Arbitrage: gained +${controller.state.config.cipher_arbitrage_cash} cash arbitrage payout."
    )
    return controller.get_full_state()


take_prometheus_arbitrage = take_cipher_arbitrage


def take_dirty_income(
    controller: GameController,
    player_id: int,
    backlash_die_index: int = 0,
    use_cipher_ability: bool = False,
    backlash_die_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Human action: corrupts the Rogue Agent ('Dirty Income') for quick cash (or backlash-free via Cipher)."""
    if use_cipher_ability:
        return take_cipher_arbitrage(controller, player_id)

    if not controller.state.config.dirty_income_enabled:
        raise ValueError("Dirty Income has been eliminated in v0.16.0")

    if controller.phase != 3:
        raise ValueError(f"Cannot take dirty income in phase {controller.phase}")
    if player_id != controller.active_player_index:
        raise ValueError(f"Not player {player_id}'s turn (current: {controller.active_player_index})")

    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]

    if player.is_patient_zero:
        raise ValueError("Eliminated players cannot perform operations")
    if meta["dirty_income_taken_this_turn"]:
        raise ValueError("Dirty Income has already been taken this turn (limit 1x per turn)")

    # Precondition checks per RULES.md Section 4 Phase 3 Step 3:
    if player.secrets <= controller.state.config.dirty_income_secret_cost:
        raise ValueError(
            f"Cannot take Dirty Income with {player.secrets} Secret(s) (must have strictly > {controller.state.config.dirty_income_secret_cost})"
        )
    if len(player.ready_dice) < 1:
        raise ValueError("Cannot take Dirty Income: must have at least 1 Ready die for Technical Debt Backlash")

    backlash_die: Optional[Die] = None
    if backlash_die_id is not None:
        for d in player.ready_dice:
            if d.die_id == backlash_die_id:
                backlash_die = d
                break
        if backlash_die is None:
            raise ValueError(f"Die with die_id {backlash_die_id} is not in player's ready pool")
    else:
        if not (0 <= backlash_die_index < len(player.ready_dice)):
            backlash_die_index = 0
        backlash_die = player.ready_dice[backlash_die_index]

    # Execute Dirty Income
    player.secrets -= controller.state.config.dirty_income_secret_cost
    player.money += controller.state.config.dirty_income_cash
    controller.state.staging_cup[CubeColor.BLACK] = (
        controller.state.staging_cup.get(CubeColor.BLACK, 0)
        + controller.state.config.dirty_income_black_cubes
    )

    # Technical Debt Backlash: demote chosen ready die to unpatched
    assert backlash_die is not None
    player.ready_dice.remove(backlash_die)
    player.unpatched_dice.append(backlash_die)
    meta["rolled_pool"] = [
        d for d in meta.get("rolled_pool", []) if d.die_id != backlash_die.die_id
    ]

    meta["dirty_income_taken_this_turn"] = True
    player.total_dirty_income_taken += 1

    controller.event_log.append(
        f"{meta['name']} took Dirty Income: gained +${controller.state.config.dirty_income_cash}, paid 1 Secret, added 1 Black Cube to Staging Cup. Backlash demoted {backlash_die.color.value.capitalize()} Die."
    )
    return controller.get_full_state()



def use_phreaker_ability(
    controller: GameController,
    player_id: int,
    count: int = 1,
    die_index: int = 0,
    die_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Human action: moves 1 die from Glitched directly to Ready for Release for free using Omnidyne Magnetic Splice (v0.22.0)."""
    if controller.phase != 3:
        raise ValueError(f"Cannot use Omnidyne/Phreaker ability in phase {controller.phase}")
    if player_id != controller.active_player_index:
        raise ValueError(f"Not player {player_id}'s turn (current: {controller.active_player_index})")

    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]
    active_ver = controller.state.active_version.version_str if (controller.state and controller.state.active_version) else None

    if player.is_patient_zero:
        raise ValueError("Eliminated players cannot perform operations")
    has_omnidyne = bool(
        (player.company and player.company.code == CompanyCode.OMNIDYNE)
        or (player.archetype and player.archetype.code == ArchetypeCode.PHREAKER)
    )
    if not has_omnidyne:
        raise ValueError("Player does not have the Omnidyne company override or Phreaker archetype")
    if not player.is_ability_available(active_ver):
        raise ValueError("Omnidyne/Phreaker ability is not available")
    if count < 1:
        raise ValueError("count must be at least 1")

    source_pool = player.glitched_dice if player.glitched_dice else player.unpatched_dice
    if not source_pool:
        raise ValueError("No glitched dice available to splice")

    repaired: Optional[Die] = None
    if die_id is not None:
        for d in source_pool:
            if d.die_id == die_id:
                repaired = d
                break
        if repaired is None:
            raise ValueError(f"Die with die_id {die_id} is not in glitched zone")
        source_pool.remove(repaired)
    else:
        if not (0 <= die_index < len(source_pool)):
            raise ValueError(f"Invalid die_index {die_index} in glitched zone")
        repaired = source_pool.pop(die_index)

    repaired.production_role = None
    repaired.is_locked = False
    repaired.chosen_choice_index = None
    repaired.current_face = None
    player.ready_for_release_dice.append(repaired)

    player.mark_ability_used(active_ver)
    controller.event_log.append(
        f"{meta['name']} activated Omnidyne Magnetic Splice: spliced {repaired.color.value.capitalize()} Die directly to Ready for Release for free."
    )
    return controller.get_full_state()


use_omnidyne_override = use_phreaker_ability


def fast_patch(
    controller: GameController,
    player_id: int,
    die_ids: Optional[List[int]] = None,
    die_indices: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """Human action: spends 1 🔧 per die to accelerate dice from glitched_dice to scanned_dice."""
    if controller.phase != 3:
        raise ValueError(f"Cannot fast-patch in phase {controller.phase}")
    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]
    if player.is_patient_zero:
        raise ValueError("Eliminated players cannot perform operations")

    targets: List[Die] = []
    if die_ids is not None:
        for d_id in die_ids:
            match = next((d for d in player.glitched_dice if d.die_id == d_id), None)
            if match and match not in targets:
                targets.append(match)
    elif die_indices is not None:
        for idx in die_indices:
            if 0 <= idx < len(player.glitched_dice):
                d = player.glitched_dice[idx]
                if d not in targets:
                    targets.append(d)

    if not targets:
        raise ValueError("No valid glitched dice selected for fast-patching")
    if player.patches < len(targets):
        raise ValueError(f"Not enough patches: have {player.patches}, need {len(targets)}")

    for d in targets:
        player.glitched_dice.remove(d)
        d.production_role = None
        d.is_locked = False
        d.chosen_choice_index = None
        d.current_face = None
        player.scanned_dice.append(d)
        player.patches -= 1

    controller.event_log.append(
        f"{meta['name']} fast-patched {len(targets)} die/dice from Glitched to Scanned for {len(targets)} 🔧."
    )
    return controller.get_full_state()



def use_acoustic_ability(controller: GameController, player_id: int, chosen_color_str: str) -> Dict[str, Any]:
    """Human action: activates Aegis Baffle Echo to remove 1 exited attack cube."""
    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]

    if player.is_patient_zero:
        raise ValueError("Eliminated players cannot use abilities")
    has_aegis = bool(
        (player.company and player.company.code == CompanyCode.AEGIS)
        or (player.archetype and player.archetype.code == ArchetypeCode.ACOUSTIC)
    )
    if not has_aegis:
        raise ValueError("Player does not have the Aegis company override or Acoustic archetype")
    if not player.is_ability_available():
        raise ValueError("Aegis/Acoustic ability is not available")

    chosen_color = CubeColor(chosen_color_str.lower())
    if chosen_color not in (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN):
        raise ValueError(f"Invalid attack cube color: {chosen_color_str}")

    if not controller.last_compile_result:
        raise ValueError("No compile drop has occurred yet")

    exited = controller.last_compile_result.get("exited_cubes", {})
    if exited.get(chosen_color.value, 0) <= 0:
        raise ValueError(f"No {chosen_color.value} cubes exited in the last compile drop")

    # In v0.13.0: Exited cubes remain in tray and recycle as normal.
    # Player ignores 1 cube of that color (mitigates damage for self)
    if chosen_color == CubeColor.BLUE:
        player.secrets = min(10, player.secrets + 1)
    elif chosen_color == CubeColor.RED:
        player.money += 1
    elif chosen_color == CubeColor.GREEN and player.unpatched_dice:
        restored = player.unpatched_dice.pop()
        player.ready_dice.append(restored)

    player.mark_ability_used()
    controller.event_log.append(
        f"{meta['name']} activated Aegis Baffle Echo: ignored 1 {chosen_color.value} cube for self."
    )
    return controller.get_full_state()


use_aegis_override = use_acoustic_ability


def use_spook_ability(controller: GameController, player_id: int, dollars: int = 0) -> Dict[str, Any]:
    """Human action: activates DTO Slush Fund (v0.13.0: absorbs up to 2 secrets free + optional cash)."""
    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]

    if player.is_patient_zero:
        raise ValueError("Eliminated players cannot use abilities")
    has_dto = bool(
        (player.company and player.company.code == CompanyCode.DTO)
        or (player.archetype and player.archetype.code == ArchetypeCode.SPOOK)
    )
    if not has_dto:
        raise ValueError("Player does not have the DTO company override or Spook archetype")
    if not player.is_ability_available():
        raise ValueError("DTO/Spook ability is not available")
    if dollars < 0:
        raise ValueError("dollars must be non-negative")

    # In v0.13.0: Absorb up to 2 secrets free, plus optional extra for $1 each
    free_secrets = 2
    cash_spent = max(0, min(dollars, player.money))
    player.money -= cash_spent
    total_secrets_absorbed = free_secrets + cash_spent
    player.secrets = min(10, player.secrets + total_secrets_absorbed)
    player.mark_ability_used()
    controller.event_log.append(
        f"{meta['name']} activated DTO Slush Fund: absorbed {total_secrets_absorbed} secrets ({free_secrets} free, ${cash_spent} cash)."
    )
    return controller.get_full_state()


use_dto_override = use_spook_ability



def execute_star_action(
    controller: GameController,
    player_id: int,
    action_type: str,
    cube_color: Optional[str] = None,
) -> Dict[str, Any]:
    """Human action: executes rolled Star ability during Phase 3."""
    if controller.phase != 3:
        raise ValueError(f"Cannot execute star actions in phase {controller.phase}")
    if player_id != controller.active_player_index:
        raise ValueError(f"Not player {player_id}'s turn")

    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]

    if action_type == "B2":
        if not player.b2_available:
            raise ValueError("B2 Deep R&D Vault ability is not available this turn")
        cost = controller.state.config.b2_secret_cost
        cap = controller.state.config.b2_secret_cap
        if player.money < cost:
            raise ValueError(f"B2 requires ${cost} cash")
        if cap is not None and player.secrets >= cap:
            raise ValueError(f"Secrets already at maximum capacity ({cap})")
        player.money -= cost
        player.secrets += 1
        player.b2_available = False
        controller.event_log.append(f"{meta['name']} activated B2 Deep R&D Vault: +1 Corporate Secret for ${cost}.")

    elif action_type == "Y1":
        if not player.y1_available:
            raise ValueError("Y1 Algorithmic Trading ability is not available this turn")
        if player.money < 6:
            raise ValueError("Y1 requires $6 cash ($4 roll refund + $2 secret fee)")
        player.money -= 6
        player.secrets += 1
        player.y1_available = False
        controller.event_log.append(f"{meta['name']} activated Y1 Algorithmic Trading: converted $6 into +1 Secret.")

    elif action_type == "P1":
        if not player.p1_available:
            raise ValueError("P1 Zero-Day Injection ability is not available this turn")
        if not cube_color or cube_color.lower() not in ("red", "blue", "green"):
            raise ValueError("P1 requires selecting an attack cube color (red, blue, or green)")
        chosen = CubeColor(cube_color.lower())
        controller.state.staging_cup[chosen] = controller.state.staging_cup.get(chosen, 0) + 1
        player.p1_available = False
        controller.event_log.append(f"{meta['name']} activated P1 Zero-Day: added 1 {chosen.value.capitalize()} Cube to Staging Cup.")

    elif action_type == "P3":
        if not player.p3_available:
            raise ValueError("P3 Packet Deflection ability is not available this turn")
        blocked_color = player.p3_available.value
        if cube_color and cube_color.lower() != blocked_color:
            raise ValueError(f"P3 must add a cube matching the blocked color ({blocked_color})")
        cost = controller.state.config.p3_cube_cash_cost
        if player.money < cost:
            raise ValueError(f"P3 requires ${cost} cash")
        player.money -= cost
        chosen = CubeColor(blocked_color)
        controller.state.staging_cup[chosen] = controller.state.staging_cup.get(chosen, 0) + 1
        player.p3_available = None
        controller.event_log.append(f"{meta['name']} activated P3 Packet Deflection: paid ${cost} to add 1 {chosen.value.capitalize()} Cube to Staging Cup.")

    else:
        raise ValueError(f"Unsupported star action type: {action_type}")

    return controller.get_full_state()



def system_reboot(controller: GameController, player_id: int) -> Dict[str, Any]:
    """Deprecated in v0.22.0. Soft-locks are eliminated by the CI/CD conveyor."""
    raise ValueError("System Reboot has been deprecated in v0.22.0. Soft-locks are eliminated by the CI/CD conveyor.")



def end_turn(controller: GameController, player_id: int) -> Dict[str, Any]:
    """Human action: finishes Phase 3 operations and advances clockwise."""
    if controller.subphase == "confirm_income":
        confirm_income(controller, player_id)

    if controller.phase != 3:
        raise ValueError(f"Cannot end turn in phase {controller.phase}")
    if player_id != controller.active_player_index:
        raise ValueError(f"Not player {player_id}'s turn (current: {controller.active_player_index})")

    meta = controller.player_meta[player_id]
    controller.event_log.append(f"{meta['name']} ended operations turn.")

    if controller.phase3_turn_queue and controller.phase3_turn_queue[0] == player_id:
        controller.phase3_turn_queue.pop(0)

    # Advance to next turn (or complete round)
    advance_phase3_turns(controller)
    return controller.get_full_state()


def upgrade_hardware_track(
    controller: GameController,
    player_id: int,
    track_type: str,
) -> Dict[str, Any]:
    """Human action: Upgrades the specified terminal mat hardware track (INV-UPGRADE-TRACK-01)."""
    if controller.subphase == "confirm_income":
        confirm_income(controller, player_id)

    if controller.phase != 3:
        raise ValueError(f"Cannot upgrade hardware tracks in phase {controller.phase}")
    if player_id != controller.active_player_index:
        raise ValueError(f"Not player {player_id}'s turn (current: {controller.active_player_index})")

    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]

    if player.is_patient_zero:
        raise ValueError("Eliminated players cannot upgrade hardware tracks")

    t = str(track_type).upper().strip()
    cost = player.get_track_upgrade_cost(t)
    if cost is None:
        raise ValueError(f"Track {track_type} is already at maximum level")
    if player.research_tokens < cost:
        raise ValueError(f"Insufficient research tokens: need {cost} 🔬, have {player.research_tokens} 🔬")

    success = player.upgrade_track(t)
    if not success:
        raise ValueError(f"Failed to upgrade track {track_type}")

    new_level = getattr(player, f"{t.lower()}_level", 1)
    controller.event_log.append(
        f"{meta['name']} upgraded {t.capitalize()} Track to Level {new_level} for {cost} 🔬."
    )
    return controller.get_full_state()


def file_cryptographic_patent(
    controller: GameController,
    player_id: int,
) -> Dict[str, Any]:
    """Human action: Files a Cryptographic Patent for +1 Corporate Secret (INV-PATENT-CONV-01)."""
    if controller.subphase == "confirm_income":
        confirm_income(controller, player_id)

    if controller.phase != 3:
        raise ValueError(f"Cannot file cryptographic patents in phase {controller.phase}")
    if player_id != controller.active_player_index:
        raise ValueError(f"Not player {player_id}'s turn (current: {controller.active_player_index})")

    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]

    if player.is_patient_zero:
        raise ValueError("Eliminated players cannot file cryptographic patents")

    cost = player.get_patent_cost()
    if player.research_tokens < cost:
        raise ValueError(f"Insufficient research tokens: need {cost} 🔬, have {player.research_tokens} 🔬")

    success = player.file_patent()
    if not success:
        raise ValueError("Failed to file cryptographic patent")

    cash_note = " and +$1 cash" if player.patent_level >= 2 else ""
    controller.event_log.append(
        f"{meta['name']} filed Cryptographic Patent (+1 Secret{cash_note}) for {cost} 🔬."
    )
    return controller.get_full_state()


