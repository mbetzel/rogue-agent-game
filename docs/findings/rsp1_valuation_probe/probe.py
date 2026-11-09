import sys, json
sys.path.insert(0, '/home/mike/antigravity/rogue-agent/.claude/worktrees/phase-49-execution-dcd489')
import scripts.run_v380_secret_faces_sweep as S
from sim.bots import market_share_policy as M
CC = M.CubeColor
CAND = sys.argv[1]; MODE = sys.argv[2] if len(sys.argv) > 2 else ''
H2H = MODE in ('h2h','vs','ctl')
CAND0 = CAND
import os; GAMMA = float(os.environ.get('G','0.85'))
orig_active = M.payout_active
orig_mbv = M._marginal_block_value_v037
AWARE = {'seat': None}

def active(player, state, pol):
    if CAND == 'off': return False
    if MODE == 'ctl': return False
    if MODE == 'h2h' and AWARE['seat'] is not None and player.player_id != AWARE['seat']: return False
    return orig_active(player, state, pol)
M.payout_active = active

def p_any(state):
    miss = 1.0
    for q in state.players: miss *= 1.0 - M.p_red_bank(q, state)
    return 1.0 - miss

def erp(state):
    if not state.config.is_red_secret_payout: return 0.0
    p = p_any(state); R = M.estimated_rounds_left(state)
    if CAND in ('A', 'D'):
        e_in = sum(GAMMA**t for t in range(R)) * p; disc = GAMMA**R
    else:
        e_in = R * p; disc = 1.0
    p_end = 0.0
    if state.config.red_secret_payout_at_end:
        low = any(int(q.market_share or 0) <= 2 for q in state.players if not q.is_patient_zero)
        p_end = (0.5 if (low and state.config.market_collapse_enabled) else 1.0) * disc
    return e_in + p_end
M.expected_red_payouts_remaining = erp

def mbv(color, rem, player, state, attack, pol):
    global CAND
    if MODE == 'vs': CAND = CAND0 if player.player_id == AWARE['seat'] else 'base'
    v = orig_mbv(color, rem, player, state, attack, pol)
    if color != CC.RED or CAND in ('base', 'off', 'A') or not active(player, state, pol) or v == float('-inf'):
        return v
    share = int(player.market_share or 0); r = int(rem.get(color, 0))
    rivals = list(M.estimated_rival_shares(player, state, attack.get(CC.RED, 0)).values())
    sched = state.config.red_secret_payout_schedule(len(state.players))
    d = M.expected_payout_value(max(0, share-r+1), rivals, sched) - M.expected_payout_value(max(0, share-r), rivals, sched)
    full = pol.blue_value * d * erp(state)
    v -= full
    if CAND in ('B', 'D'):
        cost = int(state.config.share_regain_cost_by_level.get(player.patent_level, 2))
        new = min(full, pol.blue_value * d * p_any(state) + cost)
    elif CAND == 'C':
        bp = int(state.staging_cup.get(CC.BLUE, 0)) + int(state.tower.stuck_cubes.get(CC.BLUE, 0))
        w = min(1.0, max(0.0, (player.secrets - bp) / 3.0))
        new = full * w
    return v + new
M._marginal_block_value_v037 = mbv
orig_ur = M.urgent_regain
def ur(player, state, pol, cap):
    global CAND
    if MODE == 'vs': CAND = CAND0 if player.player_id == AWARE['seat'] else 'base'
    return orig_ur(player, state, pol, cap)
M.urgent_regain = ur

orig_play = S.play
def play(task):
    _, _, P, seed, _ = task
    AWARE['seat'] = (seed + 1) % P if H2H else None
    rec = orig_play(task)
    if H2H: rec['aware_seat'] = AWARE['seat']
    return rec
S.play = play
if __name__=='__main__':
  import multiprocessing as mp; mp.set_start_method('fork')

def main():
  out = {}
  for P in (2, 3, 4):
    recs = S.play_all('v038c', 'mixed1', P, int(os.environ.get('N', 1200 if H2H else 400)), {}, 0, 8)
    s = S.summarise(recs, 'v038c', 'mixed1', P, {})
    row = {k: s[k] for k in ('endings', 'avg_rounds', 'win_rate_by_company_color', 'win_rate_by_archetype', 'win_rate_by_path', 'rsp1')}
    if H2H:
        row['aware_seat_win'] = round(sum(g['seats'][g['aware_seat']]['win'] for g in recs)/len(recs), 4)
        row['fair'] = round(1/P, 4)
    out[P] = row
  print(json.dumps({CAND0 + MODE: out}))

if __name__=='__main__': main()
