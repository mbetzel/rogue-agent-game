"""Unit tests verifying deterministic replayability with identical seeds."""

import unittest

from sim.bots import AccelerationistBot, AdaptiveBalancedBot, SecOpsTurtleBot, VentureGreedBot
from sim.config import GameConfig
from sim.engine import GameEngine


class TestDeterminism(unittest.TestCase):
    def test_reproducible_game_run(self) -> None:
        cfg = GameConfig(num_players=4)

        def make_bots():
            return [
                AdaptiveBalancedBot(0),
                SecOpsTurtleBot(1),
                VentureGreedBot(2),
                AccelerationistBot(3),
            ]

        seed = 42

        engine1 = GameEngine(cfg, make_bots(), seed=seed)
        result1 = engine1.run_game()

        engine2 = GameEngine(cfg, make_bots(), seed=seed)
        result2 = engine2.run_game()

        self.assertEqual(result1.total_rounds, result2.total_rounds)
        self.assertEqual(result1.end_reason, result2.end_reason)
        self.assertEqual(result1.winner_id, result2.winner_id)
        self.assertEqual(result1.is_total_wipeout, result2.is_total_wipeout)
        self.assertEqual(result1.singularity_reached, result2.singularity_reached)

        # Check exact player stats
        self.assertEqual(len(result1.rankings), len(result2.rankings))
        for r1, r2 in zip(result1.rankings, result2.rankings):
            self.assertEqual(r1["player_id"], r2["player_id"])
            self.assertEqual(r1["portfolio_value"], r2["portfolio_value"])
            self.assertEqual(r1["net_score"], r2["net_score"])
            self.assertEqual(r1["money"], r2["money"])
            self.assertEqual(r1["secrets"], r2["secrets"])
            self.assertEqual(r1["ready_dice_count"], r2["ready_dice_count"])
            self.assertEqual(r1["unpatched_dice_count"], r2["unpatched_dice_count"])

        # Check telemetry length
        self.assertEqual(len(result1.telemetry_history), len(result2.telemetry_history))
        for t1, t2 in zip(result1.telemetry_history, result2.telemetry_history):
            self.assertEqual(t1.staged_cubes, t2.staged_cubes)
            self.assertEqual(t1.exited_cubes, t2.exited_cubes)
            self.assertEqual(t1.attack_strengths, t2.attack_strengths)

    def test_all_five_bot_archetypes_integration(self) -> None:
        """Integration test executing matches across all 5 bot archetypes without exceptions."""
        from sim.bots import RecklessSaboteurBot

        # Test Pod 1: 4 players (Balanced, Turtle, Greed, Saboteur)
        bots_pod1 = [
            AdaptiveBalancedBot(0),
            SecOpsTurtleBot(1),
            VentureGreedBot(2),
            RecklessSaboteurBot(3),
        ]
        engine1 = GameEngine(GameConfig(num_players=4), bots_pod1, seed=101)
        result1 = engine1.run_game()

        self.assertGreater(result1.total_rounds, 0)
        self.assertEqual(len(result1.rankings), 4)
        for r in result1.rankings:
            self.assertIn("rank", r)
            self.assertIn("portfolio_value", r)

        # Test Pod 2: 4 players (Balanced, Turtle, Accel, Saboteur)
        bots_pod2 = [
            AdaptiveBalancedBot(0),
            SecOpsTurtleBot(1),
            AccelerationistBot(2),
            RecklessSaboteurBot(3),
        ]
        engine2 = GameEngine(GameConfig(num_players=4), bots_pod2, seed=202)
        result2 = engine2.run_game()

        self.assertGreater(result2.total_rounds, 0)
        self.assertEqual(len(result2.rankings), 4)


if __name__ == "__main__":
    unittest.main()
