# v0.36.0 Balance Assessment, Iteration 1 (game-designer)

**Date:** 2026-11-06 · **Inputs:** `v360_market_share_iter1_telemetry_report.md`, `sim_results/v360_market_share_iter1_sweep.json` (2,000 games per pod, seed 42), the previous assessment `v360_balance_assessment.md`, and plan §10 decisions.
**No changes** were made to `sim/`, `tests/`, `scripts/`, `RULES.md`, `PLAN.md` or `FINDINGS.md`.

**Fresh-seed slices.** I ran these on base `7000` (3,000 games per pod) with the repo's `run_pod` unchanged. The cells are `GameConfig.v036(starting_secrets_by_player_count=...)`, so they use the iteration-1 defaults: Market Share 17 / 18 / 18 and the v2.0 `$4` comparison only. I re-checked the chosen Secrets on seed 42 (2,000 games per pod).

Scratch files are in `/tmp/claude-1000/-home-mike-antigravity-rogue-agent/c78dd19b-eba2-4247-87af-5e92e16290c0/scratchpad/`:
- drivers: `gd_iter1.py`, `gd_iter1_bots.py`;
- data: `gd_iter1.json`, `gd_iter1b.json`.

## Verdict

**APPROVED WITH TUNE.** Set starting Secrets to **7 / 7 / 8** (2P / 3P / 4P), and keep the v1.0 comparison dropped. With that one change, every §6 guardrail that can be met through these rules passes in every pod, on both seed sets. The remaining fails come from bots or companies (§2), and none of them blocks the default flip.

**Final v0.36 [TUNE] values:**

| Item | Value |
|---|---|
| Market Share start (= max) | 17 / 18 / 18 |
| Version-change comparison | v2.0 → v3.0 only, `$4` (v1.0 comparison dropped) |
| Starting Secrets | **7 / 7 / 8** |

Unchanged:
- Public Relations Track: 2 🔬 per step; per-round cap 1/1/2/2/3 by level.
- Marketing ★ cards at `$5` / `$4` / `$5`; Ad Campaign is `$2` → +1 Market Share.
- `$6` starting Money.

## 1. Starting Secrets (V1D = v1.0 comparison dropped)

**Fresh seeds** (base 7000, 3,000 games per pod). PZ = Patient Zero, including Total Wipeout. The 95% CI is shown for PZ only.

| Secrets | Pod | PZ [95% CI] | Singularity | Market Collapse | Rounds | Total Wipeout | ≤ 5 rounds |
|---|---|---|---|---|---|---|---|
| 8 (current) | 2P | 23.4 [21.9–25.0] ❌ | 39.4 | 37.2 | 8.95 | 5.7% | 0.3% |
| **7** | **2P** | **30.0 [28.4–31.7]** | **35.5** | **34.5** | **8.83** | **7.1%** | **0.9%** |
| 10 (current) | 3P | 15.9 ❌ | 44.4 ❌ | 39.8 | 9.12 ❌ | 1.1% | 0.0% |
| 9 | 3P | 20.4 ❌ | 41.9 ❌ | 37.7 | 9.04 ❌ | 1.6% | 0.0% |
| 8 | 3P | 25.6 [24.1–27.2] (lower CI below floor) | 38.6 | 35.8 | 8.94 | 1.8% | 0.3% |
| **7** | **3P** | **32.9 [31.3–34.6]** | **34.1** | **32.9** | **8.79** | **2.6%** | **1.2%** |
| 11 (current) | 4P | 14.3 ❌ | 43.9 ❌ | 41.9 ❌ | 9.11 ❌ | 0.3% | 0.0% |
| 10 | 4P | 18.7 ❌ | 40.9 ❌ | 40.3 ❌ | 9.04 ❌ | 0.6% | 0.0% |
| 9 | 4P | 23.5 [22.1–25.1] ❌ | 38.1 | 38.3 | 8.95 | 0.9% | 0.1% |
| **8** | **4P** | **30.5 [28.9–32.2]** | **34.1** | **35.4** | **8.83** | **1.0%** | **0.7%** |
| 7 | 4P | 38.2 | 29.9 | 31.9 | 8.65 | 0.9% | 1.7% |

**Re-check on seed 42** (7 / 7 / 8, 2,000 games per pod):

| Pod | PZ [95% CI] | Singularity | Market Collapse | Rounds | Most-concentrated setup |
|---|---|---|---|---|---|
| 2P | 31.0 [29.0–33.1] | 34.8 | 34.2 | 8.86 | 42.7% |
| 3P | 34.5 [32.5–36.6] | 33.5 | 32.1 | 8.76 | 39.5% |
| 4P | 30.3 [28.4–32.4] | 33.6 | 36.1 | 8.83 | 42.1% |

**Choosing 3P = 7 over 8.** At 8, the 3P Patient Zero CI touches the 25% floor on both seed sets (seed 42: 26.4%). At 7, every trigger sits between 32% and 35%, the most even split in the grid. The cost: 3P Total Wipeout rises from 1.8% to 2.6%, and short games from 0.3% to 1.2%. Both are far below v0.35's 5.9% Total Wipeout and 2.2% short games.

**4P = 8** is the only centred value. At 9, Patient Zero falls below 25% on both seed sets (23.5% / 24.7%). At 7, Singularity drops under 30%.

**2P = 7.** 2P Total Wipeout is 7.1–7.5%, against v0.35's 16%. That passes.

**Implication:** the per-player-count rationale behind 8 / 10 / 11 (plan §3.7) does not hold with the fixed bots. Patient Zero barely grows with player count once VentureGreed defends itself, so the spread is +1 Secret at 4P only. This reverses the User-approved 8 / 10 / 11, so it needs User approval (Q1).

**v1.0 comparison stays dropped.**
- Restoring it (`$2`, cell K-S7_8_8, fresh seeds) leaves the v1.0 comparison all-tied in 65 / 43 / 36% of games.
- 2P then fails the < 50% guardrail (seed 42: 51.6%, lower CI 50.0%). It adds about 10 pts of regain share and buys nothing.
- With it dropped, v2.0 is all-tied in 36 / 11 / 5% of games. That passes.

## 2. Remaining fails: rules issue or bot artifact?

| Item | Measured (tuned config unless stated) | Judgement |
|---|---|---|
| **Rounds** above 9.0 at 3P/4P | 9.10–9.12 at 10/11 Secrets; **8.76–8.86 at 7/7/8** | **Rules, fixed by the Secrets tune.** Too many Secrets let Singularity run long. |
| **Release Track 68–72% of maxed tracks** | Random focus: 33–35% at 7/7/8. Default focus: Accelerationist and VentureGreed are both Release-first, and no bot is Public Relations- or Defense-first. | **Bot artifact.** Same pattern as Patents in v0.35 and Public Relations in the first sweep. **Watch item, not blocking:** under random focus, L4 holders win 41–66% on Release and 45–67% on Defense, against 11–42% on Triage and 17–44% on Public Relations. Release and Defense look like the strongest tracks. Part of this is selection (survivors max tracks). Look at it in the track-identity pass, not here. |
| **Bot spread 31–37 pts** (RecklessSaboteur 6.5% at 4P) | Random focus: RecklessSaboteur 31–49%; spread 20–34 pts. | **Bot artifact.** RecklessSaboteur's new `research_focus_v036` puts Triage first, and Triage is the weakest L4 (11–22% wins at 3P/4P). VentureGreed is now 42–62%, a healthy v0.35-level strength. The v0.35 spread was already 21–36 pts. |
| **Company spread 16.6–25.9** (V035 14–18) | 4P, iteration-1 grid vs V035: DTO 40.3 vs 34.5%; Omnidyne 20.5 vs 24.0%. The others are within ±3 pts. The same holds under random focus (DTO 35–49%). | **Company asymmetry, about +5 pts over v0.35.** It comes mostly from DTO, plus Omnidyne losing ground. It is not caused by this tune, which moves spread by under 1 pt. The bootstrap CI is ±4–5 pts. Defer to the planned company-identity phase; needs User acceptance (Q2). |
| **Economy: buys 1.8–2.0× V035, end Money ≈ `$1.9`** | Payout-driven inflation is gone: there is only one `$4` comparison, and 56–63% of its charges are forgiven. | **Not a problem.** This is the intended effect of removing the Red ransom: v0.35 drained about `$8` per seat, and the first sweep showed NO_PAYOUT ≈ V036. Money now ends at `$1.9`, against `$0.5`. Acceptable, and it gives Money a meaningful role as the second tiebreaker. |
| Kamikaze | Strict-lead and won-as-collapser are at chance (4P default focus +3–4 pts on strict lead; won ≤ chance everywhere). | No issue. |
| Ad Campaign / Customer Poaching | 0.011–0.019 uses per seat; 0.02–0.05 Market Share moved per game. | Low-impact flavour cards (rare face). Accept. |

## 3. Guardrails at the final values (7 / 7 / 8, v1.0 dropped)

| Guardrail | Result |
|---|---|
| End-reason split 25–40% | ✅ all pods, both seed sets (lowest trigger 29.9%) |
| Setup concentration ≤ 55% | ✅ max 43% |
| Rounds 8.4–9.0 | ✅ 8.76–8.86 |
| Total Wipeout ≤ v0.35 | ✅ 7.1–7.5% / 2.3–2.6% / 1.0–1.1%, against 15.8 / 5.9 / 2.1% |
| Red block rate | ✅ 14.6–15.4%, against about 10.4% (+4–5 pts) |
| Red share of buys ≤ 35% | ✅ about 27% |
| All-tied comparisons < 50% | ✅ 37 / 10 / 4% |
| Regain share 20–40% | ✅ 24–26% |
| No track > 50% of maxed tracks | ❌ Release about 69% (bot artifact; random focus 33–35% ✅) |
| Company spread ≤ v0.35 | ❌ 20–23 pts (company asymmetry; defer) |
| No Collapse in ≤ 5 rounds | ✅ 0 |

## 4. Recommendations

**Rules [TUNE], for User approval:**
1. Starting Secrets **8 / 10 / 11 → 7 / 7 / 8**.
2. Confirm the v1.0 comparison stays dropped.

**Bot-only, not blocking.** Do these before the next balance sweep:
- Give RecklessSaboteur a non-Triage-first `research_focus_v036`, for example `('RELEASE', 'TRIAGE', 'DEFENSE', 'PATENT')`.
- Make one of Accelerationist / VentureGreed Defense-first, or Public Relations-second, so the roster's focus orders cover all four tracks.
- Or run acceptance sweeps with `research_focus_mode="random"` as the reference roster.

**Docs, after sign-off:**
- `RULES.md`: Market Share 17 / 18 / 18, the v2.0-only comparison, and Secrets 7 / 7 / 8.
- `FINDINGS.md`: §33, covering both iterations.
- `PLAN.md`: Experiment status.

## 5. Questions for the User

1. Approve starting Secrets **7 / 7 / 8**? This replaces the approved 8 / 10 / 11; the per-count rationale was an artifact of the broken VentureGreed.
2. Accept the company spread (about 20–23 pts, about +5 pts over v0.35, mainly DTO) for now, and defer it to the company-identity phase?
3. Accept the Release concentration as a bot-roster artifact (random focus 33–35%), and log Release/Defense vs Triage/Public Relations L4 strength as a watch item for a later track pass?

No new glossary terms are introduced.
