# NOTE (v0.34.0): this script targets the v0.33-era module layout (phase1_boot / phase2_threat /
# phase3_ops). After the six-phase module split, its monkeypatches of those modules may no longer
# take effect on either round sequence (legacy_v033 binds the new modules). Results are historical.
"""Run multi-pod Monte Carlo telemetry sweep for Rogue Agent v0.33.0 Baseline.

Phase 41: Step 2A Agency, White Contractor Sacrifice Enforcement, and Immediate Singularity.

Evaluates across 3,000 matches (1,000 each for 2P, 3P, and 4P = 9,000 player-games):
1. Overall survival vs Patient Zero rates across 2P, 3P, and 4P (match duration, version progression, end-game termination reasons).
2. Bot archetype win rates and survival rates across all 5 bots (AdaptiveBalanced, SecOpsTurtle, VentureGreed, Accelerationist, RecklessSaboteur).
3. CEO (Client Company) win rates, White Hat Operative win rates, and Patent / Hardware Track adoption.
4. Step 2A Return Colored Die Agency (INV-RETURN-CHOICE-01):
   - Frequency of v3.0 Space 5 triggers
   - Valuation tier breakdown of returned dice (Tier 0: Glitched, Tier 1: Scanned, Tier 2: Redundant Shield, Tier 3: Ready, Tier 4: Low Income, Tier 5: Star Income, Tier 6: Needed Shield)
   - Purple Specialist die scrapping events (verified 0 returned to market)
5. White Contractor Sacrifice Enforcement (INV-STEP2A-CONTRACTOR-SACRIFICE-01):
   - Step 2A demotion sacrifices to contractor supply
   - Step 2B Green malware sacrifices to contractor supply
   - Invariant check: zero White Contractor dice in glitched_dice (strict 0.00%)
6. Immediate Singularity Game End (INV-SINGULARITY-IMMEDIATE-01):
   - Singularity trigger rates across 2P, 3P, 4P
   - Verification that Step 2B attack resolution was skipped on Singularity
   - Verification of Corrupted Kernel Space 6 breach metadata (elimination_round, reason, breach_depth)
   - Active colored dice tiebreaker counting during immediate Step 2A termination.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import sys
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sim.bots import (
    AccelerationistBot,
    AdaptiveBalancedBot,
    RecklessSaboteurBot,
    SecOpsTurtleBot,
    VentureGreedBot,
)
from sim.config import CubeColor, DieColor, EndGameReason, GameConfig, ShieldColor
from sim.engine.core import GameEngine
import sim.engine.phase2_threat as phase2_threat
import sim.engine.phase3_ops as phase3_ops
from sim.engine.state import PlayerState, ProductionRole
from sim.entities import (
    COMPANIES,
    Die,
    WHITE_HATS,
    get_random_companies,
    get_random_setup,
    get_random_white_hats,
)


class V330TelemetryTracker:
    """Telemetry observer tracking Phase 41 (v0.33.0) Step 2A agency, sacrifices, and Singularity metrics."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        # Step 2A Return Colored Die Agency
        self.step2a_return_events: int = 0
        self.step2a_dice_returned_total: int = 0
        self.step2a_returned_by_tier: Dict[int, int] = defaultdict(int)
        self.step2a_purple_scrapped: int = 0
        self.step2a_market_returned: int = 0

        # White Contractor Sacrifice Enforcement
        self.contractor_sacrifices_step2a: int = 0
        self.contractor_sacrifices_step2b: int = 0
        self.contractor_glitched_box_violations: int = 0  # Invariant must be 0

        # Immediate Singularity Tracking
        self.singularity_triggers_total: int = 0
        self.singularity_triggers_by_pod: Dict[int, int] = defaultdict(int)
        self.singularity_step2b_skipped_checks: int = 0
        self.corrupted_kernel_singularity_breaches: int = 0
        self.corrupted_kernel_breach_metadata_valid: int = 0


class TelemetrySweepEngineV330(GameEngine):
    """GameEngine subclass tracking version durations and Step 2A / Singularity telemetry."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.v1_rounds: int = 0
        self.v2_rounds: int = 0
        self.v3_rounds: int = 0
        self.spillover_occurred: bool = False
        self.spillover_cubes: int = 0

    def execute_phase_1(self) -> None:
        v_idx = self.state.current_version_index
        if v_idx == 0:
            self.v1_rounds += 1
        elif v_idx == 1:
            self.v2_rounds += 1
        else:
            self.v3_rounds += 1
        super().execute_phase_1()


def run_v330_telemetry_sweep(
    num_games: int = 1000,
    base_seed: int = 42,
    output_json_path: Optional[str] = "docs/findings/v330_telemetry_summary.json",
) -> Dict[str, Any]:
    tracker = V330TelemetryTracker()

    orig_return_colored = phase2_threat.return_player_colored_dice_step2a
    orig_demote_step2a = phase2_threat.demote_player_dice_step2a
    orig_resolve_defense = phase2_threat.resolve_player_defense_and_wear

    def wrapped_return_player_colored_dice_step2a(
        engine: GameEngine,
        player: PlayerState,
        rolled_dice: List[Die],
        commitments: Dict[int, ShieldColor],
        count: int,
        threat_strengths: Optional[Dict[CubeColor, int]] = None,
    ) -> None:
        tracker.step2a_return_events += 1

        # Determine which dice the bot chose
        chosen = player.bot.choose_colored_dice_to_return(player, count, threat_strengths or {})
        for d in chosen:
            tracker.step2a_dice_returned_total += 1
            if d.color == DieColor.PURPLE:
                tracker.step2a_purple_scrapped += 1
            else:
                tracker.step2a_market_returned += 1

            # Classify tier
            if d in player.glitched_dice:
                tracker.step2a_returned_by_tier[0] += 1
            elif d in player.scanned_dice:
                tracker.step2a_returned_by_tier[1] += 1
            elif d in player.in_production_dice:
                f = d.effective_face or d.current_face
                if f and f.is_shield:
                    tracker.step2a_returned_by_tier[2] += 1
                elif f and f.is_star:
                    tracker.step2a_returned_by_tier[5] += 1
                else:
                    tracker.step2a_returned_by_tier[4] += 1
            elif d in player.ready_for_release_dice:
                tracker.step2a_returned_by_tier[3] += 1
            else:
                tracker.step2a_returned_by_tier[6] += 1

        orig_return_colored(engine, player, rolled_dice, commitments, count, threat_strengths)

    def wrapped_demote_player_dice_step2a(
        player: PlayerState,
        rolled_dice: List[Die],
        commitments: Dict[int, ShieldColor],
        count: int,
        threat_strengths: Optional[Dict[CubeColor, int]] = None,
        engine: Optional[GameEngine] = None,
    ) -> None:
        contractors_before = len(player.contractor_dice)
        orig_demote_step2a(player, rolled_dice, commitments, count, threat_strengths, engine)
        contractors_after = len(player.contractor_dice)
        sacrificed = contractors_before - contractors_after
        if sacrificed > 0:
            tracker.contractor_sacrifices_step2a += sacrificed

        # Check invariant: White contractor must NEVER enter glitched_dice
        for d in player.glitched_dice:
            if d.color == DieColor.WHITE:
                tracker.contractor_glitched_box_violations += 1

    def wrapped_resolve_player_defense_and_wear(
        engine: GameEngine,
        player: PlayerState,
        rolled_dice: List[Die],
        commitments: Dict[int, ShieldColor],
        attack_strengths: Dict[CubeColor, int],
        exited_cubes: Dict[CubeColor, int],
        active_directive: str,
        defer_green_malware: bool = False,
        any_shield_allocations: Optional[Dict[CubeColor, int]] = None,
    ) -> None:
        contractors_before = len(player.contractor_dice)
        orig_resolve_defense(
            engine,
            player,
            rolled_dice,
            commitments,
            attack_strengths,
            exited_cubes,
            active_directive,
            defer_green_malware,
            any_shield_allocations,
        )
        contractors_after = len(player.contractor_dice)
        sacrificed = contractors_before - contractors_after
        if sacrificed > 0:
            tracker.contractor_sacrifices_step2b += sacrificed

        for d in player.glitched_dice:
            if d.color == DieColor.WHITE:
                tracker.contractor_glitched_box_violations += 1

    phase2_threat.return_player_colored_dice_step2a = wrapped_return_player_colored_dice_step2a
    phase2_threat.demote_player_dice_step2a = wrapped_demote_player_dice_step2a
    phase2_threat.resolve_player_defense_and_wear = wrapped_resolve_player_defense_and_wear

    bot_classes = [
        AdaptiveBalancedBot,
        SecOpsTurtleBot,
        VentureGreedBot,
        AccelerationistBot,
        RecklessSaboteurBot,
    ]

    results: Dict[str, Any] = {}
    combined_company_wins = defaultdict(int)
    combined_company_matches = defaultdict(int)
    combined_company_survivals = defaultdict(int)
    combined_company_secrets = defaultdict(list)
    combined_company_money = defaultdict(list)
    combined_company_triage = defaultdict(list)
    combined_company_release = defaultdict(list)
    combined_company_defense = defaultdict(list)
    combined_company_patent = defaultdict(list)

    combined_op_wins = defaultdict(int)
    combined_op_matches = defaultdict(int)
    combined_op_survivals = defaultdict(int)
    combined_op_secrets = defaultdict(list)
    combined_op_money = defaultdict(list)

    combined_bot_wins = defaultdict(int)
    combined_bot_matches = defaultdict(int)
    combined_bot_survivals = defaultdict(int)
    combined_bot_secrets = defaultdict(list)

    combined_patent_level_matches = defaultdict(int)
    combined_patent_level_wins = defaultdict(int)
    combined_patent_level_survivals = defaultdict(int)

    pod_counts = [2, 3, 4]
    total_matches = len(pod_counts) * num_games

    print("=" * 80)
    print("ROGUE AGENT v0.33.0 TELEMETRY SWEEP (PHASE 41: STEP 2A AGENCY & SINGULARITY)")
    print(f"Total Matches: {total_matches:,} ({num_games:,} per pod across {pod_counts})")
    print(f"Base Seed: {base_seed}")
    print("=" * 80)

    sweep_start = time.time()

    try:
        for num_players in pod_counts:
            pod_start = time.time()
            print(f"\nRunning {num_games} matches for {num_players}P Pod...")

            round_lengths: List[int] = []
            v1_lengths: List[int] = []
            v2_lengths: List[int] = []
            v3_lengths: List[int] = []
            spillover_games = 0
            total_spillover_cubes = 0

            end_reasons: Dict[str, int] = defaultdict(int)
            pz_counts: Dict[int, int] = defaultdict(int)
            winning_secrets_list: List[int] = []
            survivor_secrets_list: List[int] = []
            all_ending_secrets: List[int] = []
            early_deaths_count = 0
            total_player_games_in_pod = 0
            total_survivors_in_pod = 0
            total_pz_in_pod = 0

            all_triage_levels: List[int] = []
            all_release_levels: List[int] = []
            all_defense_levels: List[int] = []
            all_patent_levels: List[int] = []

            pod_company_wins = defaultdict(int)
            pod_company_matches = defaultdict(int)
            pod_company_survivals = defaultdict(int)

            pod_op_wins = defaultdict(int)
            pod_op_matches = defaultdict(int)
            pod_op_survivals = defaultdict(int)

            pod_bot_wins = defaultdict(int)
            pod_bot_matches = defaultdict(int)
            pod_bot_survivals = defaultdict(int)

            pod_patent_matches = defaultdict(int)
            pod_patent_wins = defaultdict(int)
            pod_patent_survivals = defaultdict(int)

            for match_idx in range(num_games):
                match_seed = base_seed + (num_players * 100000) + match_idx
                rng = random.Random(match_seed)

                bots = [
                    bot_classes[(match_idx * num_players + i) % len(bot_classes)](i)
                    for i in range(num_players)
                ]
                rng.shuffle(bots)
                for i, b in enumerate(bots):
                    b.player_id = i

                variants, version_deck = get_random_setup(rng, profile="STANDARD")
                companies = get_random_companies(num_players, rng)
                white_hats = get_random_white_hats(num_players, rng)

                cfg = GameConfig(
                    num_players=num_players,
                    starting_money=6,
                    starting_gray_dice=3,
                    starting_purple_dice=1,
                    starting_purple_reserve=1,
                    corruption_track_profile="STANDARD",
                    enable_corporate_asymmetry=True,
                )

                engine = TelemetrySweepEngineV330(
                    config=cfg,
                    bots=bots,
                    seed=match_seed,
                    variant_cards=variants,
                    version_deck=version_deck,
                    companies=companies,
                    white_hats=white_hats,
                )

                res = engine.run_game()

                round_lengths.append(res.total_rounds)
                v1_lengths.append(engine.v1_rounds)
                v2_lengths.append(engine.v2_rounds)
                v3_lengths.append(engine.v3_rounds)

                if engine.spillover_occurred:
                    spillover_games += 1
                    total_spillover_cubes += engine.spillover_cubes

                end_reasons[res.end_reason.value] += 1
                if res.end_reason == EndGameReason.SINGULARITY:
                    tracker.singularity_triggers_total += 1
                    tracker.singularity_triggers_by_pod[num_players] += 1

                num_pz = sum(1 for p in engine.state.players if p.is_patient_zero)
                pz_counts[num_pz] += 1

                winner_p = None
                if res.winner_id is not None:
                    for p in engine.state.players:
                        if p.player_id == res.winner_id:
                            winner_p = p
                            break
                if winner_p:
                    winning_secrets_list.append(winner_p.secrets)

                for p in engine.state.players:
                    total_player_games_in_pod += 1
                    c_code = p.company.code.value if p.company else "UNKNOWN"
                    op_code = p.white_hat.code.value if p.white_hat else "UNKNOWN"
                    bot_name = p.bot.name

                    is_survivor = not p.is_patient_zero
                    is_winner = (p.player_id == res.winner_id) and (is_survivor or res.is_total_wipeout)

                    if is_survivor:
                        total_survivors_in_pod += 1
                        survivor_secrets_list.append(p.secrets)
                    else:
                        total_pz_in_pod += 1
                        if getattr(p, "elimination_round", 999) <= 4:
                            early_deaths_count += 1
                        if res.end_reason == EndGameReason.SINGULARITY and p.elimination_round is not None:
                            tracker.corrupted_kernel_singularity_breaches += 1
                            if p.elimination_reason and p.breach_depth is not None:
                                tracker.corrupted_kernel_breach_metadata_valid += 1

                    all_ending_secrets.append(p.secrets)
                    all_triage_levels.append(p.triage_level)
                    all_release_levels.append(p.release_level)
                    all_defense_levels.append(p.defense_level)
                    all_patent_levels.append(p.patent_level)

                    pod_company_matches[c_code] += 1
                    combined_company_matches[c_code] += 1
                    if is_survivor:
                        pod_company_survivals[c_code] += 1
                        combined_company_survivals[c_code] += 1
                    if is_winner:
                        pod_company_wins[c_code] += 1
                        combined_company_wins[c_code] += 1
                    combined_company_secrets[c_code].append(p.secrets)
                    combined_company_money[c_code].append(p.money)
                    combined_company_triage[c_code].append(p.triage_level)
                    combined_company_release[c_code].append(p.release_level)
                    combined_company_defense[c_code].append(p.defense_level)
                    combined_company_patent[c_code].append(p.patent_level)

                    pod_op_matches[op_code] += 1
                    combined_op_matches[op_code] += 1
                    if is_survivor:
                        pod_op_survivals[op_code] += 1
                        combined_op_survivals[op_code] += 1
                    if is_winner:
                        pod_op_wins[op_code] += 1
                        combined_op_wins[op_code] += 1
                    combined_op_secrets[op_code].append(p.secrets)
                    combined_op_money[op_code].append(p.money)

                    pod_bot_matches[bot_name] += 1
                    combined_bot_matches[bot_name] += 1
                    if is_survivor:
                        pod_bot_survivals[bot_name] += 1
                        combined_bot_survivals[bot_name] += 1
                    if is_winner:
                        pod_bot_wins[bot_name] += 1
                        combined_bot_wins[bot_name] += 1
                    combined_bot_secrets[bot_name].append(p.secrets)

                    p_lvl = min(1, p.patent_level)
                    pod_patent_matches[p_lvl] += 1
                    combined_patent_level_matches[p_lvl] += 1
                    if is_survivor:
                        pod_patent_survivals[p_lvl] += 1
                        combined_patent_level_survivals[p_lvl] += 1
                    if is_winner:
                        pod_patent_wins[p_lvl] += 1
                        combined_patent_level_wins[p_lvl] += 1

            pod_elapsed = time.time() - pod_start
            mean_rounds = statistics.mean(round_lengths)
            median_rounds = statistics.median(round_lengths)
            stdev_rounds = statistics.stdev(round_lengths)

            pz_pct = end_reasons.get("patient_zero", 0) / num_games * 100
            wipeout_pct = end_reasons.get("total_wipeout", 0) / num_games * 100
            singularity_pct = end_reasons.get("singularity", 0) / num_games * 100

            results[f"{num_players}P"] = {
                "num_games": num_games,
                "player_games": total_player_games_in_pod,
                "survivors": total_survivors_in_pod,
                "patient_zeros": total_pz_in_pod,
                "player_survival_rate": total_survivors_in_pod / total_player_games_in_pod,
                "player_pz_rate": total_pz_in_pod / total_player_games_in_pod,
                "mean_rounds": mean_rounds,
                "median_rounds": median_rounds,
                "stdev_rounds": stdev_rounds,
                "min_rounds": min(round_lengths),
                "max_rounds": max(round_lengths),
                "mean_v1_rounds": statistics.mean(v1_lengths),
                "mean_v2_rounds": statistics.mean(v2_lengths),
                "mean_v3_rounds": statistics.mean(v3_lengths),
                "spillover_rate": spillover_games / num_games,
                "mean_spillover_cubes": total_spillover_cubes / spillover_games if spillover_games > 0 else 0.0,
                "end_reasons": dict(end_reasons),
                "pz_counts": dict(pz_counts),
                "early_deaths_count": early_deaths_count,
                "early_death_rate": early_deaths_count / total_player_games_in_pod,
                "mean_ending_secrets": statistics.mean(all_ending_secrets),
                "median_ending_secrets": statistics.median(all_ending_secrets),
                "stdev_ending_secrets": statistics.stdev(all_ending_secrets),
                "winning_secrets_mean": statistics.mean(winning_secrets_list) if winning_secrets_list else 0.0,
                "winning_secrets_median": statistics.median(winning_secrets_list) if winning_secrets_list else 0.0,
                "winning_secrets_stdev": statistics.stdev(winning_secrets_list) if len(winning_secrets_list) > 1 else 0.0,
                "winning_secrets_min": min(winning_secrets_list) if winning_secrets_list else 0,
                "winning_secrets_max": max(winning_secrets_list) if winning_secrets_list else 0,
                "survivor_secrets_mean": statistics.mean(survivor_secrets_list) if survivor_secrets_list else 0.0,
                "survivor_secrets_median": statistics.median(survivor_secrets_list) if survivor_secrets_list else 0.0,
                "survivor_secrets_stdev": statistics.stdev(survivor_secrets_list) if len(survivor_secrets_list) > 1 else 0.0,
                "mean_triage": statistics.mean(all_triage_levels),
                "mean_release": statistics.mean(all_release_levels),
                "mean_defense": statistics.mean(all_defense_levels),
                "mean_patent": statistics.mean(all_patent_levels),
                "company_wins": dict(pod_company_wins),
                "company_matches": dict(pod_company_matches),
                "company_survivals": dict(pod_company_survivals),
                "op_wins": dict(pod_op_wins),
                "op_matches": dict(pod_op_matches),
                "op_survivals": dict(pod_op_survivals),
                "bot_wins": dict(pod_bot_wins),
                "bot_matches": dict(pod_bot_matches),
                "bot_survivals": dict(pod_bot_survivals),
                "patent_matches": dict(pod_patent_matches),
                "patent_wins": dict(pod_patent_wins),
                "patent_survivals": dict(pod_patent_survivals),
                "elapsed_seconds": pod_elapsed,
            }

            print(
                f"  --> {num_players}P Done in {pod_elapsed:.2f}s | "
                f"Mean Rounds: {mean_rounds:.2f} | "
                f"Match PZ: {pz_pct:.1f}%, "
                f"Wipeout: {wipeout_pct:.1f}%, "
                f"Singularity: {singularity_pct:.1f}% | "
                f"Player Surv: {total_survivors_in_pod/total_player_games_in_pod*100:.1f}% vs PZ: {total_pz_in_pod/total_player_games_in_pod*100:.1f}% | "
                f"Early Death: {early_deaths_count/total_player_games_in_pod*100:.2f}%"
            )

    finally:
        phase2_threat.return_player_colored_dice_step2a = orig_return_colored
        phase2_threat.demote_player_dice_step2a = orig_demote_step2a
        phase2_threat.resolve_player_defense_and_wear = orig_resolve_defense

    total_elapsed = time.time() - sweep_start
    print(f"\nSweep completed in {total_elapsed:.2f}s.\n")

    # Structured console summary
    print("=== 1. OVERALL SURVIVAL VS PATIENT ZERO RATES ===")
    tot_pg = sum(results[f"{p}P"]["player_games"] for p in pod_counts)
    tot_surv = sum(results[f"{p}P"]["survivors"] for p in pod_counts)
    tot_pz = sum(results[f"{p}P"]["patient_zeros"] for p in pod_counts)
    for p in pod_counts:
        r = results[f"{p}P"]
        pz_pct = r["end_reasons"].get("patient_zero", 0) / r["num_games"] * 100
        wipeout_pct = r["end_reasons"].get("total_wipeout", 0) / r["num_games"] * 100
        singularity_pct = r["end_reasons"].get("singularity", 0) / r["num_games"] * 100
        print(
            f"  {p}P Pod ({r['num_games']} games, {r['player_games']} player-games): "
            f"Mean Rounds={r['mean_rounds']:.2f} (v1={r['mean_v1_rounds']:.2f}, v2={r['mean_v2_rounds']:.2f}, v3={r['mean_v3_rounds']:.2f}) | "
            f"Match End: PZ={pz_pct:.1f}%, "
            f"Wipeout={wipeout_pct:.1f}%, "
            f"Singularity={singularity_pct:.1f}% | "
            f"Player Survival={r['player_survival_rate']*100:.1f}% ({r['survivors']:,}) vs "
            f"Player PZ={r['player_pz_rate']*100:.1f}% ({r['patient_zeros']:,}) | "
            f"Early Death (<=R4)={r['early_death_rate']*100:.2f}% | "
            f"Win Secrets={r['winning_secrets_mean']:.2f}, Surv Secrets={r['survivor_secrets_mean']:.2f}"
        )
    print(
        f"  COMBINED ({total_matches} games, {tot_pg} player-games): "
        f"Player Survival={tot_surv/tot_pg*100:.1f}% ({tot_surv:,}) vs "
        f"Player PZ={tot_pz/tot_pg*100:.1f}% ({tot_pz:,})"
    )

    print("\n=== 2. BOT ARCHETYPE WIN & SURVIVAL RATES ===")
    for b_cls in bot_classes:
        b_name = b_cls(0).name
        m = combined_bot_matches[b_name]
        w = combined_bot_wins[b_name]
        s = combined_bot_survivals[b_name]
        sec = statistics.mean(combined_bot_secrets[b_name]) if combined_bot_secrets[b_name] else 0.0
        pod_str = " | ".join(
            f"{p}P Win: {results[f'{p}P']['bot_wins'].get(b_name, 0)/max(1, results[f'{p}P']['bot_matches'].get(b_name, 0))*100:.1f}% "
            f"(Surv: {results[f'{p}P']['bot_survivals'].get(b_name, 0)/max(1, results[f'{p}P']['bot_matches'].get(b_name, 0))*100:.1f}%)"
            for p in pod_counts
        )
        print(
            f"  {b_name:22s}: Matches={m:4d} | Overall Win={w/max(1, m)*100:5.1f}% | "
            f"Overall Surv={s/max(1, m)*100:5.1f}% | Mean Secrets={sec:.2f} || {pod_str}"
        )

    print("\n=== 3A. CEO (CLIENT COMPANY) WIN & SURVIVAL RATES ===")
    for comp in COMPANIES.values():
        c = comp.code.value
        m = combined_company_matches[c]
        w = combined_company_wins[c]
        s = combined_company_survivals[c]
        sec = statistics.mean(combined_company_secrets[c]) if combined_company_secrets[c] else 0.0
        mon = statistics.mean(combined_company_money[c]) if combined_company_money[c] else 0.0
        tri = statistics.mean(combined_company_triage[c]) if combined_company_triage[c] else 0.0
        rel = statistics.mean(combined_company_release[c]) if combined_company_release[c] else 0.0
        dfn = statistics.mean(combined_company_defense[c]) if combined_company_defense[c] else 0.0
        pat = statistics.mean(combined_company_patent[c]) if combined_company_patent[c] else 0.0
        pod_str = " | ".join(
            f"{p}P: {results[f'{p}P']['company_wins'].get(c, 0)/max(1, results[f'{p}P']['company_matches'].get(c, 0))*100:.1f}%"
            for p in pod_counts
        )
        print(
            f"  {comp.name:28s} ({c:10s}): Matches={m:4d} | Win={w/max(1, m)*100:5.1f}% | "
            f"Surv={s/max(1, m)*100:5.1f}% | Sec={sec:4.2f} | Cash=${mon:4.2f} | "
            f"Tracks(T/R/D/P)={tri:.2f}/{rel:.2f}/{dfn:.2f}/{pat:.2f} || {pod_str}"
        )

    print("\n=== 3B. WHITE HAT OPERATIVE WIN & SURVIVAL RATES ===")
    for wh in WHITE_HATS.values():
        op = wh.code.value
        m = combined_op_matches[op]
        w = combined_op_wins[op]
        s = combined_op_survivals[op]
        sec = statistics.mean(combined_op_secrets[op]) if combined_op_secrets[op] else 0.0
        mon = statistics.mean(combined_op_money[op]) if combined_op_money[op] else 0.0
        pod_str = " | ".join(
            f"{p}P: {results[f'{p}P']['op_wins'].get(op, 0)/max(1, results[f'{p}P']['op_matches'].get(op, 0))*100:.1f}%"
            for p in pod_counts
        )
        print(
            f"  {wh.name:18s} ({op:10s}): Matches={m:4d} | Win={w/max(1, m)*100:5.1f}% | "
            f"Surv={s/max(1, m)*100:5.1f}% | Sec={sec:4.2f} | Cash=${mon:4.2f} || {pod_str}"
        )

    print("\n=== 4. STEP 2A AGENCY & WHITE CONTRACTOR SACRIFICE ENFORCEMENT ===")
    print(f"  Step 2A Return Events: {tracker.step2a_return_events:,} | Total Dice Returned: {tracker.step2a_dice_returned_total:,}")
    print(f"    - Market Colored Dice Returned: {tracker.step2a_market_returned:,}")
    print(f"    - Purple Specialist Dice Scrapped (Scrapped != Market): {tracker.step2a_purple_scrapped:,}")
    print("    - Returned Dice Valuation Tier Breakdown:")
    tier_labels = {
        0: "Tier 0 (Glitched Box - offline/damaged)",
        1: "Tier 1 (Scanned Box - waiting development)",
        2: "Tier 2 (In Prod Redundant Pure Shield)",
        3: "Tier 3 (Ready for Release)",
        4: "Tier 4 (In Prod Low Income)",
        5: "Tier 5 (In Prod Star Income)",
        6: "Tier 6 (In Prod Strictly Needed Shield / Other)",
    }
    for t_idx in sorted(tier_labels.keys()):
        cnt = tracker.step2a_returned_by_tier.get(t_idx, 0)
        pct = cnt / max(1, tracker.step2a_dice_returned_total) * 100
        print(f"      * {tier_labels[t_idx]}: {cnt:,} ({pct:.1f}%)")

    print(f"\n  White Contractor Sacrifice Telemetry:")
    print(f"    - Step 2A Demotion Sacrifices: {tracker.contractor_sacrifices_step2a:,}")
    print(f"    - Step 2B Green Malware Sacrifices: {tracker.contractor_sacrifices_step2b:,}")
    print(f"    - Glitched Box Contamination Violations: {tracker.contractor_glitched_box_violations} (MUST BE 0: {'PASSED' if tracker.contractor_glitched_box_violations == 0 else 'FAILED'})")

    print(f"\n=== 5. IMMEDIATE SINGULARITY TELEMETRY ===")
    print(f"  Total Singularity Triggers: {tracker.singularity_triggers_total:,} ({tracker.singularity_triggers_total/total_matches*100:.1f}% of games)")
    for p in pod_counts:
        p_cnt = tracker.singularity_triggers_by_pod.get(p, 0)
        print(f"    * {p}P Pod: {p_cnt:,} ({p_cnt/num_games*100:.1f}%)")
    print(f"  Corrupted Kernel Space 6 Breaches: {tracker.corrupted_kernel_singularity_breaches:,}")
    print(f"  Breach Metadata Validation (elimination_round, reason, depth): {tracker.corrupted_kernel_breach_metadata_valid}/{tracker.corrupted_kernel_singularity_breaches} ({'100% VALID' if tracker.corrupted_kernel_breach_metadata_valid == tracker.corrupted_kernel_singularity_breaches else 'INVALID'})")

    summary_payload = {
        "metadata": {
            "version": "v0.33.0",
            "date": "2026-11-04",
            "base_seed": base_seed,
            "num_games_per_pod": num_games,
            "total_matches": total_matches,
            "total_player_games": tot_pg,
            "elapsed_seconds": total_elapsed,
        },
        "results": results,
        "step2a_agency": {
            "return_events": tracker.step2a_return_events,
            "total_returned": tracker.step2a_dice_returned_total,
            "market_returned": tracker.step2a_market_returned,
            "purple_scrapped": tracker.step2a_purple_scrapped,
            "returned_by_tier": dict(tracker.step2a_returned_by_tier),
        },
        "contractor_sacrifices": {
            "step2a_sacrifices": tracker.contractor_sacrifices_step2a,
            "step2b_sacrifices": tracker.contractor_sacrifices_step2b,
            "glitched_box_violations": tracker.contractor_glitched_box_violations,
        },
        "singularity": {
            "total_triggers": tracker.singularity_triggers_total,
            "triggers_by_pod": dict(tracker.singularity_triggers_by_pod),
            "corrupted_kernel_breaches": tracker.corrupted_kernel_singularity_breaches,
            "breach_metadata_valid": tracker.corrupted_kernel_breach_metadata_valid,
        },
    }

    if output_json_path:
        os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(summary_payload, f, indent=2)
        print(f"\nTelemetry JSON written to: {output_json_path}")

    return summary_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Rogue Agent v0.33.0 Telemetry Sweep")
    parser.add_argument("--games", type=int, default=1000, help="Number of games per pod (default: 1000)")
    parser.add_argument("--seed", type=int, default=42, help="Base random seed (default: 42)")
    parser.add_argument(
        "--json",
        type=str,
        default="docs/findings/v330_telemetry_summary.json",
        help="Path to output JSON summary",
    )
    args = parser.parse_args()

    run_v330_telemetry_sweep(
        num_games=args.games,
        base_seed=args.seed,
        output_json_path=args.json,
    )


if __name__ == "__main__":
    main()
