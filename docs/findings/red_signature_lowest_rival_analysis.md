# Pre-SDLC Analysis: Red Target Lock Signature Attack, "Lowest Rival Gains +2"

**Author:** game-designer (pre-SDLC modeling, CLAUDE.md workflow step 1)
**Date:** 2026-11-19
**Status:** Analysis complete. Awaiting User decisions (Section 8). No rules, sim, PnP, TTS or web files changed.
**Baseline:** `v0.46.0` (`v046_roster`, `mixed1` roster, `scripts/run_v380_secret_faces_sweep.build_engine`), seeds `42..`
**References:** `RULES.md` Phase 4 Step 4 ("Target Lock Signature Attack Resolution", Red), Phase 4 Step 5 (SETEC Corp), Market Leader Bonus; `GLOSSARY.md` Target Lock; `FINDINGS.md` §62; `sim/engine/phase4_attack_resolution.py` `_resolve_signature_red`.

---

## 1. The change

| | Current (`v0.46.0`) | Proposal |
|---|---|---|
| Locker | `-2` Market Share (not below `0`) | same |
| Recipient | the **non-locked** surviving rival with the least Market Share | the surviving rival with the least Market Share, **locked or not**; in **2P, SETEC Corp is eligible** |
| Multi-lock | all drains first, then gains (`INV-SIMUL-RED`) | same two epochs; each recipient is read from the post-drain positions |
| Fizzle | if every survivor is locked (2P: both locked; 42% of 2P events) | only if the locker has no surviving rival (3P/4P sole survivor); never in 2P |
| Card text | "-2 Market Share; non-locked survivor with least Market Share gains +2" | "-2 Market Share; lowest rival gains +2" (2P: SETEC Corp needs to be named, Section 7) |

The Red Signature only fires when Red is the strict top colour in the tray (tie order `Green > Black > Blue > Red`). So at least one Red cube exited that round, and in 2P SETEC Corp also takes its `+1` in Step 5 that same round.

## 2. Method

- I extended the existing probe into `red_lock_probe2.py` in the session scratchpad. It monkeypatches `_resolve_signature_red`. The baseline arm calls the original function and measures the deltas around it.
- Arms:
  - **base**: the current rule;
  - **A**: the proposal as written;
  - **B**: hybrid (SETEC eligible, locked rivals excluded);
  - **C**: locked rivals eligible, SETEC excluded;
  - **D1**: A, but SETEC gains only `+1`;
  - **D2**: A, but SETEC is eligible only while at `<= T` Market Share (`T = 4` and `7`).
- Tie policy:
  - when SETEC is in the tie, the locker picks SETEC (it scores no VP, so this is the safe gift);
  - otherwise the locker picks the tied rival with the fewest Secrets, as the current default heuristic does.
- Sample sizes:
  - **12,000 games per pod** for base / A at 2P, 3P and 4P, and for C / D1 at 2P;
  - **4,000 games per pod** for B and D2, and for the 3P/4P B check.
  - B at 3P/4P matches the baseline to within `0.2` pts on every metric, which validates the probe.
  - 3P/4P has no SETEC Corp, so **C = D1 = D2 = A at 3P/4P**, and B equals the current rule.
- Win-rate 95% CI per archetype:
  - about `±2.0` pts at 2P, `±1.3` at 3P and `±1.0` at 4P (12k games);
  - about `±3.5 / ±2.3 / ±1.7` at 4k games.
  - An arm-to-arm difference needs about `×1.4` of that to be significant.
  - The archetype spread (max − min) is noisier than any single archetype. Treat spread moves under about `2` pts as noise.
- Balance target: win-rate parity (FINDINGS §62 and memory "balance by win rate").

## 3. Expected-value model of one Red Signature

Let `d = min(2, MS_locker)` (the floor at `0` makes the empirical `d` about `1.8–1.9`), `g = 2`, and `f` = the fizzle probability.

- **Locker:** `-d` in every arm.
- **Recipient:** `+g`, capped at `20` (the cap never binds under A: 3 capped gains in 12k games).
- **Swing between locker and recipient:** `d + g ≈ 3.9` MS.
- **Net change in total human Market Share per event:** `g·(1 − f − s) − d`, where `s` = the share of gains that go to SETEC.

### 3.1 Empirical per-event deltas

| Pod / arm | Events / game | Drain / event | Human gain / event | SETEC gain / event | **Net human MS / event** | Fizzle | Share of gifts to a locked rival |
|---|---|---|---|---|---|---|---|
| 2P base | 1.54 | 1.81 | 1.17 | – | **−0.64** | 41.6% | – |
| 2P A | 1.53 | 1.78 | 0.88 | 1.12 | **−0.90** | 0% | 21% |
| 2P B | 1.46 | 1.81 | 0.44 | 1.56 | **−1.37** | 0% | 0% |
| 2P C | 1.65 | 1.80 | 1.97 | – | **+0.17** | 1.4% | 40% |
| 2P D1 | 1.55 | 1.78 | 0.82 | 0.59 | **−0.96** | 0% | 20% |
| 3P base | 2.30 | 1.90 | 1.67 | – | **−0.23** | 15.2% | – |
| 3P A | 2.43 | 1.89 | 2.00 | – | **+0.11** | 0.2% | 49% |
| 4P base | 2.87 | 1.91 | 1.82 | – | **−0.09** | 6.0% | – |
| 4P A | 3.09 | 1.90 | 2.00 | – | **+0.10** | 0% | 54% |

What this shows:

- **3P/4P.** The proposal turns the Red Signature from a small net Market Share sink into a pure transfer (net about `+0.1`, because drains are floored at `0` and gifts are not).
- **2P under A.** It becomes a larger sink for humans (`−0.90` per event), and SETEC Corp takes the difference. Early on SETEC sits at `0–4` and humans at `14`, so SETEC is almost always the lowest. The mean SETEC Market Share at gift time is `3.3`, and SETEC receives `56%` of 2P gifts.

### 3.2 Multi-lock rounds (A, share of Red Signature resolutions)

| Pod | 1 locked | 2 locked | 3 locked | 4 locked | Mutual-cancel pairs per multi-lock round |
|---|---|---|---|---|---|
| 2P | 76% | 24% | – | – | 47% (the other 53% go to SETEC) |
| 3P | 58% | 35% | 7% | – | **70%** |
| 4P | 44% | 39% | 15% | 2% | **55%** |

Why mutual cancels happen:

- After the simultaneous drain, two locked players are usually each other's lowest rival. Each then loses `2` and gains `2`, so the net is `0` and their relative order is unchanged.
- At 3P, 70% of multi-lock Red rounds become a no-op for the locked pair. The unlocked third player, who used to receive `+2` per locker, now gets nothing.
- In 2P under C, every double-lock is a mutual cancel (it replaces the old fizzle). The result is the same, `0` net, but the rule is longer to explain.

### 3.3 Who gets the gifts

The table shows the share of human-received Market Share that went to the eventual winner, then the win rate of seats that received any gift.

| Pod | base | A | fair `1/N` |
|---|---|---|---|
| 2P | 0.62 / 59.3% | 0.50 / 50.5% | 0.50 |
| 3P | 0.42 / 37.9% | 0.33 / 33.4% | 0.33 |
| 4P | 0.34 / 29.4% | 0.24 / 23.7% | 0.25 |

Under the current rule, gifts flow toward seats that go on to win: the unlocked lowest is often a player who has not banked Secrets recently, not a player who is behind. Under the proposal, gifts are **outcome-neutral** (exactly `1/N`). This is the "boost players who fall behind" property the User asked for, without turning into a comeback engine.

## 4. Threat curve and pacing

| Pod | Arm | Rounds | Market Collapse | Patient Zero | Singularity | Total Wipeout | Winner Secrets |
|---|---|---|---|---|---|---|---|
| 2P | base | 8.09 | 36.5% | 33.4% | 25.2% | 4.9% | 12.30 |
| 2P | **A** | 8.17 | 33.7% | 34.7% | 26.5% | 5.1% | 11.33 |
| 2P | B (4k) | 7.99 | 37.0% | 34.0% | 24.2% | 4.7% | 11.58 |
| 2P | C | 8.34 | 32.2% | 34.1% | 28.7% | 4.9% | 12.33 |
| 2P | D1 | 8.17 | 34.0% | 34.3% | 26.7% | 5.0% | 11.60 |
| 2P | D2 T4 (4k) | 8.19 | 32.7% | 34.6% | 27.8% | 4.9% | 11.79 |
| 3P | base | 7.89 | 23.1% | 54.5% | 21.0% | 1.4% | 13.00 |
| 3P | **A** | 8.15 | **15.1%** | 56.0% | **27.4%** | 1.5% | 12.67 |
| 4P | base | 7.49 | 23.9% | 60.7% | 15.1% | 0.3% | 13.75 |
| 4P | **A** | 7.83 | **13.1%** | 63.9% | **22.7%** | 0.3% | 13.43 |

Market Collapse 95% CI is about `±0.8` pts at 12k games, so every Market Collapse move here is significant.

- **Mechanism: rescue from `0` before the Market Collapse check.** Target Lock resolves in Phase 4 Step 4, before the End Game Trigger Check, so a gift to a player at `0` cancels that round's Collapse. These are rounds where someone was at `0` after the drain and nobody was at `0` after the gains:

  | Pod | base | A |
  |---|---|---|
  | 3P | 430 | 1,531 |
  | 4P | 520 | 1,899 |
  | 2P (per 4k games) | 123 | 465 |

  The typical case: two locked players at `2` both drain to `0`, then each lifts the other back to `2`.
- **Pacing.**
  - Games run `+0.26` (3P) and `+0.34` (4P) rounds longer, which brings them to the 2P length (about `8.1–8.2`).
  - The ending mix moves from Collapse to Singularity. At 4P: Patient Zero + Collapse goes from `84.6%` to `77.0%`, and Singularity from `15.1%` to `22.7%`.
  - FINDINGS §62 accepted a 4P Collapse of `22.8%` as a residual and treated Singularity `16–27%` as "accept as the third ending". The proposal stays inside that Singularity band, and it **resolves** the 4P Collapse residual rather than worsening it.
- **2P.** The pacing change is small (`±0.1` round, Collapse `−2.8` pts).
- **Breach pressure.** Patient Zero rises by `+1.3` to `+3.2` pts, mostly because games run longer. Total Wipeout is unchanged.

## 5. SETEC Corp trajectory and Market Leader Bonus denial (2P)

| Arm | SETEC final MS | SETEC MLB 1st / game | 2nd / game | Secrets absorbed / game | Winner Secrets |
|---|---|---|---|---|---|
| base | 6.75 | 0.37 | 0.52 | 1.63 | 12.30 |
| **A** | 8.49 | **0.78** | 0.39 | **2.74** | 11.33 |
| B (4k) | 8.92 | 0.76 | 0.38 | 2.65 | 11.58 |
| C | 6.96 | 0.39 | 0.56 | 1.72 | 12.33 |
| D1 | 7.72 | 0.66 | 0.43 | 2.41 | 11.60 |
| D2 T4 (4k) | 7.97 | 0.66 | 0.50 | 2.49 | 11.79 |
| D2 T7 (4k) | 8.36 | 0.78 | 0.42 | 2.75 | 11.58 |

- **A delivers the "the agent accelerates when it is low" intent.**
  - SETEC takes 1st place in the Market Leader Bonus twice as often.
  - It absorbs `+1.1` Secrets per game that would otherwise go to humans, so the winning score falls by about `1` Secret.
  - SETEC is still a minority leader: it wins 1st place in fewer than one MLB award per game.
- **D1 halves the effect and D2 T4 is similar.** D2 T7 is the same as A, because SETEC is rarely above `7` when it is the lowest.
- **D2 is not worth its extra rule text.**

## 6. Win-rate parity (archetype; the balance target)

| Pod / arm | Accel. | Adaptive | Mixed | Reckless | SecOps | Venture | **Spread** | Company spread |
|---|---|---|---|---|---|---|---|---|
| 2P base | 51.7 | 57.3 | 48.1 | 43.5 | 54.7 | 52.3 | **13.7** | 19.2 |
| 2P **A** | 52.1 | 58.4 | 47.7 | 42.1 | 57.9 | 51.0 | **16.3** | 17.7 |
| 2P B (4k) | 51.5 | 61.0 | 47.2 | 43.4 | 58.4 | 49.4 | 17.6 | 18.1 |
| 2P C | 52.2 | 56.8 | 47.8 | 43.9 | 56.0 | 52.3 | **12.9** | 19.5 |
| 2P D1 | 52.3 | 58.4 | 47.6 | 42.8 | 57.6 | 50.9 | 15.6 | 18.5 |
| 2P D2 T4 (4k) | 53.2 | 60.1 | 46.7 | 43.9 | 59.0 | 50.2 | 16.2 | 20.0 |
| 3P base | 34.6 | 37.1 | 30.6 | 27.4 | 40.2 | 34.1 | **12.9** | 17.5 |
| 3P **A** | 35.0 | 37.5 | 30.3 | 26.6 | 41.0 | 34.2 | **14.4** | 15.7 |
| 4P base | 23.3 | 28.6 | 22.5 | 20.0 | 31.8 | 25.4 | **11.8** | 13.8 |
| 4P **A** | 24.1 | 28.9 | 22.0 | 18.7 | 33.2 | 25.0 | **14.5** | 15.5 |

How to read the table:

- **2P, SETEC-eligible arms (A, B, D1, D2).**
  - SecOpsTurtle gains `+2.9` to `+3.2` pts, which is significant at 12k games (difference CI about `±2.8`). Reckless loses about `1` pt.
  - All four widen the spread by about `2–4` pts.
  - My reading: when SETEC Corp takes more Market Leader Bonus places, MLB-reliant lines are hurt more than the Secrets-turtle line.
  - **C is the only arm that keeps 2P parity** (`12.9`, the same as base within noise).
- **3P.** A is parity-neutral: every archetype moves `<= 0.8` pts, which is noise. The `+1.5` spread move is noise, and the company spread improves by `1.8` pts.
- **4P.** A widens the spread by `+2.7`. That is the extremes moving about `1.3` pts each (Reckless `−1.3`, SecOps `+1.4`), at the edge of significance. The company spread widens by `+1.7`.
- **Overall.** Every spread stays far inside the historical band (v0.46 assessment: spreads in the low teens; old guardrail `<= 45%`). None of this is a blow-out, but the direction is consistent: the change slightly favours the turtle archetype and slightly hurts Reckless.

## 7. Edge cases and incentives

1. **Mutual cancel.** Two locked players gift each other: net `0`, and the unlocked rivals gain nothing.
   - Common: 70% of 3P multi-lock rounds, 55% at 4P.
   - It is rules-correct but anticlimactic. Players may ask "why bother?" It does keep a double lock from crashing both players into a Market Collapse, which is the intended "help the fallen".
2. **Locker at `0`.** The locker loses nothing and still gifts `+2`.
   - This happens in both rules and is unchanged. About 9% of 3P events leave the locker at `0` (2,513 per 12k games).
   - Under A, that locker can be rescued in the same round by another locker.
3. **Cap at `20`.** The cap matters under the current rule, where the lowest *unlocked* rival can be high (`161` / `336` capped gains per 4k games at 3P/4P). Under A it is effectively unreachable (3 per 12k games), because the lowest rival is rarely at `19+`.
4. **Ties with SETEC (2P).**
   - A tie with SETEC happens in 4.3% of A events. "You choose" already covers it.
   - A rational locker picks SETEC, which scores no VP, unless the tied human is far behind on Secrets.
   - The bot hook `choose_signature_red_recipient(player, tied_recipients, state)` takes `PlayerState`s only, so it needs a SETEC sentinel.
5. **Patient Zero.** Patient Zeros flagged in Step 3 are not survivors: they cannot receive and do not resolve. This is unchanged. In 3P/4P, a locker whose only surviving rivals are Patient Zero gives no gift (0.2% of 3P events). In 2P SETEC always exists, so there is never a fizzle.
6. **Rescue from `0` before the Market Collapse check.** This is the main pacing effect (Section 4).
   - It is consistent with the existing order: Customer Poaching / Red Market Share changes in Phase 3 and Phase 4 are all settled before the check.
   - No new timing rule is needed.
7. **Recipient read pre- or post-drain (multi-lock).**
   - The probe used post-drain, which is consistent with "all drains first".
   - Pre-drain would send gifts to the lowest *before* the double drain. That gives fewer mutual cancels but needs a sentence saying so.
   - Recommend post-drain (no extra text).
8. **Kamikaze / stalling (staying low to farm gifts).**
   - Under A, the lowest rival receives about `0.20` events per round × `2` = **`+0.4` Market Share per round** at 3P, and less at 4P, because gifts are split between multiple low players.
   - Staying low gives up the Market Leader Bonus (`+3` / `+1` Secrets in rounds with a Red Secret face banked) and the Market Share tiebreak.
   - Market Share is not VP, so farming has negative EV. The outcome-neutral gift-to-winner share (Section 3.3) confirms that no seat profits from sitting at the bottom.
   - No new degenerate line: Target Lock itself is not voluntary (it follows from banking Secrets).
9. **2P "tax" feel.** Under A, a 2P human who is locked by Red early pays `−2` straight to SETEC Corp. The rival gains nothing directly and only a relative `+2`. Under the current rule the rival gained a relative `+4`. Lock swings in 2P therefore become smaller and SETEC becomes more present. This is intended, but players will notice it.

## 8. Recommendation and User decisions

**Recommendation:**

- **3P/4P: adopt the proposal (A).** It is parity-neutral at 3P and adds about `+2.7` spread at 4P (watch item). It makes gifts outcome-neutral and removes the "all locked" fizzle clause. It also clears the 4P Market Collapse residual from §62, at the cost of about `+0.3` rounds and Singularity rising to `23–27%`.
- **2P: adopt A with SETEC Corp eligible** if the User wants SETEC Corp to accelerate. This is the stated intent, and it doubles SETEC's MLB 1st places for a `+2.6` pt archetype spread cost (`13.7 → 16.3`).
- **2P parity alternative.** If parity outweighs SETEC acceleration, use **C** (SETEC excluded; spread `12.9`).
- **Counter-levers.** D1 (`+1` to SETEC) is the only counter-lever worth keeping in reserve: about `−0.7` spread at half the SETEC effect. D2 is not recommended.
- **Hybrid B is dominated.** It has A's spread cost, without A's pacing benefit, and keeps the fizzle-style exclusion text.

**User decisions:**

1. **D-1: 2P SETEC eligibility.** A (eligible, `+2`) / D1 (eligible, `+1`) / C (not eligible).
2. **D-2: Accept the pacing shift.** 3P/4P Market Collapse `23–24% → 13–15%`, Singularity `15–21% → 23–27%`, `+0.3` rounds.
3. **D-3: Multi-lock recipient basis.** Post-drain (recommended) or pre-drain.
4. **D-4: Card wording** (no new terms; "opponent" is not a glossary term, so use "rival"). Options:
   - pnp `:1412`: "**-2 Market Share**; lowest rival gains **+2** *(2P: SETEC Corp counts)*";
   - Phase 4 summary `:1913`: "{RED} -2 Share, +2 to lowest rival (2P: or SETEC Corp)".

   SETEC Corp is not a player and so is not a "rival" in the glossary sense. It must be named explicitly. **No new glossary term is needed.**
5. **D-5: Version.** Ship as `v0.47.0` (a full version-sync sweep) or fold it into a v0.46.x `[TUNE]`.
6. **D-6: Watch item.** Accept the 4P archetype spread `+2.7` (SecOps `+1.4` / Reckless `−1.3`) or require a confirm sweep first.

## 9. Implementation plan (after sign-off; route through the SDLC chain)

1. **principal-engineer (spec, short).** Amend `INV-SIG-RED` / `INV-SIMUL-RED`:
   - recipient = least-Market-Share surviving rival, read post-drain, locked eligible;
   - plus SETEC Corp at 2P per D-1;
   - fizzle only when no surviving rival.
2. **senior-engineer (sim).**
   - `sim/config.py`: add `signature_red_recipient_rule: str = "non_locked"` (new value `"lowest_rival"`), `signature_red_setec_eligible: bool = False`, and `signature_red_setec_gain: Optional[int] = None` (D1).
   - Turn them on in a new preset (`GameConfig.v047()` / `v047_roster()`) so the `v046` parity stays byte-identical.
   - `sim/engine/phase4_attack_resolution.py` `_resolve_signature_red` (line 737): take a post-drain snapshot; give each locker its own lowest-rival pool; sum the gains; apply them together with the cap.
   - Add SETEC as a candidate via `state.setec_market_share` (respect `state.setec_corp_active`), and update the telemetry counters.
   - `sim/bots/base.py` `choose_signature_red_recipient` / `default_signature_red_recipient_heuristic` (`:1289`, `:1322`): accept a SETEC sentinel and prefer SETEC on ties.
   - Mirror any change into `sim/engine/fast_clone.py` only if Phase 4 is duplicated there (RB-07 guard).
3. **Tests** in `tests/test_signature_dominant_attacks.py`:
   - TC-SIG-07 and TC-SIG-08 stay valid under the current rule (keep them for `v046`).
   - Add `lowest_rival` variants:
     - TC-SIG-07b: a locked rival is the lowest and receives;
     - TC-SIG-07c: two locked players mutually cancel;
     - TC-SIG-07d: a locker at `0` still gifts;
     - TC-SIG-08b: a tie including SETEC calls the hook with the sentinel;
     - TC-SIG-08c: SETEC receives `+2` (or `+1` under D1) and is capped at `20`;
     - TC-SIG-08d: a gift rescues a player from `0`, so there is no Market Collapse that round;
     - TC-SIG-08e: Patient Zero is ineligible, and there is no gift when the locker has no surviving rival.
   - Run the full suite quietly.
4. **staff-engineer review**, then a **product-owner confirm sweep**: 4,000 games per pod with the `v047` preset against `v046` (`scripts/run_v046_sweep.py`), with archetype and company win rates and CIs.
5. **game-designer sign-off**, then **FINDINGS.md §63** and a **PLAN.md** phase entry (move completed items per the archive rule).
6. **Docs, PnP, TTS and web (Phase B):**
   - Text changes:
     - `RULES.md` Phase 4 Red Signature bullet (line 279): drop the "did not trigger Target Lock" and "all surviving players triggered" clauses, and add the 2P SETEC Corp sentence;
     - `RULES_QUICKREF.md:129`;
     - `GLOSSARY.md:33` (Target Lock, Red clause);
     - `pnp/generate_pnp.py:1412` and `:1913`;
     - `web/controller/phase4_attack_actions.py:33` ("the rival with the least Market Share gains 2 (2P: SETEC Corp counts)"), plus any web tie-choice UI that lists recipients (it must offer SETEC);
   - Rebuild: run `python3 -m pnp.generate_pnp`, then `python3 -m tts.build_tts` and `--check`.
   - If D-5 is `v0.47.0`, do the full version-sync list from CLAUDE.md.
