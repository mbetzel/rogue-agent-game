"""Unit and integration tests for SETEC Corruption Track Cube Distribution Recalibration (Option B).

Covers INV-RANGE-RECALIB-01, INV-CUBE-VOLUME-01, INV-PACING-CLOCK-01, and INV-PROFILE-PARITY-01
per docs/specs/spec_option_b_v2_cube_shift.md.
"""

from __future__ import annotations

import itertools
import unittest
from collections import Counter
from typing import Dict, List

from sim.config import CubeColor, GameConfig
from sim.engine.core import GameEngine
from sim.engine.phase2_compiler import resolve_corruption_space
from sim.entities import V038D_V1_STAGING_PAYLOAD, CorruptionSpace, VersionCard, get_all_version_cards


class TestOptionBV2CubeShift(unittest.TestCase):
    """Test suite verifying Option B v2.0 Corruption Track Cube Distribution Recalibration."""

    def test_v2_space2_definitions(self):
        """6.1: Verify sim/entities.py Space 2 definitions across STANDARD and AGGRESSIVE profiles."""
        for profile in ("STANDARD", "AGGRESSIVE"):
            cards: Dict[str, VersionCard] = {
                c.directive_code: c for c in get_all_version_cards(profile=profile)
            }

            # v2.0 Ransomware-as-a-Service (RaaS) Space 2
            raas = cards["RAAS"]
            raas_space2 = raas.corruption_track[1]  # index 2 is at offset 1
            self.assertEqual(raas_space2.index, 2)
            self.assertEqual(raas_space2.label, "Add 1R, 1B + Add 1K")
            self.assertEqual(
                raas_space2.add_cubes,
                {CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.BLACK: 1},
            )

            # v2.0 Polymorphic Worm Space 2
            worm = cards["POLYMORPHIC_WORM"]
            worm_space2 = worm.corruption_track[1]  # index 2 is at offset 1
            self.assertEqual(worm_space2.index, 2)
            self.assertEqual(worm_space2.label, "Add 1B, 1G + Add 1K")
            self.assertEqual(
                worm_space2.add_cubes,
                {CubeColor.BLUE: 1, CubeColor.GREEN: 1, CubeColor.BLACK: 1},
            )

    def test_cube_volume_conservation(self):
        """6.2: Verify INV-CUBE-VOLUME-01 (15/21 and 13/19) across all 8 canonical decks."""
        for profile in ("STANDARD", "AGGRESSIVE"):
            cards = {c.directive_code: c for c in get_all_version_cards(profile=profile)}
            v1_cards = [cards["SCRIPT_KIDDIE"], cards["DATA_SCRAPER"]]
            v2_cards = [cards["RAAS"], cards["POLYMORPHIC_WORM"]]
            v3_cards = [cards["ZERO_DAY_OVERRIDE"], cards["CORRUPTED_KERNEL"]]

            decks = list(itertools.product(v1_cards, v2_cards, v3_cards))
            self.assertEqual(len(decks), 8)

            for v1, v2, v3 in decks:
                counts: Counter[CubeColor] = Counter(V038D_V1_STAGING_PAYLOAD[v1.directive_code])
                # Round 1 Phase 1 Autonomous Protocol Pulse (+1 Black)
                counts[CubeColor.BLACK] += 1

                for card in (v1, v2, v3):
                    for space in card.corruption_track:
                        counts.update(space.add_cubes)

                attack_cubes = (
                    counts[CubeColor.RED]
                    + counts[CubeColor.BLUE]
                    + counts[CubeColor.GREEN]
                )
                total_cubes = attack_cubes + counts[CubeColor.BLACK]

                if v3.directive_code == "ZERO_DAY_OVERRIDE":
                    self.assertEqual(attack_cubes, 15)
                    self.assertEqual(total_cubes, 21)
                elif v3.directive_code == "CORRUPTED_KERNEL":
                    self.assertEqual(attack_cubes, 13)
                    self.assertEqual(total_cubes, 19)
                else:
                    self.fail(f"Unexpected v3 card: {v3.directive_code}")

                # Black cubes strictly conserved at 6
                self.assertEqual(counts[CubeColor.BLACK], 6)

    def test_cube_range_bounds(self):
        """6.3: Verify INV-RANGE-RECALIB-01 (G in [2,5], B in [3,6], R in [4,8], K=6) across all 8 decks."""
        for profile in ("STANDARD", "AGGRESSIVE"):
            cards = {c.directive_code: c for c in get_all_version_cards(profile=profile)}
            v1_cards = [cards["SCRIPT_KIDDIE"], cards["DATA_SCRAPER"]]
            v2_cards = [cards["RAAS"], cards["POLYMORPHIC_WORM"]]
            v3_cards = [cards["ZERO_DAY_OVERRIDE"], cards["CORRUPTED_KERNEL"]]

            red_counts: List[int] = []
            blue_counts: List[int] = []
            green_counts: List[int] = []
            black_counts: List[int] = []

            for v1, v2, v3 in itertools.product(v1_cards, v2_cards, v3_cards):
                counts: Counter[CubeColor] = Counter(V038D_V1_STAGING_PAYLOAD[v1.directive_code])
                counts[CubeColor.BLACK] += 1  # Pulse
                for card in (v1, v2, v3):
                    for space in card.corruption_track:
                        counts.update(space.add_cubes)

                red_counts.append(counts[CubeColor.RED])
                blue_counts.append(counts[CubeColor.BLUE])
                green_counts.append(counts[CubeColor.GREEN])
                black_counts.append(counts[CubeColor.BLACK])

                # Deck 7 explicit check: Data Scraper + Polymorphic Worm + Zero-Day Override
                if (
                    v1.directive_code == "DATA_SCRAPER"
                    and v2.directive_code == "POLYMORPHIC_WORM"
                    and v3.directive_code == "ZERO_DAY_OVERRIDE"
                ):
                    self.assertEqual(counts[CubeColor.GREEN], 5)
                    self.assertEqual(counts[CubeColor.BLUE], 6)
                    self.assertEqual(counts[CubeColor.RED], 4)
                    self.assertEqual(counts[CubeColor.BLACK], 6)

            self.assertEqual((min(green_counts), max(green_counts)), (2, 5))
            self.assertEqual((min(blue_counts), max(blue_counts)), (3, 6))
            self.assertEqual((min(red_counts), max(red_counts)), (4, 8))
            self.assertTrue(all(k == 6 for k in black_counts))

    def test_phase2_staging_cup_injection(self):
        """6.4: Verify operational execution of Space 2 cube injection during Phase 2 compiler resolution."""
        cards = {c.directive_code: c for c in get_all_version_cards(profile="STANDARD")}
        raas_space2 = cards["RAAS"].corruption_track[1]
        worm_space2 = cards["POLYMORPHIC_WORM"].corruption_track[1]

        # --- Mode A: corruption_cubes_resolve_immediately = False ---
        cfg_a = GameConfig.v040(num_players=2, corruption_cubes_resolve_immediately=False)
        engine_a = GameEngine(cfg_a, seed=0)

        # Baseline snapshot before RaaS Space 2
        before_raas = dict(engine_a.state.staging_cup)
        resolve_corruption_space(
            engine=engine_a,
            space=raas_space2,
            player_commitments={},
            exited_cubes={},
        )
        after_raas = dict(engine_a.state.staging_cup)

        self.assertEqual(after_raas.get(CubeColor.RED, 0) - before_raas.get(CubeColor.RED, 0), 1)
        self.assertEqual(after_raas.get(CubeColor.BLUE, 0) - before_raas.get(CubeColor.BLUE, 0), 1)
        self.assertEqual(after_raas.get(CubeColor.BLACK, 0) - before_raas.get(CubeColor.BLACK, 0), 1)
        self.assertEqual(after_raas.get(CubeColor.GREEN, 0) - before_raas.get(CubeColor.GREEN, 0), 0)

        # Baseline snapshot before Worm Space 2
        before_worm = dict(engine_a.state.staging_cup)
        resolve_corruption_space(
            engine=engine_a,
            space=worm_space2,
            player_commitments={},
            exited_cubes={},
        )
        after_worm = dict(engine_a.state.staging_cup)

        self.assertEqual(after_worm.get(CubeColor.BLUE, 0) - before_worm.get(CubeColor.BLUE, 0), 1)
        self.assertEqual(after_worm.get(CubeColor.GREEN, 0) - before_worm.get(CubeColor.GREEN, 0), 1)
        self.assertEqual(after_worm.get(CubeColor.BLACK, 0) - before_worm.get(CubeColor.BLACK, 0), 1)
        self.assertEqual(after_worm.get(CubeColor.RED, 0) - before_worm.get(CubeColor.RED, 0), 0)

        # --- Mode B: corruption_cubes_resolve_immediately = True ---
        cfg_b = GameConfig.v040(num_players=2, corruption_cubes_resolve_immediately=True)
        engine_b = GameEngine(cfg_b, seed=0)

        # Test RaaS Space 2 in Mode B
        exited_b_raas: Dict[CubeColor, int] = {}
        before_staging_b = dict(engine_b.state.staging_cup)
        resolve_corruption_space(
            engine=engine_b,
            space=raas_space2,
            player_commitments={},
            exited_cubes=exited_b_raas,
        )
        self.assertEqual(exited_b_raas.get(CubeColor.RED, 0), 1)
        self.assertEqual(exited_b_raas.get(CubeColor.BLUE, 0), 1)
        self.assertEqual(exited_b_raas.get(CubeColor.GREEN, 0), 0)
        self.assertEqual(
            engine_b.state.staging_cup.get(CubeColor.BLACK, 0) - before_staging_b.get(CubeColor.BLACK, 0),
            1,
        )

        # Test Worm Space 2 in Mode B
        exited_b_worm: Dict[CubeColor, int] = {}
        before_staging_b_worm = dict(engine_b.state.staging_cup)
        resolve_corruption_space(
            engine=engine_b,
            space=worm_space2,
            player_commitments={},
            exited_cubes=exited_b_worm,
        )
        self.assertEqual(exited_b_worm.get(CubeColor.BLUE, 0), 1)
        self.assertEqual(exited_b_worm.get(CubeColor.GREEN, 0), 1)
        self.assertEqual(exited_b_worm.get(CubeColor.RED, 0), 0)
        self.assertEqual(
            engine_b.state.staging_cup.get(CubeColor.BLACK, 0) - before_staging_b_worm.get(CubeColor.BLACK, 0),
            1,
        )


if __name__ == "__main__":
    unittest.main()
