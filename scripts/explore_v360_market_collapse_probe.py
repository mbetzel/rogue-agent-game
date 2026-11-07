"""v0.36 Market Collapse probe (exploration only, not rules code). See docs/explorations/2026_11_market_share_red_rework_plan.md.

Usage:
  PYTHONDONTWRITEBYTECODE=1 python3 scripts/explore_v360_market_collapse_probe.py --games 400 --starts 18,20,22 --regain 1 --pods 3,4 --secrets 9,10,11

Red ransom off, no Patent filings. Market Share starts at S; -1 per unblocked Red cube.
Market Share <= 0 after Phase 4 -> Final Round (no elimination).
Regain policy (optional): end of Phase 6, spend 2 research per +1 share, max +CAP per round, only if below start.
End reason = first trigger; same-round PZ + Collapse counted as Patient Zero."""
import os, sys, json, statistics as St, argparse
from collections import Counter, defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..")); sys.path.insert(0, HERE)
import run_v360_red_rebalance_sweep as sw
from sim.engine import state as st, core
from sim.engine import phase4_attack_resolution as p4
sw.CONFIGS["OFF"] = dict(red_ransom_per_cube=0)
st.PlayerState.file_patent = lambda self: False
P = dict(S=20, regain=False, cap=1, cost=2)
SHARE = {}; FLAG = {}
orig_res = sw._resolve_hook
def res_hook(engine, player, *a, **kw):
    out = orig_res(engine, player, *a, **kw)
    b = getattr(player, "last_defense_breakdown", None)
    if b: SHARE[player.player_id] -= b["unblocked"]["red"]
    return out
p4.resolve_player_defense_and_wear = res_hook
orig_chk = p4.check_end_triggers_after_attacks
def chk(engine):
    s = engine.state; before = s.end_reason
    orig_chk(engine)
    if s.game_over: return
    alive = [p for p in s.players if not p.is_patient_zero]
    if any(SHARE[p.player_id] <= 0 for p in alive):
        if not s.is_final_round:
            s.is_final_round = True; FLAG.setdefault("collapse", True)
        elif s.end_reason.value == "patient_zero" and before.value == "none":
            FLAG.setdefault("both", True)
p4.check_end_triggers_after_attacks = chk
orig_p6 = core.GameEngine._run_phase_6_operations
def p6(self):
    out = orig_p6(self)
    if P["regain"]:
        for p in self.state.players:
            if p.is_patient_zero: continue
            k = 0
            while k < P["cap"] and SHARE[p.player_id] < P["S"] and p.research_tokens >= P["cost"]:
                p.research_tokens -= P["cost"]; SHARE[p.player_id] += 1; k += 1
    return out
core.GameEngine._run_phase_6_operations = p6

def run(n, G, base=42):
    ends = Counter(); rounds = []; by_v3 = defaultdict(Counter); by_comp = defaultdict(Counter); by_wh = defaultdict(Counter)
    min_share = []
    for idx in range(G):
        eng = sw.build_engine("OFF", n, idx, base + n*100_000 + idx)
        SHARE.clear(); FLAG.clear()
        for p in eng.state.players: SHARE[p.player_id] = P["S"]
        res = eng.run_game(); rounds.append(res.total_rounds)
        r = res.end_reason.value
        if FLAG.get("collapse") and r in ("round_limit", "none", "patient_zero") and not any(p.is_patient_zero for p in eng.state.players):
            r = "market_collapse"
        elif r == "round_limit" and FLAG.get("collapse"):
            r = "market_collapse"
        if r == "total_wipeout": r = "patient_zero"  # group wipeouts with PZ for the 3-way split
        ends[r] += 1
        v3 = eng.state.version_deck[-1].directive_code; by_v3[v3][r] += 1
        for p in eng.state.players:
            if p.company: by_comp[p.company.code.value][r] += 1
            if p.white_hat: by_wh[getattr(p.white_hat, "code", getattr(p.white_hat, "name", "?"))][r] += 1
        min_share.append(min(SHARE.values()))
    return ends, St.mean(rounds), by_v3, by_comp, by_wh

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--games", type=int, default=300)
    ap.add_argument("--starts", default="14,17,20,23"); ap.add_argument("--regain", default="0,1")
    ap.add_argument("--detail", default=""); ap.add_argument("--pods", default="2,3,4"); ap.add_argument("--secrets", default="")
    a = ap.parse_args()
    for n in [int(x) for x in a.pods.split(",")]:
      for sec in ([int(x) for x in a.secrets.split(",")] if a.secrets else [None]):
        if sec is None: sw.CONFIGS["OFF"].pop("starting_secrets", None)
        else: sw.CONFIGS["OFF"]["starting_secrets"] = sec
        for rg in [int(x) for x in a.regain.split(",")]:
            for S in [int(x) for x in a.starts.split(",")]:
                P.update(S=S, regain=bool(rg))
                ends, rd, bv3, bc, bw = run(n, a.games)
                g = sum(ends.values())
                line = "  ".join(f"{k} {ends[k]/g:.0%}" for k in ("patient_zero", "singularity", "market_collapse"))
                other = {k: v for k, v in ends.items() if k not in ("patient_zero", "singularity", "market_collapse")}
                print(f"{n}P Secrets {sec or 8} start {S:2d} regain {'on ' if rg else 'off'}: rounds {rd:.2f}  {line}  {other if other else ''}", flush=True)
                if a.detail and f"{n}:{sec or 8}:{S}:{rg}" in a.detail.split(";"):
                    for name, d in (("v3.0 card", bv3), ("company (per seat)", bc), ("white hat (per seat)", bw)):
                        print(f"    by {name}:")
                        for k, c in sorted(d.items()):
                            t = sum(c.values())
                            print(f"      {k:22s} " + "  ".join(f"{e[:4]} {c[e]/t:.0%}" for e in ("patient_zero", "singularity", "market_collapse")) + f"  (n={t})")
