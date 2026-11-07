"""Rogue Agent v0.34.0 telemetry sweep: Six-Phase Round Sequence vs the v0.33 legacy baseline.

Phase 42 (Step 7 of docs/explorations/2026_11_six_phase_round_sequence_plan.md).

Runs N matches per pod (2P / 3P / 4P) on explicit base seeds under the v0.34 default
(``GameConfig.legacy_v035()`` = SIX_PHASE, flat 8 Secrets) and the SAME seeds under ``GameConfig.legacy_v033``
(three-phase round, 4P = 12 Secrets). Match setup mirrors ``scripts/run_v330_telemetry_sweep.py``:
5-bot rotation, ``get_random_setup`` STANDARD, random Client Companies and White Hat Operatives,
starting_money=6, 3 Gray + 1 Purple, 1 Purple reserve, enable_corporate_asymmetry=True.

Telemetry that the engine does not expose is collected with observer wrappers installed by THIS
script only (no engine changes). Wrappers are pure pass-throughs: they call the original function
with the original arguments and only read state before/after.

Usage:
  PYTHONDONTWRITEBYTECODE=1 python3 scripts/run_v340_telemetry_sweep.py --games 3000 --seed 42
  PYTHONDONTWRITEBYTECODE=1 python3 scripts/run_v340_telemetry_sweep.py --replay 400017 --players 4 --seq six
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
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sim.bots import (  # noqa: E402
    AccelerationistBot,
    AdaptiveBalancedBot,
    RecklessSaboteurBot,
    SecOpsTurtleBot,
    VentureGreedBot,
)
from sim.config import DieColor, EndGameReason, GameConfig  # noqa: E402
from sim.engine.core import GameEngine  # noqa: E402
import sim.engine.legacy_v033 as legacy_mod  # noqa: E402
import sim.engine.phase2_compiler as p2c  # noqa: E402
import sim.engine.phase3_income as p3i  # noqa: E402
import sim.engine.phase4_attack_resolution as p4  # noqa: E402
import sim.engine.phase5_pipeline_shift as p5  # noqa: E402
from sim.entities import (  # noqa: E402
    COMPANIES,
    WHITE_HATS,
    get_random_companies,
    get_random_setup,
    get_random_white_hats,
)

BOT_CLASSES = [AdaptiveBalancedBot, SecOpsTurtleBot, VentureGreedBot, AccelerationistBot, RecklessSaboteurBot]
SEQUENCES = ("SIX_PHASE", "LEGACY_V033")
DAMAGE_STARS = ("R2", "R3", "B1")

# ---------------------------------------------------------------------------
# Observer wrappers (script-local; pass-through only)
# ---------------------------------------------------------------------------
ORIG_COLLECT = p3i.collect_player_production_income
ORIG_BURN = p3i.resolve_spook_burn_notice
ORIG_DEFENSE = p4.resolve_player_defense_and_wear
ORIG_DEMOTE = p2c.demote_player_dice_step2a
ORIG_GRAD = p5.graduate_scanned

T: Dict[str, Any] = {}  # pod-level counters (reset per pod)
G: Dict[str, Any] = {}  # game-level scratch (reset per game)


def reset_pod_counters() -> None:
    T.clear()
    T.update(
        income_events=0, income_cash=0, income_research=0, zero_income=0,
        star_events_ge2=0, star_events_ge2_spook=0, spook_income_events=0,
        contractor_payout_events=0, contractor_payout_cash=0,
        ransom_leaks=0, defense_events=0, unblocked_green=0,
        dmg_star_forfeit=0, dmg_star_forfeit_by_code=Counter(), dmg_star_paid_inprod=0,
        burn_notice_uses=0, burn_notice_on_inprod=0,
        grad_events=0, grad_capped=0, held_scanned_sum=0, held_scanned_nonzero=0,
        whammy_rounds=0, whammy_income=[],
        corruption_glitch_rounds=0, green_rounds=0,
        grad_by_company=defaultdict(lambda: [0, 0, 0]),  # [events, capped, held_sum]
    )


def reset_game_scratch() -> None:
    G.clear()
    G.update(income={}, glitch=set(), green=set())


def _key(engine: GameEngine, player) -> tuple:
    return (player.player_id, engine.state.current_round)


def w_collect(engine, player, plan=None):
    stars = len(p3i.purple_star_dice_in_production(player))
    m0, r0 = player.money, player.patches
    rec = ORIG_COLLECT(engine, player, plan)
    dm, dr = player.money - m0, player.patches - r0
    T["income_events"] += 1
    T["income_cash"] += dm
    T["income_research"] += dr
    if dm + dr == 0:
        T["zero_income"] += 1
    is_spook = p3i._is_operative(player, p3i.WhiteHatCode.SPOOK, p3i.ArchetypeCode.SPOOK)
    if is_spook:
        T["spook_income_events"] += 1
    if stars >= 2:
        T["star_events_ge2"] += 1
        if is_spook:
            T["star_events_ge2_spook"] += 1
    for row in getattr(rec, "details", None) or []:
        if row.get("color") == DieColor.WHITE.value and row.get("money", 0) > 0:
            T["contractor_payout_events"] += 1
            T["contractor_payout_cash"] += row["money"]
    G["income"][_key(engine, player)] = dm + dr
    return rec


def w_burn(engine, player, die_id):
    in_prod = any(d.die_id == die_id for d in player.in_production_dice)
    ok = ORIG_BURN(engine, player, die_id)
    if ok:
        T["burn_notice_uses"] += 1
        if in_prod:
            T["burn_notice_on_inprod"] += 1
    return ok


def w_defense(engine, player, rolled_dice, commitments, attack_strengths, exited_cubes, active_directive,
              *args, **kwargs):
    in_prod = {id(d) for d in player.in_production_dice}
    off_prod_stars = []
    on_prod_stars = 0
    for d in rolled_dice:
        f = d.effective_face or d.current_face
        if f is not None and f.is_star and f.star_code in DAMAGE_STARS:
            if id(d) in in_prod:
                on_prod_stars += 1
            else:
                off_prod_stars.append(f.star_code)
    ORIG_DEFENSE(engine, player, rolled_dice, commitments, attack_strengths, exited_cubes, active_directive,
                 *args, **kwargs)
    br = getattr(player, "last_defense_breakdown", None) or {}
    ub = br.get("unblocked", {})
    T["defense_events"] += 1
    if br.get("flat_ransom_leak"):
        T["ransom_leaks"] += 1
    g = ub.get("green", 0)
    T["unblocked_green"] += g
    if g > 0:
        G["green"].add(_key(engine, player))
    for code in off_prod_stars:
        met = (
            (code == "R2" and ub.get("red", 0) == 0)
            or (code == "R3" and exited_cubes.get(p4.CubeColor.RED, 0) >= 3)
            or (code == "B1" and exited_cubes.get(p4.CubeColor.BLUE, 0) >= 1 and ub.get("blue", 0) == 0)
        )
        if met:
            T["dmg_star_forfeit"] += 1
            T["dmg_star_forfeit_by_code"][code] += 1
    T["dmg_star_paid_inprod"] += on_prod_stars


def w_demote(player, rolled_dice, commitments, count, threat_strengths=None, engine=None):
    before = len(player.in_production_dice)
    ORIG_DEMOTE(player, rolled_dice, commitments, count, threat_strengths, engine=engine)
    if engine is not None and len(player.in_production_dice) < before:
        G["glitch"].add(_key(engine, player))


def w_grad(engine, player, chosen_die_ids=None, *, use_bot_choice=True):
    s0 = len(player.scanned_dice)
    out = ORIG_GRAD(engine, player, chosen_die_ids, use_bot_choice=use_bot_choice)
    T["grad_events"] += 1
    if s0 > player.release_bandwidth:
        T["grad_capped"] += 1
    held = len(player.scanned_dice)
    T["held_scanned_sum"] += held
    gc = T["grad_by_company"][player.company.code.value if player.company else "NONE"]
    gc[0] += 1
    gc[1] += s0 > player.release_bandwidth
    gc[2] += held
    if held > 0:
        T["held_scanned_nonzero"] += 1
    return out


def install_wrappers() -> None:
    p3i.collect_player_production_income = w_collect
    p3i.resolve_spook_burn_notice = w_burn
    p4.resolve_player_defense_and_wear = w_defense
    legacy_mod.resolve_player_defense_and_wear = w_defense
    p2c.demote_player_dice_step2a = w_demote
    p5.graduate_scanned = w_grad


def remove_wrappers() -> None:
    p3i.collect_player_production_income = ORIG_COLLECT
    p3i.resolve_spook_burn_notice = ORIG_BURN
    p4.resolve_player_defense_and_wear = ORIG_DEFENSE
    legacy_mod.resolve_player_defense_and_wear = ORIG_DEFENSE
    p2c.demote_player_dice_step2a = ORIG_DEMOTE
    p5.graduate_scanned = ORIG_GRAD


# ---------------------------------------------------------------------------
# Match construction (mirrors run_v330_telemetry_sweep.py)
# ---------------------------------------------------------------------------
def build_engine(seq: str, num_players: int, match_idx: int, match_seed: int) -> GameEngine:
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
    cfg = GameConfig.legacy_v035(**kw) if seq == "SIX_PHASE" else GameConfig.legacy_v033(**kw)
    return GameEngine(config=cfg, bots=bots, seed=match_seed, variant_cards=variants, version_deck=version_deck,
                      companies=companies, white_hats=white_hats)


def tiebreak_level(res, six_phase: bool) -> str:
    keys = (
        ["money", "ready_colored_dice_count", "patches", "-unpatched_dice_count"]
        if six_phase
        else ["net_score", "secrets", "money", "ready_colored_dice_count", "patches", "-unpatched_dice_count"]
    )
    r = res.rankings
    if len(r) < 2:
        return "n/a"
    for k in keys:
        a = -r[0]["unpatched_dice_count"] if k.startswith("-") else r[0][k]
        b = -r[1]["unpatched_dice_count"] if k.startswith("-") else r[1][k]
        if a != b:
            return k
    return "shared"


def pct(n: float, d: float) -> float:
    return n / d if d else 0.0


# ---------------------------------------------------------------------------
# Pod runner
# ---------------------------------------------------------------------------
def run_pod(seq: str, num_players: int, games: int, base_seed: int) -> Dict[str, Any]:
    reset_pod_counters()
    six = seq == "SIX_PHASE"
    rounds: List[int] = []
    reasons: Counter = Counter()
    survivors = 0
    final_secrets: List[int] = []
    survivor_secrets: List[int] = []
    colored_owned: List[int] = []
    contractor_hires: List[int] = []
    release_levels: Counter = Counter()
    final_trigger_phase: Counter = Counter()
    end_phase: Counter = Counter()
    wipeout_tiebreak: Counter = Counter()
    tel_held: List[int] = []
    tel_star_ge2 = 0
    tel_star_rounds = 0
    tel_income_total = 0
    tel_income_n = 0
    groups = {k: {"m": Counter(), "w": Counter(), "s": Counter(), "sec": defaultdict(list)} for k in ("bot", "company", "op")}
    outliers: Dict[str, List[Dict[str, Any]]] = {"rounds_le_3": [], "rounds_ge_14": [], "4p_under_6": [], "round_limit": []}

    for idx in range(games):
        seed = base_seed + num_players * 100_000 + idx
        reset_game_scratch()
        eng = build_engine(seq, num_players, idx, seed)
        res = eng.run_game()
        st = eng.state
        n_r = res.total_rounds
        rounds.append(n_r)
        reasons[res.end_reason.value] += 1
        rec = {"seed": seed, "match_idx": idx, "rounds": n_r, "end_reason": res.end_reason.value}
        if n_r <= 3:
            outliers["rounds_le_3"].append(rec)
        if n_r >= 14:
            outliers["rounds_ge_14"].append(rec)
        if num_players == 4 and n_r < 6:
            outliers["4p_under_6"].append(rec)
        if res.end_reason == EndGameReason.ROUND_LIMIT:
            outliers["round_limit"].append(rec)
        if getattr(st, "final_round_trigger_phase", None) is not None:
            final_trigger_phase[str(st.final_round_trigger_phase)] += 1
        if eng.telemetry_history:
            end_phase[str(eng.telemetry_history[-1].end_phase)] += 1
        if res.is_total_wipeout:
            wipeout_tiebreak[tiebreak_level(res, six)] += 1

        # Six-phase native telemetry cross-checks
        for tel in eng.telemetry_history:
            for v in (tel.scanned_held_by_player or {}).values():
                tel_held.append(v)
            for v in (tel.purple_star_triggers_per_round or {}).values():
                tel_star_rounds += 1
                if v >= 2:
                    tel_star_ge2 += 1
            for v in (tel.income_by_player or {}).values():
                tel_income_total += v.get("money", 0) + v.get("research", 0)
                tel_income_n += 1

        # Double whammy: corruption glitch + unblocked Green in the same player-round
        T["corruption_glitch_rounds"] += len(G["glitch"])
        T["green_rounds"] += len(G["green"])
        for k in G["glitch"] & G["green"]:
            T["whammy_rounds"] += 1
            if k in G["income"]:
                T["whammy_income"].append(G["income"][k])

        for p in st.players:
            surv = not p.is_patient_zero
            # Shared victory counts 1/k per tied winner (no seat bias from winner_id tie-breaking).
            w_ids = list(getattr(res, "winner_ids", None) or ([res.winner_id] if res.winner_id is not None else []))
            win = (1.0 / len(w_ids)) if (p.player_id in w_ids and (surv or res.is_total_wipeout)) else 0.0
            survivors += surv
            final_secrets.append(p.secrets)
            if surv:
                survivor_secrets.append(p.secrets)
            colored_owned.append(len([d for d in p.total_dice if d.color not in (DieColor.GRAY, DieColor.WHITE)]))
            contractor_hires.append(p.total_contractors_hired)
            release_levels[p.release_level] += 1
            for gk, label in (("bot", p.bot.name),
                              ("company", p.company.code.value if p.company else "NONE"),
                              ("op", p.white_hat.code.value if p.white_hat else "NONE")):
                g = groups[gk]
                g["m"][label] += 1
                g["s"][label] += surv
                g["w"][label] += win
                g["sec"][label].append(p.secrets)

    pg = games * num_players

    def group_out(gk: str) -> Dict[str, Dict[str, float]]:
        g = groups[gk]
        return {
            k: {"matches": g["m"][k], "win_rate": pct(g["w"][k], g["m"][k]), "survival_rate": pct(g["s"][k], g["m"][k]),
                "mean_secrets": statistics.mean(g["sec"][k])}
            for k in sorted(g["m"])
        }

    bots = group_out("bot")
    comps = group_out("company")
    ops = group_out("op")
    bot_rates = [v["win_rate"] for v in bots.values()]
    top_comp = max(comps.items(), key=lambda kv: kv[1]["win_rate"])
    return {
        "sequence": seq,
        "num_players": num_players,
        "games": games,
        "player_games": pg,
        "seed_range": [base_seed + num_players * 100_000, base_seed + num_players * 100_000 + games - 1],
        "mean_rounds": statistics.mean(rounds),
        "median_rounds": statistics.median(rounds),
        "stdev_rounds": statistics.stdev(rounds) if len(rounds) > 1 else 0.0,
        "min_rounds": min(rounds),
        "max_rounds": max(rounds),
        "round_hist": dict(sorted(Counter(rounds).items())),
        "end_reasons": {k: pct(v, games) for k, v in reasons.items()},
        "end_reason_counts": dict(reasons),
        "player_survival": pct(survivors, pg),
        "mean_final_secrets": statistics.mean(final_secrets),
        "mean_survivor_secrets": statistics.mean(survivor_secrets) if survivor_secrets else 0.0,
        "income_events": T["income_events"],
        "income_per_turn_total": pct(T["income_cash"] + T["income_research"], T["income_events"]),
        "income_per_turn_cash": pct(T["income_cash"], T["income_events"]),
        "income_per_turn_research": pct(T["income_research"], T["income_events"]),
        "zero_income_rate": pct(T["zero_income"], T["income_events"]),
        "tel_income_per_turn_incl_protocols": pct(tel_income_total, tel_income_n) if tel_income_n else None,
        "corruption_glitch_player_rounds": T["corruption_glitch_rounds"],
        "unblocked_green_player_rounds": T["green_rounds"],
        "whammy_player_rounds": T["whammy_rounds"],
        "whammy_per_player": pct(T["whammy_rounds"], pg),
        "whammy_income_mean": statistics.mean(T["whammy_income"]) if T["whammy_income"] else 0.0,
        "colored_dice_owned_end": statistics.mean(colored_owned),
        "bots": bots,
        "companies": comps,
        "operatives": ops,
        "bot_win_spread_pts": (max(bot_rates) - min(bot_rates)) * 100,
        "top_company": top_comp[0],
        "top_company_win_rate": top_comp[1]["win_rate"],
        "purple_star_ge2_rate_of_income_turns": pct(T["star_events_ge2"], T["income_events"]),
        "purple_star_ge2_spook_turns": T["star_events_ge2_spook"],
        "spook_income_turns": T["spook_income_events"],
        "tel_purple_star_double_trigger_rounds": tel_star_ge2,
        "tel_purple_star_player_rounds": tel_star_rounds,
        "burn_notice_uses": T["burn_notice_uses"],
        "burn_notice_uses_per_game": pct(T["burn_notice_uses"], games),
        "burn_notice_on_in_production": T["burn_notice_on_inprod"],
        "graduation_events": T["grad_events"],
        "graduation_capped_rate": pct(T["grad_capped"], T["grad_events"]),
        "held_in_scanned_per_player_round": pct(T["held_scanned_sum"], T["grad_events"]),
        "held_in_scanned_nonzero_rate": pct(T["held_scanned_nonzero"], T["grad_events"]),
        "graduation_by_company": {
            k: {"events": v[0], "capped_rate": pct(v[1], v[0]), "held_per_player_round": pct(v[2], v[0])}
            for k, v in sorted(T["grad_by_company"].items())
        },
        "tel_scanned_held_mean": statistics.mean(tel_held) if tel_held else None,
        "release_level_dist": {str(k): pct(v, pg) for k, v in sorted(release_levels.items())},
        "release_level_ge1": pct(sum(v for k, v in release_levels.items() if k >= 1), pg),
        "release_level_2": pct(release_levels.get(2, 0), pg),
        "contractor_hires_per_game": pct(sum(contractor_hires), games),
        "contractor_hires_per_player": statistics.mean(contractor_hires),
        "contractor_payout_events_per_game": pct(T["contractor_payout_events"], games),
        "contractor_payout_cash_per_game": pct(T["contractor_payout_cash"], games),
        "ransom_leaks_per_player": pct(T["ransom_leaks"], pg),
        "unblocked_green_per_player": pct(T["unblocked_green"], pg),
        "final_round_trigger_phase": dict(final_trigger_phase),
        "end_phase": dict(end_phase),
        "wipeout_tiebreak_level": dict(wipeout_tiebreak),
        "dmg_star_forfeited": T["dmg_star_forfeit"],
        "dmg_star_forfeited_by_code": dict(T["dmg_star_forfeit_by_code"]),
        "dmg_star_in_production_at_phase4": T["dmg_star_paid_inprod"],
        "outliers": outliers,
    }


def guardrails(r: Dict[str, Any], legacy: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    er = r["end_reasons"]
    g = {
        "rounds_8_11": 8.0 <= r["mean_rounds"] <= 11.0 and 8.0 <= r["median_rounds"] <= 11.0,
        "singularity_le_45": er.get("singularity", 0.0) <= 0.45,
        "wipeout_le_15": er.get("total_wipeout", 0.0) <= 0.15,
        "zero_income_le_30": r["zero_income_rate"] <= 0.30,
        "bot_spread_le_45": r["bot_win_spread_pts"] <= 45.0,
    }
    if legacy is not None:
        g["top_company_no_regression"] = r["top_company_win_rate"] <= legacy["top_company_win_rate"]
    return {k: ("PASS" if v else "FAIL") for k, v in g.items()}


def replay(seed: int, players: int, seq: str, base_seed: int) -> None:
    idx = seed - base_seed - players * 100_000
    reset_pod_counters()
    reset_game_scratch()
    eng = build_engine("SIX_PHASE" if seq == "six" else "LEGACY_V033", players, idx, seed)
    res = eng.run_game()
    print(f"seed={seed} players={players} seq={seq} match_idx={idx} rounds={res.total_rounds} "
          f"end={res.end_reason.value} winners={getattr(res, 'winner_ids', [res.winner_id])}")
    for t in eng.telemetry_history:
        snaps = " | ".join(f"P{s['player_id']}:{s['bot_name'][:6]} ${s['money']} S{s['secrets']}"
                           f"{' PZ' if s['is_patient_zero'] else ''}" for s in t.player_snapshots)
        print(f"  R{t.round_number} {t.active_version_name} trk={t.corruption_track} exited="
              f"{ {k.value: v for k, v in t.exited_cubes.items()} } phases={t.phases_executed} :: {snaps}")
    for r in res.rankings:
        print(f"  rank {r['rank']}: P{r['player_id']} {r['bot_name']} secrets={r['secrets']} money={r['money']} "
              f"PZ={r['is_patient_zero']}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Rogue Agent v0.34.0 six-phase telemetry sweep")
    ap.add_argument("--games", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--json", default="docs/findings/v340_telemetry_summary.json")
    ap.add_argument("--replay", type=int, default=None, help="replay one match seed")
    ap.add_argument("--players", type=int, default=2)
    ap.add_argument("--seq", choices=["six", "legacy"], default="six")
    args = ap.parse_args()

    install_wrappers()
    try:
        if args.replay is not None:
            replay(args.replay, args.players, args.seq, args.seed)
            return
        t0 = time.time()
        results: Dict[str, Dict[str, Any]] = {s: {} for s in SEQUENCES}
        timing: Dict[str, float] = {}
        for seq in SEQUENCES:
            for n in (2, 3, 4):
                ts = time.time()
                r = run_pod(seq, n, args.games, args.seed)
                timing[f"{seq}_{n}P"] = time.time() - ts
                results[seq][f"{n}P"] = r
                print(f"[{seq} {n}P] {timing[f'{seq}_{n}P']:.1f}s mean={r['mean_rounds']:.2f} "
                      f"med={r['median_rounds']} end={ {k: round(v, 3) for k, v in r['end_reasons'].items()} } "
                      f"zero_inc={r['zero_income_rate']:.3f} spread={r['bot_win_spread_pts']:.1f} "
                      f"top={r['top_company']}:{r['top_company_win_rate']:.3f}", flush=True)
        gr = {s: {} for s in SEQUENCES}
        for n in ("2P", "3P", "4P"):
            gr["SIX_PHASE"][n] = guardrails(results["SIX_PHASE"][n], results["LEGACY_V033"][n])
            gr["LEGACY_V033"][n] = guardrails(results["LEGACY_V033"][n], None)
        payload = {
            "metadata": {
                "version": "v0.34.0",
                "baseline": "GameConfig.legacy_v033 (v0.33.0, 4P = 12 Secrets)",
                "base_seed": args.seed,
                "seed_formula": "base_seed + num_players*100000 + match_idx",
                "games_per_pod": args.games,
                "elapsed_seconds": time.time() - t0,
                "pod_seconds": timing,
                "companies": {c.code.value: c.name for c in COMPANIES.values()},
                "operatives": {w.code.value: w.name for w in WHITE_HATS.values()},
            },
            "guardrails": gr,
            "results": results,
        }
        if args.json:
            os.makedirs(os.path.dirname(args.json), exist_ok=True)
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, default=str)
            print(f"JSON written to {args.json} ({payload['metadata']['elapsed_seconds']:.1f}s)")
        print(json.dumps(gr, indent=2))
    finally:
        remove_wrappers()


if __name__ == "__main__":
    main()
