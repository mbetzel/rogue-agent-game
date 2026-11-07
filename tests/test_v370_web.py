"""v0.37.0 web flow (Phase B): the Market Leader Bonus in the end-game result, the event log and the state payload.

Spec: docs/specs/v370_market_leader_bonus_spec.md §11 (Phase B web items); staff note 7 (shown only when awarded).
"""

from __future__ import annotations

import json
import unittest

from sim.config import GameConfig
from tests.test_v360_web import _drive
from web.game_controller import GameController


class TestWebV037(unittest.TestCase):
    def test_default_is_v037(self):
        for n, sec in ((2, 9), (3, 8), (4, 9)):
            gc = GameController()
            st = gc.new_game(num_players=n, seed=5)
            self.assertEqual(gc.state.config, GameConfig.v037(num_players=n, enable_corporate_asymmetry=True))
            self.assertEqual(st["players"][0]["secrets"], sec)
            self.assertEqual(st["starting_secrets"], sec)  # rendered on the Secrets card (no hardcoded values)
            self.assertTrue(st["is_market_leader_bonus"])
            self.assertEqual(st["market_leader_bonus_schedule"], {2: [2, 0], 3: [2, 1, 0], 4: [2, 1, 0, 0]}[n])
        gc = GameController()
        st = gc.new_game(num_players=1, seed=5)  # solo practice: no schedule for 1 player
        self.assertFalse(st["is_market_leader_bonus"])
        self.assertEqual(st["market_leader_bonus_schedule"], [])

    def test_scripted_games_report_bonus(self):
        awarded = 0
        for seed in range(9):
            gc = GameController()
            gc.new_game(num_players=2 + seed % 3, seed=seed, randomize_cards=True)
            st = _drive(gc)
            fr = st["final_result"]
            json.dumps(st, default=str)
            for k in ("market_leader_bonus_awarded", "market_leader_bonus_schedule", "pre_bonus_winner_ids",
                      "market_leader_bonus_changed_winner"):
                self.assertIn(k, fr)
            self.assertEqual(fr["market_leader_bonus_awarded"], not fr["is_total_wipeout"])
            log_line = any(e.startswith("MARKET LEADER BONUS") for e in gc.event_log)
            self.assertEqual(log_line, fr["market_leader_bonus_awarded"])
            for r in fr["rankings"]:
                self.assertEqual(r["secrets"], r["secrets_before_bonus"] + r["market_leader_bonus"])
                if r["is_patient_zero"] or fr["is_total_wipeout"]:
                    self.assertEqual((r["market_share_place"], r["market_leader_bonus"]), (None, 0))
                else:
                    self.assertGreaterEqual(r["market_share_place"], 1)
            # held Corporate Secrets are never changed by scoring
            held = {p.player_id: p.secrets for p in gc.state.players}
            self.assertEqual({r["player_id"]: r["secrets_before_bonus"] for r in fr["rankings"]}, held)
            awarded += int(fr["market_leader_bonus_awarded"])
        self.assertGreater(awarded, 0)

    def test_end_screen_hides_bonus_when_not_awarded(self):
        """The modal renders the Market Leader Bonus column/line only when ``market_leader_bonus_awarded``."""
        import os

        path = os.path.join(os.path.dirname(__file__), "..", "web", "static", "js", "components", "modals.js")
        with open(path, encoding="utf-8") as fh:
            js = fh.read()
        self.assertIn("const mlb = !!res.market_leader_bonus_awarded;", js)
        self.assertIn("${mlb ? '<th style=\"padding: 6px;\">Market Leader Bonus</th>' : \"\"}", js)
        self.assertIn("secrets_before_bonus", js)

    def test_player_mat_uses_serialised_starting_secrets(self):
        import os

        path = os.path.join(os.path.dirname(__file__), "..", "web", "static", "js", "components", "player_mats.js")
        with open(path, encoding="utf-8") as fh:
            js = fh.read()
        self.assertIn("state.starting_secrets", js)
        self.assertNotIn("Start: 9 (2P)", js)
        self.assertNotIn("Start: 7 (2P/3P)", js)
        gc = GameController()
        self.assertEqual(gc.new_game(num_players=4, seed=1)["starting_secrets"], 9)
        gc = GameController()
        st = gc.new_game(num_players=2, seed=1)
        gc.state.config = GameConfig.legacy_v036(num_players=2, enable_corporate_asymmetry=True)
        self.assertEqual(gc.get_full_state()["starting_secrets"], 7)


class TestPnPTextV037(unittest.TestCase):
    def test_no_stale_v036_starting_secrets_text(self):
        """Guards the Client Company card text in the PnP generator against the v0.36 "7 SECRETS" value."""
        import os

        path = os.path.join(os.path.dirname(__file__), "..", "pnp", "generate_pnp.py")
        with open(path, encoding="utf-8") as fh:
            self.assertNotIn("7 SECRETS", fh.read())


if __name__ == "__main__":
    unittest.main()
