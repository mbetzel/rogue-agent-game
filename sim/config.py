"""Configuration, constants, and tunable parameters for Rogue Agent simulation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict


class CubeColor(str, Enum):
    RED = "red"
    BLUE = "blue"
    GREEN = "green"
    BLACK = "black"


class DieColor(str, Enum):
    GRAY = "gray"
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
    starting_money: int = 7  # [TUNE: $6–$8]
    starting_secrets: int = 6  # [TUNE: 4–10]
    starting_patches: int = 1  # [TUNE: 0–2]
    max_patch_tokens: int = 3  # [TUNE: 3]
    starting_gray_dice: int = 4
    dice_per_color_multiplier: int = 2  # 2 * num_players dice per colored die type

    # Corruption track
    corruption_spaces_per_player: int = 1
    corruption_spaces_base: int = 1  # Track length = num_players + 1

    # Operations & Economy
    dirty_income_cash: int = 3  # [TUNE: $2–$4]
    dirty_income_attack_cubes: int = 0  # Obsolete in v0.3 (no attack cubes added)
    dirty_income_black_cubes: int = 1
    patch_cash_cost: int = 2  # [TUNE: $1–$3]
    patch_token_cost: int = 1
    max_market_purchases_per_turn: int = 2  # [TUNE: 2]
    max_rounds: int = 30  # Safety cap for simulation termination

    # Cube Tower mechanics
    tower_mode: TowerMode = TowerMode.LEDGE_AVALANCHE
    tower_flat_exit_prob: float = 0.70  # [0.60–0.80]
    tower_ledge_capacity: float = 5.0
    tower_base_exit_prob: float = 0.60
    tower_avalanche_scale: float = 0.05  # Extra exit probability per cube above capacity

    # Scoring weights (Portfolio Value)
    vp_per_secret: int = 4
    vp_per_die: Dict[DieColor, int] = field(
        default_factory=lambda: {
            DieColor.GRAY: 0,
            DieColor.RED: 3,
            DieColor.BLUE: 4,
            DieColor.GREEN: 3,
            DieColor.YELLOW: 5,
            DieColor.PURPLE: 3,
        }
    )
    vp_cash_divisor: int = 2  # 1 VP per $2 remaining

    # Total Wipeout Overflow Penalties
    overflow_penalty_per_secret_debt: int = -4  # -4 VP per Secret below 0
    overflow_penalty_per_cash_debt: int = 0  # Obsolete in v0.3 (cash >= 0)
    overflow_penalty_per_unfulfilled_destroyed_die: int = -3  # -3 VP per unfulfilled die destruction

    @property
    def corruption_track_capacity(self) -> int:
        """Returns the number of spaces on the corruption track: Players + 1."""
        return self.num_players * self.corruption_spaces_per_player + self.corruption_spaces_base
