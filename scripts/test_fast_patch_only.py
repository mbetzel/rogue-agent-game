# NOTE (v0.34.0): this script targets the v0.33-era module layout (phase1_boot / phase2_threat /
# phase3_ops). After the six-phase module split, its monkeypatches of those modules may no longer
# take effect on either round sequence (legacy_v033 binds the new modules). Results are historical.
"""Monte Carlo simulation comparing:
1. v0.22.0 Baseline (Both Debug Unlocks in Phase 1 and Fast-Patching in Phase 3)
2. Fast-Patch ONLY (No Phase 1 Debug Unlocks; 100% of patches reserved for Phase 3 Fast-Patching)
3. No Fast-Patch (Debug Unlocks only; No Phase 3 Fast-Patching)
"""

import random
import statistics
import time
from collections import defaultdict
from typing import Dict, List, Tuple
from sim.config import CubeColor, DieColor, GameConfig, ShieldColor
from sim.engine import GameEngine, phase1_boot, phase2_threat, phase3_ops
from sim.bots import AdaptiveBalancedBot, SecOpsTurtleBot, VentureGreedBot, AccelerationistBot
from sim.bots.base import BaseBot
from sim.entities import get_random_version_deck, Die, Face


class FastPatchOnlyBotWrapper:
    """Wraps any bot to disable Phase 1 Debug Unlocks, reserving all patches for Phase 3 Fast-Patching."""

    def __init__(self, inner_bot: BaseBot):
        self.inner_bot = inner_bot
        self.bot_id = inner_bot.bot_id
        self.name = f"FPOnly_{inner_bot.name}"

    def __getattr__(self, name):
        return getattr(self.inner_bot, name)

    def choose_debug_unlocks(self, *args, **kwargs) -> List[int]:
        # Disallow spending patches on unlocking locked/glitched dice in Phase 1
        return []

    def choose_yahtzee_rerolls(self, *args, **kwargs):
        res = self.inner_bot.choose_yahtzee_rerolls(*args, **kwargs)
        if isinstance(res, tuple) and len(res) == 2:
            return ([], res[1])
        return res

    # choose_fast_patches remains fully enabled from inner_bot!


class NoFastPatchBotWrapper:
    """Wraps any bot to disable Phase 3 Fast-Patching, allowing only Phase 1 Debug Unlocks."""

    def __init__(self, inner_bot: BaseBot):
        self.inner_bot = inner_bot
        self.bot_id = inner_bot.bot_id
        self.name = f"NoFP_{inner_bot.name}"

    def __getattr__(self, name):
        return getattr(self.inner_bot, name)

    def choose_fast_patches(self, *args, **kwargs) -> List[int]:
        return []


def run_experiment(num_games: int = 1000, player_counts: List[int] = [4, 2]):
    print(f"================ THREE-WAY EXPERIMENT: PATCH MECHANICS IN V0.22.0 (N={num_games} games/pod) ================\n")

    modes = [
        ("BASELINE", "v0.22.0 Baseline (Debug Unlocks + Fast-Patches)"),
        ("FAST_PATCH_ONLY", "Variant: Fast-Patch ONLY (No Phase 1 Debug Unlocks)"),
        ("NO_FAST_PATCH", "Variant: No Fast-Patch (Debug Unlocks ONLY)"),
    ]

    for p_count in player_counts:
        print(f"\n>>>>>>>>>>>>>>>>>>>>>>>>>>>> POD: {p_count}-PLAYER (Pod {p_count}P) <<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        summary_results = {}

        for mode_key, mode_title in modes:
            start_t = time.time()

            rounds = []
            wipeouts = 0
            singularities = 0
            v3_reached = 0

            ready_pool_history = []
            roll_glitches_history = []
            green_glitches_history = []
            corr_glitches_history = []
            total_glitches_history = []

            debug_patches_history = []
            fast_patches_history = []
            total_patches_history = []

            final_secrets = []
            final_money = []
            final_patches = []

            for seed in range(num_games):
                rng = random.Random(seed)
                cfg = GameConfig(num_players=p_count)
                raw_bots = [
                    AdaptiveBalancedBot(0),
                    SecOpsTurtleBot(1),
                    VentureGreedBot(2),
                    AccelerationistBot(3),
                ][:p_count]

                if mode_key == "BASELINE":
                    bots = raw_bots
                elif mode_key == "FAST_PATCH_ONLY":
                    bots = [FastPatchOnlyBotWrapper(b) for b in raw_bots]
                elif mode_key == "NO_FAST_PATCH":
                    bots = [NoFastPatchBotWrapper(b) for b in raw_bots]

                deck = get_random_version_deck(rng)
                eng = GameEngine(config=cfg, bots=bots, seed=seed, version_deck=deck)

                round_corr_demotions = defaultdict(int)
                round_green_glitches = defaultdict(int)

                orig_resolve_corr_space = phase2_threat.resolve_corruption_space

                def hooked_resolve_corruption_space(engine, space, player_commitments, exited_cubes):
                    pre_counts = {p.player_id: len(p.glitched_dice) for p in engine.state.players}
                    orig_resolve_corr_space(engine, space, player_commitments, exited_cubes)
                    for p in engine.state.players:
                        added = len(p.glitched_dice) - pre_counts[p.player_id]
                        if added > 0:
                            round_corr_demotions[p.player_id] += added

                phase2_threat.resolve_corruption_space = hooked_resolve_corruption_space

                orig_resolve_defense = phase2_threat.resolve_player_defense_and_wear

                def hooked_resolve_defense(engine, player, rolled_dice, commitments, attack_strengths, exited_cubes, active_directive):
                    pre_count = len(player.glitched_dice)
                    orig_resolve_defense(engine, player, rolled_dice, commitments, attack_strengths, exited_cubes, active_directive)
                    added = len(player.glitched_dice) - pre_count
                    if added > 0:
                        round_green_glitches[player.player_id] += added

                phase2_threat.resolve_player_defense_and_wear = hooked_resolve_defense

                seen_v3 = False

                try:
                    while not eng.state.game_over:
                        v_str = eng.state.active_version.version_str
                        if v_str == "v3.0":
                            seen_v3 = True

                        round_corr_demotions.clear()
                        round_green_glitches.clear()

                        pre_patches = {p.player_id: p.patches for p in eng.state.players}
                        pre_ready_len = {p.player_id: len(p.ready_for_release_dice) for p in eng.state.players}
                        pre_glitched_len = {p.player_id: len(p.glitched_dice) for p in eng.state.players}
                        pre_fp = {p.player_id: getattr(p, "total_fast_patches", 0) for p in eng.state.players}

                        commitments = eng._execute_phase_1()

                        p1_debug_patches = {}
                        p1_roll_glitches = {}
                        for p in eng.state.players:
                            if p.is_patient_zero:
                                continue
                            dp = max(0, pre_patches[p.player_id] - p.patches)
                            rg = max(0, len(p.glitched_dice) - pre_glitched_len[p.player_id])
                            p1_debug_patches[p.player_id] = dp
                            p1_roll_glitches[p.player_id] = rg

                        telemetry = eng._execute_phase_2(commitments)

                        p3_fast_patches = {}
                        if not eng.state.game_over:
                            eng._execute_phase_3()
                            for p in eng.state.players:
                                if p.is_patient_zero:
                                    continue
                                fp = max(0, getattr(p, "total_fast_patches", 0) - pre_fp[p.player_id])
                                p3_fast_patches[p.player_id] = fp

                            if eng.state.is_final_round:
                                eng.state.game_over = True
                            else:
                                eng.state.current_round += 1
                                if eng.state.current_round > eng.state.config.max_rounds:
                                    eng.state.game_over = True
                        else:
                            for p in eng.state.players:
                                p3_fast_patches[p.player_id] = 0

                        for p in eng.state.players:
                            if p.is_patient_zero:
                                continue
                            pid = p.player_id
                            rg = p1_roll_glitches.get(pid, 0)
                            gg = round_green_glitches.get(pid, 0)
                            cg = round_corr_demotions.get(pid, 0)
                            dp = p1_debug_patches.get(pid, 0)
                            fp = p3_fast_patches.get(pid, 0)

                            ready_pool_history.append(pre_ready_len[pid])
                            roll_glitches_history.append(rg)
                            green_glitches_history.append(gg)
                            corr_glitches_history.append(cg)
                            total_glitches_history.append(rg + gg + cg)

                            debug_patches_history.append(dp)
                            fast_patches_history.append(fp)
                            total_patches_history.append(dp + fp)

                finally:
                    phase2_threat.resolve_corruption_space = orig_resolve_corr_space
                    phase2_threat.resolve_player_defense_and_wear = orig_resolve_defense

                res = eng.evaluate_end_game()
                rounds.append(res.total_rounds)
                if res.end_reason.value == "total_wipeout":
                    wipeouts += 1
                if res.singularity_reached or res.end_reason.value == "singularity":
                    singularities += 1
                if seen_v3:
                    v3_reached += 1

                for p in eng.state.players:
                    final_secrets.append(p.secrets)
                    final_money.append(p.money)
                    final_patches.append(p.patches)

            elapsed = time.time() - start_t
            summary_results[mode_key] = {
                "title": mode_title,
                "mean_rds": statistics.mean(rounds),
                "med_rds": statistics.median(rounds),
                "v3_pct": (v3_reached / num_games) * 100,
                "wipeout_pct": (wipeouts / num_games) * 100,
                "singularity_pct": (singularities / num_games) * 100,
                "ready_pool": statistics.mean(ready_pool_history),
                "roll_glitch": statistics.mean(roll_glitches_history),
                "green_glitch": statistics.mean(green_glitches_history),
                "corr_glitch": statistics.mean(corr_glitches_history),
                "total_glitch": statistics.mean(total_glitches_history),
                "debug_patches": statistics.mean(debug_patches_history),
                "fast_patches": statistics.mean(fast_patches_history),
                "total_patches": statistics.mean(total_patches_history),
                "final_sec": statistics.mean(final_secrets),
                "final_mon": statistics.mean(final_money),
                "final_pat": statistics.mean(final_patches),
                "elapsed": elapsed,
            }

            print(f"Finished {mode_key} ({num_games} matches in {elapsed:.1f}s)")

        # Format comparison table for pod
        print(f"\n--- POD {p_count}P RESULTS SUMMARY ---")
        print(f"{'Metric':<32} | {'BASELINE':<15} | {'FAST-PATCH ONLY':<17} | {'NO FAST-PATCH':<15}")
        print("-" * 88)
        b = summary_results["BASELINE"]
        fp = summary_results["FAST_PATCH_ONLY"]
        nfp = summary_results["NO_FAST_PATCH"]

        print(f"{'Mean Duration (rounds)':<32} | {b['mean_rds']:<15.2f} | {fp['mean_rds']:<17.2f} | {nfp['mean_rds']:<15.2f}")
        print(f"{'Median Duration (rounds)':<32} | {b['med_rds']:<15.1f} | {fp['med_rds']:<17.1f} | {nfp['med_rds']:<15.1f}")
        print(f"{'v3.0 Reach Rate (%)':<32} | {b['v3_pct']:<15.1f} | {fp['v3_pct']:<17.1f} | {nfp['v3_pct']:<15.1f}")
        print(f"{'Total Wipeout Rate (%)':<32} | {b['wipeout_pct']:<15.1f} | {fp['wipeout_pct']:<17.1f} | {nfp['wipeout_pct']:<15.1f}")
        print(f"{'Avg Ready Pool (dice/rd)':<32} | {b['ready_pool']:<15.2f} | {fp['ready_pool']:<17.2f} | {nfp['ready_pool']:<15.2f}")
        print(f"{'Roll Glitches (dice/rd)':<32} | {b['roll_glitch']:<15.2f} | {fp['roll_glitch']:<17.2f} | {nfp['roll_glitch']:<15.2f}")
        print(f"{'Green Malware (dice/rd)':<32} | {b['green_glitch']:<15.2f} | {fp['green_glitch']:<17.2f} | {nfp['green_glitch']:<15.2f}")
        print(f"{'Corruption (dice/rd)':<32} | {b['corr_glitch']:<15.2f} | {fp['corr_glitch']:<17.2f} | {nfp['corr_glitch']:<15.2f}")
        print(f"{'TOTAL Glitches (dice/rd)':<32} | {b['total_glitch']:<15.2f} | {fp['total_glitch']:<17.2f} | {nfp['total_glitch']:<15.2f}")
        print(f"{'Phase 1 Debug Unlocks (🔬/rd)':<32} | {b['debug_patches']:<15.2f} | {fp['debug_patches']:<17.2f} | {nfp['debug_patches']:<15.2f}")
        print(f"{'Phase 3 Fast-Patches (🔬/rd)':<32} | {b['fast_patches']:<15.2f} | {fp['fast_patches']:<17.2f} | {nfp['fast_patches']:<15.2f}")
        print(f"{'TOTAL Patches Spent (🔬/rd)':<32} | {b['total_patches']:<15.2f} | {fp['total_patches']:<17.2f} | {nfp['total_patches']:<15.2f}")
        print(f"{'Final Secrets (Mean)':<32} | {b['final_sec']:<15.2f} | {fp['final_sec']:<17.2f} | {nfp['final_sec']:<15.2f}")
        print(f"{'Final Money (Mean)':<32} | ${b['final_mon']:<14.2f} | ${fp['final_mon']:<16.2f} | ${nfp['final_mon']:<14.2f}")
        print(f"{'Ending Unspent Patches':<32} | {b['final_pat']:<15.2f} | {fp['final_pat']:<17.2f} | {nfp['final_pat']:<15.2f}")
        print()


if __name__ == "__main__":
    run_experiment(num_games=1000, player_counts=[4, 2])
