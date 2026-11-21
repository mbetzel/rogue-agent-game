"""Pre-SDLC probe: Green hit drops Vulnerability to the bottom of the next lower band instead of resetting to 0.

No engine edits. Arms (on v050_roster, Mixed1 roster):
  R0  = v0.50.0 as shipped (hit -> 0)
  DB  = drop one band: 5-7 -> 0, 8-10 -> 5, 11+ -> 8; bot Green model (``loss_if``) knows the new rule
  DBn = drop one band, bots still model hit -> 0 (shows how much bot adaptation matters)
  S2F1 = 5-7 -> 2, 8-10 -> 5, 11+ -> 8; repeat hit in the same Phase 4 costs 1 (bots model reset -> 0)
  SFA = S2F1 with the bot Green model aware; SFA9 / SFA0 = 2P levers on SFA (+1 starting Secret / 5-7 -> 0)

  python3 scripts/probe_green_drop_band.py --arms R0,DB,DBn --players 2,3,4 --games 2000
One summary line per pod; summaries saved to sim_results/green_drop_band/<arm>_<P>P.json.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.run_v380_secret_faces_sweep import build_engine  # noqa: E402

OUT_DIR = os.path.join(ROOT, "sim_results", "green_drop_band")
_STATE = {"arm": None, "orig": None}


def _band(cfg, v):
    return sum(1 for x in cfg.vuln_band_thresholds if v >= x)   # 0 = safe, 1 = 5-7, 2 = 8-10, 3 = 11+


def _by_band(lands):
    """Landing per hit band (5-7, 8-10, 11+)."""
    return lambda cfg, v: int(lands[max(1, _band(cfg, v)) - 1])


# arm -> landing(cfg, v_at_hit). Band thresholds on v0.50 are (5, 8, 11).
LANDS = {
    "DB": _by_band((0, 5, 8)),     # user proposal: bottom of next lower band
    "DBn": _by_band((0, 5, 8)),    # same, bots model reset -> 0
    "S2": _by_band((2, 5, 8)),     # 5-7 lands at 2
    "S3": _by_band((3, 5, 8)),     # 5-7 lands at 3
    "S4": _by_band((4, 5, 8)),     # 5-7 lands at 4 (top of safe zone)
    "M3": lambda cfg, v: max(0, v - 3),   # flat -3
    "HALF": lambda cfg, v: v // 2,         # halve, round down
    # S2 mitigations
    "S2H1": _by_band((2, 5, 8)),   # + at most one Green hit per player per round
    "S2PT": _by_band((2, 5, 8)),   # + first Pen Test step each turn costs 1 (not 2)
    "S2S1": _by_band((2, 5, 8)),   # + 1 starting Secret
    "S2HP": _by_band((2, 5, 8)),   # + H1 and PT together
    "S2F1": _by_band((2, 5, 8)),   # + repeat hits in the same round cost a flat 1 Secret (still drop a band)
    # S2F1 with the bot Green model (``loss_if``) aware of the landing + flat repeat (S2F1 itself keeps reset -> 0)
    "SFA": _by_band((2, 5, 8)),
    "SFA9": _by_band((2, 5, 8)),   # 2P lever: + 1 starting Secret at 2P only (run at 2P)
    "SFA0": _by_band((0, 5, 8)),   # 2P lever: 5-7 lands at 0 (today) at 2P; 8-10 -> 5, 11+ -> 8 (run at 2P)
    "SFA1": _by_band((1, 5, 8)),   # softer lever: 5-7 lands at 1
}
FLAT_REPEAT = {"S2F1", "SFA", "SFA9", "SFA0", "SFA1"}
AWARE = {"DB", "SFA", "SFA9", "SFA0", "SFA1"}
ARM_OV = {
    "S2PT": {"pen_test_first_step_cost": 1},
    "S2HP": {"pen_test_first_step_cost": 1},
    "S2S1": {"starting_secrets_by_player_count": {2: 9, 3: 9, 4: 13}},
    "R2": {"vuln_hit_reset": 2},     # flat reset to 2 (native knob, reference)
    "SFA9": {"starting_secrets_by_player_count": {2: 9, 3: 8, 4: 12}},
}
HIT_CAP = {"S2H1", "S2HP", "S2HX"}
LANDS["S2HX"] = _by_band((2, 5, 8))   # one-hit cap + each cube beyond the player count costs every player 1 Secret
OVERFLOW = {"S2HX"}


def landing(cfg, v):
    return LANDS[_STATE["arm"]](cfg, v)


def install(arm):
    from sim.engine import vulnerability as vuln
    from sim.bots import vulnerability_policy as vp
    if _STATE["orig"] is None:
        _STATE["orig"] = (vuln.resolve_green, vp.loss_if)
    orig_green, orig_loss = _STATE["orig"]
    _STATE["arm"] = arm
    if arm in ("R0", "R2"):
        vuln.resolve_green, vp.loss_if = orig_green, orig_loss
        return
    cap = arm in HIT_CAP
    flat = arm in FLAT_REPEAT
    overflow = arm in OVERFLOW

    def resolve_green(engine, cr, attack):
        from sim.config import CubeColor
        cfg, s = engine.config, engine.state
        if not cfg.is_vulnerability or cr.buffer_overflow or s.green_resolved_round == s.current_round:
            return []
        s.green_resolved_round = s.current_round
        n = int(attack.get(CubeColor.GREEN, 0))
        floor = vuln.min_target(cfg, s)
        seat = lambda p: (s.players.index(p) - s.first_player_index) % len(s.players)  # noqa: E731
        events, lost_by_player, hit_once = [], {}, set()
        for k in range(n):
            elig = [p for p in s.players if vuln.eligible_for_green(s, cr, p) and p.vulnerability >= floor
                    and not (cap and p.player_id in hit_once)]
            if not elig:
                events.append({"round": s.current_round, "cube": k, "pids": [], "v": None, "damage": 0, "cancelled": []})
                continue
            top = max(p.vulnerability for p in elig)
            hit = sorted([p for p in elig if p.vulnerability == top], key=seat)
            band_dmg = vuln.band_damage(cfg, top)
            land = landing(cfg, top)
            cancelled, pdmg = [], {}
            for p in hit:
                dmg = 1 if (flat and p.player_id in hit_once) else band_dmg
                pdmg[p.player_id] = dmg
                if vuln._aegis_green_cancel(engine, p, dmg):
                    cancelled.append(p.player_id)
                    p.green_hits_cancelled += 1
                    p.green_secrets_cancelled += dmg
                else:
                    p.lose_secrets(dmg, "green_vulnerability")
                    p.green_secrets_lost += dmg
                    lost_by_player[p.player_id] = lost_by_player.get(p.player_id, 0) + dmg
                p.green_hits += 1
                p.green_hits_by_damage[dmg] = p.green_hits_by_damage.get(dmg, 0) + 1
                p.vuln_reset_by_hit_total += p.vulnerability - land
                p.vulnerability = land
                hit_once.add(p.player_id)
            events.append({"round": s.current_round, "cube": k, "pids": [p.player_id for p in hit],
                           "v": top, "damage": band_dmg, "pdmg": pdmg, "cancelled": cancelled, "land": land})
        alive = [p for p in s.players if vuln.eligible_for_green(s, cr, p)]
        extra = max(0, n - len(alive))
        ovf = {}
        if overflow and extra:
            for p in alive:
                p.lose_secrets(extra, "green_overflow")
                ovf[p.player_id] = extra
        if not hasattr(s, "_gp_rounds"):
            s._gp_rounds = []
        s._gp_rounds.append({"round": s.current_round, "n": n, "alive": len(alive), "extra": extra, "ovf": ovf})
        s.green_hit_events.extend(events)
        s.green_round_stats = {"round": s.current_round, "resolved": n,
                               "no_target": sum(1 for e in events if not e["pids"]),
                               "lost_by_player": lost_by_player, "events": events}
        return events

    def loss_if(v_self, rivals_v, k, cfg, floor):
        vals = [float(v_self)] + [float(v) for v in rivals_v]
        loss, done = 0, set()
        for _ in range(k):
            elig = [i for i, v in enumerate(vals) if v >= floor and not (cap and i in done)]
            if not elig:
                break
            top = max(vals[i] for i in elig)
            dmg = vuln.band_damage(cfg, top)
            for i in elig:
                if vals[i] == top:
                    if i == 0:
                        loss += 1 if (flat and i in done) else dmg
                    vals[i] = float(landing(cfg, int(top)))
                    done.add(i)
        return loss

    vuln.resolve_green = resolve_green
    vp.loss_if = loss_if if arm in AWARE else orig_loss


def play(task):
    arm, players, seed = task
    install(arm)
    eng = build_engine("v050_roster", "mixed1", players, seed, dict(ARM_OV.get(arm, {})))
    res = eng.run_game()
    s = eng.state
    nwin = max(1, len(res.winner_ids))
    by_pid = {r["player_id"]: r for r in res.rankings}
    # per-round Green telemetry from events
    per_round = defaultdict(lambda: defaultdict(int))   # round -> pid -> secrets lost
    hits_rr = defaultdict(lambda: defaultdict(int))     # round -> pid -> hits
    g = Counter()
    for e in s.green_hit_events:
        g["cubes"] += 1
        if not e["pids"]:
            g["fizzle"] += 1
            continue
        g[f"v_band_{e['damage']}"] += 1
        g["land_unsafe"] += 1 if e.get("land", 0) >= vuln_floor(eng) else 0
        for pid in e["pids"]:
            if pid not in e["cancelled"]:
                per_round[e["round"]][pid] += e.get("pdmg", {}).get(pid, e["damage"])
            hits_rr[e["round"]][pid] += 1
    gp = getattr(s, "_gp_rounds", [])
    ovf_lost = Counter()
    for r in gp:
        for pid, x in r["ovf"].items():
            per_round[r["round"]][pid] += x
            ovf_lost[pid] += x
    gpr = {"green_rounds": sum(1 for r in gp if r["n"] > 0), "ovf_rounds": sum(1 for r in gp if r["extra"] > 0),
           "extra": sum(r["extra"] for r in gp)}
    round_losses = [x for r in per_round.values() for x in r.values()]
    multi = sum(1 for r in hits_rr.values() for x in r.values() if x >= 2)
    hit_seat_rounds = sum(1 for r in hits_rr.values() for x in r.values() if x >= 1)
    # back-to-back: hit in round r and r+1
    b2b = sum(1 for rn, r in hits_rr.items() for pid in r if pid in hits_rr.get(rn + 1, {}))
    lock = [rec["lockin"] for p in s.players for rec in p.vuln_by_round if rec.get("lockin") is not None]
    seats = []
    for p in s.players:
        r = by_pid[p.player_id]
        seats.append({
            "win": (1.0 / nwin) if p.player_id in res.winner_ids else 0.0, "secrets": r["secrets"],
            "green_lost": p.green_secrets_lost, "green_hits": p.green_hits, "pz": bool(p.is_patient_zero),
            "company": str(r.get("company_code")).lower(), "wh": str(r.get("white_hat_code")).lower(),
            "pen_level": int(p.defense_level), "pen_steps": sum(v for k, v in p.vuln_lowered_by_source.items() if k.startswith("pen")),
            "peak": p.vuln_peak, "elim_round": p.elimination_round if p.is_patient_zero else None,
            "green_pz": bool(p.is_patient_zero and p.green_secrets_lost > 0), "ovf_lost": ovf_lost.get(p.player_id, 0),
        })
    return {"end": res.end_reason.value, "rounds": res.total_rounds, "wipeout": bool(res.is_total_wipeout),
            "g": dict(g), "round_losses": round_losses, "multi": multi, "hit_sr": hit_seat_rounds, "b2b": b2b,
            "lock": lock, "seats": seats, "gpr": gpr}


def vuln_floor(eng):
    from sim.engine import vulnerability as vuln
    return vuln.min_target(eng.config, eng.state)


def summarize(recs):
    n = len(recs)
    m = lambda xs: sum(xs) / max(1, len(xs))  # noqa: E731
    ends = Counter(r["end"] for r in recs)
    seats = [x for r in recs for x in r["seats"]]
    g = Counter()
    for r in recs:
        g.update(r["g"])
    rl = [x for r in recs for x in r["round_losses"]]
    lock = [x for r in recs for x in r["lock"]]
    by_co, by_wh = defaultdict(list), defaultdict(list)
    for x in seats:
        by_co[x["company"]].append(x["win"])
        by_wh[x["wh"]].append(x["win"])
    spread = lambda d: 100 * (max(m(v) for v in d.values()) - min(m(v) for v in d.values()))  # noqa: E731
    winners = [x for x in seats if x["win"] > 0]
    hit_cubes = max(1, g["cubes"] - g["fizzle"])
    lock_hist = Counter(min(v, 14) for v in lock)
    pen_lv = Counter(x["pen_level"] for x in seats)
    return {
        "games": n, "rounds": m([r["rounds"] for r in recs]),
        "PZ": 100 * ends["patient_zero"] / n, "MC": 100 * ends["market_collapse"] / n,
        "SING": 100 * ends["singularity"] / n, "TW": 100 * m([r["wipeout"] for r in recs]),
        "elim_pct": 100 * m([x["pz"] for x in seats]),
        "elim_round": m([x["elim_round"] for x in seats if x["elim_round"]]),
        "green_cubes_pg": g["cubes"] / n, "fizzle_pct": 100 * g["fizzle"] / max(1, g["cubes"]),
        "hits_pg": m([x["green_hits"] for x in seats]) , "green_lost": m([x["green_lost"] for x in seats]),
        "band_mix": {k: round(100 * g[f"v_band_{k}"] / hit_cubes, 1) for k in (1, 2, 3)},
        "land_unsafe_pct": 100 * g["land_unsafe"] / hit_cubes,
        "loss_per_hit_round": m(rl), "loss_round_p95": sorted(rl)[int(0.95 * len(rl))] if rl else 0,
        "loss_round_ge5_pct": 100 * m([x >= 5 for x in rl]), "loss_round_max": max(rl) if rl else 0,
        "multi_hit_pct": 100 * sum(r["multi"] for r in recs) / max(1, sum(r["hit_sr"] for r in recs)),
        "b2b_pct": 100 * sum(r["b2b"] for r in recs) / max(1, sum(r["hit_sr"] for r in recs)),
        "lock_mean": m(lock), "lock_ge5_pct": 100 * m([v >= 5 for v in lock]), "lock_ge8_pct": 100 * m([v >= 8 for v in lock]),
        "lock_ge11_pct": 100 * m([v >= 11 for v in lock]),
        "lock_hist": {k: round(100 * lock_hist[k] / max(1, len(lock)), 1) for k in sorted(lock_hist)},
        "pen_steps": m([x["pen_steps"] for x in seats]), "pen_lv": {k: round(100 * v / len(seats), 1) for k, v in sorted(pen_lv.items())},
        "peak": m([x["peak"] for x in seats]),
        "win_secrets": m([x["secrets"] for x in winners]), "secrets": m([x["secrets"] for x in seats]),
        "co_spread": spread(by_co), "wh_spread": spread(by_wh),
        "win_by_co": {k: round(100 * m(v), 1) for k, v in sorted(by_co.items())},
        "win_by_wh": {k: round(100 * m(v), 1) for k, v in sorted(by_wh.items())},
        "ovf_round_pct": 100 * sum(r.get("gpr", {}).get("ovf_rounds", 0) for r in recs)
        / max(1, sum(r.get("gpr", {}).get("green_rounds", 0) for r in recs)),
        "ovf_game_pct": 100 * m([r.get("gpr", {}).get("ovf_rounds", 0) > 0 for r in recs]),
        "extra_pg": m([r.get("gpr", {}).get("extra", 0) for r in recs]),
        "ovf_lost": m([x.get("ovf_lost", 0) for x in seats]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", default="R0,DB,DBn")
    ap.add_argument("--players", default="2,3,4")
    ap.add_argument("--games", type=int, default=2000)
    ap.add_argument("--seed0", type=int, default=42)
    ap.add_argument("--procs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--report", action="store_true", help="print the detail table from saved summaries and exit")
    a = ap.parse_args()
    if a.report:
        for pl in [int(x) for x in a.players.split(",")]:
            for arm in a.arms.split(","):
                fp = os.path.join(OUT_DIR, f"{arm}_{pl}P.json")
                if not os.path.exists(fp):
                    continue
                with open(fp) as fh:
                    d = json.load(fh)
                print(f"{pl}P {arm:4s} rounds={d['rounds']:.2f} PZ={d['PZ']:.1f} MC={d['MC']:.1f} SING={d['SING']:.1f} "
                      f"TW={d['TW']:.1f} elim={d['elim_pct']:.1f} hits={d['hits_pg']:.2f} green_lost={d['green_lost']:.2f} "
                      f"multi={d['multi_hit_pct']:.1f} b2b={d['b2b_pct']:.1f} ge5={d['loss_round_ge5_pct']:.2f} "
                      f"pen={d['pen_steps']:.2f} win_sec={d['win_secrets']:.2f} co_spr={d['co_spread']:.1f} wh_spr={d['wh_spread']:.1f}")
                print(f"        bands%={d['band_mix']} land_unsafe%={d['land_unsafe_pct']:.1f} "
                      f"cubes/g={d['green_cubes_pg']:.2f} round_loss p95={d['loss_round_p95']} max={d['loss_round_max']} "
                      f"peak={d['peak']:.2f} elim_round={d['elim_round']:.2f} pen_lv%={d['pen_lv']}")
                print(f"        lock%={d['lock_hist']}")
                print(f"        win_by_co={d['win_by_co']} win_by_wh={d['win_by_wh']}")
        return
    os.makedirs(OUT_DIR, exist_ok=True)
    from multiprocessing import Pool
    keys = ("rounds", "PZ", "MC", "SING", "elim_pct", "fizzle_pct", "hits_pg", "green_lost", "loss_per_hit_round",
            "loss_round_ge5_pct", "multi_hit_pct", "b2b_pct", "lock_mean", "lock_ge5_pct", "lock_ge8_pct", "pen_steps",
            "win_secrets", "co_spread", "wh_spread")
    with Pool(a.procs) as pool:
        for pl in [int(x) for x in a.players.split(",")]:
            for arm in a.arms.split(","):
                tasks = [(arm, pl, s) for s in range(a.seed0, a.seed0 + a.games)]
                recs = pool.map(play, tasks, chunksize=max(1, len(tasks) // (a.procs * 8)))
                sm = summarize(recs)
                with open(os.path.join(OUT_DIR, f"{arm}_{pl}P.json"), "w") as fh:
                    json.dump(sm, fh, indent=1)
                print(f"{pl}P {arm:4s} " + " ".join(f"{k}={sm[k]:.2f}" for k in keys), flush=True)
                print(f"        overflow: rounds_with_green%={sm['ovf_round_pct']:.2f} games%={sm['ovf_game_pct']:.2f} "
                      f"extra_cubes/game={sm['extra_pg']:.3f} overflow_secrets_lost/seat={sm['ovf_lost']:.3f} "
                      f"worst_round={sm['loss_round_max']}", flush=True)


if __name__ == "__main__":
    main()
