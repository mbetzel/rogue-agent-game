"""v0.48 Sprint Plan & Gray Legacy Rotation (docs/specs/sprint_plan_spec.md §15): TC-SP-01..29, INV-SP-01..20."""

from __future__ import annotations

import unittest
from typing import Any, Dict, List, Optional

from scripts.run_v380_secret_faces_sweep import build_engine
from sim.bots import research_policy as rp
from sim.bots.base import BaseBot
from sim.config import DieColor, GameConfig
from sim.engine import fast_clone, phase1_roll_deploy, phase5_pipeline_shift as p5, research_tracks as rt
from sim.engine import sprint_plan as sp, vulnerability as vuln
from sim.engine.research_tracks import BreakthroughChoice
from sim.entities import COMPANIES, CompanyCode, Die, create_colored_die, create_gray_die


def mk(players: int = 3, seed: int = 42, preset: str = "v048", **ov: Any):
    return build_engine(preset, "mixed1", players, seed, ov)


def gray(eng, did: int) -> Die:
    return create_gray_die(did, eng.config.gray_face_profile)


def colored(eng, did: int, color: DieColor = DieColor.RED, cost: int = 4) -> Die:
    return create_colored_die(color=color, die_id=did, cost=cost, face_profile=eng.config.die_face_profile)


def clear_pipeline(p) -> None:
    for z in (p.ready_for_release_dice, p.in_production_dice, p.glitched_dice, p.scanned_dice):
        z.clear()
    p.current_sprint_ids = set()


def set_sprint(eng, p, cur: List[Die], nxt: List[Die], bw: Optional[int] = None) -> None:
    clear_pipeline(p)
    p.scanned_dice.extend(cur + nxt)
    sp.mark_current(p, cur)
    if bw is not None:
        p.release_bandwidth = bw
        p.temp_release_bandwidth_bonus = 0


class StubBot(BaseBot):
    """Deterministic test bot: configurable hooks, REROLL_ALL stance, asks for every reroll."""

    def __init__(self, bot_id: int = 0):
        super().__init__(bot_id, "StubBot")
        self.vuln_strategy = "REROLL_ALL"
        self.grad: Any = None
        self.thin: Any = None
        self.helix = False
        self.reroll_all = True

    def choose_yahtzee_rerolls(self, player_state, active_dice, rerolls_remaining, *a, **k):
        return list(range(len(active_dice))) if self.reroll_all else []

    def choose_helix_override(self, *a, **k):
        return self.helix

    def choose_sprint_graduates(self, player, current, next_, bw, game_state=None, rng=None):
        if self.grad is not None:
            return self.grad(player, current, next_, bw)
        return super().choose_sprint_graduates(player, current, next_, bw, game_state, rng)

    def choose_thin_gray(self, player, state, candidates):
        return self.thin(candidates) if self.thin else super().choose_thin_gray(player, state, candidates)


def with_stub(eng, pid: int = 0) -> StubBot:
    b = StubBot(pid)
    b.player_id = pid
    eng.state.players[pid].bot = b
    return b


# ------------------------------------------------------------------------------------------------ config
class TestConfig(unittest.TestCase):
    def test_tc_sp_01_v048_values_and_v046_defaults(self):
        c = GameConfig.v048(num_players=3)
        self.assertTrue(c.sprint_plan_enabled)
        self.assertEqual(c.starting_current_sprint_gray, 3)
        self.assertEqual((c.gray_face_profile, c.vuln_face_lock), ("V048_SPRINT", "GRAY"))
        self.assertEqual(c.starting_secrets_by_player_count, {2: 6, 3: 6, 4: 6})
        self.assertEqual((c.pen_test_l1, c.triage_l1_breakthrough, c.release_l1_breakthrough),
                         ("SECRET", "CASH", "BANDWIDTH"))
        self.assertEqual((c.pen_test_l3_breakthrough, c.release_l3_breakthrough), ("THIN_GRAY", "THIN_GRAY"))
        self.assertEqual((c.pen_test_l1_secrets, c.triage_l1_cash, c.release_l1_bandwidth), (1, 2, 1))
        self.assertEqual(c.bot_research_mode, "LEGACY")
        self.assertEqual(GameConfig.v048_roster(num_players=3).bot_research_mode, "THINNING_AWARE")
        self.assertEqual(GameConfig.v048_roster(num_players=3).bot_thin_tracks, ("RELEASE",))
        d = GameConfig.v046(num_players=3)
        self.assertEqual((d.sprint_plan_enabled, d.starting_current_sprint_gray, d.vuln_face_lock), (False, 0, "NONE"))
        self.assertEqual((d.pen_test_l1, d.triage_l1_breakthrough, d.release_l1_breakthrough),
                         ("GRAY_DIE", "GRAY_DIE", "GRAY_DIE"))
        self.assertEqual((d.pen_test_l3_breakthrough, d.release_l3_breakthrough), ("SECRET", "SECRET"))
        self.assertEqual((d.bot_research_mode, d.bot_research_rush, d.bot_thin_gray_floor), ("LEGACY", "none", 3))
        self.assertEqual(d.gray_face_profile, "V046_VULN")

    def test_tc_sp_01_validation_errors(self):
        bad = [
            dict(purchased_dice_to_scanned=False), dict(starting_current_sprint_gray=-1),
            dict(starting_current_sprint_gray=True), dict(vuln_face_lock="ALL"), dict(vuln_face_lock="x"),
            dict(release_l1_breakthrough="x"), dict(pen_test_l3_breakthrough="x"), dict(release_l3_breakthrough="x"),
            dict(bot_research_mode="x"), dict(bot_research_rush="x"), dict(bot_thin_tracks=("RELEASE", "RELEASE")),
            dict(bot_thin_tracks=("TRIAGE",)), dict(pen_test_l1_secrets=-1), dict(triage_l1_cash=-1),
            dict(release_l1_bandwidth=-1), dict(bot_thin_gray_floor=-1), dict(triage_l1_breakthrough="x"),
            dict(pen_test_l1="x"),
        ]
        for ov in bad:
            with self.assertRaises(ValueError, msg=str(ov)):
                GameConfig.v048(num_players=3, **ov)
        for ov in (dict(sprint_plan_enabled=True), dict(starting_current_sprint_gray=1), dict(vuln_face_lock="GRAY"),
                   dict(gray_face_profile="V048_SPRINT")):
            with self.assertRaises(ValueError, msg=str(ov)):  # v045 is not a Vulnerability Track preset
                GameConfig.v045(num_players=3, **ov)
        with self.assertRaises(ValueError):
            GameConfig.v046(num_players=3, starting_current_sprint_gray=3)

    def test_tc_sp_02_gray_table_inv_sp_11(self):
        c = GameConfig.v048(num_players=3)
        g47, g46 = gray_faces(c.gray_face_profile), gray_faces("V046_VULN")
        self.assertEqual([f.name for f in g47], ["+$1 & +1 🔬", "+2 🔬", "+$2 / +2 🔬 ⚠", "+$1 / +1 🔬", "+$1", "+1 🔬"])
        self.assertEqual([vuln.face_vuln(f) for f in g47], [0, 0, 1, 0, 0, 0])
        self.assertEqual(sum(vuln.face_vuln(f) for f in g47), 1)
        for a, b in zip(g47, g46):  # payouts equal face for face
            self.assertEqual((a.money, a.patches, a.is_choice), (b.money, b.patches, b.is_choice))
            self.assertEqual([(x.money, x.patches) for x in a.choices], [(x.money, x.patches) for x in b.choices])
        self.assertEqual(sum(vuln.face_vuln(f) for f in gray_faces("V046_VULN")), 3)  # v046 table untouched


def gray_faces(profile: str):
    return create_gray_die(1, profile).faces


# ------------------------------------------------------------------------------------------------ setup
class TestSetup(unittest.TestCase):
    def test_tc_sp_03_setup_inv_sp_12(self):
        for players in (2, 3, 4):
            for seed in (42, 43, 44, 45, 46, 47, 48, 49):
                e = mk(players, seed)
                ds = e.state.version_deck[0].directive_code == "DATA_SCRAPER"
                expected = 6 + (1 if ds else 0)
                top_id = 0
                for p in e.state.players:
                    ready_gray = [d for d in p.ready_for_release_dice if d.color == DieColor.GRAY]
                    self.assertEqual(len(ready_gray), 2)
                    self.assertEqual(len(p.ready_for_release_dice), 4)  # 2 Gray + company die + Purple
                    self.assertEqual(sum(d.color == DieColor.PURPLE for d in p.ready_for_release_dice), 1)
                    cur = sp.current_sprint(p)
                    self.assertEqual(len(cur), 3)
                    self.assertTrue(all(d.color == DieColor.GRAY for d in cur))
                    self.assertEqual(sp.next_sprint(p), [])
                    self.assertEqual(len(sp.owned_gray(p)), 5)
                    self.assertEqual(p.secrets_by_source["starting"], p.secrets)
                    self.assertGreaterEqual(p.secrets, expected)
                    top_id = max(top_id, max(d.die_id for d in p.ready_for_release_dice))
                # Current ids are post-setup and in seat order
                ids = [d.die_id for p in e.state.players for d in sp.current_sprint(p)]
                self.assertEqual(ids, sorted(ids))
                self.assertGreater(min(ids), top_id)
                self.assertEqual(e.state.next_die_id, max(ids) + 1)
        e = mk(3, 42, preset="v046")
        for p in e.state.players:
            self.assertEqual((p.current_sprint_ids, len(p.scanned_dice)), (set(), 0))  # INV-SP-01 flag off

    def test_tc_sp_03_secrets(self):
        for seed in range(42, 60):
            e = mk(3, seed)
            ds = e.state.version_deck[0].directive_code == "DATA_SCRAPER"
            for p in e.state.players:
                comp_sec = getattr(p.company, "starting_secrets_bonus", 0) if getattr(e.config, "company_setup_bonuses", True) else 0
                self.assertEqual(p.secrets, 6 + (1 if ds else 0) + (comp_sec or 0))


# ------------------------------------------------------------------------------------------------ Production Return / Sprint Review
class TestSprintReview(unittest.TestCase):
    def setUp(self):
        self.e = mk(3, 42)
        self.p = self.e.state.players[0]
        self.b = with_stub(self.e)

    def _prod(self, dice):
        self.p.in_production_dice[:] = dice

    def test_tc_sp_04_production_return_current_empty(self):
        a, b, c = self.p.in_production_dice[:], gray(self.e, 501), gray(self.e, 502)
        set_sprint(self.e, self.p, [], [b])
        self._prod([c])
        p5.production_return_to_scanned(self.e, self.p)
        self.assertEqual({d.die_id for d in sp.current_sprint(self.p)}, {502})
        self.assertEqual([d.die_id for d in sp.next_sprint(self.p)], [501])  # Next keeps its dice
        self.assertEqual(self.e.state.sprint_round["sprint_prod_to_current_by_player"][0], True)

    def test_tc_sp_05_production_return_current_nonempty(self):
        cur, nxt, ret = gray(self.e, 501), gray(self.e, 502), colored(self.e, 503)
        set_sprint(self.e, self.p, [cur], [nxt])
        self._prod([ret])
        p5.production_return_to_scanned(self.e, self.p)
        self.assertEqual([d.die_id for d in sp.current_sprint(self.p)], [501])
        self.assertEqual({d.die_id for d in sp.next_sprint(self.p)}, {502, 503})
        self.assertEqual(self.e.state.sprint_round["sprint_prod_to_current_by_player"][0], False)

    def test_tc_sp_04_stale_id_pruned_before_return(self):
        """INV-SP-02: a stale Current id (die removed earlier) counts as empty Current."""
        stale = gray(self.e, 501)
        set_sprint(self.e, self.p, [stale], [])
        self.p.scanned_dice.clear()  # removal path leaves the id behind
        ret = colored(self.e, 503)
        self._prod([ret])
        p5.production_return_to_scanned(self.e, self.p)
        self.assertEqual(self.p.current_sprint_ids, {503})

    def _review(self, cur, nxt, bw, chosen=None):
        set_sprint(self.e, self.p, cur, nxt, bw)
        return sp.sprint_review(self.e, self.p, chosen)

    def test_tc_sp_06_review_forced_plus_next(self):
        cur = [gray(self.e, 501), gray(self.e, 502)]
        nxt = [gray(self.e, 503), colored(self.e, 504, cost=5), create_colored_die(color=DieColor.PURPLE, die_id=505, cost=0)]
        out = self._review(cur, nxt, 4)
        self.assertEqual([d.die_id for d in out], [501, 502, 505, 504])  # Current, then Next by priority
        self.assertEqual([d.die_id for d in self.p.ready_for_release_dice], [501, 502, 505, 504])
        self.assertEqual([d.die_id for d in self.p.scanned_dice], [503])
        self.assertEqual(self.p.current_sprint_ids, {503})  # INV-SP-01

    def test_tc_sp_07_current_equals_bw(self):
        cur = [gray(self.e, 500 + i) for i in range(4)]
        nxt = [colored(self.e, 510)]
        self.b.grad = lambda p, c, n, bw: ([d.die_id for d in c], [510])  # hook asks for a Next pick anyway
        out = self._review(cur, nxt, 4)
        self.assertEqual({d.die_id for d in out}, {500, 501, 502, 503})
        self.assertEqual([d.die_id for d in self.p.scanned_dice], [510])

    def test_tc_sp_08_current_over_bw(self):
        cur = [gray(self.e, 500 + i) for i in range(5)] + [colored(self.e, 505)]
        nxt = [colored(self.e, 506)]
        self.b.grad = lambda p, c, n, bw: ([505, 500, 501, 502], [])
        out = self._review(cur, nxt, 4)
        self.assertEqual([d.die_id for d in out], [505, 500, 501, 502])
        self.assertEqual(self.p.current_sprint_ids, {503, 504, 506})  # leftovers + all Next become Current

    def test_tc_sp_09_invalid_hook_output(self):
        cur = [gray(self.e, 500 + i) for i in range(3)] + [colored(self.e, 503)]
        nxt = [gray(self.e, 510), gray(self.e, 511)]
        # hook: short list for Current (back-filled to forced); Next ids that are cross-sprint / duplicate / unknown
        self.b.grad = lambda p, c, n, bw: ([500], [500, 510, 510, 9999])
        out = self._review(cur, nxt, 5)  # 4 Current forced, 1 spare
        ids = [d.die_id for d in out]
        self.assertEqual(ids[0], 500)
        self.assertEqual(set(ids[:4]), {500, 501, 502, 503})  # Current back-filled to forced
        self.assertEqual(ids[4:], [510])  # Next capped at spare, no cross-sprint / duplicate
        # a short Next list is back-filled: full Release Bandwidth is mandatory (User ruling 2026-11-19)
        self.b.grad = lambda p, c, n, bw: ([d.die_id for d in c], [])
        out = self._review([gray(self.e, 600)], [gray(self.e, 601), gray(self.e, 602)], 4)
        self.assertEqual(sorted(d.die_id for d in out), [600, 601, 602])

    def test_tc_sp_10_explicit_chosen_and_check_picks(self):
        cur = [gray(self.e, 500), gray(self.e, 501)]
        nxt = [gray(self.e, 510), gray(self.e, 511), gray(self.e, 512)]
        out = self._review(cur, nxt, 3, chosen=[512, 501, 500, 9999])  # split by membership; unknown ignored
        self.assertEqual([d.die_id for d in out], [501, 500, 512])
        set_sprint(self.e, self.p, cur, nxt, 2)  # |Cur| == BW: Next picks illegal
        self.assertEqual(sp.check_picks(self.p, [500, 501], []), [])
        errs = sp.check_picks(self.p, [500, 501], [510])
        self.assertTrue(any("no spare" in x for x in errs))
        self.assertTrue(any("unknown" in x for x in sp.check_picks(self.p, [500, 9999], [])))
        self.assertTrue(any("not in the Current Sprint" in x for x in sp.check_picks(self.p, [500, 510], [])))
        self.assertTrue(any("exactly 2" in x for x in sp.check_picks(self.p, [500], [])))
        self.assertTrue(any("duplicate" in x for x in sp.check_picks(self.p, [500, 500], [])))
        set_sprint(self.e, self.p, cur[:1], nxt, 3)  # 1 Current, 2 spare
        self.assertEqual(sp.check_picks(self.p, [500], [510, 511]), [])
        self.assertTrue(sp.check_picks(self.p, [500], [510, 511, 512]))
        self.assertTrue(any("must graduate exactly 2 Next" in x for x in sp.check_picks(self.p, [500], [510])))

    def test_tc_sp_11_bandwidth_bonuses_inv_sp_08(self):
        cur = [gray(self.e, 500 + i) for i in range(5)]
        set_sprint(self.e, self.p, cur, [], 4)
        self.assertEqual(sp.forced_count(self.p), 4)
        self.p.temp_release_bandwidth_bonus = 1  # Jumper Diagnostics
        self.assertEqual(sp.forced_count(self.p), 5)
        self.p.temp_release_bandwidth_bonus = 0
        # Release L1 raises the cap via the Breakthrough and is reset at round end (with Jumper)
        rt.resolve_breakthrough(self.e, self.p, "RELEASE", 1)
        self.assertEqual((self.p.temp_release_bandwidth_bonus, self.p.release_l1_bw_bonus_this_round), (1, 1))
        self.assertEqual(self.p.effective_release_bandwidth, 5)
        self.assertEqual(len(sp.sprint_review(self.e, self.p)), 5)
        e = mk(3, 43)
        for pl in e.state.players:
            pl.temp_release_bandwidth_bonus = 2
            pl.release_l1_bw_bonus_this_round = 1
        e.run_round()
        self.assertTrue(all(pl.temp_release_bandwidth_bonus == 0 and pl.release_l1_bw_bonus_this_round == 0
                            for pl in e.state.players))


# ------------------------------------------------------------------------------------------------ entry / removal paths
class TestPaths(unittest.TestCase):
    def setUp(self):
        self.e = mk(3, 42)
        self.p = self.e.state.players[0]
        with_stub(self.e)

    def _review_then(self):
        set_sprint(self.e, self.p, [gray(self.e, 700)], [], 4)
        sp.sprint_review(self.e, self.p)

    def test_tc_sp_12_triage_lands_in_next(self):
        self._review_then()
        d = colored(self.e, 701)
        d.secret_pending = False
        self.p.glitched_dice.append(d)
        self.p.triage_bandwidth = 2
        p5.conveyor_triage_v038(self.e, self.p)
        self.assertIn(701, [x.die_id for x in sp.next_sprint(self.p)])
        self.assertNotIn(701, self.p.current_sprint_ids)

    def test_tc_sp_12_pr_l3_purple_lands_in_next(self):
        self._review_then()
        self.assertTrue(self.e.config.pr_l3_purple_to_scanned)
        self.p.personal_purple_reserve = 1
        rec = rt.resolve_breakthrough(self.e, self.p, "PATENT", 3)
        self.assertEqual(rec.outcome, "TAKEN")
        self.assertIn(rec.detail["die_id"], [x.die_id for x in sp.next_sprint(self.p)])

    def test_tc_sp_12_blue_signature_gray_then_triage(self):
        from sim.engine.phase4_attack_resolution import _resolve_signature_blue

        self._review_then()
        self.p.ready_for_release_dice.append(gray(self.e, 702))
        n_gray = len(sp.owned_gray(self.p))
        _resolve_signature_blue(self.e, self.p)  # first Gray in scanned_dice order (the Current Gray) -> R&D
        self.assertEqual(len(self.p.glitched_dice), 1)
        moved = self.p.glitched_dice[0]
        self.assertEqual(len(sp.owned_gray(self.p)), n_gray)
        sp.prune(self.p)
        p5.conveyor_triage_v038(self.e, self.p)
        self.assertIn(moved.die_id, [x.die_id for x in sp.next_sprint(self.p)])

    def test_tc_sp_12_all_entry_paths_over_games(self):
        """INV-SP-05 (B3, Y3, purchases, Prometheus, PR L3, Triage, G3 ...): at every Sprint Review, a Current die was
        either left over from the previous review or returned by Production Return into an empty Current Sprint."""
        orig_rev, orig_ret = sp.sprint_review, p5.production_return_to_scanned
        seen: Dict[int, set] = {}

        def ret(engine, player):
            moved = orig_ret(engine, player)
            seen.setdefault(player.player_id, set()).update(
                d.die_id for d in moved if d.die_id in player.current_sprint_ids)
            return moved

        def rev(engine, player, chosen=None):
            ok = seen.get(player.player_id, set())
            sp.prune(player)
            for d in sp.current_sprint(player):
                assert d.die_id in ok, f"die {d.die_id} entered the Current Sprint outside Production Return"
            out = orig_rev(engine, player, chosen)
            seen[player.player_id] = {d.die_id for d in player.scanned_dice}
            return out

        sp.sprint_review, p5.production_return_to_scanned = rev, ret
        try:
            for players in (2, 3, 4):
                for seed in range(42, 62):
                    e = mk(players, seed)
                    for pl in e.state.players:
                        seen[pl.player_id] = {d.die_id for d in pl.scanned_dice}
                    e.run_game()
        finally:
            sp.sprint_review, p5.production_return_to_scanned = orig_rev, orig_ret

    def test_tc_sp_13_removal_paths_prune(self):
        """G3 / Blue Signature / Triage L4 / Burn Notice / corruption return: Current ids stay a subset (INV-SP-06)."""
        self._review_then()
        cur = [gray(self.e, 710), colored(self.e, 711)]
        set_sprint(self.e, self.p, cur, [gray(self.e, 712)], 4)
        # G3 Live Reboot style removal of a Current die
        self.p.scanned_dice.remove(cur[0])
        sp.prune_all(self.e.state)
        self.assertEqual(self.p.current_sprint_ids, {711})
        # Triage L4 swap on a Current Gray prunes and counts
        set_sprint(self.e, self.p, [gray(self.e, 720)], [gray(self.e, 721)], 4)
        self.p.money = 10
        rt._resolve_triage_replacement(self.e, self.p, BreakthroughChoice(gray_die_id=720, color=DieColor.YELLOW),
                                       rt.BreakthroughRecord("TRIAGE", 4, 1, "TAKEN"), cost=0, allow_decline=False)
        self.assertNotIn(720, self.p.current_sprint_ids)
        self.assertEqual(self.p.gray_removed_by_source.get("TRIAGE_L4"), 1)
        # Burn Notice counts its source (rebalanced Spook)
        from sim.engine import phase3_income

        set_sprint(self.e, self.p, [], [gray(self.e, 730)], 4)
        self.assertTrue(getattr(self.e.config, "white_hat_6f_rebalance", False), "precondition: rebalanced Spook")
        self.assertTrue(phase3_income.resolve_spook_burn_notice(self.e, self.p, 730))
        self.assertEqual(self.p.gray_removed_by_source.get("BURN_NOTICE"), 1)
        # an emptied Current Sprint sends the next Production Return to Current
        set_sprint(self.e, self.p, [gray(self.e, 740)], [], 4)
        self.p.scanned_dice.clear()
        self.p.in_production_dice[:] = [colored(self.e, 741)]
        p5.production_return_to_scanned(self.e, self.p)
        self.assertEqual(self.p.current_sprint_ids, {741})

    def test_tc_sp_13_invariants_hold_over_games(self):
        for players in (2, 3, 4):
            e = mk(players, 60 + players)
            while not e.state.game_over:
                e.run_round()
                for p in e.state.players:  # INV-SP-06 at the end of each round (after Phase 6)
                    self.assertTrue(p.current_sprint_ids <= {d.die_id for d in p.scanned_dice})

    def test_tc_sp_14_stale_id_guard(self):
        d = gray(self.e, 750)
        set_sprint(self.e, self.p, [d], [], 4)
        self.p.scanned_dice.remove(d)  # e.g. G3 removes it
        self.p.glitched_dice.append(d)
        sp.prune(self.p)
        p5.conveyor_triage_v038(self.e, self.p)  # re-enters via Triage
        self.assertIn(750, [x.die_id for x in sp.next_sprint(self.p)])
        self.assertNotIn(750, self.p.current_sprint_ids)


# ------------------------------------------------------------------------------------------------ Gray lock
class _RollLog:
    """Wraps Die.roll to log (die, face-before) so a reroll of a locked face is detectable."""

    def __init__(self):
        self.violations = 0
        self.after_warn_rerolls = 0
        self.seq_to_warn = 0
        self._orig = Die.roll

    def __enter__(self):
        log = self
        orig = self._orig

        def roll(die, rng):
            was = die.current_face
            if was is not None and die.color == DieColor.GRAY and vuln.face_vuln(was) > 0:
                log.violations += 1
            out = orig(die, rng)
            if log.violations == 0 and die.color == DieColor.GRAY and vuln.face_vuln(die.current_face) > 0 and was is not None:
                log.seq_to_warn += 1  # landed on a Gray ⚠ face on a reroll
            return out

        Die.roll = roll
        return self

    def __exit__(self, *a):
        Die.roll = self._orig


class TestGrayLock(unittest.TestCase):
    def _phase1(self, seed, helix=False, lock=True, players=3):
        e = mk(players, seed, vuln_face_lock="GRAY" if lock else "NONE")
        for i in range(players):
            b = with_stub(e, i)
            b.helix = helix
        if helix:
            for p in e.state.players:
                p.company = COMPANIES[CompanyCode.HELIX]
        e.state.rng.seed(seed)
        e._execute_phase_1()
        return e

    def test_tc_sp_15_lock_drops_gray_warn_rerolls_inv_sp_09(self):
        blocked = 0
        with _RollLog() as log:
            for seed in range(42, 72):
                e = self._phase1(seed)
                blocked += sum(p.gray_lock_blocked for p in e.state.players)
        self.assertEqual(log.violations, 0)
        self.assertGreater(blocked, 0)

    def test_tc_sp_15_no_lock_rerolls_gray_warn_and_colored_unfiltered(self):
        with _RollLog() as log:
            for seed in range(42, 72):
                self._phase1(seed, lock=False)
        self.assertGreater(log.violations, 0)  # control: without the lock the stub rerolls ⚠ Gray
        # colored ⚠ dice are never filtered: count colored ⚠ rerolls under the lock
        n = 0
        orig = Die.roll

        def roll(die, rng):
            nonlocal n
            if die.current_face is not None and die.color not in (DieColor.GRAY,) and vuln.face_vuln(die.current_face) > 0:
                n += 1
            return orig(die, rng)

        Die.roll = roll
        try:
            for seed in range(42, 72):
                self._phase1(seed)
        finally:
            Die.roll = orig
        self.assertGreater(n, 0)

    def test_tc_sp_16_helix_exempt_and_is_locked_untouched(self):
        blocked = 0
        with _RollLog() as log:
            for seed in range(42, 72):
                e = self._phase1(seed, helix=True)
                blocked += sum(p.gray_lock_blocked for p in e.state.players)
        self.assertEqual(blocked, 0)
        self.assertGreater(log.violations, 0)  # Helix Brute-Force Bypass rerolls the locked Gray
        # the lock never sets is_locked (Helix bots read it)
        e = mk(3, 42)
        d = gray(e, 800)
        d.current_face = d.faces[2]
        self.assertFalse(d.is_locked)
        self.assertTrue(vuln.is_reroll_locked(e.config, d))
        self.assertFalse(d.is_locked)
        self.assertFalse(vuln.is_reroll_locked(e.config, colored(e, 801)))
        c46 = GameConfig.v046(num_players=3)
        self.assertFalse(vuln.is_reroll_locked(c46, d))

    def test_tc_sp_16_release_l4_sets_locked_gray_face(self):
        e = mk(3, 42)
        p = e.state.players[0]
        p.release_level = 4
        d = gray(e, 810)
        d.current_face = d.faces[2]  # locked ⚠ face
        ok = phase1_roll_deploy.resolve_release_l4_gray_face_override(p, [d], e.state, 0, d.faces[0])
        self.assertTrue(ok)
        self.assertIs(d.current_face, d.faces[0])

    def test_tc_sp_17_lock_after_initial_roll_and_after_reroll(self):
        """A Gray die that lands on F3 on the initial roll or on a reroll is never rolled again."""
        landed = 0
        with _RollLog() as log:
            for seed in range(42, 82):
                self._phase1(seed)
            landed = log.seq_to_warn
        self.assertEqual(log.violations, 0)
        self.assertGreater(landed, 0)  # at least one reroll landed on F3 and stayed


# ------------------------------------------------------------------------------------------------ Breakthroughs
class TestBreakthroughs(unittest.TestCase):
    def setUp(self):
        self.e = mk(3, 42)
        self.p = self.e.state.players[0]
        self.b = with_stub(self.e)

    def test_tc_sp_18_l1_rewards_inv_sp_14(self):
        nid = self.e.state.next_die_id
        s0, m0, ready0 = self.p.secrets, self.p.money, len(self.p.ready_for_release_dice)
        r = rt.resolve_breakthrough(self.e, self.p, "DEFENSE", 1)
        self.assertEqual((r.outcome, r.detail), ("TAKEN", {"secrets": 1}))
        self.assertEqual(self.p.secrets, s0 + 1)
        self.assertEqual(self.p.secrets_by_source["breakthrough"], 1)
        r = rt.resolve_breakthrough(self.e, self.p, "TRIAGE", 1)
        self.assertEqual((r.detail, self.p.money), ({"money": 2}, m0 + 2))
        r = rt.resolve_breakthrough(self.e, self.p, "RELEASE", 1)
        self.assertEqual(r.detail, {"release_bandwidth_this_round": 1})
        self.assertEqual(self.p.temp_release_bandwidth_bonus, 1)
        self.assertEqual(self.e.state.next_die_id, nid)  # no die created
        self.assertEqual(len(self.p.ready_for_release_dice), ready0)

    def test_tc_sp_18_v046_unchanged(self):
        e = mk(3, 42, preset="v046")
        p = e.state.players[0]
        n = len(p.ready_for_release_dice)
        rt.resolve_breakthrough(e, p, "RELEASE", 1)
        self.assertEqual(len(p.ready_for_release_dice), n + 1)  # Gray die
        s0 = p.secrets
        rt.resolve_breakthrough(e, p, "RELEASE", 3)
        self.assertEqual(p.secrets, s0 + 1)

    def _thin_state(self):
        e = mk(3, 42)
        p = e.state.players[0]
        with_stub(e)
        clear_pipeline(p)
        g_rd, g_next, g_prod, g_cur, g_ready = (gray(e, 900 + i) for i in range(5))
        c = colored(e, 905)
        c.secret_pending = False
        g_rd.secret_pending = True
        p.glitched_dice.append(g_rd)
        p.scanned_dice.extend([g_next, g_cur])
        sp.mark_current(p, [g_cur])
        p.in_production_dice.append(g_prod)
        p.ready_for_release_dice.extend([g_ready, c])
        return e, p, (g_rd, g_next, g_prod, g_cur, g_ready)

    def test_tc_sp_19_thin_default_order_and_choice(self):
        for track, level in (("RELEASE", 3), ("DEFENSE", 3)):
            e, p, (g_rd, g_next, g_prod, g_cur, g_ready) = self._thin_state()
            lost = p.secrets_lost_returned
            market = dict(e.state.market)
            money = p.money
            order = []
            for _ in range(5):
                rec = rt.resolve_breakthrough(e, p, track, level) if not order else None
                if rec is not None:
                    order.append(rec.detail["gray_die_id"])
                    p.breakthroughs.clear()
                    continue
                hit = rt.thin_gray(e, p, "RELEASE_L3")
                order.append(hit.die_id)
            self.assertEqual(order, [900, 901, 902, 903, 904])  # R&D, Next, In Production, Current, Ready
            self.assertEqual(p.secrets_lost_returned, lost + 1)  # pending Secret lost in R&D
            self.assertEqual(e.state.market, market)  # to the box, not the Central Market
            self.assertEqual(p.money, money)  # no payout
            self.assertEqual(p.current_sprint_ids, set())
            self.assertEqual(p.gray_removed_by_source["PEN_TEST_L3" if track == "DEFENSE" else "RELEASE_L3"] >= 1, True)
            self.assertEqual(len(p.thin_rounds), 5)
        e, p, ds = self._thin_state()
        rec = rt.resolve_breakthrough(e, p, "RELEASE", 3, BreakthroughChoice(gray_die_id=904))
        self.assertEqual((rec.detail["gray_die_id"], rec.detail["zone"]), (904, "ready"))
        p.breakthroughs.clear()
        self.b = with_stub(e)
        self.b.thin = lambda cands: cands[-1][1].die_id  # hook choice respected
        rec = rt.resolve_breakthrough(e, p, "RELEASE", 3)
        self.assertEqual(rec.detail["gray_die_id"], 903)  # last candidate after 904 was removed (Ready -> Current)
        p.breakthroughs.clear()
        self.b.thin = lambda cands: 424242  # invalid -> default first
        rec = rt.resolve_breakthrough(e, p, "RELEASE", 3)
        self.assertEqual(rec.detail["gray_die_id"], 900)

    def test_tc_sp_20_forfeit_no_gray(self):
        e = mk(3, 42)
        p = e.state.players[0]
        clear_pipeline(p)
        p.ready_for_release_dice.append(colored(e, 950))
        s0 = p.secrets
        for track in ("DEFENSE", "RELEASE"):
            rec = rt.resolve_breakthrough(e, p, track, 3)
            self.assertEqual((rec.outcome, rec.detail), ("FORFEITED", {"reason": "no_gray_die"}))
        self.assertEqual((p.thin_forfeits, p.secrets), (2, s0))
        self.assertEqual(len(p.ready_for_release_dice), 1)

    def test_tc_sp_21_pen_test_l3_keeps_blue_bonus_inv_sp_15(self):
        from sim.engine import secret_faces

        for preset in ("v046", "v048"):
            e = mk(3, 42, preset=preset)
            p = e.state.players[0]
            p.defense_level = 2
            a = secret_faces.secret_yield(e.config, p, DieColor.BLUE)
            p.defense_level = 3
            b = secret_faces.secret_yield(e.config, p, DieColor.BLUE)
            self.assertEqual(b - a, e.config.secret_yield_blue_grid_l3_bonus)
            self.assertGreater(b - a, 0)

    def test_tc_sp_22_once_only(self):
        e, p, ds = self._thin_state()
        rt.resolve_breakthrough(e, p, "RELEASE", 3)
        n = len(sp.owned_gray(p))
        self.assertIsNone(rt.resolve_breakthrough(e, p, "RELEASE", 3))
        self.assertEqual(len(sp.owned_gray(p)), n)
        clone, _ = fast_clone.clone_engine(e)
        cp = clone.state.players[0]
        self.assertIsNone(rt.resolve_breakthrough(clone, cp, "RELEASE", 3))
        self.assertEqual(len(sp.owned_gray(cp)), n)

    def test_breakthrough_text_modes(self):
        c = GameConfig.v048(num_players=3)
        self.assertEqual(rt.breakthrough_text(c, "DEFENSE", 1), "Gain 1 Corporate Secret")
        self.assertEqual(rt.breakthrough_text(c, "TRIAGE", 1), "Gain $2")
        self.assertEqual(rt.breakthrough_text(c, "RELEASE", 1), "+1 Release Bandwidth this round")
        self.assertEqual(rt.breakthrough_text(c, "DEFENSE", 3), "Return 1 Gray Legacy die you own to the box; Blue R&D faces yield +3")
        self.assertEqual(rt.breakthrough_text(c, "RELEASE", 3), "Return 1 Gray Legacy die you own to the box")
        self.assertEqual(rt.breakthrough_text(c, "TRIAGE", 3), "Gain 1 Corporate Secret")
        c6 = GameConfig.v046(num_players=3)
        self.assertEqual(rt.breakthrough_text(c6, "RELEASE", 3), "Gain 1 Corporate Secret")
        self.assertEqual(rt.breakthrough_text(c6, "RELEASE", 1), "Gain 1 Gray Legacy die")


# ------------------------------------------------------------------------------------------------ tiebreak / clone
class TestScoringAndClone(unittest.TestCase):
    def test_tc_sp_23_tiebreak_and_bounty_count_both_sprints(self):
        import inspect

        from sim.engine import phase3_income

        e = mk(3, 42)
        p = e.state.players[0]
        set_sprint(e, p, [gray(e, 600), gray(e, 601)], [colored(e, 602), colored(e, 603, DieColor.BLUE)], 4)
        p.glitched_dice.append(gray(e, 604))
        res = e.evaluate_end_game()
        row = next(r for r in res.rankings if r["player_id"] == 0)
        self.assertEqual(row["unpatched_dice_count"], 5)  # |R&D| + |Sprint Plan| (INV-SP-17)
        self.assertIn("len({d.color for d in player.scanned_dice})", inspect.getsource(phase3_income))

    def test_tc_sp_24_clone_independent_set_and_dicts_inv_sp_18(self):
        e = mk(3, 42)
        e.run_round()
        c, _ = fast_clone.clone_engine(e)
        for a, b in zip(e.state.players, c.state.players):
            self.assertEqual(a.current_sprint_ids, b.current_sprint_ids)
            self.assertIsNot(a.current_sprint_ids, b.current_sprint_ids)
            self.assertEqual((a.sprint_wait_hist, a.sprint_max_streak, a.gray_removed_by_source, a.thin_rounds),
                             (b.sprint_wait_hist, b.sprint_max_streak, b.gray_removed_by_source, b.thin_rounds))
            self.assertIsNot(a.sprint_wait_hist, b.sprint_wait_hist)
        c.state.players[0].current_sprint_ids.add(99999)
        c.state.players[0].sprint_wait_hist["gray"][0] += 7
        self.assertNotIn(99999, e.state.players[0].current_sprint_ids)
        self.assertNotEqual(e.state.players[0].sprint_wait_hist, c.state.players[0].sprint_wait_hist)

    def _digest(self, e):
        r = e.run_game()
        return (r.end_reason, r.total_rounds, list(r.winner_ids), [(x["player_id"], x["secrets"], x["money"]) for x in r.rankings])

    def test_tc_sp_24_clone_replays_and_resume_mid_phase5(self):
        for players, seed in ((2, 42), (3, 43), (4, 44)):
            e = mk(players, seed, preset="v048_roster")
            e.run_round()
            c, _ = fast_clone.clone_engine(e)
            self.assertEqual(self._digest(e), self._digest(c))
        e = mk(3, 45, preset="v048_roster")
        s = e.state
        e.run_round()
        commitments = e._execute_phase_1()
        cr = e._run_phase_2_compiler(commitments)
        if s.game_over:
            self.skipTest("game ended in Phase 2")
        e._run_phase_3_income(commitments)
        e._run_phase_4_attack_resolution(commitments, cr)
        if s.game_over:
            self.skipTest("game ended in Phase 4")
        clone, _ = fast_clone.clone_engine(e)
        e._run_phase_operations()
        e._run_phase_pipeline_shift()
        from sim.engine.phase6_operations import pass_first_player_marker

        pass_first_player_marker(e)
        fast_clone.resume_round(clone, 5)
        for a, b in zip(e.state.players, clone.state.players):
            self.assertEqual([d.die_id for d in a.ready_for_release_dice], [d.die_id for d in b.ready_for_release_dice])
            self.assertEqual([d.die_id for d in a.scanned_dice], [d.die_id for d in b.scanned_dice])
            self.assertEqual(a.current_sprint_ids, b.current_sprint_ids)


# ------------------------------------------------------------------------------------------------ bots
class TestBots(unittest.TestCase):
    def _player(self, **lv):
        e = mk(3, 42, preset="v048_roster")
        p = e.state.players[0]
        p.research_tokens = 99
        for t, v in lv.items():
            setattr(p, rp.LEVEL_ATTR[t.upper()], v)
        return e, p

    def test_tc_sp_25_thinning_aware_want_list(self):
        e, p = self._player()
        pol = rp.ResearchPolicy(focus_order=("TRIAGE", "DEFENSE", "RELEASE", "PATENT"))
        order = rp._thinning_aware_want_order(pol, p, e.config, {t: 0 for t in rp.TRACKS})
        self.assertEqual(order[:4], ["TRIAGE", "RELEASE", "RELEASE", "RELEASE"])  # Triage L1, then Release to L3
        self.assertEqual(order[4], "TRIAGE")  # legacy Triage-to-L2 injection sits after the head
        legacy = rp._want_list(pol, {t: 0 for t in rp.TRACKS})
        self.assertEqual(legacy[0], "TRIAGE")
        # Triage L1 done -> Release only
        order = rp._thinning_aware_want_order(pol, p, e.config, {"TRIAGE": 1, "DEFENSE": 0, "RELEASE": 0, "PATENT": 0})
        self.assertEqual(order[:3], ["RELEASE"] * 3)
        # Release already L3 -> head is empty; legacy Triage-to-L2 injection follows the head
        order = rp._thinning_aware_want_order(pol, p, e.config, {"TRIAGE": 1, "DEFENSE": 0, "RELEASE": 3, "PATENT": 0})
        self.assertEqual(order[0], "TRIAGE")
        # never past L4 per track
        order = rp._thinning_aware_want_order(pol, p, e.config, {"TRIAGE": 3, "DEFENSE": 0, "RELEASE": 2, "PATENT": 0})
        for t in rp.TRACKS:
            self.assertLessEqual(order.count(t), 4 - {"TRIAGE": 3, "DEFENSE": 0, "RELEASE": 2, "PATENT": 0}[t])
        # thin tracks include Pen Test only when configured; below the Gray floor only Release L<2 is pushed
        e2 = mk(3, 42, preset="v048_roster", bot_thin_tracks=("RELEASE", "DEFENSE"))
        order = rp._thinning_aware_want_order(pol, e2.state.players[0], e2.config, {"TRIAGE": 1, "DEFENSE": 0, "RELEASE": 0, "PATENT": 0})
        self.assertEqual(order[:6], ["RELEASE"] * 3 + ["DEFENSE"] * 3)
        pl = e2.state.players[0]
        clear_pipeline(pl)  # no Gray owned: only Release below L2 is pushed
        order = rp._thinning_aware_want_order(pol, pl, e2.config, {"TRIAGE": 1, "DEFENSE": 0, "RELEASE": 2, "PATENT": 0})
        self.assertNotEqual(order[:3], ["RELEASE"] * 3)

    def test_tc_sp_25_legacy_mode_matches_v046(self):
        for seed in (42, 43, 44):
            e47 = mk(3, seed, preset="v048_roster", bot_research_mode="LEGACY")
            e46 = mk(3, seed, preset="v046_roster")
            for lv in ({}, {"TRIAGE": 1}, {"TRIAGE": 2, "RELEASE": 1}):
                for pid in range(3):
                    outs = []
                    for e in (e47, e46):
                        p = e.state.players[pid]
                        p.research_tokens = 9
                        for t in rp.TRACKS:
                            setattr(p, rp.LEVEL_ATTR[t], lv.get(t, 0))
                        pol = rp.policy_for_bot(p.bot, e.state, e.rng)
                        outs.append(rp._plan_research_share_regain(pol, p, e.state, e.config))
                    self.assertEqual(outs[0], outs[1])

    def test_tc_sp_26_rush_policy_inv_sp_19(self):
        for mode, expected in (("p0", [True, False, False]), ("all", [True, True, True]), ("none", [False] * 3)):
            e = mk(3, 42, preset="v048_roster", bot_research_rush=mode)
            self.assertEqual([rp._rushes(e.config, p, e.state) for p in e.state.players], expected)
        e = mk(3, 42, preset="v048_roster", bot_research_rush="p0half")
        e.state.rush_seed = 7
        flips = []
        for r in range(1, 9):
            e.state.current_round = r
            a = rp._rushes(e.config, e.state.players[0], e.state)
            b = rp._rushes(e.config, e.state.players[0], e.state)
            self.assertEqual(a, b)
            self.assertFalse(rp._rushes(e.config, e.state.players[1], e.state))
            flips.append(a)
        self.assertTrue(any(flips) and not all(flips))
        e = mk(3, 42, preset="v048_roster", bot_research_rush="p0")
        p = e.state.players[0]
        pol = rp.policy_for_bot(p.bot, e.state, e.rng)
        before = e.rng.getstate()
        p.research_tokens = 100
        for t in rp.TRACKS:
            setattr(p, rp.LEVEL_ATTR[t], 0)
        ups, filings, regain = rp._plan_research_share_regain(pol, p, e.state, e.config)
        self.assertEqual((ups, filings, regain), (["RELEASE", "RELEASE"], 0, 0))  # cap 2 upgrades per turn
        self.assertEqual(e.rng.getstate(), before)  # no RNG
        p.research_tokens = 2  # costs (1, 2, 2, 3): can pay L1 (1) but not L2 (2) after: stop at first unaffordable
        ups, _, _ = rp._plan_research_share_regain(pol, p, e.state, e.config)
        self.assertEqual(ups, ["RELEASE"])
        for t, lvl in (("RELEASE", 3), ("DEFENSE", 3)):
            setattr(p, rp.LEVEL_ATTR[t], lvl)
        p.research_tokens = 50  # both at L3: falls back to the normal policy
        self.assertNotEqual(rp._plan_research_share_regain(pol, p, e.state, e.config)[0], ["RELEASE"])


# ------------------------------------------------------------------------------------------------ telemetry / keys / smoke
class TestTelemetry(unittest.TestCase):
    def test_tc_sp_27_telemetry_populated(self):
        e = mk(3, 42, preset="v048_roster")
        res = e.run_game()
        fields = ("sprint_current_by_player", "sprint_next_by_player", "sprint_current_over_bw_by_player",
                  "sprint_grad_current_by_player", "sprint_grad_next_by_player", "sprint_left_by_player",
                  "sprint_prod_to_current_by_player", "gray_owned_by_player", "gray_ready_by_player",
                  "gray_rolled_by_player", "colored_rolled_by_player", "gray_vuln_kept_by_player",
                  "colored_vuln_kept_by_player")
        full = [t for t in res.telemetry_history if t.end_phase in (None, 6)]
        self.assertTrue(full)
        for t in full:
            for f in fields:
                self.assertTrue(getattr(t, f), (t.round_number, f))
        # streak histogram sums equal graduations
        for p in e.state.players:
            grads = sum(sum(v) for v in p.sprint_wait_hist.values())
            self.assertEqual(grads, sum(t.graduated_by_player.get(p.player_id, 0) for t in res.telemetry_history))
        e46 = mk(3, 42, preset="v046_roster")
        for t in e46.run_game().telemetry_history:
            self.assertTrue(all(not getattr(t, f) for f in fields))

    def test_tc_sp_27_spook_burn_counted(self):
        for seed in range(42, 400):
            e = mk(3, seed, preset="v048_roster")
            if not any(getattr(p.white_hat, "code", None) is not None and p.white_hat.code.value == "SPOOK"
                       for p in e.state.players):
                continue
            res = e.run_game()
            burned = sum(t.spook_gray_dice_burned for t in res.telemetry_history)
            if burned:
                self.assertEqual(burned, sum(p.gray_removed_by_source.get("BURN_NOTICE", 0) for p in e.state.players))
                return
        self.fail("no game with a Burn Notice found")

    def test_tc_sp_28_snapshot_and_ranking_keys_inv_sp_20(self):
        e6, e7 = mk(3, 42, preset="v046"), mk(3, 42, preset="v048")
        self.assertEqual(set(e6._snapshot_players()[0]), set(e7._snapshot_players()[0]))
        r6, r7 = e6.run_game(), e7.run_game()
        self.assertEqual(set(r6.rankings[0]), set(r7.rankings[0]))
        for name in ("current_sprint_ids", "sprint_wait_streak", "gray_lock_blocked", "thin_rounds"):
            self.assertNotIn(name, r7.rankings[0])
            self.assertNotIn(name, e7._snapshot_players()[0])


class TestSmoke(unittest.TestCase):
    def test_tc_sp_29_smoke_with_invariants(self):
        from scripts.run_v048_sweep import install_invariant_checks

        from sim.entities import Die

        install_invariant_checks()
        Die._gray_warn_ids = set()
        for preset in ("v048", "v048_roster"):
            for players in (2, 3, 4):
                for seed in range(42, 62):
                    e = mk(players, seed, preset=preset)
                    e.run_game()
                    helix_gray = {d.die_id for p in e.state.players if "helix" in str(getattr(p, "company_code", "")
                                  or getattr(getattr(p, "company", None), "code", "")).lower()
                                  for d in p.total_dice if d.color == DieColor.GRAY}
                    for p in e.state.players:
                        self.assertTrue(p.current_sprint_ids <= {d.die_id for d in p.scanned_dice})
                    bad = getattr(Die, "_gray_warn_ids", set()) - helix_gray
                    self.assertFalse(bad, f"INV-SP-09: Gray dice {sorted(bad)} rerolled on a warning face")
                    Die._gray_warn_ids = set()


if __name__ == "__main__":
    unittest.main()
