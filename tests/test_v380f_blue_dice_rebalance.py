"""v0.38f Blue Module Die Rebalance Test Suite.

Validates invariants INV-V38F-01 through INV-V38F-05 per docs/specs/v380f_blue_dice_rebalance_spec.md:
- INV-V38F-01: Blue Die Face Topology & Profile (Faces 1 & 2 direct Corporate Secrets)
- INV-V38F-02: Direct Phase 3 Income Resolution (source "blue_face", bypass Processing Box)
- INV-V38F-03: Face 5 Secret Banking Invariance (yield 2 at L0-L2, 3 at L3+, unaffected by Faces 1 & 2)
- INV-V38F-04: Bot Valuation & Reroll Protection (AdaptiveBalanced, Accelerationist, RecklessSaboteur)
- INV-V38F-05: Configuration Inheritance & Golden Parity (v038e, v038d unaffected)
"""

from __future__ import annotations

import random
import unittest

from sim.config import CubeColor, DieColor, GameConfig, PrPushParams
from sim.engine import GameEngine, secret_faces as sf
from sim.engine import phase3_income as p3, phase5_pipeline_shift as p5
from sim.bots.base import BaseBot
from sim.bots.adaptive_balanced import AdaptiveBalancedBot
from sim.bots.accelerationist import AccelerationistBot
from sim.bots.reckless_saboteur import RecklessSaboteurBot
from sim.bots import secret_face_policy as sfp
from sim.entities import (
    COMPANIES, CompanyCode, Face, WHITE_HATS, WhiteHatCode,
    create_colored_die, get_all_variant_cards, get_default_version_deck,
)

ALL_CARDS = get_all_variant_cards("MARKETING")


def _cards(**codes):
    code_to_color = {
        "R": DieColor.RED,
        "B": DieColor.BLUE,
        "G": DieColor.GREEN,
        "Y": DieColor.YELLOW,
    }
    out = {
        DieColor.RED: ALL_CARDS["R1"],
        DieColor.BLUE: ALL_CARDS["B1"],
        DieColor.GREEN: ALL_CARDS["G1"],
        DieColor.YELLOW: ALL_CARDS["Y1"],
    }
    for k, v in codes.items():
        color = code_to_color.get(k.upper(), DieColor[k.upper()] if k.upper() in DieColor.__members__ else None)
        if color:
            out[color] = ALL_CARDS[v]
    return out


def _engine_v038f(n=3, seed=1, cards=None, **cfg_overrides):
    bots = [BaseBot(i) for i in range(n)]
    companies = [COMPANIES[CompanyCode.PROMETHEUS], COMPANIES[CompanyCode.MERIDIAN], COMPANIES[CompanyCode.DTO]][:n]
    white_hats = [WHITE_HATS[WhiteHatCode.OPERATOR], WHITE_HATS[WhiteHatCode.ACOUSTIC], WHITE_HATS[WhiteHatCode.SPOOK]][:n]
    deck = get_default_version_deck()
    cfg = GameConfig.v038f(num_players=n, **cfg_overrides)
    return GameEngine(
        config=cfg,
        bots=bots,
        seed=seed,
        variant_cards=cards or _cards(),
        version_deck=deck,
        companies=companies,
        white_hats=white_hats,
    )


class TestV380fBlueDiceRebalance(unittest.TestCase):

    def test_v380f_config_defaults(self):
        """INV-V38F-05: Verify GameConfig.v038f() and v038f_roster() defaults."""
        cfg = GameConfig.v038f()
        self.assertEqual(cfg.die_face_profile, "V038F")
        self.assertEqual(cfg.secret_yield_blue_base, 2)
        self.assertEqual(cfg.secret_yield_blue_grid_l3_bonus, 1)
        self.assertEqual(cfg.secret_yield_blue_cap, 3)
        self.assertEqual(cfg.secret_yield_green_base, 2)
        self.assertFalse(cfg.secret_yield_green_glitch_penalty)
        self.assertTrue(cfg.green_bank_cleans_slot)
        self.assertEqual(cfg.green_triage_clean_mode, "COUNT_THEN_CLEAN")

        roster_cfg = GameConfig.v038f_roster()
        self.assertEqual(roster_cfg.die_face_profile, "V038F")
        self.assertTrue(roster_cfg.bot_pr_push)
        self.assertIsInstance(roster_cfg.bot_pr_push_params, PrPushParams)

    def test_v380f_blue_die_faces(self):
        """INV-V38F-01: Blue faces under V038F profile."""
        card = ALL_CARDS["B1"]
        die = create_colored_die(DieColor.BLUE, die_id=1, variant_card=card, face_profile="V038F")
        faces = die.faces
        self.assertEqual(len(faces), 6)

        # Face 1 & 2: +1 Corporate Secret
        self.assertEqual(faces[0].name, "+1 Corporate Secret")
        self.assertEqual(faces[0].secrets, 1)
        self.assertEqual(faces[0].patches, 0)
        self.assertEqual(faces[0].money, 0)
        self.assertFalse(faces[0].secrets_pending)

        self.assertEqual(faces[1].name, "+1 Corporate Secret")
        self.assertEqual(faces[1].secrets, 1)
        self.assertEqual(faces[1].patches, 0)
        self.assertEqual(faces[1].money, 0)
        self.assertFalse(faces[1].secrets_pending)

        # Face 3: +$1
        self.assertEqual(faces[2].name, "+$1")
        self.assertEqual(faces[2].money, 1)
        self.assertEqual(faces[2].secrets, 0)

        # Face 4: Choice +1 🔬 / +$1
        self.assertTrue(faces[3].is_choice)
        self.assertEqual(len(faces[3].choices), 2)
        self.assertEqual(faces[3].choices[0].patches, 1)
        self.assertEqual(faces[3].choices[1].money, 1)

        # Face 5: Secret face
        self.assertTrue(faces[4].secrets_pending)
        self.assertEqual(faces[4].name, "Secret")

        # Face 6: Variant star face
        self.assertTrue(faces[5].is_star)
        self.assertEqual(faces[5].star_code, "B1")

        # Verify other dice match V038D baselines
        green = create_colored_die(DieColor.GREEN, die_id=2, variant_card=ALL_CARDS["G1"], face_profile="V038F")
        self.assertEqual(green.faces[0].name, "+2 🔬")
        self.assertEqual(green.faces[0].patches, 2)

        red = create_colored_die(DieColor.RED, die_id=3, variant_card=ALL_CARDS["R1"], face_profile="V038F")
        self.assertTrue(red.faces[0].is_choice)

        yellow = create_colored_die(DieColor.YELLOW, die_id=4, variant_card=ALL_CARDS["Y1"], face_profile="V038F")
        self.assertEqual(yellow.faces[0].market_share, 2)

    def test_v380f_phase3_income_direct_secrets(self):
        """INV-V38F-02: Direct Phase 3 income resolution from Blue Face 1 and Face 2."""
        engine = _engine_v038f()
        player = engine.state.players[0]
        initial_secrets = player.secrets

        card = engine.variant_cards[DieColor.BLUE]
        blue_die1 = create_colored_die(DieColor.BLUE, die_id=101, variant_card=card, face_profile="V038F")
        blue_die1.current_face = blue_die1.faces[0]  # Face 1: +1 Corporate Secret
        blue_die1.production_role = "INCOME"

        player.in_production_dice.append(blue_die1)

        record = p3.collect_player_production_income(engine, player)

        self.assertEqual(record.secrets, 1)
        self.assertEqual(player.secrets, initial_secrets + 1)
        self.assertEqual(player.secrets_by_source.get("blue_face"), 1)
        # Die remains in in_production_dice, not moved to processing box (glitched_dice)
        self.assertIn(blue_die1, player.in_production_dice)
        self.assertNotIn(blue_die1, player.glitched_dice)

        # Test with 2 Blue dice (Face 1 and Face 2)
        blue_die2 = create_colored_die(DieColor.BLUE, die_id=102, variant_card=card, face_profile="V038F")
        blue_die2.current_face = blue_die2.faces[1]  # Face 2: +1 Corporate Secret
        blue_die2.production_role = "INCOME"
        player.in_production_dice.append(blue_die2)

        record2 = p3.collect_player_production_income(engine, player)
        self.assertEqual(record2.secrets, 2)
        self.assertEqual(player.secrets, initial_secrets + 3)
        self.assertEqual(player.secrets_by_source.get("blue_face"), 3)

    def test_v380f_face5_banking_unaffected(self):
        """INV-V38F-03: Blue Face 5 banking yield remains 2 (L0-L2) and 3 (L3+)."""
        engine = _engine_v038f()
        p = engine.state.players[0]
        cfg = engine.config

        # At Defense Grid L0
        p.defense_level = 0
        self.assertEqual(sf.secret_yield(cfg, p, DieColor.BLUE), 2)

        # At Defense Grid L2
        p.defense_level = 2
        self.assertEqual(sf.secret_yield(cfg, p, DieColor.BLUE), 2)

        # At Defense Grid L3
        p.defense_level = 3
        self.assertEqual(sf.secret_yield(cfg, p, DieColor.BLUE), 3)

        # Verify banking via secret_faces.bank
        card = engine.variant_cards[DieColor.BLUE]
        blue_die = create_colored_die(DieColor.BLUE, die_id=201, variant_card=card, face_profile="V038F")
        blue_die.current_face = blue_die.faces[4]  # Face 5: Secret
        sf.enter_processing_box(p, blue_die, 1)

        sec_before = p.secrets
        sf.bank(cfg, p, blue_die, engine.state)
        self.assertEqual(p.secrets, sec_before + 3)
        self.assertEqual(p.secrets_by_source.get("secret_face_blue"), 3)

    def test_v380f_bot_valuation_and_rerolls(self):
        """INV-V38F-04: Bot evaluation and reroll protection for Blue direct secret faces."""
        engine = _engine_v038f()
        player = engine.state.players[0]
        card = engine.variant_cards[DieColor.BLUE]
        blue_die = create_colored_die(DieColor.BLUE, die_id=301, variant_card=card, face_profile="V038F")

        # Face valuation
        f1 = blue_die.faces[0]
        self.assertEqual(f1.secrets, 1)
        val = sfp.face_value(player, f1, engine.state)
        self.assertEqual(val, sfp.SECRET_VALUE * 1)

        # AdaptiveBalancedBot reroll protection
        bot_adaptive = AdaptiveBalancedBot(player.player_id)
        blue_die.current_face = f1
        # Threat covered (staging and stuck 0)
        rerolls = bot_adaptive.choose_yahtzee_rerolls(
            player, [blue_die], rerolls_remaining=2,
            staging_cubes={}, stuck_cubes={}, directive_code="", rng=random.Random(42)
        )
        self.assertNotIn(0, rerolls, "AdaptiveBalancedBot should not reroll Face 1 (+1 Secret)")

        blue_die.current_face = blue_die.faces[1]  # Face 2
        rerolls = bot_adaptive.choose_yahtzee_rerolls(
            player, [blue_die], rerolls_remaining=2,
            staging_cubes={}, stuck_cubes={}, directive_code="", rng=random.Random(42)
        )
        self.assertNotIn(0, rerolls, "AdaptiveBalancedBot should not reroll Face 2 (+1 Secret)")

        # AccelerationistBot reroll protection
        bot_accel = AccelerationistBot(player.player_id)
        blue_die.current_face = f1
        rerolls_accel = bot_accel.choose_yahtzee_rerolls(
            player, [blue_die], rerolls_remaining=2,
            staging_cubes={}, stuck_cubes={}, directive_code="", rng=random.Random(42)
        )
        self.assertNotIn(0, rerolls_accel, "AccelerationistBot should not reroll Face 1 (+1 Secret)")

        # RecklessSaboteurBot reroll protection
        bot_reckless = RecklessSaboteurBot(player.player_id)
        blue_die.current_face = f1
        rerolls_reckless = bot_reckless.choose_yahtzee_rerolls(
            player, [blue_die], rerolls_remaining=2,
            staging_cubes={}, stuck_cubes={}, directive_code="", rng=random.Random(42)
        )
        self.assertNotIn(0, rerolls_reckless, "RecklessSaboteurBot should not reroll Face 1 (+1 Secret)")

        # Verify mean reroll value is higher for V038F Blue than V038D Blue
        blue_v038d = create_colored_die(DieColor.BLUE, die_id=302, variant_card=card, face_profile="V038D")
        mean_v038f = sfp.mean_reroll_value(player, engine.state, blue_die, 0)
        mean_v038d = sfp.mean_reroll_value(player, engine.state, blue_v038d, 0)
        self.assertGreater(mean_v038f, mean_v038d)

    def test_v380f_backwards_compatibility(self):
        """INV-V38F-05: Verify v038e and v038d configurations and dice profiles are unchanged."""
        card = ALL_CARDS["B1"]
        # v038e profile uses V038D die_face_profile
        cfg_e = GameConfig.v038e()
        self.assertEqual(cfg_e.die_face_profile, "V038D")

        die_e = create_colored_die(DieColor.BLUE, die_id=401, variant_card=card, face_profile="V038D")
        self.assertEqual(die_e.faces[0].name, "+1 🔬")
        self.assertEqual(die_e.faces[0].patches, 1)
        self.assertEqual(die_e.faces[0].secrets, 0)
        self.assertEqual(die_e.faces[1].name, "+1 🔬")
        self.assertEqual(die_e.faces[1].patches, 1)
        self.assertEqual(die_e.faces[1].secrets, 0)


if __name__ == "__main__":
    unittest.main()
