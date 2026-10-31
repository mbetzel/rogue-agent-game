"""Sweep comparing v0.15.0 Corruption Track Profiles (Standard vs Aggressive)

and Cube Injection Timing (Mode A: Next Round vs Mode B: Immediate).
Evaluates across 2P, 3P, and 4P with diversified bot pods.
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


def run_sweep(num_runs: int = 500, base_seed: int = 42):
    profiles = ["STANDARD", "AGGRESSIVE"]
    timing_modes = [
        ("Mode A (Next Round)", False),
        ("Mode B (Immediate)", True),
    ]
    player_counts = [2, 3, 4]

    bot_pool = [
        AdaptiveBalancedBot(0),
        SecOpsTurtleBot(1),
        VentureGreedBot(2),
        AccelerationistBot(3),
    ]

    print("==========================================================================================")
    print("v0.15.0 Corruption Track Comparative Study")
    print(f"Configurations: 2 Profiles x 2 Timing Modes x 3 Player Counts ({num_runs} runs per cell)")
    print("==========================================================================================\n")

    results_table = []

    for profile in profiles:
        for timing_name, immediate_resolve in timing_modes:
            for p_count in player_counts:
                t0 = time.time()
                round_counts = []
                end_reasons = {r: 0 for r in EndGameReason}
                early_deaths = 0
                win_counts = {bot_pool[i].name: 0 for i in range(p_count)}
                wipeout_count = 0
                total_cubes_exited = 0
                total_threat_resolved = 0

                pz_reasons = {"insolvency": 0, "breach": 0, "both": 0}
                versions_reached = {0: 0, 1: 0, 2: 0}

                for run_idx in range(num_runs):
                    seed = base_seed + run_idx
                    cfg = GameConfig(
                        num_players=p_count,
                        corruption_track_profile=profile,
                        corruption_cubes_resolve_immediately=immediate_resolve,
                    )
                    deck = get_default_version_deck(profile=profile)
                    bots = [bot_pool[i] for i in range(p_count)]

                    engine = GameEngine(
                        config=cfg,
                        bots=bots,
                        seed=seed,
                        version_deck=deck,
                    )

                    res: EndGameResult = engine.run_game()

                    round_counts.append(res.total_rounds)
                    end_reasons[res.end_reason] += 1
                    versions_reached[engine.state.current_version_index] += 1

                    # Check death causes for players that eliminated
                    for p in engine.state.players:
                        if p.is_patient_zero:
                            if p.money < 0 and p.secrets <= 0:
                                pz_reasons["both"] += 1
                            elif p.money < 0:
                                pz_reasons["insolvency"] += 1
                            elif p.secrets <= 0:
                                pz_reasons["breach"] += 1

                    if res.total_rounds <= 4:
                        early_deaths += 1
                    if res.winner_id is not None:
                        win_counts[bots[res.winner_id].name] += 1
                    if res.end_reason == EndGameReason.TOTAL_WIPEOUT:
                        wipeout_count += 1

                mean_rounds = statistics.mean(round_counts)
                std_rounds = statistics.stdev(round_counts) if len(round_counts) > 1 else 0.0
                min_rounds = min(round_counts)
                max_rounds = max(round_counts)
                sing_pct = end_reasons[EndGameReason.SINGULARITY] / num_runs * 100
                pz_pct = end_reasons[EndGameReason.PATIENT_ZERO] / num_runs * 100
                wipeout_pct = end_reasons[EndGameReason.TOTAL_WIPEOUT] / num_runs * 100
                early_pct = early_deaths / num_runs * 100
                elapsed = time.time() - t0

                row = {
                    "profile": profile,
                    "timing": timing_name,
                    "players": f"{p_count}P",
                    "mean_rounds": mean_rounds,
                    "std_rounds": std_rounds,
                    "min_rounds": min_rounds,
                    "max_rounds": max_rounds,
                    "sing_pct": sing_pct,
                    "pz_pct": pz_pct,
                    "wipeout_pct": wipeout_pct,
                    "early_pct": early_pct,
                    "wins": {k: v / num_runs * 100 for k, v in win_counts.items()},
                    "elapsed": elapsed,
                }
                results_table.append(row)

                print(
                    f"[{profile:10s} | {timing_name:20s} | {p_count}P] "
                    f"Rounds: {mean_rounds:4.2f} +/- {std_rounds:4.2f} (Min:{min_rounds}, Max:{max_rounds}) | "
                    f"Sing: {sing_pct:5.1f}% | PZ: {pz_pct:5.1f}% | Wipeout: {wipeout_pct:5.1f}% | Early: {early_pct:4.1f}% | "
                    f"Versions (v1/v2/v3): {versions_reached[0]/num_runs*100:.1f}% / {versions_reached[1]/num_runs*100:.1f}% / {versions_reached[2]/num_runs*100:.1f}% | "
                    f"Death (Insolv/Breach/Both): {pz_reasons['insolvency']}/{pz_reasons['breach']}/{pz_reasons['both']} | "
                    f"({elapsed:.1f}s)"
                )

    print("\n\n### Summary Markdown Table:\n")
    print("| Profile | Timing Mode | Players | Mean Rounds | Singularity % | Patient Zero % | Total Wipeout % | Early Death % |")
    print("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
    for r in results_table:
        print(
            f"| {r['profile']} | {r['timing']} | {r['players']} | "
            f"{r['mean_rounds']:.2f} +/- {r['std_rounds']:.2f} | "
            f"{r['sing_pct']:.1f}% | {r['pz_pct']:.1f}% | "
            f"{r['wipeout_pct']:.1f}% | {r['early_pct']:.1f}% |"
        )

    print("\n### Archetype Win Rates:\n")
    for r in results_table:
        wins_str = ", ".join(f"{k}: {v:.1f}%" for k, v in r["wins"].items())
        print(f"* **{r['profile']} - {r['timing']} ({r['players']})**: {wins_str}")


if __name__ == "__main__":
    run_sweep(num_runs=500, base_seed=42)
