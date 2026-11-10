"""Fast engine clone, phase-start snapshot and resumable round tail (reference bot spec §5.6 / §6).

Sim-only tooling for the Tier 2 reference bot (``sim/bots/reference_search.py``). Nothing in the normal game
loop imports this module, so games without a reference seat are unaffected (INV-REF-PARITY-01).

``clone_engine`` copies a running ``GameEngine`` about 20x faster than ``copy.deepcopy``:
- immutable / never-mutated-in-play objects are shared (``GameConfig``, ``Face``, Variant / Version Cards,
  Client Companies, White Hat Operatives, bots, enums);
- builtin containers are copied recursively; every other object with a ``__dict__`` (``GameState``,
  ``PlayerState``, ``CubeTower``, ``Die``, records) is rebuilt generically through an ``id()`` memo, so
  aliasing is preserved and new mutable attributes are picked up without a field list;
- the RNG is copied by state into **one** new ``random.Random`` shared by ``engine.rng`` and ``state.rng``
  (hazard H6: the two must stay the same object).

``resume_round`` re-implements the tail of ``GameEngine._run_round_six_phase`` (``core.py``) from Phase 1,
Phase 4 or Phase 6, without telemetry. Any edit to ``_run_round_six_phase`` must be mirrored here
(drift guard: RB-07 in ``tests/test_reference_bot.py``, extended to v0.38 by ``test_rb07_v038_*``).
v0.38 (spec v380 §10): every Secret face / Processing Box / Glitched Shield Slot step lives inside the phase
functions (Phase 1 round-start reset, Phase 5 step 3b graduation clear, end-game stranded pass in
``evaluate_end_game``), so ``_run_round_six_phase`` and this tail are unchanged; the new PlayerState fields are
plain ints / dicts / lists and ``Die.secret_pending`` is atomic, so the ``Die`` fast path stays valid.
RSP-1 (spec §14.5.3 step 10): the Phase 1 Red-bank flag reset lives in ``phase1_roll_deploy.execute_phase_1`` and
the Red Secret payout hook at the end of ``phase5_pipeline_shift.execute_pipeline_shift``, so this tail is again
unchanged (drift guard ``test_rb07_v038c_*``); the new GameState / Die fields are plain values.
"""

from __future__ import annotations

import copy
import random
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from sim.config import EndGameReason, GameConfig
from sim.entities import ArchetypeCard, Company, CorruptionSpace, Die, Face, VariantCard, VersionCard, WhiteHat
from sim.engine.state import _UnderDevelopmentProxy
from sim.bots.base import BaseBot
from sim.bots.market_share_policy import MarketSharePolicy

_ATOMIC = (int, float, str, bool, bytes, type(None), complex, range, type)
# Shared by reference, never copied. Bot objects (BaseBot) are shared between the live game and every clone:
# this is only safe while non-reference bots keep no state that changes after __init__ (hazard H5; Mixed draws
# are pure). A bot that starts caching per-game state on ``self`` must be copied per clone instead
# (guard: RB-18 in tests/test_reference_bot.py).
_SHARED = (GameConfig, Face, VariantCard, VersionCard, CorruptionSpace, Company, WhiteHat, ArchetypeCard,
           BaseBot, MarketSharePolicy, Enum, random.Random)


def _cp(v: Any, memo: Dict[int, Any]) -> Any:
    t = type(v)
    if t in (int, str, bool, float) or v is None:
        return v
    if t is list:
        return [_cp(x, memo) for x in v]
    if t is dict:
        return {k: _cp(x, memo) for k, x in v.items()}
    if isinstance(v, _ATOMIC) or isinstance(v, _SHARED):
        return v
    if t is set or t is frozenset:
        return t(v)  # elements are hashable (immutable in practice)
    if t is tuple:
        return tuple(_cp(x, memo) for x in v)
    key = id(v)
    hit = memo.get(key)
    if hit is not None:
        return hit
    if t is Die:
        new = object.__new__(Die)
        memo[key] = new
        # every Die field is atomic, an Enum, a frozen Face, or the never-mutated faces list: share them
        new.__dict__ = v.__dict__.copy()
        return new
    if t is _UnderDevelopmentProxy:
        new = list.__new__(_UnderDevelopmentProxy)
        memo[key] = new
        list.extend(new, [_cp(x, memo) for x in v])
        new.__dict__ = {k: _cp(x, memo) for k, x in v.__dict__.items()}
        return new
    if hasattr(v, "__dict__") and not isinstance(v, (list, dict, set)):
        new = object.__new__(t)
        memo[key] = new
        new.__dict__ = {k: _cp(x, memo) for k, x in v.__dict__.items()}
        return new
    new = copy.deepcopy(v, {})  # unknown container / slotted type: correctness first
    memo[key] = new
    return new


def _copy_rng(rng: random.Random) -> random.Random:
    r = random.Random()
    r.setstate(rng.getstate())
    return r


def clone_engine(engine: Any, extras: Any = None, engine_cls: Optional[type] = None) -> Tuple[Any, Any]:
    """Returns ``(engine_clone, extras_clone)``; ``extras`` (e.g. Phase 4 commitments + CompileResult) is cloned
    with the same memo so its players / dice map onto the clone's objects. ``engine_cls`` (default: the
    original class) sets the clone's class, e.g. plain ``GameEngine`` for rollouts (INV-REF-NEST-01)."""
    memo: Dict[int, Any] = {}
    rng = _copy_rng(engine.rng)
    memo[id(engine.rng)] = rng
    if engine.state.rng is not engine.rng:  # H6: never expected, but keep the two aliased in the clone
        memo[id(engine.state.rng)] = rng
    new = object.__new__(engine_cls or type(engine))
    d = engine.__dict__.copy()
    d["rng"] = rng
    d["telemetry_history"] = list(engine.telemetry_history)
    for k in ("_ms_round_start", "_research_round_start"):
        if k in d:
            d[k] = _cp(d[k], memo)
    for k in ("_snap",):
        d.pop(k, None)
    st = engine.state
    sd = {k: _cp(x, memo) for k, x in st.__dict__.items() if k != "rng"}
    sd["rng"] = rng
    new_state = object.__new__(type(st))
    memo[id(st)] = new_state
    new_state.__dict__ = sd
    d["state"] = new_state
    new.__dict__ = d
    ex = _cp(extras, memo) if extras is not None else None
    return new, ex


class Snapshot:
    """A pristine engine copy taken at the start of a phase (real RNG state = the realised past)."""

    __slots__ = ("engine", "phase", "commitments", "cr", "round_no")

    def __init__(self, engine: Any, phase: int, commitments: Any, cr: Any, round_no: int) -> None:
        self.engine = engine
        self.phase = phase
        self.commitments = commitments
        self.cr = cr
        self.round_no = round_no


def snapshot(engine: Any, phase: int, commitments: Any = None, cr: Any = None) -> Snapshot:
    from sim.engine.core import GameEngine

    clone, extras = clone_engine(engine, (commitments, cr), engine_cls=GameEngine)
    return Snapshot(clone, phase, extras[0], extras[1], engine.state.current_round)


def from_snapshot(snap: Snapshot) -> Tuple[Any, Any, Any]:
    """Returns ``(engine, commitments, cr)`` cloned from the snapshot (the snapshot stays untouched)."""
    from sim.engine.core import GameEngine

    clone, extras = clone_engine(snap.engine, (snap.commitments, snap.cr), engine_cls=GameEngine)
    return clone, extras[0], extras[1]


def resume_round(engine: Any, phase: int, commitments: Any = None, cr: Any = None) -> None:
    """Plays the rest of the current round from the start of ``phase`` (1, 4 or 6), mirroring
    ``GameEngine._run_round_six_phase`` without telemetry snapshots."""
    s = engine.state
    if phase == 1:
        commitments = engine._execute_phase_1()
        cr = engine._run_phase_2_compiler(commitments)
        if s.game_over:
            return
        engine._run_phase_3_income(commitments)
        phase = 4
    if phase == 4:
        engine._run_phase_4_attack_resolution(commitments, cr)
        if s.game_over:
            return
        engine._run_phase_5_pipeline_shift()
        phase = 6
    if phase != 6:
        raise ValueError(f"resume_round: unsupported phase {phase}")
    engine._run_phase_6_operations()
    if s.is_final_round:
        s.game_over = True
    else:
        s.current_round += 1
        if s.current_round > s.config.max_rounds:
            s.game_over = True
            s.end_reason = EndGameReason.ROUND_LIMIT
