"""Unit and Integration Tests for Phase 39: Blue Variant Rebalance — B1 & B3 (v0.32.0 Baseline)."""

from __future__ import annotations

import random
import unittest

from sim.bots.base import BaseBot, Phase3ActionPlan
from sim.config import CubeColor, DieColor, GameConfig, ShieldColor
from sim.engine.core import GameEngine
from sim.engine.phase2_threat import resolve_player_defense_and_wear
from sim.engine.phase3_ops import collect_player_production_income, execute_phase_3
from sim.engine.state import ProductionRole
from sim.entities import (
    Die,
    Face,
    create_colored_die,
    create_gray_die,
    get_all_variant_cards,
)
from web.controller.core import GameController


class TestV320BlueVariants(unittest.TestCase):
    """Test suite verifying v0.32.0 Blue Variant Rebalance invariants (TEST-V320-01 through TEST-V320-13)."""

    def setUp(self) -> None:
        self.rng = random.Random(42)
        self.variants = get_all_variant_cards()

    def test_v320_01_b1_metadata_and_description(self) -> None:
        """TEST-V320-01: INV-B1-BOUNTY-01: Inspect get_all_variant_cards()['B1'] metadata, cost, star face, and description."""
        b1 = self.variants["B1"]
        self.assertEqual(b1.code, "B1")
        self.assertEqual(b1.name, "Honeypot Telemetry")
        self.assertEqual(b1.die_color, DieColor.BLUE)
        self.assertEqual(b1.cost, 5)
        self.assertEqual(b1.star_face.block_amount, 2)
        self.assertEqual(b1.star_face.shield_color, ShieldColor.BLUE)
        self.assertEqual(b1.star_face.money, 0)
        self.assertTrue(b1.star_face.is_star)
        self.assertEqual(b1.star_face.star_code, "B1")
        self.assertIn("+$2", b1.description)
        self.assertNotIn("+$3", b1.description)

    def test_v320_02_b1_bounty_awards_plus_2_when_blue_exits_and_zero_unblocked(self) -> None:
        """TEST-V320-02: INV-B1-BOUNTY-01: Player commits 1 B1 die (Block 2 Blue).
        Tower drops 2 Blue cubes (attack_strengths[BLUE] = 2). Unblocked Blue = 0.
        B1 blocks both Blue cubes and awards exactly +$2 cash (player.money increases by 2, not 3).
        """
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.money = 5
        p0.secrets = 8

        b1_card = self.variants["B1"]
        d_b1 = create_colored_die(DieColor.BLUE, 1, variant_card=b1_card)
        d_b1.production_role = ProductionRole.BLUE_SHIELD
        d_b1.current_face = b1_card.star_face

        p0.in_production_dice = [d_b1]
        rolled = [d_b1]
        commitments = {0: ShieldColor.BLUE}

        resolve_player_defense_and_wear(
            engine=engine,
            player=p0,
            rolled_dice=rolled,
            commitments=commitments,
            attack_strengths={CubeColor.RED: 0, CubeColor.BLUE: 2, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 0, CubeColor.BLUE: 2, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        self.assertEqual(p0.secrets, 8, "Both Blue cubes blocked")
        self.assertEqual(p0.money, 7, "Player money increased by exactly +$2 (from 5 to 7)")

    def test_v320_03_b1_bounty_zero_when_zero_blue_cubes_exit(self) -> None:
        """TEST-V320-03: INV-B1-BOUNTY-01: Player commits 1 B1 die (Block 2 Blue).
        Tower drops 0 Blue cubes (exited_cubes[BLUE] = 0).
        Unblocked Blue is 0, but because 0 Blue cubes exited the tower, B1 awards $0 bonus cash.
        """
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.money = 5
        p0.secrets = 8

        b1_card = self.variants["B1"]
        d_b1 = create_colored_die(DieColor.BLUE, 1, variant_card=b1_card)
        d_b1.production_role = ProductionRole.BLUE_SHIELD
        d_b1.current_face = b1_card.star_face

        p0.in_production_dice = [d_b1]
        rolled = [d_b1]
        commitments = {0: ShieldColor.BLUE}

        resolve_player_defense_and_wear(
            engine=engine,
            player=p0,
            rolled_dice=rolled,
            commitments=commitments,
            attack_strengths={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        self.assertEqual(p0.secrets, 8)
        self.assertEqual(p0.money, 5, "B1 awards $0 bonus cash when 0 Blue cubes exit")

    def test_v320_04_b1_bounty_zero_when_unblocked_blue_greater_than_zero(self) -> None:
        """TEST-V320-04: INV-B1-BOUNTY-01: Player commits 1 B1 die (Block 2 Blue).
        Tower drops 3 Blue cubes (attack_strengths[BLUE] = 3). Unblocked Blue = 1.
        B1 blocks 2 Blue cubes, player loses 1 Secret, and because unblocked_blue > 0, B1 awards $0 bonus cash.
        """
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.money = 5
        p0.secrets = 8

        b1_card = self.variants["B1"]
        d_b1 = create_colored_die(DieColor.BLUE, 1, variant_card=b1_card)
        d_b1.production_role = ProductionRole.BLUE_SHIELD
        d_b1.current_face = b1_card.star_face

        p0.in_production_dice = [d_b1]
        rolled = [d_b1]
        commitments = {0: ShieldColor.BLUE}

        resolve_player_defense_and_wear(
            engine=engine,
            player=p0,
            rolled_dice=rolled,
            commitments=commitments,
            attack_strengths={CubeColor.RED: 0, CubeColor.BLUE: 3, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 0, CubeColor.BLUE: 3, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        self.assertEqual(p0.secrets, 7, "1 unblocked Blue cube causes 1 Secret loss")
        self.assertEqual(p0.money, 5, "B1 awards $0 bonus cash when unblocked_blue > 0")

    def test_v320_05_b1_bounty_credited_before_red_ransomware_payment(self) -> None:
        """TEST-V320-05: INV-B1-BOUNTY-01: Player has $0 cash, commits 1 B1 die, and faces 1 Blue cube + 2 Red cubes.
        B1 blocks the 1 Blue cube, grants +$2 cash in Step 6, and Step 7 uses that $2 to fully pay the 2 Red ransomware cubes (0 Secrets lost).
        """
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.money = 0
        p0.secrets = 8

        b1_card = self.variants["B1"]
        d_b1 = create_colored_die(DieColor.BLUE, 1, variant_card=b1_card)
        d_b1.production_role = ProductionRole.BLUE_SHIELD
        d_b1.current_face = b1_card.star_face

        p0.in_production_dice = [d_b1]
        rolled = [d_b1]
        commitments = {0: ShieldColor.BLUE}

        resolve_player_defense_and_wear(
            engine=engine,
            player=p0,
            rolled_dice=rolled,
            commitments=commitments,
            attack_strengths={CubeColor.RED: 2, CubeColor.BLUE: 1, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 2, CubeColor.BLUE: 1, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        self.assertEqual(p0.money, 0, "+$2 from B1 was immediately spent to pay 2 Red ransomware")
        self.assertEqual(p0.secrets, 8, "0 Secrets lost because B1 funded the Red ransomware")

    def test_v320_06_b3_metadata_and_description(self) -> None:
        """TEST-V320-06: INV-B3-BACKUP-01: Inspect get_all_variant_cards()['B3'] metadata, cost, star face, and description."""
        b3 = self.variants["B3"]
        self.assertEqual(b3.code, "B3")
        self.assertEqual(b3.name, "Air-Gapped Backup")
        self.assertEqual(b3.die_color, DieColor.BLUE)
        self.assertEqual(b3.cost, 4)
        self.assertEqual(b3.star_face.block_amount, 1)
        self.assertEqual(b3.star_face.shield_color, ShieldColor.BLUE)
        self.assertTrue(b3.star_face.is_star)
        self.assertEqual(b3.star_face.star_code, "B3")
        self.assertEqual(
            b3.description,
            "Block 1 Blue; in Phase 3A, move 1 die from your Glitched Box to your Scanned Box.",
        )

    def test_v320_07_b3_selects_highest_value_colored_die_from_glitched_box(self) -> None:
        """TEST-V320-07: INV-B3-BACKUP-01: Player has 1 surviving B3 die in in_production_dice and 3 dice in glitched_dice:
        Gray (cost=0, id=1), Red (cost=4, id=2), Yellow (cost=6, id=3). Call collect_player_production_income.
        B3 selects Yellow (cost=6, colored), removes it from glitched_dice, clears transient roll/role fields, and appends it to scanned_dice.
        """
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]

        b3_card = self.variants["B3"]
        d_b3 = create_colored_die(DieColor.BLUE, 10, variant_card=b3_card)
        d_b3.production_role = ProductionRole.BLUE_SHIELD
        d_b3.current_face = b3_card.star_face
        p0.in_production_dice = [d_b3]

        d_gray = create_gray_die(1)
        d_red = create_colored_die(DieColor.RED, 2, variant_card=self.variants["R3"])  # cost=4
        d_yellow = create_colored_die(DieColor.YELLOW, 3, variant_card=self.variants["Y1"])  # cost=6
        d_yellow.production_role = ProductionRole.INCOME
        d_yellow.is_locked = True
        d_yellow.chosen_choice_index = 1
        d_yellow.current_face = d_yellow.faces[0]
        setattr(d_yellow, "rolled_face_idx", 0)
        setattr(d_yellow, "overclock_face", d_yellow.faces[0])

        p0.glitched_dice = [d_gray, d_red, d_yellow]
        p0.scanned_dice = []

        collect_player_production_income(engine, p0)

        self.assertIn(d_yellow, p0.scanned_dice)
        self.assertNotIn(d_yellow, p0.glitched_dice)
        self.assertIn(d_gray, p0.glitched_dice)
        self.assertIn(d_red, p0.glitched_dice)
        self.assertIsNone(d_yellow.production_role)
        self.assertFalse(d_yellow.is_locked)
        self.assertIsNone(d_yellow.chosen_choice_index)
        self.assertIsNone(d_yellow.current_face)
        self.assertIsNone(getattr(d_yellow, "rolled_face_idx", None))
        self.assertIsNone(getattr(d_yellow, "overclock_face", None))

    def test_v320_08_b3_tiebreaker_deterministic_by_die_id(self) -> None:
        """TEST-V320-08: INV-B3-BACKUP-01: Tiebreaker check: Player has 1 surviving B3 die in in_production_dice
        and 2 Colored dice in glitched_dice with equal cost (cost=5, die_id=10 vs cost=5, die_id=25).
        B3 deterministically selects die_id=25 via (1, 5, 25) > (1, 5, 10) and moves it to scanned_dice.
        """
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]

        b3_card = self.variants["B3"]
        d_b3 = create_colored_die(DieColor.BLUE, 1, variant_card=b3_card)
        d_b3.production_role = ProductionRole.BLUE_SHIELD
        d_b3.current_face = b3_card.star_face
        p0.in_production_dice = [d_b3]

        d_10 = create_colored_die(DieColor.RED, 10, variant_card=self.variants["R1"])  # cost=5
        d_25 = create_colored_die(DieColor.GREEN, 25, variant_card=self.variants["G1"])  # cost=5
        p0.glitched_dice = [d_10, d_25]
        p0.scanned_dice = []

        collect_player_production_income(engine, p0)

        self.assertEqual(p0.scanned_dice, [d_25])
        self.assertEqual(p0.glitched_dice, [d_10])

    def test_v320_09_b3_empty_glitched_box_clean_noop(self) -> None:
        """TEST-V320-09: INV-B3-BACKUP-01: Empty Glitched Box check: Player has 1 surviving B3 die in in_production_dice
        and glitched_dice == []. Call collect_player_production_income.
        Clean no-op: glitched_dice and scanned_dice remain unchanged, no exception raised.
        """
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]

        b3_card = self.variants["B3"]
        d_b3 = create_colored_die(DieColor.BLUE, 1, variant_card=b3_card)
        d_b3.production_role = ProductionRole.BLUE_SHIELD
        d_b3.current_face = b3_card.star_face
        p0.in_production_dice = [d_b3]
        p0.glitched_dice = []
        p0.scanned_dice = []

        collect_player_production_income(engine, p0)

        self.assertEqual(p0.glitched_dice, [])
        self.assertEqual(p0.scanned_dice, [])

    def test_v320_10_b3_full_round_pipeline_synergy_with_green_malware(self) -> None:
        """TEST-V320-10: INV-B3-BACKUP-01: Full round pipeline synergy: Player has B3 (Blue Shield) and a Gray die
        (Block 1 Any) in in_production_dice, glitched_dice initially empty. Phase 2B drops 1 Blue and 1 Green cube.
        B3 blocks the 1 Blue cube. Unblocked Green glitches the Gray die into glitched_dice.
        In Phase 3A, surviving B3 recovers the Gray die from glitched_dice to scanned_dice.
        In Phase 3B, the Gray die graduates from scanned_dice to ready_for_release_dice!
        """
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.secrets = 8
        p0.money = 5
        p0.ready_for_release_dice = []
        p0.glitched_dice = []
        p0.scanned_dice = []

        b3_card = self.variants["B3"]
        d_b3 = create_colored_die(DieColor.BLUE, 10, variant_card=b3_card)
        d_b3.production_role = ProductionRole.BLUE_SHIELD
        d_b3.current_face = b3_card.star_face

        d_gray = create_gray_die(1)
        d_gray.production_role = ProductionRole.ANY_SHIELD
        d_gray.current_face = Face("Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)

        p0.in_production_dice = [d_b3, d_gray]
        rolled = [d_b3, d_gray]
        # Only commit d_b3 to BLUE_SHIELD so Green is unblocked (or commit d_gray as ANY_SHIELD, wait: if d_gray is ANY_SHIELD and blocks Green, Green wouldn't be unblocked! Let's face 2 Green cubes or have d_gray already spent blocking Blue).
        # Specifically: B3 blocks 1 Blue cube, d_gray is in in_production_dice as ANY_SHIELD (say 2 Blue + 1 Green dropped so d_gray blocked the 2nd Blue, leaving 1 Green unblocked).
        commitments = {0: ShieldColor.BLUE, 1: ShieldColor.ANY}

        resolve_player_defense_and_wear(
            engine=engine,
            player=p0,
            rolled_dice=rolled,
            commitments=commitments,
            attack_strengths={CubeColor.RED: 0, CubeColor.BLUE: 2, CubeColor.GREEN: 1},
            exited_cubes={CubeColor.RED: 0, CubeColor.BLUE: 2, CubeColor.GREEN: 1},
            active_directive="NONE",
        )

        # After Phase 2B: B3 and Gray blocked the 2 Blue cubes; 1 unblocked Green glitched the Gray die!
        self.assertEqual(p0.in_production_dice, [d_b3])
        self.assertEqual(p0.glitched_dice, [d_gray])

        class NoOpBot(BaseBot):
            def plan_phase3(self, *args, **kwargs):
                return Phase3ActionPlan()

        p0.bot = NoOpBot(0)
        engine.state.players[1].bot = NoOpBot(1)
        engine.state.players[1].in_production_dice = []
        engine.state.players[1].glitched_dice = []
        engine.state.players[1].scanned_dice = []

        # Execute Phase 3 (3A income & B3 triage -> 3B pipeline graduation)
        execute_phase_3(engine)

        # B3 moved d_gray from glitched_dice -> scanned_dice in Phase 3A, and d_b3 also entered scanned_dice at end of 3A.
        # In Phase 3B, release_bandwidth (default 3) graduates both d_gray and d_b3 to ready_for_release_dice!
        self.assertEqual(p0.glitched_dice, [])
        self.assertIn(d_gray, p0.ready_for_release_dice)
        self.assertIn(d_b3, p0.ready_for_release_dice)

    def test_v320_11_glitch_sort_key_pure_shield_before_b3_dual_output_shield(self) -> None:
        """TEST-V320-11: INV-GLITCH-SHIELD-PRIO-01: Player has 2 shields in in_production_dice:
        a $5 Blue die showing Face 1 (Block 1 Blue, pure shield) and a $4 Blue die showing B3 (Block 1 Blue + Phase 3A triage).
        1 unblocked Green malware hits.
        glitch_sort_key sacrifices the $5 pure shield (0, 0, 1, 5) BEFORE the $4 dual-output B3 shield (0, 1, 1, 4), preserving B3 for Phase 3A!
        """
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]

        b1_card = self.variants["B1"]  # cost=5
        d_pure = create_colored_die(DieColor.BLUE, 1, variant_card=b1_card)
        d_pure.production_role = ProductionRole.BLUE_SHIELD
        d_pure.current_face = Face("Block 1 Blue", block_amount=1, shield_color=ShieldColor.BLUE)

        b3_card = self.variants["B3"]  # cost=4
        d_b3 = create_colored_die(DieColor.BLUE, 2, variant_card=b3_card)
        d_b3.production_role = ProductionRole.BLUE_SHIELD
        d_b3.current_face = b3_card.star_face

        p0.in_production_dice = [d_b3, d_pure]
        p0.glitched_dice = []
        rolled = [d_b3, d_pure]
        commitments = {0: ShieldColor.BLUE, 1: ShieldColor.BLUE}

        resolve_player_defense_and_wear(
            engine=engine,
            player=p0,
            rolled_dice=rolled,
            commitments=commitments,
            attack_strengths={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 1},
            exited_cubes={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 1},
            active_directive="NONE",
        )

        self.assertEqual(p0.glitched_dice, [d_pure], "Pure $5 shield sacrificed first")
        self.assertEqual(p0.in_production_dice, [d_b3], "Dual-output $4 B3 shield preserved")

    def test_v320_12_glitch_sort_key_hierarchy_pure_vs_dual_vs_income(self) -> None:
        """TEST-V320-12: INV-GLITCH-SHIELD-PRIO-01: Verify glitch_sort_key across R1, G1, G2, and pure shields:
        pure Colored shield is sacrificed before R1/G1/G2, and R1/G1/G2 shields are sacrificed before non-shield Income dice.
        """
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]

        # Pure colored shield ($6 B2 showing basic Block 1 Blue)
        d_pure_shield = create_colored_die(DieColor.BLUE, 1, variant_card=self.variants["B2"])  # cost=6
        d_pure_shield.production_role = ProductionRole.BLUE_SHIELD
        d_pure_shield.current_face = Face("Block 1 Blue", block_amount=1, shield_color=ShieldColor.BLUE)

        # Dual-output Star shield ($4 G2 showing Block 1 Any + 1 Patch)
        g2_card = self.variants["G2"]  # cost=4
        d_dual_shield = create_colored_die(DieColor.GREEN, 2, variant_card=g2_card)
        d_dual_shield.production_role = ProductionRole.ANY_SHIELD
        d_dual_shield.current_face = g2_card.star_face

        # Gray Income die ($0 Gray showing +$1)
        d_gray_income = create_gray_die(3)
        d_gray_income.production_role = ProductionRole.INCOME
        d_gray_income.current_face = Face("+$1", money=1)

        p0.in_production_dice = [d_gray_income, d_dual_shield, d_pure_shield]
        p0.glitched_dice = []
        rolled = [d_gray_income, d_dual_shield, d_pure_shield]
        commitments = {2: ShieldColor.BLUE}  # Leave Green unblocked (don't commit d_dual_shield as ANY in commitments map so Green hits, while its production_role is ANY_SHIELD)

        # Hit with 2 unblocked Green malware cubes
        resolve_player_defense_and_wear(
            engine=engine,
            player=p0,
            rolled_dice=rolled,
            commitments=commitments,
            attack_strengths={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 2},
            exited_cubes={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 2},
            active_directive="NONE",
        )

        # 1st glitched: d_pure_shield (0, 0, 1, 6)
        # 2nd glitched: d_dual_shield (0, 1, 1, 4)
        # Surviving: d_gray_income (1, 1, 0, 0)
        self.assertEqual(p0.glitched_dice, [d_pure_shield, d_dual_shield])
        self.assertEqual(p0.in_production_dice, [d_gray_income])

    def test_v320_13_web_controller_b3_star_note_and_confirm_income_recovery(self) -> None:
        """TEST-V320-13: INV-WEB-UI-SYNC-01: Web controller integration:
        Human player rolls B3, executes compile_drop, and calls confirm_income selecting another die to glitch for Green Malware.
        compile_drop income breakdown includes star_note == 'Air-Gapped Backup (1 Glitched → Scanned)'.
        After confirm_income, the die glitched by Green Malware is immediately advanced by B3 from glitched_dice to scanned_dice.
        """
        controller = GameController()
        controller.new_game(num_players=2, seed=42)
        p0 = controller.state.players[0]
        meta0 = controller.player_meta[0]

        b3_card = self.variants["B3"]
        d_b3 = create_colored_die(DieColor.BLUE, 101, variant_card=b3_card)
        d_b3.current_face = b3_card.star_face
        d_b3.production_role = ProductionRole.BLUE_SHIELD

        d_red = create_colored_die(DieColor.RED, 102, variant_card=self.variants["R1"])
        d_red.current_face = Face("+$2", money=2)
        d_red.production_role = ProductionRole.INCOME

        p0.in_production_dice = [d_b3, d_red]
        p0.glitched_dice = []
        p0.scanned_dice = []
        meta0["rolled_pool"] = [d_b3, d_red]
        meta0["commitments"] = {"0": "blue"}

        # Ensure Phase 2 compile_drop can run cleanly
        controller.phase = 2
        res = controller.compile_drop()
        compile_res = res["last_compile_result"]

        # Verify B3 star_note in income_summary / human_income
        p0_details = compile_res["human_income"]["details"]
        b3_detail = next((item for item in p0_details if item["die_id"] == 101), None)
        self.assertIsNotNone(b3_detail)
        self.assertEqual(b3_detail["star_note"], "Air-Gapped Backup (1 Glitched → Scanned)")

        # Force 1 pending unblocked green malware on human player and call confirm_income selecting d_red (102)
        p0.pending_unblocked_green = 1
        controller.confirm_income(player_id=0, glitch_die_ids=[102])

        # d_red was glitched by Green Malware into glitched_dice, then immediately rescued by B3 into scanned_dice!
        self.assertEqual(p0.glitched_dice, [])
        self.assertIn(d_red, p0.scanned_dice)
        self.assertIn(d_b3, p0.scanned_dice)


if __name__ == "__main__":
    unittest.main()
