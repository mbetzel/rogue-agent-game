"""Run multi-pod Monte Carlo telemetry sweep for Rogue Agent v0.21.0 Baseline."""

import statistics
from collections import defaultdict
from sim.config import CubeColor, GameConfig
from sim.engine import GameEngine
from sim.bots import AdaptiveBalancedBot, SecOpsTurtleBot, VentureGreedBot, AccelerationistBot
from sim.entities import get_default_version_deck


def run_sweep(num_games: int = 1000):
    print(f"================ V0.21.0 TELEMETRY SWEEP (N={num_games} per pod) ================\n")

    results_by_pod = {}

    for p_count in [2, 3, 4]:
        rounds = []
        end_reasons = defaultdict(int)
        v_reached = defaultdict(int)
        r_tray = defaultdict(list)
        b_tray = defaultdict(list)
        g_tray = defaultdict(list)
        k_tray = defaultdict(list)
        stuck_total = defaultdict(list)
        player_final_money = []
        player_final_secrets = []
        wipeouts = 0

        for seed in range(num_games):
            cfg = GameConfig.legacy_v035(num_players=p_count)
            all_bots = [AdaptiveBalancedBot(0), SecOpsTurtleBot(1), VentureGreedBot(2), AccelerationistBot(3)]
            bots = all_bots[:p_count]
            deck = get_default_version_deck()
            eng = GameEngine(config=cfg, bots=bots, seed=seed, version_deck=deck)

            seen_versions = set()
            while not eng.state.game_over:
                v_str = eng.state.active_version.version_str
                seen_versions.add(v_str)
                telem = eng.run_round()
                r_tray[v_str].append(telem.exited_cubes.get(CubeColor.RED, 0))
                b_tray[v_str].append(telem.exited_cubes.get(CubeColor.BLUE, 0))
                g_tray[v_str].append(telem.exited_cubes.get(CubeColor.GREEN, 0))
                k_tray[v_str].append(telem.exited_cubes.get(CubeColor.BLACK, 0))
                stuck_total[v_str].append(sum(telem.stuck_cubes_after.values()))

            res = eng.evaluate_end_game()
            rounds.append(res.total_rounds)
            end_reasons[res.end_reason.value] += 1
            if res.end_reason.value == "total_wipeout":
                wipeouts += 1

            for v in seen_versions:
                v_reached[v] += 1

            for p in eng.state.players:
                player_final_money.append(p.money)
                player_final_secrets.append(p.secrets)

        mean_rds = statistics.mean(rounds)
        median_rds = statistics.median(rounds)
        v3_reach = (v_reached["v3.0"] / num_games) * 100.0
        wipeout_pct = (wipeouts / num_games) * 100.0

        print(f"--- Pod {p_count}P ({num_games} matches) ---")
        print(f"  Match Duration: Mean = {mean_rds:.2f} rds | Median = {median_rds:.1f} rds")
        print(f"  End Reasons: {dict(end_reasons)}")
        print(f"  v3.0 Reach Rate: {v3_reach:.1f}%")
        print(f"  Total Wipeout Rate: {wipeout_pct:.1f}%")
        for v in ["v1.0", "v2.0", "v3.0"]:
            if r_tray[v]:
                print(f"  {v} Tray Averages: Red={statistics.mean(r_tray[v]):.2f}, Blue={statistics.mean(b_tray[v]):.2f}, Green={statistics.mean(g_tray[v]):.2f}, Black={statistics.mean(k_tray[v]):.2f} | Stuck Cubes={statistics.mean(stuck_total[v]):.2f}")
        print()


if __name__ == "__main__":
    run_sweep(num_games=1000)
