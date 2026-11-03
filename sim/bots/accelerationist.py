from __future__ import annotations

import random
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from sim.config import CubeColor, DieColor, ShieldColor
from sim.entities import ArchetypeCode, CompanyCode, WhiteHatCode
from sim.bots.base import BaseBot, Phase3ActionPlan, choose_backlash_die_index, plan_final_round_repairs

if TYPE_CHECKING:
    from sim.engine import GameState, PlayerState
    from sim.entities import Die, Face


class AccelerationistBot(BaseBot):
    """Rushes corruption and Singularity by weaponizing the Cube Tower and taking Dirty Income."""

    def __init__(self, bot_id: int) -> None:
        super().__init__(bot_id, name="AccelerationistBot")

    def choose_contractor_hires(
        self,
        player_state: PlayerState,
        contractor_supply: int,
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        rng: random.Random,
    ) -> int:
        if contractor_supply > 0 and player_state.money >= 5 and player_state.secrets <= 3:
            return 1
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
        return contractor_supply > 0

    def choose_operator_buy_third_die(
        self,
        player_state: PlayerState,
        contractor_supply: int,
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        rng: random.Random,
        corruption_track: int = 0,
    ) -> bool:
        return contractor_supply > 0 and player_state.money >= 3

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
        return any(d.is_locked for d in active_dice)

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
        if player_state.secrets <= 4 or corruption_track >= 3:
            return min(player_state.money, secrets_at_risk)
        return 0

    choose_meridian_override = choose_operator_ability
    choose_helix_override = choose_prodigy_ability
    choose_aegis_override = choose_acoustic_ability
    choose_dto_override = choose_spook_ability

    def choose_debug_unlocks(
        self,
        player_state: PlayerState,
        active_dice: List[Die],
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        directive_code: str,
        rng: random.Random,
    ) -> List[int]:
        """DEPRECATED in v0.23.0. Delegated to BaseBot (always returns [])."""
        return super().choose_debug_unlocks(
            player_state, active_dice, staging_cubes, stuck_cubes, directive_code, rng
        )

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
        rerolls: List[int] = []
        for idx, die in enumerate(active_dice):
            if die.is_locked:
                continue
            face = die.current_face
            if face and (face.is_glitch or (face.money == 0 and not face.is_star and not face.is_shield and not face.has_cash_option and not face.has_shield_option)):
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
        staging = staging_cubes or {}
        stuck = stuck_cubes or {}
        blue_threat = staging.get(CubeColor.BLUE, 0) + stuck.get(CubeColor.BLUE, 0)
        declarations: Dict[int, int] = {}
        for idx, die in enumerate(dice):
            face = die.current_face
            if not face or not face.is_choice:
                continue
            if face.has_shield_option:
                declarations[idx] = 0 if blue_threat > 0 else 1
            elif face.name == "+$1 / +1 🔧":
                need_patch = (len(player_state.unpatched_dice) >= 2 or player_state.patches == 0)
                declarations[idx] = 1 if need_patch else 0
            elif face.name == "+1 🔧 / +$1":
                need_patch = (len(player_state.unpatched_dice) >= 2 or player_state.patches == 0)
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
        assignments: Dict[int, ShieldColor] = {}
        staging = staging_cubes or {}
        stuck = stuck_cubes or {}
        blue_threat = staging.get(CubeColor.BLUE, 0) + stuck.get(CubeColor.BLUE, 0)
        for idx, die in enumerate(rolled_dice):
            face = die.current_face
            if not face or face.is_glitch:
                continue
            if face.is_shield:
                if face.shield_color == ShieldColor.ANY:
                    assignments[idx] = ShieldColor.BLUE
                else:
                    assignments[idx] = face.shield_color
            elif face.has_shield_option and blue_threat > 0:
                assignments[idx] = ShieldColor.BLUE
        return assignments

    def take_phase3_actions(
        self,
        player_state: PlayerState,
        game_state: GameState,
        rng: random.Random,
    ) -> Phase3ActionPlan:
        plan = Phase3ActionPlan()
        current_money = player_state.money
        is_final_round = getattr(game_state, "is_final_round", False)
        cash_cushion = 0 if is_final_round else 2

        active_ver = game_state.active_version.version_str
        is_omnidyne = bool(
            (player_state.company and player_state.company.code == CompanyCode.OMNIDYNE)
            or (player_state.archetype and player_state.archetype.code == ArchetypeCode.PHREAKER)
        )
        if (
            is_omnidyne
            and player_state.is_ability_available(active_ver)
            and len(player_state.unpatched_dice) >= 1
        ):
            plan.use_omnidyne_override = True
            plan.use_phreaker_ability = True

        is_prometheus = bool(
            (player_state.company and player_state.company.code == CompanyCode.PROMETHEUS)
            or (player_state.archetype and player_state.archetype.code == ArchetypeCode.CIPHER)
        )
        if (
            is_prometheus
            and player_state.is_ability_available(active_ver)
        ):
            if not is_final_round and player_state.secrets > 1:
                plan.use_prometheus_override = True
                plan.use_cipher_ability = True
                plan.prometheus_mode = "DIRTY_INCOME"
            elif not is_final_round:
                candidates = []
                if getattr(player_state, "personal_purple_reserve", 0) > 0:
                    base_purple_cost = player_state.get_purple_reserve_cost()
                    disc_purple_cost = max(0, base_purple_cost - game_state.config.cipher_market_discount)
                    if current_money >= disc_purple_cost:
                        candidates.append((DieColor.PURPLE, disc_purple_cost))

                for c in [DieColor.BLUE, DieColor.RED, DieColor.GREEN, DieColor.YELLOW]:
                    if game_state.market.get(c, 0) > 0:
                        base_cost = game_state.get_market_die_cost(c)
                        cost = max(0, base_cost - game_state.config.cipher_market_discount)
                        if current_money >= cost:
                            candidates.append((c, cost))

                if candidates:
                    plan.use_prometheus_override = True
                    plan.use_cipher_ability = True
                    plan.prometheus_mode = "BUY_FREE_DIE"
                    plan.prometheus_discount_die_color = candidates[0][0]
                    current_money -= candidates[0][1]
            if not plan.use_cipher_ability:
                plan.use_prometheus_override = True
                plan.use_cipher_ability = True
                plan.prometheus_mode = "CASH"
                current_money += game_state.config.cipher_arbitrage_cash

        if (
            game_state.config.dirty_income_enabled
            and not is_final_round
            and player_state.secrets > game_state.config.dirty_income_secret_cost
            and len(player_state.ready_dice) >= 1
        ):
            plan.take_dirty_income = True
            plan.dirty_income_backlash_die_index = choose_backlash_die_index(player_state.ready_dice)
            current_money += game_state.config.dirty_income_cash

        b2_cost = game_state.config.b2_secret_cost
        b2_cap = game_state.config.b2_secret_cap
        if (
            player_state.b2_available
            and (current_money >= b2_cost if is_final_round else (current_money - b2_cost >= cash_cushion))
            and (b2_cap is None or player_state.secrets < b2_cap)
        ):
            plan.use_b2_secret = True
            current_money -= b2_cost

        if player_state.y1_available and (current_money >= 6 if is_final_round else (current_money - 6 >= cash_cushion)):
            plan.use_y1_secret = True
            current_money -= 6

        if player_state.p1_available:
            plan.p1_cube_choice = CubeColor.RED
        if (
            player_state.p3_available is not None
            and current_money - game_state.config.p3_cube_cash_cost >= cash_cushion
        ):
            plan.p3_cube_choice = CubeColor(player_state.p3_available.value)
            current_money -= game_state.config.p3_cube_cash_cost

        if not is_final_round:
            purchases = 0
            for color in [DieColor.PURPLE, DieColor.BLUE]:
                if purchases >= game_state.config.max_market_purchases_per_turn:
                    break
                if color == DieColor.PURPLE:
                    cost = player_state.get_purple_reserve_cost()
                    has_stock = getattr(player_state, "personal_purple_reserve", 0) > 0
                else:
                    cost = game_state.get_market_die_cost(color)
                    has_stock = game_state.market.get(color, 0) > 0

                if has_stock and (current_money - cost >= cash_cushion):
                    plan.market_purchases.append(color)
                    if color == DieColor.PURPLE:
                        plan.buy_purple_reserve = True
                    current_money -= cost
                    purchases += 1

        return plan


