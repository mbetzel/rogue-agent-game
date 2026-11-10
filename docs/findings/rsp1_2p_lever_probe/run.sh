cd /home/mike/antigravity/rogue-agent/.claude/worktrees/phase-49-execution-dcd489
S=/tmp/claude-1000/-home-mike-antigravity-rogue-agent--claude-worktrees-phase-49-execution-dcd489/c961b4b7-76ca-4f80-8b41-66414076c50b/scratchpad/p2
P=${P:-2}
r(){ n=$1; shift; python3 scripts/run_v380_secret_faces_sweep.py --config v038c --roster mixed1 --games 600 --players $P --seed0 42 --procs 8 --set red_secret_owner_yield=2 "$@" --out $S/${n}_${P}p.json --overwrite > $S/${n}_${P}p.log 2>&1 || echo FAIL $n; }
for c in $CELLS; do case $c in
base) r base;;
cap6) r cap6 --set corruption_track_flat_capacity=6;;
cap7) r cap7 --set corruption_track_flat_capacity=7;;
ms14) r ms14 --set 'market_share_start_by_player_count={"2":14,"3":16,"4":17}';;
ms12) r ms12 --set 'market_share_start_by_player_count={"2":12,"3":16,"4":17}';;
pay21) r pay21 --set 'red_secret_payout_by_player_count={"2":[2,1],"3":[3,1,0],"4":[3,1,0,0]}';;
pay20) r pay20 --set 'red_secret_payout_by_player_count={"2":[2,0],"3":[3,1,0],"4":[3,1,0,0]}';;
pulse0) r pulse0 --set 'autonomous_pulse_by_version={"v1.0":0,"v2.0":1,"v3.0":1}';;
cap5) r cap5 --set corruption_track_flat_capacity=5;;
ms13) r ms13 --set 'market_share_start_by_player_count={"2":13,"3":16,"4":17}';;
ms3p14) r ms3p14 --set 'market_share_start_by_player_count={"2":16,"3":14,"4":17}';;
esac; done
echo DONE
