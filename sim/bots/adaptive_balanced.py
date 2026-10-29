from __future__ import annotations

import random
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from sim.config import CubeColor, DieColor, ShieldColor
from sim.entities import ArchetypeCode
from sim.bots.base import BaseBot, Phase3ActionPlan, choose_backlash_die_index, plan_final_round_repairs

if TYPE_CHECKING:
    from sim.engine import GameState, PlayerState
    from sim.entities import Die, Face


class AdaptiveBalancedBot(BaseBot):
    """Balanced bot: monitors threat levels, hedges shields, patches worn dice, and buys counters."""

    def __init__(self, bot_id: int) -> None:
        super().__init__(bot_id, name="AdaptiveBalancedBot")

    def _get_threat_levels(
        self, staging_cubes: Dict[CubeColor, int], stuck_cubes: Dict[CubeColor, int]
    ) -> Dict[CubeColor, int]:
        return {
            color: staging_cubes.get(color, 0) + stuck_cubes.get(color, 0)
            for color in [CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN]
        }

    def choose_contractor_hires(
        self,
        player_state: PlayerState,
        contractor_supply: int,
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        rng: random.Random,
    ) -> int:
        if contractor_supply <= 0 or player_state.money < 4:
            return 0
        threats = self._get_threat_levels(staging_cubes, stuck_cubes)
        total_threat = sum(threats.values())
        if total_threat >= 8 and player_state.money >= 9:
            return min(3, contractor_supply)
        elif total_threat >= 6 and player_state.money >= 6:
            return min(2, contractor_supply)
        elif total_threat >= 3 and player_state.money >= 4:
            return min(1, contractor_supply)
        return 0

    def choose_operator_ability(
        self,
        player_state: PlayerState,
        contractor_supply: int,
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        rng: random.Random,
        corruption_track: int = 0,
    ) -> bool:
        if contractor_supply <= 0:
            return False
        threats = self._get_threat_levels(staging_cubes, stuck_cubes)
        total_threat = sum(threats.values())
        if corruption_track >= 3:
            return True
        return total_threat >= 3 or len(player_state.ready_dice) <= 4

    def choose_operator_buy_third_die(
        self,
        player_state: PlayerState,
        contractor_supply: int,
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        rng: random.Random,
        corruption_track: int = 0,
    ) -> bool:
        if contractor_supply <= 0 or player_state.money < 3:
            return False
        threats = self._get_threat_levels(staging_cubes, stuck_cubes)
        return sum(threats.values()) >= 6

    def choose_prodigy_ability(
        self,
        player_state: PlayerState,
        active_dice: List[Die],
        rerolls_remaining: int,
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        directive_code: str,
        rng: random.Random,
        corruption_track: int = 0,
    ) -> bool:
        has_locked = any(d.is_locked for d in active_dice)
        if not has_locked:
            return False
        if corruption_track >= 3:
            return True
        return any(d.current_face and d.current_face.is_glitch for d in active_dice) or has_locked

    def choose_acoustic_ability(
        self,
        player_state: PlayerState,
        qualifying_colors: List[CubeColor],
        exited_cubes: Dict[CubeColor, int],
        active_version_str: str,
        rng: random.Random,
        corruption_track: int = 0,
    ) -> Optional[CubeColor]:
        if not qualifying_colors:
            return None
        if CubeColor.BLUE in qualifying_colors:
            return CubeColor.BLUE
        if CubeColor.RED in qualifying_colors:
            return CubeColor.RED
        return qualifying_colors[0]

    def choose_spook_ability(
        self,
        player_state: PlayerState,
        secrets_at_risk: int,
        active_version_str: str,
        rng: random.Random,
        corruption_track: int = 0,
    ) -> int:
        if player_state.money <= 0 or secrets_at_risk <= 0:
            return 0
        if player_state.secrets <= 4 or secrets_at_risk >= 2 or corruption_track >= 3:
            return min(player_state.money, secrets_at_risk)
        return min(player_state.money, min(secrets_at_risk, 1))

    def choose_debug_unlocks(
        self,
        player_state: PlayerState,
        active_dice: List[Die],
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        directive_code: str,
        rng: random.Random,
    ) -> List[int]:
        if player_state.patches <= 0:
            return []
        unlocks: List[int] = []
        for idx, die in enumerate(active_dice):
            if len(unlocks) >= player_state.patches:
                break
            if die.is_locked:
                unlocks.append(idx)
        return unlocks

    def choose_yahtzee_rerolls(
        self,
        player_state: PlayerState,
        active_dice: List[Die],
        rerolls_remaining: int,
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        directive_code: str,
        rng: random.Random,
    ) -> List[int]:
        if rerolls_remaining <= 0:
            return []
        threats = self._get_threat_levels(staging_cubes, stuck_cubes)
        red_shields = sum(
            d.current_face.block_amount
            for d in active_dice
            if d.current_face and d.current_face.shield_color in (ShieldColor.RED, ShieldColor.ANY)
        )
        blue_shields = sum(
            (1 if (d.current_face and d.current_face.has_shield_option) else d.current_face.block_amount)
            for d in active_dice
            if d.current_face and (
                d.current_face.shield_color in (ShieldColor.BLUE, ShieldColor.ANY)
                or d.current_face.has_shield_option
            )
        )
        green_shields = sum(
            d.current_face.block_amount
            for d in active_dice
            if d.current_face and d.current_face.shield_color in (ShieldColor.GREEN, ShieldColor.ANY)
        )

        rerolls: List[int] = []
        for idx, die in enumerate(active_dice):
            if die.is_locked:
                continue
            face = die.current_face
            if not face:
                continue
            if face.is_glitch:
                rerolls.append(idx)
            elif not face.is_shield and not face.has_shield_option and (
                threats[CubeColor.BLUE] > blue_shields
                or threats[CubeColor.RED] > red_shields
                or threats[CubeColor.GREEN] > green_shields
            ):
                rerolls.append(idx)
            elif not face.is_shield and not face.has_shield_option and not face.has_cash_option and face.money <= 1 and face.patches == 0:
                rerolls.append(idx)
        return rerolls

    def choose_hotfix_rerolls(
        self,
        player_state: PlayerState,
        rolled_dice: List[Die],
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        rng: random.Random,
    ) -> List[int]:
        rerolls: List[int] = []
        available_patches = player_state.patches
        threats = self._get_threat_levels(staging_cubes, stuck_cubes)

        # Count current shields rolled
        red_shields = sum(
            d.current_face.block_amount
            for d in rolled_dice
            if d.current_face and d.current_face.shield_color in (ShieldColor.RED, ShieldColor.ANY)
        )
        blue_shields = sum(
            (1 if (d.current_face and d.current_face.has_shield_option) else d.current_face.block_amount)
            for d in rolled_dice
            if d.current_face and (
                d.current_face.shield_color in (ShieldColor.BLUE, ShieldColor.ANY)
                or d.current_face.has_shield_option
            )
        )

        # Reroll non-shield faces if we lack defense and have patches
        for idx, die in enumerate(rolled_dice):
            if available_patches <= len(rerolls):
                break
            face = die.current_face
            if not face:
                continue
            if face.name == "Idle (0)":
                rerolls.append(idx)
            elif (
                not face.is_shield
                and not face.has_shield_option
                and (threats[CubeColor.RED] > red_shields or threats[CubeColor.BLUE] > blue_shields)
            ):
                rerolls.append(idx)

        return rerolls

    def declare_choices(
        self,
        player_state: PlayerState,
        active_dice: Optional[List[Die]] = None,
        staging_cubes: Optional[Dict[CubeColor, int]] = None,
        stuck_cubes: Optional[Dict[CubeColor, int]] = None,
        directive_code: str = "",
        rng: Optional[random.Random] = None,
        rolled_dice: Optional[List[Die]] = None,
    ) -> Dict[int, int]:
        dice = active_dice if active_dice is not None else (rolled_dice or [])
        threats = self._get_threat_levels(staging_cubes or {}, stuck_cubes or {})
        declarations: Dict[int, int] = {}
        for idx, die in enumerate(dice):
            face = die.current_face
            if not face or not face.is_choice:
                continue
            if face.has_shield_option:
                declarations[idx] = 0 if threats[CubeColor.BLUE] > 0 else 1
            elif face.name == "+$1 / +1 🔧":
                need_patch = (player_state.patches < 2) or (len(player_state.unpatched_dice) > player_state.patches)
                declarations[idx] = 1 if need_patch else 0
            elif face.name == "+1 🔧 / +$1":
                need_patch = (player_state.patches < 2) or (len(player_state.unpatched_dice) > player_state.patches)
                declarations[idx] = 0 if need_patch else 1
            else:
                declarations[idx] = 0
        return declarations

    def commit_shields(
        self,
        player_state: PlayerState,
        rolled_dice: List[Die],
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        directive_code: str,
        rng: random.Random,
    ) -> Dict[int, ShieldColor]:
        threats = self._get_threat_levels(staging_cubes, stuck_cubes)
        assignments: Dict[int, ShieldColor] = {}

        # First commit fixed colored shields
        committed_red = 0
        committed_blue = 0
        committed_green = 0

        any_shield_indices: List[int] = []
        blue_choice_indices: List[int] = []

        for idx, die in enumerate(rolled_dice):
            face = die.current_face
            if not face or face.is_glitch:
                continue

            if face.is_shield:
                if face.shield_color == ShieldColor.RED:
                    assignments[idx] = ShieldColor.RED
                    committed_red += face.block_amount
                elif face.shield_color == ShieldColor.BLUE:
                    assignments[idx] = ShieldColor.BLUE
                    committed_blue += face.block_amount
                elif face.shield_color == ShieldColor.GREEN:
                    assignments[idx] = ShieldColor.GREEN
                    committed_green += face.block_amount
                elif face.shield_color == ShieldColor.ANY:
                    any_shield_indices.append(idx)
            elif face.has_shield_option:
                blue_choice_indices.append(idx)

        # Assign Blue choice faces if Blue threat > committed_blue
        for idx in blue_choice_indices:
            if threats[CubeColor.BLUE] > committed_blue:
                assignments[idx] = ShieldColor.BLUE
                committed_blue += 1

        # Assign Generic Any shields prioritizing Blue (protect Secrets) first, then Red, then Green
        for idx in any_shield_indices:
            if threats[CubeColor.BLUE] > committed_blue:
                best_color = ShieldColor.BLUE
            elif threats[CubeColor.RED] > committed_red:
                best_color = ShieldColor.RED
            elif threats[CubeColor.GREEN] > committed_green:
                best_color = ShieldColor.GREEN
            else:
                best_color = ShieldColor.BLUE

            assignments[idx] = best_color
            if best_color == ShieldColor.BLUE:
                committed_blue += 1
            elif best_color == ShieldColor.RED:
                committed_red += 1
            else:
                committed_green += 1

        return assignments

    def take_phase3_actions(
        self,
        player_state: PlayerState,
        game_state: GameState,
        rng: random.Random,
    ) -> Phase3ActionPlan:
        plan = Phase3ActionPlan()
        current_money = player_state.money
        current_patches = player_state.patches
        threats = self._get_threat_levels(game_state.staging_cup, game_state.tower.stuck_cubes)
        total_threat = sum(threats.values())
        is_final_round = getattr(game_state, "is_final_round", False)
        cash_cushion = 0 if is_final_round else 2

        active_ver = game_state.active_version.version_str

        # 0. Consultancy Archetype Phase 3 Abilities
        if (
            player_state.archetype
            and player_state.archetype.code == ArchetypeCode.PHREAKER
            and player_state.is_ability_available(active_ver)
            and len(player_state.unpatched_dice) >= 1
        ):
            plan.use_phreaker_ability = True

        preferred_colors = [DieColor.BLUE, DieColor.RED, DieColor.GREEN, DieColor.YELLOW]
        if threats[CubeColor.RED] > threats[CubeColor.BLUE]:
            preferred_colors = [DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW]

        if (
            player_state.archetype
            and player_state.archetype.code == ArchetypeCode.CIPHER
            and player_state.is_ability_available(active_ver)
        ):
            discounted_colors = []
            for c in preferred_colors + [DieColor.BLUE, DieColor.RED, DieColor.GREEN, DieColor.YELLOW, DieColor.PURPLE]:
                if c not in [dc[0] for dc in discounted_colors] and game_state.market.get(c, 0) > 0:
                    cost = (4 if c in (DieColor.RED, DieColor.GREEN, DieColor.PURPLE) else 5) - game_state.config.cipher_market_discount
                    if current_money - cost >= cash_cushion:
                        discounted_colors.append((c, cost))

            if discounted_colors and (current_money >= 3 or player_state.secrets <= 1 or is_final_round):
                plan.use_cipher_ability = True
                plan.cipher_mode = "BUY_FREE_DIE"
                plan.cipher_free_die_color = discounted_colors[0][0]
                current_money -= discounted_colors[0][1]
            elif not is_final_round and player_state.secrets > game_state.config.dirty_income_secret_cost:
                plan.use_cipher_ability = True
                plan.cipher_mode = "DIRTY_INCOME"

        # 1. Dirty Income: take dirty income if broke, has ready dice, secrets > 1, and threat is manageable (never in final round)
        wants_dirty_income = (
            not is_final_round
            and (
                (
                    current_money < 3
                    and player_state.secrets > game_state.config.dirty_income_secret_cost
                    and (plan.cipher_mode == "DIRTY_INCOME" or len(player_state.ready_dice) >= 1)
                    and total_threat <= 6
                )
                or (plan.use_cipher_ability and plan.cipher_mode == "DIRTY_INCOME")
            )
        )

        if not is_final_round and wants_dirty_income and player_state.secrets > game_state.config.dirty_income_secret_cost:
            plan.take_dirty_income = True
            plan.dirty_income_backlash_die_index = choose_backlash_die_index(player_state.ready_dice)
            current_money += game_state.config.dirty_income_cash

        # 2. Patching: patch worn dice using tokens first, then cash if preserving cushion
        patch_cash_cost = (
            3
            if game_state.active_directive_code == "POLYMORPHIC_WORM"
            else game_state.config.patch_cash_cost
        )

        if is_final_round:
            current_money, current_patches = plan_final_round_repairs(
                player_state, game_state, current_money, current_patches, patch_cash_cost, plan
            )
        else:
            start_patch_idx = 2 if plan.use_phreaker_ability else 0
            for idx in range(start_patch_idx, len(player_state.unpatched_dice)):
                if current_patches > 0:
                    plan.patch_actions.append({"die_index": idx, "use_cash": False})
                    current_patches -= 1
                elif current_money - patch_cash_cost >= cash_cushion:
                    plan.patch_actions.append({"die_index": idx, "use_cash": True})
                    current_money -= patch_cash_cost

        # 3. Market Purchases: buy counter dice matching high threats (respecting cushion)
        purchases = 0
        preferred_colors = [DieColor.BLUE, DieColor.RED, DieColor.GREEN, DieColor.YELLOW]
        if threats[CubeColor.RED] > threats[CubeColor.BLUE]:
            preferred_colors = [DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW]

        for color in preferred_colors:
            if purchases >= game_state.config.max_market_purchases_per_turn:
                break
            cost = 4 if color in (DieColor.RED, DieColor.GREEN, DieColor.PURPLE) else 5
            if game_state.market.get(color, 0) > 0 and (current_money - cost >= cash_cushion):
                plan.market_purchases.append(color)
                current_money -= cost
                purchases += 1

        # 4. In Final Round: spend remaining cash on any available market dice
        if is_final_round and purchases < game_state.config.max_market_purchases_per_turn:
            for color in [DieColor.YELLOW, DieColor.BLUE, DieColor.RED, DieColor.GREEN, DieColor.PURPLE]:
                if purchases >= game_state.config.max_market_purchases_per_turn:
                    break
                cost = 4 if color in (DieColor.RED, DieColor.GREEN, DieColor.PURPLE) else 5
                if game_state.market.get(color, 0) > 0 and current_money >= cost:
                    plan.market_purchases.append(color)
                    current_money -= cost
                    purchases += 1

        return plan


