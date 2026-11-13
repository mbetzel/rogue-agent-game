"""Phase 46 (v0.37.0) Market Leader Bonus: end-game Corporate Secrets by Market Share place among survivors.

Spec: docs/specs/v370_market_leader_bonus_spec.md §9 (MLB-01..MLB-26), with the §14.1 User resolutions
(2026-11-07). Background: FINDINGS.md §38.
"""

from __future__ import annotations

import dataclasses
import json
import random
import unittest
from typing import Dict, List, Optional, Sequence, Tuple
from unittest import mock

from sim.bots import market_share_policy as msp
from sim.config import CubeColor, DieColor, GameConfig, ShieldColor
from sim.engine import GameEngine
from sim.engine.market_share import (
    expected_market_leader_bonus,
    market_leader_bonus_awards,
    market_share_places,
)
from sim.entities import Face
from tests.test_v360_market_share import ANY1, MSBot, MSHarness

R, B, G = CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN
V037_SCHED = {2: (2, 0), 3: (2, 1, 0), 4: (2, 1, 0, 0)}
NEW_ROW_KEYS = ("secrets_before_bonus", "market_leader_bonus", "market_share_place")

# (held Secrets, Market Share, Money); None = Patient Zero (Secrets 0, Market Share given separately)
Row = Tuple[int, int, int]


class MLBHarness(MSHarness):
    def make_v037(self, n: int = 2, **kw) -> GameEngine:
        return self.make_ms(n=n, factory=GameConfig.v037, **kw)

    def end(self, e: GameEngine, rows: Sequence[Row], pz: Sequence[int] = ()):
        for p, (sec, ms, money) in zip(e.state.players, rows):
            p.secrets, p.market_share, p.money = sec, ms, money
        for pid in pz:
            p = e.state.players[pid]
            p.is_patient_zero = True
            p.secrets = min(p.secrets, 0)
            p.breach_depth = max(0, -p.secrets)
        e.state.game_over = True
        return e.evaluate_end_game()

    @staticmethod
    def by_pid(res) -> Dict[int, Dict]:
        return {r["player_id"]: r for r in res.rankings}

    def assert_awards(self, res, expected: Dict[int, Tuple[Optional[int], int]]):
        rows = self.by_pid(res)
        for pid, (place, bonus) in expected.items():
            r = rows[pid]
            self.assertEqual((r["market_share_place"], r["market_leader_bonus"]), (place, bonus), pid)
            self.assertEqual(r["secrets"], r["secrets_before_bonus"] + r["market_leader_bonus"], pid)


# ----------------------------------------------------------------------------------------------
# MLB-01..03 Configuration
# ----------------------------------------------------------------------------------------------
class TestConfig(unittest.TestCase):
    def test_mlb01_presets(self):
        # Phase B: GameConfig() is the v0.37.0 ruleset; legacy_v036() (alias v036()) is the v0.36.0 baseline.
        for n in (2, 3, 4):
            self.assertEqual(GameConfig(num_players=n, player_specific_corruption=False, v3_blue_secret_damage=1), GameConfig.v037(num_players=n))
            self.assertEqual(GameConfig.v036(num_players=n), GameConfig.legacy_v036(num_players=n))
            self.assertNotEqual(GameConfig(num_players=n), GameConfig.legacy_v036(num_players=n))
            for c in (GameConfig.legacy_v036(num_players=n), GameConfig.v036(num_players=n),
                      GameConfig.legacy_v035(num_players=n), GameConfig.legacy_v034(num_players=n)):
                self.assertEqual(c.market_leader_bonus_by_player_count, {})
                self.assertFalse(c.is_market_leader_bonus)
                self.assertEqual(c.market_leader_bonus_schedule(), ())
        self.assertEqual(GameConfig.v036().starting_secrets_by_player_count, {2: 7, 3: 7, 4: 8})
        b = GameConfig(red_mode="MARKET_SHARE")  # bare MARKET_SHARE resolves to v0.37.0
        self.assertEqual((b.market_leader_bonus_by_player_count, b.starting_secrets_by_player_count),
                         (V037_SCHED, {2: 9, 3: 8, 4: 9}))
        v = GameConfig.v037()
        self.assertEqual(v.market_leader_bonus_by_player_count, V037_SCHED)
        self.assertEqual(v.starting_secrets_by_player_count, {2: 9, 3: 8, 4: 9})
        for n in (2, 3, 4):  # INV-MLB-SETUP-01: v037() = v036() + the two levers, nothing else
            c37 = GameConfig.v037(num_players=n)
            self.assertTrue(c37.is_market_leader_bonus)
            self.assertEqual(c37.market_leader_bonus_schedule(), V037_SCHED[n])
            reset = dataclasses.replace(c37, market_leader_bonus_by_player_count={},
                                        starting_secrets_by_player_count={2: 7, 3: 7, 4: 8})
            self.assertEqual(reset, GameConfig.v036(num_players=n))

    def test_mlb02_validation(self):
        for sched in ({2: (2, -1)}, {3: (1, 2, 0)}, {2: (2.0, 0)}, {2: "20"}, {2: (True, 0)},
                      {1: (2,)}, {5: (2, 1, 0, 0, 0)}, {"2": (2, 0)}, {True: (2,)}):
            with self.assertRaises(ValueError, msg=sched):
                GameConfig.v036(market_leader_bonus_by_player_count=sched)
        with self.assertRaises(ValueError):
            GameConfig.legacy_v035(market_leader_bonus_by_player_count={2: (2, 0)})
        GameConfig.legacy_v035(market_leader_bonus_by_player_count={2: (0, 0)})  # all zero = off: allowed
        c = GameConfig.v036(market_leader_bonus_by_player_count={2: [2, 0]})
        self.assertEqual(c.market_leader_bonus_by_player_count, {2: (2, 0)})
        self.assertEqual(c, GameConfig.v036(market_leader_bonus_by_player_count={2: (2, 0)}))
        z = GameConfig.v036(num_players=3, market_leader_bonus_by_player_count={3: (0, 0, 0)})
        self.assertFalse(z.is_market_leader_bonus)
        self.assertEqual(z.market_leader_bonus_schedule(), ())

    def test_mlb03_schedule_accessor(self):
        c = GameConfig.v036(num_players=4, market_leader_bonus_by_player_count={4: (2,), 2: (2, 1, 0, 0)})
        self.assertEqual(c.market_leader_bonus_schedule(), (2, 0, 0, 0))  # padding
        self.assertEqual(c.market_leader_bonus_schedule(2), (2, 1))  # truncation
        self.assertEqual(c.market_leader_bonus_schedule(3), ())  # no entry -> disabled
        self.assertEqual(GameConfig.v036().market_leader_bonus_schedule(2), ())


# ----------------------------------------------------------------------------------------------
# MLB-04..16 End-game scoring
# ----------------------------------------------------------------------------------------------
class TestScoring(MLBHarness):
    def test_mlb04_distinct_shares(self):
        res = self.end(self.make_v037(2), [(5, 12, 0), (5, 9, 0)])
        self.assert_awards(res, {0: (1, 2), 1: (2, 0)})
        self.assertTrue(res.market_leader_bonus_awarded)
        self.assertEqual(res.market_leader_bonus_schedule, [2, 0])
        res = self.end(self.make_v037(3), [(5, 14, 0), (5, 11, 0), (5, 6, 0)])
        self.assert_awards(res, {0: (1, 2), 1: (2, 1), 2: (3, 0)})
        res = self.end(self.make_v037(4), [(5, 15, 0), (5, 12, 0), (5, 8, 0), (5, 3, 0)])
        self.assert_awards(res, {0: (1, 2), 1: (2, 1), 2: (3, 0), 3: (4, 0)})
        self.assertEqual(self.by_pid(res)[0]["portfolio_value"], 7)
        self.assertFalse(res.market_leader_bonus_tied_paid_place)
        # E14: market_share_bot_policy="NAIVE" -> bots ignore the bonus, but it still scores
        e = self.make_v037(3, market_share_bot_policy="NAIVE")
        self.assertFalse(msp.leader_bonus_active(e.state.players[0], e.state, msp.DEFAULT_POLICY))
        res = self.end(e, [(5, 14, 0), (5, 11, 0), (5, 6, 0)])
        self.assertTrue(res.market_leader_bonus_awarded)
        self.assert_awards(res, {0: (1, 2), 1: (2, 1), 2: (3, 0)})

    def test_mlb05_two_way_tie_for_first(self):
        res = self.end(self.make_v037(2), [(5, 10, 0), (5, 10, 0)])
        self.assert_awards(res, {0: (1, 2), 1: (1, 2)})
        self.assertTrue(res.market_leader_bonus_tied_paid_place)
        res = self.end(self.make_v037(3), [(5, 14, 0), (5, 14, 0), (5, 6, 0)])
        self.assert_awards(res, {0: (1, 2), 1: (1, 2), 2: (3, 0)})

    def test_mlb06_three_way_tie(self):
        res = self.end(self.make_v037(3), [(5, 7, 0)] * 3)
        self.assert_awards(res, {0: (1, 2), 1: (1, 2), 2: (1, 2)})
        res = self.end(self.make_v037(4), [(5, 15, 0)] * 3 + [(5, 3, 0)])
        self.assert_awards(res, {0: (1, 2), 1: (1, 2), 2: (1, 2), 3: (4, 0)})

    def test_mlb07_tie_for_second(self):
        res = self.end(self.make_v037(3), [(5, 14, 0), (5, 9, 0), (5, 9, 0)])
        self.assert_awards(res, {0: (1, 2), 1: (2, 1), 2: (2, 1)})
        self.assertTrue(res.market_leader_bonus_tied_paid_place)
        res = self.end(self.make_v037(4), [(5, 12, 0), (5, 8, 0), (5, 8, 0), (5, 2, 0)])
        self.assert_awards(res, {0: (1, 2), 1: (2, 1), 2: (2, 1), 3: (4, 0)})
        self.assertTrue(res.market_leader_bonus_tied_paid_place)
        res = self.end(self.make_v037(3), [(5, 14, 0), (5, 11, 0), (5, 6, 0)])
        self.assertFalse(res.market_leader_bonus_tied_paid_place)
        # a tie on an unpaid place is not a paid-place tie
        res = self.end(self.make_v037(4), [(5, 12, 0), (5, 8, 0), (5, 3, 0), (5, 3, 0)])
        self.assert_awards(res, {2: (3, 0), 3: (3, 0)})
        self.assertFalse(res.market_leader_bonus_tied_paid_place)

    def test_mlb08_patient_zero_excluded_places_shift(self):
        e = self.make_v037(4)
        res = self.end(e, [(6, 12, 0), (0, 16, 9), (6, 8, 0), (6, 0, 0)], pz=[1])
        self.assert_awards(res, {0: (1, 2), 1: (None, 0), 2: (2, 1), 3: (3, 0)})
        self.assertEqual(res.rankings[-1]["player_id"], 1)  # INV-MLB-ELIG-01: ranked after all survivors
        self.assertEqual(self.by_pid(res)[1]["secrets"], self.by_pid(res)[1]["secrets_before_bonus"])

    def test_mlb09_sole_survivor(self):
        for n in (2, 3):
            e = self.make_v037(n)
            rows = [(5, 3, 0)] + [(0, 15, 9)] * (n - 1)
            res = self.end(e, rows, pz=list(range(1, n)))
            self.assert_awards(res, {0: (1, 2)})
            self.assertEqual((res.winner_id, res.tiebreak_decided_by), (0, "sole_survivor"))
            self.assertEqual(res.pre_bonus_winner_ids, [0])
            self.assertFalse(res.market_leader_bonus_changed_winner)

    def test_mlb10_total_wipeout(self):
        def run(factory):
            e = self.make_ms(n=3, factory=factory)
            for p, d in zip(e.state.players, (2, 0, 5)):
                p.breach_depth = d
            return self.end(e, [(-2, 5, 1), (0, 9, 1), (-5, 9, 4)], pz=[0, 1, 2])

        res, base = run(GameConfig.v037), run(GameConfig.v036)
        self.assertTrue(res.is_total_wipeout)
        self.assertFalse(res.market_leader_bonus_awarded)
        self.assertEqual((res.market_leader_bonus_schedule, res.pre_bonus_winner_ids), ([], []))
        self.assertFalse(res.market_leader_bonus_changed_winner or res.market_leader_bonus_tied_paid_place)
        for r in res.rankings:
            self.assertEqual((r["market_leader_bonus"], r["market_share_place"]), (0, None))
        self.assertEqual(res.rankings, base.rankings)
        self.assertEqual((res.winner_id, res.tiebreak_decided_by), (base.winner_id, base.tiebreak_decided_by))

    def test_mlb11_market_collapse_player_at_zero(self):
        res = self.end(self.make_v037(3), [(5, 10, 0), (5, 6, 0), (5, 0, 0)])
        self.assert_awards(res, {0: (1, 2), 1: (2, 1), 2: (3, 0)})
        self.assertFalse(self.by_pid(res)[2]["is_patient_zero"])
        res = self.end(self.make_v037(2), [(5, 0, 0), (4, 0, 0)])
        self.assert_awards(res, {0: (1, 2), 1: (1, 2)})

    def test_mlb_e8_collapse_and_patient_zero_same_round(self):
        """E8 (engine run): Market Collapse and Patient Zero in the same Phase 4 -> the Patient Zero takes no
        place; the remaining survivors (including the one at 0 Market Share) are placed."""
        from sim.config import EndGameReason

        e = self.make_v037(3)
        p0, p1, p2 = e.state.players
        p0.market_share, p1.secrets, p2.market_share = 1, 1, 12
        self.run_phases_2_to_4(e, self.bare(e), {R: 1, B: 1})
        self.assertEqual(e.state.end_reason, EndGameReason.PATIENT_ZERO)
        self.assertEqual(e.state.end_triggers, ["patient_zero", "market_collapse"])
        self.assertTrue(p1.is_patient_zero and not p0.is_patient_zero and p0.market_share == 0)
        self.assertEqual(p2.market_share, 11)
        res = e.evaluate_end_game()
        self.assertTrue(res.market_leader_bonus_awarded)
        self.assert_awards(res, {2: (1, 2), 0: (2, 1), 1: (None, 0)})
        self.assertEqual(res.rankings[-1]["player_id"], 1)

    def test_mlb12_bonus_changes_winner(self):
        res = self.end(self.make_v037(2), [(5, 9, 0), (4, 12, 0)])
        self.assertEqual((res.pre_bonus_winner_ids, res.winner_ids), ([0], [1]))
        self.assertEqual(self.by_pid(res)[1]["secrets"], 6)
        self.assertTrue(res.market_leader_bonus_changed_winner)
        res = self.end(self.make_v037(2), [(7, 9, 0), (4, 12, 0)])
        self.assertEqual((res.pre_bonus_winner_ids, res.winner_ids), ([0], [0]))
        self.assertFalse(res.market_leader_bonus_changed_winner)

    def test_mlb13_ties_and_shared_victory(self):
        res = self.end(self.make_v037(3), [(6, 14, 0), (7, 9, 0), (3, 2, 0)])
        self.assertEqual([self.by_pid(res)[i]["secrets"] for i in range(3)], [8, 8, 3])
        self.assertEqual((res.winner_ids, res.pre_bonus_winner_ids), ([0], [1]))
        self.assertTrue(res.market_leader_bonus_changed_winner)
        self.assertEqual(res.tiebreak_decided_by, "market_share")
        # shared victory unchanged (INV-MLB-SHARED-01)
        res = self.end(self.make_v037(2), [(5, 10, 2), (5, 10, 2)])
        self.assert_awards(res, {0: (1, 2), 1: (1, 2)})
        self.assertTrue(res.is_shared_victory)
        self.assertEqual(sorted(res.pre_bonus_winner_ids), sorted(res.winner_ids))
        self.assertFalse(res.market_leader_bonus_changed_winner)
        # shared victory overtaken (E11)
        res = self.end(self.make_v037(3), [(6, 10, 0), (6, 10, 0), (5, 12, 0)])
        self.assertEqual([self.by_pid(res)[i]["secrets"] for i in range(3)], [7, 7, 7])
        self.assertEqual(sorted(res.pre_bonus_winner_ids), [0, 1])
        self.assertEqual((res.winner_ids, res.winner_id), ([2], 2))
        self.assertTrue(res.market_leader_bonus_changed_winner)

    def test_mlb14_tiebreakers_use_final_score(self):
        res = self.end(self.make_v037(3), [(5, 9, 0), (6, 12, 3), (6, 12, 5)])
        self.assert_awards(res, {0: (3, 0), 1: (1, 2), 2: (1, 2)})
        self.assertEqual([r["player_id"] for r in res.rankings], [2, 1, 0])
        self.assertEqual((res.winner_id, res.tiebreak_decided_by), (2, "money"))

    def test_mlb15_idempotent(self):
        e = self.make_v037(3)
        res1 = self.end(e, [(5, 9, 0), (6, 12, 3), (6, 12, 5)])
        held = [p.secrets for p in e.state.players]
        res2 = e.evaluate_end_game()
        self.assertEqual(json.dumps(res1.rankings, sort_keys=True, default=str),
                         json.dumps(res2.rankings, sort_keys=True, default=str))
        self.assertEqual([p.secrets for p in e.state.players], held)
        self.assertEqual(held, [5, 6, 6])

    def test_mlb16_starting_secrets(self):
        from tests.test_v360_market_share import BOT_CLASSES

        for n, want in ((2, 9), (3, 8), (4, 9)):
            e = GameEngine(GameConfig.v037(num_players=n), [BOT_CLASSES[i](i) for i in range(n)], seed=3)
            self.assertFalse(e.config.company_setup_bonuses)  # no company Secrets bonus under v0.35+ tracks
            self.assertEqual([p.secrets for p in e.state.players], [want] * n)

    def test_mlb_off_state_rows(self):
        """INV-MLB-OFF-01 on a whole game: v0.36 rows carry place telemetry but no bonus."""
        from tests.fixtures.v036_parity import capture

        res = capture.build_engine(GameConfig.v036, "setup", 3, 5).run_game()
        self.assertFalse(res.market_leader_bonus_awarded)
        for r in res.rankings:
            self.assertEqual((r["market_leader_bonus"], r["secrets_before_bonus"]), (0, r["secrets"]))
            self.assertEqual(r["market_share_place"] is None, r["is_patient_zero"] or res.is_total_wipeout)
        rr = GameEngine(GameConfig.legacy_v035(num_players=2), [MSBot(0), MSBot(1)], seed=1)
        rr.state.game_over = True
        self.assertIsNone(rr.evaluate_end_game().rankings[0]["market_share_place"])  # RANSOM: no place


# ----------------------------------------------------------------------------------------------
# MLB-17 / 18 Parity
# ----------------------------------------------------------------------------------------------
class TestParity(unittest.TestCase):
    def _replay(self, factory, scenarios, counts, seeds):
        from tests.fixtures.v036_parity import capture

        for scenario in scenarios:
            for n in counts:
                with open(capture.fixture_path(scenario, n), encoding="utf-8") as fh:
                    golden = json.load(fh)
                for seed in seeds:
                    got = json.loads(json.dumps(capture.run_scenario(factory, scenario, n, seed), sort_keys=True))
                    self.assertEqual(got, golden[str(seed)], f"{factory} {scenario} {n}P seed {seed}")

    def test_mlb17_v036_parity(self):
        from tests.fixtures.v036_parity import capture

        v036_factory = lambda **kw: GameConfig.legacy_v036(
            track_step_costs=(1, 2, 2, 3),
            max_hardware_upgrades_per_turn=999,
            **kw
        )
        # Phase B: legacy_v036() is the v0.36.0 baseline (full seeds); the v036() alias gets a 50-seed subset.
        self._replay(v036_factory, capture.SCENARIOS, capture.PLAYER_COUNTS, capture.SEEDS)
        self._replay(v036_factory, capture.SCENARIOS, capture.PLAYER_COUNTS, capture.SEEDS[:50])

    def test_mlb18_off_switch_parity(self):
        from tests.fixtures.v036_parity import capture

        zero = lambda **kw: GameConfig.v036(
            market_leader_bonus_by_player_count={3: (0, 0, 0)},
            track_step_costs=(1, 2, 2, 3),
            max_hardware_upgrades_per_turn=999,
            **kw
        )  # noqa: E731
        self._replay(zero, capture.SCENARIOS, (3,), capture.SEEDS[:20])


# ----------------------------------------------------------------------------------------------
# MLB-19 Pure helpers
# ----------------------------------------------------------------------------------------------
class TestHelpers(unittest.TestCase):
    def test_mlb19_expected_bonus(self):
        s3 = (2, 1, 0)
        for rivals, want in (([8, 5], 2.0), ([10, 5], 1.5), ([10, 10], 1.0), ([12, 10], 0.5), ([12, 11], 0.0)):
            self.assertAlmostEqual(expected_market_leader_bonus(10, rivals, s3), want, msg=rivals)
        for share, want in ((10, 1.0), (11, 2.0), (9, 0.0)):
            self.assertAlmostEqual(expected_market_leader_bonus(share, [10], (2, 0)), want)
        self.assertEqual(expected_market_leader_bonus(3, [], (2, 0)), 2.0)

    def test_places_and_awards(self):
        self.assertEqual(market_share_places({0: 14, 1: 9, 2: 9}), {0: 1, 1: 2, 2: 2})
        self.assertEqual(market_share_places({}), {})
        self.assertEqual(market_leader_bonus_awards({0: 15, 1: 15, 2: 15, 3: 3}, (2, 1)),
                         {0: (1, 2), 1: (1, 2), 2: (1, 2), 3: (4, 0)})


# ----------------------------------------------------------------------------------------------
# MLB-20..24 Bot valuation
# ----------------------------------------------------------------------------------------------
OFF_POL = dataclasses.replace(msp.DEFAULT_POLICY, leader_bonus_aware=False)


class TestBotValuation(MLBHarness):
    def _state(self, n=2, idx=1, final=False, share=10, rival_share=11, secrets=6, **kw):
        e = self.make_v037(n, **kw)
        e.state.current_version_index = idx
        e.state.is_final_round = final
        p0 = e.state.players[0]
        p0.secrets, p0.market_share = secrets, share
        for q in e.state.players[1:]:
            q.market_share = rival_share
        return e, p0

    def _incr(self, e, p0, rem=None, attack=None):
        rem = rem or {R: 1, B: 0, G: 0}
        attack = attack or {R: 1}
        on = msp.marginal_block_value(R, rem, p0, e.state, attack, msp.DEFAULT_POLICY)
        off = msp.marginal_block_value(R, rem, p0, e.state, attack, OFF_POL)
        return on - off

    def test_mlb20_red_increment(self):
        for idx, final, want in ((1, False, 1.8), (0, False, 0.9), (1, True, 3.0), (2, False, 3.0)):
            e, p0 = self._state(idx=idx, final=final)  # rival 11 - 1 Red -> projected 10
            self.assertEqual(msp.estimated_rival_shares(p0, e.state, 1), {1: 10})
            self.assertAlmostEqual(self._incr(e, p0), want, msg=(idx, final))
        e, p0 = self._state(idx=2)
        e.state.players[1].is_patient_zero = True
        self.assertAlmostEqual(self._incr(e, p0), 0.0)

    def test_mlb21_inert_when_off(self):
        def grid(make):
            out = []
            for idx in (0, 1, 2):
                for final in (False, True):
                    for share, rival in ((10, 11), (9, 10), (3, 3), (1, 8), (19, 5)):
                        e = make()
                        e.state.current_version_index, e.state.is_final_round = idx, final
                        p0, p1 = e.state.players
                        p0.secrets, p0.market_share, p1.market_share = 6, share, rival
                        for r in (1, 2):
                            out.append((idx, final, share, rival, r,
                                        msp.marginal_block_value(R, {R: r, B: 1, G: 0}, p0, e.state, {R: r, B: 1}, pol)))
                        for cap in (0, 1, 2):
                            out.append((idx, final, share, rival, cap,
                                        msp.urgent_regain(p0, e.state, pol, cap),
                                        msp._urgent_regain_v036(p0, e.state, pol, cap)))
            return out

        pol = msp.DEFAULT_POLICY
        base = grid(lambda: self.make_ms(2))
        base_naive = grid(lambda: self.make_ms(2, market_share_bot_policy="NAIVE"))
        self.assertEqual(grid(lambda: self.make_v037(2, market_share_bot_policy="NAIVE")), base_naive)
        pol = OFF_POL
        self.assertEqual(grid(lambda: self.make_v037(2)), base)
        for row in base:  # v0.36 config: the wrapper returns the v0.36 value
            if len(row) == 7:
                self.assertEqual(row[5], row[6], row)

    def test_mlb22_lethal_blue_dominates(self):
        e, p0 = self._state(final=True, secrets=1)
        alloc = msp.default_any_shield_allocation(p0, {R: 1, B: 1, G: 0}, 1, e.state, {R: 1, B: 1})
        self.assertEqual(alloc[B], 1)
        # INV-MLB-BOT-02 bound
        pol = msp.DEFAULT_POLICY
        worst = (max(pol.leader_bonus_time_weights + (pol.leader_bonus_final_round_weight,)) * pol.blue_value
                 * max(V037_SCHED[2]))
        self.assertLess(pol.red_base_value + pol.red_collapse_value + pol.red_danger_value
                        + pol.comparison_weight * 4 + worst, pol.blue_lethal_value)

    def test_mlb23_generic_shield_flips_to_red(self):
        e, p0 = self._state(idx=2, secrets=6)
        self.assertIsNone(msp.comparison_imminent(e.state))
        self.assertEqual(msp.red_pressure(e.state), 0)
        rem, attack = {R: 1, B: 1, G: 0}, {R: 1, B: 1}
        self.assertAlmostEqual(msp.marginal_block_value(R, rem, p0, e.state, attack, msp.DEFAULT_POLICY), 3.5)
        self.assertEqual(msp.default_any_shield_allocation(p0, rem, 1, e.state, attack)[R], 1)
        c, q0 = self._state(idx=2, secrets=6)
        c.state.config = GameConfig.v036(num_players=2)  # bonus-off control
        self.assertEqual(msp.default_any_shield_allocation(q0, rem, 1, c.state, attack)[B], 1)

    def test_mlb24_urgent_regain(self):
        pol = msp.DEFAULT_POLICY
        e, p0 = self._state(idx=0, share=9, rival_share=10)
        self.assertEqual(msp.urgent_regain(p0, e.state, pol, 2), msp._urgent_regain_v036(p0, e.state, pol, 2))
        self.assertEqual(msp.urgent_regain(p0, e.state, pol, 2), 0)
        e, p0 = self._state(idx=1, share=9, rival_share=10)
        self.assertEqual(msp._urgent_regain_v036(p0, e.state, pol, 2), 0)
        self.assertEqual(msp.urgent_regain(p0, e.state, pol, 2), 1)
        e, p0 = self._state(idx=1, share=9, rival_share=11)
        self.assertEqual(msp.urgent_regain(p0, e.state, pol, 2), 2)
        self.assertEqual(msp.urgent_regain(p0, e.state, pol, 1), msp._urgent_regain_v036(p0, e.state, pol, 1))
        e, p0 = self._state(idx=1, share=19, rival_share=19)
        self.assertEqual(p0.market_share_max, 19)
        self.assertEqual(msp.urgent_regain(p0, e.state, pol, 2), 0)
        e, p0 = self._state(idx=1, final=True, share=5, rival_share=19)
        self.assertEqual(msp.urgent_regain(p0, e.state, pol, 3), 3)  # Final Round: room (unchanged)
        e, p0 = self._state(idx=1, share=9, rival_share=10)
        e.state.players[1].is_patient_zero = True
        self.assertEqual(msp.urgent_regain(p0, e.state, pol, 2), msp._urgent_regain_v036(p0, e.state, pol, 2))


# ----------------------------------------------------------------------------------------------
# MLB-25 Determinism / no RNG
# ----------------------------------------------------------------------------------------------
class TestDeterminism(unittest.TestCase):
    def test_mlb25_determinism_and_no_rng(self):
        from tests.fixtures.v036_parity import capture

        def sig(n, seed):
            r = capture.build_engine(GameConfig.v037, "setup", n, seed).run_game()
            return json.dumps([r.end_reason.value, r.total_rounds, r.rankings, r.winner_ids, r.pre_bonus_winner_ids,
                               r.market_leader_bonus_changed_winner, r.market_leader_bonus_tied_paid_place,
                               r.market_leader_bonus_schedule], sort_keys=True, default=str)

        for n in (2, 3, 4):
            for seed in range(10):
                self.assertEqual(sig(n, seed), sig(n, seed), (n, seed))

        e = capture.build_engine(GameConfig.v037, "setup", 3, 4)
        for _ in range(4):
            if not e.state.game_over:
                e.run_round()
        s, p = e.state, e.state.players[0]

        def boom(*a, **k):
            raise AssertionError("RNG used")

        names = ("random", "randrange", "randint", "choice", "choices", "shuffle", "sample", "uniform", "getrandbits")
        with mock.patch.multiple(random.Random, **{nm: boom for nm in names}), \
                mock.patch.multiple("random", **{nm: boom for nm in names}):
            e.evaluate_end_game()
            for idx, final in ((1, False), (2, False), (2, True)):
                s.current_version_index, s.is_final_round = idx, final
                msp.marginal_block_value(R, {R: 2, B: 1, G: 0}, p, s, {R: 2, B: 1}, msp.DEFAULT_POLICY)
                msp.urgent_regain(p, s, msp.DEFAULT_POLICY, 2)


# ----------------------------------------------------------------------------------------------
# MLB-26 Generic shield / contested-round telemetry
# ----------------------------------------------------------------------------------------------
class TestShieldTelemetry(MLBHarness):
    def _round(self, alloc, exits, n_any=1):
        e = self.make_v037(bots=[MSBot(0, alloc=alloc), MSBot(1)])
        p0 = e.state.players[0]
        shields = [self.die(DieColor.GRAY, ANY1) for _ in range(n_any)]
        c = [self.deploy(e, p0, shields, {i: ShieldColor.ANY for i in range(n_any)}), self.deploy(e, e.state.players[1], [])]
        self.run_phases_2_to_4(e, c, exits)
        return e, p0

    def test_mlb26_counters(self):
        e, p0 = self._round({R: 1}, {R: 2, B: 2})
        self.assertEqual(p0.any_shield_allocated_by_color, {"red": 1, "blue": 0, "green": 0})
        self.assertEqual((p0.contested_defense_rounds, p0.contested_red_chosen, p0.contested_blue_left_open), (1, 1, 1))
        e.state.game_over = True
        row = {r["player_id"]: r for r in e.evaluate_end_game().rankings}[0]
        self.assertEqual((row["contested_defense_rounds"], row["contested_red_chosen"], row["contested_blue_left_open"]),
                         (1, 1, 1))
        self.assertEqual(row["any_shield_allocated_by_color"], {"red": 1, "blue": 0, "green": 0})
        self.assertEqual(row["dice_owned_final_by_color"]["gray"], 1)
        e, p0 = self._round({B: 1}, {R: 2, B: 2})
        self.assertEqual((p0.contested_defense_rounds, p0.contested_red_chosen, p0.contested_blue_left_open), (1, 0, 0))
        self.assertEqual(p0.any_shield_allocated_by_color["blue"], 1)
        # not contested: Generic shields cover everything left, or no Red left
        e, p0 = self._round({}, {R: 1, B: 1}, n_any=2)
        self.assertEqual(p0.contested_defense_rounds, 0)
        e, p0 = self._round({}, {B: 2, G: 2})
        self.assertEqual(p0.contested_defense_rounds, 0)
        self.assertEqual(e.state.players[1].any_shield_allocated_by_color, {"red": 0, "blue": 0, "green": 0})


if __name__ == "__main__":
    unittest.main()
