"""GameEngine orchestrator coordinating game loops and phases."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from sim.bots.base import BaseBot
from sim.bots.adaptive_balanced import AdaptiveBalancedBot
from sim.config import (
    CubeColor,
    DieColor,
    EndGameReason,
    GameConfig,
    ShieldColor,
)
from sim.entities import (
    AbilityStatus,
    ArchetypeCard,
    Die,
    Face,
    VariantCard,
    VersionCard,
    create_gray_die,
    create_white_die,
    get_all_archetype_cards,
    get_archetype_by_code,
    get_default_variant_cards,
    get_default_version_deck,
    get_random_archetypes,
)
from sim.tower import CubeTower
from sim.engine.state import EndGameResult, GameState, PlayerState, RoundTelemetry
from sim.engine import phase1_boot, phase2_threat, phase3_ops, end_game


class GameEngine:
    """Executes the complete Rogue Agent game loop per RULES.md."""

    def __init__(
        self,
        config: GameConfig,
        bots: Optional[List[BaseBot]] = None,
        seed: Optional[int] = None,
        variant_cards: Optional[Dict[DieColor, VariantCard]] = None,
        version_deck: Optional[List[VersionCard]] = None,
        archetypes: Optional[List[ArchetypeCard]] = None,
    ) -> None:
        if bots is None:
            bots = [AdaptiveBalancedBot(i) for i in range(config.num_players)]
        elif len(bots) != config.num_players:
            raise ValueError(f"Bot count ({len(bots)}) must match config.num_players ({config.num_players})")

        self.rng = random.Random(seed)
        self.config = config
        self.variant_cards = variant_cards or get_default_variant_cards()
        self.version_deck = version_deck or get_default_version_deck(profile=config.corruption_track_profile)
        if archetypes is None:
            self.archetypes = get_random_archetypes(config.num_players, self.rng)
        else:
            self.archetypes = list(archetypes)

        # Initialize players
        players: List[PlayerState] = []
        next_die_id = 1
        starting_cash_bonus = 1 if self.version_deck[0].directive_code == "DATA_SCRAPER" else 0

        for i, bot in enumerate(bots):
            ready_dice: List[Die] = []
            for _ in range(config.starting_gray_dice):
                ready_dice.append(create_gray_die(next_die_id))
                next_die_id += 1

            arch = self.archetypes[i] if i < len(self.archetypes) else None
            player = PlayerState(
                player_id=i,
                bot=bot,
                money=config.starting_money + starting_cash_bonus,
                secrets=self.config.get_starting_secrets(self.config.num_players),
                patches=self.config.get_starting_patches(self.config.num_players),
                ready_dice=ready_dice,
                archetype=arch,
                ability_v1_status=AbilityStatus.AVAILABLE,
                ability_v2_status=AbilityStatus.LOCKED,
                ability_v3_status=AbilityStatus.LOCKED,
            )
            players.append(player)

        # Initialize Market: 2 * num_players dice per colored die
        market_per_color = config.dice_per_color_multiplier * config.num_players
        market: Dict[DieColor, int] = {
            DieColor.RED: market_per_color,
            DieColor.BLUE: market_per_color,
            DieColor.GREEN: market_per_color,
            DieColor.YELLOW: market_per_color,
            DieColor.PURPLE: market_per_color,
        }

        # Staging Cup: payload from starting v1.0 card
        staging_cup: Dict[CubeColor, int] = {
            CubeColor.RED: 0,
            CubeColor.BLUE: 0,
            CubeColor.GREEN: 0,
            CubeColor.BLACK: 0,
        }
        for color, count in self.version_deck[0].get_staging_payload(self.config.num_players).items():
            staging_cup[color] = count

        # Setup First Player randomly per RULES.md Section 3 Step 4
        first_player_index = self.rng.randrange(config.num_players)

        self.state = GameState(
            config=config,
            players=players,
            market=market,
            variant_cards=self.variant_cards,
            version_deck=self.version_deck,
            staging_cup=staging_cup,
            first_player_index=first_player_index,
            contractor_supply=config.contractor_supply_total,
            next_die_id=next_die_id,
            rng=self.rng,
        )

        self._prime_compiler()

        self.telemetry_history: List[RoundTelemetry] = []

    def _prime_compiler(self) -> None:
        """Executes Setup compiler priming (Pre-Seed Drop) per RULES.md Section 3 Step 1."""
        if not self.config.enable_compiler_priming:
            return
        priming_cubes = dict(self.config.compiler_priming_cubes)
        exited = self.state.tower.drop(priming_cubes, self.rng)
        self.state.priming_exited_cubes = exited
        self.state.priming_stuck_cubes = self.state.tower.get_stuck_copy()

    def _execute_phase_1(self) -> List[Tuple[PlayerState, List[Die], Dict[int, ShieldColor]]]:
        return phase1_boot.execute_phase_1(self)

    def _apply_single_die_immediate_output(self, player: PlayerState, die: Die) -> None:
        phase1_boot.apply_single_die_immediate_output(self, player, die)

    def _apply_immediate_face_outputs(self, player: PlayerState) -> None:
        phase1_boot.apply_immediate_face_outputs(self, player)

    def _execute_phase_2(
        self,
        player_commitments: List[Tuple[PlayerState, List[Die], Dict[int, ShieldColor]]],
    ) -> RoundTelemetry:
        return phase2_threat.execute_phase_2(self, player_commitments)

    def _resolve_player_defense_and_wear(
        self,
        player: PlayerState,
        rolled_dice: List[Die],
        commitments: Dict[int, ShieldColor],
        attack_strengths: Dict[CubeColor, int],
        exited_cubes: Dict[CubeColor, int],
        active_directive: str,
    ) -> None:
        phase2_threat.resolve_player_defense_and_wear(
            self, player, rolled_dice, commitments, attack_strengths, exited_cubes, active_directive
        )

    def _execute_phase_3(self) -> None:
        phase3_ops.execute_phase_3(self)

    def run_round(self) -> RoundTelemetry:
        """Runs a single round of Rogue Agent."""
        if self.state.game_over:
            raise RuntimeError("Cannot run round on an already finished game")

        # Phase 1
        commitments = self._execute_phase_1()

        # Phase 2
        telemetry = self._execute_phase_2(commitments)

        # Phase 3 (skipped if game over triggered in Phase 2)
        if not self.state.game_over:
            self._execute_phase_3()
            if self.state.is_final_round:
                self.state.game_over = True
            else:
                self.state.current_round += 1
                if self.state.current_round > self.state.config.max_rounds:
                    self.state.game_over = True
                    self.state.end_reason = EndGameReason.ROUND_LIMIT

        return telemetry

    def run_game(self) -> EndGameResult:
        """Runs the game to completion and returns the final scoring and standings."""
        while not self.state.game_over:
            self.run_round()

        return self.evaluate_end_game()

    def evaluate_end_game(self) -> EndGameResult:
        """Calculates Portfolio Value, handles Patient Zero elimination or Total Wipeout overflow penalties."""
        return end_game.evaluate_end_game(self)
