import sys, json, collections
sys.path.insert(0, "/home/mike/antigravity/rogue-agent")
from multiprocessing import Pool
import scripts.run_reference_bot_validation as V
from sim.config import GameConfig
from sim.bots import reference_search as rs
OUT = "/home/mike/antigravity/rogue-agent/sim_results/reference_bot/attribution"
_orig_bp = rs.build_portfolio
VARIANT = {"A": {"MarketShareDump"}, "B": {"PublicRelationsPush"}, "C": set(), "D11": {"MarketShareDump", "PublicRelationsPush"}}
CH = collections.Counter()
_os = rs.ReferenceSearchBot._search
def _search(self, hook, cands):
    i = _os(self, hook, cands); CH[f"{hook}|{cands[i][0]}"] += 1; CH[f"n|{hook}"] += 1; return i
rs.ReferenceSearchBot._search = _search

def play(task):
    cfg, port, var, P, seed = task
    drop = VARIANT[port]
    rs.build_portfolio = lambda bid: [m for m in _orig_bp(bid) if m[0] not in drop]
    V._install_hook(); CH.clear()
    cfgn = cfg
    if var == "nocollapse":
        orig = getattr(GameConfig, cfg); cfgn = "_tmp_" + cfg
        setattr(GameConfig, cfgn, staticmethod(lambda num_players: orig(num_players=num_players, market_collapse_enabled=False)))
    eng, sp = V.build_engine(cfgn, "ref1", P, seed)
    V._MAIN = eng
    V._ACC = {i: {k: 0 for k in ("blocked_red","blocked_blue","blocked_green","incoming_red","incoming_blue","incoming_green","secrets_lost_blue")} for i in range(P)}
    s = eng.state; traj = []
    while not s.game_over:
        eng.run_round()
        traj.append([[p.market_share, p.secrets] for p in s.players])
    res = eng.evaluate_end_game()
    rk = {r["player_id"]: r for r in res.rankings}
    seats = [dict(V._ACC[p.player_id], pr=int(p.patent_level), ms=p.market_share, lost_red=p.market_share_lost_red,
                  regained=p.market_share_regained, place=rk.get(p.player_id, {}).get("market_share_place"),
                  bonus=rk.get(p.player_id, {}).get("market_leader_bonus"), pz=bool(p.is_patient_zero)) for p in s.players]
    return dict(seed=seed, sp=sp[0], winners=list(res.winner_ids), end=res.end_reason.value, triggers=list(res.end_triggers),
                rounds=res.total_rounds, mc_round=s.market_collapse_round, mc_pids=list(s.market_collapse_pids or []),
                traj=traj, seats=seats, choices=dict(CH))

if __name__ == "__main__":
    cfg, port, var, n = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    tasks = [(cfg, port, var, 3, 42 + 300000 + i) for i in range(n)]
    with Pool(8) as pool: rows = pool.map(play, tasks, chunksize=2)
    json.dump(rows, open(f"{OUT}/{cfg}_ref1_{port}_{var}_3p_{n}.json", "w"))
    print(cfg, port, var, "done", flush=True)
