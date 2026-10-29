"""Monte Carlo Experiment: Testing Face 5 Alternatives.

Comparing:
1. Baseline: Lean Diversity (Face 5 & 6 are Star)
2. Option 1: Face 5 is Choice Face (+$1 / +1 🔧), Face 6 is Star
3. Option 2: Face 5 is Locked Hazard (+1 Color Cube to Staging Cup, Locked), Face 6 is Star

Runs N=1,000 matches per player count (2P, 3P, 4P) with randomized setups and base seed 42.
"""

from __future__ import annotations

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
import sim.engine.phase1_boot
import sim.engine.phase3_ops

_ORIGINAL_CREATE_COLORED_DIE = sim.entities.create_colored_die


def create_colored_die_opt1_choice(
    color: DieColor,
    die_id: int,
    variant_card: Optional[VariantCard] = None,
) -> Die:
    """Option 1: Face 5 is +$1 / +1 🔧 choice face, Face 6 is Star."""
    if color == DieColor.GRAY:
        return create_gray_die(die_id)
    if color == DieColor.WHITE:
        return create_white_die(die_id)

    star_face = variant_card.star_face if variant_card else Face(name=f"{color.value} ★", is_star=True)
    var_code = variant_card.code if variant_card else None
    choice_face = Face(
        name="+$1 / +1 🔧",
        is_choice=True,
        choices=(Face("+$1", money=1), Face("+1 🔧", patches=1)),
    )

    if color == DieColor.RED:
        faces = [
            Face(name="Block 1 Red", block_amount=1, shield_color=ShieldColor.RED),
            Face(name="+$2", money=2),
            Face(name="+$2", money=2),
            Face(name="+$2", money=2),
            choice_face,
            star_face,
        ]
        return Die(die_id=die_id, color=color, cost=4, vp=3, faces=faces, variant_code=var_code)

    elif color == DieColor.BLUE:
        faces = [
            Face(name="Block 1 Blue", block_amount=1, shield_color=ShieldColor.BLUE),
            Face(name="+1 🔧", patches=1),
            Face(name="+$1", money=1),
            Face(
                name="Block 1 Blue / +1 🔧",
                is_choice=True,
                choices=(
                    Face("Block 1 Blue", block_amount=1, shield_color=ShieldColor.BLUE),
                    Face("+1 🔧", patches=1),
                ),
            ),
            choice_face,
            star_face,
        ]
        return Die(die_id=die_id, color=color, cost=5, vp=4, faces=faces, variant_code=var_code)

    elif color == DieColor.GREEN:
        faces = [
            Face(name="Block 1 Green", block_amount=1, shield_color=ShieldColor.GREEN),
            Face(name="+1 🔧", patches=1),
            Face(name="+2 🔧", patches=2),
            Face(
                name="+1 🔧 / +$1",
                is_choice=True,
                choices=(
                    Face("+1 🔧", patches=1),
                    Face("+$1", money=1),
                ),
            ),
            choice_face,
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


def create_colored_die_opt2_hazard(
    color: DieColor,
    die_id: int,
    variant_card: Optional[VariantCard] = None,
) -> Die:
    """Option 2: Face 5 is Locked Hazard (+1 Cube of Color to Staging Cup), Face 6 is Star."""
    if color == DieColor.GRAY:
        return create_gray_die(die_id)
    if color == DieColor.WHITE:
        return create_white_die(die_id)

    star_face = variant_card.star_face if variant_card else Face(name=f"{color.value} ★", is_star=True)
    var_code = variant_card.code if variant_card else None

    if color == DieColor.RED:
        faces = [
            Face(name="Block 1 Red", block_amount=1, shield_color=ShieldColor.RED),
            Face(name="+$2", money=2),
            Face(name="+$2", money=2),
            Face(name="+$2", money=2),
            Face(name="Beacon: +1 Red Cube (Locked)", is_glitch=True),
            star_face,
        ]
        return Die(die_id=die_id, color=color, cost=4, vp=3, faces=faces, variant_code=var_code)

    elif color == DieColor.BLUE:
        faces = [
            Face(name="Block 1 Blue", block_amount=1, shield_color=ShieldColor.BLUE),
            Face(name="+1 🔧", patches=1),
            Face(name="+$1", money=1),
            Face(
                name="Block 1 Blue / +1 🔧",
                is_choice=True,
                choices=(
                    Face("Block 1 Blue", block_amount=1, shield_color=ShieldColor.BLUE),
                    Face("+1 🔧", patches=1),
                ),
            ),
            Face(name="Leak: +1 Blue Cube (Locked)", is_glitch=True),
            star_face,
        ]
        return Die(die_id=die_id, color=color, cost=5, vp=4, faces=faces, variant_code=var_code)

    elif color == DieColor.GREEN:
        faces = [
            Face(name="Block 1 Green", block_amount=1, shield_color=ShieldColor.GREEN),
            Face(name="+1 🔧", patches=1),
            Face(name="+2 🔧", patches=2),
            Face(
                name="+1 🔧 / +$1",
                is_choice=True,
                choices=(
                    Face("+1 🔧", patches=1),
                    Face("+$1", money=1),
                ),
            ),
            Face(name="Crash: +1 Green Cube (Locked)", is_glitch=True),
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
    is_hazard: bool = False,
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
    total_hazard_cubes_added = 0
    total_atk_exited_list = []

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

        while not engine.state.game_over:
            # If hazard mode, check for hazard faces after Phase 1 roll and lock resolution
            # In GameEngine, run_round executes P1 -> P2 -> P3.
            # We can hook into run_round or check before Phase 2.
            # To simulate accurately: before P2 tower drop, check rolled dice for hazard faces
            # And add to staging cup!
            if is_hazard:
                # We can hook execute_phase_1 or do manual stepping:
                # Let's inspect rolled dice after Phase 1:
                pass
            
            tel = engine.run_round()
            ex = tel.exited_cubes
            atk_sum = ex.get(CubeColor.RED, 0) + ex.get(CubeColor.BLUE, 0) + ex.get(CubeColor.GREEN, 0)
            total_atk_exited_list.append(atk_sum)

        round_counts.append(engine.state.current_round)
        end_reasons[engine.state.end_reason] = end_reasons.get(engine.state.end_reason, 0) + 1

        if engine.state.current_round <= 4:
            early_deaths += 1

        res = engine.evaluate_end_game()
        if res.rankings:
            winner = res.rankings[0]
            winning_scores.append(float(winner["portfolio_value"] if not res.is_total_wipeout else winner["net_score"]))
            w_name = winner["bot_name"]
            bot_wins[w_name] = bot_wins.get(w_name, 0) + 1

        for r in res.rankings:
            if not r["is_patient_zero"]:
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
        "avg_duration": round(avg_duration, 2),
        "stdev_duration": round(stdev_duration, 2),
        "min_duration": min(round_counts),
        "max_duration": max(round_counts),
        "avg_atk_exited": round(statistics.mean(total_atk_exited_list), 2) if total_atk_exited_list else 0.0,
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
        "survivor_with_unpatched_pct": round((statistics.mean(survivor_has_unpatched_colored) * 100.0), 1) if survivor_has_unpatched_colored else 0.0,
        "bot_win_pcts": {k: round(v / num_runs * 100.0, 1) for k, v in bot_wins.items()},
    }


def main():
    print("=" * 80)
    print("EXPERIMENT C: FACE 5 ALTERNATIVES (Choice vs Push-Your-Luck Hazard)")
    print("=" * 80)

    base_seed = 42
    num_runs = 1000

    # 1. Option 1: Choice Face (+$1 / +1 🔧 on Face 5, 1x Star on Face 6)
    print("\nSimulating Option 1: Choice Face (+$1 / +1 🔧)...")
    sim.entities.create_colored_die = create_colored_die_opt1_choice
    sim.engine.phase3_ops.create_colored_die = create_colored_die_opt1_choice
    opt1 = {p: run_pod_sweep(p, num_runs=num_runs, base_seed=base_seed, is_hazard=False) for p in [4, 3, 2]}

    # 2. Option 2: Push-Your-Luck Hazard (Glitch: +1 Cube to Staging Cup, Locked)
    # We patch execute_phase_1 or GameEngine to inject cubes for active glitch faces!
    orig_p1 = sim.engine.phase1_boot.execute_phase_1

    def execute_phase_1_with_hazard(engine):
        commitments = orig_p1(engine)
        # Check active rolled dice across all players for hazard faces
        color_map = {
            "Beacon: +1 Red Cube (Locked)": CubeColor.RED,
            "Leak: +1 Blue Cube (Locked)": CubeColor.BLUE,
            "Crash: +1 Green Cube (Locked)": CubeColor.GREEN,
        }
        for p in engine.state.players:
            for die in p.ready_dice + p.contractor_dice:
                face = die.effective_face or die.current_face
                if face and face.name in color_map:
                    cube_c = color_map[face.name]
                    engine.state.staging_cup[cube_c] = engine.state.staging_cup.get(cube_c, 0) + 1
        return commitments

    sim.engine.phase1_boot.execute_phase_1 = execute_phase_1_with_hazard
    sim.engine.core.execute_phase_1 = execute_phase_1_with_hazard
    sim.entities.create_colored_die = create_colored_die_opt2_hazard
    sim.engine.phase3_ops.create_colored_die = create_colored_die_opt2_hazard

    print("Simulating Option 2: Push-Your-Luck Hazard (Auto-Locked +1 Cube to Staging)...")
    opt2 = {p: run_pod_sweep(p, num_runs=num_runs, base_seed=base_seed, is_hazard=True) for p in [4, 3, 2]}

    # Restore
    sim.engine.phase1_boot.execute_phase_1 = orig_p1
    sim.engine.core.execute_phase_1 = orig_p1
    sim.entities.create_colored_die = _ORIGINAL_CREATE_COLORED_DIE
    sim.engine.phase3_ops.create_colored_die = _ORIGINAL_CREATE_COLORED_DIE

    for p in [4, 3, 2]:
        o1 = opt1[p]
        o2 = opt2[p]
        print("\n" + "=" * 80)
        print(f"--- {p}-PLAYER POD COMPARISON (N={num_runs}) ---")
        print("=" * 80)
        print(f"{'Metric':<35} | {'Option 1 (Choice Face)':<22} | {'Option 2 (Hazard Cube)':<22} | {'Delta':<10}")
        print("-" * 92)
        
        metrics = [
            ("Average Match Duration (rds)", o1["avg_duration"], o2["avg_duration"], f"{o2['avg_duration'] - o1['avg_duration']:+.2f}"),
            ("Duration Range (Min / Max)", f"{o1['min_duration']} / {o1['max_duration']}", f"{o2['min_duration']} / {o2['max_duration']}", ""),
            ("Avg Attack Cubes Exited/rd", o1["avg_atk_exited"], o2["avg_atk_exited"], f"{o2['avg_atk_exited'] - o1['avg_atk_exited']:+.2f}"),
            ("Singularity Rate (%)", f"{o1['singularity_pct']}%", f"{o2['singularity_pct']}%", f"{o2['singularity_pct'] - o1['singularity_pct']:+.1f}%"),
            ("Patient Zero Rate (%)", f"{o1['patient_zero_pct']}%", f"{o2['patient_zero_pct']}%", f"{o2['patient_zero_pct'] - o1['patient_zero_pct']:+.1f}%"),
            ("Total Wipeout Rate (%)", f"{o1['total_wipeout_pct']}%", f"{o2['total_wipeout_pct']}%", f"{o2['total_wipeout_pct'] - o1['total_wipeout_pct']:+.1f}%"),
            ("Total Breach Endings (%)", f"{o1['total_breach_pct']}%", f"{o2['total_breach_pct']}%", f"{o2['total_breach_pct'] - o1['total_breach_pct']:+.1f}%"),
            ("Early Deaths (<= R4) (%)", f"{o1['early_death_pct']}%", f"{o2['early_death_pct']}%", f"{o2['early_death_pct'] - o1['early_death_pct']:+.1f}%"),
            ("Avg Winning Score (VP)", o1["avg_winning_score"], o2["avg_winning_score"], f"{o2['avg_winning_score'] - o1['avg_winning_score']:+.1f}"),
            ("Avg Survivor Score (VP)", o1["avg_survivor_score"], o2["avg_survivor_score"], f"{o2['avg_survivor_score'] - o1['avg_survivor_score']:+.1f}"),
            ("Avg Survivor Cash ($)", f"${o1['avg_survivor_cash']}", f"${o2['avg_survivor_cash']}", f"${o2['avg_survivor_cash'] - o1['avg_survivor_cash']:+.2f}"),
            ("Avg Survivor Secrets", o1["avg_survivor_secrets"], o2["avg_survivor_secrets"], f"{o2['avg_survivor_secrets'] - o1['avg_survivor_secrets']:+.2f}"),
            ("Avg Unpatched Colored Dice", o1["avg_survivor_unpatched_dice"], o2["avg_survivor_unpatched_dice"], f"{o2['avg_survivor_unpatched_dice'] - o1['avg_survivor_unpatched_dice']:+.2f}"),
            ("Survivors with Unpatched (%)", f"{o1['survivor_with_unpatched_pct']}%", f"{o2['survivor_with_unpatched_pct']}%", f"{o2['survivor_with_unpatched_pct'] - o1['survivor_with_unpatched_pct']:+.1f}%"),
        ]

        for label, val_1, val_2, delta in metrics:
            print(f"{label:<35} | {str(val_1):<22} | {str(val_2):<22} | {delta:<10}")

        print("\nBot Win Rates:")
        for bot_name in sorted(o1["bot_win_pcts"].keys()):
            pct_1 = o1["bot_win_pcts"].get(bot_name, 0.0)
            pct_2 = o2["bot_win_pcts"].get(bot_name, 0.0)
            print(f"  {bot_name:<25}: Option 1 {pct_1:>5.1f}% | Option 2 {pct_2:>5.1f}% | Delta {pct_2 - pct_1:>+5.1f}%")


if __name__ == "__main__":
    main()
