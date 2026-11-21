"""v0.51 parity (INV-LAND-00): v050 / v050_roster replay byte-identically against the v0.50 golden;
the v0.51 flags at their v0.50 values (or each rule alone) change nothing."""

import dataclasses
import json
import unittest

from sim.config import GameConfig
from tests.parity_v050 import capture as c50
from tests.test_v500_parity import _digest, _run


def _key(r):
    return (r.end_reason, r.total_rounds, sorted(r.winner_ids), [(x["player_id"], x["secrets"]) for x in r.rankings])


class TestV050Golden(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(c50.GOLDEN_PATH) as fh:
            cls.golden = json.load(fh)

    def test_tc_land_01_golden_complete(self):
        self.assertEqual(len(self.golden), len(c50.CONFIGS) * len(c50.PLAYERS) * len(c50.SEEDS))

    def test_tc_land_01_v050_replays_golden(self):
        bad = [k for k, v in self.golden.items()
               if c50.digest(k.split("|")[0], int(k.split("|")[1]), int(k.split("|")[2])) != v]
        self.assertEqual(bad, [], f"{len(bad)} parity mismatches, first: {bad[:5]}")

    def test_tc_land_02_preset_fields(self):
        new = {"vuln_hit_landing_by_band", "vuln_one_hit_per_round"}
        for p in (2, 3, 4):
            for a, b in (("v051", "v050"), ("v051_roster", "v050_roster")):
                x, y = getattr(GameConfig, a)(num_players=p), getattr(GameConfig, b)(num_players=p)
                diff = {f.name for f in dataclasses.fields(GameConfig) if getattr(x, f.name) != getattr(y, f.name)}
                self.assertEqual(diff, new, (a, p))

    def test_tc_land_03_neutral(self):
        bad = []
        for players in (2, 3, 4):
            for seed in range(42, 72):
                d = _digest(_run("v051_roster", players, seed, vuln_hit_landing_by_band=None, vuln_one_hit_per_round=False))
                if d != self.golden[f"v050_roster|{players}|{seed}"]:
                    bad.append((players, seed))
        self.assertEqual(bad, [])

    def test_tc_land_03b_each_rule_alone_inert(self):
        for seed in range(42, 72):
            base = _key(_run("v050_roster", 3, seed))
            self.assertEqual(_key(_run("v050_roster", 3, seed, vuln_one_hit_per_round=True)), base, seed)
            self.assertEqual(_key(_run("v050_roster", 3, seed, vuln_hit_landing_by_band=(0, 0, 0))), base, seed)


if __name__ == "__main__":
    unittest.main()
