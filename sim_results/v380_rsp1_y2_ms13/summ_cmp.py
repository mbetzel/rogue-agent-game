import json,sys
A='sim_results/v380_rsp1_y2/v038c_y2_pre_red_secret_owner_yield=2.json'
B='sim_results/v380_rsp1_y2_ms13/v038c_y2_ms13_h-5c10ad76.json'
def load(f,p=None):
    d=json.load(open(f))
    if isinstance(d,list):
        for c in d:
            if p is None or c['players']==p: return c
    return d
def row(d):
    e=d['endings'];h=d['rounds_hist'];g=d['games']
    le4=sum(v for k,v in h.items() if int(k)<=4)
    c=d['win_rate_by_company_color'];a=d['win_rate_by_archetype'];av=[v for v in a.values() if v is not None]
    r=d['rsp1'];pz=0
    s=e['singularity']*100
    return dict(sing=s,pz=e['patient_zero']*100,mc=e['market_collapse']*100,tw=e['total_wipeout']*100,rds=d['avg_rounds'],le4=le4/g*100,n4=le4,
     ge15=sum(v for k,v in h.items() if int(k)>=15),mx=max(int(k) for k in h),
     guard='PASS' if s<=43 else 'WATCH' if s<=48 else 'FAIL',strand=d['stranded_share']*100,wsec=d['winner_secrets_avg'],
     col=c,arch={k:round(v*100,1) for k,v in a.items() if v is not None},spread=(max(av)-min(av))*100,
     pay=r,ms_min=d['market_share_min_avg'],
     path={k:round(v*100,1) for k,v in d['win_rate_by_path'].items()},own=d['secrets_by_source_per_seat'].get('secret_face_red'))
x=load(A,2);y=load(B)
print(x['players'],y['players'],y['overrides'])
for n,d in(('3/4/4 y2 (base)',x),('MS13 y2',y)):
    print(n,json.dumps(row(d),default=str))
def ref(f):
    d=json.load(open(f))['games'];n=len(d)
    w=sum(1 for g in d if g['special'][0] in g['winner_ids'])
    from collections import Counter
    ec=Counter(g['end_reason'] for g in d)
    r=sum(g['rounds'] for g in d)/n
    return dict(n=n,win=w/n*100,edge=w/n*100-50,ends={k:round(v/n*100,1) for k,v in ec.items()},rds=r,le4=sum(1 for g in d if g['rounds']<=4),ge15=sum(1 for g in d if g['rounds']>=15))
print('ref old',ref('sim_results/v380_rsp1_y2/ref1/v038c_push_nonref_ref1_2p_1200.json'))
import glob
print('ref new',ref(glob.glob('sim_results/v380_rsp1_y2_ms13/ref1/*2p_1200.json')[0]))
