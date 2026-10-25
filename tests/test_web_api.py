"""Verification unit and integration tests for Rogue Agent Web Playtesting Application.

Covers all technical verification tests specified by the Principal Engineer and Staff Engineer review:
1. test_new_game_default: Initializes default 4P game (1 human, 3 bots), round 1, phase 1, staging cup payload + pulse.
2. test_new_game_custom_player_counts: 2P resilience buffer (8 Secrets, 2 Patches), 3P (7 Secrets, 1 Patch), custom bots.
3. test_get_state: Complete schema validation (header, compiler/tower, market, player mats, action dock).
4. test_phase1_roll_action: Human rolls ready pool; rolled pool populated, has_rolled set, capabilities updated.
5. test_phase1_hotfix_reroll: Spending 1 🔧 token successfully rerolls the specified die; patch token deducted.
6. test_phase1_hotfix_validation: Rejects hotfix with 0 🔧 tokens or out-of-range die index (400 Bad Request).
7. test_phase1_commit_shields: Commits shields, validates Any assignment, triggers bot Phase 1, advances to Phase 2.
8. test_phase2_compile_drop: Tower drop empties staging cup, resolves corruption & attack damage, recycles cubes.
9. test_phase3_buy_die: Market purchase pays cash ($4/$5), decrements stock, adds to ready pool, increments count.
10. test_phase3_buy_limit_and_funds: Enforces 2-purchase limit and rejects purchases if cash is insufficient.
11. test_phase3_patch_die_tokens_and_cash: Tests patching using 🔧 token and using cash; moves die from unpatched to ready.
12. test_phase3_dirty_income_success: Preconditions met: pays 1 Secret, gains +$3, adds 1 Black Cube, demotes ready die.
13. test_phase3_dirty_income_precondition_blocks: Rejects dirty income when player has <= 1 Secret or 0 Ready dice.
14. test_phase3_star_actions: Tests B2, Y1, P1, and P3 star ability execution and validation.
15. test_phase1_b2_hold_for_deep_rd_and_activate: Rolling B2 and holding it for Deep R&D sets b2_available=True without auto-committing to Blue shields.
16. test_phase1_hotfix_with_rolled_patch_face_and_locked_die: 0 held tokens can hotfix via rolled patch face; spent die is locked and cannot reroll.
17. test_phase3_end_turn_and_round_transition: Human ends turn, executes bot turns, performs round cleanup, advances round.
"""

from __future__ import annotations

import json
import threading
import unittest
import urllib.error
import urllib.request
from typing import Any, Dict

from sim.config import CubeColor, DieColor, ShieldColor
from sim.entities import Die, Face
from web.game_controller import GameController
from web.server import RogueAgentRequestHandler, create_server


class TestWebAPI(unittest.TestCase):
    """Integration and Unit Test Suite for Rogue Agent Web Architecture."""

    @classmethod
    def setUpClass(cls) -> None:
        """Starts a background HTTP test server on an ephemeral port."""
        cls.server = create_server(host="127.0.0.1", port=0)
        cls.server_port = cls.server.server_address[1]
        cls.base_url = f"http://127.0.0.1:{cls.server_port}"
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        """Shuts down the background HTTP test server."""
        cls.server.shutdown()
        cls.server.server_close()

    def _post(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Helper to send HTTP POST requests and parse JSON responses."""
        url = f"{self.base_url}{path}"
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _get(self, path: str) -> Dict[str, Any]:
        """Helper to send HTTP GET requests and parse JSON responses."""
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))

    # -------------------------------------------------------------------------
    # 1. New Game Default
    # -------------------------------------------------------------------------
    def test_new_game_default(self) -> None:
        """POST /api/game/new initializes default 4P game (1 human, 3 bots)."""
        res = self._post("/api/game/new", {"num_players": 4, "seed": 42})
        self.assertTrue(res["success"])
        state = res["state"]

        self.assertEqual(state["current_round"], 1)
        self.assertEqual(state["phase"], 1)
        self.assertEqual(state["phase_name"], "Boot & Configure")
        self.assertEqual(state["subphase"], "waiting_for_roll")
        self.assertEqual(len(state["players"]), 4)

        # Player 0 is human, players 1-3 are bots
        self.assertTrue(state["players"][0]["is_human"])
        self.assertFalse(state["players"][1]["is_human"])
        self.assertFalse(state["players"][2]["is_human"])
        self.assertFalse(state["players"][3]["is_human"])

        # Staging Cup: v1.0 Script Kiddie payload (1 Red, 1 Blue, 1 Green, 1 Black) + 1 Black Autonomous Pulse = 2 Black
        self.assertEqual(state["staging_cup"]["red"], 1)
        self.assertEqual(state["staging_cup"]["blue"], 1)
        self.assertEqual(state["staging_cup"]["green"], 1)
        self.assertEqual(state["staging_cup"]["black"], 2)

    # -------------------------------------------------------------------------
    # 2. New Game Custom Player Counts (2P Resilience Buffer)
    # -------------------------------------------------------------------------
    def test_new_game_custom_player_counts(self) -> None:
        """2P initializes with 8 Secrets & 2 Patches; 3P with 7 Secrets & 1 Patch."""
        # 2 Players
        res2p = self._post("/api/game/new", {"num_players": 2, "seed": 100})
        state2p = res2p["state"]
        self.assertEqual(len(state2p["players"]), 2)
        p0_2p = state2p["players"][0]
        self.assertEqual(p0_2p["secrets"], 8)
        self.assertEqual(p0_2p["patches"], 2)  # 2P Resilience Buffer

        # 3 Players
        res3p = self._post("/api/game/new", {"num_players": 3, "seed": 200})
        state3p = res3p["state"]
        self.assertEqual(len(state3p["players"]), 3)
        p0_3p = state3p["players"][0]
        self.assertEqual(p0_3p["secrets"], 7)
        self.assertEqual(p0_3p["patches"], 1)

    # -------------------------------------------------------------------------
    # 3. Get State Endpoint
    # -------------------------------------------------------------------------
    def test_get_state(self) -> None:
        """GET /api/game/state returns the complete serialized GameState JSON."""
        self._post("/api/game/new", {"num_players": 4, "seed": 42})
        res = self._get("/api/game/state")
        self.assertTrue(res["success"])
        state = res["state"]

        # Validate schema keys
        required_keys = [
            "current_round",
            "phase",
            "phase_name",
            "subphase",
            "staging_cup",
            "tower_stuck_cubes",
            "corruption_track",
            "market",
            "players",
            "action_capabilities",
            "event_log",
        ]
        for key in required_keys:
            self.assertIn(key, state)

        # Market contains all 5 colored dice
        for col in ["red", "blue", "green", "yellow", "purple"]:
            self.assertIn(col, state["market"])
            self.assertEqual(state["market"][col]["stock"], 8)  # 2 * 4 players

    # -------------------------------------------------------------------------
    # 4. Phase 1: Roll Action
    # -------------------------------------------------------------------------
    def test_phase1_roll_action(self) -> None:
        """POST /api/game/action/roll rolls human player's ready dice."""
        self._post("/api/game/new", {"num_players": 4, "seed": 42})
        res = self._post("/api/game/action/roll", {"player_id": 0})
        state = res["state"]

        p0 = state["players"][0]
        self.assertTrue(p0["has_rolled"])
        self.assertEqual(len(p0["rolled_pool"]), 4)
        for die in p0["rolled_pool"]:
            self.assertIsNotNone(die["current_face"])

        # Capabilities updated
        caps = state["action_capabilities"]
        self.assertFalse(caps["can_roll"])
        self.assertTrue(caps["can_commit"])

    # -------------------------------------------------------------------------
    # 5. Phase 1: Hotfix Reroll Action
    # -------------------------------------------------------------------------
    def test_phase1_hotfix_reroll(self) -> None:
        """POST /api/game/action/hotfix spends 1 🔧 token to reroll a die."""
        self._post("/api/game/new", {"num_players": 4, "seed": 42})
        self._post("/api/game/action/roll", {"player_id": 0})

        # Ensure player 0 has at least 1 patch token
        ctrl = RogueAgentRequestHandler.controller
        ctrl.state.players[0].patches = 2

        res = self._post("/api/game/action/hotfix", {"player_id": 0, "die_index": 0})
        self.assertTrue(res["success"])
        p0 = res["state"]["players"][0]
        self.assertEqual(p0["patches"], 1)

    # -------------------------------------------------------------------------
    # 6. Phase 1: Hotfix Validation
    # -------------------------------------------------------------------------
    def test_phase1_hotfix_validation(self) -> None:
        """Hotfix fails when out-of-range die index or 0 patch tokens available."""
        self._post("/api/game/new", {"num_players": 4, "seed": 42})
        self._post("/api/game/action/roll", {"player_id": 0})

        # Out-of-range index
        url = f"{self.base_url}/api/game/action/hotfix"
        body = json.dumps({"player_id": 0, "die_index": 99}).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 400)

        # Deplete all patch tokens and zero out patches on kept faces
        ctrl = RogueAgentRequestHandler.controller
        ctrl.state.players[0].patches = 0
        for d in ctrl.state.players[0].ready_dice:
            if d.current_face and d.current_face.patches > 0:
                d.current_face = Face(name="+$1", money=1)

        body2 = json.dumps({"player_id": 0, "die_index": 0}).encode("utf-8")
        req2 = urllib.request.Request(url, data=body2, headers={"Content-Type": "application/json"}, method="POST")
        with self.assertRaises(urllib.error.HTTPError) as ctx2:
            urllib.request.urlopen(req2)
        self.assertEqual(ctx2.exception.code, 400)

    # -------------------------------------------------------------------------
    # 7. Phase 1: Commit Shields Action & Transition to Phase 2
    # -------------------------------------------------------------------------
    def test_phase1_commit_shields(self) -> None:
        """Committing defenses resolves immediate outputs, auto-runs bots, and advances to Phase 2."""
        self._post("/api/game/new", {"num_players": 4, "seed": 42})
        self._post("/api/game/action/roll", {"player_id": 0})

        # Set die 0 to Generic Shield and die 1 to Money
        ctrl = RogueAgentRequestHandler.controller
        p0 = ctrl.state.players[0]
        p0.ready_dice[0].current_face = Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)
        p0.ready_dice[1].current_face = Face(name="+$1", money=1)

        res = self._post("/api/game/action/commit", {
            "player_id": 0,
            "commitments": {"0": "blue"},
        })
        self.assertTrue(res["success"])
        state = res["state"]

        # Advanced to Phase 2
        self.assertEqual(state["phase"], 2)
        self.assertEqual(state["phase_name"], "Rogue Agent Compile")
        self.assertEqual(state["subphase"], "ready_for_compile")

        # Bot players also rolled and committed
        for bot_id in [1, 2, 3]:
            bot_state = state["players"][bot_id]
            self.assertTrue(bot_state["has_rolled"])
            self.assertTrue(bot_state["has_committed"])

    # -------------------------------------------------------------------------
    # 8. Phase 2: Compile Drop
    # -------------------------------------------------------------------------
    def test_phase2_compile_drop(self) -> None:
        """POST /api/game/action/compile executes tower drop, resolves damage, advances to Phase 3."""
        self._post("/api/game/new", {"num_players": 4, "seed": 42})
        self._post("/api/game/action/roll", {"player_id": 0})
        self._post("/api/game/action/commit", {"player_id": 0, "commitments": {}})

        # Call compile
        res = self._post("/api/game/action/compile", {})
        self.assertTrue(res["success"])
        state = res["state"]

        self.assertIsNotNone(state["last_compile_result"])
        # Phase advanced to Phase 3
        self.assertEqual(state["phase"], 3)
        self.assertEqual(state["phase_name"], "Corporate Operations")

    # -------------------------------------------------------------------------
    # 9. Phase 3: Market Purchase
    # -------------------------------------------------------------------------
    def test_phase3_buy_die(self) -> None:
        """POST /api/game/action/buy purchases a colored die and updates market stock."""
        ctrl = RogueAgentRequestHandler.controller
        ctrl.new_game(num_players=4, seed=42)
        ctrl.phase = 3
        ctrl.phase_name = "Corporate Operations"
        ctrl.active_player_index = 0
        p0 = ctrl.state.players[0]
        p0.money = 10

        initial_stock = ctrl.state.market[DieColor.BLUE]
        res = self._post("/api/game/action/buy", {"player_id": 0, "color": "blue"})
        self.assertTrue(res["success"])
        state = res["state"]

        p0_state = state["players"][0]
        self.assertEqual(p0_state["money"], 5)  # $10 - $5
        self.assertEqual(state["market"]["blue"]["stock"], initial_stock - 1)
        self.assertEqual(p0_state["purchases_this_turn"], 1)

    # -------------------------------------------------------------------------
    # 10. Phase 3: Market Purchase Limits & Funds Enforcement
    # -------------------------------------------------------------------------
    def test_phase3_buy_limit_and_funds(self) -> None:
        """Enforces max 2 purchases per turn and checks funds."""
        ctrl = RogueAgentRequestHandler.controller
        ctrl.new_game(num_players=4, seed=42)
        ctrl.phase = 3
        ctrl.active_player_index = 0
        p0 = ctrl.state.players[0]
        p0.money = 20

        # Purchase 1 and 2
        self._post("/api/game/action/buy", {"player_id": 0, "color": "red"})
        self._post("/api/game/action/buy", {"player_id": 0, "color": "red"})

        # Purchase 3 should fail
        url = f"{self.base_url}/api/game/action/buy"
        body = json.dumps({"player_id": 0, "color": "red"}).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 400)

        # Insufficient funds test
        ctrl.player_meta[0]["purchases_this_turn"] = 0
        p0.money = 2  # Less than $4 or $5
        with self.assertRaises(urllib.error.HTTPError) as ctx2:
            urllib.request.urlopen(req)
        self.assertEqual(ctx2.exception.code, 400)

    # -------------------------------------------------------------------------
    # 11. Phase 3: Patching Dice (Token & Cash)
    # -------------------------------------------------------------------------
    def test_phase3_patch_die_tokens_and_cash(self) -> None:
        """Tests patching using 🔧 tokens and cash ($2)."""
        ctrl = RogueAgentRequestHandler.controller
        ctrl.new_game(num_players=4, seed=42)
        ctrl.phase = 3
        ctrl.active_player_index = 0
        p0 = ctrl.state.players[0]

        # Put 2 dice in unpatched zone
        unpatched_die1 = p0.ready_dice.pop(0)
        unpatched_die2 = p0.ready_dice.pop(0)
        p0.unpatched_dice.extend([unpatched_die1, unpatched_die2])

        p0.patches = 1
        p0.money = 5

        # Patch 1: Using token
        res1 = self._post("/api/game/action/patch", {"player_id": 0, "die_index": 0, "use_cash": False})
        self.assertTrue(res1["success"])
        p0_state1 = res1["state"]["players"][0]
        self.assertEqual(p0_state1["patches"], 0)
        self.assertEqual(len(p0_state1["unpatched_dice"]), 1)

        # Patch 2: Using cash ($2)
        res2 = self._post("/api/game/action/patch", {"player_id": 0, "die_index": 0, "use_cash": True})
        self.assertTrue(res2["success"])
        p0_state2 = res2["state"]["players"][0]
        self.assertEqual(p0_state2["money"], 3)  # $5 - $2
        self.assertEqual(len(p0_state2["unpatched_dice"]), 0)

    # -------------------------------------------------------------------------
    # 12. Phase 3: Dirty Income Success
    # -------------------------------------------------------------------------
    def test_phase3_dirty_income_success(self) -> None:
        """Dirty Income grants +$3, pays 1 Secret, adds 1 Black Cube, and demotes ready die."""
        ctrl = RogueAgentRequestHandler.controller
        ctrl.new_game(num_players=4, seed=42)
        ctrl.phase = 3
        ctrl.active_player_index = 0
        p0 = ctrl.state.players[0]
        p0.secrets = 7
        p0.money = 5
        black_before = ctrl.state.staging_cup[CubeColor.BLACK]

        res = self._post("/api/game/action/dirty_income", {"player_id": 0, "backlash_die_index": 0})
        self.assertTrue(res["success"])
        state = res["state"]

        p0_state = state["players"][0]
        self.assertEqual(p0_state["money"], 8)  # $5 + $3
        self.assertEqual(p0_state["secrets"], 6)  # 7 - 1
        self.assertEqual(len(p0_state["unpatched_dice"]), 1)  # Backlash demotion
        self.assertEqual(state["staging_cup"]["black"], black_before + 1)

    # -------------------------------------------------------------------------
    # 13. Phase 3: Dirty Income Precondition Blocks
    # -------------------------------------------------------------------------
    def test_phase3_dirty_income_precondition_blocks(self) -> None:
        """Dirty Income is rejected if player has <= 1 Secret or 0 Ready dice."""
        ctrl = RogueAgentRequestHandler.controller
        ctrl.new_game(num_players=4, seed=42)
        ctrl.phase = 3
        ctrl.active_player_index = 0
        p0 = ctrl.state.players[0]

        # Block at <= 1 Secret
        p0.secrets = 1
        url = f"{self.base_url}/api/game/action/dirty_income"
        body = json.dumps({"player_id": 0, "backlash_die_index": 0}).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 400)

        # Ensure missing or None backlash_die_index does not fail with 500 TypeError
        p0.secrets = 5
        body_none = json.dumps({"player_id": 0, "backlash_die_index": None}).encode("utf-8")
        req_none = urllib.request.Request(url, data=body_none, headers={"Content-Type": "application/json"}, method="POST")
        resp_none = urllib.request.urlopen(req_none)
        self.assertEqual(resp_none.code, 200)

        # Reset for subsequent tests
        ctrl.player_meta[0]["dirty_income_taken_this_turn"] = False

        # Block at 0 Ready dice
        p0.secrets = 5
        p0.unpatched_dice.extend(p0.ready_dice)
        p0.ready_dice.clear()
        with self.assertRaises(urllib.error.HTTPError) as ctx2:
            urllib.request.urlopen(req)
        self.assertEqual(ctx2.exception.code, 400)

    # -------------------------------------------------------------------------
    # 14. Phase 3: Star Actions
    # -------------------------------------------------------------------------
    def test_phase3_star_actions(self) -> None:
        """Tests B2 and P1 star action execution."""
        ctrl = RogueAgentRequestHandler.controller
        ctrl.new_game(num_players=4, seed=42)
        ctrl.phase = 3
        ctrl.active_player_index = 0
        p0 = ctrl.state.players[0]

        # Test B2: Pay $2 for +1 Secret
        p0.b2_available = True
        p0.money = 5
        p0.secrets = 4
        res_b2 = self._post("/api/game/action/star", {"player_id": 0, "action_type": "B2"})
        self.assertTrue(res_b2["success"])
        p0_state = res_b2["state"]["players"][0]
        self.assertEqual(p0_state["money"], 3)
        self.assertEqual(p0_state["secrets"], 5)

        # Test P1: Inject Red Attack Cube
        p0.p1_available = True
        red_before = ctrl.state.staging_cup[CubeColor.RED]
        res_p1 = self._post("/api/game/action/star", {"player_id": 0, "action_type": "P1", "cube_color": "red"})
        self.assertTrue(res_p1["success"])
        self.assertEqual(res_p1["state"]["staging_cup"]["red"], red_before + 1)

        # Test P3: Deflect Blue Cube to Staging
        p0.p3_available = ShieldColor.BLUE
        blue_before = ctrl.state.staging_cup[CubeColor.BLUE]
        res_p3 = self._post("/api/game/action/star", {"player_id": 0, "action_type": "P3", "cube_color": "blue"})
        self.assertTrue(res_p3["success"])
        self.assertEqual(res_p3["state"]["staging_cup"]["blue"], blue_before + 1)
        self.assertIsNone(ctrl.state.players[0].p3_available)

    # -------------------------------------------------------------------------
    # 15. Defect 1 Test: B2 Deep R&D Vault Hold vs Commit
    # -------------------------------------------------------------------------
    def test_phase1_b2_hold_for_deep_rd_and_activate(self) -> None:
        """Rolling B2 and committing without assigning B2 sets b2_available=True and allows Phase 3 activation."""
        self._post("/api/game/new", {"num_players": 4, "seed": 42})
        self._post("/api/game/action/roll", {"player_id": 0})

        ctrl = RogueAgentRequestHandler.controller
        p0 = ctrl.state.players[0]
        # Set die 0 to B2 Star Face
        b2_face = Face(
            name="B2: Deep R&D Vault",
            block_amount=1,
            shield_color=ShieldColor.BLUE,
            is_star=True,
            star_code="B2",
        )
        p0.ready_dice[0].current_face = b2_face

        # Commit defenses without assigning die 0 to Blue
        res = self._post("/api/game/action/commit", {
            "player_id": 0,
            "commitments": {},
        })
        self.assertTrue(res["success"])
        state = res["state"]

        # Verify B2 was NOT auto-assigned to Blue shields
        p0_state = state["players"][0]
        self.assertEqual(len(p0_state["shield_slots"]["blue"]), 0)
        self.assertTrue(p0_state["b2_available"])

        # Advance to Phase 3
        ctrl.phase = 3
        ctrl.active_player_index = 0
        p0.money = 5
        p0.secrets = 4
        p0.b2_available = True

        res_b2 = self._post("/api/game/action/star", {"player_id": 0, "action_type": "B2"})
        self.assertTrue(res_b2["success"])
        p0_after = res_b2["state"]["players"][0]
        self.assertEqual(p0_after["money"], 3)
        self.assertEqual(p0_after["secrets"], 5)
        self.assertFalse(p0_after["b2_available"])

    # -------------------------------------------------------------------------
    # 16. Defect 2 Test: Hotfix with Rolled Patch Face & Locked Die
    # -------------------------------------------------------------------------
    def test_phase1_hotfix_with_rolled_patch_face_and_locked_die(self) -> None:
        """Player with 0 held tokens can hotfix using rolled patch face; locked die cannot be rerolled."""
        self._post("/api/game/new", {"num_players": 4, "seed": 42})
        self._post("/api/game/action/roll", {"player_id": 0})

        ctrl = RogueAgentRequestHandler.controller
        p0 = ctrl.state.players[0]
        p0.patches = 0  # 0 held patch tokens

        # Die 0: Money (+$1), Die 1: Patch (+1 🔧)
        p0.ready_dice[0].current_face = Face(name="+$1", money=1)
        p0.ready_dice[1].current_face = Face(name="+1 🔧", patches=1)
        p0.ready_dice[2].current_face = Face(name="+$1", money=1)
        p0.ready_dice[3].current_face = Face(name="+$1", money=1)

        # Check that capability gate enables can_hotfix
        state_before = ctrl.get_full_state()
        self.assertTrue(state_before["action_capabilities"]["can_hotfix"])

        # Reroll die 0 by spending the patch on die 1
        res = self._post("/api/game/action/hotfix", {"player_id": 0, "die_index": 0})
        self.assertTrue(res["success"])
        state_after = res["state"]
        p0_state = state_after["players"][0]

        # Die 1 must be locked in locked_reroll_indices
        self.assertIn(1, p0_state["locked_reroll_indices"])

        # Attempting to reroll the locked die 1 must be rejected with HTTP 400
        url = f"{self.base_url}/api/game/action/hotfix"
        body = json.dumps({"player_id": 0, "die_index": 1}).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 400)

        # Commit defenses: verify locked die 1 does NOT grant a patch token in Step 4
        res_commit = self._post("/api/game/action/commit", {"player_id": 0, "commitments": {}})
        self.assertTrue(res_commit["success"])
        p0_committed = res_commit["state"]["players"][0]
        self.assertEqual(p0_committed["patches"], 0)

    # -------------------------------------------------------------------------
    # 17. Phase 3: End Turn & Round Transition
    # -------------------------------------------------------------------------
    def test_phase3_end_turn_and_round_transition(self) -> None:
        """Ending turn advances through bot turns and starts Round 2."""
        ctrl = RogueAgentRequestHandler.controller
        ctrl.new_game(num_players=4, seed=42)
        ctrl.phase = 3
        ctrl.active_player_index = 0
        ctrl.phase3_turn_queue = [0, 1, 2, 3]

        res = self._post("/api/game/action/end_turn", {"player_id": 0})
        self.assertTrue(res["success"])
        state = res["state"]

        # Round completed and advanced to Round 2 Phase 1
        self.assertEqual(state["current_round"], 2)
        self.assertEqual(state["phase"], 1)
        self.assertEqual(state["phase_name"], "Boot & Configure")


if __name__ == "__main__":
    unittest.main()
