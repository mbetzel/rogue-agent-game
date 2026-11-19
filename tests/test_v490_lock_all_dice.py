"""v0.49.0 Locked ⚠ Faces, "lock all dice" on top of v0.48.0 (GameConfig.v049): colored, Secret/R&D and Gray ⚠ faces lock."""

import unittest
from unittest import mock

from sim.config import DieColor, GameConfig
from sim.engine import phase1_roll_deploy as p1
from sim.engine import vulnerability as vuln
from sim.entities import CompanyCode, Die, create_gray_die, get_all_companies
from tests.test_locked_vuln_faces import Scripted, colored, mk_engine

GRAY_VULN_FACE = 2  # V048_SPRINT: only Face 3 (+$2 / +2 🔬) carries ⚠


def gray48(die_id):
    return create_gray_die(die_id, "V048_SPRINT")


class TestV049Config(unittest.TestCase):
    def test_preset_values(self):
        c = GameConfig.v049_roster(num_players=3)
        self.assertTrue(c.colored_vuln_lock and c.colored_vuln_lock_secret and c.vuln_lock_gray)
        self.assertTrue(c.sprint_plan_enabled)  # inherits v0.48
        self.assertEqual(c.vuln_face_lock, "GRAY")
        self.assertEqual(c.gray_face_profile, "V048_SPRINT")
        self.assertEqual(c.die_face_profile, "V046_VULN")
        self.assertEqual(tuple(c.vuln_band_thresholds), (5, 8, 11))
        self.assertEqual(tuple(c.vuln_min_target_by_version), (5, 5, 5))
        self.assertEqual((c.helix_bypass_mode, c.helix_bypass_once_per_game), ("REROLL_LOCKED", True))
        self.assertEqual(c.bot_research_mode, "THINNING_AWARE")

    def test_validation_and_older_presets(self):
        with self.assertRaises(ValueError):
            GameConfig.v048(vuln_lock_gray=True)  # needs colored_vuln_lock
        for name in ("v046", "v047", "v048", "v046_locked"):
            self.assertFalse(getattr(GameConfig, name)().vuln_lock_gray, name)


class TestV049GrayLock(unittest.TestCase):
    def setUp(self):
        self.e = mk_engine(cfg_name="v049_roster")

    def test_gray_vuln_face_sets_is_locked(self):
        g = gray48(950)
        g.current_face = g.faces[GRAY_VULN_FACE]
        self.assertTrue(vuln.lock_applies(self.e.config, g))
        g.current_face = g.faces[0]
        self.assertFalse(vuln.lock_applies(self.e.config, g))
        g2 = gray48(952)
        g2.current_face = g2.faces[GRAY_VULN_FACE]
        self.assertFalse(vuln.lock_applies(mk_engine().config, g2))

    def test_gray_and_colored_lock_in_play(self):
        g, d = gray48(953), colored(DieColor.GREEN, 954)
        h = Scripted(self.e, [g, d], {953: [GRAY_VULN_FACE, 0], 954: [0, 1]}, [[0, 1]])
        h.run()
        self.assertEqual(h.calls[0][0], [True, True])
        self.assertEqual(g.current_face, g.faces[GRAY_VULN_FACE])
        self.assertEqual(d.current_face, d.faces[0])
        self.assertEqual(h.p.total_rerolls_used, 0)

    def test_helix_bypass_rerolls_locked_gray(self):
        e = mk_engine(cfg_name="v049_roster")
        p = e.state.players[0]
        p.company = next(c for c in get_all_companies() if c.code == CompanyCode.HELIX)
        g = gray48(955)
        h = Scripted(e, [g], {955: [GRAY_VULN_FACE, 0]}, [[0]])
        p.bot.choose_helix_bypass = lambda *a: True
        h.run()
        self.assertEqual(g.current_face, g.faces[0])
        self.assertEqual(p.helix_bypass_uses, 1)
        self.assertEqual(p.helix_bypass_locked_rerolled, 1)


class TestV049Smoke(unittest.TestCase):
    def test_games_run_and_no_locked_reroll(self):
        viol = []
        orig_roll = Die.roll

        def roll(die, rng):
            if p1._ROLL_CTX["in_reroll"] and die.is_locked and not p1._ROLL_CTX["helix_active"]:
                viol.append(die.color)
            return orig_roll(die, rng)

        with mock.patch.object(Die, "roll", roll):
            for players in (2, 3, 4):
                for seed in range(42, 52):
                    r = mk_engine(players, seed, cfg_name="v049_roster").run_game()
                    self.assertTrue(r.rankings)
        self.assertEqual(viol, [])


if __name__ == "__main__":
    unittest.main()
