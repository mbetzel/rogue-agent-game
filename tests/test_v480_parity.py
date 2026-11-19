"""INV-SP-16: v0.46 and v0.47 presets replay byte-identically against goldens captured before the v0.48 Sprint Plan change."""

import json
import unittest

from tests.parity_v046.capture import CONFIGS, GOLDEN_PATH, PLAYERS, SEEDS, digest


class TestV046Parity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(GOLDEN_PATH) as fh:
            cls.golden = json.load(fh)

    def test_golden_complete(self):
        self.assertEqual(len(self.golden), len(CONFIGS) * len(PLAYERS) * len(SEEDS))

    def test_v046_replays_golden(self):
        bad = [k for k, v in self.golden.items()
               if digest(k.split("|")[0], int(k.split("|")[1]), int(k.split("|")[2])) != v]
        self.assertEqual(bad, [], f"{len(bad)} parity mismatches, first: {bad[:5]}")


from tests.parity_v047 import capture as _c47  # noqa: E402


class TestV047Parity(unittest.TestCase):
    """v0.47 (Red Signature) golden captured on origin/main before the Sprint Plan rebase."""

    @classmethod
    def setUpClass(cls):
        with open(_c47.GOLDEN_PATH) as fh:
            cls.golden = json.load(fh)

    def test_golden_complete(self):
        self.assertEqual(len(self.golden), len(_c47.CONFIGS) * len(_c47.PLAYERS) * len(_c47.SEEDS))

    def test_v047_replays_golden(self):
        bad = [k for k, v in self.golden.items()
               if _c47.digest(k.split("|")[0], int(k.split("|")[1]), int(k.split("|")[2])) != v]
        self.assertEqual(bad, [], f"{len(bad)} parity mismatches, first: {bad[:5]}")


if __name__ == "__main__":
    unittest.main()
