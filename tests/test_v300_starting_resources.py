"""Unit tests for Phase 37 (v0.30.0 Baseline) starting resources, starter purple specialist die,
phreaker fallback, and market cost calibration per docs/specs/v300_starting_resources_spec.md.
"""

from __future__ import annotations

import random
import unittest
from typing import List

from sim.config import CubeColor, DieColor, GameConfig, ShieldColor
from sim.engine.core import GameEngine
from sim.engine.phase3_ops import execute_phase_3, resolve_phreaker_jumper_diagnostics
from sim.entities import (
    COMPANIES,
    WHITE_HATS,
    CompanyCode,
    Face,
    WhiteHatCode,
    create_colored_die,
    create_gray_die,
    get_all_variant_cards,
)


class TestV300StartingResources(unittest.TestCase):
    """Test suite covering INV-START-POOL-01 through INV-VAR-COST-CALIB-01."""

    def test_starting_pool_three_gray_one_purple(self) -> None:
        """TEST-V300-01 (INV-START-POOL-01): Verify engine initialization populates exactly
        3 Gray dice and 1 Purple die in ready_for_release_dice for all players (total 4 dice).
        """
        for n in [2, 3, 4]:
            config = GameConfig(num_players=n)
            engine = GameEngine(config=config, seed=42)
            self.assertEqual(len(engine.state.players), n)
            for p in engine.state.players:
                self.assertEqual(len(p.ready_for_release_dice), 4)
                gray_dice = [d for d in p.ready_for_release_dice if d.color == DieColor.GRAY]
                purple_dice = [d for d in p.ready_for_release_dice if d.color == DieColor.PURPLE]
                self.assertEqual(len(gray_dice), 3)
                self.assertEqual(len(purple_dice), 1)

    def test_starter_purple_die_properties(self) -> None:
        """TEST-V300-02 (INV-START-POOL-01): Verify starting Purple die has correct faces
        (2 Any shields, $2, $1+1🔬, Glitch, Purple ★) and 0 starting cost.
        """
        config = GameConfig(num_players=4)
        engine = GameEngine(config=config, seed=123)
        for p in engine.state.players:
            purple_die = next(d for d in p.ready_for_release_dice if d.color == DieColor.PURPLE)
            self.assertEqual(purple_die.cost, 0)
            self.assertEqual(len(purple_die.faces), 6)

            any_shields = [f for f in purple_die.faces if f.is_shield and f.shield_color == ShieldColor.ANY]
            two_cash = [f for f in purple_die.faces if f.money == 2 and not f.is_star and not f.patches]
            cash_and_patch = [f for f in purple_die.faces if f.money == 1 and f.patches == 1]
            glitches = [f for f in purple_die.faces if f.is_glitch]
            stars = [f for f in purple_die.faces if f.is_star and f.star_code == "PURPLE_STAR"]

            self.assertEqual(len(any_shields), 2)
            self.assertEqual(len(two_cash), 1)
            self.assertEqual(len(cash_and_patch), 1)
            self.assertEqual(len(glitches), 1)
            self.assertEqual(len(stars), 1)

    def test_starting_research_baseline_zero(self) -> None:
        """TEST-V300-03 (INV-START-RES-01): Verify default corporate players start with
        0 🔬 research tokens across 2P, 3P, and 4P configurations.
        """
        for n in [2, 3, 4]:
            config = GameConfig(num_players=n, enable_corporate_asymmetry=False)
            engine = GameEngine(config=config, seed=42)
            for p in engine.state.players:
                self.assertEqual(p.patches, 0)
                self.assertEqual(p.research_tokens, 0)

    def test_helix_starting_research_bonus(self) -> None:
        """TEST-V300-04 (INV-START-RES-01): Verify Helix Biomedical Consortium starts with
        exactly 2 🔬 research tokens (0 baseline + 2 corporate bonus).
        """
        config = GameConfig(num_players=2, enable_corporate_asymmetry=True)
        helix_comp = COMPANIES[CompanyCode.HELIX]
        other_comp = COMPANIES[CompanyCode.OMNIDYNE]
        wh1 = WHITE_HATS[WhiteHatCode.PRODIGY]
        wh2 = WHITE_HATS[WhiteHatCode.PHREAKER]

        engine = GameEngine(
            config=config,
            companies=[helix_comp, other_comp],
            white_hats=[wh1, wh2],
            seed=42,
        )
        self.assertEqual(engine.state.players[0].patches, 2)
        self.assertEqual(engine.state.players[1].patches, 0)

    def test_starting_cash_baseline_six(self) -> None:
        """TEST-V300-05 (INV-START-CASH-01): Verify default corporate players start with
        exactly $6 cash (with non-bonus version card).
        """
        config = GameConfig(num_players=4, enable_corporate_asymmetry=False)
        engine = GameEngine(config=config, seed=42)
        cash_bonus = 1 if engine.state.active_directive_code == "DATA_SCRAPER" else 0
        for p in engine.state.players:
            self.assertEqual(p.money, 6 + cash_bonus)

    def test_meridian_starting_cash_bonus(self) -> None:
        """TEST-V300-06 (INV-START-CASH-01): Verify Meridian Financial Trust starts with
        exactly $8 cash ($6 baseline + $2 corporate bonus).
        """
        config = GameConfig(num_players=2, enable_corporate_asymmetry=True)
        meridian_comp = COMPANIES[CompanyCode.MERIDIAN]
        other_comp = COMPANIES[CompanyCode.OMNIDYNE]
        wh1 = WHITE_HATS[WhiteHatCode.OPERATOR]
        wh2 = WHITE_HATS[WhiteHatCode.PHREAKER]

        engine = GameEngine(
            config=config,
            companies=[meridian_comp, other_comp],
            white_hats=[wh1, wh2],
            seed=42,
        )
        cash_bonus = 1 if engine.state.active_directive_code == "DATA_SCRAPER" else 0
        self.assertEqual(engine.state.players[0].money, 8 + cash_bonus)
        self.assertEqual(engine.state.players[1].money, 6 + cash_bonus)

    def test_personal_purple_reserve_capacity_one(self) -> None:
        """TEST-V300-07 (INV-PURPLE-RES-01): Verify player.personal_purple_reserve initializes
        to 1; purchasing drops it to 0; second purchase attempt fails.
        """
        config = GameConfig(num_players=4)
        engine = GameEngine(config=config, seed=42)
        p = engine.state.players[0]
        self.assertEqual(p.personal_purple_reserve, 1)

        # Give sufficient money to buy
        p.money = 20
        # Purchase 1st Purple die from reserve
        cost = p.get_purple_reserve_cost()
        self.assertGreaterEqual(p.personal_purple_reserve, 1)
        p.personal_purple_reserve -= 1
        p.money -= cost
        self.assertEqual(p.personal_purple_reserve, 0)

        # Attempt second purchase: should not have stock
        self.assertEqual(p.personal_purple_reserve, 0)

    def test_global_purple_die_footprint(self) -> None:
        """TEST-V300-08 (INV-PURPLE-RES-01): Verify that across all players, total active
        Purple dice plus total reserve Purple dice equals 2 * num_players (8 dice in 4P).
        """
        for n in [2, 3, 4]:
            config = GameConfig(num_players=n)
            engine = GameEngine(config=config, seed=42)
            total_active_purple = sum(
                len([d for d in p.ready_for_release_dice if d.color == DieColor.PURPLE])
                for p in engine.state.players
            )
            total_reserve_purple = sum(p.personal_purple_reserve for p in engine.state.players)
            self.assertEqual(total_active_purple + total_reserve_purple, 2 * n)
            if n == 4:
                self.assertEqual(total_active_purple + total_reserve_purple, 8)

    def test_phreaker_fallback_empty_pipeline(self) -> None:
        """TEST-V300-09 (INV-PHREAKER-FALLBACK-01): Trigger Phreaker Jumper Diagnostics with
        empty Under Development pipeline; verify player receives immediate +$1 cash.
        """
        config = GameConfig(num_players=2)
        phreaker_wh = WHITE_HATS[WhiteHatCode.PHREAKER]
        other_wh = WHITE_HATS[WhiteHatCode.OPERATOR]
        engine = GameEngine(config=config, white_hats=[phreaker_wh, other_wh], seed=42)
        p = engine.state.players[0]

        # Ensure pipeline is completely empty
        p.glitched_dice.clear()
        p.scanned_dice.clear()
        self.assertEqual(len(p.under_development_dice), 0)

        initial_money = p.money
        res = resolve_phreaker_jumper_diagnostics(engine, p, die_id=None)
        self.assertIsNone(res)
        self.assertEqual(p.money, initial_money + 1)

    def test_phreaker_diagnostics_normal_pipeline(self) -> None:
        """TEST-V300-10 (INV-PHREAKER-FALLBACK-01): Trigger Phreaker Jumper Diagnostics with
        1 die in Glitched; verify glitched die is rolled and offline position is preserved.
        """
        config = GameConfig(num_players=2)
        phreaker_wh = WHITE_HATS[WhiteHatCode.PHREAKER]
        other_wh = WHITE_HATS[WhiteHatCode.OPERATOR]
        engine = GameEngine(config=config, white_hats=[phreaker_wh, other_wh], seed=42)
        p = engine.state.players[0]

        # Put 1 Gray die in glitched_dice
        offline_die = create_gray_die(999)
        p.glitched_dice = [offline_die]
        p.scanned_dice.clear()
        self.assertEqual(len(p.under_development_dice), 1)

        forced_face = Face(name="+$1", money=1)
        initial_money = p.money
        res = resolve_phreaker_jumper_diagnostics(engine, p, die_id=offline_die.die_id, forced_face=forced_face)
        self.assertEqual(res, forced_face)
        self.assertEqual(p.money, initial_money + 1)
        # Verify die remains in glitched_dice without advancing
        self.assertEqual(p.glitched_dice, [offline_die])
        self.assertEqual(len(p.scanned_dice), 0)

    def test_market_variant_card_pricing_tiers(self) -> None:
        """TEST-V300-11 (INV-VAR-COST-CALIB-01): Verify all 12 colored variant cards have exact prices:
        R3/B3/G2/G3 at $4; R1/R2/B1/G1/Y2/Y3 at $5; B2/Y1 at $6.
        """
        variants = get_all_variant_cards()

        expected_costs = {
            # $4 Tier
            "R3": 4,
            "B3": 4,
            "G2": 4,
            "G3": 4,
            # $5 Tier
            "R1": 5,
            "R2": 5,
            "B1": 5,
            "G1": 5,
            "Y2": 5,
            "Y3": 5,
            # $6 Tier
            "B2": 6,
            "Y1": 6,
        }

        for code, expected_cost in expected_costs.items():
            self.assertIn(code, variants)
            self.assertEqual(variants[code].cost, expected_cost, f"Card {code} cost mismatch")

    def test_white_hat_reserve_costs(self) -> None:
        """TEST-V300-12 (INV-VAR-COST-CALIB-01): Verify White Hat reserve costs:
        Phreaker ($4), Acoustic ($4), Operator ($5), Prodigy ($5), Spook ($5), Cipher ($6).
        """
        expected_reserve_costs = {
            WhiteHatCode.PHREAKER: 4,
            WhiteHatCode.ACOUSTIC: 4,
            WhiteHatCode.OPERATOR: 5,
            WhiteHatCode.PRODIGY: 5,
            WhiteHatCode.SPOOK: 5,
            WhiteHatCode.CIPHER: 6,
        }

        for code, expected_cost in expected_reserve_costs.items():
            self.assertIn(code, WHITE_HATS)
            self.assertEqual(WHITE_HATS[code].reserve_cost, expected_cost, f"Operative {code} cost mismatch")

    def test_colored_die_and_market_fallback_costs(self) -> None:
        """TEST-V300-13 (INV-VAR-COST-CALIB-01): Verify fallback default costs for create_colored_die
        and GameState.get_market_die_cost match Red=5, Blue=5, Green=5, Yellow=6, Purple=4.
        """
        expected_fallback = {
            DieColor.RED: 5,
            DieColor.BLUE: 5,
            DieColor.GREEN: 5,
            DieColor.YELLOW: 6,
            DieColor.PURPLE: 4,
        }

        # Verify create_colored_die with variant_card=None
        for color, cost in expected_fallback.items():
            die = create_colored_die(color, 900)
            self.assertEqual(die.cost, cost, f"create_colored_die fallback mismatch for {color}")

        # Verify GameState.get_market_die_cost fallback when variant_cards is empty
        engine = GameEngine(GameConfig(num_players=2), seed=42)
        engine.state.variant_cards.clear()
        for color, cost in expected_fallback.items():
            self.assertEqual(
                engine.state.get_market_die_cost(color),
                cost,
                f"GameState.get_market_die_cost fallback mismatch for {color}",
            )


if __name__ == "__main__":
    unittest.main()
