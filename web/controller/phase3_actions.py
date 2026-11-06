"""Deprecated v0.33 module name (kept one release). Re-exports the v0.34 web action modules."""

from web.controller.phase6_operations_actions import *  # noqa: F401,F403
from web.controller.phase6_operations_actions import (  # noqa: F401
    advance_operations_turns,
    advance_phase3_turns,
    buy_die,
    enter_phase_6,
    execute_bot_operations,
    execute_bot_phase3,
    phreaker_diagnostics,
    spook_burn,
    use_phreaker_ability,
)
from web.controller.phase3_income_actions import confirm_income  # noqa: F401
from web.controller.phase4_attack_actions import confirm_attacks  # noqa: F401
from web.controller.phase5_pipeline_actions import choose_graduates  # noqa: F401
