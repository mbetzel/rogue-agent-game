"""Scratchpad model of the §43.4 Red shared payout over v038b (monkeypatch; no repo edits)."""
import json, sys, os, argparse, collections as C
REPO = "/home/mike/antigravity/rogue-agent/.claude/worktrees/phase-49-execution-78bf2c"
sys.path.insert(0, REPO); sys.path.insert(0, REPO + "/scripts")
import run_v380_secret_faces_sweep as sw
from sim.engine import secret_faces as sf, end_game as eg
from sim.engine.market_share import market_share_places
from sim.config import DieColor, EndGameReason
from sim import entities as ent

OPT = {}
CUR = {}

def payout(state, tag):
    surv = {p.player_id: int(p.market_share or 0) for p in state.players if not p.is_patient_zero}
    if not surv: return
    places = market_share_places(surv)
    sec = OPT["sec"]; mon = OPT.get("money", [])
    for p in state.players:
        if p.player_id not in surv: continue
        i = places[p.player_id] - 1
        if i < len(sec) and sec[i]: p.gain_secrets(sec[i], "red_payout")
        if i < len(mon) and mon[i]: p.money += mon[i]
    CUR["payouts"].append(tag)

_bank = sf.bank
def bank(cfg, p, die):
    red = die.color == DieColor.RED and getattr(die, "secret_pending", False)
    y = _bank(cfg, p, die)
    if red and OPT.get("perceived") is not None:
        adj = OPT["owner"] - y
        if adj: p.gain_secrets(adj, "red_owner_adj")
    if red and CUR.get("state") is not None:
        st = CUR["state"]; CUR["counter"] += 1; CUR["trig"][p.player_id] += 1
        if CUR["counter"] % OPT["n"][st.config.num_players] == 0:
            CUR["fired_by"][p.player_id] += 1
            payout(st, "red")
    return y
sf.bank = bank

_eval = eg.evaluate_end_game
def evaluate(engine):
    s = engine.state
    allpz = all(p.is_patient_zero for p in s.players)
    CUR["red_pending_end"] = sum(1 for p in s.players for d in p.glitched_dice
                                 if d.color == DieColor.RED and getattr(d, "secret_pending", False))
    CUR["oth_pending_end"] = sum(1 for p in s.players for d in p.glitched_dice
                                 if d.color != DieColor.RED and getattr(d, "secret_pending", False))
    if OPT.get("end", True) and not allpz and s.end_reason != EndGameReason.MARKET_COLLAPSE:
        payout(s, "end")
    return _eval(engine)
eg.evaluate_end_game = evaluate

_mk = ent._create_colored_die_v038
def mk(color, *a, **k):
    d = _mk(color, *a, **k)
    if OPT.get("yellow_var") and color == DieColor.YELLOW:
        d.faces[2] = ent.Face(name="+$1 & +1 Market Share", money=1, market_share=1)
    return d
ent._create_colored_die_v038 = mk

_build = sw.build_engine
def build(*a, **k):
    e = _build(*a, **k)
    CUR.clear(); CUR.update(state=e.state, counter=0, trig=C.Counter(), fired_by=C.Counter(), payouts=[])
    return e
sw.build_engine = build

_play = sw.play
def play(task):
    r = _play(task)
    r["rp"] = {"payouts": CUR["payouts"], "counter": CUR["counter"], "trig": dict(CUR["trig"]),
               "fired_by": dict(CUR["fired_by"]), "red_pending_end": CUR.get("red_pending_end", 0),
               "oth_pending_end": CUR.get("oth_pending_end", 0)}
    return r

def worker(arg):
    opt, task = arg
    OPT.clear(); OPT.update(opt); OPT["n"] = {int(k): v for k, v in OPT["n"].items()}
    return play(task)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--opt", required=True); ap.add_argument("--players", type=int, nargs="+", default=[2, 3, 4])
    ap.add_argument("--games", type=int, default=600); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    OPT.update(json.loads(a.opt)); OPT["n"] = {int(k): v for k, v in OPT["n"].items()}
    ov = {"secret_yield_red_tiers": ((0, OPT["perceived"] if OPT.get("perceived") is not None else OPT["owner"]),), "market_leader_bonus_by_player_count": {},
          "version_share_payout": {}, "market_share_start_by_player_count": {2: 14, 3: 14, 4: 15}}
    if "set" in OPT: ov.update({k: ({int(a): b for a, b in v.items()} if isinstance(v, dict) else v) for k, v in OPT["set"].items()})
    from multiprocessing import Pool
    out = []
    for P in a.players:
        tasks = [("v038b", "mixed1", P, s, ov) for s in range(42, 42 + a.games)]
        with Pool(8) as pool: recs = pool.map(worker, [(json.loads(a.opt), t) for t in tasks], chunksize=8)
        summ = sw.summarise(recs, "v038b", "mixed1", P, {k: str(v) for k, v in ov.items()})
        summ["records"] = recs; out.append(summ)
    json.dump(out, open(a.out, "w"))
