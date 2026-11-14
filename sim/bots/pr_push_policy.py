"""Lever A: Public Relations push and Market Share dump windows (docs/specs/lever_a_roster_upgrade_spec.md).

Leaf module (hazard H-LA-4): imports only ``sim.config`` and ``market_share_policy`` at module level. The
``research_policy`` and ``phase4_attack_resolution`` imports are lazy. ``reference_search`` re-exports the line
constants and ``_ordered_research`` from here (same objects).

Everything is a pure function of ``(bot attributes, player, state)``: no RNG, no writes, no cached state
(INV-LA-RNG-01 / INV-LA-STATELESS-01). The switch is ``state.config.bot_pr_push`` (default off), the thresholds
``state.config.bot_pr_push_params``. All values are ``[TUNE-BOT]`` heuristics, not rules.
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence, Tuple

from sim.bots import market_share_policy as msp
from sim.bots.market_share_policy import MarketSharePolicy
from sim.config import CubeColor, DieColor

NONE, PUSH, DUMP = "none", "push", "dump"

# [TUNE-BOT] Public Relations push / Market Share dump lines (FINDINGS §40 follow-up, 2026-11-07)
PR_PUSH_POLICY = MarketSharePolicy(red_base_value=5.0, red_danger_value=3.0, danger_margin=4, red_buy_share_frac=1.0)
PR_PUSH_FOCUS = ("PATENT", "DEFENSE", "TRIAGE", "RELEASE")  # PATENT = Public Relations Track (internal key)
PR_PUSH_FILL = (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN)
DUMP_POLICY = MarketSharePolicy(red_base_value=-10.0, red_danger_value=0.0, red_collapse_value=0.0,
                                comparison_weight=0.0, danger_margin=-1000, red_buy_share_frac=-1.0,
                                leader_bonus_aware=False)
DUMP_FOCUS = ("DEFENSE", "TRIAGE", "RELEASE", "PATENT")  # PATENT never bought by the dump line
DUMP_FILL = (CubeColor.BLUE, CubeColor.GREEN, CubeColor.RED)

PUSH_COLORS = (DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW)
DUMP_COLORS = (DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW)


def _ordered_research(player: Any, state: Any, pr_first: bool, focus: Sequence[str],
                      pr_cap: int = 4) -> Tuple[List[str], int]:
    """Greedy research split ``(track_upgrades, share_regain)`` (no RNG).

    ``pr_first``: Public Relations Track steps (up to level ``pr_cap``), then Market Share regain (post-upgrade
    rate), then the other tracks. Otherwise: the research-policy want-list without the Public Relations Track
    and no regain. ``pr_cap=4`` is the portfolio push line's behaviour."""
    from sim.bots.research_policy import LEVEL_ATTR, ResearchPolicy, _want_list
    from sim.engine import research_tracks

    cfg = state.config
    costs = cfg.track_step_costs
    max_ups = getattr(cfg, "max_hardware_upgrades_per_turn", 2)
    res = int(player.research_tokens)
    orig_lv = {t: int(getattr(player, LEVEL_ATTR[t])) for t in LEVEL_ATTR}
    lv = dict(orig_lv)
    upgrades: List[str] = []

    def buy(t: str) -> bool:
        nonlocal res
        if len(upgrades) >= max_ups:
            return False
        if lv[t] >= 4:
            return False
        c = int(costs[lv[t]])
        if lv[t] == orig_lv[t] and research_tracks.is_track_encrypted(player, t):
            c *= 2
        if res < c:
            return False
        res -= c
        lv[t] += 1
        upgrades.append(t)
        return True

    regain = 0
    if pr_first:
        while lv["PATENT"] < pr_cap and buy("PATENT"):
            pass
        if getattr(cfg, "share_regain_currency", "RESEARCH") == "MONEY":
            regain = 0
        elif getattr(cfg, "is_share_regain", False) and getattr(player, "market_share", None) is not None:
            lvl = max(0, min(4, lv["PATENT"]))
            cost, cap = int(cfg.share_regain_cost_by_level[lvl]), int(cfg.share_regain_cap_by_level[lvl])
            room = max(0, min(cap, int(player.market_share_max) - int(player.market_share)))
            if cost > 0:
                regain = min(room, res // cost)
                res -= regain * cost
        for t in focus:
            if t != "PATENT":
                buy(t)
    else:
        others = tuple(t for t in focus if t != "PATENT")
        for t in _want_list(ResearchPolicy(focus_order=others), lv):  # type: ignore[arg-type]
            if t == "PATENT" or lv[t] >= 4:
                continue
            if not buy(t):
                break
    return upgrades, regain


ordered_research = _ordered_research


# ---------------------------------------------------------------------------
# Window (spec §3; User resolution 5: Phase 4 reads the start-of-Phase-4 Market Share)
# ---------------------------------------------------------------------------
def _share(p: Any, state: Any, phase4: bool) -> int:
    return msp._phase4_start_share(p, state) if phase4 else int(p.market_share)


def window(bot: Any, player: Any, state: Any, phase4: bool = False, hook: str = "") -> str:
    """``PUSH`` / ``DUMP`` / ``NONE`` for one AdaptiveBalanced decision. ``hook`` is a telemetry label only."""
    cfg = state.config
    if not (getattr(cfg, "bot_pr_push", False) and getattr(bot, "pr_push_capable", False)
            and msp.is_aware(state) and player.market_share is not None and not player.is_patient_zero):
        return NONE
    if getattr(cfg, "bot_pr_push_scope", "all") == "non_reference" and (
            getattr(bot, "pr_push_reference_owned", False) or getattr(state, "pr_push_rollout", False)):
        return NONE  # measurement mode: reference fallback / portfolio / rollouts keep old behaviour
    p = cfg.bot_pr_push_params
    rivals = [q for q in state.players
              if q is not player and not q.is_patient_zero and q.market_share is not None]  # H-LA-1
    if not rivals:  # sole survivor: nothing to race for
        return NONE
    ms = _share(player, state, phase4)
    shares = [_share(q, state, phase4) for q in rivals]
    lo, hi = min(shares), max(shares)
    if ms <= p.dump_max_share:
        if p.dump_condition == "share_only":
            return DUMP
        threat = ms <= msp.red_pressure(state) + p.dump_threat_margin
        if ms - hi <= -p.dump_top_gap or threat:
            return DUMP
        return NONE  # variant: low but in reach and not threatened
    sl = int(player.secrets) - max(int(q.secrets) for q in rivals)
    if (int(state.current_version_index) <= p.push_max_version and ms >= p.push_min_share
            and ms - lo <= p.push_low_gap and ms - hi <= p.push_top_gap and abs(sl) <= p.push_secrets_band):
        return PUSH
    return NONE


def policy_for_window(w: str, bot: Any) -> MarketSharePolicy:
    if w == PUSH:
        return PR_PUSH_POLICY
    if w == DUMP:
        return DUMP_POLICY
    return msp.policy_for(bot)


def effective_policy(bot: Any, player: Any, state: Any, hook: str = "") -> MarketSharePolicy:
    return policy_for_window(window(bot, player, state, hook=hook), bot)


def preferred_colors(bot: Any, player: Any, state: Any, threats: Dict[CubeColor, int],
                     hook: str = "dice") -> List[DieColor]:
    """Market purchase colour order (also the Prometheus discounted purchase, User resolution 6)."""
    w = window(bot, player, state, hook=hook)
    if w == PUSH:
        return list(PUSH_COLORS)
    if w == DUMP:
        return list(DUMP_COLORS)
    if threats[CubeColor.RED] > threats[CubeColor.BLUE]:
        return [DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW]
    return [DieColor.BLUE, DieColor.RED, DieColor.GREEN, DieColor.YELLOW]


def windowed_any_shield_allocation(w: str, player: Any, remaining: Dict[CubeColor, int], available_any: int,
                                   state: Any, attack: Dict[CubeColor, int], bot: Any) -> Dict[CubeColor, int]:
    """Greedy split with the window's policy, returned already legal and complete (H-LA-2, INV-LA-LEGAL-01).

    Push window (spec amendment 1, Blue-safe): the push split is used only if it blocks at least
    ``default[Blue] - push_blue_slack`` Blue cubes, where ``default`` is the bot's ordinary (no-window) split
    (``msp.policy_for(bot)``, legalised with ``bot.any_shield_fill_order`` as the engine will); otherwise the
    default split is returned unchanged. Dump window unchanged."""
    from sim.engine.phase4_attack_resolution import validate_any_shield_allocation

    pol = PR_PUSH_POLICY if w == PUSH else DUMP_POLICY
    fill = PR_PUSH_FILL if w == PUSH else DUMP_FILL
    raw = msp.default_any_shield_allocation(player, remaining, available_any, state, attack, pol)
    out = validate_any_shield_allocation(raw, remaining, available_any, fill)
    if w == PUSH:
        raw_default = msp.default_any_shield_allocation(player, remaining, available_any, state, attack,
                                                        msp.policy_for(bot))
        default = validate_any_shield_allocation(raw_default, remaining, available_any, tuple(
            getattr(bot, "any_shield_fill_order", None) or (CubeColor.BLUE, CubeColor.RED, CubeColor.GREEN)))  # as the engine
        slack = int(state.config.bot_pr_push_params.push_blue_slack)
        if int(out.get(CubeColor.BLUE, 0)) < int(default.get(CubeColor.BLUE, 0)) - slack:
            return default
    return out
