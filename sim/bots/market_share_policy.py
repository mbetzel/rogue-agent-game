"""v0.36.0 Market Share-aware bot policy (spec §5).

Active when ``config.is_market_share`` and ``config.market_share_bot_policy == "AWARE"``. ``"NAIVE"`` keeps the
hooks at their v0.35-equivalent behaviour (Generic shields Blue > Red > Green, regain only from leftovers, no
Red purchase nudge, no urgency-driven Ad Campaign use) for the ablation cell.

Everything here is a pure function of the game state: no RNG is drawn (INV-MS-RNG-01). All weights are
``[TUNE-BOT]`` heuristics, not rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from sim.config import CubeColor, DieColor
from sim.engine.market_share import expected_market_leader_bonus

if TYPE_CHECKING:
    from sim.engine.state import GameState, PlayerState

COLORS_BRG = (CubeColor.BLUE, CubeColor.RED, CubeColor.GREEN)


@dataclass(frozen=True)
class MarketSharePolicy:
    blue_value: float = 3.0  # per Secret saved
    blue_lethal_value: float = 100.0  # block that prevents a Total Data Breach
    green_value: float = 1.0  # per die kept In Production (0.2 if a White Contractor can be sacrificed; 0 if empty)
    red_base_value: float = 0.5
    red_danger_value: float = 2.0  # share after this round <= next-round Red pressure + danger_margin
    red_collapse_value: float = 6.0  # this cube would take Market Share to 0
    comparison_weight: float = 0.5  # x payout when blocking changes my comparison place (1.0 -> 0.5: below a Blue block)
    danger_margin: int = 2
    red_buy_share_frac: float = 0.5  # Red purchase nudge below this fraction of max
    collapse_seeking: bool = False  # stress slice only (kamikaze watch); never on in acceptance cells
    # v0.37.0 Market Leader Bonus valuation (spec §5; inert unless config.is_market_leader_bonus)
    leader_bonus_aware: bool = True  # sweep can turn individual seats off
    leader_bonus_time_weights: Tuple[float, float, float] = (0.3, 0.6, 1.0)  # current version index 0 / 1 / 2+
    leader_bonus_final_round_weight: float = 1.0
    payout_round_discount: float = 0.75  # [TUNE-BOT] RSP-1 per-round discount gamma on future Red Secret payouts


DEFAULT_POLICY = MarketSharePolicy()


# ---------------------------------------------------------------------------
# Activation / policy lookup
# ---------------------------------------------------------------------------
def is_aware(state: Any) -> bool:
    cfg = getattr(state, "config", None)
    return bool(cfg is not None and getattr(cfg, "is_market_share", False)
                and getattr(cfg, "market_share_bot_policy", "AWARE") == "AWARE")


def policy_for(bot: Any) -> MarketSharePolicy:
    pol = getattr(bot, "market_share_policy", None)
    return pol if isinstance(pol, MarketSharePolicy) else DEFAULT_POLICY


def leader_bonus_active(player: Any, state: Any, pol: MarketSharePolicy) -> bool:
    """v0.37.0: the Market Leader Bonus valuation applies (INV-MLB-BOT-01)."""
    cfg = getattr(state, "config", None)
    return bool(getattr(cfg, "is_market_leader_bonus", False) and is_aware(state) and pol.leader_bonus_aware)


# ---------------------------------------------------------------------------
# RSP-1 Red Secret payout valuation (spec §14.5.6). Pure, no RNG; inert unless the payout schedule is non-empty.
# ---------------------------------------------------------------------------
def payout_active(player: Any, state: Any, pol: MarketSharePolicy) -> bool:
    cfg = getattr(state, "config", None)
    return bool(getattr(cfg, "is_red_secret_payout", False) and is_aware(state) and pol.leader_bonus_aware)


def expected_payout_value(share: int, rival_shares: Any, schedule: Any) -> float:
    """``expected_market_leader_bonus`` generalised to any place schedule (same tie handling)."""
    return expected_market_leader_bonus(share, rival_shares, schedule)


def estimated_rounds_left(state: Any) -> int:
    """Rounds left including the current one: remaining Version-track space / observed Corruption fill rate,
    clamped to [1, max_rounds - current_round + 1]. [TUNE-BOT] (no prior pacing helper existed).
    Ignores Patient Zero / Market Collapse endings, so it is biased high; the RSP-1 payout valuation absorbs
    that bias with ``MarketSharePolicy.payout_round_discount`` (gamma) rather than correcting this estimate."""
    if getattr(state, "is_final_round", False):
        return 1
    rnd = max(1, int(state.current_round))
    cap_left = max(0, int(state.corruption_track_capacity) - int(state.corruption_track))
    filled = int(state.corruption_track)
    for i, v in enumerate(state.version_deck):
        if i < state.current_version_index:
            filled += int(v.track_capacity)
        elif i > state.current_version_index:
            cap_left += int(v.track_capacity)
    # observed fill per completed round, floored at 2 cubes / round (round-1 calibration vs v038c games) [TUNE-BOT]
    rate = max(2.0, filled / max(1, rnd - 1))
    est = int(-(-cap_left // rate)) if cap_left > 0 else 1
    return max(1, min(est, int(state.config.max_rounds) - rnd + 1))


def p_red_bank(q: Any, state: Any) -> float:
    """Per-round chance seat ``q`` banks a Red Secret: Red dice owned x 1/6 (capped at 1), or 1 with one pending."""
    if q.is_patient_zero:
        return 0.0
    if any(getattr(d, "secret_pending", False) and d.color == DieColor.RED for d in q.glitched_dice):
        return 1.0
    reds = sum(1 for d in q.total_dice if d.color == DieColor.RED)
    return min(1.0, reds / 6.0)


def expected_red_payouts_remaining(state: Any, pol: Optional[MarketSharePolicy] = None) -> float:
    """Discounted E_in (sum_{t<R} gamma^t x P(>= 1 Red bank)) + P_end x gamma^R (end payout; 0.5 if a Market
    Collapse looks likely and the end payout is skipped on Collapse). gamma = ``pol.payout_round_discount``; gamma = 1.0 is the undiscounted R x p + P_end."""
    if not getattr(state.config, "is_red_secret_payout", False):
        return 0.0
    gamma = (pol or DEFAULT_POLICY).payout_round_discount
    miss = 1.0
    for q in state.players:
        miss *= 1.0 - p_red_bank(q, state)
    p = 1.0 - miss
    r = estimated_rounds_left(state)
    e_in = p * (r if gamma == 1.0 else (1.0 - gamma ** r) / (1.0 - gamma))
    p_end = 0.0
    if state.config.red_secret_payout_at_end:
        low = any(int(q.market_share or 0) <= 2 for q in state.players if not q.is_patient_zero)
        skip = getattr(state.config, "red_secret_payout_skip_on_collapse", True)  # §14.5.10: paid on a Collapse too if False
        p_end = (0.5 if (skip and low and state.config.market_collapse_enabled) else 1.0) * gamma ** r
    return e_in + p_end


def payout_share_delta(player: Any, state: Any, before: int, after: int, rivals: Any = None,
                       pol: Optional[MarketSharePolicy] = None) -> float:
    """Δ expected payout value x discounted (E_in + P_end), in Corporate Secrets."""
    sched = state.config.red_secret_payout_schedule(len(state.players))
    if rivals is None:
        rivals = [int(q.market_share or 0) for q in state.players
                  if q.player_id != player.player_id and not q.is_patient_zero]
    rivals = list(rivals)
    d = expected_payout_value(after, rivals, sched) - expected_payout_value(before, rivals, sched)
    return d * expected_red_payouts_remaining(state, pol)


def leader_bonus_time_weight(state: Any, pol: MarketSharePolicy) -> float:
    if getattr(state, "is_final_round", False):
        return pol.leader_bonus_final_round_weight
    return pol.leader_bonus_time_weights[min(2, int(state.current_version_index))]


# ---------------------------------------------------------------------------
# Shared signals (pure)
# ---------------------------------------------------------------------------
def red_pressure(state: "GameState") -> int:
    return int(state.staging_cup.get(CubeColor.RED, 0)) + int(state.tower.stuck_cubes.get(CubeColor.RED, 0))


def next_comparison(state: "GameState") -> Optional[Tuple[str, int, int]]:
    """(version, payout, Black cubes needed) for the next Market Share comparison, or None if none is left.

    Versions without a payout (e.g. v1.0 once its comparison was dropped) are skipped: the Black cubes needed
    include the rest of the current track plus the full tracks of skipped versions.
    """
    cfg = state.config
    payouts = getattr(cfg, "version_share_payout", None) or {}
    done = getattr(state, "version_comparisons_done", set())
    deck = state.version_deck
    idx = state.current_version_index
    if state.pending_version_advance:
        idx += 1
        filled = int(state.overflow_black_cubes_on_next_track)
    else:
        filled = int(state.corruption_track)
    needed = 0
    while idx < len(deck) - 1:  # the last version never compares
        ver = deck[idx]
        needed += ver.track_capacity - filled
        payout = int(payouts.get(ver.version_str, 0))
        if payout > 0 and ver.version_str not in done:
            return ver.version_str, payout, max(0, needed)
        idx += 1
        filled = 0
    return None


def comparison_imminent(state: "GameState") -> Optional[Tuple[str, int, int]]:
    """The next comparison if it can fire next round (``+1`` = Phase 1 Pulse), else None."""
    nc = next_comparison(state)
    if nc is None:
        return None
    blacks = int(state.staging_cup.get(CubeColor.BLACK, 0)) + int(state.tower.stuck_cubes.get(CubeColor.BLACK, 0))
    return nc if nc[2] <= blacks + 1 else None


def place(player: "PlayerState", state: "GameState", my_share: int,
          rival_shares: Optional[Dict[int, int]] = None) -> str:
    """``"top"`` (sole top), ``"tied_top"``, ``"bottom"`` (incl. tied bottom), ``"middle"`` or ``"tied_all"``."""
    rivals = rival_shares if rival_shares is not None else {
        p.player_id: int(p.market_share or 0) for p in state.players
        if p.player_id != player.player_id and not p.is_patient_zero
    }
    if not rivals:
        return "tied_all"
    vals = list(rivals.values()) + [my_share]
    hi, lo = max(vals), min(vals)
    if hi == lo:
        return "tied_all"
    if my_share == hi:
        return "top" if vals.count(hi) == 1 else "tied_top"
    if my_share == lo:
        return "bottom"
    return "middle"


def _improves_place(before: str, after: str) -> bool:
    return (before == "bottom" and after != "bottom") or (after == "top" and before != "top")


def is_critical(player: "PlayerState", state: "GameState", pol: MarketSharePolicy, share: Optional[int] = None) -> bool:
    s = int(player.market_share if share is None else share)
    return s <= red_pressure(state) + pol.danger_margin


def _leads_in_secrets(player: "PlayerState", state: "GameState") -> bool:
    alive = [p.secrets for p in state.players if not p.is_patient_zero and p.player_id != player.player_id]
    return not alive or player.secrets > max(alive)


def _rival_red_shields(p: "PlayerState") -> int:
    from sim.engine.state import ProductionRole

    total = 0
    for d in p.in_production_dice:
        f = d.effective_face or d.current_face
        if f is not None and getattr(d, "production_role", None) == ProductionRole.RED_SHIELD and f.is_shield:
            total += f.block_amount
    return total


def _phase4_start_share(p: "PlayerState", state: "GameState") -> int:
    """Market Share at the start of this round's Phase 4 (so rivals resolved earlier are not hit twice)."""
    snap = getattr(state, "phase4_market_share_start", None) or {}
    if getattr(state, "phase4_snapshot_round", None) == getattr(state, "current_round", None) and snap.get(p.player_id) is not None:
        return int(snap[p.player_id])
    return int(p.market_share or 0)


def estimated_rival_shares(player: "PlayerState", state: "GameState", red_attack: int) -> Dict[int, int]:
    """Rivals' end-of-Phase-4 Market Share estimate: start-of-Phase-4 share - max(0, Red attack - Red shields).

    Each rival is projected exactly once from its start-of-Phase-4 share, whether or not it has already
    resolved earlier in seat order.
    """
    return {
        p.player_id: max(0, _phase4_start_share(p, state) - max(0, int(red_attack) - _rival_red_shields(p)))
        for p in state.players if p.player_id != player.player_id and not p.is_patient_zero
    }


# ---------------------------------------------------------------------------
# Phase 4: Generic shield valuation
# ---------------------------------------------------------------------------
def _green_value(player: "PlayerState", pol: MarketSharePolicy) -> float:
    if not player.in_production_dice:
        return 0.0
    if any(d.color == DieColor.WHITE for d in player.in_production_dice):
        return 0.2
    return pol.green_value


def marginal_block_value(color: CubeColor, rem: Dict[CubeColor, int], player: "PlayerState", state: "GameState",
                         attack: Dict[CubeColor, int], pol: MarketSharePolicy) -> float:
    """Value of blocking one more cube of ``color`` given the currently unblocked counts ``rem``."""
    v = _marginal_block_value_v037(color, rem, player, state, attack, pol)
    if getattr(state.config, "secret_face_enabled", False):
        from sim.bots import secret_face_policy

        return secret_face_policy.marginal_block_value(color, rem, player, state, attack, v)
    return v


def _marginal_block_value_v037(color: CubeColor, rem: Dict[CubeColor, int], player: "PlayerState",
                               state: "GameState", attack: Dict[CubeColor, int], pol: MarketSharePolicy) -> float:
    r = int(rem.get(color, 0))
    if r <= 0:
        return float("-inf")
    if color == CubeColor.BLUE:
        if player.secrets - r <= 0:
            return pol.blue_lethal_value
        return pol.blue_value + (1.0 if player.secrets <= 3 else 0.0)
    if color == CubeColor.GREEN:
        return _green_value(player, pol)
    # Red
    if not state.config.is_market_share:
        return 2.5 if player.money < r * int(getattr(state.config, "red_ransom_per_cube", 1)) else 0.8
    share = int(player.market_share or 0)
    v = pol.red_base_value
    if share - r <= 0:
        if pol.collapse_seeking and _leads_in_secrets(player, state):
            v -= pol.red_collapse_value
        else:
            v += pol.red_collapse_value
    if share - r <= red_pressure(state) + pol.danger_margin:
        v += pol.red_danger_value
    nc = comparison_imminent(state)
    if nc is not None:
        rivals = estimated_rival_shares(player, state, attack.get(CubeColor.RED, 0))
        before = place(player, state, max(0, share - r), rivals)
        after = place(player, state, max(0, share - r + 1), rivals)
        if _improves_place(before, after):
            v += pol.comparison_weight * nc[1]
    if leader_bonus_active(player, state, pol):
        # v0.37.0 (spec §5.2): expected Market Leader Bonus gained by keeping this Market Share
        sched = state.config.market_leader_bonus_schedule(len(state.players))
        rivals = list(estimated_rival_shares(player, state, attack.get(CubeColor.RED, 0)).values())
        d = (expected_market_leader_bonus(max(0, share - r + 1), rivals, sched)
             - expected_market_leader_bonus(max(0, share - r), rivals, sched))
        v += leader_bonus_time_weight(state, pol) * pol.blue_value * d
    if payout_active(player, state, pol):
        # RSP-1 (spec §14.5.6): Red Secret payouts kept by this Market Share (no rival-denial term)
        rivals = list(estimated_rival_shares(player, state, attack.get(CubeColor.RED, 0)).values())
        v += pol.blue_value * payout_share_delta(player, state, max(0, share - r), max(0, share - r + 1), rivals, pol)
    return v


def default_any_shield_allocation(player: "PlayerState", remaining: Dict[CubeColor, int], available_any: int,
                                  state: "GameState", attack: Dict[CubeColor, int],
                                  pol: Optional[MarketSharePolicy] = None) -> Dict[CubeColor, int]:
    """Greedy: each Generic shield goes to the color with the highest marginal value (ties Blue > Red > Green)."""
    pol = pol or DEFAULT_POLICY
    rem = {c: int(remaining.get(c, 0)) for c in COLORS_BRG}
    alloc = {c: 0 for c in COLORS_BRG}
    naive = getattr(state.config, "market_share_bot_policy", "AWARE") == "NAIVE"
    for _ in range(max(0, int(available_any))):
        if sum(rem.values()) <= 0:
            break
        if naive:
            best = next(c for c in COLORS_BRG if rem[c] > 0)
        else:
            vals = [(marginal_block_value(c, rem, player, state, attack, pol), -i, c) for i, c in enumerate(COLORS_BRG)]
            best = max(vals)[2]
            if rem[best] <= 0:
                break
        alloc[best] += 1
        rem[best] -= 1
    return alloc


def choose_aegis_color(player: "PlayerState", qualifying: List[CubeColor], state: "GameState",
                       remaining: Dict[CubeColor, int], attack: Dict[CubeColor, int],
                       pol: Optional[MarketSharePolicy] = None) -> Optional[CubeColor]:
    """Aegis *Baffle Echo* under MARKET_SHARE: ignore the color whose single cube has the highest marginal value."""
    if not qualifying:
        return None
    pol = pol or DEFAULT_POLICY
    rem = {c: int(remaining.get(c, 0)) for c in COLORS_BRG}
    best, best_v = None, float("-inf")
    for c in COLORS_BRG:  # tie order Blue > Red > Green
        if c not in qualifying:
            continue
        v = marginal_block_value(c, rem, player, state, attack, pol)
        if v > best_v:
            best, best_v = c, v
    if best is None or best_v == float("-inf"):
        for c in COLORS_BRG:
            if c in qualifying:
                return c
        return qualifying[0]
    return best


# ---------------------------------------------------------------------------
# Phase 6: regain urgency, Ad Campaign, Red purchase nudge
# ---------------------------------------------------------------------------
def urgent_regain(player: "PlayerState", state: "GameState", pol: MarketSharePolicy, cap: int) -> int:
    """Market Share steps the bot wants before any track upgrade (0..cap).

    v0.36.0 urgency (``_urgent_regain_v036``), raised in v2.0+ / the Final Round to the smallest regain that
    improves the expected Market Leader Bonus when the bonus is active (v0.37.0 spec §5.3)."""
    k0 = _urgent_regain_v036(player, state, pol, cap)
    if payout_active(player, state, pol) and player.market_share is not None:
        # RSP-1 (spec §14.5.6): largest regain whose payout value covers its research cost
        room = min(cap, player.market_share_max - player.market_share)
        cost = int(state.config.share_regain_cost_by_level.get(player.patent_level, 2))
        best = k0
        for k in range(1, room + 1):
            gain = pol.blue_value * payout_share_delta(player, state, player.market_share, player.market_share + k, None, pol)
            if gain >= k * cost:
                best = max(best, k)
        return best
    if (not leader_bonus_active(player, state, pol) or player.market_share is None
            or (state.current_version_index < 1 and not state.is_final_round)):
        return k0
    room = min(cap, player.market_share_max - player.market_share)
    rivals = [int(p.market_share or 0) for p in state.players
              if p.player_id != player.player_id and not p.is_patient_zero]
    if not rivals:
        return k0
    sched = state.config.market_leader_bonus_schedule(len(state.players))
    base = expected_market_leader_bonus(player.market_share, rivals, sched)
    for k in range(1, room + 1):
        if expected_market_leader_bonus(player.market_share + k, rivals, sched) > base:
            return max(k0, k)
    return k0


def _urgent_regain_v036(player: "PlayerState", state: "GameState", pol: MarketSharePolicy, cap: int) -> int:
    """v0.36.0 regain urgency, spec §5.3 step 1 (v360 spec)."""
    if player.market_share is None or player.market_share >= player.market_share_max or cap <= 0:
        return 0
    room = min(cap, player.market_share_max - player.market_share)
    if getattr(state, "is_final_round", False):
        return room
    if is_critical(player, state, pol):
        return room
    if comparison_imminent(state) is not None:
        before = place(player, state, player.market_share)
        for k in range(1, room + 1):
            if _improves_place(before, place(player, state, player.market_share + k)):
                return k
    return 0


def any_survivor_critical(state: "GameState", pol: MarketSharePolicy) -> bool:
    return any(p.market_share is not None and is_critical(p, state, pol)
               for p in state.players if not p.is_patient_zero)


def _planned_spend(plan: Any, player: "PlayerState", state: "GameState") -> int:
    cfg = state.config
    spend = 0
    for c in list(getattr(plan, "market_purchases", []) or [])[: cfg.max_market_purchases_per_turn]:
        if c != DieColor.PURPLE:
            spend += state.get_market_die_cost(c)
    if getattr(plan, "use_b2_secret", False) and player.b2_available:
        spend += cfg.b2_secret_cost
    if getattr(plan, "use_y1_secret", False) and player.y1_available:
        spend += 6
    return spend


def apply_market_share_policy(bot: Any, plan: Any, player: "PlayerState", state: "GameState") -> Any:
    """Sets Ad Campaign use and applies the Red purchase nudge (spec §5.4). No-op under RANSOM."""
    cfg = state.config
    if not getattr(cfg, "is_market_share", False) or player.market_share is None:
        return plan
    from sim.bots import pr_push_policy as prp  # lazy (H-LA-4)

    pol = prp.effective_policy(bot, player, state, hook="nudge")  # lever A window (NONE = policy_for(bot))
    aware = is_aware(state)
    cushion = 0  # Ad Campaign: used whenever affordable (balance iteration 1, B4)

    # Red purchase nudge (AWARE only): at most 1 Red per turn from this rule
    if aware:
        low = player.market_share <= pol.red_buy_share_frac * player.market_share_max or is_critical(player, state, pol)
        owned_red = sum(1 for d in player.total_dice if d.color == DieColor.RED)
        purchases = list(getattr(plan, "market_purchases", []) or [])
        if low and state.market.get(DieColor.RED, 0) > 0 and owned_red < 2 and DieColor.RED not in purchases:
            limit = cfg.max_market_purchases_per_turn
            red_cost = state.get_market_die_cost(DieColor.RED)
            new = None
            if len(purchases) < limit:
                new = purchases + [DieColor.RED]
            else:
                for i in range(len(purchases) - 1, -1, -1):
                    if purchases[i] != DieColor.RED:
                        new = purchases[:i] + purchases[i + 1:] + [DieColor.RED]
                        break
            if new is not None:
                trial_spend = sum(state.get_market_die_cost(c) for c in new[:limit] if c != DieColor.PURPLE)
                other = _planned_spend(plan, player, state) - sum(
                    state.get_market_die_cost(c) for c in purchases[:limit] if c != DieColor.PURPLE)
                if player.money - other - trial_spend >= 0 and red_cost <= player.money:
                    plan.market_purchases = new

    # Ad Campaign (R2): whenever below max and affordable after the planned spend (AWARE and NAIVE alike)
    n = int(getattr(player, "r2_actions_available", 0))
    use = 0
    if n > 0 and player.market_share < player.market_share_max:
        money = player.money - _planned_spend(plan, player, state)
        room = player.market_share_max - player.market_share
        while use < min(n, room) and money - cfg.r2_share_cost >= cushion:
            use += 1
            money -= cfg.r2_share_cost
    plan.use_r2_share = use
    return plan
