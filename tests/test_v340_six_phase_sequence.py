"""v0.34.0 Six-Phase Round Sequence, Release Bandwidth Routing & Flat Starting Secrets.

Spec: docs/specs/v340_six_phase_round_sequence_spec.md §11.1 (S-01..S-29) plus the §12.1 resolution
additions (graduate fewer than RB, two Purple ★ triggers, glitched Purple fires nothing, Total Wipeout
ranked purely by tiebreakers). S-30 (web state machine) lives in tests/test_web_api.py-style coverage at
the bottom of this module.
"""

from __future__ import annotations

import json
import os
import unittest
from typing import Dict, List, Optional
from unittest import mock

from sim.bots import AdaptiveBalancedBot, BaseBot, Phase3ActionPlan
from sim.config import (
    ResearchTrackModel,
    ROUND_PHASE_NAMES,
    CubeColor,
    DieColor,
    EndGameReason,
    GameConfig,
    RoundPhase,
    RoundSequence,
    ShieldColor,
)
from sim.engine import GameEngine
from sim.engine import (
    phase2_compiler,
    phase3_income,
    phase4_attack_resolution,
    phase5_pipeline_shift,
    phase6_operations,
)
from sim.engine.state import ProductionRole
from sim.entities import (
    COMPANIES,
    WHITE_HATS,
    AbilityStatus,
    CompanyCode,
    CorruptionSpace,
    Face,
    VersionCard,
    WhiteHatCode,
    create_colored_die,
    create_gray_die,
    create_white_die,
)

ZERO = {CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0}

INCOME_2 = Face(name="+$2", money=2)
INCOME_3 = Face(name="+$3", money=3)
INCOME_1 = Face(name="+$1", money=1)
BLOCK_BLUE = Face(name="Block 1 Blue", block_amount=1, shield_color=ShieldColor.BLUE)
BLOCK_RED = Face(name="Block 1 Red", block_amount=1, shield_color=ShieldColor.RED)
PURPLE_STAR = Face(name="Purple ★", is_star=True, star_code="PURPLE_STAR")
Y3_FACE = Face(name="Proprietary Training", secrets=1, is_star=True, star_code="Y3")
B3_FACE = Face(name="Air-Gapped Backup", is_star=True, star_code="B3")


class StubBot(BaseBot):
    """Deterministic bot: empty Operations plans (counted), default hooks."""

    def __init__(self, bot_id: int, plan: Optional[Phase3ActionPlan] = None) -> None:
        super().__init__(bot_id, name=f"Stub{bot_id}")
        self.ops_calls = 0
        self.plan = plan
        self.burn_ids: List[Optional[int]] = []
        self.graduate_override: Optional[List[int]] = None
        self.diag_calls: List[List[int]] = []

    def take_operations_actions(self, player_state, game_state, rng):
        self.ops_calls += 1
        return self.plan or Phase3ActionPlan()

    def choose_spook_burn_notice(self, player_state, game_state, rng):
        return self.burn_ids.pop(0) if self.burn_ids else None

    def choose_scanned_graduates(self, player_state, n, game_state=None, rng=None):
        if self.graduate_override is not None:
            return list(self.graduate_override)
        return super().choose_scanned_graduates(player_state, n, game_state, rng)

    def choose_phreaker_jumper_diagnostics(self, player_state, game_state, rng):
        self.diag_calls.append([d.die_id for d in player_state.under_development_dice])
        return super().choose_phreaker_jumper_diagnostics(player_state, game_state, rng)


def v1_card(*spaces: CorruptionSpace) -> VersionCard:
    return VersionCard(
        version_str="v1.0",
        name="Test v1.0",
        staging_payload={},
        directive_description="test",
        directive_code="SCRIPT_KIDDIE",
        corruption_track=tuple(spaces) or tuple(CorruptionSpace(index=i, label="noop") for i in range(1, 5)),
    )


def v3_card(*spaces: CorruptionSpace) -> VersionCard:
    return VersionCard(
        version_str="v3.0",
        name="Test v3.0",
        staging_payload={},
        directive_description="test",
        directive_code="ZERO_DAY_OVERRIDE",
        corruption_track=tuple(spaces),
    )


def noop_deck(first_space: Optional[CorruptionSpace] = None) -> List[VersionCard]:
    spaces = [CorruptionSpace(index=i, label="noop") for i in range(1, 5)]
    if first_space is not None:
        spaces[0] = first_space
    return [
        v1_card(*spaces),
        VersionCard("v2.0", "Test v2.0", {}, "test", "RAAS",
                    corruption_track=tuple(CorruptionSpace(index=i, label="noop") for i in range(1, 6))),
        v3_card(*[CorruptionSpace(index=i, label="noop") for i in range(1, 7)]),
    ]


class SixPhaseHarness(unittest.TestCase):
    """Builds a neutral engine (no companies / operatives / priming) with stub bots."""

    def make_engine(self, n: int = 2, deck=None, bots=None, **cfg_kw) -> GameEngine:
        cfg = GameConfig(num_players=n, enable_compiler_priming=False, **cfg_kw)
        bots = bots or [StubBot(i) for i in range(n)]
        e = GameEngine(cfg, bots, seed=7, version_deck=deck or noop_deck())
        for p in e.state.players:
            p.company = None
            p.white_hat = None
            p.ready_for_release_dice.clear()
            p.in_production_dice.clear()
            p.glitched_dice.clear()
            p.scanned_dice.clear()
            p.contractor_dice.clear()
            p.money = 0
            p.research_tokens = 0
            p.secrets = 8
        for c in e.state.staging_cup:
            e.state.staging_cup[c] = 0
        e.state.first_player_index = 0
        self._next_id = 500
        return e

    def die(self, color: DieColor, face: Face, cost: Optional[int] = None):
        self._next_id += 1
        if color == DieColor.GRAY:
            d = create_gray_die(self._next_id)
        elif color == DieColor.WHITE:
            d = create_white_die(self._next_id)
        else:
            d = create_colored_die(color, self._next_id, cost=cost)
        d.current_face = face
        return d

    def deploy(self, e: GameEngine, player, dice, shields: Optional[Dict[int, ShieldColor]] = None):
        """Place dice In Production (as Phase 1 would) and return the commitment tuple."""
        shields = shields or {}
        for idx, d in enumerate(dice):
            if idx in shields:
                d.production_role = ProductionRole(f"{shields[idx].value.upper()}_SHIELD")
            else:
                d.production_role = ProductionRole.INCOME
            player.in_production_dice.append(d)
            if d.color == DieColor.WHITE:
                player.contractor_dice.append(d)
                e.state.contractor_supply -= 1
        return (player, list(dice), dict(shields))

    def force(self, e: GameEngine, commitments, exits: Dict[CubeColor, int]):
        e._execute_phase_1 = lambda: commitments  # Phase 1 stub (instance override)
        full = dict(ZERO)
        full.update(exits)
        e.state.tower.drop = lambda cup, rng: dict(full)

    def run_phases_2_to_4(self, e, commitments, exits):
        self.force(e, commitments, exits)
        cr = phase2_compiler.execute_compiler_drop(e, commitments)
        phase2_compiler.check_end_triggers_after_compiler(e, cr)
        incomes = None
        if not e.state.game_over:
            incomes = phase3_income.execute_income(e, commitments)
            phase4_attack_resolution.execute_attack_resolution(e, commitments, cr)
        return cr, incomes

    @staticmethod
    def zone_ids(p):
        return (
            [d.die_id for d in p.ready_for_release_dice],
            [d.die_id for d in p.in_production_dice],
            [d.die_id for d in p.glitched_dice],
            [d.die_id for d in p.scanned_dice],
        )

    @staticmethod
    def white_anywhere(p) -> bool:
        zones = p.ready_for_release_dice + p.in_production_dice + p.glitched_dice + p.scanned_dice + p.contractor_dice
        return any(d.color == DieColor.WHITE for d in zones)


class TestSixPhaseIncomeTiming(SixPhaseHarness):
    def test_green_no_longer_removes_income(self):  # S-01
        e = self.make_engine()
        p0 = e.state.players[0]
        red = self.die(DieColor.RED, INCOME_2)
        c = [self.deploy(e, p0, [red]), self.deploy(e, e.state.players[1], [])]
        self.run_phases_2_to_4(e, c, {CubeColor.GREEN: 1})
        self.assertEqual(p0.money, 2)
        self.assertIn(red, p0.glitched_dice)

    def test_income_collected_once_between_phase2_and_phase4(self):  # S-02
        e = self.make_engine()
        p0, p1 = e.state.players
        c = [self.deploy(e, p0, [self.die(DieColor.GRAY, INCOME_1)]), self.deploy(e, p1, [self.die(DieColor.GRAY, INCOME_1)])]
        self.force(e, c, {CubeColor.RED: 1})
        order: List[str] = []
        orig_drop = phase2_compiler.execute_compiler_drop
        orig_collect = phase3_income.collect_player_production_income
        orig_def = phase4_attack_resolution.resolve_player_defense_and_wear

        def drop(*a, **k):
            order.append("compile")
            return orig_drop(*a, **k)

        def collect(engine, player, plan=None):
            order.append(f"income{player.player_id}")
            return orig_collect(engine, player, plan)

        def defense(*a, **k):
            order.append("defense")
            return orig_def(*a, **k)

        with mock.patch.object(phase2_compiler, "execute_compiler_drop", drop), \
                mock.patch.object(phase3_income, "collect_player_production_income", collect), \
                mock.patch.object(phase4_attack_resolution, "resolve_player_defense_and_wear", defense):
            e.run_round()
        self.assertEqual(order, ["compile", "income0", "income1", "defense", "defense"])

    def test_corruption_cash_loss_lands_before_income(self):  # S-03
        e = self.make_engine(deck=noop_deck(CorruptionSpace(index=1, label="All lose $2", lose_money=2)))
        p0 = e.state.players[0]
        p0.money = 1
        c = [self.deploy(e, p0, [self.die(DieColor.RED, INCOME_3)]), self.deploy(e, e.state.players[1], [])]
        self.force(e, c, {CubeColor.BLACK: 1})
        cr = phase2_compiler.execute_compiler_drop(e, c)
        self.assertEqual(p0.money, 0)
        phase3_income.execute_income(e, c)
        self.assertEqual(p0.money, 3)

    def test_corruption_glitch_and_return_before_income(self):  # S-04
        # Glitch 1 die
        e = self.make_engine(deck=noop_deck(CorruptionSpace(index=1, label="Glitch 1 die", demote_dice=1)))
        p0 = e.state.players[0]
        d = self.die(DieColor.RED, INCOME_3)
        c = [self.deploy(e, p0, [d]), self.deploy(e, e.state.players[1], [])]
        self.run_phases_2_to_4(e, c, {CubeColor.BLACK: 1})
        self.assertEqual(p0.money, 0)
        self.assertIn(d, p0.glitched_dice)
        # Return 1 colored die (pops its commitment)
        e = self.make_engine(deck=noop_deck(CorruptionSpace(index=1, label="Return 1", return_colored_dice=1)))
        p0 = e.state.players[0]
        shield = self.die(DieColor.BLUE, Face(name="+$2 & Block", money=2, block_amount=1, shield_color=ShieldColor.BLUE))
        c = [self.deploy(e, p0, [shield], {0: ShieldColor.BLUE}), self.deploy(e, e.state.players[1], [])]
        self.force(e, c, {CubeColor.BLACK: 1})
        phase2_compiler.execute_compiler_drop(e, c)
        self.assertEqual(c[0][2], {})
        phase3_income.execute_income(e, c)
        self.assertEqual(p0.money, 0)

    def test_contractor_plus1_face_pays_in_phase3(self):  # S-05
        e = self.make_engine()
        p0 = e.state.players[0]
        white = self.die(DieColor.WHITE, INCOME_1)
        c = [self.deploy(e, p0, [white]), self.deploy(e, e.state.players[1], [])]
        self.run_phases_2_to_4(e, c, {CubeColor.RED: 0, CubeColor.BLUE: 1})
        self.assertEqual(p0.money, 1)

    def test_contractors_expire_end_of_phase4_supply_conserved(self):  # S-06
        total = GameConfig().contractor_supply_total
        for exits in ({CubeColor.BLUE: 1}, {}, {CubeColor.GREEN: 1}):  # normal, overflow, Contractor Sacrifice
            e = self.make_engine()
            p0, p1 = e.state.players
            w1, w2 = self.die(DieColor.WHITE, INCOME_1), self.die(DieColor.WHITE, INCOME_1)
            c = [self.deploy(e, p0, [w1, self.die(DieColor.GRAY, INCOME_1)]), self.deploy(e, p1, [w2])]
            self.force(e, c, exits)
            cr = phase2_compiler.execute_compiler_drop(e, c)
            phase2_compiler.check_end_triggers_after_compiler(e, cr)
            phase3_income.execute_income(e, c)
            self.assertIn(w1, p0.contractor_dice)  # present during Phase 3
            phase4_attack_resolution.execute_attack_resolution(e, c, cr)
            for p in (p0, p1):
                self.assertEqual(p.contractor_dice, [])
                self.assertFalse(self.white_anywhere(p))
            self.assertEqual(e.state.contractor_supply, total, exits)


class TestSixPhaseEndTriggers(SixPhaseHarness):
    def _breach_setup(self, p1_secrets: int = 5, exits=None):
        e = self.make_engine(deck=noop_deck(CorruptionSpace(index=1, label="All lose 1 Secret", lose_secrets=1)))
        p0, p1 = e.state.players
        p0.secrets, p1.secrets = 1, p1_secrets
        d0 = self.die(DieColor.RED, INCOME_2)
        d1 = self.die(DieColor.RED, INCOME_2)
        c = [self.deploy(e, p0, [d0]), self.deploy(e, p1, [d1])]
        self.force(e, c, exits or {CubeColor.BLACK: 1, CubeColor.BLUE: 1})
        return e, p0, p1

    def test_phase2_patient_zero_skips_phases_3_to_6(self):  # S-07
        e, p0, p1 = self._breach_setup()
        captured = {}
        orig = phase2_compiler.check_end_triggers_after_compiler

        def spy(engine, cr):
            orig(engine, cr)
            captured.update(money=p0.money, research=p0.research_tokens, secrets=p0.secrets,
                            depth=p0.breach_depth, zones=self.zone_ids(p0))

        with mock.patch.object(phase2_compiler, "check_end_triggers_after_compiler", spy):
            e.run_round()
        self.assertTrue(p0.is_patient_zero)
        self.assertEqual((p0.money, p0.research_tokens, p0.secrets, p0.breach_depth, self.zone_ids(p0)),
                         (captured["money"], captured["research"], captured["secrets"], captured["depth"], captured["zones"]))
        self.assertEqual(p0.bot.ops_calls, 0)

    def test_phase2_breach_survivors_run_3_to_6(self):  # S-08
        e, p0, p1 = self._breach_setup()
        tel = e.run_round()
        self.assertEqual(p1.money, 2)                 # Phase 3 income
        self.assertEqual(p1.secrets, 3)               # 5 - 1 (corruption) - 1 (Phase 4 Blue)
        self.assertEqual(p1.in_production_dice, [])   # Phase 5 ran
        self.assertEqual(p1.bot.ops_calls, 1)         # Phase 6 ran
        self.assertTrue(e.state.game_over)
        self.assertEqual(e.state.end_reason, EndGameReason.PATIENT_ZERO)
        self.assertEqual(tel.final_round_trigger_phase, 2)
        self.assertEqual(tel.phases_executed, [1, 2, 3, 4, 5, 6])

    def test_phase4_wipeout_after_phase2_breach(self):  # S-09 (+ §12.1 tiebreaker-only ranking)
        e, p0, p1 = self._breach_setup(p1_secrets=3, exits={CubeColor.BLACK: 1, CubeColor.BLUE: 3})
        p1.money = 5
        tel = e.run_round()
        self.assertTrue(p1.is_patient_zero)
        self.assertEqual(e.state.end_reason, EndGameReason.TOTAL_WIPEOUT)
        self.assertEqual(tel.phases_executed, [1, 2, 3, 4])
        self.assertEqual(tel.end_phase, 4)
        res = e.evaluate_end_game()
        self.assertTrue(res.is_total_wipeout)
        # p0 breached shallower (depth 0) in Phase 2, p1 deeper (depth 1) in Phase 4 but has more Money:
        # breach depth is ignored on the six-phase path (OQ-4), so p1 ranks first.
        self.assertLess(p0.breach_depth, p1.breach_depth)
        self.assertEqual(res.rankings[0]["player_id"], 1)
        self.assertEqual(res.winner_id, 1)

    def test_legacy_wipeout_keeps_net_wipeout_score(self):  # OQ-4 legacy branch
        from sim.engine.end_game import evaluate_end_game

        e = self.make_engine()
        e.config = e.state.config = GameConfig.legacy_v033(num_players=2)
        p0, p1 = e.state.players
        p0.is_patient_zero = p1.is_patient_zero = True
        p0.breach_depth, p0.secrets, p0.money = 0, 0, 0
        p1.breach_depth, p1.secrets, p1.money = 2, -2, 9
        res = evaluate_end_game(e)
        self.assertEqual(res.rankings[0]["player_id"], 0)

    def test_singularity_skips_phases_3_to_6(self):  # S-10
        deck = [v3_card(CorruptionSpace(index=1, label="Lose 1 Secret", lose_secrets=1))]
        e = self.make_engine(deck=deck)
        p0, p1 = e.state.players
        inc, white = self.die(DieColor.RED, INCOME_2), self.die(DieColor.WHITE, INCOME_1)
        c = [self.deploy(e, p0, [inc, white]), self.deploy(e, p1, [])]
        self.force(e, c, {CubeColor.BLACK: 1, CubeColor.RED: 2})
        tel = e.run_round()
        self.assertTrue(e.state.singularity_triggered)
        self.assertEqual(e.state.end_reason, EndGameReason.SINGULARITY)
        self.assertEqual(tel.phases_executed, [1, 2])
        self.assertEqual(p0.money, 0)                 # no income
        self.assertEqual(p0.secrets, 7)               # Space 6 effect applied
        self.assertIn(inc, p0.ready_for_release_dice)
        self.assertFalse(self.white_anywhere(p0))
        self.assertEqual(e.state.contractor_supply, e.config.contractor_supply_total)

    def test_buffer_overflow_still_pays_income(self):  # S-11
        e = self.make_engine()
        p0, p1 = e.state.players
        white = self.die(DieColor.WHITE, INCOME_1)
        c = [self.deploy(e, p0, [self.die(DieColor.RED, INCOME_2), white]), self.deploy(e, p1, [])]
        self.force(e, c, {})
        tel = e.run_round()
        self.assertTrue(tel.buffer_overflow)
        self.assertEqual(p0.money, 3)
        self.assertEqual(tel.attack_strengths, {CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0})
        self.assertEqual(e.state.staging_cup[CubeColor.RED], 1)
        self.assertEqual(e.state.staging_cup[CubeColor.BLUE], 1)
        self.assertEqual(e.state.staging_cup[CubeColor.GREEN], 1)
        self.assertFalse(self.white_anywhere(p0))
        self.assertEqual(e.state.contractor_supply, e.config.contractor_supply_total)

    def test_phase2_all_breach_is_total_wipeout(self):  # S-19
        e = self.make_engine(deck=noop_deck(CorruptionSpace(index=1, label="All lose 1 Secret", lose_secrets=1)))
        p0, p1 = e.state.players
        p0.secrets = p1.secrets = 1
        c = [self.deploy(e, p0, [self.die(DieColor.WHITE, INCOME_1)]), self.deploy(e, p1, [])]
        self.force(e, c, {CubeColor.BLACK: 1})
        tel = e.run_round()
        self.assertEqual(e.state.end_reason, EndGameReason.TOTAL_WIPEOUT)
        self.assertEqual(tel.phases_executed, [1, 2])
        self.assertEqual(e.state.contractor_supply, e.config.contractor_supply_total)
        self.assertFalse(self.white_anywhere(p0))


class TestSixPhasePipeline(SixPhaseHarness):
    def test_phase5_order_and_production_routes_through_scanned(self):  # S-12
        e = self.make_engine(research_track_model=ResearchTrackModel.V034_THREE_LEVEL)
        p0 = e.state.players[0]
        p0.has_emergency_hotfix = True
        g_col = self.die(DieColor.RED, Face(name="x"), cost=5)
        g_gray1, g_gray2, g_gray3 = (self.die(DieColor.GRAY, Face(name="x")) for _ in range(3))
        p0.glitched_dice.extend([g_gray1, g_col, g_gray2, g_gray3])
        prod = [self.die(DieColor.GRAY, INCOME_1), self.die(DieColor.BLUE, INCOME_1)]
        self.deploy(e, p0, prod)
        moved = phase5_pipeline_shift.apply_hotfix_bypass(e, p0)
        self.assertEqual(moved, [g_col])
        self.assertIn(g_col, p0.ready_for_release_dice)
        phase5_pipeline_shift.production_return_to_scanned(e, p0)
        self.assertEqual(p0.in_production_dice, [])
        self.assertTrue(all(d in p0.scanned_dice for d in prod))
        self.assertTrue(all(d not in p0.ready_for_release_dice for d in prod))
        grads = phase5_pipeline_shift.graduate_scanned(e, p0)
        self.assertLessEqual(len(grads), p0.release_bandwidth)
        triaged = phase5_pipeline_shift.conveyor_triage(p0)
        self.assertEqual(len(triaged), p0.triage_bandwidth)
        self.assertTrue(all(d not in p0.ready_for_release_dice for d in triaged))  # not graduated same round
        self.assertIn(g_gray3, p0.glitched_dice)

    def test_release_bandwidth_caps_scanned_to_ready(self):  # S-13
        e = self.make_engine()
        p0, p1 = e.state.players
        dice = [self.die(DieColor.GRAY, INCOME_1) for _ in range(6)]
        c = [self.deploy(e, p0, dice), self.deploy(e, p1, [])]
        self.force(e, c, {CubeColor.RED: 1})
        tel = e.run_round()
        self.assertEqual(len(p0.ready_for_release_dice), 4)
        self.assertEqual(len(p0.scanned_dice), 2)
        self.assertEqual(tel.scanned_held_by_player[0], 2)
        self.assertEqual(tel.graduated_by_player[0], 4)

    def test_choose_scanned_graduates_priority_and_validation(self):  # S-14 (+ OQ-1)
        e = self.make_engine()
        p0 = e.state.players[0]
        gray = self.die(DieColor.GRAY, Face(name="x"))
        cheap = self.die(DieColor.RED, Face(name="x"), cost=4)
        dear = self.die(DieColor.YELLOW, Face(name="x"), cost=6)
        purple = self.die(DieColor.PURPLE, Face(name="x"), cost=0)
        p0.scanned_dice.extend([gray, cheap, dear, purple])
        p0.release_bandwidth = 3
        self.assertEqual(BaseBot(0).choose_scanned_graduates(p0, 3), [purple, dear, cheap])
        # invalid + duplicate ids replaced by default priority up to the requested count
        got = phase5_pipeline_shift.validate_graduate_ids(p0, [gray.die_id, gray.die_id, 99999], 3)
        self.assertEqual(got, [gray, purple, dear])
        # shorter list honoured (not back-filled), including 0
        self.assertEqual(phase5_pipeline_shift.validate_graduate_ids(p0, [gray.die_id], 3), [gray])
        self.assertEqual(phase5_pipeline_shift.graduate_scanned(e, p0, []), [])
        self.assertEqual(len(p0.scanned_dice), 4)
        p0.bot.graduate_override = [cheap.die_id]
        self.assertEqual(phase5_pipeline_shift.graduate_scanned(e, p0), [cheap])
        self.assertIn(cheap, p0.ready_for_release_dice)
        p0.bot.graduate_override = []
        self.assertEqual(phase5_pipeline_shift.graduate_scanned(e, p0), [])
        # over-long list truncated to n
        p0.bot.graduate_override = [d.die_id for d in p0.scanned_dice]
        self.assertEqual(len(phase5_pipeline_shift.graduate_scanned(e, p0)), 3)

    def test_purchases_go_to_ready_bypass_cap_and_marker_passes_once(self):  # S-15
        plan = Phase3ActionPlan(market_purchases=[DieColor.RED, DieColor.BLUE])
        e = self.make_engine(bots=[StubBot(0, plan), StubBot(1)])
        p0, p1 = e.state.players
        p0.money = 30
        dice = [self.die(DieColor.GRAY, Face(name="Block", block_amount=1, shield_color=ShieldColor.ANY)) for _ in range(4)]
        c = [self.deploy(e, p0, dice), self.deploy(e, p1, [])]
        self.force(e, c, {CubeColor.RED: 1})
        fp = e.state.first_player_index
        e.run_round()
        self.assertEqual(e.state.first_player_index, (fp + 1) % 2)
        self.assertEqual(len(p0.ready_for_release_dice), 6)
        bought = [d for d in p0.ready_for_release_dice if d.color in (DieColor.RED, DieColor.BLUE)]
        self.assertEqual(len(bought), 2)
        del e._execute_phase_1  # real Phase 1 next round: all 6 Ready dice roll
        e.state.tower.drop = lambda cup, rng: dict(ZERO, **{CubeColor.RED: 1})
        commitments = e._execute_phase_1()
        self.assertEqual(len(commitments[0][1]), 6)

    def test_y3_moves_to_glitched_in_phase3_not_green_target(self):  # S-24
        e = self.make_engine()
        p0 = e.state.players[0]
        y3 = self.die(DieColor.YELLOW, Y3_FACE)
        gray = self.die(DieColor.GRAY, INCOME_1)
        c = [self.deploy(e, p0, [y3, gray]), self.deploy(e, e.state.players[1], [])]
        self.force(e, c, {CubeColor.GREEN: 1})
        cr = phase2_compiler.execute_compiler_drop(e, c)
        phase3_income.execute_income(e, c)
        self.assertEqual(p0.secrets, 9)
        self.assertIn(y3, p0.glitched_dice)
        self.assertNotIn(y3, p0.in_production_dice)
        phase4_attack_resolution.execute_attack_resolution(e, c, cr)
        self.assertIn(gray, p0.glitched_dice)
        self.assertEqual(sum(1 for d in p0.glitched_dice if d is y3), 1)

    def test_b3_rescued_die_competes_for_release_bandwidth(self):  # S-25
        e = self.make_engine()
        p0, p1 = e.state.players
        rescued = self.die(DieColor.RED, Face(name="x"), cost=5)
        p0.glitched_dice.append(rescued)
        b3 = self.die(DieColor.BLUE, B3_FACE)
        grays = [self.die(DieColor.GRAY, INCOME_1) for _ in range(4)]
        c = [self.deploy(e, p0, [b3] + grays), self.deploy(e, p1, [])]
        self.force(e, c, {CubeColor.RED: 0, CubeColor.BLUE: 1})
        tel = e.run_round()
        self.assertIn(rescued, p0.ready_for_release_dice)
        self.assertIn(b3, p0.ready_for_release_dice)
        self.assertEqual(tel.scanned_held_by_player[0], 2)
        self.assertTrue(all(d.color == DieColor.GRAY for d in p0.scanned_dice))


class TestSixPhaseProtocols(SixPhaseHarness):
    def _operative(self, p, code: WhiteHatCode):
        p.white_hat = WHITE_HATS[code]
        # The legacy archetype bridge maps Spook -> DTO / Phreaker -> Omnidyne overrides; disable them.
        p.ability_v1_status = AbilityStatus.USED

    def test_burn_notice_before_blue_and_commit_sync(self):  # S-16
        e = self.make_engine()
        p0, p1 = e.state.players
        self._operative(p0, WhiteHatCode.SPOOK)
        p0.secrets = 1
        purple = self.die(DieColor.PURPLE, PURPLE_STAR)
        blue = self.die(DieColor.BLUE, BLOCK_BLUE)
        c = [self.deploy(e, p0, [purple, blue], {1: ShieldColor.BLUE}), self.deploy(e, p1, [])]
        p0.bot.burn_ids = [blue.die_id]
        cr, incomes = self.run_phases_2_to_4(e, c, {CubeColor.BLUE: 1})
        self.assertEqual(incomes[0].money, 2)
        self.assertEqual(incomes[0].secrets, 1)
        self.assertEqual(incomes[0].burned_die_ids, [blue.die_id])
        self.assertEqual(p0.last_defense_breakdown["blocked"]["blue"], 0)  # burned shield no longer blocks
        self.assertEqual(p0.secrets, 1)
        self.assertFalse(p0.is_patient_zero)

    def test_two_purple_stars_trigger_protocol_twice(self):  # §12.1 OQ-17
        e = self.make_engine()
        p0, p1 = e.state.players
        self._operative(p0, WhiteHatCode.PHREAKER)
        c = [self.deploy(e, p0, [self.die(DieColor.PURPLE, PURPLE_STAR), self.die(DieColor.PURPLE, PURPLE_STAR)]),
             self.deploy(e, p1, [])]
        cr, incomes = self.run_phases_2_to_4(e, c, {CubeColor.BLUE: 1})
        self.assertEqual(incomes[0].purple_star_triggers, 2)
        self.assertEqual(incomes[0].money, 2)  # two Jumper Diagnostics fallbacks (+$1 each)
        # Spook: two Burn Notices, never the same die twice
        e = self.make_engine()
        p0, p1 = e.state.players
        self._operative(p0, WhiteHatCode.SPOOK)
        g1, g2 = self.die(DieColor.RED, Face(name="x")), self.die(DieColor.BLUE, Face(name="x"))
        p0.glitched_dice.extend([g1, g2])
        c = [self.deploy(e, p0, [self.die(DieColor.PURPLE, PURPLE_STAR), self.die(DieColor.PURPLE, PURPLE_STAR)]),
             self.deploy(e, p1, [])]
        p0.bot.burn_ids = [g1.die_id, g1.die_id]
        cr, incomes = self.run_phases_2_to_4(e, c, {CubeColor.RED: 1})
        self.assertEqual(incomes[0].burned_die_ids, [g1.die_id])

    def test_glitched_purple_fires_nothing(self):  # §12.1 OQ-2
        e = self.make_engine(deck=noop_deck(CorruptionSpace(index=1, label="Glitch 1", demote_dice=1)))
        p0, p1 = e.state.players
        self._operative(p0, WhiteHatCode.PHREAKER)
        purple = self.die(DieColor.PURPLE, PURPLE_STAR)
        c = [self.deploy(e, p0, [purple]), self.deploy(e, p1, [])]
        cr, incomes = self.run_phases_2_to_4(e, c, {CubeColor.BLACK: 1})
        self.assertIn(purple, p0.glitched_dice)
        self.assertEqual(incomes[0].purple_star_triggers, 0)
        self.assertEqual(p0.money, 0)  # no fallback, no diagnostics

    def test_phreaker_diagnostics_phase3_excludes_phase4_victims_and_fallback(self):  # S-26
        e = self.make_engine()
        p0, p1 = e.state.players
        self._operative(p0, WhiteHatCode.PHREAKER)
        victim = self.die(DieColor.GRAY, INCOME_1)
        c = [self.deploy(e, p0, [self.die(DieColor.PURPLE, PURPLE_STAR), victim]), self.deploy(e, p1, [])]
        self.force(e, c, {CubeColor.GREEN: 1})
        cr = phase2_compiler.execute_compiler_drop(e, c)
        rec = phase3_income.execute_income(e, c)[0]
        self.assertEqual(rec.money, 1 + 1)       # gray +$1 and the empty-pipeline +$1 fallback
        self.assertEqual(p0.bot.diag_calls, [])  # Under Development empty -> fallback, no roll
        phase4_attack_resolution.execute_attack_resolution(e, c, cr)
        self.assertIn(victim, p0.glitched_dice)  # Phase 4 victim arrives after diagnostics
        # With a die already Under Development, the hook sees only pre-Phase-3 dice
        e = self.make_engine()
        p0, p1 = e.state.players
        self._operative(p0, WhiteHatCode.PHREAKER)
        old = self.die(DieColor.GREEN, Face(name="x"))
        p0.glitched_dice.append(old)
        c = [self.deploy(e, p0, [self.die(DieColor.PURPLE, PURPLE_STAR), self.die(DieColor.GRAY, INCOME_1)]),
             self.deploy(e, p1, [])]
        self.run_phases_2_to_4(e, c, {CubeColor.GREEN: 1})
        self.assertEqual(p0.bot.diag_calls, [[old.die_id]])

    def test_malware_targets_six_phase_default_key(self):  # S-27
        e = self.make_engine()
        p0 = e.state.players[0]
        purple = self.die(DieColor.PURPLE, INCOME_1, cost=0)
        dear = self.die(DieColor.RED, INCOME_1, cost=5)
        cheap = self.die(DieColor.GREEN, INCOME_1, cost=4)
        gray = self.die(DieColor.GRAY, INCOME_1)
        white = self.die(DieColor.WHITE, INCOME_1)
        order = BaseBot(0).choose_malware_glitch_targets(p0, [purple, dear, cheap, gray, white], 5)
        self.assertEqual(order, [white, gray, cheap, dear, purple])
        # Fizzle when In Production is empty
        c = [self.deploy(e, p0, []), self.deploy(e, e.state.players[1], [])]
        self.run_phases_2_to_4(e, c, {CubeColor.GREEN: 2})
        self.assertEqual(p0.glitched_dice, [])


class TestSixPhaseBotsAndSetup(SixPhaseHarness):
    def test_flat_8_starting_secrets_all_counts_dto_9(self):  # S-17
        for n in (2, 3, 4):
            cfg = GameConfig.legacy_v034(num_players=n)
            self.assertEqual(cfg.round_sequence, RoundSequence.SIX_PHASE)
            self.assertEqual(cfg.get_starting_secrets(n), 8)
            e = GameEngine(cfg, [BaseBot(i) for i in range(n)], seed=1)
            self.assertTrue(all(p.secrets == 8 for p in e.state.players))
        comps = [COMPANIES[CompanyCode.DTO], COMPANIES[CompanyCode.AEGIS], COMPANIES[CompanyCode.HELIX], COMPANIES[CompanyCode.MERIDIAN]]
        e = GameEngine(GameConfig.legacy_v034(num_players=4, enable_corporate_asymmetry=True), [BaseBot(i) for i in range(4)],
                       seed=1, companies=comps)
        self.assertEqual(e.state.players[0].secrets, 9)

    def test_legacy_flag_pins_4p_to_12(self):  # S-18
        cfg = GameConfig.legacy_v033(num_players=4)
        self.assertFalse(cfg.is_six_phase)
        self.assertEqual(cfg.get_starting_secrets(4), 12)
        comps = [COMPANIES[CompanyCode.DTO], COMPANIES[CompanyCode.AEGIS], COMPANIES[CompanyCode.HELIX], COMPANIES[CompanyCode.MERIDIAN]]
        e = GameEngine(GameConfig.legacy_v033(num_players=4, enable_corporate_asymmetry=True),
                       [BaseBot(i) for i in range(4)], seed=1, companies=comps)
        self.assertEqual(e.state.players[0].secrets, 13)
        self.assertEqual(GameConfig(num_players=4, starting_secrets_by_player_count={4: 10}).get_starting_secrets(4), 10)
        self.assertEqual(GameConfig(round_sequence="V033_THREE_PHASE").round_sequence, RoundSequence.V033_THREE_PHASE)
        self.assertTrue(GameConfig().round_sequence == "SIX_PHASE")

    def test_round_telemetry_six_phase_fields(self):  # S-20
        for seed in range(6):
            e = GameEngine(GameConfig(num_players=3), seed=seed)
            rounds = 0
            while not e.state.game_over:
                survivors = {p.player_id for p in e.state.players if not p.is_patient_zero}
                tel = e.run_round()
                rounds += 1
                self.assertEqual(len(e.telemetry_history), rounds)
                self.assertIn(tel.phases_executed, ([1, 2], [1, 2, 3, 4], [1, 2, 3, 4, 5, 6]))
                self.assertEqual(set(tel.phase_snapshots), set(tel.phases_executed))
                self.assertEqual(tel.round_sequence, "SIX_PHASE")
                if 3 in tel.phases_executed:
                    entering_p3 = {s["player_id"] for s in tel.phase_snapshots[2] if not s["is_patient_zero"]}
                    self.assertEqual(set(tel.income_by_player), entering_p3)
                    self.assertTrue(entering_p3 <= survivors)
                if 5 in tel.phases_executed:
                    self.assertTrue(all(isinstance(v, int) for v in tel.scanned_held_by_player.values()))

    def test_override_timings_six_phase(self):  # S-21
        e = self.make_engine()
        p0, p1 = e.state.players
        p0.company = COMPANIES[CompanyCode.AEGIS]
        p1.company = COMPANIES[CompanyCode.DTO]
        p1.secrets = 3
        c = [self.deploy(e, p0, []), self.deploy(e, p1, [])]
        self.force(e, c, {CubeColor.RED: 1, CubeColor.BLUE: 1})
        cr = phase2_compiler.execute_compiler_drop(e, c)
        e.state.pending_version_advance = True
        v_before = e.state.active_version
        phase3_income.execute_income(e, c)
        self.assertTrue(p0.is_ability_available("v1.0"))
        self.assertTrue(p1.is_ability_available("v1.0"))
        phase4_attack_resolution.execute_attack_resolution(e, c, cr)
        self.assertFalse(p0.is_ability_available("v1.0"))  # Aegis Baffle Echo in Phase 4
        self.assertFalse(p1.is_ability_available("v1.0"))  # DTO Slush Fund in Phase 4
        self.assertEqual(p1.secrets, 3)
        # Omnidyne Magnetic Splice: Phase 5 step 1
        p0.company = COMPANIES[CompanyCode.OMNIDYNE]
        p0.ability_v1_status = AbilityStatus.AVAILABLE
        g = self.die(DieColor.RED, Face(name="x"), cost=5)
        p0.glitched_dice.append(g)
        phase5_pipeline_shift.execute_pipeline_shift(e)
        self.assertIn(g, p0.ready_for_release_dice)
        self.assertFalse(p0.is_ability_available("v1.0"))
        # Prometheus Algorithmic Arbitrage: Phase 6
        p1.company = COMPANIES[CompanyCode.PROMETHEUS]
        p1.ability_v1_status = AbilityStatus.AVAILABLE
        p1.bot.plan = Phase3ActionPlan(use_prometheus_override=True, prometheus_mode="CASH")
        m = p1.money
        phase6_operations.execute_operations(e)
        self.assertEqual(p1.money, m + e.config.cipher_arbitrage_cash)
        self.assertIs(e.state.active_version, v_before)  # INV-SEQ-OVERRIDE-WINDOW-01

    def test_six_phase_never_sets_pre_step2b_snapshot(self):  # S-22
        for seed in range(8):
            e = GameEngine(GameConfig(num_players=4, enable_corporate_asymmetry=True), seed=seed)
            while not e.state.game_over:
                e.run_round()
                for p in e.state.players:
                    self.assertIsNone(getattr(p, "_pre_step2b_snapshot", None))
                    self.assertEqual(getattr(p, "pending_unblocked_green", 0), 0)

    def test_take_operations_actions_alias_resolution(self):  # S-28
        marker = Phase3ActionPlan(patent_filings=7)

        class OldName(BaseBot):
            def take_phase3_actions(self, ps, gs, rng):
                return marker

        class NewName(BaseBot):
            def take_operations_actions(self, ps, gs, rng):
                return marker

        class OldOnAdaptive(AdaptiveBalancedBot):
            def take_phase3_actions(self, ps, gs, rng):
                return marker

        e = self.make_engine()
        ps, gs = e.state.players[0], e.state
        for bot in (OldName(0), NewName(0), OldOnAdaptive(0)):
            self.assertIs(phase6_operations.resolve_operations_plan(bot, ps, gs, e.rng), marker, type(bot).__name__)
            self.assertIs(bot.take_phase3_actions(ps, gs, e.rng), marker)  # legacy shim call path
        for name in ("take_operations_actions", "take_phase3_actions"):
            bot = AdaptiveBalancedBot(0)
            setattr(bot, name, lambda ps_, gs_, rng_: marker)
            self.assertIs(phase6_operations.resolve_operations_plan(bot, ps, gs, e.rng), marker, name)
        self.assertIsInstance(phase6_operations.resolve_operations_plan(BaseBot(0), ps, gs, e.rng), Phase3ActionPlan)

    def test_release_track_valued_when_dice_exceed_bandwidth(self):  # S-29
        def plan_for(cfg):
            e = GameEngine(cfg, [AdaptiveBalancedBot(0), AdaptiveBalancedBot(1)], seed=3)
            p = e.state.players[0]
            p.company, p.white_hat = None, None
            p.ready_for_release_dice[:] = [create_gray_die(900 + i) for i in range(3)]
            p.glitched_dice[:] = [create_gray_die(910), create_gray_die(911)]
            p.release_bandwidth, p.release_level, p.triage_level = 4, 0, 0
            p.research_tokens, p.money, p.defense_level = 10, 0, 1
            return AdaptiveBalancedBot(0).take_operations_actions(p, e.state, e.rng).track_upgrades

        six = plan_for(GameConfig.legacy_v034(num_players=2))
        self.assertIn("RELEASE", six)
        self.assertLess(six.index("RELEASE"), six.index("TRIAGE"))
        legacy = plan_for(GameConfig.legacy_v033(num_players=2))
        self.assertNotIn("RELEASE", legacy)
        self.assertIn("TRIAGE", legacy)
        # Level 2 is also valued
        bot = BaseBot(0)
        e = self.make_engine(research_track_model=ResearchTrackModel.V034_THREE_LEVEL)
        p = e.state.players[0]
        p.ready_for_release_dice[:] = [create_gray_die(920 + i) for i in range(6)]
        p.release_level, p.release_bandwidth = 1, 5
        plan = Phase3ActionPlan()
        self.assertEqual(bot.plan_release_upgrade(p, plan, 3), 0)
        self.assertEqual(plan.track_upgrades, ["RELEASE"])


class TestLegacyParityGolden(unittest.TestCase):
    def test_legacy_sequence_parity_golden(self):  # S-23 (INV-SEQ-LEGACY-PARITY-01)
        from tests.fixtures.v033_parity import capture

        for scenario in capture.SCENARIOS:
            for n in capture.PLAYER_COUNTS:
                with open(capture.fixture_path(scenario, n), encoding="utf-8") as fh:
                    golden = json.load(fh)
                for seed in capture.SEEDS:
                    got = json.loads(json.dumps(capture.run_scenario(GameConfig.legacy_v033, scenario, n, seed), sort_keys=True))
                    self.assertEqual(got, golden[str(seed)], f"{scenario} {n}P seed {seed}")

    def test_round_phase_names(self):
        self.assertEqual(ROUND_PHASE_NAMES[RoundPhase.INCOME], "Income")
        self.assertEqual([ROUND_PHASE_NAMES[i] for i in range(1, 8)], [
            "Roll & Deploy", "Compiler Drop & Corruption", "Income", "Attack Resolution",
            "CI/CD Pipeline Shift", "Operations", "Game Over"])


class TestWebSixPhaseStateMachine(unittest.TestCase):
    def _drive(self, ctrl, pid=0, record=None):
        """Advance one step with default human choices; returns the phase visited."""
        st = ctrl.get_full_state()
        ph = st["phase"]
        if record is not None:
            record.append((ph, st["phase_name"], st["subphase"]))
        if ph == 1:
            meta = ctrl.player_meta[pid]
            if ctrl.state.players[pid].is_patient_zero:
                raise AssertionError("human eliminated in Phase 1")
            if not meta["has_rolled"]:
                ctrl.roll_pool(pid)
            ctrl.commit_defenses(pid, {})
        elif ph == 2:
            ctrl.compile_drop()
        elif ph == 3:
            ctrl.confirm_income(pid)
        elif ph == 4:
            ctrl.confirm_attacks(pid)
        elif ph == 5:
            ctrl.choose_graduates(pid, ctrl.pending_graduation[pid]["default_graduate_ids"])
        elif ph == 6:
            ctrl.end_turn(pid)
        return ph

    def test_web_six_phase_state_machine(self):  # S-30
        from web.game_controller import GameController

        for seed in (1, 2, 3, 4, 5):
            ctrl = GameController()
            ctrl.new_game(num_players=3, seed=seed)
            self.assertEqual(ctrl.state.config.round_sequence, RoundSequence.SIX_PHASE)
            visited = []
            for _ in range(400):
                if ctrl.phase == 7:
                    break
                self._drive(ctrl, record=visited)
            self.assertEqual(ctrl.phase, 7)
            self.assertEqual(ctrl.phase_name, "Game Over")
            for ph, name, sub in visited:
                self.assertEqual(name, ROUND_PHASE_NAMES[ph])
            phases = [v[0] for v in visited]
            self.assertIn(1, phases)
            self.assertIn(2, phases)
            # Phase order inside a round never goes backwards except 6 -> 1 (next round)
            for a, b in zip(phases, phases[1:]):
                self.assertTrue(b >= a or (b == 1 and a in (5, 6, 4, 3)), (a, b))
            self.assertEqual(ctrl.state.contractor_supply, ctrl.state.config.contractor_supply_total)

    def test_web_choose_graduates_validation_and_fewer(self):  # S-30 / OQ-1
        from web.game_controller import GameController
        from sim.entities import Die

        ctrl = GameController()
        ctrl.new_game(num_players=2, seed=11)
        p0 = ctrl.state.players[0]
        for i in range(3):
            p0.scanned_dice.append(Die(die_id=8000 + i, color=DieColor.GRAY, cost=0, faces=[INCOME_1]))
        ctrl.state.tower.drop = lambda cup, rng: dict(ZERO, **{CubeColor.RED: 1})
        for _ in range(10):
            if ctrl.phase == 5:
                break
            self._drive(ctrl)
        self.assertEqual(ctrl.phase, 5)
        self.assertEqual(ctrl.subphase, "choose_graduates")
        pend = ctrl.pending_graduation[0]
        self.assertGreater(len(pend["candidates"]), pend["n"])
        with self.assertRaises(ValueError):
            ctrl.choose_graduates(0, [424242])
        with self.assertRaises(ValueError):
            ctrl.choose_graduates(0, [c["die_id"] for c in pend["candidates"]])
        ctrl.choose_graduates(0, [])  # graduate none (OQ-1)
        self.assertEqual(ctrl.phase, 6)
        self.assertEqual(ctrl.last_pipeline_result[0]["graduated_ids"], [])
        self.assertTrue(all(d.die_id not in [c["die_id"] for c in pend["candidates"]] for d in p0.ready_for_release_dice))


class TestStaffReviewFollowUps(SixPhaseHarness):
    def _spook(self, p):
        p.white_hat = WHITE_HATS[WhiteHatCode.SPOOK]
        p.ability_v1_status = AbilityStatus.USED  # disable the legacy Spook->DTO Slush Fund bridge

    def test_second_burn_notice_burns_a_different_die(self):  # OQ-17
        for burn_ids in (["g1", "g2"], ["g1", "g1", "g2"]):  # second case: bot repeats a burned id, re-asked
            e = self.make_engine()
            p0, p1 = e.state.players
            self._spook(p0)
            g1, g2 = self.die(DieColor.RED, Face(name="x")), self.die(DieColor.BLUE, Face(name="x"))
            p0.glitched_dice.extend([g1, g2])
            ids = {"g1": g1.die_id, "g2": g2.die_id}
            c = [self.deploy(e, p0, [self.die(DieColor.PURPLE, PURPLE_STAR), self.die(DieColor.PURPLE, PURPLE_STAR)]),
                 self.deploy(e, p1, [])]
            p0.bot.burn_ids = [ids[k] for k in burn_ids]
            red_before, blue_before = e.state.market[DieColor.RED], e.state.market[DieColor.BLUE]
            cr, incomes = self.run_phases_2_to_4(e, c, {CubeColor.RED: 1})
            self.assertEqual(incomes[0].burned_die_ids, [g1.die_id, g2.die_id], burn_ids)
            self.assertEqual(incomes[0].secrets, 2)
            self.assertEqual(e.state.market[DieColor.RED], red_before + 1)
            self.assertEqual(e.state.market[DieColor.BLUE], blue_before + 1)

    def test_burn_notice_on_the_purple_star_die_itself(self):
        e = self.make_engine()
        p0, p1 = e.state.players
        self._spook(p0)
        purple = self.die(DieColor.PURPLE, PURPLE_STAR)
        c = [self.deploy(e, p0, [purple]), self.deploy(e, p1, [])]
        p0.bot.burn_ids = [purple.die_id]
        cr, incomes = self.run_phases_2_to_4(e, c, {CubeColor.RED: 1})
        self.assertEqual(incomes[0].money, 2)        # Spook +$2 collected before the burn
        self.assertEqual(incomes[0].secrets, 1)      # Burn Notice +1 Secret
        self.assertEqual(incomes[0].burned_die_ids, [purple.die_id])
        self.assertNotIn(purple, p0.total_dice)       # Purple is scrapped (not returned to market)
        self.assertEqual(incomes[0].purple_star_triggers, 1)

    def test_release_level_2_gives_bandwidth_6_next_phase5(self):
        plan = Phase3ActionPlan(track_upgrades=["RELEASE"])
        e = self.make_engine(bots=[StubBot(0, plan), StubBot(1)], research_track_model=ResearchTrackModel.V034_THREE_LEVEL)
        p0, p1 = e.state.players
        p0.release_level, p0.release_bandwidth, p0.research_tokens = 1, 5, 3
        dice = [self.die(DieColor.GRAY, INCOME_1) for _ in range(7)]
        c = [self.deploy(e, p0, dice), self.deploy(e, p1, [])]
        self.force(e, c, {CubeColor.RED: 1})
        tel1 = e.run_round()
        self.assertEqual(tel1.graduated_by_player[0], 5)   # upgrade bought in Phase 6 applies next round
        self.assertEqual((p0.release_level, p0.release_bandwidth), (2, 6))
        # Round 2: everything Ready rolls; the 2 held dice are still Scanned
        p0.bot.plan = Phase3ActionPlan()
        ready = list(p0.ready_for_release_dice)
        p0.ready_for_release_dice.clear()
        for d in ready:
            d.current_face = INCOME_1
        c2 = [self.deploy(e, p0, ready), self.deploy(e, p1, [])]
        self.force(e, c2, {CubeColor.RED: 1})
        tel2 = e.run_round()
        self.assertEqual(tel2.graduated_by_player[0], 6)
        self.assertEqual(tel2.scanned_held_by_player[0], 1)

    def test_mode_b_corruption_cubes_on_six_phase_path(self):
        deck = noop_deck(CorruptionSpace(index=1, label="Add 1R", add_cubes={CubeColor.RED: 1}))
        e = self.make_engine(deck=deck, corruption_cubes_resolve_immediately=True)
        p0, p1 = e.state.players
        p0.money = 5
        c = [self.deploy(e, p0, [self.die(DieColor.GRAY, INCOME_1)]), self.deploy(e, p1, [])]
        self.force(e, c, {CubeColor.BLACK: 1})
        tel = e.run_round()
        self.assertEqual(tel.attack_strengths[CubeColor.RED], 1)        # Mode-B cube attacks in Phase 4
        self.assertEqual(e.state.last_exited_cubes.get(CubeColor.RED, 0), 0)  # Acoustic reads the pre-add tray
        self.assertEqual(p0.money, 5 + 1 - 1)                            # income, then $1 ransom
        self.assertEqual(e.state.staging_cup[CubeColor.RED], 1)          # recycled by Snowball Recycle


class TestWebFollowUps(unittest.TestCase):
    def test_web_phase2_patient_zero_final_round_two_humans(self):
        from web.game_controller import GameController

        ctrl = GameController()
        ctrl.new_game(num_players=3, seed=5, players_config=[
            {"is_human": True, "name": "A"}, {"is_human": True, "name": "B"}, {"is_human": False}])
        ctrl.state.version_deck[0] = noop_deck(CorruptionSpace(index=1, label="All lose 1 Secret", lose_secrets=1))[0]
        p0, p1, p2 = ctrl.state.players
        p0.secrets, p1.secrets, p2.secrets = 1, 6, 6
        ctrl.state.tower.drop = lambda cup, rng: dict(ZERO, **{CubeColor.BLACK: 1, CubeColor.RED: 1})
        for pid in (0, 1):
            ctrl.roll_pool(pid)
            ctrl.commit_defenses(pid, {})
        self.assertEqual(ctrl.phase, 2)
        ctrl.compile_drop()
        self.assertTrue(p0.is_patient_zero)
        self.assertTrue(ctrl.state.is_final_round)
        self.assertEqual(ctrl.phase, 3)
        with self.assertRaises(ValueError):
            ctrl.confirm_income(0)  # Phase-2 Patient Zero skips Phases 3-6
        self.assertFalse(ctrl.get_action_capabilities(0)["can_confirm_income"])
        ctrl.confirm_income(1)
        self.assertEqual(ctrl.phase, 4)
        with self.assertRaises(ValueError):
            ctrl.confirm_attacks(0)
        ctrl.confirm_attacks(1)
        if ctrl.phase == 5:
            ctrl.choose_graduates(1, ctrl.pending_graduation[1]["default_graduate_ids"])
        self.assertEqual(ctrl.phase, 6)
        self.assertNotIn(0, [ctrl.active_player_index])
        ctrl.end_turn(ctrl.active_player_index)
        if ctrl.phase == 6:
            ctrl.end_turn(ctrl.active_player_index)
        self.assertEqual(ctrl.phase, 7)
        self.assertEqual(ctrl.state.end_reason, EndGameReason.PATIENT_ZERO)
        self.assertNotIn(0, [r["player_id"] for r in ctrl.final_result["rankings"][:2]])

    def test_web_confirm_income_burn_notice_list(self):
        from web.game_controller import GameController

        ctrl = GameController()
        ctrl.new_game(num_players=2, seed=3)
        ctrl.state.tower.drop = lambda cup, rng: dict(ZERO, **{CubeColor.RED: 1})
        ctrl.roll_pool(0)
        ctrl.commit_defenses(0, {})
        ctrl.compile_drop()
        self.assertEqual(ctrl.phase, 3)
        p0 = ctrl.state.players[0]
        p0.white_hat = WHITE_HATS[WhiteHatCode.SPOOK]
        for i in range(2):
            d = create_colored_die(DieColor.PURPLE, 7700 + i, cost=0)
            d.current_face = PURPLE_STAR
            p0.in_production_dice.append(d)
        g1, g2 = create_colored_die(DieColor.RED, 7710), create_colored_die(DieColor.BLUE, 7711)
        p0.glitched_dice.extend([g1, g2])
        caps = ctrl.get_action_capabilities(0)
        self.assertTrue(caps["can_spook_burn"])
        secrets = p0.secrets
        ctrl.confirm_income(0, spook_burn_die_id=[7710, 7711])
        self.assertEqual(ctrl.last_income_result[0]["burned_die_ids"], [7710, 7711])
        self.assertEqual(p0.secrets, secrets + 2)


R2_FACE = Face(name="R2: Threat Bounty", block_amount=2, shield_color=ShieldColor.RED, is_star=True, star_code="R2")
R3_FACE = Face(name="R3: Short Squeeze", money=3, is_star=True, star_code="R3")
B1_FACE = Face(name="B1: Honeypot Telemetry", block_amount=2, shield_color=ShieldColor.BLUE, is_star=True, star_code="B1")


class TestDamageConditionalStarsInProduction(SixPhaseHarness):
    """User-approved (deviation 2): on the six-phase path R2/R3/B1 pay only if that die is still In Production
    at Phase 4. Legacy v0.33 code path is unchanged."""

    def test_r3_glitched_by_phase2_corruption_does_not_pay(self):
        e = self.make_engine(deck=noop_deck(CorruptionSpace(index=1, label="Glitch 1 die", demote_dice=1)))
        p0, p1 = e.state.players
        p0.money = 10
        r3 = self.die(DieColor.RED, R3_FACE)
        c = [self.deploy(e, p0, [r3]), self.deploy(e, p1, [])]
        self.run_phases_2_to_4(e, c, {CubeColor.BLACK: 1, CubeColor.RED: 3})
        self.assertIn(r3, p0.glitched_dice)
        self.assertEqual(p0.money, 10 - 3)  # no Phase 3 income, no Phase 4 +$1, $3 ransom

    def test_r3_surviving_pays_income_and_bonus(self):
        e = self.make_engine()
        p0, p1 = e.state.players
        p0.money = 10
        c = [self.deploy(e, p0, [self.die(DieColor.RED, R3_FACE)]), self.deploy(e, p1, [])]
        self.run_phases_2_to_4(e, c, {CubeColor.RED: 3})
        self.assertEqual(p0.money, 10 + 3 + 1 - 3)

    def test_r2_burned_by_burn_notice_does_not_pay(self):
        e = self.make_engine()
        p0, p1 = e.state.players
        p0.white_hat = WHITE_HATS[WhiteHatCode.SPOOK]
        p0.ability_v1_status = AbilityStatus.USED
        r2 = self.die(DieColor.RED, R2_FACE)
        c = [self.deploy(e, p0, [self.die(DieColor.PURPLE, PURPLE_STAR), r2], {1: ShieldColor.RED}), self.deploy(e, p1, [])]
        p0.bot.burn_ids = [r2.die_id]
        cr, incomes = self.run_phases_2_to_4(e, c, {CubeColor.BLUE: 1})  # 0 Red damage would trigger R2
        self.assertEqual(incomes[0].burned_die_ids, [r2.die_id])
        self.assertEqual(p0.money, 2)  # Spook +$2 only; no R2 +$2

    def test_surviving_r2_and_b1_pay(self):
        e = self.make_engine()
        p0, p1 = e.state.players
        r2, b1 = self.die(DieColor.RED, R2_FACE), self.die(DieColor.BLUE, B1_FACE)
        c = [self.deploy(e, p0, [r2, b1], {0: ShieldColor.RED, 1: ShieldColor.BLUE}), self.deploy(e, p1, [])]
        self.run_phases_2_to_4(e, c, {CubeColor.RED: 1, CubeColor.BLUE: 1})
        self.assertEqual(p0.money, 2 + 2)
        self.assertEqual(p0.secrets, 8)

    def test_legacy_path_unchanged(self):
        from sim.engine import legacy_v033

        # Legacy: a corruption-glitched R3 also does not pay, because the glitch clears its face (v0.33 behaviour).
        e = self.make_engine(deck=noop_deck(CorruptionSpace(index=1, label="Glitch 1 die", demote_dice=1)),
                             round_sequence=RoundSequence.V033_THREE_PHASE)
        p0, p1 = e.state.players
        p0.money = 10
        r3 = self.die(DieColor.RED, R3_FACE)
        c = [self.deploy(e, p0, [r3]), self.deploy(e, p1, [])]
        self.force(e, c, {CubeColor.BLACK: 1, CubeColor.RED: 3})
        legacy_v033.execute_phase_2_v033(e, c)
        self.assertIsNone(r3.current_face)
        self.assertEqual(p0.money, 7)
        # Legacy policy still pays a rolled die that left In Production with its face intact (no membership check).
        e = self.make_engine(round_sequence=RoundSequence.V033_THREE_PHASE)
        p0 = e.state.players[0]
        p0.money = 10
        r3 = self.die(DieColor.RED, R3_FACE)  # rolled, not In Production
        phase4_attack_resolution.resolve_player_defense_and_wear(
            e, p0, [r3], {}, {CubeColor.RED: 3, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            {CubeColor.RED: 3}, "SCRIPT_KIDDIE")
        self.assertEqual(p0.money, 10 + 1 - 3)


class OverrideSpyBot(StubBot):
    """Records Phase 1 company-override hook calls and always accepts them."""

    def __init__(self, bot_id, plan=None):
        super().__init__(bot_id, plan)
        self.meridian_calls = 0
        self.helix_calls = 0

    def choose_meridian_override(self, *a, **k):
        self.meridian_calls += 1
        return True

    def choose_helix_override(self, *a, **k):
        self.helix_calls += 1
        return True


class TestIdentitySeparationNoBridge(SixPhaseHarness):
    """User-approved fix: Institutional Overrides only from the Client Company; Signature Protocols only from
    the White Hat Dossier. The v0.33 archetype bridge survives only under GameConfig.legacy_v033()."""

    def _setup(self, company, white_hat, legacy=False, plan=None):
        kw = {"round_sequence": RoundSequence.V033_THREE_PHASE, "legacy_archetype_override_bridge": True} if legacy else {}
        kw["research_track_model"] = ResearchTrackModel.V034_THREE_LEVEL  # v0.34 Slush Fund (auto, per version)
        e = self.make_engine(bots=[OverrideSpyBot(0, plan), OverrideSpyBot(1)], **kw)
        p0 = e.state.players[0]
        p0.company = COMPANIES[company] if company else None
        p0.white_hat = WHITE_HATS[white_hat] if white_hat else None
        p0.ability_v1_status = AbilityStatus.AVAILABLE
        return e, p0, e.state.players[1]

    def _attack(self, e, p0, p1, exits, dice0=()):
        c = [self.deploy(e, p0, list(dice0)), self.deploy(e, p1, [])]
        self.force(e, c, exits)
        cr = phase2_compiler.execute_compiler_drop(e, c)
        phase4_attack_resolution.execute_attack_resolution(e, c, cr)

    # --- Slush Fund (DTO) ---
    def test_spook_without_dto_never_gets_slush_fund(self):
        e, p0, p1 = self._setup(CompanyCode.MERIDIAN, WhiteHatCode.SPOOK)
        p0.secrets = 3
        self._attack(e, p0, p1, {CubeColor.BLUE: 1})
        self.assertEqual(p0.secrets, 2)
        self.assertTrue(p0.is_ability_available("v1.0"))

    def test_dto_slush_fund_works_with_any_white_hat(self):
        e, p0, p1 = self._setup(CompanyCode.DTO, WhiteHatCode.OPERATOR)
        p0.secrets = 3
        self._attack(e, p0, p1, {CubeColor.BLUE: 1})
        self.assertEqual(p0.secrets, 3)
        self.assertFalse(p0.is_ability_available("v1.0"))

    # --- Baffle Echo (Aegis) ---
    def test_acoustic_without_aegis_never_gets_baffle_echo(self):
        e, p0, p1 = self._setup(CompanyCode.MERIDIAN, WhiteHatCode.ACOUSTIC)
        p0.money = 5
        self._attack(e, p0, p1, {CubeColor.RED: 1})
        self.assertEqual(p0.money, 4)
        self.assertTrue(p0.is_ability_available("v1.0"))
        self.assertEqual(phase4_attack_resolution.aegis_qualifying_colors(
            e, p0, {CubeColor.RED: 1}, {CubeColor.RED: 1}), [])

    def test_aegis_baffle_echo_works_with_any_white_hat(self):
        e, p0, p1 = self._setup(CompanyCode.AEGIS, WhiteHatCode.SPOOK)
        p0.money = 5
        self._attack(e, p0, p1, {CubeColor.RED: 1})
        self.assertEqual(p0.money, 5)
        self.assertFalse(p0.is_ability_available("v1.0"))

    # --- Magnetic Splice (Omnidyne) ---
    def _splice(self, company, white_hat):
        e, p0, p1 = self._setup(company, white_hat)
        g = self.die(DieColor.RED, Face(name="x"), cost=5)
        p0.glitched_dice.append(g)
        phase5_pipeline_shift.execute_pipeline_shift(e)
        return p0, g

    def test_phreaker_without_omnidyne_never_splices(self):
        p0, g = self._splice(CompanyCode.MERIDIAN, WhiteHatCode.PHREAKER)
        self.assertNotIn(g, p0.ready_for_release_dice)
        self.assertTrue(p0.is_ability_available("v1.0"))

    def test_omnidyne_splice_works_with_any_white_hat(self):
        p0, g = self._splice(CompanyCode.OMNIDYNE, WhiteHatCode.CIPHER)
        self.assertIn(g, p0.ready_for_release_dice)

    # --- Algorithmic Arbitrage (Prometheus) ---
    def _arbitrage(self, company, white_hat):
        plan = Phase3ActionPlan(use_prometheus_override=True, prometheus_mode="CASH")
        e, p0, p1 = self._setup(company, white_hat, plan=plan)
        phase6_operations.execute_operations(e)
        return e, p0

    def test_cipher_without_prometheus_never_gets_arbitrage(self):
        e, p0 = self._arbitrage(CompanyCode.MERIDIAN, WhiteHatCode.CIPHER)
        self.assertEqual(p0.money, 0)
        self.assertTrue(p0.is_ability_available("v1.0"))

    def test_prometheus_arbitrage_works_with_any_white_hat(self):
        e, p0 = self._arbitrage(CompanyCode.PROMETHEUS, WhiteHatCode.PHREAKER)
        self.assertEqual(p0.money, e.config.cipher_arbitrage_cash)

    # --- Redundant Crew (Meridian) / Brute-Force Bypass (Helix): Phase 1 hooks ---
    def _phase1(self, company, white_hat):
        e, p0, p1 = self._setup(company, white_hat)
        p0.ready_for_release_dice.extend([self.die(DieColor.GRAY, INCOME_1) for _ in range(3)])
        e._execute_phase_1()
        return p0

    def test_operator_without_meridian_never_gets_redundant_crew(self):
        p0 = self._phase1(CompanyCode.AEGIS, WhiteHatCode.OPERATOR)
        self.assertEqual(p0.bot.meridian_calls, 0)
        self.assertEqual(p0.total_contractors_hired, 0)

    def test_meridian_redundant_crew_works_with_any_white_hat(self):
        p0 = self._phase1(CompanyCode.MERIDIAN, WhiteHatCode.PRODIGY)
        self.assertEqual(p0.bot.meridian_calls, 1)
        self.assertEqual(p0.total_contractors_hired, 2)

    def test_prodigy_without_helix_never_gets_brute_force_bypass(self):
        p0 = self._phase1(CompanyCode.AEGIS, WhiteHatCode.PRODIGY)
        self.assertEqual(p0.bot.helix_calls, 0)

    def test_helix_brute_force_bypass_works_with_any_white_hat(self):
        p0 = self._phase1(CompanyCode.HELIX, WhiteHatCode.ACOUSTIC)
        self.assertEqual(p0.bot.helix_calls, 1)

    # --- Signature Protocols never fire from a company alone ---
    def test_signature_protocol_never_fires_from_company_alone(self):
        for company in (CompanyCode.DTO, CompanyCode.PROMETHEUS, CompanyCode.AEGIS):  # Spook / Cipher / Acoustic pairs
            e, p0, p1 = self._setup(company, None)
            c = [self.deploy(e, p0, [self.die(DieColor.PURPLE, PURPLE_STAR)]), self.deploy(e, p1, [])]
            self.force(e, c, {CubeColor.RED: 1, CubeColor.BLUE: 1})
            phase2_compiler.execute_compiler_drop(e, c)
            rec = phase3_income.execute_income(e, c)[0]
            self.assertEqual((rec.money, rec.research, rec.secrets), (0, 0, 0), company)

    def test_archetype_setter_still_assigns_canonical_pair(self):
        from sim.entities import ArchetypeCode, get_archetype_by_code

        e, p0, p1 = self._setup(None, None)
        p0.archetype = get_archetype_by_code(ArchetypeCode.SPOOK)
        self.assertEqual(p0.company.code, CompanyCode.DTO)
        self.assertEqual(p0.white_hat.code, WhiteHatCode.SPOOK)
        self.assertEqual(p0.archetype.code, ArchetypeCode.SPOOK)

    # --- Legacy parity: the bridge is still present under legacy_v033 ---
    def test_legacy_v033_config_keeps_the_bridge(self):
        self.assertTrue(GameConfig.legacy_v033().legacy_archetype_override_bridge)
        self.assertFalse(GameConfig.legacy_v034().legacy_archetype_override_bridge)
        e, p0, p1 = self._setup(CompanyCode.MERIDIAN, WhiteHatCode.SPOOK, legacy=True)
        p0.secrets = 3
        self._attack(e, p0, p1, {CubeColor.BLUE: 1})
        self.assertEqual(p0.secrets, 3)  # v0.33 bug reproduced: Spook gets DTO Slush Fund
        e, p0, p1 = self._setup(CompanyCode.DTO, None, legacy=True)
        c = [self.deploy(e, p0, [self.die(DieColor.PURPLE, PURPLE_STAR)]), self.deploy(e, p1, [])]
        self.force(e, c, {CubeColor.RED: 1})
        phase2_compiler.execute_compiler_drop(e, c)
        self.assertEqual(phase3_income.execute_income(e, c)[0].money, 2)  # company-only player gets Spook +$2


class TestSharedVictory(SixPhaseHarness):
    """RULES §5: 'If still tied, victory is shared' - no seat bias via winner_id."""

    def _tie(self, e, wipeout):
        from sim.engine.end_game import evaluate_end_game

        for p in e.state.players:
            p.money, p.secrets, p.research_tokens = 3, (-1 if wipeout else 5), 0
            p.is_patient_zero = wipeout
            p.breach_depth = 1 if wipeout else 0
        return evaluate_end_game(e)

    def test_fully_tied_total_wipeout_is_shared(self):
        e = self.make_engine(n=3)
        res = self._tie(e, wipeout=True)
        self.assertTrue(res.is_total_wipeout)
        self.assertEqual(sorted(res.winner_ids), [0, 1, 2])
        self.assertIsNone(res.winner_id)
        self.assertTrue(res.is_shared_victory)
        self.assertTrue(all(r["is_winner"] and r["rank"] == 1 for r in res.rankings))

    def test_fully_tied_standard_ending_is_shared(self):
        e = self.make_engine(n=3)
        e.state.players[2].is_patient_zero = True  # eliminated player never shares the win
        res = self._tie(e, wipeout=False)
        self.assertEqual(sorted(res.winner_ids), [0, 1, 2])  # _tie resets PZ; re-run with one breached
        e.state.players[2].is_patient_zero = True
        e.state.players[2].secrets = 0
        from sim.engine.end_game import evaluate_end_game

        res = evaluate_end_game(e)
        self.assertEqual(sorted(res.winner_ids), [0, 1])
        self.assertIsNone(res.winner_id)
        self.assertTrue(res.is_shared_victory)
        ranks = {r["player_id"]: r["rank"] for r in res.rankings}
        self.assertEqual((ranks[0], ranks[1], ranks[2]), (1, 1, 3))

    def test_single_winner(self):
        e = self.make_engine(n=3)
        self._tie(e, wipeout=False)
        e.state.players[1].secrets = 6
        from sim.engine.end_game import evaluate_end_game

        res = evaluate_end_game(e)
        self.assertEqual(res.winner_ids, [1])
        self.assertEqual(res.winner_id, 1)
        self.assertFalse(res.is_shared_victory)

    def test_legacy_keeps_v033_winner_id(self):
        e = self.make_engine(n=3, round_sequence=RoundSequence.V033_THREE_PHASE)
        res = self._tie(e, wipeout=True)
        self.assertEqual(res.winner_id, 0)                 # v0.33 seat-order reporting kept for parity
        self.assertEqual(sorted(res.winner_ids), [0, 1, 2])
        self.assertTrue(res.is_shared_victory)
        self.assertEqual([r["rank"] for r in res.rankings], [1, 2, 3])

    def test_web_serializes_shared_victory(self):
        from web.game_controller import GameController

        ctrl = GameController()
        ctrl.new_game(num_players=2, seed=1)
        for p in ctrl.state.players:
            p.company = p.white_hat = None
            p.money, p.secrets, p.research_tokens = 3, 5, 0
            p.ready_for_release_dice.clear(); p.in_production_dice.clear()
            p.glitched_dice.clear(); p.scanned_dice.clear()
        out = ctrl._serialize_end_game_result(ctrl.engine.evaluate_end_game())
        self.assertTrue(out["is_shared_victory"])
        self.assertEqual(sorted(out["winner_ids"]), [0, 1])
        self.assertIsNone(out["winner_id"])
        self.assertIn("shared victory", out["winner_name"])


if __name__ == "__main__":
    unittest.main()
