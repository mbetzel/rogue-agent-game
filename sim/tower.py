"""Cube Tower Compiler model for Rogue Agent."""

from __future__ import annotations

import random
from typing import Dict

from sim.config import CubeColor, GameConfig, TowerMode


class CubeTower:
    """Models the Rogue Agent's Cube Tower compiler with Ledge/Avalanche and Flat Binomial modes."""

    def __init__(self, config: GameConfig) -> None:
        self.config = config
        self.stuck_cubes: Dict[CubeColor, int] = {
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

    def load_stuck(self, cubes: Dict[CubeColor, int]) -> None:
        """Loads specific stuck cubes into the tower (for deterministic unit testing)."""
        for color, count in cubes.items():
            self.stuck_cubes[color] = count

    def get_stuck_copy(self) -> Dict[CubeColor, int]:
        """Returns a copy of the currently stuck cubes."""
        return dict(self.stuck_cubes)

    def calculate_exit_probability(self, total_cubes_in_drop: int) -> float:
        """Calculates the exit probability per cube based on tower mode and mass."""
        if self.config.tower_mode == TowerMode.FLAT_BINOMIAL:
            return self.config.tower_flat_exit_prob

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
        # Combine staged cubes with stuck cubes
        all_pool: Dict[CubeColor, int] = {}
        total_cubes = 0
        for color in CubeColor:
            pool_count = staged_cubes.get(color, 0) + self.stuck_cubes.get(color, 0)
            all_pool[color] = pool_count
            total_cubes += pool_count

        exit_prob = self.calculate_exit_probability(total_cubes)

        exited: Dict[CubeColor, int] = {color: 0 for color in CubeColor}
        new_stuck: Dict[CubeColor, int] = {color: 0 for color in CubeColor}

        for color, count in all_pool.items():
            for _ in range(count):
                if rng.random() < exit_prob:
                    exited[color] += 1
                else:
                    new_stuck[color] += 1

        self.stuck_cubes = new_stuck
        return exited
