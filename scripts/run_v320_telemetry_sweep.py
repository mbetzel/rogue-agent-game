"""Run multi-pod Monte Carlo telemetry sweep for Rogue Agent v0.32.0 Baseline.

Phase 39: Blue Variant Rebalance — B1 (Honeypot Telemetry) & B3 (Air-Gapped Backup).

Evaluates across 3,000 matches (1,000 each for 2P, 3P, and 4P = 9,000 player-games):
1. Overall survival vs Patient Zero rates across 2P, 3P, and 4P (plus match duration, version progression, and end-game termination reasons).
2. Bot archetype win rates and survival rates across all 5 bots (AdaptiveBalanced, SecOpsTurtle, VentureGreed, Accelerationist, RecklessSaboteur).
3. CEO (Client Company) win rates, White Hat Operative win rates, and Patent / Hardware Track win rates & adoption curves.
4. Specific Blue Variant Card performance across games where B1, B2, or B3 is the active Blue variant card:
   - Purchase rates (Blue dice bought per game, per player, buyer adoption %, share of market purchases)
   - Win shares (win rate of Blue buyers vs non-buyers, share of winners owning Blue dice, mean ending Secrets/Cash)
   - Variant Star trigger & pipeline triage metrics:
     * B1 (Honeypot Telemetry, $5): Star rolls, +$2 bounty triggers, total bounty cash, ransom leaks prevented
     * B2 (Deep R&D Vault, $6): Star rolls, shield vs income split, $4 -> +1 Secret conversions
     * B3 (Air-Gapped Backup, $4): Star rolls surviving to Phase 3A, Glitched -> Scanned triage rescues (Colored vs Gray), dual-output shield preservation events (INV-GLITCH-SHIELD-PRIO-01), and round-over-round pipeline flow.
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


class V320TelemetryTracker:
    """Non-intrusive telemetry observer wrapping canonical v0.32.0 engine functions."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        # Per-variant (B1, B2, B3) tracking
        self.blue_variant_games: Dict[str, int] = defaultdict(int)
        self.blue_variant_player_games: Dict[str, int] = defaultdict(int)
        self.blue_variant_buyer_player_games: Dict[str, int] = defaultdict(int)
        self.blue_variant_nonbuyer_player_games: Dict[str, int] = defaultdict(int)
        self.blue_variant_buyer_wins: Dict[str, int] = defaultdict(int)
        self.blue_variant_nonbuyer_wins: Dict[str, int] = defaultdict(int)
        self.blue_variant_buyer_survivals: Dict[str, int] = defaultdict(int)
        self.blue_variant_nonbuyer_survivals: Dict[str, int] = defaultdict(int)
        self.blue_variant_winner_owned_blue: Dict[str, int] = defaultdict(int)
        self.blue_variant_total_winners: Dict[str, int] = defaultdict(int)

        self.blue_variant_dice_bought: Dict[str, int] = defaultdict(int)
        self.blue_variant_total_market_dice_bought: Dict[str, int] = defaultdict(int)
        self.blue_variant_buyer_secrets: Dict[str, List[int]] = defaultdict(list)
        self.blue_variant_nonbuyer_secrets: Dict[str, List[int]] = defaultdict(list)
        self.blue_variant_buyer_money: Dict[str, List[int]] = defaultdict(list)

        # Pipeline & Triage metrics per Blue variant (B1, B2, B3)
        self.variant_player_rounds: Dict[str, int] = defaultdict(int)
        self.variant_glitched_snapshot_sum: Dict[str, int] = defaultdict(int)
        self.variant_scanned_snapshot_sum: Dict[str, int] = defaultdict(int)
        self.variant_ready_snapshot_sum: Dict[str, int] = defaultdict(int)
        self.variant_conveyor_triaged_dice: Dict[str, int] = defaultdict(int)
        self.variant_graduated_dice: Dict[str, int] = defaultdict(int)
        self.variant_hotfixed_dice: Dict[str, int] = defaultdict(int)

        # B1 specific metrics
        self.b1_star_rolled: int = 0
        self.b1_bounty_triggers: int = 0
        self.b1_bounty_cash_gained: int = 0
        self.b1_ransom_leaks_prevented: int = 0

        # B2 specific metrics
        self.b2_star_rolled: int = 0
        self.b2_committed_as_shield: int = 0
        self.b2_kept_for_income_option: int = 0
        self.b2_secret_purchases: int = 0

        # B3 specific metrics
        self.b3_star_rolled_phase2: int = 0
        self.b3_star_surviving_phase3a: int = 0
        self.b3_triage_triggers: int = 0
        self.b3_colored_dice_rescued: int = 0
        self.b3_gray_dice_rescued: int = 0
        self.b3_empty_glitched_noops: int = 0
        self.dual_output_shield_preserved_over_pure: int = 0
        self.b3_shield_preserved_over_pure: int = 0

        # Market purchases by color overall
        self.market_purchases_by_color: Dict[str, int] = defaultdict(int)
        self.variant_purchases_by_code: Dict[str, int] = defaultdict(int)


class TelemetrySweepEngineV320(GameEngine):
    """Subclass of GameEngine tracking version durations and spillover stats without altering mechanics."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.v1_rounds: int = 0
        self.v2_rounds: int = 0
        self.v3_rounds: int = 0
        self.spillover_occurred: bool = False
        self.spillover_cubes: int = 0

    def run_round(self):
        curr_ver = self.state.active_version.version_str if self.state.active_version else "v1.0"
        if curr_ver == "v1.0":
            self.v1_rounds += 1
        elif curr_ver == "v2.0":
            self.v2_rounds += 1
        elif curr_ver == "v3.0":
            self.v3_rounds += 1

        prev_overflow = self.state.overflow_black_cubes_on_next_track

        commitments = self._execute_phase_1()
        telem = self._execute_phase_2(commitments)

        if not self.state.game_over:
            self._execute_phase_3()
            if self.state.is_final_round:
                self.state.game_over = True
            else:
                self.state.current_round += 1
                if self.state.current_round > self.state.config.max_rounds:
                    self.state.game_over = True
                    self.state.end_reason = EndGameReason.ROUND_LIMIT

        if self.state.overflow_black_cubes_on_next_track > 0 or prev_overflow > 0:
            self.spillover_occurred = True
            if self.state.overflow_black_cubes_on_next_track > self.spillover_cubes:
                self.spillover_cubes = self.state.overflow_black_cubes_on_next_track

        return telem


def run_v320_telemetry_sweep(
    num_games: int = 1000,
    base_seed: int = 42,
    pod_counts: Optional[List[int]] = None,
    output_report_path: Optional[str] = None,
    output_json_path: Optional[str] = None,
) -> Dict[str, Any]:
    if pod_counts is None:
        pod_counts = [2, 3, 4]

    tracker = V320TelemetryTracker()
    pod_trackers: Dict[int, V320TelemetryTracker] = {p: V320TelemetryTracker() for p in pod_counts}
    active_pod_num = [2]

    orig_resolve_defense = phase2_threat.resolve_player_defense_and_wear
    orig_collect_income = phase3_ops.collect_player_production_income
    orig_execute_phase_3 = phase3_ops.execute_phase_3

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
        pod = active_pod_num[0]
        pt = pod_trackers[pod]

        money_before = player.money
        prod_before = list(player.in_production_dice)

        # Count B1 / B2 / B3 stars present in rolled_dice
        b1_count = 0
        for idx, die in enumerate(rolled_dice):
            face = die.effective_face or die.current_face
            if face and face.is_star:
                if face.star_code == "B1":
                    b1_count += 1
                    tracker.b1_star_rolled += 1
                    pt.b1_star_rolled += 1
                elif face.star_code == "B2":
                    tracker.b2_star_rolled += 1
                    pt.b2_star_rolled += 1
                    if idx in commitments:
                        tracker.b2_committed_as_shield += 1
                        pt.b2_committed_as_shield += 1
                    else:
                        tracker.b2_kept_for_income_option += 1
                        pt.b2_kept_for_income_option += 1
                elif face.star_code == "B3":
                    tracker.b3_star_rolled_phase2 += 1
                    pt.b3_star_rolled_phase2 += 1

        # Call exact canonical engine function
        orig_resolve_defense(
            engine=engine,
            player=player,
            rolled_dice=rolled_dice,
            commitments=commitments,
            attack_strengths=attack_strengths,
            exited_cubes=exited_cubes,
            active_directive=active_directive,
            defer_green_malware=defer_green_malware,
            any_shield_allocations=any_shield_allocations,
        )

        bd = getattr(player, "last_defense_breakdown", {}) or {}
        unblocked_blue = bd.get("unblocked", {}).get("blue", 0)
        unblocked_red = bd.get("unblocked", {}).get("red", 0)
        unblocked_green = bd.get("unblocked", {}).get("green", 0)

        # Check B1 bounty trigger
        if b1_count > 0 and exited_cubes.get(CubeColor.BLUE, 0) >= 1 and unblocked_blue == 0:
            tracker.b1_bounty_triggers += b1_count
            tracker.b1_bounty_cash_gained += 2 * b1_count
            pt.b1_bounty_triggers += b1_count
            pt.b1_bounty_cash_gained += 2 * b1_count
            # Did B1 bounty prevent an unpaid ransom leak?
            # Without 2 * b1_count, would unblocked_red have exceeded money_before (plus any R2/R3 bonuses)?
            other_star_cash = 0
            for die in rolled_dice:
                face = die.effective_face or die.current_face
                if face and face.is_star:
                    if face.star_code == "R2" and unblocked_red == 0:
                        other_star_cash += 2
                    elif face.star_code == "R3" and exited_cubes.get(CubeColor.RED, 0) >= 3:
                        other_star_cash += 1
            cash_without_b1 = money_before + other_star_cash
            if unblocked_red > cash_without_b1 and unblocked_red <= cash_without_b1 + 2 * b1_count:
                tracker.b1_ransom_leaks_prevented += 1
                pt.b1_ransom_leaks_prevented += 1

        # Check if INV-GLITCH-SHIELD-PRIO-01 preserved a dual-output shield (B3, R1, G1, G2) over a pure shield
        if unblocked_green > 0 and not defer_green_malware:
            prod_after = set(d.die_id for d in player.in_production_dice)
            glitched_This_step = [d for d in prod_before if d.die_id not in prod_after]
            surviving_this_step = [d for d in prod_before if d.die_id in prod_after]

            def is_pure_shield(d: Die) -> bool:
                role = getattr(d, "production_role", None)
                if role not in (
                    ProductionRole.RED_SHIELD,
                    ProductionRole.BLUE_SHIELD,
                    ProductionRole.GREEN_SHIELD,
                    ProductionRole.ANY_SHIELD,
                ):
                    return False
                f = d.effective_face or d.current_face
                if f is not None and (
                    f.money > 0
                    or f.patches > 0
                    or f.secrets > 0
                    or getattr(f, "star_code", None) in ("B3", "R1", "G1", "G2")
                ):
                    return False
                return True

            def is_dual_shield(d: Die) -> bool:
                role = getattr(d, "production_role", None)
                if role not in (
                    ProductionRole.RED_SHIELD,
                    ProductionRole.BLUE_SHIELD,
                    ProductionRole.GREEN_SHIELD,
                    ProductionRole.ANY_SHIELD,
                ):
                    return False
                f = d.effective_face or d.current_face
                return bool(
                    f is not None
                    and (
                        f.money > 0
                        or f.patches > 0
                        or f.secrets > 0
                        or getattr(f, "star_code", None) in ("B3", "R1", "G1", "G2")
                    )
                )

            if any(is_pure_shield(d) for d in glitched_This_step) and any(is_dual_shield(d) for d in surviving_this_step):
                tracker.dual_output_shield_preserved_over_pure += 1
                pt.dual_output_shield_preserved_over_pure += 1
                if any(
                    is_dual_shield(d) and getattr(d.effective_face or d.current_face, "star_code", None) == "B3"
                    for d in surviving_this_step
                ):
                    tracker.b3_shield_preserved_over_pure += 1
                    pt.b3_shield_preserved_over_pure += 1

    def wrapped_collect_player_production_income(engine: GameEngine, player: PlayerState, plan: Any = None) -> None:
        pod = active_pod_num[0]
        pt = pod_trackers[pod]

        # Inspect B3 dice in in_production_dice before income collection
        b3_in_prod = [
            d for d in player.in_production_dice
            if (d.effective_face or d.current_face)
            and not (d.effective_face or d.current_face).is_glitch
            and getattr(d.effective_face or d.current_face, "star_code", None) == "B3"
        ]
        glitched_before = list(player.glitched_dice)

        if b3_in_prod:
            tracker.b3_star_surviving_phase3a += len(b3_in_prod)
            pt.b3_star_surviving_phase3a += len(b3_in_prod)

        orig_collect_income(engine, player, plan)

        if b3_in_prod:
            glitched_after_ids = {d.die_id for d in player.glitched_dice}
            rescued = [d for d in glitched_before if d.die_id not in glitched_after_ids]
            rescued_count = len(rescued)
            tracker.b3_triage_triggers += rescued_count
            pt.b3_triage_triggers += rescued_count
            for d in rescued:
                if d.color == DieColor.GRAY:
                    tracker.b3_gray_dice_rescued += 1
                    pt.b3_gray_dice_rescued += 1
                else:
                    tracker.b3_colored_dice_rescued += 1
                    pt.b3_colored_dice_rescued += 1
            if len(b3_in_prod) > rescued_count:
                noops = len(b3_in_prod) - rescued_count
                tracker.b3_empty_glitched_noops += noops
                pt.b3_empty_glitched_noops += noops

    def wrapped_execute_phase_3(engine: GameEngine) -> None:
        pod = active_pod_num[0]
        pt = pod_trackers[pod]

        blue_var = engine.state.variant_cards.get(DieColor.BLUE)
        b_code = blue_var.code if blue_var else "NONE"

        # Snapshot pre-Phase 3 dice counts & B2 availability
        b2_avail_before = {p.player_id: (p.b2_available, p.secrets, p.money) for p in engine.state.players}
        colored_counts_before = {
            p.player_id: Counter_by_color(p) for p in engine.state.players
        }

        orig_execute_phase_3(engine)

        # Check B2 secret purchases & market purchases during Phase 3
        for p in engine.state.players:
            was_b2_avail, sec_before, _ = b2_avail_before[p.player_id]
            if was_b2_avail and not p.b2_available and p.secrets > sec_before:
                tracker.b2_secret_purchases += 1
                pt.b2_secret_purchases += 1

            after_counts = Counter_by_color(p)
            before_counts = colored_counts_before[p.player_id]
            for c_color, cnt_after in after_counts.items():
                diff = cnt_after - before_counts.get(c_color, 0)
                if diff > 0:
                    tracker.market_purchases_by_color[c_color.value] += diff
                    pt.market_purchases_by_color[c_color.value] += diff
                    tracker.blue_variant_total_market_dice_bought[b_code] += diff
                    pt.blue_variant_total_market_dice_bought[b_code] += diff
                    if c_color == DieColor.BLUE:
                        tracker.blue_variant_dice_bought[b_code] += diff
                        pt.blue_variant_dice_bought[b_code] += diff
                    v_card = engine.state.variant_cards.get(c_color)
                    if v_card:
                        tracker.variant_purchases_by_code[v_card.code] += diff
                        pt.variant_purchases_by_code[v_card.code] += diff

            if not p.is_patient_zero:
                tracker.variant_player_rounds[b_code] += 1
                tracker.variant_glitched_snapshot_sum[b_code] += len(p.glitched_dice)
                tracker.variant_scanned_snapshot_sum[b_code] += len(p.scanned_dice)
                tracker.variant_ready_snapshot_sum[b_code] += len(p.ready_for_release_dice)

                pt.variant_player_rounds[b_code] += 1
                pt.variant_glitched_snapshot_sum[b_code] += len(p.glitched_dice)
                pt.variant_scanned_snapshot_sum[b_code] += len(p.scanned_dice)
                pt.variant_ready_snapshot_sum[b_code] += len(p.ready_for_release_dice)

    def Counter_by_color(p: PlayerState) -> Dict[DieColor, int]:
        counts: Dict[DieColor, int] = defaultdict(int)
        for d in p.all_Permanent_dice if hasattr(p, "all_Permanent_dice") else (
            list(p.ready_for_release_dice)
            + list(p.in_production_dice)
            + list(p.glitched_dice)
            + list(p.scanned_dice)
        ):
            if d.color not in (DieColor.GRAY, DieColor.WHITE):
                counts[d.color] += 1
        return counts

    phase2_threat.resolve_player_defense_and_wear = wrapped_resolve_player_defense_and_wear
    phase3_ops.collect_player_production_income = wrapped_collect_player_production_income
    phase3_ops.execute_phase_3 = wrapped_execute_phase_3

    # All 5 canonical bot classes!
    bot_classes = [
        AdaptiveBalancedBot,
        SecOpsTurtleBot,
        VentureGreedBot,
        AccelerationistBot,
        RecklessSaboteurBot,
    ]

    results: Dict[str, Any] = {}

    # Cross-pod aggregations
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

    # Patent level win rates & survival rates
    combined_patent_level_matches = defaultdict(int)
    combined_patent_level_wins = defaultdict(int)
    combined_patent_level_survivals = defaultdict(int)
    combined_patent_level_secrets = defaultdict(list)

    # Track level win rates
    combined_track_level_wins: Dict[str, Dict[int, int]] = {
        "triage": defaultdict(int),
        "release": defaultdict(int),
        "defense": defaultdict(int),
        "patent": defaultdict(int),
    }
    combined_track_level_matches: Dict[str, Dict[int, int]] = {
        "triage": defaultdict(int),
        "release": defaultdict(int),
        "defense": defaultdict(int),
        "patent": defaultdict(int),
    }

    # All variant card active game stats (R1-R3, B1-B3, G1-G3, Y1-Y3)
    variant_active_games: Dict[str, int] = defaultdict(int)
    variant_active_player_games: Dict[str, int] = defaultdict(int)
    variant_buyer_player_games: Dict[str, int] = defaultdict(int)
    variant_buyer_wins: Dict[str, int] = defaultdict(int)
    variant_buyer_survivals: Dict[str, int] = defaultdict(int)

    total_matches = num_games * len(pod_counts)
    print("\n================================================================================")
    print("ROGUE AGENT v0.32.0 TELEMETRY SWEEP (PHASE 39: BLUE VARIANT REBALANCE B1 & B3)")
    print(f"Total Matches: {total_matches:,} ({num_games:,} per pod across {pod_counts})")
    print(f"Base Seed: {base_seed}")
    print("================================================================================\n")

    sweep_start = time.time()

    try:
        for num_players in pod_counts:
            active_pod_num[0] = num_players
            pod_start = time.time()
            print(f"Running {num_games} matches for {num_players}P Pod...")

            round_lengths: List[int] = []
            v1_lengths: List[int] = []
            v2_lengths: List[int] = []
            v3_lengths: List[int] = []
            spillover_games = 0
            total_spillover_cubes = 0

            end_reasons: Dict[str, int] = defaultdict(int)
            pz_counts: Dict[int, int] = defaultdict(int)

            all_ending_secrets: List[int] = []
            winning_secrets_list: List[int] = []
            survivor_secrets_list: List[int] = []
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

            pt = pod_trackers[num_players]

            for match_idx in range(num_games):
                match_seed = base_seed + (num_players * 100000) + match_idx
                rng = random.Random(match_seed)

                # Rotate across all 5 bot archetypes uniformly
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

                engine = TelemetrySweepEngineV320(
                    config=cfg,
                    bots=bots,
                    seed=match_seed,
                    variant_cards=variants,
                    version_deck=version_deck,
                    companies=companies,
                    white_hats=white_hats,
                )

                blue_var = variants.get(DieColor.BLUE)
                b_code = blue_var.code if blue_var else "NONE"
                tracker.blue_variant_games[b_code] += 1
                pt.blue_variant_games[b_code] += 1

                for c_col, v_card in variants.items():
                    if c_col in (DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW):
                        variant_active_games[v_card.code] += 1
                        variant_active_player_games[v_card.code] += num_players

                res = engine.run_game()

                round_lengths.append(res.total_rounds)
                v1_lengths.append(engine.v1_rounds)
                v2_lengths.append(engine.v2_rounds)
                v3_lengths.append(engine.v3_rounds)

                if engine.spillover_occurred:
                    spillover_games += 1
                    total_spillover_cubes += engine.spillover_cubes

                end_reasons[res.end_reason.value] += 1
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

                    all_ending_secrets.append(p.secrets)
                    all_triage_levels.append(p.triage_level)
                    all_release_levels.append(p.release_level)
                    all_defense_levels.append(p.defense_level)
                    all_patent_levels.append(p.patent_level)

                    # Company
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

                    # Operative
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

                    # Bot
                    pod_bot_matches[bot_name] += 1
                    combined_bot_matches[bot_name] += 1
                    combined_bot_secrets[bot_name].append(p.secrets)
                    if is_survivor:
                        pod_bot_survivals[bot_name] += 1
                        combined_bot_survivals[bot_name] += 1
                    if is_winner:
                        pod_bot_wins[bot_name] += 1
                        combined_bot_wins[bot_name] += 1

                    # Patent & Track levels
                    pat_lvl = p.patent_level
                    pod_patent_matches[pat_lvl] += 1
                    combined_patent_level_matches[pat_lvl] += 1
                    combined_patent_level_secrets[pat_lvl].append(p.secrets)
                    if is_survivor:
                        pod_patent_survivals[pat_lvl] += 1
                        combined_patent_level_survivals[pat_lvl] += 1
                    if is_winner:
                        pod_patent_wins[pat_lvl] += 1
                        combined_patent_level_wins[pat_lvl] += 1

                    combined_track_level_matches["triage"][p.triage_level] += 1
                    combined_track_level_matches["release"][p.release_level] += 1
                    combined_track_level_matches["defense"][p.defense_level] += 1
                    combined_track_level_matches["patent"][p.patent_level] += 1
                    if is_winner:
                        combined_track_level_wins["triage"][p.triage_level] += 1
                        combined_track_level_wins["release"][p.release_level] += 1
                        combined_track_level_wins["defense"][p.defense_level] += 1
                        combined_track_level_wins["patent"][p.patent_level] += 1

                    # Blue Variant performance for this player
                    all_player_dice = (
                        list(p.ready_for_release_dice)
                        + list(p.in_production_dice)
                        + list(p.glitched_dice)
                        + list(p.scanned_dice)
                    )
                    owned_colors = {d.color for d in all_player_dice}
                    owns_blue = DieColor.BLUE in owned_colors

                    tracker.blue_variant_player_games[b_code] += 1
                    pt.blue_variant_player_games[b_code] += 1

                    if owns_blue:
                        tracker.blue_variant_buyer_player_games[b_code] += 1
                        pt.blue_variant_buyer_player_games[b_code] += 1
                        tracker.blue_variant_buyer_secrets[b_code].append(p.secrets)
                        pt.blue_variant_buyer_secrets[b_code].append(p.secrets)
                        tracker.blue_variant_buyer_money[b_code].append(p.money)
                        pt.blue_variant_buyer_money[b_code].append(p.money)
                        if is_survivor:
                            tracker.blue_variant_buyer_survivals[b_code] += 1
                            pt.blue_variant_buyer_survivals[b_code] += 1
                        if is_winner:
                            tracker.blue_variant_buyer_wins[b_code] += 1
                            pt.blue_variant_buyer_wins[b_code] += 1
                    else:
                        tracker.blue_variant_nonbuyer_player_games[b_code] += 1
                        pt.blue_variant_nonbuyer_player_games[b_code] += 1
                        tracker.blue_variant_nonbuyer_secrets[b_code].append(p.secrets)
                        pt.blue_variant_nonbuyer_secrets[b_code].append(p.secrets)
                        if is_survivor:
                            tracker.blue_variant_nonbuyer_survivals[b_code] += 1
                            pt.blue_variant_nonbuyer_survivals[b_code] += 1
                        if is_winner:
                            tracker.blue_variant_nonbuyer_wins[b_code] += 1
                            pt.blue_variant_nonbuyer_wins[b_code] += 1

                    if is_winner:
                        tracker.blue_variant_total_winners[b_code] += 1
                        pt.blue_variant_total_winners[b_code] += 1
                        if owns_blue:
                            tracker.blue_variant_winner_owned_blue[b_code] += 1
                            pt.blue_variant_winner_owned_blue[b_code] += 1

                    # Track all 12 market variants buyer win rates
                    for c_col in (DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW):
                        v_card = variants.get(c_col)
                        if v_card and c_col in owned_colors:
                            variant_buyer_player_games[v_card.code] += 1
                            if is_survivor:
                                variant_buyer_survivals[v_card.code] += 1
                            if is_winner:
                                variant_buyer_wins[v_card.code] += 1

            pod_elapsed = time.time() - pod_start
            mean_rounds = statistics.mean(round_lengths)
            median_rounds = statistics.median(round_lengths)
            stdev_rounds = statistics.stdev(round_lengths)

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
                "all_ending_secrets": all_ending_secrets,
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

            pz_matches = end_reasons.get("patient_zero", end_reasons.get("PATIENT_ZERO", 0))
            wipeout_matches = end_reasons.get("total_wipeout", end_reasons.get("TOTAL_WIPEOUT", 0))
            singularity_matches = end_reasons.get("singularity", end_reasons.get("SINGULARITY", 0))
            print(
                f"  --> {num_players}P Done in {pod_elapsed:.2f}s | "
                f"Mean Rounds: {mean_rounds:.2f} | "
                f"Match PZ: {pz_matches/num_games*100:.1f}%, "
                f"Wipeout: {wipeout_matches/num_games*100:.1f}%, "
                f"Singularity: {singularity_matches/num_games*100:.1f}% | "
                f"Player Surv: {total_survivors_in_pod/total_player_games_in_pod*100:.1f}% vs PZ: {total_pz_in_pod/total_player_games_in_pod*100:.1f}% | "
                f"Early Death: {early_deaths_count/total_player_games_in_pod*100:.2f}%"
            )

    finally:
        phase2_threat.resolve_player_defense_and_wear = orig_resolve_defense
        phase3_ops.collect_player_production_income = orig_collect_income
        phase3_ops.execute_phase_3 = orig_execute_phase_3

    total_elapsed = time.time() - sweep_start
    print(f"\nSweep completed in {total_elapsed:.2f}s.\n")

    # Print structured console summary for immediate verification
    print("=== 1. OVERALL SURVIVAL VS PATIENT ZERO RATES ===")
    tot_pg = sum(results[f"{p}P"]["player_games"] for p in pod_counts)
    tot_surv = sum(results[f"{p}P"]["survivors"] for p in pod_counts)
    tot_pz = sum(results[f"{p}P"]["patient_zeros"] for p in pod_counts)
    for p in pod_counts:
        r = results[f"{p}P"]
        pz_pct = r['end_reasons'].get('patient_zero', r['end_reasons'].get('PATIENT_ZERO', 0)) / r['num_games'] * 100
        wipeout_pct = r['end_reasons'].get('total_wipeout', r['end_reasons'].get('TOTAL_WIPEOUT', 0)) / r['num_games'] * 100
        singularity_pct = r['end_reasons'].get('singularity', r['end_reasons'].get('SINGULARITY', 0)) / r['num_games'] * 100
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
        pod_w = " | ".join(
            f"{p}P: {results[f'{p}P']['company_wins'].get(c, 0)/max(1, results[f'{p}P']['company_matches'].get(c, 0))*100:.1f}%"
            for p in pod_counts
        )
        print(
            f"  {comp.name:28s} ({c:10s}): Matches={m:4d} | Win={w/max(1, m)*100:5.1f}% | "
            f"Surv={s/max(1, m)*100:5.1f}% | Sec={sec:.2f} | Cash=${mon:.2f} | "
            f"Tracks(T/R/D/P)={tri:.2f}/{rel:.2f}/{dfn:.2f}/{pat:.2f} || {pod_w}"
        )

    print("\n=== 3B. WHITE HAT OPERATIVE WIN & SURVIVAL RATES ===")
    for op in WHITE_HATS.values():
        c = op.code.value
        m = combined_op_matches[c]
        w = combined_op_wins[c]
        s = combined_op_survivals[c]
        sec = statistics.mean(combined_op_secrets[c]) if combined_op_secrets[c] else 0.0
        mon = statistics.mean(combined_op_money[c]) if combined_op_money[c] else 0.0
        pod_w = " | ".join(
            f"{p}P: {results[f'{p}P']['op_wins'].get(c, 0)/max(1, results[f'{p}P']['op_matches'].get(c, 0))*100:.1f}%"
            for p in pod_counts
        )
        print(
            f"  {op.name:18s} ({c:10s}): Matches={m:4d} | Win={w/max(1, m)*100:5.1f}% | "
            f"Surv={s/max(1, m)*100:5.1f}% | Sec={sec:.2f} | Cash=${mon:.2f} || {pod_w}"
        )

    print("\n=== 3C. PATENT LEVEL WIN & SURVIVAL RATES ===")
    filers_m = sum(m for lvl, m in combined_patent_level_matches.items() if lvl >= 1)
    filers_w = sum(combined_patent_level_wins[lvl] for lvl in combined_patent_level_matches if lvl >= 1)
    filers_s = sum(combined_patent_level_survivals[lvl] for lvl in combined_patent_level_matches if lvl >= 1)
    nonfilers_m = combined_patent_level_matches.get(0, 0)
    nonfilers_w = combined_patent_level_wins.get(0, 0)
    nonfilers_s = combined_patent_level_survivals.get(0, 0)
    for lvl in sorted(combined_patent_level_matches.keys()):
        m = combined_patent_level_matches[lvl]
        w = combined_patent_level_wins[lvl]
        s = combined_patent_level_survivals[lvl]
        sec = statistics.mean(combined_patent_level_secrets[lvl]) if combined_patent_level_secrets[lvl] else 0.0
        print(
            f"  Patent Level {lvl}: Player-Games={m:4d} ({m/tot_pg*100:5.1f}%) | "
            f"Win Rate={w/max(1, m)*100:5.1f}% | Survival Rate={s/max(1, m)*100:5.1f}% | Mean Secrets={sec:.2f}"
        )
    print(
        f"  Patent Filers (>=1 Patent): {filers_m:4d} ({filers_m/tot_pg*100:5.1f}%) | "
        f"Win Rate={filers_w/max(1, filers_m)*100:5.1f}% | Surv={filers_s/max(1, filers_m)*100:5.1f}% "
        f"vs Non-Filers (0 Patents): Win Rate={nonfilers_w/max(1, nonfilers_m)*100:5.1f}% | Surv={nonfilers_s/max(1, nonfilers_m)*100:5.1f}%"
    )

    print("\n=== 4. BLUE VARIANT CARD PERFORMANCE (B1 vs B2 vs B3) ===")
    for b_code in ("B1", "B2", "B3"):
        g_cnt = tracker.blue_variant_games[b_code]
        pg_cnt = tracker.blue_variant_player_games[b_code]
        buy_pg = tracker.blue_variant_buyer_player_games[b_code]
        nonbuy_pg = tracker.blue_variant_nonbuyer_player_games[b_code]
        buy_w = tracker.blue_variant_buyer_wins[b_code]
        nonbuy_w = tracker.blue_variant_nonbuyer_wins[b_code]
        buy_s = tracker.blue_variant_buyer_survivals[b_code]
        nonbuy_s = tracker.blue_variant_nonbuyer_survivals[b_code]
        b_dice = tracker.blue_variant_dice_bought[b_code]
        tot_m_dice = tracker.blue_variant_total_market_dice_bought[b_code]
        win_owned_b = tracker.blue_variant_winner_owned_blue[b_code]
        tot_w = tracker.blue_variant_total_winners[b_code]
        buy_sec = statistics.mean(tracker.blue_variant_buyer_secrets[b_code]) if tracker.blue_variant_buyer_secrets[b_code] else 0.0
        nonbuy_sec = statistics.mean(tracker.blue_variant_nonbuyer_secrets[b_code]) if tracker.blue_variant_nonbuyer_secrets[b_code] else 0.0
        p_rounds = max(1, tracker.variant_player_rounds[b_code])
        mean_glitched = tracker.variant_glitched_snapshot_sum[b_code] / p_rounds
        mean_scanned = tracker.variant_scanned_snapshot_sum[b_code] / p_rounds
        mean_ready = tracker.variant_ready_snapshot_sum[b_code] / p_rounds

        print(
            f"  [{b_code}] Games={g_cnt:4d} | Player-Games={pg_cnt:4d} | "
            f"Blue Dice Bought={b_dice:4d} ({b_dice/max(1, g_cnt):.2f}/game, {b_dice/max(1, pg_cnt):.2f}/player, "
            f"{b_dice/max(1, tot_m_dice)*100:.1f}% of market buys) | "
            f"Buyer Adoption={buy_pg/max(1, pg_cnt)*100:.1f}% ({buy_pg}/{pg_cnt}) | "
            f"Buyer Win Rate={buy_w/max(1, buy_pg)*100:.1f}% (Surv: {buy_s/max(1, buy_pg)*100:.1f}%, Sec: {buy_sec:.2f}) vs "
            f"Non-Buyer Win Rate={nonbuy_w/max(1, nonbuy_pg)*100:.1f}% (Surv: {nonbuy_s/max(1, nonbuy_pg)*100:.1f}%, Sec: {nonbuy_sec:.2f}) | "
            f"Winner Owned Blue Share={win_owned_b/max(1, tot_w)*100:.1f}% ({win_owned_b}/{tot_w}) | "
            f"Pipeline Snapshots (Ready/Scanned/Glitched)={mean_ready:.2f}/{mean_scanned:.2f}/{mean_glitched:.2f}"
        )
        for p in pod_counts:
            pt_pod = pod_trackers[p]
            p_g = pt_pod.blue_variant_games[b_code]
            p_pg = pt_pod.blue_variant_player_games[b_code]
            p_buy_pg = pt_pod.blue_variant_buyer_player_games[b_code]
            p_buy_w = pt_pod.blue_variant_buyer_wins[b_code]
            p_nonbuy_pg = pt_pod.blue_variant_nonbuyer_player_games[b_code]
            p_nonbuy_w = pt_pod.blue_variant_nonbuyer_wins[b_code]
            p_bdice = pt_pod.blue_variant_dice_bought[b_code]
            p_win_b = pt_pod.blue_variant_winner_owned_blue[b_code]
            p_tot_w = pt_pod.blue_variant_total_winners[b_code]
            print(
                f"      {p}P [{b_code}]: Games={p_g:3d}, Blue Bought={p_bdice:3d} ({p_bdice/max(1, p_g):.2f}/game), "
                f"Buyer Rate={p_buy_pg/max(1, p_pg)*100:.1f}%, "
                f"Buyer Win={p_buy_w/max(1, p_buy_pg)*100:.1f}% vs Non-Buyer Win={p_nonbuy_w/max(1, p_nonbuy_pg)*100:.1f}%, "
                f"Winner Owned Blue={p_win_b/max(1, p_tot_w)*100:.1f}%"
            )

    print("\n=== 5. BLUE STAR ACTIVATION & PIPELINE TRIAGE TELEMETRY ===")
    print(
        f"  B1 (Honeypot Telemetry, $5): Star Faces Rolled={tracker.b1_star_rolled:,} | "
        f"Bounty Triggers (+$2)={tracker.b1_bounty_triggers:,} ({tracker.b1_bounty_triggers/max(1, tracker.b1_star_rolled)*100:.1f}% trigger rate) | "
        f"Total Bounty Cash=${tracker.b1_bounty_cash_gained:,} | "
        f"Ransom Leaks Prevented={tracker.b1_ransom_leaks_prevented:,}"
    )
    print(
        f"  B2 (Deep R&D Vault, $6): Star Faces Rolled={tracker.b2_star_rolled:,} | "
        f"Committed as Shield={tracker.b2_committed_as_shield:,} vs Kept for Phase 3A={tracker.b2_kept_for_income_option:,} | "
        f"Secrets Purchased ($4 -> +1 Secret)={tracker.b2_secret_purchases:,}"
    )
    print(
        f"  B3 (Air-Gapped Backup, $4): Star Faces Rolled in Phase 2={tracker.b3_star_rolled_phase2:,} | "
        f"Survived to Phase 3A={tracker.b3_star_surviving_phase3a:,} | "
        f"Glitched -> Scanned Rescues={tracker.b3_triage_triggers:,} "
        f"({tracker.b3_triage_triggers/max(1, tracker.b3_star_surviving_phase3a)*100:.1f}% active rescue rate; "
        f"Colored Rescued={tracker.b3_colored_dice_rescued:,}, Gray Rescued={tracker.b3_gray_dice_rescued:,}, "
        f"Empty Glitched No-Ops={tracker.b3_empty_glitched_noops:,}) | "
        f"Dual-Output Shield Preserved Over Pure Shield={tracker.dual_output_shield_preserved_over_pure:,} "
        f"(B3 Specifically Preserved={tracker.b3_shield_preserved_over_pure:,})"
    )

    print("\n=== 6. ALL 12 MARKET VARIANT CARDS OVERVIEW ===")
    for v_code in ("R1", "R2", "R3", "B1", "B2", "B3", "G1", "G2", "G3", "Y1", "Y2", "Y3"):
        ag = variant_active_games[v_code]
        apg = variant_active_player_games[v_code]
        bpg = variant_buyer_player_games[v_code]
        bw = variant_buyer_wins[v_code]
        bs = variant_buyer_survivals[v_code]
        bought = tracker.variant_purchases_by_code[v_code]
        print(
            f"  {v_code}: Active Games={ag:4d} | Dice Bought={bought:4d} ({bought/max(1, ag):.2f}/game) | "
            f"Buyer Rate={bpg/max(1, apg)*100:5.1f}% | Buyer Win={bw/max(1, bpg)*100:5.1f}% | Buyer Surv={bs/max(1, bpg)*100:5.1f}%"
        )

    summary_payload = {
        "results": {
            k: {sk: sv for sk, sv in v.items() if sk != "all_ending_secrets"}
            for k, v in results.items()
        },
        "blue_variants": {
            b_code: {
                "games": tracker.blue_variant_games[b_code],
                "player_games": tracker.blue_variant_player_games[b_code],
                "dice_bought": tracker.blue_variant_dice_bought[b_code],
                "total_market_dice_bought": tracker.blue_variant_total_market_dice_bought[b_code],
                "buyer_player_games": tracker.blue_variant_buyer_player_games[b_code],
                "nonbuyer_player_games": tracker.blue_variant_nonbuyer_player_games[b_code],
                "buyer_wins": tracker.blue_variant_buyer_wins[b_code],
                "nonbuyer_wins": tracker.blue_variant_nonbuyer_wins[b_code],
                "buyer_survivals": tracker.blue_variant_buyer_survivals[b_code],
                "nonbuyer_survivals": tracker.blue_variant_nonbuyer_survivals[b_code],
                "winner_owned_blue": tracker.blue_variant_winner_owned_blue[b_code],
                "total_winners": tracker.blue_variant_total_winners[b_code],
                "buyer_mean_secrets": statistics.mean(tracker.blue_variant_buyer_secrets[b_code]) if tracker.blue_variant_buyer_secrets[b_code] else 0.0,
                "nonbuyer_mean_secrets": statistics.mean(tracker.blue_variant_nonbuyer_secrets[b_code]) if tracker.blue_variant_nonbuyer_secrets[b_code] else 0.0,
                "mean_ready_snapshot": tracker.variant_ready_snapshot_sum[b_code] / max(1, tracker.variant_player_rounds[b_code]),
                "mean_scanned_snapshot": tracker.variant_scanned_snapshot_sum[b_code] / max(1, tracker.variant_player_rounds[b_code]),
                "mean_glitched_snapshot": tracker.variant_glitched_snapshot_sum[b_code] / max(1, tracker.variant_player_rounds[b_code]),
            }
            for b_code in ("B1", "B2", "B3")
        },
        "star_telemetry": {
            "b1_star_rolled": tracker.b1_star_rolled,
            "b1_bounty_triggers": tracker.b1_bounty_triggers,
            "b1_bounty_cash_gained": tracker.b1_bounty_cash_gained,
            "b1_ransom_leaks_prevented": tracker.b1_ransom_leaks_prevented,
            "b2_star_rolled": tracker.b2_star_rolled,
            "b2_committed_as_shield": tracker.b2_committed_as_shield,
            "b2_kept_for_income_option": tracker.b2_kept_for_income_option,
            "b2_secret_purchases": tracker.b2_secret_purchases,
            "b3_star_rolled_phase2": tracker.b3_star_rolled_phase2,
            "b3_star_surviving_phase3a": tracker.b3_star_surviving_phase3a,
            "b3_triage_triggers": tracker.b3_triage_triggers,
            "b3_colored_dice_rescued": tracker.b3_colored_dice_rescued,
            "b3_gray_dice_rescued": tracker.b3_gray_dice_rescued,
            "b3_empty_glitched_noops": tracker.b3_empty_glitched_noops,
            "dual_output_shield_preserved_over_pure": tracker.dual_output_shield_preserved_over_pure,
            "b3_shield_preserved_over_pure": tracker.b3_shield_preserved_over_pure,
        },
    }

    if output_json_path:
        os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(summary_payload, f, indent=2)
        print(f"\nTelemetry JSON written to: {output_json_path}")

    return summary_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Rogue Agent v0.32.0 Telemetry Sweep")
    parser.add_argument("--games", type=int, default=1000, help="Number of games per pod (default: 1000)")
    parser.add_argument("--seed", type=int, default=42, help="Base random seed (default: 42)")
    parser.add_argument(
        "--json",
        type=str,
        default="docs/findings/v320_telemetry_summary.json",
        help="Path to output JSON summary",
    )
    args = parser.parse_args()

    run_v320_telemetry_sweep(
        num_games=args.games,
        base_seed=args.seed,
        output_json_path=args.json,
    )


if __name__ == "__main__":
    main()
