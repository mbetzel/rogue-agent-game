"""v0.36.0 web controller flow (Phase B): Market Share, Public Relations Track, Customer Poaching finalisation,
free-choice Generic shields for humans, Version comparison logging, Market Collapse end reason."""

from __future__ import annotations

import json
import unittest

from sim.config import CubeColor, DieColor, EndGameReason, GameConfig, ShieldColor
from sim.engine import market_share
from sim.engine.state import ProductionRole
from sim.entities import Face
from tests.web_legacy import use_v037_rules
from web.game_controller import GameController

R3_MKT = Face(name="R3: Customer Poaching", is_star=True, star_code="R3_MKT")
R2_MKT = Face(name="R2: Ad Campaign", is_star=True, star_code="R2_MKT")
ANY1 = Face("Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)
INC1 = Face("+$1", money=1)


def _drive(gc: GameController, max_steps: int = 2000, on_phase=None) -> dict:
    """Plays every human decision with simple defaults until Game Over (scripted controller run)."""
    for _ in range(max_steps):
        st = gc.get_full_state()
        if st["phase"] == 7 or gc.state.game_over and gc.phase == 7:
            return st
        if on_phase:
            on_phase(gc, st)
        pid = 0
        ph, sub = gc.phase, gc.subphase
        if ph == 1:
            meta = gc.player_meta[pid]
            if gc.state.players[pid].is_patient_zero:
                gc.compile_drop()
            elif not meta.get("has_rolled"):
                gc.roll_pool(pid)
            elif not meta.get("has_committed"):
                gc.commit_defenses(pid, {})
            else:
                gc.compile_drop()
        elif ph == 2:
            gc.compile_drop()
        elif ph == 3:
            gc.confirm_income(pid)
        elif ph == 4:
            gc.confirm_attacks(pid, any_shield_allocations={"red": 0, "blue": 0, "green": 0})
        elif ph == 5:
            gc.choose_graduates(pid, None)
        elif ph == 6:
            caps = gc.get_action_capabilities(pid)
            if caps.get("can_regain_market_share"):
                gc.regain_market_share(pid)
            elif caps.get("can_ad_campaign"):
                gc.execute_star_action(pid, "R2")
            else:
                gc.end_turn(pid)
        else:
            raise AssertionError(f"unexpected phase {ph} {sub}")
    raise AssertionError("game did not finish")


@use_v037_rules
class TestWebV036(unittest.TestCase):
    def test_default_is_v036(self):
        gc = GameController()
        st = gc.new_game(num_players=3, seed=5)
        self.assertEqual(gc.state.config, GameConfig.v037(num_players=3, enable_corporate_asymmetry=True))
        self.assertTrue(st["is_market_share"] and st["is_share_regain"])
        self.assertEqual(st["patent_track_name"], "Public Relations Track")
        self.assertEqual(st["version_share_payout"], {"v2.0": 4})
        p0 = st["players"][0]
        # v0.37 Phase B: the web default is v0.37.0 (3P starts at 8 Secrets; Market Share unchanged)
        self.assertEqual((p0["secrets"], p0["market_share"], p0["market_share_max"], p0["regain_cost"], p0["regain_cap"]),
                         (8, 18, 18, 2, 1))
        red = st["market"]["red"]["variant"]
        self.assertEqual((red["code"], red["name"]), ("R1", "Brand Protection"))

    def test_scripted_full_games(self):
        poach_left = []

        def watch(gc, st):
            if gc.phase == 4:
                poach_left.append(len(gc.state._pending_poaches))

        for seed in range(12):
            gc = GameController()
            gc.new_game(num_players=2 + seed % 3, seed=seed, randomize_cards=True)
            st = _drive(gc, on_phase=watch)
            fr = st["final_result"]
            self.assertIsNotNone(fr)
            self.assertIn(fr["end_reason"], {"patient_zero", "singularity", "market_collapse", "total_wipeout"})
            self.assertIn("end_triggers", fr)
            for p in gc.state.players:
                ms = p.market_share
                self.assertTrue(0 <= ms <= p.market_share_max)
                self.assertEqual(p.market_share_start - p.market_share_lost_red - p.market_share_lost_poach
                                 + p.market_share_gained_poach + p.market_share_regained + p.market_share_gained_r2, ms)
                self.assertEqual((p.patent_secrets_gained, p.research_spent_patents), (0, 0))
            self.assertTrue(all(r["version"] == "v2.0" for r in st["version_comparisons"]))
            json.dumps(st, default=str)
        self.assertTrue(poach_left and all(n == 0 for n in poach_left))

    def _to_phase(self, gc, phase, exits=None, setup=None, post_commit=None):
        gc.roll_pool(0)
        if setup:
            setup(gc)
        gc.commit_defenses(0, {i: "any" for i, d in enumerate(gc.player_meta[0]["rolled_pool"])
                               if (d.current_face or INC1).shield_color == ShieldColor.ANY})
        if post_commit:
            post_commit(gc)
        if exits is not None:
            full = {CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0}
            full.update(exits)
            orig = gc.state.tower.drop
            gc.state.tower.drop = lambda cup, rng: dict(full)
        try:
            gc.compile_drop()
        finally:
            if exits is not None:
                gc.state.tower.drop = orig
        if phase >= 4:
            gc.confirm_income(0)

    def test_customer_poaching_resolves_in_web_phase3(self):
        gc = GameController()
        gc.new_game(num_players=2, seed=3)

        def setup(gc):
            rolled = gc.player_meta[0]["rolled_pool"]
            rolled[0].current_face = R3_MKT
            for d in rolled[1:]:
                d.current_face = INC1
            gc.state.players[1].market_share = 9

        self._to_phase(gc, 4, exits={CubeColor.BLACK: 1}, setup=setup)
        p0, p1 = gc.state.players
        self.assertEqual(gc.state._pending_poaches, [])
        self.assertEqual(p1.market_share_lost_poach, 1)
        self.assertTrue(any("Customer Poaching" in e for e in gc.event_log))

    def test_human_any_shield_backfilled(self):
        gc = GameController()
        gc.new_game(num_players=2, seed=3)

        def setup(gc):
            rolled = gc.player_meta[0]["rolled_pool"]
            rolled[0].current_face = ANY1
            for d in rolled[1:]:
                d.current_face = INC1

        self._to_phase(gc, 4, exits={CubeColor.RED: 1, CubeColor.GREEN: 1}, setup=setup)
        p0 = gc.state.players[0]
        ms0 = p0.market_share
        # the human asks to block nothing: the shield must still block (back-filled Blue > Red > Green -> Red)
        gc.confirm_attacks(0, any_shield_allocations={"red": 0, "blue": 0, "green": 0})
        bd = p0.last_defense_breakdown
        self.assertEqual(bd["any_allocated"], {"red": 1, "blue": 0, "green": 0})
        self.assertEqual(p0.market_share, ms0)
        # a legal choice is honoured
        gc2 = GameController()
        gc2.new_game(num_players=2, seed=3)
        self._to_phase(gc2, 4, exits={CubeColor.RED: 1, CubeColor.GREEN: 1}, setup=setup)
        gc2.confirm_attacks(0, any_shield_allocations={"green": 1})
        self.assertEqual(gc2.state.players[0].last_defense_breakdown["any_allocated"]["green"], 1)
        self.assertEqual(gc2.state.players[0].market_share, ms0 - 1)

    def test_phase6_regain_ad_campaign_and_no_patent_filing(self):
        gc = GameController()
        gc.new_game(num_players=2, seed=3)
        p0 = gc.state.players[0]
        gc.phase = 6
        gc.active_player_index = 0
        p0.market_share, p0.research_tokens, p0.money, p0.regain_this_turn = 10, 5, 3, 0
        caps = gc.get_action_capabilities(0)
        self.assertTrue(caps["can_regain_market_share"] and not caps["can_file_patent"])
        self.assertEqual((caps["regain_cost"], caps["regain_cap"], caps["regain_left_this_turn"]), (2, 1, 1))
        gc.regain_market_share(0)
        self.assertEqual((p0.market_share, p0.research_tokens), (11, 3))
        with self.assertRaises(ValueError):
            gc.regain_market_share(0)  # L0 limit: +1 per turn
        with self.assertRaises(ValueError):
            gc.file_patent(0)
        p0.r2_actions_available = 1
        self.assertTrue(gc.get_action_capabilities(0)["can_ad_campaign"])
        gc.execute_star_action(0, "R2")
        self.assertEqual((p0.market_share, p0.money, p0.r2_uses, p0.r2_actions_available), (12, 1, 1, 0))
        with self.assertRaises(ValueError):
            gc.execute_star_action(0, "R2")

    def test_comparison_and_collapse_logged(self):
        gc = GameController()
        gc.new_game(num_players=2, seed=3)
        s = gc.state
        s.current_version_index, s.corruption_track = 1, 4  # v2.0 needs 1 more Black
        s.players[1].market_share = 1

        def setup(gc):
            for d in gc.player_meta[0]["rolled_pool"]:
                d.current_face = INC1

        def strip_bot_shields(gc):  # the bot commits no shields this round
            gc.player_meta[1]["commitments"] = {}
            for d in gc.state.players[1].in_production_dice:
                d.current_face = INC1
                d.production_role = ProductionRole.INCOME

        self._to_phase(gc, 4, exits={CubeColor.BLACK: 1, CubeColor.RED: 1}, setup=setup, post_commit=strip_bot_shields)
        self.assertEqual([r.version for r in s.version_comparisons], ["v2.0"])
        self.assertTrue(any("Market Share comparison ($4)" in e for e in gc.event_log))
        gc.confirm_attacks(0, any_shield_allocations={})
        self.assertEqual(s.players[1].market_share, 0)
        self.assertEqual((s.end_reason, s.is_final_round), (EndGameReason.MARKET_COLLAPSE, True))
        self.assertTrue(any("MARKET COLLAPSE" in e for e in gc.event_log))
        self.assertIn(gc.phase, (5, 6))  # Final Round continues through Phases 5-6 (not Game Over yet)
        st = gc.get_full_state()
        self.assertEqual(st["version_comparisons"][0]["version"], "v2.0")


if __name__ == "__main__":
    unittest.main()
