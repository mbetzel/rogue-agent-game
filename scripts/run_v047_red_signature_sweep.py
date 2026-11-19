"""v0.47.0 Red Signature acceptance confirm sweep (spec §9.2). Quiet; raw JSON in sim_results/v047_red_signature/.

python3 scripts/run_v047_red_signature_sweep.py --games 4000 --seed0 42
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from scripts.run_v380_secret_faces_sweep import build_engine  # noqa: E402

OUT = os.path.join(ROOT, "sim_results", "v047_red_signature")
CTRS = ("events", "gifts_to_locked", "mutual_cancels", "fizzles", "setec_gifts", "setec_ms_gained", "capped_gains", "zero_rescues")


def play(t):
    cfgname, players, seed, ov = t
    eng = build_engine(cfgname, "mixed1", players, seed, ov)
    res = eng.run_game()
    s = eng.state
    by = {r["player_id"]: r for r in res.rankings}
    nw = max(1, len(res.winner_ids))
    seats = [{"arch": p.bot.name, "co": by[p.player_id].get("company_code"),
              "win": (1.0 / nw) if p.player_id in res.winner_ids else 0.0} for p in s.players]
    wsec = [by[i]["secrets"] for i in res.winner_ids]
    return {"seed": seed, "end": res.end_reason.value, "tw": bool(res.is_total_wipeout), "rounds": res.total_rounds,
            "seats": seats, "wsec": sum(wsec) / len(wsec) if wsec else None,
            "setec": [s.setec_market_share, s.setec_corp_mlb_1st_places, s.setec_corp_mlb_2nd_places, s.setec_corp_mlb_secrets_absorbed],
            "ctr": {k: getattr(s, "signature_red_" + k) for k in CTRS}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=4000)
    ap.add_argument("--seed0", type=int, default=42)
    ap.add_argument("--procs", type=int, default=os.cpu_count() or 1)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    arms = [(f"{P}P_{n}", P, c, ov) for P in (2, 3, 4) for n, c, ov in (("v046", "v046_roster", {}), ("v047", "v047_roster", {}))]
    arms.append(("2P_v047_D1", 2, "v047_roster", {"signature_red_setec_gain": 1}))
    for name, P, c, ov in arms:
        tasks = [(c, P, s, ov) for s in range(a.seed0, a.seed0 + a.games)]
        with Pool(a.procs) as pool:
            recs = pool.map(play, tasks, chunksize=20)
        with open(os.path.join(OUT, name + ".json"), "w") as f:
            json.dump(recs, f)
        print("done", name, flush=True)


if __name__ == "__main__":
    main()
