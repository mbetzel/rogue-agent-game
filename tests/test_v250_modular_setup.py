"""Unit and Integration Tests for Phase 32: Modular Client Companies & White Hat Dossiers (v0.25.0 Baseline)."""

from __future__ import annotations

import random
import unittest
from typing import Dict, List, Optional, Tuple

from sim.bots.adaptive_balanced import AdaptiveBalancedBot
from sim.bots.base import BaseBot, Phase3ActionPlan
from sim.config import CubeColor, DieColor, GameConfig, ShieldColor, TowerMode
from sim.engine.core import GameEngine
from sim.engine.phase1_boot import (
    check_operator_contingent_staffing,
    detect_hash_matches,
    detect_hash_matches_with_cipher,
    execute_phase_1,
    resolve_prodigy_purple_star_override,
)
from sim.engine.phase2_threat import execute_phase_2
from sim.engine.phase3_ops import (
    collect_player_production_income,
    execute_phase_3,
    resolve_phreaker_jumper_diagnostics,
    resolve_spook_burn_notice,
)
from sim.engine.state import PlayerState, ProductionRole
from sim.entities import (
    AbilityStatus,
    ArchetypeCard,
    ArchetypeCode,
    CANONICAL_COMPANY_FOR_OPERATIVE,
    CANONICAL_OPERATIVE_FOR_COMPANY,
    COMPANIES,
    Company,
    CompanyCode,
    Die,
    Face,
    INTRODUCTORY_PRESETS,
    WHITE_HATS,
    WhiteHat,
    WhiteHatCode,
    create_colored_die,
    create_gray_die,
    create_white_die,
    get_all_companies,
    get_all_white_hats,
    get_archetype_by_code,
    get_company_by_code,
    get_white_hat_by_code,
)
from web.controller.core import GameController
from web.schemas import GameStateSerializer


class TestV250ModularSetup(unittest.TestCase):
    """Exhaustive 28-point unit test matrix for v0.25.0 Modular Client Companies & White Hat Dossiers."""

    # =========================================================================
    # Category 1: Registry Completeness (TEST-MOD-01, TEST-MOD-02)
    # =========================================================================

    def test_mod_01_company_registry_completeness(self) -> None:
        """TEST-MOD-01: Exactly 6 companies with valid codes, sectors, override names, descriptions."""
        self.assertEqual(len(COMPANIES), 6, "There must be exactly 6 companies in COMPANIES registry")
        all_companies = get_all_companies()
        self.assertEqual(len(all_companies), 6)

        expected_codes = {
            CompanyCode.MERIDIAN,
            CompanyCode.OMNIDYNE,
            CompanyCode.AEGIS,
            CompanyCode.DTO,
            CompanyCode.HELIX,
            CompanyCode.PROMETHEUS,
        }
        self.assertEqual(set(COMPANIES.keys()), expected_codes)

        for code in expected_codes:
            comp = get_company_by_code(code)
            self.assertIsNotNone(comp)
            self.assertEqual(comp.code, code)
            self.assertTrue(len(comp.name) > 0, f"Company {code} must have non-empty name")
            self.assertTrue(len(comp.sector) > 0, f"Company {code} must have non-empty sector")
            self.assertTrue(len(comp.override_name) > 0, f"Company {code} must have non-empty override_name")
            self.assertTrue(len(comp.timing_window) > 0, f"Company {code} must have non-empty timing_window")
            self.assertTrue(len(comp.description) > 0, f"Company {code} must have non-empty description")

    def test_mod_02_white_hat_registry_completeness(self) -> None:
        """TEST-MOD-02: Exactly 6 white hats with valid codes, roles, protocol names, descriptions."""
        self.assertEqual(len(WHITE_HATS), 6, "There must be exactly 6 white hats in WHITE_HATS registry")
        all_white_hats = get_all_white_hats()
        self.assertEqual(len(all_white_hats), 6)

        expected_codes = {
            WhiteHatCode.OPERATOR,
            WhiteHatCode.PHREAKER,
            WhiteHatCode.ACOUSTIC,
            WhiteHatCode.SPOOK,
            WhiteHatCode.PRODIGY,
            WhiteHatCode.CIPHER,
        }
        self.assertEqual(set(WHITE_HATS.keys()), expected_codes)

        for code in expected_codes:
            wh = get_white_hat_by_code(code)
            self.assertIsNotNone(wh)
            self.assertEqual(wh.code, code)
            self.assertTrue(len(wh.name) > 0, f"WhiteHat {code} must have non-empty name")
            self.assertTrue(len(wh.role) > 0, f"WhiteHat {code} must have non-empty role")
            self.assertTrue(len(wh.protocol_name) > 0, f"WhiteHat {code} must have non-empty protocol_name")
            self.assertTrue(len(wh.timing_window) > 0, f"WhiteHat {code} must have non-empty timing_window")
            self.assertTrue(len(wh.description) > 0, f"WhiteHat {code} must have non-empty description")

    # =========================================================================
    # Category 2: Invariants INV-SETUP-01..04 (TEST-MOD-03..TEST-MOD-10)
    # =========================================================================

    def test_mod_03_inv_setup_01_modular_split_setup(self) -> None:
        """TEST-MOD-03: INV-SETUP-01: All players receive non-null company and white_hat instances."""
        for num_players in (2, 3, 4):
            engine = GameEngine(config=GameConfig(num_players=num_players), seed=42 + num_players)
            for p in engine.state.players:
                self.assertIsNotNone(p.company, f"Player {p.player_id} must have non-null company")
                self.assertIsInstance(p.company, Company)
                self.assertIsNotNone(p.white_hat, f"Player {p.player_id} must have non-null white_hat")
                self.assertIsInstance(p.white_hat, WhiteHat)

    def test_mod_04_inv_setup_02_unique_assignment_2p(self) -> None:
        """TEST-MOD-04: INV-SETUP-02: Player 1 and Player 2 receive distinct companies and distinct white hats."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=100)
        p0, p1 = engine.state.players[0], engine.state.players[1]
        self.assertNotEqual(p0.company.code, p1.company.code, "2P setup must assign distinct companies")
        self.assertNotEqual(p0.white_hat.code, p1.white_hat.code, "2P setup must assign distinct white hats")

    def test_mod_05_inv_setup_02_unique_assignment_4p(self) -> None:
        """TEST-MOD-05: INV-SETUP-02: All 4 players receive unique companies and unique white hats."""
        engine = GameEngine(config=GameConfig(num_players=4), seed=200)
        company_codes = [p.company.code for p in engine.state.players]
        white_hat_codes = [p.white_hat.code for p in engine.state.players]
        self.assertEqual(len(set(company_codes)), 4, "All 4 players must have unique companies")
        self.assertEqual(len(set(white_hat_codes)), 4, "All 4 players must have unique white hats")

    def test_mod_06_inv_setup_03_orthogonal_cross_pair(self) -> None:
        """TEST-MOD-06: INV-SETUP-03: Successfully pair Meridian with The Spook without state error."""
        meridian = get_company_by_code(CompanyCode.MERIDIAN)
        spook = get_white_hat_by_code(WhiteHatCode.SPOOK)
        player = PlayerState(
            player_id=0,
            bot=AdaptiveBalancedBot(0),
            money=10,
            secrets=10,
            patches=0,
            company=meridian,
            white_hat=spook,
        )
        self.assertEqual(player.company.code, CompanyCode.MERIDIAN)
        self.assertEqual(player.white_hat.code, WhiteHatCode.SPOOK)
        # Verify independence: neither object holds a reference to the other
        self.assertFalse(hasattr(player.company, "white_hat"))
        self.assertFalse(hasattr(player.white_hat, "company"))

    def test_mod_07_inv_setup_03_all_36_combinations(self) -> None:
        """TEST-MOD-07: INV-SETUP-03: Instantiate all 36 combinations of Company x WhiteHat without exception."""
        companies = get_all_companies()
        white_hats = get_all_white_hats()
        self.assertEqual(len(companies), 6)
        self.assertEqual(len(white_hats), 6)

        count = 0
        for comp in companies:
            for wh in white_hats:
                p = PlayerState(
                    player_id=count,
                    bot=AdaptiveBalancedBot(count),
                    money=10,
                    secrets=10,
                    patches=0,
                    company=comp,
                    white_hat=wh,
                )
                self.assertEqual(p.company.code, comp.code)
                self.assertEqual(p.white_hat.code, wh.code)
                self.assertIsNotNone(p.archetype)
                count += 1
        self.assertEqual(count, 36, "Exactly 36 combinations must instantiate successfully")

    def test_mod_08_inv_setup_04_preset_2p_mapping(self) -> None:
        """TEST-MOD-08: INV-SETUP-04: 2P preset assigns Meridian+Operator to P0 and Omnidyne+Phreaker to P1."""
        engine = GameEngine(config=GameConfig(num_players=2), use_introductory_presets=True)
        p0, p1 = engine.state.players[0], engine.state.players[1]
        self.assertEqual(p0.company.code, CompanyCode.MERIDIAN)
        self.assertEqual(p0.white_hat.code, WhiteHatCode.OPERATOR)
        self.assertEqual(p1.company.code, CompanyCode.OMNIDYNE)
        self.assertEqual(p1.white_hat.code, WhiteHatCode.PHREAKER)

    def test_mod_09_inv_setup_04_preset_3p_mapping(self) -> None:
        """TEST-MOD-09: INV-SETUP-04: 3P preset assigns Meridian+Operator, Omnidyne+Phreaker, Aegis+Acoustic."""
        engine = GameEngine(config=GameConfig(num_players=3), use_introductory_presets=True)
        self.assertEqual(engine.state.players[0].company.code, CompanyCode.MERIDIAN)
        self.assertEqual(engine.state.players[0].white_hat.code, WhiteHatCode.OPERATOR)
        self.assertEqual(engine.state.players[1].company.code, CompanyCode.OMNIDYNE)
        self.assertEqual(engine.state.players[1].white_hat.code, WhiteHatCode.PHREAKER)
        self.assertEqual(engine.state.players[2].company.code, CompanyCode.AEGIS)
        self.assertEqual(engine.state.players[2].white_hat.code, WhiteHatCode.ACOUSTIC)

    def test_mod_10_inv_setup_04_preset_4p_mapping(self) -> None:
        """TEST-MOD-10: INV-SETUP-04: 4P preset assigns Meridian+Operator, Omnidyne+Phreaker, Aegis+Acoustic, DTO+Spook."""
        engine = GameEngine(config=GameConfig(num_players=4), use_introductory_presets=True)
        self.assertEqual(engine.state.players[0].company.code, CompanyCode.MERIDIAN)
        self.assertEqual(engine.state.players[0].white_hat.code, WhiteHatCode.OPERATOR)
        self.assertEqual(engine.state.players[1].company.code, CompanyCode.OMNIDYNE)
        self.assertEqual(engine.state.players[1].white_hat.code, WhiteHatCode.PHREAKER)
        self.assertEqual(engine.state.players[2].company.code, CompanyCode.AEGIS)
        self.assertEqual(engine.state.players[2].white_hat.code, WhiteHatCode.ACOUSTIC)
        self.assertEqual(engine.state.players[3].company.code, CompanyCode.DTO)
        self.assertEqual(engine.state.players[3].white_hat.code, WhiteHatCode.SPOOK)

    # =========================================================================
    # Category 3: Invariant INV-OVERRIDE-01 (TEST-MOD-11, TEST-MOD-12)
    # =========================================================================

    def test_mod_11_inv_override_01_lifecycle_v1(self) -> None:
        """TEST-MOD-11: INV-OVERRIDE-01: Company override available in v1.0, marks used, forfeits on upgrade."""
        comp = get_company_by_code(CompanyCode.MERIDIAN)
        wh = get_white_hat_by_code(WhiteHatCode.OPERATOR)
        player = PlayerState(
            player_id=0,
            bot=AdaptiveBalancedBot(0),
            money=10,
            secrets=10,
            patches=0,
            company=comp,
            white_hat=wh,
        )

        self.assertTrue(player.is_ability_available("v1.0"))
        self.assertEqual(player.ability_v1_status, AbilityStatus.AVAILABLE)

        player.mark_ability_used("v1.0")
        self.assertEqual(player.ability_v1_status, AbilityStatus.USED)
        self.assertFalse(player.is_ability_available("v1.0"))

        # Test un-used forfeit behavior on second player
        player2 = PlayerState(
            player_id=1,
            bot=AdaptiveBalancedBot(1),
            money=10,
            secrets=10,
            patches=0,
            company=comp,
            white_hat=wh,
        )
        self.assertTrue(player2.is_ability_available("v1.0"))
        player2.mark_ability_forfeited("v1.0")
        self.assertEqual(player2.ability_v1_status, AbilityStatus.FORFEITED)
        self.assertFalse(player2.is_ability_available("v1.0"))

    def test_mod_12_inv_override_01_version_upgrade(self) -> None:
        """TEST-MOD-12: INV-OVERRIDE-01: Version upgrade unlocks v2.0 override while preserving used status of v1.0."""
        comp = get_company_by_code(CompanyCode.AEGIS)
        wh = get_white_hat_by_code(WhiteHatCode.ACOUSTIC)
        player = PlayerState(
            player_id=0,
            bot=AdaptiveBalancedBot(0),
            money=10,
            secrets=10,
            patches=0,
            company=comp,
            white_hat=wh,
        )

        player.mark_ability_used("v1.0")
        self.assertEqual(player.ability_v1_status, AbilityStatus.USED)

        # Unlock v2.0 upon Rogue Agent version upgrade
        player.unlock_version_ability("v2.0")
        self.assertEqual(player.ability_v2_status, AbilityStatus.AVAILABLE)
        self.assertEqual(player.ability_v1_status, AbilityStatus.USED, "v1.0 used status must remain preserved")
        self.assertTrue(player.is_ability_available("v2.0"))

    # =========================================================================
    # Category 4: Invariant INV-PURPLE-01 (TEST-MOD-13, TEST-MOD-14)
    # =========================================================================

    def test_mod_13_inv_purple_01_reserve_insulation(self) -> None:
        """TEST-MOD-13: INV-PURPLE-01: Purple dice initialize to 2 in reserve and cannot be drafted by opponents."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0, p1 = engine.state.players[0], engine.state.players[1]
        self.assertEqual(p0.personal_purple_reserve, 2)
        self.assertEqual(p1.personal_purple_reserve, 2)

        # Procure for P0
        p0.personal_purple_reserve -= 1
        self.assertEqual(p0.personal_purple_reserve, 1)
        self.assertEqual(p1.personal_purple_reserve, 2, "P1 reserve must be insulated from P0 purchases")

    def test_mod_14_inv_purple_01_protocol_dispatch(self) -> None:
        """TEST-MOD-14: INV-PURPLE-01: Purple ★ triggers operative protocol, not company ability."""
        # Cross pair: Meridian (Company) + Acoustic (White Hat)
        meridian = get_company_by_code(CompanyCode.MERIDIAN)
        acoustic = get_white_hat_by_code(WhiteHatCode.ACOUSTIC)
        player = PlayerState(
            player_id=0,
            bot=AdaptiveBalancedBot(0),
            money=10,
            secrets=10,
            patches=0,
            company=meridian,
            white_hat=acoustic,
        )

        purple_die = create_colored_die(color=DieColor.PURPLE, die_id=99)
        # Set Face 6: Purple Star
        purple_die.current_face = Face(name="Purple Star", is_star=True, star_code="PURPLE_STAR")
        purple_die.production_role = ProductionRole.INCOME
        player.in_production_dice.append(purple_die)

        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        engine.state.last_exited_cubes[CubeColor.RED] = 1
        engine.state.last_exited_cubes[CubeColor.BLUE] = 1
        engine.state.last_exited_cubes[CubeColor.GREEN] = 1

        initial_money = player.money
        collect_player_production_income(engine, player, None)
        # Acoustic protocol bonus = 3 distinct exited colors ($3)
        self.assertGreater(player.money, initial_money, "Acoustic White Hat protocol must trigger")
        # Meridian company ability must NOT be marked used
        self.assertEqual(player.ability_v1_status, AbilityStatus.AVAILABLE)

    # =========================================================================
    # Category 5: Phase 1 Boot Contracts (TEST-MOD-15..TEST-MOD-19)
    # =========================================================================

    def test_mod_15_phase1_meridian_override(self) -> None:
        """TEST-MOD-15: Meridian Override in Phase 1: Redundant Crew hires free White contractors."""
        engine = GameEngine(
            config=GameConfig(num_players=2),
            companies=[get_company_by_code(CompanyCode.MERIDIAN), get_company_by_code(CompanyCode.AEGIS)],
            white_hats=[get_white_hat_by_code(WhiteHatCode.OPERATOR), get_white_hat_by_code(WhiteHatCode.ACOUSTIC)],
            seed=42,
        )
        p0 = engine.state.players[0]
        self.assertEqual(p0.company.code, CompanyCode.MERIDIAN)

        class MeridianBot(BaseBot):
            def choose_meridian_override(self, *args, **kwargs):
                return True

        p0.bot = MeridianBot(0)
        p0.money = 0  # $0 cash, must hire for free
        execute_phase_1(engine)

        self.assertEqual(p0.ability_v1_status, AbilityStatus.USED)
        self.assertEqual(p0.money, 0, "Hiring via Meridian override must cost $0")

    def test_mod_16_phase1_helix_override(self) -> None:
        """TEST-MOD-16: Helix Override in Phase 1: Brute-Force Bypass unlocks locked dice and sets 1 face."""
        engine = GameEngine(
            config=GameConfig(num_players=2),
            companies=[get_company_by_code(CompanyCode.HELIX), get_company_by_code(CompanyCode.AEGIS)],
            white_hats=[get_white_hat_by_code(WhiteHatCode.PRODIGY), get_white_hat_by_code(WhiteHatCode.ACOUSTIC)],
            seed=42,
        )
        p0 = engine.state.players[0]
        self.assertEqual(p0.company.code, CompanyCode.HELIX)

        class HelixBot(BaseBot):
            def choose_helix_override(self, *args, **kwargs):
                return True

            def choose_helix_face_override(self, *args, **kwargs):
                return (0, Face(name="SetFace", money=2))

        p0.bot = HelixBot(0)
        execute_phase_1(engine)
        self.assertEqual(p0.ability_v1_status, AbilityStatus.USED)

    def test_mod_17_phase1_operator_protocol(self) -> None:
        """TEST-MOD-17: Operator Protocol in Phase 1: Rolling Purple ★ rolls 1 free White Contractor die into pool."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        # Give P0 Aegis company + Operator White Hat
        p0 = engine.state.players[0]
        p0.company = get_company_by_code(CompanyCode.AEGIS)
        p0.white_hat = get_white_hat_by_code(WhiteHatCode.OPERATOR)

        class OperatorProtocolBot(BaseBot):
            def choose_operator_contingent_staffing(self, player_state, contractor_supply, rng):
                return True

        p0.bot = OperatorProtocolBot(0)
        active_dice = [create_gray_die(die_id=1)]
        purple_die = create_colored_die(color=DieColor.PURPLE, die_id=2)
        purple_die.current_face = Face(name="Purple Star", is_star=True, star_code="PURPLE_STAR")
        active_dice.append(purple_die)

        initial_contractors = engine.state.contractor_supply
        initial_pool_len = len(active_dice)
        check_operator_contingent_staffing(engine, p0, active_dice)

        self.assertEqual(len(active_dice), initial_pool_len + 1)
        self.assertTrue(any(d.color == DieColor.WHITE for d in active_dice))
        self.assertEqual(engine.state.contractor_supply, initial_contractors - 1)

    def test_mod_18_phase1_prodigy_protocol(self) -> None:
        """TEST-MOD-18: Prodigy Protocol in Phase 1: Rolling Purple ★ overrides 1 active die face to non-Star."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.company = get_company_by_code(CompanyCode.DTO)
        p0.white_hat = get_white_hat_by_code(WhiteHatCode.PRODIGY)

        target_die = create_gray_die(die_id=1)
        target_die.current_face = Face(name="InitialFace", is_glitch=True)
        target_die.is_locked = True
        purple_die = create_colored_die(color=DieColor.PURPLE, die_id=2)
        purple_die.current_face = Face(name="Purple Star", is_star=True, star_code="PURPLE_STAR")
        active_dice = [target_die, purple_die]

        class ProdigyProtocolBot(BaseBot):
            def choose_prodigy_purple_star_override(self, player_state, active_pool, rng):
                return (0, Face(name="OverriddenBlock", block_amount=1, shield_color=ShieldColor.ANY))

        p0.bot = ProdigyProtocolBot(0)
        resolve_prodigy_purple_star_override(p0, active_dice, engine.rng)

        self.assertEqual(target_die.current_face.name, "OverriddenBlock")

    def test_mod_19_phase1_cipher_protocol(self) -> None:
        """TEST-MOD-19: Cipher Protocol in Phase 1: Purple ★ acts as wildcard completing triplet for +1 Secret."""
        p0 = PlayerState(
            player_id=0,
            bot=AdaptiveBalancedBot(0),
            money=10,
            secrets=10,
            patches=0,
            company=get_company_by_code(CompanyCode.MERIDIAN),
            white_hat=get_white_hat_by_code(WhiteHatCode.CIPHER),
        )

        d1 = create_gray_die(die_id=1)
        d1.current_face = Face(name="FaceA", money=1)
        d2 = create_gray_die(die_id=2)
        d2.current_face = Face(name="FaceA", money=1)
        d_purple = create_colored_die(color=DieColor.PURPLE, die_id=3)
        d_purple.current_face = Face(name="Purple Star", is_star=True, star_code="PURPLE_STAR")

        # Plain hash match without Cipher protocol does not count star as match
        plain_matches = detect_hash_matches([d1, d2, d_purple])
        self.assertEqual(plain_matches, 0)

        # Cipher protocol detection treats Purple ★ as wildcard completing pair
        cipher_matches = detect_hash_matches_with_cipher([d1, d2, d_purple], is_cipher=True)
        self.assertEqual(cipher_matches, 1)

    # =========================================================================
    # Category 6: Phase 2 Threat Contracts (TEST-MOD-20, TEST-MOD-21)
    # =========================================================================

    def test_mod_20_phase2_aegis_override(self) -> None:
        """TEST-MOD-20: Aegis Override in Phase 2: Baffle Echo ignores 1 Attack Cube for player."""
        engine = GameEngine(
            config=GameConfig(num_players=2),
            companies=[get_company_by_code(CompanyCode.AEGIS), get_company_by_code(CompanyCode.DTO)],
            white_hats=[get_white_hat_by_code(WhiteHatCode.OPERATOR), get_white_hat_by_code(WhiteHatCode.SPOOK)],
            seed=42,
        )
        p0 = engine.state.players[0]
        self.assertEqual(p0.company.code, CompanyCode.AEGIS)

        class AegisBot(BaseBot):
            def choose_aegis_override(self, player_state, qualifying_colors, exited_cubes, active_version_str, rng, corruption_track=0):
                return CubeColor.BLUE

        p0.bot = AegisBot(0)
        p0.secrets = 8

        # Drop 1 Blue cube into exit tray
        engine.config.tower_mode = TowerMode.FLAT_BINOMIAL
        engine.config.tower_flat_exit_prob = 1.0
        engine.state.staging_cup = {CubeColor.RED: 0, CubeColor.BLUE: 1, CubeColor.GREEN: 0, CubeColor.BLACK: 0}
        engine.state.tower.load_stuck({CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0})
        commitments = [(p, [], {}) for p in engine.state.players]
        execute_phase_2(engine, commitments)

        self.assertEqual(p0.ability_v1_status, AbilityStatus.USED)
        # Baffle Echo ignored the Blue cube, so secrets remained at 8
        self.assertEqual(p0.secrets, 8)

    def test_mod_21_phase2_dto_override(self) -> None:
        """TEST-MOD-21: DTO Override in Phase 2: Slush Fund absorbs up to 2 Secret loss for $0."""
        engine = GameEngine(
            config=GameConfig(num_players=2),
            companies=[get_company_by_code(CompanyCode.DTO), get_company_by_code(CompanyCode.AEGIS)],
            white_hats=[get_white_hat_by_code(WhiteHatCode.PHREAKER), get_white_hat_by_code(WhiteHatCode.ACOUSTIC)],
            seed=42,
        )
        p0 = engine.state.players[0]
        self.assertEqual(p0.company.code, CompanyCode.DTO)

        class DTOBot(BaseBot):
            def choose_dto_override(self, player_state, secrets_at_risk, active_version_str, rng, corruption_track=0):
                return min(2, secrets_at_risk)

        p0.bot = DTOBot(0)
        p0.secrets = 8
        p0.money = 0  # No cash to absorb secrets normally

        # Drop 2 Blue cubes
        engine.config.tower_mode = TowerMode.FLAT_BINOMIAL
        engine.config.tower_flat_exit_prob = 1.0
        engine.state.staging_cup = {CubeColor.RED: 0, CubeColor.BLUE: 2, CubeColor.GREEN: 0, CubeColor.BLACK: 0}
        engine.state.tower.load_stuck({CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0})
        commitments = [(p, [], {}) for p in engine.state.players]
        execute_phase_2(engine, commitments)

        self.assertEqual(p0.ability_v1_status, AbilityStatus.USED)
        self.assertEqual(p0.secrets, 8, "DTO Slush Fund must absorb 2 secrets for $0")

    # =========================================================================
    # Category 7: Phase 3 Ops Contracts (TEST-MOD-22..TEST-MOD-26)
    # =========================================================================

    def test_mod_22_phase3_omnidyne_override(self) -> None:
        """TEST-MOD-22: Omnidyne Override in Phase 3: Magnetic Splice moves die from Glitched directly to Ready."""
        engine = GameEngine(
            config=GameConfig(num_players=2),
            companies=[get_company_by_code(CompanyCode.OMNIDYNE), get_company_by_code(CompanyCode.DTO)],
            white_hats=[get_white_hat_by_code(WhiteHatCode.OPERATOR), get_white_hat_by_code(WhiteHatCode.SPOOK)],
            seed=42,
        )
        p0 = engine.state.players[0]
        self.assertEqual(p0.company.code, CompanyCode.OMNIDYNE)

        glitched_die = create_colored_die(color=DieColor.BLUE, die_id=50)
        p0.glitched_dice.append(glitched_die)

        class OmnidyneBot(BaseBot):
            def choose_omnidyne_override(self, player_state, game_state, rng):
                return 50

            def take_phase3_actions(self, player_state, game_state, rng):
                plan = Phase3ActionPlan()
                plan.use_omnidyne_override = True
                return plan

        p0.bot = OmnidyneBot(0)
        execute_phase_3(engine)

        self.assertEqual(p0.ability_v1_status, AbilityStatus.USED)
        self.assertNotIn(glitched_die, p0.glitched_dice)
        self.assertIn(glitched_die, p0.ready_for_release_dice)

    def test_mod_23_phase3_prometheus_override(self) -> None:
        """TEST-MOD-23: Prometheus Override in Phase 3: Algorithmic Arbitrage applies $2 discount or gives cash."""
        engine = GameEngine(
            config=GameConfig(num_players=2),
            companies=[get_company_by_code(CompanyCode.PROMETHEUS), get_company_by_code(CompanyCode.DTO)],
            white_hats=[get_white_hat_by_code(WhiteHatCode.OPERATOR), get_white_hat_by_code(WhiteHatCode.SPOOK)],
            seed=42,
        )
        p0 = engine.state.players[0]
        self.assertEqual(p0.company.code, CompanyCode.PROMETHEUS)
        p0.money = 5  # Red R1 costs $6; with $2 discount, cost is $4
        engine.state.market[DieColor.RED] = 5

        class PrometheusBot(BaseBot):
            def take_phase3_actions(self, player_state, game_state, rng):
                plan = Phase3ActionPlan()
                plan.use_prometheus_override = True
                plan.prometheus_mode = "BUY_FREE_DIE"
                plan.prometheus_discount_die_color = DieColor.RED
                return plan

        p0.bot = PrometheusBot(0)
        execute_phase_3(engine)

        self.assertEqual(p0.ability_v1_status, AbilityStatus.USED)
        self.assertEqual(p0.money, 1, "Purchasing Red ($6) with $2 discount costs $4 (5 - 4 = 1)")
        self.assertTrue(any(d.color == DieColor.RED for d in p0.ready_for_release_dice))

    def test_mod_24_phase3_acoustic_protocol(self) -> None:
        """TEST-MOD-24: Acoustic Protocol in Phase 3: Resonance Sensor yields +$1 per unique exited cube color."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.company = get_company_by_code(CompanyCode.DTO)
        p0.white_hat = get_white_hat_by_code(WhiteHatCode.ACOUSTIC)

        purple_die = create_colored_die(color=DieColor.PURPLE, die_id=88)
        purple_die.current_face = Face(name="Purple Star", is_star=True, star_code="PURPLE_STAR")
        purple_die.production_role = ProductionRole.INCOME
        p0.in_production_dice.append(purple_die)

        engine.state.last_exited_cubes[CubeColor.RED] = 2
        engine.state.last_exited_cubes[CubeColor.BLUE] = 1
        # 2 unique colors: Red, Blue -> +$2 bonus
        initial_money = p0.money
        collect_player_production_income(engine, p0, None)
        self.assertEqual(p0.money, initial_money + 2)

    def test_mod_25_phase3_phreaker_protocol(self) -> None:
        """TEST-MOD-25: Phreaker Protocol in Phase 3: Jumper Diagnostics rolls offline die for income."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.white_hat = get_white_hat_by_code(WhiteHatCode.PHREAKER)

        diag_die = create_gray_die(die_id=77)
        p0.scanned_dice.append(diag_die)

        class FixedRollRng:
            def choice(self, seq):
                return Face(name="YieldFace", money=2, patches=1)

        face = resolve_phreaker_jumper_diagnostics(engine, p0, 77, FixedRollRng())
        self.assertIsNotNone(face)
        self.assertEqual(face.money, 2)
        self.assertEqual(face.patches, 1)
        self.assertIn(diag_die, p0.scanned_dice, "Die must remain in place after diagnostics")

    def test_mod_26_phase3_spook_protocol(self) -> None:
        """TEST-MOD-26: Spook Protocol in Phase 3: Burn Notice gives +$2 cash and optional die burn for +1 Secret."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.white_hat = get_white_hat_by_code(WhiteHatCode.SPOOK)

        burn_die = create_colored_die(color=DieColor.GREEN, die_id=66)
        p0.glitched_dice.append(burn_die)

        initial_secrets = p0.secrets
        initial_market = engine.state.market.get(DieColor.GREEN, 0)

        success = resolve_spook_burn_notice(engine, p0, 66)
        self.assertTrue(success)
        self.assertEqual(p0.secrets, initial_secrets + 1, "Burning colored die must award +1 Corporate Secret")
        self.assertEqual(engine.state.market[DieColor.GREEN], initial_market + 1, "Burned die must return to market")
        self.assertNotIn(burn_die, p0.glitched_dice)

    # =========================================================================
    # Category 8: Compatibility & Serialization (TEST-MOD-27, TEST-MOD-28)
    # =========================================================================

    def test_mod_27_compatibility_legacy_archetype_bridge(self) -> None:
        """TEST-MOD-27: Legacy player.archetype bridge read/write functions transparently."""
        comp = get_company_by_code(CompanyCode.MERIDIAN)
        wh = get_white_hat_by_code(WhiteHatCode.OPERATOR)
        player = PlayerState(
            player_id=0,
            bot=AdaptiveBalancedBot(0),
            money=10,
            secrets=10,
            patches=0,
            company=comp,
            white_hat=wh,
        )

        # 1. Read backward compatibility
        arch = player.archetype
        self.assertIsNotNone(arch)
        self.assertEqual(arch.code, ArchetypeCode.OPERATOR)

        # 2. Write backward compatibility
        legacy_cipher = get_archetype_by_code(ArchetypeCode.CIPHER)
        player.archetype = legacy_cipher
        self.assertEqual(player.white_hat.code, WhiteHatCode.CIPHER)
        self.assertEqual(player.company.code, CompanyCode.PROMETHEUS)

    def test_mod_28_serialization_web_schema(self) -> None:
        """TEST-MOD-28: Web schema serialization outputs company, white_hat, and archetype."""
        comp = get_company_by_code(CompanyCode.MERIDIAN)
        wh = get_white_hat_by_code(WhiteHatCode.OPERATOR)
        player = PlayerState(
            player_id=0,
            bot=AdaptiveBalancedBot(0),
            money=10,
            secrets=10,
            patches=0,
            company=comp,
            white_hat=wh,
        )

        config = GameConfig()
        serialized = GameStateSerializer.serialize_player(player, config, is_human=True, name="P0")
        self.assertIn("company", serialized)
        self.assertIn("white_hat", serialized)
        self.assertIn("archetype", serialized)

        self.assertEqual(serialized["company"]["code"], "MERIDIAN")
        self.assertEqual(serialized["white_hat"]["code"], "OPERATOR")
        self.assertEqual(serialized["archetype"]["code"], "OPERATOR")


if __name__ == "__main__":
    unittest.main()
