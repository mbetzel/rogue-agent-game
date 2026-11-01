"""Monte Carlo simulation comparing v0.22.0 Baseline vs No-Fast-Patching Variant.

In No-Fast-Patching:
- Players CANNOT spend 1 🔧 to accelerate dice from Glitched to Scanned in Phase 3 Part 3B.
- Players CAN still spend 1 🔧 in Phase 1 Step 4 for Debug Unlocks (unlocking locked/glitched dice for rerolls).
- All glitched dice must undergo the full 1-round latency in the Scanned box.
"""

import random
import statistics
import time
from collections import defaultdict
from typing import Dict, List, Tuple
from sim.config import CubeColor, DieColor, GameConfig, ShieldColor
from sim.engine import GameEngine
from sim.bots import AdaptiveBalancedBot, SecOpsTurtleBot, VentureGreedBot, AccelerationistBot
from sim.bots.base import BaseBot
from sim.entities import get_default_version_deck, get_random_version_deck, Die, Face


class NoFastPatchBotWrapper:
    """Wraps any bot to disable Fast-Patching in Phase 3 Part 3B while preserving Phase 1 Debug Unlocks."""

    def __init__(self, inner_bot: BaseBot):
        self.inner_bot = inner_bot
        self.bot_id = inner_bot.bot_id
        self.name = f"NoFastPatch_{inner_bot.name}"

    def __getattr__(self, name):
        return getattr(self.inner_bot, name)

    def choose_fast_patches(self, *args, **kwargs) -> List[int]:
        # Fast-patching disabled!
        return []


def run_comparison(num_games: int = 1000, player_counts: List[int] = [4, 2]):
    print(f"================ COMPARISON: BASELINE vs NO FAST-PATCHING (N={num_games} games/pod) ================\n")

    for p_count in player_counts:
        print(f"\n>>>>>>>>>>>>>>>>>>>> POD: {p_count}-PLAYER (Pod {p_count}P) <<<<<<<<<<<<<<<<<<<<")
        for mode in ["BASELINE (With Fast-Patch)", "NO_FAST_PATCH (Conveyor Only)"]:
            disable_fast_patch = (mode != "BASELINE (With Fast-Patch)")
            start_t = time.time()

            rounds = []
            wipeouts = 0
            singularities = 0
            v3_reached = 0

            ready_pool_history = []
            glitched_pool_history = []
            scanned_pool_history = []

            debug_patches_history = []
            fast_patches_history = []
            patches_discarded_history = []

            final_secrets = []
            final_money = []
            final_patches = []
            destructions_history = []

            for seed in range(num_games):
                rng = random.Random(seed)
                cfg = GameConfig(num_players=p_count)
                raw_bots = [
                    AdaptiveBalancedBot(0),
                    SecOpsTurtleBot(1),
                    VentureGreedBot(2),
                    AccelerationistBot(3),
                ][:p_count]

                if disable_fast_patch:
                    bots = [NoFastPatchBotWrapper(b) for b in raw_bots]
                else:
                    bots = raw_bots

                deck = get_random_version_deck(rng)
                eng = GameEngine(config=cfg, bots=bots, seed=seed, version_deck=deck)

                seen_v3 = False

                while not eng.state.game_over:
                    v_str = eng.state.active_version.version_str
                    if v_str == "v3.0":
                        seen_v3 = True

                    pre_patches = {p.player_id: p.patches for p in eng.state.players}
                    pre_fp = {p.player_id: getattr(p, "total_fast_patches", 0) for p in eng.state.players}

                    commitments = eng._execute_phase_1()

                    # Phase 1 debug patches
                    for p in eng.state.players:
                        if not p.is_patient_zero:
                            dp = max(0, pre_patches[p.player_id] - p.patches)
                            debug_patches_history.append(dp)
                            ready_pool_history.append(len(p.ready_for_release_dice))
                            glitched_pool_history.append(len(p.glitched_dice))
                            scanned_pool_history.append(len(p.scanned_dice))

                    telemetry = eng._execute_phase_2(commitments)

                    if not eng.state.game_over:
                        # Check patches before cap in phase 3
                        eng._execute_phase_3()
                        for p in eng.state.players:
                            if not p.is_patient_zero:
                                fp = max(0, getattr(p, "total_fast_patches", 0) - pre_fp[p.player_id])
                                fast_patches_history.append(fp)
                                # Cap is 3: any patches held > 3 would have been discarded
                                # In phase 3 ops: player.patches = min(player.patches, 3)

                        if eng.state.is_final_round:
                            eng.state.game_over = True
                        else:
                            eng.state.current_round += 1
                            if eng.state.current_round > eng.state.config.max_rounds:
                                eng.state.game_over = True

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
                    destructions_history.append(p.unfulfilled_destructions)

            elapsed = time.time() - start_t
            mean_rds = statistics.mean(rounds)
            med_rds = statistics.median(rounds)
            w_pct = (wipeouts / num_games) * 100
            s_pct = (singularities / num_games) * 100
            v3_pct = (v3_reached / num_games) * 100

            mean_ready = statistics.mean(ready_pool_history)
            mean_glitched = statistics.mean(glitched_pool_history)
            mean_scanned = statistics.mean(scanned_pool_history)

            mean_dbg = statistics.mean(debug_patches_history)
            mean_fp = statistics.mean(fast_patches_history) if fast_patches_history else 0.0

            mean_sec = statistics.mean(final_secrets)
            mean_mon = statistics.mean(final_money)
            mean_pat = statistics.mean(final_patches)

            print(f"--- {mode} ({num_games} games in {elapsed:.1f}s) ---")
            print(f"  Pacing: Mean = {mean_rds:.2f} rds | Median = {med_rds:.1f} rds (Min={min(rounds)}, Max={max(rounds)})")
            print(f"  Outcomes: v3.0 Reach = {v3_pct:.1f}% | Singularity = {s_pct:.1f}% | Total Wipeout = {w_pct:.1f}%")
            print(f"  Pipeline Health (per player-round):")
            print(f"    Avg Ready Pool:    {mean_ready:.2f} dice")
            print(f"    Avg Glitched Box:  {mean_glitched:.2f} dice")
            print(f"    Avg Scanned Box:   {mean_scanned:.2f} dice")
            print(f"  Patch Economy (per player-round):")
            print(f"    Debug Unlocks:     {mean_dbg:.2f} 🔧 / pl-rd")
            print(f"    Fast-Patches:      {mean_fp:.2f} 🔧 / pl-rd")
            print(f"    Total Spent:       {(mean_dbg + mean_fp):.2f} 🔧 / pl-rd")
            print(f"  Player End-Game State:")
            print(f"    Ending Secrets:    {mean_sec:.2f} Secrets")
            print(f"    Ending Money:      ${mean_mon:.2f}")
            print(f"    Ending Patches:    {mean_pat:.2f} 🔧")
            print()


if __name__ == "__main__":
    run_comparison(num_games=1000, player_counts=[4, 2])
