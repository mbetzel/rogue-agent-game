# v0.38.0 Secret Faces Package: Balance Assessment (game-designer, 2026-11-08)

Scope: the Phase 49 sweep (`sim_results/v380_secret_faces/`, 1,200 games per cell, roster mixed1), ref1 3P (`ref1/v038_push_nonref_ref1_3p_1200.json`), and 13 targeted probes (600 games per cell, seeds 42.., `--procs 8`, v038_roster; outputs in the session scratchpad, `p*_h-*.json`). No sim, RULES.md, PLAN.md or FINDINGS.md change.

## Verdict: NOT APPROVED (as the v0.38.0 baseline)

The mechanism package works: stranding is low (3%), no seat has a zero-capacity shield round, Total Wipeout is at or under 1% at 3P/4P, rounds are 8.8–9.6, and the ref1 edge is no worse than v0.37. But four guardrail-level problems remain, and no single `[TUNE]` lever probed fixes them:

1. 2P Singularity is 63–82% (guardrail ≤ 48%). Only a three-lever stack reaches 46%, and that stack raises 2P Total Wipeout to 8%.
2. 0 Market Share is a free, stable end state (28–31% of seats). Red is inert there, and the bot that dumps Market Share wins the most.
3. The archetype spread is 41–50 points (v0.37: 27–36). About a third of it is the lever A dump line (a bot artifact); the rest is a rule effect.
4. Yellow is non-viable at 3P/4P (5–15% path win rate), and Company Blue is weak at 4P (20–22%).

Go for the SDLC only after the User rules on the decisions below (mainly D1–D3). A re-tuned candidate can then come back as APPROVED WITH TUNE.

## 1. Evidence

### 1.1 Endings vs guardrails (sweep, 1,200 games)

| P | cell | Singularity | Patient Zero | Total Wipeout | rounds | spread |
|---|---|---|---|---|---|---|
| 2 | v037 base | 47.0 | 20.4 | 7.6 | 9.13 | 26.9 |
| 2 | v038 S3 / S5 | 63.3 / 78.6 | 32.2 / 19.5 | 4.4 / 1.9 | 8.74 / 9.45 | 37.8 / 46.0 |
| 3 | v037 base | 37.7 | 37.5 | 3.9 | 8.88 | 36.1 |
| 3 | v038 S3 / S5 | 50.5 / 68.2 | 49.2 / 31.3 | 0.3 / 0.4 | 8.09 / 9.15 | 51.5 / 51.2 |
| 4 | v037 base | 41.5 | 29.9 | 1.5 | 9.00 | 34.1 |
| 4 | v038 S3 / S5 | 45.2 / 67.4 | 54.8 / 32.6 | 0.0 / 0.0 | 7.92 / 9.06 | 50.1 / 51.7 |

Starting Secrets only trade Singularity for Patient Zero, by about 5–6 points per Secret. At 2P even S3 is 15 points over the guardrail. Note that Market Collapse used to take part of the endings. With it off, Singularity is the default end, so the ≤ 48% guardrail (set under v0.37) is now much harder to meet (see D1).

### 1.2 Archetype drivers (S5, per seat)

| P | bot | win | Secret-face Secrets | faces banked | Blue loss | final MS | ends at MS 0 | win when at MS 0 |
|---|---|---|---|---|---|---|---|---|
| 3 | AdaptiveBalanced | 64 | 14.9 | 7.6 | −6.7 | 2.0 | 58% | 61% |
| 3 | Mixed | 34 | 10.3 | 5.4 | −7.5 | 2.8 | 31% | 24% |
| 3 | Accelerationist | 35 | 10.6 | 5.2 | −8.9 | 3.0 | 14% | 17% |
| 3 | SecOpsTurtle | 29 | 9.5 | 5.3 | −6.4 | 2.4 | 32% | 22% |
| 3 | VentureGreed | 26 | 7.9 | 4.2 | −8.5 | 3.8 | 14% | 16% |
| 3 | RecklessSaboteur | 13 | 7.6 | 4.2 | −7.4 | 2.5 | 28% | 10% |

2P and 4P show the same pattern (AdaptiveBalanced banks 7.5–7.8 faces vs ~5.3, and ends at MS 0 in 58% of games). Its edge is Secret-face volume plus low Blue loss, and it gets there by giving up Market Share. Note that RecklessSaboteur ("keeps every Secret face") banks the fewest faces: keeping a face does not help if you do not own the dice to bank it. Chasing in rerolls is not the driver; which dice a bot owns is.

### 1.3 Attribution probe: lever A off (`bot_pr_push=false`, P1)

| P | AdaptiveBalanced win, push on → off | spread on → off | Singularity on → off |
|---|---|---|---|
| 2 | 76.2 → 68.8 | 41.2 → 30.5 | 78.5 → 78.3 |
| 3 | 65.2 → 51.9 | 49.6 → 37.2 | 64.0 → 65.3 |
| 4 | 54.5 → 40.8 | 49.2 → 33.0 | 66.2 → 65.8 |

**Flag 3 call: mixed.** About 11–16 spread points are the lever A push/dump line, a bot artifact: only AdaptiveBalanced has it, and the line is more effective now that Market Collapse is off. The residual (AdaptiveBalanced still 1.6x fair share at 3P/4P, spread 30–37, still above v0.37) is a rule effect. It comes from committing to the Company colour (Red/Green yield 3 at best vs Blue/Purple 1) together with the fact that 0 Market Share costs nothing.

### 1.4 ref1 (3P, v038 5/5/5, push on non-reference seats)

| metric | ref | rivals |
|---|---|---|
| win | 78.2% (v0.37 13-member portfolio: 78.6%) | — |
| final Secrets | 17.2 | 9.9 |
| final Market Share | 0.36 | 0.60 |
| ends at MS 0 | 82.7% (wins 77.3% of those) | — |
| blocks R / B / G per game | 5.0 / 6.2 / 2.5 | 3.9 / 4.7 / 2.8 |
| endings | Singularity 87%, Patient Zero 13% | |

**Flag 4:** the edge is unchanged from v0.37, so the reference search does not find a new exploit. But almost every seat ends at 0 Market Share (avg MS 0.36–0.60 out of 12) and the ref wins there 77% of the time. The 12-point track mainly sets the Red yield tier early on. By the end of the game Market Share does not matter, apart from a 1–2 point Market Leader Bonus that is shared among players tied at 0.

### 1.5 Flag 6: is the Market Share dump degenerate?

Yes, as a structural weakness (not a kamikaze trigger, since no end is triggered). Once a player is at 0:
- unblocked Red cubes do nothing to them (Market Share floors at 0), so all their Any shields go to Blue/Green;
- their Red dice still pay `+$2` on F2–F4. Only the Red Secret face is dead (yield 0).

So Red pressure stops on the very players it has already beaten. That hurts the shared-threat pillar ("Red lowers Market Share, regained via Public Relations"). It is the main reason Red cube exits rise with Secrets (more survival) while the Red share of blocks falls. A larger Market Leader Bonus (P10: 4 / 4-2) barely helps: spread −4 to −5, MS 0 seats −2 to −5 points.

### 1.6 Flag 5: Company / path

| P | Co Red | Co Blue | Co Green | path red | path blue | path green | path yellow |
|---|---|---|---|---|---|---|---|
| 2 S5 | 56.0 | 46.9 | 47.2 | 60.9 | 50.4 | 53.8 | 31.3 |
| 3 S5 | 37.0 | 32.4 | 30.8 | 46.1 | 36.5 | 40.2 | 13.2 |
| 4 S5 | 31.4 | 21.7 | 22.0 | 37.7 | 23.5 | 29.0 | 5.3 |

Red is the best path at every player count (1.4–1.5x fair share). Red tiers 2/2/1/0 (P3) cut the 4P Red path to 35% and Co Red to 25% without hurting Blue. Yellow (no Secret face) cannot convert its Money into Secrets: B2 `$4 → 1 Secret` is used 0.05 times per seat. This is a face-design gap, not a bot gap: VentureGreed and Reckless both fall with it.

### 1.7 Probe table (600 games; base = v038_roster S5 unless stated)

| # | override | P | Singularity | PZ | TW | rounds | AB | spread | path R / Y | Co R / B | MS 0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P0 | base | 2/3/4 | 78.5/64.0/66.2 | 19.7/35.3/33.8 | 1.8/0.7/0.0 | 9.5/9.0/9.0 | 76/65/55 | 41/50/49 | 64,35 / 48,14 / 39,5 | 57,47 / 38,33 / 33,21 | 31/28/28 |
| P1 | bot_pr_push=false | 2/3/4 | 78.3/65.3/65.8 | 18.3/34.0/34.2 | 3.3/0.7/0.0 | 9.5/9.1/9.0 | 69/52/41 | 31/37/33 | 61,41 / 45,14 / 39,8 | 57,48 / 36,33 / 34,20 | 26/25/23 |
| P2 | Red tiers 9:2 / 5:2 / 1:1 / 0:0 | 2/3/4 | 75.0/62.0/61.0 | 23.3/36.8/38.8 | 1.7/1.2/0.2 | 9.4/9.1/8.9 | 72/63/52 | 38/50/46 | 55,30 / 42,8 / 35,7 | 52,48 / 30,37 / 25,24 | 29/30/28 |
| P3 | Green base 2 | 2/3/4 | 71.5/59.0/57.7 | 26.5/40.3/41.8 | 2.0/0.7/0.5 | 9.3/8.9/8.8 | 67/62/57 | 35/50/47 | 70,35 / 50,18 / 44,9 | 59,54 / 39,43 / 37,27 | 30/28/27 |
| P6 | Purple yield 0 | 2/3/4 | 73.0/59.2/59.3 | 23.8/40.7/40.5 | 3.2/0.2/0.2 | 9.3/8.9/8.8 | 72/57/55 | 45/47/48 | 64,26 / 43,16 / 41,8 | 55,50 / 37,32 / 32,20 | 30/29/26 |
| P7 | 2P Corruption capacity 6 (flat) | 2 | 75.0 | 21.8 | 3.2 | **12.0** | 71 | 41 | 61,26 | 52,49 | 41 |
| P5 | 2P S3 (capacity map ignored, see note) | 2 | 63.3 | 33.0 | 3.7 | 8.8 | 73 | 39 | 60,27 | 55,47 | 28 |
| P8 | 2P S3 + capacity 6 + Green 2 | 2 | 53.5 | 41.8 | 4.7 | 10.8 | 80 | 47 | 60,24 | 60,50 | 36 |
| P9 | 2P S3 + Green 2 + Purple 0 | 2 | **46.0** | 45.8 | **8.2** | 8.3 | 79 | 48 | 60,37 | 59,55 | 28 |
| P10 | MLB 2P 4 / 3–4P 4-2 | 2/3/4 | 76.5/61.5/61.8 | 21.2/38.0/38.2 | 2.3/0.5/0.0 | 9.4/9.0/8.9 | 72/61/53 | 36/46/47 | 62,29 / 45,16 / 41,5 | 55,47 / 36,35 / 33,21 | 26/26/24 |
| P11 | 3–4P S4 + Green 2 + MLB 4-2 | 3/4 | 49.5/46.5 | 50.0/53.5 | 0.5/0.0 | 8.4/8.3 | 61/52 | 45/41 | 48,15 / 42,8 | 40,41 / 37,27 | 22/21 |

Tooling note: `--set corruption_track_capacity_by_player_count={"2":5,...}` is **silently ignored** (P4 matched P0 bit for bit), probably a str-vs-int key mismatch. `corruption_track_flat_capacity` works. `starting_secrets_by_player_count` and `market_leader_bonus_by_player_count` string keys do apply. This should go to the senior-engineer.

Probe noise is about ±2 points (600 games, p ~ 0.5) for endings and ±4–6 points for archetype rates (n ≈ 120–360 seats).

## 2. Ranked tuning levers

1. **Give 0 Market Share a cost** (flags 3, 4, 6). This is the root of the dump line and most of the residual AdaptiveBalanced edge. No existing lever does it: P10 (larger MLB) gives only −4 spread. Options, all needing User approval: (a) bring Market Collapse back as an end trigger at 0 (it was turned off on purpose; it would also absorb Singularity share, which helps flags 1–2); (b) unblocked Red at 0 Market Share costs 1 Secret (no income denial, but it is close to the deprecated *Unpaid Ransom Leak*, so it needs explicit approval); (c) Red Secret face yield stays at 1 at Market Share 0 (weak, since it rewards being at 0). Recommend (a), probed at once.
2. **2P pacing stack** (flag 1): S3 + Green base 2 + Purple yield 0 at 2P (P9: Singularity 46%, rounds 8.3) meets the guardrail but breaks 2P Total Wipeout (8.2%, v037 had 7.6). P8 (capacity 6) lengthens games. Alternatively, re-baseline the guardrail (D1).
3. **Green base 2** (P3): −5 to −9 Singularity at all player counts, and Co Blue/Green rise at 2P/3P (54/43). Cheap. But it worsens the Red path at 2P (70%), so pair it with lever 4.
4. **Red tiers 2/2/1/0** (P2): Red path 64→55 (2P) and 39→35 (4P), Co Red 25–30 at 3P/4P, Singularity −3 to −5. Recommended together with lever 3.
5. **3P/4P S4 + Green 2 + MLB 4-2** (P11): Singularity 47–50%, Patient Zero 50–54%, rounds 8.3–8.4, Total Wipeout ~0. A workable 3P/4P pacing point. Spread is still 41–45 until lever 1 lands.
6. **Yellow**: needs a face or Variant change (e.g. Y-face `+$1 & +1 Market Share`, or a cheaper B2-style Money→Secret conversion). Under the current tables no numeric lever exists; this needs a design pass and User approval.
7. **Bot (not rules):** when assessing rules, either give the lever A dump to every archetype or turn it off for all of them. Right now it inflates AdaptiveBalanced by 13–16 points at 3P/4P (P1).

## 3. Decisions for the User

1. Is the 2P Singularity ≤ 48% guardrail still the target now that Market Collapse is off (it was set under v0.37, when Collapse took part of the endings)? Or should it be re-baselined, for example to ≤ 60% with Patient Zero ≥ 30%?
2. Should 0 Market Share carry a cost? Pick one to probe: (a) bring Market Collapse back as an end trigger (recommended); (b) unblocked Red at 0 Market Share costs 1 Secret each (resembles the deprecated *Unpaid Ransom Leak*); (c) none, and accept the Market Share dump as a legitimate line.
3. Approve the Red Secret face yield tiers 2/2/1/0 (was 3/2/1/0) and Green base 2 (was 3) as the next candidate `[TUNE]` baseline?
4. Starting Secrets per player count for the next candidate: 2P 3 / 3P 4 / 4P 4 (probes P5, P9, P11)? Or should 2P use the P9 stack (Purple yield 0), accepting about 8% Total Wipeout?
5. Is the Yellow fuel die allowed a design change (a Market Share or Secret-conversion face, or Y-Variant retargets) to fix 5–15% Yellow path win rates? Any new face wording will use existing glossary terms only.
6. For rule sweeps, should the lever A push/dump line be given to all archetypes or turned off for all, so the archetype spread measures rules rather than one bot's extra line?
7. Should the `corruption_track_capacity_by_player_count` `--set` override bug go to the senior-engineer before the next sweep?

---

# Candidate 2: `--config v038b` (game-designer, 2026-11-08)

`v038b` is v038 plus Market Collapse on, starting Secrets 3 / 4 / 4, Red tiers 11 / 7 / 3 / 0 (yield 3 / 2 / 1 / 0), Yellow profile `V038_YELLOW_MS`, and lever A off for all bots (FINDINGS §43, spec §14.3). Probes: 600 games per cell, seeds 42.., roster mixed1, `--procs 8`. Outputs are in the session scratchpad under `c2/` (`q*.json`, `r*.json`). Noise is about ±2 points on endings and ±4–6 points on archetype and path rates.

## Verdict: APPROVED WITH TUNE

Adopt candidate 2 (C2) = **v038b + starting Market Share 14 at all player counts + Market Leader Bonus 2P `+4` / 3–4P `+4, +2`** (probe R1). Green base stays 3, the slot cap stays off, and Yellow stays `V038_YELLOW_MS`; the profile choice is open (D4). Two items stay open as watch items and are not blockers: Yellow is weak at 3P/4P, and 4P rounds sit at 7.94, just under 8.

## C2.1 Endings, rounds, spread

| # | cell | P | Market Collapse | Singularity | Patient Zero | Total Wipeout | rounds | spread | AB | RS | MS 0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Q0 | v038b | 2 | 40.8 | 26.5 | 29.3 | 3.3 | **7.95** | 42 | 71 | 29 | 19 |
| Q0 | v038b | 3 | 44.0 | 20.0 | 35.5 | 0.5 | **7.97** | 37 | 51 | 14 | 17 |
| Q0 | v038b | 4 | **48.5** | 19.2 | 32.3 | 0.0 | **7.81** | 36 | 45 | 9 | 13 |
| Q1 | Green base 2 | 2/3/4 | 38.5/37.5/42.8 | 23.7/21.3/16.8 | 34.0/40.5/40.2 | 3.8/0.7/0.2 | 7.79/7.86/7.66 | 37/29/35 | 70/47/44 | 33/19/9 | 19/17/13 |
| Q2 | Yellow MS_ALT | 2/3/4 | 41.3/43.5/46.7 | 26.2/20.7/18.8 | 28.8/34.8/34.5 | 3.7/1.0/0.0 | 7.93/7.99/7.76 | 40/31/35 | 71/47/42 | 32/16/8 | 20/18/14 |
| Q3 | slot cap 2 | 2/3/4 | 40.5/43.7/48.3 | 26.8/20.3/19.7 | 29.3/35.5/32.0 | 3.3/0.5/0.0 | 7.95/7.98/7.82 | 41/35/36 | 71/50/45 | 30/14/9 | 19/17/13 |
| Q4 | Red tiers 9/5/1 | 2/3/4 | 42.2/46.7/48.7 | 27.7/21.5/20.3 | 27.3/31.8/31.0 | 2.8/0.0/0.0 | 8.01/7.97/7.83 | 41/32/36 | 69/48/43 | 28/16/8 | 21/17/14 |
| Q5 | Market Share start 14 | 2/3/4 | 35.3/38.8/40.3 | 33.2/27.8/26.3 | 28.2/33.2/33.3 | 3.3/0.2/0.0 | 8.20/8.17/8.04 | 43/26/36 | 68/43/43 | 25/17/8 | 16/14/12 |
| Q6 | MLB 4 / 4-2 | 2/3/4 | 35.2/36.0/36.0 | 27.3/23.2/20.8 | 33.5/39.7/43.2 | 4.0/1.2/0.0 | 8.01/7.97/7.66 | 33/27/31 | 63/45/40 | 30/18/9 | 18/14/12 |
| **R1** | **MS 14 + MLB 4 / 4-2 (C2)** | 2/3/4 | **29.5/32.2/31.0** | **34.8/30.3/26.7** | 32.2/37.0/42.2 | 3.5/0.5/0.2 | **8.24/8.25/7.94** | 41/31/32 | 69/48/42 | 28/16/11 | 14/12/10 |
| R2 | R1 + Yellow MS_ALT | 2/3/4 | 29.2/31.8/32.2 | 36.3/28.2/26.0 | 31.3/39.2/41.7 | 3.2/0.8/0.2 | 8.26/8.26/7.99 | 39/29/31 | 66/45/40 | 27/17/9 | 13/12/10 |

Findings:
1. **Market Collapse is too dominant in v038b** (41–49%, the leading ending at every player count), and games run short (7.8–8.0 rounds, under the 8–11 band at all three player counts). The 11 / 7 / 3 thresholds are not the main cause: with Red tiers back at 9 / 5 / 1 (Q4), Market Collapse does not move (±2 points). The cause is that Market Share starts at 12, and Red cube exits strip it to 0 by round 7–8. **Starting Market Share 14 (Q5) and a larger Market Leader Bonus (Q6) each cut Market Collapse by 5–12 points. Together (R1) they bring it to 30–32%**, with a balanced three-way split and rounds 7.9–8.3.
2. **The 2P Singularity ≤ 48% guardrail is met with margin** (26.5% in v038b, 34.8% in C2). The first-sweep 2P problem is solved by Market Collapse coming back.
3. **The slot cap of 2 per round is inert** (Q3 is within noise of Q0). It never binds: unblocked Green cubes per seat per round rarely exceed 2. Keep it off.
4. **Green base 2 is rejected**: the Green path collapses to 21% at 3P and 13% at 4P (Co Green 22 / 14). Keep 3.
5. **Spread.** AdaptiveBalanced 69 / 48 / 42 at 2P / 3P / 4P is now within about 1.4–1.7x of fair share, down from 2.0–2.3x in the first sweep. The spread is 31–41, still above the v0.37 band (27–36) at 2P. RecklessSaboteur is the floor (9–28%), the same as in v0.37.

## C2.2 Paths and Companies (v038b base, Q0, and C2)

| P | cell | path R | path G | path B | path Y (seats) | Co R | Co B | Co G |
|---|---|---|---|---|---|---|---|---|
| 2 | Q0 | 53 | 61 | 54 | 25 (83) | 54 | 45 | 51 |
| 3 | Q0 | 41 | 38 | 29 | 16 (133) | 34 | 33 | 33 |
| 4 | Q0 | 36 | 27 | 19 | 10 (217) | 33 | 18 | 24 |
| 2 | R1 | 60 | 53 | 61 | 31 (86) | 57 | 47 | 46 |
| 3 | R1 | 44 | 33 | 32 | 20 (157) | 39 | 31 | 30 |
| 4 | R1 | 42 | 22 | 18 | 10 (216) | 35 | 18 | 21 |

Companies are now balanced at 3P (30–39). At 4P, Red is still above Blue and Green (35 vs 18–21), and the Blue path is weak at 4P.

## C2.3 Why Yellow is still weak (Q0, per seat by path)

| P | path | win | final Secrets | final Market Share | Secret-face Secrets | MLB |
|---|---|---|---|---|---|---|
| 3 | yellow | 16 | 5.9 | **2.6** | 6.6 | 1.05 |
| 3 | red | 41 | 8.3 | 4.4 | 9.1 | 1.29 |
| 3 | green | 38 | 8.6 | 3.4 | 9.9 | 1.18 |
| 4 | yellow | 10 | 5.9 | 3.3 | 6.2 | 0.95 |
| 4 | red | 36 | 8.7 | 5.0 | 9.2 | 1.17 |

1. **Yellow is the Market Share die but ends with the lowest Market Share.** Its `+Market Share` is Phase 3 income, and shared Red exits strip it again in Phase 4. Red-path seats end higher because the Red tier pushes their bots to block Red.
2. **Market Share only turns into Secrets through the Market Leader Bonus (≤ 2–4) and the Red yield.** A Yellow-heavy seat owns few Red dice, so its Market Share has almost no Secret value, and Yellow has no Secret face. The result is about 2.5–3 fewer face Secrets than other paths, which is the whole win gap.
3. **Probable bot selection bias.** The spec §9 purchase scoring values Yellow as Money, and the Yellow path is mostly VentureGreed and RecklessSaboteur, the two weakest bots. MS_ALT (Q2, R2) does not move this beyond noise: 4P Yellow 10 → 11–14.
4. Possible levers (rules, User call): Yellow seat counts toward the Red yield tier ("+1 tier when you own ≥ 1 Yellow"; wording TBD, glossary-checked), or a Yellow `★` Variant that converts Market Share into a Secret. Bot lever: score Yellow by Market Collapse avoidance plus Market Leader Bonus value, then re-measure before any rule change.

## C2.4 Recommended candidate config

`--config v038b --set 'market_share_start_by_player_count={"2":14,"3":14,"4":14}' --set 'market_leader_bonus_by_player_count={"2":[4],"3":[4,2],"4":[4,2]}'`. Green base 3, slot cap off, Red 11 / 7 / 3 / 0, Yellow `V038_YELLOW_MS`, starting Secrets 3 / 4 / 4.

Next steps: confirm with a 1,200-game sweep at 2P / 3P / 4P plus the ref1 3P edge check, then run a 4P rounds check (if 4P stays under 8, try Market Share 15 at 4P only).

## C2.5 Decisions for the User

1. Adopt C2: v038b + starting Market Share 14 (all player counts) + Market Leader Bonus 2P `+4` / 3–4P `+4, +2`, as the next `[TUNE]` baseline for the 1,200-game confirm sweep and the ref1 check?
2. Keep Green base 3 (Green base 2 collapses the Green path at 3P/4P)?
3. Remove or keep the `glitched_slots_per_round_cap` lever? It is inert at cap 2 (recommend: keep it in code, default off, and drop it from the rules).
4. Yellow profile: keep `V038_YELLOW_MS` (`+2 Market Share`) or switch to `V038_YELLOW_MS_ALT` (`+$1 & +1 Market Share`)? They are within noise of each other; ALT is slightly better at 4P.
5. Yellow weakness: first fix the bot purchase scoring (value Yellow by Market Collapse avoidance and Market Leader Bonus) and re-measure, or approve a rules probe that links Yellow to the Red yield tier or a Market Share→Secret Variant (any new wording to be glossary-checked)?
6. Accept a 4P average of 7.9 rounds (just under the 8–11 band), or probe starting Market Share 15 at 4P only?
7. Accept the 2P archetype spread of about 41 points (AdaptiveBalanced 69%) as within bot noise for now, to be re-checked by ref1 at 2P?

---

# C2 confirm (game-designer, 2026-11-08)

Sources: `sim_results/v380_secret_faces/c2/` (1,200 games per cell; ref1 2P and 3P with lever A off, matching the preset). Probes: 600 games each, in the session scratchpad under `c3/`. T1 = lever A on for all bots; T2 = 4P Market Share 15; T3 = Market Leader Bonus 3P/4P `+3, +1`; T4 = Red yield 2 / 2 / 1 / 0 at 11 / 7 / 3 / 0. A further 3P ref1 run (600 games) had lever A on for the non-reference seats.

## Verdict: APPROVED WITH TUNE

C2 meets every pacing guardrail except 4P rounds (7.92 vs 8). Market Collapse is back to a healthy share (29–35%, v0.37: 21–27%), and the 2P Singularity guardrail holds (33.8%). The ref1 rise is a bot skill gap, not a rules exploit (§1). Two small `[TUNE]` items are recommended before the baseline is written into RULES.md: Market Share 15 at 4P, and Red yield 2 / 2 / 1 / 0. Yellow stays a watch item, to be fixed on the bot side first.

## 1. ref1 rise (3P 84.1%, 2P 92.4%; switch-off baseline 78.6%)

| 3P ref1 | ref | rivals |
|---|---|---|
| win | 84.1 | 8.0 |
| Red blocked per game | 6.29 | 4.36 |
| Public Relations level | 1.23 | 0.15 |
| final Market Share | 2.69 | 1.69 |
| MLB 1st place | 75% | 33% |
| MLB Secrets | 3.33 | 2.11 |
| final Secrets | 17.4 | 9.6 |
| ends at MS 0 | 22% | 32% |

| Market Collapse trigger (games / ref win %) | 2P | 3P |
|---|---|---|
| rivals only | 473 / 98% | 564 / 90% |
| ref with rivals | 314 / 86% | 292 / 76% |
| ref alone | 64 / 69% | 44 / 50% |
| all Market Collapse endings | 71% | 75% |

- **Not a kamikaze line or a rules exploit.** The ref seat alone triggers only 4–5% of games and wins those at no more than its normal rate.
- **The edge is a skill gap.** The ref is the only seat that blocks Red and climbs the Public Relations Track. Its rivals (lever A off) fall to 0 and end the game by Market Collapse while the ref leads.
- **Lever A barely moves the gap.** Turning it on for the rivals (600 games) drops the ref only to 79.2% (−5 points), with the rivals' Public Relations level going 0.15 → 0.31.
- **The Market Leader Bonus adds about 1.2 Secrets to the ref**, but that is a small part of its +7.8 Secret lead.
- **Rule note.** C2 makes Market Share defence matter again, which was the intent. The scripted bots just do not defend it, which is also why Market Collapse rises to 71–75% whenever a competent seat is present. With the rivals on lever A it is still 75% (448 of 600).

## 2. Red Company / path lead (3P/4P)

| cell | P | Co R / B / G | path R / G / B / Y | Market Collapse | Singularity | Patient Zero | rounds | spread |
|---|---|---|---|---|---|---|---|---|
| C2 1,200 | 3 | 39 / 30 / 31 | 44 / 38 / 29 / 21 | 32.8 | 27.4 | 39.6 | 8.16 | 38 |
| C2 1,200 | 4 | 34 / 20 / 21 | 41 / 22 / 20 / 12 | 34.6 | 25.3 | 39.9 | 7.92 | 33 |
| T4 Red 2/2/1/0 | 3 | 30 / 31 / 38 | 39 / 49 / 34 / 18 | 30.3 | 23.8 | 45.3 | 8.09 | 39 |
| T4 Red 2/2/1/0 | 4 | 27 / 23 / 25 | 34 / 29 / 23 / 11 | 31.3 | 25.2 | 43.5 | 7.83 | 32 |
| T2 4P MS 15 | 4 | 34 / 19 / 22 | 39 / 23 / 21 / 12 | 29.8 | 29.3 | 40.8 | **8.01** | 32 |
| T3 MLB 3,1 | 3/4 | 38/34 / 33/19 / 29/22 | 44/38 / 32/26 / 32/24 / 21/11 | 34.7/35.8 | 27.3/25.3 | 37.7/38.8 | 8.16/7.96 | 32/36 |
| T1 lever A all | 3/4 | 40/32 / 29/21 / 31/22 | 47/40 / 39/25 / 24/22 / 20/9 | 33.2/34.7 | 26.8/23.0 | 39.8/42.3 | 8.16/7.89 | **52/47** |

- **The Red lead is a rule effect.** The Red face yield of 3 at 11+ Market Share stacks with Red F1 `+1 Market Share`, so a Red seat both protects its tier and scores it.
- **T4 fixes the Company lead** (3P 30–38, 4P 23–27). It shifts the 3P lead to the Green path (49%), so watch Green.
- **Lever A on for all bots is rejected.** It widens the spread to 47–52 (AdaptiveBalanced 55–66%), confirming the §43 decision.

## 3. Yellow (3P 20.8%, 4P 12.1%)

Same diagnosis as C2.3. Yellow seats still end with low Market Share and own no Secret face. No rules probe moved Yellow beyond noise (T1–T4: 9–21%). The Yellow seats are mostly the two weakest bots (VentureGreed, RecklessSaboteur), and spec §9 scores Yellow as Money. Fix the bot scoring first, then re-measure. A rules change for Yellow is premature.

## 4. Market Collapse 29–35%

This is acceptable as an ending in the roster sweep: it is in a balanced three-way split with Singularity and Patient Zero, and Total Wipeout is ≤ 3.4%. Its 71–75% share in ref1 comes from the rival bots' weak defence (§1), not from the rules. Ending shares should be read from roster sweeps, not ref1 cells.

## 5. 4P rounds 7.92

T2 (Market Share 15 at 4P only) gives 8.01 rounds and Market Collapse 29.8%, with everything else within noise. Recommended.

## 6. Archetype spread

The spread is 36 / 38 / 33 at 2P / 3P / 4P (v0.37: 27 / 36 / 34). It is at the v0.37 level at 3P/4P and higher at 2P (AdaptiveBalanced 69%, RecklessSaboteur 33%). T3 (MLB `+3, +1`) trims the 3P spread to 32 with no pacing cost. It is optional and inside noise at 4P.

## 7. Recommended baseline (C2.1)

v038b + Market Share start 2P 14 / 3P 14 / 4P **15** + Red Secret face yield **2 / 2 / 1 / 0** at 11 / 7 / 3 / 0. Everything else stays as in C2. Confirm with a 1,200-game sweep at 2P / 3P / 4P plus ref1 at 3P before the SDLC writes RULES.md.

## 8. Decisions for the User

1. Accept the ref1 rise (3P 84.1%, 2P 92.4%) as a bot skill gap and not a rules exploit (ref-alone Market Collapse is 4–5% of games, and lever A on for the rivals only lowers the ref to 79%)? Should the ref1 baseline for v0.38 be reset to the C2 values?
2. Adopt Red Secret face yield 2 / 2 / 1 / 0 (thresholds 11 / 7 / 3 / 0 kept) to remove the Red Company lead at 3P/4P, and watch the Green path (49% at 3P)?
3. Adopt starting Market Share 15 at 4P only (rounds 7.92 → 8.01)?
4. Keep the Market Leader Bonus at 3–4P `+4, +2`, or trim it to `+3, +1` (3P spread 38 → 32, otherwise within noise)?
5. Yellow: approve a bot-only fix first (score Yellow by Market Collapse avoidance and Market Leader Bonus value instead of Money), then re-measure before any Yellow rules change?
6. Accept a 2P archetype spread of about 36 (v0.37: 27) for the v0.38.0 baseline?
7. Run the C2.1 confirm sweep (1,200 games, 2P / 3P / 4P plus ref1 3P), then hand it to the SDLC for RULES.md, PnP and web sync?

---

# Red shared payout (§43.4 model; game-designer, 2026-11-09)

**Model.** The engine does not support this rule yet, so it is modelled as a scratchpad monkeypatch over `v038b`. The model (`scratchpad/rp/model.py`, outputs `rp/v*.json`) wraps `secret_faces.bank`, `end_game.evaluate_end_game` and the Yellow die factory. No repo code was edited. All variants run on C2 (v038b, Market Share 14 / 14 / 15), with the Market Leader Bonus removed and the `v2.0` comparison removed. 600 games per cell, seeds 42.., roster mixed1.

Rule as modelled:
- Each Red die whose Secret is banked advances **the counter** by 1. Every *n* steps, **all survivors score by Market Share place**: 1st `3`, 2nd `1`, others `0` Corporate Secrets, ties sharing the better place.
- One more payout fires at game end, except on Market Collapse or a Total Wipeout.
- "Owner" is the Red die owner's own reward per banked die (replaces the 3 / 2 / 1 / 0 tiers).
- "Perceived 2" means the bots value a Red Secret face at 2 (owner 1 + their share of the payout) instead of the owner reward alone. Without it the bots ignore Red and the rule is measured on a Red-free game (V1 vs V5).
- The Yellow variant (`Y+`) changes Yellow F3 `+$3` to `+$1 & +1 Market Share`. It uses existing terms only.

**Limits:**
- The bots do not model the payout when they block or climb the Public Relations Track (their Market Share valuation was built for the Market Leader Bonus, which is now 0). So Market Collapse is probably **overstated** here.
- ref1 is **not feasible**: the reference bot's rollout clones would share the global counter.

## 1. Results

| # | variant | P | MC | Sing | PZ | rounds | spread | Co R / B / G | path R / B / G / Y | MS 0 | Red banked / game | payouts / game (end) | fired by winner |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| V0 | C2 baseline (MLB 4 / 3-1) | 2/3/4 | 28/35/34 | 34/27/29 | 33/38/38 | 8.20/8.16/8.06 | 42/32/37 | 60,45,45 / 38,33,29 / 36,19,20 | 56,60,52,35 / 44,32,32,21 / 39,21,23,16 | 13/13/9 | — | — | — |
| V1 | owner 1, n 2 | 2/3/4 | 45/47/46 | 29/26/25 | 23/27/29 | 8.07/8.13/8.05 | 32/33/35 | 41,54,54 / 26,37,37 / 23,24,27 | 36,53,59,42 / 16,37,44,20 / 18,26,33,10 | 20/15/14 | 1.3/1.8/2.7 | 1.0/1.2/1.7 (0.5) | 52/30/32% |
| V2 | owner 0, n 2 | 2/3/4 | 40/42/40 | 25/22/21 | 32/36/39 | 7.87/7.88/7.77 | 22/40/35 | 35,58,56 / 20,40,39 / 15,27,32 | 24,55,63,36 / 7,42,45,15 / 9,26,34,12 | 18/13/12 | 0.5/0.6/0.9 | 0.7/0.8/0.9 (0.6) | 26/12/16% |
| V3 | owner 1, n 1 | 2/3/4 | 48/51/51 | 30/30/31 | 18/19/18 | 8.24/8.37/8.42 | 31/33/36 | 44,54,52 / 32,35,33 / 26,25,24 | 43,53,59,35 / 26,40,41,20 / 27,26,30,11 | 20/16/14 | 1.3/1.9/2.9 | 1.8/2.4/3.4 (0.5) | 53/35/32% |
| V4 | V1 + Money 2 / 1 | 2/3/4 | 46/48/45 | 29/25/27 | 23/27/28 | 8.08/8.12/8.09 | 33/30/33 | 45,52,53 / 26,36,38 / 24,25,27 | 41,54,60,43 / 14,35,43,19 / 22,25,32,11 | 19/16/13 | 1.4/1.9/2.7 | 1.1/1.2/1.7 | 58/31/34% |
| V5 | V1 + perceived 2 | 2/3/4 | 45/48/45 | 28/26/28 | 24/26/27 | 8.05/8.14/8.08 | 31/29/32 | 41,54,55 / 26,35,38 / 23,25,26 | 39,55,57,35 / 28,35,45,15 / 25,29,31,11 | 19/15/14 | 1.8/2.5/3.9 | 1.2/1.6/2.2 | 56/39/31% |
| V6 | V5, n 3 | 2/3/4 | 43/46/42 | 27/23/26 | 27/31/32 | 8.01/8.05/7.99 | 29/32/28 | 41,53,56 / 24,35,40 / 22,25,28 | 39,55,59,35 / 25,39,47,14 / 24,27,33,10 | 20/15/14 | 1.7/2.5/3.8 | 0.9/1.1/1.5 | 56/36/32% |
| V7 | V5 + Y+ | 2/3/4 | 42/45/43 | 31/29/31 | 24/26/26 | 8.13/8.18/8.16 | 30/27/30 | 43,54,53 / 27,35,38 / 22,26,27 | 40,55,57,37 / 26,33,43,21 / 24,25,32,13 | 19/14/14 | 1.8/2.6/3.9 | 1.3/1.6/2.3 | 54/40/31% |
| V10 | owner 1, perceived 2, n 1/1/2 | 2/3/4 | 48/52/45 | 31/30/28 | 18/17/27 | 8.27/8.38/8.08 | 36/32/32 | 44,54,51 / 32,33,35 / 23,25,26 | 45,56,57,27 / 36,35,42,15 / 25,29,31,11 | 20/16/14 | 1.8/2.7/3.9 | 2.3/3.1/2.2 | 55/40/31% |
| V8 | V10 + Y+ | 2/3/4 | 46/50/43 | 34/34/31 | 17/16/26 | 8.35/8.44/8.16 | 31/27/30 | 44,54,51 / 33,33,34 / 22,26,27 | 41,57,56,41 / 36,32,38,23 / 24,25,32,13 | 19/14/14 | 1.9/2.7/3.9 | 2.4/3.2/2.3 | 54/40/31% |
| V11 | V8 + MS 15 / 15 / 16 | 2/3/4 | 41/46/39 | 39/38/34 | 18/16/27 | 8.45/8.57/8.25 | 26/27/30 | 46,53,51 / 34,33,34 / 21,26,28 | 42,61,56,41 / 34,33,37,24 / 23,27,32,13 | 16/15/13 | 1.9/2.7/4.0 | 2.4/3.3/2.4 | 54/40/29% |
| V9 | V8 + MS 16 / 16 / 17 | 2/3/4 | 36/41/34 | 44/42/39 | 18/16/27 | 8.55/8.68/8.34 | 25/25/31 | 46,52,52 / 33,34,33 / 21,26,28 | 45,63,54,39 / 36,33,35,24 / 24,25,32,13 | 14/13/11 | 1.9/2.8/4.0 | 2.5/3.4/2.4 | 55/39/30% |
| **V12** | **V9 at 4P with n 1** | 4 | 38 | 44 | 18 | 8.69 | 28 | 27,24,24 | 30,25,26,16 | 12 | 4.3 | 4.9 (0.6) | 35% |
| V13 | V12 package without Y+ | 2/3/4 | 38/41/39 | 41/41/42 | 18/18/18 | 8.47/8.65/8.64 | 34/33/31 | 47,53,50 / 31,35,34 / 28,25,22 | 50,65,57,26 / 39,35,40,13 / 32,28,27,13 | 15/14/12 | 1.8/2.7/4.2 | 2.4/3.3/4.8 | 56/41/36% |

Per-seat Secrets at V8 (2P / 3P / 4P): payout 5.4 / 6.0 / 3.4. That is 2–4x the Market Leader Bonus it replaces (2.3 / 1.6 / 1.3). Winner Secrets are 13.5 / 16.5 / 14.5 (C2: 11.0 / 12.1 / 13.7).

## 2. Findings

1. **Red banking volume is the binding constraint.** Only 1.3–4.3 Red dice are banked per game: Red is a fraction of the dice pool, and a Secret face shows on 1 face in 6. *n* = 2 gives just 1.0–1.7 payouts, half of them the end payout. **n = 1 at every player count** is the only setting that makes the counter a real pacing device (V12/V13: 2.4 / 3.3 / 4.8 payouts per game, about 0.6 of them at the end). n = 3 (V6) is nearly inert.
2. **Owner +1 is required.** With owner 0 (V2), nobody buys Red: Red banked 0.5–0.9, Red path 7–24%, Co Red 15–35%. The rule then only rewards Market Share, and Red disappears as a die. Owner +1 keeps Red alive, and with bots that value the payout ("perceived 2") Co Red sits at 27–47%.
3. **The Red Company lead is gone.** Co Red is 21–47 vs Blue/Green 24–54 (C2: Red led by 8–16 at 3P/4P). At 2P, Red now trails (44–47 vs 50–54). That is acceptable at 2P noise (±6) but is a watch item. With n 2 at 4P, Co Red falls to 21–23; with n 1 it is 27–28 (V12/V13).
4. **Who triggers.** The eventual winner fires 54–56% of payouts at 2P, about 40% at 3P (fair 33%) and 31–36% at 4P (fair 25%). That is a mild leader tilt, not a runaway: a seat that fires a payout is usually *not* 1st in Market Share, because Red-owning seats lose Market Share like everyone else.
5. **Secrets + Money (V4) changes nothing measurable** (≤ 3 points everywhere). Keep the payout in Secrets only; that is simpler, and the `v2.0` comparison folds away cleanly.
6. **Market Collapse rises to 38–52%** when the Market Leader Bonus is removed (the bonus was what the bots defended Market Share for). Starting Market Share +2 (V9/V12: 16 / 16 / 17) brings it to 34–41%, but moves Singularity to 39–44%: 2P 44%, inside the ≤ 48% guardrail. Rounds 8.3–8.7, inside the band. Patient Zero drops to 16–18% at 2P/3P because payouts inflate Secrets. This is the main cost of the package; starting Secrets 3 / 4 / 4 may now be one too high (D5).
7. **Archetype spread improves** to 25–31 (C2: 32–42). AdaptiveBalanced 62–65% at 2P (C2: 74%) and 41–48% at 3P/4P.
8. **Market Share 0 seats** are 11–14% (C2: 9–13%), essentially unchanged.
9. **Yellow.** The rule alone does not fix Yellow (V13: 26 / 13 / 13%). With `Y+` (V12 package) Yellow is 39 / 24 / 16%: +13 / +11 / +3 points, near fair share at 2P/3P. 4P remains low (fair 25%). The Yellow path is mostly the two weakest bots, so part of the 4P gap is roster selection (§43.3).

## 3. Stalling

**The bots cannot stall.** They triage highest current yield first and never hold a die on purpose. Red is now the lowest-yield colour (owner 1), so it is passively triaged last: 0.08–0.17 Red dice are still pending at game end per game (about 4% of Red banked), vs 0.2–0.37 other dice.

**Analytical incentive (n = 1, every bank fires a payout).** When an owner banks a Red die in place *k*, their gain relative to a rival in place *j* is: owner reward 1 + (payout_k − payout_j).

| owner's place at banking | vs 1st | vs 2nd | vs 3rd+ |
|---|---|---|---|
| 1st | — | +3 | +4 |
| 2nd | −1 | — | +2 |
| 3rd+ | −2 | 0 | +1 |

- A Red owner in 3rd or lower is net −2 against the leader on every bank, so their best move is to **hold Red dice in the Processing Box** until they lead Market Share, or until the game end. Conveyor Triage is "up to bandwidth of the player's choice", so holding is legal and nearly free: it only costs the die's income for a round.
- This is a real, rules-level degenerate line that the sim cannot show.
- **Fix (no new term):** Conveyor Triage must move dice in arrival order (oldest first) up to the bandwidth. Alternatively, any Red die in the Processing Box must leave first. With n > 1 the incentive is weaker, because only the bank that trips the counter matters, but it comes back at each trigger point.

## 4. Recommended package (Red shared payout, "RSP-1")

On top of C2 (v038b) with Market Leader Bonus and `v2.0` comparison removed:
- **Owner +1** Corporate Secret per Red Secret banked. The Red tiers are deleted.
- **n = 1** at every player count. Every Red Secret banked fires a payout.
- **Payout** 1st `+3` / 2nd `+1` / others `0` Corporate Secrets, survivors only, ties share the better place, **Secrets only**.
- **End payout** fires on Singularity and Patient Zero endings; not on Market Collapse or a Total Wipeout.
- **Starting Market Share 16 / 16 / 17.**
- **Yellow `Y+`:** F3 `+$3` → `+$1 & +1 Market Share` (on `V038_YELLOW_MS`).
- **Anti-stall:** Conveyor Triage moves Processing Box dice oldest first, up to the bandwidth.

Expected (V9/V12, 600 games):

| P | Market Collapse | Singularity | Patient Zero | rounds | spread | Yellow path |
|---|---|---|---|---|---|---|
| 2P | 36 | 44 | 18 | 8.55 | 25 | 39 |
| 3P | 41 | 42 | 16 | 8.68 | 25 | 24 |
| 4P | 38 | 44 | 18 | 8.69 | 28 | 16 |

Co Red / Blue / Green: 2P 46 / 52 / 52, 3P 33 / 34 / 33, 4P 27 / 24 / 24.

Verdict on the design: **promising; take it to the SDLC after the decisions below.** It must be re-measured once bots value the payout in their blocking and Public Relations decisions (expect Market Collapse to fall), and with the anti-stall rule implemented.

## 5. Decisions for the User

1. Owner reward: adopt **+1 Corporate Secret per Red Secret banked** (owner 0 makes Red unplayable: Red path 7–24%)?
2. Payout frequency: **n = 1 at every player count** (n = 2 gives only 1.0–1.7 payouts per game, n = 3 is nearly inert)? If you prefer fewer, larger events: n = 2 with payout 4 / 2?
3. Payout currency: **Secrets only** (the Secrets + Money fold changes nothing measurable)?
4. Starting Market Share **16 / 16 / 17** to offset the lost Market Leader Bonus (Market Collapse 34–41%, Singularity 39–44%, 2P Singularity 44% ≤ 48%)?
5. Starting Secrets: payouts add 3–6 Secrets per seat and cut Patient Zero to 16–18% at 2P/3P. Probe 2 / 3 / 4 (one lower at 2P/3P) in the SDLC sweep?
6. Anti-stall rule: Conveyor Triage moves Processing Box dice **oldest first** (no player choice) — adopt? (Alternative: Red dice leave first.)
7. Yellow: adopt `Y+` (Yellow F3 `+$3` → `+$1 & +1 Market Share`; Yellow 26 / 13 / 13 → 39 / 24 / 16%)?
8. Name for "the counter": a new glossary term is needed. Please propose or approve one before RULES.md is written. (I have not invented one.)
9. Bot work before the confirm sweep: payout-aware Market Share valuation for blocking and the Public Relations Track, and a ref1 rollout that clones the counter. Approve?
