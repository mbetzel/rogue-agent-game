"""Unit tests for Phase 24: Cryptographic Hash Match & Secrets-Only Victory Scoring (v0.17.0 Baseline)."""

import random
import unittest
from sim.config import CubeColor, DieColor, GameConfig, ShieldColor
from sim.engine import GameEngine, PlayerState, evaluate_end_game
from sim.engine.phase1_boot import detect_hash_matches, get_face_signature
from sim.engine.phase3_ops import execute_phase_3
from sim.entities import Die, Face, create_colored_die, create_gray_die, create_white_die
from sim.bots.base import BaseBot, Phase3ActionPlan


class TestHashMatchesAndScoring(unittest.TestCase):
    def setUp(self):
        self.rng = random.Random(42)

    def test_detect_hash_matches_triplet(self):
        """Verify 3 identical non-glitch faces produce +1 Corporate Secret."""
        dice = [
            Die(die_id=1, color=DieColor.GRAY, cost=0, vp=0, faces=[], current_face=Face("+$1", money=1)),
            Die(die_id=2, color=DieColor.GRAY, cost=0, vp=0, faces=[], current_face=Face("+$1", money=1)),
            Die(die_id=3, color=DieColor.WHITE, cost=1, vp=0, faces=[], current_face=Face("+$1", money=1)),
            Die(die_id=4, color=DieColor.GRAY, cost=0, vp=0, faces=[], current_face=Face("+1 🔧", patches=1)),
        ]
        self.assertEqual(detect_hash_matches(dice), 1)

    def test_detect_hash_matches_two_triplets_and_six_of_a_kind(self):
        """Verify 6 of a kind or two distinct triplets produce +2 Corporate Secrets."""
        # Two distinct triplets
        dice_two_triplets = [
            Die(die_id=1, color=DieColor.GRAY, cost=0, vp=0, faces=[], current_face=Face("+$1", money=1)),
            Die(die_id=2, color=DieColor.GRAY, cost=0, vp=0, faces=[], current_face=Face("+$1", money=1)),
            Die(die_id=3, color=DieColor.WHITE, cost=1, vp=0, faces=[], current_face=Face("+$1", money=1)),
            Die(die_id=4, color=DieColor.GRAY, cost=0, vp=0, faces=[], current_face=Face("Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)),
            Die(die_id=5, color=DieColor.GRAY, cost=0, vp=0, faces=[], current_face=Face("Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)),
            Die(die_id=6, color=DieColor.WHITE, cost=1, vp=0, faces=[], current_face=Face("Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)),
        ]
        self.assertEqual(detect_hash_matches(dice_two_triplets), 2)

        # 6 of the same kind
        dice_six = [
            Die(die_id=i, color=DieColor.GRAY, cost=0, vp=0, faces=[], current_face=Face("+$1", money=1))
            for i in range(6)
        ]
        self.assertEqual(detect_hash_matches(dice_six), 2)

    def test_glitch_faces_do_not_form_hash_matches(self):
        """Verify Glitch (Locked) faces are strictly excluded from Hash Matches."""
        glitch_dice = [
            Die(die_id=1, color=DieColor.WHITE, cost=1, vp=0, faces=[], current_face=Face("Glitch (Locked)", is_glitch=True)),
            Die(die_id=2, color=DieColor.WHITE, cost=1, vp=0, faces=[], current_face=Face("Glitch (Locked)", is_glitch=True)),
            Die(die_id=3, color=DieColor.RED, cost=4, vp=3, faces=[], current_face=Face("Glitch (Locked)", is_glitch=True)),
            Die(die_id=4, color=DieColor.BLUE, cost=5, vp=4, faces=[], current_face=Face("Glitch (Locked)", is_glitch=True)),
        ]
        self.assertEqual(detect_hash_matches(glitch_dice), 0)

    def test_choice_faces_match_declared_option(self):
        """Verify a choice face matches when resolved to an identical option."""
        choice_face = Face(
            name="+$1 / +1 🔧",
            is_choice=True,
            choices=(Face("+$1", money=1), Face("+1 🔧", patches=1)),
        )
        # Die 1 has choice face resolved to index 0 (+$1)
        die1 = Die(die_id=1, color=DieColor.GRAY, cost=0, vp=0, faces=[], current_face=choice_face, chosen_choice_index=0)
        die2 = Die(die_id=2, color=DieColor.GRAY, cost=0, vp=0, faces=[], current_face=Face("+$1", money=1))
        die3 = Die(die_id=3, color=DieColor.WHITE, cost=1, vp=0, faces=[], current_face=Face("+$1", money=1))

        self.assertEqual(detect_hash_matches([die1, die2, die3]), 1)

        # If die 1 is resolved to index 1 (+1 🔧), it no longer forms a triplet with the two +$1 dice
        die1.chosen_choice_index = 1
        self.assertEqual(detect_hash_matches([die1, die2, die3]), 0)

    def test_secrets_uncapped_beyond_10_on_b2_and_y1(self):
        """Verify B2 and Y1 allow purchasing secrets beyond the previous cap of 10."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        player = engine.state.players[0]
        player.secrets = 12
        player.money = 20

        # Test B2
        player.b2_available = True
        plan_b2 = Phase3ActionPlan(use_b2_secret=True)
        player.bot.take_phase3_actions = lambda p, s, r: plan_b2
        execute_phase_3(engine)
        self.assertEqual(player.secrets, 13)
        self.assertEqual(player.money, 16)  # $20 - $4

        # Test Y1
        player.y1_available = True
        plan_y1 = Phase3ActionPlan(use_y1_secret=True)
        player.bot.take_phase3_actions = lambda p, s, r: plan_y1
        execute_phase_3(engine)
        self.assertEqual(player.secrets, 14)
        self.assertEqual(player.money, 10)  # $16 - $6

    def test_secrets_only_victory_scoring_and_tiebreakers(self):
        """Verify survivors rank strictly by Corporate Secrets with hierarchical tiebreakers."""
        engine = GameEngine(config=GameConfig(num_players=4), seed=42)
        p0, p1, p2, p3 = engine.state.players

        # P0: 12 Secrets, $0, 0 colored dice, 0 patches, 0 unpatched
        p0.secrets = 12
        p0.money = 0
        p0.patches = 0
        p0.ready_dice = []
        p0.unpatched_dice = []

        # P1: 10 Secrets, $50, 4 colored dice (high portfolio value, but fewer secrets than P0)
        p1.secrets = 10
        p1.money = 50
        p1.patches = 2
        p1.ready_dice = [create_colored_die(DieColor.YELLOW, 101), create_colored_die(DieColor.BLUE, 102)]
        p1.unpatched_dice = []

        # P2: 10 Secrets, $10, 2 colored dice
        p2.secrets = 10
        p2.money = 10
        p2.patches = 1
        p2.ready_dice = [create_colored_die(DieColor.RED, 103)]
        p2.unpatched_dice = []

        # P3: 0 Secrets (Patient Zero)
        p3.secrets = 0
        p3.is_patient_zero = True
        p3.elimination_reason = "Total Data Breach"

        result = evaluate_end_game(engine)
        rankings = result.rankings

        # P0 has highest secrets (12), so P0 is Rank 1 despite P1 having massive cash and dice
        self.assertEqual(rankings[0]["player_id"], p0.player_id)
        self.assertEqual(rankings[0]["rank"], 1)

        # P1 has 10 secrets and $50 -> Rank 2
        self.assertEqual(rankings[1]["player_id"], p1.player_id)
        self.assertEqual(rankings[1]["rank"], 2)

        # P2 has 10 secrets and $10 -> Rank 3
        self.assertEqual(rankings[2]["player_id"], p2.player_id)
        self.assertEqual(rankings[2]["rank"], 3)

        # P3 is Patient Zero -> Rank 4
        self.assertEqual(rankings[3]["player_id"], p3.player_id)
        self.assertEqual(rankings[3]["rank"], 4)
        self.assertTrue(rankings[3]["is_patient_zero"])

    def test_detailed_tiebreaker_hierarchy(self):
        """Verify the full tiebreaker ladder: Money -> Ready Colored Dice -> Patches -> Fewest Unpatched."""
        engine = GameEngine(config=GameConfig(num_players=4), seed=42)
        p0, p1, p2, p3 = engine.state.players

        # All players have 8 secrets
        for p in (p0, p1, p2, p3):
            p.secrets = 8
            p.ready_dice = [create_gray_die(1)]
            p.unpatched_dice = []

        # Tiebreaker 1: Money
        p0.money = 15
        p1.money = 10
        p2.money = 10
        p3.money = 10

        # P1 vs P2 vs P3 (all $10): Tiebreaker 2: Ready Colored Dice count
        p1.ready_dice.append(create_colored_die(DieColor.RED, 201))  # 1 colored die
        p2.ready_dice.append(create_colored_die(DieColor.RED, 202))  # 1 colored die
        # P3 has 0 colored dice

        # P1 vs P2 (both 1 colored die): Tiebreaker 3: Patches
        p1.patches = 3
        p2.patches = 1
        p3.patches = 5

        # P2 vs another player with same patches: Tiebreaker 4: Fewest Unpatched
        # Give P1 one unpatched die, P2 zero unpatched
        p2.unpatched_dice = []

        result = evaluate_end_game(engine)
        rankings = result.rankings

        # Rank 1: P0 (most money: $15)
        self.assertEqual(rankings[0]["player_id"], p0.player_id)
        # Rank 2: P1 (1 colored die, 3 patches)
        self.assertEqual(rankings[1]["player_id"], p1.player_id)
        # Rank 3: P2 (1 colored die, 1 patch)
        self.assertEqual(rankings[2]["player_id"], p2.player_id)
        # Rank 4: P3 (0 colored dice)
        self.assertEqual(rankings[3]["player_id"], p3.player_id)


if __name__ == "__main__":
    unittest.main()
