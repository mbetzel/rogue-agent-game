"""Monte Carlo batch simulation runner and stress-testing experiments."""

from __future__ import annotations

import argparse
import random
import statistics
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from sim.bots import (
    AccelerationistBot,
    AdaptiveBalancedBot,
    BaseBot,
    RecklessSaboteurBot,
    SecOpsTurtleBot,
    VentureGreedBot,
)
from sim.config import DieColor, EndGameReason, GameConfig
from sim.engine import EndGameResult, GameEngine
from sim.entities import get_all_variant_cards, get_all_version_cards


@dataclass
class ExperimentMetrics:
    """Aggregated telemetry metrics across a batch of Monte Carlo matches."""

    total_games: int
    mean_rounds: float
    min_rounds: int
    max_rounds: int
    std_rounds: float
    singularity_pct: float
    patient_zero_pct: float
    total_wipeout_pct: float
    round_limit_pct: float
    early_death_pct: float  # % games ending <= Round 4
    mean_dirty_income: float
    mean_contractors_hired: float = 0.0
    mean_rerolls_used: float = 0.0
    win_rates: Dict[str, float] = field(default_factory=dict)
    outlier_seeds: List[Dict] = field(default_factory=list)


def run_batch(
    config_factory: Callable[[], GameConfig],
    bot_factory: Callable[[], List[BaseBot]],
    num_runs: int = 1000,
    base_seed: int = 42,
    randomize_cards: bool = False,
) -> ExperimentMetrics:
    """Executes a Monte Carlo batch of matches with reproducible seeding."""
    round_counts: List[int] = []
    end_reasons: Dict[EndGameReason, int] = {reason: 0 for reason in EndGameReason}
    early_deaths = 0
    total_dirty_income = 0
    total_contractors_hired = 0
    total_rerolls_used = 0
    wins_by_bot: Dict[str, int] = {}
    outliers: List[Dict] = []

    all_variants = list(get_all_variant_cards().values())
    all_versions = get_all_version_cards()

    for run_idx in range(num_runs):
        seed = base_seed + run_idx
        config = config_factory()
        bots = bot_factory()

        variant_cards = None
        version_deck = None

        if randomize_cards:
            rng_setup = random.Random(seed * 17)
            # Pick 1 variant per colored die
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

            # Pick 1 v1.0, 1 v2.0, 1 v3.0
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

        result: EndGameResult = engine.run_game()

        round_counts.append(result.total_rounds)
        end_reasons[result.end_reason] = end_reasons.get(result.end_reason, 0) + 1

        if result.total_rounds <= 4:
            early_deaths += 1

        # Track dirty income, contractors, and rerolls across players
        dirty_taken = sum(r.get("total_dirty_income", 0) for r in result.rankings)
        total_dirty_income += dirty_taken
        contractors_hired = sum(r.get("total_contractors_hired", 0) for r in result.rankings)
        total_contractors_hired += contractors_hired
        rerolls_used = sum(r.get("total_rerolls_used", 0) for r in result.rankings)
        total_rerolls_used += rerolls_used

        # Track winner
        if result.rankings:
            winner = result.rankings[0]
            w_name = winner["bot_name"]
            wins_by_bot[w_name] = wins_by_bot.get(w_name, 0) + 1

        # Outlier tracking: ultra-short games (<= 3 rounds) or ultra-long games (>= 20 rounds) or wipeouts
        if (
            result.total_rounds <= 3
            or result.total_rounds >= 20
            or result.is_total_wipeout
        ):
            if len(outliers) < 10:  # Keep first 10 outliers
                outliers.append(
                    {
                        "seed": seed,
                        "rounds": result.total_rounds,
                        "end_reason": result.end_reason.value,
                        "is_wipeout": result.is_total_wipeout,
                    }
                )

    mean_rounds = statistics.mean(round_counts)
    std_rounds = statistics.stdev(round_counts) if len(round_counts) > 1 else 0.0
    win_rates = {bot: count / num_runs for bot, count in wins_by_bot.items()}

    return ExperimentMetrics(
        total_games=num_runs,
        mean_rounds=mean_rounds,
        min_rounds=min(round_counts),
        max_rounds=max(round_counts),
        std_rounds=std_rounds,
        singularity_pct=end_reasons[EndGameReason.SINGULARITY] / num_runs,
        patient_zero_pct=end_reasons[EndGameReason.PATIENT_ZERO] / num_runs,
        total_wipeout_pct=end_reasons[EndGameReason.TOTAL_WIPEOUT] / num_runs,
        round_limit_pct=end_reasons[EndGameReason.ROUND_LIMIT] / num_runs,
        early_death_pct=early_deaths / num_runs,
        mean_dirty_income=total_dirty_income / num_runs,
        mean_contractors_hired=total_contractors_hired / num_runs,
        mean_rerolls_used=total_rerolls_used / num_runs,
        win_rates=win_rates,
        outlier_seeds=outliers,
    )


# =====================================================================
# Preset Experiment Suites (Experiments 1–4 from PLAN.md)
# =====================================================================

def run_experiment_1(runs: int = 500, base_seed: int = 42) -> None:
    """Experiment 1: Starting Resources Grid ($3-$9 Money x 4-10 Secrets)."""
    print("\n========================================================")
    print("Experiment 1: Starting Resources Grid (Money x Secrets)")
    print("========================================================\n")

    money_options = [3, 5, 7, 9]
    secret_options = [4, 6, 8, 10]

    print("| Money | Secrets | Mean Rounds | Min | Max | Early Death (<5) | Singularity % | Wipeout % | Contractors/Gm | Rerolls/Gm |")
    print("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

    for money in money_options:
        for secrets in secret_options:
            def cfg_fn(m=money, s=secrets):
                return GameConfig(num_players=4, starting_money=m, starting_secrets=s)

            def bots_fn():
                return [
                    AdaptiveBalancedBot(0),
                    SecOpsTurtleBot(1),
                    VentureGreedBot(2),
                    AccelerationistBot(3),
                ]

            metrics = run_batch(cfg_fn, bots_fn, num_runs=runs, base_seed=base_seed)
            print(
                f"| ${money} | {secrets} | {metrics.mean_rounds:.2f} | "
                f"{metrics.min_rounds} | {metrics.max_rounds} | "
                f"{metrics.early_death_pct * 100:.1f}% | "
                f"{metrics.singularity_pct * 100:.1f}% | "
                f"{metrics.total_wipeout_pct * 100:.1f}% | "
                f"{metrics.mean_contractors_hired:.2f} | "
                f"{metrics.mean_rerolls_used:.2f} |"
            )


def run_experiment_2(runs: int = 500, base_seed: int = 42) -> None:
    """Experiment 2: Player-Count Scaling (2P vs 3P vs 4P)."""
    print("\n========================================================")
    print("Experiment 2: Player-Count Scaling (2P, 3P, 4P)")
    print("========================================================\n")

    print("| Players | Mean Rounds | Std Dev | Singularity % | Patient Zero % | Wipeout % | Dirty Income/Gm | Contractors/Gm | Rerolls/Gm |")
    print("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

    bot_pool = [
        AdaptiveBalancedBot(0),
        SecOpsTurtleBot(1),
        VentureGreedBot(2),
        AccelerationistBot(3),
    ]

    for p_count in [2, 3, 4]:
        def cfg_fn(p=p_count):
            return GameConfig(num_players=p)

        def bots_fn(p=p_count):
            return bot_pool[:p]

        metrics = run_batch(cfg_fn, bots_fn, num_runs=runs, base_seed=base_seed)
        print(
            f"| {p_count}P | {metrics.mean_rounds:.2f} | {metrics.std_rounds:.2f} | "
            f"{metrics.singularity_pct * 100:.1f}% | "
            f"{metrics.patient_zero_pct * 100:.1f}% | "
            f"{metrics.total_wipeout_pct * 100:.1f}% | "
            f"{metrics.mean_dirty_income:.2f} | "
            f"{metrics.mean_contractors_hired:.2f} | "
            f"{metrics.mean_rerolls_used:.2f} |"
        )


def run_experiment_3(runs: int = 500, base_seed: int = 42) -> None:
    """Experiment 3: Dirty Income ($2-$4) & Patch Cost ($1-$3)."""
    print("\n========================================================")
    print("Experiment 3: Dirty Income & Patch Cost Economy")
    print("========================================================\n")

    print("| Dirty Income | Patch Cost | Mean Rounds | Mean Dirty Income | Wipeout % | Contractors/Gm | Rerolls/Gm |")
    print("| :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

    for dirty_cash in [2, 3, 4]:
        for patch_cost in [1, 2, 3]:
            def cfg_fn(d=dirty_cash, p=patch_cost):
                return GameConfig(num_players=4, dirty_income_cash=d, patch_cash_cost=p)

            def bots_fn():
                return [
                    AdaptiveBalancedBot(0),
                    SecOpsTurtleBot(1),
                    VentureGreedBot(2),
                    AccelerationistBot(3),
                ]

            metrics = run_batch(cfg_fn, bots_fn, num_runs=runs, base_seed=base_seed)
            print(
                f"| ${dirty_cash} | ${patch_cost} | {metrics.mean_rounds:.2f} | "
                f"{metrics.mean_dirty_income:.2f} | "
                f"{metrics.total_wipeout_pct * 100:.1f}% | "
                f"{metrics.mean_contractors_hired:.2f} | "
                f"{metrics.mean_rerolls_used:.2f} |"
            )


def run_experiment_4(runs: int = 1000, base_seed: int = 42) -> None:
    """Experiment 4: Ecosystem Tournament across all 5 Bot Archetypes + Card Variations."""
    print("\n========================================================")
    print("Experiment 4: Ecosystem Tournament (5 Archetypes)")
    print("========================================================\n")

    # 4-player pod combinations testing all archetypes
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
        print(f"### {pod_name}")
        metrics = run_batch(
            lambda: GameConfig(num_players=4),
            bots_fn,
            num_runs=runs,
            base_seed=base_seed,
            randomize_cards=True,
        )
        print(f"- **Mean Rounds:** {metrics.mean_rounds:.2f} (±{metrics.std_rounds:.2f})")
        print(f"- **End Triggers:** Singularity {metrics.singularity_pct * 100:.1f}%, Patient Zero {metrics.patient_zero_pct * 100:.1f}%, Wipeout {metrics.total_wipeout_pct * 100:.1f}%")
        print(f"- **Tactical Telemetry:** Contractors Hired/Gm {metrics.mean_contractors_hired:.2f}, Yahtzee Rerolls/Gm {metrics.mean_rerolls_used:.2f}")
        print("- **Win Rates:**")
        for bot_name, rate in sorted(metrics.win_rates.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {bot_name}: {rate * 100:.1f}%")
        if metrics.outlier_seeds:
            print(f"- **Sample Outlier Seeds:** {metrics.outlier_seeds[:3]}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Rogue Agent Monte Carlo Simulation Suite")
    parser.add_argument(
        "--experiment",
        "-e",
        choices=["1", "2", "3", "4", "all"],
        default="all",
        help="Which experiment to run (1-4 or all)",
    )
    parser.add_argument(
        "--runs",
        "-n",
        type=int,
        default=500,
        help="Number of games to simulate per parameter cell",
    )
    parser.add_argument(
        "--seed",
        "-s",
        type=int,
        default=42,
        help="Base random seed for reproducibility",
    )

    args = parser.parse_args()

    if args.experiment in ("1", "all"):
        run_experiment_1(runs=args.runs, base_seed=args.seed)
    if args.experiment in ("2", "all"):
        run_experiment_2(runs=args.runs, base_seed=args.seed)
    if args.experiment in ("3", "all"):
        run_experiment_3(runs=args.runs, base_seed=args.seed)
    if args.experiment in ("4", "all"):
        run_experiment_4(runs=args.runs, base_seed=args.seed)


if __name__ == "__main__":
    main()
