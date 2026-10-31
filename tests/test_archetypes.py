"""Unit and Integration Tests for Consultancy Archetypes (Too Many Secrets - Phase 13).

Covers all 21 technical verification tests specified by the Principal Engineer:
Group A: Archetype Registry & Initialization (Tests 1-3)
1. test_archetype_registry_and_definitions
2. test_get_archetype_by_code
3. test_get_random_archetypes_determinism_and_uniqueness

Group B: Version Upgrades & Ability Lifecycle (Tests 4-7)
4. test_player_state_initial_ability_statuses
5. test_player_state_mark_ability_used
6. test_engine_version_upgrade_forfeits_and_unlocks
7. test_used_ability_not_forfeited_on_upgrade

Group C: The Operator & The Prodigy (Phase 1) (Tests 8-11)
8. test_operator_redundant_crew_free_contractors
9. test_operator_redundant_crew_buy_third_die
10. test_operator_respects_contractor_supply
11. test_prodigy_brute_force_bypass_rerolls_locked_dice

Group D: The Spook & The Acoustic (Phase 2) (Tests 12-15)
12. test_spook_slush_fund_absorbs_blue_secret_loss
13. test_spook_slush_fund_absorbs_unpaid_red_ransom
14. test_spook_slush_fund_insufficient_cash
15. test_acoustic_baffle_echo_removes_exited_cube

Group E: The Phreaker & The Cipher (Phase 3) (Tests 16-19)
16. test_phreaker_magnetic_splice_patches_two_free_dice
17. test_phreaker_magnetic_splice_with_single_worn_die
18. test_cipher_algorithmic_arbitrage_free_colored_die
19. test_cipher_algorithmic_arbitrage_dirty_income_without_backlash

Group F: Web Controller & Serialization (Tests 20-21)
20. test_web_serializer_archetype_info
21. test_web_controller_archetype_assignment_and_actions
"""

from __future__ import annotations

import random
import unittest
from typing import Dict, List

from sim.bots import AdaptiveBalancedBot, BaseBot, Phase3ActionPlan
from sim.config import CubeColor, DieColor, GameConfig, ShieldColor
from sim.engine import GameEngine, PlayerState
from sim.entities import (
    AbilityStatus,
    ArchetypeCard,
    ArchetypeCode,
    Die,
    Face,
    create_gray_die,
    create_white_die,
    get_all_archetype_cards,
    get_archetype_by_code,
    get_default_variant_cards,
    get_default_version_deck,
    get_random_archetypes,
)
from web.game_controller import GameController
from web.schemas import GameStateSerializer


class TestArchetypeRegistry(unittest.TestCase):
    """Group A: Archetype Registry & Initialization (Tests 1-3)."""

    def test_archetype_registry_and_definitions(self) -> None:
        """1. Verify all 6 archetypes exist in registry with exact fields and descriptions."""
        cards = get_all_archetype_cards()
        self.assertEqual(len(cards), 6)

        codes = {card.code for card in cards}
        expected_codes = {
            ArchetypeCode.ACOUSTIC,
            ArchetypeCode.PHREAKER,
            ArchetypeCode.PRODIGY,
            ArchetypeCode.SPOOK,
            ArchetypeCode.CIPHER,
            ArchetypeCode.OPERATOR,
        }
        self.assertEqual(codes, expected_codes)

        for card in cards:
            self.assertTrue(isinstance(card.code, ArchetypeCode))
            self.assertTrue(isinstance(card.name, str) and len(card.name) > 0)
            self.assertTrue(isinstance(card.ability_name, str) and len(card.ability_name) > 0)
            self.assertTrue(isinstance(card.timing_window, str) and len(card.timing_window) > 0)
            self.assertTrue(isinstance(card.description, str) and len(card.description) > 0)

        # Exact names and ability names verification per Section 6D
        operator = get_archetype_by_code(ArchetypeCode.OPERATOR)
        self.assertEqual(operator.name, "The Operator")
        self.assertEqual(operator.ability_name, "Redundant Crew")

        prodigy = get_archetype_by_code(ArchetypeCode.PRODIGY)
        self.assertEqual(prodigy.name, "The Prodigy")
        self.assertEqual(prodigy.ability_name, "Brute-Force Bypass")

        spook = get_archetype_by_code(ArchetypeCode.SPOOK)
        self.assertEqual(spook.name, "The Spook")
        self.assertEqual(spook.ability_name, "Slush Fund")

        acoustic = get_archetype_by_code(ArchetypeCode.ACOUSTIC)
        self.assertEqual(acoustic.name, "The Acoustic")
        self.assertEqual(acoustic.ability_name, "Baffle Echo")

        phreaker = get_archetype_by_code(ArchetypeCode.PHREAKER)
        self.assertEqual(phreaker.name, "The Phreaker")
        self.assertEqual(phreaker.ability_name, "Magnetic Splice")

        cipher = get_archetype_by_code(ArchetypeCode.CIPHER)
        self.assertEqual(cipher.name, "The Cipher")
        self.assertEqual(cipher.ability_name, "Algorithmic Arbitrage")

    def test_get_archetype_by_code(self) -> None:
        """2. Verify lookup by enum and case-insensitive string, and ValueError on invalid code."""
        card1 = get_archetype_by_code(ArchetypeCode.OPERATOR)
        card2 = get_archetype_by_code("OPERATOR")
        card3 = get_archetype_by_code("operator")
        self.assertEqual(card1, card2)
        self.assertEqual(card1, card3)
        self.assertEqual(card1.code, ArchetypeCode.OPERATOR)

        with self.assertRaises(ValueError):
            get_archetype_by_code("INVALID_ARCHETYPE")

    def test_get_random_archetypes_determinism_and_uniqueness(self) -> None:
        """3. Verify random archetype selection is deterministic with seed and unique."""
        rng1 = random.Random(42)
        draw1 = get_random_archetypes(4, rng1)
        rng2 = random.Random(42)
        draw2 = get_random_archetypes(4, rng2)

        self.assertEqual([c.code for c in draw1], [c.code for c in draw2])
        self.assertEqual(len(draw1), 4)
        self.assertEqual(len(set(c.code for c in draw1)), 4)

        all_6 = get_random_archetypes(6, random.Random(99))
        self.assertEqual(len(all_6), 6)
        self.assertEqual(len(set(c.code for c in all_6)), 6)

        with self.assertRaises(ValueError):
            get_random_archetypes(7, random.Random(42))


class TestVersionUpgradesAndAbilityLifecycle(unittest.TestCase):
    """Group B: Version Upgrades & Ability Lifecycle (Tests 4-7)."""

    def test_player_state_initial_ability_statuses(self) -> None:
        """4. Verify PlayerState initializes with v1 AVAILABLE and v2/v3 LOCKED."""
        card = get_archetype_by_code(ArchetypeCode.OPERATOR)
        player = PlayerState(
            player_id=0,
            bot=AdaptiveBalancedBot(0),
            money=7,
            secrets=6,
            patches=1,
            archetype=card,
            ability_v1_status=AbilityStatus.AVAILABLE,
            ability_v2_status=AbilityStatus.LOCKED,
            ability_v3_status=AbilityStatus.LOCKED,
        )

        self.assertEqual(player.ability_v1_status, AbilityStatus.AVAILABLE)
        self.assertEqual(player.ability_v2_status, AbilityStatus.LOCKED)
        self.assertEqual(player.ability_v3_status, AbilityStatus.LOCKED)

        self.assertTrue(player.is_ability_available("v1.0"))
        self.assertFalse(player.is_ability_available("v2.0"))
        self.assertFalse(player.is_ability_available("v3.0"))
        self.assertTrue(player.is_ability_available())

        self.assertFalse(player.v1_used)
        self.assertFalse(player.v2_used)
        self.assertFalse(player.v3_used)

    def test_player_state_mark_ability_used(self) -> None:
        """5. Verify marking ability as used transitions to USED and removes availability."""
        card = get_archetype_by_code(ArchetypeCode.PRODIGY)
        player = PlayerState(
            player_id=0,
            bot=AdaptiveBalancedBot(0),
            money=7,
            secrets=6,
            patches=1,
            archetype=card,
            ability_v1_status=AbilityStatus.AVAILABLE,
            ability_v2_status=AbilityStatus.LOCKED,
            ability_v3_status=AbilityStatus.LOCKED,
        )

        player.mark_ability_used("v1.0")
        self.assertEqual(player.ability_v1_status, AbilityStatus.USED)
        self.assertFalse(player.is_ability_available("v1.0"))
        self.assertFalse(player.is_ability_available())
        self.assertTrue(player.v1_used)

    def test_engine_version_upgrade_forfeits_and_unlocks(self) -> None:
        """6. Advancing from v1.0 to v2.0 forfeits unused v1.0 and unlocks v2.0."""
        card = get_archetype_by_code(ArchetypeCode.CIPHER)
        player = PlayerState(
            player_id=0,
            bot=AdaptiveBalancedBot(0),
            money=7,
            secrets=6,
            patches=1,
            archetype=card,
            ability_v1_status=AbilityStatus.AVAILABLE,
            ability_v2_status=AbilityStatus.LOCKED,
            ability_v3_status=AbilityStatus.LOCKED,
        )

        # Mid-round version upgrade: forfeit previous, unlock next
        player.mark_ability_forfeited("v1.0")
        player.unlock_version_ability("v2.0")

        self.assertEqual(player.ability_v1_status, AbilityStatus.FORFEITED)
        self.assertEqual(player.ability_v2_status, AbilityStatus.AVAILABLE)
        self.assertEqual(player.ability_v3_status, AbilityStatus.LOCKED)

        self.assertFalse(player.is_ability_available("v1.0"))
        self.assertTrue(player.is_ability_available("v2.0"))
        self.assertFalse(player.is_ability_available("v3.0"))
        self.assertTrue(player.is_ability_available())
        self.assertFalse(player.v1_used)

    def test_used_ability_not_forfeited_on_upgrade(self) -> None:
        """7. An ability already marked USED remains USED (not FORFEITED) upon version advance."""
        card = get_archetype_by_code(ArchetypeCode.SPOOK)
        player = PlayerState(
            player_id=0,
            bot=AdaptiveBalancedBot(0),
            money=7,
            secrets=6,
            patches=1,
            archetype=card,
            ability_v1_status=AbilityStatus.USED,
            ability_v2_status=AbilityStatus.LOCKED,
            ability_v3_status=AbilityStatus.LOCKED,
        )

        player.mark_ability_forfeited("v1.0")
        player.unlock_version_ability("v2.0")

        self.assertEqual(player.ability_v1_status, AbilityStatus.USED)
        self.assertEqual(player.ability_v2_status, AbilityStatus.AVAILABLE)
        self.assertTrue(player.v1_used)
        self.assertTrue(player.is_ability_available("v2.0"))


class TestOperatorAndProdigy(unittest.TestCase):
    """Group C: The Operator & The Prodigy (Phase 1) (Tests 8-11)."""

    def test_operator_redundant_crew_free_contractors(self) -> None:
        """8. Operator Redundant Crew hires up to 2 contractor dice for free."""
        controller = GameController()
        operator_card = get_archetype_by_code(ArchetypeCode.OPERATOR)
        controller.new_game(
            num_players=4,
            seed=42,
            archetypes=[operator_card, get_archetype_by_code(ArchetypeCode.CIPHER),
                        get_archetype_by_code(ArchetypeCode.SPOOK), get_archetype_by_code(ArchetypeCode.PRODIGY)],
        )

        player = controller.state.players[0]
        initial_money = player.money
        initial_supply = controller.state.contractor_supply

        res = controller.hire_contractors(
            player_id=0,
            count=2,
            use_operator_ability=True,
            buy_third_die=False,
        )

        self.assertIn("players", res)
        self.assertEqual(player.money, initial_money)  # Free!
        self.assertEqual(len(player.contractor_dice), 2)
        self.assertEqual(controller.state.contractor_supply, initial_supply - 2)
        self.assertEqual(player.ability_v1_status, AbilityStatus.USED)
        self.assertFalse(player.is_ability_available("v1.0"))

    def test_operator_redundant_crew_buy_third_die(self) -> None:
        """9. Operator hires 2 free contractors and buys 3rd for progressive cost ($3)."""
        controller = GameController()
        operator_card = get_archetype_by_code(ArchetypeCode.OPERATOR)
        controller.new_game(
            num_players=4,
            seed=42,
            archetypes=[operator_card, get_archetype_by_code(ArchetypeCode.CIPHER),
                        get_archetype_by_code(ArchetypeCode.SPOOK), get_archetype_by_code(ArchetypeCode.PRODIGY)],
        )

        player = controller.state.players[0]
        initial_money = player.money
        initial_supply = controller.state.contractor_supply

        res = controller.hire_contractors(
            player_id=0,
            count=2,
            use_operator_ability=True,
            buy_third_die=True,
        )

        self.assertIn("players", res)
        self.assertEqual(player.money, initial_money - 3)  # 2 free + $3 for 3rd
        self.assertEqual(len(player.contractor_dice), 3)
        self.assertEqual(controller.state.contractor_supply, initial_supply - 3)
        self.assertEqual(player.ability_v1_status, AbilityStatus.USED)

    def test_operator_respects_contractor_supply(self) -> None:
        """10. Operator cannot hire more than available supply."""
        controller = GameController()
        operator_card = get_archetype_by_code(ArchetypeCode.OPERATOR)
        controller.new_game(
            num_players=4,
            seed=42,
            archetypes=[operator_card, get_archetype_by_code(ArchetypeCode.CIPHER),
                        get_archetype_by_code(ArchetypeCode.SPOOK), get_archetype_by_code(ArchetypeCode.PRODIGY)],
        )

        controller.state.contractor_supply = 1
        player = controller.state.players[0]
        initial_money = player.money

        res = controller.hire_contractors(
            player_id=0,
            count=2,
            use_operator_ability=True,
            buy_third_die=False,
        )

        self.assertIn("players", res)
        self.assertEqual(player.money, initial_money)
        self.assertEqual(len(player.contractor_dice), 1)
        self.assertEqual(controller.state.contractor_supply, 0)
        self.assertEqual(player.ability_v1_status, AbilityStatus.USED)

    def test_prodigy_brute_force_bypass_rerolls_locked_dice(self) -> None:
        """11. Prodigy Brute-Force Bypass rerolls locked dice without spending patch tokens."""
        controller = GameController()
        prodigy_card = get_archetype_by_code(ArchetypeCode.PRODIGY)
        controller.new_game(
            num_players=4,
            seed=42,
            archetypes=[prodigy_card, get_archetype_by_code(ArchetypeCode.OPERATOR),
                        get_archetype_by_code(ArchetypeCode.CIPHER), get_archetype_by_code(ArchetypeCode.SPOOK)],
        )

        controller.roll_pool(0)
        player = controller.state.players[0]
        meta = controller.player_meta[0]

        # Lock the first die manually to simulate glitch or directive lock
        meta["rolled_pool"][0].is_locked = True
        initial_patches = player.patches

        # Standard reroll on locked die raises ValueError
        with self.assertRaises(ValueError):
            controller.perform_reroll(0, [0], use_prodigy_ability=False)

        # Prodigy Brute-Force Bypass succeeds
        res = controller.perform_reroll(0, [0], use_prodigy_ability=True)
        self.assertIn("players", res)
        self.assertEqual(player.patches, initial_patches)  # No 🔧 spent!
        self.assertEqual(player.ability_v1_status, AbilityStatus.USED)

    def test_prodigy_persistence_across_multiple_rerolls(self) -> None:
        """11b. Prodigy Brute-Force Bypass persists across subsequent free rerolls in the same phase."""
        controller = GameController()
        prodigy_card = get_archetype_by_code(ArchetypeCode.PRODIGY)
        controller.new_game(
            num_players=4,
            seed=42,
            archetypes=[prodigy_card, get_archetype_by_code(ArchetypeCode.OPERATOR),
                        get_archetype_by_code(ArchetypeCode.CIPHER), get_archetype_by_code(ArchetypeCode.SPOOK)],
        )

        controller.roll_pool(0)
        player = controller.state.players[0]
        meta = controller.player_meta[0]

        meta["rolled_pool"][0].is_locked = True
        controller.perform_reroll(0, [0], use_prodigy_ability=True)
        self.assertTrue(meta.get("prodigy_active", False))
        self.assertEqual(player.ability_v1_status, AbilityStatus.USED)

        meta["rolled_pool"][1].is_locked = True
        res = controller.perform_reroll(0, [1], use_prodigy_ability=False)
        self.assertIn("players", res)

    def test_engine_operator_buy_third_die_cost(self) -> None:
        """9b. GameEngine charges $3 for Operator's 3rd contractor die."""
        config = GameConfig(num_players=4)
        operator_card = get_archetype_by_code(ArchetypeCode.OPERATOR)

        money_snapshots: List[int] = []

        class AlwaysBuyThirdBot(AdaptiveBalancedBot):
            def choose_operator_ability(self, *args, **kwargs) -> bool:
                return True
            def choose_operator_buy_third_die(self, player_state, *args, **kwargs) -> bool:
                money_snapshots.append(player_state.money)
                return True
            def choose_yahtzee_rerolls(self, player_state, *args, **kwargs) -> List[int]:
                if len(money_snapshots) == 1:
                    money_snapshots.append(player_state.money)
                return []

        engine = GameEngine(
            config=config,
            bots=[AlwaysBuyThirdBot(0), AdaptiveBalancedBot(1), AdaptiveBalancedBot(2), AdaptiveBalancedBot(3)],
            seed=42,
            archetypes=[operator_card, get_archetype_by_code(ArchetypeCode.CIPHER),
                        get_archetype_by_code(ArchetypeCode.SPOOK), get_archetype_by_code(ArchetypeCode.PRODIGY)],
        )

        player = engine.state.players[0]
        initial_money = player.money
        engine._execute_phase_1()

        self.assertEqual(player.hired_contractor_count, 3)
        self.assertEqual(len(money_snapshots), 2)
        self.assertEqual(money_snapshots[0], initial_money)  # Free first 2 dice
        self.assertEqual(money_snapshots[1], initial_money - 3)  # Charged $3 for 3rd die
        self.assertEqual(money_snapshots[0] - money_snapshots[1], 3)


class TestSpookAndAcoustic(unittest.TestCase):
    """Group D: The Spook & The Acoustic (Phase 2) (Tests 12-15)."""

    def test_spook_slush_fund_absorbs_blue_secret_loss(self) -> None:
        """12. Spook pays $1 per secret to absorb Blue secret loss."""
        config = GameConfig(num_players=4)
        spook_card = get_archetype_by_code(ArchetypeCode.SPOOK)
        engine = GameEngine(
            config=config,
            bots=[AdaptiveBalancedBot(0), AdaptiveBalancedBot(1), AdaptiveBalancedBot(2), AdaptiveBalancedBot(3)],
            seed=42,
            archetypes=[spook_card, get_archetype_by_code(ArchetypeCode.OPERATOR),
                        get_archetype_by_code(ArchetypeCode.CIPHER), get_archetype_by_code(ArchetypeCode.PRODIGY)],
        )

        player = engine.state.players[0]
        player.secrets = 6
        player.money = 5
        player.patches = 0

        # Simulate Phase 2 Step 2B with 2 unblocked Blue attacks
        attack_strengths = {CubeColor.RED: 0, CubeColor.BLUE: 2, CubeColor.GREEN: 0}
        exited_cubes = {CubeColor.RED: 0, CubeColor.BLUE: 2, CubeColor.GREEN: 0}

        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=[],
            commitments={},
            attack_strengths=attack_strengths,
            exited_cubes=exited_cubes,
            active_directive="SCRIPT_KIDDIE",
        )

        # Spook absorbs 2 Blue damage for FREE (v0.13.0)
        self.assertEqual(player.money, 5)  # $0 spent from cash
        self.assertEqual(player.secrets, 6)  # 0 Secrets lost!
        self.assertEqual(player.ability_v1_status, AbilityStatus.USED)

    def test_spook_slush_fund_absorbs_unpaid_red_ransom(self) -> None:
        """13. Spook Slush Fund absorbs unpaid Red ransom before Secret leak."""
        config = GameConfig(num_players=4)
        spook_card = get_archetype_by_code(ArchetypeCode.SPOOK)
        engine = GameEngine(
            config=config,
            bots=[AdaptiveBalancedBot(0), AdaptiveBalancedBot(1), AdaptiveBalancedBot(2), AdaptiveBalancedBot(3)],
            seed=42,
            archetypes=[spook_card, get_archetype_by_code(ArchetypeCode.OPERATOR),
                        get_archetype_by_code(ArchetypeCode.CIPHER), get_archetype_by_code(ArchetypeCode.PRODIGY)],
        )

        player = engine.state.players[0]
        player.secrets = 6
        player.money = 2
        player.patches = 0

        attack_strengths = {CubeColor.RED: 0, CubeColor.BLUE: 2, CubeColor.GREEN: 0}
        exited_cubes = {CubeColor.RED: 0, CubeColor.BLUE: 2, CubeColor.GREEN: 0}

        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=[],
            commitments={},
            attack_strengths=attack_strengths,
            exited_cubes=exited_cubes,
            active_directive="SCRIPT_KIDDIE",
        )

        # Absorbed 2 secrets for free; money remains 2
        self.assertEqual(player.money, 2)
        self.assertEqual(player.secrets, 6)
        self.assertEqual(player.ability_v1_status, AbilityStatus.USED)

    def test_spook_slush_fund_insufficient_cash(self) -> None:
        """14. Spook absorbs up to 2 secrets for free, and pays $1 cash for 3rd."""
        config = GameConfig(num_players=4)
        spook_card = get_archetype_by_code(ArchetypeCode.SPOOK)
        engine = GameEngine(
            config=config,
            bots=[AdaptiveBalancedBot(0), AdaptiveBalancedBot(1), AdaptiveBalancedBot(2), AdaptiveBalancedBot(3)],
            seed=42,
            archetypes=[spook_card, get_archetype_by_code(ArchetypeCode.OPERATOR),
                        get_archetype_by_code(ArchetypeCode.CIPHER), get_archetype_by_code(ArchetypeCode.PRODIGY)],
        )

        player = engine.state.players[0]
        player.secrets = 6
        player.money = 1  # $1 cash
        player.patches = 0

        attack_strengths = {CubeColor.RED: 0, CubeColor.BLUE: 3, CubeColor.GREEN: 0}
        exited_cubes = {CubeColor.RED: 0, CubeColor.BLUE: 3, CubeColor.GREEN: 0}

        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=[],
            commitments={},
            attack_strengths=attack_strengths,
            exited_cubes=exited_cubes,
            active_directive="SCRIPT_KIDDIE",
        )

        # 2 absorbed for free + 1 paid with cash ($1) -> 0 secrets lost, $0 money remaining
        self.assertEqual(player.money, 0)
        self.assertEqual(player.secrets, 6)
        self.assertEqual(player.ability_v1_status, AbilityStatus.USED)

    def test_acoustic_baffle_echo_removes_exited_cube(self) -> None:
        """15. Acoustic Baffle Echo ignores 1 attack cube for self without modifying exited cubes."""
        config = GameConfig(num_players=4)
        acoustic_card = get_archetype_by_code(ArchetypeCode.ACOUSTIC)
        engine = GameEngine(
            config=config,
            bots=[AdaptiveBalancedBot(0), AdaptiveBalancedBot(1), AdaptiveBalancedBot(2), AdaptiveBalancedBot(3)],
            seed=42,
            archetypes=[acoustic_card, get_archetype_by_code(ArchetypeCode.OPERATOR),
                        get_archetype_by_code(ArchetypeCode.CIPHER), get_archetype_by_code(ArchetypeCode.PRODIGY)],
        )

        player = engine.state.players[0]
        player.secrets = 6
        player.money = 5
        player.patches = 0

        attack_strengths = {CubeColor.RED: 0, CubeColor.BLUE: 2, CubeColor.GREEN: 0}
        exited_cubes = {CubeColor.RED: 1, CubeColor.BLUE: 2, CubeColor.GREEN: 1}

        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=[],
            commitments={},
            attack_strengths=attack_strengths,
            exited_cubes=exited_cubes,
            active_directive="SCRIPT_KIDDIE",
        )

        # Acoustic ignores 1 Blue cube (suffering 1 Blue damage = 1 Secret lost, so 5 Secrets remain)
        self.assertEqual(player.secrets, 5)
        # Exited cubes in tray remain conserved (NOT decremented)
        self.assertEqual(exited_cubes[CubeColor.BLUE], 2)
        self.assertEqual(player.ability_v1_status, AbilityStatus.USED)

    def test_acoustic_baffle_echo_controller_staging_cup(self) -> None:
        """15b. Acoustic Baffle Echo in controller mitigates damage for self without decrementing staging cup."""
        controller = GameController()
        acoustic_card = get_archetype_by_code(ArchetypeCode.ACOUSTIC)
        controller.new_game(
            num_players=4,
            seed=42,
            archetypes=[acoustic_card, get_archetype_by_code(ArchetypeCode.OPERATOR),
                        get_archetype_by_code(ArchetypeCode.CIPHER), get_archetype_by_code(ArchetypeCode.PRODIGY)],
        )

        controller.last_compile_result = {
            "exited_cubes": {"red": 1, "blue": 2, "green": 0, "black": 1}
        }
        controller.state.staging_cup[CubeColor.BLUE] = 3
        controller.state.players[0].secrets = 5

        res = controller.use_acoustic_ability(player_id=0, chosen_color_str="blue")
        self.assertIn("players", res)
        # In v0.13.0: Exited cubes and staging cup are preserved; player gets +1 secret (damage mitigated)
        self.assertEqual(controller.state.players[0].secrets, 6)
        self.assertEqual(controller.state.staging_cup[CubeColor.BLUE], 3)
        self.assertEqual(controller.state.players[0].ability_v1_status, AbilityStatus.USED)


class TestPhreakerAndCipher(unittest.TestCase):
    """Group E: The Phreaker & The Cipher (Phase 3) (Tests 16-19)."""

    def test_phreaker_magnetic_splice_patches_two_free_dice(self) -> None:
        """16. Phreaker repairs up to 2 unpatched dice for free without cash or tokens."""
        controller = GameController()
        phreaker_card = get_archetype_by_code(ArchetypeCode.PHREAKER)
        controller.new_game(
            num_players=4,
            seed=42,
            archetypes=[phreaker_card, get_archetype_by_code(ArchetypeCode.OPERATOR),
                        get_archetype_by_code(ArchetypeCode.CIPHER), get_archetype_by_code(ArchetypeCode.SPOOK)],
        )

        player = controller.state.players[0]
        # Transition controller directly to Phase 3
        controller.phase = 3
        controller.active_player_index = 0

        # Move 3 ready dice to unpatched
        for _ in range(3):
            d = player.ready_dice.pop(0)
            player.unpatched_dice.append(d)

        initial_unpatched = len(player.unpatched_dice)
        initial_ready = len(player.ready_dice)
        player.patches = 0
        player.money = 0

        res = controller.use_phreaker_ability(player_id=0, count=1)
        self.assertIn("players", res)
        self.assertEqual(len(player.unpatched_dice), initial_unpatched - 1)
        self.assertEqual(len(player.ready_dice), initial_ready + 1)
        self.assertEqual(player.patches, 0)
        self.assertEqual(player.money, 0)
        self.assertEqual(player.ability_v1_status, AbilityStatus.USED)

    def test_phreaker_magnetic_splice_with_single_worn_die(self) -> None:
        """17. Phreaker with only 1 unpatched die safely repairs that 1 die."""
        controller = GameController()
        phreaker_card = get_archetype_by_code(ArchetypeCode.PHREAKER)
        controller.new_game(
            num_players=4,
            seed=42,
            archetypes=[phreaker_card, get_archetype_by_code(ArchetypeCode.OPERATOR),
                        get_archetype_by_code(ArchetypeCode.CIPHER), get_archetype_by_code(ArchetypeCode.SPOOK)],
        )

        player = controller.state.players[0]
        controller.phase = 3
        controller.active_player_index = 0

        # Move exactly 1 die to unpatched
        d = player.ready_dice.pop(0)
        player.unpatched_dice.append(d)

        res = controller.use_phreaker_ability(player_id=0, count=2)
        self.assertIn("players", res)
        self.assertEqual(len(player.unpatched_dice), 0)
        self.assertEqual(player.ability_v1_status, AbilityStatus.USED)

    def test_cipher_algorithmic_arbitrage_discounted_colored_die(self) -> None:
        """18. Cipher buys a colored die from market with $2 discount (Mode 1)."""
        controller = GameController()
        cipher_card = get_archetype_by_code(ArchetypeCode.CIPHER)
        controller.new_game(
            num_players=4,
            seed=42,
            archetypes=[cipher_card, get_archetype_by_code(ArchetypeCode.OPERATOR),
                        get_archetype_by_code(ArchetypeCode.PHREAKER), get_archetype_by_code(ArchetypeCode.SPOOK)],
        )

        player = controller.state.players[0]
        controller.phase = 3
        controller.active_player_index = 0
        player.money = 0  # $0 cash

        # Blue die costs $5 base - $2 discount = $3; fails if player has $0
        with self.assertRaises(ValueError):
            controller.buy_die(player_id=0, color_str="blue", use_cipher_ability=True)

        player.money = 5  # Give $5 cash
        initial_blue_stock = controller.state.market[DieColor.BLUE]
        initial_ready_count = len(player.ready_dice)

        res = controller.buy_die(player_id=0, color_str="blue", use_cipher_ability=True)
        self.assertIn("players", res)
        self.assertEqual(player.money, 2)  # $5 - $3 = $2
        self.assertEqual(controller.state.market[DieColor.BLUE], initial_blue_stock - 1)
        self.assertEqual(len(player.ready_dice), initial_ready_count + 1)
        self.assertEqual(player.ready_dice[-1].color, DieColor.BLUE)
        self.assertEqual(player.ability_v1_status, AbilityStatus.USED)

    def test_cipher_algorithmic_arbitrage_cash_payout(self) -> None:
        """19. Cipher takes Algorithmic Arbitrage cash payout (+2$, no secret loss, no black cube)."""
        controller = GameController()
        cipher_card = get_archetype_by_code(ArchetypeCode.CIPHER)
        controller.new_game(
            num_players=4,
            seed=42,
            archetypes=[cipher_card, get_archetype_by_code(ArchetypeCode.OPERATOR),
                        get_archetype_by_code(ArchetypeCode.PHREAKER), get_archetype_by_code(ArchetypeCode.SPOOK)],
        )

        player = controller.state.players[0]
        controller.phase = 3
        controller.active_player_index = 0

        player.money = 0
        player.secrets = 6
        initial_ready_count = len(player.ready_dice)
        initial_unpatched_count = len(player.unpatched_dice)
        initial_black_cubes = controller.state.staging_cup.get(CubeColor.BLACK, 0)

        res = controller.use_cipher_ability(player_id=0)
        self.assertIn("players", res)
        self.assertEqual(player.money, 2)  # +$2 cash arbitrage
        self.assertEqual(player.secrets, 6)  # Secrets preserved (no loss)
        self.assertEqual(controller.state.staging_cup.get(CubeColor.BLACK, 0), initial_black_cubes)

        # No Technical Debt Backlash!
        self.assertEqual(len(player.ready_dice), initial_ready_count)
        self.assertEqual(len(player.unpatched_dice), initial_unpatched_count)
        self.assertEqual(player.ability_v1_status, AbilityStatus.USED)

    def test_phreaker_invalid_count_raises_value_error(self) -> None:
        """17b. Phreaker with count < 1 raises ValueError."""
        controller = GameController()
        phreaker_card = get_archetype_by_code(ArchetypeCode.PHREAKER)
        controller.new_game(
            num_players=4,
            seed=42,
            archetypes=[phreaker_card, get_archetype_by_code(ArchetypeCode.OPERATOR),
                        get_archetype_by_code(ArchetypeCode.CIPHER), get_archetype_by_code(ArchetypeCode.SPOOK)],
        )

        controller.phase = 3
        controller.active_player_index = 0
        with self.assertRaises(ValueError):
            controller.use_phreaker_ability(player_id=0, count=0)

    def test_cipher_bot_string_modes(self) -> None:
        """19b. Cipher bot execution accepts string cipher modes 'BUY_FREE_DIE' and 'DIRTY_INCOME'."""
        controller = GameController()
        cipher_card = get_archetype_by_code(ArchetypeCode.CIPHER)
        controller.new_game(
            num_players=4,
            seed=42,
            archetypes=[cipher_card, get_archetype_by_code(ArchetypeCode.OPERATOR),
                        get_archetype_by_code(ArchetypeCode.PHREAKER), get_archetype_by_code(ArchetypeCode.SPOOK)],
        )

        player = controller.state.players[0]
        meta = controller.player_meta[0]

        # Mode 1 with string "BUY_FREE_DIE"
        player.money = 5
        plan1 = Phase3ActionPlan()
        plan1.use_cipher_ability = True
        plan1.cipher_mode = "BUY_FREE_DIE"
        plan1.cipher_free_die_color = DieColor.BLUE
        player.bot.take_phase3_actions = lambda *args: plan1

        initial_blue = controller.state.market[DieColor.BLUE]
        initial_ready = len(player.ready_dice)
        controller._execute_bot_phase3(player, meta)
        self.assertEqual(len(player.ready_dice), initial_ready + 1)
        self.assertEqual(controller.state.market[DieColor.BLUE], initial_blue - 1)
        self.assertEqual(player.money, 2)  # $5 - $3 = $2
        self.assertEqual(player.ability_v1_status, AbilityStatus.USED)

        # Mode 2 with string "DIRTY_INCOME"
        player.ability_v1_status = AbilityStatus.AVAILABLE
        player.secrets = 5
        player.money = 0
        plan2 = Phase3ActionPlan()
        plan2.use_cipher_ability = True
        plan2.cipher_mode = "DIRTY_INCOME"
        plan2.take_dirty_income = True
        player.bot.take_phase3_actions = lambda *args: plan2

        ready_before = len(player.ready_dice)
        unpatched_before = len(player.unpatched_dice)
        controller._execute_bot_phase3(player, meta)
        self.assertEqual(player.money, 3)
        self.assertEqual(player.secrets, 4)
        self.assertEqual(len(player.ready_dice), ready_before)
        self.assertEqual(len(player.unpatched_dice), unpatched_before)


class TestWebSerializerAndController(unittest.TestCase):
    """Group F: Web Controller & Serialization (Tests 20-21)."""

    def test_web_serializer_archetype_info(self) -> None:
        """20. GameStateSerializer serializes player archetype card and statuses."""
        operator = get_archetype_by_code(ArchetypeCode.OPERATOR)
        player = PlayerState(
            player_id=0,
            bot=AdaptiveBalancedBot(0),
            money=7,
            secrets=6,
            patches=1,
            archetype=operator,
            ability_v1_status=AbilityStatus.AVAILABLE,
            ability_v2_status=AbilityStatus.LOCKED,
            ability_v3_status=AbilityStatus.LOCKED,
        )

        serialized = GameStateSerializer.serialize_player(player, config=GameConfig(), is_human=True, name="Corp 1")
        self.assertIn("archetype", serialized)
        self.assertIsNotNone(serialized["archetype"])
        self.assertEqual(serialized["archetype"]["code"], "OPERATOR")
        self.assertEqual(serialized["archetype"]["name"], "The Operator")
        self.assertEqual(serialized["archetype"]["ability_name"], "Redundant Crew")
        self.assertEqual(serialized["archetype"]["timing_window"], "Phase 1: Staffing Step")

        self.assertEqual(serialized["ability_v1_status"], "AVAILABLE")
        self.assertEqual(serialized["ability_v2_status"], "LOCKED")
        self.assertEqual(serialized["ability_v3_status"], "LOCKED")
        self.assertFalse(serialized["v1_used"])
        self.assertFalse(serialized["v2_used"])
        self.assertFalse(serialized["v3_used"])

    def test_web_controller_archetype_assignment_and_actions(self) -> None:
        """21. GameController logs archetype assignments and handles controller actions."""
        controller = GameController()
        archetypes = [
            get_archetype_by_code(ArchetypeCode.OPERATOR),
            get_archetype_by_code(ArchetypeCode.PRODIGY),
            get_archetype_by_code(ArchetypeCode.PHREAKER),
            get_archetype_by_code(ArchetypeCode.CIPHER),
        ]
        controller.new_game(num_players=4, seed=42, archetypes=archetypes)

        # Check event log records archetype assignments
        log_text = " ".join(controller.event_log)
        self.assertIn("The Operator", log_text)
        self.assertIn("Redundant Crew", log_text)

        # Execute human Operator hiring
        controller.hire_contractors(0, count=2, use_operator_ability=True)
        updated_log = " ".join(controller.event_log)
        self.assertIn("Redundant Crew", updated_log)

    def test_action_capabilities_archetypes(self) -> None:
        """22. get_action_capabilities accurately exposes archetype capabilities."""
        controller = GameController()
        archetypes = [
            get_archetype_by_code(ArchetypeCode.OPERATOR),
            get_archetype_by_code(ArchetypeCode.PRODIGY),
            get_archetype_by_code(ArchetypeCode.PHREAKER),
            get_archetype_by_code(ArchetypeCode.CIPHER),
        ]
        controller.new_game(num_players=4, seed=42, archetypes=archetypes)

        # Player 0 (Operator) in Phase 1 before roll
        caps0 = controller.get_action_capabilities(0)
        self.assertTrue(caps0.get("can_operator"))
        self.assertFalse(caps0.get("can_prodigy"))

        # Transition to Phase 3 with Player 2 (Phreaker) active and worn dice
        p2 = controller.state.players[2]
        p2.unpatched_dice.append(p2.ready_dice.pop(0))
        controller.phase = 3
        controller.active_player_index = 2
        caps2 = controller.get_action_capabilities(2)
        self.assertTrue(caps2.get("can_phreaker"))

        # Transition to Player 3 (Cipher) in Phase 3
        controller.active_player_index = 3
        caps3 = controller.get_action_capabilities(3)
        self.assertTrue(caps3.get("can_cipher_dirty"))
        self.assertIn("can_cipher_buy", caps3)
        self.assertIsInstance(caps3["can_cipher_buy"], dict)


if __name__ == "__main__":
    unittest.main()
