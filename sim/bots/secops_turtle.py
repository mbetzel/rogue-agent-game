from __future__ import annotations

import random
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from sim.config import CubeColor, DieColor, ShieldColor
from sim.entities import has_company_override, has_signature_protocol, legacy_bridge_enabled
from sim.entities import ArchetypeCode, CompanyCode, WhiteHatCode
from sim.bots.market_share_policy import MarketSharePolicy
from sim.bots.base import BaseBot, Phase3ActionPlan, choose_backlash_die_index, plan_final_round_repairs, is_six_phase_state, purple_purchasable

if TYPE_CHECKING:
    from sim.engine import GameState, PlayerState
    from sim.entities import Die, Face


class SecOpsTurtleBot(BaseBot):
    """Paranoid defensive turtle: focuses on shields, heavy patching, and avoiding Dirty Income."""

    research_focus = ('DEFENSE', 'TRIAGE', 'RELEASE', 'PATENT')  # v0.35.0 research-aware policy
    market_share_policy = MarketSharePolicy(red_danger_value=3.0, danger_margin=3)  # v0.36.0

    def __init__(self, bot_id: int) -> None:
        super().__init__(bot_id, name="SecOpsTurtleBot")

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
        threat = sum(staging_cubes.get(c, 0) + stuck_cubes.get(c, 0) for c in [CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN])
        if threat >= 6 and player_state.money >= 8:
            return min(3, contractor_supply)
        elif threat >= 3 and player_state.money >= 5:
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
        if contractor_supply <= 0 or player_state.money < 2:
            return False
        threat = sum(staging_cubes.get(c, 0) + stuck_cubes.get(c, 0) for c in [CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN])
        return threat >= 4 or corruption_track >= 3

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

    def choose_aegis_override(
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

    def choose_dto_override(
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
            if face and (face.is_glitch or (not face.is_shield and not face.has_shield_option)):
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
            elif face.name == "+$1 / +1 🔬":
                declarations[idx] = 1 if player_state.patches < 3 else 0
            elif face.name == "+1 🔬 / +$1":
                declarations[idx] = 0 if player_state.patches < 3 else 1
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
            elif face.has_shield_option and blue_threat > 0:
                assignments[idx] = ShieldColor.BLUE
        return assignments

    def choose_purple_reserve_purchase(
        self,
        player_state: PlayerState,
        game_state: GameState,
        rng: random.Random,
    ) -> bool:
        """SecOpsTurtleBot places high priority on Purple reserve using dynamic operative reserve cost."""
        if not purple_purchasable(game_state) or getattr(player_state, "personal_purple_reserve", 0) <= 0:
            return False
        reserve_cost = (
            player_state.get_purple_reserve_cost()
            if hasattr(player_state, "get_purple_reserve_cost")
            else 4
        )
        if player_state.money < reserve_cost:
            return False
        return True

    def choose_spook_burn_notice(
        self,
        player_state: PlayerState,
        game_state: GameState,
        rng: random.Random,
    ) -> Optional[int]:
        """SecOpsTurtleBot never burns dice via Spook unless at 12+ Secrets."""
        if player_state.secrets < 12:
            return None
        return super().choose_spook_burn_notice(player_state, game_state, rng)

    def take_operations_actions(
        self,
        player_state: PlayerState,
        game_state: GameState,
        rng: random.Random,
    ) -> Phase3ActionPlan:
        plan = Phase3ActionPlan()
        current_money = player_state.money
        current_patches = player_state.patches
        is_final_round = getattr(game_state, "is_final_round", False)
        cash_cushion = 0 if is_final_round else 2

        patch_cash_cost = game_state.config.patch_cash_cost

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
                for c in [DieColor.BLUE, DieColor.GREEN, DieColor.RED, DieColor.YELLOW]:
                    base_cost = game_state.get_market_die_cost(c)
                    cost = max(0, base_cost - game_state.config.cipher_market_discount)
                    if game_state.market.get(c, 0) > 0 and current_money - cost >= cash_cushion:
                        plan.use_prometheus_override = True
                        plan.use_cipher_ability = True
                        plan.prometheus_mode = "BUY_FREE_DIE"
                        plan.prometheus_discount_die_color = c
                        current_money -= cost
                        break
                if not plan.use_cipher_ability and (purple_purchasable(game_state) and getattr(player_state, "personal_purple_reserve", 0) > 0):
                    base_purple_cost = player_state.get_purple_reserve_cost()
                    disc_purple_cost = max(0, base_purple_cost - game_state.config.cipher_market_discount)
                    if current_money - disc_purple_cost >= cash_cushion:
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

        # 2. Fast-Patching is handled in Part 3B via choose_fast_patches (zero cash patching)

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

        # Operative Protocol Selectors (Spook & Phreaker)
        is_spook = has_signature_protocol(player_state, WhiteHatCode.SPOOK, legacy_bridge_enabled(game_state))
        if is_spook:
            plan.spook_burn_die_id = self.choose_spook_burn_notice(player_state, game_state, rng)

        is_phreaker = has_signature_protocol(player_state, WhiteHatCode.PHREAKER, legacy_bridge_enabled(game_state))
        if is_phreaker:
            plan.phreaker_diagnostics_die_id = self.choose_phreaker_jumper_diagnostics(player_state, game_state, rng)

        if not is_final_round:
            purple_cost = player_state.get_purple_reserve_cost()
            if (
                len(plan.market_purchases) < game_state.config.max_market_purchases_per_turn
                and self.choose_purple_reserve_purchase(player_state, game_state, rng)
                and (current_money - purple_cost >= cash_cushion)
            ):
                plan.market_purchases.append(DieColor.PURPLE)
                plan.buy_purple_reserve = True
                current_money -= purple_cost

            for color in [DieColor.BLUE, DieColor.GREEN, DieColor.RED]:
                if len(plan.market_purchases) >= game_state.config.max_market_purchases_per_turn:
                    break
                cost = game_state.get_market_die_cost(color)
                if game_state.market.get(color, 0) > 0 and (current_money - cost >= cash_cushion):
                    plan.market_purchases.append(color)
                    current_money -= cost

        if (
            game_state.config.dirty_income_enabled
            and not is_final_round
            and current_money == 0
            and player_state.secrets > game_state.config.dirty_income_secret_cost
            and len(player_state.ready_dice) >= 1
        ):
            plan.take_dirty_income = True
            plan.dirty_income_backlash_die_index = choose_backlash_die_index(player_state.ready_dice)

        # Hardware Upgrades & Patents (v0.29.0)
        res_available = player_state.research_tokens
        def_cost = player_state.get_track_upgrade_cost("DEFENSE")
        if def_cost is not None and res_available >= def_cost and player_state.defense_level < 2:
            plan.track_upgrades.append("DEFENSE")
            res_available -= def_cost
        six_phase = is_six_phase_state(game_state)
        if six_phase:
            # v0.34: DEFENSE first, then RELEASE (L1-L2) before TRIAGE.
            res_available = self.plan_release_upgrade(player_state, plan, res_available, min_pressure=1)
        triage_cost = player_state.get_track_upgrade_cost("TRIAGE")
        if triage_cost is not None and res_available >= triage_cost and player_state.triage_level < 1:
            plan.track_upgrades.append("TRIAGE")
            res_available -= triage_cost
        rel_cost = player_state.get_track_upgrade_cost("RELEASE")
        if not six_phase and rel_cost is not None and res_available >= rel_cost and player_state.release_level < 1 and len(player_state.total_dice) > 5:
            plan.track_upgrades.append("RELEASE")
            res_available -= rel_cost
        patent_cost = player_state.get_patent_cost()
        if res_available >= patent_cost:
            plan.patent_filings = res_available // patent_cost

        return plan


