from __future__ import annotations

import random
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from sim.config import CubeColor, DieColor, ShieldColor
from sim.entities import ArchetypeCode, CompanyCode, WhiteHatCode
from sim.bots.base import BaseBot, Phase3ActionPlan, choose_backlash_die_index, plan_final_round_repairs

if TYPE_CHECKING:
    from sim.engine import GameState, PlayerState
    from sim.entities import Die, Face


class RecklessSaboteurBot(BaseBot):
    """Chaos bot: forces extreme threat escalations and pushes for simultaneous total wipeout."""

    def __init__(self, bot_id: int) -> None:
        super().__init__(bot_id, name="RecklessSaboteurBot")

    def choose_contractor_hires(
        self,
        player_state: PlayerState,
        contractor_supply: int,
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        rng: random.Random,
    ) -> int:
        if contractor_supply <= 0 or player_state.money < 3:
            return 0
        if player_state.money >= 8:
            return min(3, contractor_supply)
        elif player_state.money >= 5:
            return min(2, contractor_supply)
        elif player_state.money >= 3:
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
        return min(player_state.money, secrets_at_risk)

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
            if face and (face.is_glitch or (face.money < 1 and not face.has_cash_option and not face.is_shield and not face.has_shield_option)):
                rerolls.append(idx)
        return rerolls

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
                for c in [DieColor.PURPLE, DieColor.BLUE, DieColor.RED, DieColor.GREEN, DieColor.YELLOW]:
                    cost = (4 if c in (DieColor.RED, DieColor.GREEN, DieColor.PURPLE) else 5) - game_state.config.cipher_market_discount
                    if game_state.market.get(c, 0) > 0 and current_money >= cost:
                        plan.use_prometheus_override = True
                        plan.use_cipher_ability = True
                        plan.prometheus_mode = "BUY_FREE_DIE"
                        plan.prometheus_discount_die_color = c
                        current_money -= cost
                        break
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

        patch_cash_cost = game_state.config.patch_cash_cost
        current_patches = player_state.patches

        if is_final_round:
            current_money, current_patches = plan_final_round_repairs(
                player_state, game_state, current_money, current_patches, patch_cash_cost, plan
            )

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

        if not is_final_round:
            purchases = 0
            for color in [DieColor.PURPLE, DieColor.RED]:
                if purchases >= game_state.config.max_market_purchases_per_turn:
                    break
                cost = 4
                if game_state.market.get(color, 0) > 0 and (current_money - cost >= cash_cushion):
                    plan.market_purchases.append(color)
                    current_money -= cost
                    purchases += 1

        return plan
