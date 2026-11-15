#!/usr/bin/env python3
"""Phase 63 Blue Die Secret & Economy Rebalance Paired Sweep (`v0.43.0` vs `v0.43.1`).

Implements the 6-cell paired Monte Carlo validation matrix from
`docs/specs/phase63_blue_die_balance_spec.md` (§5):
- Cell 1A / 1B (2P): `v043_roster` vs `v043_1_roster`, seeds 63000..63599 (600 games)
- Cell 2A / 2B (3P): `v043_roster` vs `v043_1_roster`, seeds 63600..64199 (600 games)
- Cell 3A / 3B (4P): `v043_roster` vs `v043_1_roster`, seeds 64200..64799 (600 games)
"""

from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.bots.accelerationist import AccelerationistBot
from sim.bots.adaptive_balanced import AdaptiveBalancedBot
from sim.bots.reckless_saboteur import RecklessSaboteurBot
from sim.config import DieColor, GameConfig
from sim.engine import GameEngine
from sim.entities import (
    COMPANIES,
    WHITE_HATS,
    get_all_variant_cards,
    get_default_version_deck,
)

ALL_CARDS = get_all_variant_cards("MARKETING")
_PREFIX_TO_COLOR = {"R": DieColor.RED, "B": DieColor.BLUE, "G": DieColor.GREEN, "Y": DieColor.YELLOW}
CARD_POOL: Dict[DieColor, List[Any]] = defaultdict(list)
for _code, _card in ALL_CARDS.items():
    if _code and _code[0] in _PREFIX_TO_COLOR:
        CARD_POOL[_PREFIX_TO_COLOR[_code[0]]].append(_card)
BOT_CLASSES = [AdaptiveBalancedBot, AccelerationistBot, RecklessSaboteurBot]
COMPANY_LIST = list(COMPANIES.values())
WHITE_HAT_LIST = list(WHITE_HATS.values())


def _run_one(n_players: int, seed: int, factory_name: str) -> Dict[str, Any]:
    rng = random.Random(seed)
    cfg_fn = getattr(GameConfig, factory_name)
    cfg = cfg_fn(num_players=n_players)

    companies = rng.sample(COMPANY_LIST, n_players)
    white_hats = rng.sample(WHITE_HAT_LIST, n_players)
    variant_cards = {c: rng.choice(cards) for c, cards in CARD_POOL.items()}
    bots = [rng.choice(BOT_CLASSES)(i) for i in range(n_players)]

    engine = GameEngine(
        config=cfg,
        bots=bots,
        seed=seed,
        variant_cards=variant_cards,
        version_deck=get_default_version_deck(),
        companies=companies,
        white_hats=white_hats,
    )
    res = engine.run_game()
    state = engine.state

    blue_face_sec = 0
    banked_sec = 0
    leader_bonus_sec = 0
    blue_bought = 0
    defense_levels = []
    pr_levels = []
    triage_levels = []
    blue_co_defense_levels = []
    company_results = []

    for p in state.players:
        sbs = p.secrets_by_source
        blue_face_sec += sbs.get("blue_face", 0)
        banked_sec += sum(v for k, v in sbs.items() if k.startswith("secret_face_"))
        leader_bonus_sec += sbs.get("market_leader_bonus", 0)

        owned_blue = sum(1 for d in p.total_dice if d.color == DieColor.BLUE)
        started_blue = 1 if (p.company_color or "").lower() == "blue" else 0
        blue_bought += max(0, owned_blue - started_blue)

        defense_levels.append(p.defense_level)
        pr_levels.append(p.patent_level)
        triage_levels.append(p.triage_level)
        if started_blue:
            blue_co_defense_levels.append(p.defense_level)

        co_name = p.company.code.value if p.company else "UNKNOWN"
        company_results.append({
            "company": co_name,
            "won": (p.player_id == res.winner_id),
        })

    winner_secrets = 0
    if res.winner_id is not None:
        for r in res.rankings:
            if r["player_id"] == res.winner_id:
                winner_secrets = r["secrets"]
                break

    return {
        "rounds": res.total_rounds,
        "end_reason": res.end_reason.value,
        "is_total_wipeout": res.is_total_wipeout,
        "winner_secrets": winner_secrets,
        "blue_face_sec": blue_face_sec,
        "banked_sec": banked_sec,
        "leader_bonus_sec": leader_bonus_sec,
        "blue_bought": blue_bought,
        "defense_levels": defense_levels,
        "pr_levels": pr_levels,
        "triage_levels": triage_levels,
        "blue_co_defense_levels": blue_co_defense_levels,
        "company_results": company_results,
    }


def _summarize_cell(records: List[Dict[str, Any]], n_players: int) -> Dict[str, Any]:
    n = len(records)
    rounds = [r["rounds"] for r in records]
    end_counts = Counter(r["end_reason"] for r in records)
    wipeouts = sum(1 for r in records if r["is_total_wipeout"])
    win_secs = [r["winner_secrets"] for r in records if not r["is_total_wipeout"]]

    total_blue_face = sum(r["blue_face_sec"] for r in records)
    total_banked = sum(r["banked_sec"] for r in records)
    total_leader = sum(r["leader_bonus_sec"] for r in records)
    total_blue_bought = sum(r["blue_bought"] for r in records)

    all_def = [x for r in records for x in r["defense_levels"]]
    all_pr = [x for r in records for x in r["pr_levels"]]
    all_tri = [x for r in records for x in r["triage_levels"]]
    blue_co_def = [x for r in records for x in r["blue_co_defense_levels"]]

    co_games: Dict[str, int] = defaultdict(int)
    co_wins: Dict[str, int] = defaultdict(int)
    for r in records:
        for cr in r["company_results"]:
            co_games[cr["company"]] += 1
            if cr["won"]:
                co_wins[cr["company"]] += 1

    co_win_rates = {
        co: round(co_wins[co] / co_games[co] * 100.0, 2) if co_games[co] else 0.0
        for co in sorted(co_games)
    }

    return {
        "games": n,
        "players": n_players,
        "rounds_mean": round(statistics.mean(rounds), 3),
        "rounds_stdev": round(statistics.stdev(rounds), 3) if n > 1 else 0.0,
        "rounds_min": min(rounds),
        "rounds_max": max(rounds),
        "end_trigger_pct": {k: round(v / n * 100.0, 2) for k, v in sorted(end_counts.items())},
        "total_wipeout_pct": round(wipeouts / n * 100.0, 2),
        "winner_secrets_mean": round(statistics.mean(win_secs), 3) if win_secs else 0.0,
        "blue_face_secrets_per_game": round(total_blue_face / n, 3),
        "banked_secrets_per_game": round(total_banked / n, 3),
        "leader_bonus_secrets_per_game": round(total_leader / n, 3),
        "direct_to_banked_ratio": round(total_blue_face / max(1, total_banked), 3),
        "blue_dice_bought_per_player": round(total_blue_bought / (n * n_players), 3),
        "defense_level_mean": round(statistics.mean(all_def), 3),
        "blue_co_defense_level_mean": round(statistics.mean(blue_co_def), 3) if blue_co_def else 0.0,
        "pr_level_mean": round(statistics.mean(all_pr), 3),
        "triage_level_mean": round(statistics.mean(all_tri), 3),
        "company_win_rate_pct": co_win_rates,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 63 Blue Die Balance Paired Sweep")
    parser.add_argument("--games-per-cell", type=int, default=600)
    parser.add_argument(
        "--output",
        type=str,
        default="sim_results/phase63_blue_balance_sweep.json",
    )
    args = parser.parse_args()

    cells = [
        ("2P_control_v043", 2, "v043_roster", 63000),
        ("2P_phase63_v043_1", 2, "v043_1_roster", 63000),
        ("3P_control_v043", 3, "v043_roster", 63600),
        ("3P_phase63_v043_1", 3, "v043_1_roster", 63600),
        ("4P_control_v043", 4, "v043_roster", 64200),
        ("4P_phase63_v043_1", 4, "v043_1_roster", 64200),
    ]

    summary: Dict[str, Any] = {}
    for label, n_players, factory_name, base_seed in cells:
        records = [
            _run_one(n_players, base_seed + i, factory_name)
            for i in range(args.games_per_cell)
        ]
        summary[label] = _summarize_cell(records, n_players)
        s = summary[label]
        print(
            f"[{label}] rounds={s['rounds_mean']}±{s['rounds_stdev']} | "
            f"wipeout={s['total_wipeout_pct']}% | "
            f"blue_face/g={s['blue_face_secrets_per_game']} | "
            f"blue_co_def={s['blue_co_defense_level_mean']} | "
            f"DTO={s['company_win_rate_pct'].get('DTO', 0)}% "
            f"AEGIS={s['company_win_rate_pct'].get('AEGIS', 0)}%"
        )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Saved sweep summary to {out_path}")


if __name__ == "__main__":
    main()
