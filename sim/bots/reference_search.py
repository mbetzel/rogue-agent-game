"""Tier 2 reference bot: policy-portfolio rollout search (reference bot spec §5).

Searched decisions (User resolution 1, 2026-11-07): Phase 1 ``commit_shields``, Phase 4 Generic shield split
(``choose_any_shield_allocation``) and the Phase 6 Operations plan (``take_operations_actions``). Every other
hook delegates to ``AdaptiveBalancedBot`` with attribute mirroring (spec §2.1).

``ReferenceSearchEngine`` snapshots the engine at the start of Phases 1, 4 and 6 (real RNG state = realised
past). A rollout clones the snapshot, replays the phase prefix, forces the candidate at the decision, reseeds
the clone RNG **in place** (hazard H6) and plays out with every seat at its default policy
(INV-REF-RNG-01 / INV-REF-NEST-01). All seeds are ``zlib.crc32`` derived (hazard H7).
"""

from __future__ import annotations

import copy
import math
import random
import zlib
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from sim.bots.base import BaseBot
from sim.bots.accelerationist import AccelerationistBot
from sim.bots.adaptive_balanced import AdaptiveBalancedBot
from sim.bots.market_share_policy import MarketSharePolicy
from sim.bots.mixed_policy import (
    HOOK_DTYPES, force_fixed_focus, mirror_profile, post_process_operations_plan, profile_of, raw_operations_plan,
)
from sim.bots.reckless_saboteur import RecklessSaboteurBot
from sim.bots.secops_turtle import SecOpsTurtleBot
from sim.bots.venture_greed import VentureGreedBot
from sim.config import CubeColor, DieColor
from sim.engine import fast_clone
from sim.engine.core import GameEngine

# [TUNE-BOT] constants (spec §5.4 / §5.5; User resolution 4)
N_ROLLOUTS = 8
HALVING_FIRST = 4
PZ_PENALTY = -50.0
WIN_BONUS = 3.0

SEARCHED_PHASE: Dict[str, int] = {"commit_shields": 1, "choose_any_shield_allocation": 4, "take_operations_actions": 6}
_COLORS = (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN)


# [TUNE-BOT] Public Relations push / Market Share dump portfolio lines (FINDINGS §40 follow-up, 2026-11-07).
# Defined in the leaf module ``pr_push_policy`` (lever A, H-LA-4); re-exported here as the same objects.
from sim.bots.pr_push_policy import (  # noqa: E402,F401
    DUMP_FILL, DUMP_FOCUS, DUMP_POLICY, PR_PUSH_FILL, PR_PUSH_FOCUS, PR_PUSH_POLICY, _ordered_research,
)


class _ResearchLineBot(AdaptiveBalancedBot):
    """AdaptiveBalanced with a fixed research split; ``research_aware=False`` so the engine's Phase 6
    post-processing (mirrored profile, H2) keeps the split instead of re-planning it."""

    pr_first = False
    research_aware = False
    pr_push_capable = False  # lever A H-LA-6: the fixed lines are what the window imitates; never re-window

    def take_operations_actions(self, player_state, game_state, rng):
        plan = super().take_operations_actions(player_state, game_state, rng)
        if getattr(game_state.config, "is_v035_tracks", False):
            ups, regain = _ordered_research(player_state, game_state, self.pr_first,
                                            self.research_focus_v036 or self.research_focus)
            plan.track_upgrades = ups
            plan.patent_filings = 0
            if getattr(game_state.config, "is_share_regain", False):
                plan.share_regain = regain
        return plan

    def adjust_declared_choices(self, player_state, active_dice, declared, config):
        """v0.35 research auto-pick (``research_policy.adjust_declared_choices``), which the engine skips for
        ``research_aware=False``. It only touches choice faces without a shield option, so the dump line's
        Blue-first rule on shield-option faces always wins."""
        from sim.bots.research_policy import adjust_declared_choices as pick

        prev = self.__dict__.get("research_aware", None)
        self.research_aware = True
        try:
            return pick(self, player_state, active_dice, declared, config)
        finally:
            if prev is None:
                del self.research_aware
            else:
                self.research_aware = prev

    def declare_choices(self, player_state, active_dice=None, *args, **kwargs):
        out = super().declare_choices(player_state, active_dice, *args, **kwargs)
        cfg = getattr(player_state, "config", None)
        dice = active_dice if active_dice is not None else kwargs.get("rolled_dice")
        return self.adjust_declared_choices(player_state, dice or [], out, cfg) if cfg is not None else out


class PublicRelationsPushBot(_ResearchLineBot):
    """[TUNE-BOT] Phase 6: Public Relations Track then Market Share regain first; Phase 1/4: Red first."""

    pr_first = True
    research_focus_v036 = PR_PUSH_FOCUS
    market_share_policy = PR_PUSH_POLICY
    any_shield_fill_order = PR_PUSH_FILL
    market_color_preference = (DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW)


class MarketShareDumpBot(_ResearchLineBot):
    """[TUNE-BOT] Ignores Red: no Public Relations Track, no regain, Generic shields on Blue/Green first."""

    pr_first = False
    research_focus_v036 = DUMP_FOCUS
    market_share_policy = DUMP_POLICY
    any_shield_fill_order = DUMP_FILL
    market_color_preference = (DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW)

    def commit_shields(self, player_state, rolled_dice, staging_cubes, stuck_cubes, directive_code, rng):
        # Blue-option faces are committed to Blue whenever any Blue threat exists (Red is ignored)
        out = super().commit_shields(player_state, rolled_dice, staging_cubes, stuck_cubes, directive_code, rng)
        from sim.config import ShieldColor

        if staging_cubes.get(CubeColor.BLUE, 0) + stuck_cubes.get(CubeColor.BLUE, 0) > 0:
            for idx, die in enumerate(rolled_dice):
                f = die.current_face
                if f and not f.is_glitch and not f.is_shield and f.has_shield_option:
                    out[idx] = ShieldColor.BLUE
        return out


def build_portfolio(bot_id: int) -> List[Tuple[str, BaseBot]]:
    """Spec §5.3: 5 archetypes + 4 Adaptive Balanced focus rotations + 2 Market Share policy variants
    + Public Relations push + Market Share dump (13; FINDINGS §40 follow-up)."""
    members: List[Tuple[str, BaseBot]] = [(cls.__name__, cls(bot_id)) for cls in (
        AccelerationistBot, AdaptiveBalancedBot, RecklessSaboteurBot, SecOpsTurtleBot, VentureGreedBot)]
    base = tuple(AdaptiveBalancedBot.research_focus)
    for first in ("DEFENSE", "TRIAGE", "RELEASE", "PATENT"):  # PATENT = Public Relations Track (internal key)
        i = base.index(first)
        b = AdaptiveBalancedBot(bot_id)
        b.research_focus_v036 = base[i:] + base[:i]
        members.append((f"AdaptiveBalanced[{first}-first]", b))
    for label, pol in (("red_danger3", MarketSharePolicy(red_danger_value=3.0, danger_margin=3)),
                       ("leader_bonus_unaware", MarketSharePolicy(leader_bonus_aware=False))):
        b = AdaptiveBalancedBot(bot_id)
        b.market_share_policy = pol
        members.append((f"AdaptiveBalanced[{label}]", b))
    members.append(("PublicRelationsPush", PublicRelationsPushBot(bot_id)))
    members.append(("MarketShareDump", MarketShareDumpBot(bot_id)))
    for _, b in members:
        force_fixed_focus(b)
    return members


def rollout_seed(match_seed: int, bot_id: int, round_no: int, phase: int, call_index: int, k: int) -> int:
    return zlib.crc32(f"{match_seed}|{bot_id}|{round_no}|{phase}|{call_index}|{k}".encode())


def _freeze(v: Any) -> Any:
    if isinstance(v, dict):
        return tuple(sorted(((repr(k), _freeze(x)) for k, x in v.items())))
    if isinstance(v, (list, tuple)):
        return tuple(_freeze(x) for x in v)
    if isinstance(v, set):
        return tuple(sorted(repr(x) for x in v))
    if hasattr(v, "__dataclass_fields__") and not getattr(type(v), "__hash__", None):
        return (type(v).__name__,) + tuple(_freeze(getattr(v, f)) for f in v.__dataclass_fields__)
    if hasattr(v, "__dataclass_fields__") and type(v).__name__ == "Phase3ActionPlan":
        return tuple(_freeze(getattr(v, f)) for f in v.__dataclass_fields__)
    return v


def plan_key(plan: Any) -> Tuple:
    return tuple((f, _freeze(getattr(plan, f))) for f in plan.__dataclass_fields__)


def rollout_value(result: Any, pid: int) -> float:
    """Spec §5.5 from ``EndGameResult.rankings`` (final Secrets incl. any Market Leader Bonus).

    A Patient Zero seat scores ``PZ_PENALTY`` with no win share (so a Total Wipeout values every candidate
    equally, RB-14)."""
    rows = {r["player_id"]: r for r in result.rankings}
    me = rows[pid]
    if me["is_patient_zero"]:
        return PZ_PENALTY
    rivals = [r["secrets"] for q, r in rows.items() if q != pid and not r["is_patient_zero"]]
    v = float(me["secrets"] - (max(rivals) if rivals else 0))
    if pid in result.winner_ids:
        v += WIN_BONUS / len(result.winner_ids)
    return v


# ---------------------------------------------------------------------------------------------------------
# Engine subclass
# ---------------------------------------------------------------------------------------------------------
class ReferenceSearchEngine(GameEngine):
    """Snapshots at the start of Phases 1, 4 and 6; everything else is ``GameEngine`` (INV-REF-PARITY-01)."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._snap: Optional[fast_clone.Snapshot] = None
        for p in self.state.players:
            bind = getattr(p.bot, "bind", None)
            if callable(bind):
                bind(self)

    def _needs_snapshot(self) -> bool:
        return any(isinstance(p.bot, ReferenceSearchBot) and not p.is_patient_zero for p in self.state.players)

    def _take_snapshot(self, phase: int, commitments: Any = None, cr: Any = None) -> None:
        self._snap = fast_clone.snapshot(self, phase, commitments, cr) if self._needs_snapshot() else None
        for p in self.state.players:
            if isinstance(p.bot, ReferenceSearchBot):
                p.bot.begin_phase(phase)

    def _execute_phase_1(self):
        self._take_snapshot(1)
        return super()._execute_phase_1()

    def _run_phase_4_attack_resolution(self, commitments, cr):
        self._take_snapshot(4, commitments, cr)
        return super()._run_phase_4_attack_resolution(commitments, cr)

    def _run_phase_operations(self) -> None:
        self._take_snapshot(5 if self.config.operations_before_pipeline_shift else 6)
        super()._run_phase_operations()

    def _run_phase_6_operations(self) -> None:
        self._take_snapshot(6)
        super()._run_phase_6_operations()


# ---------------------------------------------------------------------------------------------------------
# Candidate generation / materialisation
# ---------------------------------------------------------------------------------------------------------
def _candidate(hook: str, member: BaseBot, kwargs: Dict[str, Any], throwaway: random.Random) -> Tuple[Any, Any]:
    """Returns ``(dedup_key, record)`` for one portfolio member (live objects are read-only, H5)."""
    if hook == "commit_shields":
        kw = dict(kwargs, rng=throwaway, staging_cubes=dict(kwargs["staging_cubes"]),
                  stuck_cubes=dict(kwargs["stuck_cubes"]))
        raw = member.commit_shields(**kw) or {}
        rec = dict(raw)
        return tuple(sorted((int(i), c.value) for i, c in rec.items())), rec
    if hook == "choose_any_shield_allocation":
        from sim.engine.phase4_attack_resolution import validate_any_shield_allocation

        remaining = dict(kwargs["remaining"])
        raw = member.choose_any_shield_allocation(
            player_state=kwargs["player_state"], remaining=dict(remaining), available_any=kwargs["available_any"],
            game_state=kwargs["game_state"], attack=dict(kwargs["attack"]))
        fill = tuple(getattr(member, "any_shield_fill_order", None) or (CubeColor.BLUE, CubeColor.RED, CubeColor.GREEN))
        legal = validate_any_shield_allocation(raw or {}, remaining, kwargs["available_any"], fill)
        return tuple(legal[c] for c in _COLORS), legal
    if hook == "take_operations_actions":
        ps, gs = kwargs["player_state"], kwargs["game_state"]
        raw = raw_operations_plan(member, ps, gs, throwaway)
        final = post_process_operations_plan(member, copy.deepcopy(raw), ps, gs, throwaway)
        return plan_key(final), (copy.deepcopy(raw), profile_of(member))
    raise KeyError(hook)


def _materialise(hook: str, record: Any, bot: BaseBot) -> Any:
    """Turns a stored record into the hook's return value (and mirrors the profile for Phase 6)."""
    if hook == "take_operations_actions":
        raw, prof = record
        mirror_profile(bot, prof)
        return copy.deepcopy(raw)
    return dict(record)


def _make_fallback_hook(name: str) -> Callable[..., Any]:
    def hook(self: Any, *args: Any, **kwargs: Any) -> Any:
        out = getattr(self.fallback, name)(*args, **kwargs)
        mirror_profile(self, profile_of(self.fallback))
        return out

    hook.__name__ = name
    return hook


# ---------------------------------------------------------------------------------------------------------
# The seat
# ---------------------------------------------------------------------------------------------------------
class ReferenceSearchBot(BaseBot):
    """Tier 2 seat (spec §5.1). Must run inside a ``ReferenceSearchEngine``; otherwise plays as the fallback."""

    def __init__(self, bot_id: int, match_seed: int, n_rollouts: int = N_ROLLOUTS, halving_first: int = HALVING_FIRST,
                 portfolio: Optional[List[Tuple[str, BaseBot]]] = None, name: str = "ReferenceSearchBot") -> None:
        super().__init__(bot_id, name)
        self.match_seed = int(match_seed)
        self.n_rollouts = n_rollouts
        self.halving_first = halving_first
        self.fallback = force_fixed_focus(AdaptiveBalancedBot(bot_id))
        self.portfolio = portfolio if portfolio is not None else build_portfolio(bot_id)
        for _, m in self.portfolio:
            force_fixed_focus(m)
        # lever A scope "non_reference": these never window (read only in that mode)
        for m in [self.fallback] + [m for _, m in self.portfolio]:
            m.pr_push_reference_owned = True
        self.engine: Any = None
        self.phase_log: List[Tuple[str, Any]] = []
        self._phase: Optional[int] = None
        self.stats: Dict[str, Any] = {"searched": 0, "rollouts": 0, "search_entries": 0, "distinct_hist": {},
                                      "by_hook": {}}
        self.rollout_trace: Optional[List[Tuple[int, int, int]]] = None  # (decision #, candidate #, seed); tests
        mirror_profile(self, profile_of(self.fallback))

    def bind(self, engine: Any) -> None:
        self.engine = engine

    def begin_phase(self, phase: int) -> None:
        self._phase = phase
        self.phase_log = []

    # --- searched hooks ---------------------------------------------------------------------------------
    def commit_shields(self, player_state, rolled_dice, staging_cubes, stuck_cubes, directive_code, rng):
        return self._searched("commit_shields", dict(
            player_state=player_state, rolled_dice=rolled_dice, staging_cubes=staging_cubes,
            stuck_cubes=stuck_cubes, directive_code=directive_code, rng=rng))

    def choose_any_shield_allocation(self, player_state, remaining, available_any, game_state, attack):
        return self._searched("choose_any_shield_allocation", dict(
            player_state=player_state, remaining=remaining, available_any=available_any, game_state=game_state,
            attack=attack))

    def take_operations_actions(self, player_state, game_state, rng):
        return self._searched("take_operations_actions", dict(player_state=player_state, game_state=game_state))

    def take_phase3_actions(self, player_state, game_state, rng):
        return self.take_operations_actions(player_state, game_state, rng)

    # --- search -----------------------------------------------------------------------------------------
    def _snapshot_ok(self, hook: str) -> bool:
        eng = self.engine
        snap = getattr(eng, "_snap", None) if eng is not None else None
        expected = (5 if (eng is not None and getattr(eng.config, "operations_before_pipeline_shift", False) and hook == "take_operations_actions") else SEARCHED_PHASE[hook])
        return (snap is not None and snap.phase == expected == self._phase
                and snap.round_no == eng.state.current_round)

    def generate_candidates(self, hook: str, kwargs: Dict[str, Any]) -> List[Tuple[str, Any, Any]]:
        """Deduplicated ``(label, key, record)`` list, fallback first (spec §5.2). Never touches ``engine.rng``."""
        seen: Dict[Any, int] = {}
        out: List[Tuple[str, Any, Any]] = []
        for i, (label, member) in enumerate([("fallback", self.fallback)] + list(self.portfolio)):
            key, rec = _candidate(hook, member, kwargs, random.Random(zlib.crc32(f"cand|{self.match_seed}|{i}".encode())))
            if key not in seen:
                seen[key] = len(out)
                out.append((label, key, rec))
        return out

    def _searched(self, hook: str, kwargs: Dict[str, Any]) -> Any:
        if not self._snapshot_ok(hook):
            rec = _candidate(hook, self.fallback, kwargs, random.Random(0))[1]
            return _materialise(hook, rec, self)
        eng = self.engine
        self.stats["search_entries"] += 1
        g0 = eng.rng.getstate()
        cands = self.generate_candidates(hook, kwargs)
        if eng.rng.getstate() != g0:  # H1 guard (INV-REF-RNG-01)
            raise RuntimeError("candidate generation consumed the live engine RNG")
        hist = self.stats["distinct_hist"]
        hist[len(cands)] = hist.get(len(cands), 0) + 1
        best = 0
        if len(cands) > 1:
            best = self._search(hook, cands)
            self.stats["searched"] += 1
            bh = self.stats["by_hook"]
            bh[hook] = bh.get(hook, 0) + 1
        rec = cands[best][2]
        self.phase_log.append((hook, rec))
        return _materialise(hook, rec, self)

    def _search(self, hook: str, cands: List[Tuple[str, Any, Any]]) -> int:
        eng = self.engine
        call_index = len(self.phase_log)
        phase = (5 if (eng is not None and getattr(eng.config, "operations_before_pipeline_shift", False) and hook == "take_operations_actions") else SEARCHED_PHASE[hook])
        seeds = [rollout_seed(self.match_seed, self.bot_id, eng.state.current_round, phase, call_index, k)
                 for k in range(self.n_rollouts)]  # INV-REF-CRN-01: shared by every candidate
        decision_no = self.stats["search_entries"]
        values: Dict[int, List[float]] = {i: [] for i in range(len(cands))}
        alive = list(range(len(cands)))
        stages = (self.halving_first, self.n_rollouts - self.halving_first)
        used = 0
        for si, n in enumerate(stages):
            for c in alive:
                for k in range(used, used + n):
                    if self.rollout_trace is not None:
                        self.rollout_trace.append((decision_no, c, seeds[k]))
                    values[c].append(self.rollout(hook, call_index, cands[c][2], seeds[k]))
            used += n
            if si == 0 and len(alive) > 2:
                keep = math.ceil(len(alive) / 2)
                alive = sorted(alive, key=lambda c: (-sum(values[c]) / len(values[c]), c))[:keep]
                alive.sort()
        return min(alive, key=lambda c: (-sum(values[c]) / len(values[c]), c))

    def rollout(self, hook: str, call_index: int, record: Any, seed: int) -> float:
        snap = self.engine._snap
        clone, commitments, cr = fast_clone.from_snapshot(snap)
        clone.state.pr_push_rollout = True  # lever A scope "non_reference": rollouts keep old behaviour
        forced_self: Optional[ForcedChoiceBot] = None
        for p in clone.state.players:
            b = p.bot
            if isinstance(b, ReferenceSearchBot):
                target = (call_index, hook, record, seed) if b is self else None
                p.bot = ForcedChoiceBot(b, list(b.phase_log), target, clone)
                if b is self:
                    forced_self = p.bot
            elif callable(getattr(b, "for_clone", None)):
                p.bot = b.for_clone(clone)
        self.stats["rollouts"] += 1
        fast_clone.resume_round(clone, snap.phase, commitments, cr)
        result = clone.run_game() if not clone.state.game_over else clone.evaluate_end_game()
        if forced_self is None or not forced_self.reseeded:
            # INV-REF-RNG-01: a missed forced decision would roll out on the copied real RNG (clairvoyance)
            raise RuntimeError(
                f"rollout never reached the forced {hook} call #{call_index} for seat {self.bot_id} "
                f"(round {snap.round_no}, phase {snap.phase}); the clone RNG was not reseeded")
        return rollout_value(result, self.bot_id)


class ForcedChoiceBot(BaseBot):
    """The reference seat inside a clone (INV-REF-NEST-01): replays this phase's searched decisions, forces the
    candidate at the target call and reseeds the clone RNG in place, then plays as the fallback."""

    def __init__(self, source: ReferenceSearchBot, log: List[Tuple[str, Any]], target: Optional[Tuple], engine: Any) -> None:
        super().__init__(source.bot_id, source.name)
        self.fallback = source.fallback
        self.log = log
        self.target = target
        self.engine = engine
        self.calls = 0
        self.reseeded = False
        mirror_profile(self, profile_of(source))

    def _forced(self, hook: str, kwargs: Dict[str, Any]) -> Any:
        i = self.calls
        self.calls += 1
        if i < len(self.log):
            h, rec = self.log[i]
            if h != hook:
                raise RuntimeError(f"prefix replay drift: expected {h}, got {hook}")
            return _materialise(hook, rec, self)
        if self.target is not None and i == self.target[0]:
            _, h, rec, seed = self.target
            if h != hook:
                raise RuntimeError(f"prefix replay drift at target: expected {h}, got {hook}")
            self.engine.rng.seed(seed)  # H6: in place, so engine.rng is state.rng still
            self.reseeded = True
            return _materialise(hook, rec, self)
        return _materialise(hook, _candidate(hook, self.fallback, kwargs, random.Random(0))[1], self)

    def commit_shields(self, player_state, rolled_dice, staging_cubes, stuck_cubes, directive_code, rng):
        return self._forced("commit_shields", dict(
            player_state=player_state, rolled_dice=rolled_dice, staging_cubes=staging_cubes,
            stuck_cubes=stuck_cubes, directive_code=directive_code, rng=rng))

    def choose_any_shield_allocation(self, player_state, remaining, available_any, game_state, attack):
        return self._forced("choose_any_shield_allocation", dict(
            player_state=player_state, remaining=remaining, available_any=available_any, game_state=game_state,
            attack=attack))

    def take_operations_actions(self, player_state, game_state, rng):
        return self._forced("take_operations_actions", dict(player_state=player_state, game_state=game_state))

    def take_phase3_actions(self, player_state, game_state, rng):
        return self.take_operations_actions(player_state, game_state, rng)


for _name in HOOK_DTYPES:
    if _name not in SEARCHED_PHASE:
        setattr(ReferenceSearchBot, _name, _make_fallback_hook(_name))
        setattr(ForcedChoiceBot, _name, _make_fallback_hook(_name))
del _name
