"""Detailed analysis for user queries:
1. Dice pool at game end per player count (averages, distributions, market availability).
2. Remaining cash at game end per player count (averages, distributions, disparities).
3. Cube threat vs player block, specifically examining Zero-Day Override.
"""

from __future__ import annotations

import json
import os
import random
import statistics
import sys
from collections import defaultdict
from typing import Any, Dict, List

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


def run_detailed_sweep(
    num_players: int,
    num_runs: int = 2000,
    base_seed: int = 100,
    mode: str = "baseline", # "baseline" or "user_exact"
):
    dice_totals: List[int] = []
    dice_ready: List[int] = []
    dice_unpatched: List[int] = []
    dice_purchased: List[int] = []
    
    cash_totals: List[int] = []
    cash_rich_players: List[int] = [] # players ending with >= $6
    
    game_cash_deltas: List[int] = []
    game_cash_min_max: List[tuple] = []
    
    market_left_total: List[int] = []
    market_left_by_color: Dict[str, List[int]] = defaultdict(list)
    market_empty_colors: Dict[str, int] = defaultdict(int)
    
    # Block vs Threat by version
    threat_by_version: Dict[str, List[int]] = defaultdict(list)
    block_by_version: Dict[str, List[int]] = defaultdict(list)
    locked_shields_by_version: Dict[str, List[int]] = defaultdict(list)

    total_market_dice_start = 5 * (2 * num_players)

    for i in range(num_runs):
        seed = base_seed + i
        config = GameConfig(num_players=num_players)

        if mode == "user_exact" and num_players == 2:
            bots = [AdaptiveBalancedBot(0), AdaptiveBalancedBot(1)]
            variant_cards = get_default_variant_cards()
            version_deck = get_default_version_deck()
            archetypes = [
                get_archetype_by_code(ArchetypeCode.OPERATOR),
                get_archetype_by_code(ArchetypeCode.PHREAKER),
            ]
        else:
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

        # Telemetry per round
        for t in res.telemetry_history:
            v_name = t.active_version_name
            attack_exited = sum(
                t.exited_cubes.get(c, 0)
                for c in [CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN]
            )
            threat_by_version[v_name].append(attack_exited)
            
            for ps in t.player_snapshots:
                block_by_version[v_name].append(ps.get("total_block", 0))

        # Game end player stats
        g_cash = []
        for p in res.rankings:
            r = p["ready_dice_count"]
            u = p["unpatched_dice_count"]
            tot = r + u
            # Starting gray dice = 4
            # We can count actual colored dice owned
            dice_totals.append(tot)
            dice_ready.append(r)
            dice_unpatched.append(u)
            
            money = p["money"]
            cash_totals.append(money)
            g_cash.append(money)
            if money >= 6:
                cash_rich_players.append(money)

        if g_cash:
            g_cash.sort()
            game_cash_deltas.append(g_cash[-1] - g_cash[0])
            game_cash_min_max.append((g_cash[0], g_cash[-1]))

        # Market stats
        m = engine.state.market
        tot_m_left = sum(m.values())
        market_left_total.append(tot_m_left)
        for col, cnt in m.items():
            market_left_by_color[col.value].append(cnt)
            if cnt == 0:
                market_empty_colors[col.value] += 1

    def quantiles(data):
        if not data:
            return {}
        s = sorted(data)
        n = len(s)
        return {
            "p10": s[int(0.10 * n)],
            "p25": s[int(0.25 * n)],
            "p50_median": s[int(0.50 * n)],
            "p75": s[int(0.75 * n)],
            "p90": s[int(0.90 * n)],
        }

    return {
        "num_players": num_players,
        "mode": mode,
        "runs": num_runs,
        "total_market_start": total_market_dice_start,
        "market_per_color_start": 2 * num_players,
        "dice_pool": {
            "mean": round(statistics.mean(dice_totals), 2),
            "stdev": round(statistics.stdev(dice_totals), 2),
            "min": min(dice_totals),
            "max": max(dice_totals),
            "quantiles": quantiles(dice_totals),
            "mean_ready": round(statistics.mean(dice_ready), 2),
            "mean_unpatched": round(statistics.mean(dice_unpatched), 2),
        },
        "market_remaining": {
            "mean_total": round(statistics.mean(market_left_total), 2),
            "stdev_total": round(statistics.stdev(market_left_total), 2),
            "min": min(market_left_total),
            "max": max(market_left_total),
            "pct_remaining": round(statistics.mean(market_left_total) / total_market_dice_start * 100, 1),
            "by_color_mean": {
                c: round(statistics.mean(cnts), 2)
                for c, cnts in market_left_by_color.items()
            },
            "empty_rate_pct": {
                c: round(cnt / num_runs * 100, 1)
                for c, cnt in market_empty_colors.items()
            },
        },
        "cash": {
            "mean": round(statistics.mean(cash_totals), 2),
            "stdev": round(statistics.stdev(cash_totals), 2),
            "min": min(cash_totals),
            "max": max(cash_totals),
            "quantiles": quantiles(cash_totals),
            "cash_rich_pct": round(len(cash_rich_players) / len(cash_totals) * 100, 1),
            "mean_game_delta": round(statistics.mean(game_cash_deltas), 2),
            "quantiles_game_delta": quantiles(game_cash_deltas),
        },
        "threat_vs_block": {
            v: {
                "mean_threat_cubes": round(statistics.mean(threat_by_version[v]), 2) if threat_by_version[v] else 0,
                "mean_block": round(statistics.mean(block_by_version[v]), 2) if block_by_version[v] else 0,
            }
            for v in threat_by_version
        },
    }


def main():
    results = {}
    print("Running 2P baseline...")
    results["2P_baseline"] = run_detailed_sweep(2, num_runs=2000, mode="baseline")
    print("Running 3P baseline...")
    results["3P_baseline"] = run_detailed_sweep(3, num_runs=2000, mode="baseline")
    print("Running 4P baseline...")
    results["4P_baseline"] = run_detailed_sweep(4, num_runs=2000, mode="baseline")
    print("Running 2P user exact...")
    results["2P_user_exact"] = run_detailed_sweep(2, num_runs=2000, mode="user_exact")

    print("\nDETAILED_JSON_START")
    print(json.dumps(results, indent=2))
    print("DETAILED_JSON_END")


if __name__ == "__main__":
    main()
