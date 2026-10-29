"""Detailed telemetry measuring:
1. Dice worn per round (Ready -> Unpatched)
2. Damage taken per round by color (Red $, Blue Secrets, Green demotions)
3. Total attack cubes exited per round vs shields rolled
4. Shield surplus / wasted shields per round
5. How often a single die absorbs multiple cubes (the Block 2 phenomenon)
"""

from __future__ import annotations

import random
import statistics
from typing import Any, Dict, List, Optional

from sim.bots import (
    AccelerationistBot,
    AdaptiveBalancedBot,
    SecOpsTurtleBot,
    VentureGreedBot,
)
from sim.config import CubeColor, DieColor, GameConfig, ShieldColor
from sim.engine import GameEngine
from sim.entities import Die, Face, VariantCard, create_gray_die, create_white_die, get_random_setup
import sim.entities
import sim.engine.phase3_ops

from scripts.compare_block1_vs_block2 import create_colored_die_block1, _ORIGINAL_CREATE_COLORED_DIE


def run_detailed_telemetry(num_players: int = 4, num_runs: int = 500, candidate: bool = False):
    if candidate:
        sim.entities.create_colored_die = create_colored_die_block1
        sim.engine.phase3_ops.create_colored_die = create_colored_die_block1
    else:
        sim.entities.create_colored_die = _ORIGINAL_CREATE_COLORED_DIE
        sim.engine.phase3_ops.create_colored_die = _ORIGINAL_CREATE_COLORED_DIE

    # Track metrics
    match_durations: List[int] = []
    
    # Cube exits
    red_exited: List[int] = []
    blue_exited: List[int] = []
    green_exited: List[int] = []
    total_atk_exited: List[int] = []

    # Player round tracking
    red_secrets_lost_total: List[int] = []
    blue_secrets_lost_total: List[int] = []
    red_cash_lost_total: List[int] = []
    green_demotions_total: List[int] = []

    total_damage_events = 0
    total_player_rounds = 0
    clean_defense_player_rounds = 0

    dice_worn_per_player_round: List[int] = []
    colored_dice_worn_per_player_round: List[int] = []
    
    # Track ending dice profile
    ready_colored_dice_end: List[int] = []
    unpatched_colored_dice_end: List[int] = []
    total_colored_dice_bought: List[int] = []

    for run_idx in range(num_runs):
        seed = 42 + run_idx
        config = GameConfig(num_players=num_players)
        bots = [
            AdaptiveBalancedBot(0),
            SecOpsTurtleBot(1),
            VentureGreedBot(2),
            AccelerationistBot(3),
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

        while not engine.state.game_over:
            # Snapshot player state before Phase 2
            before_ready = {p.player_id: len(p.ready_dice) for p in engine.state.players}
            before_unpatched = {p.player_id: len(p.unpatched_dice) for p in engine.state.players}
            before_secrets = {p.player_id: p.secrets for p in engine.state.players}
            before_money = {p.player_id: p.money for p in engine.state.players}

            tel = engine.run_round()

            ex = tel.exited_cubes
            r_ex = ex.get(CubeColor.RED, 0)
            b_ex = ex.get(CubeColor.BLUE, 0)
            g_ex = ex.get(CubeColor.GREEN, 0)
            tot_atk = r_ex + b_ex + g_ex

            red_exited.append(r_ex)
            blue_exited.append(b_ex)
            green_exited.append(g_ex)
            total_atk_exited.append(tot_atk)

            # Compare after Phase 2 (snapshots are taken in Phase 2 Step 2C)
            for snap in tel.player_snapshots:
                pid = snap["player_id"]
                total_player_rounds += 1
                
                # Check how many dice moved to unpatched
                # Note: unpatched dice count includes worn dice + dirty income backlash (Phase 3)
                # But snap is taken right after Step 2B damage!
                worn_in_p2 = snap["unpatched_dice_count"] - before_unpatched[pid]
                dice_worn_per_player_round.append(max(0, worn_in_p2))

                # Check secret loss
                sec_lost = before_secrets[pid] - snap["secrets"]
                cash_lost = before_money[pid] - snap["money"]
                
                if sec_lost > 0 or cash_lost > 0:
                    total_damage_events += 1
                else:
                    clean_defense_player_rounds += 1

        match_durations.append(engine.state.current_round)

        for p in engine.state.players:
            ready_colored = sum(1 for d in p.ready_dice if d.color in (DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW, DieColor.PURPLE))
            unpatched_colored = sum(1 for d in p.unpatched_dice if d.color in (DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW, DieColor.PURPLE))
            ready_colored_dice_end.append(ready_colored)
            unpatched_colored_dice_end.append(unpatched_colored)
            total_colored_dice_bought.append(ready_colored + unpatched_colored)

    # Restore original
    sim.entities.create_colored_die = _ORIGINAL_CREATE_COLORED_DIE
    sim.engine.phase3_ops.create_colored_die = _ORIGINAL_CREATE_COLORED_DIE

    return {
        "avg_duration": round(statistics.mean(match_durations), 2),
        "avg_atk_exited_per_round": round(statistics.mean(total_atk_exited), 2),
        "avg_red_exited": round(statistics.mean(red_exited), 2),
        "avg_blue_exited": round(statistics.mean(blue_exited), 2),
        "avg_green_exited": round(statistics.mean(green_exited), 2),
        "avg_dice_worn_per_player_round": round(statistics.mean(dice_worn_per_player_round), 2),
        "clean_defense_rate_pct": round((clean_defense_player_rounds / total_player_rounds) * 100.0, 1),
        "damage_event_rate_pct": round((total_damage_events / total_player_rounds) * 100.0, 1),
        "avg_colored_dice_owned": round(statistics.mean(total_colored_dice_bought), 2),
        "avg_ready_colored_dice": round(statistics.mean(ready_colored_dice_end), 2),
        "avg_unpatched_colored_dice": round(statistics.mean(unpatched_colored_dice_end), 2),
    }


def main():
    print("=" * 80)
    print("IN-DEPTH CUBE ECONOMY & WEAR TELEMETRY")
    print("=" * 80)

    for p in [4, 3, 2]:
        print(f"\n--- {p}-PLAYER POD (N=500 matches) ---")
        b = run_detailed_telemetry(num_players=p, num_runs=500, candidate=False)
        c = run_detailed_telemetry(num_players=p, num_runs=500, candidate=True)

        print(f"{'Metric':<40} | {'Baseline (Block 2)':<18} | {'Candidate (Block 1)':<18} | {'Delta':<10}")
        print("-" * 92)
        for k in b.keys():
            vb = b[k]
            vc = c[k]
            delta = f"{vc - vb:+.2f}" if isinstance(vb, (int, float)) else ""
            print(f"{k:<40} | {str(vb):<18} | {str(vc):<18} | {delta:<10}")


if __name__ == "__main__":
    main()
