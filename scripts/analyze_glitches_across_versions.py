# NOTE (v0.34.0): this script targets the v0.33-era module layout (phase1_boot / phase2_threat /
# phase3_ops). After the six-phase module split, its monkeypatches of those modules may no longer
# take effect on either round sequence (legacy_v033 binds the new modules). Results are historical.
"""Analyze glitched dice by source across versions with and without patch usage.

Supports:
- Standard Roadmap (Script Kiddie -> RaaS -> Zero-Day)
- Randomized Roadmaps (All 8 version card paths including Polymorphic Worm & Corrupted Kernel)
- Pods: 2P, 3P, 4P
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
from sim.entities import get_default_version_deck, get_random_version_deck, Die, Face


class NoPatchBotWrapper:
    """Wraps any bot to disallow patch expenditure (no Phase 1 debug unlocks, no Phase 3 fast-patching)."""

    def __init__(self, inner_bot: BaseBot):
        self.inner_bot = inner_bot
        self.bot_id = inner_bot.bot_id
        self.name = f"NoPatch_{inner_bot.name}"

    def __getattr__(self, name):
        return getattr(self.inner_bot, name)

    def choose_debug_unlocks(self, *args, **kwargs) -> List[int]:
        return []

    def choose_yahtzee_rerolls(self, *args, **kwargs):
        res = self.inner_bot.choose_yahtzee_rerolls(*args, **kwargs)
        if isinstance(res, tuple) and len(res) == 2:
            return ([], res[1])
        return res

    def choose_fast_patches(self, *args, **kwargs) -> List[int]:
        return []


def run_experiment(num_games: int = 1000, player_counts: List[int] = [2, 3, 4], randomize_decks: bool = True):
    mode_label = "RANDOMIZED ROADMAPS (All 8 Variant Paths)" if randomize_decks else "STANDARD ROADMAP"
    print(f"\n{'='*30} {mode_label} (N={num_games} games/pod) {'='*30}\n")

    for p_count in player_counts:
        print(f"\n>>>>>>>>>>>>>>>>>>>> POD: {p_count}-PLAYER (Pod {p_count}P) <<<<<<<<<<<<<<<<<<<<")
        for mode in ["WITH_PATCHES", "WITHOUT_PATCHES"]:
            use_patches = (mode == "WITH_PATCHES")
            start_t = time.time()

            # Version-keyed stats: per player-round
            roll_glitches_by_v = defaultdict(list)
            green_glitches_by_v = defaultdict(list)
            corruption_glitches_by_v = defaultdict(list)
            total_glitches_by_v = defaultdict(list)
            ready_pool_by_v = defaultdict(list)

            # Patches used by version (per player-round)
            debug_patches_by_v = defaultdict(list)
            fast_patches_by_v = defaultdict(list)
            total_patches_by_v = defaultdict(list)

            # Cumulative stats per player per version
            cum_roll_by_v = defaultdict(list)
            cum_green_by_v = defaultdict(list)
            cum_corr_by_v = defaultdict(list)
            cum_total_by_v = defaultdict(list)
            cum_patches_by_v = defaultdict(list)

            rounds_in_version_by_v = defaultdict(list)

            for seed in range(num_games):
                rng = random.Random(seed)
                cfg = GameConfig(num_players=p_count)
                raw_bots = [
                    AdaptiveBalancedBot(0),
                    SecOpsTurtleBot(1),
                    VentureGreedBot(2),
                    AccelerationistBot(3),
                ][:p_count]

                if use_patches:
                    bots = raw_bots
                else:
                    bots = [NoPatchBotWrapper(b) for b in raw_bots]

                if randomize_decks:
                    deck = get_random_version_deck(rng)
                else:
                    deck = get_default_version_deck()

                eng = GameEngine(config=cfg, bots=bots, seed=seed, version_deck=deck)

                v_rounds_count = defaultdict(int)
                p_v_cum_roll = defaultdict(lambda: defaultdict(int))
                p_v_cum_green = defaultdict(lambda: defaultdict(int))
                p_v_cum_corr = defaultdict(lambda: defaultdict(int))
                p_v_cum_total = defaultdict(lambda: defaultdict(int))
                p_v_cum_patches = defaultdict(lambda: defaultdict(int))

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

                try:
                    while not eng.state.game_over:
                        v_str = eng.state.active_version.version_str
                        v_rounds_count[v_str] += 1

                        round_corr_demotions.clear()
                        round_green_glitches.clear()

                        pre_patches = {p.player_id: p.patches for p in eng.state.players}
                        pre_glitched_len = {p.player_id: len(p.glitched_dice) for p in eng.state.players}
                        pre_ready_len = {p.player_id: len(p.ready_for_release_dice) for p in eng.state.players}
                        pre_fp_total = {p.player_id: getattr(p, "total_fast_patches", 0) for p in eng.state.players}

                        commitments = eng._execute_phase_1()

                        p1_debug_patches = {}
                        p1_roll_glitches = {}
                        for p in eng.state.players:
                            if p.is_patient_zero:
                                continue
                            p1_debug_patches[p.player_id] = max(0, pre_patches[p.player_id] - p.patches)
                            p1_roll_glitches[p.player_id] = max(0, len(p.glitched_dice) - pre_glitched_len[p.player_id])

                        telemetry = eng._execute_phase_2(commitments)

                        p3_fast_patches = {}
                        if not eng.state.game_over:
                            eng._execute_phase_3()
                            for p in eng.state.players:
                                if p.is_patient_zero:
                                    continue
                                cur_fp = getattr(p, "total_fast_patches", 0)
                                p3_fast_patches[p.player_id] = max(0, cur_fp - pre_fp_total[p.player_id])

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
                            tot_g = rg + gg + cg

                            dp = p1_debug_patches.get(pid, 0)
                            fp = p3_fast_patches.get(pid, 0)
                            tot_p = dp + fp

                            roll_glitches_by_v[v_str].append(rg)
                            green_glitches_by_v[v_str].append(gg)
                            corruption_glitches_by_v[v_str].append(cg)
                            total_glitches_by_v[v_str].append(tot_g)
                            ready_pool_by_v[v_str].append(pre_ready_len[pid])

                            debug_patches_by_v[v_str].append(dp)
                            fast_patches_by_v[v_str].append(fp)
                            total_patches_by_v[v_str].append(tot_p)

                            p_v_cum_roll[v_str][pid] += rg
                            p_v_cum_green[v_str][pid] += gg
                            p_v_cum_corr[v_str][pid] += cg
                            p_v_cum_total[v_str][pid] += tot_g
                            p_v_cum_patches[v_str][pid] += tot_p

                finally:
                    phase2_threat.resolve_corruption_space = orig_resolve_corr_space
                    phase2_threat.resolve_player_defense_and_wear = orig_resolve_defense

                for v_str in ["v1.0", "v2.0", "v3.0"]:
                    if v_rounds_count[v_str] > 0:
                        rounds_in_version_by_v[v_str].append(v_rounds_count[v_str])
                        for pid in range(p_count):
                            cum_roll_by_v[v_str].append(p_v_cum_roll[v_str][pid])
                            cum_green_by_v[v_str].append(p_v_cum_green[v_str][pid])
                            cum_corr_by_v[v_str].append(p_v_cum_corr[v_str][pid])
                            cum_total_by_v[v_str].append(p_v_cum_total[v_str][pid])
                            cum_patches_by_v[v_str].append(p_v_cum_patches[v_str][pid])

            elapsed = time.time() - start_t
            print(f"--- {mode} ({num_games} matches in {elapsed:.1f}s) ---")
            print(f"{'Version':<8} | {'Mean Rds':<9} | {'Roll Glitch':<12} | {'Green Malware':<14} | {'Corruption':<11} | {'TOTAL Glitches':<15} | {'Patches Used':<13} | {'Ready Pool':<11}")
            print(f"{'':<8} | {'in Ver':<9} | {'(per pl-rd)':<12} | {'(per pl-rd)':<14} | {'(per pl-rd)':<11} | {'(per pl-rd)':<15} | {'(per pl-rd)':<13} | {'(per pl-rd)':<11}")
            print("-" * 105)

            for v in ["v1.0", "v2.0", "v3.0"]:
                if not total_glitches_by_v[v]:
                    continue
                mean_rds = statistics.mean(rounds_in_version_by_v[v]) if rounds_in_version_by_v[v] else 0.0
                m_roll = statistics.mean(roll_glitches_by_v[v])
                m_green = statistics.mean(green_glitches_by_v[v])
                m_corr = statistics.mean(corruption_glitches_by_v[v])
                m_tot = statistics.mean(total_glitches_by_v[v])
                m_pat = statistics.mean(total_patches_by_v[v])
                m_ready = statistics.mean(ready_pool_by_v[v])

                print(f"{v:<8} | {mean_rds:<9.2f} | {m_roll:<12.2f} | {m_green:<14.2f} | {m_corr:<11.2f} | {m_tot:<15.2f} | {m_pat:<13.2f} | {m_ready:<11.2f}")

            if use_patches:
                print("  -> Patch Breakdown (per player per round):")
                for v in ["v1.0", "v2.0", "v3.0"]:
                    if total_patches_by_v[v]:
                        m_dbg = statistics.mean(debug_patches_by_v[v])
                        m_fp = statistics.mean(fast_patches_by_v[v])
                        m_tot = statistics.mean(total_patches_by_v[v])
                        print(f"     {v}: Debug Unlocks = {m_dbg:.2f} 🔧 | Fast-Patches = {m_fp:.2f} 🔧 | Total = {m_tot:.2f} 🔧/pl-rd")
            print()


if __name__ == "__main__":
    run_experiment(num_games=1000, player_counts=[4, 2], randomize_decks=True)
