"""v0.50.0 Gray ⚠ B23 + Pen Test L2 Gray thinning + Gray-aware bot (docs/specs/gray_vuln_b23_spec.md §10)."""

from __future__ import annotations

import os
import random
import unittest
from types import SimpleNamespace
from typing import Any, Dict, List
from unittest import mock

from scripts.run_gray_vuln_sweep import build_engine, play
from sim.bots import research_policy as rp
from sim.config import DieColor, GameConfig, GrayAwareParams
from sim.engine import phase1_roll_deploy as p1
from sim.engine import phase6_operations as p6
from sim.engine import research_tracks as rt
from sim.engine import sprint_plan as sp
from sim.engine import vulnerability as vuln
from sim.engine.research_tracks import BreakthroughChoice
from sim.entities import (CompanyCode, WhiteHatCode, create_gray_die, get_all_companies, get_all_white_hats)
from tests.test_locked_vuln_faces import G, Scripted, colored, mk_engine
from tests.test_v480_sprint_plan import StubBot, clear_pipeline, colored as colored_sp, gray, mk, set_sprint, with_stub


def mk50(players: int = 3, seed: int = 42, preset: str = "v050_roster", **ov: Any):
    return build_engine(preset, "mixed1", players, seed, ov)


# ------------------------------------------------------------------------------------------------ config
class TestConfig(unittest.TestCase):
    def test_t_cfg_1_v050_preset(self):
        c, b = GameConfig.v050(num_players=3), GameConfig.v049(num_players=3)
        self.assertEqual((c.gray_face_profile, c.pen_test_l2_breakthrough, c.gray_vuln_telemetry),
                         ("V050_GRAY2", "THIN_GRAY", True))
        diff = {f for f in c.__dataclass_fields__ if getattr(c, f) != getattr(b, f)}
        self.assertEqual(diff, {"gray_face_profile", "pen_test_l2_breakthrough", "gray_vuln_telemetry"})

    def test_older_presets_default_off(self):
        for name in ("v046", "v047", "v048", "v049", "v049_roster", "v046_locked"):
            c = getattr(GameConfig, name)(num_players=3)
            self.assertEqual((c.pen_test_l2_breakthrough, c.gray_vuln_telemetry, c.bot_gray_aware_seats), ("NONE", False, None))

    def test_t_cfg_2_validation(self):
        bad: List[Dict[str, Any]] = [
            dict(pen_test_l2_breakthrough="BOGUS"),
            dict(pen_test_l2_breakthrough="THIN_GRAY", defense_mode="SHIELDS"),
            dict(bot_research_mode="GRAY_AWARE", share_regain_currency="RESEARCH"),
            dict(bot_gray_aware_seats=(0,), bot_research_mode="THINNING_AWARE"),  # not GRAY_AWARE
            dict(bot_gray_aware_seats=(3,), bot_research_mode="GRAY_AWARE"),  # out of range (3 players)
            dict(bot_gray_aware_seats=(0, 0), bot_research_mode="GRAY_AWARE"),
            dict(bot_gray_aware_seats=(-1,), bot_research_mode="GRAY_AWARE"),
            dict(bot_gray_aware_params=GrayAwareParams(v_thin=2.0, v_rel4=1.0)),
            dict(bot_gray_aware_params=GrayAwareParams(last_round=0)),
            dict(bot_gray_aware_params=GrayAwareParams(rolls_per_round=-0.1)),
            dict(bot_gray_aware_params=GrayAwareParams(min_gray=1.5)),
            dict(gray_vuln_telemetry=1),
        ]
        for ov in bad:
            with self.assertRaises(ValueError, msg=str(ov)):
                GameConfig.v050_roster(num_players=3, **ov)
        with self.assertRaises(ValueError):
            GameConfig(num_players=3, gray_face_profile="V050_GRAY2")  # SHIELDS mode
        GameConfig.v050_roster(num_players=3, bot_gray_aware_seats=(0, 2))  # ok
        GameConfig.v049(num_players=3, gray_face_profile="V050_GRAY2", vuln_lock_gray=False)  # B23 without the lock is legal

    def test_t_cfg_3_roster_equals_composed_v049_roster(self):
        a = GameConfig.v050_roster(num_players=3)
        b = GameConfig.v049_roster(num_players=3, gray_face_profile="V050_GRAY2", pen_test_l2_breakthrough="THIN_GRAY",
                                   gray_vuln_telemetry=True, bot_research_mode="GRAY_AWARE")
        for f in a.__dataclass_fields__:
            self.assertEqual(getattr(a, f), getattr(b, f), f)
        self.assertEqual((a.bot_thin_tracks, a.bot_thin_gray_floor), (("RELEASE",), 3))
        self.assertTrue(a.bot_pr_push)


# ------------------------------------------------------------------------------------------------ face / lock
V050_PAYOUT_FIELDS = ("money", "patches", "is_choice", "choices", "block_amount", "is_star", "secrets_pending")


class TestFaces(unittest.TestCase):
    def test_t_face_1_table(self):
        b23, v48 = create_gray_die(1, "V050_GRAY2").faces, create_gray_die(2, "V048_SPRINT").faces
        self.assertEqual(len(b23), 6)
        self.assertEqual({i for i, f in enumerate(b23) if vuln.face_vuln(f) > 0}, {1, 2})
        for a, b in zip(b23, v48):
            for fld in V050_PAYOUT_FIELDS:
                self.assertEqual(getattr(a, fld, None), getattr(b, fld, None), fld)
        self.assertEqual([vuln.face_vuln(f) for f in v48], [0, 0, 1, 0, 0, 0])  # v0.48 table untouched

    def test_t_face_2_lock_and_reroll_filter(self):
        e = mk_engine(cfg_name="v050_roster")
        cfg = e.config
        for idx, expect in enumerate((False, True, True, False, False, False)):
            g = create_gray_die(970 + idx, cfg.gray_face_profile)
            g.current_face = g.faces[idx]
            self.assertEqual(vuln.lock_applies(cfg, g), expect, idx)
            self.assertEqual(vuln.is_reroll_locked(cfg, g), expect, idx)
        # a reroll request for a locked F2 is filtered out (v0.49 lock path: die.is_locked, no reroll used)
        g = create_gray_die(980, cfg.gray_face_profile)
        h = Scripted(e, [g], {980: [1, 0]}, [[0]])
        h.run()
        self.assertEqual(g.current_face, g.faces[1])
        self.assertEqual(h.p.total_rerolls_used, 0)
        # B23 without the v0.49 lock: the v0.48 Gray filter blocks it and counts it (gray_lock_blocked +1)
        e2 = mk_engine(cfg_name="v050_roster", vuln_lock_gray=False)
        g2 = create_gray_die(981, e2.config.gray_face_profile)
        h2 = Scripted(e2, [g2], {981: [1, 0]}, [[0]])
        h2.run()
        self.assertEqual(g2.current_face, g2.faces[1])
        self.assertEqual(h2.p.gray_lock_blocked, 1)

    def test_t_face_3_deploy_counts_vuln_by_face(self):
        e = mk_engine(cfg_name="v050_roster")
        gs = [create_gray_die(990 + i, e.config.gray_face_profile) for i in range(3)]
        h = Scripted(e, gs, {990: [1], 991: [2], 992: [4]}, [])
        v0 = h.p.vulnerability
        h.run()
        self.assertEqual(h.p.vulnerability - v0, 2)
        self.assertEqual(h.p.gray_vuln_kept_by_face, {"gray:2": 1, "gray:3": 1})
        self.assertEqual((h.p.gray_rolled_total, h.p.gray_vuln_kept_total), (3, 2))
        self.assertEqual(h.p.gray_rolls_by_round[e.state.current_round], [3, 2])

    def test_rng_draw_parity_per_roll(self):
        a, b = create_gray_die(1, "V050_GRAY2"), create_gray_die(2, "V048_SPRINT")
        r1, r2 = random.Random(7), random.Random(7)
        faces = [(a.roll(r1), b.roll(r2)) for _ in range(40)]
        self.assertEqual(r1.getstate(), r2.getstate())
        self.assertEqual([a.faces.index(x) for x, _ in faces], [b.faces.index(y) for _, y in faces])


# ------------------------------------------------------------------------------------------------ a1
class TestPenTestL2(unittest.TestCase):
    def setUp(self):
        self.e = mk(3, 42, "v050")

    def _state(self, e=None):
        e = e or self.e
        p = e.state.players[0]
        with_stub(e)
        clear_pipeline(p)
        g_rd, g_next, g_prod, g_cur, g_ready = (gray(e, 900 + i) for i in range(5))
        g_rd.secret_pending = True
        p.glitched_dice.append(g_rd)
        p.scanned_dice.extend([g_next, g_cur])
        sp.mark_current(p, [g_cur])
        p.in_production_dice.append(g_prod)
        p.ready_for_release_dice.append(g_ready)
        return e, p

    def test_t_l2_1_has_level_effect(self):
        on, off = GameConfig.v050(num_players=3), GameConfig.v049(num_players=3)
        self.assertTrue(rt.has_level_effect(on, "DEFENSE", 2))
        self.assertFalse(rt.has_level_effect(off, "DEFENSE", 2))
        for t in ("TRIAGE", "RELEASE", "PATENT"):
            self.assertFalse(rt.has_level_effect(on, t, 2), t)
        self.assertEqual(rt.BREAKTHROUGH_LEVELS, (1, 3))

    def test_t_l2_2_order_choice_and_hook(self):
        e, p = self._state()
        order = []
        for _ in range(5):
            p.breakthroughs.clear()
            rec = rt.resolve_breakthrough(e, p, "DEFENSE", 2)
            order.append(rec.detail["gray_die_id"])
        self.assertEqual(order, [900, 901, 902, 903, 904])  # R&D, Next, In Production, Current, Ready
        self.assertEqual(p.gray_removed_by_source, {"PEN_TEST_L2": 5})
        e, p = self._state(mk(3, 42, "v050"))
        rec = rt.resolve_breakthrough(e, p, "DEFENSE", 2, BreakthroughChoice(gray_die_id=904))
        self.assertEqual((rec.detail["gray_die_id"], rec.detail["zone"]), (904, "ready"))
        p.breakthroughs.clear()
        p.bot.thin = lambda cands: cands[-1][1].die_id  # bot hook beats the default
        self.assertEqual(rt.resolve_breakthrough(e, p, "DEFENSE", 2).detail["gray_die_id"], 903)
        p.breakthroughs.clear()
        p.bot.thin = lambda cands: 424242  # invalid -> default first
        self.assertEqual(rt.resolve_breakthrough(e, p, "DEFENSE", 2).detail["gray_die_id"], 900)

    def test_to_the_box_no_payout(self):
        e, p = self._state()
        market, money, lost = dict(e.state.market), p.money, p.secrets_lost_returned
        rt.resolve_breakthrough(e, p, "DEFENSE", 2)  # R&D Gray carrying a pending Secret
        self.assertEqual((dict(e.state.market), p.money), (market, money))
        self.assertEqual(p.secrets_lost_returned, lost + 1)

    def test_t_l2_3_no_gray_forfeits_limit_kept(self):
        e = mk(3, 42, "v050")
        p = e.state.players[0]
        clear_pipeline(p)
        p.defense_level = 2
        rec = rt.resolve_breakthrough(e, p, "DEFENSE", 2)
        self.assertEqual((rec.outcome, rec.detail), ("FORFEITED", {"reason": "no_gray_die"}))
        self.assertEqual(p.thin_forfeits, 1)
        self.assertEqual(e.config.pen_test_limits[2], 2)
        self.assertEqual(p.gray_removed_by_source, {})

    def test_t_l2_4_l2_and_l3_same_turn(self):
        e = mk(3, 42, "v050")
        p = e.state.players[0]
        clear_pipeline(p)
        p.ready_for_release_dice.append(gray(e, 910))
        p.defense_level, p.research_tokens = 1, 99
        p.breakthroughs.clear()
        done = p6.execute_track_upgrades(e, p, SimpleNamespace(track_upgrades=["DEFENSE", "DEFENSE"]))
        self.assertEqual(done, [("DEFENSE", 2), ("DEFENSE", 3)])
        outcomes = {b.level: b.outcome for b in p.breakthroughs if b.track == "DEFENSE"}
        self.assertEqual(outcomes, {2: "TAKEN", 3: "FORFEITED"})
        self.assertEqual(p.gray_removed_by_source, {"PEN_TEST_L2": 1})
        p.defense_level = 2
        b = rt.secret_faces.secret_yield(e.config, p, DieColor.BLUE)
        p.defense_level = 3
        c = rt.secret_faces.secret_yield(e.config, p, DieColor.BLUE)
        self.assertEqual(c - b, e.config.secret_yield_blue_grid_l3_bonus)  # Blue yield is level-based

    def test_t_l2_5_current_sprint_pruned(self):
        e = mk(3, 42, "v050")
        p = e.state.players[0]
        with_stub(e)
        cur = [gray(e, 920), gray(e, 921)]
        nxt = [gray(e, 922)]
        set_sprint(e, p, cur, nxt, bw=2)
        p.bot.thin = lambda cands: 920
        rt.resolve_breakthrough(e, p, "DEFENSE", 2)
        self.assertEqual(p.current_sprint_ids, {921})
        grads = sp.sprint_review(e, p)
        self.assertEqual({d.die_id for d in grads}, {921, 922})  # forced 1 from Current, back-fill from Next
        self.assertEqual(p.scanned_dice, [])

    def test_t_l2_6_once_only(self):
        e, p = self._state()
        self.assertIsNotNone(rt.resolve_breakthrough(e, p, "DEFENSE", 2))
        n = len(sp.owned_gray(p))
        self.assertIsNone(rt.resolve_breakthrough(e, p, "DEFENSE", 2))
        self.assertEqual(len(sp.owned_gray(p)), n)
        from sim.engine import fast_clone

        clone, _ = fast_clone.clone_engine(e)
        cp = clone.state.players[0]
        self.assertIsNone(rt.resolve_breakthrough(clone, cp, "DEFENSE", 2))
        self.assertEqual(len(sp.owned_gray(cp)), n)

    def test_t_l2_7_text(self):
        on, off = GameConfig.v050(num_players=3), GameConfig.v049(num_players=3)
        want = "Return 1 Gray Legacy die you own to the box"
        self.assertEqual(rt.breakthrough_text(on, "DEFENSE", 2), want)
        self.assertIsNone(rt.breakthrough_text(off, "DEFENSE", 2))
        e_on, e_off = mk(3, 42, "v050"), mk(3, 42, "v049")
        for e, flag in ((e_on, True), (e_off, False)):
            p = e.state.players[0]
            p.config = e.config
            p.defense_level = 1
            pv = rt.breakthrough_preview(p)["DEFENSE"]
            if flag:
                self.assertEqual(pv["breakthrough"], "Pen Test limit 2; " + want[0].lower() + want[1:])
            else:
                self.assertNotIn("Gray", str(pv["breakthrough"]))
        # flag-off previews stay the v0.49 output at every level (key 2 absent)
        p = e_off.state.players[0]
        p.config = e_off.config
        exp = {0: "Gain 1 Corporate Secret", 1: None,
               2: "Return 1 Gray Legacy die you own to the box; Blue R&D faces yield +3",
               3: "Pen Test limit 3; lower your Vulnerability by 1 at the start of each Operations Turn"}
        for lvl in (1, 2, 3):
            p.defense_level = lvl
            got = rt.breakthrough_preview(p)["DEFENSE"]["breakthrough"]
            self.assertEqual(got, exp[lvl], lvl)

    def test_t_cons_1_gray_conservation(self):
        from scripts.run_gray_vuln_sweep import install_invariants

        install_invariants()
        for players in (2, 3, 4):
            for seed in range(42, 52):
                e = mk50(players, seed)
                start = {p.player_id: len(sp.owned_gray(p)) for p in e.state.players}
                e.run_game()
                for p in e.state.players:
                    self.assertEqual(len(sp.owned_gray(p)) + sum(p.gray_removed_by_source.values()), start[p.player_id],
                                     (players, seed, p.player_id))


# ------------------------------------------------------------------------------------------------ bot
def probe_ga_order(orig_want, policy, player, st, config, lv, p_face, patches_l2):
    """Verbatim copy of ``ga_order`` in scripts/probe_gray_vuln_mitigation.py (state / p_face / patches inlined)."""
    from sim.engine import sprint_plan
    GA_PARAMS = {"rolls_per_round": 0.56, "rp_per_vuln": 2.0, "near_vuln": 3, "near_bonus": 1.0, "v_thin": 1.5,
                 "v_rel4": 2.5, "last_round": 9}
    base = orig_want(policy, player, config, lv)
    g = len(sprint_plan.owned_gray(player))
    rnd = int(getattr(st, "current_round", 1)) if st is not None else 1
    P = GA_PARAMS
    v = (P["rp_per_vuln"] * p_face * P["rolls_per_round"] * max(1, P["last_round"] - rnd)
         + (P["near_bonus"] if player.vulnerability >= P["near_vuln"] else 0.0))
    if v < P["v_thin"] or g < 2:
        return base
    costs = config.track_step_costs
    pen_t = 2 if patches_l2 else 3
    tri_t = 3 if getattr(config, "triage_l3_breakthrough", "SECRET") == "UPGRADE" else 4
    opts = []
    for t, tgt in (("DEFENSE", pen_t), ("TRIAGE", tri_t)):
        if lv[t] < tgt:
            opts.append((sum(costs[lv[t]:tgt]), t, tgt))
    head = (["TRIAGE"] if lv["TRIAGE"] < 1 else []) + ["RELEASE"] * max(0, 3 - lv["RELEASE"])
    for _, t, tgt in sorted(opts):
        head += [t] * (tgt - lv[t])
    if v >= P["v_rel4"] and lv["RELEASE"] >= 3:
        head += ["RELEASE"]
    counts, out = {}, []
    for t in head + base:
        if counts.get(t, 0) < 4 - lv[t]:
            out.append(t)
            counts[t] = counts.get(t, 0) + 1
    return out


class TestGrayAwareBot(unittest.TestCase):
    def test_t_bot_1_face_share(self):
        self.assertAlmostEqual(rp.gray_vuln_face_share(GameConfig.v049(num_players=3)), 1 / 6)
        self.assertAlmostEqual(rp.gray_vuln_face_share(GameConfig.v050(num_players=3)), 1 / 3)

    def test_t_bot_2_thin_value(self):
        e = mk50(3, 42)
        p, c = e.state.players[0], e.config
        e.state.current_round, p.vulnerability = 2, 3
        self.assertAlmostEqual(rp.gray_thin_value(p, e.state, c), 2 * (1 / 3) * 0.56 * 7 + 1, places=6)
        self.assertAlmostEqual(rp.gray_thin_value(p, e.state, c), 3.613, places=3)
        e.state.current_round, p.vulnerability = 7, 0
        self.assertAlmostEqual(rp.gray_thin_value(p, e.state, c), 0.747, places=3)

    def test_t_bot_3_matches_probe_verbatim(self):
        rng = random.Random(500)
        engines = {(l2, tri): mk50(3, 42, pen_test_l2_breakthrough=l2, triage_l3_breakthrough=tri)
                   for l2 in ("THIN_GRAY", "NONE") for tri in ("UPGRADE", "SECRET")}
        policy = rp.ResearchPolicy()
        orig = rp._thinning_aware_want_order
        hot = 0
        for _ in range(240):
            key = (rng.choice(("THIN_GRAY", "NONE")), rng.choice(("UPGRADE", "SECRET")))
            e = engines[key]
            p = e.state.players[0]
            clear_pipeline(p)
            n = rng.randint(0, 5)
            for i in range(n):
                p.ready_for_release_dice.append(gray(e, 800 + i))
            p.vulnerability = rng.randint(0, 9)
            e.state.current_round = rng.randint(1, 9)
            lv = {t: rng.randint(0, 4) for t in rp.TRACKS}
            p.gray_aware_hot_rounds.clear()
            got = rp._gray_aware_want_order(policy, p, e.state, e.config, dict(lv))
            want = probe_ga_order(orig, policy, p, e.state, e.config, dict(lv), 1 / 3, key[0] == "THIN_GRAY")
            self.assertEqual(got, want, (key, lv, n, p.vulnerability, e.state.current_round))
            hot += bool(p.gray_aware_hot_rounds)
        self.assertGreater(hot, 20)  # the hot branch is actually exercised

    def test_t_bot_4_not_hot_equals_thinning_aware(self):
        e = mk50(3, 42)
        p = e.state.players[0]
        policy = rp.ResearchPolicy()
        lv = {"DEFENSE": 0, "TRIAGE": 0, "RELEASE": 0, "PATENT": 0}
        clear_pipeline(p)
        p.ready_for_release_dice.append(gray(e, 800))  # g = 1 < 2
        p.vulnerability, e.state.current_round = 9, 1
        self.assertEqual(rp._gray_aware_want_order(policy, p, e.state, e.config, dict(lv)),
                         rp._thinning_aware_want_order(policy, p, e.config, dict(lv)))
        p.ready_for_release_dice.extend([gray(e, 801), gray(e, 802)])
        e.state.current_round, p.vulnerability = 8, 0  # V < 1.5
        self.assertEqual(rp._gray_aware_want_order(policy, p, e.state, e.config, dict(lv)),
                         rp._thinning_aware_want_order(policy, p, e.config, dict(lv)))
        self.assertEqual(p.gray_aware_hot_rounds, set())

    def test_t_bot_5_seat_filter(self):
        e = mk50(3, 42, bot_gray_aware_seats=(0,))
        c = e.config
        self.assertTrue(rp.is_gray_aware_seat(c, e.state.players[0]))
        self.assertFalse(rp.is_gray_aware_seat(c, e.state.players[1]))
        self.assertFalse(rp.is_gray_aware_seat(GameConfig.v049_roster(num_players=3), e.state.players[0]))
        e.run_game()
        self.assertEqual(e.state.players[1].gray_aware_hot_rounds, set())
        self.assertEqual(e.state.players[2].gray_aware_hot_rounds, set())

    def test_inv_bot_01_never_called_without_mode(self):
        e = mk50(3, 42, bot_research_mode="THINNING_AWARE")
        with mock.patch.object(rp, "_gray_aware_want_order", side_effect=AssertionError("called")):
            e.run_game()
        for p in e.state.players:
            self.assertEqual(p.gray_aware_hot_rounds, set())

    def test_t_bot_6_no_rng_draws(self):
        counts = []
        for mode in ("GRAY_AWARE", "THINNING_AWARE"):
            e = mk50(3, 42, bot_research_mode=mode)
            p = e.state.players[0]
            clear_pipeline(p)
            for i in range(4):
                p.ready_for_release_dice.append(gray(e, 800 + i))
            p.research_tokens, p.vulnerability, e.state.current_round = 20, 4, 2

            class Counting(random.Random):
                n = 0

                def random(self):
                    Counting.n += 1
                    return super().random()

                def getrandbits(self, k):
                    Counting.n += 1
                    return super().getrandbits(k)

            c = Counting()
            c.setstate(e.rng.getstate())
            e.rng = c
            Counting.n = 0
            plan = p6.resolve_operations_plan(p.bot, p, e.state, e.rng)
            p6.execute_player_operations_turn(e, p, plan)
            counts.append(Counting.n)
        self.assertEqual(counts[0], counts[1])


# ------------------------------------------------------------------------------------------------ edge cases
class TestEdgeCases(unittest.TestCase):
    def test_t_edge_2_release_l4_sets_locked_f2(self):
        e = mk_engine(cfg_name="v050_roster")
        p = e.state.players[0]
        p.release_level = 4
        g = create_gray_die(930, e.config.gray_face_profile)
        g.current_face, g.is_locked = g.faces[1], True
        self.assertTrue(p1.resolve_release_l4_gray_face_override(p, [g], None, 0, g.faces[0]))
        self.assertFalse(g.is_locked)
        self.assertEqual(vuln.face_vuln(g.current_face), 0)
        self.assertEqual(p.l4_payouts["release_gray_face_sets"], 1)
        # no Gray in the active dice: returns False, no exception
        self.assertFalse(p1.resolve_release_l4_gray_face_override(p, [colored(DieColor.RED, 931)], None, 0, g.faces[0]))

    def test_t_edge_3_ace_breaks_lock_on_gray_f3(self):
        from sim.bots import vulnerability_policy as vp

        e = mk_engine(cfg_name="v050_roster")
        p = e.state.players[0]
        e.state.staging_cup[G] = 3
        p.vulnerability = 4
        pur, g = colored(DieColor.PURPLE, 932), create_gray_die(933, e.config.gray_face_profile)
        h = Scripted(e, [pur, g], {932: [5], 933: [2]}, [])
        p.white_hat = next(w for w in get_all_white_hats() if w.code == WhiteHatCode.PRODIGY)
        with mock.patch.object(vp, "choose_ace_target", return_value=(1, g.faces[0])):
            h.run()
        self.assertEqual(g.current_face, g.faces[0])
        self.assertEqual(p.ace_lock_breaks, 1)
        self.assertEqual(p.vuln_gained_by_source.get("lockin", 0), 0)

    def test_t_edge_4_helix_bypass_rerolls_locked_f2_once_per_game(self):
        e = mk_engine(cfg_name="v050_roster")
        p = e.state.players[0]
        p.company = next(c for c in get_all_companies() if c.code == CompanyCode.HELIX)
        p.bot.choose_helix_bypass = lambda *a: True
        g = create_gray_die(934, e.config.gray_face_profile)
        Scripted(e, [g], {934: [1, 0]}, [[0]]).run()
        self.assertEqual((p.helix_bypass_uses, p.helix_bypass_locked_rerolled), (1, 1))
        self.assertFalse(p.is_helix_bypass_available("v1.0"))

    def test_t_edge_5_two_player_setec_corp(self):
        for seed in range(42, 62):
            e = mk50(2, seed)
            res = e.run_game()
            self.assertTrue(getattr(e.state, "setec_corp_active", False), seed)
            self.assertEqual(len(res.rankings), 2)
            self.assertTrue(all("gray_le3_round" in r for r in res.rankings))


class TestEndRow(unittest.TestCase):
    def test_keys_only_under_flag(self):
        on = play(("v050_roster", "mixed1", 3, 42, {}, False))
        self.assertIn("le3", on["seats"][0])
        e = mk50(3, 42)
        r = e.run_game().rankings[0]
        for k in ("gray_owned_by_round", "gray_le3_round", "gray_le2_round", "gray_removed_by_source", "gray_removed_total",
                  "thin_rounds", "thin_forfeits", "gray_rolled_total", "gray_vuln_kept_total", "gray_vuln_kept_by_face",
                  "gray_rolls_by_round", "gray_aware_hot_rounds", "release_gray_face_sets", "pen_test_l2_round"):
            self.assertIn(k, r)
        self.assertGreater(r["gray_rolled_total"], 0)


@unittest.skipUnless(os.environ.get("RUN_SLOW"), "slow: set RUN_SLOW=1 (or run scripts/check_gray_vuln_port.py)")
class TestPortFidelity(unittest.TestCase):
    def test_t_fid_1_native_matches_probe(self):
        from scripts.check_gray_vuln_port import check

        self.assertIsNone(check(50, [2, 3, 4], 42, max(1, (os.cpu_count() or 2) - 1)))


if __name__ == "__main__":
    unittest.main()
