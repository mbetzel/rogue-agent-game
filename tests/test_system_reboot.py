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
    # Unit Tests (SR-UNIT-01 to SR-UNIT-05): Verify System Reboot Excision (v0.22.0)
    # -------------------------------------------------------------------------
    def test_sr_unit_01_can_reboot_true_at_zero_ready_dice(self) -> None:
        """SR-UNIT-01: can_system_reboot is excised in v0.22.0."""
        bot = AdaptiveBalancedBot(0)
        player = PlayerState(
            player_id=0,
            bot=bot,
            money=5,
            secrets=8,
            patches=2,
            ready_dice=[],
            unpatched_dice=[create_gray_die(1), create_gray_die(2)],
        )
        self.assertFalse(hasattr(player, "can_system_reboot"))

    def test_sr_unit_02_can_reboot_false_when_ready_dice_exist(self) -> None:
        """SR-UNIT-02: execute_system_reboot is excised in v0.22.0."""
        bot = AdaptiveBalancedBot(0)
        player = PlayerState(
            player_id=0,
            bot=bot,
            money=5,
            secrets=8,
            patches=2,
            ready_dice=[create_gray_die(1)],
            unpatched_dice=[create_gray_die(2)],
        )
        self.assertFalse(hasattr(player, "execute_system_reboot"))

    def test_sr_unit_03_can_reboot_false_when_already_used(self) -> None:
        """SR-UNIT-03: system_reboot_used is excised in v0.22.0."""
        bot = AdaptiveBalancedBot(0)
        player = PlayerState(
            player_id=0,
            bot=bot,
            money=5,
            secrets=8,
            patches=2,
            ready_dice=[],
            unpatched_dice=[create_gray_die(1)],
        )
        self.assertFalse(hasattr(player, "system_reboot_used"))

    def test_sr_unit_04_execute_reboot_restores_only_gray_dice(self) -> None:
        """SR-UNIT-04: execute_system_reboot is excised from PlayerState."""
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
        )
        self.assertFalse(hasattr(player, "execute_system_reboot"))

    def test_sr_unit_05_execute_reboot_validation_and_state_flag(self) -> None:
        """SR-UNIT-05: PlayerState does not provide system reboot methods."""
        bot = AdaptiveBalancedBot(0)
        player = PlayerState(
            player_id=0,
            bot=bot,
            money=5,
            secrets=8,
            patches=2,
            ready_dice=[create_gray_die(1)],
            unpatched_dice=[create_gray_die(2)],
        )
        self.assertFalse(hasattr(player, "can_system_reboot"))
        self.assertFalse(hasattr(player, "execute_system_reboot"))

    # -------------------------------------------------------------------------
    # Engine & Bot Phase 3 Tests (SR-ENG-01 to SR-ENG-02)
    # -------------------------------------------------------------------------
    def test_sr_eng_01_phase3_ops_bot_triggers_system_reboot_when_empty(self) -> None:
        """SR-ENG-01: Phase 3 Action Plan does not contain use_system_reboot in v0.22.0."""
        cfg = GameConfig.legacy_v035(num_players=2)
        engine = GameEngine(cfg, seed=42)
        p0 = engine.state.players[0]

        plan = p0.bot.take_phase3_actions(p0, engine.state, engine.rng)
        self.assertFalse(hasattr(plan, "use_system_reboot"))

    def test_sr_eng_02_phase3_ops_bot_does_not_reboot_if_ready_dice_or_used(self) -> None:
        """SR-ENG-02: BaseBot does not provide should_trigger_system_reboot."""
        cfg = GameConfig.legacy_v035(num_players=2)
        engine = GameEngine(cfg, seed=42)
        p0 = engine.state.players[0]
        self.assertFalse(hasattr(p0.bot, "should_trigger_system_reboot"))

    # -------------------------------------------------------------------------
    # Web & Controller Tests (SR-WEB-01 to SR-WEB-03)
    # -------------------------------------------------------------------------
    def test_sr_web_01_serialization_includes_reboot_fields(self) -> None:
        """SR-WEB-01: Serialized player dictionary does not include excised reboot fields."""
        bot = AdaptiveBalancedBot(0)
        player = PlayerState(
            player_id=0,
            bot=bot,
            money=5,
            secrets=8,
            patches=2,
            ready_dice=[],
            unpatched_dice=[create_gray_die(1)],
        )
        cfg = GameConfig.legacy_v035(num_players=2)
        ser = GameStateSerializer.serialize_player(player, cfg, is_human=True, name="Player 1")

        self.assertNotIn("system_reboot_used", ser)
        self.assertNotIn("can_system_reboot", ser)

    def test_sr_web_02_controller_system_reboot_action_and_capabilities(self) -> None:
        """SR-WEB-02: GameController system_reboot() raises ValueError deprecation notice."""
        ctrl = RogueAgentRequestHandler.controller
        ctrl.new_game(num_players=2, seed=123)

        ctrl.phase = 6
        ctrl.active_player_index = 0
        with self.assertRaises(ValueError):
            ctrl.system_reboot(0)

    def test_sr_web_03_http_endpoint_system_reboot(self) -> None:
        """SR-WEB-03: HTTP endpoint POST /api/game/action/system_reboot returns 410 Gone."""
        ctrl = RogueAgentRequestHandler.controller
        ctrl.new_game(num_players=2, seed=999)

        url = f"{self.base_url}/api/game/action/system_reboot"
        body = json.dumps({"player_id": 0}).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 410)


if __name__ == "__main__":
    unittest.main()
