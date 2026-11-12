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
from sim.config import ROUND_PHASE_NAMES, CubeColor, DieColor, EndGameReason, GameConfig, RoundPhase, ResearchTrackModel, RoundSequence, ShieldColor
from sim.engine import EndGameResult, GameEngine, GameState, PlayerState
from sim.engine import research_tracks
from sim.engine import phase1_roll_deploy
from sim.engine.phase1_roll_deploy import check_and_execute_start_of_round_version_transition
from sim.entities import (
    AbilityStatus,
    ArchetypeCard,
    ArchetypeCode,
    CANONICAL_COMPANY_FOR_OPERATIVE,
    CANONICAL_OPERATIVE_FOR_COMPANY,
    COMPANIES,
    Company,
    CompanyCode,
    Die,
    VariantCard,
    VersionCard,
    WHITE_HATS,
    WhiteHat,
    WhiteHatCode,
    create_colored_die,
    create_white_die,
    get_all_companies,
    get_archetype_by_code,
    get_company_by_code,
    get_default_variant_cards,
    get_default_version_deck,
    get_random_archetypes,
    get_random_setup,
    get_random_variant_cards,
    get_random_version_deck,
    get_white_hat_by_code,
)
from web.schemas import GameStateSerializer
from web.controller import (
    capabilities,
    phase1_actions,
    phase2_actions,
    phase3_income_actions,
    phase4_attack_actions,
    phase5_pipeline_actions,
    phase6_operations_actions,
    serializer,
)

# Deprecated v0.33 module alias (kept one release)
from web.controller import phase3_actions  # noqa: E402,F401


WEB_DEFAULT_RULES_VERSION = "v0.38.0"
WEB_RULES_VERSIONS = ("v0.38.0", "v0.37.0")


class GameController:
    """Manages the full game lifecycle and the v0.34 six-phase turn state machine.

    Phases (``RoundPhase``): 1 Roll & Deploy, 2 Compiler Drop & Corruption, 3 Income,
    4 Attack Resolution, 5 CI/CD Pipeline Shift, 6 Operations, 7 Game Over. The web is SIX_PHASE only.
    """

    def __init__(self) -> None:
        self.engine: Optional[GameEngine] = None
        self.game_id: str = "match_1"
        self.phase: int = int(RoundPhase.ROLL_AND_DEPLOY)
        self.phase_name: str = ROUND_PHASE_NAMES[1]
        self.subphase: str = "waiting_for_roll"
        self.active_player_index: int = 0
        self.player_meta: Dict[int, Dict[str, Any]] = {}
        self.event_log: List[str] = []
        self.last_compile_result: Optional[Dict[str, Any]] = None
        self.last_income_result: Dict[int, Dict[str, Any]] = {}
        self.last_attack_result: Optional[Dict[str, Any]] = None
        self.last_pipeline_result: Dict[int, Dict[str, Any]] = {}
        self.last_round_bonus: Optional[Dict[str, Any]] = None
        self.pending_graduation: Dict[int, Dict[str, Any]] = {}
        self.final_result: Optional[Dict[str, Any]] = None
        self.operations_turn_queue: List[int] = []
        self.round_commitments: List[Any] = []
        self.compile_result: Any = None
        self.attack_strengths: Dict[CubeColor, int] = {}
        self.attack_resolved_pids: set = set()

    @property
    def phase3_turn_queue(self) -> List[int]:
        """Deprecated v0.33 alias of operations_turn_queue."""
        return self.operations_turn_queue

    @phase3_turn_queue.setter
    def phase3_turn_queue(self, value: List[int]) -> None:
        self.operations_turn_queue = value

    @property
    def rng(self) -> random.Random:
        return self.engine.rng

    @property
    def state(self) -> GameState:
        """Returns the underlying GameState."""
        if self.engine is None:
            raise RuntimeError("Game has not been initialized. Call new_game() first.")
        return self.engine.state

    @staticmethod
    def _build_config(num_players: int, enable_corporate_asymmetry: bool, research_track_model: Any,
                      rules_version: Optional[str]) -> GameConfig:
        """Web ruleset: v0.38.0 (``GameConfig.v038c()``) by default; ``"v0.37.0"`` keeps the previous rules.

        An explicit legacy ``research_track_model`` (the old ``ruleset`` field) selects the pre-v0.37 plain config.
        """
        common = dict(num_players=num_players, enable_corporate_asymmetry=enable_corporate_asymmetry,
                      round_sequence=RoundSequence.SIX_PHASE)  # the web is SIX_PHASE only (OQ-7)
        if research_track_model is not None:
            return GameConfig(research_track_model=research_track_model, max_market_purchases_per_turn=2, **common)
        version = str(rules_version or WEB_DEFAULT_RULES_VERSION).lower().lstrip("v")
        if version in ("041", "0.41.0", "0.41", "040", "0.40.0", "0.40", "0391", "0.39.1", "039", "0.39.0"):
            return GameConfig.v040(**common)
        if version in ("038f", "0.38f"):
            return GameConfig.v038f(**common)
        if version in ("038e", "0.38e"):
            return GameConfig.v038e(**common)
        if version in ("038d", "0.38d"):
            return GameConfig.v038d(**common)
        if version in ("0.38.0", "0.38", "038c"):
            return GameConfig.v038c(**common)
        if version in ("0.37.0", "0.37"):
            return GameConfig.v037(research_track_model=ResearchTrackModel.V035_FIVE_LEVEL, **common)
        raise ValueError(f"Unknown rules_version {rules_version!r}; expected 'v0.38.0' or 'v0.37.0'")

    def new_game(
        self,
        num_players: int = 4,
        players_config: Optional[List[Dict[str, Any]]] = None,
        seed: Optional[int] = None,
        variant_cards: Optional[Dict[DieColor, VariantCard]] = None,
        version_deck: Optional[List[VersionCard]] = None,
        randomize_cards: bool = False,
        archetypes: Optional[List[ArchetypeCard]] = None,
        companies: Optional[List[Company]] = None,
        white_hats: Optional[List[WhiteHat]] = None,
        enable_corporate_asymmetry: bool = True,
        research_track_model: Any = None,
        rules_version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Creates and initializes a new game match."""
        if not (1 <= num_players <= 4):
            raise ValueError(f"Player count must be between 1 and 4, got {num_players}")

        config = self._build_config(num_players, enable_corporate_asymmetry, research_track_model, rules_version)
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
                "upgrades_this_turn": 0,
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

        # Resolve companies and white hats if provided or configured
        resolved_companies: Optional[List[Company]] = None
        resolved_white_hats: Optional[List[WhiteHat]] = None

        if companies is not None:
            resolved_companies = list(companies)
            if white_hats is not None:
                resolved_white_hats = list(white_hats)
            else:
                resolved_white_hats = [
                    WHITE_HATS[CANONICAL_OPERATIVE_FOR_COMPANY[c.code]] if c else None
                    for c in resolved_companies
                ]
        elif players_config and any(
            isinstance(cfg, dict) and (cfg.get("company") or cfg.get("company_code"))
            for cfg in players_config
        ):
            resolved_companies = [None] * num_players
            resolved_white_hats = [None] * num_players
            used_company_codes = set()

            for i in range(min(num_players, len(players_config))):
                cfg = players_config[i]
                if not isinstance(cfg, dict):
                    continue
                c_val = cfg.get("company") or cfg.get("company_code")
                if c_val and str(c_val).upper() != "RANDOM":
                    comp = get_company_by_code(c_val)
                    resolved_companies[i] = comp
                    used_company_codes.add(comp.code)

                    wh_val = cfg.get("white_hat") or cfg.get("white_hat_code")
                    if wh_val:
                        resolved_white_hats[i] = get_white_hat_by_code(wh_val)
                    else:
                        resolved_white_hats[i] = WHITE_HATS[CANONICAL_OPERATIVE_FOR_COMPANY[comp.code]]

            setup_rng = random.Random((seed * 31) if seed is not None else None)
            remaining_comps = [c for c in get_all_companies() if c.code not in used_company_codes]
            setup_rng.shuffle(remaining_comps)
            for i in range(num_players):
                if resolved_companies[i] is None:
                    comp = remaining_comps.pop(0)
                    resolved_companies[i] = comp
                    resolved_white_hats[i] = WHITE_HATS[CANONICAL_OPERATIVE_FOR_COMPANY[comp.code]]

        self.engine = GameEngine(
            config=config,
            bots=bots,
            seed=seed,
            variant_cards=variant_cards or get_default_variant_cards(),
            version_deck=version_deck or get_default_version_deck(),
            archetypes=archetypes,
            companies=resolved_companies,
            white_hats=resolved_white_hats,
        )

        variant_summary = ", ".join(v.code for v in self.state.variant_cards.values())
        priming_stuck_total = sum(self.state.priming_stuck_cubes.values())
        self.event_log = [
            f"Game initialized with {num_players} White Hat Operatives (Seed: {seed if seed is not None else 'auto'}).",
            f"Compiler Primed: {priming_stuck_total} cubes lodged on internal baffles.",
            f"Active Version: {self.state.active_version.name} ({self.state.active_version.version_str}).",
            f"Active Variants: {variant_summary}.",
            f"First Player Marker awarded to {self.player_meta[self.state.first_player_index]['name']}.",
        ]
        for p in self.state.players:
            p_name = self.player_meta[p.player_id]["name"]
            if p.company:
                bonuses = []
                if not config.company_setup_bonuses:
                    wh_str = f" / {p.white_hat.name}" if p.white_hat else ""
                    self.event_log.append(
                        f"{p_name} contracted with {p.company.name} ({p.company.override_name}){wh_str}."
                    )
                    continue
                starting_cash_bonus = 1 if self.state.active_directive_code == "DATA_SCRAPER" else 0
                if p.money > config.starting_money + starting_cash_bonus:
                    bonuses.append(f"+${p.company.starting_cash_bonus} Cash")
                if p.patches > 0:
                    bonuses.append(f"+{p.patches} 🔬 Research")
                if p.secrets > config.get_starting_secrets(num_players):
                    bonuses.append(f"+{p.company.starting_secrets_bonus} Secret")
                if getattr(p, "patent_level", 0) > 0:
                    bonuses.append(f"Patent Lvl {p.patent_level}")
                if getattr(p, "defense_level", 0) > 0:
                    bonuses.append(f"Defense Lvl {p.defense_level} [Cap {p.defense_capacity}]")
                if getattr(p, "triage_level", 0) > 0 or getattr(p, "release_level", 0) > 0:
                    bonuses.append(f"Triage Lvl {p.triage_level}, Release Lvl {p.release_level}")
                if getattr(p, "upgrade_discount", 0) > 0:
                    bonuses.append(f"-{p.upgrade_discount} 🔬 Track Upgrade Discount")
                bonus_str = f" [{', '.join(bonuses)}]" if bonuses else ""
                wh_str = f" / {p.white_hat.name}" if p.white_hat else ""
                self.event_log.append(
                    f"{p_name} contracted with {p.company.name} ({p.company.override_name}){wh_str}{bonus_str}."
                )
            elif p.archetype:
                self.event_log.append(
                    f"{p_name} assigned White Hat Operative: {p.archetype.name} ({p.archetype.ability_name})."
                )
        self.last_compile_result = None
        self.last_income_result = {}
        self.last_attack_result = None
        self.last_pipeline_result = {}
        self.last_round_bonus = None
        self.pending_graduation = {}
        self.pending_breakthrough = {}
        self.final_result = None

        # Start Round 1 Phase 1
        self._start_phase_1()
        return self.get_full_state()

    def _start_phase_1(self) -> None:
        """Initializes Phase 1 (Roll & Deploy): Autonomous AI Corruption Pulse and resets player roll states."""
        self.phase = int(RoundPhase.ROLL_AND_DEPLOY)
        self.phase_name = ROUND_PHASE_NAMES[self.phase]
        self.subphase = "waiting_for_roll"
        self.round_commitments = []
        self.compile_result = None
        self.attack_resolved_pids = set()
        self.last_round_bonus = None

        # Start-of-round version switch execution (INV-VER-SWITCH-01)
        check_and_execute_start_of_round_version_transition(self.engine)

        # 1. Autonomous AI Corruption Pulse per RULES.md Section 4 Phase 1 Step 1 (engine baseline per version)
        active_ver = self.state.active_version.version_str
        pulse = self.state.config.autonomous_pulse_by_version.get(active_ver, 1)
        self.state.staging_cup[CubeColor.BLACK] = (
            self.state.staging_cup.get(CubeColor.BLACK, 0) + pulse
        )
        self.event_log.append(
            f"Round {self.state.current_round} Phase 1: Autonomous AI Pulse added {pulse} Black Cube to Staging Cup."
        )

        # Promote pending next phase locks
        self.state.active_phase1_locks = set(self.state.pending_next_phase_locks)
        self.state.pending_next_phase_locks.clear()
        if self.state.active_phase1_locks:
            self.event_log.append(
                f"Phase 1 Corruption Locks active this round: {sorted(self.state.active_phase1_locks)}."
            )

        # v0.38 round-start flags (Red Secret banked flag, per-round Blue block / slot counters)
        phase1_roll_deploy.round_start_hooks(self.engine)

        # Reset per-round metadata for all players
        for i, p in enumerate(self.state.players):
            max_rerolls = research_tracks.free_rerolls_for(self.state.config, p, self.state.config.default_free_rerolls)
            meta = self.player_meta[i]
            meta["rolled_pool"] = []
            meta["shield_slots"] = {"red": [], "blue": [], "green": []}
            meta["has_rolled"] = False
            meta["has_committed"] = False
            meta["commitments"] = {}
            meta["purchases_this_turn"] = 0
            meta["upgrades_this_turn"] = 0
            meta["dirty_income_taken_this_turn"] = False
            meta["spent_from_kept"] = 0
            meta["locked_reroll_indices"] = []
            meta["hired_contractors"] = 0
            meta["prodigy_active"] = False
            meta["helix_override_used"] = False
            meta["ace_uses"] = 0
            meta["rerolls_remaining"] = max_rerolls
            meta["max_rerolls"] = max_rerolls
            # Contractors expired at the end of Phase 4; any still held are Triage L1 Breakthrough
            # contractors gained in Phase 6, which roll this round (v0.35.0).
            p.hired_contractor_count = 0

            # Reset star ability eligibility
            p.b2_available = False
            p.r2_actions_available = 0  # v0.36.0 Ad Campaign (earned in Phase 3)
            p.y1_available = False
            p.p1_available = False
            p.p3_available = None

        # If no human players exist, automatically resolve Phase 1
        if not any(meta["is_human"] for meta in self.player_meta.values()):
            self._auto_execute_bots_phase_1()
            self.phase = int(RoundPhase.COMPILER_DROP_AND_CORRUPTION)
            self.phase_name = ROUND_PHASE_NAMES[self.phase]
            self.subphase = "ready_for_compile"

    # =========================================================================
    # Phase 1: Roll & Deploy (Interactive)
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
        slot_cleaner_indices: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        return phase1_actions.commit_defenses(self, player_id, commitments, choice_declarations, slot_cleaner_indices)

    def override_face(self, player_id: int, die_index: int, face_index: int, source: str = "helix") -> Dict[str, Any]:
        return phase1_actions.override_face(self, player_id, die_index, face_index, source)

    def _auto_execute_bots_phase_1(self) -> None:
        phase1_actions.auto_execute_bots_phase_1(self)

    def compile_drop(self) -> Dict[str, Any]:
        return phase2_actions.compile_drop(self)

    def _advance_operations_turns(self) -> None:
        phase6_operations_actions.advance_operations_turns(self)

    _advance_phase3_turns = _advance_operations_turns  # deprecated v0.33 name

    def _execute_bot_operations(self, player: PlayerState, meta: Dict[str, Any]) -> None:
        phase6_operations_actions.execute_bot_operations(self, player, meta)

    _execute_bot_phase3 = _execute_bot_operations  # deprecated v0.33 name

    def buy_die(
        self,
        player_id: int,
        color_str: str,
        use_cipher_ability: bool = False,
    ) -> Dict[str, Any]:
        return phase6_operations_actions.buy_die(self, player_id, color_str, use_cipher_ability)

    def patch_die(self, player_id: int, die_index: int, use_cash: bool) -> Dict[str, Any]:
        return phase6_operations_actions.patch_die(self, player_id, die_index, use_cash)

    def take_dirty_income(
        self,
        player_id: int,
        backlash_die_index: int = 0,
        use_cipher_ability: bool = False,
        backlash_die_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        return phase6_operations_actions.take_dirty_income(
            self,
            player_id,
            backlash_die_index,
            use_cipher_ability,
            backlash_die_id=backlash_die_id,
        )

    def use_cipher_ability(self, player_id: int) -> Dict[str, Any]:
        return phase6_operations_actions.take_cipher_arbitrage(self, player_id)

    def use_phreaker_ability(
        self,
        player_id: int,
        count: int = 1,
        die_index: int = 0,
        die_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        return phase6_operations_actions.use_phreaker_ability(
            self,
            player_id,
            count=count,
            die_index=die_index,
            die_id=die_id,
        )

    def use_acoustic_ability(self, player_id: int, chosen_color_str: str) -> Dict[str, Any]:
        return phase6_operations_actions.use_acoustic_ability(self, player_id, chosen_color_str)

    def use_spook_ability(self, player_id: int, dollars: int) -> Dict[str, Any]:
        return phase6_operations_actions.use_spook_ability(self, player_id, dollars)

    def spook_burn(self, player_id: int, die_id: int) -> Dict[str, Any]:
        return phase6_operations_actions.spook_burn(self, player_id, die_id)

    def phreaker_diagnostics(self, player_id: int, die_id: Optional[int] = None) -> Dict[str, Any]:
        return phase6_operations_actions.phreaker_diagnostics(self, player_id, die_id)

    def execute_star_action(
        self,
        player_id: int,
        action_type: str,
        cube_color: Optional[str] = None,
    ) -> Dict[str, Any]:
        return phase6_operations_actions.execute_star_action(self, player_id, action_type, cube_color)

    def confirm_income(
        self,
        player_id: int,
        spook_burn_die_id: Optional[Any] = None,
        phreaker_die_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Phase 3: Income."""
        return phase3_income_actions.confirm_income(
            self, player_id, spook_burn_die_id=spook_burn_die_id, phreaker_die_id=phreaker_die_id
        )

    def capital_injection(self, player_id: int) -> Dict[str, Any]:
        """Phase 3: Meridian Financial Trust Capital Injection (+3 $)."""
        return phase3_income_actions.capital_injection(self, player_id)


    def confirm_attacks(
        self,
        player_id: int,
        any_shield_allocations: Optional[Dict[str, int]] = None,
        glitch_die_ids: Optional[List[int]] = None,
        aegis_color: Optional[str] = None,
        use_slush_fund: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Phase 4: Attack Resolution."""
        return phase4_attack_actions.confirm_attacks(
            self, player_id, any_shield_allocations=any_shield_allocations,
            glitch_die_ids=glitch_die_ids, aegis_color=aegis_color, use_slush_fund=use_slush_fund,
        )

    def choose_graduates(
        self,
        player_id: int,
        graduate_die_ids: Optional[List[int]] = None,
        splice_die_id: Optional[int] = None,
        hotfix_die_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Phase 5: CI/CD Pipeline Shift (Scanned Graduation choice)."""
        return phase5_pipeline_actions.choose_graduates(
            self, player_id, graduate_die_ids, splice_die_id=splice_die_id, hotfix_die_id=hotfix_die_id
        )

    def end_turn(self, player_id: int) -> Dict[str, Any]:
        return phase6_operations_actions.end_turn(self, player_id)

    def fast_patch(
        self,
        player_id: int,
        die_ids: Optional[List[int]] = None,
        die_indices: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        return phase6_operations_actions.fast_patch(self, player_id, die_ids=die_ids, die_indices=die_indices)

    def upgrade_track(self, player_id: int, track_type: str) -> Dict[str, Any]:
        return phase6_operations_actions.upgrade_hardware_track(self, player_id, track_type)

    upgrade_hardware_track = upgrade_track

    def file_patent(self, player_id: int) -> Dict[str, Any]:
        return phase6_operations_actions.file_cryptographic_patent(self, player_id)

    def regain_market_share(self, player_id: int) -> Dict[str, Any]:
        return phase6_operations_actions.regain_market_share(self, player_id)

    def resolve_breakthrough(
        self,
        player_id: int,
        accept: bool = True,
        gray_die_id: Optional[int] = None,
        color: Optional[str] = None,
    ) -> Dict[str, Any]:
        return phase6_operations_actions.resolve_pending_breakthrough(
            self, player_id, accept=accept, gray_die_id=gray_die_id, color=color
        )

    def system_reboot(self, player_id: int) -> Dict[str, Any]:
        return phase6_operations_actions.system_reboot(self, player_id)

    def _complete_round(self) -> None:
        serializer.complete_round(self)

    def _serialize_end_game_result(self, res: EndGameResult) -> Dict[str, Any]:
        return serializer.serialize_end_game_result(self, res)

    def get_action_capabilities(self, player_id: int) -> Dict[str, Any]:
        return capabilities.get_action_capabilities(self, player_id)

    def get_full_state(self) -> Dict[str, Any]:
        return serializer.get_full_state(self)
