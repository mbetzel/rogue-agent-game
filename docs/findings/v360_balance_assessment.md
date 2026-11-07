# v0.36.0 Balance Assessment (Phase 45, game-designer)

**Date:** 2026-11-06 · **Inputs:** `v360_market_share_telemetry_report.md`, `sim_results/v360_market_share_sweep.json`, `sim_results/v360_market_share_outlier_seeds.json`, plan `docs/explorations/2026_11_market_share_red_rework_plan.md` §2 / §6 / §8, spec `docs/specs/v360_market_share_red_rework_spec.md` §5 / §8 / §13 / §15.1, `FINDINGS.md` §31–§32.
**No changes** were made to `sim/`, `tests/`, `scripts/`, `RULES.md`, `PLAN.md` or `FINDINGS.md`.

**Follow-up slices.** All use the sweep script's `build_engine` / `run_pod` unchanged, paired seeds, on a **new seed base `7000`** (2,000–3,000 games per pod), so they also check the base-42 numbers on fresh seeds. Every cell is `GameConfig.v036(...)` plus existing levers, or a bot attribute (`market_share_policy`, `research_focus_v036`). Three slices go beyond a lever and are labelled as such:
- **Strong kamikaze.** A scratch wrapper on `research_policy.plan_research3` stops a strict Secrets leader with `collapse_seeking` from regaining Market Share.
- **No-VentureGreed roster.** The sweep's `BOT_CLASSES` without `VentureGreedBot`.
- **Ad Campaign instrumentation.** A read-only wrapper on `execute_ad_campaigns`.

Scratch drivers are in `/tmp/claude-1000/-home-mike-antigravity-rogue-agent/c78dd19b-eba2-4247-87af-5e92e16290c0/scratchpad/`: `grid.py`, `runstd.py`, `extras.py`, `kami_bot.py`, `botwr.py`, `vg.py`, `vgfix.py` and `novg.py`. Total compute was about 8 minutes.

## Verdict

**NOT APPROVED. Do not flip the defaults yet.** The mechanics work, but the end-reason split can't be tuned until one bot is fixed.

What works:
- Market Collapse always lands late: never in ≤ 5 rounds, p10 is Round 8.
- Total Wipeout falls a lot.
- No setup takes any trigger above 47%, down from 61–74%.
- The Red block rate and Red purchases both rise.
- Kamikaze Collapse is a mild "end it while ahead" lever. It is not degenerate.

The failing three-way split is mostly a bot-roster artifact:
- **VentureGreedBot fails under v0.36.** It lost its only Secrets engine (Patent Filing).
  - It becomes Patient Zero in **56% of its seats**.
  - It wins **4.5 / 1.5 / 0.7%** (2P / 3P / 4P), against 52 / 46 / 42% in v0.35.
- **It alone produces most of the Patient Zero share.**
  - Without it, v0.36 Patient Zero is **29 / 19 / 17%**, and Singularity rises to **48 / 56 / 55%**.
  - That is the opposite failure from the one the sweep reports.
- **The right starting Secrets depend on this bot, and the two answers are 2–3 Secrets apart.** The current roster needs **9 / 11 / 12**. A roster without VentureGreed needs **8 / 8 / 9** or **7 / 8 / 8**.

One rules [TUNE] is robust to the bot roster: **Market Share start −2 (17 / 18 / 18)**. A second, v1.0 payout → `$0`, is recommended but needs a User decision. Fix VentureGreed, then re-sweep a small grid before the defaults flip.

## 1. Telemetry validation: genuine vs bot artifact

| Product-owner flag | Diagnosis | Evidence |
|---|---|---|
| Patient Zero 41–43% (above 40%) | **Mostly a bot artifact (VentureGreed).** Also about 2–3 pts from a bot weight. | VentureGreed seats, 3P V036: 1.57 Secrets at the end, Patient Zero 56%, `$5.19` unspent. V035: 3.50 Secrets, of which 5.81 came from Patent Filing. Without VentureGreed: Patient Zero 29.0 / 18.5 / 16.9%. Bot weight: `comparison_weight × $4` (= 4.0) is more than `blue_value` (3.0), so bots let a Blue cube through (−1 Secret) to fight for the comparison. `comparison_weight = 0.5` lowers Patient Zero by 3.5 / 2.2 / 1.6 pts (1,500 games per pod). |
| Market Collapse 20–22% (below the ~30% probe) | **Genuine and expected.** The probe had no payouts and no Red-aware bots. | NO_PAYOUT +6–7 pts and NAIVE +6–7 pts. Comparison payouts make bots regain (regain share 37% vs 21%), which delays Collapse. VentureGreed's early breaches pre-empt about 3–6 pts more (no-VentureGreed roster: Market Collapse 23 / 25 / 28%). Market Share start is the lever: −2 gives +7 to +10 pts in both rosters. |
| v1.0 ties 65–84%, v2.0 38–57% | **Genuine and structural, but the "any tie" metric overstates it.** | Every player faces the same Red cubes. At the v1.0 fill (about Round 4) the median gap between best and worst Market Share is **0 (2P) / 1 / 1**. The real "nothing happens" rate is all-tied: **v1.0 65 / 41 / 31%, v2.0 37 / 12 / 4%**. Under the User's shared-places rule (§8.2), a top or bottom tie still pays out. No bot or lever changes this: ties are within ±3 pts in every cell. |
| Public Relations 60–62% of maxed tracks | **Bot artifact, as Patents was in v0.35.** VentureGreed and RecklessSaboteur put it first. | RANDOM_FOCUS: 18–19%. Moving Public Relations later in those two bots' `research_focus_v036`: 18–21% (VG_REL / VG_DEF), or 0% (PR_LAST). **Watch:** Public Relations L4 holders under random focus win 27 / 14 / 12%, against Defense 52 / 42 / 35% and Release 52 / 37 / 31%. It is the weakest L4 along with Triage. It is not dominant. |
| Ad Campaign almost unused | **Card frequency first, then the bot gate. The `$2` cushion is minor.** | When Ad Campaign is drawn (~1/3 of games), seats latch an action in only **0.07–0.09** seat-games. The bot then *wants* to use it 10–19% of the time; it is affordable 65–72% of the time. So 100% use would still be under 0.1 Market Share per seat per game. Also, the ★ face gives no income, so each +1 Market Share effectively costs `$4` (the forgone `$2` from a Red income face plus the `$2` paid). *Brand Protection* (Block 1 Red + `$2`) dominates it. |
| Customer Poaching almost unused | **Card frequency.** | 0.07 / 0.11 / 0.15 poaches per game when the card is in the market. Red dice owned are about 0.4–0.9 per seat, and the ★ face shows 1 time in 6. |
| Market buys +81–100%, end Money `$2.4` | **Ransom removal plus VentureGreed hoarding.** It is not caused by the payouts. | v0.35 Red ransom cost about `$8` per seat (§31). NO_PAYOUT buys match V036. Without VentureGreed, end Money is `$1.5` and buys are 1.3–1.5 per seat, against v0.35's `$0.15` and 0.63 per seat. The VentureGreed seats alone buy 5.7 dice (4.0 Yellow) and still end with `$5.2`, because Money has no route to Secrets. |
| Kamikaze signal 60–74% | **Inflated metric.** | It counts ties, and Collapse hits 1.4 / 1.8 / 2.2 players at once. Collapsers hold a *strict* Secrets lead in **60 / 45 / 41%** of Collapse games, against a chance level of 69 / 50 / 43%. A collapser wins in **70 / 53 / 48%**, against a chance level of 71 / 57 / 54%. Both are at or below chance. |
| Company spread 17.5 / 19.5 (3P / 4P) | **Mostly a carried-over company effect, plus sampling noise.** | On seeds 7000: 19.3 / 15.1 / 21.4, against 12.3 / 17.5 / 19.5 on seeds 42. DTO is +10–13 pts above fair share and AEGIS +6–8. Helix, Omnidyne and Prometheus sit 5–8 pts below. No tune moves it (17.9–22.1 in every cell). The max-minus-min of 6 rates carries about 4–5 pts of noise at this sample size. Leave it for the company-identity phase. |

## 2. Bot roster win rates (the main hidden finding)

Win rate by bot (2,000 games per pod, seeds 7000; shared wins split):

| Bot | V035 2P / 3P / 4P | V036 2P / 3P / 4P | V036 RANDOM_FOCUS |
|---|---|---|---|
| Accelerationist | 63.6 / 50.8 / 44.4 | 82.0 / 58.4 / 44.7 | 68.0 / 43.9 / 28.1 |
| SecOpsTurtle | 47.9 / 19.1 / 8.7 | 75.1 / 46.8 / 37.3 | 57.0 / 26.0 / 17.7 |
| AdaptiveBalanced | 38.9 / 17.4 / 7.7 | 50.2 / 35.5 / 23.6 | 64.7 / 54.6 / 42.6 |
| RecklessSaboteur | 48.1 / 33.3 / 22.3 | 38.2 / 24.5 / 18.7 | 51.1 / 38.7 / 35.5 |
| **VentureGreed** | **51.6 / 46.0 / 41.9** | **4.5 / 1.5 / 0.7** | **9.1 / 3.4 / 1.1** |

Moving Public Relations later in VentureGreed's focus barely helps (3–10%). Its "minimise shielding, hoard Yellow Money" logic is now a losing strategy: Money has nothing to convert into. The other bots are healthier than under v0.35, so v0.36 helps defensive play. **The design question behind this:** with Patents gone, the only scalable source of *new* Secrets is gone. Victory is now mostly "lose the fewest Secrets", plus occasional ★ gains (B2 / Y1 / Y3, *Burn Notice*, L3 Breakthroughs). That weakens the "engine-building" half of the core pillar for economy-first players. See question Q3.

## 3. Guardrails after the recommended rules [TUNE] (seeds 7000, 3,000 games per pod)

| Cell | Pod | Patient Zero | Singularity | Market Collapse | Rounds | ≤ 5 rounds | Total Wipeout | Red block | Regain share | All-tied v1.0 / v2.0 |
|---|---|---|---|---|---|---|---|---|---|---|
| V036 (baseline) | 2P | 42.8 | 37.8 | 19.4 ❌ | 8.61 | 5.2% | 4.9% | 15.1% | 37% | 66 / 37% |
| | 3P | 39.1 | 40.1 | 20.7 ❌ | 8.80 | 2.7% | 1.2% | 14.7% | 35% | 41 / 12% |
| | 4P | 41.1 ❌ | 37.1 | 21.8 ❌ | 8.75 | 2.1% | 0.3% | 14.4% | 34% | 31 / 5% |
| **MS−2 + Secrets +1** (17/18/18, 9/11/12) | 2P | 35.6 | 35.7 | 28.7 ✅ | 8.69 | 3.0% | 4.1% | 15.9% | 37% | 66 / 37% |
| | 3P | 32.2 | 37.4 | 30.4 ✅ | 8.84 | 1.2% | 0.7% | 15.4% | 35% | 41 / 12% |
| | 4P | 33.3 | 34.2 | 32.5 ✅ | 8.77 | 1.0% | 0.1% | 15.1% | 34% | 31 / 4% |
| **+ v1.0 payout `$0`** (v2.0 `$4` only) | 2P | 33.4 | 33.7 | 32.9 ✅ | 8.66 | 2.6% | 4.1% | 15.6% | 25% | – / 34% |
| | 3P | 30.0 | 36.6 | 33.4 ✅ | 8.81 | 1.0% | 0.5% | 15.2% | 25% | – / 11% |
| | 4P | 31.6 | 32.7 | 35.7 ✅ | 8.74 | 1.0% | 0.1% | 14.9% | 24% | – / 4% |

- In both tuned cells, no setup takes any trigger above 41%.
- Market Collapse still never happens in ≤ 5 rounds. Rounds to the first Collapse: p10 is Round 8 (Round 7 with the v1.0 payout at `$0`, 3P).
- Red purchase share is 27–30%. Market buys rise 3–9% (about 1.03–1.09×).

**These numbers assume the current VentureGreed.** The no-VentureGreed roster (2,000 games per pod) gives:

| Cell | Pod | Patient Zero | Singularity | Market Collapse | Rounds | Total Wipeout |
|---|---|---|---|---|---|---|
| V036 | 2P | 29.0 | 48.0 | 23.0 | 9.11 | 8.1% |
| | 3P | 18.5 | 56.3 | 25.2 | 9.33 | 2.1% |
| | 4P | 16.9 | 55.1 | 28.0 | 9.34 | 1.1% |
| MS−2 | 2P | 28.5 | 40.0 | 31.5 ✅ | 8.98 | 7.6% |
| | 3P | 17.7 | 47.2 | 35.0 | 9.18 | 2.1% |
| | 4P | 16.5 | 46.0 | 37.6 | 9.17 | 1.3% |
| MS−2, Secrets 8/8/9 | 2P / 3P / 4P | 28.5 / 29.5 / 26.4 ✅ | 40.0 / 39.8 / 40.2 | 31.5 / 30.7 / 33.5 | 8.98 / 8.97 / 9.00 | 7.6 / 3.1 / 1.3% |
| MS−2, Secrets 7/8/8 | 2P / 3P / 4P | 35.5 / 29.5 / 33.8 ✅ | 35.6 / 39.8 / 35.6 | 28.9 / 30.7 / 30.5 | 8.84 / 8.97 / 8.87 | 9.7 / 3.1 / 1.8% |

Read the two tables together:
- **Market Share −2 is right in both rosters.**
- **Starting Secrets swing from +1 to −2/−3 depending on one bot.** So they must not be re-tuned until VentureGreed is fixed.

The User's per-player-count rationale (plan §3.7) holds only while one bot breaches about half the time. With competent bots, the Patient Zero ending barely grows with player count: 29 → 18 → 17%.

## 4. Degenerate-strategy check

- **Kamikaze Market Collapse: mild, not degenerate.**
  - The spec's KAMIKAZE cell (Generic-shield sign flip on RecklessSaboteur) matches V036 almost exactly. The required-blocking rule (§15.1 #4) blunts it, and RecklessSaboteur leads strictly only about 7% of its turns.
  - **Strong stress (KAMI_ALL):** every bot that strictly leads in Secrets deprioritises Red blocks and stops regaining.
    - Market Collapse rises only +3.6 / +2.0 / +1.2 pts, and rounds fall by 0.03.
    - Collapsers then win 87 / 73 / 68%, against a chance level of 72 / 57 / 54%. The lever works when the leader pulls it.
  - **Adoption by one bot** (AdaptiveBalanced, SecOps or Accelerationist, current or tuned config): **+0 to +2 pts** win rate (≈ 1 SE). This is the usual "end the game while ahead" tension. Trailing players still get Phases 5–6, and final Market Share is the first tiebreaker. **Watch in human playtests; no rule needed.**
- **Stalling:** none seen. Rounds are 8.6–8.9, Collapse never comes before Round 7, and only 1 game in 3,000 per pod reached Round 12+.
- **Runaway leader:** final Market Share by finishing rank is flat (about 7 for every rank), so there is no share snowball. Market Share decides 10–19% of games as a tiebreaker.
- **Player-count scaling:** Total Wipeout is 4–6% at 2P and under 1.3% at 3–4P (v0.35: 16 / 6 / 2%). The Patient Zero scaling seen today is a bot artifact (§3).
- **2P short games:** 5.2% of 2P games end in ≤ 5 rounds (v0.35: 2.2%). Secrets +1 brings this back to 3.0%. Without VentureGreed it is a non-issue.

## 5. Recommendations

### A. Rules [TUNE] for User approval

1. **Market Share start 19 / 20 / 20 → 17 / 18 / 18.** This is the one change that is robust to the bot roster.
   - Current roster (PO MS−2 cell): Market Collapse 27 / 30 / 31%, Singularity −6 to −9 pts, Patient Zero unchanged.
   - No-VentureGreed roster: Market Collapse 31.5 / 35 / 37.6%, Singularity 40 / 47 / 46%.
   - Red block rate +0.5–1 pt; rounds −0.1 to −0.15.
2. **v1.0 comparison payout `$2` → `$0`**, so the only comparison is at the v2.0 change (`$4`). **User decision:** this reverses part of plan §8.5.
   - Removes the comparison that is all-tied in 65 / 41 / 31% of games.
   - Market Collapse +3–4 pts, Patient Zero −1 to −2 pts.
   - Regain share 37% → 25% (still in band).
   - Rounds unchanged; Red block rate −0.2 pt.
   - Alternative: keep `$2`, and judge the tie guardrail on the all-tied rate instead of any tie (see Q2).
3. **Starting Secrets: hold 8 / 10 / 11 for now.** Re-tune after bot fix B1, from this grid: {8/10/11, 8/9/10, 8/8/9}.
   - With the current roster, +1 (9 / 11 / 12) plus item 1 puts all three triggers at 28–37%.
   - Without VentureGreed, 8 / 8 / 9 or 7 / 8 / 8 is needed.
   - Do not ship +1 on the current evidence.
4. **No change** to the Public Relations L4 rate, the regain cap, payout size or the Red ★ costs.
   - The L4-RATE, L4-BOTH and PAYOUT-LOW / PAYOUT-HIGH cells move nothing outside noise, apart from the payout's effect on Collapse.
   - The Red ★ cards are low-impact because they come up so rarely, not because they are mispriced. Ad Campaign is weak by construction (an effective `$4` per Market Share). **Optional [TUNE] for the User:** `r2_share_gain` 1 → 2. Its impact is capped at under 0.1 uses per seat per game either way, so it is cosmetic.

### B. Bot-only fixes (no rule change; needed before the next acceptance sweep)

1. **(Blocking) Port VentureGreedBot to v0.36.**
   - Shield Blue at normal value; don't run "minimise shielding" once Secrets ≤ ~5.
   - Spend surplus Money on Y1 / B2 paid Secrets and *Ad Campaign*.
   - Use a non-Public-Relations-first `research_focus_v036`.
   - Target: a win rate in the same range as the other bots, and no more than ~15% Patient Zero per seat.
   - Measured so far: the research reorder alone gives 3–10% wins, which is not enough.
2. **`comparison_weight` 1.0 → 0.5**, or cap the comparison term below `blue_value`, so bots stop trading a Secret for a `$4` comparison place they often can't pay anyway (51% of v2.0 charges are forgiven).
   - Patient Zero −3.5 / −2.2 / −1.6 pts, Market Collapse +2.1 / +1.0 / +1.0 pts.
   - Red block rate −1.4 pts (still about +3 pts over v0.35).
3. **Public Relations later in the focus order for VentureGreed and RecklessSaboteur** (`research_focus_v036`). Public Relations share of maxed tracks goes from about 60% to 18–21%, which passes the ≤ 50% guardrail.
4. **Ad Campaign use:** use it whenever below max and affordable, with no cushion. Expected effect is negligible (under 0.1 Market Share per seat per game). Do it for fidelity.
5. **Telemetry / metrics** (product-owner script):
   - Report the kamikaze metric as strict lead and won-as-collapser, both against chance.
   - Report the all-tied comparison rate next to any tie.
   - Report win rate by bot.
   - Report company spread with a bootstrap CI.

### C. Next step

After B1–B3, re-run the spec §8 sweep with these cells:
- V036 + MS−2;
- × starting Secrets {8/10/11, 8/9/10, 8/8/9};
- × v1.0 payout {`$2`, `$0`};
- plus RANDOM_FOCUS;
- 2,000 games per pod.

Then sign off.

## 6. Questions for the User

1. **Approve Market Share start 17 / 18 / 18** (item A1)?
2. **v1.0 comparison:** drop it (`$0`, only the v2.0 `$4` comparison), or keep `$2` and accept the null comparisons (judging the tie guardrail on all-tied rather than any tie)?
3. **Design question:** v0.36 removes the only scalable way to *gain* Secrets. Money now mostly piles up: VentureGreed ends with `$5`, and the table average is `$1.5–2.4`. Is "survive with the most Secrets" acceptable as the main victory path? Or should the next phase look at a Money → Secrets outlet using existing components (for example Y1 / B2 availability or pricing)? I am **not** proposing a new term or mechanic. This is a question.
4. **Starting Secrets 8 / 10 / 11:** OK to re-open after the bot fix, since the evidence for it came from the same VentureGreed-heavy roster?

No new glossary terms are needed. "Strict Secrets lead" and "all-tied" are metric names only and do not appear in rules text.
