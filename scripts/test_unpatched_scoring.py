"""Simulate and compare:
1. Baseline Scoring: all owned colored dice score 3 VP each.
2. Active-Only Scoring: only Ready colored dice score 3 VP each; Unpatched colored dice score 0 VP.
"""

from __future__ import annotations

import json
import os
import random
import statistics
import sys
from collections import defaultdict
from typing import Any, Dict, List

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from sim.bots import (
    AccelerationistBot,
    AdaptiveBalancedBot,
    SecOpsTurtleBot,
    VentureGreedBot,
)
from sim.config import DieColor, GameConfig
from sim.engine import GameEngine
from sim.entities import (
    ArchetypeCode,
    get_archetype_by_code,
    get_default_variant_cards,
    get_default_version_deck,
    get_random_setup,
)


def run_scoring_comparison(num_runs: int = 1500, base_seed: int = 200):
    results = {}

    for num_players in [2, 3, 4]:
        baseline_winning_scores = []
        proposed_winning_scores = []
        vp_lost_to_unpatched = []
        unpatched_colored_dice_counts = []
        winner_changes = 0

        # Disparity & cash impact
        cash_left = []
        
        # Test across runs
        for i in range(num_runs):
            seed = base_seed + i
            config = GameConfig(num_players=num_players)

            if num_players == 2:
                bots = [AdaptiveBalancedBot(0), SecOpsTurtleBot(1)]
            elif num_players == 3:
                bots = [AdaptiveBalancedBot(0), SecOpsTurtleBot(1), VentureGreedBot(2)]
            else:
                bots = [
                    AdaptiveBalancedBot(0),
                    SecOpsTurtleBot(1),
                    VentureGreedBot(2),
                    AccelerationistBot(3),
                ]

            rng_setup = random.Random(seed * 17)
            variant_cards, version_deck = get_random_setup(rng_setup)

            engine = GameEngine(
                config=config,
                bots=bots,
                seed=seed,
                variant_cards=variant_cards,
                version_deck=version_deck,
            )
            res = engine.run_game()

            # Compute scores under both rules for surviving players
            # (or for all players if total wipeout)
            base_scores = []
            prop_scores = []

            for p in engine.state.players:
                # Baseline scoring
                sec_vp = max(0, p.secrets) * config.vp_per_secret
                cash_vp = max(0, p.money) // config.vp_cash_divisor
                all_colored_vp = sum(
                    config.vp_per_die.get(d.color, 0)
                    for d in (p.ready_dice + p.unpatched_dice)
                )
                b_score = sec_vp + all_colored_vp + cash_vp

                # Proposed scoring: only ready colored dice score
                ready_colored_vp = sum(
                    config.vp_per_die.get(d.color, 0)
                    for d in p.ready_dice
                )
                p_score = sec_vp + ready_colored_vp + cash_vp

                unpatched_colored = sum(
                    1 for d in p.unpatched_dice if d.color != DieColor.GRAY
                )
                lost_vp = all_colored_vp - ready_colored_vp

                base_scores.append((b_score, p.player_id, p.is_patient_zero, p.secrets, p.money))
                prop_scores.append((p_score, p.player_id, p.is_patient_zero, p.secrets, p.money))
                
                if not p.is_patient_zero:
                    vp_lost_to_unpatched.append(lost_vp)
                    unpatched_colored_dice_counts.append(unpatched_colored)
                    cash_left.append(p.money)

            # Determine winners under baseline vs proposed
            # Filter non-PZ if any survived
            surv_base = [s for s in base_scores if not s[2]]
            surv_prop = [s for s in prop_scores if not s[2]]

            candidates_base = surv_base if surv_base else base_scores
            candidates_prop = surv_prop if surv_prop else prop_scores

            candidates_base.sort(key=lambda x: (x[0], x[3], x[4]), reverse=True)
            candidates_prop.sort(key=lambda x: (x[0], x[3], x[4]), reverse=True)

            winner_base = candidates_base[0]
            winner_prop = candidates_prop[0]

            baseline_winning_scores.append(winner_base[0])
            proposed_winning_scores.append(winner_prop[0])

            if winner_base[1] != winner_prop[1]:
                winner_changes += 1

        results[f"{num_players}P"] = {
            "num_players": num_players,
            "runs": num_runs,
            "mean_baseline_winning_score": round(statistics.mean(baseline_winning_scores), 2),
            "mean_proposed_winning_score": round(statistics.mean(proposed_winning_scores), 2),
            "mean_vp_lost_per_survivor": round(statistics.mean(vp_lost_to_unpatched), 2),
            "mean_unpatched_colored_dice_per_survivor": round(statistics.mean(unpatched_colored_dice_counts), 2),
            "pct_survivors_with_unpatched_colored_dice": round(
                sum(1 for u in unpatched_colored_dice_counts if u > 0) / len(unpatched_colored_dice_counts) * 100, 1
            ),
            "winner_flip_rate_pct": round(winner_changes / num_runs * 100, 1),
        }

    print("SCORES_JSON_START")
    print(json.dumps(results, indent=2))
    print("SCORES_JSON_END")


if __name__ == "__main__":
    run_scoring_comparison()
