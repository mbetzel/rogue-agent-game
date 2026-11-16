"""v0.44.0 Research Tracks, Capstone Parity & Reroll Modernization tests.

Covers all invariants and edge cases in docs/specs/v440_research_tracks_spec.md:
- INV-RT-DEF-L4-01 / INV-DEF-L4-02
- INV-RT-TRIAGE-L2-BW-01 / INV-RT-TRIAGE-L3-BT-01 / INV-RT-TRIAGE-L4-FREE-01 / INV-RT-TRIAGE-L4-NOOP-01
- INV-RT-REL-BASE-01 / INV-REL-L4-TARGET-01 / INV-REL-L4-FACES-01 / INV-REL-ORDER-01
- INV-RT-PR-L3-SCANNED-01 / INV-RT-PR-L4-INSTANT-01
"""

from __future__ import annotations

import random
import unittest
from typing import Optional

from sim.bots import Phase3ActionPlan
from sim.config import CubeColor, DieColor, GameConfig, ShieldColor
from sim.engine import (
    GameEngine,
    phase1_roll_deploy,
    phase4_attack_resolution,
    phase5_pipeline_shift,
    phase6_operations,
    research_tracks as rt,
)
from sim.engine.state import CompileResult
from sim.entities import (
    COMPANIES,
    WHITE_HATS,
    CompanyCode,
    Face,
    WhiteHatCode,
    create_colored_die,
    create_gray_die,
)
from tests.test_v340_six_phase_sequence import ZERO, SixPhaseHarness, StubBot, noop_deck


class PlanBot440(StubBot):
    """Stub bot with explicit Operations plan and deterministic overrides."""

    research_aware = False

    def __init__(
        self,
        bot_id: int,
        plan: Optional[Phase3ActionPlan] = None,
        *,
        aegis_choice: Optional[CubeColor] = None,
        use_helix: bool = False,
        helix_override=None,
        prodigy_override=None,
        release_l4_override=None,
    ) -> None:
        super().__init__(bot_id, plan)
        self.aegis_choice = aegis_choice
        self.use_helix = use_helix
        self.helix_override = helix_override
        self.prodigy_override = prodigy_override
        self.release_l4_override = release_l4_override
        self.override_log = []

    def choose_aegis_override(self, player_state, qualifying_colors, game_state):
        if self.aegis_choice in qualifying_colors:
            return self.aegis_choice
        return super().choose_aegis_override(player_state, qualifying_colors, game_state)

    def choose_aegis_override_market_share(self, player_state, qualifying_colors, game_state, remaining, attack):
        if self.aegis_choice in qualifying_colors:
            return self.aegis_choice
        return None

    def choose_helix_override(self, *args, **kwargs):
        return self.use_helix

    def choose_helix_face_override_v038(self, player_state, active_dice, game_state):
        self.override_log.append("HELIX")
        return self.helix_override

    def choose_helix_face_override(self, *args, **kwargs):
        self.override_log.append("HELIX")
        return self.helix_override

    def choose_prodigy_purple_star_override(self, player_state, active_dice, rng):
        self.override_log.append("PRODIGY")
        return self.prodigy_override

    def choose_release_l4_gray_face(self, player_state, active_dice, game_state):
        self.override_log.append("RELEASE_L4")
        if self.release_l4_override is not None:
            return self.release_l4_override
        return super().choose_release_l4_gray_face(player_state, active_dice, game_state)


class V440Harness(SixPhaseHarness):
    def make(self, n: int = 2, bots=None, **kw) -> GameEngine:
        bots = bots or [PlanBot440(i) for i in range(n)]
        cfg_kw = GameConfig.v044(num_players=n, **kw)
        e = GameEngine(config=cfg_kw, bots=bots, seed=42)
        noop_deck(e)
        return e

    def ops(self, e: GameEngine, player, plan: Phase3ActionPlan) -> None:
        phase6_operations.execute_player_operations_turn(e, player, plan)


class TestV440DefenseGrid(V440Harness):
    def _shield_dice(self, player, count: int):
        shield = Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)
        dice = []
        for i in range(count):
            d = create_gray_die(700 + i)
            d.current_face = shield
            dice.append(d)
        player.in_production_dice = list(dice)
        return dice, {i: ShieldColor.ANY for i in range(count)}

    def test_defense_l4_natural_four_cap(self):
        e = self.make(2)
        p = e.state.players[0]
        p.defense_level = 4
        p.defense_capacity = 4
        p.money = 0
        dice, commitments = self._shield_dice(p, 4)
        attack = {CubeColor.RED: 2, CubeColor.BLUE: 1, CubeColor.GREEN: 1, CubeColor.BLACK: 0}
        cr = CompileResult({}, {}, dict(attack), {})
        phase4_attack_resolution.resolve_player_attack(e, p, dice, commitments, dict(attack), cr)
        self.assertEqual(p.money, 4)
        self.assertEqual(p.l4_payouts["defense_cash"], 4)

    def test_defense_l4_baffle_echo_ignored(self):
        bots = [PlanBot440(0, aegis_choice=CubeColor.RED), PlanBot440(1)]
        e = self.make(2, bots=bots)
        p = e.state.players[0]
        p.company = COMPANIES[CompanyCode.AEGIS]
        p.defense_level = 4
        p.defense_capacity = 4
        p.money = 0
        # 1 Red cube ignored via Baffle Echo, only 2 Blue cubes blocked by shields -> $2 cash
        dice, commitments = self._shield_dice(p, 4)
        attack = {CubeColor.RED: 1, CubeColor.BLUE: 2, CubeColor.GREEN: 0, CubeColor.BLACK: 0}
        cr = CompileResult({}, {}, dict(attack), {})
        phase4_attack_resolution.resolve_player_attack(e, p, dice, commitments, dict(attack), cr)
        self.assertEqual(p.money, 2)
        self.assertEqual(p.l4_payouts["defense_cash"], 2)

    def test_defense_l4_glitched_slot_restriction(self):
        e = self.make(2)
        p = e.state.players[0]
        p.defense_level = 4
        p.defense_capacity = 4
        p.glitched_shield_slots = 1  # effective capacity = 3
        p.money = 0
        dice, commitments = self._shield_dice(p, 3)
        attack = {CubeColor.RED: 0, CubeColor.BLUE: 4, CubeColor.GREEN: 0, CubeColor.BLACK: 0}
        cr = CompileResult({}, {}, dict(attack), {})
        phase4_attack_resolution.resolve_player_attack(e, p, dice, commitments, dict(attack), cr)
        self.assertEqual(p.money, 3)
        self.assertEqual(p.l4_payouts["defense_cash"], 3)


class TestV440TriageTrack(V440Harness):
    def test_triage_l1_breakthrough_gray_die(self):
        e = self.make(2)
        p = e.state.players[0]
        before_ready = len(p.ready_for_release_dice)
        p.research_tokens = 1
        rec = rt.upgrade_and_resolve(e, p, "TRIAGE")
        self.assertIsNotNone(rec)
        self.assertEqual(rec.outcome, "TAKEN")
        self.assertEqual(p.triage_level, 1)
        self.assertEqual(len(p.ready_for_release_dice), before_ready + 1)
        self.assertEqual(p.ready_for_release_dice[-1].color, DieColor.GRAY)

    def test_triage_l2_bandwidth_two_no_milestone(self):
        e = self.make(2)
        p = e.state.players[0]
        p.research_tokens = 10
        secrets_before = p.secrets
        rt.upgrade_and_resolve(e, p, "TRIAGE")
        rec2 = rt.upgrade_and_resolve(e, p, "TRIAGE")
        self.assertIsNone(rec2)
        self.assertEqual(p.triage_level, 2)
        self.assertEqual(p.triage_bandwidth, 2)
        self.assertEqual(p.secrets, secrets_before)

    def test_triage_l3_breakthrough_secret(self):
        e = self.make(2)
        p = e.state.players[0]
        p.research_tokens = 10
        p.money = 1
        rt.upgrade_and_resolve(e, p, "TRIAGE")
        rt.upgrade_and_resolve(e, p, "TRIAGE")
        secrets_before = p.secrets
        gray_before = sum(1 for d in p.total_dice if d.color == DieColor.GRAY)
        rec3 = rt.upgrade_and_resolve(e, p, "TRIAGE")
        self.assertIsNotNone(rec3)
        self.assertEqual(rec3.outcome, "TAKEN")
        self.assertEqual(p.triage_level, 3)
        self.assertEqual(p.secrets, secrets_before + 1)
        self.assertEqual(p.money, 1)  # no cash cost
        self.assertEqual(sum(1 for d in p.total_dice if d.color == DieColor.GRAY), gray_before)

    def test_triage_l4_free_replacement_ready_die(self):
        e = self.make(2)
        p = e.state.players[0]
        p.triage_level = 3
        p.research_tokens = 3
        p.money = 0
        gray_before = sum(1 for d in p.ready_for_release_dice if d.color == DieColor.GRAY)
        stock_before = e.state.market[DieColor.YELLOW]
        target_gray = next(d for d in p.ready_for_release_dice if d.color == DieColor.GRAY)
        choice = rt.BreakthroughChoice(accept=True, gray_die_id=target_gray.die_id, color=DieColor.YELLOW)
        rec = rt.upgrade_and_resolve(e, p, "TRIAGE", chooser=choice)
        self.assertIsNotNone(rec)
        self.assertEqual(rec.outcome, "TAKEN")
        self.assertEqual(p.triage_level, 4)
        self.assertEqual(p.money, 0)
        self.assertEqual(e.state.market[DieColor.YELLOW], stock_before - 1)
        self.assertEqual(sum(1 for d in p.ready_for_release_dice if d.color == DieColor.GRAY), gray_before - 1)
        self.assertTrue(any(d.color == DieColor.YELLOW for d in p.ready_for_release_dice))
        self.assertEqual(p.triage_l4_upgrade_color, DieColor.YELLOW.value)

    def test_triage_l4_free_replacement_scanned_die(self):
        e = self.make(2)
        p = e.state.players[0]
        p.triage_level = 3
        p.research_tokens = 3
        p.ready_for_release_dice = [d for d in p.ready_for_release_dice if d.color != DieColor.GRAY]
        scanned_gray = create_gray_die(901)
        p.scanned_dice.append(scanned_gray)
        rec = rt.upgrade_and_resolve(
            e, p, "TRIAGE", chooser=rt.BreakthroughChoice(accept=True, gray_die_id=901, color=DieColor.GREEN)
        )
        self.assertEqual(rec.outcome, "TAKEN")
        self.assertNotIn(scanned_gray, p.scanned_dice)
        self.assertTrue(any(d.color == DieColor.GREEN for d in p.ready_for_release_dice))

    def test_triage_l4_free_replacement_processing_die(self):
        e = self.make(2)
        p = e.state.players[0]
        p.triage_level = 3
        p.research_tokens = 3
        p.ready_for_release_dice = [d for d in p.ready_for_release_dice if d.color != DieColor.GRAY]
        proc_gray = create_gray_die(902)
        p.glitched_dice.append(proc_gray)
        rec = rt.upgrade_and_resolve(
            e, p, "TRIAGE", chooser=rt.BreakthroughChoice(accept=True, gray_die_id=902, color=DieColor.RED)
        )
        self.assertEqual(rec.outcome, "TAKEN")
        self.assertNotIn(proc_gray, p.glitched_dice)
        self.assertTrue(any(d.color == DieColor.RED for d in p.ready_for_release_dice))

    def test_triage_l4_forfeit_no_gray(self):
        e = self.make(2)
        p = e.state.players[0]
        p.triage_level = 3
        p.research_tokens = 3
        p.ready_for_release_dice = [d for d in p.ready_for_release_dice if d.color != DieColor.GRAY]
        p.scanned_dice.clear()
        p.glitched_dice.clear()
        rec = rt.upgrade_and_resolve(e, p, "TRIAGE")
        self.assertEqual(rec.outcome, "FORFEITED")
        self.assertEqual(rec.detail["reason"], "no_gray_die")

    def test_triage_l4_forfeit_empty_market(self):
        e = self.make(2)
        p = e.state.players[0]
        p.triage_level = 3
        p.research_tokens = 3
        for c in rt.MARKET_COLORS:
            e.state.market[c] = 0
        rec = rt.upgrade_and_resolve(e, p, "TRIAGE")
        self.assertEqual(rec.outcome, "FORFEITED")
        self.assertEqual(rec.detail["reason"], "market_empty")

    def test_phase6_triage_bandwidth_two_no_dead_research(self):
        e = self.make(2)
        p = e.state.players[0]
        p.triage_level = 4
        p.triage_bandwidth = 2
        p.research_tokens = 0
        p.glitched_dice = [create_gray_die(910), create_gray_die(911), create_gray_die(912)]
        rec = phase5_pipeline_shift.execute_player_pipeline_shift(e, p)
        self.assertEqual(len(rec.triaged_ids), 2)
        self.assertEqual(p.research_tokens, 0)
        self.assertEqual(p.l4_payouts["triage_research"], 0)


class TestV440ReleaseTrack(V440Harness):
    def test_release_base_two_rerolls(self):
        e = self.make(2)
        p = e.state.players[0]
        p.release_level = 4
        self.assertEqual(rt.free_rerolls_for(e.config, p, e.config.default_free_rerolls), 2)

    def test_release_l4_set_gray_face_shield(self):
        e = self.make(2)
        p = e.state.players[0]
        p.release_level = 4
        g = create_gray_die(801)
        g.current_face = Face(name="+$1 / +1 🔬", is_choice=True, choices=(Face("+$1", money=1), Face("+1 🔬", patches=1)))
        shield = Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)
        ok = phase1_roll_deploy.resolve_release_l4_gray_face_override(p, [g], e.state, target_idx=0, target_face=shield)
        self.assertTrue(ok)
        self.assertEqual(g.current_face, shield)
        self.assertEqual(p.l4_payouts["release_gray_face_sets"], 1)

    def test_release_l4_set_gray_face_income(self):
        e = self.make(2)
        p = e.state.players[0]
        p.release_level = 4
        g = create_gray_die(802)
        g.current_face = Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)
        dual = Face(name="+$1 & +1 🔬", money=1, patches=1)
        ok = phase1_roll_deploy.resolve_release_l4_gray_face_override(p, [g], e.state, target_idx=0, target_face=dual)
        self.assertTrue(ok)
        self.assertEqual(g.current_face, dual)

    def test_release_l4_rejects_non_gray_and_star_or_secret(self):
        e = self.make(2)
        p = e.state.players[0]
        p.release_level = 4
        purple = create_colored_die(DieColor.PURPLE, 803, face_profile=e.config.die_face_profile)
        g = create_gray_die(804)
        shield = Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)
        secret_face = Face(name="Secret", secrets_pending=1)
        star_face = Face(name="Star", is_star=True, star_code="PURPLE_STAR")
        self.assertFalse(phase1_roll_deploy.resolve_release_l4_gray_face_override(p, [purple], e.state, 0, shield))
        self.assertFalse(phase1_roll_deploy.resolve_release_l4_gray_face_override(p, [g], e.state, 0, secret_face))
        self.assertFalse(phase1_roll_deploy.resolve_release_l4_gray_face_override(p, [g], e.state, 0, star_face))

    def test_release_l4_noop_zero_gray_rolled(self):
        e = self.make(2)
        p = e.state.players[0]
        p.release_level = 4
        purple = create_colored_die(DieColor.PURPLE, 805, face_profile=e.config.die_face_profile)
        ok = phase1_roll_deploy.resolve_release_l4_gray_face_override(p, [purple], e.state)
        self.assertFalse(ok)
        self.assertEqual(p.l4_payouts["release_gray_face_sets"], 0)

    def test_post_reroll_override_sequence(self):
        # 3-tier order: Tier 1 Prodigy -> Tier 2 Helix -> Tier 3 Release L4
        g = create_gray_die(810)
        purple = create_colored_die(DieColor.PURPLE, 811, face_profile="V038F")
        purple_star = next(f for f in purple.faces if f.is_star)
        gray_income = Face(name="+$1 & +1 🔬", money=1, patches=1)
        gray_shield = Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)

        bot = PlanBot440(
            0,
            use_helix=True,
            prodigy_override=(0, gray_income),
            helix_override=(0, gray_income),
            release_l4_override=(0, gray_shield),
        )
        e = self.make(2, bots=[bot, PlanBot440(1)])
        p = e.state.players[0]
        p.company = COMPANIES[CompanyCode.HELIX]
        p.white_hat = WHITE_HATS[WhiteHatCode.PRODIGY]
        p.release_level = 4
        p.release_bandwidth = 6
        p.ready_for_release_dice = [g, purple]

        # Pre-set faces and disable actual RNG face change by forcing no rerolls (StubBot returns [])
        g.roll = lambda rng: Face(name="+1 🔬", patches=1)
        purple.roll = lambda rng: purple_star
        phase1_roll_deploy.execute_phase_1(e)
        # Prodigy fires once pre-reroll and once post-reroll, then Helix, then Release L4
        post_idx = bot.override_log.index("HELIX")
        self.assertEqual(bot.override_log[post_idx - 1 : post_idx + 2], ["PRODIGY", "HELIX", "RELEASE_L4"])
        self.assertEqual(g.current_face, gray_shield)


class TestV440PublicRelations(V440Harness):
    def test_pr_l3_purple_die_to_scanned_box(self):
        e = self.make(2)
        p = e.state.players[0]
        p.patent_level = 2
        p.research_tokens = 2
        ready_before = len(p.ready_for_release_dice)
        scanned_before = len(p.scanned_dice)
        rec = rt.upgrade_and_resolve(e, p, "PATENT")
        self.assertEqual(rec.outcome, "TAKEN")
        self.assertEqual(p.patent_level, 3)
        self.assertEqual(len(p.ready_for_release_dice), ready_before)
        self.assertEqual(len(p.scanned_dice), scanned_before + 1)
        self.assertEqual(p.scanned_dice[-1].color, DieColor.PURPLE)

    def test_pr_l4_instant_market_share_unclamped(self):
        e = self.make(2)
        p = e.state.players[0]
        p.patent_level = 3
        p.research_tokens = 3
        p.market_share = 15
        rec = rt.upgrade_and_resolve(e, p, "PATENT")
        self.assertEqual(rec.outcome, "TAKEN")
        self.assertEqual(p.patent_level, 4)
        self.assertEqual(p.market_share, 17)
        self.assertEqual(p.l4_payouts["pr_instant_market_share"], 2)

    def test_pr_l4_instant_market_share_clamped(self):
        e = self.make(2)
        p = e.state.players[0]
        p.patent_level = 3
        p.research_tokens = 3
        p.market_share = 19
        rec = rt.upgrade_and_resolve(e, p, "PATENT")
        self.assertEqual(rec.outcome, "TAKEN")
        self.assertEqual(p.market_share, 20)
        self.assertEqual(p.l4_payouts["pr_instant_market_share"], 1)

    def test_pr_l4_regain_cap_three(self):
        e = self.make(2)
        p = e.state.players[0]
        p.patent_level = 4
        cost, cap = rt.regain_rate(e.config, p)
        self.assertEqual(cost, 3)
        self.assertEqual(cap, 3)


class TestV440PresetsAndSmoke(unittest.TestCase):
    def test_v044_preset_and_roster(self):
        cfg = GameConfig.v044()
        self.assertEqual(cfg.defense_l4_cash_cap, 4)
        self.assertTrue(cfg.triage_l4_free_die_replacement)
        self.assertEqual(cfg.triage_l3_breakthrough, "SECRET")
        self.assertEqual(cfg.triage_l2_milestone_secrets, 0)
        self.assertEqual(cfg.release_l4_extra_rerolls, 0)
        self.assertTrue(cfg.release_l4_set_gray_face)
        self.assertTrue(cfg.pr_l3_purple_to_scanned)
        self.assertEqual(cfg.pr_l4_instant_market_share, 2)
        self.assertEqual(cfg.track_capacity_by_level["TRIAGE"], (1, 1, 2, 2, 2))

        rcfg = GameConfig.v044_roster()
        self.assertTrue(rcfg.bot_pr_push)
        self.assertEqual(rcfg.defense_l4_cash_cap, 4)


if __name__ == "__main__":
    unittest.main()
