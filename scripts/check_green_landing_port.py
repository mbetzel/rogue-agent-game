"""Port-fidelity check (docs/specs/green_landing_spec.md §9.8, INV-LAND-08): native v051_roster vs probe arm S2H1.

  native: probe ``play(("R0", P, seed))`` with the probe's monkeypatches uninstalled and ``build_engine`` swapped to
          ``v051_roster`` (so both sides share one record function)
  probe:  ``play(("S2H1", P, seed))``

Every key of the returned record must be identical except ``gpr`` (probe-only overflow instrumentation, filled only by the
monkeypatched ``resolve_green``). Native and probe runs use separate worker pools.
  python3 scripts/check_green_landing_port.py --games 200 --players 2,3,4
"""
from __future__ import annotations

import argparse
import os
import sys
from multiprocessing import Pool
from typing import Any, Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

IGNORED = ("gpr",)


def _native(task: Tuple[int, int]) -> Dict[str, Any]:
    import scripts.probe_green_drop_band as pg

    players, seed = task
    pg.install("R0")  # restore the original engine / bot functions: the native v0.51 code runs
    if not getattr(pg, "_native_wrapped", False):  # wrap once per worker (no nesting across tasks)
        pg._native_wrapped = True
        orig = pg.build_engine
        pg.build_engine = lambda cfg, roster, pl, sd, ov: orig("v051_roster" if cfg == "v050_roster" else cfg, roster, pl, sd, ov)
    return pg.play(("R0", players, seed))


def _probe(task: Tuple[int, int]) -> Dict[str, Any]:
    from scripts.probe_green_drop_band import play

    players, seed = task
    return play(("S2H1", players, seed))


def _sig(r: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in r.items() if k not in IGNORED}


def check(games: int, players: List[int], seed0: int, procs: int) -> Optional[Tuple]:
    first_bad: Optional[Tuple] = None
    for pl in players:
        seeds = list(range(seed0, seed0 + games))
        with Pool(procs) as pool:
            nat = pool.map(_native, [(pl, s) for s in seeds])
        with Pool(procs) as pool:
            prb = pool.map(_probe, [(pl, s) for s in seeds])
        bad = [s for s, a, b in zip(seeds, nat, prb) if _sig(a) != _sig(b)]
        print(f"{pl}P: {games - len(bad)}/{games} identical" + (f"  first divergent seed {bad[0]}" if bad else ""))
        if bad and first_bad is None:
            i = seeds.index(bad[0])
            diff = {k: (nat[i].get(k), prb[i].get(k)) for k in _sig(nat[i]) if nat[i].get(k) != prb[i].get(k)}
            first_bad = (pl, bad[0], diff)
    return first_bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=100)
    ap.add_argument("--players", default="2,3,4")
    ap.add_argument("--seed0", type=int, default=42)
    ap.add_argument("--procs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    a = ap.parse_args()
    bad = check(a.games, [int(x) for x in a.players.split(",")], a.seed0, a.procs)
    if bad:
        print("FAIL first divergence (players, seed, {key: (native, probe)}):", bad)
        return 1
    print("PASS: native port identical to the probe (S2H1)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
