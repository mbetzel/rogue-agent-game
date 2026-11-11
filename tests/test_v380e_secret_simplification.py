"""v0.38e Secret Face Simplification & Processing Triggers Test Suite.

Validates invariants INV-V38E-01 through INV-V38E-08 per docs/specs/v380e_secret_simplification_spec.md:
- INV-V38E-01: Universal Baseline Secret Yields (Red=2, Blue=2, Green=2, Purple=1)
- INV-V38E-02: Blue Defense Grid Trigger & Memory Liberation (Grid < 3 -> 2, Grid >= 3 -> 3, cap 3, no blocked_blue check)
- INV-V38E-03: Phase 3 & Phase 5 Blue Banking Equivalence (B3, Jumper Diagnostics, Conveyor Triage)
- INV-V38E-04: Green Flat Yield & Mat Decontamination (unconditional 2 yield, cleans 1 slot)
- INV-V38E-05: Red Market Leader Bonus Trigger (yield 2, sets state.red_secret_banked_this_round = True)
- INV-V38E-06: Purple Pure Specialist Yield (yield 1, zero triggers)
- INV-V38E-07: Non-Banking Exit Invariance (Burn Notice, return, stranded -> 0 yield, 0 clean)
- INV-V38E-08: Backwards Compatibility & Golden Parity (v038d, v038c, v038b, v038, v037)
"""

from __future__ import annotations

import unittest

from sim.config import CubeColor, DieColor, GameConfig, ResearchTrackModel, TowerMode
from sim.engine import GameEngine, fast_clone, secret_faces as sf
from sim.engine import phase3_income as p3, phase5_pipeline_shift as p5
from sim.bots.base import BaseBot
from sim.bots import secret_face_policy as sfp
from sim.entities import (
    COMPANIES, CompanyCode, Face, WHITE_HATS, WhiteHatCode,
    create_colored_die, create_gray_die, get_all_variant_cards,
    get_default_version_deck,
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


def _engine_v038e(n=3, seed=1, cards=None, **cfg_overrides):
    bots = [BaseBot(i) for i in range(n)]
    companies = [COMPANIES[CompanyCode.PROMETHEUS], COMPANIES[CompanyCode.MERIDIAN], COMPANIES[CompanyCode.DTO]][:n]
    white_hats = [WHITE_HATS[WhiteHatCode.OPERATOR], WHITE_HATS[WhiteHatCode.ACOUSTIC], WHITE_HATS[WhiteHatCode.SPOOK]][:n]
    deck = get_default_version_deck()
    cfg = GameConfig.v038e(num_players=n, **cfg_overrides)
    return GameEngine(
        config=cfg,
        bots=bots,
        seed=seed,
        variant_cards=cards or _cards(),
        version_deck=deck,
        companies=companies,
        white_hats=white_hats,
    )


class TestV380eSecretSimplification(unittest.TestCase):

    def test_v380e_config_defaults(self):
        """Verify GameConfig.v038e() initializes levers according to spec §3."""
        cfg = GameConfig.v038e()
        self.assertEqual(cfg.secret_yield_blue_base, 2)
        self.assertEqual(cfg.secret_yield_blue_block_bonus, 0)
        self.assertEqual(cfg.secret_yield_blue_grid_l3_bonus, 1)
        self.assertEqual(cfg.secret_yield_blue_cap, 3)
        self.assertEqual(cfg.secret_yield_green_base, 2)
        self.assertFalse(cfg.secret_yield_green_glitch_penalty)
        self.assertTrue(cfg.green_bank_cleans_slot)
        self.assertEqual(cfg.green_triage_clean_mode, "COUNT_THEN_CLEAN")
        self.assertEqual(cfg.red_secret_owner_yield, 2)
        self.assertEqual(cfg.secret_yield_purple, 1)

        # Roster config
        roster_cfg = GameConfig.v038e_roster()
        self.assertTrue(roster_cfg.bot_pr_push)
        self.assertEqual(roster_cfg.secret_yield_blue_base, 2)
        self.assertFalse(roster_cfg.secret_yield_green_glitch_penalty)

        # Validation: secret_yield_green_glitch_penalty must be bool
        with self.assertRaises(ValueError):
            GameConfig.v038e(secret_yield_green_glitch_penalty="not_a_bool")

    def test_v380e_blue_yield_grid_l0_l2(self):
        """INV-V38E-01, INV-V38E-02: Defense Grid L0, L1, L2 yield exactly 2 Secrets, regardless of blocked Blue."""
        engine = _engine_v038e()
        p = engine.state.players[0]
        cfg = engine.config

        for lvl in (0, 1, 2):
            p.defense_level = lvl
            for blocked in (0, 1, 3):
                p.blocked_blue_this_round = blocked
                y = sf.secret_yield(cfg, p, DieColor.BLUE)
                self.assertEqual(y, 2, f"Expected 2 at defense level {lvl} with {blocked} blocked, got {y}")

    def test_v380e_blue_yield_grid_l3_l4(self):
        """INV-V38E-02: Defense Grid L3 and L4 yield exactly 3 Corporate Secrets (capped at 3)."""
        engine = _engine_v038e()
        p = engine.state.players[0]
        cfg = engine.config

        for lvl in (3, 4):
            p.defense_level = lvl
            for blocked in (0, 1, 3):
                p.blocked_blue_this_round = blocked
                y = sf.secret_yield(cfg, p, DieColor.BLUE)
                self.assertEqual(y, 3, f"Expected 3 at defense level {lvl} with {blocked} blocked, got {y}")

        # Invariant on banking a Blue die
        blue_die = create_colored_die(DieColor.BLUE, 999)
        sf.enter_processing_box(p, blue_die, 1)
        p.defense_level = 3
        start_secrets = p.secrets
        banked = sf.bank(cfg, p, blue_die, engine.state)
        self.assertEqual(banked, 3)
        self.assertEqual(p.secrets, start_secrets + 3)
        self.assertEqual(p.secret_yield_hist[sf._ckey(DieColor.BLUE)]["3"], 1)

    def test_v380e_blue_phase3_instant_bank(self):
        """INV-V38E-03: Phase 3 B3 Air-Gapped Backup banks Blue die with identical yield to Phase 5."""
        engine = _engine_v038e(cards=_cards(B="B3"))
        p = engine.state.players[0]
        p.defense_level = 3  # Level 3 -> yield should be 3

        # Prepare a Blue die in Processing Box
        blue_die = create_colored_die(DieColor.BLUE, 101)
        sf.enter_processing_box(p, blue_die, 1)
        self.assertIn(blue_die, p.glitched_dice)

        # Prepare a die showing B3 in In Production
        b3_die = create_colored_die(DieColor.BLUE, 102)
        b3_card = ALL_CARDS["B3"]
        b3_die.current_face = b3_card.star_face
        p.in_production_dice.append(b3_die)

        start_secrets = p.secrets
        # Trigger Phase 3 income
        p3.collect_player_production_income(engine, p)

        # Blue die was banked by B3
        self.assertNotIn(blue_die, p.glitched_dice)
        self.assertIn(blue_die, p.scanned_dice)
        self.assertEqual(p.secrets - start_secrets, 3)  # Yield was 3, identical to Phase 5 triage

    def test_v380e_green_flat_yield_and_clean(self):
        """INV-V38E-04: Green die banks exactly 2 Secrets regardless of glitched slots, and cleans 1 slot."""
        engine = _engine_v038e()
        p = engine.state.players[0]
        cfg = engine.config

        # Test yields with 0, 1, 2, 3 glitched slots
        for g in (0, 1, 2, 3):
            p.glitched_shield_slots = g
            y = sf.secret_yield(cfg, p, DieColor.GREEN)
            self.assertEqual(y, 2, f"Expected flat yield 2 with {g} glitched slots, got {y}")

        # Test banking a Green die with 2 glitched slots
        p.glitched_shield_slots = 2
        p.slots_cleaned_by_green_triage = 0
        green_die = create_colored_die(DieColor.GREEN, 201)
        sf.enter_processing_box(p, green_die, 1)
        start_secrets = p.secrets

        banked = sf.bank(cfg, p, green_die, engine.state)
        self.assertEqual(banked, 2)
        self.assertEqual(p.secrets, start_secrets + 2)
        self.assertEqual(p.glitched_shield_slots, 1)  # 2 - 1 = 1
        self.assertEqual(p.slots_cleaned_by_green_triage, 1)
        self.assertEqual(p.secret_yield_hist[sf._ckey(DieColor.GREEN)]["2"], 1)

        # Test banking another Green die when 1 glitched slot left -> goes to 0
        green_die_2 = create_colored_die(DieColor.GREEN, 202)
        sf.enter_processing_box(p, green_die_2, 1)
        banked_2 = sf.bank(cfg, p, green_die_2, engine.state)
        self.assertEqual(banked_2, 2)
        self.assertEqual(p.glitched_shield_slots, 0)
        self.assertEqual(p.slots_cleaned_by_green_triage, 2)

        # Test banking when already at 0 glitched slots -> cleans 0, still yields 2
        green_die_3 = create_colored_die(DieColor.GREEN, 203)
        sf.enter_processing_box(p, green_die_3, 1)
        banked_3 = sf.bank(cfg, p, green_die_3, engine.state)
        self.assertEqual(banked_3, 2)
        self.assertEqual(p.glitched_shield_slots, 0)
        self.assertEqual(p.slots_cleaned_by_green_triage, 2)

    def test_v380e_red_yield_and_mlb_flag(self):
        """INV-V38E-05: Red die banks exactly 2 Secrets and sets state.red_secret_banked_this_round = True."""
        engine = _engine_v038e()
        p = engine.state.players[0]
        cfg = engine.config

        red_die = create_colored_die(DieColor.RED, 301)
        sf.enter_processing_box(p, red_die, 1)

        engine.state.red_secret_banked_this_round = False
        start_secrets = p.secrets
        banked = sf.bank(cfg, p, red_die, engine.state)
        self.assertEqual(banked, 2)
        self.assertEqual(p.secrets, start_secrets + 2)
        self.assertTrue(engine.state.red_secret_banked_this_round)
        self.assertEqual(p.secret_yield_hist[sf._ckey(DieColor.RED)]["2"], 1)

    def test_v380e_purple_specialist_yield(self):
        """INV-V38E-06: Purple die banks exactly 1 Secret; zero board or track triggers."""
        engine = _engine_v038e()
        p = engine.state.players[0]
        cfg = engine.config

        purple_die = create_colored_die(DieColor.PURPLE, 401)
        sf.enter_processing_box(p, purple_die, 1)

        engine.state.red_secret_banked_this_round = False
        p.glitched_shield_slots = 2
        start_secrets = p.secrets
        banked = sf.bank(cfg, p, purple_die, engine.state)

        self.assertEqual(banked, 1)
        self.assertEqual(p.secrets, start_secrets + 1)
        self.assertFalse(engine.state.red_secret_banked_this_round)
        self.assertEqual(p.glitched_shield_slots, 2)
        self.assertEqual(p.secret_yield_hist[sf._ckey(DieColor.PURPLE)]["1"], 1)

    def test_v380e_stranded_and_burn_notice(self):
        """INV-V38E-07: Discarding pending die (Burn Notice) yields 0 secrets and cleans 0 slots."""
        engine = _engine_v038e()
        p = engine.state.players[0]
        cfg = engine.config

        green_die = create_colored_die(DieColor.GREEN, 501)
        sf.enter_processing_box(p, green_die, 1)
        p.glitched_shield_slots = 2
        start_secrets = p.secrets

        # Discard via lose_pending
        lost = sf.lose_pending(p, green_die)
        self.assertTrue(lost)
        self.assertFalse(green_die.secret_pending)
        self.assertEqual(p.secrets, start_secrets)
        self.assertEqual(p.glitched_shield_slots, 2)
        self.assertEqual(p.slots_cleaned_by_green_triage, 0)
        self.assertEqual(p.secrets_lost_returned, 1)

        # Calling bank() on non-pending die returns 0
        banked = sf.bank(cfg, p, green_die, engine.state)
        self.assertEqual(banked, 0)

    def test_v380e_backwards_compatibility(self):
        """INV-V38E-08: v038d config retains glitch penalty for Green and block bonus for Blue."""
        cfg_d = GameConfig.v038d(num_players=1)
        self.assertTrue(cfg_d.secret_yield_green_glitch_penalty)
        self.assertEqual(cfg_d.secret_yield_blue_base, 1)
        self.assertEqual(cfg_d.secret_yield_blue_block_bonus, 1)
        self.assertEqual(cfg_d.secret_yield_green_base, 3)

        engine_d = GameEngine(
            config=cfg_d,
            bots=[BaseBot(0)],
            seed=42,
            variant_cards=_cards(),
            version_deck=get_default_version_deck(),
            companies=[COMPANIES[CompanyCode.PROMETHEUS]],
            white_hats=[WHITE_HATS[WhiteHatCode.OPERATOR]],
        )
        p = engine_d.state.players[0]
        p.glitched_shield_slots = 1
        # Under v038d: Green yield = max(0, 3 - 1) = 2; with 2 slots = 1; with 3 slots = 0
        self.assertEqual(sf.secret_yield(cfg_d, p, DieColor.GREEN), 2)
        p.glitched_shield_slots = 2
        self.assertEqual(sf.secret_yield(cfg_d, p, DieColor.GREEN), 1)
        p.glitched_shield_slots = 3
        self.assertEqual(sf.secret_yield(cfg_d, p, DieColor.GREEN), 0)

        # Under v038d: Blue at L0 with blocked=0 is 1; with blocked=1 is 2
        p.defense_level = 0
        p.blocked_blue_this_round = 0
        self.assertEqual(sf.secret_yield(cfg_d, p, DieColor.BLUE), 1)
        p.blocked_blue_this_round = 1
        self.assertEqual(sf.secret_yield(cfg_d, p, DieColor.BLUE), 2)

    def test_v380e_bot_marginal_block_value(self):
        """Test bot marginal_block_value adjusts correctly under v038e vs v038d."""
        engine_e = _engine_v038e()
        p_e = engine_e.state.players[0]
        p_e.defense_capacity = 3
        p_e.glitched_shield_slots = 1

        # Blue marginal block value under v038e has no secret block bonus
        val_blue_e = sfp.marginal_block_value(
            CubeColor.BLUE, {CubeColor.BLUE: 1}, p_e, engine_e.state, {CubeColor.BLUE: 1}, base=2.0
        )
        self.assertEqual(val_blue_e, 2.0)

        # Green marginal block value under v038e is pure SHIELD_VALUE (glitch does not reduce secrets)
        val_green_e = sfp.marginal_block_value(
            CubeColor.GREEN, {CubeColor.GREEN: 1}, p_e, engine_e.state, {CubeColor.GREEN: 1}, base=0.0
        )
        self.assertEqual(val_green_e, sfp.SHIELD_VALUE)

        # Under v038d with a pending Green die, value includes secret valuation
        engine_d = GameEngine(
            config=GameConfig.v038d(num_players=1),
            bots=[BaseBot(0)],
            seed=42,
            variant_cards=_cards(),
            version_deck=get_default_version_deck(),
            companies=[COMPANIES[CompanyCode.PROMETHEUS]],
            white_hats=[WHITE_HATS[WhiteHatCode.OPERATOR]],
        )
        p_d = engine_d.state.players[0]
        p_d.defense_capacity = 3
        p_d.glitched_shield_slots = 1
        green_pending = create_colored_die(DieColor.GREEN, 601)
        sf.enter_processing_box(p_d, green_pending, 1)

        val_green_d = sfp.marginal_block_value(
            CubeColor.GREEN, {CubeColor.GREEN: 1}, p_d, engine_d.state, {CubeColor.GREEN: 1}, base=0.0
        )
        self.assertGreater(val_green_d, sfp.SHIELD_VALUE)

    def test_v380e_conveyor_triage_flow(self):
        """Phase 5 Conveyor Triage moves dice from Processing Box to Scanned Box, banking correctly."""
        engine = _engine_v038e(n=2)
        p = engine.state.players[0]
        p.triage_bandwidth = 2
        p.glitched_shield_slots = 2
        p.defense_level = 3  # Level 3

        # Add 1 Red, 1 Blue, 1 Green to Processing Box
        d_red = create_colored_die(DieColor.RED, 701)
        d_blue = create_colored_die(DieColor.BLUE, 702)
        d_green = create_colored_die(DieColor.GREEN, 703)

        sf.enter_processing_box(p, d_red, 1)
        sf.enter_processing_box(p, d_blue, 1)
        sf.enter_processing_box(p, d_green, 1)

        start_secrets = p.secrets
        # Bandwidth 2: oldest first -> d_red (entry 1) and d_blue (entry 2) leave
        p5.conveyor_triage_v038(engine, p)

        self.assertNotIn(d_red, p.glitched_dice)
        self.assertNotIn(d_blue, p.glitched_dice)
        self.assertIn(d_green, p.glitched_dice)  # Stranded/pending

        # Red yields 2, Blue at L3 yields 3 -> total 5 secrets
        self.assertEqual(p.secrets - start_secrets, 5)
        self.assertTrue(engine.state.red_secret_banked_this_round)

        # In round 2 triage: d_green leaves
        p5.conveyor_triage_v038(engine, p)
        self.assertNotIn(d_green, p.glitched_dice)
        self.assertEqual(p.secrets - start_secrets, 7)  # +2 from Green
        self.assertEqual(p.glitched_shield_slots, 1)  # 2 - 1 = 1


if __name__ == "__main__":
    unittest.main()
