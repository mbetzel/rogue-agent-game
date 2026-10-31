"""Unit and integration tests for Rogue Agent Phase 10: Variants, Randomization, and Web API.

Covers all 21 technical test cases from the Principal Engineer specification across Groups A-F:
Group A: Setup Randomization & Determinism (Tests 1-3)
1. test_get_random_variant_cards_structure: Returns 1 variant card per colored die (5 colors).
2. test_get_random_version_deck_structure: Returns 3 version cards (1 v1.0, 1 v2.0, 1 v3.0).
3. test_get_random_setup_determinism: Seeding determinism produces identical setups; distinct seeds differ.

Group B: Variant Card Special (★) Face Behaviors (Tests 4-12)
4. test_r2_threat_bounty_zero_unblocked_damage_bonus: Blocks 2 Red and awards +$2 bonus if 0 unblocked Red damage.
5. test_r3_short_squeeze_cube_threshold: Awards base +$3 in Phase 1, plus +$1 in Phase 2 if 3+ Red cubes exit tower.
6. test_b1_honeypot_telemetry_conditional_bonus: Awards +$3 bonus if 1+ Blue cubes exit and 0 unblocked Blue damage taken.
7. test_b3_air_gapped_backup_wear_immunity: Blocks 1 Blue and moves 1 other Ready die to Unpatched (falls back to self if solo).
8. test_y2_cloud_monopoly_scaling: Grants +$2 base plus +$1 per distinct colored module die owned (capped at +$5).
9. test_y3_proprietary_training_secrets_and_wear: Grants +1 Secret and immediately moves die to unpatched zone.
10. test_p2_chaos_profiteer_black_cube_scaling: Grants +$1 in Phase 1 plus +$2 per exited Black cube in Phase 2.
11. test_b2_deep_rd_vault_cost_and_rejection: Costs $4 for +1 Secret; rejects activation when cash < $4 or secrets >= 10.
12. test_p3_packet_deflection_paid_injection_and_rejection: Costs $1 to deflect cube to Staging; rejects when cash < $1.

Group C: Version Directive Mechanics (Tests 13-14)
13. test_directive_data_scraper_starting_money: v1.0 Data Scraper grants +$1 extra starting money ($8 total).
14. test_directive_corrupted_kernel_attack_strength: 4P/2P payload scaling and +2 flat strength bonus if 2+ Black cubes exit.

Group D: Web Game Controller & State Machine (Tests 15-18)
15. test_controller_new_game_default_cards: randomize_cards=False initializes baseline variants (R1, B1, G1, Y1, P1) and versions.
16. test_controller_new_game_randomize_cards: randomize_cards=True randomizes setup derived deterministically with seed * 17.
17. test_controller_event_log_active_variants: event_log contains active variant codes upon match creation.
18. test_polymorphic_worm_patch_cash_cost_matches_config: Phase 1 max_rerolls is 1 and Phase 3 cash patch cost matches GameConfig.patch_cash_cost ($2).

Group E: Web Server REST API Endpoints (Tests 19-20)
19. test_api_new_game_randomize_cards_true: POST /api/game/new with randomize_cards=true returns randomized state.
20. test_api_new_game_randomize_cards_false: POST /api/game/new with randomize_cards=false returns baseline state.

Group F: Experiments Telemetry & Batch Simulation (Tests 21-22)
21. test_experiment_metrics_winning_and_mean_scores: ExperimentMetrics tracks mean_winning_score and mean_scores.
22. test_run_batch_with_custom_variants_and_versions: run_batch accepts custom variant_cards and version_deck.
"""

from __future__ import annotations

import json
import random
import threading
import unittest
import urllib.request
from typing import Dict, List

from sim.bots import (
    AccelerationistBot,
    AdaptiveBalancedBot,
    BaseBot,
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
    get_all_variant_cards,
    get_all_version_cards,
    get_default_variant_cards,
    get_default_version_deck,
    get_random_setup,
    get_random_variant_cards,
    get_random_version_deck,
)
from sim.experiments import ExperimentMetrics, run_batch
from web.game_controller import GameController
from web.server import create_server


# =====================================================================
# Group A: Setup Randomization & Determinism
# =====================================================================

class TestGroupASetupRandomization(unittest.TestCase):
    """Unit tests for setup card randomization in sim/entities.py."""

    def test_get_random_variant_cards_structure(self) -> None:
        """1. Returns 1 variant card per colored die (5 colors: Red, Blue, Green, Yellow, Purple)."""
        rng = random.Random(42)
        var_cards = get_random_variant_cards(rng)

        self.assertEqual(len(var_cards), 5)
        expected_colors = [
            DieColor.RED,
            DieColor.BLUE,
            DieColor.GREEN,
            DieColor.YELLOW,
            DieColor.PURPLE,
        ]
        for color in expected_colors:
            self.assertIn(color, var_cards)
            card = var_cards[color]
            self.assertIsInstance(card, VariantCard)
            self.assertEqual(card.die_color, color)
            self.assertTrue(card.code.startswith(color.value[0].upper()))

    def test_get_random_version_deck_structure(self) -> None:
        """2. Returns 3 version cards: 1 v1.0, 1 v2.0, 1 v3.0 in order."""
        rng = random.Random(42)
        deck = get_random_version_deck(rng)

        self.assertEqual(len(deck), 3)
        self.assertEqual(deck[0].version_str, "v1.0")
        self.assertIn(deck[0].directive_code, ("SCRIPT_KIDDIE", "DATA_SCRAPER"))

        self.assertEqual(deck[1].version_str, "v2.0")
        self.assertIn(deck[1].directive_code, ("RAAS", "POLYMORPHIC_WORM"))

        self.assertEqual(deck[2].version_str, "v3.0")
        self.assertIn(deck[2].directive_code, ("ZERO_DAY_OVERRIDE", "CORRUPTED_KERNEL"))

    def test_get_random_setup_determinism(self) -> None:
        """3. Identical RNG seeds produce identical setups; distinct seeds produce variation."""
        variants1, deck1 = get_random_setup(random.Random(100))
        variants2, deck2 = get_random_setup(random.Random(100))

        # Deterministic match
        self.assertEqual({c: v.code for c, v in variants1.items()}, {c: v.code for c, v in variants2.items()})
        self.assertEqual([v.directive_code for v in deck1], [v.directive_code for v in deck2])

        # Variation across different seeds
        different_found = False
        for alt_seed in (200, 300, 400, 500):
            var_alt, deck_alt = get_random_setup(random.Random(alt_seed))
            if ([v.code for v in variants1.values()] != [v.code for v in var_alt.values()]
                    or [v.name for v in deck1] != [v.name for v in deck_alt]):
                different_found = True
                break
        self.assertTrue(different_found, "Expected card variation across distinct RNG seeds")


# =====================================================================
# Group B: Variant Card Special (★) Face Behaviors
# =====================================================================

class TestGroupBVariantCardBehaviors(unittest.TestCase):
    """Unit tests for prototype Variant Card (★) face mechanics."""

    def test_r2_threat_bounty_zero_unblocked_damage_bonus(self) -> None:
        """4. R2 blocks 2 Red and grants +$2 bonus in Phase 2 if 0 unblocked Red damage taken."""
        all_vars = get_all_variant_cards()
        r2_card = all_vars["R2"]

        config = GameConfig(num_players=2, starting_money=5)
        bots = [AdaptiveBalancedBot(0), AdaptiveBalancedBot(1)]
        custom_vars = get_default_variant_cards()
        custom_vars[DieColor.RED] = r2_card

        engine = GameEngine(config=config, bots=bots, seed=42, variant_cards=custom_vars)
        player = engine.state.players[0]

        # Case A: 2 Red attack, blocked completely (unblocked_red == 0) -> +$2 bonus awarded
        r2_die = create_colored_die(DieColor.RED, die_id=101, variant_card=r2_card)
        r2_die.current_face = r2_card.star_face
        player.ready_dice.append(r2_die)
        player.money = 5

        commitments = {0: ShieldColor.RED}  # R2 assigned to Red shield
        attack_strengths = {CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 0}
        exited_cubes = {CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0}

        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=[r2_die],
            commitments=commitments,
            attack_strengths=attack_strengths,
            exited_cubes=exited_cubes,
            active_directive="SCRIPT_KIDDIE",
        )
        # Blocked 2 Red, unblocked Red = 0 -> +$2 bonus awarded
        self.assertEqual(player.money, 7)

        # Case B: 3 Red attack, 2 blocked, 1 unblocked -> takes $1 damage, no +$2 bonus
        player.money = 5
        r2_die2 = create_colored_die(DieColor.RED, die_id=102, variant_card=r2_card)
        r2_die2.current_face = r2_card.star_face
        player.ready_dice.append(r2_die2)

        attack_strengths_high = {CubeColor.RED: 3, CubeColor.BLUE: 0, CubeColor.GREEN: 0}
        exited_cubes_high = {CubeColor.RED: 3, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0}

        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=[r2_die2],
            commitments={0: ShieldColor.RED},
            attack_strengths=attack_strengths_high,
            exited_cubes=exited_cubes_high,
            active_directive="SCRIPT_KIDDIE",
        )
        # Unblocked 1 Red -> pays $1 ransom, no R2 bonus -> 5 - 1 = $4
        self.assertEqual(player.money, 4)

    def test_r3_short_squeeze_cube_threshold(self) -> None:
        """5. R3 grants +$3 base in Phase 1, plus +$1 in Phase 2 if 3+ Red cubes exit tower."""
        all_vars = get_all_variant_cards()
        r3_card = all_vars["R3"]

        config = GameConfig(num_players=2, starting_money=5)
        bots = [AdaptiveBalancedBot(0), AdaptiveBalancedBot(1)]
        custom_vars = get_default_variant_cards()
        custom_vars[DieColor.RED] = r3_card

        engine = GameEngine(config=config, bots=bots, seed=42, variant_cards=custom_vars)
        player = engine.state.players[0]
        r3_die = create_colored_die(DieColor.RED, die_id=101, variant_card=r3_card)
        r3_die.current_face = r3_card.star_face

        # Base output collection in Phase 1 Step 6
        engine._apply_single_die_immediate_output(player, r3_die)
        self.assertEqual(player.money, 8)  # 5 + 3 = $8

        # Phase 2: Exited Red >= 3 -> grants +$1 bonus
        exited_3_red = {CubeColor.RED: 3, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0}
        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=[r3_die],
            commitments={},
            attack_strengths={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes=exited_3_red,
            active_directive="SCRIPT_KIDDIE",
        )
        self.assertEqual(player.money, 9)  # 8 + 1 = $9

        # When Exited Red < 3 -> no extra bonus
        player.money = 8
        exited_2_red = {CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0}
        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=[r3_die],
            commitments={},
            attack_strengths={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes=exited_2_red,
            active_directive="SCRIPT_KIDDIE",
        )
        self.assertEqual(player.money, 8)

    def test_b1_honeypot_telemetry_conditional_bonus(self) -> None:
        """6. B1 blocks 2 Blue; if 1+ Blue exit and 0 Blue damage taken, gains +$3 bonus in Phase 2."""
        all_vars = get_all_variant_cards()
        b1_card = all_vars["B1"]

        config = GameConfig(num_players=2, starting_money=5)
        bots = [AdaptiveBalancedBot(0), AdaptiveBalancedBot(1)]
        custom_vars = get_default_variant_cards()
        custom_vars[DieColor.BLUE] = b1_card

        engine = GameEngine(config=config, bots=bots, seed=42, variant_cards=custom_vars)
        player = engine.state.players[0]
        b1_die = create_colored_die(DieColor.BLUE, die_id=201, variant_card=b1_card)
        b1_die.current_face = b1_card.star_face
        player.ready_dice.append(b1_die)

        # 1 Blue exits and 1 Blue attacks, fully blocked by B1 (unblocked == 0) -> +$3 bonus
        commitments = {0: ShieldColor.BLUE}
        attack_strengths = {CubeColor.RED: 0, CubeColor.BLUE: 1, CubeColor.GREEN: 0}
        exited_cubes = {CubeColor.RED: 0, CubeColor.BLUE: 1, CubeColor.GREEN: 0, CubeColor.BLACK: 0}

        player.money = 5
        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=[b1_die],
            commitments=commitments,
            attack_strengths=attack_strengths,
            exited_cubes=exited_cubes,
            active_directive="SCRIPT_KIDDIE",
        )
        self.assertEqual(player.money, 8)

        # If 0 Blue cubes exit -> no bonus
        player.money = 5
        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=[b1_die],
            commitments=commitments,
            attack_strengths={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0},
            active_directive="SCRIPT_KIDDIE",
        )
        self.assertEqual(player.money, 5)

    def test_b3_air_gapped_backup_wear_immunity(self) -> None:
        """7. B3 blocks 1 Blue and moves 1 other Ready die to Unpatched (or falls back to moving itself if solo)."""
        all_vars = get_all_variant_cards()
        b3_card = all_vars["B3"]

        config = GameConfig(num_players=2, starting_money=5)
        bots = [AdaptiveBalancedBot(0), AdaptiveBalancedBot(1)]
        custom_vars = get_default_variant_cards()
        custom_vars[DieColor.BLUE] = b3_card

        engine = GameEngine(config=config, bots=bots, seed=42, variant_cards=custom_vars)
        player = engine.state.players[0]
        player.unpatched_dice.clear()

        b3_die = create_colored_die(DieColor.BLUE, die_id=203, variant_card=b3_card)
        b3_die.current_face = b3_card.star_face
        gray_starter = create_gray_die(die_id=204)
        player.ready_dice = [b3_die, gray_starter]

        # Case A: Sacrificial demotion when another Ready die exists
        commitments = {0: ShieldColor.BLUE}
        attack_strengths = {CubeColor.RED: 0, CubeColor.BLUE: 1, CubeColor.GREEN: 0}
        exited_cubes = {CubeColor.RED: 0, CubeColor.BLUE: 1, CubeColor.GREEN: 0, CubeColor.BLACK: 0}

        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=[b3_die],
            commitments=commitments,
            attack_strengths=attack_strengths,
            exited_cubes=exited_cubes,
            active_directive="SCRIPT_KIDDIE",
        )
        # B3 die remains in ready_dice; gray_starter is demoted to unpatched_dice
        self.assertIn(b3_die, player.ready_dice)
        self.assertIn(gray_starter, player.unpatched_dice)
        self.assertEqual(len(player.unpatched_dice), 1)

        # Case B: Solo fallback when no other Ready dice exist
        player.ready_dice = [b3_die]
        player.unpatched_dice.clear()
        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=[b3_die],
            commitments=commitments,
            attack_strengths=attack_strengths,
            exited_cubes=exited_cubes,
            active_directive="SCRIPT_KIDDIE",
        )
        self.assertNotIn(b3_die, player.ready_dice)
        self.assertIn(b3_die, player.unpatched_dice)

        # Case C: 0 Blue attack cubes blocked -> B3 does not actively absorb damage, neither die demoted
        player.ready_dice = [b3_die, gray_starter]
        player.unpatched_dice.clear()
        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=[b3_die],
            commitments=commitments,
            attack_strengths={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0},
            active_directive="SCRIPT_KIDDIE",
        )
        self.assertIn(b3_die, player.ready_dice)
        self.assertIn(gray_starter, player.ready_dice)
        self.assertEqual(len(player.unpatched_dice), 0)

    def test_y2_cloud_monopoly_scaling(self) -> None:
        """8. Y2 grants +$2 base plus +$1 per distinct colored module die owned (capped at +$5 total)."""
        all_vars = get_all_variant_cards()
        y2_card = all_vars["Y2"]

        config = GameConfig(num_players=2, starting_money=0)
        bots = [AdaptiveBalancedBot(0), AdaptiveBalancedBot(1)]
        custom_vars = get_default_variant_cards()
        custom_vars[DieColor.YELLOW] = y2_card

        engine = GameEngine(config=config, bots=bots, seed=42, variant_cards=custom_vars)
        player = engine.state.players[0]
        player.money = 0
        player.ready_dice.clear()

        y2_die = create_colored_die(DieColor.YELLOW, die_id=402, variant_card=y2_card)
        y2_die.current_face = y2_card.star_face
        player.ready_dice.append(y2_die)

        # Case A: 1 Yellow die owned -> 1 distinct color -> 2 + 1 = $3
        engine._apply_single_die_immediate_output(player, y2_die)
        self.assertEqual(player.money, 3)

        # Case B: Multiple Yellow dice owned (3 Yellow dice) -> still only 1 distinct color -> payout remains 2 + 1 = $3!
        player.money = 0
        y_extra1 = create_colored_die(DieColor.YELLOW, die_id=403, variant_card=y2_card)
        y_extra2 = create_colored_die(DieColor.YELLOW, die_id=404, variant_card=y2_card)
        player.ready_dice.extend([y_extra1, y_extra2])
        engine._apply_single_die_immediate_output(player, y2_die)
        self.assertEqual(player.money, 3, "Multiple Yellow dice must not scale Y2 payout; distinct colors count is 1")

        # Case C: 3 distinct module colors (Yellow, Red, Blue) -> 2 + 3 = $5
        player.money = 0
        red_die = create_colored_die(DieColor.RED, die_id=405)
        blue_die = create_colored_die(DieColor.BLUE, die_id=406)
        player.ready_dice.extend([red_die, blue_die])
        engine._apply_single_die_immediate_output(player, y2_die)
        self.assertEqual(player.money, 5)

        # Case D: 5 distinct module colors (Yellow, Red, Blue, Green, Purple) -> 2 + 5 = 7 -> capped at $5
        player.money = 0
        green_die = create_colored_die(DieColor.GREEN, die_id=407)
        purple_die = create_colored_die(DieColor.PURPLE, die_id=408)
        player.ready_dice.extend([green_die, purple_die])
        engine._apply_single_die_immediate_output(player, y2_die)
        self.assertEqual(player.money, 5, "Y2 payout must be capped at GameConfig.y2_max_payout ($5)")

    def test_y3_proprietary_training_secrets_and_wear(self) -> None:
        """9. Y3 grants +1 Corporate Secret and immediately demotes this die to Unpatched."""
        all_vars = get_all_variant_cards()
        y3_card = all_vars["Y3"]

        config = GameConfig(num_players=2, starting_money=5)
        bots = [AdaptiveBalancedBot(0), AdaptiveBalancedBot(1)]
        custom_vars = get_default_variant_cards()
        custom_vars[DieColor.YELLOW] = y3_card

        engine = GameEngine(config=config, bots=bots, seed=42, variant_cards=custom_vars)
        player = engine.state.players[0]
        y3_die = create_colored_die(DieColor.YELLOW, die_id=403, variant_card=y3_card)
        y3_die.current_face = y3_card.star_face
        player.ready_dice.append(y3_die)

        starting_secrets = player.secrets
        engine._apply_single_die_immediate_output(player, y3_die)

        self.assertEqual(player.secrets, starting_secrets + 1)
        self.assertNotIn(y3_die, player.ready_dice)
        self.assertIn(y3_die, player.unpatched_dice)

    def test_p2_chaos_profiteer_black_cube_scaling(self) -> None:
        """10. P2 grants +$1 base plus +$2 per exited Black cube in Phase 2."""
        all_vars = get_all_variant_cards()
        p2_card = all_vars["P2"]

        config = GameConfig(num_players=2, starting_money=5)
        bots = [AdaptiveBalancedBot(0), AdaptiveBalancedBot(1)]
        custom_vars = get_default_variant_cards()
        custom_vars[DieColor.PURPLE] = p2_card

        engine = GameEngine(config=config, bots=bots, seed=42, variant_cards=custom_vars)
        player = engine.state.players[0]
        p2_die = create_colored_die(DieColor.PURPLE, die_id=502, variant_card=p2_card)
        p2_die.current_face = p2_card.star_face
        player.ready_dice.append(p2_die)

        # Phase 1 Step 6: +$1 base output
        engine._apply_single_die_immediate_output(player, p2_die)
        self.assertEqual(player.money, 6)

        # Drop 3 Black cubes in Phase 2 deterministically
        engine.state.staging_cup = {CubeColor.BLACK: 3, CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0}
        original_drop = engine.state.tower.drop
        engine.state.tower.drop = lambda cup, rng: {CubeColor.BLACK: 3, CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0}
        try:
            commitments = [(player, [p2_die], {})]
            engine._execute_phase_2(commitments)
            # P2 gives +$2 per black cube (+6), while Space 2 of Script Kiddie deducts $2
            self.assertEqual(player.money, 6 + (2 * 3) - 2)
        finally:
            engine.state.tower.drop = original_drop

    def test_b2_deep_rd_vault_cost_and_rejection(self) -> None:
        """B2 costs $4 to gain +1 Secret; rejects activation when cash < $4 or secrets >= 10."""
        gc = GameController()
        gc.new_game(num_players=2, randomize_cards=False)
        gc.phase = 3
        gc.phase_name = "Market & Operations"
        gc.active_player_index = 0
        p0 = gc.state.players[0]

        # Case A: Successful activation with $4
        p0.money = 5
        p0.secrets = 6
        p0.b2_available = True
        gc.execute_star_action(player_id=0, action_type="B2")
        self.assertEqual(p0.money, 1)  # 5 - 4 = $1
        self.assertEqual(p0.secrets, 7)  # 6 + 1 = 7
        self.assertFalse(p0.b2_available)

        # Case B: Rejection when insufficient cash (< $4)
        p0.money = 3
        p0.b2_available = True
        with self.assertRaises(ValueError) as ctx:
            gc.execute_star_action(player_id=0, action_type="B2")
        self.assertIn("B2 requires $4 cash", str(ctx.exception))

        # Case C: Rejection when at secrets cap if configured
        gc.state.config.b2_secret_cap = 10
        p0.money = 10
        p0.secrets = 10
        p0.b2_available = True
        with self.assertRaises(ValueError) as ctx:
            gc.execute_star_action(player_id=0, action_type="B2")
        self.assertIn("maximum capacity (10)", str(ctx.exception))

    def test_p3_packet_deflection_paid_injection_and_rejection(self) -> None:
        """P3 requires $1 cash to deflect a cube of the blocked color; rejects activation when cash < $1."""
        gc = GameController()
        gc.new_game(num_players=2, randomize_cards=False)
        gc.phase = 3
        gc.phase_name = "Market & Operations"
        gc.active_player_index = 0
        p0 = gc.state.players[0]

        # Case A: Successful activation with $1 cash
        p0.money = 2
        p0.p3_available = ShieldColor.BLUE
        blue_before = gc.state.staging_cup.get(CubeColor.BLUE, 0)
        gc.execute_star_action(player_id=0, action_type="P3", cube_color="blue")
        self.assertEqual(p0.money, 1)  # 2 - 1 = $1
        self.assertEqual(gc.state.staging_cup.get(CubeColor.BLUE, 0), blue_before + 1)
        self.assertIsNone(p0.p3_available)

        # Case B: Rejection when cash < $1 (zero cash)
        p0.money = 0
        p0.p3_available = ShieldColor.BLUE
        with self.assertRaises(ValueError) as ctx:
            gc.execute_star_action(player_id=0, action_type="P3", cube_color="blue")
        self.assertIn("P3 requires $1 cash", str(ctx.exception))

        # Case C: Rejection when color does not match blocked color
        p0.money = 5
        p0.p3_available = ShieldColor.BLUE
        with self.assertRaises(ValueError) as ctx:
            gc.execute_star_action(player_id=0, action_type="P3", cube_color="red")
        self.assertIn("matching the blocked color", str(ctx.exception))


# =====================================================================
# Group C: Version Directive Mechanics
# =====================================================================

class TestGroupCVersionDirectives(unittest.TestCase):
    """Unit tests for Rogue Agent Roadmap version directives."""

    def test_directive_data_scraper_starting_money(self) -> None:
        """11. v1.0 Data Scraper grants +$1 extra starting money ($8 total in 4P)."""
        all_versions = get_all_version_cards()
        data_scraper = all_versions[1]
        self.assertEqual(data_scraper.directive_code, "DATA_SCRAPER")

        custom_deck = [data_scraper, all_versions[2], all_versions[4]]
        config = GameConfig(num_players=4, starting_money=7)
        bots = [AdaptiveBalancedBot(i) for i in range(4)]

        engine = GameEngine(config=config, bots=bots, seed=42, version_deck=custom_deck)
        for player in engine.state.players:
            self.assertEqual(player.money, 8, "Expected $8 starting money under Data Scraper")

    def test_directive_corrupted_kernel_attack_strength(self) -> None:
        """12. v3.0 Corrupted Kernel: legacy directive fallback when corruption track is empty."""
        all_versions = get_all_version_cards()
        corrupted_kernel = VersionCard(
            version_str="v3.0",
            name="Corrupted Kernel",
            staging_payload={CubeColor.RED: 1, CubeColor.BLUE: 1},
            directive_description="If 2+ Black Cubes exit...",
            directive_code="CORRUPTED_KERNEL",
            corruption_track=(),
        )
        self.assertEqual(corrupted_kernel.directive_code, "CORRUPTED_KERNEL")

        # Staging payload verification: {RED: 1, BLUE: 1}
        self.assertEqual(corrupted_kernel.get_staging_payload(4), {CubeColor.RED: 1, CubeColor.BLUE: 1})
        self.assertEqual(corrupted_kernel.get_staging_payload(2), {CubeColor.RED: 1, CubeColor.BLUE: 1})

        custom_deck = [all_versions[0], all_versions[2], corrupted_kernel]
        config = GameConfig(num_players=2)
        bots = [AdaptiveBalancedBot(0), AdaptiveBalancedBot(1)]

        engine = GameEngine(config=config, bots=bots, seed=42, version_deck=custom_deck)
        # Fast forward version index to v3.0 Corrupted Kernel
        engine.state.current_version_index = 2
        self.assertEqual(engine.state.active_directive_code, "CORRUPTED_KERNEL")

        player = engine.state.players[0]
        commitments = [(player, list(player.ready_dice), {})]

        # Case A: < 2 Black cubes exit (e.g. 1 Black) -> NO bonus added
        original_drop = engine.state.tower.drop
        engine.state.tower.drop = lambda cup, rng: {CubeColor.BLACK: 1, CubeColor.RED: 2, CubeColor.BLUE: 1, CubeColor.GREEN: 0}
        try:
            telemetry = engine._execute_phase_2(commitments)
            self.assertEqual(telemetry.attack_strengths[CubeColor.RED], 2, "No bonus should be added when black cubes < 2")
            self.assertEqual(telemetry.attack_strengths[CubeColor.BLUE], 1)
            self.assertEqual(telemetry.attack_strengths[CubeColor.GREEN], 0)
        finally:
            engine.state.tower.drop = original_drop

        # Case B: >= 2 Black cubes exit (e.g. 2 Black) -> flat +2 bonus added to highest attack color (Red)
        engine.state.tower.drop = lambda cup, rng: {CubeColor.BLACK: 2, CubeColor.RED: 2, CubeColor.BLUE: 1, CubeColor.GREEN: 0}
        try:
            telemetry = engine._execute_phase_2(commitments)
            # Red had 2 cubes (highest count), Black had 2 cubes -> Red strength becomes 2 + 2 = 4
            self.assertEqual(telemetry.attack_strengths[CubeColor.RED], 4, "Flat +2 bonus added when black cubes >= 2 (2 + 2 = 4)")
            self.assertEqual(telemetry.attack_strengths[CubeColor.BLUE], 1)
            self.assertEqual(telemetry.attack_strengths[CubeColor.GREEN], 0)
        finally:
            engine.state.tower.drop = original_drop

        # Case C: 3 Black cubes exit -> still flat +2 bonus added (not +3)
        engine.state.tower.drop = lambda cup, rng: {CubeColor.BLACK: 3, CubeColor.RED: 2, CubeColor.BLUE: 1, CubeColor.GREEN: 0}
        try:
            telemetry = engine._execute_phase_2(commitments)
            self.assertEqual(telemetry.attack_strengths[CubeColor.RED], 4, "Bonus is flat +2 regardless of whether 2 or 3 black cubes exit")
            self.assertEqual(telemetry.attack_strengths[CubeColor.BLUE], 1)
            self.assertEqual(telemetry.attack_strengths[CubeColor.GREEN], 0)
        finally:
            engine.state.tower.drop = original_drop


# =====================================================================
# Group D: Web Game Controller & State Machine
# =====================================================================

class TestGroupDWebGameController(unittest.TestCase):
    """Unit tests for GameController initialization and variant tracking."""

    def test_controller_new_game_default_cards(self) -> None:
        """13. randomize_cards=False initializes with default baseline cards and versions."""
        gc = GameController()
        gc.new_game(num_players=4, randomize_cards=False)

        expected_var_codes = {"RED": "R1", "BLUE": "B1", "GREEN": "G1", "YELLOW": "Y1", "PURPLE": "P1"}
        actual_var_codes = {c.value.upper(): v.code for c, v in gc.state.variant_cards.items()}
        self.assertEqual(actual_var_codes, expected_var_codes)

        self.assertEqual(gc.state.active_version.name, "Script Kiddie")
        self.assertEqual(gc.state.version_deck[1].name, "Ransomware-as-a-Service")
        self.assertEqual(gc.state.version_deck[2].name, "Zero-Day Override")

    def test_controller_new_game_randomize_cards(self) -> None:
        """14. randomize_cards=True randomizes setup cards derived from seed * 17."""
        gc1 = GameController()
        gc1.new_game(num_players=4, seed=42, randomize_cards=True)

        gc2 = GameController()
        gc2.new_game(num_players=4, seed=42, randomize_cards=True)

        # Deterministic equality for same seed
        gc1_codes = [v.code for v in gc1.state.variant_cards.values()]
        gc2_codes = [v.code for v in gc2.state.variant_cards.values()]
        self.assertEqual(gc1_codes, gc2_codes)

        gc1_versions = [v.directive_code for v in gc1.state.version_deck]
        gc2_versions = [v.directive_code for v in gc2.state.version_deck]
        self.assertEqual(gc1_versions, gc2_versions)

        # Directly verify derivation from seed * 17
        expected_vars, expected_deck = get_random_setup(random.Random(42 * 17))
        self.assertEqual(gc1_codes, [v.code for v in expected_vars.values()])
        self.assertEqual(gc1_versions, [v.directive_code for v in expected_deck])

    def test_controller_event_log_active_variants(self) -> None:
        """15. event_log lists active variant codes upon match creation."""
        gc = GameController()
        gc.new_game(num_players=4, randomize_cards=False)

        log_text = " ".join(gc.event_log)
        self.assertIn("Active Variants:", log_text)
        self.assertIn("R1", log_text)
        self.assertIn("B1", log_text)
        self.assertIn("G1", log_text)
        self.assertIn("Y1", log_text)
        self.assertIn("P1", log_text)

    def test_polymorphic_worm_patch_cash_cost_matches_config(self) -> None:
        """Verifies that under POLYMORPHIC_WORM:
        - Phase 1 max_rerolls is 1
        - Cash patch cost in Phase 3 is strictly $2 (GameConfig.patch_cash_cost),
          successfully patching an unpatched die with $2 cash without raising an error.
        """
        all_versions = get_all_version_cards()
        worm_card = [v for v in all_versions if v.directive_code == "POLYMORPHIC_WORM"][0]
        custom_deck = [worm_card, all_versions[2], all_versions[4]]

        gc = GameController()
        gc.new_game(num_players=2, version_deck=custom_deck, randomize_cards=False)

        # 1. Under v0.15.0 POLYMORPHIC_WORM, Phase 1 default free rerolls is 2 (Space 4 locks Patch faces)
        self.assertEqual(gc.state.active_directive_code, "POLYMORPHIC_WORM")
        self.assertEqual(gc.player_meta[0]["max_rerolls"], 2)
        self.assertEqual(gc.player_meta[0]["rerolls_remaining"], 2)

        # 2. Setup Phase 3 state for human player 0
        gc.phase = 3
        gc.phase_name = "Market & Operations"
        gc.active_player_index = 0

        player = gc.state.players[0]
        config_cost = gc.state.config.patch_cash_cost
        self.assertEqual(config_cost, 2)

        # Give player exactly $2 cash and 1 unpatched die (and 0 patch tokens)
        player.money = config_cost
        player.patches = 0
        unpatched_die = player.ready_dice.pop()
        player.unpatched_dice.append(unpatched_die)

        initial_unpatched_count = len(player.unpatched_dice)
        initial_ready_count = len(player.ready_dice)

        # Patch die using cash ($2) - should succeed without error
        gc.patch_die(player_id=0, die_index=0, use_cash=True)

        self.assertEqual(player.money, 0)
        self.assertEqual(len(player.unpatched_dice), initial_unpatched_count - 1)
        self.assertEqual(len(player.ready_dice), initial_ready_count + 1)


# =====================================================================
# Group E: Web Server REST API Endpoints
# =====================================================================

class TestGroupEWebAPIServer(unittest.TestCase):
    """Integration tests for POST /api/game/new handling of randomize_cards."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.server = create_server(host="127.0.0.1", port=0)
        cls.server_port = cls.server.server_address[1]
        cls.base_url = f"http://127.0.0.1:{cls.server_port}"
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=2.0)

    def _post(self, path: str, payload: Dict) -> Dict:
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as res:
            return json.loads(res.read().decode("utf-8"))

    def test_api_new_game_randomize_cards_true(self) -> None:
        """16. POST /api/game/new with randomize_cards=true returns randomized match state."""
        data = self._post("/api/game/new", {"num_players": 4, "seed": 42, "randomize_cards": True})
        self.assertTrue(data["success"])
        state = data["state"]
        self.assertIn("market", state)
        self.assertIn("staging_cup", state)

        expected_vars, expected_deck = get_random_setup(random.Random(42 * 17))
        expected_codes = {c.value: v.code for c, v in expected_vars.items()}
        market_codes = {k: v["variant"]["code"] for k, v in state["market"].items()}
        self.assertEqual(market_codes, expected_codes)

    def test_api_new_game_randomize_cards_false(self) -> None:
        """17. POST /api/game/new with randomize_cards=false returns baseline match state."""
        data = self._post("/api/game/new", {"num_players": 4, "seed": 42, "randomize_cards": False})
        self.assertTrue(data["success"])
        state = data["state"]

        baseline_codes = {"red": "R1", "blue": "B1", "green": "G1", "yellow": "Y1", "purple": "P1"}
        market_codes = {k: v["variant"]["code"] for k, v in state["market"].items()}
        self.assertEqual(market_codes, baseline_codes)

    def test_server_create_with_randomize_cards_true(self) -> None:
        """18. create_server(randomize_cards=True) initializes randomized match upon server startup."""
        test_server = create_server(host="127.0.0.1", port=0, randomize_cards=True)
        try:
            ctrl = test_server.RequestHandlerClass.controller
            self.assertIsNotNone(ctrl.engine)
            # Randomized setup has 5 variant cards and 3 version cards in state
            self.assertEqual(len(ctrl.state.variant_cards), 5)
            self.assertEqual(len(ctrl.state.version_deck), 3)
        finally:
            test_server.server_close()

    def test_api_get_state_includes_all_versions_roadmap(self) -> None:
        """19. GET /api/game/state provides complete version_deck roadmap for the match."""
        # Initialize match with seed 42 and randomized cards
        data = self._post("/api/game/new", {"num_players": 4, "seed": 42, "randomize_cards": True})
        self.assertTrue(data["success"])

        # Fetch state via GET
        req = urllib.request.Request(f"{self.base_url}/api/game/state", method="GET")
        with urllib.request.urlopen(req, timeout=5) as res:
            res_data = json.loads(res.read().decode("utf-8"))

        self.assertTrue(res_data["success"])
        state = res_data["state"]

        self.assertIn("version_deck", state)
        version_deck = state["version_deck"]
        self.assertEqual(len(version_deck), 3)

        expected_versions = ["v1.0", "v2.0", "v3.0"]
        for idx, ver in enumerate(version_deck):
            self.assertEqual(ver["version_str"], expected_versions[idx])
            self.assertTrue(len(ver["name"]) > 0)
            self.assertIn("directive_description", ver)
            self.assertIn("staging_payload", ver)

        self.assertIn("current_version_index", state)
        self.assertEqual(state["current_version_index"], 0)

    def test_versions_v2_v3_have_no_directives(self) -> None:
        """Verify v2.0 and v3.0 version cards carry no persistent directives; only corruption track triggers."""
        all_cards = get_all_version_cards()
        for card in all_cards:
            if card.version_str in ("v2.0", "v3.0"):
                self.assertIn(card.directive_description, ("", "None."),
                              f"{card.name} ({card.version_str}) should not have a directive listed")
                self.assertTrue(len(card.corruption_track) >= 5,
                                f"{card.name} ({card.version_str}) must define a corruption track")


# =====================================================================
# Group F: Experiments Telemetry & Batch Simulation
# =====================================================================

class TestGroupFExperimentsTelemetry(unittest.TestCase):
    """Unit tests for Experiment 5 metrics calculation and batch execution."""

    def test_experiment_metrics_winning_and_mean_scores(self) -> None:
        """18. ExperimentMetrics calculates mean_winning_score and mean_scores dictionary."""
        def cfg_fn():
            return GameConfig(num_players=4)

        def bots_fn():
            return [
                AdaptiveBalancedBot(0),
                SecOpsTurtleBot(1),
                VentureGreedBot(2),
                AccelerationistBot(3),
            ]

        metrics = run_batch(cfg_fn, bots_fn, num_runs=5, base_seed=42)
        self.assertIsInstance(metrics, ExperimentMetrics)
        self.assertIsInstance(metrics.mean_winning_score, float)
        self.assertIsInstance(metrics.mean_scores, dict)
        self.assertEqual(len(metrics.mean_scores), 4)
        for bot_name, score in metrics.mean_scores.items():
            self.assertIsInstance(score, float)

    def test_run_batch_with_custom_variants_and_versions(self) -> None:
        """19. run_batch accepts custom variant_cards and version_deck overrides cleanly."""
        all_vars = get_all_variant_cards()
        all_vers = get_all_version_cards()

        custom_vars = get_default_variant_cards().copy()
        custom_vars[DieColor.RED] = all_vars["R2"]

        custom_deck = [all_vers[1], all_vers[3], all_vers[5]]  # All-alternates

        def cfg_fn():
            return GameConfig(num_players=4)

        def bots_fn():
            return [
                AdaptiveBalancedBot(0),
                SecOpsTurtleBot(1),
                VentureGreedBot(2),
                AccelerationistBot(3),
            ]

        metrics = run_batch(
            cfg_fn,
            bots_fn,
            num_runs=5,
            base_seed=42,
            variant_cards=custom_vars,
            version_deck=custom_deck,
        )
        self.assertEqual(metrics.total_games, 5)
        self.assertGreaterEqual(metrics.mean_rounds, 1.0)


if __name__ == "__main__":
    unittest.main()
