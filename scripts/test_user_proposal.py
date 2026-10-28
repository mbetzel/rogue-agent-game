import random
from typing import Dict, List
from sim.config import GameConfig, CubeColor
from sim.engine.core import GameEngine
from sim.bots.adaptive_balanced import AdaptiveBalancedBot

def test_user_zero_total_rule():
    player_counts = [2, 3, 4]
    games = 1000

    print("==================================================")
    print("Testing User's Proposal: Seed ONLY if ZERO total cubes exit the tower")
    print("(Combined with Pre-seed 4: 1 Red, 1 Blue, 1 Green, 1 Black at setup)")
    print("==================================================")

    for num_players in player_counts:
        total_rounds = 0
        wipeouts = 0
        singularities = 0
        patient_zeros = 0
        
        zero_total_exit_rounds = 0
        zero_attack_exit_rounds = 0
        seed_events = 0

        # Track single-cube drops (drops with <= 1 cube)
        single_cube_drops = 0
        # Track rounds where 0 attack cubes drop
        quiet_attack_streaks = []

        for g in range(games):
            config = GameConfig(num_players=num_players)
            bots = [AdaptiveBalancedBot(f"Bot{i}") for i in range(num_players)]
            engine = GameEngine(config, bots, seed=g + 40000 + num_players * 1000)

            # Pre-seed 4 cubes at setup
            pre_seed_payload = {
                CubeColor.RED: 1,
                CubeColor.BLUE: 1,
                CubeColor.GREEN: 1,
                CubeColor.BLACK: 1,
            }
            engine.state.tower.drop(pre_seed_payload, engine.rng)

            pending_seed = False
            current_quiet_streak = 0

            while not engine.state.game_over:
                # If last round had ZERO total cubes exit, seed 1 Red, 1 Blue, 1 Green into staging cup
                if pending_seed:
                    seed_events += 1
                    engine.state.staging_cup[CubeColor.RED] = engine.state.staging_cup.get(CubeColor.RED, 0) + 1
                    engine.state.staging_cup[CubeColor.BLUE] = engine.state.staging_cup.get(CubeColor.BLUE, 0) + 1
                    engine.state.staging_cup[CubeColor.GREEN] = engine.state.staging_cup.get(CubeColor.GREEN, 0) + 1
                    pending_seed = False

                # Check staged cube count before drop
                # Note: Phase 1 will add 1 Black cube in execute_phase_1
                staged_cubes_count = sum(engine.state.staging_cup.values()) + 1 # +1 for Autonomous pulse
                if staged_cubes_count <= 1:
                    single_cube_drops += 1

                tel = engine.run_round()
                total_rounds += 1
                tot_exit = sum(tel.exited_cubes.values())
                atk_exit = sum(
                    tel.exited_cubes.get(c, 0)
                    for c in [CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN]
                )

                if tot_exit == 0:
                    zero_total_exit_rounds += 1
                    # User rule: seed only if ZERO cubes of any color exited
                    pending_seed = True
                else:
                    pending_seed = False

                if atk_exit == 0:
                    zero_attack_exit_rounds += 1
                    current_quiet_streak += 1
                else:
                    if current_quiet_streak > 0:
                        quiet_attack_streaks.append(current_quiet_streak)
                        current_quiet_streak = 0

            if current_quiet_streak > 0:
                quiet_attack_streaks.append(current_quiet_streak)

            reason = engine.state.end_reason.value
            if reason == "total_wipeout":
                wipeouts += 1
            elif reason == "singularity":
                singularities += 1
            elif reason == "patient_zero":
                patient_zeros += 1

        avg_dur = total_rounds / games
        wipe_pct = wipeouts / games * 100
        sing_pct = singularities / games * 100
        pz_pct = patient_zeros / games * 100
        zero_tot_pct = zero_total_exit_rounds / total_rounds * 100
        zero_atk_pct = zero_attack_exit_rounds / total_rounds * 100
        avg_seed_events = seed_events / games
        single_drop_pct = single_cube_drops / total_rounds * 100
        max_quiet = max(quiet_attack_streaks) if quiet_attack_streaks else 0
        avg_quiet = sum(quiet_attack_streaks) / len(quiet_attack_streaks) if quiet_attack_streaks else 0

        print(
            f"[{num_players}P] Dur: {avg_dur:.2f} rds | "
            f"Sing: {sing_pct:4.1f}% | PZ: {pz_pct:4.1f}% | Wipe: {wipe_pct:4.1f}% | "
            f"0-Tot: {zero_tot_pct:4.2f}% | 0-Atk: {zero_atk_pct:4.2f}% | "
            f"SeedEvents/Gm: {avg_seed_events:.3f} | 1-Cube Drops: {single_drop_pct:.2f}% | Max 0-Atk Streak: {max_quiet}"
        )

if __name__ == "__main__":
    test_user_zero_total_rule()
