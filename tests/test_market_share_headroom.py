"""Unit and integration test suite for Unified Market Share Track & Headroom Architecture.

Specification: docs/specs/market_share_headroom_spec.md §7 (test_ms_01 .. test_ms_10)
"""

from __future__ import annotations

import unittest
from sim.bots import AdaptiveBalancedBot
from sim.bots.secret_face_policy import face_value, share_value
from sim.config import (
    DieColor,
    EndGameReason,
    GameConfig,
    V038E_MARKET_SHARE_START,
    DEFAULT_MARKET_SHARE_MAX,
)
from sim.entities import Face, _choice, Die
from sim.engine import GameEngine, market_share
from sim.engine.phase3_income import collect_player_production_income
from sim.engine.phase6_operations import execute_share_regain
from sim.engine.state import PlayerState, ProductionRole


class TestMarketShareHeadroom(unittest.TestCase):
    """Formal verification of Unified Market Share Track & Headroom Architecture."""

    def _make_dummy_player(self, pid: int = 0) -> PlayerState:
        bot = AdaptiveBalancedBot(bot_id=pid)
        return PlayerState(player_id=pid, bot=bot, money=0, secrets=5, patches=0)

    def test_ms_01_decoupled_initialization(self) -> None:
        """INV-MS-HEADROOM-03: Decoupled starting marker position from track ceiling."""
        player = self._make_dummy_player()
        player.init_market_share(start=16, max_share=20)
        self.assertEqual(player.market_share, 16)
        self.assertEqual(player.market_share_start, 16)
        self.assertEqual(player.market_share_min, 16)
        self.assertEqual(player.market_share_peak, 16)
        self.assertEqual(player.market_share_max, 20)

    def test_ms_02_default_max_backwards_compatibility(self) -> None:
        """INV-MS-HEADROOM-03, INV-MS-HEADROOM-10: Default max preserves start=max."""
        player = self._make_dummy_player()
        player.init_market_share(start=16, max_share=None)
        self.assertEqual(player.market_share, 16)
        self.assertEqual(player.market_share_start, 16)
        self.assertEqual(player.market_share_min, 16)
        self.assertEqual(player.market_share_peak, 16)
        self.assertEqual(player.market_share_max, 16)

    def test_ms_03_player_count_calibration(self) -> None:
        """INV-MS-HEADROOM-01, INV-MS-HEADROOM-02: Calibrated start positions and headroom."""
        # 2 Players: start 13, max 20, Headroom +7
        e2 = GameEngine(GameConfig.v038d(num_players=2), seed=42)
        for p in e2.state.players:
            self.assertEqual(p.market_share, 13)
            self.assertEqual(p.market_share_start, 13)
            self.assertEqual(p.market_share_max, 20)
            self.assertEqual(p.market_share_max - p.market_share, 7)

        # 3 Players: start 16, max 20, Headroom +4
        e3 = GameEngine(GameConfig.v038d(num_players=3), seed=42)
        for p in e3.state.players:
            self.assertEqual(p.market_share, 16)
            self.assertEqual(p.market_share_start, 16)
            self.assertEqual(p.market_share_max, 20)
            self.assertEqual(p.market_share_max - p.market_share, 4)

        # 4 Players: start 16, max 20, Headroom +4 (unified with 3P)
        e4 = GameEngine(GameConfig.v038d(num_players=4), seed=42)
        for p in e4.state.players:
            self.assertEqual(p.market_share, 16)
            self.assertEqual(p.market_share_start, 16)
            self.assertEqual(p.market_share_max, 20)
            self.assertEqual(p.market_share_max - p.market_share, 4)

    def test_ms_04_positive_advancement_and_ceiling_clamp(self) -> None:
        """INV-MS-HEADROOM-04: Positive advancement clamped at market_share_max = 20."""
        player = self._make_dummy_player()
        player.init_market_share(start=16, max_share=20)

        # Apply +2 from face: 16 -> 18
        actual = player.change_market_share(+2, "face")
        self.assertEqual(actual, 2)
        self.assertEqual(player.market_share, 18)
        self.assertEqual(player.market_share_peak, 18)
        self.assertEqual(player.market_share_gained_face, 2)

        # Apply +3 from regain: 18 -> 20 (clamped to +2)
        actual = player.change_market_share(+3, "regain")
        self.assertEqual(actual, 2)
        self.assertEqual(player.market_share, 20)
        self.assertEqual(player.market_share_peak, 20)
        self.assertEqual(player.market_share_regained, 2)

        # Apply +1 from r2 while at ceiling: 20 -> 20 (returns 0)
        actual = player.change_market_share(+1, "r2")
        self.assertEqual(actual, 0)
        self.assertEqual(player.market_share, 20)
        self.assertEqual(player.market_share_peak, 20)
        self.assertEqual(player.market_share_gained_r2, 0)

    def test_ms_05_red_damage_floor_and_overflow_telemetry(self) -> None:
        """INV-MS-HEADROOM-04, INV-MS-HEADROOM-05: Red damage floor at 0 and overflow tracking."""
        player = self._make_dummy_player()
        player.init_market_share(start=2, max_share=20)

        # Unblocked Red cube = 1 -> share = 1
        actual = player.change_market_share(-1, "red")
        self.assertEqual(actual, -1)
        self.assertEqual(player.market_share, 1)
        self.assertEqual(player.market_share_lost_red, 1)
        self.assertEqual(player.market_share_red_overflow, 0)

        # Unblocked Red cubes = 3 -> share = 0 (actual -1, overflow 2)
        actual = player.change_market_share(-3, "red")
        self.assertEqual(actual, -1)
        self.assertEqual(player.market_share, 0)
        self.assertEqual(player.market_share_lost_red, 2)
        self.assertEqual(player.market_share_red_overflow, 2)
        self.assertEqual(player.market_share_min, 0)

    def test_ms_06_customer_poaching_headroom_and_actor_at_max(self) -> None:
        """INV-MS-HEADROOM-04: Poaching advances actor into headroom and handles actor at ceiling."""
        engine = GameEngine(GameConfig.v038d(num_players=2), seed=1)
        actor = engine.state.players[0]
        target = engine.state.players[1]

        # Case 1: Actor at 19, Target at 18
        actor.market_share = 19
        target.market_share = 18
        market_share.queue_poach(engine, actor, 1)
        events = market_share.resolve_poaches(engine)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["reason"], "ok")
        self.assertEqual(events[0]["moved"], 1)
        self.assertEqual(events[0]["gained"], 1)
        self.assertEqual(target.market_share, 17)
        self.assertEqual(actor.market_share, 20)

        # Case 2: Actor at 20 (max), Target at 17
        actor.market_share = 20
        target.market_share = 17
        gained_before = actor.market_share_gained_poach
        market_share.queue_poach(engine, actor, 1)
        events = market_share.resolve_poaches(engine)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["reason"], "actor_at_max")
        self.assertEqual(events[0]["moved"], 1)
        self.assertEqual(events[0]["gained"], 0)
        self.assertEqual(target.market_share, 16)
        self.assertEqual(actor.market_share, 20)
        self.assertEqual(actor.market_share_gained_poach, gained_before)

    def test_ms_07_round_1_choice_face_agency(self) -> None:
        """Core Design Pillar 3: Red Face 1 (+1 MS / +$1) choice face preserves agency with headroom."""
        engine = GameEngine(GameConfig.v038d(num_players=3), seed=1)
        player = engine.state.players[0]
        # In Round 1, player starts at 16 with max 20
        self.assertEqual(player.market_share, 16)
        self.assertEqual(player.market_share_max, 20)

        face_ms = Face("+1 Market Share", market_share=1)
        face_cash = Face("+$1", money=1)
        red_f1 = _choice(face_ms, face_cash)

        # Valuation of +1 MS in Round 1:
        # With headroom (+4 remaining), share_value evaluates to > 0 and > $1.00 base value.
        val_ms = face_value(player, face_ms, engine.state)
        val_cash = face_value(player, face_cash, engine.state)
        self.assertGreater(val_ms, 0.0)
        self.assertGreater(val_ms, 1.0)
        self.assertEqual(val_cash, 1.0)

        # Choice face evaluates to max(val_ms, val_cash) = val_ms, not forced into cash
        self.assertEqual(face_value(player, red_f1, engine.state), val_ms)

    def test_ms_08_yellow_face_waste_elimination(self) -> None:
        """Core Design Pillar 3: Yellow Face 1 (+2 MS) produces real advancement without waste."""
        engine = GameEngine(GameConfig.v038d(num_players=3), seed=1)
        player = engine.state.players[0]
        self.assertEqual(player.market_share, 16)

        # Place a Yellow die showing Face 1 (+2 Market Share) in In Production
        yellow_f1 = Face("+2 Market Share", market_share=2)
        die = Die(die_id=99, color=DieColor.YELLOW, cost=6, faces=[yellow_f1] * 6)
        die.current_face = yellow_f1
        die.production_role = ProductionRole.INCOME
        player.in_production_dice.append(die)

        # Collect production income
        collect_player_production_income(engine, player)

        # Market Share advanced from 16 to 18 (+2 gained, 0 wasted)
        self.assertEqual(player.market_share, 18)
        self.assertEqual(player.market_share_gained_face, 2)

    def test_ms_09_public_relations_regain_headroom(self) -> None:
        """INV-MS-HEADROOM-07: Public Relations Track regain functions in Round 1 via headroom."""
        engine = GameEngine(GameConfig.v038d(num_players=3), seed=1)
        player = engine.state.players[0]
        self.assertEqual(player.market_share, 16)
        self.assertEqual(player.patent_level, 0)

        # Give player 3 research tokens (cost for +1 MS at Level 0 is 3 research)
        player.research_tokens = 3
        player.regain_this_turn = 0

        # Execute PR regain
        bought = execute_share_regain(engine, player, 1)
        self.assertEqual(bought, 1)
        self.assertEqual(player.market_share, 17)
        self.assertEqual(player.research_tokens, 0)
        self.assertEqual(player.market_share_regained, 1)

    def test_ms_10_market_collapse_at_zero_preserved(self) -> None:
        """INV-MS-HEADROOM-06: Market Collapse triggers at 0 Market Share without elimination."""
        engine = GameEngine(GameConfig.v038d(num_players=3), seed=1)
        p0, p1, p2 = engine.state.players

        # Reduce p0 to 0 Market Share
        p0.market_share = 0

        # Trigger Market Collapse check
        triggered = market_share.check_market_collapse(engine)
        self.assertTrue(triggered)
        self.assertTrue(engine.state.market_collapse_triggered)
        self.assertTrue(engine.state.is_final_round)
        self.assertEqual(engine.state.end_reason, EndGameReason.MARKET_COLLAPSE)

        # Confirm no player is eliminated
        self.assertFalse(p0.is_patient_zero)
        self.assertFalse(p1.is_patient_zero)
        self.assertFalse(p2.is_patient_zero)


if __name__ == "__main__":
    unittest.main()
