"""Deprecated v0.33 module. Re-exports with v0.33 semantics regardless of ``round_sequence``
(INV-SEQ-SHIM-LEGACY-01). See ``phase3_income`` / ``phase5_pipeline_shift`` / ``phase6_operations`` /
``legacy_v033``.

NOTE: purchases now bind ``create_colored_die`` inside ``sim.engine.phase6_operations``. Monkeypatching
``sim.engine.phase3_ops.create_colored_die`` no longer affects purchases; patch
``sim.engine.phase6_operations.create_colored_die`` instead.
"""

from sim.entities import create_colored_die  # noqa: F401  (attribute kept for v0.33 importers)
from sim.engine.phase3_income import (  # noqa: F401
    collect_player_production_income,
    collect_production_income,
    resolve_phreaker_jumper_diagnostics,
    resolve_spook_burn_notice,
)
from sim.engine.legacy_v033 import execute_phase_3_v033

execute_phase_3 = execute_phase_3_v033

__all__ = [
    "execute_phase_3",
    "collect_player_production_income",
    "collect_production_income",
    "resolve_spook_burn_notice",
    "resolve_phreaker_jumper_diagnostics",
    "create_colored_die",
]
