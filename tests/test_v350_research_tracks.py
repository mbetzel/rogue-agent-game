"""Phase 43 (v0.35.0) Research Track Rebalance: five-level tracks, Breakthroughs, flat Client Company setup,
Purple not purchasable, Slush Fund once per game and the new Gray Legacy faces (spec R-01..R-32)."""

from __future__ import annotations

import json
import os
import random
import unittest
from typing import Optional

from sim.bots import (
    AccelerationistBot,
    AdaptiveBalancedBot,
    BaseBot,
    Phase3ActionPlan,
    RecklessSaboteurBot,
    SecOpsTurtleBot,
    VentureGreedBot,
)
from sim.bots.research_policy import ResearchPolicy, plan_research
from sim.config import CubeColor, DieColor, GameConfig, ResearchTrackModel, ShieldColor
from sim.engine import GameEngine, phase1_roll_deploy, phase4_attack_resolution, phase5_pipeline_shift, phase6_operations
from sim.engine import research_tracks as rt
from sim.engine.state import CompileResult
from sim.entities import (
    COMPANIES,
    WHITE_HATS,
    AbilityStatus,
    CompanyCode,
    Face,
    WhiteHatCode,
    create_colored_die,
    create_gray_die,
    effective_company,
)
from tests.test_v340_six_phase_sequence import ZERO, SixPhaseHarness, StubBot, noop_deck

BOT_CLASSES = [AdaptiveBalancedBot, SecOpsTurtleBot, VentureGreedBot, AccelerationistBot, RecklessSaboteurBot]
PLAIN = Face(name="x")


class PlanBot(StubBot):
    """Stub bot whose explicit Operations plan is NOT replaced by the research-aware policy."""

    research_aware = False

    def __init__(self, bot_id: int, plan: Optional[Phase3ActionPlan] = None, slush: Optional[bool] = None) -> None:
        super().__init__(bot_id, plan)
        self.slush = slush
        self.bt_calls = []

    def choose_slush_fund(self, player_state, game_state, potential_secret_loss):
        if self.slush is None:
            return super().choose_slush_fund(player_state, game_state, potential_secret_loss)
        return self.slush

    def choose_breakthrough(self, player_state, game_state, track, level, options):
        self.bt_calls.append((track, level))
        return super().choose_breakthrough(player_state, game_state, track, level, options)


class V035Harness(SixPhaseHarness):
    def make(self, n: int = 2, bots=None, **kw) -> GameEngine:
        bots = bots or [PlanBot(i) for i in range(n)]
        e = self.make_engine(n=n, bots=bots, **kw)
        self.assertTrue(e.config.is_v035_tracks or kw.get("research_track_model"))
        return e

    def ops(self, e: GameEngine, player, plan: Phase3ActionPlan) -> None:
        phase6_operations.execute_player_operations_turn(e, player, plan)

    def gray(self, face: Face = PLAIN):
        return self.die(DieColor.GRAY, face)


# ----------------------------------------------------------------------------------------------
# Costs, levels, timing
# ----------------------------------------------------------------------------------------------
class TestTrackCostsAndLevels(V035Harness):
    def test_r01_cost_sequence_and_max(self):
        e = self.make()
        p = e.state.players[0]
        for t in rt.TRACKS:
            p.research_tokens = 8
            costs = []
            while True:
                c = p.get_track_upgrade_cost(t)
                if c is None:
                    break
                costs.append(c)
                self.assertTrue(p.upgrade_track(t))
            self.assertEqual(costs, [1, 2, 2, 3], t)
            self.assertEqual(p.research_tokens, 0)
            self.assertIsNone(p.get_track_upgrade_cost(t))
            self.assertFalse(p.upgrade_track(t))
        p2 = e.state.players[1]
        p2.research_tokens = 0
        self.assertFalse(p2.upgrade_track("DEFENSE"))
        self.assertEqual((p2.defense_level, p2.research_tokens), (0, 0))
        # No company discount under v0.35 (Prometheus discount removed)
        p2.upgrade_discount = 1
        self.assertEqual(p2.get_track_upgrade_cost("DEFENSE"), 1)
        p2.research_tokens = 1
        p2.upgrade_track("DEFENSE")
        self.assertEqual(p2.get_track_upgrade_cost("DEFENSE"), 2)

    def test_r02_capacity_per_level(self):
        e = self.make()
        p = e.state.players[0]
        p.research_tokens = 30
        expect = {"DEFENSE": (2, 2, 3, 3, 4), "TRIAGE": (2, 2, 3, 3, 4), "RELEASE": (4, 4, 5, 5, 6)}
        for t, caps in expect.items():
            attr = rt.CAPACITY_ATTR[t]
            self.assertEqual(getattr(p, attr), caps[0])
            for lvl in range(1, 5):
                p.upgrade_track(t)
                self.assertEqual(getattr(p, attr), caps[lvl], (t, lvl))

    def test_r03_level_effects_apply_next_round(self):
        plan = Phase3ActionPlan(track_upgrades=["TRIAGE", "TRIAGE"])
        e = self.make(bots=[PlanBot(0, plan), PlanBot(1)])
        p0, p1 = e.state.players
        p0.research_tokens = 3  # L0->L1 (1) + L1->L2 (2)
        p0.glitched_dice.extend(self.gray() for _ in range(4))
        c = [self.deploy(e, p0, [self.gray(Face("+$1", money=1))]), self.deploy(e, p1, [])]
        self.force(e, c, {CubeColor.RED: 1})
        tel = e.run_round()
        self.assertEqual(len(tel.track_upgrades_by_player[0]), 2)
        self.assertEqual(p0.triage_bandwidth, 3)
        # Phase 5 ran before Phase 6, so this round's Conveyor Triage used the old Bandwidth 2
        self.assertEqual((len(p0.scanned_dice), len(p0.glitched_dice)), (2, 2))


class TestBreakthroughs(V035Harness):
    def test_r04_patents_l1_cash_funds_same_turn_purchase(self):
        e = self.make()
        p = e.state.players[0]
        p.money, p.research_tokens = 2, 1
        cost = e.state.get_market_die_cost(DieColor.RED)
        p.money = cost - 3
        self.ops(e, p, Phase3ActionPlan(track_upgrades=["PATENT"], market_purchases=[DieColor.RED]))
        self.assertEqual(p.patent_level, 1)
        self.assertEqual(p.money, 0)
        self.assertTrue(any(d.color == DieColor.RED for d in p.ready_for_release_dice))

    def test_r05_defense_l0_to_l3_in_order(self):
        e = self.make()
        p = e.state.players[0]
        p.research_tokens, p.secrets = 5, 8
        self.ops(e, p, Phase3ActionPlan(track_upgrades=["DEFENSE"] * 3))
        self.assertEqual(p.defense_level, 3)
        self.assertEqual(p.defense_capacity, 3)
        self.assertEqual([(b.track, b.level, b.outcome) for b in p.breakthroughs],
                         [("DEFENSE", 1, "TAKEN"), ("DEFENSE", 3, "TAKEN")])
        self.assertEqual(p.secrets, 9)
        grays = [d for d in p.ready_for_release_dice if d.color == DieColor.GRAY]
        self.assertEqual(len(grays), 1)
        self.assertEqual(p.level_reached_round["DEFENSE"], {1: 1, 2: 1, 3: 1})

    def _triage_l3_setup(self, e, p, money=0):
        p.triage_level, p.triage_bandwidth = 2, 3
        p.money = money
        gray = self.gray()
        p.ready_for_release_dice.append(gray)
        return gray

    def test_r06_patents_cash_funds_triage_l3_and_reverse_forfeits(self):
        e = self.make()
        p = e.state.players[0]
        self._triage_l3_setup(e, p)
        p.research_tokens = 3
        self.ops(e, p, Phase3ActionPlan(track_upgrades=["PATENT", "TRIAGE"]))
        out = {(b.track, b.level): b.outcome for b in p.breakthroughs}
        self.assertEqual(out, {("PATENT", 1): "TAKEN", ("TRIAGE", 3): "TAKEN"})
        self.assertEqual(p.money, 0)

        e = self.make()
        p = e.state.players[0]
        self._triage_l3_setup(e, p)
        p.research_tokens = 3
        self.ops(e, p, Phase3ActionPlan(track_upgrades=["TRIAGE", "PATENT"]))
        out = {(b.track, b.level): b.outcome for b in p.breakthroughs}
        self.assertEqual(out, {("TRIAGE", 3): "FORFEITED", ("PATENT", 1): "TAKEN"})
        self.assertEqual(p.money, 3)

    def test_r06b_unaffordable_step_stops_the_plan(self):
        e = self.make()
        p = e.state.players[0]
        p.research_tokens = 2
        self.ops(e, p, Phase3ActionPlan(track_upgrades=["DEFENSE", "DEFENSE", "RELEASE"]))
        self.assertEqual((p.defense_level, p.release_level, p.research_tokens), (1, 0, 1))

    def test_r07_no_double_breakthrough(self):
        e = self.make()
        p = e.state.players[0]
        p.research_tokens = 10
        rt.upgrade_and_resolve(e, p, "DEFENSE")
        self.assertIsNone(rt.resolve_breakthrough(e, p, "DEFENSE", 1))
        p.defense_level = 0  # test setter re-reach
        rt.upgrade_and_resolve(e, p, "DEFENSE")
        self.assertEqual(len([b for b in p.breakthroughs if b.track == "DEFENSE"]), 1)
        # pipeline_level setter never resolves Breakthroughs (E17)
        p.pipeline_level = 3
        self.assertFalse(any(b.track in ("TRIAGE", "RELEASE") for b in p.breakthroughs))

    def test_r08_breakthrough_dice_go_to_ready(self):
        e = self.make()
        p = e.state.players[0]
        p.research_tokens = 30
        bw = p.release_bandwidth
        for t in ("DEFENSE", "RELEASE", "PATENT", "PATENT", "PATENT"):
            rt.upgrade_and_resolve(e, p, t)
        colors = sorted(d.color.value for d in p.ready_for_release_dice)
        self.assertEqual(colors, ["gray", "gray", "purple"])
        self.assertEqual(p.personal_purple_reserve, 0)
        self.assertEqual(p.release_bandwidth, 4 if bw == 4 else bw)
        self.assertEqual(p.release_level, 1)
        # Triage L1: 2 White Contractors held with the active pool (expire at the end of next Phase 4)
        supply = e.state.contractor_supply
        rt.upgrade_and_resolve(e, p, "TRIAGE")
        self.assertEqual(len(p.contractor_dice), 2)
        self.assertEqual(e.state.contractor_supply, supply - 2)
        self.assertEqual(p.hired_contractor_count, 0)  # not counted toward pricing / hire limit (OQ-6)

    def test_r08b_triage_l1_short_supply(self):
        e = self.make()
        p = e.state.players[0]
        p.research_tokens = 1
        e.state.contractor_supply = 1
        rec = rt.upgrade_and_resolve(e, p, "TRIAGE")
        self.assertEqual(rec.detail["contractors"], 1)
        self.assertEqual(rec.detail["short"], 1)
        self.assertEqual(e.state.contractor_supply, 0)

    def test_r09_triage_l3_happy_path_each_color(self):
        for color in rt.MARKET_COLORS:
            e = self.make()
            p = e.state.players[0]
            gray = self._triage_l3_setup(e, p, money=5)
            p.research_tokens = 2
            stock = e.state.market[color]
            rec = rt.upgrade_and_resolve(e, p, "TRIAGE", rt.BreakthroughChoice(True, gray.die_id, color))
            self.assertEqual(rec.outcome, "TAKEN", color)
            self.assertEqual(p.money, 2)
            self.assertEqual(e.state.market[color], stock - 1)
            self.assertNotIn(gray, p.total_dice)
            new = [d for d in p.ready_for_release_dice if d.color == color]
            self.assertEqual(len(new), 1)
            self.assertEqual(new[0].variant_code, e.state.variant_cards[color].code)
            self.assertEqual(p.triage_l3_upgrade_color, color.value)

    def test_r10_triage_l3_unaffordable(self):
        e = self.make()
        p = e.state.players[0]
        gray = self._triage_l3_setup(e, p, money=2)
        p.research_tokens = 2
        market = dict(e.state.market)
        rec = rt.upgrade_and_resolve(e, p, "TRIAGE")
        self.assertEqual(rec.outcome, "FORFEITED")
        self.assertEqual((p.money, dict(e.state.market)), (2, market))
        self.assertIn(gray, p.ready_for_release_dice)

    def test_r11_triage_l3_no_gray(self):
        e = self.make()
        p = e.state.players[0]
        self._triage_l3_setup(e, p, money=9)
        p.ready_for_release_dice.clear()
        p.research_tokens = 2
        self.assertEqual(rt.upgrade_and_resolve(e, p, "TRIAGE").outcome, "FORFEITED")
        self.assertEqual(p.money, 9)

    def test_r12_triage_l3_market_empty(self):
        e = self.make()
        p = e.state.players[0]
        self._triage_l3_setup(e, p, money=9)
        for c in rt.MARKET_COLORS:
            e.state.market[c] = 0
        p.research_tokens = 2
        rec = rt.upgrade_and_resolve(e, p, "TRIAGE")
        self.assertEqual((rec.outcome, p.money), ("FORFEITED", 9))
        # One color empty: that color is illegal, another is taken
        e = self.make()
        p = e.state.players[0]
        self._triage_l3_setup(e, p, money=9)
        e.state.market[DieColor.YELLOW] = 0
        self.assertNotIn(DieColor.YELLOW, rt.triage_l3_options(e, p).colors)
        p.research_tokens = 2
        rec = rt.upgrade_and_resolve(e, p, "TRIAGE", rt.BreakthroughChoice(True, None, DieColor.YELLOW))
        self.assertEqual(rec.outcome, "TAKEN")
        self.assertNotEqual(rec.detail["new_color"], "yellow")

    def test_r13_triage_l3_zones_and_decline(self):
        for zone in ("glitched_dice", "scanned_dice", "ready_for_release_dice"):
            e = self.make()
            p = e.state.players[0]
            p.triage_level, p.money, p.research_tokens = 2, 3, 2
            g = self.gray()
            getattr(p, zone).append(g)
            rec = rt.upgrade_and_resolve(e, p, "TRIAGE", rt.BreakthroughChoice(True, g.die_id, DieColor.RED))
            self.assertEqual(rec.outcome, "TAKEN", zone)
            self.assertNotIn(g, getattr(p, zone))
            self.assertTrue(any(d.color == DieColor.RED for d in p.ready_for_release_dice))
        # Bot default order: Glitched first
        e = self.make()
        p = e.state.players[0]
        a, b, c = self.gray(), self.gray(), self.gray()
        p.ready_for_release_dice.append(a)
        p.scanned_dice.append(b)
        p.glitched_dice.append(c)
        self.assertEqual(rt.triage_l3_options(e, p).gray_die_ids, [c.die_id, b.die_id, a.die_id])
        # Decline
        e = self.make()
        p = e.state.players[0]
        self._triage_l3_setup(e, p, money=9)
        p.research_tokens = 2
        rec = rt.upgrade_and_resolve(e, p, "TRIAGE", rt.BreakthroughChoice(accept=False))
        self.assertEqual((rec.outcome, p.money), ("DECLINED", 9))
        # Not deferred: reaching L4 later gives nothing
        p.research_tokens = 3
        self.assertIsNone(rt.upgrade_and_resolve(e, p, "TRIAGE"))


# ----------------------------------------------------------------------------------------------
# Purple, retired perks, setup, Slush Fund
# ----------------------------------------------------------------------------------------------
class TestRulesRemovals(V035Harness):
    def test_r14_purple_purchase_ignored(self):
        e = self.make()
        p = e.state.players[0]
        p.money = 30
        self.ops(e, p, Phase3ActionPlan(market_purchases=[DieColor.PURPLE, DieColor.RED, DieColor.BLUE], buy_purple_reserve=True))
        self.assertEqual(sorted(d.color.value for d in p.ready_for_release_dice), ["blue", "red"])
        self.assertEqual(p.personal_purple_reserve, 1)
        self.assertGreaterEqual(p.rejected_purple_purchases, 1)

    def test_r15_prometheus_purple_rejected_market_and_cash_work(self):
        e = self.make()
        p = e.state.players[0]
        p.company = COMPANIES[CompanyCode.PROMETHEUS]
        p.ability_v1_status = AbilityStatus.AVAILABLE
        p.money = 20
        self.ops(e, p, Phase3ActionPlan(use_prometheus_override=True, prometheus_mode="DISCOUNT",
                                         prometheus_discount_die_color=DieColor.PURPLE))
        self.assertEqual((p.money, p.personal_purple_reserve), (20, 1))
        self.assertTrue(p.is_ability_available("v1.0"))
        cost = e.state.get_market_die_cost(DieColor.GREEN)
        self.ops(e, p, Phase3ActionPlan(use_prometheus_override=True, prometheus_mode="DISCOUNT",
                                         prometheus_discount_die_color=DieColor.GREEN))
        self.assertEqual(p.money, 20 - max(0, cost - e.config.cipher_market_discount))
        p.ability_v1_status = AbilityStatus.AVAILABLE
        m = p.money
        self.ops(e, p, Phase3ActionPlan(use_prometheus_override=True, prometheus_mode="CASH"))
        self.assertEqual(p.money, m + e.config.cipher_arbitrage_cash)

    def test_r16_no_hotfix_no_firewall(self):
        e = self.make()
        p0, p1 = e.state.players
        p0.research_tokens = 6
        for _ in range(2):
            p0.upgrade_track("TRIAGE")
            p0.upgrade_track("DEFENSE")
        p0.has_emergency_hotfix = True
        p0.has_passive_firewall = True
        self.assertFalse(p0.has_emergency_hotfix or p0.has_passive_firewall)
        p0.glitched_dice.append(self.die(DieColor.RED, PLAIN, cost=5))
        self.assertEqual(phase5_pipeline_shift.apply_hotfix_bypass(e, p0), [])
        p0.secrets = 8
        self.run_phases_2_to_4(e, [self.deploy(e, p0, []), self.deploy(e, p1, [])], {CubeColor.BLUE: 1})
        self.assertEqual(p0.secrets, 7)

    def test_r17_flat_setup_all_companies(self):
        for code in CompanyCode:
            comps = [COMPANIES[code], COMPANIES[[c for c in CompanyCode if c != code][0]]]
            cfg = GameConfig.legacy_v035(num_players=2, enable_corporate_asymmetry=True)
            e = GameEngine(cfg, [PlanBot(0), PlanBot(1)], seed=3, version_deck=noop_deck(), companies=comps)
            p = e.state.players[0]
            self.assertEqual((p.money, p.secrets, p.research_tokens), (6, 8, 0), code)
            self.assertEqual((p.defense_level, p.triage_level, p.release_level, p.patent_level), (0, 0, 0, 0), code)
            self.assertEqual((p.defense_capacity, p.triage_bandwidth, p.release_bandwidth), (2, 2, 4), code)
            self.assertEqual(p.upgrade_discount, 0)
            self.assertEqual(effective_company(COMPANIES[code], cfg).starting_cash_bonus, 0)
        # Legacy still applies bonuses
        cfg = GameConfig.legacy_v034(num_players=2, enable_corporate_asymmetry=True)
        e = GameEngine(cfg, [PlanBot(0), PlanBot(1)], seed=3, version_deck=noop_deck(),
                       companies=[COMPANIES[CompanyCode.MERIDIAN], COMPANIES[CompanyCode.DTO]])
        self.assertEqual(e.state.players[0].money, 8)

    def _dto(self, slush=None):
        e = self.make(bots=[PlanBot(0, slush=slush), PlanBot(1)])
        p0 = e.state.players[0]
        p0.company = COMPANIES[CompanyCode.DTO]
        p0.white_hat = WHITE_HATS[WhiteHatCode.OPERATOR]
        p0.ability_v1_status = AbilityStatus.AVAILABLE
        return e, p0, e.state.players[1]

    def test_r18_slush_fund_once_per_game(self):
        e, p0, p1 = self._dto()
        p0.secrets = 8
        self.run_phases_2_to_4(e, [self.deploy(e, p0, []), self.deploy(e, p1, [])], {CubeColor.BLUE: 2})
        self.assertEqual(p0.secrets, 8)
        self.assertTrue(p0.slush_fund_used_game)
        p0.unlock_version_ability("v2.0")
        e.state.current_version_index = 1
        self.assertFalse(p0.is_slush_fund_available("v2.0"))
        self.run_phases_2_to_4(e, [self.deploy(e, p0, []), self.deploy(e, p1, [])], {CubeColor.BLUE: 2})
        self.assertEqual(p0.secrets, 6)
        # Optional: default bot declines on a 1-Secret loss
        e, p0, p1 = self._dto()
        self.run_phases_2_to_4(e, [self.deploy(e, p0, []), self.deploy(e, p1, [])], {CubeColor.BLUE: 1})
        self.assertEqual((p0.secrets, p0.slush_fund_used_game), (7, False))
        # ... but takes it when the loss would cause a Total Data Breach
        e, p0, p1 = self._dto()
        p0.secrets = 1
        self.run_phases_2_to_4(e, [self.deploy(e, p0, []), self.deploy(e, p1, [])], {CubeColor.BLUE: 1})
        self.assertEqual((p0.secrets, p0.is_patient_zero), (1, False))
        # Bot hook can force a decline
        e, p0, p1 = self._dto(slush=False)
        self.run_phases_2_to_4(e, [self.deploy(e, p0, []), self.deploy(e, p1, [])], {CubeColor.BLUE: 2})
        self.assertEqual(p0.secrets, 6)


# ----------------------------------------------------------------------------------------------
# Level 4 effects and Patents
# ----------------------------------------------------------------------------------------------
class TestLevel4Effects(V035Harness):
    def _shield_round(self, n_blocked, defense_level=4, buffer_overflow=False, black_only=False):
        e = self.make()
        p0, p1 = e.state.players
        p0.defense_level = defense_level
        p0.money = 0
        shields = [self.die(DieColor.GRAY, Face("Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)) for _ in range(5)]
        c0 = self.deploy(e, p0, shields, {i: ShieldColor.ANY for i in range(5)})
        c = [c0, self.deploy(e, p1, [])]
        if buffer_overflow or black_only:
            exits = dict(ZERO)
            if black_only:
                exits[CubeColor.BLACK] = 2
            else:
                exits[CubeColor.BLUE] = n_blocked
            cr = CompileResult(staged_before=dict(ZERO), stuck_before=dict(ZERO), exited_cubes=exits,
                               stuck_after=dict(ZERO), buffer_overflow=buffer_overflow)
            phase4_attack_resolution.execute_attack_resolution(e, c, cr)
        else:
            self.run_phases_2_to_4(e, c, {CubeColor.BLUE: n_blocked} if n_blocked else {CubeColor.BLACK: 1})
        return p0

    def test_r19_defense_l4_cash(self):
        for blocked, cash in ((0, 0), (1, 1), (3, 3), (5, 3)):
            p0 = self._shield_round(blocked)
            self.assertEqual(p0.money, cash, blocked)
            self.assertEqual(p0.l4_payouts["defense_cash"], cash)
        self.assertEqual(self._shield_round(3, defense_level=3).money, 0)

    def test_r20_defense_l4_overflow_black_and_baffle_echo(self):
        self.assertEqual(self._shield_round(3, buffer_overflow=True).money, 0)
        self.assertEqual(self._shield_round(0, black_only=True).money, 0)
        # Baffle Echo-ignored cube is not "blocked"
        e = self.make()
        p0, p1 = e.state.players
        p0.company = COMPANIES[CompanyCode.AEGIS]
        p0.ability_v1_status = AbilityStatus.AVAILABLE
        p0.defense_level, p0.money = 4, 0
        self.run_phases_2_to_4(e, [self.deploy(e, p0, []), self.deploy(e, p1, [])], {CubeColor.BLUE: 1})
        self.assertFalse(p0.is_ability_available("v1.0"))
        self.assertEqual((p0.money, p0.secrets), (0, 8))

    def test_r21_triage_l4_research(self):
        for moved, gain in ((2, 0), (3, 1), (4, 2)):
            e = self.make()
            p = e.state.players[0]
            p.triage_level, p.triage_bandwidth, p.research_tokens = 4, 4, 0
            p.glitched_dice.extend(self.gray() for _ in range(moved))
            phase5_pipeline_shift.execute_player_pipeline_shift(e, p, graduate_die_ids=[])
            self.assertEqual(p.research_tokens, gain, moved)
            self.assertEqual(p.research_earned_by_source.get("triage_l4", 0), gain)
        e = self.make()
        p = e.state.players[0]
        p.triage_level, p.triage_bandwidth = 3, 4
        p.glitched_dice.extend(self.gray() for _ in range(4))
        phase5_pipeline_shift.execute_player_pipeline_shift(e, p, graduate_die_ids=[])
        self.assertEqual(p.research_tokens, 0)

    def test_r22_release_l4_reroll(self):
        cfg = GameConfig.legacy_v035(num_players=2)
        e = self.make()
        p = e.state.players[0]
        self.assertEqual(rt.free_rerolls_for(cfg, p, 2), 2)
        p.release_level = 4
        self.assertEqual(rt.free_rerolls_for(cfg, p, 2), 3)
        self.assertEqual(rt.free_rerolls_for(cfg, p, 1), 2)  # throttle first, then +1 (OQ-7)
        self.assertEqual(rt.free_rerolls_for(GameConfig.legacy_v034(), p, 2), 2)

        class RerollBot(PlanBot):
            def __init__(self, i):
                super().__init__(i)
                self.helix_seen = None
                self.calls = 0

            def choose_helix_override(self, player_state, active_dice, rerolls_remaining, *a, **k):
                self.helix_seen = rerolls_remaining
                return False

            def choose_yahtzee_rerolls(self, player_state, active_dice, rerolls_remaining, *a, **k):
                self.calls += 1
                return [0]

            def choose_contractor_hires(self, *a, **k):
                return 0

        bot = RerollBot(0)
        e = self.make(bots=[bot, PlanBot(1)])
        p0 = e.state.players[0]
        p0.company = COMPANIES[CompanyCode.HELIX]
        p0.ability_v1_status = AbilityStatus.AVAILABLE
        p0.release_level = 4
        p0.ready_for_release_dice.append(create_gray_die(990))
        phase1_roll_deploy.execute_phase_1(e)
        self.assertEqual(bot.helix_seen, 3)
        self.assertEqual(bot.calls, 3)
        self.assertEqual(p0.l4_payouts["release_rerolls_used"], 1)

    def test_r23_patent_rates(self):
        e = self.make()
        p = e.state.players[0]
        for lvl, (cost, gain) in {0: (2, 1), 1: (2, 1), 2: (3, 2), 3: (3, 2), 4: (1, 1)}.items():
            p.patent_level = lvl
            p.research_tokens, p.secrets, p.money = cost * 2, 5, 0
            self.assertEqual((p.get_patent_cost(), p.get_patent_gain()), (cost, gain))
            self.assertTrue(p.file_patent())
            self.assertTrue(p.file_patent())
            self.assertFalse(p.file_patent())
            self.assertEqual((p.secrets, p.money, p.research_tokens), (5 + 2 * gain, 0, 0), lvl)
        self.assertEqual(p.l4_payouts["patent_secrets"], 2)
        # Filing after a same-turn Patents upgrade uses the new rate
        e = self.make()
        p = e.state.players[0]
        p.patent_level, p.research_tokens, p.secrets = 1, 5, 5
        self.ops(e, p, Phase3ActionPlan(track_upgrades=["PATENT"], patent_filings=5))
        self.assertEqual((p.patent_level, p.secrets, p.research_tokens), (2, 7, 0))

    def test_r24_gray_faces(self):
        v35 = [f.name for f in create_gray_die(1).faces]
        self.assertEqual(v35, ["Block 1 Any", "Block 1 Any", "+$1 & +1 🔬", "+$1 / +1 🔬", "+$1 / +1 🔬", "+1 🔬"])
        self.assertEqual((create_gray_die(1).faces[2].money, create_gray_die(1).faces[2].patches), (1, 1))
        v34 = [f.name for f in create_gray_die(1, "V034").faces]
        self.assertEqual(v34, ["Block 1 Any", "Block 1 Any", "+$1", "+$1", "+$1 / +1 🔬", "+1 🔬"])
        e = GameEngine(GameConfig.legacy_v035(num_players=2), seed=1)
        for p in e.state.players:
            for d in p.ready_for_release_dice:
                if d.color == DieColor.GRAY:
                    self.assertEqual([f.name for f in d.faces], v35)
        e = GameEngine(GameConfig.legacy_v034(num_players=2), seed=1)
        gray = [d for d in e.state.players[0].ready_for_release_dice if d.color == DieColor.GRAY][0]
        self.assertEqual([f.name for f in gray.faces], v34)
        self.assertFalse(any("🔧" in f.name for f in create_gray_die(1).faces + create_gray_die(1, "V034").faces))


# ----------------------------------------------------------------------------------------------
# Whole-game invariants, parity, determinism, policy, telemetry
# ----------------------------------------------------------------------------------------------
def _run(seed: int, n: int, cfg_factory=GameConfig.legacy_v035, mode: str = "fixed"):
    bots = [BOT_CLASSES[(seed + i) % 5](i) for i in range(n)]
    for b in bots:
        b.research_focus_mode = mode
    e = GameEngine(cfg_factory(num_players=n), bots, seed=seed)
    return e, e.run_game()


class TestWholeGame(unittest.TestCase):
    def test_r25_research_ledger(self):
        for seed in range(300):
            e, r = _run(seed, 2 + seed % 3)
            for p in e.state.players:
                spent = sum(p.research_spent_tracks.values()) + p.research_spent_patents
                self.assertEqual(
                    p.starting_research + p.research_earned_total - spent - p.research_lost_total,
                    p.research_tokens, (seed, p.player_id))
                self.assertGreaterEqual(p.research_tokens, 0)
                for t in rt.TRACKS:
                    self.assertIn(rt.level_of(p, t), range(5))
                self.assertFalse(p.has_emergency_hotfix or p.has_passive_firewall)
                purples = sum(1 for d in p.total_dice if d.color == DieColor.PURPLE)
                patent_l3 = any(b.track == "PATENT" and b.level == 3 and b.outcome == "TAKEN" for b in p.breakthroughs)
                self.assertLessEqual(purples, 1 + int(patent_l3))
                self.assertEqual(p.personal_purple_reserve, 0 if patent_l3 else 1)
            self.assertEqual(e.state.contractor_supply, e.config.contractor_supply_total, seed)

    def test_r26_v034_parity_fixtures(self):
        from tests.fixtures.v034_parity import capture

        for scenario in capture.SCENARIOS:
            for n in capture.PLAYER_COUNTS:
                with open(capture.fixture_path(scenario, n), encoding="utf-8") as fh:
                    golden = json.load(fh)
                for seed in capture.SEEDS:
                    got = json.loads(json.dumps(capture.run_scenario(GameConfig.legacy_v034, scenario, n, seed), sort_keys=True))
                    self.assertEqual(got, golden[str(seed)], f"{scenario} {n}P seed {seed}")

    def test_r27_v033_parity_fixtures(self):
        from tests.fixtures.v033_parity import capture

        self.assertEqual(GameConfig.legacy_v033().research_track_model, ResearchTrackModel.V034_THREE_LEVEL)
        for scenario in capture.SCENARIOS:
            for n in capture.PLAYER_COUNTS:
                with open(capture.fixture_path(scenario, n), encoding="utf-8") as fh:
                    golden = json.load(fh)
                for seed in capture.SEEDS:
                    got = json.loads(json.dumps(capture.run_scenario(GameConfig.legacy_v033, scenario, n, seed), sort_keys=True))
                    self.assertEqual(got, golden[str(seed)])

    def test_r28_determinism(self):
        def sig(r):
            return json.dumps([r.end_reason.value, r.total_rounds, r.rankings], sort_keys=True, default=str)

        for mode in ("fixed", "random"):
            for seed in range(100):
                a = sig(_run(seed, 2 + seed % 3, mode=mode)[1])
                b = sig(_run(seed, 2 + seed % 3, mode=mode)[1])
                self.assertEqual(a, b, (mode, seed))

    def test_r30_telemetry(self):
        for seed in range(40):
            e, r = _run(seed, 3)
            for row in r.rankings:
                p = e.state.players[row["player_id"]]
                lv = row["final_track_levels"]
                self.assertEqual(lv, {t: rt.level_of(p, t) for t in rt.TRACKS})
                reached = sum(1 for t in rt.TRACKS for L in (1, 3) if lv[t] >= L)
                self.assertEqual(len(row["breakthroughs"]), reached)
                for key in ("research_earned_total", "research_earned_by_source", "research_spent_tracks",
                            "research_spent_patents", "patent_secrets_gained", "level_reached_round", "l4_payouts",
                            "purple_dice_owned_final", "gray_dice_owned_final", "triage_l3_upgrade_color"):
                    self.assertIn(key, row)
                self.assertEqual(row["research_earned_total"], sum(row["research_earned_by_source"].values()))
                self.assertEqual(
                    sum(t.research_gained_by_player.get(p.player_id, 0) for t in r.telemetry_history),
                    row["research_earned_total"])
                self.assertEqual(
                    sum(len(t.breakthroughs_by_player.get(p.player_id, [])) for t in r.telemetry_history),
                    len(row["breakthroughs"]))

    @unittest.skipUnless(os.environ.get("RUN_SLOW"), "slow sweep reproduction (set RUN_SLOW=1)")
    def test_r32_sweep_reproduction(self):
        from scripts.run_v350_research_track_check import run

        out = run(200, 4300)
        print("R-32", out)
        self.assertLessEqual(abs(out["mean_research"] - 12.1), 1.0)
        self.assertLessEqual(abs(out["by_p"][2]["singularity"] - 0.455), 0.04)


class TestResearchPolicy(unittest.TestCase):
    class _P:
        def __init__(self, research=0, **lv):
            self.research_tokens = research
            self.defense_level = lv.get("DEFENSE", 0)
            self.triage_level = lv.get("TRIAGE", 0)
            self.release_level = lv.get("RELEASE", 0)
            self.patent_level = lv.get("PATENT", 0)
            self.secrets = 8
            self.is_patient_zero = False

    class _S:
        def __init__(self, players, final=False):
            self.players = players
            self.is_final_round = final

    def plan(self, p, final=False, order=("TRIAGE", "DEFENSE", "RELEASE", "PATENT"), others=None):
        s = self._S([p] + (others or []), final)
        return plan_research(ResearchPolicy(focus_order=order), p, s, GameConfig.legacy_v035())

    def test_r29_policy(self):
        # Focus first up to L4 (1+2+2+3 = 8)
        self.assertEqual(self.plan(self._P(8)), (["TRIAGE"] * 4, 0))
        # Save when short: 2 research buys L1 (1) then can't afford L2 (2) -> stop
        self.assertEqual(self.plan(self._P(2)), (["TRIAGE"], 0))
        # Focus done -> L1 on each other track, then L2 of 2nd track
        self.assertEqual(self.plan(self._P(5, TRIAGE=4)), (["DEFENSE", "RELEASE", "PATENT", "DEFENSE"], 0))
        # Everything bought + research >= 4 -> file Patents with the rest at the post-upgrade rate
        up, filings = self.plan(self._P(9, TRIAGE=4))
        self.assertEqual(up, ["DEFENSE", "RELEASE", "PATENT", "DEFENSE"])
        self.assertEqual(filings, (9 - 5) // 2)
        # Late game (any survivor <= 3 Secrets): no upgrades, file everything
        other = self._P(0)
        other.secrets = 3
        self.assertEqual(self.plan(self._P(6, PATENT=2), others=[other]), ([], 2))
        self.assertEqual(self.plan(self._P(5), final=True), ([], 2))
        # Bot classes carry the focus orders
        self.assertEqual(VentureGreedBot(0).research_focus, ("PATENT", "RELEASE", "DEFENSE", "TRIAGE"))
        self.assertEqual(SecOpsTurtleBot(0).research_focus[0], "DEFENSE")
        self.assertEqual(AccelerationistBot(0).research_focus[0], "RELEASE")
        self.assertEqual(RecklessSaboteurBot(0).research_focus[0], "PATENT")
        self.assertEqual(AdaptiveBalancedBot(0).research_focus[0], "TRIAGE")

    def test_r29b_policy_replaces_plan_and_takes_research_on_choice_faces(self):
        from sim.bots.research_policy import adjust_declared_choices

        e = GameEngine(GameConfig.legacy_v035(num_players=2), seed=5)
        p = e.state.players[0]
        p.research_tokens = 3
        plan = phase6_operations.resolve_operations_plan(p.bot, p, e.state, e.rng)
        self.assertEqual(plan.track_upgrades, ["TRIAGE", "TRIAGE"])
        self.assertNotIn(DieColor.PURPLE, plan.market_purchases)
        self.assertFalse(plan.buy_purple_reserve)
        g = create_gray_die(77)
        g.current_face = g.faces[3]
        self.assertEqual(adjust_declared_choices(p.bot, p, [g], {0: 0}, e.config), {0: 1})
        self.assertEqual(adjust_declared_choices(p.bot, p, [g], {0: 0}, GameConfig.legacy_v034()), {0: 0})


class TestWebV035(unittest.TestCase):
    def test_r31_web_round_trip(self):
        from web.game_controller import GameController

        ctrl = GameController()
        st = ctrl.new_game(num_players=2, seed=42)
        self.assertEqual(st["players"][0]["max_track_level"], 4)
        self.assertEqual(st["players"][0]["research_track_model"], "V035_FIVE_LEVEL")
        self.assertFalse(st["players"][0]["can_buy_purple_reserve"])
        ctrl.phase = 6
        ctrl.active_player_index = 0
        p0 = ctrl.state.players[0]
        caps = ctrl.get_action_capabilities(0)
        self.assertNotIn("can_buy_purple_reserve", caps)
        self.assertNotIn("purple", caps["can_buy"])
        self.assertIn("breakthrough_preview", caps)
        with self.assertRaises(ValueError):
            ctrl.buy_die(0, "purple") if hasattr(ctrl, "buy_die") else ctrl.buy(0, "purple")
        p0.triage_level, p0.triage_bandwidth = 2, 3
        p0.research_tokens, p0.money = 2, 5
        ctrl.upgrade_track(0, "triage")
        caps = ctrl.get_action_capabilities(0)
        self.assertIsNotNone(caps["pending_breakthrough"])
        self.assertFalse(caps["can_file_patent"])
        opts = caps["pending_breakthrough"]["options"]
        gray_id = opts["gray_die_ids"][0]
        state = ctrl.resolve_breakthrough(0, accept=True, gray_die_id=gray_id, color="green")
        self.assertIsNone(ctrl.get_action_capabilities(0)["pending_breakthrough"])
        self.assertEqual(p0.money, 2)
        self.assertTrue(any(d.color == DieColor.GREEN for d in p0.ready_for_release_dice))
        self.assertEqual(state["players"][0]["breakthroughs"][-1]["outcome"], "TAKEN")
        # Levels serialize up to 4
        p0.research_tokens = 3
        ctrl.upgrade_track(0, "triage")
        self.assertEqual(ctrl.get_full_state()["players"][0]["triage_level"], 4)

    def _web_dto_phase4(self, seed=3):
        from web.game_controller import GameController
        from web.controller import phase4_attack_actions as w4

        ctrl = GameController()
        ctrl.new_game(num_players=2, seed=seed, players_config=[
            {"is_human": True, "name": "H", "company": "DTO", "white_hat": "OPERATOR"},
            {"is_human": False, "name": "B", "company": "MERIDIAN"}])
        for _ in range(200):
            if ctrl.phase == 4 and ctrl.subphase == "confirm_attacks":
                return ctrl, w4
            st = ctrl.get_full_state()
            if ctrl.phase == 1:
                if not ctrl.player_meta[0]["has_rolled"]:
                    ctrl.roll_pool(0)
                ctrl.commit_defenses(0, {})
            elif ctrl.phase == 2:
                ctrl.compile_drop()
            elif ctrl.phase == 3:
                ctrl.confirm_income(0)
            elif ctrl.phase == 5:
                ctrl.choose_graduates(0, ctrl.pending_graduation[0]["default_graduate_ids"])
            elif ctrl.phase == 6:
                ctrl.end_turn(0)
            else:
                return None, None
        return None, None

    def test_r18b_web_human_slush_fund_choice(self):
        """OQ-5: a human DTO player chooses Slush Fund at Phase 4 confirmation; the bot hook never decides."""
        from sim.engine import phase4_attack_resolution as p4
        from web.controller import capabilities

        for use, expect_used in ((False, False), (True, True), (None, False)):
            ctrl, w4 = self._web_dto_phase4()
            self.assertIsNotNone(ctrl)
            p0 = ctrl.state.players[0]
            self.assertFalse(ctrl.get_action_capabilities(0)["can_spook"])  # no manual button under v0.35
            ctrl.attack_strengths = {CubeColor.RED: 0, CubeColor.BLUE: 3, CubeColor.GREEN: 0}
            p0.in_production_dice.clear()
            ctrl.player_meta[0]["commitments"] = {}
            p0.money = 0  # no cash absorption: only the free 2-Secret Slush Fund absorb
            secrets = p0.secrets
            ctrl.confirm_attacks(0, any_shield_allocations={}, glitch_die_ids=[], use_slush_fund=use)
            self.assertEqual(p0.slush_fund_used_game, expect_used, use)
            self.assertEqual(p0.secrets, secrets - (1 if expect_used else 3), use)

    def test_r31b_web_legacy_ruleset(self):
        from web.game_controller import GameController

        ctrl = GameController()
        st = ctrl.new_game(num_players=2, seed=42, research_track_model="V034_THREE_LEVEL")
        self.assertEqual(st["players"][0]["max_track_level"], 2)


if __name__ == "__main__":
    unittest.main()
