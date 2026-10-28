"""GameController state machine adapter wrapping sim engine for Rogue Agent Web Playtesting."""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple

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
from sim.engine import EndGameResult, GameEngine, GameState, PlayerState
from sim.entities import (
    AbilityStatus,
    ArchetypeCard,
    ArchetypeCode,
    Die,
    VariantCard,
    VersionCard,
    create_colored_die,
    create_white_die,
    get_default_variant_cards,
    get_default_version_deck,
    get_random_archetypes,
    get_random_setup,
    get_random_variant_cards,
    get_random_version_deck,
)
from web.schemas import GameStateSerializer
from web.controller import (
    capabilities,
    phase1_actions,
    phase2_actions,
    phase3_actions,
    serializer,
)


class GameController:
    """Manages the full game lifecycle and turn execution state machine."""

    def __init__(self) -> None:
        self.engine: Optional[GameEngine] = None
        self.game_id: str = "match_1"
        self.phase: int = 1  # 1: Boot, 2: Compile, 3: Operations, 4: Game Over
        self.phase_name: str = "Boot & Configure"
        self.subphase: str = "waiting_for_roll"
        self.active_player_index: int = 0
        self.player_meta: Dict[int, Dict[str, Any]] = {}
        self.event_log: List[str] = []
        self.last_compile_result: Optional[Dict[str, Any]] = None
        self.final_result: Optional[Dict[str, Any]] = None
        self.phase3_turn_queue: List[int] = []

    @property
    def state(self) -> GameState:
        """Returns the underlying GameState."""
        if self.engine is None:
            raise RuntimeError("Game has not been initialized. Call new_game() first.")
        return self.engine.state

    def new_game(
        self,
        num_players: int = 4,
        players_config: Optional[List[Dict[str, Any]]] = None,
        seed: Optional[int] = None,
        variant_cards: Optional[Dict[DieColor, VariantCard]] = None,
        version_deck: Optional[List[VersionCard]] = None,
        randomize_cards: bool = False,
        archetypes: Optional[List[ArchetypeCard]] = None,
    ) -> Dict[str, Any]:
        """Creates and initializes a new game match."""
        if not (1 <= num_players <= 4):
            raise ValueError(f"Player count must be between 1 and 4, got {num_players}")

        config = GameConfig(num_players=num_players)
        rng = random.Random(seed)

        # Default bots pool
        bot_archetype_classes = [
            AdaptiveBalancedBot,
            SecOpsTurtleBot,
            VentureGreedBot,
            AccelerationistBot,
            RecklessSaboteurBot,
        ]

        bots: List[BaseBot] = []
        self.player_meta = {}

        for i in range(num_players):
            if players_config and i < len(players_config):
                cfg = players_config[i]
                is_human = bool(cfg.get("is_human", i == 0))
                name = cfg.get("name", f"Player {i + 1}" if is_human else f"Bot {i + 1}")
                archetype_name = cfg.get("bot_archetype")
            else:
                is_human = (i == 0)
                name = f"Player {i + 1}" if is_human else f"Bot {i + 1}"
                archetype_name = None

            # Instantiate bot instance for this player
            if archetype_name == "SecOpsTurtleBot":
                bot = SecOpsTurtleBot(i)
            elif archetype_name == "VentureGreedBot":
                bot = VentureGreedBot(i)
            elif archetype_name == "AccelerationistBot":
                bot = AccelerationistBot(i)
            elif archetype_name == "RecklessSaboteurBot":
                bot = RecklessSaboteurBot(i)
            elif archetype_name == "AdaptiveBalancedBot":
                bot = AdaptiveBalancedBot(i)
            else:
                bot_cls = bot_archetype_classes[(i - 1) % len(bot_archetype_classes)] if not is_human else AdaptiveBalancedBot
                bot = bot_cls(i)
                if not is_human:
                    archetype_name = bot.name

            bots.append(bot)
            self.player_meta[i] = {
                "name": name,
                "is_human": is_human,
                "bot_archetype": archetype_name if not is_human else None,
                "rolled_pool": [],
                "shield_slots": {"red": [], "blue": [], "green": []},
                "has_rolled": False,
                "has_committed": False,
                "commitments": {},
                "purchases_this_turn": 0,
                "dirty_income_taken_this_turn": False,
                "spent_from_kept": 0,
                "locked_reroll_indices": [],
            }

        if randomize_cards:
            setup_seed = (seed * 17) if seed is not None else None
            setup_rng = random.Random(setup_seed)
            if variant_cards is None and version_deck is None:
                variant_cards, version_deck = get_random_setup(setup_rng)
            else:
                if variant_cards is None:
                    variant_cards = get_random_variant_cards(setup_rng)
                if version_deck is None:
                    version_deck = get_random_version_deck(setup_rng)

        self.engine = GameEngine(
            config=config,
            bots=bots,
            seed=seed,
            variant_cards=variant_cards or get_default_variant_cards(),
            version_deck=version_deck or get_default_version_deck(),
            archetypes=archetypes,
        )

        variant_summary = ", ".join(v.code for v in self.state.variant_cards.values())
        self.event_log = [
            f"Game initialized with {num_players} corporations (Seed: {seed if seed is not None else 'auto'}).",
            f"Active Version: {self.state.active_version.name} ({self.state.active_version.version_str}).",
            f"Active Variants: {variant_summary}.",
            f"CISO badge awarded to {self.player_meta[self.state.first_player_index]['name']}.",
        ]
        for p in self.state.players:
            if p.archetype:
                p_name = self.player_meta[p.player_id]["name"]
                self.event_log.append(
                    f"{p_name} assigned Consultancy Archetype: {p.archetype.name} ({p.archetype.ability_name})."
                )
        self.last_compile_result = None
        self.final_result = None

        # Start Round 1 Phase 1
        self._start_phase_1()
        return self.get_full_state()

    def _start_phase_1(self) -> None:
        """Initializes Phase 1: Autonomous AI Corruption Pulse and resets player roll states."""
        self.phase = 1
        self.phase_name = "Boot & Configure"
        self.subphase = "waiting_for_roll"

        # 1. Autonomous AI Corruption Pulse per RULES.md Section 4 Phase 1 Step 1
        self.state.staging_cup[CubeColor.BLACK] = (
            self.state.staging_cup.get(CubeColor.BLACK, 0) + 1
        )
        self.event_log.append(
            f"Round {self.state.current_round} Phase 1: Autonomous AI Pulse added 1 Black Cube to Staging Cup."
        )

        # Reset per-round metadata for all players
        max_rerolls = (
            self.state.config.throttled_free_rerolls
            if self.state.active_directive_code == "POLYMORPHIC_WORM"
            else self.state.config.default_free_rerolls
        )

        for i, p in enumerate(self.state.players):
            meta = self.player_meta[i]
            meta["rolled_pool"] = []
            meta["shield_slots"] = {"red": [], "blue": [], "green": []}
            meta["has_rolled"] = False
            meta["has_committed"] = False
            meta["commitments"] = {}
            meta["purchases_this_turn"] = 0
            meta["dirty_income_taken_this_turn"] = False
            meta["spent_from_kept"] = 0
            meta["locked_reroll_indices"] = []
            meta["hired_contractors"] = 0
            meta["prodigy_active"] = False
            meta["rerolls_remaining"] = max_rerolls
            meta["max_rerolls"] = max_rerolls
            p.contractor_dice.clear()
            p.hired_contractor_count = 0

            # Reset star ability eligibility
            p.b2_available = False
            p.y1_available = False
            p.p1_available = False
            p.p3_available = None

        # If no human players exist, automatically resolve Phase 1
        if not any(meta["is_human"] for meta in self.player_meta.values()):
            self._auto_execute_bots_phase_1()
            self.phase = 2
            self.phase_name = "Rogue Agent Compile"
            self.subphase = "ready_for_compile"

    # =========================================================================
    # Phase 1: Boot & Configure (Interactive)
    # =========================================================================

    def hire_contractors(
        self,
        player_id: int,
        count: int = 1,
        use_operator_ability: bool = False,
        buy_third_die: bool = False,
    ) -> Dict[str, Any]:
        return phase1_actions.hire_contractors(self, player_id, count, use_operator_ability, buy_third_die)

    def roll_pool(self, player_id: int) -> Dict[str, Any]:
        return phase1_actions.roll_pool(self, player_id)

    def perform_reroll(
        self,
        player_id: int,
        reroll_indices: List[int],
        use_prodigy_ability: bool = False,
    ) -> Dict[str, Any]:
        return phase1_actions.perform_reroll(self, player_id, reroll_indices, use_prodigy_ability)

    def debug_unlock_die(self, player_id: int, die_index: int) -> Dict[str, Any]:
        return phase1_actions.debug_unlock_die(self, player_id, die_index)

    def hotfix_reroll(self, player_id: int, die_index: int) -> Dict[str, Any]:
        return phase1_actions.hotfix_reroll(self, player_id, die_index)

    def commit_defenses(
        self,
        player_id: int,
        commitments: Dict[int, ShieldColor | str],
        choice_declarations: Optional[Dict[int, int]] = None,
    ) -> Dict[str, Any]:
        return phase1_actions.commit_defenses(self, player_id, commitments, choice_declarations)

    def _auto_execute_bots_phase_1(self) -> None:
        phase1_actions.auto_execute_bots_phase_1(self)

    def compile_drop(self) -> Dict[str, Any]:
        return phase2_actions.compile_drop(self)

    def _advance_phase3_turns(self) -> None:
        phase3_actions.advance_phase3_turns(self)

    def _execute_bot_phase3(self, player: PlayerState, meta: Dict[str, Any]) -> None:
        phase3_actions.execute_bot_phase3(self, player, meta)

    def buy_die(
        self,
        player_id: int,
        color_str: str,
        use_cipher_ability: bool = False,
    ) -> Dict[str, Any]:
        return phase3_actions.buy_die(self, player_id, color_str, use_cipher_ability)

    def patch_die(self, player_id: int, die_index: int, use_cash: bool) -> Dict[str, Any]:
        return phase3_actions.patch_die(self, player_id, die_index, use_cash)

    def take_dirty_income(
        self,
        player_id: int,
        backlash_die_index: int = 0,
        use_cipher_ability: bool = False,
    ) -> Dict[str, Any]:
        return phase3_actions.take_dirty_income(self, player_id, backlash_die_index, use_cipher_ability)

    def use_phreaker_ability(self, player_id: int, count: int = 2) -> Dict[str, Any]:
        return phase3_actions.use_phreaker_ability(self, player_id, count)

    def use_acoustic_ability(self, player_id: int, chosen_color_str: str) -> Dict[str, Any]:
        return phase3_actions.use_acoustic_ability(self, player_id, chosen_color_str)

    def use_spook_ability(self, player_id: int, dollars: int) -> Dict[str, Any]:
        return phase3_actions.use_spook_ability(self, player_id, dollars)

    def execute_star_action(
        self,
        player_id: int,
        action_type: str,
        cube_color: Optional[str] = None,
    ) -> Dict[str, Any]:
        return phase3_actions.execute_star_action(self, player_id, action_type, cube_color)

    def end_turn(self, player_id: int) -> Dict[str, Any]:
        return phase3_actions.end_turn(self, player_id)

    def _complete_round(self) -> None:
        serializer.complete_round(self)

    def _serialize_end_game_result(self, res: EndGameResult) -> Dict[str, Any]:
        return serializer.serialize_end_game_result(self, res)

    def get_action_capabilities(self, player_id: int) -> Dict[str, Any]:
        return capabilities.get_action_capabilities(self, player_id)

    def get_full_state(self) -> Dict[str, Any]:
        return serializer.get_full_state(self)
