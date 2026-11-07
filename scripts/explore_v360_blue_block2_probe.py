"""Exploration probe (not rules code): idea 2 — stronger Blue (Firewall) die faces.
  A:  Face 1 Block 1 Blue -> Block 2 Blue
  C:  Face 1 -> Block 2 Blue, and Face 4 (Block 1 Blue / +1 research) -> Block 2 Blue (no research option)
Bots are unchanged (their purchase logic does not know Blue got stronger)."""
import os, sys, statistics as St
from collections import Counter
ROOT = "/home/mike/antigravity/rogue-agent"
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "scripts"))
import run_v360_market_share_sweep as sw
from sim import entities as E
from sim.engine import phase4_attack_resolution as p4, phase6_operations as p6m, research_tracks as rt

MODE = {"m": None}
orig_create = E.create_colored_die
def create(*a, **kw):
    d = orig_create(*a, **kw)
    if d.color == E.DieColor.BLUE and MODE["m"]:
        f = d.faces
        f[0] = E.Face(name="Block 2 Blue", block_amount=2, shield_color=E.ShieldColor.BLUE)
        if MODE["m"] == "C":
            f[3] = E.Face(name="Block 2 Blue", block_amount=2, shield_color=E.ShieldColor.BLUE)
    return d
for mod in (E, p6m, rt):
    mod.create_colored_die = create

AG = Counter()
orig_res = p4.resolve_player_defense_and_wear
def res(engine, player, *a, **kw):
    s0 = player.secrets; out = orig_res(engine, player, *a, **kw)
    AG["blue_loss"] += max(0, s0 - player.secrets)
    b = getattr(player, "last_defense_breakdown", None)
    if b:
        cs = b["color_shields"]; any_n = cs["any"]
        for k in ("red", "blue", "green"):
            AG["unb_" + k] += b["unblocked"][k]; AG["any_" + k] += b["any_allocated"][k]
        rem = {k: max(0, b["effective_attacks"][k] - cs.get(k, 0)) for k in ("red", "blue", "green")}
        AG["rounds"] += 1
        if any_n > 0 and sum(v > 0 for v in rem.values()) >= 2 and sum(rem.values()) > any_n:
            AG["contested"] += 1
            AG["contested_blue"] += rem["blue"] > 0
        AG["blue_covered_by_color"] += (b["effective_attacks"]["blue"] > 0 and rem["blue"] == 0)
        AG["blue_rounds"] += b["effective_attacks"]["blue"] > 0
    return out
p4.resolve_player_defense_and_wear = res

def run(n, G, m):
    MODE["m"] = m; AG.clear()
    ends = Counter(); rounds = []; seats = 0; fin = 0; blue_own = []; win_by = Counter(); cnt_by = Counter()
    for idx in range(G):
        e = sw.build_engine("V036", n, idx, 42 + n * 100_000 + idx)
        r = e.run_game(); rounds.append(r.total_rounds); ends[sw.three_way(r.end_reason.value)] += 1
        w = set(r.winner_ids or [])
        for p in e.state.players:
            seats += 1; fin += p.secrets
            nb = sum(1 for d in p.colored_dice if d.color == E.DieColor.BLUE); blue_own.append(nb)
            k = min(nb, 2); cnt_by[k] += 1; win_by[k] += (1 / len(w)) if p.player_id in w else 0
    e3 = "/".join(f"{ends[k]/G:.0%}" for k in ("patient_zero", "singularity", "market_collapse"))
    tot_any = AG["any_red"] + AG["any_blue"] + AG["any_green"]
    s = lambda k: AG[k] / seats
    out = (f"{n}P {m or 'base'} | PZ/Sing/Coll {e3} | rnds {St.mean(rounds):.2f} | finSec {fin/seats:.2f} | Blue lost {s('blue_loss'):.2f}"
           f" | unblocked R/G {s('unb_red'):.1f}/{s('unb_green'):.1f} | Any->B/R/G {AG['any_blue']/tot_any:.0%}/{AG['any_red']/tot_any:.0%}/{AG['any_green']/tot_any:.0%}"
           f"\n      Blue fully covered by Blue shields in {AG['blue_covered_by_color']/max(1,AG['blue_rounds']):.0%} of Blue rounds"
           f" | contested splits {s('contested'):.2f}/seat, Blue still live in {AG['contested_blue']/max(1,AG['contested']):.0%}"
           f" | Blue dice owned {St.mean(blue_own):.2f} | win rate by Blue dice 0/1/2+: "
           + " / ".join(f"{win_by[k]/cnt_by[k]:.0%} (n={cnt_by[k]})" for k in (0, 1, 2) if cnt_by[k]))
    return out

if __name__ == "__main__":
    G = int(sys.argv[1])
    for n in (2, 3, 4):
        for m in (None, "A", "C"):
            print(run(n, G, m), flush=True)
