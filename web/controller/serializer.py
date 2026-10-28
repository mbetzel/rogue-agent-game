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


from web.schemas import GameStateSerializer

def serialize_end_game_result(controller: GameController, res: EndGameResult) -> Dict[str, Any]:
    return {
        "end_reason": res.end_reason.value if isinstance(res.end_reason, EndGameReason) else str(res.end_reason),
        "total_rounds": res.total_rounds,
        "winner_id": res.winner_id,
        "winner_name": controller.player_meta[res.winner_id]["name"] if res.winner_id is not None else "None",
        "is_total_wipeout": res.is_total_wipeout,
        "singularity_reached": res.singularity_reached,
        "rankings": res.rankings,
    }



def complete_round(controller: GameController) -> None:
    """Executes round cleanup and either starts the next round or concludes the game."""
    num_players = len(controller.state.players)

    # Check Final Round condition
    if controller.state.is_final_round:
        controller.state.game_over = True
        controller.phase = 4
        controller.phase_name = "Game Over"
        controller.subphase = "game_over"
        end_res = controller.engine.evaluate_end_game()
        controller.final_result = controller._serialize_end_game_result(end_res)
        controller.event_log.append(
            f"MATCH CONCLUDED! Winner: {controller.player_meta[end_res.winner_id]['name'] if end_res.winner_id is not None else 'None'}."
        )
        return

    # Advance First Player marker clockwise
    controller.state.first_player_index = (controller.state.first_player_index + 1) % num_players

    # Increment round counter
    controller.state.current_round += 1
    if controller.state.current_round > controller.state.config.max_rounds:
        controller.state.game_over = True
        controller.state.end_reason = EndGameReason.ROUND_LIMIT
        controller.phase = 4
        controller.phase_name = "Game Over"
        controller.subphase = "game_over"
        end_res = controller.engine.evaluate_end_game()
        controller.final_result = controller._serialize_end_game_result(end_res)
        controller.event_log.append("Match reached round limit.")
        return

    # Start next round Phase 1
    controller._start_phase_1()

# =========================================================================
# State Inspection & Serialization
# =========================================================================



def get_full_state(controller: GameController) -> Dict[str, Any]:
    """Returns the complete serialized GameState JSON."""
    # Find primary human player for action capabilities
    human_pids = [pid for pid, m in controller.player_meta.items() if m["is_human"]]
    primary_human = human_pids[0] if human_pids else controller.active_player_index

    player_ranks = {}
    if controller.final_result and "rankings" in controller.final_result:
        for r in controller.final_result["rankings"]:
            player_ranks[r["player_id"]] = r.get("rank")

    controller_meta = {
        "game_id": controller.game_id,
        "phase": controller.phase,
        "phase_name": controller.phase_name,
        "subphase": controller.subphase,
        "active_player_index": controller.active_player_index,
        "players": controller.player_meta,
        "player_ranks": player_ranks,
        "last_compile_result": controller.last_compile_result,
        "action_capabilities": controller.get_action_capabilities(primary_human),
        "event_log": list(reversed(controller.event_log[-50:])),  # Most recent first
        "final_result": controller.final_result,
    }

    return GameStateSerializer.serialize_game_state(controller.state, controller_meta)
