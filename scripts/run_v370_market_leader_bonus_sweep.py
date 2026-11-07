"""Rogue Agent v0.37.0 Market Leader Bonus sweep (spec docs/specs/v370_market_leader_bonus_spec.md §8).

Cells (same seeds in every cell, paired): V036 baseline, V037 acceptance, V037-S036 starting-Secrets ablation,
V037-NAIVE (bonus scores, bots ignore it), V037-ONE-AWARE (only seat ``match_idx % n`` values the bonus).
Telemetry comes only from engine fields (EndGameResult / ranking rows / RoundTelemetry), no monkeypatched hooks.
Match setup reuses scripts/run_v360_market_share_sweep (BASE_KW, BOT_CLASSES, seeded bot rotation + shuffle,
get_random_setup(rng, "STANDARD"), get_random_companies, get_random_white_hats); the bot modifier here takes
``(bots, match_idx)``.

Usage:
  PYTHONDONTWRITEBYTECODE=1 python3 scripts/run_v370_market_leader_bonus_sweep.py --workers 8          # main run
  PYTHONDONTWRITEBYTECODE=1 python3 scripts/run_v370_market_leader_bonus_sweep.py --seed 7000 \\
      --cells V036,V037,V037-ONE-AWARE --workers 8                                                   # fresh seeds
  options: --games N (overrides every cell's games per pod), --scale F (multiplies spec counts),
           --pods 2,3,4, --cells A,B, --workers K, --out PATH
           (default out: sim_results/v370_market_leader_bonus_sweep.json, or ..._seed<SEED>.json when --seed != 42)
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
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from run_v360_market_share_sweep import (  # noqa: E402
    BASE_KW,
    BOT_CLASSES,
    bootstrap_spread_ci,
    ci95,
    quantiles,
    three_way,
)

from sim.bots.market_share_policy import policy_for  # noqa: E402
from sim.config import GameConfig  # noqa: E402
from sim.engine.core import GameEngine  # noqa: E402
from sim.entities import get_random_companies, get_random_setup, get_random_white_hats  # noqa: E402

DEFAULT_SEED = 42
THREE_WAY = ("patient_zero", "singularity", "market_collapse")
V036_SECRETS = {2: 7, 3: 7, 4: 8}
MIN_SETUP_GROUP = 200  # setup groups smaller than this are reported but not judged (staff-engineer review)


def _set_aware(bots: List[Any], aware: Callable[[Any], bool]) -> None:
    for b in bots:
        b.market_share_policy = dataclasses.replace(policy_for(b), leader_bonus_aware=bool(aware(b)))


def _all_naive(bots: List[Any], match_idx: int) -> None:
    _set_aware(bots, lambda b: False)


def _one_aware(bots: List[Any], match_idx: int) -> None:
    seat = match_idx % len(bots)
    _set_aware(bots, lambda b: b.player_id == seat)


def aware_seat(cell: str, n: int, match_idx: int) -> Optional[int]:
    return match_idx % n if cell == "V037-ONE-AWARE" else None


# name -> (factory, config overrides, bot modifier(bots, match_idx), spec games per pod)
CELLS: Dict[str, Tuple[Callable[..., GameConfig], Dict[str, Any], Optional[Callable[[List[Any], int], None]], int]] = {
    "V036": (GameConfig.v036, {}, None, 3000),
    "V037": (GameConfig.v037, {}, None, 3000),
    "V037-S036": (GameConfig.v037, dict(starting_secrets_by_player_count=dict(V036_SECRETS)), None, 3000),
    "V037-NAIVE": (GameConfig.v037, {}, _all_naive, 2000),
    "V037-ONE-AWARE": (GameConfig.v037, {}, _one_aware, 3000),
}


def build_engine(cell: str, num_players: int, match_idx: int, match_seed: int) -> GameEngine:
    factory, overrides, bot_mod, _ = CELLS[cell]
    rng = random.Random(match_seed)
    bots = [BOT_CLASSES[(match_idx * num_players + i) % len(BOT_CLASSES)](i) for i in range(num_players)]
    rng.shuffle(bots)
    for i, b in enumerate(bots):
        b.player_id = i
    if bot_mod is not None:
        bot_mod(bots, match_idx)
    variants, version_deck = get_random_setup(rng, profile="STANDARD")
    companies = get_random_companies(num_players, rng)
    white_hats = get_random_white_hats(num_players, rng)
    cfg = factory(num_players=num_players, **BASE_KW, **overrides)
    return GameEngine(config=cfg, bots=bots, seed=match_seed, variant_cards=variants, version_deck=version_deck,
                      companies=companies, white_hats=white_hats)


def pct(n: float, d: float) -> float:
    return n / d if d else 0.0


def mean_ci95(xs: List[float]) -> Dict[str, Any]:
    """Mean with a normal-approximation 95% interval (fractional win credit)."""
    if not xs:
        return {"mean": 0.0, "ci95": [0.0, 0.0], "n": 0}
    m = statistics.mean(xs)
    h = 1.96 * statistics.pstdev(xs) / math.sqrt(len(xs)) if len(xs) > 1 else 0.0
    return {"mean": round(m, 4), "ci95": [round(m - h, 4), round(m + h, 4)], "n": len(xs)}


def rate(k: float, n: int) -> Dict[str, Any]:
    return {"rate": round(pct(k, n), 4), "ci95": ci95(k, n), "n": n}


# ---------------------------------------------------------------------------
# Pod runner
# ---------------------------------------------------------------------------
def run_pod(cell: str, n: int, games: int, base_seed: int) -> Dict[str, Any]:
    reasons: Counter = Counter()
    split: Counter = Counter()
    rounds: List[int] = []
    collapse_le_5 = 0
    by_setup: Dict[str, Dict[str, Counter]] = {"v3_card": defaultdict(Counter), "company_seat": defaultdict(Counter),
                                                "white_hat_seat": defaultdict(Counter)}
    red = Counter()
    research_tracks = research_regain = 0
    awarded = changed = tied_paid = 0
    multi_surv_games = 0
    hi_seats = lo_seats = 0
    hi_credit = lo_credit = 0.0
    surv_before: List[int] = []
    surv_bonus: List[int] = []
    place_bonus: Dict[int, List[int]] = defaultdict(list)
    aware_credit: List[float] = []
    any_by_color: Counter = Counter()
    contested = Counter()
    blue_dice_m: Counter = Counter()
    blue_dice_w: Counter = Counter()
    comp_m: Counter = Counter()
    comp_w: Counter = Counter()
    bot_m: Counter = Counter()
    bot_w: Counter = Counter()
    tiebreak: Counter = Counter()
    game_company_rows: List[List[Tuple[str, float]]] = []
    seed_log: Dict[str, List[int]] = defaultdict(list)
    for idx in range(games):
        seed = base_seed + n * 100_000 + idx
        res = build_engine(cell, n, idx, seed).run_game()
        r = res.end_reason.value
        reasons[r] += 1
        tw = three_way(r)
        split[tw] += 1
        rounds.append(res.total_rounds)
        if r == "market_collapse" and res.total_rounds <= 5:
            collapse_le_5 += 1
            seed_log["collapse_le_5"].append(seed)
        if res.market_leader_bonus_changed_winner:
            seed_log["bonus_changed_winner"].append(seed)
        setup = res.setup
        by_setup["v3_card"][setup["version_cards"][-1]][tw] += 1
        for seat, c in enumerate(setup["companies"]):
            by_setup["company_seat"][f"{c}@{seat}"][tw] += 1
        for seat, w in enumerate(setup["white_hats"]):
            by_setup["white_hat_seat"][f"{w}@{seat}"][tw] += 1
        tiebreak[res.tiebreak_decided_by] += 1
        for t in res.telemetry_history:  # same Red block-rate definition as the v0.36 sweep
            if t.buffer_overflow or 4 not in t.phases_executed:
                continue
            snap = {s["player_id"]: s for s in t.phase_snapshots.get(3, [])}
            for pid, rb in t.red_by_player.items():
                if snap.get(pid, {}).get("is_patient_zero", False):
                    continue
                for k, v in rb.items():
                    red[k] += v
        awarded += int(res.market_leader_bonus_awarded)
        changed += int(res.market_leader_bonus_changed_winner)
        tied_paid += int(res.market_leader_bonus_tied_paid_place)

        w_ids = list(res.winner_ids or ([res.winner_id] if res.winner_id is not None else []))
        credit = {row["player_id"]: (1.0 / len(w_ids) if row["player_id"] in w_ids else 0.0) for row in res.rankings}
        survivors = [row for row in res.rankings if not row["is_patient_zero"]]
        if len(survivors) >= 2 and not res.is_total_wipeout:
            places = [row["market_share_place"] for row in survivors if row["market_share_place"] is not None]
            if places:
                multi_surv_games += 1
                worst = max(places)
                for row in survivors:
                    if row["market_share_place"] == 1:
                        hi_seats += 1
                        hi_credit += credit[row["player_id"]]
                    if row["market_share_place"] == worst:
                        lo_seats += 1
                        lo_credit += credit[row["player_id"]]
        for row in survivors:
            surv_before.append(row["secrets_before_bonus"])
            surv_bonus.append(row["market_leader_bonus"])
            if row["market_share_place"] is not None:
                place_bonus[row["market_share_place"]].append(row["market_leader_bonus"])
        seat = aware_seat(cell, n, idx)
        if seat is not None:
            aware_credit.append(credit.get(seat, 0.0))
        rows_c: List[Tuple[str, float]] = []
        for row in res.rankings:
            pid = row["player_id"]
            for c, v in (row.get("any_shield_allocated_by_color") or {}).items():
                any_by_color[c] += v
            contested["rounds"] += row.get("contested_defense_rounds", 0)
            contested["blue_open"] += row.get("contested_blue_left_open", 0)
            contested["red_chosen"] += row.get("contested_red_chosen", 0)
            nb = (row.get("dice_owned_final_by_color") or {}).get("blue", 0)
            bucket = "2+" if nb >= 2 else str(nb)
            blue_dice_m[bucket] += 1
            blue_dice_w[bucket] += credit[pid]
            research_tracks += sum((row.get("research_spent_tracks") or {}).values())
            research_regain += row.get("research_spent_regain", 0)
            company = row.get("company_code") or "NONE"
            comp_m[company] += 1
            comp_w[company] += credit[pid]
            bot_m[row["bot_name"]] += 1
            bot_w[row["bot_name"]] += credit[pid]
            rows_c.append((company, credit[pid]))
        game_company_rows.append(rows_c)

    any_total = sum(any_by_color.values())
    comp_wr = {k: pct(comp_w[k], comp_m[k]) for k in comp_m}

    def _setup_flags(d: Dict[str, Counter]) -> Dict[str, Any]:
        out = {}
        for key, c in sorted(d.items()):
            tot = sum(c.values())
            out[key] = {e: round(pct(c[e], tot), 3) for e in THREE_WAY} | {"n": tot}
        worst = max(((k, e, v[e], v["n"]) for k, v in out.items() for e in THREE_WAY),
                    key=lambda x: x[2], default=None)
        big = [(k, e, v[e], v["n"]) for k, v in out.items() for e in THREE_WAY if v["n"] >= MIN_SETUP_GROUP]
        worst_big = max(big, key=lambda x: x[2], default=None)
        # (group, end reason, rate, n); the guardrail reads max_trigger_n_ge_200 (smaller groups are too noisy)
        return {"rates": out, "max_trigger": worst, "max_trigger_n_ge_200": worst_big}

    edge = None
    if aware_credit:
        m = mean_ci95(aware_credit)
        edge = {"aware_win_credit": m, "fair_share": round(1.0 / n, 4),
                "edge_pts": round((m["mean"] - 1.0 / n) * 100, 2),
                "edge_ci95_pts": [round((x - 1.0 / n) * 100, 2) for x in m["ci95"]]}
    return {
        "cell": cell, "players": n, "games": games,
        "end_reasons": {k: round(pct(v, games), 4) for k, v in sorted(reasons.items())},
        "three_way_split": {e: rate(split[e], games) for e in THREE_WAY},
        "total_wipeout_rate": rate(reasons["total_wipeout"], games),
        "market_collapse_le_5_rounds": collapse_le_5,
        "rounds": {"mean": round(statistics.mean(rounds), 3), "median": statistics.median(rounds),
                   "stdev": round(statistics.pstdev(rounds), 3)},
        "by_setup": {k: _setup_flags(v) for k, v in by_setup.items()},
        "red_block_rate": round(pct(red["blocked_color"] + red["blocked_any"], red["incoming"]), 4),
        "regain_share_of_spend": round(pct(research_regain, research_tracks + research_regain), 4),
        "market_leader_bonus": {
            "awarded_games": awarded,
            "winner_changed_over_awarded": rate(changed, awarded),
            "winner_changed_over_all": rate(changed, games),
            "paid_place_tied_over_awarded": rate(tied_paid, awarded),
            "mean_survivor_secrets_before_bonus": round(statistics.mean(surv_before), 3) if surv_before else 0.0,
            "mean_survivor_bonus": round(statistics.mean(surv_bonus), 3) if surv_bonus else 0.0,
            "mean_bonus_by_place": {p: round(statistics.mean(v), 3) for p, v in sorted(place_bonus.items())},
        },
        # per-seat win credit of survivors at the best / worst place in games with >= 2 survivors (as the §38 probe)
        "games_with_2plus_survivors": multi_surv_games,
        "highest_share_survivor_wins": rate(hi_credit, hi_seats),
        "lowest_share_survivor_wins": rate(lo_credit, lo_seats),
        "bonus_aware_edge": edge,
        "any_shields": {"blue": round(pct(any_by_color["blue"], any_total), 4),
                        "red": round(pct(any_by_color["red"], any_total), 4),
                        "green": round(pct(any_by_color["green"], any_total), 4), "total": any_total},
        "contested": {"rounds": contested["rounds"],
                      "blue_left_open": round(pct(contested["blue_open"], contested["rounds"]), 4),
                      "red_chosen": round(pct(contested["red_chosen"], contested["rounds"]), 4)},
        "win_rate_by_blue_dice": {k: {"rate": round(pct(blue_dice_w[k], blue_dice_m[k]), 4), "seats": blue_dice_m[k]}
                                  for k in ("0", "1", "2+")},
        "win_rate_by_bot": {b: {"rate": round(pct(bot_w[b], bot_m[b]), 4), "seats": bot_m[b]} for b in sorted(bot_m)},
        "tiebreak_decided_by": {k: round(pct(v, games), 4) for k, v in tiebreak.most_common()},
        "company_win_rates": {k: round(v, 4) for k, v in sorted(comp_wr.items())},
        "company_win_spread_pts": round((max(comp_wr.values()) - min(comp_wr.values())) * 100, 2) if comp_wr else 0.0,
        "company_win_spread_ci95_bootstrap": bootstrap_spread_ci(game_company_rows),
        "seed_log": {k: v[:50] for k, v in seed_log.items()},
    }


def _job(args: Tuple[str, int, int, int]) -> Dict[str, Any]:
    return run_pod(*args)


# ---------------------------------------------------------------------------
# Deltas and guardrails (advisory; the game-designer judges watch cases)
# ---------------------------------------------------------------------------
def _headline(r: Dict[str, Any]) -> Dict[str, float]:
    s = r["three_way_split"]
    return {
        "patient_zero": s["patient_zero"]["rate"], "singularity": s["singularity"]["rate"],
        "market_collapse": s["market_collapse"]["rate"], "total_wipeout": r["total_wipeout_rate"]["rate"],
        "rounds": r["rounds"]["mean"], "red_block_rate": r["red_block_rate"],
        "regain_share_of_spend": r["regain_share_of_spend"], "any_shields_blue": r["any_shields"]["blue"],
        "contested_blue_left_open": r["contested"]["blue_left_open"],
        "lowest_share_survivor_wins": r["lowest_share_survivor_wins"]["rate"],
        "company_win_spread_pts": r["company_win_spread_pts"],
    }


def delta(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, float]:
    ha, hb = _headline(a), _headline(b)
    return {k: round(ha[k] - hb[k], 4) for k in ha}


def _band(v: float, pass_lo: float, pass_hi: float, watch_lo: float, watch_hi: float) -> str:
    if pass_lo <= v <= pass_hi:
        return "pass"
    if watch_lo <= v <= watch_hi:
        return "watch"
    return "fail"


def guardrails(c: Dict[str, Any], base: Optional[Dict[str, Any]], one: Optional[Dict[str, Any]],
               naive: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    n = c["players"]
    s = {e: c["three_way_split"][e]["rate"] for e in THREE_WAY}
    out: Dict[str, Any] = {}
    for e, v in s.items():
        if n == 2 and e == "singularity":
            out["end_split_singularity_2p"] = "pass" if v <= 0.43 else ("watch" if v <= 0.46 else "fail")
        else:
            out[f"end_split_{e}"] = _band(v, 0.25, 0.40, 0.20, 0.46)
    tops = [v["max_trigger_n_ge_200"] for v in c["by_setup"].values() if v["max_trigger_n_ge_200"]]
    if tops:
        worst = max(t[2] for t in tops)
        out["highest_setup_trigger"] = "pass" if worst <= 0.43 else ("watch" if worst <= 0.55 else "fail")
    else:
        out["highest_setup_trigger"] = f"n/a (no setup group with n >= {MIN_SETUP_GROUP})"
    out["rounds_mean"] = _band(c["rounds"]["mean"], 8.4, 9.2, 8.2, 9.4)
    out["no_collapse_le_5_rounds"] = "pass" if c["market_collapse_le_5_rounds"] == 0 else "fail"
    rs = c["regain_share_of_spend"]
    out["regain_share_of_spend"] = ("watch (below band)" if rs < 0.20 else
                                    "pass" if rs <= 0.40 else "watch" if rs <= 0.50 else "fail")
    wc = c["market_leader_bonus"]["winner_changed_over_awarded"]["rate"]
    out["winner_changed_by_bonus"] = "pass" if 0.10 <= wc <= 0.30 else (
        "watch" if 0.30 < wc <= 0.35 or 0.05 <= wc < 0.10 else "fail")
    ab = c["any_shields"]["blue"]
    out["any_shields_on_blue"] = "pass" if ab >= 0.55 else ("watch" if ab >= 0.50 else "fail")
    bo = c["contested"]["blue_left_open"]
    out["contested_blue_left_open"] = "pass" if bo <= 0.25 else ("watch" if bo <= 0.30 else "fail")
    lo = c["lowest_share_survivor_wins"]["rate"]
    out["lowest_share_survivor_wins"] = lo if not (n == 2 and lo < 0.25) else f"watch ({lo})"
    if base is not None:
        tw, tw0 = c["total_wipeout_rate"]["rate"], base["total_wipeout_rate"]["rate"]
        d = tw - tw0
        out["total_wipeout"] = "fail" if d > 0.02 or (n == 2 and tw > 0.16) else ("watch" if d > 0.01 else "pass")
        rb = c["red_block_rate"] - base["red_block_rate"]
        out["red_block_rate"] = "pass" if rb >= 0 else ("watch" if rb >= -0.01 else "fail")
        sp = c["company_win_spread_pts"] - base["company_win_spread_pts"]
        out["company_spread_le_v036_plus_3"] = "pass" if sp <= 3.0 else "report"
    if one is not None and one.get("bonus_aware_edge"):
        e = one["bonus_aware_edge"]["edge_pts"]
        out["bonus_aware_edge_one_aware"] = "pass" if e <= 7.0 else ("watch" if e <= 10.0 else "fail")
    if naive is not None:
        pz = naive["three_way_split"]["patient_zero"]["rate"]
        out["naive_patient_zero"] = pz if pz >= 0.20 else f"watch ({pz})"
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=None, help="games per pod for every cell (overrides spec counts)")
    ap.add_argument("--scale", type=float, default=1.0, help="multiplier on spec games per pod")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--pods", default="2,3,4")
    ap.add_argument("--cells", default=",".join(CELLS), help="comma list of cell names")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or ("sim_results/v370_market_leader_bonus_sweep.json" if a.seed == DEFAULT_SEED
                    else f"sim_results/v370_market_leader_bonus_sweep_seed{a.seed}.json")
    pods = [int(x) for x in a.pods.split(",")]
    cells = [c.strip() for c in a.cells.split(",") if c.strip()]
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
        mlb = r["market_leader_bonus"]
        edge = r["bonus_aware_edge"]["edge_pts"] if r["bonus_aware_edge"] else float("nan")
        print(f"{r['players']}P {r['cell']:15s} n={r['games']:5d} rounds={r['rounds']['mean']:.2f} "
              f"PZ={s['patient_zero']['rate']:.3f} SING={s['singularity']['rate']:.3f} "
              f"MC={s['market_collapse']['rate']:.3f} TW={r['total_wipeout_rate']['rate']:.3f} "
              f"chg={mlb['winner_changed_over_awarded']['rate']:.3f} tied={mlb['paid_place_tied_over_awarded']['rate']:.3f} "
              f"anyBlue={r['any_shields']['blue']:.3f} blueOpen={r['contested']['blue_left_open']:.3f} "
              f"loMSwin={r['lowest_share_survivor_wins']['rate']:.3f} redBlock={r['red_block_rate']:.3f} "
              f"regain={r['regain_share_of_spend']:.3f} edge={edge:.1f}", flush=True)
    deltas: Dict[str, Dict[str, Any]] = {}
    gr: Dict[str, Any] = {}
    for n in pods:
        base = by.get(("V036", n))
        for c in ("V037", "V037-S036"):
            if base is not None and (c, n) in by:
                deltas.setdefault(str(n), {})[f"{c} - V036"] = delta(by[(c, n)], base)
        if ("V037", n) in by:
            gr[str(n)] = guardrails(by[("V037", n)], base, by.get(("V037-ONE-AWARE", n)), by.get(("V037-NAIVE", n)))
    for n, g in gr.items():
        print(f"{n}P guardrails (V037): {g}")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"seed": a.seed, "pods": pods, "cells": cells, "results": results, "deltas": deltas,
                   "guardrails_v037": gr}, fh, indent=1, default=str)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
