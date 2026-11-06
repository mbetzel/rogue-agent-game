# NOTE (v0.34.0): this script targets the v0.33-era module layout (phase1_boot / phase2_threat /
# phase3_ops). After the six-phase module split, its monkeypatches of those modules may no longer
# take effect on either round sequence (legacy_v033 binds the new modules). Results are historical.
"""Investigation Script: Testing User's 3 Proposed Mechanics Changes.

Proposals:
1. Flexible / Reactive "Block 1 Any":
   - "Block 1 Any" faces placed in Defense Grid (up to defense_capacity) are not pre-committed to a specific color.
   - When the tower drop occurs, they are allocated to block exited attack cubes (priority: Blue > Green > Red or cash-aware).
   - Color-specific shields remain locked to their color.

2. Unpaid Ransom Leak:
   - Baseline: Lose 1 Secret per unpaid $1.
   - Proposal: Lose 1 Secret flat if you have ANY unpaid Red cubes (unpaid_ransom > 0).

3. Destruction Fallback:
   - Baseline: If in_production_dice is empty when unblocked Green hits, destroy 1 die from Under Development.
   - Proposal: Remove Destruction Fallback entirely (fizzles if in_production_dice is empty).
"""

import sys
import os
import random
import copy
from collections import defaultdict
from typing import Dict, List, Tuple, Any, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sim.config import GameConfig, DieColor, CubeColor, ShieldColor, EndGameReason
from sim.engine.core import GameEngine
from sim.engine.state import PlayerState, ProductionRole
from sim.entities import (
    Die,
    CompanyCode,
    WhiteHatCode,
    ArchetypeCode,
    get_all_companies,
    get_all_white_hats,
    get_random_setup,
    CANONICAL_COMPANY_FOR_OPERATIVE,
)
from sim.bots import (
    AdaptiveBalancedBot,
    SecOpsTurtleBot,
    VentureGreedBot,
    AccelerationistBot,
)
import sim.engine.phase2_threat as phase2_threat


def run_pod_simulation(
    num_players: int = 4,
    num_matches: int = 1000,
    base_seed: int = 42,
    enable_flexible_any: bool = False,
    flat_unpaid_ransom: bool = False,
    remove_destruction_fallback: bool = False,
) -> Dict[str, Any]:
    """Runs a suite of matches with monkey-patched variants to measure exact impact."""

    # We can customize resolve_player_defense_and_wear dynamically
    orig_resolve = phase2_threat.resolve_player_defense_and_wear

    def custom_resolve(
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
        
        # Calculate raw color-specific shields and flexible ANY shields
        color_specific: Dict[CubeColor, int] = {
            CubeColor.RED: 0,
            CubeColor.BLUE: 0,
            CubeColor.GREEN: 0,
        }
        flexible_any_shields = 0

        for idx, color in commitments.items():
            die = rolled_dice[idx]
            face = die.effective_face or die.current_face
            if face and face.is_shield:
                if enable_flexible_any and face.shield_color == ShieldColor.ANY:
                    flexible_any_shields += face.block_amount
                else:
                    if color == ShieldColor.RED:
                        color_specific[CubeColor.RED] += face.block_amount
                    elif color == ShieldColor.BLUE:
                        color_specific[CubeColor.BLUE] += face.block_amount
                    elif color == ShieldColor.GREEN:
                        color_specific[CubeColor.GREEN] += face.block_amount

        player_attacks = dict(attack_strengths)

        # Aegis Defense Relay / Acoustic Baffle Echo
        is_aegis = bool(
            (player.company and player.company.code == CompanyCode.AEGIS)
            or (player.archetype and player.archetype.code == ArchetypeCode.ACOUSTIC if hasattr(phase2_threat, "ArchetypeCode") else False)
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

        # Passive Firewall (Level 2 Defense Track)
        if getattr(player, "has_passive_firewall", False):
            candidates = [c for c in [CubeColor.BLUE, CubeColor.RED, CubeColor.GREEN] if player_attacks.get(c, 0) > 0]
            if candidates:
                best_c = max(candidates, key=lambda c: player_attacks.get(c, 0) - color_specific.get(c, 0))
                player_attacks[best_c] = max(0, player_attacks[best_c] - 1)

        # First, apply color-specific shields
        unblocked_red = max(0, player_attacks[CubeColor.RED] - color_specific[CubeColor.RED])
        unblocked_blue = max(0, player_attacks[CubeColor.BLUE] - color_specific[CubeColor.BLUE])
        unblocked_green = max(0, player_attacks[CubeColor.GREEN] - color_specific[CubeColor.GREEN])

        # Then, apply flexible ANY shields if enabled
        if enable_flexible_any and flexible_any_shields > 0:
            # Optimal strategic allocation:
            # 1. Block Blue (direct secret loss)
            # 2. Block Red if player cannot afford ransom (prevents unpaid ransom leak), otherwise Green (prevents glitch), then Red
            while flexible_any_shields > 0:
                if unblocked_blue > 0:
                    unblocked_blue -= 1
                    flexible_any_shields -= 1
                elif unblocked_red > 0 and player.money < unblocked_red:
                    unblocked_red -= 1
                    flexible_any_shields -= 1
                elif unblocked_green > 0:
                    unblocked_green -= 1
                    flexible_any_shields -= 1
                elif unblocked_red > 0:
                    unblocked_red -= 1
                    flexible_any_shields -= 1
                else:
                    break

        # Star ability damage-dependent bonuses
        for die in rolled_dice:
            face = die.effective_face or die.current_face
            if not face or not face.is_star:
                continue
            if face.star_code == "R2":
                if unblocked_red == 0:
                    player.money += 2
            elif face.star_code == "R3":
                if exited_cubes.get(CubeColor.RED, 0) >= 3:
                    player.money += 1
            elif face.star_code == "B1":
                if exited_cubes.get(CubeColor.BLUE, 0) >= 1 and unblocked_blue == 0:
                    player.money += 3

        # Red Ransomware
        unpaid_ransom = 0
        if unblocked_red > 0:
            cash_paid = min(player.money, unblocked_red)
            player.money -= cash_paid
            unpaid_ransom = unblocked_red - cash_paid

        # DTO Slush Fund
        potential_secret_loss = unpaid_ransom + unblocked_blue
        is_dto = bool(
            (player.company and player.company.code == CompanyCode.DTO)
        ) and player.is_ability_available(active_ver)
        if potential_secret_loss > 0 and is_dto:
            free_absorb = min(2, potential_secret_loss)
            absorbed_from_ransom = min(unpaid_ransom, free_absorb)
            unpaid_ransom -= absorbed_from_ransom
            remaining_free = free_absorb - absorbed_from_ransom
            unblocked_blue -= remaining_free
            potential_secret_loss -= free_absorb
            player.mark_ability_used(active_ver)

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

        # Unpaid Ransom Secret Loss
        if unpaid_ransom > 0:
            if flat_unpaid_ransom:
                player.secrets -= 1  # 1 Secret flat for any unpaid ransom
            else:
                player.secrets -= unpaid_ransom  # 1 Secret per unpaid $1

        player.money = max(0, player.money)
        player.patches = max(0, player.patches)

        # Blue Spyware
        if unblocked_blue > 0:
            player.secrets -= unblocked_blue

        # Patient Zero Check
        if player.secrets <= 0:
            player.is_patient_zero = True
            player.elimination_round = engine.state.current_round
            player.elimination_reason = "Total Breach (<= 0 Secrets)"
            player.breach_depth = max(0, -player.secrets)

        # Green Malware
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
            elif not remove_destruction_fallback:
                # Destruction Fallback (Baseline)
                if len(player.glitched_dice) > 0 or len(player.scanned_dice) > 0:
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
                    player.unfulfilled_destructions += 1
            else:
                # Remove Destruction Fallback: Fizzles, nothing destroyed!
                pass

    phase2_threat.resolve_player_defense_and_wear = custom_resolve

    results = {
        "rounds": [],
        "end_reasons": defaultdict(int),
        "survivors": [],
        "wipeouts": 0,
        "early_deaths": 0,
        "secrets_remaining": [],
        "winning_secrets": [],
        "destruction_occurrences": 0,
        "unpaid_ransom_occurrences": 0,
        "multi_unpaid_ransom_occurrences": 0,
    }

    try:
        for match_idx in range(num_matches):
            seed = base_seed + match_idx
            config = GameConfig(num_players=num_players)
            engine = GameEngine(config, seed=seed)

            # Play match
            engine.run_game()

            r = engine.state.current_round
            results["rounds"].append(r)
            results["end_reasons"][engine.state.end_reason] += 1
            
            surviving = [p for p in engine.state.players if not p.is_patient_zero]
            results["survivors"].append(len(surviving))
            if len(surviving) == 0:
                results["wipeouts"] += 1
            
            # Check early deaths (<= round 4)
            for p in engine.state.players:
                if p.is_patient_zero and getattr(p, "elimination_round", 99) <= 4:
                    results["early_deaths"] += 1
                if getattr(p, "unfulfilled_destructions", 0) > 0:
                    results["destruction_occurrences"] += 1

            if surviving:
                max_sec = max(p.secrets for p in surviving)
                results["winning_secrets"].append(max_sec)
                for p in surviving:
                    results["secrets_remaining"].append(p.secrets)

    finally:
        phase2_threat.resolve_player_defense_and_wear = orig_resolve

    return {
        "mean_rounds": sum(results["rounds"]) / len(results["rounds"]),
        "singularity_rate": results["end_reasons"][EndGameReason.SINGULARITY] / num_matches * 100,
        "patient_zero_rate": results["end_reasons"][EndGameReason.PATIENT_ZERO] / num_matches * 100,
        "wipeout_rate": results["wipeouts"] / num_matches * 100,
        "early_death_rate": results["early_deaths"] / (num_matches * num_players) * 100,
        "mean_winning_secrets": sum(results["winning_secrets"]) / len(results["winning_secrets"]) if results["winning_secrets"] else 0,
        "mean_survivor_secrets": sum(results["secrets_remaining"]) / len(results["secrets_remaining"]) if results["secrets_remaining"] else 0,
    }


def main():
    print("=" * 80)
    print("ROUGE AGENT: MONTE CARLO INVESTIGATION OF 3 PROPOSALS (1,000 Matches/Pod)")
    print("=" * 80)
    
    scenarios = [
        ("1. Baseline (v0.30.0)", False, False, False),
        ("2. Prop 1: Flexible 'Block 1 Any'", True, False, False),
        ("3. Prop 2: Flat Unpaid Ransom (1 Sec)", False, True, False),
        ("4. Prop 3: Remove Destruction Fallback", False, False, True),
        ("5. All 3 Proposals Combined", True, True, True),
    ]

    for num_p in [4, 3, 2]:
        print(f"\n--- {num_p}-PLAYER PODS ---")
        print(f"{'Scenario':<38} | {'Rounds':<7} | {'Sing %':<7} | {'PZ %':<7} | {'Wipe %':<7} | {'Early %':<7} | {'Win Sec':<7}")
        print("-" * 88)
        for label, flex, flat_r, no_destr in scenarios:
            res = run_pod_simulation(
                num_players=num_p,
                num_matches=1000,
                base_seed=42,
                enable_flexible_any=flex,
                flat_unpaid_ransom=flat_r,
                remove_destruction_fallback=no_destr,
            )
            print(f"{label:<38} | {res['mean_rounds']:<7.2f} | {res['singularity_rate']:<6.1f}% | {res['patient_zero_rate']:<6.1f}% | {res['wipeout_rate']:<6.1f}% | {res['early_death_rate']:<6.1f}% | {res['mean_winning_secrets']:<7.2f}")


if __name__ == "__main__":
    main()
