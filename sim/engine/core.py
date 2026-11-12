"""GameEngine orchestrator coordinating game loops and phases."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple

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
    ArchetypeCode,
    Company,
    CompanyCode,
    WhiteHat,
    WhiteHatCode,
    COMPANIES,
    WHITE_HATS,
    INTRODUCTORY_PRESETS,
    CANONICAL_COMPANY_FOR_OPERATIVE,
    CANONICAL_OPERATIVE_FOR_COMPANY,
    Die,
    Face,
    VariantCard,
    VersionCard,
    create_colored_die,
    create_gray_die,
    create_white_die,
    get_all_archetype_cards,
    get_archetype_by_code,
    get_default_variant_cards,
    get_default_version_deck,
    get_random_archetypes,
    get_random_companies,
    get_random_white_hats,
    resolve_variant_cards,
    apply_variant_profile,
)
from sim.tower import CubeTower
from sim.engine.state import CompileResult, EndGameResult, GameState, PlayerState, RoundTelemetry
from sim.engine import (
    end_game,
    legacy_v033,
    phase1_roll_deploy,
    phase2_compiler,
    phase3_income,
    phase4_attack_resolution,
    phase5_pipeline_shift,
    phase6_operations,
)

from sim.engine import phase2_threat, phase3_ops  # noqa: F401,E402  (v0.33 shim modules, kept importable)

# Backward-compatible module aliases (v0.33 names)
phase1_boot = phase1_roll_deploy


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
        companies: Optional[List[Company]] = None,
        white_hats: Optional[List[WhiteHat]] = None,
        use_introductory_presets: bool = False,
    ) -> None:
        if bots is None:
            bots = [AdaptiveBalancedBot(i) for i in range(config.num_players)]
        elif len(bots) != config.num_players:
            raise ValueError(f"Bot count ({len(bots)}) must match config.num_players ({config.num_players})")

        self.rng = random.Random(seed)
        self.config = config
        self.variant_cards = resolve_variant_cards(variant_cards or get_default_variant_cards(), config.red_variant_set)
        self.variant_cards = apply_variant_profile(self.variant_cards, config.variant_profile)  # v0.38 (§5)
        self.version_deck = version_deck or get_default_version_deck(profile=config.corruption_track_profile)

        # Modular Setup Resolution (INV-SETUP-01..04)
        if use_introductory_presets and config.num_players in INTRODUCTORY_PRESETS:
            preset = INTRODUCTORY_PRESETS[config.num_players]
            self.companies = [COMPANIES[c] for c, _ in preset]
            self.white_hats = [WHITE_HATS[w] for _, w in preset]
            self.archetypes = [get_archetype_by_code(wh.code.value) for wh in self.white_hats]
        elif companies is not None and white_hats is not None:
            self.companies = list(companies)
            self.white_hats = list(white_hats)
            self.archetypes = [get_archetype_by_code(wh.code.value) for wh in self.white_hats]
        elif companies is not None:
            self.companies = list(companies)
            self.white_hats = []
            for comp in self.companies:
                if comp is not None:
                    c_code = comp.code if isinstance(comp.code, CompanyCode) else CompanyCode(comp.code)
                    wh_code = CANONICAL_OPERATIVE_FOR_COMPANY[c_code]
                    self.white_hats.append(WHITE_HATS[wh_code])
                else:
                    self.white_hats.append(None)
            self.archetypes = [get_archetype_by_code(wh.code.value) if wh else None for wh in self.white_hats]
        elif archetypes is not None:
            self.companies = []
            self.white_hats = []
            for arch in archetypes:
                if arch is not None:
                    legacy_code = arch.code if isinstance(arch.code, ArchetypeCode) else ArchetypeCode(arch.code)
                    wh_code = WhiteHatCode(legacy_code.value)
                    self.companies.append(COMPANIES[CANONICAL_COMPANY_FOR_OPERATIVE[wh_code]])
                    self.white_hats.append(WHITE_HATS[wh_code])
                else:
                    self.companies.append(None)
                    self.white_hats.append(None)
            self.archetypes = list(archetypes)
        else:
            arch_sample = get_random_archetypes(config.num_players, self.rng)
            self.archetypes = arch_sample
            self.companies = []
            self.white_hats = []
            for arch in arch_sample:
                legacy_code = arch.code if isinstance(arch.code, ArchetypeCode) else ArchetypeCode(arch.code)
                wh_code = WhiteHatCode(legacy_code.value)
                self.companies.append(COMPANIES[CANONICAL_COMPANY_FOR_OPERATIVE[wh_code]])
                self.white_hats.append(WHITE_HATS[wh_code])

        # Initialize players
        players: List[PlayerState] = []
        next_die_id = 1
        starting_cash_bonus = 1 if self.version_deck[0].directive_code == "DATA_SCRAPER" else 0

        company_dice_taken: Dict[DieColor, int] = {}
        for i, bot in enumerate(bots):
            ready_for_release_dice: List[Die] = []
            comp_for_die = self.companies[i] if i < len(self.companies) else None
            company_color: Optional[DieColor] = None
            if config.company_starting_die_enabled and comp_for_die is not None:
                company_color = DieColor(config.company_starting_colors[comp_for_die.code.value].lower())
            # 1. Add 3 Gray Legacy Dice (INV-START-POOL-01); v0.38: one fewer when a Company starting die replaces it
            for _ in range(config.starting_gray_dice - (1 if company_color is not None else 0)):
                ready_for_release_dice.append(create_gray_die(next_die_id, config.gray_face_profile))
                next_die_id += 1
            # 1b. v0.38 Company starting die (after Grays, before Purple; from the Central Market supply, OQ-5)
            if company_color is not None:
                ready_for_release_dice.append(create_colored_die(
                    color=company_color, die_id=next_die_id, variant_card=self.variant_cards.get(company_color),
                    face_profile=config.die_face_profile,
                ))
                next_die_id += 1
                company_dice_taken[company_color] = company_dice_taken.get(company_color, 0) + 1

            # 2. Add 1 Purple Proprietary Specialist Die (INV-START-POOL-01)
            wh = self.white_hats[i] if i < len(self.white_hats) else None
            purple_reserve_cost = wh.reserve_cost if wh else 4
            starter_purple = create_colored_die(
                color=DieColor.PURPLE,
                die_id=next_die_id,
                reserve_cost=purple_reserve_cost,
                cost=0,
                face_profile=config.die_face_profile,
            )
            ready_for_release_dice.append(starter_purple)
            next_die_id += 1

            comp = self.companies[i] if i < len(self.companies) else None
            # v0.35.0: Client Company setup bonuses are removed (INV-RT-FLAT-SETUP-01)
            use_asym = getattr(config, "enable_corporate_asymmetry", False) and getattr(config, "company_setup_bonuses", True)
            comp_cash = getattr(comp, "starting_cash_bonus", 0) if (comp and use_asym) else 0
            comp_res = getattr(comp, "starting_research_bonus", 0) if (comp and use_asym) else 0
            comp_sec = getattr(comp, "starting_secrets_bonus", 0) if (comp and use_asym) else 0
            player = PlayerState(
                player_id=i,
                bot=bot,
                money=config.starting_money + starting_cash_bonus + comp_cash,
                secrets=self.config.get_starting_secrets(self.config.num_players) + comp_sec,
                patches=self.config.get_starting_patches(self.config.num_players) + comp_res,
                ready_for_release_dice=ready_for_release_dice,
                company=comp,
                white_hat=wh,
                personal_purple_reserve=getattr(config, "starting_purple_reserve", 1),
                ability_v1_status=AbilityStatus.AVAILABLE,
                ability_v2_status=AbilityStatus.LOCKED,
                ability_v3_status=AbilityStatus.LOCKED,
                defense_capacity=comp.starting_defense_capacity if (comp and use_asym) else 2,
                triage_bandwidth=comp.starting_triage_bandwidth if (comp and use_asym) else 2,
                release_bandwidth=comp.starting_release_bandwidth if (comp and use_asym) else 4,
                triage_level=comp.starting_triage_level if (comp and use_asym) else 0,
                release_level=comp.starting_release_level if (comp and use_asym) else 0,
                pipeline_level=comp.starting_triage_level if (comp and use_asym) else 0,
                defense_level=comp.starting_defense_level if (comp and use_asym) else 0,
                patent_level=comp.starting_patent_level if (comp and use_asym) else 0,
                upgrade_discount=comp.upgrade_discount if (comp and use_asym) else 0,
                config=config,
            )
            if config.is_market_share:
                start_ms = config.market_share_start(config.num_players)
                max_ms = config.get_market_share_max(config.num_players)
                player.init_market_share(start=start_ms, max_share=max_ms)
            if config.secret_face_enabled:
                player.secrets_by_source["starting"] = player.secrets
                player.company_color = company_color.value if company_color is not None else None
            if config.glitched_shield_slots_enabled:
                start_g = int(getattr(config, "starting_glitched_shield_slots", 0))
                player.glitched_shield_slots = start_g
                player.max_glitched_slots = start_g
                if start_g > 0:
                    player.slots_glitched_by_source["setup"] = start_g
            players.append(player)

        # Initialize Market: 2 * num_players dice per colored die (INV-PURPLE-02: Purple excluded from Central Market)
        market_per_color = config.dice_per_color_multiplier * config.num_players
        market: Dict[DieColor, int] = {
            DieColor.RED: market_per_color,
            DieColor.BLUE: market_per_color,
            DieColor.GREEN: market_per_color,
            DieColor.YELLOW: market_per_color,
        }
        for color, n in company_dice_taken.items():
            market[color] -= n  # v0.38: Company starting dice come from the Central Market supply

        # Staging Cup: payload from starting v1.0 card
        staging_cup: Dict[CubeColor, int] = {
            CubeColor.RED: 0,
            CubeColor.BLUE: 0,
            CubeColor.GREEN: 0,
            CubeColor.BLACK: 0,
        }
        v1_code = self.version_deck[0].directive_code
        payload_override = getattr(self.config, "v1_staging_payload_override", None)
        if payload_override and (v1_code in payload_override or self.version_deck[0].name.upper().replace(" ", "_") in payload_override):
            staging_payload = payload_override.get(v1_code) or payload_override[self.version_deck[0].name.upper().replace(" ", "_")]
        else:
            staging_payload = self.version_deck[0].get_staging_payload(self.config.num_players)
        for color, count in staging_payload.items():
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
        self.state.first_player_index_start = first_player_index

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
        return phase1_roll_deploy.execute_phase_1(self)

    def _apply_single_die_immediate_output(self, player: PlayerState, die: Die) -> None:
        phase1_roll_deploy.apply_single_die_immediate_output(self, player, die)

    def _apply_immediate_face_outputs(self, player: PlayerState) -> None:
        phase1_roll_deploy.apply_immediate_face_outputs(self, player)

    def _execute_phase_2(
        self,
        player_commitments: List[Tuple[PlayerState, List[Die], Dict[int, ShieldColor]]],
        defer_green_for_pids: Optional[Set[int]] = None,  # Deprecated v0.34; remove in v0.35
    ) -> RoundTelemetry:
        """Legacy v0.33 façade (INV-SEQ-SHIM-LEGACY-01): always v0.33 semantics."""
        return legacy_v033.execute_phase_2_v033(self, player_commitments, defer_green_for_pids=defer_green_for_pids)

    def _resolve_player_defense_and_wear(
        self,
        player: PlayerState,
        rolled_dice: List[Die],
        commitments: Dict[int, ShieldColor],
        attack_strengths: Dict[CubeColor, int],
        exited_cubes: Dict[CubeColor, int],
        active_directive: str,
    ) -> None:
        phase4_attack_resolution.resolve_player_defense_and_wear(
            self, player, rolled_dice, commitments, attack_strengths, exited_cubes, active_directive
        )

    def _execute_phase_3(self) -> None:
        """Legacy v0.33 façade (INV-SEQ-SHIM-LEGACY-01): always v0.33 semantics."""
        legacy_v033.execute_phase_3_v033(self)

    # ------------------------------------------------------------------
    # v0.34.0 Six-Phase steps
    # ------------------------------------------------------------------
    def _run_phase_2_compiler(self, commitments) -> CompileResult:
        cr = phase2_compiler.execute_compiler_drop(self, commitments)
        phase2_compiler.check_end_triggers_after_compiler(self, cr)
        return cr

    def _run_phase_3_income(self, commitments):
        return phase3_income.execute_income(self, commitments)

    def _run_phase_4_attack_resolution(self, commitments, cr: CompileResult) -> Dict[CubeColor, int]:
        return phase4_attack_resolution.execute_attack_resolution(self, commitments, cr)

    def _run_phase_5_pipeline_shift(self):
        return phase5_pipeline_shift.execute_pipeline_shift(self)

    def _run_phase_6_operations(self) -> None:
        phase6_operations.execute_operations(self)

    def _snapshot_players(self) -> List[Dict]:
        return [
            {
                "player_id": p.player_id,
                "bot_name": p.bot.name,
                "money": p.money,
                "secrets": p.secrets,
                "patches": p.patches,
                "ready_dice_count": len(p.ready_for_release_dice),
                "in_production_dice_count": len(p.in_production_dice),
                "glitched_dice_count": len(p.glitched_dice),
                "scanned_dice_count": len(p.scanned_dice),
                "unpatched_dice_count": len(p.glitched_dice) + len(p.scanned_dice),
                "contractor_dice_count": len(p.contractor_dice),
                "is_patient_zero": p.is_patient_zero,
                # v0.36.0: only under MARKET_SHARE so default snapshots stay byte-identical
                **({"market_share": p.market_share} if self.config.is_market_share else {}),
            }
            for p in self.state.players
        ]

    def _begin_telemetry(self, cr: CompileResult) -> RoundTelemetry:
        return RoundTelemetry(
            round_number=self.state.current_round,
            active_version_name=self.state.active_version.name,
            corruption_track=self.state.corruption_track,
            staged_cubes=cr.staged_before,
            stuck_cubes_before=cr.stuck_before,
            exited_cubes=cr.exited_cubes,
            stuck_cubes_after=cr.stuck_after,
            attack_strengths={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            player_snapshots=[],
            buffer_overflow=cr.buffer_overflow,
            round_sequence=self.config.round_sequence.value,
            phases_executed=[1, 2],
        )

    def _begin_research_telemetry(self) -> None:
        self._research_round_start = {
            p.player_id: (
                p.research_earned_total,
                len(p.breakthroughs),
                getattr(p, "rejected_purple_purchases", 0),
                getattr(p, "excess_hardware_upgrades_requested", 0),
            )
            for p in self.state.players
        }
        for p in self.state.players:
            p.track_upgrades_this_round = []
        self._ms_round_start = {
            "players": {p.player_id: self._ms_counters(p) for p in self.state.players},
            "r3": len(self.state.r3_events),
            "cmp": len(self.state.version_comparisons),
            "triggers": len(self.state.end_triggers),
        }

    @staticmethod
    def _ms_counters(p: PlayerState) -> Dict[str, Any]:
        return {
            "incoming": p.red_incoming_total, "blocked_color": p.red_blocked_color_total,
            "blocked_any": p.red_blocked_any_total, "unblocked": p.red_unblocked_total,
            "share_lost": p.market_share_lost_red, "overflow": p.market_share_red_overflow,
            "regain_count": p.market_share_regained, "regain_research": p.research_spent_regain,
            "r2": p.market_share_gained_r2, "purchases": dict(p.purchases_by_color),
        }

    def _record_market_share_telemetry(self, tel: RoundTelemetry) -> None:
        """v0.36.0 per-round Market Share / Red telemetry (spec §6.1). Telemetry only."""
        start = getattr(self, "_ms_round_start", None)
        if start is None:
            return
        s = self.state
        ms = self.config.is_market_share
        from sim.engine import research_tracks

        for p in s.players:
            c0 = start["players"].get(p.player_id) or self._ms_counters(p)
            c1 = self._ms_counters(p)
            tel.red_by_player[p.player_id] = {
                k: c1[k] - c0[k] for k in ("incoming", "blocked_color", "blocked_any", "unblocked", "share_lost", "overflow")
            }
            tel.purchases_by_player[p.player_id] = {
                k: v - c0["purchases"].get(k, 0) for k, v in c1["purchases"].items() if v - c0["purchases"].get(k, 0)
            }
            if ms:
                cost, cap = research_tracks.regain_rate(self.config, p)
                tel.regain_by_player[p.player_id] = {
                    "count": c1["regain_count"] - c0["regain_count"],
                    "research": c1["regain_research"] - c0["regain_research"],
                    "cap": cap, "level": p.patent_level,
                }
                tel.r2_by_player[p.player_id] = c1["r2"] - c0["r2"]
                tel.market_share_end_of_round[p.player_id] = p.market_share
        tel.r3_events = [dict(e) for e in s.r3_events[start["r3"]:]]
        tel.version_comparisons = [r.as_dict() for r in s.version_comparisons[start["cmp"]:]]
        tel.end_triggers_this_round = list(s.end_triggers[start["triggers"]:])

    def _record_research_telemetry(self, tel: RoundTelemetry) -> None:
        start = getattr(self, "_research_round_start", None)
        if start is None:
            return
        self._record_market_share_telemetry(tel)
        for p in self.state.players:
            earned0, bt0, rej0, excess0 = start.get(p.player_id, (0, 0, 0, 0))
            tel.research_gained_by_player[p.player_id] = p.research_earned_total - earned0
            tel.track_upgrades_by_player[p.player_id] = list(getattr(p, "track_upgrades_this_round", []))
            tel.breakthroughs_by_player[p.player_id] = [b.as_dict() for b in p.breakthroughs[bt0:]]
            tel.rejected_purple_purchases_by_player[p.player_id] = getattr(p, "rejected_purple_purchases", 0) - rej0
            tel.excess_hardware_upgrades_by_player[p.player_id] = getattr(p, "excess_hardware_upgrades_requested", 0) - excess0

    def _finalize_telemetry(self, tel: RoundTelemetry, end_phase: Optional[int]) -> RoundTelemetry:
        self._record_research_telemetry(tel)
        tel.final_round_trigger_phase = self.state.final_round_trigger_phase
        tel.end_phase = end_phase
        self.telemetry_history.append(tel)  # exactly once per round (INV-SEQ-TELEMETRY-01)
        return tel

    def run_round(self) -> RoundTelemetry:
        """Runs a single round of Rogue Agent (six-phase by default; legacy v0.33 behind the flag)."""
        if self.state.game_over:
            raise RuntimeError("Cannot run round on an already finished game")
        if not self.config.is_six_phase:
            return legacy_v033.run_round_v033(self)
        return self._run_round_six_phase()

    def _run_round_six_phase(self) -> RoundTelemetry:
        s = self.state
        self._begin_research_telemetry()

        # Phase 1: Roll & Deploy
        commitments = self._execute_phase_1()
        p1_snap = self._snapshot_players()

        # Phase 2: Compiler Drop & Corruption (+ end-trigger check)
        cr = self._run_phase_2_compiler(commitments)
        tel = self._begin_telemetry(cr)
        tel.phase_snapshots[1] = p1_snap
        tel.phase_snapshots[2] = self._snapshot_players()
        if s.game_over:
            tel.player_snapshots = tel.phase_snapshots[2]
            return self._finalize_telemetry(tel, end_phase=2)

        # Phase 3: Income (survivors only)
        incomes = self._run_phase_3_income(commitments)
        tel.income_by_player = {
            pid: {"money": r.money, "research": r.research, "secrets": r.secrets} for pid, r in incomes.items()
        }
        tel.purple_star_triggers_per_round = {pid: r.purple_star_triggers for pid, r in incomes.items()}
        tel.phases_executed.append(3)
        tel.phase_snapshots[3] = self._snapshot_players()

        # Phase 4: Attack Resolution (damage, Snowball Recycle, Contractor Expiration, end check)
        tel.attack_strengths = self._run_phase_4_attack_resolution(commitments, cr)
        tel.phases_executed.append(4)
        tel.phase_snapshots[4] = self._snapshot_players()
        tel.player_snapshots = tel.phase_snapshots[4]
        if self.config.is_market_share:
            tel.market_share_after_p4 = {p.player_id: p.market_share for p in s.players}
        if s.game_over:
            return self._finalize_telemetry(tel, end_phase=4)

        # Phase 5: CI/CD Pipeline Shift
        shifts = self._run_phase_5_pipeline_shift()
        tel.scanned_held_by_player = {pid: r.held_in_scanned for pid, r in shifts.items()}
        tel.graduated_by_player = {pid: len(r.graduated_ids) for pid, r in shifts.items()}
        tel.phases_executed.append(5)
        tel.phase_snapshots[5] = self._snapshot_players()

        # Phase 6: Operations (clockwise; passes the First Player Marker)
        self._run_phase_6_operations()
        tel.phases_executed.append(6)
        tel.phase_snapshots[6] = self._snapshot_players()

        if s.is_final_round:
            s.game_over = True
        else:
            s.current_round += 1
            if s.current_round > s.config.max_rounds:
                s.game_over = True
                s.end_reason = EndGameReason.ROUND_LIMIT
        return self._finalize_telemetry(tel, end_phase=6 if s.game_over else None)

    def run_game(self) -> EndGameResult:
        """Runs the game to completion and returns the final scoring and standings."""
        while not self.state.game_over:
            self.run_round()

        return self.evaluate_end_game()

    def evaluate_end_game(self) -> EndGameResult:
        """Calculates Portfolio Value, handles Patient Zero elimination or Total Wipeout overflow penalties."""
        return end_game.evaluate_end_game(self)
