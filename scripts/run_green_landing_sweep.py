"""v0.51.0 Green landing + one hit per round sweep (docs/specs/green_landing_spec.md §10). Reads native telemetry only.

  python3 scripts/run_green_landing_sweep.py --players 2,3,4 --games 1200 --seed0 42,1242 --assert-invariants

Arms: M (``--config`` v051_roster), B0 (``--base`` v050_roster, delta comparator), B48 (``--income-base`` v048_roster; "" skips).
``--seed0`` may be a comma list (e.g. 42,1242): each block is reported and the guardrails are judged on the pool.
Every guardrail row computes its own pass state (None = not evaluated, never a silent PASS).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.run_v380_secret_faces_sweep import build_engine  # noqa: E402

OUT_DIR = os.path.join(ROOT, "sim_results", "green_landing_v051")
REF = {  # per player count: S2H1 probe references (plan §7)
    "pzmc": {2: 70.6, 3: 73.5, 4: 80.0}, "elim": {2: 30.1, 3: 26.3, 4: 23.4}, "rounds": {2: 8.22, 3: 8.14, 4: 8.10},
    "green": {2: 2.77, 3: 2.40, 4: 2.23}, "b2b": {2: 24.0, 3: 20.0, 4: 18.0},
}
TOL = {"pzmc": 2.0, "elim": 2.0, "rounds": 0.15, "green": 0.15, "b2b": 3.0}


def coerce(ov: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(ov)
    for k in ("vuln_hit_landing_by_band", "vuln_band_thresholds", "vuln_min_target_by_version", "bot_gray_aware_seats"):
        if isinstance(out.get(k), list):
            out[k] = tuple(out[k])
    return out


# --------------------------------------------------------------------------------------------------
# One game (native telemetry: events carry ``land`` / ``capped``; the end row carries the _v051_row keys when on)
# --------------------------------------------------------------------------------------------------
def play(task: Tuple[str, str, int, int, Dict[str, Any], bool]) -> Dict[str, Any]:
    config_name, roster, players, seed, overrides, check = task
    eng = build_engine(config_name, roster, players, seed, coerce(overrides))
    res = eng.run_game()
    s, cfg = eng.state, eng.config
    floor = min(cfg.vuln_min_target_by_version)
    nwin = max(1, len(res.winner_ids))
    by_pid = {r["player_id"]: r for r in res.rankings}
    inc = inc_n = dead = 0
    g: Counter = Counter()
    hits_rr: Dict[int, Counter] = defaultdict(Counter)   # round -> pid -> hits
    worst = 0
    capped_on = bool(getattr(cfg, "vuln_one_hit_per_round", False))
    bad: List[str] = []
    for t in res.telemetry_history:
        for pid, x in t.income_by_player.items():
            tot = x["money"] + x["research"]
            inc += tot
            inc_n += 1
            dead += tot <= 1
        evs = t.green_hit_events
        g["cubes"] += t.green_cubes_resolved
        g["no_target"] += t.green_cubes_no_target
        g["cap_no_target"] += t.green_cubes_cap_no_target
        n_empty = sum(1 for e in evs if not e["pids"])
        if check:
            if t.green_cubes_no_target != n_empty:
                bad.append(f"INV-LAND-06 no_target r{t.round_number}")
            if not capped_on and t.green_cubes_cap_no_target:
                bad.append(f"INV-LAND-06 cap_no_target without cap r{t.round_number}")
            if t.green_cubes_cap_no_target > t.green_cubes_no_target:
                bad.append(f"INV-LAND-06 cap_no_target > no_target r{t.round_number}")
        for pid, lost in t.green_secrets_lost_by_player.items():
            worst = max(worst, lost)
        for e in evs:
            if not e["pids"]:
                continue
            g[f"band_{e['damage']}"] += 1
            g["hit_cubes"] += 1
            if e.get("land") is not None and e["land"] >= floor:
                g["land_unsafe"] += 1
            for pid in e["pids"]:
                hits_rr[e["round"]][pid] += 1
    multi = sum(1 for r in hits_rr.values() for x in r.values() if x >= 2)
    hit_sr = sum(1 for r in hits_rr.values() for x in r.values() if x >= 1)
    b2b = sum(1 for rn, r in hits_rr.items() for pid in r if pid in hits_rr.get(rn + 1, {}))
    if check:
        if capped_on and multi:
            bad.append(f"INV-LAND-03 multi-hit seat-rounds {multi}")
        if worst > 3:
            bad.append(f"worst per-seat round Green loss {worst} > 3")
    seats = []
    corr3 = 0
    for p in s.players:
        r = by_pid[p.player_id]
        corr3 += int((r.get("corruption_vuln_into_target") or {}).get(3, 0))
        seats.append({
            "seat": p.player_id, "win": (1.0 / nwin) if p.player_id in res.winner_ids else 0.0, "secrets": r["secrets"],
            "company": str(r.get("company_code")).lower(), "wh": str(r.get("white_hat_code")).lower(),
            "pz": bool(p.is_patient_zero), "green_lost": p.green_secrets_lost, "pen_level": int(p.defense_level),
        })
    return {"seed": seed, "end": res.end_reason.value, "rounds": res.total_rounds, "wipeout": bool(res.is_total_wipeout),
            "inc": inc, "inc_n": inc_n, "dead": dead, "g": dict(g), "worst": worst, "multi": multi, "hit_sr": hit_sr,
            "b2b": b2b, "corr3": corr3, "seats": seats, "bad": bad}


def play_all(cfg: str, roster: str, players: int, games: int, seed0: int, ov: Dict[str, Any], procs: int,
             check: bool) -> List[Dict[str, Any]]:
    tasks = [(cfg, roster, players, sd, ov, check) for sd in range(seed0, seed0 + games)]
    if procs <= 1:
        return [play(t) for t in tasks]
    from multiprocessing import Pool

    with Pool(procs) as pool:
        return pool.map(play, tasks, chunksize=max(1, len(tasks) // (procs * 8)))


# --------------------------------------------------------------------------------------------------
# Metrics and guardrails
# --------------------------------------------------------------------------------------------------
def _m(xs: List[float]) -> float:
    return sum(xs) / max(1, len(xs))


def metrics(recs: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(recs)
    seats = [x for r in recs for x in r["seats"]]
    ends = Counter(r["end"] for r in recs)
    g: Counter = Counter()
    for r in recs:
        g.update(r["g"])
    hit_cubes = max(1, g["hit_cubes"])
    hit_sr = max(1, sum(r["hit_sr"] for r in recs))
    by_co: Dict[str, List[float]] = defaultdict(list)
    by_wh: Dict[str, List[float]] = defaultdict(list)
    for x in seats:
        by_co[x["company"]].append(x["win"])
        by_wh[x["wh"]].append(x["win"])
    spread = lambda d: 100 * (max(_m(v) for v in d.values()) - min(_m(v) for v in d.values()))  # noqa: E731
    co = {k: round(100 * _m(v), 1) for k, v in sorted(by_co.items())}
    wh = {k: round(100 * _m(v), 1) for k, v in sorted(by_wh.items())}
    pick = lambda d, name: next((v for k, v in d.items() if name in k), None)  # noqa: E731
    return {
        "games": n, "rounds": _m([r["rounds"] for r in recs]),
        "pzmc_pct": 100 * (ends["patient_zero"] + ends["market_collapse"]) / n,
        "pz_pct": 100 * ends["patient_zero"] / n, "mc_pct": 100 * ends["market_collapse"] / n,
        "sing_pct": 100 * ends["singularity"] / n, "tw_pct": 100 * _m([r["wipeout"] for r in recs]),
        "elim_pct": 100 * _m([x["pz"] for x in seats]), "green_lost_pg": _m([x["green_lost"] for x in seats]),
        "b2b_pct": 100 * sum(r["b2b"] for r in recs) / hit_sr, "multi_hit_sr": sum(r["multi"] for r in recs),
        "worst_round_loss": max((r["worst"] for r in recs), default=0),
        "income_per_seat_round": sum(r["inc"] for r in recs) / max(1, sum(r["inc_n"] for r in recs)),
        "dead_pct": 100 * sum(r["dead"] for r in recs) / max(1, sum(r["inc_n"] for r in recs)),
        "land_unsafe_pct": 100 * g["land_unsafe"] / hit_cubes, "capped_cubes_pg": g["cap_no_target"] / n,
        "band_mix": {k: round(100 * g[f"band_{k}"] / hit_cubes, 1) for k in (1, 2, 3)},
        "corr3_into_target_pg": sum(r["corr3"] for r in recs) / n,
        "pen_l4_pct": 100 * _m([x["pen_level"] >= 4 for x in seats]),
        "win_helix": pick(co, "helix"), "win_aegis": pick(co, "aegis"), "win_spook": pick(wh, "spook"),
        "co_spread": spread(by_co), "wh_spread": spread(by_wh), "win_by_co": co,
        "win_by_wh": wh,
        "invariant_violations": sum(len(r["bad"]) for r in recs), "first_violation": next((r["bad"][0] for r in recs if r["bad"]), None),
    }


def guardrails(m: Dict[str, Any], b48: Optional[Dict[str, Any]], pl: int, checked: bool) -> List[Tuple[str, str, str, Optional[bool]]]:
    def band(key: str, val: float, name: str, fmt: str) -> Tuple[str, str, str, Optional[bool]]:
        ref, tol = REF[key][pl], TOL[key]
        return (name, format(val, fmt), f"{ref:{fmt}} +/- {tol}", abs(val - ref) <= tol)

    rows = [
        band("pzmc", m["pzmc_pct"], "L1 PZ + MC %", ".1f"),
        band("elim", m["elim_pct"], "L2 eliminated seats %", ".1f"),
        band("rounds", m["rounds"], "L3 rounds (mean)", ".2f"),
        band("green", m["green_lost_pg"], "L4 Green Secrets lost / player-game", ".2f"),
        band("b2b", m["b2b_pct"], "L5 back-to-back hit %", ".1f"),
        ("L6 multi-hit seat-rounds", str(m["multi_hit_sr"]), "== 0", m["multi_hit_sr"] == 0),
        ("L7 worst per-seat round Green loss", str(m["worst_round_loss"]), "<= 3", m["worst_round_loss"] <= 3),
    ]
    rows.append(("L8 Market Collapse % (3P, 4P)", f"{m['mc_pct']:.1f}", ">= 8", m["mc_pct"] >= 8.0) if pl >= 3
                else ("L8 Market Collapse % (3P, 4P)", f"{m['mc_pct']:.1f}", "n/a at 2P", None))
    rows.append(("L9 Total Wipeout % (2P)", f"{m['tw_pct']:.1f}", "< 15", m["tw_pct"] < 15.0) if pl == 2
                else ("L9 Total Wipeout % (2P)", f"{m['tw_pct']:.1f}", "n/a above 2P", None))
    if b48 and b48["income_per_seat_round"]:
        x = m["income_per_seat_round"] / b48["income_per_seat_round"]
        rows.append(("L10 income per seat-round vs B48", f"x{x:.3f}", "<= x1.20", x <= 1.20))
    else:
        rows.append(("L10 income per seat-round vs B48", "no comparator", "<= x1.20", None))
    rows.append(("L11 invariants", f"{m['invariant_violations']} violations", "clean",
                 (m["invariant_violations"] == 0) if checked else None))
    return rows


def print_guardrails(rows, pl: int) -> bool:
    ok = True
    print(f"  guardrails {pl}P")
    for name, val, bar, passed in rows:
        required = name.startswith(("L10", "L11"))  # income comparator and invariants must actually be evaluated
        tag = "PASS" if passed else ("MISS" if (passed is None and required) else ("n/a" if passed is None else "FAIL"))
        ok &= passed is not False and not (passed is None and required)
        print(f"    {tag:<4} {name:<36} {val:<18} {bar}")
    return ok


def line(label: str, pl: int, m: Dict[str, Any]) -> str:
    return (f"{pl}P {label:<8} n={m['games']} rounds {m['rounds']:.2f} PZ+MC {m['pzmc_pct']:.1f} (MC {m['mc_pct']:.1f}) "
            f"SING {m['sing_pct']:.1f} TW {m['tw_pct']:.1f} elim {m['elim_pct']:.1f} green {m['green_lost_pg']:.2f} "
            f"b2b {m['b2b_pct']:.1f} inc {m['income_per_seat_round']:.2f} dead {m['dead_pct']:.2f}%")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default="v051_roster")
    ap.add_argument("--base", default="v050_roster")
    ap.add_argument("--income-base", default="v048_roster")
    ap.add_argument("--set", default="{}")
    ap.add_argument("--roster", default="mixed1")
    ap.add_argument("--players", default="2,3,4")
    ap.add_argument("--games", type=int, default=1200)
    ap.add_argument("--seed0", default="42,1242", help="first seed of each block; comma list for several blocks (pooled)")
    ap.add_argument("--procs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--assert-invariants", action="store_true")
    ap.add_argument("--quiet", action="store_true", default=True)
    ap.add_argument("--no-save", action="store_true")
    a = ap.parse_args()
    ov = json.loads(a.set)
    blocks = [int(x) for x in a.seed0.split(",")]
    payload: Dict[str, Any] = {"args": vars(a), "pods": {}}
    all_ok = True
    for pl in [int(x) for x in a.players.split(",")]:
        def runs(cfg: str, o: Dict[str, Any], check: bool) -> List[List[Dict[str, Any]]]:
            return [play_all(cfg, a.roster, pl, a.games, sd, o, a.procs, check) for sd in blocks]

        mb = runs(a.config, ov, a.assert_invariants)
        bb = runs(a.base, {}, False) if a.base else None
        b48r = runs(a.income_base, {}, False) if a.income_base else None
        pool = lambda rr: [x for blk in rr for x in blk]  # noqa: E731
        m = metrics(pool(mb))
        b0 = metrics(pool(bb)) if bb else None
        b48 = metrics(pool(b48r)) if b48r else None
        if len(blocks) > 1:
            for sd, blk in zip(blocks, mb):
                print(line(f"M s{sd}", pl, metrics(blk)))
        print(line("M pool", pl, m))
        if b0:
            print(line("B0", pl, b0))
        if b48:
            print(line("B48", pl, b48))
        rows = guardrails(m, b48, pl, a.assert_invariants)
        all_ok &= print_guardrails(rows, pl)
        extra = [f"unsafe-landing {m['land_unsafe_pct']:.1f}% of hits", f"capped cubes/game {m['capped_cubes_pg']:.2f}",
                 f"bands% {m['band_mix']}", f"Corruption +3 into 5+ /game {m['corr3_into_target_pg']:.3f}",
                 f"Pen L4 {m['pen_l4_pct']:.1f}%", f"SING {m['sing_pct']:.1f}%", f"dead {m['dead_pct']:.2f}%",
                 f"win% Helix {m['win_helix']} Aegis {m['win_aegis']} Spook {m['win_spook']}",
                 f"spread company {m['co_spread']:.1f} white hat {m['wh_spread']:.1f}"]
        if b0:
            extra.append(f"PZ+MC delta vs B0 {m['pzmc_pct'] - b0['pzmc_pct']:+.1f} pp (accepted residual D1)")
            extra.append(f"Green lost {m['green_lost_pg']:.2f} vs 2.5 cap (accepted residual D2, 2P)")
        print("  report only: " + "; ".join(extra))
        if m["first_violation"]:
            print(f"  first invariant violation: {m['first_violation']}")
        payload["pods"][str(pl)] = {"M": m, "B0": b0, "B48": b48,
                                    "blocks": {str(sd): metrics(blk) for sd, blk in zip(blocks, mb)},
                                    "guardrails": [list(r) for r in rows]}
    if not a.no_save:
        os.makedirs(OUT_DIR, exist_ok=True)
        path = os.path.join(OUT_DIR, f"{a.config}_s{'_'.join(str(b) for b in blocks)}.json")
        with open(path, "w") as fh:
            json.dump(payload, fh, default=str, indent=1)
        print(f"saved {os.path.relpath(path, ROOT)}")
    print("OVERALL", "PASS" if all_ok else "FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
