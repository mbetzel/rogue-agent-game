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
from sim.entities import (
    AbilityStatus,
    ArchetypeCard,
    ArchetypeCode,
    Die,
    VariantCard,
    VersionCard,
    create_colored_die,
    create_white_die,
)

if TYPE_CHECKING:
    from web.controller.core import GameController


def compile_drop(controller: GameController) -> Dict[str, Any]:
    """Executes the Cube Tower drop and attack resolution."""
    if controller.phase != 2:
        raise ValueError(f"Cannot compile drop in phase {controller.phase} ({controller.phase_name})")

    # Build player commitments for engine
    player_commitments: List[Tuple[PlayerState, List[Die], Dict[int, ShieldColor]]] = []
    for pid, player in enumerate(controller.state.players):
        if player.is_patient_zero:
            continue
        meta = controller.player_meta[pid]
        rolled = meta["rolled_pool"]
        commitments_enum = {
            int(k): ShieldColor(v) for k, v in meta["commitments"].items()
        }
        player_commitments.append((player, rolled, commitments_enum))

    # Execute Phase 2 via engine
    telemetry = controller.engine._execute_phase_2(player_commitments)

    # Update last compile result summary
    controller.last_compile_result = {
        "round": telemetry.round_number,
        "staged_cubes": {c.value: count for c, count in telemetry.staged_cubes.items()},
        "exited_cubes": {c.value: count for c, count in telemetry.exited_cubes.items()},
        "stuck_cubes_after": {c.value: count for c, count in telemetry.stuck_cubes_after.items()},
        "attack_strengths": {c.value: count for c, count in telemetry.attack_strengths.items()},
        "corruption_track": controller.state.corruption_track,
        "version_name": controller.state.active_version.name,
        "singularity_triggered": controller.state.singularity_triggered,
        "is_final_round": controller.state.is_final_round,
        "game_over": controller.state.game_over,
    }

    exited = controller.last_compile_result["exited_cubes"]
    controller.event_log.append(
        f"Cube Tower Drop results: {exited['red']} Red, {exited['blue']} Blue, {exited['green']} Green, {exited['black']} Black."
    )

    # Check end game triggers from Step 2C
    if controller.state.game_over:
        # Total Wipeout! Game ends immediately; Phase 3 is skipped
        controller.phase = 4
        controller.phase_name = "Game Over"
        controller.subphase = "game_over"
        end_res = controller.engine.evaluate_end_game()
        controller.final_result = controller._serialize_end_game_result(end_res)
        controller.event_log.append("TOTAL WIPEOUT! All corporations suffered Total Breach simultaneously.")
        return controller.get_full_state()

    # Transition to Phase 3: Corporate Operations
    controller.phase = 3
    controller.phase_name = "Corporate Operations"
    controller.subphase = "player_turn"

    # Update per-player metadata after Phase 2 attack and wear resolution
    for pid, player in enumerate(controller.state.players):
        meta = controller.player_meta[pid]
        meta["hired_contractors"] = 0
        # Shield slots have finished blocking/resolving for the round
        meta["shield_slots"] = {"red": [], "blue": [], "green": []}
        # Remove any dice that were worn down to unpatched or destroyed from the rolled pool
        unpatched_ids = {d.die_id for d in player.unpatched_dice}
        ready_ids = {d.die_id for d in player.ready_dice}
        # Active pool in Phase 3 contains non-worn rolled dice that remain active
        meta["rolled_pool"] = [
            d for d in meta.get("rolled_pool", [])
            if d.die_id not in unpatched_ids and d.die_id in ready_ids
        ]

    # Initialize Phase 3 clockwise queue starting with First Player
    num_players = len(controller.state.players)
    controller.phase3_turn_queue = [
        (controller.state.first_player_index + offset) % num_players
        for offset in range(num_players)
    ]

    controller.event_log.append(
        f"Phase 3: Corporate Operations begun. First Player turn: {controller.player_meta[controller.state.first_player_index]['name']}."
    )

    # Advance through eliminated or bot players until a human player's turn or end of round
    controller._advance_phase3_turns()
    return controller.get_full_state()

# =========================================================================
# Phase 3: Corporate Operations (Interactive)
# =========================================================================

