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


def _pause_in_phase5(controller, pid):
    """v0.34: Omnidyne Magnetic Splice resolves in Phase 5 step 1; park the controller in choose_graduates."""
    from web.controller.phase5_pipeline_actions import _needs_choice

    controller.phase = 5
    controller.subphase = "choose_graduates"
    controller.pending_graduation = {pid: _needs_choice(controller, controller.state.players[pid])}

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

    # -------------------------------------------------------------------------
    # 2. Phreaker Single Die Selection by die_id and die_index
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # 3. Bot Phreaker 1-Die Cap & Priority in Web Controller and Sim Engine
    # -------------------------------------------------------------------------
    def test_bot_phreaker_repairs_1_die_and_prioritizes_colored(self) -> None:
        """Bot Phreaker repairs 1 die (not 2) and prioritizes colored/high-VP die over starter Gray."""
        ctrl = RogueAgentRequestHandler.controller
        ctrl.new_game(num_players=4, seed=42)
        ctrl.phase = 6
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

        # v0.34: the bot's Magnetic Splice resolves in Phase 5 step 1 (engine helper used by the web)
        from sim.engine.phase5_pipeline_shift import apply_hotfix_bypass

        apply_hotfix_bypass(ctrl.engine, bot_player)
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

    # -------------------------------------------------------------------------
    # 5. Glitch Contractor Sacrifice Cleanup & Commitment Re-indexing
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # 6. Spook $0 Free Activation Capability & Execution
    # -------------------------------------------------------------------------

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


if __name__ == "__main__":
    unittest.main()
