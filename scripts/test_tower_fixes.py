import random
from sim.config import GameConfig, CubeColor
from sim.engine.core import GameEngine
from sim.bots.adaptive_balanced import AdaptiveBalancedBot

# Let's test two potential rules:
# Rule 1 (Floor): If at start of Phase 2, staging cup has 0 attack cubes, add 1 Red, 1 Blue, 1 Green from supply.
# Rule 2 (Surge): If round resolves with 0 total cubes exiting, next round add 1 Red, 1 Blue, 1 Green into staging cup.
# Rule 3 (Setup Pre-seed): Setup drops 1 Red, 1 Blue, 1 Green, 1 Black into tower, whatever exits is removed, stuck cubes stay.

def test_mechanics():
    print("Testing Baseline vs Solution Options across 2000 4P matches...")
    
    # Let's run a test simulating the Floor Rule (if 0 attack cubes staged, add 1 of each color)
    for mode in ["Baseline", "Floor_Rule", "Setup_Preseed"]:
        games = 1000
        total_rounds = 0
        wipeouts = 0
        singularities = 0
        patient_zeros = 0
        zero_total_rounds = 0
        zero_attack_rounds = 0
        
        for g in range(games):
            config = GameConfig(num_players=4)
            bots = [AdaptiveBalancedBot(f"Bot{i}") for i in range(4)]
            engine = GameEngine(config, bots, seed=g + 3000)
            
            if mode == "Setup_Preseed":
                # Pre-seed: drop 1 of each color into empty tower at setup
                pre_seed = {CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 1, CubeColor.BLACK: 1}
                exited_pre = engine.state.tower.drop(pre_seed, engine.rng)
                # Exited pre-seed cubes are discarded (do not go into staging cup)
            
            r = 0
            while not engine.state.game_over:
                r += 1
                
                if mode == "Floor_Rule":
                    # Check staging cup attack cubes before Phase 1 or Phase 2
                    atk = sum(engine.state.staging_cup.get(c, 0) for c in [CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN])
                    if atk == 0 and r > 1:
                        # Floor rule triggers: inject 1 Red, 1 Blue, 1 Green
                        engine.state.staging_cup[CubeColor.RED] += 1
                        engine.state.staging_cup[CubeColor.BLUE] += 1
                        engine.state.staging_cup[CubeColor.GREEN] += 1
                
                tel = engine.run_round()
                total_rounds += 1
                tot = sum(tel.exited_cubes.values())
                atk_exit = sum(tel.exited_cubes.get(c, 0) for c in [CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN])
                if tot == 0:
                    zero_total_rounds += 1
                if atk_exit == 0:
                    zero_attack_rounds += 1
            
            reason = engine.state.end_reason.value
            if reason == "total_wipeout":
                wipeouts += 1
            elif reason == "singularity":
                singularities += 1
            elif reason == "patient_zero":
                patient_zeros += 1

        print(f"\n--- {mode} ---")
        print(f"Avg Match Duration: {total_rounds / games:.2f} rounds")
        print(f"Total Wipeout Rate: {wipeouts / games * 100:.1f}%")
        print(f"Singularity Rate: {singularities / games * 100:.1f}%")
        print(f"Patient Zero Rate: {patient_zeros / games * 100:.1f}%")
        print(f"Rounds with 0 Total Exits: {zero_total_rounds} ({zero_total_rounds / total_rounds * 100:.2f}%)")
        print(f"Rounds with 0 Attack Exits: {zero_attack_rounds} ({zero_attack_rounds / total_rounds * 100:.2f}%)")

if __name__ == "__main__":
    test_mechanics()
