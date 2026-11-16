"""v0.44.0 Colored Die F6 (★) Variant Card Overhaul & Glitched Shield Slot Flow tests.

Covers all 9 invariant tests specified in docs/specs/f6_variant_overhaul_spec.md §7.
"""

from __future__ import annotations

import unittest

from sim.bots.base import BaseBot
from sim.config import CubeColor, DieColor, EndGameReason, GameConfig, ShieldColor
from sim.engine.core import GameEngine
from sim.engine.phase2_compiler import CompileResult
from sim.engine.phase3_income import execute_income, execute_player_income
from sim.engine.phase4_attack_resolution import execute_attack_resolution
from sim.engine.phase6_operations import execute_player_operations_turn
from sim.engine.state import ProductionRole
from sim.entities import Face, create_colored_die, create_gray_die, get_v044_variant_cards


def _v044_engine(num_players: int = 2, seed: int = 42, **cfg_kw) -> GameEngine:
    isolate = cfg_kw.pop("isolate", True)
    cfg = GameConfig.v044(num_players=num_players, **cfg_kw)
    bots = [BaseBot(i) for i in range(num_players)]
    v_by_code = {c.code: c for c in get_v044_variant_cards()}
    vcards = {
        DieColor.RED: v_by_code["R1"],
        DieColor.BLUE: v_by_code["B1"],
        DieColor.GREEN: v_by_code["G1"],
        DieColor.YELLOW: v_by_code["Y1"],
    }
    eng = GameEngine(cfg, bots, seed=seed, variant_cards=vcards)
    if isolate:
        for p in eng.state.players:
            p.company = None
            p.white_hat = None
    return eng


def _compile_result(exited: dict) -> CompileResult:
    return CompileResult(
        staged_before=dict(exited),
        stuck_before={},
        exited_cubes=dict(exited),
        stuck_after={},
    )


def _star_die(die_id: int, color: DieColor, code: str) -> object:
    v_by_code = {c.code: c for c in get_v044_variant_cards()}
    card = v_by_code[code]
    d = create_colored_die(
        face_profile="V038_DRAFT",
        color=color,
        die_id=die_id,
        variant_card=card,
    )
    d.current_face = card.star_face
    d.production_role = ProductionRole.INCOME
    return d


class TestF6VariantOverhaul(unittest.TestCase):
    """Invariant tests 1-9 from docs/specs/f6_variant_overhaul_spec.md §7."""

    def test_v044_variant_card_costs(self) -> None:
        cards = {c.code: c for c in get_v044_variant_cards()}
        self.assertEqual(len(cards), 12)
        self.assertEqual(cards["B2"].cost, 5)
        self.assertEqual(cards["G2"].cost, 5)
        self.assertEqual(cards["R2"].cost, 4)
        self.assertEqual(cards["Y1"].cost, 6)

    def test_inv_f6_b3_shields(self) -> None:
        """TC-1: B3 counts ALL shields In Production (clean + glitched) -> +$1 base + $1 per shield."""
        eng = _v044_engine()
        p0 = eng.state.players[0]
        p0.money = 0
        p0.defense_level = 0
        p0.glitched_shield_slots = 1

        s_clean = create_gray_die(101)
        s_clean.current_face = Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)
        s_clean.production_role = ProductionRole.CLEAN_SHIELD

        s_purge = create_gray_die(102)
        s_purge.current_face = Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)
        s_purge.production_role = ProductionRole.PURGING_SHIELD

        b3_die = _star_die(103, DieColor.BLUE, "B3")
        p0.in_production_dice = [s_clean, s_purge, b3_die]

        execute_player_income(eng, p0)
        self.assertEqual(p0.money, 3)

    def test_inv_f6_b2_secrets_suicide_breach(self) -> None:
        """TC-2: B2 spend at 1 Secret -> immediate Patient Zero in Phase 3 & skipped in Phase 4."""
        eng = _v044_engine(num_players=2)
        p0, p1 = eng.state.players[0], eng.state.players[1]
        p0.secrets = 1
        p0.market_share = 10
        p0.bot.choose_b2_vault_mode = lambda player, state: "market_share"

        b2_die = _star_die(201, DieColor.BLUE, "B2")
        p0.in_production_dice = [b2_die]
        p1.in_production_dice = []

        execute_income(eng)

        self.assertEqual(p0.secrets, 0)
        self.assertEqual(p0.market_share, 13)
        self.assertTrue(p0.is_patient_zero)
        self.assertEqual(p0.elimination_reason, "Total Breach (<= 0 Secrets)")
        self.assertTrue(eng.state.is_final_round)
        self.assertEqual(eng.state.end_reason, EndGameReason.PATIENT_ZERO)
        self.assertEqual(eng.state.final_round_trigger_phase, 3)

        # Phase 4: Patient Zero player is skipped
        p0_ms_before = p0.market_share
        cr = _compile_result(
            {CubeColor.RED: 2, CubeColor.BLUE: 1, CubeColor.GREEN: 0, CubeColor.BLACK: 0},
        )
        commitments = [(p0, list(p0.in_production_dice), {}), (p1, list(p1.in_production_dice), {})]
        execute_attack_resolution(eng, commitments, cr)
        self.assertEqual(p0.market_share, p0_ms_before)

    def test_inv_f6_g3_empty_scanned_box(self) -> None:
        """TC-3: G3 with empty Scanned Box grants +1 🔬, +$1 Cash, and fizzles cleanly."""
        eng = _v044_engine()
        p0 = eng.state.players[0]
        p0.money = 0
        p0.research_tokens = 0
        p0.scanned_dice = []

        g3_die = _star_die(301, DieColor.GREEN, "G3")
        p0.in_production_dice = [g3_die]

        execute_player_income(eng, p0)
        self.assertEqual(p0.research_tokens, 1)
        self.assertEqual(p0.money, 1)
        self.assertEqual(p0.f6_g3_fizzles, 1)

    def test_inv_slot_purge_and_defense_l4_exclusion(self) -> None:
        """TC-4: Purging shield cleans glitched slot -> Scanned Box, does NOT block or earn Defense L4 cash."""
        eng = _v044_engine()
        p0 = eng.state.players[0]
        p0.money = 0
        p0.defense_level = 4  # Defense Grid L4: +$1 per cube blocked
        p0.glitched_shield_slots = 1
        p0.shields_on_clean_slots = 1
        p0.shields_on_glitched_slots = 1
        p0.scanned_dice = []

        s_clean = create_gray_die(401)
        s_clean.current_face = Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)
        s_clean.production_role = ProductionRole.CLEAN_SHIELD

        s_purge = create_gray_die(402)
        s_purge.current_face = Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)
        s_purge.production_role = ProductionRole.PURGING_SHIELD

        p0.in_production_dice = [s_clean, s_purge]
        commitments = [
            (p0, [s_clean, s_purge], {0: ShieldColor.ANY, 1: ShieldColor.ANY}),
            (eng.state.players[1], [], {}),
        ]
        cr = _compile_result(
            {CubeColor.RED: 1, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0},
        )
        execute_attack_resolution(eng, commitments, cr)

        self.assertIn(s_purge, p0.scanned_dice)
        self.assertEqual(p0.glitched_shield_slots, 0)
        self.assertEqual(p0.money, 1)  # Only $1 from clean shield, NOT $2

    def test_g1_phase3_timing_and_shield_promotion(self) -> None:
        """TC-5: G1 cleans 1 glitched slot in Phase 3 and promotes assigned PURGING_SHIELD to CLEAN_SHIELD."""
        eng = _v044_engine()
        p0 = eng.state.players[0]
        p0.secrets = 5
        p0.glitched_shield_slots = 1
        p0.shields_on_clean_slots = 0
        p0.shields_on_glitched_slots = 1

        s_purge = create_gray_die(501)
        s_purge.current_face = Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)
        s_purge.production_role = ProductionRole.PURGING_SHIELD

        g1_die = _star_die(502, DieColor.GREEN, "G1")
        p0.in_production_dice = [s_purge, g1_die]

        execute_player_income(eng, p0)

        self.assertEqual(p0.glitched_shield_slots, 0)
        self.assertEqual(s_purge.production_role, ProductionRole.CLEAN_SHIELD)
        self.assertEqual(p0.shields_on_clean_slots, 1)
        self.assertEqual(p0.shields_on_glitched_slots, 0)

        # Phase 4 follow-through: promoted shield blocks 1 Blue cube
        cr = _compile_result(
            {CubeColor.RED: 0, CubeColor.BLUE: 1, CubeColor.GREEN: 0, CubeColor.BLACK: 0},
        )
        commitments = [
            (p0, [s_purge, g1_die], {0: ShieldColor.ANY}),
            (eng.state.players[1], [], {}),
        ]
        execute_attack_resolution(eng, commitments, cr)
        self.assertEqual(p0.secrets, 5)  # Blue cube blocked!

    def test_r2_ad_campaign_phase3_resolution(self) -> None:
        """TC-6: R2 resolves in Phase 3 (-$2 -> +2 MS) and leaves zero R2 actions in Phase 6."""
        eng = _v044_engine()
        p0 = eng.state.players[0]
        p0.money = 3
        p0.market_share = 10
        p0.bot.choose_r2_ad_campaign = lambda player, state: True

        r2_die = _star_die(601, DieColor.RED, "R2")
        p0.in_production_dice = [r2_die]

        execute_player_income(eng, p0)
        self.assertEqual(p0.money, 1)
        self.assertEqual(p0.market_share, 12)
        self.assertEqual(p0.r2_actions_available, 0)

        # Phase 6 Operations: no R2 action exists
        from sim.bots.base import Phase3ActionPlan

        plan = Phase3ActionPlan(use_r2_share=1)
        execute_player_operations_turn(eng, p0, plan)
        self.assertEqual(p0.r2_actions_available, 0)
        self.assertEqual(p0.market_share, 12)

    def test_y1_algorithmic_trading_modal(self) -> None:
        """TC-7: Y1 modal Cash (+$4), Secret (-$2 -> +1 Secret), and forced Cash when money < $2."""
        # Path A: Cash
        eng_a = _v044_engine()
        p0 = eng_a.state.players[0]
        p0.money = 2
        p0.bot.choose_y1_algo_mode = lambda player, state: "cash"
        p0.in_production_dice = [_star_die(701, DieColor.YELLOW, "Y1")]
        execute_player_income(eng_a, p0)
        self.assertEqual(p0.money, 6)

        # Path B: Secret
        eng_b = _v044_engine()
        p0_b = eng_b.state.players[0]
        p0_b.money = 2
        p0_b.secrets = 5
        p0_b.bot.choose_y1_algo_mode = lambda player, state: "secret"
        p0_b.in_production_dice = [_star_die(702, DieColor.YELLOW, "Y1")]
        execute_player_income(eng_b, p0_b)
        self.assertEqual(p0_b.money, 0)
        self.assertEqual(p0_b.secrets, 6)

        # Path C: Forced Cash when money < $2
        eng_c = _v044_engine()
        p0_c = eng_c.state.players[0]
        p0_c.money = 1
        p0_c.secrets = 5
        p0_c.bot.choose_y1_algo_mode = lambda player, state: "secret"  # tries secret, forced to cash
        p0_c.in_production_dice = [_star_die(703, DieColor.YELLOW, "Y1")]
        execute_player_income(eng_c, p0_c)
        self.assertEqual(p0_c.money, 5)
        self.assertEqual(p0_c.secrets, 5)

    def test_y2_and_y3_color_and_gray_scaling(self) -> None:
        """TC-8: Y2 counts CM colors (excludes Gray/Purple); Y3 grants +1 Secret + $1/Gray & stays In Production."""
        eng = _v044_engine()
        p0 = eng.state.players[0]
        p0.money = 0
        p0.secrets = 5

        r_die = create_colored_die(face_profile="V038_DRAFT", color=DieColor.RED, die_id=801)
        b_die = create_colored_die(face_profile="V038_DRAFT", color=DieColor.BLUE, die_id=802)
        g_die = create_colored_die(face_profile="V038_DRAFT", color=DieColor.GREEN, die_id=803)
        p_die = create_colored_die(face_profile="V038_DRAFT", color=DieColor.PURPLE, die_id=804)
        gray1 = create_gray_die(805)
        gray2 = create_gray_die(806)
        y2_die = _star_die(807, DieColor.YELLOW, "Y2")

        p0.ready_for_release_dice = [r_die, b_die, g_die, p_die, gray1, gray2]
        p0.glitched_dice = []
        p0.scanned_dice = []
        p0.in_production_dice = [y2_die]

        # Note: Y2 die itself is Yellow (4th CM color). To test 3 CM colors, use only Red, Blue, Green in pool
        # or check 4 CM colors = $2 + $4 = $6. Let's test exact TC-8 setup: 3 CM colors + Y2 in another test or
        # replace Y2's color check by testing Y2 with Red, Blue, Yellow (= 3 CM colors).
        p0.ready_for_release_dice = [r_die, b_die, p_die, gray1]
        execute_player_income(eng, p0)
        # CM colors owned: Red, Blue, Yellow = 3 -> $2 + $3 = $5
        self.assertEqual(p0.money, 5)

        # Now test Y3 with 2 Gray Legacy dice
        eng2 = _v044_engine()
        p0_2 = eng2.state.players[0]
        p0_2.money = 0
        p0_2.secrets = 5
        y3_die = _star_die(810, DieColor.YELLOW, "Y3")
        p0_2.ready_for_release_dice = [create_gray_die(811), create_gray_die(812)]
        p0_2.glitched_dice = []
        p0_2.scanned_dice = []
        p0_2.in_production_dice = [y3_die]

        execute_player_income(eng2, p0_2)
        self.assertEqual(p0_2.secrets, 6)
        self.assertEqual(p0_2.money, 2)
        self.assertIn(y3_die, p0_2.in_production_dice)
        self.assertNotIn(y3_die, p0_2.glitched_dice)
        self.assertNotIn(y3_die, p0_2.scanned_dice)

    def test_b1_exit_tray_telemetry(self) -> None:
        """TC-9: B1 evaluates Phase 2 exit tray (0 Blue -> +2 🔬; 1+ Blue -> +$3 Cash)."""
        # Scenario A: 0 Blue exited
        eng_a = _v044_engine()
        p0_a = eng_a.state.players[0]
        p0_a.money = 0
        p0_a.research_tokens = 0
        eng_a.state.last_exited_cubes = {CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 1}
        p0_a.in_production_dice = [_star_die(901, DieColor.BLUE, "B1")]
        execute_player_income(eng_a, p0_a)
        self.assertEqual(p0_a.research_tokens, 2)
        self.assertEqual(p0_a.money, 0)

        # Scenario B: 2 Blue exited
        eng_b = _v044_engine()
        p0_b = eng_b.state.players[0]
        p0_b.money = 0
        p0_b.research_tokens = 0
        eng_b.state.last_exited_cubes = {CubeColor.RED: 0, CubeColor.BLUE: 2, CubeColor.GREEN: 0}
        p0_b.in_production_dice = [_star_die(902, DieColor.BLUE, "B1")]
        execute_player_income(eng_b, p0_b)
        self.assertEqual(p0_b.money, 3)
        self.assertEqual(p0_b.research_tokens, 0)

    def test_full_game_v044_smoke(self) -> None:
        """Smoke test: run a full 4-player game under GameConfig.v044()."""
        eng = _v044_engine(num_players=4, seed=123, isolate=False)
        res = eng.run_game()
        self.assertGreaterEqual(eng.state.current_round, 1)
        self.assertTrue(eng.state.game_over)
        self.assertIsNotNone(res)


if __name__ == "__main__":
    unittest.main()
