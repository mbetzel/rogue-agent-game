"""Phase 1: Boot & Configure (Simultaneous) mechanics."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from sim.config import CubeColor, DieColor, ShieldColor
from sim.entities import ArchetypeCode, Die, Face, create_white_die

if TYPE_CHECKING:
    from sim.engine.core import GameEngine
    from sim.engine.state import PlayerState


def get_face_signature(face: Optional[Face]) -> Optional[Tuple]:
    """Returns a hashable signature representing the printed output of a face.

    Glitches return None and can never form Hash Matches.
    """
    if face is None or face.is_glitch:
        return None
    return (
        face.name,
        face.block_amount,
        face.shield_color,
        face.money,
        face.patches,
        face.secrets,
        face.is_star,
        face.star_code,
    )


def detect_hash_matches(dice: List[Die]) -> int:
    """Calculates Corporate Secrets gained from Cryptographic Hash Matches (triplets).

    For every set of 3 dice showing the exact same printed output (excluding Glitches),
    the player gains +1 Corporate Secret (uncapped). Choice faces match their declared option.
    """
    counts: Dict[Tuple, int] = {}
    for d in dice:
        eff = d.effective_face
        sig = get_face_signature(eff)
        if sig is not None:
            counts[sig] = counts.get(sig, 0) + 1

    secrets_gained = 0
    for count in counts.values():
        secrets_gained += count // 3
    return secrets_gained


def execute_phase_1(engine: GameEngine) -> List[Tuple[PlayerState, List[Die], Dict[int, ShieldColor]]]:
    # Promote pending next-phase locks from previous Phase 2 to active locks for this Phase 1
    engine.state.active_phase1_locks = set(engine.state.pending_next_phase_locks)
    engine.state.pending_next_phase_locks.clear()

    # 1. Autonomous AI Corruption Pulse (v0.16.0: 1 in v1.0, 2 in v2.0, 2 in v3.0)
    active_ver = engine.state.active_version.version_str if engine.state.active_version else "v1.0"
    pulse_count = engine.state.config.autonomous_pulse_by_version.get(active_ver, 1)
    engine.state.staging_cup[CubeColor.BLACK] = (
        engine.state.staging_cup.get(CubeColor.BLACK, 0) + pulse_count
    )

    player_commitments: List[Tuple[PlayerState, List[Die], Dict[int, ShieldColor]]] = []

    staging_copy = dict(engine.state.staging_cup)
    stuck_copy = engine.state.tower.get_stuck_copy()

    # 2. Temp Staffing (Contractor Hiring)
    active_ver = engine.state.active_version.version_str
    for player in engine.state.players:
        if player.is_patient_zero:
            continue

        if not player.contractor_dice:
            player.contractor_dice = []
            player.hired_contractor_count = 0

        # Hook Phase 1 Step 2: The Operator (Redundant Crew)
        is_operator = (
            player.archetype is not None
            and player.archetype.code == ArchetypeCode.OPERATOR
            and player.is_ability_available(active_ver)
        )
        used_operator = False
        if is_operator:
            use_op = player.bot.choose_operator_ability(
                player_state=player,
                contractor_supply=engine.state.contractor_supply,
                staging_cubes=staging_copy,
                stuck_cubes=stuck_copy,
                rng=engine.rng,
                corruption_track=engine.state.corruption_track,
            )
            if use_op and engine.state.contractor_supply > 0:
                free_hire = min(2, engine.state.contractor_supply)
                engine.state.contractor_supply -= free_hire
                player.hired_contractor_count += free_hire
                player.total_contractors_hired += free_hire
                for _ in range(free_hire):
                    c_die = create_white_die(engine.state.next_die_id)
                    engine.state.next_die_id += 1
                    player.contractor_dice.append(c_die)
                player.mark_ability_used(active_ver)
                used_operator = True

                # Option to buy 3rd die (progressive 3rd contractor cost, e.g. $3)
                cost = engine.config.get_contractor_cost_for_hire(1, already_hired=free_hire)
                if engine.state.contractor_supply > 0 and player.money >= cost:
                    buy_3rd = player.bot.choose_operator_buy_third_die(
                        player_state=player,
                        contractor_supply=engine.state.contractor_supply,
                        staging_cubes=staging_copy,
                        stuck_cubes=stuck_copy,
                        rng=engine.rng,
                        corruption_track=engine.state.corruption_track,
                    )
                    if buy_3rd:
                        player.money -= cost
                        engine.state.contractor_supply -= 1
                        player.hired_contractor_count += 1
                        player.total_contractors_hired += 1
                        c_die = create_white_die(engine.state.next_die_id)
                        engine.state.next_die_id += 1
                        player.contractor_dice.append(c_die)

        if not used_operator:
            max_hire = engine.config.get_max_affordable_contractors(
                money=player.money,
                already_hired=player.hired_contractor_count,
                supply=engine.state.contractor_supply,
            )
            desired_hire = player.bot.choose_contractor_hires(
                player_state=player,
                contractor_supply=engine.state.contractor_supply,
                staging_cubes=staging_copy,
                stuck_cubes=stuck_copy,
                rng=engine.rng,
            )
            actual_hire = max(0, min(desired_hire, max_hire))
            if actual_hire > 0:
                cost = engine.config.get_contractor_cost_for_hire(
                    actual_hire, already_hired=player.hired_contractor_count
                )
                player.money -= cost
                engine.state.contractor_supply -= actual_hire
                player.hired_contractor_count += actual_hire
                player.total_contractors_hired += actual_hire
                for _ in range(actual_hire):
                    c_die = create_white_die(engine.state.next_die_id)
                    engine.state.next_die_id += 1
                    player.contractor_dice.append(c_die)

    # 3. Roll Active Pool, Yahtzee Rerolls, Outputs, Commit Defenses
    for player in engine.state.players:
        if player.is_patient_zero:
            continue

        # Reset round star availability
        player.b2_available = False
        player.y1_available = False
        player.p1_available = False
        player.p3_available = None

        # Roll Active Pool (ready_dice + contractor_dice)
        active_dice: List[Die] = list(player.ready_dice) + list(player.contractor_dice)
        for die in active_dice:
            die.is_locked = False
            res_face = die.roll(engine.rng)
            if res_face and die.current_face != res_face:
                die.current_face = res_face

        # 4. Lock Evaluation & Yahtzee Rerolls Loop
        active_directive = engine.state.active_directive_code
        max_free_rerolls = engine.config.default_free_rerolls

        def _evaluate_locks(dice_list: List[Die]) -> None:
            for d in dice_list:
                face = d.current_face
                if not face:
                    continue
                if face.is_glitch:
                    d.is_locked = True
                elif "CASH" in engine.state.active_phase1_locks and face.has_cash_option:
                    d.is_locked = True
                elif "PATCH" in engine.state.active_phase1_locks and face.has_patch_option:
                    d.is_locked = True
                elif "SHIELD" in engine.state.active_phase1_locks and face.has_shield_option:
                    d.is_locked = True

        _evaluate_locks(active_dice)

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
                rng=engine.rng,
                corruption_track=engine.state.corruption_track,
            )
            if use_prodigy:
                prodigy_active = True
                player.mark_ability_used(active_ver)

        rerolls_remaining = max_free_rerolls
        while rerolls_remaining > 0:
            # Debug action: spend 1 🔧 to unlock 1 locked die
            if player.patches > 0:
                unlock_indices = player.bot.choose_debug_unlocks(
                    player_state=player,
                    active_dice=active_dice,
                    staging_cubes=staging_copy,
                    stuck_cubes=stuck_copy,
                    directive_code=active_directive,
                    rng=engine.rng,
                )
                for u_idx in unlock_indices:
                    if player.patches <= 0:
                        break
                    if 0 <= u_idx < len(active_dice) and active_dice[u_idx].is_locked:
                        active_dice[u_idx].is_locked = False
                        player.patches -= 1

            # Choose rerolls among unlocked dice (or any dice if prodigy_active)
            reroll_res = player.bot.choose_yahtzee_rerolls(
                player_state=player,
                active_dice=active_dice,
                rerolls_remaining=rerolls_remaining,
                staging_cubes=staging_copy,
                stuck_cubes=stuck_copy,
                directive_code=active_directive,
                rng=engine.rng,
            )
            if isinstance(reroll_res, tuple) and len(reroll_res) == 2:
                extra_unlocks, reroll_indices = reroll_res
                for u_idx in extra_unlocks:
                    if player.patches <= 0:
                        break
                    if 0 <= u_idx < len(active_dice) and active_dice[u_idx].is_locked:
                        active_dice[u_idx].is_locked = False
                        player.patches -= 1
            else:
                reroll_indices = reroll_res or []

            if prodigy_active:
                valid_rerolls = [
                    idx for idx in reroll_indices
                    if 0 <= idx < len(active_dice)
                ]
            else:
                valid_rerolls = [
                    idx for idx in reroll_indices
                    if 0 <= idx < len(active_dice) and not active_dice[idx].is_locked
                ]
            if not valid_rerolls:
                break

            for r_idx in valid_rerolls:
                res_face = active_dice[r_idx].roll(engine.rng)
                if res_face and active_dice[r_idx].current_face != res_face:
                    active_dice[r_idx].current_face = res_face
                active_dice[r_idx].is_locked = False

            _evaluate_locks(active_dice)
            player.total_rerolls_used += 1
            rerolls_remaining -= 1

        # Prodigy face override (RULES.md v0.13.0)
        if prodigy_active:
            override = player.bot.choose_prodigy_face_override(
                player_state=player,
                active_dice=active_dice,
                staging_cubes=staging_copy,
                stuck_cubes=stuck_copy,
                directive_code=active_directive,
                rng=engine.rng,
            )
            if override:
                die_idx, target_face = override
                if 0 <= die_idx < len(active_dice) and not target_face.is_star:
                    active_dice[die_idx].current_face = target_face
                    active_dice[die_idx].is_locked = False
                    active_dice[die_idx].chosen_choice_index = None

        # Final lock evaluation pass
        _evaluate_locks(active_dice)

        # 5. Assign Defenses & Declare Choices (RULES.md v0.8)
        declared_choices = player.bot.declare_choices(
            player_state=player,
            active_dice=active_dice,
            staging_cubes=staging_copy,
            stuck_cubes=stuck_copy,
            directive_code=active_directive,
            rng=engine.rng,
        )
        shield_commitments = player.bot.commit_shields(
            player_state=player,
            rolled_dice=active_dice,
            staging_cubes=staging_copy,
            stuck_cubes=stuck_copy,
            directive_code=active_directive,
            rng=engine.rng,
        )

        # Validate assignments & sync die.chosen_choice_index
        validated_commitments: Dict[int, ShieldColor] = {}
        for idx, die in enumerate(active_dice):
            face = die.current_face
            if not face or face.is_glitch:
                continue

            if face.is_choice:
                if face.has_shield_option:
                    # Blue Face 4: if committed to Blue shield, choice 0; if not, choice 1
                    if idx in shield_commitments and shield_commitments[idx] == ShieldColor.BLUE:
                        validated_commitments[idx] = ShieldColor.BLUE
                        die.chosen_choice_index = 0
                    else:
                        die.chosen_choice_index = 1
                else:
                    # Gray or Green choice face: use declared choice index or default 0
                    chosen = declared_choices.get(idx, 0) if declared_choices else 0
                    if not (0 <= chosen < len(face.choices)):
                        chosen = 0
                    die.chosen_choice_index = chosen

            elif face.is_shield:
                if idx in shield_commitments:
                    color = shield_commitments[idx]
                    if face.shield_color == ShieldColor.ANY:
                        validated_commitments[idx] = (
                            color if color in (ShieldColor.RED, ShieldColor.BLUE, ShieldColor.GREEN)
                            else ShieldColor.BLUE
                        )
                    else:
                        validated_commitments[idx] = face.shield_color
                else:
                    if face.shield_color in (ShieldColor.RED, ShieldColor.BLUE, ShieldColor.GREEN):
                        if face.star_code != "B2":
                            validated_commitments[idx] = face.shield_color
                    elif face.shield_color == ShieldColor.ANY:
                        validated_commitments[idx] = ShieldColor.BLUE

        # 6. Gain Resource Outputs on Effective Faces (RULES.md v0.8)
        for idx, die in enumerate(active_dice):
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
                            count = len({d.color for d in player.colored_dice})
                            total_payout = min(engine.config.y2_max_payout, engine.config.y2_base_payout + count)
                            bonus = total_payout - eff.money
                            player.money += max(0, bonus)
                        elif eff.star_code == "Y3":
                            if die in player.ready_dice:
                                player.ready_dice.remove(die)
                                player.unpatched_dice.append(die)
            else:
                # Die is assigned to defense: collect hybrid star boot outputs
                if face.is_star:
                    if face.star_code == "R1":
                        player.money += 2
                    elif face.star_code in ("G1", "G2"):
                        player.patches += 1

            # Track rolled Star abilities for Phase 3 eligibility
            if face.is_star:
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

        # Cryptographic Hash Match (RULES.md v0.17.0 Baseline)
        hash_secrets = detect_hash_matches(active_dice)
        if hash_secrets > 0:
            player.secrets += hash_secrets
            player.hash_matches_secrets += hash_secrets

        # Glitch Backlash Routine (RULES.md v0.12.0)
        # For each unresolved glitch face across active dice:
        unresolved_glitches = [
            d for d in active_dice
            if d.current_face and d.current_face.is_glitch
        ]
        for g_die in unresolved_glitches:
            chosen = player.bot.choose_glitch_demotion(
                player_state=player,
                glitch_die=g_die,
                active_dice=active_dice,
                validated_commitments=validated_commitments,
                rng=engine.rng,
            )
            if chosen and (chosen in player.contractor_dice or chosen.color == DieColor.WHITE):
                if chosen in player.contractor_dice:
                    player.contractor_dice.remove(chosen)
                elif player.contractor_dice:
                    player.contractor_dice.pop(0)
                engine.state.contractor_supply += 1
                if chosen in active_dice:
                    c_idx = active_dice.index(chosen)
                    if c_idx in validated_commitments:
                        del validated_commitments[c_idx]
            elif chosen and chosen in player.ready_dice:
                player.ready_dice.remove(chosen)
                player.unpatched_dice.append(chosen)
                if chosen in active_dice:
                    r_idx = active_dice.index(chosen)
                    if r_idx in validated_commitments:
                        del validated_commitments[r_idx]
            elif player.contractor_dice:
                c_die = player.contractor_dice.pop(0)
                engine.state.contractor_supply += 1
                if c_die in active_dice:
                    c_idx = active_dice.index(c_die)
                    if c_idx in validated_commitments:
                        del validated_commitments[c_idx]
            elif player.ready_dice:
                uncommitted = [
                    d for d in player.ready_dice
                    if d in active_dice and active_dice.index(d) not in validated_commitments
                ]
                candidates = uncommitted if uncommitted else list(player.ready_dice)
                target = min(
                    candidates,
                    key=lambda d: (0 if d.color == DieColor.GRAY else 1, getattr(d, "vp", 0), getattr(d, "cost", 0)),
                )
                player.ready_dice.remove(target)
                player.unpatched_dice.append(target)
                if target in active_dice:
                    t_idx = active_dice.index(target)
                    if t_idx in validated_commitments:
                        del validated_commitments[t_idx]

        player.patches = min(player.patches, engine.config.max_patch_tokens)

        player_commitments.append((player, list(active_dice), validated_commitments))

    engine.state.active_phase1_locks.clear()
    return player_commitments


def apply_single_die_immediate_output(engine: GameEngine, player: PlayerState, die: Die) -> None:
    eff = die.effective_face
    if not eff or eff.is_glitch:
        return

    # Basic money and patches
    player.money += eff.money
    player.patches += eff.patches
    player.secrets += eff.secrets

    # Star faces
    if eff.is_star:
        if eff.star_code == "Y2":
            # Cloud Monopoly: +$2, plus +$1 per different colored module die owned (max +$5)
            count = len({d.color for d in player.colored_dice})
            total_payout = min(engine.config.y2_max_payout, engine.config.y2_base_payout + count)
            bonus = total_payout - eff.money  # base 2 already added in eff.money
            player.money += max(0, bonus)
        elif eff.star_code == "Y3":
            # Proprietary Training: gain 1 secret (already in eff.secrets), move die to unpatched
            if die in player.ready_dice:
                player.ready_dice.remove(die)
                player.unpatched_dice.append(die)



def apply_immediate_face_outputs(engine: GameEngine, player: PlayerState) -> None:
    """Gains immediate money, patches, secrets, and special star activations from rolled faces."""
    for die in list(player.ready_dice) + list(player.contractor_dice):
        apply_single_die_immediate_output(engine, player, die)

