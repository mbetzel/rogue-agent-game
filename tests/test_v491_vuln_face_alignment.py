"""v0.49.1: every ⚠ face is printed on Face 1 or Face 5 (Gray: Face 1); payouts match v0.49.0."""
import unittest
from collections import Counter

from sim.config import DieColor, GameConfig
from sim.entities import create_colored_die, create_gray_die

COLORED = (DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW, DieColor.PURPLE)


def vuln_faces(die):
    return [i + 1 for i, f in enumerate(die.faces) if f.vuln]


class TestV491VulnFaceAlignment(unittest.TestCase):
    def setUp(self):
        self.cfg = GameConfig.v049(num_players=3)

    def test_v049_uses_aligned_profiles(self):
        self.assertEqual(self.cfg.die_face_profile, "V0491_ALIGNED")
        self.assertEqual(self.cfg.gray_face_profile, "V0491_ALIGNED")

    def test_gray_vuln_on_face_1_only(self):
        self.assertEqual(vuln_faces(create_gray_die(0, self.cfg.gray_face_profile)), [1])

    def test_colored_vuln_on_faces_1_and_5(self):
        for color in COLORED:
            with self.subTest(color=color):
                die = create_colored_die(color, 0, face_profile=self.cfg.die_face_profile)
                self.assertEqual(vuln_faces(die), [1, 5])
                self.assertTrue(die.faces[5].is_star)

    def test_same_faces_as_v049_0(self):
        """Only the order changes: the multiset of faces equals the v0.49.0 tables."""
        names = lambda d: Counter(f.name for f in d.faces)  # noqa: E731
        self.assertEqual(names(create_gray_die(0, "V0491_ALIGNED")), names(create_gray_die(0, "V048_SPRINT")))
        for color in COLORED:
            with self.subTest(color=color):
                self.assertEqual(names(create_colored_die(color, 0, face_profile="V0491_ALIGNED")),
                                 names(create_colored_die(color, 0, face_profile="V046_VULN")))


if __name__ == "__main__":
    unittest.main()
