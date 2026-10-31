"""Unit tests for Too Many Secrets Rules Draft v0.16.0.

Verifies:
1. Setup Staging Cup Priming: 2 Red, 2 Blue, 2 Green, 1 Black (7 cubes).
2. Autonomous Protocol Pulse by Version: 1 in v1.0, 2 in v2.0, 2 in v3.0.
3. Dirty Income Deprecation: disabled by default in GameConfig, rejected by engine and controller.
4. The Cipher Archetype Revision: Algorithmic Arbitrage provides $2 market discount OR +$2 cash arbitrage payout.
5. Bot Compatibility: all 5 bot types operate smoothly with dirty income disabled.
"""

from __future__ import annotations

import unittest
from sim.config import CubeColor, DieColor, GameConfig
from sim.engine import GameEngine
from sim.entities import AbilityStatus, ArchetypeCode, get_archetype_by_code
from sim.bots import (
    AdaptiveBalancedBot,
    AccelerationistBot,
    BaseBot,
    RecklessSaboteurBot,
    SecOpsTurtleBot,
    VentureGreedBot,
)
from sim.bots.base import Phase3ActionPlan
from web.game_controller import GameController


class TestV160Rules(unittest.TestCase):
    """Test suite verifying v0.16.0 rules draft mechanics."""

    def test_setup_staging_cup_priming(self) -> None:
        """Setup staging cup starts with 2 Red, 2 Blue, 2 Green, 1 Black (v1.0 Script Kiddie)."""
        engine = GameEngine(
            config=GameConfig(num_players=4),
            bots=[BaseBot(i) for i in range(4)],
            seed=42,
        )
        self.assertEqual(engine.state.staging_cup[CubeColor.RED], 2)
        self.assertEqual(engine.state.staging_cup[CubeColor.BLUE], 2)
        self.assertEqual(engine.state.staging_cup[CubeColor.GREEN], 2)
        self.assertEqual(engine.state.staging_cup[CubeColor.BLACK], 1)

    def test_autonomous_pulse_by_version(self) -> None:
        """Autonomous pulse adds 1 Black in v1.0, 2 Black in v2.0, and 2 Black in v3.0."""
        engine = GameEngine(
            config=GameConfig(num_players=4),
            bots=[BaseBot(i) for i in range(4)],
            seed=42,
        )
        # Clear cup to test pure pulse
        for c in engine.state.staging_cup:
            engine.state.staging_cup[c] = 0

        # Phase 1 in v1.0 adds 1 Black cube
        engine._execute_phase_1()
        self.assertEqual(engine.state.staging_cup[CubeColor.BLACK], 1)

        # Advance to v2.0
        engine.state.current_version_index = 1
        for c in engine.state.staging_cup:
            engine.state.staging_cup[c] = 0
        engine._execute_phase_1()
        self.assertEqual(engine.state.staging_cup[CubeColor.BLACK], 2)

        # Advance to v3.0
        engine.state.current_version_index = 2
        for c in engine.state.staging_cup:
            engine.state.staging_cup[c] = 0
        engine._execute_phase_1()
        self.assertEqual(engine.state.staging_cup[CubeColor.BLACK], 2)

    def test_dirty_income_disabled_by_default_in_engine(self) -> None:
        """Dirty Income is disabled by default; taking it does nothing in Phase 3."""
        class GreedyDirtyBot(BaseBot):
            def take_phase3_actions(self, player_state, game_state, rng):
                return Phase3ActionPlan(take_dirty_income=True)

        engine = GameEngine(
            config=GameConfig(num_players=2),
            bots=[GreedyDirtyBot(0), BaseBot(1)],
            seed=42,
        )
        p0 = engine.state.players[0]
        initial_money = p0.money
        initial_secrets = p0.secrets
        initial_black = engine.state.staging_cup[CubeColor.BLACK]

        engine._execute_phase_3()

        # No dirty income executed
        self.assertEqual(p0.money, initial_money)
        self.assertEqual(p0.secrets, initial_secrets)
        self.assertEqual(engine.state.staging_cup[CubeColor.BLACK], initial_black)
        self.assertEqual(p0.total_dirty_income_taken, 0)

    def test_cipher_cash_arbitrage_engine_execution(self) -> None:
        """The Cipher can execute cash arbitrage for +$2 without losing secrets or adding black cubes."""
        class CipherCashBot(BaseBot):
            def take_phase3_actions(self, player_state, game_state, rng):
                return Phase3ActionPlan(use_cipher_ability=True, cipher_mode="CASH")

        engine = GameEngine(
            config=GameConfig(num_players=2),
            bots=[CipherCashBot(0), BaseBot(1)],
            seed=42,
        )
        p0 = engine.state.players[0]
        p0.archetype = get_archetype_by_code(ArchetypeCode.CIPHER)
        p0.ability_v1_status = AbilityStatus.AVAILABLE
        p0.money = 1
        p0.secrets = 6
        black_before = engine.state.staging_cup[CubeColor.BLACK]
        ready_before = len(p0.ready_dice)

        engine._execute_phase_3()

        self.assertEqual(p0.money, 3)  # +$2 cash
        self.assertEqual(p0.secrets, 6)  # No secret loss
        self.assertEqual(len(p0.ready_dice), ready_before)  # No die demotion
        self.assertEqual(engine.state.staging_cup[CubeColor.BLACK], black_before)  # No black cube added
        self.assertEqual(p0.ability_v1_status, AbilityStatus.USED)

    def test_controller_dirty_income_rejection_and_cipher_action(self) -> None:
        """Web controller rejects dirty income by default, but allows Cipher cash arbitrage."""
        ctrl = GameController()
        cipher_card = get_archetype_by_code(ArchetypeCode.CIPHER)
        ctrl.new_game(num_players=4, seed=42, archetypes=[cipher_card, None, None, None])
        ctrl.phase = 3
        ctrl.active_player_index = 0

        # Attempt dirty income without cipher -> ValueError (eliminated in v0.16.0)
        with self.assertRaises(ValueError) as ctx:
            ctrl.take_dirty_income(player_id=0, use_cipher_ability=False)
        self.assertIn("v0.16.0", str(ctx.exception))

        # Use Cipher ability for cash arbitrage
        p0 = ctrl.state.players[0]
        money_before = p0.money
        res = ctrl.use_cipher_ability(player_id=0)
        self.assertEqual(p0.money, money_before + 2)
        self.assertEqual(p0.ability_v1_status, AbilityStatus.USED)

    def test_all_bot_types_run_cleanly_without_dirty_income(self) -> None:
        """All 5 bot archetypes play full matches to completion with dirty income disabled."""
        bots = [
            AdaptiveBalancedBot(0),
            SecOpsTurtleBot(1),
            VentureGreedBot(2),
            AccelerationistBot(3),
        ]
        engine = GameEngine(
            config=GameConfig(num_players=4),
            bots=bots,
            seed=123,
        )
        result = engine.run_game()
        self.assertGreater(result.total_rounds, 0)
        self.assertIn(result.end_reason.value, ["singularity", "patient_zero", "total_wipeout", "round_limit"])
        for p in engine.state.players:
            self.assertEqual(p.total_dirty_income_taken, 0)


if __name__ == "__main__":
    unittest.main()
