"""Investigation Script: Testing User's Proposed Economy & Dice Pool Changes.

Proposed Changes:
1. Starting research starts at 0 (currently 2).
2. Starting money starts at $6 (currently $4) - enough to buy one die.
3. Starting pool: 3 Gray dice + 1 Purple die (currently 4 Gray).
   Evaluating Personal Reserve:
   - Option A: 1 Purple die in reserve (total 2 Purple dice max)
   - Option B: 2 Purple dice in reserve (total 3 Purple dice max)
"""

import sys
import os
import random
import statistics
from collections import defaultdict
from typing import Dict, List, Tuple, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sim.config import GameConfig, DieColor, CubeColor, ShieldColor, EndGameReason
from sim.engine.core import GameEngine
from sim.engine.state import PlayerState
from sim.entities import (
    Die,
    create_gray_die,
    create_colored_die,
    COMPANIES,
    WHITE_HATS,
    CompanyCode,
    WhiteHatCode,
    get_all_companies,
    get_all_white_hats,
    get_random_companies,
    get_random_white_hats,
    get_random_setup,
    CANONICAL_COMPANY_FOR_OPERATIVE,
)
from sim.bots import (
    AdaptiveBalancedBot,
    SecOpsTurtleBot,
    VentureGreedBot,
    AccelerationistBot,
)


def compute_turn1_roll_probabilities():
    """Calculates exact analytical / high-iteration probabilities for Turn 1 dice pool."""
    print("=== TURN 1 PROBABILITY ANALYSIS ===")
    
    # 4 Gray vs 3 Gray + 1 Purple
    # Gray faces: 1: Block Any, 2: Block Any, 3: +$1, 4: +$1, 5: +$1 / +1 res, 6: +1 res
    # Purple faces: 1: Block Any, 2: Block Any, 3: +$2, 4: +$1 & +1 res, 5: Glitch (Locked), 6: Purple Star
    
    # Let's simulate 100,000 rolls with standard bot reroll heuristics
    rng = random.Random(42)
    
    def simulate_pool(gray_count: int, purple_count: int, n_sims: int = 50000):
        star_triggers = 0
        glitches = 0
        total_cash = []
        total_res = []
        total_shields = []
        
        for _ in range(n_sims):
            pool = [create_gray_die(i) for i in range(gray_count)] + [
                create_colored_die(DieColor.PURPLE, gray_count + i) for i in range(purple_count)
            ]
            
            # Initial roll
            for d in pool:
                d.roll(rng)
                
            # Up to 2 rerolls (simple Yahtzee: keep stars, keep shields if any, reroll non-stars/non-shields if glitch-free)
            for _ in range(2):
                for d in pool:
                    if d.is_locked:
                        continue
                    face = d.current_face
                    if face.is_star:
                        continue  # keep star
                    if face.is_glitch:
                        continue  # locked
                    # Reroll face if low value
                    if d.color == DieColor.PURPLE:
                        # On purple, keep star, or keep $2 / $1+1res if satisfied
                        if face.is_star:
                            pass
                        elif face.money >= 2 or face.patches >= 1:
                            pass  # good face
                        elif face.is_shield:
                            pass  # good defense
                        else:
                            d.roll(rng)
                    else:
                        # On gray, keep shields or research or cash
                        pass  # Gray has no bad faces
            
            # Evaluate outputs
            cash = 0
            res = 0
            shields = 0
            g = 0
            stars = 0
            
            for d in pool:
                f = d.current_face
                if f.is_glitch:
                    g += 1
                elif f.is_star:
                    stars += 1
                else:
                    if f.is_shield:
                        shields += f.block_amount
                    if f.money > 0:
                        cash += f.money
                    if f.patches > 0:
                        res += f.patches
                    if f.is_choice:
                        # Assume 50/50 or cash priority
                        cash += 1
            
            if stars > 0:
                star_triggers += 1
            glitches += g
            total_cash.append(cash)
            total_res.append(res)
            total_shields.append(shields)
            
        print(f"Pool: {gray_count} Gray + {purple_count} Purple:")
        print(f"  P(Purple Star triggered on Round 1): {star_triggers / n_sims * 100:.1f}%")
        print(f"  Mean Glitches on Round 1: {glitches / n_sims:.2f}")
        print(f"  Mean Cash generated: ${statistics.mean(total_cash):.2f}")
        print(f"  Mean Research generated: {statistics.mean(total_res):.2f} 🔬")
        print(f"  Mean Shields generated: {statistics.mean(total_shields):.2f}")
        print()

    simulate_pool(4, 0)
    simulate_pool(3, 1)


class CustomSetupEngine(GameEngine):
    """Engine that overrides starting setup parameters for investigation."""

    def __init__(
        self,
        config: GameConfig,
        starting_gray: int = 3,
        starting_purple: int = 1,
        starting_cash: int = 6,
        starting_research: int = 0,
        personal_purple_reserve: int = 1,
        *args,
        **kwargs,
    ):
        self.starting_gray = starting_gray
        self.starting_purple = starting_purple
        self.custom_starting_cash = starting_cash
        self.custom_starting_res = starting_research
        self.custom_reserve = personal_purple_reserve
        super().__init__(config, *args, **kwargs)

    def _init_players(self, bots, config):
        # We override player initialization
        pass


def run_experiment_suite(
    name: str,
    starting_gray: int,
    starting_purple: int,
    starting_cash: int,
    starting_research: int,
    purple_reserve: int,
    n_matches: int = 1000,
):
    print(f"\n========================================================")
    print(f"Running Experiment: {name}")
    print(f"Setup: {starting_gray} Gray, {starting_purple} Purple starting | ${starting_cash} Cash | {starting_research} Research | {purple_reserve} in Reserve")
    print(f"Matches: {n_matches} (4-Player Pods)")
    print(f"========================================================")

    match_lengths = []
    end_reasons = defaultdict(int)
    wh_wins = defaultdict(int)
    wh_games = defaultdict(int)
    wh_pz = defaultdict(int)
    turn1_double_buys = 0
    total_turn1_purchases = 0
    total_purple_bought = 0
    final_secrets = []

    rng = random.Random(1337)

    for match_idx in range(n_matches):
        # Create 4 bots
        bots = [
            AdaptiveBalancedBot(0),
            SecOpsTurtleBot(1),
            VentureGreedBot(2),
            AccelerationistBot(3),
        ]
        rng.shuffle(bots)

        cfg = GameConfig.legacy_v035(
            num_players=4,
            starting_money=starting_cash,
            starting_gray_dice=starting_gray,
            enable_corporate_asymmetry=True,
        )

        variants, version_deck = get_random_setup(rng, profile="STANDARD")

        # Pick random companies and white hats
        wh_pool = list(WHITE_HATS.values())
        rng.shuffle(wh_pool)
        selected_wh = wh_pool[:4]
        selected_comp = [COMPANIES[CANONICAL_COMPANY_FOR_OPERATIVE[wh.code]] for wh in selected_wh]

        # Engine init
        engine = GameEngine(
            config=cfg,
            bots=bots,
            seed=rng.randint(0, 1000000000),
            variant_cards=variants,
            version_deck=version_deck,
            companies=selected_comp,
            white_hats=selected_wh,
        )

        # Patch players for this experiment
        for p_idx, p in enumerate(engine.state.players):
            # Ready dice
            p.ready_for_release_dice = [create_gray_die(100 + i) for i in range(starting_gray)]
            for j in range(starting_purple):
                purple_die = create_colored_die(
                    DieColor.PURPLE,
                    200 + j,
                    reserve_cost=p.get_purple_reserve_cost(),
                )
                p.ready_for_release_dice.append(purple_die)

            # Personal reserve
            p.personal_purple_reserve = purple_reserve

            # Cash: custom starting cash + company cash bonus
            comp_cash = p.company.starting_cash_bonus if p.company else 0
            p.money = starting_cash + comp_cash

            # Research: custom starting res + company res bonus
            comp_res = p.company.starting_research_bonus if p.company else 0
            p.research_tokens = starting_research + comp_res

            wh_games[p.white_hat.code] += 1

        # Track turn 1 market purchases
        # Run Round 1
        engine.run_round()

        for p in engine.state.players:
            # Check how many dice bought in round 1
            # Total colored dice in ready/production/unpatched
            all_dice = p.ready_for_release_dice + p.in_production_dice + p.glitched_dice + p.scanned_dice
            colored_count = len([d for d in all_dice if d.color not in (DieColor.GRAY, DieColor.WHITE)])
            bought = colored_count - starting_purple
            if bought >= 2:
                turn1_double_buys += 1
            if bought > 0:
                total_turn1_purchases += bought

        # Run remaining rounds until end
        while not engine.state.game_over and engine.state.current_round < 25:
            engine.run_round()

        match_lengths.append(engine.state.current_round)
        end_reasons[engine.state.end_reason] += 1

        # Check winners and patient zeros
        winners = [p for p in engine.state.players if not p.is_patient_zero]
        if winners:
            best_score = max(p.secrets for p in winners)
            match_winners = [p for p in winners if p.secrets == best_score]
            for w in match_winners:
                wh_wins[w.white_hat.code] += 1 / len(match_winners)

        for p in engine.state.players:
            if p.is_patient_zero:
                wh_pz[p.white_hat.code] += 1
            all_dice = p.ready_for_release_dice + p.in_production_dice + p.glitched_dice + p.scanned_dice
            purple_owned = len([d for d in all_dice if d.color == DieColor.PURPLE])
            total_purple_bought += (purple_owned - starting_purple)
            final_secrets.append(p.secrets)

    avg_len = statistics.mean(match_lengths)
    print(f"Results across {n_matches} matches:")
    print(f"  Average Match Length: {avg_len:.2f} rounds (StdDev: {statistics.stdev(match_lengths):.2f})")
    print(f"  End Game Reasons:")
    for reason, count in end_reasons.items():
        print(f"    - {reason.value if hasattr(reason, 'value') else reason}: {count} ({count/n_matches*100:.1f}%)")
    print(f"  Turn 1 Double-Buys: {turn1_double_buys} / {n_matches * 4} ({turn1_double_buys / (n_matches * 4) * 100:.2f}%)")
    print(f"  Mean Turn 1 Purchases: {total_turn1_purchases / (n_matches * 4):.2f} dice/player")
    print(f"  Mean Additional Purple Dice Bought per player: {total_purple_bought / (n_matches * 4):.2f}")
    print(f"  Mean Final Corporate Secrets: {statistics.mean(final_secrets):.2f}")
    print(f"  White Hat Operative Win Rates:")
    for wh_code in WhiteHatCode:
        games = wh_games[wh_code]
        wins = wh_wins[wh_code]
        pz = wh_pz[wh_code]
        win_rate = (wins / games * 100) if games else 0
        pz_rate = (pz / games * 100) if games else 0
        print(f"    - {wh_code.value:<10}: Win Rate: {win_rate:5.1f}% | Patient Zero Rate: {pz_rate:5.1f}% (Games: {games})")


if __name__ == "__main__":
    compute_turn1_roll_probabilities()
    
    # 1. Baseline v0.29.0
    run_experiment_suite(
        name="Baseline (v0.29.0)",
        starting_gray=4,
        starting_purple=0,
        starting_cash=4,
        starting_research=2,
        purple_reserve=2,
        n_matches=1000,
    )

    # 2. User Proposal - Option A: Start 1 Purple, 1 in Reserve (max 2)
    run_experiment_suite(
        name="User Proposal (Option A: 1 Reserve / Max 2 Purple)",
        starting_gray=3,
        starting_purple=1,
        starting_cash=6,
        starting_research=0,
        purple_reserve=1,
        n_matches=1000,
    )

    # 3. User Proposal - Option B: Start 1 Purple, 2 in Reserve (max 3)
    run_experiment_suite(
        name="User Proposal (Option B: 2 Reserve / Max 3 Purple)",
        starting_gray=3,
        starting_purple=1,
        starting_cash=6,
        starting_research=0,
        purple_reserve=2,
        n_matches=1000,
    )
