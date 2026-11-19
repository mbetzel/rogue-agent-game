"""INV-PARITY: v0.45 presets replay byte-identically against the golden captured before any v0.46 change."""

import json
import unittest

from tests.parity_v045.capture import CONFIGS, GOLDEN_PATH, PLAYERS, SEEDS, digest


class TestV045Parity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(GOLDEN_PATH) as fh:
            cls.golden = json.load(fh)

    def test_golden_complete(self):
        self.assertEqual(len(self.golden), len(CONFIGS) * len(PLAYERS) * len(SEEDS))

    def test_v045_replays_golden(self):
        bad = [k for k, v in self.golden.items()
               if digest(k.split("|")[0], int(k.split("|")[1]), int(k.split("|")[2])) != v]
        self.assertEqual(bad, [], f"{len(bad)} parity mismatches, first: {bad[:5]}")


class TestV046Determinism(unittest.TestCase):
    def _digest(self, res):
        return (res.end_reason, res.total_rounds, list(res.winner_ids),
                [(r["player_id"], r["secrets"], r["money"]) for r in res.rankings])

    def test_v046_determinism(self):
        """Same seed -> identical result across two runs and across a fast_clone round trip."""
        from scripts.run_v380_secret_faces_sweep import build_engine
        from sim.engine import fast_clone

        for players, seed in ((2, 42), (3, 43), (4, 44)):
            a = self._digest(build_engine("v046_roster", "mixed1", players, seed, {}).run_game())
            b = self._digest(build_engine("v046_roster", "mixed1", players, seed, {}).run_game())
            self.assertEqual(a, b)
            e = build_engine("v046_roster", "mixed1", players, seed, {})
            e.run_round()
            clone, _ = fast_clone.clone_engine(e)
            self.assertEqual(self._digest(e.run_game()), self._digest(clone.run_game()))


if __name__ == "__main__":
    unittest.main()
