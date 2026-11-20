"""v0.50.0 Gray ⚠ B23 + Pen Test L2 thinning + Gray-aware bot sweep (docs/specs/gray_vuln_b23_spec.md §11).

Reads the native §8 telemetry (no monkeypatches). Mixed1 roster. One summary line per pod, JSON summaries in
``sim_results/gray_vuln_v050/``. Prints a PASS / FAIL guardrail table (each row computes its own pass state).

  --config   candidate preset (default v050_roster)         --set       JSON overrides on the candidate
  --base     comparator preset (default v049_roster)        --base-set  JSON overrides on the comparator
  --base-ga  also run the comparator with GRAY_AWARE (B0-GA); G1 is reported against both (stock B0 is the bar)
  --income-base  preset for the G4 income comparator (default v048_roster; "" skips it)
  --players 2,3,4  --games 1200  --seed0 42  --procs N  --assert-invariants  --quiet/--verbose  --no-save

Examples (smoke):  python3 scripts/run_gray_vuln_sweep.py --games 20 --players 3 --assert-invariants
Full run (not part of the implementation step): see spec §11.4.
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

OUT_DIR = os.path.join(ROOT, "sim_results", "gray_vuln_v050")
DEAD_BAR, DEAD_FLAG = 0.5, 0.4          # G5 (%), spec Q5
G1_BAR_PP, G2_MIN_MC, G3_MAX, G4_X = 3.0, 8.0, 2.5, 1.20


# --------------------------------------------------------------------------------------------------
# Overrides
# --------------------------------------------------------------------------------------------------
def coerce(ov: Dict[str, Any]) -> Dict[str, Any]:
    """JSON -> config types: tuples for seat / threshold lists, dataclass layering for ``bot_gray_aware_params``."""
    out = dict(ov)
    for k in ("bot_gray_aware_seats", "bot_thin_tracks", "vuln_band_thresholds", "vuln_min_target_by_version"):
        if isinstance(out.get(k), list):
            out[k] = tuple(out[k])
    return out


def resolve(config_name: str, ov: Dict[str, Any]) -> Dict[str, Any]:
    import dataclasses

    from sim.config import GameConfig

    out = coerce(ov)
    ga = out.get("bot_gray_aware_params")
    if isinstance(ga, dict):
        base = getattr(GameConfig, config_name)(num_players=3).bot_gray_aware_params
        out["bot_gray_aware_params"] = dataclasses.replace(base, **ga)
    return out


# --------------------------------------------------------------------------------------------------
# Invariants (G6)
# --------------------------------------------------------------------------------------------------
def install_invariants() -> None:
    """INV-GV-CONS-01: owned Gray + Gray removed is constant per player across every Sprint Review."""
    from sim.engine import sprint_plan as sp
    from scripts import run_locked_vuln_sweep as lv

    lv.install_lock_checks()
    if getattr(sp, "_gv_cons_installed", False):
        return
    sp._gv_cons_installed = True
    orig = sp.sprint_review

    def review(engine, p, chosen=None):
        out = orig(engine, p, chosen)
        total = len(sp.owned_gray(p)) + sum(p.gray_removed_by_source.values())
        base = getattr(p, "_gv_gray_total", None)
        if base is None:
            p._gv_gray_total = total
        else:
            assert total == base, f"INV-GV-CONS-01: Gray owned+removed drifted {base} -> {total}"
        return out

    sp.sprint_review = review


# --------------------------------------------------------------------------------------------------
# One game
# --------------------------------------------------------------------------------------------------
def play(task: Tuple[str, str, int, int, Dict[str, Any], bool]) -> Dict[str, Any]:
    config_name, roster, players, seed, overrides, check = task
    if check:
        install_invariants()
    eng = build_engine(config_name, roster, players, seed, resolve(config_name, overrides))
    res = eng.run_game()
    s, cfg = eng.state, eng.config
    nwin = max(1, len(res.winner_ids))
    by_pid = {r["player_id"]: r for r in res.rankings}
    inc = inc_n = dead = 0
    alive: Counter = Counter()
    for t in res.telemetry_history:
        for pid, x in t.income_by_player.items():
            tot = x["money"] + x["research"]
            inc += tot
            inc_n += 1
            dead += tot <= 1
        for row in t.phase_snapshots.get(4) or []:
            if not row.get("is_patient_zero"):
                alive[row["player_id"]] += 1
    seats = []
    for p in s.players:
        r = by_pid[p.player_id]
        lr = p.level_reached_round
        seats.append({
            "seat": p.player_id, "win": (1.0 / nwin) if p.player_id in res.winner_ids else 0.0, "secrets": r["secrets"],
            "company": r.get("company_code"), "wh": r.get("white_hat_code"), "pz": bool(p.is_patient_zero),
            "green_lost": p.green_secrets_lost, "alive_rounds": alive[p.player_id],
            "owned": {int(k): v for k, v in p.gray_owned_by_round.items()},
            "le3": p.gray_le3_round, "le2": p.gray_le2_round,
            "removed": dict(p.gray_removed_by_source), "thin_forfeits": p.thin_forfeits,
            "rolled": p.gray_rolled_total, "kept": p.gray_vuln_kept_total, "kept_by_face": dict(p.gray_vuln_kept_by_face),
            "rolls_by_round": {int(k): list(v) for k, v in p.gray_rolls_by_round.items()},
            "hot": len(p.gray_aware_hot_rounds),
            "lv": {t: {int(k): v for k, v in lr.get(t, {}).items()} for t in ("DEFENSE", "TRIAGE", "RELEASE")},
            "l4_sets": int(p.l4_payouts.get("release_gray_face_sets", 0)),
            "helix_sets": p.helix_bypass_face_sets, "helix_rerolled": p.helix_bypass_locked_rerolled,
        })
    return {"seed": seed, "end": res.end_reason.value, "rounds": res.total_rounds, "wipeout": bool(res.is_total_wipeout),
            "inc": inc, "inc_n": inc_n, "dead": dead, "seats": seats}


def play_all(config_name: str, roster: str, players: int, games: int, seed0: int, ov: Dict[str, Any], procs: int,
             check: bool) -> List[Dict[str, Any]]:
    tasks = [(config_name, roster, players, sd, ov, check) for sd in range(seed0, seed0 + games)]
    if procs <= 1:
        return [play(t) for t in tasks]
    from multiprocessing import Pool

    with Pool(procs) as pool:
        return pool.map(play, tasks, chunksize=max(1, len(tasks) // (procs * 8)))


# --------------------------------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------------------------------
def _m(xs: List[float]) -> float:
    return sum(xs) / max(1, len(xs))


def _pct(a: float, b: float) -> float:
    return 100.0 * a / b if b else 0.0


def metrics(recs: List[Dict[str, Any]], players: int) -> Dict[str, Any]:
    n = len(recs)
    ends = Counter(r["end"] for r in recs)
    seats = [x for r in recs for x in r["seats"]]
    by_wh, by_co = defaultdict(list), defaultdict(list)
    for x in seats:
        by_wh[str(x["wh"]).lower()].append(x["win"])
        by_co[str(x["company"]).lower()].append(x["win"])
    spread = lambda d: 100 * (max(_m(v) for v in d.values()) - min(_m(v) for v in d.values())) if d else 0.0  # noqa: E731
    le3 = [x["le3"] for x in seats]
    early = [x["win"] for x in seats if x["le3"] is not None and x["le3"] <= 4]
    late = [x["win"] for x in seats if x["le3"] is not None and x["le3"] > 4]
    src: Counter = Counter()
    for x in seats:
        src.update(x["removed"])
    held = {rn: _m([x["owned"][rn] for x in seats if rn in x["owned"]]) for rn in range(1, 9)}
    seat_rounds = sum(len(x["rolls_by_round"]) for x in seats)
    r2_kept = _m([x["rolls_by_round"].get(2, [0, 0])[1] for x in seats])
    reach = lambda tr, L: (_pct(sum(L in x["lv"][tr] for x in seats), len(seats)),  # noqa: E731
                           _m([x["lv"][tr][L] for x in seats if L in x["lv"][tr]]))
    rolled = sum(x["rolled"] for x in seats)
    out: Dict[str, Any] = {
        "games": n, "rounds": _m([r["rounds"] for r in recs]),
        "pz_pct": _pct(ends["patient_zero"], n), "mc_pct": _pct(ends["market_collapse"], n),
        "pz_mc_pct": _pct(ends["patient_zero"] + ends["market_collapse"], n),
        "sing_pct": _pct(ends["singularity"], n), "wipeout_pct": _pct(sum(r["wipeout"] for r in recs), n),
        "green_lost_pg": _m([x["green_lost"] for x in seats]),
        "income_per_seat_round": sum(r["inc"] for r in recs) / max(1, sum(r["inc_n"] for r in recs)),
        "dead_pct": _pct(sum(r["dead"] for r in recs), sum(r["inc_n"] for r in recs)),
        "helix_win": 100 * _m(by_co.get("helix", [])), "spook_win": 100 * _m(by_wh.get("spook", [])),
        "prodigy_win": 100 * _m(by_wh.get("prodigy", [])), "operator_win": 100 * _m(by_wh.get("operator", [])),
        "company_spread_pp": spread(by_co), "white_hat_spread_pp": spread(by_wh),
        "gray_held_by_round": {k: round(v, 2) for k, v in held.items()},
        "gray_removed_per_seat": _m([sum(x["removed"].values()) for x in seats]),
        "gray_removed_by_source": {k: round(v / max(1, len(seats)), 3) for k, v in sorted(src.items())},
        "le3_round": _m([v for v in le3 if v is not None]), "le3_never_pct": _pct(sum(v is None for v in le3), len(seats)),
        "le2_pct": _pct(sum(x["le2"] is not None for x in seats), len(seats)),
        "gray_kept_per_rolled": (sum(x["kept"] for x in seats) / rolled) if rolled else 0.0,
        "gray_kept_per_seat_round": sum(x["kept"] for x in seats) / max(1, seat_rounds), "r2_gray_kept_per_seat": r2_kept,
        "pen2": reach("DEFENSE", 2), "pen3": reach("DEFENSE", 3), "tri4": reach("TRIAGE", 4), "rel4": reach("RELEASE", 4),
        "hot_rounds_per_seat": _m([x["hot"] for x in seats]),
        "win_le3_early": 100 * _m(early), "win_le3_late": 100 * _m(late), "n_le3_early_late": [len(early), len(late)],
        "l4_face_sets_per_seat": _m([x["l4_sets"] for x in seats]),
        "helix_face_sets_per_seat": _m([x["helix_sets"] for x in seats]),
        "helix_locked_rerolled_per_seat": _m([x["helix_rerolled"] for x in seats]),
        "thin_forfeits_per_seat": _m([x["thin_forfeits"] for x in seats]),
    }
    return out


# --------------------------------------------------------------------------------------------------
# Guardrails: every row computes its own pass state
# --------------------------------------------------------------------------------------------------
def guardrails(m: Dict[str, Any], b0: Dict[str, Any], b0ga: Optional[Dict[str, Any]], b48: Optional[Dict[str, Any]],
               players: int, invariants_checked: bool) -> List[Tuple[str, str, str, Optional[bool]]]:
    rows: List[Tuple[str, str, str, Optional[bool]]] = []
    d1 = m["pz_mc_pct"] - b0["pz_mc_pct"]
    rows.append(("G1 PZ+MC vs stock B0", f"{m['pz_mc_pct']:.1f} vs {b0['pz_mc_pct']:.1f} ({d1:+.1f} pp)", f"<= +{G1_BAR_PP} pp", d1 <= G1_BAR_PP))
    if b0ga is not None:
        d = m["pz_mc_pct"] - b0ga["pz_mc_pct"]
        rows.append(("G1 PZ+MC vs Gray-aware B0-GA", f"{m['pz_mc_pct']:.1f} vs {b0ga['pz_mc_pct']:.1f} ({d:+.1f} pp)",
                     f"<= +{G1_BAR_PP} pp", d <= G1_BAR_PP))
    if players >= 3:
        rows.append(("G2 Market Collapse", f"{m['mc_pct']:.1f}%", ">= 8%", m["mc_pct"] >= G2_MIN_MC))
    else:
        rows.append(("G2 Market Collapse (2P: report)", f"{m['mc_pct']:.1f}%", "n/a", None))
    rows.append(("G3 Green Secrets lost / player-game", f"{m['green_lost_pg']:.2f}", f"<= {G3_MAX} (2P bar)",
                 (m["green_lost_pg"] <= G3_MAX) if players == 2 else None))
    if b48 is not None:
        x = m["income_per_seat_round"] / b48["income_per_seat_round"] if b48["income_per_seat_round"] else float("inf")
        rows.append(("G4 income vs v0.48", f"x{x:.3f}", f"<= x{G4_X}", x <= G4_X))
    else:
        rows.append(("G4 income vs v0.48", "no comparator", f"<= x{G4_X}", None))
    dd = m["dead_pct"]
    rows.append(("G5 dead turns", f"{dd:.2f}%" + (" (flag > 0.4%)" if DEAD_FLAG < dd <= DEAD_BAR else ""), f"<= {DEAD_BAR}%", dd <= DEAD_BAR))
    rows.append(("G6 invariants", "clean" if invariants_checked else "not checked", "clean", True if invariants_checked else None))
    return rows


def print_guardrails(rows: List[Tuple[str, str, str, Optional[bool]]], players: int) -> bool:
    ok = True
    print(f"  Guardrails {players}P")
    for name, val, bar, passed in rows:
        tag = "n/a " if passed is None else ("PASS" if passed else "FAIL")
        ok &= passed is not False
        print(f"    [{tag}] {name:<34} {val:<34} bar {bar}")
    return ok


def summary_line(label: str, players: int, m: Dict[str, Any]) -> str:
    return (f"{label:<8} {players}P n={m['games']} rnd {m['rounds']:.2f} PZ {m['pz_pct']:.1f} MC {m['mc_pct']:.1f} "
            f"SING {m['sing_pct']:.1f} TW {m['wipeout_pct']:.1f} green {m['green_lost_pg']:.2f} inc {m['income_per_seat_round']:.2f} "
            f"dead {m['dead_pct']:.2f}% removed {m['gray_removed_per_seat']:.2f} le3 {m['le3_round']:.2f} "
            f"helix {m['helix_win']:.1f} spook {m['spook_win']:.1f}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default="v050_roster")
    ap.add_argument("--base", default="v049_roster")
    ap.add_argument("--set", default="{}")
    ap.add_argument("--base-set", default="{}")
    ap.add_argument("--base-ga", action="store_true", help="also run the comparator with bot_research_mode=GRAY_AWARE (B0-GA)")
    ap.add_argument("--income-base", default="v048_roster")
    ap.add_argument("--roster", default="mixed1")
    ap.add_argument("--players", default="2,3,4")
    ap.add_argument("--games", type=int, default=1200)
    ap.add_argument("--seed0", type=int, default=42)
    ap.add_argument("--procs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--assert-invariants", action="store_true")
    ap.add_argument("--verbose", action="store_true", help="print the full metric dict per pod")
    ap.add_argument("--quiet", action="store_true", default=True)
    ap.add_argument("--name", default=None, help="output file stem (default: config + seed0)")
    ap.add_argument("--no-save", action="store_true")
    a = ap.parse_args()
    cand_ov, base_ov = json.loads(a.set), json.loads(a.base_set)
    tele = {"gray_vuln_telemetry": True}
    payload: Dict[str, Any] = {"args": vars(a), "pods": {}}
    all_ok = True
    for pl in [int(x) for x in a.players.split(",")]:
        def run(cfg: str, ov: Dict[str, Any], check: bool) -> Dict[str, Any]:
            return metrics(play_all(cfg, a.roster, pl, a.games, a.seed0, ov, a.procs, check), pl)

        mc = run(a.config, {**cand_ov}, a.assert_invariants)
        b0 = run(a.base, {**tele, **base_ov}, False)
        b0ga = run(a.base, {**tele, "bot_research_mode": "GRAY_AWARE", **base_ov}, False) if a.base_ga else None
        b48 = run(a.income_base, {}, False) if a.income_base else None
        print(summary_line("cand", pl, mc))
        print(summary_line("B0", pl, b0))
        if b0ga:
            print(summary_line("B0-GA", pl, b0ga))
        if b48:
            print(summary_line("B48", pl, b48))
        rows = guardrails(mc, b0, b0ga, b48, pl, a.assert_invariants)
        all_ok &= print_guardrails(rows, pl)
        if a.verbose:
            print(json.dumps(mc, indent=1, default=str))
        payload["pods"][str(pl)] = {"cand": mc, "B0": b0, "B0-GA": b0ga, "B48": b48,
                                    "guardrails": [list(r) for r in rows]}
    if not a.no_save:
        os.makedirs(OUT_DIR, exist_ok=True)
        path = os.path.join(OUT_DIR, f"{a.name or (a.config + '_s' + str(a.seed0))}.json")
        with open(path, "w") as fh:
            json.dump(payload, fh, default=str, indent=1)
        print(f"saved {os.path.relpath(path, ROOT)}")
    print("OVERALL", "PASS" if all_ok else "FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
