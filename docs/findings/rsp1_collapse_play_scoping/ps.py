import json,sys,collections as C
for f in sys.argv[1:]:
    d=json.load(open(f)); R=d['rows']; n=len(R); P=len(R[0]['pz'])
    sw=sum(r['sp'] in r['w'] for r in R)/n
    ends=C.Counter(r['end'] for r in R)
    mc=[r for r in R if r['end']=='market_collapse']
    spz=sum(r['sp'] in r['cpids'] for r in mc)
    print(f"{f:22s} P{P} special win {sw:.3f} ({100*(sw-1/P):+.1f}) rounds {sum(r['rounds'] for r in R)/n:.2f} "
      + " ".join(f"{k[:6]} {v/n:.3f}" for k,v in sorted(ends.items()))
      + f" | sp-is-0MS {spz/n:.3f} TW {sum(r['tw'] for r in R)/n:.3f} PZany {sum(any(r['pz']) for r in R)/n:.3f} dash/g {sum(r['dd'] for r in R)/n:.1f}")
