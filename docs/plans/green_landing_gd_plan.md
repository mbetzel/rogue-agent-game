# Pre-SDLC Game Designer Analysis: Green Hit Landing ("S2H1")

**Author:** Game Designer (pre-SDLC analysis)
**Date:** 2026-11-20 (revised the same day: **S2H1 supersedes S2F1**, per the User's decisions)
**Baseline:** `v0.50.0` (`GameConfig.v050_roster()`, `mixed1` roster)
**Status:** D1, D3 and D4 are resolved. D2 and D5 are open (§8). No changes to `RULES.md`, `GLOSSARY.md`, `FINDINGS.md`, `sim/`, `pnp/`, `tts/` or `web/`.

**Probe tooling (no engine edits):** `scripts/probe_green_drop_band.py` monkeypatches `vulnerability.resolve_green` and, for the aware arms, `vulnerability_policy.loss_if`.
- `--report --arms R0,S2H1,S2HX` prints every S2H1 number below.
- `--report --arms S2F1,SFA,SFA1,SFA0,SFA9` prints the superseded arms (§9).

Runs: seeds `42..2041` (2,000 games per pod), 2P / 3P / 4P. The SE of a per-game rate is about 1.1 pp; the SE of a same-seed difference is about 1–1.5 pp.

---

## 0. Verdict (TL;DR)

**S2H1 is ready for the SDLC.**

**What it does.** A Green hit is no longer a free cleanse. The threat now carries into the next round: hits on the same player in back-to-back rounds rise from `4 / 3 / 2`% to `24 / 20 / 18`% (2P / 3P / 4P).

**What it costs.** Patient Zero + Market Collapse endings rise by `+4.0 / +2.6 / +4.5` pp. The User **waived the +3 pp bar for this change (D1)**, so this is recorded as an **accepted residual**, not a blocker.

**Exactness result (INV-LAND-02).** With at most one hit per player per Phase 4, the Secrets lost in a single Phase 4 are **exactly today's (R0)**, given the same starting Vulnerabilities.
- Today a hit player resets to `0`, which is below `5`, so a later cube can't target them.
- Under S2H1 a hit player is skipped for the rest of the phase.
- Either way, the later cubes see the same eligible players with the same values.
- **All of the extra pressure comes from where players land, which raises their starting Vulnerability in later rounds.**

Consequences:
- The worst round stays at `3` Secrets.
- No player is hit twice in one round.
- The existing bot `loss_if` is already exact for S2H1 (§5.9).

**Side effects.**
- **Upside:** company win-rate spread narrows at 2P (`24.0 → 18.6` pp) and 4P (`16.9 → 12.2`). Helix at 4P goes from `16.8` to `20.5`%.
- **Residual:** 2P Green Secrets lost is `2.77`, over the `2.5` cap (D2).

## 1. Rule (S2H1)

Each exited Green cube, one at a time, hits the surviving player(s) with the highest Vulnerability at `5` or more **who have not been hit by Green this phase**. Every tied player is hit.

| Hit at | Today (R0) | S2H1 |
|:---|:---|:---|
| `5–7` | −1, to `0` | −1, to `2` |
| `8–10` | −2, to `0` | −2, to `5` |
| `11+` | −3, to `0` | −3, to `8` |

- **At most one Green hit per player per Phase 4.**
- If no player is a valid target (no unhit player at `5`+), the cube has no effect and still recycles. This is the existing "no effect" rule with a wider condition. There is no overflow damage and no new term.
- There is no flat repeat cost and no other mitigation.

## 2. Exact damage and landing tables

### 2.1 One player at 5+ (loss / end Vulnerability; any k ≥ 1)

| Entry V | R0 | S2H1 |
|:---|:---|:---|
| 5–7 | 1 / 0 | 1 / 2 |
| 8–10 | 2 / 0 | 2 / 5 |
| 11–15 | 3 / 0 | 3 / 8 |

### 2.2 Multi-player cases (k = cubes this round)

| State (k) | R0 loss → end | S2H1 loss → end | Note |
|:---|:---|:---|:---|
| `[8, 6]` (2) | 2, 1 → 0, 0 | 2, 1 → 5, 2 | same loss; P0 ends at 5, which is in band |
| `[5, 8]` (2) | 1, 2 → 0, 0 | 1, 2 → 2, 5 | cube 2 skips P1 (already hit) and hits P0 |
| `[11, 7]` (2) | 3, 1 → 0, 0 | 3, 1 → 8, 2 | no "lightning rod": the hit player can't soak cube 2 |
| `[11, 11]` (3) | 3, 3 → 0, 0 | 3, 3 → 8, 8 | cubes 2–3: no valid target, no effect |
| `[12, 9]` (4) | 3, 2 → 0, 0 | 3, 2 → 8, 5 | cubes 3–4: no effect |
| `[9, 5, 5]` (3) | 2, 1, 1 → 0, 0, 0 | 2, 1, 1 → 5, 2, 2 | tie at 5: both hit by one cube |

The Secret-loss columns are identical in every row (INV-LAND-02). Only the end positions differ.

### 2.3 Cost to get back to safety after a hit

Pen Test costs `2 🔬` per step. Level limits are `1 / 1 / 2 / 2 / 3`, and L4 also gives a free `−1`.

| Hit at | Lands at | Steps to 4 (safe) | Note |
|:---|:---|:---|:---|
| 5–7 | 2 | 0 | safe, but only 2 ⚠ of headroom next round (today: 4) |
| 8–10 | 5 | 1 (`2 🔬`) | the L4 free −1 makes it safe at no cost |
| 11+ | 8 | 4 (`8 🔬`) | beyond any single turn's limit below L4; a hit next round is very likely |

## 3. Threat curve and economy (probe, R0 → S2H1, 2P / 3P / 4P)

These S2H1 numbers are the **re-based reference for the SDLC sweep** (§7).

| Metric | R0 | S2H1 |
|:---|:---|:---|
| Patient Zero end % | 37.0 / 58.5 / 62.8 | 42.2 / 61.9 / 69.0 |
| Market Collapse % | 29.6 / 12.4 / 12.7 | 28.4 / 11.6 / 11.0 |
| **PZ + MC** | 66.6 / 70.9 / 75.5 | **70.6 / 73.5 / 80.0** (+4.0 / +2.6 / +4.5, waived) |
| Singularity % | 26.4 / 27.3 / 23.8 | 20.4 / 24.6 / 19.1 |
| Total Wipeout % | 6.9 / 1.7 / 0.7 | 9.0 / 1.8 / 0.9 |
| Eliminated seats % | 25.4 / 24.7 / 20.8 | 30.1 / 26.3 / 23.4 |
| Rounds | 8.40 / 8.39 / 8.33 | 8.22 / 8.14 / 8.10 |
| Green hits per seat | 1.97 / 1.77 / 1.64 | 2.47 / 2.15 / 1.97 |
| Green Secrets lost (2P cap 2.5) | 2.19 / 1.95 / 1.84 | **2.77** / 2.40 / 2.23 |
| Back-to-back hits (% of seat-rounds with a hit) | 4.4 / 3.2 / 2.3 | 23.8 / 20.1 / 17.8 |
| Seat-rounds with 2+ hits; worst round | 0; 3 | 0; 3 |
| Hits landing at 5+ (8–10 → 5, 11+ → 8) | 0 | 11.7 / 11.8 / 14.4% |
| Rounds with Green where cubes outnumber alive players | — | 13.6 / 3.2 / 0.4% |
| Pen Test steps per seat | 2.70 / 2.93 / 3.19 | 3.53 / 3.66 / 4.01 |
| Company / White Hat spread (pp) | 24.0 / 14.4 / 16.9; 6.6 / 11.6 / 11.1 | 18.6 / 15.5 / 12.2; 9.5 / 10.6 / 10.1 |
| Helix (4P) / Aegis (2P) win % | 16.8 / 63.5 | 20.5 / 62.1 |

**Where the extra damage comes from:**
- 88% of hits are at 5–7, and their immediate cost is unchanged.
- The pressure is the carry-over: 3P Phase 1 lock-ins at 5+ rise from about 29% to about 36%.
- Pen Test use rises by about +0.8 steps per seat, roughly `+1.6 🔬` per game.

**Why 2P and 4P rise most:**
- At 2P, about 10 Green cubes per game are shared by 2 seats.
- At 4P, a +2.6 pp per-seat elimination rise compounds into +6.2 pp of Patient Zero endings, because any one of 4 seats can trigger the end.

**The cap's softening is mostly at 2P:** 13.6% of rounds with Green have more cubes than alive players.
- The rejected arm `S2HX` charged each player 1 Secret per cube beyond the alive-player count.
- It pushed 2P eliminations to `36.1`% and Total Wipeout to `12.7`%. The User rejected it, so there is no overflow damage.

## 4. The 2P residual (D2)

At 2P, S2H1 raises eliminations by +4.7 pp and Total Wipeout by +2.1 pp (still well under 15%), and Green lost is `2.77` against a `2.5` cap.

**Recommendation: accept it as a residual.** Reasons:
- The cap already removes 2P's worst case (no multi-hit rounds, worst round 3).
- 2P company spread improves by 5.4 pp.
- The only levers probed either undo the change at 2P or overshoot:
  - "5–7 lands at 0 at 2P" gave Green lost 2.32 but removes most of the 2P carry-over.
  - "+1 starting Secret at 2P" gave eliminations −6.3 pp, rounds +0.75 and Green lost 3.22.
  - Both were probed on S2F1 (§9). Their effects should carry over to S2H1, because S2F1 and S2H1 differ by ≤ 0.6 pp at 2P.

If the User wants the cap honoured, the cleanest lever is to re-state the 2P cap as `≤ 2.8`. Green lost is now a "felt pressure" metric, not a damage-spike metric, since the worst round is unchanged.

## 5. Edge cases and rulings

1. **Aegis Baffle Echo (D4, resolved).** A cancelled hit **still uses up that player's one hit this phase**, and their Vulnerability still drops to the landing value. Baffle Echo cancels only the Secret loss.
   - **Optimality:** within a phase, each player can be hit at most once, so there is no "wait for a bigger hit this phase" choice. Cancelling the one hit is the only in-phase option.
   - The decision is the existing one: use Baffle Echo now, or save it for a later round in the same Version.
   - The bot rule `aegis_green_cancel_default` (damage ≥ 2, lethal, or v3.0) stays correct. No change.
2. **Ties:** one cube hits every tied unhit player. Each of them is then marked hit. Tied players are never split into first and repeat hits.
3. **Players at ≤ 0 Secrets mid-resolution** (from Blue or an earlier cube): they are still targetable if they are unhit and at 5+, as today.
   - After their one hit they are skipped, so they can't soak extra cubes, and there is no "lightning rod" effect.
   - Patient Zero is still checked once, after all Green (Step 3). Total Wipeout timing is unchanged.
4. **Pen Test L4 free −1:** turns the 5 landing (8–10 hit) safe at no cost, and 2 → 1. L4 is worth more. Bot L4 adoption is flat (14.7 → 12.7% at 2P); the bot doesn't value it more.
5. **Green R&D face (−2 on triage, Phase 6) and G1 Self-Healing Kernel (−2, Phase 3):** plain lowering, floored at 0. After a 5–7 hit they now clear the carry-over (2 → 0), where today they are wasted on a 0. This is a small, intended buff to Green dice.
6. **Target Lock Green fallback (+2 per unplaceable cube, after Green):** today it gives `0 + 4 = 4`, which is safe. Now `2 + 4 = 6` starts the next round already in band. This is rare, and no text change is needed.
7. **Corruption "lowest Vulnerability gains +2 / +3"** (before Phase 4): more players now sit at 2, and an Aggressive `+3` takes 2 to **5**, which can draw a hit this round. Watch item.
8. **Compile Buffer Overflow:** no hits, so no landing (no change).
9. **Bot `loss_if` (INV-LAND-02):**
   - Today's replay resets a hit seat to `vuln_hit_reset = 0`, below the floor, so it is never targeted again. That is exactly the one-hit cap, so the current `loss_if` already returns S2H1's in-round loss.
   - **Update it anyway** for robustness: track a `hit` set, skip hit seats when `vuln_one_hit_per_round` is on, and set the landing value. Without this, a future landing at or above the floor with the cap off would be modelled wrongly.
   - The probe's S2H1 arm used the stock `loss_if`, so the S2H1 reference numbers need no bot change to reproduce.
   - A forward-looking carry-over term in `lam` is out of scope (a separate `[TUNE-BOT]` experiment if wanted).

## 6. Degenerate strategies

- **Parking at 4:** still the main hold point. After a hit you restart at 2, with 2 ⚠ of headroom. This is the intended Pen Test pull.
- **Kamikaze climbing (rush to 11+, eat one hit):**
  - Today a hit at 11+ costs 3 and resets you to 0, a free cleanse.
  - Under S2H1 it costs 3 and lands you at 8, 4 Pen Test steps from safety. Across rounds the ladder is `3 + 2 + 1`.
  - **The reset-as-cleanse exploit is closed.** Hits at 11+ stay rare (1.0–1.5% of hits).
- **Hiding at 5+ behind a higher rival:** the cap means cube 2 often finds you once the leader is hit. Ties at 5 still share a single cube. This is unchanged from today, because a hit player was already out at 0.
- **Cheap cleanse at 5:** a hit at 5 now removes 3 Vulnerability for 1 Secret (today: 5). It is still a reasonable trade, but no longer the best substitute for Pen Test.
- **Cube flooding at 2P:** excess cubes have no effect, as today when no one is at 5+. This is not exploitable; players don't control the cube count.
- **Stalling:** rounds fall by 0.18–0.25. No stall risk.

## 7. Implementation plan

**Config (`sim/config.py`, defaults reproduce v0.50):**
- `vuln_hit_landing_by_band: Optional[Tuple[int, ...]] = None` `[TUNE]`. `None` means every band lands at `vuln_hit_reset`; S2H1 is `(2, 5, 8)`.
  - Same length as `vuln_band_thresholds`.
  - Ints ≥ 0, non-decreasing.
  - Band 0's landing must be below `min(vuln_min_target_by_version)`.
  - Band `i ≥ 1` must land below `vuln_band_thresholds[i]`, so a hit always lowers the band (INV-LAND-01).
- `vuln_one_hit_per_round: bool = False` `[TUNE]`; S2H1 sets `True`.
- Presets: `v051()` and `v051_roster()`, inheriting `v050()` and `v050_roster()`.

**Engine (`sim/engine/vulnerability.py`, `resolve_green`):**
- Add a pure helper, `hit_landing(cfg, v)`.
- Keep a local `hit_this_phase` set. When the flag is on, skip seats in it when building `elig`.
- Add every hit seat to the set, **including cancelled hits** (ruling 1).
- Set Vulnerability to `hit_landing(cfg, top)`.
- Events gain `land`.
- New counters: `green_landing_unsafe` and `green_cap_no_target`, the latter for cubes that had targets at 5+ but all were already hit.
- `vuln_reset_by_hit_total` keeps its name and is fed by `v − land`.

**Bots (`sim/bots/vulnerability_policy.py`):** update `loss_if` per §5.9. No other policy change.

**Web:**
- `web/controller/phase4_attack_actions.py`: the line 41–60 preview replay (skip hit seats, set the landing), and the line 273 log text ("Vulnerability reset to …" becomes "drops to N").
- `web/schemas.py:500`: expose the landing tuple and the flag.

**Tests (`tests/test_v510_green_landing.py`):**
- v0.50 parity at defaults (fixture replay, 0 mismatches).
- The §2.1 and §2.2 tables as unit cases.
- **INV-LAND-02 property:** on 1,000 random states, S2H1's per-seat loss equals R0's.
- At most 1 hit per seat per phase.
- An Aegis cancel uses up the hit, and Vulnerability still lands.
- A ≤ 0-Secret seat is hit once, then skipped.
- No valid target: no effect, the cube recycles, and the counter increments.
- Buffer overflow: no landing.
- `loss_if` equals `resolve_green`.
- Config validation errors.

**SDLC sweep guardrails, re-based on the S2H1 probe (§3).** The product-owner runs `v051_roster` with 2 × 1,200 seeds. Pass if within noise of the reference:

| Check | Reference / limit |
|:---|:---|
| PZ + MC | `70.6 / 73.5 / 80.0` ± 2 pp |
| Eliminated seats | `30.1 / 26.3 / 23.4` ± 2 pp |
| Rounds | `8.22 / 8.14 / 8.10` ± 0.15 |
| Green lost | `2.77 / 2.40 / 2.23` ± 0.15 |
| Back-to-back hits | `24 / 20 / 18`% ± 3 |
| Multi-hit seat-rounds | `0` (invariant) |
| Worst round | ≤ 3 |
| Collapse (3P / 4P) | ≥ 8% (reference `11.6 / 11.0`) |
| 2P Total Wipeout | < 15% |
| Income | ≤ v0.48 × 1.20 |

- Report Helix, Aegis and Spook win %.
- Report the Corruption +3 landing-at-5 count.
- The PZ + MC rise against v0.50 (`+4.0 / +2.6 / +4.5`) is an **accepted residual (D1)**. Record it in FINDINGS as such.

**Docs and assets (no new terms):**
- RULES.md lines 28 and 262–266: the hit text, "The next cube re-checks…", and the Aegis line ("still resets to 0" becomes "still drops"). Also the "no effect" sentence: "If no surviving player who has not been hit this phase is at `5` or more, the cube has no effect."
- RULES_QUICKREF line 119.
- GLOSSARY "Green Cubes" entry.
- `pnp/generate_pnp.py` lines 73, 1299 and 1371, plus the Vulnerability Track band art (print "→ 2 / → 5 / → 8"); then rebuild TTS.
- CLAUDE.md pillar text (D5).

**Wording guardrail:**
- Don't coin capitalized terms such as "Landing", "Hit Cap", "Overflow", "Drop a band" or "Immune".
- Use plain text: "then move their Vulnerability marker down to `2` / `5` / `8` (by band). A player can be hit by only one Green cube each round; later cubes skip them."
- "Band" is already used in RULES.md.

**Version:** `v0.51.0`.

## 8. Decisions

**Resolved (User, 2026-11-20):**
- **D1:** the +3 pp PZ + MC bar is waived for this change. The rise is recorded as an accepted residual, and guardrails are re-based on the S2H1 probe.
- **D3:** the flat repeat cost is dropped. The one-hit cap replaces it.
- **D4:** a cancelled Aegis hit counts as the player's one hit this phase.

- **D2:** 2P Green lost `2.77` (cap 2.5) is accepted as a residual.
- **D5:** bump to `v0.51.0`; the CLAUDE.md Core Pillar text changes ("and resets them to `0`" becomes "then drops them to `2` / `5` / `8`; one hit per player per round").

No open decisions remain (User sign-off 2026-11-20).

## 9. Superseded: S2F1 (repeat hits cost a flat 1)

S2F1 used the same landing, allowed repeat hits, and charged each repeat hit a flat `1` Secret.

| Metric | S2F1 |
|:---|:---|
| PZ + MC | `70.9 / 74.0 / 80.1` |
| Eliminated seats | `30.4 / 26.6 / 23.6`% |
| Seat-rounds with 2+ hits | `3.4 / 2.2 / 1.9`% |
| Worst round | 5 |

- The flat cost only mattered for hits at 11+.
- A rule-aware bot (`SFA`) changed nothing.
- A softer landing, "5–7 → 1" everywhere (`SFA1`), gave PZ + MC `+1.3 / +1.8 / +2.2`. It was kept as a reference, not chosen.
