"""Legacy v0.33 three-phase round (``RoundSequence.V033_THREE_PHASE``).

Kept for regression / parity tests (INV-SEQ-LEGACY-PARITY-01, INV-SEQ-SHIM-LEGACY-01). Do NOT recompose
these from the six-phase functions: RNG call order, the buffer-overflow contractor expiry and the
deferred-green skip must stay byte-for-byte equivalent to commit ``20e8c80``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional, Set, Tuple

from sim.config import CubeColor, DieColor, EndGameReason, ShieldColor
from sim.entities import Die
from sim.engine.state import RoundTelemetry
from sim.engine.phase2_compiler import resolve_corruption_space
from sim.engine.phase4_attack_resolution import MALWARE_POLICY_V033, resolve_player_defense_and_wear
from sim.engine.phase5_pipeline_shift import execute_pipeline_prep_v033
from sim.engine.phase6_operations import execute_player_operations_turn, pass_first_player_marker

if TYPE_CHECKING:
    from sim.engine.core import GameEngine
    from sim.engine.state import PlayerState


def execute_phase_2_v033(
    engine: GameEngine,
    player_commitments: List[Tuple[PlayerState, List[Die], Dict[int, ShieldColor]]],
    defer_green_for_pids: Optional[Set[int]] = None,  # Deprecated v0.34; remove in v0.35
) -> RoundTelemetry:
    """Legacy v0.33 Phase 2 (Step 2A corruption, Step 2B attacks, Step 2C end check). Verbatim move of
    v0.33 ``phase2_threat.execute_phase_2``; RNG call order must stay byte-for-byte (INV-SEQ-LEGACY-PARITY-01)."""
    staged_before = dict(engine.state.staging_cup)
    stuck_before = engine.state.tower.get_stuck_copy()

    # Drop all staged cubes into the tower
    exited_cubes = engine.state.tower.drop(engine.state.staging_cup, engine.rng)
    engine.state.last_exited_cubes = dict(exited_cubes)
    stuck_after = engine.state.tower.get_stuck_copy()

    # Clear staging cup
    for color in engine.state.staging_cup:
        engine.state.staging_cup[color] = 0

    total_exited = sum(exited_cubes.values())
    buffer_overflow = total_exited == 0 and engine.state.config.enable_buffer_overflow

    if buffer_overflow:
        engine.state.last_round_buffer_overflow = True
        engine.state.total_buffer_overflows += 1

        attack_strengths = {
            CubeColor.RED: 0,
            CubeColor.BLUE: 0,
            CubeColor.GREEN: 0,
        }

        # Inject buffer_overflow_cubes into staging_cup
        for color, count in engine.state.config.buffer_overflow_cubes.items():
            engine.state.staging_cup[color] = (
                engine.state.staging_cup.get(color, 0) + count
            )

        # Contractor Expiration: All remaining White Contractor dice across all players return to supply
        for player in engine.state.players:
            player._pre_step2b_snapshot = None
            engine.state.contractor_supply += len(player.contractor_dice)
            player.contractor_dice.clear()
            player.hired_contractor_count = 0
            white_in_prod = [d for d in player.in_production_dice if d.color == DieColor.WHITE]
            for wd in white_in_prod:
                player.in_production_dice.remove(wd)
                engine.state.contractor_supply += 1
    else:
        engine.state.last_round_buffer_overflow = False

        # Step 2A: Resolve Black (Corruption) Cubes & Version Upgrades
        black_dropped = exited_cubes.get(CubeColor.BLACK, 0)

        for _ in range(black_dropped):
            if not engine.state.pending_version_advance:
                engine.state.corruption_track += 1
                curr_track = engine.state.active_version.corruption_track
                space_idx = engine.state.corruption_track
                if curr_track and 1 <= space_idx <= len(curr_track):
                    resolve_corruption_space(
                        engine=engine,
                        space=curr_track[space_idx - 1],
                        player_commitments=player_commitments,
                        exited_cubes=exited_cubes,
                    )

                if engine.state.corruption_track >= engine.state.corruption_track_capacity:
                    if engine.state.current_version_index >= len(engine.state.version_deck) - 1:
                        # Singularity reached on v3.0!
                        if curr_track and len(curr_track) > 0:
                            engine.state.singularity_triggered = True
                            break
                    else:
                        # Mark pending advance for next round start; excess cubes spill over immediately
                        engine.state.pending_version_advance = True
                        engine.state.overflow_black_cubes_on_next_track = 0
            else:
                # Excess cubes spill over onto the upcoming version's track immediately!
                engine.state.overflow_black_cubes_on_next_track += 1
                next_ver_idx = min(engine.state.current_version_index + 1, len(engine.state.version_deck) - 1)
                next_ver = engine.state.version_deck[next_ver_idx]
                spill_idx = engine.state.overflow_black_cubes_on_next_track
                if next_ver.corruption_track and 1 <= spill_idx <= len(next_ver.corruption_track):
                    resolve_corruption_space(
                        engine=engine,
                        space=next_ver.corruption_track[spill_idx - 1],
                        player_commitments=player_commitments,
                        exited_cubes=exited_cubes,
                    )
                if (
                    next_ver_idx >= len(engine.state.version_deck) - 1
                    and spill_idx >= next_ver.track_capacity
                ):
                    engine.state.current_version_index = next_ver_idx
                    engine.state.corruption_track = spill_idx
                    engine.state.pending_version_advance = False
                    engine.state.overflow_black_cubes_on_next_track = 0
                    engine.state.singularity_triggered = True
                    break

        # Apply P2 (Chaos Profiteer) Star bonus: +$2 per exited black cube
        if black_dropped > 0:
            for player, rolled_dice, _ in player_commitments:
                for die in rolled_dice:
                    if die.current_face and die.current_face.star_code == "P2":
                        player.money += 2 * black_dropped

        if engine.state.singularity_triggered:
            # INV-SINGULARITY-IMMEDIATE-01: Game ends IMMEDIATELY at the end of Step 2A!
            # Step 2B (Attack Cubes) and Phase 3 are skipped completely.
            attack_strengths = {
                CubeColor.RED: 0,
                CubeColor.BLUE: 0,
                CubeColor.GREEN: 0,
            }
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

            all_patient_zero = all(p.is_patient_zero for p in engine.state.players)
            engine.state.game_over = True
            engine.state.is_final_round = False
            if all_patient_zero:
                engine.state.end_reason = EndGameReason.TOTAL_WIPEOUT
            else:
                engine.state.end_reason = EndGameReason.SINGULARITY
        else:
            # Step 2B: Resolve Attack Cubes (Red, Blue, Green)
            red_strength = exited_cubes.get(CubeColor.RED, 0)
            blue_strength = exited_cubes.get(CubeColor.BLUE, 0)
            green_strength = exited_cubes.get(CubeColor.GREEN, 0)

            # Apply Active Version Directives to Attack Strength
            active_directive = engine.state.active_directive_code
            if active_directive == "CORRUPTED_KERNEL" and not engine.state.active_version.corruption_track:
                # Legacy Corrupted Kernel directive without corruption track
                if black_dropped >= engine.config.corrupted_kernel_black_threshold:
                    highest_color = max(
                        [CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN],
                        key=lambda c: (
                            exited_cubes.get(c, 0),
                            c == CubeColor.RED,
                            c == CubeColor.BLUE,
                        ),
                    )
                    bonus = engine.config.corrupted_kernel_strength_bonus
                    if highest_color == CubeColor.RED:
                        red_strength += bonus
                    elif highest_color == CubeColor.BLUE:
                        blue_strength += bonus
                    elif highest_color == CubeColor.GREEN:
                        green_strength += bonus

            attack_strengths = {
                CubeColor.RED: red_strength,
                CubeColor.BLUE: blue_strength,
                CubeColor.GREEN: green_strength,
            }

            # Resolve each player's committed shields against attacks
            for player, rolled_dice, commitments in player_commitments:
                should_defer = bool(defer_green_for_pids and player.player_id in defer_green_for_pids)
                if should_defer:
                    player._pre_step2b_snapshot = {
                        "money": player.money,
                        "secrets": player.secrets,
                        "patches": player.patches,
                        "is_patient_zero": player.is_patient_zero,
                        "elimination_round": player.elimination_round,
                        "elimination_reason": player.elimination_reason,
                        "breach_depth": player.breach_depth,
                        "ability_v1_status": player.ability_v1_status,
                        "ability_v2_status": player.ability_v2_status,
                        "ability_v3_status": player.ability_v3_status,
                        "rolled_dice": list(rolled_dice),
                        "commitments": dict(commitments),
                        "attack_strengths": dict(attack_strengths),
                        "exited_cubes": dict(exited_cubes),
                        "active_directive": active_directive,
                    }
                else:
                    player._pre_step2b_snapshot = None
                resolve_player_defense_and_wear(
                    engine=engine,
                    player=player,
                    rolled_dice=rolled_dice,
                    commitments=commitments,
                    attack_strengths=attack_strengths,
                    exited_cubes=exited_cubes,
                    active_directive=active_directive,
                    defer_green_malware=should_defer,
                    malware_target_policy=MALWARE_POLICY_V033,
                )

            # Snowball Recycle: Exited Red, Blue, Green cubes return to Staging Cup
            for color in [CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN]:
                engine.state.staging_cup[color] = (
                    engine.state.staging_cup.get(color, 0) + exited_cubes.get(color, 0)
                )

            # Contractor Expiration: All remaining White Contractor dice across all players return to supply
            for player in engine.state.players:
                if defer_green_for_pids and player.player_id in defer_green_for_pids and getattr(player, "pending_unblocked_green", 0) > 0:
                    continue
                engine.state.contractor_supply += len(player.contractor_dice)
                player.contractor_dice.clear()
                player.hired_contractor_count = 0
                white_in_prod = [d for d in player.in_production_dice if d.color == DieColor.WHITE]
                for wd in white_in_prod:
                    player.in_production_dice.remove(wd)
                    engine.state.contractor_supply += 1

            # Step 2C: Check End Game Triggers
            any_patient_zero = any(p.is_patient_zero for p in engine.state.players)
            all_patient_zero = all(p.is_patient_zero for p in engine.state.players)

            if all_patient_zero:
                engine.state.game_over = True
                engine.state.is_final_round = False
                engine.state.end_reason = EndGameReason.TOTAL_WIPEOUT
            elif any_patient_zero:
                engine.state.is_final_round = True
                engine.state.end_reason = EndGameReason.PATIENT_ZERO
            elif engine.state.singularity_triggered:
                engine.state.is_final_round = True
                engine.state.end_reason = EndGameReason.SINGULARITY

    # Create Round Telemetry snapshot
    snapshots = [
        {
            "player_id": p.player_id,
            "bot_name": p.bot.name,
            "money": p.money,
            "secrets": p.secrets,
            "patches": p.patches,
            "ready_dice_count": len(p.ready_for_release_dice),
            "in_production_dice_count": len(p.in_production_dice),
            "glitched_dice_count": len(p.glitched_dice),
            "scanned_dice_count": len(p.scanned_dice),
            "unpatched_dice_count": len(p.glitched_dice) + len(p.scanned_dice),
            "contractor_dice_count": len(p.contractor_dice),
            "is_patient_zero": p.is_patient_zero,
        }
        for p in engine.state.players
    ]

    telemetry = RoundTelemetry(
        round_number=engine.state.current_round,
        active_version_name=engine.state.active_version.name,
        corruption_track=engine.state.corruption_track,
        staged_cubes=staged_before,
        stuck_cubes_before=stuck_before,
        exited_cubes=exited_cubes,
        stuck_cubes_after=stuck_after,
        attack_strengths=attack_strengths,
        player_snapshots=snapshots,
        buffer_overflow=buffer_overflow,
    )
    engine.telemetry_history.append(telemetry)
    return telemetry


def execute_phase_3_v033(engine: GameEngine) -> None:
    """Legacy v0.33 Phase 3: Part 3A Operations Turns (income first) then Part 3B Pipeline Prep."""
    if engine.state.game_over or all(p.is_patient_zero for p in engine.state.players):
        return

    num_players = len(engine.state.players)

    # Part 3A: Operations Turns (Clockwise)
    for offset in range(num_players):
        idx = (engine.state.first_player_index + offset) % num_players
        player = engine.state.players[idx]

        if player.is_patient_zero:
            continue

        plan = player.bot.take_phase3_actions(player, engine.state, engine.rng)
        execute_player_operations_turn(
            engine, player, plan, collect_income=True, resolve_signature_protocols=True
        )

    # Part 3B: Pipeline Prep & End-of-Round Staging (Simultaneous)
    execute_pipeline_prep_v033(engine)

    # Pass the First Player Marker clockwise
    pass_first_player_marker(engine)


def run_round_v033(engine: GameEngine) -> RoundTelemetry:
    """Runs a single legacy v0.33 round."""
    # Phase 1
    commitments = engine._execute_phase_1()

    # Phase 2
    telemetry = engine._execute_phase_2(commitments)

    # Phase 3 (skipped if game over triggered in Phase 2)
    if not engine.state.game_over:
        engine._execute_phase_3()
        if engine.state.is_final_round:
            engine.state.game_over = True
        else:
            engine.state.current_round += 1
            if engine.state.current_round > engine.state.config.max_rounds:
                engine.state.game_over = True
                engine.state.end_reason = EndGameReason.ROUND_LIMIT

    return telemetry
