"""Phase 20 unit and integration tests for Web App State Synchronization & Player Selection Agency."""

from __future__ import annotations

import json
import os
import threading
import unittest
import urllib.error
import urllib.request
from typing import Any, Dict

from sim.config import CubeColor, DieColor, ShieldColor
from sim.engine.phase3_ops import execute_phase_3
from sim.entities import (
    AbilityStatus,
    ArchetypeCode,
    Face,
    create_colored_die,
    create_gray_die,
    get_archetype_by_code,
)
from web.server import RogueAgentRequestHandler, create_server


class TestPhase20Sync(unittest.TestCase):
    """Tests for Phase 20 state synchronization, player selection agency, and rule ordering fixes."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.server = create_server(host="127.0.0.1", port=0)
        cls.server_port = cls.server.server_address[1]
        cls.base_url = f"http://127.0.0.1:{cls.server_port}"
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()

    def _post(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
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

    def _get_with_headers(self, path: str) -> tuple[Dict[str, Any], Any]:
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req) as resp:
            headers = resp.headers
            data = json.loads(resp.read().decode("utf-8"))
            return data, headers

    # -------------------------------------------------------------------------
    # 1. Dirty Income Backlash by die_id, rolled_pool sync, and atomic validation
    # -------------------------------------------------------------------------
    def test_dirty_income_backlash_by_die_id_and_rolled_pool_sync(self) -> None:
        """Dirty Income supports backlash_die_id across Ready Zone and Active Pool, and validates before mutating."""
        ctrl = RogueAgentRequestHandler.controller
        ctrl.new_game(num_players=4, seed=42)
        self._post("/api/game/action/roll", {"player_id": 0})
        self._post("/api/game/action/commit", {"player_id": 0, "commitments": {}})
        self._post("/api/game/action/compile", {})

        # Force Phase 3 active turn on human player 0
        ctrl.phase = 3
        ctrl.active_player_index = 0
        p0 = ctrl.state.players[0]
        meta0 = ctrl.player_meta[0]
        meta0["dirty_income_taken_this_turn"] = False
        p0.secrets = 6
        p0.money = 4

        # Ensure player has rolled dice in rolled_pool AND a newly bought colored die in ready_dice
        yellow_die = create_colored_die(DieColor.YELLOW, die_id=999)
        p0.ready_dice.append(yellow_die)
        # Active rolled_pool has the starter gray dice, while visual ready_dice has yellow_die
        state_before = ctrl.get_full_state()
        p0_ser_before = state_before["players"][0]
        self.assertIn("all_ready_dice", p0_ser_before)
        self.assertTrue(any(d["die_id"] == 999 for d in p0_ser_before["ready_dice"]))

        # Pick a starter gray die that is in rolled_pool (Active Pool)
        active_gray_id = meta0["rolled_pool"][0].die_id
        black_before = ctrl.state.staging_cup[CubeColor.BLACK]

        # 1A: Invalid backlash_die_id must fail BEFORE mutating secrets/money/black cubes
        url = f"{self.base_url}/api/game/action/dirty_income"
        bad_body = json.dumps({"player_id": 0, "backlash_die_id": 123456}).encode("utf-8")
        req_bad = urllib.request.Request(url, data=bad_body, headers={"Content-Type": "application/json"}, method="POST")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req_bad)
        self.assertEqual(ctx.exception.code, 400)
        self.assertEqual(p0.secrets, 6)
        self.assertEqual(p0.money, 4)
        self.assertEqual(ctrl.state.staging_cup[CubeColor.BLACK], black_before)

        # 1B: Valid backlash_die_id targeting the starter gray die in Active Pool
        res = self._post("/api/game/action/dirty_income", {
            "player_id": 0,
            "backlash_die_id": active_gray_id,
        })
        self.assertTrue(res["success"])
        p0_after = res["state"]["players"][0]
        self.assertEqual(p0_after["secrets"], 5)
        self.assertEqual(p0_after["money"], 7)
        # Demoted die must be in unpatched_dice and NOT in rolled_pool or ready_dice
        unpatched_ids = [d["die_id"] for d in p0_after["unpatched_dice"]]
        rolled_ids = [d["die_id"] for d in p0_after["rolled_pool"]]
        ready_ids = [d["die_id"] for d in p0_after["ready_dice"]]
        self.assertIn(active_gray_id, unpatched_ids)
        self.assertNotIn(active_gray_id, rolled_ids)
        self.assertNotIn(active_gray_id, ready_ids)
        # Yellow die (999) was preserved!
        self.assertIn(999, ready_ids)

    # -------------------------------------------------------------------------
    # 2. Phreaker Single Die Selection by die_id and die_index
    # -------------------------------------------------------------------------
    def test_phreaker_single_die_selection_by_id_and_index(self) -> None:
        """Phreaker Magnetic Splice repairs exactly 1 chosen die by die_id or die_index."""
        ctrl = RogueAgentRequestHandler.controller
        ctrl.new_game(num_players=4, seed=42)
        ctrl.phase = 3
        ctrl.active_player_index = 0
        p0 = ctrl.state.players[0]
        p0.archetype = get_archetype_by_code(ArchetypeCode.PHREAKER)
        p0.ability_v1_status = AbilityStatus.AVAILABLE

        # Put a Gray die at index 0 and a Yellow die at index 1 in unpatched_dice
        gray_die = p0.ready_dice.pop(0)
        yellow_die = create_colored_die(DieColor.YELLOW, die_id=777)
        p0.unpatched_dice = [gray_die, yellow_die]

        # Repair specifically the Yellow die using die_id=777
        res = self._post("/api/game/action/phreaker", {
            "player_id": 0,
            "count": 1,
            "die_id": 777,
        })
        self.assertTrue(res["success"])
        p0_state = res["state"]["players"][0]
        unpatched_ids = [d["die_id"] for d in p0_state["unpatched_dice"]]
        all_ready_ids = [d["die_id"] for d in p0_state["all_ready_dice"]]
        self.assertEqual(len(unpatched_ids), 1)
        self.assertIn(gray_die.die_id, unpatched_ids)
        self.assertIn(777, all_ready_ids)
        self.assertEqual(p0_state["ability_v1_status"], "USED")

    # -------------------------------------------------------------------------
    # 3. Bot Phreaker 1-Die Cap & Priority in Web Controller and Sim Engine
    # -------------------------------------------------------------------------
    def test_bot_phreaker_repairs_1_die_and_prioritizes_colored(self) -> None:
        """Bot Phreaker repairs 1 die (not 2) and prioritizes colored/high-VP die over starter Gray."""
        ctrl = RogueAgentRequestHandler.controller
        ctrl.new_game(num_players=4, seed=42)
        ctrl.phase = 3
        bot_player = ctrl.state.players[1]
        bot_meta = ctrl.player_meta[1]
        bot_player.archetype = get_archetype_by_code(ArchetypeCode.PHREAKER)
        bot_player.ability_v1_status = AbilityStatus.AVAILABLE

        gray_die = bot_player.ready_dice.pop(0)
        purple_die = create_colored_die(DieColor.PURPLE, die_id=888)
        bot_player.unpatched_dice = [gray_die, purple_die]
        bot_player.money = 0
        bot_player.patches = 0
        bot_player.secrets = 1

        ctrl._execute_bot_phase3(bot_player, bot_meta)
        # Bot should have repaired purple_die (888) and left gray_die in unpatched_dice
        self.assertIn(purple_die, bot_player.ready_dice)
        self.assertIn(gray_die, bot_player.unpatched_dice)
        self.assertEqual(len(bot_player.unpatched_dice), 1)

        # Also test sim/engine/phase3_ops.py directly
        ctrl.new_game(num_players=2, seed=99)
        sim_p0 = ctrl.state.players[0]
        sim_p0.archetype = get_archetype_by_code(ArchetypeCode.PHREAKER)
        sim_p0.ability_v1_status = AbilityStatus.AVAILABLE
        g_die = sim_p0.ready_dice.pop(0)
        y_die = create_colored_die(DieColor.YELLOW, die_id=555)
        sim_p0.unpatched_dice = [g_die, y_die]
        sim_p0.money = 0
        sim_p0.patches = 0
        sim_p0.secrets = 1
        ctrl.state.players[1].is_patient_zero = True

        execute_phase_3(ctrl.engine)
        self.assertIn(y_die, sim_p0.ready_dice)
        self.assertIn(g_die, sim_p0.unpatched_dice)

    # -------------------------------------------------------------------------
    # 4. Glitch Backlash Demotion & Zero Glitch Output
    # -------------------------------------------------------------------------
    def test_glitch_backlash_before_resource_collection(self) -> None:
        """Glitch face yields 0 outputs and Glitch Backlash demotes target die and removes it from rolled_pool."""
        ctrl = RogueAgentRequestHandler.controller
        ctrl.new_game(num_players=4, seed=42)
        self._post("/api/game/action/roll", {"player_id": 0})
        p0 = ctrl.state.players[0]

        yellow_glitch = create_colored_die(DieColor.YELLOW, die_id=301)
        gray_cash = create_gray_die(die_id=302)
        yellow_glitch.current_face = Face(name="Hardware Glitch", is_glitch=True, money=5)
        gray_cash.current_face = Face(name="+$2", money=2)
        p0.ready_dice = [yellow_glitch, gray_cash]
        ctrl.player_meta[0]["rolled_pool"] = [yellow_glitch, gray_cash]
        p0.money = 5

        res2 = self._post("/api/game/action/commit", {"player_id": 0, "commitments": {}})
        self.assertTrue(res2["success"])
        p0_state = res2["state"]["players"][0]
        # Glitch face produces $0; gray_cash produces +$2 ($5 + $2 = $7) and is then demoted by Glitch Backlash
        self.assertEqual(p0_state["money"], 7)
        unpatched_ids = [d["die_id"] for d in p0_state["unpatched_dice"]]
        rolled_ids = [d["die_id"] for d in p0_state["rolled_pool"]]
        self.assertIn(302, unpatched_ids)
        self.assertNotIn(302, rolled_ids)

    # -------------------------------------------------------------------------
    # 5. Glitch Contractor Sacrifice Cleanup & Commitment Re-indexing
    # -------------------------------------------------------------------------
    def test_glitch_contractor_sacrifice_cleanup(self) -> None:
        """Sacrificing a White Contractor die in Glitch Backlash removes it from rolled_pool and re-indexes commitments."""
        ctrl = RogueAgentRequestHandler.controller
        ctrl.new_game(num_players=4, seed=42)
        self._post("/api/game/action/hire_contractors", {"player_id": 0, "count": 1})
        self._post("/api/game/action/roll", {"player_id": 0})

        p0 = ctrl.state.players[0]
        rolled = ctrl.player_meta[0]["rolled_pool"]
        # Put Contractor die at index 0 (so removing it shifts indices of subsequent dice!)
        contractor_die = p0.contractor_dice[0]
        other_dice = list(p0.ready_dice)
        rolled = [contractor_die] + other_dice
        ctrl.player_meta[0]["rolled_pool"] = rolled

        # Contractor die shows +$1, Die 1 shows Glitch, Die 2 shows Block 1 Red
        contractor_die.current_face = Face(name="+$1", money=1)
        rolled[1].current_face = Face(name="Glitch", is_glitch=True)
        rolled[2].current_face = Face(name="Block 1 Red", block_amount=1, shield_color=ShieldColor.RED)
        rolled[3].current_face = Face(name="+$1", money=1)
        rolled[4].current_face = Face(name="+$1", money=1)

        supply_before = ctrl.state.contractor_supply
        res_commit = self._post("/api/game/action/commit", {
            "player_id": 0,
            "commitments": {"2": "red"},
        })
        self.assertTrue(res_commit["success"])
        state_p2 = res_commit["state"]
        p0_p2 = state_p2["players"][0]

        # Contractor die was sacrificed to supply, removed from contractor_dice and rolled_pool
        self.assertEqual(len(p0_p2["contractor_dice"]), 0)
        self.assertEqual(p0_p2["hired_contractors"], 0)
        rolled_ids = [d["die_id"] for d in p0_p2["rolled_pool"]]
        self.assertNotIn(contractor_die.die_id, rolled_ids)

        # Compile drop in Phase 2 must succeed without IndexError and apply the Red shield
        res_compile = self._post("/api/game/action/compile", {})
        self.assertTrue(res_compile["success"])
        self.assertEqual(res_compile["state"]["phase"], 3)

    # -------------------------------------------------------------------------
    # 6. Spook $0 Free Activation Capability & Execution
    # -------------------------------------------------------------------------
    def test_spook_zero_dollar_capability_and_execution(self) -> None:
        """Spook ability is enabled at $0 cash after a compile drop and absorbs 2 free secrets."""
        ctrl = RogueAgentRequestHandler.controller
        ctrl.new_game(num_players=4, seed=42)
        p0 = ctrl.state.players[0]
        p0.archetype = get_archetype_by_code(ArchetypeCode.SPOOK)
        p0.ability_v1_status = AbilityStatus.AVAILABLE

        self._post("/api/game/action/roll", {"player_id": 0})
        self._post("/api/game/action/commit", {"player_id": 0, "commitments": {}})
        self._post("/api/game/action/compile", {})

        p0.money = 0
        p0.secrets = 5
        state = ctrl.get_full_state()
        self.assertTrue(state["action_capabilities"]["can_spook"])

        res_spook = self._post("/api/game/action/spook", {"player_id": 0, "dollars": 0})
        self.assertTrue(res_spook["success"])
        p0_after = res_spook["state"]["players"][0]
        self.assertEqual(p0_after["secrets"], 7)
        self.assertEqual(p0_after["money"], 0)
        self.assertEqual(p0_after["ability_v1_status"], "USED")

    # -------------------------------------------------------------------------
    # 7. No-Cache Headers and Concurrency Lock
    # -------------------------------------------------------------------------
    def test_no_cache_headers_and_concurrency_lock(self) -> None:
        """API responses include Cache-Control: no-store headers and handler has RLock."""
        self.assertIsNotNone(getattr(RogueAgentRequestHandler, "controller_lock", None))
        data, headers = self._get_with_headers("/api/game/state")
        self.assertTrue(data["success"])
        cache_ctrl = headers.get("Cache-Control", "")
        self.assertIn("no-store", cache_ctrl)
        self.assertIn("no-cache", cache_ctrl)

    # -------------------------------------------------------------------------
    # 8. Frontend Selection Sanitization & Agency Selectors Verification
    # -------------------------------------------------------------------------
    def test_frontend_selection_sanitization_and_selectors(self) -> None:
        """Verifies frontend JS modules implement state sanitization and die_id selectors."""
        js_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web", "static", "js"))

        with open(os.path.join(js_dir, "state.js"), "r", encoding="utf-8") as f:
            state_js = f.read()
        self.assertIn("sanitizeSelectionState", state_js)
        self.assertIn("getEligibleBacklashDice", state_js)
        self.assertIn("selectedBacklashDieId", state_js)
        self.assertIn("selectedPhreakerDieId", state_js)

        with open(os.path.join(js_dir, "api.js"), "r", encoding="utf-8") as f:
            api_js = f.read()
        self.assertIn("isActionInFlight", api_js)
        self.assertIn("backlash_die_id", api_js)
        self.assertIn("phreakerDieSelect", api_js)
        self.assertIn("no-store", api_js)

        with open(os.path.join(js_dir, "components", "action_dock.js"), "r", encoding="utf-8") as f:
            dock_js = f.read()
        self.assertIn("phreakerDieSelect", dock_js)
        self.assertIn("getEligibleBacklashDice", dock_js)
        self.assertIn("Repair 1 Die Free", dock_js)
        self.assertIn("Ignore 1", dock_js)
        self.assertIn("renderPlayerMats()", dock_js)

        with open(os.path.join(js_dir, "components", "player_mats.js"), "r", encoding="utf-8") as f:
            mats_js = f.read()
        self.assertIn("!p.has_rolled && p.contractor_dice", mats_js)
        self.assertIn("canPatchActiveMode", mats_js)


if __name__ == "__main__":
    unittest.main()
