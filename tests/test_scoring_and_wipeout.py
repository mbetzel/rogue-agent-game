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
        """Verify 1 VP/secret, 0 VP for colored dice, 0 VP for cash, and 0 VP for gray dice."""
        player = PlayerState(
            player_id=0,
            bot=self.bot0,
            money=7,  # Cash is Tiebreaker #1, 0 direct VP
            secrets=5,  # 5 * 1 = 5 VP
            patches=1,
            ready_dice=[
                create_gray_die(1),  # 0 VP
                create_colored_die(DieColor.RED, 2),  # 0 VP
                create_colored_die(DieColor.BLUE, 3),  # 0 VP
            ],
            unpatched_dice=[
                create_colored_die(DieColor.YELLOW, 4),  # 0 VP
            ],
        )

        engine = GameEngine(self.config, [self.bot0, self.bot1], seed=42)
        engine.state.players = [player, PlayerState(1, self.bot1, 0, 0, 0, is_patient_zero=True)]

        res = engine.evaluate_end_game()
        p0_eval = [r for r in res.rankings if r["player_id"] == 0][0]

        # 5 (secrets) + 0 (dice) + 0 (cash) = 5 VP
        self.assertEqual(p0_eval["portfolio_value"], 5)
        self.assertEqual(p0_eval["unpatched_colored_dice_count"], 1)
        self.assertEqual(p0_eval["unpatched_dice_vp_lost"], 0)

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
        """When all players bust simultaneously, calculate exact overflow penalties with 0 fictitious VP added."""
        # Player 0: Money = 0, Breach = 1 (-1 penalty), Unfulfilled = 0
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
            ready_dice=[create_colored_die(DieColor.BLUE, 1)],  # 0 VP
        )
        # Net score = -1 (overflow penalties only)

        # Player 1: Money = 4, Breach = 3 (-3 penalty), Unfulfilled destructions excised in v0.31.0
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
            ready_dice=[create_colored_die(DieColor.YELLOW, 2)],  # 0 VP
        )
        # Net score = -3 (overflow penalties only)

        # v0.34: Net Wipeout Score ranking is legacy-only (OQ-4); pin to the v0.33 sequence.
        engine = GameEngine(GameConfig.legacy_v033(num_players=2), [self.bot0, self.bot1], seed=42)
        engine.state.players = [p0, p1]

        res = engine.evaluate_end_game()
        self.assertTrue(res.is_total_wipeout)

        r0 = [r for r in res.rankings if r["player_id"] == 0][0]
        r1 = [r for r in res.rankings if r["player_id"] == 1][0]

        self.assertEqual(r0["overflow_penalties"], -1)
        self.assertEqual(r0["net_score"], -1)

        self.assertEqual(r1["overflow_penalties"], -3)
        self.assertEqual(r1["net_score"], -3)

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
                create_colored_die(DieColor.BLUE, 2),    # 0 VP
                create_colored_die(DieColor.YELLOW, 3),  # 0 VP
                create_colored_die(DieColor.RED, 4),     # 0 VP
                create_colored_die(DieColor.PURPLE, 5),  # 0 VP
                create_gray_die(6),                      # 0 VP
            ],
        )

        engine = GameEngine(self.config, [self.bot0, self.bot1], seed=42)
        engine.state.players = [player, PlayerState(1, self.bot1, 0, 0, 0, is_patient_zero=True)]

        res = engine.evaluate_end_game()
        p0_eval = [r for r in res.rankings if r["player_id"] == 0][0]

        # All colored dice in unpatched zone score 0 VP
        self.assertEqual(p0_eval["portfolio_value"], 0)
        # 4 colored dice: Blue, Yellow, Red, Purple (Gray die is not counted)
        self.assertEqual(p0_eval["unpatched_colored_dice_count"], 4)
        # Total VP lost = 0 (all dice have 0 VP)
        self.assertEqual(p0_eval["unpatched_dice_vp_lost"], 0)

    def test_web_serializer_calculates_vp_as_secrets(self) -> None:
        """GameStateSerializer.calculate_player_vp calculates VP strictly from player secrets."""
        player = PlayerState(
            player_id=0,
            bot=self.bot0,
            money=4,
            secrets=2,
            patches=0,
            ready_dice=[create_colored_die(DieColor.BLUE, 1)],
            unpatched_dice=[create_colored_die(DieColor.YELLOW, 2)],
        )

        vp = GameStateSerializer.calculate_player_vp(player, self.config)
        self.assertEqual(vp, 2)

        serialized = GameStateSerializer.serialize_player(player, self.config, is_human=False, name="Bot0")
        self.assertEqual(serialized["portfolio_value"], 2)

    def test_final_round_bot_repairs_with_patches_preserving_cash(self) -> None:
        """In v0.29.0 fast-patching is excised; cash and research tokens remain intact."""
        engine = GameEngine(self.config, [self.bot0, self.bot1], seed=42)
        engine.state.is_final_round = True

        player = PlayerState(
            player_id=0,
            bot=self.bot0,
            money=4,  # $4 cash preserved for Tiebreaker #1
            secrets=5,
            patches=1,
            ready_dice=[create_gray_die(1)],
            unpatched_dice=[create_colored_die(DieColor.YELLOW, 2)],
        )
        engine.state.players = [player, PlayerState(1, self.bot1, 0, 0, 0, is_patient_zero=True)]

        # Before Phase 3 execution: 5 secrets
        score_before = GameStateSerializer.calculate_player_vp(player, self.config)
        self.assertEqual(score_before, 5)

        # Execute Phase 3
        engine._execute_phase_3()

        # Cash remains intact ($4), fast-patching excised so patches remain intact
        self.assertEqual(player.money, 4)
        self.assertEqual(player.patches, 1)

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

    def test_all_bots_preserve_cash_in_final_round(self) -> None:
        """All 5 bots must never spend cash on repairs or market purchases in the final round (preserving Tiebreaker #1)."""
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

            # $5 cash, 0 patches, 1 ready gray die, 2 unpatched colored dice
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
            # The bot must NOT plan cash repairs in the final round
            cash_repairs = [a for a in plan.patch_actions if a.get("use_cash")]
            self.assertEqual(
                len(cash_repairs),
                0,
                f"Bot {bot.name} spent cash on repairs in final round: {plan.patch_actions}",
            )
            # The bot must NOT buy market dice in the final round
            self.assertEqual(
                len(plan.market_purchases),
                0,
                f"Bot {bot.name} bought market dice in final round: {plan.market_purchases}",
            )

    def test_pure_corporate_secrets_victory_scoring(self) -> None:
        """Surviving corporations are ranked strictly by Corporate Secrets; cash and colored dice do not inflate score."""
        engine = GameEngine(self.config, [self.bot0, self.bot1], seed=42)
        # P0 has 10 secrets, $2, 0 colored dice
        p0 = PlayerState(
            player_id=0,
            bot=self.bot0,
            money=2,
            secrets=10,
            patches=0,
            ready_dice=[create_gray_die(1)],
        )
        # P1 has 8 secrets, $100, 10 ready colored dice
        p1 = PlayerState(
            player_id=1,
            bot=self.bot1,
            money=100,
            secrets=8,
            patches=0,
            ready_dice=[create_colored_die(DieColor.YELLOW, i) for i in range(10, 20)],
        )
        engine.state.players = [p0, p1]

        res = engine.evaluate_end_game()
        self.assertEqual(res.winner_id, 0)
        self.assertEqual(res.rankings[0]["player_id"], 0)
        self.assertEqual(res.rankings[0]["portfolio_value"], 10)
        self.assertEqual(res.rankings[1]["player_id"], 1)
        self.assertEqual(res.rankings[1]["portfolio_value"], 8)

    def test_elimination_of_fictitious_wipeout_bonuses(self) -> None:
        """In total wipeout, net_score strictly equals overflow penalties (no positive bonuses added)."""
        engine = GameEngine(self.config, [self.bot0, self.bot1], seed=42)
        p0 = PlayerState(
            player_id=0,
            bot=self.bot0,
            money=50,
            secrets=-1,
            patches=3,
            is_patient_zero=True,
            breach_depth=1,
            unfulfilled_destructions=2,
            ready_dice=[create_colored_die(DieColor.YELLOW, i) for i in range(10, 15)],
        )
        p1 = PlayerState(
            player_id=1,
            bot=self.bot1,
            money=0,
            secrets=-2,
            patches=0,
            is_patient_zero=True,
            breach_depth=2,
            unfulfilled_destructions=0,
            ready_dice=[],
        )
        engine.state.players = [p0, p1]

        res = engine.evaluate_end_game()
        self.assertTrue(res.is_total_wipeout)

        r0 = [r for r in res.rankings if r["player_id"] == 0][0]
        r1 = [r for r in res.rankings if r["player_id"] == 1][0]

        # P0: breach depth 1 (-1), unfulfilled destructions excised in v0.31.0 = -1
        self.assertEqual(r0["overflow_penalties"], -1)
        self.assertEqual(r0["net_score"], -1)  # Absolutely no dice or cash bonuses added!

        # P1: breach depth 2 (-2) = -2
        self.assertEqual(r1["overflow_penalties"], -2)
        self.assertEqual(r1["net_score"], -2)

        # P0 has higher (less negative) net score (-1 vs -2), so P0 ranks first
        self.assertEqual(res.rankings[0]["player_id"], 0)
        self.assertEqual(res.rankings[1]["player_id"], 1)

    def test_total_wipeout_hierarchical_tiebreakers(self) -> None:
        """In total wipeout with tied net_score, differentiate by secrets, unfulfilled_destructions, money, colored dice, patches, unpatched."""
        cfg_4p = GameConfig(num_players=4)
        bots = [AdaptiveBalancedBot(i) for i in range(4)]
        engine = GameEngine(cfg_4p, bots, seed=42)

        # All players tied at net_score = -2 and secrets = -2
        # P0: money = $10, 0 colored dice
        p0 = PlayerState(0, bots[0], money=10, secrets=-2, patches=0, is_patient_zero=True, breach_depth=2, unfulfilled_destructions=0)
        # P1: money = $5, 2 colored dice
        p1 = PlayerState(1, bots[1], money=5, secrets=-2, patches=0, is_patient_zero=True, breach_depth=2, unfulfilled_destructions=0,
                         ready_dice=[create_colored_die(DieColor.RED, 1), create_colored_die(DieColor.BLUE, 2)])
        # P2: money = $5, 1 colored die
        p2 = PlayerState(2, bots[2], money=5, secrets=-2, patches=0, is_patient_zero=True, breach_depth=2, unfulfilled_destructions=0,
                         ready_dice=[create_colored_die(DieColor.RED, 3)])
        # P3: money = $5, 1 colored die, 2 patches
        p3 = PlayerState(3, bots[3], money=5, secrets=-2, patches=2, is_patient_zero=True, breach_depth=2, unfulfilled_destructions=0,
                         ready_dice=[create_colored_die(DieColor.RED, 4)])

        engine.state.players = [p0, p1, p2, p3]
        res = engine.evaluate_end_game()

        # Tiebreaker 1 (Money): P0 ($10) beats P1/P2/P3 ($5) -> Rank 1
        self.assertEqual(res.rankings[0]["player_id"], 0)
        # Tiebreaker 2 (Ready Colored Dice): P1 (2 colored dice) beats P2/P3 (1 colored die) -> Rank 2
        self.assertEqual(res.rankings[1]["player_id"], 1)
        # Tiebreaker 3 (Patches): P3 (2 patches) beats P2 (0 patches) -> Rank 3
        self.assertEqual(res.rankings[2]["player_id"], 3)
        self.assertEqual(res.rankings[3]["player_id"], 2)

    def test_final_round_bot_preserves_cash_and_uses_patches_only(self) -> None:
        """Bot in final round uses patch tokens on colored dice first, avoids cash repairs/buys, and uses B2/Y1 secret conversions."""
        engine = GameEngine(self.config, [self.bot0, self.bot1], seed=42)
        engine.state.is_final_round = True

        player = PlayerState(
            player_id=0,
            bot=self.bot0,
            money=10,
            secrets=5,
            patches=1,
            ready_dice=[create_gray_die(1)],
            unpatched_dice=[
                create_gray_die(2),
                create_colored_die(DieColor.BLUE, 3),
            ],
        )
        player.b2_available = True
        player.y1_available = False

        plan = self.bot0.take_phase3_actions(player, engine.state, engine.rng)

        # Prioritizes B2 secret conversion ($4 for +1 Secret)
        self.assertTrue(plan.use_b2_secret)
        # Patches the colored die (Blue) first with the 1 available patch token
        self.assertEqual(len(plan.patch_actions), 1)
        self.assertFalse(plan.patch_actions[0]["use_cash"])
        self.assertEqual(plan.patch_actions[0]["die_index"], 1)  # Blue die is at index 1 in unpatched_dice
        # Zero cash repairs and zero market purchases
        self.assertEqual(len(plan.market_purchases), 0)


if __name__ == "__main__":
    unittest.main()
