"""Comprehensive unit and integration tests for Operative Signature Cube & Target Lock Protocol.

Covers invariants INV-TL-01 through INV-TL-08 and tests TEST-TL-01 through TEST-TL-11
per docs/specs/target_lock_signature_cubes_spec.md.
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock
from typing import Dict, List, Optional

from sim.bots.base import BaseBot, default_target_lock_color_heuristic
from sim.config import CubeColor, DieColor, GameConfig, ShieldColor, SignatureCubeLocation, TowerMode
from sim.engine import secret_faces
from sim.engine.core import GameEngine
from sim.engine.phase2_compiler import execute_compiler_drop
from sim.engine.phase4_attack_resolution import (
    calculate_target_lock_extra_cube,
    finalize_attack_resolution,
    resolve_player_defense_and_wear,
)
from sim.engine.phase5_pipeline_shift import check_and_queue_signature_cube, conveyor_triage_v038
from sim.engine.state import CompileResult, GameState, PlayerState
from sim.entities import Die, Face, create_colored_die, create_gray_die


class StubBot(BaseBot):
    """Stub bot for test execution with configurable hook overrides."""

    def __init__(self, bot_id: int = 0):
        super().__init__(bot_id=bot_id, name=f"StubBot_{bot_id}")
        self.chosen_color_override: Optional[CubeColor] = None
        self.choose_target_lock_color_called_with: Optional[List[CubeColor]] = None

    def choose_target_lock_color(
        self,
        player: PlayerState,
        tied_colors: List[CubeColor],
        game_state: GameState,
        attack: Dict[CubeColor, int],
    ) -> CubeColor:
        self.choose_target_lock_color_called_with = list(tied_colors)
        if self.chosen_color_override is not None:
            return self.chosen_color_override
        return super().choose_target_lock_color(player, tied_colors, game_state, attack)


class TestTargetLockProtocol(unittest.TestCase):
    """Test suite verifying Target Lock Protocol and Operative Signature Cubes."""

    def setUp(self) -> None:
        self.config = GameConfig.v042(num_players=2)
        self.engine = GameEngine(config=self.config, seed=42)

    def test_tl_01_volume_conservation(self) -> None:
        """TEST-TL-01: Exactly 1 Signature Cube queued on triage secret banking (INV-TL-03)."""
        player = self.engine.state.players[0]
        player.triage_level = 4
        player.triage_bandwidth = 2
        player.signature_cube_location = SignatureCubeLocation.IDLE_ON_MAT
        self.engine.state.staging_signature_cubes.clear()

        # Place 3 dice with Secret faces into Processing Box
        player.glitched_dice.clear()
        for i in range(3):
            d = create_colored_die(DieColor.RED, die_id=100 + i)
            d.secret_pending = True
            player.glitched_dice.append(d)

        moved = conveyor_triage_v038(self.engine, player)
        self.assertEqual(len(moved), 2)
        # Invariant: exactly 1 signature cube in staging cup
        self.assertEqual(player.signature_cube_location, SignatureCubeLocation.STAGING_CUP)
        self.assertEqual(len(self.engine.state.staging_signature_cubes), 1)
        self.assertIn(player.player_id, self.engine.state.staging_signature_cubes)
        self.assertEqual(player.baffle_hold_visits, 1)

    def test_tl_02_no_duplication_on_successive_banking(self) -> None:
        """TEST-TL-02: No duplication when cube is already in tower (INV-TL-03)."""
        player = self.engine.state.players[0]
        player.signature_cube_location = SignatureCubeLocation.IN_TOWER
        self.engine.state.staging_signature_cubes.clear()

        d = create_colored_die(DieColor.RED, die_id=201)
        d.secret_pending = True
        player.glitched_dice = [d]

        conveyor_triage_v038(self.engine, player)
        self.assertEqual(player.signature_cube_location, SignatureCubeLocation.IN_TOWER)
        self.assertEqual(len(self.engine.state.staging_signature_cubes), 0)

    def test_tl_03_clean_exit_and_target_lock_activation(self) -> None:
        """TEST-TL-03: Exiting signature triggers Target Lock and returns to mat (INV-TL-05)."""
        player = self.engine.state.players[0]
        player.signature_cube_location = SignatureCubeLocation.STAGING_CUP
        self.engine.state.staging_signature_cubes = {player.player_id}

        # Mock tower drop such that signature exits
        tower = self.engine.state.tower
        tower.drop = MagicMock(return_value={CubeColor.RED: 1, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0})
        tower.last_exited_signatures = {player.player_id}
        tower.stuck_signatures = {}

        cr = execute_compiler_drop(self.engine, [])
        self.assertTrue(player.target_locked)
        self.assertEqual(player.signature_cube_location, SignatureCubeLocation.IDLE_ON_MAT)
        self.assertEqual(player.target_locks_triggered, 1)
        self.assertIn(player.player_id, cr.exited_signature_pids)
        self.assertEqual(len(self.engine.state.staging_signature_cubes), 0)

    def test_tl_04_baffle_trapping_and_hold_rounds(self) -> None:
        """TEST-TL-04: Trapped signature cube remains in tower and tracks baffle hold rounds."""
        player = self.engine.state.players[0]
        player.signature_cube_location = SignatureCubeLocation.STAGING_CUP
        self.engine.state.staging_signature_cubes = {player.player_id}

        tower = self.engine.state.tower
        tower.drop = MagicMock(return_value={CubeColor.RED: 1, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0})
        tower.last_exited_signatures = set()
        tower.stuck_signatures = {player.player_id: 1}

        cr = execute_compiler_drop(self.engine, [])
        self.assertFalse(player.target_locked)
        self.assertEqual(player.signature_cube_location, SignatureCubeLocation.IN_TOWER)
        self.assertEqual(player.target_lock_baffle_rounds, 1)
        self.assertEqual(player.baffle_hold_rounds_total, 1)
        self.assertIn(player.player_id, cr.stuck_signature_pids)

    def test_tl_05_dominant_color_single_max_attack_resolution(self) -> None:
        """TEST-TL-05: Target lock adds +1 of the unique dominant threat color (INV-TL-04)."""
        player = self.engine.state.players[0]
        player.target_locked = True
        player.init_market_share(15, 20)
        player.secrets = 5

        exited_cubes = {CubeColor.BLUE: 3, CubeColor.RED: 1, CubeColor.GREEN: 0, CubeColor.BLACK: 0}
        attack_strengths = {CubeColor.BLUE: 3, CubeColor.RED: 1, CubeColor.GREEN: 0}

        resolve_player_defense_and_wear(
            engine=self.engine,
            player=player,
            rolled_dice=[],
            commitments={},
            attack_strengths=attack_strengths,
            exited_cubes=exited_cubes,
            active_directive="NONE",
        )

        eff = player.last_defense_breakdown["effective_attacks"]
        self.assertEqual(eff["blue"], 4)  # 3 baseline + 1 extra
        self.assertEqual(eff["red"], 1)   # 1 baseline
        self.assertEqual(eff["green"], 0)
        self.assertEqual(player.last_defense_breakdown["target_lock_extra_color"], "blue")

    def test_tl_06_dominant_color_tie_resolution_agency(self) -> None:
        """TEST-TL-06: Defending player chooses between tied dominant colors (INV-TL-01)."""
        player = self.engine.state.players[0]
        stub_bot = StubBot(player.player_id)
        stub_bot.chosen_color_override = CubeColor.GREEN
        player.bot = stub_bot
        player.target_locked = True
        player.init_market_share(15, 20)

        exited_cubes = {CubeColor.RED: 2, CubeColor.GREEN: 2, CubeColor.BLUE: 0, CubeColor.BLACK: 0}
        attack_strengths = {CubeColor.RED: 2, CubeColor.GREEN: 2, CubeColor.BLUE: 0}

        resolve_player_defense_and_wear(
            engine=self.engine,
            player=player,
            rolled_dice=[],
            commitments={},
            attack_strengths=attack_strengths,
            exited_cubes=exited_cubes,
            active_directive="NONE",
        )

        eff = player.last_defense_breakdown["effective_attacks"]
        self.assertEqual(eff["red"], 2)
        self.assertEqual(eff["green"], 3)  # Chosen +1 Green
        self.assertEqual(eff["blue"], 0)
        self.assertCountEqual(stub_bot.choose_target_lock_color_called_with, [CubeColor.RED, CubeColor.GREEN])

    def test_tl_07_empty_tray_fizzle(self) -> None:
        """TEST-TL-07: Compile Buffer Overflow (0 exited cubes) cleanly fizzles Target Lock (INV-TL-02)."""
        player = self.engine.state.players[0]
        player.target_locked = True
        player.init_market_share(15, 20)
        player.secrets = 5

        exited_cubes = {CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0}
        attack_strengths = {CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0}

        resolve_player_defense_and_wear(
            engine=self.engine,
            player=player,
            rolled_dice=[],
            commitments={},
            attack_strengths=attack_strengths,
            exited_cubes=exited_cubes,
            active_directive="NONE",
        )

        eff = player.last_defense_breakdown["effective_attacks"]
        self.assertEqual(eff["red"], 0)
        self.assertEqual(eff["blue"], 0)
        self.assertEqual(eff["green"], 0)
        self.assertIsNone(player.last_defense_breakdown["target_lock_extra_color"])
        self.assertEqual(player.secrets, 5)

    def test_tl_08_only_black_cubes_fizzle(self) -> None:
        """TEST-TL-08: Drop with exclusively Black Corruption cubes cleanly fizzles Target Lock (INV-TL-02)."""
        player = self.engine.state.players[0]
        player.target_locked = True

        exited_cubes = {CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 3}
        attack_strengths = {CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0}

        extra = calculate_target_lock_extra_cube(self.engine, player, exited_cubes, attack_strengths)
        self.assertIsNone(extra)

    def test_tl_09_shield_absorption_and_defense_l4_payout(self) -> None:
        """TEST-TL-09: Extra Target Lock cube can be blocked and rewards Defense Grid L4 cash (INV-TL-04)."""
        player = self.engine.state.players[0]
        player.defense_level = 4
        player.defense_capacity = 4
        player.target_locked = True
        player.money = 0
        player.init_market_share(15, 20)

        exited_cubes = {CubeColor.RED: 1, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0}
        attack_strengths = {CubeColor.RED: 1, CubeColor.BLUE: 0, CubeColor.GREEN: 0}

        # 2 dice committing Block 1 Any shields
        d1 = create_gray_die(die_id=301)
        d1.current_face = Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)
        d2 = create_gray_die(die_id=302)
        d2.current_face = Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)
        rolled = [d1, d2]
        player.in_production_dice = list(rolled)
        commitments = {0: ShieldColor.ANY, 1: ShieldColor.ANY}

        resolve_player_defense_and_wear(
            engine=self.engine,
            player=player,
            rolled_dice=rolled,
            commitments=commitments,
            attack_strengths=attack_strengths,
            exited_cubes=exited_cubes,
            active_directive="NONE",
        )

        self.assertEqual(player.extra_attacks_absorbed, 1)
        self.assertEqual(player.extra_attacks_unblocked, 0)
        self.assertEqual(player.last_defense_breakdown["blocked"]["red"], 2)
        # Defense L4 gives $1 per blocked Attack Cube (2 blocked = $2)
        self.assertEqual(player.money, 2)

    def test_tl_10_snowball_recycle_purity(self) -> None:
        """TEST-TL-10: Target lock extra attack cube never recycles into staging cup (INV-TL-08)."""
        player = self.engine.state.players[0]
        player.target_locked = True
        self.engine.state.staging_cup = {c: 0 for c in CubeColor}

        exited_cubes = {CubeColor.BLUE: 2, CubeColor.RED: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0}
        cr = CompileResult(
            staged_before={},
            stuck_before={},
            exited_cubes=exited_cubes,
            stuck_after={},
        )

        finalize_attack_resolution(self.engine, cr)
        # Snowball recycle receives exactly the 2 physical cubes in exited_cubes
        self.assertEqual(self.engine.state.staging_cup[CubeColor.BLUE], 2)
        self.assertEqual(self.engine.state.staging_cup[CubeColor.RED], 0)
        self.assertFalse(player.target_locked)

    def test_tl_11_backward_compatibility_flag_parity(self) -> None:
        """TEST-TL-11: target_lock_enabled=False leaves engine 100% untouched (INV-TL-07)."""
        cfg_off = GameConfig.v040_roster(num_players=2, target_lock_enabled=False)
        eng_off = GameEngine(config=cfg_off, seed=42)

        # Run 2 full rounds
        eng_off.run_round()
        eng_off.run_round()

        for p in eng_off.state.players:
            self.assertEqual(p.target_locks_triggered, 0)
            self.assertEqual(p.signature_cube_location, SignatureCubeLocation.IDLE_ON_MAT)
            self.assertFalse(p.target_locked)
        self.assertEqual(len(eng_off.state.staging_signature_cubes), 0)


class TestTowerSignatureIntegration(unittest.TestCase):
    """Verifies Cube Tower physics integration with signature cubes."""

    def test_signature_mass_avalanche_trigger(self) -> None:
        """Adding signature cubes increases falling and stuck mass in Shogun tower mode."""
        cfg = GameConfig(
            tower_mode=TowerMode.SHOGUN_BAFFLE,
            tower_avalanche_stuck_threshold=3,
            tower_avalanche_mass_threshold=7,
        )
        from sim.tower import CubeTower
        tower = CubeTower(cfg)
        tower.reset()

        # 2 threat stuck, 1 signature stuck -> total_stuck = 3 (triggers avalanche!)
        tower.load_stuck({CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0})
        tower.load_stuck_signatures({1: 1})
        self.assertEqual(tower.total_stuck(), 3)
        self.assertEqual(tower.tower_regime(falling_count=1, stuck_count=tower.total_stuck()), "avalanche")


if __name__ == "__main__":
    unittest.main()
