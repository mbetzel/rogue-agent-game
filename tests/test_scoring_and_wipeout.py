"""Unit tests for Portfolio Value scoring, survivor ranking, and Total Wipeout overflow penalties."""

import unittest

from sim.bots import AdaptiveBalancedBot
from sim.config import DieColor, EndGameReason, GameConfig
from sim.engine import GameEngine, PlayerState
from sim.entities import create_colored_die, create_gray_die


class TestScoringAndWipeout(unittest.TestCase):
    def setUp(self) -> None:
        self.config = GameConfig(num_players=2)
        self.bot0 = AdaptiveBalancedBot(0)
        self.bot1 = AdaptiveBalancedBot(1)

    def test_portfolio_value_formula(self) -> None:
        """Verify 4 VP/secret, colored die VP table, 1 VP per $2, and 0 VP for gray dice."""
        player = PlayerState(
            player_id=0,
            bot=self.bot0,
            money=7,  # 7 // 2 = 3 VP
            secrets=5,  # 5 * 4 = 20 VP
            patches=1,
            ready_dice=[
                create_gray_die(1),  # 0 VP
                create_colored_die(DieColor.RED, 2),  # 3 VP
                create_colored_die(DieColor.BLUE, 3),  # 4 VP
            ],
            unpatched_dice=[
                create_colored_die(DieColor.YELLOW, 4),  # 4 VP
            ],
        )

        engine = GameEngine(self.config, [self.bot0, self.bot1], seed=42)
        engine.state.players = [player, PlayerState(1, self.bot1, 0, 0, 0, is_patient_zero=True)]

        res = engine.evaluate_end_game()
        p0_eval = [r for r in res.rankings if r["player_id"] == 0][0]

        # 20 (secrets) + (0+3+4+4=11) (dice) + 3 (cash) = 34 VP
        self.assertEqual(p0_eval["portfolio_value"], 34)

    def test_standard_ending_patient_zero_eliminated(self) -> None:
        """Patient Zero must be ranked behind all survivors, regardless of raw VP."""
        p0 = PlayerState(player_id=0, bot=self.bot0, money=10, secrets=0, patches=0, is_patient_zero=True)
        p1 = PlayerState(player_id=1, bot=self.bot1, money=2, secrets=1, patches=0, is_patient_zero=False)

        engine = GameEngine(self.config, [self.bot0, self.bot1], seed=42)
        engine.state.players = [p0, p1]

        res = engine.evaluate_end_game()
        self.assertEqual(res.winner_id, 1)
        self.assertEqual(res.rankings[0]["player_id"], 1)
        self.assertEqual(res.rankings[1]["player_id"], 0)

    def test_total_wipeout_overflow_penalties(self) -> None:
        """When all players bust simultaneously, calculate exact overflow penalties."""
        # Player 0: Money = 0, Breach = 1 (-4 VP), Unfulfilled = 0
        p0 = PlayerState(
            player_id=0,
            bot=self.bot0,
            money=0,
            secrets=-1,
            patches=0,
            is_patient_zero=True,
            debt=0,
            breach_depth=1,
            unfulfilled_destructions=0,
            ready_dice=[create_colored_die(DieColor.BLUE, 1)],  # 4 VP
        )
        # Raw VP = 0 + 4 + 0 = 4 VP. Penalty = 1 * -4 = -4. Net = 0 VP.

        # Player 1: Debt = $0, Breach = 3 (-12 VP), Unfulfilled = 1 (-3 VP)
        p1 = PlayerState(
            player_id=1,
            bot=self.bot1,
            money=4,
            secrets=-3,
            patches=0,
            is_patient_zero=True,
            debt=0,
            breach_depth=3,
            unfulfilled_destructions=1,
            ready_dice=[create_colored_die(DieColor.YELLOW, 2)],  # 4 VP
        )
        # Raw VP = max(0, -3)*4 + 4 + 2 = 6 VP. Penalty = 3 * (-4) + 1 * (-3) = -15 VP. Net = -9 VP.

        engine = GameEngine(self.config, [self.bot0, self.bot1], seed=42)
        engine.state.players = [p0, p1]

        res = engine.evaluate_end_game()
        self.assertTrue(res.is_total_wipeout)

        r0 = [r for r in res.rankings if r["player_id"] == 0][0]
        r1 = [r for r in res.rankings if r["player_id"] == 1][0]

        self.assertEqual(r0["overflow_penalties"], -4)
        self.assertEqual(r0["net_score"], 0)

        self.assertEqual(r1["overflow_penalties"], -15)
        self.assertEqual(r1["net_score"], -9)

        self.assertEqual(res.rankings[0]["player_id"], 0)
        self.assertEqual(res.rankings[1]["player_id"], 1)


if __name__ == "__main__":
    unittest.main()
