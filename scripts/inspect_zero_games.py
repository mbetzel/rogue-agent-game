import random
from sim.config import GameConfig, CubeColor
from sim.engine.core import GameEngine
from sim.bots.adaptive_balanced import AdaptiveBalancedBot

# Let's inspect what happens in games where 0 total cubes exit currently.
# How do those games proceed?
def inspect_zero_exit_games():
    config = GameConfig(num_players=4)
    bots = [AdaptiveBalancedBot(f"Bot{i}") for i in range(4)]
    
    stalled_games = 0
    total_games = 1000
    
    for g in range(total_games):
        engine = GameEngine(config, bots, seed=g + 5000)
        rounds_with_zero = []
        r = 0
        while not engine.state.game_over:
            r += 1
            tel = engine.run_round()
            tot = sum(tel.exited_cubes.values())
            if tot == 0:
                rounds_with_zero.append(r)
        
        if rounds_with_zero:
            stalled_games += 1
            if stalled_games <= 3:
                print(f"Game seed {g+5000}: Zero exit in round(s) {rounds_with_zero}. Match ended round {r} with reason {engine.state.end_reason.value}")
                for tel in engine.telemetry_history:
                    print(f"  R{tel.round_number}: Staged={tel.staged_cubes} StuckBefore={sum(tel.stuck_cubes_before.values())} Exited={tel.exited_cubes} StuckAfter={sum(tel.stuck_cubes_after.values())}")

if __name__ == "__main__":
    inspect_zero_exit_games()
