"""v0.48.0 Sprint Plan & Gray Legacy Rotation sweeps (docs/specs/sprint_plan_spec.md §16.2, §17).

  --arm S0|S1|S2|S2b|S3|R0|R1|R2|R3|V45     one arm (V45 = v045_roster, the income reference for ``--ref45``)
  --players 2,3,4   --games 1200   --seed0 42   --assert-invariants   --reuse   --procs N

Every arm is paired against S0 on the same seeds (``mixed1`` roster); rush arms (R*) are also paired against the arm
they stress (R0 vs S1, R1-R3 vs S2) for the seat-0 win edge. Quiet by default: summary tables on stdout, raw per-game
records in sim_results/v048/<arm>_<P>P.json (``--reuse`` re-reads a saved pod instead of replaying it).

Examples:  python3 scripts/run_v048_sweep.py --arm S2 --players 3 --games 50 --assert-invariants
           python3 scripts/run_v048_sweep.py --list-arms
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from typing import Any, Callable, Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts import v046_tables as tbl  # noqa: E402
from scripts.run_v380_secret_faces_sweep import build_engine  # noqa: E402  (v0.35 setup + mixed1 roster rule)

OUT_DIR = os.path.join(ROOT, "sim_results", "v048")
_BOTH = ("RELEASE", "DEFENSE")
# arm -> (config preset, GameConfig overrides)
ARMS: Dict[str, Tuple[str, Dict[str, Any]]] = {
    "S0": ("v047_roster", {}),
    "S1": ("v048_roster", {"bot_research_mode": "LEGACY"}),
    "S2": ("v048_roster", {}),
    "S2b": ("v048_roster", {"bot_thin_tracks": _BOTH}),
    "S3": ("v047_roster", {"bot_research_mode": "THINNING_AWARE"}),
    "S0_46": ("v046_roster", {}),
    "R0": ("v048_roster", {"bot_research_mode": "LEGACY", "bot_research_rush": "p0"}),
    "R1": ("v048_roster", {"bot_research_rush": "p0"}),
    "R2": ("v048_roster", {"bot_research_rush": "p0half"}),
    "R3": ("v048_roster", {"bot_research_rush": "all"}),
    "V45": ("v045_roster", {}),
}
PAIR = {"R0": "S1", "R1": "S2", "R2": "S2", "R3": "S2"}  # rush arm -> the arm it stresses (seat-0 edge)
GUARDED = ("S2", "S2b")


# --------------------------------------------------------------------------------------------------
# Invariant assertions (--assert-invariants): wrap the engine functions once per process
# --------------------------------------------------------------------------------------------------
def install_invariant_checks() -> None:
    from sim.config import DieColor
    from sim.engine import sprint_plan as sp
    from sim.engine import vulnerability as vuln
    from sim.entities import Die

    if getattr(sp, "_checks_installed", False):
        return
    sp._checks_installed = True
    orig_review, orig_prune_all, orig_roll = sp.sprint_review, sp.prune_all, Die.roll

    def review(engine, p, chosen=None):
        ready0 = len(p.ready_for_release_dice)
        total0 = len(p.total_dice)
        bw = p.effective_release_bandwidth
        sp.prune(p)
        cur = {d.die_id for d in sp.current_sprint(p)}
        nxt = {d.die_id for d in sp.next_sprint(p)}
        grads = orig_review(engine, p, chosen)
        forced = min(len(cur), bw)
        ids = [g.die_id for g in grads]
        assert len(grads) <= bw, "INV-SP-04: more graduates than effective Release Bandwidth"
        assert set(ids[:forced]) <= cur and len(ids) >= forced, "INV-SP-03: Current graduates are not exactly the forced count"
        assert set(ids[forced:]) <= nxt and (len(ids) == forced or len(cur) < bw), "INV-SP-04: illegal Next graduates"
        assert [d.die_id for d in p.ready_for_release_dice[ready0:]] == ids, "INV-SP-07: Ready order is Current picks, then Next"
        assert len(p.total_dice) == total0, "INV-SP-07: die count not conserved"
        assert p.current_sprint_ids == {d.die_id for d in p.scanned_dice}, "INV-SP-01: Current != Sprint Plan after review"
        return grads

    def prune_all(state):
        orig_prune_all(state)
        for p in state.players:
            assert p.current_sprint_ids <= {d.die_id for d in p.scanned_dice}, "INV-SP-06: stale Current Sprint id"

    def roll(self, rng):
        was = self.current_face
        out = orig_roll(self, rng)
        if (was is not None and self.color == DieColor.GRAY and vuln.face_vuln(was) > 0):
            Die._gray_warn_rerolled = getattr(Die, "_gray_warn_rerolled", 0) + 1
            Die._gray_warn_ids = getattr(Die, "_gray_warn_ids", set()) | {self.die_id}
        return out

    sp.sprint_review, sp.prune_all = review, prune_all
    Die.roll = roll


# --------------------------------------------------------------------------------------------------
# Secret-face counter (per round) for the Round 2 dip report
# --------------------------------------------------------------------------------------------------
def install_secret_face_counter() -> None:
    from sim.engine import vulnerability as vuln

    if getattr(vuln, "_sf_counter", False):
        return
    vuln._sf_counter = True
    orig = vuln.lock_in

    def lock(engine, p, active_dice):
        acc = engine.__dict__.setdefault("_sw_sf", Counter())
        r = min(engine.state.current_round, 9)
        acc[f"sf_{r}"] += sum(1 for d in active_dice if getattr(d.current_face, "secrets_pending", 0))
        acc[f"n_{r}"] += 1
        return orig(engine, p, active_dice)

    vuln.lock_in = lock


# --------------------------------------------------------------------------------------------------
# One game
# --------------------------------------------------------------------------------------------------
def play(task: Tuple[str, str, int, int, Dict[str, Any], bool]) -> Dict[str, Any]:
    config_name, roster, players, seed, overrides, check = task
    if check:
        install_invariant_checks()
    install_secret_face_counter()
    tbl.install_block_probe()
    eng = build_engine(config_name, roster, players, seed, overrides)
    eng.state.rush_seed = seed
    # INV-SP-09 exemption is per seat: only Gray dice owned by a Helix seat may be rerolled on ⚠ (Brute-Force Bypass)
    helix_gray = {d.die_id for p in eng.state.players if "helix" in str(getattr(p, "company_code", "") or
                  getattr(getattr(p, "company", None), "code", "")).lower() for d in p.total_dice if d.color.name == "GRAY"}
    res = eng.run_game()
    s, cfg = eng.state, eng.config
    sprint = cfg.sprint_plan_enabled
    nwin = max(1, len(res.winner_ids))
    by_pid = {r["player_id"]: r for r in res.rankings}
    inc_n = inc_dead = 0
    owned_by_round: Dict[int, List[int]] = defaultdict(list)
    t = Counter()
    for tel in res.telemetry_history:
        for pid, inc in tel.income_by_player.items():
            inc_n += 1
            inc_dead += (inc["money"] + inc["research"]) <= 1
            if tel.round_number <= 4:  # early liquidity (Phase 3 income, rounds 1-4)
                t["early_cash"] += inc["money"]
                t["early_research"] += inc["research"]
                t["early_n"] += 1
        if sprint:
            t["gray_owned"] += sum(tel.gray_owned_by_player.values())
            t["gray_ready"] += sum(tel.gray_ready_by_player.values())
            t["gray_rolled"] += sum(tel.gray_rolled_by_player.values())
            t["col_rolled"] += sum(tel.colored_rolled_by_player.values())
            t["gray_vuln"] += sum(tel.gray_vuln_kept_by_player.values())
            t["col_vuln"] += sum(tel.colored_vuln_kept_by_player.values())
            t["cur_over_bw"] += sum(1 for v in tel.sprint_current_over_bw_by_player.values() if v)
            t["reviews"] += len(tel.sprint_current_by_player)
            t["l1_bw_grads"] += tel.release_l1_bandwidth_graduates
            for pid, n in tel.gray_owned_by_player.items():
                owned_by_round[tel.round_number].append(n)
    sf = getattr(eng, "_sw_sf", Counter())
    seats = []
    for p in s.players:
        r = by_pid[p.player_id]
        seats.append({
            "seat": p.player_id, "bot": p.bot.name, "win": (1.0 / nwin) if p.player_id in res.winner_ids else 0.0,
            "secrets": r["secrets"], "green_lost": p.green_secrets_lost if cfg.is_vulnerability else 0,
            "wh": r.get("white_hat_code"), "company": r.get("company_code"), "pz": bool(p.is_patient_zero),
            "max_streak": dict(p.sprint_max_streak), "wait_hist": {k: list(v) for k, v in p.sprint_wait_hist.items()},
            "thin": dict(p.gray_removed_by_source), "thin_rounds": list(p.thin_rounds), "thin_forfeits": p.thin_forfeits,
            "lock_blocked": p.gray_lock_blocked,
        })
    if check and sprint:
        from sim.entities import Die
        if cfg.vuln_face_lock == "GRAY":
            bad = getattr(Die, "_gray_warn_ids", set()) - helix_gray
            assert not bad, f"INV-SP-09: Gray dice {sorted(bad)} showing a warning face were rerolled"
        Die._gray_warn_rerolled = 0
        Die._gray_warn_ids = set()
    return {
        "seed": seed, "players": players, "end": res.end_reason.value, "rounds": res.total_rounds,
        "wipeout": bool(res.is_total_wipeout), "v1_card": s.version_deck[0].directive_code,
        "inc_n": inc_n, "inc_dead": inc_dead, "t": dict(t), "owned_by_round": {str(k): v for k, v in owned_by_round.items()},
        "sf": dict(sf), "seats": seats, "tbl": tbl.collect_game(eng, res),
    }


def play_all(arm: str, players: int, games: int, seed0: int, procs: int, check: bool) -> List[Dict[str, Any]]:
    name, ov = ARMS[arm]
    tasks = [(name, "mixed1", players, s, ov, check) for s in range(seed0, seed0 + games)]
    if procs <= 1:
        return [play(x) for x in tasks]
    from multiprocessing import Pool

    with Pool(procs) as pool:
        return pool.map(play, tasks, chunksize=max(1, len(tasks) // (procs * 8)))


# --------------------------------------------------------------------------------------------------
# Metrics and guardrails (§16.2, §17)
# --------------------------------------------------------------------------------------------------
def pct(a: float, b: float) -> Optional[float]:
    return None if not b else 100.0 * a / b


def _income(recs: List[Dict[str, Any]]) -> Dict[str, float]:
    ss = [x for r in recs for x in r["tbl"]["seats"]]
    n = sum(x["income"][2] for x in ss) or 1
    m, rs = sum(x["income"][0] for x in ss), sum(x["income"][1] for x in ss)
    blocks = sum(v for x in ss for k, v in x["blocks"].items() if k.endswith("_block"))
    return {"liquid": (m + rs) / n, "liquid_plus_blocks": (m + rs + blocks) / n, "money": m / n, "research": rs / n}


def metrics(recs: List[Dict[str, Any]], players: int) -> Dict[str, Any]:
    n = len(recs)
    ends = Counter(r["end"] for r in recs)
    seats = [x for r in recs for x in r["seats"]]
    t: Counter = Counter()
    for r in recs:
        t.update(r["t"])
    by_wh: Dict[str, List[float]] = defaultdict(list)
    by_card: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    by_bot: Dict[str, List[float]] = defaultdict(list)
    by_co: Dict[str, List[float]] = defaultdict(list)
    for x in seats:
        by_wh[str(x["wh"]).lower()].append(x["win"])
        by_bot[str(x["bot"])].append(x["win"])
        by_co[str(x["company"]).lower()].append(x["win"])
    for r in recs:
        by_card[r["v1_card"]].append(r)
    first = [x["thin_rounds"][0] for x in seats if x["thin_rounds"]]
    second = [x["thin_rounds"][1] for x in seats if len(x["thin_rounds"]) > 1]
    thin_src: Counter = Counter()
    for x in seats:
        thin_src.update(x["thin"])
    owned: Dict[int, List[int]] = defaultdict(list)
    sf: Counter = Counter()
    for r in recs:
        for k, v in r["owned_by_round"].items():
            owned[int(k)].extend(v)
        sf.update(r["sf"])
    streak = {c: max((x["max_streak"].get(c, 0) for x in seats), default=0) for c in ("gray", "colored")}
    spread = lambda d: (max(sum(v) / len(v) for v in d.values()) - min(sum(v) / len(v) for v in d.values())) * 100 if d else None  # noqa: E731
    seat0 = [x["win"] for x in seats if x["seat"] == 0]
    inc = _income(recs)
    return {
        "games": n, "rounds": sum(r["rounds"] for r in recs) / max(1, n),
        "singularity_pct": pct(ends["singularity"], n), "patient_zero_pct": pct(ends["patient_zero"], n),
        "market_collapse_pct": pct(ends["market_collapse"], n), "total_wipeout_pct": pct(sum(r["wipeout"] for r in recs), n),
        "pz_plus_collapse_pct": pct(ends["patient_zero"] + ends["market_collapse"], n),
        "green_lost_per_seat": sum(x["green_lost"] for x in seats) / max(1, len(seats)),
        "dead_turn_pct": pct(sum(r["inc_dead"] for r in recs), sum(r["inc_n"] for r in recs)),
        "liquid": inc["liquid"], "liquid_plus_blocks": inc["liquid_plus_blocks"],
        "gray_roll_share_pct": pct(t["gray_ready"], t["gray_owned"]),
        "cur_over_bw_pct": pct(t["cur_over_bw"], t["reviews"]),
        "longest_streak_gray": streak["gray"], "longest_streak_colored": streak["colored"],
        "white_hat_spread_pp": spread(by_wh), "bot_spread_pp": spread(by_bot), "company_spread_pp": spread(by_co),
        "win_by_white_hat": {k: 100 * sum(v) / len(v) for k, v in sorted(by_wh.items())},
        "win_by_bot": {k: 100 * sum(v) / len(v) for k, v in sorted(by_bot.items())},
        "win_by_company": {k: 100 * sum(v) / len(v) for k, v in sorted(by_co.items())},
        "early_cash_per_seat_round": (t["early_cash"] / t["early_n"]) if t["early_n"] else None,
        "early_research_per_seat_round": (t["early_research"] / t["early_n"]) if t["early_n"] else None, "seat0_win_pct": 100 * sum(seat0) / max(1, len(seat0)),
        "first_thin_min": min(first, default=None), "first_thin_mean": (sum(first) / len(first)) if first else None,
        "second_thin_mean": (sum(second) / len(second)) if second else None,
        "thin_by_source": {k: v / max(1, len(seats)) for k, v in sorted(thin_src.items())},
        "forfeits_per_seat": sum(x["thin_forfeits"] for x in seats) / max(1, len(seats)),
        "lock_blocked_per_seat": sum(x["lock_blocked"] for x in seats) / max(1, len(seats)),
        "owned_gray_by_round": {r: sum(v) / len(v) for r, v in sorted(owned.items()) if v and r <= 8},
        "secret_faces_by_round": {r: sf[f"sf_{r}"] / max(1, sf[f"n_{r}"]) for r in range(1, 9)},
        "spook_win_pct": 100 * sum(by_wh["spook"]) / max(1, len(by_wh["spook"])) if "spook" in by_wh else None,
        "operator_win_pct": 100 * sum(by_wh["operator"]) / max(1, len(by_wh["operator"])) if "operator" in by_wh else None,
        "by_v1_card": {c: {"games": len(g), "rounds": sum(r["rounds"] for r in g) / len(g),
                           "singularity_pct": pct(sum(r["end"] == "singularity" for r in g), len(g))}
                       for c, g in sorted(by_card.items())},
    }


def guardrails(m: Dict[str, Any], base: Dict[str, Any], ref45: Optional[Dict[str, Any]],
               players: int) -> List[Tuple[str, Any, str, Optional[bool]]]:
    i = {2: 0, 3: 1, 4: 2}[players]
    out: List[Tuple[str, Any, str, Optional[bool]]] = []
    f = lambda v: None if v is None else round(v, 2)  # noqa: E731

    def add(name, val, rule, ok):
        out.append((name, f(val), rule, None if val is None else bool(ok(val))))

    add("Delta mean rounds vs S0", m["rounds"] - base["rounds"], "within +-0.30", lambda v: abs(v) <= 0.30)
    sr = pct(m["singularity_pct"] or 0, base["singularity_pct"] or 0)
    add("Singularity share % of S0", sr, "report; >= 60", lambda v: v >= 60)
    if ref45 is not None:
        add("Income x v0.45 (method b)", m["liquid_plus_blocks"] / ref45["liquid_plus_blocks"], "<= 1.25", lambda v: v <= 1.25)
    else:
        add("Income x S0 (liquid; no --ref45)", m["liquid"] / base["liquid"], "report", lambda v: True)
    add("Green Secrets lost / seat", m["green_lost_per_seat"], "1.2-2.5", lambda v: 1.2 <= v <= 2.5)
    if players == 4:
        add("4P PZ + Collapse %", m["pz_plus_collapse_pct"], "<= 95.5", lambda v: v <= 95.5)
    add("Total Wipeout %", m["total_wipeout_pct"], f"<= {(15, 5, 2)[i]}", lambda v: v <= (15, 5, 2)[i])
    add("Dead turns % (Phase 3 $+RP <= 1)", m["dead_turn_pct"], f"<= S0 {f(base['dead_turn_pct'])}", lambda v: v <= base["dead_turn_pct"])
    add("Gray roll share %", m["gray_roll_share_pct"], ">= 45 (OQ-5)", lambda v: v >= 45)
    add("Longest stranding run (Gray)", m["longest_streak_gray"], "<= 8", lambda v: v <= 8)
    add("Longest stranding run (colored)", m["longest_streak_colored"], "<= 4", lambda v: v <= 4)
    if players == 4:
        add("White Hat spread pp", m["white_hat_spread_pp"], "<= 12", lambda v: v <= 12)
    add("Earliest thin round", m["first_thin_min"], ">= 2 (Phase 5)", lambda v: v >= 2)
    return out


def print_guardrails(arm: str, gr: List[Tuple[str, Any, str, Optional[bool]]]) -> None:
    print(f"{'guardrail':40}{arm:>9}  {'rule':26}result")
    for name, val, rule, ok in gr:
        print(f"{name:40}{'n/a' if val is None else val:>9}  {rule:26}{'n/a' if ok is None else ('PASS' if ok else 'FAIL')}")


def print_pod(arm: str, players: int, m: Dict[str, Any]) -> None:
    keys = ("games", "rounds", "singularity_pct", "patient_zero_pct", "market_collapse_pct", "total_wipeout_pct",
            "green_lost_per_seat", "dead_turn_pct", "liquid", "gray_roll_share_pct", "cur_over_bw_pct",
            "longest_streak_gray", "longest_streak_colored", "white_hat_spread_pp", "seat0_win_pct",
            "first_thin_mean", "second_thin_mean", "forfeits_per_seat", "lock_blocked_per_seat")
    print(f"[{arm} {players}P] " + "  ".join(f"{k}={'n/a' if m[k] is None else round(m[k], 2)}" for k in keys))
    print("   thin by source/seat: " + json.dumps({k: round(v, 3) for k, v in m["thin_by_source"].items()})
          + "  owned Gray R1-8: " + " ".join(f"{v:.1f}" for v in m["owned_gray_by_round"].values())
          + "  secret faces/roll R1-8: " + " ".join(f"{v:.2f}" for v in m["secret_faces_by_round"].values()))
    print("   Spook win% " + str(None if m["spook_win_pct"] is None else round(m["spook_win_pct"], 1))
          + "  Operator win% " + str(None if m["operator_win_pct"] is None else round(m["operator_win_pct"], 1))
          + "  v1.0 card: " + ", ".join(f"{c} n={d['games']} r={d['rounds']:.2f} sing={d['singularity_pct']:.0f}%"
                                         for c, d in m["by_v1_card"].items()))
    ec, er = m.get("early_cash_per_seat_round"), m.get("early_research_per_seat_round")
    print("   early R1-4 per seat-round: cash " + ("n/a" if ec is None else f"{ec:.2f}") + "  research "
          + ("n/a" if er is None else f"{er:.2f}") + f"  spreads pp: bot {m['bot_spread_pp']:.1f}"
          f"  company {m['company_spread_pp']:.1f}")
    for k in ("win_by_bot", "win_by_company", "win_by_white_hat"):
        print(f"   {k}: " + ", ".join(f"{a} {b:.1f}" for a, b in m[k].items()))


def save(name: str, payload: Any) -> str:
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    with open(path, "w") as fh:
        json.dump(payload, fh, separators=(",", ":"), default=str)
    return path


def get_pod(arm: str, players: int, args: argparse.Namespace) -> List[Dict[str, Any]]:
    path = os.path.join(OUT_DIR, f"{arm}_{players}P.json")
    if args.reuse and os.path.exists(path):
        with open(path) as fh:
            recs = json.load(fh)
        if len(recs) == args.games and recs and recs[0]["seed"] == args.seed0:
            return recs
    recs = play_all(arm, players, args.games, args.seed0, args.procs, args.assert_invariants)
    save(f"{arm}_{players}P.json", recs)
    return recs


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", default="S2")
    ap.add_argument("--players", default="2,3,4")
    ap.add_argument("--games", type=int, default=1200)
    ap.add_argument("--seed0", type=int, default=42)
    ap.add_argument("--procs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--assert-invariants", action="store_true")
    ap.add_argument("--reuse", action="store_true", help="reuse saved pods from sim_results/v048 when games/seed0 match")
    ap.add_argument("--ref45", action="store_true", help="also run V45 (v045_roster) for the method-b income ratio")
    ap.add_argument("--list-arms", action="store_true")
    args = ap.parse_args(argv)
    if args.list_arms:
        print(" ".join(ARMS))
        return 0
    if args.arm not in ARMS:
        ap.error(f"unknown arm {args.arm!r}; choose from {list(ARMS)}")
    for pl in [int(x) for x in args.players.split(",")]:
        recs = get_pod(args.arm, pl, args)
        m = metrics(recs, pl)
        print_pod(args.arm, pl, m)
        summary: Dict[str, Any] = {"arm": args.arm, "players": pl, "metrics": m}
        if args.arm != "S0":
            s0 = metrics(get_pod("S0", pl, args), pl)
            ref = metrics(get_pod("V45", pl, args), pl) if args.ref45 else None
            gr = guardrails(m, s0, ref, pl)
            print_guardrails(args.arm, gr)
            summary["guardrails"] = gr
            print(f"   vs S0: d rounds {m['rounds'] - s0['rounds']:+.2f}  singularity {m['singularity_pct']:.1f}% vs {s0['singularity_pct']:.1f}%")
        if args.arm in PAIR:
            base = metrics(get_pod(PAIR[args.arm], pl, args), pl)
            edge = m["seat0_win_pct"] - base["seat0_win_pct"]
            summary["rush_edge_pp"] = edge
            print(f"   rush edge (seat 0 win, {args.arm} - {PAIR[args.arm]}): {edge:+.2f} pp (bar <= +4 on the S2 pair)")
        save(f"summary_{args.arm}_{pl}P.json", summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
