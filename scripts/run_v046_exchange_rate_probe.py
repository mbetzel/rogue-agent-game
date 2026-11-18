"""Step 0 exchange-rate probe (spec §14.1, on v0.45): what is +1 starting Secret worth in $ and in research?

Arms (paired seeds -> common random numbers; focal seat = seed % 3, Mixed seat = (seed + 1) % 3):
  control   no bonus (required for the deltas)
  money     +$1 per round the focal seat survives (end of its Income)
  research  +1 research token per round the focal seat survives
  secret    +1 starting Corporate Secret

Usage:  python3 scripts/run_v046_exchange_rate_probe.py [--games 1200] [--seed0 42] [--procs N] [--verbose]
Output: sim_results/v046/exchange_rate_probe.json (+ summary tables on stdout; --quiet is the default).
"""

from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import sys
from typing import Any, Dict, List, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from sim.bots.mixed_policy import MixedPolicyBot  # noqa: E402
from sim.config import GameConfig  # noqa: E402
from sim.engine import GameEngine  # noqa: E402
from sim.entities import get_random_companies, get_random_setup, get_random_white_hats  # noqa: E402
from tests.fixtures.v035_parity.capture import _bot_classes  # noqa: E402

PLAYERS = 3
ARMS: Dict[str, Dict[str, int]] = {
    "control": {},
    "money": {"probe_bonus_money_per_round": 1},
    "research": {"probe_bonus_research_per_round": 1},
    "secret": {"probe_bonus_starting_secrets": 1},
}
OUT_DEFAULT = os.path.join(ROOT, "sim_results", "v046", "exchange_rate_probe.json")


def build_engine(arm: str, seed: int) -> Tuple[GameEngine, int]:
    """v0.45 sweep setup (STANDARD deck, same RNG draws), mixed1 roster rule with the Mixed seat rotated off the focal seat."""
    classes = _bot_classes()
    rng = random.Random(seed)
    bots = [classes[(seed * PLAYERS + i) % len(classes)](i) for i in range(PLAYERS)]
    rng.shuffle(bots)
    for i, b in enumerate(bots):
        b.player_id = i
    focal = seed % PLAYERS
    bots[(seed + 1) % PLAYERS] = MixedPolicyBot((seed + 1) % PLAYERS, seed)
    variants, version_deck = get_random_setup(rng, profile="STANDARD")
    companies = get_random_companies(PLAYERS, rng)
    white_hats = get_random_white_hats(PLAYERS, rng)
    kw = dict(num_players=PLAYERS, starting_money=6, starting_gray_dice=3, starting_purple_dice=1,
              starting_purple_reserve=1, corruption_track_profile="STANDARD", enable_corporate_asymmetry=True,
              probe_bonus_seat=focal)
    kw.update(ARMS[arm])
    cfg = GameConfig.v045_roster(**kw)
    eng = GameEngine(config=cfg, bots=bots, seed=seed, variant_cards=variants, version_deck=version_deck,
                     companies=companies, white_hats=white_hats)
    return eng, focal


def play(task: Tuple[str, int]) -> Dict[str, Any]:
    arm, seed = task
    eng, focal = build_engine(arm, seed)
    res = eng.run_game()
    sec = {r["player_id"]: r["secrets"] for r in res.rankings}
    rival = max(v for k, v in sec.items() if k != focal)
    return {
        "arm": arm, "seed": seed, "focal": focal,
        "win": (1.0 / len(res.winner_ids)) if focal in res.winner_ids else 0.0,
        "secrets": sec[focal], "margin": sec[focal] - rival, "rounds": res.total_rounds,
        "units": eng.state.players[focal].probe_units_granted,
        "end": str(getattr(res.end_reason, "value", res.end_reason)),
    }


def bootstrap_ci(deltas: List[float], n: int = 2000, seed: int = 12345) -> Tuple[float, float]:
    rng = random.Random(seed)
    k = len(deltas)
    means = sorted(sum(deltas[rng.randrange(k)] for _ in range(k)) / k for _ in range(n))
    return means[int(0.025 * n)], means[int(0.975 * n) - 1]


def summarise(recs: List[Dict[str, Any]]) -> Dict[str, Any]:
    by: Dict[str, Dict[int, Dict[str, Any]]] = {a: {} for a in ARMS}
    for r in recs:
        by[r["arm"]][r["seed"]] = r
    seeds = sorted(by["control"])
    ctl = by["control"]
    out: Dict[str, Any] = {"games": len(seeds), "arms": {}}
    for a in ARMS:
        g = [by[a][s] for s in seeds]
        d_win = [by[a][s]["win"] - ctl[s]["win"] for s in seeds]
        d_mar = [by[a][s]["margin"] - ctl[s]["margin"] for s in seeds]
        lo, hi = bootstrap_ci(d_win) if a != "control" else (0.0, 0.0)
        ends: Dict[str, int] = {}
        for x in g:
            ends[x["end"]] = ends.get(x["end"], 0) + 1
        out["arms"][a] = {
            "win_share": statistics.fmean(x["win"] for x in g),
            "d_win": statistics.fmean(d_win), "d_win_ci95": [lo, hi],
            "secrets": statistics.fmean(x["secrets"] for x in g),
            "margin": statistics.fmean(x["margin"] for x in g), "d_margin": statistics.fmean(d_mar),
            "rounds": statistics.fmean(x["rounds"] for x in g),
            "units": statistics.fmean(x["units"] for x in g), "end_reasons": ends,
        }
    A = out["arms"]
    rates: Dict[str, Dict[str, float | None]] = {}
    for a in ("money", "research"):
        u = A[a]["units"]
        w = (u * A["secret"]["d_win"] / A[a]["d_win"]) if A[a]["d_win"] else None
        m = (u / A[a]["d_margin"] * A["secret"]["d_margin"]) if A[a]["d_margin"] else None
        rates[a] = {"units_per_secret_win": w, "units_per_secret_margin": m}
    vals = [v for r in rates.values() for v in r.values() if v is not None]
    mean = statistics.fmean(vals) if vals else None
    out["rates"] = rates
    out["mean_units_per_secret"] = mean
    if mean is None:
        out["decision"] = "undetermined (zero delta in an arm)"
    elif mean < 5.0:
        out["decision"] = "+1 premium is fine (< 5.0)"
    elif mean > 5.7:
        out["decision"] = "apply anti-avoid levers first (> 5.7)"
    else:
        out["decision"] = "game-designer call (5.0-5.7)"
    return out


def print_summary(s: Dict[str, Any]) -> None:
    f = lambda v: "n/a" if v is None else f"{v:.2f}"  # noqa: E731
    print(f"Exchange-rate probe: v0.45 roster, 3P, {s['games']} paired games/arm")
    print(f"{'arm':9}{'win%':>7}{'dWin%':>8}{'CI95 (pp)':>17}{'dMargin':>9}{'units':>7}{'rounds':>8}")
    for a, r in s["arms"].items():
        ci = "" if a == "control" else f"[{r['d_win_ci95'][0]*100:+.1f},{r['d_win_ci95'][1]*100:+.1f}]"
        print(f"{a:9}{r['win_share']*100:7.1f}{r['d_win']*100:+8.1f}{ci:>17}{r['d_margin']:+9.2f}{r['units']:7.2f}{r['rounds']:8.2f}")
    print("units per +1 Secret:")
    for a, r in s["rates"].items():
        print(f"  {a:9} by win {f(r['units_per_secret_win']):>7}  by margin {f(r['units_per_secret_margin']):>7}")
    print(f"  mean {f(s['mean_units_per_secret'])}  ->  {s['decision']}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--games", type=int, default=1200, help="paired games per arm (full probe = 1200)")
    ap.add_argument("--seed0", type=int, default=42)
    ap.add_argument("--procs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--verbose", action="store_true", help="also print per-arm end-reason counts")
    ap.add_argument("--quiet", action="store_true", default=True, help="(default) summary only")
    a = ap.parse_args()
    tasks = [(arm, s) for s in range(a.seed0, a.seed0 + a.games) for arm in ARMS]
    if a.procs <= 1:
        recs = [play(t) for t in tasks]
    else:
        from multiprocessing import Pool

        with Pool(a.procs) as pool:
            recs = pool.map(play, tasks, chunksize=16)
    s = summarise(recs)
    a.out = os.path.abspath(a.out) if os.path.dirname(a.out) else os.path.join(os.path.dirname(OUT_DEFAULT), a.out)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump({"args": {"games": a.games, "seed0": a.seed0}, "summary": s, "games": recs}, fh)
    print_summary(s)
    if a.verbose:
        for arm, r in s["arms"].items():
            print(f"  {arm}: ends {r['end_reasons']}")
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
