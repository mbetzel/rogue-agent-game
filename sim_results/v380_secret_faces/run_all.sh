set -e
D=sim_results/v380_secret_faces
for s in 3 4 5 6; do
 python3 scripts/run_v380_secret_faces_sweep.py --config v038_roster --roster mixed1 --games 1200 --players 2 3 4 --seed0 42 --procs 8 --set "starting_secrets_by_player_count={\"2\":$s,\"3\":$s,\"4\":$s}" --out $D/v038_roster_s$s.json --overwrite > $D/v038_roster_s$s.log
done
python3 scripts/run_v380_secret_faces_sweep.py --config v037_roster --roster mixed1 --games 1200 --players 2 3 4 --seed0 42 --procs 8 --out $D/v037_roster.json --overwrite > $D/v037_roster.log
python3 scripts/run_reference_bot_validation.py --config v038 --cells ref1 --players 3 --games 1200 --procs 8 --pr-push on --pr-push-scope non_reference --out-dir $D/ref1 > $D/ref1.log 2>&1
echo DONE
