# exact per-die finals with 3 rolls; faces: S (secret warn), C (core warn), T (star), P (plain)
from fractions import Fraction as F
def die(nS, nC, nT, nP, reroll):  # reroll: set of face kinds rerolled while rerolls remain; lock: C,S can't be rerolled
    p = {"S": F(nS,6), "C": F(nC,6), "T": F(nT,6), "P": F(nP,6)}
    dist = dict(p)
    for _ in range(2):
        nd = {k: F(0) for k in p}
        for k, pk in dist.items():
            if k in reroll:
                for j, pj in p.items(): nd[j] += pk*pj
            else: nd[k] += pk
        dist = nd
    return dist
pol = {
 "v046 safe (rr C)": {"C"}, "v046 rr all warn": {"C","S"}, "v046 chase (rr C,P)": {"C","P"}, "v046 chase all (rr C,S,P)": {"C","S","P"},
 "lock keep all": set(), "lock chase (rr P)": {"P"},
}
for name, kinds in [("R/B/G/P (1S+1C+1T+3P)", (1,1,1,3)), ("Yellow (2C+1T+3P)", (0,2,1,3)), ("Gray (3W as C, 3P)", (0,3,0,3))]:
    print("==", name)
    for pn, rr in pol.items():
        if name.startswith("Gray") and pn.startswith("lock"): continue
        if name.startswith("Gray") and "S" in rr: continue
        d = die(*kinds, rr)
        print(f"  {pn:28s} warn={float(d['S']+d['C']):.3f}  S={float(d['S']):.3f} C={float(d['C']):.3f} star={float(d['T']):.3f}")
# pool distributions
import itertools
def conv(ps):
    dist=[1.0]
    for p in ps:
        nd=[0.0]*(len(dist)+1)
        for i,x in enumerate(dist): nd[i]+=x*(1-p); nd[i+1]+=x*p
        dist=nd
    return dist
G_SAFE, G_OBS = 0.125, 0.38
pools = {"starter 2G+2C": 2, "mid 2G+4C": 4, "late 2G+6C": 6}
rates = {"v046 safe": (G_SAFE, 0.204), "lock safe": (G_SAFE, 1/3), "v046 chase": (G_SAFE, 0.426), "lock chase": (G_SAFE, 0.583),
         "sim v046 obs": (G_OBS, 0.33), "sim lock obs": (G_OBS, 0.52)}
print("\nE[warn]/round and P(cross t | V0): rows pool x policy; cols V0=0..9 -> P(V0+X >= next threshold among 4/7/10)")
for pn, nc in pools.items():
    for rn, (g, c) in rates.items():
        d = conv([g,g]+[c]*nc)
        ev = sum(i*x for i,x in enumerate(d))
        cross=[]
        for v0 in range(10):
            t = next(t for t in (4,7,10) if t > v0)
            cross.append(sum(x for i,x in enumerate(d) if v0+i >= t))
        p4 = sum(x for i,x in enumerate(d) if i>=4)
        print(f"{pn:14s} {rn:13s} E={ev:4.2f} P(X>=4 from 0)={p4:.2f} | " + " ".join(f"{x:.2f}" for x in cross))
