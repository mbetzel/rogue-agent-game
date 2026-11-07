"""Exploration probe (not rules code): end-game Market Share placement bonus.

Rule under test: when the game ends (not a Total Wipeout), surviving players are ranked by Market Share and gain
bonus Corporate Secrets by placement (e.g. 5/3/2/1). Patient Zeros gain nothing.
  pool="surv": only survivors are placed (a Patient Zero frees its place for survivors below it).
  pool="all":  every player is placed; a Patient Zero's place is simply forfeited.
  ties="std":  Market Share ties broken by the standard tiebreakers (Money > Active Colored dice in Ready >
               Research > fewest Under Development); fully tied players share the better place.
  ties="share": tied Market Share shares the better place (no further tiebreak).
Then the normal Corporate Secrets ranking runs.

Bot modes: "none" (current bots, bonus ignored in play), "all" / "one" bonus-aware seats.
Aware seats (TUNE-BOT heuristics):
  * Generic shield: one Red cube is worth W(time) x 3 x (expected bonus with it blocked - unblocked), on top
    of the existing Red value (3 = value of one Secret saved by blocking Blue). Lethal Blue still protected.
  * Research: before upgrades, buy the smallest regain that raises the expected bonus (v2.0 onward / Final Round).
"""
import os, sys, statistics as St
from collections import Counter, defaultdict
from multiprocessing import Pool
ROOT = "/home/mike/antigravity/rogue-agent"
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "scripts"))
import run_v360_market_share_sweep as sw
from sim.engine import core, end_game, phase4_attack_resolution as p4
from sim.bots import market_share_policy as msp
from sim.entities import CubeColor
from sim.config import DieColor

P = dict(bonus=None, pool="surv", ties="std", aware=set(), w=(0.3, 0.6, 1.0, 1.0))
TEL = {}


def bonus_vec(n):
    b = list(P["bonus"] or [])
    return (b + [0] * 4)[:n]


def _ready_colored(p):
    ds = list(p.ready_for_release_dice) + [x for x in p.in_production_dice if x not in p.ready_for_release_dice]
    return sum(1 for d in ds if d.color not in (DieColor.GRAY, DieColor.WHITE))


def _tkey(p):
    ms = int(p.market_share or 0)
    if P["ties"] == "share":
        return (ms,)
    return (ms, p.money, _ready_colored(p), p.patches, -(len(p.glitched_dice) + len(p.scanned_dice)))


def award(players):
    """Returns {pid: bonus}. Competition ranking on the tie key; tied players share the better place."""
    n = len(players)
    B = bonus_vec(n)
    pool = [p for p in players if (P["pool"] == "all" or not p.is_patient_zero)]
    pool.sort(key=_tkey, reverse=True)
    out, prev, place = {}, None, 0
    ties_ms = 0
    for i, p in enumerate(pool):
        k = _tkey(p)
        if k != prev:
            place, prev = i, k
        out[p.player_id] = 0 if p.is_patient_zero else B[place]
    # telemetry: did any adjacent pair tie on Market Share (so a non-MS key decided a paid place)?
    for a, b in zip(pool, pool[1:]):
        if int(a.market_share or 0) == int(b.market_share or 0) and not b.is_patient_zero:
            ties_ms += 1
    return out, ties_ms


orig_eval = end_game.evaluate_end_game
def eval_hook(engine):
    ps = engine.state.players
    pre = {p.player_id: p.secrets for p in ps}
    surv = [p for p in ps if not p.is_patient_zero]
    TEL.update(pre=pre, bonus={}, ms_ties=0, winner_pre=None)
    if surv:
        best = max(surv, key=lambda p: (p.secrets, int(p.market_share or 0), p.money))
        TEL["winner_pre"] = {p.player_id for p in surv if (p.secrets, int(p.market_share or 0), p.money) ==
                             (best.secrets, int(best.market_share or 0), best.money)}
    if P["bonus"] and surv:
        b, t = award(ps)
        TEL["bonus"], TEL["ms_ties"] = b, t
        for p in ps:
            p.secrets += b.get(p.player_id, 0)
    return orig_eval(engine)
end_game.evaluate_end_game = eval_hook


# ---------------- aware bots ----------------
def exp_bonus(share, rivals, n):
    B = bonus_vec(n)
    hi = sum(1 for v in rivals if v > share); tie = sum(1 for v in rivals if v == share)
    places = B[hi: hi + tie + 1]
    return sum(places) / len(places)


def _time_w(state):
    if getattr(state, "is_final_round", False):
        return P["w"][3]
    return P["w"][min(2, state.current_version_index)]


orig_mbv = msp.marginal_block_value
def mbv(color, rem, player, state, attack, pol):
    v = orig_mbv(color, rem, player, state, attack, pol)
    if (color == CubeColor.RED and P["bonus"] and player.player_id in P["aware"] and v != float("-inf")):
        r = int(rem.get(color, 0)); share = int(player.market_share or 0); n = len(state.players)
        rivals = list(msp.estimated_rival_shares(player, state, attack.get(CubeColor.RED, 0)).values())
        d = exp_bonus(max(0, share - r + 1), rivals, n) - exp_bonus(max(0, share - r), rivals, n)
        v += _time_w(state) * pol.blue_value * d
    return v
msp.marginal_block_value = mbv

orig_ur = msp.urgent_regain
def ur(player, state, pol, cap):
    k0 = orig_ur(player, state, pol, cap)
    if (not P["bonus"] or player.player_id not in P["aware"] or player.market_share is None
            or (state.current_version_index < 1 and not state.is_final_round)):
        return k0
    room = min(cap, player.market_share_max - player.market_share)
    rivals = [int(p.market_share or 0) for p in state.players if p.player_id != player.player_id and not p.is_patient_zero]
    if not rivals:
        return k0
    n = len(state.players); base = exp_bonus(player.market_share, rivals, n)
    for k in range(1, room + 1):
        if exp_bonus(player.market_share + k, rivals, n) > base:
            return max(k0, k)
    return k0
msp.urgent_regain = ur


orig_amsp = msp.apply_market_share_policy
def amsp(bot, plan, player, state):
    plan = orig_amsp(bot, plan, player, state)
    cfg = state.config
    if not (P["bonus"] and P.get("deep") is True and player.player_id in P["aware"] and player.market_share is not None):
        return plan
    if state.current_version_index >= 2 or state.market.get(DieColor.RED, 0) <= 0:
        return plan
    rivals = [int(p.market_share or 0) for p in state.players if p.player_id != player.player_id and not p.is_patient_zero]
    n = len(state.players)
    if not rivals or exp_bonus(player.market_share, rivals, n) >= max(bonus_vec(n)):
        return plan
    owned_red = sum(1 for d in player.total_dice if d.color == DieColor.RED)
    purchases = list(getattr(plan, "market_purchases", []) or [])
    if owned_red >= 2 or DieColor.RED in purchases:
        return plan
    limit = cfg.max_market_purchases_per_turn
    new = purchases + [DieColor.RED] if len(purchases) < limit else (
        [c for c in purchases if c != DieColor.BLUE][: limit - 1] + [DieColor.RED] if DieColor.BLUE not in purchases or len(purchases) > 1 else None)
    if new is None:
        return plan
    other = msp._planned_spend(plan, player, state) - sum(state.get_market_die_cost(c) for c in purchases[:limit] if c != DieColor.PURPLE)
    trial = sum(state.get_market_die_cost(c) for c in new[:limit] if c != DieColor.PURPLE)
    if player.money - other - trial >= 0:
        plan.market_purchases = new
        RED_NUDGE[player.player_id] += 1
    return plan
msp.apply_market_share_policy = amsp
RED_NUDGE = Counter()


def pr_focus(bot):
    f = list(getattr(bot, "research_focus_v036", None) or bot.research_focus)
    f.remove("PATENT")
    return tuple(["PATENT"] + f) if P.get("deep") == "pr_first" else tuple([f[0], "PATENT"] + f[1:])


# ---------------- defense telemetry ----------------
DEF = Counter()
orig_res = p4.resolve_player_defense_and_wear
def res(engine, player, *a, **kw):
    s0 = player.secrets; out = orig_res(engine, player, *a, **kw)
    DEF[(player.player_id, "blue_lost")] += max(0, s0 - player.secrets)
    b = getattr(player, "last_defense_breakdown", None)
    if b:
        pid = player.player_id
        cs = b["color_shields"]; any_n = cs["any"]
        for c in ("red", "blue", "green"):
            DEF[(pid, "any_" + c)] += b["any_allocated"][c]
            DEF[(pid, "inc_" + c)] += b["effective_attacks"][c]
            DEF[(pid, "blk_" + c)] += b["blocked"][c]
        rem = {k: max(0, b["effective_attacks"][k] - cs.get(k, 0)) for k in ("red", "blue", "green")}
        if any_n > 0 and rem["blue"] > 0 and rem["red"] > 0 and rem["blue"] + rem["red"] + rem["green"] > any_n:
            DEF[(pid, "contested")] += 1
            if b["any_allocated"]["blue"] < min(rem["blue"], any_n):
                DEF[(pid, "blue_open")] += 1
            if b["any_allocated"]["red"] > 0:
                DEF[(pid, "red_chosen")] += 1
    return out
p4.resolve_player_defense_and_wear = res


def play(args):
    n, idx, bonus, pool, ties, mode, w, sec_d, deep, seed0 = args
    P.update(bonus=bonus, pool=pool, ties=ties, w=w, deep=deep)
    e = sw.build_engine("V036", n, idx, seed0 + n * 100_000 + idx)
    sd = sec_d.get(n, 0) if isinstance(sec_d, dict) else sec_d
    for p in e.state.players:
        p.secrets += sd
    ids = [p.player_id for p in e.state.players]
    P["aware"] = set(ids) if mode == "all" else ({ids[idx % n]} if mode == "one" else set())
    if deep:
        for p in e.state.players:
            if p.player_id in P["aware"]:
                p.bot.research_focus_v036 = pr_focus(p.bot)
    DEF.clear(); TEL.clear(); RED_NUDGE.clear()
    r = e.run_game()
    wset = set(r.winner_ids or [])
    seats = []
    surv = [p for p in e.state.players if not p.is_patient_zero]
    ms_sorted = sorted(int(p.market_share or 0) for p in surv)
    for p in e.state.players:
        pid = p.player_id
        rk = next(x for x in r.rankings if x["player_id"] == pid)
        seats.append(dict(
            aware=pid in P["aware"], bot=p.bot.name, win=(1 / len(wset)) if pid in wset else 0.0, pz=p.is_patient_zero,
            fin=p.secrets, pre=TEL.get("pre", {}).get(pid, p.secrets), bonus=TEL.get("bonus", {}).get(pid, 0),
            ms=int(p.market_share or 0), ms_low=(not p.is_patient_zero and len(surv) > 1 and int(p.market_share or 0) == ms_sorted[0]),
            ms_top=(not p.is_patient_zero and len(surv) > 1 and int(p.market_share or 0) == ms_sorted[-1]),
            regained=rk["market_share_regained"], res_regain=rk["research_spent_regain"],
            buys=dict(rk["purchases_by_color"]),
            blue_owned=sum(1 for d in p.total_dice if d.color == DieColor.BLUE),
            red_owned=sum(1 for d in p.total_dice if d.color == DieColor.RED), nudges=RED_NUDGE[pid],
            pr_level=p.patent_level,
            **{k: DEF[(pid, k)] for k in ("blue_lost", "any_red", "any_blue", "any_green", "inc_red", "inc_blue",
                                           "inc_green", "blk_red", "blk_blue", "blk_green", "contested", "blue_open",
                                           "red_chosen")}))
    flip = (TEL.get("winner_pre") is not None and not r.is_total_wipeout and wset != TEL["winner_pre"])
    return dict(end=sw.three_way(r.end_reason.value), tw=r.is_total_wipeout, rounds=r.total_rounds, seats=seats,
                flip=flip, ms_ties=TEL.get("ms_ties", 0), nsurv=len(surv))


def run(n, G, bonus, pool="surv", ties="std", mode="none", w=(0.3, 0.6, 1.0, 1.0), sec_d=0, deep=False, seed0=42, workers=8):
    with Pool(workers) as pl:
        games = pl.map(play, [(n, i, bonus, pool, ties, mode, w, sec_d, deep, seed0) for i in range(G)], chunksize=25)
    ends = Counter(g["end"] for g in games)
    seats = [s for g in games for s in g["seats"]]
    def agg(ss):
        k = len(ss) or 1; S = lambda f: sum(s[f] for s in ss)
        anyt = S("any_red") + S("any_blue") + S("any_green") or 1
        sv = [s for s in ss if not s["pz"]]
        return dict(k=len(ss), win=S("win") / k, pz=S("pz") / k, fin=S("fin") / k,
                    pre_surv=sum(s["pre"] for s in sv) / max(1, len(sv)), bonus_surv=sum(s["bonus"] for s in sv) / max(1, len(sv)),
                    blue_lost=S("blue_lost") / k, regained=S("regained") / k, res_regain=S("res_regain") / k,
                    any_blue=S("any_blue") / anyt, any_red=S("any_red") / anyt,
                    rblk=S("blk_red") / max(1, S("inc_red")), bblk=S("blk_blue") / max(1, S("inc_blue")),
                    contested=S("contested") / k, blue_open=S("blue_open") / max(1, S("contested")),
                    red_chosen=S("red_chosen") / max(1, S("contested")),
                    buy_red=sum(s["buys"].get("red", 0) for s in ss) / k,
                    buy_blue=sum(s["buys"].get("blue", 0) for s in ss) / k,
                    pr=S("pr_level") / k, nudges=S("nudges") / k)
    low = [s for s in seats if s["ms_low"]]; top = [s for s in seats if s["ms_top"]]
    def wr_by(field, v):
        ss = [s for s in seats if (s[field] >= 2 if v == 2 else s[field] == v)]
        return sum(s["win"] for s in ss) / max(1, len(ss))
    bots = defaultdict(list)
    for s in seats: bots[s["bot"]].append(s["win"])
    return dict(
        n=n, G=G, bonus=bonus, pool=pool, ties=ties, mode=mode, w=w, sec_d=sec_d, deep=deep, seed0=seed0,
        ends={k: ends[k] / G for k in ("patient_zero", "singularity", "market_collapse")},
        tw=sum(g["tw"] for g in games) / G, rounds=St.mean(g["rounds"] for g in games),
        flip=sum(g["flip"] for g in games) / G,
        ms_tie_games=sum(1 for g in games if g["ms_ties"]) / G,
        multi_surv=sum(1 for g in games if g["nsurv"] > 1) / G,
        low_win=sum(s["win"] for s in low) / max(1, len(low)), top_win=sum(s["win"] for s in top) / max(1, len(top)),
        all=agg(seats), aware=agg([s for s in seats if s["aware"]]), naive=agg([s for s in seats if not s["aware"]]),
        wr_blue={v: wr_by("blue_owned", v) for v in (0, 1, 2)}, wr_red={v: wr_by("red_owned", v) for v in (0, 1, 2)},
        bots={b: sum(v) / len(v) for b, v in sorted(bots.items())},
    )


def fmt(r):
    a = r["all"]; e = r["ends"]
    s = (f"{r['n']}P bonus={'/'.join(map(str, r['bonus'])) if r['bonus'] else '-':9s} {r['pool']}/{r['ties']} {r['mode']:4s}{'+deep' if r['deep'] else ''} w={r['w'][0]}-{r['w'][2]} sec{r['sec_d'] if isinstance(r['sec_d'], int) else r['sec_d'].get(r['n'], 0):+d} seed{r['seed0']} | "
         f"PZ/Sing/Coll {e['patient_zero']:.0%}/{e['singularity']:.0%}/{e['market_collapse']:.0%} TW {r['tw']:.1%} rnds {r['rounds']:.2f} | "
         f"flip {r['flip']:.0%} MS-tie games {r['ms_tie_games']:.0%} | lowMS win {r['low_win']:.0%} topMS win {r['top_win']:.0%}\n"
         f"   all: survSec pre {a['pre_surv']:.2f} +bonus {a['bonus_surv']:.2f} | BlueLost {a['blue_lost']:.2f} regain {a['regained']:.2f} "
         f"| Any->Blue {a['any_blue']:.0%} Any->Red {a['any_red']:.0%} | blk R/B {a['rblk']:.0%}/{a['bblk']:.0%} "
         f"| contested {a['contested']:.2f}/seat: Blue left open {a['blue_open']:.0%}, Red chosen {a['red_chosen']:.0%} "
         f"| buys R/B {a['buy_red']:.2f}/{a['buy_blue']:.2f} PR lvl {a['pr']:.2f}\n"
         f"   win by Blue owned 0/1/2+ {'/'.join(f'{v:.0%}' for v in r['wr_blue'].values())}  Red owned 0/1/2+ {'/'.join(f'{v:.0%}' for v in r['wr_red'].values())}"
         f"  bots {' '.join(f'{b[:6]}={v:.0%}' for b, v in r['bots'].items())}")
    if r["mode"] == "one":
        x = r["aware"]; y = r["naive"]
        s += (f"\n   aware seat win {x['win']:.1%} (naive {y['win']:.1%}) PZ {x['pz']:.0%}/{y['pz']:.0%} "
              f"BlueLost {x['blue_lost']:.2f}/{y['blue_lost']:.2f} regain {x['regained']:.2f}/{y['regained']:.2f} "
              f"buys R {x['buy_red']:.2f}/{y['buy_red']:.2f} PR lvl {x['pr']:.2f}/{y['pr']:.2f} finSec {x['fin']:.2f}/{y['fin']:.2f}")
    return s


if __name__ == "__main__":
    import json
    G = int(sys.argv[1]); which = sys.argv[2] if len(sys.argv) > 2 else "main"
    out = []
    def go(*a, **kw):
        r = run(*a, **kw); out.append(r); print(fmt(r), flush=True)
    if which == "main":
        for n in (2, 3, 4):
            go(n, G, None)
            for b in ([5, 3, 2, 1], [3, 2, 1, 0], [2, 1, 0, 0]):
                go(n, G, b, mode="none"); go(n, G, b, mode="all"); go(n, G, b, mode="one")
    elif which == "variants":
        for n in (2, 3, 4):
            go(n, G, [5, 3, 2, 1], pool="all", mode="all")
            go(n, G, [5, 3, 2, 1], ties="share", mode="all")
            go(n, G, [5, 3, 2, 1], ties="share", mode="one")
            go(n, G, [3, 2, 1, 0], ties="share", mode="all")
            go(n, G, [5, 3, 2, 1], mode="all", w=(1.0, 1.0, 1.0, 1.0))
            go(n, G, [5, 3, 2, 1], mode="all", w=(0.15, 0.3, 0.5, 1.0))
            go(n, G, [5, 3, 2, 1], mode="all", sec_d=1)
            go(n, G, [3, 2, 1, 0], mode="all", sec_d=1)
            go(n, G, [3, 2, 1, 0], mode="one", sec_d=1)
            go(n, G, [2, 1, 0, 0] if n < 4 else [3, 2, 1, 1], mode="all", sec_d=1)
            go(n, G, [1, 0, 0, 0], mode="all")
            go(n, G, [1, 0, 0, 0], mode="one")
    elif which == "cands":
        LO = (0.15, 0.3, 0.5, 1.0)
        A = {2: [2, 0], 3: [2, 1, 0], 4: [2, 1, 0, 0]}
        for n in (2, 3, 4):
            go(n, G, None)
            go(n, G, [5, 3, 2, 1], mode="one", w=LO)
            go(n, G, [3, 2, 1, 0], mode="one", w=LO)
            for sd in (0, 1):
                go(n, G, A[n], ties="share", mode="all", sec_d=sd)
                go(n, G, A[n], ties="share", mode="all", w=LO, sec_d=sd)
            go(n, G, A[n], ties="share", mode="one")
            go(n, G, A[n], ties="share", mode="one", w=LO)
            go(n, G, A[n], ties="std", mode="all")
            go(n, G, A[n], ties="share", mode="none")
    elif which == "deep":
        A = {2: [2, 0], 3: [2, 1, 0], 4: [2, 1, 0, 0]}
        for n in (2, 3, 4):
            go(n, G, A[n], ties="share", mode="one", sec_d=1)
            go(n, G, A[n], ties="share", mode="one", sec_d=1, deep=True)
            go(n, G, A[n], ties="share", mode="all", sec_d=1)
            go(n, G, A[n], ties="share", mode="all", sec_d=1, deep=True)
    elif which == "prfirst":
        A = {2: [2, 0], 3: [2, 1, 0], 4: [2, 1, 0, 0]}
        for n in (2, 3, 4):
            go(n, G, A[n], ties="share", mode="one", sec_d=1, deep="pr_first")
            go(n, G, None, mode="one", sec_d=1, deep="pr_first")
    elif which == "tw2p":
        for b, sd in (([2, 0], 2), ([1, 0], 1), ([1, 0], 0), ([3, 0], 2)):
            go(2, G, b, ties="share", mode="all", sec_d=sd, deep=True)
            go(2, G, b, ties="share", mode="one", sec_d=sd, deep=True)
        go(2, G, None, sec_d=1)
    elif which == "fresh":
        A = {2: [2, 0], 3: [2, 1, 0], 4: [2, 1, 0, 0]}
        SD = {2: int(sys.argv[3]) if len(sys.argv) > 3 else 1, 3: 1, 4: 1}
        for n in (2, 3, 4):
            go(n, G, None, seed0=7000)
            go(n, G, A[n], ties="share", mode="none", sec_d=SD, seed0=7000)
            go(n, G, A[n], ties="share", mode="all", sec_d=SD, deep=True, seed0=7000)
            go(n, G, A[n], ties="share", mode="one", sec_d=SD, deep=True, seed0=7000)
    json.dump(out, open(os.path.join(ROOT, f"sim_results/v360_share_placement_{which}.json"), "w"), default=str)
