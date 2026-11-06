"""Unit test suite for Phase 36: Rules Streamlining, Decoupled Tracks & Wireframes (v0.29.0).

Verifies invariants defined in docs/specs/v290_rules_streamlining_spec.md:
- TEST-V290-01: test_version_switch_start_of_round (INV-VER-SWITCH-01)
- TEST-V290-02: test_black_cube_immediate_spillover (INV-VER-SWITCH-01)
- TEST-V290-03: test_v3_singularity_remains_immediate (INV-VER-SWITCH-01)
- TEST-V290-04: test_hash_matches_completely_removed (INV-HASH-EXCISE-01)
- TEST-V290-05: test_cipher_face6_algorithmic_parity (INV-CIPHER-FACE6-01)
- TEST-V290-06: test_corruption_space_free_choice_glitch (INV-CORRUPT-CHOICE-01)
- TEST-V290-07: test_replaced_phase_lock_spaces (INV-LOCK-EXCISE-01)
- TEST-V290-08: test_decoupled_triage_track (INV-TRIAGE-TRACK-01)
- TEST-V290-09: test_decoupled_release_track (INV-RELEASE-TRACK-01)
- TEST-V290-10: test_fast_patching_completely_excised (INV-FASTPATCH-EXCISE-01)
- TEST-V290-11: test_corporate_starting_configs_4_tracks (INV-CORP-CONFIG-01)
- TEST-V290-12: test_web_api_four_track_upgrades (INV-UPGRADE-TRACK-01)
"""

from __future__ import annotations

import random
import unittest
from typing import Dict, List, Optional

from sim.bots.base import BaseBot, Phase3ActionPlan
from sim.config import CubeColor, DieColor, GameConfig, ShieldColor
from sim.engine.core import GameEngine
from sim.engine.phase1_boot import (
    check_and_execute_start_of_round_version_transition,
    execute_phase_1,
)
from sim.engine.phase2_threat import execute_phase_2, resolve_corruption_space
from sim.engine.phase3_ops import execute_phase_3, collect_production_income
from sim.engine.state import GameState, PlayerState, ProductionRole
from sim.entities import (
    COMPANIES,
    CompanyCode,
    CorruptionSpace,
    Die,
    Face,
    WHITE_HATS,
    WhiteHatCode,
    create_colored_die,
    create_gray_die,
    get_all_version_cards,
)
from web.game_controller import GameController


class TestV290RulesStreamlining(unittest.TestCase):
    """Test suite verifying v0.29.0 rules streamlining invariants."""

    def setUp(self) -> None:
        self.rng = random.Random(42)

    def test_version_switch_start_of_round(self) -> None:
        """TEST-V290-01 (INV-VER-SWITCH-01): Filling v1.0 Space 4 marks pending advance,

        leaves active version at v1.0 for Phase 2B/3, keeps v1 override usable in Phase 3,
        and transitions at start of next round.
        """
        cfg = GameConfig(num_players=2)
        engine = GameEngine(cfg, seed=42)

        # Ensure v1.0 is active with 3 corruption cubes
        self.assertEqual(engine.state.active_version.version_str, "v1.0")
        engine.state.corruption_track = 3
        engine.state.pending_version_advance = False

        # Drop 1 Black cube in Phase 2
        engine.state.tower.drop = lambda cup, rng: {CubeColor.BLACK: 1, CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0}
        execute_phase_2(engine, [(p, [], {}) for p in engine.state.players])

        # Track should hit capacity (4), pending advance flagged, but active version remains v1.0
        self.assertEqual(engine.state.corruption_track, 4)
        self.assertTrue(engine.state.pending_version_advance)
        self.assertEqual(engine.state.active_version.version_str, "v1.0")

        # Player's v1.0 override remains valid and usable in Phase 3
        p0 = engine.state.players[0]
        self.assertTrue(p0.is_ability_available("v1.0"))

        # Transition into next round (Start of Round Phase 1)
        advanced = check_and_execute_start_of_round_version_transition(engine)
        self.assertTrue(advanced)
        self.assertEqual(engine.state.active_version.version_str, "v2.0")
        self.assertEqual(engine.state.current_version_index, 1)
        self.assertFalse(engine.state.pending_version_advance)
        self.assertEqual(engine.state.corruption_track, 0)

    def test_black_cube_immediate_spillover(self) -> None:
        """TEST-V290-02 (INV-VER-SWITCH-01): Drop 3 Black cubes when v1.0 is at 3/4.

        Space 4 triggers, and 2 excess cubes trigger v2.0 Spaces 1 and 2 immediately.
        """
        cfg = GameConfig(num_players=2)
        engine = GameEngine(cfg, seed=42)

        engine.state.corruption_track = 3
        engine.state.pending_version_advance = False

        # v2.0 Space 1 in Standard track loses $2
        p0 = engine.state.players[0]
        p0.money = 10

        # Drop 3 Black cubes: 1 finishes v1.0, 2 spill over to v2.0
        engine.state.tower.drop = lambda cup, rng: {CubeColor.BLACK: 3, CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0}
        execute_phase_2(engine, [(p, [], {}) for p in engine.state.players])

        self.assertTrue(engine.state.pending_version_advance)
        self.assertEqual(engine.state.overflow_black_cubes_on_next_track, 2)
        # Active version remains v1.0 during Phase 2
        self.assertEqual(engine.state.active_version.version_str, "v1.0")

        # Transition at start of round
        advanced = check_and_execute_start_of_round_version_transition(engine)
        self.assertTrue(advanced)
        self.assertEqual(engine.state.active_version.version_str, "v2.0")
        self.assertEqual(engine.state.corruption_track, 2)
        self.assertFalse(engine.state.pending_version_advance)
        self.assertEqual(engine.state.overflow_black_cubes_on_next_track, 0)

    def test_v3_singularity_remains_immediate(self) -> None:
        """TEST-V290-03 (INV-VER-SWITCH-01): Covering v3.0 Space 6 triggers Singularity

        immediately in Step 2A without waiting for next round.
        """
        cfg = GameConfig(num_players=2)
        engine = GameEngine(cfg, seed=42)

        # Advance to v3.0
        engine.state.current_version_index = 2
        self.assertEqual(engine.state.active_version.version_str, "v3.0")

        engine.state.corruption_track = 5  # Capacity is 6
        engine.state.singularity_triggered = False

        # Drop 1 Black cube
        engine.state.tower.drop = lambda cup, rng: {CubeColor.BLACK: 1, CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0}
        execute_phase_2(engine, [(p, [], {}) for p in engine.state.players])

        self.assertEqual(engine.state.corruption_track, 6)
        self.assertTrue(engine.state.singularity_triggered)
        self.assertFalse(engine.state.is_final_round)
        self.assertTrue(engine.state.game_over)

    def test_hash_matches_completely_removed(self) -> None:
        """TEST-V290-04 (INV-HASH-EXCISE-01): Roll 3 identical faces; verify zero corporate

        secrets awarded from cryptographic hash matches.
        """
        cfg = GameConfig(num_players=2)
        engine = GameEngine(cfg, seed=42)
        p0 = engine.state.players[0]

        # Give p0 three identical Gray dice rolling +$1
        face_income = Face("+$1", money=1)
        p0.ready_for_release_dice = [
            Die(1, DieColor.GRAY, cost=0, faces=[face_income] * 6),
            Die(2, DieColor.GRAY, cost=0, faces=[face_income] * 6),
            Die(3, DieColor.GRAY, cost=0, faces=[face_income] * 6),
        ]
        initial_secrets = p0.secrets

        execute_phase_1(engine)

        # Secrets must NOT have changed from hash match
        self.assertEqual(p0.secrets, initial_secrets)
        self.assertEqual(p0.hash_matches_secrets, 0)

    def test_cipher_face6_algorithmic_parity(self) -> None:
        """TEST-V290-05 (INV-CIPHER-FACE6-01): Roll Cipher Purple Face 6; verify Phase 3A

        income yields +$2 cash and +1 🔬 Research without hash matching.
        """
        cfg = GameConfig(num_players=2)
        engine = GameEngine(cfg, seed=42)
        p0 = engine.state.players[0]

        p0.white_hat = WHITE_HATS[WhiteHatCode.CIPHER]
        p0.money = 5
        p0.research_tokens = 2

        # Create Purple die showing Face 6 (PURPLE_STAR)
        purple_die = create_colored_die(color=DieColor.PURPLE, die_id=99)
        purple_die.current_face = purple_die.faces[5]  # PURPLE_STAR face
        self.assertTrue(purple_die.current_face.is_star)
        self.assertEqual(purple_die.current_face.star_code, "PURPLE_STAR")

        p0.in_production_dice = [purple_die]

        collect_production_income(engine, p0)

        self.assertEqual(p0.money, 7)  # 5 + 2
        self.assertEqual(p0.research_tokens, 3)  # 2 + 1

    def test_corruption_space_free_choice_glitch(self) -> None:
        """TEST-V290-06 (INV-CORRUPT-CHOICE-01): Trigger glitch space; verify player can

        choose redundant shield die instead of income die.
        """
        cfg = GameConfig(num_players=2)
        engine = GameEngine(cfg, seed=42)
        p0 = engine.state.players[0]

        shield_die = Die(101, DieColor.GRAY, cost=0, faces=[Face("Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)] * 6)
        income_die = Die(102, DieColor.YELLOW, cost=5, faces=[Face("+$3", money=3)] * 6)
        shield_die.production_role = ProductionRole.RED_SHIELD
        income_die.production_role = ProductionRole.INCOME

        p0.in_production_dice = [shield_die, income_die]

        # Define custom bot that chooses the shield die
        class SpecificGlitchBot(BaseBot):
            def choose_dice_to_glitch(self, player, in_production_dice, count, threat_strengths):
                # Pick the shield die explicitly
                return [d for d in in_production_dice if d.die_id == 101][:count]

        p0.bot = SpecificGlitchBot(0)

        # Trigger a corruption space requiring 1 demote
        space = CorruptionSpace(index=1, label="Demote 1", demote_dice=1)
        commitments = {0: ShieldColor.RED}
        resolve_corruption_space(
            engine=engine,
            space=space,
            player_commitments=[(p0, [shield_die, income_die], commitments)],
            exited_cubes={},
        )

        # Shield die must be glitched, income die intact in production
        self.assertIn(shield_die, p0.glitched_dice)
        self.assertIn(income_die, p0.in_production_dice)
        self.assertEqual(len(commitments), 0)  # Commitment was revoked

    def test_replaced_phase_lock_spaces(self) -> None:
        """TEST-V290-07 (INV-LOCK-EXCISE-01): Verify v2.0 RaaS Space 3, Worm Space 3, and

        v3.0 Zero-Day Space 4 execute kinetic/glitch effects with zero phase locks.
        """
        all_versions = {v.directive_code: v for v in get_all_version_cards("STANDARD")}

        # 1. v2.0 RaaS Space 3: Lose $2, Add 1 Red
        raas = all_versions["RAAS"]
        s3_raas = raas.corruption_track[2]
        self.assertEqual(s3_raas.lose_money, 2)
        self.assertEqual(s3_raas.add_cubes.get(CubeColor.RED), 1)

        # 2. v2.0 Worm Space 3: All glitch 1 die, Add 1 Green
        worm = all_versions["POLYMORPHIC_WORM"]
        s3_worm = worm.corruption_track[2]
        self.assertEqual(s3_worm.demote_dice, 1)
        self.assertEqual(s3_worm.add_cubes.get(CubeColor.GREEN), 1)

        # 3. v3.0 Zero-Day Space 4: All glitch 1 die, Add 1 Blue, 1 Black
        zd = all_versions["ZERO_DAY_OVERRIDE"]
        s4_zd = zd.corruption_track[3]
        self.assertEqual(s4_zd.demote_dice, 1)
        self.assertEqual(s4_zd.add_cubes.get(CubeColor.BLUE), 1)
        self.assertEqual(s4_zd.add_cubes.get(CubeColor.BLACK), 1)

    def test_decoupled_triage_track(self) -> None:
        """TEST-V290-08 (INV-TRIAGE-TRACK-01): Verify Triage Track Level 0 (2 dice),

        Level 1 (3 dice), Level 2 (4 dice + Emergency Hotfix).
        """
        player = PlayerState(player_id=0, bot=BaseBot(0), money=5, secrets=8, patches=10)
        self.assertEqual(player.triage_level, 0)
        self.assertEqual(player.triage_bandwidth, 2)
        self.assertFalse(player.has_emergency_hotfix)

        self.assertEqual(player.get_track_upgrade_cost("TRIAGE"), 2)
        player.research_tokens = 5

        # L0 -> L1
        self.assertTrue(player.upgrade_track("TRIAGE"))
        self.assertEqual(player.triage_level, 1)
        self.assertEqual(player.triage_bandwidth, 3)
        self.assertEqual(player.research_tokens, 3)

        # L1 -> L2
        self.assertEqual(player.get_track_upgrade_cost("TRIAGE"), 3)
        self.assertTrue(player.upgrade_track("TRIAGE"))
        self.assertEqual(player.triage_level, 2)
        self.assertEqual(player.triage_bandwidth, 4)
        self.assertTrue(player.has_emergency_hotfix)
        self.assertEqual(player.research_tokens, 0)

        # Capped at L2
        self.assertIsNone(player.get_track_upgrade_cost("TRIAGE"))
        self.assertFalse(player.upgrade_track("TRIAGE"))

    def test_decoupled_release_track(self) -> None:
        """TEST-V290-09 (INV-RELEASE-TRACK-01): Verify Release Track Level 0 (4 dice),

        Level 1 (5 dice), Level 2 (6 dice).
        """
        player = PlayerState(player_id=0, bot=BaseBot(0), money=5, secrets=8, patches=10)
        self.assertEqual(player.release_level, 0)
        self.assertEqual(player.release_bandwidth, 4)

        self.assertEqual(player.get_track_upgrade_cost("RELEASE"), 2)
        player.research_tokens = 5

        # L0 -> L1
        self.assertTrue(player.upgrade_track("RELEASE"))
        self.assertEqual(player.release_level, 1)
        self.assertEqual(player.release_bandwidth, 5)
        self.assertEqual(player.research_tokens, 3)

        # L1 -> L2
        self.assertEqual(player.get_track_upgrade_cost("RELEASE"), 3)
        self.assertTrue(player.upgrade_track("RELEASE"))
        self.assertEqual(player.release_level, 2)
        self.assertEqual(player.release_bandwidth, 6)
        self.assertEqual(player.research_tokens, 0)

        # Capped at L2
        self.assertIsNone(player.get_track_upgrade_cost("RELEASE"))
        self.assertFalse(player.upgrade_track("RELEASE"))

    def test_fast_patching_completely_excised(self) -> None:
        """TEST-V290-10 (INV-FASTPATCH-EXCISE-01): Verify excess glitched dice beyond triage

        bandwidth cannot be fast-patched with research tokens.
        """
        cfg = GameConfig(num_players=2)
        engine = GameEngine(cfg, seed=42)
        p0 = engine.state.players[0]

        # Give player 4 glitched dice and 10 research tokens, triage bandwidth = 2
        p0.triage_bandwidth = 2
        p0.research_tokens = 10
        p0.glitched_dice = [create_gray_die(i) for i in range(1, 5)]

        class IdleBot(BaseBot):
            def take_phase3_actions(self, p, g, rng):
                return Phase3ActionPlan()

        p0.bot = IdleBot(0)
        engine.state.players[1].bot = IdleBot(1)

        execute_phase_3(engine)

        # Only 2 dice moved from glitched to scanned via triage bandwidth
        self.assertEqual(len(p0.glitched_dice), 2)
        self.assertEqual(len(p0.scanned_dice), 2)
        # Research tokens should remain unspent on fast-patching
        self.assertEqual(p0.research_tokens, 10)

    def test_corporate_starting_configs_4_tracks(self) -> None:
        """TEST-V290-11 (INV-CORP-CONFIG-01): Verify starting track levels and bandwidths

        for all 6 companies.
        """
        # Meridian: 2/2/4/0/0/0/0, +$2 bonus
        mer = COMPANIES[CompanyCode.MERIDIAN]
        self.assertEqual(mer.starting_defense_capacity, 2)
        self.assertEqual(mer.starting_triage_bandwidth, 2)
        self.assertEqual(mer.starting_release_bandwidth, 4)
        self.assertEqual(mer.starting_cash_bonus, 2)

        # Omnidyne: 1/3/5/1/1/0/0
        omni = COMPANIES[CompanyCode.OMNIDYNE]
        self.assertEqual(omni.starting_defense_capacity, 1)
        self.assertEqual(omni.starting_triage_bandwidth, 3)
        self.assertEqual(omni.starting_release_bandwidth, 5)
        self.assertEqual(omni.starting_triage_level, 1)
        self.assertEqual(omni.starting_release_level, 1)

        # Aegis: 3/1/3/0/0/1/0
        aegis = COMPANIES[CompanyCode.AEGIS]
        self.assertEqual(aegis.starting_defense_capacity, 3)
        self.assertEqual(aegis.starting_triage_bandwidth, 1)
        self.assertEqual(aegis.starting_release_bandwidth, 3)
        self.assertEqual(aegis.starting_defense_level, 1)

        # DTO: 2/2/4/0/0/0/0, +1 Secret
        dto = COMPANIES[CompanyCode.DTO]
        self.assertEqual(dto.starting_defense_capacity, 2)
        self.assertEqual(dto.starting_triage_bandwidth, 2)
        self.assertEqual(dto.starting_release_bandwidth, 4)
        self.assertEqual(dto.starting_secrets_bonus, 1)

        # Helix: 2/2/4/0/0/0/1, +2 Research
        helix = COMPANIES[CompanyCode.HELIX]
        self.assertEqual(helix.starting_defense_capacity, 2)
        self.assertEqual(helix.starting_triage_bandwidth, 2)
        self.assertEqual(helix.starting_release_bandwidth, 4)
        self.assertEqual(helix.starting_patent_level, 1)
        self.assertEqual(helix.starting_research_bonus, 2)

        # Prometheus: 2/2/4/0/0/0/0, upgrade_discount 1
        prom = COMPANIES[CompanyCode.PROMETHEUS]
        self.assertEqual(prom.starting_defense_capacity, 2)
        self.assertEqual(prom.starting_triage_bandwidth, 2)
        self.assertEqual(prom.starting_release_bandwidth, 4)
        self.assertEqual(prom.upgrade_discount, 1)

    def test_web_api_four_track_upgrades(self) -> None:
        """TEST-V290-12 (INV-UPGRADE-TRACK-01): Verify GameController / web API handles

        'triage' and 'release' independently.
        """
        ctrl = GameController()
        ctrl.new_game(research_track_model="V034_THREE_LEVEL", num_players=2, seed=42)
        ctrl.phase = 6
        ctrl.subphase = "operations"
        ctrl.active_player_index = 0

        p0 = ctrl.state.players[0]
        p0.triage_level = 0
        p0.triage_bandwidth = 2
        p0.release_level = 0
        p0.release_bandwidth = 4
        p0.research_tokens = 6

        # Upgrade triage
        state_triage = ctrl.upgrade_track(player_id=0, track_type="triage")
        self.assertIsNotNone(state_triage)
        self.assertEqual(p0.triage_level, 1)
        self.assertEqual(p0.triage_bandwidth, 3)
        self.assertEqual(p0.release_level, 0)
        self.assertEqual(p0.release_bandwidth, 4)
        self.assertEqual(p0.research_tokens, 4)

        # Upgrade release
        state_release = ctrl.upgrade_track(player_id=0, track_type="release")
        self.assertIsNotNone(state_release)
        self.assertEqual(p0.triage_level, 1)
        self.assertEqual(p0.triage_bandwidth, 3)
        self.assertEqual(p0.release_level, 1)
        self.assertEqual(p0.release_bandwidth, 5)
        self.assertEqual(p0.research_tokens, 2)


if __name__ == "__main__":
    unittest.main()
