"""v0.52.0 Market Share stack (docs/specs/ms_stack_order_spec.md, unit test plan section 12)."""

import dataclasses
import os
import re
import unittest
from unittest import mock

from scripts.run_v380_secret_faces_sweep import build_engine
from sim.config import GameConfig
from sim.engine import market_share as msm
from sim.engine import ms_stack as mss
from sim.engine import phase4_attack_resolution as p4
from sim.engine.ms_stack import MarketShareStack, SETEC_CORP_ID

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def eng(players=4, seed=5, preset="v052_roster", **ov):
    return build_engine(preset, "mixed1", players, seed, ov)


def land(e, pid, value):
    """Moves ``pid`` to ``value`` as a sequential move (re-lands on top even when already there)."""
    p = e.state.players[pid]
    if p.market_share == value:
        p.change_market_share(-1 if value > 0 else 1, "r2")
    p.change_market_share(value - p.market_share, "r2")


def stack_of(e):
    return e.state.ms_stack


def bottom_to_top(e, pids, space=None):
    st = stack_of(e)
    return sorted(pids, key=lambda m: (st.space[m], st.seq[m]))


# ---------------------------------------------------------------------------
class TestConfig(unittest.TestCase):
    def test_c1_v052_values(self):
        for p in (2, 3, 4):
            for name in ("v052", "v052_roster"):
                c = getattr(GameConfig, name)(num_players=p)
                self.assertTrue(c.market_share_stacking)
                self.assertEqual(c.market_share_max, 25)
                self.assertEqual(c.market_share_stack_setup, "FIRST_SEAT_TOP")
                self.assertTrue(c.bot_ms_stack_aware)
                self.assertTrue(c.ms_tie_telemetry)
                self.assertEqual(c.red_secret_payout_by_player_count, {2: (3, 1), 3: (3, 1, 0), 4: (3, 2, 0, 0)})
                self.assertEqual(c.market_leader_bonus_by_player_count, {})
                self.assertEqual(c.ms_max(), 25)
                self.assertEqual(c.market_share_start_by_player_count, {2: 14, 3: 18, 4: 18})

    def test_c2_v051_unchanged(self):
        c = GameConfig.v051(num_players=4)
        self.assertFalse(c.market_share_stacking)
        self.assertFalse(c.ms_tie_telemetry)
        self.assertFalse(c.bot_ms_stack_aware)
        self.assertEqual(c.market_share_max, 20)
        self.assertEqual(c.red_secret_payout_by_player_count[4], (3, 1, 0, 0))

    def test_c3_only_new_fields_differ(self):
        for p in (2, 3, 4):
            x, y = GameConfig.v052_roster(num_players=p), GameConfig.v051_roster(num_players=p)
            diff = {f.name for f in dataclasses.fields(GameConfig) if getattr(x, f.name) != getattr(y, f.name)}
            want = {"market_share_stacking", "market_share_max", "ms_tie_telemetry", "bot_ms_stack_aware",
                    "market_share_stack_setup", "red_secret_payout_by_player_count"}  # dict differs at 4P only
            for n in (2, 3):
                self.assertEqual(x.red_secret_payout_by_player_count[n], y.red_secret_payout_by_player_count[n])
            self.assertEqual(diff, want, p)

    def test_c4_validation(self):
        with self.assertRaises(ValueError):
            GameConfig.v051(market_share_stacking=True, red_mode="RANSOM", num_players=2)
        with self.assertRaises(ValueError):
            GameConfig.v052(market_share_stack_setup="MIDDLE")
        with self.assertRaises(ValueError):
            GameConfig.v051(bot_ms_stack_aware=True)
        with self.assertRaises(ValueError):
            GameConfig.v052(market_share_max=10)
        GameConfig.v052(bot_ms_stack_aware=False)  # ablation arm is legal
        GameConfig.v052(market_share_stack_setup="LAST_SEAT_TOP")  # sweep arm stays legal

    def test_c5_roster_bots_kept(self):
        a, b = GameConfig.v052_roster(num_players=3), GameConfig.v051_roster(num_players=3)
        for f in ("bot_pr_push", "bot_pr_push_params", "bot_research_mode", "vuln_hit_landing_by_band"):
            self.assertEqual(getattr(a, f), getattr(b, f), f)


# ---------------------------------------------------------------------------
class TestSetup(unittest.TestCase):
    def test_s1_seat_order(self):
        for players in (3, 4):
            for seed in range(1, 12):
                e = eng(players, seed)
                s = e.state
                st = stack_of(e)
                self.assertEqual(len({p.market_share for p in s.players}), 1)
                order = [s.players[(s.first_player_index + k) % players].player_id for k in range(players)]
                order.reverse()  # v052 default FIRST_SEAT_TOP: the First Player is on top, the last seat at the bottom
                self.assertEqual(bottom_to_top(e, [p.player_id for p in s.players]), order)
                self.assertEqual(len(set(st.seq.values())), len(st.seq))

    def test_s1b_explicit_first_player_two(self):
        st = MarketShareStack.setup([2, 3, 0, 1], 18, None)
        self.assertEqual(sorted(st.seq, key=st.seq.get), [2, 3, 0, 1])
        self.assertEqual(st.highest([0, 1, 2, 3]), 1)

    def test_s2_two_player_setec(self):
        e = eng(2, 3)
        st = stack_of(e)
        self.assertEqual(st.seq[SETEC_CORP_ID], 0)
        self.assertEqual(st.space[SETEC_CORP_ID], 0)
        self.assertEqual(st.space[0], 14)

    def test_s3_rng_state_equals_v051(self):
        for players in (2, 3, 4):
            a, b = eng(players, 9), eng(players, 9, preset="v051_roster")
            self.assertEqual(a.rng.getstate(), b.rng.getstate())

    def test_s4_last_seat_top_arm(self):
        e = eng(3, 4, market_share_stack_setup="LAST_SEAT_TOP")
        s = e.state
        top = stack_of(e).highest([p.player_id for p in s.players])
        self.assertEqual(top, s.players[(s.first_player_index + 2) % 3].player_id)


# ---------------------------------------------------------------------------
class TestSequential(unittest.TestCase):
    def test_q1_move_lands_on_top(self):
        e = eng(4, 7)
        st = stack_of(e)
        land(e, 0, 20)
        land(e, 1, 20)
        self.assertGreater(st.key(1), st.key(0))
        land(e, 0, 20)  # leaves and returns: on top again
        self.assertGreater(st.key(0), st.key(1))
        self.assertEqual(max(st.seq.values()), st.seq[0])  # INV-MS-STACK-02

    def test_q2_multi_step_regain_ends_on_top(self):
        e = eng(3, 2)
        st = stack_of(e)
        land(e, 1, 21)
        e.state.players[0].change_market_share(-5, "red")
        for _ in range(3):
            e.state.players[0].change_market_share(+1, "regain")
        self.assertEqual(e.state.players[0].market_share, 16)
        land(e, 2, 16)
        e.state.players[0].change_market_share(-1, "red")
        e.state.players[0].change_market_share(+1, "regain")
        self.assertGreater(st.key(0), st.key(2))

    def test_q3_poach_actor_lands_on_top_of_rival(self):
        e = eng(3, 2)
        st, s = stack_of(e), e.state
        # rival 1 at 20, actor 0 at 18: one poach moves rival to 19 and the actor to 19; actor on top (R4)
        land(e, 0, 18)
        land(e, 1, 20)
        land(e, 2, 10)
        msm.queue_poach(e, s.players[0], 1)
        ev = msm.resolve_poaches(e)
        self.assertEqual(ev[0]["target"], 1)
        self.assertEqual((s.players[0].market_share, s.players[1].market_share), (19, 19))
        self.assertGreater(st.key(0), st.key(1))

    def test_q4_pr_l4_and_setec_land_on_top(self):
        e = eng(2, 3)
        st, s = stack_of(e), e.state
        land(e, 0, 14)
        s.players[1].change_market_share(-14, "red")
        s.setec_market_share = 0
        st.on_move(SETEC_CORP_ID, 0, 0, "setec_advance")  # no move: nothing changes
        before = st.seq[SETEC_CORP_ID]
        self.assertEqual(before, 0)
        # SETEC Corp +1 onto a player's space lands on top of the player
        s.players[1].change_market_share(+1, "regain")  # player 1 at 1
        s.setec_market_share = 1
        st.on_move(SETEC_CORP_ID, 0, 1, "setec_advance")
        self.assertGreater(st.key(SETEC_CORP_ID), st.key(1))
        # PR L4 capstone arrives on top
        s.players[0].change_market_share(-13, "red")  # 1
        s.players[0].change_market_share(+2, "pr_l4")
        s.players[1].change_market_share(+2, "pr_l4")
        self.assertGreater(st.key(1), st.key(0))


# ---------------------------------------------------------------------------
class TestBatches(unittest.TestCase):
    def test_b1_uniform_red_keeps_ranking(self):
        st = MarketShareStack.setup([0, 1, 2, 3], 10, None)
        for m, v in ((0, 9), (1, 10), (2, 10)):
            st.on_move(m, st.space[m], v, "x") if st.space[m] != v else None
        st.on_move(3, 10, 12, "x")
        before = st.order([0, 1, 2, 3])
        st.begin("red")
        for m in (0, 1, 2, 3):
            st.on_move(m, st.space[m], st.space[m] - 2, "red")
        st.end()
        self.assertEqual(st.order([0, 1, 2, 3]), before)

    def test_b2_clamp_at_zero(self):
        st = MarketShareStack.setup([0, 1, 2, 3], 5, None)
        st.on_move(3, 5, 0, "r")  # already at 0
        st.on_move(1, 5, 1, "r")
        st.on_move(2, 5, 2, "r")
        st.on_move(0, 5, 9, "r")
        st.begin("red")
        st.on_move(1, 1, 0, "red")  # from 1
        st.on_move(2, 2, 0, "red")  # from 2 (clamped from -1)
        st.end()
        self.assertEqual(st.order([1, 2, 3]), [2, 1, 3])  # 2 above 1, both above the one already at 0

    def test_b3_baffle_echo_covers_non_mover(self):
        st2 = MarketShareStack.setup([0, 1], 10, None)  # 1 on top, 0 echoes (no move), 1 loses 1
        st2.begin("red")
        st2.on_move(1, 10, 9, "red")
        st2.end()
        self.assertEqual(st2.highest([0, 1]), 0)  # the one that did not move is now above

    def test_b4_phase3_batch_order_independent(self):
        def run(order):
            st = MarketShareStack.setup([0, 1, 2], 10, None)
            st.on_move(0, 10, 12, "x")
            st.on_move(1, 10, 11, "x")
            st.begin("income")
            moves = {0: (12, 14), 1: (11, 14), 2: (10, 10)}
            for m in order:
                a, b = moves[m]
                st.on_move(m, a, b, "face")
            st.end()
            return st.order([0, 1, 2])

        base = run([0, 1, 2])
        self.assertEqual(base, [0, 1, 2])  # 0 was above 1 before; both land on 14; the previous order is kept
        for order in ([2, 1, 0], [1, 0, 2], [1, 2, 0]):
            self.assertEqual(run(order), base)

    def test_b5_mover_above_non_mover_and_noops_keep_seq(self):
        st = MarketShareStack.setup([0, 1, 2], 10, 7)
        s_before = dict(st.seq)
        st.begin("income")
        st.on_move(0, 10, 11, "face")
        st.on_move(0, 11, 10, "face")  # net zero
        st.on_move(1, 10, 12, "face")
        st.end()
        self.assertEqual(st.seq[0], s_before[0])
        self.assertGreater(st.seq[1], max(s_before.values()))
        st2 = MarketShareStack.setup([0, 1], 10, None)
        st2.begin("income")
        st2.on_move(0, 10, 12, "face")
        st2.end()
        st3 = MarketShareStack.setup([0, 1], 10, None)
        st3.on_move(1, 10, 12, "r")
        st3.begin("income")
        st3.on_move(0, 10, 12, "face")  # lands on 1's space as a mover: above the non-mover
        st3.end()
        self.assertEqual(st3.highest([0, 1]), 0)

    def test_b6_clamp_at_max_keeps_seq(self):
        e = eng(3, 3)
        st = stack_of(e)
        p = e.state.players[0]
        p.change_market_share(+7, "r2")
        self.assertEqual(p.market_share, 25)
        seq = st.seq[0]
        p.change_market_share(+3, "regain")  # clamped to 0: not a move
        self.assertEqual(st.seq[0], seq)

    def test_b7_guards(self):
        st = MarketShareStack.setup([0, 1], 10, None)
        st.begin("a")
        with self.assertRaises(RuntimeError):
            st.begin("b")
        for call in (lambda: st.key(0), lambda: st.order([0, 1]), lambda: st.highest([0, 1]), lambda: st.lowest([0, 1])):
            with self.assertRaises(RuntimeError):
                call()
        e = eng(3, 3)
        e.state.ms_stack.begin("x")
        with self.assertRaises(RuntimeError):
            msm.stack_order(e.state, [0, 1])
        e.state.ms_stack.end()


# ---------------------------------------------------------------------------
class TestTargets(unittest.TestCase):
    def test_t1_poach_reads_stack_and_skips_hook(self):
        e = eng(3, 2)
        s, st = e.state, stack_of(e)
        land(e, 1, 20)
        land(e, 2, 20)  # 2 on top of 1
        land(e, 0, 5)
        hook = mock.Mock(return_value=1)
        s.players[0].bot.choose_poach_target = hook
        msm.queue_poach(e, s.players[0], 1)
        ev = msm.resolve_poaches(e)
        self.assertEqual(ev[0]["target"], 2)
        hook.assert_not_called()
        self.assertEqual(s.ms_tie_tel.c["poach_stack_decided"], 1)

    def test_t2_target_reread_after_previous_poach(self):
        e = eng(3, 2)
        s = e.state
        land(e, 1, 20)
        land(e, 2, 20)
        land(e, 0, 5)
        msm.queue_poach(e, s.players[0], 1)
        msm.queue_poach(e, s.players[0], 2)
        ev = msm.resolve_poaches(e)
        # first poach hits 2 (on top), actor goes to 6; second: 1 at 20 is now the most
        self.assertEqual([x["target"] for x in ev], [2, 1])

    def test_t3_hooks_still_called_under_v051(self):
        e = eng(3, 2, preset="v051_roster")
        s = e.state
        for p, v in zip(s.players, (5, 20, 20)):
            p.market_share = v
        hook = mock.Mock(return_value=2)
        s.players[0].bot.choose_poach_target = hook
        msm.queue_poach(e, s.players[0], 1)
        msm.resolve_poaches(e)
        hook.assert_called_once()

    def _sig(self, e, locked, breached=frozenset()):
        for p in e.state.players:
            p.target_locked = p.player_id in locked
        p4._resolve_signature_red(e, [e.state.players[i] for i in sorted(locked)], breached)

    def test_t4_signature_recipient_is_lowest_post_drain(self):
        e = eng(4, 2)
        s, st = e.state, stack_of(e)
        land(e, 1, 10)
        land(e, 2, 10)
        land(e, 3, 18)
        land(e, 0, 22)
        hook = mock.Mock()
        s.players[0].bot.choose_signature_red_recipient = hook
        before = {p.player_id: p.market_share for p in s.players}
        self._sig(e, {0})
        hook.assert_not_called()
        # locker 0 drains 2 -> 20; recipients are 1 and 2 on 10; 1 is lower in the stack -> gets +2
        self.assertEqual(s.players[1].market_share, before[1] + 2)
        self.assertEqual(s.players[2].market_share, before[2])
        self.assertEqual(s.ms_tie_tel.c["sig_red_stack_decided"], 1)

    def test_t5_drained_locker_shares_new_space(self):
        e = eng(3, 2)
        s, st = e.state, stack_of(e)
        land(e, 1, 16)  # rival lowest unless the locker drains below it
        land(e, 2, 25)
        land(e, 0, 17)  # locker drains 2 -> 15 (lowest, locked): rival 1 at 16 -> recipient is 1 or 2
        self._sig(e, {0})
        # pool for locker 0 is {1, 2}: lowest is 1
        self.assertEqual(s.players[1].market_share, 18)

    def test_t6_setec_recipient_two_player(self):
        e = eng(2, 3)
        s = e.state
        self.assertTrue(s.setec_corp_active)
        s.players[0].change_market_share(-5, "red")  # 9, locker 0 -> pool {1 (14), SETEC (0)}
        land(e, 1, 14)
        self._sig(e, {0})
        self.assertEqual(s.setec_market_share, 2)  # SETEC Corp ranks lowest and receives +2
        self.assertGreater(stack_of(e).key(SETEC_CORP_ID), (0, 10 ** 9))  # now on space 2

    def test_t7_signature_batches_and_cap(self):
        e = eng(3, 2)
        s, st = e.state, stack_of(e)
        land(e, 0, 25)
        land(e, 1, 24)
        land(e, 2, 25)
        # locker 0 drains to 23; its lowest rival is 1 (24): gains +2 -> capped at 25
        self._sig(e, {0})
        self.assertEqual(s.players[1].market_share, 25)
        self.assertEqual(s.signature_red_capped_gains, 1)
        self.assertIsNone(st.batch_tag)

    def test_t8_locker_also_recipient_ends_on_top(self):
        e = eng(3, 2)
        s, st = e.state, stack_of(e)
        land(e, 1, 12)
        land(e, 2, 20)
        land(e, 0, 14)
        # lockers 0 and 1: 0 drains to 12, 1 drains to 10; recipient of 0 is 2? pool {1:10, 2:20} -> 1 (+2 -> 12)
        # recipient of 1 is pool {0:12, 2:20} -> 0 (+2 -> 14)
        self._sig(e, {0, 1})
        self.assertEqual((s.players[0].market_share, s.players[1].market_share), (14, 12))
        self.assertEqual(s.signature_red_mutual_cancels, 1)


# ---------------------------------------------------------------------------
class TestRanking(unittest.TestCase):
    def test_r1_places_strict(self):
        shares = {0: 10, 1: 10, 2: 5}
        self.assertEqual(msm.market_share_places(shares), {0: 1, 1: 1, 2: 3})  # legacy competition ranking
        self.assertEqual(msm.market_share_places(shares, {0: 1, 1: 2, 2: 3}), {1: 1, 0: 2, 2: 3})
        self.assertEqual(msm.market_leader_bonus_awards(shares, (3, 2, 1), {0: 1, 1: 2, 2: 3})[1], (1, 3))

    def test_r2_schedules_pay_by_height(self):
        e = eng(4, 2)
        s = e.state
        for p in s.players:
            s.players[p.player_id].market_share = 18
        for pid in (0, 1, 2):  # all on 18 already: re-land in the order 2, 0, 1 (1 on top)
            pass
        land(e, 2, 20)
        land(e, 0, 20)
        land(e, 1, 20)
        land(e, 3, 7)
        from sim.engine import secret_faces

        aw = secret_faces.red_secret_payout_awards(s.config, s)
        self.assertEqual({k: v for k, v in aw.items()}, {1: (1, 3), 0: (2, 2), 2: (3, 0), 3: (4, 0)})

    def test_r3_three_player_schedule_and_setec_first(self):
        e = eng(2, 3)
        s = e.state
        from sim.engine import secret_faces

        land(e, 0, 3)
        land(e, 1, 3)
        s.setec_market_share = 3
        stack_of(e).on_move(SETEC_CORP_ID, 0, 3, "setec_advance")
        aw = secret_faces.red_secret_payout_awards(s.config, s)
        self.assertEqual(aw[SETEC_CORP_ID], (1, 3))
        self.assertEqual(aw[1], (2, 1))
        self.assertEqual(aw[0], (3, 0))

    def test_r4_end_payout_uses_height(self):
        e = eng(3, 2)
        s = e.state
        land(e, 0, 20)
        land(e, 1, 20)
        land(e, 2, 20)
        s.game_over = True
        s.end_reason = s.end_reason
        for p in s.players:
            p.secrets = 10
        res = e.evaluate_end_game()
        self.assertEqual([r["player_id"] for r in res.rankings][0], 2)  # 2 on top: wins the Secrets tie
        by = {r["player_id"]: r for r in res.rankings}
        self.assertEqual(by[2]["market_share_place"], 1)
        self.assertEqual(by[1]["market_share_place"], 2)
        self.assertEqual(by[0]["market_share_place"], 3)

    def test_r5_legacy_places_unchanged_without_order(self):
        self.assertEqual(msm.market_share_places({7: 4, 8: 4, 9: 1}), {7: 1, 8: 1, 9: 3})


# ---------------------------------------------------------------------------
class TestEndGame(unittest.TestCase):
    def _end(self, e):
        e.state.game_over = True
        return e.evaluate_end_game()

    def test_e1_height_decides_over_money(self):
        e = eng(3, 2)
        s = e.state
        land(e, 0, 15)
        land(e, 1, 15)
        land(e, 2, 1)
        # end Market Leader payout: 1 on top (+3), 0 beneath it (+1): 20 + 3 == 22 + 1
        s.players[0].secrets, s.players[1].secrets, s.players[2].secrets = 22, 20, 0
        s.players[0].money, s.players[1].money = 40, 0
        res = self._end(e)
        self.assertEqual(res.winner_ids, [1])
        self.assertEqual(res.tiebreak_decided_by, "market_share_stack")
        self.assertFalse(res.market_leader_bonus_tied_paid_place)
        self.assertFalse(res.is_shared_victory)

    def test_e2_different_market_share_decides(self):
        e = eng(3, 2)
        s = e.state
        land(e, 0, 16)
        land(e, 1, 15)
        land(e, 2, 3)
        s.players[0].secrets, s.players[1].secrets, s.players[2].secrets = 20, 22, 0  # 20 + 3 == 22 + 1
        res = self._end(e)
        self.assertEqual(res.winner_ids, [0])
        self.assertEqual(res.tiebreak_decided_by, "market_share")

    def test_e3_total_wipeout_ranks_by_position_only(self):
        e = eng(3, 2)
        s = e.state
        land(e, 0, 9)
        land(e, 1, 9)
        land(e, 2, 12)
        for p in s.players:
            p.is_patient_zero = True
            p.breach_depth = 1
        s.players[0].money = 99
        res = self._end(e)
        self.assertTrue(res.is_total_wipeout)
        self.assertEqual([r["player_id"] for r in res.rankings], [2, 1, 0])
        self.assertEqual(len(res.winner_ids), 1)

    def test_e4_v051_still_reaches_money_tiebreak(self):
        e = eng(3, 2, preset="v051_roster")
        s = e.state
        for p in s.players:
            p.market_share, p.secrets, p.money = 15, 20, 1
        s.players[0].money = 9
        res = self._end(e)
        self.assertEqual(res.winner_ids, [0])
        self.assertEqual(res.tiebreak_decided_by, "money")
        self.assertNotIn("market_share_stack_seq", res.rankings[0])


# ---------------------------------------------------------------------------
class TestPatientZero(unittest.TestCase):
    def test_p1_frozen_excluded_and_covered(self):
        e = eng(4, 2)
        s, st = e.state, stack_of(e)
        land(e, 0, 20)
        land(e, 1, 20)
        s.players[1].is_patient_zero = True
        frozen = (st.space[1], st.seq[1])
        from sim.engine import secret_faces

        aw = secret_faces.red_secret_payout_awards(s.config, s)
        self.assertNotIn(1, aw)
        self.assertEqual(aw[0][0], 1)  # survivors below move up
        land(e, 2, 20)  # later arrival lands on top of the frozen marker
        self.assertGreater(st.key(2), st.key(1))
        self.assertEqual((st.space[1], st.seq[1]), frozen)
        msm.queue_poach(e, s.players[3], 1)
        land(e, 3, 2)
        ev = msm.resolve_poaches(e)
        self.assertNotEqual(ev[0]["target"], 1)
        self.assertIn(ev[0]["target"], (0, 2))


# ---------------------------------------------------------------------------
class TestCap(unittest.TestCase):
    def test_k1_clamps_at_25(self):
        e = eng(3, 2)
        p = e.state.players[0]
        p.change_market_share(+50, "r2")
        self.assertEqual(p.market_share, 25)
        self.assertEqual(p.max_market_share, 25)

    def test_k2_source_scan(self):
        pat = re.compile(r"market_share\w*[^\n]*(\bor 20\b|,\s*20\))|\bor 20\b[^\n]*market_share")
        bad = []
        for sub in ("sim/engine", "sim/bots"):
            d = os.path.join(ROOT, sub)
            for fn in sorted(os.listdir(d)):
                if not fn.endswith(".py") or fn.startswith("legacy"):
                    continue
                with open(os.path.join(d, fn), encoding="utf-8") as fh:
                    for i, line in enumerate(fh, 1):
                        if pat.search(line.split("#", 1)[0]):
                            bad.append(f"{sub}/{fn}:{i}: {line.strip()}")
        self.assertEqual(bad, [])


# ---------------------------------------------------------------------------
class TestBots(unittest.TestCase):
    def test_o1_stacked_estimate(self):
        f = msm.expected_market_leader_bonus
        sched = (3, 2, 1, 0)
        self.assertEqual(f(10, [10, 8], sched, stacked=True), 3)           # matching = above
        self.assertEqual(f(10, [10, 8], sched, stacked=True, ahead_on_space=1), 2)
        self.assertEqual(f(5, [10, 9, 8], sched, stacked=True), 0)
        self.assertEqual(f(9, [10, 7, 6], (3, 2, 1), stacked=True), 2)
        self.assertEqual(f(1, [10, 9], (3, 2, 1), stacked=True), 1)         # 4P-style 3rd place
        self.assertEqual(f(0, [10, 9, 8, 7], (3, 2), stacked=True), 0)      # past the end
        self.assertEqual(f(10, [10, 8], sched), (3 + 2) / 2)                # legacy span average unchanged

    def test_o2_payout_share_delta(self):
        from sim.bots import market_share_policy as msp

        e = eng(3, 2)
        s = e.state
        land(e, 1, 20)
        land(e, 2, 10)
        land(e, 0, 12)
        p = s.players[0]
        with mock.patch.object(msp, "expected_red_payouts_remaining", return_value=1.0):
            # regain from 12 to 20 only matches the leader: ranks above it when moving (+1 place)
            self.assertGreater(msp.payout_share_delta(p, s, 12, 20), 0)
            # already on top of a shared space: passing gives nothing
            land(e, 0, 20)
            self.assertEqual(msp.ahead_on_space(p, s, 20), 0)
            self.assertEqual(msp.payout_share_delta(p, s, 20, 22), 0)
            land(e, 1, 20)  # rival now sits above the player
            self.assertEqual(msp.ahead_on_space(p, s, 20), 1)
            self.assertGreater(msp.payout_share_delta(p, s, 20, 21), 0)

    def test_o3_legacy_mode_unchanged(self):
        from sim.bots import market_share_policy as msp

        e = eng(3, 2, bot_ms_stack_aware=False)
        self.assertFalse(msp.stack_aware(e.state))
        self.assertEqual(msm.expected_market_leader_bonus(10, [10, 5], (3, 1, 0)), 2.0)


# ---------------------------------------------------------------------------
class TestSmoke(unittest.TestCase):
    def test_m1_games(self):
        for players in (2, 3, 4):
            for seed in range(42, 62):
                e = eng(players, seed)
                res = e.run_game()
                mss.audit(e.state)
                st = e.state.ms_stack
                self.assertEqual(len(set(st.seq.values())), len(st.seq))
                self.assertIsNone(st.batch_tag)
                self.assertEqual(len(res.winner_ids), 1, (players, seed))
                self.assertFalse(res.market_leader_bonus_tied_paid_place)
                self.assertEqual(res.ms_tie["mlb_effective_tie_1st"], 0)
                self.assertEqual(res.ms_tie["mlb_effective_tie_paid"], 0)
                self.assertTrue(all("market_share_stack_seq" in r for r in res.rankings))

    def test_m2_deterministic(self):
        a = eng(4, 50).run_game()
        b = eng(4, 50).run_game()
        self.assertEqual((a.winner_ids, a.total_rounds, a.ms_tie), (b.winner_ids, b.total_rounds, b.ms_tie))
        self.assertEqual([r["secrets"] for r in a.rankings], [r["secrets"] for r in b.rankings])

    def test_m3_telemetry_on_baseline_v051(self):
        res = eng(4, 50, preset="v051_roster", ms_tie_telemetry=True).run_game()
        self.assertIsNotNone(res.ms_tie)
        self.assertGreater(res.ms_tie["mlb_awards"], 0)
        self.assertEqual(res.ms_tie["arrivals_occupied"], {})
        res2 = eng(4, 50, preset="v051_roster").run_game()
        self.assertIsNone(res2.ms_tie)


class TestPhaseFunctions(unittest.TestCase):
    """Engine-level cases through the real phase functions (web path, Red clamp, Baffle Echo, corruption)."""

    def _to_phase3(self, players=3, seed=11):
        e = eng(players, seed)
        commitments = e._execute_phase_1()
        cr = e._run_phase_2_compiler(commitments)
        self.assertFalse(e.state.game_over)
        return e, commitments, cr

    def test_w1_web_path_batches_close(self):
        from sim.engine.phase3_income import execute_player_income, finalize_income

        for players, seed in ((3, 11), (4, 12), (2, 13)):
            e, commitments, cr = self._to_phase3(players, seed)
            s, st = e.state, stack_of(e)
            for p in s.players:
                if not p.is_patient_zero:
                    execute_player_income(e, p)
            finalize_income(e)
            self.assertIsNone(st.batch_tag)
            st.audit(s)
            attack = p4.execute_attack_resolution(e, commitments, cr, resolve_damage=False, finalize=False)
            for player, rolled, commits in commitments:
                if player.is_patient_zero or player.player_id in cr.breached_pids:
                    continue
                p4.resolve_player_attack(e, player, rolled, commits, attack, cr)
            p4.finalize_attack_resolution(e, cr)
            self.assertIsNone(st.batch_tag)
            st.audit(s)

    def _red_round(self, e, commitments, cr, red, **kw):
        cr.exited_cubes = {c: 0 for c in cr.exited_cubes}
        cr.exited_cubes[p4.CubeColor.RED] = red
        cr.buffer_overflow = False
        cr.breached_pids = set()
        return p4.execute_attack_resolution(e, commitments, cr, resolve_damage=True, finalize=False, **kw)

    def test_w2_phase4_red_clamp_at_zero(self):
        e, commitments, cr = self._to_phase3(3, 11)
        st = stack_of(e)
        land(e, 2, 0)
        land(e, 0, 1)
        land(e, 1, 2)
        self._red_round(e, commitments, cr, 3)
        s = e.state
        self.assertEqual([p.market_share for p in s.players], [0, 0, 0])
        self.assertIsNone(st.batch_tag)
        self.assertEqual(st.order([0, 1, 2]), [1, 0, 2])  # from 2 above from 1, both above the one already at 0

    def test_w3_phase4_baffle_echo_covers_non_mover(self):
        e, commitments, cr = self._to_phase3(3, 11)
        st = stack_of(e)
        for pid, v in ((0, 10), (1, 10), (2, 10)):
            land(e, pid, v)  # 2 on top, then 1, then 0 at the bottom? order of landing: 0, 1, 2 -> 2 on top
        self.assertEqual(st.highest([0, 1, 2]), 2)
        with mock.patch.object(p4, "is_aegis_echo_available", lambda eng_, pl: pl.player_id == 2):
            self._red_round(e, commitments, cr, 1, aegis_colors_by_pid={2: p4.CubeColor.RED})
        s = e.state
        self.assertEqual([p.market_share for p in s.players], [9, 9, 10])  # marker 2 ignores the cube and stays
        self.assertEqual(st.highest([0, 1, 2]), 2)
        self.assertEqual(st.order([0, 1, 2]), [2, 1, 0])  # 1 above 0 (kept order); 2 on 10 above them

    def test_w4_phase2_corruption_batch(self):
        from sim.entities import CorruptionSpace

        e, commitments, cr = self._to_phase3(3, 11)
        s, st = e.state, stack_of(e)
        land(e, 0, 12)
        land(e, 1, 11)
        land(e, 2, 10)
        space = CorruptionSpace(index=1, label="ms", lose_market_share=2)
        from sim.engine import phase2_compiler as p2

        p2.resolve_corruption_space(e, space, commitments, cr.exited_cubes)
        self.assertEqual([p.market_share for p in s.players], [10, 9, 8])
        self.assertIsNone(st.batch_tag)
        self.assertEqual(st.order([0, 1, 2]), [0, 1, 2])  # uniform loss keeps the ranking
        # a clamped mover lands on top of a non-mover at its new space
        land(e, 2, 0)
        land(e, 0, 1)
        p2.resolve_corruption_space(e, space, commitments, cr.exited_cubes)
        self.assertEqual(st.highest([0, 2]), 0)


class TestMsMaxFallback(unittest.TestCase):
    def test_f1_start_value_when_max_unset(self):
        c = GameConfig.v046(num_players=3)
        c.market_share_max = None
        self.assertEqual(c.ms_max(), c.market_share_start(3))
        self.assertEqual(GameConfig.v052(num_players=3).ms_max(), 25)


if __name__ == "__main__":
    unittest.main()
