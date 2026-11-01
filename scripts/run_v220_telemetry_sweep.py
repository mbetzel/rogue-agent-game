"""Run multi-pod Monte Carlo telemetry sweep for Rogue Agent v0.22.0 Baseline.

Tracks:
- Rounds (duration / pacing: Mean, Median, Min, Max)
- End reasons distribution (Patient Zero, Singularity, Total Wipeout, Round Limit)
- v3.0 / Singularity reach rate
- Total wipeout rate
- CI/CD Pipeline metrics:
  - Average glitched dice per player per round
  - Average scanned dice per player per round
  - Fast-patch activations (total and per-player-match)
- Player end-state economy (Final Secrets, Final Money, Final Patches)
- Attack cube exits and stuck cube telemetry per version card
"""

import statistics
import time
from collections import defaultdict
from sim.config import CubeColor, GameConfig
from sim.engine import GameEngine
from sim.bots import AdaptiveBalancedBot, SecOpsTurtleBot, VentureGreedBot, AccelerationistBot
from sim.entities import get_default_version_deck


def run_sweep(num_games: int = 1000):
    print(f"================ V0.22.0 BASELINE TELEMETRY SWEEP (N={num_games} per pod) ================\n")

    summary_tables = {}

    for p_count in [2, 3, 4]:
        start_t = time.time()
        rounds = []
        end_reasons = defaultdict(int)
        v_reached = defaultdict(int)
        r_tray = defaultdict(list)
        b_tray = defaultdict(list)
        g_tray = defaultdict(list)
        k_tray = defaultdict(list)
        stuck_total = defaultdict(list)
        wipeouts = 0
        singularities = 0

        # Pipeline & Economy metrics
        glitched_dice_per_round_player = []
        scanned_dice_per_round_player = []
        fast_patches_per_game = []
        fast_patches_per_player = []
        player_final_money = []
        player_final_secrets = []
        player_final_patches = []

        for seed in range(num_games):
            cfg = GameConfig(num_players=p_count)
            all_bots = [
                AdaptiveBalancedBot(0),
                SecOpsTurtleBot(1),
                VentureGreedBot(2),
                AccelerationistBot(3),
            ]
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

                for snap in telem.player_snapshots:
                    glitched_dice_per_round_player.append(snap["glitched_dice_count"])
                    scanned_dice_per_round_player.append(snap["scanned_dice_count"])

            res = eng.evaluate_end_game()
            rounds.append(res.total_rounds)
            end_reasons[res.end_reason.value] += 1
            if res.end_reason.value == "total_wipeout":
                wipeouts += 1
            if res.singularity_reached or res.end_reason.value == "singularity":
                singularities += 1

            for v in seen_versions:
                v_reached[v] += 1

            game_fast_patches = 0
            for p in eng.state.players:
                player_final_money.append(p.money)
                player_final_secrets.append(p.secrets)
                player_final_patches.append(p.patches)
                game_fast_patches += getattr(p, "total_fast_patches", 0)
                fast_patches_per_player.append(getattr(p, "total_fast_patches", 0))

            fast_patches_per_game.append(game_fast_patches)

        elapsed = time.time() - start_t
        mean_rds = statistics.mean(rounds)
        median_rds = statistics.median(rounds)
        v3_reach = (v_reached["v3.0"] / num_games) * 100.0
        singularity_pct = (singularities / num_games) * 100.0
        wipeout_pct = (wipeouts / num_games) * 100.0

        mean_glitched = statistics.mean(glitched_dice_per_round_player)
        mean_scanned = statistics.mean(scanned_dice_per_round_player)
        mean_fast_patches_game = statistics.mean(fast_patches_per_game)
        mean_fast_patches_player = statistics.mean(fast_patches_per_player)

        mean_money = statistics.mean(player_final_money)
        median_money = statistics.median(player_final_money)
        mean_secrets = statistics.mean(player_final_secrets)
        median_secrets = statistics.median(player_final_secrets)
        mean_patches = statistics.mean(player_final_patches)
        median_patches = statistics.median(player_final_patches)

        summary_tables[p_count] = {
            "mean_rds": mean_rds,
            "median_rds": median_rds,
            "v3_reach": v3_reach,
            "singularity_pct": singularity_pct,
            "wipeout_pct": wipeout_pct,
            "end_reasons": dict(end_reasons),
            "mean_glitched": mean_glitched,
            "mean_scanned": mean_scanned,
            "mean_fast_patches_game": mean_fast_patches_game,
            "mean_fast_patches_player": mean_fast_patches_player,
            "mean_money": mean_money,
            "median_money": median_money,
            "mean_secrets": mean_secrets,
            "median_secrets": median_secrets,
            "mean_patches": mean_patches,
            "median_patches": median_patches,
            "elapsed": elapsed,
        }

        print(f"--- Pod {p_count}P ({num_games} matches in {elapsed:.1f}s) ---")
        print(f"  Match Duration: Mean = {mean_rds:.2f} rds | Median = {median_rds:.1f} rds (Min={min(rounds)}, Max={max(rounds)})")
        print(f"  End Reasons: {dict(end_reasons)}")
        print(f"  v3.0 Reach Rate: {v3_reach:.1f}% | Singularity Rate: {singularity_pct:.1f}%")
        print(f"  Total Wipeout Rate: {wipeout_pct:.1f}%")
        print(f"  CI/CD Pipeline Telemetry:")
        print(f"    Avg Glitched Dice / player-rd: {mean_glitched:.2f}")
        print(f"    Avg Scanned Dice / player-rd:  {mean_scanned:.2f}")
        print(f"    Avg Fast-Patches / match:      {mean_fast_patches_game:.2f} (Per Player: {mean_fast_patches_player:.2f})")
        print(f"  Player Economy at End Game:")
        print(f"    Final Secrets: Mean = {mean_secrets:.2f} | Median = {median_secrets:.1f}")
        print(f"    Final Money:   Mean = ${mean_money:.2f} | Median = ${median_money:.1f}")
        print(f"    Final Patches: Mean = {mean_patches:.2f} | Median = {median_patches:.1f}")
        for v in ["v1.0", "v2.0", "v3.0"]:
            if r_tray[v]:
                print(f"  {v} Tray Averages: Red={statistics.mean(r_tray[v]):.2f}, Blue={statistics.mean(b_tray[v]):.2f}, Green={statistics.mean(g_tray[v]):.2f}, Black={statistics.mean(k_tray[v]):.2f} | Stuck Cubes={statistics.mean(stuck_total[v]):.2f}")
        print()

    print("================ OVERALL COMPARISON SUMMARY ================")
    print(f"{'Metric':<32} | {'2P':<10} | {'3P':<10} | {'4P':<10}")
    print("-" * 68)
    print(f"{'Mean Rounds':<32} | {summary_tables[2]['mean_rds']:<10.2f} | {summary_tables[3]['mean_rds']:<10.2f} | {summary_tables[4]['mean_rds']:<10.2f}")
    print(f"{'Median Rounds':<32} | {summary_tables[2]['median_rds']:<10.1f} | {summary_tables[3]['median_rds']:<10.1f} | {summary_tables[4]['median_rds']:<10.1f}")
    print(f"{'v3.0 Reach (%)':<32} | {summary_tables[2]['v3_reach']:<10.1f} | {summary_tables[3]['v3_reach']:<10.1f} | {summary_tables[4]['v3_reach']:<10.1f}")
    print(f"{'Singularity Rate (%)':<32} | {summary_tables[2]['singularity_pct']:<10.1f} | {summary_tables[3]['singularity_pct']:<10.1f} | {summary_tables[4]['singularity_pct']:<10.1f}")
    print(f"{'Total Wipeout (%)':<32} | {summary_tables[2]['wipeout_pct']:<10.1f} | {summary_tables[3]['wipeout_pct']:<10.1f} | {summary_tables[4]['wipeout_pct']:<10.1f}")
    print(f"{'Avg Glitched Dice / player-rd':<32} | {summary_tables[2]['mean_glitched']:<10.2f} | {summary_tables[3]['mean_glitched']:<10.2f} | {summary_tables[4]['mean_glitched']:<10.2f}")
    print(f"{'Avg Scanned Dice / player-rd':<32} | {summary_tables[2]['mean_scanned']:<10.2f} | {summary_tables[3]['mean_scanned']:<10.2f} | {summary_tables[4]['mean_scanned']:<10.2f}")
    print(f"{'Fast-Patches / match':<32} | {summary_tables[2]['mean_fast_patches_game']:<10.2f} | {summary_tables[3]['mean_fast_patches_game']:<10.2f} | {summary_tables[4]['mean_fast_patches_game']:<10.2f}")
    print(f"{'Fast-Patches / player':<32} | {summary_tables[2]['mean_fast_patches_player']:<10.2f} | {summary_tables[3]['mean_fast_patches_player']:<10.2f} | {summary_tables[4]['mean_fast_patches_player']:<10.2f}")
    print(f"{'Final Secrets (Mean)':<32} | {summary_tables[2]['mean_secrets']:<10.2f} | {summary_tables[3]['mean_secrets']:<10.2f} | {summary_tables[4]['mean_secrets']:<10.2f}")
    print(f"{'Final Money (Mean)':<32} | ${summary_tables[2]['mean_money']:<9.2f} | ${summary_tables[3]['mean_money']:<9.2f} | ${summary_tables[4]['mean_money']:<9.2f}")
    print(f"{'Final Patches (Mean)':<32} | {summary_tables[2]['mean_patches']:<10.2f} | {summary_tables[3]['mean_patches']:<10.2f} | {summary_tables[4]['mean_patches']:<10.2f}")


if __name__ == "__main__":
    run_sweep(num_games=1000)
