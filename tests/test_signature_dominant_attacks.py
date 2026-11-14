"""Comprehensive unit and integration tests for Dominant Cube Color Signature Attacks (v0.43.0).

Covers invariants INV-SIG-01 through INV-SIG-03, INV-SIG-RED, INV-SIMUL-RED,
INV-SIG-BLUE, INV-SIG-BLUE-TRIAGE, INV-SIG-GREEN, INV-GREEN-SUPPLY,
INV-GREEN-OVERFLOW, INV-SIG-BLACK, INV-SIG-COMPAT, and test cases TC-SIG-01 through TC-SIG-14
per docs/specs/signature_cube_dominant_attacks_spec.md.
"""

from __future__ import annotations

import unittest
from typing import Dict, List, Optional

from sim.bots.base import BaseBot
from sim.config import (
    CubeColor,
    DieColor,
    EndGameReason,
    GameConfig,
    ShieldColor,
    SignatureAttackMode,
    SignatureCubeLocation,
)
from sim.engine import fast_clone, research_tracks
from sim.engine.core import GameEngine
from sim.engine.phase4_attack_resolution import (
    check_end_triggers_after_attacks,
    determine_dominant_tray_color,
    execute_attack_resolution,
    resolve_signature_attacks,
)
from sim.engine.phase5_pipeline_shift import conveyor_triage_v038
from sim.engine.state import CompileResult, GameState, PlayerState, ProductionRole
from sim.entities import COMPANIES, CompanyCode, Die, Face, create_colored_die, create_gray_die


class SignatureStubBot(BaseBot):
    """Stub bot for testing signature attack decision hooks."""

    def __init__(self, bot_id: int = 0) -> None:
        super().__init__(bot_id=bot_id, name=f"SigStub_{bot_id}")
        self.red_recipient_called_with: Optional[List[int]] = None
        self.red_recipient_override_pid: Optional[int] = None
        self.green_tracks_called_with: Optional[List[str]] = None
        self.green_tracks_override: Optional[List[str]] = None

    def choose_signature_red_recipient(
        self,
        player: PlayerState,
        tied_recipients: List[PlayerState],
        game_state: Optional[GameState] = None,
        **kwargs,
    ) -> PlayerState:
        self.red_recipient_called_with = [p.player_id for p in tied_recipients]
        if self.red_recipient_override_pid is not None:
            for p in tied_recipients:
                if p.player_id == self.red_recipient_override_pid:
                    return p
        return super().choose_signature_red_recipient(player, tied_recipients, game_state, **kwargs)

    def choose_signature_green_tracks(
        self,
        player: PlayerState,
        eligible_tracks: List[str],
        count: int = 2,
        game_state: Optional[GameState] = None,
        **kwargs,
    ) -> List[str]:
        self.green_tracks_called_with = list(eligible_tracks)
        if self.green_tracks_override is not None:
            return list(self.green_tracks_override[:count])
        return super().choose_signature_green_tracks(player, eligible_tracks, count, game_state, **kwargs)


class TestSignatureCubeDominantAttacks(unittest.TestCase):
    """Validates TC-SIG-01 through TC-SIG-14 for Phase 62 Dominant Cube Color Signature Attacks."""

    def setUp(self) -> None:
        self.config = GameConfig.v043(num_players=4)
        self.engine = GameEngine(config=self.config, seed=101)

    def _make_compile_result(
        self,
        exited: Dict[CubeColor, int],
        buffer_overflow: bool = False,
    ) -> CompileResult:
        empty = {c: 0 for c in (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN, CubeColor.BLACK)}
        full_exited = dict(empty)
        full_exited.update(exited)
        return CompileResult(
            staged_before=dict(empty),
            stuck_before=dict(empty),
            exited_cubes=full_exited,
            stuck_after=dict(empty),
            buffer_overflow=buffer_overflow,
        )

    def test_tc_sig_01_unique_maximum_dominant_color(self) -> None:
        """TC-SIG-01: Unique maximum count in Exit Tray returns that color (INV-SIG-01)."""
        exited = {
            CubeColor.BLACK: 3,
            CubeColor.RED: 1,
            CubeColor.BLUE: 1,
            CubeColor.GREEN: 0,
        }
        dom = determine_dominant_tray_color(exited, self.config.signature_attack_tie_order)
        self.assertEqual(dom, CubeColor.BLACK)

        exited_red = {
            CubeColor.RED: 4,
            CubeColor.BLUE: 2,
            CubeColor.GREEN: 1,
            CubeColor.BLACK: 0,
        }
        self.assertEqual(
            determine_dominant_tray_color(exited_red, self.config.signature_attack_tie_order),
            CubeColor.RED,
        )

    def test_tc_sig_02_four_way_tie_priority_order(self) -> None:
        """TC-SIG-02: 4-way tie for highest count selects GREEN per GREEN > BLACK > BLUE > RED (INV-SIG-01)."""
        exited = {
            CubeColor.RED: 1,
            CubeColor.BLUE: 1,
            CubeColor.GREEN: 1,
            CubeColor.BLACK: 1,
        }
        dom = determine_dominant_tray_color(exited, self.config.signature_attack_tie_order)
        self.assertEqual(dom, CubeColor.GREEN)

    def test_tc_sig_03_two_way_and_three_way_ties(self) -> None:
        """TC-SIG-03: 2-way and 3-way ties evaluate strictly per GREEN > BLACK > BLUE > RED (INV-SIG-01)."""
        order = self.config.signature_attack_tie_order
        # 2 Black & 2 Blue -> Black
        self.assertEqual(
            determine_dominant_tray_color(
                {CubeColor.BLACK: 2, CubeColor.BLUE: 2, CubeColor.RED: 1, CubeColor.GREEN: 0},
                order,
            ),
            CubeColor.BLACK,
        )
        # 2 Blue & 2 Red -> Blue
        self.assertEqual(
            determine_dominant_tray_color(
                {CubeColor.BLUE: 2, CubeColor.RED: 2, CubeColor.BLACK: 1, CubeColor.GREEN: 0},
                order,
            ),
            CubeColor.BLUE,
        )
        # 2 Green & 2 Black -> Green
        self.assertEqual(
            determine_dominant_tray_color(
                {CubeColor.GREEN: 2, CubeColor.BLACK: 2, CubeColor.BLUE: 1, CubeColor.RED: 0},
                order,
            ),
            CubeColor.GREEN,
        )
        # 3-way tie: Black, Blue, Red -> Black
        self.assertEqual(
            determine_dominant_tray_color(
                {CubeColor.BLACK: 3, CubeColor.BLUE: 3, CubeColor.RED: 3, CubeColor.GREEN: 1},
                order,
            ),
            CubeColor.BLACK,
        )

    def test_tc_sig_04_configurable_tie_order(self) -> None:
        """TC-SIG-04: Custom signature_attack_tie_order on GameConfig overrides default (INV-SIG-01)."""
        custom_order = (CubeColor.BLUE, CubeColor.GREEN, CubeColor.BLACK, CubeColor.RED)
        cfg = GameConfig.v043(signature_attack_tie_order=custom_order)
        self.assertEqual(cfg.signature_attack_tie_order, custom_order)

        exited = {CubeColor.BLUE: 2, CubeColor.GREEN: 2, CubeColor.BLACK: 0, CubeColor.RED: 0}
        self.assertEqual(determine_dominant_tray_color(exited, cfg.signature_attack_tie_order), CubeColor.BLUE)

    def test_tc_sig_05_clean_tray_fizzle_on_zero_exited_cubes(self) -> None:
        """TC-SIG-05: 0 total exited cubes in tray -> dominant color is None and Target Lock fizzles (INV-SIG-02)."""
        p0 = self.engine.state.players[0]
        p0.target_locked = True
        ms_before = p0.market_share
        secrets_before = p0.secrets

        cr = self._make_compile_result(
            {CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0},
            buffer_overflow=True,
        )
        dom = determine_dominant_tray_color(cr.exited_cubes, self.config.signature_attack_tie_order)
        self.assertIsNone(dom)

        resolve_signature_attacks(self.engine, cr)
        self.assertIsNone(self.engine.state.last_dominant_color)
        self.assertEqual(p0.market_share, ms_before)
        self.assertEqual(p0.secrets, secrets_before)
        self.assertEqual(sum(p0.signature_attacks_suffered.values()), 0)

    def test_tc_sig_06_phase4_timing_after_shields_and_before_end_triggers(self) -> None:
        """TC-SIG-06: Standard shields block base attack & Defense L4 pays cash; then Black signature attack resolves before end triggers (INV-SIG-03)."""
        p0 = self.engine.state.players[0]
        p0.target_locked = True
        p0.defense_level = 4
        p0.defense_capacity = 4
        p0.glitched_shield_slots = 0
        p0.money = 0
        p0.secrets = 2
        p0.company_ability_used_this_version = True  # Already used -> Black fallback will drop 2 Secrets to 0 -> PZ

        # Give p0 1 Block 1 Any shield die In Production to block the 1 Blue cube
        shield_die = create_gray_die(die_id=901)
        shield_die.current_face = Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)
        shield_die.production_role = ProductionRole.ANY_SHIELD
        p0.in_production_dice = [shield_die]

        commitments = [
            (p0, [shield_die], {0: ShieldColor.ANY}),
        ] + [
            (p, [], {}) for p in self.engine.state.players[1:]
        ]

        # 2 Black cubes and 1 Blue cube exited -> Black is dominant, Blue is base attack (1)
        cr = self._make_compile_result(
            {CubeColor.BLACK: 2, CubeColor.BLUE: 1, CubeColor.RED: 0, CubeColor.GREEN: 0}
        )

        execute_attack_resolution(self.engine, commitments, cr)

        # 1. Base Blue attack (1) was blocked by the 1 shield (NOT +1 extra Blue cube because v0.43 uses dominant_color_effects)
        self.assertEqual(p0.last_defense_breakdown["blocked"]["blue"], 1)
        self.assertEqual(p0.last_defense_breakdown["unblocked"]["blue"], 0)
        # 2. Defense L4 paid +$1 cash for the 1 blocked Blue cube before signature attack eliminated p0
        self.assertEqual(p0.money, 1)
        # 3. Black signature attack fallback reduced p0 secrets from 2 to 0
        self.assertEqual(p0.secrets, 0)
        self.assertEqual(p0.signature_black_secrets_lost, 2)
        # 4. End-of-Phase-4 trigger flagged p0 as Patient Zero and triggered Final Round
        self.assertTrue(p0.is_patient_zero)
        self.assertTrue(self.engine.state.is_final_round)
        self.assertEqual(self.engine.state.end_reason, EndGameReason.PATIENT_ZERO)
        # 5. Closing step reset target_locked to False
        self.assertFalse(p0.target_locked)

    def test_tc_sig_07_red_solo_attack_transfer_to_unique_trailing(self) -> None:
        """TC-SIG-07: 1 locked player at 10 MS; 3 non-locked at 12, 8, 6 MS -> locked drops to 8, trailing (6) rises to 8 (INV-SIG-RED)."""
        players = self.engine.state.players
        players[0].market_share = 10
        players[0].target_locked = True
        players[1].market_share = 12
        players[1].target_locked = False
        players[2].market_share = 8
        players[2].target_locked = False
        players[3].market_share = 6
        players[3].target_locked = False

        cr = self._make_compile_result({CubeColor.RED: 3, CubeColor.BLUE: 1, CubeColor.GREEN: 0, CubeColor.BLACK: 0})
        resolve_signature_attacks(self.engine, cr)

        self.assertEqual(players[0].market_share, 8)
        self.assertEqual(players[1].market_share, 12)
        self.assertEqual(players[2].market_share, 8)
        self.assertEqual(players[3].market_share, 8)
        self.assertEqual(players[0].signature_red_transfers_sent, 2)
        self.assertEqual(players[3].signature_red_transfers_received, 2)
        self.assertEqual(players[0].signature_attacks_suffered["red"], 1)

    def test_tc_sig_08_red_tied_recipient_bot_hook(self) -> None:
        """TC-SIG-08: Locked player loses 2 MS; two non-locked players tie for least MS -> invokes choose_signature_red_recipient (INV-SIG-RED)."""
        players = self.engine.state.players
        stub_bot = SignatureStubBot(bot_id=0)
        stub_bot.red_recipient_override_pid = players[3].player_id
        players[0].bot = stub_bot
        players[0].market_share = 10
        players[0].target_locked = True

        players[1].market_share = 12
        players[1].target_locked = False
        players[2].market_share = 6
        players[2].target_locked = False
        players[3].market_share = 6
        players[3].target_locked = False

        cr = self._make_compile_result({CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0})
        resolve_signature_attacks(self.engine, cr)

        self.assertEqual(players[0].market_share, 8)
        self.assertEqual(stub_bot.red_recipient_called_with, [players[2].player_id, players[3].player_id])
        self.assertEqual(players[2].market_share, 6)
        self.assertEqual(players[3].market_share, 8)

    def test_tc_sig_09_red_multi_locked_all_four_fizzle_transfer(self) -> None:
        """TC-SIG-09: All 4 players locked -> Epoch 1 drains all by -2 MS; Epoch 2 eligible set is empty so transfers fizzle (INV-SIMUL-RED)."""
        players = self.engine.state.players
        initial_ms = [14, 12, 10, 8]
        for p, ms in zip(players, initial_ms):
            p.market_share = ms
            p.target_locked = True

        cr = self._make_compile_result({CubeColor.RED: 3, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0})
        resolve_signature_attacks(self.engine, cr)

        expected_ms = [12, 10, 8, 6]
        for p, exp in zip(players, expected_ms):
            self.assertEqual(p.market_share, exp)
            self.assertEqual(p.signature_red_transfers_sent, 0)
            self.assertEqual(p.signature_red_transfers_received, 0)
            self.assertEqual(p.signature_attacks_suffered["red"], 1)

    def test_tc_sig_10_blue_buffer_congestion_source_precedence(self) -> None:
        """TC-SIG-10: Blue dominant moves 1 Gray die from Scanned (or In Production / Ready) to Processing Box with secret_pending=False (INV-SIG-BLUE)."""
        p0 = self.engine.state.players[0]
        p0.target_locked = True
        p0.glitched_dice.clear()
        p0.scanned_dice.clear()
        p0.in_production_dice.clear()
        p0.ready_for_release_dice.clear()

        gray_scanned = create_gray_die(die_id=101)
        gray_ready = create_gray_die(die_id=102)
        p0.scanned_dice.append(gray_scanned)
        p0.ready_for_release_dice.append(gray_ready)

        cr = self._make_compile_result({CubeColor.BLUE: 3, CubeColor.RED: 1, CubeColor.GREEN: 0, CubeColor.BLACK: 0})
        resolve_signature_attacks(self.engine, cr)

        self.assertEqual(len(p0.scanned_dice), 0)
        self.assertEqual(len(p0.ready_for_release_dice), 1)
        self.assertEqual(len(p0.glitched_dice), 1)
        self.assertIs(p0.glitched_dice[0], gray_scanned)
        self.assertFalse(gray_scanned.secret_pending)

        # Fallback: Scanned empty, Gray in In Production -> moves from In Production
        p0.target_locked = True
        p0.glitched_dice.clear()
        p0.in_production_dice.append(gray_ready)
        p0.ready_for_release_dice.clear()
        resolve_signature_attacks(self.engine, cr)
        self.assertEqual(len(p0.in_production_dice), 0)
        self.assertEqual(len(p0.glitched_dice), 1)
        self.assertIs(p0.glitched_dice[0], gray_ready)

    def test_tc_sig_11_blue_triage_zero_secrets_and_no_signature_queue(self) -> None:
        """TC-SIG-11: Gray die in Processing Box consumes 1 triage bandwidth, yields 0 Secrets, and does NOT queue Signature Cube (INV-SIG-BLUE-TRIAGE, INV-TL-03)."""
        p0 = self.engine.state.players[0]
        p0.triage_bandwidth = 1
        p0.signature_cube_location = SignatureCubeLocation.IDLE_ON_MAT
        self.engine.state.staging_signature_cubes.clear()
        secrets_before = p0.secrets

        gray_die = create_gray_die(die_id=201)
        gray_die.secret_pending = False
        p0.glitched_dice = [gray_die]
        p0.scanned_dice.clear()

        moved = conveyor_triage_v038(self.engine, p0)

        self.assertEqual(len(moved), 1)
        self.assertIs(moved[0], gray_die)
        self.assertIn(gray_die, p0.scanned_dice)
        self.assertEqual(p0.secrets, secrets_before)
        self.assertEqual(p0.signature_cube_location, SignatureCubeLocation.IDLE_ON_MAT)
        self.assertNotIn(p0.player_id, self.engine.state.staging_signature_cubes)

    def test_tc_sig_12_green_malware_encryption_and_double_cost_clearance(self) -> None:
        """TC-SIG-12: Green dominant encrypts 2 tracks; next step costs 2x research and clears on upgrade (INV-SIG-GREEN)."""
        p0 = self.engine.state.players[0]
        stub_bot = SignatureStubBot(bot_id=0)
        stub_bot.green_tracks_override = ["DEFENSE", "TRIAGE"]
        p0.bot = stub_bot
        p0.target_locked = True
        p0.defense_level = 0
        p0.triage_level = 0
        p0.release_level = 0
        p0.patent_level = 0
        p0.encrypted_research_tracks.clear()

        cr = self._make_compile_result({CubeColor.GREEN: 2, CubeColor.RED: 1, CubeColor.BLUE: 0, CubeColor.BLACK: 0})
        resolve_signature_attacks(self.engine, cr)

        self.assertEqual(p0.encrypted_research_tracks, {"DEFENSE", "TRIAGE"})
        # Base cost for L0 -> L1 is 1; encrypted cost is 2
        self.assertEqual(research_tracks.step_cost(self.config, p0, "DEFENSE"), 2)
        self.assertEqual(research_tracks.step_cost(self.config, p0, "TRIAGE"), 2)
        self.assertEqual(research_tracks.step_cost(self.config, p0, "RELEASE"), 1)
        self.assertEqual(research_tracks.step_cost(self.config, p0, "PR"), 1)

        # Cannot upgrade DEFENSE with only 1 research token
        p0.research_tokens = 1
        self.assertFalse(p0.upgrade_track("DEFENSE"))
        self.assertIn("DEFENSE", p0.encrypted_research_tracks)

        # With 2 research tokens, upgrade succeeds and clears encryption marker
        p0.research_tokens = 2
        self.assertTrue(p0.upgrade_track("DEFENSE"))
        self.assertEqual(p0.research_tokens, 0)
        self.assertEqual(p0.defense_level, 1)
        self.assertNotIn("DEFENSE", p0.encrypted_research_tracks)
        # Next step L1 -> L2 is unencrypted (base cost = 2)
        self.assertEqual(research_tracks.step_cost(self.config, p0, "DEFENSE"), 2)

    def test_tc_sig_13_green_saturation_spillover_and_supply_isolation(self) -> None:
        """TC-SIG-13: 3 tracks at L4 and 1 at L2 -> marks the 1 eligible track and spills 1 cube to glitch 1 shield slot; compiler Green supply untouched (INV-GREEN-OVERFLOW, INV-GREEN-SUPPLY)."""
        p0 = self.engine.state.players[0]
        p0.target_locked = True
        p0.defense_level = 4
        p0.defense_capacity = 4
        p0.triage_level = 4
        p0.release_level = 4
        p0.patent_level = 2  # Only PR is < L4
        p0.glitched_shield_slots = 1
        p0.encrypted_research_tracks.clear()

        staging_green_before = self.engine.state.staging_cup.get(CubeColor.GREEN, 0)
        stuck_green_before = self.engine.state.tower.stuck_cubes.get(CubeColor.GREEN, 0)

        cr = self._make_compile_result({CubeColor.GREEN: 3, CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.BLACK: 0})
        resolve_signature_attacks(self.engine, cr)

        # PR is encrypted
        self.assertEqual(p0.encrypted_research_tracks, {"PR"})
        # Base cost for L2 -> L3 is 2; encrypted cost is 4
        self.assertEqual(research_tracks.step_cost(self.config, p0, "PR"), 4)
        self.assertEqual(research_tracks.step_cost(self.config, p0, "PATENT"), 4)
        # 1 unplaced cube spilled over to glitch 1 shield slot (1 -> 2)
        self.assertEqual(p0.glitched_shield_slots, 2)
        # Compiler Green supply is strictly isolated
        self.assertEqual(self.engine.state.staging_cup.get(CubeColor.GREEN, 0), staging_green_before)
        self.assertEqual(self.engine.state.tower.stuck_cubes.get(CubeColor.GREEN, 0), stuck_green_before)

    def test_tc_sig_14_black_override_burn_and_secret_loss_patient_zero_fallback(self) -> None:
        """TC-SIG-14: Black burns Institutional Override if unused; loses 2 Secrets if already used; triggers Patient Zero via check_end_triggers_after_attacks at <= 0 Secrets (INV-SIG-BLACK)."""
        p0, p1, p2, p3 = self.engine.state.players

        # Player 0: Override available -> burned, Secrets unchanged
        p0.target_locked = True
        p0.company_ability_used_this_version = False
        p0.secrets = 4

        # Player 1: Override already used, 3 Secrets -> drops to 1 Secret (survives)
        p1.target_locked = True
        p1.company_ability_used_this_version = True
        p1.secrets = 3

        # Player 2: Override already used, 2 Secrets -> drops to 0 Secrets -> Patient Zero in check_end_triggers_after_attacks
        p2.target_locked = True
        p2.company_ability_used_this_version = True
        p2.secrets = 2

        # Player 3: Not target-locked -> untouched
        p3.target_locked = False
        p3.company_ability_used_this_version = False
        p3.secrets = 4

        cr = self._make_compile_result({CubeColor.BLACK: 2, CubeColor.RED: 1, CubeColor.BLUE: 0, CubeColor.GREEN: 0})
        resolve_signature_attacks(self.engine, cr)

        # Before end-trigger check, p2 has 0 Secrets and is flagged by check_end_triggers_after_attacks
        self.assertEqual(p2.secrets, 0)
        self.assertFalse(p2.is_patient_zero)

        check_end_triggers_after_attacks(self.engine)

        # P0: Override burned, 4 Secrets intact
        self.assertTrue(p0.company_ability_used_this_version)
        self.assertEqual(p0.signature_override_hijacks, 1)
        self.assertEqual(p0.secrets, 4)
        self.assertFalse(p0.is_patient_zero)

        # P1: Lost 2 Secrets (3 -> 1), survives
        self.assertEqual(p1.secrets, 1)
        self.assertEqual(p1.signature_black_secrets_lost, 2)
        self.assertFalse(p1.is_patient_zero)

        # P2: Lost 2 Secrets (2 -> 0), eliminated as Patient Zero
        self.assertEqual(p2.secrets, 0)
        self.assertEqual(p2.signature_black_secrets_lost, 2)
        self.assertTrue(p2.is_patient_zero)
        self.assertEqual(p2.breach_depth, 0)
        self.assertTrue(self.engine.state.is_final_round)
        self.assertEqual(self.engine.state.end_reason, EndGameReason.PATIENT_ZERO)

        # P3: Untouched
        self.assertFalse(p3.company_ability_used_this_version)
        self.assertEqual(p3.secrets, 4)

    def test_dto_black_override_burn_and_fast_clone_parity(self) -> None:
        """Validates DTO Slush Fund burn under Black Signature Attack and fast_clone deep-copy parity."""
        p0 = self.engine.state.players[0]
        p0.company = COMPANIES[CompanyCode.DTO]
        p0.target_locked = True
        p0.company_ability_used_this_version = False
        p0.dto_slush_fund_used = False
        p0.encrypted_research_tracks.add("DEFENSE")

        clone_eng, _ = fast_clone.clone_engine(self.engine)
        clone_p0 = clone_eng.state.players[0]
        self.assertEqual(clone_p0.encrypted_research_tracks, {"DEFENSE"})
        self.assertIsNot(clone_p0.encrypted_research_tracks, p0.encrypted_research_tracks)

        cr = self._make_compile_result({CubeColor.BLACK: 1})
        resolve_signature_attacks(self.engine, cr)
        self.assertTrue(p0.company_ability_used_this_version)
        self.assertTrue(p0.dto_slush_fund_used)
        self.assertEqual(p0.signature_override_hijacks, 1)

    def test_backward_compatibility_modes(self) -> None:
        """Validates INV-SIG-COMPAT across v041 ('none'), v042 ('v042_plus_one_cube'), and v043 ('dominant_color_effects')."""
        cfg_41 = GameConfig.v041()
        self.assertFalse(cfg_41.target_lock_enabled)
        self.assertEqual(cfg_41.signature_attack_mode, SignatureAttackMode.NONE.value)

        cfg_42 = GameConfig.v042()
        self.assertTrue(cfg_42.target_lock_enabled)
        self.assertEqual(cfg_42.signature_attack_mode, SignatureAttackMode.V042_PLUS_ONE_CUBE.value)

        cfg_43 = GameConfig.v043()
        self.assertTrue(cfg_43.target_lock_enabled)
        self.assertEqual(cfg_43.signature_attack_mode, SignatureAttackMode.DOMINANT_COLOR_EFFECTS.value)


if __name__ == "__main__":
    unittest.main()
