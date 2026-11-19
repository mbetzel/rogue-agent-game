"""Shared per-game collection and stdout summary tables for the v0.46.0 sweep scripts (tooling only).

``collect_game`` turns one finished engine into a compact record (seat rows, Green stats by version, version-track
diagnostics). The ``t_*`` functions aggregate records into tables, print them and return a JSON-friendly dict
(the ``summary`` block). Nothing here changes engine behaviour: Block-face counting wraps
``phase3_income.execute_player_income`` read-only.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

VERS = ("v1.0", "v2.0", "v3.0")
STRAT = {"ADAPTIVE": "Adaptive", "KEEP_ALL": "KeepAll", "REROLL_ALL": "RerollAllVuln", "KAMIKAZE": "Kamikaze",
         "PEN_TEST_RUSH": "PenTestRush"}
TRACKS = ("pen_test_or_defense", "triage", "release", "pr")
TRACK_LABEL = {"pen_test_or_defense": "Pen Test (v0.45: Defense Grid)", "triage": "Triage", "release": "Release",
               "pr": "Public Relations"}
LEDGER_COLS = ("start", "face_red", "face_blue", "face_green", "face_purple", "mlb_in_game", "mlb_end", "blue_F1_face",
               "cards", "breakthrough", "blue_loss", "green_loss", "other")  # mlb = Market Leader Bonus (Red payout)


# --------------------------------------------------------------------------------------------------
# CLI helpers shared by the sweep scripts
# --------------------------------------------------------------------------------------------------
def coerce_overrides(d: Dict[str, Any]) -> Dict[str, Any]:
    """JSON -> GameConfig overrides: lists become tuples, and dicts with digit-string keys get int keys
    (e.g. ``{"market_share_start_by_player_count": {"2": 13, "3": 16, "4": 16}}``, ``share_regain_cost_by_level``)."""
    out: Dict[str, Any] = {}
    for k, v in d.items():
        if isinstance(v, list):
            v = tuple(v)
        elif isinstance(v, dict) and v and all(str(x).lstrip("-").isdigit() for x in v):
            v = {int(x): y for x, y in v.items()}
        out[k] = v
    return out


def resolve_out(path: Optional[str], default_name: str, out_dir: str) -> str:
    """``--out`` may be a bare file name (-> ``out_dir``), a relative path (cwd) or an absolute path; never double-prefixed."""
    import os

    p = path or default_name
    if os.path.isabs(p) or os.path.dirname(p):
        full = os.path.abspath(p)
    else:
        full = os.path.join(out_dir, p)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    return full


# --------------------------------------------------------------------------------------------------
# Collection
# --------------------------------------------------------------------------------------------------
def install_block_probe() -> None:
    """Counts final Block faces among the dice In Production at the start of each player's Phase 3 (read-only)."""
    from sim.engine import phase3_income

    if getattr(phase3_income, "_tbl_probe", False):
        return
    orig = phase3_income.execute_player_income

    def wrapped(engine, player, *a, **k):
        acc = engine.__dict__.setdefault("_tbl_block", defaultdict(Counter))
        for d in player.in_production_dice:
            f = d.effective_face or d.current_face
            acc[player.player_id][f"{d.color.value}_rolls"] += 1
            if f is not None and f.is_shield:
                acc[player.player_id][f"{d.color.value}_block"] += 1
        return orig(engine, player, *a, **k)

    phase3_income.execute_player_income = wrapped
    phase3_income._tbl_probe = True


def _ledger(src: Dict[str, int]) -> Dict[str, int]:
    out: Counter = Counter()
    for k, v in src.items():
        if k == "starting":
            b = "start"
        elif k.startswith("secret_face_") and k != "secret_face_":
            c = k[len("secret_face_"):]
            b = f"face_{c}" if f"face_{c}" in LEDGER_COLS else "other"
        elif k == "red_secret_payout":
            b = "mlb_in_game"
        elif k in ("red_secret_payout_end", "market_leader_bonus"):
            b = "mlb_end"
        elif k in ("blue_face", "face"):
            b = "blue_F1_face"
        elif k in ("y1", "y3", "b2") and v > 0:
            b = "cards"
        elif k == "breakthrough":
            b = "breakthrough"
        elif k == "blue_damage":
            b = "blue_loss"
        elif k in ("green_vulnerability", "defense_grid_overflow"):
            b = "green_loss"
        else:
            b = "other"
        out[b] += v
    return dict(out)


def collect_game(eng: Any, res: Any, label_of=None) -> Dict[str, Any]:
    """One finished game -> record. ``label_of(player)`` names the seat's strategy (default: stance / Mixed)."""
    s = eng.state
    cfg = eng.config
    vuln_on = cfg.is_vulnerability
    by_pid = {r["player_id"]: r for r in res.rankings}
    nwin = max(1, len(res.winner_ids))
    ver_of = {c.name: c.version_str for c in s.version_deck}
    inc_m: Counter = Counter()
    inc_r: Counter = Counter()
    inc_n: Counter = Counter()
    gv: Dict[str, Dict[str, Any]] = {v: {"rounds": 0, "cubes": 0, "no_target": 0, "cubes_hit": 0, "player_hits": 0,
                                         "dmg": Counter(), "overflow": 0, "black_exit": 0, "black_staged": 0,
                                         "track_delta": 0, "track_end": 0, "non_entry_rounds": 0,
                                         "black_exit_ne": 0} for v in VERS}
    entry: Dict[str, int] = {}
    prev_track = 0
    prev_ver = None
    for t in res.telemetry_history:
        v = ver_of.get(t.active_version_name, "v1.0")
        entry.setdefault(v, t.round_number)
        g = gv[v]
        g["rounds"] += 1
        g["cubes"] += t.green_cubes_resolved
        g["no_target"] += t.green_cubes_no_target
        for ev in t.green_hit_events:
            if ev["pids"]:
                g["cubes_hit"] += 1
                g["player_hits"] += len(ev["pids"])
                g["dmg"][ev["damage"]] += len(ev["pids"])
        g["overflow"] += int(bool(t.buffer_overflow))
        g["black_exit"] += int(t.exited_cubes.get(_black(), 0))
        g["black_staged"] += int(t.staged_cubes.get(_black(), 0))
        if prev_ver == v:  # non-entry round: the track did not reset, so the delta is a real advance
            g["track_delta"] += t.corruption_track - prev_track
            g["non_entry_rounds"] += 1
            g["black_exit_ne"] += int(t.exited_cubes.get(_black(), 0))
        g["track_end"] = t.corruption_track
        prev_track, prev_ver = t.corruption_track, v
        for pid, inc in t.income_by_player.items():
            inc_m[pid] += inc["money"]
            inc_r[pid] += inc["research"]
            inc_n[pid] += 1
    blk = getattr(eng, "_tbl_block", {})
    seats = []
    for p in s.players:
        r = by_pid[p.player_id]
        b = blk.get(p.player_id, Counter())
        lab = label_of(p) if label_of else ("Mixed" if p.bot.name == "MixedPolicyBot"
                                            else STRAT.get(p.vuln_stance_this_round, p.vuln_stance_this_round))
        seats.append({
            "seat": p.player_id, "label": lab, "company": r.get("company_code"), "colour": r.get("company_color"),
            "win": (1.0 / nwin) if p.player_id in res.winner_ids else 0.0,
            "green_lost": p.green_secrets_lost if vuln_on else p.secrets_lost_to_overflow,
            "income": [inc_m[p.player_id], inc_r[p.player_id], inc_n[p.player_id]],
            "blocks": dict(b), "ledger": _ledger(r["secrets_by_source"]),
            "levels": [p.defense_level, p.triage_level, p.release_level, p.patent_level],
            "keep_face": {k: list(v) for k, v in p.vuln_keep_by_face.items()},
        })
    return {"seats": seats, "green_by_ver": {v: {**g, "dmg": dict(g["dmg"])} for v, g in gv.items()},
            "ver_entry": entry, "end": res.end_reason.value, "rounds": res.total_rounds,
            "buffer_overflows": sum(int(bool(t.buffer_overflow)) for t in res.telemetry_history)}


def _black():
    from sim.config import CubeColor

    return CubeColor.BLACK


# --------------------------------------------------------------------------------------------------
# Aggregation helpers
# --------------------------------------------------------------------------------------------------
def _seats(recs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [x for r in recs for x in r["seats"]]


def _f(v: Optional[float], nd: int = 2) -> str:
    return "n/a" if v is None else f"{v:.{nd}f}"


def _div(a: float, b: float) -> Optional[float]:
    return None if not b else a / b


def _hdr(title: str) -> None:
    print(f"\n-- {title}")


# 1. Income, two ways --------------------------------------------------------------------------------
def t_income(r45: List[Dict[str, Any]], r46: List[Dict[str, Any]]) -> Dict[str, Any]:
    def agg(recs):
        ss = _seats(recs)
        n = sum(x["income"][2] for x in ss)
        m, rs = sum(x["income"][0] for x in ss), sum(x["income"][1] for x in ss)
        blocks = sum(v for x in ss for k, v in x["blocks"].items() if k.endswith("_block"))
        gray_b = sum(x["blocks"].get("gray_block", 0) for x in ss)
        gray_r = sum(x["blocks"].get("gray_rolls", 0) for x in ss)
        pur_b = sum(x["blocks"].get("purple_block", 0) for x in ss)
        pur_r = sum(x["blocks"].get("purple_rolls", 0) for x in ss)
        return {"money": _div(m, n), "research": _div(rs, n), "liquid": _div(m + rs, n), "block_rolls": _div(blocks, n),
                "liquid_plus_blocks": _div(m + rs + blocks, n), "gray_block_rate": _div(gray_b, gray_r),
                "purple_block_rate": _div(pur_b, pur_r), "player_rounds": n}

    a, b = agg(r45), agg(r46)
    _hdr("1. Income per player-round (Phase 3 income record; Block-face roll = 1 unit in the adjusted rows)")
    print(f"{'':34}{'v0.45':>9}{'v0.46':>9}{'v0.46/v0.45':>13}")
    for key, lab in (("money", "$ per player-round"), ("research", "🔬 per player-round"),
                     ("liquid", "(a) liquid $ + 🔬"), ("block_rolls", "Block-face rolls per player-round"),
                     ("liquid_plus_blocks", "(b) liquid + Block rolls as 1 unit")):
        ratio = _div(b[key], a[key]) if a[key] else None
        print(f"{lab:34}{_f(a[key]):>9}{_f(b[key]):>9}{_f(ratio):>13}")
    print(f"  v0.45 Block-face share of final faces: Gray {_f(100 * a['gray_block_rate'] if a['gray_block_rate'] is not None else None, 1)}%"
          f"  Purple {_f(100 * a['purple_block_rate'] if a['purple_block_rate'] is not None else None, 1)}%")
    return {"v045": a, "v046": b}


# 2. Company / colour --------------------------------------------------------------------------------
def t_company_colour(r45: List[Dict[str, Any]], r46: List[Dict[str, Any]], players: int) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key, title in (("company", "Company"), ("colour", "Company colour")):
        def agg(recs):
            d: Dict[str, List[float]] = defaultdict(list)
            for x in _seats(recs):
                d[str(x[key])].append(x["win"])
            return {k: (len(v), sum(v) / len(v)) for k, v in d.items()}

        a, b = agg(r45), agg(r46)
        _hdr(f"2. Win rate by {title.lower()} ({players}P; fair {100 / players:.1f}%)")
        print(f"{title:14}{'seats45':>9}{'win%45':>9}{'seats46':>9}{'win%46':>9}")
        for k in sorted(set(a) | set(b)):
            n1, w1 = a.get(k, (0, None))
            n2, w2 = b.get(k, (0, None))
            print(f"{k:14}{n1:>9}{_f(None if w1 is None else 100 * w1, 1):>9}{n2:>9}{_f(None if w2 is None else 100 * w2, 1):>9}")
        sp = lambda d: (max(v[1] for v in d.values()) - min(v[1] for v in d.values())) * 100 if d else None  # noqa: E731
        print(f"{'spread pp':14}{'':>9}{_f(sp(a), 1):>9}{'':>9}{_f(sp(b), 1):>9}")
        out[key] = {"v045": a, "v046": b}
    return out


# 3. Strategy / stance --------------------------------------------------------------------------------
def t_strategy(recs: List[Dict[str, Any]], players: int, title: str = "") -> Dict[str, Any]:
    d: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for x in _seats(recs):
        d[x["label"]].append(x)
    _hdr(f"3. Win rate and Green loss by strategy {title}(fair {100 / players:.1f}%)")
    print(f"{'strategy':16}{'seats':>7}{'win%':>8}{'vs fair pp':>12}{'green loss / player-game':>26}")
    out = {}
    for lab in sorted(d):
        v = d[lab]
        w = sum(x["win"] for x in v) / len(v)
        gl = sum(x["green_lost"] for x in v) / len(v)
        out[lab] = {"seats": len(v), "win": w, "vs_fair_pp": (w - 1 / players) * 100, "green_lost": gl}
        print(f"{lab:16}{len(v):>7}{100 * w:>8.1f}{(w - 1 / players) * 100:>+12.1f}{gl:>26.2f}")
    return out


# 4. Secret ledger ------------------------------------------------------------------------------------
def t_ledger(r45: List[Dict[str, Any]], r46: List[Dict[str, Any]]) -> Dict[str, Any]:
    def agg(recs):
        ss = _seats(recs)
        n = max(1, len(ss))
        return {c: sum(x["ledger"].get(c, 0) for x in ss) / n for c in LEDGER_COLS}

    a, b = agg(r45), agg(r46)
    _hdr("4. Secret ledger per player-game, by source (before end-game scoring comparison)")
    print(f"{'source':16}{'v0.45':>9}{'v0.46':>9}{'delta':>9}")
    for c in LEDGER_COLS:
        print(f"{c:16}{a[c]:>9.2f}{b[c]:>9.2f}{b[c] - a[c]:>+9.2f}")
    print(f"{'net':16}{sum(a.values()):>9.2f}{sum(b.values()):>9.2f}{sum(b.values()) - sum(a.values()):>+9.2f}")
    return {"v045": a, "v046": b}


# 5. Track levels -------------------------------------------------------------------------------------
def _levels(seats: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = max(1, len(seats))
    out: Dict[str, Any] = {"seats": len(seats)}
    for i, t in enumerate(TRACKS):
        out[t] = [sum(1 for x in seats if x["levels"][i] >= k) / n for k in (1, 2, 3, 4)]
    out["two_plus_l4"] = sum(1 for x in seats if sum(1 for lv in x["levels"] if lv >= 4) >= 2) / n
    return out


def t_levels(groups: Dict[str, List[Dict[str, Any]]], title: str = "") -> Dict[str, Any]:
    """``groups``: label -> seat rows. One block per group."""
    _hdr(f"5. Track level reach (% of seats at level >= k at game end) {title}".rstrip())
    out = {}
    print(f"{'group / track':34}{'L1':>7}{'L2':>7}{'L3':>7}{'L4':>7}")
    for lab, seats in groups.items():
        lv = _levels(seats)
        out[lab] = lv
        print(f"[{lab}] seats {lv['seats']}  2+ L4 tracks: {100 * lv['two_plus_l4']:.1f}%")
        for t in TRACKS:
            print(f"  {TRACK_LABEL[t]:32}" + "".join(f"{100 * x:>7.1f}" for x in lv[t]))
    return out


# 6. Keep rate per warning face -----------------------------------------------------------------------
def _face_names(profile: str = "V046_VULN_NOPREMIUM") -> Dict[str, str]:  # names of the v0.46 default dice
    from sim.entities import DieColor, create_colored_die, create_gray_die

    names = {}
    for i, f in enumerate(create_gray_die(0, "V046_VULN").faces):
        names[f"gray:{i + 1}"] = f.name
    for c in (DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW, DieColor.PURPLE):
        for i, f in enumerate(create_colored_die(c, 0, face_profile=profile).faces):
            names[f"{c.value}:{i + 1}"] = f.name
    return names


def t_keep_faces(recs: List[Dict[str, Any]]) -> Dict[str, Any]:
    ss = _seats(recs)
    tot: Dict[str, List[int]] = defaultdict(lambda: [0, 0])
    for x in ss:
        for k, (kept, ev) in x["keep_face"].items():
            tot[k][0] += kept
            tot[k][1] += ev
    names = _face_names()
    _hdr("6. Keep rate per ⚠ face (decisions with rerolls left; every seat)")
    print(f"{'die:face':12}{'face':26}{'events/player-game':>20}{'keep %':>9}")
    out = {}
    for k in sorted(tot, key=lambda z: (z.split(":")[0], int(z.split(":")[1]))):
        kept, ev = tot[k]
        out[k] = {"events_per_player_game": ev / max(1, len(ss)), "keep_rate": _div(kept, ev)}
        print(f"{k:12}{names.get(k, '?'):26}{ev / max(1, len(ss)):>20.2f}{_f(None if not ev else 100 * kept / ev, 1):>9}")
    return out


# 7. Green resolution ---------------------------------------------------------------------------------
def t_green(recs: List[Dict[str, Any]], pod: str = "") -> Dict[str, Any]:
    tot = {v: {"rounds": 0, "cubes": 0, "no_target": 0, "cubes_hit": 0, "player_hits": 0, "dmg": Counter()} for v in VERS}
    for r in recs:
        for v, g in r["green_by_ver"].items():
            t = tot[v]
            for k in ("rounds", "cubes", "no_target", "cubes_hit", "player_hits"):
                t[k] += g[k]
            for d, n in g["dmg"].items():
                t["dmg"][int(d)] += n
    allv = {"rounds": 0, "cubes": 0, "no_target": 0, "cubes_hit": 0, "player_hits": 0, "dmg": Counter()}
    for t in tot.values():
        for k in ("rounds", "cubes", "no_target", "cubes_hit", "player_hits"):
            allv[k] += t[k]
        allv["dmg"].update(t["dmg"])
    _hdr(f"7. Green resolution {pod}".rstrip())
    print(f"{'version':9}{'rounds':>8}{'cubes/rd':>10}{'no-target%':>12}{'hit/cube':>10}{'dmg1':>7}{'dmg2':>7}{'dmg3':>7}{'avg dmg':>9}")
    out = {}
    for v, t in list(tot.items()) + [("all", allv)]:
        hits = sum(t["dmg"].values())
        dm = {d: _div(t["dmg"].get(d, 0), hits) for d in (1, 2, 3)}
        avg = _div(sum(d * n for d, n in t["dmg"].items()), hits)
        row = {"rounds": t["rounds"], "cubes_per_round": _div(t["cubes"], t["rounds"]),
               "no_target_pct": None if not t["cubes"] else 100 * t["no_target"] / t["cubes"],
               "players_hit_per_targeted_cube": _div(t["player_hits"], t["cubes_hit"]), "damage_share": dm, "avg_damage": avg}
        out[v] = row
        print(f"{v:9}{t['rounds']:>8}{_f(row['cubes_per_round']):>10}{_f(row['no_target_pct'], 1):>12}"
              f"{_f(row['players_hit_per_targeted_cube']):>10}"
              + "".join(f"{_f(None if dm[d] is None else 100 * dm[d], 0):>7}" for d in (1, 2, 3)) + f"{_f(avg):>9}")
    return out


# 8. Singularity / version track ----------------------------------------------------------------------
def t_singularity(r45: List[Dict[str, Any]], r46: List[Dict[str, Any]]) -> Dict[str, Any]:
    def agg(recs):
        n = max(1, len(recs))
        sing = [r for r in recs if r["end"] == "singularity"]
        out: Dict[str, Any] = {
            "games": len(recs), "singularity_pct": 100 * len(sing) / n,
            "singularity_round_mean": _div(sum(r["rounds"] for r in sing), len(sing)),
            "rounds_mean_all": sum(r["rounds"] for r in recs) / n,
            "rounds_mean_non_singularity": _div(sum(r["rounds"] for r in recs if r["end"] != "singularity"),
                                                len([r for r in recs if r["end"] != "singularity"])),
            "buffer_overflows_per_game": sum(r["buffer_overflows"] for r in recs) / n}
        for v in VERS:
            reach = [r for r in recs if v in r["ver_entry"]]
            out[v] = {
                "reached_pct": 100 * len(reach) / n,
                "entry_round_mean": _div(sum(r["ver_entry"][v] for r in reach), len(reach)),
                "rounds_in_version": _div(sum(r["green_by_ver"][v]["rounds"] for r in recs), max(1, len(reach))),
                "black_exit_per_round": _div(sum(r["green_by_ver"][v]["black_exit"] for r in recs),
                                             sum(r["green_by_ver"][v]["rounds"] for r in recs)),
                "black_staged_per_round": _div(sum(r["green_by_ver"][v]["black_staged"] for r in recs),
                                               sum(r["green_by_ver"][v]["rounds"] for r in recs)),
                # fixed: divide the non-entry delta by non-entry rounds (entry rounds are not advances)
                "track_advance_per_round": _div(sum(r["green_by_ver"][v]["track_delta"] for r in recs),
                                                sum(r["green_by_ver"][v]["non_entry_rounds"] for r in recs)),
                "black_exit_per_non_entry_round": _div(sum(r["green_by_ver"][v]["black_exit_ne"] for r in recs),
                                                       sum(r["green_by_ver"][v]["non_entry_rounds"] for r in recs)),
            }
        return out

    a, b = agg(r45), agg(r46)
    _hdr("8. Singularity diagnostics (version track advances on Black cubes exiting the tower each round)")
    print(f"{'':36}{'v0.45':>9}{'v0.46':>9}")
    for k, lab in (("singularity_pct", "Singularity endings %"), ("singularity_round_mean", "mean round of Singularity"),
                   ("rounds_mean_all", "mean rounds (all games)"),
                   ("rounds_mean_non_singularity", "mean rounds (non-Singularity)"),
                   ("buffer_overflows_per_game", "Compile Buffer Overflows / game")):
        print(f"{lab:36}{_f(a[k]):>9}{_f(b[k]):>9}")
    for v in VERS:
        for k, lab in (("reached_pct", "games reaching"), ("entry_round_mean", "mean entry round"),
                       ("rounds_in_version", "mean rounds spent in"), ("black_staged_per_round", "Black staged / round in"),
                       ("black_exit_per_round", "Black exited / round in"), ("black_exit_per_non_entry_round", "Black exited / non-entry rd in"),
                       ("track_advance_per_round", "track advance / non-entry rd in")):
            print(f"{lab + ' ' + v:36}{_f(a[v][k]):>9}{_f(b[v][k]):>9}")
    return {"v045": a, "v046": b}
