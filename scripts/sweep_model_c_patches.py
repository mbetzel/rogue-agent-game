"""Monte Carlo verification sweep for Model C: End-of-Round Cleanup Cap for Patches.

Evaluates pacing, survival rates, patch economy (excess patches generated, used in P2/P3, discarded at cleanup),
and tiebreaker resolution across 2P, 3P, and 4P pods.
"""

from __future__ import annotations

import statistics
import time
from typing import Dict, List

from sim.bots import (
    AccelerationistBot,
    AdaptiveBalancedBot,
    SecOpsTurtleBot,
    VentureGreedBot,
)
from sim.config import EndGameReason, GameConfig
from sim.engine import GameEngine


def run_sweep(num_runs: int = 1000, base_seed: int = 42):
    player_counts = [2, 3, 4]
    bot_classes = [
        AdaptiveBalancedBot,
        SecOpsTurtleBot,
        VentureGreedBot,
        AccelerationistBot,
    ]

    print("==========================================================================================")
    print("Model C: End-of-Round Cleanup Cap for Patches — Verification Sweep")
    print(f"Sample size: {num_runs} runs per cell | Base Seed: {base_seed}")
    print("==========================================================================================\n")

    summary_rows = []

    for p_count in player_counts:
        t0 = time.time()
        round_counts = []
        end_reasons = {r: 0 for r in EndGameReason}
        win_counts: Dict[str, int] = {}
        winner_secrets = []
        survivor_secrets = []
        winner_patches = []
        survivor_patches = []
        tiebreaker_used_count = 0
        tiebreaker_levels = {1: 0, 2: 0, 3: 0, 4: 0}
        total_wipeouts = 0

        for run_idx in range(num_runs):
            seed = base_seed + run_idx * 13
            config = GameConfig(num_players=p_count)
            bots = [bot_classes[i % len(bot_classes)](i) for i in range(p_count)]
            engine = GameEngine(config=config, bots=bots, seed=seed)

            res = engine.run_game()
            round_counts.append(res.total_rounds)
            end_reasons[res.end_reason] = end_reasons.get(res.end_reason, 0) + 1

            if res.is_total_wipeout:
                total_wipeouts += 1
            else:
                survivors = [r for r in res.rankings if not r["is_patient_zero"]]
                if survivors:
                    winner = survivors[0]
                    win_counts[winner["bot_name"]] = win_counts.get(winner["bot_name"], 0) + 1
                    winner_secrets.append(winner["secrets"])
                    winner_patches.append(winner["patches"])

                    for s in survivors:
                        survivor_secrets.append(s["secrets"])
                        survivor_patches.append(s["patches"])

                    # Check if tiebreaker was needed between rank 1 and rank 2
                    if len(survivors) >= 2 and survivors[0]["secrets"] == survivors[1]["secrets"]:
                        tiebreaker_used_count += 1
                        if survivors[0]["money"] != survivors[1]["money"]:
                            tiebreaker_levels[1] += 1
                        elif survivors[0]["ready_colored_dice_count"] != survivors[1]["ready_colored_dice_count"]:
                            tiebreaker_levels[2] += 1
                        elif survivors[0]["patches"] != survivors[1]["patches"]:
                            tiebreaker_levels[3] += 1
                        else:
                            tiebreaker_levels[4] += 1

        elapsed = time.time() - t0
        mean_rounds = statistics.mean(round_counts)
        stdev_rounds = statistics.stdev(round_counts) if len(round_counts) > 1 else 0.0
        sing_pct = (end_reasons.get(EndGameReason.SINGULARITY, 0) / num_runs) * 100.0
        pz_pct = (end_reasons.get(EndGameReason.PATIENT_ZERO, 0) / num_runs) * 100.0
        wipeout_pct = (total_wipeouts / num_runs) * 100.0
        mean_win_sec = statistics.mean(winner_secrets) if winner_secrets else 0.0
        mean_surv_sec = statistics.mean(survivor_secrets) if survivor_secrets else 0.0
        mean_win_patches = statistics.mean(winner_patches) if winner_patches else 0.0
        mean_surv_patches = statistics.mean(survivor_patches) if survivor_patches else 0.0
        valid_games = max(1, num_runs - total_wipeouts)
        tb_rate = (tiebreaker_used_count / valid_games) * 100.0

        sorted_bots = sorted(win_counts.items(), key=lambda x: x[1], reverse=True)
        total_wins = sum(win_counts.values()) or 1
        lead_bot = f"{sorted_bots[0][0]} ({sorted_bots[0][1]/total_wins*100:.1f}%)" if sorted_bots else "N/A"

        row = {
            "p_count": p_count,
            "mean_rounds": f"{mean_rounds:.2f} +/- {stdev_rounds:.2f}",
            "sing_pct": f"{sing_pct:.1f}%",
            "pz_pct": f"{pz_pct:.1f}%",
            "wipeout_pct": f"{wipeout_pct:.1f}%",
            "mean_win_sec": f"{mean_win_sec:.2f}",
            "mean_surv_sec": f"{mean_surv_sec:.2f}",
            "mean_win_patches": f"{mean_win_patches:.2f}",
            "mean_surv_patches": f"{mean_surv_patches:.2f}",
            "tb_rate": f"{tb_rate:.1f}%",
            "tb_breakdown": f"L1($):{tiebreaker_levels[1]} L2(Dice):{tiebreaker_levels[2]} L3(Wrench):{tiebreaker_levels[3]} L4(Rel):{tiebreaker_levels[4]}",
            "lead_bot": lead_bot,
            "elapsed": f"{elapsed:.1f}s",
        }
        summary_rows.append(row)

    print("\n==========================================================================================")
    print("TELEMETRY SUMMARY TABLE (Model C Baseline)")
    print("==========================================================================================")
    header = (
        f"| {'Pod':<4} | {'Mean Rounds':<15} | {'Sing %':<8} | {'PZ %':<8} | {'Wipeout %':<10} | "
        f"{'Win Sec':<8} | {'Surv Sec':<8} | {'Win 🔧':<7} | {'Surv 🔧':<7} | {'TB %':<7} | "
        f"{'Lead Bot':<30} |"
    )
    sep = "|" + "-+-".join(["-" * len(c) for c in header.split("|")[1:-1]]) + "|"
    print(header)
    print(sep)
    for r in summary_rows:
        print(
            f"| {r['p_count']}P   | {r['mean_rounds']:<15} | {r['sing_pct']:<8} | {r['pz_pct']:<8} | {r['wipeout_pct']:<10} | "
            f"{r['mean_win_sec']:<8} | {r['mean_surv_sec']:<8} | {r['mean_win_patches']:<7} | {r['mean_surv_patches']:<7} | {r['tb_rate']:<7} | "
            f"{r['lead_bot']:<30} |"
        )
    print("==========================================================================================\n")
    print("Tiebreaker Level Breakdown:")
    for r in summary_rows:
        print(f"  {r['p_count']}P: {r['tb_breakdown']}")
    print("==========================================================================================")


if __name__ == "__main__":
    run_sweep(num_runs=1000, base_seed=42)
