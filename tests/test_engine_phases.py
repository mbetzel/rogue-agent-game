"""Unit tests for Phase 1, Phase 2, and Phase 3 mechanics in GameEngine."""

import unittest

from sim.bots import AdaptiveBalancedBot, BaseBot, Phase3ActionPlan
from sim.config import CubeColor, DieColor, EndGameReason, GameConfig, ShieldColor
from sim.engine import GameEngine
from sim.entities import Face, create_colored_die, create_gray_die


class DummyControlledBot(BaseBot):
    """Bot for strictly deterministic phase assertions."""

    def __init__(self, bot_id: int) -> None:
        super().__init__(bot_id, name="DummyControlledBot")
        self.next_rerolls: list[int] = []
        self.next_commitments: dict[int, ShieldColor] = {}
        self.next_plan = Phase3ActionPlan()

    def choose_hotfix_rerolls(self, *args, **kwargs) -> list[int]:
        return self.next_rerolls

    def commit_shields(self, *args, **kwargs) -> dict[int, ShieldColor]:
        return self.next_commitments

    def take_phase3_actions(self, *args, **kwargs) -> Phase3ActionPlan:
        return self.next_plan


class TestEnginePhases(unittest.TestCase):
    def test_phase1_boot_and_configure(self) -> None:
        cfg = GameConfig(num_players=2, starting_money=5, starting_secrets=6, starting_patches=1)
        bot0 = DummyControlledBot(0)
        bot1 = DummyControlledBot(1)
        engine = GameEngine(cfg, [bot0, bot1], seed=42)

        # Force specific faces on player 0's dice
        p0 = engine.state.players[0]
        p0.ready_dice[0].current_face = Face("+$1", money=1)
        p0.ready_dice[1].current_face = Face("+1 🔧", patches=1)
        p0.ready_dice[2].current_face = Face("Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)
        p0.ready_dice[3].current_face = Face("Idle (0)")

        # Verify immediate collection logic
        engine._apply_immediate_face_outputs(p0)
        self.assertEqual(p0.money, 6)  # 5 + 1
        self.assertEqual(p0.patches, 2)  # 1 + 1

    def test_hotfix_reroll_costs_patch_token(self) -> None:
        cfg = GameConfig(num_players=2, starting_patches=2)
        bot0 = DummyControlledBot(0)
        bot1 = DummyControlledBot(1)
        bot0.next_rerolls = [0]  # Request reroll on index 0
        engine = GameEngine(cfg, [bot0, bot1], seed=10)

        p0 = engine.state.players[0]
        # Override die.roll on all p0 dice to return Idle (0) to eliminate random patch face gains
        for d in p0.ready_dice:
            d.roll = lambda rng=None: Face("Idle (0)")

        p0.patches = 2
        engine._execute_phase_1()

        # Started with 2 patches, spent 1 on hotfix reroll, gained 0 from Idle -> exactly 1 left
        self.assertEqual(p0.patches, 1)

    def test_phase2_black_cubes_and_version_upgrade(self) -> None:
        cfg = GameConfig(num_players=2)  # corruption track = 2 + 1 = 3 spaces
        bot0 = DummyControlledBot(0)
        bot1 = DummyControlledBot(1)
        engine = GameEngine(cfg, [bot0, bot1], seed=1)

        # Force 100% exit probability
        engine.state.tower.calculate_exit_probability = lambda count: 1.0

        # Stage 3 Black cubes to fill v1.0 track (Script Kiddie -> RaaS)
        engine.state.staging_cup = {CubeColor.BLACK: 3, CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0}

        commitments = [(engine.state.players[0], engine.state.players[0].ready_dice, {}),
                       (engine.state.players[1], engine.state.players[1].ready_dice, {})]

        self.assertEqual(engine.state.current_version_index, 0)
        engine._execute_phase_2(commitments)

        # Version should advance to v2.0 (index 1)
        self.assertEqual(engine.state.current_version_index, 1)
        self.assertEqual(engine.state.corruption_track, 0)
        # RaaS upgrade payload (+2 Red, +1 Green) should now be in Staging Cup
        self.assertEqual(engine.state.staging_cup[CubeColor.RED], 2)
        self.assertEqual(engine.state.staging_cup[CubeColor.GREEN], 1)

    def test_phase2_singularity_trigger_on_v3(self) -> None:
        cfg = GameConfig(num_players=2)
        bot0 = DummyControlledBot(0)
        bot1 = DummyControlledBot(1)
        engine = GameEngine(cfg, [bot0, bot1], seed=1)
        engine.state.tower.calculate_exit_probability = lambda count: 1.0

        # Set version to v3.0 (index 2)
        engine.state.current_version_index = 2
        engine.state.corruption_track = 2  # 1 space away from full (cap = 3)

        engine.state.staging_cup = {CubeColor.BLACK: 1, CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0}
        commitments = [(engine.state.players[0], engine.state.players[0].ready_dice, {}),
                       (engine.state.players[1], engine.state.players[1].ready_dice, {})]

        engine._execute_phase_2(commitments)

        self.assertTrue(engine.state.singularity_triggered)
        self.assertTrue(engine.state.is_final_round)
        self.assertFalse(engine.state.game_over)
        self.assertEqual(engine.state.end_reason, EndGameReason.SINGULARITY)

    def test_phase3_operations_and_turn_rotation(self) -> None:
        cfg = GameConfig(num_players=2, starting_money=10, starting_patches=1)
        bot0 = DummyControlledBot(0)
        bot1 = DummyControlledBot(1)

        # Player 0 takes Dirty Income and buys 1 Blue die ($5)
        bot0.next_plan = Phase3ActionPlan(
            take_dirty_income=True,
            dirty_income_cube_choice=CubeColor.RED,
            market_purchases=[DieColor.BLUE],
        )

        engine = GameEngine(cfg, [bot0, bot1], seed=42)
        p0 = engine.state.players[0]
        initial_money = p0.money  # 10
        initial_market_blue = engine.state.market[DieColor.BLUE]
        initial_staging_red = engine.state.staging_cup[CubeColor.RED]
        initial_staging_black = engine.state.staging_cup[CubeColor.BLACK]
        engine.state.first_player_index = 0

        engine._execute_phase_3()

        # Money: 10 + 3 (dirty) - 5 (market) = 8
        self.assertEqual(p0.money, 8)
        self.assertEqual(p0.total_dirty_income_taken, 1)
        self.assertEqual(engine.state.staging_cup[CubeColor.BLACK], initial_staging_black + 1)
        self.assertEqual(engine.state.staging_cup[CubeColor.RED], initial_staging_red)
        self.assertEqual(engine.state.market[DieColor.BLUE], initial_market_blue - 1)
        self.assertTrue(any(d.color == DieColor.BLUE for d in p0.ready_dice))

        # First player index should rotate
        self.assertEqual(engine.state.first_player_index, 1)

    def test_hotfix_reroll_does_not_retain_old_face_output(self) -> None:
        """Verify that rerolling a die discards its initial face output (no double-dipping)."""
        cfg = GameConfig(num_players=2, starting_money=5, starting_patches=1)
        bot0 = DummyControlledBot(0)
        bot1 = DummyControlledBot(1)
        bot0.next_rerolls = [0]  # Reroll die 0
        engine = GameEngine(cfg, [bot0, bot1], seed=10)

        p0 = engine.state.players[0]
        # Die 0 initially rolls +$2, but is rerolled into Idle (0)
        # Other dice roll Idle (0)
        rolls = [Face("+$2", money=2), Face("Idle (0)")]

        def roll_sequence(rng=None):
            return rolls.pop(0) if rolls else Face("Idle (0)")

        p0.ready_dice[0].roll = roll_sequence
        for d in p0.ready_dice[1:]:
            d.roll = lambda rng=None: Face("Idle (0)")

        engine._execute_phase_1()

        # Money must remain $5 (the +$2 was discarded), patches should be 0 (1 spent on reroll)
        self.assertEqual(p0.money, 5)
        self.assertEqual(p0.patches, 0)


if __name__ == "__main__":
    unittest.main()
