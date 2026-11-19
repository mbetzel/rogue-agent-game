"""INV-LOCK-07: v0.46 presets replay byte-identically against the golden captured before any v0.47 change."""

import json
import unittest

from sim.config import GameConfig
from tests.parity_v046_mixed.capture import GOLDEN_PATH, digest, digest_for_key, keys


class TestV046Parity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(GOLDEN_PATH) as fh:
            cls.golden = json.load(fh)

    def test_golden_complete(self):
        self.assertEqual(set(self.golden), set(keys()))

    def test_v046_replays_golden(self):
        bad = [k for k, v in self.golden.items() if digest_for_key(k) != v]
        self.assertEqual(bad, [], f"{len(bad)} parity mismatches, first: {bad[:5]}")

    def test_v047_flags_off_reproduce_v046(self):
        """v047 with every v0.47 knob reverted to v0.46 gives the v046 digest (30 seeds x 2/3/4P)."""
        revert = dict(colored_vuln_lock=False, helix_bypass_mode="LEGACY", helix_bypass_once_per_game=False,
                      die_face_profile="V046_VULN_NOPREMIUM", vuln_band_thresholds=(4, 7, 10),
                      vuln_min_target_by_version=(4, 4, 4))
        orig = GameConfig.v046_locked.__func__
        for players in (2, 3, 4):
            for seed in range(42, 72):
                want = digest("v046", players, seed)
                GameConfig.v046_locked = classmethod(lambda cls, **o: orig(cls, **{**revert, **o}))
                try:
                    got = digest("v046_locked", players, seed)
                finally:
                    GameConfig.v046_locked = classmethod(orig)
                self.assertEqual(got, want, (players, seed))


if __name__ == "__main__":
    unittest.main()
