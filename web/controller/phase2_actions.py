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
from sim.engine.state import ProductionRole
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
            "any": sum(1 for c in commitments.values() if c == "any"),
        }

    # Human player ids whose green malware resolution is deferred for user choice
    human_pids = {pid for pid, meta in controller.player_meta.items() if meta.get("is_human")}

    # Execute Phase 2 via engine (deferring green malware resolution for human players)
    telemetry = controller.engine._execute_phase_2(player_commitments, defer_green_for_pids=human_pids)

    # Calculate harvested income and details for each player from in_production_dice
    income_breakdowns: Dict[int, Dict[str, Any]] = {}
    player_candidate_glitches: Dict[int, List[Dict[str, Any]]] = {}

    for pid, player in enumerate(controller.state.players):
        if player.is_patient_zero:
            continue
        meta = controller.player_meta[pid]
        is_human = meta.get("is_human", False)
        
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
                elif eff.star_code == "B3":
                    star_note = "Air-Gapped Backup (1 Glitched → Scanned)"
                elif eff.star_code == "R1":
                    star_note = "Ransom Insurance (+$2)"
                elif eff.star_code == "G1":
                    star_note = "Self-Healing Kernel (+1 🔬)"
                elif eff.star_code == "G2":
                    star_note = "Universal Sandbox (+1 🔬)"
                elif eff.star_code == "G3":
                    star_note = "Live Reboot (+$1, +2 🔬)"
            role_val = getattr(die, "production_role", None)
            details.append({
                "die_id": die.die_id,
                "color": die.color.value,
                "face_name": eff.name,
                "money": m,
                "patches": p_patches,
                "secrets": s,
                "star_note": star_note,
                "role": role_val.value if role_val else "INCOME",
            })

        # Build candidate glitch dice for this player
        candidates: List[Dict[str, Any]] = []
        # 1. Any contractor dice
        for d in player.contractor_dice:
            eff = d.effective_face or d.current_face
            candidates.append({
                "die_id": d.die_id,
                "color": d.color.value,
                "face_name": eff.name if eff else "Contractor",
                "role": "Contractor",
                "money": 0,
                "patches": 0,
                "secrets": 0,
                "star_note": None,
                "is_contractor": True,
                "is_shield": False,
                "is_income": False,
                "is_fallback": False,
            })
        # 2. In production dice (income and shields)
        for d in player.in_production_dice:
            eff = d.effective_face or d.current_face
            role_val = getattr(d, "production_role", None)
            role_name = "Income"
            is_shield = False
            is_income = True
            if role_val in (ProductionRole.RED_SHIELD, ProductionRole.BLUE_SHIELD, ProductionRole.GREEN_SHIELD, ProductionRole.ANY_SHIELD):
                role_name = role_val.value.replace("_", " ").title()
                is_shield = True
                is_income = False
            d_money = 0
            d_patches = 0
            d_secrets = 0
            d_star_note = None
            for det in details:
                if det["die_id"] == d.die_id:
                    d_money = det["money"]
                    d_patches = det["patches"]
                    d_secrets = det["secrets"]
                    d_star_note = det["star_note"]
                    break

            candidates.append({
                "die_id": d.die_id,
                "color": d.color.value,
                "face_name": eff.name if eff else "Module",
                "role": role_name,
                "money": d_money,
                "patches": d_patches,
                "secrets": d_secrets,
                "star_note": d_star_note,
                "is_contractor": (d.color == DieColor.WHITE),
                "is_shield": is_shield,
                "is_income": is_income,
                "is_fallback": False,
            })

        # Under v0.31.0 INV-MALWARE-FIZZLE-01: No Destruction Fallback!
        # If no active dice exist in In Production or Contractors, Green malware fizzles with 0 penalty.

        player_candidate_glitches[pid] = candidates

        if not is_human and not controller.state.game_over:
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
        else:
            # Human player or game over: income preview (actual collection happens on confirm_income after glitch choices)
            meta["income_collected_this_turn"] = False
            income_breakdowns[pid] = {
                "money": sum(d["money"] for d in details) if not controller.state.game_over else 0,
                "patches": sum(d["patches"] for d in details) if not controller.state.game_over else 0,
                "secrets": sum(d["secrets"] for d in details) if not controller.state.game_over else 0,
                "details": details,
            }

    exited_dict = {c.value: count for c, count in telemetry.exited_cubes.items()}
    atk_dict = {c.value: count for c, count in telemetry.attack_strengths.items()}

    threat_summaries: Dict[int, Dict[str, Any]] = {}
    for pid, shields in player_shields.items():
        player = controller.state.players[pid]
        breakdown = getattr(player, "last_defense_breakdown", None)
        red_atk = atk_dict.get("red", 0)
        blue_atk = atk_dict.get("blue", 0)
        green_atk = atk_dict.get("green", 0)

        if breakdown:
            red_blocked = breakdown["blocked"]["red"]
            red_unblocked = breakdown["unblocked"]["red"]
            blue_blocked = breakdown["blocked"]["blue"]
            blue_unblocked = breakdown["unblocked"]["blue"]
            green_blocked = breakdown["blocked"]["green"]
            green_unblocked = breakdown["unblocked"]["green"]
            unpaid_ransom = breakdown.get("unpaid_ransom", 0)
            flat_leak = breakdown.get("flat_ransom_leak", False)
            fizzled = breakdown.get("malware_fizzled", False)
            any_shields_count = breakdown["color_shields"].get("any", 0)
        else:
            red_blocked = min(shields["red"], red_atk)
            red_unblocked = max(0, red_atk - shields["red"])
            blue_blocked = min(shields["blue"], blue_atk)
            blue_unblocked = max(0, blue_atk - shields["blue"])
            green_blocked = min(shields["green"], green_atk)
            green_unblocked = max(0, green_atk - shields["green"])
            unpaid_ransom = 0
            flat_leak = False
            fizzled = False
            any_shields_count = shields.get("any", 0)

        any_dice_info = []
        meta_p = controller.player_meta[pid]
        for idx, c_val in meta_p.get("commitments", {}).items():
            if c_val == "any" and int(idx) < len(meta_p.get("rolled_pool", [])):
                d = meta_p["rolled_pool"][int(idx)]
                eff = d.effective_face or d.current_face
                any_dice_info.append({
                    "die_id": d.die_id,
                    "color": d.color.value,
                    "face_name": eff.name if eff else "Block 1 Any",
                    "block_amount": eff.block_amount if eff else 1,
                })

        snap_p = getattr(player, "_pre_step2b_snapshot", None)
        threat_summaries[pid] = {
            "any": {
                "shields": any_shields_count,
                "allocated": breakdown.get("any_allocated", {"red": 0, "blue": 0, "green": 0}) if breakdown else {"red": 0, "blue": 0, "green": 0},
                "dice": any_dice_info,
            },
            "effective_attacks": breakdown.get("effective_attacks", {"red": red_atk, "blue": blue_atk, "green": green_atk}) if breakdown else {"red": red_atk, "blue": blue_atk, "green": green_atk},
            "firewall_blocked": breakdown.get("firewall_blocked") if breakdown else None,
            "pre_step2b_money": snap_p.get("money", player.money) if snap_p else player.money,
            "pre_step2b_secrets": snap_p.get("secrets", player.secrets) if snap_p else player.secrets,
            "r2_count": sum(1 for d in meta_p.get("rolled_pool", []) if (d.effective_face or d.current_face) and (d.effective_face or d.current_face).star_code == "R2"),
            "r3_count": sum(1 for d in meta_p.get("rolled_pool", []) if (d.effective_face or d.current_face) and (d.effective_face or d.current_face).star_code == "R3"),
            "b1_count": sum(1 for d in meta_p.get("rolled_pool", []) if (d.effective_face or d.current_face) and (d.effective_face or d.current_face).star_code == "B1"),
            "red": {
                "cubes": exited_dict.get("red", 0),
                "attack": red_atk,
                "shields": shields["red"],
                "blocked": red_blocked,
                "unblocked": red_unblocked,
                "unpaid_ransom": unpaid_ransom,
                "flat_leak": flat_leak,
            },
            "blue": {
                "cubes": exited_dict.get("blue", 0),
                "attack": blue_atk,
                "shields": shields["blue"],
                "blocked": blue_blocked,
                "unblocked": blue_unblocked,
            },
            "green": {
                "cubes": exited_dict.get("green", 0),
                "attack": green_atk,
                "shields": shields["green"],
                "blocked": green_blocked,
                "unblocked": green_unblocked,
                "fizzled": fizzled,
                "pending_glitches": getattr(player, "pending_unblocked_green", 0),
                "candidate_dice": player_candidate_glitches.get(pid, []),
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
        "candidate_glitch_dice": player_candidate_glitches.get(human_pid, []),
        "pending_glitches": getattr(controller.state.players[human_pid], "pending_unblocked_green", 0) if human_pid < len(controller.state.players) else 0,
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

    # Check end game triggers from Step 2C / Singularity Step 2A
    if controller.state.game_over:
        controller.phase = 4
        controller.phase_name = "Game Over"
        controller.subphase = "game_over"
        end_res = controller.engine.evaluate_end_game()
        controller.final_result = controller._serialize_end_game_result(end_res)
        if controller.state.end_reason == EndGameReason.TOTAL_WIPEOUT:
            controller.event_log.append("TOTAL WIPEOUT! All corporations suffered Total Breach simultaneously.")
        elif controller.state.end_reason == EndGameReason.SINGULARITY:
            controller.event_log.append("SINGULARITY REACHED! Project: SETEC completed v3.0 compilation. Game Over!")
        else:
            controller.event_log.append("GAME OVER!")
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

