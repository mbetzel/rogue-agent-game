"""Comprehensive unit tests for Rogue Agent RULES.md v0.7 specifications.

Covers all 18 technical test cases from the Principal Engineer specification:
1. test_config_parameters_v07: GameConfig progressive contractor pricing (1, 2, 3), cost helper methods, Yellow die VP=4.
2. test_white_contractor_die_faces_v07: 3x Block 1 Any, 1x +$1, 2x Glitch (Locked), zero +1 🔧 faces.
3. test_yellow_die_faces_and_vp_v07: Yellow die face 2 is +$2, vp is 4.
4. test_version_cards_2p_payloads: 2P staging payloads configured for RaaS, Polymorphic Worm, Zero-Day Override, Corrupted Kernel.
5. test_staging_cup_initialization_2p_and_4p: Engine initializes staging cup using card.get_staging_payload(config.num_players).
6. test_step_2a_version_upgrade_payload_2p_vs_4p: Version upgrades add scaled 2P vs 4P payloads to staging cup.
7. test_contractor_progressive_cost_calculation: get_contractor_cost_for_hire calculates exact cumulative progressive costs ($1, $3, $6).
8. test_contractor_hiring_single_call_deduction: Hiring multiple contractors in a single call deducts progressive cumulative cost ($6 for 3).
9. test_contractor_hiring_sequential_calls: Sequential Phase 1 hire calls charge incremental progressive costs ($1 for 1st, $2 for 2nd, $3 for 3rd).
10. test_contractor_hiring_max_hire_limit_enforced: Max hire of 3 per round is strictly enforced across sequential calls.
11. test_contractor_hiring_insufficient_funds_progressive: Rejects hire when player cannot afford the progressive cost of subsequent contractor.
12. test_commercial_exposure_ready_yellow_demoted_first: Ready Yellow dice are demoted to Unpatched first before Contractor Sacrifice can absorb Green malware.
13. test_commercial_exposure_multiple_green_malware: Demotes Ready Yellow die first, then uses Contractor Sacrifice for subsequent Green malware.
14. test_commercial_exposure_no_yellow_allows_contractor_sacrifice: When player has no Ready Yellow dice, Contractor Sacrifice absorbs malware normally.
15. test_commercial_exposure_unpatched_yellow_not_demoted_again: Unpatched Yellow dice do not prevent Contractor Sacrifice from absorbing malware.
16. test_bot_contractor_hiring_thresholds: Bot archetypes (AdaptiveBalanced, SecOpsTurtle, VentureGreed, RecklessSaboteur) follow progressive thresholds ($1, $3, $6).
17. test_schema_serialization_v07: GameStateSerializer exports contractor_cost_progression, next_contractor_cost, staging_payload_2p, and Yellow VP=4.
18. test_action_capabilities_next_contractor_cost: Capabilities check next contractor cost and update can_hire_contractors dynamically.
"""

from __future__ import annotations

import random
import unittest
from typing import Dict, List, Optional

from sim.bots import (
    AccelerationistBot,
    AdaptiveBalancedBot,
    BaseBot,
    Phase3ActionPlan,
    RecklessSaboteurBot,
    SecOpsTurtleBot,
    VentureGreedBot,
)
from sim.config import CubeColor, DieColor, EndGameReason, GameConfig, ShieldColor
from sim.engine import GameEngine, PlayerState
from sim.entities import (
    Die,
    Face,
    VersionCard,
    create_colored_die,
    create_gray_die,
    create_white_die,
    get_all_version_cards,
)
from web.game_controller import GameController
from web.schemas import GameStateSerializer


class TestV07Rules(unittest.TestCase):
    # -------------------------------------------------------------------------
    # 1. GameConfig Parameters & Helpers (v0.7)
    # -------------------------------------------------------------------------
    def test_config_parameters_v07(self) -> None:
        """GameConfig defines progressive contractor pricing (1, 2, 3), cost helper methods, and Yellow VP=4."""
        cfg = GameConfig()
        self.assertEqual(cfg.contractor_cost_progression, (1, 2, 3))
        self.assertEqual(cfg.contractor_max_hire, 3)
        self.assertEqual(cfg.vp_per_die[DieColor.YELLOW], 4)

        # get_contractor_cost_for_hire helper
        self.assertEqual(cfg.get_contractor_cost_for_hire(0, 0), 0)
        self.assertEqual(cfg.get_contractor_cost_for_hire(1, 0), 1)  # 1st die = $1
        self.assertEqual(cfg.get_contractor_cost_for_hire(2, 0), 3)  # 1st + 2nd = 1 + 2 = $3
        self.assertEqual(cfg.get_contractor_cost_for_hire(3, 0), 6)  # 1st + 2nd + 3rd = 1 + 2 + 3 = $6
        self.assertEqual(cfg.get_contractor_cost_for_hire(1, 1), 2)  # 2nd die alone = $2
        self.assertEqual(cfg.get_contractor_cost_for_hire(2, 1), 5)  # 2nd + 3rd = 2 + 3 = $5
        self.assertEqual(cfg.get_contractor_cost_for_hire(1, 2), 3)  # 3rd die alone = $3

        # get_max_affordable_contractors helper
        self.assertEqual(cfg.get_max_affordable_contractors(money=0, already_hired=0), 0)
        self.assertEqual(cfg.get_max_affordable_contractors(money=1, already_hired=0), 1)
        self.assertEqual(cfg.get_max_affordable_contractors(money=2, already_hired=0), 1)
        self.assertEqual(cfg.get_max_affordable_contractors(money=3, already_hired=0), 2)
        self.assertEqual(cfg.get_max_affordable_contractors(money=5, already_hired=0), 2)
        self.assertEqual(cfg.get_max_affordable_contractors(money=6, already_hired=0), 3)
        self.assertEqual(cfg.get_max_affordable_contractors(money=10, already_hired=0), 3)  # Max hire cap
        self.assertEqual(cfg.get_max_affordable_contractors(money=10, already_hired=1), 2)  # Remaining cap
        self.assertEqual(cfg.get_max_affordable_contractors(money=10, already_hired=0, supply=2), 2)  # Supply cap

    # -------------------------------------------------------------------------
    # 2. White Contractor Die Faces (v0.7)
    # -------------------------------------------------------------------------
    def test_white_contractor_die_faces_v07(self) -> None:
        """White contractor die has 3x Block 1 Any, 1x +$1, 2x Glitch (Locked), zero +1 🔧 faces."""
        white_die = create_white_die(die_id=101)
        self.assertEqual(white_die.color, DieColor.WHITE)
        self.assertEqual(len(white_die.faces), 6)

        block_any_count = 0
        cash_1_count = 0
        patch_count = 0
        glitch_count = 0

        for face in white_die.faces:
            if face.is_glitch:
                glitch_count += 1
                self.assertEqual(face.money, 0)
                self.assertEqual(face.patches, 0)
                self.assertFalse(face.is_shield)
                self.assertEqual(face.name, "Glitch (Locked)")
            elif face.is_shield and face.shield_color == ShieldColor.ANY and face.block_amount == 1:
                block_any_count += 1
            elif face.money == 1:
                cash_1_count += 1
            elif face.patches > 0:
                patch_count += 1

        self.assertEqual(block_any_count, 3)
        self.assertEqual(cash_1_count, 1)
        self.assertEqual(patch_count, 0)
        self.assertEqual(glitch_count, 2)

        factory_die = create_colored_die(DieColor.WHITE, 102)
        self.assertEqual(factory_die.color, DieColor.WHITE)
        self.assertEqual(len(factory_die.faces), 6)

    # -------------------------------------------------------------------------
    # 3. Yellow Die Faces & VP (v0.7)
    # -------------------------------------------------------------------------
    def test_yellow_die_faces_and_vp_v07(self) -> None:
        """Yellow die face 2 is +$2 and VP is 4 in v0.7."""
        yellow_die = create_colored_die(DieColor.YELLOW, 201)
        self.assertEqual(yellow_die.vp, 4)
        self.assertEqual(yellow_die.cost, 5)
        self.assertEqual(len(yellow_die.faces), 6)

        # Faces: [+$3, +$2, +$2, +$1 & +1 🔧, star, star]
        self.assertEqual(yellow_die.faces[0].name, "+$3")
        self.assertEqual(yellow_die.faces[0].money, 3)

        self.assertEqual(yellow_die.faces[1].name, "+$2")
        self.assertEqual(yellow_die.faces[1].money, 2)

        self.assertEqual(yellow_die.faces[2].name, "+$2")
        self.assertEqual(yellow_die.faces[2].money, 2)

        self.assertEqual(yellow_die.faces[3].money, 1)
        self.assertEqual(yellow_die.faces[3].patches, 1)

        self.assertTrue(yellow_die.faces[4].is_star)
        self.assertTrue(yellow_die.faces[5].is_star)

    # -------------------------------------------------------------------------
    # 4. Version Cards 2P Payload Configuration
    # -------------------------------------------------------------------------
    def test_version_cards_2p_payloads(self) -> None:
        """Version cards configure 2P payloads: RaaS, Polymorphic Worm, Zero-Day Override, Corrupted Kernel (v0.7 Baseline)."""
        # Historical v0.7 version cards with 2P vs 4P payloads
        raas = VersionCard(
            version_str="v2.0",
            name="Ransomware-as-a-Service",
            staging_payload={CubeColor.RED: 2, CubeColor.GREEN: 1},
            directive_description="Encrypted Memory",
            directive_code="RAAS",
            staging_payload_2p={CubeColor.RED: 1, CubeColor.GREEN: 1},
        )
        self.assertEqual(raas.get_staging_payload(2), {CubeColor.RED: 1, CubeColor.GREEN: 1})
        self.assertEqual(raas.get_staging_payload(4), {CubeColor.RED: 2, CubeColor.GREEN: 1})

        worm = VersionCard(
            version_str="v2.0",
            name="Polymorphic Worm",
            staging_payload={CubeColor.GREEN: 1, CubeColor.BLUE: 1, CubeColor.BLACK: 1},
            directive_description="Subroutine Throttling",
            directive_code="POLYMORPHIC_WORM",
            staging_payload_2p={CubeColor.GREEN: 1, CubeColor.BLACK: 1},
        )
        self.assertEqual(worm.get_staging_payload(2), {CubeColor.GREEN: 1, CubeColor.BLACK: 1})
        self.assertEqual(worm.get_staging_payload(4), {CubeColor.GREEN: 1, CubeColor.BLUE: 1, CubeColor.BLACK: 1})

        zero_day = VersionCard(
            version_str="v3.0",
            name="Zero-Day Override",
            staging_payload={CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.BLACK: 1},
            directive_description="Kernel Lock",
            directive_code="ZERO_DAY_OVERRIDE",
            staging_payload_2p={CubeColor.RED: 1, CubeColor.BLACK: 1},
        )
        self.assertEqual(zero_day.get_staging_payload(2), {CubeColor.RED: 1, CubeColor.BLACK: 1})
        self.assertEqual(zero_day.get_staging_payload(4), {CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.BLACK: 1})

        kernel = VersionCard(
            version_str="v3.0",
            name="Corrupted Kernel",
            staging_payload={CubeColor.RED: 2, CubeColor.BLUE: 1},
            directive_description="Corrupted Kernel",
            directive_code="CORRUPTED_KERNEL",
            staging_payload_2p={CubeColor.RED: 1, CubeColor.BLUE: 1},
        )
        self.assertEqual(kernel.get_staging_payload(2), {CubeColor.RED: 1, CubeColor.BLUE: 1})
        self.assertEqual(kernel.get_staging_payload(4), {CubeColor.RED: 2, CubeColor.BLUE: 1})

        # Script Kiddie (v1.0): flat across 2P and 4P
        cards = {c.directive_code: c for c in get_all_version_cards()}
        kiddie = cards["SCRIPT_KIDDIE"]
        self.assertEqual(kiddie.get_staging_payload(2), kiddie.get_staging_payload(4))

    # -------------------------------------------------------------------------
    # 5. Staging Cup Initialization 2P and 4P
    # -------------------------------------------------------------------------
    def test_staging_cup_initialization_2p_and_4p(self) -> None:
        """Engine initializes staging cup using version_deck[0].get_staging_payload(num_players)."""
        engine_2p = GameEngine(
            config=GameConfig(num_players=2),
            bots=[BaseBot(0), BaseBot(1)],
            seed=42,
        )
        self.assertEqual(engine_2p.state.staging_cup[CubeColor.RED], 1)
        self.assertEqual(engine_2p.state.staging_cup[CubeColor.BLUE], 1)
        self.assertEqual(engine_2p.state.staging_cup[CubeColor.GREEN], 1)
        self.assertEqual(engine_2p.state.staging_cup[CubeColor.BLACK], 1)

        engine_4p = GameEngine(
            config=GameConfig(num_players=4),
            bots=[BaseBot(0), BaseBot(1), BaseBot(2), BaseBot(3)],
            seed=42,
        )
        self.assertEqual(engine_4p.state.staging_cup[CubeColor.RED], 1)
        self.assertEqual(engine_4p.state.staging_cup[CubeColor.BLUE], 1)
        self.assertEqual(engine_4p.state.staging_cup[CubeColor.GREEN], 1)
        self.assertEqual(engine_4p.state.staging_cup[CubeColor.BLACK], 1)

    # -------------------------------------------------------------------------
    # 6. Step 2A Version Upgrade Payload 2P vs 4P
    # -------------------------------------------------------------------------
    def test_step_2a_version_upgrade_payload_2p_vs_4p(self) -> None:
        """In Step 2A, version upgrade to RaaS adds 1 Red, 1 Green in 2P, and 2 Red, 1 Green in 4P."""
        # 2-Player Match
        engine_2p = GameEngine(
            config=GameConfig(num_players=2),
            bots=[BaseBot(0), BaseBot(1)],
            seed=42,
        )
        engine_2p.state.tower.calculate_exit_probability = lambda count: 1.0
        engine_2p.state.tower.reset()
        engine_2p.state.staging_cup = {CubeColor.BLACK: 4, CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0}
        engine_2p._execute_phase_2([(engine_2p.state.players[0], [], {}), (engine_2p.state.players[1], [], {})])

        self.assertEqual(engine_2p.state.current_version_index, 1)  # v2.0 RaaS
        self.assertEqual(engine_2p.state.staging_cup[CubeColor.RED], 3)  # v0.15.0 Script Kiddie spaces 1 & 4 (2) + RaaS 2p payload (1) = 3 Red
        self.assertEqual(engine_2p.state.staging_cup[CubeColor.GREEN], 2)  # v0.15.0 Script Kiddie space 1 (1) + RaaS 2p payload (1) = 2 Green

        # 4-Player Match
        v07_raas = VersionCard(
            version_str="v2.0",
            name="Ransomware-as-a-Service",
            staging_payload={CubeColor.RED: 2, CubeColor.GREEN: 1},
            directive_description="Encrypted Memory",
            directive_code="RAAS",
            staging_payload_2p={CubeColor.RED: 1, CubeColor.GREEN: 1},
        )
        custom_v07_deck = [
            get_all_version_cards()[0],
            v07_raas,
            get_all_version_cards()[4],
        ]
        engine_4p = GameEngine(
            config=GameConfig(num_players=4, corruption_track_flat_capacity=4),
            bots=[BaseBot(0), BaseBot(1), BaseBot(2), BaseBot(3)],
            seed=42,
            version_deck=custom_v07_deck,
        )
        engine_4p.state.tower.calculate_exit_probability = lambda count: 1.0
        engine_4p.state.tower.reset()
        engine_4p.state.staging_cup = {CubeColor.BLACK: 4, CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0}
        engine_4p._execute_phase_2([(p, [], {}) for p in engine_4p.state.players])

        self.assertEqual(engine_4p.state.current_version_index, 1)  # v2.0 RaaS
        self.assertEqual(engine_4p.state.staging_cup[CubeColor.RED], 4)  # v0.15.0 Script Kiddie spaces 1 & 4 (2) + 4P payload (2) = 4 Red
        self.assertEqual(engine_4p.state.staging_cup[CubeColor.GREEN], 2)  # v0.15.0 Script Kiddie space 1 (1) + 4P payload (1) = 2 Green

    # -------------------------------------------------------------------------
    # 7. Contractor Progressive Cost Calculation
    # -------------------------------------------------------------------------
    def test_contractor_progressive_cost_calculation(self) -> None:
        """get_contractor_cost_for_hire calculates exact progressive cumulative costs."""
        cfg = GameConfig()
        # From 0 hired: 1 die costs $1, 2 dice cost $3, 3 dice cost $6
        self.assertEqual(cfg.get_contractor_cost_for_hire(1, already_hired=0), 1)
        self.assertEqual(cfg.get_contractor_cost_for_hire(2, already_hired=0), 3)
        self.assertEqual(cfg.get_contractor_cost_for_hire(3, already_hired=0), 6)

        # From 1 hired: 1 more die costs $2 (2nd die), 2 more dice cost $5 (2nd + 3rd = 2 + 3)
        self.assertEqual(cfg.get_contractor_cost_for_hire(1, already_hired=1), 2)
        self.assertEqual(cfg.get_contractor_cost_for_hire(2, already_hired=1), 5)

        # From 2 hired: 1 more die costs $3 (3rd die)
        self.assertEqual(cfg.get_contractor_cost_for_hire(1, already_hired=2), 3)

    # -------------------------------------------------------------------------
    # 8. Contractor Hiring Single Call Deduction
    # -------------------------------------------------------------------------
    def test_contractor_hiring_single_call_deduction(self) -> None:
        """Hiring 3 contractors in a single call costs $6 ($1 + $2 + $3)."""
        ctrl = GameController()
        ctrl.new_game(num_players=2, seed=42)
        ctrl.state.players[0].money = 7

        ctrl.hire_contractors(player_id=0, count=3)
        self.assertEqual(ctrl.state.players[0].money, 1)  # $7 - $6 = $1
        self.assertEqual(len(ctrl.state.players[0].contractor_dice), 3)
        self.assertEqual(ctrl.player_meta[0]["hired_contractors"], 3)
        self.assertEqual(ctrl.state.contractor_supply, 9)

    # -------------------------------------------------------------------------
    # 9. Contractor Hiring Sequential Calls
    # -------------------------------------------------------------------------
    def test_contractor_hiring_sequential_calls(self) -> None:
        """Sequential Phase 1 hire calls charge incremental progressive costs ($1, $2, $3)."""
        ctrl = GameController()
        ctrl.new_game(num_players=2, seed=42)
        ctrl.state.players[0].money = 7

        # 1st hire: 1 contractor costs $1
        ctrl.hire_contractors(player_id=0, count=1)
        self.assertEqual(ctrl.state.players[0].money, 6)
        self.assertEqual(ctrl.player_meta[0]["hired_contractors"], 1)

        # 2nd hire: 1 contractor costs $2
        ctrl.hire_contractors(player_id=0, count=1)
        self.assertEqual(ctrl.state.players[0].money, 4)  # $6 - $2 = $4
        self.assertEqual(ctrl.player_meta[0]["hired_contractors"], 2)

        # 3rd hire: 1 contractor costs $3
        ctrl.hire_contractors(player_id=0, count=1)
        self.assertEqual(ctrl.state.players[0].money, 1)  # $4 - $3 = $1
        self.assertEqual(ctrl.player_meta[0]["hired_contractors"], 3)
        self.assertEqual(len(ctrl.state.players[0].contractor_dice), 3)

    # -------------------------------------------------------------------------
    # 10. Contractor Hiring Max Limit Enforced
    # -------------------------------------------------------------------------
    def test_contractor_hiring_max_hire_limit_enforced(self) -> None:
        """Cannot exceed maximum 3 contractors per round across sequential calls."""
        ctrl = GameController()
        ctrl.new_game(num_players=2, seed=42)
        ctrl.state.players[0].money = 15

        ctrl.hire_contractors(player_id=0, count=2)  # Hired 2
        with self.assertRaises(ValueError):
            ctrl.hire_contractors(player_id=0, count=2)  # 2 + 2 = 4 > 3 -> reject

        ctrl.hire_contractors(player_id=0, count=1)  # Hired 3rd (now 3)
        self.assertEqual(ctrl.player_meta[0]["hired_contractors"], 3)

        with self.assertRaises(ValueError):
            ctrl.hire_contractors(player_id=0, count=1)  # 3 + 1 = 4 > 3 -> reject

    # -------------------------------------------------------------------------
    # 11. Contractor Hiring Insufficient Funds Progressive
    # -------------------------------------------------------------------------
    def test_contractor_hiring_insufficient_funds_progressive(self) -> None:
        """Player with $2 can afford 1st contractor ($1) but cannot afford 2nd ($2)."""
        ctrl = GameController()
        ctrl.new_game(num_players=2, seed=42)
        ctrl.state.players[0].money = 2

        # 1st die costs $1 -> succeeds
        ctrl.hire_contractors(player_id=0, count=1)
        self.assertEqual(ctrl.state.players[0].money, 1)

        # 2nd die costs $2, but player only has $1 -> raises ValueError
        with self.assertRaises(ValueError):
            ctrl.hire_contractors(player_id=0, count=1)

    # -------------------------------------------------------------------------
    # 12. Commercial Exposure: Ready Yellow Demoted First
    # -------------------------------------------------------------------------
    def test_commercial_exposure_ready_yellow_demoted_first(self) -> None:
        """Commercial Exposure: Ready Yellow die is demoted first before Contractor Sacrifice can absorb Green malware."""
        engine = GameEngine(
            config=GameConfig(num_players=2),
            bots=[BaseBot(0), BaseBot(1)],
            seed=42,
        )
        p0 = engine.state.players[0]

        yellow_die = create_colored_die(DieColor.YELLOW, 101)
        gray_die = create_gray_die(102)
        white_die = create_white_die(103)

        p0.ready_dice = [yellow_die, gray_die]
        p0.contractor_dice = [white_die]
        p0.unpatched_dice = []
        engine.state.contractor_supply = 10

        # 1 unblocked Green malware hits
        engine._resolve_player_defense_and_wear(
            player=p0,
            rolled_dice=[],
            commitments={},
            attack_strengths={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 1},
            exited_cubes={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 1},
            active_directive="NONE",
        )

        # Commercial Exposure enforced: Yellow die demoted to unpatched!
        self.assertEqual(len(p0.unpatched_dice), 1)
        self.assertEqual(p0.unpatched_dice[0].color, DieColor.YELLOW)
        # Contractor die was NOT sacrificed
        self.assertEqual(len(p0.contractor_dice), 1)
        # Gray die remains in ready zone
        self.assertEqual(len(p0.ready_dice), 1)
        self.assertEqual(p0.ready_dice[0].color, DieColor.GRAY)

    # -------------------------------------------------------------------------
    # 13. Commercial Exposure: Multiple Green Malware
    # -------------------------------------------------------------------------
    def test_commercial_exposure_multiple_green_malware(self) -> None:
        """With 2 Green malware: 1st demotes Ready Yellow; 2nd is absorbed by Contractor Sacrifice."""
        engine = GameEngine(
            config=GameConfig(num_players=2),
            bots=[BaseBot(0), BaseBot(1)],
            seed=42,
        )
        p0 = engine.state.players[0]

        yellow_die = create_colored_die(DieColor.YELLOW, 101)
        gray_die = create_gray_die(102)
        white_die = create_white_die(103)

        p0.ready_dice = [yellow_die, gray_die]
        p0.contractor_dice = [white_die]
        p0.unpatched_dice = []
        engine.state.contractor_supply = 10

        # 2 unblocked Green malware hit
        engine._resolve_player_defense_and_wear(
            player=p0,
            rolled_dice=[],
            commitments={},
            attack_strengths={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 2},
            exited_cubes={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 2},
            active_directive="NONE",
        )

        # 1st malware: Yellow demoted to unpatched
        self.assertEqual(len(p0.unpatched_dice), 1)
        self.assertEqual(p0.unpatched_dice[0].color, DieColor.YELLOW)
        # 2nd malware: Contractor sacrificed to supply
        self.assertEqual(len(p0.contractor_dice), 0)
        self.assertEqual(engine.state.contractor_supply, 11)
        # Gray die untouched in ready zone
        self.assertEqual(len(p0.ready_dice), 1)
        self.assertEqual(p0.ready_dice[0].color, DieColor.GRAY)

    # -------------------------------------------------------------------------
    # 14. Commercial Exposure: No Yellow Allows Contractor Sacrifice
    # -------------------------------------------------------------------------
    def test_commercial_exposure_no_yellow_allows_contractor_sacrifice(self) -> None:
        """When player has no Ready Yellow dice, Contractor Sacrifice absorbs Green malware normally."""
        engine = GameEngine(
            config=GameConfig(num_players=2),
            bots=[BaseBot(0), BaseBot(1)],
            seed=42,
        )
        p0 = engine.state.players[0]

        gray1 = create_gray_die(101)
        gray2 = create_gray_die(102)
        white_die = create_white_die(103)

        p0.ready_dice = [gray1, gray2]
        p0.contractor_dice = [white_die]
        p0.unpatched_dice = []
        engine.state.contractor_supply = 10

        engine._resolve_player_defense_and_wear(
            player=p0,
            rolled_dice=[],
            commitments={},
            attack_strengths={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 1},
            exited_cubes={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 1},
            active_directive="NONE",
        )

        # Contractor sacrificed to supply
        self.assertEqual(len(p0.contractor_dice), 0)
        self.assertEqual(engine.state.contractor_supply, 11)
        # Both gray dice remain ready; none unpatched
        self.assertEqual(len(p0.ready_dice), 2)
        self.assertEqual(len(p0.unpatched_dice), 0)

    # -------------------------------------------------------------------------
    # 15. Commercial Exposure: Unpatched Yellow Not Demoted Again
    # -------------------------------------------------------------------------
    def test_commercial_exposure_unpatched_yellow_not_demoted_again(self) -> None:
        """Unpatched Yellow dice do not trigger Commercial Exposure; Contractor Sacrifice absorbs malware."""
        engine = GameEngine(
            config=GameConfig(num_players=2),
            bots=[BaseBot(0), BaseBot(1)],
            seed=42,
        )
        p0 = engine.state.players[0]

        yellow_die = create_colored_die(DieColor.YELLOW, 101)
        gray_die = create_gray_die(102)
        white_die = create_white_die(103)

        p0.ready_dice = [gray_die]
        p0.unpatched_dice = [yellow_die]
        p0.contractor_dice = [white_die]
        engine.state.contractor_supply = 10

        engine._resolve_player_defense_and_wear(
            player=p0,
            rolled_dice=[],
            commitments={},
            attack_strengths={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 1},
            exited_cubes={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 1},
            active_directive="NONE",
        )

        # White contractor was sacrificed
        self.assertEqual(len(p0.contractor_dice), 0)
        self.assertEqual(engine.state.contractor_supply, 11)
        # Gray die remains ready
        self.assertEqual(len(p0.ready_dice), 1)
        self.assertEqual(len(p0.unpatched_dice), 1)

    # -------------------------------------------------------------------------
    # 16. Bot Contractor Hiring Progressive Thresholds
    # -------------------------------------------------------------------------
    def test_bot_contractor_hiring_thresholds(self) -> None:
        """Bots choose contractor hires reflecting progressive thresholds ($1, $3, $6)."""
        rng = random.Random(42)
        threats_high = {CubeColor.RED: 4, CubeColor.BLUE: 3, CubeColor.GREEN: 2}  # total 9
        threats_med = {CubeColor.RED: 3, CubeColor.BLUE: 2, CubeColor.GREEN: 1}   # total 6
        threats_low = {CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 1}   # total 3
        stuck_zero = {CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0}

        # AdaptiveBalancedBot: requires money >= 4 for 1, >= 6 for 2, >= 9 for 3
        bal = AdaptiveBalancedBot(0)
        p_bal = PlayerState(0, bal, money=3, secrets=7, patches=1)
        self.assertEqual(bal.choose_contractor_hires(p_bal, 12, threats_med, stuck_zero, rng), 0)
        p_bal.money = 4
        self.assertEqual(bal.choose_contractor_hires(p_bal, 12, threats_low, stuck_zero, rng), 1)
        p_bal.money = 6
        self.assertEqual(bal.choose_contractor_hires(p_bal, 12, threats_med, stuck_zero, rng), 2)
        p_bal.money = 9
        self.assertEqual(bal.choose_contractor_hires(p_bal, 12, threats_high, stuck_zero, rng), 3)

        # SecOpsTurtleBot: requires money >= 3 for 1, >= 5 for 2, >= 8 for 3
        turtle = SecOpsTurtleBot(1)
        p_turt = PlayerState(1, turtle, money=2, secrets=7, patches=1)
        self.assertEqual(turtle.choose_contractor_hires(p_turt, 12, threats_low, stuck_zero, rng), 0)
        p_turt.money = 3
        self.assertEqual(turtle.choose_contractor_hires(p_turt, 12, threats_low, stuck_zero, rng), 1)
        p_turt.money = 5
        self.assertEqual(turtle.choose_contractor_hires(p_turt, 12, threats_low, stuck_zero, rng), 2)
        p_turt.money = 8
        self.assertEqual(turtle.choose_contractor_hires(p_turt, 12, threats_med, stuck_zero, rng), 3)

        # VentureGreedBot: requires money >= 6 for 1, >= 8 for 2, >= 11 for 3
        greed = VentureGreedBot(2)
        p_grd = PlayerState(2, greed, money=5, secrets=7, patches=1)
        self.assertEqual(greed.choose_contractor_hires(p_grd, 12, threats_high, stuck_zero, rng), 0)
        p_grd.money = 6
        self.assertEqual(greed.choose_contractor_hires(p_grd, 12, threats_high, stuck_zero, rng), 1)
        p_grd.money = 8
        self.assertEqual(greed.choose_contractor_hires(p_grd, 12, threats_high, stuck_zero, rng), 2)
        p_grd.money = 11
        self.assertEqual(greed.choose_contractor_hires(p_grd, 12, threats_high, stuck_zero, rng), 3)

        # RecklessSaboteurBot: requires money >= 3 for 1, >= 5 for 2, >= 8 for 3
        sab = RecklessSaboteurBot(3)
        p_sab = PlayerState(3, sab, money=2, secrets=7, patches=1)
        self.assertEqual(sab.choose_contractor_hires(p_sab, 12, threats_low, stuck_zero, rng), 0)
        p_sab.money = 3
        self.assertEqual(sab.choose_contractor_hires(p_sab, 12, threats_low, stuck_zero, rng), 1)
        p_sab.money = 5
        self.assertEqual(sab.choose_contractor_hires(p_sab, 12, threats_low, stuck_zero, rng), 2)
        p_sab.money = 8
        self.assertEqual(sab.choose_contractor_hires(p_sab, 12, threats_low, stuck_zero, rng), 3)

    # -------------------------------------------------------------------------
    # 17. Schema Serialization v0.7
    # -------------------------------------------------------------------------
    def test_schema_serialization_v07(self) -> None:
        """GameStateSerializer exports contractor_cost_progression, staging_payload_2p, and next_contractor_cost."""
        ctrl = GameController()
        ctrl.new_game(num_players=2, seed=42)
        state_dict = ctrl.get_full_state()

        # Config / Top-level serialization
        self.assertIn("contractor_cost_progression", state_dict)
        self.assertEqual(state_dict["contractor_cost_progression"], [1, 2, 3])
        self.assertIn("next_contractor_cost", state_dict)
        self.assertEqual(state_dict["next_contractor_cost"], 1)

        # Yellow die VP in market is 4
        self.assertEqual(state_dict["market"]["yellow"]["vp"], 4)

        # Player serialization includes next_contractor_cost
        p0 = state_dict["players"][0]
        self.assertIn("next_contractor_cost", p0)
        self.assertEqual(p0["next_contractor_cost"], 1)

        # Version cards include staging_payload_2p
        for v in state_dict["version_deck"]:
            self.assertIn("staging_payload_2p", v)
            if v["directive_code"] == "RAAS":
                self.assertEqual(v["staging_payload_2p"], {"red": 1, "green": 1})

    # -------------------------------------------------------------------------
    # 18. Action Capabilities Dynamic Next Contractor Cost
    # -------------------------------------------------------------------------
    def test_action_capabilities_next_contractor_cost(self) -> None:
        """Capabilities reflect dynamic next contractor cost across progressive hires."""
        ctrl = GameController()
        ctrl.new_game(num_players=2, seed=42)
        ctrl.state.players[0].money = 4  # Can afford die 1 ($1) and die 2 ($2), but not die 3 ($3)

        caps0 = ctrl.get_action_capabilities(0)
        self.assertTrue(caps0["can_hire_contractors"])
        self.assertEqual(caps0["next_contractor_cost"], 1)

        # Hire 1st die ($1 paid, $3 left)
        ctrl.hire_contractors(player_id=0, count=1)
        caps1 = ctrl.get_action_capabilities(0)
        self.assertTrue(caps1["can_hire_contractors"])
        self.assertEqual(caps1["next_contractor_cost"], 2)

        # Hire 2nd die ($2 paid, $1 left)
        ctrl.hire_contractors(player_id=0, count=1)
        caps2 = ctrl.get_action_capabilities(0)
        self.assertEqual(caps2["next_contractor_cost"], 3)
        self.assertFalse(caps2["can_hire_contractors"])  # Needs $3, has $1

        # Give $5 cash -> now can afford 3rd die ($3)
        ctrl.state.players[0].money += 5
        caps2b = ctrl.get_action_capabilities(0)
        self.assertTrue(caps2b["can_hire_contractors"])

        # Hire 3rd die -> max hire reached
        ctrl.hire_contractors(player_id=0, count=1)
        caps3 = ctrl.get_action_capabilities(0)
        self.assertIsNone(caps3["next_contractor_cost"])
        self.assertFalse(caps3["can_hire_contractors"])


if __name__ == "__main__":
    unittest.main()
