"""Monte Carlo Simulation Sweep for Phase 17: Active Infrastructure Valuation & Maintenance Scoring (v0.11.0).

Executes N=1,000 matches per player count (2P, 3P, 4P) with randomized setups and base seed 42.
Collects pacing, end-game vectors, active infrastructure scoring metrics, and technical debt telemetry.
"""

from __future__ import annotations

import json
import random
import statistics
import sys
from typing import Any, Dict, List

from sim.bots import (
    AccelerationistBot,
    AdaptiveBalancedBot,
    SecOpsTurtleBot,
    VentureGreedBot,
)
from sim.config import EndGameReason, GameConfig
from sim.engine import EndGameResult, GameEngine
from sim.entities import get_random_setup


def run_sweep(num_runs: int = 1000, base_seed: int = 42) -> Dict[str, Any]:
    player_counts = [2, 3, 4]
    results_by_pod: Dict[int, Dict[str, Any]] = {}

    for p_count in player_counts:
        round_counts: List[int] = []
        end_reasons: Dict[EndGameReason, int] = {reason: 0 for reason in EndGameReason}
        winning_scores: List[float] = []
        survivor_scores: List[float] = []
        all_players_cash: List[int] = []
        survivor_cash: List[int] = []
        all_players_unpatched_colored_dice: List[int] = []
        survivor_unpatched_colored_dice: List[int] = []
        all_players_unpatched_vp_lost: List[int] = []
        survivor_unpatched_vp_lost: List[int] = []
        survivor_has_unpatched_colored: List[int] = []
        total_survivors = 0
        total_players_evaluated = 0
        early_deaths = 0
        outliers: List[Dict[str, Any]] = []
        bot_wins: Dict[str, int] = {}

        for run_idx in range(num_runs):
            seed = base_seed + run_idx
            config = GameConfig(num_players=p_count)

            bots = [
                AdaptiveBalancedBot(0),
                SecOpsTurtleBot(1),
                VentureGreedBot(2),
                AccelerationistBot(3),
            ][:p_count]

            rng_setup = random.Random(seed * 17)
            variant_cards, version_deck = get_random_setup(rng_setup)

            engine = GameEngine(
                config=config,
                bots=bots,
                seed=seed,
                variant_cards=variant_cards,
                version_deck=version_deck,
            )

            result: EndGameResult = engine.run_game()

            round_counts.append(result.total_rounds)
            end_reasons[result.end_reason] = end_reasons.get(result.end_reason, 0) + 1

            if result.total_rounds <= 4:
                early_deaths += 1

            if result.rankings:
                winner = result.rankings[0]
                winning_scores.append(float(winner["portfolio_value"] if not result.is_total_wipeout else winner["net_score"]))
                w_name = winner["bot_name"]
                bot_wins[w_name] = bot_wins.get(w_name, 0) + 1

            for r in result.rankings:
                total_players_evaluated += 1
                all_players_cash.append(r["money"])
                all_players_unpatched_colored_dice.append(r["unpatched_colored_dice_count"])
                all_players_unpatched_vp_lost.append(r["unpatched_dice_vp_lost"])

                if not r["is_patient_zero"]:
                    total_survivors += 1
                    survivor_scores.append(float(r["portfolio_value"]))
                    survivor_cash.append(r["money"])
                    survivor_unpatched_colored_dice.append(r["unpatched_colored_dice_count"])
                    survivor_unpatched_vp_lost.append(r["unpatched_dice_vp_lost"])
                    survivor_has_unpatched_colored.append(1 if r["unpatched_colored_dice_count"] > 0 else 0)

            # Capture outlier seeds
            if result.total_rounds <= 3 or result.total_rounds >= 15 or result.is_total_wipeout:
                if len(outliers) < 10:
                    outliers.append({
                        "seed": seed,
                        "rounds": result.total_rounds,
                        "end_reason": result.end_reason.value,
                        "is_wipeout": result.is_total_wipeout,
                    })

        mean_rounds = statistics.mean(round_counts)
        std_rounds = statistics.stdev(round_counts) if len(round_counts) > 1 else 0.0

        results_by_pod[p_count] = {
            "player_count": p_count,
            "total_games": num_runs,
            "mean_rounds": mean_rounds,
            "std_rounds": std_rounds,
            "min_rounds": min(round_counts),
            "max_rounds": max(round_counts),
            "singularity_pct": end_reasons[EndGameReason.SINGULARITY] / num_runs * 100,
            "patient_zero_pct": end_reasons[EndGameReason.PATIENT_ZERO] / num_runs * 100,
            "total_wipeout_pct": end_reasons[EndGameReason.TOTAL_WIPEOUT] / num_runs * 100,
            "round_limit_pct": end_reasons[EndGameReason.ROUND_LIMIT] / num_runs * 100,
            "early_death_pct": early_deaths / num_runs * 100,
            "mean_winning_score": statistics.mean(winning_scores) if winning_scores else 0.0,
            "mean_survivor_score": statistics.mean(survivor_scores) if survivor_scores else 0.0,
            "mean_cash_all": statistics.mean(all_players_cash) if all_players_cash else 0.0,
            "mean_cash_survivors": statistics.mean(survivor_cash) if survivor_cash else 0.0,
            "mean_unpatched_colored_all": statistics.mean(all_players_unpatched_colored_dice) if all_players_unpatched_colored_dice else 0.0,
            "mean_unpatched_colored_survivors": statistics.mean(survivor_unpatched_colored_dice) if survivor_unpatched_colored_dice else 0.0,
            "mean_unpatched_vp_lost_all": statistics.mean(all_players_unpatched_vp_lost) if all_players_unpatched_vp_lost else 0.0,
            "mean_unpatched_vp_lost_survivors": statistics.mean(survivor_unpatched_vp_lost) if survivor_unpatched_vp_lost else 0.0,
            "survivors_with_unpatched_colored_pct": (statistics.mean(survivor_has_unpatched_colored) * 100) if survivor_has_unpatched_colored else 0.0,
            "total_survivors": total_survivors,
            "bot_win_rates": {b: count / num_runs * 100 for b, count in sorted(bot_wins.items(), key=lambda x: x[1], reverse=True)},
            "outliers": outliers,
        }

    return results_by_pod


def print_markdown_report(results: Dict[int, Dict[str, Any]]) -> None:
    print("\n# Phase 17: Active Infrastructure Valuation & Maintenance Scoring (v0.11.0 Baseline)")
    print(f"Sample: N=1,000 matches per player count (Total 3,000 matches), Master Base Seed 42, Randomized Setups\n")

    print("## 1. Pacing & Win/Loss Telemetry Matrix")
    print("| Metric | 2-Player Pod (2P) | 3-Player Pod (3P) | 4-Player Pod (4P) | Target Benchmark |")
    print("| :--- | :---: | :---: | :---: | :---: |")

    r2 = results[2]
    r3 = results[3]
    r4 = results[4]

    print(f"| **Average Match Duration** | **{r2['mean_rounds']:.2f}** (±{r2['std_rounds']:.2f}) rds | **{r3['mean_rounds']:.2f}** (±{r3['std_rounds']:.2f}) rds | **{r4['mean_rounds']:.2f}** (±{r4['std_rounds']:.2f}) rds | ~8.0 rounds target |")
    print(f"| **Duration Range (Min / Max)** | {r2['min_rounds']} / {r2['max_rounds']} rds | {r3['min_rounds']} / {r3['max_rounds']} rds | {r4['min_rounds']} / {r4['max_rounds']} rds | Min ≥ 3, Max ≤ 16 |")
    print(f"| **Singularity Rate (%)** | **{r2['singularity_pct']:.1f}%** | **{r3['singularity_pct']:.1f}%** | **{r4['singularity_pct']:.1f}%** | 10%–40% |")
    print(f"| **Patient Zero Rate (%)** | **{r2['patient_zero_pct']:.1f}%** | **{r3['patient_zero_pct']:.1f}%** | **{r4['patient_zero_pct']:.1f}%** | Primary win/loss vector |")
    print(f"| **Total Wipeout Rate (%)** | **{r2['total_wipeout_pct']:.1f}%** | **{r3['total_wipeout_pct']:.1f}%** | **{r4['total_wipeout_pct']:.1f}%** | Safe limits across pods |")
    print(f"| **Early Deaths (≤ R4) (%)** | **{r2['early_death_pct']:.1f}%** | **{r3['early_death_pct']:.1f}%** | **{r4['early_death_pct']:.1f}%** | < 5.0% |")
    print(f"| **Round Limit Timeouts (30 rds)** | **{r2['round_limit_pct']:.1f}%** | **{r3['round_limit_pct']:.1f}%** | **{r4['round_limit_pct']:.1f}%** | 0.0% (Zero stalling) |")

    print("\n## 2. Active Infrastructure & Technical Debt Scoring Telemetry")
    print("| Metric | 2-Player Pod (2P) | 3-Player Pod (3P) | 4-Player Pod (4P) | Target Benchmark |")
    print("| :--- | :---: | :---: | :---: | :---: |")
    print(f"| **Average Winning Portfolio Score** | **{r2['mean_winning_score']:.1f}** VP | **{r3['mean_winning_score']:.1f}** VP | **{r4['mean_winning_score']:.1f}** VP | Healthy score spread |")
    print(f"| **Average Survivor Portfolio Score** | **{r2['mean_survivor_score']:.1f}** VP | **{r3['mean_survivor_score']:.1f}** VP | **{r4['mean_survivor_score']:.1f}** VP | Competitive survivor baseline |")
    print(f"| **Average Ending Cash (All Players)** | **${r2['mean_cash_all']:.2f}** | **${r3['mean_cash_all']:.2f}** | **${r4['mean_cash_all']:.2f}** | Cash spent on maintenance |")
    print(f"| **Average Ending Cash (Survivors)** | **${r2['mean_cash_survivors']:.2f}** | **${r3['mean_cash_survivors']:.2f}** | **${r4['mean_cash_survivors']:.2f}** | Late-game liquidity |")
    print(f"| **Avg Ending Unpatched Colored Dice (All)** | **{r2['mean_unpatched_colored_all']:.2f}** dice | **{r3['mean_unpatched_colored_all']:.2f}** dice | **{r4['mean_unpatched_colored_all']:.2f}** dice | Technical debt backlog |")
    print(f"| **Avg Ending Unpatched Colored Dice (Survivors)** | **{r2['mean_unpatched_colored_survivors']:.2f}** dice | **{r3['mean_unpatched_colored_survivors']:.2f}** dice | **{r4['mean_unpatched_colored_survivors']:.2f}** dice | Clean maintenance execution |")
    print(f"| **Avg VP Lost to Unpatched Debt (Survivors)** | **{r2['mean_unpatched_vp_lost_survivors']:.2f}** VP | **{r3['mean_unpatched_vp_lost_survivors']:.2f}** VP | **{r4['mean_unpatched_vp_lost_survivors']:.2f}** VP | Meaningful maintenance stakes |")
    print(f"| **Survivors with Unpatched Colored Dice (%)** | **{r2['survivors_with_unpatched_colored_pct']:.1f}%** | **{r3['survivors_with_unpatched_colored_pct']:.1f}%** | **{r4['survivors_with_unpatched_colored_pct']:.1f}%** | Triage pressure |")

    print("\n## 3. Bot Win Rates & Balance Distribution")
    print("| Bot Archetype | 2-Player (2P) | 3-Player (3P) | 4-Player (4P) | Target Benchmark |")
    print("| :--- | :---: | :---: | :---: | :---: |")
    all_bots = ["AdaptiveBalancedBot", "SecOpsTurtleBot", "VentureGreedBot", "AccelerationistBot"]
    for bot in all_bots:
        w2 = f"{r2['bot_win_rates'].get(bot, 0.0):.1f}%" if bot in ["AdaptiveBalancedBot", "SecOpsTurtleBot"] else "—"
        w3 = f"{r3['bot_win_rates'].get(bot, 0.0):.1f}%" if bot != "AccelerationistBot" else "—"
        w4 = f"{r4['bot_win_rates'].get(bot, 0.0):.1f}%"
        print(f"| **{bot}** | {w2} | {w3} | {w4} | ≤ 38% (4P) |")


if __name__ == "__main__":
    runs = 1000
    seed = 42
    if len(sys.argv) > 1:
        runs = int(sys.argv[1])
    if len(sys.argv) > 2:
        seed = int(sys.argv[2])

    results = run_sweep(num_runs=runs, base_seed=seed)
    print_markdown_report(results)

    # Also dump JSON telemetry
    with open("phase17_telemetry.json", "w") as f:
        json.dump(results, f, indent=2)
