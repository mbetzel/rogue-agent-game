"""Phase 2: Rogue Agent Threat & Defense Resolution (Cube Tower Drop)."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from sim.config import CubeColor, DieColor, EndGameReason, ShieldColor
from sim.entities import ArchetypeCode, CompanyCode, WhiteHatCode, CorruptionSpace, Die
from sim.engine.state import ProductionRole, RoundTelemetry

if TYPE_CHECKING:
    from sim.engine.core import GameEngine
    from sim.engine.state import PlayerState


def execute_phase_2(
    engine: GameEngine,
    player_commitments: List[Tuple[PlayerState, List[Die], Dict[int, ShieldColor]]],
    defer_green_for_pids: Optional[Set[int]] = None,
) -> RoundTelemetry:
    staged_before = dict(engine.state.staging_cup)
    stuck_before = engine.state.tower.get_stuck_copy()

    # Drop all staged cubes into the tower
    exited_cubes = engine.state.tower.drop(engine.state.staging_cup, engine.rng)
    engine.state.last_exited_cubes = dict(exited_cubes)
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
            white_in_prod = [d for d in player.in_production_dice if d.color == DieColor.WHITE]
            for wd in white_in_prod:
                player.in_production_dice.remove(wd)
                engine.state.contractor_supply += 1
    else:
        engine.state.last_round_buffer_overflow = False

        # Step 2A: Resolve Black (Corruption) Cubes & Version Upgrades
        black_dropped = exited_cubes.get(CubeColor.BLACK, 0)

        for _ in range(black_dropped):
            engine.state.corruption_track += 1
            space_idx = engine.state.corruption_track
            track = engine.state.active_version.corruption_track
            if track and 1 <= space_idx <= len(track):
                space = track[space_idx - 1]
                resolve_corruption_space(
                    engine=engine,
                    space=space,
                    player_commitments=player_commitments,
                    exited_cubes=exited_cubes,
                )

            if engine.state.corruption_track >= engine.state.corruption_track_capacity:
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
                    # Add new version upgrade payload to Staging Cup (drops starting next round, if any)
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
        if active_directive == "CORRUPTED_KERNEL" and not engine.state.active_version.corruption_track:
            # Legacy Corrupted Kernel directive without corruption track
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
            should_defer = bool(defer_green_for_pids and player.player_id in defer_green_for_pids)
            resolve_player_defense_and_wear(
                engine=engine,
                player=player,
                rolled_dice=rolled_dice,
                commitments=commitments,
                attack_strengths=attack_strengths,
                exited_cubes=exited_cubes,
                active_directive=active_directive,
                defer_green_malware=should_defer,
            )

        # Snowball Recycle: Exited Red, Blue, Green cubes return to Staging Cup
        for color in [CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN]:
            engine.state.staging_cup[color] = (
                engine.state.staging_cup.get(color, 0) + exited_cubes.get(color, 0)
            )

        # Contractor Expiration: All remaining White Contractor dice across all players return to supply
        for player in engine.state.players:
            if defer_green_for_pids and player.player_id in defer_green_for_pids and getattr(player, "pending_unblocked_green", 0) > 0:
                continue
            engine.state.contractor_supply += len(player.contractor_dice)
            player.contractor_dice.clear()
            player.hired_contractor_count = 0
            white_in_prod = [d for d in player.in_production_dice if d.color == DieColor.WHITE]
            for wd in white_in_prod:
                player.in_production_dice.remove(wd)
                engine.state.contractor_supply += 1

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
            "ready_dice_count": len(p.ready_for_release_dice),
            "in_production_dice_count": len(p.in_production_dice),
            "glitched_dice_count": len(p.glitched_dice),
            "scanned_dice_count": len(p.scanned_dice),
            "unpatched_dice_count": len(p.glitched_dice) + len(p.scanned_dice),
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
    defer_green_malware: bool = False,
) -> None:
    active_ver = engine.state.active_version.version_str
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

    # Hook Phase 2 Step 2B: Aegis Defense Relay (Baffle Echo - v0.13.0)
    # When resolving compiler damage, ignore 1 Attack Cube of your choice for yourself this round.
    # Exited cubes remain in the exit tray and recycle as normal.
    player_attacks = dict(attack_strengths)
    is_aegis = bool(
        (player.company and player.company.code == CompanyCode.AEGIS)
        or (player.archetype and player.archetype.code == ArchetypeCode.ACOUSTIC)
    ) and player.is_ability_available(active_ver)
    if is_aegis:
        # Determine qualifying attack colors where threat exceeds shields (or causes unblocked damage)
        qualifying = [
            c for c in [CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN]
            if player_attacks.get(c, 0) > 0 and exited_cubes.get(c, 0) > 0
        ]
        if qualifying:
            chosen_color = player.bot.choose_aegis_override(
                player_state=player,
                qualifying_colors=qualifying,
                exited_cubes=exited_cubes,
                active_version_str=active_ver,
                rng=engine.rng,
                corruption_track=engine.state.corruption_track,
            )
            if chosen_color in qualifying:
                player_attacks[chosen_color] = max(0, player_attacks[chosen_color] - 1)
                player.mark_ability_used(active_ver)

    # Passive Firewall (Level 2 Defense Track - INV-UPGRADE-TRACK-01)
    if getattr(player, "has_passive_firewall", False):
        candidates = [c for c in [CubeColor.BLUE, CubeColor.RED, CubeColor.GREEN] if player_attacks.get(c, 0) > 0]
        if candidates:
            best_c = max(candidates, key=lambda c: player_attacks.get(c, 0) - effective_shields.get(c, 0))
            player_attacks[best_c] = max(0, player_attacks[best_c] - 1)

    # Calculate blocked and unblocked attacks
    blocked_red = min(effective_shields[CubeColor.RED], player_attacks[CubeColor.RED])
    unblocked_red = player_attacks[CubeColor.RED] - blocked_red

    blocked_blue = min(effective_shields[CubeColor.BLUE], player_attacks[CubeColor.BLUE])
    unblocked_blue = player_attacks[CubeColor.BLUE] - blocked_blue

    blocked_green = min(effective_shields[CubeColor.GREEN], player_attacks[CubeColor.GREEN])
    unblocked_green = player_attacks[CubeColor.GREEN] - blocked_green

    # 1. Zero Dice Wear (v0.22.0 Canonical):
    # Modules assigned to shields DO NOT wear down or move to Under Development when blocking!
    # They absorb the attack cleanly and remain safely deployed in in_production_dice.

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
    # v0.21.0 Baseline: Cash-Only Ransom. Unpaid ransom leaks directly to Secrets (1 Secret per unpaid $1).
    # Emergency patch absorption is deprecated and disabled by default (config.patch_ransom_absorption=False).
    # Money and patches are strictly non-negative (>= 0).
    unpaid_ransom = 0
    if unblocked_red > 0:
        cash_paid = min(player.money, unblocked_red)
        player.money -= cash_paid
        unpaid_ransom = unblocked_red - cash_paid

        if unpaid_ransom > 0 and getattr(engine.state.config, "patch_ransom_absorption", False) and player.patches > 0:
            patches_absorbed = min(player.patches, unpaid_ransom)
            player.patches -= patches_absorbed
            unpaid_ransom -= patches_absorbed

    # Hook Phase 2 Step 2B: Dept. of Telecom (DTO) (Slush Fund - v0.13.0)
    # Absorb up to 2 Corporate Secret loss (from Blue Spyware or unpaid Red Ransom) for free without paying cash.
    # (Any additional Secret loss may be absorbed by paying $1 per Secret as normal).
    potential_secret_loss = unpaid_ransom + unblocked_blue
    is_dto = bool(
        (player.company and player.company.code == CompanyCode.DTO)
        or (player.archetype and player.archetype.code == ArchetypeCode.SPOOK)
    ) and player.is_ability_available(active_ver)
    if (
        potential_secret_loss > 0
        and is_dto
    ):
        # 1. Absorb up to 2 Secrets for FREE from emergency slush reserves
        free_absorb = min(2, potential_secret_loss)
        absorbed_from_ransom = min(unpaid_ransom, free_absorb)
        unpaid_ransom -= absorbed_from_ransom
        remaining_free = free_absorb - absorbed_from_ransom
        unblocked_blue -= remaining_free
        potential_secret_loss -= free_absorb
        player.mark_ability_used(active_ver)

        # 2. If excess secret loss remains and player has cash, allow additional cash absorption at $1/Secret
        if potential_secret_loss > 0 and player.money > 0:
            dto_dollars = player.bot.choose_dto_override(
                player_state=player,
                secrets_at_risk=potential_secret_loss,
                active_version_str=active_ver,
                rng=engine.rng,
                corruption_track=engine.state.corruption_track,
            )
            actual_dto_dollars = max(0, min(dto_dollars, player.money, potential_secret_loss))
            if actual_dto_dollars > 0:
                player.money -= actual_dto_dollars
                absorbed_paid_ransom = min(unpaid_ransom, actual_dto_dollars)
                unpaid_ransom -= absorbed_paid_ransom
                remaining_paid = actual_dto_dollars - absorbed_paid_ransom
                unblocked_blue -= remaining_paid

    if unpaid_ransom > 0:
        player.secrets -= unpaid_ransom

    player.money = max(0, player.money)
    player.patches = max(0, player.patches)

    # Blue (Spyware): Lose 1 Corporate Secret per unblocked Blue cube
    if unblocked_blue > 0:
        player.secrets -= unblocked_blue

    # Patient Zero Check: Strictly occurs upon Total Data Breach (Secrets <= 0)
    if player.secrets <= 0:
        player.is_patient_zero = True
        player.elimination_round = engine.state.current_round
        player.elimination_reason = "Total Breach (<= 0 Secrets)"
        player.breach_depth = max(0, -player.secrets)

    # Green (Malware / Logic Bombs): Move 1 active die from in_production_dice to glitched_dice per cube
    player.pending_unblocked_green = unblocked_green
    if defer_green_malware:
        return

    for _ in range(unblocked_green):
        sacrifice = player.bot.choose_malware_sacrifice(
            player_state=player,
            unblocked_green=unblocked_green,
            rng=engine.rng,
        )
        if sacrifice and len(player.contractor_dice) > 0:
            sacrificed_die = player.contractor_dice.pop(0)
            engine.state.contractor_supply += 1
        elif len(player.in_production_dice) > 0:
            # Defensive Shield Sacrifice / Triage:
            # Defending consultancy prioritizes glitching a Shield die first (which already blocked) to protect Income dice
            def glitch_sort_key(d: Die) -> Tuple[int, int, int]:
                role = getattr(d, "production_role", None)
                is_shield = 0 if role in (
                    ProductionRole.RED_SHIELD,
                    ProductionRole.BLUE_SHIELD,
                    ProductionRole.GREEN_SHIELD,
                ) else 1
                is_gray = 0 if d.color == DieColor.GRAY else 1
                return (is_shield, is_gray, getattr(d, "cost", 0))

            target_die = min(player.in_production_dice, key=glitch_sort_key)
            player.in_production_dice.remove(target_die)
            player.glitched_dice.append(target_die)
        elif len(player.glitched_dice) > 0 or len(player.scanned_dice) > 0:
            # Destruction Fallback: Destroy (return to box) 1 die from Under Development
            if player.glitched_dice:
                player.glitched_dice.sort(key=lambda d: (0 if d.color == DieColor.GRAY else 1, getattr(d, "cost", 0)))
                player.glitched_dice.pop(0)
            else:
                player.scanned_dice.sort(key=lambda d: (0 if d.color == DieColor.GRAY else 1, getattr(d, "cost", 0)))
                player.scanned_dice.pop(0)
        elif len(player.ready_for_release_dice) > 0:
            player.ready_for_release_dice.sort(key=lambda d: (0 if d.color == DieColor.GRAY else 1, getattr(d, "cost", 0)))
            player.ready_for_release_dice.pop(0)
        else:
            # Completely wiped out; record unfulfilled die destruction
            player.unfulfilled_destructions += 1

    player.pending_unblocked_green = 0


def demote_player_dice_step2a(
    player: PlayerState,
    rolled_dice: List[Die],
    commitments: Dict[int, ShieldColor],
    count: int,
) -> None:
    demoted = 0
    # Prioritize Income dice in in_production_dice
    income_dice = [
        d for d in list(player.in_production_dice)
        if getattr(d, "production_role", None) == ProductionRole.INCOME
    ]
    income_dice.sort(key=lambda d: (0 if d.color == DieColor.GRAY else 1, getattr(d, "cost", 0)))
    while demoted < count and income_dice:
        die = income_dice.pop(0)
        if die in player.in_production_dice:
            player.in_production_dice.remove(die)
            player.glitched_dice.append(die)
            demoted += 1

    # If still need to demote, move Shield dice and revoke their defensive shield commitment
    if demoted < count:
        shield_dice = [
            d for d in list(player.in_production_dice)
            if getattr(d, "production_role", None) != ProductionRole.INCOME
        ]
        shield_dice.sort(key=lambda d: (0 if d.color == DieColor.GRAY else 1, getattr(d, "cost", 0)))
        while demoted < count and shield_dice:
            die = shield_dice.pop(0)
            if die in player.in_production_dice:
                player.in_production_dice.remove(die)
                player.glitched_dice.append(die)
                demoted += 1
                if die in rolled_dice:
                    idx = rolled_dice.index(die)
                    commitments.pop(idx, None)

    # Fallback to ready_for_release_dice if in_production_dice was empty
    if demoted < count and player.ready_for_release_dice:
        ready_pool = list(player.ready_for_release_dice)
        ready_pool.sort(key=lambda d: (0 if d.color == DieColor.GRAY else 1, getattr(d, "cost", 0)))
        while demoted < count and ready_pool:
            die = ready_pool.pop(0)
            if die in player.ready_for_release_dice:
                player.ready_for_release_dice.remove(die)
                player.glitched_dice.append(die)
                demoted += 1


def return_player_colored_dice_step2a(
    engine: GameEngine,
    player: PlayerState,
    rolled_dice: List[Die],
    commitments: Dict[int, ShieldColor],
    count: int,
) -> None:
    returned = 0
    # 1. Under Development (Glitched + Scanned)
    for zone in (player.glitched_dice, player.scanned_dice):
        colored = [d for d in list(zone) if d.color != DieColor.GRAY and d.color != DieColor.WHITE]
        for die in colored:
            if returned >= count:
                break
            zone.remove(die)
            if die.color in engine.state.market:
                engine.state.market[die.color] += 1
            # If Purple, die is scrapped and not returned to market
            returned += 1

    # 2. In Production (Income dice first, then Shield dice)
    if returned < count:
        prod_colored = [
            d for d in list(player.in_production_dice)
            if d.color != DieColor.GRAY and d.color != DieColor.WHITE
        ]
        prod_colored.sort(key=lambda d: 1 if getattr(d, "production_role", None) in (
            ProductionRole.RED_SHIELD, ProductionRole.BLUE_SHIELD, ProductionRole.GREEN_SHIELD
        ) else 0)
        for die in prod_colored:
            if returned >= count:
                break
            player.in_production_dice.remove(die)
            if die.color in engine.state.market:
                engine.state.market[die.color] += 1
            # If Purple, die is scrapped and not returned to market
            if die in rolled_dice:
                idx = rolled_dice.index(die)
                commitments.pop(idx, None)
            returned += 1

    # 3. Ready for Release
    if returned < count:
        ready_colored = [
            d for d in list(player.ready_for_release_dice)
            if d.color != DieColor.GRAY and d.color != DieColor.WHITE
        ]
        for die in ready_colored:
            if returned >= count:
                break
            player.ready_for_release_dice.remove(die)
            if die.color in engine.state.market:
                engine.state.market[die.color] += 1
            # If Purple, die is scrapped and not returned to market
            returned += 1


def resolve_corruption_space(
    engine: GameEngine,
    space: CorruptionSpace,
    player_commitments: List[Tuple[PlayerState, List[Die], Dict[int, ShieldColor]]],
    exited_cubes: Dict[CubeColor, int],
) -> None:
    # 1. Add Cubes
    if space.add_cubes:
        for color, count in space.add_cubes.items():
            if engine.config.corruption_cubes_resolve_immediately:
                if color == CubeColor.BLACK:
                    engine.state.staging_cup[color] = engine.state.staging_cup.get(color, 0) + count
                else:
                    exited_cubes[color] = exited_cubes.get(color, 0) + count
            else:
                engine.state.staging_cup[color] = engine.state.staging_cup.get(color, 0) + count

    # 2. Lose Money
    if space.lose_money > 0:
        for player in engine.state.players:
            player.money = max(0, player.money - space.lose_money)

    # 3. Lose Patches
    if space.lose_patches > 0:
        for player in engine.state.players:
            player.patches = max(0, player.patches - space.lose_patches)

    # 4. Demote Dice
    if space.demote_dice > 0:
        for player, rolled_dice, commitments in player_commitments:
            demote_player_dice_step2a(player, rolled_dice, commitments, space.demote_dice)

    # 5. Return Colored Dice
    if space.return_colored_dice > 0:
        for player, rolled_dice, commitments in player_commitments:
            return_player_colored_dice_step2a(engine, player, rolled_dice, commitments, space.return_colored_dice)

    # 6. Lose Secrets
    if space.lose_secrets > 0:
        for player in engine.state.players:
            player.secrets -= space.lose_secrets
            if player.secrets <= 0:
                player.is_patient_zero = True

    # 7. Next Phase Lock
    if space.next_phase_lock:
        engine.state.pending_next_phase_locks.add(space.next_phase_lock)

