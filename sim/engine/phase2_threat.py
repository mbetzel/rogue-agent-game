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
            if not engine.state.pending_version_advance:
                engine.state.corruption_track += 1
                curr_track = engine.state.active_version.corruption_track
                space_idx = engine.state.corruption_track
                if curr_track and 1 <= space_idx <= len(curr_track):
                    resolve_corruption_space(
                        engine=engine,
                        space=curr_track[space_idx - 1],
                        player_commitments=player_commitments,
                        exited_cubes=exited_cubes,
                    )

                if engine.state.corruption_track >= engine.state.corruption_track_capacity:
                    if engine.state.current_version_index >= len(engine.state.version_deck) - 1:
                        # Singularity reached on v3.0!
                        engine.state.singularity_triggered = True
                        break
                    else:
                        # Mark pending advance for next round start; excess cubes spill over immediately
                        engine.state.pending_version_advance = True
                        engine.state.overflow_black_cubes_on_next_track = 0
            else:
                # Excess cubes spill over onto the upcoming version's track immediately!
                engine.state.overflow_black_cubes_on_next_track += 1
                next_ver_idx = min(engine.state.current_version_index + 1, len(engine.state.version_deck) - 1)
                next_ver = engine.state.version_deck[next_ver_idx]
                spill_idx = engine.state.overflow_black_cubes_on_next_track
                if next_ver.corruption_track and 1 <= spill_idx <= len(next_ver.corruption_track):
                    resolve_corruption_space(
                        engine=engine,
                        space=next_ver.corruption_track[spill_idx - 1],
                        player_commitments=player_commitments,
                        exited_cubes=exited_cubes,
                    )

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

    # 1. Tally committed shields by color and generic ANY
    color_shields: Dict[ShieldColor, int] = {
        ShieldColor.RED: 0,
        ShieldColor.BLUE: 0,
        ShieldColor.GREEN: 0,
        ShieldColor.ANY: 0,
    }
    for idx, color in commitments.items():
        die = rolled_dice[idx]
        face = die.effective_face or die.current_face
        if face and face.is_shield:
            color_shields[color] += face.block_amount

    player_attacks = dict(attack_strengths)

    # 2. Pre-Defense Overrides: Aegis Defense Relay / Baffle Echo
    is_aegis = bool(
        (player.company and player.company.code == CompanyCode.AEGIS)
        or (player.archetype and player.archetype.code == ArchetypeCode.ACOUSTIC)
    ) and player.is_ability_available(active_ver)
    if is_aegis:
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

    # 3. Passive Firewall (Defense Track Level 2)
    if getattr(player, "has_passive_firewall", False):
        candidates = [c for c in [CubeColor.BLUE, CubeColor.RED, CubeColor.GREEN] if player_attacks.get(c, 0) > 0]
        if candidates:
            best_c = max(candidates, key=lambda c: player_attacks.get(c, 0) - color_shields.get(ShieldColor(c.value), 0))
            player_attacks[best_c] = max(0, player_attacks[best_c] - 1)

    # 4. Stage 1: Color-Specific Shield Absorption
    rem_red = max(0, player_attacks[CubeColor.RED] - color_shields[ShieldColor.RED])
    rem_blue = max(0, player_attacks[CubeColor.BLUE] - color_shields[ShieldColor.BLUE])
    rem_green = max(0, player_attacks[CubeColor.GREEN] - color_shields[ShieldColor.GREEN])

    # 5. Stage 2: Reactive Generic "Block 1 Any" Absorption (INV-FLEX-SHIELD-01)
    avail_any = color_shields[ShieldColor.ANY]
    while avail_any > 0 and (rem_red + rem_blue + rem_green) > 0:
        # Tier 1: Blue Threat (prevent Secret loss)
        if rem_blue > 0:
            rem_blue -= 1
            avail_any -= 1
        # Tier 2: Red Threat if Cash < Red (prevent Unpaid Ransom Flat Leak)
        elif rem_red > 0 and player.money < rem_red:
            rem_red -= 1
            avail_any -= 1
        # Tier 3: Green Threat (prevent Glitch to in_production_dice)
        elif rem_green > 0:
            rem_green -= 1
            avail_any -= 1
        # Tier 4: Red Threat if Cash >= Red (save Cash buffer)
        elif rem_red > 0:
            rem_red -= 1
            avail_any -= 1
        else:
            break

    unblocked_red = rem_red
    unblocked_blue = rem_blue
    unblocked_green = rem_green

    # 6. Star face bonuses dependent on damage (R2, R3, B1)
    for die in rolled_dice:
        face = die.effective_face or die.current_face
        if not face or not face.is_star:
            continue
        if face.star_code == "R2" and unblocked_red == 0:
            player.money += 2
        elif face.star_code == "R3" and exited_cubes.get(CubeColor.RED, 0) >= 3:
            player.money += 1
        elif face.star_code == "B1" and exited_cubes.get(CubeColor.BLUE, 0) >= 1 and unblocked_blue == 0:
            player.money += 3

    # 7. Red Ransomware Resolution (INV-RANSOM-FLAT-01)
    unpaid_ransom = 0
    if unblocked_red > 0:
        cash_paid = min(player.money, unblocked_red)
        player.money -= cash_paid
        unpaid_ransom = unblocked_red - cash_paid

    # Legacy Patch Ransom Absorption Flag (if explicitly enabled in GameConfig)
    if getattr(engine.state.config, "patch_ransom_absorption", False) and unpaid_ransom > 0 and player.patches > 0:
        patch_paid = min(player.patches, unpaid_ransom)
        player.patches -= patch_paid
        unpaid_ransom -= patch_paid

    # Flat Secret Leak: 1 Secret if any shortfall exists, else 0
    ransom_secret_loss = 1 if unpaid_ransom > 0 else 0
    potential_secret_loss = ransom_secret_loss + unblocked_blue

    # DTO Slush Fund Interaction
    is_dto = bool(
        (player.company and player.company.code == CompanyCode.DTO)
        or (player.archetype and player.archetype.code == ArchetypeCode.SPOOK)
    ) and player.is_ability_available(active_ver)
    if potential_secret_loss > 0 and is_dto:
        free_absorb = min(2, potential_secret_loss)
        potential_secret_loss -= free_absorb
        player.mark_ability_used(active_ver)
        if potential_secret_loss > 0 and player.money > 0:
            cash_absorb = min(player.money, potential_secret_loss)
            player.money -= cash_absorb
            potential_secret_loss -= cash_absorb

    if potential_secret_loss > 0:
        player.secrets -= potential_secret_loss

    player.money = max(0, player.money)

    # Patient Zero Check
    if player.secrets <= 0:
        player.is_patient_zero = True
        player.elimination_round = engine.state.current_round
        player.elimination_reason = "Total Breach (<= 0 Secrets)"
        player.breach_depth = max(0, -player.secrets)

    player.last_defense_breakdown = {
        "color_shields": {
            "red": color_shields[ShieldColor.RED],
            "blue": color_shields[ShieldColor.BLUE],
            "green": color_shields[ShieldColor.GREEN],
            "any": color_shields[ShieldColor.ANY],
        },
        "blocked": {
            "red": player_attacks[CubeColor.RED] - unblocked_red,
            "blue": player_attacks[CubeColor.BLUE] - unblocked_blue,
            "green": player_attacks[CubeColor.GREEN] - unblocked_green,
        },
        "unblocked": {
            "red": unblocked_red,
            "blue": unblocked_blue,
            "green": unblocked_green,
        },
        "unpaid_ransom": unpaid_ransom,
        "flat_ransom_leak": bool(unpaid_ransom > 0),
        "ransom_secret_loss": ransom_secret_loss,
        "malware_fizzled": bool(unblocked_green > 0 and len(player.in_production_dice) == 0 and len(player.contractor_dice) == 0),
    }

    # 8. Green Malware Resolution & Malware Fizzle (INV-MALWARE-FIZZLE-01)
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
            player.contractor_dice.pop(0)
            engine.state.contractor_supply += 1
        elif len(player.in_production_dice) > 0:
            def glitch_sort_key(d: Die) -> Tuple[int, int, int]:
                role = getattr(d, "production_role", None)
                is_shield = 0 if role in (
                    ProductionRole.RED_SHIELD,
                    ProductionRole.BLUE_SHIELD,
                    ProductionRole.GREEN_SHIELD,
                    ProductionRole.ANY_SHIELD,
                ) else 1
                is_gray = 0 if d.color == DieColor.GRAY else 1
                return (is_shield, is_gray, getattr(d, "cost", 0))

            target_die = min(player.in_production_dice, key=glitch_sort_key)
            player.in_production_dice.remove(target_die)
            player.glitched_dice.append(target_die)
        else:
            # MALWARE FIZZLE: in_production_dice is empty.
            # ZERO dice destroyed from glitched, scanned, or ready_for_release. Zero penalty!
            break

    player.pending_unblocked_green = 0


def demote_player_dice_step2a(
    player: PlayerState,
    rolled_dice: List[Die],
    commitments: Dict[int, ShieldColor],
    count: int,
    threat_strengths: Optional[Dict[CubeColor, int]] = None,
) -> None:
    demoted = 0
    threats = threat_strengths or {}
    prod_dice = list(player.in_production_dice)
    if prod_dice:
        if hasattr(player.bot, "choose_dice_to_glitch"):
            chosen = player.bot.choose_dice_to_glitch(player, prod_dice, count, threats)
        else:
            chosen = prod_dice[:count]
        for die in chosen:
            if demoted >= count:
                break
            if die in player.in_production_dice:
                player.in_production_dice.remove(die)
                player.glitched_dice.append(die)
                demoted += 1
                if die in rolled_dice:
                    idx = rolled_dice.index(die)
                    commitments.pop(idx, None)

    # Fallback to ready_for_release_dice if in_production_dice was empty or exhausted
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
            ProductionRole.RED_SHIELD, ProductionRole.BLUE_SHIELD, ProductionRole.GREEN_SHIELD, ProductionRole.ANY_SHIELD
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
        threat_strengths = {
            CubeColor.RED: exited_cubes.get(CubeColor.RED, 0),
            CubeColor.BLUE: exited_cubes.get(CubeColor.BLUE, 0),
            CubeColor.GREEN: exited_cubes.get(CubeColor.GREEN, 0),
        }
        for player, rolled_dice, commitments in player_commitments:
            demote_player_dice_step2a(player, rolled_dice, commitments, space.demote_dice, threat_strengths)

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

    # 7. Next Phase Lock (Excised in v0.29.0)
    if getattr(space, "next_phase_lock", None):
        engine.state.pending_next_phase_locks.add(space.next_phase_lock)

