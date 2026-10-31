"""Unit and integration tests for Model C: End-of-Round Cleanup Cap for Patches.

Test Matrix:
- TC-01: Phase 1 boot allows patch accumulation above cap without premature clipping.
- TC-02: Hotfixing in Phase 1 allows spending down from an above-cap patch balance, and committing preserves above-cap patches.
- TC-03: Phase 3 operations can spend down from an above-cap patch total.
- TC-04: Sim engine End-of-Round Cleanup clamps unspent patches to max_patch_tokens.
- TC-05: Web controller complete_round() discards excess patches and logs the event.
- TC-06: End-of-Round Cleanup preserves patches at or below max_patch_tokens without discard or event log.
- TC-07: Patient Zero players are skipped during End-of-Round Cleanup.
- TC-08: Web schema serialize_game_state exposes max_patch_tokens at top level.
"""

from __future__ import annotations

import unittest
from sim.config import CubeColor, DieColor, GameConfig, ShieldColor
from sim.engine import GameEngine, PlayerState
from sim.engine.phase1_boot import execute_phase_1
from sim.engine.phase3_ops import execute_phase_3
from sim.entities import Die, Face, create_gray_die
from sim.bots.base import BaseBot, Phase3ActionPlan
from web.controller.core import GameController
from web.controller.serializer import complete_round
from web.schemas import GameStateSerializer


class TestModelCPatches(unittest.TestCase):
    """Test suite for Model C: End-of-Round Cleanup Cap for Patches."""

    def test_tc01_phase1_boot_allows_patch_accumulation_above_cap(self):
        """TC-01: Phase 1 boot allows patch accumulation above cap without premature clipping."""
        cfg = GameConfig(num_players=2, max_patch_tokens=3)
        engine = GameEngine(config=cfg, seed=42)
        player = engine.state.players[0]
        player.patches = 2

        class PassiveBot(BaseBot):
            def choose_contractor_hires(self, *args, **kwargs):
                return 0

            def choose_yahtzee_rerolls(self, *args, **kwargs):
                return []

            def commit_shields(self, *args, **kwargs):
                return {}

        player.bot = PassiveBot(bot_id=0)

        # Give player 4 gray dice all showing +1 🔧 face on all 6 faces
        patch_face = Face("+1 🔧", patches=1)
        player.ready_dice = [
            Die(die_id=i, color=DieColor.GRAY, cost=0, vp=0, faces=[patch_face] * 6)
            for i in range(4)
        ]
        # Execute Phase 1 boot
        execute_phase_1(engine)

        # Player started with 2 patches, rolled 4 patches -> total should be 6, NOT capped at 3
        self.assertEqual(player.patches, 6)
        self.assertGreater(player.patches, engine.config.max_patch_tokens)

    def test_tc02_phase1_hotfixing_with_above_cap_patches(self):
        """TC-02: Hotfixing in Phase 1 allows spending down from an above-cap patch balance."""
        controller = GameController()
        controller.new_game(num_players=2, seed=42)
        human_player = controller.state.players[0]
        # Start Phase 1 by rolling the pool
        controller.roll_pool(0)

        # Set human player patches to 5 (> max_patch_tokens of 3)
        human_player.patches = 5
        self.assertEqual(controller.state.config.max_patch_tokens, 3)

        # Hotfix die index 0 using 1 patch token
        state = controller.hotfix_reroll(0, 0)
        self.assertIsNotNone(state)
        # Patches should be 4, still above cap of 3
        self.assertEqual(human_player.patches, 4)

        # Hotfix die index 1 using another patch token
        state2 = controller.hotfix_reroll(0, 1)
        self.assertIsNotNone(state2)
        # Patches should now be 3
        self.assertEqual(human_player.patches, 3)

        # Now test commit_defenses when player has > 3 patches
        human_player.patches = 5
        # Set rolled die faces to non-patch, non-glitch to verify commit doesn't clamp patches
        controller.commit_defenses(0, commitments={})
        self.assertEqual(human_player.patches, 5)

    def test_tc03_phase3_ops_spending_down_excess_patches(self):
        """TC-03: Phase 3 operations can spend down from an above-cap patch total."""
        cfg = GameConfig(num_players=2, max_patch_tokens=3)
        engine = GameEngine(config=cfg, seed=42)
        player = engine.state.players[0]

        # Player enters Phase 3 with 5 patches and 2 unpatched dice
        player.patches = 5
        player.unpatched_dice = [create_gray_die(101), create_gray_die(102)]
        player.ready_dice = []
        player.system_reboot_used = True  # Prevent system reboot trigger

        # Bot plans to patch both unpatched dice using patch tokens
        class CustomBot(BaseBot):
            def take_phase3_actions(self, p_state, g_state, rng):
                return Phase3ActionPlan(
                    patch_actions=[{"die_index": 0, "use_cash": False}, {"die_index": 0, "use_cash": False}]
                )

        player.bot = CustomBot(bot_id=0)
        execute_phase_3(engine)

        # Player spent 2 patches, leaving 3.
        self.assertEqual(len(player.unpatched_dice), 0)
        self.assertEqual(len(player.ready_dice), 2)
        self.assertEqual(player.patches, 3)

    def test_tc04_sim_engine_end_of_round_cleanup_clamps_unspent_patches(self):
        """TC-04: Sim engine End-of-Round Cleanup clamps unspent patches to max_patch_tokens."""
        cfg = GameConfig(num_players=2, max_patch_tokens=3)
        engine = GameEngine(config=cfg, seed=42)
        player0 = engine.state.players[0]
        player1 = engine.state.players[1]

        # Player 0 has 5 patches, Player 1 has 2 patches
        player0.patches = 5
        player1.patches = 2

        # Empty action plans for phase 3
        class PassiveBot(BaseBot):
            def take_phase3_actions(self, p_state, g_state, rng):
                return Phase3ActionPlan()

        player0.bot = PassiveBot(bot_id=0)
        player1.bot = PassiveBot(bot_id=1)
        execute_phase_3(engine)

        # At End-of-Round Cleanup, Player 0 should be clamped to 3, Player 1 stays at 2
        self.assertEqual(player0.patches, 3)
        self.assertEqual(player1.patches, 2)

    def test_tc05_web_complete_round_discards_excess_patches_and_logs(self):
        """TC-05: Web controller complete_round() discards excess patches and logs the event."""
        controller = GameController()
        controller.new_game(num_players=2, seed=42)
        player0 = controller.state.players[0]
        player1 = controller.state.players[1]

        player0.patches = 5
        player1.patches = 1
        controller.state.config.max_patch_tokens = 3

        complete_round(controller)

        # Player 0 clamped to 3, Player 1 remains 1
        self.assertEqual(player0.patches, 3)
        self.assertEqual(player1.patches, 1)

        # Check event log
        name0 = controller.player_meta[0]["name"]
        expected_log = f"{name0} discarded 2 excess Patch token(s) at End-of-Round Cleanup (cap: 3)."
        self.assertIn(expected_log, controller.event_log)

    def test_tc06_end_of_round_cleanup_preserves_patches_at_or_below_cap(self):
        """TC-06: End-of-Round Cleanup preserves patches at or below max_patch_tokens without discard or event log."""
        controller = GameController()
        controller.new_game(num_players=2, seed=42)
        player0 = controller.state.players[0]
        player1 = controller.state.players[1]

        player0.patches = 3
        player1.patches = 2
        controller.state.config.max_patch_tokens = 3

        initial_log_count = len(controller.event_log)
        complete_round(controller)

        self.assertEqual(player0.patches, 3)
        self.assertEqual(player1.patches, 2)

        # No discard event should be logged
        for entry in controller.event_log[initial_log_count:]:
            self.assertNotIn("discarded", entry)
            self.assertNotIn("excess Patch", entry)

    def test_tc07_patient_zero_skipped_during_cleanup(self):
        """TC-07: Patient Zero players are skipped during End-of-Round Cleanup."""
        # Sim engine test
        cfg = GameConfig(num_players=2, max_patch_tokens=3)
        engine = GameEngine(config=cfg, seed=42)
        pz_player = engine.state.players[0]
        pz_player.is_patient_zero = True
        pz_player.patches = 6

        class PassiveBot(BaseBot):
            def take_phase3_actions(self, p_state, g_state, rng):
                return Phase3ActionPlan()

        pz_player.bot = PassiveBot(bot_id=0)
        execute_phase_3(engine)

        # Patient Zero is skipped
        self.assertEqual(pz_player.patches, 6)

        # Web controller test
        controller = GameController()
        controller.new_game(num_players=2, seed=42)
        pz_player_web = controller.state.players[0]
        pz_player_web.is_patient_zero = True
        pz_player_web.patches = 7

        initial_log_count = len(controller.event_log)
        complete_round(controller)

        self.assertEqual(pz_player_web.patches, 7)
        for entry in controller.event_log[initial_log_count:]:
            self.assertNotIn("discarded", entry)

    def test_tc08_web_schema_serializes_max_patch_tokens(self):
        """TC-08: Web schema serialize_game_state exposes max_patch_tokens at top level."""
        controller = GameController()
        controller.new_game(num_players=2, seed=42)
        controller.state.config.max_patch_tokens = 3

        full_state = controller.get_full_state()
        self.assertIn("max_patch_tokens", full_state)
        self.assertEqual(full_state["max_patch_tokens"], 3)


if __name__ == "__main__":
    unittest.main()
