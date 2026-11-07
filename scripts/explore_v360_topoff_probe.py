"""Exploration probe (not rules code): L4 top-off rule + a top-off-aware bot behaviour.

Rule: once per round in Phase 6, a player with any track at L4 may pay COST research for +1 Corporate Secret.
Aware seats:
  * Phase 6: top off BEFORE other research spending (reserve COST each round once at L4).
  * Any-shield split: a Blue cube they can repair this round (the 1st unblocked Blue, when they hold or will hold
    COST research and have an L4 track) is valued at its repair price, COST * RES_UNIT, not as a permanent Secret.
    Red/Green values unchanged (Red base already ~ its 2-research regain price). Lethal Blue is still protected.
Naive seats: convert leftover research only, value Blue as permanent (default bot).
"""
import os, sys, statistics as St
from collections import Counter
ROOT = "/home/mike/antigravity/rogue-agent"
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "scripts"))
import run_v360_market_share_sweep as sw
from sim.engine import core, phase4_attack_resolution as p4
from sim.bots import market_share_policy as msp, base
from sim.entities import CubeColor

P = dict(cost=3, aware=set(), res_unit=0.5)
USES = Counter(); BLUE = Counter(); AG = Counter()

def can_top(p):
    return max(p.defense_level, p.triage_level, p.release_level, p.patent_level) >= 4

def _conv(eng, which):
    for p in eng.state.players:
        if p.is_patient_zero or (p.player_id in P["aware"]) != which: continue
        if P["cost"] and can_top(p) and p.research_tokens >= P["cost"]:
            p.research_tokens -= P["cost"]; p.secrets += 1; USES[p.player_id] += 1

orig_p6 = core.GameEngine._run_phase_6_operations
def p6(self):
    _conv(self, True)            # aware: top off first
    out = orig_p6(self)
    _conv(self, False)           # naive: leftovers
    return out
core.GameEngine._run_phase_6_operations = p6

orig_mbv = msp.marginal_block_value
def mbv(color, rem, player, state, attack, pol):
    v = orig_mbv(color, rem, player, state, attack, pol)
    if (color == CubeColor.BLUE and player.player_id in P["aware"] and P["cost"] and can_top(player)
            and v < pol.blue_lethal_value and int(rem.get(color, 0)) == 1
            and player.research_tokens + 1 >= P["cost"] and not getattr(state, "is_final_round", False)):
        return P["cost"] * P["res_unit"]   # repairable: price in research
    return v
msp.marginal_block_value = mbv

orig_res = p4.resolve_player_defense_and_wear
def res(engine, player, *a, **kw):
    s0 = player.secrets; out = orig_res(engine, player, *a, **kw)
    BLUE[player.player_id] += max(0, s0 - player.secrets)
    b = getattr(player, "last_defense_breakdown", None)
    if b:
        c = (player.player_id in P["aware"])
        cs = b["color_shields"]; any_n = cs["any"]
        rem = {k: max(0, b["effective_attacks"][k] - cs.get(k, 0)) for k in ("red", "blue", "green")}
        AG[(c, "any_blue")] += b["any_allocated"]["blue"]; AG[(c, "any_all")] += sum(b["any_allocated"].values())
        if any_n > 0 and rem["blue"] > 0 and sum(v > 0 for v in rem.values()) >= 2 and sum(rem.values()) > any_n:
            AG[(c, "contested")] += 1
            if b["any_allocated"]["blue"] < min(rem["blue"], any_n): AG[(c, "took_blue")] += 1
    return out
p4.resolve_player_defense_and_wear = res

def run(n, G, cost, mode):
    P["cost"] = cost; AG.clear()
    ends = Counter(); rounds = []; S = {True: Counter(), False: Counter()}
    for idx in range(G):
        e = sw.build_engine("V036", n, idx, 42 + n * 100_000 + idx); USES.clear(); BLUE.clear()
        ids = [p.player_id for p in e.state.players]
        P["aware"] = set(ids) if mode == "all" else ({ids[idx % n]} if mode == "one" else set())
        r = e.run_game(); rounds.append(r.total_rounds); ends[sw.three_way(r.end_reason.value)] += 1
        w = set(r.winner_ids or [])
        for p in e.state.players:
            a = p.player_id in P["aware"]; s = S[a]
            s["seats"] += 1; s["fin"] += p.secrets; s["blue"] += BLUE[p.player_id]; s["use"] += USES[p.player_id]
            s["win"] += (1 / len(w)) if p.player_id in w else 0; s["pz"] += p.is_patient_zero
    e3 = "/".join(f"{ends[k]/G:.0%}" for k in ("patient_zero", "singularity", "market_collapse"))
    out = f"{n}P {mode:4s} cost={cost or '-'} | PZ/Sing/Coll {e3} | rnds {St.mean(rounds):.2f}"
    for a in (True, False):
        s = S[a]
        if not s["seats"]: continue
        k = s["seats"]; con = AG[(a, "contested")]
        out += (f"\n     {'aware' if a else 'naive'}: win {s['win']/k:.1%} PZ {s['pz']/k:.0%} finSec {s['fin']/k:.2f} Blue lost {s['blue']/k:.2f}"
                f" top-offs {s['use']/k:.2f} | Any->Blue {AG[(a,'any_blue')]/max(1,AG[(a,'any_all')]):.0%}"
                f" | contested rounds w/ Blue left open on purpose {AG[(a,'took_blue')]/max(1,con):.0%} ({con/k:.2f}/seat)")
    return out

if __name__ == "__main__":
    G = int(sys.argv[1])
    for n in (2, 3, 4):
        print(run(n, G, None, "none"), flush=True)
        print(run(n, G, 3, "all"), flush=True)
        print(run(n, G, 3, "one"), flush=True)
