"""v0.52 parity (INV-MS-STACK-00, INV-MS-TEL-01): v051 / v051_roster replay byte-identically against the v0.51 golden
with the v0.52 flags off; Market Share telemetry alone changes nothing."""

import json
import unittest

from tests.parity_v051 import capture as c51
from tests.test_v500_parity import _digest, _run


class TestV051Golden(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(c51.GOLDEN_PATH) as fh:
            cls.golden = json.load(fh)

    def test_ms_par_01_golden_complete(self):
        self.assertEqual(len(self.golden), len(c51.CONFIGS) * len(c51.PLAYERS) * len(c51.SEEDS))

    def test_ms_par_02_v051_replays_golden(self):
        bad = [k for k, v in self.golden.items()
               if c51.digest(k.split("|")[0], int(k.split("|")[1]), int(k.split("|")[2])) != v]
        self.assertEqual(bad, [], f"{len(bad)} parity mismatches, first: {bad[:5]}")

    def test_ms_par_03_telemetry_is_passive(self):
        """INV-MS-TEL-01: v051_roster with ms_tie_telemetry=True digests like the golden."""
        bad = []
        for players in (2, 3, 4):
            for seed in range(42, 62):
                d = _digest(_run("v051_roster", players, seed, ms_tie_telemetry=True))
                if d != self.golden[f"v051_roster|{players}|{seed}"]:
                    bad.append((players, seed))
        self.assertEqual(bad, [])

    def test_ms_par_04_stack_setup_inert_when_off(self):
        for seed in range(42, 52):
            d = _digest(_run("v051_roster", 3, seed, market_share_stack_setup="FIRST_SEAT_TOP"))
            self.assertEqual(d, self.golden[f"v051_roster|3|{seed}"], seed)


if __name__ == "__main__":
    unittest.main()
