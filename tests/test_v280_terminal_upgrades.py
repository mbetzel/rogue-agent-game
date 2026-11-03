"""Unit tests for Phase 35: Asymmetric Corporate Terminal Mats, Hardware Bottlenecks & Research Economy (v0.28.0).

Verifies invariants from docs/specs/v280_terminal_upgrades_spec.md:
- INV-RESEARCH-UNCAPPED-01: Uncapped Research tokens (no 3-patch token clamp).
- INV-DEF-CAP-01: Defense Grid Shield Capacity enforcement (max N shields committed in Phase 1).
- INV-PIPE-GRAD-01: Scanned Graduation Throughput (up to release_bandwidth).
- INV-PIPE-TRIAGE-01: Conveyor Triage Throughput (up to triage_bandwidth).
- INV-UPGRADE-TRACK-01: Hardware upgrade tracks (Pipeline, Defense, Patent R&D).
- INV-PATENT-CONV-01: Cryptographic Patent Conversion (+1 Corporate Secret per patent).
- INV-ASYM-COMPANY-01: Asymmetric Company profiles, starting resources, and upgrade discounts.
"""

from __future__ import annotations

import random
import unittest
from typing import Dict, List

from sim.bots.base import BaseBot, Phase3ActionPlan
from sim.config import CubeColor, DieColor, GameConfig, ShieldColor
from sim.engine.core import GameEngine
from sim.engine.phase1_boot import execute_phase_1
from sim.engine.phase2_threat import execute_phase_2
from sim.engine.phase3_ops import execute_phase_3
from sim.engine.state import GameState, PlayerState, ProductionRole
from sim.entities import (
    COMPANIES,
    CompanyCode,
    Die,
    Face,
    WHITE_HATS,
    WhiteHatCode,
    create_colored_die,
    create_gray_die,
    get_all_variant_cards,
)


class TestV280TerminalUpgrades(unittest.TestCase):
    """Test suite verifying v0.28.0 terminal upgrade invariants."""

    def setUp(self) -> None:
        self.rng = random.Random(42)

    def test_research_tokens_no_cap(self) -> None:
        """INV-RESEARCH-UNCAPPED-01: Research tokens accumulate without an upper bound cap of 3."""
        cfg = GameConfig(num_players=2)
        engine = GameEngine(cfg, seed=42)
        p0 = engine.state.players[0]
        p0.research_tokens = 7

        class IdleBot(BaseBot):
            def take_phase3_actions(self, p, g, rng):
                return Phase3ActionPlan()

        p0.bot = IdleBot(0)
        engine.state.players[1].bot = IdleBot(1)

        execute_phase_3(engine)

        # In v0.28.0, 7 research tokens are fully preserved
        self.assertEqual(p0.research_tokens, 7)
        self.assertEqual(p0.patches, 7)

    def test_defense_capacity_enforcement(self) -> None:
        """INV-DEF-CAP-01: When defense_capacity=2, players cannot commit more than 2 dice to Shields."""
        cfg = GameConfig(num_players=2)
        engine = GameEngine(cfg, seed=42)
        p0 = engine.state.players[0]
        p0.defense_capacity = 2

        # Give player 4 dice with guaranteed shield faces
        shield_face = Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)
        shield_dice: List[Die] = []
        for i in range(4):
            d = create_gray_die(i + 1)
            d.faces = [shield_face] * 6
            d.current_face = shield_face
            shield_dice.append(d)
        p0.ready_for_release_dice = list(shield_dice)

        class HeavyShieldBot(BaseBot):
            def commit_shields(self, player_state, rolled_dice, staging_cubes, stuck_cubes, directive_code, rng):
                # Try to commit all 4 dice to Red shields
                return {i: ShieldColor.RED for i in range(len(rolled_dice))}

            def choose_yahtzee_rerolls(self, *args, **kwargs):
                return []

        p0.bot = HeavyShieldBot(0)
        engine.state.players[1].bot = HeavyShieldBot(1)

        execute_phase_1(engine)

        committed_shields = p0.shield_dice
        self.assertLessEqual(len(committed_shields), 2, "Committed shields must not exceed defense_capacity=2")
        self.assertEqual(len(committed_shields), 2)

    def test_pipeline_triage_bandwidth(self) -> None:
        """INV-PIPE-TRIAGE-01: At most triage_bandwidth dice move from Glitched to Scanned per round."""
        cfg = GameConfig(num_players=2)
        engine = GameEngine(cfg, seed=42)
        p0 = engine.state.players[0]
        p0.triage_bandwidth = 2
        p0.release_bandwidth = 2
        p0.glitched_dice = [create_gray_die(i + 1) for i in range(5)]
        p0.scanned_dice = []
        p0.in_production_dice = []

        class PassiveBot(BaseBot):
            def take_phase3_actions(self, p, g, rng):
                return Phase3ActionPlan()

        p0.bot = PassiveBot(0)
        engine.state.players[1].bot = PassiveBot(1)

        execute_phase_3(engine)

        # Exactly 2 dice should have triaged into scanned_dice; 3 remain in glitched_dice
        self.assertEqual(len(p0.scanned_dice), 2)
        self.assertEqual(len(p0.glitched_dice), 3)

    def test_pipeline_release_bandwidth(self) -> None:
        """INV-PIPE-GRAD-01: At most release_bandwidth dice move from Scanned to Ready per round."""
        cfg = GameConfig(num_players=2)
        engine = GameEngine(cfg, seed=42)
        p0 = engine.state.players[0]
        p0.release_bandwidth = 2
        p0.triage_bandwidth = 0  # Isolate release test
        p0.scanned_dice = [create_gray_die(i + 1) for i in range(4)]
        p0.ready_for_release_dice = []
        p0.glitched_dice = []
        p0.in_production_dice = []

        class PassiveBot(BaseBot):
            def take_phase3_actions(self, p, g, rng):
                return Phase3ActionPlan()

        p0.bot = PassiveBot(0)
        engine.state.players[1].bot = PassiveBot(1)

        execute_phase_3(engine)

        # Exactly 2 dice graduate to ready; 2 remain in scanned
        self.assertEqual(len(p0.ready_for_release_dice), 2)
        self.assertEqual(len(p0.scanned_dice), 2)

    def test_upgrade_pipeline_track(self) -> None:
        """INV-UPGRADE-TRACK-01: Upgrading Pipeline increases triage & release bandwidth and unlocks hotfix."""
        p = PlayerState(player_id=0, bot=BaseBot(0), money=5, secrets=8, patches=10)
        self.assertEqual(p.pipeline_level, 0)
        self.assertEqual(p.triage_bandwidth, 2)
        self.assertEqual(p.release_bandwidth, 2)
        self.assertFalse(p.has_emergency_hotfix)

        # Upgrade Level 0 -> 1 costs 2 research
        self.assertEqual(p.get_track_upgrade_cost("PIPELINE"), 2)
        ok = p.upgrade_track("PIPELINE")
        self.assertTrue(ok)
        self.assertEqual(p.pipeline_level, 1)
        self.assertEqual(p.triage_bandwidth, 3)
        self.assertEqual(p.release_bandwidth, 3)
        self.assertEqual(p.research_tokens, 8)

        # Upgrade Level 1 -> 2 costs 3 research
        self.assertEqual(p.get_track_upgrade_cost("PIPELINE"), 3)
        ok2 = p.upgrade_track("PIPELINE")
        self.assertTrue(ok2)
        self.assertEqual(p.pipeline_level, 2)
        self.assertEqual(p.triage_bandwidth, 4)
        self.assertEqual(p.release_bandwidth, 4)
        self.assertTrue(p.has_emergency_hotfix)
        self.assertEqual(p.research_tokens, 5)

        # Cannot upgrade past Level 2
        self.assertIsNone(p.get_track_upgrade_cost("PIPELINE"))
        self.assertFalse(p.upgrade_track("PIPELINE"))

    def test_upgrade_defense_track(self) -> None:
        """INV-UPGRADE-TRACK-01: Upgrading Defense increases capacity to 3 and 4 + unlocks passive firewall."""
        p = PlayerState(player_id=0, bot=BaseBot(0), money=5, secrets=8, patches=10)
        self.assertEqual(p.defense_level, 0)
        self.assertEqual(p.defense_capacity, 2)
        self.assertFalse(p.has_passive_firewall)

        # Level 0 -> 1
        self.assertEqual(p.get_track_upgrade_cost("DEFENSE"), 2)
        self.assertTrue(p.upgrade_track("DEFENSE"))
        self.assertEqual(p.defense_level, 1)
        self.assertEqual(p.defense_capacity, 3)
        self.assertEqual(p.research_tokens, 8)

        # Level 1 -> 2
        self.assertEqual(p.get_track_upgrade_cost("DEFENSE"), 3)
        self.assertTrue(p.upgrade_track("DEFENSE"))
        self.assertEqual(p.defense_level, 2)
        self.assertEqual(p.defense_capacity, 4)
        self.assertTrue(p.has_passive_firewall)
        self.assertEqual(p.research_tokens, 5)

    def test_patent_conversion_all_levels(self) -> None:
        """INV-PATENT-CONV-01: Filing Cryptographic Patents converts research to Corporate Secrets."""
        p = PlayerState(player_id=0, bot=BaseBot(0), money=5, secrets=8, patches=15)
        # Level 0: costs 4 research
        self.assertEqual(p.get_patent_cost(), 4)
        self.assertTrue(p.file_patent())
        self.assertEqual(p.secrets, 9)
        self.assertEqual(p.research_tokens, 11)

        # Upgrade to Level 1: costs 3 research
        p.upgrade_track("PATENT")
        self.assertEqual(p.patent_level, 1)
        self.assertEqual(p.get_patent_cost(), 3)
        self.assertTrue(p.file_patent())
        self.assertEqual(p.secrets, 10)
        self.assertEqual(p.research_tokens, 11 - 2 - 3)  # 11 - 2 (upgrade) - 3 (patent) = 6

        # Upgrade to Level 2: costs 2 research + awards $1 cash!
        p.upgrade_track("PATENT")
        self.assertEqual(p.patent_level, 2)
        self.assertEqual(p.get_patent_cost(), 2)
        initial_money = p.money
        self.assertTrue(p.file_patent())
        self.assertEqual(p.secrets, 11)
        self.assertEqual(p.money, initial_money + 1)

    def test_corporate_asymmetry_initialization(self) -> None:
        """INV-ASYM-COMPANY-01: When enable_corporate_asymmetry=True, all companies apply distinct hardware and starting assets."""
        cfg = GameConfig(num_players=2, enable_corporate_asymmetry=True)
        # Test Omnidyne
        engine_omni = GameEngine(
            cfg,
            companies=[COMPANIES[CompanyCode.OMNIDYNE], COMPANIES[CompanyCode.AEGIS]],
            white_hats=[WHITE_HATS[WhiteHatCode.PHREAKER], WHITE_HATS[WhiteHatCode.ACOUSTIC]],
        )
        p_omni = engine_omni.state.players[0]
        self.assertEqual(p_omni.defense_capacity, 1, "Omnidyne starts with 1 Defense Capacity")
        self.assertEqual(p_omni.triage_bandwidth, 3, "Omnidyne starts with 3 Triage Bandwidth")
        self.assertEqual(p_omni.release_bandwidth, 3, "Omnidyne starts with 3 Release Bandwidth")
        self.assertEqual(p_omni.pipeline_level, 1)

        # Test Aegis
        p_aegis = engine_omni.state.players[1]
        self.assertEqual(p_aegis.defense_capacity, 3, "Aegis starts with 3 Defense Capacity")
        self.assertEqual(p_aegis.triage_bandwidth, 1, "Aegis starts with 1 Triage Bandwidth")
        self.assertEqual(p_aegis.release_bandwidth, 1, "Aegis starts with 1 Release Bandwidth")
        self.assertEqual(p_aegis.defense_level, 1)

        # Test Meridian: +$2 starting cash
        engine_mer = GameEngine(
            cfg,
            companies=[COMPANIES[CompanyCode.MERIDIAN], COMPANIES[CompanyCode.HELIX]],
            white_hats=[WHITE_HATS[WhiteHatCode.OPERATOR], WHITE_HATS[WhiteHatCode.PRODIGY]],
        )
        p_mer = engine_mer.state.players[0]
        self.assertEqual(p_mer.money, cfg.starting_money + 2, "Meridian starts with +$2 cash")

        # Test Helix: +2 research grant, patent_level=1
        p_helix = engine_mer.state.players[1]
        self.assertEqual(p_helix.research_tokens, 2 + 2, "Helix starts with +2 research tokens")
        self.assertEqual(p_helix.patent_level, 1)

        # Test DTO: +1 starting secret
        engine_dto = GameEngine(
            cfg,
            companies=[COMPANIES[CompanyCode.DTO], COMPANIES[CompanyCode.PROMETHEUS]],
            white_hats=[WHITE_HATS[WhiteHatCode.SPOOK], WHITE_HATS[WhiteHatCode.CIPHER]],
        )
        p_dto = engine_dto.state.players[0]
        self.assertEqual(p_dto.secrets, cfg.get_starting_secrets(2) + 1, "DTO starts with +1 Secret")

        # Test Prometheus: -1 upgrade discount
        p_prom = engine_dto.state.players[1]
        self.assertEqual(p_prom.upgrade_discount, 1)
        self.assertEqual(p_prom.get_track_upgrade_cost("PIPELINE"), 1, "Prometheus upgrades L0->L1 cost 1 research")

    def test_emergency_hotfix_in_phase_3b(self) -> None:
        """INV-UPGRADE-TRACK-01: Level 2 Pipeline hotfixes 1 die directly from Glitched to Ready."""
        cfg = GameConfig(num_players=2)
        engine = GameEngine(cfg, seed=42)
        p0 = engine.state.players[0]
        p0.pipeline_level = 2
        p0.has_emergency_hotfix = True
        p0.glitched_dice = [create_gray_die(1), create_gray_die(2)]
        p0.scanned_dice = []
        p0.ready_for_release_dice = []

        class PassiveBot(BaseBot):
            def take_phase3_actions(self, p, g, rng):
                return Phase3ActionPlan()

        p0.bot = PassiveBot(0)
        engine.state.players[1].bot = PassiveBot(1)

        execute_phase_3(engine)

        # 1 die hotfixed to ready, 1 die triaged to scanned (with bandwidth 4)
        self.assertEqual(len(p0.ready_for_release_dice), 1)
        self.assertEqual(len(p0.scanned_dice), 1)
        self.assertEqual(len(p0.glitched_dice), 0)


if __name__ == "__main__":
    unittest.main()
