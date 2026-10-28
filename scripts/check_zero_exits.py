import random
from sim.config import GameConfig, CubeColor
from sim.engine.core import GameEngine
from sim.bots.adaptive_balanced import AdaptiveBalancedBot

def run_check():
    for num_players in [2, 3, 4]:
        games_tested = 2000
        zero_total_exit_rounds = 0
        zero_attack_exit_rounds = 0
        games_with_zero_total_exit = 0
        games_with_zero_attack_exit = 0
        total_rounds = 0

        # Also track round 1 specifically
        r1_zero_total = 0
        r1_zero_attack = 0

        # Track consecutive 0-total rounds
        consecutive_zero_total_events = 0

        for g in range(games_tested):
            config = GameConfig(num_players=num_players)
            bots = [AdaptiveBalancedBot(f"Bot{i}") for i in range(num_players)]
            engine = GameEngine(config, bots, seed=g + 1000)
            has_zero_total = False
            has_zero_attack = False
            prev_zero_total = False

            round_num = 0
            while not engine.state.game_over:
                round_num += 1
                telemetry = engine.run_round()
                total_rounds += 1
                exited = telemetry.exited_cubes
                total_exited = sum(exited.values())
                attack_exited = (
                    exited.get(CubeColor.RED, 0)
                    + exited.get(CubeColor.BLUE, 0)
                    + exited.get(CubeColor.GREEN, 0)
                )

                if total_exited == 0:
                    zero_total_exit_rounds += 1
                    has_zero_total = True
                    if round_num == 1:
                        r1_zero_total += 1
                    if prev_zero_total:
                        consecutive_zero_total_events += 1
                    prev_zero_total = True
                else:
                    prev_zero_total = False

                if attack_exited == 0:
                    zero_attack_exit_rounds += 1
                    has_zero_attack = True
                    if round_num == 1:
                        r1_zero_attack += 1

            if has_zero_total:
                games_with_zero_total_exit += 1
            if has_zero_attack:
                games_with_zero_attack_exit += 1

        print(f"=== {num_players} PLAYERS ({games_tested} games) ===")
        print(f"Total rounds: {total_rounds}")
        print(f"Round 1 Zero Total Exits: {r1_zero_total} ({r1_zero_total / games_tested * 100:.2f}%)")
        print(f"Round 1 Zero Attack Exits: {r1_zero_attack} ({r1_zero_attack / games_tested * 100:.2f}%)")
        print(f"Rounds with 0 Total Cubes Exited: {zero_total_exit_rounds} ({zero_total_exit_rounds / total_rounds * 100:.2f}%)")
        print(f"Games with >=1 Round of 0 Total Cubes: {games_with_zero_total_exit} ({games_with_zero_total_exit / games_tested * 100:.2f}%)")
        print(f"Consecutive 0 Total Exit Rounds: {consecutive_zero_total_events}")
        print(f"Rounds with 0 Attack Cubes Exited: {zero_attack_exit_rounds} ({zero_attack_exit_rounds / total_rounds * 100:.2f}%)")
        print(f"Games with >=1 Round of 0 Attack Cubes: {games_with_zero_attack_exit} ({games_with_zero_attack_exit / games_tested * 100:.2f}%)\n")

if __name__ == "__main__":
    run_check()
