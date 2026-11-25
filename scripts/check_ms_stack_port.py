"""Port check: v0.52.0 engine (``v052_roster``) vs the probe arm STACKTOP+AWARET+CAP25+S321
(``scripts/probe_ms_ties.py``, a monkeypatch prototype), same seeds and setups, mixed1 roster.

  python3 scripts/check_ms_stack_port.py --players 2,3,4 --games 200

Expect close aggregates, not identity. Known, intended gaps (spec section 11): the engine adds stack-read Customer
Poaching / Red Signature targets (R2), the trimmed Section 5 tiebreakers (R3), simultaneous Phase 3 / Red / corruption
batches, and ticks SETEC Corp at the move. Each metric prints probe, port, the difference and its size in standard
errors (``z``; ``|z| > 2.5`` is flagged). ``--ahead0`` zeroes the spec section 7 real-height term in the port's bots (the probe's AWARET never had it).
Probe and port run in separate worker pools: the probe monkeypatches
engine modules inside its workers only.
"""
from __future__ import annotations

import argparse
import math
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

ARM = "STACKTOP+AWARET+CAP25+S321"
# metric -> (kind, key). kind "pct" has a binomial SE; "mean" uses the per-game sample SE.
METRICS = (("rounds", "mean"), ("PZ", "pct"), ("MC", "pct"), ("SING", "pct"), ("elim", "pct"), ("win_sec", "mean"),
           ("co_spread", "spread"), ("seat_spread", "spread"), ("mlb_sec_pg", "mean"), ("lead_chg_pg", "mean"),
           ("end_spread", "mean"))


def port_game(task):
    """One v052_roster game, shaped like a probe record so ``probe_ms_ties.summarize`` reads it."""
    from scripts.run_v380_secret_faces_sweep import build_engine

    players, seed, ahead0 = task
    if ahead0:  # ablation: bots ignore the real height when staying put (what the probe's AWARET did)
        from sim.bots import market_share_policy as msp

        msp.ahead_on_space = lambda *a, **k: 0
    eng = build_engine("v052_roster", "mixed1", players, seed, {})
    res = eng.run_game()
    n = players
    first = int(res.setup.get("first_player_index_start", 0))
    nwin = max(1, len(res.winner_ids))
    by_pid = {r["player_id"]: r for r in res.rankings}
    t = res.ms_tie or {}
    seats = []
    for i, p in enumerate(eng.state.players):
        r = by_pid[p.player_id]
        seats.append({"win": (1.0 / nwin) if p.player_id in res.winner_ids else 0.0, "secrets": r["secrets"],
                      "pz": bool(p.is_patient_zero), "seat": (i - first) % n,
                      "company": str(r.get("company_code")).lower()})
    tel = Counter({"rounds_obs": t.get("rounds_obs", 0), "top_tie": t.get("top_same_space", 0),
                   "top_tie_cap": t.get("top_same_space_at_max", 0), "any_tie": t.get("any_same_space", 0),
                   "mlb_awards": t.get("mlb_awards", 0), "mlb_tie1": t.get("mlb_raw_tie_1st", 0),
                   "mlb_eff_tie1": t.get("mlb_effective_tie_1st", 0),
                   "mlb_secrets": sum(t.get("mlb_secrets_by_seat", {}).values()),
                   "lead_change": t.get("lead_changes", 0), "lead_back": t.get("lead_back", 0)})
    ms_end = [p.market_share for p in eng.state.players if not p.is_patient_zero]
    return {"end": res.end_reason.value, "rounds": res.total_rounds, "seats": seats, "tel": dict(tel),
            "ms_end_tie": int(len(ms_end) != len(set(ms_end))),
            "ms_end_spread": (max(ms_end) - min(ms_end)) if ms_end else 0,
            "unique_winner": len(res.winner_ids) == 1}




def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--players", default="2,3,4")
    ap.add_argument("--games", type=int, default=200)
    ap.add_argument("--seed0", type=int, default=42)
    ap.add_argument("--ahead0", action="store_true",
                    help="ablation: zero the spec section 7 ahead_on_space term in the port's bots (probe-like AWARET)")
    ap.add_argument("--procs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    a = ap.parse_args()
    from multiprocessing import Pool

    for pl in [int(x) for x in a.players.split(",")]:
        seeds = range(a.seed0, a.seed0 + a.games)
        with Pool(a.procs) as pool:  # fresh workers: the probe patches engine modules in-process
            from scripts import probe_ms_ties as probe

            probe_recs = pool.map(probe.play, [(ARM, pl, s) for s in seeds], chunksize=8)
        with Pool(a.procs) as pool:
            port_recs = pool.map(port_game, [(pl, s, a.ahead0) for s in seeds], chunksize=8)
        from scripts import probe_ms_ties as probe

        sp, sq = probe.summarize(probe_recs), probe.summarize(port_recs)
        n = a.games
        print(f"== {pl}P, {n} games, seeds {a.seed0}..{a.seed0 + n - 1}: probe {ARM} vs port v052_roster")
        print(f"{'metric':14s}{'probe':>9s}{'port':>9s}{'diff':>9s}{'z':>7s}")
        for key, kind in METRICS:
            x, y = sp[key], sq[key]
            if kind == "pct":
                pbar = (x + y) / 200.0
                se = 100.0 * math.sqrt(max(1e-9, 2 * pbar * (1 - pbar) / n))
            elif kind == "spread":
                se = None  # a max-minus-min of noisy win rates has no simple SE: shown, never flagged
            else:
                vals_p = _per_game(probe_recs, key)
                vals_q = _per_game(port_recs, key)
                se = math.sqrt(_var(vals_p) / n + _var(vals_q) / n) or 1e-9
            if se is None:
                print(f"{key:14s}{x:9.2f}{y:9.2f}{y - x:9.2f}{'':>7s}  (spread: indicative only)")
                continue
            z = (y - x) / se
            print(f"{key:14s}{x:9.2f}{y:9.2f}{y - x:9.2f}{z:7.1f}{'  <-- gap' if abs(z) > 2.5 else ''}")
        shared = 100 * sum(1 for r in probe_recs if sum(1 for s in r["seats"] if s["win"] > 0) != 1) / n
        print(f"{'unique winner':14s}{100 - shared:9.1f}{100 * sum(r['unique_winner'] for r in port_recs) / n:9.1f}  (% of games)")
        print(f"{'mlb_eff_tie1':14s}{sp['mlb_eff_tie1']:9.2f}{sq['mlb_eff_tie1']:9.2f}  (both must be 0)")
        print(f"{'any_tie':14s}{sp['any_tie']:9.2f}{sq['any_tie']:9.2f}  (raw same-space rounds, % of rounds)")
    return 0


def _per_game(recs, key):
    if key == "rounds":
        return [r["rounds"] for r in recs]
    if key == "win_sec":
        return [sum(s["secrets"] for s in r["seats"] if s["win"] > 0) / max(1, sum(1 for s in r["seats"] if s["win"] > 0))
                for r in recs]
    if key == "mlb_sec_pg":
        return [r["tel"].get("mlb_secrets", 0) for r in recs]
    if key == "lead_chg_pg":
        return [r["tel"].get("lead_change", 0) for r in recs]
    if key == "end_spread":
        return [r["ms_end_spread"] for r in recs]
    return [0.0 for _ in recs]


def _var(xs):
    m = sum(xs) / max(1, len(xs))
    return sum((x - m) ** 2 for x in xs) / max(1, len(xs) - 1)


if __name__ == "__main__":
    sys.exit(main())
