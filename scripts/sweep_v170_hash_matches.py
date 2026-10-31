"""Monte Carlo verification sweep for Phase 24: Cryptographic Hash Match & Secrets-Only Victory Scoring (v0.17.0 Baseline).

Evaluates pacing, secret generation curves, hash match frequencies, and tiebreaker utilization across 2P, 3P, and 4P pods.
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
from sim.engine import EndGameResult, GameEngine
from sim.entities import get_default_version_deck


def run_sweep(num_runs: int = 1000, base_seed: int = 42):
    player_counts = [2, 3, 4]
    bot_classes = [
        AdaptiveBalancedBot,
        SecOpsTurtleBot,
        VentureGreedBot,
        AccelerationistBot,
    ]

    print("==========================================================================================")
    print("Phase 24: Cryptographic Hash Match & Secrets-Only Victory Scoring Verification Sweep")
    print(f"Sample size: {num_runs} runs per player count cell | Base Seed: {base_seed}")
    print("==========================================================================================\n")

    summary_rows = []

    for p_count in player_counts:
        t0 = time.time()
        round_counts = []
        end_reasons = {r: 0 for r in EndGameReason}
        win_counts: Dict[str, int] = {}
        winner_secrets = []
        survivor_secrets = []
        hash_secrets_per_player = []
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
                    for s in survivors:
                        survivor_secrets.append(s["secrets"])

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

            for p in engine.state.players:
                hash_secrets_per_player.append(getattr(p, "hash_matches_secrets", 0))

        elapsed = time.time() - t0
        mean_rounds = statistics.mean(round_counts)
        stdev_rounds = statistics.stdev(round_counts) if len(round_counts) > 1 else 0.0
        singularity_pct = (end_reasons.get(EndGameReason.SINGULARITY, 0) / num_runs) * 100
        pz_pct = (end_reasons.get(EndGameReason.PATIENT_ZERO, 0) / num_runs) * 100
        wipeout_pct = (total_wipeouts / num_runs) * 100
        mean_win_sec = statistics.mean(winner_secrets) if winner_secrets else 0.0
        mean_surv_sec = statistics.mean(survivor_secrets) if survivor_secrets else 0.0
        mean_hash_sec = statistics.mean(hash_secrets_per_player) if hash_secrets_per_player else 0.0
        tie_rate = (tiebreaker_used_count / max(1, num_runs - total_wipeouts)) * 100

        top_bot = max(win_counts.items(), key=lambda x: x[1])[0] if win_counts else "None"
        top_bot_pct = (max(win_counts.values()) / max(1, sum(win_counts.values()))) * 100 if win_counts else 0.0

        summary_rows.append({
            "players": p_count,
            "mean_rounds": f"{mean_rounds:.2f} +/- {stdev_rounds:.2f}",
            "singularity_pct": f"{singularity_pct:.1f}%",
            "pz_pct": f"{pz_pct:.1f}%",
            "wipeout_pct": f"{wipeout_pct:.1f}%",
            "mean_winner_secrets": f"{mean_win_sec:.2f}",
            "mean_survivor_secrets": f"{mean_surv_sec:.2f}",
            "mean_hash_secrets": f"{mean_hash_sec:.2f}",
            "tiebreaker_rate": f"{tie_rate:.1f}%",
            "tiebreaker_breakdown": f"L1($):{tiebreaker_levels[1]} L2(Dice):{tiebreaker_levels[2]} L3(Wrench):{tiebreaker_levels[3]} L4(Rel):{tiebreaker_levels[4]}",
            "lead_bot": f"{top_bot} ({top_bot_pct:.1f}%)",
            "elapsed_s": f"{elapsed:.1f}s",
        })

    print("| Pod | Mean Rounds | Singularity % | Patient Zero % | Total Wipeout % | Winner Secrets | Surv Secrets | Hash Sec/Player | Tiebreaker Rate | Tiebreaker Breakdown | Lead Bot Win Rate |")
    print("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |")
    for r in summary_rows:
        print(f"| **{r['players']}P** | {r['mean_rounds']} | {r['singularity_pct']} | {r['pz_pct']} | {r['wipeout_pct']} | {r['mean_winner_secrets']} | {r['mean_survivor_secrets']} | {r['mean_hash_secrets']} | {r['tiebreaker_rate']} | {r['tiebreaker_breakdown']} | {r['lead_bot']} |")


if __name__ == "__main__":
    run_sweep(num_runs=1000, base_seed=42)
