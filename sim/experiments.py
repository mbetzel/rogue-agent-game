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
from sim.entities import (
    VariantCard,
    VersionCard,
    get_all_variant_cards,
    get_all_version_cards,
    get_default_variant_cards,
    get_default_version_deck,
    get_random_setup,
    get_roadmap_deck,
)


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
    mean_winning_score: float = 0.0
    mean_scores: Dict[str, float] = field(default_factory=dict)
    outlier_seeds: List[Dict] = field(default_factory=list)


def run_batch(
    config_factory: Callable[[], GameConfig],
    bot_factory: Callable[[], List[BaseBot]],
    num_runs: int = 1000,
    base_seed: int = 42,
    randomize_cards: bool = False,
    variant_cards: Optional[Dict[DieColor, VariantCard]] = None,
    version_deck: Optional[List[VersionCard]] = None,
) -> ExperimentMetrics:
    """Executes a Monte Carlo batch of matches with reproducible seeding."""
    round_counts: List[int] = []
    end_reasons: Dict[EndGameReason, int] = {reason: 0 for reason in EndGameReason}
    early_deaths = 0
    total_dirty_income = 0
    total_contractors_hired = 0
    total_rerolls_used = 0
    wins_by_bot: Dict[str, int] = {}
    winning_scores: List[float] = []
    scores_by_bot: Dict[str, List[float]] = {}
    outliers: List[Dict] = []

    for run_idx in range(num_runs):
        seed = base_seed + run_idx
        config = config_factory()
        bots = bot_factory()

        run_variant_cards = variant_cards
        run_version_deck = version_deck

        if randomize_cards:
            rng_setup = random.Random(seed * 17)
            run_variant_cards, run_version_deck = get_random_setup(rng_setup)

        engine = GameEngine(
            config=config,
            bots=bots,
            seed=seed,
            variant_cards=run_variant_cards,
            version_deck=run_version_deck,
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

        # Track winner and scores
        if result.rankings:
            winner = result.rankings[0]
            w_name = winner["bot_name"]
            wins_by_bot[w_name] = wins_by_bot.get(w_name, 0) + 1
            winning_scores.append(float(winner["net_score"]))
            for r in result.rankings:
                b_name = r["bot_name"]
                if b_name not in scores_by_bot:
                    scores_by_bot[b_name] = []
                scores_by_bot[b_name].append(float(r["net_score"]))

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
    mean_winning_score = statistics.mean(winning_scores) if winning_scores else 0.0
    mean_scores = {
        b_name: statistics.mean(scores)
        for b_name, scores in scores_by_bot.items()
    }

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
        mean_winning_score=mean_winning_score,
        mean_scores=mean_scores,
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


def run_experiment_5a(runs: int = 500, base_seed: int = 42) -> None:
    """Experiment 5a: Version Directives Benchmark."""
    print("\n========================================================")
    print("Experiment 5a: Version Directives Benchmark")
    print("========================================================\n")

    all_versions = get_all_version_cards()
    roadmaps = [
        ("Baseline Roadmap (Script Kiddie / RaaS / Zero-Day)", [all_versions[0], all_versions[2], all_versions[4]]),
        ("Data Scraper v1.0 (+$1 Starting Money)", [all_versions[1], all_versions[2], all_versions[4]]),
        ("Polymorphic Worm v2.0 (1 Free Reroll)", [all_versions[0], all_versions[3], all_versions[4]]),
        ("Corrupted Kernel v3.0 (Black Attack Boost)", [all_versions[0], all_versions[2], all_versions[5]]),
        ("All-Alternates Roadmap", [all_versions[1], all_versions[3], all_versions[5]]),
    ]

    print("| Roadmap / Directive | Mean Rounds | Singularity % | Patient Zero % | Wipeout % | Mean Win VP | Top Bot (Win %) |")
    print("| :--- | :---: | :---: | :---: | :---: | :---: | :--- |")

    for name, deck in roadmaps:
        def cfg_fn():
            return GameConfig(num_players=4)

        def bots_fn():
            return [
                AdaptiveBalancedBot(0),
                SecOpsTurtleBot(1),
                VentureGreedBot(2),
                AccelerationistBot(3),
            ]

        metrics = run_batch(cfg_fn, bots_fn, num_runs=runs, base_seed=base_seed, version_deck=deck)
        top_bot = max(metrics.win_rates.items(), key=lambda x: x[1]) if metrics.win_rates else ("None", 0.0)
        print(
            f"| {name} | {metrics.mean_rounds:.2f} | "
            f"{metrics.singularity_pct * 100:.1f}% | "
            f"{metrics.patient_zero_pct * 100:.1f}% | "
            f"{metrics.total_wipeout_pct * 100:.1f}% | "
            f"{metrics.mean_winning_score:.1f} | "
            f"{top_bot[0]} ({top_bot[1] * 100:.1f}%) |"
        )


def run_experiment_5b(runs: int = 500, base_seed: int = 42) -> None:
    """Experiment 5b: Colored Module Variant Benchmark (R1-R3, B1-B3, G1-G3, Y1-Y3, P1-P3)."""
    print("\n========================================================")
    print("Experiment 5b: Colored Module Variant Benchmark")
    print("========================================================\n")

    all_vars = get_all_variant_cards()
    variant_codes = [
        "R1", "R2", "R3",
        "B1", "B2", "B3",
        "G1", "G2", "G3",
        "Y1", "Y2", "Y3",
        "P1", "P2", "P3",
    ]

    print("| Code | Card Name | Color | Mean Rounds | Singularity % | Wipeout % | Mean Win VP | Top Bot (Win %) |")
    print("| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |")

    for code in variant_codes:
        card = all_vars[code]
        custom_vars = get_default_variant_cards().copy()
        custom_vars[card.die_color] = card

        def cfg_fn():
            return GameConfig(num_players=4)

        def bots_fn():
            return [
                AdaptiveBalancedBot(0),
                SecOpsTurtleBot(1),
                VentureGreedBot(2),
                AccelerationistBot(3),
            ]

        metrics = run_batch(cfg_fn, bots_fn, num_runs=runs, base_seed=base_seed, variant_cards=custom_vars)
        top_bot = max(metrics.win_rates.items(), key=lambda x: x[1]) if metrics.win_rates else ("None", 0.0)
        is_baseline = " (Baseline)" if code in ("R1", "B1", "G1", "Y1", "P1") else ""
        print(
            f"| {code} | {card.name}{is_baseline} | {card.die_color.value.capitalize()} | "
            f"{metrics.mean_rounds:.2f} | "
            f"{metrics.singularity_pct * 100:.1f}% | "
            f"{metrics.total_wipeout_pct * 100:.1f}% | "
            f"{metrics.mean_winning_score:.1f} | "
            f"{top_bot[0]} ({top_bot[1] * 100:.1f}%) |"
        )


def run_experiment_5(runs: int = 500, base_seed: int = 42) -> None:
    """Experiment 5: Version Directives & Colored Module Variants Full Suite."""
    run_experiment_5a(runs=runs, base_seed=base_seed)
    run_experiment_5b(runs=runs, base_seed=base_seed)


def run_experiment_6(runs: int = 500, base_seed: int = 42) -> None:
    """Experiment 6: 4-Way Roadmap Matrix Benchmark across 4P, 3P, and 2P (v0.8.2 Asymmetric Payloads)."""
    print("\n========================================================")
    print("Experiment 6: 4-Way Roadmap Matrix Benchmark (v0.8.2)")
    print("========================================================\n")

    paths = [
        (1, "Path 1 (Kinetic: RaaS / Corrupted Kernel)"),
        (2, "Path 2 (Contagion: Worm / Zero-Day)"),
        (3, "Path 3 (Mixed A: RaaS / Zero-Day)"),
        (4, "Path 4 (Mixed B: Worm / Corrupted Kernel)"),
    ]
    player_counts = [4, 3, 2]
    all_results = []

    print("### 1. Pacing & Triggers Telemetry")
    print("| Path | Players | Mean Rounds (Std) | Singularity % | Patient Zero % | Wipeout % | Early Death % |")
    print("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")

    for path_id, path_name in paths:
        deck = get_roadmap_deck(path_id)
        for p_count in player_counts:
            def cfg_fn(p=p_count):
                return GameConfig(num_players=p)

            def bots_fn(p=p_count):
                return [
                    AdaptiveBalancedBot(0),
                    SecOpsTurtleBot(1),
                    VentureGreedBot(2),
                    AccelerationistBot(3),
                ][:p]

            metrics = run_batch(cfg_fn, bots_fn, num_runs=runs, base_seed=base_seed, version_deck=deck)
            all_results.append((path_name, p_count, metrics))
            print(
                f"| {path_name} | {p_count}P | {metrics.mean_rounds:.2f} (±{metrics.std_rounds:.2f}) | "
                f"{metrics.singularity_pct * 100:.1f}% | "
                f"{metrics.patient_zero_pct * 100:.1f}% | "
                f"{metrics.total_wipeout_pct * 100:.1f}% | "
                f"{metrics.early_death_pct * 100:.1f}% |"
            )

    print("\n### 2. Bot Balance & Scores Telemetry")
    print("| Path | Players | Top Bot (Win %) | Runner-Up Win Rates | Mean Win VP |")
    print("| :--- | :---: | :--- | :--- | :---: |")
    for path_name, p_count, m in all_results:
        sorted_bots = sorted(m.win_rates.items(), key=lambda x: x[1], reverse=True)
        top_str = f"{sorted_bots[0][0]} ({sorted_bots[0][1] * 100:.1f}%)" if sorted_bots else "None"
        runner_ups = ", ".join(f"{b} ({w * 100:.1f}%)" for b, w in sorted_bots[1:]) if len(sorted_bots) > 1 else "None"
        print(
            f"| {path_name} | {p_count}P | {top_str} | "
            f"{runner_ups} | "
            f"{m.mean_winning_score:.1f} |"
        )

    print("\n### 3. Outlier Game Seeds")
    for path_name, p_count, m in all_results:
        if m.outlier_seeds:
            print(f"- **{path_name} ({p_count}P):** {m.outlier_seeds[:5]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Rogue Agent Monte Carlo Simulation Suite")
    parser.add_argument(
        "--experiment",
        "-e",
        choices=["1", "2", "3", "4", "5", "6", "all"],
        default="all",
        help="Which experiment to run (1-6 or all)",
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
    if args.experiment in ("5", "all"):
        run_experiment_5(runs=args.runs, base_seed=args.seed)
    if args.experiment in ("6", "all"):
        run_experiment_6(runs=args.runs, base_seed=args.seed)


if __name__ == "__main__":
    main()
