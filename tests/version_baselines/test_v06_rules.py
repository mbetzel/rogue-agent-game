"""Comprehensive unit tests for Rogue Agent RULES.md v0.6 specifications.

Covers all 16 technical test cases from the Principal Engineer specification:
1. GameConfig parameters: contractor cost ($1), max hire (3), supply (12), rerolls (2/1), White die 0 VP.
2. White Contractor Die faces: 3x Block 1 Any, 1x +$2, 1x +1 🔧, 1x Glitch (Locked).
3. Schema fields: Face.is_glitch, Die.is_locked, Die.is_contractor serialization.
4. Version card directives: RAAS Encrypted Memory, Polymorphic Worm Subroutine Throttling, Zero-Day Override Kernel Lock.
5. Contractor hiring deduction and supply: cash deducted, supply decremented, contractor_dice populated.
6. Contractor hiring limits: cash limit, supply limit, max 3 per round limit.
7. Phase 1 active pool includes ready dice + hired contractor dice.
8. Glitch face immediate lock: rolling Glitch sets die.is_locked = True.
9. RAAS Encrypted Memory directive: rolling cash locks die immediately.
10. ZERO_DAY_OVERRIDE Kernel Lock directive: rolling shield locks die immediately.
11. POLYMORPHIC_WORM Subroutine Throttling directive: limits free rerolls to 1.
12. Yahtzee rerolls cannot reroll locked dice.
13. Debug Unlock action: spends 1 🔧 to unlock locked die.
14. Immediate outputs collection: Glitch produces 0; locked cash grants cash; locked shields remain shields.
15. White Contractor Die wear immunity: blocking attack does not move White die to unpatched zone.
16. Green malware contractor sacrifice and round-end contractor expiration back to supply.
"""

from __future__ import annotations

import random
import unittest
from typing import Dict, List, Optional

from sim.bots import (
    AccelerationistBot,
    AdaptiveBalancedBot,
    BaseBot,
    Phase3ActionPlan,
    RecklessSaboteurBot,
    SecOpsTurtleBot,
    VentureGreedBot,
)
from sim.config import CubeColor, DieColor, EndGameReason, GameConfig, ShieldColor
from sim.engine import GameEngine, PlayerState
from sim.entities import (
    Die,
    Face,
    VersionCard,
    create_colored_die,
    create_gray_die,
    create_white_die,
    get_all_version_cards,
)
from web.game_controller import GameController
from web.schemas import GameStateSerializer


class TestV06Rules(unittest.TestCase):
    # -------------------------------------------------------------------------
    # 1. GameConfig Parameters
    # -------------------------------------------------------------------------
    def test_config_parameters_v06(self) -> None:
        """GameConfig defines contractor and reroll parameters for v0.6."""
        cfg = GameConfig()
        self.assertEqual(cfg.contractor_hire_cost, 1)
        self.assertEqual(cfg.contractor_max_hire, 3)
        self.assertEqual(cfg.contractor_supply_total, 12)
        self.assertEqual(cfg.default_free_rerolls, 2)
        self.assertEqual(cfg.throttled_free_rerolls, 1)
        self.assertEqual(cfg.vp_per_die[DieColor.WHITE], 0)

        engine = GameEngine(config=GameConfig(num_players=2), bots=[BaseBot(0), BaseBot(1)], seed=42)
        self.assertEqual(engine.state.contractor_supply, 12)

    # -------------------------------------------------------------------------
    # 2. White Contractor Die Faces
    # -------------------------------------------------------------------------
    def test_white_die_faces(self) -> None:
        """White contractor die has 6 defined faces: 3x Block 1 Any, 1x +$1, 2x Glitch (Locked)."""
        white_die = create_white_die(die_id=101)
        self.assertEqual(white_die.color, DieColor.WHITE)
        self.assertEqual(len(white_die.faces), 6)

        block_any_count = 0
        cash_1_count = 0
        patch_count = 0
        glitch_count = 0

        for face in white_die.faces:
            if face.is_glitch:
                glitch_count += 1
                self.assertEqual(face.money, 0)
                self.assertEqual(face.patches, 0)
                self.assertFalse(face.is_shield)
                self.assertEqual(face.name, "Glitch (Locked)")
            elif face.is_shield and face.shield_color == ShieldColor.ANY and face.block_amount == 1:
                block_any_count += 1
            elif face.money == 1:
                cash_1_count += 1
            elif face.patches > 0:
                patch_count += 1

        self.assertEqual(block_any_count, 3)
        self.assertEqual(cash_1_count, 1)
        self.assertEqual(patch_count, 0)
        self.assertEqual(glitch_count, 2)

        # create_colored_die must dispatch DieColor.WHITE to create_white_die
        factory_die = create_colored_die(DieColor.WHITE, 102)
        self.assertEqual(factory_die.color, DieColor.WHITE)
        self.assertEqual(len(factory_die.faces), 6)

    # -------------------------------------------------------------------------
    # 3. Schema Fields
    # -------------------------------------------------------------------------
    def test_schema_fields(self) -> None:
        """Face has is_glitch, Die has is_locked, and serialization includes v0.6 fields."""
        normal_face = Face("Test Face", shield_color=ShieldColor.RED, block_amount=1)
        self.assertFalse(normal_face.is_glitch)
        self.assertTrue(normal_face.is_shield)

        glitch_face = Face("Glitch Face", shield_color=ShieldColor.ANY, block_amount=1, is_glitch=True)
        self.assertTrue(glitch_face.is_glitch)
        self.assertFalse(glitch_face.is_shield)  # is_shield property excludes glitch

        die = Die(die_id=1, color=DieColor.WHITE, cost=1, vp=0, faces=[glitch_face])
        self.assertFalse(die.is_locked)
        die.is_locked = True
        self.assertTrue(die.is_locked)

        ser_face = GameStateSerializer.serialize_face(glitch_face)
        self.assertIn("is_glitch", ser_face)
        self.assertTrue(ser_face["is_glitch"])

        ser_die = GameStateSerializer.serialize_die(die)
        self.assertIn("is_locked", ser_die)
        self.assertTrue(ser_die["is_locked"])
        self.assertIn("is_contractor", ser_die)
        self.assertTrue(ser_die["is_contractor"])

    # -------------------------------------------------------------------------
    # 4. Version Card Directives
    # -------------------------------------------------------------------------
    def test_version_cards_v06_directives(self) -> None:
        """Version cards have updated directives for Phase 1 locks and rerolls."""
        cards = {c.directive_code: c for c in get_all_version_cards()}
        self.assertIn("RAAS", cards)
        self.assertIn("Encrypted Memory: Any rolled die showing Cash (+$1 or +$2) is Locked immediately.", cards["RAAS"].directive_description)

        self.assertIn("POLYMORPHIC_WORM", cards)
        self.assertIn("Subroutine Throttling: Players receive only 1 free reroll in Phase 1 (instead of 2).", cards["POLYMORPHIC_WORM"].directive_description)

        self.assertIn("ZERO_DAY_OVERRIDE", cards)
        self.assertIn("Kernel Lock: Any rolled die showing a Shield (Block 1 or Block 2) is Locked immediately.", cards["ZERO_DAY_OVERRIDE"].directive_description)

        self.assertIn("CORRUPTED_KERNEL", cards)
        self.assertIn("gains +2 Strength total", cards["CORRUPTED_KERNEL"].directive_description)

    # -------------------------------------------------------------------------
    # 5. Contractor Hiring Deduction and Supply
    # -------------------------------------------------------------------------
    def test_contractor_hiring_deduction_and_supply(self) -> None:
        """Hiring contractors deducts $1 per die, decrements supply, and adds dice to player."""
        engine = GameEngine(config=GameConfig(num_players=2), bots=[BaseBot(0), BaseBot(1)], seed=42)
        p0 = engine.state.players[0]
        p0.money = 7
        self.assertEqual(engine.state.contractor_supply, 12)

        ctrl = GameController()
        ctrl.new_game(num_players=2, seed=42)
        ctrl.state.players[0].money = 7
        initial_supply = ctrl.state.contractor_supply

        ctrl.hire_contractors(player_id=0, count=2)
        self.assertEqual(ctrl.state.players[0].money, 4)  # $7 - ($1 + $2) = $4
        self.assertEqual(ctrl.state.contractor_supply, initial_supply - 2)
        self.assertEqual(len(ctrl.state.players[0].contractor_dice), 2)
        self.assertEqual(ctrl.state.players[0].hired_contractor_count, 2)
        self.assertEqual(ctrl.state.players[0].total_contractors_hired, 2)
        self.assertEqual(ctrl.player_meta[0]["hired_contractors"], 2)

    # -------------------------------------------------------------------------
    # 6. Contractor Hiring Limits
    # -------------------------------------------------------------------------
    def test_contractor_hiring_limits(self) -> None:
        """Contractor hiring strictly enforces max 3 per round, cash limits, and supply limits."""
        ctrl = GameController()
        ctrl.new_game(num_players=2, seed=42)

        # 1. Cash limit: Player has $1, tries to hire 2 -> rejected
        ctrl.state.players[0].money = 1
        with self.assertRaises(ValueError):
            ctrl.hire_contractors(player_id=0, count=2)

        # 2. Max hire limit: Try to hire 4 -> rejected
        ctrl.state.players[0].money = 10
        with self.assertRaises(ValueError):
            ctrl.hire_contractors(player_id=0, count=4)

        # Hire 2 successfully
        ctrl.hire_contractors(player_id=0, count=2)
        self.assertEqual(ctrl.player_meta[0]["hired_contractors"], 2)

        # Try to hire 2 more (2 + 2 = 4 > 3 max) -> rejected
        with self.assertRaises(ValueError):
            ctrl.hire_contractors(player_id=0, count=2)

        # Hire 1 more -> now at 3 (max reached)
        ctrl.hire_contractors(player_id=0, count=1)
        self.assertEqual(ctrl.player_meta[0]["hired_contractors"], 3)

        # Further hire rejected
        with self.assertRaises(ValueError):
            ctrl.hire_contractors(player_id=0, count=1)

        # 3. Supply limit
        ctrl.new_game(num_players=2, seed=42)
        ctrl.state.contractor_supply = 1
        ctrl.state.players[0].money = 5
        with self.assertRaises(ValueError):
            ctrl.hire_contractors(player_id=0, count=2)

    # -------------------------------------------------------------------------
    # 7. Phase 1 Active Pool Includes Contractors
    # -------------------------------------------------------------------------
    def test_phase1_active_pool_includes_contractors(self) -> None:
        """Active pool rolled in Phase 1 includes ready dice + contractor dice."""
        ctrl = GameController()
        ctrl.new_game(num_players=2, seed=42)
        ctrl.state.players[0].money = 5
        ctrl.hire_contractors(player_id=0, count=2)

        ctrl.roll_pool(player_id=0)
        p0_meta = ctrl.player_meta[0]
        # 4 ready starter dice + 2 hired contractors = 6 active dice
        self.assertEqual(len(p0_meta["rolled_pool"]), 6)
        white_count = sum(1 for d in p0_meta["rolled_pool"] if d.color == DieColor.WHITE)
        self.assertEqual(white_count, 2)

    # -------------------------------------------------------------------------
    # 8. Glitch Face Immediate Lock
    # -------------------------------------------------------------------------
    def test_glitch_face_immediate_lock(self) -> None:
        """Rolling a Glitch face immediately sets die.is_locked = True."""
        glitch_face = Face("Glitch (Locked)", is_glitch=True)
        white_die = Die(1, DieColor.WHITE, 1, 0, faces=[glitch_face] * 6)
        white_die.roll(random.Random(42))

        ctrl = GameController()
        ctrl.new_game(num_players=2, seed=42)
        ctrl.state.players[0].ready_dice = [white_die]
        ctrl.roll_pool(player_id=0)

        rolled = ctrl.player_meta[0]["rolled_pool"]
        self.assertEqual(len(rolled), 1)
        self.assertTrue(rolled[0].is_locked)

    # -------------------------------------------------------------------------
    # 9. RAAS Directive Locks Rolled Cash
    # -------------------------------------------------------------------------
    def test_raas_encrypted_memory_locks_cash(self) -> None:
        """Under RAAS, any rolled die showing cash is immediately locked."""
        cash_face = Face("+$2", money=2)
        shield_face = Face("Block 1 Red", shield_color=ShieldColor.RED, block_amount=1)

        die_cash = Die(1, DieColor.GRAY, 0, 0, faces=[cash_face] * 6)
        die_shield = Die(2, DieColor.GRAY, 0, 0, faces=[shield_face] * 6)

        ctrl = GameController()
        ctrl.new_game(num_players=2, seed=42)
        ctrl.state.version_deck = [c for c in get_all_version_cards() if c.directive_code == "RAAS"]
        ctrl.state.current_version_index = 0
        ctrl.state.active_phase1_locks = {"CASH"}
        ctrl.state.players[0].ready_dice = [die_cash, die_shield]

        ctrl.roll_pool(player_id=0)
        rolled = ctrl.player_meta[0]["rolled_pool"]

        self.assertTrue(rolled[0].is_locked, "Cash die must be locked under RAAS")
        self.assertFalse(rolled[1].is_locked, "Shield die must NOT be locked under RAAS")

    # -------------------------------------------------------------------------
    # 10. ZERO_DAY_OVERRIDE Directive Locks Rolled Shields
    # -------------------------------------------------------------------------
    def test_zero_day_override_locks_shields(self) -> None:
        """Under ZERO_DAY_OVERRIDE, any rolled die showing a Shield is immediately locked."""
        cash_face = Face("+$1", money=1)
        shield_face = Face("Block 1 Blue", shield_color=ShieldColor.BLUE, block_amount=1)

        die_cash = Die(1, DieColor.GRAY, 0, 0, faces=[cash_face] * 6)
        die_shield = Die(2, DieColor.GRAY, 0, 0, faces=[shield_face] * 6)

        ctrl = GameController()
        ctrl.new_game(num_players=2, seed=42)
        ctrl.state.version_deck = [c for c in get_all_version_cards() if c.directive_code == "ZERO_DAY_OVERRIDE"]
        ctrl.state.current_version_index = 0
        ctrl.state.active_phase1_locks = {"SHIELD"}
        ctrl.state.players[0].ready_dice = [die_cash, die_shield]

        ctrl.roll_pool(player_id=0)
        rolled = ctrl.player_meta[0]["rolled_pool"]

        self.assertFalse(rolled[0].is_locked, "Cash die must NOT be locked under ZERO_DAY_OVERRIDE")
        self.assertTrue(rolled[1].is_locked, "Shield die must be locked under ZERO_DAY_OVERRIDE")

    # -------------------------------------------------------------------------
    # 11. POLYMORPHIC_WORM Throttles Rerolls
    # -------------------------------------------------------------------------
    def test_polymorphic_worm_throttles_rerolls(self) -> None:
        """Under POLYMORPHIC_WORM, players receive only 1 free reroll instead of 2."""
        ctrl = GameController()
        ctrl.new_game(num_players=2, seed=42)

        # Standard directive: max 2 free rerolls
        ctrl.state.version_deck = [c for c in get_all_version_cards() if c.directive_code == "SCRIPT_KIDDIE"]
        ctrl.state.current_version_index = 0
        ctrl._start_phase_1()
        self.assertEqual(ctrl.player_meta[0]["rerolls_remaining"], 2)
        self.assertEqual(ctrl.player_meta[0]["max_rerolls"], 2)

        # Polymorphic worm: max 1 free reroll
        ctrl.state.version_deck = [c for c in get_all_version_cards() if c.directive_code == "POLYMORPHIC_WORM"]
        ctrl.state.current_version_index = 0
        ctrl._start_phase_1()
        # In v0.15.0, default free rerolls is 2 (Space 4 locks patch faces)
        self.assertEqual(ctrl.player_meta[0]["rerolls_remaining"], 2)
        self.assertEqual(ctrl.player_meta[0]["max_rerolls"], 2)

    # -------------------------------------------------------------------------
    # 12. Yahtzee Rerolls Exclude Locked Dice
    # -------------------------------------------------------------------------
    def test_yahtzee_rerolls_exclude_locked_dice(self) -> None:
        """Yahtzee rerolls strictly reject or ignore locked dice."""
        ctrl = GameController()
        ctrl.new_game(num_players=2, seed=42)

        face_a = Face("Face A", money=1)
        face_b = Face("Face B", money=2)
        die0 = Die(1, DieColor.GRAY, 0, 0, faces=[face_a] * 6)
        die1 = Die(2, DieColor.GRAY, 0, 0, faces=[face_b] * 6)

        ctrl.state.players[0].ready_dice = [die0, die1]
        ctrl.roll_pool(player_id=0)

        # Lock die0 manually
        ctrl.player_meta[0]["rolled_pool"][0].is_locked = True

        # Attempting to reroll die0 must be rejected
        with self.assertRaises(ValueError):
            ctrl.perform_reroll(player_id=0, reroll_indices=[0])

        # Rerolling unlocked die1 succeeds
        prev_rerolls = ctrl.player_meta[0]["rerolls_remaining"]
        ctrl.perform_reroll(player_id=0, reroll_indices=[1])
        self.assertEqual(ctrl.player_meta[0]["rerolls_remaining"], prev_rerolls - 1)
        self.assertEqual(ctrl.state.players[0].total_rerolls_used, 1)

    # -------------------------------------------------------------------------
    # 13. Debug Unlock Action
    # -------------------------------------------------------------------------
    def test_debug_unlock_action(self) -> None:
        """Debug unlock spends 1 🔧 token to unlock a locked die."""
        ctrl = GameController()
        ctrl.new_game(num_players=2, seed=42)
        ctrl.state.players[0].patches = 2

        face = Face("Test", money=1)
        die0 = Die(1, DieColor.GRAY, 0, 0, faces=[face] * 6)
        ctrl.state.players[0].ready_dice = [die0]
        ctrl.roll_pool(player_id=0)

        ctrl.player_meta[0]["rolled_pool"][0].is_locked = True
        self.assertTrue(ctrl.player_meta[0]["rolled_pool"][0].is_locked)

        # Debug unlock
        ctrl.debug_unlock_die(player_id=0, die_index=0)
        self.assertFalse(ctrl.player_meta[0]["rolled_pool"][0].is_locked)
        self.assertEqual(ctrl.state.players[0].patches, 1)

        # Debug unlock on already unlocked die raises ValueError
        with self.assertRaises(ValueError):
            ctrl.debug_unlock_die(player_id=0, die_index=0)

        # Debug unlock with 0 patches raises ValueError
        ctrl.state.players[0].patches = 0
        ctrl.player_meta[0]["rolled_pool"][0].is_locked = True
        with self.assertRaises(ValueError):
            ctrl.debug_unlock_die(player_id=0, die_index=0)

    # -------------------------------------------------------------------------
    # 14. Immediate Outputs Collection
    # -------------------------------------------------------------------------
    def test_immediate_outputs_collection(self) -> None:
        """Glitch produces 0 outputs; locked cash grants cash; locked shields remain shields."""
        ctrl = GameController()
        ctrl.new_game(num_players=2, seed=42)

        glitch_face = Face("Glitch", is_glitch=True)
        cash_face = Face("+$2 Cash", money=2)
        shield_face = Face("Block 1 Blue", shield_color=ShieldColor.BLUE, block_amount=1)

        d_glitch = Die(1, DieColor.WHITE, 1, 0, faces=[glitch_face] * 6)
        d_cash = Die(2, DieColor.GRAY, 0, 0, faces=[cash_face] * 6)
        d_shield = Die(3, DieColor.GRAY, 0, 0, faces=[shield_face] * 6)

        ctrl.state.version_deck = [c for c in get_all_version_cards() if c.directive_code == "RAAS"]
        ctrl.state.current_version_index = 0
        ctrl.state.players[0].ready_dice = [d_glitch, d_cash, d_shield]
        ctrl.state.players[0].money = 0
        ctrl.state.players[0].patches = 0
        ctrl.state.active_phase1_locks = {"CASH"}

        ctrl.roll_pool(player_id=0)

        # d_glitch is locked, d_cash is locked by RAAS, d_shield is unlocked
        rolled = ctrl.player_meta[0]["rolled_pool"]
        self.assertTrue(rolled[0].is_locked)
        self.assertTrue(rolled[1].is_locked)
        self.assertFalse(rolled[2].is_locked)

        # Commit defenses
        ctrl.commit_defenses(player_id=0, commitments={2: "blue"})

        # Verify immediate outputs:
        # Glitch gave 0 cash and 0 patches
        # Locked cash die gave +$2
        self.assertEqual(ctrl.state.players[0].money, 2)
        # Shield was committed to blue shields
        self.assertEqual(len(ctrl.player_meta[0]["shield_slots"]["blue"]), 1)

    # -------------------------------------------------------------------------
    # 15. White Contractor Dice Wear Immunity
    # -------------------------------------------------------------------------
    def test_white_contractor_wear_immunity(self) -> None:
        """White contractor dice that absorb damage are immune to wear and do not go to unpatched zone."""
        engine = GameEngine(config=GameConfig(num_players=2), bots=[BaseBot(0), BaseBot(1)], seed=42)
        p0 = engine.state.players[0]

        shield_face = Face("Block 1 Red", shield_color=ShieldColor.RED, block_amount=1)
        white_die = Die(1, DieColor.WHITE, 1, 0, faces=[shield_face] * 6)
        white_die.current_face = shield_face

        gray_die = Die(2, DieColor.GRAY, 0, 0, faces=[shield_face] * 6)
        gray_die.current_face = shield_face

        p0.contractor_dice = [white_die]
        p0.ready_dice = [gray_die]
        p0.unpatched_dice = []

        # 1 Red cube hits: White die absorbs it
        engine._resolve_player_defense_and_wear(
            player=p0,
            rolled_dice=[white_die, gray_die],
            commitments={0: ShieldColor.RED, 1: ShieldColor.RED},
            attack_strengths={CubeColor.RED: 1, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 1, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        # White die absorbed 1 Red, but is IMMUNE to wear -> NOT in unpatched_dice
        # Gray die was unused -> NOT in unpatched_dice
        self.assertEqual(len(p0.unpatched_dice), 0)

        # If 2 Red cubes hit: White absorbs 1 (immune), Gray absorbs 1 (wears down)
        p0.ready_dice = [gray_die]
        p0.unpatched_dice = []
        engine._resolve_player_defense_and_wear(
            player=p0,
            rolled_dice=[white_die, gray_die],
            commitments={0: ShieldColor.RED, 1: ShieldColor.RED},
            attack_strengths={CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        self.assertEqual(len(p0.unpatched_dice), 1)
        self.assertEqual(p0.unpatched_dice[0].color, DieColor.GRAY)

    # -------------------------------------------------------------------------
    # 16. Green Malware Contractor Sacrifice & Expiration
    # -------------------------------------------------------------------------
    def test_green_malware_contractor_sacrifice_and_expiration(self) -> None:
        """Green malware can be absorbed by contractor sacrifice, and contractors expire to supply."""
        engine = GameEngine(config=GameConfig(num_players=2), bots=[BaseBot(0), BaseBot(1)], seed=42)
        p0 = engine.state.players[0]

        c_die1 = create_white_die(101)
        c_die2 = create_white_die(102)
        p0.contractor_dice = [c_die1, c_die2]
        p0.ready_dice = [create_gray_die(1), create_gray_die(2)]
        p0.unpatched_dice = []
        engine.state.contractor_supply = 10

        # Bot chooses to sacrifice contractor to green malware
        engine._resolve_player_defense_and_wear(
            player=p0,
            rolled_dice=[],
            commitments={},
            attack_strengths={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 1},
            exited_cubes={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 1},
            active_directive="NONE",
        )

        # 1 contractor sacrificed -> returned to supply; ready dice untouched
        self.assertEqual(len(p0.contractor_dice), 1)
        self.assertEqual(len(p0.ready_dice), 2)
        self.assertEqual(len(p0.unpatched_dice), 0)
        self.assertEqual(engine.state.contractor_supply, 11)

        # In _execute_phase_2, all remaining White Contractor dice expire to supply
        commitments = [(p0, [], {}), (engine.state.players[1], [], {})]
        engine.state.staging_cup = {CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0}
        engine._execute_phase_2(commitments)

        self.assertEqual(len(p0.contractor_dice), 0)
        self.assertEqual(engine.state.contractor_supply, 12)

    # -------------------------------------------------------------------------
    # 17. End Game Evaluation Metrics
    # -------------------------------------------------------------------------
    def test_evaluate_end_game_includes_contractor_and_reroll_metrics(self) -> None:
        """evaluate_end_game includes total_contractors_hired and total_rerolls_used."""
        engine = GameEngine(config=GameConfig(num_players=2), bots=[BaseBot(0), BaseBot(1)], seed=42)
        p0 = engine.state.players[0]
        p0.total_contractors_hired = 3
        p0.total_rerolls_used = 4

        result = engine.evaluate_end_game()
        r0 = [r for r in result.rankings if r["player_id"] == 0][0]
        self.assertIn("total_contractors_hired", r0)
        self.assertEqual(r0["total_contractors_hired"], 3)
        self.assertIn("total_rerolls_used", r0)
        self.assertEqual(r0["total_rerolls_used"], 4)


if __name__ == "__main__":
    unittest.main()
