"""Monte Carlo Validation Sweep Runner: v0.44.0 Research Tracks & Capstones.

Compares Baseline (GameConfig.v043()) vs Candidate (GameConfig.v044())
across 4P, 3P, and 2P pods (1,200 games/pod/variant = 7,200 games total, seeds 42..1241).

Outputs:
- sim_results/v440_research_tracks/summary.json
- sim_results/v440_research_tracks/validation_report.md
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import multiprocessing as mp
import os
import random
import sys
import time
from typing import Any, Dict, List, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from sim.config import EndGameReason, GameConfig, V038_COMPANY_STARTING_COLORS
from sim.engine import GameEngine
from sim.entities import get_random_companies, get_random_setup, get_random_white_hats
from tests.fixtures.v035_parity.capture import _bot_classes

TRACKS = ("DEFENSE", "TRIAGE", "RELEASE", "PATENT")
TRACK_LABELS = {
    "DEFENSE": "Defense Grid",
    "TRIAGE": "Triage",
    "RELEASE": "Release",
    "PATENT": "Public Relations",
}
COMPANY_DISPLAY = {
    "MERIDIAN": "Meridian",
    "OMNIDYNE": "Omnidyne",
    "AEGIS": "Aegis",
    "DTO": "DTO",
    "HELIX": "Helix",
    "PROMETHEUS": "Prometheus",
}


def build_engine(config_name: str, players: int, seed: int) -> GameEngine:
    classes = _bot_classes()
    rng = random.Random(seed)
    bots = [classes[(seed * players + i) % len(classes)](i) for i in range(players)]
    rng.shuffle(bots)
    for i, b in enumerate(bots):
        b.player_id = i

    variants, version_deck = get_random_setup(rng, profile="STANDARD")
    companies = get_random_companies(players, rng)
    white_hats = get_random_white_hats(players, rng)

    kw = dict(
        num_players=players,
        starting_money=6,
        starting_gray_dice=3,
        starting_purple_dice=1,
        starting_purple_reserve=1,
        corruption_track_profile="STANDARD",
        enable_corporate_asymmetry=True,
    )
    cfg = getattr(GameConfig, config_name)(**kw)
    return GameEngine(
        config=cfg,
        bots=bots,
        seed=seed,
        variant_cards=variants,
        version_deck=version_deck,
        companies=companies,
        white_hats=white_hats,
    )


def simulate_game(task: Tuple[str, int, int]) -> Dict[str, Any]:
    config_name, players, seed = task
    engine = build_engine(config_name, players, seed)
    res = engine.run_game()

    nwin = max(1, len(res.winner_ids))
    end_reason = res.end_reason.value if hasattr(res.end_reason, "value") else str(res.end_reason)

    player_records = []
    for p in engine.state.players:
        won = (1.0 / nwin) if p.player_id in res.winner_ids else 0.0
        c_code = getattr(p.company, "code", "") or "NONE"
        c_color = V038_COMPANY_STARTING_COLORS.get(c_code, "NONE")

        levels = {
            "DEFENSE": int(p.defense_level),
            "TRIAGE": int(p.triage_level),
            "RELEASE": int(p.release_level),
            "PATENT": int(p.patent_level),
        }
        l4_count = sum(1 for v in levels.values() if v >= 4)

        l4_payouts = dict(getattr(p, "l4_payouts", {}))
        triage_color = getattr(p, "triage_l4_upgrade_color", None)

        # Check PR L3 2nd Purple die breakthrough & whether it graduated from Scanned Box
        pr_l3_awarded = False
        pr_l3_graduated = False
        scanned_ids = {d.die_id for d in p.scanned_dice}
        for rec in getattr(p, "breakthroughs", []):
            if rec.track == "PATENT" and rec.level == 3 and rec.outcome != "FORFEITED":
                die_id = (rec.detail or {}).get("die_id")
                if die_id is not None:
                    pr_l3_awarded = True
                    if die_id not in scanned_ids:
                        pr_l3_graduated = True

        player_records.append({
            "archetype": p.bot.name,
            "company": c_code,
            "company_color": c_color,
            "won": won,
            "levels": levels,
            "l4_count": l4_count,
            "defense_cash": int(l4_payouts.get("defense_cash", 0)),
            "release_gray_face_sets": int(l4_payouts.get("release_gray_face_sets", 0)),
            "release_rerolls_used": int(l4_payouts.get("release_rerolls_used", 0)),
            "pr_instant_market_share": int(l4_payouts.get("pr_instant_market_share", 0)),
            "triage_l4_upgrade_color": triage_color,
            "pr_l3_awarded": pr_l3_awarded,
            "pr_l3_graduated": pr_l3_graduated,
        })

    return {
        "config": config_name,
        "players": players,
        "seed": seed,
        "rounds": int(res.total_rounds),
        "end_reason": end_reason,
        "total_wipeout": bool(res.is_total_wipeout),
        "player_records": player_records,
    }


def aggregate_pod(games: List[Dict[str, Any]]) -> Dict[str, Any]:
    n_games = len(games)
    rounds_list = sorted(g["rounds"] for g in games)
    mean_rounds = sum(rounds_list) / n_games
    median_rounds = rounds_list[n_games // 2]

    wipeouts = sum(1 for g in games if g["total_wipeout"])
    end_reasons = Counter(g["end_reason"] for g in games)

    early_wipeouts = [g["seed"] for g in games if g["total_wipeout"] and g["rounds"] <= 6]
    long_stalls = [g["seed"] for g in games if g["rounds"] >= 13]

    total_seats = 0
    track_level_sum = Counter()
    track_l1_plus = Counter()
    track_l2_plus = Counter()
    track_l3_plus = Counter()
    track_l4_seats = Counter()
    track_l4_games = Counter()
    seats_2plus_l4 = 0

    # v0.44.0 telemetry
    def_l4_cash_total = 0
    def_l4_seats = 0
    rel_gray_sets_total = 0
    rel_gray_sets_seats_used = 0
    rel_l4_seats = 0
    rel_rerolls_total = 0
    pr_l4_ms_total = 0
    pr_l4_full_2_seats = 0
    pr_l4_seats = 0
    tri_l4_seats = 0
    tri_l4_replacements = 0
    tri_l4_colors = Counter()
    pr_l3_awarded_count = 0
    pr_l3_graduated_count = 0

    arch_games = Counter()
    arch_wins = defaultdict(float)
    comp_games = Counter()
    comp_wins = defaultdict(float)

    for g in games:
        game_l4_seen = set()
        for pr in g["player_records"]:
            total_seats += 1
            arch = pr["archetype"]
            comp = pr["company"]
            arch_games[arch] += 1
            arch_wins[arch] += pr["won"]
            comp_games[comp] += 1
            comp_wins[comp] += pr["won"]

            if pr["l4_count"] >= 2:
                seats_2plus_l4 += 1

            for t in TRACKS:
                lvl = pr["levels"][t]
                track_level_sum[t] += lvl
                if lvl >= 1:
                    track_l1_plus[t] += 1
                if lvl >= 2:
                    track_l2_plus[t] += 1
                if lvl >= 3:
                    track_l3_plus[t] += 1
                if lvl >= 4:
                    track_l4_seats[t] += 1
                    game_l4_seen.add(t)

            if pr["levels"]["DEFENSE"] >= 4:
                def_l4_seats += 1
            def_l4_cash_total += pr["defense_cash"]

            if pr["levels"]["RELEASE"] >= 4:
                rel_l4_seats += 1
            rel_gray_sets_total += pr["release_gray_face_sets"]
            if pr["release_gray_face_sets"] > 0:
                rel_gray_sets_seats_used += 1
            rel_rerolls_total += pr["release_rerolls_used"]

            if pr["levels"]["PATENT"] >= 4:
                pr_l4_seats += 1
            pr_l4_ms_total += pr["pr_instant_market_share"]
            if pr["pr_instant_market_share"] >= 2:
                pr_l4_full_2_seats += 1

            if pr["levels"]["TRIAGE"] >= 4:
                tri_l4_seats += 1
            if pr["triage_l4_upgrade_color"]:
                tri_l4_replacements += 1
                tri_l4_colors[pr["triage_l4_upgrade_color"]] += 1

            if pr["pr_l3_awarded"]:
                pr_l3_awarded_count += 1
                if pr["pr_l3_graduated"]:
                    pr_l3_graduated_count += 1

        for t in game_l4_seen:
            track_l4_games[t] += 1

    return {
        "n_games": n_games,
        "n_seats": total_seats,
        "mean_rounds": round(mean_rounds, 3),
        "median_rounds": median_rounds,
        "min_rounds": rounds_list[0],
        "max_rounds": rounds_list[-1],
        "wipeout_count": wipeouts,
        "wipeout_rate": round(100.0 * wipeouts / n_games, 2),
        "end_reasons": {
            k: {"count": v, "pct": round(100.0 * v / n_games, 2)}
            for k, v in sorted(end_reasons.items())
        },
        "early_wipeout_seeds": early_wipeouts[:15],
        "early_wipeout_count": len(early_wipeouts),
        "long_stall_seeds": long_stalls[:15],
        "long_stall_count": len(long_stalls),
        "seats_2plus_l4_pct": round(100.0 * seats_2plus_l4 / total_seats, 2),
        "tracks": {
            t: {
                "mean_level": round(track_level_sum[t] / total_seats, 3),
                "l1_plus_pct": round(100.0 * track_l1_plus[t] / total_seats, 2),
                "l2_plus_pct": round(100.0 * track_l2_plus[t] / total_seats, 2),
                "l3_plus_pct": round(100.0 * track_l3_plus[t] / total_seats, 2),
                "l4_seat_pct": round(100.0 * track_l4_seats[t] / total_seats, 2),
                "l4_game_pct": round(100.0 * track_l4_games[t] / n_games, 2),
                "l4_seats": track_l4_seats[t],
            }
            for t in TRACKS
        },
        "v440_telemetry": {
            "defense_l4_cash_total": def_l4_cash_total,
            "defense_l4_cash_per_l4_seat": round(def_l4_cash_total / max(1, def_l4_seats), 2),
            "defense_l4_cash_per_seat": round(def_l4_cash_total / total_seats, 3),
            "release_gray_face_sets_total": rel_gray_sets_total,
            "release_gray_face_sets_per_l4_seat": round(rel_gray_sets_total / max(1, rel_l4_seats), 2),
            "release_gray_face_seats_used": rel_gray_sets_seats_used,
            "release_rerolls_used_total": rel_rerolls_total,
            "pr_l4_instant_ms_total": pr_l4_ms_total,
            "pr_l4_instant_ms_per_l4_seat": round(pr_l4_ms_total / max(1, pr_l4_seats), 2),
            "pr_l4_full_2_pct": round(100.0 * pr_l4_full_2_seats / max(1, pr_l4_seats), 1) if pr_l4_seats else 0.0,
            "triage_l4_replacements_taken": tri_l4_replacements,
            "triage_l4_replacement_rate_pct": round(100.0 * tri_l4_replacements / max(1, tri_l4_seats), 1) if tri_l4_seats else 0.0,
            "triage_l4_colors": dict(tri_l4_colors),
            "pr_l3_awarded_count": pr_l3_awarded_count,
            "pr_l3_graduated_count": pr_l3_graduated_count,
            "pr_l3_graduation_pct": round(100.0 * pr_l3_graduated_count / max(1, pr_l3_awarded_count), 1) if pr_l3_awarded_count else 0.0,
        },
        "archetypes": {
            k: {
                "games": arch_games[k],
                "wins": round(arch_wins[k], 2),
                "win_pct": round(100.0 * arch_wins[k] / max(1, arch_games[k]), 2),
            }
            for k in sorted(arch_games)
        },
        "companies": {
            k: {
                "games": comp_games[k],
                "wins": round(comp_wins[k], 2),
                "win_pct": round(100.0 * comp_wins[k] / max(1, comp_games[k]), 2),
            }
            for k in sorted(comp_games)
        },
    }


def write_report(summary: Dict[str, Any], out_path: str) -> None:
    lines: List[str] = []
    lines.append("# v0.44.0 Research Tracks & Capstones Validation Report")
    lines.append("")
    lines.append(
        f"**Sweep:** `v043` (Baseline) vs `v044` (Candidate) | "
        f"**Pods:** 4P, 3P, 2P | **Games/pod/variant:** {summary['games_per_pod']} "
        f"(seeds {summary['seed_start']}..{summary['seed_start'] + summary['games_per_pod'] - 1}, "
        f"{summary['total_games']} games total)"
    )
    lines.append("")

    # 1. Macro Pacing & End-Game Triad
    lines.append("## 1. Macro Pacing & End-Game Triad")
    lines.append("")
    lines.append("| Pod | Variant | Mean Rounds | Median (Min–Max) | Wipeout % | Singularity % | Patient Zero % | Market Collapse % |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for p in (4, 3, 2):
        for cfg in ("v043", "v044"):
            d = summary["results"][cfg][str(p)]
            er = d["end_reasons"]
            sing = er.get("singularity", {}).get("pct", 0.0)
            pz = er.get("patient_zero", {}).get("pct", 0.0)
            mc = er.get("market_collapse", {}).get("pct", 0.0)
            lines.append(
                f"| {p}P | `{cfg}` | {d['mean_rounds']:.2f} | "
                f"{d['median_rounds']} ({d['min_rounds']}–{d['max_rounds']}) | "
                f"{d['wipeout_rate']:.2f}% | {sing:.2f}% | {pz:.2f}% | {mc:.2f}% |"
            )
    lines.append("")

    # 2. Track Progression & L4 Capstone Achievement Rates
    lines.append("## 2. Research Track Progression & L4 Capstone Rates")
    lines.append("")
    lines.append("| Pod | Variant | Track | Mean Lvl | L2+ Seat % | L3+ Seat % | L4 Seat % | L4 Game % | 2+ L4 Seats % |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for p in (4, 3, 2):
        for t in TRACKS:
            for cfg in ("v043", "v044"):
                d = summary["results"][cfg][str(p)]
                tr = d["tracks"][t]
                lines.append(
                    f"| {p}P | `{cfg}` | {TRACK_LABELS[t]} | {tr['mean_level']:.2f} | "
                    f"{tr['l2_plus_pct']:.1f}% | {tr['l3_plus_pct']:.1f}% | "
                    f"{tr['l4_seat_pct']:.2f}% | {tr['l4_game_pct']:.2f}% | {d['seats_2plus_l4_pct']:.2f}% |"
                )
    lines.append("")

    # 3. v0.44.0 Capstone & Breakthrough Telemetry
    lines.append("## 3. v0.44.0 Capstone & Breakthrough Telemetry")
    lines.append("")
    lines.append("| Pod | Variant | Def L4 Cash (Total / Per L4 Seat) | Rel L4 Gray Sets (Total / Per L4 Seat) | PR L4 Instant MS (Total / Per L4 Seat / Full +2 %) | Tri L4 Replacements (Taken / Rate %) | PR L3 Scanned Grad (Awarded / Grad %) |")
    lines.append("|---|---|---|---|---|---|---|")
    for p in (4, 3, 2):
        for cfg in ("v043", "v044"):
            v = summary["results"][cfg][str(p)]["v440_telemetry"]
            lines.append(
                f"| {p}P | `{cfg}` | "
                f"${v['defense_l4_cash_total']} / ${v['defense_l4_cash_per_l4_seat']:.2f} | "
                f"{v['release_gray_face_sets_total']} / {v['release_gray_face_sets_per_l4_seat']:.2f} | "
                f"{v['pr_l4_instant_ms_total']} / {v['pr_l4_instant_ms_per_l4_seat']:.2f} / {v['pr_l4_full_2_pct']:.1f}% | "
                f"{v['triage_l4_replacements_taken']} / {v['triage_l4_replacement_rate_pct']:.1f}% | "
                f"{v['pr_l3_awarded_count']} / {v['pr_l3_graduation_pct']:.1f}% |"
            )
    lines.append("")

    # Triage L4 color breakdown
    lines.append("**Triage L4 Upgrade Color Breakdown (`v044`):**")
    for p in (4, 3, 2):
        colors = summary["results"]["v044"][str(p)]["v440_telemetry"]["triage_l4_colors"]
        c_str = ", ".join(f"{k}: {v}" for k, v in sorted(colors.items())) or "None"
        lines.append(f"- {p}P: {c_str}")
    lines.append("")

    # 4. Archetype & Client Company Win Rate Parity
    lines.append("## 4. Archetype & Client Company Win Rate Parity")
    lines.append("")
    lines.append("### Bot Archetype Win Rates (%)")
    all_archs = sorted(summary["results"]["v044"]["4"]["archetypes"].keys())
    lines.append("| Archetype | 4P v043 | 4P v044 | 3P v043 | 3P v044 | 2P v043 | 2P v044 |")
    lines.append("|---|---|---|---|---|---|---|")
    for a in all_archs:
        vals = []
        for p in ("4", "3", "2"):
            for cfg in ("v043", "v044"):
                vals.append(f"{summary['results'][cfg][p]['archetypes'].get(a, {}).get('win_pct', 0.0):.2f}%")
        lines.append(f"| {a} | " + " | ".join(vals) + " |")
    lines.append("")

    lines.append("### Client Company Win Rates (%)")
    all_comps = sorted(summary["results"]["v044"]["4"]["companies"].keys())
    lines.append("| Company | 4P v043 | 4P v044 | 3P v043 | 3P v044 | 2P v043 | 2P v044 |")
    lines.append("|---|---|---|---|---|---|---|")
    for c in all_comps:
        vals = []
        for p in ("4", "3", "2"):
            for cfg in ("v043", "v044"):
                vals.append(f"{summary['results'][cfg][p]['companies'].get(c, {}).get('win_pct', 0.0):.2f}%")
        lines.append(f"| {COMPANY_DISPLAY.get(c, c)} | " + " | ".join(vals) + " |")
    lines.append("")

    # 5. Outlier Seeds
    lines.append("## 5. Outlier Seeds")
    lines.append("")
    for p in (4, 3, 2):
        for cfg in ("v043", "v044"):
            d = summary["results"][cfg][str(p)]
            lines.append(
                f"- **{p}P `{cfg}`:** Early wipeouts (<=6 rds): {d['early_wipeout_count']} "
                f"(sample: {d['early_wipeout_seeds'][:8]}) | "
                f"Long stalls (>=13 rds): {d['long_stall_count']} "
                f"(sample: {d['long_stall_seeds'][:8]})"
            )
    lines.append("")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description="v0.44.0 Research Tracks & Capstones Validation Sweep")
    parser.add_argument("--games", type=int, default=1200, help="Games per pod per variant (default: 1200)")
    parser.add_argument("--seed", type=int, default=42, help="Starting seed (default: 42)")
    parser.add_argument("--players", type=int, nargs="+", default=[4, 3, 2], help="Pod sizes (default: 4 3 2)")
    parser.add_argument("--procs", type=int, default=8, help="Worker processes (default: 8)")
    parser.add_argument("--out-dir", type=str, default="sim_results/v440_research_tracks", help="Output directory")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    t0 = time.time()

    tasks = []
    for cfg in ("v043", "v044"):
        for p in args.players:
            for s in range(args.seed, args.seed + args.games):
                tasks.append((cfg, p, s))

    print(f"Running {len(tasks)} games across {args.procs} workers...", flush=True)
    with mp.Pool(processes=args.procs) as pool:
        results = pool.map(simulate_game, tasks, chunksize=50)

    grouped: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
        "v043": defaultdict(list),
        "v044": defaultdict(list),
    }
    for r in results:
        grouped[r["config"]][str(r["players"])].append(r)

    summary = {
        "games_per_pod": args.games,
        "seed_start": args.seed,
        "total_games": len(tasks),
        "elapsed_sec": round(time.time() - t0, 2),
        "results": {
            cfg: {
                str(p): aggregate_pod(grouped[cfg][str(p)])
                for p in args.players
            }
            for cfg in ("v043", "v044")
        },
    }

    json_path = os.path.join(args.out_dir, "summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    report_path = os.path.join(args.out_dir, "validation_report.md")
    write_report(summary, report_path)
    print(f"Completed {len(tasks)} games in {summary['elapsed_sec']}s -> {report_path}", flush=True)


if __name__ == "__main__":
    main()
