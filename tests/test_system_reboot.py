"""Unit and integration tests for Phase 21: Once-per-Game System Reboot (RULES.md v0.14.0).

Test Matrix:
- SR-UNIT-01: can_system_reboot is True when 0 ready dice and reboot not used.
- SR-UNIT-02: can_system_reboot is False when ready dice > 0.
- SR-UNIT-03: can_system_reboot is False when reboot already used.
- SR-UNIT-04: execute_system_reboot() restores ONLY Gray starter dice from unpatched_dice to ready_dice;
              colored module dice remain in unpatched_dice.
- SR-UNIT-05: execute_system_reboot() raises ValueError if can_system_reboot is False, and sets
              system_reboot_used = True upon execution.
- SR-ENG-01: Simulation engine Phase 3: Bot at 0 ready dice triggers system reboot in Phase 3 ops,
             restoring unpatched gray dice to ready_dice.
- SR-ENG-02: Simulation engine Phase 3: Bot does not trigger reboot if ready dice > 0 or already used.
- SR-WEB-01: PlayerState / GameState serialization includes system_reboot_used and can_system_reboot.
- SR-WEB-02: Web controller system_reboot() action executes reboot on active human player, restores dice,
             updates capabilities, and logs event.
- SR-WEB-03: Web server HTTP endpoint POST /api/game/action/system_reboot returns 200 on success and 400 on error.
"""

from __future__ import annotations

import json
import threading
import unittest
import urllib.error
import urllib.request
from typing import Any, Dict

from sim.bots import AdaptiveBalancedBot, Phase3ActionPlan
from sim.config import CubeColor, DieColor, GameConfig, ShieldColor
from sim.engine import GameEngine, PlayerState
from sim.engine.phase3_ops import execute_phase_3
from sim.entities import create_colored_die, create_gray_die, get_default_variant_cards
from web.controller.core import GameController
from web.schemas import GameStateSerializer
from web.server import RogueAgentRequestHandler, create_server


class TestSystemReboot(unittest.TestCase):
    """Test suite covering System Reboot specification across sim, engine, schemas, controller, and web server."""

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

    # -------------------------------------------------------------------------
    # Unit Tests (SR-UNIT-01 to SR-UNIT-05)
    # -------------------------------------------------------------------------
    def test_sr_unit_01_can_reboot_true_at_zero_ready_dice(self) -> None:
        """SR-UNIT-01: can_system_reboot is True when player has 0 ready dice and reboot not used."""
        bot = AdaptiveBalancedBot(0)
        player = PlayerState(
            player_id=0,
            bot=bot,
            money=5,
            secrets=8,
            patches=2,
            ready_dice=[],
            unpatched_dice=[create_gray_die(1), create_gray_die(2)],
            system_reboot_used=False,
        )
        self.assertTrue(player.can_system_reboot)

    def test_sr_unit_02_can_reboot_false_when_ready_dice_exist(self) -> None:
        """SR-UNIT-02: can_system_reboot is False when player has 1 or more ready dice."""
        bot = AdaptiveBalancedBot(0)
        player = PlayerState(
            player_id=0,
            bot=bot,
            money=5,
            secrets=8,
            patches=2,
            ready_dice=[create_gray_die(1)],
            unpatched_dice=[create_gray_die(2)],
            system_reboot_used=False,
        )
        self.assertFalse(player.can_system_reboot)

    def test_sr_unit_03_can_reboot_false_when_already_used(self) -> None:
        """SR-UNIT-03: can_system_reboot is False when player has already used system reboot."""
        bot = AdaptiveBalancedBot(0)
        player = PlayerState(
            player_id=0,
            bot=bot,
            money=5,
            secrets=8,
            patches=2,
            ready_dice=[],
            unpatched_dice=[create_gray_die(1)],
            system_reboot_used=True,
        )
        self.assertFalse(player.can_system_reboot)

    def test_sr_unit_04_execute_reboot_restores_only_gray_dice(self) -> None:
        """SR-UNIT-04: execute_system_reboot() restores ONLY Gray starter dice to ready_dice; colored dice remain unpatched."""
        bot = AdaptiveBalancedBot(0)
        gray1 = create_gray_die(1)
        gray2 = create_gray_die(2)
        red_die = create_colored_die(DieColor.RED, 3)
        blue_die = create_colored_die(DieColor.BLUE, 4)

        player = PlayerState(
            player_id=0,
            bot=bot,
            money=5,
            secrets=8,
            patches=2,
            ready_dice=[],
            unpatched_dice=[gray1, red_die, gray2, blue_die],
            system_reboot_used=False,
        )

        restored = player.execute_system_reboot()

        # Validations
        self.assertEqual(len(restored), 2)
        self.assertEqual(set(d.die_id for d in restored), {gray1.die_id, gray2.die_id})
        self.assertEqual(len(player.ready_dice), 2)
        self.assertTrue(all(d.color == DieColor.GRAY for d in player.ready_dice))
        self.assertEqual(len(player.unpatched_dice), 2)
        self.assertEqual(set(d.die_id for d in player.unpatched_dice), {red_die.die_id, blue_die.die_id})
        self.assertTrue(player.system_reboot_used)
        self.assertFalse(player.can_system_reboot)

    def test_sr_unit_05_execute_reboot_validation_and_state_flag(self) -> None:
        """SR-UNIT-05: execute_system_reboot() raises ValueError when can_system_reboot is False, and sets flag."""
        bot = AdaptiveBalancedBot(0)
        player = PlayerState(
            player_id=0,
            bot=bot,
            money=5,
            secrets=8,
            patches=2,
            ready_dice=[create_gray_die(1)],
            unpatched_dice=[create_gray_die(2)],
            system_reboot_used=False,
        )

        with self.assertRaises(ValueError):
            player.execute_system_reboot()

        player.ready_dice.clear()
        self.assertTrue(player.can_system_reboot)
        player.execute_system_reboot()
        self.assertTrue(player.system_reboot_used)

        # Cannot execute second time
        with self.assertRaises(ValueError):
            player.execute_system_reboot()

    # -------------------------------------------------------------------------
    # Engine & Bot Phase 3 Tests (SR-ENG-01 to SR-ENG-02)
    # -------------------------------------------------------------------------
    def test_sr_eng_01_phase3_ops_bot_triggers_system_reboot_when_empty(self) -> None:
        """SR-ENG-01: Engine Phase 3 execution: Bot entering Phase 3 with 0 ready dice reboots and restores starter gray dice."""
        cfg = GameConfig(num_players=2)
        engine = GameEngine(cfg, seed=42)
        p0 = engine.state.players[0]

        # Put all p0 dice into unpatched
        gray_dice = list(p0.ready_dice)
        p0.ready_dice.clear()
        p0.unpatched_dice.extend(gray_dice)
        self.assertEqual(len(p0.ready_dice), 0)
        self.assertFalse(p0.system_reboot_used)

        plan = p0.bot.take_phase3_actions(p0, engine.state, engine.rng)
        self.assertTrue(plan.use_system_reboot)

        # Execute Phase 3
        execute_phase_3(engine)

        # Player 0 should have rebooted and restored gray dice
        self.assertTrue(p0.system_reboot_used)
        self.assertGreater(len(p0.ready_dice), 0)
        self.assertTrue(all(d.color == DieColor.GRAY for d in p0.ready_dice))

    def test_sr_eng_02_phase3_ops_bot_does_not_reboot_if_ready_dice_or_used(self) -> None:
        """SR-ENG-02: Engine Phase 3 execution: Bot does not trigger reboot if it has ready dice or already used reboot."""
        cfg = GameConfig(num_players=2)
        engine = GameEngine(cfg, seed=42)
        p0 = engine.state.players[0]

        # Case A: Ready dice exist
        self.assertGreater(len(p0.ready_dice), 0)
        plan_a = p0.bot.take_phase3_actions(p0, engine.state, engine.rng)
        self.assertFalse(plan_a.use_system_reboot)

        # Case B: Already used
        p0.ready_dice.clear()
        p0.system_reboot_used = True
        plan_b = p0.bot.take_phase3_actions(p0, engine.state, engine.rng)
        self.assertFalse(plan_b.use_system_reboot)

    # -------------------------------------------------------------------------
    # Web & Controller Tests (SR-WEB-01 to SR-WEB-03)
    # -------------------------------------------------------------------------
    def test_sr_web_01_serialization_includes_reboot_fields(self) -> None:
        """SR-WEB-01: Serialized player dictionary includes system_reboot_used and can_system_reboot."""
        bot = AdaptiveBalancedBot(0)
        player = PlayerState(
            player_id=0,
            bot=bot,
            money=5,
            secrets=8,
            patches=2,
            ready_dice=[],
            unpatched_dice=[create_gray_die(1)],
            system_reboot_used=False,
        )
        cfg = GameConfig(num_players=2)
        ser = GameStateSerializer.serialize_player(player, cfg, is_human=True, name="Player 1")

        self.assertIn("system_reboot_used", ser)
        self.assertIn("can_system_reboot", ser)
        self.assertFalse(ser["system_reboot_used"])
        self.assertTrue(ser["can_system_reboot"])

    def test_sr_web_02_controller_system_reboot_action_and_capabilities(self) -> None:
        """SR-WEB-02: GameController system_reboot() restores dice, updates capabilities, and logs event."""
        ctrl = RogueAgentRequestHandler.controller
        ctrl.new_game(num_players=2, seed=123)

        ctrl.phase = 3
        ctrl.active_player_index = 0
        p0 = ctrl.state.players[0]

        # Move ready dice to unpatched
        worn_dice = list(p0.ready_dice)
        p0.ready_dice.clear()
        p0.unpatched_dice.extend(worn_dice)

        caps_before = ctrl.get_action_capabilities(0)
        self.assertTrue(caps_before.get("can_system_reboot", False))

        state = ctrl.system_reboot(0)
        p0_ser = state["players"][0]
        self.assertTrue(p0_ser["system_reboot_used"])
        self.assertFalse(p0_ser["can_system_reboot"])
        self.assertEqual(len(p0_ser["ready_dice"]), len(worn_dice))

        caps_after = state["action_capabilities"]
        self.assertFalse(caps_after.get("can_system_reboot", True))

        # Event log check
        event_found = any("System Reboot" in ev for ev in state["event_log"])
        self.assertTrue(event_found)

    def test_sr_web_03_http_endpoint_system_reboot(self) -> None:
        """SR-WEB-03: HTTP endpoint POST /api/game/action/system_reboot executes reboot or returns 400."""
        ctrl = RogueAgentRequestHandler.controller
        ctrl.new_game(num_players=2, seed=999)

        # Force Phase 3 active turn
        ctrl.phase = 3
        ctrl.active_player_index = 0
        p0 = ctrl.state.players[0]

        # Case A: Fails when player still has ready dice
        url = f"{self.base_url}/api/game/action/system_reboot"
        body = json.dumps({"player_id": 0}).encode("utf-8")
        req_bad = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req_bad)
        self.assertEqual(ctx.exception.code, 400)

        # Case B: Succeeds when player has 0 ready dice
        worn_dice = list(p0.ready_dice)
        p0.ready_dice.clear()
        p0.unpatched_dice.extend(worn_dice)

        resp_data = self._post("/api/game/action/system_reboot", {"player_id": 0})
        self.assertTrue(resp_data["success"])
        p0_state = resp_data["state"]["players"][0]
        self.assertTrue(p0_state["system_reboot_used"])
        self.assertEqual(len(p0_state["ready_dice"]), len(worn_dice))

        # Case C: Fails on second attempt
        with self.assertRaises(urllib.error.HTTPError) as ctx2:
            urllib.request.urlopen(req_bad)
        self.assertEqual(ctx2.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
