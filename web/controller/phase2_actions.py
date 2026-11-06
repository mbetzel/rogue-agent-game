"""Web Phase 2: Compiler Drop & Corruption (v0.34.0 six-phase)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from sim.config import ROUND_PHASE_NAMES, DieColor, EndGameReason, RoundPhase, ShieldColor
from sim.engine import phase2_compiler
from sim.engine.state import PlayerState
from sim.entities import Die

if TYPE_CHECKING:
    from web.controller.core import GameController


def build_round_commitments(controller: GameController) -> List[Tuple[PlayerState, List[Die], Dict[int, ShieldColor]]]:
    """Builds engine commitments from the Phase 1 web metadata (alive players only)."""
    player_commitments: List[Tuple[PlayerState, List[Die], Dict[int, ShieldColor]]] = []
    for pid, player in enumerate(controller.state.players):
        if player.is_patient_zero:
            continue
        meta = controller.player_meta[pid]
        rolled = meta["rolled_pool"]
        commitments_enum = {int(k): ShieldColor(v) for k, v in meta["commitments"].items()}
        player_commitments.append((player, rolled, commitments_enum))
    return player_commitments


def enter_game_over(controller: GameController) -> None:
    controller.phase = int(RoundPhase.GAME_OVER)
    controller.phase_name = ROUND_PHASE_NAMES[controller.phase]
    controller.subphase = "game_over"
    end_res = controller.engine.evaluate_end_game()
    controller.final_result = controller._serialize_end_game_result(end_res)
    if controller.state.end_reason == EndGameReason.TOTAL_WIPEOUT:
        controller.event_log.append("TOTAL WIPEOUT! All corporations suffered Total Breach simultaneously.")
    elif controller.state.end_reason == EndGameReason.SINGULARITY:
        controller.event_log.append("SINGULARITY REACHED! Project: SETEC completed v3.0 compilation. Game Over!")
    else:
        if end_res.is_shared_victory:
            winner = " & ".join(controller.player_meta[w]["name"] for w in end_res.winner_ids) + " (shared victory)"
        else:
            winner = controller.player_meta[end_res.winner_id]["name"] if end_res.winner_id is not None else "None"
        controller.event_log.append(f"MATCH CONCLUDED! Winner: {winner}.")


def compile_drop(controller: GameController) -> Dict[str, Any]:
    """Phase 2: drops the Staging Cup, resolves corruption, then enters Phase 3 (Income)."""
    if controller.phase != int(RoundPhase.COMPILER_DROP_AND_CORRUPTION):
        raise ValueError(f"Cannot compile drop in phase {controller.phase} ({controller.phase_name})")

    commitments = build_round_commitments(controller)
    controller.round_commitments = commitments

    cr = phase2_compiler.execute_compiler_drop(controller.engine, commitments)
    phase2_compiler.check_end_triggers_after_compiler(controller.engine, cr)
    controller.compile_result = cr

    exited_dict = {c.value: count for c, count in cr.exited_cubes.items()}
    controller.last_compile_result = {
        "round": controller.state.current_round,
        "staged_cubes": {c.value: count for c, count in cr.staged_before.items()},
        "exited_cubes": exited_dict,
        "stuck_cubes_after": {c.value: count for c, count in cr.stuck_after.items()},
        "corruption_track": controller.state.corruption_track,
        "version_name": controller.state.active_version.name,
        "singularity_triggered": controller.state.singularity_triggered,
        "is_final_round": controller.state.is_final_round,
        "game_over": controller.state.game_over,
        "buffer_overflow": cr.buffer_overflow,
        "black_dropped": cr.black_dropped,
        "breached_player_ids": sorted(cr.breached_pids),
    }
    controller.last_income_result = {}
    controller.last_attack_result = None
    controller.pending_graduation = {}

    if cr.buffer_overflow:
        controller.event_log.append(
            "BUFFER OVERFLOW! 0 cubes exited the compiler. Idle cycle injects 1 Red, 1 Blue, 1 Green into Staging Cup "
            "(no attacks this round; income is still collected)."
        )
    else:
        controller.event_log.append(
            f"Cube Tower Drop results: {exited_dict.get('red', 0)} Red, {exited_dict.get('blue', 0)} Blue, "
            f"{exited_dict.get('green', 0)} Green, {exited_dict.get('black', 0)} Black."
        )
    for pid in sorted(cr.breached_pids):
        controller.event_log.append(
            f"{controller.player_meta[pid]['name']} suffered a Total Data Breach in Phase 2 and becomes Patient Zero."
        )

    if controller.state.game_over:
        enter_game_over(controller)
        return controller.get_full_state()

    if controller.state.is_final_round:
        controller.event_log.append("FINAL ROUND: surviving corporations complete every remaining phase.")

    from web.controller.phase3_income_actions import enter_phase_3

    enter_phase_3(controller)
    return controller.get_full_state()
