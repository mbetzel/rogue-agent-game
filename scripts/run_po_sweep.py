import json, random, statistics
from sim.config import GameConfig, EndGameReason
from sim.engine import GameEngine
from sim.entities import get_random_setup
from sim.bots import AdaptiveBalancedBot, SecOpsTurtleBot, VentureGreedBot, AccelerationistBot

def main():
    runs = 1000
    base_seed = 42
    player_counts = [2, 3, 4]
    results = {}

    for p_count in player_counts:
        round_counts = []
        end_reasons = {r: 0 for r in EndGameReason}
        total_buffer_overflows = 0
        total_rounds_all_games = 0
        total_zero_exit_rounds = 0
        ending_secrets = []
        ending_money = []
        outliers = []
        
        for i in range(runs):
            seed = base_seed + i
            config = GameConfig(num_players=p_count)
            bots = [
                AdaptiveBalancedBot(0),
                SecOpsTurtleBot(1),
                VentureGreedBot(2),
                AccelerationistBot(3),
            ][:p_count]
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
            
            round_counts.append(res.total_rounds)
            end_reasons[res.end_reason] = end_reasons.get(res.end_reason, 0) + 1
            total_buffer_overflows += res.total_buffer_overflows
            
            for t in res.telemetry_history:
                total_rounds_all_games += 1
                if sum(t.exited_cubes.values()) == 0:
                    total_zero_exit_rounds += 1
                    
            for r in res.rankings:
                ending_secrets.append(r['secrets'])
                ending_money.append(r['money'])
                
            if (res.total_rounds <= 3 or res.total_rounds >= 20 or res.is_total_wipeout) and len(outliers) < 5:
                outliers.append({
                    'seed': seed,
                    'rounds': res.total_rounds,
                    'reason': res.end_reason.value,
                    'wipeout': res.is_total_wipeout,
                    'overflows': res.total_buffer_overflows,
                })
                
        results[p_count] = {
            'mean_rounds': round(statistics.mean(round_counts), 2),
            'std_rounds': round(statistics.stdev(round_counts), 2),
            'min_rounds': min(round_counts),
            'max_rounds': max(round_counts),
            'singularity_pct': round(end_reasons[EndGameReason.SINGULARITY] / runs * 100, 2),
            'patient_zero_pct': round(end_reasons[EndGameReason.PATIENT_ZERO] / runs * 100, 2),
            'wipeout_pct': round(end_reasons[EndGameReason.TOTAL_WIPEOUT] / runs * 100, 2),
            'round_limit_pct': round(end_reasons[EndGameReason.ROUND_LIMIT] / runs * 100, 2),
            'buffer_overflows_per_game': round(total_buffer_overflows / runs, 2),
            'zero_exit_round_pct': round(total_zero_exit_rounds / total_rounds_all_games * 100, 2) if total_rounds_all_games else 0.0,
            'mean_ending_secrets': round(statistics.mean(ending_secrets), 2),
            'mean_ending_money': round(statistics.mean(ending_money), 2),
            'outliers': outliers,
        }

    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
