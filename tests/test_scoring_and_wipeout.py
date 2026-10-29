"""Unit tests for Portfolio Value scoring, survivor ranking, and Total Wipeout overflow penalties."""

import random
import unittest

from sim.bots import (
    AdaptiveBalancedBot,
    SecOpsTurtleBot,
    VentureGreedBot,
    AccelerationistBot,
    RecklessSaboteurBot,
)
from sim.config import DieColor, EndGameReason, GameConfig
from sim.engine import GameEngine, PlayerState
from sim.entities import (
    ArchetypeCard,
    ArchetypeCode,
    create_colored_die,
    create_gray_die,
)
from web.schemas import GameStateSerializer


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
                create_colored_die(DieColor.YELLOW, 4),  # 4 VP (unpatched scores 0 VP)
            ],
        )

        engine = GameEngine(self.config, [self.bot0, self.bot1], seed=42)
        engine.state.players = [player, PlayerState(1, self.bot1, 0, 0, 0, is_patient_zero=True)]

        res = engine.evaluate_end_game()
        p0_eval = [r for r in res.rankings if r["player_id"] == 0][0]

        # 20 (secrets) + (0+3+4=7) (ready dice) + 3 (cash) = 30 VP
        self.assertEqual(p0_eval["portfolio_value"], 30)
        self.assertEqual(p0_eval["unpatched_colored_dice_count"], 1)
        self.assertEqual(p0_eval["unpatched_dice_vp_lost"], 4)

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

    def test_unpatched_colored_dice_zero_vp_and_telemetry(self) -> None:
        """Unpatched colored dice contribute 0 VP to Portfolio Value and are tracked in telemetry."""
        player = PlayerState(
            player_id=0,
            bot=self.bot0,
            money=0,
            secrets=0,
            patches=0,
            ready_dice=[create_gray_die(1)],  # 0 VP
            unpatched_dice=[
                create_colored_die(DieColor.BLUE, 2),    # 4 VP
                create_colored_die(DieColor.YELLOW, 3),  # 4 VP
                create_colored_die(DieColor.RED, 4),     # 3 VP
                create_colored_die(DieColor.PURPLE, 5),  # 3 VP
                create_gray_die(6),                      # 0 VP
            ],
        )

        engine = GameEngine(self.config, [self.bot0, self.bot1], seed=42)
        engine.state.players = [player, PlayerState(1, self.bot1, 0, 0, 0, is_patient_zero=True)]

        res = engine.evaluate_end_game()
        p0_eval = [r for r in res.rankings if r["player_id"] == 0][0]

        # All colored dice in unpatched zone score 0 VP
        self.assertEqual(p0_eval["portfolio_value"], 0)
        # 4 colored dice: Blue, Yellow, Red, Purple (Gray die has 0 VP and is not counted)
        self.assertEqual(p0_eval["unpatched_colored_dice_count"], 4)
        # Total VP lost = 4 + 4 + 3 + 3 = 14 VP
        self.assertEqual(p0_eval["unpatched_dice_vp_lost"], 14)

    def test_web_serializer_calculates_vp_exclusively_from_ready_dice(self) -> None:
        """GameStateSerializer.calculate_player_vp calculates dice VP exclusively from ready_dice."""
        player = PlayerState(
            player_id=0,
            bot=self.bot0,
            money=4,    # 4 // 2 = 2 VP
            secrets=2,  # 2 * 4 = 8 VP
            patches=0,
            ready_dice=[create_colored_die(DieColor.BLUE, 1)],      # 4 VP
            unpatched_dice=[create_colored_die(DieColor.YELLOW, 2)], # 4 VP (ignored)
        )

        vp = GameStateSerializer.calculate_player_vp(player, self.config)
        # 8 (secrets) + 4 (ready Blue) + 2 (cash) = 14 VP
        self.assertEqual(vp, 14)

        serialized = GameStateSerializer.serialize_player(player, self.config, is_human=False, name="Bot0")
        self.assertEqual(serialized["portfolio_value"], 14)

    def test_final_round_bot_repairs_increase_portfolio_value(self) -> None:
        """In the final round, repairing a worn colored die yields higher portfolio value than hoarding cash."""
        engine = GameEngine(self.config, [self.bot0, self.bot1], seed=42)
        engine.state.is_final_round = True

        player = PlayerState(
            player_id=0,
            bot=self.bot0,
            money=4,  # $4 cash = 2 VP if hoarded
            secrets=0,
            patches=0,
            ready_dice=[create_gray_die(1)],  # 0 VP
            unpatched_dice=[create_colored_die(DieColor.YELLOW, 2)],  # 4 VP when repaired for $2
        )
        engine.state.players = [player, PlayerState(1, self.bot1, 0, 0, 0, is_patient_zero=True)]

        # Before Phase 3 execution: 0 (secrets) + 0 (dice) + 2 (cash) = 2 VP
        score_before = GameStateSerializer.calculate_player_vp(player, self.config)
        self.assertEqual(score_before, 2)

        # Bot chooses Phase 3 actions in the final round
        plan = self.bot0.take_phase3_actions(player, engine.state, engine.rng)
        self.assertTrue(len(plan.patch_actions) > 0)
        self.assertTrue(plan.patch_actions[0]["use_cash"])

        # Execute Phase 3
        engine._execute_phase_3()

        # After repair: Yellow die is now in ready_dice, money is $2 ($2 // 2 = 1 VP)
        # 0 (secrets) + 4 (ready Yellow) + 1 (cash) = 5 VP (+3 VP net gain)
        score_after = GameStateSerializer.calculate_player_vp(player, self.config)
        self.assertEqual(score_after, 5)

        res = engine.evaluate_end_game()
        p0_eval = [r for r in res.rankings if r["player_id"] == 0][0]
        self.assertEqual(p0_eval["portfolio_value"], 5)
        self.assertEqual(p0_eval["unpatched_colored_dice_count"], 0)
        self.assertEqual(p0_eval["unpatched_dice_vp_lost"], 0)

    def test_all_bots_suppress_dirty_income_in_final_round(self) -> None:
        """All 5 bot archetypes must never take Dirty Income when is_final_round is True."""
        bots = [
            AdaptiveBalancedBot(0),
            SecOpsTurtleBot(1),
            VentureGreedBot(2),
            AccelerationistBot(3),
            RecklessSaboteurBot(4),
        ]
        rng = random.Random(42)

        for bot in bots:
            engine = GameEngine(GameConfig(num_players=2), [bot, self.bot1], seed=42)
            engine.state.is_final_round = True

            # Broke with high secrets and ready dice: conditions that would normally trigger Dirty Income
            player = PlayerState(
                player_id=0,
                bot=bot,
                money=0,
                secrets=5,
                patches=0,
                ready_dice=[create_gray_die(1), create_gray_die(2)],
                unpatched_dice=[],
            )

            plan = bot.take_phase3_actions(player, engine.state, rng)
            self.assertFalse(
                plan.take_dirty_income,
                f"Bot {bot.name} took dirty income in final round!",
            )
            self.assertNotEqual(
                plan.cipher_mode,
                "DIRTY_INCOME",
                f"Bot {bot.name} selected CIPHER DIRTY_INCOME in final round!",
            )

    def test_all_bots_prioritize_cash_repairs_over_hoarding_in_final_round(self) -> None:
        """All 5 bots must spend cash to repair unpatched colored dice in the final round."""
        bots = [
            AdaptiveBalancedBot(0),
            SecOpsTurtleBot(1),
            VentureGreedBot(2),
            AccelerationistBot(3),
            RecklessSaboteurBot(4),
        ]
        rng = random.Random(42)

        for bot in bots:
            engine = GameEngine(GameConfig(num_players=2), [bot, self.bot1], seed=42)
            engine.state.is_final_round = True

            # $5 cash, 0 patches, 1 ready gray die, 2 unpatched colored dice (Yellow=4 VP, Red=3 VP)
            player = PlayerState(
                player_id=0,
                bot=bot,
                money=5,
                secrets=3,
                patches=0,
                ready_dice=[create_gray_die(1)],
                unpatched_dice=[
                    create_colored_die(DieColor.YELLOW, 2),
                    create_colored_die(DieColor.RED, 3),
                ],
            )

            plan = bot.take_phase3_actions(player, engine.state, rng)
            # The bot should plan cash repairs for high-VP colored dice rather than leaving them broken
            cash_repairs = [a for a in plan.patch_actions if a.get("use_cash")]
            self.assertTrue(
                len(cash_repairs) >= 1,
                f"Bot {bot.name} failed to prioritize cash repairs in final round (actions={plan.patch_actions})",
            )
            # Yellow (4 VP) should be repaired before or along with Red (3 VP)
            self.assertEqual(plan.patch_actions[0]["die_index"], 0)  # Yellow at index 0


if __name__ == "__main__":
    unittest.main()
