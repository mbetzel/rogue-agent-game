import sys, json, os
sys.path.insert(0, os.getcwd())
from multiprocessing import Pool
import scripts.run_reference_bot_validation as m
from sim.config import GameConfig, PrPushParams
def _mk(cfg_name, players, pr_push=False, pr_params=None, pr_scope="all"):
    kw = dict(num_players=players, bot_pr_push=bool(pr_push), red_secret_owner_yield=2)
    if pr_params: kw["bot_pr_push_params"] = PrPushParams(**pr_params)
    if pr_scope != "all": kw["bot_pr_push_scope"] = pr_scope
    return getattr(GameConfig, cfg_name)(**kw)
m.make_config = _mk
def play(task):
    cfg, cell, P, seed, pp, ppar, scope = task
    eng, special = m.build_engine(cfg, cell, P, seed, pp, ppar, scope)
    res = eng.run_game()
    rk = {r["player_id"]: r for r in res.rankings}
    sp = special[0]
    return dict(seed=seed, rounds=res.total_rounds, pending=getattr(res,"red_pending_at_end",0),
        wait_rounds=sum(r.get("red_processing_wait_rounds",0) for r in rk.values()),
        wait_count=sum(r.get("red_processing_wait_count",0) for r in rk.values()),
        ref_wait_rounds=rk[sp].get("red_processing_wait_rounds",0), ref_wait_count=rk[sp].get("red_processing_wait_count",0),
        payouts=getattr(res,"red_secret_payouts_fired",0), end_payout=bool(getattr(res,"red_secret_payout_end_fired",False)),
        multi=getattr(res,"rounds_with_multi_red_banks",0))
if __name__=="__main__":
    P=int(sys.argv[1]); out=sys.argv[2]
    tasks=[("v038c","ref1",P,42+P*100000+i,True,None,"non_reference") for i in range(1200)]
    with Pool(8) as p: rows=p.map(play,tasks,chunksize=1)
    json.dump(rows,open(out,"w"))
    print(P,len(rows))
