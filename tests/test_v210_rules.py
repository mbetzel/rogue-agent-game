"""Unit and Integration Tests for Phase 28: 9-Round Pacing & Asymmetric Variant Recalibration (v0.21.0 Baseline)."""

import unittest

from sim.bots.base import BaseBot
from sim.config import CubeColor, DieColor, GameConfig, ShieldColor
from sim.engine.core import GameEngine
from sim.entities import (
    ArchetypeCode,
    get_archetype_by_code,
    get_all_version_cards,
    get_default_version_deck,
)


class TestV210Rules(unittest.TestCase):
    """Test suite verifying v0.21.0 rules and mechanics."""

    def test_starting_secrets_by_player_count(self) -> None:
        """Legacy v0.33 sequence: 4P starts with 12 Secrets; 2P and 3P start with 8 Secrets."""
        cfg = GameConfig.legacy_v033()
        self.assertEqual(cfg.starting_secrets_by_player_count[2], 8)
        self.assertEqual(cfg.starting_secrets_by_player_count[3], 8)
        self.assertEqual(cfg.starting_secrets_by_player_count[4], 12)

        eng4 = GameEngine(config=GameConfig.legacy_v033(num_players=4), bots=[BaseBot(i) for i in range(4)], seed=42)
        for p in eng4.state.players:
            self.assertEqual(p.secrets, 12)

        eng2 = GameEngine(config=GameConfig(num_players=2), bots=[BaseBot(i) for i in range(2)], seed=42)
        for p in eng2.state.players:
            self.assertEqual(p.secrets, 8)

    def test_autonomous_pulse_1_black_across_all_versions(self) -> None:
        """Autonomous AI Pulse adds exactly 1 Black cube in v1.0, v2.0, and v3.0."""
        cfg = GameConfig()
        self.assertEqual(cfg.autonomous_pulse_by_version["v1.0"], 1)
        self.assertEqual(cfg.autonomous_pulse_by_version["v2.0"], 1)
        self.assertEqual(cfg.autonomous_pulse_by_version["v3.0"], 1)

        eng = GameEngine(config=GameConfig(num_players=4), bots=[BaseBot(i) for i in range(4)], seed=42)
        # v1.0 Pulse
        for c in eng.state.staging_cup:
            eng.state.staging_cup[c] = 0
        eng._execute_phase_1()
        self.assertEqual(eng.state.staging_cup[CubeColor.BLACK], 1)

        # v2.0 Pulse
        eng.state.current_version_index = 1
        for c in eng.state.staging_cup:
            eng.state.staging_cup[c] = 0
        eng._execute_phase_1()
        self.assertEqual(eng.state.staging_cup[CubeColor.BLACK], 1)

        # v3.0 Pulse
        eng.state.current_version_index = 2
        for c in eng.state.staging_cup:
            eng.state.staging_cup[c] = 0
        eng._execute_phase_1()
        self.assertEqual(eng.state.staging_cup[CubeColor.BLACK], 1)

    def test_red_ransomware_cash_only_no_patch_absorption(self) -> None:
        """Unblocked Red ransom is strictly cash-only; held patches NEVER absorb unpaid ransom."""
        cfg = GameConfig(num_players=2)
        eng = GameEngine(config=cfg, bots=[BaseBot(0), BaseBot(1)], seed=42)
        p0 = eng.state.players[0]
        p0.money = 0
        p0.patches = 3
        p0.secrets = 8

        # 2 unblocked Red attacks with $0 cash and 3 patches
        eng._resolve_player_defense_and_wear(
            player=p0,
            rolled_dice=[],
            commitments={},
            attack_strengths={CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        self.assertEqual(p0.money, 0)
        self.assertEqual(p0.patches, 3, "Patches must NOT absorb unpaid Red ransom")
        self.assertEqual(p0.secrets, 7, "Unpaid ransom must leak flat 1 Secret under v0.31.0")

    def test_red_ransomware_partial_cash_leak(self) -> None:
        """Cash pays partial ransom; remaining balance leaks to Secrets while patches remain intact."""
        cfg = GameConfig(num_players=2)
        eng = GameEngine(config=cfg, bots=[BaseBot(0), BaseBot(1)], seed=42)
        p0 = eng.state.players[0]
        p0.money = 1
        p0.patches = 2
        p0.secrets = 8

        # 3 unblocked Red attacks with $1 cash and 2 patches
        eng._resolve_player_defense_and_wear(
            player=p0,
            rolled_dice=[],
            commitments={},
            attack_strengths={CubeColor.RED: 3, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 3, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        self.assertEqual(p0.money, 0)
        self.assertEqual(p0.patches, 2, "Patches must remain untouched")
        self.assertEqual(p0.secrets, 7, "1 cash paid, unpaid shortfall leaks flat 1 Secret (8 - 1 = 7)")

    def test_spook_slush_fund_absorbs_unpaid_ransom_without_patches(self) -> None:
        """Spook Slush Fund absorbs up to 2 Secrets from unpaid Red ransom without using patches."""
        cfg = GameConfig.legacy_v034(num_players=2)
        eng = GameEngine(config=cfg, bots=[BaseBot(0), BaseBot(1)], seed=42)
        p0 = eng.state.players[0]
        p0.money = 0
        p0.patches = 2
        p0.secrets = 8
        p0.archetype = get_archetype_by_code(ArchetypeCode.SPOOK)

        # 2 unblocked Red attacks
        eng._resolve_player_defense_and_wear(
            player=p0,
            rolled_dice=[],
            commitments={},
            attack_strengths={CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        self.assertEqual(p0.money, 0)
        self.assertEqual(p0.patches, 2)
        self.assertEqual(p0.secrets, 8, "Spook Slush Fund absorbed 2 unpaid ransom without patch usage")

    def test_v10_setup_staging_payloads(self) -> None:
        """v1.0 cards stage exactly 3 attack cubes (0 Black) at match start."""
        cards = {c.directive_code: c for c in get_all_version_cards("STANDARD")}
        sk = cards["SCRIPT_KIDDIE"]
        self.assertEqual(sk.staging_payload, {CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 1})
        self.assertEqual(sum(sk.staging_payload.values()), 3)

        ds = cards["DATA_SCRAPER"]
        self.assertEqual(ds.staging_payload, {CubeColor.RED: 1, CubeColor.BLUE: 2})
        self.assertEqual(sum(ds.staging_payload.values()), 3)
        self.assertEqual(ds.starting_cash_bonus, 1)

    def test_corruption_track_black_cube_injections(self) -> None:
        """Corruption track spaces inject Black cubes into Staging Cup (Mode A)."""
        cfg = GameConfig(num_players=2)
        eng = GameEngine(config=cfg, bots=[BaseBot(0), BaseBot(1)], seed=42)
        # Advance to space 1
        eng.state.corruption_track = 1
        # Clear staging cup
        for c in eng.state.staging_cup:
            eng.state.staging_cup[c] = 0

        # Simulate 1 Black cube exiting to fill Space 2 (Script Kiddie space 2: Lose $2 + Add 1K)
        eng.state.tower.drop = lambda cup, rng: {CubeColor.BLACK: 1, CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0}
        commitments = [(p, list(p.ready_dice), {}) for p in eng.state.players]
        eng._execute_phase_2(commitments)

        self.assertEqual(eng.state.corruption_track, 2)
        self.assertEqual(eng.state.staging_cup[CubeColor.BLACK], 1, "Space 2 must inject 1 Black cube into Staging Cup")

    def test_legacy_patch_ransom_absorption_flag(self) -> None:
        """When patch_ransom_absorption is explicitly enabled, legacy Tier 2 behavior is preserved."""
        cfg = GameConfig(num_players=2, patch_ransom_absorption=True)
        eng = GameEngine(config=cfg, bots=[BaseBot(0), BaseBot(1)], seed=42)
        p0 = eng.state.players[0]
        p0.money = 0
        p0.patches = 2
        p0.secrets = 8

        eng._resolve_player_defense_and_wear(
            player=p0,
            rolled_dice=[],
            commitments={},
            attack_strengths={CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            active_directive="NONE",
        )

        self.assertEqual(p0.money, 0)
        self.assertEqual(p0.patches, 0, "Patches should absorb under legacy mode")
        self.assertEqual(p0.secrets, 8, "Secrets untouched under legacy mode")


if __name__ == "__main__":
    unittest.main()
