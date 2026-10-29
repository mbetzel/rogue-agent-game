"""Archetype Tournament Sweep with Face 5 Glitch (Wear 1 Active Die).

Tests all 6 consultancy archetypes:
1. The Acoustic (Baffle Echo)
2. The Phreaker (Magnetic Splice)
3. The Prodigy (Brute-Force Bypass)
4. The Spook (Slush Fund)
5. The Cipher (Algorithmic Arbitrage)
6. The Operator (Redundant Crew)

Measures win rate, survival rate, portfolio score, and ability utilization for The Prodigy
under the new Glitch face rule.
"""

from __future__ import annotations

import random
import statistics
from typing import Any, Dict, List

from sim.bots import (
    AccelerationistBot,
    AdaptiveBalancedBot,
    SecOpsTurtleBot,
    VentureGreedBot,
)
from sim.config import GameConfig
from sim.engine import GameEngine
from sim.entities import ArchetypeCode, get_archetype_by_code, get_random_setup
import sim.entities
import sim.engine.phase1_boot
import sim.engine.phase3_ops

from scripts.test_wear_glitch_face import create_colored_die_wear_glitch, _ORIGINAL_CREATE_COLORED_DIE


def run_archetype_tournament(num_runs: int = 1000, base_seed: int = 42):
    # Set up wear glitch face
    orig_p1 = sim.engine.phase1_boot.execute_phase_1

    def execute_phase_1_with_wear_glitch(engine):
        commitments = orig_p1(engine)
        for player in engine.state.players:
            wear_glitch_count = sum(
                1 for d in player.ready_dice + player.contractor_dice
                if d.current_face and d.current_face.is_glitch and "Wear Active" in d.current_face.name
            )
            for _ in range(wear_glitch_count):
                if player.contractor_dice:
                    player.contractor_dice.pop(0)
                    engine.state.contractor_supply += 1
                elif player.ready_dice:
                    gray_dice = [d for d in player.ready_dice if d.color == sim.config.DieColor.GRAY]
                    if gray_dice:
                        target = gray_dice[0]
                    else:
                        target = min(player.ready_dice, key=lambda d: getattr(d, "vp", 0))
                    player.ready_dice.remove(target)
                    player.unpatched_dice.append(target)
        return commitments

    sim.engine.phase1_boot.execute_phase_1 = execute_phase_1_with_wear_glitch
    sim.engine.core.execute_phase_1 = execute_phase_1_with_wear_glitch
    sim.entities.create_colored_die = create_colored_die_wear_glitch
    sim.engine.phase3_ops.create_colored_die = create_colored_die_wear_glitch

    archetype_codes = [
        ArchetypeCode.ACOUSTIC,
        ArchetypeCode.PHREAKER,
        ArchetypeCode.PRODIGY,
        ArchetypeCode.SPOOK,
        ArchetypeCode.CIPHER,
        ArchetypeCode.OPERATOR,
    ]

    # In 4P pods, 4 archetypes are randomly dealt each match.
    # We track performance per archetype across 3,000 matches.
    games_played = {code: 0 for code in archetype_codes}
    wins = {code: 0 for code in archetype_codes}
    survivals = {code: 0 for code in archetype_codes}
    scores = {code: [] for code in archetype_codes}
    prodigy_ability_uses = []

    for run_idx in range(num_runs):
        seed = base_seed + run_idx
        config = GameConfig(num_players=4)

        bots = [
            AdaptiveBalancedBot(0),
            AdaptiveBalancedBot(1),
            AdaptiveBalancedBot(2),
            AdaptiveBalancedBot(3),
        ]

        rng_setup = random.Random(seed * 17)
        variant_cards, version_deck = get_random_setup(rng_setup)

        # Deal 4 distinct archetypes
        dealt_archetypes = rng_setup.sample(archetype_codes, 4)

        engine = GameEngine(
            config=config,
            bots=bots,
            seed=seed,
            variant_cards=variant_cards,
            version_deck=version_deck,
        )

        # Assign dealt archetypes
        for idx, arch_code in enumerate(dealt_archetypes):
            engine.state.players[idx].archetype = get_archetype_by_code(arch_code)
            games_played[arch_code] += 1

        while not engine.state.game_over:
            engine.run_round()

        res = engine.evaluate_end_game()
        if res.rankings:
            winner = res.rankings[0]
            w_code = winner["archetype_code"]
            if w_code:
                wins[ArchetypeCode(w_code)] += 1

        for r in res.rankings:
            code = ArchetypeCode(r["archetype_code"])
            if not r["is_patient_zero"]:
                survivals[code] += 1
                scores[code].append(r["portfolio_value"])
            if code == ArchetypeCode.PRODIGY:
                p_state = [p for p in engine.state.players if p.archetype.code == ArchetypeCode.PRODIGY][0]
                prodigy_ability_uses.append(sum([
                    1 if p_state.ability_v1_status.value == "USED" else 0,
                    1 if p_state.ability_v2_status.value == "USED" else 0,
                    1 if p_state.ability_v3_status.value == "USED" else 0,
                ]))

    # Restore
    sim.engine.phase1_boot.execute_phase_1 = orig_p1
    sim.engine.core.execute_phase_1 = orig_p1
    sim.entities.create_colored_die = _ORIGINAL_CREATE_COLORED_DIE
    sim.engine.phase3_ops.create_colored_die = _ORIGINAL_CREATE_COLORED_DIE

    print("=" * 80)
    print("ARCHETYPE TOURNAMENT TELEMETRY (4P Pods, N=1,000 matches, Random Archetypes)")
    print("Target Balance: ~25.0% win rate per dealt match (or 16.7% across total field)")
    print("=" * 80)
    print(f"{'Archetype':<20} | {'Matches':<8} | {'Wins':<6} | {'Win %':<8} | {'Survival %':<12} | {'Avg Score':<10}")
    print("-" * 74)

    for code in archetype_codes:
        n_games = games_played[code]
        n_wins = wins[code]
        win_pct = (n_wins / n_games * 100) if n_games > 0 else 0
        surv_pct = (survivals[code] / n_games * 100) if n_games > 0 else 0
        avg_sc = statistics.mean(scores[code]) if scores[code] else 0
        name = get_archetype_by_code(code).name
        print(f"{name:<20} | {n_games:<8} | {n_wins:<6} | {win_pct:>5.1f}%  | {surv_pct:>9.1f}%  | {avg_sc:>7.1f} VP")

    if prodigy_ability_uses:
        print(f"\nAverage Prodigy Ability Triggers per Game: {statistics.mean(prodigy_ability_uses):.2f} / 3.0 max")


if __name__ == "__main__":
    run_archetype_tournament(num_runs=1000)
