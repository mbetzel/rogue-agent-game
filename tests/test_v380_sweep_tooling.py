"""Sweep tooling for Phase 49: scripts/run_v380_secret_faces_sweep.py (roster, baselines, per-game records,
--procs determinism) and scripts/run_reference_bot_validation.py --out-dir."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from unittest import mock

from scripts import run_v380_secret_faces_sweep as sw
from sim.bots.mixed_policy import MixedPolicyBot


class TestSweep(unittest.TestCase):
    def test_mixed_seat_default_and_rotation(self):
        for seed in range(6):
            eng = sw.build_engine("v038_roster", "mixed1", 3, seed, {})
            mixed = [p.player_id for p in eng.state.players if isinstance(p.bot, MixedPolicyBot)]
            self.assertEqual(mixed, [seed % 3])
            eng = sw.build_engine("v038_roster", "archetypes", 3, seed, {})
            self.assertFalse(any(isinstance(p.bot, MixedPolicyBot) for p in eng.state.players))
        self.assertEqual(sw.run("v038", 3, 2, {})["roster"], "mixed1")

    def test_archetypes_roster_matches_parity_setup(self):
        from sim.config import GameConfig
        from tests.fixtures.v035_parity.capture import build_engine

        for seed in range(3):
            a = sw.build_engine("v038", "archetypes", 3, seed, {}).run_game()
            b = build_engine(GameConfig.v038, "setup", 3, seed).run_game()
            self.assertEqual(a.rankings, b.rankings)

    def test_record_fields_and_baselines(self):
        for cfg in sw.CONFIGS:
            rec = sw.play((cfg, "mixed1", 3, 1, {}))
            for k in ("seed", "end_reason", "rounds", "final_market_share", "cube_exits", "winner_archetypes",
                      "winner_company_colors", "winner_paths", "seats"):
                self.assertIn(k, rec, (cfg, k))
            self.assertEqual(len(rec["final_market_share"]), 3)
            self.assertEqual(set(rec["cube_exits"]), {"red", "blue", "green"})
            self.assertTrue(all(c in ("red", "blue", "green", "none") for c in rec["winner_company_colors"]))
        rec = sw.play(("v038", "mixed1", 3, 2, {"max_rounds": 1}))
        self.assertEqual(rec["end_reason"], "round_limit")
        s = sw.summarise([rec], "v038", "mixed1", 3, {})
        self.assertEqual(s["outliers"]["round_limit"], [2])

    def test_procs_determinism(self):
        a = sw.play_all("v038_roster", "mixed1", 3, 12, {}, 0, procs=1)
        b = sw.play_all("v038_roster", "mixed1", 3, 12, {}, 0, procs=3)
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))
        self.assertEqual([r["seed"] for r in b], list(range(12)))

    def test_cli_out(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "sub", "s.json")
            with mock.patch("sys.stdout"):
                sw.main(["--games", "3", "--players", "2", "--procs", "2", "--out", path])
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(len(data[0]["records"]), 3)
            with self.assertRaises(FileExistsError), mock.patch("sys.stdout"):
                sw.main(["--games", "3", "--players", "2", "--out", path])


class TestOverrides(unittest.TestCase):
    def test_dict_keys_and_tuples_coerced(self):
        ov = sw._parse_overrides(['starting_secrets_by_player_count={"2":4,"3":4,"4":6}',
                                  'secret_yield_red_tiers=[[10,3],[5,2],[1,1],[0,0]]',
                                  'market_leader_bonus_by_player_count={"3":[3,1,0]}'])
        self.assertEqual(ov["starting_secrets_by_player_count"], {2: 4, 3: 4, 4: 6})
        self.assertEqual(ov["secret_yield_red_tiers"], ((10, 3), (5, 2), (1, 1), (0, 0)))
        self.assertEqual(ov["market_leader_bonus_by_player_count"], {3: (3, 1, 0)})
        rec = sw.build_engine("v038_roster", "mixed1", 3, 0, ov)
        self.assertEqual(rec.config.get_starting_secrets(), 4)
        sw.check_overrides_effective("v038_roster", "mixed1", 3, {"starting_secrets_by_player_count": {3: 4}})

    def test_unknown_inert_and_noop_fail_loudly(self):
        for bad in ("no_such_field=1", 'corruption_track_capacity_by_player_count={"3":3}', "max_rounds"):
            with self.assertRaises(sw.OverrideError, msg=bad):
                sw._parse_overrides([bad])
        with self.assertRaises(sw.OverrideError):  # equals the default
            sw.check_overrides_effective("v038_roster", "mixed1", 3, {"max_rounds": 30})
        with self.assertRaises(sw.OverrideError):  # changes the config but never the games
            sw.check_overrides_effective("v038_roster", "mixed1", 3, {"cipher_market_discount": 2, "max_rounds": 31})
        with self.assertRaises(sw.OverrideError), mock.patch("sys.stdout"):
            sw.main(["--games", "1", "--set", 'corruption_track_capacity_by_player_count={"3":3}'])


class TestValidationOutDir(unittest.TestCase):
    def test_out_dir(self):
        from scripts import run_reference_bot_validation as v

        self.assertTrue(v.OUT.endswith(os.path.join("sim_results", "reference_bot")))
        with tempfile.TemporaryDirectory() as d:
            target = os.path.join(d, v.output_name("v037", "ref1", 3, 1, True, None, "non_reference"))
            open(target, "w").close()
            with self.assertRaises(FileExistsError):  # guard reads --out-dir, not the default
                v.main(["--config", "v037", "--cells", "ref1", "--games", "1", "--out-dir", d])
            self.assertEqual(os.path.getsize(target), 0)


if __name__ == "__main__":
    unittest.main()
