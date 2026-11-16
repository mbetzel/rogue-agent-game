"""Monte Carlo validation sweep for v0.44.0 Colored Die F6 Variant Overhaul & Glitched Shield Slot Flow.

Runs 300 games per player count (2P, 3P, 4P; seeds 42..341) for both:
- v044_roster (v0.44.0 Candidate)
- v043_roster (v0.43.0 Baseline)

Total: 1,800 games. Outputs compact summary tables and outlier seed lists.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import math
import multiprocessing as mp
import os
import random
import sys
from typing import Any, Dict, List, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from sim.config import EndGameReason, GameConfig, V038_COMPANY_STARTING_COLORS
from sim.engine import GameEngine
from sim.entities import get_random_companies, get_random_setup, get_random_white_hats
from tests.fixtures.v035_parity.capture import _bot_classes


def _company_color(company_code: str) -> str:
    c = V038_COMPANY_STARTING_COLORS.get(company_code or "")
    return c.lower() if c else "none"


def build_engine(config_name: str, players: int, seed: int) -> GameEngine:
    classes = _bot_classes()
    rng = random.Random(seed)
    bots = [classes[(seed * players + i) % len(classes)](i) for i in range(players)]
    rng.shuffle(bots)
    for i, b in enumerate(bots):
        b.player_id = i

    variants, version_deck = get_random_setup(rng, profile="STANDARD")
    companies = get_random_companies(players, rng)
    white_hats = get_random_white_hats(players, rng)

    cfg = getattr(GameConfig, config_name)(
        num_players=players,
        starting_money=6,
        starting_gray_dice=3,
        starting_purple_dice=1,
        starting_purple_reserve=1,
        corruption_track_profile="STANDARD",
        enable_corporate_asymmetry=True,
    )
    return GameEngine(
        config=cfg,
        bots=bots,
        seed=seed,
        variant_cards=variants,
        version_deck=version_deck,
        companies=companies,
        white_hats=white_hats,
    )


def simulate_game(task: Tuple[str, int, int]) -> Dict[str, Any]:
    config_name, players, seed = task
    engine = build_engine(config_name, players, seed)
    res = engine.run_game()

    nwin = max(1, len(res.winner_ids))
    variants_active = {c.name: v.code for c, v in engine.state.variant_cards.items()}

    player_records = []
    for p in engine.state.players:
        c_code = p.company.code.value if getattr(p, "company", None) else "NONE"
        c_color = _company_color(c_code)
        won = (1.0 / nwin) if p.player_id in res.winner_ids else 0.0
        player_records.append({
            "seat": p.player_id,
            "company": c_code,
            "color": c_color,
            "won": won,
            "secrets": p.secrets,
            "market_share": p.market_share,
            "eliminated": getattr(p, "eliminated", False),
            "purged_slots": getattr(p, "slots_purged_by_shields_total", 0),
            "r2_act": getattr(p, "f6_r2_activations", 0),
            "b2_cash": getattr(p, "f6_b2_cash_activations", 0),
            "b2_sec": getattr(p, "f6_b2_secret_activations", 0),
            "b2_sui": getattr(p, "f6_b2_suicide_breaches", 0),
            "g1_act": getattr(p, "f6_g1_activations", 0),
            "g1_prom": getattr(p, "f6_g1_shield_promotions", 0),
            "g3_grad": getattr(p, "f6_g3_graduations", 0),
            "g3_fizz": getattr(p, "f6_g3_fizzles", 0),
            "y1_cash": getattr(p, "f6_y1_cash_activations", 0),
            "y1_sec": getattr(p, "f6_y1_secret_activations", 0),
        })

    return {
        "config": config_name,
        "players": players,
        "seed": seed,
        "rounds": res.total_rounds,
        "end_reason": res.end_reason.value,
        "is_wipeout": res.is_total_wipeout,
        "is_shared": res.is_shared_victory,
        "variants": variants_active,
        "player_records": player_records,
    }


def _pct(num: float, den: float) -> str:
    return f"{(100.0 * num / den):.1f}%" if den > 0 else "0.0%"


def summarize(records: List[Dict[str, Any]], config_name: str) -> str:
    lines: List[str] = []
    lines.append(f"=== {config_name} (N={len(records)} games) ===")

    # Overall & per-player-count pacing + end triggers
    for pcount in (None, 2, 3, 4):
        sub = records if pcount is None else [r for r in records if r["players"] == pcount]
        label = "ALL" if pcount is None else f"{pcount}P"
        n = len(sub)
        rounds = sorted(r["rounds"] for r in sub)
        mean_r = sum(rounds) / n
        std_r = math.sqrt(sum((x - mean_r) ** 2 for x in rounds) / n)
        p10, p50, p90 = rounds[int(0.1 * n)], rounds[int(0.5 * n)], rounds[int(0.9 * n)]
        ends = Counter(r["end_reason"] for r in sub)
        shared = sum(1 for r in sub if r["is_shared"])
        lines.append(
            f"[{label} n={n}] rounds: mean={mean_r:.2f} std={std_r:.2f} "
            f"min={rounds[0]} p10={p10} p50={p50} p90={p90} max={rounds[-1]} | "
            f"Sing={_pct(ends['singularity'], n)} PZ={_pct(ends['patient_zero'], n)} "
            f"MC={_pct(ends['market_collapse'], n)} WO={_pct(ends['total_wipeout'], n)} "
            f"RL={_pct(ends['round_limit'], n)} Shared={_pct(shared, n)}"
        )

    # Seat fairness
    lines.append("\n-- Seat Fairness (Win Share %) --")
    for pcount in (2, 3, 4):
        sub = [r for r in records if r["players"] == pcount]
        seat_wins = Counter()
        for r in sub:
            for pr in r["player_records"]:
                seat_wins[pr["seat"]] += pr["won"]
        parts = [f"S{s+1}={_pct(seat_wins[s], len(sub))}" for s in range(pcount)]
        lines.append(f"  {pcount}P: " + "  ".join(parts))

    # Company & Starting Color win rates
    comp_games = Counter()
    comp_wins = Counter()
    color_games = Counter()
    color_wins = Counter()
    for r in records:
        for pr in r["player_records"]:
            comp_games[pr["company"]] += 1
            comp_wins[pr["company"]] += pr["won"]
            color_games[pr["color"]] += 1
            color_wins[pr["color"]] += pr["won"]

    lines.append("\n-- Client Company Win Rates --")
    for comp in ("MERIDIAN", "PROMETHEUS", "DTO", "AEGIS", "OMNIDYNE", "HELIX"):
        g = comp_games[comp]
        w = comp_wins[comp]
        exp = 0.0
        # Expected win rate given player-count mix
        for r in records:
            if any(pr["company"] == comp for pr in r["player_records"]):
                exp += 1.0 / r["players"]
        lines.append(
            f"  {comp:11s}: {w:5.1f}/{g:4d} = {_pct(w, g):>6s} (expected {_pct(exp, g):>6s}, diff={((w-exp)/g*100):+.2f}pp)"
        )

    lines.append("\n-- Starting Color Win Rates --")
    for col in ("red", "blue", "green"):
        g = color_games[col]
        w = color_wins[col]
        lines.append(f"  {col.upper():6s}: {w:5.1f}/{g:4d} = {_pct(w, g):>6s}")

    # F6 & Purge Telemetry (meaningful for v044)
    total_purged = sum(pr["purged_slots"] for r in records for pr in r["player_records"])
    total_player_rounds = sum(r["rounds"] * r["players"] for r in records)
    lines.append("\n-- F6 Variant & Glitched Shield Slot Purge Telemetry --")
    lines.append(
        f"  Glitched slots purged by shields: {total_purged} total "
        f"({total_purged / len(records):.2f}/game, {total_purged / total_player_rounds:.3f}/player-round)"
    )

    if "v044" in config_name:
        card_games = Counter()
        for r in records:
            for vcode in r["variants"].values():
                card_games[vcode] += 1

        sums = Counter()
        for r in records:
            for pr in r["player_records"]:
                for k in ("r2_act", "b2_cash", "b2_sec", "b2_sui", "g1_act", "g1_prom", "g3_grad", "g3_fizz", "y1_cash", "y1_sec"):
                    sums[k] += pr[k]

        lines.append(f"  R2 activations: {sums['r2_act']} (in {card_games['R2']} R2 games => {sums['r2_act']/max(1, card_games['R2']):.2f}/R2-game)")
        lines.append(
            f"  B2 (in {card_games['B2']} B2 games): cash={sums['b2_cash']} ({sums['b2_cash']/max(1, card_games['B2']):.2f}/gm), "
            f"secret={sums['b2_sec']} ({sums['b2_sec']/max(1, card_games['B2']):.2f}/gm), "
            f"suicide_breaches={sums['b2_sui']} ({_pct(sums['b2_sui'], sums['b2_sec'])} of secret acts)"
        )
        lines.append(
            f"  G1 (in {card_games['G1']} G1 games): activations={sums['g1_act']} ({sums['g1_act']/max(1, card_games['G1']):.2f}/gm), "
            f"shield_promotions={sums['g1_prom']} ({_pct(sums['g1_prom'], sums['g1_act'])} of acts)"
        )
        g3_tot = sums["g3_grad"] + sums["g3_fizz"]
        lines.append(
            f"  G3 (in {card_games['G3']} G3 games): graduations={sums['g3_grad']}, fizzles={sums['g3_fizz']} "
            f"(fizzle rate={_pct(sums['g3_fizz'], g3_tot)}, total={g3_tot/max(1, card_games['G3']):.2f}/gm)"
        )
        lines.append(
            f"  Y1 (in {card_games['Y1']} Y1 games): cash={sums['y1_cash']} ({sums['y1_cash']/max(1, card_games['Y1']):.2f}/gm), "
            f"secret={sums['y1_sec']} ({sums['y1_sec']/max(1, card_games['Y1']):.2f}/gm)"
        )

    # Outliers
    wipeouts = [(r["players"], r["seed"], r["rounds"]) for r in records if r["is_wipeout"]]
    short_games = [(r["players"], r["seed"], r["rounds"], r["end_reason"]) for r in records if r["rounds"] <= 5]
    long_games = [(r["players"], r["seed"], r["rounds"], r["end_reason"]) for r in records if r["rounds"] >= 14]
    b2_suicides = [
        (r["players"], r["seed"], r["rounds"])
        for r in records
        if any(pr["b2_sui"] > 0 for pr in r["player_records"])
    ]
    lines.append("\n-- Outliers --")
    lines.append(f"  Total Wipeouts ({len(wipeouts)}): {wipeouts[:12]}")
    lines.append(f"  Short games <=5r ({len(short_games)}): {short_games[:12]}")
    lines.append(f"  Long games >=14r ({len(long_games)}): {long_games[:12]}")
    if "v044" in config_name:
        lines.append(f"  B2 suicide seeds ({len(b2_suicides)}): {b2_suicides[:12]}")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run v0.44.0 F6 Variant Overhaul Monte Carlo sweep")
    parser.add_argument("--runs", type=int, default=300, help="Games per player count (default: 300)")
    parser.add_argument("--seed", type=int, default=42, help="Base seed (default: 42)")
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 4) - 1))
    parser.add_argument("--no-baseline", action="store_true", help="Skip v043_roster baseline")
    args = parser.parse_args()

    configs = ["v044_roster"] if args.no_baseline else ["v044_roster", "v043_roster"]
    tasks = [
        (cfg, pcount, args.seed + i)
        for cfg in configs
        for pcount in (2, 3, 4)
        for i in range(args.runs)
    ]

    with mp.Pool(processes=args.workers) as pool:
        all_records = pool.map(simulate_game, tasks)

    for cfg in configs:
        sub = [r for r in all_records if r["config"] == cfg]
        print(summarize(sub, cfg))
        print()


if __name__ == "__main__":
    main()
