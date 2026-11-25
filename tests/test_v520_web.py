"""v0.52.0 web (docs/specs/ms_stack_order_spec.md): ruleset, Market Share stack order in the state."""

from __future__ import annotations

import unittest
from pathlib import Path

from web.game_controller import GameController
from tests.test_v460_web import _fresh

ROOT = Path(__file__).resolve().parents[1]


class TestWebMsStack(unittest.TestCase):
    def test_rules_version(self):
        self.assertEqual(_fresh(n=2, seed=3).get_full_state()["rules_version"], "v0.52.0")
        for old in ("v0.51.0", "v0.50.0"):
            with self.assertRaises(ValueError):
                GameController().new_game(num_players=2, seed=1, rules_version=old)

    def test_max_25_and_stack_in_state(self):
        for n in (2, 3, 4):
            st = _fresh(n=n, seed=5).get_full_state()
            ms = st["market_share_stack"]
            self.assertEqual(ms["max"], 25)
            ids = [e["id"] for e in ms["order"]]
            self.assertEqual(len(ids), n + (1 if n == 2 else 0))
            self.assertEqual(-1 in ids, n == 2)
            self.assertEqual([e["rank"] for e in ms["order"]], list(range(1, len(ids) + 1)))
            self.assertTrue(all(p["market_share_max"] == 25 for p in st["players"]))
            ranks = {p["player_id"]: p["market_share_stack_rank"] for p in st["players"]}
            self.assertEqual(sorted(ranks.values()), sorted(r for r in ranks.values()))
            for e in ms["order"]:
                if e["id"] >= 0:
                    self.assertEqual(ranks[e["id"]], e["rank"])

    def test_first_player_on_top_and_move(self):
        gc = _fresh(n=3, seed=7)
        st = gc.get_full_state()
        first = gc.state.first_player_index
        space = {e["id"]: e["market_share"] for e in st["market_share_stack"]["order"]}
        self.assertEqual(len(set(space.values())), 1)
        self.assertEqual(st["market_share_stack"]["order"][0]["id"], gc.state.players[first].player_id)
        # a lone mover lands on top of its new space
        s = gc.state
        other = s.players[(first + 1) % 3]
        before = other.market_share
        other.change_market_share(-1, "red")
        other.change_market_share(1, "regain")  # back up: arrives on top of the shared space
        order = gc.get_full_state()["market_share_stack"]["order"]
        self.assertEqual(order[0]["id"], other.player_id)

    def test_ui_wording(self):
        js = "".join((ROOT / "web/static/js/components" / f).read_text() for f in ("compiler.js", "player_mats.js", "modals.js"))
        self.assertNotIn("ties share", js)
        self.assertIn("v0.52.0", (ROOT / "web/static/index.html").read_text())


if __name__ == "__main__":
    unittest.main()
