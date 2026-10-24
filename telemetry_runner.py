"""Comprehensive Phase 2 Monte Carlo telemetry runner for Rogue Agent.
Executes Experiments 1 to 4 with statistical hygiene and granular telemetry.
"""

from __future__ import annotations

import copy
import json
import random
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from sim.bots import (
    AccelerationistBot,
    AdaptiveBalancedBot,
    BaseBot,
    RecklessSaboteurBot,
    SecOpsTurtleBot,
    VentureGreedBot,
)
from sim.config import CubeColor, DieColor, EndGameReason, GameConfig, ShieldColor
from sim.engine import EndGameResult, GameEngine
import sim.entities as entities


def run_experiment_batch(
    config_factory: Callable[[], GameConfig],
    bot_factory: Callable[[], List[BaseBot]],
    num_runs: int = 1000,
    base_seed: int = 42,
    randomize_cards: bool = False,
    colored_shield_strength: int = 2,
) -> Dict[str, Any]:
    """Runs a batch of games and computes granular telemetry."""
    round_counts: List[int] = []
    end_reasons: Dict[str, int] = defaultdict(int)
    pz_elim_reasons: Dict[str, int] = defaultdict(int)
    bot_wins: Dict[str, int] = defaultdict(int)
    bot_scores: Dict[str, List[int]] = defaultdict(list)
    bot_pz_counts: Dict[str, int] = defaultdict(int)
    
    total_dirty_income_list: List[int] = []
    end_unpatched_dice_list: List[float] = []
    end_patch_tokens_list: List[float] = []
    
    outliers_short: List[Dict[str, Any]] = []
    outliers_long: List[Dict[str, Any]] = []
    outliers_wipeout: List[Dict[str, Any]] = []

    all_variants = list(entities.get_all_variant_cards().values())
    all_versions = entities.get_all_version_cards()

    # Monkey patch entities.create_colored_die if shield strength != 2
    orig_create_colored_die = entities.create_colored_die
    import sim.engine as engine_module

    def custom_create_colored_die(color: DieColor, die_id: int, variant_card: Optional[entities.VariantCard] = None):
        die = orig_create_colored_die(color, die_id, variant_card)
        if colored_shield_strength != 2:
            new_faces = []
            for face in die.faces:
                if face.is_shield and not face.is_star:
                    new_faces.append(
                        entities.Face(
                            name=f"Block {colored_shield_strength} {face.shield_color.value.capitalize()}",
                            block_amount=colored_shield_strength,
                            shield_color=face.shield_color,
                        )
                    )
                else:
                    new_faces.append(face)
            die.faces = new_faces
        return die

    entities.create_colored_die = custom_create_colored_die
    engine_module.create_colored_die = custom_create_colored_die

    try:
        for run_idx in range(num_runs):
            seed = base_seed + run_idx
            config = config_factory()
            bots = bot_factory()

            variant_cards = None
            version_deck = None

            if randomize_cards:
                rng_setup = random.Random(seed * 17)
                variant_cards = {}
                for color in [
                    DieColor.RED,
                    DieColor.BLUE,
                    DieColor.GREEN,
                    DieColor.YELLOW,
                    DieColor.PURPLE,
                ]:
                    matching = [v for v in all_variants if v.die_color == color]
                    variant_cards[color] = rng_setup.choice(matching)

                v1_pool = [v for v in all_versions if v.version_str == "v1.0"]
                v2_pool = [v for v in all_versions if v.version_str == "v2.0"]
                v3_pool = [v for v in all_versions if v.version_str == "v3.0"]
                version_deck = [
                    rng_setup.choice(v1_pool),
                    rng_setup.choice(v2_pool),
                    rng_setup.choice(v3_pool),
                ]

            engine = GameEngine(
                config=config,
                bots=bots,
                seed=seed,
                variant_cards=variant_cards,
                version_deck=version_deck,
            )
            result = engine.run_game()

            round_counts.append(result.total_rounds)
            end_reasons[result.end_reason.value] += 1

            # Granular PZ reasons
            insolvency_in_game = False
            breach_in_game = False
            for p in result.rankings:
                bot_scores[p["bot_name"]].append(p["portfolio_value"])
                if p["is_patient_zero"]:
                    bot_pz_counts[p["bot_name"]] += 1
                    reason = p.get("elimination_reason", "")
                    if "Insolvency" in reason:
                        insolvency_in_game = True
                    if "Breach" in reason:
                        breach_in_game = True
            
            if result.end_reason == EndGameReason.PATIENT_ZERO:
                if insolvency_in_game and not breach_in_game:
                    pz_elim_reasons["Insolvency"] += 1
                elif breach_in_game and not insolvency_in_game:
                    pz_elim_reasons["Total Breach"] += 1
                elif insolvency_in_game and breach_in_game:
                    pz_elim_reasons["Both"] += 1
                else:
                    pz_elim_reasons["Other"] += 1

            # Winner tracking
            if result.rankings:
                winner_name = result.rankings[0]["bot_name"]
                bot_wins[winner_name] += 1

            # Economy metrics
            dirty_taken = sum(p["total_dirty_income"] for p in result.rankings)
            total_dirty_income_list.append(dirty_taken)

            unpatched_avg = statistics.mean([p["unpatched_dice_count"] for p in result.rankings])
            end_unpatched_dice_list.append(unpatched_avg)

            # Patch tokens from last snapshot
            if result.telemetry_history:
                last_snap = result.telemetry_history[-1].player_snapshots
                patches_avg = statistics.mean([p["patches"] for p in last_snap])
                end_patch_tokens_list.append(patches_avg)
            else:
                end_patch_tokens_list.append(config.starting_patches)

            # Outlier tracking
            if result.total_rounds <= 3 and len(outliers_short) < 5:
                outliers_short.append({
                    "seed": seed,
                    "rounds": result.total_rounds,
                    "end_reason": result.end_reason.value,
                    "wipeout": result.is_total_wipeout,
                })
            if result.total_rounds >= 6 and len(outliers_long) < 5:
                outliers_long.append({
                    "seed": seed,
                    "rounds": result.total_rounds,
                    "end_reason": result.end_reason.value,
                    "wipeout": result.is_total_wipeout,
                })
            if result.is_total_wipeout and len(outliers_wipeout) < 5:
                outliers_wipeout.append({
                    "seed": seed,
                    "rounds": result.total_rounds,
                    "end_reason": result.end_reason.value,
                })

    finally:
        entities.create_colored_die = orig_create_colored_die
        engine_module.create_colored_die = orig_create_colored_die

    early_deaths = sum(1 for r in round_counts if r <= 4)

    return {
        "num_runs": num_runs,
        "mean_rounds": statistics.mean(round_counts),
        "std_rounds": statistics.stdev(round_counts) if len(round_counts) > 1 else 0.0,
        "min_rounds": min(round_counts),
        "max_rounds": max(round_counts),
        "early_death_pct": early_deaths / num_runs * 100.0,
        "singularity_pct": end_reasons.get("singularity", 0) / num_runs * 100.0,
        "patient_zero_pct": end_reasons.get("patient_zero", 0) / num_runs * 100.0,
        "wipeout_pct": end_reasons.get("total_wipeout", 0) / num_runs * 100.0,
        "round_limit_pct": end_reasons.get("round_limit", 0) / num_runs * 100.0,
        "pz_insolvency_pct": pz_elim_reasons.get("Insolvency", 0) / num_runs * 100.0,
        "pz_breach_pct": pz_elim_reasons.get("Total Breach", 0) / num_runs * 100.0,
        "pz_both_pct": pz_elim_reasons.get("Both", 0) / num_runs * 100.0,
        "mean_dirty_income_per_game": statistics.mean(total_dirty_income_list),
        "mean_dirty_income_per_player": statistics.mean(total_dirty_income_list) / config_factory().num_players,
        "mean_end_unpatched_dice": statistics.mean(end_unpatched_dice_list),
        "mean_end_patch_tokens": statistics.mean(end_patch_tokens_list),
        "win_rates": {bot: (count / num_runs) * 100.0 for bot, count in bot_wins.items()},
        "mean_scores": {bot: statistics.mean(scores) if scores else 0.0 for bot, scores in bot_scores.items()},
        "pz_rates": {bot: (count / num_runs) * 100.0 for bot, count in bot_pz_counts.items()},
        "outliers_short": outliers_short,
        "outliers_long": outliers_long,
        "outliers_wipeout": outliers_wipeout,
    }


def execute_all_experiments(runs: int = 1000, base_seed: int = 42) -> Dict[str, Any]:
    all_results = {}

    print(f"Starting Phase 2 Sweeps (runs={runs}, base_seed={base_seed})...")

    # =========================================================================
    # Experiment 1: Starting Resources Grid
    # =========================================================================
    print("Executing Experiment 1: Starting Resources Grid (16 cells)...")
    exp1_data = []
    money_vals = [3, 5, 7, 9]
    secret_vals = [4, 6, 8, 10]

    for m in money_vals:
        for s in secret_vals:
            print(f"  Exp 1: Money=${m}, Secrets={s}...")
            metrics = run_experiment_batch(
                config_factory=lambda m=m, s=s: GameConfig(num_players=4, starting_money=m, starting_secrets=s),
                bot_factory=lambda: [
                    AdaptiveBalancedBot(0),
                    SecOpsTurtleBot(1),
                    VentureGreedBot(2),
                    AccelerationistBot(3),
                ],
                num_runs=runs,
                base_seed=base_seed,
            )
            metrics["money"] = m
            metrics["secrets"] = s
            exp1_data.append(metrics)
    all_results["exp1"] = exp1_data

    # =========================================================================
    # Experiment 2: Player-Count Scaling (2P, 3P, 4P)
    # =========================================================================
    print("Executing Experiment 2: Player-Count Scaling (3 cells)...")
    exp2_data = []
    bot_pool = [
        AdaptiveBalancedBot(0),
        SecOpsTurtleBot(1),
        VentureGreedBot(2),
        AccelerationistBot(3),
    ]

    for p in [2, 3, 4]:
        print(f"  Exp 2: {p} Players...")
        metrics = run_experiment_batch(
            config_factory=lambda p=p: GameConfig(num_players=p),
            bot_factory=lambda p=p: [copy.copy(b) for b in bot_pool[:p]],
            num_runs=runs,
            base_seed=base_seed,
        )
        metrics["players"] = p
        exp2_data.append(metrics)
    all_results["exp2"] = exp2_data

    # =========================================================================
    # Experiment 3: Dirty Income & Wear Economy
    # Dirty Income ($2, $3, $4) x Patch Cost ($1, $2, $3) x Shield (1 vs 2)
    # =========================================================================
    print("Executing Experiment 3: Dirty Income & Wear Economy (18 cells)...")
    exp3_data = []
    for shield_strength in [2, 1]:
        for d in [2, 3, 4]:
            for pc in [1, 2, 3]:
                print(f"  Exp 3: Shield={shield_strength}, Dirty=${d}, PatchCost=${pc}...")
                metrics = run_experiment_batch(
                    config_factory=lambda d=d, pc=pc: GameConfig(
                        num_players=4,
                        dirty_income_cash=d,
                        patch_cash_cost=pc,
                    ),
                    bot_factory=lambda: [
                        AdaptiveBalancedBot(0),
                        SecOpsTurtleBot(1),
                        VentureGreedBot(2),
                        AccelerationistBot(3),
                    ],
                    num_runs=runs,
                    base_seed=base_seed,
                    colored_shield_strength=shield_strength,
                )
                metrics["shield_strength"] = shield_strength
                metrics["dirty_cash"] = d
                metrics["patch_cost"] = pc
                exp3_data.append(metrics)
    all_results["exp3"] = exp3_data

    # =========================================================================
    # Experiment 4: Ecosystem Tournament
    # =========================================================================
    print("Executing Experiment 4: Ecosystem Tournament (3 pods x randomized setups)...")
    exp4_data = []
    pods = [
        (
            "Pod A (Balanced, Turtle, Greed, Accel)",
            lambda: [
                AdaptiveBalancedBot(0),
                SecOpsTurtleBot(1),
                VentureGreedBot(2),
                AccelerationistBot(3),
            ],
        ),
        (
            "Pod B (Balanced, Turtle, Saboteur, Accel)",
            lambda: [
                AdaptiveBalancedBot(0),
                SecOpsTurtleBot(1),
                RecklessSaboteurBot(2),
                AccelerationistBot(3),
            ],
        ),
        (
            "Pod C (Balanced, Greed, Saboteur, Accel)",
            lambda: [
                AdaptiveBalancedBot(0),
                VentureGreedBot(1),
                RecklessSaboteurBot(2),
                AccelerationistBot(3),
            ],
        ),
    ]

    for pod_name, bots_fn in pods:
        print(f"  Exp 4: {pod_name}...")
        metrics = run_experiment_batch(
            config_factory=lambda: GameConfig(num_players=4),
            bot_factory=bots_fn,
            num_runs=runs,
            base_seed=base_seed,
            randomize_cards=True,
        )
        metrics["pod_name"] = pod_name
        exp4_data.append(metrics)
    all_results["exp4"] = exp4_data

    print("Phase 2 Sweeps Complete!")
    return all_results


if __name__ == "__main__":
    results = execute_all_experiments(runs=1000, base_seed=42)
    with open("phase2_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Results saved to phase2_results.json")
