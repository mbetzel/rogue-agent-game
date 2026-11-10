import json,glob,os,sys
for f in sorted(glob.glob(sys.argv[1]+'/*.json')):
    d=json.load(open(f)); d=d[0] if isinstance(d,list) else d.get('summary',d)
    if 'endings' not in d:
        d=next(v for v in d.values() if isinstance(v,dict) and 'endings' in v)
    e=d['endings']; h=d['rounds_hist']; g=d['games']
    le4=sum(v for k,v in h.items() if int(k)<=4)/g
    col=d['win_rate_by_company_color']; arch=d['win_rate_by_archetype']
    av=[v for v in arch.values() if v is not None]
    r=d['rsp1']
    print(os.path.basename(f), {k:round(v*100,1) for k,v in e.items()}, 'TW',d['total_wipeout_rate'],'rnd',d['avg_rounds'],'le4 %.1f'%(le4*100),
      'col',{k:round(v*100,1) for k,v in col.items()}, 'arch %.1f-%.1f'%(min(av)*100,max(av)*100),
      'pay/g',r['payouts_per_game'],'paySec',r['payout_secrets_per_seat'],'payLdrWin',r['payout_leader_is_winner_rate'])
