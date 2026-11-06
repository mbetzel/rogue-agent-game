"""Rogue Agent v0.35.0 telemetry sweep: Research Track Rebalance vs the v0.34.0 baseline.

Phase 43 (Scenario Execution & Telemetry, product-owner).

Runs N matches per pod (2P / 3P / 4P) on explicit base seeds under the v0.35 default
(``GameConfig()`` = SIX_PHASE + V035_FIVE_LEVEL) and the SAME seeds under ``GameConfig.legacy_v034``.
Match setup mirrors ``scripts/run_v340_telemetry_sweep.py``: 5-bot rotation, ``get_random_setup``
STANDARD, random Client Companies and White Hat Operatives, starting_money=6, 3 Gray + 1 Purple,
1 Purple reserve, enable_corporate_asymmetry=True.

All telemetry is read from the engine's native v0.35 ledger (``EndGameResult.rankings``); no wrappers,
no engine changes.

Usage:
  PYTHONDONTWRITEBYTECODE=1 python3 scripts/run_v350_telemetry_sweep.py --games 3000 --seed 42
  PYTHONDONTWRITEBYTECODE=1 python3 scripts/run_v350_telemetry_sweep.py --replay 400017 --players 4 --cfg v035
"""

from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import sys
import time
from collections import Counter, defaultdict
from typing import Any, Dict, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sim.bots import (  # noqa: E402
    AccelerationistBot,
    AdaptiveBalancedBot,
    RecklessSaboteurBot,
    SecOpsTurtleBot,
    VentureGreedBot,
)
from sim.config import EndGameReason, GameConfig  # noqa: E402
from sim.engine.core import GameEngine  # noqa: E402
from sim.entities import get_random_companies, get_random_setup, get_random_white_hats  # noqa: E402

BOT_CLASSES = [AdaptiveBalancedBot, SecOpsTurtleBot, VentureGreedBot, AccelerationistBot, RecklessSaboteurBot]
CONFIGS = ("V035", "V034")
TRACKS = ("DEFENSE", "TRIAGE", "RELEASE", "PATENT")


def build_engine(cfg_name: str, num_players: int, match_idx: int, match_seed: int) -> GameEngine:
    rng = random.Random(match_seed)
    bots = [BOT_CLASSES[(match_idx * num_players + i) % len(BOT_CLASSES)](i) for i in range(num_players)]
    rng.shuffle(bots)
    for i, b in enumerate(bots):
        b.player_id = i
    variants, version_deck = get_random_setup(rng, profile="STANDARD")
    companies = get_random_companies(num_players, rng)
    white_hats = get_random_white_hats(num_players, rng)
    kw = dict(
        num_players=num_players, starting_money=6, starting_gray_dice=3, starting_purple_dice=1,
        starting_purple_reserve=1, corruption_track_profile="STANDARD", enable_corporate_asymmetry=True,
    )
    cfg = GameConfig(**kw) if cfg_name == "V035" else GameConfig.legacy_v034(**kw)
    return GameEngine(config=cfg, bots=bots, seed=match_seed, variant_cards=variants, version_deck=version_deck,
                      companies=companies, white_hats=white_hats)


def pct(n: float, d: float) -> float:
    return n / d if d else 0.0


def mean(xs: List[float]) -> float:
    return statistics.mean(xs) if xs else 0.0


def run_pod(cfg_name: str, num_players: int, games: int, base_seed: int) -> Dict[str, Any]:
    rounds: List[int] = []
    reasons: Counter = Counter()
    pz_games = 0
    survivors = 0
    final_secrets: List[int] = []
    survivor_secrets: List[int] = []
    winner_secrets: List[int] = []
    research: List[int] = []
    research_src: Counter = Counter()
    research_left: List[int] = []
    level_dist = {t: Counter() for t in TRACKS}
    steps_total: List[int] = []
    l4_count_dist: Counter = Counter()
    maxed_track: Counter = Counter()
    seats_maxing = 0
    all_maxed = 0
    bt: Counter = Counter()  # (track, level, outcome)
    tl3_reasons: Counter = Counter()
    tl3_colors: Counter = Counter()
    l4_pay = Counter()
    l4_holders = Counter()
    patent_secrets: List[int] = []
    purple_lost = 0
    purple_lost_games = 0
    purple_final: List[int] = []
    dto = {"seats": 0, "slush_used": 0, "slush_versions_used": 0}
    groups = {k: {"m": Counter(), "w": Counter(), "s": Counter()} for k in ("bot", "company", "op")}
    outliers: Dict[str, List[Dict[str, Any]]] = {"round_le_2_wipeout": [], "rounds_le_3": [], "rounds_ge_20": [],
                                                 "rounds_ge_14": [], "round_limit": []}

    for idx in range(games):
        seed = base_seed + num_players * 100_000 + idx
        eng = build_engine(cfg_name, num_players, idx, seed)
        res = eng.run_game()
        st = eng.state
        n_r = res.total_rounds
        rounds.append(n_r)
        reasons[res.end_reason.value] += 1
        rec = {"seed": seed, "match_idx": idx, "rounds": n_r, "end_reason": res.end_reason.value}
        if n_r <= 2 and res.is_total_wipeout:
            outliers["round_le_2_wipeout"].append(rec)
        if n_r <= 3:
            outliers["rounds_le_3"].append(rec)
        if n_r >= 20:
            outliers["rounds_ge_20"].append(rec)
        if n_r >= 14:
            outliers["rounds_ge_14"].append(rec)
        if res.end_reason == EndGameReason.ROUND_LIMIT:
            outliers["round_limit"].append(rec)
        if any(p.is_patient_zero for p in st.players):
            pz_games += 1
        w_ids = list(getattr(res, "winner_ids", None) or ([res.winner_id] if res.winner_id is not None else []))
        game_purple_lost = 0
        for r in res.rankings:
            p = next(pp for pp in st.players if pp.player_id == r["player_id"])
            surv = not r["is_patient_zero"]
            win = (1.0 / len(w_ids)) if (p.player_id in w_ids and (surv or res.is_total_wipeout)) else 0.0
            survivors += surv
            final_secrets.append(r["secrets"])
            if surv:
                survivor_secrets.append(r["secrets"])
            if win:
                winner_secrets.append(r["secrets"])
            research.append(r.get("research_earned_total", 0))
            research_src.update(r.get("research_earned_by_source", {}))
            research_left.append(p.patches)
            lv = r["final_track_levels"]
            for t in TRACKS:
                level_dist[t][lv[t]] += 1
            steps_total.append(sum(lv.values()))
            n4 = sum(1 for t in TRACKS if lv[t] >= 4)
            l4_count_dist[n4] += 1
            if n4:
                seats_maxing += 1
                for t in TRACKS:
                    if lv[t] >= 4:
                        maxed_track[t] += 1
                        l4_holders[t] += 1
            if n4 == 4:
                all_maxed += 1
            for b in r.get("breakthroughs", []):
                bt[(b["track"], b["level"], b["outcome"])] += 1
                if b["track"] == "TRIAGE" and b["level"] == 3:
                    if b["outcome"] == "TAKEN":
                        tl3_colors[b["detail"].get("new_color")] += 1
                    else:
                        tl3_reasons[b["detail"].get("reason", b["outcome"].lower())] += 1
            l4_pay.update(r.get("l4_payouts", {}))
            patent_secrets.append(r.get("patent_secrets_gained", 0))
            owned_p = r.get("purple_dice_owned_final", 0)
            purple_final.append(owned_p)
            gained = 1 + (1 - p.personal_purple_reserve)  # starter + reserve die drawn (purchase or Patents L3)
            lost = max(0, gained - owned_p)
            purple_lost += lost
            game_purple_lost += lost
            comp = p.company.code.value if p.company else "NONE"
            if comp == "DTO":
                dto["seats"] += 1
                dto["slush_used"] += bool(r.get("slush_fund_used_game"))
                dto["slush_versions_used"] += sum(r.get(f"ability_v{i}_status") == "USED" for i in (1, 2, 3))
            for gk, label in (("bot", r["bot_name"]), ("company", comp),
                              ("op", p.white_hat.code.value if p.white_hat else "NONE")):
                g = groups[gk]
                g["m"][label] += 1
                g["s"][label] += surv
                g["w"][label] += win
        purple_lost_games += game_purple_lost > 0

    pg = games * num_players

    def group_out(gk: str) -> Dict[str, Dict[str, float]]:
        g = groups[gk]
        return {k: {"seats": g["m"][k], "win_rate": pct(g["w"][k], g["m"][k]),
                    "survival_rate": pct(g["s"][k], g["m"][k])} for k in sorted(g["m"])}

    bots, comps, ops = group_out("bot"), group_out("company"), group_out("op")

    def spread(d):
        v = [x["win_rate"] for x in d.values()]
        return (max(v) - min(v)) * 100

    bt_out: Dict[str, Dict[str, float]] = {}
    for (t, lv, oc), n in sorted(bt.items()):
        bt_out.setdefault(f"{t}_L{lv}", {})[oc] = n
    for k, v in bt_out.items():
        v["per_seat"] = pct(sum(v.values()), pg)
    tl3 = bt_out.get("TRIAGE_L3", {})
    tl3_n = sum(tl3.get(k, 0) for k in ("TAKEN", "DECLINED", "FORFEITED"))
    return {
        "config": cfg_name, "num_players": num_players, "games": games, "player_games": pg,
        "seed_range": [base_seed + num_players * 100_000, base_seed + num_players * 100_000 + games - 1],
        "mean_rounds": mean(rounds), "median_rounds": statistics.median(rounds),
        "min_rounds": min(rounds), "max_rounds": max(rounds),
        "round_hist": dict(sorted(Counter(rounds).items())),
        "end_reasons": {k: pct(v, games) for k, v in reasons.items()},
        "patient_zero_game_rate": pct(pz_games, games),
        "player_survival": pct(survivors, pg),
        "mean_final_secrets": mean(final_secrets), "mean_survivor_secrets": mean(survivor_secrets),
        "mean_winner_secrets": mean(winner_secrets),
        "max_final_secrets": max(final_secrets),
        "research_mean": mean(research), "research_median": statistics.median(research),
        "research_p10_p90": [sorted(research)[pg // 10], sorted(research)[(pg * 9) // 10]],
        "research_by_source_per_seat": {k: pct(v, pg) for k, v in research_src.most_common()},
        "research_unspent_end": mean(research_left),
        "track_level_dist": {t: {str(k): pct(v, pg) for k, v in sorted(c.items())} for t, c in level_dist.items()},
        "mean_track_steps": mean(steps_total),
        "l4_tracks_per_seat_dist": {str(k): pct(v, pg) for k, v in sorted(l4_count_dist.items())},
        "seats_maxing_any_track": pct(seats_maxing, pg),
        "maxed_track_share": {t: pct(maxed_track[t], sum(maxed_track.values())) for t in TRACKS},
        "all_tracks_maxed_seats": all_maxed,
        "breakthroughs": bt_out,
        "triage_l3": {"resolutions": tl3_n, "take_rate": pct(tl3.get("TAKEN", 0), tl3_n),
                      "declined_rate": pct(tl3.get("DECLINED", 0), tl3_n),
                      "forfeit_rate": pct(tl3.get("FORFEITED", 0), tl3_n),
                      "forfeit_reasons": dict(tl3_reasons), "colors": dict(tl3_colors)},
        "l4_payouts_total": dict(l4_pay),
        "l4_payouts_per_holder": {
            "defense_cash": pct(l4_pay["defense_cash"], l4_holders["DEFENSE"]),
            "triage_research": pct(l4_pay["triage_research"], l4_holders["TRIAGE"]),
            "release_rerolls_used": pct(l4_pay["release_rerolls_used"], l4_holders["RELEASE"]),
            "patent_secrets_at_L4": pct(l4_pay["patent_secrets"], l4_holders["PATENT"]),
        },
        "l4_holders": dict(l4_holders),
        "patent_secrets_per_seat": mean(patent_secrets),
        "purple_lost_total": purple_lost, "purple_lost_per_seat": pct(purple_lost, pg),
        "games_with_purple_lost": pct(purple_lost_games, games),
        "purple_owned_end_mean": mean(purple_final),
        "dto": {**dto, "slush_used_rate": pct(dto["slush_used"], dto["seats"]),
                "slush_versions_used_per_seat": pct(dto["slush_versions_used"], dto["seats"])},
        "bots": bots, "companies": comps, "operatives": ops,
        "bot_win_spread_pts": spread(bots), "company_win_spread_pts": spread(comps),
        "white_hat_win_spread_pts": spread(ops),
        "outliers": outliers,
    }


def guardrails(r: Dict[str, Any]) -> Dict[str, str]:
    er = r["end_reasons"]
    share = max(r["maxed_track_share"].values()) if r["seats_maxing_any_track"] else 0.0
    g = {
        "rounds_8_11": 8.0 <= r["mean_rounds"] <= 11.0 and 8.0 <= r["median_rounds"] <= 11.0,
        "singularity_le_45": er.get("singularity", 0.0) <= 0.45,
        "wipeout_le_15": er.get("total_wipeout", 0.0) <= 0.15,
        "bot_spread_le_45": r["bot_win_spread_pts"] <= 45.0,
        "research_12_14": 12.0 <= r["research_mean"] <= 14.0,
        "no_seat_maxes_all": r["all_tracks_maxed_seats"] == 0,
        "max_track_share_le_50": share <= 0.50,
    }
    return {k: ("PASS" if v else "FAIL") for k, v in g.items()}


def replay(seed: int, players: int, cfg: str, base_seed: int) -> None:
    idx = seed - base_seed - players * 100_000
    eng = build_engine("V035" if cfg == "v035" else "V034", players, idx, seed)
    res = eng.run_game()
    print(f"seed={seed} players={players} cfg={cfg} rounds={res.total_rounds} end={res.end_reason.value}")
    for t in eng.telemetry_history:
        snaps = " | ".join(f"P{s['player_id']}:{s['bot_name'][:6]} ${s['money']} S{s['secrets']}"
                           f"{' PZ' if s['is_patient_zero'] else ''}" for s in t.player_snapshots)
        print(f"  R{t.round_number} {t.active_version_name} trk={t.corruption_track} :: {snaps}")
    for r in res.rankings:
        print(f"  rank {r['rank']}: P{r['player_id']} {r['bot_name']} S={r['secrets']} ${r['money']} "
              f"🔬={r.get('research_earned_total')} lv={r.get('final_track_levels')} PZ={r['is_patient_zero']}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Rogue Agent v0.35.0 research-track telemetry sweep")
    ap.add_argument("--games", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--json", default="docs/findings/v350_telemetry_summary.json")
    ap.add_argument("--replay", type=int, default=None)
    ap.add_argument("--players", type=int, default=2)
    ap.add_argument("--cfg", choices=["v035", "v034"], default="v035")
    args = ap.parse_args()
    if args.replay is not None:
        replay(args.replay, args.players, args.cfg, args.seed)
        return
    t0 = time.time()
    results: Dict[str, Dict[str, Any]] = {c: {} for c in CONFIGS}
    for c in CONFIGS:
        for n in (2, 3, 4):
            ts = time.time()
            r = run_pod(c, n, args.games, args.seed)
            r["seconds"] = time.time() - ts
            results[c][f"{n}P"] = r
            print(f"[{c} {n}P] {r['seconds']:.1f}s rounds={r['mean_rounds']:.2f} "
                  f"end={ {k: round(v, 3) for k, v in r['end_reasons'].items()} } 🔬={r['research_mean']:.2f} "
                  f"spread={r['bot_win_spread_pts']:.1f}", flush=True)
    gr = {c: {n: guardrails(results[c][n]) for n in results[c]} for c in CONFIGS}
    payload = {"metadata": {"version": "v0.35.0", "baseline": "GameConfig.legacy_v034 (same seeds)",
                            "base_seed": args.seed, "seed_formula": "base_seed + num_players*100000 + match_idx",
                            "games_per_pod": args.games, "elapsed_seconds": time.time() - t0},
               "guardrails": gr, "results": results}
    if args.json:
        os.makedirs(os.path.dirname(args.json), exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)
        print(f"JSON written to {args.json}")
    print(json.dumps(gr, indent=2))


if __name__ == "__main__":
    main()
