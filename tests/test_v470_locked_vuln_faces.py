"""v0.47.0 Locked ⚠ Faces tests (docs/specs/locked_vuln_faces_spec.md §10). Seeds are fixed (42 / 43 / 44 for 2P / 3P / 4P)."""

import dataclasses
import random
import unittest
from unittest import mock

from sim.bots import AdaptiveBalancedBot
from sim.bots import vulnerability_policy as vp
from sim.bots.mixed_policy import HOOK_DTYPES, MixedPolicyBot
from sim.bots.reference_search import build_portfolio
from sim.config import CubeColor, DieColor, GameConfig, VulnPolicyParams
from sim.engine import GameEngine, fast_clone, phase1_roll_deploy as p1, phase4_attack_resolution as p4
from sim.engine import vulnerability as vuln
from sim.engine.state import AbilityStatus
from sim.entities import (
    CompanyCode, Die, WhiteHatCode, create_colored_die, create_gray_die, create_white_die, get_all_companies,
    get_all_white_hats, get_random_companies, get_random_setup, get_random_white_hats,
)

G = CubeColor.GREEN
BASE_KW = dict(starting_money=6, starting_gray_dice=3, starting_purple_dice=1, starting_purple_reserve=1,
               corruption_track_profile="STANDARD", enable_corporate_asymmetry=True)
_ORIG_ROLL = Die.roll


def mk_engine(players=2, seed=42, cfg_name="v047_roster", **ov):
    rng = random.Random(seed)
    bots = [AdaptiveBalancedBot(i) for i in range(players)]
    variants, deck = get_random_setup(rng, profile="STANDARD")
    kw = dict(num_players=players, **BASE_KW)
    kw.update(ov)
    return GameEngine(config=getattr(GameConfig, cfg_name)(**kw), bots=bots, seed=seed, variant_cards=variants,
                      version_deck=deck, companies=get_random_companies(players, rng),
                      white_hats=get_random_white_hats(players, rng))


def colored(color, die_id):
    return create_colored_die(color, die_id, face_profile="V046_VULN")


def gray(die_id):
    return create_gray_die(die_id, "V046_VULN")


class Scripted:
    """Phase 1 harness: seat 0 gets ``dice`` with scripted face indices per roll; reroll picks come from ``picks``."""

    def __init__(self, e, dice, script, picks, stance="KEEP_ALL", seat=0):
        self.e, self.p = e, e.state.players[seat]
        self.dice, self.script = dice, {d.die_id: list(script.get(d.die_id, [])) for d in dice}
        self.p.ready_for_release_dice = list(dice)
        self.p.contractor_dice = []
        self.picks = list(picks)
        self.calls = []
        self.p.bot.vuln_strategy = stance
        self.p.bot.choose_yahtzee_rerolls = self._rerolls
        self.snap = []

    def _rerolls(self, player_state, active_dice, rerolls_remaining, **kw):
        self.calls.append(([d.is_locked for d in active_dice], rerolls_remaining))
        return list(self.picks.pop(0)) if self.picks else []

    def run(self, **extra):
        script = self.script
        ids = {id(d) for d in self.dice}
        phase_snap = self.snap

        def fake_roll(die, rng):
            if die.die_id in script and script[die.die_id]:
                die.chosen_choice_index = None
                die.current_face = die.faces[script[die.die_id].pop(0)]
                return die.current_face
            return _ORIG_ROLL(die, rng)

        with mock.patch.object(Die, "roll", fake_roll):
            res = self.e._execute_phase_1()
        phase_snap.append(res)
        return res


def lockable_cases():
    return [(DieColor.RED, 0), (DieColor.RED, 4), (DieColor.BLUE, 2), (DieColor.BLUE, 4), (DieColor.GREEN, 0),
            (DieColor.GREEN, 4), (DieColor.YELLOW, 0), (DieColor.YELLOW, 4), (DieColor.PURPLE, 3), (DieColor.PURPLE, 4)]


class TestConfig(unittest.TestCase):
    def test_v047_preset_values(self):
        c = GameConfig.v047_roster(num_players=3)
        self.assertTrue(c.colored_vuln_lock and c.colored_vuln_lock_secret and c.helix_bypass_once_per_game)
        self.assertEqual(c.helix_bypass_mode, "REROLL_LOCKED")
        self.assertEqual(c.die_face_profile, "V046_VULN")
        self.assertEqual(tuple(c.vuln_band_thresholds), (5, 8, 11))
        self.assertEqual(tuple(c.vuln_min_target_by_version), (5, 5, 5))
        self.assertEqual((c.power_profile, c.white_hat_6f_rebalance, c.signature_attack_mode),
                         ("V038_DRAFT", True, "dominant_color_effects"))
        self.assertTrue(c.bot_pr_push)

    def test_v047_validation(self):
        with self.assertRaises(ValueError):
            GameConfig(colored_vuln_lock=True)  # SHIELDS mode
        with self.assertRaises(ValueError):
            GameConfig.v047(helix_bypass_mode="BOGUS")
        with self.assertRaises(ValueError):
            GameConfig.v046(helix_bypass_mode="REROLL_LOCKED")
        with self.assertRaises(ValueError):
            GameConfig.v046(helix_bypass_once_per_game=True)
        with self.assertRaises(ValueError):
            GameConfig.v047(vuln_bot_params=VulnPolicyParams(lock_policy="X"))
        GameConfig.v047(colored_vuln_lock_secret=False)
        GameConfig.v047(die_face_profile="V046_VULN_NOPREMIUM")  # arm A constructs

    def test_v046_defaults_unchanged(self):
        c = GameConfig.v046()
        self.assertEqual((c.colored_vuln_lock, c.helix_bypass_mode, c.helix_bypass_once_per_game),
                         (False, "LEGACY", False))
        self.assertEqual(tuple(c.vuln_band_thresholds), (4, 7, 10))

    def test_face_table_inv_lock_12(self):
        for color in (DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW, DieColor.PURPLE):
            d = colored(color, 1)
            self.assertEqual(sum(1 for f in d.faces if f.vuln > 0), 2, color)
            self.assertTrue(all(f.vuln == 0 for f in d.faces if f.is_star))


class TestLockRule(unittest.TestCase):
    def setUp(self):
        self.e = mk_engine()

    def test_core_vuln_face_locks_after_initial_roll(self):
        for color, fi in lockable_cases():
            e = mk_engine()
            d = colored(color, 900)
            h = Scripted(e, [d], {900: [fi]}, [[0]])
            h.run()
            self.assertEqual(h.calls[0][0], [True], (color, fi))
            self.assertEqual(h.p.lock_events, 1)
            self.assertEqual(d.current_face, d.faces[fi])  # the request for the locked die was dropped

    def test_secret_face_locks_and_subflag_off(self):
        d = colored(DieColor.RED, 901)
        h = Scripted(self.e, [d], {901: [4]}, [[0]])
        h.run()
        self.assertEqual(h.calls[0][0], [True])
        e2 = mk_engine(colored_vuln_lock_secret=False)
        d2 = colored(DieColor.RED, 902)
        h2 = Scripted(e2, [d2], {902: [4, 1]}, [[0]])
        h2.run()
        self.assertEqual(h2.calls[0][0], [False])  # INV-LOCK-11: rerollable like v0.46

    def test_gray_never_locks_and_white_never_vuln_locks(self):
        g = gray(903)
        h = Scripted(self.e, [g], {903: [0, 4]}, [[0]])
        h.run()
        self.assertEqual(h.calls[0][0], [False])
        self.assertEqual(g.current_face, g.faces[4])
        w = create_white_die(904)
        for f in w.faces:
            w.current_face = f
            self.assertFalse(vuln.lock_applies(self.e.config, w))

    def test_lock_after_reroll_and_not_rerolled_again(self):
        d = colored(DieColor.BLUE, 905)
        h = Scripted(self.e, [d], {905: [1, 2, 0]}, [[0], [0]])
        h.run()
        # initial clean (1), reroll 1 -> core ⚠ (2) -> locked; the second request is dropped (no 0 roll consumed)
        self.assertEqual([c[0] for c in h.calls], [[False], [True]])
        self.assertEqual(d.current_face, d.faces[2])
        self.assertEqual(h.script[905], [0])
        self.assertEqual(h.p.total_rerolls_used, 1)

    def test_locked_request_dropped_breaks_loop(self):
        d = colored(DieColor.RED, 906)
        h = Scripted(self.e, [d], {906: [0]}, [[0], [0]])
        h.run()
        self.assertEqual(len(h.calls), 1)
        self.assertEqual(h.p.total_rerolls_used, 0)

    def test_locks_cleared_after_deploy_and_vuln_counts(self):
        d1, d2 = colored(DieColor.RED, 907), colored(DieColor.GREEN, 908)
        h = Scripted(self.e, [d1, d2], {907: [4], 908: [0]}, [[]])
        h.run()
        for p in self.e.state.players:
            for zone in (p.ready_for_release_dice, p.contractor_dice, p.in_production_dice, p.glitched_dice):
                self.assertFalse(any(x.is_locked for x in zone))
        self.assertEqual(h.p.vuln_gained_by_source.get("lockin"), 2)  # INV-LOCK-04 (final-face accounting)
        self.assertEqual(h.p.lock_dice_by_round[1], 2)
        self.assertEqual(h.p.locked_vuln_kept_by_face, {"red:5": 1, "green:1": 1} | {})

    def test_operator_contingent_die_no_vuln_lock(self):
        # a White die can show ⚠-like vuln=0 faces only; lock_applies is False for it regardless of its face
        w = create_white_die(909)
        w.current_face = w.faces[0]
        self.assertFalse(vuln.lock_applies(self.e.config, w))

    def test_lock_no_rng(self):
        e1, e2 = mk_engine(), mk_engine()
        d1, d2 = colored(DieColor.RED, 910), colored(DieColor.RED, 910)
        h1 = Scripted(e1, [d1], {910: [0]}, [[0]])
        h1.p.bot.vuln_strategy = "KEEP_ALL"
        h2 = Scripted(e2, [d2], {910: [0]}, [])
        h1.run()
        h2.run()
        self.assertEqual(e1.rng.getstate(), e2.rng.getstate())

    def test_release_l4_extra_reroll_and_gray_unaffected(self):
        g = gray(911)
        h = Scripted(self.e, [g], {911: [0, 0, 0, 4]}, [[0], [0], [0]])
        h.p.release_level = 4
        h.run()
        self.assertEqual(h.p.total_rerolls_used, 2 + int(self.e.config.release_l4_extra_rerolls))
        self.assertEqual(h.p.l4_payouts.get("release_rerolls_used", 0), int(self.e.config.release_l4_extra_rerolls))

    def test_ace_breaks_lock_and_counts_final_face(self):
        e = mk_engine()
        p = e.state.players[0]
        e.state.staging_cup[G] = 3
        p.vulnerability = 4
        pur, red = colored(DieColor.PURPLE, 912), colored(DieColor.RED, 913)
        h = Scripted(e, [pur, red], {912: [5], 913: [0]}, [])
        p.white_hat = next(w for w in get_all_white_hats() if w.code == WhiteHatCode.PRODIGY)
        with mock.patch.object(vp, "choose_ace_target", return_value=(1, red.faces[1])) as spy:
            h.run()
        self.assertIsInstance(spy.call_args.args[3], set)  # game_state and excluded_targets are passed under the lock
        self.assertEqual(h.calls[0][0], [False, True])
        self.assertEqual(p.vuln_gained_by_source.get("lockin", 0), 0)  # ⚠ counts on the final face (ACE turned it clean)
        self.assertEqual(p.ace_lock_breaks, 1)
        self.assertEqual(red.current_face.vuln, 0)


class TestHelix(unittest.TestCase):
    def _helix(self, **ov):
        e = mk_engine(**ov)
        p = e.state.players[0]
        p.company = next(c for c in get_all_companies() if c.code == CompanyCode.HELIX)
        return e, p

    def test_reroll_locked_dice_no_extra_reroll_no_face_set(self):
        e, p = self._helix()
        d = colored(DieColor.RED, 920)
        h = Scripted(e, [d], {920: [0, 1]}, [[0]])
        p.bot.choose_helix_bypass = lambda *a: True
        spy = mock.Mock(return_value=None)
        p.bot.choose_helix_face_override_v038 = spy
        p.bot.choose_helix_override = mock.Mock(return_value=True)
        h.run()
        self.assertEqual(d.current_face, d.faces[1])
        self.assertEqual(p.helix_bypass_uses, 1)
        self.assertEqual(p.helix_bypass_locked_rerolled, 1)
        spy.assert_not_called()
        p.bot.choose_helix_override.assert_not_called()
        self.assertEqual(h.calls[0][1], e.config.default_free_rerolls)  # no +1
        self.assertEqual(p.helix_bypass_vuln_removed, 1)
        self.assertTrue(p.helix_bypass_used_game)

    def test_offered_per_step_and_not_without_locks(self):
        e, p = self._helix()
        offers = []
        p.bot.choose_helix_bypass = lambda pl, dice, rr, st: offers.append(rr) or False
        d1, d2 = colored(DieColor.BLUE, 921), colored(DieColor.RED, 922)
        h = Scripted(e, [d1, d2], {921: [1, 2], 922: [1]}, [[0], []])
        h.run()
        # no lock at step 1 (no offer); die 1 locks after reroll 1 -> offered at step 2 with 1 reroll left
        self.assertEqual(offers, [1])
        e2, p2 = self._helix()
        offers2 = []
        p2.bot.choose_helix_bypass = lambda *a: offers2.append(1) or False
        Scripted(e2, [colored(DieColor.RED, 923)], {923: [1]}, [[]]).run()
        self.assertEqual(offers2, [])

    def test_once_per_game_and_per_version_control(self):
        e, p = self._helix()
        p.helix_bypass_used_game = True
        self.assertFalse(p.is_helix_bypass_available("v1.0"))
        e2, p2 = self._helix(helix_bypass_once_per_game=False)
        p2.helix_bypass_used_game = True
        self.assertTrue(p2.is_helix_bypass_available("v1.0"))
        p2.mark_ability_used("v1.0")
        self.assertFalse(p2.is_helix_bypass_available("v1.0"))
        p2.ability_v2_status = AbilityStatus.AVAILABLE
        self.assertTrue(p2.is_helix_bypass_available("v2.0"))  # per-version control: the game flag does not block
        p.ability_v2_status = AbilityStatus.AVAILABLE
        self.assertFalse(p.is_helix_bypass_available("v2.0"))  # once per game: used in v1.0 blocks v2.0 / v3.0

    def test_black_burns_unused_helix_bypass_then_costs_two(self):
        e, p = self._helix()
        s0 = p.secrets
        p4._resolve_signature_black(e, p)
        self.assertEqual((p.secrets, p.helix_bypass_used_game, p.helix_bypass_lost_to_black), (s0, True, 1))
        p4._resolve_signature_black(e, p)
        self.assertEqual(p.secrets, s0 - 2)
        self.assertEqual(p.helix_bypass_lost_to_black, 1)

    def test_black_after_helix_use_costs_two(self):
        e, p = self._helix()
        p.helix_bypass_used_game = True
        s0 = p.secrets
        p4._resolve_signature_black(e, p)
        self.assertEqual(p.secrets, s0 - 2)

    def test_black_dto_unchanged(self):
        e = mk_engine()
        p = e.state.players[0]
        p.company = next(c for c in get_all_companies() if c.code == CompanyCode.DTO)
        s0 = p.secrets
        p4._resolve_signature_black(e, p)
        self.assertEqual((p.secrets, p.dto_slush_fund_used, p.helix_bypass_lost_to_black), (s0, True, 0))

    def test_legacy_helix_unchanged_under_v046(self):
        e = mk_engine(cfg_name="v046_roster")
        p = e.state.players[0]
        p.company = next(c for c in get_all_companies() if c.code == CompanyCode.HELIX)
        p.bot.choose_helix_override = mock.Mock(return_value=True)
        p.bot.choose_helix_bypass = mock.Mock(side_effect=AssertionError("v0.47 hook under LEGACY"))
        d = gray(924)
        Scripted(e, [d], {924: [3]}, []).run()
        p.bot.choose_helix_override.assert_called_once()
        self.assertEqual(p.helix_bypass_uses, 0)

    def test_helix_bypass_default_triggers_on_band_cross(self):
        e = mk_engine()
        p, s = e.state.players[0], e.state
        s.vuln_p1_snapshot = {}
        s.staging_cup[G] = 3
        p.vuln_stance_this_round = "ADAPTIVE"
        blue, red = colored(DieColor.BLUE, 1), colored(DieColor.RED, 2)
        blue.current_face, red.current_face = blue.faces[2], red.faces[0]  # two locked core ⚠ faces
        blue.is_locked = red.is_locked = True
        p.vulnerability = 3  # tab 5 -> the locked ⚠ cross the v0.47 band-1 / min-target value 5
        self.assertTrue(vp.helix_bypass_default(p, [blue, red], 2, s))
        p.vulnerability = 0  # tab 2: no crossing
        self.assertFalse(vp.helix_bypass_default(p, [blue, red], 2, s))
        self.assertFalse(vp.helix_bypass_default(p, [blue, red], 0, s))  # no rerolls left
        s.is_final_round = False
        p.vulnerability = 3
        p.vuln_stance_this_round = "KEEP_ALL"
        self.assertFalse(vp.helix_bypass_default(p, [blue, red], 2, s))

    def test_mixed_hook_dtype_helix_bypass(self):
        self.assertEqual(HOOK_DTYPES["choose_helix_bypass"], "phase1_roll")
        self.assertTrue(hasattr(MixedPolicyBot, "choose_helix_bypass"))


class TestBots(unittest.TestCase):
    def setUp(self):
        self.e = mk_engine()
        self.p, self.s = self.e.state.players[0], self.e.state
        self.s.vuln_p1_snapshot = {}
        self.p.vuln_stance_this_round = "ADAPTIVE"

    def _pool(self, vulns_on_table):
        """A clean Blue die (index 0) plus Gray dice showing ⚠ faces (kept on the table)."""
        dice = [colored(DieColor.BLUE, 1)]
        dice[0].current_face = dice[0].faces[1]
        for k in range(vulns_on_table):
            g = colored(DieColor.RED, 10 + k)  # a locked core ⚠ stays on the table
            g.current_face, g.is_locked = g.faces[0], True
            dice.append(g)
        return dice

    def _cfg(self, policy):
        object.__setattr__(self.s.config, "vuln_bot_params", dataclasses.replace(self.s.config.vuln_bot_params, lock_policy=policy))

    def test_aware_rule_uses_config_crossings(self):
        self._cfg("AWARE")
        self.p.vulnerability = 1
        dice = self._pool(3)  # tab 4 -> +1 = 5 is a v0.47 crossing
        self.assertEqual(vp.adjust_rerolls(self.p.bot, self.p, dice, [0], self.s, 2), [])
        self.p.vulnerability = 0  # tab 3 -> 4 not a crossing
        self.assertEqual(vp.adjust_rerolls(self.p.bot, self.p, dice, [0], self.s, 2), [0])
        # v0.46 thresholds (4, 7, 10), min 4: tab 4 -> 5 is not a crossing
        e46 = mk_engine(cfg_name="v046_roster")
        p46, s46 = e46.state.players[0], e46.state
        s46.vuln_p1_snapshot = {}
        p46.vuln_stance_this_round = "ADAPTIVE"
        object.__setattr__(s46.config, "colored_vuln_lock", True)
        object.__setattr__(s46.config, "vuln_bot_params", dataclasses.replace(s46.config.vuln_bot_params, lock_policy="AWARE"))
        p46.vulnerability = 1
        self.assertEqual(vp.adjust_rerolls(p46.bot, p46, self._pool(3), [0], s46, 2), [0])

    def test_lambda_rule_and_margin(self):
        self._cfg("LAMBDA")
        self.s.staging_cup[G] = 3
        self.p.secrets = 6
        near = self._pool(3)
        self.p.vulnerability = 1
        got_near = vp.adjust_rerolls(self.p.bot, self.p, near, [0], self.s, 2)
        self.p.vulnerability = 0
        far = self._pool(0)
        got_far = vp.adjust_rerolls(self.p.bot, self.p, far, [0], self.s, 2)
        self.assertEqual(got_far, [0])
        self.assertLessEqual(len(got_near), len(got_far))
        # a huge margin always drops, a hugely negative one never does
        self._cfg("LAMBDA")
        object.__setattr__(self.s.config, "vuln_bot_params", dataclasses.replace(
            self.s.config.vuln_bot_params, lock_reroll_margin=1e6))
        self.assertEqual(vp.adjust_rerolls(self.p.bot, self.p, far, [0], self.s, 2), [])
        object.__setattr__(self.s.config, "vuln_bot_params", dataclasses.replace(
            self.s.config.vuln_bot_params, lock_reroll_margin=-1e6))
        self.assertEqual(vp.adjust_rerolls(self.p.bot, self.p, near, [0], self.s, 2), [0])

    def test_lambda_aware_superset(self):
        self.s.staging_cup[G] = 2
        rnd = random.Random(1)
        for _ in range(40):
            dice = [colored(rnd.choice([DieColor.RED, DieColor.BLUE, DieColor.GREEN]), 50 + i) for i in range(4)]
            for d in dice:
                d.current_face = rnd.choice([f for f in d.faces if f.vuln == 0])
                d.is_locked = False
            self.p.vulnerability = rnd.randint(0, 6)
            res = {}
            for pol in ("AWARE", "LAMBDA_AWARE"):
                self._cfg(pol)
                res[pol] = set(vp.adjust_rerolls(self.p.bot, self.p, dice, [0, 1, 2, 3], self.s, 2))
            self.assertLessEqual(res["LAMBDA_AWARE"], res["AWARE"])

    def test_no_color_reroll_and_star_chase_stances(self):
        self.p.vulnerability = 0
        blue = colored(DieColor.BLUE, 1)
        blue.current_face = blue.faces[1]
        star = colored(DieColor.RED, 2)
        star.current_face = star.faces[5]
        g = gray(3)
        g.current_face = g.faces[4]
        dice = [blue, star, g]
        self.p.vuln_stance_this_round = "NO_COLOR_REROLL"
        stats = {}
        self.assertEqual(vp.adjust_rerolls(self.p.bot, self.p, dice, [0, 1, 2], self.s, 2, stats=stats), [2])
        self.assertEqual(stats["no_color"], 2)
        self.p.vuln_stance_this_round = "STAR_CHASE"
        self.assertEqual(vp.adjust_rerolls(self.p.bot, self.p, dice, [2], self.s, 2), [0, 2])
        self.assertIn("NO_COLOR_REROLL", vp.STRATEGIES)

    def test_adjust_rerolls_unchanged_when_lock_off(self):
        e = mk_engine(cfg_name="v046_roster")
        p, s = e.state.players[0], e.state
        s.vuln_p1_snapshot = {}
        rnd = random.Random(7)
        for strat in ("ADAPTIVE", "REROLL_ALL", "PEN_TEST_RUSH", "KAMIKAZE", "KEEP_ALL"):
            p.vuln_stance_this_round = strat
            for _ in range(40):
                dice = []
                for i in range(5):
                    d = rnd.choice([lambda n: gray(n), lambda n: colored(DieColor.RED, n)])(60 + i)
                    d.current_face = rnd.choice(d.faces)
                    d.is_locked = rnd.random() < 0.2
                    dice.append(d)
                p.vulnerability = rnd.randint(0, 8)
                idx = [i for i in range(5) if rnd.random() < 0.5]
                a = vp.adjust_rerolls(p.bot, p, dice, list(idx), s, 2)
                b = vp.adjust_rerolls(p.bot, p, dice, list(idx), s, 2, stats={})
                self.assertEqual(a, b)

    def test_ace_prefers_locked_core_vuln(self):
        self.s.vuln_p1_snapshot = {}
        self.s.staging_cup[G] = 3
        pur = colored(DieColor.PURPLE, 1)
        pur.current_face = pur.faces[5]
        red = colored(DieColor.RED, 2)
        red.current_face, red.is_locked = red.faces[0], True
        self.p.vulnerability = 4  # one more ⚠ would cross the min target
        r = vp.choose_ace_target(self.p, [pur, red], self.s, set())
        self.assertIsNotNone(r)
        self.assertEqual(r[0], 1)
        self.assertEqual(r[1].vuln, 0)
        self.assertFalse(r[1].is_star or r[1].secrets_pending)
        self.assertIsNone(vp.choose_ace_target(self.p, [pur, red], self.s, {1}))  # excluded
        self.assertIsNone(vp.choose_ace_target(self.p, [pur], self.s, set()))  # the lone Purple star is not a target

    def test_pen_policy_floor_relative(self):
        from sim.bots.base import Phase3ActionPlan

        def plan_for(cfg_name, **ov):
            e = mk_engine(cfg_name=cfg_name)
            p, s = e.state.players[0], e.state
            for k, v in ov.items():
                object.__setattr__(s.config, k, v)
            p.vuln_stance_this_round = "ADAPTIVE"
            p.research_tokens = 20
            p.vulnerability = 5
            for q in s.players[1:]:
                q.vulnerability = 0
            s.staging_cup[G] = 1
            plan = vp.apply_pen_test_policy(p.bot, Phase3ActionPlan(), p, s)
            return plan.pen_test

        base = plan_for("v046_roster")
        flag_on_floor4 = plan_for("v046_roster", vuln_bot_params=VulnPolicyParams(pen_relative_to_floor=True))
        self.assertEqual(base, flag_on_floor4)  # floor 4: identity
        on = plan_for("v047_roster")  # floor 5: thresholds shift +1
        off = plan_for("v047_roster", vuln_bot_params=VulnPolicyParams(pen_relative_to_floor=False))
        self.assertLessEqual(on, off)

    def test_ref1_portfolio(self):
        a = [n for n, _ in build_portfolio(0, vulnerability=True)]
        b = [n for n, _ in build_portfolio(0, vulnerability=True, locked=True)]
        self.assertEqual(b[:len(a)], a)
        self.assertEqual(b[len(a):], ["AdaptiveBalanced[no_color_reroll]", "AdaptiveBalanced[star_chase]"])
        self.assertEqual([n for n, _ in build_portfolio(0)], a[:-3])


class TestTelemetryAndDeterminism(unittest.TestCase):
    def _digest(self, res):
        return (res.end_reason, res.total_rounds, list(res.winner_ids),
                [(r["player_id"], r["secrets"], r["money"]) for r in res.rankings])

    def test_v047_row_only_under_lock(self):
        r47 = mk_engine(2, 42).run_game()
        r46 = mk_engine(2, 42, cfg_name="v046_roster").run_game()
        self.assertTrue(all("lock_events" in r for r in r47.rankings))
        self.assertFalse(any("lock_events" in r or "helix_bypass_uses" in r for r in r46.rankings))

    def test_lock_telemetry_counts(self):
        e = mk_engine()
        a, b, c = colored(DieColor.RED, 940), colored(DieColor.BLUE, 941), colored(DieColor.PURPLE, 942)
        g = gray(943)
        h = Scripted(e, [a, b, c, g], {940: [4], 941: [5], 942: [3], 943: [0]}, [[]])
        h.run()
        p = h.p
        self.assertEqual(p.lock_events, 2)
        self.assertEqual(p.lock_events_by_face, {"red:5": 1, "purple:4": 1})
        self.assertEqual(p.lock_dice_by_round[1], 2)
        self.assertEqual(p.vuln_kept_by_source, {"secret": 1, "core": 1, "gray": 1})
        self.assertEqual(p.colored_dice_rolled_by_color, {"red": 1, "blue": 1, "purple": 1})
        self.assertEqual(p.colored_star_by_color, {"blue": 1})

    def test_v047_determinism_and_fast_clone(self):
        for players, seed in ((2, 42), (3, 43), (4, 44)):
            a = self._digest(mk_engine(players, seed).run_game())
            b = self._digest(mk_engine(players, seed).run_game())
            self.assertEqual(a, b)
            e = mk_engine(players, seed)
            e.run_round()
            clone, _ = fast_clone.clone_engine(e)
            self.assertEqual(self._digest(e.run_game()), self._digest(clone.run_game()))

    def test_v047_smoke_invariants(self):
        """INV-LOCK-01/-02/-03/-05/-06 across 20 games per pod (lock_in wrapper + Die.roll wrapper)."""
        viol = []
        orig_roll, orig_lock = Die.roll, vuln.lock_in

        def roll(die, rng):
            if p1._ROLL_CTX["in_reroll"] and die.is_locked and not p1._ROLL_CTX["helix_active"]:
                viol.append("INV-LOCK-01")
            return orig_roll(die, rng)

        def lock_in(engine, p, dice):
            for d in dice:
                if vuln.lock_applies(engine.config, d) and not d.is_locked:
                    viol.append("INV-LOCK-02")
                if d.color in (DieColor.GRAY, DieColor.WHITE) and d.is_locked and not d.current_face.is_glitch:
                    viol.append("INV-LOCK-02 gray")
            return orig_lock(engine, p, dice)

        with mock.patch.object(Die, "roll", roll), mock.patch.object(vuln, "lock_in", lock_in):
            for players in (2, 3, 4):
                for seed in range(42, 62):
                    e = mk_engine(players, seed)
                    r = e.run_game()
                    for p in e.state.players:
                        if p.helix_bypass_uses + p.helix_bypass_lost_to_black > 1:
                            viol.append("INV-LOCK-05/06")
                        for zone in (p.in_production_dice, p.glitched_dice, p.ready_for_release_dice):
                            if any(d.is_locked for d in zone):
                                viol.append("INV-LOCK-03")
        self.assertEqual(viol, [])


if __name__ == "__main__":
    unittest.main()
