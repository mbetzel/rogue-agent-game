"""v0.51.0 Green hit landing + one hit per round (docs/specs/green_landing_spec.md §9). Fixed seeds."""

from __future__ import annotations

import dataclasses
import random
import unittest
from unittest import mock

from sim.bots import vulnerability_policy as vp
from sim.config import GameConfig
from sim.engine import end_game, vulnerability as vuln
from sim.engine import phase4_attack_resolution as p4
from sim.engine.phase2_compiler import _v046_corruption_demote
from sim.entities import CompanyCode, CorruptionSpace, TargetCriterion
from tests.test_v460_vulnerability_track import G, atk, mk_cr, mk_engine, set_company
from tests.test_v500_parity import _run

FLOOR = 5


def mk(players=3, cfg="v051", seed=9, **ov):
    e = mk_engine(players=players, seed=seed, cfg_name=cfg, **ov)
    for p in e.state.players:
        p.company = None  # no Aegis unless a test sets one
    return e


def green(e, vs, k, secrets=10, rnd=None):
    cr = mk_cr(green=k)
    for p, v in zip(e.state.players, vs):
        p.vulnerability, p.secrets = v, secrets
    return vuln.resolve_green(e, cr, atk(cr))


def lost(e, secrets=10):
    return [secrets - p.secrets for p in e.state.players]


def vs_of(e):
    return [p.vulnerability for p in e.state.players]


class TestConfig(unittest.TestCase):
    def test_tc_land_04_presets_and_helpers(self):
        c = GameConfig.v051(num_players=3)
        self.assertEqual((c.vuln_hit_landing_by_band, c.vuln_one_hit_per_round), ((2, 5, 8), True))
        for v, want in [(5, 2), (6, 2), (7, 2), (8, 5), (9, 5), (10, 5), (11, 8), (12, 8), (15, 8)]:
            self.assertEqual(vuln.hit_landing(c, v), want, v)
        d = GameConfig.v050(num_players=3)
        self.assertTrue(all(vuln.hit_landing(d, v) == 0 for v in range(16)))

    def test_tc_land_05_invalid(self):
        bad = [dict(vuln_hit_landing_by_band=(2, 5)), dict(vuln_hit_landing_by_band=(2, 5, 8, 9)),
               dict(vuln_hit_landing_by_band=[2, 5, 8]), dict(vuln_hit_landing_by_band=(True, 5, 8)),
               dict(vuln_hit_landing_by_band=(-1, 5, 8)), dict(vuln_hit_landing_by_band=(5, 2, 8)),
               dict(vuln_hit_landing_by_band=(5, 5, 8)), dict(vuln_hit_landing_by_band=(2, 8, 8)),
               dict(vuln_hit_landing_by_band=(2, 5, 11)), dict(vuln_one_hit_per_round=1),
               dict(defense_mode="SHIELDS", vuln_one_hit_per_round=True),
               dict(defense_mode="SHIELDS", vuln_hit_landing_by_band=(2, 5, 8))]
        for ov in bad:
            with self.assertRaises(ValueError, msg=str(ov)):
                GameConfig.v050(num_players=3, **ov)

    def test_tc_land_06_valid_edges(self):
        for ov in (dict(vuln_hit_landing_by_band=(4, 7, 10)), dict(vuln_hit_landing_by_band=(0, 0, 0)),
                   dict(vuln_hit_landing_by_band=(2, 5, 8), vuln_one_hit_per_round=False)):
            GameConfig.v050(num_players=3, **ov)

    def test_tc_land_07_band_index_below_first(self):
        c = GameConfig.v050(num_players=3, vuln_min_target_by_version=(3, 3, 3))
        self.assertEqual(vuln.band_index(c, 2), 0)
        self.assertEqual(vuln.band_index(c, 4), 0)
        self.assertEqual((vuln.band_index(c, 5), vuln.band_index(c, 11), vuln.band_index(c, 14.5)), (0, 2, 2))

    def test_tc_land_20_hit_leaves_band(self):
        for land in ((4, 7, 10), (0, 0, 0), (2, 5, 8)):
            c = GameConfig.v050(num_players=3, vuln_hit_landing_by_band=land)
            for v in range(FLOOR, 16):
                self.assertLess(vuln.hit_landing(c, v), v)
                if vuln.band_index(c, v) >= 1:
                    self.assertLess(vuln.band_index(c, vuln.hit_landing(c, v)), vuln.band_index(c, v))


class TestEngine(unittest.TestCase):
    def test_tc_land_08a(self):
        for v, loss, end in ((6, 1, 2), (9, 2, 5), (12, 3, 8)):
            for k in (1, 3):
                e = mk()
                ev = green(e, [v, 1, 2], k)
                self.assertEqual((lost(e)[0], e.state.players[0].vulnerability), (loss, end), (v, k))
                if k == 3:  # a landing below the min target (6 -> 2) leaves no one at 5+: not "capped" (§4.2 code)
                    self.assertTrue(all(x["capped"] == (end >= FLOOR) for x in ev[1:]))

    def test_tc_land_08_multi(self):
        cases = [("b", [8, 6], 2, [2, 1], [5, 2]), ("c", [5, 8], 2, [1, 2], [2, 5]),
                 ("d", [11, 7], 2, [3, 1], [8, 2]), ("e", [11, 11], 3, [3, 3], [8, 8]),
                 ("f", [12, 9], 4, [3, 2], [8, 5]), ("g", [9, 5, 5], 3, [2, 1, 1], [5, 2, 2]),
                 ("h", [3, 4], 2, [0, 0], [3, 4])]
        for name, vs, k, loss, end in cases:
            e = mk(players=len(vs) if len(vs) > 2 else 2)
            ev = green(e, vs, k)
            self.assertEqual((lost(e), vs_of(e)), (loss, end), name)
            if name == "c":
                self.assertEqual([x["pids"] for x in ev], [[1], [0]])
            if name == "e":
                self.assertEqual(sorted(ev[0]["pids"]), [0, 1])
                self.assertTrue(ev[1]["capped"] and ev[2]["capped"])
                self.assertEqual(e.state.green_cap_no_target, 2)
                self.assertEqual([p.green_landing_unsafe for p in e.state.players], [1, 1])
                self.assertEqual([p.green_cap_skips for p in e.state.players], [2, 2])
            if name == "f":
                self.assertEqual((e.state.green_cap_no_target, e.state.green_round_stats["no_target"]), (2, 2))
            if name == "g":
                self.assertTrue(ev[2]["capped"])
            if name == "h":
                self.assertTrue(all(not x["capped"] for x in ev))
                self.assertEqual(e.state.green_cap_no_target, 0)

    def test_tc_land_09_counters(self):
        e = mk(players=2)
        green(e, [11, 7], 2)
        p0, p1 = e.state.players
        self.assertEqual((p0.vuln_reset_by_hit_total, p1.vuln_reset_by_hit_total), (3, 5))
        self.assertEqual((p0.green_landing_unsafe, p1.green_landing_unsafe), (1, 0))
        self.assertEqual(p0.green_hit_rounds, [e.state.current_round])
        e = mk(players=2)
        green(e, [8, 6], 2)
        self.assertEqual(e.state.players[1].green_landing_unsafe, 0)

    def _random_state(self, rng):
        n = rng.randint(2, 4)
        return n, [rng.randint(0, 15) for _ in range(n)], rng.randint(0, 6)

    def test_tc_land_10_loss_exactness(self):
        rng = random.Random(2026)
        for i in range(1000):
            n, vs, k = self._random_state(rng)
            a, b = mk(players=n, cfg="v050"), mk(players=n)
            green(a, vs, k)
            green(b, vs, k)
            self.assertEqual(lost(a), lost(b), (vs, k))
            hit = [p.green_hits > 0 for p in b.state.players]
            for pa, pb, h in zip(a.state.players, b.state.players, hit):
                if not h:
                    self.assertEqual(pa.vulnerability, pb.vulnerability)

    def test_tc_land_11_no_repeat_hit(self):
        rng = random.Random(7)
        for i in range(200):
            n, vs, k = self._random_state(rng)
            e = mk(players=n)
            ev = green(e, vs, k)
            pids = [pid for x in ev for pid in x["pids"]]
            self.assertEqual(len(pids), len(set(pids)), (vs, k))

    def test_tc_land_12_aegis(self):
        e = mk(players=2)
        set_company(e.state.players[0], CompanyCode.AEGIS)
        e.aegis_green_override = {0: True}
        ev = green(e, [9, 6], 2)
        p0 = e.state.players[0]
        self.assertEqual((lost(e), vs_of(e), p0.green_hits_cancelled), ([0, 1], [5, 2], 1))
        self.assertEqual([x["pids"] for x in ev], [[0], [1]])

    def test_tc_land_12b_patient_zero_once(self):
        e = mk(players=3)
        green(e, [11, 1, 2], 3, secrets=1)
        self.assertEqual(e.state.players[0].secrets, -2)
        self.assertEqual(e.state.players[0].green_hits, 1)
        vuln.flag_patient_zero(e)
        self.assertTrue(e.state.players[0].is_patient_zero)

    def test_tc_land_13_no_target(self):
        e = mk()
        cup0 = e.state.staging_cup[G]
        for p, v in zip(e.state.players, (0, 1, 4)):
            p.vulnerability = v
        cr = mk_cr(green=2)
        p4.execute_attack_resolution(e, [], cr)
        self.assertEqual(vs_of(e), [0, 1, 4])
        self.assertEqual(e.state.staging_cup[G], cup0 + 2)
        st = e.state.green_round_stats
        self.assertEqual(st["no_target"], sum(1 for x in st["events"] if not x["pids"]))
        self.assertEqual((st["no_target"], st["cap_no_target"]), (2, 0))

    def test_tc_land_13_round_stats_relations(self):
        rng = random.Random(3)
        for _ in range(100):
            n, vs, k = self._random_state(rng)
            for cfg in ("v050", "v051"):
                e = mk(players=n, cfg=cfg)
                green(e, vs, k)
                st = e.state.green_round_stats
                self.assertLessEqual(st["cap_no_target"], st["no_target"])
                if cfg == "v050":
                    self.assertEqual(st["cap_no_target"], 0)

    def test_tc_land_13b_buffer_overflow(self):
        e = mk()
        for p in e.state.players:
            p.vulnerability = 9
        cr = mk_cr(green=2, overflow=True)
        self.assertEqual(vuln.resolve_green(e, cr, atk(cr)), [])
        self.assertEqual((vs_of(e), e.state.green_cap_no_target), ([9, 9, 9], 0))
        self.assertEqual([p.green_hits for p in e.state.players], [0, 0, 0])


def stock_loss_if(v_self, rivals_v, k, cfg, floor):
    vals = [float(v_self)] + [float(v) for v in rivals_v]
    loss = 0
    for _ in range(k):
        elig = [i for i, v in enumerate(vals) if v >= floor]
        if not elig:
            break
        top = max(vals[i] for i in elig)
        dmg = vuln.band_damage(cfg, top)
        for i in elig:
            if vals[i] == top:
                if i == 0:
                    loss += dmg
                vals[i] = float(cfg.vuln_hit_reset)
    return loss


class TestBot(unittest.TestCase):
    def test_tc_land_14_matches_stock(self):
        cfg = GameConfig.v051_roster(num_players=4)
        rng = random.Random(14)

        def draw():
            x = rng.randint(0, 15)
            return x + 0.4 * rng.randint(0, 2) if rng.random() < 0.4 else x

        for _ in range(2000):
            vs, rv, k = draw(), [draw() for _ in range(rng.randint(1, 3))], rng.randint(0, 6)
            self.assertEqual(vp.loss_if(vs, rv, k, cfg, FLOOR), stock_loss_if(vs, rv, k, cfg, FLOOR), (vs, rv, k))

    def test_tc_land_15_matches_engine(self):
        rng = random.Random(15)
        shapes = (("v051", {}), ("v050", {}), ("v050", dict(vuln_hit_landing_by_band=(2, 5, 8))))
        for name, ov in shapes:
            for _ in range(500):
                n = rng.randint(2, 4)
                vs, k = [rng.randint(0, 15) for _ in range(n)], rng.randint(0, 6)
                e = mk(players=n, cfg=name, **ov)
                green(e, vs, k)
                want = lost(e)[0]
                got = vp.loss_if(vs[0], vs[1:], k, e.config, FLOOR)
                self.assertEqual(got, want, (name, ov, vs, k))


class TestEdges(unittest.TestCase):
    def test_tc_land_21_target_lock_after_hit(self):
        e = mk()
        green(e, [6, 1, 1], 1)
        p = e.state.players[0]
        self.assertEqual(p.vulnerability, 2)
        for t in ("DEFENSE", "TRIAGE", "RELEASE", "PR"):
            p.encrypted_research_tracks.add(t)
        p4._resolve_signature_green(e, p)
        self.assertEqual(p.vulnerability, 2 + 2 * e.config.signature_green_cube_count)

    def test_tc_land_22_corruption_counter(self):
        sp = CorruptionSpace(1, "t", demote_dice=2, target_demote_criterion=TargetCriterion.FEWEST_GLITCHED,
                             target_criterion=TargetCriterion.FEWEST_GLITCHED)
        e = mk()
        for p, v in zip(e.state.players, (2, 9, 9)):
            p.vulnerability = v
        _v046_corruption_demote(e, sp)
        p0 = e.state.players[0]
        self.assertEqual((p0.vulnerability, p0.corruption_vuln_into_target), (5, {3: 1}))
        self.assertEqual([p.corruption_vuln_into_target for p in e.state.players[1:]], [{}, {}])

    def test_tc_land_23_end_row_gate(self):
        a = _run("v051_roster", 3, 42)
        b = _run("v050_roster", 3, 42)
        for k in ("green_landing_unsafe", "green_cap_skips", "green_hit_rounds", "green_multi_hit_rounds",
                  "green_back_to_back", "corruption_vuln_into_target"):
            self.assertIn(k, a.rankings[0])
            self.assertNotIn(k, b.rankings[0])
        key = lambda r: (r.end_reason, r.total_rounds, sorted(r.winner_ids),  # noqa: E731
                         [(x["player_id"], x["secrets"]) for x in r.rankings])
        for seed in range(42, 62):
            on = _run("v051_roster", 3, seed)
            with mock.patch.object(end_game, "_v051_enabled", lambda cfg: False):
                off = _run("v051_roster", 3, seed)
            self.assertEqual(key(on), key(off), seed)
            self.assertNotIn("green_hit_rounds", off.rankings[0])
            self.assertTrue(all(r["green_multi_hit_rounds"] == 0 for r in on.rankings))

    def test_tc_land_24_cap_off_landing_in_range(self):
        e = mk(players=2, cfg="v050", vuln_hit_landing_by_band=(2, 5, 8))
        green(e, [9, 0], 2)
        p0 = e.state.players[0]
        self.assertEqual((lost(e)[0], p0.vulnerability), (3, 2))
        rounds = [p0.green_hit_rounds.count(r) for r in set(p0.green_hit_rounds)]
        self.assertEqual(sum(1 for c in rounds if c >= 2), 1)


if __name__ == "__main__":
    unittest.main()
