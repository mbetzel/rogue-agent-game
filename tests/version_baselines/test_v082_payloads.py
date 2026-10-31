"""Unit and integration tests for Rogue Agent Phase 12: v0.8.2 Asymmetric Version Payloads & Roadmap Paths.

Covers all 13 technical test cases from the Principal Engineer specification across Groups A-D:
Group A: Version Card Staging Payloads & 2P Scaling (Tests 1-4)
1. test_v082_asymmetric_payloads_4p: Polymorphic Worm has {GREEN: 1, BLUE: 1, BLACK: 1}; Zero-Day Override has {RED: 1, BLUE: 1, BLACK: 1}; RaaS & Corrupted Kernel retain kinetic payloads.
2. test_v082_asymmetric_payloads_2p: 2P payloads scale to {GREEN: 1, BLACK: 1} for Worm and {RED: 1, BLACK: 1} for Zero-Day; RaaS has {RED: 1, GREEN: 1}; Corrupted Kernel has {RED: 1, BLUE: 1}.
3. test_v10_payloads_scaling: v1.0 Script Kiddie and Data Scraper retain flat payloads across 2P and 4P.
4. test_payload_3p_matches_4p: All version cards return identical staging payloads for 3P and 4P (and default num_players).

Group B: Roadmap Decks Helper (Tests 5-9)
5. test_get_roadmap_deck_path_1_kinetic: Path 1 returns Script Kiddie, RaaS, Corrupted Kernel.
6. test_get_roadmap_deck_path_2_contagion: Path 2 returns Script Kiddie, Polymorphic Worm, Zero-Day Override.
7. test_get_roadmap_deck_path_3_mixed_a: Path 3 returns Script Kiddie, RaaS, Zero-Day Override (matches default baseline deck).
8. test_get_roadmap_deck_path_4_mixed_b: Path 4 returns Script Kiddie, Polymorphic Worm, Corrupted Kernel.
9. test_get_roadmap_deck_invalid_path_raises: Unknown path IDs (< 1 or > 4) raise ValueError.

Group C: Simulation Engine & Cube Tower Mechanics with Asymmetric Payloads (Tests 10-12)
10. test_engine_upgrade_polymorphic_worm_adds_black_cube: Upgrading to v2.0 Polymorphic Worm injects Black cube into Staging Cup (in both 4P and 2P).
11. test_engine_upgrade_zero_day_override_adds_black_cube: Upgrading to v3.0 Zero-Day Override injects Black cube into Staging Cup (in both 4P and 2P).
12. test_tower_drop_with_upgrade_black_cubes: CubeTower correctly tracks, drops, and holds Black corruption cubes from version upgrade payloads.

Group D: Web Controller & Serialization Compatibility (Test 13)
13. test_web_serializer_and_controller_with_asymmetric_payloads: GameStateSerializer correctly serializes Black in version payloads; GameController boots all 4 roadmap decks cleanly.
"""

from __future__ import annotations

import json
import random
import unittest
from typing import Dict, List

from sim.bots import AdaptiveBalancedBot, SecOpsTurtleBot
from sim.config import CubeColor, DieColor, GameConfig, ShieldColor, TowerMode
from sim.engine import GameEngine, PlayerState
from sim.entities import (
    VersionCard,
    get_all_version_cards,
    get_default_version_deck,
    get_roadmap_deck,
)
from sim.tower import CubeTower
from web.game_controller import GameController
from web.schemas import GameStateSerializer


def get_v082_test_cards() -> Dict[str, VersionCard]:
    """Returns the historical v0.8.2 version cards baseline for regression testing."""
    return {
        "SCRIPT_KIDDIE": VersionCard(
            version_str="v1.0",
            name="Script Kiddie",
            staging_payload={CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 1, CubeColor.BLACK: 1},
            directive_description="None.",
            directive_code="SCRIPT_KIDDIE",
        ),
        "DATA_SCRAPER": VersionCard(
            version_str="v1.0",
            name="Data Scraper",
            staging_payload={CubeColor.RED: 1, CubeColor.BLUE: 2, CubeColor.BLACK: 1},
            directive_description="Players start with +$1 extra Money.",
            directive_code="DATA_SCRAPER",
        ),
        "RAAS": VersionCard(
            version_str="v2.0",
            name="Ransomware-as-a-Service",
            staging_payload={CubeColor.RED: 2, CubeColor.GREEN: 1},
            directive_description="Encrypted Memory: Any rolled die showing Cash (+$1 or +$2) is Locked immediately.",
            directive_code="RAAS",
            staging_payload_2p={CubeColor.RED: 1, CubeColor.GREEN: 1},
        ),
        "POLYMORPHIC_WORM": VersionCard(
            version_str="v2.0",
            name="Polymorphic Worm",
            staging_payload={CubeColor.GREEN: 1, CubeColor.BLUE: 1, CubeColor.BLACK: 1},
            directive_description="Subroutine Throttling: Players receive only 1 free reroll in Phase 1 (instead of 2).",
            directive_code="POLYMORPHIC_WORM",
            staging_payload_2p={CubeColor.GREEN: 1, CubeColor.BLACK: 1},
        ),
        "ZERO_DAY_OVERRIDE": VersionCard(
            version_str="v3.0",
            name="Zero-Day Override",
            staging_payload={CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.BLACK: 1},
            directive_description="Kernel Lock: Any rolled die showing a Shield (Block 1 or Block 2) is Locked immediately.",
            directive_code="ZERO_DAY_OVERRIDE",
            staging_payload_2p={CubeColor.RED: 1, CubeColor.BLACK: 1},
        ),
        "CORRUPTED_KERNEL": VersionCard(
            version_str="v3.0",
            name="Corrupted Kernel",
            staging_payload={CubeColor.RED: 2, CubeColor.BLUE: 1},
            directive_description="If 2+ Black Cubes exit the tower this round, the Attack Color with the most exited cubes gains +2 Strength total.",
            directive_code="CORRUPTED_KERNEL",
            staging_payload_2p={CubeColor.RED: 1, CubeColor.BLUE: 1},
        ),
    }


# =====================================================================
# Group A: Version Card Staging Payloads & 2P Scaling
# =====================================================================

class TestGroupAVersionCardPayloads(unittest.TestCase):
    """Unit tests for v0.8.2 asymmetric version staging payloads and player-count scaling."""

    def setUp(self) -> None:
        self.cards = get_v082_test_cards()

    def test_v082_asymmetric_payloads_4p(self) -> None:
        """1. 4P payloads: Polymorphic Worm and Zero-Day Override contain +1 Black cube alongside attack cubes."""
        # Polymorphic Worm (v2.0): +1 Green, +1 Blue, +1 Black (total 3 cubes)
        worm = self.cards["POLYMORPHIC_WORM"]
        payload_worm = worm.get_staging_payload(4)
        self.assertEqual(payload_worm, {CubeColor.GREEN: 1, CubeColor.BLUE: 1, CubeColor.BLACK: 1})
        self.assertEqual(sum(payload_worm.values()), 3)
        self.assertEqual(payload_worm.get(CubeColor.BLACK, 0), 1)

        # Zero-Day Override (v3.0): +1 Red, +1 Blue, +1 Black (total 3 cubes)
        zero_day = self.cards["ZERO_DAY_OVERRIDE"]
        payload_zd = zero_day.get_staging_payload(4)
        self.assertEqual(payload_zd, {CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.BLACK: 1})
        self.assertEqual(sum(payload_zd.values()), 3)
        self.assertEqual(payload_zd.get(CubeColor.BLACK, 0), 1)

        # Kinetic cards: RaaS and Corrupted Kernel retain 0 Black cubes
        raas = self.cards["RAAS"]
        payload_raas = raas.get_staging_payload(4)
        self.assertEqual(payload_raas, {CubeColor.RED: 2, CubeColor.GREEN: 1})
        self.assertEqual(payload_raas.get(CubeColor.BLACK, 0), 0)

        kernel = self.cards["CORRUPTED_KERNEL"]
        payload_kernel = kernel.get_staging_payload(4)
        self.assertEqual(payload_kernel, {CubeColor.RED: 2, CubeColor.BLUE: 1})
        self.assertEqual(payload_kernel.get(CubeColor.BLACK, 0), 0)

    def test_v082_asymmetric_payloads_2p(self) -> None:
        """2. 2P payloads: Polymorphic Worm scales to {Green: 1, Black: 1}; Zero-Day scales to {Red: 1, Black: 1}."""
        # Polymorphic Worm (v2.0) 2P: +1 Green, +1 Black (total 2 cubes)
        worm = self.cards["POLYMORPHIC_WORM"]
        payload_worm_2p = worm.get_staging_payload(2)
        self.assertEqual(payload_worm_2p, {CubeColor.GREEN: 1, CubeColor.BLACK: 1})
        self.assertEqual(sum(payload_worm_2p.values()), 2)
        self.assertEqual(payload_worm_2p.get(CubeColor.BLACK, 0), 1)
        self.assertNotIn(CubeColor.BLUE, payload_worm_2p)

        # Zero-Day Override (v3.0) 2P: +1 Red, +1 Black (total 2 cubes)
        zero_day = self.cards["ZERO_DAY_OVERRIDE"]
        payload_zd_2p = zero_day.get_staging_payload(2)
        self.assertEqual(payload_zd_2p, {CubeColor.RED: 1, CubeColor.BLACK: 1})
        self.assertEqual(sum(payload_zd_2p.values()), 2)
        self.assertEqual(payload_zd_2p.get(CubeColor.BLACK, 0), 1)
        self.assertNotIn(CubeColor.BLUE, payload_zd_2p)

        # RaaS (v2.0) 2P: +1 Red, +1 Green
        raas = self.cards["RAAS"]
        self.assertEqual(raas.get_staging_payload(2), {CubeColor.RED: 1, CubeColor.GREEN: 1})

        # Corrupted Kernel (v3.0) 2P: +1 Red, +1 Blue
        kernel = self.cards["CORRUPTED_KERNEL"]
        self.assertEqual(kernel.get_staging_payload(2), {CubeColor.RED: 1, CubeColor.BLUE: 1})

    def test_v10_payloads_scaling(self) -> None:
        """3. v1.0 cards (Script Kiddie and Data Scraper) have flat payloads across 2P, 3P, and 4P."""
        kiddie = self.cards["SCRIPT_KIDDIE"]
        expected_kiddie = {CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 1, CubeColor.BLACK: 1}
        self.assertEqual(kiddie.get_staging_payload(2), expected_kiddie)
        self.assertEqual(kiddie.get_staging_payload(3), expected_kiddie)
        self.assertEqual(kiddie.get_staging_payload(4), expected_kiddie)

        scraper = self.cards["DATA_SCRAPER"]
        expected_scraper = {CubeColor.RED: 1, CubeColor.BLUE: 2, CubeColor.BLACK: 1}
        self.assertEqual(scraper.get_staging_payload(2), expected_scraper)
        self.assertEqual(scraper.get_staging_payload(3), expected_scraper)
        self.assertEqual(scraper.get_staging_payload(4), expected_scraper)

    def test_payload_3p_matches_4p(self) -> None:
        """4. All version cards return identical staging payloads for 3P and 4P."""
        for card in self.cards.values():
            self.assertEqual(card.get_staging_payload(3), card.get_staging_payload(4))
            self.assertEqual(card.get_staging_payload(), card.get_staging_payload(4))


# =====================================================================
# Group B: Roadmap Decks Helper (get_roadmap_deck)
# =====================================================================

class TestGroupBRoadmapDecks(unittest.TestCase):
    """Unit tests for get_roadmap_deck() supporting Paths 1 to 4."""

    def test_get_roadmap_deck_path_1_kinetic(self) -> None:
        """5. Path 1 (Kinetic): Returns Script Kiddie (v1.0), RaaS (v2.0), Corrupted Kernel (v3.0)."""
        deck = get_roadmap_deck(1)
        self.assertEqual(len(deck), 3)
        self.assertEqual([c.version_str for c in deck], ["v1.0", "v2.0", "v3.0"])
        self.assertEqual([c.directive_code for c in deck], ["SCRIPT_KIDDIE", "RAAS", "CORRUPTED_KERNEL"])
        self.assertEqual(deck[0].name, "Script Kiddie")
        self.assertEqual(deck[1].name, "Ransomware-as-a-Service")
        self.assertEqual(deck[2].name, "Corrupted Kernel")

    def test_get_roadmap_deck_path_2_contagion(self) -> None:
        """6. Path 2 (Contagion): Returns Script Kiddie (v1.0), Polymorphic Worm (v2.0), Zero-Day Override (v3.0)."""
        deck = get_roadmap_deck(2)
        self.assertEqual(len(deck), 3)
        self.assertEqual([c.version_str for c in deck], ["v1.0", "v2.0", "v3.0"])
        self.assertEqual([c.directive_code for c in deck], ["SCRIPT_KIDDIE", "POLYMORPHIC_WORM", "ZERO_DAY_OVERRIDE"])
        self.assertEqual(deck[0].name, "Script Kiddie")
        self.assertEqual(deck[1].name, "Polymorphic Worm")
        self.assertEqual(deck[2].name, "Zero-Day Override")

    def test_get_roadmap_deck_path_3_mixed_a(self) -> None:
        """7. Path 3 (Mixed A): Returns Script Kiddie (v1.0), RaaS (v2.0), Zero-Day Override (v3.0)."""
        deck = get_roadmap_deck(3)
        self.assertEqual(len(deck), 3)
        self.assertEqual([c.version_str for c in deck], ["v1.0", "v2.0", "v3.0"])
        self.assertEqual([c.directive_code for c in deck], ["SCRIPT_KIDDIE", "RAAS", "ZERO_DAY_OVERRIDE"])
        # Should match default baseline deck
        default_deck = get_default_version_deck()
        self.assertEqual([c.directive_code for c in deck], [c.directive_code for c in default_deck])

    def test_get_roadmap_deck_path_4_mixed_b(self) -> None:
        """8. Path 4 (Mixed B): Returns Script Kiddie (v1.0), Polymorphic Worm (v2.0), Corrupted Kernel (v3.0)."""
        deck = get_roadmap_deck(4)
        self.assertEqual(len(deck), 3)
        self.assertEqual([c.version_str for c in deck], ["v1.0", "v2.0", "v3.0"])
        self.assertEqual([c.directive_code for c in deck], ["SCRIPT_KIDDIE", "POLYMORPHIC_WORM", "CORRUPTED_KERNEL"])
        self.assertEqual(deck[0].name, "Script Kiddie")
        self.assertEqual(deck[1].name, "Polymorphic Worm")
        self.assertEqual(deck[2].name, "Corrupted Kernel")

    def test_get_roadmap_deck_invalid_path_raises(self) -> None:
        """9. Invalid roadmap path IDs raise ValueError with descriptive error message."""
        for invalid_id in [0, 5, -1, 42]:
            with self.assertRaises(ValueError) as ctx:
                get_roadmap_deck(invalid_id)
            self.assertIn(f"Unknown roadmap path_id: {invalid_id}", str(ctx.exception))


# =====================================================================
# Group C: Simulation Engine & Cube Tower Mechanics with Asymmetric Payloads
# =====================================================================

class TestGroupCEngineAndTowerMechanics(unittest.TestCase):
    """Integration tests for Version upgrade payloads entering the Staging Cup and Cube Tower."""

    def test_engine_upgrade_polymorphic_worm_adds_black_cube(self) -> None:
        """10. Version upgrade to Polymorphic Worm adds Black cube to Staging Cup in 4P and 2P."""
        # 4P Test
        cfg_4p = GameConfig(num_players=4, tower_mode=TowerMode.FLAT_BINOMIAL, tower_flat_exit_prob=1.0, corruption_track_flat_capacity=4)
        bots_4p = [AdaptiveBalancedBot(i) for i in range(4)]
        v082_cards = get_v082_test_cards()
        deck_contagion = [v082_cards["SCRIPT_KIDDIE"], v082_cards["POLYMORPHIC_WORM"], v082_cards["ZERO_DAY_OVERRIDE"]]
        engine_4p = GameEngine(config=cfg_4p, bots=bots_4p, seed=42, version_deck=deck_contagion)

        # Clear staging cup and simulate corruption advancement to trigger upgrade to v2.0
        engine_4p.state.staging_cup = {c: 0 for c in CubeColor}
        engine_4p.state.staging_cup[CubeColor.BLACK] = 4  # 4 Black cubes exiting triggers upgrade
        player_commitments = [(p, [], {}) for p in engine_4p.state.players]
        engine_4p._execute_phase_2(player_commitments)

        self.assertEqual(engine_4p.state.current_version_index, 1)
        self.assertEqual(engine_4p.state.active_version.name, "Polymorphic Worm")
        # Staging cup should have 4P payload: {GREEN: 1, BLUE: 1, BLACK: 1}
        self.assertEqual(engine_4p.state.staging_cup[CubeColor.GREEN], 1)
        self.assertEqual(engine_4p.state.staging_cup[CubeColor.BLUE], 1)
        self.assertEqual(engine_4p.state.staging_cup[CubeColor.BLACK], 1)

        # 2P Test
        cfg_2p = GameConfig(num_players=2, tower_mode=TowerMode.FLAT_BINOMIAL, tower_flat_exit_prob=1.0, corruption_track_flat_capacity=4)
        bots_2p = [AdaptiveBalancedBot(i) for i in range(2)]
        engine_2p = GameEngine(config=cfg_2p, bots=bots_2p, seed=42, version_deck=deck_contagion)

        engine_2p.state.staging_cup = {c: 0 for c in CubeColor}
        engine_2p.state.staging_cup[CubeColor.BLACK] = 4
        player_commitments_2p = [(p, [], {}) for p in engine_2p.state.players]
        engine_2p._execute_phase_2(player_commitments_2p)

        self.assertEqual(engine_2p.state.current_version_index, 1)
        self.assertEqual(engine_2p.state.active_version.name, "Polymorphic Worm")
        # Staging cup should have 2P scaled payload: {GREEN: 1, BLACK: 1} (0 Blue)
        self.assertEqual(engine_2p.state.staging_cup[CubeColor.GREEN], 1)
        self.assertEqual(engine_2p.state.staging_cup[CubeColor.BLACK], 1)
        self.assertEqual(engine_2p.state.staging_cup.get(CubeColor.BLUE, 0), 0)

    def test_engine_upgrade_zero_day_override_adds_black_cube(self) -> None:
        """11. Version upgrade to Zero-Day Override adds Black cube to Staging Cup in 4P and 2P."""
        # 4P Test
        cfg_4p = GameConfig(num_players=4, tower_mode=TowerMode.FLAT_BINOMIAL, tower_flat_exit_prob=1.0, corruption_track_flat_capacity=4)
        bots_4p = [AdaptiveBalancedBot(i) for i in range(4)]
        v082_cards = get_v082_test_cards()
        deck_contagion = [v082_cards["SCRIPT_KIDDIE"], v082_cards["POLYMORPHIC_WORM"], v082_cards["ZERO_DAY_OVERRIDE"]]
        engine_4p = GameEngine(config=cfg_4p, bots=bots_4p, seed=42, version_deck=deck_contagion)

        # Advance directly to v2.0
        engine_4p.state.current_version_index = 1
        engine_4p.state.corruption_track = 0

        # Trigger upgrade to v3.0 via 4 Black cubes drop
        engine_4p.state.staging_cup = {c: 0 for c in CubeColor}
        engine_4p.state.staging_cup[CubeColor.BLACK] = 4
        player_commitments = [(p, [], {}) for p in engine_4p.state.players]
        engine_4p._execute_phase_2(player_commitments)

        self.assertEqual(engine_4p.state.current_version_index, 2)
        self.assertEqual(engine_4p.state.active_version.name, "Zero-Day Override")
        # Staging cup should have 4P payload: {RED: 1, BLUE: 1, BLACK: 1}
        self.assertEqual(engine_4p.state.staging_cup[CubeColor.RED], 1)
        self.assertEqual(engine_4p.state.staging_cup[CubeColor.BLUE], 1)
        self.assertEqual(engine_4p.state.staging_cup[CubeColor.BLACK], 1)

        # 2P Test
        cfg_2p = GameConfig(num_players=2, tower_mode=TowerMode.FLAT_BINOMIAL, tower_flat_exit_prob=1.0, corruption_track_flat_capacity=4)
        bots_2p = [AdaptiveBalancedBot(i) for i in range(2)]
        engine_2p = GameEngine(config=cfg_2p, bots=bots_2p, seed=42, version_deck=deck_contagion)

        engine_2p.state.current_version_index = 1
        engine_2p.state.corruption_track = 0
        engine_2p.state.staging_cup = {c: 0 for c in CubeColor}
        engine_2p.state.staging_cup[CubeColor.BLACK] = 4
        player_commitments_2p = [(p, [], {}) for p in engine_2p.state.players]
        engine_2p._execute_phase_2(player_commitments_2p)

        self.assertEqual(engine_2p.state.current_version_index, 2)
        self.assertEqual(engine_2p.state.active_version.name, "Zero-Day Override")
        # Staging cup should have 2P payload: {RED: 1, BLACK: 1} (0 Blue)
        self.assertEqual(engine_2p.state.staging_cup[CubeColor.RED], 1)
        self.assertEqual(engine_2p.state.staging_cup[CubeColor.BLACK], 1)
        self.assertEqual(engine_2p.state.staging_cup.get(CubeColor.BLUE, 0), 0)

    def test_tower_drop_with_upgrade_black_cubes(self) -> None:
        """12. CubeTower correctly drops and processes Black cubes added by version upgrades."""
        cfg = GameConfig(tower_mode=TowerMode.FLAT_BINOMIAL, tower_flat_exit_prob=1.0)
        tower = CubeTower(cfg)

        staged = {CubeColor.RED: 1, CubeColor.GREEN: 1, CubeColor.BLUE: 1, CubeColor.BLACK: 2}
        rng = random.Random(42)
        exited = tower.drop(staged, rng)

        # With 100% exit probability, all staged Black cubes exit
        self.assertEqual(exited[CubeColor.BLACK], 2)
        self.assertEqual(tower.stuck_cubes[CubeColor.BLACK], 0)

        # Test with 0% exit probability (all cubes get stuck)
        cfg_stuck = GameConfig(tower_mode=TowerMode.FLAT_BINOMIAL, tower_flat_exit_prob=0.0)
        tower_stuck = CubeTower(cfg_stuck)
        exited_stuck = tower_stuck.drop(staged, rng)
        self.assertEqual(exited_stuck[CubeColor.BLACK], 0)
        self.assertEqual(tower_stuck.stuck_cubes[CubeColor.BLACK], 2)


# =====================================================================
# Group D: Web Controller & Serialization Compatibility
# =====================================================================

class TestGroupDWebSerializationAndController(unittest.TestCase):
    """Integration tests for Web API schemas and GameController with v0.8.2 payloads."""

    def test_web_serializer_and_controller_with_asymmetric_payloads(self) -> None:
        """13. GameStateSerializer exports Black in version payloads, and GameController boots all 4 roadmap paths (v0.8.2 Baseline)."""
        cards = get_v082_test_cards()

        # Verify GameStateSerializer serialization of Polymorphic Worm
        worm = cards["POLYMORPHIC_WORM"]
        ser_worm = GameStateSerializer.serialize_version_card(worm)
        self.assertEqual(ser_worm["staging_payload"]["black"], 1)
        self.assertEqual(ser_worm["staging_payload"]["green"], 1)
        self.assertEqual(ser_worm["staging_payload"]["blue"], 1)
        self.assertEqual(ser_worm["staging_payload_2p"]["black"], 1)
        self.assertEqual(ser_worm["staging_payload_2p"]["green"], 1)
        self.assertNotIn("blue", ser_worm["staging_payload_2p"])

        # Verify serialization of Zero-Day Override
        zero_day = cards["ZERO_DAY_OVERRIDE"]
        ser_zd = GameStateSerializer.serialize_version_card(zero_day)
        self.assertEqual(ser_zd["staging_payload"]["black"], 1)
        self.assertEqual(ser_zd["staging_payload"]["red"], 1)
        self.assertEqual(ser_zd["staging_payload"]["blue"], 1)
        self.assertEqual(ser_zd["staging_payload_2p"]["black"], 1)
        self.assertEqual(ser_zd["staging_payload_2p"]["red"], 1)
        self.assertNotIn("blue", ser_zd["staging_payload_2p"])

        # Verify GameController boots each of the 4 Roadmap decks cleanly
        for path_id in [1, 2, 3, 4]:
            deck = get_roadmap_deck(path_id)
            controller = GameController()
            controller.new_game(
                num_players=4,
                seed=42 + path_id,
                version_deck=deck,
            )
            state_dict = controller.get_full_state()
            # Verify JSON serializability
            json_str = json.dumps(state_dict)
            self.assertTrue(len(json_str) > 0)

            # Verify version deck in serialized state
            self.assertIn("version_deck", state_dict)
            deck_serialized = state_dict["version_deck"]
            self.assertEqual(len(deck_serialized), 3)
            self.assertEqual(deck_serialized[0]["name"], deck[0].name)
            self.assertEqual(deck_serialized[1]["name"], deck[1].name)
            self.assertEqual(deck_serialized[2]["name"], deck[2].name)


if __name__ == "__main__":
    unittest.main()
