"""Pre-SDLC investigation: move Income collection ahead of Attack Cube resolution.

Compares three sequencing variants of the v0.33.0 round on identical seeds:

  BASELINE  - current rules: Drop -> 2A Corruption -> 2B Attacks -> 3A Income/Ops -> 3B Pipeline
  INCOME1ST - proposal:      Drop -> 2A Corruption -> Income -> Attacks -> Pipeline -> Ops
              (Income is collected per player immediately before their Step 2B resolution;
               Phase 3A then skips income. Corruption still lands before income.)
  LITERAL   - INCOME1ST + the proposal's literal pipeline text:
              In Production -> Scanned, then Scanned -> Ready (release_bandwidth cap, FIFO),
              then Glitched -> Scanned. (Production dice now compete for release bandwidth.)

Implementation is monkeypatch-only; the engine is not modified.

v0.34 note: this script models v0.33 vs. proposals, so it runs the LEGACY path
(GameConfig.legacy_v033). Since the v0.34 module split, the monkeypatches target the call sites the
legacy path actually uses (sim.engine.legacy_v033 / phase2_compiler / phase3_income); LITERAL mode
therefore requires the legacy path.

Usage:  [MODES=BASELINE,LITERAL] [FLAT_SECRETS=8] python3 scripts/investigate_income_before_defense.py [games_per_pod]
"""

from __future__ import annotations

import os
import random
import statistics
import sys
from collections import defaultdict
from typing import Any, Dict, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sim.bots import (
    AccelerationistBot,
    AdaptiveBalancedBot,
    RecklessSaboteurBot,
    SecOpsTurtleBot,
    VentureGreedBot,
)
from sim.config import DieColor, GameConfig
from sim.engine.core import GameEngine
import sim.engine.phase2_threat as p2
import sim.engine.phase3_ops as p3
from sim.entities import get_random_companies, get_random_setup, get_random_white_hats

ORIG_DEFENSE = p2.resolve_player_defense_and_wear
ORIG_INCOME = p3.collect_player_production_income
ORIG_PHASE3 = p3.execute_phase_3
ORIG_DEMOTE = p2.demote_player_dice_step2a

BOTS = [AdaptiveBalancedBot, SecOpsTurtleBot, VentureGreedBot, AccelerationistBot, RecklessSaboteurBot]

MODE = "BASELINE"
FLAT_SECRETS = int(os.environ["FLAT_SECRETS"]) if os.environ.get("FLAT_SECRETS") else None  # e.g. 8 for all player counts
T: Dict[str, Any] = {}


def reset_tel() -> None:
    T.clear()
    T.update(
        income_cash=0, income_research=0, income_events=0,
        green_unblocked=0, green_income_dice_hit=0, green_cash_face_lost=0,
        red_unblocked=0, red_paid=0, ransom_leaks=0, blue_unblocked=0,
        zero_income_rounds=0, whammy_rounds=0, whammy_income=[],
        corruption_glitch_rounds=set(),
        literal_held_back=0,
        per_round_income=[],
    )


def _face_value(d) -> int:
    f = d.effective_face or d.current_face
    if not f or f.is_glitch:
        return 0
    return f.money + f.patches


# ---------------------------------------------------------------- patches
def patched_income(engine, player, plan=None):
    if MODE != "BASELINE" and getattr(player, "_income_done_round", None) == engine.state.current_round:
        return  # already collected before Step 2B
    m0, r0 = player.money, player.research_tokens
    ORIG_INCOME(engine, player, plan)
    dm, dr = player.money - m0, player.research_tokens - r0
    T["income_cash"] += dm
    T["income_research"] += dr
    T["income_events"] += 1
    T["per_round_income"].append(dm + dr)
    if dm + dr == 0:
        T["zero_income_rounds"] += 1
    key = (id(engine), player.player_id, engine.state.current_round)
    if key in T["corruption_glitch_rounds"] and player._green_this_round > 0:
        T["whammy_rounds"] += 1
        T["whammy_income"].append(dm + dr)
    player._income_done_round = engine.state.current_round


def patched_defense(engine, player, rolled_dice, commitments, attack_strengths, exited_cubes,
                    active_directive, defer_green_malware=False, any_shield_allocations=None, **kwargs):
    if MODE != "BASELINE":
        patched_income(engine, player, None)
    prod_before = [(d, _face_value(d)) for d in player.in_production_dice]
    ORIG_DEFENSE(engine, player, rolled_dice, commitments, attack_strengths, exited_cubes,
                 active_directive, defer_green_malware=defer_green_malware,
                 any_shield_allocations=any_shield_allocations, **kwargs)
    br = getattr(player, "last_defense_breakdown", None) or {}
    ub = br.get("unblocked", {})
    g = ub.get("green", 0)
    player._green_this_round = g
    T["green_unblocked"] += g
    T["red_unblocked"] += ub.get("red", 0)
    T["blue_unblocked"] += ub.get("blue", 0)
    T["ransom_leaks"] += 1 if br.get("flat_ransom_leak") else 0
    for d, v in prod_before:
        if d in player.in_production_dice or d.color == DieColor.WHITE:
            continue
        if v > 0:
            T["green_income_dice_hit"] += 1
            T["green_cash_face_lost"] += v


def patched_demote(player, rolled_dice, commitments, n, threat, engine=None):
    before = len(player.in_production_dice)
    ORIG_DEMOTE(player, rolled_dice, commitments, n, threat, engine=engine)
    if engine is not None and len(player.in_production_dice) < before:
        T["corruption_glitch_rounds"].add((id(engine), player.player_id, engine.state.current_round))


def patched_phase3(engine):
    if MODE != "LITERAL":
        return ORIG_PHASE3(engine)
    snap = {}
    for p in engine.state.players:
        snap[p.player_id] = ([d.die_id for d in p.scanned_dice], [d for d in p.in_production_dice if d.color != DieColor.WHITE])
    ORIG_PHASE3(engine)
    for p in engine.state.players:
        if p.is_patient_zero:
            continue
        s0_ids, prod = snap[p.player_id]
        bw = p.release_bandwidth
        slots_left = max(0, bw - len(s0_ids))
        # player chooses which production dice graduate first: most valuable (colored, expensive)
        prod = [d for d in prod if d in p.ready_for_release_dice]
        prod.sort(key=lambda d: (d.color != DieColor.GRAY, getattr(d, "cost", 0)), reverse=True)
        held = prod[slots_left:]
        n_old_stuck = max(0, len(s0_ids) - bw)
        for d in held:
            p.ready_for_release_dice.remove(d)
        p.scanned_dice[n_old_stuck:n_old_stuck] = held
        T["literal_held_back"] += len(held)


# v0.34: patch the call sites used by the legacy (v0.33) path after the module split.
import sim.engine.legacy_v033 as legacy  # noqa: E402
import sim.engine.phase2_compiler as p2c  # noqa: E402
import sim.engine.phase3_income as p3i  # noqa: E402

p2.resolve_player_defense_and_wear = legacy.resolve_player_defense_and_wear = patched_defense
p2.demote_player_dice_step2a = p2c.demote_player_dice_step2a = patched_demote
p3.collect_player_production_income = p3i.collect_player_production_income = patched_income
p3.execute_phase_3 = legacy.execute_phase_3_v033 = patched_phase3


# ---------------------------------------------------------------- runner
def run_pod(num_players: int, games: int, base_seed: int = 7_000_000) -> Dict[str, Any]:
    reset_tel()
    rounds, reasons = [], defaultdict(int)
    bot_win, bot_n, bot_surv, secrets_final = defaultdict(int), defaultdict(int), defaultdict(int), []
    dice_owned, survivors = [], []
    for gi in range(games):
        seed = base_seed + num_players * 100_000 + gi
        rng = random.Random(seed)
        bots = [BOTS[(gi * num_players + i) % len(BOTS)](i) for i in range(num_players)]
        rng.shuffle(bots)
        for i, b in enumerate(bots):
            b.player_id = i
        variants, deck = get_random_setup(rng, profile="STANDARD")
        cfg = GameConfig.legacy_v033(num_players=num_players, starting_money=6, starting_gray_dice=3,
                         starting_purple_dice=1, starting_purple_reserve=1,
                         corruption_track_profile="STANDARD", enable_corporate_asymmetry=True,
                         starting_secrets=FLAT_SECRETS)
        eng = GameEngine(config=cfg, bots=bots, seed=seed, variant_cards=variants, version_deck=deck,
                         companies=get_random_companies(num_players, rng),
                         white_hats=get_random_white_hats(num_players, rng))
        for p in eng.state.players:
            p._green_this_round = 0
        res = eng.run_game()
        rounds.append(res.total_rounds)
        reasons[eng.state.end_reason.value] += 1
        winners = set(getattr(res, "winner_ids", None) or ([res.winner_id] if getattr(res, "winner_id", None) is not None else []))
        surv = 0
        for p in eng.state.players:
            name = type(p.bot).__name__
            bot_n[name] += 1
            if not p.is_patient_zero:
                bot_surv[name] += 1
                surv += 1
            if p.player_id in winners:
                bot_win[name] += 1
            secrets_final.append(p.secrets)
            dice_owned.append(len([d for d in p.total_dice if d.color not in (DieColor.GRAY, DieColor.WHITE)]))
        survivors.append(surv)
    n_pg = games * num_players
    return dict(
        rounds=statistics.mean(rounds),
        reasons={k: v / games for k, v in reasons.items()},
        surv=sum(survivors) / n_pg,
        secrets=statistics.mean(secrets_final),
        colored=statistics.mean(dice_owned),
        inc=(T["income_cash"] + T["income_research"]) / max(1, T["income_events"]),
        cash=T["income_cash"] / max(1, T["income_events"]),
        zero_inc=T["zero_income_rounds"] / max(1, T["income_events"]),
        green_ub=T["green_unblocked"] / n_pg,
        green_inc_hits=T["green_income_dice_hit"] / n_pg,
        green_val_lost=T["green_cash_face_lost"] / n_pg,
        red_ub=T["red_unblocked"] / n_pg,
        leaks=T["ransom_leaks"] / n_pg,
        blue_ub=T["blue_unblocked"] / n_pg,
        whammy=T["whammy_rounds"] / n_pg,
        whammy_inc=statistics.mean(T["whammy_income"]) if T["whammy_income"] else 0.0,
        held=T["literal_held_back"] / n_pg,
        bot_win={k: bot_win[k] / bot_n[k] for k in bot_n},
        bot_surv={k: bot_surv[k] / bot_n[k] for k in bot_n},
        p10_inc=sorted(T["per_round_income"])[len(T["per_round_income"]) // 10] if T["per_round_income"] else 0,
    )


def main() -> None:
    global MODE
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    out: Dict[str, Dict[int, Dict[str, Any]]] = {}
    modes = os.environ.get("MODES", "BASELINE,INCOME1ST,LITERAL").split(",")
    for mode in modes:
        MODE = mode
        out[mode] = {n: run_pod(n, games) for n in (2, 3, 4)}

    def row(label, key, fmt="{:.2f}", sub=None):
        cells = []
        for mode in out:
            for n in (2, 3, 4):
                v = out[mode][n][key] if sub is None else out[mode][n][key].get(sub, 0.0)
                cells.append(fmt.format(v))
        print(f"{label:<28}" + " | ".join(f"{c:>6}" for c in cells))

    print(f"games/pod={games}")
    print(f"{'metric':<28}" + " | ".join(f"{m[:4]}{n}P".rjust(6) for m in out for n in (2, 3, 4)))
    row("mean rounds", "rounds")
    for r in ("patient_zero", "singularity", "total_wipeout", "round_limit"):
        row(f"end: {r}", "reasons", "{:.1%}", r)
    row("player survival", "surv", "{:.1%}")
    row("final secrets (mean)", "secrets")
    row("colored dice owned (end)", "colored")
    row("income/turn ($+R)", "inc")
    row("cash income/turn", "cash")
    row("p10 income/turn", "p10_inc", "{:.0f}")
    row("zero-income turns", "zero_inc", "{:.1%}")
    row("unblocked green /plyr", "green_ub")
    row("income dice glitched /plyr", "green_inc_hits")
    row("income face value hit /plyr", "green_val_lost")
    row("unblocked red /plyr", "red_ub")
    row("ransom leaks /plyr", "leaks")
    row("unblocked blue /plyr", "blue_ub")
    row("whammy rounds /plyr", "whammy")
    row("income in whammy rounds", "whammy_inc")
    row("LITERAL dice held /plyr", "held")
    print("\nWin rate by bot (2P/3P/4P per mode)")
    for b in sorted(next(iter(out.values()))[2]["bot_win"]):
        row(f"  win {b[:22]}", "bot_win", "{:.0%}", b)
    for b in sorted(next(iter(out.values()))[2]["bot_surv"]):
        row(f"  surv {b[:21]}", "bot_surv", "{:.0%}", b)


if __name__ == "__main__":
    main()
