"""Monte Carlo Experiment: Comparing Baseline (Block 2) vs Candidate (Block 1) for Red, Blue, Green.

Tests the user proposal:
Faces 1 & 2 on Red, Blue, and Green dice changed from Block 2 to Block 1.
Other faces (Cash, Patches, Choice faces, Variants/Stars) remain unchanged.
Yellow and Purple dice remain unchanged.

Runs N=1,000 matches per player count (2P, 3P, 4P) with randomized setups and base seed 42.
"""

from __future__ import annotations

import json
import random
import statistics
import time
from typing import Any, Dict, List, Optional

from sim.bots import (
    AccelerationistBot,
    AdaptiveBalancedBot,
    SecOpsTurtleBot,
    VentureGreedBot,
)
from sim.config import CubeColor, DieColor, EndGameReason, GameConfig, ShieldColor
from sim.engine import EndGameResult, GameEngine
from sim.entities import Die, Face, VariantCard, create_gray_die, create_white_die, get_random_setup
import sim.entities
import sim.engine.phase3_ops

# Save original create_colored_die
_ORIGINAL_CREATE_COLORED_DIE = sim.entities.create_colored_die


def create_colored_die_block1(
    color: DieColor,
    die_id: int,
    variant_card: Optional[VariantCard] = None,
) -> Die:
    """Creates a colored die with Faces 1 & 2 having Block 1 instead of Block 2 on Red, Blue, and Green."""
    if color == DieColor.GRAY:
        return create_gray_die(die_id)
    if color == DieColor.WHITE:
        return create_white_die(die_id)

    star_face = variant_card.star_face if variant_card else Face(name=f"{color.value} ★", is_star=True)
    var_code = variant_card.code if variant_card else None

    if color == DieColor.RED:
        faces = [
            Face(name="Block 1 Red", block_amount=1, shield_color=ShieldColor.RED),
            Face(name="Block 1 Red", block_amount=1, shield_color=ShieldColor.RED),
            Face(name="+$2", money=2),
            Face(name="+$2", money=2),
            star_face,
            star_face,
        ]
        return Die(die_id=die_id, color=color, cost=4, vp=3, faces=faces, variant_code=var_code)

    elif color == DieColor.BLUE:
        faces = [
            Face(name="Block 1 Blue", block_amount=1, shield_color=ShieldColor.BLUE),
            Face(name="Block 1 Blue", block_amount=1, shield_color=ShieldColor.BLUE),
            Face(name="+$1", money=1),
            Face(
                name="Block 1 Blue / +1 🔧",
                is_choice=True,
                choices=(
                    Face("Block 1 Blue", block_amount=1, shield_color=ShieldColor.BLUE),
                    Face("+1 🔧", patches=1),
                ),
            ),
            star_face,
            star_face,
        ]
        return Die(die_id=die_id, color=color, cost=5, vp=4, faces=faces, variant_code=var_code)

    elif color == DieColor.GREEN:
        faces = [
            Face(name="Block 1 Green", block_amount=1, shield_color=ShieldColor.GREEN),
            Face(name="Block 1 Green", block_amount=1, shield_color=ShieldColor.GREEN),
            Face(name="+2 🔧", patches=2),
            Face(
                name="+1 🔧 / +$1",
                is_choice=True,
                choices=(
                    Face("+1 🔧", patches=1),
                    Face("+$1", money=1),
                ),
            ),
            star_face,
            star_face,
        ]
        return Die(die_id=die_id, color=color, cost=4, vp=3, faces=faces, variant_code=var_code)

    elif color == DieColor.YELLOW:
        faces = [
            Face(name="+$3", money=3),
            Face(name="+$2", money=2),
            Face(name="+$2", money=2),
            Face(name="+$1 & +1 🔧", money=1, patches=1),
            star_face,
            star_face,
        ]
        return Die(die_id=die_id, color=color, cost=5, vp=4, faces=faces, variant_code=var_code)

    elif color == DieColor.PURPLE:
        faces = [
            Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY),
            Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY),
            Face(name="+$2", money=2),
            Face(name="+$1 & +1 🔧", money=1, patches=1),
            star_face,
            star_face,
        ]
        return Die(die_id=die_id, color=color, cost=4, vp=3, faces=faces, variant_code=var_code)

    raise ValueError(f"Unsupported die color: {color}")


def run_pod_sweep(
    p_count: int,
    num_runs: int = 1000,
    base_seed: int = 42,
) -> Dict[str, Any]:
    round_counts: List[int] = []
    end_reasons: Dict[EndGameReason, int] = {reason: 0 for reason in EndGameReason}
    winning_scores: List[float] = []
    survivor_scores: List[float] = []
    survivor_cash: List[int] = []
    survivor_secrets: List[int] = []
    survivor_unpatched_colored_dice: List[int] = []
    survivor_unpatched_vp_lost: List[int] = []
    survivor_has_unpatched_colored: List[int] = []
    early_deaths = 0
    bot_wins: Dict[str, int] = {}
    total_unblocked_damage_events: int = 0
    total_rounds_played: int = 0
    total_survivors: int = 0

    for run_idx in range(num_runs):
        seed = base_seed + run_idx
        config = GameConfig(num_players=p_count)

        bots = [
            AdaptiveBalancedBot(0),
            SecOpsTurtleBot(1),
            VentureGreedBot(2),
            AccelerationistBot(3),
        ][:p_count]

        rng_setup = random.Random(seed * 17)
        variant_cards, version_deck = get_random_setup(rng_setup)

        engine = GameEngine(
            config=config,
            bots=bots,
            seed=seed,
            variant_cards=variant_cards,
            version_deck=version_deck,
        )

        result: EndGameResult = engine.run_game()

        round_counts.append(result.total_rounds)
        total_rounds_played += result.total_rounds
        end_reasons[result.end_reason] = end_reasons.get(result.end_reason, 0) + 1

        if result.total_rounds <= 4:
            early_deaths += 1

        if result.rankings:
            winner = result.rankings[0]
            winning_scores.append(float(winner["portfolio_value"] if not result.is_total_wipeout else winner["net_score"]))
            w_name = winner["bot_name"]
            bot_wins[w_name] = bot_wins.get(w_name, 0) + 1

        for r in result.rankings:
            if not r["is_patient_zero"]:
                total_survivors += 1
                survivor_scores.append(float(r["portfolio_value"]))
                survivor_cash.append(r["money"])
                survivor_secrets.append(r["secrets"])
                survivor_unpatched_colored_dice.append(r["unpatched_colored_dice_count"])
                survivor_unpatched_vp_lost.append(r["unpatched_dice_vp_lost"])
                survivor_has_unpatched_colored.append(1 if r["unpatched_colored_dice_count"] > 0 else 0)

    avg_duration = statistics.mean(round_counts)
    stdev_duration = statistics.stdev(round_counts) if len(round_counts) > 1 else 0.0
    sing_pct = (end_reasons[EndGameReason.SINGULARITY] / num_runs) * 100.0
    pz_pct = (end_reasons[EndGameReason.PATIENT_ZERO] / num_runs) * 100.0
    wipe_pct = (end_reasons[EndGameReason.TOTAL_WIPEOUT] / num_runs) * 100.0
    total_breach_pct = pz_pct + wipe_pct
    early_death_pct = (early_deaths / num_runs) * 100.0

    return {
        "num_runs": num_runs,
        "avg_duration": round(avg_duration, 2),
        "stdev_duration": round(stdev_duration, 2),
        "min_duration": min(round_counts),
        "max_duration": max(round_counts),
        "singularity_pct": round(sing_pct, 1),
        "patient_zero_pct": round(pz_pct, 1),
        "total_wipeout_pct": round(wipe_pct, 1),
        "total_breach_pct": round(total_breach_pct, 1),
        "early_death_pct": round(early_death_pct, 1),
        "avg_winning_score": round(statistics.mean(winning_scores), 1) if winning_scores else 0.0,
        "avg_survivor_score": round(statistics.mean(survivor_scores), 1) if survivor_scores else 0.0,
        "avg_survivor_cash": round(statistics.mean(survivor_cash), 2) if survivor_cash else 0.0,
        "avg_survivor_secrets": round(statistics.mean(survivor_secrets), 2) if survivor_secrets else 0.0,
        "avg_survivor_unpatched_dice": round(statistics.mean(survivor_unpatched_colored_dice), 2) if survivor_unpatched_colored_dice else 0.0,
        "avg_survivor_vp_lost": round(statistics.mean(survivor_unpatched_vp_lost), 2) if survivor_unpatched_vp_lost else 0.0,
        "survivor_with_unpatched_pct": round((statistics.mean(survivor_has_unpatched_colored) * 100.0), 1) if survivor_has_unpatched_colored else 0.0,
        "bot_wins": bot_wins,
        "bot_win_pcts": {k: round(v / num_runs * 100.0, 1) for k, v in bot_wins.items()},
    }


def main():
    print("=" * 80)
    print("ROGUE AGENT BALANCE EXPERIMENT: BASELINE (BLOCK 2) VS CANDIDATE (BLOCK 1)")
    print("Testing User Proposal: Faces 1 & 2 on Red, Blue, Green = Block 1")
    print("=" * 80)

    base_seed = 42
    num_runs = 1000

    # 1. Run Baseline (Block 2)
    print("\n>>> RUNNING BASELINE (Block 2 on Red, Blue, Green)...")
    sim.entities.create_colored_die = _ORIGINAL_CREATE_COLORED_DIE
    sim.engine.phase3_ops.create_colored_die = _ORIGINAL_CREATE_COLORED_DIE

    t0 = time.time()
    baseline_results = {}
    for p in [2, 3, 4]:
        print(f"  Simulating {p}P Baseline (N={num_runs})...")
        baseline_results[p] = run_pod_sweep(p, num_runs=num_runs, base_seed=base_seed)
    t_baseline = time.time() - t0
    print(f"Baseline complete in {t_baseline:.2f}s.")

    # 2. Run Candidate (Block 1)
    print("\n>>> RUNNING CANDIDATE (Block 1 on Red, Blue, Green)...")
    sim.entities.create_colored_die = create_colored_die_block1
    sim.engine.phase3_ops.create_colored_die = create_colored_die_block1

    t0 = time.time()
    candidate_results = {}
    for p in [2, 3, 4]:
        print(f"  Simulating {p}P Candidate (N={num_runs})...")
        candidate_results[p] = run_pod_sweep(p, num_runs=num_runs, base_seed=base_seed)
    t_candidate = time.time() - t0
    print(f"Candidate complete in {t_candidate:.2f}s.")

    # Restore original
    sim.entities.create_colored_die = _ORIGINAL_CREATE_COLORED_DIE
    sim.engine.phase3_ops.create_colored_die = _ORIGINAL_CREATE_COLORED_DIE

    # Save to JSON
    summary = {
        "baseline_block2": baseline_results,
        "candidate_block1": candidate_results,
    }
    with open("block1_vs_block2_telemetry.json", "w") as f:
        json.dump(summary, f, indent=2)

    # Print comparison tables
    for p in [2, 3, 4]:
        b = baseline_results[p]
        c = candidate_results[p]
        print("\n" + "=" * 80)
        print(f"--- {p}-PLAYER POD COMPARISON (N={num_runs}) ---")
        print("=" * 80)
        print(f"{'Metric':<35} | {'Baseline (Block 2)':<18} | {'Candidate (Block 1)':<18} | {'Delta':<10}")
        print("-" * 88)
        
        metrics = [
            ("Average Match Duration (rds)", b["avg_duration"], c["avg_duration"], f"{c['avg_duration'] - b['avg_duration']:+.2f}"),
            ("Duration Stdev (rds)", b["stdev_duration"], c["stdev_duration"], f"{c['stdev_duration'] - b['stdev_duration']:+.2f}"),
            ("Duration Range (Min / Max)", f"{b['min_duration']} / {b['max_duration']}", f"{c['min_duration']} / {c['max_duration']}", ""),
            ("Singularity Rate (%)", f"{b['singularity_pct']}%", f"{c['singularity_pct']}%", f"{c['singularity_pct'] - b['singularity_pct']:+.1f}%"),
            ("Patient Zero Rate (%)", f"{b['patient_zero_pct']}%", f"{c['patient_zero_pct']}%", f"{c['patient_zero_pct'] - b['patient_zero_pct']:+.1f}%"),
            ("Total Wipeout Rate (%)", f"{b['total_wipeout_pct']}%", f"{c['total_wipeout_pct']}%", f"{c['total_wipeout_pct'] - b['total_wipeout_pct']:+.1f}%"),
            ("Total Breach Endings (%)", f"{b['total_breach_pct']}%", f"{c['total_breach_pct']}%", f"{c['total_breach_pct'] - b['total_breach_pct']:+.1f}%"),
            ("Early Deaths (<= R4) (%)", f"{b['early_death_pct']}%", f"{c['early_death_pct']}%", f"{c['early_death_pct'] - b['early_death_pct']:+.1f}%"),
            ("Avg Winning Score (VP)", b["avg_winning_score"], c["avg_winning_score"], f"{c['avg_winning_score'] - b['avg_winning_score']:+.1f}"),
            ("Avg Survivor Score (VP)", b["avg_survivor_score"], c["avg_survivor_score"], f"{c['avg_survivor_score'] - b['avg_survivor_score']:+.1f}"),
            ("Avg Survivor Cash ($)", f"${b['avg_survivor_cash']}", f"${c['avg_survivor_cash']}", f"${c['avg_survivor_cash'] - b['avg_survivor_cash']:+.2f}"),
            ("Avg Survivor Secrets", b["avg_survivor_secrets"], c["avg_survivor_secrets"], f"{c['avg_survivor_secrets'] - b['avg_survivor_secrets']:+.2f}"),
            ("Avg Unpatched Colored Dice", b["avg_survivor_unpatched_dice"], c["avg_survivor_unpatched_dice"], f"{c['avg_survivor_unpatched_dice'] - b['avg_survivor_unpatched_dice']:+.2f}"),
            ("Avg VP Lost to Debt", b["avg_survivor_vp_lost"], c["avg_survivor_vp_lost"], f"{c['avg_survivor_vp_lost'] - b['avg_survivor_vp_lost']:+.2f}"),
            ("Survivors with Unpatched (%)", f"{b['survivor_with_unpatched_pct']}%", f"{c['survivor_with_unpatched_pct']}%", f"{c['survivor_with_unpatched_pct'] - b['survivor_with_unpatched_pct']:+.1f}%"),
        ]

        for label, val_b, val_c, delta in metrics:
            print(f"{label:<35} | {str(val_b):<18} | {str(val_c):<18} | {delta:<10}")

        print("\nBot Win Rates:")
        for bot_name in sorted(b["bot_win_pcts"].keys()):
            pct_b = b["bot_win_pcts"].get(bot_name, 0.0)
            pct_c = c["bot_win_pcts"].get(bot_name, 0.0)
            print(f"  {bot_name:<25}: Baseline {pct_b:>5.1f}% | Candidate {pct_c:>5.1f}% | Delta {pct_c - pct_b:>+5.1f}%")


if __name__ == "__main__":
    main()
