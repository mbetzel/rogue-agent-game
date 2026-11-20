"""Pre-SDLC probe: Gray Legacy ⚠ count (docs/plans/gray_vulnerability_gd_plan.md). No engine edits.

Gray face tables are swapped by monkeypatching ``sim.entities._v048_gray_faces`` inside each worker.
Seat-0 research policy is forced per arm by monkeypatching ``research_policy._thinning_aware_want_order``:
  S = roster as shipped (THINNING_AWARE for all seats)
  R = seat 0 rushes Release L3 then Pen Test L3 (``bot_research_rush="p0"``)
  T = seat 0 thinning-aware on Release AND Pen Test (pushes Pen Test L3 too)
  L = seat 0 uses the LEGACY archetype want-list (no thinning focus); other seats unchanged

  python3 scripts/probe_gray_vuln.py --variants G1,A13,D123 --policies S,R,L --players 2,3,4 --games 2000
Quiet: one summary line per pod; per-pod summaries saved to sim_results/gray_vuln/<variant>_<policy>_<P>P.json.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.run_v380_secret_faces_sweep import build_engine  # noqa: E402

OUT_DIR = os.path.join(ROOT, "sim_results", "gray_vuln")

# variant -> (⚠ face numbers 1..6, payout overrides {face#: (money, patches)} for plain faces)
VARIANTS = {
    "G1": ((3,), {}),            # v0.49 baseline
    "A13": ((1, 3), {}),         # 2⚠ strong: F1 +$1&+1🔬
    "B23": ((2, 3), {}),         # 2⚠ strong: F2 +2🔬
    "C35": ((3, 5), {}),         # 2⚠ weak:   F5 +$1 (pure liability)
    "C36": ((3, 6), {}),         # 2⚠ weak:   F6 +1🔬
    "D123": ((1, 2, 3), {}),     # 3⚠ strong = v0.46 table
    "E356": ((3, 5, 6), {}),     # 3⚠ weak:   F5, F6
    "E345": ((3, 4, 5), {}),     # 3⚠ weak incl. choice F4
}


def gray_faces(spec):
    from sim.entities import Face
    vset, pay = spec
    base = [
        Face(name="+$1 & +1 🔬", money=1, patches=1),
        Face(name="+2 🔬", patches=2),
        Face(name="+$2 / +2 🔬", is_choice=True, choices=(Face("+$2", money=2), Face("+2 🔬", patches=2))),
        Face(name="+$1 / +1 🔬", is_choice=True, choices=(Face("+$1", money=1), Face("+1 🔬", patches=1))),
        Face(name="+$1", money=1),
        Face(name="+1 🔬", patches=1),
    ]
    out = []
    for i, f in enumerate(base, 1):
        if i in pay:
            m, r = pay[i]
            f = Face(name=f"+${m} & +{r} 🔬", money=m, patches=r)
        if i in vset:
            f = dataclasses.replace(f, name=f.name + " ⚠", vuln=1)
        out.append(f)
    return out


_STATE = {"variant": None, "p0": None}


def install(variant, p0):
    import sim.entities as ent
    from sim.bots import research_policy as rp
    if not getattr(rp, "_gv_probe", False):
        rp._gv_probe = True
        orig = rp._thinning_aware_want_order

        def want(policy, player, config, lv):
            if _STATE["p0"] == "L" and player.player_id == 0:
                return rp._want_list(policy, lv)
            if _STATE["p0"] == "T" and player.player_id == 0:  # seat 0 thins on Release AND Pen Test (S2b-style)
                return orig(policy, player, dataclasses.replace(config, bot_thin_tracks=("RELEASE", "DEFENSE")), lv)
            return orig(policy, player, config, lv)
        rp._thinning_aware_want_order = want
    spec = VARIANTS[variant]
    ent._v048_gray_faces = lambda: gray_faces(spec)
    _STATE.update(variant=variant, p0=p0)


def play(task):
    variant, policy, players, seed = task
    install(variant, policy)
    ov = {"bot_research_rush": "p0"} if policy == "R" else {}
    eng = build_engine("v049_roster", "mixed1", players, seed, ov)
    eng.state.rush_seed = seed
    res = eng.run_game()
    s = eng.state
    nwin = max(1, len(res.winner_ids))
    by_pid = {r["player_id"]: r for r in res.rankings}
    t = Counter()
    owned = defaultdict(dict)   # pid -> round -> gray owned
    vuln_r = defaultdict(lambda: [0, 0])  # round -> [gray ⚠, colored ⚠] summed over seats
    for tel in res.telemetry_history:
        rn = tel.round_number
        for pid, inc in tel.income_by_player.items():
            t["inc"] += inc["money"] + inc["research"]
            t["inc_n"] += 1
            t["dead"] += (inc["money"] + inc["research"]) <= 1
        for pid, n in tel.gray_owned_by_player.items():
            owned[pid][rn] = n
        t["gray_rolled"] += sum(tel.gray_rolled_by_player.values())
        t["col_rolled"] += sum(tel.colored_rolled_by_player.values())
        gv, cv = sum(tel.gray_vuln_kept_by_player.values()), sum(tel.colored_vuln_kept_by_player.values())
        t["gray_vuln"] += gv
        t["col_vuln"] += cv
        t["seat_rounds"] += len(tel.gray_rolled_by_player)
        vuln_r[rn][0] += gv
        vuln_r[rn][1] += cv
    seats = []
    for p in s.players:
        r = by_pid[p.player_id]
        lr = p.level_reached_round
        seats.append({
            "seat": p.player_id, "win": (1.0 / nwin) if p.player_id in res.winner_ids else 0.0,
            "secrets": r["secrets"], "green_lost": p.green_secrets_lost, "green_hits": p.green_hits,
            "resets": p.vuln_reset_by_hit_total, "pz": bool(p.is_patient_zero), "company": r.get("company_code"),
            "wh": r.get("white_hat_code"), "thin": dict(p.gray_removed_by_source), "thin_rounds": list(p.thin_rounds),
            "rel": {str(k): v for k, v in lr.get("RELEASE", {}).items()}, "pen": {str(k): v for k, v in lr.get("DEFENSE", {}).items()},
            "tri": {str(k): v for k, v in lr.get("TRIAGE", {}).items()},
            "owned": owned.get(p.player_id, {}), "vg": dict(p.vuln_gained_by_source),
        })
    return {"seed": seed, "end": res.end_reason.value, "rounds": res.total_rounds, "wipeout": bool(res.is_total_wipeout),
            "t": dict(t), "vr": {k: v for k, v in vuln_r.items()}, "seats": seats}


def summarize(recs, players):
    n = len(recs)
    ends = Counter(r["end"] for r in recs)
    seats = [x for r in recs for x in r["seats"]]
    t = Counter()
    for r in recs:
        t.update(r["t"])
    m = lambda xs: sum(xs) / max(1, len(xs))  # noqa: E731
    by_co, by_wh = defaultdict(list), defaultdict(list)
    for x in seats:
        by_co[str(x["company"]).lower()].append(x["win"])
        by_wh[str(x["wh"]).lower()].append(x["win"])
    spread = lambda d: 100 * (max(m(v) for v in d.values()) - min(m(v) for v in d.values()))  # noqa: E731
    # Gray owned by round (alive seat-rounds)
    own = defaultdict(list)
    for x in seats:
        for rn, v in x["owned"].items():
            own[int(rn)].append(v)
    first = [x["thin_rounds"][0] if x["thin_rounds"] else 99 for x in seats]
    thin_n = [len(x["thin_rounds"]) for x in seats]
    src = Counter()
    for x in seats:
        src.update(x["thin"])
    winners = [x for x in seats if x["win"] > 0]
    # early vs late/never thinners (correlational)
    early = [x["win"] for x, f in zip(seats, first) if f <= 3]
    late = [x["win"] for x, f in zip(seats, first) if 3 < f < 99]
    never = [x["win"] for x, f in zip(seats, first) if f == 99]
    rel1 = [int(x["rel"]["1"]) for x in seats if "1" in x["rel"]]
    rel2 = [int(x["rel"]["2"]) for x in seats if "2" in x["rel"]]
    rel3 = [int(x["rel"]["3"]) for x in seats if "3" in x["rel"]]
    pen3 = [int(x["pen"]["3"]) for x in seats if "3" in x["pen"]]
    tri4 = [int(x["tri"]["4"]) for x in seats if "4" in x["tri"]]
    s0 = [x for x in seats if x["seat"] == 0]
    gray5 = defaultdict(list)  # Gray owned entering round 5 -> win
    for x in seats:
        g = x["owned"].get(5, x["owned"].get("5"))
        if g is not None:
            gray5[min(int(g), 5)].append(x["win"])
    return {
        "games": n, "rounds": m([r["rounds"] for r in recs]),
        "PZ": 100 * ends["patient_zero"] / n, "MC": 100 * ends["market_collapse"] / n, "SING": 100 * ends["singularity"] / n,
        "TW": 100 * m([r["wipeout"] for r in recs]),
        "green_lost": m([x["green_lost"] for x in seats]), "resets": m([x["resets"] for x in seats]), "hits": m([x["green_hits"] for x in seats]),
        "inc": t["inc"] / max(1, t["inc_n"]), "dead_pct": 100 * t["dead"] / max(1, t["inc_n"]),
        "gray_rolled_pr": t["gray_rolled"] / max(1, t["seat_rounds"]), "col_rolled_pr": t["col_rolled"] / max(1, t["seat_rounds"]),
        "gray_vuln_per_die": t["gray_vuln"] / max(1, t["gray_rolled"]), "col_vuln_per_die": t["col_vuln"] / max(1, t["col_rolled"]),
        "gray_vuln_pr": t["gray_vuln"] / max(1, t["seat_rounds"]), "col_vuln_pr": t["col_vuln"] / max(1, t["seat_rounds"]),
        "win_secrets": m([x["secrets"] for x in winners]), "secrets": m([x["secrets"] for x in seats]),
        "co_spread": spread(by_co), "wh_spread": spread(by_wh),
        "win_by_co": {k: round(100 * m(v), 1) for k, v in sorted(by_co.items())},
        "owned_by_round": {rn: round(m(v), 2) for rn, v in sorted(own.items()) if rn <= 10},
        "first_thin_mean": m([f for f in first if f < 99]), "never_thin_pct": 100 * m([f == 99 for f in first]),
        "thins_per_seat": m(thin_n), "thin_src": {k: round(v / len(seats), 3) for k, v in sorted(src.items())},
        "win_early_thin": 100 * m(early), "win_late_thin": 100 * m(late), "win_never_thin": 100 * m(never),
        "n_early": len(early), "n_late": len(late), "n_never": len(never),
        "rel1_round": m(rel1), "rel2_round": m(rel2), "rel3_round": m(rel3), "pen3_round": m(pen3), "tri4_round": m(tri4),
        "rel2_pct": 100 * len(rel2) / len(seats), "rel3_pct": 100 * len(rel3) / len(seats), "pen3_pct": 100 * len(pen3) / len(seats),
        "tri4_pct": 100 * len(tri4) / len(seats),
        "win_by_gray_r5": {k: (round(100 * m(v), 1), len(v)) for k, v in sorted(gray5.items())},
        "seat0_win": 100 * m([x["win"] for x in s0]), "seat0_secrets": m([x["secrets"] for x in s0]),
        "seat0_green_lost": m([x["green_lost"] for x in s0]), "seat0_thins": m([len(x["thin_rounds"]) for x in s0]),
        "seat0_rel2_pct": 100 * m([("2" in x["rel"]) for x in s0]), "seat0_pen3_pct": 100 * m([("3" in x["pen"]) for x in s0]),
        "vuln_by_round": {rn: [round(a / max(1, n), 2), round(b / max(1, n), 2)] for rn, (a, b) in sorted(
            ((int(k), v) for k, v in _sum_vr(recs).items())) if rn <= 10},
    }


def _sum_vr(recs):
    acc = defaultdict(lambda: [0, 0])
    for r in recs:
        for k, (a, b) in r["vr"].items():
            acc[k][0] += a
            acc[k][1] += b
    return acc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", default="G1")
    ap.add_argument("--policies", default="S")
    ap.add_argument("--players", default="2,3,4")
    ap.add_argument("--games", type=int, default=2000)
    ap.add_argument("--seed0", type=int, default=42)
    ap.add_argument("--procs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    a = ap.parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)
    from multiprocessing import Pool
    keys = ("rounds", "PZ", "MC", "SING", "green_lost", "hits", "inc", "gray_vuln_per_die", "gray_vuln_pr", "col_vuln_pr",
            "win_secrets", "co_spread", "first_thin_mean", "thins_per_seat", "seat0_win", "seat0_thins", "seat0_green_lost", "seat0_secrets", "win_early_thin", "win_never_thin")
    with Pool(a.procs) as pool:
        for pl in [int(x) for x in a.players.split(",")]:
            for v in a.variants.split(","):
                for pol in a.policies.split(","):
                    tasks = [(v, pol, pl, s) for s in range(a.seed0, a.seed0 + a.games)]
                    recs = pool.map(play, tasks, chunksize=max(1, len(tasks) // (a.procs * 8)))
                    sm = summarize(recs, pl)
                    with open(os.path.join(OUT_DIR, f"{v}_{pol}_{pl}P.json"), "w") as fh:
                        json.dump(sm, fh, indent=1)
                    print(f"{pl}P {v:5s} {pol} " + " ".join(f"{k}={sm[k]:.2f}" for k in keys), flush=True)


if __name__ == "__main__":
    main()
