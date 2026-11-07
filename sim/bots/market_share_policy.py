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
    """Market Share steps the bot wants before any track upgrade (0..cap), spec §5.3 step 1."""
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
    pol = policy_for(bot)
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
