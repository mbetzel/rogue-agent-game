"""Exploration probe (not rules code): Blue-defense pressure & Secret economy under v0.36 baseline."""
import os, sys, statistics as St
from collections import Counter, defaultdict
ROOT = "/home/mike/antigravity/rogue-agent"
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "scripts"))
import run_v360_market_share_sweep as sw
from sim.engine import phase4_attack_resolution as p4, phase2_compiler as p2

T = defaultdict(Counter)   # per pod totals
CUR = {}                   # per-player per-game accumulators
orig = p4.resolve_player_defense_and_wear
def hook(engine, player, *a, **kw):
    s0 = player.secrets
    out = orig(engine, player, *a, **kw)
    b = getattr(player, "last_defense_breakdown", None)
    c = CUR[player.player_id]
    if b:
        for col in ("red", "blue", "green"):
            c["att_" + col] += b["effective_attacks"][col]
            c["unb_" + col] += b["unblocked"][col]
            c["any_" + col] += b["any_allocated"][col]
        c["blue_secret_loss"] += max(0, s0 - player.secrets)
        anyn = b["color_shields"]["any"]
        rem = {k: b["effective_attacks"][k] - (b["color_shields"][k] if k in b["color_shields"] else 0) for k in ("red", "blue", "green")}
        rem = {k: max(0, v) for k, v in rem.items()}
        live = [k for k, v in rem.items() if v > 0]
        c["attack_rounds"] += 1
        if anyn > 0 and len(live) >= 2 and sum(rem.values()) > anyn:
            c["contested"] += 1
            if rem["blue"] > 0:
                c["contested_blue"] += 1
                if b["any_allocated"]["blue"] == min(rem["blue"], anyn):
                    c["contested_blue_first"] += 1
        if b["unblocked"]["blue"] > 0:
            c["rounds_blue_hit"] += 1
    return out
p4.resolve_player_defense_and_wear = hook

def run(n, G, base=42):
    rows = []; ends = Counter()
    for idx in range(G):
        eng = sw.build_engine("V036", n, idx, base + n * 100_000 + idx)
        CUR.clear()
        for p in eng.state.players:
            CUR[p.player_id] = Counter(start=p.secrets)
        res = eng.run_game(); ends[res.end_reason.value] += 1
        for p in eng.state.players:
            c = CUR[p.player_id]
            c["final"] = p.secrets
            c["pz"] = int(p.is_patient_zero)
            # gains = final - start + all losses; losses = blue + corruption (approx: residual)
            rows.append(c)
    return rows, ends

if __name__ == "__main__":
    G = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    for n in (2, 3, 4):
        rows, ends = run(n, G)
        S = lambda k: sum(r[k] for r in rows) / len(rows)
        print(f"\n=== {n}P  ({G} games, {len(rows)} seats)  ends={dict(ends)}")
        for col in ("red", "blue", "green"):
            a, u = S("att_" + col), S("unb_" + col)
            print(f"  {col:5s}: attacks/seat {a:5.2f}  unblocked {u:5.2f}  block rate {1-u/a if a else 0:5.1%}  Any-shields spent {S('any_'+col):4.2f}")
        tot_any = S("any_red") + S("any_blue") + S("any_green")
        print(f"  Any-shield share -> blue {S('any_blue')/tot_any:5.1%}  red {S('any_red')/tot_any:5.1%}  green {S('any_green')/tot_any:5.1%}")
        ar = S("attack_rounds"); con = S("contested")
        print(f"  contested Any-split rounds: {con:4.2f}/seat of {ar:4.2f} attack rounds ({con/ar:4.1%}); "
              f"Blue live in {S('contested_blue')/con if con else 0:4.1%} of those; Blue-first fill {S('contested_blue_first')/max(1e-9,S('contested_blue')):4.1%}")
        start = S("start"); fin = S("final"); bl = S("blue_secret_loss")
        print(f"  Secrets: start {start:4.2f} final {fin:4.2f}  Blue loss {bl:4.2f}  "
              f"other net (gains - corruption) {fin - start + bl:+4.2f}")
        hit = [r["rounds_blue_hit"] for r in rows]
        print(f"  rounds with Blue damage per seat: mean {St.mean(hit):4.2f}  share of seats never hit by Blue {sum(h==0 for h in hit)/len(hit):4.1%}")
        pzb = [r for r in rows if r["pz"]]
        if pzb:
            print(f"  Patient Zero seats {len(pzb)/len(rows):4.1%}; their Blue loss {sum(r['blue_secret_loss'] for r in pzb)/len(pzb):4.2f} vs survivors "
                  f"{sum(r['blue_secret_loss'] for r in rows if not r['pz'])/max(1,len(rows)-len(pzb)):4.2f}")
