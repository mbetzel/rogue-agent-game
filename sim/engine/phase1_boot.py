"""Deprecated v0.33 module name. Re-exports Phase 1: Roll & Deploy (see ``phase1_roll_deploy``)."""

from sim.engine.phase1_roll_deploy import *  # noqa: F401,F403
from sim.engine.phase1_roll_deploy import (  # noqa: F401
    apply_immediate_face_outputs,
    apply_single_die_immediate_output,
    check_and_execute_start_of_round_version_transition,
    check_operator_contingent_staffing,
    detect_hash_matches,
    detect_hash_matches_with_cipher,
    execute_phase_1,
    get_face_signature,
    resolve_prodigy_purple_star_override,
)

__all__ = [
    "get_face_signature",
    "detect_hash_matches_with_cipher",
    "detect_hash_matches",
    "resolve_prodigy_purple_star_override",
    "check_operator_contingent_staffing",
    "check_and_execute_start_of_round_version_transition",
    "execute_phase_1",
    "apply_single_die_immediate_output",
    "apply_immediate_face_outputs",
]
