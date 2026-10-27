"""Unit tests for dice faces, variant cards, and version cards."""

import random
import unittest

from sim.config import CubeColor, DieColor, ShieldColor
from sim.entities import (
    create_colored_die,
    create_gray_die,
    get_all_variant_cards,
    get_all_version_cards,
    get_default_variant_cards,
    get_default_version_deck,
)


class TestEntities(unittest.TestCase):
    def test_gray_starter_die(self) -> None:
        die = create_gray_die(1)
        self.assertEqual(die.die_id, 1)
        self.assertEqual(die.color, DieColor.GRAY)
        self.assertEqual(die.cost, 0)
        self.assertEqual(die.vp, 0)
        self.assertEqual(len(die.faces), 6)

        # Count face types
        any_shields = [f for f in die.faces if f.shield_color == ShieldColor.ANY and f.block_amount == 1]
        cash_faces = [f for f in die.faces if f.has_cash_option]
        patch_faces = [f for f in die.faces if f.has_patch_option]
        choice_faces = [f for f in die.faces if f.is_choice]
        idle_faces = [f for f in die.faces if f.name == "Idle (0)"]

        self.assertEqual(len(any_shields), 2)
        self.assertEqual(len(cash_faces), 3)
        self.assertEqual(len(patch_faces), 2)
        self.assertEqual(len(choice_faces), 1)
        self.assertEqual(len(idle_faces), 0)

    def test_colored_dice_costs_and_vps(self) -> None:
        variants = get_default_variant_cards()

        red = create_colored_die(DieColor.RED, 1, variants[DieColor.RED])
        self.assertEqual(red.cost, 4)
        self.assertEqual(red.vp, 3)
        self.assertEqual(len(red.faces), 6)

        blue = create_colored_die(DieColor.BLUE, 2, variants[DieColor.BLUE])
        self.assertEqual(blue.cost, 5)
        self.assertEqual(blue.vp, 4)

        green = create_colored_die(DieColor.GREEN, 3, variants[DieColor.GREEN])
        self.assertEqual(green.cost, 4)
        self.assertEqual(green.vp, 3)

        yellow = create_colored_die(DieColor.YELLOW, 4, variants[DieColor.YELLOW])
        self.assertEqual(yellow.cost, 5)
        self.assertEqual(yellow.vp, 4)

        purple = create_colored_die(DieColor.PURPLE, 5, variants[DieColor.PURPLE])
        self.assertEqual(purple.cost, 4)
        self.assertEqual(purple.vp, 3)

    def test_all_15_variant_cards_exist(self) -> None:
        variants = get_all_variant_cards()
        self.assertEqual(len(variants), 15)

        expected_codes = [
            "R1", "R2", "R3",
            "B1", "B2", "B3",
            "G1", "G2", "G3",
            "Y1", "Y2", "Y3",
            "P1", "P2", "P3",
        ]
        for code in expected_codes:
            self.assertIn(code, variants)
            card = variants[code]
            self.assertTrue(card.star_face.is_star)
            self.assertEqual(card.star_face.star_code, code)

    def test_all_6_version_cards_exist(self) -> None:
        versions = get_all_version_cards()
        self.assertEqual(len(versions), 6)

        directives = {v.directive_code for v in versions}
        expected_directives = {
            "SCRIPT_KIDDIE",
            "DATA_SCRAPER",
            "RAAS",
            "POLYMORPHIC_WORM",
            "ZERO_DAY_OVERRIDE",
            "CORRUPTED_KERNEL",
        }
        self.assertEqual(directives, expected_directives)

    def test_die_rolling(self) -> None:
        die = create_gray_die(1)
        rng = random.Random(42)
        rolled = die.roll(rng)
        self.assertIn(rolled, die.faces)
        self.assertEqual(die.current_face, rolled)


if __name__ == "__main__":
    unittest.main()
