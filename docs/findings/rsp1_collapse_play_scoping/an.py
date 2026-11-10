import json,sys,collections as C
rows=json.load(open(sys.argv[1])); P=int(sys.argv[2]); n=len(rows)
win=sum(r['win']/r['nwin'] if r['win'] else 0 for r in rows)/n  # tie-split
winf=sum(r['win'] for r in rows)/n
ends=C.Counter(r['end'] for r in rows)
mc=[r for r in rows if r['end']=='market_collapse']
refz=[r for r in mc if r['sp'] in r['cpids']]
print(f"P={P} n={n} ref win {winf:.3f} (tie-split {win:.3f}) edge {100*(winf-1/P):+.1f}")
print("ends",{k:round(v/n,3) for k,v in ends.items()})
print(f"MC games {len(mc)} ; ref among 0-MS triggerers {len(refz)} ({len(refz)/max(1,len(mc)):.2f}); ref-only {sum(1 for r in mc if r['cpids']==[r['sp']])}")
print("ref win | MC & ref0:",round(sum(r['win'] for r in refz)/max(1,len(refz)),3)," MC & not ref0:",round(sum(r['win'] for r in mc if r not in refz)/max(1,len(mc)-len(refz)),3),
      " non-MC:",round(sum(r['win'] for r in rows if r['end']!='market_collapse')/max(1,n-len(mc)),3))
# ref-triggered collapses: state at start of collapse round, and 1-2 rounds before
def bucket(f,x):
    return f(x)
print("avg rounds all",sum(r['rounds'] for r in rows)/n," ref0 MC",sum(r['rounds'] for r in refz)/max(1,len(refz)))
feat=C.defaultdict(C.Counter)
for r in refz:
    k=r['cround']; pre=[x['pre'] for x in r['rlog'] if x['pre']['r']==k][0]
    sl=pre['sec']-max(pre['rsec']); feat['round'][k]+=1; feat['v'][pre['v']]+=1
    feat['ms_pre'][min(pre['ms'],10)]+=1; feat['sl_pre'][max(-4,min(6,sl))]+=1; feat['rl'][min(pre['rl'],8)]+=1
    feat['rank_ms'][sorted([pre['ms']]+pre['rms']).index(pre['ms'])]+=1
for k,v in feat.items(): print(k,sorted(v.items()))
# trajectory: ref MS by round, ref0 MC games vs others
def traj(rs):
    d=C.defaultdict(list)
    for r in rs:
        for x in r['rlog']: d[x['pre']['r']].append((x['pre']['ms'],x['pre']['sec']-max(x['pre']['rsec']) if x['pre']['rsec'] else 0, sum(x['pre']['rms'])/max(1,len(x['pre']['rms']))))
    return {k:(round(sum(a for a,_,_ in v)/len(v),1),round(sum(b for _,b,_ in v)/len(v),1),round(sum(c for _,_,c in v)/len(v),1),len(v)) for k,v in sorted(d.items())}
print("traj ref0MC (ms, secLead, rivalMS, n):",traj(refz))
print("traj other:",traj([r for r in rows if r not in refz]))
# chosen labels by hook in ref0MC vs others
lab=C.defaultdict(C.Counter)
for r in rows:
    g='ref0' if r in refz else 'oth'
    for d in r['dec']: lab[(g,d['hook'])][d['lab']]+=1
for k,v in sorted(lab.items()): print(k,v.most_common(6))
