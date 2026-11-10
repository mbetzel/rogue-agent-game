import json,sys,collections as C
rows=json.load(open(sys.argv[1]))
# phase-4 dump choice rate by ms bucket & sec lead (when dump distinct unknown; use chosen share among searched decisions)
t=C.defaultdict(lambda:[0,0])
for r in rows:
    for d in r['dec']:
        if d['hook']!='choose_any_shield_allocation': continue
        sl=d['sec']-max(d['rsec']) if d['rsec'] else 0
        k=(min(d['ms']//3*3,12), 'lead>=3' if sl>=3 else 'lead<3')
        t[k][1]+=1; t[k][0]+= d['lab']=='MarketShareDump'
for k in sorted(t): print(k, t[k], round(t[k][0]/t[k][1],3))
