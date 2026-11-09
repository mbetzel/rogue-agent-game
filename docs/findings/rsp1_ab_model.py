import json, sys, collections as C
REPO = "/home/mike/antigravity/rogue-agent/.claude/worktrees/phase-49-execution-dcd489"
sys.path.insert(0, REPO); sys.path.insert(0, REPO + "/scripts")
import run_v380_secret_faces_sweep as sw
from sim.engine import secret_faces as sf, end_game as eg, phase5_pipeline_shift as p5
from sim.engine.market_share import market_share_places
from sim.config import DieColor, EndGameReason
from sim import entities as ent
SEC = (3, 1, 0, 0); MODE = {"m": "A"}; CUR = {}

def payout(state, tag):
    surv = {p.player_id: int(p.market_share or 0) for p in state.players if not p.is_patient_zero}
    if not surv: return
    pl = market_share_places(surv); g = {}
    for p in state.players:
        if p.player_id in surv:
            k = SEC[pl[p.player_id] - 1] if pl[p.player_id] - 1 < len(SEC) else 0
            if k: p.gain_secrets(k, "red_payout")
            g[p.player_id] = k
    CUR["payouts"].append(tag); CUR["gains"].append((tag, g))

_bank = sf.bank
def bank(cfg, p, die):
    red = die.color == DieColor.RED and getattr(die, "secret_pending", False)
    y = _bank(cfg, p, die)
    if red and CUR.get("state") is not None:
        CUR["banks"] += 1; CUR["rb"] += 1; CUR["trig"][p.player_id] += 1
        if MODE["m"] == "A": payout(CUR["state"], "red")
    return y
sf.bank = bank

_shift = p5.execute_pipeline_shift
def shift(engine):
    r = _shift(engine)
    if MODE["m"] == "B" and CUR["rb"] > 0: payout(engine.state, "red")
    CUR["round_banks"].append(CUR["rb"]); CUR["rb"] = 0
    return r
p5.execute_pipeline_shift = shift

_tri = p5.conveyor_triage_v038
def tri(engine, player):
    b = player.bot; orig = b.choose_triage_order
    b.choose_triage_order = lambda pl, dice, st: list(dice)  # oldest first (append order)
    try: return _tri(engine, player)
    finally: b.choose_triage_order = orig
p5.conveyor_triage_v038 = tri

_eval = eg.evaluate_end_game
def evaluate(engine):
    s = engine.state
    if CUR["rb"]: CUR["round_banks"].append(CUR["rb"]); CUR["rb"] = 0  # game ended before Phase 5
    if not all(p.is_patient_zero for p in s.players) and s.end_reason != EndGameReason.MARKET_COLLAPSE:
        payout(s, "end")
    return _eval(engine)
eg.evaluate_end_game = evaluate

_mk = ent._create_colored_die_v038
def mk(color, *a, **k):
    d = _mk(color, *a, **k)
    if color == DieColor.YELLOW:
        assert d.faces[2].name == "+$3", d.faces[2].name
        d.faces[2] = ent.Face(name="+$1 & +1 Market Share", money=1, market_share=1)
    return d
ent._create_colored_die_v038 = mk

_build = sw.build_engine
def build(*a, **k):
    e = _build(*a, **k)
    CUR.clear(); CUR.update(state=e.state, banks=0, rb=0, trig=C.Counter(), payouts=[], gains=[], round_banks=[])
    return e
sw.build_engine = build

def worker(arg):
    m, task = arg; MODE["m"] = m
    r = sw.play(task)
    r["rp"] = {k: (dict(v) if isinstance(v, C.Counter) else v) for k, v in CUR.items() if k != "state"}
    return r

if __name__ == "__main__":
    from multiprocessing import Pool
    G = int(sys.argv[1]); out = {}
    ov = {"secret_yield_red_tiers": ((0, 1),), "market_leader_bonus_by_player_count": {}, "version_share_payout": {},
          "market_share_start_by_player_count": {2: 16, 3: 16, 4: 17}, "starting_secrets_by_player_count": {2: 3, 3: 4, 4: 4}}
    for m in "AB":
        for P in (2, 3, 4):
            tasks = [("v038b", "mixed1", P, s, ov) for s in range(42, 42 + G)]
            with Pool(8) as pool: recs = pool.map(worker, [(m, t) for t in tasks], chunksize=8)
            sm = sw.summarise(recs, "v038b", "mixed1", P, {k: str(v) for k, v in ov.items()})
            rb = [x for g in recs for x in g["rp"]["round_banks"]]
            sm["x"] = {"rounds_ge2_red": sum(x >= 2 for x in rb) / sum(g["rounds"] for g in recs),
                       "rounds_ge1_red": sum(x >= 1 for x in rb) / sum(g["rounds"] for g in recs),
                       "payouts_pg": sum(len(g["rp"]["payouts"]) for g in recs) / G,
                       "inround_payouts_pg": sum(g["rp"]["payouts"].count("red") for g in recs) / G,
                       "red_banks_pg": sum(g["rp"]["banks"] for g in recs) / G,
                       "payout_secrets_per_seat": sum(sum(gg.values()) for g in recs for _, gg in g["rp"]["gains"]) / (G * P)}
            out[f"{m}{P}"] = sm
            print(m, P, sm["x"], sm["endings"], sm["avg_rounds"], flush=True)
    json.dump(out, open("rsp1ab_out.json", "w"))
