"""Unit and Integration Tests for Player-Count Pacing Parity & Scaling (v0.10.0 Baseline)."""

import random
import unittest

from sim.config import CubeColor, DieColor, GameConfig, ShieldColor
from sim.bots.adaptive_balanced import AdaptiveBalancedBot
from sim.engine.core import GameEngine
from sim.entities import get_all_version_cards, get_default_version_deck
from web.schemas import GameStateSerializer


class TestV100Rules(unittest.TestCase):
    """Test suite covering Corruption Track scaling and buffer parity for v0.10.0."""

    def test_corruption_track_capacity_scaling(self):
        """Corruption track capacity should scale to 4 for 2P, 5 for 3P, and 6 for 4P."""
        cfg_2p = GameConfig(num_players=2)
        cfg_3p = GameConfig(num_players=3)
        cfg_4p = GameConfig(num_players=4)

        self.assertEqual(cfg_2p.corruption_track_capacity, 4)
        self.assertEqual(cfg_3p.corruption_track_capacity, 5)
        self.assertEqual(cfg_4p.corruption_track_capacity, 6)

    def test_corruption_track_flat_override(self):
        """Flat capacity scalar override should override player-count scaling when provided."""
        cfg = GameConfig(num_players=4, corruption_track_flat_capacity=4)
        self.assertEqual(cfg.corruption_track_capacity, 4)

    def test_starting_secrets_scaling(self):
        """Starting Secrets should be 8 for 2P, 8 for 3P, and 10 for 4P."""
        cfg_2p = GameConfig(num_players=2)
        cfg_3p = GameConfig(num_players=3)
        cfg_4p = GameConfig(num_players=4)

        self.assertEqual(cfg_2p.get_starting_secrets(2), 8)
        self.assertEqual(cfg_3p.get_starting_secrets(3), 8)
        self.assertEqual(cfg_4p.get_starting_secrets(4), 10)

    def test_starting_patches_flat(self):
        """Starting Patch Tokens should be 2 across all player counts."""
        cfg_2p = GameConfig(num_players=2)
        cfg_3p = GameConfig(num_players=3)
        cfg_4p = GameConfig(num_players=4)

        self.assertEqual(cfg_2p.get_starting_patches(2), 2)
        self.assertEqual(cfg_3p.get_starting_patches(3), 2)
        self.assertEqual(cfg_4p.get_starting_patches(4), 2)

    def test_version_cards_upgrade_payloads_standardized(self):
        """v2.0 and v3.0 cards should inject exactly 2 cubes on upgrade across all versions."""
        cards = {c.directive_code: c for c in get_all_version_cards()}

        # v2.0 cards
        raas_payload = cards["RAAS"].get_staging_payload(4)
        self.assertEqual(sum(raas_payload.values()), 2)
        self.assertEqual(raas_payload[CubeColor.RED], 1)
        self.assertEqual(raas_payload[CubeColor.GREEN], 1)

        worm_payload = cards["POLYMORPHIC_WORM"].get_staging_payload(4)
        self.assertEqual(sum(worm_payload.values()), 2)
        self.assertEqual(worm_payload[CubeColor.GREEN], 1)
        self.assertEqual(worm_payload[CubeColor.BLACK], 1)

        # v3.0 cards
        zero_day_payload = cards["ZERO_DAY_OVERRIDE"].get_staging_payload(4)
        self.assertEqual(sum(zero_day_payload.values()), 2)
        self.assertEqual(zero_day_payload[CubeColor.RED], 1)
        self.assertEqual(zero_day_payload[CubeColor.BLACK], 1)

        corrupted_payload = cards["CORRUPTED_KERNEL"].get_staging_payload(4)
        self.assertEqual(sum(corrupted_payload.values()), 2)
        self.assertEqual(corrupted_payload[CubeColor.RED], 1)
        self.assertEqual(corrupted_payload[CubeColor.BLUE], 1)

    def test_game_engine_initializes_with_v100_defaults(self):
        """GameEngine initializes players with correct v0.10.0 resources per player count."""
        # 4-player game
        cfg_4p = GameConfig(num_players=4)
        bots_4p = [AdaptiveBalancedBot(i) for i in range(4)]
        eng_4p = GameEngine(cfg_4p, bots_4p, seed=42)

        self.assertEqual(eng_4p.config.corruption_track_capacity, 6)
        for player in eng_4p.state.players:
            self.assertEqual(player.secrets, 10)
            self.assertEqual(player.patches, 2)

        # 3-player game
        cfg_3p = GameConfig(num_players=3)
        bots_3p = [AdaptiveBalancedBot(i) for i in range(3)]
        eng_3p = GameEngine(cfg_3p, bots_3p, seed=42)

        self.assertEqual(eng_3p.config.corruption_track_capacity, 5)
        for player in eng_3p.state.players:
            self.assertEqual(player.secrets, 8)
            self.assertEqual(player.patches, 2)

        # 2-player game
        cfg_2p = GameConfig(num_players=2)
        bots_2p = [AdaptiveBalancedBot(i) for i in range(2)]
        eng_2p = GameEngine(cfg_2p, bots_2p, seed=42)

        self.assertEqual(eng_2p.config.corruption_track_capacity, 4)
        for player in eng_2p.state.players:
            self.assertEqual(player.secrets, 8)
            self.assertEqual(player.patches, 2)

    def test_web_serializer_reports_player_count_capacity(self):
        """Web state serializer correctly exposes corruption_capacity matching player count."""
        cfg_4p = GameConfig(num_players=4)
        bots_4p = [AdaptiveBalancedBot(i) for i in range(4)]
        eng_4p = GameEngine(cfg_4p, bots_4p, seed=42)

        serialized = GameStateSerializer.serialize_game_state(eng_4p.state, {"players": {}})
        self.assertEqual(serialized["corruption_capacity"], 6)

        cfg_2p = GameConfig(num_players=2)
        bots_2p = [AdaptiveBalancedBot(i) for i in range(2)]
        eng_2p = GameEngine(cfg_2p, bots_2p, seed=42)

        serialized_2p = GameStateSerializer.serialize_game_state(eng_2p.state, {"players": {}})
        self.assertEqual(serialized_2p["corruption_capacity"], 4)


if __name__ == "__main__":
    unittest.main()
