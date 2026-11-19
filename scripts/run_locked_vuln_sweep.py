"""v0.47.0 Locked ⚠ Faces sweeps (docs/specs/locked_vuln_faces_spec.md §11.1).

  --step smoke   v046_locked_roster, 2P/3P/4P, 300 games per pod, every invariant asserted inside the loop
  --step main    v045_roster (guardrail comparator), v046_roster (delta comparator), v046_locked_roster; mixed1 roster rule,
                 seeds 42..1241, 1,200 per pod; pre-checks v046_roster against FINDINGS §62 and stops when it differs
  --step arm --arm <id>   one sweep arm on v046_locked_roster (override dict), 1,200 games per pod by default

Quiet by default: summary tables on stdout, raw per-game records in sim_results/locked_vuln_v046base/<name>.json.
``--set`` / ``--vuln-params`` are layered onto the preset (``dataclasses.replace(cfg.vuln_bot_params, **json)``), never
built from a fresh ``VulnPolicyParams`` (that would silently reset every other bot parameter).
Examples (smoke sizes):  python3 scripts/run_locked_vuln_sweep.py --step smoke --games 10
                         python3 scripts/run_locked_vuln_sweep.py --step main --games 20
                         python3 scripts/run_locked_vuln_sweep.py --step arm --arm bots_aware --games 20
Pass ``--list-arms`` to print the arm ids.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from collections import Counter, defaultdict
from typing import Any, Callable, Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts import run_v046_sweep as rv  # noqa: E402
from scripts import v046_tables as tbl  # noqa: E402

OUT_DIR = os.path.join(ROOT, "sim_results", "locked_vuln_v046base")
CONFIG = "v046_locked_roster"
COLORS = ("red", "blue", "green", "yellow")
LOCKABLE = ("red", "blue", "green", "yellow", "purple")

# Overrides on v046_locked_roster (dicts, not presets). ``vuln_bot_params`` dicts are layered onto the preset's params.
ARMS: Dict[str, Dict[str, Any]] = {
    "A_nopremium": {"die_face_profile": "V046_VULN_NOPREMIUM"},                                        # D2 control
    "B_safe03": {"vuln_band_thresholds": (4, 7, 10), "vuln_min_target_by_version": (4, 4, 4)},          # D1 control
    "A_safe03": {"die_face_profile": "V046_VULN_NOPREMIUM", "vuln_band_thresholds": (4, 7, 10),
                 "vuln_min_target_by_version": (4, 4, 4)},                                              # probe arm A
    "dmg_112": {"vuln_band_damage": (1, 1, 2)},                                                         # counter-lever
    "green_yield_3": {"green_secret_vuln_reduction": 3},                                                # counter-lever
    "pen_cost_1": {"pen_test_cost": 1},                                                                 # counter-lever
    "secret_lock_off": {"colored_vuln_lock_secret": False},                                             # D5 control
    "helix_per_version": {"helix_bypass_once_per_game": False},                                         # cost of once/game
    "helix_legacy": {"helix_bypass_mode": "LEGACY", "helix_bypass_once_per_game": False},               # probe semantics
    "bots_naive": {"vuln_bot_params": {"lock_policy": "NONE"}},
    "bots_aware": {"vuln_bot_params": {"lock_policy": "AWARE"}},
    "bots_lambda": {"vuln_bot_params": {"lock_policy": "LAMBDA"}},
    "pen_lock_headroom": {"vuln_bot_params": {"pen_lock_headroom": 1}},                                 # optional (OQ-5)
}

# FINDINGS §62 v0.46 reference (2P / 3P / 4P) for the --step main pre-check
PRECHECK = {"green_lost_per_player_game": (2.42, 2.08, 1.86), "rounds": (8.20, 7.77, 7.51),
            "market_collapse_pct": (35.7, 21.1, 22.8)}
PRECHECK_TOL = {"green_lost_per_player_game": 0.15, "rounds": 0.15, "market_collapse_pct": 3.0}


# --------------------------------------------------------------------------------------------------
# Overrides (layered onto the preset)
# --------------------------------------------------------------------------------------------------
def resolve_overrides(config_name: str, overrides: Dict[str, Any]) -> Dict[str, Any]:
    """``vuln_bot_params`` given as a dict is layered onto the preset's own ``VulnPolicyParams``."""
    from sim.config import GameConfig

    out = dict(overrides)
    vp = out.get("vuln_bot_params")
    if isinstance(vp, dict):
        base = getattr(GameConfig, config_name)(num_players=3).vuln_bot_params
        out["vuln_bot_params"] = dataclasses.replace(base, **vp)
    return out


def parse_overrides(set_json: Optional[str], vuln_params_json: Optional[str]) -> Dict[str, Any]:
    """Raw (unresolved) overrides; ``--vuln-params`` stays a dict so it is layered at build time."""
    out: Dict[str, Any] = tbl.coerce_overrides(json.loads(set_json or "{}"))
    if vuln_params_json:
        prior = out.get("vuln_bot_params") if isinstance(out.get("vuln_bot_params"), dict) else {}
        out["vuln_bot_params"] = {**prior, **json.loads(vuln_params_json)}
    return out


# --------------------------------------------------------------------------------------------------
# Invariants (smoke)
# --------------------------------------------------------------------------------------------------
def install_lock_checks() -> None:
    from sim.engine import phase1_roll_deploy as p1
    from sim.engine import vulnerability as vuln
    from sim.config import DieColor
    from sim.entities import Die

    rv.install_invariant_checks()
    if getattr(vuln, "_lock_checks_installed", False):
        return
    vuln._lock_checks_installed = True
    orig_roll, orig_lock_in = Die.roll, vuln.lock_in

    def roll(self, rng):  # INV-LOCK-01
        if p1._ROLL_CTX["in_reroll"]:
            assert not self.is_locked or p1._ROLL_CTX["helix_active"], "INV-LOCK-01: a locked die was rerolled"
        return orig_roll(self, rng)

    def lock_in(engine, p, active_dice):  # INV-LOCK-02 / -04
        cfg = engine.config
        if getattr(cfg, "colored_vuln_lock", False):
            for d in active_dice:
                if vuln.lock_applies(cfg, d):
                    assert d.is_locked, "INV-LOCK-02: a lockable ⚠ die is not locked at Deploy"
                if d.color in (DieColor.GRAY, DieColor.WHITE) and d.is_locked:
                    assert d.current_face is not None and d.current_face.is_glitch, "INV-LOCK-02: Gray/White ⚠-locked"
        return orig_lock_in(engine, p, active_dice)

    Die.roll, vuln.lock_in = roll, lock_in


def check_game(eng: Any) -> None:
    """INV-LOCK-03 / -05 / -06 after a game."""
    cfg = eng.config
    if not getattr(cfg, "colored_vuln_lock", False):
        return
    for p in eng.state.players:
        for zone in (p.ready_for_release_dice, p.contractor_dice, p.in_production_dice, p.glitched_dice):
            assert not any(d.is_locked for d in zone), "INV-LOCK-03: a die left Phase 1 locked"
        if getattr(cfg, "helix_bypass_once_per_game", False):
            assert p.helix_bypass_uses + p.helix_bypass_lost_to_black <= 1, "INV-LOCK-05/06: bypass used more than once"
        assert not p.helix_bypass_active, "INV-LOCK-05: bypass window left open"


# --------------------------------------------------------------------------------------------------
# One game: the v0.46 record plus the v0.47 seat telemetry
# --------------------------------------------------------------------------------------------------
def play(task: Tuple[str, str, int, int, Dict[str, Any], bool]) -> Dict[str, Any]:
    config_name, roster, players, seed, overrides, check = task
    if check and config_name.startswith("v046_locked"):
        install_lock_checks()
    holder: List[Any] = []
    orig = rv.build_engine

    def capture(cn, ro, pl, sd, ov):
        eng = orig(cn, ro, pl, sd, resolve_overrides(cn, ov))
        holder.append(eng)
        return eng

    rv.build_engine = capture
    try:
        rec = rv.play((config_name, roster, players, seed, overrides, check))
    finally:
        rv.build_engine = orig
    eng = holder[0]
    if check:
        check_game(eng)
    by_pid = {p.player_id: p for p in eng.state.players}
    for s in rec["seats"]:
        p = by_pid[s["seat"]]
        s.update({
            "company_color": (p.company_color or "none"),
            "wh": getattr(getattr(p.white_hat, "code", None), "value", None),
            "purchases": dict(p.purchases_by_color), "release_level": p.release_level,
            "l4_gray_sets": int(p.l4_payouts.get("release_gray_face_sets", 0)),
            "lock_dice": sum(p.lock_dice_by_round.values()), "lock_events": p.lock_events,
            "locked_kept_by_face": dict(p.locked_vuln_kept_by_face), "kept_by_source": dict(p.vuln_kept_by_source),
            "kept_by_color": dict(p.vuln_kept_by_color), "rolled_by_color": dict(p.colored_dice_rolled_by_color),
            "star_by_color": dict(p.colored_star_by_color), "declined": dict(p.lock_declined_rerolls),
            "ace_breaks": p.ace_lock_breaks, "helix_uses": p.helix_bypass_uses, "helix_log": list(p.helix_bypass_use_log),
            "helix_rerolled": p.helix_bypass_locked_rerolled, "helix_removed": p.helix_bypass_vuln_removed,
            "helix_black": p.helix_bypass_lost_to_black, "player_rounds": len(p.vuln_by_round),
        })
    return rec


def play_all(config_name: str, roster: str, players: int, games: int, seed0: int, overrides: Dict[str, Any],
             procs: int, check: bool) -> List[Dict[str, Any]]:
    tasks = [(config_name, roster, players, s, overrides, check) for s in range(seed0, seed0 + games)]
    if procs <= 1:
        return [play(t) for t in tasks]
    from multiprocessing import Pool

    with Pool(procs) as pool:
        return pool.map(play, tasks, chunksize=max(1, len(tasks) // (procs * 8)))


# --------------------------------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------------------------------
def _sum_dicts(dicts: List[Dict[str, Any]]) -> Dict[str, float]:
    out: Dict[str, float] = defaultdict(float)
    for d in dicts:
        for k, v in d.items():
            out[k] += v
    return dict(out)


def _ratio(a: float, b: float) -> Optional[float]:
    return None if not b else a / b


def win_by(seats: List[Dict[str, Any]], pred: Callable[[Dict[str, Any]], bool]) -> Optional[float]:
    sel = [s for s in seats if pred(s)]
    return None if not sel else 100.0 * sum(s["win"] for s in sel) / len(sel)


def colour_parity(seats: List[Dict[str, Any]]) -> Dict[str, Any]:
    """§8.3: per-colour win rates (a) by Client Company die colour, (b) purchased >= 1, (c) purchase-weighted."""
    out: Dict[str, Any] = {}
    for c in COLORS:
        n_c = sum(s["purchases"].get(c, 0) for s in seats)
        out[c] = {
            "a_company": win_by(seats, lambda s, c=c: s["company_color"] == c),
            "b_bought": win_by(seats, lambda s, c=c: s["purchases"].get(c, 0) >= 1),
            "c_weighted": (100.0 * sum(s["win"] * s["purchases"].get(c, 0) for s in seats) / n_c) if n_c else None,
        }
    for key in ("a_company", "b_bought", "c_weighted"):
        vals = [out[c][key] for c in COLORS if out[c][key] is not None]
        mean = sum(vals) / len(vals) if vals else None
        for c in COLORS:
            v = out[c][key]
            out[c][key + "_flag"] = None if (v is None or mean is None) else abs(v - mean) > 5.0  # OQ-4
    return out


def metrics47(recs: List[Dict[str, Any]], players: int) -> Dict[str, Any]:
    m = rv.metrics(recs, players)
    seats = [s for r in recs for s in r["seats"]]
    games = len(recs)
    pr = sum(s["player_rounds"] for s in seats)
    rolled = _sum_dicts([s["rolled_by_color"] for s in seats])
    stars = _sum_dicts([s["star_by_color"] for s in seats])
    by_face = _sum_dicts([s["locked_kept_by_face"] for s in seats])
    kept_color = _sum_dicts([s["kept_by_color"] for s in seats])
    kept_src = _sum_dicts([s["kept_by_source"] for s in seats])
    declined = _sum_dicts([s["declined"] for s in seats])
    helix = [s for s in seats if s["company"] == "HELIX"]
    log = [e for s in helix for e in s["helix_log"]]
    col_rolled = sum(rolled.values())
    m.update({
        "locks_per_player_round": _ratio(sum(s["lock_dice"] for s in seats), pr),
        "locked_vuln_by_face_per_die": {k: _ratio(v, rolled.get(k.split(":")[0], 0)) for k, v in sorted(by_face.items())},
        "kept_vuln_per_die_by_color": {c: _ratio(kept_color.get(c, 0), rolled.get(c, 0)) for c in LOCKABLE},
        "kept_vuln_per_player_round_by_source": {k: _ratio(v, pr) for k, v in sorted(kept_src.items())},
        "p_star_per_colored_die": _ratio(sum(stars.values()), col_rolled),
        "p_star_by_color": {c: _ratio(stars.get(c, 0), rolled.get(c, 0)) for c in LOCKABLE},
        "ace_lock_breaks_per_game": _ratio(sum(s["ace_breaks"] for s in seats), games),
        "helix_locked_rerolled_per_game": _ratio(sum(s["helix_rerolled"] for s in seats), games),
        "declined_per_player_round": {k: _ratio(v, pr) for k, v in sorted(declined.items())},
        "helix_seats": len(helix),
        "helix_use_share_pct": None if not helix else 100.0 * sum(1 for s in helix if s["helix_uses"]) / len(helix),
        "helix_lost_to_black_pct": None if not helix else 100.0 * sum(1 for s in helix if s["helix_black"]) / len(helix),
        "helix_round_hist": dict(sorted(Counter(e["round"] for e in log).items())),
        "helix_mean_vuln_removed": None if not any(s["helix_uses"] for s in helix) else
        sum(s["helix_removed"] for s in helix) / sum(1 for s in helix if s["helix_uses"]),
        "helix_win_pct": win_by(seats, lambda s: s["company"] == "HELIX"),
        "prodigy_win_pct": win_by(seats, lambda s: s["wh"] == "PRODIGY"),
        "operator_win_pct": win_by(seats, lambda s: s["wh"] == "OPERATOR"),
        "white_hat_win_pct": {w: win_by(seats, lambda s, w=w: s["wh"] == w) for w in sorted({s["wh"] for s in seats if s["wh"]})},
        "colour_parity": colour_parity(seats),
        "colored_dice_bought_per_game": _ratio(sum(s["purchases"].get(c, 0) for s in seats for c in COLORS), games),
        "release_l4_pct": None if not seats else 100.0 * sum(1 for s in seats if s["release_level"] >= 4) / len(seats),
        "l4_gray_sets_per_game": _ratio(sum(s["l4_gray_sets"] for s in seats), games),
        "end_secrets": _ratio(sum(s["secrets"] for s in seats), len(seats)),
    })
    return m


def f(v: Any, nd: int = 2) -> str:
    return "n/a" if v is None else (f"{v:.{nd}f}" if isinstance(v, (int, float)) else str(v))


# --------------------------------------------------------------------------------------------------
# Paired bootstrap CIs (v0.47 - v0.46 on the same seeds)
# --------------------------------------------------------------------------------------------------
def _num_den(rec: Dict[str, Any], key: str) -> Tuple[float, float]:
    seats = rec["seats"]
    adaptive = [s for s in seats if s["stance"] == "ADAPTIVE"]
    if key == "rounds":
        return rec["rounds"], 1
    if key == "patient_zero":
        return 100.0 * (rec["end"] == "patient_zero"), 1
    if key == "total_wipeout":
        return 100.0 * rec["wipeout"], 1
    if key == "market_collapse":
        return 100.0 * (rec["end"] == "market_collapse"), 1
    if key == "green_lost":
        return sum(s["green_lost"] for s in adaptive), len(adaptive)
    if key == "pen_steps":
        return sum(s["pen_steps"] for s in seats), len(seats)
    if key == "end_secrets":
        return sum(s["secrets"] for s in seats), len(seats)
    if key == "helix_win":
        h = [s for s in seats if s["company"] == "HELIX"]
        return 100.0 * sum(s["win"] for s in h), len(h)
    if key == "prodigy_win":
        h = [s for s in seats if s["wh"] == "PRODIGY"]
        return 100.0 * sum(s["win"] for s in h), len(h)
    if key == "operator_win":
        h = [s for s in seats if s["wh"] == "OPERATOR"]
        return 100.0 * sum(s["win"] for s in h), len(h)
    raise KeyError(key)


def paired_ci(a: List[Dict[str, Any]], b: List[Dict[str, Any]], key: str, n_boot: int = 400) -> Tuple[float, float, float]:
    """Ratio-estimator delta (a - b) with a 95% paired bootstrap CI over games (common seeds)."""
    nd_a = [_num_den(r, key) for r in a]
    nd_b = [_num_den(r, key) for r in b]
    n = min(len(nd_a), len(nd_b))

    def delta(idx: List[int]) -> Optional[float]:
        ra = _ratio(sum(nd_a[i][0] for i in idx), sum(nd_a[i][1] for i in idx))
        rb = _ratio(sum(nd_b[i][0] for i in idx), sum(nd_b[i][1] for i in idx))
        return None if ra is None or rb is None else ra - rb

    full = delta(list(range(n)))
    rng = random.Random(20261119)
    ds = sorted(d for d in (delta([rng.randrange(n) for _ in range(n)]) for _ in range(n_boot)) if d is not None)
    if full is None or not ds:
        return (float("nan"),) * 3
    return full, ds[int(0.025 * len(ds))], ds[min(len(ds) - 1, int(0.975 * len(ds)))]


CI_KEYS = (("rounds", "rounds"), ("patient_zero", "Patient Zero %"), ("total_wipeout", "Total Wipeout %"),
           ("market_collapse", "Market Collapse %"), ("green_lost", "Green lost / player-game"),
           ("pen_steps", "Pen Test steps / player-game"), ("end_secrets", "end Secrets / player"),
           ("helix_win", "Helix win % (pp)"), ("prodigy_win", "Prodigy win % (pp)"), ("operator_win", "Operator win % (pp)"))


def print_ci_table(r47: List[Dict[str, Any]], r46: List[Dict[str, Any]]) -> Dict[str, Any]:
    print(f"  {'delta v0.47 - v0.46 (paired, 95% CI)':44}{'delta':>9}{'lo':>9}{'hi':>9}")
    out: Dict[str, Any] = {}
    for key, label in CI_KEYS:
        d, lo, hi = paired_ci(r47, r46, key)
        out[key] = [d, lo, hi]
        print(f"  {label:44}{f(d):>9}{f(lo):>9}{f(hi):>9}")
    return out


# --------------------------------------------------------------------------------------------------
# Guardrails (v0.46 section 8.2 set vs v0.45, plus the GD section 9 rows vs v0.46)
# --------------------------------------------------------------------------------------------------
def extra_guardrails(m47: Dict[str, Any], m46: Dict[str, Any]) -> List[Tuple[str, Any, str, Optional[bool]]]:
    rows: List[Tuple[str, Any, str, Optional[bool]]] = []

    def add(name, val, rule, ok):
        rows.append((name, None if val is None else round(val, 2) if isinstance(val, float) else val, rule,
                     None if val is None else bool(ok)))

    flags = [(c, k) for c, d in m47["colour_parity"].items() for k in ("a_company", "b_bought", "c_weighted")
             if d[k + "_flag"]]
    rows.append(("Per-colour win-rate parity (a/b/c)", ", ".join(f"{c}:{k[0]}" for c, k in flags) or "none",
                 "no colour > 5 pp from the colour mean (Yellow named)", not flags))
    h47, h46 = m47["helix_win_pct"], m46["helix_win_pct"]
    add(None if h47 is None else "Helix company win % vs v0.46", None if h47 is None or h46 is None else h47 - h46,
        ">= -2 pp", lambda_ok(lambda v: v >= -2))
    for key, label in (("prodigy_win_pct", "Prodigy win % vs v0.46"), ("operator_win_pct", "Operator win % vs v0.46")):
        a, b = m47[key], m46[key]
        add(label, None if a is None or b is None else a - b, "within +-3 pp", lambda_ok(lambda v: abs(v) <= 3))
    add("P(star) per colored die", m47["p_star_per_colored_die"], ">= 0.12", lambda_ok(lambda v: v >= 0.12))
    b47, b46 = m47["colored_dice_bought_per_game"], m46["colored_dice_bought_per_game"]
    add("Colored dice bought / game vs v0.46", None if not b46 else b47 / b46 - 1, ">= -10 %",
        lambda_ok(lambda v: v >= -0.10))
    rows.append(("Release L4 share % (report only)", None if m47["release_l4_pct"] is None else round(m47["release_l4_pct"], 1),
                 "report", None))
    return rows


def lambda_ok(fn: Callable[[float], bool]) -> Callable[[float], bool]:
    return fn


def print_guardrail_rows(rows: List[Tuple[str, Any, str, Optional[bool]]]) -> None:
    for name, val, rule, ok in rows:
        if name is None:
            continue
        print(f"  {name:42}{f(val) if not isinstance(val, str) else val:>12}  {rule:44}{'n/a' if ok is None else ('PASS' if ok else 'FAIL')}")


# --------------------------------------------------------------------------------------------------
# Printing
# --------------------------------------------------------------------------------------------------
def print_pod(title: str, m: Dict[str, Any]) -> None:
    keys = ("games", "rounds", "patient_zero_pct", "total_wipeout_pct", "market_collapse_pct", "green_lost_per_player_game",
            "pen_steps_per_player_game", "end_secrets", "green_no_target_pct")
    print(f"{title}: " + "  ".join(f"{k}={f(m.get(k))}" for k in keys))


def print_v047_tables(m: Dict[str, Any]) -> None:
    print(f"  locks / player-round {f(m['locks_per_player_round'], 3)}   P(star) per colored die {f(m['p_star_per_colored_die'], 3)}"
          f"   ACE lock-breaks / game {f(m['ace_lock_breaks_per_game'], 3)}   Helix locked-rerolls / game {f(m['helix_locked_rerolled_per_game'], 3)}")
    print("  locked ⚠ by face (per rolled die of that colour): " +
          "  ".join(f"{k}={f(v, 3)}" for k, v in m["locked_vuln_by_face_per_die"].items()))
    print("  kept ⚠ per die by colour: " + "  ".join(f"{c}={f(v, 3)}" for c, v in m["kept_vuln_per_die_by_color"].items()) +
          "   by source / player-round: " + "  ".join(f"{k}={f(v, 3)}" for k, v in m["kept_vuln_per_player_round_by_source"].items()))
    print("  declined rerolls / player-round: " + ("  ".join(f"{k}={f(v, 3)}" for k, v in m["declined_per_player_round"].items()) or "none"))
    print(f"  Helix: seats={m['helix_seats']} use%={f(m['helix_use_share_pct'], 1)} lost-to-Black%={f(m['helix_lost_to_black_pct'], 1)}"
          f" mean ⚠ removed={f(m['helix_mean_vuln_removed'])} win%={f(m['helix_win_pct'], 1)} round hist={m['helix_round_hist']}")
    print(f"  Prodigy win%={f(m['prodigy_win_pct'], 1)} Operator win%={f(m['operator_win_pct'], 1)}  all WH: " +
          " ".join(f"{k}={f(v, 1)}" for k, v in m["white_hat_win_pct"].items()))
    print(f"  colored dice bought / game {f(m['colored_dice_bought_per_game'])}  Release L4 {f(m['release_l4_pct'], 1)}%"
          f"  L4 Gray face-sets / game {f(m['l4_gray_sets_per_game'], 3)}")
    print("  per-colour win % (a company die / b bought>=1 / c purchase-weighted; * = flag > 5 pp from mean):")
    for c, d in m["colour_parity"].items():
        cell = lambda k: f"{f(d[k], 1)}{'*' if d[k + '_flag'] else ''}"  # noqa: E731
        print(f"    {c:7} a={cell('a_company'):>8} b={cell('b_bought'):>8} c={cell('c_weighted'):>8}")


def save(name: str, payload: Dict[str, Any]) -> str:
    path = tbl.resolve_out(name, "out.json", OUT_DIR)
    with open(path, "w") as fh:
        json.dump(payload, fh, default=str)
    return path


def precheck(m46: Dict[str, Any], players: int, games: int, seed0: int) -> bool:
    """FINDINGS §62 reproduction (only meaningful at the full 1,200-game size and seed0 42)."""
    i = {2: 0, 3: 1, 4: 2}[players]
    ok = True
    rows = []
    for k, vals in PRECHECK.items():
        v, ref = m46[k], vals[i]
        good = abs(v - ref) <= PRECHECK_TOL[k]
        ok &= good
        rows.append(f"{k}={f(v)} (ref {ref}, tol {PRECHECK_TOL[k]}) {'ok' if good else 'MISMATCH'}")
    full = games >= 1200 and seed0 == 42
    print(f"  pre-check v0.46 vs FINDINGS §62 ({players}P): " + "; ".join(rows) + ("" if full else "  [informational: not full size]"))
    return ok or not full


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--step", choices=("smoke", "main", "arm"), default="smoke")
    ap.add_argument("--arm", default=None)
    ap.add_argument("--list-arms", action="store_true")
    ap.add_argument("--games", type=int, default=None, help="per pod (defaults: smoke 300, main 1200, arm 1200)")
    ap.add_argument("--seed0", type=int, default=42)
    ap.add_argument("--players", default=None, help="comma list, e.g. 3 or 2,3,4")
    ap.add_argument("--roster", default="mixed1", choices=("mixed1", "archetypes"))
    ap.add_argument("--procs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--assert-invariants", action="store_true")
    ap.add_argument("--set", default=None, help="extra GameConfig overrides (JSON) applied to v046_locked_roster")
    ap.add_argument("--vuln-params", default=None,
                    help="VulnPolicyParams overrides (JSON), LAYERED onto the preset's params (not rebuilt from defaults)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--no-baseline", action="store_true", help="arm step: skip the v0.45 / v0.46 comparator runs")
    ap.add_argument("--verbose", action="store_true", help="keep per-game records in the JSON")
    ap.add_argument("--quiet", action="store_true", default=True, help="(default) summary only")
    a = ap.parse_args()
    if a.list_arms:
        print("\n".join(ARMS))
        return
    pods = [int(x) for x in a.players.split(",")] if a.players else [2, 3, 4]
    extra = parse_overrides(a.set, a.vuln_params)
    if a.step == "smoke":
        games = a.games or 300
        out: Dict[str, Any] = {"step": "smoke", "pods": {}}
        for pl in pods:
            recs = play_all(CONFIG, a.roster, pl, games, a.seed0, dict(extra), a.procs, True)
            m = metrics47(recs, pl)
            out["pods"][str(pl)] = {"metrics": m, "games": recs if a.verbose else None}
            print_pod(f"smoke {pl}P invariants OK", m)
            print_v047_tables(m)
        print("wrote", save(a.out or "smoke.json", out))
        return
    if a.step == "main":
        games = a.games or 1200
        out = {"step": "main", "pods": {}}
        for pl in pods:
            r45 = play_all("v045_roster", a.roster, pl, games, a.seed0, {}, a.procs, a.assert_invariants)
            r46 = play_all("v046_roster", a.roster, pl, games, a.seed0, {}, a.procs, a.assert_invariants)
            m45, m46 = metrics47(r45, pl), metrics47(r46, pl)
            print(f"\n== {pl}P, {games} games/pod (v0.45 vs v0.46 vs v0.47) ==")
            if not precheck(m46, pl, games, a.seed0):
                print("STOP: v0.46 does not reproduce FINDINGS §62; do not trust the v0.47 comparison.")
                print("wrote", save(a.out or "main_precheck_failed.json", {"step": "main", "precheck": "FAILED",
                                                                           "pods": out["pods"], "m46": m46}))
                sys.exit(2)
            r47 = play_all(CONFIG, a.roster, pl, games, a.seed0, dict(extra), a.procs, a.assert_invariants)
            m47 = metrics47(r47, pl)
            print_pod("v0.45", m45)
            print_pod("v0.46", m46)
            print_pod("v0.47", m47)
            print_v047_tables(m47)
            print("  guardrails (v0.46 section 8.2 set vs v0.45)")
            gr = rv.guardrails(m45, m47, pl)
            print(f"  {'guardrail':42}{'v0.47':>12}  {'rule':44}result")
            for name, val, rule, ok in gr:
                print(f"  {name:42}{f(val):>12}  {rule:44}{'n/a' if ok is None else ('PASS' if ok else 'FAIL')}")
            print("  GD section 9 rows vs v0.46")
            ex = extra_guardrails(m47, m46)
            print_guardrail_rows(ex)
            ci = print_ci_table(r47, r46)
            out["pods"][str(pl)] = {"v045": m45, "v046": m46, "v047": m47, "guardrails": gr, "extra_guardrails": ex,
                                    "ci_vs_v046": ci}
            if a.verbose:
                out["pods"][str(pl)]["games"] = r47
        print("wrote", save(a.out or "main.json", out))
        return
    if not a.arm or a.arm not in ARMS:
        ap.error(f"--arm must be one of {list(ARMS)}")
    games = a.games or 1200
    out = {"step": "arm", "arm": a.arm, "overrides": {k: str(v) for k, v in ARMS[a.arm].items()}, "pods": {}}
    for pl in pods:
        ov = {**ARMS[a.arm], **extra}
        if isinstance(ARMS[a.arm].get("vuln_bot_params"), dict) and isinstance(extra.get("vuln_bot_params"), dict):
            ov["vuln_bot_params"] = {**ARMS[a.arm]["vuln_bot_params"], **extra["vuln_bot_params"]}
        recs = play_all(CONFIG, a.roster, pl, games, a.seed0, ov, a.procs, a.assert_invariants)
        m = metrics47(recs, pl)
        print(f"\n== arm {a.arm}, {pl}P, {games} games ==")
        print_pod(f"arm {a.arm} {pl}P", m)
        print_v047_tables(m)
        out["pods"][str(pl)] = {"metrics": m}
        if not a.no_baseline:
            r45 = play_all("v045_roster", a.roster, pl, games, a.seed0, {}, a.procs, False)
            r46 = play_all("v046_roster", a.roster, pl, games, a.seed0, {}, a.procs, False)
            m45, m46 = metrics47(r45, pl), metrics47(r46, pl)
            gr = rv.guardrails(m45, m, pl)
            print(f"  {'guardrail':42}{'arm':>12}  {'rule':44}result")
            for name, val, rule, ok in gr:
                print(f"  {name:42}{f(val):>12}  {rule:44}{'n/a' if ok is None else ('PASS' if ok else 'FAIL')}")
            ex = extra_guardrails(m, m46)
            print_guardrail_rows(ex)
            ci = print_ci_table(recs, r46)
            out["pods"][str(pl)].update({"v045": m45, "v046": m46, "guardrails": gr, "extra_guardrails": ex, "ci_vs_v046": ci})
    print("wrote", save(a.out or f"arm_{a.arm}.json", out))


if __name__ == "__main__":
    main()
