"""Collapse-dash monkeypatch probe. env DASH = JSON {seats:'special'|'all'|'none', lead:int, minv:int, maxms:int, minsec:int}"""
import sys, json, os
WT="/home/mike/antigravity/rogue-agent/.claude/worktrees/phase-49-execution-dcd489"
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, WT); os.chdir(WT)
from multiprocessing import Pool
import scripts.run_reference_bot_validation as m
from sim.bots import pr_push_policy as prp, market_share_policy as msp, base as basemod
P_=json.loads(os.environ.get("DASH","{}"))
SEATS=set()
STATS={"dash_dec":0}
def dash(bot, player, state, ctx=None):
    if player.player_id not in SEATS or player.market_share is None or player.is_patient_zero: return False
    if getattr(state,"pr_push_rollout",False) or getattr(bot,"pr_push_reference_owned",False): return False
    if not msp.is_aware(state): return False
    riv=[q for q in state.players if q is not player and not q.is_patient_zero]
    if not riv: return False
    sl=int(player.secrets)-max(int(q.secrets) for q in riv)
    if sl < P_.get("lead",2): return False
    if P_.get("mode")=="fin":
        rp=msp.red_pressure(state) if ctx is None else ctx
        return int(player.market_share) <= rp + P_.get("margin",0)
    if int(state.current_version_index) < P_.get("minv",0): return False
    if int(player.market_share) > P_.get("maxms",99): return False
    if int(player.secrets) < P_.get("minsec",0): return False
    if msp.estimated_rounds_left(state) > P_.get("maxrl",99): return False
    return True
SUP=[False]
_ow=prp.window
def window(bot, player, state, phase4=False, hook=""):
    if not SUP[0] and dash(bot, player, state):
        STATS["dash_dec"]+=1; return prp.DUMP
    return _ow(bot, player, state, phase4, hook)
prp.window=window
from sim.bots import adaptive_balanced as abm
_oab=abm.AdaptiveBalancedBot.choose_any_shield_allocation
SUP=[False]
def abcas(self, player_state, remaining, available_any, game_state, attack):
    if P_.get("mode")=="fin":
        if dash(self, player_state, game_state, int(remaining.get(prp.CubeColor.RED,0))):
            STATS["dash_dec"]+=1
            return prp.windowed_any_shield_allocation(prp.DUMP, player_state, remaining, available_any, game_state, attack, self)
        SUP[0]=True
        try: return _oab(self, player_state, remaining, available_any, game_state, attack)
        finally: SUP[0]=False
    return _oab(self, player_state, remaining, available_any, game_state, attack)
abm.AdaptiveBalancedBot.choose_any_shield_allocation=abcas
_oa=basemod.BaseBot.choose_any_shield_allocation
def cas(self, player_state, remaining, available_any, game_state, attack):
    if dash(self, player_state, game_state, int(remaining.get(prp.CubeColor.RED,0)) if P_.get("mode")=="fin" else None):
        STATS["dash_dec"]+=1
        return prp.windowed_any_shield_allocation(prp.DUMP, player_state, remaining, available_any, game_state, attack, self)
    return _oa(self, player_state, remaining, available_any, game_state, attack)
basemod.BaseBot.choose_any_shield_allocation=cas
_om=msp.apply_market_share_policy
def amsp(bot, plan, player, state):
    plan=_om(bot, plan, player, state)
    if dash(bot, player, state): plan.use_r2_share=0
    return plan
msp.apply_market_share_policy=amsp
import sim.engine as E
for modname in list(sys.modules):
    mod=sys.modules[modname]
    if modname.startswith("sim.") and getattr(mod,"apply_market_share_policy",None) is _om: mod.apply_market_share_policy=amsp

_omc=m.make_config
def make_config(cfg_name, players, pr_push=False, pr_params=None, pr_scope="all"):
    from sim.config import GameConfig
    kw=dict(num_players=players, bot_pr_push=bool(pr_push))
    if pr_scope!="all": kw["bot_pr_push_scope"]=pr_scope
    kw.update(json.loads(os.environ.get("CFG","{}")))
    return getattr(GameConfig,cfg_name)(**kw)
m.make_config=make_config
def play(task):
    cell,P,seed=task
    if cell=="sweep_ref1":
        import scripts.run_v380_secret_faces_sweep as sw
        from sim.bots.reference_search import ReferenceSearchBot, ReferenceSearchEngine
        e0=sw.build_engine("v038c","mixed1",P,seed,dict(json.loads(os.environ.get("CFG","{}")), bot_pr_push=True, bot_pr_push_scope="non_reference"))
        sp=seed%P; bots=[p.bot for p in e0.state.players]; bots[sp]=ReferenceSearchBot(sp,seed)
        import random
        from sim.entities import get_random_companies, get_random_setup, get_random_white_hats
        rng=random.Random(seed); _b=list(range(P)); rng.shuffle(_b)
        variants, vd = get_random_setup(rng, profile="STANDARD"); co=get_random_companies(P, rng); wh=get_random_white_hats(P, rng)
        eng=ReferenceSearchEngine(config=e0.config, bots=bots, seed=seed, variant_cards=variants, version_deck=vd, companies=co, white_hats=wh); special=[sp]
    elif cell=="sweep_mixed1":
        import scripts.run_v380_secret_faces_sweep as sw
        eng=sw.build_engine("v038c","mixed1",P,seed,json.loads(os.environ.get("CFG","{}"))); special=[seed%P]
    else:
        eng, special = m.build_engine("v038c", cell, P, seed, os.environ.get("PRPUSH","1")=="1", None, "non_reference")
    s=P_.get("seats","special"); sp=special[0]
    SEATS.clear()
    if s=="special": SEATS.add(sp)
    elif s=="all": SEATS.update(range(P))
    elif s=="others": SEATS.update(i for i in range(P) if i!=sp)
    STATS["dash_dec"]=0
    res=eng.run_game(); st=eng.state
    return dict(seed=seed, sp=sp, w=list(res.winner_ids), end=res.end_reason.value, rounds=res.total_rounds,
        cpids=list(res.market_collapse_pids), pz=[p.is_patient_zero for p in st.players], names=[p.bot.name for p in st.players],
        tw=all(p.is_patient_zero for p in st.players), dd=STATS["dash_dec"])
if __name__=="__main__":
    cell=sys.argv[1]; P=int(sys.argv[2]); n=int(sys.argv[3]); out=sys.argv[4]
    with Pool(8) as p: rows=p.map(play,[(cell,P,42+i) for i in range(n)],chunksize=4)
    json.dump(dict(cfg=P_,rows=rows),open(os.path.join(HERE,out),"w")); print(out,len(rows))
