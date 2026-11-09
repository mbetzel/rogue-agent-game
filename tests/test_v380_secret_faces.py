"""v0.38.0 candidate: Secret faces, Processing Box, Glitched Shield Slots, Company starting die.

Spec: docs/specs/v380_secret_faces_processing_box_spec.md §13 (edge cases 1-37) with the User resolutions in
§14.1 / §14.2. Test names carry the §13 item number (``test_sfNN_*``).
"""

from __future__ import annotations

import dataclasses
import json
import unittest
from unittest import mock

from sim.config import CubeColor, DieColor, EndGameReason, GameConfig, ShieldColor
from sim.engine import GameEngine, fast_clone, secret_faces as sf
from sim.engine import phase1_roll_deploy as p1, phase2_compiler as p2, phase3_income as p3
from sim.engine import phase4_attack_resolution as p4, phase5_pipeline_shift as p5, research_tracks as rt
from sim.engine.end_game import evaluate_end_game
from sim.bots.base import BaseBot
from sim.bots import secret_face_policy as sfp
from sim.entities import (
    COMPANIES, CompanyCode, CorruptionSpace, Face, WHITE_HATS, WhiteHatCode, create_colored_die, create_gray_die,
    create_white_die, get_all_variant_cards,
)

V038 = GameConfig.v038
ALL_CARDS = get_all_variant_cards("MARKETING")


def _cards(**codes):
    """{DieColor: card} from codes like red="R1"."""
    out = {DieColor.RED: ALL_CARDS["R1"], DieColor.BLUE: ALL_CARDS["B1"], DieColor.GREEN: ALL_CARDS["G1"],
           DieColor.YELLOW: ALL_CARDS["Y1"]}
    for k, v in codes.items():
        out[DieColor(k)] = ALL_CARDS[v]
    return out


def _engine(n=3, seed=1, bots=None, companies=None, cards=None, **cfg):
    bots = bots or [BaseBot(i) for i in range(n)]
    kw = {}
    companies = companies or (CompanyCode.PROMETHEUS, CompanyCode.MERIDIAN, CompanyCode.DTO, CompanyCode.HELIX)[:n]
    if companies is not None:
        kw = dict(companies=[COMPANIES[c] for c in companies],
                  white_hats=[WHITE_HATS[w] for w in (WhiteHatCode.OPERATOR, WhiteHatCode.ACOUSTIC,
                                                       WhiteHatCode.SPOOK, WhiteHatCode.CIPHER)[:n]])
    return GameEngine(V038(num_players=n, **cfg), bots, seed=seed, variant_cards=cards or _cards(), **kw)


def _die(eng, color, **kw):
    d = create_colored_die(color=color, die_id=eng.state.next_die_id,
                           variant_card=eng.state.variant_cards.get(color),
                           face_profile=eng.config.die_face_profile, **kw)
    eng.state.next_die_id += 1
    return d


def _face(die, pred):
    return next(f for f in die.faces if pred(f))


SECRET = lambda f: f.secrets_pending  # noqa: E731
SHIELD = lambda f: f.is_shield  # noqa: E731


class _Roll:
    """Patches Die.roll: each die id maps to a list of faces returned in turn (last one repeats)."""

    def __init__(self, plan):
        self.plan = {k: list(v) for k, v in plan.items()}

    def __call__(self, die, rng):
        seq = self.plan.get(die.die_id)
        if seq:
            f = seq.pop(0) if len(seq) > 1 else seq[0]
        else:
            f = next((x for x in die.faces if x.money and not x.is_choice), die.faces[0])
        die.chosen_choice_index = None
        die.current_face = f
        return f


def _phase1(eng, plan):
    roller = _Roll(plan)
    with mock.patch("sim.entities.Die.roll", lambda die, rng: roller(die, rng)):
        return eng._execute_phase_1()


def _only(eng, pid, dice):
    p = eng.state.players[pid]
    p.ready_for_release_dice = list(dice)
    for q in eng.state.players:
        if q is not p:
            q.ready_for_release_dice = []
    return p


class NoClean(BaseBot):
    def choose_slot_cleaners(self, *a, **k):
        return []


class RerollAll(BaseBot):
    def choose_yahtzee_rerolls(self, player_state, active_dice, *a, **k):
        return list(range(len(active_dice)))


# ---------------------------------------------------------------------------
class TestSF01Parity(unittest.TestCase):
    def test_sf01_v037_parity_fixtures(self):
        from tests.fixtures.v037_parity import capture as c

        factories = {"v037": [GameConfig, GameConfig.v037], "v037_roster": [GameConfig.v037_roster]}
        for name, facs in factories.items():
            for sc in c.SCENARIOS:
                for n in c.PLAYER_COUNTS:
                    with open(c.fixture_path(name, sc, n), encoding="utf-8") as fh:
                        golden = json.load(fh)
                    for fac in facs:
                        for seed in c.SEEDS[:15]:
                            got = json.loads(json.dumps(c.run_scenario(fac, sc, n, seed), sort_keys=True))
                            self.assertEqual(got, golden[str(seed)], f"{name} {fac} {sc} {n}P {seed}")

    def test_sf01_defaults_equal(self):
        for n in (2, 3, 4):
            self.assertEqual(GameConfig(num_players=n), GameConfig.v037(num_players=n))
            self.assertFalse(GameConfig(num_players=n).secret_face_enabled)


class TestPhase1(unittest.TestCase):
    def test_sf02_secret_face_to_processing_box(self):
        eng = _engine()
        red = _die(eng, DieColor.RED)
        p = _only(eng, 0, [red])
        _phase1(eng, {red.die_id: [_face(red, SECRET)]})
        self.assertIn(red, p.glitched_dice)
        self.assertTrue(red.secret_pending)
        self.assertNotIn(red, p.in_production_dice)
        self.assertEqual(p.secret_faces_rolled, {"red": 1})
        m0 = p.money
        eng._run_phase_3_income(None)
        self.assertEqual(p.money, m0)

    def test_sf03_secret_face_rerolled_away(self):
        eng = _engine(bots=[RerollAll(0), BaseBot(1), BaseBot(2)])
        red = _die(eng, DieColor.RED)
        p = _only(eng, 0, [red])
        p.market_share = 0  # Red yield 0 -> policy rerolls it
        two = _face(red, lambda f: f.money == 2)
        _phase1(eng, {red.die_id: [_face(red, SECRET), two]})
        self.assertFalse(red.is_locked)
        self.assertIn(red, p.in_production_dice)
        self.assertFalse(red.secret_pending)
        # high yield: the policy keeps the Secret face instead
        p.market_share = 12
        dice = [red]
        red.current_face = _face(red, SECRET)
        self.assertEqual(sfp.adjust_rerolls(p.bot, p, dice, [0], eng.state, 2), [])

    def test_sf16_effective_capacity(self):
        eng = _engine(bots=[NoClean(0), BaseBot(1), BaseBot(2)])
        grays = [create_gray_die(900 + i) for i in range(3)]
        p = _only(eng, 0, grays)
        p.glitched_shield_slots = 1
        com = _phase1(eng, {g.die_id: [_face(g, SHIELD)] for g in grays})
        _, dice, commits = com[0]
        self.assertEqual(len(commits), 1)  # defense_capacity 2 - 1 glitched slot
        self.assertEqual(len(p.in_production_dice), 3)

    def test_sf17_placement_cleans_slot(self):
        eng = _engine()
        grays = [create_gray_die(900 + i) for i in range(3)]
        p = _only(eng, 0, grays)
        p.glitched_shield_slots = 1
        com = _phase1(eng, {g.die_id: [_face(g, SHIELD)] for g in grays})
        self.assertEqual(p.glitched_shield_slots, 0)
        self.assertEqual(len(p.scanned_dice), 1)
        self.assertEqual(len(com[0][2]), 2)
        self.assertEqual(p.slots_cleaned_by_die, 1)
        # White Contractor cleaner is discarded instead
        eng = _engine()
        w = create_white_die(950)
        g = create_gray_die(951)
        p = _only(eng, 0, [g])
        p.contractor_dice = [w]
        p.glitched_shield_slots = 2
        sup = eng.state.contractor_supply
        _phase1(eng, {w.die_id: [_face(w, SHIELD)], g.die_id: [_face(g, SHIELD)]})
        self.assertNotIn(w, p.contractor_dice)
        self.assertEqual(eng.state.contractor_supply, sup + 1)
        self.assertNotIn(w, p.scanned_dice)

    def test_sf18_green_f1_clean_frees_slot_this_round(self):
        eng = _engine(bots=[NoClean(0), BaseBot(1), BaseBot(2)])
        green = _die(eng, DieColor.GREEN)
        g = create_gray_die(960)
        p = _only(eng, 0, [green, g])
        p.glitched_shield_slots = 2
        f1 = _face(green, lambda f: f.is_choice and f.choices[0].clean_slots)
        com = _phase1(eng, {green.die_id: [f1], g.die_id: [_face(g, SHIELD)]})
        self.assertEqual(p.glitched_shield_slots, 1)
        self.assertEqual(len(com[0][2]), 1)
        self.assertIn(green, p.in_production_dice)
        self.assertEqual(p.slots_cleaned_by_face, 1)

    def test_sf20_white_glitch_discard_and_no_colored_glitch(self):
        eng = _engine()
        for c in (DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW, DieColor.PURPLE):
            d = _die(eng, c)
            self.assertFalse(any(f.is_glitch for f in d.faces), c)
            self.assertFalse(any(f.is_shield and f.shield_color != ShieldColor.ANY for f in d.faces), c)
        w = create_white_die(970)
        p = _only(eng, 0, [])
        p.contractor_dice = [w]
        sup = eng.state.contractor_supply
        _phase1(eng, {w.die_id: [_face(w, lambda f: f.is_glitch)]})
        self.assertNotIn(w, p.contractor_dice)
        self.assertEqual(eng.state.contractor_supply, sup + 1)

    def test_sf29_hash_matches_never_from_secret_faces(self):
        eng = _engine()
        dice = [_die(eng, DieColor.RED) for _ in range(3)]
        for d in dice:
            d.current_face = _face(d, SECRET)
        self.assertEqual(p1.detect_hash_matches(dice), 0)
        self.assertIsNone(p1.get_face_signature(dice[0].current_face))

    def test_sf32_yellow_faces(self):
        eng = _engine()
        y = _die(eng, DieColor.YELLOW)
        self.assertFalse(any(f.secrets_pending or f.is_shield for f in y.faces))
        choice = [f for f in y.faces if f.is_choice]
        self.assertEqual(len(choice), 3)
        p = _only(eng, 0, [y])
        _phase1(eng, {y.die_id: [choice[0]]})
        m0, r0 = p.money, p.research_tokens
        eng._run_phase_3_income(None)
        self.assertIn((p.money - m0, p.research_tokens - r0), ((2, 0), (0, 1)))


class TestYields(unittest.TestCase):
    def setUp(self):
        self.eng = _engine()
        self.p = self.eng.state.players[0]
        self.cfg = self.eng.config

    def test_sf06_red_tiers(self):
        for share, y in ((12, 3), (9, 3), (8, 2), (5, 2), (4, 1), (1, 1), (0, 0)):
            self.p.market_share = share
            self.assertEqual(sf.secret_yield(self.cfg, self.p, DieColor.RED), y, share)

    def test_sf08_blue(self):
        p = self.p
        self.assertEqual(sf.secret_yield(self.cfg, p, DieColor.BLUE), 1)
        p.blocked_blue_this_round = 1
        self.assertEqual(sf.secret_yield(self.cfg, p, DieColor.BLUE), 2)
        p.defense_level = 3
        self.assertEqual(sf.secret_yield(self.cfg, p, DieColor.BLUE), 3)
        cfg = dataclasses.replace(self.cfg, secret_yield_blue_base=3)
        self.assertEqual(sf.secret_yield(cfg, p, DieColor.BLUE), 3)  # cap

    def test_sf08_baffle_echo_not_blocked(self):
        eng = _engine(companies=(CompanyCode.AEGIS, CompanyCode.DTO, CompanyCode.HELIX))
        p = eng.state.players[0]
        attack = {CubeColor.RED: 0, CubeColor.BLUE: 1, CubeColor.GREEN: 0}
        p4.resolve_player_defense_and_wear(eng, p, [], {}, attack, dict(attack), "",
                                           malware_target_policy=p4.MALWARE_POLICY_SIX_PHASE)
        self.assertEqual(p.blocked_blue_this_round, 0)
        self.assertEqual(p.last_defense_breakdown["effective_attacks"]["blue"], 0)

    def test_sf08_blocked_blue_recorded(self):
        eng = _engine()
        p = eng.state.players[0]
        g = create_gray_die(990)
        g.current_face = _face(g, SHIELD)
        p.in_production_dice = [g]
        attack = {CubeColor.RED: 0, CubeColor.BLUE: 1, CubeColor.GREEN: 0}
        p4.resolve_player_defense_and_wear(eng, p, [g], {0: ShieldColor.ANY}, attack, dict(attack), "",
                                           malware_target_policy=p4.MALWARE_POLICY_SIX_PHASE)
        self.assertEqual(p.blocked_blue_this_round, 1)

    def test_sf09_banking_round_flag(self):
        p = self.p
        b = _die(self.eng, DieColor.BLUE)
        b.secret_pending = True
        p.glitched_dice = [b]
        p.blocked_blue_this_round = 1
        sf.record_round_start(p)  # next round: flag reset
        self.assertEqual(sf.bank(self.cfg, p, b), 1)

    def test_sf10_green(self):
        p = self.p
        for slots, y in ((0, 3), (1, 2), (2, 1), (3, 0), (4, 0)):
            p.glitched_shield_slots = slots
            self.assertEqual(sf.secret_yield(self.cfg, p, DieColor.GREEN), y)

    def test_sf11_purple(self):
        self.assertEqual(sf.secret_yield(self.cfg, self.p, DieColor.PURPLE), 1)


class TestPhase5(unittest.TestCase):
    def _pending(self, eng, p, colors):
        dice = []
        for c in colors:
            d = _die(eng, c)
            d.secret_pending = True
            dice.append(d)
        p.glitched_dice = list(dice)
        return dice

    def test_sf04_bandwidth(self):
        eng = _engine()
        p = eng.state.players[0]
        dice = self._pending(eng, p, [DieColor.PURPLE] * 3)
        s0 = p.secrets
        moved = p5.conveyor_triage_v038(eng, p)
        self.assertEqual(len(moved), 2)
        self.assertEqual(p.secrets - s0, 2)
        self.assertTrue(p.glitched_dice[0].secret_pending)
        moved = p5.conveyor_triage_v038(eng, p)
        self.assertEqual(p.secrets - s0, 3)
        self.assertEqual(set(d.die_id for d in p.scanned_dice), {d.die_id for d in dice})

    def test_sf05_triage_order(self):
        eng = _engine()
        p = eng.state.players[0]
        purple, red = self._pending(eng, p, [DieColor.PURPLE, DieColor.RED])
        p.triage_bandwidth = 1
        p5.conveyor_triage_v038(eng, p)
        self.assertEqual(p.scanned_dice, [red])  # yield 3 before 1

        class Purple1st(BaseBot):
            def choose_triage_order(self, player_state, dice, game_state=None):
                return sorted(dice, key=lambda d: d.color != DieColor.PURPLE)

        eng = _engine(bots=[Purple1st(0), BaseBot(1), BaseBot(2)])
        p = eng.state.players[0]
        purple, red = self._pending(eng, p, [DieColor.PURPLE, DieColor.RED])
        p.triage_bandwidth = 1
        p5.conveyor_triage_v038(eng, p)
        self.assertEqual(p.scanned_dice, [purple])

    def test_sf07_red_after_damage(self):
        eng = _engine()
        p = eng.state.players[0]
        p.market_share = 9
        (red,) = self._pending(eng, p, [DieColor.RED])
        p.in_production_dice = []
        attack = {CubeColor.RED: 1, CubeColor.BLUE: 0, CubeColor.GREEN: 0}
        p4.resolve_player_defense_and_wear(eng, p, [], {}, attack, dict(attack), "",
                                           malware_target_policy=p4.MALWARE_POLICY_SIX_PHASE)
        self.assertEqual(p.market_share, 8)
        s0 = p.secrets
        p5.conveyor_triage_v038(eng, p)
        self.assertEqual(p.secrets - s0, 2)

    def test_sf10_sf19_graduation_clear(self):
        eng = _engine()
        p = eng.state.players[0]
        (green,) = self._pending(eng, p, [DieColor.GREEN])
        p.glitched_shield_slots = 2
        p.scanned_dice = []
        p.in_production_dice = []
        p.ready_for_release_dice = []
        s0 = p.secrets
        p5.execute_player_pipeline_shift(eng, p)  # 0 graduates -> no clear
        self.assertEqual(p.glitched_shield_slots, 2)
        self.assertEqual(p.secrets - s0, 1)
        eng = _engine()
        p = eng.state.players[0]
        (green,) = self._pending(eng, p, [DieColor.GREEN])
        p.glitched_shield_slots = 2
        p.ready_for_release_dice = []
        p.scanned_dice = [create_gray_die(980 + i) for i in range(3)]
        s0 = p.secrets
        p5.execute_player_pipeline_shift(eng, p)  # 3 graduates -> 1 clear only, before triage
        self.assertEqual(p.glitched_shield_slots, 1)
        self.assertEqual(p.slots_cleared_by_graduation, 1)
        self.assertEqual(p.secrets - s0, 2)

    def test_sf25_magnetic_splice_banks_before_clear(self):
        eng = _engine(companies=(CompanyCode.OMNIDYNE, CompanyCode.DTO, CompanyCode.HELIX))
        p = eng.state.players[0]
        (green,) = self._pending(eng, p, [DieColor.GREEN])
        p.glitched_shield_slots = 1
        p.scanned_dice = [create_gray_die(985)]
        p.in_production_dice = []
        s0 = p.secrets
        p5.execute_player_pipeline_shift(eng, p)
        self.assertIn(green, p.ready_for_release_dice)
        self.assertEqual(p.secrets - s0, 2)  # yield read at step 1 (1 slot), before the 3b clear
        self.assertEqual(p.glitched_shield_slots, 0)

    def test_sf37_non_pending_yields_zero(self):
        eng = _engine()
        p = eng.state.players[0]
        d = _die(eng, DieColor.RED)
        p.glitched_dice = [d]  # e.g. a legacy dirty-income backlash die
        s0 = p.secrets
        p5.conveyor_triage_v038(eng, p)
        self.assertEqual(p.secrets, s0)
        self.assertIn(d, p.scanned_dice)


class TestDamageAndCorruption(unittest.TestCase):
    def test_sf14_green_glitches_slots(self):
        eng = _engine()
        p = eng.state.players[0]
        g = create_gray_die(991)
        g.current_face = _face(g, lambda f: f.money)
        p.in_production_dice = [g]
        attack = {CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 5}
        p4.resolve_player_defense_and_wear(eng, p, [g], {}, attack, dict(attack), "",
                                           malware_target_policy=p4.MALWARE_POLICY_SIX_PHASE)
        self.assertEqual(p.glitched_shield_slots, p.defense_capacity)  # capped; excess no effect
        self.assertIn(g, p.in_production_dice)
        self.assertEqual(p.glitched_dice, [])
        p.defense_capacity += 1  # new capacity arrives clean
        self.assertEqual(sf.effective_capacity(p), 1)

    def test_sf15_corruption_glitches_slots(self):
        eng = _engine()
        com = [(p, [], {}) for p in eng.state.players]
        p2.resolve_corruption_space(eng, CorruptionSpace(index=1, label="x", demote_dice=2), com, {})
        self.assertTrue(all(p.glitched_shield_slots == 2 for p in eng.state.players))
        self.assertEqual(eng.state.players[0].slots_glitched_by_source, {"corruption": 2})

    def test_sf28_return_colored_loses_secret(self):
        eng = _engine()
        p = eng.state.players[0]
        d = _die(eng, DieColor.RED)
        d.secret_pending = True
        p.glitched_dice = [d]
        p.ready_for_release_dice = []
        p.in_production_dice = []
        p.scanned_dice = []
        p2.return_player_colored_dice_step2a(eng, p, [], {}, 1)
        self.assertEqual(p.glitched_dice, [])
        self.assertEqual(p.secrets_lost_returned, 1)
        self.assertFalse(d.secret_pending)

    def test_sf30_no_market_collapse(self):
        eng = _engine()
        p = eng.state.players[0]
        p.market_share = 0
        p4.check_end_triggers_after_attacks(eng)
        self.assertFalse(eng.state.is_final_round)
        self.assertNotIn("market_collapse", eng.state.end_triggers)
        self.assertEqual(sf.secret_yield(eng.config, p, DieColor.RED), 0)


class TestIncome(unittest.TestCase):
    def test_sf26_jumper_diagnostics(self):
        eng = _engine()
        p = eng.state.players[0]
        b = _die(eng, DieColor.BLUE)
        b.secret_pending = True
        p.glitched_dice = [b]
        p.blocked_blue_this_round = 0
        s0 = p.secrets
        p3.resolve_phreaker_jumper_diagnostics(eng, p)
        self.assertEqual(p.secrets - s0, 1)  # Phase-3 state: no Blue block bonus
        self.assertIn(b, p.scanned_dice)
        m0 = p.money
        p.scanned_dice = []
        p3.resolve_phreaker_jumper_diagnostics(eng, p)
        self.assertEqual(p.money - m0, 1)
        g = create_gray_die(992)
        p.scanned_dice = [g]
        roller = _Roll({992: [_face(g, lambda f: f.money == 1 and f.patches == 1)]})
        with mock.patch("sim.entities.Die.roll", lambda die, rng: roller(die, rng)):
            p3.resolve_phreaker_jumper_diagnostics(eng, p)
        self.assertIn(g, p.scanned_dice)
        self.assertEqual(p.money - m0, 2)

    def test_sf27_b3_and_y3(self):
        eng = _engine(cards=_cards(blue="B3", yellow="Y3"))
        p = eng.state.players[0]
        purple = _die(eng, DieColor.PURPLE)
        purple.secret_pending = True
        p.glitched_dice = [purple]
        b3 = _die(eng, DieColor.BLUE)
        b3.current_face = _face(b3, lambda f: f.star_code == "B3")
        self.assertFalse(b3.current_face.is_shield)
        y3 = _die(eng, DieColor.YELLOW)
        y3.current_face = _face(y3, lambda f: f.star_code == "Y3")
        p.in_production_dice = [b3, y3]
        s0 = p.secrets
        p3.collect_player_production_income(eng, p)
        self.assertEqual(p.secrets - s0, 2)  # Purple Secret banked + Y3
        self.assertIn(purple, p.scanned_dice)
        self.assertIn(y3, p.scanned_dice)
        self.assertNotIn(y3, p.glitched_dice)

    def test_sf31_red_market_share_clamp(self):
        eng = _engine()
        p = eng.state.players[0]
        r = _die(eng, DieColor.RED)
        r1 = _face(r, lambda f: f.star_code == "R1")
        self.assertEqual((r1.market_share, r1.money, r1.is_shield), (1, 2, False))
        r.current_face = r1
        p.in_production_dice = [r]
        p.market_share = 11
        p3.collect_player_production_income(eng, p)
        p.in_production_dice = [r]
        p3.collect_player_production_income(eng, p)
        self.assertEqual(p.market_share, 12)
        self.assertEqual(p.regain_this_turn, 0)
        self.assertEqual(p.market_share_gained_face, 1)


class TestSetupAndTracks(unittest.TestCase):
    def test_sf21_company_starting_die(self):
        comps = (CompanyCode.MERIDIAN, CompanyCode.DTO, CompanyCode.OMNIDYNE)
        eng = _engine(companies=comps)
        want = {CompanyCode.MERIDIAN: DieColor.RED, CompanyCode.DTO: DieColor.BLUE, CompanyCode.OMNIDYNE: DieColor.GREEN}
        for p, c in zip(eng.state.players, comps):
            colors = [d.color for d in p.ready_for_release_dice]
            self.assertEqual(colors.count(DieColor.GRAY), 2)
            self.assertEqual(colors.count(DieColor.PURPLE), 1)
            col = [d for d in p.ready_for_release_dice if d.color == want[c]]
            self.assertEqual(len(col), 1)
            self.assertEqual(col[0].variant_code, eng.state.variant_cards[want[c]].code)
            ids = [d.die_id for d in p.ready_for_release_dice]
            self.assertEqual(ids, sorted(ids))  # Gray, Company die, Purple
            self.assertEqual(p.ready_for_release_dice[2].color, want[c])
        for c in (DieColor.RED, DieColor.BLUE, DieColor.GREEN):
            self.assertEqual(eng.state.market[c], 2 * 3 - 1)
        self.assertEqual(eng.state.market[DieColor.YELLOW], 6)
        self.assertEqual(len(eng.state.players[0].total_dice), 4)  # INV-SF-07
        e2 = _engine(companies=comps)
        self.assertEqual([[d.die_id for d in p.ready_for_release_dice] for p in eng.state.players],
                         [[d.die_id for d in p.ready_for_release_dice] for p in e2.state.players])

    def test_sf22_triage_l1_gray(self):
        eng = _engine()
        p = eng.state.players[0]
        n0, w0 = len(p.ready_for_release_dice), len(p.contractor_dice)
        rt.resolve_breakthrough(eng, p, "TRIAGE", 1)
        self.assertEqual(len(p.ready_for_release_dice), n0 + 1)
        self.assertEqual(p.ready_for_release_dice[-1].color, DieColor.GRAY)
        self.assertEqual(len(p.contractor_dice), w0)

    def test_sf23_ace_secret_face(self):
        for allow in (False, True):
            eng = _engine(ace_allows_secret_face=allow)
            p = eng.state.players[0]
            purple = _die(eng, DieColor.PURPLE)
            purple.current_face = _face(purple, lambda f: f.star_code == "PURPLE_STAR")
            red = _die(eng, DieColor.RED)
            red.current_face = _face(red, lambda f: f.money == 2)
            ok = p1.resolve_prodigy_purple_star_override(p, [purple, red], eng.rng, 1, _face(red, SECRET))
            self.assertEqual(ok, allow)
            self.assertEqual(red.current_face.secrets_pending, allow)

    def test_sf24_brute_force_bypass(self):
        class Helix(BaseBot):
            calls = 0

            def choose_helix_override(self, *a, **k):
                return True

            def choose_yahtzee_rerolls(self, player_state, active_dice, *a, **k):
                Helix.calls += 1
                return [1]

            def choose_helix_face_override_v038(self, player_state, active_dice, game_state):
                return 0, _face(active_dice[0], SECRET)

        eng = _engine(bots=[Helix(0), BaseBot(1), BaseBot(2)],
                      companies=(CompanyCode.HELIX, CompanyCode.DTO, CompanyCode.AEGIS))
        red, g = _die(eng, DieColor.RED), create_gray_die(993)
        p = _only(eng, 0, [red, g])
        _phase1(eng, {})
        self.assertEqual(Helix.calls, eng.config.default_free_rerolls + 1)
        self.assertTrue(red.secret_pending)
        self.assertIn(red, p.glitched_dice)


class TestEndGame(unittest.TestCase):
    def test_sf12_sf13_stranded(self):
        eng = _engine()
        p = eng.state.players[0]
        d = _die(eng, DieColor.RED)
        d.secret_pending = True
        p.glitched_dice = [d]
        p2._six_phase_singularity_cleanup(eng)
        self.assertIn(d, p.glitched_dice)
        s0 = p.secrets
        r1 = evaluate_end_game(eng)
        r2 = evaluate_end_game(eng)
        row = next(r for r in r1.rankings if r["player_id"] == 0)
        self.assertEqual((row["stranded_dice"], row["stranded_secrets"]), (1, 3))
        self.assertEqual(row["secrets_before_bonus"], s0)
        self.assertEqual(r1.rankings, r2.rankings)  # pure, idempotent

    def test_sf13_patient_zero_final_round_runs_phase5(self):
        found = 0
        from tests.fixtures.v035_parity.capture import build_engine

        for seed in range(40):
            res = build_engine(V038, "setup", 3, seed).run_game()
            if res.end_reason == EndGameReason.PATIENT_ZERO and res.telemetry_history[-1].final_round_trigger_phase:
                last = res.telemetry_history[-1]
                if last.end_phase == 6:
                    self.assertIn(5, last.phases_executed)
                    found += 1
        self.assertGreater(found, 0)

    def test_sf33_market_leader_bonus_after_stranded(self):
        eng = _engine()
        for p, ms in zip(eng.state.players, (12, 8, 4)):
            p.market_share = ms
        d = _die(eng, DieColor.PURPLE)
        d.secret_pending = True
        eng.state.players[0].glitched_dice = [d]
        res = evaluate_end_game(eng)
        row = next(r for r in res.rankings if r["player_id"] == 0)
        self.assertEqual(row["market_leader_bonus"], 2)
        self.assertEqual(row["secrets"], row["secrets_before_bonus"] + 2)
        self.assertEqual(row["secrets_by_source"]["market_leader_bonus"], 2)
        for p in eng.state.players:
            p.is_patient_zero = True
        res = evaluate_end_game(eng)
        self.assertTrue(all(r["market_leader_bonus"] == 0 for r in res.rankings))


class TestConfig(unittest.TestCase):
    def test_sf34_validation(self):
        bad = [
            dict(secret_face_enabled=True),  # V037 face profile
            dict(die_face_profile="V038_DRAFT"),  # without banking
            dict(die_face_profile="X"),
            dict(triage_l1_breakthrough="X"),
            dict(secret_yield_red_tiers=((5, 2), (9, 3), (0, 0))),
            dict(secret_yield_red_tiers=((9, 3), (5, 2), (1, 1))),
            dict(secret_yield_red_tiers=((9, -1), (0, 0))),
            dict(secret_yield_blue_cap=0, secret_yield_blue_base=1),
            dict(company_starting_die_enabled=True, company_starting_colors={"MERIDIAN": "RED"}),
        ]
        for kw in bad:
            with self.assertRaises(ValueError, msg=kw):
                GameConfig.v037(**kw)
        with self.assertRaises(ValueError):
            V038(glitched_shield_slots_enabled=False)
        with self.assertRaises(ValueError):
            V038(dirty_income_enabled=True)
        with self.assertRaises(ValueError):
            V038(starting_gray_dice=0)
        with self.assertRaises(ValueError):
            GameConfig.legacy_v035(secret_face_enabled=True, die_face_profile="V038_DRAFT",
                                   glitched_shield_slots_enabled=True)
        GameConfig.v037(glitched_shield_slots_enabled=True)  # ablation allowed
        V038(market_collapse_enabled=True)  # ablation allowed

    def test_presets(self):
        c = V038(num_players=4)
        self.assertEqual((c.market_share_start(), c.get_starting_secrets(), c.market_collapse_enabled),
                         (12, 5, False))
        self.assertEqual(set(c.share_regain_cost_by_level.values()), {3})
        self.assertEqual(c.share_regain_cap_by_level, GameConfig.v037().share_regain_cap_by_level)
        r = GameConfig.v038_roster(num_players=3)
        self.assertTrue(r.bot_pr_push)
        self.assertEqual(dataclasses.replace(r, bot_pr_push=False), V038(num_players=3))


class TestCloneAndDeterminism(unittest.TestCase):
    def test_sf35_fast_clone_resume(self):
        from tests.test_reference_bot import SnapAtEngine, _summary
        from tests.fixtures.v035_parity import capture

        for n in (2, 3, 4):
            for seed in range(12):
                for phase in (1, 4, 6):
                    cls = type("E", (SnapAtEngine,), {"want": (2 + seed % 3, phase)})
                    with mock.patch("sim.engine.GameEngine", cls):
                        e = capture.build_engine(V038, "setup", n, seed)
                    real = e.run_game()
                    if e.kept is None:
                        continue
                    c, com, cr = fast_clone.from_snapshot(e.kept)
                    fast_clone.resume_round(c, phase, com, cr)
                    got = c.run_game() if not c.state.game_over else c.evaluate_end_game()
                    self.assertEqual(_summary(got), _summary(real), f"{n}P seed {seed} phase {phase}")
                    self.assertEqual([r["secrets_by_source"] for r in got.rankings],
                                     [r["secrets_by_source"] for r in real.rankings])

    def test_sf36_determinism(self):
        from tests.fixtures.v035_parity.capture import build_engine

        for seed in range(5):
            a = build_engine(V038, "setup", 3, seed)
            b = build_engine(V038, "setup", 3, seed)
            ra, rb = a.run_game(), b.run_game()
            self.assertEqual(ra.rankings, rb.rankings)
            self.assertEqual(a.rng.getstate(), b.rng.getstate())


class TestStrandedEndings(unittest.TestCase):
    """Staff review R1-R4: full-engine stranded paths, capacity increase, Jumper Diagnostics shield fallback."""

    def _setup(self, companies=None, **cfg):
        eng = _engine(companies=companies, **cfg)
        red = _die(eng, DieColor.RED)
        p = _only(eng, 0, [red])
        p.market_share = 12
        return eng, p, red

    def _round(self, eng, red, drop):
        roller = _Roll({red.die_id: [_face(red, SECRET)]})

        with mock.patch("sim.entities.Die.roll", lambda die, rng: roller(die, rng)), \
                mock.patch.object(eng.state.tower, "drop", lambda cubes, rng: dict(drop)):
            eng.run_round()

    def _row(self, eng):
        return next(r for r in evaluate_end_game(eng).rankings if r["player_id"] == 0)

    def test_r1_singularity_strands_phase1_secret(self):
        eng, p, red = self._setup()
        s = eng.state
        s.current_version_index = len(s.version_deck) - 1
        s.corruption_track = s.corruption_track_capacity - 1
        s0 = p.secrets
        self._round(eng, red, {CubeColor.BLACK: 1})
        self.assertEqual(s.end_reason, EndGameReason.SINGULARITY)
        self.assertTrue(red.secret_pending)
        row = self._row(eng)
        self.assertEqual(p.secret_faces_banked, {})
        self.assertEqual(row["secrets_before_bonus"], p.secrets)  # nothing banked
        self.assertLessEqual(p.secrets, s0)
        self.assertNotIn("secret_face_red", p.secrets_by_source)
        self.assertEqual((row["stranded_dice"], row["stranded_secrets"]), (1, 3))

    def test_r2_total_wipeout_strands(self):
        eng, p, red = self._setup(companies=(CompanyCode.PROMETHEUS, CompanyCode.MERIDIAN, CompanyCode.HELIX))
        for q in eng.state.players:
            q.secrets = 1
        self._round(eng, red, {CubeColor.BLUE: 3})
        self.assertEqual(eng.state.end_reason, EndGameReason.TOTAL_WIPEOUT)
        row = self._row(eng)
        self.assertNotIn("secret_face_red", p.secrets_by_source)
        self.assertEqual((row["stranded_dice"], row["stranded_secrets"]), (1, 3))

    def test_r2_round_limit_strands(self):
        eng, p, red = self._setup(max_rounds=1)
        p.triage_bandwidth = 0  # stays pending through Phase 5
        self._round(eng, red, {CubeColor.RED: 0, CubeColor.BLACK: 0})
        self.assertEqual(eng.state.end_reason, EndGameReason.ROUND_LIMIT)
        self.assertTrue(eng.state.game_over)
        row = self._row(eng)
        self.assertNotIn("secret_face_red", p.secrets_by_source)
        self.assertEqual((row["stranded_dice"], row["stranded_secrets"]), (1, 3))

    def test_r3_capacity_increase_adds_clean_slot(self):
        eng = _engine()
        p = eng.state.players[0]
        p.defense_level = 1
        p.glitched_shield_slots = 2
        p.research_tokens = 10
        cap0 = p.defense_capacity
        self.assertTrue(p.upgrade_track("DEFENSE"))
        self.assertEqual(p.defense_capacity, cap0 + 1)
        self.assertEqual(p.glitched_shield_slots, 2)
        self.assertEqual(sf.effective_capacity(p), 1)

    def test_r4_jumper_scanned_shield_no_output(self):
        eng = _engine()
        p = eng.state.players[0]
        p.glitched_dice = []
        g = create_gray_die(994)
        p.scanned_dice = [g]
        m0, r0, s0 = p.money, p.research_tokens, p.secrets
        roller = _Roll({994: [_face(g, SHIELD)]})
        with mock.patch("sim.entities.Die.roll", lambda die, rng: roller(die, rng)):
            face = p3.resolve_phreaker_jumper_diagnostics(eng, p)
        self.assertTrue(face.is_shield)
        self.assertEqual((p.money, p.research_tokens, p.secrets), (m0, r0, s0))
        self.assertIn(g, p.scanned_dice)


class TestCandidate2(unittest.TestCase):
    """spec §14.3 (User 2026-11-08, FINDINGS §43): GameConfig.v038b()."""

    def _eng(self, **cfg):
        bots = [BaseBot(i) for i in range(3)]
        comps = (CompanyCode.PROMETHEUS, CompanyCode.MERIDIAN, CompanyCode.HELIX)
        return GameEngine(GameConfig.v038b(num_players=3, **cfg), bots, seed=1, variant_cards=_cards(),
                          companies=[COMPANIES[c] for c in comps],
                          white_hats=[WHITE_HATS[w] for w in (WhiteHatCode.OPERATOR, WhiteHatCode.ACOUSTIC,
                                                               WhiteHatCode.CIPHER)])

    def test_preset_values(self):
        for n, sec in ((2, 3), (3, 4), (4, 4)):
            c = GameConfig.v038b(num_players=n)
            self.assertEqual(c.get_starting_secrets(), sec)
            self.assertTrue(c.market_collapse_enabled)
            self.assertEqual(c.secret_yield_red_tiers, ((11, 3), (7, 2), (3, 1), (0, 0)))
            self.assertEqual(c.die_face_profile, "V038_YELLOW_MS")
            self.assertFalse(c.bot_pr_push)
            self.assertEqual(c.market_share_start(), 14)
            self.assertEqual(c.market_leader_bonus_schedule(), {2: (4, 0), 3: (4, 2, 0), 4: (4, 2, 0, 0)}[n])
            self.assertIsNone(c.glitched_slots_per_round_cap)
        base = V038(num_players=3)  # first-sweep preset unchanged
        self.assertEqual((base.market_collapse_enabled, base.get_starting_secrets(), base.die_face_profile),
                         (False, 5, "V038_DRAFT"))
        self.assertEqual(base.secret_yield_red_tiers, ((9, 3), (5, 2), (1, 1), (0, 0)))
        for share, y in ((12, 3), (11, 3), (10, 2), (7, 2), (6, 1), (3, 1), (2, 0), (0, 0)):
            p = self._eng().state.players[0]
            p.market_share = share
            self.assertEqual(sf.secret_yield(p.config, p, DieColor.RED), y, share)
        with self.assertRaises(ValueError):
            GameConfig.v038b(glitched_slots_per_round_cap=-1)
        with self.assertRaises(ValueError):
            GameConfig.v037(die_face_profile="V038_YELLOW_MS")

    def test_market_collapse_fires(self):
        eng = self._eng()
        p = eng.state.players[0]
        p.market_share = 1
        p.in_production_dice = []
        attack = {CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 0}
        p4.resolve_player_defense_and_wear(eng, p, [], {}, attack, dict(attack), "",
                                           malware_target_policy=p4.MALWARE_POLICY_SIX_PHASE)
        self.assertEqual(p.market_share, 0)
        p4.check_end_triggers_after_attacks(eng)
        self.assertIn("market_collapse", eng.state.end_triggers)
        self.assertTrue(eng.state.is_final_round)
        self.assertFalse(p.is_patient_zero)
        from tests.fixtures.v035_parity.capture import build_engine

        n = sum(build_engine(GameConfig.v038b, "setup", 3, s).run_game().end_reason == EndGameReason.MARKET_COLLAPSE
                for s in range(30))
        self.assertGreater(n, 0)

    def test_yellow_faces_phase3_cap(self):
        for prof, f1 in (("V038_YELLOW_MS", (0, 2)), ("V038_YELLOW_MS_ALT", (1, 1))):
            eng = self._eng(die_face_profile=prof)
            y = _die(eng, DieColor.YELLOW)
            self.assertFalse(any(f.secrets_pending or f.is_shield for f in y.faces))
            self.assertEqual((y.faces[0].money, y.faces[0].market_share), f1)
            self.assertEqual([f.money for f in y.faces[2:3]], [3])
            self.assertTrue(y.faces[5].is_star)
            p = eng.state.players[0]
            self.assertEqual(p.market_share_max, 14)
            p.market_share = 13
            y.current_face = y.faces[0]
            p.in_production_dice = [y]
            m0 = p.money
            p3.collect_player_production_income(eng, p)
            self.assertEqual(p.market_share, 14)  # clamped at the maximum
            self.assertEqual(p.money - m0, f1[0])
            self.assertEqual(p.regain_this_turn, 0)  # outside the Public Relations limit
            # F2 choice "+1 Market Share / +1 🔬": the policy takes research at the maximum
            y.current_face = y.faces[1]
            ch = sfp.adjust_declared_choices(p.bot, p, [y], {0: 0}, eng.state)
            self.assertEqual(ch[0], 1)
            p.market_share = 5
            self.assertEqual(sfp.adjust_declared_choices(p.bot, p, [y], {0: 1}, eng.state)[0], 0)
            y.chosen_choice_index = 0
            p3.collect_player_production_income(eng, p)
            self.assertEqual(p.market_share, 6)

    def test_share_value_policy(self):
        eng = self._eng()
        p = eng.state.players[0]
        p.market_share = 6  # +1 crosses the 7 tier: worth more with Red dice owned
        plain = sfp.share_value(p, eng.state, 1)
        p.glitched_dice = [_die(eng, DieColor.RED)]
        p.glitched_dice[0].secret_pending = True
        self.assertGreater(sfp.share_value(p, eng.state, 1), plain)
        p.market_share = 14
        self.assertEqual(sfp.share_value(p, eng.state, 1), 0.0)
        p.market_share = 0
        self.assertGreaterEqual(sfp.share_value(p, eng.state, 1), 4.0)  # Market Collapse risk

    def test_yellow_purchase_scored_by_market_share(self):
        eng = self._eng()
        p = eng.state.players[0]
        bot = p.bot
        p.market_share = 14
        high = sfp.color_score(bot, p, eng.state, DieColor.YELLOW)
        p.market_share = 2  # low share: Market Collapse risk + Market Leader Bonus place -> Yellow worth more
        low = sfp.color_score(bot, p, eng.state, DieColor.YELLOW)
        self.assertGreater(low, high)
        die = _die(eng, DieColor.YELLOW)
        self.assertNotEqual(sfp.yellow_ms_score(p, eng.state, die), sfp.mean_reroll_value(p, eng.state, die, 0))
        # v038 draft profile: Yellow keeps the Money valuation (first-sweep reproducibility)
        e2 = _engine()
        q = e2.state.players[0]
        a = sfp.color_score(q.bot, q, e2.state, DieColor.YELLOW)
        q.market_share = 2
        self.assertEqual(sfp.color_score(q.bot, q, e2.state, DieColor.YELLOW), a)

    def test_slot_cap(self):
        eng = self._eng(glitched_slots_per_round_cap=1)
        p = eng.state.players[0]
        p.defense_capacity = 4
        self.assertEqual(sf.glitch_slots(p, 3, "green_cube"), 1)
        self.assertEqual(sf.glitch_slots(p, 1, "corruption"), 0)  # cap is across all sources
        self.assertEqual(p.glitched_shield_slots, 1)
        sf.record_round_start(p)  # next round
        self.assertEqual(sf.glitch_slots(p, 2, "corruption"), 1)
        self.assertEqual(p.glitched_shield_slots, 2)
        eng = self._eng()  # default uncapped
        p = eng.state.players[0]
        p.defense_capacity = 4
        self.assertEqual(sf.glitch_slots(p, 3, "green_cube"), 3)


if __name__ == "__main__":
    unittest.main()
