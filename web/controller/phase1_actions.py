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
from sim.engine.phase1_boot import detect_hash_matches
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


def hire_contractors(
    controller: GameController,
    player_id: int,
    count: int = 1,
    use_operator_ability: bool = False,
    buy_third_die: bool = False,
) -> Dict[str, Any]:
    """Hires 1-3 temporary White Contractor dice during Phase 1 before rolling."""
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
        if not (player.archetype and player.archetype.code == ArchetypeCode.OPERATOR):
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

    meta["rolled_pool"] = list(active_dice)
    meta["has_rolled"] = True
    controller.subphase = "waiting_for_commit"

    # Evaluate locks per RULES.md v0.15.0
    for die in active_dice:
        face = die.current_face
        if not face:
            continue
        if face.is_glitch:
            die.is_locked = True
        elif "CASH" in controller.state.active_phase1_locks and face.has_cash_option:
            die.is_locked = True
        elif "PATCH" in controller.state.active_phase1_locks and face.has_patch_option:
            die.is_locked = True
        elif "SHIELD" in controller.state.active_phase1_locks and face.has_shield_option:
            die.is_locked = True

    face_names = [
        f"{d.current_face.name}{' [LOCKED]' if d.is_locked else ''}" if d.current_face else "?"
        for d in active_dice
    ]
    controller.event_log.append(f"{meta['name']} rolled {len(active_dice)} dice: {', '.join(face_names)}")
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
    if meta.get("rerolls_remaining", 0) <= 0:
        raise ValueError("No free rerolls remaining this round")
    if not isinstance(reroll_indices, list) or len(reroll_indices) == 0:
        raise ValueError("reroll_indices must be a non-empty list of integers")

    if use_prodigy_ability:
        if not player.archetype or player.archetype.code != ArchetypeCode.PRODIGY:
            raise ValueError("Player does not have the Prodigy archetype")
        if not meta.get("prodigy_active", False) and not player.is_ability_available():
            raise ValueError("Prodigy ability is not available")

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

    if use_prodigy_ability and not meta.get("prodigy_active", False):
        player.mark_ability_used()
        meta["prodigy_active"] = True
        controller.event_log.append(
            f"{meta['name']} activated Prodigy Brute-Force Bypass to reroll locked dice."
        )

    # Re-evaluate locks on all dice in rolled_pool
    for d in rolled:
        face = d.current_face
        if not face:
            continue
        if face.is_glitch:
            d.is_locked = True
        elif "CASH" in controller.state.active_phase1_locks and face.has_cash_option:
            d.is_locked = True
        elif "PATCH" in controller.state.active_phase1_locks and face.has_patch_option:
            d.is_locked = True
        elif "SHIELD" in controller.state.active_phase1_locks and face.has_shield_option:
            d.is_locked = True

    controller.event_log.append(
        f"{meta['name']} rerolled dice {', '.join(rerolled_faces)} ({meta['rerolls_remaining']} rerolls remaining)."
    )
    return controller.get_full_state()



def debug_unlock_die(controller: GameController, player_id: int, die_index: int) -> Dict[str, Any]:
    """Spends 1 🔧 token to unlock a locked die, allowing it to be rerolled in remaining rerolls."""
    if controller.phase != 1:
        raise ValueError(f"Cannot debug unlock in phase {controller.phase}")
    if player_id not in controller.player_meta:
        raise ValueError(f"Invalid player_id {player_id}")

    meta = controller.player_meta[player_id]
    player = controller.state.players[player_id]

    if player.is_patient_zero:
        raise ValueError(f"Player {player_id} is eliminated")
    if not meta["has_rolled"]:
        raise ValueError("Must roll pool before debug unlocking")
    if meta["has_committed"]:
        raise ValueError("Cannot debug unlock after committing defenses")

    rolled = meta["rolled_pool"]
    if not (0 <= die_index < len(rolled)):
        raise ValueError(f"Invalid die_index {die_index}. Rolled pool size: {len(rolled)}")

    die = rolled[die_index]
    if not die.is_locked:
        raise ValueError(f"Die #{die_index + 1} is not locked")

    if player.patches < 1:
        raise ValueError("Not enough patch tokens (🔧) to debug unlock")

    player.patches -= 1
    die.is_locked = False

    controller.event_log.append(
        f"{meta['name']} spent 1 🔧 to debug unlock die #{die_index + 1} ({die.color.value})."
    )
    return controller.get_full_state()



def hotfix_reroll(controller: GameController, player_id: int, die_index: int) -> Dict[str, Any]:
    """Spends 1 🔧 token to reroll any 1 rolled die before committing defenses."""
    if controller.phase != 1:
        raise ValueError(f"Cannot hotfix reroll in phase {controller.phase}")
    if player_id not in controller.player_meta:
        raise ValueError(f"Invalid player_id {player_id}")

    meta = controller.player_meta[player_id]
    player = controller.state.players[player_id]

    if player.is_patient_zero:
        raise ValueError(f"Player {player_id} is eliminated")
    if not meta["has_rolled"]:
        raise ValueError("Must roll ready pool before using hotfix rerolls")
    if meta["has_committed"]:
        raise ValueError("Cannot reroll dice after committing defenses")

    rolled = meta["rolled_pool"]
    if not (0 <= die_index < len(rolled)):
        raise ValueError(f"Invalid die_index {die_index}. Rolled pool size: {len(rolled)}")

    locked = set(meta.get("locked_reroll_indices", []))
    if die_index in locked:
        raise ValueError(f"Die #{die_index + 1} is locked (its patch output was spent for a hotfix) and cannot be rerolled")

    # Available patch tokens = player.patches + any patches showing on kept unlocked rolled dice minus spent_from_kept
    kept_rolled_patches = sum(
        d.current_face.patches
        for i, d in enumerate(rolled)
        if i != die_index and i not in locked and d.current_face
    )
    spent_from_kept = meta.get("spent_from_kept", 0)
    available_kept = max(0, kept_rolled_patches - spent_from_kept)
    total_available = player.patches + available_kept

    if total_available < 1:
        raise ValueError(f"Not enough patch tokens (🔧). Available: {total_available}")

    # Spend 1 patch: prefer spending from held tokens first
    if player.patches > 0:
        player.patches -= 1
    else:
        spend_idx = None
        for i, d in enumerate(rolled):
            if i != die_index and i not in locked and d.current_face and d.current_face.patches > 0:
                spend_idx = i
                break
        if spend_idx is not None:
            meta.setdefault("locked_reroll_indices", []).append(spend_idx)
        meta["spent_from_kept"] = spent_from_kept + 1

    # Reroll the specified die
    die_to_reroll = rolled[die_index]
    new_face = die_to_reroll.roll(controller.engine.rng)

    controller.event_log.append(
        f"{meta['name']} spent 1 🔧 to hotfix reroll die #{die_index + 1} ({die_to_reroll.color.value.capitalize()}) -> rolled '{new_face.name}'."
    )
    return controller.get_full_state()



def commit_defenses(
    controller: GameController,
    player_id: int,
    commitments: Dict[int, ShieldColor | str],
    choice_declarations: Optional[Dict[int, int]] = None,
) -> Dict[str, Any]:
    """Commits rolled shield dice to Red, Blue, or Green shield slots and sets choice branches."""
    if controller.phase != 1:
        raise ValueError(f"Cannot commit defenses in phase {controller.phase}")
    if player_id not in controller.player_meta:
        raise ValueError(f"Invalid player_id {player_id}")

    meta = controller.player_meta[player_id]
    player = controller.state.players[player_id]

    if player.is_patient_zero:
        raise ValueError(f"Player {player_id} is eliminated")
    if not meta["has_rolled"]:
        raise ValueError("Must roll ready pool before committing defenses")
    if meta["has_committed"]:
        raise ValueError("Defenses have already been committed this round")

    rolled = meta["rolled_pool"]
    choice_decls: Dict[int, int] = {}
    if choice_declarations:
        for k, v in choice_declarations.items():
            try:
                choice_decls[int(k)] = int(v)
            except (ValueError, TypeError):
                pass

    validated_commitments: Dict[int, ShieldColor] = {}

    # Validate commitments
    for idx_str, color_str in commitments.items():
        idx = int(idx_str)
        if not (0 <= idx < len(rolled)):
            raise ValueError(f"Invalid die index {idx} in commitments")

        die = rolled[idx]
        face = die.current_face
        if not face or face.is_glitch:
            raise ValueError(f"Die #{idx + 1} ({die.color.value}) cannot be committed ({face.name if face else 'None'})")

        shield_target = ShieldColor(color_str.lower())
        if shield_target not in (ShieldColor.RED, ShieldColor.BLUE, ShieldColor.GREEN):
            raise ValueError(f"Shield target must be red, blue, or green, got {color_str}")

        if face.is_shield:
            if face.shield_color == ShieldColor.ANY:
                validated_commitments[idx] = shield_target
            elif face.shield_color in (ShieldColor.RED, ShieldColor.BLUE, ShieldColor.GREEN):
                # Fixed colored shields must commit to their color
                validated_commitments[idx] = face.shield_color
        elif face.has_shield_option:
            if shield_target == ShieldColor.BLUE:
                validated_commitments[idx] = ShieldColor.BLUE
                die.chosen_choice_index = 0
            else:
                raise ValueError(f"Die #{idx + 1} ({die.color.value}) can only block Blue, got {color_str}")
        else:
            raise ValueError(f"Die #{idx + 1} ({die.color.value}) is not a shield die ({face.name})")

    # Auto-assign any unassigned fixed colored shields (excluding B2, and excluding choice faces)
    for idx, die in enumerate(rolled):
        face = die.current_face
        if face and face.is_shield and not face.is_choice and idx not in validated_commitments:
            if face.shield_color in (ShieldColor.RED, ShieldColor.BLUE, ShieldColor.GREEN) and face.star_code != "B2":
                validated_commitments[idx] = face.shield_color

    # Sync choice faces
    for idx, die in enumerate(rolled):
        face = die.current_face
        if face and face.is_choice:
            if face.has_shield_option:
                if idx in validated_commitments and validated_commitments[idx] == ShieldColor.BLUE:
                    die.chosen_choice_index = 0
                else:
                    die.chosen_choice_index = 1
            else:
                chosen = choice_decls.get(idx, 0)
                if not (0 <= chosen < len(face.choices)):
                    chosen = 0
                die.chosen_choice_index = chosen

    # Collect resource outputs on effective faces (RULES.md v0.8 Phase 1 Step 6)
    demoted_or_sacrificed_ids: set[int] = set()
    for idx, die in enumerate(rolled):
        face = die.current_face
        if not face or face.is_glitch:
            continue

        if idx not in validated_commitments:
            eff = die.effective_face
            if eff:
                player.money += eff.money
                player.patches += eff.patches
                player.secrets += eff.secrets
                if eff.is_star:
                    if eff.star_code == "Y2":
                        distinct_count = len({d.color for d in player.colored_dice})
                        total_payout = min(controller.state.config.y2_max_payout, controller.state.config.y2_base_payout + distinct_count)
                        bonus = total_payout - eff.money
                        player.money += max(0, bonus)
                    elif eff.star_code == "Y3":
                        if die in player.ready_dice:
                            player.ready_dice.remove(die)
                            player.unpatched_dice.append(die)
                            demoted_or_sacrificed_ids.add(die.die_id)
        else:
            # Assigned to defense: hybrid star boot outputs
            if face.is_star:
                if face.star_code == "R1":
                    player.money += 2
                elif face.star_code in ("G1", "G2"):
                    player.patches += 1

    spent_from_kept = meta.get("spent_from_kept", 0)
    player.patches = max(0, player.patches - spent_from_kept)
    player.patches = min(player.patches, controller.state.config.max_patch_tokens)

    # Cryptographic Hash Match (RULES.md v0.17.0 Baseline)
    hash_secrets = detect_hash_matches(rolled)
    if hash_secrets > 0:
        player.secrets += hash_secrets
        player.hash_matches_secrets = getattr(player, "hash_matches_secrets", 0) + hash_secrets
        controller.event_log.append(
            f"{meta['name']} triggered Cryptographic Hash Match (+{hash_secrets} Corporate Secret{'s' if hash_secrets > 1 else ''})!"
        )

    # Glitch Backlash Routine (RULES.md v0.12.0)
    unresolved_glitches = [
        d for d in rolled
        if d.current_face and d.current_face.is_glitch
    ]
    for g_die in unresolved_glitches:
        chosen = player.bot.choose_glitch_demotion(
            player_state=player,
            glitch_die=g_die,
            active_dice=rolled,
            validated_commitments=validated_commitments,
            rng=controller.engine.rng,
        )
        if chosen and (chosen in player.contractor_dice or chosen.color == DieColor.WHITE):
            if chosen in player.contractor_dice:
                player.contractor_dice.remove(chosen)
            elif player.contractor_dice:
                chosen = player.contractor_dice.pop(0)
            controller.state.contractor_supply += 1
            player.hired_contractor_count = max(0, len(player.contractor_dice))
            meta["hired_contractors"] = len(player.contractor_dice)
            demoted_or_sacrificed_ids.add(chosen.die_id)
            if chosen in rolled:
                c_idx = rolled.index(chosen)
                if c_idx in validated_commitments:
                    del validated_commitments[c_idx]
            controller.event_log.append(
                f"{meta['name']} resolved Glitch Backlash: sacrificed 1 White Contractor die to supply."
            )
        elif chosen and chosen in player.ready_dice:
            player.ready_dice.remove(chosen)
            player.unpatched_dice.append(chosen)
            demoted_or_sacrificed_ids.add(chosen.die_id)
            if chosen in rolled:
                r_idx = rolled.index(chosen)
                if r_idx in validated_commitments:
                    del validated_commitments[r_idx]
            controller.event_log.append(
                f"{meta['name']} resolved Glitch Backlash: demoted {chosen.color.value.capitalize()} die to Unpatched Zone."
            )
        elif player.contractor_dice:
            c_die = player.contractor_dice.pop(0)
            controller.state.contractor_supply += 1
            player.hired_contractor_count = max(0, len(player.contractor_dice))
            meta["hired_contractors"] = len(player.contractor_dice)
            demoted_or_sacrificed_ids.add(c_die.die_id)
            if c_die in rolled:
                c_idx = rolled.index(c_die)
                if c_idx in validated_commitments:
                    del validated_commitments[c_idx]
            controller.event_log.append(
                f"{meta['name']} resolved Glitch Backlash: sacrificed 1 White Contractor die to supply."
            )
        elif player.ready_dice:
            uncommitted = [
                d for d in player.ready_dice
                if d in rolled and rolled.index(d) not in validated_commitments
            ]
            candidates = uncommitted if uncommitted else list(player.ready_dice)
            target = min(
                candidates,
                key=lambda d: (0 if d.color == DieColor.GRAY else 1, getattr(d, "vp", 0), getattr(d, "cost", 0)),
            )
            player.ready_dice.remove(target)
            player.unpatched_dice.append(target)
            demoted_or_sacrificed_ids.add(target.die_id)
            if target in rolled:
                t_idx = rolled.index(target)
                if t_idx in validated_commitments:
                    del validated_commitments[t_idx]
            controller.event_log.append(
                f"{meta['name']} resolved Glitch Backlash: demoted {target.color.value.capitalize()} die to Unpatched Zone."
            )

    # Track star ability eligibility for Phase 3
    for idx, die in enumerate(rolled):
        if die.die_id in demoted_or_sacrificed_ids:
            continue
        face = die.current_face
        if not face or not face.is_star:
            continue
        if face.star_code == "B2":
            if idx not in validated_commitments:
                player.b2_available = True
        elif face.star_code == "Y1":
            player.y1_available = True
        elif face.star_code == "P1":
            player.p1_available = True
        elif face.star_code == "P3":
            if idx in validated_commitments:
                player.p3_available = validated_commitments[idx]

    # Filter out sacrificed contractor dice and demoted dice from rolled_pool and re-index commitments
    new_rolled: List[Die] = []
    new_commitments: Dict[int, str] = {}
    slots: Dict[str, List[Die]] = {"red": [], "blue": [], "green": []}
    for old_idx, die in enumerate(rolled):
        if die.die_id in demoted_or_sacrificed_ids:
            continue
        new_idx = len(new_rolled)
        new_rolled.append(die)
        if old_idx in validated_commitments:
            color = validated_commitments[old_idx]
            new_commitments[new_idx] = color.value
            slots[color.value].append(die)

    meta["rolled_pool"] = new_rolled
    meta["commitments"] = new_commitments
    meta["has_committed"] = True
    meta["shield_slots"] = slots

    shield_summary = [f"{len(slots[c])} {c.capitalize()}" for c in ["red", "blue", "green"] if slots[c]]
    controller.event_log.append(
        f"{meta['name']} committed shields: {', '.join(shield_summary) if shield_summary else 'No shields'}."
    )

    # Check if all human players have committed
    all_humans_committed = all(
        m["has_committed"]
        for pid, m in controller.player_meta.items()
        if m["is_human"] and not controller.state.players[pid].is_patient_zero
    )

    if all_humans_committed:
        # Auto-execute Phase 1 for all bot players
        auto_execute_bots_phase_1(controller)

        # Advance to Phase 2
        controller.phase = 2
        controller.phase_name = "Rogue Agent Compile"
        controller.subphase = "ready_for_compile"
        controller.event_log.append("All corporations have committed defenses. Ready for Compile Drop.")

    return controller.get_full_state()



def auto_execute_bots_phase_1(controller: GameController) -> None:
    """Runs Phase 1 contractor hiring, roll, Yahtzee rerolls/debug, and defense commitments for bot players."""
    staging_copy = dict(controller.state.staging_cup)
    stuck_copy = controller.state.tower.get_stuck_copy()

    for pid, player in enumerate(controller.state.players):
        meta = controller.player_meta[pid]
        if meta["is_human"] or player.is_patient_zero:
            continue

        # 1. Temp Staffing (Contractor Hiring)
        active_ver = controller.state.active_version.version_str
        used_operator = False
        if (
            player.archetype is not None
            and player.archetype.code == ArchetypeCode.OPERATOR
            and player.is_ability_available(active_ver)
        ):
            use_op = player.bot.choose_operator_ability(
                player_state=player,
                contractor_supply=controller.state.contractor_supply,
                staging_cubes=staging_copy,
                stuck_cubes=stuck_copy,
                rng=controller.engine.rng,
                corruption_track=controller.state.corruption_track,
            )
            if use_op:
                free_hire = min(2, controller.state.contractor_supply)
                controller.state.contractor_supply -= free_hire
                player.hired_contractor_count += free_hire
                player.total_contractors_hired += free_hire
                meta["hired_contractors"] = player.hired_contractor_count
                for _ in range(free_hire):
                    c_die = create_white_die(controller.state.next_die_id)
                    controller.state.next_die_id += 1
                    player.contractor_dice.append(c_die)
                player.mark_ability_used(active_ver)
                used_operator = True

                # Option to buy 3rd die (progressive 3rd contractor cost, e.g. $3)
                cost = controller.state.config.get_contractor_cost_for_hire(1, already_hired=free_hire)
                if controller.state.contractor_supply > 0 and player.money >= cost:
                    buy_3rd = player.bot.choose_operator_buy_third_die(
                        player_state=player,
                        contractor_supply=controller.state.contractor_supply,
                        staging_cubes=staging_copy,
                        stuck_cubes=stuck_copy,
                        rng=controller.engine.rng,
                        corruption_track=controller.state.corruption_track,
                    )
                    if buy_3rd:
                        player.money -= cost
                        controller.state.contractor_supply -= 1
                        player.hired_contractor_count += 1
                        player.total_contractors_hired += 1
                        meta["hired_contractors"] = player.hired_contractor_count
                        c_die = create_white_die(controller.state.next_die_id)
                        controller.state.next_die_id += 1
                        player.contractor_dice.append(c_die)

        if not used_operator:
            max_hire = controller.state.config.get_max_affordable_contractors(
                money=player.money,
                already_hired=player.hired_contractor_count,
                supply=controller.state.contractor_supply,
            )
            desired_hire = player.bot.choose_contractor_hires(
                player_state=player,
                contractor_supply=controller.state.contractor_supply,
                staging_cubes=staging_copy,
                stuck_cubes=stuck_copy,
                rng=controller.engine.rng,
            )
            actual_hire = max(0, min(desired_hire, max_hire))
            if actual_hire > 0:
                cost = controller.state.config.get_contractor_cost_for_hire(
                    actual_hire, already_hired=player.hired_contractor_count
                )
                player.money -= cost
                controller.state.contractor_supply -= actual_hire
                player.hired_contractor_count += actual_hire
                player.total_contractors_hired += actual_hire
                meta["hired_contractors"] = player.hired_contractor_count
                for _ in range(actual_hire):
                    c_die = create_white_die(controller.state.next_die_id)
                    controller.state.next_die_id += 1
                    player.contractor_dice.append(c_die)

        # 2. Roll Active Pool
        active_dice: List[Die] = list(player.ready_dice) + list(player.contractor_dice)
        for die in active_dice:
            die.is_locked = False
            die.roll(controller.engine.rng)

        # 3. Yahtzee Rerolls & Lock Resolution
        active_directive = controller.state.active_directive_code
        max_free_rerolls = controller.state.config.default_free_rerolls

        is_prodigy = (
            player.archetype is not None
            and player.archetype.code == ArchetypeCode.PRODIGY
            and player.is_ability_available(active_ver)
        )
        prodigy_active = False
        if is_prodigy:
            use_prodigy = player.bot.choose_prodigy_ability(
                player_state=player,
                active_dice=active_dice,
                rerolls_remaining=max_free_rerolls,
                staging_cubes=staging_copy,
                stuck_cubes=stuck_copy,
                directive_code=active_directive,
                rng=controller.engine.rng,
                corruption_track=controller.state.corruption_track,
            )
            if use_prodigy:
                prodigy_active = True
                player.mark_ability_used(active_ver)

        def _eval_locks(dice_list: List[Die]) -> None:
            for d in dice_list:
                face = d.current_face
                if not face:
                    continue
                if face.is_glitch:
                    d.is_locked = True
                elif "CASH" in controller.state.active_phase1_locks and face.has_cash_option:
                    d.is_locked = True
                elif "PATCH" in controller.state.active_phase1_locks and face.has_patch_option:
                    d.is_locked = True
                elif "SHIELD" in controller.state.active_phase1_locks and face.has_shield_option:
                    d.is_locked = True

        _eval_locks(active_dice)

        rerolls_remaining = max_free_rerolls
        while rerolls_remaining > 0:
            if player.patches > 0:
                unlock_indices = player.bot.choose_debug_unlocks(
                    player_state=player,
                    active_dice=active_dice,
                    staging_cubes=staging_copy,
                    stuck_cubes=stuck_copy,
                    directive_code=active_directive,
                    rng=controller.engine.rng,
                )
                for u_idx in unlock_indices:
                    if player.patches <= 0:
                        break
                    if 0 <= u_idx < len(active_dice) and active_dice[u_idx].is_locked:
                        active_dice[u_idx].is_locked = False
                        player.patches -= 1

            reroll_indices = player.bot.choose_yahtzee_rerolls(
                player_state=player,
                active_dice=active_dice,
                rerolls_remaining=rerolls_remaining,
                staging_cubes=staging_copy,
                stuck_cubes=stuck_copy,
                directive_code=active_directive,
                rng=controller.engine.rng,
            )
            valid_rerolls = [
                idx for idx in reroll_indices
                if 0 <= idx < len(active_dice) and (prodigy_active or not active_dice[idx].is_locked)
            ]
            if not valid_rerolls:
                break

            for r_idx in valid_rerolls:
                active_dice[r_idx].roll(controller.engine.rng)
                active_dice[r_idx].is_locked = False

            _eval_locks(active_dice)
            player.total_rerolls_used += 1
            rerolls_remaining -= 1

        _eval_locks(active_dice)

        # 5. Assign Defenses & Declare Choices (RULES.md v0.8)
        declared_choices = player.bot.declare_choices(
            player_state=player,
            active_dice=active_dice,
            staging_cubes=staging_copy,
            stuck_cubes=stuck_copy,
            directive_code=active_directive,
            rng=controller.engine.rng,
        )
        commitments = player.bot.commit_shields(
            player_state=player,
            rolled_dice=active_dice,
            staging_cubes=staging_copy,
            stuck_cubes=stuck_copy,
            directive_code=active_directive,
            rng=controller.engine.rng,
        )
        validated: Dict[int, ShieldColor] = {}
        for idx, die in enumerate(active_dice):
            face = die.current_face
            if not face or face.is_glitch:
                continue

            if face.is_choice:
                if face.has_shield_option:
                    if idx in commitments and commitments[idx] == ShieldColor.BLUE:
                        validated[idx] = ShieldColor.BLUE
                        die.chosen_choice_index = 0
                    else:
                        die.chosen_choice_index = 1
                else:
                    chosen = declared_choices.get(idx, 0) if declared_choices else 0
                    if not (0 <= chosen < len(face.choices)):
                        chosen = 0
                    die.chosen_choice_index = chosen

            elif face.is_shield:
                if idx in commitments:
                    c = commitments[idx]
                    validated[idx] = c if c in (ShieldColor.RED, ShieldColor.BLUE, ShieldColor.GREEN) else ShieldColor.BLUE
                elif face.shield_color in (ShieldColor.RED, ShieldColor.BLUE, ShieldColor.GREEN):
                    if face.star_code != "B2":
                        validated[idx] = face.shield_color
                elif face.shield_color == ShieldColor.ANY:
                    validated[idx] = ShieldColor.BLUE

        # 6. Gain Resource Outputs on Effective Faces (RULES.md v0.8)
        demoted_or_sacrificed_ids: set[int] = set()
        for idx, die in enumerate(active_dice):
            face = die.current_face
            if not face or face.is_glitch:
                continue

            if idx not in validated:
                eff = die.effective_face
                if eff:
                    player.money += eff.money
                    player.patches += eff.patches
                    player.secrets += eff.secrets
                    if eff.is_star:
                        if eff.star_code == "Y2":
                            distinct_count = len({d.color for d in player.colored_dice})
                            total_payout = min(controller.state.config.y2_max_payout, controller.state.config.y2_base_payout + distinct_count)
                            bonus = total_payout - eff.money
                            player.money += max(0, bonus)
                        elif eff.star_code == "Y3":
                            if die in player.ready_dice:
                                player.ready_dice.remove(die)
                                player.unpatched_dice.append(die)
                                demoted_or_sacrificed_ids.add(die.die_id)
            else:
                if face.is_star:
                    if face.star_code == "R1":
                        player.money += 2
                    elif face.star_code in ("G1", "G2"):
                        player.patches += 1

        player.patches = min(player.patches, controller.state.config.max_patch_tokens)

        # Cryptographic Hash Match (RULES.md v0.17.0 Baseline)
        hash_secrets = detect_hash_matches(active_dice)
        if hash_secrets > 0:
            player.secrets += hash_secrets
            player.hash_matches_secrets = getattr(player, "hash_matches_secrets", 0) + hash_secrets
            controller.event_log.append(
                f"{meta['name']} triggered Cryptographic Hash Match (+{hash_secrets} Corporate Secret{'s' if hash_secrets > 1 else ''})!"
            )

        # Glitch Backlash Routine (RULES.md v0.12.0)
        unresolved_glitches = [
            d for d in active_dice
            if d.current_face and d.current_face.is_glitch
        ]
        for g_die in unresolved_glitches:
            chosen = player.bot.choose_glitch_demotion(
                player_state=player,
                glitch_die=g_die,
                active_dice=active_dice,
                validated_commitments=validated,
                rng=controller.engine.rng,
            )
            if chosen and (chosen in player.contractor_dice or chosen.color == DieColor.WHITE):
                if chosen in player.contractor_dice:
                    player.contractor_dice.remove(chosen)
                elif player.contractor_dice:
                    chosen = player.contractor_dice.pop(0)
                controller.state.contractor_supply += 1
                player.hired_contractor_count = max(0, len(player.contractor_dice))
                meta["hired_contractors"] = len(player.contractor_dice)
                demoted_or_sacrificed_ids.add(chosen.die_id)
                if chosen in active_dice:
                    c_idx = active_dice.index(chosen)
                    if c_idx in validated:
                        del validated[c_idx]
                controller.event_log.append(
                    f"{meta['name']} resolved Glitch Backlash: sacrificed 1 White Contractor die to supply."
                )
            elif chosen and chosen in player.ready_dice:
                player.ready_dice.remove(chosen)
                player.unpatched_dice.append(chosen)
                demoted_or_sacrificed_ids.add(chosen.die_id)
                if chosen in active_dice:
                    r_idx = active_dice.index(chosen)
                    if r_idx in validated:
                        del validated[r_idx]
                controller.event_log.append(
                    f"{meta['name']} resolved Glitch Backlash: demoted {chosen.color.value.capitalize()} die to Unpatched Zone."
                )
            elif player.contractor_dice:
                c_die = player.contractor_dice.pop(0)
                controller.state.contractor_supply += 1
                player.hired_contractor_count = max(0, len(player.contractor_dice))
                meta["hired_contractors"] = len(player.contractor_dice)
                demoted_or_sacrificed_ids.add(c_die.die_id)
                if c_die in active_dice:
                    c_idx = active_dice.index(c_die)
                    if c_idx in validated:
                        del validated[c_idx]
                controller.event_log.append(
                    f"{meta['name']} resolved Glitch Backlash: sacrificed 1 White Contractor die to supply."
                )
            elif player.ready_dice:
                uncommitted = [
                    d for d in player.ready_dice
                    if d in active_dice and active_dice.index(d) not in validated
                ]
                candidates = uncommitted if uncommitted else list(player.ready_dice)
                target = min(
                    candidates,
                    key=lambda d: (0 if d.color == DieColor.GRAY else 1, getattr(d, "vp", 0), getattr(d, "cost", 0)),
                )
                player.ready_dice.remove(target)
                player.unpatched_dice.append(target)
                demoted_or_sacrificed_ids.add(target.die_id)
                if target in active_dice:
                    t_idx = active_dice.index(target)
                    if t_idx in validated:
                        del validated[t_idx]
                controller.event_log.append(
                    f"{meta['name']} resolved Glitch Backlash: demoted {target.color.value.capitalize()} die to Unpatched Zone."
                )

        # Track Star availability
        for idx, die in enumerate(active_dice):
            if die.die_id in demoted_or_sacrificed_ids:
                continue
            face = die.current_face
            if not face or not face.is_star:
                continue
            if face.star_code == "B2":
                if idx not in validated:
                    player.b2_available = True
            elif face.star_code == "Y1":
                player.y1_available = True
            elif face.star_code == "P1":
                player.p1_available = True
            elif face.star_code == "P3":
                if idx in validated:
                    player.p3_available = validated[idx]

        new_rolled: List[Die] = []
        new_commitments: Dict[int, str] = {}
        slots: Dict[str, List[Die]] = {"red": [], "blue": [], "green": []}
        for old_idx, die in enumerate(active_dice):
            if die.die_id in demoted_or_sacrificed_ids:
                continue
            new_idx = len(new_rolled)
            new_rolled.append(die)
            if old_idx in validated:
                color = validated[old_idx]
                new_commitments[new_idx] = color.value
                slots[color.value].append(die)

        meta["rolled_pool"] = new_rolled
        meta["commitments"] = new_commitments
        meta["has_rolled"] = True
        meta["has_committed"] = True
        meta["shield_slots"] = slots

# =========================================================================
# Phase 2: Rogue Agent Compile (The Cube Tower Drop)
# =========================================================================

