"""Phase 6: Operations (Operations Turns, clockwise from the First Player).

Buy dice (limit 2; purchases go directly to Ready for Release, O3), Terminal Hardware Track upgrades,
Patent Filings, paid ``★`` actions (B2, Y1, P1, P3) and Prometheus *Algorithmic Arbitrage*; then pass
the First Player Marker.

v0.36.0 (``patents_mode=SHARE_REGAIN``): the Public Relations Track replaces Patent Filing with a Market Share
regain step (research per +1, capped per Operations Turn by level); Ad Campaign (R2) is a paid ``★`` action.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

from sim.config import CubeColor, DieColor
from sim.entities import has_company_override, has_signature_protocol, legacy_bridge_enabled
from sim.entities import ArchetypeCode, CompanyCode, WhiteHatCode, create_colored_die

if TYPE_CHECKING:
    from sim.bots.base import BaseBot, Phase3ActionPlan
    from sim.engine.core import GameEngine
    from sim.engine.state import GameState, PlayerState


def resolve_operations_plan(bot: BaseBot, player_state: PlayerState, state: GameState, rng: random.Random) -> Phase3ActionPlan:
    """Resolves the bot's Operations plan, honouring both the v0.34 name (``take_operations_actions``)
    and the deprecated v0.33 name (``take_phase3_actions``): instance monkeypatches first, then the
    most-derived class that defines either name."""
    inst = vars(bot) if hasattr(bot, "__dict__") else {}
    plan = _resolve_raw_operations_plan(bot, player_state, state, rng)
    from sim.bots.research_policy import apply_research_policy

    plan = apply_research_policy(bot, plan, player_state, state, rng)
    if getattr(state.config, "is_market_share", False):
        from sim.bots.market_share_policy import apply_market_share_policy

        plan = apply_market_share_policy(bot, plan, player_state, state)
    if getattr(state.config, "secret_face_enabled", False):
        from sim.bots.secret_face_policy import adjust_purchases

        plan = adjust_purchases(bot, plan, player_state, state)
    return plan


def _resolve_raw_operations_plan(bot: BaseBot, player_state: PlayerState, state: GameState, rng: random.Random) -> Phase3ActionPlan:
    inst = vars(bot) if hasattr(bot, "__dict__") else {}
    if "take_operations_actions" in inst:
        return inst["take_operations_actions"](player_state, state, rng)
    if "take_phase3_actions" in inst:
        return inst["take_phase3_actions"](player_state, state, rng)
    for klass in type(bot).__mro__:
        if "take_operations_actions" in klass.__dict__:
            return bot.take_operations_actions(player_state, state, rng)
        if "take_phase3_actions" in klass.__dict__:
            return klass.__dict__["take_phase3_actions"](bot, player_state, state, rng)
    return bot.take_operations_actions(player_state, state, rng)


def execute_player_operations_turn(
    engine: GameEngine,
    player: PlayerState,
    plan: Any,
    *,
    collect_income: bool = False,
    resolve_signature_protocols: bool = False,
) -> None:
    """One Operations Turn. ``collect_income=True`` and ``resolve_signature_protocols=True`` reproduce the
    legacy v0.33 Part 3A turn exactly; the six-phase path passes ``False`` / ``False`` (Phase 3 handles both)."""
    from sim.engine.phase3_income import (
        collect_player_production_income,
        resolve_phreaker_jumper_diagnostics,
        resolve_spook_burn_notice,
    )

    active_ver = engine.state.active_version.version_str
    v035 = bool(getattr(engine.config, "is_v035_tracks", False))
    purple_ok = bool(getattr(engine.config, "purple_purchasable", True))

    # v0.35.0: research first - track upgrades step by step, each Breakthrough resolving immediately
    # (INV-RT-BT-IMMEDIATE-01 / INV-RT-BT-ORDER-01), then Patent filings at the post-upgrade rate.
    share_regain = bool(getattr(engine.config, "is_share_regain", False))
    if v035:
        execute_track_upgrades(engine, player, plan)
        if share_regain:
            _reject_patent_filings(player, getattr(plan, "patent_filings", 0))
            execute_share_regain(engine, player, getattr(plan, "share_regain", 0))
        else:
            execute_patent_filings(player, getattr(plan, "patent_filings", 0))

    # 1. Collect Income from ALL surviving dice in in_production_dice (legacy v0.33 only)
    if collect_income:
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
    is_prometheus = has_company_override(player, CompanyCode.PROMETHEUS, legacy_bridge_enabled(engine)) and player.is_ability_available(active_ver)
    use_prom = bool(getattr(plan, "use_prometheus_override", False) or getattr(plan, "use_cipher_ability", False))
    prom_mode = getattr(plan, "prometheus_mode", None) or getattr(plan, "cipher_mode", None)
    prom_color = getattr(plan, "prometheus_discount_die_color", None) or getattr(plan, "cipher_free_die_color", None)

    if prom_color == DieColor.PURPLE and not purple_ok:
        _log_rejected_purple(player)
        prom_color = None  # v0.35.0: Algorithmic Arbitrage discounts Central Market dice only
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
                    face_profile=engine.config.die_face_profile,
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
                face_profile=engine.config.die_face_profile,
                color=free_color,
                die_id=engine.state.next_die_id,
                variant_card=engine.state.variant_cards.get(free_color),
            )
            engine.state.next_die_id += 1
            player.ready_for_release_dice.append(new_die)
            player.record_purchase(free_color)
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
            player.gain_secrets(1, "b2")
            player.b2_available = False

    if plan.use_y1_secret and player.y1_available:
        # Reverses +$4 from P1 and pays $2 for +1 Secret (net -$2)
        if player.money >= 6:
            player.money -= 6
            player.gain_secrets(1, "y1")
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

    # Operative Protocol Face 6 Resolution in Phase 3A (Spook & Phreaker) - legacy v0.33 only
    has_purple_star = resolve_signature_protocols and (player.purple_star_available or any(
        (d.effective_face or d.current_face)
        and (d.effective_face or d.current_face).is_star
        and (d.effective_face or d.current_face).star_code == "PURPLE_STAR"
        for d in player.in_production_dice
    ))
    if has_purple_star:
        is_spook = has_signature_protocol(player, WhiteHatCode.SPOOK, legacy_bridge_enabled(engine))
        is_phreaker = has_signature_protocol(player, WhiteHatCode.PHREAKER, legacy_bridge_enabled(engine))
        if is_spook and plan.spook_burn_die_id is not None:
            resolve_spook_burn_notice(engine, player, plan.spook_burn_die_id)
        elif is_phreaker:
            diag_id = plan.phreaker_diagnostics_die_id
            if diag_id is None and player.under_development_dice:
                diag_id = player.bot.choose_phreaker_jumper_diagnostics(player, engine.state, engine.rng)
            # Always resolve diagnostics even if under_development_dice is empty (triggers fallback)
            resolve_phreaker_jumper_diagnostics(engine, player, diag_id, engine.rng)

    # 3b. Ad Campaign (R2, v0.36.0): pay $X -> +Market Share; outside the Public Relations cap (INV-MS-R2-01)
    execute_ad_campaigns(engine, player, getattr(plan, "use_r2_share", 0))

    # 4. Market Purchases (Limit 2 dice per turn; deliver directly to ready_for_release_dice)
    purchased_count = 1 if prometheus_discount_applied else 0
    purchases_list = list(plan.market_purchases)
    if plan.buy_purple_reserve and DieColor.PURPLE not in purchases_list:
        purchases_list.append(DieColor.PURPLE)
    if not purple_ok and DieColor.PURPLE in purchases_list:
        # v0.35.0 (INV-RT-NO-PURPLE-BUY-01): Purple is not purchasable; ignored, purchase limit untouched.
        for _ in range(purchases_list.count(DieColor.PURPLE)):
            _log_rejected_purple(player)
        purchases_list = [c for c in purchases_list if c != DieColor.PURPLE]

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
                    face_profile=engine.config.die_face_profile,
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
                    face_profile=engine.config.die_face_profile,
                    color=color,
                    die_id=engine.state.next_die_id,
                    variant_card=engine.state.variant_cards.get(color),
                )
                engine.state.next_die_id += 1
                player.ready_for_release_dice.append(new_die)
                player.record_purchase(color)

    # Unused Ad Campaign actions are lost at the end of the Operations Turn
    player.r2_actions_available = 0

    if v035:
        return

    # 5. Terminal Mat Track Upgrades (INV-UPGRADE-TRACK-01)
    upgrades = getattr(plan, "track_upgrades", [])
    for track in upgrades:
        cost = player.get_track_upgrade_cost(track)
        if cost is not None and player.research_tokens >= cost:
            player.upgrade_track(track)

    # 6. Cryptographic Patent Filings (INV-PATENT-CONV-01) / v0.36 Public Relations regain
    patent_filings = getattr(plan, "patent_filings", 0)
    if share_regain:
        _reject_patent_filings(player, patent_filings)
        execute_share_regain(engine, player, getattr(plan, "share_regain", 0))
        patent_filings = 0
    while patent_filings > 0:
        cost = player.get_patent_cost()
        if player.research_tokens >= cost:
            player.file_patent()
            patent_filings -= 1
        else:
            break


def _reject_patent_filings(player: PlayerState, filings: int) -> None:
    """Under the Public Relations Track Patent Filing does not exist: planned filings are ignored and logged."""
    if filings and filings > 0:
        player.rejected_patent_filings = getattr(player, "rejected_patent_filings", 0) + int(filings)


def execute_share_regain(engine: GameEngine, player: PlayerState, wanted: int) -> int:
    """Public Relations Track Phase 6 step: regain Market Share (INV-MS-REGAIN-01).

    Each +1 costs the research rate of the current level; at most ``cap[level]`` per Operations Turn; never
    above the maximum. Cap and cost are re-read per step at the post-upgrade level (E15).
    """
    cfg = engine.config
    player.regain_this_turn = 0
    done = 0
    if not cfg.is_share_regain or player.market_share is None:
        return 0
    while done < int(wanted or 0):
        lvl = player.patent_level
        cap = cfg.share_regain_cap_by_level[lvl]
        cost = cfg.share_regain_cost_by_level[lvl]
        if player.regain_this_turn >= cap or player.market_share >= player.market_share_max \
                or player.research_tokens < cost:
            break
        player.research_tokens -= cost
        player.research_spent_regain += cost
        player.change_market_share(+1, "regain")
        player.regain_this_turn += 1
        done += 1
    return done


def execute_ad_campaigns(engine: GameEngine, player: PlayerState, wanted: int) -> int:
    """Ad Campaign (R2): one paid action per R2 face In Production in Phase 3 (INV-MS-R2-01). Atomic at max."""
    cfg = engine.config
    used = 0
    wanted = int(wanted or 0)
    if not cfg.is_market_share or player.market_share is None:
        return 0
    while wanted > 0 and player.r2_actions_available > 0:
        if player.money >= cfg.r2_share_cost and player.market_share < player.market_share_max:
            player.money -= cfg.r2_share_cost
            player.change_market_share(+cfg.r2_share_gain, "r2")
            player.r2_uses += 1
            used += 1
        wanted -= 1
        player.r2_actions_available -= 1
    return used


def _log_rejected_purple(player: PlayerState) -> None:
    player.rejected_purple_purchases = getattr(player, "rejected_purple_purchases", 0) + 1


def execute_track_upgrades(engine: GameEngine, player: PlayerState, plan: Any) -> list:
    """Phase 6 Item 1: Pay and raise tracks step by step up to max_hardware_upgrades_per_turn.
    Each Breakthrough resolves immediately before the next step is paid (INV-RT-BT-IMMEDIATE-01).
    Excess requested upgrades beyond the per-turn limit are rejected and recorded in telemetry.
    """
    from sim.engine import research_tracks

    choices = getattr(plan, "breakthrough_choices", None) or {}
    done = []
    max_upgrades = getattr(engine.config, "max_hardware_upgrades_per_turn", 2)
    requested = list(getattr(plan, "track_upgrades", []) or [])

    for track in requested:
        # Check per-turn upgrade cap
        if len(done) >= max_upgrades:
            break

        t = research_tracks.normalize_track(track)
        if t not in research_tracks.LEVEL_ATTR:
            continue

        if not player.upgrade_track(t, round_number=engine.state.current_round):
            break

        lvl = research_tracks.level_of(player, t)
        done.append((t, lvl))

        if lvl in research_tracks.BREAKTHROUGH_LEVELS:
            choice = research_tracks.ask_breakthrough_choice(engine, player, t, lvl, choices)
            research_tracks.resolve_breakthrough(engine, player, t, lvl, choice)

    # Telemetry & error handling: record excess requested upgrades
    if len(requested) > max_upgrades:
        excess = len(requested) - max_upgrades
        player.excess_hardware_upgrades_requested = getattr(player, "excess_hardware_upgrades_requested", 0) + excess

    player.track_upgrades_this_round = getattr(player, "track_upgrades_this_round", []) + done
    return done


def execute_patent_filings(player: PlayerState, filings: int) -> int:
    filed = 0
    while filings > 0 and player.research_tokens >= player.get_patent_cost():
        player.file_patent()
        filings -= 1
        filed += 1
    return filed


def pass_first_player_marker(engine: GameEngine) -> None:
    """Pass the First Player Marker clockwise."""
    num_players = len(engine.state.players)
    engine.state.first_player_index = (engine.state.first_player_index + 1) % num_players


def execute_operations(engine: GameEngine) -> None:
    """Phase 6: Operations Turns clockwise from the First Player (survivors only), then pass the marker."""
    if engine.state.game_over:
        return
    num_players = len(engine.state.players)
    for offset in range(num_players):
        idx = (engine.state.first_player_index + offset) % num_players
        player = engine.state.players[idx]
        if player.is_patient_zero:
            continue
        plan = resolve_operations_plan(player.bot, player, engine.state, engine.rng)
        execute_player_operations_turn(engine, player, plan)
    pass_first_player_marker(engine)
