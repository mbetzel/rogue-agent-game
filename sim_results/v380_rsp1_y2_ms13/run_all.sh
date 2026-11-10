set -e
D=sim_results/v380_rsp1_y2_ms13
python3 scripts/run_v380_secret_faces_sweep.py --config v038c --roster mixed1 --games 1200 --players 2 --seed0 42 --procs 8 --set red_secret_owner_yield=2 --set 'market_share_start_by_player_count={"2":13,"3":16,"4":17}' --out $D/v038c_y2_ms13.json --overwrite > $D/v038c_y2_ms13.log
python3 $D/ref1/ref_run.py --config v038c --cells ref1 --players 2 --games 1200 --procs 8 --pr-push on --pr-push-scope non_reference --out-dir $D/ref1 > $D/ref1_2p.log 2>&1
echo DONE
