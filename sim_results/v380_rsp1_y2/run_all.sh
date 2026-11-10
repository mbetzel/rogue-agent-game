set -e
D=sim_results/v380_rsp1_y2
Y='red_secret_owner_yield=2'
python3 scripts/run_v380_secret_faces_sweep.py --config v038c --roster mixed1 --games 1200 --players 2 3 4 --seed0 42 --procs 8 --set "$Y" --out $D/v038c_y2_pre.json --overwrite > $D/v038c_y2_pre.log
python3 scripts/run_v380_secret_faces_sweep.py --config v038c --roster mixed1 --games 1200 --players 2 --seed0 42 --procs 8 --set "$Y" --set 'starting_secrets_by_player_count={"2":2,"3":4,"4":4}' --out $D/v038c_y2_s2.json --overwrite > $D/v038c_y2_s2.log
python3 $D/ref1/ref_run.py --config v038c --cells ref1 --players 3 --games 1200 --procs 8 --pr-push on --pr-push-scope non_reference --out-dir $D/ref1 > $D/ref1_3p.log 2>&1
python3 $D/ref1/ref_run.py --config v038c --cells ref1 --players 2 --games 1200 --procs 8 --pr-push on --pr-push-scope non_reference --out-dir $D/ref1 > $D/ref1_2p.log 2>&1
python3 $D/ref1/ref_run.py diag 3 $D/ref1/diag_3p.json
python3 $D/ref1/ref_run.py diag 2 $D/ref1/diag_2p.json
echo DONE
