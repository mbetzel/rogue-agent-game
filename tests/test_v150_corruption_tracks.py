"""Unit and Integration Tests for Per-Version Escalating Corruption Tracks (v0.15.0 Baseline)."""

from __future__ import annotations

import random
import unittest
from typing import Dict, List

from sim.bots.adaptive_balanced import AdaptiveBalancedBot
from sim.config import CubeColor, DieColor, GameConfig, ShieldColor
from sim.engine.core import GameEngine
from sim.engine.phase1_boot import execute_phase_1
from sim.engine.phase2_threat import execute_phase_2
from sim.entities import (
    CorruptionSpace,
    Die,
    Face,
    VersionCard,
    create_colored_die,
    create_gray_die,
    get_all_variant_cards,
    get_all_version_cards,
    get_default_variant_cards,
    get_default_version_deck,
)


class TestV150CorruptionTracks(unittest.TestCase):
    """Test suite covering per-version corruption tracks, space triggers, and lock directives."""

    def test_version_card_track_lengths_and_profiles(self) -> None:
        """Verify track lengths (4/5/6), empty staging payloads on v2/v3, and profiles."""
        for profile in ("STANDARD", "AGGRESSIVE"):
            cards = get_all_version_cards(profile=profile)
            self.assertEqual(len(cards), 6)

            v1_cards = [c for c in cards if c.version_str == "v1.0"]
            v2_cards = [c for c in cards if c.version_str == "v2.0"]
            v3_cards = [c for c in cards if c.version_str == "v3.0"]

            self.assertEqual(len(v1_cards), 2)
            self.assertEqual(len(v2_cards), 2)
            self.assertEqual(len(v3_cards), 2)

            # Check track lengths
            for c in v1_cards:
                self.assertEqual(c.track_capacity, 4)
                self.assertEqual(len(c.corruption_track), 4)
                self.assertGreater(sum(c.staging_payload.values()), 0)

            for c in v2_cards:
                self.assertEqual(c.track_capacity, 5)
                self.assertEqual(len(c.corruption_track), 5)
                self.assertEqual(c.staging_payload, {})  # Sole source of cubes is corruption track

            for c in v3_cards:
                self.assertEqual(c.track_capacity, 6)
                self.assertEqual(len(c.corruption_track), 6)
                self.assertEqual(c.staging_payload, {})  # Sole source of cubes is corruption track

        # Data Scraper starting bonus
        std_cards = {c.directive_code: c for c in get_all_version_cards("STANDARD")}
        self.assertEqual(std_cards["DATA_SCRAPER"].starting_cash_bonus, 1)

    def test_step_by_step_black_cube_resolution_and_carryover(self) -> None:
        """2 Black Cubes dropping at 3/4 on v1.0 trigger v1.0 space 4 upgrade and v2.0 space 1."""
        config = GameConfig(num_players=2, starting_money=10, starting_patches=3)
        bots = [AdaptiveBalancedBot(0), AdaptiveBalancedBot(1)]
        engine = GameEngine(config=config, bots=bots, seed=42)

        # Set v1.0 track to 3 (next cube fills space 4: Lose 1 Patch + Add 1R, 1B + Upgrade to v2.0)
        engine.state.corruption_track = 3
        self.assertEqual(engine.state.active_version.version_str, "v1.0")

        p0 = engine.state.players[0]
        p1 = engine.state.players[1]
        p0.patches = 3
        p1.patches = 3
        p0.money = 10
        p1.money = 10

        # Simulate 2 Black Cubes exiting in Phase 2
        engine.state.tower.drop = lambda cup, rng: {
            CubeColor.BLACK: 2,
            CubeColor.RED: 0,
            CubeColor.BLUE: 0,
            CubeColor.GREEN: 0,
        }

        commitments = [(p0, list(p0.ready_dice), {}), (p1, list(p1.ready_dice), {})]
        telemetry = engine._execute_phase_2(commitments)

        # Check that v1.0 Space 4 resolved (both lose 1 patch: 3 -> 2)
        self.assertEqual(p0.patches, 2)
        self.assertEqual(p1.patches, 2)

        # Check upgrade occurred: active version is now v2.0
        self.assertEqual(engine.state.active_version.version_str, "v2.0")

        # Check carryover: 2nd Black Cube advanced v2.0 to Space 1 (All lose $3: 10 -> $7)
        self.assertEqual(engine.state.corruption_track, 1)
        self.assertEqual(p0.money, 7)
        self.assertEqual(p1.money, 7)

    def test_corruption_space_penalties(self) -> None:
        """Test lose_money, lose_patches, lose_secrets, demote_dice, and return_colored_dice."""
        config = GameConfig(num_players=2, starting_money=5, starting_patches=2)
        bots = [AdaptiveBalancedBot(0), AdaptiveBalancedBot(1)]
        engine = GameEngine(config=config, bots=bots, seed=42)

        p0 = engine.state.players[0]
        p1 = engine.state.players[1]

        # Give p0 a Red colored die in ready_dice and Blue in unpatched_dice
        red_die = create_colored_die(DieColor.RED, die_id=101)
        blue_die = create_colored_die(DieColor.BLUE, die_id=102)
        p0.ready_dice.append(red_die)
        p0.unpatched_dice.append(blue_die)

        # Create a custom test version card with specific spaces
        test_track = (
            CorruptionSpace(index=1, label="Lose $4 & 1 Patch", lose_money=4, lose_patches=1),
            CorruptionSpace(index=2, label="Demote 1 die", demote_dice=1),
            CorruptionSpace(index=3, label="Return 1 Colored Die", return_colored_dice=1),
            CorruptionSpace(index=4, label="Lose 1 Secret", lose_secrets=1),
        )
        custom_v1 = VersionCard(
            version_str="v1.0",
            name="Test Threat",
            staging_payload={CubeColor.BLACK: 1},
            directive_description="Test",
            directive_code="TEST",
            corruption_track=test_track,
        )
        engine.state.version_deck[0] = custom_v1

        # Drop 1 Black Cube: Space 1 triggers (Lose $4 & 1 Patch)
        engine.state.tower.drop = lambda cup, rng: {CubeColor.BLACK: 1, CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0}
        commitments = [(p0, list(p0.ready_dice), {}), (p1, list(p1.ready_dice), {})]
        engine._execute_phase_2(commitments)

        self.assertEqual(p0.money, 1)  # 5 - 4 = $1
        self.assertEqual(p0.patches, 1)  # 2 - 1 = 1

        # Drop 1 Black Cube: Space 2 triggers (Demote 1 die)
        ready_count_before = len(p0.ready_dice)
        unpatched_count_before = len(p0.unpatched_dice)
        commitments = [(p0, list(p0.ready_dice), {}), (p1, list(p1.ready_dice), {})]
        engine._execute_phase_2(commitments)

        self.assertEqual(len(p0.ready_dice), ready_count_before - 1)
        self.assertEqual(len(p0.unpatched_dice), unpatched_count_before + 1)

        # Drop 1 Black Cube: Space 3 triggers (Return 1 Colored Die)
        market_blue_before = engine.state.market[DieColor.BLUE]
        commitments = [(p0, list(p0.ready_dice), {}), (p1, list(p1.ready_dice), {})]
        engine._execute_phase_2(commitments)

        # Unpatched Blue die should have been returned to market
        self.assertNotIn(blue_die, p0.unpatched_dice)
        self.assertEqual(engine.state.market[DieColor.BLUE], market_blue_before + 1)

        # Drop 1 Black Cube: Space 4 triggers (Lose 1 Secret)
        secrets_before = p0.secrets
        commitments = [(p0, list(p0.ready_dice), {}), (p1, list(p1.ready_dice), {})]
        engine._execute_phase_2(commitments)
        self.assertEqual(p0.secrets, secrets_before - 1)

    def test_phase1_lock_directives_lifecycle(self) -> None:
        """Lock directives queued in Phase 2 apply in next round's Phase 1, then clear."""
        config = GameConfig(num_players=2)
        bots = [AdaptiveBalancedBot(0), AdaptiveBalancedBot(1)]
        engine = GameEngine(config=config, bots=bots, seed=42)

        # Manually queue a CASH lock directive as if triggered by a Corruption Track space
        engine.state.pending_next_phase_locks.add("CASH")
        self.assertIn("CASH", engine.state.pending_next_phase_locks)
        self.assertEqual(len(engine.state.active_phase1_locks), 0)

        # Execute Phase 1: pending lock promotes to active lock
        player_commitments = engine._execute_phase_1()

        # During Phase 1 execution, any die showing Cash was locked
        # Verify that pending_next_phase_locks was cleared
        self.assertEqual(len(engine.state.pending_next_phase_locks), 0)
        # And after Phase 1 finishes, active_phase1_locks is cleared
        self.assertEqual(len(engine.state.active_phase1_locks), 0)

    def test_mode_a_vs_mode_b_cube_spawn_timing(self) -> None:
        """Mode A adds cubes to staging cup; Mode B immediately adds attack cubes to tray."""
        # --- Mode A (Default: corruption_cubes_resolve_immediately = False) ---
        cfg_a = GameConfig(num_players=2, corruption_cubes_resolve_immediately=False)
        bots_a = [AdaptiveBalancedBot(0), AdaptiveBalancedBot(1)]
        engine_a = GameEngine(config=cfg_a, bots=bots_a, seed=42)

        # Space 1 of Script Kiddie adds 1R, 1G
        engine_a.state.tower.drop = lambda cup, rng: {CubeColor.BLACK: 1, CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0}
        commitments_a = [(p, list(p.ready_dice), {}) for p in engine_a.state.players]
        telemetry_a = engine_a._execute_phase_2(commitments_a)

        # Mode A: Step 2B attack strength was 0 Red, 0 Green
        self.assertEqual(telemetry_a.attack_strengths[CubeColor.RED], 0)
        self.assertEqual(telemetry_a.attack_strengths[CubeColor.GREEN], 0)
        # But staging cup received 1 Red and 1 Green for next round
        self.assertEqual(engine_a.state.staging_cup[CubeColor.RED], 1)
        self.assertEqual(engine_a.state.staging_cup[CubeColor.GREEN], 1)

        # --- Mode B (corruption_cubes_resolve_immediately = True) ---
        cfg_b = GameConfig(num_players=2, corruption_cubes_resolve_immediately=True)
        bots_b = [AdaptiveBalancedBot(0), AdaptiveBalancedBot(1)]
        engine_b = GameEngine(config=cfg_b, bots=bots_b, seed=42)

        # Space 1 of Script Kiddie adds 1R, 1G
        engine_b.state.tower.drop = lambda cup, rng: {CubeColor.BLACK: 1, CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0}
        commitments_b = [(p, list(p.ready_dice), {}) for p in engine_b.state.players]
        telemetry_b = engine_b._execute_phase_2(commitments_b)

        # Mode B: Newly added 1R and 1G immediately joined this round's attack!
        self.assertEqual(telemetry_b.attack_strengths[CubeColor.RED], 1)
        self.assertEqual(telemetry_b.attack_strengths[CubeColor.GREEN], 1)

    def test_v3_singularity_space_6_resolution(self) -> None:
        """Filling Space 6 of v3.0 triggers Singularity and final round."""
        config = GameConfig(num_players=2)
        bots = [AdaptiveBalancedBot(0), AdaptiveBalancedBot(1)]
        engine = GameEngine(config=config, bots=bots, seed=42)

        # Fast forward to v3.0 at 5 spaces (capacity is 6)
        engine.state.current_version_index = 2
        engine.state.corruption_track = 5
        self.assertEqual(engine.state.active_version.version_str, "v3.0")
        self.assertFalse(engine.state.singularity_triggered)

        # Drop 1 Black Cube to fill Space 6
        engine.state.tower.drop = lambda cup, rng: {CubeColor.BLACK: 1, CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0}
        commitments = [(p, list(p.ready_dice), {}) for p in engine.state.players]
        telemetry = engine._execute_phase_2(commitments)

        # Singularity must be triggered!
        self.assertTrue(engine.state.singularity_triggered)
        self.assertTrue(engine.state.is_final_round)


if __name__ == "__main__":
    unittest.main()
