"""Core GameEngine, GameState, and phase execution pipeline for Rogue Agent."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from sim.bots import BaseBot, Phase3ActionPlan
from sim.config import CubeColor, DieColor, EndGameReason, GameConfig, ShieldColor
from sim.entities import (
    Die,
    Face,
    VariantCard,
    VersionCard,
    create_colored_die,
    create_gray_die,
    create_white_die,
    get_default_variant_cards,
    get_default_version_deck,
)
from sim.tower import CubeTower


@dataclass
class PlayerState:
    """Tracks corporate resources, dice pools, and breach status for one player."""

    player_id: int
    bot: BaseBot
    money: int
    secrets: int
    patches: int
    ready_dice: List[Die] = field(default_factory=list)
    unpatched_dice: List[Die] = field(default_factory=list)
    contractor_dice: List[Die] = field(default_factory=list)
    hired_contractor_count: int = 0
    is_patient_zero: bool = False
    elimination_round: Optional[int] = None
    elimination_reason: Optional[str] = None
    debt: int = 0  # Money deficit below $0
    breach_depth: int = 0  # Secret deficit below 0
    unfulfilled_destructions: int = 0  # Unfulfilled die destructions
    total_dirty_income_taken: int = 0
    total_contractors_hired: int = 0
    total_rerolls_used: int = 0
    b2_available: bool = False
    y1_available: bool = False
    p1_available: bool = False
    p3_available: Optional[ShieldColor] = None

    @property
    def total_dice(self) -> List[Die]:
        return self.ready_dice + self.unpatched_dice

    @property
    def colored_dice(self) -> List[Die]:
        return [d for d in self.total_dice if d.color != DieColor.GRAY]


@dataclass
class RoundTelemetry:
    """Per-round execution metrics for telemetry and balance analysis."""

    round_number: int
    active_version_name: str
    corruption_track: int
    staged_cubes: Dict[CubeColor, int]
    stuck_cubes_before: Dict[CubeColor, int]
    exited_cubes: Dict[CubeColor, int]
    stuck_cubes_after: Dict[CubeColor, int]
    attack_strengths: Dict[CubeColor, int]
    player_snapshots: List[Dict]


@dataclass
class EndGameResult:
    """Comprehensive post-game evaluation and final standings."""

    end_reason: EndGameReason
    total_rounds: int
    winner_id: Optional[int]
    is_total_wipeout: bool
    singularity_reached: bool
    rankings: List[Dict]
    telemetry_history: List[RoundTelemetry]


@dataclass
class GameState:
    """Complete simulation state for a running match."""

    config: GameConfig
    players: List[PlayerState]
    market: Dict[DieColor, int]
    variant_cards: Dict[DieColor, VariantCard]
    version_deck: List[VersionCard]
    current_version_index: int = 0
    corruption_track: int = 0
    staging_cup: Dict[CubeColor, int] = field(
        default_factory=lambda: {
            CubeColor.RED: 0,
            CubeColor.BLUE: 0,
            CubeColor.GREEN: 0,
            CubeColor.BLACK: 0,
        }
    )
    tower: CubeTower = field(init=False)
    first_player_index: int = 0
    current_round: int = 1
    game_over: bool = False
    is_final_round: bool = False
    end_reason: EndGameReason = EndGameReason.NONE
    singularity_triggered: bool = False
    contractor_supply: int = 12
    next_die_id: int = 1
    rng: random.Random = field(default_factory=random.Random)

    def __post_init__(self) -> None:
        self.tower = CubeTower(self.config)

    @property
    def active_version(self) -> VersionCard:
        return self.version_deck[self.current_version_index]

    @property
    def active_directive_code(self) -> str:
        return self.active_version.directive_code


class GameEngine:
    """Executes the complete Rogue Agent game loop per RULES.md."""

    def __init__(
        self,
        config: GameConfig,
        bots: List[BaseBot],
        seed: Optional[int] = None,
        variant_cards: Optional[Dict[DieColor, VariantCard]] = None,
        version_deck: Optional[List[VersionCard]] = None,
    ) -> None:
        if len(bots) != config.num_players:
            raise ValueError(f"Bot count ({len(bots)}) must match config.num_players ({config.num_players})")

        self.rng = random.Random(seed)
        self.config = config
        self.variant_cards = variant_cards or get_default_variant_cards()
        self.version_deck = version_deck or get_default_version_deck()

        # Initialize players
        players: List[PlayerState] = []
        next_die_id = 1
        starting_cash_bonus = 1 if self.version_deck[0].directive_code == "DATA_SCRAPER" else 0

        for i, bot in enumerate(bots):
            ready_dice: List[Die] = []
            for _ in range(config.starting_gray_dice):
                ready_dice.append(create_gray_die(next_die_id))
                next_die_id += 1

            player = PlayerState(
                player_id=i,
                bot=bot,
                money=config.starting_money + starting_cash_bonus,
                secrets=self.config.get_starting_secrets(self.config.num_players),
                patches=self.config.get_starting_patches(self.config.num_players),
                ready_dice=ready_dice,
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

        self.telemetry_history: List[RoundTelemetry] = []

    # =========================================================================
    # Phase 1: Boot & Configure (Simultaneous)
    # =========================================================================

    def _execute_phase_1(self) -> List[Tuple[PlayerState, List[Die], Dict[int, ShieldColor]]]:
        """Executes Phase 1 per RULES.md v0.6: Autonomous AI Pulse, Contractor Hiring, Roll Active Pool, Yahtzee Rerolls & Lock Resolution, collect immediate outputs, and commit defenses."""
        # 1. Autonomous AI Corruption Pulse
        self.state.staging_cup[CubeColor.BLACK] = (
            self.state.staging_cup.get(CubeColor.BLACK, 0) + 1
        )

        player_commitments: List[Tuple[PlayerState, List[Die], Dict[int, ShieldColor]]] = []

        staging_copy = dict(self.state.staging_cup)
        stuck_copy = self.state.tower.get_stuck_copy()

        # 2. Temp Staffing (Contractor Hiring)
        for player in self.state.players:
            if player.is_patient_zero:
                continue

            player.contractor_dice = []
            player.hired_contractor_count = 0

            max_hire = self.config.get_max_affordable_contractors(
                money=player.money,
                already_hired=player.hired_contractor_count,
                supply=self.state.contractor_supply,
            )
            desired_hire = player.bot.choose_contractor_hires(
                player_state=player,
                contractor_supply=self.state.contractor_supply,
                staging_cubes=staging_copy,
                stuck_cubes=stuck_copy,
                rng=self.rng,
            )
            actual_hire = max(0, min(desired_hire, max_hire))
            if actual_hire > 0:
                cost = self.config.get_contractor_cost_for_hire(
                    actual_hire, already_hired=player.hired_contractor_count
                )
                player.money -= cost
                self.state.contractor_supply -= actual_hire
                player.hired_contractor_count += actual_hire
                player.total_contractors_hired += actual_hire
                for _ in range(actual_hire):
                    c_die = create_white_die(self.state.next_die_id)
                    self.state.next_die_id += 1
                    player.contractor_dice.append(c_die)

        # 3. Roll Active Pool, Yahtzee Rerolls, Outputs, Commit Defenses
        for player in self.state.players:
            if player.is_patient_zero:
                continue

            # Reset round star availability
            player.b2_available = False
            player.y1_available = False
            player.p1_available = False
            player.p3_available = None

            # Roll Active Pool (ready_dice + contractor_dice)
            active_dice: List[Die] = list(player.ready_dice) + list(player.contractor_dice)
            for die in active_dice:
                die.is_locked = False
                res_face = die.roll(self.rng)
                if res_face and die.current_face != res_face:
                    die.current_face = res_face

            # 4. Lock Evaluation & Yahtzee Rerolls Loop
            active_directive = self.state.active_directive_code
            max_free_rerolls = (
                self.config.throttled_free_rerolls
                if active_directive == "POLYMORPHIC_WORM"
                else self.config.default_free_rerolls
            )

            def _evaluate_locks(dice_list: List[Die]) -> None:
                for d in dice_list:
                    face = d.current_face
                    if not face:
                        continue
                    if face.is_glitch:
                        d.is_locked = True
                    elif active_directive == "RAAS" and face.money > 0:
                        d.is_locked = True
                    elif active_directive == "ZERO_DAY_OVERRIDE" and face.is_shield:
                        d.is_locked = True

            _evaluate_locks(active_dice)

            rerolls_remaining = max_free_rerolls
            while rerolls_remaining > 0:
                # Debug action: spend 1 🔧 to unlock 1 locked die
                if player.patches > 0:
                    unlock_indices = player.bot.choose_debug_unlocks(
                        player_state=player,
                        active_dice=active_dice,
                        staging_cubes=staging_copy,
                        stuck_cubes=stuck_copy,
                        directive_code=active_directive,
                        rng=self.rng,
                    )
                    for u_idx in unlock_indices:
                        if player.patches <= 0:
                            break
                        if 0 <= u_idx < len(active_dice) and active_dice[u_idx].is_locked:
                            active_dice[u_idx].is_locked = False
                            player.patches -= 1

                # Choose rerolls among unlocked dice
                reroll_res = player.bot.choose_yahtzee_rerolls(
                    player_state=player,
                    active_dice=active_dice,
                    rerolls_remaining=rerolls_remaining,
                    staging_cubes=staging_copy,
                    stuck_cubes=stuck_copy,
                    directive_code=active_directive,
                    rng=self.rng,
                )
                if isinstance(reroll_res, tuple) and len(reroll_res) == 2:
                    extra_unlocks, reroll_indices = reroll_res
                    for u_idx in extra_unlocks:
                        if player.patches <= 0:
                            break
                        if 0 <= u_idx < len(active_dice) and active_dice[u_idx].is_locked:
                            active_dice[u_idx].is_locked = False
                            player.patches -= 1
                else:
                    reroll_indices = reroll_res or []

                valid_rerolls = [
                    idx for idx in reroll_indices
                    if 0 <= idx < len(active_dice) and not active_dice[idx].is_locked
                ]
                if not valid_rerolls:
                    break

                for r_idx in valid_rerolls:
                    res_face = active_dice[r_idx].roll(self.rng)
                    if res_face and active_dice[r_idx].current_face != res_face:
                        active_dice[r_idx].current_face = res_face
                    active_dice[r_idx].is_locked = False

                _evaluate_locks(active_dice)
                player.total_rerolls_used += 1
                rerolls_remaining -= 1

            # Final lock evaluation pass
            _evaluate_locks(active_dice)

            # 5. Collect Immediate Outputs on Final Faces
            for die in active_dice:
                self._apply_single_die_immediate_output(player, die)
            player.patches = min(player.patches, self.config.max_patch_tokens)

            # 6. Commit Defenses
            shield_commitments = player.bot.commit_shields(
                player_state=player,
                rolled_dice=active_dice,
                staging_cubes=staging_copy,
                stuck_cubes=stuck_copy,
                directive_code=active_directive,
                rng=self.rng,
            )

            # Validate assignments & auto-assign fixed colored shields if omitted
            validated_commitments: Dict[int, ShieldColor] = {}
            for idx, die in enumerate(active_dice):
                face = die.current_face
                if not face or not face.is_shield or face.is_glitch:
                    continue

                if idx in shield_commitments:
                    color = shield_commitments[idx]
                    if face.shield_color == ShieldColor.ANY:
                        validated_commitments[idx] = (
                            color if color in (ShieldColor.RED, ShieldColor.BLUE, ShieldColor.GREEN)
                            else ShieldColor.BLUE
                        )
                    else:
                        validated_commitments[idx] = face.shield_color
                else:
                    if face.shield_color in (ShieldColor.RED, ShieldColor.BLUE, ShieldColor.GREEN):
                        validated_commitments[idx] = face.shield_color
                    elif face.shield_color == ShieldColor.ANY:
                        validated_commitments[idx] = ShieldColor.BLUE

            # Track rolled Star abilities for Phase 3 eligibility
            for idx, die in enumerate(active_dice):
                face = die.current_face
                if not face or not face.is_star:
                    continue
                if face.star_code == "B2":
                    if idx not in validated_commitments:
                        player.b2_available = True
                elif face.star_code == "Y1":
                    player.y1_available = True
                elif face.star_code == "P1":
                    player.p1_available = True
                elif face.star_code == "P3":
                    if idx in validated_commitments:
                        player.p3_available = validated_commitments[idx]

            player_commitments.append((player, list(active_dice), validated_commitments))

        return player_commitments

    def _apply_single_die_immediate_output(self, player: PlayerState, die: Die) -> None:
        face = die.current_face
        if not face or face.is_glitch:
            return

        # Basic money and patches
        player.money += face.money
        player.patches += face.patches
        player.secrets += face.secrets

        # Star faces
        if face.is_star:
            if face.star_code == "Y2":
                # Cloud Monopoly: +$2, plus +$1 per Yellow die owned (max +$5)
                yellow_count = sum(1 for d in player.total_dice if d.color == DieColor.YELLOW)
                bonus = min(5, 2 + yellow_count) - 2  # base 2 already added in face.money
                player.money += max(0, bonus)
            elif face.star_code == "Y3":
                # Proprietary Training: gain 1 secret (already in face.secrets), move die to unpatched
                if die in player.ready_dice:
                    player.ready_dice.remove(die)
                    player.unpatched_dice.append(die)

    def _apply_immediate_face_outputs(self, player: PlayerState) -> None:
        """Gains immediate money, patches, secrets, and special star activations from rolled faces."""
        for die in list(player.ready_dice) + list(player.contractor_dice):
            self._apply_single_die_immediate_output(player, die)

    # =========================================================================
    # Phase 2: Rogue Agent Compile (The Cube Tower Drop)
    # =========================================================================

    def _execute_phase_2(
        self,
        player_commitments: List[Tuple[PlayerState, List[Die], Dict[int, ShieldColor]]],
    ) -> RoundTelemetry:
        """Executes Phase 2: Cube Tower drop, Version advancement, Attack & Wear resolution, and End Game checks."""
        staged_before = dict(self.state.staging_cup)
        stuck_before = self.state.tower.get_stuck_copy()

        # Drop all staged cubes into the tower
        exited_cubes = self.state.tower.drop(self.state.staging_cup, self.rng)
        stuck_after = self.state.tower.get_stuck_copy()

        # Clear staging cup
        for color in self.state.staging_cup:
            self.state.staging_cup[color] = 0

        # Step 2A: Resolve Black (Corruption) Cubes & Version Upgrades
        black_dropped = exited_cubes.get(CubeColor.BLACK, 0)
        track_capacity = self.state.config.corruption_track_capacity

        for _ in range(black_dropped):
            self.state.corruption_track += 1
            if self.state.corruption_track >= track_capacity:
                if self.state.current_version_index >= len(self.state.version_deck) - 1:
                    # Singularity reached on v3.0!
                    self.state.singularity_triggered = True
                    break
                else:
                    # Upgrade to next version
                    self.state.corruption_track = 0
                    self.state.current_version_index += 1
                    # Add new version upgrade payload to Staging Cup (drops starting next round)
                    new_version = self.state.active_version
                    for color, count in new_version.get_staging_payload(self.config.num_players).items():
                        self.state.staging_cup[color] = self.state.staging_cup.get(color, 0) + count

        # Apply P2 (Chaos Profiteer) Star bonus: +$2 per exited black cube
        if black_dropped > 0:
            for player, rolled_dice, _ in player_commitments:
                for die in rolled_dice:
                    if die.current_face and die.current_face.star_code == "P2":
                        player.money += 2 * black_dropped

        # Step 2B: Resolve Attack Cubes (Red, Blue, Green)
        red_strength = exited_cubes.get(CubeColor.RED, 0)
        blue_strength = exited_cubes.get(CubeColor.BLUE, 0)
        green_strength = exited_cubes.get(CubeColor.GREEN, 0)

        # Apply Active Version Directives to Attack Strength
        active_directive = self.state.active_directive_code
        if active_directive == "CORRUPTED_KERNEL":
            # Corrupted Kernel: Each Black Cube adds +1 Strength to the Attack Color with the most exited cubes
            if black_dropped > 0:
                highest_color = max(
                    [CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN],
                    key=lambda c: (
                        exited_cubes.get(c, 0),
                        c == CubeColor.RED,
                        c == CubeColor.BLUE,
                    ),
                )
                if highest_color == CubeColor.RED:
                    red_strength += black_dropped
                elif highest_color == CubeColor.BLUE:
                    blue_strength += black_dropped
                elif highest_color == CubeColor.GREEN:
                    green_strength += black_dropped

        attack_strengths = {
            CubeColor.RED: red_strength,
            CubeColor.BLUE: blue_strength,
            CubeColor.GREEN: green_strength,
        }

        # Resolve each player's committed shields against attacks
        for player, rolled_dice, commitments in player_commitments:
            self._resolve_player_defense_and_wear(
                player=player,
                rolled_dice=rolled_dice,
                commitments=commitments,
                attack_strengths=attack_strengths,
                exited_cubes=exited_cubes,
                active_directive=active_directive,
            )

        # Snowball Recycle: Exited Red, Blue, Green cubes return to Staging Cup
        for color in [CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN]:
            self.state.staging_cup[color] = (
                self.state.staging_cup.get(color, 0) + exited_cubes.get(color, 0)
            )

        # Contractor Expiration: All remaining White Contractor dice across all players return to supply
        for player in self.state.players:
            self.state.contractor_supply += len(player.contractor_dice)
            player.contractor_dice.clear()
            player.hired_contractor_count = 0

        # Step 2C: Check End Game Triggers
        any_patient_zero = any(p.is_patient_zero for p in self.state.players)
        all_patient_zero = all(p.is_patient_zero for p in self.state.players)

        if all_patient_zero:
            self.state.game_over = True
            self.state.is_final_round = False
            self.state.end_reason = EndGameReason.TOTAL_WIPEOUT
        elif any_patient_zero:
            self.state.is_final_round = True
            self.state.end_reason = EndGameReason.PATIENT_ZERO
        elif self.state.singularity_triggered:
            self.state.is_final_round = True
            self.state.end_reason = EndGameReason.SINGULARITY

        # Create Round Telemetry snapshot
        snapshots = [
            {
                "player_id": p.player_id,
                "bot_name": p.bot.name,
                "money": p.money,
                "secrets": p.secrets,
                "patches": p.patches,
                "ready_dice_count": len(p.ready_dice),
                "unpatched_dice_count": len(p.unpatched_dice),
                "contractor_dice_count": len(p.contractor_dice),
                "is_patient_zero": p.is_patient_zero,
            }
            for p in self.state.players
        ]

        telemetry = RoundTelemetry(
            round_number=self.state.current_round,
            active_version_name=self.state.active_version.name,
            corruption_track=self.state.corruption_track,
            staged_cubes=staged_before,
            stuck_cubes_before=stuck_before,
            exited_cubes=exited_cubes,
            stuck_cubes_after=stuck_after,
            attack_strengths=attack_strengths,
            player_snapshots=snapshots,
        )
        self.telemetry_history.append(telemetry)
        return telemetry

    def _resolve_player_defense_and_wear(
        self,
        player: PlayerState,
        rolled_dice: List[Die],
        commitments: Dict[int, ShieldColor],
        attack_strengths: Dict[CubeColor, int],
        exited_cubes: Dict[CubeColor, int],
        active_directive: str,
    ) -> None:
        """Resolves wear for actively blocking dice, post-attack star bonuses, and unblocked damage."""
        # Calculate raw committed shields per color
        raw_shields: Dict[ShieldColor, int] = {
            ShieldColor.RED: 0,
            ShieldColor.BLUE: 0,
            ShieldColor.GREEN: 0,
        }
        color_dice_map: Dict[ShieldColor, List[Tuple[int, Die]]] = {
            ShieldColor.RED: [],
            ShieldColor.BLUE: [],
            ShieldColor.GREEN: [],
        }

        for idx, color in commitments.items():
            die = rolled_dice[idx]
            face = die.current_face
            if face and face.is_shield:
                raw_shields[color] += face.block_amount
                color_dice_map[color].append((idx, die))

        effective_shields: Dict[CubeColor, int] = {
            CubeColor.RED: raw_shields[ShieldColor.RED],
            CubeColor.BLUE: raw_shields[ShieldColor.BLUE],
            CubeColor.GREEN: raw_shields[ShieldColor.GREEN],
        }

        # Calculate blocked and unblocked attacks
        blocked_red = min(effective_shields[CubeColor.RED], attack_strengths[CubeColor.RED])
        unblocked_red = attack_strengths[CubeColor.RED] - blocked_red

        blocked_blue = min(effective_shields[CubeColor.BLUE], attack_strengths[CubeColor.BLUE])
        unblocked_blue = attack_strengths[CubeColor.BLUE] - blocked_blue

        blocked_green = min(effective_shields[CubeColor.GREEN], attack_strengths[CubeColor.GREEN])
        unblocked_green = attack_strengths[CubeColor.GREEN] - blocked_green

        # 1. Dice Wear: Any permanent die assigned as a shield that actively blocks at least 1 cube moves to Unpatched
        # White Contractor dice have wear immunity (return to supply at round end).
        # Dice that block 0 cubes remain Ready
        worn_dice_set: set[int] = set()

        for s_color, attack_blocked in [
            (ShieldColor.RED, blocked_red),
            (ShieldColor.BLUE, blocked_blue),
            (ShieldColor.GREEN, blocked_green),
        ]:
            assigned_dice = [die for _, die in color_dice_map[s_color]]
            ordered_dice = player.bot.choose_shield_wear_order(
                player_state=player,
                color=s_color,
                assigned_dice=assigned_dice,
                cubes_to_absorb=attack_blocked,
            )
            cubes_remaining_to_absorb = attack_blocked
            for die in ordered_dice:
                if cubes_remaining_to_absorb <= 0:
                    break  # Unused shields remain Ready!

                face = die.current_face
                amt = face.block_amount if face else 0
                cubes_remaining_to_absorb -= amt

                # White contractor dice wear immunity!
                if die.color == DieColor.WHITE:
                    continue

                # B3 — Air-Gapped Backup: does NOT move to unpatched when blocking
                if face and face.star_code == "B3":
                    continue

                if die in player.ready_dice:
                    player.ready_dice.remove(die)
                    player.unpatched_dice.append(die)
                    worn_dice_set.add(die.die_id)

        # 2. Star ability damage-dependent bonuses
        for die in rolled_dice:
            face = die.current_face
            if not face or not face.is_star:
                continue
            if face.star_code == "R2":
                # Threat Bounty: Block 2 Red; if you take 0 unblocked Red damage, gain +$2
                if unblocked_red == 0:
                    player.money += 2
            elif face.star_code == "R3":
                # Short Squeeze: if 3+ Red cubes exit tower, gain extra +$1
                if exited_cubes.get(CubeColor.RED, 0) >= 3:
                    player.money += 1
            elif face.star_code == "B1":
                # Honeypot: Block 2 Blue; if 1+ Blue cubes exit and you take 0 Blue damage, gain +$3
                if exited_cubes.get(CubeColor.BLUE, 0) >= 1 and unblocked_blue == 0:
                    player.money += 3

        # 3. Apply Unblocked Damage
        # Red (Ransomware): Lose $1 per unblocked Red cube.
        # Tier 1: Cash pays min(player.money, unblocked_red).
        # Tier 2: Emergency Patch Absorption - patches absorb min(player.patches, unpaid_ransom).
        # Tier 3: Unpaid Ransom Leak - remaining unpaid ransom leaks Secrets (1 Secret per unpaid $1).
        # Money and patches are strictly non-negative (>= 0).
        if unblocked_red > 0:
            cash_paid = min(player.money, unblocked_red)
            player.money -= cash_paid
            unpaid_ransom = unblocked_red - cash_paid

            if unpaid_ransom > 0 and player.patches > 0:
                patches_absorbed = min(player.patches, unpaid_ransom)
                player.patches -= patches_absorbed
                unpaid_ransom -= patches_absorbed

            if unpaid_ransom > 0:
                player.secrets -= unpaid_ransom

            player.money = max(0, player.money)
            player.patches = max(0, player.patches)

        # Blue (Spyware): Lose 1 Corporate Secret per unblocked Blue cube
        if unblocked_blue > 0:
            player.secrets -= unblocked_blue

        # Patient Zero Check: Strictly occurs upon Total Data Breach (Secrets <= 0)
        if player.secrets <= 0:
            player.is_patient_zero = True
            player.elimination_round = self.state.current_round
            player.elimination_reason = "Total Breach (<= 0 Secrets)"
            player.breach_depth = max(0, -player.secrets)

        # Green (Malware): Move 1 Ready die to Unpatched per cube.
        # Commercial Exposure: Ready Yellow dice must be demoted first before Contractor Sacrifice or other ready dice can absorb malware.
        # Contractor Sacrifice: You may discard 1 active White Contractor die instead (if no ready yellow dice)!
        for _ in range(unblocked_green):
            ready_yellow_idx = next(
                (idx for idx, d in enumerate(player.ready_dice) if d.color == DieColor.YELLOW),
                None,
            )
            if ready_yellow_idx is not None:
                # Commercial Exposure: demote ready Yellow die first
                demoted_yellow = player.ready_dice.pop(ready_yellow_idx)
                player.unpatched_dice.append(demoted_yellow)
            else:
                sacrifice = player.bot.choose_malware_sacrifice(
                    player_state=player,
                    unblocked_green=unblocked_green,
                    rng=self.rng,
                )
                if sacrifice and len(player.contractor_dice) > 0:
                    sacrificed_die = player.contractor_dice.pop(0)
                    self.state.contractor_supply += 1
                elif len(player.ready_dice) > 0:
                    # Move first ready die to unpatched
                    demoted = player.ready_dice.pop(0)
                    player.unpatched_dice.append(demoted)
                elif len(player.unpatched_dice) > 0:
                    # Destroy 1 Unpatched die of player's choice (destroy lowest VP die first)
                    player.unpatched_dice.sort(key=lambda d: d.vp)
                    player.unpatched_dice.pop(0)
                else:
                    # Completely wiped out; record unfulfilled die destruction
                    player.unfulfilled_destructions += 1

    # =========================================================================
    # Phase 3: Corporate Operations (Clockwise Turns)
    # =========================================================================

    def _execute_phase_3(self) -> None:
        """Executes Phase 3: Clockwise player operations (Dirty Income, Patching, Purchasing, Stars)."""
        if self.state.game_over or all(p.is_patient_zero for p in self.state.players):
            return

        num_players = len(self.state.players)
        patch_cash_cost = self.state.config.patch_cash_cost

        for offset in range(num_players):
            idx = (self.state.first_player_index + offset) % num_players
            player = self.state.players[idx]

            if player.is_patient_zero:
                continue

            plan = player.bot.take_phase3_actions(player, self.state, self.rng)

            # 1. Dirty Income ("Monetize the Rogue Agent" — Limit 1x per turn)
            # Preconditions: secrets > dirty_income_secret_cost and at least 1 ready die for Backlash
            if (
                plan.take_dirty_income
                and player.secrets > self.state.config.dirty_income_secret_cost
                and len(player.ready_dice) >= 1
            ):
                player.secrets -= self.state.config.dirty_income_secret_cost
                player.money += self.state.config.dirty_income_cash
                self.state.staging_cup[CubeColor.BLACK] = (
                    self.state.staging_cup.get(CubeColor.BLACK, 0)
                    + self.state.config.dirty_income_black_cubes
                )
                # Technical Debt Backlash: demote 1 Ready die to Unpatched
                backlash_idx = plan.dirty_income_backlash_die_index
                if not (0 <= backlash_idx < len(player.ready_dice)):
                    backlash_idx = 0
                backlash_die = player.ready_dice.pop(backlash_idx)
                player.unpatched_dice.append(backlash_die)
                player.total_dirty_income_taken += 1

            # 2. Star Special Actions in Phase 3 (Guarded by Phase 1 eligibility)
            if plan.use_b2_secret and player.b2_available:
                if player.money >= 2 and player.secrets < 10:
                    player.money -= 2
                    player.secrets = min(10, player.secrets + 1)
                    player.b2_available = False

            if plan.use_y1_secret and player.y1_available:
                # Reverses +$4 from P1 and pays $2 for +1 Secret (net -$2)
                if player.money >= 6 and player.secrets < 10:
                    player.money -= 6
                    player.secrets = min(10, player.secrets + 1)
                    player.y1_available = False

            if (
                plan.p1_cube_choice in (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN)
                and player.p1_available
            ):
                self.state.staging_cup[plan.p1_cube_choice] = (
                    self.state.staging_cup.get(plan.p1_cube_choice, 0) + 1
                )
                player.p1_available = False

            if (
                plan.p3_cube_choice in (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN)
                and player.p3_available is not None
            ):
                # Must match the color that P3 blocked!
                if plan.p3_cube_choice.value == player.p3_available.value:
                    self.state.staging_cup[plan.p3_cube_choice] = (
                        self.state.staging_cup.get(plan.p3_cube_choice, 0) + 1
                    )
                    player.p3_available = None

            # 3. Patching Worn-Out Dice (Unlimited)
            for patch_action in plan.patch_actions:
                if len(player.unpatched_dice) == 0:
                    break
                idx = patch_action.get("die_index", 0)
                if not isinstance(idx, int) or not (0 <= idx < len(player.unpatched_dice)):
                    idx = 0

                use_cash = bool(patch_action.get("use_cash", False))
                if use_cash:
                    if player.money >= patch_cash_cost:
                        player.money -= patch_cash_cost
                        patched_die = player.unpatched_dice.pop(idx)
                        player.ready_dice.append(patched_die)
                else:
                    if player.patches >= self.state.config.patch_token_cost:
                        player.patches -= self.state.config.patch_token_cost
                        patched_die = player.unpatched_dice.pop(idx)
                        player.ready_dice.append(patched_die)

            # 4. Market Purchases (Limit 2 dice per turn)
            purchased_count = 0
            for color in plan.market_purchases:
                if purchased_count >= self.state.config.max_market_purchases_per_turn:
                    break
                cost = 4 if color in (DieColor.RED, DieColor.GREEN, DieColor.PURPLE) else 5
                if self.state.market.get(color, 0) > 0 and player.money >= cost:
                    player.money -= cost
                    self.state.market[color] -= 1
                    purchased_count += 1
                    new_die = create_colored_die(
                        color=color,
                        die_id=self.state.next_die_id,
                        variant_card=self.state.variant_cards.get(color),
                    )
                    self.state.next_die_id += 1
                    player.ready_dice.append(new_die)

            # Cap patch tokens
            player.patches = min(player.patches, self.state.config.max_patch_tokens)

        # Advance First Player marker clockwise
        self.state.first_player_index = (self.state.first_player_index + 1) % num_players

    # =========================================================================
    # Game Loop Execution & Final Evaluation
    # =========================================================================

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
        cfg = self.config
        all_patient_zero = all(p.is_patient_zero for p in self.state.players)

        rankings: List[Dict] = []

        for p in self.state.players:
            # Portfolio Value:
            # 4 VP per Secret + VP per owned colored die + 1 VP per $2 (rounded down)
            # 4 VP per Secret (raw VP cannot be negative; negative secrets penalize via overflow)
            secret_vp = max(0, p.secrets) * cfg.vp_per_secret
            dice_vp = sum(cfg.vp_per_die.get(d.color, 0) for d in p.total_dice)
            cash_vp = max(0, p.money) // cfg.vp_cash_divisor
            portfolio_value = secret_vp + dice_vp + cash_vp

            # Overflow penalties (used if total wipeout: -4 VP per Secret below 0, -3 VP per unfulfilled destruction)
            overflow_penalties = 0
            if all_patient_zero:
                secret_penalty = p.breach_depth * cfg.overflow_penalty_per_secret_debt
                destruction_penalty = (
                    p.unfulfilled_destructions * cfg.overflow_penalty_per_unfulfilled_destroyed_die
                )
                overflow_penalties = secret_penalty + destruction_penalty

            net_score = portfolio_value + overflow_penalties

            rankings.append(
                {
                    "player_id": p.player_id,
                    "bot_name": p.bot.name,
                    "portfolio_value": portfolio_value,
                    "overflow_penalties": overflow_penalties,
                    "net_score": net_score,
                    "is_patient_zero": p.is_patient_zero,
                    "elimination_reason": p.elimination_reason,
                    "secrets": p.secrets,
                    "money": p.money,
                    "debt": p.debt,
                    "breach_depth": p.breach_depth,
                    "unfulfilled_destructions": p.unfulfilled_destructions,
                    "ready_dice_count": len(p.ready_dice),
                    "unpatched_dice_count": len(p.unpatched_dice),
                    "total_dirty_income": p.total_dirty_income_taken,
                    "total_contractors_hired": p.total_contractors_hired,
                    "total_rerolls_used": p.total_rerolls_used,
                }
            )

        if not all_patient_zero:
            # Standard Ending: Survivors ranked by Portfolio Value, Secrets, Money. Patient Zeros eliminated.
            survivors = [r for r in rankings if not r["is_patient_zero"]]
            eliminated = [r for r in rankings if r["is_patient_zero"]]

            survivors.sort(
                key=lambda r: (r["portfolio_value"], r["secrets"], r["money"]),
                reverse=True,
            )
            eliminated.sort(
                key=lambda r: (r["portfolio_value"], r["secrets"], r["money"]),
                reverse=True,
            )

            sorted_rankings = survivors + eliminated
            for rank_idx, r in enumerate(sorted_rankings):
                r["rank"] = rank_idx + 1

            winner_id = sorted_rankings[0]["player_id"] if sorted_rankings else None
            final_rankings = sorted_rankings
        else:
            # Total Wipeout: Ranked by Net Score, Secrets (higher/less negative), Money (higher/less debt)
            rankings.sort(
                key=lambda r: (r["net_score"], r["secrets"], r["money"]),
                reverse=True,
            )
            for rank_idx, r in enumerate(rankings):
                r["rank"] = rank_idx + 1

            # In total wipeout, narrative victory belongs to Rogue Agent, but top human takes 1st rank
            winner_id = rankings[0]["player_id"] if rankings else None
            final_rankings = rankings

        return EndGameResult(
            end_reason=self.state.end_reason,
            total_rounds=self.state.current_round,
            winner_id=winner_id,
            is_total_wipeout=all_patient_zero,
            singularity_reached=self.state.singularity_triggered,
            rankings=final_rankings,
            telemetry_history=self.telemetry_history,
        )
