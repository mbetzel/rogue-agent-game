"""Rogue Agent v0.36 Red rebalance sweep (Phase 44, FINDINGS.md §31).

ARCHIVED: §31 results are in ``sim_results/v360_red_rebalance_sweep.json``. The ``REDDIE`` / ``PACKAGE`` cells
(the ``red_die_profile`` / ``V036_RED`` lever) were removed in v0.36.0 (spec §2.6). Kept runnable because
``scripts/explore_v360_market_collapse_probe.py`` imports ``build_engine`` / ``_resolve_hook``.

Cells:
  V035      : $1 / unblocked Red cube, Red die = Block 1 Red, +$2 x3
  RANSOM2   : $2 / unblocked Red cube (``red_ransom_per_cube=2``, RANSOM only)

Same seeds across configs. Match setup mirrors scripts/run_v350_telemetry_sweep.py.
Red telemetry is read from player.last_defense_breakdown (wrapped per resolution) and
market purchases (wrapped create_colored_die in phase6_operations).

Usage:
  PYTHONDONTWRITEBYTECODE=1 python3 scripts/run_v360_red_rebalance_sweep.py --games 2000 --seed 42
"""

from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import sys
from collections import Counter
from typing import Any, Dict, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sim.bots import (  # noqa: E402
    AccelerationistBot,
    AdaptiveBalancedBot,
    RecklessSaboteurBot,
    SecOpsTurtleBot,
    VentureGreedBot,
)
from sim.config import GameConfig  # noqa: E402
from sim.engine import phase4_attack_resolution as p4  # noqa: E402
from sim.engine import phase6_operations as p6  # noqa: E402
from sim.engine.core import GameEngine  # noqa: E402
from sim.entities import get_random_companies, get_random_setup, get_random_white_hats  # noqa: E402

BOT_CLASSES = [AdaptiveBalancedBot, SecOpsTurtleBot, VentureGreedBot, AccelerationistBot, RecklessSaboteurBot]
CONFIGS = {
    "V035": dict(red_ransom_per_cube=1),
    "RANSOM2": dict(red_ransom_per_cube=2),
}

# ---- telemetry hooks -------------------------------------------------------
TALLY: Counter = Counter()
_orig_resolve = p4.resolve_player_defense_and_wear
_orig_create = p6.create_colored_die


def _resolve_hook(engine, player, *a, **kw):
    out = _orig_resolve(engine, player, *a, **kw)
    b = getattr(player, "last_defense_breakdown", None)
    if b:
        rate = engine.config.red_ransom_per_cube
        TALLY["resolutions"] += 1
        TALLY["red_incoming"] += b["effective_attacks"]["red"]
        TALLY["red_blocked"] += b["blocked"]["red"]
        TALLY["red_blocked_by_color_shield"] += min(b["color_shields"]["red"], b["effective_attacks"]["red"])
        TALLY["red_blocked_by_any"] += b["any_allocated"]["red"]
        TALLY["red_unblocked"] += b["unblocked"]["red"]
        TALLY["ransom_paid"] += b["unblocked"]["red"] * rate - b["unpaid_ransom"]
        TALLY["leaks"] += int(b["flat_ransom_leak"])
        TALLY["red_shield_capacity"] += b["color_shields"]["red"]
        TALLY["blue_unblocked"] += b["unblocked"]["blue"]
        TALLY["green_unblocked"] += b["unblocked"]["green"]
    return out


def _create_hook(*a, **kw):
    die = _orig_create(*a, **kw)
    TALLY[f"bought_{die.color.value}"] += 1
    return die


p4.resolve_player_defense_and_wear = _resolve_hook
p6.create_colored_die = _create_hook


def build_engine(cfg_name: str, num_players: int, match_idx: int, match_seed: int) -> GameEngine:
    rng = random.Random(match_seed)
    bots = [BOT_CLASSES[(match_idx * num_players + i) % len(BOT_CLASSES)](i) for i in range(num_players)]
    rng.shuffle(bots)
    for i, b in enumerate(bots):
        b.player_id = i
    variants, version_deck = get_random_setup(rng, profile="STANDARD")
    companies = get_random_companies(num_players, rng)
    white_hats = get_random_white_hats(num_players, rng)
    cfg = GameConfig(
        num_players=num_players, starting_money=6, starting_gray_dice=3, starting_purple_dice=1,
        starting_purple_reserve=1, corruption_track_profile="STANDARD", enable_corporate_asymmetry=True,
        **CONFIGS[cfg_name],
    )
    return GameEngine(config=cfg, bots=bots, seed=match_seed, variant_cards=variants, version_deck=version_deck,
                      companies=companies, white_hats=white_hats)


def pct(n: float, d: float) -> float:
    return n / d if d else 0.0


def run_pod(cfg_name: str, num_players: int, games: int, base_seed: int) -> Dict[str, Any]:
    TALLY.clear()
    rounds: List[int] = []
    reasons: Counter = Counter()
    pz = 0
    secrets: List[int] = []
    money_end: List[int] = []
    comp_m: Counter = Counter()
    comp_w: Counter = Counter()
    for idx in range(games):
        seed = base_seed + num_players * 100_000 + idx
        eng = build_engine(cfg_name, num_players, idx, seed)
        res = eng.run_game()
        rounds.append(res.total_rounds)
        reasons[res.end_reason.value] += 1
        pz += any(p.is_patient_zero for p in eng.state.players)
        w_ids = list(getattr(res, "winner_ids", None) or ([res.winner_id] if res.winner_id is not None else []))
        for r in res.rankings:
            p = next(pp for pp in eng.state.players if pp.player_id == r["player_id"])
            secrets.append(r["secrets"])
            money_end.append(r["money"])
            comp = p.company.code.value if p.company else "NONE"
            comp_m[comp] += 1
            if p.player_id in w_ids:
                comp_w[comp] += 1.0 / len(w_ids)
    pg = games * num_players
    t = TALLY
    bought = {c: pct(t[f"bought_{c}"], pg) for c in ("red", "blue", "green", "yellow", "purple")}
    buy_total = sum(t[f"bought_{c}"] for c in ("red", "blue", "green", "yellow"))
    comp_wr = {k: pct(comp_w[k], comp_m[k]) for k in comp_m}
    return {
        "config": cfg_name, "players": num_players, "games": games,
        "mean_rounds": statistics.mean(rounds), "median_rounds": statistics.median(rounds),
        "end_reasons": {k: round(pct(v, games), 3) for k, v in reasons.items()},
        "patient_zero_game_rate": pct(pz, games),
        "mean_final_secrets": statistics.mean(secrets),
        "mean_final_money": statistics.mean(money_end),
        "market_buys_per_seat": bought,
        "red_share_of_market_buys": pct(t["bought_red"], buy_total),
        "red_incoming_per_resolution": pct(t["red_incoming"], t["resolutions"]),
        "red_block_rate": pct(t["red_blocked"], t["red_incoming"]),
        "red_blocked_by_color_shield_share": pct(t["red_blocked_by_color_shield"], t["red_blocked"]),
        "red_shield_value_per_resolution": pct(t["red_shield_capacity"], t["resolutions"]),
        "ransom_paid_per_seat": pct(t["ransom_paid"], pg),
        "leak_rate_per_resolution": pct(t["leaks"], t["resolutions"]),
        "leaks_per_seat": pct(t["leaks"], pg),
        "blue_unblocked_per_resolution": pct(t["blue_unblocked"], t["resolutions"]),
        "green_unblocked_per_resolution": pct(t["green_unblocked"], t["resolutions"]),
        "company_win_rates": dict(sorted(comp_wr.items())),
        "company_win_spread_pts": (max(comp_wr.values()) - min(comp_wr.values())) * 100,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="sim_results/v360_red_rebalance_sweep.json")
    args = ap.parse_args()
    results = []
    for n in (2, 3, 4):
        for cfg in CONFIGS:
            r = run_pod(cfg, n, args.games, args.seed)
            results.append(r)
            print(f"{n}P {cfg:8s} rounds={r['mean_rounds']:.2f} PZ={r['patient_zero_game_rate']:.3f} "
                  f"redBuys/seat={r['market_buys_per_seat']['red']:.2f} redShare={r['red_share_of_market_buys']:.3f} "
                  f"redBlock={r['red_block_rate']:.3f} ransom/seat=${r['ransom_paid_per_seat']:.2f} "
                  f"leaks/seat={r['leaks_per_seat']:.2f} secrets={r['mean_final_secrets']:.2f} "
                  f"$end={r['mean_final_money']:.1f} compSpread={r['company_win_spread_pts']:.1f} "
                  f"ends={r['end_reasons']}", flush=True)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump({"games_per_pod": args.games, "seed": args.seed, "results": results}, f, indent=2)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
