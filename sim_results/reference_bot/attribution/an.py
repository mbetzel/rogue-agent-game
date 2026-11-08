import json, sys, glob, math, collections
D = "/home/mike/antigravity/rogue-agent/sim_results/reference_bot/attribution"
def ci(k, n): p = k/n; return 100*p, 196*math.sqrt(p*(1-p)/n)
for fn in sorted(glob.glob(D + "/*_1200.json")):
    R = json.load(open(fn)); n = len(R); tag = fn.split("/")[-1][:-15]
    w = sum(r["sp"] in r["winners"] and 1/len(r["winners"]) for r in R)
    ends = collections.Counter(r["end"] for r in R)
    at0 = alone = at0w = alonew = 0; leads = []
    for r in R:
        sp = r["sp"]
        if r["end"] == "market_collapse" or r["mc_round"]:
            if sp in r["mc_pids"]:
                at0 += 1; win = sp in r["winners"]; at0w += win
                if len(r["mc_pids"]) == 1: alone += 1; alonew += win
                sec = r["traj"][r["mc_round"] - 1][1] if False else None
                row = r["traj"][min(r["mc_round"], len(r["traj"])) - 1]
                oth = max(row[i][1] for i in range(len(row)) if i != sp)
                leads.append(row[sp][1] - oth)
    def avg(f, me=True):
        v = [f(s) for r in R for i, s in enumerate(r["seats"]) if (i == r["sp"]) == me and f(s) is not None]; return sum(v)/len(v)
    blk = {c: sum(r["seats"][r["sp"]]["blocked_" + c] for r in R) for c in ("red", "blue", "green")}; tb = sum(blk.values())
    pl = collections.Counter(r["seats"][r["sp"]]["place"] for r in R)
    ch = collections.Counter()
    for r in R: ch.update(r["choices"])
    def share(h, lab): return 100*ch[f"{h}|{lab}"]/max(1, ch[f"n|{h}"])
    p, h = ci(w, n)
    print(f"== {tag}  win {p:.1f}±{h:.1f}  ends " + " ".join(f"{k} {100*v/n:.1f}" for k, v in ends.items()) + f"  rounds {sum(r['rounds'] for r in R)/n:.2f}")
    print(f"   ref at0@MC {at0} (won {at0w}) alone {alone} (won {alonew})  lead@trigger {sum(leads)/max(1,len(leads)):+.2f}  behind {sum(l<0 for l in leads)}")
    print(f"   lostRed ref/riv {avg(lambda s:s['lost_red']):.2f}/{avg(lambda s:s['lost_red'],False):.2f}  regained {avg(lambda s:s['regained']):.2f}/{avg(lambda s:s['regained'],False):.2f}  PR {avg(lambda s:s['pr']):.2f}/{avg(lambda s:s['pr'],False):.2f}  finalMS {avg(lambda s:s['ms']):.2f}/{avg(lambda s:s['ms'],False):.2f}")
    print(f"   MLB places " + " ".join(f"{k}:{100*v/n:.1f}" for k, v in sorted(pl.items(), key=lambda x: str(x[0]))) + "  blocks R/B/G " + "/".join(f"{100*blk[c]/tb:.1f}" for c in ("red","blue","green")) + f"  Redblockrate {blk['red']/max(1,sum(r['seats'][r['sp']]['incoming_red'] for r in R)):.2f}")
    print(f"   choice P4 push {share('choose_any_shield_allocation','PublicRelationsPush'):.1f} dump {share('choose_any_shield_allocation','MarketShareDump'):.1f} | P6 push {share('take_operations_actions','PublicRelationsPush'):.1f} dump {share('take_operations_actions','MarketShareDump'):.1f}")
