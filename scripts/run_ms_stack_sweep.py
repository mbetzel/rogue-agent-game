"""v0.52.0 Market Share stack sweep (docs/specs/ms_stack_order_spec.md section 8). Reads native telemetry only.

  python3 scripts/run_ms_stack_sweep.py --players 2,3,4 --games 1200 --seed0 42

Arms: B (``--base`` v051_roster + ms_tie_telemetry, the baseline) and M (``--config`` v052_roster), mixed1 roster.
Prints one quiet summary table per player count (outcomes, tie telemetry, win spreads); writes JSON under
``sim_results/ms_stack_v052/``. ``--set`` takes JSON config overrides applied to both arms (e.g. a sweep arm such as
``{"market_share_stack_setup": "FIRST_SEAT_TOP"}`` is only legal on the M arm: use ``--set-m`` for that).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, List, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.run_v380_secret_faces_sweep import build_engine  # noqa: E402

OUT_DIR = os.path.join(ROOT, "sim_results", "ms_stack_v052")


def play(task: Tuple[str, str, int, int, Dict[str, Any]]) -> Dict[str, Any]:
    config_name, roster, players, seed, overrides = task
    eng = build_engine(config_name, roster, players, seed, overrides)
    res = eng.run_game()
    first = int(res.setup.get("first_player_index_start", 0))
    nwin = max(1, len(res.winner_ids))
    seats = []
    by_pid = {r["player_id"]: r for r in res.rankings}
    for i, p in enumerate(eng.state.players):
        r = by_pid[p.player_id]
        src = r.get("secrets_by_source", {})
        seats.append({"win": (1.0 / nwin) if p.player_id in res.winner_ids else 0.0, "secrets": r["secrets"],
                      "pz": bool(p.is_patient_zero), "seat": (i - first) % players,
                      "company": str(r.get("company_code")).lower(),
                      "mlb": src.get("red_secret_payout", 0) + src.get("red_secret_payout_end", 0)})
    return {"end": res.end_reason.value, "rounds": res.total_rounds, "seats": seats, "tel": res.ms_tie or {},
            "unique_winner": len(res.winner_ids) == 1, "tied_paid": bool(res.market_leader_bonus_tied_paid_place),
            "tiebreak": res.tiebreak_decided_by}


def play_all(config_name: str, roster: str, players: int, games: int, seed0: int, ov: Dict[str, Any],
             procs: int) -> List[Dict[str, Any]]:
    from multiprocessing import Pool

    tasks = [(config_name, roster, players, s, ov) for s in range(seed0, seed0 + games)]
    if procs <= 1:
        return [play(t) for t in tasks]
    with Pool(procs) as pool:
        return pool.map(play, tasks, chunksize=max(1, len(tasks) // (procs * 8)))


def _m(xs: List[float]) -> float:
    return sum(xs) / max(1, len(xs))


def metrics(recs: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(recs)
    ends = Counter(r["end"] for r in recs)
    seats = [x for r in recs for x in r["seats"]]
    by_co, by_seat = defaultdict(list), defaultdict(list)
    for x in seats:
        by_co[x["company"]].append(x["win"])
        by_seat[x["seat"]].append(x["win"])
    spread = lambda d: 100 * (max(_m(v) for v in d.values()) - min(_m(v) for v in d.values()))  # noqa: E731
    t: Counter = Counter()
    by_src: Dict[str, Counter] = {"arrivals_occupied": Counter(), "overtakes": Counter()}
    for r in recs:
        for k, v in r["tel"].items():
            if isinstance(v, (int, float)):
                t[k] += v
            elif k in by_src:
                by_src[k].update(v)
    pct = lambda a, b: 100 * t[a] / max(1, t[b])  # noqa: E731
    return {
        "games": n, "rounds": _m([r["rounds"] for r in recs]),
        "PZ": 100 * ends["patient_zero"] / n, "MC": 100 * ends["market_collapse"] / n,
        "SING": 100 * ends["singularity"] / n,
        "mlb_sec_pg": _m([sum(x["mlb"] for x in r["seats"]) for r in recs]),
        "win_sec": _m([x["secrets"] for x in seats if x["win"] > 0]),
        "co_spread": spread(by_co), "seat_spread": spread(by_seat),
        "win_by_seat": {k: round(100 * _m(v), 1) for k, v in sorted(by_seat.items())},
        "raw_tie1": pct("mlb_raw_tie_1st", "mlb_awards"), "eff_tie1": pct("mlb_effective_tie_1st", "mlb_awards"),
        "eff_tie_paid": pct("mlb_effective_tie_paid", "mlb_awards"),
        "stack_decided_paid": pct("mlb_stack_decided_paid", "mlb_awards"),
        "top_same": pct("top_same_space", "rounds_obs"), "top_same_max": pct("top_same_space_at_max", "rounds_obs"),
        "any_same": pct("any_same_space", "rounds_obs"),
        "lead_chg_pg": t["lead_changes"] / n, "lead_back": pct("lead_back", "lead_changes"),
        "end_spread": t["ms_end_spread"] / n, "end_same": 100 * t["ms_end_same_space"] / n,
        "poach_dec_pg": t["poach_stack_decided"] / n, "sig_dec_pg": t["sig_red_stack_decided"] / n,
        "tb_stack": 100 * t["tiebreak_by_stack"] / n,
        "arrivals": dict(by_src["arrivals_occupied"]), "overtakes": dict(by_src["overtakes"]),
        "unique_winner": 100 * _m([r["unique_winner"] for r in recs]), "tied_paid": sum(r["tied_paid"] for r in recs),
    }


KEYS = ("rounds", "PZ", "MC", "SING", "mlb_sec_pg", "win_sec", "co_spread", "seat_spread", "raw_tie1", "eff_tie1",
        "top_same", "any_same", "lead_chg_pg", "end_spread", "poach_dec_pg", "sig_dec_pg", "tb_stack")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default="v052_roster")
    ap.add_argument("--base", default="v051_roster")
    ap.add_argument("--roster", default="mixed1")
    ap.add_argument("--players", default="2,3,4")
    ap.add_argument("--games", type=int, default=1200)
    ap.add_argument("--seed0", type=int, default=42)
    ap.add_argument("--set", default="{}", help="JSON overrides applied to both arms")
    ap.add_argument("--set-m", default="{}", help="JSON overrides applied to the M arm only")
    ap.add_argument("--procs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--no-save", action="store_true")
    a = ap.parse_args()
    ov = json.loads(a.set)
    ov_m = {**ov, **json.loads(a.set_m)}
    ov_b = {**ov, "ms_tie_telemetry": True}  # the baseline measures the same telemetry (passive, INV-MS-TEL-01)
    out: Dict[str, Any] = {}
    print("arm  P  " + " ".join(f"{k:>10s}" for k in KEYS))
    for pl in [int(x) for x in a.players.split(",")]:
        for label, cfg, o in (("B", a.base, ov_b), ("M", a.config, ov_m)):
            recs = play_all(cfg, a.roster, pl, a.games, a.seed0, o, a.procs)
            m = metrics(recs)
            out[f"{label}_{pl}P"] = m
            print(f"{label:3s}  {pl}  " + " ".join(f"{m[k]:10.2f}" for k in KEYS), flush=True)
            if label == "M":
                print(f"      seat wins {m['win_by_seat']}  unique_winner {m['unique_winner']:.1f}%  "
                      f"tied_paid {m['tied_paid']}  eff_tie_paid {m['eff_tie_paid']:.2f}%  arrivals {m['arrivals']}")
    if not a.no_save:
        os.makedirs(OUT_DIR, exist_ok=True)
        with open(os.path.join(OUT_DIR, f"sweep_{a.games}g_s{a.seed0}.json"), "w") as fh:
            json.dump(out, fh, indent=1, sort_keys=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
