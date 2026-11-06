"""Phase 43 (v0.35.0) reproduction check against the D1 prototype sweep (spec R-32).

Runs the canonical engine (``GameConfig()`` = V035_FIVE_LEVEL, research-aware bots) with the same setup
harness as ``scripts/investigate_v350_research_sweep.py`` (random Variant Cards / version deck / Client
Companies / White Hat Operatives) and reports mean research per player and Singularity rate per player count.

Usage:
  python3 scripts/run_v350_research_track_check.py --games 200 --seed 4300
"""

from __future__ import annotations

import argparse
import os
import random
import statistics
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sim.bots import (  # noqa: E402
    AccelerationistBot, AdaptiveBalancedBot, RecklessSaboteurBot, SecOpsTurtleBot, VentureGreedBot,
)
from sim.config import EndGameReason, GameConfig  # noqa: E402
from sim.engine import GameEngine  # noqa: E402
from sim.entities import get_random_companies, get_random_setup, get_random_white_hats  # noqa: E402

BOT_CLASSES = [AdaptiveBalancedBot, SecOpsTurtleBot, VentureGreedBot, AccelerationistBot, RecklessSaboteurBot]


def run(games: int, seed: int, players=(2, 3, 4), config_factory=GameConfig) -> dict:
    out = {"research": [], "by_p": {}}
    for n in players:
        reasons: Counter = Counter()
        rounds = []
        res_n = []
        for i in range(games):
            ms = seed + n * 100_000 + i
            rng = random.Random(ms)
            bots = [BOT_CLASSES[(i * n + j) % 5](j) for j in range(n)]
            rng.shuffle(bots)
            for j, b in enumerate(bots):
                b.bot_id = j
            variants, deck = get_random_setup(rng, profile="STANDARD")
            comps = get_random_companies(n, rng)
            whs = get_random_white_hats(n, rng)
            cfg = config_factory(num_players=n, enable_corporate_asymmetry=True)
            eng = GameEngine(config=cfg, bots=bots, seed=ms, variant_cards=variants, version_deck=deck,
                             companies=comps, white_hats=whs)
            r = eng.run_game()
            reasons[r.end_reason.value] += 1
            rounds.append(r.total_rounds)
            for row in r.rankings:
                res_n.append(row.get("research_earned_total", 0))
        out["research"].extend(res_n)
        out["by_p"][n] = {
            "research": round(statistics.mean(res_n), 2),
            "singularity": round(reasons[EndGameReason.SINGULARITY.value] / games, 3),
            "rounds": round(statistics.mean(rounds), 2),
        }
    out["mean_research"] = round(statistics.mean(out["research"]), 2)
    del out["research"]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=200)
    ap.add_argument("--seed", type=int, default=4300)
    a = ap.parse_args()
    print(run(a.games, a.seed))


if __name__ == "__main__":
    main()
