"""Simulation script to measure dice accumulation, market depletion, and end-game cash across player counts."""

from __future__ import annotations

import json
import os
import random
import statistics
import sys
from collections import defaultdict
from typing import Any, Dict, List

# Ensure repository root is in sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from sim.bots import (
    AccelerationistBot,
    AdaptiveBalancedBot,
    BaseBot,
    RecklessSaboteurBot,
    SecOpsTurtleBot,
    VentureGreedBot,
)
from sim.config import CubeColor, DieColor, EndGameReason, GameConfig
from sim.engine import GameEngine
from sim.entities import (
    ArchetypeCode,
    get_all_variant_cards,
    get_archetype_by_code,
    get_default_variant_cards,
    get_default_version_deck,
    get_random_setup,
)


def analyze_pod(
    num_players: int,
    num_runs: int = 1000,
    base_seed: int = 42,
    fixed_setup: bool = False,
    exact_user_setup: bool = False,
) -> Dict[str, Any]:
    dice_per_player: List[int] = []
    ready_dice_per_player: List[int] = []
    unpatched_dice_per_player: List[int] = []
    purchased_dice_per_player: List[int] = []
    
    cash_per_player: List[int] = []
    winner_cash: List[int] = []
    loser_cash: List[int] = []
    cash_disparities_2p: List[int] = []
    cash_rich_vs_strapped_count_2p = 0

    market_remaining_total: List[int] = []
    market_remaining_by_color: Dict[str, List[int]] = defaultdict(list)
    rounds_list: List[int] = []

    # Block vs Threat metrics
    block_totals_by_version: Dict[str, List[float]] = defaultdict(list)
    threat_cubes_by_version: Dict[str, List[float]] = defaultdict(list)

    total_market_start = 5 * (2 * num_players)  # 5 colors * 2 * num_players

    for i in range(num_runs):
        seed = base_seed + i
        config = GameConfig(num_players=num_players)

        if num_players == 2:
            bots = [AdaptiveBalancedBot(0), SecOpsTurtleBot(1)]
        elif num_players == 3:
            bots = [AdaptiveBalancedBot(0), SecOpsTurtleBot(1), VentureGreedBot(2)]
        else:
            bots = [
                AdaptiveBalancedBot(0),
                SecOpsTurtleBot(1),
                VentureGreedBot(2),
                AccelerationistBot(3),
            ]

        if exact_user_setup and num_players == 2:
            variant_cards = get_default_variant_cards()
            version_deck = get_default_version_deck()
            archetypes = [
                get_archetype_by_code(ArchetypeCode.OPERATOR),
                get_archetype_by_code(ArchetypeCode.PHREAKER),
            ]
        elif fixed_setup:
            variant_cards = get_default_variant_cards()
            version_deck = get_default_version_deck()
            archetypes = None
        else:
            rng_setup = random.Random(seed * 17)
            variant_cards, version_deck = get_random_setup(rng_setup)
            archetypes = None

        engine = GameEngine(
            config=config,
            bots=bots,
            seed=seed,
            variant_cards=variant_cards,
            version_deck=version_deck,
            archetypes=archetypes,
        )
        res = engine.run_game()
        rounds_list.append(res.total_rounds)

        # Track player dice and cash
        game_cash: List[int] = []
        for p in res.rankings:
            ready = p["ready_dice_count"]
            unpatched = p["unpatched_dice_count"]
            total_d = ready + unpatched
            purchased = max(0, total_d - 4)  # 4 starting gray dice
            money = p["money"]

            dice_per_player.append(total_d)
            ready_dice_per_player.append(ready)
            unpatched_dice_per_player.append(unpatched)
            purchased_dice_per_player.append(purchased)
            cash_per_player.append(money)
            game_cash.append(money)

        if len(res.rankings) >= 1:
            winner_cash.append(res.rankings[0]["money"])
        if len(res.rankings) >= 2:
            loser_cash.append(res.rankings[-1]["money"])

        if num_players == 2:
            disp = abs(game_cash[0] - game_cash[1])
            cash_disparities_2p.append(disp)
            # Check if one player >= $5 and other <= $1
            if (game_cash[0] >= 5 and game_cash[1] <= 1) or (game_cash[1] >= 5 and game_cash[0] <= 1):
                cash_rich_vs_strapped_count_2p += 1

        # Track Market Remaining
        market = engine.state.market
        tot_left = sum(market.values())
        market_remaining_total.append(tot_left)
        for col, count in market.items():
            market_remaining_by_color[col.value].append(count)

        # Block vs Threat telemetry
        for t in res.telemetry_history:
            v_name = t.active_version_name
            tot_exited = sum(t.exited_cubes.get(c, 0) for c in [CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN])
            threat_cubes_by_version[v_name].append(tot_exited)
            # From snapshots, get average block per player
            round_blocks = []
            for ps in t.player_snapshots:
                blk = ps.get("total_block", 0)
                round_blocks.append(blk)
            if round_blocks:
                block_totals_by_version[v_name].append(statistics.mean(round_blocks))

    result = {
        "num_players": num_players,
        "runs": num_runs,
        "total_market_start": total_market_start,
        "market_start_per_color": 2 * num_players,
        "mean_rounds": round(statistics.mean(rounds_list), 2),
        "dice": {
            "mean_total": round(statistics.mean(dice_per_player), 2),
            "stdev_total": round(statistics.stdev(dice_per_player), 2),
            "min_total": min(dice_per_player),
            "max_total": max(dice_per_player),
            "median_total": round(statistics.median(dice_per_player), 2),
            "mean_purchased": round(statistics.mean(purchased_dice_per_player), 2),
            "mean_ready": round(statistics.mean(ready_dice_per_player), 2),
            "mean_unpatched": round(statistics.mean(unpatched_dice_per_player), 2),
        },
        "market_remaining": {
            "mean_total_left": round(statistics.mean(market_remaining_total), 2),
            "stdev_total_left": round(statistics.stdev(market_remaining_total), 2),
            "min_total_left": min(market_remaining_total),
            "max_total_left": max(market_remaining_total),
            "pct_left": round(statistics.mean(market_remaining_total) / total_market_start * 100, 1),
            "pct_depleted": round((1.0 - statistics.mean(market_remaining_total) / total_market_start) * 100, 1),
            "by_color": {
                c: round(statistics.mean(vals), 2)
                for c, vals in market_remaining_by_color.items()
            },
        },
        "cash": {
            "mean_end_cash": round(statistics.mean(cash_per_player), 2),
            "stdev_end_cash": round(statistics.stdev(cash_per_player), 2),
            "min_end_cash": min(cash_per_player),
            "max_end_cash": max(cash_per_player),
            "median_end_cash": round(statistics.median(cash_per_player), 2),
            "mean_winner_cash": round(statistics.mean(winner_cash), 2),
            "mean_loser_cash": round(statistics.mean(loser_cash), 2),
        },
        "block_vs_threat": {
            v: {
                "mean_player_block": round(statistics.mean(block_totals_by_version[v]), 2) if block_totals_by_version[v] else 0,
                "mean_threat_cubes": round(statistics.mean(threat_cubes_by_version[v]), 2) if threat_cubes_by_version[v] else 0,
            }
            for v in block_totals_by_version
        },
    }

    if num_players == 2:
        result["cash"]["mean_disparity_2p"] = round(statistics.mean(cash_disparities_2p), 2)
        result["cash"]["cash_rich_vs_strapped_pct_2p"] = round(
            cash_rich_vs_strapped_count_2p / num_runs * 100, 1
        )

    return result


def main():
    print("=== ROGUE AGENT: DICE & CASH TELEMETRY SWEEP (v0.10.0) ===")
    
    # 1. Broad baseline sweep (Randomized Setups, 1000 runs each)
    baseline_results = {}
    for p in [2, 3, 4]:
        print(f"Running baseline {p}P sweep (N=1000)...")
        baseline_results[f"{p}P_baseline"] = analyze_pod(p, num_runs=1000, fixed_setup=False)

    # 2. User's exact configuration (2P Operator vs Phreaker, R1, B1, G1, Y1, P1, Default Deck)
    print("Running User Exact Match 2P sweep (Operator vs Phreaker, N=1000)...")
    baseline_results["2P_user_exact"] = analyze_pod(2, num_runs=1000, exact_user_setup=True)

    print("\nRESULTS_JSON_START")
    print(json.dumps(baseline_results, indent=2))
    print("RESULTS_JSON_END")


if __name__ == "__main__":
    main()
