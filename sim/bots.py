"""Bot archetypes and AI decision heuristics for Rogue Agent simulation."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional

from sim.config import CubeColor, DieColor, ShieldColor

if TYPE_CHECKING:
    from sim.engine import GameState, PlayerState
    from sim.entities import Die, Face


@dataclass
class Phase3ActionPlan:
    """Operations plan chosen by a bot during Phase 3."""

    take_dirty_income: bool = False
    dirty_income_cube_choice: CubeColor = CubeColor.RED
    dirty_income_backlash_die_index: int = 0  # Index in ready_dice to demote on backlash
    # Each entry in patch_actions is a dict: {"die_index": int, "use_cash": bool}
    patch_actions: List[Dict[str, int | bool]] = field(default_factory=list)
    # Market purchases: list of die colors to buy (up to 2)
    market_purchases: List[DieColor] = field(default_factory=list)
    # Special star actions
    use_b2_secret: bool = False  # Pay $2 for +1 Secret
    use_y1_secret: bool = False  # Pay $2 for +1 Secret
    p1_cube_choice: Optional[CubeColor] = None  # Add 1 Attack cube via P1
    p3_cube_choice: Optional[CubeColor] = None  # Add 1 Attack cube via P3


def choose_backlash_die_index(ready_dice: List[Die]) -> int:
    """Selects the best die to demote for Technical Debt Backlash (lowest VP, Gray preferred)."""
    if not ready_dice:
        return 0
    best_idx = 0
    best_score = (ready_dice[0].vp, 0 if ready_dice[0].color == DieColor.GRAY else 1)
    for idx, d in enumerate(ready_dice):
        score = (d.vp, 0 if d.color == DieColor.GRAY else 1)
        if score < best_score:
            best_score = score
            best_idx = idx
    return best_idx


class BaseBot:
    """Abstract base class for Rogue Agent bot archetypes."""

    def __init__(self, bot_id: int, name: str = "BaseBot") -> None:
        self.bot_id = bot_id
        self.name = name

    def choose_hotfix_rerolls(
        self,
        player_state: PlayerState,
        rolled_dice: List[Die],
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        rng: random.Random,
    ) -> List[int]:
        """Returns the indices of rolled dice to reroll using available patch tokens."""
        return []

    def commit_shields(
        self,
        player_state: PlayerState,
        rolled_dice: List[Die],
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        directive_code: str,
        rng: random.Random,
    ) -> Dict[int, ShieldColor]:
        """Maps die indices in rolled_dice to assigned ShieldColor (RED, BLUE, GREEN).

        Generic (ANY) shields MUST choose a specific color: RED, BLUE, or GREEN.
        """
        assignments: Dict[int, ShieldColor] = {}
        for idx, die in enumerate(rolled_dice):
            face = die.current_face
            if face and face.is_shield:
                if face.shield_color == ShieldColor.ANY:
                    assignments[idx] = ShieldColor.BLUE  # Prioritize Blue over Red/Green
                else:
                    assignments[idx] = face.shield_color
        return assignments

    def take_phase3_actions(
        self,
        player_state: PlayerState,
        game_state: GameState,
        rng: random.Random,
    ) -> Phase3ActionPlan:
        """Returns the actions to execute during Phase 3: Corporate Operations."""
        return Phase3ActionPlan()


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
            d.current_face.block_amount
            for d in rolled_dice
            if d.current_face and d.current_face.shield_color in (ShieldColor.BLUE, ShieldColor.ANY)
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
                and (threats[CubeColor.RED] > red_shields or threats[CubeColor.BLUE] > blue_shields)
            ):
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
        threats = self._get_threat_levels(staging_cubes, stuck_cubes)
        assignments: Dict[int, ShieldColor] = {}

        # First commit fixed colored shields
        committed_red = 0
        committed_blue = 0
        committed_green = 0

        any_shield_indices: List[int] = []

        for idx, die in enumerate(rolled_dice):
            face = die.current_face
            if not face or not face.is_shield:
                continue

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
            amt = rolled_dice[idx].current_face.block_amount if rolled_dice[idx].current_face else 1
            if best_color == ShieldColor.BLUE:
                committed_blue += amt
            elif best_color == ShieldColor.RED:
                committed_red += amt
            elif best_color == ShieldColor.GREEN:
                committed_green += amt

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
        is_final_round = getattr(game_state, "is_final_round", False)
        cash_cushion = 0 if is_final_round else 2

        threats = {
            c: game_state.staging_cup.get(c, 0) + game_state.tower.stuck_cubes.get(c, 0)
            for c in [CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN]
        }
        total_threat = sum(threats.values())

        # 1. Dirty Income: take dirty income if broke, has ready dice, secrets > 1, and threat is manageable
        if (
            current_money < 3
            and player_state.secrets > game_state.config.dirty_income_secret_cost
            and len(player_state.ready_dice) > 0
            and total_threat <= 6
        ):
            plan.take_dirty_income = True
            plan.dirty_income_backlash_die_index = choose_backlash_die_index(player_state.ready_dice)
            current_money += game_state.config.dirty_income_cash

        # 2. Patching: patch worn dice using tokens first, then cash if preserving cushion
        patch_cash_cost = (
            3
            if game_state.active_directive_code == "POLYMORPHIC_WORM"
            else game_state.config.patch_cash_cost
        )

        for idx in range(len(player_state.unpatched_dice)):
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


class SecOpsTurtleBot(BaseBot):
    """Paranoid defensive turtle: focuses on shields, heavy patching, and avoiding Dirty Income."""

    def __init__(self, bot_id: int) -> None:
        super().__init__(bot_id, name="SecOpsTurtleBot")

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
        for idx, die in enumerate(rolled_dice):
            if available_patches <= len(rerolls):
                break
            face = die.current_face
            # Reroll non-shield faces aggressively
            if face and not face.is_shield:
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
        # Protect Secrets first (BLUE), then Money (RED), then Dice (GREEN)
        for idx, die in enumerate(rolled_dice):
            face = die.current_face
            if not face or not face.is_shield:
                continue
            if face.shield_color == ShieldColor.ANY:
                # Default ANY shields to Blue to safeguard Secrets
                assignments[idx] = ShieldColor.BLUE
            else:
                assignments[idx] = face.shield_color
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
        is_final_round = getattr(game_state, "is_final_round", False)
        cash_cushion = 0 if is_final_round else 2

        patch_cash_cost = (
            3
            if game_state.active_directive_code == "POLYMORPHIC_WORM"
            else game_state.config.patch_cash_cost
        )

        # Turtle aggressively patches all dice (preserving cushion for cash)
        for idx in range(len(player_state.unpatched_dice)):
            if current_patches > 0:
                plan.patch_actions.append({"die_index": idx, "use_cash": False})
                current_patches -= 1
            elif current_money - patch_cash_cost >= cash_cushion:
                plan.patch_actions.append({"die_index": idx, "use_cash": True})
                current_money -= patch_cash_cost

        # Buy Blue > Green > Red dice (respecting cushion)
        for color in [DieColor.BLUE, DieColor.GREEN, DieColor.RED]:
            if len(plan.market_purchases) >= game_state.config.max_market_purchases_per_turn:
                break
            cost = 4 if color in (DieColor.RED, DieColor.GREEN) else 5
            if game_state.market.get(color, 0) > 0 and (current_money - cost >= cash_cushion):
                plan.market_purchases.append(color)
                current_money -= cost

        # In Final Round: spend out remaining cash on any available dice
        if is_final_round and len(plan.market_purchases) < game_state.config.max_market_purchases_per_turn:
            for color in [DieColor.BLUE, DieColor.GREEN, DieColor.RED, DieColor.YELLOW, DieColor.PURPLE]:
                if len(plan.market_purchases) >= game_state.config.max_market_purchases_per_turn:
                    break
                cost = 4 if color in (DieColor.RED, DieColor.GREEN, DieColor.PURPLE) else 5
                if game_state.market.get(color, 0) > 0 and current_money >= cost:
                    plan.market_purchases.append(color)
                    current_money -= cost

        # Never take Dirty Income unless literally $0, secrets > 1, and has ready dice
        if (
            current_money == 0
            and player_state.secrets > game_state.config.dirty_income_secret_cost
            and len(player_state.ready_dice) > 0
        ):
            plan.take_dirty_income = True
            plan.dirty_income_backlash_die_index = choose_backlash_die_index(player_state.ready_dice)

        return plan


class VentureGreedBot(BaseBot):
    """Greedy capitalist: maximizes Yellow dice, buys secrets, and minimizes shielding."""

    def __init__(self, bot_id: int) -> None:
        super().__init__(bot_id, name="VentureGreedBot")

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
        # Reroll shield faces into money/secrets if we aren't in lethal danger
        if player_state.secrets > 2 and player_state.money > 2:
            for idx, die in enumerate(rolled_dice):
                if available_patches <= len(rerolls):
                    break
                face = die.current_face
                if face and (face.is_shield or face.name == "Idle (0)"):
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
        for idx, die in enumerate(rolled_dice):
            face = die.current_face
            if face and face.is_shield:
                if face.shield_color == ShieldColor.ANY:
                    assignments[idx] = ShieldColor.BLUE  # Prioritize Blue over Red/Green
                else:
                    assignments[idx] = face.shield_color
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

        # Greed bot takes Dirty Income aggressively to fund purchases (requires ready dice and >1 secret)
        if (
            current_money < 5
            and player_state.secrets > game_state.config.dirty_income_secret_cost
            and len(player_state.ready_dice) > 0
        ):
            plan.take_dirty_income = True
            plan.dirty_income_backlash_die_index = choose_backlash_die_index(player_state.ready_dice)
            current_money += game_state.config.dirty_income_cash

        # Buy Secrets only if special abilities are eligible and affordable (preserving cushion)
        if player_state.b2_available and (current_money - 2 >= cash_cushion) and player_state.secrets < 10:
            plan.use_b2_secret = True
            current_money -= 2

        if player_state.y1_available and (current_money - 6 >= cash_cushion) and player_state.secrets < 10:
            plan.use_y1_secret = True
            current_money -= 6

        # Greed bot buys Yellow dice first, then Blue (respecting cushion)
        purchases = 0
        for _ in range(game_state.config.max_market_purchases_per_turn):
            if game_state.market.get(DieColor.YELLOW, 0) > 0 and (current_money - 5 >= cash_cushion):
                plan.market_purchases.append(DieColor.YELLOW)
                current_money -= 5
                purchases += 1
            elif game_state.market.get(DieColor.BLUE, 0) > 0 and (current_money - 5 >= cash_cushion):
                plan.market_purchases.append(DieColor.BLUE)
                current_money -= 5
                purchases += 1

        # In Final Round: spend out remaining cash on any available dice
        if is_final_round and purchases < game_state.config.max_market_purchases_per_turn:
            for color in [DieColor.YELLOW, DieColor.BLUE, DieColor.RED, DieColor.GREEN, DieColor.PURPLE]:
                if purchases >= game_state.config.max_market_purchases_per_turn:
                    break
                cost = 4 if color in (DieColor.RED, DieColor.GREEN, DieColor.PURPLE) else 5
                if game_state.market.get(color, 0) > 0 and current_money >= cost:
                    plan.market_purchases.append(color)
                    current_money -= cost
                    purchases += 1

        # Only patch if ready dice is critically low (<= 2)
        if len(player_state.ready_dice) <= 2:
            patch_cash_cost = (
                3
                if game_state.active_directive_code == "POLYMORPHIC_WORM"
                else game_state.config.patch_cash_cost
            )
            current_patches = player_state.patches
            for idx in range(len(player_state.unpatched_dice)):
                if current_patches > 0:
                    plan.patch_actions.append({"die_index": idx, "use_cash": False})
                    current_patches -= 1
                elif current_money - patch_cash_cost >= cash_cushion:
                    plan.patch_actions.append({"die_index": idx, "use_cash": True})
                    current_money -= patch_cash_cost

        return plan


class AccelerationistBot(BaseBot):
    """Rushes corruption and Singularity by weaponizing the Cube Tower and taking Dirty Income."""

    def __init__(self, bot_id: int) -> None:
        super().__init__(bot_id, name="AccelerationistBot")

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
        for idx, die in enumerate(rolled_dice):
            face = die.current_face
            if face and face.is_shield:
                if face.shield_color == ShieldColor.ANY:
                    assignments[idx] = ShieldColor.BLUE
                else:
                    assignments[idx] = face.shield_color
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

        # Always take Dirty Income if ready dice available and secrets > 1 to accelerate corruption track
        if (
            player_state.secrets > game_state.config.dirty_income_secret_cost
            and len(player_state.ready_dice) > 0
        ):
            plan.take_dirty_income = True
            plan.dirty_income_backlash_die_index = choose_backlash_die_index(player_state.ready_dice)
            current_money += game_state.config.dirty_income_cash

        # Use P1 / P3 attack cube additions only if eligible
        if player_state.p1_available:
            plan.p1_cube_choice = CubeColor.RED
        if player_state.p3_available is not None:
            plan.p3_cube_choice = CubeColor(player_state.p3_available.value)

        # Buy Purple (Black-Hat) or Blue dice (respecting cushion)
        purchases = 0
        for color in [DieColor.PURPLE, DieColor.BLUE]:
            if purchases >= game_state.config.max_market_purchases_per_turn:
                break
            cost = 4 if color == DieColor.PURPLE else 5
            if game_state.market.get(color, 0) > 0 and (current_money - cost >= cash_cushion):
                plan.market_purchases.append(color)
                current_money -= cost
                purchases += 1

        # In Final Round: spend remaining cash on any available dice
        if is_final_round and purchases < game_state.config.max_market_purchases_per_turn:
            for color in [DieColor.PURPLE, DieColor.BLUE, DieColor.RED, DieColor.GREEN, DieColor.YELLOW]:
                if purchases >= game_state.config.max_market_purchases_per_turn:
                    break
                cost = 4 if color in (DieColor.PURPLE, DieColor.RED, DieColor.GREEN) else 5
                if game_state.market.get(color, 0) > 0 and current_money >= cost:
                    plan.market_purchases.append(color)
                    current_money -= cost
                    purchases += 1

        # Patch using tokens
        current_patches = player_state.patches
        for idx in range(len(player_state.unpatched_dice)):
            if current_patches > 0:
                plan.patch_actions.append({"die_index": idx, "use_cash": False})
                current_patches -= 1

        return plan


class RecklessSaboteurBot(BaseBot):
    """Chaos bot: forces extreme threat escalations and pushes for simultaneous total wipeout."""

    def __init__(self, bot_id: int) -> None:
        super().__init__(bot_id, name="RecklessSaboteurBot")

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
        for idx, die in enumerate(rolled_dice):
            face = die.current_face
            if face and face.is_shield:
                if face.shield_color == ShieldColor.ANY:
                    assignments[idx] = ShieldColor.BLUE  # Prioritize Blue over Red/Green
                else:
                    assignments[idx] = face.shield_color
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

        # Always take Dirty Income if ready dice available and secrets > 1
        if (
            player_state.secrets > game_state.config.dirty_income_secret_cost
            and len(player_state.ready_dice) > 0
        ):
            plan.take_dirty_income = True
            plan.dirty_income_backlash_die_index = choose_backlash_die_index(player_state.ready_dice)
            current_money += game_state.config.dirty_income_cash

        # Buy Purple or Red (respecting cushion)
        purchases = 0
        for color in [DieColor.PURPLE, DieColor.RED]:
            if purchases >= game_state.config.max_market_purchases_per_turn:
                break
            cost = 4
            if game_state.market.get(color, 0) > 0 and (current_money - cost >= cash_cushion):
                plan.market_purchases.append(color)
                current_money -= cost
                purchases += 1

        # In Final Round: spend out on any available dice
        if is_final_round and purchases < game_state.config.max_market_purchases_per_turn:
            for color in [DieColor.PURPLE, DieColor.RED, DieColor.GREEN, DieColor.BLUE, DieColor.YELLOW]:
                if purchases >= game_state.config.max_market_purchases_per_turn:
                    break
                cost = 4 if color in (DieColor.PURPLE, DieColor.RED, DieColor.GREEN) else 5
                if game_state.market.get(color, 0) > 0 and current_money >= cost:
                    plan.market_purchases.append(color)
                    current_money -= cost
                    purchases += 1

        # Never patch unless completely depleted (0 ready dice), preserving cash cushion
        patch_cash_cost = (
            3
            if game_state.active_directive_code == "POLYMORPHIC_WORM"
            else game_state.config.patch_cash_cost
        )
        if len(player_state.ready_dice) == 0 and len(player_state.unpatched_dice) > 0:
            if player_state.patches > 0:
                plan.patch_actions.append({"die_index": 0, "use_cash": False})
            elif current_money - patch_cash_cost >= cash_cushion:
                plan.patch_actions.append({"die_index": 0, "use_cash": True})

        return plan
