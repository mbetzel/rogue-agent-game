"""Phase 1: Roll & Deploy (Simultaneous) mechanics."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from sim.config import CubeColor, DieColor, ShieldColor
from sim.entities import has_company_override, has_signature_protocol, legacy_bridge_enabled
from sim.entities import ArchetypeCode, CompanyCode, WhiteHatCode, Die, Face, create_white_die
from sim.engine.state import ProductionRole
from sim.engine import research_tracks
from sim.bots import research_policy

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


def detect_hash_matches_with_cipher(
    dice: List[Die],
    is_cipher: bool = False,
) -> int:
    """Calculates Corporate Secrets gained from Cryptographic Hash Matches (triplets).

    For every set of 3 dice showing the exact same printed output (excluding Glitches),
    the player gains +1 Corporate Secret (uncapped). Choice faces match their declared option.

    If is_cipher is True and a Purple die showing PURPLE_STAR is present in dice,
    one Purple Star acts as a wildcard completing any natural pair (count == 2)
    into a 3-of-a-kind triplet.
    """
    counts: Dict[Tuple, int] = {}
    purple_star_wildcards = 0

    for d in dice:
        eff = d.effective_face
        if not eff or eff.is_glitch:
            continue
        if is_cipher and eff.is_star and eff.star_code == "PURPLE_STAR":
            purple_star_wildcards += 1
            continue
        sig = get_face_signature(eff)
        if sig is not None:
            counts[sig] = counts.get(sig, 0) + 1

    secrets_gained = 0
    # Natural triplets
    for sig, count in list(counts.items()):
        secrets_gained += count // 3
        counts[sig] = count % 3

    # Cipher wildcard resolution: completes any natural pair into a triplet
    if is_cipher and purple_star_wildcards > 0:
        for sig, remainder in list(counts.items()):
            if remainder == 2 and purple_star_wildcards > 0:
                secrets_gained += 1
                purple_star_wildcards -= 1
                counts[sig] = 0

    return secrets_gained


def detect_hash_matches(dice: List[Die], is_cipher: bool = False) -> int:
    """Calculates Corporate Secrets gained from triplets (calls detect_hash_matches_with_cipher)."""
    return detect_hash_matches_with_cipher(dice, is_cipher=is_cipher)


def resolve_prodigy_purple_star_override(
    player: PlayerState,
    active_dice: List[Die],
    rng: random.Random,
    target_idx: Optional[int] = None,
    target_face: Optional[Face] = None,
) -> bool:
    """Prodigy Face 6 Protocol (Arbitrary Code Execution):
    Turn any 1 other rolled die to any legal non-Star face of choice.
    """
    purple_star_indices = [
        i for i, d in enumerate(active_dice)
        if d.current_face and d.current_face.is_star and d.current_face.star_code == "PURPLE_STAR"
    ]
    if not purple_star_indices:
        return False

    if target_idx is None or target_face is None:
        choice = player.bot.choose_prodigy_purple_star_override(player, active_dice, rng)
        if choice is not None:
            target_idx, target_face = choice

    if target_idx is not None and target_face is not None:
        if 0 <= target_idx < len(active_dice) and not target_face.is_star:
            if target_idx not in purple_star_indices:
                active_dice[target_idx].current_face = target_face
                active_dice[target_idx].is_locked = False
                active_dice[target_idx].chosen_choice_index = None
                return True
    return False


def check_operator_contingent_staffing(
    engine: GameEngine,
    player: PlayerState,
    active_dice: List[Die],
) -> Optional[Die]:
    """Operator Face 6 Protocol (Contingent Staffing):
    Immediately roll 1 free White Contractor die into rolled pool.
    """
    if engine.state.contractor_supply <= 0:
        return None
    has_purple_star = any(
        d.current_face and d.current_face.is_star and d.current_face.star_code == "PURPLE_STAR"
        for d in active_dice
    )
    if not has_purple_star:
        return None

    engine.state.contractor_supply -= 1
    c_die = create_white_die(engine.state.next_die_id)
    engine.state.next_die_id += 1
    c_die.roll(engine.rng)
    active_dice.append(c_die)
    player.contractor_dice.append(c_die)
    return c_die


def check_and_execute_start_of_round_version_transition(engine: GameEngine) -> bool:
    """Executes pending version switch from previous round's filled track (INV-VER-SWITCH-01)."""
    if not engine.state.pending_version_advance:
        return False

    old_version_str = engine.state.active_version.version_str
    engine.state.current_version_index += 1
    new_version_str = engine.state.active_version.version_str

    # Forfeit unused old ability, unlock new ability
    for p in engine.state.players:
        p.mark_ability_forfeited(old_version_str)
        p.unlock_version_ability(new_version_str)

    # Add new version staging payload to staging cup
    new_version = engine.state.active_version
    for color, count in new_version.get_staging_payload(engine.config.num_players).items():
        engine.state.staging_cup[color] = engine.state.staging_cup.get(color, 0) + count

    # Initialize new track with spilled-over cubes
    engine.state.corruption_track = engine.state.overflow_black_cubes_on_next_track
    engine.state.overflow_black_cubes_on_next_track = 0
    engine.state.pending_version_advance = False
    return True


def execute_phase_1(engine: GameEngine) -> List[Tuple[PlayerState, List[Die], Dict[int, ShieldColor]]]:
    # Start-of-round version switch execution (INV-VER-SWITCH-01)
    check_and_execute_start_of_round_version_transition(engine)

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

        # Hook Phase 1 Step 2: Meridian Financial Trust (Redundant Crew)
        is_meridian = has_company_override(player, CompanyCode.MERIDIAN, legacy_bridge_enabled(engine)) and player.is_ability_available(active_ver)
        used_operator = False
        if is_meridian:
            use_op = player.bot.choose_meridian_override(
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
        player.purple_star_available = False
        player.purple_star_count = 0

        # Roll Active Pool (ready_for_release_dice + contractor_dice)
        active_dice: List[Die] = list(player.ready_for_release_dice) + list(player.contractor_dice)
        for die in active_dice:
            die.is_locked = False
            res_face = die.roll(engine.rng)
            if res_face and die.current_face != res_face:
                die.current_face = res_face

        # Protocol Check: The Operator (Contingent Staffing Face 6 Trigger)
        is_operator_operative = has_signature_protocol(player, WhiteHatCode.OPERATOR, legacy_bridge_enabled(engine))
        operator_contingent_staffing_triggered = False
        if is_operator_operative:
            new_contractor = check_operator_contingent_staffing(engine, player, active_dice)
            if new_contractor is not None:
                operator_contingent_staffing_triggered = True

        # Protocol Check: The Prodigy (Arbitrary Code Execution Face 6 Trigger)
        is_prodigy_operative = has_signature_protocol(player, WhiteHatCode.PRODIGY, legacy_bridge_enabled(engine))
        if is_prodigy_operative:
            resolve_prodigy_purple_star_override(player, active_dice, engine.rng)

        # 4. Lock Evaluation & Yahtzee Rerolls Loop
        active_directive = engine.state.active_directive_code
        base_free_rerolls = engine.config.default_free_rerolls
        # v0.35.0 Release L4: +1 free reroll (applied after any throttle, OQ-7)
        max_free_rerolls = research_tracks.free_rerolls_for(engine.config, player, base_free_rerolls)

        def _evaluate_locks(dice_list: List[Die]) -> None:
            for d in dice_list:
                face = d.current_face
                if not face:
                    continue
                if face.is_glitch:
                    d.is_locked = True

        _evaluate_locks(active_dice)

        is_helix = has_company_override(player, CompanyCode.HELIX, legacy_bridge_enabled(engine)) and player.is_ability_available(active_ver)
        helix_active = False
        if is_helix:
            use_helix = player.bot.choose_helix_override(
                player_state=player,
                active_dice=active_dice,
                rerolls_remaining=max_free_rerolls,
                staging_cubes=staging_copy,
                stuck_cubes=stuck_copy,
                directive_code=active_directive,
                rng=engine.rng,
                corruption_track=engine.state.corruption_track,
            )
            if use_helix:
                helix_active = True
                player.mark_ability_used(active_ver)

        # Pure Rerolls: ZERO debug actions, ZERO patch deductions
        rerolls_remaining = max_free_rerolls
        while rerolls_remaining > 0:
            # Choose rerolls among unlocked dice (or any dice if helix_active)
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
                _, reroll_indices = reroll_res
            else:
                reroll_indices = reroll_res or []

            # Filter reroll indices: Helix/Prodigy override may reroll locked dice; standard players cannot
            if helix_active:
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
            if is_operator_operative and not operator_contingent_staffing_triggered:
                new_contractor = check_operator_contingent_staffing(engine, player, active_dice)
                if new_contractor is not None:
                    operator_contingent_staffing_triggered = True
                    _evaluate_locks(active_dice)

            player.total_rerolls_used += 1
            rerolls_remaining -= 1
            if max_free_rerolls - rerolls_remaining > base_free_rerolls:
                player.l4_payouts["release_rerolls_used"] = player.l4_payouts.get("release_rerolls_used", 0) + 1

        # Prodigy Face 6 protocol check after rerolls (Arbitrary Code Execution)
        if is_prodigy_operative:
            resolve_prodigy_purple_star_override(player, active_dice, engine.rng)
            _evaluate_locks(active_dice)

        # Helix face override (Brute-Force Bypass)
        if helix_active:
            override = player.bot.choose_helix_face_override(
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
        declared_choices = research_policy.adjust_declared_choices(
            player.bot, player, active_dice, declared_choices, engine.config
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
                    if face.shield_color == ShieldColor.ANY or color == ShieldColor.ANY:
                        validated_commitments[idx] = ShieldColor.ANY
                    else:
                        validated_commitments[idx] = face.shield_color
                else:
                    if face.shield_color in (ShieldColor.RED, ShieldColor.BLUE, ShieldColor.GREEN):
                        if face.star_code != "B2":
                            validated_commitments[idx] = face.shield_color
                    elif face.shield_color == ShieldColor.ANY:
                        validated_commitments[idx] = ShieldColor.ANY

        # Enforce Defense Grid Shield Capacity (INV-DEF-CAP-01, INV-FLEX-SHIELD-01)
        if len(validated_commitments) > player.defense_capacity:
            priority_map = {
                ShieldColor.BLUE: 0,
                ShieldColor.ANY: 1,
                ShieldColor.RED: 2,
                ShieldColor.GREEN: 3,
            }
            sorted_items = sorted(
                validated_commitments.items(),
                key=lambda item: priority_map.get(item[1], 4),
            )
            allowed = dict(sorted_items[:player.defense_capacity])
            rejected_indices = set(validated_commitments.keys()) - set(allowed.keys())
            validated_commitments = allowed
            for r_idx in rejected_indices:
                r_die = active_dice[r_idx]
                if r_die.current_face and r_die.current_face.is_choice and r_die.current_face.has_shield_option:
                    r_die.chosen_choice_index = 1

        # Post-Reroll Triage & Production Assignment (v0.22.0 Canonical)
        # 1. Unresolved Glitches:
        surviving_active: List[Die] = []
        new_commitments: Dict[int, ShieldColor] = {}

        for idx, die in enumerate(active_dice):
            face = die.current_face
            if face and face.is_glitch:
                if die.color == DieColor.WHITE:
                    # White Contractor with glitch: discarded to supply
                    if die in player.contractor_dice:
                        player.contractor_dice.remove(die)
                    engine.state.contractor_supply += 1
                else:
                    # Permanent die with unresolved glitch: moves immediately to glitched_dice
                    if die in player.ready_for_release_dice:
                        player.ready_for_release_dice.remove(die)
                    player.glitched_dice.append(die)
            else:
                new_idx = len(surviving_active)
                surviving_active.append(die)
                if idx in validated_commitments:
                    new_commitments[new_idx] = validated_commitments[idx]

        # 3. Assign Production Roles and Deploy to in_production_dice
        player.in_production_dice.clear()
        for idx, die in enumerate(surviving_active):
            face = die.effective_face or die.current_face
            if idx in new_commitments:
                s_color = new_commitments[idx]
                if s_color == ShieldColor.RED:
                    die.production_role = ProductionRole.RED_SHIELD
                elif s_color == ShieldColor.BLUE:
                    die.production_role = ProductionRole.BLUE_SHIELD
                elif s_color == ShieldColor.GREEN:
                    die.production_role = ProductionRole.GREEN_SHIELD
                elif s_color == ShieldColor.ANY:
                    die.production_role = ProductionRole.ANY_SHIELD
                else:
                    die.production_role = ProductionRole.ANY_SHIELD
            else:
                die.production_role = ProductionRole.INCOME

            # Star Special eligibility tracking for Phase 3
            if face and face.is_star:
                if face.star_code == "B2":
                    if idx not in new_commitments:
                        player.b2_available = True
                elif face.star_code == "Y1":
                    player.y1_available = True
                elif face.star_code == "P1":
                    player.p1_available = True
                elif face.star_code == "P3":
                    if idx in new_commitments:
                        player.p3_available = new_commitments[idx]
                elif face.star_code == "PURPLE_STAR":
                    player.purple_star_available = True
                    player.purple_star_count += 1

            player.in_production_dice.append(die)

        # Clear ready_for_release_dice since all rolled ready dice deployed or glitched
        player.ready_for_release_dice.clear()

        # INCOME DELAY INVARIANT: No money, patch, or secret face outputs collected in Phase 1!
        player_commitments.append((player, list(surviving_active), new_commitments))

    engine.state.active_phase1_locks.clear()
    return player_commitments


def apply_single_die_immediate_output(engine: GameEngine, player: PlayerState, die: Die) -> None:
    eff = die.effective_face
    if not eff or eff.is_glitch:
        return

    # Basic money and patches
    player.money += eff.money
    player.gain_research(eff.patches, "star" if eff.is_star else "income")
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

