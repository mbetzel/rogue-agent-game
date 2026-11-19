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
from sim.config import ROUND_PHASE_NAMES, CubeColor, DieColor, EndGameReason, GameConfig, RoundPhase, ShieldColor
from sim.bots import research_policy
from sim.engine import research_tracks, secret_faces, phase1_roll_deploy, vulnerability
from sim.engine import EndGameResult, GameEngine, GameState, PlayerState
from sim.engine.phase1_boot import (
    check_operator_contingent_staffing,
    detect_hash_matches,
    resolve_prodigy_purple_star_override,
)
from sim.engine.state import ProductionRole
from sim.entities import has_company_override, has_signature_protocol, legacy_bridge_enabled
from sim.entities import (
    AbilityStatus,
    ArchetypeCard,
    ArchetypeCode,
    CompanyCode,
    WhiteHatCode,
    Die,
    VariantCard,
    VersionCard,
    create_colored_die,
    create_white_die,
)

if TYPE_CHECKING:
    from web.controller.core import GameController


def hire_contractors(
    controller: GameController,
    player_id: int,
    count: int = 1,
    use_operator_ability: bool = False,
    buy_third_die: bool = False,
) -> Dict[str, Any]:
    """Hires 1-3 temporary White Contractor dice during Phase 1 before rolling."""
    if not getattr(controller.state.config, "white_contractor_dice_enabled", True) or controller.state.config.contractor_max_hire <= 0:
        raise ValueError("Contractor hiring is disabled in v0.40.0")
    if controller.phase != 1:
        raise ValueError(f"Cannot hire contractors in phase {controller.phase} ({controller.phase_name})")
    if player_id not in controller.player_meta:
        raise ValueError(f"Invalid player_id {player_id}")

    meta = controller.player_meta[player_id]
    player = controller.state.players[player_id]

    if player.is_patient_zero:
        raise ValueError(f"Player {player_id} is eliminated")
    if meta["has_rolled"]:
        raise ValueError("Cannot hire contractors after rolling pool")
    if not isinstance(count, int) or not (1 <= count <= controller.state.config.contractor_max_hire):
        raise ValueError(f"Contractor hire count must be between 1 and {controller.state.config.contractor_max_hire}, got {count}")

    already_hired = meta.get("hired_contractors", 0)
    if already_hired + count > controller.state.config.contractor_max_hire:
        raise ValueError(f"Cannot hire {count} contractors: already hired {already_hired}, max allowed is {controller.state.config.contractor_max_hire}")

    active_ver = controller.state.active_version.version_str
    if use_operator_ability:
        is_operator_corp = has_company_override(player, CompanyCode.MERIDIAN, legacy_bridge_enabled(controller))
        if not is_operator_corp:
            raise ValueError("Player is not The Operator")
        if not player.is_ability_available(active_ver):
            raise ValueError(f"Operator ability already used or forfeited for {active_ver}")
        # Free hire up to 2
        free_hire = min(count if count <= 2 else 2, controller.state.contractor_supply)
        third_hire = 1 if (count >= 3 or buy_third_die) and (controller.state.contractor_supply > free_hire) else 0
        cost = controller.state.config.get_contractor_cost_for_hire(1, already_hired=free_hire) if third_hire > 0 else 0
        total_hire = free_hire + third_hire

        if player.money < cost:
            raise ValueError(f"Insufficient funds for 3rd contractor die: need ${cost}, have ${player.money}")
        if controller.state.contractor_supply < total_hire:
            raise ValueError(f"Insufficient contractor supply: requested {total_hire}, available {controller.state.contractor_supply}")

        player.money -= cost
        controller.state.contractor_supply -= total_hire
        player.hired_contractor_count += total_hire
        player.total_contractors_hired += total_hire
        meta["hired_contractors"] = already_hired + total_hire
        for _ in range(total_hire):
            c_die = create_white_die(controller.state.next_die_id)
            controller.state.next_die_id += 1
            player.contractor_dice.append(c_die)

        player.mark_ability_used(active_ver)
        controller.event_log.append(
            f"{meta['name']} triggered Redundant Crew: hired {total_hire} Contractor dice for ${cost}."
        )
        return controller.get_full_state()

    cost = controller.state.config.get_contractor_cost_for_hire(count, already_hired=already_hired)
    if player.money < cost:
        raise ValueError(f"Insufficient funds: need ${cost}, have ${player.money}")
    if controller.state.contractor_supply < count:
        raise ValueError(f"Insufficient contractor supply: requested {count}, available {controller.state.contractor_supply}")

    player.money -= cost
    controller.state.contractor_supply -= count
    player.hired_contractor_count += count
    player.total_contractors_hired += count
    meta["hired_contractors"] = already_hired + count

    for _ in range(count):
        c_die = create_white_die(controller.state.next_die_id)
        controller.state.next_die_id += 1
        player.contractor_dice.append(c_die)

    controller.event_log.append(
        f"{meta['name']} hired {count} Contractor dice for ${cost} (Total hired: {meta['hired_contractors']}, Remaining supply: {controller.state.contractor_supply})."
    )
    return controller.get_full_state()



def roll_pool(controller: GameController, player_id: int) -> Dict[str, Any]:
    """Rolls the ready pool and contractor dice for an interactive human player in Phase 1."""
    if controller.phase != 1:
        raise ValueError(f"Cannot roll pool in phase {controller.phase} ({controller.phase_name})")
    if player_id not in controller.player_meta:
        raise ValueError(f"Invalid player_id {player_id}")

    meta = controller.player_meta[player_id]
    player = controller.state.players[player_id]

    if player.is_patient_zero:
        raise ValueError(f"Player {player_id} is eliminated (Patient Zero)")
    if meta["has_rolled"]:
        raise ValueError(f"Player {player_id} has already rolled their pool this round")

    # Roll active pool (ready_dice + contractor_dice)
    active_dice: List[Die] = list(player.ready_dice) + list(player.contractor_dice)
    for die in active_dice:
        die.is_locked = False
        die.roll(controller.engine.rng)

    # Operator Contingent Staffing Face 6 Protocol
    is_operator_op = has_signature_protocol(player, WhiteHatCode.OPERATOR, legacy_bridge_enabled(controller))
    if is_operator_op:
        c_die = check_operator_contingent_staffing(controller.engine or controller, player, active_dice)
        if c_die:
            controller.event_log.append(
                f"{meta['name']} triggered Operator Contingent Staffing: free White Contractor die rolled into pool."
            )

    meta["rolled_pool"] = list(active_dice)
    meta["has_rolled"] = True
    controller.subphase = "waiting_for_commit"

    # Evaluate locks
    for die in active_dice:
        face = die.current_face
        if not face:
            continue
        if face.is_glitch:
            die.is_locked = True

    face_names = [
        f"{d.current_face.name}{' [LOCKED]' if d.is_locked else ''}" if d.current_face else "?"
        for d in active_dice
    ]
    controller.event_log.append(f"{meta['name']} rolled {len(active_dice)} dice: {', '.join(face_names)}")
    return controller.get_full_state()



def _activate_bypass(controller: GameController, player: PlayerState, meta: Dict[str, Any]) -> None:
    """Helix Brute-Force Bypass (Phase 1 Step 4): +1 free reroll this phase (v0.38), Glitch dice may be rerolled,
    and one rolled die may be turned to any legal non-Star face of its colour (``override_face``)."""
    is_helix = has_company_override(player, CompanyCode.HELIX, legacy_bridge_enabled(controller))
    if not is_helix:
        raise ValueError("Player does not have the Brute-Force Bypass override")
    if meta.get("prodigy_active", False):
        return
    if not player.is_ability_available(controller.state.active_version.version_str):
        raise ValueError("Brute-Force Bypass is not available")
    player.mark_ability_used(controller.state.active_version.version_str)
    meta["prodigy_active"] = True
    if controller.state.config.power_profile == "V038_DRAFT":
        meta["rerolls_remaining"] = meta.get("rerolls_remaining", 0) + 1
        meta["max_rerolls"] = meta.get("max_rerolls", 0) + 1
    controller.event_log.append(f"{meta['name']} activated Brute-Force Bypass.")


def override_face(controller: GameController, player_id: int, die_index: int, face_index: int,
                  source: str = "helix") -> Dict[str, Any]:
    """Turns one rolled die to a legal non-Star face of its colour.

    ``source="helix"``: Brute-Force Bypass (once; the Secret face is allowed). ``source="prodigy"``: Arbitrary Code
    Execution (needs a rolled Purple ``★`` on another die; the Secret face is not allowed)."""
    if controller.phase != 1:
        raise ValueError(f"Cannot override a face in phase {controller.phase}")
    if player_id not in controller.player_meta:
        raise ValueError(f"Invalid player_id {player_id}")
    meta = controller.player_meta[player_id]
    player = controller.state.players[player_id]
    if player.is_patient_zero:
        raise ValueError(f"Player {player_id} is eliminated")
    if not meta["has_rolled"] or meta["has_committed"]:
        raise ValueError("Faces can only be overridden after rolling and before committing")
    rolled = meta["rolled_pool"]
    if not (0 <= die_index < len(rolled)):
        raise ValueError(f"Invalid die index {die_index}")
    die = rolled[die_index]
    if not (isinstance(face_index, int) and 0 <= face_index < len(die.faces)):
        raise ValueError(f"Invalid face index {face_index}")
    target = die.faces[face_index]
    if target.is_star:
        raise ValueError("Star faces cannot be chosen")
    if source == "helix":
        if meta.get("helix_override_used"):
            raise ValueError("Brute-Force Bypass face override already used this round")
        _activate_bypass(controller, player, meta)
        meta["helix_override_used"] = True
        label = "Brute-Force Bypass"
    elif source == "prodigy":
        if not has_signature_protocol(player, WhiteHatCode.PRODIGY, legacy_bridge_enabled(controller)):
            raise ValueError("Player is not The Prodigy")
        stars = [i for i, d in enumerate(rolled)
                 if d.current_face and d.current_face.is_star and d.current_face.star_code == "PURPLE_STAR"]
        if len(stars) <= meta.get("ace_uses", 0):
            raise ValueError("No unused Purple star showing for Arbitrary Code Execution")
        if die_index in stars:
            raise ValueError("Arbitrary Code Execution must target another die")
        if target.secrets_pending and not getattr(controller.state.config, "ace_allows_secret_face", False):
            raise ValueError("Arbitrary Code Execution cannot set the Secret face")
        meta["ace_uses"] = meta.get("ace_uses", 0) + 1
        label = "Arbitrary Code Execution"
    elif source == "release_l4":
        if die_index not in release_l4_gray_faces(player, rolled):
            raise ValueError("The Release Track Level 4 Capstone sets 1 rolled Gray Legacy die")
        if meta.get("release_l4_used"):
            raise ValueError("The Release Track Level 4 Capstone was already used this round")
        meta["release_l4_used"] = True
        label = "Release Track Level 4 Capstone"
    else:
        raise ValueError(f"Unknown face override source {source!r}")
    die.current_face = target
    die.is_locked = bool(target.is_glitch)
    die.chosen_choice_index = None
    controller.event_log.append(f"{meta['name']} used {label}: {die.color.value.capitalize()} die #{die_index + 1} -> '{target.name}'.")
    return controller.get_full_state()


def perform_reroll(
    controller: GameController,
    player_id: int,
    reroll_indices: List[int],
    use_prodigy_ability: bool = False,
) -> Dict[str, Any]:
    if player_id not in controller.player_meta:
        raise ValueError(f"Invalid player_id {player_id}")

    meta = controller.player_meta[player_id]
    player = controller.state.players[player_id]

    if player.is_patient_zero:
        raise ValueError(f"Player {player_id} is eliminated")
    if not meta["has_rolled"]:
        raise ValueError("Must roll pool before rerolling")
    if meta["has_committed"]:
        raise ValueError("Cannot reroll after committing defenses")
    if use_prodigy_ability and not meta.get("prodigy_active", False):
        _activate_bypass(controller, player, meta)  # v0.38: Brute-Force Bypass grants +1 free reroll first
    if meta.get("rerolls_remaining", 0) <= 0:
        raise ValueError("No free rerolls remaining this round")
    if not isinstance(reroll_indices, list) or len(reroll_indices) == 0:
        raise ValueError("reroll_indices must be a non-empty list of integers")

    prodigy_allowed = use_prodigy_ability or meta.get("prodigy_active", False)
    rolled = meta["rolled_pool"]
    for idx in reroll_indices:
        if not isinstance(idx, int) or not (0 <= idx < len(rolled)):
            raise ValueError(f"Invalid die index {idx}. Rolled pool size: {len(rolled)}")
        if not prodigy_allowed and rolled[idx].is_locked:
            raise ValueError(f"Die #{idx + 1} ({rolled[idx].color.value}) is locked and cannot be rerolled")

    rerolled_faces = []
    for idx in reroll_indices:
        die = rolled[idx]
        new_face = die.roll(controller.engine.rng)
        die.is_locked = False
        rerolled_faces.append(f"#{idx + 1} ({new_face.name})")

    meta["rerolls_remaining"] -= 1
    player.total_rerolls_used += 1

    # Re-evaluate locks on all dice in rolled_pool
    for d in rolled:
        face = d.current_face
        if not face:
            continue
        if face.is_glitch:
            d.is_locked = True

    # Operator Contingent Staffing Face 6 Protocol (if not triggered yet)
    is_operator_op = has_signature_protocol(player, WhiteHatCode.OPERATOR, legacy_bridge_enabled(controller))
    if is_operator_op:
        c_die = check_operator_contingent_staffing(controller.engine or controller, player, rolled)
        if c_die:
            controller.event_log.append(
                f"{meta['name']} triggered Operator Contingent Staffing: free White Contractor die rolled into pool."
            )

    controller.event_log.append(
        f"{meta['name']} rerolled dice {', '.join(rerolled_faces)} ({meta['rerolls_remaining']} rerolls remaining)."
    )
    return controller.get_full_state()



def _log_pipeline(controller: GameController, meta: Dict[str, Any], msg: str) -> None:
    controller.event_log.append(f"{meta['name']} {msg}")


def finalize_assignment(
    controller: GameController,
    player: PlayerState,
    meta: Dict[str, Any],
    active_dice: List[Die],
) -> None:
    """Phase 1 Step 4 post-processing for a human (mirrors ``sim.engine.phase1_roll_deploy``): White Contractor
    Glitch -> supply, Secret faces -> Processing Box, every other die deployed In Production."""
    st = controller.state
    surviving_active: List[Die] = []
    for die in active_dice:
        face = die.current_face
        if face and face.secrets_pending:
            if die in player.ready_for_release_dice:
                player.ready_for_release_dice.remove(die)
            secret_faces.enter_processing_box(player, die, st.current_round)
            _log_pipeline(controller, meta, f"{die.color.value.capitalize()} die showed a Secret face: moved to the Processing Box.")
        elif face and face.is_glitch:
            if die.color == DieColor.WHITE:
                if die in player.contractor_dice:
                    player.contractor_dice.remove(die)
                st.contractor_supply += 1
                player.hired_contractor_count = max(0, len(player.contractor_dice))
                meta["hired_contractors"] = len(player.contractor_dice)
                _log_pipeline(controller, meta, "White Contractor glitched: discarded to supply.")
            else:
                if die in player.ready_for_release_dice:
                    player.ready_for_release_dice.remove(die)
                player.glitched_dice.append(die)
                _log_pipeline(controller, meta, f"{die.color.value.capitalize()} die glitched: moved to Under Development.")
        else:
            surviving_active.append(die)

    player.in_production_dice.clear()
    for die in surviving_active:
        face = die.effective_face or die.current_face
        die.production_role = ProductionRole.INCOME
        if face and face.is_star:  # v0.44+ resolves B2 / Y1 in Phase 3; P3 needed a shield (retired)
            if face.star_code == "P1":
                player.p1_available = True
            elif face.star_code == "PURPLE_STAR":
                player.purple_star_available = True
                player.purple_star_count += 1
        player.in_production_dice.append(die)

    player.ready_for_release_dice.clear()
    meta["rolled_pool"] = surviving_active
    meta["has_rolled"] = True
    meta["has_committed"] = True


def release_l4_gray_faces(player: PlayerState, rolled: List[Die]) -> List[int]:
    """Rolled-pool indices of Gray dice the Release Track L4 Capstone may set (empty when it is unavailable)."""
    cfg = player.config
    if not getattr(cfg, "release_l4_set_gray_face", False) or int(player.release_level) < 4:
        return []
    return [i for i, d in enumerate(rolled) if d.color == DieColor.GRAY]


def lock_in(
    controller: GameController,
    player_id: int,
    choice_declarations: Optional[Dict[int, int]] = None,
) -> Dict[str, Any]:
    """Phase 1 Step 4 for a human: Lock-in & Assign Dice.

    Declares Choice Faces (``choice_declarations`` maps rolled-pool index -> option index; default option 0), gains
    ``+1`` Vulnerability per ⚠ on the final faces (``vulnerability.lock_in``), sends Secret faces to the Processing
    Box and deploys every other die In Production. Nothing is blocked in v0.46.0, so there is no shield step."""
    if controller.phase != 1:
        raise ValueError(f"Cannot lock in dice in phase {controller.phase}")
    if player_id not in controller.player_meta:
        raise ValueError(f"Invalid player_id {player_id}")

    meta = controller.player_meta[player_id]
    player = controller.state.players[player_id]

    if player.is_patient_zero:
        raise ValueError(f"Player {player_id} is eliminated")
    if not meta["has_rolled"]:
        raise ValueError("Must roll the Ready Pool before locking in")
    if meta["has_committed"]:
        raise ValueError("Dice have already been locked in this round")

    rolled = meta["rolled_pool"]
    choice_decls: Dict[int, int] = {}
    for k, v in (choice_declarations or {}).items():
        try:
            choice_decls[int(k)] = int(v)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid choice declaration {k!r}: {v!r}")
    for idx in choice_decls:
        if not (0 <= idx < len(rolled)):
            raise ValueError(f"Invalid die index {idx} in choice_declarations")

    for idx, die in enumerate(rolled):
        face = die.current_face
        if face and face.is_choice:
            chosen = choice_decls.get(idx, 0)
            die.chosen_choice_index = chosen if 0 <= chosen < len(face.choices) else 0

    before = player.vulnerability
    gained = vulnerability.lock_in(controller.engine, player, rolled)
    icons = sum(vulnerability.face_vuln(d.current_face) for d in rolled)
    lost = icons - gained
    controller.event_log.append(
        f"{meta['name']} locked in {len(rolled)} dice: {icons} ⚠, Vulnerability {before} -> {player.vulnerability}"
        + (f" ({lost} lost at the top of the Vulnerability Track)" if lost > 0 else "") + "."
    )

    finalize_assignment(controller, player, meta, rolled)

    all_humans_committed = all(
        m["has_committed"]
        for pid, m in controller.player_meta.items()
        if m["is_human"] and not controller.state.players[pid].is_patient_zero
    )
    if all_humans_committed:
        auto_execute_bots_phase_1(controller)
        controller.phase = int(RoundPhase.COMPILER_DROP_AND_CORRUPTION)
        controller.phase_name = ROUND_PHASE_NAMES[controller.phase]
        controller.subphase = "ready_for_compile"
        controller.event_log.append("All corporations have locked in. Ready for Compile Drop.")

    return controller.get_full_state()


def auto_execute_bots_phase_1(controller: GameController) -> None:
    """Runs Phase 1 for every bot through the engine (staffing, roll, rerolls, Step 5), then mirrors the result into
    the web metadata. The once-per-round steps (version switch, Pulse, round flags) already ran in ``_start_phase_1``."""
    bot_ids = {
        pid for pid, meta in controller.player_meta.items()
        if not meta["is_human"] and not controller.state.players[pid].is_patient_zero
    }
    if not bot_ids:
        return
    results = phase1_roll_deploy.execute_phase_1(controller.engine, player_ids=bot_ids, prelude=False)
    for player, surviving, commitments in results:
        meta = controller.player_meta[player.player_id]
        meta["rolled_pool"] = list(surviving)
        meta["has_rolled"] = True
        meta["has_committed"] = True
        meta["hired_contractors"] = player.hired_contractor_count
