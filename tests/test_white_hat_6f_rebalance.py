"""Tests for White Hat Face 6 (Purple ★) Signature Protocol Rebalance (v0.43.0).

Covers TEST-WH-01 through TEST-WH-26 from docs/specs/white_hat_6f_rebalance_spec.md.
"""

from __future__ import annotations

import unittest

from sim.bots.base import BaseBot
from sim.config import CubeColor, DieColor, GameConfig, ShieldColor
from sim.engine.core import GameEngine
from sim.engine import (
    phase1_roll_deploy,
    phase3_income,
    phase4_attack_resolution,
    phase5_pipeline_shift,
)
from sim.engine.state import ProductionRole
from sim.entities import (
    CompanyCode,
    Face,
    WhiteHatCode,
    create_colored_die,
    create_gray_die,
    create_white_die,
    get_company_by_code,
    get_white_hat_by_code,
)


def _purple_star_die(die_id: int) -> object:
    d = create_colored_die(DieColor.PURPLE, die_id)
    d.current_face = d.faces[5]  # Purple ★
    d.production_role = ProductionRole.INCOME
    return d


class TestWhiteHat6FRebalance(unittest.TestCase):
    """TEST-WH-01 through TEST-WH-26."""

    def _make_engine(self, white_hat_code: WhiteHatCode, seed: int = 42) -> tuple[GameEngine, object]:
        cfg = GameConfig.v043(num_players=2)
        engine = GameEngine(config=cfg, seed=seed)
        p0 = engine.state.players[0]
        p0.company = get_company_by_code(CompanyCode.AEGIS)
        p0.white_hat = get_white_hat_by_code(white_hat_code)
        p0.money = 0
        p0.research_tokens = 0
        p0.in_production_dice.clear()
        p0.scanned_dice.clear()
        p0.glitched_dice.clear()
        p0.ready_for_release_dice.clear()
        return engine, p0

    # --- The Operator (Logistics Bounty) ---

    def test_operator_scanned_box_zero_dice(self) -> None:
        """TEST-WH-01: Empty Scanned Box -> +0 research (no fallback)."""
        engine, p0 = self._make_engine(WhiteHatCode.OPERATOR)
        p0.in_production_dice.append(_purple_star_die(101))
        rec = phase3_income.execute_player_income(engine, p0)
        self.assertEqual(rec.research, 0)
        self.assertEqual(p0.research_tokens, 0)
        self.assertEqual(len(p0.scanned_dice), 0)

    def test_operator_scanned_box_scaling(self) -> None:
        """TEST-WH-02: 3 dice in Scanned Box -> +3 research; Scanned Box unchanged."""
        engine, p0 = self._make_engine(WhiteHatCode.OPERATOR)
        p0.in_production_dice.append(_purple_star_die(101))
        p0.scanned_dice.extend([create_gray_die(1), create_gray_die(2), create_colored_die(DieColor.GREEN, 3)])
        rec = phase3_income.execute_player_income(engine, p0)
        self.assertEqual(rec.research, 3)
        self.assertEqual(p0.research_tokens, 3)
        self.assertEqual(len(p0.scanned_dice), 3)

    def test_operator_double_purple_star(self) -> None:
        """TEST-WH-03: 2 Purple Stars In Production with 2 Scanned dice -> +4 research."""
        engine, p0 = self._make_engine(WhiteHatCode.OPERATOR)
        p0.in_production_dice.extend([_purple_star_die(101), _purple_star_die(102)])
        p0.scanned_dice.extend([create_gray_die(1), create_gray_die(2)])
        rec = phase3_income.execute_player_income(engine, p0)
        self.assertEqual(rec.research, 4)
        self.assertEqual(p0.research_tokens, 4)

    # --- The Phreaker (Jumper Diagnostics) ---

    def test_phreaker_cash_and_bandwidth(self) -> None:
        """TEST-WH-04: 1 Purple Star -> +$1 cash, temp_release_bandwidth_bonus == 1, cap 4 -> 5."""
        engine, p0 = self._make_engine(WhiteHatCode.PHREAKER)
        p0.release_bandwidth = 4
        p0.in_production_dice.append(_purple_star_die(101))
        rec = phase3_income.execute_player_income(engine, p0)
        self.assertEqual(rec.money, 1)
        self.assertEqual(p0.money, 1)
        self.assertEqual(p0.temp_release_bandwidth_bonus, 1)
        self.assertEqual(p0.effective_release_bandwidth, 5)
        p0.scanned_dice.extend([create_gray_die(i) for i in range(1, 7)])
        self.assertEqual(phase5_pipeline_shift.max_graduates(p0), 5)

    def test_phreaker_double_purple_star(self) -> None:
        """TEST-WH-05: 2 Purple Stars -> +$2 cash, temp_release_bandwidth_bonus == 2, cap 4 -> 6."""
        engine, p0 = self._make_engine(WhiteHatCode.PHREAKER)
        p0.release_bandwidth = 4
        p0.in_production_dice.extend([_purple_star_die(101), _purple_star_die(102)])
        rec = phase3_income.execute_player_income(engine, p0)
        self.assertEqual(rec.money, 2)
        self.assertEqual(p0.money, 2)
        self.assertEqual(p0.temp_release_bandwidth_bonus, 2)
        self.assertEqual(p0.effective_release_bandwidth, 6)
        p0.scanned_dice.extend([create_gray_die(i) for i in range(1, 8)])
        self.assertEqual(phase5_pipeline_shift.max_graduates(p0), 6)

    def test_phreaker_bandwidth_reset_at_round_end(self) -> None:
        """TEST-WH-06: temp_release_bandwidth_bonus resets to 0 after round finalization."""
        engine, p0 = self._make_engine(WhiteHatCode.PHREAKER)
        p0.release_bandwidth = 4
        p0.temp_release_bandwidth_bonus = 2
        tel = engine._begin_telemetry(type(
            "CR", (), {
                "staged_before": {}, "stuck_before": {}, "exited_cubes": {},
                "stuck_after": {}, "buffer_overflow": False,
                "target_locks": {}, "signature_cube_locations": {},
            }
        )())
        engine._finalize_telemetry(tel, end_phase=6)
        self.assertEqual(p0.temp_release_bandwidth_bonus, 0)
        self.assertEqual(p0.effective_release_bandwidth, 4)

    # --- The Acoustic (Resonance Sensor) ---

    def test_acoustic_zero_exited_cubes(self) -> None:
        """TEST-WH-07: Empty tray -> distinct_colors == 0 -> $0 cash."""
        engine, p0 = self._make_engine(WhiteHatCode.ACOUSTIC)
        engine.state.distinct_exited_colors_this_round = 0
        p0.in_production_dice.append(_purple_star_die(101))
        rec = phase3_income.execute_player_income(engine, p0)
        self.assertEqual(rec.money, 0)
        self.assertEqual(p0.money, 0)

    def test_acoustic_compiler_cubes_only(self) -> None:
        """TEST-WH-08: Red: 2, Blue: 1, Green: 1, Black: 0 -> 3 colors -> +$3 cash."""
        engine, p0 = self._make_engine(WhiteHatCode.ACOUSTIC)
        exited = {CubeColor.RED: 2, CubeColor.BLUE: 1, CubeColor.GREEN: 1, CubeColor.BLACK: 0}
        engine.state.distinct_exited_colors_this_round = phase3_income.compute_distinct_exited_colors(exited, [])
        p0.in_production_dice.append(_purple_star_die(101))
        rec = phase3_income.execute_player_income(engine, p0)
        self.assertEqual(rec.money, 3)
        self.assertEqual(p0.money, 3)

    def test_acoustic_with_signature_cubes(self) -> None:
        """TEST-WH-09: 3 compiler colors + 1 signature cube -> 4 distinct colors -> +$4 cash."""
        engine, p0 = self._make_engine(WhiteHatCode.ACOUSTIC)
        exited = {CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 1, CubeColor.BLACK: 0}
        engine.state.distinct_exited_colors_this_round = phase3_income.compute_distinct_exited_colors(exited, [0])
        p0.in_production_dice.append(_purple_star_die(101))
        rec = phase3_income.execute_player_income(engine, p0)
        self.assertEqual(rec.money, 4)
        self.assertEqual(p0.money, 4)

    def test_acoustic_max_five_cap(self) -> None:
        """TEST-WH-10: 4 compiler colors + 2 signature cubes -> capped at +$5 max."""
        engine, p0 = self._make_engine(WhiteHatCode.ACOUSTIC)
        exited = {CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 1, CubeColor.BLACK: 1}
        engine.state.distinct_exited_colors_this_round = phase3_income.compute_distinct_exited_colors(exited, [0, 1])
        self.assertEqual(engine.state.distinct_exited_colors_this_round, 5)
        p0.in_production_dice.append(_purple_star_die(101))
        rec = phase3_income.execute_player_income(engine, p0)
        self.assertEqual(rec.money, 5)
        self.assertEqual(p0.money, 5)

    def test_acoustic_double_purple_star(self) -> None:
        """TEST-WH-11: 2 Purple Stars with 4 exited colors -> +$8 cash."""
        engine, p0 = self._make_engine(WhiteHatCode.ACOUSTIC)
        engine.state.distinct_exited_colors_this_round = 4
        p0.in_production_dice.extend([_purple_star_die(101), _purple_star_die(102)])
        rec = phase3_income.execute_player_income(engine, p0)
        self.assertEqual(rec.money, 8)
        self.assertEqual(p0.money, 8)

    # --- The Spook (Burn Notice) ---

    def test_spook_base_cash_no_burn(self) -> None:
        """TEST-WH-12: 1 Purple Star, declining burn -> +$2 cash, Gray dice unchanged."""
        engine, p0 = self._make_engine(WhiteHatCode.SPOOK)
        p0.in_production_dice.append(_purple_star_die(101))
        gray = create_gray_die(10)
        p0.scanned_dice.append(gray)
        rec = phase3_income.execute_player_income(engine, p0, spook_burn_die_id=None)
        self.assertEqual(rec.money, 2)
        self.assertEqual(p0.money, 2)
        self.assertIn(gray, p0.scanned_dice)

    def test_spook_burn_from_scanned_or_ready(self) -> None:
        """TEST-WH-13: Burn Gray die from Scanned -> +$5 cash ($2 + $3), die permanently removed."""
        engine, p0 = self._make_engine(WhiteHatCode.SPOOK)
        p0.in_production_dice.append(_purple_star_die(101))
        gray = create_gray_die(10)
        p0.scanned_dice.append(gray)
        rec = phase3_income.execute_player_income(engine, p0, spook_burn_die_id=10)
        self.assertEqual(rec.money, 5)
        self.assertEqual(p0.money, 5)
        self.assertNotIn(gray, p0.scanned_dice)
        self.assertNotIn(gray, p0.total_dice)

    def test_spook_burn_from_income_slot(self) -> None:
        """TEST-WH-14: Burn Gray die from Income slot -> harvests Phase 3 income, then culls for +$3."""
        engine, p0 = self._make_engine(WhiteHatCode.SPOOK)
        p0.in_production_dice.append(_purple_star_die(101))
        gray = create_gray_die(10)
        gray.current_face = Face(name="+$1", money=1)
        gray.production_role = ProductionRole.INCOME
        p0.in_production_dice.append(gray)
        rec = phase3_income.execute_player_income(engine, p0, spook_burn_die_id=10)
        self.assertEqual(rec.money, 6)  # $2 (Spook) + $1 (Gray face) + $3 (Burn Notice)
        self.assertNotIn(gray, p0.in_production_dice)

    def test_spook_burn_from_shield_slot(self) -> None:
        """TEST-WH-15: Burn Gray die from Shield slot -> +$5 cash, commitment dropped, 0 blocks in Phase 4."""
        engine, p0 = self._make_engine(WhiteHatCode.SPOOK)
        star = _purple_star_die(101)
        gray = create_gray_die(10)
        gray.current_face = Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)
        gray.production_role = ProductionRole.ANY_SHIELD
        p0.in_production_dice.extend([star, gray])
        rolled_dice = [star, gray]
        commitments = {1: ShieldColor.BLUE}
        rec = phase3_income.execute_player_income(engine, p0, spook_burn_die_id=10)
        self.assertEqual(rec.money, 5)
        self.assertNotIn(gray, p0.in_production_dice)
        phase4_attack_resolution.sync_commitments_with_production(p0, rolled_dice, commitments)
        self.assertEqual(commitments, {})

    def test_spook_double_purple_star_burn_two(self) -> None:
        """TEST-WH-16: 2 Purple Stars, burn 2 Gray dice -> +$10 cash ($4 + $6), 2 Gray dice removed."""
        engine, p0 = self._make_engine(WhiteHatCode.SPOOK)
        p0.in_production_dice.extend([_purple_star_die(101), _purple_star_die(102)])
        g1, g2 = create_gray_die(10), create_gray_die(11)
        p0.scanned_dice.extend([g1, g2])
        rec = phase3_income.execute_player_income(engine, p0, spook_burn_die_id=[10, 11])
        self.assertEqual(rec.money, 10)
        self.assertEqual(len(p0.scanned_dice), 0)
        self.assertEqual(rec.burned_gray_die_ids, [10, 11])

    def test_spook_zero_gray_dice_owned(self) -> None:
        """TEST-WH-17: Player owns 0 Gray dice -> burn unavailable, awards +$2 cash base."""
        engine, p0 = self._make_engine(WhiteHatCode.SPOOK)
        p0.in_production_dice.append(_purple_star_die(101))
        red = create_colored_die(DieColor.RED, 20)
        p0.scanned_dice.append(red)
        rec = phase3_income.execute_player_income(engine, p0)
        self.assertEqual(rec.money, 2)
        self.assertIn(red, p0.scanned_dice)

    def test_spook_cannot_burn_colored_or_white(self) -> None:
        """TEST-WH-18: Cannot target Red, Blue, Green, Yellow, Purple, or White Contractor dice."""
        engine, p0 = self._make_engine(WhiteHatCode.SPOOK)
        p0.in_production_dice.append(_purple_star_die(101))
        for idx, c in enumerate((DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW, DieColor.PURPLE)):
            d = create_colored_die(c, 30 + idx)
            p0.scanned_dice.append(d)
            self.assertFalse(phase3_income.resolve_spook_burn_notice(engine, p0, d.die_id))
        w = create_white_die(99)
        p0.scanned_dice.append(w)
        self.assertFalse(phase3_income.resolve_spook_burn_notice(engine, p0, w.die_id))

    # --- The Prodigy (Arbitrary Code Execution) ---

    def test_prodigy_timing_step4_only(self) -> None:
        """TEST-WH-19: Prodigy executes in Step 4 after rerolls, zero executions before rerolls."""
        call_rerolls_remaining: list[int] = []

        class _TimingBot(BaseBot):
            def choose_yahtzee_rerolls(self, player_state, active_dice, rerolls_remaining, **kwargs):
                # Record whether Prodigy already ran before rerolls
                return [1] if rerolls_remaining == 1 else []

            def choose_prodigy_purple_star_override(self, player_state, active_dice, rng):
                call_rerolls_remaining.append(player_state.total_rerolls_used)
                green = active_dice[1]
                return (1, green.faces[0])

        cfg = GameConfig.v043(num_players=2, default_free_rerolls=1)
        engine = GameEngine(config=cfg, seed=42)
        p0 = engine.state.players[0]
        p0.white_hat = get_white_hat_by_code(WhiteHatCode.PRODIGY)
        p0.bot = _TimingBot(bot_id=0)
        purple = create_colored_die(DieColor.PURPLE, 1)
        green = create_colored_die(DieColor.GREEN, 2)
        p0.ready_for_release_dice = [purple, green]

        # Force deterministic rolls: Purple rolls Face 6 (Star), Green rolls Face 3
        orig_roll = type(purple).roll

        def _fixed_roll(self_die, rng):
            if self_die.die_id == 1:
                self_die.current_face = self_die.faces[5]
            else:
                self_die.current_face = self_die.faces[2]
            return self_die.current_face

        type(purple).roll = _fixed_roll
        try:
            phase1_roll_deploy.execute_phase_1(engine)
        finally:
            type(purple).roll = orig_roll

        # Should have been called exactly once, AFTER the 1 reroll was used
        self.assertEqual(call_rerolls_remaining, [1])

    def test_prodigy_valid_face_conversion(self) -> None:
        """TEST-WH-20: Turn Green Face 3 to Green Face 1 (+2 research)."""
        engine, p0 = self._make_engine(WhiteHatCode.PRODIGY)
        purple = _purple_star_die(1)
        green = create_colored_die(DieColor.GREEN, 2)
        green.current_face = green.faces[2]
        active = [purple, green]
        ok = phase1_roll_deploy.resolve_prodigy_purple_star_override(
            p0, active, engine.rng, target_idx=1, target_face=green.faces[0]
        )
        self.assertTrue(ok)
        self.assertEqual(green.current_face, green.faces[0])

    def test_prodigy_forbidden_faces(self) -> None:
        """TEST-WH-21: Attempting to select Star face (Face 6) or Secret face (Face 5) is rejected."""
        engine, p0 = self._make_engine(WhiteHatCode.PRODIGY)
        purple = _purple_star_die(1)
        green = create_colored_die(DieColor.GREEN, 2, face_profile=engine.config.die_face_profile)
        green.current_face = green.faces[2]
        active = [purple, green]
        # Face 5 (Secret)
        self.assertTrue(green.faces[4].secrets_pending)
        self.assertFalse(
            phase1_roll_deploy.resolve_prodigy_purple_star_override(
                p0, active, engine.rng, target_idx=1, target_face=green.faces[4]
            )
        )
        # Face 6 (Star)
        self.assertTrue(green.faces[5].is_star)
        self.assertFalse(
            phase1_roll_deploy.resolve_prodigy_purple_star_override(
                p0, active, engine.rng, target_idx=1, target_face=green.faces[5]
            )
        )

    def test_prodigy_cannot_retarget_trigger_star(self) -> None:
        """TEST-WH-22: Cannot alter the single triggering Purple ★ die."""
        engine, p0 = self._make_engine(WhiteHatCode.PRODIGY)
        purple = _purple_star_die(1)
        green = create_colored_die(DieColor.GREEN, 2)
        active = [purple, green]
        self.assertFalse(
            phase1_roll_deploy.resolve_prodigy_purple_star_override(
                p0, active, engine.rng, target_idx=0, target_face=purple.faces[0]
            )
        )

    def test_prodigy_double_purple_star(self) -> None:
        """TEST-WH-23: 2 Purple Stars allow 2 independent overrides on other dice."""
        engine, p0 = self._make_engine(WhiteHatCode.PRODIGY)
        p1 = _purple_star_die(1)
        p2 = _purple_star_die(2)
        g1 = create_colored_die(DieColor.GREEN, 3)
        g1.current_face = g1.faces[2]
        r1 = create_colored_die(DieColor.RED, 4)
        r1.current_face = r1.faces[0]
        active = [p1, p2, g1, r1]
        excluded: set[int] = set()
        self.assertTrue(
            phase1_roll_deploy.resolve_prodigy_purple_star_override(
                p0, active, engine.rng, target_idx=2, target_face=g1.faces[0], excluded_targets=excluded
            )
        )
        self.assertTrue(
            phase1_roll_deploy.resolve_prodigy_purple_star_override(
                p0, active, engine.rng, target_idx=3, target_face=r1.faces[1], excluded_targets=excluded
            )
        )
        self.assertEqual(g1.current_face, g1.faces[0])
        self.assertEqual(r1.current_face, r1.faces[1])

    # --- The Cipher (Algorithmic Parity) ---

    def test_cipher_baseline_deterministic(self) -> None:
        """TEST-WH-24: 1 Purple Star -> +$2, +1 research; 2 Purple Stars -> +$4, +2 research."""
        engine, p0 = self._make_engine(WhiteHatCode.CIPHER)
        p0.in_production_dice.append(_purple_star_die(101))
        rec1 = phase3_income.execute_player_income(engine, p0)
        self.assertEqual((rec1.money, rec1.research), (2, 1))

        engine2, p1 = self._make_engine(WhiteHatCode.CIPHER)
        p1.in_production_dice.extend([_purple_star_die(101), _purple_star_die(102)])
        rec2 = phase3_income.execute_player_income(engine2, p1)
        self.assertEqual((rec2.money, rec2.research), (4, 2))

    # --- Suppression & Smoke ---

    def test_glitched_purple_suppression(self) -> None:
        """TEST-WH-25: Purple die in Processing Box -> 0 triggers for all White Hats."""
        for wh in WhiteHatCode:
            engine, p0 = self._make_engine(wh)
            p0.glitched_dice.append(_purple_star_die(101))
            rec = phase3_income.execute_player_income(engine, p0)
            self.assertEqual(rec.purple_star_triggers, 0)
            self.assertEqual(rec.money, 0)
            self.assertEqual(rec.research, 0)

    def test_all_36_pairings_smoke(self) -> None:
        """TEST-WH-26: All 36 Company x White Hat pairings execute 1 complete round without exception."""
        companies = list(CompanyCode)
        white_hats = list(WhiteHatCode)
        pairings = [(c, w) for c in companies for w in white_hats]
        self.assertEqual(len(pairings), 36)
        for idx in range(0, 36, 2):
            c0, w0 = pairings[idx]
            c1, w1 = pairings[idx + 1]
            cfg = GameConfig.v043(num_players=2)
            engine = GameEngine(config=cfg, seed=100 + idx)
            engine.state.players[0].company = get_company_by_code(c0)
            engine.state.players[0].white_hat = get_white_hat_by_code(w0)
            engine.state.players[1].company = get_company_by_code(c1)
            engine.state.players[1].white_hat = get_white_hat_by_code(w1)
            tel = engine.run_round()
            self.assertIsNotNone(tel)


if __name__ == "__main__":
    unittest.main()
