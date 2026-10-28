"""Phase 2: Rogue Agent Threat & Defense Resolution (Cube Tower Drop)."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from sim.config import CubeColor, DieColor, EndGameReason, ShieldColor
from sim.entities import ArchetypeCode, Die
from sim.engine.state import RoundTelemetry

if TYPE_CHECKING:
    from sim.engine.core import GameEngine
    from sim.engine.state import PlayerState


def execute_phase_2(
    engine: GameEngine,
    player_commitments: List[Tuple[PlayerState, List[Die], Dict[int, ShieldColor]]],
) -> RoundTelemetry:
    staged_before = dict(engine.state.staging_cup)
    stuck_before = engine.state.tower.get_stuck_copy()

    # Drop all staged cubes into the tower
    exited_cubes = engine.state.tower.drop(engine.state.staging_cup, engine.rng)
    stuck_after = engine.state.tower.get_stuck_copy()

    # Clear staging cup
    for color in engine.state.staging_cup:
        engine.state.staging_cup[color] = 0

    total_exited = sum(exited_cubes.values())
    buffer_overflow = total_exited == 0 and engine.state.config.enable_buffer_overflow

    if buffer_overflow:
        engine.state.last_round_buffer_overflow = True
        engine.state.total_buffer_overflows += 1

        attack_strengths = {
            CubeColor.RED: 0,
            CubeColor.BLUE: 0,
            CubeColor.GREEN: 0,
        }

        # Inject buffer_overflow_cubes into staging_cup
        for color, count in engine.state.config.buffer_overflow_cubes.items():
            engine.state.staging_cup[color] = (
                engine.state.staging_cup.get(color, 0) + count
            )

        # Contractor Expiration: All remaining White Contractor dice across all players return to supply
        for player in engine.state.players:
            engine.state.contractor_supply += len(player.contractor_dice)
            player.contractor_dice.clear()
            player.hired_contractor_count = 0
    else:
        engine.state.last_round_buffer_overflow = False

        # Step 2A: Resolve Black (Corruption) Cubes & Version Upgrades
        black_dropped = exited_cubes.get(CubeColor.BLACK, 0)
        track_capacity = engine.state.config.corruption_track_capacity

        for _ in range(black_dropped):
            engine.state.corruption_track += 1
            if engine.state.corruption_track >= track_capacity:
                if engine.state.current_version_index >= len(engine.state.version_deck) - 1:
                    # Singularity reached on v3.0!
                    engine.state.singularity_triggered = True
                    break
                else:
                    # Upgrade to next version: forfeit unspent old ability, unlock new ability
                    old_version_str = engine.state.active_version.version_str
                    engine.state.corruption_track = 0
                    engine.state.current_version_index += 1
                    new_version_str = engine.state.active_version.version_str
                    for p in engine.state.players:
                        p.mark_ability_forfeited(old_version_str)
                        p.unlock_version_ability(new_version_str)
                    # Add new version upgrade payload to Staging Cup (drops starting next round)
                    new_version = engine.state.active_version
                    for color, count in new_version.get_staging_payload(engine.config.num_players).items():
                        engine.state.staging_cup[color] = engine.state.staging_cup.get(color, 0) + count

        # Apply P2 (Chaos Profiteer) Star bonus: +$2 per exited black cube
        if black_dropped > 0:
            for player, rolled_dice, _ in player_commitments:
                for die in rolled_dice:
                    if die.current_face and die.current_face.star_code == "P2":
                        player.money += 2 * black_dropped

        # Step 2B: Resolve Attack Cubes (Red, Blue, Green)
        red_strength = exited_cubes.get(CubeColor.RED, 0)
        blue_strength = exited_cubes.get(CubeColor.BLUE, 0)
        green_strength = exited_cubes.get(CubeColor.GREEN, 0)

        # Apply Active Version Directives to Attack Strength
        active_directive = engine.state.active_directive_code
        if active_directive == "CORRUPTED_KERNEL":
            # Corrupted Kernel: If 2+ Black Cubes exit the tower this round, the Attack Color with the most exited cubes gains +2 Strength total.
            if black_dropped >= engine.config.corrupted_kernel_black_threshold:
                highest_color = max(
                    [CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN],
                    key=lambda c: (
                        exited_cubes.get(c, 0),
                        c == CubeColor.RED,
                        c == CubeColor.BLUE,
                    ),
                )
                bonus = engine.config.corrupted_kernel_strength_bonus
                if highest_color == CubeColor.RED:
                    red_strength += bonus
                elif highest_color == CubeColor.BLUE:
                    blue_strength += bonus
                elif highest_color == CubeColor.GREEN:
                    green_strength += bonus

        attack_strengths = {
            CubeColor.RED: red_strength,
            CubeColor.BLUE: blue_strength,
            CubeColor.GREEN: green_strength,
        }

        # Resolve each player's committed shields against attacks
        for player, rolled_dice, commitments in player_commitments:
            resolve_player_defense_and_wear(
                engine=engine,
                player=player,
                rolled_dice=rolled_dice,
                commitments=commitments,
                attack_strengths=attack_strengths,
                exited_cubes=exited_cubes,
                active_directive=active_directive,
            )

        # Snowball Recycle: Exited Red, Blue, Green cubes return to Staging Cup
        for color in [CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN]:
            engine.state.staging_cup[color] = (
                engine.state.staging_cup.get(color, 0) + exited_cubes.get(color, 0)
            )

        # Contractor Expiration: All remaining White Contractor dice across all players return to supply
        for player in engine.state.players:
            engine.state.contractor_supply += len(player.contractor_dice)
            player.contractor_dice.clear()
            player.hired_contractor_count = 0

        # Step 2C: Check End Game Triggers
        any_patient_zero = any(p.is_patient_zero for p in engine.state.players)
        all_patient_zero = all(p.is_patient_zero for p in engine.state.players)

        if all_patient_zero:
            engine.state.game_over = True
            engine.state.is_final_round = False
            engine.state.end_reason = EndGameReason.TOTAL_WIPEOUT
        elif any_patient_zero:
            engine.state.is_final_round = True
            engine.state.end_reason = EndGameReason.PATIENT_ZERO
        elif engine.state.singularity_triggered:
            engine.state.is_final_round = True
            engine.state.end_reason = EndGameReason.SINGULARITY

    # Create Round Telemetry snapshot
    snapshots = [
        {
            "player_id": p.player_id,
            "bot_name": p.bot.name,
            "money": p.money,
            "secrets": p.secrets,
            "patches": p.patches,
            "ready_dice_count": len(p.ready_dice),
            "unpatched_dice_count": len(p.unpatched_dice),
            "contractor_dice_count": len(p.contractor_dice),
            "is_patient_zero": p.is_patient_zero,
        }
        for p in engine.state.players
    ]

    telemetry = RoundTelemetry(
        round_number=engine.state.current_round,
        active_version_name=engine.state.active_version.name,
        corruption_track=engine.state.corruption_track,
        staged_cubes=staged_before,
        stuck_cubes_before=stuck_before,
        exited_cubes=exited_cubes,
        stuck_cubes_after=stuck_after,
        attack_strengths=attack_strengths,
        player_snapshots=snapshots,
        buffer_overflow=buffer_overflow,
    )
    engine.telemetry_history.append(telemetry)
    return telemetry



def resolve_player_defense_and_wear(
    engine: GameEngine,
    player: PlayerState,
    rolled_dice: List[Die],
    commitments: Dict[int, ShieldColor],
    attack_strengths: Dict[CubeColor, int],
    exited_cubes: Dict[CubeColor, int],
    active_directive: str,
) -> None:
    # Calculate raw committed shields per color
    raw_shields: Dict[ShieldColor, int] = {
        ShieldColor.RED: 0,
        ShieldColor.BLUE: 0,
        ShieldColor.GREEN: 0,
    }
    color_dice_map: Dict[ShieldColor, List[Tuple[int, Die]]] = {
        ShieldColor.RED: [],
        ShieldColor.BLUE: [],
        ShieldColor.GREEN: [],
    }

    for idx, color in commitments.items():
        die = rolled_dice[idx]
        face = die.effective_face or die.current_face
        if face and face.is_shield:
            raw_shields[color] += face.block_amount
            color_dice_map[color].append((idx, die))

    effective_shields: Dict[CubeColor, int] = {
        CubeColor.RED: raw_shields[ShieldColor.RED],
        CubeColor.BLUE: raw_shields[ShieldColor.BLUE],
        CubeColor.GREEN: raw_shields[ShieldColor.GREEN],
    }

    # Calculate blocked and unblocked attacks
    blocked_red = min(effective_shields[CubeColor.RED], attack_strengths[CubeColor.RED])
    unblocked_red = attack_strengths[CubeColor.RED] - blocked_red

    blocked_blue = min(effective_shields[CubeColor.BLUE], attack_strengths[CubeColor.BLUE])
    unblocked_blue = attack_strengths[CubeColor.BLUE] - blocked_blue

    blocked_green = min(effective_shields[CubeColor.GREEN], attack_strengths[CubeColor.GREEN])
    unblocked_green = attack_strengths[CubeColor.GREEN] - blocked_green

    # 1. Dice Wear: Any permanent die assigned as a shield that actively blocks at least 1 cube moves to Unpatched
    # White Contractor dice have wear immunity (return to supply at round end).
    # Dice that block 0 cubes remain Ready
    worn_dice_set: set[int] = set()

    for s_color, attack_blocked in [
        (ShieldColor.RED, blocked_red),
        (ShieldColor.BLUE, blocked_blue),
        (ShieldColor.GREEN, blocked_green),
    ]:
        assigned_dice = [die for _, die in color_dice_map[s_color]]
        ordered_dice = player.bot.choose_shield_wear_order(
            player_state=player,
            color=s_color,
            assigned_dice=assigned_dice,
            cubes_to_absorb=attack_blocked,
        )
        cubes_remaining_to_absorb = attack_blocked
        for die in ordered_dice:
            if cubes_remaining_to_absorb <= 0:
                break  # Unused shields remain Ready!

            face = die.effective_face or die.current_face
            amt = face.block_amount if face else 0
            cubes_remaining_to_absorb -= amt

            # White contractor dice wear immunity!
            if die.color == DieColor.WHITE:
                continue

            # B3 — Air-Gapped Backup: when actively blocking, move 1 other Ready die of your choice to Unpatched instead of this die (if no other Ready die, this die moves to Unpatched)
            if face and face.star_code == "B3":
                other_ready = [d for d in player.ready_dice if d.die_id != die.die_id]
                if other_ready:
                    sacrificial_die = player.bot.choose_b3_sacrificial_die(
                        player_state=player, other_ready_dice=other_ready
                    )
                    if sacrificial_die not in other_ready:
                        sacrificial_die = other_ready[0]
                    if sacrificial_die in player.ready_dice:
                        player.ready_dice.remove(sacrificial_die)
                        player.unpatched_dice.append(sacrificial_die)
                        worn_dice_set.add(sacrificial_die.die_id)
                    continue
                else:
                    if die in player.ready_dice:
                        player.ready_dice.remove(die)
                        player.unpatched_dice.append(die)
                        worn_dice_set.add(die.die_id)
                    continue

            if die in player.ready_dice:
                player.ready_dice.remove(die)
                player.unpatched_dice.append(die)
                worn_dice_set.add(die.die_id)

    # 2. Star ability damage-dependent bonuses
    for die in rolled_dice:
        face = die.effective_face or die.current_face
        if not face or not face.is_star:
            continue
        if face.star_code == "R2":
            # Threat Bounty: Block 2 Red; if you take 0 unblocked Red damage, gain +$2
            if unblocked_red == 0:
                player.money += 2
        elif face.star_code == "R3":
            # Short Squeeze: if 3+ Red cubes exit tower, gain extra +$1
            if exited_cubes.get(CubeColor.RED, 0) >= 3:
                player.money += 1
        elif face.star_code == "B1":
            # Honeypot: Block 2 Blue; if 1+ Blue cubes exit and you take 0 Blue damage, gain +$3
            if exited_cubes.get(CubeColor.BLUE, 0) >= 1 and unblocked_blue == 0:
                player.money += 3

    # Record unblocked attacks for Acoustic
    acoustic_unblocked = {
        CubeColor.RED: unblocked_red,
        CubeColor.BLUE: unblocked_blue,
        CubeColor.GREEN: unblocked_green,
    }
    active_ver = engine.state.active_version.version_str

    # 3. Apply Unblocked Damage
    # Red (Ransomware): Lose $1 per unblocked Red cube.
    # Tier 1: Cash pays min(player.money, unblocked_red).
    # Tier 2: Emergency Patch Absorption - patches absorb min(player.patches, unpaid_ransom).
    # Tier 3: Unpaid Ransom Leak - remaining unpaid ransom leaks Secrets (1 Secret per unpaid $1).
    # Money and patches are strictly non-negative (>= 0).
    unpaid_ransom = 0
    if unblocked_red > 0:
        cash_paid = min(player.money, unblocked_red)
        player.money -= cash_paid
        unpaid_ransom = unblocked_red - cash_paid

        if unpaid_ransom > 0 and player.patches > 0:
            patches_absorbed = min(player.patches, unpaid_ransom)
            player.patches -= patches_absorbed
            unpaid_ransom -= patches_absorbed

    # Hook Phase 2 Step 2B: The Spook (Slush Fund)
    # Pay $1 per secret to absorb Blue secret loss or unpaid Red ransom before leak
    potential_secret_loss = unpaid_ransom + unblocked_blue
    if (
        potential_secret_loss > 0
        and player.money > 0
        and player.archetype is not None
        and player.archetype.code == ArchetypeCode.SPOOK
        and player.is_ability_available(active_ver)
    ):
        spook_dollars = player.bot.choose_spook_ability(
            player_state=player,
            secrets_at_risk=potential_secret_loss,
            active_version_str=active_ver,
            rng=engine.rng,
            corruption_track=engine.state.corruption_track,
        )
        actual_spook_dollars = max(0, min(spook_dollars, player.money, potential_secret_loss))
        if actual_spook_dollars > 0:
            player.money -= actual_spook_dollars
            player.mark_ability_used(active_ver)
            # First absorb from unpaid ransom, then unblocked blue
            absorbed_from_ransom = min(unpaid_ransom, actual_spook_dollars)
            unpaid_ransom -= absorbed_from_ransom
            remaining_absorb = actual_spook_dollars - absorbed_from_ransom
            unblocked_blue -= remaining_absorb

    if unpaid_ransom > 0:
        player.secrets -= unpaid_ransom

    player.money = max(0, player.money)
    player.patches = max(0, player.patches)

    # Blue (Spyware): Lose 1 Corporate Secret per unblocked Blue cube
    if unblocked_blue > 0:
        player.secrets -= unblocked_blue

    # Hook Phase 2 Step 2B: The Acoustic (Baffle Echo)
    # If suffering unblocked damage from any color, permanently remove 1 exited cube of that color
    if (
        player.archetype is not None
        and player.archetype.code == ArchetypeCode.ACOUSTIC
        and player.is_ability_available(active_ver)
    ):
        qualifying = [
            c for c in [CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN]
            if acoustic_unblocked.get(c, 0) > 0 and exited_cubes.get(c, 0) > 0
        ]
        if qualifying:
            chosen_color = player.bot.choose_acoustic_ability(
                player_state=player,
                qualifying_colors=qualifying,
                exited_cubes=exited_cubes,
                active_version_str=active_ver,
                rng=engine.rng,
                corruption_track=engine.state.corruption_track,
            )
            if chosen_color in qualifying and exited_cubes.get(chosen_color, 0) > 0:
                exited_cubes[chosen_color] -= 1
                player.mark_ability_used(active_ver)

    # Patient Zero Check: Strictly occurs upon Total Data Breach (Secrets <= 0)
    if player.secrets <= 0:
        player.is_patient_zero = True
        player.elimination_round = engine.state.current_round
        player.elimination_reason = "Total Breach (<= 0 Secrets)"
        player.breach_depth = max(0, -player.secrets)

    # Green (Malware): Move 1 Ready die to Unpatched per cube.
    # Commercial Exposure: Ready Yellow dice must be demoted first before Contractor Sacrifice or other ready dice can absorb malware.
    # Contractor Sacrifice: You may discard 1 active White Contractor die instead (if no ready yellow dice)!
    for _ in range(unblocked_green):
        ready_yellow_idx = next(
            (idx for idx, d in enumerate(player.ready_dice) if d.color == DieColor.YELLOW),
            None,
        )
        if ready_yellow_idx is not None:
            # Commercial Exposure: demote ready Yellow die first
            demoted_yellow = player.ready_dice.pop(ready_yellow_idx)
            player.unpatched_dice.append(demoted_yellow)
        else:
            sacrifice = player.bot.choose_malware_sacrifice(
                player_state=player,
                unblocked_green=unblocked_green,
                rng=engine.rng,
            )
            if sacrifice and len(player.contractor_dice) > 0:
                sacrificed_die = player.contractor_dice.pop(0)
                engine.state.contractor_supply += 1
            elif len(player.ready_dice) > 0:
                # Move first ready die to unpatched
                demoted = player.ready_dice.pop(0)
                player.unpatched_dice.append(demoted)
            elif len(player.unpatched_dice) > 0:
                # Destroy 1 Unpatched die of player's choice (destroy lowest VP die first)
                player.unpatched_dice.sort(key=lambda d: d.vp)
                player.unpatched_dice.pop(0)
            else:
                # Completely wiped out; record unfulfilled die destruction
                player.unfulfilled_destructions += 1

