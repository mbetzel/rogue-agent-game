"""Configuration, constants, and tunable parameters for Rogue Agent simulation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Tuple


class CubeColor(str, Enum):
    RED = "red"
    BLUE = "blue"
    GREEN = "green"
    BLACK = "black"


class DieColor(str, Enum):
    GRAY = "gray"
    WHITE = "white"
    RED = "red"
    BLUE = "blue"
    GREEN = "green"
    YELLOW = "yellow"
    PURPLE = "purple"


class ShieldColor(str, Enum):
    RED = "red"
    BLUE = "blue"
    GREEN = "green"
    ANY = "any"


class TowerMode(str, Enum):
    LEDGE_AVALANCHE = "ledge_avalanche"
    FLAT_BINOMIAL = "flat_binomial"


class EndGameReason(str, Enum):
    NONE = "none"
    SINGULARITY = "singularity"
    PATIENT_ZERO = "patient_zero"
    TOTAL_WIPEOUT = "total_wipeout"
    ROUND_LIMIT = "round_limit"


@dataclass
class GameConfig:
    """Tunable game parameters with baselines from RULES.md."""

    # Player count & setup
    num_players: int = 4
    starting_money: int = 6  # [v0.30.0 Baseline: Calibrated from $4 to $6 (INV-START-CASH-01)]
    starting_secrets_by_player_count: Dict[int, int] = field(
        default_factory=lambda: {2: 8, 3: 8, 4: 12}
    )
    starting_patches_by_player_count: Dict[int, int] = field(
        default_factory=lambda: {2: 0, 3: 0, 4: 0}  # [v0.30.0 Baseline: Calibrated from 2 to 0 (INV-START-RES-01)]
    )
    starting_secrets: Optional[int] = None  # Optional scalar override for backwards compatibility
    starting_patches: Optional[int] = None  # Optional scalar override for backwards compatibility
    max_patch_tokens: int = 3  # [TUNE: 3] Maximum unspent patch tokens retained across rounds during End-of-Round Cleanup (Model C)
    starting_gray_dice: int = 3   # [v0.30.0 Baseline: Calibrated from 4 to 3 (INV-START-POOL-01)]
    starting_purple_dice: int = 1 # [v0.30.0 Baseline: 1 starter Purple die (INV-START-POOL-01)]
    starting_purple_reserve: int = 1 # [v0.30.0 Baseline: Option A 1 die in reserve (INV-PURPLE-RES-01)]
    dice_per_color_multiplier: int = 2  # 2 * num_players dice per colored die type

    # Corruption track (v0.15.0 Per-Version Escalating Tracks)
    corruption_track_profile: str = "STANDARD"  # "STANDARD" (Profile 1) or "AGGRESSIVE" (Profile 2)
    corruption_cubes_resolve_immediately: bool = False  # Mode A (False): Staging Cup; Mode B (True): immediate tray attack for R/B/G
    corruption_track_lengths: Dict[str, int] = field(
        default_factory=lambda: {"v1.0": 4, "v2.0": 5, "v3.0": 6}
    )
    corruption_track_capacity_by_player_count: Dict[int, int] = field(
        default_factory=lambda: {2: 4, 3: 5, 4: 6}
    )
    corruption_track_flat_capacity: Optional[int] = None  # Scalar override for backwards compatibility / tests
    corruption_spaces_per_player: int = 1  # Deprecated in v0.4
    corruption_spaces_base: int = 1  # Deprecated in v0.4

    # Autonomous AI Pulse by Version (v0.21.0 Baseline: 1 Black cube/round across all versions)
    autonomous_pulse_by_version: Dict[str, int] = field(
        default_factory=lambda: {"v1.0": 1, "v2.0": 1, "v3.0": 1}
    )

    # Operations & Economy
    cipher_arbitrage_cash: int = 2  # [TUNE: v0.16.0] Cipher Phase 3 alternate cash arbitrage payout
    patch_ransom_absorption: bool = False  # Deprecated in v0.21.0 (Emergency patch absorption eliminated; Red ransom is strictly cash-only)
    dirty_income_enabled: bool = False  # Deprecated in v0.16.0 (Dirty income eliminated)
    dirty_income_cash: int = 3  # Deprecated
    dirty_income_secret_cost: int = 1  # Deprecated
    dirty_income_attack_cubes: int = 0  # Deprecated
    dirty_income_black_cubes: int = 1  # Deprecated
    patch_cash_cost: int = 2  # [TUNE: $1–$3]
    patch_token_cost: int = 1
    max_market_purchases_per_turn: int = 2  # [TUNE: 2]
    max_rounds: int = 30  # Safety cap for simulation termination

    # Temp Staffing & Yahtzee Rerolls (v0.6 / v0.7)
    contractor_hire_cost: int = 1
    contractor_cost_progression: Tuple[int, ...] = (1, 2, 3)
    contractor_max_hire: int = 3
    contractor_supply_total: int = 12
    default_free_rerolls: int = 2
    throttled_free_rerolls: int = 1

    # Corporate Asymmetry & Hardware Tracks (v0.28.0)
    enable_corporate_asymmetry: bool = False  # When True, applies Company-specific hardware and starting resource modifiers

    # Variant & Boss Tunables (Phase 10)
    y2_base_payout: int = 2
    y2_max_payout: int = 5
    b2_secret_cost: int = 4
    b2_secret_cap: Optional[int] = None
    p3_cube_cash_cost: int = 1
    corrupted_kernel_black_threshold: int = 2
    corrupted_kernel_strength_bonus: int = 2
    cipher_market_discount: int = 2  # [TUNE: v0.9.1] $2 discount on 1 colored die purchase

    # Cube Tower mechanics
    tower_mode: TowerMode = TowerMode.LEDGE_AVALANCHE
    tower_flat_exit_prob: float = 0.70  # [0.60–0.80]
    tower_ledge_capacity: float = 5.0
    tower_base_exit_prob: float = 0.60
    tower_avalanche_scale: float = 0.05  # Extra exit probability per cube above capacity

    # Compiler Priming & Buffer Overflow (v0.9.1 Baseline)
    enable_compiler_priming: bool = True
    compiler_priming_cubes: Dict[CubeColor, int] = field(
        default_factory=lambda: {
            CubeColor.RED: 1,
            CubeColor.BLUE: 1,
            CubeColor.GREEN: 1,
            CubeColor.BLACK: 1,
        }
    )
    enable_buffer_overflow: bool = True
    buffer_overflow_cubes: Dict[CubeColor, int] = field(
        default_factory=lambda: {
            CubeColor.RED: 1,
            CubeColor.BLUE: 1,
            CubeColor.GREEN: 1,
        }
    )

    # Scoring weights (Portfolio Value - v0.19.0 Pure Corporate Secrets Victory Scoring)
    vp_per_secret: int = 1
    vp_per_die: Dict[DieColor, int] = field(
        default_factory=lambda: {
            DieColor.GRAY: 0,
            DieColor.WHITE: 0,
            DieColor.RED: 0,
            DieColor.BLUE: 0,
            DieColor.GREEN: 0,
            DieColor.YELLOW: 0,
            DieColor.PURPLE: 0,
        }
    )
    vp_cash_divisor: int = 0  # Deprecated in v0.19.0 (Cash is Tiebreaker #1, not direct VP)

    # Total Wipeout Overflow Penalties (v0.19.0: Elimination of Fictitious Wipeout Bonuses)
    overflow_penalty_per_secret_debt: int = -1  # -1 VP per Secret breach depth below 0
    overflow_penalty_per_cash_debt: int = 0  # Obsolete in v0.3 (cash >= 0)
    overflow_penalty_per_unfulfilled_destroyed_die: int = -1  # -1 VP per unfulfilled die destruction

    @property
    def corruption_track_capacity(self) -> int:
        """Returns corruption track capacity from player-count mapping or flat capacity override."""
        if self.corruption_track_flat_capacity is not None:
            return self.corruption_track_flat_capacity
        return self.corruption_track_capacity_by_player_count.get(self.num_players, 4)

    @property
    def corruption_cube_resolve_immediate(self) -> bool:
        return self.corruption_cubes_resolve_immediately

    @corruption_cube_resolve_immediate.setter
    def corruption_cube_resolve_immediate(self, val: bool) -> None:
        self.corruption_cubes_resolve_immediately = val

    def get_starting_secrets(self, num_players: Optional[int] = None) -> int:
        """Returns starting secrets for the specified player count (or self.num_players).

        Scalar override starting_secrets takes precedence if provided.
        """
        if self.starting_secrets is not None:
            return self.starting_secrets
        n = num_players if num_players is not None else self.num_players
        fallback = self.starting_secrets_by_player_count.get(4, 8)
        return self.starting_secrets_by_player_count.get(n, fallback)

    def get_starting_patches(self, num_players: Optional[int] = None) -> int:
        """Returns starting patch tokens for the specified player count (or self.num_players).

        Scalar override starting_patches takes precedence if provided.
        """
        if self.starting_patches is not None:
            return self.starting_patches
        n = num_players if num_players is not None else self.num_players
        fallback = self.starting_patches_by_player_count.get(4, 0)
        return self.starting_patches_by_player_count.get(n, fallback)

    def get_contractor_cost_for_hire(self, count: int, already_hired: int = 0) -> int:
        """Returns the total cost to hire `count` additional contractors given `already_hired` in the current round."""
        if count <= 0:
            return 0
        total_cost = 0
        for i in range(already_hired, already_hired + count):
            if i < len(self.contractor_cost_progression):
                total_cost += self.contractor_cost_progression[i]
            else:
                total_cost += self.contractor_cost_progression[-1]
        return total_cost

    def get_max_affordable_contractors(
        self, money: int, already_hired: int = 0, supply: Optional[int] = None
    ) -> int:
        """Calculates the maximum number of contractors that can be afforded given money, already_hired, and supply."""
        max_possible = self.contractor_max_hire - already_hired
        if supply is not None:
            max_possible = min(max_possible, supply)
        if max_possible <= 0 or money <= 0:
            return 0

        affordable = 0
        for c in range(1, max_possible + 1):
            if self.get_contractor_cost_for_hire(c, already_hired) <= money:
                affordable = c
            else:
                break
        return affordable
