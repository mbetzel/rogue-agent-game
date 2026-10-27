"""GameController state machine adapter wrapping sim/engine.py for Rogue Agent Web Playtesting."""

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
    Die,
    VariantCard,
    VersionCard,
    create_colored_die,
    create_white_die,
    get_default_variant_cards,
    get_default_version_deck,
    get_random_setup,
    get_random_variant_cards,
    get_random_version_deck,
)
from web.schemas import GameStateSerializer


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
        if self.engine is None:
            raise RuntimeError("Game has not been initialized. Call new_game() first.")
        return self.engine.state

    # =========================================================================
    # Game Setup & Initialization
    # =========================================================================

    def new_game(
        self,
        num_players: int = 4,
        players_config: Optional[List[Dict[str, Any]]] = None,
        seed: Optional[int] = None,
        variant_cards: Optional[Dict[DieColor, VariantCard]] = None,
        version_deck: Optional[List[VersionCard]] = None,
        randomize_cards: bool = False,
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
        )

        variant_summary = ", ".join(v.code for v in self.state.variant_cards.values())
        self.event_log = [
            f"Game initialized with {num_players} corporations (Seed: {seed if seed is not None else 'auto'}).",
            f"Active Version: {self.state.active_version.name} ({self.state.active_version.version_str}).",
            f"Active Variants: {variant_summary}.",
            f"CISO badge awarded to {self.player_meta[self.state.first_player_index]['name']}.",
        ]
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

    def hire_contractors(self, player_id: int, count: int) -> Dict[str, Any]:
        """Hires 1-3 temporary White Contractor dice during Phase 1 before rolling."""
        if self.phase != 1:
            raise ValueError(f"Cannot hire contractors in phase {self.phase} ({self.phase_name})")
        if player_id not in self.player_meta:
            raise ValueError(f"Invalid player_id {player_id}")

        meta = self.player_meta[player_id]
        player = self.state.players[player_id]

        if player.is_patient_zero:
            raise ValueError(f"Player {player_id} is eliminated")
        if meta["has_rolled"]:
            raise ValueError("Cannot hire contractors after rolling pool")
        if not isinstance(count, int) or not (1 <= count <= self.state.config.contractor_max_hire):
            raise ValueError(f"Contractor hire count must be between 1 and {self.state.config.contractor_max_hire}, got {count}")

        already_hired = meta.get("hired_contractors", 0)
        if already_hired + count > self.state.config.contractor_max_hire:
            raise ValueError(f"Cannot hire {count} contractors: already hired {already_hired}, max allowed is {self.state.config.contractor_max_hire}")

        cost = self.state.config.get_contractor_cost_for_hire(count, already_hired=already_hired)
        if player.money < cost:
            raise ValueError(f"Insufficient funds: need ${cost}, have ${player.money}")
        if self.state.contractor_supply < count:
            raise ValueError(f"Insufficient contractor supply: requested {count}, available {self.state.contractor_supply}")

        player.money -= cost
        self.state.contractor_supply -= count
        player.hired_contractor_count += count
        player.total_contractors_hired += count
        meta["hired_contractors"] = already_hired + count

        for _ in range(count):
            c_die = create_white_die(self.state.next_die_id)
            self.state.next_die_id += 1
            player.contractor_dice.append(c_die)

        self.event_log.append(
            f"{meta['name']} hired {count} Contractor dice for ${cost} (Total hired: {meta['hired_contractors']}, Remaining supply: {self.state.contractor_supply})."
        )
        return self.get_full_state()

    def roll_pool(self, player_id: int) -> Dict[str, Any]:
        """Rolls the ready pool and contractor dice for an interactive human player in Phase 1."""
        if self.phase != 1:
            raise ValueError(f"Cannot roll pool in phase {self.phase} ({self.phase_name})")
        if player_id not in self.player_meta:
            raise ValueError(f"Invalid player_id {player_id}")

        meta = self.player_meta[player_id]
        player = self.state.players[player_id]

        if player.is_patient_zero:
            raise ValueError(f"Player {player_id} is eliminated (Patient Zero)")
        if meta["has_rolled"]:
            raise ValueError(f"Player {player_id} has already rolled their pool this round")

        # Roll active pool (ready_dice + contractor_dice)
        active_dice: List[Die] = list(player.ready_dice) + list(player.contractor_dice)
        for die in active_dice:
            die.is_locked = False
            die.roll(self.engine.rng)

        meta["rolled_pool"] = list(active_dice)
        meta["has_rolled"] = True
        self.subphase = "waiting_for_commit"

        # Evaluate locks per RULES.md v0.6
        active_directive = self.state.active_directive_code
        for die in active_dice:
            face = die.current_face
            if not face:
                continue
            if face.is_glitch:
                die.is_locked = True
            elif active_directive == "RAAS" and face.has_cash_option:
                die.is_locked = True
            elif active_directive == "ZERO_DAY_OVERRIDE" and face.has_shield_option:
                die.is_locked = True

        face_names = [
            f"{d.current_face.name}{' [LOCKED]' if d.is_locked else ''}" if d.current_face else "?"
            for d in active_dice
        ]
        self.event_log.append(f"{meta['name']} rolled {len(active_dice)} dice: {', '.join(face_names)}")
        return self.get_full_state()

    def perform_reroll(self, player_id: int, reroll_indices: List[int]) -> Dict[str, Any]:
        """Performs a Yahtzee free reroll on a subset of unlocked rolled dice."""
        if self.phase != 1:
            raise ValueError(f"Cannot reroll in phase {self.phase}")
        if player_id not in self.player_meta:
            raise ValueError(f"Invalid player_id {player_id}")

        meta = self.player_meta[player_id]
        player = self.state.players[player_id]

        if player.is_patient_zero:
            raise ValueError(f"Player {player_id} is eliminated")
        if not meta["has_rolled"]:
            raise ValueError("Must roll pool before rerolling")
        if meta["has_committed"]:
            raise ValueError("Cannot reroll after committing defenses")
        if meta.get("rerolls_remaining", 0) <= 0:
            raise ValueError("No free rerolls remaining this round")
        if not isinstance(reroll_indices, list) or len(reroll_indices) == 0:
            raise ValueError("reroll_indices must be a non-empty list of integers")

        rolled = meta["rolled_pool"]
        for idx in reroll_indices:
            if not isinstance(idx, int) or not (0 <= idx < len(rolled)):
                raise ValueError(f"Invalid die index {idx}. Rolled pool size: {len(rolled)}")
            if rolled[idx].is_locked:
                raise ValueError(f"Die #{idx + 1} ({rolled[idx].color.value}) is locked and cannot be rerolled")

        rerolled_faces = []
        for idx in reroll_indices:
            die = rolled[idx]
            new_face = die.roll(self.engine.rng)
            die.is_locked = False
            rerolled_faces.append(f"#{idx + 1} ({new_face.name})")

        meta["rerolls_remaining"] -= 1
        player.total_rerolls_used += 1

        # Re-evaluate locks on all dice in rolled_pool
        active_directive = self.state.active_directive_code
        for d in rolled:
            face = d.current_face
            if not face:
                continue
            if face.is_glitch:
                d.is_locked = True
            elif active_directive == "RAAS" and face.has_cash_option:
                d.is_locked = True
            elif active_directive == "ZERO_DAY_OVERRIDE" and face.has_shield_option:
                d.is_locked = True

        self.event_log.append(
            f"{meta['name']} rerolled dice {', '.join(rerolled_faces)} ({meta['rerolls_remaining']} rerolls remaining)."
        )
        return self.get_full_state()

    def debug_unlock_die(self, player_id: int, die_index: int) -> Dict[str, Any]:
        """Spends 1 🔧 token to unlock a locked die, allowing it to be rerolled in remaining rerolls."""
        if self.phase != 1:
            raise ValueError(f"Cannot debug unlock in phase {self.phase}")
        if player_id not in self.player_meta:
            raise ValueError(f"Invalid player_id {player_id}")

        meta = self.player_meta[player_id]
        player = self.state.players[player_id]

        if player.is_patient_zero:
            raise ValueError(f"Player {player_id} is eliminated")
        if not meta["has_rolled"]:
            raise ValueError("Must roll pool before debug unlocking")
        if meta["has_committed"]:
            raise ValueError("Cannot debug unlock after committing defenses")

        rolled = meta["rolled_pool"]
        if not (0 <= die_index < len(rolled)):
            raise ValueError(f"Invalid die_index {die_index}. Rolled pool size: {len(rolled)}")

        die = rolled[die_index]
        if not die.is_locked:
            raise ValueError(f"Die #{die_index + 1} is not locked")

        if player.patches < 1:
            raise ValueError("Not enough patch tokens (🔧) to debug unlock")

        player.patches -= 1
        die.is_locked = False

        self.event_log.append(
            f"{meta['name']} spent 1 🔧 to debug unlock die #{die_index + 1} ({die.color.value})."
        )
        return self.get_full_state()

    def hotfix_reroll(self, player_id: int, die_index: int) -> Dict[str, Any]:
        """Spends 1 🔧 token to reroll any 1 rolled die before committing defenses."""
        if self.phase != 1:
            raise ValueError(f"Cannot hotfix reroll in phase {self.phase}")
        if player_id not in self.player_meta:
            raise ValueError(f"Invalid player_id {player_id}")

        meta = self.player_meta[player_id]
        player = self.state.players[player_id]

        if player.is_patient_zero:
            raise ValueError(f"Player {player_id} is eliminated")
        if not meta["has_rolled"]:
            raise ValueError("Must roll ready pool before using hotfix rerolls")
        if meta["has_committed"]:
            raise ValueError("Cannot reroll dice after committing defenses")

        rolled = meta["rolled_pool"]
        if not (0 <= die_index < len(rolled)):
            raise ValueError(f"Invalid die_index {die_index}. Rolled pool size: {len(rolled)}")

        locked = set(meta.get("locked_reroll_indices", []))
        if die_index in locked:
            raise ValueError(f"Die #{die_index + 1} is locked (its patch output was spent for a hotfix) and cannot be rerolled")

        # Available patch tokens = player.patches + any patches showing on kept unlocked rolled dice minus spent_from_kept
        kept_rolled_patches = sum(
            d.current_face.patches
            for i, d in enumerate(rolled)
            if i != die_index and i not in locked and d.current_face
        )
        spent_from_kept = meta.get("spent_from_kept", 0)
        available_kept = max(0, kept_rolled_patches - spent_from_kept)
        total_available = player.patches + available_kept

        if total_available < 1:
            raise ValueError(f"Not enough patch tokens (🔧). Available: {total_available}")

        # Spend 1 patch: prefer spending from held tokens first
        if player.patches > 0:
            player.patches -= 1
        else:
            spend_idx = None
            for i, d in enumerate(rolled):
                if i != die_index and i not in locked and d.current_face and d.current_face.patches > 0:
                    spend_idx = i
                    break
            if spend_idx is not None:
                meta.setdefault("locked_reroll_indices", []).append(spend_idx)
            meta["spent_from_kept"] = spent_from_kept + 1

        # Reroll the specified die
        die_to_reroll = rolled[die_index]
        new_face = die_to_reroll.roll(self.engine.rng)

        self.event_log.append(
            f"{meta['name']} spent 1 🔧 to hotfix reroll die #{die_index + 1} ({die_to_reroll.color.value.capitalize()}) -> rolled '{new_face.name}'."
        )
        return self.get_full_state()

    def commit_defenses(
        self,
        player_id: int,
        commitments: Dict[int, str],
        choice_declarations: Optional[Dict[int, int]] = None,
    ) -> Dict[str, Any]:
        """Commits rolled shield dice to Red, Blue, or Green shield slots and sets choice branches."""
        if self.phase != 1:
            raise ValueError(f"Cannot commit defenses in phase {self.phase}")
        if player_id not in self.player_meta:
            raise ValueError(f"Invalid player_id {player_id}")

        meta = self.player_meta[player_id]
        player = self.state.players[player_id]

        if player.is_patient_zero:
            raise ValueError(f"Player {player_id} is eliminated")
        if not meta["has_rolled"]:
            raise ValueError("Must roll ready pool before committing defenses")
        if meta["has_committed"]:
            raise ValueError("Defenses have already been committed this round")

        rolled = meta["rolled_pool"]
        choice_decls: Dict[int, int] = {}
        if choice_declarations:
            for k, v in choice_declarations.items():
                try:
                    choice_decls[int(k)] = int(v)
                except (ValueError, TypeError):
                    pass

        validated_commitments: Dict[int, ShieldColor] = {}

        # Validate commitments
        for idx_str, color_str in commitments.items():
            idx = int(idx_str)
            if not (0 <= idx < len(rolled)):
                raise ValueError(f"Invalid die index {idx} in commitments")

            die = rolled[idx]
            face = die.current_face
            if not face or face.is_glitch:
                raise ValueError(f"Die #{idx + 1} ({die.color.value}) cannot be committed ({face.name if face else 'None'})")

            shield_target = ShieldColor(color_str.lower())
            if shield_target not in (ShieldColor.RED, ShieldColor.BLUE, ShieldColor.GREEN):
                raise ValueError(f"Shield target must be red, blue, or green, got {color_str}")

            if face.is_shield:
                if face.shield_color == ShieldColor.ANY:
                    validated_commitments[idx] = shield_target
                elif face.shield_color in (ShieldColor.RED, ShieldColor.BLUE, ShieldColor.GREEN):
                    # Fixed colored shields must commit to their color
                    validated_commitments[idx] = face.shield_color
            elif face.has_shield_option:
                if shield_target == ShieldColor.BLUE:
                    validated_commitments[idx] = ShieldColor.BLUE
                    die.chosen_choice_index = 0
                else:
                    raise ValueError(f"Die #{idx + 1} ({die.color.value}) can only block Blue, got {color_str}")
            else:
                raise ValueError(f"Die #{idx + 1} ({die.color.value}) is not a shield die ({face.name})")

        # Auto-assign any unassigned fixed colored shields (excluding B2, and excluding choice faces)
        for idx, die in enumerate(rolled):
            face = die.current_face
            if face and face.is_shield and not face.is_choice and idx not in validated_commitments:
                if face.shield_color in (ShieldColor.RED, ShieldColor.BLUE, ShieldColor.GREEN) and face.star_code != "B2":
                    validated_commitments[idx] = face.shield_color

        # Sync choice faces
        for idx, die in enumerate(rolled):
            face = die.current_face
            if face and face.is_choice:
                if face.has_shield_option:
                    if idx in validated_commitments and validated_commitments[idx] == ShieldColor.BLUE:
                        die.chosen_choice_index = 0
                    else:
                        die.chosen_choice_index = 1
                else:
                    chosen = choice_decls.get(idx, 0)
                    if not (0 <= chosen < len(face.choices)):
                        chosen = 0
                    die.chosen_choice_index = chosen

        meta["commitments"] = {idx: color.value for idx, color in validated_commitments.items()}
        meta["has_committed"] = True

        # Group shield slots
        slots = {"red": [], "blue": [], "green": []}
        for idx, color in validated_commitments.items():
            slots[color.value].append(rolled[idx])
        meta["shield_slots"] = slots

        # Collect resource outputs on effective faces (RULES.md v0.8 Phase 1 Step 6)
        for idx, die in enumerate(rolled):
            face = die.current_face
            if not face or face.is_glitch:
                continue

            if idx not in validated_commitments:
                eff = die.effective_face
                if eff:
                    player.money += eff.money
                    player.patches += eff.patches
                    player.secrets += eff.secrets
                    if eff.is_star:
                        if eff.star_code == "Y2":
                            distinct_count = len({d.color for d in player.colored_dice})
                            total_payout = min(self.state.config.y2_max_payout, self.state.config.y2_base_payout + distinct_count)
                            bonus = total_payout - eff.money
                            player.money += max(0, bonus)
                        elif eff.star_code == "Y3":
                            if die in player.ready_dice:
                                player.ready_dice.remove(die)
                                player.unpatched_dice.append(die)
            else:
                # Assigned to defense: hybrid star boot outputs
                if face.is_star:
                    if face.star_code == "R1":
                        player.money += 2
                    elif face.star_code in ("G1", "G2"):
                        player.patches += 1

        spent_from_kept = meta.get("spent_from_kept", 0)
        player.patches = max(0, player.patches - spent_from_kept)
        player.patches = min(player.patches, self.state.config.max_patch_tokens)

        # Track star ability eligibility for Phase 3
        for idx, die in enumerate(rolled):
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

        shield_summary = [f"{len(slots[c])} {c.capitalize()}" for c in ["red", "blue", "green"] if slots[c]]
        self.event_log.append(
            f"{meta['name']} committed shields: {', '.join(shield_summary) if shield_summary else 'No shields'}."
        )

        # Check if all human players have committed
        all_humans_committed = all(
            m["has_committed"]
            for pid, m in self.player_meta.items()
            if m["is_human"] and not self.state.players[pid].is_patient_zero
        )

        if all_humans_committed:
            # Auto-execute Phase 1 for all bot players
            self._auto_execute_bots_phase_1()

            # Advance to Phase 2
            self.phase = 2
            self.phase_name = "Rogue Agent Compile"
            self.subphase = "ready_for_compile"
            self.event_log.append("All corporations have committed defenses. Ready for Compile Drop.")

        return self.get_full_state()

    def _auto_execute_bots_phase_1(self) -> None:
        """Runs Phase 1 contractor hiring, roll, Yahtzee rerolls/debug, and defense commitments for bot players."""
        staging_copy = dict(self.state.staging_cup)
        stuck_copy = self.state.tower.get_stuck_copy()

        for pid, player in enumerate(self.state.players):
            meta = self.player_meta[pid]
            if meta["is_human"] or player.is_patient_zero:
                continue

            # 1. Temp Staffing (Contractor Hiring)
            max_hire = self.state.config.get_max_affordable_contractors(
                money=player.money,
                already_hired=player.hired_contractor_count,
                supply=self.state.contractor_supply,
            )
            desired_hire = player.bot.choose_contractor_hires(
                player_state=player,
                contractor_supply=self.state.contractor_supply,
                staging_cubes=staging_copy,
                stuck_cubes=stuck_copy,
                rng=self.engine.rng,
            )
            actual_hire = max(0, min(desired_hire, max_hire))
            if actual_hire > 0:
                cost = self.state.config.get_contractor_cost_for_hire(
                    actual_hire, already_hired=player.hired_contractor_count
                )
                player.money -= cost
                self.state.contractor_supply -= actual_hire
                player.hired_contractor_count += actual_hire
                player.total_contractors_hired += actual_hire
                meta["hired_contractors"] = player.hired_contractor_count
                for _ in range(actual_hire):
                    c_die = create_white_die(self.state.next_die_id)
                    self.state.next_die_id += 1
                    player.contractor_dice.append(c_die)

            # 2. Roll Active Pool
            active_dice: List[Die] = list(player.ready_dice) + list(player.contractor_dice)
            for die in active_dice:
                die.is_locked = False
                die.roll(self.engine.rng)

            # 3. Yahtzee Rerolls & Lock Resolution
            active_directive = self.state.active_directive_code
            max_free_rerolls = (
                self.state.config.throttled_free_rerolls
                if active_directive == "POLYMORPHIC_WORM"
                else self.state.config.default_free_rerolls
            )

            def _eval_locks(dice_list: List[Die]) -> None:
                for d in dice_list:
                    face = d.current_face
                    if not face:
                        continue
                    if face.is_glitch:
                        d.is_locked = True
                    elif active_directive == "RAAS" and face.has_cash_option:
                        d.is_locked = True
                    elif active_directive == "ZERO_DAY_OVERRIDE" and face.has_shield_option:
                        d.is_locked = True

            _eval_locks(active_dice)

            rerolls_remaining = max_free_rerolls
            while rerolls_remaining > 0:
                if player.patches > 0:
                    unlock_indices = player.bot.choose_debug_unlocks(
                        player_state=player,
                        active_dice=active_dice,
                        staging_cubes=staging_copy,
                        stuck_cubes=stuck_copy,
                        directive_code=active_directive,
                        rng=self.engine.rng,
                    )
                    for u_idx in unlock_indices:
                        if player.patches <= 0:
                            break
                        if 0 <= u_idx < len(active_dice) and active_dice[u_idx].is_locked:
                            active_dice[u_idx].is_locked = False
                            player.patches -= 1

                reroll_indices = player.bot.choose_yahtzee_rerolls(
                    player_state=player,
                    active_dice=active_dice,
                    rerolls_remaining=rerolls_remaining,
                    staging_cubes=staging_copy,
                    stuck_cubes=stuck_copy,
                    directive_code=active_directive,
                    rng=self.engine.rng,
                )
                valid_rerolls = [
                    idx for idx in reroll_indices
                    if 0 <= idx < len(active_dice) and not active_dice[idx].is_locked
                ]
                if not valid_rerolls:
                    break

                for r_idx in valid_rerolls:
                    active_dice[r_idx].roll(self.engine.rng)
                    active_dice[r_idx].is_locked = False

                _eval_locks(active_dice)
                player.total_rerolls_used += 1
                rerolls_remaining -= 1

            _eval_locks(active_dice)

            # 5. Assign Defenses & Declare Choices (RULES.md v0.8)
            declared_choices = player.bot.declare_choices(
                player_state=player,
                active_dice=active_dice,
                staging_cubes=staging_copy,
                stuck_cubes=stuck_copy,
                directive_code=active_directive,
                rng=self.engine.rng,
            )
            commitments = player.bot.commit_shields(
                player_state=player,
                rolled_dice=active_dice,
                staging_cubes=staging_copy,
                stuck_cubes=stuck_copy,
                directive_code=active_directive,
                rng=self.engine.rng,
            )
            validated: Dict[int, ShieldColor] = {}
            for idx, die in enumerate(active_dice):
                face = die.current_face
                if not face or face.is_glitch:
                    continue

                if face.is_choice:
                    if face.has_shield_option:
                        if idx in commitments and commitments[idx] == ShieldColor.BLUE:
                            validated[idx] = ShieldColor.BLUE
                            die.chosen_choice_index = 0
                        else:
                            die.chosen_choice_index = 1
                    else:
                        chosen = declared_choices.get(idx, 0) if declared_choices else 0
                        if not (0 <= chosen < len(face.choices)):
                            chosen = 0
                        die.chosen_choice_index = chosen

                elif face.is_shield:
                    if idx in commitments:
                        c = commitments[idx]
                        validated[idx] = c if c in (ShieldColor.RED, ShieldColor.BLUE, ShieldColor.GREEN) else ShieldColor.BLUE
                    elif face.shield_color in (ShieldColor.RED, ShieldColor.BLUE, ShieldColor.GREEN):
                        if face.star_code != "B2":
                            validated[idx] = face.shield_color
                    elif face.shield_color == ShieldColor.ANY:
                        validated[idx] = ShieldColor.BLUE

            # 6. Gain Resource Outputs on Effective Faces (RULES.md v0.8)
            for idx, die in enumerate(active_dice):
                face = die.current_face
                if not face or face.is_glitch:
                    continue

                if idx not in validated:
                    eff = die.effective_face
                    if eff:
                        player.money += eff.money
                        player.patches += eff.patches
                        player.secrets += eff.secrets
                        if eff.is_star:
                            if eff.star_code == "Y2":
                                distinct_count = len({d.color for d in player.colored_dice})
                                total_payout = min(self.state.config.y2_max_payout, self.state.config.y2_base_payout + distinct_count)
                                bonus = total_payout - eff.money
                                player.money += max(0, bonus)
                            elif eff.star_code == "Y3":
                                if die in player.ready_dice:
                                    player.ready_dice.remove(die)
                                    player.unpatched_dice.append(die)
                else:
                    if face.is_star:
                        if face.star_code == "R1":
                            player.money += 2
                        elif face.star_code in ("G1", "G2"):
                            player.patches += 1

            player.patches = min(player.patches, self.state.config.max_patch_tokens)

            meta["rolled_pool"] = list(active_dice)
            meta["commitments"] = {idx: color.value for idx, color in validated.items()}
            meta["has_rolled"] = True
            meta["has_committed"] = True

            slots = {"red": [], "blue": [], "green": []}
            for idx, color in validated.items():
                slots[color.value].append(active_dice[idx])
            meta["shield_slots"] = slots

            # 6. Track Star availability
            for idx, die in enumerate(active_dice):
                face = die.current_face
                if not face or not face.is_star:
                    continue
                if face.star_code == "B2":
                    if idx not in validated:
                        player.b2_available = True
                elif face.star_code == "Y1":
                    player.y1_available = True
                elif face.star_code == "P1":
                    player.p1_available = True
                elif face.star_code == "P3":
                    if idx in validated:
                        player.p3_available = validated[idx]

    # =========================================================================
    # Phase 2: Rogue Agent Compile (The Cube Tower Drop)
    # =========================================================================

    def compile_drop(self) -> Dict[str, Any]:
        """Executes the Cube Tower drop and attack resolution."""
        if self.phase != 2:
            raise ValueError(f"Cannot compile drop in phase {self.phase} ({self.phase_name})")

        # Build player commitments for engine
        player_commitments: List[Tuple[PlayerState, List[Die], Dict[int, ShieldColor]]] = []
        for pid, player in enumerate(self.state.players):
            if player.is_patient_zero:
                continue
            meta = self.player_meta[pid]
            rolled = meta["rolled_pool"]
            commitments_enum = {
                int(k): ShieldColor(v) for k, v in meta["commitments"].items()
            }
            player_commitments.append((player, rolled, commitments_enum))

        # Execute Phase 2 via engine
        telemetry = self.engine._execute_phase_2(player_commitments)

        # Update last compile result summary
        self.last_compile_result = {
            "round": telemetry.round_number,
            "staged_cubes": {c.value: count for c, count in telemetry.staged_cubes.items()},
            "exited_cubes": {c.value: count for c, count in telemetry.exited_cubes.items()},
            "stuck_cubes_after": {c.value: count for c, count in telemetry.stuck_cubes_after.items()},
            "attack_strengths": {c.value: count for c, count in telemetry.attack_strengths.items()},
            "corruption_track": self.state.corruption_track,
            "version_name": self.state.active_version.name,
            "singularity_triggered": self.state.singularity_triggered,
            "is_final_round": self.state.is_final_round,
            "game_over": self.state.game_over,
        }

        exited = self.last_compile_result["exited_cubes"]
        self.event_log.append(
            f"Cube Tower Drop results: {exited['red']} Red, {exited['blue']} Blue, {exited['green']} Green, {exited['black']} Black."
        )

        # Check end game triggers from Step 2C
        if self.state.game_over:
            # Total Wipeout! Game ends immediately; Phase 3 is skipped
            self.phase = 4
            self.phase_name = "Game Over"
            self.subphase = "game_over"
            end_res = self.engine.evaluate_end_game()
            self.final_result = self._serialize_end_game_result(end_res)
            self.event_log.append("TOTAL WIPEOUT! All corporations suffered Total Breach simultaneously.")
            return self.get_full_state()

        # Transition to Phase 3: Corporate Operations
        self.phase = 3
        self.phase_name = "Corporate Operations"
        self.subphase = "player_turn"

        # Update per-player metadata after Phase 2 attack and wear resolution
        for pid, player in enumerate(self.state.players):
            meta = self.player_meta[pid]
            meta["hired_contractors"] = 0
            # Shield slots have finished blocking/resolving for the round
            meta["shield_slots"] = {"red": [], "blue": [], "green": []}
            # Remove any dice that were worn down to unpatched or destroyed from the rolled pool
            unpatched_ids = {d.die_id for d in player.unpatched_dice}
            ready_ids = {d.die_id for d in player.ready_dice}
            # Active pool in Phase 3 contains non-worn rolled dice that remain active
            meta["rolled_pool"] = [
                d for d in meta.get("rolled_pool", [])
                if d.die_id not in unpatched_ids and d.die_id in ready_ids
            ]

        # Initialize Phase 3 clockwise queue starting with First Player
        num_players = len(self.state.players)
        self.phase3_turn_queue = [
            (self.state.first_player_index + offset) % num_players
            for offset in range(num_players)
        ]

        self.event_log.append(
            f"Phase 3: Corporate Operations begun. First Player turn: {self.player_meta[self.state.first_player_index]['name']}."
        )

        # Advance through eliminated or bot players until a human player's turn or end of round
        self._advance_phase3_turns()
        return self.get_full_state()

    # =========================================================================
    # Phase 3: Corporate Operations (Interactive)
    # =========================================================================

    def _advance_phase3_turns(self) -> None:
        """Processes Phase 3 turns clockwise, automatically executing bots until a human turn or round end."""
        while self.phase3_turn_queue:
            next_pid = self.phase3_turn_queue[0]
            player = self.state.players[next_pid]
            meta = self.player_meta[next_pid]

            # Skip eliminated players
            if player.is_patient_zero:
                self.phase3_turn_queue.pop(0)
                self.event_log.append(f"{meta['name']} is Patient Zero (eliminated, skipping Phase 3).")
                continue

            # If human player's turn: stop and wait for interactive actions
            if meta["is_human"]:
                self.active_player_index = next_pid
                meta["purchases_this_turn"] = 0
                meta["dirty_income_taken_this_turn"] = False
                return

            # Bot player turn: execute automatically
            self.active_player_index = next_pid
            self.phase3_turn_queue.pop(0)
            self._execute_bot_phase3(player, meta)

        # All players have finished Phase 3 -> complete round cleanup
        self._complete_round()

    def _execute_bot_phase3(self, player: PlayerState, meta: Dict[str, Any]) -> None:
        """Executes Phase 3 plan for a single bot player."""
        plan: Phase3ActionPlan = player.bot.take_phase3_actions(player, self.state, self.engine.rng)

        # 1. Dirty Income
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
            backlash_idx = plan.dirty_income_backlash_die_index
            if not (0 <= backlash_idx < len(player.ready_dice)):
                backlash_idx = 0
            demoted = player.ready_dice.pop(backlash_idx)
            player.unpatched_dice.append(demoted)
            player.total_dirty_income_taken += 1
            self.event_log.append(f"{meta['name']} (Bot) took Dirty Income: +$3, -1 Secret, +1 Black Cube.")

        # 2. Star Special Actions
        if plan.use_b2_secret and player.b2_available:
            cost = self.state.config.b2_secret_cost
            cap = self.state.config.b2_secret_cap
            if player.money >= cost and player.secrets < cap:
                player.money -= cost
                player.secrets = min(cap, player.secrets + 1)
                player.b2_available = False
                self.event_log.append(f"{meta['name']} (Bot) used B2 Deep R&D: +1 Secret for ${cost}.")

        if plan.use_y1_secret and player.y1_available:
            if player.money >= 6 and player.secrets < 10:
                player.money -= 6
                player.secrets = min(10, player.secrets + 1)
                player.y1_available = False
                self.event_log.append(f"{meta['name']} (Bot) used Y1 Algorithmic Trading: +1 Secret for $6.")

        if plan.p1_cube_choice in (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN) and player.p1_available:
            self.state.staging_cup[plan.p1_cube_choice] = self.state.staging_cup.get(plan.p1_cube_choice, 0) + 1
            player.p1_available = False

        if plan.p3_cube_choice in (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN) and player.p3_available:
            if plan.p3_cube_choice.value == player.p3_available.value:
                p3_cost = self.state.config.p3_cube_cash_cost
                if player.money >= p3_cost:
                    player.money -= p3_cost
                    self.state.staging_cup[plan.p3_cube_choice] = self.state.staging_cup.get(plan.p3_cube_choice, 0) + 1
                    player.p3_available = None

        # 3. Patching
        patch_cash_cost = self.state.config.patch_cash_cost
        for patch_act in plan.patch_actions:
            if not player.unpatched_dice:
                break
            idx = patch_act.get("die_index", 0)
            if not isinstance(idx, int) or not (0 <= idx < len(player.unpatched_dice)):
                idx = 0
            use_cash = bool(patch_act.get("use_cash", False))

            if use_cash:
                if player.money >= patch_cash_cost:
                    player.money -= patch_cash_cost
                    patched = player.unpatched_dice.pop(idx)
                    player.ready_dice.append(patched)
            else:
                if player.patches >= self.state.config.patch_token_cost:
                    player.patches -= self.state.config.patch_token_cost
                    patched = player.unpatched_dice.pop(idx)
                    player.ready_dice.append(patched)

        # 4. Market Purchases
        purchases = 0
        for color in plan.market_purchases:
            if purchases >= self.state.config.max_market_purchases_per_turn:
                break
            cost = 4 if color in (DieColor.RED, DieColor.GREEN, DieColor.PURPLE) else 5
            if self.state.market.get(color, 0) > 0 and player.money >= cost:
                player.money -= cost
                self.state.market[color] -= 1
                purchases += 1
                new_die = create_colored_die(
                    color=color,
                    die_id=self.state.next_die_id,
                    variant_card=self.state.variant_cards.get(color),
                )
                self.state.next_die_id += 1
                player.ready_dice.append(new_die)
                self.event_log.append(f"{meta['name']} (Bot) bought {color.value.capitalize()} Die.")

        player.patches = min(player.patches, self.state.config.max_patch_tokens)

    def buy_die(self, player_id: int, color_str: str) -> Dict[str, Any]:
        """Human action: purchases a colored software module die from the market."""
        if self.phase != 3:
            raise ValueError(f"Cannot purchase dice in phase {self.phase}")
        if player_id != self.active_player_index:
            raise ValueError(f"Not player {player_id}'s turn (current: {self.active_player_index})")

        player = self.state.players[player_id]
        meta = self.player_meta[player_id]

        if player.is_patient_zero:
            raise ValueError("Eliminated players cannot perform operations")
        if meta["purchases_this_turn"] >= self.state.config.max_market_purchases_per_turn:
            raise ValueError(f"Purchase limit reached ({self.state.config.max_market_purchases_per_turn} dice per turn)")

        color = DieColor(color_str.lower())
        cost = 4 if color in (DieColor.RED, DieColor.GREEN, DieColor.PURPLE) else 5

        if self.state.market.get(color, 0) <= 0:
            raise ValueError(f"Market stock for {color.value} is depleted")
        if player.money < cost:
            raise ValueError(f"Insufficient funds: die costs ${cost}, but player only has ${player.money}")

        player.money -= cost
        self.state.market[color] -= 1
        meta["purchases_this_turn"] += 1

        new_die = create_colored_die(
            color=color,
            die_id=self.state.next_die_id,
            variant_card=self.state.variant_cards.get(color),
        )
        self.state.next_die_id += 1
        player.ready_dice.append(new_die)

        self.event_log.append(
            f"{meta['name']} purchased a {color.value.capitalize()} Die for ${cost}. (Stock remaining: {self.state.market[color]})."
        )
        return self.get_full_state()

    def patch_die(self, player_id: int, die_index: int, use_cash: bool) -> Dict[str, Any]:
        """Human action: patches an unpatched die back to the ready zone."""
        if self.phase != 3:
            raise ValueError(f"Cannot patch dice in phase {self.phase}")
        if player_id != self.active_player_index:
            raise ValueError(f"Not player {player_id}'s turn (current: {self.active_player_index})")

        player = self.state.players[player_id]
        meta = self.player_meta[player_id]

        if player.is_patient_zero:
            raise ValueError("Eliminated players cannot perform operations")
        if not (0 <= die_index < len(player.unpatched_dice)):
            raise ValueError(f"Invalid die_index {die_index} in unpatched zone (size: {len(player.unpatched_dice)})")

        patch_cash_cost = self.state.config.patch_cash_cost

        if use_cash:
            if player.money < patch_cash_cost:
                raise ValueError(f"Insufficient cash for patching: costs ${patch_cash_cost}, player has ${player.money}")
            player.money -= patch_cash_cost
            cost_desc = f"${patch_cash_cost} cash"
        else:
            if player.patches < self.state.config.patch_token_cost:
                raise ValueError(f"Insufficient patch tokens: costs {self.state.config.patch_token_cost} 🔧, player has {player.patches} 🔧")
            player.patches -= self.state.config.patch_token_cost
            cost_desc = "1 🔧 token"

        patched_die = player.unpatched_dice.pop(die_index)
        player.ready_dice.append(patched_die)

        self.event_log.append(
            f"{meta['name']} patched {patched_die.color.value.capitalize()} Die using {cost_desc}."
        )
        return self.get_full_state()

    def take_dirty_income(self, player_id: int, backlash_die_index: int = 0) -> Dict[str, Any]:
        """Human action: corrupts the Rogue Agent ('Dirty Income') for quick cash."""
        if self.phase != 3:
            raise ValueError(f"Cannot take dirty income in phase {self.phase}")
        if player_id != self.active_player_index:
            raise ValueError(f"Not player {player_id}'s turn (current: {self.active_player_index})")

        player = self.state.players[player_id]
        meta = self.player_meta[player_id]

        if player.is_patient_zero:
            raise ValueError("Eliminated players cannot perform operations")
        if meta["dirty_income_taken_this_turn"]:
            raise ValueError("Dirty Income has already been taken this turn (limit 1x per turn)")

        # Precondition checks per RULES.md Section 4 Phase 3 Step 3:
        # Must have at least 1 ready die and strictly > 1 secret (cannot be taken at <= 1 secret)
        if player.secrets <= self.state.config.dirty_income_secret_cost:
            raise ValueError(
                f"Cannot take Dirty Income with {player.secrets} Secret(s) (must have strictly > {self.state.config.dirty_income_secret_cost})"
            )
        if len(player.ready_dice) < 1:
            raise ValueError("Cannot take Dirty Income: must have at least 1 Ready die for Technical Debt Backlash")

        if not (0 <= backlash_die_index < len(player.ready_dice)):
            backlash_die_index = 0

        # Execute Dirty Income
        player.secrets -= self.state.config.dirty_income_secret_cost
        player.money += self.state.config.dirty_income_cash
        self.state.staging_cup[CubeColor.BLACK] = (
            self.state.staging_cup.get(CubeColor.BLACK, 0)
            + self.state.config.dirty_income_black_cubes
        )

        # Technical Debt Backlash: demote chosen ready die to unpatched
        backlash_die = player.ready_dice.pop(backlash_die_index)
        player.unpatched_dice.append(backlash_die)

        meta["dirty_income_taken_this_turn"] = True
        player.total_dirty_income_taken += 1

        self.event_log.append(
            f"{meta['name']} took Dirty Income: gained +${self.state.config.dirty_income_cash}, paid 1 Secret, added 1 Black Cube to Staging Cup. Backlash demoted {backlash_die.color.value.capitalize()} Die."
        )
        return self.get_full_state()

    def execute_star_action(
        self,
        player_id: int,
        action_type: str,
        cube_color: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Human action: executes rolled Star ability during Phase 3."""
        if self.phase != 3:
            raise ValueError(f"Cannot execute star actions in phase {self.phase}")
        if player_id != self.active_player_index:
            raise ValueError(f"Not player {player_id}'s turn")

        player = self.state.players[player_id]
        meta = self.player_meta[player_id]

        if action_type == "B2":
            if not player.b2_available:
                raise ValueError("B2 Deep R&D Vault ability is not available this turn")
            cost = self.state.config.b2_secret_cost
            cap = self.state.config.b2_secret_cap
            if player.money < cost:
                raise ValueError(f"B2 requires ${cost} cash")
            if player.secrets >= cap:
                raise ValueError(f"Secrets already at maximum capacity ({cap})")
            player.money -= cost
            player.secrets += 1
            player.b2_available = False
            self.event_log.append(f"{meta['name']} activated B2 Deep R&D Vault: +1 Corporate Secret for ${cost}.")

        elif action_type == "Y1":
            if not player.y1_available:
                raise ValueError("Y1 Algorithmic Trading ability is not available this turn")
            if player.money < 6:
                raise ValueError("Y1 requires $6 cash ($4 roll refund + $2 secret fee)")
            if player.secrets >= 10:
                raise ValueError("Secrets already at maximum capacity (10)")
            player.money -= 6
            player.secrets += 1
            player.y1_available = False
            self.event_log.append(f"{meta['name']} activated Y1 Algorithmic Trading: converted $6 into +1 Secret.")

        elif action_type == "P1":
            if not player.p1_available:
                raise ValueError("P1 Zero-Day Injection ability is not available this turn")
            if not cube_color or cube_color.lower() not in ("red", "blue", "green"):
                raise ValueError("P1 requires selecting an attack cube color (red, blue, or green)")
            chosen = CubeColor(cube_color.lower())
            self.state.staging_cup[chosen] = self.state.staging_cup.get(chosen, 0) + 1
            player.p1_available = False
            self.event_log.append(f"{meta['name']} activated P1 Zero-Day: added 1 {chosen.value.capitalize()} Cube to Staging Cup.")

        elif action_type == "P3":
            if not player.p3_available:
                raise ValueError("P3 Packet Deflection ability is not available this turn")
            blocked_color = player.p3_available.value
            if cube_color and cube_color.lower() != blocked_color:
                raise ValueError(f"P3 must add a cube matching the blocked color ({blocked_color})")
            cost = self.state.config.p3_cube_cash_cost
            if player.money < cost:
                raise ValueError(f"P3 requires ${cost} cash")
            player.money -= cost
            chosen = CubeColor(blocked_color)
            self.state.staging_cup[chosen] = self.state.staging_cup.get(chosen, 0) + 1
            player.p3_available = None
            self.event_log.append(f"{meta['name']} activated P3 Packet Deflection: paid ${cost} to add 1 {chosen.value.capitalize()} Cube to Staging Cup.")

        else:
            raise ValueError(f"Unsupported star action type: {action_type}")

        return self.get_full_state()

    def end_turn(self, player_id: int) -> Dict[str, Any]:
        """Human action: finishes Phase 3 operations and advances clockwise."""
        if self.phase != 3:
            raise ValueError(f"Cannot end turn in phase {self.phase}")
        if player_id != self.active_player_index:
            raise ValueError(f"Not player {player_id}'s turn (current: {self.active_player_index})")

        meta = self.player_meta[player_id]
        self.event_log.append(f"{meta['name']} ended operations turn.")

        if self.phase3_turn_queue and self.phase3_turn_queue[0] == player_id:
            self.phase3_turn_queue.pop(0)

        # Advance to next turn (or complete round)
        self._advance_phase3_turns()
        return self.get_full_state()

    def _complete_round(self) -> None:
        """Executes round cleanup and either starts the next round or concludes the game."""
        num_players = len(self.state.players)

        # Check Final Round condition
        if self.state.is_final_round:
            self.state.game_over = True
            self.phase = 4
            self.phase_name = "Game Over"
            self.subphase = "game_over"
            end_res = self.engine.evaluate_end_game()
            self.final_result = self._serialize_end_game_result(end_res)
            self.event_log.append(
                f"MATCH CONCLUDED! Winner: {self.player_meta[end_res.winner_id]['name'] if end_res.winner_id is not None else 'None'}."
            )
            return

        # Advance First Player marker clockwise
        self.state.first_player_index = (self.state.first_player_index + 1) % num_players

        # Increment round counter
        self.state.current_round += 1
        if self.state.current_round > self.state.config.max_rounds:
            self.state.game_over = True
            self.state.end_reason = EndGameReason.ROUND_LIMIT
            self.phase = 4
            self.phase_name = "Game Over"
            self.subphase = "game_over"
            end_res = self.engine.evaluate_end_game()
            self.final_result = self._serialize_end_game_result(end_res)
            self.event_log.append("Match reached round limit.")
            return

        # Start next round Phase 1
        self._start_phase_1()

    # =========================================================================
    # State Inspection & Serialization
    # =========================================================================

    def _serialize_end_game_result(self, res: EndGameResult) -> Dict[str, Any]:
        return {
            "end_reason": res.end_reason.value if isinstance(res.end_reason, EndGameReason) else str(res.end_reason),
            "total_rounds": res.total_rounds,
            "winner_id": res.winner_id,
            "winner_name": self.player_meta[res.winner_id]["name"] if res.winner_id is not None else "None",
            "is_total_wipeout": res.is_total_wipeout,
            "singularity_reached": res.singularity_reached,
            "rankings": res.rankings,
        }

    def get_action_capabilities(self, player_id: int) -> Dict[str, Any]:
        """Calculates valid action flags for the specified player given current state."""
        if player_id not in self.player_meta or self.engine is None:
            return {}

        player = self.state.players[player_id]
        meta = self.player_meta[player_id]
        is_active = (player_id == self.active_player_index)
        is_eliminated = player.is_patient_zero

        # Available patch tokens: held tokens + any patches showing on kept unlocked rolled faces minus spent_from_kept
        kept_patches = 0
        if meta.get("rolled_pool"):
            locked = set(meta.get("locked_reroll_indices", []))
            for i, d in enumerate(meta["rolled_pool"]):
                if i not in locked and d.current_face and d.current_face.patches > 0:
                    kept_patches += d.current_face.patches
        avail_patches = player.patches + max(0, kept_patches - meta.get("spent_from_kept", 0))

        can_roll = (self.phase == 1 and not meta["has_rolled"] and not is_eliminated)
        already_hired = meta.get("hired_contractors", 0)
        max_contractors = self.state.config.contractor_max_hire
        if already_hired < max_contractors:
            next_contractor_cost = self.state.config.get_contractor_cost_for_hire(1, already_hired=already_hired)
        else:
            next_contractor_cost = None

        can_hire_contractors = (
            self.phase == 1
            and not meta["has_rolled"]
            and not is_eliminated
            and already_hired < max_contractors
            and self.state.contractor_supply > 0
            and next_contractor_cost is not None
            and player.money >= next_contractor_cost
        )
        rolled_pool = meta.get("rolled_pool", [])
        can_reroll = (
            self.phase == 1
            and meta["has_rolled"]
            and not meta["has_committed"]
            and not is_eliminated
            and meta.get("rerolls_remaining", 0) > 0
            and any(not getattr(d, "is_locked", False) for d in rolled_pool)
        )
        can_debug_unlock = (
            self.phase == 1
            and meta["has_rolled"]
            and not meta["has_committed"]
            and not is_eliminated
            and player.patches > 0
            and any(getattr(d, "is_locked", False) for d in rolled_pool)
        )
        can_hotfix = (self.phase == 1 and meta["has_rolled"] and not meta["has_committed"] and avail_patches > 0 and not is_eliminated)
        can_commit = (self.phase == 1 and meta["has_rolled"] and not meta["has_committed"] and not is_eliminated)
        can_compile = (self.phase == 2 and self.subphase == "ready_for_compile")

        patch_cost = self.state.config.patch_cash_cost
        can_patch_cash = (
            self.phase == 3
            and is_active
            and not is_eliminated
            and len(player.unpatched_dice) > 0
            and player.money >= patch_cost
        )
        can_patch_token = (
            self.phase == 3
            and is_active
            and not is_eliminated
            and len(player.unpatched_dice) > 0
            and player.patches >= self.state.config.patch_token_cost
        )
        can_dirty = (
            self.phase == 3
            and is_active
            and not is_eliminated
            and not meta["dirty_income_taken_this_turn"]
            and player.secrets > self.state.config.dirty_income_secret_cost
            and len(player.ready_dice) >= 1
        )
        can_end_turn = (self.phase == 3 and is_active and not is_eliminated)

        # Market purchase availability per color
        can_buy = {}
        for color in [DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW, DieColor.PURPLE]:
            cost = 4 if color in (DieColor.RED, DieColor.GREEN, DieColor.PURPLE) else 5
            can_buy[color.value] = (
                self.phase == 3
                and is_active
                and not is_eliminated
                and meta["purchases_this_turn"] < self.state.config.max_market_purchases_per_turn
                and self.state.market.get(color, 0) > 0
                and player.money >= cost
            )

        # Star actions
        can_star = {
            "B2": bool(
                self.phase == 3
                and is_active
                and player.b2_available
                and player.money >= self.state.config.b2_secret_cost
                and player.secrets < self.state.config.b2_secret_cap
            ),
            "Y1": bool(self.phase == 3 and is_active and player.y1_available and player.money >= 6 and player.secrets < 10),
            "P1": bool(self.phase == 3 and is_active and player.p1_available),
            "P3": bool(
                self.phase == 3
                and is_active
                and player.p3_available is not None
                and player.money >= self.state.config.p3_cube_cash_cost
            ),
        }

        return {
            "can_roll": can_roll,
            "can_hire_contractors": can_hire_contractors,
            "next_contractor_cost": next_contractor_cost,
            "can_reroll": can_reroll,
            "can_debug_unlock": can_debug_unlock,
            "can_hotfix": can_hotfix,
            "can_commit": can_commit,
            "can_compile": can_compile,
            "can_buy": can_buy,
            "can_patch_cash": can_patch_cash,
            "can_patch_token": can_patch_token,
            "can_dirty_income": can_dirty,
            "can_star": can_star,
            "can_end_turn": can_end_turn,
        }

    def get_full_state(self) -> Dict[str, Any]:
        """Returns the complete serialized GameState JSON."""
        # Find primary human player for action capabilities
        human_pids = [pid for pid, m in self.player_meta.items() if m["is_human"]]
        primary_human = human_pids[0] if human_pids else self.active_player_index

        player_ranks = {}
        if self.final_result and "rankings" in self.final_result:
            for r in self.final_result["rankings"]:
                player_ranks[r["player_id"]] = r.get("rank")

        controller_meta = {
            "game_id": self.game_id,
            "phase": self.phase,
            "phase_name": self.phase_name,
            "subphase": self.subphase,
            "active_player_index": self.active_player_index,
            "players": self.player_meta,
            "player_ranks": player_ranks,
            "last_compile_result": self.last_compile_result,
            "action_capabilities": self.get_action_capabilities(primary_human),
            "event_log": list(reversed(self.event_log[-50:])),  # Most recent first
            "final_result": self.final_result,
        }

        return GameStateSerializer.serialize_game_state(self.state, controller_meta)
