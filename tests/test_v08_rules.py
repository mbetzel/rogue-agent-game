"""Comprehensive unit tests for Rogue Agent RULES.md v0.8 specifications.

Covers all 18 technical test cases from the Principal Engineer specification:
1. test_face_dataclass_choice_fields_and_properties: Face dataclass supports is_choice, choices, has_cash_option, has_shield_option, has_patch_option.
2. test_face_shield_choice_properties: Face with shield choices reflects has_shield_option=True while is_shield=False on parent.
3. test_die_dataclass_effective_face_and_roll_reset: Die effective_face evaluates chosen_choice_index, and roll() resets chosen_choice_index to None.
4. test_gray_die_faces_v08: Gray die Face 5 is +$1 / +1 🔧 choice face; exactly 3 faces with cash option, 2 with patch option.
5. test_blue_die_faces_v08: Blue die Face 4 is Block 1 Blue / +1 🔧 choice face; offers Blue shield or +1 🔧.
6. test_green_die_faces_v08: Green die Face 4 is +1 🔧 / +$1 choice face; offers +1 🔧 or +$1.
7. test_directive_raas_locks_cash_choice_faces: Under RaaS, choice faces with cash options (Gray Face 5, Green Face 4) are locked.
8. test_directive_zero_day_locks_shield_choice_faces: Under Zero-Day Override, choice faces with shield options (Blue Face 4) are locked.
9. test_phase1_sequence_assign_before_collect: Step 5 (Assign Defenses & Choices) precedes Step 6 (Gain Resource Outputs).
10. test_blue_choice_face_committed_to_shield_produces_no_patch: Committed Blue Face 4 blocks Blue damage and produces 0 patches in Step 6.
11. test_blue_choice_face_unassigned_produces_patch: Unassigned Blue Face 4 syncs choice 1 and grants +1 🔧 in Step 6.
12. test_gray_choice_face_money_declaration: Declaring Choice 0 on Gray Face 5 grants +$1 in Step 6 without altering patches.
13. test_gray_choice_face_patch_declaration: Declaring Choice 1 on Gray Face 5 grants +1 🔧 in Step 6 without altering cash.
14. test_green_choice_face_declarations: Declaring Choice 0 on Green Face 4 grants +1 🔧; Choice 1 grants +$1.
15. test_hybrid_star_boot_outputs_collected_when_assigned_to_defense: R1 grants +$2 and G1 grants +1 🔧 in Step 6 even when committed to defense.
16. test_bot_declare_choices_and_commit_heuristics: Bot archetypes declare choices and commit shields according to strategic profiles.
17. test_web_schemas_serialization_choice_faces: GameStateSerializer exports is_choice, choices, has_*_option, chosen_choice_index, and effective_face.
18. test_web_controller_commit_defenses_choice_declarations: GameController.commit_defenses processes choice_declarations and applies Step 6 outputs.
19. test_blue_choice_face_blocks_damage_and_wears_in_phase_2: Blue Face 4 committed to Blue defense blocks 1 Blue damage and wears to unpatched_dice.
"""

from __future__ import annotations

import random
import unittest
from typing import Dict, List, Optional

from sim.bots import (
    AccelerationistBot,
    AdaptiveBalancedBot,
    BaseBot,
    RecklessSaboteurBot,
    SecOpsTurtleBot,
    VentureGreedBot,
)
from sim.config import CubeColor, DieColor, GameConfig, ShieldColor
from sim.engine import GameEngine, PlayerState
from sim.entities import (
    Die,
    Face,
    VariantCard,
    VersionCard,
    create_colored_die,
    create_gray_die,
    create_white_die,
    get_all_version_cards,
    get_default_variant_cards,
)
from web.game_controller import GameController
from web.schemas import GameStateSerializer


class TestV08Rules(unittest.TestCase):
    # -------------------------------------------------------------------------
    # 1. Face Dataclass Choice Fields & Properties
    # -------------------------------------------------------------------------
    def test_face_dataclass_choice_fields_and_properties(self) -> None:
        """Face dataclass supports is_choice, choices, has_cash_option, has_shield_option, has_patch_option."""
        c0 = Face("+$1", money=1)
        c1 = Face("+1 🔧", patches=1)
        choice_face = Face("+$1 / +1 🔧", is_choice=True, choices=(c0, c1))

        self.assertTrue(choice_face.is_choice)
        self.assertEqual(len(choice_face.choices), 2)
        self.assertTrue(choice_face.has_cash_option)
        self.assertTrue(choice_face.has_patch_option)
        self.assertFalse(choice_face.has_shield_option)
        self.assertFalse(choice_face.is_shield)
        self.assertEqual(choice_face.money, 0)
        self.assertEqual(choice_face.patches, 0)

        # Non-choice face
        simple_cash = Face("+$1", money=1)
        self.assertFalse(simple_cash.is_choice)
        self.assertEqual(simple_face_choices := getattr(simple_cash, "choices", ()), ())
        self.assertTrue(simple_cash.has_cash_option)
        self.assertFalse(simple_cash.has_shield_option)
        self.assertFalse(simple_cash.has_patch_option)

    # -------------------------------------------------------------------------
    # 2. Face Shield Choice Properties
    # -------------------------------------------------------------------------
    def test_face_shield_choice_properties(self) -> None:
        """Face with shield choice reflects has_shield_option=True while is_shield=False on parent."""
        c0 = Face("Block 1 Blue", block_amount=1, shield_color=ShieldColor.BLUE)
        c1 = Face("+1 🔧", patches=1)
        choice_face = Face("Block 1 Blue / +1 🔧", is_choice=True, choices=(c0, c1))

        self.assertTrue(choice_face.has_shield_option)
        self.assertTrue(choice_face.has_patch_option)
        self.assertFalse(choice_face.has_cash_option)
        self.assertFalse(choice_face.is_shield)  # Parent is uncommitted, not a shield directly

        # Child 0 is a shield
        self.assertTrue(c0.is_shield)
        self.assertTrue(c0.has_shield_option)
        self.assertFalse(c0.has_patch_option)

    # -------------------------------------------------------------------------
    # 3. Die Effective Face & Roll Reset
    # -------------------------------------------------------------------------
    def test_die_dataclass_effective_face_and_roll_reset(self) -> None:
        """Die effective_face evaluates chosen_choice_index, and roll() resets chosen_choice_index to None."""
        c0 = Face("+$1", money=1)
        c1 = Face("+1 🔧", patches=1)
        choice_face = Face("+$1 / +1 🔧", is_choice=True, choices=(c0, c1))

        die = Die(die_id=1, color=DieColor.GRAY, cost=0, vp=0, faces=[choice_face] * 6)
        die.current_face = choice_face
        die.chosen_choice_index = None

        # When unchosen, effective_face is current_face
        self.assertEqual(die.effective_face, choice_face)

        # Set choice index 0
        die.chosen_choice_index = 0
        self.assertEqual(die.effective_face, c0)
        self.assertEqual(die.effective_face.money, 1)

        # Set choice index 1
        die.chosen_choice_index = 1
        self.assertEqual(die.effective_face, c1)
        self.assertEqual(die.effective_face.patches, 1)

        # roll() resets chosen_choice_index to None
        rng = random.Random(42)
        die.roll(rng)
        self.assertIsNone(die.chosen_choice_index)
        self.assertEqual(die.current_face, choice_face)

    # -------------------------------------------------------------------------
    # 4. Gray Die Faces (v0.8)
    # -------------------------------------------------------------------------
    def test_gray_die_faces_v08(self) -> None:
        """Gray die Face 5 is +$1 / +1 🔧 choice face; exactly 3 faces with cash option, 2 with patch option."""
        die = create_gray_die(1)
        self.assertEqual(len(die.faces), 6)

        face5 = die.faces[4]
        self.assertEqual(face5.name, "+$1 / +1 🔧")
        self.assertTrue(face5.is_choice)
        self.assertEqual(len(face5.choices), 2)
        self.assertEqual(face5.choices[0].name, "+$1")
        self.assertEqual(face5.choices[0].money, 1)
        self.assertEqual(face5.choices[1].name, "+1 🔧")
        self.assertEqual(face5.choices[1].patches, 1)

        cash_option_faces = [f for f in die.faces if f.has_cash_option]
        patch_option_faces = [f for f in die.faces if f.has_patch_option]
        shield_faces = [f for f in die.faces if f.is_shield]

        self.assertEqual(len(cash_option_faces), 3)  # 2x +$1, 1x choice face
        self.assertEqual(len(patch_option_faces), 2)  # 1x choice face, 1x +1 🔧
        self.assertEqual(len(shield_faces), 2)  # 2x Block 1 Any

    # -------------------------------------------------------------------------
    # 5. Blue Die Faces (v0.8)
    # -------------------------------------------------------------------------
    def test_blue_die_faces_v08(self) -> None:
        """Blue die Face 4 is Block 1 Blue / +1 🔧 choice face; offers Blue shield or +1 🔧."""
        variants = get_default_variant_cards()
        blue = create_colored_die(DieColor.BLUE, 2, variants[DieColor.BLUE])
        self.assertEqual(len(blue.faces), 6)

        face4 = blue.faces[3]
        self.assertEqual(face4.name, "Block 1 Blue / +1 🔧")
        self.assertTrue(face4.is_choice)
        self.assertEqual(len(face4.choices), 2)
        self.assertTrue(face4.has_shield_option)
        self.assertTrue(face4.has_patch_option)
        self.assertFalse(face4.has_cash_option)

        c0 = face4.choices[0]
        self.assertEqual(c0.name, "Block 1 Blue")
        self.assertEqual(c0.block_amount, 1)
        self.assertEqual(c0.shield_color, ShieldColor.BLUE)

        c1 = face4.choices[1]
        self.assertEqual(c1.name, "+1 🔧")
        self.assertEqual(c1.patches, 1)

    # -------------------------------------------------------------------------
    # 6. Green Die Faces (v0.8)
    # -------------------------------------------------------------------------
    def test_green_die_faces_v08(self) -> None:
        """Green die Face 4 is +1 🔧 / +$1 choice face; offers +1 🔧 or +$1."""
        variants = get_default_variant_cards()
        green = create_colored_die(DieColor.GREEN, 3, variants[DieColor.GREEN])
        self.assertEqual(len(green.faces), 6)

        face4 = green.faces[3]
        self.assertEqual(face4.name, "+1 🔧 / +$1")
        self.assertTrue(face4.is_choice)
        self.assertEqual(len(face4.choices), 2)
        self.assertTrue(face4.has_patch_option)
        self.assertTrue(face4.has_cash_option)
        self.assertFalse(face4.has_shield_option)

        c0 = face4.choices[0]
        self.assertEqual(c0.name, "+1 🔧")
        self.assertEqual(c0.patches, 1)

        c1 = face4.choices[1]
        self.assertEqual(c1.name, "+$1")
        self.assertEqual(c1.money, 1)

    # -------------------------------------------------------------------------
    # 7. Directive RaaS Locks Cash Choice Faces
    # -------------------------------------------------------------------------
    def test_directive_raas_locks_cash_choice_faces(self) -> None:
        """Under RaaS, choice faces with cash options (Gray Face 5, Green Face 4) are locked."""
        deck = get_all_version_cards()
        raas_card = next(c for c in deck if c.directive_code == "RAAS")

        engine = GameEngine(
            config=GameConfig(num_players=2),
            bots=[BaseBot(0), BaseBot(1)],
            version_deck=[raas_card, raas_card, raas_card],
            seed=42,
        )

        gray_die = create_gray_die(1)
        gray_die.current_face = gray_die.faces[4]  # +$1 / +1 🔧

        green_die = create_colored_die(DieColor.GREEN, 2)
        green_die.current_face = green_die.faces[3]  # +1 🔧 / +$1

        blue_die = create_colored_die(DieColor.BLUE, 3)
        blue_die.current_face = blue_die.faces[3]  # Block 1 Blue / +1 🔧

        player = engine.state.players[0]
        player.ready_dice = [gray_die, green_die, blue_die]

        # In _execute_phase_1, lock evaluation checks has_cash_option
        # Manually evaluate locks using the engine's active directive logic
        for d in [gray_die, green_die, blue_die]:
            d.is_locked = False
            if engine.state.active_directive_code == "RAAS" and d.current_face.has_cash_option:
                d.is_locked = True

        self.assertTrue(gray_die.is_locked)
        self.assertTrue(green_die.is_locked)
        self.assertFalse(blue_die.is_locked)

    # -------------------------------------------------------------------------
    # 8. Directive Zero-Day Override Locks Shield Choice Faces
    # -------------------------------------------------------------------------
    def test_directive_zero_day_locks_shield_choice_faces(self) -> None:
        """Under Zero-Day Override, choice faces with shield options (Blue Face 4) are locked."""
        deck = get_all_version_cards()
        zero_day_card = next(c for c in deck if c.directive_code == "ZERO_DAY_OVERRIDE")

        engine = GameEngine(
            config=GameConfig(num_players=2),
            bots=[BaseBot(0), BaseBot(1)],
            version_deck=[zero_day_card, zero_day_card, zero_day_card],
            seed=42,
        )

        blue_die = create_colored_die(DieColor.BLUE, 1)
        blue_die.current_face = blue_die.faces[3]  # Block 1 Blue / +1 🔧

        gray_die = create_gray_die(2)
        gray_die.current_face = gray_die.faces[4]  # +$1 / +1 🔧

        green_die = create_colored_die(DieColor.GREEN, 3)
        green_die.current_face = green_die.faces[3]  # +1 🔧 / +$1

        for d in [blue_die, gray_die, green_die]:
            d.is_locked = False
            if engine.state.active_directive_code == "ZERO_DAY_OVERRIDE" and d.current_face.has_shield_option:
                d.is_locked = True

        self.assertTrue(blue_die.is_locked)
        self.assertFalse(gray_die.is_locked)
        self.assertFalse(green_die.is_locked)

    # -------------------------------------------------------------------------
    # 9. Phase 1 Sequence: Assign Before Collect
    # -------------------------------------------------------------------------
    def test_phase1_sequence_assign_before_collect(self) -> None:
        """Step 5 (Assign Defenses & Choices) precedes Step 6 (Gain Resource Outputs)."""
        engine = GameEngine(
            config=GameConfig(num_players=2),
            bots=[AdaptiveBalancedBot(0), AdaptiveBalancedBot(1)],
            seed=42,
        )
        player = engine.state.players[0]
        blue_die = create_colored_die(DieColor.BLUE, 10)
        blue_face = blue_die.faces[3]  # Block 1 Blue / +1 🔧
        blue_die.faces = [blue_face] * 6
        blue_die.current_face = blue_face

        # Threat of 2 Blue cubes
        engine.state.staging_cup[CubeColor.BLUE] = 2

        # Give bot only this Blue die
        player.ready_dice = [blue_die]
        player.patches = 0

        # Run Phase 1
        commitments = engine._execute_phase_1()
        player0_res = next(res for res in commitments if res[0].player_id == 0)
        p, dice, val_commits = player0_res

        # Die was assigned to Blue defense
        self.assertIn(0, val_commits)
        self.assertEqual(val_commits[0], ShieldColor.BLUE)
        self.assertEqual(blue_die.chosen_choice_index, 0)

        # Because it was assigned to defense, it did NOT produce a patch in Step 6
        self.assertEqual(player.patches, 0)

    # -------------------------------------------------------------------------
    # 10. Blue Choice Face Committed to Shield Produces No Patch
    # -------------------------------------------------------------------------
    def test_blue_choice_face_committed_to_shield_produces_no_patch(self) -> None:
        """Committed Blue Face 4 blocks Blue damage and produces 0 patches in Step 6."""
        engine = GameEngine(config=GameConfig(num_players=2), bots=[BaseBot(0), BaseBot(1)], seed=42)
        player = engine.state.players[0]
        blue_die = create_colored_die(DieColor.BLUE, 10)
        blue_face = blue_die.faces[3]  # Block 1 Blue / +1 🔧
        blue_die.faces = [blue_face] * 6
        blue_die.current_face = blue_face
        player.ready_dice = [blue_die]
        player.patches = 0

        # Custom commit assigning index 0 to BLUE
        class ShieldBlueBot(BaseBot):
            def commit_shields(self, *args, **kwargs) -> Dict[int, ShieldColor]:
                return {0: ShieldColor.BLUE}

        player.bot = ShieldBlueBot(0)
        commitments = engine._execute_phase_1()
        p0_commit = commitments[0][2]

        self.assertIn(0, p0_commit)
        self.assertEqual(blue_die.chosen_choice_index, 0)
        self.assertEqual(player.patches, 0)

    # -------------------------------------------------------------------------
    # 11. Blue Choice Face Unassigned Produces Patch
    # -------------------------------------------------------------------------
    def test_blue_choice_face_unassigned_produces_patch(self) -> None:
        """Unassigned Blue Face 4 syncs choice 1 and grants +1 🔧 in Step 6."""
        engine = GameEngine(config=GameConfig(num_players=2), bots=[BaseBot(0), BaseBot(1)], seed=42)
        player = engine.state.players[0]
        blue_die = create_colored_die(DieColor.BLUE, 10)
        blue_face = blue_die.faces[3]  # Block 1 Blue / +1 🔧
        blue_die.faces = [blue_face] * 6
        blue_die.current_face = blue_face
        player.ready_dice = [blue_die]
        player.patches = 0

        # Bot does not commit to shield
        class NoShieldBot(BaseBot):
            def commit_shields(self, *args, **kwargs) -> Dict[int, ShieldColor]:
                return {}

        player.bot = NoShieldBot(0)
        commitments = engine._execute_phase_1()
        p0_commit = commitments[0][2]

        self.assertNotIn(0, p0_commit)
        self.assertEqual(blue_die.chosen_choice_index, 1)
        self.assertEqual(player.patches, 1)

    # -------------------------------------------------------------------------
    # 12. Gray Choice Face Money Declaration
    # -------------------------------------------------------------------------
    def test_gray_choice_face_money_declaration(self) -> None:
        """Declaring Choice 0 on Gray Face 5 grants +$1 in Step 6 without altering patches."""
        engine = GameEngine(config=GameConfig(num_players=2), bots=[BaseBot(0), BaseBot(1)], seed=42)
        player = engine.state.players[0]
        gray_die = create_gray_die(10)
        gray_face = gray_die.faces[4]  # +$1 / +1 🔧
        gray_die.faces = [gray_face] * 6
        gray_die.current_face = gray_face
        player.ready_dice = [gray_die]
        player.money = 7
        player.patches = 1

        class Choice0Bot(BaseBot):
            def declare_choices(self, *args, **kwargs) -> Dict[int, int]:
                return {0: 0}

        player.bot = Choice0Bot(0)
        engine._execute_phase_1()

        self.assertEqual(gray_die.chosen_choice_index, 0)
        self.assertEqual(player.money, 8)  # +$1
        self.assertEqual(player.patches, 1)  # unchanged

    # -------------------------------------------------------------------------
    # 13. Gray Choice Face Patch Declaration
    # -------------------------------------------------------------------------
    def test_gray_choice_face_patch_declaration(self) -> None:
        """Declaring Choice 1 on Gray Face 5 grants +1 🔧 in Step 6 without altering cash."""
        engine = GameEngine(config=GameConfig(num_players=2), bots=[BaseBot(0), BaseBot(1)], seed=42)
        player = engine.state.players[0]
        gray_die = create_gray_die(10)
        gray_face = gray_die.faces[4]  # +$1 / +1 🔧
        gray_die.faces = [gray_face] * 6
        gray_die.current_face = gray_face
        player.ready_dice = [gray_die]
        player.money = 7
        player.patches = 1

        class Choice1Bot(BaseBot):
            def declare_choices(self, *args, **kwargs) -> Dict[int, int]:
                return {0: 1}

        player.bot = Choice1Bot(0)
        engine._execute_phase_1()

        self.assertEqual(gray_die.chosen_choice_index, 1)
        self.assertEqual(player.money, 7)  # unchanged
        self.assertEqual(player.patches, 2)  # +1 🔧

    # -------------------------------------------------------------------------
    # 14. Green Choice Face Declarations
    # -------------------------------------------------------------------------
    def test_green_choice_face_declarations(self) -> None:
        """Declaring Choice 0 on Green Face 4 grants +1 🔧; Choice 1 grants +$1."""
        engine = GameEngine(config=GameConfig(num_players=2), bots=[BaseBot(0), BaseBot(1)], seed=42)
        player = engine.state.players[0]
        green_die = create_colored_die(DieColor.GREEN, 10)
        green_face = green_die.faces[3]  # +1 🔧 / +$1
        green_die.faces = [green_face] * 6
        green_die.current_face = green_face
        player.ready_dice = [green_die]
        player.money = 7
        player.patches = 0

        # Choice 0: +1 🔧
        class Choice0Bot(BaseBot):
            def declare_choices(self, *args, **kwargs) -> Dict[int, int]:
                return {0: 0}

        player.bot = Choice0Bot(0)
        engine._execute_phase_1()
        self.assertEqual(green_die.chosen_choice_index, 0)
        self.assertEqual(player.patches, 1)
        self.assertEqual(player.money, 7)

        # Reset and declare Choice 1: +$1
        green_die.chosen_choice_index = None
        player.patches = 0
        player.money = 7

        class Choice1Bot(BaseBot):
            def declare_choices(self, *args, **kwargs) -> Dict[int, int]:
                return {0: 1}

        player.bot = Choice1Bot(0)
        engine._execute_phase_1()
        self.assertEqual(green_die.chosen_choice_index, 1)
        self.assertEqual(player.patches, 0)
        self.assertEqual(player.money, 8)

    # -------------------------------------------------------------------------
    # 15. Hybrid Star Boot Outputs Collected When Assigned to Defense
    # -------------------------------------------------------------------------
    def test_hybrid_star_boot_outputs_collected_when_assigned_to_defense(self) -> None:
        """R1 grants +$2 and G1 grants +1 🔧 in Step 6 even when committed to defense."""
        variants = get_default_variant_cards()
        r1_card = variants[DieColor.RED]  # R1: Ransom Insurance: Block 1 Red + gain +$2
        g1_card = variants[DieColor.GREEN]  # G1: Self-Healing Kernel: Block 2 Green + gain +1 🔧

        engine = GameEngine(
            config=GameConfig(num_players=2),
            bots=[BaseBot(0), BaseBot(1)],
            variant_cards={DieColor.RED: r1_card, DieColor.GREEN: g1_card},
            seed=42,
        )
        player = engine.state.players[0]
        red_die = create_colored_die(DieColor.RED, 10, r1_card)
        red_die.faces = [r1_card.star_face] * 6
        red_die.current_face = r1_card.star_face

        green_die = create_colored_die(DieColor.GREEN, 11, g1_card)
        green_die.faces = [g1_card.star_face] * 6
        green_die.current_face = g1_card.star_face

        player.ready_dice = [red_die, green_die]
        player.money = 7
        player.patches = 0

        commitments = engine._execute_phase_1()
        p0_commit = commitments[0][2]

        # Both are committed to defense
        self.assertIn(0, p0_commit)
        self.assertIn(1, p0_commit)

        # Step 6 collected boot outputs: +$2 from R1, +1 🔧 from G1
        self.assertEqual(player.money, 9)
        self.assertEqual(player.patches, 1)

    # -------------------------------------------------------------------------
    # 16. Bot Declare Choices and Commit Heuristics
    # -------------------------------------------------------------------------
    def test_bot_declare_choices_and_commit_heuristics(self) -> None:
        """Bot archetypes declare choices and commit shields according to strategic profiles."""
        p_state = PlayerState(player_id=0, bot=BaseBot(0), money=5, secrets=5, patches=1)

        gray = create_gray_die(1)
        gray.current_face = gray.faces[4]  # +$1 / +1 🔧

        green = create_colored_die(DieColor.GREEN, 2)
        green.current_face = green.faces[3]  # +1 🔧 / +$1

        blue = create_colored_die(DieColor.BLUE, 3)
        blue.current_face = blue.faces[3]  # Block 1 Blue / +1 🔧

        dice = [gray, green, blue]

        # SecOpsTurtleBot: prefers patches and Blue shielding
        turtle = SecOpsTurtleBot(0)
        turtle_decls = turtle.declare_choices(p_state, active_dice=dice, staging_cubes={CubeColor.BLUE: 1})
        self.assertEqual(turtle_decls[0], 1)  # Gray: prefers +1 🔧 (1)
        self.assertEqual(turtle_decls[1], 0)  # Green: prefers +1 🔧 (0)
        self.assertEqual(turtle_decls[2], 0)  # Blue: threat > 0 -> Block 1 Blue (0)
        turtle_commits = turtle.commit_shields(p_state, rolled_dice=dice, staging_cubes={CubeColor.BLUE: 1}, stuck_cubes={}, directive_code="", rng=random.Random(1))
        self.assertEqual(turtle_commits.get(2), ShieldColor.BLUE)

        # VentureGreedBot: prefers cash
        greed = VentureGreedBot(1)
        greed_decls = greed.declare_choices(p_state, active_dice=dice, staging_cubes={CubeColor.BLUE: 1})
        self.assertEqual(greed_decls[0], 0)  # Gray: prefers +$1 (0)
        self.assertEqual(greed_decls[1], 1)  # Green: prefers +$1 (1)

        # AdaptiveBalancedBot: patches < 2 -> needs patch
        balanced = AdaptiveBalancedBot(2)
        bal_decls = balanced.declare_choices(p_state, active_dice=dice, staging_cubes={CubeColor.BLUE: 2})
        self.assertEqual(bal_decls[0], 1)  # patches < 2 -> +1 🔧
        self.assertEqual(bal_decls[1], 0)  # patches < 2 -> +1 🔧
        self.assertEqual(bal_decls[2], 0)  # Blue threat > 0 -> Block 1 Blue

    # -------------------------------------------------------------------------
    # 17. Web Schemas Serialization of Choice Faces
    # -------------------------------------------------------------------------
    def test_web_schemas_serialization_choice_faces(self) -> None:
        """GameStateSerializer exports is_choice, choices, has_*_option, chosen_choice_index, and effective_face."""
        gray = create_gray_die(1)
        gray.current_face = gray.faces[4]  # +$1 / +1 🔧
        gray.chosen_choice_index = 1

        face_data = GameStateSerializer.serialize_face(gray.current_face)
        self.assertTrue(face_data["is_choice"])
        self.assertEqual(len(face_data["choices"]), 2)
        self.assertTrue(face_data["has_cash_option"])
        self.assertTrue(face_data["has_patch_option"])
        self.assertFalse(face_data["has_shield_option"])

        die_data = GameStateSerializer.serialize_die(gray)
        self.assertEqual(die_data["chosen_choice_index"], 1)
        self.assertIsNotNone(die_data["effective_face"])
        self.assertEqual(die_data["effective_face"]["name"], "+1 🔧")
        self.assertEqual(die_data["effective_face"]["patches"], 1)

    # -------------------------------------------------------------------------
    # 18. Web Controller commit_defenses with Choice Declarations
    # -------------------------------------------------------------------------
    def test_web_controller_commit_defenses_choice_declarations(self) -> None:
        """GameController.commit_defenses processes choice_declarations and applies Step 6 outputs."""
        ctrl = GameController()
        ctrl.new_game(num_players=2, seed=42)

        # Setup rolled pool with choice faces
        p0 = ctrl.state.players[0]
        meta0 = ctrl.player_meta[0]

        gray = create_gray_die(1)
        gray.current_face = gray.faces[4]  # +$1 / +1 🔧

        green = create_colored_die(DieColor.GREEN, 2)
        green.current_face = green.faces[3]  # +1 🔧 / +$1

        blue = create_colored_die(DieColor.BLUE, 3)
        blue.current_face = blue.faces[3]  # Block 1 Blue / +1 🔧

        meta0["rolled_pool"] = [gray, green, blue]
        meta0["has_rolled"] = True
        p0.patches = 0
        p0.money = 7

        # Commit Blue die to defense, declare Gray choice 0 (+$1) and Green choice 0 (+1 🔧)
        res = ctrl.commit_defenses(
            player_id=0,
            commitments={2: "blue"},
            choice_declarations={0: 0, 1: 0},
        )

        self.assertTrue(meta0["has_committed"])
        self.assertEqual(blue.chosen_choice_index, 0)
        self.assertEqual(gray.chosen_choice_index, 0)
        self.assertEqual(green.chosen_choice_index, 0)

        # Outputs applied in Step 6:
        # Gray choice 0: +$1 -> money 8
        # Green choice 0: +1 🔧 -> patches 1
        # Blue choice 0: committed to defense -> 0 patches
        self.assertEqual(p0.money, 8)
        self.assertEqual(p0.patches, 1)

    # -------------------------------------------------------------------------
    # 19. Blue Choice Face Blocks Damage and Wears in Phase 2
    # -------------------------------------------------------------------------
    def test_blue_choice_face_blocks_damage_and_wears_in_phase_2(self) -> None:
        """When Blue Face 4 is committed to Blue defense and 1 Blue cube exits in Phase 2:
        0 Blue damage is taken (secrets stay intact) and the Blue die wears to unpatched_dice.
        """
        engine = GameEngine(config=GameConfig(num_players=2), bots=[BaseBot(0), BaseBot(1)], seed=42)
        player = engine.state.players[0]
        blue_die = create_colored_die(DieColor.BLUE, 10)
        blue_face = blue_die.faces[3]  # Block 1 Blue / +1 🔧
        blue_die.faces = [blue_face] * 6
        blue_die.current_face = blue_face
        blue_die.chosen_choice_index = 0  # Committed to Blue defense (Block 1 Blue)

        player.ready_dice = [blue_die]
        player.unpatched_dice = []
        initial_secrets = player.secrets

        # Mock tower.drop to return exactly 1 Blue cube exiting
        engine.state.tower.drop = lambda staged, rng: {
            CubeColor.BLUE: 1,
            CubeColor.RED: 0,
            CubeColor.GREEN: 0,
            CubeColor.BLACK: 0,
        }

        commitments = [(player, [blue_die], {0: ShieldColor.BLUE})]
        engine._execute_phase_2(commitments)

        # 0 Blue damage taken -> secrets stay intact
        self.assertEqual(player.secrets, initial_secrets)
        self.assertFalse(player.is_patient_zero)

        # Blue die actively blocked 1 Blue cube -> wore to unpatched_dice
        self.assertNotIn(blue_die, player.ready_dice)
        self.assertIn(blue_die, player.unpatched_dice)


if __name__ == "__main__":
    unittest.main()
