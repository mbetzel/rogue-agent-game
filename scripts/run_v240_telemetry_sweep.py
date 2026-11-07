# NOTE (v0.34.0): this script targets the v0.33-era module layout (phase1_boot / phase2_threat /
# phase3_ops). After the six-phase module split, its monkeypatches of those modules may no longer
# take effect on either round sequence (legacy_v033 binds the new modules). Results are historical.
"""Run multi-pod Monte Carlo telemetry sweep for Rogue Agent v0.24.0 Baseline.

Phase 31: Proprietary Specialist (Purple) Dice Overhaul & Personal Reserve.

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
   - Phase 3 Fast-Patches (per match, per player, and per player-round)
   - Ending unspent patch tokens (Mean and Median)
6. Player end-game assets (Corporate Secrets, Money, Unfulfilled Destructions)
7. Phase 31 Specialist / Personal Reserve metrics:
   - Purple Reserve Procurement Rate (per match, per player, % buying >= 1, % capacity)
   - Purple Star activations (total Purple Stars rolled/triggered per game)
   - Face 6 Archetype Signature Protocol activations breakdown:
     * Acoustic: Resonance Sensor
     * Phreaker: Jumper Diagnostics
     * Prodigy: Arbitrary Code Execution
     * Spook: Burn Notice (+ die burned count)
     * Cipher: Algorithmic Parity (Phase 1 wildcard triplet + Phase 3A income)
     * Operator: Contingent Staffing
   - Archetype Win Rates and Survival Rates across the 6 archetypes (Acoustic, Phreaker, Prodigy, Spook, Cipher, Operator)
     verifying the target corridor (20%–30% in 4P).
"""

from __future__ import annotations

import os
import random
import statistics
import sys
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sim.bots import (
    AdaptiveBalancedBot,
    SecOpsTurtleBot,
    VentureGreedBot,
    AccelerationistBot,
)
from sim.config import CubeColor, DieColor, GameConfig
from sim.engine.core import GameEngine
from sim.engine import phase1_boot, phase2_threat, phase3_ops
from sim.entities import ArchetypeCode, get_random_setup


class TelemetrySweepEngineV240(GameEngine):
    """Subclass of GameEngine that hooks into intermediate phases to track pipeline and Face 6 protocol telemetry."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.round_ready_pool_sizes: List[int] = []
        self.match_roll_glitches: int = 0
        self.match_corruption_demotions: int = 0
        self.match_malware_glitches: int = 0

        # Phase 31 Telemetry Counters
        self.match_purple_stars_rolled: int = 0
        self.match_purple_stars_in_production: int = 0
        self.protocol_activations: Dict[str, int] = {
            ArchetypeCode.ACOUSTIC.value: 0,
            ArchetypeCode.PHREAKER.value: 0,
            ArchetypeCode.PRODIGY.value: 0,
            ArchetypeCode.SPOOK.value: 0,
            ArchetypeCode.CIPHER.value: 0,
            ArchetypeCode.OPERATOR.value: 0,
        }
        self.spook_dice_burned: int = 0

    def run_instrumented_round(self) -> Any:
        if self.state.game_over:
            raise RuntimeError("Cannot run round on finished game")

        # 1. Capture Ready Pool size prior to Phase 1 rolling
        for p in self.state.players:
            if not p.is_patient_zero:
                self.round_ready_pool_sizes.append(len(p.ready_for_release_dice))

        glitched_before_p1 = {p.player_id: len(p.glitched_dice) for p in self.state.players}

        # --- Phase 1 Hooks: Operator, Prodigy, Cipher, and Roll Glitches ---
        orig_operator_staffing = phase1_boot.check_operator_contingent_staffing
        orig_prodigy_override = phase1_boot.resolve_prodigy_purple_star_override
        orig_cipher_hash = phase1_boot.detect_hash_matches_with_cipher

        operator_triggers = [0]
        prodigy_triggers = [0]
        cipher_wildcard_triggers = [0]

        def hooked_operator_staffing(engine: Any, player: Any, active_dice: Any) -> Any:
            c_die = orig_operator_staffing(engine, player, active_dice)
            if c_die is not None:
                operator_triggers[0] += 1
            return c_die

        def hooked_prodigy_override(*args: Any, **kwargs: Any) -> bool:
            res = orig_prodigy_override(*args, **kwargs)
            if res:
                prodigy_triggers[0] += 1
            return res

        def hooked_cipher_hash(dice: Any, is_cipher: bool = False) -> int:
            if is_cipher:
                # Check if a Purple Star is present and can complete a pair
                has_purple_star = any(
                    (d.effective_face or d.current_face)
                    and (d.effective_face or d.current_face).is_star
                    and (d.effective_face or d.current_face).star_code == "PURPLE_STAR"
                    for d in dice
                )
                if has_purple_star:
                    # Check if natural count == 2 exists
                    counts: Dict[Any, int] = {}
                    for d in dice:
                        eff = d.effective_face
                        if not eff or eff.is_glitch or (eff.is_star and eff.star_code == "PURPLE_STAR"):
                            continue
                        sig = phase1_boot.get_face_signature(eff)
                        if sig is not None:
                            counts[sig] = counts.get(sig, 0) + 1
                    if any(cnt == 2 for cnt in counts.values()):
                        cipher_wildcard_triggers[0] += 1
            return orig_cipher_hash(dice, is_cipher=is_cipher)

        phase1_boot.check_operator_contingent_staffing = hooked_operator_staffing
        phase1_boot.resolve_prodigy_purple_star_override = hooked_prodigy_override
        phase1_boot.detect_hash_matches_with_cipher = hooked_cipher_hash

        try:
            commitments = self._execute_phase_1()
        finally:
            phase1_boot.check_operator_contingent_staffing = orig_operator_staffing
            phase1_boot.resolve_prodigy_purple_star_override = orig_prodigy_override
            phase1_boot.detect_hash_matches_with_cipher = orig_cipher_hash

        self.protocol_activations[ArchetypeCode.OPERATOR.value] += operator_triggers[0]
        self.protocol_activations[ArchetypeCode.PRODIGY.value] += prodigy_triggers[0]
        self.protocol_activations[ArchetypeCode.CIPHER.value] += cipher_wildcard_triggers[0]

        # Track Purple Stars deployed to In Production this round
        round_purple_stars = sum(p.purple_star_count for p in self.state.players if not p.is_patient_zero)
        self.match_purple_stars_in_production += round_purple_stars

        # Track Roll Glitches (permanent dice with unresolved Face 5 glitches)
        for p in self.state.players:
            delta = len(p.glitched_dice) - glitched_before_p1[p.player_id]
            if delta > 0:
                self.match_roll_glitches += delta

        # --- Phase 2: Threat Evaluation with Corruption / Malware Hooks ---
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

        # Green malware = total Phase 2 glitched delta minus corruption demotions
        total_p2_glitched_delta = sum(
            len(p.glitched_dice) - glitched_before_p2[p.player_id] for p in self.state.players
        )
        malware_delta = max(0, total_p2_glitched_delta - demoted_count[0])
        self.match_malware_glitches += malware_delta

        # --- Phase 3: Operations & Face 6 Income/Action Hooks ---
        if not self.state.game_over:
            # Pre-Phase 3 Income inspection for Acoustic, Cipher, Spook Purple Star activations
            for p in self.state.players:
                if p.is_patient_zero:
                    continue
                has_p_star = any(
                    (d.effective_face or d.current_face)
                    and (d.effective_face or d.current_face).is_star
                    and (d.effective_face or d.current_face).star_code == "PURPLE_STAR"
                    for d in p.in_production_dice
                )
                if has_p_star and p.archetype is not None:
                    if p.archetype.code == ArchetypeCode.ACOUSTIC:
                        self.protocol_activations[ArchetypeCode.ACOUSTIC.value] += 1
                    elif p.archetype.code == ArchetypeCode.CIPHER:
                        # Cipher Phase 3A +$2 income activation
                        self.protocol_activations[ArchetypeCode.CIPHER.value] += 1
                    elif p.archetype.code == ArchetypeCode.SPOOK:
                        # Spook Phase 3A +$2 base income activation
                        self.protocol_activations[ArchetypeCode.SPOOK.value] += 1

            orig_phreaker_diag = phase3_ops.resolve_phreaker_jumper_diagnostics
            orig_spook_burn = phase3_ops.resolve_spook_burn_notice

            phreaker_triggers = [0]
            spook_burns = [0]

            def hooked_phreaker_diag(*args: Any, **kwargs: Any) -> Any:
                res = orig_phreaker_diag(*args, **kwargs)
                if res is not None:
                    phreaker_triggers[0] += 1
                return res

            def hooked_spook_burn(*args: Any, **kwargs: Any) -> bool:
                res = orig_spook_burn(*args, **kwargs)
                if res:
                    spook_burns[0] += 1
                return res

            phase3_ops.resolve_phreaker_jumper_diagnostics = hooked_phreaker_diag
            phase3_ops.resolve_spook_burn_notice = hooked_spook_burn

            try:
                self._execute_phase_3()
            finally:
                phase3_ops.resolve_phreaker_jumper_diagnostics = orig_phreaker_diag
                phase3_ops.resolve_spook_burn_notice = orig_spook_burn

            self.protocol_activations[ArchetypeCode.PHREAKER.value] += phreaker_triggers[0]
            self.spook_dice_burned += spook_burns[0]

            if self.state.is_final_round:
                self.state.game_over = True
            else:
                self.state.current_round += 1
                if self.state.current_round > self.state.config.max_rounds:
                    self.state.game_over = True
                    from sim.config import EndGameReason
                    self.state.end_reason = EndGameReason.ROUND_LIMIT

        return telemetry


def run_sweep(num_games: int = 1000, base_seed: int = 42) -> Dict[int, Dict[str, Any]]:
    print(f"================ V0.24.0 BASELINE TELEMETRY SWEEP (N={num_games} per pod, base_seed={base_seed}) ================\n")

    summary_tables: Dict[int, Dict[str, Any]] = {}
    archetype_codes = [c.value for c in ArchetypeCode]

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
        debug_unlocks_total = 0  # In v0.24.0, strictly 0.00
        fast_patches_per_game = []
        fast_patches_per_player = []
        player_ending_patches = []

        # End Game Assets
        player_ending_secrets = []
        player_ending_money = []
        player_unfulfilled_destructions = []

        # Phase 31 Specialist & Personal Reserve metrics
        purple_bought_per_game = []
        purple_bought_per_player = []
        players_buying_purple = 0
        total_player_count = 0
        purple_purchase_counts = {0: 0, 1: 0, 2: 0}

        purple_stars_in_prod_per_game = []
        total_protocol_activations = defaultdict(int)
        total_spook_dice_burned = 0

        # Archetype telemetry
        archetype_matches = defaultdict(int)
        archetype_wins = defaultdict(int)
        archetype_survivals = defaultdict(int)
        archetype_secrets = defaultdict(list)
        archetype_money = defaultdict(list)

        for match_idx in range(num_games):
            seed = base_seed + match_idx
            cfg = GameConfig.legacy_v035(num_players=p_count)
            all_bots = [
                AdaptiveBalancedBot(0),
                SecOpsTurtleBot(1),
                VentureGreedBot(2),
                AccelerationistBot(3),
            ]
            bots = all_bots[:p_count]

            rng = random.Random(seed)
            variant_cards, version_deck = get_random_setup(rng)

            eng = TelemetrySweepEngineV240(
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
            game_purple_bought = 0

            for p in eng.state.players:
                player_ending_secrets.append(p.secrets)
                player_ending_money.append(p.money)
                player_ending_patches.append(p.patches)
                player_unfulfilled_destructions.append(p.unfulfilled_destructions)
                game_fast_patches += getattr(p, "total_fast_patches", 0)
                fast_patches_per_player.append(getattr(p, "total_fast_patches", 0))

                # Personal Reserve procurement tracking
                bought = 2 - p.personal_purple_reserve
                game_purple_bought += bought
                purple_bought_per_player.append(bought)
                total_player_count += 1
                if bought > 0:
                    players_buying_purple += 1
                purple_purchase_counts[bought] = purple_purchase_counts.get(bought, 0) + 1

            fast_patches_per_game.append(game_fast_patches)
            purple_bought_per_game.append(game_purple_bought)
            purple_stars_in_prod_per_game.append(eng.match_purple_stars_in_production)

            for code, act_count in eng.protocol_activations.items():
                total_protocol_activations[code] += act_count
            total_spook_dice_burned += eng.spook_dice_burned

            # Archetype ranking telemetry
            for r in res.rankings:
                arch_code = r.get("archetype_code", "NONE")
                if arch_code in archetype_codes:
                    archetype_matches[arch_code] += 1
                    if r.get("rank") == 1:
                        archetype_wins[arch_code] += 1
                    if not r.get("is_patient_zero", False):
                        archetype_survivals[arch_code] += 1
                    archetype_secrets[arch_code].append(r.get("secrets", 0))
                    archetype_money[arch_code].append(r.get("money", 0))

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

        # Specialist & Personal Reserve metrics calculations
        mean_purple_game = statistics.mean(purple_bought_per_game)
        mean_purple_player = statistics.mean(purple_bought_per_player)
        purple_buyer_pct = (players_buying_purple / total_player_count) * 100.0 if total_player_count else 0.0
        reserve_utilization_pct = (mean_purple_player / 2.0) * 100.0

        mean_purple_stars_game = statistics.mean(purple_stars_in_prod_per_game)
        purple_stars_per_player_rd = sum(purple_stars_in_prod_per_game) / total_player_rounds if total_player_rounds else 0.0

        # Archetype metrics compilation
        archetype_stats: Dict[str, Dict[str, float]] = {}
        for code in archetype_codes:
            m_count = archetype_matches[code]
            w_count = archetype_wins[code]
            s_count = archetype_survivals[code]
            win_rate = (w_count / m_count * 100.0) if m_count > 0 else 0.0
            surv_rate = (s_count / m_count * 100.0) if m_count > 0 else 0.0
            avg_sec = statistics.mean(archetype_secrets[code]) if archetype_secrets[code] else 0.0
            avg_mon = statistics.mean(archetype_money[code]) if archetype_money[code] else 0.0
            proto_acts = total_protocol_activations[code]
            proto_per_game = proto_acts / num_games

            archetype_stats[code] = {
                "matches": m_count,
                "wins": w_count,
                "win_rate": win_rate,
                "survivals": s_count,
                "survival_rate": surv_rate,
                "avg_secrets": avg_sec,
                "avg_money": avg_mon,
                "protocol_activations": proto_acts,
                "protocol_per_game": proto_per_game,
            }

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
            # Phase 31 specific
            "mean_purple_game": mean_purple_game,
            "mean_purple_player": mean_purple_player,
            "purple_buyer_pct": purple_buyer_pct,
            "reserve_utilization_pct": reserve_utilization_pct,
            "purple_purchase_counts": dict(purple_purchase_counts),
            "mean_purple_stars_game": mean_purple_stars_game,
            "purple_stars_per_player_rd": purple_stars_per_player_rd,
            "total_protocol_activations": dict(total_protocol_activations),
            "total_spook_dice_burned": total_spook_dice_burned,
            "archetype_stats": archetype_stats,
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
        print(f"  Personal Reserve (Purple) Economy:")
        print(f"    Purple Bought / match:          {mean_purple_game:.2f} (Per Player: {mean_purple_player:.2f})")
        print(f"    Adoption Rate (>=1 Purple):     {purple_buyer_pct:.1f}% | Capacity Utilization: {reserve_utilization_pct:.1f}%")
        print(f"    Purchase Distribution:          0={purple_purchase_counts.get(0, 0)} ({purple_purchase_counts.get(0, 0)/total_player_count*100:.1f}%), 1={purple_purchase_counts.get(1, 0)} ({purple_purchase_counts.get(1, 0)/total_player_count*100:.1f}%), 2={purple_purchase_counts.get(2, 0)} ({purple_purchase_counts.get(2, 0)/total_player_count*100:.1f}%)")
        print(f"  Purple Star & Protocol Activity:")
        print(f"    Purple Stars in Prod / match:   {mean_purple_stars_game:.2f} ({purple_stars_per_player_rd:.2f} / player-rd)")
        print(f"    Face 6 Protocol Activations / match: {sum(total_protocol_activations.values()) / num_games:.2f}")
        for code in archetype_codes:
            st = archetype_stats[code]
            print(f"      - {code:<10}: {st['protocol_per_game']:.2f}/match (Total: {st['protocol_activations']}) | Win Rate: {st['win_rate']:.1f}% | Surv: {st['survival_rate']:.1f}%")
        if total_spook_dice_burned > 0:
            print(f"    Spook Dice Burned to Market:    {total_spook_dice_burned} ({total_spook_dice_burned/num_games:.2f}/match)")
        print()

    print("================ V0.24.0 OVERALL COMPARISON SUMMARY ================")
    print(f"{'Metric':<38} | {'2P Pod':<10} | {'3P Pod':<10} | {'4P Pod':<10}")
    print("-" * 76)
    print(f"{'Match Duration (Mean)':<38} | {summary_tables[2]['mean_rds']:<10.2f} | {summary_tables[3]['mean_rds']:<10.2f} | {summary_tables[4]['mean_rds']:<10.2f}")
    print(f"{'Match Duration (Median)':<38} | {summary_tables[2]['median_rds']:<10.1f} | {summary_tables[3]['median_rds']:<10.1f} | {summary_tables[4]['median_rds']:<10.1f}")
    print(f"{'v3.0 Reach Rate (%)':<38} | {summary_tables[2]['v3_reach']:<10.1f} | {summary_tables[3]['v3_reach']:<10.1f} | {summary_tables[4]['v3_reach']:<10.1f}")
    print(f"{'Singularity Rate (%)':<38} | {summary_tables[2]['singularity_pct']:<10.1f} | {summary_tables[3]['singularity_pct']:<10.1f} | {summary_tables[4]['singularity_pct']:<10.1f}")
    print(f"{'Total Wipeout Rate (%)':<38} | {summary_tables[2]['wipeout_pct']:<10.1f} | {summary_tables[3]['wipeout_pct']:<10.1f} | {summary_tables[4]['wipeout_pct']:<10.1f}")
    print(f"{'Avg Ready Pool / player-rd':<38} | {summary_tables[2]['mean_ready_pool']:<10.2f} | {summary_tables[3]['mean_ready_pool']:<10.2f} | {summary_tables[4]['mean_ready_pool']:<10.2f}")
    print(f"{'Avg Glitched Box / player-rd':<38} | {summary_tables[2]['mean_glitched_box']:<10.2f} | {summary_tables[3]['mean_glitched_box']:<10.2f} | {summary_tables[4]['mean_glitched_box']:<10.2f}")
    print(f"{'Avg Scanned Box / player-rd':<38} | {summary_tables[2]['mean_scanned_box']:<10.2f} | {summary_tables[3]['mean_scanned_box']:<10.2f} | {summary_tables[4]['mean_scanned_box']:<10.2f}")
    print(f"{'Fast-Patches / match':<38} | {summary_tables[2]['mean_fast_patches_game']:<10.2f} | {summary_tables[3]['mean_fast_patches_game']:<10.2f} | {summary_tables[4]['mean_fast_patches_game']:<10.2f}")
    print(f"{'Ending Patches (Mean)':<38} | {summary_tables[2]['mean_unspent_patches']:<10.2f} | {summary_tables[3]['mean_unspent_patches']:<10.2f} | {summary_tables[4]['mean_unspent_patches']:<10.2f}")
    print(f"{'Ending Secrets (Mean)':<38} | {summary_tables[2]['mean_secrets']:<10.2f} | {summary_tables[3]['mean_secrets']:<10.2f} | {summary_tables[4]['mean_secrets']:<10.2f}")
    print(f"{'Ending Money (Mean)':<38} | ${summary_tables[2]['mean_money']:<9.2f} | ${summary_tables[3]['mean_money']:<9.2f} | ${summary_tables[4]['mean_money']:<9.2f}")
    print(f"{'Purple Bought / match':<38} | {summary_tables[2]['mean_purple_game']:<10.2f} | {summary_tables[3]['mean_purple_game']:<10.2f} | {summary_tables[4]['mean_purple_game']:<10.2f}")
    print(f"{'Purple Bought / player':<38} | {summary_tables[2]['mean_purple_player']:<10.2f} | {summary_tables[3]['mean_purple_player']:<10.2f} | {summary_tables[4]['mean_purple_player']:<10.2f}")
    print(f"{'Purple Adoption Rate (>=1)':<38} | {summary_tables[2]['purple_buyer_pct']:<9.1f}% | {summary_tables[3]['purple_buyer_pct']:<9.1f}% | {summary_tables[4]['purple_buyer_pct']:<9.1f}%")
    print(f"{'Reserve Utilization Rate':<38} | {summary_tables[2]['reserve_utilization_pct']:<9.1f}% | {summary_tables[3]['reserve_utilization_pct']:<9.1f}% | {summary_tables[4]['reserve_utilization_pct']:<9.1f}%")
    print(f"{'Purple Stars in Prod / match':<38} | {summary_tables[2]['mean_purple_stars_game']:<10.2f} | {summary_tables[3]['mean_purple_stars_game']:<10.2f} | {summary_tables[4]['mean_purple_stars_game']:<10.2f}")
    print(f"{'Face 6 Protocols / match':<38} | {sum(summary_tables[2]['total_protocol_activations'].values())/num_games:<10.2f} | {sum(summary_tables[3]['total_protocol_activations'].values())/num_games:<10.2f} | {sum(summary_tables[4]['total_protocol_activations'].values())/num_games:<10.2f}")
    print("-" * 76)

    print("\n================ ARCHETYPE WIN RATES & CORRIDOR VERIFICATION ================")
    print(f"{'Archetype':<12} | {'2P Win% (Target 50%)':<22} | {'3P Win% (Target 33.3%)':<24} | {'4P Win% (Corridor 20-30%)':<26}")
    print("-" * 92)
    for code in archetype_codes:
        w2 = summary_tables[2]['archetype_stats'][code]['win_rate']
        w3 = summary_tables[3]['archetype_stats'][code]['win_rate']
        w4 = summary_tables[4]['archetype_stats'][code]['win_rate']
        in_corridor_4p = "PASS" if 20.0 <= w4 <= 30.0 else "FLAG"
        print(f"{code:<12} | {w2:<22.1f}% | {w3:<24.1f}% | {w4:<6.1f}% [{in_corridor_4p}]")

    print("\n================ ARCHETYPE SURVIVAL RATES ================")
    print(f"{'Archetype':<12} | {'2P Survival%':<14} | {'3P Survival%':<14} | {'4P Survival%':<14}")
    print("-" * 60)
    for code in archetype_codes:
        s2 = summary_tables[2]['archetype_stats'][code]['survival_rate']
        s3 = summary_tables[3]['archetype_stats'][code]['survival_rate']
        s4 = summary_tables[4]['archetype_stats'][code]['survival_rate']
        print(f"{code:<12} | {s2:<13.1f}% | {s3:<13.1f}% | {s4:<13.1f}%")

    return summary_tables


if __name__ == "__main__":
    run_sweep(num_games=1000, base_seed=42)
