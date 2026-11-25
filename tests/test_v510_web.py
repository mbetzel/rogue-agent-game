"""v0.51.0 web (docs/specs/green_landing_spec.md §7, TC-LAND-16..19)."""

from __future__ import annotations

import random
import unittest

from sim.config import CubeColor
from web.controller.phase4_attack_actions import green_preview
from web.game_controller import GameController
from tests.test_v460_web import _fresh, _to_phase4


def _phase4_gc(seed, vs, k, n=3):
    gc = _fresh(n=n, seed=seed)
    _to_phase4(gc)
    if gc.phase != 4:
        return None
    gc.attack_strengths[CubeColor.GREEN] = k
    gc.compile_result.exited_cubes[CubeColor.GREEN] = k
    for p, v in zip(gc.state.players, vs):
        p.vulnerability = v
        p.company = None
    return gc


class TestWebLanding(unittest.TestCase):
    def test_tc_land_16_preview_matches_engine(self):
        rng = random.Random(16)
        checked = 0
        for seed in range(100, 130):
            vs, k = [rng.randint(0, 14) for _ in range(3)], rng.randint(1, 5)
            gc = _phase4_gc(seed, vs, k)
            if gc is None:
                continue
            prev = green_preview(gc)
            gc.confirm_attacks(0)
            ev = gc.state.green_round_stats["events"]
            keys = ("cube", "pids", "v", "damage", "land", "capped")
            if any(e["cancelled"] for e in ev):
                continue
            for a, b in zip(prev, ev):
                for key in keys:
                    if key in a or key in b:
                        self.assertEqual(a.get(key), b.get(key), (seed, key))
            self.assertEqual(len(prev), len(ev))
            checked += 1
        self.assertGreater(checked, 10)

    def test_tc_land_17_log_text(self):
        gc = _phase4_gc(21, [9, 2, 2], 2)
        if gc is None:
            self.skipTest("no Phase 4 this seed")
        gc.confirm_attacks(0)
        log = "\n".join(gc.event_log)
        self.assertIn("Vulnerability drops to 5", log)
        self.assertIn("already hit by Green this round", log)
        self.assertNotIn("reset to", log)

    def test_tc_land_18_track_view(self):
        st = _fresh(n=2, seed=3).get_full_state()["vulnerability_track"]
        self.assertEqual([b["land"] for b in st["bands"]], [2, 5, 8])
        self.assertIs(st["one_hit_per_round"], True)
        self.assertEqual(st["hit_landing_by_band"], [2, 5, 8])

    def test_tc_land_19_rules_version(self):
        self.assertEqual(_fresh(n=2, seed=3).get_full_state()["rules_version"], "v0.52.0")
        with self.assertRaises(ValueError):
            GameController().new_game(num_players=2, seed=1, rules_version="v0.50.0")


if __name__ == "__main__":
    unittest.main()
