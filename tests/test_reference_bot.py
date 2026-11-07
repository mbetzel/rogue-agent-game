"""Reference bot (Tier 1 Mixed + Tier 2 Search) tests RB-01..RB-17 (docs/specs/reference_bot_spec.md §12)."""

from __future__ import annotations

import copy
import json
import os
import random
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from sim.config import CubeColor, GameConfig
from sim.engine import GameEngine, fast_clone
from sim.engine.phase6_operations import resolve_operations_plan
from sim.bots import AdaptiveBalancedBot
from sim.bots.base import BaseBot
from sim.bots.mixed_policy import DEFAULT_POOL, MixedPolicyBot, post_process_operations_plan, raw_operations_plan
from sim.bots import reference_search as rs
from sim.bots.reference_search import (
    ForcedChoiceBot, ReferenceSearchBot, ReferenceSearchEngine, rollout_value,
)
from tests.fixtures.v035_parity.capture import _bot_classes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V036 = GameConfig.v036


def _build(scenario, n, seed, engine_cls=GameEngine):
    """``tests/fixtures/v035_parity/capture.build_engine`` with a selectable engine class."""
    from tests.fixtures.v035_parity import capture

    with mock.patch("sim.engine.GameEngine", engine_cls):
        return capture.build_engine(V036, scenario, n, seed)


def _summary(res):
    return (res.end_reason, res.total_rounds, list(res.winner_ids),
            [{k: r.get(k) for k in ("player_id", "secrets", "money", "market_share", "is_patient_zero", "net_score")}
             for r in res.rankings])


def _p4_rows(engine):
    return [[[s["money"], s["secrets"], s.get("market_share")] for s in t.phase_snapshots.get(4, [])]
            for t in engine.telemetry_history]


class SnapAtEngine(ReferenceSearchEngine):
    """Always snapshots; keeps the snapshot of (round, phase) == ``self.want``."""

    want = (3, 4)
    kept = None

    def _needs_snapshot(self):
        return True

    def _take_snapshot(self, phase, commitments=None, cr=None):
        super()._take_snapshot(phase, commitments, cr)
        if (self.state.current_round, phase) == self.want:
            self.kept = self._snap


def _ref_game(n, seed, cls=ReferenceSearchEngine, **bot_kw):
    classes = _bot_classes()
    bots = [classes[(seed + i) % len(classes)](i) for i in range(n)]
    seat = seed % n
    bots[seat] = ReferenceSearchBot(seat, seed, **bot_kw)
    return cls(V036(num_players=n), bots, seed=seed), bots[seat]


class TestFastClone(unittest.TestCase):
    def _mid_game(self, scenario="setup", n=3, seed=4, rounds=3):
        e = _build(scenario, n, seed)
        for _ in range(rounds):
            if not e.state.game_over:
                e.run_round()
        return e

    def test_rb01_independence(self):
        e = self._mid_game()
        before = copy.deepcopy(e)
        c, _ = fast_clone.clone_engine(e)
        self.assertIs(c.rng, c.state.rng)
        self.assertIsNot(c.rng, e.rng)
        for p in c.state.players:
            p.money += 7
            p.secrets -= 3
            for lst in (p.ready_for_release_dice, p.in_production_dice, p.glitched_dice, p.scanned_dice,
                        p.contractor_dice):
                for d in lst:
                    d.is_locked = not d.is_locked
                    d.current_face = None
                lst.clear()
            for k, v in list(vars(p).items()):
                if isinstance(v, dict):
                    v["__x"] = 1
                elif isinstance(v, list):
                    v.append("__x")
                elif isinstance(v, set):
                    v.add("__x")
        s = c.state
        s.tower.stuck_cubes[CubeColor.RED] += 9
        s.staging_cup[CubeColor.BLUE] += 9
        for k in list(s.market):
            s.market[k] += 9
        s.pending_next_phase_locks.add("__x")
        s.active_phase1_locks.add("__x")
        s.version_comparisons_done.add("__x")
        s.end_triggers.append("__x")
        c.rng.random()
        self.assertEqual(e.rng.getstate(), before.rng.getstate())
        for p, q in zip(e.state.players, before.state.players):
            self.assertEqual(p.money, q.money)
            self.assertEqual(p.secrets, q.secrets)
            for z in ("ready_for_release_dice", "in_production_dice", "glitched_dice", "scanned_dice", "contractor_dice"):
                self.assertEqual([(d.die_id, d.is_locked, d.current_face) for d in getattr(p, z)],
                                 [(d.die_id, d.is_locked, d.current_face) for d in getattr(q, z)])
            for k, v in vars(p).items():
                if isinstance(v, (dict, list, set)):
                    self.assertNotIn("__x", v, k)
        self.assertEqual(e.state.tower.stuck_cubes, before.state.tower.stuck_cubes)
        self.assertEqual(e.state.staging_cup, before.state.staging_cup)
        self.assertEqual(e.state.market, before.state.market)
        self.assertEqual(e.state.end_triggers, before.state.end_triggers)
        self.assertNotIn("__x", e.state.pending_next_phase_locks | e.state.active_phase1_locks
                         | e.state.version_comparisons_done)

    def test_rb02_parity_vs_deepcopy(self):
        for scenario in ("mixed", "setup"):
            for n in (2, 3, 4):
                for seed in range(100):
                    ctl = _build(scenario, n, seed).run_game()
                    e = _build(scenario, n, seed)
                    for target in (1, 3, 5):
                        while not e.state.game_over and e.state.current_round < target:
                            e.run_round()
                        if e.state.game_over:
                            break
                        a = copy.deepcopy(e)
                        b, _ = fast_clone.clone_engine(e)
                        s = zlib_seed(scenario, n, seed, target)
                        a.rng.seed(s)
                        b.rng.seed(s)
                        ra, rb = a.run_game(), b.run_game()
                        msg = f"{scenario} {n}P seed {seed} r{target}"
                        self.assertEqual(_summary(ra), _summary(rb), msg)
                        self.assertEqual(_p4_rows(a), _p4_rows(b), msg)
                    if not e.state.game_over:
                        self.assertEqual(_summary(e.run_game()), _summary(ctl), "original perturbed")

    def test_rb07_replay_reproduces_real_game(self):
        for n in (2, 3, 4):
            for seed in range(100):
                for phase in (1, 4, 6):
                    cls = type("E", (SnapAtEngine,), {"want": (2 + seed % 3, phase)})
                    e = _build("mixed", n, seed, engine_cls=cls)
                    real = e.run_game()
                    if e.kept is None:
                        continue
                    c, com, cr = fast_clone.from_snapshot(e.kept)
                    fast_clone.resume_round(c, phase, com, cr)
                    got = c.run_game() if not c.state.game_over else c.evaluate_end_game()
                    self.assertEqual(_summary(got), _summary(real), f"{n}P seed {seed} phase {phase}")


def zlib_seed(*parts):
    import zlib

    return zlib.crc32("|".join(map(str, parts)).encode())


class TestMixed(unittest.TestCase):
    def test_rb03_draws_pure_and_rng_untouched(self):
        a, b = MixedPolicyBot(1, 77), MixedPolicyBot(1, 77)
        for dt in ("phase1_roll", "phase1_deploy", "phase2", "phase4", "phase6", "misc"):
            self.assertIs(type(a._draw(dt, 0)), type(b._draw(dt, 0)))
        seen = {type(MixedPolicyBot(0, s)._draw("phase6", 0)) for s in range(200)}
        self.assertEqual(seen, set(DEFAULT_POOL))
        # rng trajectory: Mixed seat vs a bot replaying its delegate choices through a fixed table
        for n in (2, 3, 4):
            for seed in range(10):
                seat = seed % n

                def run(make):
                    classes = _bot_classes()
                    bots = [classes[(seed + i) % 5](i) for i in range(n)]
                    bots[seat] = make()
                    e = GameEngine(V036(num_players=n), bots, seed=seed)
                    traj = []
                    while not e.state.game_over:
                        e.run_round()
                        traj.append(e.rng.getstate())
                    return traj, _summary(e.evaluate_end_game())

                mixed = MixedPolicyBot(seat, seed)
                table = {dt: mixed._draw(dt, 0) for dt in
                         ("phase1_roll", "phase1_deploy", "phase2", "phase4", "phase6", "misc")}

                class Replay(MixedPolicyBot):
                    def _draw(self, dtype, round_no):
                        return self._table[dtype]

                def make_replay():
                    r = Replay(seat, 0)
                    r._table = {k: v for k, v in table.items()}
                    return r

                self.assertEqual(run(lambda: MixedPolicyBot(seat, seed)), run(make_replay), f"{n}P {seed}")

    def test_rb03_round_granularity(self):
        m = MixedPolicyBot(0, 5, granularity="round")
        draws = {type(m._draw("phase4", r)) for r in range(1, 40)}
        self.assertGreater(len(draws), 1)
        with self.assertRaises(ValueError):
            MixedPolicyBot(0, 5, granularity="turn")

    def test_rb04_mirroring(self):
        checked = 0
        for seed in range(80):
            if checked >= 200:
                break
            n = 2 + seed % 3
            cls = type("E", (SnapAtEngine,), {"want": (2 + seed % 4, 6)})
            classes = _bot_classes()
            bots = [classes[(seed + i) % 5](i) for i in range(n)]
            bots[0] = MixedPolicyBot(0, seed)
            e = cls(V036(num_players=n), bots, seed=seed)
            e.run_game()
            if e.kept is None:
                continue
            se = e.kept.engine
            for p in se.state.players:
                if p.is_patient_zero:
                    continue
                st = se.state
                if isinstance(p.bot, MixedPolicyBot):
                    delegate = p.bot._draw("phase6", 0)
                    self.assertEqual(resolve_operations_plan(p.bot, p, st, random.Random(1)),
                                     resolve_operations_plan(delegate, p, st, random.Random(1)))
                rb = ReferenceSearchBot(p.player_id, seed)
                for label, key, rec in rb.generate_candidates("take_operations_actions",
                                                              {"player_state": p, "game_state": st}):
                    raw, prof = rec
                    forced = ForcedChoiceBot(rb, [("take_operations_actions", rec)], None, se)
                    self.assertEqual(resolve_operations_plan(forced, p, st, random.Random(1)),
                                     post_process_operations_plan(
                                         dict(rb.portfolio + [("fallback", rb.fallback)])[label], copy.deepcopy(raw),
                                         p, st, random.Random(1)), label)
                    forced2 = ForcedChoiceBot(rb, [("take_operations_actions", rec)], None, se)
                    self.assertEqual(rs.plan_key(resolve_operations_plan(forced2, p, st, random.Random(1))), key)
                for label, member in rb.portfolio:
                    self.assertEqual(
                        post_process_operations_plan(member, raw_operations_plan(member, p, st, random.Random(1)),
                                                     p, st, random.Random(1)),
                        resolve_operations_plan(member, p, st, random.Random(1)), label)
                checked += 1
        self.assertGreaterEqual(checked, 200)

    def test_rb11_v036_parity(self):
        from tests.fixtures.v036_parity import capture

        for scenario in capture.SCENARIOS:
            for n in capture.PLAYER_COUNTS:
                with open(capture.fixture_path(scenario, n), encoding="utf-8") as fh:
                    golden = json.load(fh)
                for seed in capture.SEEDS[:100]:
                    got = json.loads(json.dumps(capture.run_scenario(V036, scenario, n, seed), sort_keys=True))
                    self.assertEqual(got, golden[str(seed)], f"{scenario} {n}P {seed}")
        # a ReferenceSearchEngine without a reference seat is a GameEngine (no snapshots, same game)
        for seed in range(20):
            a = _build("mixed", 3, seed).run_game()
            b = _build("mixed", 3, seed, engine_cls=ReferenceSearchEngine).run_game()
            self.assertEqual(_summary(a), _summary(b))


class TestSearch(unittest.TestCase):
    def test_rb05_candidate_generation_keeps_rng(self):
        member = AdaptiveBalancedBot(0)
        member.research_focus_mode = "random"
        rb = ReferenceSearchBot(0, 3, portfolio=[("random", member)])
        self.assertEqual(member.research_focus_mode, "fixed")
        e, bot = _ref_game(3, 3)
        calls = []
        orig = ReferenceSearchBot.generate_candidates

        def spy(self, hook, kwargs):
            g0 = self.engine.rng.getstate()
            out = orig(self, hook, kwargs)
            calls.append(self.engine.rng.getstate() == g0)
            return out

        with mock.patch.object(ReferenceSearchBot, "generate_candidates", spy):
            e.run_game()
        self.assertTrue(calls and all(calls))

    def test_rb06_anti_clairvoyance(self):
        captured = []
        orig = ForcedChoiceBot._forced

        def spy(self, hook, kwargs):
            out = orig(self, hook, kwargs)
            if self.reseeded and not getattr(self, "_cap", False):
                self._cap = True
                captured.append((self.target[3], self.engine.rng.getstate()))
            return out

        with mock.patch.object(ForcedChoiceBot, "_forced", spy):
            e, bot = _ref_game(3, 1)
            e.run_game()
        self.assertTrue(captured)
        for seed, state in captured:
            self.assertEqual(state, random.Random(seed).getstate())
        # next-round Phase 1 faces in a rollout differ from the real game's
        diffs = 0
        trials = 0
        for seed in range(6):
            cls = type("E", (SnapAtEngine,), {"want": (2, 6)})
            e, bot = _ref_game(3, seed, cls=cls)
            nxt = {}

            orig_p1 = cls._execute_phase_1

            def p1(self):
                out = orig_p1(self)
                if self.state.current_round == 3:
                    nxt["real"] = [(p.player_id, [d.current_face for d in dice]) for p, dice, _ in out]
                return out

            with mock.patch.object(cls, "_execute_phase_1", p1):
                e.run_game()
            if e.kept is None or "real" not in nxt:
                continue
            c, com, cr = fast_clone.from_snapshot(e.kept)
            for p in c.state.players:
                if isinstance(p.bot, ReferenceSearchBot):
                    p.bot = ForcedChoiceBot(p.bot, [], (0, "take_operations_actions",
                                                        rs._candidate("take_operations_actions", p.bot.fallback,
                                                                      {"player_state": p, "game_state": c.state},
                                                                      random.Random(0))[1], 12345), c)
            fast_clone.resume_round(c, 6)
            if c.state.game_over:
                continue
            out = c._execute_phase_1()
            trials += 1
            diffs += [(p.player_id, [d.current_face for d in dice]) for p, dice, _ in out] != nxt["real"]
        self.assertGreater(trials, 0)
        self.assertEqual(diffs, trials)

    def test_rb08_crn_and_rb09_nesting(self):
        e, bot = _ref_game(3, 1)
        bot.rollout_trace = []
        nested = []
        orig_resume = fast_clone.resume_round

        def resume(engine, phase, commitments=None, cr=None):
            nested.append(any(isinstance(p.bot, ReferenceSearchBot) for p in engine.state.players))
            self.assertIs(type(engine), GameEngine)
            return orig_resume(engine, phase, commitments, cr)

        entries = []
        orig_searched = ReferenceSearchBot._searched

        def searched(self_, hook, kwargs):
            entries.append(hook)
            return orig_searched(self_, hook, kwargs)

        with mock.patch.object(fast_clone, "resume_round", resume), \
                mock.patch.object(ReferenceSearchBot, "_searched", searched):
            e.run_game()
        self.assertTrue(nested)
        self.assertFalse(any(nested))  # INV-REF-NEST-01
        self.assertEqual(len(entries), bot.stats["search_entries"])  # one entry per real decision, none nested
        by_dec = {}
        for dec, cand, seed in bot.rollout_trace:
            by_dec.setdefault(dec, {}).setdefault(cand, []).append(seed)
        self.assertTrue(by_dec)
        for dec, per in by_dec.items():
            longest = max(per.values(), key=len)
            for cand, seeds in per.items():
                self.assertEqual(seeds, longest[:len(seeds)], f"decision {dec}")  # INV-REF-CRN-01

    def test_rb10_determinism(self):
        e1, _ = _ref_game(2, 4)
        e2, _ = _ref_game(2, 4)
        self.assertEqual(_summary(e1.run_game()), _summary(e2.run_game()))
        code = ("import json,sys; sys.path.insert(0,%r); from scripts.run_reference_bot_check import play; "
                "rows=[play((c,2,s)) for c in ('ref1','mixed1') for s in range(20)]; "
                "[r.pop('ms') for r in rows]; print(json.dumps(rows, sort_keys=True))") % ROOT
        outs = []
        for h in ("1", "2"):
            env = dict(os.environ, PYTHONHASHSEED=h)
            outs.append(subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env, capture_output=True,
                                       text=True, check=True).stdout)
        self.assertEqual(outs[0], outs[1])

    def _fake(self, n_cands):
        rb = ReferenceSearchBot(0, 1)
        rb.engine = mock.Mock()
        rb.engine.state.current_round = 1
        cands = [(f"c{i}", i, {CubeColor.RED: i}) for i in range(n_cands)]
        calls = []

        def rollout(hook, idx, rec, seed):
            calls.append((rec[CubeColor.RED], seed))
            return float(rec[CubeColor.RED] % 4)

        rb.rollout = rollout
        return rb, cands, calls

    def test_rb12_single_candidate_no_rollouts(self):
        e, bot = _ref_game(3, 2)
        with mock.patch.object(ReferenceSearchBot, "generate_candidates",
                               lambda self, hook, kw: [orig_gen(self, hook, kw)[0]]), \
                mock.patch.object(ReferenceSearchBot, "rollout", side_effect=AssertionError("rollout ran")):
            e.run_game()
        self.assertEqual(bot.stats["rollouts"], 0)
        self.assertEqual(bot.stats["searched"], 0)
        self.assertGreater(bot.stats["search_entries"], 0)

    def test_rb13_successive_halving(self):
        rb, cands, calls = self._fake(6)
        best = rb._search("choose_any_shield_allocation", cands)
        self.assertEqual(len(calls), 6 * 4 + 3 * 4)
        per = {}
        for c, s in calls:
            per.setdefault(c, []).append(s)
        self.assertEqual(sorted(len(v) for v in per.values()), [4, 4, 4, 8, 8, 8])
        self.assertEqual(best, 3)  # value c % 4: 3 is best
        rb, cands, calls = self._fake(2)
        rb._search("choose_any_shield_allocation", cands)
        self.assertEqual(len(calls), 16)

    def test_rb14_value(self):
        from types import SimpleNamespace as NS

        def res(rows, winners):
            return NS(rankings=[{"player_id": i, "secrets": s, "is_patient_zero": pz} for i, (s, pz) in enumerate(rows)],
                      winner_ids=winners)

        self.assertEqual(rollout_value(res([(0, True), (5, False)], [1]), 0), rs.PZ_PENALTY)
        self.assertEqual(rollout_value(res([(9, False), (5, False), (2, True)], [0]), 0), 4 + rs.WIN_BONUS)
        self.assertEqual(rollout_value(res([(5, False), (5, False)], [0, 1]), 0), rs.WIN_BONUS / 2)
        self.assertEqual(rollout_value(res([(5, False), (9, True)], [0]), 0), 5 + rs.WIN_BONUS)
        wipe = res([(-1, True), (-3, True)], [0])
        self.assertEqual(rollout_value(wipe, 0), rs.PZ_PENALTY)
        rb, cands, calls = self._fake(4)
        rb.rollout = lambda *a: rs.PZ_PENALTY
        self.assertEqual(rb._search("choose_any_shield_allocation", cands), 0)  # tie -> portfolio order

    def test_rb15_legal_generic_split(self):
        from sim.engine.state import PlayerState

        e, bot = _ref_game(3, 0)
        legal = []
        orig = ReferenceSearchBot.choose_any_shield_allocation

        def spy(self, player_state, remaining, available_any, game_state, attack):
            out = orig(self, player_state, dict(remaining), available_any, game_state, attack)
            legal.append((out, dict(remaining), available_any))
            return out

        for seed in range(12):
            e, bot = _ref_game(3, seed)
            with mock.patch.object(ReferenceSearchBot, "choose_any_shield_allocation", spy):
                e.run_game()
        self.assertTrue(legal)
        for out, rem, avail in legal:
            self.assertEqual(sum(out.values()), min(avail, sum(rem.values())))
            for c in (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN):
                self.assertLessEqual(out[c], rem.get(c, 0))

    def test_rb16_runner_smoke(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run([sys.executable, "scripts/run_reference_bot_check.py", "--smoke", "--procs", "8",
                            "--out-dir", d], cwd=ROOT, check=True, capture_output=True)
            for cell in ("baseline", "mixed1", "ref1", "ref_all"):
                for n in (2, 3, 4):
                    with open(os.path.join(d, f"reference_bot_{cell}_{n}p.json"), encoding="utf-8") as fh:
                        self.assertEqual(json.load(fh)["summary"]["games"], 20)


orig_gen = ReferenceSearchBot.generate_candidates


class TestFollowUps(unittest.TestCase):
    def _first_search(self, seed, probe):
        """Runs a ref game; on the first real search calls ``probe(bot, hook, cands)`` instead of searching."""
        e, bot = _ref_game(3, seed)
        out = []

        def search(self_, hook, cands):
            if not out:
                out.append(probe(self_, hook, cands))
            return 0

        with mock.patch.object(ReferenceSearchBot, "_search", search):
            e.run_game()
        self.assertTrue(out)
        return out[0]

    def test_rb18_missed_forced_decision_raises(self):
        def probe(bot, hook, cands):
            with self.assertRaisesRegex(RuntimeError, "never reached the forced"):
                bot.rollout(hook, 999, cands[1][2], 1)  # target call index the clone never reaches
            return True

        self.assertTrue(self._first_search(1, probe))

    def test_rb18_shared_bots_unchanged_by_rollout(self):
        def probe(bot, hook, cands):
            shared = [p.bot for p in bot.engine.state.players if not isinstance(p.bot, ReferenceSearchBot)]
            shared.append(bot.fallback)
            before = [copy.deepcopy(vars(b)) for b in shared]
            for c in range(len(cands)):
                bot.rollout(hook, len(bot.phase_log), cands[c][2], 7 + c)
            for b, d in zip(shared, before):
                self.assertEqual(vars(b), d, type(b).__name__)
            return True

        self.assertTrue(self._first_search(1, probe))
        # also with a Mixed opponent seat
        classes = _bot_classes()
        bots = [classes[i](i) for i in range(3)]
        bots[0] = ReferenceSearchBot(0, 2)
        bots[1] = MixedPolicyBot(1, 2)
        e = ReferenceSearchEngine(V036(num_players=3), bots, seed=2)
        seen = []

        def search(self_, hook, cands):
            if not seen:
                before = copy.deepcopy({k: v for k, v in vars(bots[1]).items() if k not in ("draw_log", "pool", "engine")})
                pool_before = [copy.deepcopy(vars(m)) for m in bots[1].pool]
                self_.rollout(hook, len(self_.phase_log), cands[-1][2], 3)
                self.assertEqual({k: v for k, v in vars(bots[1]).items() if k not in ("draw_log", "pool", "engine")}, before)
                self.assertEqual([vars(m) for m in bots[1].pool], pool_before)
                seen.append(1)
            return 0

        with mock.patch.object(ReferenceSearchBot, "_search", search):
            e.run_game()
        self.assertTrue(seen)


class TestCleanup(unittest.TestCase):
    REMOVED = ("choose_debug_unlocks", "choose_hotfix_rerolls", "choose_fast_patches", "choose_glitch_demotion",
               "choose_shield_wear_order", "choose_b3_sacrificial_die", "choose_prometheus_override",
               "choose_acoustic_ability", "choose_spook_ability")
    KEPT = ("choose_yahtzee_rerolls", "choose_operator_ability", "choose_prodigy_ability", "take_phase3_actions",
            "choose_aegis_override", "choose_dto_override")

    def test_rb17_cleanup(self):
        for cls in (BaseBot,) + tuple(DEFAULT_POOL):
            for m in self.REMOVED:
                self.assertFalse(hasattr(cls, m), f"{cls.__name__}.{m}")
            for m in self.KEPT:
                self.assertTrue(callable(getattr(cls, m, None)), f"{cls.__name__}.{m}")
        from tests.fixtures.v035_parity import capture as c35
        from tests.fixtures.v033_parity import capture as c33

        for cap, factory, scen in ((c35, GameConfig.legacy_v035, c35.SCENARIOS),):
            for scenario in scen:
                for n in cap.PLAYER_COUNTS:
                    with open(cap.fixture_path(scenario, n), encoding="utf-8") as fh:
                        golden = json.load(fh)
                    for seed in cap.SEEDS[:30]:
                        got = json.loads(json.dumps(cap.run_scenario(factory, scenario, n, seed), sort_keys=True))
                        self.assertEqual(got, golden[str(seed)])
        self.assertTrue(os.path.exists(c33.fixture_path("mixed", 2)))  # full v033 replay: test_v350 / test_v360


if __name__ == "__main__":
    unittest.main()
