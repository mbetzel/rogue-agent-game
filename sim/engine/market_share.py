"""v0.36.0 Market Share engine helpers (INV-MS-*).

- Phase 2: Market Share comparison when the final space of a non-last Version (``v1.0`` / ``v2.0``) is covered
  (``resolve_version_comparison``).
- Phase 3: Customer Poaching (R3) resolution after all players' Income (``resolve_poaches``).
- Phase 4: Market Collapse end-trigger check (``check_market_collapse``).

Every function is a no-op unless ``config.is_market_share``. No RNG is drawn anywhere in this module
(INV-MS-RNG-01): all ties are broken by seat / clockwise order.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional

from sim.config import EndGameReason
from sim.engine.state import VersionComparisonRecord

if TYPE_CHECKING:
    from sim.engine.core import GameEngine
    from sim.engine.state import GameState, PlayerState


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def add_end_trigger(state: "GameState", name: str) -> None:
    """Records an end trigger once, in firing order (telemetry only)."""
    if name not in state.end_triggers:
        state.end_triggers.append(name)


def survivors(state: "GameState") -> List["PlayerState"]:
    return [p for p in state.players if not p.is_patient_zero]


def clockwise_from(state: "GameState", start_index: int) -> List["PlayerState"]:
    n = len(state.players)
    return [state.players[(start_index + k) % n] for k in range(n)]


# ---------------------------------------------------------------------------
# Phase 2: Version comparison
# ---------------------------------------------------------------------------
def resolve_version_comparison(
    engine: "GameEngine", completed_version: str, during_spillover: bool
) -> Optional[VersionComparisonRecord]:
    """Market Share comparison after the final space of ``completed_version`` resolved (spec §4.3).

    Highest Market Share gains the payout from the bank; lowest pays the bank what they can (shortfall forgiven).
    Ties share places. Patient Zero players are excluded. At most once per version per game.
    """
    s = engine.state
    cfg = s.config
    if not cfg.is_market_share:
        return None
    payout = int((cfg.version_share_payout or {}).get(completed_version, 0))
    if payout <= 0:
        return None
    if completed_version in s.version_comparisons_done:
        return None
    s.version_comparisons_done.add(completed_version)

    eligible = [p for p in s.players if not p.is_patient_zero]
    rec = VersionComparisonRecord(
        version=completed_version,
        round_number=s.current_round,
        payout=payout,
        during_spillover=during_spillover,
        eligible_pids=[p.player_id for p in eligible],
        shares={p.player_id: int(p.market_share) for p in eligible},
        money_before={p.player_id: p.money for p in eligible},
    )
    shares = list(rec.shares.values())
    if len(eligible) < 2 or len(set(shares)) <= 1:
        rec.all_tied = True
    else:
        hi, lo = max(shares), min(shares)
        for p in eligible:  # seat order (no RNG)
            if p.market_share == hi:
                rec.top_pids.append(p.player_id)
                p.money += payout
                p.comparison_money_gained += payout
                rec.gains[p.player_id] = payout
            elif p.market_share == lo:
                rec.bottom_pids.append(p.player_id)
                paid = min(max(p.money, 0), payout)
                p.money -= paid
                p.comparison_money_paid += paid
                p.comparison_shortfall_forgiven += payout - paid
                rec.paid[p.player_id] = paid
                rec.forgiven[p.player_id] = payout - paid
    s.version_comparisons.append(rec)
    return rec


# ---------------------------------------------------------------------------
# Phase 3: Customer Poaching (R3)
# ---------------------------------------------------------------------------
def default_poach_target(actor: "PlayerState", state: "GameState", tied_pids: List[int]) -> int:
    """Default R3 tie-break: most Corporate Secrets, then first clockwise from the actor."""
    n = len(state.players)
    by_id = {p.player_id: p for p in state.players}
    order = {pid: (pid - actor.player_id) % n for pid in tied_pids}
    return min(tied_pids, key=lambda pid: (-by_id[pid].secrets, order[pid]))


def queue_poach(engine: "GameEngine", player: "PlayerState", die_id: int) -> None:
    engine.state._pending_poaches.append((player.player_id, die_id))


def resolve_poaches(engine: "GameEngine") -> List[Dict]:
    """Resolves pending Customer Poaching faces (INV-MS-R3-01, User resolution 2026-11-06 #3).

    Clockwise from the First Player, then die order within a player. The rival with the most Market Share
    (> 0, not Patient Zero) loses ``r3_poach_amount``; the actor gains that much, capped at its maximum
    (the rival still loses Market Share when the actor is at max). "Most" is re-evaluated for every poach.
    """
    s = engine.state
    pending = list(s._pending_poaches)
    s._pending_poaches.clear()
    if not pending or not s.config.is_market_share:
        return []
    events: List[Dict] = []
    by_pid: Dict[int, List[int]] = {}
    for pid, die_id in pending:
        by_pid.setdefault(pid, []).append(die_id)
    by_id = {p.player_id: p for p in s.players}
    amount = int(s.config.r3_poach_amount)
    for actor in clockwise_from(s, s.first_player_index):
        for die_id in by_pid.get(actor.player_id, []):
            ev = {"round": s.current_round, "actor": actor.player_id, "die_id": die_id, "target": None,
                  "moved": 0, "gained": 0, "reason": "ok"}
            if actor.is_patient_zero or actor.market_share is None:
                ev["reason"] = "actor_patient_zero"
            else:
                cands = [p for p in s.players
                         if p.player_id != actor.player_id and not p.is_patient_zero and (p.market_share or 0) > 0]
                if not cands:
                    ev["reason"] = "no_target"
                else:
                    top = max(p.market_share for p in cands)
                    tied = [p.player_id for p in cands if p.market_share == top]
                    if len(tied) == 1:
                        tpid = tied[0]
                    else:
                        hook = getattr(actor.bot, "choose_poach_target", None)
                        tpid = hook(actor, s, list(tied)) if callable(hook) else None
                        if tpid not in tied:
                            tpid = default_poach_target(actor, s, tied)
                    target = by_id[tpid]
                    taken = -target.change_market_share(-amount, "poach_lost")
                    gained = actor.change_market_share(taken, "poach_gained")
                    ev.update(target=tpid, moved=taken, gained=gained,
                              reason="ok" if gained == taken else "actor_at_max")
            s.r3_events.append(ev)
            events.append(ev)
    return events


# ---------------------------------------------------------------------------
# Phase 4: Market Collapse
# ---------------------------------------------------------------------------
def check_market_collapse(engine: "GameEngine") -> bool:
    """End of Phase 4: any surviving player at 0 Market Share makes this round the Final Round (INV-MS-COLLAPSE-01).

    Nobody is eliminated; ``game_over`` is never set here. ``end_reason`` keeps any higher-precedence trigger.
    """
    s = engine.state
    if s.game_over or not s.config.is_market_share or not s.config.market_collapse_enabled:
        return False
    alive = survivors(s)
    hit = [p.player_id for p in alive if (p.market_share or 0) <= 0]
    if not hit:
        return False
    first = not s.market_collapse_triggered
    s.market_collapse_triggered = True
    if first:
        s.market_collapse_round = s.current_round
        top_secrets = max(p.secrets for p in alive)
        by_id = {p.player_id: p for p in s.players}
        s.market_collapse_pids = list(hit)
        s.market_collapse_secret_leaders = [by_id[pid].secrets == top_secrets for pid in hit]
        leaders = [p.player_id for p in alive if p.secrets == top_secrets]
        s.market_collapse_context = {
            "survivor_pids": [p.player_id for p in alive],
            "strict_leader_pid": leaders[0] if len(leaders) == 1 else None,  # unique Secrets leader, else None
        }
    add_end_trigger(s, "market_collapse")
    s.is_final_round = True
    if s.final_round_trigger_phase is None:
        s.final_round_trigger_phase = 4
    if s.end_reason == EndGameReason.NONE:
        s.end_reason = EndGameReason.MARKET_COLLAPSE
    return True
