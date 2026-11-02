from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from sim.bots import (
    AccelerationistBot,
    AdaptiveBalancedBot,
    BaseBot,
    Phase3ActionPlan,
    RecklessSaboteurBot,
    SecOpsTurtleBot,
    VentureGreedBot,
)
from sim.config import CubeColor, DieColor, EndGameReason, GameConfig, ShieldColor
from sim.engine import EndGameResult, GameEngine, GameState, PlayerState
from sim.engine.phase3_ops import collect_player_production_income
from sim.entities import (
    AbilityStatus,
    ArchetypeCard,
    ArchetypeCode,
    Die,
    VariantCard,
    VersionCard,
    create_colored_die,
    create_white_die,
)

if TYPE_CHECKING:
    from web.controller.core import GameController


def compile_drop(controller: GameController) -> Dict[str, Any]:
    """Executes the Cube Tower drop and attack resolution."""
    if controller.phase != 2:
        raise ValueError(f"Cannot compile drop in phase {controller.phase} ({controller.phase_name})")

    # Build player commitments for engine
    player_commitments: List[Tuple[PlayerState, List[Die], Dict[int, ShieldColor]]] = []
    for pid, player in enumerate(controller.state.players):
        if player.is_patient_zero:
            continue
        meta = controller.player_meta[pid]
        rolled = meta["rolled_pool"]
        commitments_enum = {
            int(k): ShieldColor(v) for k, v in meta["commitments"].items()
        }
        player_commitments.append((player, rolled, commitments_enum))

    # Record committed shields before resolution for reporting
    player_shields: Dict[int, Dict[str, int]] = {}
    for pid, player in enumerate(controller.state.players):
        meta = controller.player_meta[pid]
        commitments = meta.get("commitments", {})
        player_shields[pid] = {
            "red": sum(1 for c in commitments.values() if c == "red"),
            "blue": sum(1 for c in commitments.values() if c == "blue"),
            "green": sum(1 for c in commitments.values() if c == "green"),
        }

    # Execute Phase 2 via engine
    telemetry = controller.engine._execute_phase_2(player_commitments)

    # Calculate harvested income and details for each player from in_production_dice
    income_breakdowns: Dict[int, Dict[str, Any]] = {}
    for pid, player in enumerate(controller.state.players):
        if player.is_patient_zero:
            continue
        meta = controller.player_meta[pid]
        
        # Calculate income details from current in_production_dice
        details = []
        for die in player.in_production_dice:
            eff = die.effective_face or die.current_face
            if not eff or eff.is_glitch:
                continue
            m = eff.money
            p_patches = eff.patches
            s = eff.secrets
            star_note = None
            if eff.is_star:
                if eff.star_code == "Y2":
                    count = len({d.color for d in player.colored_dice})
                    total_payout = min(controller.state.config.y2_max_payout, controller.state.config.y2_base_payout + count)
                    bonus = max(0, total_payout - eff.money)
                    m += bonus
                    star_note = f"Cloud Monopoly (+${bonus} bonus)"
                elif eff.star_code == "Y3":
                    star_note = "Proprietary Training (+1 Secret -> Glitched)"
                elif eff.star_code == "R1":
                    star_note = "Ransom Insurance (+$2)"
                elif eff.star_code == "G1":
                    star_note = "Self-Healing Kernel (+1 🔧)"
                elif eff.star_code == "G2":
                    star_note = "Universal Sandbox (+1 🔧)"
                elif eff.star_code == "G3":
                    star_note = "Live Reboot (+$1, +2 🔧)"
            details.append({
                "die_id": die.die_id,
                "color": die.color.value,
                "face_name": eff.name,
                "money": m,
                "patches": p_patches,
                "secrets": s,
                "star_note": star_note,
                "role": getattr(die, "production_role", None).value if getattr(die, "production_role", None) else "INCOME",
            })

        money_before = player.money
        patches_before = player.patches
        secrets_before = player.secrets

        collect_player_production_income(controller.engine, player, None)
        meta["income_collected_this_turn"] = True

        income_breakdowns[pid] = {
            "money": max(0, player.money - money_before),
            "patches": max(0, player.patches - patches_before),
            "secrets": max(0, player.secrets - secrets_before),
            "details": details,
        }

    exited_dict = {c.value: count for c, count in telemetry.exited_cubes.items()}
    atk_dict = {c.value: count for c, count in telemetry.attack_strengths.items()}

    threat_summaries: Dict[int, Dict[str, Any]] = {}
    for pid, shields in player_shields.items():
        red_atk = atk_dict.get("red", 0)
        blue_atk = atk_dict.get("blue", 0)
        green_atk = atk_dict.get("green", 0)
        threat_summaries[pid] = {
            "red": {
                "cubes": exited_dict.get("red", 0),
                "attack": red_atk,
                "shields": shields["red"],
                "blocked": min(shields["red"], red_atk),
                "unblocked": max(0, red_atk - shields["red"]),
            },
            "blue": {
                "cubes": exited_dict.get("blue", 0),
                "attack": blue_atk,
                "shields": shields["blue"],
                "blocked": min(shields["blue"], blue_atk),
                "unblocked": max(0, blue_atk - shields["blue"]),
            },
            "green": {
                "cubes": exited_dict.get("green", 0),
                "attack": green_atk,
                "shields": shields["green"],
                "blocked": min(shields["green"], green_atk),
                "unblocked": max(0, green_atk - shields["green"]),
            },
            "black": {
                "cubes": exited_dict.get("black", 0),
                "corruption_track": controller.state.corruption_track,
            },
        }

    # Find human player id (default 0)
    human_pid = 0
    for pid, meta in controller.player_meta.items():
        if meta.get("is_human"):
            human_pid = pid
            break

    # Update last compile result summary
    controller.last_compile_result = {
        "round": telemetry.round_number,
        "staged_cubes": {c.value: count for c, count in telemetry.staged_cubes.items()},
        "exited_cubes": exited_dict,
        "stuck_cubes_after": {c.value: count for c, count in telemetry.stuck_cubes_after.items()},
        "attack_strengths": atk_dict,
        "corruption_track": controller.state.corruption_track,
        "version_name": controller.state.active_version.name,
        "singularity_triggered": controller.state.singularity_triggered,
        "is_final_round": controller.state.is_final_round,
        "game_over": controller.state.game_over,
        "buffer_overflow": getattr(telemetry, "buffer_overflow", False),
        "income_summary": income_breakdowns,
        "threat_summary": threat_summaries,
        "human_income": income_breakdowns.get(human_pid, {"money": 0, "patches": 0, "secrets": 0, "details": []}),
        "human_threat": threat_summaries.get(human_pid, {}),
    }

    if getattr(telemetry, "buffer_overflow", False):
        controller.event_log.append(
            "BUFFER OVERFLOW! 0 cubes exited the compiler. Idle cycle injects 1 Red, 1 Blue, 1 Green into Staging Cup."
        )
    else:
        exited = controller.last_compile_result["exited_cubes"]
        controller.event_log.append(
            f"Cube Tower Drop results: {exited['red']} Red, {exited['blue']} Blue, {exited['green']} Green, {exited['black']} Black."
        )

    # Check end game triggers from Step 2C
    if controller.state.game_over:
        # Total Wipeout! Game ends immediately; Phase 3 is skipped
        controller.phase = 4
        controller.phase_name = "Game Over"
        controller.subphase = "game_over"
        end_res = controller.engine.evaluate_end_game()
        controller.final_result = controller._serialize_end_game_result(end_res)
        controller.event_log.append("TOTAL WIPEOUT! All corporations suffered Total Breach simultaneously.")
        return controller.get_full_state()

    # Transition to Phase 3: Corporate Operations (Intermediate confirmation step)
    controller.phase = 3
    controller.phase_name = "Corporate Operations"
    controller.subphase = "confirm_income"

    # Reset contractor counters but leave shield_slots visible for review
    for pid, player in enumerate(controller.state.players):
        meta = controller.player_meta[pid]
        meta["hired_contractors"] = 0
        unpatched_ids = {d.die_id for d in player.unpatched_dice}
        ready_ids = {d.die_id for d in player.ready_dice}
        meta["rolled_pool"] = [
            d for d in meta.get("rolled_pool", [])
            if d.die_id not in unpatched_ids and d.die_id in ready_ids
        ]

    # Initialize Phase 3 clockwise queue starting with First Player
    num_players = len(controller.state.players)
    controller.phase3_turn_queue = [
        (controller.state.first_player_index + offset) % num_players
        for offset in range(num_players)
    ]

    controller.event_log.append(
        f"Phase 2 Compile Drop completed. Corporations reviewing defense outcomes and harvesting production income."
    )

    return controller.get_full_state()

# =========================================================================
# Phase 3: Corporate Operations (Interactive)
# =========================================================================

