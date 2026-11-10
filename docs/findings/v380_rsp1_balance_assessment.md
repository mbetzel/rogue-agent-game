# RSP-1 (`GameConfig.v038c()`) balance assessment (Phase 49, game-designer, 2026-11-09)

Inputs: `sim_results/v380_rsp1/sweep_report.md` (1,200 games per cell, mixed1, seeds 42..1241) and its raw JSON; ref1 JSON and stall diagnostic in `sim_results/v380_rsp1/ref1/`. Probes: 400 games per cell, seeds 42..441, mixed1, `scripts/run_v380_secret_faces_sweep.py --config v038c --set ...` (output kept in scratchpad, not committed).

## Verdict: APPROVED WITH TUNE

The RSP-1 structure is sound and should be the v0.38.0 baseline: no stalling (mean Red wait 0.01–0.02 rounds, ≤0.12 pending Red dice at end, ≥2 Red banks in 2–3% of rounds), no game reached 15 rounds, archetype spread 30–32 pts (v038b 33–38), and end reasons are well spread (3P 40/37/22, 4P 42/40/18 Singularity/Patient Zero/Market Collapse). Two tunes are needed before it is locked: Red Company/Red path are too weak at 3–4P, and the 2P Singularity guardrail is WATCH (46.8%).

## 1. Red Company / Red path weakness: root cause

Per-seat breakdown by Company colour (1,200-game cells, v038c 3/4/4):

| P | Co | win | final Market Share | payout Secrets | own Secret-face Secrets | Red Secrets banked | Patient Zero rate |
|---|---|---|---|---|---|---|---|
| 3 | Red | .212 | 8.6 | 6.50 | 4.23 | 1.79 | .24 |
| 3 | Blue | .384 | 7.7 | 4.99 | 5.51 | 0.17 | .09 |
| 3 | Green | .399 | 7.5 | 4.69 | 8.36 | 0.14 | .11 |
| 4 | Red | .147 | 9.7 | 6.51 | 4.48 | 1.76 | .20 |
| 4 | Blue | .296 | 9.3 | 5.67 | 5.29 | 0.09 | .08 |
| 4 | Green | .305 | 9.1 | 5.40 | 7.97 | 0.11 | .09 |

(v038b: Red Company owned 8.9–9.4 face Secrets per seat and won .39/.34 at 3P/4P.)

- **Not "Red banks feed the leader" in the net.** Red Company seats actually hold the most Market Share and take the most payout Secrets (+1.5 to +1.8 over Blue/Green), because they bank most of the Red Secrets and the bots time banks to their own Market Share lead.
- **The cause is the payout structure: the owner yield is too small.** Red Secret owner yield +1 is the worst Secret face in the game (Green faces earn ~2.3 Secrets per bank, Blue ~1.7 with the protection value on top). Red Company gives up ~4 face Secrets per seat versus v038b and gets back only ~1.6 net from payouts, since the +3/+1 payout is paid to everyone by place, not to the banker. Red Company ends ~2.4 Secrets behind Green.
- **Second-order: Patient Zero 2–2.5x.** Red-heavy seats commit dice and Research to Red/Market Share and under-invest in Blue defence (Blue damage taken is like Green's, but they start with less Secret buffer from faces), so they are breached far more often.
- **Not the Company setup.** The Company starting colours are the same as v038b, where Red led; the swing came entirely from the RSP-1 face change.

## 2. Candidate fixes (probe, 400 games per cell, v038c 3/4/4)

| cell | P | Sing/PZ/MC % | rounds | Co win Red / Blue / Green | path red / yellow | archetype spread |
|---|---|---|---|---|---|---|
| base | 2 | 48/23/25 | 8.54 | .436 / .521 / .540 | .42 / .42 | 28.9 |
| base | 3 | 39/38/23 | 8.30 | .220 / .366 / .407 | .19 / .21 | 28.2 |
| base | 4 | 41/46/13 | 8.07 | .122 / .290 / .335 | .12 / .20 | 28.4 |
| **F1 owner yield +2** | 2 | 52/20/26 | 8.67 | .537 / .464 / .500 | .52 / .32 | 30.4 |
| **F1 owner yield +2** | 3 | 45/34/21 | 8.42 | .339 / .341 / .321 | .34 / .23 | 36.3 |
| **F1 owner yield +2** | 4 | 50/36/13 | 8.32 | .221 / .240 / .288 | .19 / .21 | 29.5 |
| F2 payout 2/1 (3–4P) | 3 | 40/35/25 | 8.44 | .215 / .374 / .404 | .26 / .21 | 31.2 |
| F2 payout 2/1 (3–4P) | 4 | 42/43/14 | 8.13 | .135 / .285 / .327 | .16 / .15 | 31.5 |
| F1+F2 | 3 | 45/33/22 | 8.50 | .370 / .323 / .309 | .38 / .17 | 37.1 |
| F1+F2 | 4 | 46/38/16 | 8.27 | .242 / .242 / .266 | .25 / .19 | 38.8 |
| F1 + 2P start Secrets 2 | 2 | 42/31/22 | 7.79 | .521 / .498 / .482 | .49 / .35 | 36.9 |

- **F1 (recommended): Red Secret owner yield +2.** Fixes Company colour at 3P (within 2 pts) and mostly at 4P (Red .22 vs .24–.29); lowers Patient Zero by 4–10 pts. Costs: Singularity +4 to +9 pts (2P 52% is a guardrail FAIL by itself), 3P spread +8 pts (noise band at 400 games is ~±5).
- **F2 (flatter payout 2/1):** barely moves Red Company (the payout is not the lever) and hurts Yellow at 4P. Reject.
- **F1+F2:** overcorrects at 3P (Red .37) and widens spread to 37–39. Reject.
- **F3 (not probed; no config knob):** Red Company starts with +1 Research Token / +1 Market Share, a Company-setup patch. Lower priority, since the cause is the face yield, not setup.

## 3. Starting Secrets

- 3/3/4 vs 3/4/4 data: 2/3/4 doubles games of ≤4 rounds (20–21%) and lifts 3P Patient Zero to 47%. **Keep 3P/4P at 4.**
- 2P: with F1, 3 gives Singularity 52% (FAIL) and 2 gives 42% (PASS) but 20% of games ≤4 rounds. Recommend **3/4/4 with F1, plus a 2P-only Singularity lever** (e.g. `v3.0` one slot larger at 2P) rather than cutting 2P Secrets; if the User prefers a single knob, 2/4/4 is acceptable with the short-game cost noted.

## 4. ref1 and Market Collapse

ref1 edge +43.9 pts at 3P (77.2%) and +38.6 at 2P (88.6%), vs ~+38 / +33–36 before (gate +10). ref1 games end by Market Collapse 52% (3P) / 60% (2P), vs ~20–27% in mixed play.

Kamikaze/denial check on the ref1 per-game records:
- ref1 wins the same share of Market Collapse and non-Market Collapse games (3P 77.4 vs 77.0%; 2P 87.4 vs 90.3%).
- ref1 is itself at 0 Market Share (one of the collapsed players) in 47% (3P) / 59% (2P) of its Market Collapse games, and still wins 71% / 86% of those.
- If the end payout had fired in those Market Collapse games (+3/+1 by final Market Share place), ref1 would still have the most Secrets in 76.2% (3P) / 87.9% (2P) of them, versus 77.4% / 87.4% actual. **Denying the end payout is worth ≤1.2 pts to ref1.**

Conclusion: ref1 is not exploiting the end-payout exception. It uses Market Collapse as a **tempo end**: it drives everyone's Market Share down while ahead on Secrets and closes the game early, which the mixed bots do not do. This is the existing Phase 47 finding (FINDINGS §40), now stronger because Market Share no longer pays Money and is cheaper to sacrifice. Not a rules hole by the kamikaze test (no elimination, no pay-off from losing), but it is a degenerate-strategy WATCH: a leader can end the game at will once Market Share is low. Optional rule fix if wanted: a player at 0 Market Share who triggers Market Collapse scores no end payout but the end payout fires for the rest (ends the "Market Collapse cancels the end payout" exception). This removes the denial lever entirely at no measured cost; not probed (no knob).

## 5. User decisions needed

1. Adopt **F1: Red Secret owner yield +2** (`red_secret_owner_yield=2`) as the v0.38.0 tune? (Confirm sweep 1,200 games before locking.)
2. 2P Singularity: add a 2P-only lever (preferred), or 2P starting Secrets 2 (2/4/4), or accept WATCH?
3. Starting Secrets 3P/4P stay at 4 (recommended; 2/3/4 rejected)?
4. Market Collapse end payout: keep the exception (ref1 gains ≤1.2 pts) or fire the end payout on Market Collapse for non-collapsed players?
5. Accept ref1 edge +44 as a bot-skill gap (FAIL vs +10 gate, as in every version), or open a mixed-bot Market Collapse tempo upgrade?
