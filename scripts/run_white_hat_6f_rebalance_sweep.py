"""Monte Carlo validation sweep for White Hat 6F Rebalance (v0.43.0).

Compares Baseline (`GameConfig.v043(white_hat_6f_rebalance=False)`) vs.
Candidate (`GameConfig.v043(white_hat_6f_rebalance=True)`) across 4P, 3P, and 2P
pods (1,000 games per pod per arm = 6,000 total games, seeds 42..1041).

Outputs a compact telemetry report to:
  sim_results/white_hat_6f_rebalance/validation_report.md
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import multiprocessing as mp
import os
import random
import sys
import time
from typing import Any, Dict, List, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from sim.config import EndGameReason, GameConfig
from sim.engine import GameEngine
from sim.entities import get_random_companies, get_random_setup, get_random_white_hats
from tests.fixtures.v035_parity.capture import _bot_classes

OPERATIVES = ("OPERATOR", "PHREAKER", "ACOUSTIC", "SPOOK", "PRODIGY", "CIPHER")
COMPANIES = ("MERIDIAN", "OMNIDYNE", "AEGIS", "DTO", "HELIX", "PROMETHEUS")


def build_engine(players: int, seed: int, rebalance: bool) -> GameEngine:
    classes = _bot_classes()
    rng = random.Random(seed)
    bots = [classes[(seed * players + i) % len(classes)](i) for i in range(players)]
    rng.shuffle(bots)
    for i, b in enumerate(bots):
        b.player_id = i

    variants, version_deck = get_random_setup(rng, profile="STANDARD")
    companies = get_random_companies(players, rng)
    white_hats = get_random_white_hats(players, rng)

    cfg = GameConfig.v043(
        num_players=players,
        white_hat_6f_rebalance=rebalance,
    )
    return GameEngine(
        config=cfg,
        bots=bots,
        seed=seed,
        variant_cards=variants,
        version_deck=version_deck,
        companies=companies,
        white_hats=white_hats,
    )


def simulate_game(task: Tuple[int, int, bool]) -> Dict[str, Any]:
    players, seed, rebalance = task
    engine = build_engine(players, seed, rebalance)
    res = engine.run_game()

    nwin = max(1, len(res.winner_ids))
    star_by_op: Counter = Counter()
    op_research = 0
    ph_grads = 0
    ac_cash = 0
    sp_burns = 0
    pr_overrides = 0

    for t in engine.telemetry_history:
        for op_code, cnt in t.purple_star_triggers_by_operative.items():
            star_by_op[op_code] += cnt
        op_research += t.operator_research_harvested
        ph_grads += t.phreaker_bandwidth_graduates
        ac_cash += t.acoustic_cash_harvested
        sp_burns += t.spook_gray_dice_burned
        pr_overrides += t.prodigy_overrides_executed

    player_records = []
    for p in engine.state.players:
        wh_code = p.white_hat.code.value if p.white_hat is not None else "NONE"
        c_code = p.company.code.value if getattr(p.company, "code", None) is not None else str(getattr(p.company, "code", "NONE"))
        won = (1.0 / nwin) if p.player_id in res.winner_ids else 0.0
        player_records.append({
            "white_hat": wh_code,
            "company": c_code,
            "win": won,
            "is_patient_zero": bool(p.is_patient_zero),
            "secrets": int(p.secrets),
        })

    return {
        "players": players,
        "seed": seed,
        "rounds": int(res.total_rounds),
        "end_reason": res.end_reason.value,
        "is_total_wipeout": bool(res.is_total_wipeout),
        "star_by_op": dict(star_by_op),
        "op_research": op_research,
        "ph_grads": ph_grads,
        "ac_cash": ac_cash,
        "sp_burns": sp_burns,
        "pr_overrides": pr_overrides,
        "player_records": player_records,
    }


def summarize_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(records)
    mean_rounds = sum(r["rounds"] for r in records) / n
    wipeouts = sum(1 for r in records if r["is_total_wipeout"])
    end_counts = Counter(r["end_reason"] for r in records)

    survivor_secrets = [
        p["secrets"]
        for r in records
        for p in r["player_records"]
        if not p["is_patient_zero"]
    ]
    mean_surv_secrets = (sum(survivor_secrets) / len(survivor_secrets)) if survivor_secrets else 0.0

    # Per operative stats (conditional on operative being present in the game)
    op_stats: Dict[str, Dict[str, float]] = {}
    for op in OPERATIVES:
        appearances = 0
        wins = 0.0
        pzs = 0
        stars = 0
        yield_main = 0
        yield_sec = 0
        for r in records:
            present = [p for p in r["player_records"] if p["white_hat"] == op]
            if not present:
                continue
            appearances += len(present)
            for p in present:
                wins += p["win"]
                if p["is_patient_zero"]:
                    pzs += 1
            stars += r["star_by_op"].get(op, 0)
            if op == "OPERATOR":
                yield_main += r["op_research"]
            elif op == "PHREAKER":
                yield_main += r["ph_grads"]
                yield_sec += r["star_by_op"].get(op, 0)  # $1 per Star when rebalanced
            elif op == "ACOUSTIC":
                yield_main += r["ac_cash"]
            elif op == "SPOOK":
                yield_main += r["sp_burns"]
                yield_sec += r["sp_burns"]  # $1 per burned Gray die
            elif op == "PRODIGY":
                yield_main += r["pr_overrides"]

        op_stats[op] = {
            "games": appearances,
            "win_pct": 100.0 * wins / appearances if appearances else 0.0,
            "pz_pct": 100.0 * pzs / appearances if appearances else 0.0,
            "mean_stars": stars / appearances if appearances else 0.0,
            "mean_yield_main": yield_main / appearances if appearances else 0.0,
            "mean_yield_sec": yield_sec / appearances if appearances else 0.0,
        }

    # Per company stats
    comp_stats: Dict[str, Dict[str, float]] = {}
    for comp in COMPANIES:
        appearances = 0
        wins = 0.0
        pzs = 0
        for r in records:
            for p in r["player_records"]:
                if p["company"] == comp:
                    appearances += 1
                    wins += p["win"]
                    if p["is_patient_zero"]:
                        pzs += 1
        comp_stats[comp] = {
            "games": appearances,
            "win_pct": 100.0 * wins / appearances if appearances else 0.0,
            "pz_pct": 100.0 * pzs / appearances if appearances else 0.0,
        }

    # Outlier seeds
    min_r = min(records, key=lambda r: (r["rounds"], r["seed"]))
    max_r = max(records, key=lambda r: (r["rounds"], -r["seed"]))
    wipeout_seeds = [r["seed"] for r in records if r["is_total_wipeout"]][:10]

    return {
        "n_games": n,
        "mean_rounds": mean_rounds,
        "wipeout_pct": 100.0 * wipeouts / n,
        "singularity_pct": 100.0 * end_counts.get(EndGameReason.SINGULARITY.value, 0) / n,
        "patient_zero_end_pct": 100.0 * end_counts.get(EndGameReason.PATIENT_ZERO.value, 0) / n,
        "market_collapse_pct": 100.0 * end_counts.get(EndGameReason.MARKET_COLLAPSE.value, 0) / n,
        "mean_surv_secrets": mean_surv_secrets,
        "op_stats": op_stats,
        "comp_stats": comp_stats,
        "min_round_seed": (min_r["players"], min_r["seed"], min_r["rounds"], min_r["end_reason"]),
        "max_round_seed": (max_r["players"], max_r["seed"], max_r["rounds"], max_r["end_reason"]),
        "sample_wipeout_seeds": wipeout_seeds,
    }


def format_report(
    base_all: Dict[str, Any],
    cand_all: Dict[str, Any],
    base_by_pod: Dict[int, Dict[str, Any]],
    cand_by_pod: Dict[int, Dict[str, Any]],
    num_games: int,
    base_seed: int,
) -> str:
    lines: List[str] = []
    lines.append("# White Hat 6F Rebalance — Monte Carlo Validation Report")
    lines.append("")
    lines.append(
        f"- **Config**: Baseline `GameConfig.v043(white_hat_6f_rebalance=False)` vs. "
        f"Candidate `GameConfig.v043(white_hat_6f_rebalance=True)`"
    )
    lines.append(
        f"- **Matrix**: 4P, 3P, 2P pods × {num_games} games/pod "
        f"(seeds `{base_seed}..{base_seed + num_games - 1}`), randomized White Hat & Client Company pairings "
        f"({num_games * 3} games/arm, {num_games * 6} total)."
    )
    lines.append("")
    lines.append("## 1. Macro Metrics (Pooled & By Pod)")
    lines.append("")
    lines.append("| Scope | Arm | Mean Rounds | Total Wipeout % | Singularity % | Patient Zero % | Market Collapse % | Mean Surv. Secrets |")
    lines.append("| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |")

    def add_macro_row(label: str, arm: str, s: Dict[str, Any]) -> None:
        lines.append(
            f"| {label} | {arm} | {s['mean_rounds']:.2f} | {s['wipeout_pct']:.1f}% | "
            f"{s['singularity_pct']:.1f}% | {s['patient_zero_end_pct']:.1f}% | "
            f"{s['market_collapse_pct']:.1f}% | {s['mean_surv_secrets']:.2f} |"
        )

    add_macro_row("All (3,000)", "Baseline", base_all)
    add_macro_row("All (3,000)", "Candidate", cand_all)
    for pod in (4, 3, 2):
        add_macro_row(f"{pod}P ({num_games})", "Baseline", base_by_pod[pod])
        add_macro_row(f"{pod}P ({num_games})", "Candidate", cand_by_pod[pod])

    lines.append("")
    lines.append("## 2. Per-White-Hat Operative Metrics (Pooled Across 2P/3P/4P)")
    lines.append("")
    lines.append("*Note: Mean Stars and Protocol Yields are per game in which the operative appeared.*")
    lines.append("")
    lines.append("| Operative | Arm | Games | Win Rate % | Patient Zero % | Mean ★/Game | Protocol Yield / Game |")
    lines.append("| :--- | :--- | ---: | ---: | ---: | ---: | :--- |")

    for op in OPERATIVES:
        for arm_name, summary in (("Baseline", base_all), ("Candidate", cand_all)):
            st = summary["op_stats"][op]
            if op == "OPERATOR":
                y_str = f"{st['mean_yield_main']:.2f} 🔬"
            elif op == "PHREAKER":
                sec = st["mean_yield_sec"] if arm_name == "Candidate" else 0.0
                y_str = f"{st['mean_yield_main']:.2f} extra grads, ${sec:.2f}"
            elif op == "ACOUSTIC":
                y_str = f"${st['mean_yield_main']:.2f}"
            elif op == "SPOOK":
                y_str = f"{st['mean_yield_main']:.2f} burns (${st['mean_yield_sec']:.2f})"
            elif op == "PRODIGY":
                y_str = f"{st['mean_yield_main']:.2f} overrides"
            else:
                y_str = "— (parity)"
            lines.append(
                f"| {op} | {arm_name} | {st['games']} | {st['win_pct']:.1f}% | "
                f"{st['pz_pct']:.1f}% | {st['mean_stars']:.2f} | {y_str} |"
            )

    lines.append("")
    lines.append("### Operative Win Rate % By Pod (Baseline → Candidate)")
    lines.append("")
    lines.append("| Operative | 4P Win % | 3P Win % | 2P Win % |")
    lines.append("| :--- | ---: | ---: | ---: |")
    for op in OPERATIVES:
        row = [op]
        for pod in (4, 3, 2):
            bw = base_by_pod[pod]["op_stats"][op]["win_pct"]
            cw = cand_by_pod[pod]["op_stats"][op]["win_pct"]
            row.append(f"{bw:.1f}% → {cw:.1f}%")
        lines.append(f"| {' | '.join(row)} |")

    lines.append("")
    lines.append("## 3. Client Company Win-Rate Parity Check (Pooled)")
    lines.append("")
    lines.append("| Company | Baseline Win % | Candidate Win % | Delta (pp) | Candidate PZ % |")
    lines.append("| :--- | ---: | ---: | ---: | ---: |")
    for comp in COMPANIES:
        bw = base_all["comp_stats"][comp]["win_pct"]
        cw = cand_all["comp_stats"][comp]["win_pct"]
        cpz = cand_all["comp_stats"][comp]["pz_pct"]
        lines.append(f"| {comp} | {bw:.1f}% | {cw:.1f}% | {cw - bw:+.1f} | {cpz:.1f}% |")

    lines.append("")
    lines.append("## 4. Outlier Seeds")
    lines.append("")
    for arm_name, summary in (("Baseline", base_all), ("Candidate", cand_all)):
        mn = summary["min_round_seed"]
        mx = summary["max_round_seed"]
        lines.append(
            f"- **{arm_name}**: Shortest `{mn[0]}P seed={mn[1]}` ({mn[2]} rounds, `{mn[3]}`); "
            f"Longest `{mx[0]}P seed={mx[1]}` ({mx[2]} rounds, `{mx[3]}`); "
            f"Sample wipeout seeds: `{summary['sample_wipeout_seeds']}`"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="White Hat 6F Rebalance Monte Carlo sweep.")
    parser.add_argument("--runs", type=int, default=1000, help="Games per pod per arm (default: 1000).")
    parser.add_argument("--seed", type=int, default=42, help="Starting seed (default: 42).")
    parser.add_argument(
        "--out",
        type=str,
        default="sim_results/white_hat_6f_rebalance/validation_report.md",
        help="Output markdown report path.",
    )
    args = parser.parse_args()

    pods = (4, 3, 2)
    seeds = [args.seed + i for i in range(args.runs)]

    t0 = time.time()
    tasks_base = [(p, s, False) for p in pods for s in seeds]
    tasks_cand = [(p, s, True) for p in pods for s in seeds]

    workers = max(1, min(os.cpu_count() or 4, 8))
    with mp.Pool(processes=workers) as pool:
        base_records = pool.map(simulate_game, tasks_base, chunksize=50)
        cand_records = pool.map(simulate_game, tasks_cand, chunksize=50)

    base_by_pod = {p: summarize_records([r for r in base_records if r["players"] == p]) for p in pods}
    cand_by_pod = {p: summarize_records([r for r in cand_records if r["players"] == p]) for p in pods}
    base_all = summarize_records(base_records)
    cand_all = summarize_records(cand_records)

    report = format_report(base_all, cand_all, base_by_pod, cand_by_pod, args.runs, args.seed)
    out_path = os.path.join(ROOT, args.out) if not os.path.isabs(args.out) else args.out
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)

    elapsed = time.time() - t0
    print(f"Completed {len(tasks_base) + len(tasks_cand)} games in {elapsed:.1f}s -> {out_path}")


if __name__ == "__main__":
    main()
