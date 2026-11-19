"""v0.46.0 Step 3: strategy dominance matrix (spec §14.4, §13.4).

Focal {KeepAll, RerollAllVuln, Adaptive, PenTestRush, Kamikaze} x field {Adaptive, KeepAll, RerollAllVuln}; every
seat is an Adaptive Balanced instance whose ``vuln_strategy`` is set per the cell. 3P, 600 games per cell by default;
the Adaptive-field row is repeated at 2P and 4P. The focal seat is rotated (seed % players). Win share vs fair
(1 / players); Adaptive keep rate by round.

Dominance rule (plan §10.4): no fixed strategy beats an Adaptive field by more than +5 pp over fair share;
Adaptive reaches at least fair - 3 pp against every field; Adaptive keep rate 35-85%.

Usage:  python3 scripts/run_v046_dominance_matrix.py [--games 600] [--seed0 42] [--procs N] [--quick]
Output: sim_results/v046/dominance_matrix.json, tables on stdout (--quiet is the default).
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from typing import Any, Dict, List, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from sim.bots.adaptive_balanced import AdaptiveBalancedBot  # noqa: E402
from sim.config import GameConfig  # noqa: E402
from sim.engine import GameEngine  # noqa: E402
from scripts import v046_tables as tbl  # noqa: E402
from sim.entities import get_random_companies, get_random_setup, get_random_white_hats  # noqa: E402

FOCALS = ("KeepAll", "RerollAllVuln", "Adaptive", "PenTestRush", "Kamikaze")
FIELDS = ("Adaptive", "KeepAll", "RerollAllVuln")
STRATEGY = {"KeepAll": "KEEP_ALL", "RerollAllVuln": "REROLL_ALL", "Adaptive": "ADAPTIVE", "PenTestRush": "PEN_TEST_RUSH",
            "Kamikaze": "KAMIKAZE", "NoColorReroll": "NO_COLOR_REROLL", "StarChase": "STAR_CHASE"}
# v0.47 (--config v047_roster): the two lock-era stances join the focal set (spec §11.2)
FOCALS_V047 = ("KeepAll", "RerollAllVuln", "Adaptive", "NoColorReroll", "StarChase", "PenTestRush", "Kamikaze")
OUT = os.path.join(ROOT, "sim_results", "v046", "dominance_matrix.json")


def make_bot(seat: int, label: str) -> AdaptiveBalancedBot:
    b = AdaptiveBalancedBot(seat)
    b.vuln_strategy = STRATEGY[label]
    if label == "PenTestRush":
        b.research_focus_v036 = ("DEFENSE", "TRIAGE", "RELEASE", "PATENT")
    return b


def build_engine(players: int, seed: int, focal: str, field: str, overrides: Dict[str, Any],
                 config: str = "v046_roster") -> Tuple[GameEngine, int]:
    rng = random.Random(seed)
    seat = seed % players
    bots = [make_bot(i, focal if i == seat else field) for i in range(players)]
    variants, version_deck = get_random_setup(rng, profile="STANDARD")
    companies = get_random_companies(players, rng)
    white_hats = get_random_white_hats(players, rng)
    kw = dict(num_players=players, starting_money=6, starting_gray_dice=3, starting_purple_dice=1,
              starting_purple_reserve=1, corruption_track_profile="STANDARD", enable_corporate_asymmetry=True)
    kw.update(overrides)
    cfg = getattr(GameConfig, config)(**kw)
    return GameEngine(config=cfg, bots=bots, seed=seed, variant_cards=variants, version_deck=version_deck,
                      companies=companies, white_hats=white_hats), seat


def play(task: Tuple) -> Dict[str, Any]:
    players, seed, focal, field, overrides = task[:5]
    config = task[5] if len(task) > 5 else "v046_roster"
    eng, seat = build_engine(players, seed, focal, field, overrides, config)
    res = eng.run_game()
    nwin = max(1, len(res.winner_ids))
    p = eng.state.players[seat]
    return {"win": (1.0 / nwin) if seat in res.winner_ids else 0.0, "keep_by_round": dict(p.vuln_keep_by_round),
            "green_lost": p.green_secrets_lost,
            "levels": [p.defense_level, p.triage_level, p.release_level, p.patent_level],
            "keep": [p.vuln_keep_kept, p.vuln_keep_events], "pen_steps": p.pen_test_steps, "rounds": res.total_rounds,
            "seed": seed, "icons": p.vuln_icons_kept_total, "player_rounds": len(p.vuln_by_round),
            "stars": sum(p.colored_star_by_color.values()), "colored_rolled": sum(p.colored_dice_rolled_by_color.values())}


def run_cell(players: int, games: int, seed0: int, focal: str, field: str, procs: int,
             overrides: Dict[str, Any], config: str = "v046_roster") -> List[Dict[str, Any]]:
    tasks = [(players, s, focal, field, overrides, config) for s in range(seed0, seed0 + games)]
    if procs <= 1:
        return [play(t) for t in tasks]
    from multiprocessing import Pool

    with Pool(procs) as pool:
        return pool.map(play, tasks, chunksize=max(1, len(tasks) // (procs * 8)))


def paired_win_delta(focal: List[Dict[str, Any]], control: List[Dict[str, Any]], n_boot: int = 400) -> Tuple[float, float, float]:
    """Mean win-share delta in pp (focal - control, same seeds and seat) with a 95% paired bootstrap CI."""
    diffs = [100.0 * (f["win"] - c["win"]) for f, c in zip(focal, control)]
    n = len(diffs)
    mean = sum(diffs) / max(1, n)
    rng = random.Random(20261119)
    ms = sorted(sum(diffs[rng.randrange(n)] for _ in range(n)) / n for _ in range(n_boot)) if n else [0.0]
    return mean, ms[int(0.025 * len(ms))], ms[min(len(ms) - 1, int(0.975 * len(ms)))]


def cell_stats(recs: List[Dict[str, Any]], players: int) -> Dict[str, Any]:
    n = len(recs)
    win = sum(r["win"] for r in recs) / max(1, n)
    kept = sum(r["keep"][0] for r in recs)
    ev = sum(r["keep"][1] for r in recs)
    by_round: Dict[int, List[int]] = defaultdict(lambda: [0, 0])
    for r in recs:
        for k, (a, b) in r["keep_by_round"].items():
            by_round[int(k)][0] += a
            by_round[int(k)][1] += b
    return {"games": n, "win": win, "green_lost": sum(r["green_lost"] for r in recs) / max(1, n),
            "levels": tbl._levels([{"levels": r["levels"]} for r in recs]),
            "vs_fair_pp": (win - 1.0 / players) * 100,
            "icons_per_player_round": (sum(r["icons"] for r in recs) / max(1, sum(r["player_rounds"] for r in recs))),
            "p_star": (sum(r["stars"] for r in recs) / sum(r["colored_rolled"] for r in recs)
                       if sum(r["colored_rolled"] for r in recs) else None),
            "keep_rate": (kept / ev) if ev else None, "pen_steps": sum(r["pen_steps"] for r in recs) / max(1, n),
            "keep_by_round": {k: (v[0] / v[1] if v[1] else None) for k, v in sorted(by_round.items())}}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--games", type=int, default=600, help="per cell (default 600)")
    ap.add_argument("--seed0", type=int, default=42)
    ap.add_argument("--procs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--config", default="v046_roster", help="preset name (v047_roster adds the NoColorReroll / StarChase focals)")
    ap.add_argument("--set", default=None, help='JSON GameConfig overrides, e.g. \'{"vuln_band_thresholds":[4,7,10]}\'')
    ap.add_argument("--vuln-params", default=None, help='VulnPolicyParams overrides (JSON), e.g. \'{"secret_value": 2.0}\'')
    ap.add_argument("--no-repeat-2p4p", action="store_true", help="skip the 2P / 4P Adaptive-field rows")
    ap.add_argument("--tables", choices=("full", "basic"), default="full",
                    help="full (default) adds win/Green-loss by strategy (item 3) and track-level reach by strategy (item 5)")
    ap.add_argument("--quiet", action="store_true", default=True, help="(default) summary only")
    a = ap.parse_args()
    overrides = tbl.coerce_overrides(json.loads(a.set)) if a.set else {}
    if a.vuln_params:
        import dataclasses

        # layered onto the preset's own params (not rebuilt from defaults)
        overrides["vuln_bot_params"] = dataclasses.replace(
            getattr(GameConfig, a.config)(num_players=3).vuln_bot_params, **json.loads(a.vuln_params))
    focals = FOCALS_V047 if a.config.startswith("v047") else FOCALS
    out: Dict[str, Any] = {"games": a.games, "seed0": a.seed0, "cells": {}}
    pods = [(3, FIELDS)] + ([] if a.no_repeat_2p4p else [(2, ("Adaptive",)), (4, ("Adaptive",))])
    for players, fields in pods:
        print(f"\n== {players}P, {a.games} games/cell: focal win share (pp vs fair {100 / players:.1f}) ==")
        print(f"{'focal':15}" + "".join(f"{f:>22}" for f in fields))
        cell_recs: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        for focal in focals:
            row = f"{focal:15}"
            for field in fields:
                cell_recs[(focal, field)] = run_cell(players, a.games, a.seed0, focal, field, a.procs, overrides, a.config)
                st = cell_stats(cell_recs[(focal, field)], players)
                out["cells"][f"{players}P|{focal}|{field}"] = st
                row += f"{st['win'] * 100:>14.1f}% ({st['vs_fair_pp']:+5.1f})"
            print(row)
        for field in fields:
            for focal in focals:
                st = out["cells"][f"{players}P|{focal}|{field}"]
                if focal != "Adaptive" and field == "Adaptive":
                    flag = "FAIL (dominates > +5 pp)" if st["vs_fair_pp"] > 5 else "ok"
                    print(f"  dominance {focal:14} vs Adaptive field: {st['vs_fair_pp']:+5.1f} pp  {flag}")
                    if a.config.startswith("v047"):
                        # spec §11.2: flag a focal policy beating the Adaptive control by > 3 pp with the paired 95% CI above 0
                        d, lo, hi = paired_win_delta(cell_recs[(focal, field)], cell_recs[("Adaptive", field)])
                        st["delta_vs_adaptive_pp"] = [d, lo, hi]
                        fl = "FLAG (> +3 pp, CI > 0)" if (d > 3 and lo > 0) else "ok"
                        ps = st["p_star"]
                        print(f"    vs Adaptive control (paired): {d:+5.1f} pp [{lo:+5.1f}, {hi:+5.1f}]  {fl}  "
                              f"⚠ kept/player-round {st['icons_per_player_round']:.2f}  P(★) {'n/a' if ps is None else f'{ps:.3f}'}")
            ad = out["cells"][f"{players}P|Adaptive|{field}"]
            print(f"  Adaptive vs {field:14} field: {ad['vs_fair_pp']:+5.1f} pp  {'ok' if ad['vs_fair_pp'] >= -3 else 'FAIL (< fair - 3 pp)'}")
        ad = out["cells"][f"{players}P|Adaptive|Adaptive"]
        kr = ad["keep_rate"]
        print(f"  Adaptive keep rate (Adaptive field): {'n/a' if kr is None else f'{kr * 100:.1f}%'}  "
              f"{'ok' if kr is not None and 0.35 <= kr <= 0.85 else 'OUT OF 35-85% BAND'}")
        print("  by round: " + " ".join(f"r{k}={'-' if v is None else f'{v * 100:.0f}%'}" for k, v in ad["keep_by_round"].items()))
        if a.tables == "full":
            summ: Dict[str, Any] = {}
            for field in fields:
                as_games = [{"seats": [{"label": focal, "win": r["win"], "green_lost": r["green_lost"], "levels": r["levels"]}
                                       for focal in focals for r in cell_recs[(focal, field)]]}]
                summ[f"strategy|{field}"] = tbl.t_strategy(as_games, players, f"({players}P, focal seat vs {field} field) ")
            groups = {f"{focal} (vs Adaptive field)": [{"levels": r["levels"]} for r in cell_recs[(focal, "Adaptive")]]
                      for focal in focals}
            summ["levels|Adaptive"] = tbl.t_levels(groups, f"({players}P, focal seat)")
            out.setdefault("summary", {})[f"{players}P"] = summ
    out_path = tbl.resolve_out(a.out, "dominance_matrix.json", os.path.dirname(OUT))
    with open(out_path, "w") as fh:
        json.dump(out, fh)
    print("wrote", out_path)


if __name__ == "__main__":
    main()
