"""Lever A: Public Relations push / Market Share dump windows (docs/specs/lever_a_roster_upgrade_spec.md §10)."""

from __future__ import annotations

import copy
import dataclasses
import json
import os
import random
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from sim.config import CubeColor, DieColor, GameConfig, PrPushParams
from sim.engine import GameEngine
from sim.bots import AdaptiveBalancedBot
from sim.bots import market_share_policy as msp
from sim.bots import pr_push_policy as prp
from sim.bots import reference_search as rs
from sim.bots.accelerationist import AccelerationistBot
from sim.bots.mixed_policy import MixedPolicyBot, PROFILE_ATTRS, post_process_operations_plan, raw_operations_plan
from sim.bots.reckless_saboteur import RecklessSaboteurBot
from sim.bots.research_policy import plan_research3, policy_for_bot
from sim.bots.secops_turtle import SecOpsTurtleBot
from sim.bots.venture_greed import VentureGreedBot
from sim.engine.phase4_attack_resolution import validate_any_shield_allocation
from sim.engine.phase6_operations import resolve_operations_plan
from tests.fixtures.v035_parity.capture import _bot_classes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ON = lambda **kw: GameConfig.v037(bot_pr_push=True, **kw)  # noqa: E731
R, B, G = CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN


def _engine(n=3, seed=5, cfg=ON, bots=None, rounds=2):
    bots = bots or [AdaptiveBalancedBot(i) for i in range(n)]
    e = GameEngine(cfg(num_players=n), bots, seed=seed)
    for _ in range(rounds):
        if not e.state.game_over:
            e.run_round()
    return e


def _set(state, shares, secrets=None, version=0):
    for p, s in zip(state.players, shares):
        p.market_share = s
        p.market_share_max = max(p.market_share_max, s, 18)
        p.is_patient_zero = False
    for p, s in zip(state.players, secrets or [5] * len(shares)):
        p.secrets = s
    state.current_version_index = version
    state.phase4_snapshot_round = None  # live == snapshot
    return state


class TestLA01Parity(unittest.TestCase):
    def test_la01_switch_off_explicit(self):
        from tests.fixtures.v036_parity import capture

        off = lambda **kw: GameConfig.legacy_v036(bot_pr_push=False, **kw)  # noqa: E731
        for scenario in capture.SCENARIOS:
            for n in capture.PLAYER_COUNTS:
                with open(capture.fixture_path(scenario, n), encoding="utf-8") as fh:
                    golden = json.load(fh)
                for seed in capture.SEEDS[:20]:
                    got = json.loads(json.dumps(capture.run_scenario(off, scenario, n, seed), sort_keys=True))
                    self.assertEqual(got, golden[str(seed)], f"{scenario} {n}P {seed}")


class TestLA02PushFixtures(unittest.TestCase):
    def test_la02_v037_push_fixtures(self):
        from tests.fixtures.v036_parity.capture import PLAYER_COUNTS, SCENARIOS, SEEDS, run_scenario
        from tests.fixtures.v037_push import capture

        for scenario in SCENARIOS:
            for n in PLAYER_COUNTS:
                with open(capture.fixture_path(scenario, n), encoding="utf-8") as fh:
                    golden = json.load(fh)
                for seed in SEEDS:
                    got = json.loads(json.dumps(run_scenario(capture.config_factory, scenario, n, seed), sort_keys=True))
                    self.assertEqual(got, golden[str(seed)], f"{scenario} {n}P {seed}")

    def test_la02_ref1_fixture(self):
        from tests.fixtures.v037_push import capture

        with open(os.path.join(capture.FIXTURE_DIR, "ref1_3p.json"), encoding="utf-8") as fh:
            golden = json.load(fh)
        for seed in capture.REF_SEEDS[:3]:
            got = json.loads(json.dumps(capture.run_ref1(seed), sort_keys=True))
            self.assertEqual(got, golden[str(seed)], f"ref1 {seed}")

    def test_la02_switch_changes_play(self):
        from tests.fixtures.v036_parity.capture import run_scenario

        diff = sum(run_scenario(ON, "mixed", 3, s) != run_scenario(GameConfig.v037, "mixed", 3, s) for s in range(20))
        self.assertGreater(diff, 0)


def _old_ordered_research(player, state, pr_first, focus):
    """Verbatim copy of the pre-lever-A ``reference_search._ordered_research``."""
    from sim.bots.research_policy import LEVEL_ATTR, ResearchPolicy, _want_list

    cfg = state.config
    costs = cfg.track_step_costs
    res = int(player.research_tokens)
    lv = {t: int(getattr(player, LEVEL_ATTR[t])) for t in LEVEL_ATTR}
    upgrades = []

    def buy(t):
        nonlocal res
        if lv[t] >= 4 or res < int(costs[lv[t]]):
            return False
        res -= int(costs[lv[t]])
        lv[t] += 1
        upgrades.append(t)
        return True

    regain = 0
    if pr_first:
        while buy("PATENT"):
            pass
        if getattr(cfg, "is_share_regain", False) and getattr(player, "market_share", None) is not None:
            lvl = max(0, min(4, lv["PATENT"]))
            cost, cap = int(cfg.share_regain_cost_by_level[lvl]), int(cfg.share_regain_cap_by_level[lvl])
            room = max(0, min(cap, int(player.market_share_max) - int(player.market_share)))
            if cost > 0:
                regain = min(room, res // cost)
                res -= regain * cost
        for t in focus:
            if t != "PATENT":
                buy(t)
    else:
        others = tuple(t for t in focus if t != "PATENT")
        for t in _want_list(ResearchPolicy(focus_order=others), lv):
            if t == "PATENT" or lv[t] >= 4:
                continue
            if not buy(t):
                break
    return upgrades, regain


class TestLA03MovedConstants(unittest.TestCase):
    def test_la03_same_objects(self):
        for n in ("PR_PUSH_POLICY", "PR_PUSH_FOCUS", "PR_PUSH_FILL", "DUMP_POLICY", "DUMP_FOCUS", "DUMP_FILL",
                  "_ordered_research"):
            self.assertIs(getattr(rs, n), getattr(prp, n), n)

    def test_la03_pr_cap4_equals_old(self):
        e = _engine(rounds=1)
        rng = random.Random(1)
        p = e.state.players[0]
        for _ in range(200):
            q = copy.copy(p)
            q.research_tokens = rng.randint(0, 9)
            for a in ("defense_level", "triage_level", "release_level", "patent_level"):
                setattr(q, a, rng.randint(0, 4))
            q.market_share = rng.randint(0, 18)
            pr_first = rng.random() < 0.5
            focus = tuple(rng.sample(["DEFENSE", "TRIAGE", "RELEASE", "PATENT"], 4))
            self.assertEqual(prp._ordered_research(q, e.state, pr_first, focus, pr_cap=4),
                             _old_ordered_research(q, e.state, pr_first, focus))


class TestLA04Config(unittest.TestCase):
    def test_la04(self):
        with self.assertRaises(ValueError):
            GameConfig.v037(bot_pr_push_params=PrPushParams(push_min_share=5, dump_max_share=5))
        with self.assertRaises(ValueError):
            GameConfig.v037(bot_pr_push_params=PrPushParams(push_min_share=4))
        GameConfig.v037(bot_pr_push_params=PrPushParams(push_min_share=5, dump_max_share=4))
        with self.assertRaises(ValueError):
            GameConfig.v037(bot_pr_push_params=PrPushParams(dump_condition="bogus"))
        self.assertEqual(GameConfig(), GameConfig.v037())
        self.assertFalse(GameConfig().bot_pr_push)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            PrPushParams().push_min_share = 3  # type: ignore[misc]


class TestLA05Window(unittest.TestCase):
    def setUp(self):
        self.e = _engine()
        self.s = self.e.state
        self.me = self.s.players[0]
        self.bot = AdaptiveBalancedBot(0)

    def w(self, shares, secrets=None, version=0, **kw):
        _set(self.s, shares, secrets, version)
        return prp.window(self.bot, self.me, self.s, **kw)

    def test_la05_boundaries(self):
        self.assertEqual(self.w([6, 6, 6]), prp.PUSH)
        self.assertEqual(self.w([5, 6, 6]), prp.DUMP)
        self.assertEqual(self.w([13, 6, 10]), prp.PUSH)  # low gap 7
        self.assertEqual(self.w([14, 6, 11]), prp.NONE)  # low gap 8
        self.assertEqual(self.w([13, 10, 10]), prp.PUSH)  # lead over the top rival 3
        self.assertEqual(self.w([14, 10, 10]), prp.NONE)  # lead over the top rival 4
        self.assertEqual(self.w([10, 10, 10], version=1), prp.PUSH)
        self.assertEqual(self.w([10, 10, 10], version=2), prp.NONE)
        self.assertEqual(self.w([10, 10, 10], secrets=[7, 5, 4]), prp.PUSH)
        self.assertEqual(self.w([10, 10, 10], secrets=[8, 5, 4]), prp.NONE)
        self.assertEqual(self.w([10, 10, 10], secrets=[3, 5, 4]), prp.PUSH)
        self.assertEqual(self.w([10, 10, 10], secrets=[2, 5, 4]), prp.NONE)

    def test_la05_patient_zero_and_sole_survivor(self):
        _set(self.s, [10, 0, 10])
        self.s.players[1].is_patient_zero = True  # stale low share must not count (H-LA-1)
        # included, the stale 0 would make the low gap 10 > 7 (NONE); survivors only -> PUSH
        self.assertEqual(prp.window(self.bot, self.me, self.s), prp.PUSH)
        self.s.players[2].is_patient_zero = True
        self.assertEqual(prp.window(self.bot, self.me, self.s), prp.NONE)

    def test_la05_inert(self):
        _set(self.s, [5, 10, 10])
        self.assertEqual(prp.window(self.bot, self.me, self.s), prp.DUMP)
        nb = AdaptiveBalancedBot(0)
        nb.pr_push_capable = False
        self.assertEqual(prp.window(nb, self.me, self.s), prp.NONE)
        self.assertEqual(prp.window(SecOpsTurtleBot(0), self.me, self.s), prp.NONE)
        for cfg in (dataclasses.replace(self.s.config, bot_pr_push=False),
                    dataclasses.replace(self.s.config, market_share_bot_policy="NAIVE")):
            with mock.patch.object(self.s, "config", cfg):
                self.assertEqual(prp.window(self.bot, self.me, self.s), prp.NONE)
        e = _engine(cfg=lambda **kw: GameConfig.legacy_v035(bot_pr_push=True, **kw), rounds=1)
        self.assertEqual(prp.window(self.bot, e.state.players[0], e.state), prp.NONE)

    def test_la05_phase4_snapshot(self):
        _set(self.s, [10, 10, 10])
        self.s.phase4_snapshot_round = self.s.current_round
        self.s.phase4_market_share_start = {p.player_id: 4 for p in self.s.players}
        self.assertEqual(prp.window(self.bot, self.me, self.s), prp.PUSH)  # live
        self.assertEqual(prp.window(self.bot, self.me, self.s, phase4=True), prp.DUMP)  # snapshot


class TestLA06DumpVariant(unittest.TestCase):
    def test_la06(self):
        e = _engine()
        s = e.state
        bot = AdaptiveBalancedBot(0)
        for ms in range(0, 6):
            _set(s, [ms, ms, ms])
            self.assertEqual(prp.window(bot, s.players[0], s), prp.DUMP)
        cfg = dataclasses.replace(s.config, bot_pr_push_params=PrPushParams(dump_condition="reach_or_threat"))
        with mock.patch.object(s, "config", cfg), mock.patch.object(msp, "red_pressure", return_value=0):
            _set(s, [5, 6, 6])
            self.assertEqual(prp.window(bot, s.players[0], s), prp.NONE)
            _set(s, [5, 7, 6])
            self.assertEqual(prp.window(bot, s.players[0], s), prp.DUMP)  # gap -2
        with mock.patch.object(s, "config", cfg), mock.patch.object(msp, "red_pressure", return_value=3):
            _set(s, [5, 6, 6])
            self.assertEqual(prp.window(bot, s.players[0], s), prp.DUMP)  # threat 5 <= 3 + 2


class TestLA07to09Phase4(unittest.TestCase):
    def setUp(self):
        self.e = _engine()
        self.s = self.e.state
        self.me = self.s.players[0]
        self.bot = AdaptiveBalancedBot(0)

    def alloc(self, shares, rem, n, secrets=5):
        _set(self.s, shares, [secrets, 5, 5])
        return self.bot.choose_any_shield_allocation(self.me, dict(rem), n, self.s, dict(rem))

    def test_la07_legal(self):
        rng = random.Random(3)
        for shares in ([10, 10, 10], [4, 10, 10]):
            for _ in range(150):
                rem = {c: rng.randint(0, 4) for c in (R, B, G)}
                n = rng.randint(0, 6)
                out = self.alloc(shares, rem, n, secrets=rng.randint(1, 9))
                self.assertEqual(validate_any_shield_allocation(out, rem, n, self.bot.any_shield_fill_order), out)

    def test_la08_lethal_blue_first(self):
        for shares in ([10, 10, 10], [4, 10, 10]):
            out = self.alloc(shares, {B: 1, R: 3, G: 0}, 1, secrets=1)
            self.assertEqual(out[B], 1, shares)

    def test_la09_fill(self):
        out = self.alloc([10, 10, 10], {B: 1, R: 3, G: 0}, 2, secrets=9)
        self.assertGreaterEqual(out[R], 1)
        out = self.alloc([4, 10, 10], {B: 1, R: 3, G: 1}, 2, secrets=9)
        self.assertEqual(out[R], 0)
        self.assertEqual((out[B], out[G]), (1, 1))
        out = self.alloc([4, 10, 10], {B: 1, R: 3, G: 1}, 4, secrets=9)
        self.assertEqual(out, {B: 1, G: 1, R: 2})


class TestLA10to12Phase6(unittest.TestCase):
    def setUp(self):
        self.e = _engine()
        self.s = self.e.state
        self.me = self.s.players[0]
        self.bot = AdaptiveBalancedBot(0)

    def plan(self):
        rng = random.Random(0)
        return resolve_operations_plan(self.bot, self.me, self.s, rng)

    def test_la10_push_step(self):
        _set(self.s, [10, 10, 10])
        self.me.patent_level, self.me.research_tokens = 0, 2
        p = self.plan()
        self.assertEqual(p.track_upgrades[:1], ["PATENT"])
        self.assertEqual(p.track_upgrades.count("PATENT"), 1)
        self.assertGreaterEqual(p.share_regain, 0)

    def test_la10_la11_push_fallthrough(self):
        for lvl, tok in ((1, 2), (0, 3)):
            _set(self.s, [10, 10, 10])
            self.me.patent_level, self.me.research_tokens = lvl, tok
            p = self.plan()
            ups, _, regain = plan_research3(policy_for_bot(self.bot, self.s), self.me, self.s, self.s.config,
                                            prp.PR_PUSH_POLICY)
            self.assertEqual((p.track_upgrades, p.share_regain), (ups, regain))
        seen = []
        orig = msp.urgent_regain
        with mock.patch.object(msp, "urgent_regain", lambda pl, st, pol, cap: seen.append(pol) or orig(pl, st, pol, cap)):
            self.plan()
        self.assertTrue(seen and all(x is prp.PR_PUSH_POLICY for x in seen))

    def test_la12_dump_and_push_purchases(self):
        _set(self.s, [4, 10, 10])
        self.me.research_tokens, self.me.money = 6, 30
        p = self.plan()
        self.assertNotIn("PATENT", p.track_upgrades)
        self.assertEqual(p.share_regain, 0)
        self.assertNotIn(DieColor.RED, p.market_purchases)
        self.assertNotEqual(getattr(p, "prometheus_discount_die_color", None), DieColor.RED)
        self.assertEqual(prp.effective_policy(self.bot, self.me, self.s), prp.DUMP_POLICY)
        _set(self.s, [10, 10, 10])
        self.assertEqual(prp.preferred_colors(self.bot, self.me, self.s, {R: 0, B: 5, G: 0})[0], DieColor.RED)
        pol = prp.effective_policy(self.bot, self.me, self.s)
        self.assertEqual(pol.red_buy_share_frac, 1.0)


class TestLA13Mixed(unittest.TestCase):
    def test_la13(self):
        e = _engine(rounds=3)
        s = e.state
        _set(s, [10, 10, 10])
        me = s.players[0]
        for seed in range(40):
            m = MixedPolicyBot(0, seed)
            d6 = m._draw("phase6", 0)
            d4 = m._draw("phase4", 0)
            rem = {R: 2, B: 1, G: 1}
            got4 = m.choose_any_shield_allocation(me, dict(rem), 2, s, dict(rem))
            raw = m.take_operations_actions(me, s, random.Random(0))
            got6 = post_process_operations_plan(m, raw, me, s, random.Random(0))
            if isinstance(d4, AdaptiveBalancedBot):
                self.assertEqual(got4, AdaptiveBalancedBot(0).choose_any_shield_allocation(me, dict(rem), 2, s, dict(rem)))
            if isinstance(d6, AdaptiveBalancedBot):
                self.assertEqual(got6, resolve_operations_plan(AdaptiveBalancedBot(0), me, s, random.Random(0)))
            if isinstance(d6, SecOpsTurtleBot):
                off = dataclasses.replace(s.config, bot_pr_push=False)
                with mock.patch.object(s, "config", off):
                    m2 = MixedPolicyBot(0, seed)
                    raw2 = m2.take_operations_actions(me, s, random.Random(0))
                    exp = post_process_operations_plan(m2, raw2, me, s, random.Random(0))
                self.assertEqual(got6, exp)
        self.assertIn("pr_push_capable", PROFILE_ATTRS)


class TestLA14Reference(unittest.TestCase):
    def test_la14(self):
        e = _engine(rounds=3)
        s = e.state
        _set(s, [10, 10, 10])
        me = s.players[0]
        rb = rs.ReferenceSearchBot(0, 1)
        self.assertTrue(rb.pr_push_capable)
        kw = dict(player_state=me, remaining={R: 2, B: 1, G: 1}, available_any=2, game_state=s, attack={R: 2, B: 1, G: 1})
        _, fb = rs._candidate("choose_any_shield_allocation", rb.fallback, kw, random.Random(0))
        self.assertEqual(fb, prp.windowed_any_shield_allocation(prp.PUSH, me, kw["remaining"], 2, s, kw["attack"],
                                                              rb.fallback))
        off = dataclasses.replace(s.config, bot_pr_push=False)
        for cls in (rs.PublicRelationsPushBot, rs.MarketShareDumpBot):
            self.assertFalse(cls(0).pr_push_capable)
            for hook, hk in (("choose_any_shield_allocation", kw),
                             ("take_operations_actions", dict(player_state=me, game_state=s))):
                on_key = rs._candidate(hook, cls(0), hk, random.Random(0))[0]
                with mock.patch.object(s, "config", off):
                    off_key = rs._candidate(hook, cls(0), hk, random.Random(0))[0]
                self.assertEqual(on_key, off_key, (cls, hook))


class TestLA15to16StateAndRng(unittest.TestCase):
    def test_la15_stateless(self):
        bots = [AdaptiveBalancedBot(0), MixedPolicyBot(1, 7), AdaptiveBalancedBot(2)]
        e = GameEngine(ON(num_players=3), bots, seed=7)
        e.run_round()
        before = [dict(vars(b)) for b in bots]
        before[1].pop("draw_log")
        e.run_game()
        after = [dict(vars(b)) for b in bots]
        after[1].pop("draw_log")
        self.assertEqual(before[0], after[0])
        self.assertEqual(before[2], after[2])
        self.assertEqual(set(before[1]), set(after[1]))

    def test_la15_rollout_leaves_live(self):
        classes = _bot_classes()
        bots = [classes[(2 + i) % len(classes)](i) for i in range(3)]
        bots[2] = rs.ReferenceSearchBot(2, 2, n_rollouts=2, halving_first=1)
        e = rs.ReferenceSearchEngine(ON(num_players=3), bots, seed=2)
        e.run_round()
        live = [dict(vars(b)) for b in bots[:2]]
        e.run_round()
        self.assertEqual(live, [dict(vars(b)) for b in bots[:2]])

    def test_la16_rng(self):
        e = _engine(rounds=3)
        s = e.state
        _set(s, [10, 10, 10])
        me = s.players[0]
        bot = AdaptiveBalancedBot(0)
        for shares in ([10, 10, 10], [4, 10, 10]):
            _set(s, shares)
            g0 = e.rng.getstate()
            prp.window(bot, me, s)
            bot.choose_any_shield_allocation(me, {R: 2, B: 1, G: 1}, 2, s, {R: 2, B: 1, G: 1})
            post_process_operations_plan(bot, raw_operations_plan(bot, me, s, random.Random(0)), me, s, random.Random(0))
            self.assertEqual(e.rng.getstate(), g0)
        classes = _bot_classes()
        bots = [classes[(3 + i) % len(classes)](i) for i in range(3)]
        bots[0] = rs.ReferenceSearchBot(0, 3, n_rollouts=2, halving_first=1)
        e2 = rs.ReferenceSearchEngine(ON(num_players=3), bots, seed=3)
        for _ in range(3):
            if not e2.state.game_over:
                e2.run_round()  # _searched raises on any live RNG draw (H1 guard)


class TestLA17Determinism(unittest.TestCase):
    def test_la17(self):
        code = ("import json,sys; sys.path.insert(0,%r); from multiprocessing import Pool; "
                "from scripts.run_reference_bot_validation import play; "
                "t=[('v037','ref1',3,42+300000+i,True,None) for i in range(3)]; "
                "a=[play(x) for x in t]; p=Pool(4); b=p.map(play,t); p.close(); "
                "strip=lambda r:[{k:v for k,v in x.items() if k!='ms'} for x in r]; "
                "assert all(x['error'] is None for x in a), a; "
                "print(json.dumps(strip(a)==strip(b)))") % ROOT
        out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT, timeout=900)
        self.assertEqual(out.stdout.strip(), "true", out.stderr[-2000:])


class TestLA18OtherArchetypes(unittest.TestCase):
    def test_la18(self):
        from tests.fixtures.v036_parity.capture import run_scenario  # noqa: F401

        for seed in range(15):
            res = []
            for cfg in (GameConfig.v037, ON):
                bots = [AccelerationistBot(0), RecklessSaboteurBot(1), SecOpsTurtleBot(2), VentureGreedBot(3)]
                r = GameEngine(cfg(num_players=4), bots, seed=seed).run_game()
                res.append((r.end_reason, r.total_rounds, list(r.winner_ids), r.rankings))
            self.assertEqual(res[0], res[1], seed)


class TestLA19SweepScript(unittest.TestCase):
    def test_la19(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "s.json")
            r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "run_lever_a_sweep.py"), "--games", "4",
                                "--procs", "1", "--out", out,
                                "--cells", 'off;on;{"push_min_share": 5, "dump_max_share": 5}'],
                               capture_output=True, text=True, cwd=ROOT, timeout=600)
            self.assertEqual(r.returncode, 0, r.stderr[-2000:])
            self.assertIn("PUSH_MIN_SHARE must exceed DUMP_MAX_SHARE", r.stdout)
            with open(out) as fh:
                data = json.load(fh)
            self.assertEqual([c["cell"] for c in data["cells"]], ["off", "on"])
            for c in data["cells"]:
                self.assertEqual(c["params"], dataclasses.asdict(PrPushParams()))
                self.assertEqual(c["errors"], 0)
            self.assertEqual(len(data["skipped"]), 1)


class TestLA20BlueSafe(unittest.TestCase):
    """Spec amendment 1: the push split never blocks fewer Blue than the default split (slack 0)."""

    def setUp(self):
        self.e = _engine()
        self.s = self.e.state
        self.me = self.s.players[0]
        self.bot = AdaptiveBalancedBot(0)

    def _both(self, rem, n, secrets):
        _set(self.s, [10, 10, 10], [secrets, 5, 5])
        self.assertEqual(prp.window(self.bot, self.me, self.s, phase4=True), prp.PUSH)
        out = self.bot.choose_any_shield_allocation(self.me, dict(rem), n, self.s, dict(rem))
        default = validate_any_shield_allocation(
            msp.default_any_shield_allocation(self.me, dict(rem), n, self.s, dict(rem), msp.policy_for(self.bot)),
            dict(rem), n, self.bot.any_shield_fill_order)
        raw_push = msp.default_any_shield_allocation(self.me, dict(rem), n, self.s, dict(rem), prp.PR_PUSH_POLICY)
        push = validate_any_shield_allocation(raw_push, dict(rem), n, prp.PR_PUSH_FILL)
        return out, default, push

    def test_la20_blue_never_below_default(self):
        rng = random.Random(11)
        switched = 0
        for _ in range(300):
            rem = {c: rng.randint(0, 4) for c in (R, B, G)}
            n = rng.randint(0, 6)
            out, default, push = self._both(rem, n, rng.randint(3, 7))
            self.assertGreaterEqual(out.get(B, 0), default.get(B, 0), (rem, n))
            self.assertIn(out, (push, default))
            if push.get(B, 0) < default.get(B, 0):
                switched += 1
                self.assertEqual(out, default)
            else:
                self.assertEqual(out, push)
        self.assertGreater(switched, 0)  # the crafted sample exercises the fallback branch

    def test_la20_slack(self):
        rng = random.Random(11)
        cfg = ON(num_players=3, bot_pr_push_params=PrPushParams(push_blue_slack=1))
        seen = 0
        for _ in range(300):
            rem = {c: rng.randint(0, 4) for c in (R, B, G)}
            n = rng.randint(0, 6)
            sec = rng.randint(3, 7)
            with mock.patch.object(self.s, "config", cfg):
                out, default, push = self._both(rem, n, sec)
            if push.get(B, 0) >= default.get(B, 0) - 1:
                self.assertEqual(out, push)
                if push.get(B, 0) == default.get(B, 0) - 1:
                    seen += 1
            else:
                self.assertEqual(out, default)
        self.assertGreater(seen, 0)

    def test_la20_validation(self):
        self.assertEqual(PrPushParams().push_blue_slack, 0)
        for bad in (-1, 1.5, "1"):
            with self.assertRaises(ValueError):
                PrPushParams(push_blue_slack=bad).validate()
        with self.assertRaises(ValueError):
            GameConfig.v037(bot_pr_push_params=PrPushParams(push_blue_slack=-1))
        with self.assertRaises(ValueError):
            GameConfig.v037(bot_pr_push_scope="reference")
        self.assertEqual(GameConfig.v037().bot_pr_push_scope, "all")


class TestLA21Scope(unittest.TestCase):
    """Spec amendment 3: scope 'non_reference' keeps reference fallback / portfolio / rollouts on old play."""

    def test_la21_flags_and_window(self):
        e = _engine()
        s = e.state
        _set(s, [10, 10, 10])
        ref = rs.ReferenceSearchBot(0, 0)
        owned = [ref.fallback] + [m for _, m in ref.portfolio]
        self.assertTrue(all(getattr(m, "pr_push_reference_owned", False) for m in owned))
        plain = AdaptiveBalancedBot(0)
        nr = ON(num_players=3, bot_pr_push_scope="non_reference")
        self.assertEqual(prp.window(ref.fallback, s.players[0], s), prp.PUSH)  # scope "all": unchanged
        with mock.patch.object(s, "config", nr):
            self.assertEqual(prp.window(plain, s.players[0], s), prp.PUSH)
            self.assertEqual(prp.window(ref.fallback, s.players[0], s), prp.NONE)
            s.pr_push_rollout = True
            try:
                self.assertEqual(prp.window(plain, s.players[0], s), prp.NONE)
            finally:
                del s.pr_push_rollout

    def _ref1(self, cfg, seed=3):
        classes = _bot_classes()
        bots = [classes[(seed + i) % len(classes)](i) for i in range(3)]
        bots[0] = rs.ReferenceSearchBot(0, seed, n_rollouts=2, halving_first=1)
        r = rs.ReferenceSearchEngine(cfg, bots, seed=seed).run_game()
        return r.end_reason, r.total_rounds, list(r.winner_ids), r.rankings

    def test_la21_rollouts_off_in_non_reference(self):
        seen = []
        orig = prp.window

        def spy(bot, player, state, phase4=False, hook=""):
            w = orig(bot, player, state, phase4=phase4, hook=hook)
            if getattr(state, "pr_push_rollout", False) or getattr(bot, "pr_push_reference_owned", False):
                seen.append(w)
            return w

        with mock.patch.object(prp, "window", spy):
            self._ref1(ON(num_players=3, bot_pr_push_scope="non_reference"))
        self.assertTrue(seen)
        self.assertEqual(set(seen), {prp.NONE})

    def test_la21_live_state_unmarked(self):
        classes = _bot_classes()
        bots = [classes[(3 + i) % len(classes)](i) for i in range(3)]
        bots[0] = rs.ReferenceSearchBot(0, 3, n_rollouts=2, halving_first=1)
        e = rs.ReferenceSearchEngine(ON(num_players=3), bots, seed=3)
        e.run_game()
        self.assertGreater(bots[0].stats["rollouts"], 0)
        self.assertFalse(hasattr(e.state, "pr_push_rollout"))

    def test_la21_deterministic(self):
        cfg = lambda: ON(num_players=3, bot_pr_push_scope="non_reference")  # noqa: E731
        self.assertEqual(self._ref1(cfg()), self._ref1(cfg()))


if __name__ == "__main__":
    unittest.main()
