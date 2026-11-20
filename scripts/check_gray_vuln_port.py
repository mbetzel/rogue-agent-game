"""Port-fidelity check (docs/specs/gray_vuln_b23_spec.md §10.4, T-FID-1): native v0.50 vs the monkeypatch probe.

  native v050_roster                                  vs probe play(("B23","GA","a1_penL2",P,seed))
  native v050_roster(bot_research_mode=THINNING_AWARE) vs probe play(("B23","S","a1_penL2",P,seed))

End reason, rounds, winners and per-seat Secrets must be identical. Native runs and probe runs use separate worker pools
(the probe monkeypatches module functions inside its workers). Quiet; prints one line per arm / player count.
  python3 scripts/check_gray_vuln_port.py --games 50 --players 2,3,4
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

ARMS = (("GA", "v050_roster", {}), ("S", "v050_roster", {"bot_research_mode": "THINNING_AWARE"}))


def _native(task: Tuple[str, Dict[str, Any], int, int]) -> Dict[str, Any]:
    from scripts.run_gray_vuln_sweep import play

    cfg, ov, players, seed = task
    return play((cfg, "mixed1", players, seed, ov, False))


def _probe(task: Tuple[str, int, int]) -> Dict[str, Any]:
    from scripts.probe_gray_vuln_mitigation import play

    pol, players, seed = task
    return play(("B23", pol, "a1_penL2", players, seed))


def _sig(r: Dict[str, Any]) -> Tuple:
    seats = sorted(r["seats"], key=lambda s: s["seat"])
    return (r["end"], r["rounds"], tuple(s["win"] > 0 for s in seats), tuple(s["secrets"] for s in seats))


def check(games: int, players: List[int], seed0: int, procs: int) -> Optional[Tuple]:
    first_bad: Optional[Tuple] = None
    for pol, cfg, ov in ARMS:
        for pl in players:
            seeds = list(range(seed0, seed0 + games))
            with Pool(procs) as pool:
                nat = pool.map(_native, [(cfg, ov, pl, s) for s in seeds])
            with Pool(procs) as pool:
                prb = pool.map(_probe, [(pol, pl, s) for s in seeds])
            bad = [s for s, a, b in zip(seeds, nat, prb) if _sig(a) != _sig(b)]
            print(f"arm {pol:<2} {pl}P: {games - len(bad)}/{games} identical" + (f"  first divergent seed {bad[0]}" if bad else ""))
            if bad and first_bad is None:
                i = seeds.index(bad[0])
                first_bad = (pol, pl, bad[0], _sig(nat[i]), _sig(prb[i]))
    return first_bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=50)
    ap.add_argument("--players", default="2,3,4")
    ap.add_argument("--seed0", type=int, default=42)
    ap.add_argument("--procs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    a = ap.parse_args()
    bad = check(a.games, [int(x) for x in a.players.split(",")], a.seed0, a.procs)
    if bad:
        print("FAIL first divergence (arm, players, seed, native, probe):", bad)
        return 1
    print("PASS: native port identical to the probe")
    return 0


if __name__ == "__main__":
    sys.exit(main())
