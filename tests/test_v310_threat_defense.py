"""Unit and Integration Tests for Phase 38: Flexible Generic Defense, Flat Unpaid Ransom & Malware Fizzle (v0.31.0 Baseline)."""

from __future__ import annotations

import random
import unittest

from sim.bots.base import BaseBot
from sim.config import CubeColor, DieColor, EndGameReason, GameConfig, ShieldColor
from sim.engine.core import GameEngine
from sim.engine.end_game import evaluate_end_game
from sim.engine.phase1_boot import execute_phase_1
from sim.engine.phase2_threat import execute_phase_2, resolve_player_defense_and_wear
from sim.engine.state import PlayerState, ProductionRole
from sim.entities import (
    COMPANIES,
    CompanyCode,
    Die,
    Face,
    WHITE_HATS,
    WhiteHatCode,
    create_colored_die,
    create_gray_die,
    create_white_die,
)


class TestV310ThreatDefense(unittest.TestCase):
    """Test suite verifying v0.31.0 threat defense invariants."""

    def setUp(self) -> None:
        self.rng = random.Random(42)

    def test_01_flex_shield_generic_assignment_phase1(self) -> None:
        """TEST-01: INV-FLEX-SHIELD-01: Commit Gray and Purple dice showing Block 1 Any.
        Dice are assigned ShieldColor.ANY and ProductionRole.ANY_SHIELD without being coerced to Blue/Red/Green.
        """
        cfg = GameConfig(num_players=2)
        engine = GameEngine(cfg, seed=42)
        p0 = engine.state.players[0]

        gray_die = create_gray_die(1)
        gray_shield_face = Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)
        gray_die.faces = [gray_shield_face] * 6
        gray_die.current_face = gray_shield_face

        purple_die = create_colored_die(DieColor.PURPLE, 2)
        purple_shield_face = Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)
        purple_die.faces = [purple_shield_face] * 6
        purple_die.current_face = purple_shield_face

        p0.ready_for_release_dice = [gray_die, purple_die]

        class FlexBot(BaseBot):
            def commit_shields(self, player_state, rolled_dice, *args, **kwargs):
                return {0: ShieldColor.ANY, 1: ShieldColor.ANY}

            def choose_yahtzee_rerolls(self, *args, **kwargs):
                return []

        p0.bot = FlexBot(0)
        engine.state.players[1].bot = FlexBot(1)

        commitments_summary = execute_phase_1(engine)

        p0_commits = None
        for p, dice, comms in commitments_summary:
            if p.player_id == 0:
                p0_commits = comms
                break

        self.assertIsNotNone(p0_commits)
        self.assertEqual(p0_commits[0], ShieldColor.ANY)
        self.assertEqual(p0_commits[1], ShieldColor.ANY)
        self.assertEqual(gray_die.production_role, ProductionRole.ANY_SHIELD)
        self.assertEqual(purple_die.production_role, ProductionRole.ANY_SHIELD)
        self.assertEqual(len(p0.any_shield_dice), 2)

    def test_02_flex_shield_defense_capacity_truncation(self) -> None:
        """TEST-02: INV-FLEX-SHIELD-01: Assign 3 shields with defense_capacity=2 (1 Blue, 1 Any, 1 Green).
        Priority BLUE > ANY > RED > GREEN truncates Green, keeping Blue and Any. Rejected die moved to Income.
        """
        cfg = GameConfig(num_players=2)
        engine = GameEngine(cfg, seed=42)
        p0 = engine.state.players[0]
        p0.defense_capacity = 2

        d_blue = create_colored_die(DieColor.BLUE, 1)
        f_blue = Face(name="Block 1 Blue", block_amount=1, shield_color=ShieldColor.BLUE)
        d_blue.faces = [f_blue] * 6
        d_blue.current_face = f_blue

        d_any = create_gray_die(2)
        f_any = Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)
        d_any.faces = [f_any] * 6
        d_any.current_face = f_any

        d_green = create_colored_die(DieColor.GREEN, 3)
        f_green = Face(name="Block 1 Green", block_amount=1, shield_color=ShieldColor.GREEN)
        d_green.faces = [f_green] * 6
        d_green.current_face = f_green

        p0.ready_for_release_dice = [d_blue, d_any, d_green]

        class MultiShieldBot(BaseBot):
            def commit_shields(self, player_state, rolled_dice, *args, **kwargs):
                return {0: ShieldColor.BLUE, 1: ShieldColor.ANY, 2: ShieldColor.GREEN}

            def choose_yahtzee_rerolls(self, *args, **kwargs):
                return []

        p0.bot = MultiShieldBot(0)
        engine.state.players[1].bot = MultiShieldBot(1)

        execute_phase_1(engine)

        self.assertEqual(len(p0.shield_dice), 2)
        self.assertEqual(d_blue.production_role, ProductionRole.BLUE_SHIELD)
        self.assertEqual(d_any.production_role, ProductionRole.ANY_SHIELD)
        self.assertEqual(d_green.production_role, ProductionRole.INCOME)

    def test_03_flex_shield_tier1_blue_threat_priority(self) -> None:
        """TEST-03: INV-FLEX-SHIELD-01: Drop 2 Red, 2 Blue with 1 Red shield, 1 Blue shield, and 1 Any shield.
        Stage 1: Red blocks 1 Red, Blue blocks 1 Blue.
        Stage 2: Any shield prioritizes remaining Blue threat (Tier 1).
        Result: 0 Blue unblocked, 1 Red unblocked.
        """
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.money = 5
        p0.secrets = 8

        d_red = create_colored_die(DieColor.RED, 1)
        d_red.production_role = ProductionRole.RED_SHIELD
        d_red.current_face = Face("Block 1 Red", block_amount=1, shield_color=ShieldColor.RED)

        d_blue = create_colored_die(DieColor.BLUE, 2)
        d_blue.production_role = ProductionRole.BLUE_SHIELD
        d_blue.current_face = Face("Block 1 Blue", block_amount=1, shield_color=ShieldColor.BLUE)

        d_any = create_gray_die(3)
        d_any.production_role = ProductionRole.ANY_SHIELD
        d_any.current_face = Face("Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)

        rolled = [d_red, d_blue, d_any]
        commitments = {0: ShieldColor.RED, 1: ShieldColor.BLUE, 2: ShieldColor.ANY}

        resolve_player_defense_and_wear(
            engine=engine,
            player=p0,
            rolled_dice=rolled,
            commitments=commitments,
            attack_strengths={CubeColor.RED: 2, CubeColor.BLUE: 2, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 2, CubeColor.BLUE: 2, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        # Blue threat completely blocked (1 by Blue shield, 1 by Any shield)
        # Red threat: 1 blocked by Red shield, 1 unblocked -> player pays $1 cash
        self.assertEqual(p0.secrets, 8, "0 Corporate Secrets lost because Blue was fully absorbed")
        self.assertEqual(p0.money, 4, "$1 paid for 1 unblocked Red")

    def test_04_flex_shield_tier2_unfunded_red_over_green(self) -> None:
        """TEST-04: INV-FLEX-SHIELD-01: Drop 2 Red, 0 Blue, 1 Green. Player has $0 cash and 1 Any shield.
        Stage 2 Any shield prioritizes unfunded Red threat (Tier 2: player.money < rem_red) over Green.
        Result: 1 Red unblocked (shortfall $1 -> flat 1 Secret leak), 1 Green unblocked (glitches die).
        """
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.money = 0
        p0.secrets = 8

        d_any = create_gray_die(1)
        d_any.production_role = ProductionRole.ANY_SHIELD
        d_any.current_face = Face("Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)

        d_inc = create_gray_die(2)
        d_inc.production_role = ProductionRole.INCOME
        d_inc.current_face = Face("+$1", money=1)

        p0.in_production_dice = [d_any, d_inc]
        rolled = [d_any, d_inc]
        commitments = {0: ShieldColor.ANY}

        resolve_player_defense_and_wear(
            engine=engine,
            player=p0,
            rolled_dice=rolled,
            commitments=commitments,
            attack_strengths={CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 1},
            exited_cubes={CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 1},
            active_directive="NONE",
        )

        # 1 Red blocked by Any (leaving 1 Red unblocked). With $0 cash, shortfall = 1 -> -1 Secret.
        # Green unblocked = 1 -> glitches 1 die to glitched_dice.
        self.assertEqual(p0.secrets, 7)
        self.assertEqual(len(p0.glitched_dice), 1)

    def test_05_flex_shield_tier3_green_over_funded_red(self) -> None:
        """TEST-05: INV-FLEX-SHIELD-01: Drop 2 Red, 0 Blue, 1 Green. Player has $5 cash and 1 Any shield.
        Player has enough cash ($5 >= 2), so Any shield prioritizes Green (Tier 3) over funded Red.
        Result: 0 Green unblocked (no glitch), 2 Red unblocked (player pays $2 cash).
        """
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.money = 5
        p0.secrets = 8

        d_any = create_gray_die(1)
        d_any.production_role = ProductionRole.ANY_SHIELD
        d_any.current_face = Face("Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)

        d_inc = create_gray_die(2)
        d_inc.production_role = ProductionRole.INCOME
        d_inc.current_face = Face("+$1", money=1)

        p0.in_production_dice = [d_any, d_inc]
        rolled = [d_any, d_inc]
        commitments = {0: ShieldColor.ANY}

        resolve_player_defense_and_wear(
            engine=engine,
            player=p0,
            rolled_dice=rolled,
            commitments=commitments,
            attack_strengths={CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 1},
            exited_cubes={CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 1},
            active_directive="NONE",
        )

        self.assertEqual(p0.money, 3, "Paid $2 for 2 unblocked Red cubes")
        self.assertEqual(p0.secrets, 8, "Zero secrets lost")
        self.assertEqual(len(p0.glitched_dice), 0, "Green was blocked; 0 dice glitched")

    def test_06_flex_shield_tier4_funded_red_fallback(self) -> None:
        """TEST-06: INV-FLEX-SHIELD-01: Drop 2 Red, 0 Blue, 0 Green. Player has $5 cash and 1 Any shield.
        Any shield absorbs 1 Red (Tier 4 fallback to save cash).
        Result: 1 Red unblocked -> player pays $1 cash ($4 remaining).
        """
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.money = 5
        p0.secrets = 8

        d_any = create_gray_die(1)
        d_any.production_role = ProductionRole.ANY_SHIELD
        d_any.current_face = Face("Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)

        p0.in_production_dice = [d_any]
        rolled = [d_any]
        commitments = {0: ShieldColor.ANY}

        resolve_player_defense_and_wear(
            engine=engine,
            player=p0,
            rolled_dice=rolled,
            commitments=commitments,
            attack_strengths={CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        self.assertEqual(p0.money, 4, "Any shield absorbed 1 Red, paid $1 for the other")
        self.assertEqual(p0.secrets, 8)

    def test_07_flex_shield_zero_wear_retention(self) -> None:
        """TEST-07: INV-FLEX-SHIELD-01: Zero wear verification.
        Gray and Purple dice assigned to ANY_SHIELD absorb threat cleanly and remain in in_production_dice.
        """
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]

        d_gray = create_gray_die(1)
        d_gray.production_role = ProductionRole.ANY_SHIELD
        d_gray.current_face = Face("Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)

        d_purple = create_colored_die(DieColor.PURPLE, 2)
        d_purple.production_role = ProductionRole.ANY_SHIELD
        d_purple.current_face = Face("Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)

        p0.in_production_dice = [d_gray, d_purple]
        rolled = [d_gray, d_purple]
        commitments = {0: ShieldColor.ANY, 1: ShieldColor.ANY}

        resolve_player_defense_and_wear(
            engine=engine,
            player=p0,
            rolled_dice=rolled,
            commitments=commitments,
            attack_strengths={CubeColor.BLUE: 2, CubeColor.RED: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.BLUE: 2, CubeColor.RED: 0, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        self.assertIn(d_gray, p0.in_production_dice)
        self.assertIn(d_purple, p0.in_production_dice)
        self.assertEqual(len(p0.glitched_dice), 0)
        self.assertEqual(len(p0.scanned_dice), 0)

    def test_08_ransom_flat_single_leak_partial_cash(self) -> None:
        """TEST-08: INV-RANSOM-FLAT-01: Unblocked Red = 2, Player Cash = $1.
        Shortfall = $1 ($1 unpaid). Player pays $1 cash ($0 left). Player loses exactly flat 1 Corporate Secret.
        """
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.money = 1
        p0.secrets = 8

        resolve_player_defense_and_wear(
            engine=engine,
            player=p0,
            rolled_dice=[],
            commitments={},
            attack_strengths={CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        self.assertEqual(p0.money, 0)
        self.assertEqual(p0.secrets, 7, "Flat 1 Secret leak fine (8 - 1 = 7)")

    def test_09_ransom_flat_single_leak_zero_cash_large_shortfall(self) -> None:
        """TEST-09: INV-RANSOM-FLAT-01: Unblocked Red = 4, Player Cash = $0.
        Shortfall = $4 ($4 unpaid). Player pays $0. Player loses exactly flat 1 Corporate Secret (NOT 4).
        """
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.money = 0
        p0.secrets = 8

        resolve_player_defense_and_wear(
            engine=engine,
            player=p0,
            rolled_dice=[],
            commitments={},
            attack_strengths={CubeColor.RED: 4, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 4, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        self.assertEqual(p0.money, 0)
        self.assertEqual(p0.secrets, 7, "Flat 1 Secret leak fine regardless of shortfall size (8 - 1 = 7)")

    def test_10_ransom_fully_funded_zero_leak(self) -> None:
        """TEST-10: INV-RANSOM-FLAT-01: Unblocked Red = 3, Player Cash = $3.
        Shortfall = $0 (fully funded). Player pays $3 cash ($0 left). Exactly 0 Secrets lost.
        """
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.money = 3
        p0.secrets = 8

        resolve_player_defense_and_wear(
            engine=engine,
            player=p0,
            rolled_dice=[],
            commitments={},
            attack_strengths={CubeColor.RED: 3, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 3, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        self.assertEqual(p0.money, 0)
        self.assertEqual(p0.secrets, 8, "0 Secrets lost when ransom is fully funded")

    def test_11_dto_slush_fund_absorbs_flat_ransom_leak(self) -> None:
        """TEST-11: INV-RANSOM-FLAT-01: DTO Slush Fund active.
        Unblocked Red = 3, Cash = $0 (shortfall $3 -> 1 Secret), Unblocked Blue = 0.
        Potential secret loss = 1. Slush Fund absorbs 1 Secret completely. Net secret loss = 0.
        """
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.money = 0
        p0.secrets = 8
        p0.company = COMPANIES[CompanyCode.DTO]
        p0.white_hat = WHITE_HATS[WhiteHatCode.SPOOK]

        resolve_player_defense_and_wear(
            engine=engine,
            player=p0,
            rolled_dice=[],
            commitments={},
            attack_strengths={CubeColor.RED: 3, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 3, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        self.assertEqual(p0.secrets, 8, "Slush Fund absorbed the flat 1 Secret ransom leak")
        self.assertFalse(p0.is_ability_available("v1.0"), "Ability marked used")

    def test_12_malware_fizzle_empty_in_production(self) -> None:
        """TEST-12: INV-MALWARE-FIZZLE-01: Unblocked Green = 2.
        Player has 0 dice in in_production_dice, 3 dice in glitched_dice, 2 dice in ready_for_release_dice.
        Malware fizzles! Glitched count remains 3, Ready count remains 2. Zero dice destroyed. Zero unfulfilled destructions.
        """
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.in_production_dice = []
        p0.contractor_dice = []
        p0.glitched_dice = [create_gray_die(i) for i in range(1, 4)]
        p0.ready_for_release_dice = [create_colored_die(DieColor.RED, i) for i in range(4, 6)]
        p0.unfulfilled_destructions = 0

        resolve_player_defense_and_wear(
            engine=engine,
            player=p0,
            rolled_dice=[],
            commitments={},
            attack_strengths={CubeColor.GREEN: 2, CubeColor.RED: 0, CubeColor.BLUE: 0},
            exited_cubes={CubeColor.GREEN: 2, CubeColor.RED: 0, CubeColor.BLUE: 0},
            active_directive="NONE",
        )

        self.assertEqual(len(p0.glitched_dice), 3, "Zero dice destroyed from glitched_dice")
        self.assertEqual(len(p0.ready_for_release_dice), 2, "Zero dice destroyed from ready_for_release_dice")
        self.assertEqual(p0.unfulfilled_destructions, 0, "Zero unfulfilled destructions recorded")

    def test_13_malware_contractor_sacrifice(self) -> None:
        """TEST-13: INV-MALWARE-FIZZLE-01: Unblocked Green = 1.
        Player has 1 White contractor die and 1 Gray die in in_production_dice.
        Contractor is sacrificed and returned to supply. Gray die in production remains safe.
        """
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        contractor = create_white_die(99)
        p0.contractor_dice = [contractor]
        d_gray = create_gray_die(1)
        d_gray.production_role = ProductionRole.INCOME
        p0.in_production_dice = [d_gray]

        supply_before = engine.state.contractor_supply

        resolve_player_defense_and_wear(
            engine=engine,
            player=p0,
            rolled_dice=[],
            commitments={},
            attack_strengths={CubeColor.GREEN: 1, CubeColor.RED: 0, CubeColor.BLUE: 0},
            exited_cubes={CubeColor.GREEN: 1, CubeColor.RED: 0, CubeColor.BLUE: 0},
            active_directive="NONE",
        )

        self.assertEqual(len(p0.contractor_dice), 0, "Contractor was sacrificed")
        self.assertEqual(engine.state.contractor_supply, supply_before + 1, "Contractor returned to supply")
        self.assertIn(d_gray, p0.in_production_dice, "Gray die in production remains safe")
        self.assertEqual(len(p0.glitched_dice), 0)

    def test_14_wipeout_clean_scoring_no_destruction_penalty(self) -> None:
        """TEST-14: INV-WIPEOUT-CLEAN-01: Total Wipeout scoring.
        All players reach Secrets <= 0. Player A has Secrets -2; Player B has Secrets -4.
        Both had empty production. Net score: Player A = -2, Player B = -4.
        Player A ranked #1. unfulfilled_destructions is absent from tiebreakers.
        """
        cfg = GameConfig(num_players=2)
        engine = GameEngine(cfg, seed=42)
        pA = engine.state.players[0]
        pB = engine.state.players[1]

        pA.secrets = -2
        pA.is_patient_zero = True
        pA.breach_depth = 2
        pA.money = 0
        pA.unfulfilled_destructions = 5  # Legacy value should have 0 effect

        pB.secrets = -4
        pB.is_patient_zero = True
        pB.breach_depth = 4
        pB.money = 0
        pB.unfulfilled_destructions = 0

        engine.state.end_reason = EndGameReason.TOTAL_WIPEOUT
        result = evaluate_end_game(engine)

        self.assertTrue(result.is_total_wipeout)
        rankings = result.rankings
        self.assertEqual(rankings[0]["player_id"], pA.player_id)
        self.assertEqual(rankings[0]["net_score"], -2)
        self.assertEqual(rankings[1]["player_id"], pB.player_id)
        self.assertEqual(rankings[1]["net_score"], -4)
        self.assertEqual(result.winner_id, pA.player_id)


if __name__ == "__main__":
    unittest.main()
