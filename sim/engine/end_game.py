"""End game scoring and final portfolio evaluation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from sim.config import DieColor, EndGameReason
from sim.engine.state import EndGameResult

if TYPE_CHECKING:
    from sim.engine.core import GameEngine


def _standard_key(r: Dict) -> Tuple:
    return (r["secrets"], r["money"], r["ready_colored_dice_count"], r["patches"], -r["unpatched_dice_count"])


def _wipeout_key_six_phase(r: Dict) -> Tuple:
    return (r["money"], r["ready_colored_dice_count"], r["patches"], -r["unpatched_dice_count"])


def _wipeout_key_v033(r: Dict) -> Tuple:
    return (r["net_score"], r["secrets"], r["money"], r["ready_colored_dice_count"], r["patches"], -r["unpatched_dice_count"])


def _return_held_contractors(engine: GameEngine) -> None:
    """End-of-game cleanup: unexpired White Contractor dice (e.g. Triage L1 Breakthrough contractors gained in
    the Final Round's Phase 6) return to the supply, keeping ``contractor_supply`` conserved."""
    for p in engine.state.players:
        whites = [d for d in p.contractor_dice if d.color == DieColor.WHITE]
        if whites:
            engine.state.contractor_supply += len(whites)
            p.contractor_dice.clear()
            p.hired_contractor_count = 0


def evaluate_end_game(engine: GameEngine) -> EndGameResult:
    cfg = engine.config
    _return_held_contractors(engine)
    all_patient_zero = all(p.is_patient_zero for p in engine.state.players)

    rankings: List[Dict] = []

    for p in engine.state.players:
        # Portfolio Value (v0.19.0: Pure Corporate Secrets Victory Scoring):
        # 1 VP per Secret. Software modules and cash have 0 direct VP.
        portfolio_value = max(0, p.secrets) * cfg.vp_per_secret

        # Telemetry: unpatched colored dice count and VP lost
        unpatched_colored_dice_count = sum(
            1 for d in p.unpatched_dice if d.color != DieColor.GRAY
        )
        unpatched_dice_vp_lost = 0

        # Overflow penalties (used if total wipeout: -1 per Secret below 0)
        overflow_penalties = 0
        if all_patient_zero:
            secret_penalty = p.breach_depth * cfg.overflow_penalty_per_secret_debt
            overflow_penalties = secret_penalty
            net_score = overflow_penalties
        else:
            net_score = portfolio_value

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
                "patches": p.patches,
                "debt": p.debt,
                "breach_depth": p.breach_depth,
                "unfulfilled_destructions": p.unfulfilled_destructions,
                "ready_dice_count": sum(
                    1 for d in (list(p.ready_for_release_dice) + [x for x in p.in_production_dice if x not in p.ready_for_release_dice])
                    if d.color != DieColor.WHITE
                ),
                "ready_colored_dice_count": sum(
                    1 for d in (list(p.ready_for_release_dice) + [x for x in p.in_production_dice if x not in p.ready_for_release_dice])
                    if d.color != DieColor.GRAY and d.color != DieColor.WHITE
                ),
                "unpatched_dice_count": len(p.glitched_dice) + len(p.scanned_dice),
                "glitched_dice_count": len(p.glitched_dice),
                "scanned_dice_count": len(p.scanned_dice),
                "under_development_dice_count": len(p.glitched_dice) + len(p.scanned_dice),
                "unpatched_colored_dice_count": unpatched_colored_dice_count,
                "unpatched_dice_vp_lost": unpatched_dice_vp_lost,
                # v0.35.0 research telemetry (spec §4.6)
                "research_earned_total": getattr(p, "research_earned_total", 0),
                "research_earned_by_source": dict(getattr(p, "research_earned_by_source", {})),
                "research_lost_total": getattr(p, "research_lost_total", 0),
                "research_spent_tracks": dict(getattr(p, "research_spent_tracks", {})),
                "research_spent_patents": getattr(p, "research_spent_patents", 0),
                "patent_secrets_gained": getattr(p, "patent_secrets_gained", 0),
                "final_track_levels": {
                    "DEFENSE": p.defense_level, "TRIAGE": p.triage_level,
                    "RELEASE": p.release_level, "PATENT": p.patent_level,
                },
                "level_reached_round": {t: dict(v) for t, v in getattr(p, "level_reached_round", {}).items()},
                "breakthroughs": [b.as_dict() for b in getattr(p, "breakthroughs", [])],
                "l4_payouts": dict(getattr(p, "l4_payouts", {})),
                "purple_dice_owned_final": sum(1 for d in p.total_dice if d.color == DieColor.PURPLE),
                "gray_dice_owned_final": sum(1 for d in p.total_dice if d.color == DieColor.GRAY),
                "triage_l3_upgrade_color": getattr(p, "triage_l3_upgrade_color", None),
                "slush_fund_used_game": getattr(p, "slush_fund_used_game", False),
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
        # Standard Ending: Survivors ranked strictly by Corporate Secrets, with hierarchical tiebreakers:
        # 1. Money, 2. Ready Colored Dice, 3. Patches, 4. Fewest Unpatched Dice. Patient Zeros eliminated.
        survivors = [r for r in rankings if not r["is_patient_zero"]]
        eliminated = [r for r in rankings if r["is_patient_zero"]]

        survivors.sort(
            key=lambda r: (
                r["secrets"],
                r["money"],
                r["ready_colored_dice_count"],
                r["patches"],
                -r["unpatched_dice_count"],
            ),
            reverse=True,
        )
        eliminated.sort(
            key=lambda r: (
                r["secrets"],
                r["money"],
                r["ready_colored_dice_count"],
                r["patches"],
                -r["unpatched_dice_count"],
            ),
            reverse=True,
        )

        sorted_rankings = survivors + eliminated
        for rank_idx, r in enumerate(sorted_rankings):
            r["rank"] = rank_idx + 1

        winner_id = sorted_rankings[0]["player_id"] if sorted_rankings else None
        final_rankings = sorted_rankings
        win_pool, win_key = survivors, _standard_key
    elif getattr(cfg, "is_six_phase", False):
        # v0.34 Total Wipeout (OQ-4): breach depth is ignored; rank ONLY by the standard hierarchical
        # tiebreakers: Money > Active Colored dice in Ready > Research > fewest Under Development.
        # breach_depth / net_score stay recorded for telemetry only. Python's stable sort keeps
        # player-index order for fully shared ranks.
        rankings.sort(
            key=lambda r: (
                r["money"],
                r["ready_colored_dice_count"],
                r["patches"],
                -r["unpatched_dice_count"],
            ),
            reverse=True,
        )
        for rank_idx, r in enumerate(rankings):
            r["rank"] = rank_idx + 1
        winner_id = rankings[0]["player_id"] if rankings else None
        final_rankings = rankings
        win_pool, win_key = rankings, _wipeout_key_six_phase
    else:
        # Legacy v0.33 Total Wipeout: Ranked by Net Wipeout Score, Secrets, Money, Ready Colored Dice, Patches, fewest unpatched dice
        rankings.sort(
            key=lambda r: (
                r["net_score"],
                r["secrets"],
                r["money"],
                r["ready_colored_dice_count"],
                r["patches"],
                -r["unpatched_dice_count"],
            ),
            reverse=True,
        )
        for rank_idx, r in enumerate(rankings):
            r["rank"] = rank_idx + 1

        # In total wipeout, narrative victory belongs to Rogue Agent, but top human takes 1st rank
        winner_id = rankings[0]["player_id"] if rankings else None
        final_rankings = rankings
        win_pool, win_key = rankings, _wipeout_key_v033

    # Shared victory (RULES §5: "If still tied, victory is shared"): every player tied for first on the
    # full ranking key wins. Reporting only; gameplay is unaffected.
    winner_ids = [r["player_id"] for r in win_pool if win_key(r) == win_key(win_pool[0])] if win_pool else []
    is_shared_victory = len(winner_ids) > 1
    for r in final_rankings:
        r["is_winner"] = r["player_id"] in winner_ids
    if getattr(cfg, "is_six_phase", False):
        winner_id = None if is_shared_victory else (winner_ids[0] if winner_ids else None)
        # Competition ranking: fully tied players share a rank (survivors before Patient Zeros).
        prev = None
        for idx, r in enumerate(final_rankings):
            k = (not r["is_patient_zero"] or all_patient_zero, win_key(r))
            if k != prev:
                rank = idx + 1
                prev = k
            r["rank"] = rank
    # Legacy v0.33 path keeps winner_id = first in seat-stable sort order and sequential ranks (parity).

    return EndGameResult(
        end_reason=engine.state.end_reason,
        total_rounds=engine.state.current_round,
        winner_id=winner_id,
        winner_ids=winner_ids,
        is_shared_victory=is_shared_victory,
        is_total_wipeout=all_patient_zero,
        singularity_reached=engine.state.singularity_triggered,
        rankings=final_rankings,
        telemetry_history=engine.telemetry_history,
        total_buffer_overflows=engine.state.total_buffer_overflows,
    )
