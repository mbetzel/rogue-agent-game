"""Tests for Research Upgrade Limit & Track Step Costs (v0.39.0 / spec_research_upgrade_limit.md).

Covers TEST-RUL-01 through TEST-RUL-08:
- TEST-RUL-01: Track Step Cost Sequence (1, 1, 2, 2)
- TEST-RUL-02: Per-Turn Hardware Upgrade Limit Enforcement (Engine)
- TEST-RUL-03: Multi-Track Upgrades Obey Combined Limit
- TEST-RUL-04: PR Market Share Regain Does Not Count Toward Upgrade Limit
- TEST-RUL-05: Breakthrough Cash Funds Same-Turn Market Purchase at Turn Cap
- TEST-RUL-06: Telemetry Records Excess Requested Upgrades
- TEST-RUL-07: Web Controller Rejects 3rd Upgrade
- TEST-RUL-08: Bot Research Policy Honors Upgrade Limit
"""

from __future__ import annotations

import unittest
from typing import Any, List, Optional

from sim.bots import BaseBot, Phase3ActionPlan
from sim.bots.research_policy import apply_research_policy, plan_research3
from sim.config import DieColor, GameConfig, RoundPhase
from sim.engine import GameEngine, phase6_operations
from sim.engine import research_tracks as rt
from sim.engine.state import PlayerState
from web.game_controller import GameController


class StubPlanBot(BaseBot):
    def __init__(self, player_id: int, plan: Optional[Phase3ActionPlan] = None, research_aware: bool = False):
        super().__init__(player_id)
        self.preset_plan = plan or Phase3ActionPlan()
        self.research_aware = research_aware

    def take_operations_actions(self, player_state: PlayerState, game_state: Any, rng: Any = None) -> Phase3ActionPlan:
        return self.preset_plan


class TestResearchUpgradeLimit(unittest.TestCase):
    def test_rul_01_track_step_cost_sequence(self):
        """TEST-RUL-01: Verify step costs are (1, 1, 2, 2) on all 4 tracks, total 6 🔬."""
        cfg = GameConfig(num_players=2)
        self.assertEqual(cfg.track_step_costs, (1, 1, 2, 2))
        self.assertEqual(cfg.max_hardware_upgrades_per_turn, 2)

        p = PlayerState(0, StubPlanBot(0), money=0, secrets=5, patches=0, config=cfg)

        for t in rt.TRACKS:
            # Reset levels
            p.defense_level = 0
            p.triage_level = 0
            p.release_level = 0
            p.patent_level = 0
            p.research_tokens = 6

            costs = []
            while True:
                c = p.get_track_upgrade_cost(t)
                if c is None:
                    break
                costs.append(c)
                self.assertTrue(p.upgrade_track(t))

            self.assertEqual(costs, [1, 1, 2, 2], f"Track {t} step cost sequence")
            self.assertEqual(p.research_tokens, 0, f"Track {t} remaining research")
            self.assertIsNone(p.get_track_upgrade_cost(t), f"Track {t} cost at L4")
            self.assertFalse(p.upgrade_track(t), f"Track {t} upgrade at L4")

    def test_rul_02_per_turn_hardware_upgrade_limit_engine(self):
        """TEST-RUL-02: Exactly 2 upgrades execute when 3 are requested on a single track."""
        cfg = GameConfig(num_players=2)
        engine = GameEngine(cfg, [StubPlanBot(0), StubPlanBot(1)], seed=42)
        p = engine.state.players[0]
        p.research_tokens = 6
        p.defense_level = 0

        plan = Phase3ActionPlan(track_upgrades=["DEFENSE", "DEFENSE", "DEFENSE"])
        done = phase6_operations.execute_track_upgrades(engine, p, plan)

        self.assertEqual(len(done), 2)
        self.assertEqual(p.defense_level, 2)
        self.assertEqual(p.research_tokens, 4)  # 6 - (1 + 1)
        self.assertEqual(p.excess_hardware_upgrades_requested, 1)

    def test_rul_03_multi_track_upgrades_obey_combined_limit(self):
        """TEST-RUL-03: Combined upgrades across distinct tracks stop at turn limit."""
        cfg = GameConfig(num_players=2)
        engine = GameEngine(cfg, [StubPlanBot(0), StubPlanBot(1)], seed=42)
        p = engine.state.players[0]
        p.research_tokens = 4
        p.defense_level = 0
        p.release_level = 0
        p.triage_level = 0

        plan = Phase3ActionPlan(track_upgrades=["DEFENSE", "RELEASE", "TRIAGE"])
        done = phase6_operations.execute_track_upgrades(engine, p, plan)

        self.assertEqual(len(done), 2)
        self.assertEqual(p.defense_level, 1)
        self.assertEqual(p.release_level, 1)
        self.assertEqual(p.triage_level, 0)
        self.assertEqual(p.research_tokens, 2)  # 4 - (1 + 1)
        self.assertEqual(p.excess_hardware_upgrades_requested, 1)

    def test_rul_04_pr_market_share_regain_exempt_from_limit(self):
        """TEST-RUL-04: PR Market Share regain is exempt from the 2 hardware upgrade limit."""
        cfg = GameConfig(num_players=2)
        engine = GameEngine(cfg, [StubPlanBot(0), StubPlanBot(1)], seed=42)
        p = engine.state.players[0]
        p.research_tokens = 6
        p.defense_level = 0
        p.patent_level = 0
        p.market_share = 10
        p.market_share_max = 20

        # Defense L0->L2 costs 1 + 1 = 2 🔬.
        # PR regain 1 step costs 2 🔬 under v0.37 / 3 🔬 under v0.38
        cost = cfg.share_regain_cost_by_level[0]
        p.research_tokens = 2 + cost  # 2 for defense upgrades + cost for 1 regain
        plan = Phase3ActionPlan(track_upgrades=["DEFENSE", "DEFENSE"], share_regain=1)
        phase6_operations.execute_player_operations_turn(engine, p, plan)

        self.assertEqual(p.defense_level, 2)
        self.assertEqual(p.market_share, 11)
        self.assertEqual(p.research_tokens, 0)
        self.assertEqual(p.excess_hardware_upgrades_requested, 0)

    def test_rul_05_breakthrough_cash_funds_market_purchase_at_cap(self):
        """TEST-RUL-05: Breakthrough cash from PR L1 funds same-turn die purchase at turn upgrade cap."""
        cfg = GameConfig(num_players=2)
        engine = GameEngine(cfg, [StubPlanBot(0), StubPlanBot(1)], seed=42)
        p = engine.state.players[0]
        p.research_tokens = 2
        p.patent_level = 0
        p.defense_level = 0

        cost = engine.state.get_market_die_cost(DieColor.RED)
        p.money = cost - 3  # PR L1 breakthrough awards $3

        plan = Phase3ActionPlan(
            track_upgrades=["PATENT", "DEFENSE"],
            market_purchases=[DieColor.RED],
        )
        phase6_operations.execute_player_operations_turn(engine, p, plan)

        self.assertEqual(p.patent_level, 1)
        self.assertEqual(p.defense_level, 1)
        self.assertEqual(p.research_tokens, 0)
        self.assertEqual(p.money, 0)
        self.assertTrue(any(d.color == DieColor.RED for d in p.ready_for_release_dice))
        self.assertEqual(p.excess_hardware_upgrades_requested, 0)

    def test_rul_06_telemetry_records_excess_requested_upgrades(self):
        """TEST-RUL-06: Telemetry accurately records rejected excess upgrade requests."""
        cfg = GameConfig(num_players=2)
        plan = Phase3ActionPlan(track_upgrades=["DEFENSE", "DEFENSE", "RELEASE", "TRIAGE"])
        engine = GameEngine(cfg, [StubPlanBot(0, plan), StubPlanBot(1)], seed=42)
        p0 = engine.state.players[0]
        p0.research_tokens = 10

        tel = engine.run_round()

        self.assertEqual(p0.excess_hardware_upgrades_requested, 2)
        self.assertEqual(tel.excess_hardware_upgrades_by_player.get(0), 2)
        self.assertEqual(len(tel.track_upgrades_by_player[0]), 2)

    def test_rul_07_web_controller_rejects_3rd_upgrade(self):
        """TEST-RUL-07: Web controller rejects 3rd upgrade and updates capabilities."""
        gc = GameController()
        gc.new_game(num_players=2, seed=42)
        gc.phase = int(RoundPhase.OPERATIONS)
        gc.active_player_index = 0

        p0 = gc.state.players[0]
        p0.research_tokens = 10
        p0.defense_level = 0
        p0.release_level = 0
        p0.triage_level = 0
        p0.patent_level = 0

        meta0 = gc.player_meta[0]
        meta0["upgrades_this_turn"] = 0

        # 1st upgrade: DEFENSE
        res1 = gc.upgrade_hardware_track(0, "DEFENSE")
        self.assertEqual(p0.defense_level, 1)
        self.assertEqual(meta0["upgrades_this_turn"], 1)

        # 2nd upgrade: RELEASE
        res2 = gc.upgrade_hardware_track(0, "RELEASE")
        self.assertEqual(p0.release_level, 1)
        self.assertEqual(meta0["upgrades_this_turn"], 2)

        # 3rd upgrade: should raise ValueError
        with self.assertRaises(ValueError) as ctx:
            gc.upgrade_hardware_track(0, "TRIAGE")
        self.assertIn("Hardware upgrade limit reached", str(ctx.exception))

        # Check capabilities: all tracks must have can_upgrade_track == False
        caps = gc.get_action_capabilities(0)
        can_upgrade = caps["can_upgrade_track"]
        for track_name, can_up in can_upgrade.items():
            self.assertFalse(can_up, f"Track {track_name} should not be upgradeable after reaching cap")

    def test_rul_08_bot_research_policy_honors_upgrade_limit(self):
        """TEST-RUL-08: Bot research policy generates at most 2 upgrades and diverts excess to regain."""
        cfg = GameConfig(num_players=2)
        engine = GameEngine(cfg, [StubPlanBot(0), StubPlanBot(1)], seed=42)
        p = engine.state.players[0]
        p.research_tokens = 10
        p.market_share = 12
        p.market_share_max = 20
        p.defense_level = 4  # Focus track complete so leftovers go to regain
        p.patent_level = 0

        bot = StubPlanBot(0, research_aware=True)
        bot.research_focus = ("DEFENSE", "TRIAGE", "RELEASE", "PATENT")
        bot.research_focus_mode = "fixed"

        plan = Phase3ActionPlan()
        plan = apply_research_policy(bot, plan, p, engine.state)

        self.assertLessEqual(len(plan.track_upgrades), 2)
        # Surplus research should be directed to Market Share regain
        self.assertGreater(plan.share_regain, 0)
        self.assertLessEqual(plan.share_regain, cfg.share_regain_cap_by_level[p.patent_level])


if __name__ == "__main__":
    unittest.main()
