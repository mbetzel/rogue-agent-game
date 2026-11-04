"""Unit and Integration Tests for Phase 31: Proprietary Specialist (Purple) Dice Overhaul & Personal Reserve (v0.24.0 Baseline)."""

from __future__ import annotations

import random
import unittest
from typing import Dict, List, Optional, Tuple

from sim.bots.adaptive_balanced import AdaptiveBalancedBot
from sim.bots.base import BaseBot, Phase3ActionPlan
from sim.bots.secops_turtle import SecOpsTurtleBot
from sim.config import CubeColor, DieColor, GameConfig, ShieldColor
from sim.engine.core import GameEngine
from sim.engine.phase1_boot import (
    check_operator_contingent_staffing,
    detect_hash_matches_with_cipher,
    execute_phase_1,
    resolve_prodigy_purple_star_override,
)
from sim.engine.phase2_threat import execute_phase_2, return_player_colored_dice_step2a
from sim.engine.phase3_ops import (
    collect_player_production_income,
    execute_phase_3,
    resolve_phreaker_jumper_diagnostics,
    resolve_spook_burn_notice,
)
from sim.engine.state import PlayerState, ProductionRole
from sim.entities import (
    ArchetypeCard,
    ArchetypeCode,
    CorruptionSpace,
    Die,
    Face,
    create_colored_die,
    create_gray_die,
    create_white_die,
    get_archetype_by_code,
    get_default_variant_cards,
)
from web.controller.core import GameController
from web.schemas import GameStateSerializer


class TestV240Rules(unittest.TestCase):
    """Exhaustive 25-point unit test matrix for v0.24.0 Purple Dice Overhaul & Personal Reserve."""

    # =========================================================================
    # Category 1: Personal Reserve Insulation & Procurement (5 tests)
    # =========================================================================

    def test_personal_purple_reserve_initializes_to_two(self) -> None:
        """INV-PURPLE-01: Each player starts the match with personal_purple_reserve == 1 (v0.30.0 Baseline)."""
        engine = GameEngine(config=GameConfig(num_players=4), seed=42)
        self.assertEqual(len(engine.state.players), 4)
        for p in engine.state.players:
            self.assertEqual(p.personal_purple_reserve, 1, "Each player must initialize with 1 Purple die in reserve")

    def test_procuring_purple_die_deducts_four_dollars_and_one_reserve(self) -> None:
        """INV-PURPLE-03: Purchasing Purple costs $4, decrements reserve by 1, and delivers die to ready."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.money = 7
        p0.personal_purple_reserve = 1
        initial_ready_count = len(p0.ready_for_release_dice)

        class BuyPurpleBot(BaseBot):
            def take_phase3_actions(self, player_state, game_state, rng):
                plan = Phase3ActionPlan()
                plan.market_purchases.append(DieColor.PURPLE)
                return plan

        p0.bot = BuyPurpleBot(0)
        execute_phase_3(engine)

        # Operator reserve cost is calibrated to $5 (7 - 5 = 2)
        self.assertEqual(p0.money, 2, "Procuring Purple die must cost operative reserve cost (7 - 5 = 2)")
        self.assertEqual(p0.personal_purple_reserve, 0, "Reserve must decrement from 1 to 0")
        self.assertEqual(len(p0.ready_for_release_dice), initial_ready_count + 1)
        purple_dice = [d for d in p0.ready_for_release_dice if d.color == DieColor.PURPLE]
        self.assertEqual(len(purple_dice), 2, "Exactly 2 Purple dice must be in ready pool (1 starter + 1 purchased)")

    def test_cannot_procure_purple_die_when_reserve_empty(self) -> None:
        """INV-PURPLE-03: Attempting to procure a Purple die with empty reserve fails."""
        gc = GameController()
        gc.new_game(num_players=2, seed=42)
        gc.phase = 3
        gc.subphase = "operations_turn"
        gc.active_player_index = 0
        p0 = gc.state.players[0]
        p0.personal_purple_reserve = 0
        p0.money = 10

        with self.assertRaises(ValueError):
            gc.buy_die(player_id=0, color_str="purple")

        self.assertEqual(p0.money, 10, "Money must not be deducted if purchase is rejected")
        self.assertEqual(p0.personal_purple_reserve, 0)

    def test_procuring_purple_die_respects_per_turn_purchase_limit(self) -> None:
        """INV-PURPLE-03: Purple reserve purchases count towards max_market_purchases_per_turn (2)."""
        gc = GameController()
        gc.new_game(num_players=2, seed=42)
        gc.phase = 3
        gc.subphase = "operations_turn"
        gc.active_player_index = 0
        p0 = gc.state.players[0]
        p0.money = 20
        p0.personal_purple_reserve = 2

        # 1st purchase: 1 Red die from central market
        gc.buy_die(player_id=0, color_str="red")
        self.assertEqual(gc.player_meta[0]["purchases_this_turn"], 1)

        # 2nd purchase: 1 Purple die from personal reserve
        gc.buy_die(player_id=0, color_str="purple")
        self.assertEqual(gc.player_meta[0]["purchases_this_turn"], 2)
        self.assertEqual(p0.personal_purple_reserve, 1)

        # 3rd purchase: must be rejected by per-turn limit
        with self.assertRaises(ValueError):
            gc.buy_die(player_id=0, color_str="purple")

    def test_central_market_excludes_purple_die_supply(self) -> None:
        """INV-PURPLE-02: Central Market excludes Purple and only stocks Red, Blue, Green, Yellow."""
        engine = GameEngine(config=GameConfig(num_players=3), seed=42)
        self.assertNotIn(DieColor.PURPLE, engine.state.market, "DieColor.PURPLE must not exist in central market")
        for col in [DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW]:
            self.assertIn(col, engine.state.market)
            self.assertEqual(engine.state.market[col], 3 * 2)  # 2 per player

    # =========================================================================
    # Category 2: Standardized Face Configuration & Normal Play (4 tests)
    # =========================================================================

    def test_purple_die_faces_geometry_and_star_code(self) -> None:
        """INV-PURPLE-04: Standardized Purple face geometry and PURPLE_STAR code."""
        purple = create_colored_die(DieColor.PURPLE, 1)
        self.assertEqual(purple.cost, 4)
        self.assertEqual(len(purple.faces), 6)

        # Faces 1 & 2: Block 1 Any
        self.assertEqual(purple.faces[0].name, "Block 1 Any")
        self.assertEqual(purple.faces[0].block_amount, 1)
        self.assertEqual(purple.faces[0].shield_color, ShieldColor.ANY)

        self.assertEqual(purple.faces[1].name, "Block 1 Any")
        self.assertEqual(purple.faces[1].block_amount, 1)
        self.assertEqual(purple.faces[1].shield_color, ShieldColor.ANY)

        # Face 3: +$2
        self.assertEqual(purple.faces[2].name, "+$2")
        self.assertEqual(purple.faces[2].money, 2)

        # Face 4: +$1 & +1 🔧
        self.assertEqual(purple.faces[3].name, "+$1 & +1 🔧")
        self.assertEqual(purple.faces[3].money, 1)
        self.assertEqual(purple.faces[3].patches, 1)

        # Face 5: Glitch (Locked)
        self.assertTrue(purple.faces[4].is_glitch)

        # Face 6: Purple ★
        self.assertTrue(purple.faces[5].is_star)
        self.assertEqual(purple.faces[5].star_code, "PURPLE_STAR")
        self.assertEqual(purple.variant_code, "PURPLE_STAR")

    def test_purple_die_glitch_locks_immediately_in_phase_1(self) -> None:
        """INV-PURPLE-04 / INV-LOCK-01: Purple die rolling Face 5 (Glitch) locks immediately."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        purple = create_colored_die(DieColor.PURPLE, 1)
        glitch_face = purple.faces[4]
        self.assertTrue(glitch_face.is_glitch)
        purple.faces = [glitch_face] * 6  # Guarantee glitch
        p0.ready_for_release_dice = [purple]

        class PassiveBot(BaseBot):
            def choose_yahtzee_rerolls(self, *args, **kwargs):
                return []

        p0.bot = PassiveBot(0)
        execute_phase_1(engine)

        self.assertIn(purple, p0.glitched_dice, "Glitch face must send permanent Purple die to glitched_dice")

    def test_purple_die_wild_shields_absorb_red_blue_or_green(self) -> None:
        """INV-PURPLE-04: Block 1 Any shield can be assigned to Red, Blue, or Green threat."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.secrets = 8
        p0.money = 5
        purple = create_colored_die(DieColor.PURPLE, 1)
        shield_face = purple.faces[0]  # Block 1 Any
        purple.faces = [shield_face] * 6
        p0.ready_for_release_dice = [purple]

        class RedShieldBot(BaseBot):
            def commit_shields(self, *args, **kwargs):
                return {0: ShieldColor.RED}

        p0.bot = RedShieldBot(0)
        commitments = execute_phase_1(engine)

        self.assertEqual(purple.production_role, ProductionRole.RED_SHIELD)

        # Set Red threat of 1 cube in Phase 2
        engine.state.staging_cup = {CubeColor.RED: 1, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0}
        engine.state.tower.load_stuck({CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0})
        # Force 100% exit
        engine.config.tower_flat_exit_prob = 1.0

        execute_phase_2(engine, commitments)
        self.assertEqual(p0.secrets, 8, "Block 1 Any assigned to Red must block 1 Red attack cube")

    def test_purple_die_face3_and_face4_income_harvesting(self) -> None:
        """INV-PURPLE-04: Faces 3 (+$2) and 4 (+$1 & +1 🔧) harvest resources accurately in Phase 3A."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.money = 0
        p0.patches = 0

        p_die1 = create_colored_die(DieColor.PURPLE, 1)
        p_die1.current_face = p_die1.faces[2]  # +$2
        p_die1.production_role = ProductionRole.INCOME

        p_die2 = create_colored_die(DieColor.PURPLE, 2)
        p_die2.current_face = p_die2.faces[3]  # +$1 & +1 🔧
        p_die2.production_role = ProductionRole.INCOME

        p0.in_production_dice = [p_die1, p_die2]
        collect_player_production_income(engine, p0, Phase3ActionPlan())

        self.assertEqual(p0.money, 3, "Face 3 (+$2) + Face 4 (+$1) = +$3 cash")
        self.assertEqual(p0.patches, 1, "Face 4 must award exact +1 🔧")

    # =========================================================================
    # Category 3: Archetype Face 6 Signature Protocols (6 tests - 1 per archetype)
    # =========================================================================

    def test_acoustic_resonance_sensor_awards_dollar_per_unique_exit_color(self) -> None:
        """INV-PURPLE-05: The Acoustic gains +$1 per unique cube color in Exit Tray this round (max +$4)."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.archetype = get_archetype_by_code(ArchetypeCode.ACOUSTIC)
        p0.money = 0

        purple = create_colored_die(DieColor.PURPLE, 1)
        purple.current_face = purple.faces[5]  # Purple ★
        purple.production_role = ProductionRole.INCOME
        p0.in_production_dice = [purple]

        # 3 unique colors in Exit Tray: Red, Blue, Black
        engine.state.last_exited_cubes = {
            CubeColor.RED: 2,
            CubeColor.BLUE: 1,
            CubeColor.GREEN: 0,
            CubeColor.BLACK: 1,
        }
        engine.state.tower.last_exited_cubes = dict(engine.state.last_exited_cubes)

        collect_player_production_income(engine, p0, Phase3ActionPlan())
        self.assertEqual(p0.money, 3, "Acoustic must receive +$3 for 3 unique cube colors in Exit Tray")

    def test_phreaker_jumper_diagnostics_harvests_ud_die_without_moving_it(self) -> None:
        """INV-PURPLE-05: The Phreaker rolls 1 die in Under Development, harvests resources, leaves die in place."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.archetype = get_archetype_by_code(ArchetypeCode.PHREAKER)
        p0.money = 0
        p0.patches = 0

        gray = create_gray_die(101)
        p0.glitched_dice = [gray]

        # Force Face 3 (+ $1)
        forced_face = gray.faces[2]
        self.assertEqual(forced_face.money, 1)

        face = resolve_phreaker_jumper_diagnostics(engine, p0, die_id=101, forced_face=forced_face)
        self.assertEqual(face, forced_face)
        self.assertEqual(p0.money, 1, "Phreaker must harvest +$1 from rolled face")
        self.assertEqual(len(p0.glitched_dice), 1, "Die must NOT be moved or repaired out of glitched_dice")
        self.assertIn(gray, p0.glitched_dice)

    def test_prodigy_arbitrary_code_execution_overrides_other_rolled_die(self) -> None:
        """INV-PURPLE-05: The Prodigy turns any 1 other rolled die to any legal non-Star face."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.archetype = get_archetype_by_code(ArchetypeCode.PRODIGY)

        purple = create_colored_die(DieColor.PURPLE, 1)
        purple.current_face = purple.faces[5]  # Purple ★

        gray = create_gray_die(2)
        gray.current_face = Face(name="Glitch (Locked)", is_glitch=True)
        gray.is_locked = True

        active_dice = [purple, gray]

        target_face = Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)
        success = resolve_prodigy_purple_star_override(
            player=p0,
            active_dice=active_dice,
            rng=engine.rng,
            target_idx=1,
            target_face=target_face,
        )

        self.assertTrue(success)
        self.assertEqual(gray.current_face, target_face)
        self.assertFalse(gray.is_locked, "Overridden die must be unlocked")

    def test_spook_burn_notice_awards_cash_and_optional_secret_burn(self) -> None:
        """INV-PURPLE-05: The Spook gains +$2 cash and may permanently burn 1 colored die for +1 Secret."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.archetype = get_archetype_by_code(ArchetypeCode.SPOOK)
        p0.money = 0
        p0.secrets = 8

        purple = create_colored_die(DieColor.PURPLE, 1)
        purple.current_face = purple.faces[5]  # Purple ★
        purple.production_role = ProductionRole.INCOME
        p0.in_production_dice = [purple]

        red = create_colored_die(DieColor.RED, 2)
        p0.glitched_dice = [red]

        collect_player_production_income(engine, p0, Phase3ActionPlan())
        self.assertEqual(p0.money, 2, "Spook must gain baseline +$2 cash from Purple Star")

        # Execute optional Burn Notice on Red die
        success = resolve_spook_burn_notice(engine, p0, die_id=2)
        self.assertTrue(success)
        self.assertEqual(p0.secrets, 9, "Burning 1 colored die must grant +1 Corporate Secret")
        self.assertNotIn(red, p0.glitched_dice)
        self.assertEqual(engine.state.market[DieColor.RED], (2 * 2) + 1, "Burned colored market die returns to stock")

    def test_cipher_algorithmic_parity_wildcard_triplet_and_income(self) -> None:
        """INV-PURPLE-05: The Cipher uses Purple Star as a wildcard for pairs and gains +$2 Phase 3 Income."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.archetype = get_archetype_by_code(ArchetypeCode.CIPHER)
        p0.money = 0
        p0.secrets = 8

        # Create two dice showing identical faces (a pair)
        d1 = create_gray_die(1)
        d1.current_face = d1.faces[2]  # +$1
        d2 = create_gray_die(2)
        d2.current_face = d2.faces[3]  # +$1

        purple = create_colored_die(DieColor.PURPLE, 3)
        purple.current_face = purple.faces[5]  # Purple ★

        active_dice = [d1, d2, purple]
        secrets_gained = detect_hash_matches_with_cipher(active_dice, is_cipher=True)
        self.assertEqual(secrets_gained, 1, "Cipher Purple Star must complete pair into 3-of-a-kind triplet")

        # Phase 3 Income collection
        purple.production_role = ProductionRole.INCOME
        p0.in_production_dice = [purple]
        collect_player_production_income(engine, p0, Phase3ActionPlan())
        self.assertEqual(p0.money, 2, "Cipher must gain +$2 income from Purple Star in production")

    def test_operator_contingent_staffing_rolls_free_white_contractor(self) -> None:
        """INV-PURPLE-05: The Operator rolls a free White Contractor into pool when Purple Star is rolled."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.archetype = get_archetype_by_code(ArchetypeCode.OPERATOR)
        supply_before = engine.state.contractor_supply

        purple = create_colored_die(DieColor.PURPLE, 1)
        purple.current_face = purple.faces[5]  # Purple ★
        active_dice = [purple]

        c_die = check_operator_contingent_staffing(engine, p0, active_dice)
        self.assertIsNotNone(c_die, "Contingent Staffing must return a new contractor die")
        self.assertEqual(engine.state.contractor_supply, supply_before - 1)
        self.assertEqual(len(active_dice), 2)
        self.assertIn(c_die, p0.contractor_dice)

    # =========================================================================
    # Category 4: Bot Heuristics & Decision Trees (5 tests)
    # =========================================================================

    def test_bot_procures_purple_die_when_capital_available(self) -> None:
        """BaseBot.choose_purple_reserve_purchase evaluates capital and pool size."""
        bot = BaseBot(0)
        p0 = PlayerState(0, bot, money=8, secrets=8, patches=2, personal_purple_reserve=2)
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)

        # Money >= 8: should buy
        self.assertTrue(bot.choose_purple_reserve_purchase(p0, engine.state, random.Random(42)))

        # Money < 4: cannot buy
        p0.money = 3
        self.assertFalse(bot.choose_purple_reserve_purchase(p0, engine.state, random.Random(42)))

        # Empty reserve: cannot buy
        p0.money = 10
        p0.personal_purple_reserve = 0
        self.assertFalse(bot.choose_purple_reserve_purchase(p0, engine.state, random.Random(42)))

    def test_bot_spook_burn_notice_prioritizes_glitched_colored_dice(self) -> None:
        """BaseBot.choose_spook_burn_notice prioritizes glitched colored dice."""
        bot = BaseBot(0)
        p0 = PlayerState(0, bot, money=5, secrets=6, patches=2)
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)

        red_glitched = create_colored_die(DieColor.RED, 10)
        p0.glitched_dice = [red_glitched]

        chosen_id = bot.choose_spook_burn_notice(p0, engine.state, random.Random(42))
        self.assertEqual(chosen_id, 10, "Bot must target glitched colored die for Burn Notice")

    def test_bot_phreaker_diagnostics_targets_highest_yield_ud_die(self) -> None:
        """BaseBot.choose_phreaker_jumper_diagnostics targets highest yield die (Green/Yellow)."""
        bot = BaseBot(0)
        p0 = PlayerState(0, bot, money=5, secrets=6, patches=2)
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)

        gray = create_gray_die(1)
        green = create_colored_die(DieColor.GREEN, 2)
        p0.glitched_dice = [gray, green]

        target_id = bot.choose_phreaker_jumper_diagnostics(p0, engine.state, random.Random(42))
        self.assertEqual(target_id, 2, "Bot must target Green die (id 2) over Gray die for diagnostics")

    def test_bot_prodigy_ace_clears_active_glitches(self) -> None:
        """BaseBot.choose_prodigy_purple_star_override targets active Glitches to override."""
        bot = BaseBot(0)
        p0 = PlayerState(0, bot, money=5, secrets=6, patches=2)

        purple = create_colored_die(DieColor.PURPLE, 1)
        purple.current_face = purple.faces[5]  # Purple ★

        gray = create_gray_die(2)
        gray.current_face = Face("Glitch (Locked)", is_glitch=True)

        active_dice = [purple, gray]
        choice = bot.choose_prodigy_purple_star_override(p0, active_dice, random.Random(42))
        self.assertIsNotNone(choice)
        idx, target_face = choice
        self.assertEqual(idx, 1)
        self.assertFalse(target_face.is_glitch)
        self.assertFalse(target_face.is_star)

    def test_secops_bot_prioritizes_purple_for_wild_defense(self) -> None:
        """SecOpsTurtleBot prioritizes Purple reserve and restricts Spook burn unless at 12+ Secrets."""
        bot = SecOpsTurtleBot(0)
        p0 = PlayerState(0, bot, money=4, secrets=6, patches=2, personal_purple_reserve=1)
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)

        # High priority on Purple reserve
        self.assertTrue(bot.choose_purple_reserve_purchase(p0, engine.state, random.Random(42)))

        # Refuses Spook burn when secrets < 12
        p0.glitched_dice = [create_colored_die(DieColor.RED, 1)]
        self.assertIsNone(bot.choose_spook_burn_notice(p0, engine.state, random.Random(42)))

        # Allows Spook burn when secrets >= 12
        p0.secrets = 12
        self.assertEqual(bot.choose_spook_burn_notice(p0, engine.state, random.Random(42)), 1)

    # =========================================================================
    # Category 5: Web API, Capabilities & Edge Cases (5 tests)
    # =========================================================================

    def test_web_serializer_includes_personal_purple_reserve(self) -> None:
        """GameStateSerializer exposes personal_purple_reserve and can_buy_purple_reserve."""
        p0 = PlayerState(0, BaseBot(0), money=5, secrets=8, patches=2, personal_purple_reserve=2)
        data = GameStateSerializer.serialize_player(p0, GameConfig(), is_human=True, name="TestPlayer")
        self.assertIn("personal_purple_reserve", data)
        self.assertEqual(data["personal_purple_reserve"], 2)
        self.assertIn("can_buy_purple_reserve", data)
        self.assertTrue(data["can_buy_purple_reserve"])

    def test_web_buy_endpoint_procures_from_personal_reserve(self) -> None:
        """POST /api/game/action/buy with color='purple' procures from personal reserve."""
        gc = GameController()
        gc.new_game(num_players=2, seed=42)
        gc.phase = 3
        gc.subphase = "operations_turn"
        gc.active_player_index = 0
        p0 = gc.state.players[0]
        p0.money = 6
        p0.personal_purple_reserve = 2

        state = gc.buy_die(player_id=0, color_str="purple")
        # Operator reserve cost is $5 (6 - 5 = 1)
        self.assertEqual(p0.money, 1)
        self.assertEqual(p0.personal_purple_reserve, 1)
        self.assertTrue(any(d.color == DieColor.PURPLE for d in p0.ready_for_release_dice))

    def test_cipher_discount_applies_to_personal_purple_reserve(self) -> None:
        """Cipher Algorithmic Arbitrage discount applies to Personal Reserve purchase ($6 - $2 = $4)."""
        gc = GameController()
        gc.new_game(num_players=2, seed=42)
        gc.phase = 3
        gc.subphase = "operations_turn"
        gc.active_player_index = 0
        p0 = gc.state.players[0]
        p0.archetype = get_archetype_by_code(ArchetypeCode.CIPHER)
        p0.money = 4
        p0.personal_purple_reserve = 2

        state = gc.buy_die(player_id=0, color_str="purple", use_cipher_ability=True)
        # Cipher operative reserve cost is $6, discounted by $2 to $4 (4 - 4 = 0)
        self.assertEqual(p0.money, 0, "Purple die under Cipher ($6) should cost $4 after $2 Cipher discount (4 - 4 = 0)")
        self.assertEqual(p0.personal_purple_reserve, 1)

    def test_reserve_dice_immune_to_corruption_track_market_returns(self) -> None:
        """INV-PURPLE-01: Personal reserve dice are immune to corruption track Return 1 Colored Die."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.personal_purple_reserve = 1
        p0.ready_for_release_dice = [d for d in p0.ready_for_release_dice if d.color == DieColor.GRAY]
        # No owned physical colored dice
        self.assertEqual(len(p0.colored_dice), 0)

        space = CorruptionSpace(index=5, label="Return 1 Colored Die", return_colored_dice=1)
        return_player_colored_dice_step2a(engine, p0, [], {}, count=space.return_colored_dice)

        self.assertEqual(p0.personal_purple_reserve, 1, "Personal Reserve must remain completely untouched at 1")

    def test_corruption_return_scraps_owned_purple_die_without_contaminating_market(self) -> None:
        """INV-PURPLE-02: Returning an owned physical Purple die scraps it and does NOT add Purple to central market."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        purple = create_colored_die(DieColor.PURPLE, 99)
        p0.ready_for_release_dice = [purple]

        space = CorruptionSpace(index=5, label="Return 1 Colored Die", return_colored_dice=1)
        return_player_colored_dice_step2a(engine, p0, [], {}, count=space.return_colored_dice)

        self.assertNotIn(purple, p0.ready_for_release_dice, "Purple die must be removed from player")
        self.assertNotIn(DieColor.PURPLE, engine.state.market, "Purple must NOT be added to central market stock")

    def test_multiple_players_cannot_interfere_with_opponents_reserve(self) -> None:
        """INV-PURPLE-01: Player A procuring a Purple die does NOT affect Player B's personal reserve."""
        engine = GameEngine(config=GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p1 = engine.state.players[1]
        p0.money = 10
        p1.money = 10
        p0.personal_purple_reserve = 2
        p1.personal_purple_reserve = 2

        class BuyPurpleP0Bot(BaseBot):
            def take_phase3_actions(self, player_state, game_state, rng):
                plan = Phase3ActionPlan()
                if player_state.player_id == 0:
                    plan.market_purchases.append(DieColor.PURPLE)
                return plan

        p0.bot = BuyPurpleP0Bot(0)
        p1.bot = BuyPurpleP0Bot(1)
        execute_phase_3(engine)

        self.assertEqual(p0.personal_purple_reserve, 1, "P0 reserve should decrement to 1")
        self.assertEqual(p1.personal_purple_reserve, 2, "P1 reserve must remain completely insulated at 2")


if __name__ == "__main__":
    unittest.main()
