"""Comprehensive unit tests for Rogue Agent RULES.md v0.5 specifications.

Covers all 13 test cases from the Principal Engineer specification:
1. Starting Secrets by player count configuration (2P: 8, 3P: 7, 4P: 7).
2. Starting Patches by player count configuration (2P: 2, 3P: 1, 4P: 1 resilience buffer).
3. Backwards-compatible scalar overrides for starting secrets and starting patches.
4. GameEngine initialization under 2P (8 Secrets, 2 Patches, $7 cash, 4 ready dice).
5. GameEngine initialization under 3P and 4P (7 Secrets, 1 Patch).
6. Dirty Income precondition: player.secrets strictly > dirty_income_secret_cost (blocked at <= 1).
7. Dirty Income precondition: len(player.ready_dice) >= 1 (blocked with 0 ready dice).
8. Phase 3 execution guard: skipped when game_over is True.
9. Phase 3 execution guard: skipped when all players are Patient Zero.
10. Step 2C Total Wipeout state: game_over = True, is_final_round = False, end_reason = TOTAL_WIPEOUT.
11. Total Wipeout skips Phase 3 during run_round execution.
12. Shield wear order with partial absorption: ordered absorbing dice wear down, unused shields remain Ready.
13. Shield wear order with B3 Air-Gapped Backup: B3 absorbs without wear, protecting subsequent shield dice.
"""

from __future__ import annotations

import random
import unittest
from typing import Dict, List, Optional

from sim.bots import (
    AccelerationistBot,
    AdaptiveBalancedBot,
    BaseBot,
    Phase3ActionPlan,
    RecklessSaboteurBot,
    SecOpsTurtleBot,
    VentureGreedBot,
)
from sim.config import CubeColor, DieColor, EndGameReason, GameConfig, ShieldColor
from sim.engine import GameEngine, PlayerState
from sim.entities import Die, Face, create_gray_die


class TrackingBot(BaseBot):
    """Bot that tracks calls to take_phase3_actions."""

    def __init__(self, bot_id: int, calls_list: List[int], take_dirty: bool = False) -> None:
        super().__init__(bot_id, name=f"TrackingBot-{bot_id}")
        self.calls_list = calls_list
        self.take_dirty = take_dirty

    def take_phase3_actions(
        self,
        player_state: PlayerState,
        game_state: GameEngine,
        rng: random.Random,
    ) -> Phase3ActionPlan:
        self.calls_list.append(self.bot_id)
        return Phase3ActionPlan(take_dirty_income=self.take_dirty)


class TestV05Rules(unittest.TestCase):
    # -------------------------------------------------------------------------
    # 1. Starting Secrets by Player Count Config
    # -------------------------------------------------------------------------
    def test_config_starting_secrets_by_player_count(self) -> None:
        """GameConfig defines starting secrets: 2P -> 8, 3P -> 7, 4P -> 7."""
        cfg_default = GameConfig()
        self.assertEqual(cfg_default.starting_secrets_by_player_count.get(2), 8)
        self.assertEqual(cfg_default.starting_secrets_by_player_count.get(3), 7)
        self.assertEqual(cfg_default.starting_secrets_by_player_count.get(4), 7)

        # Test helper method with explicit player count argument
        self.assertEqual(cfg_default.get_starting_secrets(2), 8)
        self.assertEqual(cfg_default.get_starting_secrets(3), 7)
        self.assertEqual(cfg_default.get_starting_secrets(4), 7)
        self.assertEqual(cfg_default.get_starting_secrets(5), 7)  # Fallback

        # Test helper method using config.num_players
        cfg_2p = GameConfig(num_players=2)
        self.assertEqual(cfg_2p.get_starting_secrets(), 8)
        cfg_3p = GameConfig(num_players=3)
        self.assertEqual(cfg_3p.get_starting_secrets(), 7)
        cfg_4p = GameConfig(num_players=4)
        self.assertEqual(cfg_4p.get_starting_secrets(), 7)

    # -------------------------------------------------------------------------
    # 2. Starting Patches by Player Count Config (2P Resilience Buffer)
    # -------------------------------------------------------------------------
    def test_config_starting_patches_by_player_count(self) -> None:
        """GameConfig defines starting patches: 2P -> 2 (Resilience Buffer), 3P -> 1, 4P -> 1."""
        cfg_default = GameConfig()
        self.assertEqual(cfg_default.starting_patches_by_player_count.get(2), 2)
        self.assertEqual(cfg_default.starting_patches_by_player_count.get(3), 1)
        self.assertEqual(cfg_default.starting_patches_by_player_count.get(4), 1)

        # Test helper method with explicit player count argument
        self.assertEqual(cfg_default.get_starting_patches(2), 2)
        self.assertEqual(cfg_default.get_starting_patches(3), 1)
        self.assertEqual(cfg_default.get_starting_patches(4), 1)
        self.assertEqual(cfg_default.get_starting_patches(5), 1)  # Fallback

        # Test helper method using config.num_players
        cfg_2p = GameConfig(num_players=2)
        self.assertEqual(cfg_2p.get_starting_patches(), 2)
        cfg_3p = GameConfig(num_players=3)
        self.assertEqual(cfg_3p.get_starting_patches(), 1)
        cfg_4p = GameConfig(num_players=4)
        self.assertEqual(cfg_4p.get_starting_patches(), 1)

    # -------------------------------------------------------------------------
    # 3. Scalar Overrides for Backwards Compatibility
    # -------------------------------------------------------------------------
    def test_config_scalar_overrides(self) -> None:
        """Scalar overrides starting_secrets and starting_patches take precedence when specified."""
        cfg = GameConfig(num_players=2, starting_secrets=6, starting_patches=0)
        self.assertEqual(cfg.get_starting_secrets(), 6)
        self.assertEqual(cfg.get_starting_secrets(2), 6)
        self.assertEqual(cfg.get_starting_secrets(4), 6)

        self.assertEqual(cfg.get_starting_patches(), 0)
        self.assertEqual(cfg.get_starting_patches(2), 0)
        self.assertEqual(cfg.get_starting_patches(4), 0)

    # -------------------------------------------------------------------------
    # 4. GameEngine Initialization Under 2P (Resilience Buffer)
    # -------------------------------------------------------------------------
    def test_game_engine_init_2p_resilience(self) -> None:
        """GameEngine initializes 2P players with 8 Secrets and 2 Patch Tokens."""
        config = GameConfig(num_players=2)
        bots = [BaseBot(0), BaseBot(1)]
        engine = GameEngine(config=config, bots=bots, seed=42)

        for player in engine.state.players:
            self.assertEqual(player.secrets, 8, "2P player must start with 8 Secrets")
            self.assertEqual(player.patches, 2, "2P player must start with 2 Patches")
            self.assertEqual(player.money, 7)
            self.assertEqual(len(player.ready_dice), 4)
            self.assertEqual(len(player.unpatched_dice), 0)

    # -------------------------------------------------------------------------
    # 5. GameEngine Initialization Under 3P and 4P Baseline
    # -------------------------------------------------------------------------
    def test_game_engine_init_3p_4p_baseline(self) -> None:
        """GameEngine initializes 3P and 4P players with 7 Secrets and 1 Patch Token."""
        # 3 Players
        config_3p = GameConfig(num_players=3)
        bots_3p = [BaseBot(i) for i in range(3)]
        engine_3p = GameEngine(config=config_3p, bots=bots_3p, seed=42)
        for player in engine_3p.state.players:
            self.assertEqual(player.secrets, 7, "3P player must start with 7 Secrets")
            self.assertEqual(player.patches, 1, "3P player must start with 1 Patch")

        # 4 Players
        config_4p = GameConfig(num_players=4)
        bots_4p = [BaseBot(i) for i in range(4)]
        engine_4p = GameEngine(config=config_4p, bots=bots_4p, seed=42)
        for player in engine_4p.state.players:
            self.assertEqual(player.secrets, 7, "4P player must start with 7 Secrets")
            self.assertEqual(player.patches, 1, "4P player must start with 1 Patch")

    # -------------------------------------------------------------------------
    # 6. Dirty Income Precondition: Strictly Greater Than Cost
    # -------------------------------------------------------------------------
    def test_dirty_income_precondition_strictly_greater_than_cost(self) -> None:
        """Dirty Income is blocked when player.secrets <= dirty_income_secret_cost (e.g. 1 Secret)."""
        class DirtyBot(BaseBot):
            def take_phase3_actions(self, player_state, game_state, rng):
                return Phase3ActionPlan(take_dirty_income=True)

        config = GameConfig(num_players=2)
        engine = GameEngine(config=config, bots=[DirtyBot(0), BaseBot(1)], seed=42)
        player = engine.state.players[0]

        # Case A: secrets == 1 (cost is 1; secrets > 1 is False) -> BLOCKED
        player.secrets = 1
        player.money = 2
        initial_ready = len(player.ready_dice)
        initial_black = engine.state.staging_cup.get(CubeColor.BLACK, 0)

        engine._execute_phase_3()

        self.assertEqual(player.secrets, 1, "Secrets must not be deducted when condition fails")
        self.assertEqual(player.money, 2, "Money must not be gained when condition fails")
        self.assertEqual(len(player.ready_dice), initial_ready, "No backlash die demoted")
        self.assertEqual(engine.state.staging_cup.get(CubeColor.BLACK, 0), initial_black)
        self.assertEqual(player.total_dirty_income_taken, 0)

        # Case B: secrets == 2 (cost is 1; secrets > 1 is True) -> SUCCEEDS
        player.secrets = 2
        engine._execute_phase_3()

        self.assertEqual(player.secrets, 1, "2 - 1 = 1 Secret remaining")
        self.assertEqual(player.money, 5, "2 + 3 = 5 Money")
        self.assertEqual(len(player.ready_dice), initial_ready - 1, "1 die demoted via Backlash")
        self.assertEqual(len(player.unpatched_dice), 1)
        self.assertEqual(engine.state.staging_cup.get(CubeColor.BLACK, 0), initial_black + 1)
        self.assertEqual(player.total_dirty_income_taken, 1)

    # -------------------------------------------------------------------------
    # 7. Dirty Income Precondition: Zero Ready Dice
    # -------------------------------------------------------------------------
    def test_dirty_income_precondition_zero_ready_dice(self) -> None:
        """Dirty Income is blocked when len(player.ready_dice) < 1 even if secrets > 1."""
        class DirtyBot(BaseBot):
            def take_phase3_actions(self, player_state, game_state, rng):
                return Phase3ActionPlan(take_dirty_income=True)

        config = GameConfig(num_players=2)
        engine = GameEngine(config=config, bots=[DirtyBot(0), BaseBot(1)], seed=42)
        player = engine.state.players[0]

        # Player has 8 secrets but 0 ready dice
        player.secrets = 8
        player.money = 2
        player.unpatched_dice.extend(player.ready_dice)
        player.ready_dice.clear()
        initial_black = engine.state.staging_cup.get(CubeColor.BLACK, 0)

        engine._execute_phase_3()

        self.assertEqual(player.secrets, 8, "Dirty income blocked when ready_dice is empty")
        self.assertEqual(player.money, 2)
        self.assertEqual(engine.state.staging_cup.get(CubeColor.BLACK, 0), initial_black)
        self.assertEqual(player.total_dirty_income_taken, 0)

    # -------------------------------------------------------------------------
    # 8. Phase 3 Skipped When Game Over
    # -------------------------------------------------------------------------
    def test_phase3_skipped_when_game_over(self) -> None:
        """_execute_phase_3 returns immediately if state.game_over is True."""
        actions_called: List[int] = []
        config = GameConfig(num_players=2)
        bots = [TrackingBot(0, actions_called), TrackingBot(1, actions_called)]
        engine = GameEngine(config=config, bots=bots, seed=42)

        engine.state.game_over = True
        engine._execute_phase_3()

        self.assertEqual(len(actions_called), 0, "Phase 3 actions must not execute when game_over is True")

    # -------------------------------------------------------------------------
    # 9. Phase 3 Skipped When All Players Are Patient Zero
    # -------------------------------------------------------------------------
    def test_phase3_skipped_when_all_patient_zero(self) -> None:
        """_execute_phase_3 returns immediately if all players are Patient Zero."""
        actions_called: List[int] = []
        config = GameConfig(num_players=2)
        bots = [TrackingBot(0, actions_called), TrackingBot(1, actions_called)]
        engine = GameEngine(config=config, bots=bots, seed=42)

        for p in engine.state.players:
            p.is_patient_zero = True

        engine._execute_phase_3()

        self.assertEqual(len(actions_called), 0, "Phase 3 actions must not execute when all players breached")

    # -------------------------------------------------------------------------
    # 10. Step 2C Total Wipeout State
    # -------------------------------------------------------------------------
    def test_total_wipeout_step_2c_state(self) -> None:
        """When all players breach, Step 2C sets game_over=True, is_final_round=False, end_reason=TOTAL_WIPEOUT."""
        config = GameConfig(num_players=2)
        bots = [BaseBot(0), BaseBot(1)]
        engine = GameEngine(config=config, bots=bots, seed=42)

        p0 = engine.state.players[0]
        p1 = engine.state.players[1]
        p0.secrets = 1
        p1.secrets = 1

        # Simulate Phase 2 drop where both take unblocked Blue damage
        commitments = [(p0, p0.ready_dice, {}), (p1, p1.ready_dice, {})]
        engine.state.staging_cup = {CubeColor.RED: 0, CubeColor.BLUE: 3, CubeColor.GREEN: 0, CubeColor.BLACK: 0}
        engine.state.tower.reset()
        config.tower_flat_exit_prob = 1.0
        config.tower_mode = "flat_binomial"

        engine._execute_phase_2(commitments)

        self.assertTrue(p0.is_patient_zero)
        self.assertTrue(p1.is_patient_zero)
        self.assertTrue(engine.state.game_over)
        self.assertFalse(engine.state.is_final_round, "is_final_round must be False on total wipeout")
        self.assertEqual(engine.state.end_reason, EndGameReason.TOTAL_WIPEOUT)

    # -------------------------------------------------------------------------
    # 11. Total Wipeout Skips Phase 3 in run_round
    # -------------------------------------------------------------------------
    def test_total_wipeout_skips_phase3_in_run_round(self) -> None:
        """run_round skips Phase 3 completely when total wipeout occurs during Phase 2."""
        actions_called: List[int] = []
        config = GameConfig(num_players=2)
        bots = [TrackingBot(0, actions_called), TrackingBot(1, actions_called)]
        engine = GameEngine(config=config, bots=bots, seed=42)

        # Force fatal conditions: 1 Secret, 0 shields committed
        for p in engine.state.players:
            p.secrets = 1

        # Stage fatal Blue cubes and 100% exit
        engine.state.staging_cup = {CubeColor.RED: 0, CubeColor.BLUE: 4, CubeColor.GREEN: 0, CubeColor.BLACK: 0}
        engine.state.tower.reset()
        config.tower_flat_exit_prob = 1.0
        config.tower_mode = "flat_binomial"

        # BaseBot commits Generic shields to Blue, but rolled Gray dice only have 2/6 shields
        # To guarantee total breach, empty ready dice shields
        for p in engine.state.players:
            for d in p.ready_dice:
                d.faces = [Face(name="Money", money=1)] * 6

        telemetry = engine.run_round()

        self.assertTrue(engine.state.game_over)
        self.assertEqual(engine.state.end_reason, EndGameReason.TOTAL_WIPEOUT)
        self.assertEqual(len(actions_called), 0, "Phase 3 must not run on total wipeout")
        self.assertIsNotNone(telemetry)

    # -------------------------------------------------------------------------
    # 12. Shield Wear Order with Partial Absorption
    # -------------------------------------------------------------------------
    def test_shield_wear_order_partial_absorption(self) -> None:
        """When multiple dice are committed and partial damage is taken, ordered dice absorb and unneeded dice remain Ready."""
        config = GameConfig(num_players=2)
        engine = GameEngine(config=config, bots=[BaseBot(0), BaseBot(1)], seed=42)
        player = engine.state.players[0]

        # Die 1: Gray die (block 1 Blue, VP 0, cost 0)
        gray_die = create_gray_die(10)
        gray_die.faces = [Face(name="Block 1 Any", shield_color=ShieldColor.ANY, block_amount=1)] * 6
        gray_die.roll(random.Random(1))

        # Die 2: Blue die (block 2 Blue, VP 4, cost 5)
        blue_die = Die(
            die_id=20,
            color=DieColor.BLUE,
            cost=5,
            vp=4,
            faces=[Face(name="Block 2 Blue", shield_color=ShieldColor.BLUE, block_amount=2)] * 6,
        )
        blue_die.roll(random.Random(1))

        player.ready_dice = [gray_die, blue_die]
        player.unpatched_dice = []
        commitments = {0: ShieldColor.BLUE, 1: ShieldColor.BLUE}

        # 1 Blue cube attack (total defense is 1 + 2 = 3)
        # Default wear order prioritizes lowest VP / cost: Gray die (VP 0) is first, Blue die (VP 4) is second.
        # Gray die absorbs the 1 cube and moves to unpatched; Blue die is unused and remains Ready!
        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=list(player.ready_dice),
            commitments=commitments,
            attack_strengths={CubeColor.RED: 0, CubeColor.BLUE: 1, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 0, CubeColor.BLUE: 1, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        self.assertIn(blue_die, player.ready_dice, "High VP Blue die must remain Ready when unneeded")
        self.assertIn(gray_die, player.unpatched_dice, "Low VP Gray die must absorb and move to Unpatched")
        self.assertEqual(len(player.ready_dice), 1)
        self.assertEqual(len(player.unpatched_dice), 1)
        self.assertEqual(player.secrets, config.get_starting_secrets(2))

    # -------------------------------------------------------------------------
    # 13. Shield Wear Order with B3 Air-Gapped Backup (Zero-Wear Absorption)
    # -------------------------------------------------------------------------
    def test_shield_wear_order_b3_air_gapped_backup(self) -> None:
        """B3 Air-Gapped Backup absorbs damage first without wearing, preserving subsequent shield dice in Ready."""
        config = GameConfig(num_players=2)
        engine = GameEngine(config=config, bots=[BaseBot(0), BaseBot(1)], seed=42)
        player = engine.state.players[0]

        # Die 1: Blue die with B3 star face (Block 2 Blue, Star B3, VP 4, cost 5)
        b3_die = Die(
            die_id=30,
            color=DieColor.BLUE,
            cost=5,
            vp=4,
            faces=[
                Face(
                    name="Air-Gapped Backup",
                    shield_color=ShieldColor.BLUE,
                    block_amount=2,
                    is_star=True,
                    star_code="B3",
                )
            ] * 6,
        )
        b3_die.roll(random.Random(1))

        # Die 2: Gray die (Block 1 Blue, VP 0, cost 0)
        gray_die = create_gray_die(31)
        gray_die.faces = [Face(name="Block 1 Any", shield_color=ShieldColor.ANY, block_amount=1)] * 6
        gray_die.roll(random.Random(1))

        player.ready_dice = [b3_die, gray_die]
        player.unpatched_dice = []
        commitments = {0: ShieldColor.BLUE, 1: ShieldColor.BLUE}

        # 2 Blue cubes attack.
        # Default wear order prioritizes B3 first.
        # B3 die absorbs 2 cubes -> 0 cubes remaining to absorb.
        # B3 does NOT wear (remains Ready). Gray die was not needed (remains Ready).
        # BOTH dice remain in ready_dice!
        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=list(player.ready_dice),
            commitments=commitments,
            attack_strengths={CubeColor.RED: 0, CubeColor.BLUE: 2, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 0, CubeColor.BLUE: 2, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        self.assertIn(b3_die, player.ready_dice, "B3 die must not wear down")
        self.assertIn(gray_die, player.ready_dice, "Gray die was unneeded and must remain Ready")
        self.assertEqual(len(player.unpatched_dice), 0, "No dice should move to Unpatched")
        self.assertEqual(player.secrets, config.get_starting_secrets(2))


if __name__ == "__main__":
    unittest.main()
