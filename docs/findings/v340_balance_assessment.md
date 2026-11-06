# v0.34.0 Balance Assessment (Game Designer, Post-Telemetry)

**Date:** 2026-11-05
**Author:** game-designer
**Input:** [v340_telemetry_sweep_report.md](./v340_telemetry_sweep_report.md) and [v340_telemetry_summary.json](./v340_telemetry_summary.json). This is the product-owner sweep: 3,000 games per pod, six-phase vs `legacy_v033`, base seed 42.
**Constraints honored:** D5. Starting Corporate Secrets stay a flat 8 at every player count (DTO 9). No lever scales the attack threat by player count.

**Method:**
- Every lever was run on the same seeds as the sweep: 3,000 games per pod, match seed = `42 + N·100000 + idx`.
- The key packages were also re-run on fresh seeds: base 777, 2,000 games per pod.
- Levers were applied only by monkeypatching in scratch scripts:
  - `dataclasses.replace` on `Company` and `VersionCard`;
  - a source-patched copy of `resolve_player_defense_and_wear`;
  - a `PlayerState.archetype` override.
- No `sim/` files were edited.
- My harness reproduces the sweep's baseline exactly: 8.30 / 7.98 / 7.76 rounds, and 27.1 / 25.8 / 25.4% zero-income turns.
- Scratch scripts: `/tmp/claude-1000/-home-mike-antigravity-rogue-agent/78a3211a-824b-4cd0-ab0e-8d056a2309d4/scratchpad/harness.py`, `analyze.py` and `fullmetrics.py` in the same folder.

---

## 0. Headline: a rules-fidelity defect contaminates the company and White Hat numbers

The sim gives every **White Hat Operative** the **Institutional Override** of its canonical paired **Client Company**.

How it happens:
- `PlayerState.archetype` (`sim/engine/state.py:446-463`) is a backward-compatibility bridge. It derives a legacy archetype from the White Hat code.
- Every override check is written as `company == X or archetype == Y`.
- So in both sequences:
  - **The Spook** gets *Slush Fund* (`phase4_attack_resolution.py:317`);
  - **The Acoustic** gets *Baffle Echo* (`:34`, `:191`);
  - **The Operator** gets *Redundant Crew* (`phase1_roll_deploy.py:202`, `:297`);
  - **The Phreaker** gets *Magnetic Splice* (`phase5_pipeline_shift.py:48`);
  - **The Cipher** gets *Algorithmic Arbitrage* (`phase6_operations.py:87`);
  - **The Prodigy** probably gets *Brute-Force Bypass* (`phase1_roll_deploy.py:308`, `:329`). This needs an engineer to audit, because Prodigy's own protocol shares that code path.

`RULES.md` v0.34 §6 gives The Spook *Burn Notice* only. An Institutional Override belongs to the Client Company.

**Effect of removing the bridge** (lever `Z_nobridge`; six-phase, same seeds):

| Metric (2P / 3P / 4P) | Sweep (bridged) | Bridge removed |
| :--- | :---: | :---: |
| White Hat win-rate range | 43.0–65.1 / 28.3–48.7 / 20.0–37.5 | **45.9–52.8 / 29.3–36.8 / 22.4–26.7** |
| The Spook win % | 65.1 / 48.7 / 37.5 | 52.0 / 36.8 / 24.2 (≈ par) |
| DTO win % | 75.7 / 65.0 / 58.5 | **88.3 / 80.0 / 75.4** |
| Legacy DTO win % (same fix) | 72.0 / 61.0 / 53.2 | 83.8 / 75.1 / 71.2 |
| Mean rounds | 8.30 / 7.98 / 7.76 | 8.21 / 7.85 / 7.66 |
| Total Wipeout | 19.0 / 6.5 / 2.5% | 16.6 / 5.7 / 2.2% |

**What this means:**
- The "Spook watch item" (OQ-17) is an artifact of the leaked Slush Fund, not of Burn Notice timing. Once the leak is removed, the White Hat Operatives are well balanced: a spread of 4–7 points.
- **DTO's true dominance is much larger than the sweep shows.** The leak spread Slush Fund across every Spook player, which diluted DTO's edge.
- **Every company and White Hat guardrail must be re-baselined after this fix.** The legacy "no-regression" baseline is contaminated too.

---

## 1. Guardrail verdicts

| Guardrail | Verdict | Basis |
| :--- | :--- | :--- |
| Mean/median rounds 8–11 | **FAIL (3P, 4P), but tunable.** Mostly driven by a weak bot. | VentureGreedBot is Patient Zero in 82% of 4P games under 6 rounds. With it replaced, 4P = 8.29 and 3P = 8.39. The v1.0 track lever fixes this robustly. |
| Singularity ≤ 45% | PASS | Range 15–31% across all levers. |
| Total Wipeout ≤ 15% (2P) | **FAIL. Structural and pre-existing.** | It was 18.1% under legacy. No D5-compliant lever tested gets 2P below 14.5% without side effects (§2.4). |
| Zero-income turns ≤ 30% | PASS | 25–27% at baseline; 22–24% with the package. |
| Bot win-rate spread ≤ 45 pts | PASS | 31–35 at baseline; 34–42 with the package (closest to the limit in 2P/3P). |
| Top company ≤ legacy | **FAIL, and understated by the defect.** | DTO is top in every pod, in every configuration, under both sequences. |
| Watch: Aegis | **Confirmed regression.** About 65% of it is Release Bandwidth 3. | §2.3 |

---

## 2. Diagnosis

### 2.1 Short 3P/4P games come mostly from VentureGreedBot, and partly from flat 8 Secrets
- **Patient Zero in games under 6 rounds:** VentureGreedBot is Patient Zero in 70% / 78% / 82% of them (2P / 3P / 4P). Omnidyne (Defense Grid Capacity 1) is the most over-represented company.
- **Whether VentureGreed is present (baseline 4P):** games that include VentureGreed average 7.65 rounds (n = 2,400). The 600 games without it average 8.18.
- **Replacing VentureGreed with AdaptiveBalancedBot in the rotation:** 4P goes 7.76 → **8.29** (under 6 rounds: 11.0% → 4.3%), 3P goes 7.98 → **8.39** and 2P goes 8.30 → 8.62.
- **Six-phase is not the cause:**
  - Under legacy, at 8 Secrets in 2P/3P, the share of games under 6 rounds was already 7.3% / 10.9%.
  - Under legacy with 4P at 8 Secrets (`legacy_flat8`), 4P drops to 7.43 rounds, with 12.8% under 6.
  - Six-phase actually *mitigates* the flat-8 effect: 4P has 11.0% of games under 6 rounds and averages 7.76.
- **Conclusion:** the 4P gap is the expected flat-8 trade-off (D5 Notes), amplified by one weak bot. It is not a sequence defect. A real-table concern remains: one negligent player ends the game for three others.

### 2.2 DTO's gain is not about the bonus Secret's proportion, and not about cash
- **Starting Secrets proportion: no.** On 4P same seeds:
  - legacy at 12 Secrets: 53.2%; legacy at 8: 52.7%;
  - six-phase at 8: 58.5%; six-phase at 12: 57.3%.
  - Changing Secrets moves DTO by ≤ 1.2 points. The sequence change moves it by +4–6 points in every pod, including 2P/3P where Secrets did not change.
- **Slush Fund cash path: no.** The `$1 per Secret` cash absorb fires about 0.05 times per DTO player-game. Disabling it (lever B2) changes nothing (Δ ≤ 0.3 points).
- **The real driver is the free Slush Fund absorb:**
  - It averages **2.6–3.1 Corporate Secrets saved per DTO player-game** (about 1.8–2.1 uses), and fires in every SETEC version.
  - Together with the +1 starting Secret, that is about 4 Secrets of extra buffer on an 8-Secret base: **+50% effective life**.
  - DTO's Patient Zero rate is 12–25%, against 28–68% for the other companies.
- **Part of the six-phase increase is redistribution from Aegis's collapse.** Aegis Release Bandwidth 4 alone takes DTO down 1.8 / 1.1 / 2.7 points.

### 2.3 Aegis: about 65% of the drop is Release Bandwidth 3
- Raising Aegis to Release Bandwidth 4 cuts its capped graduations from 32–34% to 10%, and recovers its win rate:

  | Aegis win % (2P / 3P / 4P) | Value | Share of the drop recovered |
  | :--- | :---: | :---: |
  | Six-phase (Release Bandwidth 3) | 27.1 / 15.3 / 8.5 | — |
  | Six-phase (Release Bandwidth 4) | 36.9 / 21.3 / 16.2 | 61% / 50% / 88% |
  | Legacy | 43.3 / 27.3 / 17.3 | — |

- Most of the rest comes from Triage Bandwidth 1 compounding under D1 routing.
- Adding Triage Bandwidth 2 as well (lever A2) overshoots in 2P: Aegis wins 52.9%.

### 2.4 The 2P Total Wipeout is structural
- Every player faces the same exited cubes, so breaches are highly correlated.
- Given that a breach ended the game, the chance it was a Total Wipeout is 25.5% / 8.0% / 3.0% (2P / 3P / 4P). That roughly follows a geometric decay (≈ 0.25ⁿ⁻¹): it is the chance that *every* survivor breaches in the same Phase 4.
- 2P sits at 16–20% under every configuration tested, legacy included (18.1%).
- Only the softer Unpaid Ransom Leak gets it to ≤ 15% (14.5% on the fixed engine), and that costs +3–6 points of Singularity and a wider bot spread.
- This is a 2P-format property, not a v0.34 regression.

---

## 3. Lever table

All runs are six-phase, 3,000 games per pod, same seeds. Values are 2P / 3P / 4P; Δ is against the matching baseline. "Bridged" means the current engine; "Fixed" means the White Hat Override bridge is removed.

### 3.1 Single levers (bridged engine, comparable to the sweep)

| Lever | Mean rounds | 4P < 6 rounds | Singularity % | Total Wipeout % | DTO win % | Aegis win % | Bot spread |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| Baseline v0.34 | 8.30 / 7.98 / 7.76 | 11.0% | 25.4 / 19.0 / 15.7 | 19.0 / 6.5 / 2.5 | 75.7 / 65.0 / 58.5 | 27.1 / 15.3 / 8.5 | 34.5 / 34.3 / 31.2 |
| (a) Aegis Release Bandwidth 3 → 4 | +0.03 / +0.04 / +0.02 | 11.4% | +1.3 / +0.3 / +1.3 | −0.4 / +0.1 / −0.3 | −1.8 / −1.1 / −2.7 | **+9.9 / +6.0 / +7.7** | 35.9 / 35.3 / 32.8 |
| (a2) + Aegis Triage Bandwidth 1 → 2 | +0.06 / +0.08 / +0.07 | 11.1% | +2.9 / +2.1 / +3.2 | −1.8 / −1.1 / −0.3 | −4.5 / −3.9 / −5.3 | +25.8 / +17.3 / +15.6 (overshoots) | 34.5 / 37.9 / 33.8 |
| (b1) DTO starting Secrets bonus +1 → 0 | −0.03 / −0.04 / −0.03 | 11.4% | −0.9 / −0.4 / −0.7 | +1.5 / +0.6 / +0.2 | **−11.5 / −14.2 / −18.3** | +1.6 / +1.7 / +2.0 | 36.0 / 37.3 / 33.2 |
| (b2) Slush Fund without the cash absorb | 0 / 0 / 0 | 11.0% | 0 | 0 | 0 / −0.2 / −0.3 | 0 | ≈ 0 |
| (b3) Slush Fund absorbs 2 → 1 | −0.02 / −0.02 / −0.01 | 11.0% | −1.1 / −0.5 / −0.5 | +1.4 / +0.6 / +0.3 | −4.1 / −4.6 / −5.4 | +1.2 / +1.0 / +1.3 | 35.2 / 36.4 / 33.3 |
| (b4) DTO +1 Secret → +$2 Starting Cash | −0.04 / −0.04 / −0.02 | 12.0% | −0.8 / +0.2 / −0.2 | +0.6 / +0.7 / +0.3 | −9.3 / −12.6 / −14.3 | +0.9 / +1.1 / +2.0 | 37.8 / 36.8 / 32.9 |
| (c) v1.0 Corruption Track 4 → 5 (new space 1 = "Lose 1 🔬") | **+0.78 / +0.70 / +0.68** | 10.5% | −1.4 / −0.7 / −0.7 | −0.7 / −0.9 / −0.3 | −1.1 / −1.8 / −3.5 | +3.0 / +1.7 / +0.5 | 29.2 / 34.6 / 28.7 |
| (c′) same, with a no-effect space 1 | +0.79 / +0.72 / +0.69 | 10.2% | −0.9 / −0.4 / +0.3 | −1.6 / −1.4 / −0.3 | −3.1 / −2.6 / −4.8 | +2.1 / +1.7 / +0.1 | 30.2 / 34.7 / 28.5 |
| (d) Softer Unpaid Ransom Leak (no leak if the shortfall is ≤ $1) | +0.19 / +0.17 / +0.16 | 9.9% | **+5.9 / +5.3 / +4.3** | −2.6 / −1.3 / −0.4 | 0 / −0.9 / −1.2 | 0 / −1.5 / +0.1 | 40.4 / 38.1 / 34.6 |
| (x) VentureGreed → AdaptiveBalanced (diagnostic only) | +0.32 / +0.41 / +0.54 | 4.3% | +5.6 / +5.3 / +5.8 | 0 / +1.3 / +0.9 | +1.9 / +2.1 / −1.1 | −3.9 / −3.1 / −1.5 | 26.7 / 23.8 / 19.2 |

### 3.2 Packages on the fixed engine (the configuration I recommend evaluating)

| Configuration | Mean rounds | Singularity % | Total Wipeout % | Zero-income % | DTO win % | Aegis win % | White Hat range | Bot spread |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Fixed, legacy sequence (new "no-regression" baseline) | 7.88 / 7.53 / 8.60 | 16.2 / 9.8 / 31.8 | 17.7 / 5.5 / 1.1 | — | 83.8 / 75.1 / 71.2 | 46.8 / 31.0 / 16.2 | ≤ 8 pts | 56.1 / 51.3 / 44.5 |
| Fixed, v0.34 as-is | 8.21 / 7.85 / 7.66 | 23.9 / 17.7 / 14.9 | 16.6 / 5.7 / 2.2 | 27.1 / 25.8 / 25.3 | 88.3 / 80.0 / 75.4 | 29.0 / 14.8 / 8.6 | 4–7 pts | 32.7 / 32.0 / 25.5 |
| Fixed + (a) + (c) | 9.04 / 8.60 / 8.39 | 24.4 / 18.6 / 16.1 | 15.6 / 4.2 / 2.0 | — | 84.9 / 76.7 / 70.3 | 38.0 / 23.1 / 15.5 | 5–8 pts | 34.5 / 34.1 / 25.3 |
| Fixed + (a) + (c) + (b3) Slush Fund absorbs 1 | 9.03 / 8.61 / 8.38 | 23.7 / 18.3 / 15.8 | 17.1 / 4.6 / 2.3 | — | 78.8 / 70.4 / 61.7 | 39.1 / 24.0 / 16.7 | 6–8 pts | 35.8 / 36.0 / 28.3 |
| Fixed + (a) + (c) + Slush Fund Blue-only | 9.03 / 8.60 / 8.39 | 23.4 / 18.2 / 15.9 | 16.8 / 4.7 / 2.5 | — | 77.3 / 64.8 / 57.1 | 38.7 / 24.8 / 17.1 | 6–8 pts | 34.1 / 35.6 / 25.0 |
| Fixed + (a) + (c) + (b1) + (b3) *(touches D5)* | 9.00 / 8.58 / 8.35 | 22.7 / 17.6 / 15.4 | 18.5 / 5.5 / 2.4 | 24.2 / 22.9 / 22.4 | 68.2 / 55.3 / 44.8 | 40.7 / 26.6 / 20.2 | 6–10 pts | 38.9 / 39.6 / 32.2 |
| **Fixed + (a) + (c) + Slush Fund once per game (absorb 2, DTO keeps 9)** | **8.99 / 8.55 / 8.34** | 22.2 / 17.1 / 15.1 | 19.2 / 5.6 / 2.5 | **24.1 / 22.8 / 22.4** | **62.0 / 53.0 / 46.0** | **41.2 / 27.3 / 19.3** | 6–9 pts | 41.1 / 41.7 / 34.4 |
| Same package, fresh seeds (base 777, 2,000 games per pod) | 8.99 / 8.57 / 8.32 | 21.6 / 16.9 / 15.4 | 19.1 / 5.1 / 2.6 | 24.2 / 22.9 / 22.3 | 62.8 / 52.7 / 46.0 | 43.2 / 27.2 / 20.1 | 7–10 pts | 40.9 / 40.9 / 33.8 |

**Side effects:**
- **(c) v1.0 track:**
  - It is the only lever that moves rounds by more than 0.2.
  - Singularity share stays flat (it delays only the first Version Switch), and Total Wipeout falls slightly.
  - It does **not** remove the under-6-round tail: VentureGreed dies to Blue early regardless.
  - Income per turn rises from 2.31 to 2.52 and zero-income turns fall by about 3 points, because the gentler first version leaves more dice In Production.
- **(d) Softer Unpaid Ransom Leak:**
  - It is the only lever that reaches the 2P Total Wipeout target on the fixed engine (14.5%).
  - It inflates Singularity by 4–6 points, hurts VentureGreed further and widens the bot spread.
  - Not recommended.
- **Slush Fund once per game:**
  - It brings DTO to the legacy level or below in every pod, against either baseline.
  - It pushes the bot spread to about 41 in 2P/3P, inside the 45 limit but the closest margin in the package.
  - It raises 2P Total Wipeout by about 2.5 points versus (a)+(c) alone, because DTO now breaches alongside its opponent more often.

---

## 4. Recommendation

**Do not sign off v0.34 balance as-is.** The six-phase sequence itself is healthy and should be kept:
- the economy goals are met;
- bot spread fell from 63 to 34;
- Singularity is under control;
- no sequence-level invariant was violated.

The company and White Hat numbers, however, rest on a rules-fidelity defect. The pacing and Aegis issues have cheap, well-isolated fixes.

**Step 0 (engineering, before any tuning):** remove the White Hat → Institutional Override bridge:
- every override check should test `player.company` only;
- every Signature Protocol check should test `player.white_hat` only;
- keep the archetype path for legacy archetype-only setups;
- then re-run the product-owner sweep.

**Recommended package (3 changes):**
1. **Aegis Release Bandwidth 3 → 4.** Aegis keeps Triage Bandwidth 1 and Defense Grid Capacity 3.
2. **v1.0 Corruption Track 4 → 5 spaces**, on both v1.0 SETEC Version Cards.
   - Insert a new space 1, "Lose 1 🔬", which reuses an existing space effect.
   - Track lengths become 5 / 5 / 6. This is the same at every player count, so it is D5-compliant.
3. **Slush Fund becomes once per game** instead of once per SETEC version. It still absorbs up to 2 Corporate Secret loss, and DTO keeps its 9 starting Corporate Secrets, so D5 is untouched.

**Projected results** (fixed engine, two seed sets):
- mean rounds 9.0 / 8.55 / 8.33, with median 9 in every pod;
- Singularity 15–22%;
- zero-income turns 22–24%;
- bot spread 34–42;
- DTO 62 / 53 / 46 (top company, but inside even the contaminated legacy baseline);
- Aegis 41–43 / 27 / 19–20, back to its legacy level.

**What the package does not fix:**
- **2P Total Wipeout stays at about 19%.** I recommend treating this as a 2P-format property (§2.4) and resetting the 2P guardrail rather than tuning it.
- **The tail of games under 6 rounds** (about 12% in 4P) is driven by VentureGreedBot.
  - That is a follow-up item: re-tune the bot, or add a "Lean" defense floor to VentureGreed's heuristics.
  - It is not a rules change.
- **Omnidyne** becomes the weakest company on the fixed engine: 28 / 12 / 8%. This is a new watch item for the next cycle.

**Fallback if the user rules the bridge intentional** (White Hats *do* carry the paired Override):
- use (a) + (c) + (b3), Slush Fund absorbing 1 on the bridged engine;
- this gives DTO 70.1 / 57.7 / 48.0 against legacy 72.0 / 61.0 / 53.2 (2P margin about 1 point on fresh seeds) and rounds 9.10 / 8.73 / 8.45.

---

## 5. Decisions needing user sign-off

1. **Bridge ruling.** Do White Hat Operatives grant the paired Client Company's Institutional Override?
   - `RULES.md` says no.
   - If no, engineering removes the bridge, and every company/White Hat guardrail is re-baselined (legacy included).
2. **Aegis Release Bandwidth 3 → 4.** This changes a `[TUNE]` value in RULES.md §3 and the PnP mat.
3. **v1.0 Corruption Track 4 → 5**, with a new space 1 "Lose 1 🔬" on Script Kiddie and Data Scraper.
   - This changes card content (PnP version cards) and `corruption_track_lengths`.
   - A no-effect space measures the same, but "no-effect / blank space" would be a **new term and is not proposed**.
4. **Slush Fund once per game.** This makes Slush Fund an exception to the once-per-version cadence of Institutional Overrides, so RULES §3/§6 wording and the glossary *Institutional Override* entry would need a note.
   - Alternative that touches D5's "DTO 9": DTO +1 → 0 combined with absorb 1.
5. **Guardrail policy.**
   - Reset the 2P Total Wipeout guardrail to ≤ 20%, or accept it as a known 2P property.
   - Re-baseline "top company ≤ legacy" on the fixed engine.
6. **Pacing acceptance.** Is about 12% of 4P games ending before round 6 acceptable, given that it is mostly a bot artifact? Should a VentureGreedBot heuristic follow-up be scheduled?

**Glossary:** this report uses canonical §7 terms only. No new term is introduced. Item 4 needs a cadence note on an existing entry, and item 3 deliberately avoids a "blank space" term.
