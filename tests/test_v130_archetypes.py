"""Unit tests for Phase 19: Consultancy Archetype Recalibration & Parity (v0.13.0 Baseline)."""

import unittest
from typing import Dict, List

from sim.bots import AdaptiveBalancedBot
from sim.config import CubeColor, DieColor, GameConfig, ShieldColor
from sim.engine import GameEngine
from sim.entities import (
    AbilityStatus,
    ArchetypeCode,
    Face,
    get_all_archetype_cards,
    get_archetype_by_code,
)


class TestV130Archetypes(unittest.TestCase):
    """Unit tests for v0.13.0 archetype ability rebalance rules."""

    def test_phreaker_patches_strictly_one_die(self) -> None:
        """1. Phreaker restores strictly 1 worn die (down from 2 in v0.12.0) for free."""
        config = GameConfig(num_players=4)
        phreaker_card = get_archetype_by_code(ArchetypeCode.PHREAKER)
        engine = GameEngine(
            config=config,
            bots=[AdaptiveBalancedBot(0), AdaptiveBalancedBot(1), AdaptiveBalancedBot(2), AdaptiveBalancedBot(3)],
            seed=42,
            archetypes=[phreaker_card, get_archetype_by_code(ArchetypeCode.OPERATOR),
                        get_archetype_by_code(ArchetypeCode.CIPHER), get_archetype_by_code(ArchetypeCode.SPOOK)],
        )

        player = engine.state.players[0]
        # Move 3 ready dice to unpatched
        for _ in range(3):
            d = player.ready_dice.pop(0)
            player.unpatched_dice.append(d)

        initial_unpatched = len(player.unpatched_dice)
        initial_ready = len(player.ready_dice)
        player.patches = 0
        player.money = 0
        player.secrets = 1  # Avoid dirty income triggering during Phase 3

        engine._execute_phase_3()

        # Under v0.13.0, exactly 1 die is patched for free
        self.assertEqual(len(player.unpatched_dice), initial_unpatched - 1)
        self.assertEqual(len(player.ready_dice), initial_ready + 1)
        self.assertEqual(player.ability_v1_status, AbilityStatus.USED)

    def test_acoustic_ignores_one_cube_without_tray_removal(self) -> None:
        """2. Acoustic Baffle Echo ignores 1 attack cube for self without decrementing tray exited cubes."""
        config = GameConfig(num_players=4)
        acoustic_card = get_archetype_by_code(ArchetypeCode.ACOUSTIC)
        engine = GameEngine(
            config=config,
            bots=[AdaptiveBalancedBot(0), AdaptiveBalancedBot(1), AdaptiveBalancedBot(2), AdaptiveBalancedBot(3)],
            seed=42,
            archetypes=[acoustic_card, get_archetype_by_code(ArchetypeCode.OPERATOR),
                        get_archetype_by_code(ArchetypeCode.CIPHER), get_archetype_by_code(ArchetypeCode.PRODIGY)],
        )

        player = engine.state.players[0]
        player.secrets = 8
        player.money = 5
        player.patches = 0

        # Drop 2 Blue cubes
        attack_strengths = {CubeColor.RED: 0, CubeColor.BLUE: 2, CubeColor.GREEN: 0}
        exited_cubes = {CubeColor.RED: 0, CubeColor.BLUE: 2, CubeColor.GREEN: 0}

        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=[],
            commitments={},
            attack_strengths=attack_strengths,
            exited_cubes=exited_cubes,
            active_directive="SCRIPT_KIDDIE",
        )

        # Acoustic ignores 1 Blue cube: takes 1 damage (8 - 1 = 7 Secrets)
        self.assertEqual(player.secrets, 7)
        # Exited cubes in tray are NOT decremented (they recycle into the staging cup)
        self.assertEqual(exited_cubes[CubeColor.BLUE], 2)
        self.assertEqual(player.ability_v1_status, AbilityStatus.USED)

    def test_acoustic_multiple_colors_prioritizes_highest_threat(self) -> None:
        """3. Acoustic bot prioritizes Blue threat (Secrets) over Red (Cash) when both deal unblocked damage."""
        config = GameConfig(num_players=4)
        acoustic_card = get_archetype_by_code(ArchetypeCode.ACOUSTIC)
        engine = GameEngine(
            config=config,
            bots=[AdaptiveBalancedBot(0), AdaptiveBalancedBot(1), AdaptiveBalancedBot(2), AdaptiveBalancedBot(3)],
            seed=42,
            archetypes=[acoustic_card, get_archetype_by_code(ArchetypeCode.OPERATOR),
                        get_archetype_by_code(ArchetypeCode.CIPHER), get_archetype_by_code(ArchetypeCode.PRODIGY)],
        )

        player = engine.state.players[0]
        player.secrets = 8
        player.money = 5
        player.patches = 0

        attack_strengths = {CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 0}
        exited_cubes = {CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 0}

        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=[],
            commitments={},
            attack_strengths=attack_strengths,
            exited_cubes=exited_cubes,
            active_directive="SCRIPT_KIDDIE",
        )

        # Bot prioritizes Blue: ignores 1 Blue (0 secret lost), but suffers 1 Red ($1 lost)
        self.assertEqual(player.secrets, 8)
        self.assertEqual(player.money, 4)
        self.assertEqual(player.ability_v1_status, AbilityStatus.USED)

    def test_spook_slush_fund_absorbs_two_secrets_free(self) -> None:
        """4. Spook Slush Fund absorbs up to 2 Corporate Secret loss for free ($0 spent)."""
        config = GameConfig(num_players=4)
        spook_card = get_archetype_by_code(ArchetypeCode.SPOOK)
        engine = GameEngine(
            config=config,
            bots=[AdaptiveBalancedBot(0), AdaptiveBalancedBot(1), AdaptiveBalancedBot(2), AdaptiveBalancedBot(3)],
            seed=42,
            archetypes=[spook_card, get_archetype_by_code(ArchetypeCode.OPERATOR),
                        get_archetype_by_code(ArchetypeCode.CIPHER), get_archetype_by_code(ArchetypeCode.PRODIGY)],
        )

        player = engine.state.players[0]
        player.secrets = 8
        player.money = 5
        player.patches = 0

        attack_strengths = {CubeColor.RED: 0, CubeColor.BLUE: 2, CubeColor.GREEN: 0}
        exited_cubes = {CubeColor.RED: 0, CubeColor.BLUE: 2, CubeColor.GREEN: 0}

        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=[],
            commitments={},
            attack_strengths=attack_strengths,
            exited_cubes=exited_cubes,
            active_directive="SCRIPT_KIDDIE",
        )

        # 2 Secrets absorbed for free without spending cash
        self.assertEqual(player.secrets, 8)
        self.assertEqual(player.money, 5)
        self.assertEqual(player.ability_v1_status, AbilityStatus.USED)

    def test_spook_slush_fund_absorbs_excess_with_cash(self) -> None:
        """5. Spook absorbs 2 secrets free + pays $1 cash for the 3rd secret loss."""
        config = GameConfig(num_players=4)
        spook_card = get_archetype_by_code(ArchetypeCode.SPOOK)
        engine = GameEngine(
            config=config,
            bots=[AdaptiveBalancedBot(0), AdaptiveBalancedBot(1), AdaptiveBalancedBot(2), AdaptiveBalancedBot(3)],
            seed=42,
            archetypes=[spook_card, get_archetype_by_code(ArchetypeCode.OPERATOR),
                        get_archetype_by_code(ArchetypeCode.CIPHER), get_archetype_by_code(ArchetypeCode.PRODIGY)],
        )

        player = engine.state.players[0]
        player.secrets = 8
        player.money = 5
        player.patches = 0

        attack_strengths = {CubeColor.RED: 0, CubeColor.BLUE: 3, CubeColor.GREEN: 0}
        exited_cubes = {CubeColor.RED: 0, CubeColor.BLUE: 3, CubeColor.GREEN: 0}

        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=[],
            commitments={},
            attack_strengths=attack_strengths,
            exited_cubes=exited_cubes,
            active_directive="SCRIPT_KIDDIE",
        )

        # 2 free + 1 paid with cash -> 8 secrets remain, $4 cash remain ($5 - $1)
        self.assertEqual(player.secrets, 8)
        self.assertEqual(player.money, 4)
        self.assertEqual(player.ability_v1_status, AbilityStatus.USED)

    def test_spook_does_not_waste_charge_on_zero_loss(self) -> None:
        """6. Spook Slush Fund does not activate or waste charge when 0 Secret loss occurs."""
        config = GameConfig(num_players=4)
        spook_card = get_archetype_by_code(ArchetypeCode.SPOOK)
        engine = GameEngine(
            config=config,
            bots=[AdaptiveBalancedBot(0), AdaptiveBalancedBot(1), AdaptiveBalancedBot(2), AdaptiveBalancedBot(3)],
            seed=42,
            archetypes=[spook_card, get_archetype_by_code(ArchetypeCode.OPERATOR),
                        get_archetype_by_code(ArchetypeCode.CIPHER), get_archetype_by_code(ArchetypeCode.PRODIGY)],
        )

        player = engine.state.players[0]
        player.secrets = 8
        player.money = 5

        # Red ransom fully paid by cash: 0 secret loss
        attack_strengths = {CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 0}
        exited_cubes = {CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 0}

        engine._resolve_player_defense_and_wear(
            player=player,
            rolled_dice=[],
            commitments={},
            attack_strengths=attack_strengths,
            exited_cubes=exited_cubes,
            active_directive="SCRIPT_KIDDIE",
        )

        # Cash pays $2 ransom; 0 secret loss; ability remains AVAILABLE
        self.assertEqual(player.money, 3)
        self.assertEqual(player.secrets, 8)
        self.assertEqual(player.ability_v1_status, AbilityStatus.AVAILABLE)

    def test_prodigy_brute_force_face_override(self) -> None:
        """7. Prodigy Brute-Force Bypass unlocks locked dice and overrides 1 rolled die to non-Star face."""
        config = GameConfig(num_players=4)
        prodigy_card = get_archetype_by_code(ArchetypeCode.PRODIGY)
        engine = GameEngine(
            config=config,
            bots=[AdaptiveBalancedBot(0), AdaptiveBalancedBot(1), AdaptiveBalancedBot(2), AdaptiveBalancedBot(3)],
            seed=42,
            archetypes=[prodigy_card, get_archetype_by_code(ArchetypeCode.OPERATOR),
                        get_archetype_by_code(ArchetypeCode.CIPHER), get_archetype_by_code(ArchetypeCode.SPOOK)],
        )

        player = engine.state.players[0]
        # Force a die to have a glitch face
        glitch_face = Face(name="Glitch (Locked)", is_glitch=True)
        player.ready_dice[0].current_face = glitch_face
        player.ready_dice[0].is_locked = True

        engine._execute_phase_1()

        # Prodigy activates Brute-Force Bypass
        self.assertEqual(player.ability_v1_status, AbilityStatus.USED)
        # Die 0 should have been overridden to a valid non-star, non-glitch face
        face = player.ready_dice[0].current_face
        self.assertIsNotNone(face)
        self.assertFalse(face.is_glitch)
        self.assertFalse(face.is_star)

    def test_dossier_text_accuracy(self) -> None:
        """8. All 6 archetype dossier texts accurately reflect v0.13.0 rules."""
        cards = {c.code: c for c in get_all_archetype_cards()}
        self.assertIn("ignore 1 Attack Cube", cards[ArchetypeCode.ACOUSTIC].description)
        self.assertIn("Move 1 worn die", cards[ArchetypeCode.PHREAKER].description)
        self.assertIn("turn 1 of your rolled dice to any non-Star face", cards[ArchetypeCode.PRODIGY].description)
        self.assertIn("Absorb up to 2 Corporate Secret loss", cards[ArchetypeCode.SPOOK].description)
        self.assertIn("$2 discount", cards[ArchetypeCode.CIPHER].description)
        self.assertIn("2 White Contractor Dice for free", cards[ArchetypeCode.OPERATOR].description)


if __name__ == "__main__":
    unittest.main()
