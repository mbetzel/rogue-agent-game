"""Unit tests for CubeTower compiler behavior and modes."""

import random
import unittest

from sim.config import CubeColor, GameConfig, TowerMode
from sim.tower import CubeTower


class TestCubeTower(unittest.TestCase):
    def setUp(self) -> None:
        self.config = GameConfig()
        self.tower = CubeTower(self.config)

    def test_tower_initial_empty(self) -> None:
        self.assertEqual(self.tower.total_stuck(), 0)
        for color in CubeColor:
            self.assertEqual(self.tower.stuck_cubes[color], 0)

    def test_load_and_reset_stuck(self) -> None:
        self.tower.load_stuck({CubeColor.RED: 2, CubeColor.BLACK: 1})
        self.assertEqual(self.tower.total_stuck(), 3)
        self.assertEqual(self.tower.stuck_cubes[CubeColor.RED], 2)
        self.assertEqual(self.tower.stuck_cubes[CubeColor.BLACK], 1)

        copy_dict = self.tower.get_stuck_copy()
        self.assertEqual(copy_dict[CubeColor.RED], 2)

        self.tower.reset()
        self.assertEqual(self.tower.total_stuck(), 0)

    def test_flat_binomial_probabilities(self) -> None:
        cfg = GameConfig(tower_mode=TowerMode.FLAT_BINOMIAL, tower_flat_exit_prob=1.0)
        tower = CubeTower(cfg)
        rng = random.Random(123)

        staged = {CubeColor.RED: 3, CubeColor.BLUE: 2, CubeColor.GREEN: 1, CubeColor.BLACK: 1}
        exited = tower.drop(staged, rng)

        # All cubes must exit with p=1.0
        self.assertEqual(exited[CubeColor.RED], 3)
        self.assertEqual(exited[CubeColor.BLUE], 2)
        self.assertEqual(exited[CubeColor.GREEN], 1)
        self.assertEqual(exited[CubeColor.BLACK], 1)
        self.assertEqual(tower.total_stuck(), 0)

        # With p=0.0, all cubes remain stuck
        cfg_zero = GameConfig(tower_mode=TowerMode.FLAT_BINOMIAL, tower_flat_exit_prob=0.0)
        tower_zero = CubeTower(cfg_zero)
        exited_zero = tower_zero.drop(staged, rng)
        self.assertEqual(sum(exited_zero.values()), 0)
        self.assertEqual(tower_zero.total_stuck(), 7)

    def test_ledge_avalanche_probability_scaling(self) -> None:
        cfg = GameConfig(
            tower_mode=TowerMode.LEDGE_AVALANCHE,
            tower_ledge_capacity=5.0,
            tower_base_exit_prob=0.60,
            tower_avalanche_scale=0.05,
        )
        tower = CubeTower(cfg)

        # Mass <= capacity (e.g. 4 cubes)
        self.assertAlmostEqual(tower.calculate_exit_probability(4), 0.60)
        self.assertAlmostEqual(tower.calculate_exit_probability(5), 0.60)

        # Mass > capacity (e.g. 10 cubes -> 5 over capacity -> 0.60 + 5 * 0.05 = 0.85)
        self.assertAlmostEqual(tower.calculate_exit_probability(10), 0.85)

        # Capped at 0.95 max
        self.assertAlmostEqual(tower.calculate_exit_probability(25), 0.95)

    def test_cube_conservation(self) -> None:
        """Every cube dropped into the tower must either exit or remain stuck (no cubes vanish or duplicate)."""
        rng = random.Random(999)
        staged = {CubeColor.RED: 4, CubeColor.BLUE: 3, CubeColor.GREEN: 2, CubeColor.BLACK: 2}
        initial_stuck = {CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 0, CubeColor.BLACK: 1}

        self.tower.load_stuck(initial_stuck)
        exited = self.tower.drop(staged, rng)

        for color in CubeColor:
            total_in = staged.get(color, 0) + initial_stuck.get(color, 0)
            total_out = exited.get(color, 0) + self.tower.stuck_cubes.get(color, 0)
            self.assertEqual(total_in, total_out, f"Cube count mismatch for color {color}")


if __name__ == "__main__":
    unittest.main()
