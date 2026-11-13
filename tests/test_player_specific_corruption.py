"""Unit and integration tests for Player-Specific Corruption Attacks (v0.41.0 / Phase 59).

Validates all 13 required test cases (TC-P2-TGT-01 through TC-P2-TGT-13) per
docs/specs/player_specific_corruption_spec.md §7.
"""

from __future__ import annotations

import itertools
import unittest
from collections import Counter
from typing import Dict, List

from sim.bots.adaptive_balanced import AdaptiveBalancedBot
from sim.config import CubeColor, DieColor, GameConfig, RoundSequence
from sim.engine.core import GameEngine
from sim.engine.phase2_compiler import (
    get_targeted_players,
    resolve_corruption_space,
    resolve_corruption_transfer,
)
from sim.entities import (
    V038D_V1_STAGING_PAYLOAD,
    CorruptionSpace,
    Die,
    TargetCriterion,
    TransferType,
    VersionCard,
    create_colored_die,
    create_gray_die,
    get_all_version_cards,
)


class TestPlayerSpecificCorruption(unittest.TestCase):
    """Test suite covering deterministic player-specific corruption hazards, transfers, and parity."""

    def setUp(self) -> None:
        self.std_cards: Dict[str, VersionCard] = {
            c.directive_code: c for c in get_all_version_cards(profile="STANDARD")
        }
        self.agg_cards: Dict[str, VersionCard] = {
            c.directive_code: c for c in get_all_version_cards(profile="AGGRESSIVE")
        }

    def test_tc_p2_tgt_01_direct_hazard_unique_leader(self) -> None:
        """TC-P2-TGT-01: Direct Hazard: Unique Leader.

        Setup: P0=$10, P1=$6, P2=$4. Space 2 Script Kiddie (-$2 cash on Most $).
        Assert P0 loses $2 ($8); P1 and P2 remain untouched. Table drain = $2.00.
        """
        cfg = GameConfig.v040(num_players=3)
        engine = GameEngine(cfg, seed=42)
        p0, p1, p2 = engine.state.players[0], engine.state.players[1], engine.state.players[2]
        p0.money = 10
        p1.money = 6
        p2.money = 4

        space = self.std_cards["SCRIPT_KIDDIE"].corruption_track[1]  # Space 2 (0-indexed 1)
        self.assertEqual(space.index, 2)
        self.assertEqual(space.target_criterion, TargetCriterion.MOST_MONEY)
        self.assertEqual(space.lose_money, 2)

        resolve_corruption_space(engine, space, [], {})

        self.assertEqual(p0.money, 8)
        self.assertEqual(p1.money, 6)
        self.assertEqual(p2.money, 4)

    def test_tc_p2_tgt_02_direct_hazard_inclusive_ties(self) -> None:
        """TC-P2-TGT-02: Direct Hazard: Inclusive Ties (INV-TARGET-02).

        Setup: P0=$8, P1=$8, P2=$4. Space 2 Script Kiddie.
        Assert BOTH P0 and P1 lose $2 ($6 each); P2 untouched. Table drain = $4.00.
        """
        cfg = GameConfig.v040(num_players=3)
        engine = GameEngine(cfg, seed=42)
        p0, p1, p2 = engine.state.players[0], engine.state.players[1], engine.state.players[2]
        p0.money = 8
        p1.money = 8
        p2.money = 4

        space = self.std_cards["SCRIPT_KIDDIE"].corruption_track[1]
        resolve_corruption_space(engine, space, [], {})

        self.assertEqual(p0.money, 6)
        self.assertEqual(p1.money, 6)
        self.assertEqual(p2.money, 4)

    def test_tc_p2_tgt_03_round_1_monolithic_state_parity(self) -> None:
        """TC-P2-TGT-03: Round 1 Monolithic State Parity.

        Setup: 4P pod, Round 1 baselines ($6 cash each). Trigger Space 2 Script Kiddie.
        Assert ALL 4 players lose $2 ($4 each). Total drain = $8.00 (100% parity with baseline).
        """
        cfg = GameConfig.v040(num_players=4, starting_money=6)
        engine = GameEngine(cfg, seed=42)
        for p in engine.state.players:
            p.money = 6

        space = self.std_cards["SCRIPT_KIDDIE"].corruption_track[1]
        resolve_corruption_space(engine, space, [], {})

        for p in engine.state.players:
            self.assertEqual(p.money, 4)
        total_drain = sum(6 - p.money for p in engine.state.players)
        self.assertEqual(total_drain, 8)

    def test_tc_p2_tgt_04_fewest_glitched_shield_slots(self) -> None:
        """TC-P2-TGT-04: Fewest Glitched Shield Slots.

        Setup: P0 has 1 glitched slot, P1 has 2, P2 has 3. Space 4 Data Scraper.
        Assert only P0 glitches 1 slot (P0 now has 2). P1 and P2 untouched.
        """
        cfg = GameConfig.v040(num_players=3, glitched_shield_slots_enabled=True)
        engine = GameEngine(cfg, seed=42)
        p0, p1, p2 = engine.state.players[0], engine.state.players[1], engine.state.players[2]
        p0.glitched_shield_slots = 1
        p1.glitched_shield_slots = 2
        p2.glitched_shield_slots = 3

        space = self.std_cards["DATA_SCRAPER"].corruption_track[3]  # Space 4
        self.assertEqual(space.index, 4)
        self.assertEqual(space.target_criterion, TargetCriterion.FEWEST_GLITCHED)
        self.assertEqual(space.demote_dice, 1)

        resolve_corruption_space(engine, space, [], {})

        self.assertEqual(p0.glitched_shield_slots, 2)
        self.assertEqual(p1.glitched_shield_slots, 2)
        self.assertEqual(p2.glitched_shield_slots, 3)

    def test_tc_p2_tgt_05_transfer_unique_leader_and_trailer(self) -> None:
        """TC-P2-TGT-05: Transfer: Unique Leader & Trailer (INV-TARGET-03).

        Setup: P0 has 18 MS ($5), P1 has 12 MS ($2). RaaS Space 1.
        Assert P0 loses $1 ($4), P1 gains $1 ($3). Net table cash delta = $0.00.
        """
        cfg = GameConfig.v040(num_players=2)
        engine = GameEngine(cfg, seed=42)
        p0, p1 = engine.state.players[0], engine.state.players[1]
        p0.market_share = 18
        p0.money = 5
        p1.market_share = 12
        p1.money = 2

        space = self.std_cards["RAAS"].corruption_track[0]  # Space 1
        self.assertEqual(space.index, 1)
        self.assertEqual(space.transfer_type, TransferType.LEAST_MS_TAKES_CASH)
        self.assertEqual(space.transfer_amount, 1)

        resolve_corruption_space(engine, space, [], {})

        self.assertEqual(p0.money, 4)
        self.assertEqual(p1.money, 3)
        self.assertEqual(p0.money + p1.money, 7)  # Zero-sum macro table conservation

    def test_tc_p2_tgt_06_transfer_table_wide_tie_fizzle(self) -> None:
        """TC-P2-TGT-06: Transfer: Table-Wide Tie Fizzle (INV-TARGET-04).

        Setup: 4P pod, all players at 16 MS. RaaS Space 1 triggers.
        Assert max == min; 0 cash moved; telemetry logs fizzle event.
        """
        cfg = GameConfig.v040(num_players=4)
        engine = GameEngine(cfg, seed=42)
        for p in engine.state.players:
            p.market_share = 16
            p.money = 5

        space = self.std_cards["RAAS"].corruption_track[0]
        events = resolve_corruption_transfer(engine, space)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["status"], "fizzle")
        self.assertEqual(events[0]["reason"], "all_players_tied")

        for p in engine.state.players:
            self.assertEqual(p.money, 5)

    def test_tc_p2_tgt_07_transfer_tied_donors_agency(self) -> None:
        """TC-P2-TGT-07: Transfer: Tied Donors Agency (INV-TARGET-05).

        Setup: P0 has 16 MS ($5, 4 Secrets), P1 has 16 MS ($5, 7 Secrets), P2 has 10 MS ($2).
        P2 bot hook selects P1 (higher Secrets). Assert P1 loses $1, P2 gains $1, P0 untouched.
        """
        cfg = GameConfig.v040(num_players=3)
        engine = GameEngine(cfg, seed=42)
        p0, p1, p2 = engine.state.players[0], engine.state.players[1], engine.state.players[2]
        p0.market_share = 16
        p0.money = 5
        p0.secrets = 4

        p1.market_share = 16
        p1.money = 5
        p1.secrets = 7

        p2.market_share = 10
        p2.money = 2
        p2.secrets = 5

        space = self.std_cards["RAAS"].corruption_track[0]
        resolve_corruption_space(engine, space, [], {})

        self.assertEqual(p0.money, 5)  # untouched
        self.assertEqual(p1.money, 4)  # donor (lost $1)
        self.assertEqual(p2.money, 3)  # receiver (gained $1)

    def test_tc_p2_tgt_08_transfer_zero_floor_protection(self) -> None:
        """TC-P2-TGT-08: Transfer: Zero-Floor Protection (INV-TARGET-07).

        Setup: P0 has 18 MS, but $0 cash. P1 has 10 MS, $2 cash. RaaS Space 1.
        Assert P0 loses $0, P1 gains $0. P0 cash never drops to negative.
        """
        cfg = GameConfig.v040(num_players=2)
        engine = GameEngine(cfg, seed=42)
        p0, p1 = engine.state.players[0], engine.state.players[1]
        p0.market_share = 18
        p0.money = 0
        p1.market_share = 10
        p1.money = 2

        space = self.std_cards["RAAS"].corruption_track[0]
        events = resolve_corruption_transfer(engine, space)

        self.assertEqual(p0.money, 0)
        self.assertEqual(p1.money, 2)
        self.assertEqual(events[0]["actual_moved"], 0)

    def test_tc_p2_tgt_09_compound_space_zero_day_space_2(self) -> None:
        """TC-P2-TGT-09: Compound Space: Zero-Day Space 2.

        Setup: P0 has Most $ ($10, 1 🔬), P1 has Most 🔬 ($2, 5 🔬). Space 2 triggers.
        Assert P0 loses $3 cash, P1 loses 1 🔬. Both independent criteria hit their respective leader.
        """
        cfg = GameConfig.v040(num_players=2)
        engine = GameEngine(cfg, seed=42)
        p0, p1 = engine.state.players[0], engine.state.players[1]
        p0.money = 10
        p0.research = 1

        p1.money = 2
        p1.research = 5

        space = self.std_cards["ZERO_DAY_OVERRIDE"].corruption_track[1]  # Space 2
        self.assertEqual(space.index, 2)
        self.assertEqual(space.target_money_criterion, TargetCriterion.MOST_MONEY)
        self.assertEqual(space.target_patches_criterion, TargetCriterion.MOST_RESEARCH)
        self.assertEqual(space.lose_money, 3)
        self.assertEqual(space.lose_patches, 1)

        resolve_corruption_space(engine, space, [], {})

        self.assertEqual(p0.money, 7)  # lost $3
        self.assertEqual(p0.research, 1)  # untouched
        self.assertEqual(p1.money, 2)  # untouched
        self.assertEqual(p1.research, 4)  # lost 1 🔬

    def test_tc_p2_tgt_10_deprecate_module_gray_die_immunity(self) -> None:
        """TC-P2-TGT-10: Deprecate Module: Gray Die Immunity (INV-TARGET-07).

        Setup: P0 has 4 colored dice + 2 Gray; P1 has 0 colored dice + 2 Gray. Space 5 Zero-Day Override.
        Assert P0 returns 1 colored die. Gray dice cannot be returned.
        """
        cfg = GameConfig.v040(num_players=2)
        engine = GameEngine(cfg, seed=42)
        p0, p1 = engine.state.players[0], engine.state.players[1]

        # Clear starting dice
        p0.ready_for_release_dice.clear()
        p1.ready_for_release_dice.clear()
        p0.in_production_dice.clear()
        p1.in_production_dice.clear()
        p0.scanned_dice.clear()
        p1.scanned_dice.clear()
        p0.glitched_dice.clear()
        p1.glitched_dice.clear()

        # P0: 2 Gray + 4 Red
        p0.ready_for_release_dice.extend([create_gray_die(1), create_gray_die(2)])
        for i in range(4):
            p0.ready_for_release_dice.append(create_colored_die(DieColor.RED, 10 + i))

        # P1: 2 Gray
        p1.ready_for_release_dice.extend([create_gray_die(3), create_gray_die(4)])

        self.assertEqual(len(p0.colored_dice), 4)
        self.assertEqual(len(p1.colored_dice), 0)

        space = self.std_cards["ZERO_DAY_OVERRIDE"].corruption_track[4]  # Space 5
        self.assertEqual(space.index, 5)
        self.assertEqual(space.target_criterion, TargetCriterion.MOST_COLORED_DICE)
        self.assertEqual(space.return_colored_dice, 1)

        commitments = [
            (p0, list(p0.ready_for_release_dice), {}),
            (p1, list(p1.ready_for_release_dice), {}),
        ]
        resolve_corruption_space(engine, space, commitments, {})

        self.assertEqual(len(p0.colored_dice), 3)  # returned 1 colored die
        # Gray dice strictly conserved
        self.assertEqual(len([d for d in p0.ready_for_release_dice if d.color == DieColor.GRAY]), 2)
        self.assertEqual(len([d for d in p1.ready_for_release_dice if d.color == DieColor.GRAY]), 2)

    def test_tc_p2_tgt_11_corporate_secrets_patient_zero(self) -> None:
        """TC-P2-TGT-11: Corporate Secrets Patient Zero.

        Setup: P0 has 1 Secret (tied for most), P1 has 1 Secret. Kernel Space 4 (-1 Secret).
        Assert P0 and P1 both drop to 0 Secrets and are marked Patient Zero.
        """
        cfg = GameConfig.v040(num_players=2)
        engine = GameEngine(cfg, seed=42)
        p0, p1 = engine.state.players[0], engine.state.players[1]
        p0.secrets = 1
        p1.secrets = 1

        space = self.std_cards["CORRUPTED_KERNEL"].corruption_track[3]  # Space 4
        self.assertEqual(space.index, 4)
        self.assertEqual(space.target_criterion, TargetCriterion.MOST_SECRETS)
        self.assertEqual(space.lose_secrets, 1)

        resolve_corruption_space(engine, space, [], {})

        self.assertEqual(p0.secrets, 0)
        self.assertEqual(p1.secrets, 0)
        self.assertTrue(p0.is_patient_zero)
        self.assertTrue(p1.is_patient_zero)
        self.assertIn("Total Breach", p0.elimination_reason or "")
        self.assertIn("Total Breach", p1.elimination_reason or "")

    def test_tc_p2_tgt_12_backwards_compatibility_toggle(self) -> None:
        """TC-P2-TGT-12: Backwards Compatibility Toggle (INV-TARGET-08).

        Set player_specific_corruption = False. Script Kiddie Space 2 runs with P0=$10, P1=$6.
        Assert both P0 and P1 lose $2 (legacy table-wide drain).
        """
        cfg = GameConfig(num_players=2, player_specific_corruption=False)
        engine = GameEngine(cfg, seed=42)
        p0, p1 = engine.state.players[0], engine.state.players[1]
        p0.money = 10
        p1.money = 6

        space = self.std_cards["SCRIPT_KIDDIE"].corruption_track[1]  # Space 2 (lose_money=2)
        resolve_corruption_space(engine, space, [], {})

        self.assertEqual(p0.money, 8)  # lost $2
        self.assertEqual(p1.money, 4)  # lost $2 (table-wide hit despite not being leader)

    def test_tc_p2_tgt_13_option_b_threat_conservation(self) -> None:
        """TC-P2-TGT-13: Option B Threat Conservation (INV-TARGET-06).

        Assert all 6 Version cards in Profile 1 and Profile 2 conserve Attack cubes, Black cubes,
        and cap enforcement exactly bit-for-bit per Option B.
        """
        for profile in ("V041_STANDARD", "V041_AGGRESSIVE"):
            cards = {c.directive_code: c for c in get_all_version_cards(profile=profile, player_specific=True)}
            v1_cards = [cards["SCRIPT_KIDDIE"], cards["DATA_SCRAPER"]]
            v2_cards = [cards["RAAS"], cards["POLYMORPHIC_WORM"]]
            v3_cards = [cards["ZERO_DAY_OVERRIDE"], cards["CORRUPTED_KERNEL"]]

            decks = list(itertools.product(v1_cards, v2_cards, v3_cards))
            self.assertEqual(len(decks), 8)

            red_counts: List[int] = []
            blue_counts: List[int] = []
            green_counts: List[int] = []
            black_counts: List[int] = []

            for v1, v2, v3 in decks:
                counts: Counter[CubeColor] = Counter(V038D_V1_STAGING_PAYLOAD[v1.directive_code])
                # Round 1 Phase 1 Autonomous Protocol Pulse (+1 Black)
                counts[CubeColor.BLACK] += 1

                for card in (v1, v2, v3):
                    for space in card.corruption_track:
                        counts.update(space.add_cubes)

                attack_cubes = (
                    counts[CubeColor.RED]
                    + counts[CubeColor.BLUE]
                    + counts[CubeColor.GREEN]
                )
                total_cubes = attack_cubes + counts[CubeColor.BLACK]

                if v3.directive_code == "ZERO_DAY_OVERRIDE":
                    self.assertEqual(attack_cubes, 15)
                    self.assertEqual(total_cubes, 21)
                elif v3.directive_code == "CORRUPTED_KERNEL":
                    self.assertEqual(attack_cubes, 13)
                    self.assertEqual(total_cubes, 19)

                # Black cubes strictly conserved at 6
                self.assertEqual(counts[CubeColor.BLACK], 6)

                red_counts.append(counts[CubeColor.RED])
                blue_counts.append(counts[CubeColor.BLUE])
                green_counts.append(counts[CubeColor.GREEN])
                black_counts.append(counts[CubeColor.BLACK])

            # Range bounds check
            self.assertEqual((min(green_counts), max(green_counts)), (2, 5))
            self.assertEqual((min(blue_counts), max(blue_counts)), (3, 6))
            self.assertEqual((min(red_counts), max(red_counts)), (4, 8))
            self.assertTrue(all(k == 6 for k in black_counts))


if __name__ == "__main__":
    unittest.main()
