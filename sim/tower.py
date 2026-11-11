"""Cube Tower Compiler model for Rogue Agent."""

from __future__ import annotations

import random
from typing import Dict, Tuple

from sim.config import CubeColor, GameConfig, TowerMode


class CubeTower:
    """Models the Rogue Agent's Cube Tower compiler with Ledge/Avalanche, Flat Binomial, and Shogun Baffle modes."""

    def __init__(self, config: GameConfig) -> None:
        self.config = config
        self.stuck_cubes: Dict[CubeColor, int] = {
            CubeColor.RED: 0,
            CubeColor.BLUE: 0,
            CubeColor.GREEN: 0,
            CubeColor.BLACK: 0,
        }
        self.last_exited_cubes: Dict[CubeColor, int] = {
            CubeColor.RED: 0,
            CubeColor.BLUE: 0,
            CubeColor.GREEN: 0,
            CubeColor.BLACK: 0,
        }

    def total_stuck(self) -> int:
        """Returns the total number of cubes currently stuck inside the tower."""
        return sum(self.stuck_cubes.values())

    def reset(self) -> None:
        """Clears all stuck cubes from inside the tower."""
        for color in self.stuck_cubes:
            self.stuck_cubes[color] = 0
        for color in self.last_exited_cubes:
            self.last_exited_cubes[color] = 0

    def load_stuck(self, cubes: Dict[CubeColor, int]) -> None:
        """Loads specific stuck cubes into the tower (for deterministic unit testing)."""
        for color, count in cubes.items():
            self.stuck_cubes[color] = count

    def get_stuck_copy(self) -> Dict[CubeColor, int]:
        """Returns a copy of the currently stuck cubes."""
        return dict(self.stuck_cubes)

    def tower_regime(self, falling_count: int, stuck_count: int) -> str:
        """Returns the Shogun baffle regime ('empty' | 'trapping' | 'avalanche') for telemetry."""
        if stuck_count <= 0:
            return "empty"
        if (
            stuck_count >= self.config.tower_avalanche_stuck_threshold
            or (falling_count + stuck_count) >= self.config.tower_avalanche_mass_threshold
        ):
            return "avalanche"
        return "trapping"

    def calculate_shogun_probabilities(self, falling_count: int, stuck_count: int) -> Tuple[float, float]:
        """Calculates independent exit probabilities for falling cubes and resting stuck cubes.

        Args:
            falling_count (int): Incoming cubes dropped into the tower (F).
            stuck_count (int): Resting cubes settled on internal baffles (S).

        Returns:
            Tuple[float, float]: (p_fall, p_dislodge)
        """
        # Invariant: Resting cubes never spontaneously exit without incoming falling cubes
        if falling_count <= 0:
            return (0.0, 0.0)

        # Empty Tower Regime (S = 0): falling cubes pass through clear baffles, no resting cubes to dislodge
        if stuck_count == 0:
            return (self.config.tower_empty_exit_prob, 0.0)

        # Avalanche Cascade Regime: shelf capacity saturated or drop mass collapses resting shelves
        if (
            stuck_count >= self.config.tower_avalanche_stuck_threshold
            or (falling_count + stuck_count) >= self.config.tower_avalanche_mass_threshold
        ):
            return (self.config.tower_avalanche_fall_prob, self.config.tower_avalanche_dislodge_prob)

        # Sub-Avalanche Baffle Trapping Regime: resting cubes obstruct paths and absorb falling kinetic energy
        p_fall = max(
            self.config.tower_min_fall_prob,
            self.config.tower_empty_exit_prob - self.config.tower_obstruction_alpha * stuck_count,
        )
        p_dislodge = self.config.tower_trapping_dislodge_prob
        return (p_fall, p_dislodge)

    def calculate_exit_probability(self, total_cubes_in_drop: int) -> float:
        """Calculates the expected per-cube exit probability.

        Under FLAT_BINOMIAL and LEDGE_AVALANCHE, returns the uniform per-cube probability.
        Under SHOGUN_BAFFLE, computes the mass-weighted aggregate expected exit probability
        based on the current stuck reservoir.
        """
        if self.config.tower_mode == TowerMode.FLAT_BINOMIAL:
            return self.config.tower_flat_exit_prob

        if self.config.tower_mode == TowerMode.SHOGUN_BAFFLE:
            falling = total_cubes_in_drop
            stuck = self.total_stuck()
            p_fall, p_dislodge = self.calculate_shogun_probabilities(falling, stuck)
            total = falling + stuck
            if total <= 0:
                return 0.0
            return (falling * p_fall + stuck * p_dislodge) / total

        # Ledge / Avalanche Mode
        mass = total_cubes_in_drop
        capacity = self.config.tower_ledge_capacity
        base_p = self.config.tower_base_exit_prob
        scale = self.config.tower_avalanche_scale

        if mass <= capacity:
            return base_p

        # Mass exceeds resting capacity; avalanche triggers higher exit chance
        extra_mass = mass - capacity
        p = base_p + extra_mass * scale
        return min(0.95, p)

    def drop(
        self,
        staged_cubes: Dict[CubeColor, int],
        rng: random.Random,
    ) -> Dict[CubeColor, int]:
        """Drops all staged cubes into the tower along with currently stuck cubes.

        Returns:
            Dict[CubeColor, int]: Exited cubes grouped by color.
        """
        if self.config.tower_mode == TowerMode.SHOGUN_BAFFLE:
            falling_count = sum(staged_cubes.get(c, 0) for c in CubeColor)
            stuck_count = self.total_stuck()
            p_fall, p_dislodge = self.calculate_shogun_probabilities(falling_count, stuck_count)
            exited: Dict[CubeColor, int] = {color: 0 for color in CubeColor}
            if falling_count <= 0:
                self.last_exited_cubes = dict(exited)
                return exited

            new_stuck: Dict[CubeColor, int] = {color: 0 for color in CubeColor}
            for color in CubeColor:
                for _ in range(staged_cubes.get(color, 0)):
                    if rng.random() < p_fall:
                        exited[color] += 1
                    else:
                        new_stuck[color] += 1
                for _ in range(self.stuck_cubes.get(color, 0)):
                    if rng.random() < p_dislodge:
                        exited[color] += 1
                    else:
                        new_stuck[color] += 1

            self.stuck_cubes = new_stuck
            self.last_exited_cubes = dict(exited)
            return exited

        # Combine staged cubes with stuck cubes
        all_pool: Dict[CubeColor, int] = {}
        total_cubes = 0
        for color in CubeColor:
            pool_count = staged_cubes.get(color, 0) + self.stuck_cubes.get(color, 0)
            all_pool[color] = pool_count
            total_cubes += pool_count

        exit_prob = self.calculate_exit_probability(total_cubes)

        exited = {color: 0 for color in CubeColor}
        new_stuck = {color: 0 for color in CubeColor}

        for color, count in all_pool.items():
            for _ in range(count):
                if rng.random() < exit_prob:
                    exited[color] += 1
                else:
                    new_stuck[color] += 1

        self.stuck_cubes = new_stuck
        self.last_exited_cubes = dict(exited)
        return exited
