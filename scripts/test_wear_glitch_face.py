"""Monte Carlo Experiment: Testing "Glitch: Wear 1 Active Die (Locked)" on Face 5.

Face 5 on Red, Blue, Green:
- Glitch: Wear 1 Active Die (Locked)
- Auto-locks when rolled (can be unlocked with 1 🔧 Debug action, or Prodigy).
- In Step 6, each unresolved Glitch face demotes 1 other Active die to Unpatched
  (or sacrifices a White Contractor die to supply).
- Face 6 is the single Star (★) face.

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


def create_colored_die_wear_glitch(
    color: DieColor,
    die_id: int,
    variant_card: Optional[VariantCard] = None,
) -> Die:
    if color == DieColor.GRAY:
        return create_gray_die(die_id)
    if color == DieColor.WHITE:
        return create_white_die(die_id)

    star_face = variant_card.star_face if variant_card else Face(name=f"{color.value} ★", is_star=True)
    var_code = variant_card.code if variant_card else None

    glitch_face = Face(name=f"Glitch: Wear Active ({color.value})", is_glitch=True)

    if color == DieColor.RED:
        faces = [
            Face(name="Block 1 Red", block_amount=1, shield_color=ShieldColor.RED),
            Face(name="+$2", money=2),
            Face(name="+$2", money=2),
            Face(name="+$2", money=2),
            glitch_face,
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
            glitch_face,
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
            glitch_face,
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


def run_pod_sweep(p_count: int, num_runs: int = 1000, base_seed: int = 42) -> Dict[str, Any]:
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
    contractor_sacrifices_total = 0
    glitch_demotions_total = 0

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
            tel = engine.run_round()

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
    print("TESTING USER PROPOSAL: FACE 5 = 'GLITCH: WEAR 1 ACTIVE DIE (LOCKED)'")
    print("Contractor sacrifice supported (White contractor die discarded to central pool)")
    print("=" * 80)

    base_seed = 42
    num_runs = 1000

    # Patch Phase 1 Boot to resolve the Wear Glitch face in Step 6
    orig_p1 = sim.engine.phase1_boot.execute_phase_1

    def execute_phase_1_with_wear_glitch(engine):
        commitments = orig_p1(engine)

        # After Phase 1 rolls and debug unlocks, resolve final Glitch: Wear faces
        for player in engine.state.players:
            # Count how many unresolved Wear Glitches are rolled
            wear_glitch_count = sum(
                1 for d in player.ready_dice + player.contractor_dice
                if d.current_face and d.current_face.is_glitch and "Wear Active" in d.current_face.name
            )

            for _ in range(wear_glitch_count):
                # 1. Can sacrifice a White Contractor die if available!
                if player.contractor_dice:
                    c_die = player.contractor_dice.pop(0)
                    engine.state.contractor_supply += 1
                elif player.ready_dice:
                    # Demote the lowest VP ready die to unpatched (prefer Gray)
                    # Don't demote the same die twice in one round
                    gray_dice = [d for d in player.ready_dice if d.color == DieColor.GRAY]
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

    results = {p: run_pod_sweep(p, num_runs=num_runs, base_seed=base_seed) for p in [4, 3, 2]}

    # Restore
    sim.engine.phase1_boot.execute_phase_1 = orig_p1
    sim.engine.core.execute_phase_1 = orig_p1
    sim.entities.create_colored_die = _ORIGINAL_CREATE_COLORED_DIE
    sim.engine.phase3_ops.create_colored_die = _ORIGINAL_CREATE_COLORED_DIE

    for p in [4, 3, 2]:
        res = results[p]
        print(f"\n--- {p}-PLAYER POD TELEMETRY (N={num_runs}) ---")
        print(f"Average Match Duration:       {res['avg_duration']} rds (Range: {res['min_duration']} - {res['max_duration']})")
        print(f"Singularity Rate:              {res['singularity_pct']}%")
        print(f"Patient Zero Rate:             {res['patient_zero_pct']}%")
        print(f"Total Wipeout Rate:            {res['total_wipeout_pct']}%")
        print(f"Total Breach Endings:          {res['total_breach_pct']}%")
        print(f"Early Deaths (<= R4):          {res['early_death_pct']}%")
        print(f"Avg Winning Score:             {res['avg_winning_score']} VP")
        print(f"Avg Survivor Score:            {res['avg_survivor_score']} VP")
        print(f"Avg Survivor Cash:             ${res['avg_survivor_cash']}")
        print(f"Avg Survivor Secrets:          {res['avg_survivor_secrets']}")
        print(f"Avg Unpatched Colored Dice:    {res['avg_survivor_unpatched_dice']}")
        print(f"Survivors with Debt:           {res['survivor_with_unpatched_pct']}%")
        print(f"Bot Win Rates:                 {res['bot_win_pcts']}")


if __name__ == "__main__":
    main()
