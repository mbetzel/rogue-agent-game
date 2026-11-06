"""Unit and Integration Tests for Phase 30: Consolidated Fast-Patching & Pure Reroll Streamlining (v0.23.0 Baseline)."""

from __future__ import annotations

import random
import unittest
from typing import Dict, List, Tuple

from sim.bots.base import BaseBot, Phase3ActionPlan
from sim.bots.adaptive_balanced import AdaptiveBalancedBot
from sim.bots.secops_turtle import SecOpsTurtleBot
from sim.bots.venture_greed import VentureGreedBot
from sim.bots.accelerationist import AccelerationistBot
from sim.bots.reckless_saboteur import RecklessSaboteurBot

from sim.config import CubeColor, DieColor, GameConfig, ShieldColor
from sim.engine.core import GameEngine
from sim.engine.phase1_boot import execute_phase_1
from sim.engine.phase2_threat import execute_phase_2
from sim.engine.phase3_ops import execute_phase_3
from sim.engine.state import PlayerState, ProductionRole
from sim.entities import (
    ArchetypeCode,
    Die,
    Face,
    create_colored_die,
    create_gray_die,
    create_white_die,
    get_archetype_by_code,
)
from web.controller.core import GameController
from web.controller.capabilities import get_action_capabilities
from web.controller.phase1_actions import debug_unlock_die, perform_reroll, auto_execute_bots_phase_1


class TestV230Rules(unittest.TestCase):
    """Exhaustive test suite for v0.23.0 Consolidated Fast-Patching & Pure Reroll Streamlining."""

    # =========================================================================
    # Category 1: Pure Yahtzee Rerolls & Absolute Locks
    # =========================================================================

    def test_glitch_die_locks_immediately_on_roll(self) -> None:
        """INV-LOCK-01: Any die rolling a Glitch face receives is_locked = True immediately."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        red = create_colored_die(DieColor.RED, 1)
        glitch_face = red.faces[4]  # Face 5 is Glitch
        self.assertTrue(glitch_face.is_glitch)
        red.faces = [glitch_face] * 6  # Force glitch on all faces
        p0.ready_for_release_dice = [red]

        class PassiveBot(BaseBot):
            def choose_yahtzee_rerolls(self, *args, **kwargs):
                return []

        p0.bot = PassiveBot(0)
        execute_phase_1(engine)

        self.assertTrue(red.is_locked, "Glitch die must be locked")

    def test_corruption_track_locks_cannot_be_unlocked_with_patches(self) -> None:
        """INV-LOCK-02 & INV-PATCH-01: Corruption track locks are absolute; patches cannot unlock them."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.patches = 3

        # Activate CASH corruption lock via pending locks
        engine.state.pending_next_phase_locks = {"CASH"}
        gray = create_gray_die(1)
        cash_face = Face("+$1", money=1)
        gray.faces = [cash_face] * 6
        p0.ready_for_release_dice = [gray]

        for p in engine.state.players:
            p.bot = BaseBot(p.player_id)

        class AttemptUnlockBot(BaseBot):
            def choose_debug_unlocks(self, *args, **kwargs):
                return [0]  # Attempts to debug unlock

            def choose_yahtzee_rerolls(self, *args, **kwargs):
                return [0]

        p0.bot = AttemptUnlockBot(0)
        execute_phase_1(engine)

        # Invariant: Phase locks excised in v0.29.0; die is not locked and patches were NEVER deducted
        self.assertFalse(gray.is_locked, "Phase 1 locks excised in v0.29.0")
        self.assertEqual(p0.patches, 3, "Patch count must never decrease in Phase 1")

    def test_standard_reroll_cannot_include_locked_dice(self) -> None:
        """INV-LOCK-03: Reroll indices corresponding to locked dice are strictly filtered out."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]

        red = create_colored_die(DieColor.RED, 1)
        glitch_face = red.faces[4]
        red.faces = [glitch_face] * 6  # Will be locked on roll

        gray = create_gray_die(2)
        money_face = Face("+$1", money=1)
        gray.faces = [money_face] * 6

        p0.ready_for_release_dice = [red, gray]

        reroll_attempts = []

        class BadRerollBot(BaseBot):
            def choose_yahtzee_rerolls(self, player_state, active_dice, rerolls_remaining, *args, **kwargs):
                if rerolls_remaining == 2:
                    reroll_attempts.append(True)
                    # Attempt to reroll both index 0 (locked) and 1 (unlocked)
                    return [0, 1]
                return []

        p0.bot = BadRerollBot(0)
        execute_phase_1(engine)

        self.assertTrue(reroll_attempts, "Bot choose_yahtzee_rerolls should be called")
        # Red was locked, so it was never rerolled and remains locked
        self.assertTrue(red.is_locked)
        self.assertIn(red, p0.glitched_dice)

    def test_patches_never_spent_in_phase_1(self) -> None:
        """INV-PATCH-01: Patch balances must NEVER decrease during Phase 1 for any player."""
        engine = GameEngine(config=GameConfig(num_players=4), seed=42)
        for i, p in enumerate(engine.state.players):
            p.patches = 3
            # Give player some colored dice that may glitch
            red = create_colored_die(DieColor.RED, 100 + i)
            p.ready_for_release_dice.append(red)

        execute_phase_1(engine)

        for p in engine.state.players:
            self.assertGreaterEqual(p.patches, 3, "Patches should never decrease during Phase 1")

    def test_unresolved_glitch_moves_to_glitched_box(self) -> None:
        """INV-LOCK-04: Permanent module die locked on Glitch moves immediately to glitched_dice."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        red = create_colored_die(DieColor.RED, 1)
        red.faces = [red.faces[4]] * 6  # Glitch
        p0.ready_for_release_dice = [red]

        p0.bot = BaseBot(0)
        execute_phase_1(engine)

        self.assertIn(red, p0.glitched_dice, "Glitch die must move to glitched_dice")
        self.assertNotIn(red, p0.in_production_dice, "Glitch die must not be in production")
        self.assertEqual(len(p0.ready_for_release_dice), 0)

    def test_unresolved_contractor_glitch_discarded_to_supply(self) -> None:
        """INV-LOCK-04: White Contractor with unresolved glitch is discarded to general supply."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        contractor = create_white_die(99)
        contractor.faces = [contractor.faces[4]] * 6  # Glitch
        p0.contractor_dice = [contractor]
        p0.ready_for_release_dice = []

        supply_before = engine.state.contractor_supply
        for p in engine.state.players:
            p.bot = BaseBot(p.player_id)
        execute_phase_1(engine)

        self.assertEqual(engine.state.contractor_supply, supply_before + 1)
        self.assertEqual(len(p0.glitched_dice), 0, "White contractor must not enter glitched_dice")
        self.assertEqual(len(p0.in_production_dice), 0)

    # =========================================================================
    # Category 2: Archetype Invariants
    # =========================================================================

    def test_prodigy_rerolls_locked_dice_without_spending_patches(self) -> None:
        """The Prodigy rerolls locked glitch dice with zero patch cost via Brute-Force Bypass."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.archetype = get_archetype_by_code(ArchetypeCode.PRODIGY)
        p0.patches = 0  # Zero patches

        red = create_colored_die(DieColor.RED, 1)
        # Face 5 is glitch, Face 1 is Block 1 Red
        red.current_face = red.faces[4]
        red.is_locked = True
        p0.ready_for_release_dice = [red]

        class ProdigyBot(BaseBot):
            def choose_prodigy_ability(self, *args, **kwargs):
                return True

            def choose_yahtzee_rerolls(self, *args, **kwargs):
                # Reroll the locked die
                return [0]

        p0.bot = ProdigyBot(0)
        execute_phase_1(engine)

        self.assertTrue(p0.v1_used)
        self.assertEqual(p0.patches, 0, "Prodigy rerolls must be free of patch costs")

    def test_prodigy_face_override_non_star(self) -> None:
        """The Prodigy can override 1 rolled die to any legal non-Star face."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.archetype = get_archetype_by_code(ArchetypeCode.PRODIGY)

        gray = create_gray_die(1)
        p0.ready_for_release_dice = [gray]

        target_face = Face("+$2", money=2)

        class ProdigyOverrideBot(BaseBot):
            def choose_prodigy_ability(self, *args, **kwargs):
                return True

            def choose_yahtzee_rerolls(self, *args, **kwargs):
                return []

            def choose_prodigy_face_override(self, player_state, active_dice, *args, **kwargs):
                return (0, target_face)

        p0.bot = ProdigyOverrideBot(0)
        execute_phase_1(engine)

        self.assertEqual(len(p0.in_production_dice), 1)
        self.assertEqual(p0.in_production_dice[0].current_face.name, "+$2")

    def test_prodigy_only_entity_capable_of_rerolling_locks(self) -> None:
        """Non-Prodigy player cannot reroll locked dice; Prodigy can."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]  # Standard (No archetype)
        p1 = engine.state.players[1]
        p1.archetype = get_archetype_by_code(ArchetypeCode.PRODIGY)

        red0 = create_colored_die(DieColor.RED, 10)
        red0.faces = [red0.faces[4]] * 6  # Glitch
        p0.ready_for_release_dice = [red0]

        red1 = create_colored_die(DieColor.RED, 20)
        # Face 5 glitch, Face 1 Block 1 Red
        red1.faces = [red1.faces[4], red1.faces[0], red1.faces[0], red1.faces[0], red1.faces[0], red1.faces[0]]
        p1.ready_for_release_dice = [red1]

        class RerollAllBot(BaseBot):
            def choose_prodigy_ability(self, *args, **kwargs):
                return True

            def choose_yahtzee_rerolls(self, *args, **kwargs):
                return [0]

        p0.bot = RerollAllBot(0)
        p1.bot = RerollAllBot(1)

        execute_phase_1(engine)

        # p0 (Standard) could not reroll locked die; ends up in glitched_dice
        self.assertIn(red0, p0.glitched_dice)
        # p1 (Prodigy) rerolled the locked die
        self.assertTrue(p1.v1_used)

    def test_phreaker_magnetic_splice_free_glitch_to_ready(self) -> None:
        """The Phreaker moves 1 die from glitched_dice directly to ready_for_release_dice for free."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.archetype = get_archetype_by_code(ArchetypeCode.PHREAKER)
        p0.patches = 0

        red = create_colored_die(DieColor.RED, 1)
        p0.glitched_dice = [red]
        p0.scanned_dice = []
        p0.ready_for_release_dice = []

        execute_phase_3(engine)

        # Directly into ready_for_release_dice, glitched_dice empty, 0 patches spent
        self.assertIn(red, p0.ready_for_release_dice)
        self.assertEqual(len(p0.glitched_dice), 0)
        self.assertEqual(p0.patches, 0)
        self.assertTrue(p0.v1_used)

    def test_phreaker_coexists_with_fast_patching(self) -> None:
        """The Phreaker ability and Fast-Patching operate together cleanly in Phase 3B."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.archetype = get_archetype_by_code(ArchetypeCode.PHREAKER)
        p0.patches = 1

        d1 = create_colored_die(DieColor.RED, 1)
        d2 = create_colored_die(DieColor.BLUE, 2)
        p0.glitched_dice = [d1, d2]
        p0.scanned_dice = []
        p0.ready_for_release_dice = []

        class PhreakerAndPatchBot(BaseBot):
            def choose_fast_patches(self, player_state, game_state, rng):
                # Fast patch the remaining die
                return [0]

        p0.bot = PhreakerAndPatchBot(0)
        execute_phase_3(engine)

        # Phreaker moves 1 die free to ready; in v0.29.0 fast-patch is excised so remaining die shifts via triage
        self.assertEqual(p0.patches, 1)
        self.assertEqual(len(p0.glitched_dice), 0)
        self.assertEqual(len(p0.ready_for_release_dice), 1)
        self.assertEqual(len(p0.scanned_dice), 1)

    # =========================================================================
    # Category 3: Consolidated Fast-Patching in Phase 3B
    # =========================================================================

    def test_fast_patch_spends_exact_one_wrench_per_die(self) -> None:
        """Fast-patching costs exactly 1 🔬 per die."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.patches = 2

        d1 = create_colored_die(DieColor.RED, 1)
        d2 = create_colored_die(DieColor.GREEN, 2)
        p0.glitched_dice = [d1, d2]
        p0.scanned_dice = []
        p0.ready_for_release_dice = []

        class FastPatchBothBot(BaseBot):
            def choose_fast_patches(self, player_state, game_state, rng):
                return [0, 1]

        p0.bot = FastPatchBothBot(0)
        execute_phase_3(engine)

        # In v0.29.0 fast-patching is excised; natural triage shifts both dice to scanned with 0 patches spent
        self.assertEqual(p0.patches, 2)
        self.assertEqual(len(p0.glitched_dice), 0)
        self.assertEqual(len(p0.scanned_dice), 2)

    def test_fast_patched_dice_graduate_immediately_to_ready(self) -> None:
        """Fast-patched dice move to scanned_dice, then graduate to ready_for_release_dice at round end."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.patches = 1
        d1 = create_gray_die(1)
        p0.glitched_dice = [d1]
        p0.scanned_dice = []
        p0.ready_for_release_dice = []

        class PatchOneBot(BaseBot):
            def choose_fast_patches(self, player_state, game_state, rng):
                return [0]

        p0.bot = PatchOneBot(0)
        execute_phase_3(engine)

        self.assertIn(d1, p0.scanned_dice)
        self.assertEqual(len(p0.scanned_dice), 1)
        self.assertEqual(len(p0.glitched_dice), 0)

    def test_unpatched_dice_shift_naturally_via_conveyor(self) -> None:
        """Unpatched dice shift Glitched -> Scanned -> Ready over 2 rounds with 0 patches spent."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.money = 0
        p0.patches = 0
        d1 = create_colored_die(DieColor.RED, 1)
        p0.glitched_dice = [d1]
        p0.scanned_dice = []
        p0.ready_for_release_dice = []

        # End of Round 1
        p0.in_production_dice = []
        p0.ready_for_release_dice = []
        execute_phase_3(engine)
        self.assertIn(d1, p0.scanned_dice)
        self.assertEqual(len(p0.glitched_dice), 0)
        self.assertEqual(len(p0.ready_for_release_dice), 0)

        # End of Round 2
        p0.in_production_dice = []
        p0.ready_for_release_dice = []
        execute_phase_3(engine)
        self.assertIn(d1, p0.ready_for_release_dice)
        self.assertEqual(len(p0.scanned_dice), 0)
        self.assertEqual(p0.patches, 0)

    def test_patch_token_cap_enforced_at_three(self) -> None:
        """Patches exceeding 3 🔬 are discarded at round end cleanup (uncapped in v0.28.0+)."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.bot = BaseBot(0)
        engine.state.players[1].bot = BaseBot(1)
        p0.patches = 5

        execute_phase_3(engine)

        self.assertEqual(p0.patches, 5)

    def test_fast_patch_respects_available_wrench_balance(self) -> None:
        """Fast-patching cannot exceed the player's available patch tokens."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.patches = 1

        d1 = create_gray_die(1)
        d2 = create_gray_die(2)
        p0.glitched_dice = [d1, d2]
        p0.scanned_dice = []
        p0.ready_for_release_dice = []

        class GreedPatchBot(BaseBot):
            def choose_fast_patches(self, player_state, game_state, rng):
                # Try to patch both with only 1 patch
                return [0, 1]

        p0.bot = GreedPatchBot(0)
        execute_phase_3(engine)

        # In v0.29.0, fast-patching is excised; triage shifts up to bandwidth (2) dice into scanned
        self.assertEqual(p0.patches, 1)
        self.assertEqual(len(p0.ready_for_release_dice), 0)
        self.assertEqual(len(p0.scanned_dice), 2)
        self.assertEqual(len(p0.glitched_dice), 0)

    # =========================================================================
    # Category 4: Bot Heuristics & Deprecation Verification
    # =========================================================================

    def test_base_bot_choose_debug_unlocks_returns_empty(self) -> None:
        """BaseBot.choose_debug_unlocks is deprecated and returns []."""
        bot = BaseBot(0)
        p = PlayerState(0, bot, money=5, secrets=8, patches=3)
        die = create_gray_die(1)
        die.is_locked = True
        res = bot.choose_debug_unlocks(p, [die], {}, {}, "DIRECTIVE", random.Random(42))
        self.assertEqual(res, [])

    def test_bot_subclasses_delegate_or_empty_debug_unlocks(self) -> None:
        """All bot subclasses return [] for choose_debug_unlocks."""
        subclasses = [
            AdaptiveBalancedBot(0),
            SecOpsTurtleBot(1),
            VentureGreedBot(2),
            AccelerationistBot(3),
            RecklessSaboteurBot(4),
        ]
        for bot in subclasses:
            p = PlayerState(bot.bot_id, bot, money=5, secrets=8, patches=3)
            die = create_gray_die(1)
            die.is_locked = True
            res = bot.choose_debug_unlocks(p, [die], {}, {}, "DIRECTIVE", random.Random(42))
            self.assertEqual(res, [], f"{bot.name} must return empty list for choose_debug_unlocks")

    def test_bot_fast_patch_avoids_cap_waste(self) -> None:
        """Bot fast-patches down to <= 3 patches to avoid end-of-round cap discard."""
        bot = BaseBot(0)
        p = PlayerState(0, bot, money=5, secrets=8, patches=4)
        d1 = create_colored_die(DieColor.RED, 1)
        d2 = create_gray_die(2)
        p.glitched_dice = [d1, d2]

        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        chosen = bot.choose_fast_patches(p, engine.state, random.Random(42))

        self.assertEqual(chosen, [], "Fast patching is excised in v0.29.0")

    def test_bot_fast_patch_prioritizes_colored_dice(self) -> None:
        """BaseBot.choose_fast_patches is deprecated and returns [] in v0.29.0."""
        bot = BaseBot(0)
        p = PlayerState(0, bot, money=5, secrets=8, patches=4)
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        chosen = bot.choose_fast_patches(p, engine.state, random.Random(42))
        self.assertEqual(chosen, [])

    def test_bot_full_round_wrench_conservation(self) -> None:
        """Run a full game round; verify bots spend 0 patches in Phase 1."""
        engine = GameEngine(
            config=GameConfig(num_players=4),
            bots=[
                AdaptiveBalancedBot(0),
                SecOpsTurtleBot(1),
                VentureGreedBot(2),
                AccelerationistBot(3),
            ],
            seed=42,
        )
        for p in engine.state.players:
            p.patches = 3

        execute_phase_1(engine)

        for p in engine.state.players:
            self.assertEqual(p.patches, 3, "No bot should have spent patches during Phase 1")

    # =========================================================================
    # Category 5: Web API & Controller Synchronization
    # =========================================================================

    def test_controller_debug_unlock_endpoint_deprecated(self) -> None:
        """Calling debug_unlock_die on controller raises ValueError deprecation notice."""
        ctrl = GameController()
        ctrl.new_game(num_players=2, seed=42)
        with self.assertRaises(ValueError) as ctx:
            debug_unlock_die(ctrl, 0, 0)
        self.assertIn("deprecated in v0.23.0", str(ctx.exception))

    def test_controller_capabilities_omits_can_debug_unlock(self) -> None:
        """get_action_capabilities does not expose can_debug_unlock."""
        ctrl = GameController()
        ctrl.new_game(num_players=2, seed=42)
        ctrl.roll_pool(0)

        caps = get_action_capabilities(ctrl, 0)
        self.assertNotIn("can_debug_unlock", caps)

    def test_controller_reroll_rejects_locked_die_without_prodigy(self) -> None:
        """Attempting to reroll a locked die raises ValueError for non-Prodigy."""
        ctrl = GameController()
        ctrl.new_game(num_players=2, seed=42)
        ctrl.roll_pool(0)

        # Force die 0 to locked
        ctrl.player_meta[0]["rolled_pool"][0].is_locked = True

        with self.assertRaises(ValueError) as ctx:
            perform_reroll(ctrl, 0, [0], use_prodigy_ability=False)
        self.assertIn("locked and cannot be rerolled", str(ctx.exception))

    def test_controller_auto_bot_phase1_spends_zero_patches(self) -> None:
        """auto_execute_bots_phase_1 does not decrement patches for bot players."""
        ctrl = GameController()
        ctrl.new_game(num_players=4, seed=42)

        for pid in [1, 2, 3]:
            ctrl.state.players[pid].patches = 3

        auto_execute_bots_phase_1(ctrl)

        for pid in [1, 2, 3]:
            self.assertEqual(ctrl.state.players[pid].patches, 3)


if __name__ == "__main__":
    unittest.main()
