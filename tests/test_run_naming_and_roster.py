"""FINDINGS §41 follow-ups: override-aware output names, overwrite refusal, roster helper."""
from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from unittest import mock

from sim.config import GameConfig, PrPushParams
from sim.run_naming import OutputExistsError, guard_overwrite, overrides_tag

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, "scripts", name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestOverridesTag(unittest.TestCase):
    def test_sorted_stable_readable(self):
        self.assertEqual(overrides_tag({"push_top_gap": 3, "push_low_gap": 9}), "push_low_gap=9,push_top_gap=3")
        self.assertEqual(overrides_tag({"push_low_gap": 9, "push_top_gap": 3}),
                         overrides_tag({"push_top_gap": 3, "push_low_gap": 9}))
        self.assertEqual(overrides_tag(None), "")

    def test_long_falls_back_to_sha1(self):
        ov = {"dump_condition": "reach_or_threat", "dump_top_gap": 2, "dump_threat_margin": 3}
        t = overrides_tag(ov)
        self.assertRegex(t, r"^h-[0-9a-f]{8}$")
        self.assertEqual(t, overrides_tag(dict(reversed(list(ov.items())))))
        self.assertNotEqual(t, overrides_tag({**ov, "dump_top_gap": 1}))

    def test_guard(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.json")
            guard_overwrite(p, False)
            open(p, "w").close()
            with self.assertRaises(OutputExistsError):
                guard_overwrite(p, False)
            guard_overwrite(p, True)


class TestValidationScript(unittest.TestCase):
    def setUp(self):
        self.m = _load("run_reference_bot_validation")

    def test_distinct_overrides_distinct_names(self):
        n = lambda ov, scope="non_reference": self.m.output_name("v037", "ref1", 3, 1200, True, ov, scope)  # noqa
        names = {n(None), n({"push_low_gap": 9}), n({"push_low_gap": 7}), n({"push_top_gap": 3}),
                 n(None, "all"), self.m.output_name("v037", "ref1", 3, 1200, False, None, "all")}
        self.assertEqual(len(names), 6)
        self.assertEqual(n(None), "v037_push_nonref_ref1_3p_1200.json")
        self.assertEqual(n({"push_low_gap": 9}), "v037_push_p-push_low_gap=9_nonref_ref1_3p_1200.json")

    def test_defaults_and_refusal(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(self.m, "OUT", d):
            target = os.path.join(d, "v037_push_nonref_ref1_3p_1.json")
            open(target, "w").close()
            with self.assertRaises(OutputExistsError):
                self.m.main(["--config", "v037", "--cells", "ref1", "--games", "1"])
            self.assertEqual(os.path.getsize(target), 0)

    def test_make_config_pins_push(self):
        self.assertFalse(self.m.make_config("v037", 3, False).bot_pr_push)
        self.assertTrue(self.m.make_config("v037", 3, True).bot_pr_push)


class TestSweepScript(unittest.TestCase):
    def setUp(self):
        self.m = _load("run_lever_a_sweep")

    def test_names(self):
        self.assertEqual(self.m.output_name(3, 600), "sweep_3p_600.json")
        names = {self.m.output_name(3, 600), self.m.output_name(3, 600, "non_reference"),
                 self.m.output_name(3, 600, cells="on"), self.m.output_name(3, 600, cells='{"push_low_gap": 9}'),
                 self.m.output_name(3, 600, cells='{"push_low_gap": 7}'), self.m.output_name(3, 600, pr_push=False)}
        self.assertEqual(len(names), 6)

    def test_refusal(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "o.json")
            open(p, "w").close()
            with self.assertRaises(OutputExistsError):
                self.m.main(["--games", "1", "--cells", "off", "--procs", "1", "--out", p])


class TestRosterHelper(unittest.TestCase):
    def test_roster(self):
        c = GameConfig.v037_roster(num_players=3)
        self.assertTrue(c.bot_pr_push)
        self.assertEqual(c.bot_pr_push_params, PrPushParams())
        self.assertEqual(c.bot_pr_push_scope, "all")
        base = GameConfig.v037(num_players=3)
        self.assertFalse(base.bot_pr_push)
        self.assertEqual(c.market_leader_bonus_by_player_count, base.market_leader_bonus_by_player_count)
        self.assertFalse(GameConfig.v037_roster(bot_pr_push=False).bot_pr_push)
        self.assertEqual(GameConfig.v037_roster(bot_pr_push_scope="non_reference").bot_pr_push_scope, "non_reference")

    def test_default_stays_off(self):
        self.assertFalse(GameConfig().bot_pr_push)
        self.assertFalse(GameConfig.legacy_v036().bot_pr_push)
