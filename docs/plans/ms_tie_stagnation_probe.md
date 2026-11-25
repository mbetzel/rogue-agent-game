# Market Share Tie Stagnation: Pre-SDLC Probe (v0.51.0)

*2026-11-25. Investigation only: no rules, presets or engine code changed.*
Probe: `scripts/probe_ms_ties.py` (monkeypatch only), `v051_roster`, `mixed1`, 3,000 games per pod, seeds 42+.
Raw summaries: `sim_results/ms_ties/<arm>_<P>P.json`.

## 1. The question

Playtest feel: Market Share ties are too common, players have little reason to move past a rival, and Red cubes
keep tied players tied.

## 2. Diagnosis (v0.51.0 baseline, R0)

| Metric (end of each round, MLB participants) | 2P | 3P | 4P |
|---|---|---|---|
| Rounds with a tie for 1st | 17.5% | 29.7% | 35.2% |
| ...of which the tie is at the track maximum (20) | 0.2% | 5.0% | 7.2% |
| Rounds with any tie | 21.8% | 48.6% | 71.7% |
| Market Leader Bonus awards with a tie for 1st | 12.4% | 26.4% | 32.4% |
| Game-end Market Share tie | 3.1% | 22.9% | 42.4% |
| Game-end Market Share spread (max − min) | 2.1 | 3.2 | 4.4 |
| A tie still there next round | 28.5% | 36.4% | 36.6% |
| MLB Secrets paid per game | 10.8 | 17.2 | 21.9 |

Market Share movement per player-round (4P): **Red −1.81**, faces +0.70, PR regain +0.36, everything else < 0.1.

Three structural causes:

1. **Red never changes a gap.** Red is ~62% of all Market Share movement, and every survivor loses the same amount.
   Only gains (faces + PR, ~1.1 per player-round) move players relative to each other, and those are similar
   across players. Two tied players stay tied unless one of them rolls or buys more.
2. **The track is crowded.** At 3–4P the whole table sits in a ~3–4 space band (spread 3.2 / 4.4). With 4
   cubes in 4–5 spaces, ties follow from counting alone. The start (18) sits 2 below the cap (20), so the top
   of the band also piles up on the cap (~20% of 1st-place ties at 3–4P).
3. **A tie is as good as a lead.** Tied players share the *better* place, so matching the leader pays the full
   +3. Passing them earns nothing more. (The bots already value breaking ties, yet ties persist, so the cause is
   structural, not bot laziness.)

**Hidden consequence:** tie sharing is a large Secret faucet. At 4P, roughly a quarter to half of MLB Secrets
come from tied players each taking the better award (21.9/game vs 11.5–15.9 with ties broken; §3). Any fix that
breaks ties must re-tune the MLB schedule, or games get shorter and more lethal.

## 3. Candidates probed

| Arm | Rule (probe wording) |
|---|---|
| TWORSE | MLB: tied players share the **worse** place (2 tied for 1st both score 2nd's `+1`) |
| TSPLIT | MLB: tied players split the awards of the places they span, rounded down (2-way 1st tie: `+2` each) |
| STACK | **Arrival order**: a marker that moves onto an occupied space goes *beneath* the markers already there and ranks below them (MLB and the Market Share tiebreaker). Red moves everyone together, so the order is kept. Setup stack: last seat on top. SETEC Corp is included at 2P |
| CAP25 | Track maximum 25 (starts unchanged: 14 / 18 / 18) |
| STAG | Staggered start 18/17/16/15 (2P 14/13), last seat highest |
| RLOW | Red: each cube costs only the lowest player(s) 1 (from the feedback-1122 probe) |
| RVULN | Red as today, plus players at Vulnerability 5+ lose 1 more in any round with Red |
| AWARE | Bots value a tie as the worse place, so they push to pass (needed to see the incentive effect of STACK / TWORSE) |
| S32 | MLB `+3 / +2` at 3P and 4P (2P stays `+3 / +1`) |

Effective 1st-place ties are what the MLB actually sees: under STACK they are 0% by construction. "Raw" is cubes
on the same space.

### 4P (3,000 games per arm)

| Arm | Rounds | PZ | MC | Sing | Raw top tie | MLB 1st tie (effective) | End spread | MLB Secrets/g | Winner Secrets | Company spread |
|---|---|---|---|---|---|---|---|---|---|---|
| **R0 (v0.51)** | 8.1 | 67.0 | 12.3 | 19.7 | 35.2 | 32.4 | 4.4 | 21.9 | 12.5 | 11.4 |
| TWORSE | 7.5 | 78.6 | 9.7 | 11.1 | 34.9 | 31.9 | 4.1 | 11.5 | 10.5 | 12.5 |
| TSPLIT | 7.7 | 75.2 | 10.5 | 13.6 | 35.2 | 32.2 | 4.2 | 14.7 | 11.2 | 12.5 |
| STACK | 7.7 | 74.1 | 10.8 | 14.4 | 34.9 | 0 | 4.2 | 15.9 | 11.7 | 14.6 |
| CAP25 | 8.0 | 68.8 | 12.0 | 18.6 | 26.6 | 22.9 | 5.4 | 20.3 | 12.6 | 11.1 |
| STAG | 7.8 | 68.3 | 16.3 | 15.2 | 25.1 | 23.8 | 5.4 | 19.2 | 13.0 | 11.4 |
| RLOW | 8.4 | 62.4 | 6.2 | 30.9 | 64.5 | 70.3 | 7.3 | 28.0 | 14.3 | 15.3 |
| RVULN | 7.7 | 65.2 | 22.5 | 11.6 | 31.8 | 28.2 | 4.6 | 20.5 | 12.7 | 12.0 |
| STACK+AWARE | 7.9 | 69.0 | 14.0 | 16.6 | 31.1 | 0 | 4.7 | 16.8 | 12.5 | 18.8 |
| TWORSE+AWARE | 7.7 | 72.7 | 13.0 | 13.7 | 31.0 | 27.5 | 4.6 | 12.8 | 11.4 | 14.9 |
| STACK+AWARE+S32 | 7.9 | 69.6 | 13.8 | 16.2 | 31.3 | 0 | 4.8 | 21.6 | 14.8 | 20.2 |
| STACK+AWARE+CAP25 | 7.9 | 69.5 | 14.1 | 15.9 | 24.6 | 0 | 5.8 | 16.8 | 12.6 | 15.8 |
| **STACK+AWARE+CAP25+S32** | 7.9 | 69.8 | 14.0 | 15.8 | 24.8 | 0 | 5.8 | 21.6 | 15.0 | 15.5 |

### 3P

| Arm | Rounds | PZ | MC | Sing | Raw top tie | MLB 1st tie (eff.) | End spread | MLB Sec/g | Winner Sec | Co. spread |
|---|---|---|---|---|---|---|---|---|---|---|
| **R0** | 8.2 | 61.4 | 12.0 | 24.5 | 29.7 | 26.4 | 3.2 | 17.2 | 11.4 | 15.0 |
| TWORSE | 7.7 | 71.2 | 10.4 | 16.2 | 29.3 | 25.1 | 3.0 | 11.2 | 10.1 | 16.6 |
| STACK | 8.0 | 66.4 | 11.6 | 19.6 | 29.5 | 0 | 3.1 | 13.9 | 10.8 | 18.7 |
| CAP25 | 8.2 | 62.8 | 12.2 | 23.0 | 23.3 | 19.5 | 3.9 | 16.5 | 11.4 | 13.3 |
| STAG | 8.1 | 62.1 | 16.3 | 20.0 | 23.6 | 21.0 | 3.6 | 16.6 | 11.9 | 11.6 |
| RLOW | 8.3 | 62.2 | 8.2 | 27.8 | 49.4 | 52.7 | 6.4 | 18.9 | 12.8 | 20.4 |
| RVULN | 7.9 | 60.2 | 21.8 | 16.1 | 27.2 | 22.9 | 3.4 | 16.4 | 11.6 | 12.3 |
| STACK+AWARE | 8.1 | 64.6 | 14.5 | 19.4 | 26.7 | 0 | 3.4 | 14.5 | 11.6 | 16.5 |
| STACK+AWARE+S32 | 8.0 | 64.9 | 14.2 | 19.3 | 26.5 | 0 | 3.5 | 19.0 | 14.1 | 18.9 |
| **STACK+AWARE+CAP25+S32** | 8.0 | 65.1 | 14.1 | 19.4 | 21.6 | 0 | 4.2 | 19.2 | 14.3 | 18.2 |

### 2P

Ties are rarer (17.5% raw top tie, 12.4% of MLB awards; SETEC Corp is the usual partner). Every tie-break arm stays
within ~3pp of R0 on PZ / MC / Singularity. STACK+AWARE: PZ 41.9, MC 29.3, Sing 20.8 (R0 42.2 / 28.1 / 20.8). 2P
needs no schedule change.

## 4. Takeaways

1. **Red-side fixes are the wrong lever.** RLOW makes ties far worse: everyone but the trailer parks on the cap
   (4P raw top tie 35 → 65%). RVULN breaks a few ties but nearly doubles Market Collapse (12 → 22%). Leader-
   targeted Red was already shown to remove Market Collapse (cube-escalation and feedback-1122 probes). Uniform
   Red is what makes Market Collapse a shared threat, so keep it, and fix ties on the scoring side.
2. **Any tie-break costs Secrets.** TWORSE / TSPLIT / STACK without compensation cut MLB Secrets by 6–10 per
   game at 4P, so PZ rises 7–12pp and Singularity falls 5–9pp. S32 (`+3 / +2` at 3–4P) restores MLB Secrets
   almost exactly (21.6 vs 21.9 at 4P; 19.0 vs 17.2 at 3P).
3. **STACK gives the incentive the playtest asked for.** Matching the leader no longer earns 1st place; you must
   pass them. Taught bots (AWARE) respond: raw ties fall 35 → 31% (4P) with no extra Market Share sources.
   TWORSE also motivates, but through a spoiler move (matching the leader drops you both to `+1`) and it deflates
   Secrets harder.
4. **CAP25 is the cheapest spread lever.** It removes the pile-up on the cap (ties at the cap 7.2 → 0.3%), widens
   end spread 4.4 → 5.8, and is about pacing-neutral on its own. With STACK, the cap also matters for incentive:
   two players stacked on the maximum can never pass each other.
5. **STAG is not needed with STACK.** The setup stack order already breaks the opening ties without the +4pp
   Market Collapse that staggered starts cost.

## 5. Recommended package (for sign-off): STACK + CAP25 + S32

| vs v0.51 | 3P | 4P |
|---|---|---|
| Effective MLB ties for 1st | 26.4% → 0 | 32.4% → 0 |
| Cubes on the same space at the top | 29.7 → 21.6% | 35.2 → 24.8% |
| End Market Share spread | 3.2 → 4.2 | 4.4 → 5.8 |
| Rounds | 8.2 → 8.0 | 8.1 → 7.9 |
| Patient Zero / Market Collapse / Singularity | +3.7 / +2.1 / −5.1pp | +2.8 / +1.7 / −3.9pp |
| MLB Secrets per game | 17.2 → 19.2 | 21.9 → 21.6 |
| Winner Secrets | 11.4 → 14.3 | 12.5 → 15.0 |
| Company win spread | 15.0 → 18.2 | 11.4 → 15.5 |

**Watch items:** (a) winner Secrets +3: a stronger 2nd-place award means MLB matters more to who wins. A `+3 / +1`
schedule with a `+4` sole leader would be an alternative to probe. (b) Company spread +3–4pp: at 3,000 games
per arm that is close to noise, but it needs a per-company look in the SDLC sweep. (c) Seat balance under the
setup stack (4P seat spread 1.9 → 4.1).

## 6. Decisions for the user

- **D1 Tie rule:** STACK (arrival order, the incumbent holds the space) / TWORSE (ties take the worse place) /
  keep shared ties.
- **D2 Terminology:** STACK needs wording. Proposed RULES text without a new glossary term: *"A Market Share
  marker that moves onto an occupied space is placed beneath the markers already there; a higher marker ranks
  ahead of the ones beneath it."* Or approve a new term, e.g. **Stack Order** (CLAUDE.md requires sign-off).
- **D3 Cap:** track maximum 20 → 25 (new track art in PnP / TTS / web), or keep 20.
- **D4 Schedule:** S32 (`+3 / +2` at 3–4P) or another way to replace the lost Secrets.
- **D5 Simultaneous moves:** Red (and the Red Signature loss) keeps stack order; in a Phase 5 PR regain the
  marker arrives on top or beneath? (The probe uses "beneath", which makes passing necessary.) Rule on the setup
  stack (last seat on top, mirroring first-player advantage).
- **D6 Version:** ship as v0.52.0 with new `v052` presets after the full SDLC sweep.

## 7. Follow-up (2026-11-25): beneath vs on top, simultaneous Red, Vulnerability tie-break

New arms: **STACKTOP** (the latest arrival goes on top and ranks above; bots value matching as enough, AWARET),
**VTB** (MLB ties go to the lower Vulnerability; players still tied share the better place; SETEC Corp loses
ties). New metrics: *lead changes per game* (the sole effective leader changes hands) and *lead back* (share of
lead changes that return to the previous leader, a proxy for "the covered leader answers").

All arms with CAP25 + S32, 3,000 games per pod:

| 4P | PZ | MC | Sing | Raw top tie | Effective MLB 1st tie | Lead changes/g | Lead back | End spread | Seat spread |
|---|---|---|---|---|---|---|---|---|---|
| R0 (v0.51, no CAP25/S32) | 67.0 | 12.3 | 19.7 | 35.2 | 32.4 | 1.5 | 26% | 4.4 | 1.9 |
| Beneath (STACK) | 69.8 | 14.0 | 15.8 | 24.8 | 0 | 2.2 | 34% | 5.8 | 4.1 |
| On top (STACKTOP) | 73.6 | 10.2 | 15.6 | 28.0 | 0 | 2.9 | 32% | 4.7 | 5.1 |
| Vulnerability (VTB) | 71.8 | 10.8 | 16.7 | 27.0 | 6.9 | 2.2 | 32% | 5.4 | 1.7 |

| 3P | PZ | MC | Sing | Raw top tie | Effective MLB 1st tie | Lead changes/g | Lead back | End spread | Seat spread |
|---|---|---|---|---|---|---|---|---|---|
| R0 | 61.4 | 12.0 | 24.5 | 29.7 | 26.4 | 1.4 | 32% | 3.2 | 2.1 |
| Beneath | 65.1 | 14.1 | 19.4 | 21.6 | 0 | 2.0 | 40% | 4.2 | 1.9 |
| On top | 67.3 | 11.5 | 19.3 | 24.2 | 0 | 2.5 | 41% | 3.6 | 1.5 |
| Vulnerability | 65.5 | 11.9 | 20.5 | 23.4 | 5.8 | 2.0 | 39% | 3.8 | 2.0 |

2P: all three stay within ~3pp of R0; on top is the harshest (PZ 45.3 vs 42.2).

**On top vs beneath.**
* On top gives the most leapfrogging (4P lead changes 2.9/g vs 2.2), as expected: matching a rival is enough.
* But the covered leader does not answer more often (lead back 32% vs 34%). The answer can only come next round,
  and this round's bonus is scored at the end of Phase 6 before the leader gets a turn. Phase 5 is the clockwise
  phase where PR regains happen, so in practice on top means **the later player in turn order wins the tie**.
  That shows up as seat skew (4P seat spread 5.1; a 5pp gap between seats).
* Matching is enough, so players stop at the leader instead of passing: the table stays tighter (end spread 4.7 vs
  5.8, more cubes sharing the top space). PZ is ~4pp higher at 3–4P.
* Beneath keeps the incentive "pass, don't match", spreads the track most, and acting later earns nothing.

**Simultaneous Red needs no turn order.** Every survivor loses the same Red, so markers on one space move together
as a stack and keep their order; markers on different spaces never meet. The only time markers meet during a
simultaneous step is the clamp at `0`, Aegis *Baffle Echo* (one marker moves 1 less), the Red Signature, and Phase 3
face gains. One rule covers all of them and is read straight off the board: *markers that reach the same space at
the same time keep their previous order (the one that was higher stays above).* The arrival rule (beneath or on
top) then only matters when a marker joins a space someone already holds, which is mostly the clockwise Phase 5.

**Vulnerability tie-break.** It works with no stacking at all and fits the theme (the more secure company wins the
tie). But 6–11% of MLB awards still tie (equal Market Share *and* Vulnerability), so it needs a fallback, which is
the cascade you want to avoid. It also adds a second Vulnerability penalty on top of Green. Seat balance is the best
of the three.

**Updated recommendation:** beneath (incumbent holds the space) + CAP25 + S32. Ranking is read from the board with
no tiebreaker lookup, and Red stays simultaneous. On top is the alternative if more leapfrogging is wanted, at the
cost of PZ +4pp, a tighter track and a turn-order edge.

## 8. User decision log

* **2026-11-25 D1 Tie rule: On top (latest arrival ranks above).** Accepted with its costs: PZ about +4pp at 3–4P,
  a tighter track (4P end spread 4.7) and a later-in-Phase-5 seat edge (4P seat spread 5.1, watch item for the
  SDLC sweep). Simultaneous moves use "markers that reach a space at the same time keep their previous order".
* **2026-11-25 D2 Wording:** plain rules text, no new glossary term (e.g. *"A Market Share marker that moves onto an
  occupied space goes on top; a higher marker ranks ahead of those beneath it."*).
* **2026-11-25 D3 Track maximum:** 20 → 25 (starts stay 14 / 18 / 18). Needs new track art in PnP, TTS and web.
* **2026-11-25 D4 Market Leader Bonus:** `+3 / +2` at 3P and 4P; 2P stays `+3 / +1`.
* **2026-11-25 D6 Version:** ship as `v0.52.0` with new `v052` presets after the SDLC sweep.
* Still to settle in the spec (defaults proposed): setup stack has the last seat on top; SETEC Corp (2P) stacks
  like a player when it moves in Phase 4.

**Package for the SDLC:** STACKTOP + CAP25 + S32. Probe numbers (§7): 4P PZ 73.6 / MC 10.2 / Sing 15.6,
3P 67.3 / 11.5 / 19.3, 2P 45.3 / 27.7 / 18.4. Watch items: PZ +3–6pp vs v0.51, 4P seat spread 5.1, company spread.

## 9. Correction (2026-11-25): the S32 / S321 arms were wrong

The principal-engineer spec review found that v0.51 pays the Market Leader Bonus through
`red_secret_payout_by_player_count` (`(3, 1, …)`), while `market_leader_bonus_by_player_count` is `{}`. The S32 /
S321 arms in §3–§7 set the second one. That left the per-round award at `+3 / +1` and added an *extra* end-game
award, so **every S32 / S321 row above is invalid**. The probe now overrides `red_secret_payout_by_player_count`.
Arms without S32 are unaffected.

Corrected re-run (STACKTOP + AWARET + CAP25, 3,000 games per pod):

| | Schedule | Rounds | PZ | MC | Sing | MLB Secrets/g | Winner Secrets | Company spread | Seat spread |
|---|---|---|---|---|---|---|---|---|---|
| 3P v0.51 (R0) | +3/+1 | 8.2 | 61.4 | 12.0 | 24.5 | 17.2 | 11.4 | 15.0 | 2.1 |
| 3P package | +3/+1 | 7.9 | 67.2 | 11.6 | 19.3 | 14.3 | 11.1 | 12.6 | 1.9 |
| 3P package | **+3/+2** | 8.1 | 62.7 | 12.2 | 23.2 | 18.4 | 12.0 | 15.0 | 3.0 |
| 4P v0.51 (R0) | +3/+1 | 8.1 | 67.0 | 12.3 | 19.7 | 21.9 | 12.5 | 11.4 | 1.9 |
| 4P package | +3/+1 | 7.8 | 73.6 | 10.3 | 15.5 | 16.4 | 11.9 | 7.8 | 3.0 |
| 4P package | **+3/+2** | 8.0 | 70.5 | 10.5 | 18.5 | 20.9 | 12.6 | 9.7 | 3.7 |
| 4P package | +3/+2/+1 | 8.2 | 66.6 | 10.6 | 22.2 | 24.8 | 12.6 | 10.5 | 4.0 |
| 2P v0.51 (R0) | +3/+1 | 8.2 | 42.2 | 28.1 | 20.8 | 10.8 | 9.4 | 18.5 | 1.9 |
| 2P package | +3/+1 | 8.1 | 45.3 | 27.7 | 18.4 | 9.5 | 9.1 | 14.6 | 3.6 |

The corrected numbers are better than reported. At 3P the package is close to v0.51. Winner Secrets rise only
+0.1 to +0.6, not +3, so the old watch item (a) is gone. At 4P, `+3 / +2` leaves PZ +3.5pp; `+3 / +2 / +1` is
PZ-neutral (−0.4pp, Singularity +2.5pp). 2P (schedule unchanged) is PZ +3.1pp from stacking and the cap alone.
