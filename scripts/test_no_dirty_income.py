"""Test scenarios with Low/Zero Dirty Income (simulating cautious human prototype play).

Measures how defense scales against the slow cube economy when players do not accelerate the compiler.
"""

from __future__ import annotations

import random
import statistics
from typing import Any, Dict, List, Optional

from sim.bots import (
    AdaptiveBalancedBot,
    SecOpsTurtleBot,
)
from sim.config import CubeColor, DieColor, GameConfig, ShieldColor
from sim.engine import GameEngine
from sim.entities import Die, Face, VariantCard, create_gray_die, create_white_die, get_random_setup
import sim.entities
import sim.engine.phase3_ops

from scripts.compare_block1_vs_block2 import create_colored_die_block1, _ORIGINAL_CREATE_COLORED_DIE


def run_no_dirty_income_sweep(num_players: int = 4, num_runs: int = 500, candidate: bool = False):
    if candidate:
        sim.entities.create_colored_die = create_colored_die_block1
        sim.engine.phase3_ops.create_colored_die = create_colored_die_block1
    else:
        sim.entities.create_colored_die = _ORIGINAL_CREATE_COLORED_DIE
        sim.engine.phase3_ops.create_colored_die = _ORIGINAL_CREATE_COLORED_DIE

    # All bots are SecOpsTurtle or AdaptiveBalanced with Dirty Income disabled
    # Let's subclass to ensure ZERO dirty income
    class NoDirtyAdaptiveBot(AdaptiveBalancedBot):
        def take_phase3_actions(self, player_state, game_state, rng):
            plan = super().take_phase3_actions(player_state, game_state, rng)
            plan.take_dirty_income = False
            if plan.cipher_mode == "DIRTY_INCOME":
                plan.cipher_mode = "BUY_FREE_DIE"
                plan.cipher_free_die_color = DieColor.BLUE
            return plan

    class NoDirtyTurtleBot(SecOpsTurtleBot):
        def take_phase3_actions(self, player_state, game_state, rng):
            plan = super().take_phase3_actions(player_state, game_state, rng)
            plan.take_dirty_income = False
            return plan

    match_durations: List[int] = []
    end_reasons = {}
    winning_scores = []
    survivor_scores = []
    survivor_secrets = []
    survivor_unpatched = []
    v1_rounds = []
    
    # Overkill / surplus shields tracking
    total_shields_rolled = []
    total_atk_exited = []
    wasted_shields_ratio = []

    for run_idx in range(num_runs):
        seed = 100 + run_idx
        config = GameConfig(num_players=num_players)
        # 4 Cautious human-style bots
        bots = [
            NoDirtyAdaptiveBot(0),
            NoDirtyTurtleBot(1),
            NoDirtyAdaptiveBot(2),
            NoDirtyTurtleBot(3),
        ][:num_players]

        rng_setup = random.Random(seed * 17)
        variant_cards, version_deck = get_random_setup(rng_setup)

        engine = GameEngine(
            config=config,
            bots=bots,
            seed=seed,
            variant_cards=variant_cards,
            version_deck=version_deck,
        )

        v1_end_round = None

        while not engine.state.game_over:
            if v1_end_round is None and engine.state.active_version.version_str != "v1.0":
                v1_end_round = engine.state.current_round - 1

            tel = engine.run_round()
            ex = tel.exited_cubes
            atk_sum = ex.get(CubeColor.RED, 0) + ex.get(CubeColor.BLUE, 0) + ex.get(CubeColor.GREEN, 0)
            total_atk_exited.append(atk_sum)

        if v1_end_round is None:
            v1_end_round = engine.state.current_round
        v1_rounds.append(v1_end_round)

        res = engine.evaluate_end_game()
        match_durations.append(res.total_rounds)
        end_reasons[res.end_reason] = end_reasons.get(res.end_reason, 0) + 1

        if res.rankings:
            w = res.rankings[0]
            winning_scores.append(w["portfolio_value"] if not res.is_total_wipeout else w["net_score"])

        for r in res.rankings:
            if not r["is_patient_zero"]:
                survivor_scores.append(r["portfolio_value"])
                survivor_secrets.append(r["secrets"])
                survivor_unpatched.append(r["unpatched_colored_dice_count"])

    # Restore
    sim.entities.create_colored_die = _ORIGINAL_CREATE_COLORED_DIE
    sim.engine.phase3_ops.create_colored_die = _ORIGINAL_CREATE_COLORED_DIE

    return {
        "avg_duration": round(statistics.mean(match_durations), 2),
        "v1_duration": round(statistics.mean(v1_rounds), 2),
        "avg_atk_cubes_exited": round(statistics.mean(total_atk_exited), 2),
        "singularity_pct": round((end_reasons.get(sim.config.EndGameReason.SINGULARITY, 0) / num_runs) * 100, 1),
        "patient_zero_pct": round((end_reasons.get(sim.config.EndGameReason.PATIENT_ZERO, 0) / num_runs) * 100, 1),
        "total_wipeout_pct": round((end_reasons.get(sim.config.EndGameReason.TOTAL_WIPEOUT, 0) / num_runs) * 100, 1),
        "avg_survivor_secrets": round(statistics.mean(survivor_secrets), 2) if survivor_secrets else 0,
        "avg_survivor_score": round(statistics.mean(survivor_scores), 1) if survivor_scores else 0,
        "avg_unpatched_dice": round(statistics.mean(survivor_unpatched), 2) if survivor_unpatched else 0,
    }


def main():
    print("=" * 80)
    print("TESTING CAUTIOUS / ZERO DIRTY INCOME ENVIRONMENT (Prototype Experience)")
    print("=" * 80)

    for p in [4, 3, 2]:
        print(f"\n--- {p} Players (Cautious / Zero Dirty Income, N=500) ---")
        b = run_no_dirty_income_sweep(num_players=p, num_runs=500, candidate=False)
        c = run_no_dirty_income_sweep(num_players=p, num_runs=500, candidate=True)

        print(f"{'Metric':<35} | {'Baseline (Block 2)':<18} | {'Candidate (Block 1)':<18} | {'Delta':<10}")
        print("-" * 88)
        for k in b.keys():
            vb = b[k]
            vc = c[k]
            delta = f"{vc - vb:+.2f}" if isinstance(vb, (int, float)) else ""
            print(f"{k:<35} | {str(vb):<18} | {str(vc):<18} | {delta:<10}")


if __name__ == "__main__":
    main()
