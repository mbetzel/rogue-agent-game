"""Unit tests for dice wear mechanics, unblocked damage, and Patient Zero triggers."""

import unittest

from sim.bots import AdaptiveBalancedBot
from sim.config import CubeColor, DieColor, GameConfig, ShieldColor
from sim.engine import GameEngine, PlayerState
from sim.entities import Face, VariantCard, create_colored_die, create_gray_die


class TestWearAndDamage(unittest.TestCase):
    def setUp(self) -> None:
        self.config = GameConfig(num_players=2, starting_money=5, starting_secrets=6)
        self.bot = AdaptiveBalancedBot(0)

    def test_unused_shields_do_not_wear(self) -> None:
        """Under v0.22.0 Zero Dice Wear, shield dice remain in production/ready and do not wear."""
        player = PlayerState(
            player_id=0,
            bot=self.bot,
            money=5,
            secrets=6,
            patches=0,
        )
        die1 = create_gray_die(1)
        die1.current_face = Face("Block 1 Any", block_amount=1, shield_color=ShieldColor.RED)
        die2 = create_gray_die(2)
        die2.current_face = Face("Block 1 Any", block_amount=1, shield_color=ShieldColor.RED)

        player.in_production_dice = [die1, die2]
        player.ready_dice = []

        engine = GameEngine(self.config, [self.bot, AdaptiveBalancedBot(1)], seed=42)

        # 1 Red cube dropped: die1 absorbs it, die2 is unused
        commitments = {0: ShieldColor.RED, 1: ShieldColor.RED}
        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=[die1, die2],
            commitments=commitments,
            attack_strengths={CubeColor.RED: 1, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 1, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        # Zero Dice Wear: both dice remain safely in in_production_dice
        self.assertIn(die1, player.in_production_dice)
        self.assertIn(die2, player.in_production_dice)
        self.assertEqual(len(player.in_production_dice), 2)
        self.assertEqual(len(player.unpatched_dice), 0)

    def test_air_gapped_backup_b3_does_not_wear(self) -> None:
        """Variant B3 (Air-Gapped Backup) blocks 1 Blue and under v0.22.0 Zero Dice Wear, neither wears."""
        player = PlayerState(player_id=0, bot=self.bot, money=5, secrets=6, patches=0)
        b3_card = VariantCard(
            code="B3",
            name="Air-Gapped Backup",
            die_color=DieColor.BLUE,
            description="Block 1 Blue; zero dice wear in v0.22.0.",
            star_face=Face("B3: Air-Gapped", block_amount=1, shield_color=ShieldColor.BLUE, is_star=True, star_code="B3"),
        )
        die = create_colored_die(DieColor.BLUE, 1, b3_card)
        die.current_face = b3_card.star_face
        gray_die = create_gray_die(2)
        player.in_production_dice = [die, gray_die]
        player.ready_dice = []

        engine = GameEngine(self.config, [self.bot, AdaptiveBalancedBot(1)], seed=42)
        commitments = {0: ShieldColor.BLUE}

        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=[die],
            commitments=commitments,
            attack_strengths={CubeColor.RED: 0, CubeColor.BLUE: 1, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 0, CubeColor.BLUE: 1, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        self.assertIn(die, player.in_production_dice)
        self.assertEqual(len(player.unpatched_dice), 0)

    def test_red_damage_and_insolvency(self) -> None:
        """Under v0.3, unblocked Red drains cash to $0, then unpaid ransom leaks to Secrets."""
        player = PlayerState(player_id=0, bot=self.bot, money=2, secrets=6, patches=0)
        engine = GameEngine(self.config, [self.bot, AdaptiveBalancedBot(1)], seed=42)

        # 3 unblocked Red cubes with $2 cash: cash drops to 0, 1 unpaid leaks to secrets (6 -> 5)
        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=[],
            commitments={},
            attack_strengths={CubeColor.RED: 3, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 3, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        self.assertEqual(player.money, 0)
        self.assertEqual(player.secrets, 5)
        self.assertFalse(player.is_patient_zero)

        # Additional unblocked Red when player has 1 secret: flat 1 secret leak -> Patient Zero
        player.secrets = 1
        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=[],
            commitments={},
            attack_strengths={CubeColor.RED: 5, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 5, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        self.assertEqual(player.money, 0)
        self.assertEqual(player.secrets, 0)
        self.assertTrue(player.is_patient_zero)
        self.assertEqual(player.elimination_reason, "Total Breach (<= 0 Secrets)")

    def test_blue_damage_and_total_breach(self) -> None:
        player = PlayerState(player_id=0, bot=self.bot, money=5, secrets=2, patches=0)
        engine = GameEngine(self.config, [self.bot, AdaptiveBalancedBot(1)], seed=42)

        # 3 unblocked Blue cubes with 2 secrets -> secrets reach -1 (<= 0)
        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=[],
            commitments={},
            attack_strengths={CubeColor.RED: 0, CubeColor.BLUE: 3, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 0, CubeColor.BLUE: 3, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        self.assertEqual(player.secrets, -1)
        self.assertTrue(player.is_patient_zero)
        self.assertEqual(player.breach_depth, 1)

    def test_green_malware_demotion_and_destruction(self) -> None:
        die_ready1 = create_gray_die(1)
        die_ready2 = create_gray_die(2)
        player = PlayerState(
            player_id=0,
            bot=self.bot,
            money=5,
            secrets=6,
            patches=0,
            in_production_dice=[die_ready1, die_ready2],
            unpatched_dice=[],
        )
        engine = GameEngine(self.config, [self.bot, AdaptiveBalancedBot(1)], seed=42)

        # 1 unblocked Green cube -> moves 1 active die from in_production to glitched (unpatched)
        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=[],
            commitments={},
            attack_strengths={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 1},
            exited_cubes={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 1},
            active_directive="NONE",
        )
        self.assertEqual(len(player.in_production_dice), 1)
        self.assertEqual(len(player.unpatched_dice), 1)

        # 2 more unblocked Green cubes:
        # First moves the remaining in_production die to glitched (unpatched).
        # Second has NO active dice left -> under v0.31.0 Malware Fizzle, 0 dice destroyed!
        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=[],
            commitments={},
            attack_strengths={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 2},
            exited_cubes={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 2},
            active_directive="NONE",
        )
        self.assertEqual(len(player.in_production_dice), 0)
        self.assertEqual(len(player.unpatched_dice), 2)  # Both moved to unpatched, 0 destroyed


if __name__ == "__main__":
    unittest.main()
