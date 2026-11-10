"""ref1 diagnostic on v038c: per-round state snapshot of the main engine + chosen portfolio label per searched decision."""
import sys, json, os
WT="/home/mike/antigravity/rogue-agent/.claude/worktrees/phase-49-execution-dcd489"
sys.path.insert(0, WT); os.chdir(WT)
from multiprocessing import Pool
import scripts.run_reference_bot_validation as m
from sim.bots import reference_search as rs
from sim.bots import market_share_policy as msp

_LOG=None
def feats(eng, pid):
    s=eng.state; me=s.players[pid]
    riv=[q for q in s.players if q is not me and not q.is_patient_zero]
    return dict(r=s.current_round, v=int(s.current_version_index), ct=int(s.corruption_track), cap=int(s.corruption_track_capacity),
        ms=me.market_share, rms=[q.market_share for q in riv], sec=me.secrets, rsec=[q.secrets for q in riv],
        rp=msp.red_pressure(s), rl=msp.estimated_rounds_left(s), money=me.money, res=me.research_tokens,
        pr=int(me.patent_level))
orig_searched=rs.ReferenceSearchBot._searched
orig_search=rs.ReferenceSearchBot._search
def _search(self, hook, cands):
    b=orig_search(self, hook, cands)
    if _LOG is not None and self.engine is _LOG["eng"]:
        _LOG["dec"].append(dict(feats(self.engine,self.bot_id), hook=hook, lab=cands[b][0], n=len(cands)))
    return b
rs.ReferenceSearchBot._search=_search

def play(task):
    global _LOG
    cfg, cell, P, seed = task
    eng, special = m.build_engine(cfg, cell, P, seed, True, None, "non_reference")
    sp=special[0]
    _LOG=dict(eng=eng, dec=[], rounds=[])
    while not eng.state.game_over:
        pre=feats(eng,sp)
        eng.run_round()
        _LOG["rounds"].append(dict(pre=pre, post_ms=[p.market_share for p in eng.state.players], post_sec=[p.secrets for p in eng.state.players]))
    res=eng.evaluate_end_game()
    s=eng.state
    out=dict(seed=seed, sp=sp, win=sp in res.winner_ids, nwin=len(res.winner_ids), end=res.end_reason.value,
        rounds=res.total_rounds, cpids=list(res.market_collapse_pids), cround=s.market_collapse_round,
        fms=[p.market_share for p in s.players], fsec=[p.secrets for p in s.players], pz=[p.is_patient_zero for p in s.players],
        names=[p.bot.name for p in s.players], dec=_LOG["dec"], rlog=_LOG["rounds"])
    _LOG=None
    return out
if __name__=="__main__":
    P=int(sys.argv[1]); n=int(sys.argv[2]); outp=sys.argv[3]
    tasks=[("v038c","ref1",P,42+P*100000+i) for i in range(n)]
    with Pool(8) as p: rows=p.map(play,tasks,chunksize=2)
    json.dump(rows,open(outp,"w"))
    print(P,len(rows))
