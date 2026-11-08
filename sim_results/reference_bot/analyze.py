import json, glob, os, math
D = os.path.dirname(os.path.abspath(__file__))
def load(cfg, cell, P, n):
    return json.load(open(f"{D}/{cfg}_{cell}_{P}p_{n}.json"))
def share(r, pid): return (1/len(r["winner_ids"])) if pid in r["winner_ids"] else 0.0
def ci(p, n):
    h = 1.96 * math.sqrt(p*(1-p)/n); return p-h, p+h
out = []
def pr(s=""): out.append(s)
ERR = []
for cfg in ("v036", "v037"):
    pr(f"\n## {cfg}\n")
    d = load(cfg, "ref1", 3, 600); pr(f"Timing ref1 3P 600: wall {d['wall_s']:.1f}s")
    d = load(cfg, "ref_all", 3, 600); pr(f"Timing ref_all 3P 600: wall {d['wall_s']:.1f}s\n")
    pr("| cell | P | N | ref/special win | 95% CI | fair |"); pr("|---|---|---|---|---|---|")
    for cell, P, n in (("ref1", 3, 1200), ("ref1", 2, 600), ("ref1", 4, 600), ("mixed1", 2, 1200), ("mixed1", 3, 1200), ("mixed1", 4, 1200)):
        g = [r for r in load(cfg, cell, P, n)["games"] if not r["error"]]
        w = sum(share(r, r["special"][0]) for r in g) / len(g); lo, hi = ci(w, len(g))
        pr(f"| {cell} | {P} | {len(g)} | {w:.1%} | {lo:.1%}–{hi:.1%} | {1/P:.1%} |")
    pr("\n| cell | P | PZ% | Sing% | MC-end% | Wipeout% | MC trigger (any)% | rounds |"); pr("|---|---|---|---|---|---|---|---|")
    for cell in ("baseline", "mixed1"):
        for P in (2, 3, 4):
            g = [r for r in load(cfg, cell, P, 1200)["games"] if not r["error"]]; n = len(g)
            e = lambda k: sum(r["end_reason"] == k for r in g) / n
            mc = sum(bool(r["collapse_pids"]) for r in g) / n
            pr(f"| {cell} | {P} | {e('patient_zero'):.1%} | {e('singularity'):.1%} | {e('market_collapse'):.1%} | {e('total_wipeout'):.1%} | {mc:.1%} | {sum(r['rounds'] for r in g)/n:.2f} |")
    pr("\nWin rate by archetype (baseline -> mixed1):\n"); 
    for P in (2, 3, 4):
        res = {}
        for cell in ("baseline", "mixed1"):
            acc = {}
            for r in load(cfg, cell, P, 1200)["games"]:
                if r["error"]: continue
                for pid, s in enumerate(r["seats"]):
                    a = acc.setdefault(s["name"], [0, 0]); a[0] += share(r, pid); a[1] += 1
            res[cell] = {k: v[0]/v[1] for k, v in acc.items()}
        pr(f"- {P}P: " + "; ".join(f"{k.replace('Bot','')} {res['baseline'].get(k, float('nan')):.1%}->{res['mixed1'].get(k, float('nan')):.1%}" for k in sorted(set(res['baseline'])|set(res['mixed1']))))
    pr("\n| cell | N | ref win | blk R/B/G share | Secrets lost to Blue/g | PR lvl | end MS | MLB place 1/2/3/none | MC end% | MC triggered by ref seat% | MC trigger seats (ref/other) |")
    pr("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for cell, n in (("ref1", 1200), ("ref_all", 600)):
        g = [r for r in load(cfg, cell, 3, n)["games"] if not r["error"]]
        S = [(r, pid, r["seats"][pid]) for r in g for pid in r["special"]]
        tb = {c: sum(s["blocked_"+c] for _, _, s in S) for c in ("red", "blue", "green")}; T = sum(tb.values()) or 1
        pl = {}
        for _, _, s in S: pl[s["mlb_place"]] = pl.get(s["mlb_place"], 0) + 1
        mcref = sum(pid in r["collapse_pids"] for r, pid, _ in S) / len(S)
        trig_ref = sum(sum(p in r["special"] for p in r["collapse_pids"]) for r in g)
        trig_oth = sum(sum(p not in r["special"] for p in r["collapse_pids"]) for r in g)
        mse = [s["market_share"] for _, _, s in S if s["market_share"] is not None]
        w = sum(share(r, pid) for r, pid, _ in S) / len(S)
        pr(f"| {cell} | {len(g)} | {w:.1%} | {tb['red']/T:.0%}/{tb['blue']/T:.0%}/{tb['green']/T:.0%} | {sum(s['secrets_lost_blue'] for _,_,s in S)/len(S):.2f} | "
           f"{sum(s['pr_level'] for _,_,s in S)/len(S):.2f} | {sum(mse)/max(1,len(mse)):.2f} | "
           f"{'/'.join(f'{pl.get(k,0)/len(S):.0%}' for k in (1,2,3,None))} | {sum(r['end_reason']=='market_collapse' for r in g)/len(g):.1%} | {mcref:.1%} | {trig_ref}/{trig_oth} |")
        ex = [r["seed"] for r, pid, _ in S if pid in r["collapse_pids"] and pid in r["winner_ids"]]
        pr(f"\n{cell} seeds where ref seat triggered Market Collapse and won ({len(ex)} total): {sorted(set(ex))[:5]}\n")
for f in sorted(glob.glob(f"{D}/*.json")):
    for r in json.load(open(f))["games"]:
        if r["error"]: ERR.append((os.path.basename(f), r["seed"], r["error"]))
pr(f"\nErrors: {len(ERR)}")
for e in ERR[:5]: pr(str(e))
print("\n".join(out))
