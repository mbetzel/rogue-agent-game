"""Deprecated v0.33 module. Re-exports with v0.33 semantics regardless of ``round_sequence``
(INV-SEQ-SHIM-LEGACY-01). See ``phase2_compiler`` / ``phase4_attack_resolution`` / ``legacy_v033``."""

from sim.engine.phase2_compiler import (  # noqa: F401
    demote_player_dice_step2a,
    resolve_corruption_space,
    return_player_colored_dice_step2a,
)
from sim.engine.phase4_attack_resolution import resolve_player_defense_and_wear  # noqa: F401
from sim.engine.legacy_v033 import execute_phase_2_v033

execute_phase_2 = execute_phase_2_v033

__all__ = [
    "execute_phase_2",
    "resolve_player_defense_and_wear",
    "resolve_corruption_space",
    "demote_player_dice_step2a",
    "return_player_colored_dice_step2a",
]
