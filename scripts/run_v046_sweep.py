"""v0.46.0 Vulnerability Track sweeps (spec §14.4, Steps 1, 2 and 5).

  --step smoke   v046_roster, 2P/3P/4P, 300 games per pod, every invariant asserted inside the loop
  --step main    v045_roster vs v046_roster, mixed1 roster rule, seeds 42..1241, 1,200 per pod (2P/3P/4P) + guardrails
  --step arm --arm <id>   one sweep arm (spec §3.5) on v046_roster, 600 games at 3P (Red / Total Wipeout arms also at 2P)

Quiet by default: summary tables on stdout, raw per-game records in sim_results/v046/<name>.json.
Examples (smoke sizes):  python3 scripts/run_v046_sweep.py --step smoke --games 10
                         python3 scripts/run_v046_sweep.py --step main --games 20
                         python3 scripts/run_v046_sweep.py --step arm --arm bands_4_7_10 --games 20
Pass ``--list-arms`` to print the arm ids.
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

from scripts import v046_tables as tbl  # noqa: E402
from scripts.run_v380_secret_faces_sweep import build_engine  # noqa: E402  (v0.35 setup + mixed1 roster rule)

OUT_DIR = os.path.join(ROOT, "sim_results", "v046")
_RED15 = {2: 13, 3: 16, 4: 16}
_PR2 = {i: 2 for i in range(5)}
ARMS: Dict[str, Dict[str, Any]] = {
    "red_A": {},
    "red_none": {"market_share_start_by_player_count": _RED15},
    "red_B": {"market_share_start_by_player_count": _RED15, "share_regain_cost_by_level": dict(_PR2)},
    "red_AB": {"share_regain_cost_by_level": dict(_PR2)},
    "bands_3_6_9": {"vuln_band_thresholds": (3, 6, 9)},  # the pre-package bands (v0.46 default is 4/7/10)
    "bands_3_5_7": {"vuln_band_thresholds": (3, 5, 7)},
    "min_target_3": {"vuln_min_target_by_version": (3, 3, 3)},  # old behaviour: Vulnerability 3 targetable (dmg 1)
    "green_yield_1": {"green_secret_vuln_reduction": 1},
    "green_yield_0": {"green_secret_vuln_reduction": 0},
    "pen_l1_zero": {"pen_test_l1": "SET_ZERO"},
    "premium_on": {"die_face_profile": "V046_VULN"},  # the old +1 🔬 premium on colored ⚠ faces (default is NOPREMIUM)
    # 2026-11-18 safe zone 0-3: the old v3_min2 would put 2 inside the safe zone, so the arm is v3.0 hits from 3 (dmg 1)
    "v3_min3": {"vuln_min_target_by_version": (4, 4, 3)},
    "l4_set_zero": {"pen_test_l4_set_zero_on_reach": True},
    # counter-levers (only if Step 3 fails)
    "ctr_corruption3": {"corruption_lowest_vuln_gain": 3, "corruption_lowest_vuln_gain_double": 4},
    # Pen Test cost {1, first-step 2, 2} (the v0.46 default is 2)
    "pen_cost_1": {"pen_test_cost": 1},
    "pen_first_step_2": {"pen_test_cost": 1, "pen_test_first_step_cost": 2},
    "pen_cost_2": {"pen_test_cost": 2},
    # Data Scraper (v1.0) starting bonus: +$1, +1 Corporate Secret (the default), both
    "ds_cash": {"data_scraper_cash_bonus": 1, "data_scraper_secret_bonus": 0},
    "ds_secret": {"data_scraper_cash_bonus": 0, "data_scraper_secret_bonus": 1},
    "ds_both": {"data_scraper_cash_bonus": 1, "data_scraper_secret_bonus": 1},
    "ctr_l4_free0": {"pen_test_l4_free": 0},
}
TWO_P_ARMS = {"red_A", "red_none", "red_B", "red_AB"}  # Red arms (and Total Wipeout watch) also at 2P


# --------------------------------------------------------------------------------------------------
# Invariant assertions (smoke): wrap the engine functions once per process
# --------------------------------------------------------------------------------------------------
def install_invariant_checks() -> None:
    from sim.engine import phase4_attack_resolution as p4
    from sim.engine import vulnerability as vuln

    if getattr(vuln, "_checks_installed", False):
        return
    vuln._checks_installed = True
    orig_green, orig_pen, orig_rb = vuln.resolve_green, vuln.execute_pen_test, p4.resolve_player_red_blue_v046

    def snap(engine):
        return [(p.money, p.research_tokens, p.market_share, len(p.total_dice)) for p in engine.state.players]

    def green(engine, cr, attack):
        before, pz = snap(engine), [p.is_patient_zero for p in engine.state.players]
        ev = orig_green(engine, cr, attack)
        assert snap(engine) == before, "INV-VULN-05: Green changed dice / money / research / Market Share"
        assert pz == [p.is_patient_zero for p in engine.state.players], "INV-VULN-06: Green set Patient Zero"
        hit = Counter(pid for e in ev for pid in e["pids"])
        assert all(n <= 1 for n in hit.values()), "INV-VULN-05: a player was hit twice in a round"
        for p in engine.state.players:
            assert 0 <= p.vulnerability <= engine.config.vuln_track_max, "INV-VULN-02: out of range"
        return ev

    def pen(engine, p, wanted):
        cfg = engine.config
        r0, v0, s0 = p.research_tokens, p.vulnerability, p.pen_test_steps
        done = orig_pen(engine, p, wanted)
        assert done <= max(0, int(wanted or 0)), "INV-PEN-01: more steps than asked"
        assert p.pen_test_this_turn <= cfg.pen_test_limits[p.defense_level], "INV-PEN-01: limit exceeded"
        assert v0 - p.vulnerability == done and p.vulnerability >= 0, "INV-PEN-01: Vulnerability delta"
        assert r0 - p.research_tokens >= done * cfg.pen_test_cost, "INV-PEN-01: research not spent"
        assert p.pen_test_steps - s0 == done
        return done

    def rb(engine, player, attack, cr, **kw):
        pz = player.is_patient_zero
        out = orig_rb(engine, player, attack, cr, **kw)
        assert player.is_patient_zero == pz, "INV-VULN-06: Red/Blue set Patient Zero"
        return out

    vuln.resolve_green, vuln.execute_pen_test, p4.resolve_player_red_blue_v046 = green, pen, rb


# --------------------------------------------------------------------------------------------------
# One game
# --------------------------------------------------------------------------------------------------
def play(task: Tuple[str, str, int, int, Dict[str, Any], bool]) -> Dict[str, Any]:
    config_name, roster, players, seed, overrides, check = task
    if check:
        install_invariant_checks()
    tbl.install_block_probe()
    eng = build_engine(config_name, roster, players, seed, overrides)
    res = eng.run_game()
    s = eng.state
    cfg = eng.config
    nwin = max(1, len(res.winner_ids))
    vuln_on = cfg.is_vulnerability
    min_cost = min((c.cost for c in s.variant_cards.values()), default=4)
    resolved = no_target = resolved7 = no_target7 = lose3 = player_rounds = cap_rounds = 0
    liquid = liquid_n = 0
    unaff = {p.player_id: [] for p in s.players}
    alive = Counter()
    for t in res.telemetry_history:
        resolved += t.green_cubes_resolved
        no_target += t.green_cubes_no_target
        if t.round_number >= 7:
            resolved7 += t.green_cubes_resolved
            no_target7 += t.green_cubes_no_target
        lose3 += sum(1 for v in t.green_secrets_lost_by_player.values() if v >= 3)
        snap4 = t.phase_snapshots.get(4) or []
        for i, row in enumerate(snap4):
            if row.get("is_patient_zero"):
                continue
            player_rounds += 1
            alive[row["player_id"]] += 1
            unaff[row["player_id"]].append(row["money"] < min_cost)
            inc = t.income_by_player.get(row["player_id"])
            if inc is not None:
                liquid += inc["money"] + inc["research"]
                liquid_n += 1
    b2b = sum(1 for flags in unaff.values() for a, b in zip(flags, flags[1:]) if a and b)
    v1_name = s.version_deck[0].name if s.version_deck else ""
    v1_breach = any(t.active_version_name == v1_name and any(x.get("is_patient_zero") for x in t.player_snapshots)
                    for t in res.telemetry_history)
    seats = []
    by_pid = {r["player_id"]: r for r in res.rankings}
    for p in s.players:
        r = by_pid[p.player_id]
        cap = p.vuln_rounds_at_cap
        cap_rounds += cap
        e, l = p.vuln_keep_by_round, None
        seats.append({
            "seat": p.player_id, "bot": p.bot.name, "stance": p.vuln_stance_this_round, "alive_rounds": alive[p.player_id], "company": r.get("company_code"),
            "win": (1.0 / nwin) if p.player_id in res.winner_ids else 0.0, "secrets": r["secrets"],
            "green_lost": p.green_secrets_lost if vuln_on else p.secrets_lost_to_overflow,
            "levels": [p.defense_level, p.triage_level, p.release_level, p.patent_level],
            "keep": [p.vuln_keep_kept, p.vuln_keep_events], "keep_by_round": {str(k): v for k, v in e.items()},
            "pen_steps": p.pen_test_steps, "pen_research": p.pen_test_research_spent,
            "icons": p.vuln_icons_kept_total, "vuln_peak": p.vuln_peak, "overflow_lost": p.vuln_overflow_lost,
        })
    if check and vuln_on:
        for p in s.players:
            assert 0 <= p.vulnerability <= cfg.vuln_track_max and 0 <= p.vuln_peak <= cfg.vuln_track_max
            assert sum(p.vuln_gained_by_source.values()) - sum(p.vuln_lowered_by_source.values()) \
                - p.vuln_reset_by_hit_total == p.vulnerability, "INV-VULN-01/02: Vulnerability ledger does not balance"
    return {
        "seed": seed, "players": players, "end": res.end_reason.value, "rounds": res.total_rounds,
        "wipeout": bool(res.is_total_wipeout), "v1_breach": v1_breach, "v1_card": s.version_deck[0].directive_code, "green_resolved": resolved,
        "green_no_target": no_target, "green_resolved7": resolved7, "green_no_target7": no_target7,
        "lose3_rounds": lose3, "player_rounds": player_rounds, "cap_rounds": cap_rounds, "liquid": liquid,
        "liquid_n": liquid_n, "b2b_unaffordable": b2b, "seats": seats, "tbl": tbl.collect_game(eng, res),
    }


def play_all(config_name: str, roster: str, players: int, games: int, seed0: int, overrides: Dict[str, Any],
             procs: int, check: bool) -> List[Dict[str, Any]]:
    tasks = [(config_name, roster, players, s, overrides, check) for s in range(seed0, seed0 + games)]
    if procs <= 1:
        return [play(t) for t in tasks]
    from multiprocessing import Pool

    with Pool(procs) as pool:
        return pool.map(play, tasks, chunksize=max(1, len(tasks) // (procs * 8)))


# --------------------------------------------------------------------------------------------------
# Metrics and guardrails (plan §10.4)
# --------------------------------------------------------------------------------------------------
def pct(a: float, b: float) -> Optional[float]:
    return None if not b else 100.0 * a / b


def metrics(recs: List[Dict[str, Any]], players: int) -> Dict[str, Any]:
    n = len(recs)
    ends = Counter(r["end"] for r in recs)
    seats = [x for r in recs for x in r["seats"]]
    adaptive = [x for x in seats if x["stance"] == "ADAPTIVE"]  # Secrets-lost-to-Green is measured on Adaptive seats
    by_company: Dict[str, List[float]] = defaultdict(list)
    by_seat: Dict[int, List[float]] = defaultdict(list)
    for x in seats:
        by_company[x["company"]].append(x["win"])
        by_seat[x["seat"]].append(x["win"])
    kept = sum(x["keep"][0] for x in seats)
    ev = sum(x["keep"][1] for x in seats)
    early = [0, 0]
    late = [0, 0]
    for x in seats:
        for rk, (k, e) in x["keep_by_round"].items():
            tgt = early if int(rk) <= 3 else (late if int(rk) >= 6 else None)
            if tgt is not None:
                tgt[0] += k
                tgt[1] += e
    spread = lambda d: (max(sum(v) / len(v) for v in d.values()) - min(sum(v) / len(v) for v in d.values())) * 100 if d else None  # noqa: E731
    return {
        "games": n,
        "rounds": sum(r["rounds"] for r in recs) / max(1, n),
        "patient_zero_pct": pct(ends["patient_zero"], n), "total_wipeout_pct": pct(sum(r["wipeout"] for r in recs), n),
        "market_collapse_pct": pct(ends["market_collapse"], n), "singularity_pct": pct(ends["singularity"], n),
        "v1_breach_pct": pct(sum(r["v1_breach"] for r in recs), n),
        "green_lost_per_player_game": sum(x["green_lost"] for x in adaptive) / max(1, len(adaptive)),
        "green_lost_per_player_round": sum(x["green_lost"] for x in adaptive) / max(1, sum(x["alive_rounds"] for x in adaptive)),
        "by_v1_card": {c: {"games": len(g), "share_pct": pct(len(g), n),
                           "v1_breach_pct": pct(sum(r["v1_breach"] for r in g), len(g)),
                           "rounds": sum(r["rounds"] for r in g) / len(g),
                           "patient_zero_pct": pct(sum(r["end"] == "patient_zero" for r in g), len(g)),
                           "singularity_pct": pct(sum(r["end"] == "singularity" for r in g), len(g)),
                           "market_collapse_pct": pct(sum(r["end"] == "market_collapse" for r in g), len(g)),
                           "total_wipeout_pct": pct(sum(r["wipeout"] for r in g), len(g))}
                       for c in sorted({r["v1_card"] for r in recs})
                       for g in [[r for r in recs if r["v1_card"] == c]]},
        "green_no_target_pct": pct(sum(r["green_no_target"] for r in recs), sum(r["green_resolved"] for r in recs)),
        "green_no_target_r7_pct": pct(sum(r["green_no_target7"] for r in recs), sum(r["green_resolved7"] for r in recs)),
        "lose3_pct": pct(sum(r["lose3_rounds"] for r in recs), sum(r["player_rounds"] for r in recs)),
        "liquid_per_player_round": sum(r["liquid"] for r in recs) / max(1, sum(r["liquid_n"] for r in recs)),
        "company_spread_pp": spread(by_company) if players == 4 else None,
        "seat_spread_pp": spread(by_seat) if players == 4 else None,
        "two_l4_pct": pct(sum(1 for x in seats if sum(1 for lv in x["levels"] if lv >= 4) >= 2), len(seats)),
        "cap_pct": pct(sum(r["cap_rounds"] for r in recs), sum(r["player_rounds"] for r in recs)),
        "b2b_unaffordable_per_game": sum(r["b2b_unaffordable"] for r in recs) / max(1, n),
        "keep_rate_pct": pct(kept, ev), "keep_early_pct": pct(*early), "keep_late_pct": pct(*late),
        "pen_steps_per_player_game": sum(x["pen_steps"] for x in seats) / max(1, len(seats)),
    }


def guardrails(m45: Dict[str, Any], m46: Dict[str, Any], players: int) -> List[Tuple[str, Any, str, Optional[bool]]]:
    i = {2: 0, 3: 1, 4: 2}[players]
    f = lambda v: None if v is None else round(v, 2)  # noqa: E731
    g: List[Tuple[str, Any, str, Optional[bool]]] = []

    def add(name, val, rule, ok):
        g.append((name, f(val), rule, None if val is None else bool(ok(val))))

    add("Mean rounds", m46["rounds"], "6.5-8.5", lambda v: 6.5 <= v <= 8.5)
    add("Patient Zero ending %", m46["patient_zero_pct"], f"<= v0.45 {f(m45['patient_zero_pct'])} + 3", lambda v: v <= m45["patient_zero_pct"] + 3)
    add("Total Wipeout %", m46["total_wipeout_pct"], f"<= {(15, 5, 2)[i]}", lambda v: v <= (15, 5, 2)[i])
    add("Market Collapse %", m46["market_collapse_pct"], f"v0.45 {f(m45['market_collapse_pct'])} +-5", lambda v: abs(v - m45["market_collapse_pct"]) <= 5)
    add("v1.0 breach %", m46["v1_breach_pct"], f"<= v0.45 {f(m45['v1_breach_pct'])}", lambda v: v <= m45["v1_breach_pct"])
    add("Secrets lost to Green / player-game", m46["green_lost_per_player_game"],
        f"1.2-2.5 (v0.45 Overflow {f(m45['green_lost_per_player_game'])})", lambda v: 1.2 <= v <= 2.5)
    add("Secrets lost to Green / player-round", m46["green_lost_per_player_round"],
        f"report (<= 0.35 proposed; v0.45 {f(m45['green_lost_per_player_round'])})", lambda v: v <= 0.35)
    add("Green no-target % (overall)", m46["green_no_target_pct"], "25-70", lambda v: 25 <= v <= 70)
    add("Green no-target % (rounds 7+)", m46["green_no_target_r7_pct"], "flag if > 60", lambda v: v <= 60)
    add("Player-rounds losing 3 to Green %", m46["lose3_pct"], "<= 5", lambda v: v <= 5)
    base = m45["liquid_per_player_round"]
    add("Liquid income / player-round", m46["liquid_per_player_round"], f"<= v0.45 {f(base)} x 1.25", lambda v: v <= base * 1.25)
    add("Company spread pp (4P)", m46["company_spread_pp"], "<= 10", lambda v: v <= 10)
    add("Seat spread pp (4P)", m46["seat_spread_pp"], "<= 6", lambda v: v <= 6)
    add("2+ L4 tracks %", m46["two_l4_pct"], "<= 5", lambda v: v <= 5)
    add("Player-rounds at cap %", m46["cap_pct"], "<= 1", lambda v: v <= 1)
    add("Back-to-back unaffordable / game", m46["b2b_unaffordable_per_game"], f"<= v0.45 {f(m45['b2b_unaffordable_per_game'])}",
        lambda v: v <= m45["b2b_unaffordable_per_game"])
    return g


def print_guardrails(m45: Dict[str, Any], m46: Dict[str, Any], players: int) -> List[Any]:
    gr = guardrails(m45, m46, players)
    print(f"{'guardrail':42}{'v0.46':>9}  {'rule':40}result")
    for name, val, rule, ok in gr:
        print(f"{name:42}{'n/a' if val is None else val:>9}  {rule:40}{'n/a' if ok is None else ('PASS' if ok else 'FAIL')}")
    return gr


def print_card_split(m45: Optional[Dict[str, Any]], m46: Dict[str, Any]) -> None:
    """Breach, rounds and endings split by the v1.0 Version Card (standard guardrail-table companion)."""
    print("\nv1.0 card split (v0.46" + (" | v0.45" if m45 else "") + ")")
    print(f"{'card':14}{'ver':>6}{'games%':>8}{'v1 breach%':>12}{'rounds':>8}{'PZ%':>7}{'Sing%':>7}{'MC%':>7}{'TW%':>6}")
    for ver, m in (("v0.46", m46), ("v0.45", m45)):
        if not m:
            continue
        for card, d in m["by_v1_card"].items():
            print(f"{card:14}{ver:>6}{d['share_pct']:>8.1f}{d['v1_breach_pct']:>12.1f}{d['rounds']:>8.2f}"
                  f"{d['patient_zero_pct']:>7.1f}{d['singularity_pct']:>7.1f}{d['market_collapse_pct']:>7.1f}{d['total_wipeout_pct']:>6.1f}")


def print_pod(title: str, m: Dict[str, Any]) -> None:
    keys = ("games", "rounds", "patient_zero_pct", "total_wipeout_pct", "market_collapse_pct", "singularity_pct",
            "green_lost_per_player_game", "green_no_target_pct", "keep_rate_pct", "keep_early_pct", "keep_late_pct",
            "pen_steps_per_player_game")
    print(f"{title}: " + "  ".join(f"{k}={'n/a' if m[k] is None else round(m[k], 2)}" for k in keys))


def parse_overrides(set_json: Optional[str], vuln_params_json: Optional[str]) -> Dict[str, Any]:
    """``--set '{"vuln_band_thresholds": [4,7,10]}'`` and ``--vuln-params '{"secret_value": 2.0}'`` (OQ-8: bot
    lambda parameters are config, so the product-owner can retune without code changes)."""
    out: Dict[str, Any] = tbl.coerce_overrides(json.loads(set_json or "{}"))
    if vuln_params_json:
        from sim.config import VulnPolicyParams

        out["vuln_bot_params"] = VulnPolicyParams(**json.loads(vuln_params_json))
    return out


def print_full_tables(recs45: Optional[List[Dict[str, Any]]], recs46: List[Dict[str, Any]], players: int) -> Dict[str, Any]:
    """Items 1-8 (v0.46 vs v0.45 at the same pod). Returns the JSON ``summary`` block."""
    t46 = [r["tbl"] for r in recs46]
    t45 = [r["tbl"] for r in recs45] if recs45 else []
    print(f"\n######## {players}P summary tables ({len(t46)} games per version) ########")
    out: Dict[str, Any] = {}
    out["income"] = tbl.t_income(t45, t46)
    out["company_colour"] = tbl.t_company_colour(t45, t46, players)
    out["strategy"] = tbl.t_strategy(t46, players, "(v0.46) ")
    out["ledger"] = tbl.t_ledger(t45, t46)
    groups = {"v0.46 all seats": tbl._seats(t46)}
    if t45:
        groups["v0.45 all seats"] = tbl._seats(t45)
    by_label: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for x in tbl._seats(t46):
        by_label[x["label"]].append(x)
    groups.update({f"v0.46 {k}": v for k, v in sorted(by_label.items())})
    out["levels"] = tbl.t_levels(groups)
    out["keep_faces"] = tbl.t_keep_faces(t46)
    out["green"] = tbl.t_green(t46, f"({players}P)")
    out["singularity"] = tbl.t_singularity(t45, t46)
    return out


def save(name: str, payload: Dict[str, Any]) -> str:
    path = tbl.resolve_out(name, "out.json", OUT_DIR)
    with open(path, "w") as fh:
        json.dump(payload, fh)
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--step", choices=("smoke", "main", "arm"), default="smoke")
    ap.add_argument("--arm", default=None)
    ap.add_argument("--list-arms", action="store_true")
    ap.add_argument("--games", type=int, default=None, help="per pod / arm (defaults: smoke 300, main 1200, arm 600)")
    ap.add_argument("--seed0", type=int, default=42)
    ap.add_argument("--players", default=None, help="comma list, e.g. 3 or 2,3,4")
    ap.add_argument("--roster", default="mixed1", choices=("mixed1", "archetypes"))
    ap.add_argument("--procs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--assert-invariants", action="store_true")
    ap.add_argument("--set", default=None, help='extra GameConfig overrides (JSON) applied to v046_roster')
    ap.add_argument("--vuln-params", default=None, help='VulnPolicyParams overrides (JSON), e.g. \'{"secret_value": 2.0}\'')
    ap.add_argument("--out", default=None)
    ap.add_argument("--tables", choices=("full", "basic", "guard"), default=None,
                    help="full = items 1-8 summary tables (default for --step main); guard = metrics + guardrails + v1.0 "
                         "card split + income (b) + company table (default for --step arm, needs a v0.45 baseline run); "
                         "basic = metrics line only")
    ap.add_argument("--no-baseline", action="store_true", help="arm step: skip the v0.45 comparator run")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--quiet", action="store_true", default=True, help="(default) summary only")
    a = ap.parse_args()
    if a.list_arms:
        print("\n".join(ARMS))
        return
    if a.tables is None:
        a.tables = "guard" if a.step == "arm" else ("full" if a.step == "main" else "basic")
    pods = [int(x) for x in a.players.split(",")] if a.players else None
    extra = parse_overrides(a.set, a.vuln_params)
    if a.step == "smoke":
        games = a.games or 300
        out: Dict[str, Any] = {"step": "smoke", "pods": {}}
        for pl in pods or (2, 3, 4):
            recs = play_all("v046_roster", a.roster, pl, games, a.seed0, dict(extra), a.procs, True)
            m = metrics(recs, pl)
            out["pods"][str(pl)] = {"metrics": m, "games": recs if a.verbose else None}
            print_pod(f"smoke {pl}P invariants OK", m)
            print_card_split(None, m)
            if a.tables == "full":
                out["pods"][str(pl)]["summary"] = print_full_tables(None, recs, pl)
        print("wrote", save(a.out or "smoke.json", out))
    elif a.step == "main":
        games = a.games or 1200
        out = {"step": "main", "pods": {}}
        for pl in pods or (2, 3, 4):
            r45 = play_all("v045_roster", a.roster, pl, games, a.seed0, {}, a.procs, a.assert_invariants)
            r46 = play_all("v046_roster", a.roster, pl, games, a.seed0, dict(extra), a.procs, a.assert_invariants)
            m45, m46 = metrics(r45, pl), metrics(r46, pl)
            gr = guardrails(m45, m46, pl)
            out["pods"][str(pl)] = {"v045": m45, "v046": m46, "guardrails": gr}
            if a.tables != "basic":
                out["pods"][str(pl)]["summary"] = print_full_tables(r45, r46, pl)
            print(f"\n== {pl}P, {games} games/pod (v0.45 vs v0.46) ==")
            print_pod("v0.45", m45)
            print_pod("v0.46", m46)
            print_guardrails(m45, m46, pl)
            print_card_split(m45, m46)
        print("wrote", save(a.out or "main.json", out))
    else:
        if not a.arm or a.arm not in ARMS:
            ap.error(f"--arm must be one of {list(ARMS)}")
        games = a.games or 600
        out = {"step": "arm", "arm": a.arm, "overrides": {k: str(v) for k, v in ARMS[a.arm].items()}, "pods": {}}
        for pl in pods or ((3, 2) if a.arm in TWO_P_ARMS else (3,)):
            recs = play_all("v046_roster", a.roster, pl, games, a.seed0, {**ARMS[a.arm], **extra}, a.procs, a.assert_invariants)
            m = metrics(recs, pl)
            out["pods"][str(pl)] = {"metrics": m}
            print(f"\n== arm {a.arm}, {pl}P, {games} games ==")
            print_pod(f"arm {a.arm} {pl}P", m)
            if a.tables == "basic":
                continue
            # guardrail columns as in main: v0.45 comparator at the same pod/seeds (skip with --no-baseline)
            r45 = None if a.no_baseline else play_all("v045_roster", a.roster, pl, games, a.seed0, {}, a.procs, False)
            m45 = metrics(r45, pl) if r45 else None
            if m45:
                out["pods"][str(pl)]["v045"] = m45
                out["pods"][str(pl)]["guardrails"] = print_guardrails(m45, m, pl)
            print_card_split(m45, m)
            t46 = [r["tbl"] for r in recs]
            t45 = [r["tbl"] for r in r45] if r45 else []
            out["pods"][str(pl)]["income"] = tbl.t_income(t45, t46)
            out["pods"][str(pl)]["company_colour"] = tbl.t_company_colour(t45, t46, pl)
            if a.tables == "full":
                out["pods"][str(pl)]["summary"] = print_full_tables(r45, recs, pl)
        print("wrote", save(a.out or f"arm_{a.arm}.json", out))


if __name__ == "__main__":
    main()
