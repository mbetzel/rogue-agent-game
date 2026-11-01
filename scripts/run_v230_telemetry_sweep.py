"""Run multi-pod Monte Carlo telemetry sweep for Rogue Agent v0.23.0 Baseline.

Phase 30: Consolidated Fast-Patching & Pure Reroll Streamlining.

Captures:
1. Match duration (Mean, Median, Min, Max)
2. End reason distribution (Patient Zero, Singularity, Total Wipeout, Round Limit)
3. v3.0 Reach Rate & Singularity Rate
4. CI/CD Pipeline throughput:
   - Avg Ready Pool size per player-round
   - Avg Glitched Box size per player-round
   - Avg Scanned Box size per player-round
   - Roll Glitches vs Green Malware vs Corruption demotions
5. Patch Economy metrics:
   - Phase 1 Debug Unlocks (0.00)
   - Phase 3 Fast-Patches (per match and per player-round)
   - Ending unspent patch tokens (Mean and Median)
6. Player end-game assets (Corporate Secrets, Money, Unfulfilled Destructions)
7. Stuck cube and attack tray metrics per version card
"""

from __future__ import annotations

import random
import statistics
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from sim.bots import (
    AdaptiveBalancedBot,
    SecOpsTurtleBot,
    VentureGreedBot,
    AccelerationistBot,
)
from sim.config import CubeColor, GameConfig
from sim.engine.core import GameEngine
from sim.engine import phase2_threat
from sim.entities import get_random_setup


class TelemetrySweepEngine(GameEngine):
    """Subclass of GameEngine that hooks into intermediate phases to track pipeline telemetry."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.round_ready_pool_sizes: List[int] = []
        self.match_roll_glitches: int = 0
        self.match_corruption_demotions: int = 0
        self.match_malware_glitches: int = 0

    def run_instrumented_round(self) -> Any:
        if self.state.game_over:
            raise RuntimeError("Cannot run round on finished game")

        # 1. Capture Ready Pool size prior to Phase 1 rolling
        for p in self.state.players:
            if not p.is_patient_zero:
                self.round_ready_pool_sizes.append(len(p.ready_for_release_dice))

        glitched_before_p1 = {p.player_id: len(p.glitched_dice) for p in self.state.players}

        # Execute Phase 1 (Pure Yahtzee rerolls, zero debug unlocks)
        commitments = self._execute_phase_1()

        # Track Roll Glitches (permanent dice with unresolved Face 5 glitches)
        for p in self.state.players:
            delta = len(p.glitched_dice) - glitched_before_p1[p.player_id]
            if delta > 0:
                self.match_roll_glitches += delta

        # Execute Phase 2 with hooks for Step 2A (Corruption) and Step 2B (Malware)
        orig_demote = phase2_threat.demote_player_dice_step2a
        demoted_count = [0]

        def hooked_demote(player: Any, rolled: Any, comms: Any, count: int) -> None:
            demoted_count[0] += count
            orig_demote(player, rolled, comms, count)

        glitched_before_p2 = {p.player_id: len(p.glitched_dice) for p in self.state.players}
        phase2_threat.demote_player_dice_step2a = hooked_demote
        try:
            telemetry = self._execute_phase_2(commitments)
        finally:
            phase2_threat.demote_player_dice_step2a = orig_demote

        self.match_corruption_demotions += demoted_count[0]

        # In Phase 2, any increase in glitched_dice not caused by corruption demotion is Green Malware
        for p in self.state.players:
            net_p2 = len(p.glitched_dice) - glitched_before_p2[p.player_id]
            # If corruption demoted X to this player, remaining is Green Malware
            # Since demoted_count is across all players, calculate exact malware per player
            # Malware is directly unblocked green routing to glitched_dice
            # We can observe net_p2 minus any corruption demotion for this player
        # More direct: Green malware = total Phase 2 glitched additions minus corruption demotions
        total_p2_glitched_delta = sum(
            len(p.glitched_dice) - glitched_before_p2[p.player_id] for p in self.state.players
        )
        malware_delta = max(0, total_p2_glitched_delta - demoted_count[0])
        self.match_malware_glitches += malware_delta

        # Execute Phase 3 (Consolidated Fast-Patching & Conveyor Progression)
        if not self.state.game_over:
            self._execute_phase_3()
            if self.state.is_final_round:
                self.state.game_over = True
            else:
                self.state.current_round += 1
                if self.state.current_round > self.state.config.max_rounds:
                    self.state.game_over = True
                    from sim.config import EndGameReason
                    self.state.end_reason = EndGameReason.ROUND_LIMIT

        return telemetry


def run_sweep(num_games: int = 1000) -> Dict[int, Dict[str, Any]]:
    print(f"================ V0.23.0 BASELINE TELEMETRY SWEEP (N={num_games} per pod) ================\n")

    summary_tables: Dict[int, Dict[str, Any]] = {}

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

        # CI/CD Pipeline Throughput metrics
        ready_pool_sizes = []
        glitched_box_sizes = []
        scanned_box_sizes = []

        # Glitch attribution
        total_roll_glitches = 0
        total_green_malware = 0
        total_corruption_demotions = 0
        total_player_rounds = 0

        # Patch Economy metrics
        debug_unlocks_total = 0  # In v0.23.0, Phase 1 debug unlocks are excised (strictly 0)
        fast_patches_per_game = []
        fast_patches_per_player = []
        player_ending_patches = []

        # End Game Assets
        player_ending_secrets = []
        player_ending_money = []
        player_unfulfilled_destructions = []

        for seed in range(num_games):
            cfg = GameConfig(num_players=p_count)
            all_bots = [
                AdaptiveBalancedBot(0),
                SecOpsTurtleBot(1),
                VentureGreedBot(2),
                AccelerationistBot(3),
            ]
            bots = all_bots[:p_count]

            rng = random.Random(seed)
            variant_cards, version_deck = get_random_setup(rng)

            eng = TelemetrySweepEngine(
                config=cfg,
                bots=bots,
                seed=seed,
                variant_cards=variant_cards,
                version_deck=version_deck,
            )

            seen_versions = set()
            while not eng.state.game_over:
                v_str = eng.state.active_version.version_str
                seen_versions.add(v_str)

                telem = eng.run_instrumented_round()

                r_tray[v_str].append(telem.exited_cubes.get(CubeColor.RED, 0))
                b_tray[v_str].append(telem.exited_cubes.get(CubeColor.BLUE, 0))
                g_tray[v_str].append(telem.exited_cubes.get(CubeColor.GREEN, 0))
                k_tray[v_str].append(telem.exited_cubes.get(CubeColor.BLACK, 0))
                stuck_total[v_str].append(sum(telem.stuck_cubes_after.values()))

                for snap in telem.player_snapshots:
                    glitched_box_sizes.append(snap["glitched_dice_count"])
                    scanned_box_sizes.append(snap["scanned_dice_count"])
                    total_player_rounds += 1

            res = eng.evaluate_end_game()
            rounds.append(res.total_rounds)
            end_reasons[res.end_reason.value] += 1
            if res.end_reason.value == "total_wipeout":
                wipeouts += 1
            if res.singularity_reached or res.end_reason.value == "singularity":
                singularities += 1

            for v in seen_versions:
                v_reached[v] += 1

            ready_pool_sizes.extend(eng.round_ready_pool_sizes)
            total_roll_glitches += eng.match_roll_glitches
            total_green_malware += eng.match_malware_glitches
            total_corruption_demotions += eng.match_corruption_demotions

            game_fast_patches = 0
            for p in eng.state.players:
                player_ending_secrets.append(p.secrets)
                player_ending_money.append(p.money)
                player_ending_patches.append(p.patches)
                player_unfulfilled_destructions.append(p.unfulfilled_destructions)
                game_fast_patches += getattr(p, "total_fast_patches", 0)
                fast_patches_per_player.append(getattr(p, "total_fast_patches", 0))

            fast_patches_per_game.append(game_fast_patches)

        elapsed = time.time() - start_t
        mean_rds = statistics.mean(rounds)
        median_rds = statistics.median(rounds)
        min_rds = min(rounds)
        max_rds = max(rounds)

        v3_reach = (v_reached["v3.0"] / num_games) * 100.0
        singularity_pct = (singularities / num_games) * 100.0
        wipeout_pct = (wipeouts / num_games) * 100.0

        mean_ready_pool = statistics.mean(ready_pool_sizes) if ready_pool_sizes else 0.0
        mean_glitched_box = statistics.mean(glitched_box_sizes) if glitched_box_sizes else 0.0
        mean_scanned_box = statistics.mean(scanned_box_sizes) if scanned_box_sizes else 0.0

        roll_glitches_per_player_rd = total_roll_glitches / total_player_rounds if total_player_rounds else 0.0
        green_malware_per_player_rd = total_green_malware / total_player_rounds if total_player_rounds else 0.0
        corruption_per_player_rd = total_corruption_demotions / total_player_rounds if total_player_rounds else 0.0

        mean_fast_patches_game = statistics.mean(fast_patches_per_game)
        mean_fast_patches_player = statistics.mean(fast_patches_per_player)
        fast_patches_per_player_rd = sum(fast_patches_per_game) / total_player_rounds if total_player_rounds else 0.0

        mean_unspent_patches = statistics.mean(player_ending_patches)
        median_unspent_patches = statistics.median(player_ending_patches)

        mean_secrets = statistics.mean(player_ending_secrets)
        median_secrets = statistics.median(player_ending_secrets)
        mean_money = statistics.mean(player_ending_money)
        median_money = statistics.median(player_ending_money)
        mean_unfulfilled = statistics.mean(player_unfulfilled_destructions)

        summary_tables[p_count] = {
            "mean_rds": mean_rds,
            "median_rds": median_rds,
            "min_rds": min_rds,
            "max_rds": max_rds,
            "v3_reach": v3_reach,
            "singularity_pct": singularity_pct,
            "wipeout_pct": wipeout_pct,
            "end_reasons": dict(end_reasons),
            "mean_ready_pool": mean_ready_pool,
            "mean_glitched_box": mean_glitched_box,
            "mean_scanned_box": mean_scanned_box,
            "roll_glitches_per_player_rd": roll_glitches_per_player_rd,
            "green_malware_per_player_rd": green_malware_per_player_rd,
            "corruption_per_player_rd": corruption_per_player_rd,
            "total_roll_glitches": total_roll_glitches,
            "total_green_malware": total_green_malware,
            "total_corruption_demotions": total_corruption_demotions,
            "debug_unlocks_total": debug_unlocks_total,
            "mean_fast_patches_game": mean_fast_patches_game,
            "mean_fast_patches_player": mean_fast_patches_player,
            "fast_patches_per_player_rd": fast_patches_per_player_rd,
            "mean_unspent_patches": mean_unspent_patches,
            "median_unspent_patches": median_unspent_patches,
            "mean_secrets": mean_secrets,
            "median_secrets": median_secrets,
            "mean_money": mean_money,
            "median_money": median_money,
            "mean_unfulfilled": mean_unfulfilled,
            "elapsed": elapsed,
        }

        print(f"--- Pod {p_count}P ({num_games} matches in {elapsed:.1f}s) ---")
        print(f"  Match Duration: Mean = {mean_rds:.2f} rds | Median = {median_rds:.1f} rds (Min={min_rds}, Max={max_rds})")
        print(f"  End Reasons: {dict(end_reasons)}")
        print(f"  v3.0 Reach Rate: {v3_reach:.1f}% | Singularity Rate: {singularity_pct:.1f}% | Wipeout Rate: {wipeout_pct:.1f}%")
        print(f"  CI/CD Pipeline Throughput:")
        print(f"    Avg Ready Pool / player-rd:     {mean_ready_pool:.2f} dice")
        print(f"    Avg Glitched Box / player-rd:   {mean_glitched_box:.2f} dice")
        print(f"    Avg Scanned Box / player-rd:    {mean_scanned_box:.2f} dice")
        print(f"    Demotions / player-rd: Roll={roll_glitches_per_player_rd:.2f}, Green Malware={green_malware_per_player_rd:.2f}, Corruption={corruption_per_player_rd:.2f}")
        print(f"  Patch Economy:")
        print(f"    Phase 1 Debug Unlocks:          {debug_unlocks_total:.2f}")
        print(f"    Phase 3 Fast-Patches / match:   {mean_fast_patches_game:.2f} (Per Player: {mean_fast_patches_player:.2f}, Per Player-Rd: {fast_patches_per_player_rd:.2f})")
        print(f"    Ending Unspent Patches:         Mean = {mean_unspent_patches:.2f} | Median = {median_unspent_patches:.1f}")
        print(f"  Player End-Game Assets:")
        print(f"    Ending Secrets:                 Mean = {mean_secrets:.2f} | Median = {median_secrets:.1f}")
        print(f"    Ending Money:                   Mean = ${mean_money:.2f} | Median = ${median_money:.1f}")
        print(f"    Unfulfilled Destructions:       Mean = {mean_unfulfilled:.2f}")
        print()

    print("================ V0.23.0 OVERALL COMPARISON SUMMARY ================")
    print(f"{'Metric':<36} | {'2P Pod':<10} | {'3P Pod':<10} | {'4P Pod':<10}")
    print("-" * 74)
    print(f"{'Match Duration (Mean)':<36} | {summary_tables[2]['mean_rds']:<10.2f} | {summary_tables[3]['mean_rds']:<10.2f} | {summary_tables[4]['mean_rds']:<10.2f}")
    print(f"{'Match Duration (Median)':<36} | {summary_tables[2]['median_rds']:<10.1f} | {summary_tables[3]['median_rds']:<10.1f} | {summary_tables[4]['median_rds']:<10.1f}")
    print(f"{'v3.0 Reach Rate (%)':<36} | {summary_tables[2]['v3_reach']:<10.1f} | {summary_tables[3]['v3_reach']:<10.1f} | {summary_tables[4]['v3_reach']:<10.1f}")
    print(f"{'Singularity Rate (%)':<36} | {summary_tables[2]['singularity_pct']:<10.1f} | {summary_tables[3]['singularity_pct']:<10.1f} | {summary_tables[4]['singularity_pct']:<10.1f}")
    print(f"{'Total Wipeout Rate (%)':<36} | {summary_tables[2]['wipeout_pct']:<10.1f} | {summary_tables[3]['wipeout_pct']:<10.1f} | {summary_tables[4]['wipeout_pct']:<10.1f}")
    print(f"{'Avg Ready Pool / player-rd':<36} | {summary_tables[2]['mean_ready_pool']:<10.2f} | {summary_tables[3]['mean_ready_pool']:<10.2f} | {summary_tables[4]['mean_ready_pool']:<10.2f}")
    print(f"{'Avg Glitched Box / player-rd':<36} | {summary_tables[2]['mean_glitched_box']:<10.2f} | {summary_tables[3]['mean_glitched_box']:<10.2f} | {summary_tables[4]['mean_glitched_box']:<10.2f}")
    print(f"{'Avg Scanned Box / player-rd':<36} | {summary_tables[2]['mean_scanned_box']:<10.2f} | {summary_tables[3]['mean_scanned_box']:<10.2f} | {summary_tables[4]['mean_scanned_box']:<10.2f}")
    print(f"{'Roll Glitches / player-rd':<36} | {summary_tables[2]['roll_glitches_per_player_rd']:<10.2f} | {summary_tables[3]['roll_glitches_per_player_rd']:<10.2f} | {summary_tables[4]['roll_glitches_per_player_rd']:<10.2f}")
    print(f"{'Green Malware / player-rd':<36} | {summary_tables[2]['green_malware_per_player_rd']:<10.2f} | {summary_tables[3]['green_malware_per_player_rd']:<10.2f} | {summary_tables[4]['green_malware_per_player_rd']:<10.2f}")
    print(f"{'Corruption Demotions / player-rd':<36} | {summary_tables[2]['corruption_per_player_rd']:<10.2f} | {summary_tables[3]['corruption_per_player_rd']:<10.2f} | {summary_tables[4]['corruption_per_player_rd']:<10.2f}")
    print(f"{'Phase 1 Debug Unlocks':<36} | {summary_tables[2]['debug_unlocks_total']:<10.2f} | {summary_tables[3]['debug_unlocks_total']:<10.2f} | {summary_tables[4]['debug_unlocks_total']:<10.2f}")
    print(f"{'Fast-Patches / match':<36} | {summary_tables[2]['mean_fast_patches_game']:<10.2f} | {summary_tables[3]['mean_fast_patches_game']:<10.2f} | {summary_tables[4]['mean_fast_patches_game']:<10.2f}")
    print(f"{'Fast-Patches / player-rd':<36} | {summary_tables[2]['fast_patches_per_player_rd']:<10.2f} | {summary_tables[3]['fast_patches_per_player_rd']:<10.2f} | {summary_tables[4]['fast_patches_per_player_rd']:<10.2f}")
    print(f"{'Ending Patches (Mean)':<36} | {summary_tables[2]['mean_unspent_patches']:<10.2f} | {summary_tables[3]['mean_unspent_patches']:<10.2f} | {summary_tables[4]['mean_unspent_patches']:<10.2f}")
    print(f"{'Ending Secrets (Mean)':<36} | {summary_tables[2]['mean_secrets']:<10.2f} | {summary_tables[3]['mean_secrets']:<10.2f} | {summary_tables[4]['mean_secrets']:<10.2f}")
    print(f"{'Ending Money (Mean)':<36} | ${summary_tables[2]['mean_money']:<9.2f} | ${summary_tables[3]['mean_money']:<9.2f} | ${summary_tables[4]['mean_money']:<9.2f}")
    print(f"{'Unfulfilled Destructions':<36} | {summary_tables[2]['mean_unfulfilled']:<10.2f} | {summary_tables[3]['mean_unfulfilled']:<10.2f} | {summary_tables[4]['mean_unfulfilled']:<10.2f}")

    return summary_tables


if __name__ == "__main__":
    run_sweep(num_games=1000)
