"""Research-aware Operations policy for the v0.35.0 five-level Terminal Hardware Tracks.

Port of the ``aware_research`` prototype in ``scripts/investigate_v350_research_sweep.py`` (package D1).
Only used when ``config.is_v035_tracks``; the v0.34 per-bot research logic is untouched.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from sim.config import GameConfig
    from sim.engine.state import GameState, PlayerState

TRACKS = ("DEFENSE", "TRIAGE", "RELEASE", "PATENT")
LEVEL_ATTR = {"DEFENSE": "defense_level", "TRIAGE": "triage_level", "RELEASE": "release_level", "PATENT": "patent_level"}
DEFAULT_FOCUS = ("TRIAGE", "DEFENSE", "RELEASE", "PATENT")


@dataclass(frozen=True)
class ResearchPolicy:
    focus_order: Tuple[str, str, str, str] = DEFAULT_FOCUS
    late_secret_threshold: int = 3  # "late" when any survivor <= 3 Secrets, or the Final Round
    reserve_floor: int = 4  # file Patents with leftovers only once the focus track is at L4 and research >= this


def is_late_game(policy: ResearchPolicy, state: GameState) -> bool:
    if getattr(state, "is_final_round", False):
        return True
    survivors = [p.secrets for p in getattr(state, "players", []) if not p.is_patient_zero]
    return bool(survivors) and min(survivors) <= policy.late_secret_threshold


def plan_research(policy: ResearchPolicy, player: PlayerState, state: GameState, config: GameConfig) -> Tuple[List[str], int]:
    """Returns ``(track_upgrades, patent_filings)``.

    1. Not late: want-list = focus track up to L4, then L1 on each other track, then L2 on the 2nd track;
       buy while affordable and stop at the first unaffordable step (save toward it).
    2. If the focus track is still below L4, or research < ``reserve_floor``: no filings.
    3. Otherwise (or late game): file ``research // cost`` Patents at the post-upgrade Patents level.
    """
    costs = config.track_step_costs
    res = int(player.research_tokens)
    lv: Dict[str, int] = {t: int(getattr(player, LEVEL_ATTR[t])) for t in TRACKS}
    order = list(policy.focus_order)
    upgrades: List[str] = []
    sim_lv = dict(lv)
    if not is_late_game(policy, state):
        focus = order[0]
        wants: List[str] = [focus] * max(0, 4 - lv[focus])
        wants.extend(t for t in order[1:] if lv[t] < 1)
        if lv[order[1]] < 2:
            wants.append(order[1])
        for t in wants:
            if sim_lv[t] >= 4:
                continue
            c = int(costs[sim_lv[t]])
            if res >= c:
                upgrades.append(t)
                res -= c
                sim_lv[t] += 1
            else:
                break  # save toward this step
        if sim_lv[focus] < 4 or res < policy.reserve_floor:
            return upgrades, 0
    cost = int(config.patent_rate_by_level[min(4, sim_lv["PATENT"])][0])
    return upgrades, (res // cost if cost > 0 else 0)


def policy_for_bot(bot: Any, state: Any = None, rng: Optional[random.Random] = None) -> ResearchPolicy:
    """Resolves the bot's ``research_focus`` (or a seeded random order for ``research_focus_mode="random"``)."""
    mode = getattr(bot, "research_focus_mode", "fixed")
    if mode == "random":
        cached = getattr(bot, "_research_focus_random", None)
        if cached is None:
            r = rng if rng is not None else random.Random(getattr(bot, "bot_id", 0))
            order = list(TRACKS)
            r.shuffle(order)
            cached = tuple(order)
            bot._research_focus_random = cached
        return ResearchPolicy(focus_order=cached)  # type: ignore[arg-type]
    return ResearchPolicy(focus_order=tuple(getattr(bot, "research_focus", DEFAULT_FOCUS)))  # type: ignore[arg-type]


def apply_research_policy(bot: Any, plan: Any, player: PlayerState, state: GameState, rng: Optional[random.Random] = None) -> Any:
    """Replaces ``plan.track_upgrades`` / ``plan.patent_filings`` (v0.35 only) and drops Purple purchases."""
    from sim.config import DieColor

    cfg = getattr(state, "config", None)
    if cfg is None or not getattr(cfg, "is_v035_tracks", False):
        return plan
    if not getattr(cfg, "purple_purchasable", True):
        plan.market_purchases = [c for c in plan.market_purchases if c != DieColor.PURPLE]
        plan.buy_purple_reserve = False
        if getattr(plan, "prometheus_discount_die_color", None) == DieColor.PURPLE:
            plan.prometheus_discount_die_color = None
    if getattr(bot, "research_aware", True):
        upgrades, filings = plan_research(policy_for_bot(bot, state, rng), player, state, cfg)
        plan.track_upgrades = upgrades
        plan.patent_filings = filings
    return plan


def adjust_declared_choices(bot: Any, player: PlayerState, active_dice: List[Any], declared: Dict[int, int], config: Any) -> Dict[int, int]:
    """v0.35 (spec §7.3): take research on every choice face without a shield option."""
    if config is None or not getattr(config, "is_v035_tracks", False) or not getattr(bot, "research_aware", True):
        return declared
    if declared is None:
        declared = {}
    for idx, die in enumerate(active_dice):
        f = getattr(die, "current_face", None)
        if f and f.is_choice and not f.has_shield_option:
            for j, c in enumerate(f.choices):
                if c.patches > 0:
                    declared[idx] = j
                    break
    return declared
