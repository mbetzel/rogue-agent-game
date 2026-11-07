"""Unit tests for v0.33.0 Step 2A Player Agency and Singularity rules.

Verifies:
1. `choose_colored_dice_to_return` 7-tier valuation hierarchy:
   - Tier 0: Glitched Box (least valuable)
   - Tier 1: Scanned Box
   - Tier 2: Redundant Shield in In Production
   - Tier 3: Ready Zone (non-shield)
   - Tier 4: In Production - Low Income (1 Coin/Compute)
   - Tier 5: In Production - Star Income (Shield + Coin, Star, Multi-Compute)
   - Tier 6: In Production - Strictly Needed Shield (most valuable)
2. Purple Specialist die scrapped on return (never returned to Central Market supply).
3. Step 2A White Contractor Sacrifice (discard to contractor_supply; never enters Glitched Box).
4. Step 2A Gray and Colored dice demotion directly into Glitched Box.
5. v3.0 Space 6 Singularity triggers immediate game end (skips Step 2B attack cubes and Phase 3).
6. v3.0 Corrupted Kernel Space 6 Patient Zero metadata populated on breach.
7. v3.0 Space 6 added cubes excised (Staging Cup remains empty).
"""

import unittest
from sim.config import CubeColor, DieColor, EndGameReason, GameConfig, ShieldColor
from sim.entities import (
    Die,
    Face,
    CorruptionSpace,
    VersionCard,
    create_colored_die,
    create_gray_die,
    create_white_die,
    get_all_version_cards,
)
from sim.engine.core import GameEngine
from sim.engine.state import ProductionRole
from sim.engine.phase2_threat import (
    demote_player_dice_step2a,
    return_player_colored_dice_step2a,
    execute_phase_2,
)


class TestV330Step2AAgencyAndSingularity(unittest.TestCase):
    def setUp(self):
        self.config = GameConfig.legacy_v035(num_players=2)
        self.engine = GameEngine(config=self.config, seed=42)
        self.p1 = self.engine.state.players[0]
        self.p2 = self.engine.state.players[1]
        self.bot = self.p1.bot

    def test_return_colored_dice_tier0_glitched_box(self):
        """Glitched colored dice are discarded before scanned, ready, or in_production."""
        d_glitched = create_colored_die(DieColor.GREEN, 101, cost=5)
        d_scanned = create_colored_die(DieColor.RED, 102, cost=5)
        d_ready = create_colored_die(DieColor.BLUE, 103, cost=5)

        self.p1.glitched_dice = [d_glitched]
        self.p1.scanned_dice = [d_scanned]
        self.p1.ready_for_release_dice = [d_ready]

        chosen = self.bot.choose_colored_dice_to_return(self.p1, count=1, threat_strengths={})
        self.assertEqual(len(chosen), 1)
        self.assertEqual(chosen[0].die_id, 101)

    def test_return_colored_dice_tier1_scanned_box(self):
        """Scanned colored dice are discarded before ready or in_production."""
        d_scanned = create_colored_die(DieColor.RED, 102, cost=5)
        d_ready = create_colored_die(DieColor.BLUE, 103, cost=5)

        self.p1.glitched_dice = []
        self.p1.scanned_dice = [d_scanned]
        self.p1.ready_for_release_dice = [d_ready]

        chosen = self.bot.choose_colored_dice_to_return(self.p1, count=1, threat_strengths={})
        self.assertEqual(len(chosen), 1)
        self.assertEqual(chosen[0].die_id, 102)

    def test_return_colored_dice_tier2_redundant_shield(self):
        """Redundant shields in In Production are discarded before ready dice."""
        d_shield1 = create_colored_die(DieColor.RED, 201, cost=5)
        d_shield1.current_face = Face(name="Block 1 Red", block_amount=1, shield_color=ShieldColor.RED)
        d_shield1.production_role = ProductionRole.RED_SHIELD

        d_shield2 = create_colored_die(DieColor.RED, 202, cost=5)
        d_shield2.current_face = Face(name="Block 1 Red", block_amount=1, shield_color=ShieldColor.RED)
        d_shield2.production_role = ProductionRole.RED_SHIELD

        d_ready = create_colored_die(DieColor.BLUE, 203, cost=5)

        self.p1.in_production_dice = [d_shield1, d_shield2]
        self.p1.ready_for_release_dice = [d_ready]
        self.p1.glitched_dice = []
        self.p1.scanned_dice = []

        # SETEC needs 1 Red shield: 1 is needed (Tier 6), 1 is redundant (Tier 2)
        threats = {CubeColor.RED: 1, CubeColor.BLUE: 0, CubeColor.GREEN: 0}

        chosen = self.bot.choose_colored_dice_to_return(self.p1, count=1, threat_strengths=threats)
        self.assertEqual(len(chosen), 1)
        # One of the redundant shields should be chosen before the ready die
        self.assertIn(chosen[0].die_id, [201, 202])

    def test_return_colored_dice_tier3_ready_zone(self):
        """Ready zone colored dice are discarded before in_production income dice."""
        d_ready = create_colored_die(DieColor.BLUE, 301, cost=5)
        d_prod = create_colored_die(DieColor.GREEN, 302, cost=5)
        d_prod.current_face = Face(name="+$1", money=1)
        d_prod.production_role = ProductionRole.INCOME

        self.p1.ready_for_release_dice = [d_ready]
        self.p1.in_production_dice = [d_prod]
        self.p1.glitched_dice = []
        self.p1.scanned_dice = []

        chosen = self.bot.choose_colored_dice_to_return(self.p1, count=1, threat_strengths={})
        self.assertEqual(len(chosen), 1)
        self.assertEqual(chosen[0].die_id, 301)

    def test_return_colored_dice_tier4_low_income(self):
        """Low income dice in In Production are discarded before star income dice."""
        d_low = create_colored_die(DieColor.BLUE, 401, cost=5)
        d_low.current_face = Face(name="+$1", money=1)
        d_low.production_role = ProductionRole.INCOME

        d_star = create_colored_die(DieColor.PURPLE, 402, cost=4)
        d_star.current_face = Face(name="Purple ★", is_star=True, star_code="PURPLE_STAR")
        d_star.production_role = ProductionRole.INCOME

        self.p1.in_production_dice = [d_low, d_star]
        self.p1.glitched_dice = []
        self.p1.scanned_dice = []
        self.p1.ready_for_release_dice = []

        chosen = self.bot.choose_colored_dice_to_return(self.p1, count=1, threat_strengths={})
        self.assertEqual(len(chosen), 1)
        self.assertEqual(chosen[0].die_id, 401)

    def test_return_colored_dice_tier5_star_income(self):
        """Star income dice in In Production are discarded before strictly needed shields."""
        d_star = create_colored_die(DieColor.PURPLE, 501, cost=4)
        d_star.current_face = Face(name="Purple ★", is_star=True, star_code="PURPLE_STAR")
        d_star.production_role = ProductionRole.INCOME

        d_needed_shield = create_colored_die(DieColor.RED, 502, cost=5)
        d_needed_shield.current_face = Face(name="Block 1 Red", block_amount=1, shield_color=ShieldColor.RED)
        d_needed_shield.production_role = ProductionRole.RED_SHIELD

        self.p1.in_production_dice = [d_star, d_needed_shield]
        self.p1.glitched_dice = []
        self.p1.scanned_dice = []
        self.p1.ready_for_release_dice = []

        # Red threat is present, so shield is strictly needed
        threats = {CubeColor.RED: 1, CubeColor.BLUE: 0, CubeColor.GREEN: 0}

        chosen = self.bot.choose_colored_dice_to_return(self.p1, count=1, threat_strengths=threats)
        self.assertEqual(len(chosen), 1)
        self.assertEqual(chosen[0].die_id, 501)

    def test_return_colored_dice_tier6_needed_shield_preserved(self):
        """When player has a choice between needed shield and other colored die, needed shield is preserved."""
        d_needed_shield = create_colored_die(DieColor.RED, 601, cost=5)
        d_needed_shield.current_face = Face(name="Block 1 Red", block_amount=1, shield_color=ShieldColor.RED)
        d_needed_shield.production_role = ProductionRole.RED_SHIELD

        d_other = create_colored_die(DieColor.BLUE, 602, cost=5)
        d_other.current_face = Face(name="+1 🔬", patches=1)
        d_other.production_role = ProductionRole.INCOME

        self.p1.in_production_dice = [d_needed_shield, d_other]
        self.p1.glitched_dice = []
        self.p1.scanned_dice = []
        self.p1.ready_for_release_dice = []

        threats = {CubeColor.RED: 1, CubeColor.BLUE: 0, CubeColor.GREEN: 0}

        chosen = self.bot.choose_colored_dice_to_return(self.p1, count=1, threat_strengths=threats)
        self.assertEqual(len(chosen), 1)
        self.assertEqual(chosen[0].die_id, 602)

    def test_return_colored_dice_purple_scrapped_not_in_market(self):
        """Purple specialist dice are scrapped and NOT returned to the Central Market supply."""
        d_purple = create_colored_die(DieColor.PURPLE, 701, cost=4)
        self.p1.ready_for_release_dice = [d_purple]
        initial_market_purple = self.engine.state.market.get(DieColor.PURPLE, 0)

        return_player_colored_dice_step2a(
            engine=self.engine,
            player=self.p1,
            rolled_dice=[],
            commitments={},
            count=1,
            threat_strengths={},
        )

        self.assertEqual(len(self.p1.ready_for_release_dice), 0)
        # Should NOT add PURPLE to market supply
        self.assertEqual(self.engine.state.market.get(DieColor.PURPLE, 0), initial_market_purple)
        self.assertNotIn(DieColor.PURPLE, self.engine.state.market)

    def test_step2a_demote_white_contractor_triggers_sacrifice(self):
        """White contractor dice in In Production trigger sacrifice (discarded to supply; not glitched)."""
        white_contractor = create_white_die(801)
        gray_legacy = create_gray_die(802)

        self.p1.in_production_dice = [white_contractor, gray_legacy]
        self.p1.contractor_dice = [white_contractor]
        initial_supply = self.engine.state.contractor_supply

        demote_player_dice_step2a(
            player=self.p1,
            rolled_dice=[],
            commitments={},
            count=1,
            threat_strengths={},
            engine=self.engine,
        )

        # White contractor should be sacrificed directly to contractor_supply
        self.assertEqual(self.engine.state.contractor_supply, initial_supply + 1)
        self.assertNotIn(white_contractor, self.p1.in_production_dice)
        self.assertNotIn(white_contractor, self.p1.contractor_dice)
        self.assertNotIn(white_contractor, self.p1.glitched_dice)
        # Gray die remains in production
        self.assertIn(gray_legacy, self.p1.in_production_dice)

    def test_step2a_demote_gray_and_colored_enters_glitched(self):
        """Gray and colored dice in In Production are demoted into Glitched Box."""
        gray_die = create_gray_die(901)
        blue_die = create_colored_die(DieColor.BLUE, 902, cost=5)

        self.p1.in_production_dice = [gray_die, blue_die]
        gray_die.production_role = ProductionRole.INCOME
        blue_die.production_role = ProductionRole.INCOME

        demote_player_dice_step2a(
            player=self.p1,
            rolled_dice=[],
            commitments={},
            count=2,
            threat_strengths={},
            engine=self.engine,
        )

        self.assertEqual(len(self.p1.in_production_dice), 0)
        self.assertEqual(len(self.p1.glitched_dice), 2)
        self.assertIn(gray_die, self.p1.glitched_dice)
        self.assertIn(blue_die, self.p1.glitched_dice)

    def test_v3_space6_singularity_immediate_game_over_skips_step2b(self):
        """Placing the 6th Black Cube on v3.0 Space 6 ends game immediately in Step 2A, skipping Step 2B."""
        v3_card = VersionCard(
            version_str="v3.0",
            name="Zero-Day Override",
            staging_payload={},
            directive_description="None.",
            directive_code="ZERO_DAY_OVERRIDE",
            corruption_track=(
                CorruptionSpace(index=1, label="Space 1"),
                CorruptionSpace(index=2, label="Space 2"),
                CorruptionSpace(index=3, label="Space 3"),
                CorruptionSpace(index=4, label="Space 4"),
                CorruptionSpace(index=5, label="Return 1 Colored Die", return_colored_dice=1),
                CorruptionSpace(index=6, label="Singularity", is_singularity=True),
            ),
        )
        self.engine.state.version_deck = [v3_card]
        self.engine.state.current_version_index = 0
        self.engine.state.corruption_track = 5  # 5 cubes currently; next advance hits space 6

        # Populate staging cup with 1 Black cube + attack cubes that would breach if Step 2B executed
        self.engine.state.staging_cup = {
            CubeColor.BLACK: 1,
            CubeColor.RED: 3,
            CubeColor.BLUE: 1,
            CubeColor.GREEN: 1,
        }
        self.engine.state.tower.drop = lambda cup, rng: dict(cup)
        self.p1.secrets = 10
        self.p2.secrets = 10

        commitments = [
            (self.p1, list(self.p1.in_production_dice), {}),
            (self.p2, list(self.p2.in_production_dice), {}),
        ]

        # Execute Phase 2
        execute_phase_2(self.engine, commitments)

        # Game must end immediately in Step 2A
        self.assertTrue(self.engine.state.game_over)
        self.assertFalse(self.engine.state.is_final_round)
        self.assertEqual(self.engine.state.end_reason, EndGameReason.SINGULARITY)
        # Players did not take damage from staging cup because Step 2B was skipped
        self.assertEqual(self.p1.secrets, 10)
        self.assertEqual(self.p2.secrets, 10)

    def test_v3_corrupted_kernel_space6_patient_zero_metadata(self):
        """Singularity with lose_secrets causing breach populates complete Patient Zero metadata."""
        v3_kernel = VersionCard(
            version_str="v3.0",
            name="Corrupted Kernel",
            staging_payload={},
            directive_description="None.",
            directive_code="CORRUPTED_KERNEL",
            corruption_track=(
                CorruptionSpace(index=1, label="Space 1"),
                CorruptionSpace(index=2, label="Space 2"),
                CorruptionSpace(index=3, label="Space 3"),
                CorruptionSpace(index=4, label="Space 4", lose_secrets=1),
                CorruptionSpace(index=5, label="Return 1 Colored Die", return_colored_dice=1),
                CorruptionSpace(index=6, label="Singularity: Lose 1 Secret", lose_secrets=1, is_singularity=True),
            ),
        )
        self.engine.state.version_deck = [v3_kernel]
        self.engine.state.current_version_index = 0
        self.engine.state.corruption_track = 5
        self.engine.state.current_round = 7

        # Set player 1 to 1 secret so lose_secrets=1 causes total data breach
        self.p1.secrets = 1
        self.p2.secrets = 5

        self.engine.state.staging_cup = {
            CubeColor.BLACK: 1,
            CubeColor.RED: 0,
            CubeColor.BLUE: 0,
            CubeColor.GREEN: 0,
        }
        self.engine.state.tower.drop = lambda cup, rng: dict(cup)

        commitments = [
            (self.p1, list(self.p1.in_production_dice), {}),
            (self.p2, list(self.p2.in_production_dice), {}),
        ]

        execute_phase_2(self.engine, commitments)

        self.assertTrue(self.engine.state.game_over)
        self.assertEqual(self.p1.secrets, 0)
        self.assertTrue(self.p1.is_patient_zero)
        self.assertEqual(self.p1.elimination_round, 7)
        self.assertEqual(self.p1.breach_depth, 0)
        self.assertEqual(self.p1.elimination_reason, "Total Breach (<= 0 Secrets)")

    def test_v3_space6_add_cubes_excised_staging_cup_empty(self):
        """v3.0 Space 6 has 0 add_cubes across all definitions."""
        for profile in ("STANDARD", "AGGRESSIVE"):
            cards = get_all_version_cards(profile=profile)
            for card in cards:
                if card.version_str == "v3.0":
                    space_6 = card.corruption_track[5]
                    self.assertEqual(
                        space_6.add_cubes, {}, f"Card {card.name} ({profile}) Space 6 has add_cubes={space_6.add_cubes}"
                    )


if __name__ == "__main__":
    unittest.main()
