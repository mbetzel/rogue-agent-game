"""Web round phase ids (v0.49.0, RULES.md Section 4).

The rules order Operations before the CI/CD Pipeline Shift (``GameConfig.operations_before_pipeline_shift``), so the
web numbers its phases as the rules do. ``sim.config.RoundPhase`` keeps the legacy numbering (5 = Pipeline Shift,
6 = Operations) for the engine, so the web never uses those two enum values for its own state.
"""

from __future__ import annotations

from sim.config import ROUND_PHASE_NAMES, RoundPhase

ROLL_AND_DEPLOY = int(RoundPhase.ROLL_AND_DEPLOY)              # 1
COMPILER_DROP = int(RoundPhase.COMPILER_DROP_AND_CORRUPTION)    # 2
INCOME = int(RoundPhase.INCOME)                                 # 3
ATTACK_RESOLUTION = int(RoundPhase.ATTACK_RESOLUTION)           # 4
OPERATIONS = 5
PIPELINE_SHIFT = 6
GAME_OVER = int(RoundPhase.GAME_OVER)                           # 7

PHASE_NAMES = {
    ROLL_AND_DEPLOY: ROUND_PHASE_NAMES[1],
    COMPILER_DROP: ROUND_PHASE_NAMES[2],
    INCOME: ROUND_PHASE_NAMES[3],
    ATTACK_RESOLUTION: ROUND_PHASE_NAMES[4],
    OPERATIONS: "Operations",
    PIPELINE_SHIFT: "CI/CD Pipeline Shift",
    GAME_OVER: ROUND_PHASE_NAMES[7],
}
