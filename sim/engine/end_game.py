"""End game scoring and final portfolio evaluation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from sim.config import DieColor, EndGameReason, TiebreakOrder
from sim.engine.market_share import market_leader_bonus_awards, market_share_places
from sim.engine.state import EndGameResult

if TYPE_CHECKING:
    from sim.engine.core import GameEngine


def _standard_key(r: Dict) -> Tuple:
    return (r["secrets"], r["money"], r["ready_colored_dice_count"], r["patches"], -r["unpatched_dice_count"])


def _wipeout_key_six_phase(r: Dict) -> Tuple:
    return (r["money"], r["ready_colored_dice_count"], r["patches"], -r["unpatched_dice_count"])


# v0.36.0 MARKET_SHARE_FIRST tiebreakers (INV-MS-TIEBREAK-01): Market Share sits right after Secrets
def _standard_key_ms(r: Dict) -> Tuple:
    return (r["secrets"], r["market_share"], r["money"], r["ready_colored_dice_count"], r["patches"],
            -r["unpatched_dice_count"])


def _wipeout_key_ms(r: Dict) -> Tuple:
    return (r["market_share"], r["money"], r["ready_colored_dice_count"], r["patches"], -r["unpatched_dice_count"])


_KEY_FIELDS = {
    _standard_key: ("secrets", "money", "ready_colored_dice_count", "patches", "unpatched_dice_count"),
    _wipeout_key_six_phase: ("money", "ready_colored_dice_count", "patches", "unpatched_dice_count"),
    _standard_key_ms: ("secrets", "market_share", "money", "ready_colored_dice_count", "patches", "unpatched_dice_count"),
    _wipeout_key_ms: ("market_share", "money", "ready_colored_dice_count", "patches", "unpatched_dice_count"),
}


def _tiebreak_decided_by(win_pool: List[Dict], key) -> str:
    """Name of the first key field separating the winner from the runner-up (``"shared"`` / ``"sole_survivor"``)."""
    if len(win_pool) <= 1:
        return "sole_survivor"
    a, b = key(win_pool[0]), key(win_pool[1])
    names = _KEY_FIELDS.get(key)
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return names[i] if names and i < len(names) else f"key_{i}"
    return "shared"


def _setup_record(engine: GameEngine) -> Dict[str, Any]:
    s = engine.state
    return {
        "version_cards": [v.directive_code for v in s.version_deck],
        "variant_cards": {getattr(c, "value", str(c)): v.code for c, v in s.variant_cards.items()},
        "companies": [getattr(getattr(p.company, "code", None), "value", None) for p in s.players],
        "white_hats": [getattr(getattr(p.white_hat, "code", None), "value", None) for p in s.players],
        "first_player_index_start": getattr(s, "first_player_index_start", 0),
    }


def _wipeout_key_v033(r: Dict) -> Tuple:
    return (r["net_score"], r["secrets"], r["money"], r["ready_colored_dice_count"], r["patches"], -r["unpatched_dice_count"])


def _dice_by_color(p) -> Dict[str, int]:
    out: Dict[str, int] = {c.value: 0 for c in DieColor}
    for d in p.total_dice:
        k = getattr(d.color, "value", str(d.color))
        out[k] = out.get(k, 0) + 1
    return out


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

    # v0.37.0 Market Leader Bonus (INV-MLB-*): survivors are placed by final Market Share (ties share the better
    # place) and gain bonus Corporate Secrets by place before Secrets are compared. None on a Total Wipeout.
    # PlayerState.secrets is never mutated: the bonus lives in the ranking rows (INV-MLB-SCORE-01).
    players = engine.state.players
    bonus_on = bool(cfg.is_market_leader_bonus) and not all_patient_zero
    bonus_schedule = list(cfg.market_leader_bonus_schedule(len(players))) if bonus_on else []
    survivor_shares = {p.player_id: int(p.market_share or 0) for p in players if not p.is_patient_zero}
    places = market_share_places(survivor_shares) if cfg.is_market_share and not all_patient_zero else {}
    awards = market_leader_bonus_awards(survivor_shares, bonus_schedule) if bonus_on else {}

    rankings: List[Dict] = []

    for p in players:
        bonus = awards.get(p.player_id, (None, 0))[1]
        final_secrets = p.secrets + bonus
        # Portfolio Value (v0.19.0: Pure Corporate Secrets Victory Scoring):
        # 1 VP per Secret. Software modules and cash have 0 direct VP.
        portfolio_value = max(0, final_secrets) * cfg.vp_per_secret

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
                "secrets": final_secrets,
                "secrets_before_bonus": p.secrets,
                "market_leader_bonus": bonus,
                "market_share_place": places.get(p.player_id),
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
                # v0.36.0 Market Share / Red telemetry (spec §4.8)
                "market_share": p.market_share,
                "market_share_min": p.market_share_min,
                "market_share_lost_red": p.market_share_lost_red,
                "market_share_red_overflow": p.market_share_red_overflow,
                "market_share_lost_poach": p.market_share_lost_poach,
                "market_share_gained_poach": p.market_share_gained_poach,
                "market_share_regained": p.market_share_regained,
                "market_share_gained_r2": p.market_share_gained_r2,
                "research_spent_regain": p.research_spent_regain,
                "r2_uses": p.r2_uses,
                "comparison_money_gained": p.comparison_money_gained,
                "comparison_money_paid": p.comparison_money_paid,
                "comparison_shortfall_forgiven": p.comparison_shortfall_forgiven,
                "purchases_by_color": dict(p.purchases_by_color),
                "red_incoming_total": p.red_incoming_total,
                "red_blocked_color_total": p.red_blocked_color_total,
                "red_blocked_any_total": p.red_blocked_any_total,
                "red_unblocked_total": p.red_unblocked_total,
                # v0.37.0 Generic shield / contested-round telemetry (spec §4.4)
                "any_shield_allocated_by_color": dict(p.any_shield_allocated_by_color),
                "contested_defense_rounds": p.contested_defense_rounds,
                "contested_blue_left_open": p.contested_blue_left_open,
                "contested_red_chosen": p.contested_red_chosen,
                "dice_owned_final_by_color": _dice_by_color(p),
                "rejected_patent_filings": getattr(p, "rejected_patent_filings", 0),
                "company_code": getattr(getattr(p.company, "code", None), "value", None),
                "white_hat_code": getattr(getattr(p.white_hat, "code", None), "value", None),
                "seat": p.player_id,
            }
        )

    ms_first = getattr(cfg, "tiebreak_order", TiebreakOrder.V035) == TiebreakOrder.MARKET_SHARE_FIRST
    std_key = _standard_key_ms if ms_first else _standard_key
    wipe_key = _wipeout_key_ms if ms_first else _wipeout_key_six_phase

    if not all_patient_zero:
        # Standard Ending: Survivors ranked strictly by Corporate Secrets, with hierarchical tiebreakers:
        # 1. Money, 2. Ready Colored Dice, 3. Patches, 4. Fewest Unpatched Dice. Patient Zeros eliminated.
        survivors = [r for r in rankings if not r["is_patient_zero"]]
        eliminated = [r for r in rankings if r["is_patient_zero"]]

        survivors.sort(key=std_key, reverse=True)
        eliminated.sort(key=std_key, reverse=True)

        sorted_rankings = survivors + eliminated
        for rank_idx, r in enumerate(sorted_rankings):
            r["rank"] = rank_idx + 1

        winner_id = sorted_rankings[0]["player_id"] if sorted_rankings else None
        final_rankings = sorted_rankings
        win_pool, win_key = survivors, std_key
    elif getattr(cfg, "is_six_phase", False):
        # v0.34 Total Wipeout (OQ-4): breach depth is ignored; rank ONLY by the standard hierarchical
        # tiebreakers: Money > Active Colored dice in Ready > Research > fewest Under Development.
        # breach_depth / net_score stay recorded for telemetry only. Python's stable sort keeps
        # player-index order for fully shared ranks.
        rankings.sort(key=wipe_key, reverse=True)
        for rank_idx, r in enumerate(rankings):
            r["rank"] = rank_idx + 1
        winner_id = rankings[0]["player_id"] if rankings else None
        final_rankings = rankings
        win_pool, win_key = rankings, wipe_key
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

    # v0.37.0 telemetry: who would have won on Corporate Secrets held, and was a paid place tied?
    pre_bonus_winner_ids: List[int] = []
    tied_paid_place = False
    if bonus_on:
        pre_pool = [dict(r, secrets=r["secrets_before_bonus"]) for r in rankings if not r["is_patient_zero"]]
        pre_pool.sort(key=win_key, reverse=True)
        if pre_pool:
            top = win_key(pre_pool[0])
            pre_bonus_winner_ids = [r["player_id"] for r in pre_pool if win_key(r) == top]
        group_sizes: Dict[int, int] = {}
        for place, _ in awards.values():
            group_sizes[place] = group_sizes.get(place, 0) + 1
        tied_paid_place = any(size >= 2 and bonus_schedule[place - 1] > 0
                              for place, size in group_sizes.items() if place - 1 < len(bonus_schedule))
    changed_winner = bonus_on and set(pre_bonus_winner_ids) != set(winner_ids)
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
        end_triggers=list(engine.state.end_triggers),
        market_collapse_pids=list(engine.state.market_collapse_pids),
        market_collapse_round=engine.state.market_collapse_round,
        version_comparisons=[r.as_dict() for r in engine.state.version_comparisons],
        tiebreak_decided_by=_tiebreak_decided_by(win_pool, win_key),
        setup=_setup_record(engine),
        collapse_trigger_pids_were_secret_leaders=list(engine.state.market_collapse_secret_leaders),
        market_collapse_context=dict(engine.state.market_collapse_context),
        double_version_fill_events=engine.state.double_version_fill_events,
        market_leader_bonus_awarded=bonus_on,
        market_leader_bonus_schedule=bonus_schedule,
        pre_bonus_winner_ids=pre_bonus_winner_ids,
        market_leader_bonus_changed_winner=changed_winner,
        market_leader_bonus_tied_paid_place=tied_paid_place,
    )
