"""Unit tests for Phase 33 (v0.26.0): Variable Module Dice Costs & Turn-1 Economic Calibration.

Verifies:
- INV-START-CASH-01: Default starting cash calibrated to $4.
- INV-VAR-COST-01: Dynamic Central Market variant die pricing.
- INV-RES-COST-01: Dynamic White Hat operative personal purple reserve pricing.
- INV-PROMETHEUS-01: Dynamic Algorithmic Arbitrage discount calculation.
- INV-DIE-COST-01: Entity construction and cost binding.
- INV-MARKET-01: Market purchasing operations and stock management.
- INV-PURPLE-02: Personal Reserve procurement validation.
- Bot AI heuristics and Web API serializers / controllers.
"""

import random
import unittest
from typing import Dict

from sim.bots.adaptive_balanced import AdaptiveBalancedBot
from sim.bots.base import BaseBot, Phase3ActionPlan
from sim.bots.secops_turtle import SecOpsTurtleBot
from sim.config import GameConfig
from sim.engine.core import GameEngine
from sim.engine.phase3_ops import execute_phase_3
from sim.engine.state import GameState, PlayerState
from sim.entities import (
    CANONICAL_COMPANY_FOR_OPERATIVE,
    COMPANIES,
    WHITE_HATS,
    ArchetypeCode,
    CompanyCode,
    CubeColor,
    DieColor,
    Face,
    ShieldColor,
    VariantCard,
    WhiteHatCode,
    create_colored_die,
    create_gray_die,
    create_white_die,
    get_all_variant_cards,
    get_all_version_cards,
    get_all_white_hats,
    get_company_by_code,
    get_default_variant_cards,
    get_white_hat_by_code,
)
from web.controller.core import GameController
from web.schemas import GameStateSerializer


class TestV260VariableDiceCosts(unittest.TestCase):
    """30 Comprehensive verification test cases for Phase 33 (v0.26.0)."""

    def setUp(self) -> None:
        self.rng = random.Random(42)
        self.variants = get_all_variant_cards()

    # -------------------------------------------------------------------------
    # TEST-VAR-01: Default starting cash is $6 (INV-START-CASH-01)
    # -------------------------------------------------------------------------
    def test_default_starting_cash_is_four(self) -> None:
        """Instantiate GameEngine; verify player.money == 6 for all players. Verify GameConfig().starting_money == 6."""
        cfg = GameConfig()
        self.assertEqual(cfg.starting_money, 6)

        engine = GameEngine(cfg, seed=42)
        cash_bonus = 1 if engine.state.active_directive_code == "DATA_SCRAPER" else 0
        for p in engine.state.players:
            self.assertEqual(p.money, 6 + cash_bonus, f"Player {p.player_id} must initialize with exactly ${6 + cash_bonus} starting cash")

    # -------------------------------------------------------------------------
    # TEST-VAR-02: Version cash bonus stacks on $6 (INV-START-CASH-01)
    # -------------------------------------------------------------------------
    def test_version_cash_bonus_stacks_on_four(self) -> None:
        """Initialize engine with Data Scraper (starting_cash_bonus=1); verify players start with $7."""
        data_scraper = [c for c in get_all_version_cards() if c.directive_code == "DATA_SCRAPER"][0]
        cfg = GameConfig(num_players=2)
        engine = GameEngine(config=cfg, seed=42, version_deck=[data_scraper])
        for p in engine.state.players:
            self.assertEqual(p.money, 7, "Data Scraper starting cash bonus (+$1) must stack onto $6 to yield $7")

    # -------------------------------------------------------------------------
    # TEST-VAR-03: All 12 market variants have strictly positive integer costs (INV-VAR-COST-01)
    # -------------------------------------------------------------------------
    def test_all_variants_have_positive_costs(self) -> None:
        """Iterate get_all_variant_cards(); assert isinstance(v.cost, int) and v.cost > 0 for all 12 market variants."""
        for code, card in self.variants.items():
            self.assertIsInstance(card.cost, int)
            self.assertGreater(card.cost, 0, f"Variant {code} cost must be strictly greater than 0")

    # -------------------------------------------------------------------------
    # TEST-VAR-04: Red variant costs calibration (INV-VAR-COST-01)
    # -------------------------------------------------------------------------
    def test_red_variant_costs(self) -> None:
        """Assert R1.cost == 5, R2.cost == 5, R3.cost == 4."""
        self.assertEqual(self.variants["R1"].cost, 5)
        self.assertEqual(self.variants["R2"].cost, 5)
        self.assertEqual(self.variants["R3"].cost, 4)

    # -------------------------------------------------------------------------
    # TEST-VAR-05: Blue variant costs calibration (INV-VAR-COST-01)
    # -------------------------------------------------------------------------
    def test_blue_variant_costs(self) -> None:
        """Assert B1.cost == 5, B2.cost == 6, B3.cost == 4."""
        self.assertEqual(self.variants["B1"].cost, 5)
        self.assertEqual(self.variants["B2"].cost, 6)
        self.assertEqual(self.variants["B3"].cost, 4)

    # -------------------------------------------------------------------------
    # TEST-VAR-06: Green variant costs calibration (INV-VAR-COST-01)
    # -------------------------------------------------------------------------
    def test_green_variant_costs(self) -> None:
        """Assert G1.cost == 5, G2.cost == 4, G3.cost == 4."""
        self.assertEqual(self.variants["G1"].cost, 5)
        self.assertEqual(self.variants["G2"].cost, 4)
        self.assertEqual(self.variants["G3"].cost, 4)

    # -------------------------------------------------------------------------
    # TEST-VAR-07: Yellow variant costs calibration (INV-VAR-COST-01)
    # -------------------------------------------------------------------------
    def test_yellow_variant_costs(self) -> None:
        """Assert Y1.cost == 6, Y2.cost == 5, Y3.cost == 5."""
        self.assertEqual(self.variants["Y1"].cost, 6)
        self.assertEqual(self.variants["Y2"].cost, 5)
        self.assertEqual(self.variants["Y3"].cost, 5)

    # -------------------------------------------------------------------------
    # TEST-VAR-08: All White Hats have positive integer reserve costs (INV-RES-COST-01)
    # -------------------------------------------------------------------------
    def test_all_white_hats_have_reserve_costs(self) -> None:
        """Iterate get_all_white_hats(); assert isinstance(w.reserve_cost, int) and w.reserve_cost > 0 for all 6 operatives."""
        for wh in get_all_white_hats():
            self.assertIsInstance(wh.reserve_cost, int)
            self.assertGreater(wh.reserve_cost, 0, f"WhiteHat {wh.code} reserve_cost must be > 0")

    # -------------------------------------------------------------------------
    # TEST-VAR-09: Operative reserve cost calibration (INV-RES-COST-01)
    # -------------------------------------------------------------------------
    def test_operative_reserve_cost_calibration(self) -> None:
        """Assert Acoustic: 4, Phreaker: 4, Operator: 5, Prodigy: 5, Spook: 5, Cipher: 6."""
        self.assertEqual(WHITE_HATS[WhiteHatCode.ACOUSTIC].reserve_cost, 4)
        self.assertEqual(WHITE_HATS[WhiteHatCode.PHREAKER].reserve_cost, 4)
        self.assertEqual(WHITE_HATS[WhiteHatCode.OPERATOR].reserve_cost, 5)
        self.assertEqual(WHITE_HATS[WhiteHatCode.PRODIGY].reserve_cost, 5)
        self.assertEqual(WHITE_HATS[WhiteHatCode.SPOOK].reserve_cost, 5)
        self.assertEqual(WHITE_HATS[WhiteHatCode.CIPHER].reserve_cost, 6)

    # -------------------------------------------------------------------------
    # TEST-VAR-10: GameState.get_market_die_cost (INV-VAR-COST-01)
    # -------------------------------------------------------------------------
    def test_game_state_get_market_die_cost(self) -> None:
        """Set active variant cards to R3 ($4), B2 ($6), G1 ($5), Y1 ($6); verify get_market_die_cost returns 4, 6, 5, 6."""
        engine = GameEngine(GameConfig(num_players=2), seed=42)
        engine.state.variant_cards = {
            DieColor.RED: self.variants["R3"],
            DieColor.BLUE: self.variants["B2"],
            DieColor.GREEN: self.variants["G1"],
            DieColor.YELLOW: self.variants["Y1"],
        }
        self.assertEqual(engine.state.get_market_die_cost(DieColor.RED), 4)
        self.assertEqual(engine.state.get_market_die_cost(DieColor.BLUE), 6)
        self.assertEqual(engine.state.get_market_die_cost(DieColor.GREEN), 5)
        self.assertEqual(engine.state.get_market_die_cost(DieColor.YELLOW), 6)

    # -------------------------------------------------------------------------
    # TEST-VAR-11: PlayerState.get_purple_reserve_cost (INV-RES-COST-01)
    # -------------------------------------------------------------------------
    def test_player_state_get_purple_reserve_cost(self) -> None:
        """Pair player with The Cipher; assert get_purple_reserve_cost() == 6. Pair with The Acoustic; assert == 4."""
        engine = GameEngine(GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]

        p0.white_hat = WHITE_HATS[WhiteHatCode.CIPHER]
        self.assertEqual(p0.get_purple_reserve_cost(), 6)

        p0.white_hat = WHITE_HATS[WhiteHatCode.ACOUSTIC]
        self.assertEqual(p0.get_purple_reserve_cost(), 4)

    # -------------------------------------------------------------------------
    # TEST-VAR-12: create_colored_die binds variant cost (INV-DIE-COST-01)
    # -------------------------------------------------------------------------
    def test_create_colored_die_binds_variant_cost(self) -> None:
        """Call create_colored_die with B2; assert die.cost == 6. Call with R3; assert die.cost == 4."""
        die_b2 = create_colored_die(DieColor.BLUE, 1, self.variants["B2"])
        self.assertEqual(die_b2.cost, 6)
        self.assertEqual(die_b2.variant_code, "B2")

        die_r3 = create_colored_die(DieColor.RED, 2, self.variants["R3"])
        self.assertEqual(die_r3.cost, 4)
        self.assertEqual(die_r3.variant_code, "R3")

    # -------------------------------------------------------------------------
    # TEST-VAR-13: create_colored_die binds reserve cost (INV-DIE-COST-01)
    # -------------------------------------------------------------------------
    def test_create_colored_die_binds_reserve_cost(self) -> None:
        """Call create_colored_die for PURPLE with reserve_cost=6; assert die.cost == 6."""
        die_purple = create_colored_die(DieColor.PURPLE, 1, reserve_cost=6)
        self.assertEqual(die_purple.cost, 6)
        self.assertEqual(die_purple.color, DieColor.PURPLE)

    # -------------------------------------------------------------------------
    # TEST-VAR-14: create_colored_die fallback defaults (INV-DIE-COST-01)
    # -------------------------------------------------------------------------
    def test_create_colored_die_fallback_defaults(self) -> None:
        """Call create_colored_die with variant_card=None; assert Red=5, Blue=5, Green=5, Yellow=6, Gray=0, White=1."""
        self.assertEqual(create_colored_die(DieColor.RED, 1).cost, 5)
        self.assertEqual(create_colored_die(DieColor.BLUE, 2).cost, 5)
        self.assertEqual(create_colored_die(DieColor.GREEN, 3).cost, 5)
        self.assertEqual(create_colored_die(DieColor.YELLOW, 4).cost, 6)
        self.assertEqual(create_colored_die(DieColor.GRAY, 5).cost, 0)
        self.assertEqual(create_colored_die(DieColor.WHITE, 6).cost, 1)

    # -------------------------------------------------------------------------
    # TEST-VAR-15: Phase 3 market purchase deducts exact cost (INV-MARKET-01)
    # -------------------------------------------------------------------------
    def test_phase3_market_purchase_deducts_exact_cost(self) -> None:
        """Set active Blue to B2 ($6). Player has $6; buy Blue; assert player.money == 0, stock decrements, die in ready."""
        engine = GameEngine(GameConfig(num_players=2), seed=42)
        engine.state.variant_cards[DieColor.BLUE] = self.variants["B2"]
        p0 = engine.state.players[0]
        p0.money = 6
        initial_stock = engine.state.market[DieColor.BLUE]
        initial_ready_count = len(p0.ready_for_release_dice)

        class BuyBlueBot(BaseBot):
            def take_phase3_actions(self, player_state, game_state, rng):
                plan = Phase3ActionPlan()
                plan.market_purchases.append(DieColor.BLUE)
                return plan

        p0.bot = BuyBlueBot(0)
        execute_phase_3(engine)

        self.assertEqual(p0.money, 0)
        self.assertEqual(engine.state.market[DieColor.BLUE], initial_stock - 1)
        self.assertEqual(len(p0.ready_for_release_dice), initial_ready_count + 1)
        purchased_die = p0.ready_for_release_dice[-1]
        self.assertEqual(purchased_die.color, DieColor.BLUE)
        self.assertEqual(purchased_die.cost, 6)

    # -------------------------------------------------------------------------
    # TEST-VAR-16: Phase 3 market purchase rejects insufficient funds (INV-MARKET-01)
    # -------------------------------------------------------------------------
    def test_phase3_market_purchase_rejects_insufficient_funds(self) -> None:
        """Set active Blue to B2 ($6). Player has $5; assert purchase fails / die not bought."""
        engine = GameEngine(GameConfig(num_players=2), seed=42)
        engine.state.variant_cards[DieColor.BLUE] = self.variants["B2"]
        p0 = engine.state.players[0]
        p0.money = 5
        initial_stock = engine.state.market[DieColor.BLUE]
        initial_ready_count = len(p0.ready_for_release_dice)

        class BuyBlueBot(BaseBot):
            def take_phase3_actions(self, player_state, game_state, rng):
                plan = Phase3ActionPlan()
                plan.market_purchases.append(DieColor.BLUE)
                return plan

        p0.bot = BuyBlueBot(0)
        execute_phase_3(engine)

        self.assertEqual(p0.money, 5)
        self.assertEqual(engine.state.market[DieColor.BLUE], initial_stock)
        self.assertEqual(len(p0.ready_for_release_dice), initial_ready_count)

    # -------------------------------------------------------------------------
    # TEST-VAR-17: Phase 3 purple purchase deducts operative cost (INV-PURPLE-02)
    # -------------------------------------------------------------------------
    def test_phase3_purple_purchase_deducts_operative_cost(self) -> None:
        """Player with The Prodigy ($5) has $5; procure purple; assert player.money == 0, reserve == 0."""
        engine = GameEngine(GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.white_hat = WHITE_HATS[WhiteHatCode.PRODIGY]
        p0.money = 5
        p0.personal_purple_reserve = 1

        class BuyPurpleBot(BaseBot):
            def take_phase3_actions(self, player_state, game_state, rng):
                plan = Phase3ActionPlan()
                plan.buy_purple_reserve = True
                return plan

        p0.bot = BuyPurpleBot(0)
        execute_phase_3(engine)

        self.assertEqual(p0.money, 0)
        self.assertEqual(p0.personal_purple_reserve, 0)
        purple_dice = [d for d in p0.ready_for_release_dice if d.color == DieColor.PURPLE]
        self.assertEqual(len(purple_dice), 2)
        self.assertEqual(purple_dice[-1].cost, 5)

    # -------------------------------------------------------------------------
    # TEST-VAR-18: Phase 3 purple purchase rejects insufficient funds (INV-PURPLE-02)
    # -------------------------------------------------------------------------
    def test_phase3_purple_purchase_rejects_insufficient_funds(self) -> None:
        """Player with The Cipher ($6) has $5; assert purple procurement fails; reserve remains 1."""
        engine = GameEngine(GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.white_hat = WHITE_HATS[WhiteHatCode.CIPHER]
        p0.money = 5
        p0.personal_purple_reserve = 1

        class BuyPurpleBot(BaseBot):
            def take_phase3_actions(self, player_state, game_state, rng):
                plan = Phase3ActionPlan()
                plan.buy_purple_reserve = True
                return plan

        p0.bot = BuyPurpleBot(0)
        execute_phase_3(engine)

        self.assertEqual(p0.money, 5)
        self.assertEqual(p0.personal_purple_reserve, 1)
        purple_dice = [d for d in p0.ready_for_release_dice if d.color == DieColor.PURPLE]
        self.assertEqual(len(purple_dice), 1)  # only starter purple

    # -------------------------------------------------------------------------
    # TEST-VAR-19: Prometheus discount on high-tier market die (INV-PROMETHEUS-01)
    # -------------------------------------------------------------------------
    def test_prometheus_discount_on_high_tier_market_die(self) -> None:
        """Active B2 ($6). Prometheus activates discount; assert purchase price is max(0, 6 - 2) = $4."""
        engine = GameEngine(
            GameConfig(num_players=2),
            companies=[COMPANIES[CompanyCode.PROMETHEUS], COMPANIES[CompanyCode.AEGIS]],
            white_hats=[WHITE_HATS[WhiteHatCode.OPERATOR], WHITE_HATS[WhiteHatCode.ACOUSTIC]],
            seed=42,
        )
        engine.state.variant_cards[DieColor.BLUE] = self.variants["B2"]
        p0 = engine.state.players[0]
        p0.money = 4

        class PromBot(BaseBot):
            def take_phase3_actions(self, player_state, game_state, rng):
                plan = Phase3ActionPlan()
                plan.use_prometheus_override = True
                plan.prometheus_mode = "BUY_FREE_DIE"
                plan.prometheus_discount_die_color = DieColor.BLUE
                return plan

        p0.bot = PromBot(0)
        execute_phase_3(engine)

        self.assertEqual(p0.money, 0, "B2 ($6) with $2 discount should cost $4 (4 - 4 = 0)")
        self.assertTrue(any(d.color == DieColor.BLUE for d in p0.ready_for_release_dice))

    # -------------------------------------------------------------------------
    # TEST-VAR-20: Prometheus discount on budget market die (INV-PROMETHEUS-01)
    # -------------------------------------------------------------------------
    def test_prometheus_discount_on_budget_market_die(self) -> None:
        """Active R3 ($4). Prometheus activates discount; assert purchase price is max(0, 4 - 2) = $2."""
        engine = GameEngine(
            GameConfig(num_players=2),
            companies=[COMPANIES[CompanyCode.PROMETHEUS], COMPANIES[CompanyCode.AEGIS]],
            white_hats=[WHITE_HATS[WhiteHatCode.OPERATOR], WHITE_HATS[WhiteHatCode.ACOUSTIC]],
            seed=42,
        )
        engine.state.variant_cards[DieColor.RED] = self.variants["R3"]
        p0 = engine.state.players[0]
        p0.money = 2

        class PromBot(BaseBot):
            def take_phase3_actions(self, player_state, game_state, rng):
                plan = Phase3ActionPlan()
                plan.use_prometheus_override = True
                plan.prometheus_mode = "BUY_FREE_DIE"
                plan.prometheus_discount_die_color = DieColor.RED
                return plan

        p0.bot = PromBot(0)
        execute_phase_3(engine)

        self.assertEqual(p0.money, 0, "R3 ($4) with $2 discount should cost $2 (2 - 2 = 0)")
        self.assertTrue(any(d.color == DieColor.RED for d in p0.ready_for_release_dice))

    # -------------------------------------------------------------------------
    # TEST-VAR-21: Prometheus discount on purple reserve (INV-PROMETHEUS-01)
    # -------------------------------------------------------------------------
    def test_prometheus_discount_on_purple_reserve(self) -> None:
        """Player with Prometheus + The Cipher ($6); procure Purple; assert cost is max(0, 6 - 2) = $4."""
        engine = GameEngine(
            GameConfig(num_players=2),
            companies=[COMPANIES[CompanyCode.PROMETHEUS], COMPANIES[CompanyCode.AEGIS]],
            white_hats=[WHITE_HATS[WhiteHatCode.CIPHER], WHITE_HATS[WhiteHatCode.ACOUSTIC]],
            seed=42,
        )
        p0 = engine.state.players[0]
        p0.money = 4
        p0.personal_purple_reserve = 2

        class PromBot(BaseBot):
            def take_phase3_actions(self, player_state, game_state, rng):
                plan = Phase3ActionPlan()
                plan.use_prometheus_override = True
                plan.prometheus_mode = "BUY_FREE_DIE"
                plan.prometheus_discount_die_color = DieColor.PURPLE
                return plan

        p0.bot = PromBot(0)
        execute_phase_3(engine)

        self.assertEqual(p0.money, 0, "Cipher Purple ($6) with $2 discount should cost $4 (4 - 4 = 0)")
        self.assertEqual(p0.personal_purple_reserve, 1)

    # -------------------------------------------------------------------------
    # TEST-VAR-22: Prometheus discount on budget purple reserve (INV-PROMETHEUS-01)
    # -------------------------------------------------------------------------
    def test_prometheus_discount_on_budget_purple_reserve(self) -> None:
        """Player with Prometheus + The Acoustic ($4); procure Purple; assert cost is max(0, 4 - 2) = $2."""
        engine = GameEngine(
            GameConfig(num_players=2),
            companies=[COMPANIES[CompanyCode.PROMETHEUS], COMPANIES[CompanyCode.AEGIS]],
            white_hats=[WHITE_HATS[WhiteHatCode.ACOUSTIC], WHITE_HATS[WhiteHatCode.OPERATOR]],
            seed=42,
        )
        p0 = engine.state.players[0]
        p0.money = 2
        p0.personal_purple_reserve = 2

        class PromBot(BaseBot):
            def take_phase3_actions(self, player_state, game_state, rng):
                plan = Phase3ActionPlan()
                plan.use_prometheus_override = True
                plan.prometheus_mode = "BUY_FREE_DIE"
                plan.prometheus_discount_die_color = DieColor.PURPLE
                return plan

        p0.bot = PromBot(0)
        execute_phase_3(engine)

        self.assertEqual(p0.money, 0, "Acoustic Purple ($4) with $2 discount should cost $2 (2 - 2 = 0)")
        self.assertEqual(p0.personal_purple_reserve, 1)

    # -------------------------------------------------------------------------
    # TEST-VAR-23: Bot base & SecOps purple reserve heuristic (Bot AI)
    # -------------------------------------------------------------------------
    def test_bot_base_purple_reserve_heuristic(self) -> None:
        """Assert choose_purple_reserve_purchase returns False if cash < reserve_cost + 2 for BaseBot and SecOpsTurtleBot (v0.30.0)."""
        bot = BaseBot(0)
        secops = SecOpsTurtleBot(1)
        engine = GameEngine(GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.white_hat = WHITE_HATS[WhiteHatCode.CIPHER]  # reserve_cost = 6
        p0.personal_purple_reserve = 1

        p0.money = 5
        self.assertFalse(bot.choose_purple_reserve_purchase(p0, engine.state, self.rng))
        self.assertFalse(secops.choose_purple_reserve_purchase(p0, engine.state, self.rng), "SecOpsTurtleBot must reject when cash ($5) < Cipher reserve ($6)")

        p0.money = 6
        self.assertFalse(bot.choose_purple_reserve_purchase(p0, engine.state, self.rng))
        self.assertTrue(secops.choose_purple_reserve_purchase(p0, engine.state, self.rng))

        p0.money = 8
        self.assertTrue(bot.choose_purple_reserve_purchase(p0, engine.state, self.rng))
        self.assertTrue(secops.choose_purple_reserve_purchase(p0, engine.state, self.rng))

    # -------------------------------------------------------------------------
    # TEST-VAR-24: AdaptiveBalancedBot respects variant costs (Bot AI)
    # -------------------------------------------------------------------------
    def test_adaptive_balanced_bot_respects_variant_costs(self) -> None:
        """Run bot Phase 3 planning with $4 cash and $5 Red market die; assert bot does not plan purchase."""
        bot = AdaptiveBalancedBot(0)
        engine = GameEngine(GameConfig(num_players=2), seed=42)
        engine.state.variant_cards[DieColor.RED] = self.variants["R1"]  # Cost: $5
        p0 = engine.state.players[0]
        p0.money = 4
        p0.personal_purple_reserve = 0  # Disable purple reserve

        plan = bot.take_phase3_actions(p0, engine.state, self.rng)
        self.assertNotIn(DieColor.RED, plan.market_purchases)

    # -------------------------------------------------------------------------
    # TEST-VAR-25: Web serializer variant card cost (Web API)
    # -------------------------------------------------------------------------
    def test_web_serializer_variant_card_cost(self) -> None:
        """Call GameStateSerializer.serialize_variant_card(B2); assert output dictionary contains 'cost': 6."""
        res = GameStateSerializer.serialize_variant_card(self.variants["B2"])
        self.assertEqual(res["cost"], 6)
        self.assertEqual(res["code"], "B2")

    # -------------------------------------------------------------------------
    # TEST-VAR-26: Web serializer white hat reserve cost (Web API)
    # -------------------------------------------------------------------------
    def test_web_serializer_white_hat_reserve_cost(self) -> None:
        """Call GameStateSerializer.serialize_white_hat(CIPHER); assert output contains 'reserve_cost': 6."""
        res = GameStateSerializer.serialize_white_hat(WHITE_HATS[WhiteHatCode.CIPHER])
        self.assertIsNotNone(res)
        self.assertEqual(res["reserve_cost"], 6)

    # -------------------------------------------------------------------------
    # TEST-VAR-27: Web serializer game state market costs (Web API)
    # -------------------------------------------------------------------------
    def test_web_serializer_game_state_market_costs(self) -> None:
        """Call serialize_game_state; assert market['blue']['cost'] reflects active variant cost."""
        engine = GameEngine(GameConfig(num_players=2), seed=42)
        engine.state.variant_cards[DieColor.BLUE] = self.variants["B2"]  # Cost: $6
        engine.state.variant_cards[DieColor.YELLOW] = self.variants["Y1"]  # Cost: $6

        meta = {"players": {}, "player_ranks": {}}
        serialized = GameStateSerializer.serialize_game_state(engine.state, meta)

        self.assertEqual(serialized["market"]["blue"]["cost"], 6)
        self.assertEqual(serialized["market"]["yellow"]["cost"], 6)

    # -------------------------------------------------------------------------
    # TEST-VAR-28: Web serializer player purple reserve cost (Web API)
    # -------------------------------------------------------------------------
    def test_web_serializer_player_purple_reserve_cost(self) -> None:
        """Call serialize_player; assert purple_reserve_cost matches operative and can_buy_purple_reserve checks dynamic cost."""
        engine = GameEngine(GameConfig(num_players=2), seed=42)
        p0 = engine.state.players[0]
        p0.white_hat = WHITE_HATS[WhiteHatCode.CIPHER]  # reserve_cost = 6
        p0.personal_purple_reserve = 1

        p0.money = 5
        s1 = GameStateSerializer.serialize_player(p0, engine.state.config, is_human=True, name="Player 1")
        self.assertEqual(s1["purple_reserve_cost"], 6)
        self.assertFalse(s1["can_buy_purple_reserve"])

        p0.money = 6
        s2 = GameStateSerializer.serialize_player(p0, engine.state.config, is_human=True, name="Player 1")
        self.assertEqual(s2["purple_reserve_cost"], 6)
        self.assertTrue(s2["can_buy_purple_reserve"])

    # -------------------------------------------------------------------------
    # TEST-VAR-29: Web controller buy action dynamic cost (Web Controller)
    # -------------------------------------------------------------------------
    def test_web_controller_buy_action_dynamic_cost(self) -> None:
        """Execute /api/game/action/buy with Blue B2 ($6); verify $6 deducted from player cash."""
        gc = GameController()
        gc.new_game(num_players=2, seed=42)
        gc.state.variant_cards[DieColor.BLUE] = self.variants["B2"]  # Cost: $6
        gc.phase = 3
        gc.subphase = "operations_turn"
        gc.active_player_index = 0
        p0 = gc.state.players[0]
        p0.money = 10

        gc.buy_die(player_id=0, color_str="blue")
        self.assertEqual(p0.money, 4, "Buying B2 ($6) with $10 cash leaves $4 (10 - 6 = 4)")

    # -------------------------------------------------------------------------
    # TEST-VAR-30: Web controller purple buy action dynamic cost (Web Controller)
    # -------------------------------------------------------------------------
    def test_web_controller_purple_buy_action_dynamic_cost(self) -> None:
        """Execute /api/game/action/buy with purple under The Spook ($5); verify $5 deducted."""
        gc = GameController()
        gc.new_game(num_players=2, seed=42)
        p0 = gc.state.players[0]
        p0.white_hat = WHITE_HATS[WhiteHatCode.SPOOK]  # reserve_cost: 5
        p0.money = 10
        p0.personal_purple_reserve = 1
        gc.phase = 3
        gc.subphase = "operations_turn"
        gc.active_player_index = 0

        gc.buy_die(player_id=0, color_str="purple")
        self.assertEqual(p0.money, 5, "Procuring Purple under The Spook ($5) with $10 cash leaves $5 (10 - 5 = 5)")
        self.assertEqual(p0.personal_purple_reserve, 0)


if __name__ == "__main__":
    unittest.main()
