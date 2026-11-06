"""SUPERSEDED (v0.35.0): the D1 design is now in the engine (sim/engine/research_tracks.py, sim/bots/research_policy.py);
use scripts/run_v350_research_track_check.py. Kept for the record; it monkeypatches the v0.34 engine, so run it
against GameConfig.legacy_v034() semantics only.

Phase 43 Research Income Sweep (throwaway modeling script; does NOT modify sim/).

Prototypes the locked v0.35.0 Research Track design
(docs/explorations/2026_11_research_track_rebalance_plan.md) on top of the v0.34.0 engine by
monkeypatching PlayerState track/patent methods, die factories and two phase hooks, then measures
research income, track completion, pacing and company win rates for several levers.

Usage:
  python3 scripts/investigate_v350_research_sweep.py --games 600 --seed 4300 --cells all
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import statistics
import sys
import time
from collections import Counter, defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import sim.entities as ent  # noqa: E402
import sim.engine.core as core_mod  # noqa: E402
import sim.engine.phase4_attack_resolution as p4  # noqa: E402
import sim.engine.phase5_pipeline_shift as p5  # noqa: E402
import sim.engine.phase6_operations as p6  # noqa: E402
import sim.engine.state as st_mod  # noqa: E402
from sim.bots import (  # noqa: E402
    AccelerationistBot, AdaptiveBalancedBot, RecklessSaboteurBot, SecOpsTurtleBot, VentureGreedBot,
)
from sim.config import DieColor, GameConfig  # noqa: E402
from sim.entities import Face, ShieldColor, get_random_companies, get_random_setup, get_random_white_hats  # noqa: E402
from sim.engine.core import GameEngine  # noqa: E402
from sim.engine.state import PlayerState  # noqa: E402

BOT_CLASSES = [AdaptiveBalancedBot, SecOpsTurtleBot, VentureGreedBot, AccelerationistBot, RecklessSaboteurBot]
TRACKS = ("DEFENSE", "TRIAGE", "RELEASE", "PATENT")
LVL_ATTR = {"DEFENSE": "defense_level", "TRIAGE": "triage_level", "RELEASE": "release_level", "PATENT": "patent_level"}

# ----------------------------------------------------------------------------------------------
# Global knobs (set per cell)
# ----------------------------------------------------------------------------------------------
K = {
    "design": "v035",      # "v034" (untouched engine) or "v035"
    "costs": (1, 2, 2, 3),
    "gray": "base",        # base | choice2 | r2 | r2c
    "purple": "base",      # base | r2
    "policy": "stock",     # stock | aware
    "purple_l3": "free",   # free | access
    "swap": "diff",        # diff | free
    "comp_bonus": {},      # company code -> dict of overrides
}
ENG = {"e": None}
STATS = defaultdict(Counter)  # per-game scratch

# ----------------------------------------------------------------------------------------------
# Die faces
# ----------------------------------------------------------------------------------------------
ORIG_GRAY, ORIG_COLORED = ent.create_gray_die, ent.create_colored_die
R1 = Face(name="+1 🔬", patches=1)
CHOICE = Face(name="+$1 / +1 🔬", is_choice=True, choices=(Face("+$1", money=1), Face("+1 🔬", patches=1)))
M1R1 = Face(name="+$1 & +1 🔬", money=1, patches=1)


def gray_die(die_id, profile="V034"):
    d = ORIG_GRAY(die_id, "V034")
    f = list(d.faces)  # [B, B, $1, $1, choice, R1]
    g = K["gray"]
    if K["design"] == "v035":
        if g == "choice2":      # one +$1 -> +$1/+1 choice   (1 R1 + 2 choice)
            f[3] = CHOICE
        elif g == "r2":         # choice -> +1 research     (2 R1, 2 $1)
            f[4] = R1
        elif g == "m1":         # one +$1 -> +$1 & +1 research
            f[3] = M1R1
        elif g == "m1c":        # +$1 -> +$1 & +1 research, other +$1 -> +$1/+1 choice
            f[2] = M1R1; f[3] = CHOICE
        elif g == "m2":         # both +$1 -> +$1 & +1 research
            f[2] = M1R1; f[3] = M1R1
        elif g == "r2c":        # +$1 -> +1 research, keep choice (2 R1 + 1 choice + 1 $1)
            f[3] = R1
    d.faces = f
    return d


def colored_die(color, die_id, *a, **kw):
    d = ORIG_COLORED(color, die_id, *a, **kw)
    if color == DieColor.PURPLE and K["design"] == "v035" and K["purple"] == "r2":
        f = list(d.faces)  # [B, B, $2, $1&R1, glitch, star]
        f[2] = M1R1
        d.faces = f
    return d


for mod in list(sys.modules.values()):
    if mod and getattr(mod, "__name__", "").startswith("sim"):
        if getattr(mod, "create_gray_die", None) is ORIG_GRAY:
            mod.create_gray_die = gray_die
        if getattr(mod, "create_colored_die", None) is ORIG_COLORED:
            mod.create_colored_die = colored_die

# ----------------------------------------------------------------------------------------------
# Tracks, Breakthroughs, Patents
# ----------------------------------------------------------------------------------------------
ORIG_COST, ORIG_UP = PlayerState.get_track_upgrade_cost, PlayerState.upgrade_track
ORIG_PCOST, ORIG_FILE = PlayerState.get_patent_cost, PlayerState.file_patent
PATENT_RATE = {0: (2, 1), 1: (2, 1), 2: (3, 2), 3: (3, 2), 4: (1, 1)}


def new_cost(self, track):
    if K["design"] != "v035":
        return ORIG_COST(self, track)
    t = track.upper().strip()
    if t not in LVL_ATTR:
        return None
    lvl = getattr(self, LVL_ATTR[t])
    return None if lvl >= 4 else K["costs"][lvl]


def _ready_append(self, die):
    self.ready_for_release_dice.append(die)


def new_upgrade(self, track):
    if K["design"] != "v035":
        return ORIG_UP(self, track)
    t = track.upper().strip()
    cost = new_cost(self, t)
    if cost is None or self.research_tokens < cost:
        return False
    self.research_tokens -= cost
    attr = LVL_ATTR[t]
    lvl = getattr(self, attr) + 1
    setattr(self, attr, lvl)
    eng = ENG["e"]
    s = STATS[self.player_id]
    s[f"{t}_spent"] += cost
    bump = (lvl >= 2) + (lvl >= 4)
    if t == "DEFENSE":
        self.defense_capacity = 2 + bump
    elif t == "TRIAGE":
        self.triage_bandwidth = 2 + bump
    elif t == "RELEASE":
        self.release_bandwidth = 4 + bump
    # Breakthroughs
    if lvl == 1 and t in ("DEFENSE", "RELEASE"):
        _ready_append(self, gray_die(eng.state.next_die_id)); eng.state.next_die_id += 1
        s["bt_gray"] += 1
    elif lvl == 3 and t in ("DEFENSE", "RELEASE"):
        self.secrets += 1; s["bt_secret"] += 1
    elif lvl == 1 and t == "TRIAGE":
        n = min(2, eng.state.contractor_supply)
        for _ in range(n):
            _ready_append(self, ent.create_white_die(eng.state.next_die_id)); eng.state.next_die_id += 1
        eng.state.contractor_supply -= n
        s["bt_white"] += n
    elif lvl == 3 and t == "TRIAGE":
        _swap(self, eng, s)
    elif lvl == 1 and t == "PATENT":
        self.money += 3; s["bt_cash"] += 3
    elif lvl == 3 and t == "PATENT":
        if K["purple_l3"] == "free":
            if self.personal_purple_reserve > 0:
                self.personal_purple_reserve -= 1
                _ready_append(self, colored_die(DieColor.PURPLE, eng.state.next_die_id, reserve_cost=5))
                eng.state.next_die_id += 1
                s["bt_purple"] += 1
            else:
                s["bt_purple_dead"] += 1
        else:
            self._purple_unlocked = True
    return True


def _swap(self, eng, s):
    """Triage L3: swap 1 owned colored die (not Purple) in Ready for Release for a Market die of a
    different color; pay the cost difference if higher (no refund); old die returns to the Market."""
    owned = [d for d in self.ready_for_release_dice if d.color in (DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW)]
    if not owned:
        s["bt_swap_dead"] += 1
        return
    old = min(owned, key=lambda d: d.cost)
    best = None
    for c in (DieColor.YELLOW, DieColor.GREEN, DieColor.RED, DieColor.BLUE):
        if c == old.color or eng.state.market.get(c, 0) <= 0:
            continue
        cost = eng.state.get_market_die_cost(c)
        pay = 0 if K["swap"] == "free" else max(0, cost - old.cost)
        if pay <= self.money:
            best = (c, pay); break
    if not best:
        s["bt_swap_dead"] += 1
        return
    c, pay = best
    self.money -= pay
    self.ready_for_release_dice.remove(old)
    eng.state.market[old.color] = eng.state.market.get(old.color, 0) + 1
    eng.state.market[c] -= 1
    _ready_append(self, colored_die(c, eng.state.next_die_id, variant_card=eng.state.variant_cards.get(c)))
    eng.state.next_die_id += 1
    s["bt_swap"] += 1


def new_pcost(self):
    if K["design"] != "v035":
        return ORIG_PCOST(self)
    return PATENT_RATE[self.patent_level][0]


def new_file(self):
    if K["design"] != "v035":
        r = ORIG_FILE(self)
        if r:
            STATS[self.player_id]["patent_secrets"] += 1
        return r
    cost, gain = PATENT_RATE[self.patent_level]
    if self.research_tokens < cost:
        return False
    self.research_tokens -= cost
    self.secrets += gain
    STATS[self.player_id]["patent_secrets"] += gain
    STATS[self.player_id]["patent_spent"] += cost
    return True


def _rt_get(self):
    return self.__dict__.get("_rt", 0)


def _rt_set(self, v):
    old = self.__dict__.get("_rt", 0)
    if v > old and "player_id" in self.__dict__ and self.__dict__.get("_rt_live"):
        STATS[self.player_id]["res_gained"] += v - old
    self.__dict__["_rt"] = v


PlayerState.research_tokens = property(_rt_get, _rt_set)
PlayerState.get_track_upgrade_cost = new_cost
PlayerState.upgrade_track = new_upgrade
PlayerState.get_patent_cost = new_pcost
PlayerState.file_patent = new_file

# Purple reserve gating (purple_l3 == "access": reserve purchase only after Patents L3)
ORIG_P6_EXEC = p6.execute_player_operations_turn


def gated_exec(engine, player, plan, **kw):
    if K["design"] == "v035" and K["purple_l3"] == "access" and not getattr(player, "_purple_unlocked", False):
        if plan is not None and DieColor.PURPLE in getattr(plan, "market_purchases", []):
            plan.market_purchases = [c for c in plan.market_purchases if c != DieColor.PURPLE]
            plan.buy_purple_reserve = False
    if plan is not None and DieColor.PURPLE in getattr(plan, "market_purchases", []):
        STATS[player.player_id]["purple_buy_attempt"] += 1
    return ORIG_P6_EXEC(engine, player, plan, **kw)


p6.execute_player_operations_turn = gated_exec

# Triage L4: +1 research per die moved in Conveyor Triage beyond the 2nd
ORIG_TRIAGE = p5.conveyor_triage


def triage_hook(player):
    moved = ORIG_TRIAGE(player)
    if K["design"] == "v035" and player.triage_level >= 4 and len(moved) > 2:
        player.research_tokens += len(moved) - 2
        STATS[player.player_id]["t4_research"] += len(moved) - 2
    return moved


p5.conveyor_triage = triage_hook

# Defense L4: +$1 if no unblocked Attack Cube hit you (approx: no Secret/$/die-to-Glitched loss)
ORIG_DEF = p4.resolve_player_defense_and_wear


def def_hook(engine, player, *a, **kw):
    before = (player.secrets, player.money, len(player.glitched_dice))
    r = ORIG_DEF(engine, player, *a, **kw)
    if K["design"] == "v035" and player.defense_level >= 4:
        if player.secrets >= before[0] and player.money >= before[1] and len(player.glitched_dice) <= before[2]:
            player.money += 1
            STATS[player.player_id]["d4_cash"] += 1
    if K["design"] == "v035":
        player.has_passive_firewall = False
        player.has_emergency_hotfix = False
    return r


p4.resolve_player_defense_and_wear = def_hook
# NOTE: Release L4 "+1 free reroll" is NOT modeled (free rerolls are a global config read).

# ----------------------------------------------------------------------------------------------
# Research-aware policy (wraps each bot's Operations plan; replaces only the research section)
# ----------------------------------------------------------------------------------------------
FOCUS = {
    "AdaptiveBalancedBot": ["TRIAGE", "DEFENSE", "RELEASE", "PATENT"],
    "SecOpsTurtleBot": ["DEFENSE", "TRIAGE", "RELEASE", "PATENT"],
    "VentureGreedBot": ["PATENT", "RELEASE", "DEFENSE", "TRIAGE"],
    "AccelerationistBot": ["RELEASE", "PATENT", "TRIAGE", "DEFENSE"],
    "RecklessSaboteurBot": ["PATENT", "TRIAGE", "RELEASE", "DEFENSE"],
}


def aware_research(bot, player, state, plan):
    plan.track_upgrades = []
    plan.patent_filings = 0
    res = player.research_tokens
    lv = {t: getattr(player, LVL_ATTR[t]) for t in TRACKS}
    order = FOCUS[type(bot).__name__]
    if K.get("focus") == "random":
        if not hasattr(bot, "_rfocus"):
            r = random.Random(hash((id(state), bot.player_id)) & 0xFFFF)
            o = list(TRACKS); r.shuffle(o); bot._rfocus = o
        order = bot._rfocus
    late = getattr(state, "is_final_round", False) or min(p.secrets for p in state.players if not p.is_patient_zero) <= 3
    if not late:
        # 1) focus track to L4; 2) then L1 Breakthroughs (cost 1) on secondaries; 3) then L2 of 2nd track
        wants = []
        f = order[0]
        for _ in range(lv[f], 4):
            wants.append(f)
        for t in order[1:]:
            if lv[t] < 1:
                wants.append(t)
        wants.append(order[1]) if lv[order[1]] < 2 else None
        sim_lv = dict(lv)
        for t in wants:
            if sim_lv[t] >= 4:
                continue
            c = K["costs"][sim_lv[t]]
            if res >= c:
                plan.track_upgrades.append(t); res -= c; sim_lv[t] += 1
            else:
                break  # save toward this step
        if any(sim_lv[t] < 4 for t in [order[0]]) or res < 4:
            return plan
    # file patents with whatever remains (late game, or nothing left to buy)
    rate = PATENT_RATE[lv["PATENT"]][0]
    plan.patent_filings = res // rate
    return plan


def install_policy(bot):
    if K["policy"] != "aware" or K["design"] != "v035":
        return
    cls_fn = None
    for klass in type(bot).__mro__:
        if "take_operations_actions" in klass.__dict__ or "take_phase3_actions" in klass.__dict__:
            cls_fn = klass.__dict__.get("take_operations_actions") or klass.__dict__.get("take_phase3_actions")
            break

    def ops(player_state, game_state, rng, _f=cls_fn, _b=bot):
        plan = _f(_b, player_state, game_state, rng)
        return aware_research(_b, player_state, game_state, plan)

    bot.take_operations_actions = ops
    orig_decl = bot.declare_choices

    def decl(player_state, active_dice=None, *a, _o=orig_decl, **kw):
        d = _o(player_state, active_dice, *a, **kw)
        dice = active_dice if active_dice is not None else (kw.get("rolled_dice") or [])
        for idx, die in enumerate(dice):
            f = die.current_face
            if f and f.is_choice and not f.has_shield_option:
                for j, c in enumerate(f.choices):
                    if c.patches > 0:
                        d[idx] = j
        return d

    bot.declare_choices = decl


# ----------------------------------------------------------------------------------------------
# Companies
# ----------------------------------------------------------------------------------------------
def adjust_company(c):
    if K["design"] != "v035":
        return c
    c = dataclasses.replace(
        c, starting_defense_capacity=2, starting_triage_bandwidth=2, starting_release_bandwidth=4,
        starting_triage_level=0, starting_release_level=0, starting_defense_level=0, starting_patent_level=0,
        starting_research_bonus=0, upgrade_discount=0,
    )
    extra = K["comp_bonus"].get(c.code.value if hasattr(c.code, "value") else str(c.code))
    if extra:
        c = dataclasses.replace(c, **extra)
    return c


# ----------------------------------------------------------------------------------------------
# Runner
# ----------------------------------------------------------------------------------------------
def pctl(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else 0


def run_cell(name, games, seed, players=(2, 3, 4)):
    out = {"name": name, "knobs": {k: v for k, v in K.items()}, "by_p": {}}
    agg = defaultdict(list)
    comp_m, comp_w = Counter(), Counter()
    bot_m, bot_w = Counter(), Counter()
    maxed_track = Counter()
    for n in players:
        rounds, reasons = [], Counter()
        for i in range(games):
            ms = seed + n * 100_000 + i
            rng = random.Random(ms)
            bots = [BOT_CLASSES[(i * n + j) % 5](j) for j in range(n)]
            rng.shuffle(bots)
            for j, b in enumerate(bots):
                b.player_id = j
                install_policy(b)
            variants, deck = get_random_setup(rng, profile="STANDARD")
            comps = [adjust_company(c) for c in get_random_companies(n, rng)]
            whs = get_random_white_hats(n, rng)
            cfg = GameConfig.legacy_v034(num_players=n, starting_money=6, starting_gray_dice=3, starting_purple_dice=1,
                             starting_purple_reserve=1, corruption_track_profile="STANDARD",
                             enable_corporate_asymmetry=True)
            STATS.clear()
            eng = GameEngine(config=cfg, bots=bots, seed=ms, variant_cards=variants, version_deck=deck,
                             companies=comps, white_hats=whs)
            ENG["e"] = eng
            if K["design"] == "v035":
                for p in eng.state.players:
                    p.has_passive_firewall = False
                    p.has_emergency_hotfix = False
            for p in eng.state.players:
                p.__dict__["_rt_live"] = True
            res = eng.run_game()
            rounds.append(res.total_rounds)
            reasons[res.end_reason.value] += 1
            inc = defaultdict(int)
            for tel in eng.telemetry_history:
                for pid, v in (tel.income_by_player or {}).items():
                    inc[pid] += v.get("research", 0)
            w_ids = list(getattr(res, "winner_ids", None) or ([res.winner_id] if res.winner_id is not None else []))
            for p in eng.state.players:
                s = STATS[p.player_id]
                r_total = s["res_gained"]
                agg[f"res_{n}"].append(r_total)
                agg["res"].append(r_total)
                lv = [getattr(p, LVL_ATTR[t]) for t in TRACKS]
                agg["steps"].append(sum(lv))
                agg["n_l4"].append(sum(1 for x in lv if x >= 4))
                agg["all_max"].append(int(all(x >= 4 for x in lv)))
                for t, x in zip(TRACKS, lv):
                    agg[f"lvl_{t}"].append(x)
                    if x >= 4:
                        maxed_track[t] += 1
                agg["patent_secrets"].append(s["patent_secrets"])
                agg["bt_secret"].append(s["bt_secret"])
                agg["final_secrets"].append(p.secrets)
                if not p.is_patient_zero:
                    agg[f"surv_secrets_{n}"].append(p.secrets)
                agg["leftover_res"].append(p.research_tokens)
                for k2 in ("bt_swap", "bt_swap_dead", "bt_purple", "bt_purple_dead", "d4_cash", "bt_white", "bt_gray", "purple_buy_attempt"):
                    agg[k2].append(s[k2])
                win = (1.0 / len(w_ids)) if (p.player_id in w_ids and (not p.is_patient_zero or res.is_total_wipeout)) else 0.0
                cc = p.company.code.value if p.company else "none"
                comp_m[cc] += 1; comp_w[cc] += win
                bn = type(p.bot).__name__
                bot_m[bn] += 1; bot_w[bn] += win
        out["by_p"][n] = {
            "rounds": round(statistics.mean(rounds), 2),
            "reasons": {k: round(v / games, 3) for k, v in reasons.items()},
            "res_mean": round(statistics.mean(agg[f"res_{n}"]), 2),
            "res_med": statistics.median(agg[f"res_{n}"]),
            "res_p10": pctl(agg[f"res_{n}"], 0.1), "res_p90": pctl(agg[f"res_{n}"], 0.9),
            "surv_secrets": round(statistics.mean(agg[f"surv_secrets_{n}"]), 2) if agg[f"surv_secrets_{n}"] else None,
        }
    m = lambda k: round(statistics.mean(agg[k]), 3)
    out["res_mean"] = m("res")
    out["res_med"] = statistics.median(agg["res"])
    out["steps_mean"] = m("steps")
    out["steps_dist"] = dict(sorted(Counter(agg["steps"]).items()))
    out["n_l4_dist"] = {k: round(v / len(agg["n_l4"]), 3) for k, v in sorted(Counter(agg["n_l4"]).items())}
    out["all_max"] = m("all_max")
    tot_max = sum(maxed_track.values())
    out["maxed_share"] = {t: round(maxed_track[t] / tot_max, 3) if tot_max else 0 for t in TRACKS}
    out["lvl_mean"] = {t: m(f"lvl_{t}") for t in TRACKS}
    for k2 in ("patent_secrets", "bt_secret", "final_secrets", "leftover_res", "bt_swap", "bt_swap_dead", "bt_purple",
               "bt_purple_dead", "d4_cash", "bt_white", "bt_gray", "purple_buy_attempt"):
        out[k2] = m(k2)
    out["company_wr"] = {c: round(comp_w[c] / comp_m[c], 3) for c in sorted(comp_m)}
    out["bot_wr"] = {c: round(bot_w[c] / bot_m[c], 3) for c in sorted(bot_m)}
    cw = list(out["company_wr"].values())
    out["company_spread"] = round(max(cw) - min(cw), 3)
    bw = list(out["bot_wr"].values())
    out["bot_spread"] = round(max(bw) - min(bw), 3)
    return out


CELLS = {
    "A0_v034_baseline": dict(design="v034"),
    "A1_v035_stock_baseFaces": dict(),
    "A2_v035_aware_baseFaces": dict(policy="aware"),
    "B1_stock_gray_r2": dict(gray="r2"),
    "B2_stock_gray_choice2": dict(gray="choice2"),
    "B3_stock_gray_r2c": dict(gray="r2c"),
    "B4_stock_purple_r2": dict(purple="r2"),
    "B5_stock_gray_m1": dict(gray="m1"),
    "B6_stock_gray_m2": dict(gray="m2"),
    "C7_aware_gray_m1": dict(policy="aware", gray="m1"),
    "C8_aware_gray_m2": dict(policy="aware", gray="m2"),
    "C9_aware_gray_m1_purple_r2": dict(policy="aware", gray="m1", purple="r2"),
    "C10_aware_gray_m2_purple_r2": dict(policy="aware", gray="m2", purple="r2"),
    "D1_aware_gray_m1c": dict(policy="aware", gray="m1c"),
    "D2_aware_gray_m1c_purple_r2": dict(policy="aware", gray="m1c", purple="r2"),
    "D3_aware_m2_access": dict(policy="aware", gray="m2", purple_l3="access"),
    "D4_aware_m2_swapfree": dict(policy="aware", gray="m2", swap="free"),
    "D5_aware_m1c_p_r2_access": dict(policy="aware", gray="m1c", purple="r2", purple_l3="access"),
    "E1_D1_randfocus": dict(policy="aware", gray="m1c", focus="random"),
    "F1_D1_helix_cash2_prom_cash2": dict(policy="aware", gray="m1c", comp_bonus={"HELIX": {"starting_cash_bonus": 2}, "PROMETHEUS": {"starting_cash_bonus": 2}}),
    "F2_D1_helix_sec1_prom_sec1": dict(policy="aware", gray="m1c", comp_bonus={"HELIX": {"starting_secrets_bonus": 1}, "PROMETHEUS": {"starting_secrets_bonus": 1}}),
    "F3_D1_helix_cash1_prom_cash2_dto_nosec": dict(policy="aware", gray="m1c", comp_bonus={"HELIX": {"starting_cash_bonus": 1}, "PROMETHEUS": {"starting_cash_bonus": 2}, "DTO": {"starting_secrets_bonus": 0}}),
    "F4_D1_dto_nosec": dict(policy="aware", gray="m1c", comp_bonus={"DTO": {"starting_secrets_bonus": 0}}),
    "C1_aware_gray_r2": dict(policy="aware", gray="r2"),
    "C2_aware_gray_choice2": dict(policy="aware", gray="choice2"),
    "C3_aware_gray_r2c": dict(policy="aware", gray="r2c"),
    "C4_aware_gray_r2_purple_r2": dict(policy="aware", gray="r2", purple="r2"),
    "C5_aware_gray_choice2_purple_r2": dict(policy="aware", gray="choice2", purple="r2"),
    "C6_aware_gray_r2c_purple_r2": dict(policy="aware", gray="r2c", purple="r2"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=400)
    ap.add_argument("--seed", type=int, default=4300)
    ap.add_argument("--cells", default="all")
    ap.add_argument("--extra", default="", help="JSON dict of knob overrides applied to every selected cell")
    ap.add_argument("--tag", default="")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    names = list(CELLS) if a.cells == "all" else a.cells.split(",")
    extra = json.loads(a.extra) if a.extra else {}
    results = []
    defaults = dict(K)
    for nm in names:
        K.clear(); K.update(defaults); K.update(CELLS[nm]); K.update(extra)
        t0 = time.time()
        r = run_cell(nm + a.tag, a.games, a.seed)
        r["secs"] = round(time.time() - t0, 1)
        results.append(r)
        print(json.dumps(r, default=str), flush=True)
    if a.out:
        with open(a.out, "w") as fh:
            json.dump(results, fh, indent=1, default=str)


if __name__ == "__main__":
    main()
