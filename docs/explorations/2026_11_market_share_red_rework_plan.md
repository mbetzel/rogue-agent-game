# Red Rework: Market Share & Market Collapse — Pre-SDLC Design Plan (`v0.36.0` candidate)

Status: design locked with User 2026-11-06 (Section 8 decisions and Section 7 terms approved). Engineering not started. Supersedes the Phase 44 Red rebalance exploration (`FINDINGS.md` §31, not adopted).

## 1. Problem

- Red is a flat cash tax with no real decision. At `$1` per cube, blocking Red is worth less than any income face. Red block rate is ~10%, and Red dice are ~0.16 buys per seat.
- Red's real impact is the **Unpaid Ransom Leak**: about **2.3 Secrets per seat** per game, hitting players who happen to be broke in Phase 4. Turning Red damage off drops Patient Zero games from 59 / 69 / 72% to 28 / 33 / 38% (2P / 3P / 4P).
- Red does not connect to the rest of the game's systems.
- Cryptographic Patents has proven very strong: about +2.0 Secrets per seat, and 20+ Secret outliers at L4.

## 2. Design direction

Red becomes **corporate competition** instead of a cash attack:

1. Unblocked Red cubes (**Market Manipulation**) lower your **Market Share**.
2. You spend research to win Market Share back, at a rate set by the **Public Relations Track**, which replaces Cryptographic Patents.
3. At each SETEC Version change, players compare Market Share for **Money**.
4. If anyone's Market Share hits 0, **Market Collapse** triggers the Final Round. It is a third end trigger alongside Patient Zero and Singularity.

**Being out of Money never costs Secrets.** The Unpaid Ransom Leak concept is removed.

## 3. Proposed rules

### 3.1 Red cubes

- Each unblocked Red cube in Phase 4 lowers your Market Share by 1. Red no longer costs Money or Secrets.
- Red shields block as today. **Stage 2 `Any` shields are assigned by the player's free choice** once cubes are known (User, 2026-11-06). The printed 4-tier priority is removed for all colors; bots keep their own heuristics.
- Snowball Recycle is unchanged.

### 3.2 Market Share track

- One track on each Company Terminal Mat, from 0 up to the starting value.
- Starting value: **19 at 2P, 20 at 3–4P** `[TUNE]`. This is also the maximum; Market Share can never go above it.
- Market Share cannot drop below 0.

### 3.3 Regaining Market Share (replaces Cryptographic Patents)

The Cryptographic Patents track is replaced by the **Public Relations Track** (User, 2026-11-06). It keeps the 5-level shape (step costs 1 / 2 / 2 / 3 🔬) and both Breakthroughs:

| Level | Effect `[TUNE]` |
|---|---|
| L0 | In Phase 6, regain up to **+1** Market Share per round at **2 🔬** each |
| L1 (Breakthrough) | Gain `$3` (unchanged) |
| L2 | Cap **+2** per round |
| L3 (Breakthrough) | Gain your 2nd Purple die from the Personal Reserve (unchanged) |
| L4 | Cap **+3** per round, and/or **1 🔬** each (one or both, to be set by the sweep) |

- The per-round cap works like Triage and Release bandwidth. It stops players from dumping research into share all at once before a comparison.
- Patent Filing is removed. Secrets still come from B2 / Y1 paid ★ actions, Y3, the Spook's *Burn Notice*, and the Defense / Release L3 Breakthroughs.

### 3.4 Version-change comparison (Money)

- **When it happens:** in Phase 2, right after the final space of `v1.0` or `v2.0` is covered and resolved. Doing it in Phase 2 means nobody can time a regain in Phase 6 knowing the comparison is coming. `v3.0` filling is Singularity, which ends the game, so there is no comparison then.
- **Payout `[TUNE]`** (User, 2026-11-06): **`$2` at the `v1.0` → `v2.0` change, `$4` at the `v2.0` → `v3.0` change.**
  - Highest Market Share: **gain the payout from the bank**. The bank always pays in full.
  - Lowest Market Share: **pay the payout to the bank**, or as much as they have. **Any shortfall is forgiven** (User, 2026-11-06). They never lose Secrets.
  - **All Money goes through the bank; players never pay each other** (User, 2026-11-06). Bottom players pay the bank; top players are paid by the bank.
  - **Ties are shared places** (User, 2026-11-06): everyone tied for top gains the payout, and everyone tied for bottom pays. If all players tie, nothing happens.
- There is **no Money comparison at game end**. Instead, **final Market Share becomes the first Secrets tiebreaker** (User, 2026-11-06). The new order is Market Share > Money > Active Colored Module Dice in Ready for Release > Research Tokens > fewest dice Under Development > shared. The same order ranks players in a Total Wipeout.

### 3.5 Market Collapse (new end trigger)

- Checked at the end of Phase 4, together with the Patient Zero check.
- If any surviving player has **0 Market Share**, the current round becomes the **Final Round**. All surviving players finish Phases 5–6, then the game is scored.
- **No one is eliminated, and there is no extra penalty** (User, 2026-11-06). The player at 0 scores normally. They will usually lose Secret ties, since final Market Share is the first tiebreaker.
- If Patient Zero and Market Collapse happen in the same round, Patient Zero rules apply: the breached players are eliminated and the round is the Final Round.
- Singularity in Phase 2 ends the game before Market Collapse could trigger.

### 3.6 Red die becomes Marketing

- The Red die's subtitle changes from *FinSec / Encryption* to **Marketing**. Faces are unchanged: `Block 1 Red`, `+$2` ×3, `Glitch`, `Red ★`.
- **Red `★` Variant Cards** (User, 2026-11-06). Card names and costs are spec tasks:
  - **R1:** `Block 1 Red` + `+$2` (today's R1, renamed so it no longer refers to ransom).
  - **R2:** pay `$2` → +1 Market Share.
  - **R3:** move 1 Market Share from the rival with the most Market Share to you.
- Today's R2 *Threat Bounty* and R3 *Short Squeeze* are retired.

### 3.7 Starting Secrets by player count

- **8 / 10 / 11** at 2P / 3P / 4P `[TUNE]`, approved by User 2026-11-06. This reverses the flat 8 Secrets from v0.34.0.
- Why: Patient Zero triggers when *any* player breaches, so it grows with player count. Market Collapse barely does, because every player faces the same Red cubes. The extra Secrets at 3–4P restore the balance between the three endings.

### 3.8 Other rules to update

- **DTO *Slush Fund*:** absorbs Secret loss from Blue only. Remove the unpaid-ransom wording.
- **Defense Grid L4** (`+$1` per blocked cube): unchanged.
- **Money glossary entry:** remove "pay Red Ransomware".

## 4. Evidence (probe, not rules code)

Probe: [`scripts/explore_v360_market_collapse_probe.py`](../../scripts/explore_v360_market_collapse_probe.py). Outputs are in `sim_results/v360_market_collapse_probe*.txt`. The probe runs with Red ransom off and no Patent filings. Market Share drops 1 per unblocked Red cube; at 0 it triggers the Final Round. Bots regain share by a fixed rule: 2 🔬 each, at most +1 per round. Money payouts and new Red `★` variants are **not** modeled.

| Pod | Starting Secrets | Market Share start | Patient Zero / Singularity / Market Collapse | Rounds | Games |
|---|---|---|---|---|---|
| 2P | 8 | 19 | 37 / 33 / 30% | 8.56 | 800 |
| 3P | 10 | 20 | 35 / 32 / 33% | 8.78 | 400 |
| 4P | 11 | 20 | 36 / 33 / 31% | 8.79 | 400 |
| *v0.35 reference* | *8* | *—* | *PZ games 59 / 69 / 72%* | *8.87 / 8.74 / 8.63* | *600* |

Supporting measurements (Red damage off):

- **Unblocked Red per player** is 3.4 / 5.7 / 9.0 in the `v1.0` / `v2.0` / `v3.0` windows. `v2.0` starts around round 5 and `v3.0` around round 8. About 90% of games reach `v3.0`.
- **Ties:** without deliberate Red play, the gap between best and worst player is only 1–2 cubes. Rankings tie 38–67% of the time, so comparisons need players to block Red and regain share on purpose to mean anything.
- **Money in hand:** at the Phase 2 Version change, the median player has `$2`, and 75% have under `$4`. That is why the bank funds the top payout.
- **Patents removal:** removing both Patents and Red damage keeps pacing close to v0.35. Rounds are 9.02 / 8.65 / 8.41, and Patient Zero games 40 / 57 / 58%.
- **Setup tilt at 2P:**
  - v3.0 card: Corrupted Kernel 39 / 31 / 29%, Zero-Day Override 35 / 35 / 30%.
  - Company seats: from Prometheus 42 / 32 / 25% to DTO 33 / 37 / 30%.
  - White Hats: within ±4 points.
  - Setup tips the balance without breaking it, which is the goal.
- **If hitting 0 eliminated the player instead:** everyone tends to hit 0 in the same round, which would make 25–66% of games Total Wipeouts. This is why Market Collapse does not eliminate.

## 5. Sim implementation plan

New `GameConfig` levers. Defaults reproduce v0.35 exactly.

| Lever | Values |
|---|---|
| `red_mode` | `"RANSOM"` (v0.35) / `"MARKET_SHARE"` |
| `market_share_start_by_player_count` | `{2: 19, 3: 20, 4: 20}` |
| `market_collapse_enabled` | bool |
| `version_share_payout` | `{v1→v2: 2, v2→v3: 4}`; top paid by bank, bottom pays bank (shortfall forgiven), ties share places |
| `share_regain_cost_by_level` / `share_regain_cap_by_level` | 2 🔬 each; caps L0 1 / L2 2 / L4 3 |
| `patents_mode` | `"PATENTS"` (v0.35) / `"SHARE_REGAIN"` |
| `starting_secrets_by_player_count` | `{2: 8, 3: 10, 4: 11}` (existing lever) |
| `red_variant_set` | `"V035"` / `"MARKETING"` |
| `tiebreak_order` | v0.35 order / Market Share first |
| `any_shield_policy` | v0.35 tiers / bot free choice |

Engine changes:

- Phase 4 Red resolution and the Stage 2 tiers.
- Phase 2 Version-change comparison.
- End-of-Phase-4 Market Collapse check, with a new `EndGameReason.MARKET_COLLAPSE`.
- Phase 6 regain action, replacing Patent Filing.
- Telemetry:
  - Market Share curves.
  - Regain spend.
  - Comparison payouts and shortfalls.
  - Red block rate.
  - Red die buys.
  - End-reason split by setup (Version cards, company, White Hat).

Bot policies (required; v0.35 bots ignore Red):

1. **Red-aware shield allocation:** value Red blocks more as Market Share nears 0, and before a Version change.
2. **Regain policy:** spend research on share when the player is in danger or when a comparison is close.
3. **Track focus:** include the replacement track in each bot's focus order.

## 6. Guardrails (sweep acceptance)

- **End-reason split:** each of Patient Zero, Singularity and Market Collapse at **25–40%** in every pod. Single setups may go outside this, but no setup should take any trigger above ~55%.
- **Rounds:** 8.4–9.0 mean.
- **Total Wipeout:** no higher than v0.35 (2P ≤ 16%).
- **Red blocking:** Red block rate clearly above v0.35's ~10%.
- **Red dice:** purchase share rises, but stays ≤ ~35% of market buys.
- **Ties:** Version-comparison ties well below the ~50% seen with today's bots.
- **Research:** share regain takes some but not most of research spend (target 20–40% `[TUNE]`). No track takes more than ~50% of maxed tracks.
- **Company win-rate spread:** no worse than v0.35 (~15 points).
- **Money:** end-of-game Money and purchase counts reported against v0.35. Bank payouts should not inflate dice buys by more than ~20%.

## 7. Glossary & terminology

**New terms**, approved by User 2026-11-06. Add them to Section 7 when `RULES.md` is updated:

| Term | Meaning |
|---|---|
| **Market Share** | Per-player track and resource. Starts at 19 / 20, drops 1 per unblocked Red cube, and is regained with research. |
| **Market Collapse** | End trigger: a surviving player at 0 Market Share after Phase 4 makes the current round the Final Round (no elimination). |
| **Marketing** | The Red die's subtitle, replacing *FinSec / Encryption*. |
| **Market Manipulation** | The Red cube theme, replacing *Ransomware / Financial Wiretaps*. |
| **Public Relations Track** | The research track that replaces Cryptographic Patents. It sets how much Market Share you can regain per round and at what cost. |
| ***Brand Protection* / *Ad Campaign* / *Customer Poaching*** | Red `★` (Marketing) Variant Cards R1 / R2 / R3 (User, 2026-11-06). |

**Terms to retire** (add to Retired Terms): *Unpaid Ransom Leak*, *Ransomware / Financial Wiretaps*, *Cryptographic Patents Track*, *Patent Filing*, *FinSec*, *Ransom Insurance* (R1 name), *Threat Bounty*, *Short Squeeze*.

Do not reuse *Corruption* for Market Share. It clashes with the Corruption Track used by Black cubes.

## 8. Decisions (User, 2026-11-06)

1. **Shortfall:** forgiven. The bottom player pays the bank what they have.
2. **Ties:** shared places. All Money goes through the bank; players never pay each other.
3. **Game-end tiebreaker:** final Market Share becomes the first tiebreaker, ahead of Money. This also applies to Total Wipeout ranking.
4. **Market Collapse penalty:** none.
5. **Payouts:** `$2` at `v1.0` → `v2.0`, `$4` at `v2.0` → `v3.0` `[TUNE]`.
6. **Stage 2 `Any` shields:** the player's free choice. The printed priority tiers are removed.
7. **Red `★` set:** Block + `$2` (old R1), buy back share (`$2` → +1), poach share (take 1 from the rival with the most).
8. **Starting Secrets:** 8 / 10 / 11 approved.

Still open for the spec:
- Card names and costs for the new Red `★` variants.
- The Public Relations Track L4 choice (cap +3, a 1 🔬 rate, or both).
- Mat layout for the Market Share track.

## 9. SDLC routing

1. `game-designer`: sweep regain rates, payouts and Market Share starts once Red-aware bots exist.
2. `principal-engineer`: spec covering config levers, phase hooks, bot policies and telemetry.
3. `senior-engineer` ↔ `staff-engineer`: build and review.
4. `product-owner`: telemetry sweep ↔ `game-designer` balance sign-off against Section 6.
5. `graphic-designer`: Market Share track and replacement track on the Company Terminal Mat; Red Variant Cards; the Marketing die label.

Docs to update after sign-off:

- `RULES.md`: Sections 2, 3 (Phases 2 / 4 / 6), 5, 6A–B, the Client Company table, Section 7 glossary and Retired Terms.
- `PLAN.md`
- `FINDINGS.md`

## 10. Balance iteration 1 decisions (User, 2026-11-06)

Source: [docs/findings/v360_balance_assessment.md](../findings/v360_balance_assessment.md) (game-designer: NOT APPROVED pending the VentureGreed bot fix) and [docs/findings/v360_market_share_telemetry_report.md](../findings/v360_market_share_telemetry_report.md). These supersede Sections 3.2, 3.4 and 3.7 where they differ.

1. **Market Share start: 17 / 18 / 18** (2P / 3P / 4P) `[TUNE]`, down from 19 / 20 / 20.
2. **The `v1.0` → `v2.0` comparison is dropped.** Only the `v2.0` → `v3.0` comparison remains, at `$4` `[TUNE]`.
3. **Starting Secrets are re-opened.** Re-sweep 8 / 10 / 11, 8 / 9 / 10 and 8 / 8 / 9 after the bot fixes.
4. **Next phase:** look at a Money → Secrets outlet using existing components (Y1 / B2 availability or pricing). v0.36 removes Patent Filing, so "lose the fewest Secrets" is now the main way to win and Money piles up.

## 11. Balance iteration 2 decisions (User, 2026-11-06)

Source: [docs/findings/v360_balance_assessment_iter1.md](../findings/v360_balance_assessment_iter1.md) (game-designer: **APPROVED WITH TUNE**) and [docs/findings/v360_market_share_iter1_telemetry_report.md](../findings/v360_market_share_iter1_telemetry_report.md). These supersede Section 10.3.

1. **Starting Secrets: 7 / 7 / 8** (2P / 3P / 4P) `[TUNE]`, replacing 8 / 10 / 11. The per-player-count scaling came mostly from the broken VentureGreed bot. With fixed bots, every rules guardrail passes in every pod on two seed sets (each end reason 30–36%, 8.8 rounds).
2. **Company spread (20–23 points):** deferred to the company-identity phase as a watch item (DTO up, Omnidyne down).
3. **Release Track concentration** is a bot artifact. The Release / Defense versus Triage / Public Relations strength gap is a watch item for a later track pass.

Final v0.36 `[TUNE]` values: Market Share start 17 / 18 / 18; one Market Share comparison at `v2.0` → `v3.0` (`$4`); starting Secrets 7 / 7 / 8; everything else as in Section 3.
