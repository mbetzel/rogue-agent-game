"""Unit tests for Phase 18: Push-Your-Luck Hardware Glitches & Colored Dice Recalibration (v0.12.0 Baseline)."""

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
    AbilityStatus,
    ArchetypeCode,
    Die,
    Face,
    create_colored_die,
    create_gray_die,
    create_white_die,
    get_all_variant_cards,
    get_archetype_by_code,
    get_default_variant_cards,
)
from web.controller.core import GameController
from web.controller.phase1_actions import auto_execute_bots_phase_1, commit_defenses, hire_contractors, roll_pool


class TestV120Rules(unittest.TestCase):
    """Test suite covering the 16 unit test specifications for v0.12.0 Push-Your-Luck Hardware Glitches."""

    def setUp(self) -> None:
        self.variants = get_default_variant_cards()
        self.config = GameConfig(num_players=2)

    # -------------------------------------------------------------------------
    # Test 1: Red Die Recalibration
    # -------------------------------------------------------------------------
    def test_01_red_die_recalibration(self) -> None:
        """1. Red die: Cost $4, 3 VP; Face 1 Block 1 Red, Faces 2-4 +$2, Face 5 Glitch, Face 6 Star."""
        red = create_colored_die(DieColor.RED, 1, self.variants[DieColor.RED])
        self.assertEqual(red.cost, 4)
        self.assertEqual(red.vp, 3)
        self.assertEqual(len(red.faces), 6)

        # Face 1 (idx 0): Block 1 Red
        f1 = red.faces[0]
        self.assertEqual(f1.name, "Block 1 Red")
        self.assertEqual(f1.block_amount, 1)
        self.assertEqual(f1.shield_color, ShieldColor.RED)
        self.assertFalse(f1.is_glitch)

        # Faces 2-4 (idx 1..3): +$2
        for idx in [1, 2, 3]:
            f = red.faces[idx]
            self.assertEqual(f.name, "+$2")
            self.assertEqual(f.money, 2)
            self.assertFalse(f.is_glitch)

        # Face 5 (idx 4): Glitch (Locked)
        f5 = red.faces[4]
        self.assertEqual(f5.name, "Glitch (Locked)")
        self.assertTrue(f5.is_glitch)
        self.assertFalse(f5.is_shield)
        self.assertEqual(f5.money, 0)
        self.assertEqual(f5.patches, 0)

        # Face 6 (idx 5): Red ★
        f6 = red.faces[5]
        self.assertTrue(f6.is_star)
        self.assertEqual(f6.star_code, "R1")

    # -------------------------------------------------------------------------
    # Test 2: Blue Die Recalibration
    # -------------------------------------------------------------------------
    def test_02_blue_die_recalibration(self) -> None:
        """2. Blue die: Cost $5, 4 VP; Face 1 Block 1 Blue, Face 2 +1 🔧, Face 3 +$1, Face 4 Choice, Face 5 Glitch, Face 6 Star."""
        blue = create_colored_die(DieColor.BLUE, 2, self.variants[DieColor.BLUE])
        self.assertEqual(blue.cost, 5)
        self.assertEqual(blue.vp, 4)
        self.assertEqual(len(blue.faces), 6)

        # Face 1 (idx 0): Block 1 Blue
        self.assertEqual(blue.faces[0].name, "Block 1 Blue")
        self.assertEqual(blue.faces[0].block_amount, 1)
        self.assertEqual(blue.faces[0].shield_color, ShieldColor.BLUE)

        # Face 2 (idx 1): +1 🔧
        self.assertEqual(blue.faces[1].name, "+1 🔧")
        self.assertEqual(blue.faces[1].patches, 1)

        # Face 3 (idx 2): +$1
        self.assertEqual(blue.faces[2].name, "+$1")
        self.assertEqual(blue.faces[2].money, 1)

        # Face 4 (idx 3): Choice (Block 1 Blue / +1 🔧)
        f4 = blue.faces[3]
        self.assertTrue(f4.is_choice)
        self.assertEqual(len(f4.choices), 2)
        self.assertEqual(f4.choices[0].block_amount, 1)
        self.assertEqual(f4.choices[0].shield_color, ShieldColor.BLUE)
        self.assertEqual(f4.choices[1].patches, 1)

        # Face 5 (idx 4): Glitch (Locked)
        self.assertEqual(blue.faces[4].name, "Glitch (Locked)")
        self.assertTrue(blue.faces[4].is_glitch)

        # Face 6 (idx 5): Blue ★
        self.assertTrue(blue.faces[5].is_star)
        self.assertEqual(blue.faces[5].star_code, "B1")

    # -------------------------------------------------------------------------
    # Test 3: Green Die Recalibration
    # -------------------------------------------------------------------------
    def test_03_green_die_recalibration(self) -> None:
        """3. Green die: Cost $4, 3 VP; Face 1 Block 1 Green, Face 2 +1 🔧, Face 3 +2 🔧, Face 4 Choice, Face 5 Glitch, Face 6 Star."""
        green = create_colored_die(DieColor.GREEN, 3, self.variants[DieColor.GREEN])
        self.assertEqual(green.cost, 4)
        self.assertEqual(green.vp, 3)
        self.assertEqual(len(green.faces), 6)

        # Face 1 (idx 0): Block 1 Green
        self.assertEqual(green.faces[0].name, "Block 1 Green")
        self.assertEqual(green.faces[0].block_amount, 1)
        self.assertEqual(green.faces[0].shield_color, ShieldColor.GREEN)

        # Face 2 (idx 1): +1 🔧
        self.assertEqual(green.faces[1].name, "+1 🔧")
        self.assertEqual(green.faces[1].patches, 1)

        # Face 3 (idx 2): +2 🔧
        self.assertEqual(green.faces[2].name, "+2 🔧")
        self.assertEqual(green.faces[2].patches, 2)

        # Face 4 (idx 3): Choice (+1 🔧 / +$1)
        f4 = green.faces[3]
        self.assertTrue(f4.is_choice)
        self.assertEqual(len(f4.choices), 2)
        self.assertEqual(f4.choices[0].patches, 1)
        self.assertEqual(f4.choices[1].money, 1)

        # Face 5 (idx 4): Glitch (Locked)
        self.assertEqual(green.faces[4].name, "Glitch (Locked)")
        self.assertTrue(green.faces[4].is_glitch)

        # Face 6 (idx 5): Green ★
        self.assertTrue(green.faces[5].is_star)
        self.assertEqual(green.faces[5].star_code, "G1")

    # -------------------------------------------------------------------------
    # Test 4: Unchanged Dice Faces (Yellow, Purple, Gray, White)
    # -------------------------------------------------------------------------
    def test_04_yellow_purple_gray_white_unchanged(self) -> None:
        """4. Yellow, Purple, Gray, and White dice maintain their standard configurations."""
        yellow = create_colored_die(DieColor.YELLOW, 4, self.variants[DieColor.YELLOW])
        self.assertEqual(yellow.cost, 5)
        self.assertEqual(yellow.vp, 4)
        self.assertTrue(yellow.faces[4].is_star)
        self.assertTrue(yellow.faces[5].is_star)
        self.assertFalse(any(f.is_glitch for f in yellow.faces))

        purple = create_colored_die(DieColor.PURPLE, 5, self.variants[DieColor.PURPLE])
        self.assertEqual(purple.cost, 4)
        self.assertEqual(purple.vp, 3)
        self.assertEqual(purple.faces[0].name, "Block 1 Any")
        self.assertEqual(purple.faces[1].name, "Block 1 Any")
        self.assertTrue(purple.faces[4].is_star)
        self.assertTrue(purple.faces[5].is_star)
        self.assertFalse(any(f.is_glitch for f in purple.faces))

        gray = create_gray_die(6)
        self.assertEqual(gray.cost, 0)
        self.assertEqual(gray.vp, 0)
        self.assertFalse(any(f.is_glitch for f in gray.faces))

        white = create_white_die(7)
        self.assertEqual(white.cost, 1)
        self.assertEqual(white.vp, 0)
        self.assertEqual(white.faces[4].name, "Glitch (Locked)")
        self.assertTrue(white.faces[4].is_glitch)
        self.assertEqual(white.faces[5].name, "Glitch (Locked)")
        self.assertTrue(white.faces[5].is_glitch)

    # -------------------------------------------------------------------------
    # Test 5: Glitch Die Automatically Locked in Step 4
    # -------------------------------------------------------------------------
    def test_05_glitch_die_automatically_locked_in_step_4(self) -> None:
        """5. Rolling a glitch face on a colored die sets is_locked = True during Step 4 lock evaluation."""
        bot0 = BaseBot(0)
        bot1 = BaseBot(1)
        engine = GameEngine(self.config, [bot0, bot1], seed=42)

        red_die = create_colored_die(DieColor.RED, 10)
        red_die.faces = [red_die.faces[4]] * 6  # Force Glitch on roll
        self.assertTrue(red_die.faces[0].is_glitch)

        player = engine.state.players[0]
        player.patches = 0  # Cannot debug unlock
        player.ready_dice = [red_die]

        commitments = engine._execute_phase_1()
        active_dice = commitments[0][1]
        self.assertEqual(len(active_dice), 1)
        self.assertTrue(active_dice[0].current_face.is_glitch)
        self.assertTrue(active_dice[0].is_locked)

    # -------------------------------------------------------------------------
    # Test 6: Debug Unlock Glitch Die with Patch Token
    # -------------------------------------------------------------------------
    def test_06_glitch_die_debug_unlock_spending_patch(self) -> None:
        """6. A locked glitch die can be unlocked by spending 1 🔧 token via choose_debug_unlocks."""
        bot = AdaptiveBalancedBot(0)
        red_die = create_colored_die(DieColor.RED, 10)
        red_die.current_face = red_die.faces[4]  # Glitch
        red_die.is_locked = True

        player = PlayerState(0, bot, money=5, secrets=8, patches=1, ready_dice=[red_die])
        unlocks = bot.choose_debug_unlocks(
            player_state=player,
            active_dice=[red_die],
            staging_cubes={},
            stuck_cubes={},
            directive_code="SCRIPT_KIDDIE",
            rng=random.Random(42),
        )
        self.assertEqual(unlocks, [0])

    # -------------------------------------------------------------------------
    # Test 7: Reroll Glitch Die After Debug Unlock
    # -------------------------------------------------------------------------
    def test_07_glitch_die_reroll_after_debug_unlock(self) -> None:
        """7. Once unlocked, a die showing a glitch face is prioritized in yahtzee rerolls."""
        bot = AdaptiveBalancedBot(0)
        red_die = create_colored_die(DieColor.RED, 10)
        red_die.current_face = red_die.faces[4]  # Glitch
        red_die.is_locked = False  # Debug unlocked

        player = PlayerState(0, bot, money=5, secrets=8, patches=0, ready_dice=[red_die])
        rerolls = bot.choose_yahtzee_rerolls(
            player_state=player,
            active_dice=[red_die],
            rerolls_remaining=2,
            staging_cubes={},
            stuck_cubes={},
            directive_code="SCRIPT_KIDDIE",
            rng=random.Random(42),
        )
        self.assertIn(0, rerolls)

    # -------------------------------------------------------------------------
    # Test 8: Prodigy Brute-Force Bypass Rerolls Locked Glitch Without Patches
    # -------------------------------------------------------------------------
    def test_08_prodigy_brute_force_bypass_rerolls_locked_glitch_without_patches(self) -> None:
        """8. The Prodigy can reroll locked glitch dice without spending 🔧 tokens."""
        prodigy_card = get_archetype_by_code(ArchetypeCode.PRODIGY)
        bot0 = AdaptiveBalancedBot(0)
        bot1 = AdaptiveBalancedBot(1)
        engine = GameEngine(self.config, [bot0, bot1], seed=42, archetypes=[prodigy_card, None])

        player = engine.state.players[0]
        player.patches = 0  # No patches available to unlock

        red_die = create_colored_die(DieColor.RED, 10)
        red_die.faces = [red_die.faces[4]] * 6  # Force glitch face on roll
        player.ready_dice = [red_die]

        self.assertTrue(player.is_ability_available("v1.0"))
        # Force Prodigy bot decision
        bot0.choose_prodigy_ability = lambda *args, **kwargs: True

        commitments = engine._execute_phase_1()
        self.assertEqual(player.ability_v1_status, AbilityStatus.USED)
        self.assertGreater(player.total_rerolls_used, 0)

    # -------------------------------------------------------------------------
    # Test 9: Unresolved Glitch Yields 0 Shield and 0 Output
    # -------------------------------------------------------------------------
    def test_09_unresolved_glitch_yields_zero_shield_and_zero_output(self) -> None:
        """9. An unresolved Glitch face yields 0 shield strength and 0 cash/patch/secret outputs."""
        bot0 = BaseBot(0)
        bot1 = BaseBot(1)
        engine = GameEngine(self.config, [bot0, bot1], seed=42)

        player = engine.state.players[0]
        player.patches = 0
        initial_money = player.money
        initial_patches = player.patches
        initial_secrets = player.secrets

        red_die = create_colored_die(DieColor.RED, 10)
        red_die.faces = [red_die.faces[4]] * 6  # Glitch only
        gray_die = create_gray_die(11)
        gray_die.faces = [Face("Idle", money=0)] * 6
        player.ready_dice = [red_die, gray_die]

        commitments = engine._execute_phase_1()
        p0_commitments = commitments[0][2]

        # Red die (index 0) has glitch -> must NOT be in validated commitments
        self.assertNotIn(0, p0_commitments)
        # Red glitch die yields 0 resources
        self.assertEqual(player.money, initial_money)
        self.assertEqual(player.patches, initial_patches)
        self.assertEqual(player.secrets, initial_secrets)

    # -------------------------------------------------------------------------
    # Test 10: Glitch Backlash Contractor Sacrifice
    # -------------------------------------------------------------------------
    def test_10_glitch_backlash_contractor_sacrifice(self) -> None:
        """10. Unresolved glitch face sacrifices an active White contractor die, sparing ready dice."""
        bot0 = BaseBot(0)
        bot1 = BaseBot(1)
        engine = GameEngine(self.config, [bot0, bot1], seed=42)

        player = engine.state.players[0]
        player.patches = 0
        red_die = create_colored_die(DieColor.RED, 10)
        red_die.faces = [red_die.faces[4]] * 6  # Glitch face
        player.ready_dice = [red_die]

        c_die = create_white_die(100)
        c_die.faces = [Face("Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)] * 6
        player.contractor_dice = [c_die]
        initial_supply = engine.state.contractor_supply

        commitments = engine._execute_phase_1()

        # Contractor die sacrificed to supply
        self.assertEqual(len(player.contractor_dice), 0)
        self.assertEqual(engine.state.contractor_supply, initial_supply + 1)
        # Red die remained in ready_dice!
        self.assertIn(red_die, player.ready_dice)
        self.assertEqual(len(player.unpatched_dice), 0)

    # -------------------------------------------------------------------------
    # Test 11: Glitch Backlash Permanent Demotion Lowest VP
    # -------------------------------------------------------------------------
    def test_11_glitch_backlash_permanent_demotion_lowest_vp(self) -> None:
        """11. Glitch backlash demotes lowest VP uncommitted ready die (Gray 0 VP preferred over Red 3 VP)."""
        bot0 = BaseBot(0)  # Hires 0 contractors
        bot1 = BaseBot(1)
        engine = GameEngine(self.config, [bot0, bot1], seed=42)

        player = engine.state.players[0]
        player.patches = 0  # Cannot unlock
        red_die = create_colored_die(DieColor.RED, 10)
        red_die.faces = [red_die.faces[4]] * 6  # Glitch
        gray_die = create_gray_die(11)  # 0 VP
        gray_die.faces = [Face("+$1", money=1)] * 6

        player.ready_dice = [red_die, gray_die]

        commitments = engine._execute_phase_1()

        # Gray die (0 VP) should be demoted, preserving Red die (3 VP) in ready_dice
        self.assertIn(red_die, player.ready_dice)
        self.assertIn(gray_die, player.unpatched_dice)
        self.assertEqual(len(player.ready_dice), 1)
        self.assertEqual(len(player.unpatched_dice), 1)

    # -------------------------------------------------------------------------
    # Test 12: Glitch Backlash Removes Shield Commitment if Demoted
    # -------------------------------------------------------------------------
    def test_12_glitch_backlash_removes_shield_commitment_if_demoted(self) -> None:
        """12. If a committed shield die is demoted to unpatched, its commitment is removed."""
        bot0 = BaseBot(0)
        bot1 = BaseBot(1)
        engine = GameEngine(self.config, [bot0, bot1], seed=42)

        player = engine.state.players[0]
        player.patches = 0
        # Red die rolls glitch
        red_die = create_colored_die(DieColor.RED, 10)
        red_die.faces = [red_die.faces[4]] * 6

        # Blue die committed to shield
        blue_die = create_colored_die(DieColor.BLUE, 11)
        blue_die.faces = [blue_die.faces[0]] * 6  # Block 1 Blue
        player.ready_dice = [red_die, blue_die]

        # Explicitly instruct bot to choose the committed blue die for demotion
        bot0.choose_glitch_demotion = lambda *args, **kwargs: blue_die

        commitments = engine._execute_phase_1()
        p0_commitments = commitments[0][2]

        # Blue die demoted to unpatched
        self.assertIn(blue_die, player.unpatched_dice)
        # Blue die commitment at index 1 must be cleanly removed from validated_commitments!
        self.assertNotIn(1, p0_commitments)
        self.assertEqual(len(p0_commitments), 0)

    # -------------------------------------------------------------------------
    # Test 13: Multiple Glitches Sequential Resolution
    # -------------------------------------------------------------------------
    def test_13_glitch_backlash_multiple_glitches_sequential_resolution(self) -> None:
        """13. Multiple unresolved glitch faces resolve sequentially across contractor and ready pools."""
        bot0 = BaseBot(0)
        bot1 = BaseBot(1)
        engine = GameEngine(self.config, [bot0, bot1], seed=42)

        player = engine.state.players[0]
        player.patches = 0

        # 2 Red dice showing Glitch
        red1 = create_colored_die(DieColor.RED, 10)
        red1.faces = [red1.faces[4]] * 6
        red2 = create_colored_die(DieColor.RED, 11)
        red2.faces = [red2.faces[4]] * 6

        gray1 = create_gray_die(12)
        gray1.faces = [Face("+$1", money=1)] * 6

        c_die = create_white_die(100)
        c_die.faces = [Face("Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)] * 6

        player.ready_dice = [red1, red2, gray1]
        player.contractor_dice = [c_die]

        commitments = engine._execute_phase_1()

        # Glitch 1: sacrificed contractor die
        self.assertEqual(len(player.contractor_dice), 0)
        # Glitch 2: demoted Gray die (0 VP)
        self.assertIn(gray1, player.unpatched_dice)
        # Red dice preserved in ready
        self.assertIn(red1, player.ready_dice)
        self.assertIn(red2, player.ready_dice)

    # -------------------------------------------------------------------------
    # Test 14: Bot Debug Unlock Prioritizes Colored Glitches
    # -------------------------------------------------------------------------
    def test_14_bot_debug_unlock_prioritizes_colored_glitches(self) -> None:
        """14. Bot debug unlock heuristics prioritize locked colored glitch dice over other locked dice."""
        bot = AdaptiveBalancedBot(0)
        # Die 0: Contractor die with glitch
        c_die = create_white_die(100)
        c_die.current_face = c_die.faces[4]  # Glitch
        c_die.is_locked = True

        # Die 1: Colored Red die with glitch
        red_die = create_colored_die(DieColor.RED, 10)
        red_die.current_face = red_die.faces[4]  # Glitch
        red_die.is_locked = True

        player = PlayerState(0, bot, money=5, secrets=8, patches=1, ready_dice=[red_die], contractor_dice=[c_die])
        active_dice = [c_die, red_die]

        unlocks = bot.choose_debug_unlocks(
            player_state=player,
            active_dice=active_dice,
            staging_cubes={},
            stuck_cubes={},
            directive_code="SCRIPT_KIDDIE",
            rng=random.Random(42),
        )
        # With only 1 patch, bot must unlock index 1 (Red colored glitch) rather than index 0 (White contractor)
        self.assertEqual(unlocks, [1])

    # -------------------------------------------------------------------------
    # Test 15: Web Controller Human Glitch Backlash
    # -------------------------------------------------------------------------
    def test_15_web_controller_human_glitch_backlash(self) -> None:
        """15. Web controller handles glitch backlash in commit_defenses for human player."""
        controller = GameController()
        controller.new_game(num_players=2, seed=42)

        # Hire 1 contractor
        hire_contractors(controller, 0, count=1)
        human = controller.state.players[0]
        meta = controller.player_meta[0]

        # Force a glitch face on a rolled die
        roll_pool(controller, 0)
        rolled = meta["rolled_pool"]
        rolled[0].current_face = Face("Glitch (Locked)", is_glitch=True)

        initial_contractors = len(human.contractor_dice)
        commit_defenses(controller, 0, commitments={})

        # Glitch backlash sacrificed 1 contractor die
        self.assertEqual(len(human.contractor_dice), initial_contractors - 1)
        # Verified backlash logged in event log
        self.assertTrue(any("Glitch Backlash: sacrificed" in event for event in controller.event_log))

    # -------------------------------------------------------------------------
    # Test 16: Web Controller Bot Glitch Backlash
    # -------------------------------------------------------------------------
    def test_16_web_controller_bot_glitch_backlash(self) -> None:
        """16. Web controller handles glitch backlash in auto_execute_bots_phase_1."""
        controller = GameController()
        controller.new_game(num_players=2, seed=42)

        # Set bot player 1 ready dice to include a die that will show glitch
        bot_player = controller.state.players[1]
        bot_player.bot = BaseBot(1)  # Hires 0 contractors
        glitch_red = create_colored_die(DieColor.RED, 50)
        glitch_red.faces = [Face("Glitch (Locked)", is_glitch=True)] * 6
        gray_die = create_gray_die(51)
        gray_die.faces = [Face("+$1", money=1)] * 6
        bot_player.ready_dice = [glitch_red, gray_die]
        bot_player.patches = 0  # Cannot debug unlock

        auto_execute_bots_phase_1(controller)

        # Bot resolved glitch backlash: Gray die demoted to unpatched
        self.assertIn(gray_die, bot_player.unpatched_dice)
        self.assertTrue(any("Glitch Backlash: demoted" in event for event in controller.event_log))


if __name__ == "__main__":
    unittest.main()
