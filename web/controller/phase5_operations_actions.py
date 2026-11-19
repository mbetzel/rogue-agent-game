"""Web Phase 5: Operations (Operations Turns, clockwise from the First Player), then Phase 6: CI/CD Pipeline Shift.

v0.47.0 order (RULES.md Section 4, ``operations_before_pipeline_shift``).
"""

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
from sim.engine import research_tracks, vulnerability
from web.controller import phases
from sim.engine.phase6_operations import execute_share_regain, resolve_operations_plan
from sim.engine.state import ProductionRole
from sim.entities import has_company_override, has_signature_protocol, legacy_bridge_enabled
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

def enter_operations(controller: GameController) -> None:
    """Starts Phase 5: Operations Turns clockwise from the First Player."""
    controller.phase = phases.OPERATIONS
    controller.phase_name = phases.PHASE_NAMES[controller.phase]
    controller.subphase = "player_turn"
    num_players = len(controller.state.players)
    controller.operations_turn_queue = [
        (controller.state.first_player_index + offset) % num_players for offset in range(num_players)
    ]
    for pid, meta in controller.player_meta.items():
        meta["hired_contractors"] = 0
        player = controller.state.players[pid]
        ready_ids = {d.die_id for d in player.ready_dice}
        meta["rolled_pool"] = [d for d in meta.get("rolled_pool", []) if d.die_id in ready_ids]
    advance_operations_turns(controller)


def advance_operations_turns(controller: GameController) -> None:
    """Processes Operations Turns clockwise, automatically executing bots until a human turn or round end."""
    while controller.operations_turn_queue:
        next_pid = controller.operations_turn_queue[0]
        player = controller.state.players[next_pid]
        meta = controller.player_meta[next_pid]

        if player.is_patient_zero:
            controller.operations_turn_queue.pop(0)
            controller.event_log.append(f"{meta['name']} is Patient Zero (eliminated, skipping Operations).")
            continue

        controller.active_player_index = next_pid
        if meta["is_human"]:
            if meta.get("ops_turn_started_round") != controller.state.current_round:
                # Start of the Operations Turn (same resets as sim.engine.phase6_operations.execute_player_operations_turn)
                meta["ops_turn_started_round"] = controller.state.current_round
                meta["purchases_this_turn"] = 0
                meta["upgrades_this_turn"] = 0
                meta["dirty_income_taken_this_turn"] = False
                player.regain_this_turn = 0  # Public Relations Track: per-Operations-Turn cap
                player.scanned_dice_purchased_this_turn = 0
                player.pen_test_this_turn = 0
                freed = vulnerability.apply_l4_free(controller.engine, player)
                if freed:
                    controller.event_log.append(
                        f"{meta['name']} Pen Test Track Level 4: -{freed} Vulnerability (now {player.vulnerability})."
                    )
            return

        controller.operations_turn_queue.pop(0)
        meta["purchases_this_turn"] = 0
        meta["upgrades_this_turn"] = 0
        execute_bot_operations(controller, player, meta)

    # Every survivor has finished Phase 5 -> Phase 6: CI/CD Pipeline Shift
    from web.controller.phase6_pipeline_actions import enter_pipeline_shift

    enter_pipeline_shift(controller)


def execute_bot_operations(controller: GameController, player: PlayerState, meta: Dict[str, Any]) -> None:
    """Runs one bot Operations Turn through the engine (same fixed order as the simulation)."""
    plan: Phase3ActionPlan = resolve_operations_plan(player.bot, player, controller.state, controller.engine.rng)
    _execute_bot_operations_v035(controller, player, meta, plan)


def _execute_bot_operations_v035(controller: GameController, player: PlayerState, meta: Dict[str, Any], plan: Phase3ActionPlan) -> None:
    """v0.35.0: bot Operations Turns run through the engine (same fixed order as the simulation)."""
    from sim.engine.phase6_operations import execute_player_operations_turn

    money0, secrets0, research0 = player.money, player.secrets, player.research_tokens
    ms0, regain0, r2_0 = player.market_share, player.market_share_regained, player.r2_uses
    vuln0, pen0, l4_0 = player.vulnerability, player.pen_test_steps, player.pen_test_l4_free_uses
    bt0 = len(player.breakthroughs)
    dice0 = {d.die_id for d in player.ready_for_release_dice}
    lv0 = {t: getattr(player, a) for t, a in research_tracks.LEVEL_ATTR.items()}
    execute_player_operations_turn(controller.engine, player, plan)
    for t, a in research_tracks.LEVEL_ATTR.items():
        if getattr(player, a) != lv0[t]:
            controller.event_log.append(
                f"{meta['name']} upgraded the {research_tracks.track_display_name(controller.state.config, t)} to Level {getattr(player, a)}."
            )
    for b in player.breakthroughs[bt0:]:
        controller.event_log.append(
            f"{meta['name']} {_level_effect_label(b)} ({_track_label(controller, b.track)} L{b.level}): {_breakthrough_log(b)}.")
    new_dice = [d for d in player.ready_for_release_dice if d.die_id not in dice0]
    if new_dice:
        controller.event_log.append(
            f"{meta['name']} added {', '.join(d.color.value.capitalize() for d in new_dice)} to Ready for Release."
        )
    if player.market_share_regained > regain0:
        controller.event_log.append(
            f"{meta['name']} Public Relations Track: regained {player.market_share_regained - regain0} Market Share."
        )
    if player.pen_test_l4_free_uses > l4_0:
        controller.event_log.append(f"{meta['name']} Pen Test Track Level 4: -1 Vulnerability.")
    if player.pen_test_steps > pen0:
        controller.event_log.append(
            f"{meta['name']} Pen Test Track: -{player.pen_test_steps - pen0} Vulnerability."
        )
    if player.r2_uses > r2_0:
        controller.event_log.append(f"{meta['name']} Ad Campaign: +{player.r2_uses - r2_0} Market Share.")
    ms_note = f", Market Share {ms0} -> {player.market_share}" if ms0 is not None else ""
    controller.event_log.append(
        f"{meta['name']} finished Operations (${player.money - money0:+d}, {player.secrets - secrets0:+d} Secrets, "
        f"{player.research_tokens - research0:+d} 🔬{ms_note}, Vulnerability {vuln0} -> {player.vulnerability})."
    )


def _breakthrough_log(b: Any) -> str:
    text = {
        ("DEFENSE", 1): "Gain 1 Gray Legacy die",
        ("DEFENSE", 3): "Gain 1 Corporate Secret",
        ("DEFENSE", 4): "Pen Test limit 3; -1 Vulnerability free at the start of each later Operations Turn",
        ("TRIAGE", 1): "Gain 1 Gray Legacy die",
        ("TRIAGE", 3): "Gain 1 Corporate Secret",
        ("TRIAGE", 4): "Replace 1 Gray Legacy die with a Central Market colored die (free)",
        ("RELEASE", 1): "Gain 1 Gray Legacy die",
        ("RELEASE", 3): "Gain 1 Corporate Secret",
        ("RELEASE", 4): "Set 1 rolled Gray Legacy die to any printed face each Phase 1",
        ("PATENT", 1): "Gain $3",
        ("PATENT", 3): "Gain your 2nd Purple die",
        ("PATENT", 4): "Gain +2 Market Share",
    }.get((b.track, b.level), research_tracks.BREAKTHROUGH_TEXT.get((b.track, b.level), ""))
    if b.outcome == "TAKEN":
        if b.track == "TRIAGE" and b.detail.get("new_color"):
            paid = b.detail.get("paid", 0)
            return f"replaced a Gray Legacy die with a {b.detail.get('new_color', '').capitalize()} die" + (f" for ${paid}" if paid else "")
        return text
    return f"{text} - {b.outcome.lower()}"


def _require_no_pending_breakthrough(controller: GameController, player_id: int) -> None:
    pending = getattr(controller, "pending_breakthrough", {}) or {}
    if player_id in pending:
        raise ValueError("Resolve the pending Breakthrough before taking another operation")


def resolve_pending_breakthrough(
    controller: GameController,
    player_id: int,
    accept: bool = True,
    gray_die_id: Optional[int] = None,
    color: Optional[str] = None,
) -> Dict[str, Any]:
    """Human action: answers an optional Breakthrough / Capstone prompt (Triage: replace a Gray Legacy die)."""
    pending = getattr(controller, "pending_breakthrough", {}) or {}
    if player_id not in pending:
        raise ValueError("No Breakthrough is pending for this player")
    info = pending.pop(player_id)
    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]
    die_color = DieColor(str(color).lower()) if color else None
    choice = research_tracks.BreakthroughChoice(accept=bool(accept), gray_die_id=gray_die_id, color=die_color)
    rec = research_tracks.resolve_breakthrough(controller.engine, player, info["track"], info["level"], choice)
    if rec is not None:
        controller.event_log.append(
            f"{meta['name']} {_level_effect_label(rec)} ({_track_label(controller, rec.track)} L{rec.level}): {_breakthrough_log(rec)}."
        )
    return controller.get_full_state()


def buy_die(
    controller: GameController,
    player_id: int,
    color_str: str,
    use_cipher_ability: bool = False,
    use_prometheus_override: bool = False,
) -> Dict[str, Any]:
    if controller.phase != phases.OPERATIONS:
        raise ValueError(f"Cannot buy dice in phase {controller.phase}")
    if player_id != controller.active_player_index:
        raise ValueError(f"Not player {player_id}'s turn (current: {controller.active_player_index})")

    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]

    if player.is_patient_zero:
        raise ValueError("Eliminated players cannot perform operations")
    if meta["purchases_this_turn"] >= controller.state.config.max_market_purchases_per_turn:
        raise ValueError(f"Purchase limit reached ({controller.state.config.max_market_purchases_per_turn} dice per turn)")

    _require_no_pending_breakthrough(controller, player_id)
    color = DieColor(color_str.lower())
    if color == DieColor.PURPLE and not controller.state.config.purple_purchasable:
        raise ValueError("Purple dice cannot be purchased; your 2nd Purple die comes from the Public Relations Track Level 3 Breakthrough")
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
        has_prometheus = has_company_override(player, CompanyCode.PROMETHEUS, legacy_bridge_enabled(controller))
        if not has_prometheus:
            raise ValueError("Player does not have the Prometheus company override or Cipher archetype")
        if not player.is_ability_available(controller.state.active_version.version_str):
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
            face_profile=controller.state.config.die_face_profile,
            color=DieColor.PURPLE,
            die_id=controller.state.next_die_id,
            reserve_cost=player.get_purple_reserve_cost() if hasattr(player, "get_purple_reserve_cost") else 4,
        )
        controller.state.next_die_id += 1
        player.ready_for_release_dice.append(new_die)

        if use_discount:
            player.mark_ability_used(controller.state.active_version.version_str)
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
        face_profile=controller.state.config.die_face_profile,
        color=color,
        die_id=controller.state.next_die_id,
        variant_card=controller.state.variant_cards.get(color),
    )
    controller.state.next_die_id += 1
    if controller.state.config.purchased_dice_to_scanned:
        player.scanned_dice.append(new_die)  # v0.40+: bought dice go to the Scanned Box and graduate in Phase 6
        player.scanned_dice_purchased_this_turn += 1
    else:
        player.ready_dice.append(new_die)
    player.record_purchase(color)

    if use_discount:
        player.mark_ability_used(controller.state.active_version.version_str)
        controller.event_log.append(
            f"{meta['name']} used Prometheus Algorithmic Arbitrage to acquire a {color.value.capitalize()} Die at a ${controller.state.config.cipher_market_discount} discount (${cost})! (Stock remaining: {controller.state.market[color]})."
        )
    else:
        controller.event_log.append(
            f"{meta['name']} purchased a {color.value.capitalize()} Die for ${cost}. (Stock remaining: {controller.state.market[color]})."
        )
    return controller.get_full_state()


def spook_burn(controller: GameController, player_id: int, die_id: int) -> Dict[str, Any]:
    """Spook Burn Notice resolves in Phase 3: Income (records the target until the Phase 3 confirm)."""
    from web.controller.phase3_income_actions import record_spook_burn

    return record_spook_burn(controller, player_id, die_id)


def phreaker_diagnostics(controller: GameController, player_id: int, die_id: Optional[int] = None) -> Dict[str, Any]:
    """Phreaker Jumper Diagnostics resolves in Phase 3: Income (records the target until the Phase 3 confirm)."""
    from web.controller.phase3_income_actions import record_phreaker_diagnostics

    return record_phreaker_diagnostics(controller, player_id, die_id)


def take_cipher_arbitrage(
    controller: GameController,
    player_id: int,
) -> Dict[str, Any]:
    """Executes Prometheus Algorithmic Arbitrage mode 2: immediate cash arbitrage payout."""
    if controller.phase != phases.OPERATIONS:
        raise ValueError(f"Cannot use Prometheus/Cipher ability in phase {controller.phase}")
    if player_id != controller.active_player_index:
        raise ValueError(f"Not player {player_id}'s turn (current: {controller.active_player_index})")

    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]

    if player.is_patient_zero:
        raise ValueError("Eliminated players cannot perform operations")
    has_prometheus = has_company_override(player, CompanyCode.PROMETHEUS, legacy_bridge_enabled(controller))
    if not has_prometheus:
        raise ValueError("Player does not have the Prometheus company override or Cipher archetype")
    if not player.is_ability_available(controller.state.active_version.version_str):
        raise ValueError("Prometheus/Cipher ability is not available")

    player.money += controller.state.config.cipher_arbitrage_cash
    player.mark_ability_used(controller.state.active_version.version_str)
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

    if controller.phase != phases.OPERATIONS:
        raise ValueError(f"Cannot take dirty income in phase {controller.phase}")
    if player_id != controller.active_player_index:
        raise ValueError(f"Not player {player_id}'s turn (current: {controller.active_player_index})")

    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]

    if player.is_patient_zero:
        raise ValueError("Eliminated players cannot perform operations")
    if meta["dirty_income_taken_this_turn"]:
        raise ValueError("Dirty Income has already been taken this turn (limit 1x per turn)")

    # Precondition checks per RULES.md Section 4 Phase 5 (Operations):
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
    """Omnidyne Magnetic Splice resolves in Phase 5 step 1 (Emergency Hotfix & Magnetic Splice)."""
    from web.controller.phase6_pipeline_actions import record_magnetic_splice

    if count < 1:
        raise ValueError("count must be at least 1")
    return record_magnetic_splice(controller, player_id, die_id=die_id, die_index=die_index)


use_omnidyne_override = use_phreaker_ability


def use_acoustic_ability(controller: GameController, player_id: int, chosen_color_str: str) -> Dict[str, Any]:
    """Human action: activates Aegis Baffle Echo to remove 1 exited attack cube."""
    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]

    if player.is_patient_zero:
        raise ValueError("Eliminated players cannot use abilities")
    has_aegis = has_company_override(player, CompanyCode.AEGIS, legacy_bridge_enabled(controller))
    if not has_aegis:
        raise ValueError("Player does not have the Aegis company override or Acoustic archetype")
    if not player.is_ability_available(controller.state.active_version.version_str):
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

    player.mark_ability_used(controller.state.active_version.version_str)
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
    has_dto = has_company_override(player, CompanyCode.DTO, legacy_bridge_enabled(controller))
    if not has_dto:
        raise ValueError("Player does not have the DTO company override or Spook archetype")
    if controller.state.config.slush_fund_once_per_game:
        raise ValueError("Slush Fund is chosen when confirming Phase 4: Attack Resolution (use_slush_fund)")
    if not player.is_slush_fund_available(controller.state.active_version.version_str):
        raise ValueError("DTO/Spook ability is not available")
    if dollars < 0:
        raise ValueError("dollars must be non-negative")

    # In v0.13.0: Absorb up to 2 secrets free, plus optional extra for $1 each
    free_secrets = 2
    cash_spent = max(0, min(dollars, player.money))
    player.money -= cash_spent
    total_secrets_absorbed = free_secrets + cash_spent
    player.secrets = min(10, player.secrets + total_secrets_absorbed)
    player.mark_ability_used(controller.state.active_version.version_str)
    if controller.state.config.slush_fund_once_per_game:
        player.slush_fund_used_game = True
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
    """Human action: executes a paid Star ability during Phase 5: Operations."""
    if controller.phase != phases.OPERATIONS:
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

    elif action_type in ("R2", "R2_MKT", "AD_CAMPAIGN"):
        cfg = controller.state.config
        if not cfg.is_market_share:
            raise ValueError("Ad Campaign requires the Market Share ruleset")
        if player.r2_actions_available <= 0:
            raise ValueError("Ad Campaign is not available: no Ad Campaign face was In Production in Phase 3")
        if player.market_share >= player.market_share_max:
            raise ValueError("Market Share is already at its maximum")
        if player.money < cfg.r2_share_cost:
            raise ValueError(f"Ad Campaign requires ${cfg.r2_share_cost}")
        from sim.engine.phase6_operations import execute_ad_campaigns

        execute_ad_campaigns(controller.engine, player, 1)
        controller.event_log.append(
            f"{meta['name']} ran an Ad Campaign: paid ${cfg.r2_share_cost} for +{cfg.r2_share_gain} Market Share."
        )

    else:
        raise ValueError(f"Unsupported star action type: {action_type}")

    return controller.get_full_state()



def system_reboot(controller: GameController, player_id: int) -> Dict[str, Any]:
    """Deprecated in v0.22.0. Soft-locks are eliminated by the CI/CD conveyor."""
    raise ValueError("System Reboot has been deprecated in v0.22.0. Soft-locks are eliminated by the CI/CD conveyor.")



def end_turn(controller: GameController, player_id: int) -> Dict[str, Any]:
    """Human action: finishes the Phase 5 Operations Turn and advances clockwise."""
    if controller.phase != phases.OPERATIONS:
        raise ValueError(f"Cannot end turn in phase {controller.phase}")
    if player_id != controller.active_player_index:
        raise ValueError(f"Not player {player_id}'s turn (current: {controller.active_player_index})")

    meta = controller.player_meta[player_id]
    pending = getattr(controller, "pending_breakthrough", {}) or {}
    if player_id in pending:  # an unanswered Triage L3 prompt is declined (forfeited, OQ-1)
        resolve_pending_breakthrough(controller, player_id, accept=False)
    controller.state.players[player_id].r2_actions_available = 0  # unused Ad Campaign actions are lost
    controller.event_log.append(f"{meta['name']} ended operations turn.")

    if controller.operations_turn_queue and controller.operations_turn_queue[0] == player_id:
        controller.operations_turn_queue.pop(0)

    # Advance to next turn (or complete round)
    advance_operations_turns(controller)
    return controller.get_full_state()


def upgrade_hardware_track(
    controller: GameController,
    player_id: int,
    track_type: str,
) -> Dict[str, Any]:
    """Human action: Upgrades the specified terminal mat hardware track (INV-UPGRADE-TRACK-01)."""
    if controller.phase != phases.OPERATIONS:
        raise ValueError(f"Cannot upgrade hardware tracks in phase {controller.phase}")
    if player_id != controller.active_player_index:
        raise ValueError(f"Not player {player_id}'s turn (current: {controller.active_player_index})")

    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]

    if player.is_patient_zero:
        raise ValueError("Eliminated players cannot upgrade hardware tracks")

    max_upgrades = getattr(controller.state.config, "max_hardware_upgrades_per_turn", 2)
    if meta.get("upgrades_this_turn", 0) >= max_upgrades:
        raise ValueError(f"Hardware upgrade limit reached ({max_upgrades} upgrades per Operations Turn)")

    t = str(track_type).upper().strip()
    cost = player.get_track_upgrade_cost(t)
    if cost is None:
        raise ValueError(f"Track {track_type} is already at maximum level")
    if player.research_tokens < cost:
        raise ValueError(f"Insufficient research tokens: need {cost} 🔬, have {player.research_tokens} 🔬")

    _require_no_pending_breakthrough(controller, player_id)
    success = player.upgrade_track(t, round_number=controller.state.current_round)
    if not success:
        raise ValueError(f"Failed to upgrade track {track_type}")

    meta["upgrades_this_turn"] = meta.get("upgrades_this_turn", 0) + 1

    new_level = getattr(player, f"{t.lower()}_level", 1)
    controller.event_log.append(
        f"{meta['name']} upgraded the {research_tracks.track_display_name(controller.state.config, t)} to Level {new_level} for {cost} 🔬."
    )
    if research_tracks.has_level_effect(controller.state.config, t, new_level):
        opts = research_tracks.breakthrough_options(controller.engine, player, t, new_level)
        if opts is not None and meta.get("is_human") and opts.as_dict().get("possible"):
            # An optional Breakthrough / Capstone (Triage die replacement): ask the player before any other operation
            if not hasattr(controller, "pending_breakthrough") or controller.pending_breakthrough is None:
                controller.pending_breakthrough = {}
            controller.pending_breakthrough[player_id] = {"track": t, "level": new_level, "options": opts.as_dict()}
        else:
            rec = research_tracks.resolve_breakthrough(controller.engine, player, t, new_level, None)
            if rec is not None:
                controller.event_log.append(
                    f"{meta['name']} {_level_effect_label(rec)} ({_track_label(controller, rec.track)} L{rec.level}): "
                    f"{_breakthrough_log(rec)}."
                )
    return controller.get_full_state()


def _track_label(controller: GameController, track: str) -> str:
    return research_tracks.track_display_name(controller.state.config, track).replace(" Track", "")


def _level_effect_label(rec: Any) -> str:
    return "Capstone" if rec.level == research_tracks.MAX_LEVEL else "Breakthrough"


def regain_market_share(controller: GameController, player_id: int) -> Dict[str, Any]:
    """Human action (Public Relations Track): +1 Market Share for the current level's price (cash in v0.47.0).

    Runs ``sim.engine.phase6_operations.execute_share_regain`` for one step (cost and per-turn cap by level)."""
    cfg = controller.state.config
    player, meta = _require_operations_turn(controller, player_id, "regain Market Share")
    cost, cap = research_tracks.regain_rate(cfg, player)
    unit = "$" if cfg.share_regain_currency == "MONEY" else "🔬"
    if player.market_share >= player.market_share_max:
        raise ValueError("Market Share is already at its maximum")
    if player.regain_this_turn >= cap:
        raise ValueError(f"Public Relations Track limit reached: +{cap} Market Share this turn at Level {player.patent_level}")
    have = player.money if unit == "$" else player.research_tokens
    if have < cost:
        raise ValueError(f"Insufficient {'cash' if unit == '$' else 'research'}: need {_fmt(cost, unit)}, have {_fmt(have, unit)}")
    if execute_share_regain(controller.engine, player, 1) != 1:
        raise ValueError("Market Share could not be regained")
    controller.event_log.append(
        f"{meta['name']} Public Relations Track: spent {_fmt(cost, unit)} for +1 Market Share (now {player.market_share})."
    )
    return controller.get_full_state()


def pen_test(controller: GameController, player_id: int, steps: int = 1) -> Dict[str, Any]:
    """Human action (Pen Test Track): each step costs ``pen_test_cost`` 🔬 for -1 Vulnerability, at most the
    level's Pen Test limit per Operations Turn (``sim.engine.vulnerability.execute_pen_test``)."""
    cfg = controller.state.config
    player, meta = _require_operations_turn(controller, player_id, "Pen Test")
    steps = int(steps)
    if steps < 1:
        raise ValueError("steps must be >= 1")
    limit = vulnerability.pen_test_limit(cfg, player)
    if player.vulnerability <= 0:
        raise ValueError("Vulnerability is already 0")
    if player.pen_test_this_turn + steps > limit:
        raise ValueError(
            f"Pen Test limit reached: -{limit} Vulnerability per Operations Turn at Pen Test Level {player.defense_level}")
    cost = vulnerability.pen_test_step_cost(cfg, player) * steps
    if player.research_tokens < cost:
        raise ValueError(f"Insufficient research tokens: need {cost} 🔬, have {player.research_tokens} 🔬")
    before = player.vulnerability
    done = vulnerability.execute_pen_test(controller.engine, player, steps)
    if done <= 0:
        raise ValueError("Pen Test could not lower Vulnerability")
    controller.event_log.append(
        f"{meta['name']} Pen Test Track: spent {cost} 🔬 for -{done} Vulnerability ({before} -> {player.vulnerability})."
    )
    return controller.get_full_state()


def _fmt(n: int, unit: str) -> str:
    return f"${n}" if unit == "$" else f"{n} 🔬"


def _require_operations_turn(controller: GameController, player_id: int, what: str):
    if controller.phase != phases.OPERATIONS:
        raise ValueError(f"Cannot {what} outside Phase 5: Operations (current phase {controller.phase})")
    if player_id != controller.active_player_index:
        raise ValueError(f"Not player {player_id}'s turn (current: {controller.active_player_index})")
    player = controller.state.players[player_id]
    if player.is_patient_zero:
        raise ValueError("Eliminated players cannot take operations")
    _require_no_pending_breakthrough(controller, player_id)
    return player, controller.player_meta[player_id]
