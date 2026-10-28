"""Unit and Integration Tests for Compiler Priming & Buffer Overflow (v0.9.1 Baseline).

Covers all 16 technical verification tests across 4 test groups specified by the Principal Engineer:

Group A: Compiler Priming (Pre-Seed Drop) (Tests 1-4)
1. test_priming_enabled_by_default
2. test_priming_executes_on_engine_init
3. test_priming_exited_cubes_not_added_to_staging_cup
4. test_priming_disabled_configuration

Group B: Buffer Overflow Detection & Mechanics (Tests 5-8)
5. test_buffer_overflow_triggered_on_zero_exits
6. test_buffer_overflow_injects_rgb_into_staging_cup
7. test_buffer_overflow_no_corruption_no_damage
8. test_buffer_overflow_unused_shields_remain_ready

Group C: Multi-Round & Contractor Lifecycle during Buffer Overflow (Tests 9-12)
9. test_buffer_overflow_contractors_expire
10. test_buffer_overflow_flag_resets_on_normal_round
11. test_buffer_overflow_disabled_configuration
12. test_consecutive_buffer_overflows_accumulation

Group D: End Game, Telemetry, and Web Controller Integration (Tests 13-16)
13. test_end_game_result_records_total_buffer_overflows
14. test_round_telemetry_records_buffer_overflow
15. test_web_controller_priming_log_and_state
16. test_web_controller_compile_drop_buffer_overflow_event_log
"""

from __future__ import annotations

import random
import unittest
from typing import Dict, List

from sim.bots import AdaptiveBalancedBot
from sim.config import CubeColor, DieColor, GameConfig, ShieldColor, TowerMode
from sim.engine import GameEngine, PlayerState
from sim.entities import (
    Die,
    Face,
    create_gray_die,
    create_white_die,
    get_default_variant_cards,
    get_default_version_deck,
)
from web.controller import GameController


class TestCompilerPrimingAndBufferOverflow(unittest.TestCase):
    """Test suite covering Compiler Buffer Overflow & Tower Priming for v0.9.1."""

    def setUp(self) -> None:
        self.config = GameConfig(num_players=4)
        self.bots = [AdaptiveBalancedBot(i) for i in range(4)]

    # =========================================================================
    # Group A: Compiler Priming (Pre-Seed Drop) (Tests 1-4)
    # =========================================================================

    def test_priming_enabled_by_default(self) -> None:
        """1. Verify GameConfig has priming and overflow enabled by default with correct cube payloads."""
        cfg = GameConfig()
        self.assertTrue(cfg.enable_compiler_priming)
        self.assertEqual(
            cfg.compiler_priming_cubes,
            {
                CubeColor.RED: 1,
                CubeColor.BLUE: 1,
                CubeColor.GREEN: 1,
                CubeColor.BLACK: 1,
            },
        )
        self.assertTrue(cfg.enable_buffer_overflow)
        self.assertEqual(
            cfg.buffer_overflow_cubes,
            {
                CubeColor.RED: 1,
                CubeColor.BLUE: 1,
                CubeColor.GREEN: 1,
            },
        )

    def test_priming_executes_on_engine_init(self) -> None:
        """2. Verify GameEngine.__init__ executes _prime_compiler, recording exited and stuck cubes."""
        engine = GameEngine(config=self.config, bots=self.bots, seed=42)

        # Invariant: for each color, exited + stuck == compiler_priming_cubes
        total_accounted = 0
        for color, initial_count in self.config.compiler_priming_cubes.items():
            exited = engine.state.priming_exited_cubes.get(color, 0)
            stuck = engine.state.priming_stuck_cubes.get(color, 0)
            self.assertEqual(
                exited + stuck,
                initial_count,
                f"Mismatch for color {color}: exited={exited}, stuck={stuck}",
            )
            total_accounted += exited + stuck

        self.assertEqual(total_accounted, 4)

        # Tower stuck cubes must exactly match priming_stuck_cubes
        self.assertEqual(engine.state.tower.stuck_cubes, engine.state.priming_stuck_cubes)
        self.assertEqual(
            engine.state.tower.total_stuck(),
            sum(engine.state.priming_stuck_cubes.values()),
        )

    def test_priming_exited_cubes_not_added_to_staging_cup(self) -> None:
        """3. Verify cubes exiting the tower during priming return to supply and are not in staging_cup."""
        engine = GameEngine(config=self.config, bots=self.bots, seed=42)

        # Staging cup should strictly contain the starting payload of the v1.0 card (1 R, 1 B, 1 G, 1 Black)
        starting_v1_payload = engine.version_deck[0].get_staging_payload(self.config.num_players)
        for color in CubeColor:
            expected = starting_v1_payload.get(color, 0)
            actual = engine.state.staging_cup.get(color, 0)
            self.assertEqual(
                actual,
                expected,
                f"Staging cup cube count for {color} should match v1.0 payload ({expected}), got {actual}",
            )

    def test_priming_disabled_configuration(self) -> None:
        """4. Verify that when enable_compiler_priming=False, the tower starts completely empty."""
        cfg = GameConfig(num_players=4, enable_compiler_priming=False)
        engine = GameEngine(config=cfg, bots=self.bots, seed=42)

        self.assertEqual(engine.state.tower.total_stuck(), 0)
        for color in CubeColor:
            self.assertEqual(engine.state.priming_exited_cubes.get(color, 0), 0)
            self.assertEqual(engine.state.priming_stuck_cubes.get(color, 0), 0)
            self.assertEqual(engine.state.tower.stuck_cubes.get(color, 0), 0)

    # =========================================================================
    # Group B: Buffer Overflow Detection & Mechanics (Tests 5-8)
    # =========================================================================

    def test_buffer_overflow_triggered_on_zero_exits(self) -> None:
        """5. Verify buffer overflow is triggered and tracked when 0 cubes exit in Phase 2."""
        cfg = GameConfig(
            num_players=4,
            tower_mode=TowerMode.FLAT_BINOMIAL,
            tower_flat_exit_prob=0.0,
        )
        engine = GameEngine(config=cfg, bots=self.bots, seed=10)

        # Phase 1
        commitments = engine._execute_phase_1()

        # Phase 2
        telemetry = engine._execute_phase_2(commitments)

        self.assertTrue(telemetry.buffer_overflow)
        self.assertTrue(engine.state.last_round_buffer_overflow)
        self.assertEqual(engine.state.total_buffer_overflows, 1)
        self.assertEqual(sum(telemetry.exited_cubes.values()), 0)

    def test_buffer_overflow_injects_rgb_into_staging_cup(self) -> None:
        """6. Verify buffer overflow injects 1 Red, 1 Blue, and 1 Green cube into staging_cup."""
        cfg = GameConfig(
            num_players=4,
            tower_mode=TowerMode.FLAT_BINOMIAL,
            tower_flat_exit_prob=0.0,
        )
        engine = GameEngine(config=cfg, bots=self.bots, seed=10)

        commitments = engine._execute_phase_1()
        engine._execute_phase_2(commitments)

        # Buffer overflow cubes injected: 1 Red, 1 Blue, 1 Green
        self.assertEqual(engine.state.staging_cup[CubeColor.RED], 1)
        self.assertEqual(engine.state.staging_cup[CubeColor.BLUE], 1)
        self.assertEqual(engine.state.staging_cup[CubeColor.GREEN], 1)
        self.assertEqual(engine.state.staging_cup[CubeColor.BLACK], 0)

    def test_buffer_overflow_no_corruption_no_damage(self) -> None:
        """7. Verify 0 corruption advances and 0 damage is dealt to player cash, secrets, or dice."""
        cfg = GameConfig(
            num_players=4,
            tower_mode=TowerMode.FLAT_BINOMIAL,
            tower_flat_exit_prob=0.0,
        )
        engine = GameEngine(config=cfg, bots=self.bots, seed=10)

        commitments = engine._execute_phase_1()

        # Record player resource baselines after Phase 1 but before Phase 2
        initial_resources = [
            (p.money, p.secrets, p.patches, len(p.ready_dice), len(p.unpatched_dice))
            for p in engine.state.players
        ]

        engine._execute_phase_2(commitments)

        self.assertEqual(engine.state.corruption_track, 0)
        for i, p in enumerate(engine.state.players):
            init_m, init_s, init_p, init_ready, init_unp = initial_resources[i]
            # Secrets and patches must not decrease, ready dice must not be lost to unpatched
            self.assertEqual(p.money, init_m)
            self.assertEqual(p.secrets, init_s)
            self.assertEqual(p.patches, init_p)
            self.assertEqual(len(p.ready_dice), init_ready)
            self.assertEqual(len(p.unpatched_dice), init_unp)
            self.assertFalse(p.is_patient_zero)

    def test_buffer_overflow_unused_shields_remain_ready(self) -> None:
        """8. Verify committed permanent shield dice do not wear into unpatched during buffer overflow."""
        cfg = GameConfig(
            num_players=4,
            tower_mode=TowerMode.FLAT_BINOMIAL,
            tower_flat_exit_prob=0.0,
        )
        engine = GameEngine(config=cfg, bots=self.bots, seed=10)

        # Setup Player 0 with a Gray shield die committed to Red
        p0 = engine.state.players[0]
        p0.ready_dice.clear()
        p0.unpatched_dice.clear()
        shield_die = create_gray_die(1)
        shield_die.current_face = Face("Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)
        p0.ready_dice.append(shield_die)

        rolled = [shield_die]
        commitments_dict = {0: ShieldColor.RED}
        commitments = [(p0, rolled, commitments_dict)]
        for other in engine.state.players[1:]:
            commitments.append((other, [], {}))

        engine._execute_phase_2(commitments)

        # Shield was unused because 0 attacks landed; must remain in ready_dice
        self.assertIn(shield_die, p0.ready_dice)
        self.assertEqual(len(p0.unpatched_dice), 0)

    # =========================================================================
    # Group C: Multi-Round & Contractor Lifecycle during Buffer Overflow (Tests 9-12)
    # =========================================================================

    def test_buffer_overflow_contractors_expire(self) -> None:
        """9. Verify hired White Contractor dice expire and return to supply during buffer overflow."""
        cfg = GameConfig(
            num_players=4,
            tower_mode=TowerMode.FLAT_BINOMIAL,
            tower_flat_exit_prob=0.0,
        )
        engine = GameEngine(config=cfg, bots=self.bots, seed=10)

        p0 = engine.state.players[0]
        contractor = create_white_die(99)
        p0.contractor_dice.append(contractor)
        p0.hired_contractor_count = 1
        engine.state.contractor_supply -= 1

        self.assertEqual(engine.state.contractor_supply, 11)

        commitments = [(p, [], {}) for p in engine.state.players]
        engine._execute_phase_2(commitments)

        self.assertEqual(len(p0.contractor_dice), 0)
        self.assertEqual(p0.hired_contractor_count, 0)
        self.assertEqual(engine.state.contractor_supply, 12)

    def test_buffer_overflow_flag_resets_on_normal_round(self) -> None:
        """10. Verify last_round_buffer_overflow flag resets on a round with exits, while total persists."""
        cfg = GameConfig(
            num_players=4,
            tower_mode=TowerMode.FLAT_BINOMIAL,
            tower_flat_exit_prob=0.0,
        )
        engine = GameEngine(config=cfg, bots=self.bots, seed=10)

        # Round 1: 0 exits (overflow)
        commitments = engine._execute_phase_1()
        engine._execute_phase_2(commitments)
        self.assertTrue(engine.state.last_round_buffer_overflow)
        self.assertEqual(engine.state.total_buffer_overflows, 1)

        # Round 2: Change exit probability to 1.0 (all cubes exit)
        engine.config.tower_flat_exit_prob = 1.0
        commitments2 = engine._execute_phase_1()
        t2 = engine._execute_phase_2(commitments2)

        self.assertFalse(t2.buffer_overflow)
        self.assertFalse(engine.state.last_round_buffer_overflow)
        self.assertEqual(engine.state.total_buffer_overflows, 1)

    def test_buffer_overflow_disabled_configuration(self) -> None:
        """11. Verify that when enable_buffer_overflow=False, 0 exits does not trigger buffer overflow."""
        cfg = GameConfig(
            num_players=4,
            enable_buffer_overflow=False,
            tower_mode=TowerMode.FLAT_BINOMIAL,
            tower_flat_exit_prob=0.0,
        )
        engine = GameEngine(config=cfg, bots=self.bots, seed=10)

        commitments = engine._execute_phase_1()
        telemetry = engine._execute_phase_2(commitments)

        self.assertFalse(telemetry.buffer_overflow)
        self.assertFalse(engine.state.last_round_buffer_overflow)
        self.assertEqual(engine.state.total_buffer_overflows, 0)
        # Staging cup should have 0 recycled attack cubes since 0 exited
        self.assertEqual(engine.state.staging_cup[CubeColor.RED], 0)
        self.assertEqual(engine.state.staging_cup[CubeColor.BLUE], 0)
        self.assertEqual(engine.state.staging_cup[CubeColor.GREEN], 0)

    def test_consecutive_buffer_overflows_accumulation(self) -> None:
        """12. Verify consecutive buffer overflow rounds accumulate total_buffer_overflows and staging cubes."""
        cfg = GameConfig(
            num_players=4,
            tower_mode=TowerMode.FLAT_BINOMIAL,
            tower_flat_exit_prob=0.0,
        )
        engine = GameEngine(config=cfg, bots=self.bots, seed=10)

        # Round 1: overflow
        c1 = engine._execute_phase_1()
        engine._execute_phase_2(c1)
        self.assertEqual(engine.state.total_buffer_overflows, 1)
        self.assertEqual(engine.state.staging_cup[CubeColor.RED], 1)
        self.assertEqual(engine.state.staging_cup[CubeColor.BLUE], 1)
        self.assertEqual(engine.state.staging_cup[CubeColor.GREEN], 1)

        # Round 2: second overflow
        c2 = engine._execute_phase_1()
        engine._execute_phase_2(c2)
        self.assertEqual(engine.state.total_buffer_overflows, 2)
        self.assertTrue(engine.state.last_round_buffer_overflow)
        # R1's injected cubes were dropped into the tower and got stuck; R2 injects a new set into staging cup
        self.assertEqual(engine.state.staging_cup[CubeColor.RED], 1)
        self.assertEqual(engine.state.staging_cup[CubeColor.BLUE], 1)
        self.assertEqual(engine.state.staging_cup[CubeColor.GREEN], 1)
        # Total red cubes stuck in tower should include the dropped overflow cubes
        self.assertGreaterEqual(engine.state.tower.stuck_cubes[CubeColor.RED], 2)

    # =========================================================================
    # Group D: End Game, Telemetry, and Web Controller Integration (Tests 13-16)
    # =========================================================================

    def test_end_game_result_records_total_buffer_overflows(self) -> None:
        """13. Verify EndGameResult properly includes total_buffer_overflows."""
        cfg = GameConfig(
            num_players=4,
            tower_mode=TowerMode.FLAT_BINOMIAL,
            tower_flat_exit_prob=0.0,
        )
        engine = GameEngine(config=cfg, bots=self.bots, seed=10)

        c1 = engine._execute_phase_1()
        engine._execute_phase_2(c1)
        c2 = engine._execute_phase_1()
        engine._execute_phase_2(c2)

        result = engine.evaluate_end_game()
        self.assertEqual(result.total_buffer_overflows, 2)

    def test_round_telemetry_records_buffer_overflow(self) -> None:
        """14. Verify RoundTelemetry.buffer_overflow is recorded in telemetry_history."""
        cfg = GameConfig(
            num_players=4,
            tower_mode=TowerMode.FLAT_BINOMIAL,
            tower_flat_exit_prob=0.0,
        )
        engine = GameEngine(config=cfg, bots=self.bots, seed=10)

        # Round 1: overflow
        c1 = engine._execute_phase_1()
        t1 = engine._execute_phase_2(c1)
        self.assertTrue(t1.buffer_overflow)

        # Round 2: normal drop
        engine.config.tower_flat_exit_prob = 1.0
        c2 = engine._execute_phase_1()
        t2 = engine._execute_phase_2(c2)
        self.assertFalse(t2.buffer_overflow)

        self.assertTrue(engine.telemetry_history[0].buffer_overflow)
        self.assertFalse(engine.telemetry_history[1].buffer_overflow)

    def test_web_controller_priming_log_and_state(self) -> None:
        """15. Verify GameController logs compiler priming and exposes priming state in get_full_state."""
        controller = GameController()
        state_dict = controller.new_game(num_players=4, seed=42)

        # Event log should contain Compiler Primed message
        log_text = " ".join(controller.event_log)
        self.assertIn("Compiler Primed:", log_text)

        # State dictionary should serialize priming and buffer overflow fields
        self.assertIn("priming_exited_cubes", state_dict)
        self.assertIn("priming_stuck_cubes", state_dict)
        self.assertIn("last_round_buffer_overflow", state_dict)
        self.assertIn("total_buffer_overflows", state_dict)
        self.assertEqual(state_dict["total_buffer_overflows"], 0)
        self.assertFalse(state_dict["last_round_buffer_overflow"])

    def test_web_controller_compile_drop_buffer_overflow_event_log(self) -> None:
        """16. Verify GameController.compile_drop logs buffer overflow and updates last_compile_result."""
        controller = GameController()
        controller.new_game(num_players=4, seed=42)

        # Set tower to 0 exit probability
        controller.state.config.tower_mode = TowerMode.FLAT_BINOMIAL
        controller.state.config.tower_flat_exit_prob = 0.0

        # Advance to Phase 2
        controller.phase = 2
        controller.phase_name = "Rogue Agent Compile"
        controller.subphase = "ready_for_compile"

        # Execute compile drop
        state_dict = controller.compile_drop()

        self.assertIsNotNone(controller.last_compile_result)
        self.assertTrue(controller.last_compile_result.get("buffer_overflow"))
        self.assertTrue(state_dict.get("last_round_buffer_overflow"))
        self.assertEqual(state_dict.get("total_buffer_overflows"), 1)

        # Check event log
        log_text = " ".join(controller.event_log)
        self.assertIn("BUFFER OVERFLOW!", log_text)


if __name__ == "__main__":
    unittest.main()
