"""Reference bot check runner (reference bot spec §8).

One task = one game ``(cell, players, seed)``; workers return a compact summary dict.

Cells:
- ``baseline``: archetype rotation as in ``tests/fixtures/v036_parity`` ("mixed" scenario).
- ``mixed1``: one ``MixedPolicyBot`` seat (Tier 1), rotated by ``seed % P``.
- ``ref1``: one ``ReferenceSearchBot`` seat (Tier 2), rotated by ``seed % P``.
- ``ref_all``: every seat is a ``ReferenceSearchBot``.

Usage:
    python3 scripts/run_reference_bot_check.py --cells ref1 --players 3 --games 600 --procs 8
    python3 scripts/run_reference_bot_check.py --smoke
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from multiprocessing import Pool
from typing import Any, Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CELLS = ("baseline", "mixed1", "ref1", "ref_all")
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sim_results")


def build_engine(cell: str, players: int, seed: int):
    from sim.config import GameConfig
    from sim.engine import GameEngine
    from sim.bots.mixed_policy import MixedPolicyBot
    from sim.bots.reference_search import ReferenceSearchBot, ReferenceSearchEngine
    from tests.fixtures.v035_parity.capture import _bot_classes

    classes = _bot_classes()
    offset = seed % len(classes)
    bots: List[Any] = [classes[(offset + i) % len(classes)](i) for i in range(players)]
    special = seed % players
    cfg = GameConfig.v036(num_players=players)
    if cell == "baseline":
        return GameEngine(cfg, bots, seed=seed), []
    if cell == "mixed1":
        bots[special] = MixedPolicyBot(special, seed)
        return GameEngine(cfg, bots, seed=seed), [special]
    if cell == "ref1":
        bots[special] = ReferenceSearchBot(special, seed)
        return ReferenceSearchEngine(cfg, bots, seed=seed), [special]
    if cell == "ref_all":
        bots = [ReferenceSearchBot(i, seed) for i in range(players)]
        return ReferenceSearchEngine(cfg, bots, seed=seed), list(range(players))
    raise ValueError(f"unknown cell {cell!r}")


def play(task) -> Dict[str, Any]:
    cell, players, seed = task
    t0 = time.perf_counter()
    engine, special = build_engine(cell, players, seed)
    res = engine.run_game()
    ms = 1000.0 * (time.perf_counter() - t0)
    stats = [getattr(p.bot, "stats", None) for p in engine.state.players]
    return {
        "cell": cell, "players": players, "seed": seed, "ms": ms,
        "special": special,
        "winner_ids": list(res.winner_ids),
        "end_reason": res.end_reason.value,
        "total_rounds": res.total_rounds,
        "patient_zero": [p.player_id for p in engine.state.players if p.is_patient_zero],
        "bot_names": [p.bot.name for p in engine.state.players],
        "searched": sum(s["searched"] for s in stats if s),
        "rollouts": sum(s["rollouts"] for s in stats if s),
        "distinct_hist": _merge([s["distinct_hist"] for s in stats if s]),
    }


def _merge(hists):
    out: Dict[str, int] = {}
    for h in hists:
        for k, v in h.items():
            out[str(k)] = out.get(str(k), 0) + v
    return out


def summarise(rows: List[Dict[str, Any]], wall_s: float) -> Dict[str, Any]:
    n = len(rows)
    P = rows[0]["players"]
    win_by_type: Dict[str, List[float]] = {}
    for r in rows:
        for pid, name in enumerate(r["bot_names"]):
            share = (1.0 / len(r["winner_ids"])) if pid in r["winner_ids"] else 0.0
            w = win_by_type.setdefault(name, [0.0, 0])
            w[0] += share
            w[1] += 1
    special_win = sum((1.0 / len(r["winner_ids"])) for r in rows for s in r["special"] if s in r["winner_ids"])
    special_n = sum(len(r["special"]) for r in rows)
    ends: Dict[str, int] = {}
    for r in rows:
        ends[r["end_reason"]] = ends.get(r["end_reason"], 0) + 1
    return {
        "cell": rows[0]["cell"], "players": P, "games": n, "wall_s": wall_s,
        "ms_per_game": sum(r["ms"] for r in rows) / n,
        "searched_per_game": sum(r["searched"] for r in rows) / n,
        "rollouts_per_game": sum(r["rollouts"] for r in rows) / n,
        "distinct_hist": _merge([r["distinct_hist"] for r in rows]),
        "fair_share": 1.0 / P,
        "special_seat_win_rate": (special_win / special_n) if special_n else None,
        "win_rate_by_bot": {k: v[0] / v[1] for k, v in sorted(win_by_type.items())},
        "patient_zero_rate": sum(len(r["patient_zero"]) for r in rows) / (n * P),
        "end_reasons": ends,
    }


def run_cell(cell: str, players: int, games: int, procs: int, out_dir: str = OUT_DIR) -> Dict[str, Any]:
    tasks = [(cell, players, s) for s in range(games)]
    t0 = time.perf_counter()
    if procs > 1:
        with Pool(procs) as pool:
            rows = pool.map(play, tasks, chunksize=1)
    else:
        rows = [play(t) for t in tasks]
    summary = summarise(rows, time.perf_counter() - t0)
    os.makedirs(out_dir, exist_ok=True)
    stem = os.path.join(out_dir, f"reference_bot_{cell}_{players}p")
    with open(stem + ".json", "w", encoding="utf-8") as fh:
        json.dump({"summary": summary, "games": rows}, fh, sort_keys=True, indent=1)
    with open(stem + ".txt", "w", encoding="utf-8") as fh:
        for k, v in summary.items():
            fh.write(f"{k}: {v}\n")
    return summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cells", default="baseline,mixed1,ref1")
    ap.add_argument("--players", default="3")
    ap.add_argument("--games", type=int, default=600)
    ap.add_argument("--procs", type=int, default=8)
    ap.add_argument("--smoke", action="store_true", help="20 games per cell at 2/3/4P")
    ap.add_argument("--out-dir", default=OUT_DIR)
    a = ap.parse_args(argv)
    cells = [c.strip() for c in a.cells.split(",") if c.strip()]
    players = [int(p) for p in a.players.split(",")]
    games = a.games
    if a.smoke:
        games, players = 20, [2, 3, 4]
        if a.cells == ap.get_default("cells"):
            cells = list(CELLS)
    for c in cells:
        if c not in CELLS:
            ap.error(f"unknown cell {c}")
    for p in players:
        for c in cells:
            s = run_cell(c, p, games, a.procs, a.out_dir)
            print(f"{c} {p}P: {s['games']} games, wall {s['wall_s']:.1f}s, {s['ms_per_game']:.1f} ms/game, "
                  f"special seat win {s['special_seat_win_rate']} (fair {s['fair_share']:.3f}), "
                  f"searched/game {s['searched_per_game']:.1f}, rollouts/game {s['rollouts_per_game']:.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
