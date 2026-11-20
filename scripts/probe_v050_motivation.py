"""v0.50 post-telemetry motivation check (FINDINGS §66). Paired seeds; seat 0 is the probe seat.

Arms (config, overrides, seat-0 Gray handicap):
  M      v050_roster, all seats GRAY_AWARE
  M_def  v050_roster, seat 0 THINNING_AWARE (stock), others GRAY_AWARE   -> M - M_def = cost of not mitigating
  M_one  v050_roster, all GRAY_AWARE, seat 0 owns 1 fewer Gray from setup  -> marginal value of one Gray die
  S      v050_roster, all stock (bot_gray_aware_seats=())
  S_ga0  v050_roster, seat 0 GRAY_AWARE, others stock
  B      v049_roster + GRAY_AWARE (all), the G1 table without Pen Test L2   -> same tests on v0.49
  B_def  as B, seat 0 stock
  B_one  as B, seat 0 owns 1 fewer Gray
  python3 scripts/probe_v050_motivation.py --players 2,3,4 --games 2000
"""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.run_v380_secret_faces_sweep import build_engine  # noqa: E402

GA = {"bot_research_mode": "GRAY_AWARE"}
ARMS = {
    "M": ("v050_roster", {}, 0), "M_def": ("v050_roster", {"bot_gray_aware_seats": "others"}, 0),
    "M_one": ("v050_roster", {}, 1), "S": ("v050_roster", {"bot_gray_aware_seats": ()}, 0),
    "S_ga0": ("v050_roster", {"bot_gray_aware_seats": (0,)}, 0),
    "B": ("v049_roster", dict(GA), 0), "B_def": ("v049_roster", dict(GA, bot_gray_aware_seats="others"), 0),
    "B_one": ("v049_roster", dict(GA), 1),
}


def play(task):
    arm, players, seed = task
    cfg, ov, handicap = ARMS[arm]
    ov = dict(ov)
    if ov.get("bot_gray_aware_seats") == "others":
        ov["bot_gray_aware_seats"] = tuple(range(1, players))
    eng = build_engine(cfg, "mixed1", players, seed, ov)
    eng.state.rush_seed = seed
    if handicap:
        p0 = next(p for p in eng.state.players if p.player_id == 0)
        from sim.engine import sprint_plan
        g = next(d for d in p0.scanned_dice if d.color.name == "GRAY")  # one Current Sprint Gray to the box at setup
        p0.scanned_dice.remove(g)
        sprint_plan.prune(p0)
    res = eng.run_game()
    nwin = max(1, len(res.winner_ids))
    r0 = next(r for r in res.rankings if r["player_id"] == 0)
    p0 = next(p for p in eng.state.players if p.player_id == 0)
    return (1.0 / nwin if 0 in res.winner_ids else 0.0, r0["secrets"], p0.green_secrets_lost,
            sum(p0.gray_removed_by_source.values()), bool(p0.is_patient_zero))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--players", default="2,3,4")
    ap.add_argument("--games", type=int, default=2000)
    ap.add_argument("--seed0", type=int, default=42)
    ap.add_argument("--procs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    a = ap.parse_args()
    from multiprocessing import Pool
    with Pool(a.procs) as pool:
        for pl in [int(x) for x in a.players.split(",")]:
            for arm in a.arms.split(","):
                rs = pool.map(play, [(arm, pl, s) for s in range(a.seed0, a.seed0 + a.games)], chunksize=32)
                n = len(rs)
                m = [sum(r[i] for r in rs) / n for i in range(5)]
                print(f"{pl}P {arm:6s} seat0 win={100 * m[0]:.2f} secrets={m[1]:.2f} green_lost={m[2]:.2f} "
                      f"removed={m[3]:.2f} PZ={100 * m[4]:.1f}", flush=True)


if __name__ == "__main__":
    main()
