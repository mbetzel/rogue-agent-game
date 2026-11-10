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
from sim.config import ROUND_PHASE_NAMES, CubeColor, DieColor, EndGameReason, GameConfig, ShieldColor
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

def _game_end_bonus(controller: GameController, res: EndGameResult) -> Dict[str, Any]:
    """v0.38.0 game-end Market Leader Bonus (RSP-1 end payout) in the shape the end screen reads; also folds the
    v0.37.0 bonus in so one ``end_bonus`` column covers both rulesets."""
    cfg = controller.state.config
    end_fired = bool(getattr(res, "red_secret_payout_end_fired", False))
    awarded = bool(getattr(res, "market_leader_bonus_awarded", False)) or end_fired
    per_player = {}
    for r in res.rankings:
        end_award = int(r.get("red_secret_payout_end", 0) or 0)
        r["end_bonus"] = int(r.get("market_leader_bonus", 0) or 0) + end_award
        if "red_payout_secrets" in r:
            r["round_bonus_total"] = int(r["red_payout_secrets"]) - end_award
        per_player[r["player_id"]] = r["end_bonus"]
    schedule = (list(getattr(res, "market_leader_bonus_schedule", []) or [])
                or (list(cfg.red_secret_payout_schedule(len(controller.state.players))) if end_fired else []))
    return {
        "game_end_bonus_awarded": awarded,
        "game_end_bonus_schedule": schedule,
        "red_secret_payouts_fired": int(getattr(res, "red_secret_payouts_fired", 0) or 0),
        "stranded_note": any(int(r.get("stranded_dice", 0) or 0) > 0 for r in res.rankings),
    }


def serialize_end_game_result(controller: GameController, res: EndGameResult) -> Dict[str, Any]:
    extra = _game_end_bonus(controller, res)
    return {
        **extra,
        "end_reason": res.end_reason.value if isinstance(res.end_reason, EndGameReason) else str(res.end_reason),
        "total_rounds": res.total_rounds,
        "winner_id": res.winner_id,
        "winner_ids": list(getattr(res, "winner_ids", []) or []),
        "is_shared_victory": bool(getattr(res, "is_shared_victory", False)),
        "winner_names": [controller.player_meta[w]["name"] for w in (getattr(res, "winner_ids", []) or [])],
        "winner_name": (
            " & ".join(controller.player_meta[w]["name"] for w in res.winner_ids) + " (shared victory)"
            if getattr(res, "is_shared_victory", False)
            else (controller.player_meta[res.winner_id]["name"] if res.winner_id is not None else "None")
        ),
        "is_total_wipeout": res.is_total_wipeout,
        "singularity_reached": res.singularity_reached,
        "rankings": res.rankings,
        "total_buffer_overflows": getattr(res, "total_buffer_overflows", 0),
        # v0.36.0
        "end_triggers": list(getattr(res, "end_triggers", []) or []),
        "market_collapse_pids": list(getattr(res, "market_collapse_pids", []) or []),
        "market_collapse_round": getattr(res, "market_collapse_round", None),
        "version_comparisons": list(getattr(res, "version_comparisons", []) or []),
        "tiebreak_decided_by": getattr(res, "tiebreak_decided_by", None),
        # v0.37.0 Market Leader Bonus (rows carry secrets_before_bonus / market_leader_bonus / market_share_place)
        "market_leader_bonus_awarded": bool(getattr(res, "market_leader_bonus_awarded", False)),
        "market_leader_bonus_schedule": list(getattr(res, "market_leader_bonus_schedule", []) or []),
        "pre_bonus_winner_ids": list(getattr(res, "pre_bonus_winner_ids", []) or []),
        "market_leader_bonus_changed_winner": bool(getattr(res, "market_leader_bonus_changed_winner", False)),
    }



def complete_round(controller: GameController) -> None:
    """End of Phase 6: Final Round -> Game Over; else pass the First Player Marker and start the next round.

    The CI/CD Pipeline Shift already ran in Phase 5 (web/controller/phase5_pipeline_actions.py).
    """
    from web.controller.phase2_actions import enter_game_over

    num_players = len(controller.state.players)

    if controller.state.is_final_round:
        controller.state.game_over = True
        enter_game_over(controller)
        return

    # Pass the First Player Marker clockwise (end of Phase 6)
    controller.state.first_player_index = (controller.state.first_player_index + 1) % num_players

    controller.state.current_round += 1
    if controller.state.current_round > controller.state.config.max_rounds:
        controller.state.game_over = True
        controller.state.end_reason = EndGameReason.ROUND_LIMIT
        enter_game_over(controller)
        controller.event_log.append("Match reached round limit.")
        return

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
        "last_income_result": getattr(controller, "last_income_result", {}) or {},
        "last_attack_result": getattr(controller, "last_attack_result", None),
        "last_pipeline_result": getattr(controller, "last_pipeline_result", {}) or {},
        "pending_graduation": getattr(controller, "pending_graduation", {}) or {},
        "round_sequence": controller.state.config.round_sequence.value,
        "phase_names": dict(ROUND_PHASE_NAMES),
        "action_capabilities": controller.get_action_capabilities(primary_human),
        "event_log": list(reversed(controller.event_log[-50:])),  # Most recent first
        "final_result": controller.final_result,
        "last_round_bonus": getattr(controller, "last_round_bonus", None),
    }

    return GameStateSerializer.serialize_game_state(controller.state, controller_meta)
