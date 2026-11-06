"""Unit and Integration Tests for Phase 29: Streamlined CI/CD Pipeline & Universal Glitch/Patch Overhaul (v0.22.0 Baseline)."""

import random
import unittest

from sim.bots.base import BaseBot, Phase3ActionPlan
from sim.config import CubeColor, DieColor, GameConfig, ShieldColor
from sim.engine.core import GameEngine
from sim.engine.end_game import evaluate_end_game
from sim.engine.phase1_boot import execute_phase_1, detect_hash_matches
from sim.engine.phase2_threat import execute_phase_2
from sim.engine.phase3_ops import execute_phase_3
from sim.engine.state import PlayerState, ProductionRole
from sim.entities import (
    ArchetypeCode,
    Die,
    Face,
    create_colored_die,
    create_gray_die,
    create_white_die,
    get_all_archetype_cards,
    get_archetype_by_code,
    get_default_variant_cards,
)


class TestV220Rules(unittest.TestCase):
    """Exhaustive test suite for v0.22.0 Streamlined CI/CD Pipeline & Universal Glitch/Patch mechanics."""

    # =========================================================================
    # Category 1: Universal Face 5 Glitch & Die Profiles
    # =========================================================================

    def test_colored_dice_face5_glitch(self) -> None:
        """Face 5 is is_glitch=True for Red, Blue, Green, Yellow, and Purple."""
        for color in [DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW, DieColor.PURPLE]:
            die = create_colored_die(color, 1)
            self.assertEqual(len(die.faces), 6)
            face5 = die.faces[4]  # 0-indexed Face 5
            self.assertTrue(face5.is_glitch, f"{color.value} Face 5 must be a Glitch face")
            self.assertIn("Glitch", face5.name)

    def test_yellow_and_purple_single_star(self) -> None:
        """Yellow and Purple have exactly 1 Star on Face 6 and 0 Stars on Face 5."""
        for color in [DieColor.YELLOW, DieColor.PURPLE]:
            die = create_colored_die(color, 1)
            face5 = die.faces[4]
            face6 = die.faces[5]
            self.assertFalse(face5.is_star, f"{color.value} Face 5 must not be a Star face")
            self.assertTrue(face6.is_star, f"{color.value} Face 6 must be a Star face")
            star_count = sum(1 for f in die.faces if f.is_star)
            self.assertEqual(star_count, 1, f"{color.value} must have exactly 1 Star face")

    def test_white_contractor_two_glitches(self) -> None:
        """White Contractor has 2 Glitches (Faces 5 & 6)."""
        white = create_white_die(1)
        self.assertEqual(len(white.faces), 6)
        self.assertTrue(white.faces[4].is_glitch)
        self.assertTrue(white.faces[5].is_glitch)
        glitch_count = sum(1 for f in white.faces if f.is_glitch)
        self.assertEqual(glitch_count, 2)

    def test_gray_starter_zero_glitches(self) -> None:
        """Gray Starter has 0 Glitches."""
        gray = create_gray_die(1)
        self.assertEqual(len(gray.faces), 6)
        glitch_count = sum(1 for f in gray.faces if f.is_glitch)
        self.assertEqual(glitch_count, 0)

    def test_commercial_exposure_deleted(self) -> None:
        """Verify that an unblocked Green cube does NOT force Yellow dice to be glitched first."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        yellow_die = create_colored_die(DieColor.YELLOW, 10)
        yellow_die.production_role = ProductionRole.INCOME
        gray_die = create_gray_die(11)
        gray_die.production_role = ProductionRole.BLUE_SHIELD

        # Put Yellow in income and Gray in shield
        p0.in_production_dice = [yellow_die, gray_die]
        p0.contractor_dice.clear()

        # Execute Phase 2 with 1 unblocked green cube
        commitments = [(p0, list(p0.in_production_dice), {1: ShieldColor.BLUE})]
        engine.state.staging_cup = {CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 1, CubeColor.BLACK: 0}
        
        # When 1 unblocked green hits, default triage glitches the shield die (gray) to protect income
        # Yellow must NOT be forced to demote
        execute_phase_2(engine, commitments)
        self.assertIn(yellow_die, p0.in_production_dice, "Yellow die should be preserved when shield is sacrificed")
        self.assertIn(gray_die, p0.glitched_dice)

    # =========================================================================
    # Category 2: State Machine & Zone Transitions
    # =========================================================================

    def test_initial_state_ready_for_release(self) -> None:
        """Verify 4 Gray dice start in ready_for_release_dice and Under Development is empty."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        for p in engine.state.players:
            self.assertEqual(len(p.ready_for_release_dice), 4)
            self.assertEqual(len(p.in_production_dice), 0)
            self.assertEqual(len(p.glitched_dice), 0)
            self.assertEqual(len(p.scanned_dice), 0)
            self.assertEqual(len(p.under_development_dice), 0)

    def test_zone_properties_and_aliases(self) -> None:
        """Verify ready_dice and unpatched_dice accessors mirror ready_for_release_dice and glitched+scanned."""
        p = PlayerState(player_id=0, bot=BaseBot(0), money=5, secrets=8, patches=2)
        d1 = create_gray_die(1)
        d2 = create_colored_die(DieColor.RED, 2)
        d3 = create_colored_die(DieColor.BLUE, 3)

        p.ready_for_release_dice = [d1]
        p.glitched_dice = [d2]
        p.scanned_dice = [d3]

        self.assertEqual(p.ready_dice, [d1])
        self.assertEqual(p.unpatched_dice, [d2, d3])
        self.assertEqual(p.under_development_dice, [d2, d3])

        # Setter synchronization
        d4 = create_gray_die(4)
        p.ready_dice = [d4]
        self.assertEqual(p.ready_for_release_dice, [d4])

        p.unpatched_dice = [d1]
        self.assertEqual(p.glitched_dice, [d1])
        self.assertEqual(p.scanned_dice, [])

    def test_in_production_role_accessors(self) -> None:
        """Verify income_dice, red_shield_dice, etc. correctly filter in_production_dice."""
        p = PlayerState(player_id=0, bot=BaseBot(0), money=5, secrets=8, patches=2)
        d_inc = create_gray_die(1)
        d_inc.production_role = ProductionRole.INCOME
        d_red = create_colored_die(DieColor.RED, 2)
        d_red.production_role = ProductionRole.RED_SHIELD
        d_blue = create_colored_die(DieColor.BLUE, 3)
        d_blue.production_role = ProductionRole.BLUE_SHIELD
        d_green = create_colored_die(DieColor.GREEN, 4)
        d_green.production_role = ProductionRole.GREEN_SHIELD

        p.in_production_dice = [d_inc, d_red, d_blue, d_green]

        self.assertEqual(p.income_dice, [d_inc])
        self.assertEqual(p.red_shield_dice, [d_red])
        self.assertEqual(p.blue_shield_dice, [d_blue])
        self.assertEqual(p.green_shield_dice, [d_green])
        self.assertEqual(p.shield_dice, [d_red, d_blue, d_green])

    # =========================================================================
    # Category 3: Phase 1 Roll, Reroll, Debug, & Glitch Triage
    # =========================================================================

    def test_phase1_glitch_locking(self) -> None:
        """Assert rolling a Glitch face sets is_locked = True."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.bot = BaseBot(0)
        red = create_colored_die(DieColor.RED, 1)
        red.faces = [red.faces[4]] * 6  # Glitch face
        p0.ready_for_release_dice = [red]

        execute_phase_1(engine)
        # Glitched die moved immediately to glitched_dice
        self.assertIn(red, p0.glitched_dice)

    def test_phase1_debug_action_unlock(self) -> None:
        """Verify spending 1 🔬 unlocks a glitched die for subsequent rerolls."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.patches = 2

        red = create_colored_die(DieColor.RED, 1)
        red.is_locked = True
        p0.ready_for_release_dice = [red]

        class UnlockBot(BaseBot):
            def choose_debug_unlocks(self, player_state, active_dice, *args, **kwargs):
                return [0]

            def choose_yahtzee_rerolls(self, player_state, active_dice, *args, **kwargs):
                return [0]

        p0.bot = UnlockBot(0)
        # Execute Phase 1
        execute_phase_1(engine)
        # In v0.23.0, debug unlocks in Phase 1 are deprecated; patches never decrease in Phase 1
        self.assertEqual(p0.patches, 2)

    def test_phase1_unresolved_glitch_moves_to_glitched_box(self) -> None:
        """Verify permanent dice with unresolved glitches move to glitched_dice."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        red = create_colored_die(DieColor.RED, 1)
        # Lock bot from rerolling
        class NoRerollBot(BaseBot):
            def choose_yahtzee_rerolls(self, *args, **kwargs):
                return []

        p0.bot = NoRerollBot(0)
        p0.ready_for_release_dice = [red]

        # Force roll to glitch face
        red.faces = [red.faces[4]] * 6
        execute_phase_1(engine)

        self.assertIn(red, p0.glitched_dice)
        self.assertNotIn(red, p0.in_production_dice)
        self.assertEqual(len(p0.ready_for_release_dice), 0)

    def test_phase1_unresolved_contractor_glitch_discarded(self) -> None:
        """Verify White contractor with unresolved glitch returns to supply, not Under Development."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        for p in engine.state.players:
            p.bot = BaseBot(p.player_id)
        p0 = engine.state.players[0]
        contractor = create_white_die(99)
        contractor.faces = [contractor.faces[4]] * 6  # Glitch
        p0.contractor_dice = [contractor]
        p0.ready_for_release_dice = []

        supply_before = engine.state.contractor_supply
        execute_phase_1(engine)

        self.assertEqual(engine.state.contractor_supply, supply_before + 1)
        self.assertEqual(len(p0.glitched_dice), 0)
        self.assertEqual(len(p0.in_production_dice), 0)

    def test_hash_matches_ignore_glitches(self) -> None:
        """Verify 3 of a kind yields +1 Secret, but Glitch faces never form matches."""
        # 3 identical non-glitch faces
        f_cash = Face(name="+$1", money=1)
        d1 = Die(1, DieColor.GRAY, 0, faces=[f_cash], current_face=f_cash)
        d2 = Die(2, DieColor.GRAY, 0, faces=[f_cash], current_face=f_cash)
        d3 = Die(3, DieColor.GRAY, 0, faces=[f_cash], current_face=f_cash)
        self.assertEqual(detect_hash_matches([d1, d2, d3]), 1)

        # 3 Glitches
        f_glitch = Face(name="Glitch (Locked)", is_glitch=True)
        g1 = Die(4, DieColor.RED, 4, faces=[f_glitch], current_face=f_glitch)
        g2 = Die(5, DieColor.RED, 4, faces=[f_glitch], current_face=f_glitch)
        g3 = Die(6, DieColor.RED, 4, faces=[f_glitch], current_face=f_glitch)
        self.assertEqual(detect_hash_matches([g1, g2, g3]), 0)

    def test_no_income_collected_in_phase1(self) -> None:
        """Verify money/patches/secrets do not increase during Phase 1 deployment."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        for p in engine.state.players:
            p.bot = BaseBot(p.player_id)
        p0 = engine.state.players[0]
        p0.money = 7
        p0.patches = 2
        p0.secrets = 8

        # Give player dice with pure income faces
        f_money = Face(name="+$2", money=2)
        f_patch = Face(name="+2 🔬", patches=2)
        d1 = Die(1, DieColor.RED, 4, faces=[f_money] * 6)
        d2 = Die(2, DieColor.GREEN, 4, faces=[f_patch] * 6)
        p0.ready_for_release_dice = [d1, d2]

        execute_phase_1(engine)

        # Invariant: money and patches must NOT have changed in Phase 1!
        self.assertEqual(p0.money, 7)
        self.assertEqual(p0.patches, 2)
        self.assertEqual(len(p0.in_production_dice), 2)

    # =========================================================================
    # Category 4: Phase 2 Zero-Wear Defense & Threat Resolution
    # =========================================================================

    def test_defensive_shields_zero_dice_wear(self) -> None:
        """Assert shields that block attack cubes remain safely in in_production_dice."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        blue_die = create_colored_die(DieColor.BLUE, 1)
        blue_die.production_role = ProductionRole.BLUE_SHIELD
        blue_die.current_face = Face("Block 1 Blue", block_amount=1, shield_color=ShieldColor.BLUE)

        p0.in_production_dice = [blue_die]
        commitments = [(p0, list(p0.in_production_dice), {0: ShieldColor.BLUE})]

        # Drop 1 Blue cube
        engine.state.staging_cup = {CubeColor.RED: 0, CubeColor.BLUE: 1, CubeColor.GREEN: 0, CubeColor.BLACK: 0}
        # Pre-prime tower with no stuck cubes
        for c in engine.state.tower.stuck_cubes:
            engine.state.tower.stuck_cubes[c] = 0

        execute_phase_2(engine, commitments)

        # Invariant: blue_die must NOT have moved to Under Development / unpatched!
        self.assertIn(blue_die, p0.in_production_dice)
        self.assertEqual(len(p0.glitched_dice), 0)

    def test_red_ransom_cash_only_leak(self) -> None:
        """Assert unblocked Red drains cash, and unpaid cash leaks 1:1 to Corporate Secrets."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.money = 2
        p0.secrets = 8
        p0.patches = 5  # Held patches cannot absorb ransom

        p0.in_production_dice = []
        commitments = [(p0, [], {})]

        # 4 Red cubes exit
        engine.state.tower.calculate_exit_probability = lambda count: 1.0
        engine.state.tower.reset()
        engine.state.staging_cup = {CubeColor.RED: 4, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0}
        for c in engine.state.tower.stuck_cubes:
            engine.state.tower.stuck_cubes[c] = 0

        execute_phase_2(engine, commitments)

        # Paid $2 cash; remaining $2 unpaid leaks flat 1 Secret under v0.31.0: 8 - 1 = 7 Secrets
        self.assertEqual(p0.money, 0)
        self.assertEqual(p0.patches, 5, "Patches cannot absorb cash-only ransom")
        self.assertEqual(p0.secrets, 7)

    def test_green_malware_glitches_in_production_die(self) -> None:
        """Verify unblocked Green moves 1 die from in_production_dice to glitched_dice."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        d1 = create_gray_die(1)
        d1.production_role = ProductionRole.INCOME
        p0.in_production_dice = [d1]
        commitments = [(p0, list(p0.in_production_dice), {})]

        engine.state.tower.calculate_exit_probability = lambda count: 1.0
        engine.state.tower.reset()
        engine.state.staging_cup = {CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 1, CubeColor.BLACK: 0}
        for c in engine.state.tower.stuck_cubes:
            engine.state.tower.stuck_cubes[c] = 0

        execute_phase_2(engine, commitments)

        self.assertEqual(len(p0.in_production_dice), 0)
        self.assertIn(d1, p0.glitched_dice)

    def test_green_malware_contractor_sacrifice(self) -> None:
        """Verify player can sacrifice 1 active White contractor instead of glitching a die."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        d1 = create_gray_die(1)
        d1.production_role = ProductionRole.INCOME
        p0.in_production_dice = [d1]

        contractor = create_white_die(99)
        p0.contractor_dice = [contractor]
        commitments = [(p0, list(p0.in_production_dice), {})]

        engine.state.tower.calculate_exit_probability = lambda count: 1.0
        engine.state.tower.reset()
        engine.state.staging_cup = {CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 1, CubeColor.BLACK: 0}
        for c in engine.state.tower.stuck_cubes:
            engine.state.tower.stuck_cubes[c] = 0

        execute_phase_2(engine, commitments)

        # Contractor was sacrificed; d1 in in_production_dice is preserved
        self.assertIn(d1, p0.in_production_dice)
        self.assertEqual(len(p0.glitched_dice), 0)

    def test_green_malware_destruction_fallback(self) -> None:
        """Verify when in_production_dice is empty, unblocked Green fizzles with 0 penalty (v0.31.0 INV-MALWARE-FIZZLE-01)."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.ready_for_release_dice = []
        p0.in_production_dice = []
        p0.contractor_dice = []
        d_glitched = create_gray_die(1)
        p0.glitched_dice = [d_glitched]

        commitments = [(p0, [], {})]
        engine.state.tower.calculate_exit_probability = lambda count: 1.0
        engine.state.tower.reset()
        engine.state.staging_cup = {CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 1, CubeColor.BLACK: 0}
        for c in engine.state.tower.stuck_cubes:
            engine.state.tower.stuck_cubes[c] = 0

        execute_phase_2(engine, commitments)

        # Under v0.31.0 Malware Fizzle, glitched die is preserved and NOT destroyed
        self.assertEqual(len(p0.glitched_dice), 1)
        self.assertEqual(len(p0.total_dice), 1)

    def test_green_glitched_die_forfeits_income(self) -> None:
        """Verify a die glitched by Green malware in Phase 2 yields 0 income in Phase 3."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.money = 0
        p0.patches = 0

        f_money = Face(name="+$3", money=3)
        d1 = Die(1, DieColor.YELLOW, 5, faces=[f_money] * 6, current_face=f_money)
        d1.production_role = ProductionRole.INCOME
        p0.in_production_dice = [d1]

        # Phase 2 Green hits and glitches d1
        commitments = [(p0, list(p0.in_production_dice), {})]
        engine.state.tower.calculate_exit_probability = lambda count: 1.0
        engine.state.tower.reset()
        engine.state.staging_cup = {CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 1, CubeColor.BLACK: 0}
        for c in engine.state.tower.stuck_cubes:
            engine.state.tower.stuck_cubes[c] = 0

        execute_phase_2(engine, commitments)
        self.assertIn(d1, p0.glitched_dice)

        # Execute Phase 3
        execute_phase_3(engine)

        # Income must be $0 because die was glitched before Phase 3
        self.assertEqual(p0.money, 0)

    # =========================================================================
    # Category 5: Phase 3 Operations & Pipeline Prep
    # =========================================================================

    def test_phase3_income_collected_from_all_production_dice(self) -> None:
        """Verify surviving Income and Shield dice yield their printed resources."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.money = 0
        p0.patches = 0

        d_inc = create_gray_die(1)
        d_inc.current_face = Face("+$1", money=1)
        d_inc.production_role = ProductionRole.INCOME

        d_shield = create_colored_die(DieColor.RED, 2)
        d_shield.current_face = Face("R1: Ransom Insurance", block_amount=1, shield_color=ShieldColor.RED, money=2, is_star=True, star_code="R1")
        d_shield.production_role = ProductionRole.RED_SHIELD

        p0.in_production_dice = [d_inc, d_shield]

        execute_phase_3(engine)

        # Income collected: $1 from d_inc + $2 from d_shield = $3
        self.assertEqual(p0.money, 3)

    def test_phase3_fast_patching(self) -> None:
        """Verify spending 1 🔬 moves a die from glitched_dice to scanned_dice."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.patches = 2
        d1 = create_colored_die(DieColor.RED, 1)
        p0.glitched_dice = [d1]

        class FastPatchBot(BaseBot):
            def choose_fast_patches(self, player_state, game_state, rng):
                return [0]

        p0.bot = FastPatchBot(0)
        execute_phase_3(engine)

        # In v0.29.0 fast-patching is excised; triage shifts d1 to scanned with 0 patches
        self.assertEqual(p0.patches, 2)
        self.assertIn(d1, p0.scanned_dice)
        self.assertEqual(len(p0.glitched_dice), 0)

    def test_phase3_scanned_graduation(self) -> None:
        """Verify all dice in scanned_dice graduate to ready_for_release_dice."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        d1 = create_gray_die(1)
        p0.scanned_dice = [d1]
        p0.ready_for_release_dice = []
        p0.in_production_dice = []
        p0.glitched_dice = []

        execute_phase_3(engine)

        self.assertIn(d1, p0.ready_for_release_dice)
        self.assertEqual(len(p0.scanned_dice), 0)

    def test_phase3_production_return(self) -> None:
        """Verify all surviving in_production_dice return to ready_for_release_dice."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        d1 = create_gray_die(1)
        d1.production_role = ProductionRole.INCOME
        p0.in_production_dice = [d1]
        p0.ready_for_release_dice = []

        execute_phase_3(engine)

        self.assertIn(d1, p0.ready_for_release_dice)
        self.assertEqual(len(p0.in_production_dice), 0)
        self.assertIsNone(d1.production_role)

    def test_phase3_conveyor_shift(self) -> None:
        """Verify all remaining glitched_dice shift to scanned_dice."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.patches = 0  # No patches to fast-patch
        p0.ready_for_release_dice = []
        d1 = create_gray_die(1)
        p0.glitched_dice = [d1]
        p0.scanned_dice = []

        execute_phase_3(engine)

        # Unpatched die in Glitched shifts to Scanned at round end
        self.assertIn(d1, p0.scanned_dice)
        self.assertEqual(len(p0.glitched_dice), 0)
        self.assertNotIn(d1, p0.ready_for_release_dice)

    def test_natural_pipeline_graduation_lifecycle(self) -> None:
        """Trace a die through Glitched -> Scanned -> Ready over 2 rounds with 0 patch spent."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.money = 0
        p0.patches = 0
        d1 = create_colored_die(DieColor.RED, 1)

        # Round 1: Die enters Glitched
        p0.glitched_dice = [d1]
        p0.scanned_dice = []
        p0.in_production_dice = []
        p0.ready_for_release_dice = []

        # End of Round 1: shifts to Scanned
        execute_phase_3(engine)
        self.assertIn(d1, p0.scanned_dice)
        self.assertEqual(len(p0.glitched_dice), 0)
        self.assertEqual(len(p0.ready_for_release_dice), 0)

        # Round 2: sits in Scanned (offline)
        # End of Round 2: graduates to Ready for Release!
        execute_phase_3(engine)
        self.assertIn(d1, p0.ready_for_release_dice)
        self.assertEqual(len(p0.scanned_dice), 0)

    def test_patch_token_cap_cleanup(self) -> None:
        """Verify patch tokens in excess of 3 🔬 are discarded at round end."""
        engine = GameEngine(config=GameConfig.legacy_v034(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.patches = 5

        execute_phase_3(engine)

        self.assertEqual(p0.patches, 3)

    # =========================================================================
    # Category 6: Archetypes & System Reboot Excision
    # =========================================================================

    def test_phreaker_magnetic_splice(self) -> None:
        """Verify Phreaker moves 1 die from glitched_dice directly to ready_for_release_dice for free."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.archetype = get_archetype_by_code(ArchetypeCode.PHREAKER)
        p0.patches = 0

        d1 = create_colored_die(DieColor.RED, 1)
        p0.glitched_dice = [d1]
        p0.scanned_dice = []
        p0.ready_for_release_dice = []

        execute_phase_3(engine)

        # Spliced directly to ready_for_release_dice without passing through scanned
        self.assertIn(d1, p0.ready_for_release_dice)
        self.assertEqual(len(p0.glitched_dice), 0)
        self.assertTrue(p0.v1_used)

    def test_prodigy_brute_force_bypass(self) -> None:
        """Verify Prodigy rerolls locked dice freely and overrides 1 face to a legal non-Star face."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.archetype = get_archetype_by_code(ArchetypeCode.PRODIGY)
        p0.patches = 0  # 0 patches, but Prodigy bypasses locks freely

        red = create_colored_die(DieColor.RED, 1)
        p0.ready_for_release_dice = [red]

        class ProdigyBot(BaseBot):
            def choose_prodigy_ability(self, *args, **kwargs):
                return True

            def choose_yahtzee_rerolls(self, *args, **kwargs):
                return [0]

            def choose_prodigy_face_override(self, player_state, active_dice, *args, **kwargs):
                # Override to +$2
                return (0, Face("+$2", money=2))

        p0.bot = ProdigyBot(0)
        execute_phase_1(engine)

        self.assertTrue(p0.v1_used)
        self.assertEqual(len(p0.in_production_dice), 1)
        self.assertEqual(p0.in_production_dice[0].current_face.name, "+$2")

    def test_system_reboot_excised(self) -> None:
        """Verify can_system_reboot and execute_system_reboot are completely removed."""
        p = PlayerState(player_id=0, bot=BaseBot(0), money=5, secrets=8, patches=2)
        self.assertFalse(hasattr(p, "can_system_reboot"))
        self.assertFalse(hasattr(p, "execute_system_reboot"))
        self.assertFalse(hasattr(p, "system_reboot_used"))


if __name__ == "__main__":
    unittest.main()
