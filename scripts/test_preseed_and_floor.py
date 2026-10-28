import random
from typing import Dict, List, Optional
from sim.config import GameConfig, CubeColor
from sim.engine.core import GameEngine
from sim.bots.adaptive_balanced import AdaptiveBalancedBot

def run_simulation_sweep():
    configurations = [
        ("Baseline (v0.9.0)", False, 0, False),
        ("Threat Floor Only (1 of each color)", True, 0, False),
        ("Pre-seed 4 Cubes Only", False, 1, False),
        ("Pre-seed 8 Cubes Only", False, 2, False),
        ("Combined: Pre-seed 4 + Threat Floor", True, 1, False),
        ("Combined: Pre-seed 8 + Threat Floor", True, 2, False),
    ]

    player_counts = [2, 3, 4]
    games_per_cell = 1000

    results = []

    for name, use_floor, preseed_per_color, _ in configurations:
        print(f"\n==================================================")
        print(f"Running Config: {name}")
        print(f"==================================================")

        for num_players in player_counts:
            total_rounds = 0
            wipeouts = 0
            singularities = 0
            patient_zeros = 0
            round_limit = 0
            
            zero_total_exit_rounds = 0
            zero_attack_exit_rounds = 0
            floor_triggers = 0
            
            # Ending stats
            secrets_at_end = []
            
            for g in range(games_per_cell):
                config = GameConfig(num_players=num_players)
                bots = [AdaptiveBalancedBot(f"Bot{i}") for i in range(num_players)]
                engine = GameEngine(config, bots, seed=g + 20000 + num_players * 1000)

                # Pre-seed step at setup
                if preseed_per_color > 0:
                    pre_seed_payload = {
                        CubeColor.RED: preseed_per_color,
                        CubeColor.BLUE: preseed_per_color,
                        CubeColor.GREEN: preseed_per_color,
                        CubeColor.BLACK: preseed_per_color,
                    }
                    # Drop into empty tower; exited cubes are discarded (do not go into staging cup)
                    engine.state.tower.drop(pre_seed_payload, engine.rng)

                r = 0
                while not engine.state.game_over:
                    r += 1
                    
                    # Threat Floor Check:
                    # In Phase 1 Step 1, if Staging Cup has 0 attack cubes (and it is after R1 drop or any round),
                    # add 1 Red, 1 Blue, 1 Green.
                    if use_floor:
                        atk_staged = sum(
                            engine.state.staging_cup.get(c, 0)
                            for c in [CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN]
                        )
                        if atk_staged == 0:
                            floor_triggers += 1
                            engine.state.staging_cup[CubeColor.RED] = engine.state.staging_cup.get(CubeColor.RED, 0) + 1
                            engine.state.staging_cup[CubeColor.BLUE] = engine.state.staging_cup.get(CubeColor.BLUE, 0) + 1
                            engine.state.staging_cup[CubeColor.GREEN] = engine.state.staging_cup.get(CubeColor.GREEN, 0) + 1

                    tel = engine.run_round()
                    total_rounds += 1
                    tot_exit = sum(tel.exited_cubes.values())
                    atk_exit = sum(
                        tel.exited_cubes.get(c, 0)
                        for c in [CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN]
                    )

                    if tot_exit == 0:
                        zero_total_exit_rounds += 1
                    if atk_exit == 0:
                        zero_attack_exit_rounds += 1

                reason = engine.state.end_reason.value
                if reason == "total_wipeout":
                    wipeouts += 1
                elif reason == "singularity":
                    singularities += 1
                elif reason == "patient_zero":
                    patient_zeros += 1
                elif reason == "round_limit":
                    round_limit += 1

                avg_sec = sum(p.secrets for p in engine.state.players) / num_players
                secrets_at_end.append(avg_sec)

            avg_dur = total_rounds / games_per_cell
            wipe_pct = wipeouts / games_per_cell * 100
            sing_pct = singularities / games_per_cell * 100
            pz_pct = patient_zeros / games_per_cell * 100
            zero_tot_pct = zero_total_exit_rounds / total_rounds * 100
            zero_atk_pct = zero_attack_exit_rounds / total_rounds * 100
            avg_triggers_per_game = floor_triggers / games_per_cell

            print(
                f"[{num_players}P] Dur: {avg_dur:.2f} rds | "
                f"Sing: {sing_pct:4.1f}% | PZ: {pz_pct:4.1f}% | Wipe: {wipe_pct:4.1f}% | "
                f"0-Tot: {zero_tot_pct:4.2f}% | 0-Atk: {zero_atk_pct:4.2f}% | "
                f"FloorTrig/Gm: {avg_triggers_per_game:.2f}"
            )

if __name__ == "__main__":
    run_simulation_sweep()
