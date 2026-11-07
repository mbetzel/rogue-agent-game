"""Multi-version Black cube spillover cascade (six-phase Phase 2).

RULES.md Phase 2, "Version Advance & Track Spillover": excess Black cubes dropped in the same compile
immediately spill onto the next Version's Corruption Track starting at Space 1, triggering each covered
space's printed effect in sequence. When that spillover itself fills v2.0, the remaining cubes continue
onto v3.0, and filling v3.0's final space triggers Singularity.

Before this fix the engine stopped at v2.0: cubes past v2.0's capacity were counted but never resolved,
and the v3.0 advance waited for a later Black cube.
"""

from __future__ import annotations

import unittest
from typing import List, Tuple
from unittest import mock

from sim.config import CubeColor, EndGameReason, GameConfig
from sim.engine import phase2_compiler
from sim.engine.core import GameEngine
from sim.engine.phase1_roll_deploy import check_and_execute_start_of_round_version_transition
from sim.engine.state import AbilityStatus


def _drop(black: int):
    return lambda cup, rng: {CubeColor.BLACK: black, CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0}


class TestVersionSpilloverCascade(unittest.TestCase):
    def make_engine(self, track_before: int = 3) -> GameEngine:
        engine = GameEngine(GameConfig(num_players=2), seed=7)
        self.assertEqual(
            [v.track_capacity for v in engine.state.version_deck], [4, 5, 6], "STANDARD deck expected"
        )
        engine.state.corruption_track = track_before
        for p in engine.state.players:
            p.secrets = 50  # keep everyone alive through every space
            p.money = 50
        return engine

    def compile(self, engine: GameEngine, black: int) -> List[Tuple[str, int]]:
        """Run one Phase 2 compile; return the (version, space index) of every space resolved, in order."""
        deck = engine.state.version_deck
        owner = {id(s): v.version_str for v in deck for s in v.corruption_track}
        resolved: List[Tuple[str, int]] = []
        real = phase2_compiler.resolve_corruption_space

        def spy(engine, space, *args, **kwargs):
            resolved.append((owner[id(space)], space.index))
            return real(engine, space, *args, **kwargs)

        engine.state.tower.drop = _drop(black)
        commitments = [(p, [], {}) for p in engine.state.players]
        with mock.patch.object(phase2_compiler, "resolve_corruption_space", spy):
            cr = phase2_compiler.execute_compiler_drop(engine, commitments)
        phase2_compiler.check_end_triggers_after_compiler(engine, cr)
        return resolved

    def test_fill_v1_and_v2_then_spill_onto_v3(self) -> None:
        """v1.0 at 3/4, 8 Black cubes: v1.0 #4, v2.0 #1-5, v3.0 #1-2 all resolve in order."""
        engine = self.make_engine(track_before=3)
        resolved = self.compile(engine, 8)

        expected = [("v1.0", 4)] + [("v2.0", i) for i in range(1, 6)] + [("v3.0", 1), ("v3.0", 2)]
        self.assertEqual(resolved, expected)
        self.assertFalse(engine.state.singularity_triggered)
        self.assertFalse(engine.state.game_over)
        # Active version card stays v1.0 for the rest of this round.
        self.assertEqual(engine.state.active_version.version_str, "v1.0")
        self.assertTrue(engine.state.pending_version_advance)

        # Next round Phase 1 Step 1: both transitions execute, landing on v3.0 with 2 cubes.
        self.assertTrue(check_and_execute_start_of_round_version_transition(engine))
        self.assertEqual(engine.state.active_version.version_str, "v3.0")
        self.assertEqual(engine.state.corruption_track, 2)
        self.assertFalse(engine.state.pending_version_advance)
        self.assertEqual(engine.state.overflow_black_cubes_on_next_track, 0)
        for p in engine.state.players:
            self.assertEqual(p.ability_v2_status, AbilityStatus.FORFEITED)
            self.assertEqual(p.ability_v3_status, AbilityStatus.AVAILABLE)

    def test_exactly_fill_v2_by_spillover_advances_to_v3(self) -> None:
        """v1.0 at 3/4, 6 Black cubes: v2.0 fills exactly; next round starts on v3.0 at 0, not v2.0 at 5."""
        engine = self.make_engine(track_before=3)
        resolved = self.compile(engine, 6)
        self.assertEqual(resolved, [("v1.0", 4)] + [("v2.0", i) for i in range(1, 6)])

        check_and_execute_start_of_round_version_transition(engine)
        self.assertEqual(engine.state.active_version.version_str, "v3.0")
        self.assertEqual(engine.state.corruption_track, 0)

        # The next Black cube lands on v3.0 Space 1 (no cube is wasted on a phantom v2.0 Space 6).
        resolved = self.compile(engine, 1)
        self.assertEqual(resolved, [("v3.0", 1)])
        self.assertFalse(engine.state.pending_version_advance)

    def test_cascade_through_v3_triggers_singularity(self) -> None:
        """v1.0 at 3/4, 14 Black cubes: 1 + 5 + 6 covers v3.0 Space 6 -> Singularity this Phase 2."""
        engine = self.make_engine(track_before=3)
        resolved = self.compile(engine, 14)  # 2 more than needed: they must not resolve anything

        expected = [("v1.0", 4)] + [("v2.0", i) for i in range(1, 6)] + [("v3.0", i) for i in range(1, 7)]
        self.assertEqual(resolved, expected)
        self.assertTrue(engine.state.singularity_triggered)
        self.assertTrue(engine.state.game_over)
        self.assertEqual(engine.state.end_reason, EndGameReason.SINGULARITY)
        self.assertEqual(engine.state.active_version.version_str, "v3.0")
        self.assertEqual(engine.state.corruption_track, 6)
        self.assertFalse(engine.state.pending_version_advance)

    def test_single_version_spillover_unchanged(self) -> None:
        """Regression guard: v1.0 at 3/4, 3 Black cubes -> v1.0 #4, v2.0 #1-2; next round v2.0 at 2."""
        engine = self.make_engine(track_before=3)
        resolved = self.compile(engine, 3)
        self.assertEqual(resolved, [("v1.0", 4), ("v2.0", 1), ("v2.0", 2)])
        self.assertEqual(engine.state.overflow_black_cubes_on_next_track, 2)
        check_and_execute_start_of_round_version_transition(engine)
        self.assertEqual(engine.state.active_version.version_str, "v2.0")
        self.assertEqual(engine.state.corruption_track, 2)


if __name__ == "__main__":
    unittest.main()
