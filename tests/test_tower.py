"""Unit tests for CubeTower compiler behavior and modes."""

import random
import unittest
from unittest.mock import MagicMock

from sim.config import CubeColor, GameConfig, TowerMode
from sim.tower import CubeTower


class TestCubeTower(unittest.TestCase):
    def setUp(self) -> None:
        self.config = GameConfig.legacy_v035()
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
        cfg = GameConfig.legacy_v035(tower_mode=TowerMode.FLAT_BINOMIAL, tower_flat_exit_prob=1.0)
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
        cfg_zero = GameConfig.legacy_v035(tower_mode=TowerMode.FLAT_BINOMIAL, tower_flat_exit_prob=0.0)
        tower_zero = CubeTower(cfg_zero)
        exited_zero = tower_zero.drop(staged, rng)
        self.assertEqual(sum(exited_zero.values()), 0)
        self.assertEqual(tower_zero.total_stuck(), 7)

    def test_ledge_avalanche_probability_scaling(self) -> None:
        cfg = GameConfig.legacy_v035(
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

    def test_shogun_probabilities_regimes(self) -> None:
        cfg = GameConfig.v038c(tower_mode=TowerMode.SHOGUN_BAFFLE)
        tower = CubeTower(cfg)

        # F=0, S=4 -> (0.0, 0.0)
        p_fall, p_dis = tower.calculate_shogun_probabilities(0, 4)
        self.assertAlmostEqual(p_fall, 0.0)
        self.assertAlmostEqual(p_dis, 0.0)

        # F=4, S=0 -> (0.70, 0.0)
        p_fall, p_dis = tower.calculate_shogun_probabilities(4, 0)
        self.assertAlmostEqual(p_fall, 0.70)
        self.assertAlmostEqual(p_dis, 0.0)
        self.assertEqual(tower.tower_regime(4, 0), "empty")
        self.assertAlmostEqual(tower.calculate_exit_probability(4), 0.70)

        # F=4, S=1 -> (0.55, 0.21)
        p_fall, p_dis = tower.calculate_shogun_probabilities(4, 1)
        self.assertAlmostEqual(p_fall, 0.55)
        self.assertAlmostEqual(p_dis, 0.21)
        self.assertEqual(tower.tower_regime(4, 1), "trapping")
        tower.load_stuck({CubeColor.RED: 1, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0})
        self.assertAlmostEqual(tower.calculate_exit_probability(4), (4 * 0.55 + 1 * 0.21) / 5.0)

        # F=4, S=2 -> (0.40, 0.21)
        p_fall, p_dis = tower.calculate_shogun_probabilities(4, 2)
        self.assertAlmostEqual(p_fall, 0.40)
        self.assertAlmostEqual(p_dis, 0.21)
        self.assertEqual(tower.tower_regime(4, 2), "trapping")

        # F=4, S=3 -> (0.60, 0.70) (S >= 3 triggers avalanche)
        p_fall, p_dis = tower.calculate_shogun_probabilities(4, 3)
        self.assertAlmostEqual(p_fall, 0.60)
        self.assertAlmostEqual(p_dis, 0.70)
        self.assertEqual(tower.tower_regime(4, 3), "avalanche")

        # F=6, S=1 -> (0.60, 0.70) (F+S = 7 >= 7 triggers mass avalanche)
        p_fall, p_dis = tower.calculate_shogun_probabilities(6, 1)
        self.assertAlmostEqual(p_fall, 0.60)
        self.assertAlmostEqual(p_dis, 0.70)
        self.assertEqual(tower.tower_regime(6, 1), "avalanche")

        # F=2, S=3 -> (0.60, 0.70) (S >= 3 triggers avalanche)
        p_fall, p_dis = tower.calculate_shogun_probabilities(2, 3)
        self.assertAlmostEqual(p_fall, 0.60)
        self.assertAlmostEqual(p_dis, 0.70)
        self.assertEqual(tower.tower_regime(2, 3), "avalanche")

    def test_shogun_zero_falling_cubes(self) -> None:
        cfg = GameConfig.v038c(tower_mode=TowerMode.SHOGUN_BAFFLE)
        tower = CubeTower(cfg)
        tower.load_stuck({CubeColor.RED: 2, CubeColor.BLACK: 1})
        stuck_before = tower.get_stuck_copy()

        rng = MagicMock(spec=random.Random)
        exited = tower.drop({}, rng)

        self.assertEqual(exited, {c: 0 for c in CubeColor})
        self.assertEqual(tower.stuck_cubes, stuck_before)
        rng.random.assert_not_called()

    def test_shogun_cube_conservation(self) -> None:
        cfg = GameConfig.v038c(tower_mode=TowerMode.SHOGUN_BAFFLE)
        tower = CubeTower(cfg)
        staged = {CubeColor.RED: 3, CubeColor.BLUE: 2, CubeColor.GREEN: 1, CubeColor.BLACK: 2}
        preload = {CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 2, CubeColor.BLACK: 0}

        for seed in range(50):
            tower.reset()
            tower.load_stuck(preload)
            rng = random.Random(seed)
            exited = tower.drop(staged, rng)
            for color in CubeColor:
                in_count = staged.get(color, 0) + preload.get(color, 0)
                out_count = exited.get(color, 0) + tower.stuck_cubes.get(color, 0)
                self.assertEqual(in_count, out_count, f"Conservation failed for {color} on seed {seed}")

    def test_shogun_boundary_floor(self) -> None:
        cfg = GameConfig.v038c(
            tower_mode=TowerMode.SHOGUN_BAFFLE,
            tower_obstruction_alpha=0.30,
            tower_min_fall_prob=0.35,
        )
        tower = CubeTower(cfg)
        p_fall, p_dis = tower.calculate_shogun_probabilities(4, 2)
        self.assertAlmostEqual(p_fall, 0.35)
        self.assertAlmostEqual(p_dis, 0.21)

    def test_shogun_config_validation(self) -> None:
        invalid_overrides = [
            {"tower_empty_exit_prob": 1.2},
            {"tower_empty_exit_prob": -0.1},
            {"tower_trapping_dislodge_prob": 1.05},
            {"tower_avalanche_fall_prob": -0.01},
            {"tower_avalanche_stuck_threshold": 0},
            {"tower_avalanche_stuck_threshold": -1},
            {"tower_avalanche_mass_threshold": 0},
        ]
        for overrides in invalid_overrides:
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    GameConfig.v038c(**overrides)

    def test_shogun_empirical_drop_means(self) -> None:
        cfg = GameConfig.v038c(tower_mode=TowerMode.SHOGUN_BAFFLE)
        tower = CubeTower(cfg)
        rng = random.Random(20261110)

        staged = {
            CubeColor.RED: 1,
            CubeColor.BLUE: 1,
            CubeColor.GREEN: 1,
            CubeColor.BLACK: 1,
        }
        n_trials = 20000
        drop1_exited = []
        drop2_exited = []
        drop2_by_s1 = {0: [], 1: [], 2: [], 3: [], 4: []}

        for _ in range(n_trials):
            tower.reset()
            ex1 = tower.drop(staged, rng)
            e1 = sum(ex1.values())
            s1 = tower.total_stuck()
            self.assertEqual(e1 + s1, 4)
            drop1_exited.append(e1)

            ex2 = tower.drop(staged, rng)
            e2 = sum(ex2.values())
            drop2_exited.append(e2)
            drop2_by_s1[s1].append(e2)

        mean_e1 = sum(drop1_exited) / len(drop1_exited)
        mean_e2 = sum(drop2_exited) / len(drop2_exited)
        mean_e2_s1 = sum(drop2_by_s1[1]) / len(drop2_by_s1[1])
        mean_e2_s2 = sum(drop2_by_s1[2]) / len(drop2_by_s1[2])
        mean_e2_s3 = sum(drop2_by_s1[3]) / len(drop2_by_s1[3])

        self.assertAlmostEqual(mean_e1, 2.80, delta=0.03)
        self.assertAlmostEqual(mean_e2, 2.58, delta=0.03)
        self.assertAlmostEqual(mean_e2_s1, 2.41, delta=0.04)
        self.assertAlmostEqual(mean_e2_s2, 2.02, delta=0.04)
        self.assertAlmostEqual(mean_e2_s3, 4.50, delta=0.06)

    def test_legacy_tower_parity_intact(self) -> None:
        self.assertEqual(GameConfig().tower_mode, TowerMode.LEDGE_AVALANCHE)
        self.assertEqual(GameConfig.v038c().tower_mode, TowerMode.SHOGUN_BAFFLE)
        self.assertEqual(GameConfig.v038c_legacy_tower().tower_mode, TowerMode.LEDGE_AVALANCHE)

        cfg = GameConfig.legacy_v035()
        self.assertEqual(cfg.tower_mode, TowerMode.LEDGE_AVALANCHE)
        tower = CubeTower(cfg)
        rng = random.Random(42)

        staged = {
            CubeColor.RED: 1,
            CubeColor.BLUE: 1,
            CubeColor.GREEN: 1,
            CubeColor.BLACK: 1,
        }
        ex1 = tower.drop(staged, rng)
        ex2 = tower.drop(staged, rng)

        # Replay with identical seed and explicit LEDGE_AVALANCHE
        tower_ref = CubeTower(GameConfig.legacy_v035(tower_mode=TowerMode.LEDGE_AVALANCHE))
        rng_ref = random.Random(42)
        self.assertEqual(ex1, tower_ref.drop(staged, rng_ref))
        self.assertEqual(ex2, tower_ref.drop(staged, rng_ref))
        self.assertEqual(tower.stuck_cubes, tower_ref.stuck_cubes)


if __name__ == "__main__":
    unittest.main()
