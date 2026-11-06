from __future__ import annotations

import random
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from sim.config import CubeColor, DieColor, ShieldColor
from sim.entities import has_company_override, has_signature_protocol, legacy_bridge_enabled
from sim.entities import ArchetypeCode, CompanyCode, WhiteHatCode
from sim.bots.base import BaseBot, Phase3ActionPlan, choose_backlash_die_index, plan_final_round_repairs, is_six_phase_state

if TYPE_CHECKING:
    from sim.engine import GameState, PlayerState
    from sim.entities import Die, Face


class VentureGreedBot(BaseBot):
    """Greedy capitalist: maximizes Yellow dice, buys secrets, and minimizes shielding."""

    def __init__(self, bot_id: int) -> None:
        super().__init__(bot_id, name="VentureGreedBot")

    def choose_contractor_hires(
        self,
        player_state: PlayerState,
        contractor_supply: int,
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        rng: random.Random,
    ) -> int:
        if contractor_supply <= 0 or player_state.money < 6:
            return 0
        if player_state.money >= 11:
            return min(3, contractor_supply)
        elif player_state.money >= 8:
            return min(2, contractor_supply)
        return min(1, contractor_supply)

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
        threat = sum(staging_cubes.get(c, 0) + stuck_cubes.get(c, 0) for c in [CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN])
        return threat >= 4 or corruption_track >= 3

    def choose_operator_buy_third_die(
        self,
        player_state: PlayerState,
        contractor_supply: int,
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        rng: random.Random,
        corruption_track: int = 0,
    ) -> bool:
        return False

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
            if not face:
                continue
            if face.is_glitch or (face.money == 0 and not face.is_star and not face.has_cash_option):
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
        if player_state.secrets > 2 and player_state.money > 2:
            for idx, die in enumerate(rolled_dice):
                if available_patches <= len(rerolls):
                    break
                face = die.current_face
                if face and (face.is_shield or face.name == "Idle (0)"):
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
                declarations[idx] = 0 if (blue_threat > 0 and player_state.secrets <= 2) else 1
            elif face.name == "+$1 / +1 🔧":
                need_patch = (player_state.patches == 0 and len(player_state.unpatched_dice) > 0)
                declarations[idx] = 1 if need_patch else 0
            elif face.name == "+1 🔧 / +$1":
                need_patch = (player_state.patches == 0 and len(player_state.unpatched_dice) > 0)
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
                    assignments[idx] = ShieldColor.ANY
                else:
                    assignments[idx] = face.shield_color
            elif face.has_shield_option and blue_threat > 0 and player_state.secrets <= 2:
                assignments[idx] = ShieldColor.BLUE
        return assignments

    def take_operations_actions(
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
        is_omnidyne = has_company_override(player_state, CompanyCode.OMNIDYNE, legacy_bridge_enabled(game_state))
        if (
            is_omnidyne
            and player_state.is_ability_available(active_ver)
            and len(player_state.unpatched_dice) >= 1
        ):
            plan.use_omnidyne_override = True
            plan.use_phreaker_ability = True

        is_prometheus = has_company_override(player_state, CompanyCode.PROMETHEUS, legacy_bridge_enabled(game_state))
        if (
            is_prometheus
            and player_state.is_ability_available(active_ver)
        ):
            if not is_final_round:
                for c in [DieColor.YELLOW, DieColor.BLUE, DieColor.RED, DieColor.GREEN]:
                    base_cost = game_state.get_market_die_cost(c)
                    cost = max(0, base_cost - game_state.config.cipher_market_discount)
                    if game_state.market.get(c, 0) > 0 and current_money >= cost:
                        plan.use_prometheus_override = True
                        plan.use_cipher_ability = True
                        plan.prometheus_mode = "BUY_FREE_DIE"
                        plan.prometheus_discount_die_color = c
                        current_money -= cost
                        break
                if not plan.use_cipher_ability and getattr(player_state, "personal_purple_reserve", 0) > 0:
                    base_purple_cost = player_state.get_purple_reserve_cost()
                    disc_purple_cost = max(0, base_purple_cost - game_state.config.cipher_market_discount)
                    if current_money >= disc_purple_cost:
                        plan.use_prometheus_override = True
                        plan.use_cipher_ability = True
                        plan.prometheus_mode = "BUY_FREE_DIE"
                        plan.prometheus_discount_die_color = DieColor.PURPLE
                        current_money -= disc_purple_cost
            if not plan.use_cipher_ability:
                plan.use_prometheus_override = True
                plan.use_cipher_ability = True
                plan.prometheus_mode = "CASH"
                current_money += game_state.config.cipher_arbitrage_cash

        if (
            game_state.config.dirty_income_enabled
            and not is_final_round
            and current_money < 5
            and player_state.secrets > game_state.config.dirty_income_secret_cost
            and len(player_state.ready_dice) >= 1
        ):
            plan.take_dirty_income = True
            plan.dirty_income_backlash_die_index = choose_backlash_die_index(player_state.ready_dice)
            current_money += game_state.config.dirty_income_cash

        b2_cost = game_state.config.b2_secret_cost
        b2_cap = game_state.config.b2_secret_cap
        if player_state.b2_available and (current_money >= b2_cost if is_final_round else (current_money - b2_cost >= cash_cushion)) and (b2_cap is None or player_state.secrets < b2_cap):
            plan.use_b2_secret = True
            current_money -= b2_cost

        if player_state.y1_available and (current_money >= 6 if is_final_round else (current_money - 6 >= cash_cushion)):
            plan.use_y1_secret = True
            current_money -= 6

        # Operative Protocol Selectors (Spook & Phreaker)
        is_spook = has_signature_protocol(player_state, WhiteHatCode.SPOOK, legacy_bridge_enabled(game_state))
        if is_spook:
            plan.spook_burn_die_id = self.choose_spook_burn_notice(player_state, game_state, rng)

        is_phreaker = has_signature_protocol(player_state, WhiteHatCode.PHREAKER, legacy_bridge_enabled(game_state))
        if is_phreaker:
            plan.phreaker_diagnostics_die_id = self.choose_phreaker_jumper_diagnostics(player_state, game_state, rng)

        if not is_final_round:
            purchases = 0
            yellow_cost = game_state.get_market_die_cost(DieColor.YELLOW)
            blue_cost = game_state.get_market_die_cost(DieColor.BLUE)
            for _ in range(game_state.config.max_market_purchases_per_turn):
                if game_state.market.get(DieColor.YELLOW, 0) > 0 and (current_money - yellow_cost >= cash_cushion):
                    plan.market_purchases.append(DieColor.YELLOW)
                    current_money -= yellow_cost
                    purchases += 1
                elif game_state.market.get(DieColor.BLUE, 0) > 0 and (current_money - blue_cost >= cash_cushion):
                    plan.market_purchases.append(DieColor.BLUE)
                    current_money -= blue_cost
                    purchases += 1

        # Hardware Upgrades & Patents (v0.28.0)
        res_available = player_state.research_tokens
        if is_six_phase_state(game_state):
            # v0.34: value RELEASE (L1-L2) before Patent Filings when owned dice exceed Release Bandwidth.
            res_available = self.plan_release_upgrade(player_state, plan, res_available, min_pressure=1)
        pat_cost = player_state.get_track_upgrade_cost("PATENT")
        if pat_cost is not None and res_available >= pat_cost and player_state.patent_level < 1:
            plan.track_upgrades.append("PATENT")
            res_available -= pat_cost
        patent_cost = player_state.get_patent_cost()
        if res_available >= patent_cost:
            plan.patent_filings = res_available // patent_cost

        return plan


