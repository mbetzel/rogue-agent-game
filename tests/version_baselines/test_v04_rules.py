"""Comprehensive unit tests for Rogue Agent RULES.md v0.4 specifications.

Covers all 11 mandatory test cases from the Principal Engineer specification:
1. Flat 4-space corruption track capacity across all player counts (2P, 3P, 4P).
2. Configuration dirty_income_secret_cost == 1.
3. Unblocked Red damage paid fully by cash when cash is sufficient.
4. Unblocked Red damage: Tier 2 Emergency Patch Absorption absorbs unpaid ransom.
5. Unblocked Red damage: Tier 1 cash + Tier 2 patches exhausted -> remaining leaks to Secrets.
6. Unblocked Red damage: $0 cash and 0 patches -> full leak directly to Secrets.
7. Red damage resolution strictly maintains player.money >= 0 and player.patches >= 0.
8. Dirty Income execution: deducts 1 Secret, adds +$3 cash, adds 1 Black cube, demotes 1 Ready die.
9. Dirty Income precondition enforcement: blocked when player.secrets <= dirty_income_secret_cost (e.g. 1 Secret).
10. Dirty Income precondition enforcement: blocked when player has 0 Ready dice.
11. Bot archetypes compliance: Generic ANY shields prioritize Blue, Dirty Income guarded by secrets > 1, and $2 cash cushion respected.
"""

from __future__ import annotations

import random
import unittest
from typing import Dict, List

from sim.bots import (
    AdaptiveBalancedBot,
    AccelerationistBot,
    BaseBot,
    Phase3ActionPlan,
    RecklessSaboteurBot,
    SecOpsTurtleBot,
    VentureGreedBot,
)
from sim.config import CubeColor, DieColor, GameConfig, ShieldColor
from sim.engine import GameEngine, PlayerState
from sim.entities import Die, Face, create_gray_die


class TestV04Rules(unittest.TestCase):
    # -------------------------------------------------------------------------
    # 1. Corruption Track Flat Capacity (Flat 4 spaces across all player counts)
    # -------------------------------------------------------------------------
    def test_corruption_track_flat_capacity(self) -> None:
        """Corruption track capacity is flat 4 spaces across 2P, 3P, and 4P."""
        for num_players in [2, 3, 4]:
            config = GameConfig(num_players=num_players, corruption_track_flat_capacity=4)
            self.assertEqual(
                config.corruption_track_capacity,
                4,
                f"Expected 4 spaces for {num_players} players, got {config.corruption_track_capacity}",
            )

    # -------------------------------------------------------------------------
    # 2. Dirty Income Secret Cost Config
    # -------------------------------------------------------------------------
    def test_dirty_income_config_secret_cost(self) -> None:
        """GameConfig defines dirty_income_secret_cost == 1."""
        config = GameConfig()
        self.assertEqual(config.dirty_income_secret_cost, 1)

    # -------------------------------------------------------------------------
    # 3. Red Damage Paid Fully By Cash
    # -------------------------------------------------------------------------
    def test_red_damage_paid_fully_by_cash(self) -> None:
        """When cash >= unblocked Red damage, cash pays fully; patches and secrets untouched."""
        config = GameConfig(num_players=2)
        engine = GameEngine(config=config, bots=[BaseBot(0), BaseBot(1)], seed=42)
        player = engine.state.players[0]
        player.money = 5
        player.patches = 2
        player.secrets = 6

        # 3 unblocked Red
        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=list(player.ready_dice),
            commitments={},
            attack_strengths={CubeColor.RED: 3, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 3, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        self.assertEqual(player.money, 2)
        self.assertEqual(player.patches, 2)
        self.assertEqual(player.secrets, 6)
        self.assertFalse(player.is_patient_zero)

    # -------------------------------------------------------------------------
    # 4. Red Damage: Partial Cash, Partial Patches (Secrets Untouched)
    # -------------------------------------------------------------------------
    def test_red_damage_partial_cash_partial_patches(self) -> None:
        """When cash is exhausted, Tier 2 patches absorb unpaid ransom; secrets untouched."""
        config = GameConfig(num_players=2)
        engine = GameEngine(config=config, bots=[BaseBot(0), BaseBot(1)], seed=42)
        player = engine.state.players[0]
        player.money = 2
        player.patches = 3
        player.secrets = 6

        # 4 unblocked Red: drains $2 cash to $0, remaining 2 absorbed by 2 patches -> 1 patch left
        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=list(player.ready_dice),
            commitments={},
            attack_strengths={CubeColor.RED: 4, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 4, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        self.assertEqual(player.money, 0)
        self.assertEqual(player.patches, 1)
        self.assertEqual(player.secrets, 6)
        self.assertFalse(player.is_patient_zero)

    # -------------------------------------------------------------------------
    # 5. Red Damage: Cash + Patches Exhausted -> Remaining Leaks to Secrets
    # -------------------------------------------------------------------------
    def test_red_damage_partial_cash_partial_patches_leak_secrets(self) -> None:
        """When cash and patches are both exhausted, remaining unpaid ransom leaks to Secrets."""
        config = GameConfig(num_players=2)
        engine = GameEngine(config=config, bots=[BaseBot(0), BaseBot(1)], seed=42)
        player = engine.state.players[0]
        player.money = 2
        player.patches = 1
        player.secrets = 6

        # 5 unblocked Red: drains $2 to $0, 1 patch absorbs 1 to 0, remaining 2 leaks 2 secrets -> 4 left
        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=list(player.ready_dice),
            commitments={},
            attack_strengths={CubeColor.RED: 5, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 5, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        self.assertEqual(player.money, 0)
        self.assertEqual(player.patches, 0)
        self.assertEqual(player.secrets, 4)
        self.assertFalse(player.is_patient_zero)

    # -------------------------------------------------------------------------
    # 6. Red Damage: No Cash, No Patches -> Full Leak to Secrets
    # -------------------------------------------------------------------------
    def test_red_damage_no_cash_no_patches_full_secret_leak(self) -> None:
        """With $0 cash and 0 patches, unblocked Red damage directly leaks all damage to Secrets."""
        config = GameConfig(num_players=2)
        engine = GameEngine(config=config, bots=[BaseBot(0), BaseBot(1)], seed=42)
        player = engine.state.players[0]
        player.money = 0
        player.patches = 0
        player.secrets = 6

        # 4 unblocked Red
        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=list(player.ready_dice),
            commitments={},
            attack_strengths={CubeColor.RED: 4, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 4, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        self.assertEqual(player.money, 0)
        self.assertEqual(player.patches, 0)
        self.assertEqual(player.secrets, 2)
        self.assertFalse(player.is_patient_zero)

    # -------------------------------------------------------------------------
    # 7. Red Damage Non-Negative Invariants
    # -------------------------------------------------------------------------
    def test_red_damage_non_negative_invariants(self) -> None:
        """Massive Red damage leaves player.money >= 0 and player.patches >= 0."""
        config = GameConfig(num_players=2)
        engine = GameEngine(config=config, bots=[BaseBot(0), BaseBot(1)], seed=42)
        player = engine.state.players[0]
        player.money = 1
        player.patches = 1
        player.secrets = 4

        # 10 unblocked Red
        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=list(player.ready_dice),
            commitments={},
            attack_strengths={CubeColor.RED: 10, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 10, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        self.assertGreaterEqual(player.money, 0)
        self.assertGreaterEqual(player.patches, 0)
        self.assertEqual(player.money, 0)
        self.assertEqual(player.patches, 0)
        self.assertEqual(player.secrets, -4)  # 4 - 8 = -4
        self.assertTrue(player.is_patient_zero)
        self.assertEqual(player.breach_depth, 4)

    # -------------------------------------------------------------------------
    # 8. Dirty Income Execution Success (Deducts 1 Secret, +$3 Cash, +1 Black)
    # -------------------------------------------------------------------------
    def test_dirty_income_execution_success(self) -> None:
        """Dirty Income deducts 1 Secret, grants +$3 cash, adds 1 Black cube, demotes 1 Ready die."""
        class WillingDirtyBot(BaseBot):
            def take_phase3_actions(self, player_state, game_state, rng):
                return Phase3ActionPlan(take_dirty_income=True)

        config = GameConfig(num_players=2)
        engine = GameEngine(config=config, bots=[WillingDirtyBot(0), BaseBot(1)], seed=42)
        player = engine.state.players[0]
        player.money = 5
        player.secrets = 6
        initial_ready = len(player.ready_dice)
        initial_unpatched = len(player.unpatched_dice)
        initial_black = engine.state.staging_cup.get(CubeColor.BLACK, 0)

        engine._execute_phase_3()

        self.assertEqual(player.secrets, 5)  # Deducted 1 Secret
        self.assertEqual(player.money, 8)    # +$3 Cash
        self.assertEqual(engine.state.staging_cup[CubeColor.BLACK], initial_black + 1)
        self.assertEqual(len(player.ready_dice), initial_ready - 1)
        self.assertEqual(len(player.unpatched_dice), initial_unpatched + 1)
        self.assertEqual(player.total_dirty_income_taken, 1)

    # -------------------------------------------------------------------------
    # 9. Dirty Income Blocked at 1 Secret (Precondition Enforced)
    # -------------------------------------------------------------------------
    def test_dirty_income_blocked_at_one_secret(self) -> None:
        """Dirty Income cannot be taken if player has <= 1 Secret (cannot commit suicide)."""
        class SuicidalDirtyBot(BaseBot):
            def take_phase3_actions(self, player_state, game_state, rng):
                return Phase3ActionPlan(take_dirty_income=True)

        config = GameConfig(num_players=2)
        engine = GameEngine(config=config, bots=[SuicidalDirtyBot(0), BaseBot(1)], seed=42)
        player = engine.state.players[0]
        player.money = 2
        player.secrets = 1  # At secret cost limit
        initial_ready = len(player.ready_dice)
        initial_black = engine.state.staging_cup.get(CubeColor.BLACK, 0)

        engine._execute_phase_3()

        # Action blocked: no state mutated
        self.assertEqual(player.secrets, 1)
        self.assertEqual(player.money, 2)
        self.assertEqual(engine.state.staging_cup.get(CubeColor.BLACK, 0), initial_black)
        self.assertEqual(len(player.ready_dice), initial_ready)
        self.assertEqual(player.total_dirty_income_taken, 0)
        self.assertFalse(player.is_patient_zero)

    # -------------------------------------------------------------------------
    # 10. Dirty Income Blocked With Zero Ready Dice
    # -------------------------------------------------------------------------
    def test_dirty_income_blocked_with_zero_ready_dice(self) -> None:
        """Dirty Income cannot be taken when ready_dice is empty."""
        class AggressiveDirtyBot(BaseBot):
            def take_phase3_actions(self, player_state, game_state, rng):
                return Phase3ActionPlan(take_dirty_income=True)

        config = GameConfig(num_players=2)
        engine = GameEngine(config=config, bots=[AggressiveDirtyBot(0), BaseBot(1)], seed=42)
        player = engine.state.players[0]
        player.secrets = 6
        player.money = 2
        # Move all ready dice to unpatched
        player.unpatched_dice.extend(player.ready_dice)
        player.ready_dice.clear()
        initial_black = engine.state.staging_cup.get(CubeColor.BLACK, 0)

        engine._execute_phase_3()

        self.assertEqual(player.secrets, 6)
        self.assertEqual(player.money, 2)
        self.assertEqual(engine.state.staging_cup.get(CubeColor.BLACK, 0), initial_black)
        self.assertEqual(player.total_dirty_income_taken, 0)

    # -------------------------------------------------------------------------
    # 11. Bot Compliance Across All Archetypes
    # -------------------------------------------------------------------------
    def test_bot_compliance_across_all_archetypes(self) -> None:
        """All 5 bot archetypes prioritize Blue for ANY shields, guard dirty income at <=1 secret, and respect $2 cash cushion."""
        config = GameConfig(num_players=4)
        bots = [
            AdaptiveBalancedBot(0),
            SecOpsTurtleBot(1),
            VentureGreedBot(2),
            AccelerationistBot(3),
            RecklessSaboteurBot(4),
        ]
        rng = random.Random(42)

        # Die with Generic ANY shield face
        any_shield_die = Die(
            die_id=99,
            color=DieColor.GRAY,
            cost=0,
            vp=0,
            faces=[Face(name="Block 1 Any", shield_color=ShieldColor.ANY, block_amount=1)] * 6,
        )
        any_shield_die.roll(rng)

        for bot in bots:
            engine = GameEngine(config=config, bots=[bot] + [BaseBot(i) for i in range(1, 4)], seed=42)
            player = engine.state.players[0]

            # 1. commit_shields assigns ANY shield to BLUE
            commitments = bot.commit_shields(
                player_state=player,
                rolled_dice=[any_shield_die],
                staging_cubes={CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 1},
                stuck_cubes={},
                directive_code="NONE",
                rng=rng,
            )
            self.assertEqual(
                commitments.get(0),
                ShieldColor.BLUE,
                f"{bot.name} failed to assign generic ANY shield to ShieldColor.BLUE",
            )

            # 2. Guard Dirty Income at <= 1 Secret
            player.secrets = 1
            player.money = 0  # Desperate for money
            plan = bot.take_phase3_actions(player, engine.state, rng)
            self.assertFalse(
                plan.take_dirty_income,
                f"{bot.name} attempted Dirty Income with only 1 Secret!",
            )

            # 3. Respect $2 cash cushion before cash-patching
            # Player has $3, 0 patches, 2 unpatched dice.
            # Patch cash cost is $2. Paying $2 would leave $1 (< $2 cushion).
            player.money = 3
            player.patches = 0
            player.unpatched_dice = [create_gray_die(101), create_gray_die(102)]
            plan2 = bot.take_phase3_actions(player, engine.state, rng)
            cash_patches = [p for p in plan2.patch_actions if p.get("use_cash")]
            self.assertEqual(
                len(cash_patches),
                0,
                f"{bot.name} spent cash on patching violating the $2 cushion (money=$3, cost=$2)",
            )


if __name__ == "__main__":
    unittest.main()
