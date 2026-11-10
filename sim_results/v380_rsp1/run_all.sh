set -e
D=sim_results/v380_rsp1
S='starting_secrets_by_player_count={"2":2,"3":3,"4":4}'
python3 scripts/run_v380_secret_faces_sweep.py --config v038c --roster mixed1 --games 1200 --players 2 3 --seed0 42 --procs 8 --set "$S" --out $D/v038c_s234.json --overwrite > $D/v038c_s234.log
python3 scripts/run_v380_secret_faces_sweep.py --config v038b --roster mixed1 --games 1200 --players 2 3 4 --seed0 42 --procs 8 --out $D/v038b_pre.json --overwrite > $D/v038b_pre.log
python3 scripts/run_reference_bot_validation.py --config v038c --cells ref1 --players 3 --games 1200 --procs 8 --pr-push on --pr-push-scope non_reference --out-dir $D/ref1 > $D/ref1_3p.log 2>&1
python3 scripts/run_reference_bot_validation.py --config v038c --cells ref1 --players 2 --games 1200 --procs 8 --pr-push on --pr-push-scope non_reference --out-dir $D/ref1 > $D/ref1_2p.log 2>&1
echo DONE
