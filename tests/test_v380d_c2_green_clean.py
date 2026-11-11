"""v0.38d Candidate C2 + Green-Clean Package (Variant B) Test Suite.

Validates invariants INV-V38D-01 through INV-V38D-08 per docs/specs/v380d_c2_green_clean_spec.md:
- INV-V38D-01: C2 Compiler Priming (4 cubes: 1R, 1B, 1G, 1K) & Staging Cup payload (4 cubes)
- INV-V38D-02: C2 Starting Glitched Shield Slot (1 per player)
- INV-V38D-03: Elimination of Passive Graduation Auto-Clean (slot_graduation_clear = 0)
- INV-V38D-04: Green Face 1 Profile V038D (+2 🔬, clean_slots=0) & G1 intact
- INV-V38D-05: Variant B Green Banking Slot Clean (Count yield then Clean 1 slot)
- INV-V38D-06: Stranded & Return Non-Banking Integrity (zero yield, zero clean)
- INV-V38D-07: Telemetry & Ledger Completeness (slots_cleaned_by_green_triage, cloner, end game)
- INV-V38D-08: Backwards Parity Preservation (v038c, v038b, v038, v037)
"""

from __future__ import annotations

import unittest

from sim.config import CubeColor, DieColor, GameConfig, ShieldColor, TowerMode
from sim.engine import GameEngine, fast_clone, secret_faces as sf
from sim.engine import phase3_income as p3, phase5_pipeline_shift as p5
from sim.engine.end_game import evaluate_end_game
from sim.bots.base import BaseBot
from sim.entities import (
    COMPANIES, CompanyCode, Face, WHITE_HATS, WhiteHatCode,
    create_colored_die, create_gray_die, get_all_variant_cards, get_all_version_cards,
    get_default_version_deck, apply_variant_profile,
    V038D_V1_STAGING_PAYLOAD, CLEAN_SLOT_NAME,
)

ALL_CARDS = get_all_variant_cards("MARKETING")


def _cards(**codes):
    out = {
        DieColor.RED: ALL_CARDS["R1"],
        DieColor.BLUE: ALL_CARDS["B1"],
        DieColor.GREEN: ALL_CARDS["G1"],
        DieColor.YELLOW: ALL_CARDS["Y1"],
    }
    for k, v in codes.items():
        out[DieColor(k)] = ALL_CARDS[v]
    return out


def _engine_v038d(n=3, seed=1, v1_card=None, cards=None, **cfg_overrides):
    bots = [BaseBot(i) for i in range(n)]
    companies = [COMPANIES[CompanyCode.PROMETHEUS], COMPANIES[CompanyCode.MERIDIAN], COMPANIES[CompanyCode.DTO]][:n]
    white_hats = [WHITE_HATS[WhiteHatCode.OPERATOR], WHITE_HATS[WhiteHatCode.ACOUSTIC], WHITE_HATS[WhiteHatCode.SPOOK]][:n]
    deck = get_default_version_deck()
    if v1_card is not None:
        deck = [v1_card] + list(deck[1:])
    cfg = GameConfig.v038d(num_players=n, **cfg_overrides)
    return GameEngine(
        config=cfg,
        bots=bots,
        seed=seed,
        variant_cards=cards or _cards(),
        version_deck=deck,
        companies=companies,
        white_hats=white_hats,
    )


class TestV038dC2GreenClean(unittest.TestCase):
    """Candidate C2 + Green-Clean Package (Variant B) test suite."""

    def test_v038d_config_preset(self):
        """Spec §4.2 item 1: GameConfig.v038d preset and validation."""
        cfg = GameConfig.v038d()
        self.assertEqual(cfg.starting_glitched_shield_slots, 1)
        self.assertEqual(cfg.slot_graduation_clear, 0)
        self.assertEqual(cfg.green_triage_clean_mode, "COUNT_THEN_CLEAN")
        self.assertTrue(cfg.green_bank_cleans_slot)
        self.assertEqual(cfg.die_face_profile, "V038D")
        self.assertEqual(cfg.tower_mode, TowerMode.SHOGUN_BAFFLE)
        self.assertEqual(cfg.red_secret_owner_yield, 2)
        self.assertIsNotNone(cfg.v1_staging_payload_override)
        self.assertEqual(cfg.v1_staging_payload_override, V038D_V1_STAGING_PAYLOAD)

        # Validation checks
        with self.assertRaises(ValueError):
            GameConfig(green_triage_clean_mode="INVALID_MODE")
        with self.assertRaises(ValueError):
            GameConfig(starting_glitched_shield_slots=-1)

    def test_c2_setup_staging_cup_and_priming(self):
        """INV-V38D-01 / Spec §4.2 item 2: 4-cube staging cup and 4-cube priming drop."""
        all_v1 = [c for c in get_all_version_cards() if c.version_str == "v1.0"]
        script_kiddie = next(c for c in all_v1 if c.directive_code == "SCRIPT_KIDDIE")
        data_scraper = next(c for c in all_v1 if c.directive_code == "DATA_SCRAPER")

        # 1. Script Kiddie starting staging cup: 2R, 1B, 1G, 0K (total 4 cubes)
        eng_sk = _engine_v038d(n=3, seed=42, v1_card=script_kiddie)
        self.assertEqual(eng_sk.state.staging_cup[CubeColor.RED], 2)
        self.assertEqual(eng_sk.state.staging_cup[CubeColor.BLUE], 1)
        self.assertEqual(eng_sk.state.staging_cup[CubeColor.GREEN], 1)
        self.assertEqual(eng_sk.state.staging_cup[CubeColor.BLACK], 0)
        total_sk = sum(eng_sk.state.staging_cup.values())
        self.assertEqual(total_sk, 4)

        # 2. Data Scraper starting staging cup: 1R, 2B, 1G, 0K (total 4 cubes)
        eng_ds = _engine_v038d(n=3, seed=42, v1_card=data_scraper)
        self.assertEqual(eng_ds.state.staging_cup[CubeColor.RED], 1)
        self.assertEqual(eng_ds.state.staging_cup[CubeColor.BLUE], 2)
        self.assertEqual(eng_ds.state.staging_cup[CubeColor.GREEN], 1)
        self.assertEqual(eng_ds.state.staging_cup[CubeColor.BLACK], 0)
        total_ds = sum(eng_ds.state.staging_cup.values())
        self.assertEqual(total_ds, 4)

        # 3. Compiler priming drops exactly 4 cubes: 1R, 1B, 1G, 1K
        exited = eng_sk.state.priming_exited_cubes
        stuck = eng_sk.state.priming_stuck_cubes
        total_primed = {c: exited.get(c, 0) + stuck.get(c, 0) for c in (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN, CubeColor.BLACK)}
        self.assertEqual(total_primed, {CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 1, CubeColor.BLACK: 1})

    def test_c2_starting_glitched_shield_slots(self):
        """INV-V38D-02 / Spec §4.2 item 3: Every player starts with 1 Glitched Shield Slot."""
        eng = _engine_v038d(n=3, seed=123)
        for p in eng.state.players:
            self.assertEqual(p.glitched_shield_slots, 1)
            self.assertEqual(p.max_glitched_slots, 1)
            self.assertEqual(p.slots_glitched_by_source.get("setup"), 1)
            # Baseline defense capacity is 2; 1 glitched slot leaves 1 clean shield slot
            self.assertEqual(sf.effective_capacity(p), 1)

    def test_green_face_1_profile_v038d(self):
        """INV-V38D-04 / Spec §4.2 item 4: Green F1 is unconditional +2 🔬; G1 intact."""
        green_die = create_colored_die(color=DieColor.GREEN, die_id=1, face_profile="V038D")
        f1 = green_die.faces[0]
        self.assertEqual(f1.name, "+2 🔬")
        self.assertEqual(f1.patches, 2)
        self.assertEqual(f1.clean_slots, 0)
        self.assertEqual(f1.money, 0)
        self.assertFalse(f1.is_choice)

        # Yellow die under V038D retains F3 = +$1 & +1 Market Share
        yellow_die = create_colored_die(color=DieColor.YELLOW, die_id=2, face_profile="V038D")
        f3 = yellow_die.faces[2]
        self.assertEqual(f3.name, "+$1 & +1 Market Share")
        self.assertEqual(f3.money, 1)
        self.assertEqual(f3.market_share, 1)

        # G1 Self-Healing Kernel star face under V038 retains clean_slots == 1, patches == 1
        cards_v038 = apply_variant_profile({DieColor.GREEN: ALL_CARDS["G1"]}, "V038_DRAFT")
        g1_card = cards_v038[DieColor.GREEN]
        self.assertEqual(g1_card.star_face.clean_slots, 1)
        self.assertEqual(g1_card.star_face.patches, 1)

    def test_no_graduation_auto_clean(self):
        """INV-V38D-03 / Spec §4.2 item 5: slot_graduation_clear = 0 cleans zero slots."""
        eng = _engine_v038d(n=2, seed=1)
        p = eng.state.players[0]
        p.glitched_shield_slots = 1
        d = create_gray_die(die_id=101)
        p.scanned_dice = [d]
        p.ready_for_release_dice = []

        # Execute Phase 5 pipeline shift
        p5.execute_pipeline_shift(eng)

        # Die graduated from Scanned to Ready for Release
        self.assertIn(d, p.ready_for_release_dice)
        self.assertEqual(len(p.scanned_dice), 0)

        # Glitched slot is NOT cleaned by graduation
        self.assertEqual(p.glitched_shield_slots, 1)
        self.assertEqual(p.slots_cleared_by_graduation, 0)
        self.assertFalse(p.slot_clear_used_this_phase5)

    def test_green_triage_banking_variant_b_timing(self):
        """INV-V38D-05 / Spec §4.2 item 6: Variant B Count-Then-Clean timing verification."""
        cfg = GameConfig.v038d(num_players=2)

        # Case A: g = 1 -> yield = max(0, 3 - 1) = 2, then g becomes 0
        eng = _engine_v038d(n=2)
        p = eng.state.players[0]
        p.glitched_shield_slots = 1
        p.secrets = 0
        g_die = create_colored_die(color=DieColor.GREEN, die_id=201, face_profile="V038D")
        sf.enter_processing_box(p, g_die, round_no=1)
        p.glitched_dice.remove(g_die)
        awarded = sf.bank(cfg, p, g_die, eng.state)

        self.assertEqual(awarded, 2)
        self.assertEqual(p.secrets, 2)
        self.assertEqual(p.glitched_shield_slots, 0)
        self.assertEqual(p.slots_cleaned_by_green_triage, 1)

        # Case B: g = 0 -> yield = max(0, 3 - 0) = 3, g stays 0
        p.glitched_shield_slots = 0
        p.secrets = 0
        g_die2 = create_colored_die(color=DieColor.GREEN, die_id=202, face_profile="V038D")
        sf.enter_processing_box(p, g_die2, round_no=1)
        p.glitched_dice.remove(g_die2)
        awarded2 = sf.bank(cfg, p, g_die2, eng.state)

        self.assertEqual(awarded2, 3)
        self.assertEqual(p.secrets, 3)
        self.assertEqual(p.glitched_shield_slots, 0)
        self.assertEqual(p.slots_cleaned_by_green_triage, 1)  # unchanged from before

        # Case C: g = 2 -> yield = max(0, 3 - 2) = 1, then g becomes 1
        p.glitched_shield_slots = 2
        p.secrets = 0
        g_die3 = create_colored_die(color=DieColor.GREEN, die_id=203, face_profile="V038D")
        sf.enter_processing_box(p, g_die3, round_no=1)
        p.glitched_dice.remove(g_die3)
        awarded3 = sf.bank(cfg, p, g_die3, eng.state)

        self.assertEqual(awarded3, 1)
        self.assertEqual(p.secrets, 1)
        self.assertEqual(p.glitched_shield_slots, 1)
        self.assertEqual(p.slots_cleaned_by_green_triage, 2)

        # Case D: g = 3 -> yield = max(0, 3 - 3) = 0, then g becomes 2
        p.glitched_shield_slots = 3
        p.secrets = 0
        g_die4 = create_colored_die(color=DieColor.GREEN, die_id=204, face_profile="V038D")
        sf.enter_processing_box(p, g_die4, round_no=1)
        p.glitched_dice.remove(g_die4)
        awarded4 = sf.bank(cfg, p, g_die4, eng.state)

        self.assertEqual(awarded4, 0)
        self.assertEqual(p.secrets, 0)
        self.assertEqual(p.glitched_shield_slots, 2)
        self.assertEqual(p.slots_cleaned_by_green_triage, 3)

        # Variant A comparison mode (CLEAN_THEN_COUNT)
        cfg_var_a = GameConfig.v038d(green_triage_clean_mode="CLEAN_THEN_COUNT")
        p.glitched_shield_slots = 1
        p.secrets = 0
        g_die_a = create_colored_die(color=DieColor.GREEN, die_id=205, face_profile="V038D")
        sf.enter_processing_box(p, g_die_a, round_no=1)
        p.glitched_dice.remove(g_die_a)
        awarded_a = sf.bank(cfg_var_a, p, g_die_a, eng.state)
        # Variant A: cleans first (g: 1 -> 0), then counts yield: max(0, 3 - 0) = 3
        self.assertEqual(awarded_a, 3)
        self.assertEqual(p.glitched_shield_slots, 0)

    def test_green_triage_exit_routes(self):
        """INV-V38D-05 / Spec §4.2 item 7: All 4 exit routes clean a slot and yield properly."""
        # Route 1: Phase 5 Conveyor Triage
        eng1 = _engine_v038d(n=2, seed=10)
        p1_state = eng1.state.players[0]
        p1_state.glitched_shield_slots = 1
        p1_state.secrets = 0
        g1 = create_colored_die(color=DieColor.GREEN, die_id=301, face_profile="V038D")
        sf.enter_processing_box(p1_state, g1, round_no=1)
        self.assertIn(g1, p1_state.glitched_dice)

        triaged = p5.conveyor_triage_v038(eng1, p1_state)
        self.assertIn(g1, triaged)
        self.assertIn(g1, p1_state.scanned_dice)
        self.assertEqual(p1_state.secrets, 2)
        self.assertEqual(p1_state.glitched_shield_slots, 0)
        self.assertEqual(p1_state.slots_cleaned_by_green_triage, 1)

        # Route 2: Phase 3 B3 Air-Gapped Backup
        b3_variants = apply_variant_profile(_cards(blue="B3"), "V038_DRAFT")
        eng2 = _engine_v038d(n=2, seed=20, cards=b3_variants)
        p2_state = eng2.state.players[0]
        p2_state.glitched_shield_slots = 1
        p2_state.secrets = 0
        g2 = create_colored_die(color=DieColor.GREEN, die_id=302, face_profile="V038D")
        sf.enter_processing_box(p2_state, g2, round_no=1)

        # Deploy Blue B3 die In Production showing B3 star face
        b3_die = create_colored_die(color=DieColor.BLUE, die_id=303, variant_card=b3_variants[DieColor.BLUE], face_profile="V038D")
        b3_die.current_face = b3_variants[DieColor.BLUE].star_face
        p2_state.in_production_dice = [b3_die]

        p3.execute_player_income(eng2, p2_state)
        self.assertIn(g2, p2_state.scanned_dice)
        self.assertEqual(p2_state.secrets, 2)
        self.assertEqual(p2_state.glitched_shield_slots, 0)
        self.assertEqual(p2_state.slots_cleaned_by_green_triage, 1)

        # Route 3: Phase 3 Jumper Diagnostics (Phreaker)
        eng3 = _engine_v038d(n=2, seed=30)
        p3_state = eng3.state.players[0]
        p3_state.white_hat = WHITE_HATS[WhiteHatCode.PHREAKER]
        p3_state.glitched_shield_slots = 1
        p3_state.secrets = 0
        g3 = create_colored_die(color=DieColor.GREEN, die_id=304, face_profile="V038D")
        sf.enter_processing_box(p3_state, g3, round_no=1)

        # Purple ★ In Production triggers Jumper Diagnostics
        purple_die = create_colored_die(color=DieColor.PURPLE, die_id=305, face_profile="V038D")
        star_face = next(f for f in purple_die.faces if f.is_star and f.star_code == "PURPLE_STAR")
        purple_die.current_face = star_face
        p3_state.in_production_dice = [purple_die]

        p3.execute_player_income(eng3, p3_state, phreaker_die_id=g3.die_id)
        self.assertIn(g3, p3_state.scanned_dice)
        self.assertEqual(p3_state.secrets, 2)
        self.assertEqual(p3_state.glitched_shield_slots, 0)
        self.assertEqual(p3_state.slots_cleaned_by_green_triage, 1)

        # Route 4: Phase 5 Magnetic Splice (Omnidyne)
        eng4 = _engine_v038d(n=2, seed=40)
        p4_state = eng4.state.players[0]
        p4_state.company = COMPANIES[CompanyCode.OMNIDYNE]
        p4_state.glitched_shield_slots = 1
        p4_state.secrets = 0
        g4 = create_colored_die(color=DieColor.GREEN, die_id=306, face_profile="V038D")
        sf.enter_processing_box(p4_state, g4, round_no=1)

        p5.execute_player_pipeline_shift(eng4, p4_state, splice_die_id=g4.die_id)
        self.assertIn(g4, p4_state.ready_for_release_dice)
        self.assertEqual(p4_state.secrets, 2)
        self.assertEqual(p4_state.glitched_shield_slots, 0)
        self.assertEqual(p4_state.slots_cleaned_by_green_triage, 1)

    def test_green_stranded_and_burn_notice_no_clean(self):
        """INV-V38D-06 / Spec §4.2 item 8: Stranded & Burn Notice do not clean slots or bank secrets."""
        eng = _engine_v038d(n=2, seed=50)
        p = eng.state.players[0]
        p.glitched_shield_slots = 1
        p.secrets = 0
        g_die = create_colored_die(color=DieColor.GREEN, die_id=401, face_profile="V038D")
        sf.enter_processing_box(p, g_die, round_no=1)

        # Lose pending via sf.lose_pending()
        self.assertTrue(sf.lose_pending(p, g_die))
        self.assertEqual(p.secrets, 0)
        self.assertEqual(p.glitched_shield_slots, 1)
        self.assertEqual(p.slots_cleaned_by_green_triage, 0)
        self.assertEqual(p.secrets_lost_returned, 1)

        # Spook Burn Notice in Phase 3
        p.white_hat = WHITE_HATS[WhiteHatCode.SPOOK]
        g_die2 = create_colored_die(color=DieColor.GREEN, die_id=402, face_profile="V038D")
        sf.enter_processing_box(p, g_die2, round_no=1)

        purple_die = create_colored_die(color=DieColor.PURPLE, die_id=403, face_profile="V038D")
        star_face = next(f for f in purple_die.faces if f.is_star and f.star_code == "PURPLE_STAR")
        purple_die.current_face = star_face
        p.in_production_dice = [purple_die]

        p3.execute_player_income(eng, p, spook_burn_die_id=g_die2.die_id)
        self.assertNotIn(g_die2, p.glitched_dice)
        # Burn Notice grants +1 Secret for trashing the die itself, but zero Secret face banking yield
        self.assertEqual(p.secrets_by_source.get("secret_face_green", 0), 0)
        self.assertEqual(p.secret_faces_banked.get("green", 0), 0)
        self.assertEqual(p.glitched_shield_slots, 1)
        self.assertEqual(p.slots_cleaned_by_green_triage, 0)

    def test_v038c_backwards_parity_preserved(self):
        """INV-V38D-08 / Spec §4.2 item 9: v038c maintains exact baseline configuration and behavior."""
        cfg_c = GameConfig.v038c(num_players=2)
        self.assertEqual(cfg_c.starting_glitched_shield_slots, 0)
        self.assertEqual(cfg_c.slot_graduation_clear, 1)
        self.assertEqual(cfg_c.green_triage_clean_mode, "NONE")
        self.assertFalse(cfg_c.green_bank_cleans_slot)
        self.assertIsNone(cfg_c.v1_staging_payload_override)
        self.assertEqual(cfg_c.die_face_profile, "V038_YELLOW_MS_F3")

        # Green die under V038_YELLOW_MS_F3 (or V038_DRAFT) has Clean/Cash split F1
        g_die_c = create_colored_die(color=DieColor.GREEN, die_id=501, face_profile=cfg_c.die_face_profile)
        f1 = g_die_c.faces[0]
        self.assertTrue(f1.is_choice)
        choice_names = [c.name for c in f1.choices]
        self.assertIn(CLEAN_SLOT_NAME, choice_names)
        self.assertIn("+$1", choice_names)

        # Staging cup under v038c uses default VersionCard payload (3 cubes for Script Kiddie)
        deck = get_default_version_deck()
        script_kiddie = next(c for c in deck if c.directive_code == "SCRIPT_KIDDIE")
        eng_c = GameEngine(
            config=cfg_c,
            bots=[BaseBot(0), BaseBot(1)],
            seed=42,
            variant_cards=_cards(),
            version_deck=[script_kiddie] + list(deck[1:]),
            companies=[COMPANIES[CompanyCode.PROMETHEUS], COMPANIES[CompanyCode.MERIDIAN]],
            white_hats=[WHITE_HATS[WhiteHatCode.OPERATOR], WHITE_HATS[WhiteHatCode.ACOUSTIC]],
        )
        self.assertEqual(eng_c.state.staging_cup[CubeColor.RED], 1)
        self.assertEqual(eng_c.state.staging_cup[CubeColor.BLUE], 1)
        self.assertEqual(eng_c.state.staging_cup[CubeColor.GREEN], 1)
        self.assertEqual(eng_c.state.staging_cup[CubeColor.BLACK], 0)
        self.assertEqual(sum(eng_c.state.staging_cup.values()), 3)

        # Starting glitched slots is 0
        for p in eng_c.state.players:
            self.assertEqual(p.glitched_shield_slots, 0)

    def test_telemetry_and_fast_clone(self):
        """INV-V38D-07: Telemetry export and fast_clone preservation of slots_cleaned_by_green_triage."""
        eng = _engine_v038d(n=2, seed=60)
        p = eng.state.players[0]
        p.slots_cleaned_by_green_triage = 3

        # Clone engine
        clone, _ = fast_clone.clone_engine(eng)
        p_clone = clone.state.players[0]
        self.assertEqual(p_clone.slots_cleaned_by_green_triage, 3)

        # Mutating clone does not mutate original
        p_clone.slots_cleaned_by_green_triage += 1
        self.assertEqual(p.slots_cleaned_by_green_triage, 3)
        self.assertEqual(p_clone.slots_cleaned_by_green_triage, 4)

        # End-game telemetry export
        res = evaluate_end_game(eng)
        row = next(r for r in res.rankings if r["player_id"] == p.player_id)
        self.assertEqual(row.get("slots_cleaned_by_green_triage"), 3)


if __name__ == "__main__":
    unittest.main()
