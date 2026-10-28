"""End game scoring and final portfolio evaluation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from sim.config import DieColor, EndGameReason
from sim.engine.state import EndGameResult

if TYPE_CHECKING:
    from sim.engine.core import GameEngine


def evaluate_end_game(engine: GameEngine) -> EndGameResult:
    cfg = engine.config
    all_patient_zero = all(p.is_patient_zero for p in engine.state.players)

    rankings: List[Dict] = []

    for p in engine.state.players:
        # Portfolio Value:
        # 4 VP per Secret + VP per owned colored die + 1 VP per $2 (rounded down)
        # 4 VP per Secret (raw VP cannot be negative; negative secrets penalize via overflow)
        secret_vp = max(0, p.secrets) * cfg.vp_per_secret
        dice_vp = sum(cfg.vp_per_die.get(d.color, 0) for d in p.total_dice)
        cash_vp = max(0, p.money) // cfg.vp_cash_divisor
        portfolio_value = secret_vp + dice_vp + cash_vp

        # Overflow penalties (used if total wipeout: -4 VP per Secret below 0, -3 VP per unfulfilled destruction)
        overflow_penalties = 0
        if all_patient_zero:
            secret_penalty = p.breach_depth * cfg.overflow_penalty_per_secret_debt
            destruction_penalty = (
                p.unfulfilled_destructions * cfg.overflow_penalty_per_unfulfilled_destroyed_die
            )
            overflow_penalties = secret_penalty + destruction_penalty

        net_score = portfolio_value + overflow_penalties

        rankings.append(
            {
                "player_id": p.player_id,
                "bot_name": p.bot.name,
                "portfolio_value": portfolio_value,
                "overflow_penalties": overflow_penalties,
                "net_score": net_score,
                "is_patient_zero": p.is_patient_zero,
                "elimination_reason": p.elimination_reason,
                "secrets": p.secrets,
                "money": p.money,
                "debt": p.debt,
                "breach_depth": p.breach_depth,
                "unfulfilled_destructions": p.unfulfilled_destructions,
                "ready_dice_count": len(p.ready_dice),
                "unpatched_dice_count": len(p.unpatched_dice),
                "total_dirty_income": p.total_dirty_income_taken,
                "total_contractors_hired": p.total_contractors_hired,
                "total_rerolls_used": p.total_rerolls_used,
                "archetype_code": p.archetype.code.value if p.archetype else "NONE",
                "archetype_name": p.archetype.name if p.archetype else "None",
                "ability_v1_status": p.ability_v1_status.value,
                "ability_v2_status": p.ability_v2_status.value,
                "ability_v3_status": p.ability_v3_status.value,
            }
        )

    if not all_patient_zero:
        # Standard Ending: Survivors ranked by Portfolio Value, Secrets, Money. Patient Zeros eliminated.
        survivors = [r for r in rankings if not r["is_patient_zero"]]
        eliminated = [r for r in rankings if r["is_patient_zero"]]

        survivors.sort(
            key=lambda r: (r["portfolio_value"], r["secrets"], r["money"]),
            reverse=True,
        )
        eliminated.sort(
            key=lambda r: (r["portfolio_value"], r["secrets"], r["money"]),
            reverse=True,
        )

        sorted_rankings = survivors + eliminated
        for rank_idx, r in enumerate(sorted_rankings):
            r["rank"] = rank_idx + 1

        winner_id = sorted_rankings[0]["player_id"] if sorted_rankings else None
        final_rankings = sorted_rankings
    else:
        # Total Wipeout: Ranked by Net Score, Secrets (higher/less negative), Money (higher/less debt)
        rankings.sort(
            key=lambda r: (r["net_score"], r["secrets"], r["money"]),
            reverse=True,
        )
        for rank_idx, r in enumerate(rankings):
            r["rank"] = rank_idx + 1

        # In total wipeout, narrative victory belongs to Rogue Agent, but top human takes 1st rank
        winner_id = rankings[0]["player_id"] if rankings else None
        final_rankings = rankings

    return EndGameResult(
        end_reason=engine.state.end_reason,
        total_rounds=engine.state.current_round,
        winner_id=winner_id,
        is_total_wipeout=all_patient_zero,
        singularity_reached=engine.state.singularity_triggered,
        rankings=final_rankings,
        telemetry_history=engine.telemetry_history,
    )
