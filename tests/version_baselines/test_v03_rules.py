"""Comprehensive unit tests for Rogue Agent RULES.md v0.3 specifications.

Covers all 14 mandatory test cases from the Principal Engineer specification:
1. Autonomous AI Corruption Pulse at Phase 1 start.
2. Version cards v1.0 payload includes Black Cube.
3. Gray Starter Die faces (no Idle faces, 3x +$1).
4. Default starting money = $7 ($8 with Data Scraper).
5. Unblocked Red damage drains cash when cash is sufficient.
6. Unpaid Red ransom leaks into Corporate Secrets.
7. Corporate money is strictly non-negative (>= $0).
8. Patient Zero is strictly triggered at <= 0 Secrets (not at $0 cash).
9. Dirty Income grants +$3, +1 Black cube (no attack cubes), and demotes 1 Ready die to Unpatched.
10. Dirty Income backlash die index selection moves the chosen die.
11. Dirty Income requires at least 1 Ready die (cannot be taken with 0 ready dice).
12. Final Round: breached player skips Phase 3, surviving players execute Phase 3 before game over.
13. Final Round: Singularity triggers Phase 3 operations before game over.
14. Total Wipeout: immediate game over (Phase 3 skipped), overflow penalties evaluated.
"""

from __future__ import annotations

import random
import unittest
from typing import Dict, List

from sim.bots import BaseBot, Phase3ActionPlan
from sim.config import CubeColor, DieColor, EndGameReason, GameConfig, ShieldColor
from sim.engine import GameEngine, PlayerState
from sim.entities import (
    Die,
    Face,
    VersionCard,
    create_colored_die,
    create_gray_die,
    get_all_version_cards,
)


class TestV03Rules(unittest.TestCase):
    # -------------------------------------------------------------------------
    # 1. Autonomous AI Corruption Pulse
    # -------------------------------------------------------------------------
    def test_autonomous_ai_pulse(self) -> None:
        """Autonomous AI Corruption Pulse adds +1 Black Cube to staging cup at Phase 1 start."""
        config = GameConfig(num_players=2, dirty_income_enabled=True)
        bots = [BaseBot(0), BaseBot(1)]
        engine = GameEngine(config=config, bots=bots, seed=42)

        initial_black = engine.state.staging_cup.get(CubeColor.BLACK, 0)
        self.assertEqual(initial_black, 1)  # From v1.0 Script Kiddie starting payload

        # Execute Phase 1
        engine._execute_phase_1()
        self.assertEqual(engine.state.staging_cup[CubeColor.BLACK], initial_black + 1)

    # -------------------------------------------------------------------------
    # 2. Version v1.0 Cards Staging Payload Has Black Cube
    # -------------------------------------------------------------------------
    def test_v1_cards_staging_payload_has_black(self) -> None:
        """Both v1.0 cards (Script Kiddie and Data Scraper) must include CubeColor.BLACK: 1."""
        cards = get_all_version_cards()
        v1_cards = [c for c in cards if c.version_str == "v1.0"]
        self.assertEqual(len(v1_cards), 2)

        for card in v1_cards:
            self.assertIn(CubeColor.BLACK, card.staging_payload)
            self.assertEqual(card.staging_payload[CubeColor.BLACK], 1)

    # -------------------------------------------------------------------------
    # 3. Gray Starter Die Faces
    # -------------------------------------------------------------------------
    def test_gray_starter_die_faces(self) -> None:
        """Gray die has exactly 2x Block 1 Any, 2x +$1, 1x +$1 / +1 🔧, 1x +1 🔧, and 0 Idle (0) faces."""
        die = create_gray_die(1)
        self.assertEqual(len(die.faces), 6)

        any_shields = [f for f in die.faces if f.shield_color == ShieldColor.ANY and f.block_amount == 1]
        cash_faces = [f for f in die.faces if f.has_cash_option]
        patch_faces = [f for f in die.faces if f.has_patch_option]
        choice_faces = [f for f in die.faces if f.is_choice]
        idle_faces = [f for f in die.faces if f.name == "Idle (0)"]

        self.assertEqual(len(any_shields), 2)
        self.assertEqual(len(cash_faces), 3)
        self.assertEqual(len(patch_faces), 2)
        self.assertEqual(len(choice_faces), 1)
        self.assertEqual(len(idle_faces), 0)

    # -------------------------------------------------------------------------
    # 4. Default Starting Money
    # -------------------------------------------------------------------------
    def test_starting_money_default(self) -> None:
        """Default starting money is $7 (or $8 under Data Scraper)."""
        config = GameConfig(num_players=2, dirty_income_enabled=True)
        self.assertEqual(config.starting_money, 7)

        # Baseline engine with Script Kiddie
        bots = [BaseBot(0), BaseBot(1)]
        engine = GameEngine(config=config, bots=bots, seed=42)
        for p in engine.state.players:
            self.assertEqual(p.money, 7)

        # Engine with Data Scraper (+ $1 starting money)
        data_scraper = [c for c in get_all_version_cards() if c.directive_code == "DATA_SCRAPER"][0]
        engine_ds = GameEngine(config=config, bots=bots, seed=42, version_deck=[data_scraper])
        for p in engine_ds.state.players:
            self.assertEqual(p.money, 8)

    # -------------------------------------------------------------------------
    # 5. Unblocked Red Damage Drains Cash
    # -------------------------------------------------------------------------
    def test_unblocked_red_drains_cash(self) -> None:
        """Unblocked Red damage drains cash down when money is sufficient; secrets remain intact."""
        config = GameConfig(num_players=2, dirty_income_enabled=True)
        engine = GameEngine(config=config, bots=[BaseBot(0), BaseBot(1)], seed=42)
        player = engine.state.players[0]
        player.money = 5
        player.secrets = 6

        # Apply unblocked Red = 3
        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=list(player.ready_dice),
            commitments={},
            attack_strengths={CubeColor.RED: 3, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 3, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        self.assertEqual(player.money, 2)
        self.assertEqual(player.secrets, 6)
        self.assertFalse(player.is_patient_zero)

    # -------------------------------------------------------------------------
    # 6. Unpaid Red Ransom Leaks to Corporate Secrets
    # -------------------------------------------------------------------------
    def test_unblocked_red_ransom_leak_to_secrets(self) -> None:
        """When money is exhausted ($0), unpaid Red damage leaks into Secrets (1 Secret per unpaid $1)."""
        config = GameConfig(num_players=2, dirty_income_enabled=True)
        engine = GameEngine(config=config, bots=[BaseBot(0), BaseBot(1)], seed=42)
        player = engine.state.players[0]
        player.money = 2
        player.secrets = 6
        player.patches = 0  # Zero patches to test direct cash-to-secret leak

        # 5 unblocked Red: drains $2 to $0, remaining 3 unpaid leaks 3 secrets -> 3 secrets left
        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=list(player.ready_dice),
            commitments={},
            attack_strengths={CubeColor.RED: 5, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 5, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        self.assertEqual(player.money, 0)
        self.assertEqual(player.secrets, 3)
        self.assertFalse(player.is_patient_zero)

    # -------------------------------------------------------------------------
    # 7. Cash Is Strictly Non-Negative (>= $0)
    # -------------------------------------------------------------------------
    def test_cash_strictly_non_negative(self) -> None:
        """Money never drops below $0 even under massive unblocked Red ransomware attack."""
        config = GameConfig(num_players=2, dirty_income_enabled=True)
        engine = GameEngine(config=config, bots=[BaseBot(0), BaseBot(1)], seed=42)
        player = engine.state.players[0]
        player.money = 1
        player.secrets = 6
        player.patches = 0  # Zero patches to test direct cash-to-secret leak

        # 10 unblocked Red: drains $1 to $0, unpaid 9 damage reduces secrets to -3
        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=list(player.ready_dice),
            commitments={},
            attack_strengths={CubeColor.RED: 10, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 10, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        self.assertEqual(player.money, 0)
        self.assertEqual(player.secrets, -3)
        self.assertEqual(player.breach_depth, 3)
        self.assertTrue(player.is_patient_zero)

    # -------------------------------------------------------------------------
    # 8. Patient Zero Strictly on Secrets (<= 0 Secrets)
    # -------------------------------------------------------------------------
    def test_patient_zero_strictly_on_secrets(self) -> None:
        """Patient Zero is strictly determined by Secrets <= 0, NOT by having $0 money."""
        config = GameConfig(num_players=2, dirty_income_enabled=True)
        engine = GameEngine(config=config, bots=[BaseBot(0), BaseBot(1)], seed=42)
        player = engine.state.players[0]

        # Case A: $0 money, 4 secrets -> survives (not Patient Zero)
        player.money = 0
        player.secrets = 4
        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=list(player.ready_dice),
            commitments={},
            attack_strengths={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            active_directive="NONE",
        )
        self.assertFalse(player.is_patient_zero)

        # Case B: $0 money, 2 secrets, takes 2 unblocked Red -> secrets drops to 0 -> Patient Zero!
        player.money = 0
        player.secrets = 2
        player.patches = 0  # Zero patches to test direct cash-to-secret leak
        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=list(player.ready_dice),
            commitments={},
            attack_strengths={CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            active_directive="NONE",
        )
        self.assertEqual(player.secrets, 0)
        self.assertTrue(player.is_patient_zero)
        self.assertEqual(player.elimination_reason, "Total Breach (<= 0 Secrets)")

    # -------------------------------------------------------------------------
    # 9. Dirty Income Technical Debt Backlash
    # -------------------------------------------------------------------------
    def test_dirty_income_technical_debt_backlash(self) -> None:
        """Dirty Income gives +$3, +1 Black cube (no attack cubes), and demotes 1 Ready die to Unpatched."""
        class DirtyIncomeBot(BaseBot):
            def take_phase3_actions(self, player_state, game_state, rng):
                return Phase3ActionPlan(take_dirty_income=True)

        config = GameConfig(num_players=2, dirty_income_enabled=True)
        engine = GameEngine(config=config, bots=[DirtyIncomeBot(0), BaseBot(1)], seed=42)
        player = engine.state.players[0]
        initial_money = player.money
        initial_ready = len(player.ready_dice)
        initial_unpatched = len(player.unpatched_dice)
        initial_black = engine.state.staging_cup.get(CubeColor.BLACK, 0)

        initial_red = engine.state.staging_cup.get(CubeColor.RED, 0)
        initial_blue = engine.state.staging_cup.get(CubeColor.BLUE, 0)
        initial_green = engine.state.staging_cup.get(CubeColor.GREEN, 0)

        # Execute Phase 3
        engine._execute_phase_3()

        self.assertEqual(player.money, initial_money + 3)
        self.assertEqual(engine.state.staging_cup[CubeColor.BLACK], initial_black + 1)
        self.assertEqual(engine.state.staging_cup[CubeColor.RED], initial_red)
        self.assertEqual(engine.state.staging_cup[CubeColor.BLUE], initial_blue)
        self.assertEqual(engine.state.staging_cup[CubeColor.GREEN], initial_green)
        self.assertEqual(len(player.ready_dice), initial_ready - 1)
        self.assertEqual(len(player.unpatched_dice), initial_unpatched + 1)
        self.assertEqual(player.total_dirty_income_taken, 1)

    # -------------------------------------------------------------------------
    # 10. Dirty Income Backlash Die Index Selection
    # -------------------------------------------------------------------------
    def test_dirty_income_backlash_die_index_selection(self) -> None:
        """Chosen backlash die index in plan is demoted to unpatched zone."""
        class SelectiveBacklashBot(BaseBot):
            def take_phase3_actions(self, player_state, game_state, rng):
                # Request demotion of die at index 1
                return Phase3ActionPlan(
                    take_dirty_income=True,
                    dirty_income_backlash_die_index=1,
                )

        config = GameConfig(num_players=2, dirty_income_enabled=True)
        engine = GameEngine(config=config, bots=[SelectiveBacklashBot(0), BaseBot(1)], seed=42)
        player = engine.state.players[0]
        target_die = player.ready_dice[1]

        engine._execute_phase_3()

        self.assertNotIn(target_die, player.ready_dice)
        self.assertIn(target_die, player.unpatched_dice)

    # -------------------------------------------------------------------------
    # 11. Dirty Income Requires Ready Die
    # -------------------------------------------------------------------------
    def test_dirty_income_requires_ready_die(self) -> None:
        """Dirty Income cannot be taken if the player has 0 Ready dice."""
        class AggressiveDirtyBot(BaseBot):
            def take_phase3_actions(self, player_state, game_state, rng):
                return Phase3ActionPlan(take_dirty_income=True)

        config = GameConfig(num_players=2, dirty_income_enabled=True)
        engine = GameEngine(config=config, bots=[AggressiveDirtyBot(0), BaseBot(1)], seed=42)
        player = engine.state.players[0]

        # Move all ready dice to unpatched
        player.unpatched_dice.extend(player.ready_dice)
        player.ready_dice.clear()

        initial_money = player.money
        initial_black = engine.state.staging_cup.get(CubeColor.BLACK, 0)

        engine._execute_phase_3()

        # Dirty income should not have been executed
        self.assertEqual(player.money, initial_money)
        self.assertEqual(engine.state.staging_cup.get(CubeColor.BLACK, 0), initial_black)
        self.assertEqual(player.total_dirty_income_taken, 0)

    # -------------------------------------------------------------------------
    # 12. Final Round: Breached Player Skips Phase 3, Survivors Execute Phase 3
    # -------------------------------------------------------------------------
    def test_final_round_surviving_players_execute_phase_3(self) -> None:
        """When 1 player breaches in Phase 2, final round is declared; survivor takes Phase 3 turn."""
        p0_acted = []
        p1_acted = []

        class TrackingBot(BaseBot):
            def __init__(self, bot_id: int, log_list: list) -> None:
                super().__init__(bot_id)
                self.log_list = log_list

            def take_phase3_actions(self, player_state, game_state, rng):
                self.log_list.append(self.bot_id)
                # Survivor buys a die
                return Phase3ActionPlan(market_purchases=[DieColor.RED])

        config = GameConfig(num_players=2, tower_mode="flat_binomial", tower_flat_exit_prob=1.0)
        engine = GameEngine(
            config=config,
            bots=[TrackingBot(0, p0_acted), TrackingBot(1, p1_acted)],
            seed=42,
        )

        p0 = engine.state.players[0]
        p1 = engine.state.players[1]

        # Force p0 to have only 1 secret and $0 cash, so taking 2 Blue damage causes breach
        p0.secrets = 1
        p0.money = 0
        p1.secrets = 6
        p1.money = 10

        # Execute Phase 1
        engine._execute_phase_1()
        # Ensure no blue shields committed for p0
        commitments = [(p0, p0.ready_dice, {}), (p1, p1.ready_dice, {})]

        # Manually set tower staging to 2 Blue cubes
        engine.state.staging_cup = {
            CubeColor.RED: 0,
            CubeColor.BLUE: 2,
            CubeColor.GREEN: 0,
            CubeColor.BLACK: 0,
        }
        # Clear tower stuck cubes to ensure deterministic drop
        engine.state.tower.reset()

        # Run Phase 2
        engine._execute_phase_2(commitments)

        # p0 should have breached
        self.assertTrue(p0.is_patient_zero)
        self.assertFalse(p1.is_patient_zero)
        self.assertTrue(engine.state.is_final_round)
        self.assertFalse(engine.state.game_over)
        self.assertEqual(engine.state.end_reason, EndGameReason.PATIENT_ZERO)

        # Run Phase 3
        engine._execute_phase_3()

        # p0 must have skipped Phase 3; p1 must have acted
        self.assertEqual(len(p0_acted), 0)
        self.assertEqual(len(p1_acted), 1)

        # In run_round pipeline, after Phase 3, game_over is set to True
        if engine.state.is_final_round:
            engine.state.game_over = True
        self.assertTrue(engine.state.game_over)

        result = engine.evaluate_end_game()
        self.assertEqual(result.winner_id, 1)
        self.assertFalse(result.is_total_wipeout)

    # -------------------------------------------------------------------------
    # 13. Final Round: Singularity Triggers Phase 3 Operations
    # -------------------------------------------------------------------------
    def test_final_round_singularity_triggers_phase_3(self) -> None:
        """Singularity in Phase 2 sets is_final_round; surviving players take Phase 3 before game over."""
        p0_acted = []
        p1_acted = []

        class TrackingBot(BaseBot):
            def __init__(self, bot_id: int, log_list: list) -> None:
                super().__init__(bot_id)
                self.log_list = log_list

            def take_phase3_actions(self, player_state, game_state, rng):
                self.log_list.append(self.bot_id)
                return Phase3ActionPlan()

        config = GameConfig(num_players=2, dirty_income_enabled=True)
        engine = GameEngine(
            config=config,
            bots=[TrackingBot(0, p0_acted), TrackingBot(1, p1_acted)],
            seed=42,
        )

        # Set game to v3.0 with track at capacity - 1
        engine.state.current_version_index = len(engine.state.version_deck) - 1
        engine.state.corruption_track = engine.state.corruption_track_capacity - 1

        commitments = engine._execute_phase_1()

        # Stage 1 Black cube (plus whatever Phase 1 pulse added)
        engine.state.staging_cup = {
            CubeColor.RED: 0,
            CubeColor.BLUE: 0,
            CubeColor.GREEN: 0,
            CubeColor.BLACK: 1,
        }
        engine.state.tower.reset()
        # Force 100% exit probability
        config.tower_flat_exit_prob = 1.0
        config.tower_mode = "flat_binomial"

        engine._execute_phase_2(commitments)

        self.assertTrue(engine.state.singularity_triggered)
        self.assertTrue(engine.state.is_final_round)
        self.assertFalse(engine.state.game_over)
        self.assertEqual(engine.state.end_reason, EndGameReason.SINGULARITY)

        # Both surviving players should get their operations turn
        engine._execute_phase_3()
        self.assertEqual(len(p0_acted), 1)
        self.assertEqual(len(p1_acted), 1)

    # -------------------------------------------------------------------------
    # 14. Total Wipeout Immediate Game Over & Overflow Scoring
    # -------------------------------------------------------------------------
    def test_total_wipeout_immediate_game_over_and_overflow_scoring(self) -> None:
        """When ALL players breach in Phase 2: immediate game_over, Phase 3 skipped, overflow scoring applied."""
        p_acted = []

        class NoOpBot(BaseBot):
            def take_phase3_actions(self, player_state, game_state, rng):
                p_acted.append(self.bot_id)
                return Phase3ActionPlan()

        config = GameConfig(num_players=2, dirty_income_enabled=True)
        engine = GameEngine(config=config, bots=[NoOpBot(0), NoOpBot(1)], seed=42)

        p0 = engine.state.players[0]
        p1 = engine.state.players[1]
        p0.archetype = None
        p1.archetype = None

        # Both players in critical condition
        p0.secrets = 1
        p0.money = 0
        p1.secrets = 2
        p1.money = 0

        engine._execute_phase_1()
        # Commit zero shields to ensure all damage is unblocked
        commitments = [(p0, p0.ready_dice, {}), (p1, p1.ready_dice, {})]

        # Drop 4 Blue cubes: p0 takes 4 damage (secrets -> -3), p1 takes 4 damage (secrets -> -2)
        engine.state.staging_cup = {
            CubeColor.RED: 0,
            CubeColor.BLUE: 4,
            CubeColor.GREEN: 0,
            CubeColor.BLACK: 0,
        }
        engine.state.tower.reset()
        config.tower_flat_exit_prob = 1.0
        config.tower_mode = "flat_binomial"

        engine._execute_phase_2(commitments)

        # Both breached -> Total Wipeout
        self.assertTrue(p0.is_patient_zero)
        self.assertTrue(p1.is_patient_zero)
        self.assertTrue(engine.state.game_over)
        self.assertEqual(engine.state.end_reason, EndGameReason.TOTAL_WIPEOUT)

        # Phase 3 must not run
        if not engine.state.game_over:
            engine._execute_phase_3()
        self.assertEqual(len(p_acted), 0)

        # Evaluate scoring
        result = engine.evaluate_end_game()
        self.assertTrue(result.is_total_wipeout)

        # p1 breached to -2 secrets (breach_depth 2 -> -8 VP overflow penalty)
        # p0 breached to -3 secrets (breach_depth 3 -> -12 VP overflow penalty)
        r0 = [r for r in result.rankings if r["player_id"] == 0][0]
        r1 = [r for r in result.rankings if r["player_id"] == 1][0]

        self.assertEqual(r0["overflow_penalties"], 3 * config.overflow_penalty_per_secret_debt)
        self.assertEqual(r1["overflow_penalties"], 2 * config.overflow_penalty_per_secret_debt)
        # p1 has higher net score than p0
        self.assertGreater(r1["net_score"], r0["net_score"])
        self.assertEqual(result.winner_id, 1)


if __name__ == "__main__":
    unittest.main()
