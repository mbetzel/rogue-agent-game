"""Phase 45 (v0.36.0) Red rework: Market Share, Market Collapse, Public Relations Track, Marketing ★ variants and
free-choice Generic shields. Spec: docs/specs/v360_market_share_red_rework_spec.md §9 (MS-01..MS-50), with the
§15.1 User resolutions (2026-11-06)."""

from __future__ import annotations

import json
import os
import random
import unittest
from typing import Dict, List, Optional
from unittest import mock

from sim.bots import (
    AccelerationistBot,
    AdaptiveBalancedBot,
    Phase3ActionPlan,
    RecklessSaboteurBot,
    SecOpsTurtleBot,
    VentureGreedBot,
)
from sim.bots import market_share_policy as msp
from sim.bots.research_policy import ResearchPolicy, plan_research3
from sim.config import (
    AnyShieldPolicy,
    CubeColor,
    DieColor,
    EndGameReason,
    GameConfig,
    PatentsMode,
    RedMode,
    RedVariantSet,
    RoundSequence,
    ShieldColor,
    TiebreakOrder,
)
from sim.engine import GameEngine, market_share, phase1_roll_deploy
from sim.engine import phase4_attack_resolution as p4
from sim.engine import phase6_operations
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
    get_all_variant_cards,
    get_random_companies,
    get_random_setup,
    get_random_white_hats,
    resolve_variant_cards,
)
from tests.test_v340_six_phase_sequence import SixPhaseHarness, StubBot, noop_deck

BOT_CLASSES = [AdaptiveBalancedBot, SecOpsTurtleBot, VentureGreedBot, AccelerationistBot, RecklessSaboteurBot]
ANY1 = Face("Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)
RED1 = Face("Block 1 Red", block_amount=1, shield_color=ShieldColor.RED)
R2_MKT = Face(name="R2: Ad Campaign", is_star=True, star_code="R2_MKT")
R3_MKT = Face(name="R3: Customer Poaching", is_star=True, star_code="R3_MKT")
V035_R2 = Face(name="R2: Threat Bounty", block_amount=2, shield_color=ShieldColor.RED, is_star=True, star_code="R2")


class MSBot(StubBot):
    """Stub bot: explicit plans (not replaced by the research policy), optional Generic split / poach target."""

    research_aware = False

    def __init__(self, bot_id: int, plan: Optional[Phase3ActionPlan] = None, alloc=None, poach=None) -> None:
        super().__init__(bot_id, plan)
        self.alloc = alloc
        self.poach = poach
        self.alloc_calls: List[Dict] = []
        self.poach_calls: List[List[int]] = []

    def choose_any_shield_allocation(self, player_state, remaining, available_any, game_state, attack):
        self.alloc_calls.append(dict(remaining))
        if self.alloc is not None:
            return dict(self.alloc)
        return super().choose_any_shield_allocation(player_state, remaining, available_any, game_state, attack)

    def choose_poach_target(self, player_state, game_state, tied_pids):
        self.poach_calls.append(list(tied_pids))
        if self.poach is not None:
            return self.poach
        return super().choose_poach_target(player_state, game_state, tied_pids)


def deck(v1_last: Optional[CorruptionSpace] = None, v1_spaces=None, v2_spaces=None) -> List[VersionCard]:
    d = noop_deck()
    s1 = list(v1_spaces or d[0].corruption_track)
    if v1_last is not None:
        s1[-1] = v1_last
    s2 = list(v2_spaces or d[1].corruption_track)
    return [
        VersionCard("v1.0", "Test v1.0", {}, "test", "SCRIPT_KIDDIE", corruption_track=tuple(s1)),
        VersionCard("v2.0", "Test v2.0", {}, "test", "RAAS", corruption_track=tuple(s2)),
        d[2],
    ]


# Mechanics tests pin the pre-iteration-1 tune (start 19/20/20, v1.0 $2 + v2.0 $4) so their arithmetic is explicit;
# the v036() preset values themselves are checked in MS-01 / MS-49 / MS-51.
MECH_TUNE = dict(market_share_start_by_player_count={2: 19, 3: 20, 4: 20}, version_share_payout={"v1.0": 2, "v2.0": 4})


class MSHarness(SixPhaseHarness):
    def make_ms(self, n: int = 2, bots=None, deck_=None, factory=GameConfig.v036, **kw) -> GameEngine:
        for k, v in MECH_TUNE.items():
            kw.setdefault(k, dict(v))
        cfg = factory(num_players=n, enable_compiler_priming=False, **kw)
        bots = bots or [MSBot(i) for i in range(n)]
        e = GameEngine(cfg, bots, seed=7, version_deck=deck_ or noop_deck())
        for p in e.state.players:
            p.company = None
            p.white_hat = None
            for z in (p.ready_for_release_dice, p.in_production_dice, p.glitched_dice, p.scanned_dice, p.contractor_dice):
                z.clear()
            p.money = 0
            p.research_tokens = 0
            p.secrets = 8
        for c in e.state.staging_cup:
            e.state.staging_cup[c] = 0
        e.state.first_player_index = 0
        self._next_id = 500
        return e

    def bare(self, e, *players):
        return [self.deploy(e, p, []) for p in (players or e.state.players)]

    def ops(self, e, p, **plan_kw):
        phase6_operations.execute_player_operations_turn(e, p, Phase3ActionPlan(**plan_kw))

    @staticmethod
    def cmp(e, version="v1.0", spill=False):
        return market_share.resolve_version_comparison(e, version, spill)


# ----------------------------------------------------------------------------------------------
# MS-01..04 Configuration and parity
# ----------------------------------------------------------------------------------------------
class TestConfig(unittest.TestCase):
    def test_ms01_resolution(self):
        # Phase B: GameConfig() is the v0.36.0 ruleset; legacy_v035() is the v0.35.0 baseline.
        self.assertEqual(GameConfig(), GameConfig.v036())
        for n in (2, 3, 4):
            self.assertEqual(GameConfig(num_players=n), GameConfig.v036(num_players=n))
        c = GameConfig.legacy_v035()
        self.assertEqual((c.red_mode, c.patents_mode, c.red_variant_set, c.tiebreak_order, c.any_shield_policy),
                         (RedMode.RANSOM, PatentsMode.PATENTS, RedVariantSet.V035, TiebreakOrder.V035,
                          AnyShieldPolicy.V035_TIERS))
        self.assertFalse(c.market_collapse_enabled)
        self.assertEqual(c.version_share_payout, {})
        self.assertFalse(c.is_market_share or c.is_share_regain)
        self.assertEqual(c.starting_secrets_by_player_count, {2: 8, 3: 8, 4: 8})
        v = GameConfig.v036()
        self.assertEqual((v.red_mode, v.patents_mode, v.red_variant_set, v.tiebreak_order, v.any_shield_policy),
                         (RedMode.MARKET_SHARE, PatentsMode.SHARE_REGAIN, RedVariantSet.MARKETING,
                          TiebreakOrder.MARKET_SHARE_FIRST, AnyShieldPolicy.FREE_CHOICE))
        self.assertTrue(v.market_collapse_enabled and v.is_market_share and v.is_share_regain)
        self.assertEqual(v.version_share_payout, {"v2.0": 4})  # balance iteration 1: v1.0 comparison dropped
        self.assertEqual(v.starting_secrets_by_player_count, {2: 7, 3: 7, 4: 8})  # final tune (plan §11)
        self.assertEqual([v.market_share_start(n) for n in (2, 3, 4)], [17, 18, 18])  # balance iteration 1
        # the bare MARKET_SHARE resolution matches the preset
        b = GameConfig(red_mode=RedMode.MARKET_SHARE)
        self.assertEqual((b.version_share_payout, b.market_share_start(2)), ({"v2.0": 4}, 17))
        self.assertEqual(GameConfig.legacy_v035().red_mode, RedMode.RANSOM)
        for f in (GameConfig.legacy_v034, GameConfig.legacy_v033):
            self.assertEqual(f().red_mode, RedMode.RANSOM)
        # strings coerce; explicit sub-flags win; no re-resolve after construction
        s = GameConfig(red_mode="MARKET_SHARE", any_shield_policy="V035_TIERS")
        self.assertEqual((s.red_mode, s.any_shield_policy), (RedMode.MARKET_SHARE, AnyShieldPolicy.V035_TIERS))
        # allowed under RANSOM (documented, no raise)
        GameConfig.legacy_v035(any_shield_policy=AnyShieldPolicy.FREE_CHOICE)
        GameConfig.legacy_v035(red_variant_set=RedVariantSet.MARKETING)
        # legacy round / track models default to RANSOM
        self.assertEqual(GameConfig(round_sequence=RoundSequence.V033_THREE_PHASE).red_mode, RedMode.RANSOM)
        self.assertEqual(GameConfig(research_track_model="V034_THREE_LEVEL").red_mode, RedMode.RANSOM)

    def test_ms02_invalid_combos(self):
        bad = [
            dict(patents_mode=PatentsMode.SHARE_REGAIN),
            dict(market_collapse_enabled=True),
            dict(version_share_payout={"v1.0": 2}),
            dict(tiebreak_order=TiebreakOrder.MARKET_SHARE_FIRST),
            dict(red_mode=RedMode.MARKET_SHARE, share_regain_cost_by_level={0: 2, 1: 2, 2: 2, 3: 2}),
            dict(red_mode=RedMode.MARKET_SHARE, share_regain_cap_by_level={0: 1}),
            dict(red_mode=RedMode.MARKET_SHARE, market_share_bot_policy="SMART"),
        ]
        for kw in bad:
            kw.setdefault("red_mode", RedMode.RANSOM)
            with self.assertRaises(ValueError, msg=kw):
                GameConfig(**kw)
        with self.assertRaises(ValueError):
            GameConfig(red_mode=RedMode.MARKET_SHARE, round_sequence=RoundSequence.V033_THREE_PHASE)
        with self.assertRaises(ValueError):
            GameConfig.legacy_v033(red_mode=RedMode.MARKET_SHARE)
        with self.assertRaises(ValueError):  # Public Relations regain needs the five-level tracks (review defect 3)
            GameConfig.legacy_v034(red_mode=RedMode.MARKET_SHARE)


class TestParity(unittest.TestCase):
    def test_ms03_v035_parity_fixtures(self):
        from tests.fixtures.v035_parity import capture

        # Phase B: legacy_v035() is the v0.35.0 baseline (full seeds); GameConfig() is now v0.36.0.
        # GameConfig(red_mode=RANSOM) resolves identically and gets a 50-seed subset.
        for n in capture.PLAYER_COUNTS:
            self.assertEqual(GameConfig(num_players=n, red_mode=RedMode.RANSOM), GameConfig.legacy_v035(num_players=n))
        ransom = lambda **kw: GameConfig(red_mode=RedMode.RANSOM, **kw)  # noqa: E731
        for factory, seeds in ((GameConfig.legacy_v035, capture.SEEDS), (ransom, capture.SEEDS[:50])):
            for scenario in capture.SCENARIOS:
                for n in capture.PLAYER_COUNTS:
                    with open(capture.fixture_path(scenario, n), encoding="utf-8") as fh:
                        golden = json.load(fh)
                    for seed in seeds:
                        got = json.loads(json.dumps(capture.run_scenario(factory, scenario, n, seed), sort_keys=True))
                        self.assertEqual(got, golden[str(seed)], f"{factory} {scenario} {n}P seed {seed}")

    def test_ms04_older_fixtures_still_load(self):
        # Full v034 / v033 replays live in tests/test_v350_research_tracks.py (R-26 / R-27); spot-check here.
        from tests.fixtures.v033_parity import capture as c33
        from tests.fixtures.v034_parity import capture as c34

        for cap, factory, seeds in ((c34, GameConfig.legacy_v034, (0, 1, 2)), (c33, GameConfig.legacy_v033, c33.SEEDS)):
            with open(cap.fixture_path("mixed", 3), encoding="utf-8") as fh:
                golden = json.load(fh)
            for seed in seeds:
                got = json.loads(json.dumps(cap.run_scenario(factory, "mixed", 3, seed), sort_keys=True))
                self.assertEqual(got, golden[str(seed)])


# ----------------------------------------------------------------------------------------------
# MS-05..10 Phase 4 Red damage, Slush Fund, Generic shields
# ----------------------------------------------------------------------------------------------
class TestRedDamage(MSHarness):
    def test_ms05_red_lowers_market_share_only(self):
        e = self.make_ms()
        p0, p1 = e.state.players
        p0.money, p0.secrets = 5, 8
        self.run_phases_2_to_4(e, self.bare(e), {CubeColor.RED: 3})
        self.assertEqual((p0.market_share, p0.money, p0.secrets), (16, 5, 8))
        b = p0.last_defense_breakdown
        self.assertEqual((b["unpaid_ransom"], b["flat_ransom_leak"], b["ransom_secret_loss"]), (0, False, 0))
        self.assertEqual((b["market_share_before"], b["market_share_after"], b["market_share_lost"]), (19, 16, 3))
        self.assertEqual((p0.market_share_lost_red, p0.red_incoming_total, p0.red_unblocked_total), (3, 3, 3))
        # RANSOM is untouched: $1 per cube
        e = self.make_engine()
        p0 = e.state.players[0]
        p0.money = 5
        self.run_phases_2_to_4(e, self.bare(e), {CubeColor.RED: 3})
        self.assertEqual((p0.money, p0.market_share), (2, None))

    def test_ms06_red_floor(self):
        e = self.make_ms()
        p0 = e.state.players[0]
        p0.market_share = 2
        self.run_phases_2_to_4(e, self.bare(e), {CubeColor.RED: 5})
        self.assertEqual((p0.market_share, p0.market_share_red_overflow, p0.market_share_lost_red), (0, 3, 2))
        self.assertEqual(p0.market_share_min, 0)

    def test_ms07_slush_fund_blue_only(self):
        e = self.make_ms()
        p0, p1 = e.state.players
        p0.company = COMPANIES[CompanyCode.DTO]
        p0.white_hat = WHITE_HATS[WhiteHatCode.OPERATOR]
        p0.ability_v1_status = AbilityStatus.AVAILABLE
        p0.money = 3
        self.run_phases_2_to_4(e, self.bare(e), {CubeColor.BLUE: 2, CubeColor.RED: 4})
        self.assertEqual((p0.secrets, p0.money, p0.market_share), (8, 3, 15))
        self.assertTrue(p0.slush_fund_used_game)


class TestGenericShields(MSHarness):
    def _any_round(self, alloc, exits, n_any=2, **kw):
        bots = [MSBot(0, alloc=alloc), MSBot(1)]
        e = self.make_ms(bots=bots, **kw)
        p0 = e.state.players[0]
        shields = [self.die(DieColor.GRAY, ANY1) for _ in range(n_any)]
        c = [self.deploy(e, p0, shields, {i: ShieldColor.ANY for i in range(n_any)}), self.deploy(e, e.state.players[1], [])]
        self.run_phases_2_to_4(e, c, exits)
        return e, p0

    def test_ms08_free_choice_honoured_clamped_backfilled(self):
        e, p0 = self._any_round({CubeColor.RED: 2}, {CubeColor.RED: 2, CubeColor.BLUE: 2})
        b = p0.last_defense_breakdown
        self.assertEqual(b["any_allocated"], {"red": 2, "blue": 0, "green": 0})
        self.assertEqual((p0.secrets, p0.market_share), (6, 19))
        self.assertEqual(p0.red_blocked_any_total, 2)
        # illegal: over-asks and asks for a color with no cubes -> clamped, back-filled B > R > G
        e, p0 = self._any_round({CubeColor.GREEN: 3, CubeColor.RED: 9}, {CubeColor.RED: 1, CubeColor.BLUE: 2}, n_any=3)
        self.assertEqual(p0.last_defense_breakdown["any_allocated"], {"red": 1, "blue": 2, "green": 0})
        e, p0 = self._any_round({}, {CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 1}, n_any=2)
        self.assertEqual(p0.last_defense_breakdown["any_allocated"], {"red": 1, "blue": 1, "green": 0})
        V = p4.validate_any_shield_allocation
        R, B, G = CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN
        for raw, rem, avail in (({R: 5, B: 5, G: 5}, {R: 2, B: 1, G: 3}, 4), ({}, {R: 0, B: 0, G: 2}, 5),
                                ({G: -3}, {R: 1, B: 1, G: 1}, 1), ({R: 1}, {R: 3, B: 3, G: 3}, 0)):
            out = V(raw, rem, avail)
            self.assertEqual(sum(out.values()), min(avail, sum(rem.values())), (raw, rem, avail))
            self.assertTrue(all(0 <= out[c] <= rem[c] for c in (R, B, G)))
        self.assertEqual(V({R: 5, B: 5, G: 5}, {R: 2, B: 1, G: 3}, 4), {R: 2, B: 1, G: 1})  # trim B, R, G

    def test_ms09_default_heuristic(self):
        R, B, G = CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN
        e = self.make_ms()
        p0, p1 = e.state.players
        p0.in_production_dice.append(self.die(DieColor.GRAY, Face("+$1", money=1)))
        alloc = lambda rem, avail=1: msp.default_any_shield_allocation(p0, rem, avail, e.state, {R: 1, B: 1, G: 1})
        p0.secrets = 2
        self.assertEqual(alloc({R: 1, B: 2, G: 1})[B], 1)  # lethal Blue first
        p0.secrets, p0.market_share = 8, 1
        self.assertEqual(alloc({R: 1, B: 0, G: 1})[R], 1)  # Red that would collapse beats Green
        p0.market_share = 10
        self.assertEqual(alloc({R: 1, B: 0, G: 1})[G], 1)  # plain Red < Green
        # comparison imminent (v1.0 needs 1 Black) and blocking lifts me off the bottom
        e.state.corruption_track = 3
        p1.market_share = 10
        shield = self.die(DieColor.RED, RED1)
        shield.production_role = ProductionRole.RED_SHIELD  # p1 blocks its Red: estimated to stay at 10
        p1.in_production_dice.append(shield)
        self.assertIsNotNone(msp.comparison_imminent(e.state))
        self.assertEqual(alloc({R: 1, B: 0, G: 1})[R], 1)

    def test_ms09b_rival_projection_uses_phase4_start_share(self):
        R, B, G = CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN
        e = self.make_ms(n=3)
        p0, p1, p2 = e.state.players
        p0.market_share = p1.market_share = p2.market_share = 10
        self.run_phases_2_to_4(e, self.bare(e), {R: 3})
        self.assertEqual(e.state.phase4_snapshot_round, e.state.current_round)
        self.assertEqual(e.state.phase4_market_share_start, {0: 10, 1: 10, 2: 10})
        # p1 already resolved this Phase 4 (10 -> 7); p2 not yet: both projected once from 10
        self.assertEqual(msp.estimated_rival_shares(p0, e.state, 3), {1: 7, 2: 7})
        e.state.phase4_snapshot_round = None  # outside Phase 4: current shares
        self.assertEqual(msp.estimated_rival_shares(p0, e.state, 3), {1: 4, 2: 4})
        # RANSOM valuation scales with red_ransom_per_cube (review defect 5)
        e2 = self.make_engine(red_ransom_per_cube=2)
        q = e2.state.players[0]
        q.money = 3
        self.assertEqual(msp.marginal_block_value(R, {R: 2, B: 0, G: 0}, q, e2.state, {R: 2}, msp.DEFAULT_POLICY), 2.5)
        e3 = self.make_engine()
        q3 = e3.state.players[0]
        q3.money = 3
        self.assertEqual(msp.marginal_block_value(R, {R: 2, B: 0, G: 0}, q3, e3.state, {R: 2}, msp.DEFAULT_POLICY), 0.8)

    def test_ms09c_marketing_faces_count_as_phase3_output(self):
        def returned(v036: bool):
            e = self.make_ms() if v036 else self.make_engine()
            p0 = e.state.players[0]
            r3 = self.die(DieColor.RED, R3_MKT)
            r3.production_role = ProductionRole.RED_SHIELD  # redundant (no Red threat)
            p0.in_production_dice.append(r3)
            p0.ready_for_release_dice.append(self.die(DieColor.BLUE, Face("+$2", money=2)))
            return p0.bot.choose_colored_dice_to_return(p0, 1, {CubeColor.RED: 0})[0].color

        self.assertEqual(returned(False), DieColor.RED)   # RANSOM: inert face -> redundant pure shield first
        self.assertEqual(returned(True), DieColor.BLUE)   # MARKET_SHARE: Customer Poaching is Phase 3 output

    def test_ms10_v035_tiers_under_market_share(self):
        e, p0 = self._any_round(None, {CubeColor.RED: 2, CubeColor.GREEN: 1}, n_any=1,
                                any_shield_policy=AnyShieldPolicy.V035_TIERS)
        self.assertEqual(p0.last_defense_breakdown["any_allocated"]["green"], 1)  # share 19 > 2: Tier 3 Green
        bots = [MSBot(0), MSBot(1)]
        e = self.make_ms(bots=bots, any_shield_policy=AnyShieldPolicy.V035_TIERS)
        p0 = e.state.players[0]
        p0.market_share = 2
        c = [self.deploy(e, p0, [self.die(DieColor.GRAY, ANY1)], {0: ShieldColor.ANY}), self.deploy(e, e.state.players[1], [])]
        self.run_phases_2_to_4(e, c, {CubeColor.RED: 2, CubeColor.GREEN: 1})
        self.assertEqual(p0.last_defense_breakdown["any_allocated"]["red"], 1)  # would collapse: Tier 2 Red
        self.assertEqual(bots[0].alloc_calls, [])


# ----------------------------------------------------------------------------------------------
# MS-11..20 Version comparison
# ----------------------------------------------------------------------------------------------
class TestComparison(MSHarness):
    def _set(self, e, shares, money):
        for p, s, m in zip(e.state.players, shares, money):
            p.market_share, p.money = s, m

    def test_ms11_happy_path_2p(self):
        e = self.make_ms()
        self._set(e, (19, 15), (3, 5))
        rec = self.cmp(e)
        self.assertEqual([p.money for p in e.state.players], [5, 3])
        self.assertEqual((rec.top_pids, rec.bottom_pids, rec.gains, rec.paid, rec.forgiven), ([0], [1], {0: 2}, {1: 2}, {1: 0}))
        self.assertEqual((e.state.players[0].comparison_money_gained, e.state.players[1].comparison_money_paid), (2, 2))

    def test_ms12_shortfall_at_zero(self):
        e = self.make_ms()
        self._set(e, (19, 15), (0, 0))
        rec = self.cmp(e)
        p1 = e.state.players[1]
        self.assertEqual((p1.money, p1.secrets, rec.paid[1], rec.forgiven[1]), (0, 8, 0, 2))
        self.assertEqual(p1.comparison_shortfall_forgiven, 2)

    def test_ms13_partial_shortfall(self):
        e = self.make_ms()
        self._set(e, (19, 15), (0, 1))
        rec = self.cmp(e)
        self.assertEqual((rec.paid[1], rec.forgiven[1], e.state.players[1].money), (1, 1, 0))

    def test_ms14_all_tied(self):
        for n in (2, 4):
            e = self.make_ms(n=n)
            self._set(e, [12] * n, [3] * n)
            rec = self.cmp(e)
            self.assertTrue(rec.all_tied)
            self.assertEqual([p.money for p in e.state.players], [3] * n)

    def test_ms15_shared_places(self):
        e = self.make_ms(n=3)
        self._set(e, (10, 10, 5), (0, 0, 4))
        self.cmp(e)
        self.assertEqual([p.money for p in e.state.players], [2, 2, 2])
        e = self.make_ms(n=4)
        self._set(e, (9, 7, 7, 7), (0, 1, 2, 3))
        rec = self.cmp(e)
        self.assertEqual([p.money for p in e.state.players], [2, 0, 0, 1])
        self.assertEqual(rec.bottom_pids, [1, 2, 3])
        self.assertEqual(rec.forgiven, {1: 1, 2: 0, 3: 0})

    def test_ms16_timing_and_once(self):
        lose1 = CorruptionSpace(index=4, label="Lose $1", lose_money=1)
        v2 = [CorruptionSpace(index=1, label="Lose $1", lose_money=1)] + [CorruptionSpace(index=i, label="noop") for i in range(2, 6)]
        e = self.make_ms(deck_=deck(v1_last=lose1, v2_spaces=v2))
        self._set(e, (19, 15), (3, 3))
        e.state.corruption_track = 3
        cr, _ = self.run_phases_2_to_4(e, self.bare(e), {CubeColor.BLACK: 2})
        rec = e.state.version_comparisons[0]
        self.assertEqual(rec.money_before, {0: 2, 1: 2})  # after the final space's Lose $1, before spillover
        self.assertEqual(rec.payout, 2)
        self.assertFalse(rec.during_spillover)
        self.assertEqual([p.money for p in e.state.players], [3, 0])  # 2+2-1 ; 2-2-0 (spill Lose $1 floors at 0)
        self.assertEqual(len(cr.version_comparisons), 1)
        self.assertIsNone(self.cmp(e))  # once per version
        self.assertEqual(len(e.state.version_comparisons), 1)

    def test_ms17_spillover_fills_two_versions(self):
        e = self.make_ms()
        self._set(e, (19, 15), (5, 5))
        e.state.corruption_track = 3
        self.run_phases_2_to_4(e, self.bare(e), {CubeColor.BLACK: 6})
        vs = [(r.version, r.payout, r.during_spillover) for r in e.state.version_comparisons]
        self.assertEqual(vs, [("v1.0", 2, False), ("v2.0", 4, True)])
        self.assertEqual(e.state.double_version_fill_events, 1)
        self.assertEqual([p.money for p in e.state.players], [11, 0])
        # spillover cascade (FINDINGS §35): the next Version Switch goes straight to v3.0, and
        # later compiles never repeat a comparison (once per version)
        phase1_roll_deploy.check_and_execute_start_of_round_version_transition(e)
        self.assertEqual(e.state.active_version.version_str, "v3.0")
        self.run_phases_2_to_4(e, self.bare(e), {CubeColor.BLACK: 1})
        self.assertEqual(len(e.state.version_comparisons), 2)

    def test_ms18_no_comparison_on_v3_or_game_end(self):
        e = self.make_ms()
        self._set(e, (19, 15), (5, 5))
        e.state.current_version_index, e.state.corruption_track = 2, 5
        self.run_phases_2_to_4(e, self.bare(e), {CubeColor.BLACK: 1})
        self.assertTrue(e.state.singularity_triggered)
        e.state.game_over = True
        e.evaluate_end_game()
        self.assertEqual(e.state.version_comparisons, [])
        self.assertIsNone(self.cmp(e, "v3.0"))

    def test_ms19_patient_zero_excluded(self):
        e = self.make_ms(deck_=deck(v1_last=CorruptionSpace(index=4, label="Lose 1 Secret", lose_secrets=1)))
        self._set(e, (10, 15), (5, 5))
        e.state.players[1].secrets = 1
        e.state.corruption_track = 3
        self.run_phases_2_to_4(e, self.bare(e), {CubeColor.BLACK: 1})
        rec = e.state.version_comparisons[0]
        self.assertTrue(e.state.players[1].is_patient_zero)
        self.assertEqual((rec.eligible_pids, rec.all_tied), ([0], True))
        self.assertEqual(e.state.players[0].money, 5)

    def test_ms20_buffer_overflow_no_comparison(self):
        e = self.make_ms()
        self._set(e, (19, 15), (5, 5))
        e.state.corruption_track = 3
        cr, _ = self.run_phases_2_to_4(e, self.bare(e), {})
        self.assertTrue(cr.buffer_overflow)
        self.assertEqual(e.state.version_comparisons, [])


# ----------------------------------------------------------------------------------------------
# MS-21..28 Market Collapse
# ----------------------------------------------------------------------------------------------
class TestCollapse(MSHarness):
    def test_ms21_collapse_final_round(self):
        e = self.make_ms()
        p0 = e.state.players[0]
        p0.market_share = 1
        c = self.bare(e)
        self.force(e, c, {CubeColor.RED: 1})
        tel = e.run_round()
        s = e.state
        self.assertEqual((s.end_reason, s.final_round_trigger_phase, s.market_collapse_pids), (EndGameReason.MARKET_COLLAPSE, 4, [0]))
        self.assertTrue(s.game_over and s.is_final_round)
        self.assertFalse(any(p.is_patient_zero for p in s.players))
        self.assertEqual(tel.phases_executed, [1, 2, 3, 4, 5, 6])
        self.assertEqual(tel.end_triggers_this_round, ["market_collapse"])
        self.assertEqual(e.evaluate_end_game().end_reason, EndGameReason.MARKET_COLLAPSE)

    def test_ms22_collapse_and_patient_zero_same_phase4(self):
        e = self.make_ms()
        p0, p1 = e.state.players
        p0.market_share, p1.secrets = 1, 1
        self.run_phases_2_to_4(e, self.bare(e), {CubeColor.RED: 1, CubeColor.BLUE: 1})
        self.assertEqual(e.state.end_reason, EndGameReason.PATIENT_ZERO)
        self.assertEqual(e.state.end_triggers, ["patient_zero", "market_collapse"])
        self.assertTrue(p1.is_patient_zero and not p0.is_patient_zero and e.state.is_final_round)

    def test_ms23_pz_phase2_then_collapse(self):
        e = self.make_ms(deck_=deck(v1_spaces=[CorruptionSpace(index=1, label="Lose 1 Secret", lose_secrets=1)] +
                                    [CorruptionSpace(index=i, label="noop") for i in range(2, 5)]))
        p0, p1 = e.state.players
        p0.market_share, p1.secrets = 1, 1
        self.run_phases_2_to_4(e, self.bare(e), {CubeColor.BLACK: 1, CubeColor.RED: 1})
        self.assertEqual(e.state.end_reason, EndGameReason.PATIENT_ZERO)
        self.assertEqual(e.state.final_round_trigger_phase, 2)
        self.assertEqual(e.state.end_triggers, ["patient_zero", "market_collapse"])

    def test_ms24_sole_survivor(self):
        for n in (2, 3):
            e = self.make_ms(n=n)
            ps = e.state.players
            ps[0].market_share = 1
            for p in ps[1:]:
                p.secrets = 1
            self.run_phases_2_to_4(e, self.bare(e), {CubeColor.RED: 1, CubeColor.BLUE: 1})
            e.state.game_over = True
            res = e.evaluate_end_game()
            self.assertEqual((res.winner_id, res.tiebreak_decided_by), (0, "sole_survivor"), n)
            self.assertIn("market_collapse", res.end_triggers)

    def test_ms25_total_wipeout_not_collapse(self):
        e = self.make_ms()
        for p in e.state.players:
            p.secrets, p.market_share = 1, 1
        self.run_phases_2_to_4(e, self.bare(e), {CubeColor.RED: 1, CubeColor.BLUE: 1})
        s = e.state
        self.assertEqual((s.end_reason, s.game_over, s.market_collapse_triggered), (EndGameReason.TOTAL_WIPEOUT, True, False))
        self.assertNotIn("market_collapse", s.end_triggers)

    def test_ms26_singularity_preempts(self):
        e = self.make_ms()
        e.state.current_version_index, e.state.corruption_track = 2, 5
        e.state.players[0].market_share = 0
        self.force(e, self.bare(e), {CubeColor.BLACK: 1})
        with mock.patch.object(market_share, "check_market_collapse", wraps=market_share.check_market_collapse) as m:
            tel = e.run_round()
        self.assertEqual((e.state.end_reason, tel.end_phase), (EndGameReason.SINGULARITY, 2))
        m.assert_not_called()

    def test_ms27_collapse_on_buffer_overflow_via_r3(self):
        e = self.make_ms()
        p0, p1 = e.state.players
        p0.market_share, p1.market_share = 10, 1
        c = [self.deploy(e, p0, [self.die(DieColor.RED, R3_MKT)]), self.deploy(e, p1, [])]
        cr, _ = self.run_phases_2_to_4(e, c, {})
        self.assertTrue(cr.buffer_overflow)
        self.assertEqual((p1.market_share, e.state.end_reason), (0, EndGameReason.MARKET_COLLAPSE))

    def test_ms28_sticky_final_round(self):
        bots = [MSBot(0, plan=Phase3ActionPlan(share_regain=1)), MSBot(1)]
        e = self.make_ms(bots=bots)
        p0 = e.state.players[0]
        p0.market_share, p0.research_tokens = 1, 2
        self.force(e, self.bare(e), {CubeColor.RED: 1})
        e.run_round()
        self.assertEqual((p0.market_share, p0.market_share_regained), (1, 1))
        self.assertTrue(e.state.game_over)
        self.assertEqual(e.state.end_reason, EndGameReason.MARKET_COLLAPSE)


# ----------------------------------------------------------------------------------------------
# MS-29..40 Regain, Public Relations Track, R2, R3, variants
# ----------------------------------------------------------------------------------------------
class TestRegainAndVariants(MSHarness):
    def test_ms29_regain_caps_and_cost(self):
        for lvl, cap in ((0, 1), (1, 1), (2, 2), (3, 2), (4, 3)):
            e = self.make_ms()
            p = e.state.players[0]
            p.patent_level, p.market_share, p.research_tokens = lvl, 10, 9
            got = phase6_operations.execute_share_regain(e, p, 5)
            self.assertEqual((got, p.market_share, p.research_tokens, p.research_spent_regain), (cap, 10 + cap, 9 - 2 * cap, 2 * cap))
            self.assertEqual((p.market_share_regained, p.regain_this_turn), (cap, cap))
        # L4 rate lever
        e = self.make_ms(share_regain_cost_by_level={0: 2, 1: 2, 2: 2, 3: 2, 4: 1})
        p = e.state.players[0]
        p.patent_level, p.market_share, p.research_tokens = 4, 10, 3
        self.assertEqual(phase6_operations.execute_share_regain(e, p, 9), 3)
        self.assertEqual(p.research_tokens, 0)

    def test_ms30_cap_and_mid_turn_upgrade(self):
        e = self.make_ms()
        p = e.state.players[0]
        p.market_share, p.research_tokens = 10, 6
        self.ops(e, p, share_regain=3)
        self.assertEqual((p.market_share, p.research_tokens), (11, 4))
        e = self.make_ms()
        p = e.state.players[0]
        p.market_share, p.research_tokens = 10, 7
        self.ops(e, p, track_upgrades=["PUBLIC_RELATIONS", "PATENT"], share_regain=3)
        self.assertEqual((p.patent_level, p.market_share, p.research_tokens, p.money), (2, 12, 0, 3))

    def test_ms31_at_max(self):
        e = self.make_ms()
        p0, p1 = e.state.players
        p0.research_tokens, p0.money, p0.r2_actions_available = 4, 5, 1
        self.ops(e, p0, share_regain=1, use_r2_share=1)
        self.assertEqual((p0.market_share, p0.research_tokens, p0.money, p0.r2_uses), (19, 4, 5, 0))
        # R3 at max: the rival still loses 1, actor stays capped (User resolution #3)
        p1.market_share = 15
        market_share.queue_poach(e, p0, 1)
        ev = market_share.resolve_poaches(e)[0]
        self.assertEqual((p0.market_share, p1.market_share, ev["moved"], ev["gained"], ev["reason"]), (19, 14, 1, 0, "actor_at_max"))
        p1.market_share = 19
        self.assertTrue(self.cmp(e).all_tied)

    def test_ms32_final_round_regain_and_no_patent_filing(self):
        e = self.make_ms()
        p = e.state.players[0]
        e.state.is_final_round = True
        p.market_share, p.research_tokens, p.secrets = 10, 6, 8
        self.ops(e, p, share_regain=1, patent_filings=2)
        self.assertEqual((p.market_share, p.secrets, p.research_tokens, p.rejected_patent_filings), (11, 8, 4, 2))
        self.assertFalse(p.file_patent())
        self.assertEqual((p.patent_secrets_gained, p.research_spent_patents, p.research_tokens), (0, 0, 4))

    def test_ms33_public_relations_breakthroughs(self):
        from sim.engine import research_tracks as rt

        e = self.make_ms()
        p = e.state.players[0]
        p.research_tokens = 5
        self.ops(e, p, track_upgrades=["PATENT", "PATENT", "PATENT"])
        self.assertEqual((p.patent_level, p.money, p.personal_purple_reserve), (3, 3, 0))
        self.assertEqual(sum(1 for d in p.total_dice if d.color == DieColor.PURPLE), 1)
        self.assertEqual(rt.track_display_name(e.config, "PATENT"), "Public Relations Track")
        self.assertEqual(rt.track_display_name(GameConfig.legacy_v035(), "PATENT"), "Cryptographic Patents Track")
        self.assertEqual(rt.breakthrough_preview(p)["PATENT"]["regain_cap"], 2)

    def test_ms34_ad_campaign(self):
        e = self.make_ms()
        p0, p1 = e.state.players
        p0.market_share, p0.money = 10, 0
        c = [self.deploy(e, p0, [self.die(DieColor.RED, R2_MKT), self.die(DieColor.RED, R2_MKT)]), self.deploy(e, p1, [])]
        self.run_phases_2_to_4(e, c, {CubeColor.BLACK: 1})
        self.assertEqual(p0.r2_actions_available, 2)
        p0.money, p0.research_tokens = 4, 2
        self.ops(e, p0, use_r2_share=2, share_regain=1)
        self.assertEqual((p0.market_share, p0.money, p0.r2_uses, p0.market_share_gained_r2, p0.regain_this_turn), (13, 0, 2, 2, 1))
        self.assertEqual(p0.r2_actions_available, 0)
        # not earned unless In Production in Phase 3; reset in Phase 1
        p0.r2_actions_available = 1
        p0.ready_for_release_dice.append(self.die(DieColor.GRAY, Face("+$1", money=1)))
        phase1_roll_deploy.execute_phase_1(e)
        self.assertEqual(p0.r2_actions_available, 0)
        # under RANSOM the face is inert
        e = self.make_engine(red_variant_set=RedVariantSet.MARKETING)
        q = e.state.players[0]
        self.run_phases_2_to_4(e, [self.deploy(e, q, [self.die(DieColor.RED, R2_MKT)]), self.deploy(e, e.state.players[1], [])],
                               {CubeColor.BLACK: 1})
        self.assertEqual(q.r2_actions_available, 0)

    def _poach(self, n, shares, secrets=None, r3_pids=(0,), first=0, bots=None):
        e = self.make_ms(n=n, bots=bots)
        e.state.first_player_index = first
        for i, p in enumerate(e.state.players):
            p.market_share = shares[i]
            if secrets:
                p.secrets = secrets[i]
            market_share.queue_poach(e, p, 900 + i) if i in r3_pids else None
        return e, market_share.resolve_poaches(e)

    def test_ms35_poach_basic(self):
        e, ev = self._poach(3, (10, 15, 12))
        self.assertEqual([p.market_share for p in e.state.players], [11, 14, 12])
        self.assertEqual((ev[0]["target"], ev[0]["moved"]), (1, 1))
        self.assertEqual(sum(p.market_share for p in e.state.players), 37)

    def test_ms36_poach_ties(self):
        e, ev = self._poach(3, (10, 15, 15), secrets=(8, 5, 9))
        self.assertEqual(ev[0]["target"], 2)
        e, ev = self._poach(3, (10, 15, 15), secrets=(8, 5, 5))
        self.assertEqual(ev[0]["target"], 1)
        bots = [MSBot(0, poach=2), MSBot(1), MSBot(2)]
        e, ev = self._poach(3, (10, 15, 15), secrets=(8, 9, 5), bots=bots)
        self.assertEqual((bots[0].poach_calls, ev[0]["target"]), ([[1, 2]], 2))
        # actor in the middle: clockwise from actor 1 -> 2 before 0
        e, ev = self._poach(3, (15, 10, 15), r3_pids=(1,))
        self.assertEqual(ev[0]["target"], 2)

    def test_ms37_poach_skips_pz_zero_and_chains(self):
        e = self.make_ms(n=3)
        p0, p1, p2 = e.state.players
        p0.market_share, p1.market_share, p2.market_share = 10, 18, 9
        p1.is_patient_zero = True
        market_share.queue_poach(e, p0, 1)
        self.assertEqual(market_share.resolve_poaches(e)[0]["target"], 2)
        e, ev = self._poach(3, (10, 0, 0))
        self.assertEqual((ev[0]["moved"], ev[0]["reason"]), (0, "no_target"))
        e, ev = self._poach(3, (10, 10, 12), r3_pids=(0, 1), first=1)
        self.assertEqual([(x["actor"], x["target"]) for x in ev], [(1, 2), (0, 1)])
        self.assertEqual([p.market_share for p in e.state.players], [11, 10, 11])

    def test_ms38_poach_to_zero_collapses(self):
        e = self.make_ms()
        p0, p1 = e.state.players
        p0.market_share, p1.market_share = 10, 1
        c = [self.deploy(e, p0, [self.die(DieColor.RED, R3_MKT)]), self.deploy(e, p1, [])]
        self.run_phases_2_to_4(e, c, {CubeColor.BLACK: 1})
        self.assertEqual((p1.market_share, p0.market_share, e.state.end_reason), (0, 11, EndGameReason.MARKET_COLLAPSE))
        self.assertEqual(e.state.market_collapse_pids, [1])

    def test_ms39_variant_mapping_rng_paired(self):
        seen = set()
        for seed in range(60):
            r1, r2 = random.Random(seed), random.Random(seed)
            v1, _ = get_random_setup(r1)
            v2, _ = get_random_setup(r2)
            self.assertEqual(r1.getstate(), r2.getstate())
            mapped = resolve_variant_cards(v2, "MARKETING")
            want = {"R1": "R1", "R2": "R2_MKT", "R3": "R3_MKT"}[v1[DieColor.RED].code]
            self.assertEqual(mapped[DieColor.RED].code, want)
            self.assertIs(resolve_variant_cards(v1, RedVariantSet.V035), v1)
            for c in (DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW):
                self.assertIs(mapped[c], v2[c])
            seen.add(want)
            e = GameEngine(GameConfig.v036(num_players=2), seed=seed, variant_cards=v2)
            self.assertEqual(e.state.variant_cards[DieColor.RED].code, want)
        self.assertEqual(seen, {"R1", "R2_MKT", "R3_MKT"})
        mk = get_all_variant_cards("MARKETING")
        self.assertEqual(list(mk)[:3], ["R1", "R2_MKT", "R3_MKT"])
        self.assertEqual(len(mk), 15)
        self.assertEqual([mk[c].name for c in ("R1", "R2_MKT", "R3_MKT")], ["Brand Protection", "Ad Campaign", "Customer Poaching"])
        self.assertEqual([mk[c].cost for c in ("R1", "R2_MKT", "R3_MKT")], [5, 4, 5])
        self.assertEqual([mk[c].printed_code for c in ("R1", "R2_MKT", "R3_MKT")], ["R1", "R2", "R3"])
        self.assertEqual(list(get_all_variant_cards())[:3], ["R1", "R2", "R3"])

    def test_ms40_old_bonuses_inert_and_r1_identical(self):
        def r2_round(v036: bool):
            e = self.make_ms() if v036 else self.make_engine()
            p0 = e.state.players[0]
            c = [self.deploy(e, p0, [self.die(DieColor.RED, V035_R2)], {0: ShieldColor.RED}), self.deploy(e, e.state.players[1], [])]
            self.run_phases_2_to_4(e, c, {CubeColor.RED: 1})
            return p0.money

        self.assertEqual(r2_round(False), 2)
        self.assertEqual(r2_round(True), 0)
        a, b = get_all_variant_cards()["R1"], get_all_variant_cards("MARKETING")["R1"]
        fa, fb = a.star_face, b.star_face
        self.assertEqual((fa.block_amount, fa.shield_color, fa.money, fa.star_code, a.cost),
                         (fb.block_amount, fb.shield_color, fb.money, fb.star_code, b.cost))
        self.assertEqual(b.name, "Brand Protection")


# ----------------------------------------------------------------------------------------------
# MS-41..43 Tiebreaks and invariants
# ----------------------------------------------------------------------------------------------
def _seeded_engine(factory, n, idx, seed, bot_mod=None, **kw):
    rng = random.Random(seed)
    bots = [BOT_CLASSES[(idx * n + i) % 5](i) for i in range(n)]
    rng.shuffle(bots)
    for i, b in enumerate(bots):
        b.player_id = i
        if bot_mod:
            bot_mod(b)
    variants, version_deck = get_random_setup(rng, profile="STANDARD")
    cfg = factory(num_players=n, enable_corporate_asymmetry=True, **kw)
    return GameEngine(cfg, bots, seed=seed, variant_cards=variants, version_deck=version_deck,
                      companies=get_random_companies(n, rng), white_hats=get_random_white_hats(n, rng))


class TestTiebreaks(MSHarness):
    def _end(self, e, rows):
        for p, (sec, ms, money) in zip(e.state.players, rows):
            p.secrets, p.market_share, p.money = sec, ms, money
        e.state.game_over = True
        return e.evaluate_end_game()

    def test_ms41_tiebreak_ordering(self):
        res = self._end(self.make_ms(), [(5, 10, 0), (5, 9, 10)])
        self.assertEqual((res.winner_id, res.tiebreak_decided_by), (0, "market_share"))
        res = self._end(self.make_ms(), [(5, 10, 0), (6, 1, 0)])
        self.assertEqual((res.winner_id, res.tiebreak_decided_by), (1, "secrets"))
        res = self._end(self.make_ms(), [(5, 10, 3), (5, 10, 1)])
        self.assertEqual((res.winner_id, res.tiebreak_decided_by), (0, "money"))
        res = self._end(self.make_ms(), [(5, 10, 3), (5, 10, 3)])
        self.assertEqual((res.winner_id, res.is_shared_victory, res.tiebreak_decided_by), (None, True, "shared"))
        e = self.make_ms(n=3)
        e.state.players[2].is_patient_zero = True
        res = self._end(e, [(5, 3, 0), (5, 2, 0), (9, 19, 9)])
        self.assertEqual([r["player_id"] for r in res.rankings], [0, 1, 2])
        # V035 order unchanged under defaults (market_share is None there)
        e = self.make_engine()
        for p, m in zip(e.state.players, (0, 10)):
            p.secrets, p.money = 5, m
        e.state.game_over = True
        res = e.evaluate_end_game()
        self.assertEqual((res.winner_id, res.tiebreak_decided_by), (1, "money"))
        self.assertIsNone(res.rankings[0]["market_share"])

    def test_ms42_total_wipeout_ranking(self):
        e = self.make_ms()
        p0, p1 = e.state.players
        for p in (p0, p1):
            p.is_patient_zero = True
        p0.breach_depth, p1.breach_depth = 9, 0
        res = self._end(e, [(-9, 5, 0), (0, 3, 9)])
        self.assertTrue(res.is_total_wipeout)
        self.assertEqual((res.winner_id, res.tiebreak_decided_by), (0, "market_share"))


def _ms_ledger_ok(p) -> bool:
    return (p.market_share_start - p.market_share_lost_red - p.market_share_lost_poach + p.market_share_gained_poach
            + p.market_share_regained + p.market_share_gained_r2) == p.market_share


class TestWholeGameV036(unittest.TestCase):
    def test_ms43_ledgers_and_ranges(self):
        for idx in range(300):
            n = 2 + idx % 3
            e = _seeded_engine(GameConfig.v036, n, idx, 7_000 + idx)
            res = e.run_game()
            for p in e.state.players:
                self.assertTrue(_ms_ledger_ok(p), (idx, p.player_id))
                spent = sum(p.research_spent_tracks.values()) + p.research_spent_patents + p.research_spent_regain
                self.assertEqual(p.starting_research + p.research_earned_total - spent - p.research_lost_total,
                                 p.research_tokens, idx)
                self.assertEqual((p.patent_secrets_gained, p.research_spent_patents), (0, 0))
            for t in res.telemetry_history:
                for ph, snaps in t.phase_snapshots.items():
                    for s in snaps:
                        self.assertTrue(0 <= s["market_share"] <= e.config.market_share_start(n), (idx, ph))
                for s in t.phase_snapshots.get(1, []):  # INV-MS-COLLAPSE-02 (Phase 1 cannot change Market Share)
                    if not s["is_patient_zero"]:
                        self.assertGreaterEqual(s["market_share"], 1, (idx, t.round_number))
            if res.end_reason == EndGameReason.MARKET_COLLAPSE:
                self.assertEqual(res.end_triggers[-1], "market_collapse")
            total_poach = sum(p.market_share_gained_poach for p in e.state.players)
            self.assertLessEqual(total_poach, sum(p.market_share_lost_poach for p in e.state.players))

    def test_ms44_determinism(self):
        def sig(policy, seed):
            r = _seeded_engine(GameConfig.v036, 2 + seed % 3, seed, seed, market_share_bot_policy=policy).run_game()
            return json.dumps([r.end_reason.value, r.total_rounds, r.rankings, r.end_triggers, r.version_comparisons],
                              sort_keys=True, default=str)

        for policy in ("AWARE", "NAIVE"):
            for seed in range(100):
                self.assertEqual(sig(policy, seed), sig(policy, seed), (policy, seed))

    def test_ms45_no_rng(self):
        e = _seeded_engine(GameConfig.v036, 3, 1, 11)
        for _ in range(3):
            if not e.state.game_over:
                e.run_round()
        s = e.state
        p = s.players[0]

        def boom(*a, **k):
            raise AssertionError("RNG used")

        names = ("random", "randrange", "randint", "choice", "choices", "shuffle", "sample", "uniform", "getrandbits")
        with mock.patch.multiple(random.Random, **{nm: boom for nm in names}):
            R, B, G = CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN
            market_share.resolve_version_comparison(e, "v2.0", False)
            market_share.queue_poach(e, p, 1)
            market_share.resolve_poaches(e)
            market_share.check_market_collapse(e)
            msp.default_any_shield_allocation(p, {R: 2, B: 1, G: 1}, 3, s, {R: 2, B: 1, G: 1})
            msp.choose_aegis_color(p, [R, B], s, {R: 1, B: 1, G: 0}, {R: 1, B: 1, G: 0})
            msp.urgent_regain(p, s, msp.DEFAULT_POLICY, 2)
            msp.next_comparison(s), msp.comparison_imminent(s), msp.red_pressure(s)
            msp.apply_market_share_policy(p.bot, Phase3ActionPlan(), p, s)
            plan_research3(ResearchPolicy(), p, s, s.config)


# ----------------------------------------------------------------------------------------------
# MS-46..49 Bot policy, telemetry, setup
# ----------------------------------------------------------------------------------------------
class TestBotPolicy(MSHarness):
    def test_ms46_regain_policy(self):
        e = self.make_ms(n=2)
        p0, p1 = e.state.players
        pol = ResearchPolicy(focus_order=("TRIAGE", "DEFENSE", "RELEASE", "PATENT"))
        p0.research_tokens, p0.market_share = 3, 2  # critical -> also "late": no upgrades, regain up to the cap
        self.assertEqual(plan_research3(pol, p0, e.state, e.config), ([], 0, 1))
        p0.market_share = 15  # not critical, no comparison imminent -> upgrades only
        self.assertEqual(plan_research3(pol, p0, e.state, e.config), (["TRIAGE", "TRIAGE"], 0, 0))
        e.state.corruption_track = 3  # v1.0 comparison imminent; +1 lifts me off the bottom (15 vs 16)
        p1.market_share = 16
        self.assertEqual(plan_research3(pol, p0, e.state, e.config), (["TRIAGE"], 0, 1))
        p1.market_share = 18  # +1 does not change place -> no urgent regain
        self.assertEqual(plan_research3(pol, p0, e.state, e.config)[2], 0)
        # NAIVE: no urgency
        e2 = self.make_ms(market_share_bot_policy="NAIVE")
        q = e2.state.players[0]
        q.research_tokens, q.market_share = 3, 2
        self.assertEqual(plan_research3(pol, q, e2.state, e2.config)[2], 0)
        # Final Round: spend up to the cap
        e.state.is_final_round = True
        p0.research_tokens, p0.market_share = 9, 10
        self.assertEqual(plan_research3(pol, p0, e.state, e.config), ([], 0, 1))

    def test_ms47_red_purchase_nudge(self):
        e = self.make_ms()
        p0 = e.state.players[0]
        bot = p0.bot
        p0.money, p0.market_share = 20, 9
        plan = msp.apply_market_share_policy(bot, Phase3ActionPlan(market_purchases=[DieColor.BLUE]), p0, e.state)
        self.assertEqual(plan.market_purchases, [DieColor.BLUE, DieColor.RED])
        plan = msp.apply_market_share_policy(bot, Phase3ActionPlan(market_purchases=[DieColor.BLUE, DieColor.GREEN]), p0, e.state)
        self.assertEqual(plan.market_purchases, [DieColor.BLUE, DieColor.RED])
        plan = msp.apply_market_share_policy(bot, Phase3ActionPlan(market_purchases=[DieColor.RED]), p0, e.state)
        self.assertEqual(plan.market_purchases, [DieColor.RED])  # at most 1 Red from the rule
        p0.market_share = 10  # above 50% of 19
        self.assertEqual(msp.apply_market_share_policy(bot, Phase3ActionPlan(), p0, e.state).market_purchases, [])
        p0.market_share = 9
        p0.money = 4  # Red costs $5
        self.assertEqual(msp.apply_market_share_policy(bot, Phase3ActionPlan(), p0, e.state).market_purchases, [])
        p0.money = 20
        e.state.market[DieColor.RED] = 0
        self.assertEqual(msp.apply_market_share_policy(bot, Phase3ActionPlan(), p0, e.state).market_purchases, [])
        e.state.market[DieColor.RED] = 4
        p0.ready_for_release_dice.extend(self.die(DieColor.RED, RED1) for _ in range(2))
        self.assertEqual(msp.apply_market_share_policy(bot, Phase3ActionPlan(), p0, e.state).market_purchases, [])
        e2 = self.make_ms(market_share_bot_policy="NAIVE")
        q = e2.state.players[0]
        q.money, q.market_share = 20, 2
        self.assertEqual(msp.apply_market_share_policy(q.bot, Phase3ActionPlan(), q, e2.state).market_purchases, [])

    def test_ms48_telemetry(self):
        for idx in range(30):
            n = 2 + idx % 3
            e = _seeded_engine(GameConfig.v036, n, idx, 100 + idx)
            res = e.run_game()
            self.assertEqual(set(res.setup), {"version_cards", "variant_cards", "companies", "white_hats", "first_player_index_start"})
            self.assertEqual(len(res.setup["version_cards"]), 3)
            tr = res.end_triggers
            self.assertEqual(len(tr), len(set(tr)))
            if "market_collapse" in tr and "patient_zero" in tr and res.end_reason == EndGameReason.PATIENT_ZERO:
                self.assertLess(tr.index("patient_zero"), tr.index("market_collapse"))
            if res.end_reason == EndGameReason.TOTAL_WIPEOUT:
                self.assertEqual(tr[0], "patient_zero")
            self.assertIn(res.end_reason.value, res.end_triggers)
            self.assertEqual(sum(len(t.version_comparisons) for t in res.telemetry_history), len(res.version_comparisons))
            self.assertGreaterEqual(res.double_version_fill_events, 0)
            for r in res.rankings:
                pid = r["player_id"]
                tot = lambda f: sum(f(t) for t in res.telemetry_history)
                self.assertEqual(tot(lambda t: t.red_by_player[pid]["share_lost"]), r["market_share_lost_red"])
                self.assertEqual(tot(lambda t: t.red_by_player[pid]["incoming"]), r["red_incoming_total"])
                self.assertEqual(tot(lambda t: t.regain_by_player[pid]["count"]), r["market_share_regained"])
                self.assertEqual(tot(lambda t: t.regain_by_player[pid]["research"]), r["research_spent_regain"])
                self.assertEqual(tot(lambda t: t.r2_by_player[pid]), r["market_share_gained_r2"])
                buys: Dict[str, int] = {}
                for t in res.telemetry_history:
                    for c, k in t.purchases_by_player[pid].items():
                        buys[c] = buys.get(c, 0) + k
                self.assertEqual(buys, r["purchases_by_color"])
                self.assertNotIn("purple", r["purchases_by_color"])  # Central Market only (review defect 4)
                self.assertEqual(res.telemetry_history[-1].market_share_end_of_round[pid], r["market_share"])
                for k in ("market_share_min", "comparison_money_gained", "company_code", "white_hat_code", "seat"):
                    self.assertIn(k, r)
            self.assertIn(res.tiebreak_decided_by, {"secrets", "market_share", "money", "ready_colored_dice_count",
                                                    "patches", "unpatched_dice_count", "shared", "sole_survivor"})
        # RANSOM keeps Red ledgers / purchases but no Market Share telemetry
        res = _seeded_engine(GameConfig.legacy_v035, 3, 0, 5).run_game()
        t = res.telemetry_history[0]
        self.assertTrue(t.red_by_player and not t.regain_by_player and not t.market_share_end_of_round)

    def test_ms49_starting_values(self):
        for n, sec, ms in ((2, 7, 17), (3, 7, 18), (4, 8, 18)):
            e = GameEngine(GameConfig.v036(num_players=n), seed=1)
            for p in e.state.players:
                self.assertEqual((p.secrets, p.market_share, p.market_share_max, p.market_share_min), (sec, ms, ms, ms))
            e = GameEngine(GameConfig(num_players=n), seed=1)  # v0.36 default
            self.assertTrue(all((p.secrets, p.market_share) == (sec, ms) for p in e.state.players))
            e = GameEngine(GameConfig.legacy_v035(num_players=n), seed=1)
            self.assertTrue(all(p.market_share is None and p.secrets == 8 for p in e.state.players))


# ----------------------------------------------------------------------------------------------
# MS-51..55 Balance iteration 1 (User decisions 2026-11-06; game-designer bot fixes B1-B4)
# ----------------------------------------------------------------------------------------------
class TestBalanceIteration1(MSHarness):
    def test_ms51_v1_comparison_absent(self):
        e = self.make_ms(factory=GameConfig.v036, version_share_payout={"v2.0": 4})
        for p, sh in zip(e.state.players, (19, 10)):
            p.market_share, p.money = sh, 5
        e.state.corruption_track = 3
        cr, _ = self.run_phases_2_to_4(e, self.bare(e), {CubeColor.BLACK: 1})
        self.assertTrue(e.state.pending_version_advance)  # v1.0 filled ...
        self.assertEqual((e.state.version_comparisons, cr.version_comparisons), ([], []))  # ... but no comparison event
        self.assertEqual(e.state.version_comparisons_done, set())
        self.assertEqual([p.money for p in e.state.players], [5, 5])
        self.assertIsNone(self.cmp(e, "v1.0"))
        self.assertIsNone(market_share.resolve_version_comparison(e, "v1.0", True))
        self.assertIsNotNone(self.cmp(e, "v2.0"))  # v2.0 -> v3.0 still pays $4
        self.assertEqual(e.state.version_comparisons[0].payout, 4)
        # whole games: never a v1.0 record
        for idx in range(40):
            res = _seeded_engine(GameConfig.v036, 2 + idx % 3, idx, 500 + idx).run_game()
            self.assertTrue(all(r["version"] == "v2.0" for r in res.version_comparisons), idx)

    def test_ms52_next_comparison_skips_dropped_version(self):
        e = self.make_ms(version_share_payout={"v2.0": 4})
        self.assertEqual(msp.next_comparison(e.state), ("v2.0", 4, 4 + 5))
        e.state.corruption_track = 3
        self.assertEqual(msp.next_comparison(e.state), ("v2.0", 4, 1 + 5))
        e.state.pending_version_advance, e.state.overflow_black_cubes_on_next_track = True, 4
        self.assertEqual(msp.next_comparison(e.state), ("v2.0", 4, 1))
        self.assertIsNotNone(msp.comparison_imminent(e.state))
        e.state.version_comparisons_done.add("v2.0")
        self.assertIsNone(msp.next_comparison(e.state))

    def test_ms53_comparison_weight_below_blue_block(self):
        R, B, G = CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN
        self.assertEqual(msp.DEFAULT_POLICY.comparison_weight, 0.5)
        e = self.make_ms(version_share_payout={"v2.0": 4})
        p0, p1 = e.state.players
        e.state.current_version_index, e.state.corruption_track = 1, 4  # v2.0 comparison imminent
        p0.market_share = p1.market_share = 10
        shield = self.die(DieColor.RED, RED1)
        shield.production_role = ProductionRole.RED_SHIELD
        p1.in_production_dice.append(shield)
        p0.in_production_dice.append(self.die(DieColor.GRAY, Face("+$1", money=1)))
        attack = {R: 1, B: 1, G: 1}
        # Red block lifts p0 off the bottom: 0.5 + 0.5 x $4 = 2.5 < Blue 3.0 -> Blue
        self.assertEqual(msp.marginal_block_value(R, {R: 1, B: 1, G: 0}, p0, e.state, attack, msp.DEFAULT_POLICY), 2.5)
        alloc = msp.default_any_shield_allocation(p0, {R: 1, B: 1, G: 0}, 1, e.state, attack)
        self.assertEqual(alloc[B], 1)

    def test_ms54_ad_campaign_whenever_affordable(self):
        e = self.make_ms()
        p0 = e.state.players[0]
        p0.market_share, p0.money, p0.r2_actions_available = 15, 2, 1  # not critical, no comparison imminent
        self.assertEqual(msp.apply_market_share_policy(p0.bot, Phase3ActionPlan(), p0, e.state).use_r2_share, 1)
        p0.money = 1
        self.assertEqual(msp.apply_market_share_policy(p0.bot, Phase3ActionPlan(), p0, e.state).use_r2_share, 0)
        p0.money = 7  # planned $5 Blue purchase is kept affordable
        plan = msp.apply_market_share_policy(p0.bot, Phase3ActionPlan(market_purchases=[DieColor.BLUE]), p0, e.state)
        self.assertEqual(plan.use_r2_share, 1)
        p0.money = 6
        plan = msp.apply_market_share_policy(p0.bot, Phase3ActionPlan(market_purchases=[DieColor.BLUE]), p0, e.state)
        self.assertEqual(plan.use_r2_share, 0)

    def test_ms55_venture_greed_v036_port(self):
        from sim.bots.base import Phase3ActionPlan as Plan  # noqa: F401
        self.assertEqual(VentureGreedBot.research_focus_v036[-1], "PATENT")
        self.assertEqual(RecklessSaboteurBot.research_focus_v036[-1], "PATENT")
        self.assertEqual(VentureGreedBot.research_focus[0], "PATENT")  # v0.35 order untouched
        choice = Face("+$2 / Block 1 Blue", is_choice=True,
                      choices=(Face("Block 1 Blue", block_amount=1, shield_color=ShieldColor.BLUE), Face("+$2", money=2)))
        blue_cup = {CubeColor.BLUE: 2}
        out = {}
        for v036 in (False, True):
            e = self.make_ms(bots=[VentureGreedBot(0), MSBot(1)]) if v036 else self.make_engine(bots=[VentureGreedBot(0), StubBot(1)])
            p0, bot = e.state.players[0], e.state.players[0].bot
            p0.secrets = 8
            d = self.die(DieColor.BLUE, choice)
            shield_die = self.die(DieColor.BLUE, Face("Block 1 Blue", block_amount=1, shield_color=ShieldColor.BLUE))
            decl = bot.declare_choices(p0, [d], blue_cup, {}, "", None)
            commits = bot.commit_shields(p0, [d, shield_die], blue_cup, {}, "", None)
            rr = bot.choose_yahtzee_rerolls(p0, [shield_die], 2, blue_cup, {}, "", None)
            # Spending: $6 with Y1 available; no Yellow / Blue stock, $5 left for a Green die next turn
            p0.money, p0.y1_available = 6, True
            y1 = bot.take_operations_actions(p0, e.state, e.rng).use_y1_secret
            p0.y1_available = False
            p0.money = 5
            e.state.market[DieColor.YELLOW] = e.state.market[DieColor.BLUE] = 0
            buys = bot.take_operations_actions(p0, e.state, e.rng).market_purchases
            out[v036] = (decl.get(0), commits.get(0), rr, y1, buys)
        self.assertEqual(out[False], (1, None, [0], False, []))  # v0.35: take the Money, reroll shields, hoard
        self.assertEqual(out[True], (0, ShieldColor.BLUE, [], True, [DieColor.GREEN]))


@unittest.skipUnless(os.environ.get("RUN_SLOW"), "slow: set RUN_SLOW=1")
class TestSlowSmoke(unittest.TestCase):
    def test_ms50_v036_smoke(self):
        from collections import Counter

        for n in (2, 3, 4):
            c: Counter = Counter()
            for idx in range(600):
                r = _seeded_engine(GameConfig.v036, n, idx, 42 + n * 100_000 + idx).run_game()
                c["patient_zero" if r.end_reason.value == "total_wipeout" else r.end_reason.value] += 1
            print(f"\n{n}P v036 end-reason split (600 games): {dict(c)}  (probe §32 reference; no hard gate)")


if __name__ == "__main__":
    unittest.main()
