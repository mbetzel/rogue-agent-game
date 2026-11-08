"""Lever A one-at-a-time constant sweep (docs/specs/lever_a_roster_upgrade_spec.md §7).

Baseline pods (v0.37, 3P, 600 games per cell by default), seeds ``42 + P*100000 + idx``, the ``_bot_classes``
rotation from ``tests/fixtures/v035_parity/capture`` (same as ``run_reference_bot_validation.py --cells baseline``).

Each task carries a fully built ``GameConfig`` (pickled into the worker). The script never mutates a config after
construction (H-LA-5: rollout clones share ``config``; flipping ``bot_pr_push`` mid-game would flip every clone).
Illegal cells (``push_min_share <= dump_max_share``) are skipped with a logged reason.

Window telemetry is counted here by wrapping ``sim.bots.pr_push_policy.window`` per worker (read-only counter);
sim code is never changed for telemetry.

Usage: python3 scripts/run_lever_a_sweep.py [--games 600] [--players 3] [--procs 8] [--cells off,on,...]
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import math
import os
import sys
import time
from multiprocessing import Pool
from typing import Any, Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "sim_results", "lever_a")

_COUNTS: Dict[str, Dict[str, int]] = {}
_MAIN_STATE: Any = None


def build_cells() -> List[Tuple[str, bool, Dict[str, Any]]]:
    """(name, bot_pr_push, PrPushParams overrides): off, on, then one-at-a-time (spec §7)."""
    cells: List[Tuple[str, bool, Dict[str, Any]]] = [("off", False, {}), ("on", True, {})]
    for v in (5, 6, 7):
        cells.append((f"push_min_share={v}", True, {"push_min_share": v, **({"dump_max_share": 4} if v == 5 else {})}))
    for v in (5, 7, 9):
        cells.append((f"push_low_gap={v}", True, {"push_low_gap": v}))
    for v in (2, 3, 4):
        cells.append((f"push_top_gap={v}", True, {"push_top_gap": v}))
    for v in (2, 3):
        cells.append((f"push_secrets_band={v}", True, {"push_secrets_band": v}))
    for v in (4, 5):
        cells.append((f"dump_max_share={v}", True, {"dump_max_share": v}))
    for g in (1, 2, 3):
        for m in (2, 3):
            cells.append((f"reach_or_threat,dump_top_gap={g},dump_threat_margin={m}", True,
                          {"dump_condition": "reach_or_threat", "dump_top_gap": g, "dump_threat_margin": m}))
    return cells


def make_config(players: int, pr_push: bool, overrides: Dict[str, Any], scope: str = "all"):
    from sim.config import GameConfig, PrPushParams

    return GameConfig.v037(num_players=players, bot_pr_push=pr_push, bot_pr_push_params=PrPushParams(**overrides),
                           bot_pr_push_scope=scope)


def _install_window_counter() -> None:
    from sim.bots import pr_push_policy as prp

    if getattr(prp, "_sweep_hooked", False):
        return
    orig = prp.window

    def counted(bot, player, state, phase4=False, hook=""):
        w = orig(bot, player, state, phase4=phase4, hook=hook)
        if state is _MAIN_STATE and getattr(bot, "pr_push_capable", False):
            c = _COUNTS.setdefault(hook or "?", {})
            c[w] = c.get(w, 0) + 1
        return w

    prp.window = counted
    prp._sweep_hooked = True


def play(task):
    global _MAIN_STATE, _COUNTS
    cell, cfg, players, seed = task
    try:
        _install_window_counter()
        from sim.engine import GameEngine
        from tests.fixtures.v035_parity.capture import _bot_classes

        classes = _bot_classes()
        off = seed % len(classes)
        bots = [classes[(off + i) % len(classes)](i) for i in range(players)]
        eng = GameEngine(cfg, bots, seed=seed)
        _MAIN_STATE = eng.state
        _COUNTS = {}
        res = eng.run_game()
        return dict(cell=cell, seed=seed, error=None, winner_ids=list(res.winner_ids),
                    names=[p.bot.name for p in eng.state.players], end_triggers=list(res.end_triggers),
                    end_reason=res.end_reason.value, wipeout=bool(res.is_total_wipeout), rounds=res.total_rounds,
                    windows=_COUNTS)
    except Exception:
        import traceback
        return dict(cell=cell, seed=seed, error=traceback.format_exc())


def wilson(k: float, n: int, z: float = 1.96) -> Tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (100 * (c - h), 100 * (c + h))


def summarise(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    ok = [r for r in rows if not r["error"]]
    seats: Dict[str, int] = {}
    wins: Dict[str, float] = {}
    trig: Dict[str, int] = {}
    win_counts: Dict[str, Dict[str, int]] = {}
    for r in ok:
        for i, nm in enumerate(r["names"]):
            seats[nm] = seats.get(nm, 0) + 1
            if i in r["winner_ids"]:
                wins[nm] = wins.get(nm, 0.0) + 1.0 / len(r["winner_ids"])
        for t in set(r["end_triggers"]):
            trig[t] = trig.get(t, 0) + 1
        for h, c in r["windows"].items():
            agg = win_counts.setdefault(h, {})
            for w, n in c.items():
                agg[w] = agg.get(w, 0) + n
    n = len(ok)
    ab = "AdaptiveBalancedBot"
    return dict(
        games=n, errors=len(rows) - n,
        adaptive_balanced_win_pct=100 * wins.get(ab, 0) / max(1, seats.get(ab, 0)),
        adaptive_balanced_win_ci95=wilson(wins.get(ab, 0), seats.get(ab, 0)),
        win_pct={k: 100 * wins.get(k, 0) / v for k, v in sorted(seats.items())},
        end_trigger_pct={k: 100 * v / max(1, n) for k, v in sorted(trig.items())},
        total_wipeout_pct=100 * sum(r["wipeout"] for r in ok) / max(1, n),
        avg_rounds=sum(r["rounds"] for r in ok) / max(1, n),
        window_decisions=win_counts,
    )


def output_name(players: int, games: int, scope: str = "all", cells: Optional[str] = None,
                pr_push: bool = True) -> str:
    """``sweep[_off][_nonref][_c-<cells>]_{P}p_{games}.json``; long cell lists fall back to a sha1 tag."""
    from sim.run_naming import overrides_tag, scope_tag
    c = overrides_tag({"cells": cells}) if cells else ""
    c = c[len("cells="):] if c.startswith("cells=") else c
    return f"sweep{'' if pr_push else '_off'}{scope_tag(scope)}{f'_c-{c}' if c else ''}_{players}p_{games}.json"


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=600)
    ap.add_argument("--players", type=int, default=3)
    ap.add_argument("--procs", type=int, default=8)
    ap.add_argument("--cells", default=None, help="comma list of cell names (default: all)")
    ap.add_argument("--pr-push-scope", choices=("all", "non_reference"), default="all",
                    help="GameConfig.bot_pr_push_scope (no reference seats here, so only recorded)")
    ap.add_argument("--pr-push", choices=("off", "on"), default="on",
                    help="bot_pr_push for ad-hoc JSON cells ('{...}' in --cells); roster rule default on (FINDINGS §41)")
    ap.add_argument("--out", default=None,
                    help="default: sim_results/lever_a/<name from push/scope/cells/players/games>.json")
    ap.add_argument("--overwrite", action="store_true", help="allow replacing an existing output file")
    a = ap.parse_args(argv)
    from sim.run_naming import guard_overwrite
    a.out = a.out or os.path.join(OUT, output_name(a.players, a.games, a.pr_push_scope, a.cells, a.pr_push == "on"))
    guard_overwrite(a.out, a.overwrite)
    cells = build_cells()
    if a.cells:
        want = a.cells.split(";") if ";" in a.cells else a.cells.split(",")
        cells = [c for c in cells if c[0] in want] + [
            (w, a.pr_push == "on", json.loads(w)) for w in want if w.startswith("{")]
    out_rows = []
    skipped = []
    seen = {}
    for name, push, ov in cells:
        try:
            cfg = make_config(a.players, push, ov, a.pr_push_scope)
        except ValueError as e:
            print(f"skip {name}: {e}", flush=True)
            skipped.append(dict(cell=name, reason=str(e)))
            continue
        key = (push, tuple(sorted(dataclasses.asdict(cfg.bot_pr_push_params).items())))
        if key in seen:
            print(f"skip {name}: duplicate of {seen[key]}", flush=True)
            continue
        seen[key] = name
        tasks = [(name, cfg, a.players, 42 + a.players * 100000 + i) for i in range(a.games)]
        t0 = time.perf_counter()
        if a.procs > 1:
            with Pool(a.procs) as pool:
                rows = pool.map(play, tasks, chunksize=1)
        else:
            rows = [play(t) for t in tasks]
        s = summarise(rows)
        s.update(cell=name, bot_pr_push=push, params=dataclasses.asdict(cfg.bot_pr_push_params),
                 dump_condition=cfg.bot_pr_push_params.dump_condition, scope=cfg.bot_pr_push_scope, wall_s=time.perf_counter() - t0)
        out_rows.append(s)
        print(f"{name}: AB win {s['adaptive_balanced_win_pct']:.1f}% errors {s['errors']} wall {s['wall_s']:.0f}s",
              flush=True)
        for r in rows:
            if r["error"]:
                print(r["seed"], r["error"])
                break
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    guard_overwrite(a.out, a.overwrite)
    with open(a.out, "w") as fh:
        json.dump({"players": a.players, "games": a.games, "cells": out_rows, "skipped": skipped}, fh, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
