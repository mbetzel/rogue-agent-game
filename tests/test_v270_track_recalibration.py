"""Unit tests for Phase 34: Per-Version Corruption Track Recalibration (v0.27.0).

Verifies invariants:
- INV-TRACK-CALIB-01: Standard Profile Track Definitions
- INV-TRACK-AGGR-01: Aggressive Profile Consistency
- INV-TRACK-CAPACITY-01: Pacing Invariance (4, 5, 6 spaces)
- INV-STEP2A-DEDUCTION-01: Sequential Step 2A Threat Resolution
"""

from __future__ import annotations

import unittest
from sim.config import CubeColor, DieColor, GameConfig, ShieldColor
from sim.entities import get_all_version_cards
from sim.engine.core import GameEngine
from sim.engine.phase2_threat import resolve_corruption_space
from sim.bots import AdaptiveBalancedBot


class TestV270CorruptionTrackRecalibration(unittest.TestCase):
    """Test suite verifying v0.27.0 track recalibration invariants."""

    def test_standard_raas_space_1(self) -> None:
        """INV-TRACK-CALIB-01: v2.0 RaaS Space 1 deals $2 cash loss (recalibrated from $1)."""
        standard_cards = {c.directive_code: c for c in get_all_version_cards("STANDARD", player_specific=False)}
        raas = standard_cards["RAAS"]
        sp1 = raas.corruption_track[0]
        self.assertEqual(sp1.index, 1)
        self.assertEqual(sp1.label, "All lose $2")
        self.assertEqual(sp1.lose_money, 2)
        self.assertEqual(sp1.lose_patches, 0)
        self.assertEqual(sp1.add_cubes, {})

    def test_standard_raas_space_4(self) -> None:
        """INV-TRACK-CALIB-01: v2.0 RaaS Space 4 deals $3 & 1 research + 1K (recalibrated from $2)."""
        standard_cards = {c.directive_code: c for c in get_all_version_cards("STANDARD", player_specific=False)}
        raas = standard_cards["RAAS"]
        sp4 = raas.corruption_track[3]
        self.assertEqual(sp4.index, 4)
        self.assertEqual(sp4.label, "Lose $3 & 1 🔬 + Add 1K")
        self.assertEqual(sp4.lose_money, 3)
        self.assertEqual(sp4.lose_patches, 1)
        self.assertEqual(sp4.add_cubes, {CubeColor.BLACK: 1})

    def test_standard_zeroday_space_2(self) -> None:
        """INV-TRACK-CALIB-01: v3.0 Zero-Day Space 2 deals $3 & 1 research + 1K (recalibrated from $2)."""
        standard_cards = {c.directive_code: c for c in get_all_version_cards("STANDARD", player_specific=False)}
        zd = standard_cards["ZERO_DAY_OVERRIDE"]
        sp2 = zd.corruption_track[1]
        self.assertEqual(sp2.index, 2)
        self.assertEqual(sp2.label, "Lose $3 & 1 🔬 + Add 1K")
        self.assertEqual(sp2.lose_money, 3)
        self.assertEqual(sp2.lose_patches, 1)
        self.assertEqual(sp2.add_cubes, {CubeColor.BLACK: 1})

    def test_standard_kernel_space_2(self) -> None:
        """INV-TRACK-CALIB-01: v3.0 Corrupted Kernel Space 2 deals $3 & 1 research + 1K (recalibrated from $2)."""
        standard_cards = {c.directive_code: c for c in get_all_version_cards("STANDARD", player_specific=False)}
        ck = standard_cards["CORRUPTED_KERNEL"]
        sp2 = ck.corruption_track[1]
        self.assertEqual(sp2.index, 2)
        self.assertEqual(sp2.label, "Lose $3 & 1 🔬 + Add 1K")
        self.assertEqual(sp2.lose_money, 3)
        self.assertEqual(sp2.lose_patches, 1)
        self.assertEqual(sp2.add_cubes, {CubeColor.BLACK: 1})

    def test_aggressive_profile_parity(self) -> None:
        """INV-TRACK-AGGR-01: Aggressive profile maintains parity with calibrated thresholds."""
        aggr_cards = {c.directive_code: c for c in get_all_version_cards("AGGRESSIVE", player_specific=False)}
        raas = aggr_cards["RAAS"]
        self.assertEqual(raas.corruption_track[0].lose_money, 2)
        self.assertEqual(raas.corruption_track[3].lose_money, 3)
        self.assertEqual(raas.corruption_track[3].lose_patches, 1)

        zd = aggr_cards["ZERO_DAY_OVERRIDE"]
        self.assertEqual(zd.corruption_track[1].lose_money, 3)
        self.assertEqual(zd.corruption_track[1].lose_patches, 1)

        ck = aggr_cards["CORRUPTED_KERNEL"]
        self.assertEqual(ck.corruption_track[1].lose_money, 3)
        self.assertEqual(ck.corruption_track[1].lose_patches, 1)

    def test_track_capacity_invariance(self) -> None:
        """INV-TRACK-CAPACITY-01: Track capacities strictly 4 (v1.0), 5 (v2.0), 6 (v3.0)."""
        for profile in ["STANDARD", "AGGRESSIVE"]:
            cards = get_all_version_cards(profile)
            for c in cards:
                if c.version_str == "v1.0":
                    self.assertEqual(len(c.corruption_track), 4)
                elif c.version_str == "v2.0":
                    self.assertEqual(len(c.corruption_track), 5)
                elif c.version_str == "v3.0":
                    self.assertEqual(len(c.corruption_track), 6)

    def test_step2a_raas_space_1_execution(self) -> None:
        """INV-STEP2A-DEDUCTION-01: Triggering RaaS Space 1 in Step 2A deducts exactly $2."""
        cfg = GameConfig.legacy_v035(num_players=2, starting_money=5)
        bots = [AdaptiveBalancedBot(0), AdaptiveBalancedBot(1)]
        engine = GameEngine(cfg, bots=bots, seed=42)

        standard_cards = {c.directive_code: c for c in get_all_version_cards("STANDARD", player_specific=False)}
        raas = standard_cards["RAAS"]
        sp1 = raas.corruption_track[0]

        p0 = engine.state.players[0]
        p1 = engine.state.players[1]
        p0.money = 5
        p1.money = 4

        exited = {CubeColor.BLACK: 1}
        commitments = [(p0, [], {}), (p1, [], {})]
        resolve_corruption_space(engine, sp1, commitments, exited)

        self.assertEqual(p0.money, 3)
        self.assertEqual(p1.money, 2)

    def test_step2a_zeroday_space_2_execution(self) -> None:
        """INV-STEP2A-DEDUCTION-01: Triggering Zero-Day Space 2 deducts $3 and 1 patch."""
        cfg = GameConfig.legacy_v035(num_players=2, starting_money=5)
        bots = [AdaptiveBalancedBot(0), AdaptiveBalancedBot(1)]
        engine = GameEngine(cfg, bots=bots, seed=42)

        standard_cards = {c.directive_code: c for c in get_all_version_cards("STANDARD", player_specific=False)}
        zd = standard_cards["ZERO_DAY_OVERRIDE"]
        sp2 = zd.corruption_track[1]

        p0 = engine.state.players[0]
        p1 = engine.state.players[1]
        p0.money = 6
        p0.patches = 2
        p1.money = 2
        p1.patches = 0

        exited = {CubeColor.BLACK: 1}
        commitments = [(p0, [], {}), (p1, [], {})]
        resolve_corruption_space(engine, sp2, commitments, exited)

        # p0: $6 - $3 = $3, 2 - 1 = 1 patch
        self.assertEqual(p0.money, 3)
        self.assertEqual(p0.patches, 1)

        # p1: $2 - $3 = floored at $0, 0 - 1 = floored at 0 patches
        self.assertEqual(p1.money, 0)
        self.assertEqual(p1.patches, 0)

    def test_floor_at_zero_no_secret_leak(self) -> None:
        """INV-STEP2A-DEDUCTION-01: Unpaid track cash loss does NOT leak into secrets."""
        cfg = GameConfig.legacy_v035(num_players=2, starting_money=5)
        bots = [AdaptiveBalancedBot(0), AdaptiveBalancedBot(1)]
        engine = GameEngine(cfg, bots=bots, seed=42)

        standard_cards = {c.directive_code: c for c in get_all_version_cards("STANDARD", player_specific=False)}
        zd = standard_cards["ZERO_DAY_OVERRIDE"]
        sp2 = zd.corruption_track[1]

        p0 = engine.state.players[0]
        p0.money = 0
        p0.patches = 0
        p0.secrets = 8

        exited = {CubeColor.BLACK: 1}
        commitments = [(p0, [], {})]
        resolve_corruption_space(engine, sp2, commitments, exited)

        self.assertEqual(p0.money, 0)
        self.assertEqual(p0.patches, 0)
        self.assertEqual(p0.secrets, 8)  # Track cash loss does NOT leak into secrets


if __name__ == "__main__":
    unittest.main()
