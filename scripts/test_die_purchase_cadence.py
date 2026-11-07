"""Cadence Analysis: How many rounds until players can buy their second die?

Tests:
1. Current pricing tier ($5-$7 market, $4-$6 reserve)
2. Leaner pricing tier ($4-$5 market, $4 reserve)
3. Flat pricing tier ($4 flat market, $3 reserve)
Assuming all players buy a die on Turn 1 (with $6 starting cash, Meridian $8).
Tracks rounds until 2nd die, 3rd die, pipeline throughput, and economic stalling.
"""

import sys
import os
import random
import statistics
from collections import defaultdict
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sim.config import GameConfig, DieColor, CubeColor
from sim.engine.core import GameEngine
from sim.entities import (
    Die,
    create_gray_die,
    create_colored_die,
    COMPANIES,
    WHITE_HATS,
    CompanyCode,
    WhiteHatCode,
    CANONICAL_COMPANY_FOR_OPERATIVE,
    get_random_setup,
)
from sim.bots import (
    AdaptiveBalancedBot,
    SecOpsTurtleBot,
    VentureGreedBot,
    AccelerationistBot,
)


def run_cadence_experiment(
    pricing_mode: str = "CURRENT",  # "CURRENT", "LEAN" ($4-$5), "CHEAP" ($4 flat)
    n_matches: int = 1000,
):
    rng = random.Random(42)
    
    rounds_to_second_die = []
    rounds_to_third_die = []
    total_dice_bought_by_end = []
    cash_at_end_of_round = defaultdict(list)
    dice_in_development_by_round = defaultdict(list)
    ready_dice_by_round = defaultdict(list)
    stalled_players = 0  # Players who never buy a 2nd die before game ends
    
    for match_idx in range(n_matches):
        bots = [
            AdaptiveBalancedBot(0),
            SecOpsTurtleBot(1),
            VentureGreedBot(2),
            AccelerationistBot(3),
        ]
        rng.shuffle(bots)
        
        cfg = GameConfig.legacy_v035(
            num_players=4,
            starting_money=6,
            starting_gray_dice=3,
            enable_corporate_asymmetry=True,
        )
        
        variants, version_deck = get_random_setup(rng, profile="STANDARD")
        
        # Adjust variant prices if testing LEAN or CHEAP
        if pricing_mode == "LEAN":
            # Red: R1 $5, R2 $5, R3 $4
            # Blue: B1 $5, B2 $5, B3 $4
            # Green: G1 $5, G2 $4, G3 $4
            # Yellow: Y1 $5, Y2 $5, Y3 $4
            lean_costs = {
                "R1": 5, "R2": 5, "R3": 4,
                "B1": 5, "B2": 5, "B3": 4,
                "G1": 5, "G2": 4, "G3": 4,
                "Y1": 5, "Y2": 5, "Y3": 4,
            }
            # Recreate variants with lean costs
            new_variants = {}
            for col, v in variants.items():
                cost = lean_costs.get(v.code, 4)
                # create updated variant card with new cost
                from dataclasses import replace
                new_variants[col] = replace(v, cost=cost)
            variants = new_variants
            
        elif pricing_mode == "CHEAP":
            new_variants = {}
            for col, v in variants.items():
                from dataclasses import replace
                new_variants[col] = replace(v, cost=4)
            variants = new_variants

        wh_pool = list(WHITE_HATS.values())
        rng.shuffle(wh_pool)
        selected_wh = wh_pool[:4]
        selected_comp = [COMPANIES[CANONICAL_COMPANY_FOR_OPERATIVE[wh.code]] for wh in selected_wh]

        engine = GameEngine(
            config=cfg,
            bots=bots,
            seed=rng.randint(0, 1000000000),
            variant_cards=variants,
            version_deck=version_deck,
            companies=selected_comp,
            white_hats=selected_wh,
        )

        # Initialize players with 3 Gray + 1 Purple
        for i, p in enumerate(engine.state.players):
            p.ready_for_release_dice = [create_gray_die(100 + j) for j in range(3)]
            purple_die = create_colored_die(
                DieColor.PURPLE,
                200 + i,
                reserve_cost=4 if pricing_mode != "CURRENT" else p.get_purple_reserve_cost(),
            )
            p.ready_for_release_dice.append(purple_die)
            p.personal_purple_reserve = 1
            
            # Meridian starts with $8, others with $6
            comp_cash = 2 if (p.company and p.company.code == CompanyCode.MERIDIAN) else 0
            p.money = 6 + comp_cash
            p.research_tokens = 2 if (p.company and p.company.code == CompanyCode.HELIX) else 0

        # Player purchase tracking: player_id -> [round_of_buy1, round_of_buy2, ...]
        purchase_rounds = defaultdict(list)
        
        # Track initial die counts (1 colored die: Purple)
        initial_colored = {p.player_id: 1 for p in engine.state.players}

        while not engine.state.game_over and engine.state.current_round <= 15:
            r = engine.state.current_round
            engine.run_round()
            
            for p in engine.state.players:
                if p.is_patient_zero:
                    continue
                cash_at_end_of_round[r].append(p.money)
                dice_in_development_by_round[r].append(len(p.glitched_dice) + len(p.scanned_dice))
                ready_dice_by_round[r].append(len(p.ready_for_release_dice))
                
                # Check how many colored dice owned
                all_dice = p.ready_for_release_dice + p.in_production_dice + p.glitched_dice + p.scanned_dice
                colored = len([d for d in all_dice if d.color not in (DieColor.GRAY, DieColor.WHITE)])
                bought_so_far = colored - initial_colored[p.player_id]
                
                # If newly bought dice
                current_recorded = len(purchase_rounds[p.player_id])
                if bought_so_far > current_recorded:
                    for _ in range(bought_so_far - current_recorded):
                        purchase_rounds[p.player_id].append(r)

        # After match, record player metrics
        for p in engine.state.players:
            buys = purchase_rounds[p.player_id]
            total_dice_bought_by_end.append(len(buys))
            if len(buys) >= 2:
                # Delta between buy 1 and buy 2
                delta = buys[1] - buys[0]
                rounds_to_second_die.append(delta)
            elif len(buys) == 1:
                # Bought 1 die, never bought a 2nd die
                stalled_players += 1
            if len(buys) >= 3:
                rounds_to_third_die.append(buys[2] - buys[1])

    print(f"\n========================================================")
    print(f"CADENCE RESULTS: Pricing Mode = {pricing_mode}")
    print(f"========================================================")
    print(f"Matches: {n_matches} | Total Players: {n_matches * 4}")
    print(f"Players who bought at least 1 die: {len([x for x in total_dice_bought_by_end if x >= 1])} ({len([x for x in total_dice_bought_by_end if x >= 1])/(n_matches*4)*100:.1f}%)")
    print(f"Players who bought at least 2 dice: {len(rounds_to_second_die)} ({len(rounds_to_second_die)/(n_matches*4)*100:.1f}%)")
    print(f"Players who STALLED at exactly 1 die: {stalled_players} ({stalled_players/(n_matches*4)*100:.1f}%)")
    if rounds_to_second_die:
        print(f"Average rounds between 1st die and 2nd die: {statistics.mean(rounds_to_second_die):.2f} rounds (Median: {statistics.median(rounds_to_second_die)}, StdDev: {statistics.stdev(rounds_to_second_die):.2f})")
        from collections import Counter
        dist = Counter(rounds_to_second_die)
        print("  Distribution of rounds to 2nd die:")
        for gap in sorted(dist.keys())[:6]:
            print(f"    - Gap of {gap} round(s) (bought on Round {1 + gap}): {dist[gap]} players ({dist[gap]/len(rounds_to_second_die)*100:.1f}%)")
    print(f"Mean total dice purchased per player by game end: {statistics.mean(total_dice_bought_by_end):.2f}")
    
    print("\nEconomic Trajectory by Round:")
    for r in range(1, 6):
        if cash_at_end_of_round[r]:
            print(f"  Round {r}: Mean Cash: ${statistics.mean(cash_at_end_of_round[r]):.2f} | Mean Ready Dice: {statistics.mean(ready_dice_by_round[r]):.2f} | Mean Pipeline Debt: {statistics.mean(dice_in_development_by_round[r]):.2f}")


if __name__ == "__main__":
    run_cadence_experiment("CURRENT", 500)
    run_cadence_experiment("LEAN", 500)
    run_cadence_experiment("CHEAP", 500)
