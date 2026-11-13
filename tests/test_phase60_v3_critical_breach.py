"""Unit test suite for Phase 60: Late-Game Patient Zero Threat Escalation (v3.0 Critical Breach).

Tests TC-P60-01 through TC-P60-08 verifying:
- Version-gated Blue exfiltration damage multiplier (INV-P60-01)
- SETEC v3.0 track cube density recalibration (INV-P60-02)
- Macro threat parity & global green cap conservation (INV-P60-03, INV-P60-04)
- Early-game knockout guardrail & v1/v2 damage invariance (INV-P60-05)
- Defensive mitigation and company ability parity in v3.0 (INV-P60-06)
- Backward compatibility and legacy preset parity (INV-P60-07)
"""

from collections import Counter
import itertools
from typing import Dict, List
import unittest

from sim.config import CubeColor, GameConfig, ShieldColor
from sim.engine.core import GameEngine
from sim.engine.phase4_attack_resolution import resolve_player_defense_and_wear
from sim.entities import (
    CompanyCode,
    Face,
    TargetCriterion,
    V038D_V1_STAGING_PAYLOAD,
    VersionCard,
    create_gray_die,
    get_all_companies,
    get_all_version_cards,
)


class TestPhase60V3CriticalBreach(unittest.TestCase):
    """Test suite for Phase 60: Late-Game Patient Zero Threat Escalation (v3.0 Critical Breach)."""

    def _attack(self, blue: int = 0, red: int = 0, green: int = 0) -> Dict[CubeColor, int]:
        return {CubeColor.RED: red, CubeColor.BLUE: blue, CubeColor.GREEN: green}

    def _setup_engine(self, config: GameConfig, active_card: VersionCard, player_secrets: int = 10, player_money: int = 0) -> GameEngine:
        """Helper to create an engine with a single player at specified secrets and active version."""
        engine = GameEngine(config, seed=42)
        engine.state.version_deck = [active_card]
        engine.state.current_version_index = 0
        engine.state.corruption_track = 0
        p0 = engine.state.players[0]
        p0.secrets = player_secrets
        p0.money = player_money
        p0.market_share = 10
        p0.in_production_dice = []
        p0.contractor_dice = []
        p0.unlock_version_ability(active_card.version_str)
        return engine

    def test_tc_p60_01_v3_blue_critical_breach_damage_multiplier(self) -> None:
        """TC-P60-01: v3.0 Blue Critical Breach Damage Multiplier (INV-P60-01).

        Verify that in v3.0, each unblocked Blue cube deals 2 Corporate Secrets damage.
        """
        cards = {c.directive_code: c for c in get_all_version_cards("STANDARD")}
        v3_card = cards["ZERO_DAY_OVERRIDE"]
        cfg = GameConfig.v042(num_players=2)

        # Case A: 1 unblocked Blue cube -> 2 Secrets loss (10 -> 8)
        engine_a = self._setup_engine(cfg, v3_card, player_secrets=10)
        p0_a = engine_a.state.players[0]
        resolve_player_defense_and_wear(
            engine=engine_a,
            player=p0_a,
            rolled_dice=[],
            commitments={},
            attack_strengths=self._attack(blue=1),
            exited_cubes=self._attack(blue=1),
            active_directive="NONE",
        )
        self.assertEqual(p0_a.secrets, 8)
        self.assertFalse(p0_a.is_patient_zero)
        self.assertEqual(p0_a.last_defense_breakdown["blue_damage_multiplier"], 2)
        self.assertEqual(p0_a.last_defense_breakdown["blue_secret_loss"], 2)

        # Case B: 3 unblocked Blue cubes -> 6 Secrets loss (10 -> 4)
        engine_b = self._setup_engine(cfg, v3_card, player_secrets=10)
        p0_b = engine_b.state.players[0]
        resolve_player_defense_and_wear(
            engine=engine_b,
            player=p0_b,
            rolled_dice=[],
            commitments={},
            attack_strengths=self._attack(blue=3),
            exited_cubes=self._attack(blue=3),
            active_directive="NONE",
        )
        self.assertEqual(p0_b.secrets, 4)
        self.assertFalse(p0_b.is_patient_zero)
        self.assertEqual(p0_b.last_defense_breakdown["blue_damage_multiplier"], 2)
        self.assertEqual(p0_b.last_defense_breakdown["blue_secret_loss"], 6)

        # Case C: 5 unblocked Blue cubes -> 10 Secrets loss (10 -> 0), Patient Zero elimination
        engine_c = self._setup_engine(cfg, v3_card, player_secrets=10)
        p0_c = engine_c.state.players[0]
        resolve_player_defense_and_wear(
            engine=engine_c,
            player=p0_c,
            rolled_dice=[],
            commitments={},
            attack_strengths=self._attack(blue=5),
            exited_cubes=self._attack(blue=5),
            active_directive="NONE",
        )
        self.assertEqual(p0_c.secrets, 0)
        self.assertTrue(p0_c.is_patient_zero)
        self.assertEqual(p0_c.elimination_reason, "Total Breach (<= 0 Secrets)")
        self.assertEqual(p0_c.last_defense_breakdown["blue_damage_multiplier"], 2)
        self.assertEqual(p0_c.last_defense_breakdown["blue_secret_loss"], 10)

    def test_tc_p60_02_v1_and_v2_standard_blue_damage_invariance(self) -> None:
        """TC-P60-02: v1.0 and v2.0 Standard Blue Damage Invariance (INV-P60-01, INV-P60-05).

        Verify that v3_blue_secret_damage = 2 has zero effect outside of v3.0.
        """
        cards = {c.directive_code: c for c in get_all_version_cards("STANDARD")}
        v1_card = cards["SCRIPT_KIDDIE"]
        v2_card = cards["RAAS"]
        cfg = GameConfig.v042(num_players=2)

        # Case A: v1.0 active, 2 unblocked Blue cubes -> 2 Secrets loss (8 -> 6)
        engine_a = self._setup_engine(cfg, v1_card, player_secrets=8)
        p0_a = engine_a.state.players[0]
        resolve_player_defense_and_wear(
            engine=engine_a,
            player=p0_a,
            rolled_dice=[],
            commitments={},
            attack_strengths=self._attack(blue=2),
            exited_cubes=self._attack(blue=2),
            active_directive="NONE",
        )
        self.assertEqual(p0_a.secrets, 6)
        self.assertEqual(p0_a.last_defense_breakdown["blue_damage_multiplier"], 1)
        self.assertEqual(p0_a.last_defense_breakdown["blue_secret_loss"], 2)

        # Case B: v2.0 active, 2 unblocked Blue cubes -> 2 Secrets loss (8 -> 6)
        engine_b = self._setup_engine(cfg, v2_card, player_secrets=8)
        p0_b = engine_b.state.players[0]
        resolve_player_defense_and_wear(
            engine=engine_b,
            player=p0_b,
            rolled_dice=[],
            commitments={},
            attack_strengths=self._attack(blue=2),
            exited_cubes=self._attack(blue=2),
            active_directive="NONE",
        )
        self.assertEqual(p0_b.secrets, 6)
        self.assertEqual(p0_b.last_defense_breakdown["blue_damage_multiplier"], 1)
        self.assertEqual(p0_b.last_defense_breakdown["blue_secret_loss"], 2)

    def test_tc_p60_03_v3_corruption_track_card_payloads_standard_profile(self) -> None:
        """TC-P60-03: v3.0 Corruption Track Card Payloads (Standard Profile) (INV-P60-02)."""
        cards = {c.directive_code: c for c in get_all_version_cards(profile="STANDARD")}
        zd = cards["ZERO_DAY_OVERRIDE"]
        ck = cards["CORRUPTED_KERNEL"]

        # ZERO_DAY_OVERRIDE Space 1 & Space 3
        self.assertEqual(zd.corruption_track[0].index, 1)
        self.assertEqual(
            zd.corruption_track[0].add_cubes,
            {CubeColor.RED: 1, CubeColor.BLUE: 2, CubeColor.GREEN: 1},
        )
        self.assertEqual(zd.corruption_track[2].index, 3)
        self.assertEqual(
            zd.corruption_track[2].add_cubes,
            {CubeColor.RED: 1, CubeColor.BLUE: 2},
        )

        # CORRUPTED_KERNEL Space 1 & Space 3
        self.assertEqual(ck.corruption_track[0].index, 1)
        self.assertEqual(
            ck.corruption_track[0].add_cubes,
            {CubeColor.RED: 1, CubeColor.BLUE: 2},
        )
        self.assertEqual(ck.corruption_track[0].demote_dice, 1)
        self.assertEqual(ck.corruption_track[0].target_criterion, TargetCriterion.FEWEST_GLITCHED)

        self.assertEqual(ck.corruption_track[2].index, 3)
        self.assertEqual(
            ck.corruption_track[2].add_cubes,
            {CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 1},
        )

        # Non-cube hazards on Spaces 1-6 match v0.41 baseline bit-for-bit
        legacy_cards = {c.directive_code: c for c in get_all_version_cards(profile="V041_STANDARD")}
        legacy_zd = legacy_cards["ZERO_DAY_OVERRIDE"]
        legacy_ck = legacy_cards["CORRUPTED_KERNEL"]

        for s_new, s_leg in zip(zd.corruption_track, legacy_zd.corruption_track):
            self.assertEqual(s_new.lose_money, s_leg.lose_money)
            self.assertEqual(s_new.lose_patches, s_leg.lose_patches)
            self.assertEqual(s_new.lose_secrets, s_leg.lose_secrets)
            self.assertEqual(s_new.lose_market_share, s_leg.lose_market_share)
            self.assertEqual(s_new.demote_dice, s_leg.demote_dice)
            self.assertEqual(s_new.return_colored_dice, s_leg.return_colored_dice)
            self.assertEqual(s_new.is_singularity, s_leg.is_singularity)

        for s_new, s_leg in zip(ck.corruption_track, legacy_ck.corruption_track):
            self.assertEqual(s_new.lose_money, s_leg.lose_money)
            self.assertEqual(s_new.lose_patches, s_leg.lose_patches)
            self.assertEqual(s_new.lose_secrets, s_leg.lose_secrets)
            self.assertEqual(s_new.lose_market_share, s_leg.lose_market_share)
            self.assertEqual(s_new.demote_dice, s_leg.demote_dice)
            self.assertEqual(s_new.return_colored_dice, s_leg.return_colored_dice)
            self.assertEqual(s_new.is_singularity, s_leg.is_singularity)

    def test_tc_p60_04_v3_corruption_track_card_payloads_aggressive_profile(self) -> None:
        """TC-P60-04: v3.0 Corruption Track Card Payloads (Aggressive Profile) (INV-P60-02)."""
        cards = {c.directive_code: c for c in get_all_version_cards(profile="AGGRESSIVE")}
        zd = cards["ZERO_DAY_OVERRIDE"]
        ck = cards["CORRUPTED_KERNEL"]

        # ZERO_DAY_OVERRIDE Space 1 has 2 Blue, Space 3 has 2 Blue
        self.assertEqual(zd.corruption_track[0].add_cubes[CubeColor.BLUE], 2)
        self.assertEqual(zd.corruption_track[2].add_cubes[CubeColor.BLUE], 2)

        # CORRUPTED_KERNEL Space 1 has 2 Blue, Space 3 has 1 Blue
        self.assertEqual(ck.corruption_track[0].add_cubes[CubeColor.BLUE], 2)
        self.assertEqual(ck.corruption_track[2].add_cubes[CubeColor.BLUE], 1)

        # Aggressive hazards intact
        self.assertEqual(zd.corruption_track[1].lose_money, 4)
        self.assertEqual(zd.corruption_track[1].lose_patches, 2)
        self.assertEqual(ck.corruption_track[0].demote_dice, 2)

    def test_tc_p60_05_macro_threat_parity_and_global_green_cap_conservation(self) -> None:
        """TC-P60-05: Macro Threat Parity & Global Green Cap Conservation (INV-P60-03, INV-P60-04)."""
        for profile in ("STANDARD", "AGGRESSIVE"):
            cards = {c.directive_code: c for c in get_all_version_cards(profile=profile)}
            v1_cards = [cards["SCRIPT_KIDDIE"], cards["DATA_SCRAPER"]]
            v2_cards = [cards["RAAS"], cards["POLYMORPHIC_WORM"]]
            v3_cards = [cards["ZERO_DAY_OVERRIDE"], cards["CORRUPTED_KERNEL"]]

            decks = list(itertools.product(v1_cards, v2_cards, v3_cards))
            self.assertEqual(len(decks), 8)

            red_counts: List[int] = []
            blue_counts: List[int] = []
            green_counts: List[int] = []
            black_counts: List[int] = []

            for v1, v2, v3 in decks:
                counts: Counter[CubeColor] = Counter(V038D_V1_STAGING_PAYLOAD[v1.directive_code])
                counts[CubeColor.BLACK] += 1  # Round 1 setup pulse

                for card in (v1, v2, v3):
                    for space in card.corruption_track:
                        counts.update(space.add_cubes)

                red_counts.append(counts[CubeColor.RED])
                blue_counts.append(counts[CubeColor.BLUE])
                green_counts.append(counts[CubeColor.GREEN])
                black_counts.append(counts[CubeColor.BLACK])

                attack_cubes = counts[CubeColor.RED] + counts[CubeColor.BLUE] + counts[CubeColor.GREEN]
                total_cubes = attack_cubes + counts[CubeColor.BLACK]

                if v3.directive_code == "ZERO_DAY_OVERRIDE":
                    self.assertEqual(attack_cubes, 17)
                    self.assertEqual(total_cubes, 23)
                elif v3.directive_code == "CORRUPTED_KERNEL":
                    self.assertEqual(attack_cubes, 15)
                    self.assertEqual(total_cubes, 21)

            # Assertions across canonical decks
            self.assertTrue(all(k == 6 for k in black_counts))
            self.assertEqual((min(blue_counts), max(blue_counts)), (5, 8))
            self.assertAlmostEqual(sum(blue_counts) / len(blue_counts), 6.50)
            self.assertEqual((min(red_counts), max(red_counts)), (4, 8))
            self.assertAlmostEqual(sum(red_counts) / len(red_counts), 6.00)
            self.assertEqual((min(green_counts), max(green_counts)), (2, 5))
            self.assertAlmostEqual(sum(green_counts) / len(green_counts), 3.50)
            self.assertLessEqual(max(green_counts), 5)

    def test_tc_p60_06_defense_grid_shield_absorption_parity_in_v3(self) -> None:
        """TC-P60-06: Defense Grid Shield Absorption Parity in v3.0 (INV-P60-06).

        1 Generic shield assigned to Blue absorbs 1 Blue cube, preventing 2 Secrets loss.
        """
        cards = {c.directive_code: c for c in get_all_version_cards("STANDARD")}
        v3_card = cards["ZERO_DAY_OVERRIDE"]
        cfg = GameConfig.v042(num_players=2)

        engine = self._setup_engine(cfg, v3_card, player_secrets=10)
        p0 = engine.state.players[0]

        # Deploy 1 Generic (Any) Shield die
        gray_die = create_gray_die(1)
        shield_face = Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)
        gray_die.faces = [shield_face] * 6
        gray_die.current_face = shield_face

        # Allocate 1 Any shield to Blue
        resolve_player_defense_and_wear(
            engine=engine,
            player=p0,
            rolled_dice=[gray_die],
            commitments={0: ShieldColor.ANY},
            attack_strengths=self._attack(blue=2),
            exited_cubes=self._attack(blue=2),
            active_directive="NONE",
            any_shield_allocations={CubeColor.BLUE: 1},
        )

        # 1 Blue blocked by Generic shield, 1 Blue unblocked -> 1 * 2 = 2 Secrets loss (10 -> 8)
        self.assertEqual(p0.secrets, 8)
        bd = p0.last_defense_breakdown
        self.assertEqual(bd["blocked"]["blue"], 1)
        self.assertEqual(bd["unblocked"]["blue"], 1)
        self.assertEqual(bd["blue_damage_multiplier"], 2)
        self.assertEqual(bd["blue_secret_loss"], 2)

    def test_tc_p60_07_client_company_ability_overrides_in_v3(self) -> None:
        """TC-P60-07: Client Company Ability Overrides in v3.0 (Aegis & DTO) (INV-P60-06)."""
        cards = {c.directive_code: c for c in get_all_version_cards("STANDARD")}
        v3_card = cards["ZERO_DAY_OVERRIDE"]
        cfg = GameConfig.v042(num_players=2)
        comps = {c.code: c for c in get_all_companies()}

        # Case A: Aegis Defense Relay (Baffle Echo)
        engine_a = self._setup_engine(cfg, v3_card, player_secrets=10)
        p_aegis = engine_a.state.players[0]
        p_aegis.company = comps[CompanyCode.AEGIS]
        self.assertTrue(p_aegis.is_ability_available("v3.0"))

        resolve_player_defense_and_wear(
            engine=engine_a,
            player=p_aegis,
            rolled_dice=[],
            commitments={},
            attack_strengths=self._attack(blue=2),
            exited_cubes=self._attack(blue=2),
            active_directive="NONE",
            aegis_color_override=CubeColor.BLUE,
        )
        # Baffle Echo ignored 1 Blue; 1 unblocked Blue resolves at 2 Secrets loss (10 -> 8)
        self.assertEqual(p_aegis.secrets, 8)
        self.assertFalse(p_aegis.is_ability_available("v3.0"))

        # Case B: DTO (Slush Fund) Single Cube
        engine_b = self._setup_engine(cfg, v3_card, player_secrets=10, player_money=0)
        p_dto_b = engine_b.state.players[0]
        p_dto_b.company = comps[CompanyCode.DTO]
        self.assertTrue(p_dto_b.is_slush_fund_available("v3.0"))

        resolve_player_defense_and_wear(
            engine=engine_b,
            player=p_dto_b,
            rolled_dice=[],
            commitments={},
            attack_strengths=self._attack(blue=1),
            exited_cubes=self._attack(blue=1),
            active_directive="NONE",
            slush_fund_override=True,
        )
        # 1 unblocked Blue = 2 Secrets loss. Slush Fund absorbs min(2, 2) = 2 Secrets free.
        self.assertEqual(p_dto_b.secrets, 10)
        self.assertFalse(p_dto_b.is_slush_fund_available("v3.0"))

        # Case C: DTO (Slush Fund) Multiple Cubes + Cash
        engine_c = self._setup_engine(cfg, v3_card, player_secrets=10, player_money=2)
        p_dto_c = engine_c.state.players[0]
        p_dto_c.company = comps[CompanyCode.DTO]
        self.assertTrue(p_dto_c.is_slush_fund_available("v3.0"))

        resolve_player_defense_and_wear(
            engine=engine_c,
            player=p_dto_c,
            rolled_dice=[],
            commitments={},
            attack_strengths=self._attack(blue=2),
            exited_cubes=self._attack(blue=2),
            active_directive="NONE",
            slush_fund_override=True,
        )
        # 2 unblocked Blue = 4 Secrets loss. Slush Fund absorbs 2 Secrets free, then $2 cash absorbs 2 Secrets.
        self.assertEqual(p_dto_c.secrets, 10)
        self.assertEqual(p_dto_c.money, 0)
        self.assertFalse(p_dto_c.is_slush_fund_available("v3.0"))

    def test_tc_p60_08_backward_compatibility_and_legacy_preset_parity(self) -> None:
        """TC-P60-08: Backward Compatibility & Legacy Preset Parity (INV-P60-07)."""
        cards = {c.directive_code: c for c in get_all_version_cards("STANDARD")}
        v3_card = cards["ZERO_DAY_OVERRIDE"]

        # GameConfig.v040() sets v3_blue_secret_damage = 1
        cfg_v040 = GameConfig.v040(num_players=2)
        self.assertEqual(cfg_v040.v3_blue_secret_damage, 1)

        engine = self._setup_engine(cfg_v040, v3_card, player_secrets=10)
        p0 = engine.state.players[0]
        resolve_player_defense_and_wear(
            engine=engine,
            player=p0,
            rolled_dice=[],
            commitments={},
            attack_strengths=self._attack(blue=2),
            exited_cubes=self._attack(blue=2),
            active_directive="NONE",
        )
        # 2 unblocked Blue * 1 legacy damage = 2 Secrets loss (10 -> 8)
        self.assertEqual(p0.secrets, 8)
        self.assertEqual(p0.last_defense_breakdown["blue_damage_multiplier"], 1)
        self.assertEqual(p0.last_defense_breakdown["blue_secret_loss"], 2)

        # Legacy / v041 card loading preserves [3, 6] Blue cube bounds
        for profile in ("V041_STANDARD", "V041_AGGRESSIVE"):
            leg_cards = {c.directive_code: c for c in get_all_version_cards(profile=profile)}
            v1_cards = [leg_cards["SCRIPT_KIDDIE"], leg_cards["DATA_SCRAPER"]]
            v2_cards = [leg_cards["RAAS"], leg_cards["POLYMORPHIC_WORM"]]
            v3_cards = [leg_cards["ZERO_DAY_OVERRIDE"], leg_cards["CORRUPTED_KERNEL"]]

            blue_counts: List[int] = []
            for v1, v2, v3 in itertools.product(v1_cards, v2_cards, v3_cards):
                counts: Counter[CubeColor] = Counter(V038D_V1_STAGING_PAYLOAD[v1.directive_code])
                for card in (v1, v2, v3):
                    for space in card.corruption_track:
                        counts.update(space.add_cubes)
                blue_counts.append(counts[CubeColor.BLUE])

            self.assertEqual((min(blue_counts), max(blue_counts)), (3, 6))


if __name__ == "__main__":
    unittest.main()
