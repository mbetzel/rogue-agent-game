"""Pre-SDLC probe, part 2: Gray-aware bot and mitigation-side lever arms on B23 (docs/plans/gray_vulnerability_gd_plan.md §9).

No engine edits. Everything below is a monkeypatch installed inside each worker.
  Gray table: VARIANTS from scripts/probe_gray_vuln.py (default B23 = ⚠ on F2 and F3).
  Policies:
    S   = stock v0.49 roster (THINNING_AWARE, all seats)
    GA  = every seat uses the Gray-aware research focus (below)
    GA0 = seat 0 only uses the Gray-aware focus (paired-seed payoff of the policy)
  Gray-aware focus (sim-only): thin value V = 2 🔬 x P(⚠ face) x 0.56 rolls/round x rounds left (9 - round)
    + 1.0 if Vulnerability >= 3. While V >= 1.5 and the seat owns >= 2 Gray, push the cheapest remaining thinning
    track (Pen Test to its thinning level, Triage to its replacement level) right after Triage L1 / Release L3,
    and Release to L4 (set-Gray-face) once V >= 2.5.
  Levers (all on top of v0.49; NEW = needs a new rule, EXIST = existing [TUNE] knob / option):
    none
    a1_penL2   NEW   Pen Test L2 also returns 1 Gray die to the box (L3 still does)
    a2_penL3x2 NEW   Pen Test L3 returns 2 Gray dice
    b1_triL3   EXIST triage_l3_breakthrough=UPGRADE (L3: pay $3 to replace 1 Gray with a Market die; was +1 Secret)
    b2_triL3f  EXIST b1 with triage_l3_upgrade_cost=0
    c1_bw1    EXIST Release Bandwidth by level 5/5/6/6/7 (was 4/4/5/5/6)
    c2_relL1   EXIST Release Bandwidth by level 4/5/5/6/6 (L1 permanent +1, keeps the this-round +1)
    combos: any "x+y" of the above

  python3 scripts/probe_gray_vuln_mitigation.py --variants G1,B23 --policies S,GA,GA0 --levers none --players 2,3,4
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

from scripts.probe_gray_vuln import VARIANTS, gray_faces, summarize  # noqa: E402
from scripts.run_v380_secret_faces_sweep import build_engine  # noqa: E402

OUT_DIR = os.path.join(ROOT, "sim_results", "gray_vuln")
_BASE_CAP = {"DEFENSE": (2, 2, 3, 3, 4), "TRIAGE": (1, 1, 2, 2, 2)}
LEVERS = {
    "none": ({}, set()),
    "a1_penL2": ({}, {"pen_l2_thin"}),
    "a2_penL3x2": ({}, {"pen_l3_thin2"}),
    "b1_triL3": ({"triage_l3_breakthrough": "UPGRADE"}, set()),
    "b2_triL3f": ({"triage_l3_breakthrough": "UPGRADE", "triage_l3_upgrade_cost": 0}, set()),
    "c1_bw1": ({"track_capacity_by_level": dict(_BASE_CAP, RELEASE=(5, 5, 6, 6, 7))}, set()),
    "c2_relL1": ({"track_capacity_by_level": dict(_BASE_CAP, RELEASE=(4, 5, 5, 6, 6))}, set()),
}
GA_PARAMS = {"rolls_per_round": 0.56, "rp_per_vuln": 2.0, "near_vuln": 3, "near_bonus": 1.0, "v_thin": 1.5, "v_rel4": 2.5,
             "last_round": 9}
_S = {"policy": "S", "patches": set(), "state": None, "p_face": 1 / 6}


def lever(name):
    ov, pt = {}, set()
    for part in name.split("+") if name != "none" else []:
        o, p = LEVERS[part]
        if "track_capacity_by_level" in o and "track_capacity_by_level" in ov:  # combine two Release tables: take max
            a, b = ov["track_capacity_by_level"]["RELEASE"], o["track_capacity_by_level"]["RELEASE"]
            o = dict(o, track_capacity_by_level=dict(_BASE_CAP, RELEASE=tuple(max(x, y) for x, y in zip(a, b))))
        ov.update(o)
        pt |= p
    return ov, pt


def install():
    from sim.bots import research_policy as rp
    from sim.engine import research_tracks as rt
    if getattr(rp, "_gv2_probe", False):
        return
    rp._gv2_probe = True
    orig_want, orig_plan = rp._thinning_aware_want_order, rp._plan_research_share_regain
    orig_res, orig_has = rt.resolve_breakthrough, rt.has_level_effect

    def plan(policy, player, state, config, *a, **k):
        _S["state"] = state
        return orig_plan(policy, player, state, config, *a, **k)

    def ga_order(policy, player, config, lv):
        from sim.engine import sprint_plan
        base = orig_want(policy, player, config, lv)
        st = _S["state"]
        g = len(sprint_plan.owned_gray(player))
        rnd = int(getattr(st, "current_round", 1)) if st is not None else 1
        P = GA_PARAMS
        v = (P["rp_per_vuln"] * _S["p_face"] * P["rolls_per_round"] * max(1, P["last_round"] - rnd)
             + (P["near_bonus"] if player.vulnerability >= P["near_vuln"] else 0.0))
        player._ga_hot = getattr(player, "_ga_hot", 0) + (1 if v >= P["v_thin"] and g >= 2 else 0)
        if v < P["v_thin"] or g < 2:
            return base
        costs = config.track_step_costs
        pen_t = 2 if "pen_l2_thin" in _S["patches"] else 3
        tri_t = 3 if getattr(config, "triage_l3_breakthrough", "SECRET") == "UPGRADE" else 4
        opts = []
        for t, tgt in (("DEFENSE", pen_t), ("TRIAGE", tri_t)):
            if lv[t] < tgt:
                opts.append((sum(costs[lv[t]:tgt]), t, tgt))
        head = (["TRIAGE"] if lv["TRIAGE"] < 1 else []) + ["RELEASE"] * max(0, 3 - lv["RELEASE"])
        for _, t, tgt in sorted(opts):
            head += [t] * (tgt - lv[t])
        if v >= P["v_rel4"] and lv["RELEASE"] >= 3:
            head += ["RELEASE"]
        counts, out = {}, []
        for t in head + base:
            if counts.get(t, 0) < 4 - lv[t]:
                out.append(t)
                counts[t] = counts.get(t, 0) + 1
        return out

    def want(policy, player, config, lv):
        pol = _S["policy"]
        if pol == "GA" or (pol == "GA0" and player.player_id == 0):
            return ga_order(policy, player, config, lv)
        return orig_want(policy, player, config, lv)

    def has(cfg, track, level):
        if "pen_l2_thin" in _S["patches"] and rt.normalize_track(track) == "DEFENSE" and level == 2:
            return True
        return orig_has(cfg, track, level)

    def res(engine, player, track, level, choice=None):
        t = rt.normalize_track(track)
        if t == "DEFENSE" and level == 2 and "pen_l2_thin" in _S["patches"]:
            if not getattr(player, "_pen_l2_done", False):
                player._pen_l2_done = True
                rt._thin_gray(engine, player, "PEN_TEST_L2")
            return orig_res(engine, player, track, level, choice)
        rec = orig_res(engine, player, track, level, choice)
        if t == "DEFENSE" and level == 3 and "pen_l3_thin2" in _S["patches"] and rec is not None and rec.outcome == "TAKEN":
            rt._thin_gray(engine, player, "PEN_TEST_L3")
        return rec

    rp._thinning_aware_want_order, rp._plan_research_share_regain = want, plan
    rt.resolve_breakthrough, rt.has_level_effect = res, has


def play(task):
    import sim.entities as ent
    variant, policy, lev, players, seed = task
    install()
    spec = VARIANTS[variant]
    ent._v048_gray_faces = lambda: gray_faces(spec)
    ov, pt = lever(lev)
    _S.update(policy=policy, patches=pt, p_face=len(spec[0]) / 6, state=None)
    eng = build_engine("v049_roster", "mixed1", players, seed, dict(ov))
    eng.state.rush_seed = seed
    res = eng.run_game()
    s = eng.state
    nwin = max(1, len(res.winner_ids))
    by_pid = {r["player_id"]: r for r in res.rankings}
    t = Counter()
    owned = defaultdict(dict)
    vuln_r = defaultdict(lambda: [0, 0])
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
            "owned": owned.get(p.player_id, {}), "ga_hot": getattr(p, "_ga_hot", 0),
        })
    return {"seed": seed, "end": res.end_reason.value, "rounds": res.total_rounds, "wipeout": bool(res.is_total_wipeout),
            "t": dict(t), "vr": {k: v for k, v in vuln_r.items()}, "seats": seats}


def _ols(xs, ys):
    n = len(xs)
    if n < 3:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx if sxx else float("nan")


def extra(recs):
    seats = [x for r in recs for x in r["seats"]]
    m = lambda xs: sum(xs) / max(1, len(xs))  # noqa: E731
    by_wh, by_co = defaultdict(list), defaultdict(list)
    for x in seats:
        by_wh[str(x["wh"]).lower()].append(x["win"])
        by_co[str(x["company"]).lower()].append(x["win"])

    def reach(x, k):  # first round the seat owns <= k Gray dice (99 = never)
        for rn in sorted(int(a) for a in x["owned"]):
            if x["owned"].get(rn, x["owned"].get(str(rn))) <= k:
                return rn
        return 99
    m3 = [reach(x, 3) for x in seats]
    m2 = [reach(x, 2) for x in seats]
    g5 = [(x, x["owned"].get(5, x["owned"].get("5"))) for x in seats]
    g5 = [(x, g) for x, g in g5 if g is not None]
    lv = lambda key, L: [int(x[key][L]) for x in seats if L in x[key]]  # noqa: E731
    out = {
        "helix_win": 100 * m(by_co.get("helix", [])), "spook_win": 100 * m(by_wh.get("spook", [])),
        "prodigy_win": 100 * m(by_wh.get("prodigy", [])), "operator_win": 100 * m(by_wh.get("operator", [])),
        "win_by_wh": {k: round(100 * m(v), 1) for k, v in sorted(by_wh.items())},
        "m3_round": m([r for r in m3 if r < 99]), "m3_never": 100 * m([r == 99 for r in m3]),
        "m2_round": m([r for r in m2 if r < 99]), "m2_pct": 100 * m([r < 99 for r in m2]),
        "win_m3_early": 100 * m([x["win"] for x, r in zip(seats, m3) if r <= 4]),
        "win_m3_late": 100 * m([x["win"] for x, r in zip(seats, m3) if 4 < r < 99]),
        "win_m3_never": 100 * m([x["win"] for x, r in zip(seats, m3) if r == 99]),
        "n_m3": [sum(r <= 4 for r in m3), sum(4 < r < 99 for r in m3), sum(r == 99 for r in m3)],
        "slope_win_pp": -100 * _ols([g for _, g in g5], [x["win"] for x, _ in g5]),
        "slope_secrets": -_ols([g for _, g in g5], [x["secrets"] for x, _ in g5]),
        "pen2_pct": 100 * len(lv("pen", "2")) / len(seats), "pen2_round": m(lv("pen", "2")),
        "pen3_pct": 100 * len(lv("pen", "3")) / len(seats), "pen3_round": m(lv("pen", "3")),
        "tri3_pct": 100 * len(lv("tri", "3")) / len(seats), "tri3_round": m(lv("tri", "3")),
        "tri4_pct": 100 * len(lv("tri", "4")) / len(seats), "tri4_round": m(lv("tri", "4")),
        "rel4_pct": 100 * len(lv("rel", "4")) / len(seats), "rel4_round": m(lv("rel", "4")),
        "removed_per_seat": m([sum(x["thin"].values()) for x in seats]),
        "ga_hot_rounds": m([x["ga_hot"] for x in seats]),
        "seat0_removed": m([sum(x["thin"].values()) for x in seats if x["seat"] == 0]),
    }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", default="B23")
    ap.add_argument("--policies", default="GA")
    ap.add_argument("--levers", default="none")
    ap.add_argument("--players", default="2,3,4")
    ap.add_argument("--games", type=int, default=2000)
    ap.add_argument("--seed0", type=int, default=42)
    ap.add_argument("--procs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    a = ap.parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)
    from multiprocessing import Pool
    keys = ("rounds", "PZ", "MC", "SING", "TW", "green_lost", "inc", "dead_pct", "gray_vuln_pr", "win_secrets", "co_spread",
            "seat0_win", "seat0_secrets")
    xkeys = ("removed_per_seat", "m3_round", "m2_pct", "pen3_pct", "tri3_pct", "tri4_pct", "rel4_pct", "win_m3_early",
             "win_m3_late", "slope_win_pp", "slope_secrets", "helix_win", "spook_win", "ga_hot_rounds", "seat0_removed")
    with Pool(a.procs) as pool:
        for pl in [int(x) for x in a.players.split(",")]:
            for v in a.variants.split(","):
                for lev in a.levers.split(","):
                    for pol in a.policies.split(","):
                        tasks = [(v, pol, lev, pl, s) for s in range(a.seed0, a.seed0 + a.games)]
                        recs = pool.map(play, tasks, chunksize=max(1, len(tasks) // (a.procs * 8)))
                        sm = summarize(recs, pl)
                        sm.update(extra(recs))
                        tag = f"m_{v}_{pol}_{lev}_{pl}P_s{a.seed0}n{a.games}"
                        with open(os.path.join(OUT_DIR, tag + ".json"), "w") as fh:
                            json.dump(sm, fh, indent=1)
                        print(f"{pl}P {v} {pol} {lev} " + " ".join(f"{k}={sm[k]:.2f}" for k in keys + xkeys), flush=True)


if __name__ == "__main__":
    main()
