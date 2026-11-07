"""Tests for Phase 27: Initial Staging Cup Black Cube Zeroing (v0.20.0 Baseline)."""

import unittest
from collections import Counter

from sim.config import CubeColor, GameConfig
from sim.engine.core import GameEngine
from sim.entities import get_all_version_cards, get_default_version_deck
from sim.bots.base import BaseBot
from web.controller.core import GameController


class TestV200Rules(unittest.TestCase):
    """Verifies that v1.0 version cards stage 0 Black cubes, capping Round 1 Black drops at <= 2."""

    def test_v10_payloads_have_zero_black(self) -> None:
        """All v1.0 cards across Standard and Aggressive profiles must stage 0 Black cubes."""
        cards = get_all_version_cards()
        v1_cards = [c for c in cards if c.version_str == "v1.0"]
        self.assertGreaterEqual(len(v1_cards), 2)
        for card in v1_cards:
            self.assertEqual(
                card.staging_payload.get(CubeColor.BLACK, 0),
                0,
                f"{card.name} ({card.version_str}) should have 0 Black in staging payload",
            )

    def test_default_version_deck_v10_staging_payload(self) -> None:
        """get_default_version_deck()[0] must have 0 Black cubes."""
        deck = get_default_version_deck()
        v1 = deck[0]
        self.assertEqual(v1.version_str, "v1.0")
        self.assertEqual(v1.staging_payload.get(CubeColor.BLACK, 0), 0)

    def test_engine_setup_and_pulse_staging_cup(self) -> None:
        """Setup staging cup starts with 0 Black cubes; Phase 1 pulse brings it to exactly 1 Black cube."""
        engine = GameEngine(
            config=GameConfig.legacy_v035(num_players=4),
            bots=[BaseBot(i) for i in range(4)],
            seed=42,
        )
        # Right after setup (before Phase 1)
        self.assertEqual(engine.state.staging_cup[CubeColor.RED], 1)
        self.assertEqual(engine.state.staging_cup[CubeColor.BLUE], 1)
        self.assertEqual(engine.state.staging_cup[CubeColor.GREEN], 1)
        self.assertEqual(engine.state.staging_cup[CubeColor.BLACK], 0)

        # Execute Phase 1 (Autonomous Pulse: +1 Black for v1.0)
        engine._execute_phase_1()
        self.assertEqual(engine.state.staging_cup[CubeColor.BLACK], 1)

    def test_web_controller_initial_staging_cup(self) -> None:
        """Web GameController initializes with 1 Black cube in Staging Cup after _start_phase_1()."""
        gc = GameController()
        state = gc.new_game(num_players=4, seed=42)
        # In GameController, new_game immediately runs _start_phase_1(), which adds 1 Black cube
        self.assertEqual(state["staging_cup"]["black"], 1)
        self.assertEqual(gc.state.staging_cup[CubeColor.BLACK], 1)

    def test_round1_black_cube_drop_ceiling_monte_carlo(self) -> None:
        """Over 10,000 independent Round 1 drops, exited Black cubes must NEVER equal 3."""
        trials = 10000
        counts = Counter()

        for seed in range(trials):
            engine = GameEngine(
                config=GameConfig.legacy_v035(num_players=4),
                bots=[BaseBot(i) for i in range(4)],
                seed=seed,
            )
            # engine._prime_compiler() has run. Stuck black is either 0 or 1.
            # Staged black before pulse is 0.
            # Execute Phase 1: pulse adds 1 Black cube.
            engine._execute_phase_1()
            # Staged black is now 1.
            self.assertEqual(engine.state.staging_cup[CubeColor.BLACK], 1)

            # Drop staging cup into tower
            exited = engine.state.tower.drop(engine.state.staging_cup, engine.rng)
            black_exited = exited[CubeColor.BLACK]
            counts[black_exited] += 1

            # Strict assertion: Black exited can never exceed 2
            self.assertLessEqual(
                black_exited,
                2,
                f"Drop produced {black_exited} Black cubes on Round 1! Maximum possible is 2.",
            )

        # Verify that 0, 1, and 2 Black cubes occurred, but 3 NEVER occurred
        self.assertGreater(counts[0], 0)
        self.assertGreater(counts[1], 0)
        self.assertGreater(counts[2], 0)
        self.assertEqual(counts[3], 0)
        self.assertEqual(counts[4], 0)


if __name__ == "__main__":
    unittest.main()
