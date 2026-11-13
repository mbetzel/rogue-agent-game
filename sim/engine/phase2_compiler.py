"""Phase 2: Compiler Drop & Corruption (Simultaneous).

Drops the Staging Cup into the Cube Tower, resolves exited Black Cubes on the Corruption Track
(Version Advance, Spillover, Singularity), and handles Compile Buffer Overflow cube injection.
Attack Cubes (Red / Blue / Green) are NOT resolved here; see ``phase4_attack_resolution``.
"""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from sim.config import CubeColor, DieColor, EndGameReason, ShieldColor, SignatureCubeLocation
from sim.entities import CorruptionSpace, Die, TargetCriterion, TransferType
from sim.engine.state import CompileResult
from sim.engine import market_share

if TYPE_CHECKING:
    from sim.engine.core import GameEngine
    from sim.engine.state import Commitments, GameState, PlayerState


def _accepts_kwarg(func, name: str) -> bool:
    try:
        params = inspect.signature(func).parameters
    except (TypeError, ValueError):
        return False
    return name in params or any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())


# ---------------------------------------------------------------------------
# Corruption helpers (moved verbatim from v0.33 phase2_threat.py)
# ---------------------------------------------------------------------------
def demote_player_dice_step2a(
    player: PlayerState,
    rolled_dice: List[Die],
    commitments: Dict[int, ShieldColor],
    count: int,
    threat_strengths: Optional[Dict[CubeColor, int]] = None,
    engine: Optional[GameEngine] = None,
) -> None:
    demoted = 0
    threats = threat_strengths or {}
    prod_dice = list(player.in_production_dice)
    if prod_dice:
        if hasattr(player.bot, "choose_dice_to_glitch"):
            chosen = player.bot.choose_dice_to_glitch(player, prod_dice, count, threats)
        else:
            chosen = prod_dice[:count]
        for die in chosen:
            if demoted >= count:
                break
            if die in player.in_production_dice:
                player.in_production_dice.remove(die)
                if die in rolled_dice:
                    idx = rolled_dice.index(die)
                    commitments.pop(idx, None)
                die.production_role = None
                die.is_locked = False
                die.chosen_choice_index = None
                die.current_face = None
                if die.color == DieColor.WHITE:
                    if die in player.contractor_dice:
                        player.contractor_dice.remove(die)
                    player.hired_contractor_count = len(player.contractor_dice)
                    if engine is not None:
                        engine.state.contractor_supply += 1
                else:
                    player.glitched_dice.append(die)
                demoted += 1

    # Fallback to ready_for_release_dice if in_production_dice was empty or exhausted
    if demoted < count and player.ready_for_release_dice:
        ready_pool = list(player.ready_for_release_dice)
        ready_pool.sort(key=lambda d: (0 if d.color == DieColor.GRAY else 1, getattr(d, "cost", 0)))
        while demoted < count and ready_pool:
            die = ready_pool.pop(0)
            if die in player.ready_for_release_dice:
                player.ready_for_release_dice.remove(die)
                die.production_role = None
                die.is_locked = False
                die.chosen_choice_index = None
                die.current_face = None
                if die.color == DieColor.WHITE:
                    if die in player.contractor_dice:
                        player.contractor_dice.remove(die)
                    player.hired_contractor_count = len(player.contractor_dice)
                    if engine is not None:
                        engine.state.contractor_supply += 1
                else:
                    player.glitched_dice.append(die)
                demoted += 1


def return_player_colored_dice_step2a(
    engine: GameEngine,
    player: PlayerState,
    rolled_dice: List[Die],
    commitments: Dict[int, ShieldColor],
    count: int,
    threat_strengths: Optional[Dict[CubeColor, int]] = None,
    expected_income: int = 0,
) -> None:
    """Corruption *Return Colored Dice*. ``expected_income`` (v0.34 six-phase only) is this player's
    previewed Phase 3 cash, forwarded to the bot so Red-funding judgments see post-income cash."""
    if count <= 0:
        return
    threats = threat_strengths or {}
    from sim.bots.base import BaseBot

    if hasattr(player.bot, "choose_colored_dice_to_return"):
        hook = player.bot.choose_colored_dice_to_return
        if expected_income and _accepts_kwarg(hook, "expected_income"):
            chosen = list(hook(player, count, threats, expected_income=expected_income))
        else:
            chosen = list(hook(player, count, threats))
    else:
        chosen = BaseBot(player.player_id).choose_colored_dice_to_return(
            player, count, threats, expected_income=expected_income
        )

    returned = 0
    zones = (
        player.glitched_dice,
        player.scanned_dice,
        player.in_production_dice,
        player.ready_for_release_dice,
    )

    def _return_single_die(die: Die) -> bool:
        if die.color in (DieColor.GRAY, DieColor.WHITE):
            return False
        removed = False
        for z in zones:
            if die in z:
                z.remove(die)
                removed = True
                break
        if not removed:
            return False
        if getattr(die, "secret_pending", False):
            from sim.engine import secret_faces

            secret_faces.lose_pending(player, die)  # v0.38: a returned Processing Box die loses its Secret
        if die in rolled_dice:
            idx = rolled_dice.index(die)
            commitments.pop(idx, None)
        die.production_role = None
        die.is_locked = False
        die.chosen_choice_index = None
        die.current_face = None
        if die.color in engine.state.market:
            engine.state.market[die.color] += 1
        # If Purple, die is scrapped and not returned to market (INV-PURPLE-02)
        return True

    for die in chosen:
        if returned >= count:
            break
        if _return_single_die(die):
            returned += 1

    # Fallback if a custom bot returned fewer dice than count while player still owns Colored Dice
    if returned < count:
        fallback_dice = BaseBot(player.player_id).choose_colored_dice_to_return(
            player, count - returned, threats, expected_income=expected_income
        )
        for die in fallback_dice:
            if returned >= count:
                break
            if _return_single_die(die):
                returned += 1


def clamp_green_cubes_to_add(state: Any, cfg: Any, requested_green: int) -> int:
    """Clamps requested Green cubes against global_green_cube_cap (spec §3.9)."""
    if getattr(cfg, "global_green_cube_cap", 0) <= 0:
        return requested_green
    if hasattr(state, "total_green_cubes_in_circulation"):
        current_green = state.total_green_cubes_in_circulation()
    else:
        staged = state.staging_cup.get(CubeColor.GREEN, 0) if isinstance(state.staging_cup, dict) else state.staging_cup.count(CubeColor.GREEN)
        exit_tray = getattr(state, "exit_tray", getattr(state, "last_exited_cubes", {}))
        exited = exit_tray.get(CubeColor.GREEN, 0) if isinstance(exit_tray, dict) else exit_tray.count(CubeColor.GREEN)
        if hasattr(state.tower, "stuck_cubes") and isinstance(state.tower.stuck_cubes, dict):
            stuck = state.tower.stuck_cubes.get(CubeColor.GREEN, 0)
        elif hasattr(state.tower, "count"):
            stuck = state.tower.count(CubeColor.GREEN)
        elif hasattr(state.tower, "get_stuck_copy"):
            stuck = state.tower.get_stuck_copy().get(CubeColor.GREEN, 0)
        else:
            stuck = 0
        current_green = staged + exited + stuck
    headroom = max(0, cfg.global_green_cube_cap - current_green)
    return min(requested_green, headroom)


def default_transfer_donor(
    receiver: PlayerState,
    state: GameState,
    donor_pids: List[int],
) -> int:
    """Canonical default deterministic fallback for transfer donor selection (INV-TARGET-05)."""
    by_id = {p.player_id: p for p in state.players}
    n = len(state.players)
    order = {pid: (pid - receiver.player_id) % n for pid in donor_pids}
    return min(donor_pids, key=lambda pid: (-by_id[pid].secrets, order[pid]))


def get_targeted_players(
    engine: GameEngine,
    criterion: Optional[TargetCriterion],
) -> List[PlayerState]:
    """Identifies players targeted by a corruption space criterion.

    Adheres strictly to INV-TARGET-02 (all tied players affected).
    Excludes eliminated Patient Zero players.
    """
    if criterion is None or criterion == TargetCriterion.ALL:
        return [p for p in engine.state.players if not p.is_patient_zero]

    active_players = [p for p in engine.state.players if not p.is_patient_zero]
    if not active_players:
        return []

    if criterion == TargetCriterion.MOST_MONEY:
        max_val = max(p.money for p in active_players)
        return [p for p in active_players if p.money == max_val]

    elif criterion == TargetCriterion.MOST_RESEARCH:
        max_val = max(p.research for p in active_players)
        return [p for p in active_players if p.research == max_val]

    elif criterion == TargetCriterion.MOST_MARKET_SHARE:
        max_val = max(p.market_share or 0 for p in active_players)
        return [p for p in active_players if (p.market_share or 0) == max_val]

    elif criterion == TargetCriterion.FEWEST_GLITCHED:
        min_val = min(p.glitched_shield_slots for p in active_players)
        return [p for p in active_players if p.glitched_shield_slots == min_val]

    elif criterion == TargetCriterion.MOST_COLORED_DICE:
        get_cd = lambda p: p.colored_dice() if callable(getattr(p, "colored_dice", None)) else p.colored_dice
        max_val = max(len(get_cd(p)) for p in active_players)
        return [p for p in active_players if len(get_cd(p)) == max_val]

    elif criterion == TargetCriterion.MOST_SECRETS:
        max_val = max(p.secrets for p in active_players)
        return [p for p in active_players if p.secrets == max_val]

    return active_players


def resolve_corruption_transfer(engine: GameEngine, space: CorruptionSpace) -> List[Dict[str, Any]]:
    """Resolves Robin Hood transfer spaces per INV-TARGET-03, 04, 05.

    Transfer Types:
    - LEAST_MS_TAKES_CASH: Player with least MS takes $X from player with most MS.
    - LEAST_RESEARCH_TAKES_RESEARCH: Player with least 🔬 takes X 🔬 from player with most 🔬.
    """
    s = engine.state
    active_players = [p for p in s.players if not p.is_patient_zero]
    if len(active_players) < 2:
        return []

    # 1. Identify metrics
    if space.transfer_type == TransferType.LEAST_MS_TAKES_CASH:
        get_metric = lambda p: p.market_share or 0
        get_res = lambda p: p.money
        deduct_res = lambda p, amt: setattr(p, "money", max(0, p.money - amt))
        credit_res = lambda p, amt: setattr(p, "money", p.money + amt)
        res_name = "cash"
    elif space.transfer_type == TransferType.LEAST_RESEARCH_TAKES_RESEARCH:
        get_metric = lambda p: p.research
        get_res = lambda p: p.research
        deduct_res = lambda p, amt: p.lose_research(amt, "corruption_transfer")
        credit_res = lambda p, amt: p.gain_research(amt, "corruption_transfer")
        res_name = "research"
    else:
        return []

    max_val = max(get_metric(p) for p in active_players)
    min_val = min(get_metric(p) for p in active_players)

    # INV-TARGET-04: Table-wide tie fizzles
    if max_val == min_val:
        return [{"status": "fizzle", "reason": "all_players_tied"}]

    donors = [p for p in active_players if get_metric(p) == max_val]
    receivers = [p for p in active_players if get_metric(p) == min_val]

    # Order receivers clockwise from First Player for stable execution
    first_idx = getattr(s, "first_player_index", 0)
    receivers_ordered = sorted(
        receivers,
        key=lambda p: (s.players.index(p) - first_idx) % len(s.players),
    )

    events = []
    by_id = {p.player_id: p for p in s.players}
    requested_amount = space.transfer_amount

    for receiver in receivers_ordered:
        # Determine donor among tied leaders (INV-TARGET-05)
        donor_pids = [d.player_id for d in donors]
        if len(donor_pids) == 1:
            chosen_pid = donor_pids[0]
        else:
            hook = getattr(receiver.bot, "choose_corruption_transfer_donor", None) if hasattr(receiver, "bot") else None
            chosen_pid = hook(receiver, s, list(donor_pids), space.transfer_type) if callable(hook) else None
            if chosen_pid not in donor_pids:
                chosen_pid = default_transfer_donor(receiver, s, donor_pids)

        donor = by_id[chosen_pid]

        # INV-TARGET-07: Zero-floor check on donor
        available = max(0, get_res(donor))
        actual_moved = min(available, requested_amount)

        if actual_moved > 0:
            deduct_res(donor, actual_moved)
            credit_res(receiver, actual_moved)

        ev = {
            "round": s.current_round,
            "space_index": space.index,
            "transfer_type": space.transfer_type.value,
            "receiver_pid": receiver.player_id,
            "donor_pid": donor.player_id,
            "requested": requested_amount,
            "actual_moved": actual_moved,
            "resource": res_name,
        }
        events.append(ev)

    return events


def resolve_corruption_space(
    engine: GameEngine,
    space: CorruptionSpace,
    player_commitments: Commitments,
    exited_cubes: Dict[CubeColor, int],
    expected_income_by_pid: Optional[Dict[int, int]] = None,
) -> None:
    # 1. Add Cubes (conserved 100%)
    if space.add_cubes:
        for color, count in space.add_cubes.items():
            if color == CubeColor.GREEN and getattr(engine.config, "global_green_cube_cap", 0) > 0:
                actual_count = clamp_green_cubes_to_add(engine.state, engine.config, count)
                clamped_diff = count - actual_count
                if clamped_diff > 0 and hasattr(engine, "telemetry_history") and engine.telemetry_history:
                    engine.telemetry_history[-1].green_cubes_clamped_per_round += clamped_diff
                count = actual_count
            if count <= 0:
                continue
            if engine.config.corruption_cubes_resolve_immediately:
                if color == CubeColor.BLACK:
                    engine.state.staging_cup[color] = engine.state.staging_cup.get(color, 0) + count
                else:
                    exited_cubes[color] = exited_cubes.get(color, 0) + count
            else:
                engine.state.staging_cup[color] = engine.state.staging_cup.get(color, 0) + count

    # Helper for commitments lookup by player ID
    commitments_by_pid = {}
    if player_commitments:
        pc_items = player_commitments.values() if isinstance(player_commitments, dict) else player_commitments
        for item in pc_items:
            if isinstance(item, (list, tuple)) and len(item) == 3:
                p, rolled, comm = item
                commitments_by_pid[p.player_id] = (rolled, comm)

    threat_strengths = {
        CubeColor.RED: exited_cubes.get(CubeColor.RED, 0),
        CubeColor.BLUE: exited_cubes.get(CubeColor.BLUE, 0),
        CubeColor.GREEN: exited_cubes.get(CubeColor.GREEN, 0),
    }

    # Backward compatibility check
    if not getattr(engine.config, "player_specific_corruption", True):
        # 2. Lose Money
        if space.lose_money > 0:
            for player in engine.state.players:
                player.money = max(0, player.money - space.lose_money)

        # 3. Lose Patches
        if space.lose_patches > 0:
            for player in engine.state.players:
                player.lose_research(space.lose_patches, "corruption")

        # 3b. Lose Market Share
        if getattr(space, "lose_market_share", 0) > 0:
            for player in engine.state.players:
                player.change_market_share(-space.lose_market_share, "corruption")

        # 4. Demote Dice (v0.38 Glitched Shield Slots)
        if space.demote_dice > 0 and getattr(engine.config, "glitched_shield_slots_enabled", False):
            from sim.engine import secret_faces
            for player in engine.state.players:
                secret_faces.glitch_slots(player, space.demote_dice, "corruption")
        elif space.demote_dice > 0:
            for player in engine.state.players:
                rolled, comm = commitments_by_pid.get(player.player_id, (list(player.ready_dice) if hasattr(player, "ready_dice") else [], {}))
                demote_player_dice_step2a(
                    player, rolled, comm, space.demote_dice, threat_strengths, engine=engine
                )

        # 5. Return Colored Dice
        if space.return_colored_dice > 0:
            for player in engine.state.players:
                exp_income = (expected_income_by_pid or {}).get(player.player_id, 0)
                rolled, comm = commitments_by_pid.get(player.player_id, (list(player.ready_dice) if hasattr(player, "ready_dice") else [], {}))
                return_player_colored_dice_step2a(
                    engine, player, rolled, comm, space.return_colored_dice, threat_strengths,
                    expected_income=exp_income,
                )

        # 6. Lose Secrets
        if space.lose_secrets > 0:
            for player in engine.state.players:
                player.gain_secrets(-space.lose_secrets, "corruption")
                if player.secrets <= 0:
                    player.is_patient_zero = True
                    if player.elimination_round is None:
                        player.elimination_round = engine.state.current_round
                    if player.elimination_reason is None:
                        player.elimination_reason = "Total Breach (<= 0 Secrets)"
                    player.breach_depth = max(0, -player.secrets)

        # 7. Next Phase Lock
        if getattr(space, "next_phase_lock", None):
            engine.state.pending_next_phase_locks.add(space.next_phase_lock)
        return

    # --- Targeted Player-Specific Resolution (v0.41.0 / Phase 59) ---
    # 2. Robin Hood Transfers (INV-TARGET-03, 04, 05)
    if space.transfer_type != TransferType.NONE and space.transfer_amount > 0:
        resolve_corruption_transfer(engine, space)

    # 3. Direct Hazards with Targeted Resolution
    # Money Loss
    if space.lose_money > 0:
        crit = space.target_money_criterion or space.target_criterion
        targets = get_targeted_players(engine, crit)
        for player in targets:
            player.money = max(0, player.money - space.lose_money)

    # Research Loss
    if space.lose_patches > 0:
        crit = space.target_patches_criterion or space.target_criterion
        targets = get_targeted_players(engine, crit)
        for player in targets:
            player.lose_research(space.lose_patches, "corruption")

    # Market Share Loss
    if getattr(space, "lose_market_share", 0) > 0:
        crit = space.target_market_share_criterion or space.target_criterion
        targets = get_targeted_players(engine, crit)
        for player in targets:
            player.change_market_share(-space.lose_market_share, "corruption")

    # Demote Dice (Glitched Shield Slots)
    if space.demote_dice > 0:
        crit = space.target_demote_criterion or space.target_criterion
        targets = get_targeted_players(engine, crit)
        if getattr(engine.config, "glitched_shield_slots_enabled", False):
            from sim.engine import secret_faces
            for player in targets:
                secret_faces.glitch_slots(player, space.demote_dice, "corruption")
        else:
            for player in targets:
                rolled, comm = commitments_by_pid.get(player.player_id, (list(player.ready_dice) if hasattr(player, "ready_dice") else [], {}))
                demote_player_dice_step2a(
                    player, rolled, comm, space.demote_dice, threat_strengths, engine=engine
                )

    # Return Colored Module Dice
    if space.return_colored_dice > 0:
        crit = space.target_return_colored_criterion or space.target_criterion
        targets = get_targeted_players(engine, crit)
        for player in targets:
            exp_income = (expected_income_by_pid or {}).get(player.player_id, 0)
            rolled, comm = commitments_by_pid.get(player.player_id, (list(player.ready_dice) if hasattr(player, "ready_dice") else [], {}))
            return_player_colored_dice_step2a(
                engine, player, rolled, comm, space.return_colored_dice, threat_strengths,
                expected_income=exp_income,
            )

    # Corporate Secrets Loss
    if space.lose_secrets > 0:
        crit = space.target_secrets_criterion or space.target_criterion
        targets = get_targeted_players(engine, crit)
        for player in targets:
            player.gain_secrets(-space.lose_secrets, "corruption")
            if player.secrets <= 0:
                player.is_patient_zero = True
                if player.elimination_round is None:
                    player.elimination_round = engine.state.current_round
                if player.elimination_reason is None:
                    player.elimination_reason = "Total Breach (<= 0 Secrets)"
                player.breach_depth = max(0, -player.secrets)

    # Next Phase Lock
    if getattr(space, "next_phase_lock", None):
        engine.state.pending_next_phase_locks.add(space.next_phase_lock)


def apply_p2_chaos_profiteer_bonus(engine: GameEngine, player_commitments: Commitments, black_dropped: int) -> None:
    """Legacy sim-only P2 (Chaos Profiteer) star: +$2 per exited Black Cube (stays in Phase 2, OQ-5)."""
    if black_dropped > 0:
        for player, rolled_dice, _ in player_commitments:
            for die in rolled_dice:
                if die.current_face and die.current_face.star_code == "P2":
                    player.money += 2 * black_dropped


def apply_singularity_cleanup(engine: GameEngine) -> None:
    """Singularity: In Production dice return to Ready, contractors return to supply (INV-SEQ-SINGULARITY-SKIP-01)."""
    for player in engine.state.players:
        player._pre_step2b_snapshot = None
        player.pending_unblocked_green = 0
        engine.state.contractor_supply += len(player.contractor_dice)
        player.contractor_dice.clear()
        player.hired_contractor_count = 0
        for d in list(player.in_production_dice):
            player.in_production_dice.remove(d)
            d.production_role = None
            d.is_locked = False
            d.chosen_choice_index = None
            d.current_face = None
            if d.color == DieColor.WHITE:
                engine.state.contractor_supply += 1
            else:
                player.ready_for_release_dice.append(d)


def _six_phase_singularity_cleanup(engine: GameEngine) -> None:
    """Six-phase Singularity cleanup with exact contractor-supply accounting."""
    from sim.engine.phase4_attack_resolution import expire_contractors

    expire_contractors(engine)
    for player in engine.state.players:
        player.pending_unblocked_green = 0
        for d in list(player.in_production_dice):
            player.in_production_dice.remove(d)
            d.production_role = None
            d.is_locked = False
            d.chosen_choice_index = None
            d.current_face = None
            player.ready_for_release_dice.append(d)


def _expected_income_by_pid(engine: GameEngine) -> Dict[int, int]:
    from sim.engine.phase3_income import preview_player_income

    return {
        p.player_id: preview_player_income(engine.state, p).money
        for p in engine.state.players
        if not p.is_patient_zero
    }


# ---------------------------------------------------------------------------
# Phase 2 entry point (six-phase path)
# ---------------------------------------------------------------------------
def execute_compiler_drop(engine: GameEngine, player_commitments: Commitments) -> CompileResult:
    """Phase 2: Compiler Drop & Corruption. Does not compute attack strengths (Phase 4)."""
    state = engine.state
    staged_before = dict(state.staging_cup)
    stuck_before = state.tower.get_stuck_copy()

    staged_sigs = set(state.staging_signature_cubes)
    if _accepts_kwarg(state.tower.drop, "staged_signatures"):
        exited_cubes = state.tower.drop(state.staging_cup, engine.rng, staged_signatures=staged_sigs)
    else:
        exited_cubes = state.tower.drop(state.staging_cup, engine.rng)
    state.staging_signature_cubes.clear()
    state.last_exited_cubes = dict(exited_cubes)
    stuck_after = state.tower.get_stuck_copy()

    for color in state.staging_cup:
        state.staging_cup[color] = 0

    exited_sigs = getattr(state.tower, "last_exited_signatures", set())
    exited_signature_pids = set(exited_sigs)
    stuck_signature_pids = set(getattr(state.tower, "stuck_signatures", {}).keys())

    if engine.config.target_lock_enabled:
        for player in state.players:
            pid = player.player_id
            if pid in exited_sigs:
                # Signature exited into tray: Target Lock established!
                player.target_locked = True
                player.target_locks_triggered += 1
                player.signature_cube_location = SignatureCubeLocation.IDLE_ON_MAT
                player.target_lock_baffle_rounds = 0
            elif pid in stuck_signature_pids:
                # Signature remains trapped on baffles
                player.target_locked = False
                player.signature_cube_location = SignatureCubeLocation.IN_TOWER
                player.target_lock_baffle_rounds = state.tower.stuck_signatures.get(pid, 1)
                player.baffle_hold_rounds_total += 1

    total_exited = sum(exited_cubes.values())
    buffer_overflow = total_exited == 0 and state.config.enable_buffer_overflow
    black_dropped = 0
    cmp_start = len(state.version_comparisons)

    if buffer_overflow:
        state.last_round_buffer_overflow = True
        state.total_buffer_overflows += 1
        for color, count in state.config.buffer_overflow_cubes.items():
            state.staging_cup[color] = state.staging_cup.get(color, 0) + count
        # Contractor Expiration is deferred to the end of Phase 4 (contractor +$1 still pays in Phase 3).
    else:
        state.last_round_buffer_overflow = False
        black_dropped = exited_cubes.get(CubeColor.BLACK, 0)

        def _resolve(space: CorruptionSpace) -> None:
            exp = _expected_income_by_pid(engine) if space.return_colored_dice > 0 else None
            resolve_corruption_space(
                engine=engine,
                space=space,
                player_commitments=player_commitments,
                exited_cubes=exited_cubes,
                expected_income_by_pid=exp,
            )

        for _ in range(black_dropped):
            if not state.pending_version_advance:
                state.corruption_track += 1
                curr_track = state.active_version.corruption_track
                space_idx = state.corruption_track
                if curr_track and 1 <= space_idx <= len(curr_track):
                    _resolve(curr_track[space_idx - 1])

                if state.corruption_track >= state.corruption_track_capacity:
                    if state.current_version_index >= len(state.version_deck) - 1:
                        if curr_track and len(curr_track) > 0:
                            state.singularity_triggered = True
                            break
                    else:
                        # v0.36.0: Market Share comparison after the final space resolves (INV-MS-CMP-TIMING-01)
                        market_share.resolve_version_comparison(engine, state.active_version.version_str, False)
                        state.pending_version_advance = True
                        state.overflow_black_cubes_on_next_track = 0
            else:
                # Spillover: cubes go onto the pending target Version's track, cascading through every
                # track they fill (RULES Phase 2 "Version Advance & Track Spillover").
                last_idx = len(state.version_deck) - 1
                state.overflow_black_cubes_on_next_track += 1
                next_ver_idx = min(
                    state.current_version_index + 1 + state.pending_extra_version_advances, last_idx
                )
                next_ver = state.version_deck[next_ver_idx]
                spill_idx = state.overflow_black_cubes_on_next_track
                if next_ver.corruption_track and 1 <= spill_idx <= len(next_ver.corruption_track):
                    _resolve(next_ver.corruption_track[spill_idx - 1])
                if spill_idx >= next_ver.track_capacity:
                    if next_ver_idx >= last_idx:
                        state.current_version_index = next_ver_idx
                        state.corruption_track = spill_idx
                        state.pending_version_advance = False
                        state.pending_extra_version_advances = 0
                        state.overflow_black_cubes_on_next_track = 0
                        state.singularity_triggered = True
                        break
                    # A non-final track filled by spillover: queue one more Version Switch and keep
                    # spilling onto the following Version's track from Space 1.
                    state.pending_extra_version_advances += 1
                    # Spillover covered the final space of a non-last version (spec §4.3, E6). The counter is
                    # telemetry only (both modes); the comparison is a no-op under RANSOM.
                    state.double_version_fill_events += 1
                    market_share.resolve_version_comparison(engine, next_ver.version_str, True)
                    state.overflow_black_cubes_on_next_track = 0
                    state.multi_version_spill_events += 1

        apply_p2_chaos_profiteer_bonus(engine, player_commitments, black_dropped)

    breached = {
        p.player_id
        for p in state.players
        if p.is_patient_zero and p.elimination_round == state.current_round
    }
    return CompileResult(
        staged_before=staged_before,
        stuck_before=stuck_before,
        exited_cubes=exited_cubes,
        stuck_after=stuck_after,
        buffer_overflow=buffer_overflow,
        black_dropped=black_dropped,
        breached_pids=breached,
        version_comparisons=list(state.version_comparisons[cmp_start:]),
        exited_signature_pids=exited_signature_pids,
        stuck_signature_pids=stuck_signature_pids,
    )


def check_end_triggers_after_compiler(engine: GameEngine, cr: CompileResult) -> None:
    """End-of-Phase-2 trigger check (spec §4.2)."""
    from sim.engine.phase4_attack_resolution import expire_contractors

    state = engine.state
    players = state.players
    if state.singularity_triggered:
        _six_phase_singularity_cleanup(engine)
        state.game_over = True
        state.is_final_round = False
        state.end_reason = (
            EndGameReason.TOTAL_WIPEOUT if all(p.is_patient_zero for p in players) else EndGameReason.SINGULARITY
        )
        if any(p.is_patient_zero for p in players):
            market_share.add_end_trigger(state, "patient_zero")
        market_share.add_end_trigger(state, state.end_reason.value)
        return
    if all(p.is_patient_zero for p in players):
        expire_contractors(engine)
        state.game_over = True
        state.is_final_round = False
        state.end_reason = EndGameReason.TOTAL_WIPEOUT
        market_share.add_end_trigger(state, "patient_zero")
        market_share.add_end_trigger(state, "total_wipeout")
        return
    if any(p.is_patient_zero for p in players):
        market_share.add_end_trigger(state, "patient_zero")
        state.is_final_round = True
        state.end_reason = EndGameReason.PATIENT_ZERO
        if state.final_round_trigger_phase is None:
            state.final_round_trigger_phase = 2
