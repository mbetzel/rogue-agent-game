"""Monte Carlo Telemetry Sweep: v0.45.0 (GameConfig.v045_roster) vs v0.44.0 (GameConfig.v044_roster).

Runs 2P, 3P, and 4P pods with explicit seeds and captures:
1. Pacing & Endings (rounds, Singularity, Patient Zero, Market Collapse, Total Wipeout, v1.0 breach rate).
2. Defense Grid Overflow (overflow events/game, Secret loss, shield purges/game, Green cube capacity stress).
3. WS-OPERATOR (win rate, Research Tokens gained per trigger / per game).
4. 2P SETEC Corp (final Market Share, 1st/2nd/3rd place %, human MLB share, Market Collapse % in 2P).
5. Outlier seeds (fastest v1.0 breach, extreme overflow, extreme SETEC MS, shortest/longest games).

Outputs:
- sim_results/v045_telemetry_summary.json
- sim_results/v045_telemetry_report.md
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

from sim.config import GameConfig
from sim.engine import GameEngine
from sim.entities import WhiteHatCode, get_random_companies, get_random_setup, get_random_white_hats
from tests.fixtures.v035_parity.capture import _bot_classes


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
    s = engine.state

    nwin = max(1, len(res.winner_ids))
    end_reason = res.end_reason.value if hasattr(res.end_reason, "value") else str(res.end_reason)

    v1_name = s.version_deck[0].name if s.version_deck else ""
    v1_breach_round = None
    for tel in res.telemetry_history:
        if tel.active_version_name == v1_name:
            if any(snap.get("is_patient_zero") for snap in tel.player_snapshots):
                v1_breach_round = tel.round_number
                break

    # Operator triggers per game from round telemetry
    op_triggers_total = sum(
        tel.purple_star_triggers_by_operative.get(WhiteHatCode.OPERATOR.value, 0)
        for tel in res.telemetry_history
    )

    player_records = []
    overflow_events = 0
    secrets_lost_overflow = 0
    slots_purged = 0
    cubes_purged = 0
    max_green_cubes = 0
    max_green_util = 0.0
    final_green_cubes_sum = 0
    final_green_cap_sum = 0

    for p in s.players:
        won = (1.0 / nwin) if p.player_id in res.winner_ids else 0.0
        wh_code = p.white_hat.code.value if p.white_hat is not None else "NONE"
        overflow_events += int(p.defense_grid_overflow_count)
        secrets_lost_overflow += int(p.secrets_lost_to_overflow)
        slots_purged += int(p.slots_purged_by_shields_total)
        cubes_purged += int(p.cubes_purged_by_shields_total)

        g_cubes = int(p.total_green_cubes)
        g_cap = int(p.max_green_capacity)
        final_green_cubes_sum += g_cubes
        final_green_cap_sum += g_cap
        if g_cubes > max_green_cubes:
            max_green_cubes = g_cubes
        util = (g_cubes / g_cap) if g_cap > 0 else 0.0
        if util > max_green_util:
            max_green_util = util

        player_records.append({
            "wh_code": wh_code,
            "won": won,
            "secrets": int(p.secrets),
            "market_share": int(p.market_share),
            "is_patient_zero": bool(p.is_patient_zero),
            "op_research": int(p.operator_research_harvested),
            "red_payout_secrets": int(p.red_payout_secrets),
        })

    # 2P SETEC Corp stats
    setec_active = bool(s.setec_corp_active)
    setec_ms = int(s.setec_market_share)
    setec_place = None
    if setec_active:
        higher_humans = sum(1 for p in s.players if p.market_share > setec_ms)
        setec_place = 1 + higher_humans

    human_mlb_secrets = sum(p.red_payout_secrets for p in s.players)
    setec_mlb_absorbed = int(s.setec_corp_mlb_secrets_absorbed)

    return {
        "config": config_name,
        "players": players,
        "seed": seed,
        "rounds": int(res.total_rounds),
        "end_reason": end_reason,
        "is_total_wipeout": bool(res.is_total_wipeout),
        "v1_breach": v1_breach_round is not None,
        "v1_breach_round": v1_breach_round,
        "overflow_events": overflow_events,
        "secrets_lost_overflow": secrets_lost_overflow,
        "slots_purged": slots_purged,
        "cubes_purged": cubes_purged,
        "max_green_cubes": max_green_cubes,
        "max_green_util": max_green_util,
        "final_green_cubes": final_green_cubes_sum,
        "final_green_cap": final_green_cap_sum,
        "green_clamped": sum(tel.green_cubes_clamped_per_round for tel in res.telemetry_history),
        "op_triggers_total": op_triggers_total,
        "setec_active": setec_active,
        "setec_ms": setec_ms,
        "setec_place": setec_place,
        "setec_advances": int(s.setec_corp_advances_total),
        "setec_mlb_1st": int(s.setec_corp_mlb_1st_places),
        "setec_mlb_2nd": int(s.setec_corp_mlb_2nd_places),
        "setec_mlb_absorbed": setec_mlb_absorbed,
        "human_mlb_secrets": human_mlb_secrets,
        "players_data": player_records,
    }


def aggregate(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(records)
    end_counts = Counter(r["end_reason"] for r in records)
    v1_breaches = [r for r in records if r["v1_breach"]]
    op_games = []
    op_wins = 0.0
    op_research_total = 0
    op_triggers_total = 0

    for r in records:
        ops = [p for p in r["players_data"] if p["wh_code"] == WhiteHatCode.OPERATOR.value]
        if ops:
            op_games.append(r)
            for p in ops:
                op_wins += p["won"]
                op_research_total += p["op_research"]
            op_triggers_total += r["op_triggers_total"]

    n_ops = sum(
        1 for r in records for p in r["players_data"] if p["wh_code"] == WhiteHatCode.OPERATOR.value
    )

    setec_recs = [r for r in records if r["setec_active"]]
    setec_summary = None
    if setec_recs:
        sn = len(setec_recs)
        place_counts = Counter(r["setec_place"] for r in setec_recs)
        tot_human_mlb = sum(r["human_mlb_secrets"] for r in setec_recs)
        tot_setec_mlb = sum(r["setec_mlb_absorbed"] for r in setec_recs)
        tot_mlb = tot_human_mlb + tot_setec_mlb
        setec_summary = {
            "games": sn,
            "mean_final_ms": sum(r["setec_ms"] for r in setec_recs) / sn,
            "place_1_pct": 100.0 * place_counts[1] / sn,
            "place_2_pct": 100.0 * place_counts[2] / sn,
            "place_3_pct": 100.0 * place_counts[3] / sn,
            "mean_advances": sum(r["setec_advances"] for r in setec_recs) / sn,
            "mean_mlb_1st_events": sum(r["setec_mlb_1st"] for r in setec_recs) / sn,
            "mean_mlb_2nd_events": sum(r["setec_mlb_2nd"] for r in setec_recs) / sn,
            "human_mlb_share_pct": (100.0 * tot_human_mlb / tot_mlb) if tot_mlb > 0 else 100.0,
            "mean_human_mlb_secrets": tot_human_mlb / sn,
            "mean_setec_mlb_absorbed": tot_setec_mlb / sn,
        }

    # Outliers
    outliers: Dict[str, Any] = {}
    if v1_breaches:
        fastest_v1 = min(v1_breaches, key=lambda r: (r["v1_breach_round"], r["seed"]))
        outliers["fastest_v1_breach"] = {
            "seed": fastest_v1["seed"],
            "round": fastest_v1["v1_breach_round"],
            "end_reason": fastest_v1["end_reason"],
        }
    max_ov = max(records, key=lambda r: (r["overflow_events"], r["secrets_lost_overflow"], -r["seed"]))
    if max_ov["overflow_events"] > 0:
        outliers["max_overflow"] = {
            "seed": max_ov["seed"],
            "overflow_events": max_ov["overflow_events"],
            "secrets_lost": max_ov["secrets_lost_overflow"],
            "rounds": max_ov["rounds"],
        }
    if setec_recs:
        max_setec = max(setec_recs, key=lambda r: (r["setec_ms"], -r["seed"]))
        outliers["max_setec_ms"] = {
            "seed": max_setec["seed"],
            "setec_ms": max_setec["setec_ms"],
            "rounds": max_setec["rounds"],
            "end_reason": max_setec["end_reason"],
        }
    shortest = min(records, key=lambda r: (r["rounds"], r["seed"]))
    longest = max(records, key=lambda r: (r["rounds"], -r["seed"]))
    outliers["shortest_game"] = {"seed": shortest["seed"], "rounds": shortest["rounds"], "end_reason": shortest["end_reason"]}
    outliers["longest_game"] = {"seed": longest["seed"], "rounds": longest["rounds"], "end_reason": longest["end_reason"]}

    return {
        "games": n,
        "mean_rounds": sum(r["rounds"] for r in records) / n,
        "singularity_pct": 100.0 * end_counts["singularity"] / n,
        "patient_zero_pct": 100.0 * end_counts["patient_zero"] / n,
        "market_collapse_pct": 100.0 * end_counts["market_collapse"] / n,
        "total_wipeout_pct": 100.0 * sum(1 for r in records if r["is_total_wipeout"]) / n,
        "v1_breach_pct": 100.0 * len(v1_breaches) / n,
        "overflow_games_pct": 100.0 * sum(1 for r in records if r["overflow_events"] > 0) / n,
        "mean_overflow_events": sum(r["overflow_events"] for r in records) / n,
        "mean_secrets_lost_overflow": sum(r["secrets_lost_overflow"] for r in records) / n,
        "mean_slots_purged": sum(r["slots_purged"] for r in records) / n,
        "mean_cubes_purged": sum(r["cubes_purged"] for r in records) / n,
        "mean_final_green_cubes_per_game": sum(r["final_green_cubes"] for r in records) / n,
        "mean_final_green_util_pct": 100.0 * sum(r["final_green_cubes"] for r in records) / max(1, sum(r["final_green_cap"] for r in records)),
        "mean_peak_player_green_util_pct": 100.0 * sum(r["max_green_util"] for r in records) / n,
        "mean_green_clamped": sum(r["green_clamped"] for r in records) / n,
        "operator": {
            "appearances": n_ops,
            "win_rate_pct": (100.0 * op_wins / n_ops) if n_ops else 0.0,
            "mean_research_per_game": (op_research_total / n_ops) if n_ops else 0.0,
            "mean_triggers_per_game": (op_triggers_total / n_ops) if n_ops else 0.0,
            "mean_research_per_trigger": (op_research_total / op_triggers_total) if op_triggers_total else 0.0,
        },
        "setec_corp": setec_summary,
        "outliers": outliers,
    }


def format_report(summary: Dict[str, Any], games: int, seed_start: int, elapsed: float) -> str:
    lines: List[str] = [
        "# v0.45.0 Monte Carlo Telemetry Report",
        "",
        f"- **Configs**: `GameConfig.v045_roster()` vs `GameConfig.v044_roster()`",
        f"- **Sample**: {games} games/pod/variant (seeds `{seed_start}..{seed_start + games - 1}`), elapsed `{elapsed:.1f}s`",
        "",
        "## 1. Pacing & Endings",
        "",
        "| Pod | Variant | Mean Rounds | Singularity % | Patient Zero % | Market Collapse % | Total Wipeout % | v1.0 Breach % |",
        "|---:|:---|---:|---:|---:|---:|---:|---:|",
    ]
    for p in (2, 3, 4):
        for cfg in ("v044_roster", "v045_roster"):
            d = summary[f"{p}P"][cfg]
            lines.append(
                f"| {p}P | `{cfg}` | {d['mean_rounds']:.2f} | {d['singularity_pct']:.1f}% | "
                f"{d['patient_zero_pct']:.1f}% | {d['market_collapse_pct']:.1f}% | "
                f"{d['total_wipeout_pct']:.1f}% | {d['v1_breach_pct']:.1f}% |"
            )

    lines += [
        "",
        "## 2. Defense Grid Overflow & Green Cube Stress",
        "",
        "| Pod | Variant | Games w/ Overflow % | Overflows / Game | Secrets Lost / Game | Slots Purged / Game | Cubes Purged / Game | Final Green Util % | Clamped / Game |",
        "|---:|:---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for p in (2, 3, 4):
        for cfg in ("v044_roster", "v045_roster"):
            d = summary[f"{p}P"][cfg]
            lines.append(
                f"| {p}P | `{cfg}` | {d['overflow_games_pct']:.1f}% | {d['mean_overflow_events']:.2f} | "
                f"{d['mean_secrets_lost_overflow']:.2f} | {d['mean_slots_purged']:.2f} | "
                f"{d['mean_cubes_purged']:.2f} | {d['mean_final_green_util_pct']:.1f}% | {d['mean_green_clamped']:.2f} |"
            )

    lines += [
        "",
        "## 3. WS-OPERATOR Telemetry",
        "",
        "| Pod | Variant | Appearances | Win Rate % | Research / Game | Triggers / Game | Research / Trigger |",
        "|---:|:---|---:|---:|---:|---:|---:|",
    ]
    for p in (2, 3, 4):
        for cfg in ("v044_roster", "v045_roster"):
            op = summary[f"{p}P"][cfg]["operator"]
            lines.append(
                f"| {p}P | `{cfg}` | {op['appearances']} | {op['win_rate_pct']:.1f}% | "
                f"{op['mean_research_per_game']:.2f} | {op['mean_triggers_per_game']:.2f} | {op['mean_research_per_trigger']:.2f} |"
            )

    lines += [
        "",
        "## 4. 2P SETEC Corp (v0.45.0)",
        "",
    ]
    sc = summary["2P"]["v045_roster"]["setec_corp"]
    if sc:
        lines += [
            "| Metric | Value |",
            "|:---|---:|",
            f"| Mean Final SETEC Market Share | {sc['mean_final_ms']:.2f} |",
            f"| SETEC 1st / 2nd / 3rd Place % | {sc['place_1_pct']:.1f}% / {sc['place_2_pct']:.1f}% / {sc['place_3_pct']:.1f}% |",
            f"| Mean SETEC Advances / Game | {sc['mean_advances']:.2f} |",
            f"| Human Market Leader Bonus Share | {sc['human_mlb_share_pct']:.1f}% |",
            f"| Mean Human MLB Secrets / Game | {sc['mean_human_mlb_secrets']:.2f} |",
            f"| Mean SETEC MLB Secrets Absorbed / Game | {sc['mean_setec_mlb_absorbed']:.2f} |",
            f"| 2P Market Collapse % (v0.45 vs v0.44) | {summary['2P']['v045_roster']['market_collapse_pct']:.1f}% vs {summary['2P']['v044_roster']['market_collapse_pct']:.1f}% |",
        ]

    lines += [
        "",
        "## 5. Notable Outlier Seeds (`v045_roster`)",
        "",
    ]
    for p in (2, 3, 4):
        o = summary[f"{p}P"]["v045_roster"]["outliers"]
        parts = [f"shortest={o['shortest_game']}", f"longest={o['longest_game']}"]
        if "fastest_v1_breach" in o:
            parts.append(f"fastest_v1_breach={o['fastest_v1_breach']}")
        if "max_overflow" in o:
            parts.append(f"max_overflow={o['max_overflow']}")
        if "max_setec_ms" in o:
            parts.append(f"max_setec_ms={o['max_setec_ms']}")
        lines.append(f"- **{p}P**: " + "; ".join(parts))

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="v0.45.0 Monte Carlo Telemetry Sweep")
    parser.add_argument("--games", type=int, default=1000, help="Games per pod per variant (default: 1000)")
    parser.add_argument("--seed", type=int, default=42, help="Starting seed (default: 42)")
    parser.add_argument("--players", type=int, nargs="+", default=[2, 3, 4], help="Pod sizes (default: 2 3 4)")
    parser.add_argument("--procs", type=int, default=8, help="Worker processes (default: 8)")
    parser.add_argument("--out-dir", default=os.path.join(ROOT, "sim_results"), help="Output directory")
    args = parser.parse_args()

    t0 = time.time()
    tasks: List[Tuple[str, int, int]] = []
    for p in args.players:
        for cfg in ("v044_roster", "v045_roster"):
            for i in range(args.games):
                tasks.append((cfg, p, args.seed + i))

    with mp.Pool(processes=args.procs) as pool:
        results = pool.map(simulate_game, tasks, chunksize=25)

    grouped: Dict[Tuple[int, str], List[Dict[str, Any]]] = defaultdict(list)
    for r in results:
        grouped[(r["players"], r["config"])].append(r)

    summary: Dict[str, Any] = {}
    for p in args.players:
        summary[f"{p}P"] = {}
        for cfg in ("v044_roster", "v045_roster"):
            summary[f"{p}P"][cfg] = aggregate(grouped[(p, cfg)])

    elapsed = time.time() - t0
    os.makedirs(args.out_dir, exist_ok=True)
    json_path = os.path.join(args.out_dir, "v045_telemetry_summary.json")
    md_path = os.path.join(args.out_dir, "v045_telemetry_report.md")

    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)

    report = format_report(summary, args.games, args.seed, elapsed)
    with open(md_path, "w") as f:
        f.write(report)

    print(report)


if __name__ == "__main__":
    main()
