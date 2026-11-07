"""Rogue Agent v0.36.0 Market Share sweep (spec docs/specs/v360_market_share_red_rework_spec.md §8).

Cells (same seeds in every cell, paired): C0 V035 baseline, C1 V036 acceptance, plus tuning / ablation cells.
Telemetry comes only from engine fields (EndGameResult / RoundTelemetry), no monkeypatched hooks.
Match setup mirrors scripts/run_v360_red_rebalance_sweep.build_engine (seeded rng -> bot rotation + shuffle,
get_random_setup(rng, "STANDARD"), get_random_companies, get_random_white_hats).

Usage:
  PYTHONDONTWRITEBYTECODE=1 python3 scripts/run_v360_market_share_sweep.py                 # full spec sweep
  PYTHONDONTWRITEBYTECODE=1 python3 scripts/run_v360_market_share_sweep.py --games 50 --cells V035,V036
  PYTHONDONTWRITEBYTECODE=1 python3 scripts/run_v360_market_share_sweep.py --cells GRID,V035 --workers 8   # re-sweep grid
  options: --games N (overrides every cell's games per pod), --scale F (multiplies spec counts),
           --pods 2,3,4, --cells A,B, --workers K, --out PATH
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import math
import os
import random
import statistics
import sys
from collections import Counter, defaultdict
from typing import Any, Callable, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sim.bots import (  # noqa: E402
    AccelerationistBot,
    AdaptiveBalancedBot,
    RecklessSaboteurBot,
    SecOpsTurtleBot,
    VentureGreedBot,
)
from sim.bots.market_share_policy import policy_for  # noqa: E402
from sim.config import AnyShieldPolicy, GameConfig  # noqa: E402
from sim.engine.core import GameEngine  # noqa: E402
from sim.entities import get_random_companies, get_random_setup, get_random_white_hats  # noqa: E402

BOT_CLASSES = [AdaptiveBalancedBot, SecOpsTurtleBot, VentureGreedBot, AccelerationistBot, RecklessSaboteurBot]
BASE_KW = dict(starting_money=6, starting_gray_dice=3, starting_purple_dice=1, starting_purple_reserve=1,
               corruption_track_profile="STANDARD", enable_corporate_asymmetry=True)
V036_START = {2: 17, 3: 18, 4: 18}  # balance iteration 1 (User 2026-11-06)
V1_DROPPED = {"v2.0": 4}  # v036() default: only the v2.0 -> v3.0 comparison
V1_KEPT = {"v1.0": 2, "v2.0": 4}
# v036() now uses 7/7/8 (final tune, plan §11); the earlier grid points are kept for comparison.
GRID_SECRETS = {"7_7_8": {2: 7, 3: 7, 4: 8}, "8_10_11": {2: 8, 3: 10, 4: 11}, "8_9_10": {2: 8, 3: 9, 4: 10},
                "8_8_9": {2: 8, 3: 8, 4: 9}}


def _regain(cap4: int, cost4: int) -> Dict[str, Any]:
    return dict(share_regain_cap_by_level={0: 1, 1: 1, 2: 2, 3: 2, 4: cap4},
                share_regain_cost_by_level={0: 2, 1: 2, 2: 2, 3: 2, 4: cost4})


def _shift_start(d: int) -> Dict[str, Any]:
    return dict(market_share_start_by_player_count={n: v + d for n, v in V036_START.items()})


def _random_focus(bots: List[Any]) -> None:
    for b in bots:
        b.research_focus_mode = "random"


def _kamikaze(bots: List[Any]) -> None:
    for b in bots:
        if isinstance(b, RecklessSaboteurBot):
            b.market_share_policy = dataclasses.replace(policy_for(b), collapse_seeking=True)


# name -> (factory, config overrides, bot modifier, spec games per pod)
CELLS: Dict[str, Tuple[Callable[..., GameConfig], Dict[str, Any], Optional[Callable[[List[Any]], None]], int]] = {
    "V035": (GameConfig, {}, None, 3000),
    "V036": (GameConfig.v036, {}, None, 3000),
    "L4-RATE": (GameConfig.v036, _regain(2, 1), None, 1000),
    "L4-BOTH": (GameConfig.v036, _regain(3, 1), None, 1000),
    "PAYOUT-LOW": (GameConfig.v036, dict(version_share_payout={"v2.0": 2}), None, 1000),
    "PAYOUT-HIGH": (GameConfig.v036, dict(version_share_payout={"v2.0": 6}), None, 1000),
    "V1-KEPT": (GameConfig.v036, dict(version_share_payout=dict(V1_KEPT)), None, 1000),
    "NO_PAYOUT": (GameConfig.v036, dict(version_share_payout={}), None, 1000),
    "MS-2": (GameConfig.v036, _shift_start(-2), None, 1000),
    "MS+2": (GameConfig.v036, _shift_start(+2), None, 1000),
    "NAIVE": (GameConfig.v036, dict(market_share_bot_policy="NAIVE"), None, 1000),
    "RANDOM_FOCUS": (GameConfig.v036, {}, _random_focus, 1000),
    "KAMIKAZE": (GameConfig.v036, {}, _kamikaze, 1000),
    "TIERS": (GameConfig.v036, dict(any_shield_policy=AnyShieldPolicy.V035_TIERS), None, 1000),
}
# Re-sweep grid (game-designer, balance iteration 1): Market Share 17/18/18 x starting Secrets x v1.0 payout
# {dropped, $2}, each also with RANDOM_FOCUS. Select with --cells GRID (all) or by name, e.g. G-S8_9_10-V1D.
GRID_CELLS: List[str] = []
for _sk, _sec in GRID_SECRETS.items():
    for _vk, _pay in (("V1D", V1_DROPPED), ("V1K", V1_KEPT)):
        for _rf, _mod in (("", None), ("-RF", _random_focus)):
            _name = f"G-S{_sk}-{_vk}{_rf}"
            CELLS[_name] = (GameConfig.v036, dict(starting_secrets_by_player_count=dict(_sec),
                                                  version_share_payout=dict(_pay)), _mod, 2000)
            GRID_CELLS.append(_name)
THREE_WAY = ("patient_zero", "singularity", "market_collapse")


def build_engine(cell: str, num_players: int, match_idx: int, match_seed: int) -> GameEngine:
    factory, overrides, bot_mod, _ = CELLS[cell]
    rng = random.Random(match_seed)
    bots = [BOT_CLASSES[(match_idx * num_players + i) % len(BOT_CLASSES)](i) for i in range(num_players)]
    rng.shuffle(bots)
    for i, b in enumerate(bots):
        b.player_id = i
    if bot_mod is not None:
        bot_mod(bots)
    variants, version_deck = get_random_setup(rng, profile="STANDARD")
    companies = get_random_companies(num_players, rng)
    white_hats = get_random_white_hats(num_players, rng)
    cfg = factory(num_players=num_players, **BASE_KW, **overrides)
    return GameEngine(config=cfg, bots=bots, seed=match_seed, variant_cards=variants, version_deck=version_deck,
                      companies=companies, white_hats=white_hats)


# ---------------------------------------------------------------------------
# Stats helpers
# ---------------------------------------------------------------------------
def pct(n: float, d: float) -> float:
    return n / d if d else 0.0


def ci95(k: float, n: int) -> List[float]:
    """Wilson 95% interval for a proportion."""
    if n <= 0:
        return [0.0, 0.0]
    p, z = k / n, 1.96
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


def quantiles(xs: List[float]) -> Dict[str, float]:
    if not xs:
        return {}
    s = sorted(xs)

    def q(f: float) -> float:
        return float(s[min(len(s) - 1, int(f * (len(s) - 1) + 0.5))])

    return {"mean": round(statistics.mean(s), 3), "p10": q(0.1), "p50": q(0.5), "p90": q(0.9), "n": len(s)}


def bootstrap_spread_ci(game_rows: List[List[Tuple[str, float]]], reps: int = 200, seed: int = 12345) -> List[float]:
    """95% bootstrap interval (games resampled) for max - min company win rate, in points. Script-side RNG only."""
    if not game_rows:
        return [0.0, 0.0]
    rng = random.Random(seed)
    spreads: List[float] = []
    n = len(game_rows)
    for _ in range(reps):
        m: Counter = Counter()
        w: Counter = Counter()
        for _i in range(n):
            for comp_code, win in game_rows[rng.randrange(n)]:
                m[comp_code] += 1
                w[comp_code] += win
        rates = [w[c] / m[c] for c in m if m[c]]
        spreads.append((max(rates) - min(rates)) * 100 if rates else 0.0)
    spreads.sort()
    return [round(spreads[int(0.025 * (reps - 1))], 2), round(spreads[int(0.975 * (reps - 1))], 2)]


def three_way(reason: str) -> str:
    return "patient_zero" if reason == "total_wipeout" else reason


# ---------------------------------------------------------------------------
# Pod runner
# ---------------------------------------------------------------------------
def run_pod(cell: str, n: int, games: int, base_seed: int) -> Dict[str, Any]:
    reasons: Counter = Counter()
    split: Counter = Counter()
    rounds: List[int] = []
    by_setup: Dict[str, Dict[str, Counter]] = {"v3_card": defaultdict(Counter), "company_seat": defaultdict(Counter),
                                                "white_hat_seat": defaultdict(Counter)}
    red = Counter()
    buys: Counter = Counter()
    research_tracks = 0
    research_regain = 0
    maxed: Counter = Counter()
    comp: Dict[str, Counter] = defaultdict(Counter)
    collapse_games = 0
    collapse_kamikaze = 0
    collapse_rounds: List[int] = []
    tiebreak: Counter = Counter()
    curve: Dict[int, List[int]] = defaultdict(list)
    by_rank: Dict[int, List[int]] = defaultdict(list)
    end_money: List[int] = []
    cmp_money_seat: List[int] = []
    comp_m: Counter = Counter()
    comp_w: Counter = Counter()
    dbl = 0
    triggers_multi = 0
    seed_log: Dict[str, List[int]] = defaultdict(list)
    regain_steps = 0
    r2_uses = 0
    poach_moves = 0
    kami = Counter()  # strict-lead kamikaze vs chance
    bot_m: Counter = Counter()
    bot_w: Counter = Counter()
    game_company_rows: List[List[Tuple[str, float]]] = []
    for idx in range(games):
        seed = base_seed + n * 100_000 + idx
        eng = build_engine(cell, n, idx, seed)
        res = eng.run_game()
        r = res.end_reason.value
        reasons[r] += 1
        tw = three_way(r)
        split[tw] += 1
        rounds.append(res.total_rounds)
        if res.total_rounds <= 5:
            seed_log["rounds_le_5"].append(seed)
        if res.total_rounds >= 12:
            seed_log["rounds_ge_12"].append(seed)
        if res.is_total_wipeout and res.total_rounds <= 5:
            seed_log["wipeout_le_5"].append(seed)
        if r == "market_collapse" and res.total_rounds <= 5:
            seed_log["collapse_le_5"].append(seed)
        setup = res.setup
        by_setup["v3_card"][setup["version_cards"][-1]][tw] += 1
        for seat, c in enumerate(setup["companies"]):
            by_setup["company_seat"][f"{c}@{seat}"][tw] += 1
        for seat, w in enumerate(setup["white_hats"]):
            by_setup["white_hat_seat"][f"{w}@{seat}"][tw] += 1
        dbl += res.double_version_fill_events
        triggers_multi += int(len(res.end_triggers) > 1)
        if res.market_collapse_round is not None:
            collapse_games += 1
            collapse_rounds.append(res.market_collapse_round)
            collapse_kamikaze += int(any(res.collapse_trigger_pids_were_secret_leaders))
            ctx = res.market_collapse_context or {}
            surv = ctx.get("survivor_pids") or []
            if surv:
                k = len(res.market_collapse_pids) / len(surv)
                lead = ctx.get("strict_leader_pid")
                kami["games"] += 1
                kami["strict_lead"] += int(lead is not None and lead in res.market_collapse_pids)
                kami["strict_lead_chance"] += k if lead is not None else 0.0
                wids = set(res.winner_ids or ([res.winner_id] if res.winner_id is not None else []))
                kami["collapser_won"] += int(bool(wids & set(res.market_collapse_pids)))
                kami["collapser_won_chance"] += min(1.0, k)
        tiebreak[res.tiebreak_decided_by] += 1
        for t in res.telemetry_history:
            for pid, rb in t.red_by_player.items():
                if t.buffer_overflow or 4 not in t.phases_executed:
                    continue
                snap = {s["player_id"]: s for s in t.phase_snapshots.get(3, [])}
                if snap.get(pid, {}).get("is_patient_zero", False):
                    continue
                for k, v in rb.items():
                    red[k] += v
            for pid, ms in t.market_share_end_of_round.items():
                if ms is not None:
                    curve[t.round_number].append(ms)
            for v in t.version_comparisons:
                c = comp[v["version"]]
                c["events"] += 1
                c["paid"] += sum(v["paid"].values())
                c["forgiven"] += sum(v["forgiven"].values())
                c["gained"] += sum(v["gains"].values())
                c["all_tied"] += int(v["all_tied"])
                c["top_tie"] += int(len(v["top_pids"]) > 1)
                c["bottom_tie"] += int(len(v["bottom_pids"]) > 1)
                c["any_tie"] += int(v["all_tied"] or len(v["top_pids"]) > 1 or len(v["bottom_pids"]) > 1)
                c["spillover"] += int(v["during_spillover"])
            poach_moves += sum(e["moved"] for e in t.r3_events)
        w_ids = list(res.winner_ids or ([res.winner_id] if res.winner_id is not None else []))
        rows_c: List[Tuple[str, float]] = []
        for rk, row in enumerate(res.rankings):
            bot_m[row["bot_name"]] += 1
            if row["player_id"] in w_ids:
                bot_w[row["bot_name"]] += 1.0 / len(w_ids)
            rows_c.append((row.get("company_code") or "NONE", (1.0 / len(w_ids)) if row["player_id"] in w_ids else 0.0))
            for color, k in (row.get("purchases_by_color") or {}).items():
                buys[color] += k
            research_tracks += sum((row.get("research_spent_tracks") or {}).values())
            research_regain += row.get("research_spent_regain", 0)
            for trk, lv in row["final_track_levels"].items():
                if lv >= 4:
                    maxed[trk] += 1
            end_money.append(row["money"])
            cmp_money_seat.append(row.get("comparison_money_gained", 0) - row.get("comparison_money_paid", 0))
            if row.get("market_share") is not None:
                by_rank[rk + 1].append(row["market_share"])
            regain_steps += row.get("market_share_regained", 0)
            r2_uses += row.get("r2_uses", 0)
            company = row.get("company_code") or "NONE"
            comp_m[company] += 1
            if row["player_id"] in w_ids:
                comp_w[company] += 1.0 / len(w_ids)
        game_company_rows.append(rows_c)
    seats = games * n
    cmp_events = sum(c["events"] for c in comp.values())
    cmp_all_tied = sum(c["all_tied"] for c in comp.values())
    market_buys = sum(v for k, v in buys.items() if k in ("red", "blue", "green", "yellow"))
    comp_wr = {k: pct(comp_w[k], comp_m[k]) for k in comp_m}

    def _setup_flags(d: Dict[str, Counter]) -> Dict[str, Any]:
        out = {}
        for key, c in sorted(d.items()):
            tot = sum(c.values())
            out[key] = {e: round(pct(c[e], tot), 3) for e in THREE_WAY} | {"n": tot}
        worst = max(((k, e, v[e]) for k, v in out.items() for e in THREE_WAY), key=lambda x: x[2], default=None)
        return {"rates": out, "max_trigger": worst}

    return {
        "cell": cell, "players": n, "games": games,
        "end_reasons": {k: round(pct(v, games), 4) for k, v in sorted(reasons.items())},
        "three_way_split": {e: {"rate": round(pct(split[e], games), 4), "ci95": ci95(split[e], games)} for e in THREE_WAY},
        "other_end_reasons": {k: v for k, v in split.items() if k not in THREE_WAY},
        "total_wipeout_rate": {"rate": round(pct(reasons["total_wipeout"], games), 4),
                               "ci95": ci95(reasons["total_wipeout"], games)},
        "rounds": {"mean": round(statistics.mean(rounds), 3), "median": statistics.median(rounds),
                   "pct_le_5": round(pct(sum(1 for x in rounds if x <= 5), games), 4),
                   "stdev": round(statistics.pstdev(rounds), 3)},
        "by_setup": {k: _setup_flags(v) for k, v in by_setup.items()},
        "red": {
            "block_rate": round(pct(red["blocked_color"] + red["blocked_any"], red["incoming"]), 4),
            "incoming_per_seat": round(pct(red["incoming"], seats), 3),
            "blocked_any_share": round(pct(red["blocked_any"], red["blocked_color"] + red["blocked_any"]), 4),
            "share_lost_per_seat": round(pct(red["share_lost"], seats), 3),
            "overflow_per_seat": round(pct(red["overflow"], seats), 3),
        },
        "purchases": {
            "per_seat_by_color": {c: round(pct(buys[c], seats), 3) for c in ("red", "blue", "green", "yellow", "purple")},
            "red_share_of_market_buys": round(pct(buys["red"], market_buys), 4),
            "market_buys_per_seat": round(pct(market_buys, seats), 3),
        },
        "research": {
            "regain_share_of_spend": round(pct(research_regain, research_tracks + research_regain), 4),
            "maxed_track_share": {t: round(pct(v, sum(maxed.values())), 4) for t, v in sorted(maxed.items())},
            "regain_steps_per_seat": round(pct(regain_steps, seats), 3),
        },
        "r2_uses_per_seat": round(pct(r2_uses, seats), 3),
        "poach_moves_per_game": round(pct(poach_moves, games), 3),
        "comparisons": {
            v: {"events_per_game": round(pct(c["events"], games), 3), "paid_total": c["paid"],
                "forgiven_total": c["forgiven"], "gained_total": c["gained"],
                "pct_all_tied": round(pct(c["all_tied"], c["events"]), 4),
                "pct_top_tie": round(pct(c["top_tie"], c["events"]), 4),
                "pct_bottom_tie": round(pct(c["bottom_tie"], c["events"]), 4),
                "pct_any_tie": round(pct(c["any_tie"], c["events"]), 4),
                "pct_during_spillover": round(pct(c["spillover"], c["events"]), 4)}
            for v, c in sorted(comp.items())
        },
        "collapse": {
            "games_with_collapse": round(pct(collapse_games, games), 4),
            "pct_collapser_led_secrets": round(pct(collapse_kamikaze, collapse_games), 4),
            "rounds_to_collapse": quantiles(collapse_rounds),
        },
        "kamikaze": {
            "collapse_games": kami["games"],
            "strict_lead_rate": round(pct(kami["strict_lead"], kami["games"]), 4),
            "strict_lead_chance": round(pct(kami["strict_lead_chance"], kami["games"]), 4),
            "collapser_won_rate": round(pct(kami["collapser_won"], kami["games"]), 4),
            "collapser_won_chance": round(pct(kami["collapser_won_chance"], kami["games"]), 4),
        },
        "comparison_all_tied_rate": {"rate": round(pct(cmp_all_tied, cmp_events), 4), "ci95": ci95(cmp_all_tied, cmp_events),
                                     "events": cmp_events},
        "win_rate_by_bot": {b: {"rate": round(pct(bot_w[b], bot_m[b]), 4), "seats": bot_m[b]} for b in sorted(bot_m)},
        "multi_trigger_games": round(pct(triggers_multi, games), 4),
        "tiebreak_decided_by": {k: round(pct(v, games), 4) for k, v in tiebreak.most_common()},
        "market_share_curve_by_round": {r: quantiles(v) for r, v in sorted(curve.items())},
        "market_share_final_by_rank": {r: quantiles(v) for r, v in sorted(by_rank.items())},
        "economy": {"end_money": quantiles(end_money), "comparison_net_money_per_seat": round(pct(sum(cmp_money_seat), seats), 3)},
        "company_win_rates": {k: round(v, 4) for k, v in sorted(comp_wr.items())},
        "company_win_spread_pts": round((max(comp_wr.values()) - min(comp_wr.values())) * 100, 2) if comp_wr else 0.0,
        "company_win_spread_ci95_bootstrap": bootstrap_spread_ci(game_company_rows),
        "double_version_fill_rate": round(pct(dbl, games), 5),
        "seed_log": {k: v[:50] for k, v in seed_log.items()},
    }


def _job(args: Tuple[str, int, int, int]) -> Dict[str, Any]:
    return run_pod(*args)


def guardrails(c1: Dict[str, Any], c0: Optional[Dict[str, Any]], t4: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Spec §8 guardrail table for the acceptance cell (pass/fail flags are advisory; the game-designer judges)."""
    split = {e: c1["three_way_split"][e]["rate"] for e in THREE_WAY}
    worst = max((v["max_trigger"][2] for v in c1["by_setup"].values() if v["max_trigger"]), default=0.0)
    out: Dict[str, Any] = {
        "end_split_each_25_40": all(0.25 <= v <= 0.40 for v in split.values()),
        "no_setup_trigger_above_55": worst <= 0.55,
        "mean_rounds_8_4_to_9_0": 8.4 <= c1["rounds"]["mean"] <= 9.0,
        "comparison_any_tie_below_50": all(v["pct_any_tie"] < 0.5 for v in c1["comparisons"].values()),
        "comparison_all_tied_below_50": c1["comparison_all_tied_rate"]["rate"] < 0.5,
        "regain_share_20_40": 0.20 <= c1["research"]["regain_share_of_spend"] <= 0.40,
        "no_track_above_50_of_maxed": all(v <= 0.5 for v in c1["research"]["maxed_track_share"].values()),
        "red_purchase_share_le_35": c1["purchases"]["red_share_of_market_buys"] <= 0.35,
    }
    if c0 is not None:
        out["total_wipeout_le_c0"] = c1["total_wipeout_rate"]["rate"] <= c0["total_wipeout_rate"]["rate"]
        out["red_block_rate_delta"] = round(c1["red"]["block_rate"] - c0["red"]["block_rate"], 4)
        out["red_purchase_share_delta"] = round(
            c1["purchases"]["red_share_of_market_buys"] - c0["purchases"]["red_share_of_market_buys"], 4)
        out["company_spread_le_c0"] = c1["company_win_spread_pts"] <= c0["company_win_spread_pts"]
        out["rounds_delta"] = round(c1["rounds"]["mean"] - c0["rounds"]["mean"], 3)
        out["end_money_delta"] = round(c1["economy"]["end_money"]["mean"] - c0["economy"]["end_money"]["mean"], 3)
    if t4 is not None:
        out["purchases_le_1_2x_no_payout"] = (
            c1["purchases"]["market_buys_per_seat"] <= 1.2 * t4["purchases"]["market_buys_per_seat"])
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=None, help="games per pod for every cell (overrides spec counts)")
    ap.add_argument("--scale", type=float, default=1.0, help="multiplier on spec games per pod")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--pods", default="2,3,4")
    ap.add_argument("--cells", default=",".join(c for c in CELLS if c not in GRID_CELLS),
                    help="comma list of cell names; 'GRID' expands to the balance-iteration-1 re-sweep grid")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--out", default="sim_results/v360_market_share_sweep.json")
    a = ap.parse_args()
    pods = [int(x) for x in a.pods.split(",")]
    cells: List[str] = []
    for c in (c.strip() for c in a.cells.split(",")):
        if c == "GRID":
            cells.extend(GRID_CELLS)
        elif c:
            cells.append(c)
    unknown = [c for c in cells if c not in CELLS]
    if unknown:
        raise SystemExit(f"unknown cells {unknown}; known: {list(CELLS)}")
    jobs = []
    for n in pods:
        for c in cells:
            g = a.games if a.games is not None else max(1, int(CELLS[c][3] * a.scale))
            jobs.append((c, n, g, a.seed))
    if a.workers > 1:
        from multiprocessing import Pool

        with Pool(a.workers) as pool:
            results = pool.map(_job, jobs)
    else:
        results = [_job(j) for j in jobs]
    by = {(r["cell"], r["players"]): r for r in results}
    for r in results:
        s = r["three_way_split"]
        print(f"{r['players']}P {r['cell']:12s} n={r['games']:5d} rounds={r['rounds']['mean']:.2f} "
              f"PZ={s['patient_zero']['rate']:.3f} SING={s['singularity']['rate']:.3f} "
              f"MC={s['market_collapse']['rate']:.3f} TW={r['total_wipeout_rate']['rate']:.3f} "
              f"redBlock={r['red']['block_rate']:.3f} redBuy={r['purchases']['red_share_of_market_buys']:.3f} "
              f"regain={r['research']['regain_share_of_spend']:.3f} spread={r['company_win_spread_pts']:.1f} "
              f"allTied={r['comparison_all_tied_rate']['rate']:.3f} "
              f"VGwin={r['win_rate_by_bot'].get('VentureGreedBot', {}).get('rate', 0):.3f}", flush=True)
    gr = {}
    for n in pods:
        if ("V036", n) in by:
            gr[str(n)] = guardrails(by[("V036", n)], by.get(("V035", n)), by.get(("NO_PAYOUT", n)))
    for n, g in gr.items():
        print(f"{n}P guardrails: {g}")
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump({"seed": a.seed, "pods": pods, "cells": cells, "results": results, "guardrails_v036": gr},
                  fh, indent=1, default=str)
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
