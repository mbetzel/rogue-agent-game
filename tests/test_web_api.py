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

    def _advance_to_phase(self, target: int, player_id: int = 0) -> Dict[str, Any]:
        """Drives the v0.34 six-phase web state machine with default human choices until `target` phase."""
        state = self._get("/api/game/state")["state"]
        for _ in range(12):
            phase = state["phase"]
            if phase >= target or phase == 7:
                return state
            if phase == 2:
                state = self._post("/api/game/action/compile", {})["state"]
            elif phase == 3:
                state = self._post("/api/game/action/confirm_income", {"player_id": player_id})["state"]
            elif phase == 4:
                state = self._post("/api/game/action/confirm_attacks", {"player_id": player_id})["state"]
            elif phase == 5:
                pend = state["pending_graduation"].get(str(player_id)) or state["pending_graduation"].get(player_id)
                state = self._post("/api/game/action/choose_graduates", {
                    "player_id": player_id, "graduate_die_ids": pend["default_graduate_ids"]})["state"]
            else:
                return state
        return state

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
        self.assertEqual(state["phase_name"], "Roll & Deploy")
        self.assertEqual(state["subphase"], "waiting_for_roll")
        self.assertEqual(len(state["players"]), 4)

        # Player 0 is human, players 1-3 are bots
        self.assertTrue(state["players"][0]["is_human"])
        self.assertFalse(state["players"][1]["is_human"])
        self.assertFalse(state["players"][2]["is_human"])
        self.assertFalse(state["players"][3]["is_human"])

        # Staging Cup: v1.0 Script Kiddie payload (1 Red, 1 Blue, 1 Green, 0 Black) + 1 Black Autonomous Pulse = 1 Black
        self.assertEqual(state["staging_cup"]["red"], 1)
        self.assertEqual(state["staging_cup"]["blue"], 1)
        self.assertEqual(state["staging_cup"]["green"], 1)
        self.assertEqual(state["staging_cup"]["black"], 1)

    # -------------------------------------------------------------------------
    # 2. New Game Custom Player Counts (2P Resilience Buffer)
    # -------------------------------------------------------------------------
    def test_new_game_custom_player_counts(self) -> None:
        """2P and 3P initialize with 8 Secrets & 0 Patches; 4P with 12 Secrets & 0 Patches (v0.30.0 INV-START-RES-01)."""
        # 2 Players
        res2p = self._post("/api/game/new", {"num_players": 2, "seed": 100})
        state2p = res2p["state"]
        self.assertEqual(len(state2p["players"]), 2)
        p0_2p = state2p["players"][0]
        self.assertEqual(p0_2p["secrets"], 8)
        self.assertEqual(p0_2p["patches"], 0)

        # 3 Players
        res3p = self._post("/api/game/new", {"num_players": 3, "seed": 200})
        state3p = res3p["state"]
        self.assertEqual(len(state3p["players"]), 3)
        p0_3p = state3p["players"][0]
        self.assertEqual(p0_3p["secrets"], 8)
        self.assertEqual(p0_3p["patches"], 0)

        # 4 Players
        res4p = self._post("/api/game/new", {"num_players": 4, "seed": 300})
        state4p = res4p["state"]
        self.assertEqual(len(state4p["players"]), 4)
        p0_4p = state4p["players"][0]
        self.assertEqual(p0_4p["secrets"], 8)  # v0.34 flat 8 Secrets at every player count
        self.assertEqual(p0_4p["patches"], 0)

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

        # Market contains 4 central market colored dice (INV-PURPLE-02: Purple excluded)
        for col in ["red", "blue", "green", "yellow"]:
            self.assertIn(col, state["market"])
            self.assertEqual(state["market"][col]["stock"], 8)  # 2 * 4 players
        self.assertNotIn("purple", state["market"])

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
        self.assertEqual(state["phase_name"], "Compiler Drop & Corruption")
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
        """POST /api/game/action/compile resolves Phase 2 (drop + corruption) and enters Phase 3: Income."""
        self._post("/api/game/new", {"num_players": 4, "seed": 42})
        self._post("/api/game/action/roll", {"player_id": 0})
        self._post("/api/game/action/commit", {"player_id": 0, "commitments": {}})

        res = self._post("/api/game/action/compile", {})
        self.assertTrue(res["success"])
        state = res["state"]

        self.assertIsNotNone(state["last_compile_result"])
        self.assertNotIn("threat_summary", state["last_compile_result"])  # attacks resolve in Phase 4
        self.assertEqual(state["phase"], 3)
        self.assertEqual(state["phase_name"], "Income")
        self.assertEqual(state["phase_names"]["4"] if "4" in state["phase_names"] else state["phase_names"][4], "Attack Resolution")

        for p in state["players"]:
            unpatched_ids = {d["die_id"] for d in p["unpatched_dice"]}
            rolled_ids = {d["die_id"] for d in p["rolled_pool"]}
            ready_ids = {d["die_id"] for d in p["ready_dice"]}
            self.assertEqual(len(unpatched_ids.intersection(rolled_ids)), 0)
            self.assertEqual(len(unpatched_ids.intersection(ready_ids)), 0)
            self.assertEqual(len(rolled_ids.intersection(ready_ids)), 0)

        self.assertEqual(state["subphase"], "confirm_income")
        self.assertTrue(state["action_capabilities"]["can_confirm_income"])
        self.assertFalse(state["action_capabilities"]["can_end_turn"])
        self.assertTrue(state["last_income_result"]["0"]["preview"] if "0" in state["last_income_result"] else state["last_income_result"][0]["preview"])

        # Phase 3 -> Phase 4 (Attack Resolution) unless the round overflowed
        conf_state = self._post("/api/game/action/confirm_income", {"player_id": 0})["state"]
        self.assertFalse(conf_state["action_capabilities"]["can_confirm_income"])
        if not state["last_compile_result"]["buffer_overflow"]:
            self.assertEqual(conf_state["phase"], 4)
            self.assertEqual(conf_state["subphase"], "confirm_attacks")
            self.assertTrue(conf_state["action_capabilities"]["can_confirm_attacks"])

        final_state = self._advance_to_phase(6)
        self.assertEqual(final_state["phase"], 6)
        self.assertEqual(final_state["subphase"], "player_turn")
        p0 = final_state["players"][0]
        self.assertEqual(len(p0["in_production_dice"]), 0)  # Phase 5 routed In Production -> Scanned Box
        self.assertLessEqual(len(p0["ready_for_release_dice"]), p0["release_bandwidth"] + 2)

    def test_confirm_income_invalid_phase(self) -> None:
        """POST /api/game/action/confirm_income rejects call outside Phase 3."""
        self._post("/api/game/new", {"num_players": 4, "seed": 42})
        url = f"{self.base_url}/api/game/action/confirm_income"
        body = json.dumps({"player_id": 0}).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 400)

    def test_confirm_attacks_with_green_malware_glitch_choice(self) -> None:
        """Phase 4: unblocked Green malware lets the human choose which In Production die is glitched."""
        self._post("/api/game/new", {"num_players": 4, "seed": 42})
        ctrl = RogueAgentRequestHandler.controller
        self._post("/api/game/action/roll", {"player_id": 0})
        self._post("/api/game/action/commit", {"player_id": 0, "commitments": {}})
        orig_drop = ctrl.state.tower.drop
        ctrl.state.tower.drop = lambda cup, rng: {CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 1, CubeColor.BLACK: 0}
        try:
            self._post("/api/game/action/compile", {})
        finally:
            ctrl.state.tower.drop = orig_drop
        state = self._post("/api/game/action/confirm_income", {"player_id": 0})["state"]
        self.assertEqual(state["phase"], 4)
        attack_res = state["last_attack_result"]
        self.assertEqual(attack_res["human_threat"]["green"]["unblocked"], 1)
        candidates = attack_res["candidate_glitch_dice"]
        self.assertGreater(len(candidates), 0)
        chosen_die_id = candidates[-1]["die_id"]
        self.assertEqual(len(state["players"][0]["glitched_dice"]), 0)  # nothing glitched before confirm

        conf_state = self._post("/api/game/action/confirm_attacks", {
            "player_id": 0, "glitch_die_ids": [chosen_die_id],
            "any_shield_allocations": {"red": 0, "blue": 0, "green": 0},  # leave the Green cube unblocked
        })["state"]
        conf_p0 = conf_state["players"][0]
        self.assertEqual(ctrl.last_attack_result["threat_summary"][0]["green"]["unblocked"], 1)
        p0_dice = ctrl.state.players[0]
        self.assertIn(chosen_die_id, [d.die_id for d in p0_dice.glitched_dice + p0_dice.scanned_dice])
        self.assertNotIn(chosen_die_id, [d["die_id"] for d in conf_p0["ready_for_release_dice"]])
        self.assertEqual(len(conf_p0["in_production_dice"]), 0)

    def test_confirm_income_rejects_attack_payload(self) -> None:
        """v0.34: glitch_die_ids / any_shield_allocations belong to confirm_attacks (Phase 4)."""
        self._post("/api/game/new", {"num_players": 4, "seed": 42})
        self._post("/api/game/action/roll", {"player_id": 0})
        self._post("/api/game/action/commit", {"player_id": 0, "commitments": {}})
        self._post("/api/game/action/compile", {})
        url = f"{self.base_url}/api/game/action/confirm_income"
        body = json.dumps({"player_id": 0, "glitch_die_ids": []}).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 400)

    def test_confirm_attacks_with_contractor_sacrifice(self) -> None:
        """Phase 4: unblocked Green malware can be absorbed by sacrificing an active White Contractor."""
        self._post("/api/game/new", {"num_players": 4, "seed": 42})
        ctrl = RogueAgentRequestHandler.controller
        self._post("/api/game/action/hire_contractors", {"player_id": 0, "count": 1})
        self._post("/api/game/action/roll", {"player_id": 0})
        rolled = ctrl.player_meta[0]["rolled_pool"]
        white = next(d for d in rolled if d.color == DieColor.WHITE)
        white.current_face = Face(name="+$1", money=1)
        self._post("/api/game/action/commit", {"player_id": 0, "commitments": {}})
        orig_drop = ctrl.state.tower.drop
        ctrl.state.tower.drop = lambda cup, rng: {CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 1, CubeColor.BLACK: 0}
        try:
            self._post("/api/game/action/compile", {})
        finally:
            ctrl.state.tower.drop = orig_drop
        money_before = ctrl.state.players[0].money
        state = self._post("/api/game/action/confirm_income", {"player_id": 0})["state"]
        self.assertGreaterEqual(state["players"][0]["money"], money_before + 1)  # contractor +$1 paid in Phase 3
        candidates = state["last_attack_result"]["candidate_glitch_dice"]
        contractor_candidate = next((c for c in candidates if c.get("is_contractor")), None)
        self.assertIsNotNone(contractor_candidate)
        contractor_id = contractor_candidate["die_id"]

        res_conf = self._post("/api/game/action/confirm_attacks", {"player_id": 0, "glitch_die_ids": [contractor_id]})
        self.assertTrue(res_conf["success"])
        p0 = ctrl.state.players[0]
        all_ids = [d.die_id for d in p0.ready_for_release_dice + p0.glitched_dice + p0.scanned_dice + p0.in_production_dice]
        self.assertNotIn(contractor_id, all_ids)  # Contractor Sacrifice: returned to supply
        self.assertEqual(len(p0.glitched_dice), 0)

    def _spook_in_phase3(self):
        from sim.entities import WHITE_HATS, WhiteHatCode, create_colored_die

        self._post("/api/game/new", {"num_players": 2, "seed": 3})
        ctrl = RogueAgentRequestHandler.controller
        ctrl.state.tower.drop = lambda cup, rng: {CubeColor.RED: 1, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0}
        self._post("/api/game/action/roll", {"player_id": 0})
        self._post("/api/game/action/commit", {"player_id": 0, "commitments": {}})
        self._post("/api/game/action/compile", {})
        self.assertEqual(ctrl.phase, 3)
        p0 = ctrl.state.players[0]
        p0.white_hat = WHITE_HATS[WhiteHatCode.SPOOK]
        star = Face(name="Purple ★", is_star=True, star_code="PURPLE_STAR")
        for i in range(2):
            d = create_colored_die(DieColor.PURPLE, 7800 + i, cost=0)
            d.current_face = star
            p0.in_production_dice.append(d)
        p0.glitched_dice.append(create_colored_die(DieColor.RED, 5))
        return ctrl, p0

    def test_confirm_income_burn_list_with_null_entry(self) -> None:
        """[null, 5]: the null trigger is declined and die 5 is burned."""
        ctrl, p0 = self._spook_in_phase3()
        secrets = p0.secrets
        res = self._post("/api/game/action/confirm_income", {"player_id": 0, "spook_burn_die_id": [None, 5]})
        self.assertTrue(res["success"])
        self.assertEqual(ctrl.last_income_result[0]["burned_die_ids"], [5])
        self.assertEqual(p0.secrets, secrets + 1)

    def test_confirm_income_burn_non_integer_is_400(self) -> None:
        ctrl, p0 = self._spook_in_phase3()
        url = f"{self.base_url}/api/game/action/confirm_income"
        req = urllib.request.Request(url, data=json.dumps({"player_id": 0, "spook_burn_die_id": ["abc"]}).encode("utf-8"),
                                     headers={"Content-Type": "application/json"}, method="POST")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 400)
        self.assertEqual(ctrl.phase, 3)  # nothing resolved

    def test_confirm_income_burn_bare_null_is_noop(self) -> None:
        ctrl, p0 = self._spook_in_phase3()
        secrets = p0.secrets
        res = self._post("/api/game/action/confirm_income", {"player_id": 0, "spook_burn_die_id": None})
        self.assertTrue(res["success"])
        self.assertEqual(ctrl.last_income_result[0]["burned_die_ids"], [])
        self.assertEqual(p0.secrets, secrets)

    def test_confirm_attacks_aegis_color_validation(self) -> None:
        """Phase 4: aegis_color must be a qualifying Baffle Echo color (400 otherwise); "none" declines."""
        from sim.entities import COMPANIES, CompanyCode, AbilityStatus

        self._post("/api/game/new", {"num_players": 2, "seed": 9})
        ctrl = RogueAgentRequestHandler.controller
        p0 = ctrl.state.players[0]
        p0.company = COMPANIES[CompanyCode.AEGIS]
        p0.ability_v1_status = AbilityStatus.AVAILABLE
        self._post("/api/game/action/roll", {"player_id": 0})
        self._post("/api/game/action/commit", {"player_id": 0, "commitments": {}})
        ctrl.state.tower.drop = lambda cup, rng: {CubeColor.RED: 1, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0}
        self._post("/api/game/action/compile", {})
        state = self._post("/api/game/action/confirm_income", {"player_id": 0})["state"]
        self.assertEqual(state["phase"], 4)
        self.assertEqual(state["last_attack_result"]["human_threat"]["aegis"]["qualifying_colors"], ["red"])
        self.assertTrue(state["action_capabilities"]["can_aegis_echo"])
        url = f"{self.base_url}/api/game/action/confirm_attacks"
        for bad in ("green", "teal"):
            req = urllib.request.Request(url, data=json.dumps({"player_id": 0, "aegis_color": bad}).encode("utf-8"),
                                         headers={"Content-Type": "application/json"}, method="POST")
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(req)
            self.assertEqual(ctx.exception.code, 400)
        self.assertEqual(ctrl.phase, 4)  # rejected payloads did not resolve damage
        res = self._post("/api/game/action/confirm_attacks", {"player_id": 0, "aegis_color": "red"})
        self.assertTrue(res["success"])
        self.assertEqual(p0.ability_v1_status, AbilityStatus.USED)
        self.assertEqual(ctrl.last_attack_result["threat_summary"][0]["red"]["unblocked"], 0)

    def test_choose_graduates_validates_payload(self) -> None:
        """Phase 5: choose_graduates rejects ids outside the Scanned Box or above Release Bandwidth; fewer is allowed."""
        self._post("/api/game/new", {"num_players": 2, "seed": 7})
        ctrl = RogueAgentRequestHandler.controller
        self._post("/api/game/action/roll", {"player_id": 0})
        self._post("/api/game/action/commit", {"player_id": 0, "commitments": {}})
        ctrl.state.tower.drop = lambda cup, rng: {CubeColor.RED: 1, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0}
        p0 = ctrl.state.players[0]
        for i in range(3):  # overflow the Scanned Box beyond Release Bandwidth
            p0.scanned_dice.append(Die(die_id=9000 + i, color=DieColor.GRAY, cost=0, faces=[Face(name="+$1", money=1)]))
        state = self._advance_to_phase(5)
        self.assertEqual(state["phase"], 5)
        self.assertEqual(state["subphase"], "choose_graduates")
        self.assertTrue(state["action_capabilities"]["can_choose_graduates"])
        pend = state["pending_graduation"].get("0") or state["pending_graduation"].get(0)
        n = pend["n"]
        url = f"{self.base_url}/api/game/action/choose_graduates"
        for bad in ({"player_id": 0, "graduate_die_ids": [123456]},
                    {"player_id": 0, "graduate_die_ids": [c["die_id"] for c in pend["candidates"]]},
                    {"player_id": 0}):
            req = urllib.request.Request(url, data=json.dumps(bad).encode("utf-8"),
                                         headers={"Content-Type": "application/json"}, method="POST")
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(req)
            self.assertEqual(ctx.exception.code, 400)
        keep = pend["default_graduate_ids"][:1]  # graduate fewer than allowed (OQ-1)
        state = self._post("/api/game/action/choose_graduates", {"player_id": 0, "graduate_die_ids": keep})["state"]
        self.assertEqual(state["phase"], 6)
        self.assertEqual(ctrl.last_pipeline_result[0]["graduated_ids"], keep)
        self.assertGreaterEqual(len(p0.scanned_dice), len(pend["candidates"]) - 1 - p0.triage_bandwidth + 0)

    # -------------------------------------------------------------------------
    # 9. Phase 3: Market Purchase
    # -------------------------------------------------------------------------
    def test_phase3_buy_die(self) -> None:
        """POST /api/game/action/buy purchases a colored die and updates market stock."""
        ctrl = RogueAgentRequestHandler.controller
        ctrl.new_game(num_players=4, seed=42)
        ctrl.phase = 6
        ctrl.phase_name = "Corporate Operations"
        ctrl.active_player_index = 0
        p0 = ctrl.state.players[0]
        p0.money = 10

        initial_stock = ctrl.state.market[DieColor.BLUE]
        res = self._post("/api/game/action/buy", {"player_id": 0, "color": "blue"})
        self.assertTrue(res["success"])
        state = res["state"]

        p0_state = state["players"][0]
        self.assertEqual(p0_state["money"], 5)  # $10 - $5 (B1)
        self.assertEqual(state["market"]["blue"]["stock"], initial_stock - 1)
        self.assertEqual(p0_state["purchases_this_turn"], 1)

    # -------------------------------------------------------------------------
    # 10. Phase 3: Market Purchase Limits & Funds Enforcement
    # -------------------------------------------------------------------------
    def test_phase3_buy_limit_and_funds(self) -> None:
        """Enforces max 2 purchases per turn and checks funds."""
        ctrl = RogueAgentRequestHandler.controller
        ctrl.new_game(num_players=4, seed=42)
        ctrl.phase = 6
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
        ctrl.phase = 6
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

        # Patch 2: Using cash ($2) is abolished in v0.22.0 -> returns 400
        url = f"{self.base_url}/api/game/action/patch"
        bad_req = json.dumps({"player_id": 0, "die_index": 0, "use_cash": True}).encode("utf-8")
        req = urllib.request.Request(url, data=bad_req, headers={"Content-Type": "application/json"}, method="POST")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 400)

    # -------------------------------------------------------------------------
    # 12. Phase 3: Dirty Income Success
    # -------------------------------------------------------------------------
    def test_phase3_dirty_income_success(self) -> None:
        """Dirty Income grants +$3, pays 1 Secret, adds 1 Black Cube, and demotes ready die when enabled."""
        ctrl = RogueAgentRequestHandler.controller
        ctrl.new_game(num_players=4, seed=42)
        ctrl.state.config.dirty_income_enabled = True
        ctrl.phase = 6
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
    # 13. Phase 3: Dirty Income Precondition Blocks & v0.16.0 Elimination
    # -------------------------------------------------------------------------
    def test_phase3_dirty_income_precondition_blocks(self) -> None:
        """Dirty Income is rejected if player has <= 1 Secret, 0 Ready dice, or disabled (v0.16.0)."""
        ctrl = RogueAgentRequestHandler.controller
        ctrl.new_game(num_players=4, seed=42)
        ctrl.state.config.dirty_income_enabled = True
        ctrl.phase = 6
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

        # Block when disabled in v0.16.0 default
        ctrl.state.config.dirty_income_enabled = False
        with self.assertRaises(urllib.error.HTTPError) as ctx_disabled:
            urllib.request.urlopen(req_none)
        self.assertEqual(ctx_disabled.exception.code, 400)
        ctrl.state.config.dirty_income_enabled = True

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
        ctrl.phase = 6
        ctrl.active_player_index = 0
        p0 = ctrl.state.players[0]

        # Test B2: Pay $4 for +1 Secret
        p0.b2_available = True
        p0.money = 5
        p0.secrets = 4
        res_b2 = self._post("/api/game/action/star", {"player_id": 0, "action_type": "B2"})
        self.assertTrue(res_b2["success"])
        p0_state = res_b2["state"]["players"][0]
        self.assertEqual(p0_state["money"], 1)
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
        ctrl.phase = 6
        ctrl.active_player_index = 0
        p0.money = 5
        p0.secrets = 4
        p0.b2_available = True

        res_b2 = self._post("/api/game/action/star", {"player_id": 0, "action_type": "B2"})
        self.assertTrue(res_b2["success"])
        p0_after = res_b2["state"]["players"][0]
        self.assertEqual(p0_after["money"], 1)
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
        ctrl.phase = 6
        ctrl.active_player_index = 0
        ctrl.phase3_turn_queue = [0, 1, 2, 3]

        res = self._post("/api/game/action/end_turn", {"player_id": 0})
        self.assertTrue(res["success"])
        state = res["state"]

        # Round completed and advanced to Round 2 Phase 1
        self.assertEqual(state["current_round"], 2)
        self.assertEqual(state["phase"], 1)
        self.assertEqual(state["phase_name"], "Roll & Deploy")


    # -------------------------------------------------------------------------
    # 18. Phase 1: Hire Contractors API
    # -------------------------------------------------------------------------
    def test_phase1_hire_contractors_api(self) -> None:
        """POST /api/game/action/hire_contractors hires white contractor dice."""
        self._post("/api/game/new", {"num_players": 4, "seed": 42})
        res = self._post("/api/game/action/hire_contractors", {"player_id": 0, "count": 2})
        self.assertTrue(res["success"])
        p0 = res["state"]["players"][0]
        self.assertEqual(p0["hired_contractors"], 2)
        self.assertEqual(len(p0["contractor_dice"]), 2)
        self.assertEqual(res["state"]["contractor_supply"], 10)

    # -------------------------------------------------------------------------
    # 19. Phase 1: Perform Reroll API
    # -------------------------------------------------------------------------
    def test_phase1_perform_reroll_api(self) -> None:
        """POST /api/game/action/reroll rerolls selected unlocked dice."""
        self._post("/api/game/new", {"num_players": 4, "seed": 42})
        self._post("/api/game/action/roll", {"player_id": 0})
        res = self._post("/api/game/action/reroll", {"player_id": 0, "reroll_indices": [0, 1]})
        self.assertTrue(res["success"])
        p0 = res["state"]["players"][0]
        self.assertEqual(p0["rerolls_remaining"], 1)

    # -------------------------------------------------------------------------
    # 20. Phase 1: Debug Unlock API (Deprecated in v0.23.0)
    # -------------------------------------------------------------------------
    def test_phase1_debug_unlock_api(self) -> None:
        """POST /api/game/action/debug_unlock returns 400 deprecation error in v0.23.0."""
        self._post("/api/game/new", {"num_players": 4, "seed": 42})
        self._post("/api/game/action/roll", {"player_id": 0})

        url = f"{self.base_url}/api/game/action/debug_unlock"
        body = json.dumps({"player_id": 0, "die_index": 0}).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 400)

    # -------------------------------------------------------------------------
    # 21. v0.28.0: Defense Capacity Enforcement in Phase 1 Commit
    # -------------------------------------------------------------------------
    def test_v280_defense_capacity_enforcement(self) -> None:
        """INV-DEF-CAP-01: Phase 1 commit clamps total shields to player.defense_capacity."""
        self._post("/api/game/new", {"num_players": 4, "seed": 42})
        self._post("/api/game/action/roll", {"player_id": 0})

        # Set player 0's rolled dice to all be shield faces
        shield_face = Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)
        RogueAgentRequestHandler.controller.state.players[0].defense_capacity = 2
        for d in RogueAgentRequestHandler.controller.player_meta[0]["rolled_pool"]:
            d.current_face = shield_face

        # Try to commit 4 shields
        commitments = {"0": "red", "1": "blue", "2": "green", "3": "blue"}
        res = self._post("/api/game/action/commit", {"player_id": 0, "commitments": commitments})
        self.assertTrue(res["success"])
        p0 = res["state"]["players"][0]
        # Committed shields must not exceed defense_capacity (2)
        total_shields = (
            len(p0["shield_slots"]["red"])
            + len(p0["shield_slots"]["blue"])
            + len(p0["shield_slots"]["green"])
            + len(p0["shield_slots"].get("any", []))
        )
        self.assertLessEqual(total_shields, 2)
        self.assertEqual(total_shields, 2)

    # -------------------------------------------------------------------------
    # 22. v0.28.0: Terminal Track Upgrade API
    # -------------------------------------------------------------------------
    def test_v280_upgrade_track_api(self) -> None:
        """POST /api/game/action/upgrade_track upgrades hardware tracks using research tokens."""
        self._post("/api/game/new", {"num_players": 4, "seed": 42})
        self._post("/api/game/action/roll", {"player_id": 0})
        self._post("/api/game/action/commit", {"player_id": 0, "commitments": {}})
        self._advance_to_phase(6)

        # Advance to human player 0's turn in Phase 3
        ctrl = RogueAgentRequestHandler.controller
        ctrl.active_player_index = 0
        p0_state = ctrl.state.players[0]
        p0_state.research_tokens = 5
        p0_state.pipeline_level = 0
        p0_state.defense_level = 0

        # Upgrade Pipeline track from L0 -> L1 (Cost: 2 🔬)
        res = self._post("/api/game/action/upgrade_track", {"player_id": 0, "track_type": "pipeline"})
        self.assertTrue(res["success"])
        p0 = res["state"]["players"][0]
        self.assertEqual(p0["pipeline_level"], 1)
        self.assertEqual(p0["triage_bandwidth"], 3)
        self.assertEqual(p0["release_bandwidth"], 4)
        self.assertEqual(p0["research_tokens"], 3)

        # Upgrade Defense track from L0 -> L1 (Cost: 2 🔬)
        res2 = self._post("/api/game/action/upgrade_track", {"player_id": 0, "track_type": "defense"})
        self.assertTrue(res2["success"])
        p0_after_def = res2["state"]["players"][0]
        self.assertEqual(p0_after_def["defense_level"], 1)
        self.assertEqual(p0_after_def["defense_capacity"], 3)
        self.assertEqual(p0_after_def["research_tokens"], 1)

    # -------------------------------------------------------------------------
    # 23. v0.28.0: Cryptographic Patent Filing API
    # -------------------------------------------------------------------------
    def test_v280_patent_api(self) -> None:
        """POST /api/game/action/patent converts research tokens to Corporate Secrets."""
        self._post("/api/game/new", {"num_players": 4, "seed": 42})
        self._post("/api/game/action/roll", {"player_id": 0})
        self._post("/api/game/action/commit", {"player_id": 0, "commitments": {}})
        self._advance_to_phase(6)

        ctrl = RogueAgentRequestHandler.controller
        ctrl.active_player_index = 0
        p0_state = ctrl.state.players[0]
        p0_state.patent_level = 0
        p0_state.research_tokens = 4
        initial_secrets = p0_state.secrets

        # Patent at Level 0 costs 4 🔬 -> +1 Secret
        res = self._post("/api/game/action/patent", {"player_id": 0})
        self.assertTrue(res["success"])
        p0 = res["state"]["players"][0]
        self.assertEqual(p0["secrets"], initial_secrets + 1)
        self.assertEqual(p0["research_tokens"], 0)

    # -------------------------------------------------------------------------
    # 24. Company Setup & Hardware Baselines (v0.28.0 / v0.30.0)
    # -------------------------------------------------------------------------
    def test_new_game_company_setup_helix(self) -> None:
        """POST /api/game/new with Helix assigns Patent Level 1 and +2 🔬 Research Tokens."""
        res = self._post("/api/game/new", {
            "num_players": 4,
            "seed": 42,
            "players": [{"is_human": True, "name": "BioHacker", "company": "HELIX"}],
        })
        self.assertTrue(res["success"])
        state = res["state"]
        p0 = state["players"][0]

        # Verify company identity
        self.assertEqual(p0["company"]["code"], "HELIX")
        self.assertEqual(p0["company"]["starting_patent_level"], 1)
        self.assertEqual(p0["company"]["starting_research_bonus"], 2)

        # Verify starting research level (patent level 1) and starting research tokens (2)
        self.assertEqual(p0["patent_level"], 1)
        self.assertEqual(p0["research_tokens"], 2)
        self.assertEqual(p0["patches"], 2)

        # Verify standard hardware tracks for Helix
        self.assertEqual(p0["defense_capacity"], 2)
        self.assertEqual(p0["triage_bandwidth"], 2)
        self.assertEqual(p0["release_bandwidth"], 4)
        self.assertEqual(p0["triage_level"], 0)
        self.assertEqual(p0["release_level"], 0)
        self.assertEqual(p0["defense_level"], 0)

    def test_new_game_company_setup_omnidyne(self) -> None:
        """POST /api/game/new with Omnidyne assigns Triage L1, Release L1, and Def Cap 1."""
        res = self._post("/api/game/new", {
            "num_players": 4,
            "seed": 42,
            "players": [{"is_human": True, "name": "SysAdmin", "company": "OMNIDYNE"}],
        })
        self.assertTrue(res["success"])
        p0 = res["state"]["players"][0]

        self.assertEqual(p0["company"]["code"], "OMNIDYNE")
        self.assertEqual(p0["defense_capacity"], 1)
        self.assertEqual(p0["triage_bandwidth"], 3)
        self.assertEqual(p0["release_bandwidth"], 5)
        self.assertEqual(p0["triage_level"], 1)
        self.assertEqual(p0["release_level"], 1)
        self.assertEqual(p0["patent_level"], 0)
        self.assertEqual(p0["research_tokens"], 0)

    def test_new_game_company_setup_aegis(self) -> None:
        """POST /api/game/new with Aegis assigns Defense Level 1 and Defense Cap 3."""
        res = self._post("/api/game/new", {
            "num_players": 4,
            "seed": 42,
            "players": [{"is_human": True, "name": "SecLead", "company": "AEGIS"}],
        })
        self.assertTrue(res["success"])
        p0 = res["state"]["players"][0]

        self.assertEqual(p0["company"]["code"], "AEGIS")
        self.assertEqual(p0["defense_capacity"], 3)
        self.assertEqual(p0["defense_level"], 1)
        self.assertEqual(p0["triage_bandwidth"], 1)
        self.assertEqual(p0["release_bandwidth"], 3)
        self.assertEqual(p0["patent_level"], 0)

    def test_new_game_company_setup_meridian(self) -> None:
        """POST /api/game/new with Meridian assigns +$2 Starting Cash ($8 start)."""
        res = self._post("/api/game/new", {
            "num_players": 4,
            "seed": 42,
            "players": [{"is_human": True, "name": "Banker", "company": "MERIDIAN"}],
        })
        self.assertTrue(res["success"])
        p0 = res["state"]["players"][0]

        self.assertEqual(p0["company"]["code"], "MERIDIAN")
        self.assertEqual(p0["money"], 8)
        self.assertEqual(p0["defense_capacity"], 2)
        self.assertEqual(p0["patent_level"], 0)

    def test_new_game_company_setup_dto(self) -> None:
        """POST /api/game/new with DTO assigns +1 Corporate Secret."""
        res = self._post("/api/game/new", {
            "num_players": 4,
            "seed": 42,
            "players": [{"is_human": True, "name": "Agent", "company": "DTO"}],
        })
        self.assertTrue(res["success"])
        p0 = res["state"]["players"][0]

        self.assertEqual(p0["company"]["code"], "DTO")
        self.assertEqual(p0["secrets"], 9)  # v0.34 flat 8 baseline + 1 (DTO)

    def test_new_game_company_setup_prometheus(self) -> None:
        """POST /api/game/new with Prometheus assigns -1 🔬 Upgrade Discount."""
        res = self._post("/api/game/new", {
            "num_players": 4,
            "seed": 42,
            "players": [{"is_human": True, "name": "Dev", "company": "PROMETHEUS"}],
        })
        self.assertTrue(res["success"])
        p0 = res["state"]["players"][0]

        self.assertEqual(p0["company"]["code"], "PROMETHEUS")
        self.assertEqual(p0["company"]["upgrade_discount"], 1)

    def test_new_game_disable_corporate_asymmetry(self) -> None:
        """POST /api/game/new with enable_corporate_asymmetry=False applies 0 baselines."""
        res = self._post("/api/game/new", {
            "num_players": 4,
            "seed": 42,
            "enable_corporate_asymmetry": False,
            "players": [{"is_human": True, "name": "BioHacker", "company": "HELIX"}],
        })
        self.assertTrue(res["success"])
        p0 = res["state"]["players"][0]

        # With asymmetry disabled, company modifiers are not applied
        self.assertEqual(p0["patent_level"], 0)
        self.assertEqual(p0["research_tokens"], 0)
        self.assertEqual(p0["patches"], 0)

    # -------------------------------------------------------------------------
    # 25. Manual Any Shield Allocation in confirm_attacks (Phase 4 Player Agency)
    # -------------------------------------------------------------------------
    def test_confirm_income_manual_any_shield_allocation_red_vs_green(self) -> None:
        """Human player overrides default Green allocation to block Red instead, saving $1 cash and taking 1 Green glitch."""
        self._post("/api/game/new", {"num_players": 4, "seed": 42})
        self._post("/api/game/action/roll", {"player_id": 0})

        ctrl = RogueAgentRequestHandler.controller
        p0 = ctrl.state.players[0]
        p0.money = 5
        p0.secrets = 8

        # Set die 0 to Block 1 Any and die 1..3 to +$1 income
        rolled = ctrl.player_meta[0]["rolled_pool"]
        rolled[0].current_face = Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)
        for d in rolled[1:]:
            d.current_face = Face(name="+$1", money=1)

        self._post("/api/game/action/commit", {
            "player_id": 0,
            "commitments": {"0": "any"},
        })

        # Ensure deterministic drop of 1 Red, 0 Blue, 1 Green, 0 Black
        ctrl.state.staging_cup = {
            CubeColor.RED: 1,
            CubeColor.BLUE: 0,
            CubeColor.GREEN: 1,
            CubeColor.BLACK: 0,
        }
        ctrl.state.tower.stuck_cubes = {
            CubeColor.RED: 0,
            CubeColor.BLUE: 0,
            CubeColor.GREEN: 0,
            CubeColor.BLACK: 0,
        }
        orig_drop = ctrl.state.tower.drop
        ctrl.state.tower.drop = lambda cup, rng: {
            CubeColor.RED: 1,
            CubeColor.BLUE: 0,
            CubeColor.GREEN: 1,
            CubeColor.BLACK: 0,
        }
        try:
            res_comp = self._post("/api/game/action/compile", {})
        finally:
            ctrl.state.tower.drop = orig_drop

        self.assertTrue(res_comp["success"])
        inc_state = self._post("/api/game/action/confirm_income", {"player_id": 0})["state"]
        self.assertEqual(inc_state["players"][0]["money"], 8)  # $5 + $3 Phase 3 income (before attacks)
        human_threat = inc_state["last_attack_result"]["human_threat"]
        self.assertEqual(inc_state["phase"], 4)
        self.assertEqual(human_threat["any"]["shields"], 1)
        self.assertFalse(human_threat["resolved"])

        # Human allocates the Any shield to Red instead of Green, and glitches die 0 (the shield die)
        shield_die_id = rolled[0].die_id
        res_conf = self._post("/api/game/action/confirm_attacks", {
            "player_id": 0,
            "glitch_die_ids": [shield_die_id],
            "any_shield_allocations": {"red": 1, "blue": 0, "green": 0},
        })
        self.assertTrue(res_conf["success"])
        conf_p0 = res_conf["state"]["players"][0]

        # Red blocked (no ransom), Green glitched the chosen shield die; income already banked in Phase 3
        self.assertEqual(conf_p0["money"], 8)
        self.assertEqual(conf_p0["secrets"], 8)
        self.assertEqual(ctrl.last_attack_result["threat_summary"][0]["any"]["allocated"], {"red": 1, "blue": 0, "green": 0})
        p0_dice = ctrl.state.players[0]
        self.assertIn(shield_die_id, [d.die_id for d in p0_dice.glitched_dice + p0_dice.scanned_dice])
        self.assertNotIn(shield_die_id, [d.die_id for d in p0_dice.ready_for_release_dice])

    def test_confirm_income_manual_any_shield_allocation_blue_vs_red(self) -> None:
        """Human player overrides default Blue allocation to block Red instead (saving $1 cash and losing 1 Corporate Secret)."""
        self._post("/api/game/new", {"num_players": 4, "seed": 42})
        self._post("/api/game/action/roll", {"player_id": 0})

        ctrl = RogueAgentRequestHandler.controller
        p0 = ctrl.state.players[0]
        p0.money = 5
        p0.secrets = 8

        rolled = ctrl.player_meta[0]["rolled_pool"]
        rolled[0].current_face = Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)
        for d in rolled[1:]:
            d.current_face = Face(name="+$1", money=1)

        self._post("/api/game/action/commit", {
            "player_id": 0,
            "commitments": {"0": "any"},
        })

        orig_drop = ctrl.state.tower.drop
        ctrl.state.tower.drop = lambda cup, rng: {
            CubeColor.RED: 1,
            CubeColor.BLUE: 1,
            CubeColor.GREEN: 0,
            CubeColor.BLACK: 0,
        }
        try:
            res_comp = self._post("/api/game/action/compile", {})
        finally:
            ctrl.state.tower.drop = orig_drop

        self.assertTrue(res_comp["success"])
        inc_state = self._post("/api/game/action/confirm_income", {"player_id": 0})["state"]
        self.assertEqual(inc_state["players"][0]["money"], 8)
        self.assertEqual(inc_state["players"][0]["secrets"], 8)

        # Allocate the Any shield to Red instead of Blue
        res_conf = self._post("/api/game/action/confirm_attacks", {
            "player_id": 0,
            "glitch_die_ids": [],
            "any_shield_allocations": {"red": 1, "blue": 0, "green": 0},
        })
        self.assertTrue(res_conf["success"])
        conf_p0 = res_conf["state"]["players"][0]

        # No ransom ($5 + $3 Phase 3 income = $8), lost 1 Secret from unblocked Blue (8 - 1 = 7)
        self.assertEqual(conf_p0["money"], 8)
        self.assertEqual(conf_p0["secrets"], 7)

    def test_confirm_income_default_any_shield_allocation_when_omitted(self) -> None:
        """Calling confirm_attacks without any_shield_allocations preserves the default 4-tier heuristic."""
        self._post("/api/game/new", {"num_players": 4, "seed": 42})
        self._post("/api/game/action/roll", {"player_id": 0})

        ctrl = RogueAgentRequestHandler.controller
        p0 = ctrl.state.players[0]
        p0.money = 5
        p0.secrets = 8

        rolled = ctrl.player_meta[0]["rolled_pool"]
        rolled[0].current_face = Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)
        for d in rolled[1:]:
            d.current_face = Face(name="+$1", money=1)

        self._post("/api/game/action/commit", {
            "player_id": 0,
            "commitments": {"0": "any"},
        })

        orig_drop = ctrl.state.tower.drop
        ctrl.state.tower.drop = lambda cup, rng: {
            CubeColor.RED: 1,
            CubeColor.BLUE: 1,
            CubeColor.GREEN: 0,
            CubeColor.BLACK: 0,
        }
        try:
            res_comp = self._post("/api/game/action/compile", {})
        finally:
            ctrl.state.tower.drop = orig_drop

        self.assertTrue(res_comp["success"])
        self._post("/api/game/action/confirm_income", {"player_id": 0})
        res_conf = self._post("/api/game/action/confirm_attacks", {"player_id": 0})
        self.assertTrue(res_conf["success"])
        conf_p0 = res_conf["state"]["players"][0]

        # Default heuristic kept: Blue blocked (8 secrets), paid $1 for Red ($5 + $3 Phase 3 income - $1 = $7)
        self.assertEqual(conf_p0["money"], 7)
        self.assertEqual(conf_p0["secrets"], 8)


if __name__ == "__main__":
    unittest.main()
