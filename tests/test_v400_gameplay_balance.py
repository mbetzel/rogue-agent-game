"""Unit tests for Phase 56 (v0.40.0 Candidate) Gameplay Balance Architecture.

Covers TEST-V400-01 through TEST-V400-08 and invariants INV-V400-01 through INV-V400-08
per docs/specs/v400_gameplay_balance_spec.md.
"""

from __future__ import annotations

import unittest
from typing import Dict, List, Optional

from sim.bots.base import BaseBot, Phase3ActionPlan
from sim.config import (
    CubeColor,
    DieColor,
    GameConfig,
    RoundSequence,
    V040_SHARE_REGAIN_CAP,
    V040_SHARE_REGAIN_COST_MONEY,
    V040_TRACK_STEP_COSTS,
    V040_TRIAGE_CAPACITY,
)
from sim.engine import secret_faces
from sim.engine.core import GameEngine
from sim.engine.phase2_compiler import clamp_green_cubes_to_add, resolve_corruption_space
from sim.engine.phase5_pipeline_shift import execute_pipeline_shift, execute_player_pipeline_shift
from sim.engine.phase6_operations import execute_operations, execute_player_operations_turn, execute_share_regain
from sim.engine.research_tracks import apply_level, level_of, step_cost, upgrade_and_resolve
from sim.engine.state import GameState, PlayerState
from sim.entities import (
    CorruptionSpace,
    Die,
    Face,
    VersionCard,
    create_colored_die,
    create_gray_die,
    get_all_version_cards,
    get_default_version_deck,
)


class StubBot(BaseBot):
    """Minimal stub bot for deterministic test execution."""

    def __init__(self, bot_id: int = 0):
        super().__init__(bot_id=bot_id, name=f"StubBot_{bot_id}")

    def take_operations_actions(self, player_state, game_state, rng):
        return Phase3ActionPlan()


class TestV400GameplayBalance(unittest.TestCase):
    """TEST-V400-01 through TEST-V400-08 per spec §7."""

    def test_v400_01_phase_resequencing_and_immediate_hardware_gratification(self):
        """TEST-V400-01: Verify Phase 5 Operations precedes Phase 6 Pipeline Shift,

        and hardware upgraded in Phase 5 takes effect in Phase 6 of the same round (INV-V400-01).
        """
        cfg = GameConfig.v040(num_players=2)
        self.assertTrue(cfg.operations_before_pipeline_shift)
        self.assertTrue(cfg.purchased_dice_to_scanned)

        engine = GameEngine(cfg, seed=42)
        p0 = engine.state.players[0]
        p0.research_tokens = 5
        # Set release track to L1 (release_bandwidth = 4)
        p0.release_level = 1
        p0.release_bandwidth = 4

        # Put 5 dice in scanned_dice
        p0.scanned_dice = [create_gray_die(100 + i) for i in range(5)]
        p0.ready_for_release_dice = []

        # Intercept Operations planning so P0 upgrades RELEASE from L1 to L2 (step cost = 2)
        class UpgradeReleaseBot(StubBot):
            research_aware = False

            def take_operations_actions(self, player_state, game_state, rng):
                return Phase3ActionPlan(track_upgrades=["RELEASE"])

        p0.bot = UpgradeReleaseBot(0)

        # Run one round
        tel = engine.run_round()

        # Telemetry verification: phases executed in sequence 1..6
        self.assertEqual(tel.phases_executed, [1, 2, 3, 4, 5, 6])
        # P0 upgraded Release to L2 in Phase 5
        self.assertEqual(p0.release_level, 2)
        self.assertEqual(p0.release_bandwidth, 5)

        # In Phase 6 Scanned Graduation, exactly 5 dice graduated
        self.assertEqual(len(p0.ready_for_release_dice), 5)
        self.assertEqual(len(p0.scanned_dice), 0)

    def test_v400_02_market_purchases_placed_into_scanned_box(self):
        """TEST-V400-02: Verify purchased Central Market dice enter scanned_dice,

        while Breakthrough dice enter ready_for_release_dice (INV-V400-02).
        """
        cfg = GameConfig.v040(num_players=2)
        engine = GameEngine(cfg)
        p0 = engine.state.players[0]
        p0.money = 20
        d1 = create_gray_die(101)
        d2 = create_gray_die(102)
        p0.ready_for_release_dice = [d1, d2]
        p0.scanned_dice = []

        class BuyDiceBot(StubBot):
            def take_operations_actions(self, player_state, game_state, rng):
                return Phase3ActionPlan(market_purchases=[DieColor.RED, DieColor.BLUE])

        p0.bot = BuyDiceBot(0)
        plan = Phase3ActionPlan(market_purchases=[DieColor.RED, DieColor.BLUE])
        execute_player_operations_turn(engine, p0, plan)

        # Purchased dice must be in scanned_dice, not ready_for_release
        self.assertEqual(len(p0.scanned_dice), 2)
        self.assertEqual(p0.scanned_dice_purchased_this_turn, 2)
        self.assertEqual(p0.ready_for_release_dice, [d1, d2])
        self.assertEqual({d.color for d in p0.scanned_dice}, {DieColor.RED, DieColor.BLUE})

    def test_v400_03_scanned_graduation_under_release_bandwidth_gate(self):
        """TEST-V400-03: Verify Scanned Graduation strictly respects Release Bandwidth

        when both returned dice and purchased dice occupy Scanned (INV-V400-03).
        """
        cfg = GameConfig.v040(num_players=2)
        engine = GameEngine(cfg)
        p0 = engine.state.players[0]
        p0.release_bandwidth = 4
        p0.ready_for_release_dice = []

        # 2 purchased dice + 4 returned dice = 6 dice in scanned
        p0.scanned_dice = [create_gray_die(200 + i) for i in range(6)]
        p0.in_production_dice = []

        rec = execute_player_pipeline_shift(engine, p0)
        self.assertEqual(len(rec.graduated_ids), 4)
        self.assertEqual(len(p0.ready_for_release_dice), 4)
        self.assertEqual(len(p0.scanned_dice), 2)
        self.assertEqual(rec.held_in_scanned, 2)

    def test_v400_04_triage_track_progression_and_level_2_milestone(self):
        """TEST-V400-04: Verify Triage Track bandwidth is 1 at L0-L3 and 2 at L4,

        and advancing to L2 grants +1 Corporate Secret milestone (INV-V400-04).
        """
        cfg = GameConfig.v040(num_players=2)
        engine = GameEngine(cfg)
        p0 = engine.state.players[0]
        p0.secrets = 4
        p0.research_tokens = 20

        # L0
        self.assertEqual(p0.triage_level, 0)
        self.assertEqual(p0.triage_bandwidth, 1)

        # Upgrade to L1
        p0.upgrade_track("TRIAGE")
        self.assertEqual(p0.triage_level, 1)
        self.assertEqual(p0.triage_bandwidth, 1)
        self.assertEqual(p0.secrets, 4)

        # Upgrade to L2 -> awards +1 Corporate Secret milestone
        p0.upgrade_track("TRIAGE")
        self.assertEqual(p0.triage_level, 2)
        self.assertEqual(p0.triage_bandwidth, 1)
        self.assertEqual(p0.secrets, 5)
        self.assertIn("triage_l2", p0.triage_milestones_claimed)

        # Upgrade to L3
        p0.upgrade_track("TRIAGE")
        self.assertEqual(p0.triage_level, 3)
        self.assertEqual(p0.triage_bandwidth, 1)
        self.assertEqual(p0.secrets, 5)

        # Upgrade to L4 -> bandwidth increases to 2
        p0.upgrade_track("TRIAGE")
        self.assertEqual(p0.triage_level, 4)
        self.assertEqual(p0.triage_bandwidth, 2)

    def test_v400_05_fifo_conveyor_triage_and_phase6_market_leader_bonus(self):
        """TEST-V400-05: Verify Secret faces bank during Phase 6 Conveyor Triage,

        and a banked Red Secret triggers the Market Leader Bonus evaluating post-Phase 5 Market Share (INV-V400-05).
        """
        cfg = GameConfig.v040(num_players=2)
        engine = GameEngine(cfg)
        p0 = engine.state.players[0]
        p1 = engine.state.players[1]

        # Equal starting Market Share
        p0.market_share = 10
        p1.market_share = 10
        p0.secrets = 5
        p1.secrets = 5

        # P0 has a Red Secret die in Processing Box (glitched_dice)
        red_die = create_colored_die(DieColor.RED, 999, face_profile="V038_DRAFT")
        secret_faces.enter_processing_box(p0, red_die, engine.state.current_round)

        # P1 spends cash in Operations to gain +1 Market Share, taking 1st place
        p1.money = 6
        execute_share_regain(engine, p1, wanted=1)
        self.assertEqual(p1.market_share, 11)
        self.assertEqual(p0.market_share, 10)

        # Now execute Phase 6 Pipeline Shift
        execute_pipeline_shift(engine)

        # P0 banked the Red Secret: gains owner yield (+2 Corporate Secrets)
        # Red die moved from glitched_dice to scanned_dice
        self.assertEqual(len(p0.glitched_dice), 0)
        self.assertEqual(len(p0.scanned_dice), 1)

        # Market Leader Bonus evaluated post-Phase 5 Market Share:
        # P1 has 11 MS (1st place) -> +3 Secrets
        # P0 has 10 MS (2nd place) -> +1 Secret
        # P0 total secrets: 5 starting + 2 (red secret yield) + 1 (2nd place MLB) = 8
        # P1 total secrets: 5 starting + 3 (1st place MLB) = 8
        self.assertEqual(p1.secrets, 8)
        self.assertEqual(p0.secrets, 8)
        self.assertEqual(engine.state.red_secret_payouts_fired, 1)

    def test_v400_06_cash_fueled_pr_regain_and_per_turn_limit(self):
        """TEST-V400-06: Verify PR Market Share regain costs $3 Cash per +1 MS

        and enforces PR Track level caps (INV-V400-06).
        """
        cfg = GameConfig.v040(num_players=2)
        engine = GameEngine(cfg)
        p0 = engine.state.players[0]
        p0.patent_level = 0  # cap = 1
        p0.market_share = 10
        p0.market_share_max = 20
        p0.money = 10
        p0.research_tokens = 0

        # Attempt to regain 2 Market Share
        done = execute_share_regain(engine, p0, wanted=2)

        self.assertEqual(done, 1)
        self.assertEqual(p0.market_share, 11)
        self.assertEqual(p0.money, 7)  # paid $3
        self.assertEqual(p0.money_spent_regain, 3)
        self.assertEqual(p0.research_tokens, 0)  # 0 research spent

        # Attempt another regain in the same turn -> rejected by turn limit
        done2 = execute_share_regain(engine, p0, wanted=1)
        self.assertEqual(done2, 0)
        self.assertEqual(p0.market_share, 11)
        self.assertEqual(p0.money, 7)

    def test_v400_07_hardware_step_costs_and_upgrade_cap(self):
        """TEST-V400-07: Verify track step costs are (1, 2, 2, 3) 🔬 and max 2 hardware upgrades per turn (INV-V400-07)."""
        cfg = GameConfig.v040(num_players=2)
        self.assertEqual(cfg.track_step_costs, (1, 2, 2, 3))
        self.assertEqual(cfg.max_hardware_upgrades_per_turn, 2)

        engine = GameEngine(cfg)
        p0 = engine.state.players[0]
        p0.research_tokens = 10

        # Upgrade Defense L0 -> L1 (cost 1)
        cost_l0 = step_cost(cfg, p0, "DEFENSE")
        self.assertEqual(cost_l0, 1)
        p0.upgrade_track("DEFENSE")
        self.assertEqual(p0.defense_level, 1)
        self.assertEqual(p0.research_tokens, 9)

        # Upgrade Defense L1 -> L2 (cost 2)
        cost_l1 = step_cost(cfg, p0, "DEFENSE")
        self.assertEqual(cost_l1, 2)
        p0.upgrade_track("DEFENSE")
        self.assertEqual(p0.defense_level, 2)
        self.assertEqual(p0.research_tokens, 7)

        # Upgrade Defense L2 -> L3 (cost 2)
        cost_l2 = step_cost(cfg, p0, "DEFENSE")
        self.assertEqual(cost_l2, 2)
        p0.upgrade_track("DEFENSE")
        self.assertEqual(p0.defense_level, 3)
        self.assertEqual(p0.research_tokens, 5)

        # Upgrade Defense L3 -> L4 (cost 3)
        cost_l3 = step_cost(cfg, p0, "DEFENSE")
        self.assertEqual(cost_l3, 3)
        p0.upgrade_track("DEFENSE")
        self.assertEqual(p0.defense_level, 4)
        self.assertEqual(p0.research_tokens, 2)

        # Verify max 2 hardware upgrades per turn in operations
        p1 = engine.state.players[1]
        p1.research_tokens = 10
        p1.defense_level = 0
        p1.triage_level = 0
        p1.release_level = 0

        class GreedyUpgradeBot(StubBot):
            def take_operations_actions(self, player_state, game_state, rng):
                return Phase3ActionPlan(track_upgrades=["DEFENSE", "TRIAGE", "RELEASE"])

        p1.bot = GreedyUpgradeBot(1)
        from sim.engine.phase6_operations import resolve_operations_plan

        plan = resolve_operations_plan(p1.bot, p1, engine.state, engine.rng)
        execute_player_operations_turn(engine, p1, plan)

        # Exactly 2 upgrades should have executed
        total_upgrades = p1.defense_level + p1.triage_level + p1.release_level
        self.assertEqual(total_upgrades, 2)

    def test_v400_08_global_green_cube_cap_clamping(self):
        """TEST-V400-08: Verify Green cube additions are clamped when the global cap of 5 is reached (INV-V400-08)."""
        cfg = GameConfig.v040(num_players=2, global_green_cube_cap=5)
        engine = GameEngine(cfg)

        # Set active Green cubes across tower, staging cup, and exit tray to 4
        engine.state.staging_cup[CubeColor.GREEN] = 2
        engine.state.last_exited_cubes[CubeColor.GREEN] = 1
        engine.state.tower.stuck_cubes[CubeColor.GREEN] = 1
        self.assertEqual(engine.state.total_green_cubes_in_circulation(), 4)

        # Corruption space calling for Add 2G
        space = CorruptionSpace(index=1, label="Add 2G", add_cubes={CubeColor.GREEN: 2})
        resolve_corruption_space(
            engine=engine,
            space=space,
            player_commitments={},
            exited_cubes={},
        )

        # Only 1 Green cube should have been added to staging cup (from 2 to 3)
        self.assertEqual(engine.state.staging_cup[CubeColor.GREEN], 3)
        self.assertEqual(engine.state.total_green_cubes_in_circulation(), 5)

        # Further green additions are completely clamped to 0
        resolve_corruption_space(
            engine=engine,
            space=space,
            player_commitments={},
            exited_cubes={},
        )
        self.assertEqual(engine.state.staging_cup[CubeColor.GREEN], 3)
        self.assertEqual(engine.state.total_green_cubes_in_circulation(), 5)

    def test_v400_config_validation(self):
        """Test validation rules in _validate_v040()."""
        # Invalid step costs
        with self.assertRaises(ValueError):
            GameConfig.v040(track_step_costs=(1, 2, 0, 3))

        # Invalid global green cube cap
        with self.assertRaises(ValueError):
            GameConfig.v040(global_green_cube_cap=0)

        # Invalid share regain currency
        with self.assertRaises(ValueError):
            GameConfig.v040(share_regain_currency="CREDITS")

        # Invalid operations_before_pipeline_shift with round_sequence != SIX_PHASE
        with self.assertRaises(ValueError):
            GameConfig.v040(round_sequence=RoundSequence.V033_THREE_PHASE)

    def test_v400_asymmetric_version_cards(self):
        """Verify V040_ASYMMETRIC profile produces the 3 distinct thematic branches."""
        cards = get_all_version_cards(profile="V040_ASYMMETRIC")
        self.assertEqual(len(cards), 9)

        deck = get_default_version_deck(profile="V040_ASYMMETRIC")
        self.assertEqual(len(deck), 3)
        self.assertEqual(deck[0].version_str, "v1.0")
        self.assertEqual(deck[1].version_str, "v2.0")
        self.assertEqual(deck[2].version_str, "v3.0")

        # Branch Alpha (Economic Extortion)
        self.assertEqual(deck[0].staging_payload, {CubeColor.RED: 2, CubeColor.BLUE: 1})
        self.assertEqual(deck[0].directive_code, "SCRIPT_KIDDIE")

    def test_backwards_compatibility_presets(self):
        """Verify legacy presets remain intact and bit-compatible."""
        cfg_v038f = GameConfig.v038f()
        self.assertFalse(cfg_v038f.operations_before_pipeline_shift)
        self.assertFalse(cfg_v038f.purchased_dice_to_scanned)
        self.assertEqual(cfg_v038f.share_regain_currency, "RESEARCH")
        self.assertEqual(cfg_v038f.track_step_costs, (1, 1, 2, 2))

        cfg_v037 = GameConfig.v037()
        self.assertFalse(cfg_v037.operations_before_pipeline_shift)
        self.assertEqual(cfg_v037.track_step_costs, (1, 1, 2, 2))


if __name__ == "__main__":
    unittest.main()
