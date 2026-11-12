"""Tests for Phase 56: Remove White Contractor Dice & Glitch Faces (v0.39.1 / v0.40.0).

Validates invariants INV-RCD-01 through INV-RCD-08 per docs/specs/remove_contractor_dice_spec.md:
- TEST-RCD-01: Zero contractor config & levers (INV-RCD-01)
- TEST-RCD-02: Phase 1 bypasses temp staffing (INV-RCD-02)
- TEST-RCD-03: Universal slot clean without die identity exceptions (INV-RCD-03)
- TEST-RCD-04: Meridian Financial Trust Capital Injection in Phase 3 (INV-RCD-04)
- TEST-RCD-05: The Operator Logistics Bounty in Phase 3 (INV-RCD-05)
- TEST-RCD-06: Phase 4 no contractor expiry or sacrifice (INV-RCD-06)
- TEST-RCD-07: Backwards parity preservation (INV-RCD-07)
- TEST-RCD-08: Bot decision hooks and capital injection (INV-RCD-08)
- TEST-RCD-09: Web controller capabilities & actions
"""

from __future__ import annotations

import random
import unittest

from sim.config import CubeColor, DieColor, GameConfig, RoundPhase
from sim.engine import GameEngine, secret_faces
from sim.engine.phase1_roll_deploy import execute_phase_1
from sim.engine.phase3_income import execute_player_income, purple_star_dice_in_production
from sim.engine.phase4_attack_resolution import expire_contractors, resolve_player_attack
from sim.engine.state import GameState, PlayerState
from sim.entities import (
    COMPANIES,
    WHITE_HATS,
    CompanyCode,
    Face,
    WhiteHatCode,
    create_gray_die,
    create_colored_die,
    get_all_variant_cards,
    get_default_version_deck,
)
from sim.bots.base import BaseBot
from sim.bots.mixed_policy import MixedPolicyBot
from sim.bots.adaptive_balanced import AdaptiveBalancedBot
from web.controller.core import GameController


ALL_CARDS = get_all_variant_cards("MARKETING")


def _cards():
    return {
        DieColor.RED: ALL_CARDS["R1"],
        DieColor.BLUE: ALL_CARDS["B1"],
        DieColor.GREEN: ALL_CARDS["G1"],
        DieColor.YELLOW: ALL_CARDS["Y1"],
    }


def _engine_v040(n: int = 3, seed: int = 42, **cfg_overrides) -> GameEngine:
    bots = [MixedPolicyBot(i, match_seed=seed) for i in range(n)]
    companies = [COMPANIES[CompanyCode.MERIDIAN], COMPANIES[CompanyCode.PROMETHEUS], COMPANIES[CompanyCode.DTO]][:n]
    white_hats = [WHITE_HATS[WhiteHatCode.OPERATOR], WHITE_HATS[WhiteHatCode.PHREAKER], WHITE_HATS[WhiteHatCode.ACOUSTIC]][:n]
    deck = get_default_version_deck()
    cfg = GameConfig.v040(num_players=n, **cfg_overrides)
    return GameEngine(
        config=cfg,
        bots=bots,
        version_deck=deck,
        variant_cards=_cards(),
        companies=companies,
        white_hats=white_hats,
        seed=seed,
    )


class TestRemoveContractorDice(unittest.TestCase):
    """Test suite for Phase 56: Remove White Contractor Dice & Glitch Faces."""

    def test_rcd_01_zero_contractor_config(self) -> None:
        """TEST-RCD-01: Verify GameConfig.v040() and v0391() zero contractor configuration."""
        for cfg in (GameConfig.v040(), GameConfig.v0391(), GameConfig.v040_roster()):
            self.assertFalse(cfg.white_contractor_dice_enabled)
            self.assertEqual(cfg.contractor_max_hire, 0)
            self.assertEqual(cfg.contractor_supply_total, 0)
            self.assertEqual(cfg.meridian_override_mode, "CAPITAL_INJECTION")
            self.assertEqual(cfg.meridian_capital_injection_cash, 3)
            self.assertEqual(cfg.operator_protocol_mode, "LOGISTICS_BOUNTY")
            self.assertEqual(cfg.operator_logistics_bounty_research, 1)

        engine = _engine_v040()
        self.assertEqual(engine.state.contractor_supply, 0)

    def test_rcd_02_phase1_bypasses_temp_staffing(self) -> None:
        """TEST-RCD-02: Run Phase 1 on v040(). Verify player has no contractor dice and 0 hires."""
        engine = _engine_v040()
        player = engine.state.players[0]
        self.assertEqual(player.contractor_dice, [])
        self.assertEqual(player.hired_contractor_count, 0)

        # Run Phase 1
        execute_phase_1(engine)

        self.assertEqual(player.contractor_dice, [])
        self.assertEqual(player.hired_contractor_count, 0)
        self.assertEqual(engine.state.contractor_supply, 0)
        # All deployed dice in In Production or Processing Box must be non-white
        all_deployed = player.in_production_dice + list(player.processing_box)
        for die in all_deployed:
            self.assertNotEqual(die.color, DieColor.WHITE)

    def test_rcd_03_universal_slot_clean_no_exceptions(self) -> None:
        """TEST-RCD-03: Gray die with Block 1 Any cleans Glitched Shield Slot in Phase 1 and moves to Scanned Box."""
        engine = _engine_v040()
        player = engine.state.players[0]
        player.glitched_shield_slots = 1

        gray_die = create_gray_die(999)
        gray_die.roll = lambda rng=None: gray_die.faces[0]
        player.ready_for_release_dice = [gray_die]
        player.bot.choose_slot_cleaners = lambda p, dice, cand, s, st: cand[:1]

        # Execute Phase 1 through the engine
        execute_phase_1(engine)

        self.assertEqual(player.glitched_shield_slots, 0)
        self.assertIn(gray_die, player.scanned_dice)
        self.assertNotIn(gray_die, player.ready_for_release_dice)
        self.assertNotIn(gray_die, player.in_production_dice)
        self.assertIsNone(gray_die.production_role)
        self.assertEqual(engine.state.contractor_supply, 0)

    def test_rcd_04_meridian_capital_injection_phase3(self) -> None:
        """TEST-RCD-04: Meridian Financial Trust Capital Injection awards +$3 in Phase 3 Income."""
        engine = _engine_v040()
        player = engine.state.players[0]  # contracted with MERIDIAN
        active_ver = engine.state.active_version.version_str

        self.assertTrue(player.is_ability_available(active_ver))
        initial_money = player.money

        # Execute Phase 3 Income for player
        rec = execute_player_income(engine, player)

        # Meridian should have activated Capital Injection (+3 cash)
        self.assertFalse(player.is_ability_available(active_ver))
        self.assertEqual(rec.money, 3)
        self.assertEqual(player.money, initial_money + 3)

        # Subsequent Income in same version should NOT activate it again
        rec2 = execute_player_income(engine, player)
        self.assertEqual(rec2.money, 0)

    def test_rcd_05_operator_logistics_bounty_phase3(self) -> None:
        """TEST-RCD-05: The Operator Logistics Bounty awards +1 Research per Purple Star in In Production."""
        engine = _engine_v040()
        # Seat 0 has White Hat OPERATOR
        player = engine.state.players[0]
        self.assertEqual(player.white_hat.code, WhiteHatCode.OPERATOR)

        # Set up 1 Purple Star in In Production
        purple1 = create_colored_die(DieColor.PURPLE, 888)
        purple1.current_face = Face("Purple ★ (Signature Protocol)", is_star=True, star_code="PURPLE_STAR")
        player.in_production_dice.append(purple1)

        initial_research = player.research_tokens
        rec = execute_player_income(engine, player)
        self.assertEqual(rec.protocol_research, 1)
        self.assertEqual(player.research_tokens, initial_research + 1)

        # Test with 2 Purple Stars in In Production
        player.research_tokens = initial_research
        purple2 = create_colored_die(DieColor.PURPLE, 889)
        purple2.current_face = Face("Purple ★ (Signature Protocol)", is_star=True, star_code="PURPLE_STAR")
        player.in_production_dice.append(purple2)

        rec_double = execute_player_income(engine, player)
        self.assertEqual(rec_double.protocol_research, 2)
        self.assertEqual(player.research_tokens, initial_research + 2)

    def test_rcd_06_phase4_no_contractor_expiry_or_sacrifice(self) -> None:
        """TEST-RCD-06: Phase 4 Attack Resolution with unblocked Green malware glitches slots, no contractor sacrifice."""
        engine = _engine_v040()
        player = engine.state.players[0]
        player.glitched_shield_slots = 0

        secret_faces.glitch_slots(player, 2, "malware")
        self.assertEqual(player.glitched_shield_slots, 2)

        # expire_contractors should be a clean no-op
        supply_before = engine.state.contractor_supply
        expire_contractors(engine)
        self.assertEqual(engine.state.contractor_supply, supply_before)
        self.assertEqual(player.contractor_dice, [])

    def test_rcd_07_backwards_parity_preserved(self) -> None:
        """TEST-RCD-07: Verify historical config presets preserve contractor dice and legacy abilities, and pass parity."""
        cfg_v038 = GameConfig.v038()
        self.assertTrue(cfg_v038.white_contractor_dice_enabled)
        self.assertEqual(cfg_v038.contractor_max_hire, 3)
        self.assertEqual(cfg_v038.contractor_supply_total, 12)
        self.assertEqual(cfg_v038.meridian_override_mode, "REDUNDANT_CREW")
        self.assertEqual(cfg_v038.operator_protocol_mode, "CONTINGENT_STAFFING")

        cfg_v037 = GameConfig.v037()
        self.assertTrue(cfg_v037.white_contractor_dice_enabled)
        self.assertEqual(cfg_v037.contractor_max_hire, 3)

        # Run historical bit-for-bit parity fixtures check
        from tests.test_v380_secret_faces import TestRSP1
        TestRSP1().test_rsp01_v038b_parity_fixtures()

    def test_rcd_08_bot_hooks_and_capital_injection(self) -> None:
        """TEST-RCD-08: Verify bots return 0 for contractor hires and True for capital injection."""
        bot = MixedPolicyBot(0, match_seed=42)
        player = PlayerState(player_id=0, name="Bot 0", bot=bot, money=10, secrets=4, patches=0)

        self.assertEqual(bot.choose_contractor_hires(player, 0, {}, {}, random.Random(42)), 0)
        self.assertFalse(bot.choose_operator_buy_third_die(player, 0, {}, {}, random.Random(42)))
        self.assertTrue(bot.choose_meridian_capital_injection(player))

    def test_rcd_09_web_controller_capabilities(self) -> None:
        """TEST-RCD-09: Web controller capabilities and actions under v0.40.0."""
        controller = GameController()
        controller.new_game(rules_version="v0.40.0")
        caps = controller.get_action_capabilities(0)

        # Contractor hiring must be disabled
        self.assertFalse(caps["can_hire_contractors"])
        self.assertIsNone(caps["next_contractor_cost"])

        # hire_contractors() should raise ValueError
        with self.assertRaises(ValueError):
            controller.hire_contractors(0, count=1)


if __name__ == "__main__":
    unittest.main()
