"""Unit tests for Phase 50: Green Die G2 (Universal Sandbox) Redesign."""

from __future__ import annotations

import unittest

from sim.bots.base import BaseBot
from sim.bots.secret_face_policy import face_value
from sim.config import DieColor, GameConfig, ShieldColor
from sim.engine.core import GameEngine
from sim.engine.phase1_roll_deploy import execute_phase_1
from sim.engine.phase3_income import collect_player_production_income
from sim.engine.state import ProductionRole
from sim.entities import (
    apply_variant_profile,
    create_colored_die,
    get_all_variant_cards,
    get_default_variant_cards,
)
from web.schemas import GameStateSerializer


def _make_v038c_engine_with_g2(**cfg_overrides) -> GameEngine:
    cfg = GameConfig.v038c(num_players=2, **cfg_overrides)
    cards = get_default_variant_cards()
    cards[DieColor.GREEN] = get_all_variant_cards()["G2"]
    bots = [BaseBot(0, "Bot0"), BaseBot(1, "Bot1")]
    return GameEngine(config=cfg, bots=bots, seed=42, variant_cards=cards)


def _make_g2_die(engine: GameEngine, die_id: int = 99):
    g2_card = engine.state.variant_cards[DieColor.GREEN]
    die = create_colored_die(
        color=DieColor.GREEN,
        die_id=die_id,
        variant_card=g2_card,
        face_profile=engine.config.die_face_profile,
    )
    die.current_face = g2_card.star_face
    die.production_role = ProductionRole.INCOME
    return die


class TestG2UniversalSandbox(unittest.TestCase):
    """Comprehensive test matrix for G2 Universal Sandbox (spec §10)."""

    def test_g2_income_at_zero_glitches(self) -> None:
        """TC-G2-01: Verify G2 In Production yields 2 research and $0 when glitched_shield_slots == 0."""
        engine = _make_v038c_engine_with_g2()
        player = engine.state.players[0]
        player.glitched_shield_slots = 0
        player.research_tokens = 0
        player.money = 0
        player.in_production_dice = [_make_g2_die(engine)]

        rec = collect_player_production_income(engine, player)
        self.assertEqual(rec.research, 2)
        self.assertEqual(rec.money, 0)
        self.assertEqual(player.research_tokens, 2)
        self.assertEqual(player.money, 0)
        self.assertEqual(rec.details[0]["star_note"], "Universal Sandbox (+2 🔬)")

    def test_g2_income_scaling_with_glitches(self) -> None:
        """TC-G2-02: Set glitched_shield_slots to 1, 2, 3; verify yields are 3, 4, 5 research."""
        for g, expected in ((1, 3), (2, 4), (3, 5)):
            with self.subTest(glitched_slots=g):
                engine = _make_v038c_engine_with_g2()
                player = engine.state.players[0]
                player.glitched_shield_slots = g
                player.research_tokens = 0
                player.in_production_dice = [_make_g2_die(engine)]

                rec = collect_player_production_income(engine, player)
                self.assertEqual(rec.research, expected)
                self.assertEqual(player.research_tokens, expected)
                self.assertIn(f"+{expected} 🔬, incl. +{g} from {g} glitched slots", rec.details[0]["star_note"])

    def test_g2_does_not_clean_in_phase1(self) -> None:
        """TC-G2-03: Player has 2 glitched slots. Roll G2. Execute Phase 1 Step 5. Verify slots remain 2."""
        engine = _make_v038c_engine_with_g2()
        player = engine.state.players[0]
        g2_die = _make_g2_die(engine)
        g2_face = g2_die.current_face
        self.assertEqual(g2_face.clean_slots, 0)

        player.ready_for_release_dice = [g2_die]
        player.contractor_dice = []
        player.glitched_shield_slots = 2

        # Force die.roll to return G2 star face during Phase 1 execution
        g2_die.faces = [g2_face] * 6
        execute_phase_1(engine, player_ids={player.player_id})

        self.assertEqual(player.glitched_shield_slots, 2)
        self.assertEqual(player.slots_cleaned_by_face, 0)

    def test_g2_cannot_commit_to_shield(self) -> None:
        """TC-G2-04: Verify G2 star face has is_shield == False and assigns to ProductionRole.INCOME."""
        engine = _make_v038c_engine_with_g2()
        player = engine.state.players[0]
        g2_die = _make_g2_die(engine)
        g2_face = g2_die.current_face

        self.assertFalse(g2_face.is_shield)
        self.assertEqual(g2_face.block_amount, 0)
        self.assertIsNone(g2_face.shield_color)

        player.ready_for_release_dice = [g2_die]
        player.contractor_dice = []
        g2_die.faces = [g2_face] * 6
        execute_phase_1(engine, player_ids={player.player_id})

        self.assertEqual(len(player.in_production_dice), 1)
        self.assertEqual(player.in_production_dice[0].production_role, ProductionRole.INCOME)

    def test_multiple_g2_dice_independent_scaling(self) -> None:
        """TC-G2-05: Two G2 dice In Production with g=2; verify total yield is (2 + 2) + (2 + 2) = 8 research."""
        engine = _make_v038c_engine_with_g2(max_patch_tokens=10)
        player = engine.state.players[0]
        player.glitched_shield_slots = 2
        player.research_tokens = 0
        player.in_production_dice = [_make_g2_die(engine, die_id=101), _make_g2_die(engine, die_id=102)]

        rec = collect_player_production_income(engine, player)
        self.assertEqual(rec.research, 8)
        self.assertEqual(player.research_tokens, 8)

    def test_legacy_v037_parity(self) -> None:
        """TC-G2-06: Under GameConfig.legacy_v035(), verify G2 retains Block 1 Any + 1 research and does not scale."""
        cfg = GameConfig.legacy_v035(num_players=2)
        cards = get_default_variant_cards()
        cards[DieColor.GREEN] = get_all_variant_cards()["G2"]
        bots = [BaseBot(0, "Bot0"), BaseBot(1, "Bot1")]
        engine = GameEngine(config=cfg, bots=bots, seed=42, variant_cards=cards)

        g2_card = engine.state.variant_cards[DieColor.GREEN]
        self.assertEqual(g2_card.star_face.block_amount, 1)
        self.assertEqual(g2_card.star_face.shield_color, ShieldColor.ANY)
        self.assertEqual(g2_card.star_face.patches, 1)
        self.assertEqual(g2_card.star_face.clean_slots, 0)
        self.assertTrue(g2_card.star_face.is_shield)

        player = engine.state.players[0]
        player.glitched_shield_slots = 3
        player.research_tokens = 0
        player.in_production_dice = [_make_g2_die(engine)]

        rec = collect_player_production_income(engine, player)
        self.assertEqual(rec.research, 1)
        self.assertEqual(player.research_tokens, 1)
        self.assertEqual(rec.details[0]["star_note"], "Universal Sandbox (+1 🔬)")

    def test_config_tuning_levers(self) -> None:
        """TC-G2-07: Override g2_base_research=3, g2_glitch_bonus=2; verify yield with g=2 is 3 + 2*2 = 7 research."""
        engine = _make_v038c_engine_with_g2(g2_base_research=3, g2_glitch_bonus=2, max_patch_tokens=10)
        player = engine.state.players[0]
        player.glitched_shield_slots = 2
        player.research_tokens = 0
        player.in_production_dice = [_make_g2_die(engine)]

        rec = collect_player_production_income(engine, player)
        self.assertEqual(rec.research, 7)
        self.assertEqual(player.research_tokens, 7)

        with self.assertRaises(ValueError):
            GameConfig.v038c(g2_base_research=-1)
        with self.assertRaises(ValueError):
            GameConfig.v038c(g2_glitch_bonus=-1)

    def test_bot_face_valuation(self) -> None:
        """TC-G2-08: Verify face_value(player, g2_face, state) increases strictly monotonically with glitched slots."""
        engine = _make_v038c_engine_with_g2()
        player = engine.state.players[0]
        g2_face = engine.state.variant_cards[DieColor.GREEN].star_face

        vals = []
        for g in (0, 1, 2, 3):
            player.glitched_shield_slots = g
            vals.append(face_value(player, g2_face, engine.state))

        self.assertLess(vals[0], vals[1])
        self.assertLess(vals[1], vals[2])
        self.assertLess(vals[2], vals[3])

    def test_pnp_and_web_serialization(self) -> None:
        """TC-G2-09: Assert GameStateSerializer.serialize_variant_card(g2_card)['description'] matches V038_DRAFT G2 text."""
        cards = apply_variant_profile({DieColor.GREEN: get_all_variant_cards()["G2"]}, "V038_DRAFT")
        g2_card = cards[DieColor.GREEN]
        payload = GameStateSerializer.serialize_variant_card(g2_card)
        self.assertIn(
            "Gain +2 🔬, plus +1 🔬 for each of your Glitched Shield Slots.",
            payload["description"],
        )


if __name__ == "__main__":
    unittest.main()
