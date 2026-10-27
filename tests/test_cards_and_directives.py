"""Unit tests for active Version Directives and Module Variant (★) abilities."""

import unittest

from sim.bots import AdaptiveBalancedBot
from sim.config import CubeColor, DieColor, GameConfig, ShieldColor
from sim.engine import GameEngine, PlayerState
from sim.entities import (
    Face,
    VariantCard,
    VersionCard,
    create_colored_die,
    get_all_variant_cards,
    get_all_version_cards,
)


class TestCardsAndDirectives(unittest.TestCase):
    def setUp(self) -> None:
        self.bot = AdaptiveBalancedBot(0)
        self.all_variants = get_all_variant_cards()
        self.all_versions = {v.directive_code: v for v in get_all_version_cards()}

    def test_directive_data_scraper_setup_cash(self) -> None:
        cfg = GameConfig(num_players=2, starting_money=5)
        deck = [self.all_versions["DATA_SCRAPER"], self.all_versions["RAAS"], self.all_versions["ZERO_DAY_OVERRIDE"]]
        engine = GameEngine(cfg, [self.bot, AdaptiveBalancedBot(1)], version_deck=deck, seed=42)

        # Each player starts with +$1 extra money ($5 + 1 = $6)
        self.assertEqual(engine.state.players[0].money, 6)
        self.assertEqual(engine.state.players[1].money, 6)

    def test_directive_raas_red_strength_boost(self) -> None:
        """v0.6 RAAS Encrypted Memory: Any rolled die showing cash is locked immediately."""
        cfg = GameConfig(num_players=2)
        deck = [self.all_versions["SCRIPT_KIDDIE"], self.all_versions["RAAS"], self.all_versions["ZERO_DAY_OVERRIDE"]]
        engine = GameEngine(cfg, [self.bot, AdaptiveBalancedBot(1)], version_deck=deck, seed=42)
        engine.state.current_version_index = 1  # Active: RAAS

        player = engine.state.players[0]
        cash_face = Face("+$1", money=1)
        gray_die = create_colored_die(DieColor.GRAY, 1)
        gray_die.faces = [cash_face] * 6
        player.ready_dice = [gray_die]

        engine._execute_phase_1()
        self.assertTrue(gray_die.is_locked, "Under RAAS, rolled cash die must be locked")

    def test_directive_zero_day_override_reduces_shields(self) -> None:
        """v0.6 ZERO_DAY_OVERRIDE Kernel Lock: Any rolled die showing a shield is locked immediately."""
        cfg = GameConfig(num_players=2)
        deck = [self.all_versions["SCRIPT_KIDDIE"], self.all_versions["RAAS"], self.all_versions["ZERO_DAY_OVERRIDE"]]
        engine = GameEngine(cfg, [self.bot, AdaptiveBalancedBot(1)], version_deck=deck, seed=42)
        engine.state.current_version_index = 2  # Active: ZERO_DAY_OVERRIDE

        player = engine.state.players[0]
        shield_face = Face("Block 1 Blue", block_amount=1, shield_color=ShieldColor.BLUE)
        gray_die = create_colored_die(DieColor.GRAY, 1)
        gray_die.faces = [shield_face] * 6
        player.ready_dice = [gray_die]

        engine._execute_phase_1()
        self.assertTrue(gray_die.is_locked, "Under ZERO_DAY_OVERRIDE, rolled shield die must be locked")

    def test_variant_r2_threat_bounty(self) -> None:
        """R2 gives +$2 if player takes 0 unblocked Red damage."""
        player = PlayerState(player_id=0, bot=self.bot, money=5, secrets=6, patches=0)
        die = create_colored_die(DieColor.RED, 1, self.all_variants["R2"])
        die.current_face = self.all_variants["R2"].star_face
        player.ready_dice = [die]

        engine = GameEngine(GameConfig(num_players=2), [self.bot, AdaptiveBalancedBot(1)], seed=42)
        commitments = {0: ShieldColor.RED}

        # 2 Red attack vs 2 Red shield -> 0 unblocked Red damage -> +$2 bounty awarded!
        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=[die],
            commitments=commitments,
            attack_strengths={CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            active_directive="NONE",
        )
        self.assertEqual(player.money, 7)  # 5 + 2

    def test_variant_y2_cloud_monopoly(self) -> None:
        """Y2 gives +$2 plus +$1 per different colored module die owned (max +$5)."""
        player = PlayerState(player_id=0, bot=self.bot, money=5, secrets=6, patches=0)
        y_card = self.all_variants["Y2"]
        die1 = create_colored_die(DieColor.YELLOW, 1, y_card)
        die2 = create_colored_die(DieColor.RED, 2)
        die1.current_face = y_card.star_face
        die2.current_face = Face("+$2", money=2)

        player.ready_dice = [die1, die2]
        engine = GameEngine(GameConfig(num_players=2), [self.bot, AdaptiveBalancedBot(1)], seed=42)

        # Owned distinct colored dice = 2 (Yellow, Red). Payout = 2 + 2 = $4 from die1, plus $2 from die2 = +$6
        engine._apply_immediate_face_outputs(player)
        self.assertEqual(player.money, 11)  # 5 + 4 + 2

    def test_variant_y3_proprietary_training(self) -> None:
        """Y3 gives +1 Corporate Secret and immediately moves the die to Unpatched."""
        player = PlayerState(player_id=0, bot=self.bot, money=5, secrets=6, patches=0)
        y3_card = self.all_variants["Y3"]
        die = create_colored_die(DieColor.YELLOW, 1, y3_card)
        die.current_face = y3_card.star_face
        player.ready_dice = [die]

        engine = GameEngine(GameConfig(num_players=2), [self.bot, AdaptiveBalancedBot(1)], seed=42)
        engine._apply_immediate_face_outputs(player)

        self.assertEqual(player.secrets, 7)  # 6 + 1
        self.assertIn(die, player.unpatched_dice)
        self.assertNotIn(die, player.ready_dice)

    def test_phase3_star_activation_guards_reject_unrolled_actions(self) -> None:
        """Verify that Phase 3 guards reject attempts to execute un-rolled star abilities."""
        from sim.bots import Phase3ActionPlan

        engine = GameEngine(
            GameConfig(num_players=2, starting_money=10, starting_secrets=5),
            [self.bot, AdaptiveBalancedBot(1)],
            seed=42,
        )
        p0 = engine.state.players[0]
        # p0 did not roll B2, Y1, P1, or P3
        p0.b2_available = False
        p0.y1_available = False
        p0.p1_available = False
        p0.p3_available = None

        plan = Phase3ActionPlan(
            use_b2_secret=True,
            use_y1_secret=True,
            p1_cube_choice=CubeColor.RED,
            p3_cube_choice=CubeColor.BLUE,
        )

        initial_money = p0.money
        initial_secrets = p0.secrets
        initial_staging = dict(engine.state.staging_cup)

        p0.bot.take_phase3_actions = lambda *args, **kwargs: plan
        engine.state.players[1].bot.take_phase3_actions = lambda *args, **kwargs: Phase3ActionPlan()
        engine.state.first_player_index = 0
        engine._execute_phase_3()

        # All unauthorized star actions must be rejected
        self.assertEqual(p0.money, initial_money)
        self.assertEqual(p0.secrets, initial_secrets)
        for c in CubeColor:
            self.assertEqual(engine.state.staging_cup[c], initial_staging[c])


if __name__ == "__main__":
    unittest.main()
