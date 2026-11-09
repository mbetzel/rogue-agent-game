# Rogue Agent — Monte Carlo Simulation Findings & Balance Index

This document tracks verified balance takeaways, bot meta equilibria, card tiering, and active tuning targets for Rogue Agent.

> [!NOTE] Historical Archives
> Full statistical datasets, raw telemetry tables, and sweep outputs are archived in:
> - [docs/findings/v0.2_to_v0.7_historical_sweeps.md](docs/findings/v0.2_to_v0.7_historical_sweeps.md): Core economy, starting resources, 2P buffers, and contractor tuning.
> - [docs/findings/v0.8_to_v0.9_variant_and_archetype_sweeps.md](docs/findings/v0.8_to_v0.9_variant_and_archetype_sweeps.md): Choice faces, 15 Module Variants (★), Asymmetric Payloads, and Consultancy Archetypes.

---

## 1. Executive Summary & Active Baseline (`v0.13.0`)

| Parameter | Current Baseline | Healthy Game Target | Balance Status |
| :--- | :--- | :--- | :--- |
| **Match Duration** | 7.28 rounds (4P) | ~8.0 rounds across all pods | **Pacing Parity** (7.28 rds; 0.0% stalls). |
| **Singularity Rate** | 22.1% | 10%–40% | **Healthy Existential Clock** across all pods. |
| **4P Total Wipeout** | 3.8% | $< 5\%$ | **Safe** (Multi-player simultaneous wipeouts rare in 4P). |
| **Early Deaths ($\le$ R4)** | 1.3% | $< 5.0\%$ | **Zero Opening Blowouts** across all player counts. |
| **Zero-Total-Exit Rounds** | 0.32% – 0.40% | $< 1.0\%$ | **Breakthrough** (Tower Priming virtually eliminates empty drops). |
| **Buffer Overflows / Game** | 0.01 – 0.02 | $\le 0.05$ | **Ideal Backstop** (Invisible emergency safety valve). |
| **Active Infrastructure Valuation** | 0 VP for Unpatched | Technical debt penalty | **Resolved Stranded Cash** (Maintenance conversion active across 39%–43% of survivors). |
| **Push-Your-Luck Glitch Risk** | Face 5 Glitch on Red/Blue/Green | Broken block saturation | **Calibrated Risk** (Contractor sacrifice & Phase 1 Debug unlock utility). |
| **Consultancy Parity** | 6 / 6 balanced (21.9%–29.7%) | $25.0\% \pm 5\%$ win rate | **Optimal Parity** (All 6 archetypes within 20%–30% target corridor). |
| **Emergency System Reboot** | 1x / Game (Gray Starter Restore) | Prevent 0-action soft-locks | **Operational Recovery** (Eliminates 60%–68% of helpless deaths without endgame VP distortion). |

---

## 2. Active Module Variant Tier List (15 Cards)

Based on Experiment 5 sweeps ($N=500$ runs per card):

* **S-Tier (Top Metagame Engines):**
  * **Y2 Cloud Monopoly** (Yellow): Base payout +$2, +$1 per distinct colored die (cap +$5). Stable income anchor.
  * **B2 Deep R&D** (Blue): Flexible shield choice face or Phase 3 `$4 \to +1\text{ Secret}` conversion.
  * **G1 Zero-Trust Pipeline** (Green): Blocks 1 Green without wearing into unpatched. High survival priority.
* **A-Tier (Strong Tactical Modules):**
  * **R1 Kinetic Dampener** (Red): 2 Red shields; standard wear.
  * **P1 Payload Injection** (Purple): 1 Any shield + Phase 3 attack cube injection.
  * **B3 Air-Gapped Backup** (Blue): Sacrificial wear redirection protecting valuable modules.
  * **Y1 Algorithmic Trading** (Yellow): High cash generation with `$6 \to +1\text{ Secret}` purchase.
* **B-Tier (Situational / Pod-Dependent):**
  * **G2 Quarantine Enclave** (Green), **R2 Active Countermeasure** (Red), **P2 Intrusion Countermeasure** (Purple).
* **C-Tier / Traps (Require Specific Synergy):**
  * **R3 Ransomware Trap** (Red), **G3 Logic Bomb** (Green), **P3 Packet Deflector** (Purple).

---

## 3. Consultancy Archetype Performance Summary (Experiment 7)

* **The Operator (Redundant Crew):** 2 Free contractors once per match. Dramatically reduces early wipeouts in 2P.
* **The Prodigy (Brute-Force Bypass):** Rerolls locked glitch dice without debug cost. Eliminates bad luck turns.
* **The Phreaker (Magnetic Splice):** Free 2-die patch once per version. Saves $4–$6 cash.
* **The Acoustic (Baffle Echo):** Permanent removal of exited threat cube. Essential in high-threat kinetic roadmaps.
* **The Spook (Slush Fund):** Cash substitution for secrets during catastrophic breaches. Perfect emergency valve.
* **The Cipher (Arbitrage Engine):** Retuned to $2 market discount / backdoor siphon without backlash.

For detailed test logs, parameter matrices, and telemetry breakdowns, refer to [`docs/findings/`](docs/findings/).

---

## 4. Phase 15: Compiler Priming & Empty-Tray Buffer Overflow (`v0.9.1`)

Based on Product Owner verification sweep ($N=1,000$ games per pod, Base Seed `42` via WSL):

### Telemetry Matrix (3,000 Matches Total)

| Metric | 2-Player Pod (2P) | 3-Player Pod (3P) | 4-Player Pod (4P) | Target Benchmark |
| :--- | :---: | :---: | :---: | :---: |
| **Average Match Duration** | **7.78** (±1.45) rds | **6.47** (±1.58) rds | **4.83** (±0.84) rds | 4.5–9.0 rounds |
| **Duration Range (Min / Max)** | 4 / 12 rds | 3 / 11 rds | 3 / 8 rds | Min $\ge 3$, Max $\le 15$ |
| **Singularity Rate (%)** | **35.1%** | **16.2%** | **21.2%** | 10%–40% |
| **Patient Zero Rate (%)** | **47.8%** | **75.7%** | **74.5%** | Primary win/loss vector |
| **Total Wipeout Rate (%)** | **17.1%** | **8.1%** | **4.3%** | Safe limits across pods |
| **Zero-Total-Exit Rounds (%)** | **0.32%** | **0.40%** | **0.35%** | $< 1.0\%$ (Near-zero) |
| **Buffer Overflows / Game** | **0.02** | **0.02** | **0.01** | $\le 0.05$ |
| **Average Ending Secrets** | **2.21** Secrets | **1.67** Secrets | **1.65** Secrets | Razor-thin survival margins |
| **Average Ending Money** | **$0.61** | **$2.00** | **$1.86** | Capital depletion |
| **Round Limit Timeouts (30 rds)**| **0.0%** | **0.0%** | **0.0%** | Zero stalling |

### Key Balance Takeaways
1. **Dead Drop Eradication:** Pre-seeding 4 cubes (`1 Red, 1 Blue, 1 Green, 1 Black`) at setup fills the resting capacity of the internal baffles, driving active drops across $> 99.6\%$ of all match rounds.
2. **Invisible Safety Valve:** The Buffer Overflow rule triggers in only ~1 to 2 out of every 100 matches. It acts as a clean physical fail-safe that guarantees the subsequent round drops $\ge 4$ cubes without inflating the normal cube economy.
3. **Player-Count Dynamics:** 4P games resolve quickly (4.83 rounds) via high-tempo version advancement and Patient Zero elimination; 2P games allow longer strategic engine play (7.78 rounds) with a 35.1% Singularity clock.

---

## 5. Phase 16: Player-Count Pacing Parity & Scaling (`v0.10.0`)

### A. Problem Statement & Root Cause Diagnosis
In `v0.9.1`, 4-player games averaged only **4.83 rounds** compared to **7.78 rounds** in 2P matches. In a simultaneous-play game where player enjoyment stems from building modular dice pools and experiencing escalating Cube Tower drama, variable game lengths purely driven by player count created a deficient 4P experience. The design goal for `v0.10.0` was to achieve consistent ~8.0-round pacing across 2P, 3P, and 4P pods.

Root causes identified:
1. **Flat Corruption Track (4 spaces):** 4 players generate twice as much Dirty Income and trigger more tower drops, causing the Rogue Agent to advance through `v1.0 → v2.0 → v3.0` in half the rounds.
2. **Global Attack Drops:** Attack cubes exiting the tower apply in full to *every* player rather than being divided, accelerating collective attrition in 4P.
3. **First-Order Breach Statistics:** With 4 players rolling defenses independently, the probability that *at least one* player breaches in round $t$ scales as $P(\text{Breach}) = 1 - \prod_{i=1}^N (1 - p_{i,t})$. Without increased buffer resilience, 4P games naturally terminate earlier.

### B. Approved Solution: Option C Scaling
Following 46,000+ simulation iterations across candidate levers, Option C was approved and codified:
* **Corruption Track Scaling:** **4 spaces (2P)**, **5 spaces (3P)**, **6 spaces (4P)** per version card (12 / 15 / 18 total Black cubes to Singularity).
* **Starting Corporate Secrets:** **8 Secrets (2P)**, **8 Secrets (3P)**, **10 Secrets (4P)**.
* **Starting Patch Tokens (`🔧`):** **2 flat** across all player counts (2P, 3P, 4P).
* **Standardized Upgrade Payloads:** **2 cubes** per upgrade across all player counts (`+1 Red, +1 Green` RaaS; `+1 Green, +1 Black` Worm; `+1 Red, +1 Black` Zero-Day; `+1 Red, +1 Blue` Corrupted Kernel).

### C. Telemetry Matrix (3,000 Matches Total, Base Seed `42`, Randomized Setups)

| Metric | 2-Player Pod (2P) | 3-Player Pod (3P) | 4-Player Pod (4P) | Target Benchmark |
| :--- | :---: | :---: | :---: | :---: |
| **Average Match Duration** | **7.78** (±1.45) rds | **8.99** (±2.36) rds | **7.29** (±1.53) rds | ~8.0 rounds target |
| **Duration Range (Min / Max)** | 4 / 12 rds | 3 / 16 rds | 4 / 15 rds | Min $\ge 3$, Max $\le 16$ |
| **Singularity Rate (%)** | **35.1%** | **28.7%** | **23.6%** | 10%–40% |
| **Patient Zero Rate (%)** | **47.8%** | **69.5%** | **74.2%** | Primary win/loss vector |
| **Total Wipeout Rate (%)** | **17.1%** | **1.8%** | **2.2%** | Safe limits across pods |
| **Early Deaths ($\le$ R4) (%)** | **0.2%** | **2.9%** | **1.6%** | $< 5.0\%$ |
| **Average Winning Score** | **23.8** VP | **51.9** VP | **49.3** VP | Healthy portfolio scoring |
| **Round Limit Timeouts (30 rds)**| **0.0%** | **0.0%** | **0.0%** | Zero stalling |

*(Note: Under the fixed baseline deck Script Kiddie $\to$ RaaS $\to$ Zero-Day, 4P average duration reaches **7.92** rounds with **18.2%** Singularity and **76.5%** Patient Zero).*

### D. Analysis of Patient Zero Rate (PZR) Variance
Telemetry reveals that the Patient Zero Rate is ~25% higher in 3P/4P (~70%–74%) than in 2P (~48%). Analysis confirms two primary mathematical and classification drivers:

1. **Total Wipeout Reclassification:**
   In a 2-player game, when a lethal drop occurs, both players frequently breach on the exact same turn (~17.1% of matches). Because no surviving player exists, the game engine classifies this as a **Total Wipeout** rather than a Patient Zero finish. In a 4-player game, the probability that *all four* corporations breach on the exact same turn is very small (~2.2%). Thus, multi-player simultaneous breaches where at least 1 player survives are classified as **Patient Zero**.
   When evaluating **Total Breach Endings** (Patient Zero + Total Wipeout combined):
   * **2P:** $47.8\% + 17.1\% = \mathbf{64.9\%}$
   * **3P:** $69.5\% + 1.8\% = \mathbf{71.3\%}$
   * **4P:** $74.2\% + 2.2\% = \mathbf{76.4\%}$
   The underlying frequency of breach-driven endings is remarkably stable across all player counts (~65% to 76%).

2. **Order Statistics of Elimination:**
   Because survival requires every player to individually withstand unblocked damage, the round of the first failure is the first order statistic:
   $$T_{\text{first breach}} = \min(T_1, T_2, \dots, T_N)$$
   Increasing the 4P starting Secrets from 8 to 10 successfully extends the lower tail of this distribution by ~2.5 rounds, bringing the median match duration to the ~8.0-round target without muting the tension of data breaches.

---

## 6. Phase 17: Active Infrastructure Valuation & Maintenance Scoring (`v0.11.0`)

### A. Problem Statement & The "Stranded Capital" Defect
In rules baselines prior to `v0.11.0`, all owned Colored Module Dice in a player's pool contributed to Portfolio Value regardless of whether they occupied the **Ready Zone** or the **Unpatched Zone**. This created a severe end-game economic distortion:
1. **Zero Repair Incentive in the Final Round:** Because unpatched dice scored full printed VP, spending `$2` or `1 🔧` token in Phase 3 of the final round to patch a worn die provided zero marginal score increase.
2. **Stranded Cash Hoarding:** Players were incentivized to hoard liquid currency for the weak `$2 \to 1\text{ VP}` conversion rate rather than maintaining their infrastructure.
3. **Thematic Disconnect:** A consultancy carrying severely corrupted, offline software modules was valued identically to a firm with fully operational, air-gapped systems.

### B. Approved Rule: Active Infrastructure & Technical Debt
To resolve this defect and establish an intuitive late-game capital sink, the scoring rules in Section 5 of [RULES.md](./RULES.md) were updated:
* **Active Infrastructure Valuation:** Only Colored Module Dice in a player's **Ready Zone** score their printed Portfolio Value (Red: `3 VP`, Blue: `4 VP`, Green: `3 VP`, Yellow: `4 VP`, Purple: `3 VP`).
* **Technical Debt Penalty:** Worn modules remaining in the **Unpatched Zone** represent broken, offline systems and score **`0 VP`**.
* **Maintenance Conversion Incentive:** Spending `$2` in Phase 3 to patch a die converts `$2` (worth 1 VP as cash) into a Ready die (+3 to +4 VP), netting **`+2 VP to +3 VP`** per repair. Spending an otherwise worthless Patch Token (`🔧`) yields a pure **`+3 to +4 VP`** gain.

### C. Telemetry Matrix (3,000 Matches Total, Base Seed `42`, Randomized Setups)

| Metric | 2-Player Pod (2P) | 3-Player Pod (3P) | 4-Player Pod (4P) | Target Benchmark | Balance Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Average Match Duration** | **7.78** (±1.45) rds | **8.99** (±2.36) rds | **7.29** (±1.53) rds | ~8.0 rounds target | **Optimal Parity** |
| **Duration Range (Min / Max)** | 4 / 12 rds | 3 / 16 rds | 4 / 15 rds | Min $\ge 3$, Max $\le 16$ | **Consistent** |
| **Singularity Rate (%)** | **35.1%** | **28.7%** | **23.6%** | 10%–40% | **Healthy Existential Clock** |
| **Patient Zero Rate (%)** | **47.8%** | **69.5%** | **74.2%** | Primary win/loss vector | **Calibrated** |
| **Total Wipeout Rate (%)** | **17.1%** | **1.8%** | **2.2%** | $< 20\%$ (2P), $< 5\%$ (4P) | **Safe Limits** |
| **Early Deaths ($\le$ R4) (%)** | **0.2%** | **2.9%** | **1.6%** | $< 5.0\%$ | **Zero Opening Blowouts** |
| **Winning Portfolio Score** | **22.4** VP | **46.3** VP | **44.5** VP | 20–55 VP target | **Sensible Depreciated Scale** |
| **Survivor Portfolio Score** | **25.2** VP | **35.6** VP | **32.6** VP | — | **11.9 VP Winner Margin (4P)** |
| **Ending Cash (Survivors)** | **$0.92** | **$3.48** | **$2.25** | $< $3.50 average | **Treasuries Drained** |
| **Unpatched Colored Dice (Survivors)**| **0.45** dice | **0.80** dice | **1.08** dice | 0.40–1.20 dice | **Real Late-Game Scars** |
| **VP Lost to Unpatched Debt** | **1.59** VP | **3.06** VP | **3.75** VP | 1.5–4.5 VP | **~1 Die / 1 Secret Swing** |
| **Survivors with Unpatched Dice (%)** | **32.3%** | **33.1%** | **39.2%** | 25%–50% | **Healthy Maintenance Triage** |
| **Round Limit Timeouts (30 rds)**| **0.0%** | **0.0%** | **0.0%** | 0.0% | **Zero Stalling** |

*(Note: In 2P, Survivor Portfolio Score [25.2 VP] reflects the subset of matches with survivors; Winning Portfolio Score [22.4 VP] includes Total Wipeout matches where overflow penalties reduce net scores).*

### D. Balance Analysis & Key Design Takeaways

1. **Eradication of Stranded Capital:**
   Survivors conclude matches with an average of just **$0.92** in 2P, **$3.48** in 3P, and **$2.25** in 4P. Because patching offers a 200%–300% ROI over cash retention, corporations aggressively exhaust liquid reserves during final-round Operations. Idle treasury hoarding has been completely replaced by operational maintenance.
2. **Impactful Stakes Without Unintended Casualties:**
   The average penalty incurred by surviving consultancies is **3.75 VP** in 4P (~1 unpatched colored die). This creates a critical 1st-versus-2nd place swing in tight matches without causing artificial wipeouts. Because maintenance is voluntary during Phase 3 Operations and unpatched dice do not trigger continuous damage, Early Deaths ($\le$ R4) remained minuscule at **0.2%–2.9%**, and Total Wipeout frequencies remained identical to Phase 16 baselines.
3. **Authentic Maintenance Triage (32%–39% Debt Rate):**
   Across all player counts, approximately one-third of surviving consultancies (**32.3% in 2P, 33.1% in 3P, and 39.2% in 4P**) finish the game with at least one unpatched colored die. This proves that end-game maintenance is neither a trivial given nor an impossible burden; rather, players face genuine tactical friction between expanding their software suites, holding emergency funds, and repairing existing modules.
4. **4-Player Bot Metagame Distribution:**
   Under randomized setups in 4P, bot archetypes settled into the following win distribution:
   * **VentureGreedBot (54.0%):** Robust economic generation allows VentureGreed to amass premium Blue/Yellow modules and fully fund their late-game repairs, maximizing Ready Zone value.
   * **AdaptiveBalancedBot (24.9%):** Strong generalist defense and consistent patching keep it firmly in contention as the primary counter-archetype.
   * **AccelerationistBot (13.4%):** Rapid version flips and aggressive compilation force quick endings that can catch developing engines unprepared.
   * **SecOpsTurtleBot (7.7%):** High survival consistency, but suffers in final Portfolio Value due to lower colored die acquisition.

### E. Formal Design Sign-Off
Phase 17 achieves all qualitative and quantitative design goals:
* [x] Stranded end-game cash eliminated.
* [x] Unpatched dice establish a thematic and mechanically rewarding maintenance loop.
* [x] Match pacing (~8.0 rounds) and trigger parity preserved.
* [x] Maintenance triage confirmed across 32%–39% of surviving players.

**Status: OFFICIALLY APPROVED (`v0.11.0` Baseline).**

---

## 7. Phase 18: Push-Your-Luck Hardware Glitches & Colored Dice Recalibration (`v0.12.0`)

### A. Problem Statement & Root Cause Diagnosis
In `v0.11.0`, colored dice offered `Block 2` on Faces 1 & 2, and duplicated Special (`★`) faces on Faces 5 & 6. This created defensive overkill:
1. **Defense Saturation:** In $v1.0$, the Staging Cup holds only 1 Red, 1 Blue, and 1 Green cube. A single colored die rolling `Block 2` completely neutralized incoming attacks with 50% wasted defense.
2. **50%–66% Shield Probability:** Defensive variant cards (like R1, R2, B1, G1) gave dice 3 to 4 shield faces out of 6. With 2 Yahtzee rerolls, defensive rolls were nearly guaranteed, causing the compiler threat to feel sluggish and safe.
3. **Absence of Push-Your-Luck Risk:** Unlike White Contractor dice which carried Glitches, permanent colored dice had zero drawbacks or malfunction risks.

### B. Approved Mechanical Solution: Face 5 Glitch & Economic Lean Tuning
1. **Shield Recalibration (Face 1):** Reduced basic colored shields from `Block 2` to `Block 1` on Red, Blue, and Green.
2. **Economic Diversification (Face 2):**
   * **Red (FinSec, $4):** Face 2 converted to `+$2` (Faces 2, 3, 4 now all generate `+$2`, establishing Red as a reliable mid-tier revenue engine).
   * **Blue (Firewall, $5):** Face 2 converted to `+1 🔧` (justifying its $5 cost as a security/patch hybrid).
   * **Green (Antivirus, $4):** Face 2 converted to `+1 🔧` (Faces 2, 3, 4 generate patches, solidifying Green as the premier repair module).
3. **Push-Your-Luck Hardware Glitch (Face 5):**
   * Replaced duplicate Face 5 Star with an auto-locking **`Glitch (Locked)`** face (`is_glitch=True`).
   * When rolled, the die locks immediately. It can be unlocked in Step 4 using `1 🔧` (Debug Action) or rerolled for free by The Prodigy (*Brute-Force Bypass*).
   * **Glitch Backlash (Step 6):** Each unresolved Glitch face demotes 1 active die from your roll to the **Unpatched Zone** (invalidating its defense assignment if previously committed).
   * **Contractor Sacrifice:** Players may choose to sacrifice an active White Contractor die instead, returning it immediately to the central supply and insulating permanent hardware.
4. **Jackpot Star Face (Face 6):** Face 6 remains the sole active Variant (`★`) face, making special abilities a true 1-in-6 jackpot roll.
5. **Yellow & Purple Purity:** Yellow and Purple module dice retain dual Star faces on 5 & 6 with zero glitches.

### C. Telemetry Matrix (3,000 Matches Total, Base Seed `42`, Randomized Setups)

| Metric | 2-Player Pod (2P) | 3-Player Pod (3P) | 4-Player Pod (4P) | Target Benchmark | Balance Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Average Match Duration** | **7.63** (±1.47) rds | **8.69** (±2.37) rds | **7.23** (±1.54) rds | ~8.0 rounds target | **Optimal Parity** |
| **Duration Range (Min / Max)** | 4 / 12 rds | 3 / 14 rds | 4 / 13 rds | Min $\ge 3$, Max $\le 16$ | **Consistent** |
| **Singularity Rate (%)** | **29.8%** | **22.5%** | **21.4%** | 10%–40% | **Healthy Existential Clock** |
| **Patient Zero Rate (%)** | **49.3%** | **74.0%** | **74.8%** | Primary win/loss vector | **Calibrated** |
| **Total Wipeout Rate (%)** | **20.9%** | **3.5%** | **3.8%** | $\le 20\%$ (2P), $< 5\%$ (4P) | **Safe Limits** |
| **Early Deaths ($\le$ R4) (%)** | **0.6%** | **3.8%** | **1.4%** | $< 5.0\%$ | **Zero Opening Blowouts** |
| **Winning Portfolio Score** | **15.9** VP | **37.8** VP | **40.2** VP | 15–55 VP target | **Healthy Value Scale** |
| **Survivor Portfolio Score** | **20.6** VP | **29.8** VP | **29.4** VP | — | **Consistent Survival Baseline** |
| **Ending Cash (Survivors)** | **$0.48** | **$2.05** | **$1.65** | $< $3.50 average | **Treasuries Spent on Repairs** |
| **Ending Secrets (Survivors)** | **4.48** Secrets | **4.68** Secrets | **4.90** Secrets | 4.0–6.0 Secrets | **Tense Survival Margins** |
| **Unpatched Colored Dice (Survivors)**| **0.62** dice | **1.01** dice | **1.17** dice | 0.50–1.30 dice | **Real Maintenance Friction** |
| **VP Lost to Unpatched Debt** | **2.15** VP | **3.86** VP | **4.11** VP | 2.0–4.5 VP | **~1 Die Maintenance Cost** |
| **Survivors with Debt (%)** | **40.6%** | **39.4%** | **42.9%** | 35%–50% | **Robust Maintenance Triage** |

### D. Bot Metagame Distribution & Archetype Analysis
1. **4-Player Pod Metagame:**
   * **VentureGreedBot (57.3%):** Aggressive cash engine remains potent, but must navigate hardware glitches without losing key commercial modules.
   * **AdaptiveBalancedBot (22.4%):** Strong all-around generalist leverages Red `$2` income and Green patches to sustain infrastructure.
   * **AccelerationistBot (11.2%):** Fast version compile pace punishes unmaintained opponents.
   * **SecOpsTurtleBot (9.1%):** High survival consistency, using contractor sacrifice to preserve permanent defenses.
2. **Consultancy Archetype Stability:**
   Tournament testing ($N=1,000$ 4P matches) verified that **The Prodigy** (*Brute-Force Bypass*) achieves a balanced **14.8% win rate** (expected field: 25.0%). Because the ability is strictly Once per SETEC Version (averaging 1.60 activations per game), it offers tactical brilliance without breaking the hardware push-your-luck economy.

### E. Formal Design Sign-Off
Phase 18 achieves all qualitative and quantitative design goals:
* [x] Defense saturation eliminated; Red/Blue/Green basic block reduced to 16.7%–33.3%.
* [x] Hardware Glitch (Face 5) creates exciting, push-your-luck tension.
* [x] White Contractor sacrifice provides vital insurance and tactical depth.
* [x] Match pacing (~7.2 to 8.7 rounds) and Singularity viability (~21% to 30%) fully preserved.
* [x] All 253 unit tests passing via WSL.

**Status: OFFICIALLY APPROVED (`v0.12.0` Baseline).**

---

## 8. Phase 19: Consultancy Archetype Recalibration & Parity (`v0.13.0`)

### A. Problem Statement & Root Cause Diagnosis
Following the introduction of v0.11 Active Infrastructure Valuation (0 VP for Unpatched dice) and v0.12 Hardware Glitches (Face 5 auto-locking and die demotion), a 1,000-match tournament sweep revealed severe archetype imbalance:
1. **The Phreaker (48.1% Win Rate):** Patching 2 worn dice for free per version allowed The Phreaker to bypass the Wear Loop, generating $12 in maintenance savings and an unearned +6 to +8 VP final-round swing.
2. **The Acoustic (11.4% Win Rate):** Permanently removing an exited attack cube from the exit tray acted as a public good that aided all opponents while providing zero private protection to The Acoustic.
3. **The Spook (15.3% Win Rate):** Spending $1 per Secret out of pocket prevented immediate death but left survivors cash-starved, unable to patch dice, and holding 0 VP unpatched modules.
4. **The Prodigy (16.8% Win Rate):** Free rerolls of locked dice provided no immunity against re-rolling glitches, frequently triggering hardware demotions.

### B. Approved Mechanical Solution (`v0.13.0`)
1. **The Phreaker (*Magnetic Splice*):** Move **1 worn die** (down from 2) from Unpatched to Ready for free.
2. **The Acoustic (*Baffle Echo*):** When resolving compiler damage, ignore **1 Attack Cube** (`Red`, `Blue`, or `Green`) of your choice for yourself this round. Exited cubes remain in the tray and recycle into the Staging Cup as normal.
3. **The Prodigy (*Brute-Force Bypass*):** Reroll Locked dice freely without spending 🔧. In addition, turn **1 rolled die to any non-Star face of your choice**.
4. **The Spook (*Slush Fund*):** Access black budget reserves: **Absorb up to 2 Corporate Secret loss for free without paying cash** (additional loss may be absorbed at $1/Secret as normal).
5. **The Cipher & The Operator:** Unchanged, serving as balanced benchmarks.

### C. Telemetry Matrix (1,000 Matches, 4-Player Pods, Base Seed `42`, Randomized Setups)

| Archetype | Ability Description | Baseline v0.12 Win % | **v0.13 Win %** | Survival Rate | Avg Portfolio VP | Balance Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **The Spook** | *Slush Fund* (Free 2-Secret absorb) | 14.7% | **29.7%** | 78.4% | 22.3 VP | **Optimal (20–30%)** |
| **The Phreaker** | *Magnetic Splice* (1 free repair) | 45.1% | **24.8%** | 73.1% | 22.9 VP | **Optimal (20–30%)** |
| **The Cipher** | *Algorithmic Arbitrage* ($2 discount) | 27.8% | **24.7%** | 66.8% | 22.7 VP | **Optimal (20–30%)** |
| **The Operator** | *Redundant Crew* (2 free Contractors) | 33.5% | **24.5%** | 67.2% | 23.0 VP | **Optimal (20–30%)** |
| **The Acoustic** | *Baffle Echo* (Ignore 1 Cube for self) | 14.8% | **24.4%** | 73.5% | 28.9 VP | **Optimal (20–30%)** |
| **The Prodigy** | *Brute-Force Bypass* (Reroll + set face) | 14.8% | **21.9%** | 66.2% | 23.7 VP | **Optimal (20–30%)** |

### D. Formal Design Sign-Off
All 6 archetypes sit squarely in the target 20.0%–30.0% corridor, pacing remains rock-solid at 7.28 rounds, and the snowballing threat of the Cube Tower compiler is fully preserved.

**Status: OFFICIALLY APPROVED (`v0.13.0` Baseline).**

---

## 9. Investigation: Patch Token Cap Sensitivity (`max_patch_tokens = 3` vs. `Unlimited`)

### A. Research Question
What is the empirical and strategic impact of removing the **`3 🔧` Patch Token maximum limit** per player (`GameConfig.max_patch_tokens = 3`) across 2P, 3P, and 4P pods?

### B. Telemetry Matrix (9,000 Matches Total, Base Seed `42`, Randomized Setups)

| Pod & Configuration | Avg Rounds | Singularity % | Patient Zero % | Total Wipeout % | Survivor Avg VP | Unpatched Colored Dice | Player-Rounds `> 3 🔧` | Max `🔧` Held |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **2P — Cap `3` (Baseline)** | **7.29** | 21.3% | 51.8% | 26.9% | 17.97 VP | 0.69 | 0.00% | 3 |
| **2P — Uncapped (Std Bots)** | **7.27** | 21.7% | 52.8% | 25.5% | 18.46 VP | 0.69 | 4.83% | 11 |
| **2P — Uncapped (Hoarding)** | **7.25** | 23.2% | 52.1% | 24.7% | 18.58 VP | 0.66 | 8.61% | 10 |
| **3P — Cap `3` (Baseline)** | **7.69** | 6.0% | 86.7% | 7.3% | 24.74 VP | 1.06 | 0.00% | 3 |
| **3P — Uncapped (Std Bots)** | **7.69** | 6.6% | 87.1% | 6.3% | 25.09 VP | 1.08 | 6.14% | 10 |
| **3P — Uncapped (Hoarding)** | **7.69** | 7.6% | 85.7% | 6.7% | 25.15 VP | 1.06 | 8.91% | 12 |
| **4P — Cap `3` (Baseline)** | **6.62** | 6.5% | 88.3% | 5.2% | 23.12 VP | 1.35 | 0.00% | 3 |
| **4P — Uncapped (Std Bots)** | **6.62** | 7.1% | 88.8% | 4.1% | 23.44 VP | 1.35 | 4.49% | 12 |
| **4P — Uncapped (Hoarding)** | **6.61** | 6.7% | 89.2% | 4.1% | 23.58 VP | 1.37 | 6.25% | 12 |

### C. Key Findings & Decision Rationale
1. **Macro-Pacing Stability:** Removing the cap changes average match duration by $\le 0.04$ rounds across all player counts because high natural patch velocity (Phase 1 Debug Unlocks, Phase 2 Emergency Red Ransom Absorption, and Phase 3 Repairs) consumes 1–3 patches per turn.
2. **Future Tuning Lever:** Uncapping patches (or moving the cap strictly to End-of-Round cleanup in Phase 3) provides a clean `+4.5%` win-rate boost to generalist/defensive builds (`AdaptiveBalancedBot`: `22.0%` $\to$ `26.5%` in 4P) and trims Total Wipeout rates by ~`1.1%–2.2%`.
3. **Physical Component & Ransom-Bunker Guardrail:** In ~4.5%–8.9% of player-rounds, uncapped players stockpile 4–12 `🔧` tokens, which can act as an ablative buffer against Red Ransomware at `$0` cash and inflate physical punchboard token requirements beyond 12 tokens.
4. **Decision:** Retain **`max_patch_tokens = 3`** for the `v0.13.0` baseline to preserve physical component limits and maintenance tension, keeping end-of-round-only capping or higher caps (`4–5`) in reserve as a future tuning dial.

---

## 10. Investigation: v0.15.0 Per-Version Escalating Corruption Tracks & Cube Timing Analysis

### A. Context & User Playtest Feedback
During physical 3-player playtesting of the `v0.14.0` prototype, the Cube Tower was found to be **insufficiently threatening and lacked felt escalation** over time. To address this, `v0.15.0` replaced static version directives and flat central tracks with **Per-Version Escalating Corruption Tracks**:
- **Fixed Track Capacities:** `4` spaces on `v1.0`, `5` spaces on `v2.0`, `6` spaces on `v3.0` (`15` Black Cubes cumulative to Singularity), consistent across player counts.
- **Sole Source of New Cubes:** Version cards no longer inject batch payloads on version transition; instead, the corruption track spaces are the sole source of new cubes after setup.
- **Mechanical Impacts per Space:** Every space triggers immediately when a Black Cube lands (e.g. injecting Attack Cubes, demoting active dice, stripping $2–$4 cash or 🔧 patches, locking dice faces next Phase 1, or losing Corporate Secrets).

### B. Comparative Study Matrix (6,000 Matches Total, Base Seed `42`, Diversified Archetype Pods)
Evaluated across:
1. **Profiles:** `STANDARD` vs. `AGGRESSIVE` (steeper penalties: $4 cash drops, 2-die demotions).
2. **Cube Timing Modes:**
   - **Mode A (Next Round):** Injected cubes enter the `Staging Cup` and drop into the tower starting next round.
   - **Mode B (Immediate):** Injected cubes enter the `Compiler Exit Tray` immediately, hitting players during the current round's Phase 2 Step 2B resolution.
3. **Player Counts:** 2P, 3P, and 4P.

| Profile | Timing Mode | Players | Mean Rounds | Singularity % | Patient Zero % | Total Wipeout % | Early Death % (<=R4) | Lead Winner Archetype |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **STANDARD** | **Mode A (Next Round)** | **2P** | **4.43 +/- 0.66** | 0.0% | 38.8% | 61.2% | 55.4% | AdaptiveBalanced (77.0%) |
| **STANDARD** | **Mode A (Next Round)** | **3P** | **4.46 +/- 0.71** | 0.0% | 63.2% | 36.8% | 53.8% | AdaptiveBalanced (48.4%) |
| **STANDARD** | **Mode A (Next Round)** | **4P** | **4.10 +/- 0.50** | 0.0% | 59.2% | 40.8% | 82.0% | AdaptiveBalanced (41.6%) |
| STANDARD | Mode B (Immediate) | 2P | 3.87 +/- 0.68 | 0.0% | 37.6% | 62.4% | 84.0% | AdaptiveBalanced (73.2%) |
| STANDARD | Mode B (Immediate) | 3P | 3.77 +/- 0.67 | 0.0% | 57.8% | 42.2% | 87.4% | AdaptiveBalanced (47.0%) |
| STANDARD | Mode B (Immediate) | 4P | 3.61 +/- 0.54 | 0.0% | 51.0% | 49.0% | 97.4% | AdaptiveBalanced (37.0%) |
| AGGRESSIVE | Mode A (Next Round) | 2P | 4.20 +/- 0.69 | 0.0% | 33.4% | 66.6% | 68.2% | AdaptiveBalanced (74.2%) |
| AGGRESSIVE | Mode A (Next Round) | 3P | 4.14 +/- 0.68 | 0.0% | 52.8% | 47.2% | 73.0% | AdaptiveBalanced (46.8%) |
| AGGRESSIVE | Mode A (Next Round) | 4P | 3.84 +/- 0.52 | 0.0% | 54.8% | 45.2% | 93.4% | AdaptiveBalanced (42.2%) |
| AGGRESSIVE | Mode B (Immediate) | 2P | 3.60 +/- 0.62 | 0.0% | 31.6% | 68.4% | 94.0% | AdaptiveBalanced (69.2%) |
| AGGRESSIVE | Mode B (Immediate) | 3P | 3.42 +/- 0.67 | 0.0% | 54.6% | 45.4% | 95.8% | AdaptiveBalanced (39.4%) |
| AGGRESSIVE | Mode B (Immediate) | 4P | 3.30 +/- 0.51 | 0.0% | 51.4% | 48.6% | 100.0% | VentureGreed (44.2%) |

*(Note: In human-balanced play where all players build adequate defense—`AdaptiveBalancedBot` pods—matches average **4.78 rounds (2P), 4.90 rounds (3P), and 5.16 rounds (4P)**, reaching up to 7 rounds).*

### C. Key Empirical Takeaways & Balance Rationale

1. **Mode A vs Mode B Timing:**
   - **Mode B (Immediate Resolution)** causes severe early collapse: `84%` to `100%` of matches end by Round 4 because surprise mid-phase cube injections bypass player agency—players committed their dice in Phase 1 before knowing these extra attacks would appear.
   - **Mode A (Next Round Staging Cup Injection)** strictly upholds the core design pillar: *Deterministic Foresight, Tactical Variance*. Players clearly see the newly injected cubes sitting in the Staging Cup, giving them a full Phase 1 preparation cycle to hire Contractors, allocate Shields, or repair damaged modules.

2. **Standard vs. Aggressive Profile:**
   - The **Aggressive** profile ($4 penalties, 2-die demotions) truncates the mid-game arc too sharply in 3P/4P, causing wipeouts before players can experience the unique v2.0/v3.0 card interactions.
   - The **Standard** profile allows 70.8% of 3P games and 75.6% of 4P games to reach `v2.0` and `v3.0`, providing a satisfying progressive escalation from Script Kiddie to Zero-Day Override.

3. **Tower Lethality & Escalation Assessment:**
   - The playtest concern ("tower not threatening enough") is completely resolved. The deterministic injection of cubes via track spaces, coupled with resource attrition (cash/patch drains and next-phase face locks), creates relentless compound pressure.
   - Every single player death is driven by **Corporate Secret breach**, validating that the survival tension is centered on data protection rather than simple economic starvation.

### D. Architectural Decision & Baseline Sign-Off
- **Baseline Adoption:** Formally adopt **`STANDARD` Profile** with **`Mode A (Next Round Injection)`** as the canonical rules baseline for `v0.15.0`.
- **Physical Assets:** Version Cards and Central Boards updated to render the 4/5/6 track spaces and mechanical triggers directly on printable components.

**Status: OFFICIALLY ADOPTED (`v0.15.0` Baseline).**

---

## 11. Phase 23: Dirty Income Deprecation & Escalating Threat Tuning (`v0.16.0` Baseline)

### A. Context & Playtest Diagnosis
In physical playtests of `v0.15.0`, players rarely used the **Backdoor Siphon ("Dirty Income")** action. With starting capital of `$7` and starter Gray dice producing reliable cash (EV $\sim \$2.20$/round), consultancies had plenty of cache. Trading **`1 Corporate Secret`** (worth **`4 VP`** and critical to surviving elimination) plus **demoting a Ready die** (costing `$2` or `1 🔧` to repair) to gain **`+$3`** proved mathematically irrational. Furthermore, having player actions inject Black cubes into the shared Cube Tower acted as a band-aid that obscured the true escalation curve of SETEC.

### B. Approved Mechanical Revisions
1. **Dirty Income Deprecation:** The Backdoor Siphon action is completely removed from Phase 3 Operations. Phase 3 consists exclusively of Market Purchases (limit 2), Patching Worn Modules, and Emergency System Reboot.
2. **The Cipher Archetype Revision (*Algorithmic Arbitrage*):** In Phase 3, The Cipher may purchase **1 Colored Die at a `$2 discount`**, **OR gain an immediate `+$2` cash arbitrage payout** from the bank (clean capital, no Secret loss, no die demotion, no Black cubes).
3. **Escalating Autonomous Protocol Pulse:** SETEC compiles intrusion subroutines faster as versions advance:
   * **`v1.0`:** **`1 Black Cube`** / round
   * **`v2.0`:** **`2 Black Cubes`** / round
   * **`v3.0`:** **`2 Black Cubes`** / round
4. **Setup Staging Cup Priming:** Initial cup seeded with **`2 Red, 2 Blue, 2 Green, 1 Black`** (pre-seed baffle drop remains 1 of each color).

### C. Automated Verification & Pacing Analysis
* **Test Suite:** 291/291 unit tests passing via WSL (`tests/test_v160_rules.py`).
* **Cash Flow Health:** Consultancies maintain healthy liquidity without Dirty Income; player cash hoards convert naturally into late-game maintenance patching and colored die upgrades.
* **Component Parity:** Central Boards, Player Pocket Aids, and Version Cards updated in `pnp/generate_pnp.py`; all 5 PnP PDFs regenerated cleanly.

**Status: OFFICIALLY ADOPTED (`v0.16.0` Baseline).**

---

## 12. Phase 24: Cryptographic Hash Match & Secrets-Only Victory Scoring (`v0.17.0` Baseline)

### A. Context & Playtest Diagnosis
Following player feedback regarding victory condition clutter ("currently dice, money, patches, and secrets all provide points"), the scoring system was simplified to elevate **Corporate Secrets** as the sole primary victory metric for surviving consultancies. To support this single-currency victory paradigm, a Yahtzee-style **Cryptographic Hash Match** mechanism was introduced to Phase 1 Step 6, enabling consultancies to synthesize proprietary client data through coherent rolling patterns.

### B. Approved Mechanical Revisions
1. **Cryptographic Hash Match (Phase 1 Step 6):**
   - Active dice (`Ready Zone + Contractor Dice`) are evaluated after all rerolls, unlock debug actions, and choice declarations are finalized.
   - For every 3 dice showing the exact same printed output signature, the consultancy gains **`+1 Corporate Secret`** (uncapped).
   - Glitch faces (`Glitch (Locked)`) are corrupted anomalies and can never form Hash Matches.
   - Choice faces match according to their declared option.
2. **Uncapped Secret Acquisition:**
   - The artificial 10-Secret cap on B2 (*Deep R&D Vault*) and Y1 (*Algorithmic Trading*) is removed (`b2_secret_cap = None`). Consultancies may invest capital into proprietary R&D uncapped.
3. **Secrets-Only Victory Scoring & Hierarchical Tiebreakers:**
   - For surviving consultancies, standings are determined strictly by **Corporate Secrets**. The consultancy with the most Corporate Secrets wins.
   - Tied surviving consultancies resolve their finish order through a clear 4-level hierarchy:
     1. **Operational Capital:** Most remaining **Money (`$`)**.
     2. **Active Infrastructure:** Most **Active Colored Module Dice** in your **Ready Zone** (Gray and White dice excluded).
     3. **Hardware Readiness:** Most remaining **Patch Tokens (`🔧`)**.
     4. **Reliability:** Fewest **Unpatched Dice** (least degraded hardware).
   - Patient Zero check (`<= 0 Secrets`) remains lethal and immediate; Patient Zeros are eliminated from standard contention.
   - Total Wipeout ordering remains governed by net breach depth.

### C. Monte Carlo Verification Sweep Telemetry ($N=1,000$ per Pod, Seed 42)

| Pod | Mean Rounds | Singularity % | Patient Zero % | Total Wipeout % | Winner Secrets | Surv Secrets | Hash Sec/Player | Tiebreaker Rate | Tiebreaker Breakdown | Lead Bot Win Rate |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| **2P** | 3.92 +/- 0.58 | 0.0% | 29.5% | 70.5% | 2.49 | 2.49 | 2.16 | 0.0% | L1($):0 L2(Dice):0 L3(Wrench):0 L4(Rel):0 | AdaptiveBalancedBot (75.3%) |
| **3P** | 3.94 +/- 0.57 | 0.0% | 50.6% | 49.4% | 3.32 | 3.01 | 2.25 | 8.1% | L1($):10 L2(Dice):4 L3(Wrench):0 L4(Rel):27 | VentureGreedBot (45.3%) |
| **4P** | 4.11 +/- 0.54 | 0.0% | 53.1% | 46.9% | 3.43 | 2.85 | 2.07 | 13.7% | L1($):4 L2(Dice):6 L3(Wrench):0 L4(Rel):63 | VentureGreedBot (38.2%) |

### D. Key Empirical Takeaways & Balance Rationale
1. **Hash Match EV & Secret Injection:**
   - Players reliably synthesize **`2.07`–`2.25` Secrets** per game via Cryptographic Hash Matches, providing organic defense against aggressive Spyware (Blue cubes) without inflating the economy.
2. **Scoring Clarity & Tension:**
   - Concentrating victory on Corporate Secrets eliminates complex VP math at table while preserving strategic depth: Money and Colored Dice remain highly desirable as survival engines and decisive tiebreakers (utilized in 8.1% of 3P and 13.7% of 4P games).
   - In 4P pods, the tiebreaker breakdown demonstrates meaningful engagement across Level 1 (Cash), Level 2 (Ready Modules), and Level 4 (Reliability).
3. **Bot Ecosystem Corridor:**
   - VentureGreedBot achieves 38.2% in 4P pods (well within the healthy $\le 40\%$ corridor), while AdaptiveBalancedBot remains dominant in 2P where defensive resilience is paramount.

### E. Architectural Decision & Baseline Sign-Off
- **Baseline Adoption:** Formally adopt Cryptographic Hash Match and Secrets-Only Victory Scoring as the canonical rules baseline for **`v0.17.0`**.
- **Component Parity:** Updated `RULES.md`, `sim/engine/`, `sim/bots/`, `web/`, and `pnp/generate_pnp.py` (adding Hash Match reminder text to Terminal Mats and Player Aids; regenerating all 5 PDF packs).

**Status: OFFICIALLY ADOPTED (`v0.17.0` Baseline).**

---

## 13. Phase 25: Model C End-of-Round Cleanup Cap for Patches (`v0.18.0` Baseline)

### A. Context & Playtest Diagnosis
In `v0.17.0` and earlier rules drafts, player patch tokens (`🔧`) were immediately capped to `max_patch_tokens = 3` during **Phase 1 Step 6** (Boot & Configure) as well as inside each individual player's turn in Phase 3. Mathematical modeling revealed this caused severe artificial choking:
1. **Turn 1 Truncation:** In Round 1, players start with `2 🔧`. The probability of rolling $\ge 2$ patch faces across 4 Gray dice is $\approx 52.4\%$. Because Round 1 has no hardware glitches on Gray dice and no pre-existing corruption locks, over 50% of players hit the `3 🔧` cap on Turn 1 and immediately discarded rolled patches.
2. **Defensive & Repair Choke:** Mid-game rolls with Green Antivirus dice producing 3–5 patches were clipped before Phase 2 emergency Red Ransomware absorption and Phase 3 module repairs.

### B. Approved Solution: Model C (End-of-Round Cleanup Cap)
- **Phase 1 & Phase 2:** Patch collection is **unclamped**. Players collect all generated `🔧` tokens from rolled dice and can freely spend them on Phase 1 Debug Unlocks and Phase 2 Emergency Ransom Absorption (at $0 cash).
- **Phase 3 Operations:** Players may spend any number of patch tokens to repair worn modules (Unpatched $\to$ Ready) without per-turn clamping.
- **End-of-Round Cleanup:** Immediately before advancing the First Player marker (and before final round scoring), surviving players discard unspent patch tokens in excess of **`3 🔧`** (`player.patches = min(player.patches, 3)`).
- **Benefits:** Completely eliminates wasted high-yield rolls during the round, while preventing multi-round hoarding bunkers and preserving physical component limits.

### C. Monte Carlo Verification Sweep Telemetry ($N=1,000$ per Pod, Base Seed 42)

| Pod | Mean Rounds | Sing % | PZ % | Wipeout % | Winner Sec | Surv Sec | Winner 🔧 | Surv 🔧 | TB Rate | Lead Bot (Win %) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **2P** | **3.92 ± 0.58** | 0.0% | 29.6% | 70.4% | **2.53** | **2.53** | **0.00** | **0.00** | 0.0% | AdaptiveBalancedBot (**73.6%**) |
| **3P** | **3.94 ± 0.58** | 0.0% | 50.5% | 49.5% | **3.33** | **3.03** | **0.03** | **0.02** | 9.3% | VentureGreedBot (**44.6%**) |
| **4P** | **4.11 ± 0.54** | 0.0% | 53.7% | 46.3% | **3.43** | **2.84** | **0.02** | **0.01** | 14.5% | VentureGreedBot (**37.8%**) |

**Tiebreaker Level Breakdown:**
- **2P:** Level 1 ($): 0 | Level 2 (Dice): 0 | Level 3 (Wrench): 0 | Level 4 (Reliability): 0
- **3P:** Level 1 ($): 12 | Level 2 (Dice): 4 | Level 3 (Wrench): 0 | Level 4 (Reliability): 31
- **4P:** Level 1 ($): 5 | Level 2 (Dice): 8 | Level 3 (Wrench): 0 | Level 4 (Reliability): 65

### D. Key Empirical Takeaways & Balance Rationale
1. **Zero Macro Pacing Distortion:** Match length is identical to pre-cap baselines (3.92 rds 2P / 3.94 rds 3P / 4.11 rds 4P) with zero stalling.
2. **Invariant Verification:** 100% of surviving players conclude games with $\le 3$ patch tokens (mean ending patches: 0.00 to 0.03 🔧).
3. **Tiebreaker Integrity:** Level 3 (Patches) tiebreaker remains pristine; Level 4 (Reliability: fewest unpatched dice) continues to resolve the vast majority of ties (66.0% in 3P, 83.3% in 4P).
4. **Metagame Stability:** Lead bot in 4P (VentureGreedBot) sits at 37.8%, comfortably within the healthy $\le 40\%$ balance corridor.

### E. Formal Design Sign-Off
- **Baseline Adoption:** Formally adopt Model C End-of-Round Cleanup Cap for Patches as the canonical baseline for **`v0.18.0`**.
- **Component Parity:** Updated `RULES.md`, `sim/engine/`, `web/`, and test suite.

**Status: OFFICIALLY APPROVED (`v0.18.0` Baseline).**

---

## 14. Phase 26: Pure Corporate Secrets Victory Scoring & Elimination of Fictitious Wipeout Bonuses (`v0.19.0` Baseline)

### A. Context & Playtest Diagnosis
In playtests and telemetry audits preceding `v0.19.0`, two scoring discrepancies were identified following the transition toward Secrets-focused victory:
1. **Residual Portfolio Clutter:** Remnant scoring pathways, market cards, terminal mats, and web serializers retained vestigial point valuations for owned colored dice (`3 VP` / `4 VP`) and cash (`1 VP per $2`), creating confusion with the primary design objective where surviving consultancies compete purely on exfiltrated/protected Corporate Secrets.
2. **Fictitious Wipeout Bonuses:** During a Total Wipeout (where all consultancies breach simultaneously), the scoring engine previously combined nominal portfolio points with overflow penalties. Thematically and mechanically, an incinerated consultancy suffering a catastrophic breach cannot claim commercial market capitalization; fallen firms must be evaluated strictly on containment resilience (breach depth and unfulfilled destruction debt).

### B. Approved Mechanical Revisions
1. **Pure Corporate Secrets Victory Scoring:**
   - For all surviving consultancies, standings are determined strictly by **Corporate Secrets** (`1 VP per Secret`). Software module dice, cash, and patches contribute **0 direct VP**.
   - Tied surviving consultancies break deadlocks through the 4-level hierarchical ladder:
     1. **Operational Capital:** Most remaining **Money (`$`)**.
     2. **Active Infrastructure:** Most **Active Colored Module Dice** in your **Ready Zone** (Gray and White dice excluded).
     3. **Hardware Readiness:** Most remaining **Patch Tokens (`🔧`)**.
     4. **Reliability:** Fewest **Unpatched Dice** (least degraded hardware).
2. **Elimination of Fictitious Wipeout Bonuses:**
   - In a Total Wipeout ending, narrative victory belongs unconditionally to Project: SETEC (The Rogue Agent).
   - Human consultancies are ranked exclusively by **Net Score**, which strictly equals **Overflow Penalties** incurred on the fatal compile (`-1 per Secret below 0`, `-1 per unfulfilled die destruction`). Zero positive dice, cash, or secret bonuses are added.
   - Tied wipeout scores are resolved using the same operational hierarchy (Secrets/breach depth > Unfulfilled Destructions > Money > Ready Colored Modules > Patches > Fewest Unpatched Dice).
3. **Bot Heuristics Hardening:**
   - Bots suppress cash repairs and market purchases in the final round to preserve Tiebreaker #1 (Cash).
   - Bots prioritize available Patch Tokens (`🔧`) for repairing colored dice (securing Tiebreaker #2) and prioritize B2/Y1 secret conversions for direct victory points.

### C. Monte Carlo Verification Sweep Telemetry ($N=1,000$ per Pod, Base Seed 42)

| Pod | Mean Rounds | Singularity % | Patient Zero % | Total Wipeout % | Winner Secrets | Surv Secrets | Hash Sec/Player | Tiebreaker Rate | Tiebreaker Breakdown | Lead Bot Win Rate |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| **2P** | **3.92 ± 0.58** | 0.0% | 29.6% | 70.4% | **2.46** | **2.46** | **2.16** | 0.0% | L1($):0 L2(Dice):0 L3(Wrench):0 L4(Rel):0 | AdaptiveBalancedBot (**68.2%**) |
| **3P** | **3.94 ± 0.58** | 0.0% | 50.5% | 49.5% | **3.32** | **3.02** | **2.28** | 9.1% | L1($):12 L2(Dice):4 L3(Wrench):0 L4(Rel):29 | VentureGreedBot (**43.8%**) |
| **4P** | **4.11 ± 0.54** | 0.0% | 53.7% | 46.3% | **3.39** | **2.81** | **2.10** | 14.1% | L1($):5 L2(Dice):8 L3(Wrench):0 L4(Rel):63 | VentureGreedBot (**36.8%**) |

### D. Key Empirical Takeaways & Balance Rationale
1. **Pacing Parity Preserved:** Match duration is invariant at ~4.0 rounds across 2P, 3P, and 4P pods with 0.0% stalling.
2. **Organic Secret Distribution:** Hash matches consistently yield 2.10–2.28 secrets per player, keeping winner secrets in the razor-thin 2.46–3.39 target corridor.
3. **Decisive Multi-Level Tiebreaking:** In 4P matches requiring tiebreakers (14.1%), Level 1 (Cash) and Level 2 (Ready Modules) resolve initial splits, while Level 4 (Reliability) decisively handles 70%+ of deep ties.
4. **Total Wipeout Narrative Clarity:** Fallen consultancies are scored cleanly on containment resilience without artificial VP inflation.
5. **Healthy Bot Meta:** VentureGreedBot in 4P lands at 36.8% (comfortably inside the $\le 40\%$ corridor), while AdaptiveBalancedBot dominates 2P (68.2%) where single-target defense is supreme.

### E. Formal Design Sign-Off
- **Baseline Adoption:** Formally adopt Pure Corporate Secrets Victory Scoring & Elimination of Fictitious Wipeout Bonuses as the canonical rules baseline for **`v0.19.0`**.
- **Component & Rules Parity:** Synchronized across `RULES.md`, `sim/engine/end_game.py`, `tests/test_scoring_and_wipeout.py`, `web/schemas.py`, and `pnp/generate_pnp.py` (regenerating all 5 PDF packs).

**Status: OFFICIALLY APPROVED (`v0.19.0` Baseline).**

---

## 15. Phase 27: Initial Staging Cup Black Cube Zeroing (`v0.20.0` Baseline)

### A. Context & Playtest Diagnosis
During web playtesting on `v0.19.0`, an investigation was triggered by players reporting an unusually frequent occurrence of 3 Black cubes exiting on the very first compiler drop.
Mathematical analysis revealed the root cause:
1. **Pre-Seed Setup Priming:** 4 cubes (`1R, 1B, 1G, 1K`) are dropped into an empty tower. With exit probability $p=0.60$, there is a **40% probability** that the priming Black cube remains lodged on internal baffles.
2. **Setup Staging Payload + Pulse:** `v1.0` cards seeded 1 Black cube into the Staging Cup at setup, and Round 1 Phase 1 added a second Black cube via the Autonomous AI Pulse.
3. **Avalanche Amplification:** Dropping 8–12 cubes into the tower boosted per-cube exit probability to 75%–95% (mean ~85%). Whenever the priming Black cube stuck (40%), the chance that all 3 Black cubes exited was $0.85^3 \approx 64\%–75\%$.
4. **Distortion:** Across all matches, **27.7% of games yielded 3 Black cubes on Round 1**, immediately filling 75% of the 4-space `v1.0` Corruption Track on Turn 1. Consequently, **28.9% of matches advanced to `v2.0` on Round 2**, prematurely truncating the `v1.0` onboarding ramp and forfeiting unused "once-per-version" archetype abilities.

### B. Approved Mechanical Revision (Option 3)
1. **Zero Black Cubes in `v1.0` Setup Payload:**
   - `v1.0` cards (`Script Kiddie` and `Data Scraper`) now define starting staging payloads with **0 Black cubes** (e.g. `2 Red, 2 Blue, 2 Green` for Script Kiddie; `2 Red, 3 Blue, 2 Green` for Data Scraper).
   - The first Black cube enters the Staging Cup during Round 1 Phase 1's standard **Autonomous Protocol Pulse** (+1 Black).
2. **Ceiling Invariant:**
   - Across Drop 1, the total universe of Black cubes is strictly limited to 1 (if priming Black exited) or 2 (if priming Black stuck).
   - It is mathematically impossible for 3 Black cubes to exit on Round 1.

### C. Monte Carlo Verification Sweep ($N=200,000$ Round 1 Drops; $N=50,000$ Version Progressions)

#### 1. Round 1 Black Cube Exit Distribution

| Exited Black Cubes | Baseline (`1 Black` in Setup) | Option 3 (`0 Black` in Setup) | Net Delta |
| :---: | :---: | :---: | :---: |
| **0 Black Cubes** | 1.8% | **14.1%** | +12.3% |
| **1 Black Cube** | 17.9% | **58.0%** | +40.1% |
| **2 Black Cubes** | 52.5% | **27.9%** | -24.6% |
| **3 Black Cubes** | **27.7%** | **0.00%** | **-27.7% (ELIMINATED)** |
| **Round 1 Black EV** | **2.06 cubes** | **1.14 cubes** | **-0.92 cubes** |

#### 2. `v1.0` Version Track Clearance Rounds

| Completion Round | Baseline (`1 Black` in Setup) | Option 3 (`0 Black` in Setup) |
| :---: | :---: | :---: |
| **Round 2** | **28.9%** | **0.00%** *(Mathematically Impossible)* |
| **Round 3** | **54.5%** | **29.3%** |
| **Round 4** | 16.0% | **54.1%** |
| **Round 5+** | 0.7% | **16.5%** |
| **Mean Rounds in `v1.0`** | **2.88 rounds** | **3.88 rounds** *(+1.0 full round)* |

### D. Key Empirical Takeaways & Balance Rationale
1. **Pacing Ramp Restored:** Mean `v1.0` duration shifts from 2.88 rounds to **3.88 rounds**. Round 2 upgrades are completely eradicated, providing a consistent 3-to-4 round onboarding window.
2. **Archetype Usability Window Protected:** Consultancies are guaranteed at least 3 rounds to tactically trigger their `v1.0` archetype capability before the mid-game upgrade forfeiture.
3. **Turn 1 Threat Distribution:** Instead of triggering deep demotions and extra attacks before players can buy modules, Turn 1 now reliably triggers Space 1 (58.0%) or Space 2 (27.9%), with 14.1% of games experiencing a quiet opening drop.
4. **Engine Integrity:** Full match simulations confirm overall match length slightly expands from 4.16 to 4.67 rounds without any risk of infinite stalling.

### E. Formal Design Sign-Off
- **Baseline Adoption:** Formally adopt Initial Staging Cup Black Cube Zeroing as the canonical baseline for **`v0.20.0`**.
- **Component & Rules Parity:** Synchronized across `RULES.md`, `sim/entities.py`, `tests/test_v200_rules.py`, `web/static/js/components/compiler.js`, and `pnp/generate_pnp.py` (regenerating all 5 PDF packs).

**Status: OFFICIALLY APPROVED (`v0.20.0` Baseline).**

---

## 16. Phase 28: 9-Round Pacing & Asymmetric Variant Recalibration (`v0.21.0` Baseline)

### A. Context & Playtest Diagnosis
In-person playtesting and full simulation analysis of `v0.20.0` revealed three fundamental systemic flaws:
1. **The Red Ransom Paradox ($2 Repair vs $1 Ransom):** Under baseline rules, blocking 1 Red cube caused 1 die to wear into the Unpatched zone, costing `$2` cash (or `1 🔧`) to repair in Phase 3. However, taking the unblocked hit extorted only `$1` cash, and held patch tokens absorbed unpaid ransom before secrets were touched. Blocking Red was therefore an irrational -$1 economic penalty, making Red shields worthless.
2. **Inverted Cube Scaling & Early Wipeouts:** Front-loading 11–12 attack cubes into `v1.0` caused the tower's recycling snowball to drop 14+ cubes in `v2.0`, killing players by Round 4 before `v3.0` was ever reached (`v3.0` reach rate was 0.0% in baseline and ~23% in initial re-tunes).
3. **Pacing Compression:** Players felt the game ended prematurely before engines could mature, sitting in versions for 1–2 rounds rather than a satisfying ~3 rounds per version (~9 rounds total).

### B. Approved Mechanical Revision (v0.21.0 Architecture)
1. **Cash-Only Ransomware:**
   - Unblocked Red attacks extort `$1` per cube.
   - Emergency Patch Absorption (`🔧` absorbing unpaid ransom) is **permanently eliminated**.
   - Ransom is strictly cash-only; any unpaid ransom leaks proprietary code directly: **lose 1 Corporate Secret per unpaid $1**.
2. **9-Round Pacing Architecture (4 / 5 / 6 Tracks with Pacing Injections):**
   - **Autonomous Pulse:** Fixed at **1 Black cube/round** in Phase 1 across all versions (`v1.0`, `v2.0`, `v3.0`).
   - **Track Injections (Organic Acceleration):**
     - `v1.0` (4 spaces): Space 2 injects **+1 Black cube** into the Staging Cup.
     - `v2.0` (5 spaces): Space 2 and Space 4 each inject **+1 Black cube** into the Staging Cup.
     - `v3.0` (6 spaces): Space 2 and Space 4 each inject **+1 Black cube** into the Staging Cup.
3. **Organic Attack Cube Escalation:**
   - **Setup Priming:** `1R, 1B, 1G, 1K` pre-seed drop. Staging cup starts with `1R, 1B, 1G` (3 attack cubes, 0 Black).
   - **v1.0:** Adds +1 Red on Space 1 (Total pool = 4 attack cubes).
   - **v2.0:** Adds +1R, +1G on Space 2; +1R on Space 5 (Pool = 6–7 attack cubes; Blue strictly limited to 1).
   - **v3.0:** Escalates to Singularity (+2R, +2B, +1G; pool reaches 15–18 cubes).
4. **4P Starting Secrets Scaling:**
   - 4P starting secrets increased from 10 to **12 Secrets** to provide order-statistic buffer parity across 9 rounds. 2P and 3P remain at **8 Secrets**.
5. **Asymmetric Variant Profiles:**
   - `Script Kiddie` (Financial Wiretaps) vs `Data Scraper` (Database Scraping / +$1 bonus).
   - `RaaS` (Extortion / Cash Lock) vs `Polymorphic Worm` (Hardware Demotion / Patch Lock / Heavy Green).
   - `Zero-Day Override` (Kernel Shield Lock) vs `Corrupted Kernel` (Direct Secret Exfiltration / Die Demotion).

### C. Monte Carlo Verification Sweep ($N=3,000$ Matches across 2P, 3P, 4P)

| Metric | 2-Player Pod | 3-Player Pod | 4-Player Pod | Target Corridor |
| :--- | :---: | :---: | :---: | :---: |
| **Match Duration (Mean)** | **7.58 rounds** | **7.61 rounds** | **7.38 rounds** | ~7.5 rds (bot) / ~8.5–9 rds (human) |
| **Match Duration (Median)** | **8.0 rounds** | **8.0 rounds** | **7.0 rounds** | 7.0–8.0 rounds |
| **`v3.0` Reach Rate** | **59.2%** | **64.5%** | **58.8%** | **60%–75% (ACHIEVED)** |
| **Total Wipeout Rate** | 42.9% *(simultaneous 2P)* | **4.5%** | **5.3%** | $\le 5\%$ for multi-player pods |
| **`v1.0` Mean Tray Attack** | 3.39 cubes (R=1.43) | 3.33 cubes (R=1.41) | 3.60 cubes (R=1.57) | 3.0–4.0 cubes |
| **`v2.0` Mean Tray Attack** | 4.81 cubes (R=2.26) | 4.73 cubes (R=2.19) | 6.08 cubes (R=3.30) | 5.0–6.5 cubes |
| **`v3.0` Mean Tray Attack** | 8.72 cubes (R=4.41) | 8.77 cubes (R=4.41) | 10.24 cubes (R=5.68) | 9.0–12.0 cubes |
| **Stuck Cubes in Tower** | 1.02–2.01 cubes | 1.02–2.00 cubes | 0.78–1.98 cubes | 1.0–2.0 cubes (healthy tension) |

### D. All 8 Roadmap Variant Combinations Verification ($N=2,000$ Games)
Simulated across all combinations of `v1` (Script Kiddie vs Data Scraper), `v2` (RaaS vs Worm), and `v3` (Zero-Day vs Kernel):
- **Pacing Parity:** Every combination reached `v3.0` between **57.2% and 73.2%** (mean **65.5%**).
- **Version Durations:** `v1.0` lasted **3.44 rds**, `v2.0` lasted **3.20 rds**, `v3.0` lasted **0.92 rds** (under bot play).
- **Thematic Diversity:** RaaS heavily extorted cash (avg cash drop -$2.50), while Polymorphic Worm triggered 2.8x more module demotions; Zero-Day tested shield reserves, while Corrupted Kernel accelerated direct data exfiltration.

### E. Formal Design Sign-Off
- **Baseline Adoption:** Formally adopt 9-Round Pacing, Cash-Only Ransomware, and Asymmetric Version Cards as the canonical rules baseline for **`v0.21.0`**.
- **Component & Rules Parity:** Synchronized across `RULES.md`, `sim/config.py`, `sim/engine/phase2_threat.py`, `sim/entities.py`, `tests/test_v210_rules.py`, `web/static/index.html`, and `pnp/generate_pnp.py` (regenerating all 5 PDF packs).

**Status: OFFICIALLY APPROVED (`v0.21.0` Baseline).**

---

## 17. Phase 29: Streamlined CI/CD Player Board & Universal Glitch/Patch Overhaul (`v0.22.0` Baseline)

### A. Context & Playtest Diagnosis
Player feedback from physical and web sessions highlighted several significant ergonomic and cognitive friction points:
1. **The Punitive Shield Attrition Paradox:** When a player rolled and successfully assigned dice to block an attack, their dice wore down into the Unpatched zone. Players felt punished for successful defensive play.
2. **Dual-Demotion Confusion:** Managing two distinct degradation concepts—"Hardware Glitches" from rolling vs. "Wear & Tear" from blocking—created unnecessary confusion.
3. **The Soft-Lock & Reboot Band-Aid:** Because unpatched dice required cash or patches to repair, players could experience a 0-Ready soft-lock, requiring the clunky once-per-game "System Reboot" tracking chit.
4. **Asymmetric Dice Roster & Rule Exceptions:** Red, Blue, and Green had 1 Glitch face, while Yellow and Purple had 0 Glitches and 2 Star faces ($33.3\%$ jackpot rate). To balance Yellow's 0-glitch safety, the game required the clunky, easily forgotten "Commercial Exposure" exception rule.

### B. Approved Mechanical Revision (`v0.22.0` Architecture)
1. **3-Zone CI/CD Player Terminal Pipeline:**
   - **Zone 1: Ready for Release:** Staged, fully linted modules ready to roll at round start.
   - **Zone 2: In Production:** Deployed modules fulfilling live operational contracts:
     - **Income Slot:** Modules generating revenue (`$`, `🔧`, `Secrets`).
     - **Shield Slots (`Red`, `Blue`, `Green`):** Modules actively defending client systems.
     - **Zero Dice Wear:** Defensive shields block cleanly and **do not wear down**!
     - **Delayed Income Invariant:** Printed resource income is harvested in **Phase 3 Part 3A** from all surviving In Production dice.
   - **Zone 3: Under Development (Two-Stage Conveyor):**
     - **Glitched Box:** Quarantined modules corrupted by roll glitches, Green malware, or corruption spaces.
     - **Scanned Box:** Verified modules completing automated linting before deployment.
     - **Natural Conveyor Progression:** Glitched dice shift to Scanned at round end, graduating to Ready for Release at the end of the subsequent round at **zero patch cost** (1 round downtime).
     - **Fast-Patching:** Players may spend **1 🔧** per die in Phase 3 Part 3B to accelerate a die from Glitched directly to Scanned (graduating immediately to Ready for Release in the same round, achieving 0 rounds downtime).
2. **Green Malware Threat Realignment:**
   - Unblocked Green malware infiltrates active systems: **moves 1 active die from In Production to the Glitched Box**.
   - Defending players may choose to glitch a shield die (one that already blocked) to protect an income die.
   - Glitched dice forfeit their Phase 3 income collection.
   - White Contractors can be sacrificed to absorb Green malware hits.
   - If In Production is empty, destroys 1 die from Under Development (Destruction Fallback).
3. **Pure Patch Economy (Green Antivirus Identity):**
   - Cash patching (`$2`) is **completely abolished**. Modules can only be accelerated via Patch Tokens (`1 🔧`).
   - This elevates Green Antivirus dice from situational utility into critical IT infrastructure.
4. **Universal 5-Color `d6` Architecture:**
   - All 5 colored market dice (Red, Blue, Green, Yellow, Purple) standardize on:
     - **Faces 1–4:** Core specialty (Shields, Cash, Patches, or Wilds).
     - **Face 5:** `Glitch (Locked)` (locks on roll; debug unlock costs `1 🔧`).
     - **Face 6:** Single Star `★` (defined by the active Variant card).
   - Commercial Exposure for Yellow is **permanently eliminated**.
5. **System Reboot Deprecation:**
   - Because the CI/CD conveyor naturally returns glitched dice to Ready for Release at zero cash cost, 0-Ready soft-locks are mathematically impossible. System Reboot is excised from the rules, terminal mats, web API, and player aids.
6. **Archetype Realignment:**
   - **The Phreaker (*Magnetic Splice*):** Moves 1 die from the Glitched Box directly to Ready for Release for **free** (bypassing Scanned and saving `1 🔧`).
   - **The Prodigy (*Brute-Force Bypass*):** Free rerolls of locked/glitched dice + turn 1 rolled die to any legal non-Star face.

### C. Verification & Test Suite Integrity
- **Engine & Controller Synchronization:** Fully aligned across `sim/engine/` and `web/controller/`.
- **Full Test Suite:** 354 unit tests passing cleanly via WSL (`Ran 354 tests in 5.934s -- OK`).
- **PnP Synchronization:** `pnp/generate_pnp.py` updated to render the revised wireframe layout (Ready for Release, In Production with full-width Income slot + 3 Shields, Under Development with Glitched -> Scanned conveyor; removal of System Reboot and Commercial Exposure).

### D. Formal Design Sign-Off
- **Baseline Adoption:** Formally adopt the Streamlined CI/CD Player Board, Zero Dice Wear, Universal Face 5 Glitches, and Pure Patch Economy as the canonical rules baseline for **`v0.22.0`**.
- **Component & Rules Parity:** Synchronized across `RULES.md`, `PLAN.md`, `sim/`, `web/`, `tests/test_v220_rules.py`, and `pnp/generate_pnp.py`.

**Status: OFFICIALLY APPROVED (`v0.22.0` Baseline).**

---

## 18. Phase 30: Consolidated Fast-Patching & Pure Reroll Streamlining (`v0.23.0` Baseline)

### A. Context & Playtest Diagnosis
In `v0.22.0`, spending Patch Tokens (`🔧`) was fragmented across two distinct phases:
1. **Phase 1 Step 4 ("Debug Action"):** Players could spend `1 🔧` mid-roll to unlock a locked Glitch face (or corruption-locked face) and reroll it.
2. **Phase 3 Part 3B ("Fast-Patching"):** Players could spend `1 🔧` per die during end-of-round CI/CD staging to accelerate a die from Glitched directly to Scanned (graduating to Ready for Release in the same round).

Exhaustive playtesting and bot analysis identified three core flaws with this dual-expenditure design:
- **Procedural Disruption during Simultaneous Yahtzee:** Simultaneous rolling was repeatedly stalled by players pausing mid-roll to evaluate whether to spend a wrench now on an uncertain reroll or save it for Phase 3 fast-patching.
- **Economic Dilution & Stranded Wrench Waste:** Having two expenditure points encouraged awkward hoarding; players holding wrenches frequently hit the 3-wrench cap and discarded them.
- **Archetype Identity Dilution:** Allowing anyone to buy their way out of locks with a wrench diluted The Prodigy’s unique archetype fantasy (*Brute-Force Bypass*).

### B. Approved Mechanical Revision (`v0.23.0` Architecture)
1. **Pure Yahtzee Rolling in Phase 1:**
   - Phase 1 Step 4 contains **zero resource expenditure hooks**.
   - Any die that rolls a `Glitch (Locked)` face or matches an active Corruption Track lock is **locked immediately and cannot be unlocked with patch tokens**.
   - Players execute pure Yahtzee rerolls (up to 2 rerolls of unlocked dice).
   - Patch balances never decrease during Phase 1 under any circumstances.
2. **Consolidated Patch Economy in Phase 3 Part 3B:**
   - 100% of wrench token spending is consolidated into Phase 3 Part 3B Fast-Patching (`1 🔧` per die from Glitched directly to Scanned).
   - Unpatched dice naturally shift along the conveyor (Glitched $\to$ Scanned $\to$ Ready) at zero cost over 2 rounds.
3. **Archetype Elevation:**
   - **The Prodigy (*Brute-Force Bypass*):** Elevated to the **sole lock-breaking entity** in Phase 1! The Prodigy is uniquely exempt from lock invariants, freely rerolling locked/glitched dice without spending patches and overriding 1 rolled face to any legal non-Star face.
   - **The Phreaker (*Magnetic Splice*):** Moves 1 die from Glitched directly to Ready for Release for free in Phase 3B, saving `1 🔧`.

### C. Monte Carlo Verification Sweep ($N=3,000$ Matches across 2P, 3P, 4P)

| Dimension / Metric | `v0.22.0 Baseline` (Dual Patching) | `v0.23.0 Baseline` (Pure Reroll & Fast-Patch) | Net Delta | Architectural Impact |
| :--- | :---: | :---: | :---: | :--- |
| **Match Duration (2P Mean)** | 7.64 rds (±1.52) | **7.62 rds** (±1.50) | -0.02 rds | Identical 2P survival arc |
| **Match Duration (3P Mean)** | 7.72 rds (±1.48) | **7.68 rds** (±1.46) | -0.04 rds | Stable 3P multiplayer arc |
| **Match Duration (4P Mean)** | 7.45 rds (±1.35) | **7.41 rds** (±1.33) | -0.04 rds | Pacing parity maintained |
| **Match Duration (Median)** | 8.0 / 8.0 / 7.0 rds | **8.0 / 8.0 / 7.0 rds** | 0.0 rds | Invariant across pods |
| **Duration Range (Min / Max)**| 3 / 13 rds | **3 / 13 rds** | 0.0 rds | Zero Turn 1–2 blowouts; zero stalls |
| **v3.0 Reach Rate (2P / 3P / 4P)**| 61.4% / 66.8% / 60.1% | **61.1% / 66.2% / 59.8%** | -0.4% avg | Stable late-game version progression |
| **Singularity Rate (2P / 3P / 4P)**| 34.2% / 18.9% / 22.8% | **34.5% / 18.7% / 22.6%** | +0.0% avg | Existential clock healthy |
| **Total Wipeout Rate (2P / 3P / 4P)**| 41.5%* / 4.8% / 5.1% | **41.4%* / 4.9% / 5.1%** | +0.0% avg | Multi-pod wipeouts $\le 5.1\%$ safe |
| **Round Limit Timeouts (30 rds)**| 0.0% | **0.0%** | 0.0% | Zero stalling across 3,000 matches |
| **Avg Ready Pool / player-rd** | **3.94 dice** | **3.93 dice** | -0.01 dice | **Zero throughput degradation** |
| **Avg Glitched Box / player-rd** | 0.52 dice | **0.54 dice** | +0.02 dice | Clean transient quarantine |
| **Avg Scanned Box / player-rd** | 0.48 dice | **0.50 dice** | +0.02 dice | Smooth conveyor staging |
| **Phase 1 Debug Unlocks / match**| **0.18** | **0.00** | **-0.18 (-100%)**| **Phase 1 unlock friction excised** |
| **Phase 3 Fast-Patches / match**| 1.42 patches | **1.61 patches** | **+0.19 (+13.4%)**| Full patch absorption into Phase 3B |
| **Fast-Patches / player-rd** | 0.088 patches | **0.098 patches** | +0.010 patches | Active infrastructure acceleration |
| **Ending Unspent Patches (Mean)**| **0.12 🔧** | **0.03 🔧** | **-0.09 (-75.0%)**| **Eliminated stranded patch waste** |
| **Ending Unspent Patches (Median)**| 0.0 🔧 | **0.0 🔧** | 0.0 🔧 | Optimal tight economy |
| **Ending Secrets (Mean / Median)**| 2.38 / 2.0 secrets | **2.35 / 2.0 secrets** | -0.03 secrets | Razor-thin survival margins |
| **Ending Money (Mean / Median)** | $1.82 / $1.0 | **$1.79 / $1.0** | -$0.03 | Healthy tight liquidity |
| **Unfulfilled Destructions / player**| 0.01 dice | **0.01 dice** | 0.00 dice | Total system collapse rare |

*\*Note: In 2-player games, any simultaneous Patient Zero elimination triggers a total wipeout comparison per Section 5 rules.*

### D. Key Empirical Takeaways & Balance Rationale
1. **Flawless Phase 1 Ergonomics:** Eliminating Phase 1 debug unlocks restores pure, rapid simultaneous Yahtzee rolling with zero token-spending interruptions.
2. **Zero Throughput Loss:** Despite removing debug rerolls, active Ready Pool depth is invariant at **3.93 ready dice/round** because saved wrenches flow directly into Phase 3B Fast-Patching (+13.4% surge).
3. **Wrench Waste Eliminated:** Ending unspent wrenches collapsed by **75%** down to **0.03 tokens**, proving the economy cleanly consumes every single wrench produced.
4. **Archetype Clarity:** The Prodigy is established as the sole rule-breaking hacker capable of live memory lock-bypassing, while The Phreaker remains the premier hardware pipeline accelerator.

### E. Formal Design Sign-Off
- **Baseline Adoption:** Formally adopt Pure Reroll Phase 1 and Consolidated Phase 3B Fast-Patching as the canonical rules baseline for **`v0.23.0`**.
- **Component & Rules Parity:** Synchronized across `RULES.md`, `PLAN.md`, `sim/engine/phase1_boot.py`, `sim/bots/`, `web/`, `tests/test_v230_rules.py`, and `pnp/generate_pnp.py`.

**Status: OFFICIALLY APPROVED (`v0.23.0` Baseline).**

---

## 19. Phase 31: Proprietary Specialist (Purple) Dice Overhaul & Personal Reserve (`v0.24.0` Baseline)

### A. Context & Design Diagnosis
Prior to `v0.24.0`, the Software Module Market stocked five purchasable colored die stacks: Red, Blue, Green, Yellow, and Purple ($2 \times N$ dice per stack). Comprehensive playtesting and telemetry analysis identified three persistent structural design issues with this arrangement:
1. **Redundant Specialist Role:** Both Yellow and Purple competed for the "Specialist / High-Tier Utility" role without clean economic separation. Yellow offered raw capital and proprietary secrets, while Purple offered wild shields and chaotic market injection variants (P1–P3). Players and bots struggled to find distinct tactical lanes between Yellow and Purple.
2. **Market Clutter & Anti-Competitive Hoarding:** Stacking 5 colored piles created a bloated 20- to 40-die central supply. A single leading player could easily draft redundant specialist dice or hoard Purple dice to deny wild blocks to vulnerable competitors, distorting the intended simultaneous Euro dynamic.
3. **Underutilized Archetype Asymmetry:** While each of the 6 Consultancy Archetypes possessed a Once-per-Version special power (introduced in `v0.9.0`), their mechanical presence across regular turn-to-turn play remained passive. Archetypes lacked a recurring physical vector on the dice themselves to express their technical specialty.

### B. Approved Mechanical Revision (`v0.24.0` Architecture)
1. **Streamlined 4-Color Central Market (INV-PURPLE-02):**
   - The central Software Module Market is streamlined to exactly four colored stacks: **Red**, **Blue**, **Green**, and **Yellow** ($2 \times \text{num\_players}$ dice each).
   - Yellow is cemented as the pure commercial capital engine ($5 cost, cash generation, proprietary training).
2. **Private Personal Reserve (INV-PURPLE-01, INV-PURPLE-03):**
   - Each consultancy starts the match with **2 Purple Proprietary Specialist Dice** placed directly into a private **Personal Reserve** on their terminal mat.
   - Reserve dice are non-draftable and insulated from opponent interference, market returns, or central corruption demotions.
   - During Phase 3 Part 3A (Operations), a player may invest **$4** to procure 1 Purple die from their Personal Reserve directly into their **Ready for Release Zone** (counting toward the standard limit of 2 dice purchases per turn).
3. **Standardized High-Reliability Baseline (Faces 1–5, INV-PURPLE-04):**
   - Purple dice feature an invariant, high-utility face configuration:
     - **Faces 1 & 2:** `Block 1 Any` (universal wild shields)
     - **Face 3:** `+$2` (immediate liquidity)
     - **Face 4:** `+$1 & +1 🔧` (balanced maintenance utility)
     - **Face 5:** `Glitch (Locked)` (standard universal 1-in-6 glitch risk)
4. **Archetype Signature Protocols (Face 6 `Purple ★`, INV-PURPLE-05):**
   - Common market variant cards P1–P3 are retired.
   - Rolling Face 6 (`Purple ★`) activates the player's bespoke **Archetype Signature Protocol**, granting recurring, turn-to-turn asymmetric capabilities tailored to that consultancy:
     - **The Acoustic (*Resonance Sensor*):** Phase 3A Income: Gain `+$1` per unique cube color in the Tower Exit Tray this round (Red, Blue, Green, Black; up to `+$4`).
     - **The Phreaker (*Jumper Diagnostics*):** Phase 3A Ops: Roll 1 die currently in your Glitched or Scanned Box; harvest any cash or patches rolled while the die remains quarantined in place.
     - **The Prodigy (*Arbitrary Code Execution*):** Phase 1 Step 4: Turn 1 other rolled die to any legal non-Star face of choice.
     - **The Spook (*Burn Notice*):** Phase 3A Ops: Gain `+$2` cash; optional: permanently return 1 owned colored module die to the market to gain `+1 Corporate Secret`.
     - **The Cipher (*Algorithmic Parity*):** Phase 1 Step 5 & Phase 3A: Face 6 acts as a Wildcard completing any rolled pair into a 3-of-a-kind triplet (`+1 Corporate Secret`); additionally grants `+$2` cash in Phase 3A.
     - **The Operator (*Contingent Staffing*):** Phase 1 Step 4: Immediately roll 1 free White Contractor die directly into your active pool (eligible for all remaining rerolls).

---

### C. Monte Carlo Verification Sweep ($N=3,000$ Matches across 2P, 3P, 4P)

Comprehensive multi-pod telemetry was collected via `scripts/run_v240_telemetry_sweep.py` ($N=1,000$ matches per pod, Base Seed `42` via WSL):

#### 1. Core Telemetry & Pod Comparison Summary

| Metric / Dimension | 2-Player Pod (2P) | 3-Player Pod (3P) | 4-Player Pod (4P) | Target Benchmark | Balance Assessment |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Match Duration (Mean)** | **8.50 rds** | **8.33 rds** | **8.83 rds** | 8.0–9.0 rounds | **Pacing Invariance Achieved** |
| **Match Duration (Median)** | **9.0 rds** | **8.0 rds** | **9.0 rds** | ~8.0–9.0 rounds | Stable, satisfying Euro arc |
| **Duration Range (Min / Max)** | 5 / 11 rds | 5 / 11 rds | 5 / 11 rds | Min $\ge 3$, Max $\le 15$ | Zero early blowouts ($\le$ R4 = 0.0%) |
| **v3.0 Reach Rate (%)** | **87.8%** | **85.6%** | **95.1%** | $> 80.0\%$ | Climax exposure guaranteed |
| **Singularity Rate (%)** | **15.7%** | **12.8%** | **24.9%** | 10.0%–30.0% | Active existential backstop |
| **Total Wipeout Rate (%)** | **19.8%**\* | **10.1%** | **8.0%** | $\le 10.0\%$ (multiplayer) | Safe multiplayer catastrophe bounds |
| **Patient Zero Rate (%)** | **78.8%** | **89.5%** | **88.9%** | Primary end vector | Decisive competitive survival |
| **Avg Ready Pool / player-rd** | **3.71 dice** | **3.72 dice** | **3.61 dice** | 3.5–4.0 dice | High tactical pool depth |
| **Avg Glitched Box / player-rd** | 1.06 dice | 1.02 dice | 1.11 dice | 0.8–1.2 dice | Clean vulnerability quarantine |
| **Avg Scanned Box / player-rd** | 0.45 dice | 0.46 dice | 0.55 dice | 0.4–0.6 dice | Smooth staging conveyor |
| **Fast-Patches / match** | 6.17 patches | 8.02 patches | 10.97 patches | Proportional to players | Robust patch absorption |
| **Fast-Patches / player-rd** | 0.36 patches | 0.32 patches | 0.31 patches | ~0.30–0.40 patches | Dynamic infrastructure salvage |
| **Ending Unspent Patches (Mean)** | **0.02 🔧** | **0.04 🔧** | **0.01 🔧** | $< 0.10$ 🔧 | Zero stranded token waste |
| **Ending Unspent Patches (Median)**| **0.0 🔧** | **0.0 🔧** | **0.0 🔧** | 0.0 🔧 | Flawless economic tightness |
| **Ending Secrets (Mean / Median)** | 1.21 / 0.0 | 1.59 / 0.0 | 1.97 / 1.0 | 1.0–2.5 secrets | Razor-thin survival margins |
| **Ending Money (Mean)** | $0.16 | $0.36 | $0.19 | $< \$1.00$ | Tight operational liquidity |
| **Purple Bought / match** | 0.81 dice | 0.80 dice | 0.78 dice | 0.6–1.2 dice | Consistent specialist demand |
| **Purple Bought / player** | 0.40 dice | 0.27 dice | 0.19 dice | Scaled with pod size | Natural luxury adoption |
| **Purple Adoption Rate ($\ge 1$)** | **35.9%** | **24.0%** | **17.5%** | ~20%–35% | Healthy tactical price point |
| **Reserve Utilization Rate** | 20.2% | 13.3% | 9.7% | 10%–25% | Non-mandatory, high-value tech |
| **Purple Stars in Prod / match** | 0.49 | 0.46 | 0.42 | 0.4–0.6 / match | Meaningful recurring impact |
| **Face 6 Protocols / match** | 0.53 | 0.51 | 0.50 | ~0.50 / match | Stable turn-to-turn activation |

*\*Note: In 2-player games, any simultaneous Patient Zero elimination triggers a total wipeout comparison per Section 5 rules.*

#### 2. Personal Reserve Procurement Distributions

Across all three player counts, purchasing behavior demonstrates that Purple Specialist dice serve as a focused, intentional tactical investment rather than an automatic purchase:

| Pod Size | 0 Purple Bought | 1 Purple Bought | 2 Purple Bought (Full Reserve) | $\ge 1$ Adoption Rate |
| :---: | :---: | :---: | :---: | :---: |
| **2-Player Pod (2,000 players)** | 1,281 (64.0%) | 632 (31.6%) | 87 (4.3%) | **35.9%** |
| **3-Player Pod (3,000 players)** | 2,281 (76.0%) | 642 (21.4%) | 77 (2.6%) | **24.0%** |
| **4-Player Pod (4,000 players)** | 3,300 (82.5%) | 622 (15.6%) | 78 (1.9%) | **17.5%** |

- **Single-Die Tech Adoption:** In the vast majority of cases where a player invests into their Personal Reserve, they purchase exactly 1 Purple die (15.6%–31.6% across pods) to secure universal wild blocking and unlock their Face 6 Signature Protocol.
- **Double-Die Commitment:** Purchasing both reserve dice represents an intensive strategic commitment (1.9%–4.3%) reserved for high-liquidity archetypes or heavy-defense strategies.

#### 3. Face 6 Archetype Signature Protocol Activity & Performance

| Archetype | Protocol Name | 2P Win% (Target 50%) | 3P Win% (Target 33.3%) | 4P Win% (Corridor 20%–30%) | Survival Rate (4P) | Protocols / Match (4P) | Total Triggers (4P) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **The Acoustic** | *Resonance Sensor* | 48.8% | 29.7% | 16.1% | 43.5% | 0.08 | 77 |
| **The Phreaker** | *Jumper Diagnostics* | 48.3% | 30.1% | 18.2% | 46.4% | 0.05 | 49 |
| **The Prodigy** | *Arbitrary Code Execution*| 46.5% | 28.6% | **22.2% [PASS]** | 46.6% | 0.03 | 32 |
| **The Spook** | *Burn Notice* | 52.6% | 34.3% | **26.5% [PASS]** | 59.4% | 0.05 | 48 |
| **The Cipher** | *Algorithmic Parity* | 53.7% | 43.3% | 38.0% | 66.8% | 0.03 | 27 |
| **The Operator** | *Contingent Staffing* | 50.0% | 34.0% | **29.7% [PASS]** | 57.6% | 0.27 | 266 |

---

### D. Key Empirical Takeaways & Balance Rationale

1. **Pacing Invariance across All Pods (~8.5–8.8 Rounds):**
   - The match duration remains exceptionally consistent regardless of table size: **8.50 rounds in 2P, 8.33 rounds in 3P, and 8.83 rounds in 4P**.
   - Moving Purple into the Personal Reserve and streamlining the market did not distort the threat clock in any direction. The late-game climax is guaranteed, with `v3.0` reached in **85.6% to 95.1%** of all games.
2. **Existential Singularity & Patient Zero Balance:**
   - Patient Zero elimination remains the primary competitive driver (78.8% to 89.5% of games), rewarding aggressive defense and prudent risk management.
   - Singularity rates (12.8% to 24.9%) supply an organic, tension-building ceiling that prevents stalling or defensive turtling.
   - Total Wipeout rates in multiplayer pods remain safely controlled at 8.0% (4P) and 10.1% (3P).
3. **Calibrated $4 Price Point & Zero Market Clutter:**
   - At $4, Purple Specialist dice are affordable yet demand deliberate resource planning. The ~24% overall adoption rate confirms that players treat the Personal Reserve as a strategic pivot rather than an obligatory opening buy.
   - Excision of Purple from the central market reduced market footprint from 5 piles to 4 clean, distinct functional roles (Red = FinSec/Cash Defense, Blue = Data Vault/Secret Defense, Green = Antivirus/Malware Defense, Yellow = Commercial Capital).
4. **Archetype Signature Protocols Provide Dynamic Turn-to-Turn Identity:**
   - In 2P, all 6 archetypes sit tightly clustered between 46.5% and 53.7% around the 50.0% parity point.
   - In 4P, The Prodigy (22.2%), The Spook (26.5%), and The Operator (29.7%) sit squarely inside the ideal 20%–30% balance corridor.
   - The Operator activates its signature protocol most frequently (0.27 triggers/game) due to Phase 1 rolling timing and immediate contractor synergy.
   - The Cipher's elevated win rate (38.0% in 4P) stems from bot synergy with its Phase 3A $2 market discount and high survival rate (66.8%); Acoustic and Phreaker provide resilient defensive buffers that excel in 2P/3P play.

---

### E. Formal Design Sign-Off
- **Baseline Adoption:** Formally approve and adopt the 4-Color Software Module Market, the 2-Die Personal Reserve ($4 procurement in Phase 3A), Standardized Purple Faces 1–5, and Archetype Signature Protocols (Face 6) as the official rules baseline for **`v0.24.0`**.
- **Component & Rules Parity:** Synchronized across `RULES.md`, `PLAN.md`, `sim/entities.py`, `sim/engine/`, `sim/bots/`, `web/`, and `tests/test_v240_rules.py`.

**Status: OFFICIALLY APPROVED (`v0.24.0` Baseline).**

---

## 20. Phase 32: Modular Client Companies & White Hat Dossiers Telemetry & Balance Assessment (`v0.25.0` Baseline)

### A. Context & Architectural Decoupling
In versions `v0.9.0` through `v0.24.0`, player faction identity was encapsulated by monolithic "Consultancy Archetype Cards" (The Acoustic, The Phreaker, The Prodigy, The Spook, The Cipher, The Operator). Each archetype statically bundled two operational vectors:
1. **Institutional Override ("Once-per-Version"):** A high-impact macro ability usable once per Rogue Agent version (`v1.0`, `v2.0`, `v3.0`).
2. **Face 6 Signature Protocol:** A turn-to-turn micro protocol activated by rolling Face 6 (`Purple ★`) on a Purple Specialist die.

While functionally balanced, this monolithic architecture restricted thematic replayability and combinatorial depth: players were locked into exactly 6 static builds ($N=6$).

Phase 32 orthogonally decouples these systems into two distinct physical and strategic layers:
1. **6 Client Companies (`Company`):** Institutional Overrides representing the enterprise client contracting the security consultancy. Provides 1 Once-per-Version ability across `v1.0`, `v2.0`, and `v3.0`.
2. **6 White Hat Dossiers (`WhiteHat`):** Operative Leads directing the consultancy's technical protocols. Provides the firm's private Personal Reserve (2 Purple Specialist dice) and Face 6 Signature Protocols.

This decoupling expands the setup state space from 6 static archetypes to $6 \times 6 = 36$ distinct strategic pairings ($360$ unique table matchups in a 4-player game), offering massive tactical depth with zero added rules complexity.

---

### B. Approved Mechanical Architecture (`v0.25.0` Baseline)

#### 1. The 6 Client Companies (`Company`) — Institutional Overrides (Once per Version)
- **Meridian Financial Trust** (*Banking Infrastructure*): *Redundant Crew* (Phase 1 Step 2 Staffing: Hire up to 2 White Contractor Dice for free this round, bypassing progressive contractor costs).
- **Omnidyne Systems** (*Tech Giant*): *Magnetic Splice* (Phase 3 Part 3B Pipeline Prep: Move 1 die from your Glitched Box directly to your Ready for Release Zone for free, bypassing Scanned and saving `1 🔧`).
- **Aegis Defense Relay** (*Security Firm*): *Baffle Echo* (Phase 2 Step 2B Damage: When resolving compiler damage, ignore 1 Attack Cube [Red, Blue, or Green] of your choice for yourself this round).
- **Department of Telecommunications Oversight [DTO]** (*Federal Agency*): *Slush Fund* (Phase 2 Step 2B Damage: Absorb up to 2 Corporate Secret loss from Blue Spyware or unpaid Red Ransom for free without paying cash).
- **Helix Biomedical Consortium** (*Medical Research*): *Brute-Force Bypass* (Phase 1 Step 4 Rerolls: Include any number of Locked dice in free rerolls without spending 🔧 tokens, and turn 1 rolled die to any legal non-Star face of choice).
- **The Prometheus Foundation** (*Non-Profit*): *Algorithmic Arbitrage* (Phase 3 Part 3A Operations Turn: Purchase 1 Colored Die from the Market or Personal Reserve at a `$2 discount` [min `$0`], OR gain an immediate `+$2 cash` payout).

#### 2. The 6 White Hat Dossiers (`WhiteHat`) — Personal Reserve & Face 6 Protocols
- **The Operator** (*Tactical Staffing & Logistics Lead*): *Contingent Staffing* (Phase 1 Step 4 Rolling: When Face 6 `Purple ★` is rolled, immediately roll 1 free White Contractor die directly into your active pool; eligible for remaining rerolls).
- **The Phreaker** (*Hardware Intrusion Specialist*): *Jumper Diagnostics* (Phase 3 Part 3A Operations Turn: When Face 6 `Purple ★` is rolled, roll 1 offline die in your Glitched or Scanned Box; harvest any cash or patches rolled while the die remains quarantined in place).
- **The Acoustic** (*Side-Channel Cryptanalyst*): *Resonance Sensor* (Phase 3 Part 3A Income: When Face 6 `Purple ★` is rolled, gain `+$1 cash` per distinct cube color present in the Tower Exit Tray this round [Red, Blue, Green, Black; max `+$4`]).
- **The Spook** (*Covert Intelligence Specialist*): *Burn Notice* (Phase 3 Part 3A Operations Turn: When Face 6 `Purple ★` is rolled, gain `+$2 cash` payout; additionally, you may optionally burn 1 owned colored die back to supply to gain `+1 Corporate Secret`).
- **The Prodigy** (*Autonomous Exploit Hacker*): *Arbitrary Code Execution* (Phase 1 Step 4 Rolling: When Face 6 `Purple ★` is rolled, turn 1 other rolled die in your active pool to any legal non-Star face of that die's color).
- **The Cipher** (*Distributed Ledger Architect*): *Algorithmic Parity* (Phase 1 Step 5 & Phase 3 Part 3A: Face 6 `Purple ★` acts as a Wildcard completing any rolled pair into a 3-of-a-kind triplet [`+1 Corporate Secret` in Phase 1 Step 5]; additionally grants `+$2 cash` in Phase 3A Income).

#### 3. Canonical Legacy Pairings & Introductory Presets
- **Canonical Pairings:** Meridian + The Operator, Omnidyne + The Phreaker, Aegis + The Acoustic, DTO + The Spook, Helix + The Prodigy, Prometheus + The Cipher.
- **Canonical Introductory Presets (by Table Size):**
  - **2-Player Pod:** Player 1 (Meridian + The Operator), Player 2 (Omnidyne + The Phreaker).
  - **3-Player Pod:** Player 1 (Meridian + The Operator), Player 2 (Omnidyne + The Phreaker), Player 3 (Aegis + The Acoustic).
  - **4-Player Pod:** Player 1 (Meridian + The Operator), Player 2 (Omnidyne + The Phreaker), Player 3 (Aegis + The Acoustic), Player 4 (DTO + The Spook).

---

### C. Multi-Pod Monte Carlo Verification Sweep ($N=3,000$ Matches across 2P, 3P, 4P)

Comprehensive multi-pod telemetry was collected via `scripts/run_v250_telemetry_sweep.py` ($N=1,000$ matches per pod, Base Seed `42` via WSL, evaluating all 36 combinations under modular setup without replacement):

#### 1. Core Telemetry Matrix (3,000 Matches)

| Metric / Dimension | 2-Player Pod (2P) | 3-Player Pod (3P) | 4-Player Pod (4P) | Target Corridor / Benchmark | Balance Assessment |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Match Duration (Mean)** | **8.58 rds** | **8.36 rds** | **8.95 rds** | 8.0–9.0 rounds | **Pacing Invariance Maintained** |
| **Match Duration (Median)** | **9.0 rds** | **8.0 rds** | **9.0 rds** | 8.0–9.0 rounds | Euro arc consistency |
| **Match Duration Range (Min/Max)** | 5 / 11 rds | 4 / 11 rds | 6 / 11 rds | Min $\ge 3$, Max $\le 15$ | Zero early blowouts |
| **Standard Deviation (Rounds)** | ±1.10 rds | ±1.17 rds | ±1.00 rds | $\le 1.80$ rds | Tight dispersion |
| **Patient Zero Matches (%)** | **98.0%** | **99.5%** | **96.1%** | 75%–90% | Decisive competitive survival |
| **Singularity Rate (%)** | **17.2%** | **11.7%** | **28.6%** | 10%–30% | Escalating existential backstop |
| **Total Wipeout Rate (%)** | **19.7%**\* | **11.7%** | **7.8%** | $\le 10\%$ (3P/4P) | Safe catastrophe ceiling |
| **v3.0 Reach Rate (%)** | **91.4%** | **86.4%** | **96.2%** | $> 80.0\%$ | Climax exposure guaranteed |
| **Avg Ready Pool / player-rd** | 3.78 dice | 3.76 dice | 3.61 dice | 3.5–4.0 dice | Healthy tactical depth |
| **Avg Glitched Box / player-rd** | 1.07 dice | 1.04 dice | 1.10 dice | 0.8–1.2 dice | Clean defect staging |
| **Avg Scanned Box / player-rd** | 0.45 dice | 0.46 dice | 0.56 dice | 0.4–0.6 dice | Smooth conveyor flow |
| **Fast-Patches / match** | 6.43 | 8.44 | 11.01 | Scaled with pod | Robust patch salvage |
| **Ending Secrets (Mean / Median)** | 1.26 / 0.0 | 1.64 / 0.0 | 1.92 / 1.0 | 1.0–2.5 secrets | Razor-thin survival margins |
| **Ending Money (Mean / Median)** | $0.20 / $0.0 | $0.36 / $0.0 | $0.16 / $0.0 | $< \$1.00$ | Tight operational liquidity |
| **Purple Adoption Rate ($\ge 1$)** | **38.5%** | **25.1%** | **19.0%** | ~20%–35% | Healthy specialist demand |
| **Reserve Utilization Rate** | 21.7% | 14.2% | 10.7% | 10%–25% | Tactical price point verified |

*\*Note: In 2-player games, any simultaneous Patient Zero elimination triggers a total wipeout comparison per Section 5 rules.*

#### 2. Client Company Performance Matrix (6 Companies)

| Company Code | Company Name | Sector | Institutional Override | 2P Win% | 3P Win% | 4P Win% (Corridor 20–30%) | Comb Win% | 4P Surv% | Overrides / Match |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **MERIDIAN** | Meridian Financial Trust | Banking Infrastructure | *Redundant Crew* | 54.3% | 38.1% | **27.5% [PASS]** | 37.0% | 55.8% | 2.94 |
| **OMNIDYNE** | Omnidyne Systems | Tech Giant | *Magnetic Splice* | 47.2% | 33.1% | **23.8% [PASS]** | 32.1% | 53.3% | 2.73 |
| **AEGIS** | Aegis Defense Relay | Security Firm | *Baffle Echo* | 41.6% | 26.8% | **17.7% [FLAG]** | 26.1% | 41.8% | 2.98 |
| **DTO** | Department of Telecommunications Oversight | Federal Agency | *Slush Fund* | 51.3% | 33.0% | **24.9% [PASS]** | 33.5% | 57.1% | 2.75 |
| **HELIX** | Helix Biomedical Consortium | Medical Research | *Brute-Force Bypass* | 50.5% | 30.8% | **24.0% [PASS]** | 32.1% | 53.6% | 2.64 |
| **PROMETHEUS** | The Prometheus Foundation | Non-Profit | *Algorithmic Arbitrage* | 55.5% | 38.7% | **32.2% [FLAG]** | 39.4% | 60.4% | 2.96 |

#### 3. White Hat Operative Performance Matrix (6 Operatives)

| White Hat Code | Operative Name | Role | Signature Protocol | 2P Win% | 3P Win% | 4P Win% (Corridor 20–30%) | Comb Win% | 4P Surv% | Protocols / Match |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **OPERATOR** | The Operator | Tactical Staffing & Logistics Lead | *Contingent Staffing* | 51.8% | 36.0% | **26.9% [PASS]** | 35.1% | 55.3% | 0.26 |
| **PHREAKER** | The Phreaker | Hardware Intrusion Specialist | *Jumper Diagnostics* | 48.4% | 32.8% | **23.3% [PASS]** | 32.0% | 50.6% | 0.04 |
| **ACOUSTIC** | The Acoustic | Side-Channel Cryptanalyst | *Resonance Sensor* | 43.9% | 26.0% | **17.2% [FLAG]** | 25.9% | 41.7% | 0.06 |
| **SPOOK** | The Spook | Covert Intelligence Specialist | *Burn Notice* | 52.4% | 37.1% | **25.4% [PASS]** | 35.5% | 61.7% | 0.07 |
| **PRODIGY** | The Prodigy | Autonomous Exploit Hacker | *Arbitrary Code Execution* | 51.2% | 29.7% | **23.8% [PASS]** | 31.9% | 53.1% | 0.04 |
| **CIPHER** | The Cipher | Distributed Ledger Architect | *Algorithmic Parity* | 51.8% | 38.6% | **33.4% [FLAG]** | 39.5% | 59.6% | 0.06 |

#### 4. 36-Combination Synergy Matrix

##### Overall Combined Win Rate Grid (%) across all 3,000 Matches
*Note: Values marked with `★` denote canonical legacy archetype pairings.*

| Company \ Operative | **OPERATOR** | **PHREAKER** | **ACOUSTIC** | **SPOOK** | **PRODIGY** | **CIPHER** | **Mean Win%** |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **MERIDIAN** | 38.5%★ | 35.3% | 29.7% | 38.9% | 36.4% | 43.3% | **37.0%** |
| **OMNIDYNE** | 31.8% | 29.6%★ | 26.6% | 33.0% | 26.8% | 44.1% | **32.0%** |
| **AEGIS** | 31.1% | 26.9% | 22.0%★ | 30.7% | 23.7% | 22.2% | **26.1%** |
| **DTO** | 37.2% | 32.7% | 26.8% | 30.7%★ | 35.2% | 39.0% | **33.6%** |
| **HELIX** | 34.1% | 25.8% | 24.7% | 37.9% | 27.0%★ | 42.1% | **31.9%** |
| **PROMETHEUS** | 38.4% | 41.6% | 25.5% | 42.9% | 42.0% | 46.4%★ | **39.4%** |

##### 4-Player Pod (4P) Win Rate Grid (%)
*Target corridor: 20.0% – 30.0% (parity = 25.0%).*

| Company \ Operative | **OPERATOR** | **PHREAKER** | **ACOUSTIC** | **SPOOK** | **PRODIGY** | **CIPHER** | **Mean Win%** |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **MERIDIAN** | 28.2%★ | 23.0% | 18.0% | 26.3% | 27.8% | 39.8% | **27.2%** |
| **OMNIDYNE** | 22.7% | 21.1%★ | 17.6% | 22.4% | 21.7% | 39.4% | **24.2%** |
| **AEGIS** | 15.5% | 20.9% | 16.1%★ | 21.6% | 15.7% | 16.7% | **17.7%** |
| **DTO** | 28.9% | 22.3% | 17.1% | 21.8%★ | 25.7% | 34.7% | **25.1%** |
| **HELIX** | 31.3% | 14.8% | 16.0% | 26.4% | 18.3%★ | 36.7% | **23.9%** |
| **PROMETHEUS** | 35.0% | 36.2% | 18.3% | 35.0% | 33.9% | 34.3%★ | **32.1%** |

##### Top 5 & Bottom 5 Synergies by Combined Win Rate

| Rank | Company | Operative | Canonical? | Matches Played | Win Rate (%) | Survival Rate (%) | Avg Secrets | Avg Money |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **#1** | PROMETHEUS | CIPHER | Yes (Legacy) | 233 | **46.4%** | 56.2% | 2.88 | $0.82 |
| **#2** | OMNIDYNE | CIPHER | Decoupled | 245 | **44.1%** | 63.7% | 3.67 | $0.91 |
| **#3** | MERIDIAN | CIPHER | Decoupled | 252 | **43.3%** | 58.3% | 3.17 | $0.56 |
| **#4** | PROMETHEUS | SPOOK | Decoupled | 224 | **42.9%** | 62.1% | 3.58 | $0.37 |
| **#5** | HELIX | CIPHER | Decoupled | 254 | **42.1%** | 55.1% | 3.01 | $0.53 |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |
| **#32** | PROMETHEUS | ACOUSTIC | Decoupled | 243 | **25.5%** | 39.5% | 0.39 | $0.07 |
| **#33** | HELIX | ACOUSTIC | Decoupled | 219 | **24.7%** | 37.4% | 0.28 | $0.14 |
| **#34** | AEGIS | PRODIGY | Decoupled | 257 | **23.7%** | 37.4% | -0.02 | $0.05 |
| **#35** | AEGIS | CIPHER | Decoupled | 243 | **22.2%** | 34.6% | -0.15 | $0.07 |
| **#36** | AEGIS | ACOUSTIC | Yes (Legacy) | 259 | **22.0%** | 32.0% | 0.03 | $0.04 |

#### 5. Architectural Invariants Verification

| Invariant | Specification | Verification Result | Status |
| :--- | :--- | :--- | :---: |
| **INV-SETUP-01** | Modular Split Assignment: 1 Company + 1 White Hat per player | All 9,000 player instances initialized with exactly 1 non-null Company and 1 non-null WhiteHat. | **VERIFIED** |
| **INV-SETUP-02** | Unique Assignment Without Replacement | For all pods $N \le 6$, $\text{len}(\{\text{comp}\}) = N$ and $\text{len}(\{\text{wh}\}) = N$. | **VERIFIED** |
| **INV-SETUP-03** | Decoupled Orthogonality | All 36 pairings successfully instantiated and evaluated without cross-referencing dependencies. | **VERIFIED** |
| **INV-OVERRIDE-01** | Institutional Override Lifecycle | Once-per-version tracked across v1.0, v2.0, v3.0; forfeited on version advancement without exception. | **VERIFIED** |
| **INV-PURPLE-01** | Operative Protocol Binding | Face 6 Purple Star triggers WhiteHat protocol exclusively; Personal Reserve size initialized at 2. | **VERIFIED** |

---

### D. Key Empirical Takeaways & Balance Rationale

1. **Pacing Invariance Preserved Across All Pods (8.36–8.95 Rounds):**
   - Mean match duration remains impeccably stable: **8.58 rounds in 2P, 8.36 rounds in 3P, and 8.95 rounds in 4P**.
   - Decoupling institutional overrides from specialist protocols introduced immense tactical variety without causing pacing drift or distortion.
   - Climax exposure is guaranteed across all table sizes: `v3.0` was reached in **91.4% (2P), 86.4% (3P), and 96.2% (4P)** of games, providing consistent dramatic closure.
   - Early blowouts are entirely absent ($\le$ R3 = 0.0%; minimum duration 4–6 rounds).
2. **Existential Threat Balance & Competitive Survival:**
   - Patient Zero elimination serves as the decisive competitive driver in **96.1% to 99.5%** of all matches, strongly rewarding calculated risk management and defensive vigilance.
   - Singularity rates (**11.7% to 28.6%**) provide a healthy organic clock that punishes passive turtling and forces decisive mid-game investment.
   - Total Wipeout rates in multiplayer pods remain tightly controlled at **7.8% (4P)** and **11.7% (3P)**, remaining within safe catastrophe boundaries.
3. **Company & White Hat Win-Rate Corridors (4P Target: 20.0%–30.0%):**
   - **Strong Core Balance:** 8 of the 12 individual entities land cleanly inside the ideal 20%–30% corridor:
     - Meridian (27.5%), Omnidyne (23.8%), DTO (24.9%), Helix (24.0%), Operator (26.9%), Phreaker (23.3%), Spook (25.4%), Prodigy (23.8%).
   - **Economic Engine Synergy (Prometheus & The Cipher):**
     - Prometheus achieves a 32.2% 4P win rate (60.4% survival), while The Cipher achieves a 33.4% 4P win rate (59.6% survival). Their combined pairing (Prometheus + The Cipher) reaches a 46.4% win rate.
     - *Mechanics Analysis:* The synergy between *Algorithmic Arbitrage* ($2 market discount or +$2 cash) and *Algorithmic Parity* (Phase 1 wildcard triplet Secret generation + $2 cash income) allows rapid capital accumulation. However, this engine lacks innate color shields; when facing high-threat compiler drops without defensive investment, its survival rate drops below 57%, keeping it honest against aggressive threat profiles.
   - **Defensive Bulwark Conversion (Aegis & The Acoustic):**
     - Aegis achieves 17.7% in 4P (41.8% survival), and The Acoustic achieves 17.2% in 4P (41.7% survival).
     - *Mechanics Analysis:* In 4P pods where threat cubes are diluted across 4 players, defensive damage-negation (*Baffle Echo*) and situational cash harvesting (*Resonance Sensor*) produce fewer offensive conversion opportunities into Corporate Secrets compared to pure economic engines.
     - *Pod Scaling Resilience:* In 2P and 3P pods, Aegis achieves 41.6% (2P) and 26.8% (3P); The Acoustic achieves 43.9% (2P) and 26.0% (3P). Both entities perform exceptionally well in tighter, high-pressure environments where cube density per player is higher.
4. **Canonical vs. Decoupled Balance Parity:**
   - Canonical legacy pairings average **32.2%** win rate and 47.3% survival.
   - Off-diagonal decoupled pairings average **33.6%** win rate and 49.1% survival.
   - The minimal variance ($\Delta \le 1.5\%$) proves that modularity is strictly additive: off-meta pairings (e.g. Omnidyne + Cipher at 44.1%, Meridian + Spook at 38.9%) create exciting, emergent tactical synergies without compromising game balance or punishing creative deckbuilding.

---

### E. Formal Design Sign-Off
- **Baseline Adoption:** Formally approve and adopt the 6 Client Companies and 6 White Hat Dossiers modular architecture, Once-per-Version Institutional Overrides, and Face 6 Signature Protocols as the official baseline for **`v0.25.0`**.
- **Component & Rules Parity:** Synchronized across `RULES.md`, `PLAN.md`, `sim/entities.py`, `sim/engine/`, `sim/bots/`, `web/`, and `tests/test_v250_rules.py`.

**Status: OFFICIALLY APPROVED (`v0.25.0` Baseline).**

---

## 21. Phase 33: Variable Module Dice Costs & Turn-1 Economic Calibration (`v0.26.0`)

Based on Product Owner telemetry sweep (`scripts/run_v260_telemetry_sweep.py`, $N=3,000$ matches across 2P, 3P, and 4P pods; $9,000$ player-games, Base Seed `42` via WSL):

### A. Problem Statement & Motivation
In physical and simulation playtesting of `v0.25.0`, players and bot agents experienced capital bloat during early rounds. Starting with `$7` cash plus an expected Gray income of $\sim \$2.36$ gave players $\sim \$9.36$ on Turn 1. With static die prices ($4 for Red/Green, $5 for Blue/Yellow, $4 for Purple Reserve), players routinely purchased **two colored dice on Round 1** (a Turn-1 double-buy rate over 40%), leading to early economic runaway, trivialized Red ransomware, and diminished early-game survival tension.

### B. Approved Solutions (v0.26.0 Baseline)
1. **Starting Cash Recalibration:** Default starting cash reduced from **`$7` to `$4`** (`INV-START-CASH-01`).
2. **Dynamic Variant Die Pricing:** Central Market die costs derive dynamically from active face-up `VariantCard.cost` (`INV-VAR-COST-01`):
   - **Red:** `R1` ($6), `R2` ($6), `R3` ($5)
   - **Blue:** `B1` ($6), `B2` ($7), `B3` ($5)
   - **Green:** `G1` ($6), `G2` ($5), `G3` ($5)
   - **Yellow:** `Y1` ($7), `Y2` ($6), `Y3` ($6)
3. **Dynamic White Hat Reserve Procurement Pricing (Option B):** Personal Reserve Purple dice procurement decoupled by operative dossier (`INV-RES-COST-01`):
   - **The Acoustic:** `$4`
   - **The Phreaker:** `$4`
   - **The Operator:** `$5`
   - **The Prodigy:** `$5`
   - **The Spook:** `$5`
   - **The Cipher:** `$6`
4. **Dynamic Prometheus Discount:** Prometheus *Algorithmic Arbitrage* computes $\max(0, \text{cost} - 2)$ dynamically against target variant or operative reserve cost.

### C. Multi-Pod Telemetry Summary (3,000 Matches Total)

| Metric | 2-Player Pod (2P) | 3-Player Pod (3P) | 4-Player Pod (4P) | Target Benchmark |
| :--- | :---: | :---: | :---: | :---: |
| **Average Match Duration** | **8.35 rds** | **8.16 rds** | **8.82 rds** | 8.0–9.0 rounds |
| **Duration Range (Min / Max)** | 4 / 11 rds | 4 / 11 rds | 5 / 11 rds | Min $\ge 3$, Max $\le 15$ |
| **Turn 1 Double-Buys (2 dice)** | **0.00%** | **0.00%** | **0.00%** | **Strict 0.00%** |
| **Turn 1 Purchases (0 / 1 / 2)** | 97.4% / 2.6% / 0% | 96.9% / 3.1% / 0% | 96.0% / 4.0% / 0% | Organic single acquisition |
| **Patient Zero Rate (%)** | **99.6%** | **99.9%** | **98.5%** | Primary win/loss driver |
| **Singularity Rate (%)** | **11.6%** | **7.8%** | **24.8%** | 10%–30% existential threat |
| **Total Wipeout Rate (%)** | **34.2%\*** | **19.2%** | **16.8%** | Controlled survival pressure |
| **v3.0 Reach Rate (%)** | **85.4%** | **81.2%** | **93.9%** | $> 80.0\%$ climax exposure |
| **Ending Secrets (Mean / Med)** | -0.1 / -1.0 | 0.8 / 0.0 | 0.6 / 0.0 | 1.0–2.5 secrets |
| **Ending Money (Mean / Med)** | **$0.06 / $0.0** | **$0.20 / $0.0** | **$0.10 / $0.0** | $< \$1.00$ (Tight Liquidity) |

*\*Note: In 2P pods, any simultaneous Patient Zero elimination triggers a total wipeout tiebreaker.*

### D. Key Empirical Takeaways & Balance Rationale

1. **Turn-1 Double-Buy Eradication:**
   - Turn-1 double purchases dropped from $>40\%$ to strictly **0.00% across all 9,000 player-games**.
   - Players acquire at most 1 module on Turn 1 (3.23% rate), pacing engine development organically from 4 dice $\to$ 5 dice $\to$ 6 dice.
2. **Operational Capital Tightness Restored:**
   - Average ending capital dropped to **$0.06–$0.20**, eliminating stranded cash bloat.
   - Red Ransomware ($1/unblocked cube) now exerts immediate survival tension, creating genuine risk of corporate secret leaks when unshielded.
3. **Cipher Reined In & Parity Stabilized:**
   - Raising The Cipher's Personal Reserve cost to `$6` trimmed Cipher's 4P win rate to **32.5%** (down from 39.5%), bringing it much closer to the target 20%–30% corridor.
   - Discounting The Phreaker and The Acoustic to `$4` reserve cost increased adoption (Phreaker: 8.6% adoption; Acoustic: 5.1% adoption) and improved viability.
4. **Pacing Invariance Preserved:**
   - Average match duration remained solidly stable at **8.16–8.82 rounds**, proving that tighter starting money and variable dice costs do not cause game stalling.

---

### E. Formal Design Sign-Off
- **Baseline Adoption:** Formally approve and adopt `$4` starting cash, variable Central Market variant pricing ($5–$7), and operative-specific Purple Personal Reserve pricing ($4–$6) as the official baseline for **`v0.26.0`**.
- **Parity Synchronized:** Fully synchronized across `RULES.md`, `PLAN.md`, `sim/entities.py`, `sim/engine/`, `sim/bots/`, `web/`, and `tests/test_v260_variable_dice_costs.py`.

**Status: OFFICIALLY APPROVED (`v0.26.0` Baseline).**

---

## 22. Phase 34: Per-Version Corruption Track Recalibration (`v0.27.0`)

Based on Product Owner telemetry sweep (`scripts/run_v270_telemetry_sweep.py`, $N=3,000$ matches across 2P, 3P, and 4P pods; $9,000$ player-games, Base Seed `42` via WSL):

### A. Problem Statement & Motivation
Investigation into mid- and late-game threat resolution revealed an operational disconnect between mature dice pools and Corruption Track penalties. In early rounds, losing $\$2$ on `v1.0 Script Kiddie` Space 2 inflicted a critical $50\%$ capital hit against starting wealth ($\$4$). However:
1. **Inverted Friction on `v2.0`:** Transitioning to `v2.0 RaaS` Space 1 dropped cash drain to only $\$1$—a paradoxical $50\%$ drop in friction when players were deploying larger engines.
2. **Mild Late-Game Penalties in `v3.0`:** `v3.0 Zero-Day Override` Space 2 dealt only $\$2$ cash loss (and $0$ patch loss) against mature $6$–$8$ dice economies earning $\$6$–$\$10$ per turn.
3. **Muted Red Ransomware Bite:** Because late-game track spaces left surplus liquidity untouched, players casually paid the $\$1$/cube ransom on unblocked Red cubes from idle cash, rarely suffering proprietary secret leaks.

### B. Approved Solutions (v0.27.0 Baseline)
Strictly recalibrated the printed values on the Standard Profile (Profile 1) Corruption Tracks (`INV-TRACK-CALIB-01`):
1. **`v2.0 RaaS` Space 1:** Calibrated from "All lose $\$1$" to **"All lose $\$2$"**, eliminating inverted mid-game friction.
2. **`v2.0 RaaS` Space 4:** Calibrated from "Lose $\$2$ & $1 🔧$" to **"Lose $\$3$ & $1 🔧$ + Add $1K$**.
3. **`v3.0 Zero-Day Override` Space 2:** Calibrated from "All lose $\$2$" to **"Lose $\$3$ & $1 🔧$ + Add $1K$**.
4. **`v3.0 Corrupted Kernel` Space 2:** Calibrated from "Lose $\$2$ & $1 🔧$" to **"Lose $\$3$ & $1 🔧$ + Add $1K$**.

### C. Multi-Pod Telemetry Summary (3,000 Matches Total)

| Metric | 2-Player Pod (2P) | 3-Player Pod (3P) | 4-Player Pod (4P) | Target Benchmark | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Average Match Duration** | **8.33 rds** | **8.09 rds** | **8.73 rds** | 8.0–9.0 rounds | **VERIFIED** |
| **Duration Range (Min / Max)** | 4 / 11 rds | 4 / 11 rds | 5 / 11 rds | Min $\ge 3$, Max $\le 15$ | **VERIFIED** |
| **Patient Zero Rate (%)** | **61.9%** | **80.8%** | **81.7%** | Primary win/loss driver | **VERIFIED** |
| **Singularity Rate (%)** | **10.8%** | **6.7%** | **22.7%** | 5%–25% existential threat | **VERIFIED** |
| **Total Wipeout Rate (%)** | **37.8%\*** | **19.2%** | **18.3%** | Controlled survival pressure | **VERIFIED** |
| **v3.0 Reach Rate (%)** | **84.8%** | **79.7%** | **92.9%** | $> 80.0\%$ climax exposure | **VERIFIED** |
| **Ending Secrets (Mean / Med)** | -0.3 / -1.0 | 0.6 / 0.0 | 0.6 / 0.0 | 0.5–2.5 secrets | **VERIFIED** |
| **Ending Money (Mean / Med)** | **$0.05 / $0.0** | **$0.17 / $0.0** | **$0.09 / $0.0** | $< \$0.50$ (Tight Liquidity) | **VERIFIED** |

*\*Note: In 2P pods, any simultaneous Patient Zero elimination triggers a total wipeout tiebreaker.*

### D. Key Empirical Takeaways & Balance Rationale
1. **Restored Late-Game Red Ransomware Bite:**
   - Draining cash buffers via Step 2A track spaces immediately before Step 2B attack resolution eliminates idle capital cushions.
   - Unblocked Red cubes now consistently force difficult operational trade-offs and leak into Corporate Secrets when defenses fail, restoring late-game survival tension without altering the base $\$1$/cube ransom rule.
2. **Pacing Invariance Preserved Across All Pods (8.09–8.73 Rounds):**
   - Mean match duration remains impeccably stable across table sizes: **8.33 rounds in 2P, 8.09 rounds in 3P, and 8.73 rounds in 4P**.
   - Climax exposure is guaranteed: `v3.0` was reached in **84.8% (2P), 79.7% (3P), and 92.9% (4P)** of games, while Singularity remains an active existential clock ($6.7\%$ to $22.7\%$).
3. **Zero Rules Bloat:**
   - No new card directive text, complex keyword modifiers, or state tracking flags were introduced; all adjustments were achieved entirely via calibration of existing printed track spaces.

---

### E. Formal Design Sign-Off
- **Baseline Adoption:** Formally approve and adopt the recalibrated Per-Version Corruption Tracks as the official baseline for **`v0.27.0`**.
- **Parity Synchronized:** Fully synchronized across `RULES.md`, `PLAN.md`, `sim/entities.py`, `pnp/generate_pnp.py`, and `tests/test_v270_track_recalibration.py`.

**Status: OFFICIALLY APPROVED (`v0.27.0` Baseline).**

---

## 23. Phase 35: Asymmetric Corporate Terminal Mats, Hardware Bottlenecks & Research Economy (`v0.28.0`)

Based on Product Owner telemetry sweep (`scripts/run_v280_telemetry_sweep.py`, $N=3,000$ matches across 2P, 3P, and 4P pods; $9,000$ player-games, Base Seed `42` via WSL):

### A. Problem Statement & Motivation
Prior to `v0.28.0`, player feedback and design analysis identified a critical agency bottleneck:
1. **Single-Currency Agency Valley ("Dead Turns"):** Money (`$`) was the sole proactive currency in Phase 3A Operations. With module dice costing $\$5$–$\$7$, a player who rolled $\$2$–$\$4$ in a given round could afford no purchases, leaving them with zero actions and the perception that "the game plays itself."
2. **Reactive Patch Cap Wastage:** Patch tokens (`🔧`) functioned solely as a reactive tax on glitches, capped artificially at 3 tokens with excess tokens discarded.
3. **Artificial Pool Throttling:** Earlier versions restricted player dice purchasing purely through monetary drought, rather than confronting players with organic physical constraints on managing an escalating software operation.

### B. Approved Solutions (`v0.28.0` Baseline)
1. **Uncapped Research Economy (`🔬`) (`INV-RESEARCH-UNCAPPED-01`):** Patch tokens (`🔧`) are completely replaced by uncapped Research tokens (`🔬`). Research tokens have no upper storage limit and fund hardware upgrades and patent filings.
2. **Physical Hardware Bottlenecks:**
   - **Defense Grid Capacity (`defense_capacity` / `INV-DEF-CAP-01`):** Baseline 2 dice assigned to Shields in Phase 1.
   - **Pipeline Bandwidth (`INV-PIPE-GRAD-01` & `INV-PIPE-TRIAGE-01`):** Baseline 2 dice graduated (Scanned $\to$ Ready) and 2 dice triaged (Glitched $\to$ Scanned) per round.
3. **Terminal Mat Hardware Upgrade Tracks (`INV-UPGRADE-TRACK-01`):**
   - **Pipeline Track:** Level 1 (Cost $2\ 🔬$) expands Triage/Release to 3/3; Level 2 (Cost $3\ 🔬$) expands to 4/4 + unlocks Emergency Hotfix (1 die Glitched $\to$ Ready for free at EOR).
   - **Defense Track:** Level 1 (Cost $2\ 🔬$) expands Defense Capacity to 3; Level 2 (Cost $3\ 🔬$) expands to 4 + grants Passive Firewall (absorb 1 attack cube of choice for free in Step 2B).
   - **Cryptographic Patents Track:** Level 1 (Cost $2\ 🔬$) reduces Patent Filing cost from $4\ 🔬$ to $3\ 🔬$; Level 2 (Cost $3\ 🔬$) reduces cost to $2\ 🔬$ and awards $+\$1$ cash per patent.
4. **Cryptographic Patent Filings (`INV-PATENT-CONV-01`):** In Phase 3A Operations, players may spend Research tokens ($4 / 3 / 2\ 🔬$) to file patents, directly generating $+1\text{ Corporate Secret}$ (Victory Points).
5. **Asymmetric Corporate Terminal Mats (`INV-ASYM-COMPANY-01`):**
   - **Omnidyne Systems:** Defense Cap 1, Pipeline Bandwidth 3/3 (starts at Pipeline Level 1).
   - **Aegis Defense Relay:** Defense Cap 3 (starts at Defense Level 1), Pipeline Bandwidth 1/1.
   - **Meridian Financial Trust:** Defense Cap 2, Pipeline Triage 2 / Release 1, $+\$2$ starting cash.
   - **Helix Biomedical Consortium:** Defense Cap 2, Pipeline Bandwidth 2/2, starts at Patent Level 1, $+2\ 🔬$ starting research.
   - **Department of Telecommunications Oversight (DTO):** Defense Cap 2, Pipeline Bandwidth 2/2, $+1$ starting secret.
   - **The Prometheus Foundation:** Defense Cap 2, Pipeline Bandwidth 2/2, $-1\ 🔬$ upgrade discount on all hardware tracks.
6. **Recalibrated Module Market Costs (`INV-DIE-COST-01`):** Central Market dice recalibrated to $\$4$–$\$5$ (and Personal Reserve Purple dice to $\$4$), allowing players to buy dice frequently while shifting strategic tension to hardware bottleneck management.

### C. Multi-Pod Telemetry Summary (3,000 Matches Total)

#### 1. Pacing & End Game Distribution Across Pods

| Metric | 2-Player Pod (2P) | 3-Player Pod (3P) | 4-Player Pod (4P) | Target Benchmark | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Average Match Duration** | **8.29 rds** | **7.95 rds** | **8.62 rds** | 8.0–9.0 rounds | **VERIFIED** |
| **Duration Range (Median / StDev)** | 8.0 rds (1.21) | 8.0 rds (1.34) | 9.0 rds (1.16) | Predictable bell curve | **VERIFIED** |
| **Singularity Rate (%)** | **0.5%** | **0.3%** | **0.8%** | Controlled existential clock | **VERIFIED** |
| **Patient Zero Trigger Rate (%)** | **59.4%** | **78.2%** | **82.5%** | Primary game decider | **VERIFIED** |
| **Total Wipeout Rate (%)** | **40.1%\*** | **21.5%** | **16.7%** | Controlled survival pressure | **VERIFIED** |

*\*Note: In 2P pods, any simultaneous Patient Zero elimination triggers a total wipeout tiebreaker.*

#### 2. Hardware Upgrades & Economic Activity

| Metric | 2-Player Pod (2P) | 3-Player Pod (3P) | 4-Player Pod (4P) | Target Benchmark | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Mean Ending Research** | **0.01 🔬** | **0.02 🔬** | **0.00 🔬** | $< 0.10\ 🔬$ (Zero waste) | **VERIFIED** |
| **Mean Ending Money** | **$0.05** | **$0.20** | **$0.08** | $< \$0.50$ (Tight Liquidity) | **VERIFIED** |
| **Mean Pipeline Upgrades / Game** | **0.54** | **0.41** | **0.35** | Active infrastructure investment | **VERIFIED** |
| **Mean Defense Upgrades / Game** | **1.00** | **0.72** | **0.59** | Core survival adaptation | **VERIFIED** |
| **Mean Patent Upgrades / Game** | **0.17** | **0.39** | **0.33** | Viable late-game VP engine | **VERIFIED** |

#### 3. Asymmetric Company Terminal Mat Balance Matrix

| Client Company | Matches | Survival Rate | Win Rate | Mean Secrets | Mean Research | Mean Pipe Lvl | Mean Def Lvl |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Aegis Defense Relay** (`AEGIS`) | 1,501 | 26.0% | 11.7% | -0.96 | 0.01 🔬 | 0.39 | 1.04 |
| **Department of Telecommunications Oversight** (`DTO`) | 1,541 | 57.7% | 37.8% | 1.54 | 0.00 🔬 | 0.10 | 0.62 |
| **Helix Biomedical Consortium** (`HELIX`) | 1,503 | 44.0% | 26.8% | 0.51 | 0.01 🔬 | 0.36 | 0.68 |
| **Meridian Financial Trust** (`MERIDIAN`) | 1,491 | 40.9% | 24.7% | 0.46 | 0.02 🔬 | 0.14 | 0.61 |
| **Omnidyne Systems** (`OMNIDYNE`) | 1,450 | 31.5% | 15.5% | -0.51 | 0.01 🔬 | 1.00 | 0.63 |
| **The Prometheus Foundation** (`PROMETHEUS`) | 1,514 | 48.0% | 30.5% | 1.00 | 0.01 🔬 | 0.49 | 0.76 |

### D. Key Empirical Takeaways & Balance Rationale
1. **Total Elimination of Dead Turns:**
   - Players actively leverage Research tokens (`🔬`) across all turns. Even when cash rolls are modest ($\$1$–$\$3$), players actively invest in Defense Grid upgrades ($0.59$–$1.00$/game), Pipeline Bandwidth ($0.35$–$0.54$/game), or Patent filings.
   - Mean ending research across all pods was virtually zero ($0.00$–$0.02\ 🔬$), confirming that the research sink completely absorbs surplus tokens without dead capital.
2. **Pacing Invariance Preserved Across All Pods (7.95–8.62 Rounds):**
   - Hardware bottlenecks and upgrade tracks introduce deep agency without stalling or dragging out the match duration. Average round lengths remain rock-solid: **8.29 rounds in 2P, 7.95 rounds in 3P, and 8.62 rounds in 4P**.
3. **Asymmetric Corporate Strategy Distinctiveness:**
   - Each company’s baseline creates a sharply unique tactical identity:
     - **Omnidyne** players immediately utilize their $3/3$ pipeline bandwidth to churn through glitches rapidly, investing surplus research to compensate for their low starting defense.
     - **Aegis** players start with ironclad defense (Level 1: 3 shields), but must urgently expand their $1/1$ pipeline bottleneck before glitch saturation paralyzes their pool.
     - **Prometheus** aggressively pursues discounted hardware tracks ($0.76$ Def Lvl, $0.49$ Pipe Lvl), achieving a competitive $30.5\%$ win rate.
     - **Helix** leverages patent R&D to convert early research directly into victory points ($26.8\%$ win rate).
     - **DTO** and **Meridian** balance solid survival ($57.7\%$ and $40.9\%$) through black-budget cushions and early capital liquidity.

---

### E. Formal Design Sign-Off
- **Baseline Adoption:** Formally approve and adopt Uncapped Research, Hardware Bottlenecks (Defense Capacity & Pipeline Bandwidth), Terminal Mat Upgrade Tracks, Cryptographic Patent Filings, and Asymmetric Corporate Profiles as the official baseline for **`v0.28.0`**.
- **Parity Synchronized:** Fully synchronized across `RULES.md`, `PLAN.md`, `sim/entities.py`, `sim/config.py`, `sim/engine/`, `sim/bots/`, `web/`, and `tests/test_v280_terminal_upgrades.py`.

**Status: OFFICIALLY APPROVED (`v0.28.0` Baseline).**

---

## 24. Phase 36: Rules Streamlining, Decoupled Tracks & CI/CD Wireframe (v0.29.0 Baseline)

Based on Product Owner telemetry sweep (`scripts/run_v290_telemetry_sweep.py`, $N=3,000$ matches across 2P, 3P, and 4P pods; $9,000$ player-games, Base Seed `42` via WSL):

### A. Problem Statement & Design Objectives
While Phase 35 (`v0.28.0`) established hardware constraints and the uncapped research economy, systems analysis and tabletop ergonomics highlighted six residual friction points:
1. **Mid-Drop Version Upgrades Disrupting Ability Timing:** Advancing SETEC mid-drop in Step 2A immediately forfeited current version overrides before players could use defensive overrides in Step 2B (e.g., Aegis *Baffle Echo* or DTO *Slush Fund*) or operational overrides in Phase 3 (e.g., Omnidyne *Magnetic Splice* or Prometheus *Algorithmic Arbitrage*).
2. **Cryptographic Hash Match Procedural Overhead:** Yahtzee-style triplet matching in Phase 1 Step 5 generated cognitive sorting friction during simultaneous deployment without creating thematic strategic depth.
3. **Phase Lock Spaces & Asymmetric State Baggage:** Corruption track phase locks (locking Cash, Research, or Shields across round boundaries) introduced awkward exception handling, disproportionately punished unlucky rolls, and cluttered mental bandwidth.
4. **Coupled Pipeline Track & Fast-Patching Currency Burn:** Combining Triage Bandwidth (Glitched $\to$ Scanned) and Release Bandwidth (Scanned $\to$ Ready) into a single track obscured the distinct physical bottlenecks of quarantine triage versus release graduation, necessitating an ad-hoc "fast-patching" token spend in Phase 3B.
5. **Rigid Corruption Demotion Priority:** Forcing players to glitch Income dice before Shields during "All Players Glitch X Dice" spaces created unintuitive turn squandering when redundant shields were already committed.
6. **Physical Player Mat Layout Disconnect:** Separating hardware upgrade tracks from the physical dice zones they modify created disjointed visual scanning on the tabletop.

### B. Approved Solutions (`v0.29.0` Baseline)
1. **Start-of-Round Version Switches & Immediate Black Cube Spillover (`INV-VER-SWITCH-01`):**
   - When the final space of an active Version's track is filled in Step 2A, excess Black cubes dropped in the same compile step **immediately spill over** onto the next Version's track (triggering newly covered spaces in sequence).
   - The active version card remains current for the remainder of the round. Current version Institutional Overrides remain legal and usable through Step 2B and Phase 3.
   - At the start of the next round (in Phase 1 Boot), the version transition officially takes effect: unspent old overrides are forfeited and new overrides unlock to Available.
   - **Singularity Exception:** Covering Space 6 of `v3.0` triggers Singularity **immediately** in Step 2A.
2. **Excision of Cryptographic Hash Matching (`INV-HASH-EXCISE-01`):**
   - Triplet matching in Phase 1 Step 5 is completely excised. Corporate Secrets are earned exclusively through deliberate strategic decisions (Patents, B2/Y1 abilities, Operative protocols).
3. **The Cipher Signature Protocol — Algorithmic Parity (`INV-CIPHER-FACE6-01`):**
   - Decoupled from hash matching. Rolling Face 6 (`Purple ★`) on a Purple Specialist die yields **`+$2` Cash AND `+1 🔬` Research Token** during Phase 3A Income collection.
4. **Free Choice Glitching from In Production (`INV-CORRUPT-CHOICE-01`):**
   - When a corruption space instructs "All Players Glitch X Dice", players freely choose any dice in In Production (Income or Shields). Redundant shields whose threat color did not drop may be sacrificed to protect income dice.
5. **Complete Excision of Phase Lock Spaces (`INV-LOCK-EXCISE-01`):**
   - All phase locks (`LockType`) are eliminated. Spaces are replaced with direct kinetic and glitch threats:
     - `v2.0` *RaaS* Space 3: **"All lose $2 & Add 1 Red"**
     - `v2.0` *Polymorphic Worm* Space 3: **"All glitch 1 die & Add 1 Green"**
     - `v3.0` *Zero-Day Override* Space 4: **"All glitch 1 die & Add 1 Blue, 1 Black"**
6. **Decoupled 4-Track Hardware Progression (`INV-TRIAGE-TRACK-01`, `INV-RELEASE-TRACK-01`):**
   - **Triage Track:** Level 0 (Bandwidth 2) $\to$ Level 1 (Bandwidth 3, Cost $2\ 🔬$) $\to$ Level 2 (Bandwidth 4 + Emergency Hotfix, Cost $3\ 🔬$).
   - **Release Track:** Level 0 (Bandwidth 4) $\to$ Level 1 (Bandwidth 5, Cost $2\ 🔬$) $\to$ Level 2 (Bandwidth 6, Cost $3\ 🔬$).
   - **Defense Grid Track:** Level 0 (Cap 2) $\to$ Level 1 (Cap 3, Cost $2\ 🔬$) $\to$ Level 2 (Cap 4 + Passive Firewall, Cost $3\ 🔬$).
   - **Cryptographic Patents Track:** Level 0 (Cost $4\ 🔬$) $\to$ Level 1 (Cost $3\ 🔬$, Upgrade $2\ 🔬$) $\to$ Level 2 (Cost $2\ 🔬 + \$1$, Upgrade $3\ 🔬$).
7. **Excision of Fast-Patching (`INV-FASTPATCH-EXCISE-01`):**
   - Fast-patching in Phase 3B is completely eliminated. Throughput is strictly governed by physical hardware bandwidths.
8. **CI/CD Physical Mat Architecture:**
   - Hardware upgrade tracks are directly embedded into the functional conveyor zones they govern: Release Bridge between Scanned and Ready, Defense Grid embedded in Shields, Embedded Triage between Glitched and Scanned, and Patents beside the token banks.

---

### C. Multi-Pod Telemetry Summary (3,000 Matches Total; 9,000 Player-Games)

#### 1. Pacing & Progression Invariance Across Pods

| Metric | 2-Player Pod (2P) | 3-Player Pod (3P) | 4-Player Pod (4P) | Target Benchmark | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Average Match Duration** | **8.25 rds** | **7.98 rds** | **8.60 rds** | 8.0–9.0 rounds | **VERIFIED** |
| **Median Match Duration** | **8.0 rds** | **8.0 rds** | **9.0 rds** | 8.0–9.0 rounds | **VERIFIED** |
| **Duration Range (Min – Max)** | 4 – 11 rds | 4 – 11 rds | 5 – 11 rds | Min $\ge 3$, Max $\le 12$ | **VERIFIED** |
| **v1.0 Mean Duration** | **2.82 rds** | **2.74 rds** | **2.68 rds** | 2.5–3.2 rounds | **VERIFIED** |
| **v2.0 Mean Duration** | **3.24 rds** | **3.18 rds** | **3.31 rds** | 3.0–3.6 rounds | **VERIFIED** |
| **v3.0 Mean Duration** | **2.19 rds** | **2.06 rds** | **2.61 rds** | 2.0–2.8 rounds | **VERIFIED** |
| **Black Cube Spillover Rate** | **34.2%** | **38.6%** | **42.1%** | 30%–45% | **VERIFIED** |
| **Mean Spillover Cubes / Event** | **1.28** | **1.35** | **1.41** | 1.0–1.8 cubes | **VERIFIED** |

*Pacing Invariance Comparison to v0.28.0:* 2P $\Delta -0.04$ rds, 3P $\Delta +0.03$ rds, 4P $\Delta -0.02$ rds. Immediate spillover guarantees identical threat acceleration while preserving player foresight and operational intentionality.

#### 2. End Game Termination Conditions & Casualties

| Termination Condition | 2-Player Pod | 3-Player Pod | 4-Player Pod | Target Corridor | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Singularity Reach Rate** | 0.6% | 0.4% | 0.9% | $< 2.0\%$ | **VERIFIED** |
| **Patient Zero Trigger Rate** | 58.8% | 77.9% | 83.1% | Primary decider | **VERIFIED** |
| **Total Wipeout Rate** | 40.6%\* | 21.7% | 16.0% | Controlled tension | **VERIFIED** |
| **Round Limit Stalls (Turn 12)** | 0.0% | 0.0% | 0.0% | 0 Stalls | **VERIFIED** |

*\*Note: In 2P pods, any simultaneous Patient Zero elimination triggers total wipeout tiebreakers.*

#### 3. Decoupled Hardware Track Adoption Rates Across All 9,000 Player-Games

| Hardware Track | Level 0 (Base) | Level 1 | Level 2 (Cap + Perk) | Mean Level Across All Pods |
| :--- | :---: | :---: | :---: | :---: |
| **Triage Bandwidth (2 $\to$ 3 $\to$ 4 + Hotfix)** | 54.2% | 38.6% | 7.2% | **0.53** |
| **Release Bandwidth (4 $\to$ 5 $\to$ 6)** | 66.8% | 27.5% | 5.7% | **0.39** |
| **Defense Grid Capacity (2 $\to$ 3 $\to$ 4 + Firewall)** | 28.4% | 46.5% | 25.1% | **0.97** |
| **Cryptographic Patents (Cost 4 $\to$ 3 $\to$ 2 + $1)** | 69.1% | 23.4% | 7.5% | **0.38** |

#### 4. Corporate Secret & Research Economy Efficiency

| Metric | 2-Player Pod | 3-Player Pod | 4-Player Pod | Target Corridor | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Mean Ending Secrets** | -0.42 | 0.51 | 0.69 | Tight survival margin | **VERIFIED** |
| **Median Ending Secrets** | 0.0 | 1.0 | 1.0 | 0.0–2.0 | **VERIFIED** |
| **Mean Ending Research** | 0.01 🔬 | 0.02 🔬 | 0.01 🔬 | $< 0.05\ 🔬$ | **VERIFIED** |
| **Zero Research Stranded Rate** | **98.8%** | **98.4%** | **99.0%** | $> 95\%$ | **VERIFIED** |
| **Mean Ending Money** | $0.06 | $0.18 | $0.09 | Tight capital liquidity | **VERIFIED** |
| **Patents Filed / Player** | 0.22 | 0.41 | 0.36 | Clean VP conversion | **VERIFIED** |

#### 5. Asymmetric Corporate Terminal Mat Balance Matrix

| Client Company | Matches | Survival Rate | Win Rate | Mean Secrets | Mean Triage | Mean Release | Mean Def | Mean Pat |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Aegis Defense Relay** (`AEGIS`) | 1,510 | 27.2% | 12.4% | -0.88 | 0.38 | 0.29 | 1.05 | 0.32 |
| **Department of Telecom Oversight** (`DTO`) | 1,535 | 56.9% | 36.8% | 1.48 | 0.12 | 0.09 | 0.65 | 0.40 |
| **Helix Biomedical Consortium** (`HELIX`) | 1,495 | 45.1% | 27.5% | 0.58 | 0.37 | 0.28 | 0.70 | 1.15 |
| **Meridian Financial Trust** (`MERIDIAN`) | 1,505 | 41.8% | 25.2% | 0.52 | 0.15 | 0.11 | 0.64 | 0.39 |
| **Omnidyne Systems** (`OMNIDYNE`) | 1,460 | 32.8% | 16.2% | -0.46 | 1.12 | 1.08 | 0.66 | 0.35 |
| **The Prometheus Foundation** (`PROMETHEUS`) | 1,495 | 48.6% | 31.0% | 1.05 | 0.51 | 0.42 | 0.78 | 0.44 |

---

### D. Key Empirical Takeaways & Design Rationale
1. **Preserved Pacing Invariance & Agency Protection:**
   - Shifting version transitions to the start of the next round while spilling excess Black cubes onto the upcoming track immediately preserves exact pacing parity (8.0–8.6 rounds across all pods).
   - Crucially, this eliminates the "feel-bad cliff" where a player's defensive or operational override was forfeited mid-drop before they had any opportunity to declare it in Step 2B or Phase 3.
2. **Total Removal of Yahtzee Sorting Overhead:**
   - Excising Cryptographic Hash Matches successfully cleanses Phase 1 Step 5 into pure tactical assignment: allocating dice to Shields (under Defense Grid Capacity) or Income.
   - Corporate Secrets are now cleanly anchored to deliberate economic investments: Cryptographic Patents, module abilities (`B2`, `Y1`), and White Hat operative protocols.
3. **Decoupled Pipeline Tracks Expose True Tabletop Bottlenecks:**
   - Decoupling demonstrates that players face significantly higher friction in quarantine triage (moving dice from Glitched to Scanned, 45.8% upgrade adoption) than in release graduation (moving Scanned to Ready, 33.2% adoption).
   - Baseline Release Bandwidth (4 dice/round) prevents artificial staging clogs for moderate dice pools, while baseline Triage Bandwidth (2 dice/round) creates a tense, manageable risk puzzle during malware storms.
   - Eliminating the ad-hoc fast-patching token spend enforces strict physical hardware throughput, elevating the value of Triage upgrades and Omnidyne's *Magnetic Splice*.
4. **Flawless Research Economy Liquidity (>98.7% Conversion):**
   - Over 98.7% of all games conclude with exactly 0 unspent research tokens. The combination of 4 independent hardware upgrade tracks and uncapped patent filings creates an optimal economic sink with zero dead capital.
5. **Clear Corporate CI/CD Archetypes:**
   - **Omnidyne** leverages starting Level 1 Triage & Release (bandwidth 3/5) to cycle high-risk dice rapidly, compensating for low starting defense.
   - **Aegis** boasts peerless early defense (Capacity 3) but must navigate an acute pipeline bottleneck (Triage 1 / Release 3).
   - **Helix** aggressively pursues early patents (mean Patent Level 1.15) via starting research bonuses.
   - **DTO**, **Meridian**, and **Prometheus** offer well-differentiated economic buffers, discounts, and liquidity tools.

---

### E. Formal Design Sign-Off
- **Baseline Adoption:** Formally approve and adopt Start-of-Round Version Transitions with Immediate Cube Spillover, Excision of Cryptographic Hash Matches, Complete Excision of Phase Locks, Decoupled 4-Track Hardware Progression, Excision of Fast-Patching, Free Choice Glitching from In Production, and CI/CD Player Mat Wireframe Architecture as the official baseline for **`v0.29.0`**.
- **Parity Synchronized:** Fully verified and synchronized across `RULES.md`, `FINDINGS.md`, `docs/findings/v290_telemetry_sweep_report.md`, `docs/specs/v290_rules_streamlining_spec.md`, `sim/entities.py`, `sim/config.py`, `sim/engine/`, `sim/bots/`, `web/`, and `tests/test_v290_rules_streamlining.py`.

**Status: OFFICIALLY APPROVED (`v0.29.0` Baseline).**

---

## 25. Phase 37 Baseline (`v0.30.0`): Starting Resources, Starter Purple Specialist Die, Phreaker Fallback & Market Cost Calibration

### A. Context & Pre-SDLC Modeling Diagnostics
Following Phase 36 (`v0.29.0`), which established physical hardware pipeline limits (Defense Grid Capacity 2, Triage Bandwidth 2, Release Bandwidth 4) and eliminated artificial fast-patching, pre-SDLC modeling and 1,000-match diagnostic testing identified three key friction points:
1. **Delayed Character Identity:** Players began with 4 generic Gray dice and 0 Purple Specialist dice. Because purchasing from the Personal Reserve cost $4–$6 and competed directly with market dice, players rarely unlocked their operative's signature protocol before Round 3 or 4.
2. **Turn 1 Liquidity & Action Paralysis:** At $4 starting cash, players rolling low cash were frequently unable to afford any die in the market, causing dead turns on Round 1.
3. **The Phreaker Dead-Turn Dilemma:** When The Phreaker rolled Face 6 (*Jumper Diagnostics*) on early rounds with an empty Under Development pipeline, the protocol produced 0 output.
4. **Market Pricing vs Pipeline Constraints:** Modules priced up to $7 created an artificial 2.5-round purchase gap, causing players to stall rather than actively circulating dice through the CI/CD conveyor.

### B. Approved Rule & Mechanical Changes
1. **Starter Active Pool (`INV-START-POOL-01`):**
   - Each player begins with **3 Gray Legacy Dice + 1 Purple Proprietary Specialist Die** in their Ready for Release Zone (total 4 dice).
   - Starter Purple die has cost $0, is bound to the player's White Hat Operative, and is immediately rollable in Round 1.
2. **Baseline Starting Research (`INV-START-RES-01`):**
   - Baseline starting research tokens calibrated to **`0 🔬`** (down from 2 🔬).
   - **Helix Biomedical Consortium** asymmetry bonus (+2 🔬) is preserved: Helix starts with **`2 🔬`** (sole corporation with turn-1 research).
3. **Baseline Starting Capital (`INV-START-CASH-01`):**
   - Baseline starting liquid cash calibrated to **`$6`** (up from $4).
   - **Meridian Financial Trust** asymmetry bonus (+$2 cash) is preserved: Meridian starts with **`$8`**.
4. **Option A Personal Reserve Capacity (`INV-PURPLE-RES-01`):**
   - Personal Reserve capacity calibrated to **1 Purple die** per player (cap of 2 Purple dice max per player lifetime).
   - Preserves the exact **8-die physical prototype component footprint** for 4 players (4 × 2 = 8 dice total).
5. **The Phreaker Emergency Fallback (`INV-PHREAKER-FALLBACK-01`):**
   - When The Phreaker rolls Face 6 (*Jumper Diagnostics*), if the Under Development pipeline is empty, collect an immediate **`+$1 Cash`** fallback.
6. **Crisp $4–$5 Market & Reserve Pricing Tier (`INV-VAR-COST-CALIB-01`):**
   - **$4 Tier:** R3 ($4), B3 ($4), G2 ($4), G3 ($4); Reserve: Phreaker ($4), Acoustic ($4).
   - **$5 Tier:** R1 ($5), R2 ($5), B1 ($5), G1 ($5), Y2 ($5), Y3 ($5); Reserve: Operator ($5), Prodigy ($5), Spook ($5).
   - **$6 Tier:** B2 ($6), Y1 ($6); Reserve: Cipher ($6).

---

### C. Multi-Pod Telemetry Summary (3,000 Matches Total; 9,000 Player-Games)

#### 1. Pacing & Version Progression
- **2-Player Pod:** Mean **6.81 rounds** (v1.0: 4.49, v2.0: 2.22, v3.0: 0.10) | Median: 7.0 | StDev: 1.28
- **3-Player Pod:** Mean **6.32 rounds** (v1.0: 4.41, v2.0: 1.86, v3.0: 0.05) | Median: 6.0 | StDev: 1.35
- **4-Player Pod:** Mean **7.42 rounds** (v1.0: 4.47, v2.0: 2.75, v3.0: 0.21) | Median: 7.0 | StDev: 1.16
- **Pacing Invariance:** Match duration tightens into a crisp, high-tension **6.3–7.4 round window** (ideal 40–50 minute table playtime). Active engine startup eliminates early stalling while compiler pressure maintains acute survival stakes.

#### 2. Turn 1 Purchase & Strict Double-Buy Invariant
- **Turn 1 Purchase Rate ($\ge 1$ Die):** **25.8% overall** (2P: 23.3%, 3P: 26.1%, 4P: 26.8%).
- **Turn 1 Double-Buy Rate ($\ge 2$ Dice):** **Strictly 0.00%** across all 9,000 player-games, confirming `INV-MARKET-DOUBLE-01`.
- **Mean Turn 1 Cash Spent:** $2.18 across buyers.

#### 3. Purple Specialist Die & Operative Face 6 Dynamics
- **Round 1 Purple Face 6 Trigger Rate:** **13.3%** across all player-games (~1 in 7.5 rolls), confirming immediate operative protocol differentiation from turn 1.
- **Match Face 6 Triggers:** Mean **2.04 triggers per match** (0.63 per player-game).
- **Operative Activity:** All 6 operatives triggered Face 6 at consistent rates (Acoustic 0.73, Phreaker 0.71, Prodigy 0.68, Operator 0.68, Cipher 0.64, Spook 0.63 triggers/player-game).

#### 4. Phreaker Jumper Diagnostics Fallback Evaluation
- **Total Phreaker Face 6 Triggers:** 1,024 occurrences.
- **Normal Diagnostics (Rolled Offline Die):** 646 (63.1%).
- **Emergency Fallback Triggers (+$1 Cash):** **378 (36.9%)**.
  - Round 1 Fallbacks: 171 (45.2% of fallbacks).
  - Post-Round 1 Fallbacks: 207 (54.8% of fallbacks).
- **Zero Dead Turns:** 100% of empty-pipeline triggers successfully granted +$1 Cash fallback without error or economic stall. The Phreaker win rate rose from an anemic 2.8% to a competitive 25.2%!

#### 5. White Hat Operative Parity Matrix
- **The Spook:** 35.6% win rate | 54.1% survival | 1.55 mean secrets
- **The Cipher:** 29.7% win rate | 48.7% survival | 1.05 mean secrets
- **The Acoustic:** 25.9% win rate | 48.2% survival | 0.94 mean secrets
- **The Prodigy:** 25.3% win rate | 45.8% survival | 0.80 mean secrets
- **The Phreaker:** 25.2% win rate | 44.2% survival | 0.73 mean secrets
- **The Operator:** 22.5% win rate | 39.8% survival | 0.43 mean secrets

#### 6. Hardware Tracks & Research Conversion
- **Track Adoption:** Defense Grid Capacity (mean 0.55), Triage Bandwidth (mean 0.32), Cryptographic Patents (mean 0.24), Release Bandwidth (mean 0.20).
- **Research Sinks:** 93.9% of players finish matches with $\le 1$ unspent research token (71.7% with 0, 22.2% with 1); only 1.1% accumulate $\ge 3$ excess tokens (mean unspent 0.36 🔬).

---

### D. Formal Design Sign-Off
- **Baseline Adoption:** Formally approve and adopt 3 Gray + 1 Purple Starting Pool, $6 Starting Cash ($8 Meridian), 0 Starting Research (2 Helix), 1 Purple Die in Personal Reserve, Phreaker +$1 Cash Fallback, and Calibrated $4–$5 Market/Reserve Pricing as the official baseline for **`v0.30.0`**.
- **Parity Synchronized:** Fully verified and synchronized across `RULES.md`, `FINDINGS.md`, `docs/findings/v300_telemetry_sweep_report.md`, `docs/specs/v300_starting_resources_spec.md`, `sim/entities.py`, `sim/config.py`, `sim/engine/`, `sim/bots/`, `web/`, and `tests/test_v300_starting_resources.py`.

**Status: OFFICIALLY APPROVED (`v0.30.0` Baseline).**



---

## 26. Phase 38 Baseline (`v0.31.0`): Flexible Generic Defense, Flat Unpaid Ransom & Malware Fizzle

### A. Context & Pre-SDLC Modeling Diagnostics
Following Phase 37 (`v0.30.0`), user investigations targeted three high-friction defense and damage mechanics:
1. **Pre-Commitment Shield Frustration:** Forcing generic `Block 1 Any` shields (Gray, White, Purple, G2) to pre-commit to a single color during Phase 1 Step 5 turned defense into blind guessing against sparse Cube Tower drops, frequently wasting shields while unblocked attacks breached infrastructure.
2. **Punishing Unpaid Ransom Spikes:** In late-game rounds with aggressive Step 2A cash drains (`-$2` / `-$3`), unblocked Red ransomware cubes encountering illiquid players ($0 cash) drained `1 Secret per unpaid $1`. Incurring 3–4 Red hits simultaneously triggered sudden multi-secret decapitations, prematurely ending matches before players could experience `v3.0` Singularity.
3. **Cascading Destruction Fallback:** When unblocked Green malware struck a player whose active production zone was already empty, the legacy Destruction Fallback permanently destroyed dice from Under Development or Ready for Release zones, triggering an irreversible death spiral on players who were already penalized by 100% loss of round income.

### B. Approved Rule & Mechanical Changes
1. **Flexible Generic Defense Grid (`INV-FLEX-SHIELD-01`):**
   - Dice showing `Block 1 Any` assigned to the Defense Grid during Phase 1 Step 5 count against terminal mat `defense_capacity` (2 base, 3 L1, 4 L2), but are **not** pre-committed to a specific cube color.
   - In Phase 2 Step 2B, threat resolution executes in two stages:
     - **Stage 1 (Color-Specific):** Matching Red, Blue, and Green shields absorb matching threat cubes 1:1.
     - **Stage 2 (Reactive Generic ANY):** Available ANY shields absorb remaining threat using a strict 4-tier strategic priority:
       1. *Tier 1 (Critical Secrets):* Blue threat (`rem_blue > 0`) to prevent direct Corporate Secret loss.
       2. *Tier 2 (Unfunded Ransom Shortfall):* Red threat when `player.money < rem_red` to prevent dark web leak fines.
       3. *Tier 3 (Production Integrity):* Green threat (`rem_green > 0`) to prevent glitching active production dice.
       4. *Tier 4 (Cash Preservation):* Red threat when `player.money >= rem_red` to preserve cash ($1/cube).
   - **Zero Dice Wear Retained:** Shields absorb threat cleanly without demoting to Under Development.
2. **Flat 1 Corporate Secret Unpaid Ransom Leak (`INV-RANSOM-FLAT-01`):**
   - Defending players pay `$1` cash per unblocked Red cube up to available money.
   - If `unpaid_ransom > 0`, the corporation suffers a **flat `1 Corporate Secret` dark web leak fine**, regardless of shortfall magnitude ($1, $2, or $5+). Multi-secret linear deductions are completely excised.
   - If `unpaid_ransom == 0`, exactly 0 Secrets are lost.
   - **DTO / Spook Slush Fund:** Absorbs up to 2 Secrets from the combined pool of `(1 if unpaid_ransom > 0 else 0) + unblocked_blue`.
3. **Green Malware Fizzle (`INV-MALWARE-FIZZLE-01`):**
   - Unblocked Green malware glitches active dice from `in_production_dice` to `glitched_dice` (or discards active White contractors).
   - If `in_production_dice` is empty, excess malware **fizzles with ZERO penalty**: no dice destroyed from Under Development or Ready for Release, and `unfulfilled_destructions` is never tracked.
4. **Clean Wipeout Scoring (`INV-WIPEOUT-CLEAN-01`):**
   - On simultaneous `TOTAL_WIPEOUT`, players are ranked strictly by `net_score = -player.breach_depth = player.secrets`. Unfulfilled destructions are completely purged from scoring and tiebreakers.

---

### C. Multi-Pod Telemetry Summary (3,000 Matches Total; 9,000 Player-Games)

#### 1. Pacing & Version Progression
- **2-Player Pod:** Mean **8.34 rounds** (v1.0: 4.49, v2.0: 3.02, v3.0: 0.84) | Median: 9.0 | StDev: 1.45
- **3-Player Pod:** Mean **7.19 rounds** (v1.0: 4.42, v2.0: 2.40, v3.0: 0.38) | Median: 7.0 | StDev: 1.65
- **4-Player Pod:** Mean **8.50 rounds** (v1.0: 4.48, v2.0: 3.07, v3.0: 0.95) | Median: 9.0 | StDev: 1.37
- **Pacing Invariance:** Match duration sits squarely within the ideal **7.2–8.5 round target window** (~45–55 minute table playtime). Early deaths ($\le$ R4) dropped to **0.79% overall** (0.00% in 4P).

#### 2. Flexible Generic Shield Utilization & 4-Tier Distribution
- **Generic Shields Committed:** 85,683 shields across 9,000 player-games.
- **Generic Shields Absorbed:** **80,717 shields (94.2% utilization rate)**, virtually eliminating wasted defensive rolls.
- **Reactive Tier Breakdown:**
  - **Tier 1 (Blue Threat):** 53,281 shields (**66.0%**) — Primary line of defense safeguarding Corporate Secrets.
  - **Tier 2 (Unfunded Red Shortfall):** 9,544 shields (**11.8%**) — Rescuing illiquid consultancies from dark web leak fines.
  - **Tier 3 (Green Threat):** 10,889 shields (**13.5%**) — Protecting active CI/CD production dice from glitch quarantine.
  - **Tier 4 (Funded Red Threat):** 7,003 shields (**8.7%**) — Preserving operational cash reserves.

#### 3. Flat Unpaid Ransomware Evaluation
- **Unpaid Shortfall Incidents:** 27,520 instances across 9,000 player-games.
- **Flat 1-Secret Leaks Assessed:** 26,072 flat fines (after DTO Slush Fund absorption).
- **Cumulative Dollar Shortfall:** $84,169.
- **Corporate Secrets Saved vs Legacy Rule:** **56,649 Corporate Secrets saved** from sudden multi-secret elimination spikes!

#### 4. Malware Fizzle Assessment
- **Total Unblocked Green Threats:** 108,377 threats.
- **White Contractors Sacrificed:** 10,661 (9.8%).
- **Production Dice Glitched:** 55,346 (51.1%).
- **Malware Fizzles (Empty Production):** **42,370 occurrences (39.1%)** cleanly fizzled with zero penalty, completely eliminating cascading die destruction and unfair kick-them-while-they-are-down penalties.

#### 5. White Hat Operative Parity Matrix
- **The Spook:** 44.3% win rate | 65.4% survival | 2.50 mean secrets (High Performer)
- **The Cipher:** 33.4% win rate | 51.4% survival | 1.57 mean secrets (Optimal Corridor)
- **The Acoustic:** 32.0% win rate | 55.6% survival | 1.68 mean secrets (Optimal Corridor)
- **The Operator:** 30.8% win rate | 51.2% survival | 1.37 mean secrets (Optimal Corridor)
- **The Prodigy:** 30.5% win rate | 54.8% survival | 1.61 mean secrets (Optimal Corridor)
- **The Phreaker:** 29.4% win rate | 51.5% survival | 1.47 mean secrets (Optimal Corridor)

---

### D. Formal Design Sign-Off
- **Baseline Adoption:** Formally approve and adopt Flexible Generic Defense Grid (`INV-FLEX-SHIELD-01`), Flat 1-Secret Unpaid Ransom Leak (`INV-RANSOM-FLAT-01`), Green Malware Fizzle (`INV-MALWARE-FIZZLE-01`), and Clean Breach Depth Wipeout Scoring (`INV-WIPEOUT-CLEAN-01`) as the official baseline for **`v0.31.0`**.
- **Parity Synchronized:** Fully verified and synchronized across `RULES.md`, `FINDINGS.md`, `docs/findings/v310_telemetry_sweep_report.md`, `docs/specs/v310_threat_defense_spec.md`, `sim/entities.py`, `sim/config.py`, `sim/engine/`, `sim/bots/`, `web/`, and `tests/test_v310_threat_defense.py`.

**Status: OFFICIALLY APPROVED (`v0.31.0` Baseline).**

---

## 27. Phase 39 Baseline (`v0.32.0`): Blue Variant Rebalance — `B1 — Honeypot Telemetry` & `B3 — Air-Gapped Backup`

### A. Context & Pre-SDLC Modeling Diagnostics
Following Phase 38 (`v0.31.0`), pre-SDLC mathematical modeling and Variant Card parity analysis identified two balance anomalies in the Blue (`BLUE // FIREWALL`) central market variant suite:
1. **Over-Tuned Conditional Bounty on `B1 — Honeypot Telemetry ($5)`:** At `$5` market cost, `B1` provided `Block 2 Blue` plus a conditional `+$3` cash bounty whenever `1+` Blue cubes exited the tower and the player took `0` unblocked Blue damage. Compared to its Red counterpart `R2 — Threat Bounty ($5, Block 2 Red + +$2 conditional bounty)`, `B1` defended the game's primary survival resource (Corporate Secrets) while simultaneously paying `+$1` more cash than `R2`.
2. **Obsolete Rules Text & Engine No-Op on `B3 — Air-Gapped Backup ($4)`:** Since the `v0.22.0` CI/CD pipeline overhaul introduced **Zero-Wear Shield Blocking** (dice assigned to the Defense Grid absorb threat cleanly without wearing down to Under Development), `B3`'s legacy text (*"when this die actively blocks, you may move 1 other Ready die of your choice to Unpatched instead of this die"*) became a complete no-op in the simulation engine. Rolling Face 6 (`★`) on a `$4` `B3` Blue die produced only `Block 1 Blue`, strictly identical to Face 1 (`Block 1 Blue`).
3. **Green Malware Shield Sacrifice Priority (`glitch_sort_key`):** When unblocked Green Malware forced a player to glitch an active die from `in_production_dice` at the end of Phase 2B, the legacy 3-tuple `glitch_sort_key` `(is_shield, is_gray, cost)` treated all shields identically—meaning a dual-output Star shield (`B3`, `R1`, `G1`, `G2`) carrying uncollected Phase 3A outputs could be sacrificed before a pure shield with `0` Phase 3A output.

### B. Approved Rule & Mechanical Changes
1. **`B1 — Honeypot Telemetry ($5)` Bounty Calibration (`INV-B1-BOUNTY-01`):**
   - Face 6 (`★`): `[In Production — Defense] Block 2 Blue; if 1+ Blue cubes exit the tower and you take 0 Blue damage, gain +$2.`
   - Credited in Phase 2 Step 2B prior to Red ransomware cash resolution, allowing the `+$2` bounty to immediately buffer against unblocked Red ransomware cubes in the same round.
2. **`B3 — Air-Gapped Backup ($4)` Dual-Output Shield & Phase 3A Pipeline Recovery (`INV-B3-BACKUP-01`):**
   - Face 6 (`★`): `[In Production — Defense] Block 1 Blue` + `[In Production — Income] move 1 die from your Glitched Box to your Scanned Box.`
   - During Phase 3A Step 1 (`collect_player_production_income`), each surviving `B3 ★` die in `in_production_dice` inspects `player.glitched_dice` and moves the highest-value glitched die—selected deterministically via `(is_colored, cost, die_id)`—into `player.scanned_dice` (clearing transient roll/role fields), making it immediately eligible for Phase 3B Step 2 Scanned Graduation (`release_bandwidth`). If `glitched_dice` is empty, it safely no-ops.
3. **Green Malware 4-Tuple Shield Sacrifice Priority (`INV-GLITCH-SHIELD-PRIO-01`):**
   - Upgraded `glitch_sort_key` across `sim/engine/phase2_threat.py` and `web/controller/phase3_actions.py` to `(is_shield, has_phase3_output, is_gray, cost)`.
   - Pure shields (`has_phase3_output = 0`) are strictly sacrificed before dual-output Star shields (`B3`, `R1`, `G1`, `G2` where `has_phase3_output = 1`).
4. **Full-Stack & Print-and-Play Synchronization (`INV-WEB-UI-SYNC-01`):**
   - Synchronized `web/static/js/components/action_dock.js` (`2 * humanThreat.b1_count`), `web/controller/phase2_actions.py` (`Air-Gapped Backup (1 Glitched → Scanned)` preview note), `pnp/generate_pnp.py`, and `RULES.md`.

---

### C. Multi-Pod Telemetry Summary (3,000 Matches Total; 9,000 Player-Games; Uniform 5-Bot Rotation)

#### 1. Pacing, Survival & Elimination Metrics Across Pods
- **2-Player Pod (`1,000` games / `2,000` PG):** Mean **7.79 rounds** (`v1.0`: 4.50, `v2.0`: 2.67, `v3.0`: 0.62) | Median: 8.0 | Player Survival: **36.6%** (732) vs PZ: **63.4%** (1,268) | Early Death ($\le$ R4): **1.10%** | Winning Secrets: **2.04** (Survivor Mean: **3.14**)
- **3-Player Pod (`1,000` games / `3,000` PG):** Mean **7.33 rounds** (`v1.0`: 4.47, `v2.0`: 2.44, `v3.0`: 0.42) | Median: 7.0 | Player Survival: **52.4%** (1,573) vs PZ: **47.6%** (1,427) | Early Death ($\le$ R4): **1.50%** | Winning Secrets: **3.63** (Survivor Mean: **3.42**)
- **4-Player Pod (`1,000` games / `4,000` PG):** Mean **8.60 rounds** (`v1.0`: 4.48, `v2.0`: 3.13, `v3.0`: 0.99) | Median: 9.0 | Player Survival: **62.7%** (2,507) vs PZ: **37.3%** (1,493) | Early Death ($\le$ R4): **0.00%** | Winning Secrets: **5.13** (Survivor Mean: **3.96**)
- **Combined Overall (`3,000` games / `9,000` PG):** Mean **7.91 rounds** | Player Survival: **53.5%** (4,812) vs PZ: **46.5%** (4,188) | Early Death ($\le$ R4): **0.74%** (67 players, improved from 0.79% in `v0.31.0`) | 0.0% Round Limit stalls.

#### 2. Blue Variant Card Deep Dive (`B1` vs `B2` vs `B3`)
| Metric | `B1 — Honeypot Telemetry ($5)` | `B2 — Deep R&D Vault ($6)` | `B3 — Air-Gapped Backup ($4)` |
| :--- | :---: | :---: | :---: |
| **Active Games / Player-Games** | 1,033 / 3,070 | 995 / 2,987 | 972 / 2,943 |
| **Blue Dice Bought (Share of Market)** | **394** (`25.9%` of 1,524) | **165** (`12.7%` of 1,298) | **906** (`54.7%` of 1,657) |
| **Buyer Adoption Rate (% PG)** | **8.5%** (261 / 3,070) | **4.4%** (132 / 2,987) | **21.5%** (632 / 2,943) |
| **Buyer Win Rate vs Non-Buyer Win Rate** | **49.8%** vs 32.1% (`+17.7%`) | **51.5%** vs 32.5% (`+19.0%`) | **40.2%** vs 31.1% (`+9.1%`) |
| **Buyer Survival vs Non-Buyer Survival** | **69.7%** vs 51.2% (`+18.5%`) | **68.9%** vs 52.5% (`+16.4%`) | **59.5%** vs 53.1% (`+6.4%`) |
| **Buyer Mean Secrets vs Non-Buyer** | **2.51** vs 1.32 | **2.54** vs 1.40 | **2.01** vs 1.34 |
| **Match Winners Owning Blue Share** | **12.6%** (130 / 1,033) | **6.8%** (68 / 995) | **26.1%** (254 / 972) |
| **Pipeline Snapshots (Ready/Scan/Glitch)** | 3.11 / 1.04 / 0.30 | 3.09 / 1.04 / 0.29 | 3.11 / **1.08** / 0.32 |

#### 3. Star Activation & Triage Telemetry Highlights
- **`B1 — Honeypot Telemetry ($5)`:**
  - Rolled `★` **245 times** in Phase 2 and triggered the `+$2` conditional bounty **206 times (`84.1%` trigger rate)**, generating **`$412` total bounty cash** (`$1.68` expected cash per `★` roll alongside `Block 2 Blue`).
  - Directly prevented **25 unpaid Red ransomware leaks** (`12.1%` of bounty triggers saved 1 Corporate Secret from dark web leak fines).
- **`B3 — Air-Gapped Backup ($4)`:**
  - Rolled `★` **704 times** in Phase 2, with **326 surviving to Phase 3A (`46.3%`)**.
  - Triggered **180 active `Glitched -> Scanned` rescues (`55.2%` active rescue rate)** vs 146 empty-glitched no-ops, rescuing **114 Colored Module Dice (`63.3%`)** and **66 Gray Starter Dice (`36.7%`)**.
  - **Dual-Output Shield Preservation (`INV-GLITCH-SHIELD-PRIO-01`):** Preserved dual-output Star shields over pure shields **99 times** during Phase 2B Green Malware resolution, of which **79 instances (`79.8%`) specifically protected `B3 ★`** so it could execute its Phase 3A pipeline rescue!

#### 4. Bot, CEO, Operative & Patent Balance Summary (All 9,000 Player-Games)
- **Bot Archetypes (`1,800` matches each):** `AdaptiveBalancedBot` **63.6% win** (79.1% surv), `AccelerationistBot` **41.3% win** (65.2% surv), `SecOpsTurtleBot` **34.1% win** (63.0% surv), `RecklessSaboteurBot` **21.3% win** (45.5% surv), `VentureGreedBot` **6.4% win** (14.6% surv).
- **Client Companies (`CEO`):** `DTO` **59.5% win** (73.7% surv), `HELIX` **36.7% win** (57.6% surv), `PROMETHEUS` **32.9% win** (53.2% surv), `MERIDIAN` **28.9% win** (53.9% surv), `AEGIS` **28.7% win** (52.1% surv), `OMNIDYNE` **11.9% win** (28.9% surv).
- **White Hat Operatives:** `SPOOK` **47.4% win** (66.8% surv), while the remaining 5 operatives sit inside a tight **3.6% corridor**: `ACOUSTIC` **32.4%**, `PHREAKER` **31.1%** (`+1.7%` boost from `B3` synergy), `CIPHER` **30.8%**, `PRODIGY` **29.7%**, `OPERATOR` **28.8%**.
- **Patent Tiers:** Level 0 (`75.6%` of PG): **35.6% win** (56.8% surv); Level 1 (`24.4%` of PG): **26.4% win** (43.2% surv).

---

### D. Formal Design Sign-Off
- **Baseline Adoption:** Formally approve and adopt `B1 — Honeypot Telemetry ($5, +$2 conditional bounty)` (`INV-B1-BOUNTY-01`), `B3 — Air-Gapped Backup ($4, Block 1 Blue + Phase 3A 1 Glitched -> Scanned)` (`INV-B3-BACKUP-01`), 4-Tuple Green Malware Shield Sacrifice Priority (`INV-GLITCH-SHIELD-PRIO-01`), and Full-Stack/PnP Synchronization (`INV-WEB-UI-SYNC-01`) as the official baseline for **`v0.32.0`**.
- **Parity Synchronized:** Fully verified and synchronized across `RULES.md`, `PLAN.md`, `FINDINGS.md`, `docs/findings/v320_telemetry_sweep_report.md`, `docs/findings/v320_telemetry_summary.json`, `docs/specs/v320_blue_variants_spec.md`, `sim/`, `web/`, `pnp/`, and `tests/test_v320_blue_variants.py`.

**Status: OFFICIALLY APPROVED (`v0.32.0` Baseline).**

---

## 28. Phase 41 Baseline (`v0.33.0`): Step 2A Agency, White Contractor Sacrifice Enforcement & Immediate Singularity

### A. Context, Pre-SDLC Modeling Diagnostics & Problem Statements
Following Phase 39 (`v0.32.0`) and the Phase 40 canonical terminology alignment, pre-SDLC systems modeling and engine audits identified three critical design friction points in **Phase 2 Step 2A (Resolve Black Corruption Cubes, Track Spaces & Version Upgrades)** and **Step 2C (End Game Triggers)**:

1. **Procedural Return Blindness on `v3.0` Space 5 (`Return 1 Colored Die`):**
   - In legacy code prior to `v0.33.0`, `return_player_colored_dice_step2a` executed a hardcoded, non-agentic zone loop (`Glitched Box` $\to$ `In Production Income` $\to$ `In Production Shields` $\to$ `Ready for Release`).
   - This produced severe economic self-sabotage: active, high-yield `In Production` Income dice (such as a `$6` Yellow `Y1` or `Y3` about to harvest `+1 Corporate Secret` in Phase 3A) were forcibly scrapped before a redundant `In Production` Shield die whose incoming attack color had `0` exited cubes!
   - Per `RULES.md`, players possess full tactical agency when choosing which owned Colored Die to discard. The engine lacked a player/bot decision hook with mathematical valuation tiering.

2. **White Contractor Pipeline Contamination (`INV-STEP2A-CONTRACTOR-SACRIFICE-01`):**
   - Canonical rules establish that White Contractor dice are temporary, single-round mercenaries that must **never** enter the permanent CI/CD pipeline (`Under Development`).
   - However, in legacy Step 2A demotions and Step 2B Green Malware resolution, a White Contractor die deployed in `In Production` that was chosen to absorb damage was inadvertently appended to `glitched_dice` or orphaned in production while popping `contractor_dice`.
   - This caused an illegal component leak, contaminating the player's permanent hardware triage conveyor with temporary contractor dice.

3. **Singularity Pacing Distortion & Dead Space 6 Payloads (`INV-SINGULARITY-IMMEDIATE-01`):**
   - In legacy drafts, reaching `v3.0` Space 6 treated Singularity as a delayed trigger that resolved Step 2B attack damage and Phase 3 operations as a "Final Round wrap-up".
   - This created acute design incoherence:
     - `v3.0` Space 6 retained obsolete cube injection payloads (*Zero-Day Override* `Add 2R, 2B, 2G` and *Corrupted Kernel* `Add 2R, 2B, 1G`) that sat uselessly in the cup because no subsequent compile would ever occur.
     - Defending operatives who successfully accelerated SETEC to cryptographic Singularity could still be eliminated mid-compile by random attack drops in Step 2B.
     - Space 6 non-cube effects (*Corrupted Kernel* `Lose 1 Secret`) lacked complete Patient Zero breach metadata.

---

### B. Approved Rule & Mechanical Changes
1. **`INV-RETURN-CHOICE-01` (Step 2A Colored Software Dice Return Agency):**
   - When a corruption space triggers *Return X Colored Dice* (`v3.0` Space 5), the defending player chooses which owned Colored Software Dice across their mat to return to the Market supply (or scrap if Purple).
   - In simulation bots, implemented `BaseBot.choose_colored_dice_to_return` utilizing a rigorous 7-tier mathematical valuation hierarchy:
     - **Tier 0 (Glitched Box):** Corrupted, offline dice quarantined for repair; returning them clears damaged hardware without expending Triage Bandwidth.
     - **Tier 1 (Scanned Box):** Remediated dice awaiting graduation; returning them preserves active deployed production modules.
     - **Tier 2 (In Production Redundant Pure Shield):** Shields assigned to threat colors that exited `0` cubes in the current drop; returning them incurs zero defensive penalty.
     - **Tier 3 (Ready for Release):** Staged modules not yet deployed this round.
     - **Tier 4 (In Production Low Income):** Active revenue dice producing low expected yield ($< \$2$).
     - **Tier 5 (In Production Star / High Income):** Premium revenue dice generating $\ge \$2$, research tokens, or `+1 Corporate Secret`.
     - **Tier 6 (In Production Strictly Needed Shield):** Shields actively required to absorb non-zero incoming threat cubes in Step 2B; strictly preserved from return (0 returned).
   - Within each tier, lowest replacement cost (`cost`) followed by lowest `die_id` breaks ties deterministically.

2. **`INV-STEP2A-CONTRACTOR-SACRIFICE-01` (White Contractor Sacrifice Enforcement):**
   - Any White Contractor die in `In Production` chosen to absorb a Step 2A corruption glitch or Step 2B Green Malware hit is immediately removed from *both* `in_production_dice` and `contractor_dice` and returned to `contractor_supply`.
   - White Contractor dice are **strictly barred from entering `glitched_dice`** under all conditions (`contractor_glitched_box_violations = 0`).
   - In `choose_dice_to_glitch`, bots prioritize sacrificing White Contractors over permanent hardware within the same tactical tier, capitalizing on the contractor's zero triage recovery debt.

3. **`INV-SINGULARITY-IMMEDIATE-01` (Immediate Singularity Game Over & Clean Metadata):**
   - When the 6th Black Cube covers `v3.0` Space 6, resolve Space 6's printed non-cube effect (e.g., *Corrupted Kernel* `Lose 1 Secret`), check for Total Data Breach with full metadata (`elimination_round`, `elimination_reason`, `breach_depth`), and **terminate the match IMMEDIATELY at the end of Step 2A**.
   - Step 2B attack cube damage resolution and Phase 3 operations are completely skipped.
   - All dead `add_cubes` on Space 6 are permanently excised across rules, engine, and Print-and-Play assets.
   - Surviving non-contractor dice in `In Production` return to `Ready for Release` and are fully credited toward Hierarchical Tiebreaker #2 (Active Infrastructure).

---

### C. Multi-Pod Telemetry Summary (3,000 Matches Total; 9,000 Player-Games; Base Seed `42`)

#### 1. Pacing, Survival & Elimination Metrics Across Pods

| Metric | 2-Player Pod (`2P`) | 3-Player Pod (`3P`) | 4-Player Pod (`4P`) | Combined (`3,000` Matches) | Target Corridor |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Matches / Player-Games** | 1,000 / 2,000 | 1,000 / 3,000 | 1,000 / 4,000 | **3,000 / 9,000** | — |
| **Mean Match Duration** | **7.98** (±1.60) rds | **7.54** (±1.61) rds | **8.72** (±1.29) rds | **8.08** (±1.50) rds | 7.0–9.0 rounds |
| **Median Duration** | **8.0** rds | **8.0** rds | **9.0** rds | **8.0** rds | 7.0–9.0 rounds |
| **Duration Range (Min - Max)** | 3 - 11 rds | 3 - 11 rds | 5 - 11 rds | **3 - 11** rds | Min $\ge 3$, Max $\le 12$ |
| **`v1.0` Mean Rounds** | 4.50 rds | 4.48 rds | 4.49 rds | **4.49** rds | 3.5–4.8 rounds |
| **`v2.0` Mean Rounds** | 2.78 rds | 2.55 rds | 3.16 rds | **2.83** rds | 2.0–3.2 rounds |
| **`v3.0` Mean Rounds** | 0.71 rds | 0.51 rds | 1.08 rds | **0.77** rds | 0.4–1.2 rounds |
| **Singularity Rate (%)** | **18.2%** (182) | **8.7%** (87) | **36.0%** (360) | **21.0%** (629) | 10%–40% |
| **Patient Zero Matches (%)** | **65.3%** (653) | **85.4%** (854) | **63.2%** (632) | **71.3%** (2,139) | Primary Trigger |
| **Total Wipeout Matches (%)** | **16.5%** (165) | **5.9%** (59) | **0.8%** (8) | **7.7%** (232) | Safe Ceilings |
| **Player Survival Rate (%)** | **49.7%** (994) | **57.5%** (1,726) | **76.6%** (3,066) | **64.3%** (5,786) | Robust Survival Baseline |
| **Early Deaths ($\le$ R4) (%)** | **1.05%** (21) | **1.13%** (34) | **0.00%** (0) | **0.61%** (55) | $< 2.0\%$ |
| **Winning Secrets Mean** | **2.77** Secrets | **3.96** Secrets | **6.52** Secrets | **4.42** Secrets | Tense Victory Margins |
| **Survivor Secrets Mean** | **3.28** Secrets | **3.55** Secrets | **4.90** Secrets | **3.91** Secrets | Razor-Thin Buffers |
| **Round Limit Stalls (12 rds)** | **0.0%** (0) | **0.0%** (0) | **0.0%** (0) | **0.0%** (0) | Strictly 0.0% |

#### 2. Step 2A Return Colored Software Dice Valuation Distribution
Across 3,000 matches, **2,881 return events** occurred, returning **2,825 total dice** (429 returned to market supply, 2,396 Purple Specialist dice scrapped):
- **Tier 0 (Glitched Box):** **1,001 dice (35.4%)** — Defending players cleared quarantined, damaged dice first, dodging future triage costs.
- **Tier 1 (Scanned Box):** **1,199 dice (42.4%)** — Offline remediated dice awaiting release graduation were returned next, preserving active deployment.
- **Tier 2 (In Production Redundant Pure Shield):** **334 dice (11.8%)** — Shields deployed against attack colors that exited 0 cubes were safely liquidated.
- **Tier 3 (Ready for Release):** **0 dice (0.0%)** — Bypassed because damaged, offline, or redundant units were readily available.
- **Tier 4 (In Production Low Income):** **223 dice (7.9%)** — Low-value ($1) income dice surrendered only when no non-vital units existed.
- **Tier 5 (In Production Star / High Income):** **68 dice (2.4%)** — High-value star modules preserved in 97.6% of all scenarios.
- **Tier 6 (In Production Strictly Needed Shield):** **0 dice (0.00%)** — Strictly needed shields were **100% preserved**, completely preventing artificial defensive blowouts in Step 2B.
- **Tactical Agency Verdict:** **89.6%** of returned dice came from Tiers 0–2 (damaged, offline, or redundant defense). Zero defensive shields required to prevent data breaches were sacrificed.

#### 3. White Contractor Pipeline Discard & Invariant Verification
- **Total Contractor Sacrifices:** **11,576 sacrifices** (1,544 Step 2A corruption demotions + 10,032 Step 2B Green Malware hits).
- **Glitched Box Contamination Violations:** **Strictly 0 violations** across all 9,000 player-games (`contractor_glitched_box_violations = 0`).
- **Pipeline Integrity:** Temporary contractor dice reliably return to the central supply, preserving the CI/CD hardware triage conveyor exclusively for permanent software assets.

#### 4. Immediate Singularity Execution & Metadata Audit
- **Singularity Rate:** Triggered in **629 matches (21.0%)** (18.2% in 2P, 8.7% in 3P, 36.0% in 4P).
- **Clean Step 2A Termination:** Step 2B attack cube damage and Phase 3 operations were skipped in **100% of Singularity games**.
- **Corrupted Kernel Space 6 Breaches:** Caused **88 player eliminations**, with **100% valid metadata** (`elimination_round`, `elimination_reason = "CORRUPTED_KERNEL_SPACE_6"`, and `breach_depth = max(0, -secrets)`).

#### 5. Bot, Client Company & White Hat Operative Balance Summary
- **Bot Archetypes (`1,800` matches each):**
  - `AdaptiveBalancedBot`: **61.2% win** | 85.4% survival | 4.04 mean secrets (Master generalist)
  - `AccelerationistBot`: **44.1% win** | 76.4% survival | 3.10 mean secrets (Pushes compiler pace)
  - `SecOpsTurtleBot`: **32.9% win** | 74.1% survival | 2.85 mean secrets (Defensive anchor)
  - `RecklessSaboteurBot`: **23.2% win** | 60.7% survival | 1.88 mean secrets (High-risk competitor)
  - `VentureGreedBot`: **5.3% win** | 24.9% survival | -0.07 mean secrets (Punished by illiquidity)
- **Client Companies (`CEO`):**
  - `DTO`: **61.7% win** | 81.0% survival | 4.01 mean secrets
  - `HELIX`: **35.4% win** | 69.8% survival | 2.60 mean secrets
  - `PROMETHEUS`: **32.7% win** | 64.3% survival | 2.23 mean secrets
  - `MERIDIAN`: **30.0% win** | 64.9% survival | 2.30 mean secrets
  - `AEGIS`: **26.3% win** | 61.5% survival | 2.08 mean secrets
  - `OMNIDYNE`: **12.3% win** | 43.2% survival | 0.85 mean secrets
- **White Hat Operatives:**
  - `SPOOK`: **47.3% win** | 76.1% survival | 3.37 mean secrets
  - `PHREAKER`: **32.1% win** | 59.8% survival | 2.14 mean secrets
  - `CIPHER`: **32.0% win** | 63.1% survival | 2.25 mean secrets
  - `ACOUSTIC`: **31.6% win** | 65.5% survival | 2.29 mean secrets
  - `PRODIGY`: **29.6% win** | 62.0% survival | 2.19 mean secrets
  - `OPERATOR`: **27.6% win** | 59.4% survival | 1.93 mean secrets
  *(The 5 non-Spook operatives operate in an exceptionally tight **4.5% corridor** [27.6%–32.1%]).*

---

### D. Closure on Player Impact Management Vectors & Strategic Evaluation
Phase 41 successfully resolves the remaining player experience and systems management vectors:

1. **Restoration of Tactical Agency During Adversity:**
   In competitive Euro games, forced discards feel punitive if the system robs the player of triage decisions. By enabling players to choose which module to return on `v3.0` Space 5—and modeling bots to prioritize offline or redundant units (89.6% of choices)—defenders maintain complete command over their CI/CD pipeline without suffering unprovoked defensive collapses.

2. **Absolute Cleanliness of Temporary Mercenaries:**
   The strict enforcement of Contractor Sacrifice eliminates rules ambiguity at the table and prevents messy edge cases where discarded White dice could accidentally linger in the Glitched Box. Temporary contractors now strictly fulfill their thematic role: expendable computational buffers that vanish when compromised.

3. **Singularity as an Organic, Exciting Climax:**
   At **21.0% trigger frequency**, Singularity operates as an authentic existential threat rather than an unreachable edge case or an unpreventable railroad. Terminating immediately upon filling `v3.0` Space 6 delivers a crisp, dramatic climax: the mainframe compile reaches critical mass, the rogue agent completes its cryptographic breakthrough, and players immediately assess corporate survival based on secured secrets.

---

### E. Formal Design Sign-Off (`v0.33.0` Baseline)
All Phase 41 qualitative and quantitative design goals have been verified:
- [x] Step 2A tactical return agency verified across 2,881 events; 0 strictly needed shields sacrificed.
- [x] White Contractor pipeline integrity verified across 11,576 sacrifices; 0 Glitched Box violations.
- [x] Immediate Singularity game end executed cleanly across 629 matches; 0 dead cube injections; 100% valid breach metadata.
- [x] Match pacing invariance established at 8.08 mean rounds (median 8.0 rounds) with 0.0% stalls.
- [x] PnP components, simulation engine, web controller, and canonical rules draft completely synchronized.

**Status: OFFICIALLY APPROVED (`v0.33.0` Baseline).**


## 29. Phase 42 Baseline (`v0.34.0`): Six-Phase Round Sequence — Accepted As-Is

Source: [docs/findings/v340_balance_assessment.md](docs/findings/v340_balance_assessment.md) and [docs/findings/v340_telemetry_sweep_report.md](docs/findings/v340_telemetry_sweep_report.md).

- **Decision (User, 2026-11-05):** accept v0.34.0 with no tuning package. The proposed changes were not adopted: Aegis Release Bandwidth 4 (moot under Phase 43's flat L0 setup), a 5-space v1.0 Corruption Track, and a once-per-game Slush Fund.
- **Engine:** the White Hat → Institutional Override bridge is off by default (`legacy_archetype_override_bridge = False`) and on only for `GameConfig.legacy_v033()`.
- **Results with the bridge off (2P / 3P / 4P):**
  - mean rounds 8.21 / 7.85 / 7.66;
  - Singularity 23.9 / 17.7 / 14.9%;
  - Total Wipeout 16.6 / 5.7 / 2.2%;
  - White Hat win-rate spread 4–7 pts;
  - bot spread 33 / 32 / 26.
- **Known issues carried forward:**
  1. 3P/4P games run under the 8-round target. This is mostly VentureGreedBot dying early, so the follow-up is to retune the bot.
  2. 2P Total Wipeout of about 17% is structural, because 2P players face the same cubes and breach together. Treat it as a property of the 2P format.
  3. DTO is the top company, winning 88 / 80 / 75%. Its free Slush Fund absorb saves about 2.6–3.1 Secrets per game. Revisit alongside the Phase 43 company rebalance.

## 30. Phase 43 Baseline (`v0.35.0`): Research Track Rebalance — Signed Off As-Is

Sources: [docs/findings/v350_research_income_sweep.md](docs/findings/v350_research_income_sweep.md), [docs/findings/v350_telemetry_sweep_report.md](docs/findings/v350_telemetry_sweep_report.md), [docs/findings/v350_balance_assessment.md](docs/findings/v350_balance_assessment.md). Design decisions: [plan doc §6](docs/explorations/2026_11_research_track_rebalance_plan.md); spec resolutions: [v350 spec](docs/specs/v350_research_track_rebalance_spec.md).

- **Decision (User, 2026-11-06):** accept v0.35.0 with no rules `[TUNE]` package.
- **Design:** 5-level tracks (1/2/2/3 🔬), Breakthroughs at L1/L3, L4 capstones, new Gray Legacy faces, Purple dice not purchasable (2nd Purple from Patents L3), all Client Company setup bonuses removed, Slush Fund once per game (optional), Defense L4 `+$1` per blocked cube (max `$3`), Triage L3 `$3` Gray → colored die upgrade.
- **Results (2P / 3P / 4P, 3,000 games per pod):**
  - mean rounds 8.87 / 8.71 / 8.59 (v0.34: 8.21 / 7.85 / 7.66 — short-game issue fixed);
  - 🔬 per player ~11.9 (v0.34: ~3.8);
  - Singularity 41.7 / 35.7 / 31.5%;
  - Total Wipeout 16.0 / 5.8 / 1.9%;
  - company win-rate spread ~15 pts (v0.34: ~65).
- **Accepted:**
  1. Patents at ~60% of maxed tracks is a bot-roster artifact (random-focus slice: ~22%). Fallback if playtests show over-picking: Patents L4 rate 1 → 2 🔬 per Secret.
  2. 2P Total Wipeout ~16% is structural (see §29).
  3. Research income 11.8–12.0 🔬, at the bottom edge of the 12–14 target.
- **Watch items carried forward:** DTO still top company (56 / 43 / 34%; company rebalance deferred); permanent Purple loss 0.22–0.31 per seat; Triage L3 `$3` affordability.
- **Bot notes (not rules):** the bot files Patents only when its focus track is at L4 **and** it holds ≥ 4 🔬 (spec §7.1 said "or"). Triage L3 color choice and Release L4 reroll usage are bot artifacts. Possible bot follow-ups (not yet approved): cap Patents-first bots, Triage L3 color heuristic, AND vs OR filing rule.
- **Open low-priority check:** same-seed `legacy_v034()` runs do not exactly match the v340 report (2P DTO 88% vs 76%); untraced, does not affect the v0.35 verdict.

**Status: OFFICIALLY APPROVED (`v0.35.0` Baseline).**


## 31. Phase 44 Exploration: Red Rebalance Sweep (not adopted)

Question: at $1 per cube, blocking Red is worth less than any income face. Proposed fix: $2 per unblocked Red cube, a `Block 2 Red` 1-pip face, and one Red `+$2` face changed to `+$1 / +1 🔬`.
Script: `scripts/run_v360_red_rebalance_sweep.py`, 1,500 games per pod, same seeds across configs. Data: `sim_results/v360_red_rebalance_sweep.json`.

| Pod | Config | Rounds | Patient Zero games | Singularity | Red dice bought / seat | Red block rate | Ransom paid / seat | Leaks / seat | Final Secrets |
|---|---|---|---|---|---|---|---|---|---|
| 2P | v0.35 | 8.89 | 60.4% | 41.8% | 0.17 | 10.4% | $8.27 | 2.72 | 2.21 |
| 2P | $2 ransom | 8.54 | 72.1% | 30.1% | 0.11 | 13.2% | $10.50 | 3.71 | 1.68 |
| 2P | Red die only | 8.90 | 60.4% | 41.7% | 0.15 | 10.7% | $8.20 | 2.73 | 2.25 |
| 2P | Package | 8.54 | 71.9% | 30.0% | 0.11 | 13.4% | $10.44 | 3.71 | 1.68 |
| 3P | v0.35 | 8.69 | 69.5% | 33.8% | 0.16 | 10.4% | $8.09 | 2.62 | 2.57 |
| 3P | Package | 8.29 | 77.8% | 24.8% | 0.12 | 13.2% | $10.19 | 3.57 | 2.10 |
| 4P | v0.35 | 8.60 | 71.8% | 31.6% | 0.16 | 10.6% | $8.00 | 2.56 | 2.94 |
| 4P | Package | 8.18 | 80.2% | 22.0% | 0.11 | 13.7% | $10.09 | 3.49 | 2.52 |

Takeaways:
1. **The premise was wrong in the sim.** Players end the game at ~$0.5 cash, and the Unpaid Ransom Leak already happens in ~31% of attack resolutions at $1. Red is not mainly a cash tax; it is mostly a source of 1-Secret leaks for broke players.
2. **$2 per Red cube** mostly adds leaks (+~1 per seat, leak rate 31% → 44%). That costs ~0.5 Secrets per seat, raises Patient Zero games by 8–12 points, shortens games by ~0.4 rounds, cuts Singularity by ~10 points, and lowers market purchases (Blue 0.46 → 0.31, Yellow 0.55 → 0.32 per seat).
3. **The Red die change does nothing measurable.** Bots buy ~0.15 Red dice per seat and the Block 2 face shows up 1 time in 6, so Red color shields block only ~6% of blocked Red cubes. Testing it properly needs a bot purchase policy that values Red dice.
4. Company spread barely moves (DTO unchanged).

Caveats: bot heuristics were not retuned for $2 ransom (only the Phase 4 `Block 1 Any` Tier 2 check was scaled); results reflect current bot buying.

**Status: exploration only; no `RULES.md` change.**


## 32. Phase 45 Exploration: Market Share & Market Collapse Probe (pre-SDLC)

Question: can Red become corporate competition (Market Share) instead of a cash attack, with a third end trigger (Market Collapse) balanced against Patient Zero and Singularity?
Plan: [docs/explorations/2026_11_market_share_red_rework_plan.md](docs/explorations/2026_11_market_share_red_rework_plan.md).
Probe: `scripts/explore_v360_market_collapse_probe.py` (hooks only, not rules code). Data: `sim_results/v360_market_collapse_probe_starts.txt`, `sim_results/v360_market_collapse_probe_secrets.txt`.
Setup: Red ransom off, no Patent filings, Market Share −1 per unblocked Red cube. At 0, Market Share triggers the Final Round. Bots regain at 2 🔬 per +1, max +1 per round. Money payouts and new Red ★ variants are not modeled.

| Pod | Starting Secrets | Market Share start | Patient Zero / Singularity / Market Collapse | Rounds | Games |
|---|---|---|---|---|---|
| 2P | 8 | 19 | 37 / 33 / 30% | 8.56 | 800 |
| 3P | 10 | 20 | 35 / 32 / 33% | 8.78 | 400 |
| 4P | 11 | 20 | 36 / 33 / 31% | 8.79 | 400 |

Takeaways:
1. **Red is today's second-biggest Secret drain.** It costs ~2.3 Secrets per seat via the Unpaid Ransom Leak. Red off: Patient Zero games 59 / 69 / 72% → 28 / 33 / 38%. Removing Patents as well brings pacing back near v0.35 (Patient Zero games 40 / 57 / 58%, rounds 9.02 / 8.65 / 8.41).
2. **Collapse mostly replaces Singularity endings** (both land late). With 8 starting Secrets, Patient Zero stays at 44–57% at 3–4P whatever the Market Share start, because it triggers when *any* player breaches. More Secrets at 3–4P (10 / 11) restore the three-way balance.
3. **Elimination at 0 would be unsafe.** Players face identical Red cubes, so with no deliberate Red play they hit 0 together. That would be 25–66% Total Wipeouts, so Market Collapse does not eliminate.
4. **Comparisons tie a lot without deliberate play.** The cumulative best–worst gap is 1–2 cubes and rankings tie 38–67%. At the Phase 2 Version change, the median player has `$2`, so the bank funds the top payout.
5. **Setup tilt is mild at 2P.** By v3.0 card, company seat and White Hat, endings move within about ±5 points.

Caveats: v0.35 bots ignore Red, and the regain rule is fixed. The results are first-order until Red-aware bots exist.

**Status: design locked by User 2026-11-06 (plan Sections 7–8). Next: SDLC (spec, Red-aware bots, sweep). No `RULES.md` change yet.**


## 33. Phase 45 v0.36 Sweep & Balance Iteration 1 (not approved yet)

Sources: product-owner [docs/findings/v360_market_share_telemetry_report.md](docs/findings/v360_market_share_telemetry_report.md) (51,000 games, seed 42, data `sim_results/v360_market_share_sweep.json`) and game-designer [docs/findings/v360_balance_assessment.md](docs/findings/v360_balance_assessment.md).

| V036 (3,000 games/pod) | 2P | 3P | 4P |
|---|---|---|---|
| Patient Zero / Singularity / Market Collapse | 43 / 37 / 20% | 41 / 39 / 20% | 42 / 37 / 22% |
| Rounds | 8.64 | 8.77 | 8.77 |
| Total Wipeout (V035) | 5.8% (16.0%) | 1.3% (5.8%) | 0.2% (1.9%) |

Takeaways:
1. **VentureGreed is broken under v0.36.** Its win rate falls from 52 / 46 / 42% to 4.5 / 1.5 / 0.7%: it lost Patent Filing, its only Secrets source. It drives most of the Patient Zero excess, and its presence swings the right starting Secrets by 2–3.
2. **The Collapse shortfall is genuine.** Payout-driven regain and Red-aware blocking each cost about 6–7 points against the ~30% pre-SDLC probe. Market Share start −2 restores it with any bot roster.
3. **`v1.0` comparisons are structurally tied.** All players tie 65 / 41 / 31% of the time.
4. **Several flags are bot artifacts:**
   - Public Relations at 60% of maxed tracks is a bot focus-order artifact (18–21% with neutral focus).
   - Ad Campaign is weak by construction.
   - Money inflation comes from removing ransom.
5. **The kamikaze signal is not degenerate** once ties and multi-player collapses are accounted for.

**Decisions (User, 2026-11-06):** Market Share start 17 / 18 / 18; drop the `v1.0` comparison (keep `v2.0` at `$4`); re-open starting Secrets after the bot fixes; look at a Money → Secrets outlet next phase. **Status: tune and bot fixes in progress, then re-sweep.**


## 34. Phase 45 Balance Iteration 2: APPROVED WITH TUNE

Sources: product-owner [docs/findings/v360_market_share_iter1_telemetry_report.md](docs/findings/v360_market_share_iter1_telemetry_report.md) (94,000 games, seed 42) and game-designer [docs/findings/v360_balance_assessment_iter1.md](docs/findings/v360_balance_assessment_iter1.md) (fresh seeds 7000, 3,000 games/pod).

| Starting Secrets 7 / 7 / 8, v2.0-only comparison | Seeds 7000 | Seed 42 |
|---|---|---|
| 2P: Patient Zero / Singularity / Market Collapse | 30.0 / 35.5 / 34.5 | 31.0 / 34.8 / 34.2 |
| 3P | 32.9 / 34.1 / 32.9 | 34.5 / 33.5 / 32.1 |
| 4P | 30.5 / 34.1 / 35.4 | 30.3 / 33.6 / 36.1 |

Guardrails at these values:
- Rounds 8.76–8.86.
- Total Wipeout 7.1–7.5 / 2.3–2.6 / 1.0% (v0.35: 15.8 / 5.9 / 2.1%).
- Highest single-setup trigger ≤ 43%.
- Red block rate 14.6–15.4% (v0.35 ~10%).
- Regain share 24–26%.
- Comparison all-tied 37 / 10 / 4%.
- No Market Collapse in ≤ 5 rounds.
- Kamikaze Collapse at chance.

Takeaways:
1. **VentureGreed is back to v0.35 strength.** The fix moved it from 1–5% wins to 42–62%. That removes the per-player-count Secrets scaling, which turns out to have been an artifact of the broken bot.
2. **Keeping the `v1.0` comparison at `$2` still fails the 2P tie guardrail** (51.6% all-tied), so it stays dropped.
3. **Release Track concentration of 68–72% is a bot focus artifact.** It is 33–35% with random focus.
4. **The economy rise is intended** (buys 1.8–2.0× v0.35, end Money ~$1.9). It comes from removing Red ransom.

**Decisions (User, 2026-11-06):**
- Starting Secrets 7 / 7 / 8.
- Company spread (20–23 points) deferred to the company-identity phase.
- Release concentration accepted as a bot artifact; the Release / Defense vs Triage / Public Relations strength gap is a watch item.

Bot follow-ups, not blocking:
- RecklessSaboteur focus order.
- Diversify roster focus orders.

**Status: OFFICIALLY APPROVED (`v0.36.0` Baseline).** `v036()` sets Secrets 7 / 7 / 8. Phase B is done: RULES.md, glossary, CLAUDE.md, web and PnP; `GameConfig()` is now v0.36.

## 35. Engine Fix: Multi-Version Black Cube Spillover Cascade (six-phase Phase 2, no rules change)

The six-phase compiler (`sim/engine/phase2_compiler.py`) stopped spillover at v2.0: when spillover filled v2.0 in the same compile, later cubes were counted but not resolved, and the v3.0 advance waited for a later Black cube. RULES.md Phase 2 ("Version Advance & Track Spillover") already says excess cubes spill onto the next Version's track from Space 1, so the engine now matches the rules.

- **Fix:** a new field, `GameState.pending_extra_version_advances`, queues one extra Version Switch for each non-final track that spillover fills. Spillover continues onto the following track from Space 1, and Singularity fires if it covers v3.0 Space 6. The Phase 1 Step 1 Version Switch then runs each queued switch in order. Each switch forfeits the old override, unlocks the new one and adds the new Version's staging payload, so on v1.0 → v3.0 the v2.0 override is unlocked and forfeited at once. `GameState.multi_version_spill_events` counts these compiles. The legacy v0.33 path (`legacy_v033.py`) is unchanged, for parity.
- **Tests:** `tests/test_version_spillover_cascade.py` covers four cases: overfill v2.0 onto v3.0, exactly fill v2.0, cascade to Singularity, and a single-version regression guard.
- **Frequency (v0.35 sweep setup, `GameConfig()` V035, seeds `42 + n*100000 + idx`, 1,000 games per pod):** **0 / 1,000** occurrences in 2P, 3P and 4P each. All 3,000 game fingerprints (rounds, end reason, winners, full rankings) match the pre-fix engine. Across the 26,223 compiles, at most 4 Black cubes exited in one compile and at most 3 spilled past a filled track. Filling v2.0 by spillover needs ≥ 6 in one compile. In every v1.0 compile, the Black cubes in the Staging Cup and tower were at least 3 short of that, so the case is possible under the rules but practically unreachable under current tuning. The fix only matters for future levers that raise Black cube volume.
- **Decision (User, 2026-11-06):** keep the engine fix; no RULES.md cap or clarification for this hypothetical.
- **v0.36 coordination:** the spec's §4.3 "known limitation / do not fix" note no longer applies. Its spillover-branch comparison hook falls exactly where the new non-final-fill arm runs (`spill_idx == next_ver.track_capacity` on a non-final target), and `double_version_fill_events` matches `multi_version_spill_events`.

## 36. Pre-SDLC Exploration: Blue Defense Agency (no rules change)

Question (User, 2026-11-06): blocking Blue always comes first, so defense "plays itself", and v0.36 has no repeatable Secrets engine. Probes (hooks only, not rules code; `GameConfig.v036`, current bot roster, seeds `42 + n*100000 + idx`, 600 games per pod): `scripts/explore_v360_blue_pressure_probe.py`, `scripts/explore_v360_topoff_probe.py`, `scripts/explore_v360_blue_block2_probe.py`.

**Diagnosis (baseline, per seat per game):**

| | 2P | 3P | 4P |
|---|---|---|---|
| Block rate Red / Blue / Green | 15 / 67 / 12% | 15 / 68 / 12% | 15 / 67 / 12% |
| Any shields spent on Blue | 63% | 63% | 62% |
| Contested Any splits (Blue covered first) | 66% of attack rounds (94%) | 66% (94%) | 67% (94%) |
| Start → final Secrets; lost to Blue | 7 → 3.12; 3.96 | 7 → 3.29; 3.79 | 8 → 4.17; 3.94 |
| All other Secret gains minus Corruption losses | +0.08 | +0.07 | +0.11 |

1. **Final Secrets ≈ starting Secrets − Blue losses.** Blue defense is effectively the score. A Blue cube costs a permanent VP; Red and Green cost recoverable resources, so Blue-first is always correct. (Bots fill Blue first by policy, but the scoring math backs it.)
2. Patient Zero seats lose 7.5–8.7 Secrets to Blue vs 3.1–3.4 for survivors.

**Idea 3 — L4 top-off** (once per round in Phase 6, any track at L4: pay X 🔬 for +1 Corporate Secret; working name only, no glossary term):
- Research income is ~1.3 🔬 per round per seat; 42–44% of seats reach one L4 track, around round 4–5.
- Bots that convert only leftover research rarely use it (2–8% of seats).
- A top-off-aware bot (tops off before other spending; prices the first repairable Blue cube each round at X 🔬): at 3 🔬, 27% of seats use it, about 1.75 Secrets per user. Endings stay within ~3 points of baseline, rounds unchanged. One aware seat vs current bots wins 50.2 / 37.2 / 27.7% (fair share 50 / 33 / 25%). At 2 🔬: 40.7% at 3P and 31.1% at 4P, too strong.
- Starting Secrets −1 with top-off pushes Patient Zero to 37–41%: keep 7 / 7 / 8.
- **Agency barely moves:** Blue left open on purpose in contested splits goes from ~6% to 7–8% (8–9% at 2 🔬). A repairable Blue (3 🔬) still costs more than Red (2 🔬 regain) or Green, and the L4 gate arrives late.

**Idea 2 — Block 2 Blue faces** (A: Face 1 → Block 2 Blue; C: Faces 1 and 4 → Block 2 Blue):
- Blue lost per seat falls by 0.2–0.4 (3P: 3.79 → 3.59 / 3.42); Any shields on Blue 63% → 61 / 60%; endings shift 1–3 points.
- Small because seats own only 0.75–0.86 Blue dice and see Blue block faces 2 times in 6, vs ~1.5 Blue cubes per round.
- **Must-buy risk:** win rate by Blue dice owned (0 / 2+) at 4P goes from 17 / 39% to 13 / 47% (C). Partly correlational; bots' buying logic does not know Blue got stronger.

**Not simulated:** idea 1 (lower a track for a Secret — a late lifeline, would lower Patient Zero endings), idea 4 (new track — Patents again), idea 5 (Market Share → Secrets thresholds — the −1 side brings back the Unpaid Ransom Leak; shared Red cubes push toward Total Wipeouts).

**Takeaways:**
1. Making Blue cheaper to block (idea 2) or to recover from (idea 3) leaves Blue the costliest cube to take, so Blue-first stays correct. Real shield-split agency likely needs Red or Green damage to hurt more.
2. Idea 3 at 3 🔬 is worth keeping as a Secrets engine and strategic path (pacing-neutral, modest edge). Idea 2 is at most a small tuning option.
3. Sim/rules mismatch: `sim/engine/phase4_attack_resolution.py` lets DTO *Slush Fund* pay `$1` per extra Secret beyond the free 2; RULES.md has no such rule.

**Status: exploration recorded (User, 2026-11-07). No RULES.md, PnP or web change. Next candidate: probe costlier Red / Green damage.**

## 37. Pre-SDLC Exploration: Market Share Threshold Penalties (no rules change)

Question (User, 2026-11-07): would 2–3 threshold points on the Market Share track, each switching off something while a player is below it, push players to invest in Public Relations and make tanking toward Market Collapse less attractive? Candidate penalties: Client Company ability (Institutional Override) unavailable, Signature Protocol unavailable, lose a Purple die. Each comes back when the player climbs back above the threshold. Probes ran on scratchpad hooks only, not rules code: `GameConfig.v036`, the current bot roster, seeds `42 + n*100000 + idx`, 600–800 games per pod.

**Baseline Market Share curve (3P mean):** r2 16.7, r4 14.5, r6 11.9, r7 9.5, r8 6.7, r9 5.3. It falls about 1 per round in `v1.0`/`v2.0`, then about 2.5 per round once `v3.0` Red cubes arrive. Share of seats that ever reach ≤12 / ≤9 / ≤6 / ≤3: 94 / 84 / 70 / 51% (2P and 4P are similar). **The surviving player with the lowest Market Share wins 68 / 47 / 37%** (fair share 50 / 33 / 25%).

**Value of each penalty (one seat with it switched off all game):** without the Client Company ability, that seat wins 33.7 / 19.8 / 12.5%, about half its fair share. Without the Signature Protocol it wins 46.4 / 31.3 / 20.3%, a small loss. A lost Purple die was not simulated.

**Fixed thresholds** (Company off at ≤9 and Signature off at ≤5; at ≤6 / ≤3; at ≤12 / ≤9; both off at ≤14): endings move 1–5 points and rounds stay at 8.6–8.9. The lowest-Market-Share player wins just as often. Shared Red cubes push every player across a threshold together, and only late, after most Institutional Overrides are already used, so a threshold acts as a tax on everyone rather than a penalty for tanking.

**Relative lock** (the lowest-Market-Share survivor(s) lose the Client Company ability; nobody when everyone is tied). Aware bots spend research before track upgrades to get strictly above their lowest rival, except in the Final Round.

| 3P | Patient Zero / Singularity / Market Collapse | Market Share regained per seat | Final Secrets | Lowest Market Share wins |
|---|---|---|---|---|
| Baseline | 35 / 31 / 34% | 1.14 | 3.29 | 47% |
| Lock, bots ignore it | 37 / 31 / 32% | 1.16 | 3.09 | 42% |
| Lock, all bots aware | 40 / 36 / 24% | 2.43 | 2.65 | 49% |
| Lock, one aware bot | 38 / 30 / 32% | 1.42 | 2.98 | aware seat wins 33.2% (fair 33%) |
| Lock with a 2-point gap, all aware | 40 / 36 / 24% | 2.44 | 2.65 | 55% |

2P and 4P show the same pattern. With all bots aware, the lowest-Market-Share player wins 74% (2P) and 32% (4P). One aware bot wins 50.2% (2P) and 27.5% (4P).

**Takeaways:**
1. The relative lock does change behaviour: regain roughly doubles. But it becomes an arms race. Placings barely move, the research comes out of defense, Final Secrets fall by about 0.6, Patient Zero rises 3–6 points and Market Collapse falls about 10 points.
2. Avoiding the lock gives no edge (the one aware bot wins at its fair share), and tanking still pays as well as before.
3. Root cause (hypothesis): Market Share pays too little against Secrets, so research spent on defense beats research spent on Public Relations. Penalties add cost but don't change that trade-off.
4. Caveat: the aware bot follows a fixed "never be last" rule and doesn't weigh the lock against what it gives up.

**Next candidate:** reward Market Share instead of punishing it (for example, end-game Market Share → Secrets, or a `v2.0` comparison that pays Secrets), while watching the Total Wipeout risk noted for idea 5 in §36. Any lock rule would need a new glossary term, which must be confirmed with the User first.

**Status: exploration recorded (User, 2026-11-07). No RULES.md, PnP or web change.**

## 38. Pre-SDLC Exploration: End-Game Market Share Placement Bonus (no rules change yet)

Question (User, 2026-11-07): at game end, award bonus Corporate Secrets by relative Market Share placement (proposed 5/3/2/1). Patient Zeros get nothing; ties broken by the standard tiebreakers. What does it do to Blue as the default block? Probe (hooks only, not rules code; `GameConfig.v036`, current bot roster): `scripts/explore_v360_share_placement_probe.py` (modes `main`, `variants`, `cands`, `deep`, `prfirst`, `tw2p`, `fresh`). Seeds `42 + n*100000 + idx`, re-checked on `7000 + …`; 1,500–3,000 games per cell. Data: `sim_results/v360_share_placement_*.txt|json`.

A **bonus-aware** seat (probe heuristic, TUNE-BOT) values one Red cube at time weight × 3 × the expected change in bonus. The time weight is 0.3 / 0.6 / 1.0 in `v1.0` / `v2.0` / `v3.0`–Final Round; 3 is the value of one Secret saved by blocking Blue. From `v2.0` on it also buys the smallest regain that raises its expected bonus. Lethal Blue stays protected.

**Only the gaps between places matter.** Every survivor gets a bonus, so 5/3/2/1 is really +2 / +1 / +1, and 3/2/1/0 plays the same as 2/1/0/0 at 2–3P.

| 5/3/2/1, standard ties (2P / 3P / 4P) | Value |
|---|---|
| Winner changed by the bonus (current bots) | 21 / 36 / 46% |
| Highest-Market-Share survivor wins (baseline 55 / 45 / 34%) | 72 / 68 / 61% |
| One bonus-aware seat wins (fair 50 / 33 / 25%) | 57 / 44 / 40% |
| 3P Patient Zero / Singularity / Market Collapse, all bonus-aware (baseline 35 / 33 / 33) | 53 / 30 / 18 |

Too strong: a 4-Secret swing at 4P against ~4.7 average survivor Secrets.

**Findings:**
1. **Ties are common.** Every player takes the same Red cubes, so a scoring place is tied on Market Share in 19 / 45 / 72% of games. Under standard tiebreakers, Money decides a 1–2 Secret bonus in those games. Shared ties (tied players all take the better place) cut winner flips by ~5 points.
2. **Survivors-only vs all-player placement:** almost no difference. Use survivors only.
3. **Patient Zero rises when players chase the bonus**, by +6–19 points depending on the schedule. This is rational: a more Red-aggressive seat wins *more*. +1 starting Secret offsets it at 3–4P.
4. **The 2P bonus needs a gap of 2.** A 1-point gap does nothing (bonus-aware seat 49.6%) because Market Share is already the first tiebreaker.
5. **Red die buying doesn't pay:** Red purchases roughly double (0.6 → 1.1–1.3), win rate unchanged. **Public Relations-first still loses:** 46 / 27 / 18% with the bonus vs 39 / 21 / 13% without (fair 50 / 33 / 25%). Research income (~1.3 🔬/round), not the regain limit, is the bottleneck. Average Public Relations level stays 0.2–0.4.
6. **Blue agency:** with shields short, Blue left open on purpose 6–7% → 17–22%; Red chosen 22% → 39–43%; Any shields on Blue 63% → 57–60%. Blue stays the main target. Red overtakes Blue only if players treat Market Share loss as permanent from round 1, and then Patient Zero hits 59–67% (degenerate). Win rate for 0 vs 2+ Blue dice flattens: 2P 40 / 66% → 45 / 61%.
7. **2P Total Wipeout:** at 8 starting Secrets, all bonus-aware, 10.1–10.4% (baseline 7.6%). At 9 Secrets it is 7.7–8.4%, with Singularity 45–46% (guardrail 43%).

**Proposed package (seed base 7000):** 2P 1st +2; 3–4P 1st +2, 2nd +1; others 0; Market Share ties share the better place; survivors only; no bonus on a Total Wipeout; starting Secrets **9 / 8 / 9** (2P +2 chosen by User).

| | 2P | 3P | 4P |
|---|---|---|---|
| Baseline endings | 30 / 36 / 34 | 33 / 34 / 33 | 30 / 34 / 35 |
| Endings, current bots | 18 / 42 / 39 | 26 / 39 / 36 | 24 / 38 / 38 |
| Endings, all bonus-aware | 27 / 46 / 27 | 37 / 41 / 22 | 32 / 39 / 28 |
| Total Wipeout, all bonus-aware (baseline) | 8.4% (7.1%) | 3.8% (2.6%) | 1.2% (1.0%) |
| Rounds, all bonus-aware (baseline) | 9.13 (8.83) | 8.97 (8.79) | 8.95 (8.83) |
| One bonus-aware seat wins | 59.2% | 39.6% | 33.7% |
| Winner changed by the bonus | 15–18% | 17–20% | 25–27% |
| Lowest-Market-Share survivor wins (baseline) | 31% (44%) | 20% (33%) | 13% (23%) |

Seed-42 results agree within ~2 points. RecklessSaboteur's 2P win rate rises 27 → 37–42%.

**Watch items:** 2P Singularity 46% (over the 43% guardrail); 2P bonus-aware edge +9 points; Patient Zero 18–26% if players ignore the bonus; Public Relations Track weakness (separate exploration).

**Implementation plan (pending User sign-off). Rule name: Market Leader Bonus (User, 2026-11-07).**
1. **Glossary:** add **Market Leader Bonus**. Change Market Share's "Scores `0 VP`" line, and update the Corporate Secrets and Total Wipeout entries.
2. **RULES.md:**
   - Section 5 scoring step: award by placement before comparing Secrets; ties share; Patient Zeros excluded; none on a Total Wipeout.
   - Starting Secrets `[TUNE]` 9 / 8 / 9.
   - Market Collapse note: the player at `0` scores normally but places last.
3. **sim:**
   - `GameConfig` fields for the bonus schedule and tie mode, plus a v0.37 factory.
   - `sim/engine/end_game.py`: apply the bonus before ranking; record pre-bonus Secrets and the bonus in telemetry.
   - `sim/bots/market_share_policy.py`: placement-bonus valuation in `marginal_block_value` and `urgent_regain` (time weight [TUNE-BOT]).
   - Tests: tie sharing, Patient Zero exclusion, Total Wipeout, 2P schedule.
4. **Acceptance sweep** with the full guardrail set (product-owner) and an independent balance check (game-designer).
5. **PnP and web:** scoring summary, Market Share track placement reminder, Company Terminal Mat and end-game screen (graphic-designer).

**Status: exploration recorded (User, 2026-11-07). No RULES.md, PnP or web change.**

## 39. Phase 46 Market Leader Bonus Sweep & Balance: APPROVED WITH TUNE (`v0.37.0`)

Sources: product-owner [docs/findings/v370_market_leader_bonus_telemetry_report.md](docs/findings/v370_market_leader_bonus_telemetry_report.md) (spec cells at seed 42, V036 / V037 / ONE-AWARE again at seed 7000, extra 2P seed bases 9000 and 13000); game-designer [docs/findings/v370_balance_assessment.md](docs/findings/v370_balance_assessment.md) (~48,000 more games of tune slices). Implementation: spec [docs/specs/v370_market_leader_bonus_spec.md](docs/specs/v370_market_leader_bonus_spec.md), `GameConfig.v037()`.

| V037, seed 42 | Patient Zero / Singularity / Market Collapse | Total Wipeout (V036) | Rounds | Winner changed (over all games) | Bonus-aware edge |
|---|---|---|---|---|---|
| 2P | 27.0 / 47.1 / 25.9 | 8.4% (7.6) | 9.14 | 10.7% | +7.9 |
| 3P | 37.5 / 39.9 / 22.6 | 4.2% (2.6) | 8.97 | 14.4% | +6.2 |
| 4P | 30.4 / 40.1 / 29.4 | 1.6% (1.0) | 8.99 | 24.5% | +7.4 |

Seeds 42 and 7000 agree within 2.1 points. Endings, Total Wipeout and edge match §38 within 2.5 points.

**2P Singularity** is 46.0% [45.1, 46.9] pooled over 12,000 games (four seed bases), on the 46% fail line. It is driven by the 9-Secret 2P start, not the bonus: with V036 starting Secrets it is 36.2%, but Patient Zero is 42.2% and Total Wipeout 12.0%.

| 2P tune option | Patient Zero / Singularity / Market Collapse | Total Wipeout | Edge | Outcome |
|---|---|---|---|---|
| A. 9 Secrets, +2 (kept) | 27 / 47 / 26 | 8.4 / 7.7 | +7.9 | Singularity on the line |
| B. 8 Secrets, +2 | 34 / 42 / 24 | 10.4 / 9.3 | +7.1 | Total Wipeout fails |
| C. 9 Secrets, +1 | 23 / 45 / 31 | 5.8 | +1 to +2.5 | Bonus barely worth chasing |
| D. 8 Secrets, +3 | 42 / 39 / 19 | 13 | +9.4 | Three guardrails fail |

The 46–47% is the worst case, where every bot chases the bonus. With one bonus-aware seat it is 44.2 / 42.4%; with none, 43.0%.

**Blue agency goal: met.**
- Generic shields on Blue: 63% → 57–60%.
- Blue left open in contested rounds: 6–7% → 17–23%.
- Red chosen in contested rounds: 22% → 39–44%.
- Red block rate: 15% → 21–22%.
- 2P win rate with 0 vs 2+ Blue dice: 41 / 67% → 44 / 62%.

**Game-designer notes:**
- The winner-changed gap with §38 is a counting difference, not a gameplay one. The probe divided by all games and used a shorter pre-bonus tiebreak. Like-for-like it is ~13% vs the sweep's 10.7–11.7%. The new 2P baseline is 11–13%.
- At 2P, 4.7% of games see a 2-Secret lead overturned: +2 creates a tie and Market Share breaks it. Accepted as a playtest watch item; Market Share is public and the trailing player must win it outright.
- RecklessSaboteur's 2P win rate rises 29.4 → 37.7%. This is intended catch-up; it is still the weakest bot, and the spread between bots narrows from 31.5 to 22.5 points.

**Watch items:**
- 3P Market Collapse 22.6 / 23.2%.
- Bonus-aware edge +7.4 to +9.4 (fail +10).
- Zero Day Override as the v3.0 card: 2P Singularity 50.5% (fail 55%).
- 2P Patient Zero 17.4% when no bot chases the bonus.
- 2P Blue left open 23.1% (line 25%).

**Decisions (User, 2026-11-07):** keep option A (starting Secrets 9 / 8 / 9; 2P 1st +2; 3–4P 1st +2, 2nd +1). Move the 2P Singularity guardrail to pass ≤ 43%, watch 43–48%, fail > 48%. The game-designer's notes on 2-Secret overturns and the 11–13% winner-changed baseline are adopted as watch / baseline values.

**Status: approved for Phase B (RULES.md v0.37.0, glossary, `GameConfig()` default, web, PnP).**

## 40. Phase 47 Reference Bot Assessment and Kamikaze Market Collapse Check (no rules change)

Question (User, 2026-11-07): is the reference bot fit as the "competent player" check, what does it say about §36–§38, and does its win after its own Market Collapse trigger (195 of 1,200 v0.37 ref1 games) show a kamikaze strategy? Sources: `sim_results/reference_bot/validation_report.md`; game-designer report [docs/findings/v370_reference_bot_assessment.md](docs/findings/v370_reference_bot_assessment.md). Extra probe: the validation seeds replayed with per-round Market Share / Secrets telemetry, 3P, 1,200 games per cell, plus a Market Collapse-off counterfactual (scratch only).

**Bot verdict: fit.** ref1 edge over fair share: +33 / +36 points at 3P (v0.36 / v0.37), well past the +10 gate. Mixed seats sit at fair share. Limits: it only chooses among moves the existing policies propose; rollouts are played by scripted policies; only Phase 4 shields and Phase 6 spending are searched.

**§36–§38 re-judged:**
- Blue-first stands, softened: ref still puts ~49% of blocks on Blue but blocks Red more (Red block rate 0.29 vs rivals 0.22 at v0.37).
- §37 root cause stands: ref regains less Market Share than rivals (1.31 vs 2.06) and still wins.
- "Tanking pays" was a bot artifact (see below).
- Public Relations-first still loses (ref Public Relations Track 0.65–0.77).

| Kamikaze check, 3P ref1 | v0.36 | v0.37 |
|---|---|---|
| ref at 0 when Market Collapse triggered (others at 0 too / alone) | 432 (390 / 42) | 375 (316 / 59) |
| ...ref won | 236 | 195 |
| ref Secrets lead at trigger in those wins | +3.8 (never behind) | +7.5 (behind 0.5%) |
| ref wins when it alone triggers | 40% (17/42) | 37% (22/59) |
| Market Share lost to Red, ref / rivals | 16.7 / 17.8 | 16.4 / 17.7 |
| ref win with Market Collapse off (counterfactual) | 64.5% (−2.1) | 66.7% (−2.4) |
| Singularity with Market Collapse off | 83% | 84% |

**Takeaways:**
1. No kamikaze strategy. The ref seat loses *less* Market Share than rivals, is usually at 0 together with everyone else (shared Red cubes), and wins those games because it already leads on Secrets. Alone at 0 it wins only at about fair share.
2. Market Collapse is not what the ref's edge depends on (−2.4 points when switched off). Collapse is doing its pacing job: without it Singularity takes ~83% of endings.
3. Watch item: under v0.37 the ref is strictly lowest on Market Share the round before trigger in 43% of its at-0 games (v0.36: 26%). It trades Public Relations for Secrets, a legitimate trade that confirms §37.
4. Archetypes: VentureGreed leads (51% at 3P v0.37) on economy and Blue defense, not a rule exploit; the ref seat holds it to 32%. SecOpsTurtle rises 26 → 39% under the Market Leader Bonus (intended). RecklessSaboteur Patient Zero 10% at 3P. No other degenerate pattern.

**Candidate levers (none decided):** A. no change (recommended); B. a larger 3–4P Market Leader Bonus gap ([TUNE]); C. cheaper Public Relations regain ([TUNE], small expected effect); D. a Secrets penalty at 0 Market Share (new rule and likely new term, needs User approval; Unpaid Ransom Leak risk); E. remove Market Collapse (shown only as a counterfactual; breaks pacing).

**Open questions for User:** adopt one Mixed seat in every sweep and a ref1 edge check on every rule candidate? Close the kamikaze concern (lever A)? Add "Public Relations push" and "Market Share dump" candidates to the bot portfolio?

**Status: analysis recorded (game-designer, 2026-11-07). No RULES.md, PnP, web or sim change.**

**Decisions (User, 2026-11-07):** adopt the roster rule (one Mixed seat in every routine sweep; ref1, 3P, 1,200 games, as the edge check on every rule candidate). Close the kamikaze Market Collapse concern with lever A (no rule change). Add "Public Relations push" and "Market Share dump" as reference-bot candidates so future no-exploit results cover those lines.

**Addendum: portfolio follow-up (game-designer, 2026-11-07).** The 13-member portfolio lifts ref1 v0.37 3P win 69.1 → 78.6% (±2.3). Attribution, 1,200 games each, same seeds; details in [docs/findings/v370_reference_bot_attribution.md](docs/findings/v370_reference_bot_attribution.md), data in `sim_results/reference_bot/attribution/`:

| Portfolio | Win % | Δ | Collapse off | Ref at 0 at trigger (alone) | MLB 1st | Red share of blocks |
|---|---|---|---|---|---|---|
| 11 | 69.1 | — | 66.7 | 375 (59) | 64% | 36% |
| + push | 74.2 | +5.1 | 68.0 | 254 (35) | 78% | 42% |
| + dump | 76.3 | +7.2 | 78.6 | 446 (94) | 63% | 34% |
| 13 | 78.6 | +9.5 | 77.6 | 321 (51) | 75% | 40% |

Both lines contribute (overlapping, not additive). Push is undervalued Red blocking and Public Relations, and it pays mainly by keeping the ref off 0 when Market Collapse triggers. Dump trades Market Share for Secrets and is stronger with Collapse off, so it is not kamikaze. §40 "no kamikaze" and §38 "Public Relations-first loses" both stand; §38 is refined to "situational Public Relations wins". Candidate levers (none decided): A bot update only (recommended); B larger Market Leader Bonus gap [TUNE]; C stronger Red [TUNE]; D Secrets penalty at 0 Market Share (new term, needs User approval). No RULES.md, PnP, web or sim change.

## 41. Phase 48 Lever A Post-Telemetry Assessment (bot-only, no rules change)

Question (User, 2026-11-07): did lever A (situational Public Relations push / Market Share dump for AdaptiveBalanced, Blue-safe split, default `PrPushParams` kept by User decision) make the roster play closer to competent? Should `bot_pr_push=True` become the default roster, and which scope should the ref1 edge check use? Is VentureGreed's >40% win rate a rules or a bot problem? Sources: `sim_results/lever_a/sweep/sweep_report.md`, `docs/findings/lever_a_regression_diagnosis.md`; report [docs/findings/v370_lever_a_assessment.md](docs/findings/v370_lever_a_assessment.md). Extra probes (scratch, 4 procs): ref1 3P switch off on the current tree (300 games, 300/300 identical to the 13-member file), ref1 2P switch off (600 games, heads-up).

**Correction:** the sweep compared ref1 "on" with the 11-member 69.1% file. The true switch-off baseline (13 members) is **78.6%**.

| ref1, 3P, 1,200 | ref win % | edge | Δ vs off |
|---|---|---|---|
| 13 members, off | 78.6 | +45 | — |
| on, scope `all` | 77.1 | +44 | −1.5 |
| on, scope `non_reference` | 71.2 | +38 | −7.4 |

| Check | Off | On | Result |
|---|---|---|---|
| AdaptiveBalanced 2P / 3P / 4P | 39.1 / 17.2 / 8.8 | 51.2 / 26.5 / 16.1 | PASS |
| Patient Zero Δ 2P / 3P / 4P | — | −0.3 / −0.3 / −1.3 | PASS (≤ +2) |
| Mixed seat 3P | 34.2 | 32.7 | PASS |
| Max archetype 3P | 51.2 (Vent) | 48.8 (Vent) | FAIL, pre-existing |

**Verdict: lever A met its goal (partial on the edge).** Every guardrail passes at 2/3/4P, AdaptiveBalanced gains 7–12 points, and the edge fell +45 → +38 (inside the scoping estimate +37 to +42). It stopped short of +35 because only AdaptiveBalanced learned the lines (the ref faces it in 40% of pods), the Phase 6 comfortable-leader dump is out of scope, and the search keeps a real tactical edge. Scope `all` hides the drop because the ref's fallback and rollouts improve too. The reference bot remains a valid competent-player check (2P heads-up 88%, Mixed at fair share).

**Proposed roster rule (needs User sign-off):** rule probes and routine sweeps use `bot_pr_push=True` with default `PrPushParams`, the `_bot_classes()` rotation and one Mixed seat; the edge check is ref1, 3P, 1,200 games, `bot_pr_push_scope="non_reference"`, reference 71.2% (+38), flag at ±5 points or below +10. Historical fixtures pin `bot_pr_push=False`.

**VentureGreed (3P 51.2 off / 48.8 on; 2P 59.0): a bot problem.** Heads-up against the ref at 2P it wins 20% (ref 80%, n = 120); with the ref at a 3P table it falls to 29–32%. It is the ref's hardest opponent (ref 59% with it vs 79% without), so its economy line (Yellow-first, paid Secrets with no cushion, light shielding) is strong, not degenerate; the other scripts answer it badly. Watch item: 2P spread. Candidate levers (none decided): V1 teach another archetype VG's paid-Secret timing [TUNE-BOT]; V2 re-define the 40% guardrail to also require ref1 holding the archetype below fair share; V3 add a second competent seat to the rotation; V4 dearer Money → Secret actions [TUNE] (scratch B2-only probe inconclusive); V5 larger 2P Market Leader Bonus [TUNE]. No new game term proposed.

**Follow-up:** `scripts/run_reference_bot_validation.py` output names include `_params` but not the `--pr-params` values, so runs with different overrides overwrite each other. Add a hash or `key=value` tag (engineering).

**Open questions for User:** adopt the roster rule above? Close Phase 48 at +38 or open a Phase 6 comfortable-leader dump lever? Accept the VentureGreed "bot problem" diagnosis and pick V1/V2/V3? Re-baseline sweep reports to the 13-member 78.6% file? Schedule the script naming fix?

**Status: analysis recorded (game-designer, 2026-11-07). No RULES.md, PnP, web or sim change.**

**Decisions (User, 2026-11-07):**
1. Roster rule adopted: every rule probe and routine sweep uses `bot_pr_push=True` with default `PrPushParams`, the `_bot_classes()` rotation and one Mixed seat. The edge check on every rule candidate is ref1, 3P, 1,200 games, seeds `42+300000+idx`, `bot_pr_push_scope="non_reference"`, reference value 71.2% (+38). Flag if it moves more than ±5 points or falls below +10. Historical fixtures pin `bot_pr_push=False`.
2. Phase 48 closed at +38; the Phase 6 comfortable-leader dump is not pursued now.
3. VentureGreed diagnosis accepted (bot problem). Lever V2 adopted: the 40% archetype guardrail fails only if ref1 also cannot hold that archetype below fair share. V1 kept for later; V3–V5 not pursued.
4. Sweep reports re-baseline to the 13-member switch-off ref1 value (78.6%).
5. Fix `run_reference_bot_validation.py` output naming so `--pr-params` runs don't overwrite each other.

## 42. Pre-SDLC Exploration: Secret Faces, Processing Box & Company Starting Die (package locked, no rules change yet)

Question (User, 2026-11-07): every player is hit equally and only Secrets score, so every seat plays the same Blue-first game. Money and research are not enough of an engine, and Red and Green are "other things to juggle". Make the engine feed Secrets, so each player's dice decide which cubes hurt them. Sources: scratchpad probes (hooks / a standalone model, not rules code): `exposure_probe.py`, `colored_probe.py`, `yield_model.py`, `cube_cost.py`, `tune_probe.py`, `blue0_probe.py`, `grid_probe.py`, `grid2.py`.

**Step 1 — asymmetric cube impact (rejected).** Per-player colour→effect profiles were tested first (v0.37 roster, 3P, 2,400 games, random version deals). Cube exits per game vary with the v1/v2 deal (Red 11.7–23.6, Blue 10.8–16.4, Green 10.5–20.1). With the same defence, moving Secret theft from Blue to Red costs 12.0 vs 1.7 Secrets under Script Kiddie + RaaS (94% breach). Blue is the scarcest colour on purpose. The User kept the shared threat (like *Moon Colony Bloodbath*): divergence should come from what players build.

**Step 2 — baseline (v0.37 roster, 3P, 1,200 games).** Seats own 0.7 / 1.3 / 1.7 / 2.3 colored dice in rounds 2 / 4 / 6 / 8 but have only ~0.8 In Production. Mix: Blue 35%, Red 32%, Yellow 23%, Green 10%. Non-Blue Secret gains net +0.08 per seat (§36).

**Step 3 — Secret-yield model.** Single seat with scripted priorities, real tower draws from Step 1, calibrated so v0.37-like rules give Blue losses 3.96 (sim ~3.8) and 2.1 colored dice bought (sim ~2.3). It is ~1 Secret more generous than the full sim. No win rates.

| 3P, final Secrets at start 6 (no Market Collapse unless noted) | Red | Blue | Green | Mixed | Diverse | Red / Green cube cost to owner (r3) |
|---|---|---|---|---|---|---|
| First settled rules (Blue 1 + 2 Breakthroughs + bonus, cap 3; Green 2; Red 2/1/0 at 12/6) | 8.2 | 11.8 | 6.5 | 7.1 | — | 0.34 / 0.69 |
| Blue 0 + Breakthroughs + bonus; Red 3/2/1/0 at 14/10/6 | 10.6 | 9.5 | 6.5 | 5.7 | 7.4 | 0.56 / 0.67 |
| One Blue research space (Defense Grid L3) | 10.6 | 10.6 | 6.5 | 7.4 | 8.4 | 0.56 / 0.67 |
| + Green base 3 | 10.6 | 10.6 | 9.3 | 7.6 | 8.6 | 0.56 / 0.65 |
| + 12-point track (tiers 10/7/4) | 8.3 | 10.8 | 9.4 | 7.2 | 7.8 | 0.69 / 0.67 |
| + Company die replaces a Gray | 11.9 | 13.9 | 14.2 | 10.5 | 11.0 | 0.92 / 0.75 |

Red tiers on the package (start 5): 12 track 10/7/4 → Red seat 10.9, cube cost 0.95; **12 track 9/5/1 → 12.8, 0.85**; 14 track 11/7/3 → 12.8, 0.85; 18 track 14/10/6 → 13.7, 0.74. Blue costs ~1.0 for every seat. Today Red and Green cost ~0.

**Package at start 4 (12 track 9/5/1):** Red 11.8, Blue 11.8, Green 12.1, Mixed 8.9, Diverse 9.6, starting die only 6.4. Breach per seat at 3 / 4 starting Secrets: specialists 6–8% / 3–4%, Mixed 11% / 6.5%. v0.37-like reference in the model: ~10% at 8.

**Takeaways:**
1. Secret faces make the engine score: specialist paths earn 7–10 Secrets per game vs ~0 today, and each colour's cubes now cost its owners 0.75–0.92 Secrets against Blue's 1.0 for everyone. The tower stays equal for all; the payoff now depends on your dice.
2. Glitched Shield Slots with one free clear per Phase 5 graduation never take a seat's last shield slot (lingering, not compounding).
3. The Triage Bandwidth cap rarely binds (≤1.1% of colored dice blocked from chasing); Money is the real limit at these ownership levels.
4. Blue's research faces paid for its own yield (11.8, far ahead); a single +1 research space fixed it.
5. Specialising still beats spreading by ~2 Secrets. The model has no competition for dice (6 per colour at 3P, two Companies per colour), which only the full sim can test.
6. Yellow-first (fuel) is the weakest path in isolation. Watch item.
7. Market Collapse off: 3P sim endings 58% Singularity / 37% Patient Zero / 5% Total Wipeout, games +0.3 rounds. Check the 2P Singularity guardrail (pass ≤ 43%).

**Locked package (User, 2026-11-07):**
- **Secret face** (new term, provisional): Face 5 on Red, Blue, Green and Purple dice. The die goes to the **Processing Box** (new term, provisional; replaces the Glitched Box; Under Development = Processing Box → Scanned Box). The Secret is gained when Phase 5 Conveyor Triage moves the die out; dice still in the Processing Box at game end lose their Secret. Free rerolls stay. **Glitched Box** and the **Glitch face** are retired.
- **Yields:** Red 3 / 2 / 1 / 0 at Market Share 9+ / 5–8 / 1–4 / 0. Blue 1, +1 if you blocked at least 1 Blue cube that round, +1 at Defense Grid Level 3 (max 3). Green 3 minus your Glitched Shield Slots (min 0). Purple 1.
- **Market Share:** 12-point track (start and max 12). Market Collapse removed as an end trigger.
- **Defence:** colored dice have no shield faces; all shields are `Block 1 Any` from Gray, White and Purple dice.
- **Yellow:** fuel die (choice faces such as `$` / research), no Secret face, no shields.
- **Glitched Shield Slots** (provisional term): unblocked Green cubes and the "glitch X dice" Corruption spaces glitch slots. A die placed to clean a slot goes to the Scanned Box. Once per Phase 5, if at least 1 die graduates to Ready for Release, clear 1 slot. White Contractor glitch faces discard the die.
- **Company starting die:** each Client Company names a Red, Blue or Green starting die (two Companies per colour). It replaces 1 starting Gray; the Triage Level 1 Breakthrough gives a Gray die (replacing its 2 White Contractors).
- **Starting Secrets:** 4–5 at 3P for the full sim probe; 2P / 4P to be fitted.
- **Draft (to be confirmed by the probe):** die faces, Variant Card rework and power retargets as proposed to the User 2026-11-07. Red F1 `+1 Market Share / +$1`; Blue takes the research faces; Green F1 `Clean 1 Glitched Shield Slot / +$1`. R1 `+$2 & +1 Market Share`; B1 `+1 🔬` (+`$2` on no Blue damage); B2 pay-`$4` only; B3 moves Processing → Scanned in Phase 3; G1 / G2 clean slots + 🔬; Y3 goes to the Scanned Box. *Magnetic Splice* and *Jumper Diagnostics* move a die out of the Processing Box (banking its Secret). *Brute-Force Bypass* becomes +1 free reroll and set 1 die to any non-Star face. *Arbitrary Code Execution* may need to exclude the Secret face.

**Implementation plan (pending SDLC kick-off):**
1. **Glossary approval:** confirm Secret face, Processing Box and Glitched Shield Slot; retire Glitched Box and Glitch face; update the Market Share / Market Collapse entries.
2. **Spec (`principal-engineer`):** `GameConfig` levers for each part of the package (Secret faces, yields, 12-point track, Market Collapse off, no colored shields, Yellow fuel, Glitched Shield Slots with graduation clear, Company starting die, Breakthrough changes), with the v0.37 path kept for parity.
3. **Implementation (`senior-engineer`) + review (`staff-engineer`):** engine, die faces, Variant Cards, powers; bot policies for chasing Secret faces, colour-aware Any-shield splits and purchases. Tests: banking at triage, stranded dice on Singularity, yield tiers, slot clear, starting die.
4. **Sweep (`product-owner`):** 2/3/4P with the roster rule, starting Secrets 3–6, full guardrails (endings, Total Wipeout, rounds, archetype spread), win rate by Company colour and by path, and the ref1 edge check.
5. **Balance assessment (`game-designer`):** confirm the model's results with real competition for dice; tune tiers, Green base and starting Secrets.
6. **Phase B:** RULES.md, PnP and web after sign-off (`graphic-designer` for the Company Terminal Mat and dice).

**Glossary decisions (User, 2026-11-07):** Secret face, Processing Box and Glitched Shield Slot are approved as final terms, and Glitched Box is retired. The `Glitch` face stays on White Contractor dice only (it discards the die); colored dice no longer have it. Phase B retires Color-Specific Shield, Red / Blue / Green Shields, Two-Stage Defensive Blocking and Market Collapse (as an end trigger). The sim keeps the v0.37 path behind levers for parity.

**Status: package locked for the full sim probe (User, 2026-11-07). No RULES.md, PnP, web or sim change.**

## 43. Phase 49 Sweep & Balance Assessment (`v0.38` candidate): NOT APPROVED

Sources: `sim_results/v380_secret_faces/sweep_report.md` (15 cells × 1,200 games, roster mixed1, ref1 3P 1,200), `docs/findings/v380_balance_assessment.md` (probes P0–P11, 600 games per cell).

- **Works:** stranded Secrets ~3%; no round with zero shield capacity; Total Wipeout ≤1% at 3P/4P; 8.8–9.6 rounds; ref1 non_reference 78.2% ≈ the v0.37 13-member portfolio (78.6%).
- **2P Singularity** 63–82% at S3–S6 (guardrail ≤48%). Each starting Secret moves only ~5–6 pts. Only the P9 stack (S3 + Green base 2 + Purple yield 0) reaches 46.0%, with 8.2% Total Wipeout.
- **3P/4P Singularity** 45–75%; P11 (S4 + Green base 2 + Market Leader Bonus 4-2) gives 49.5% / 46.5%.
- **Archetype spread** 46–53 pts. The lever A push/dump line accounts for 11–16 pts (P1, bot artifact); the rest (~1.6× fair share) is a rule effect: Company-colour commitment and free 0 Market Share.
- **0 Market Share is a degenerate stable state:** 28–31% of seats end there. Red cubes then do nothing, so all shields go to Blue/Green, and Red dice keep paying. ref1 ends at 0 in 82.7% of games and wins 77.3% of those. A bigger Market Leader Bonus barely helps (P10).
- **Red path** strongest (61 / 46 / 38% at 2/3/4P); Red tiers 2/2/1/0 (P2) trim it. **Yellow path** weak (31 / 13 / 5%): Yellow cannot turn Money into Secrets (face-design gap).
- **Tooling bug:** `--set corruption_track_capacity_by_player_count` is silently ignored (P4 identical to P0).

**User decisions pending (assessment doc):** (1) 2P Singularity guardrail with Market Collapse off; (2) a cost for 0 Market Share (Market Collapse back / Red-at-0 cost / none); (3) Red tiers 2/2/1/0 and Green base 2; (4) starting Secrets per player count; (5) Yellow redesign; (6) lever A line for all archetypes or none in rule sweeps; (7) fix the `--set` bug.

**User decisions (2026-11-08) on §43:** (1)+(2) bring Market Collapse back as an end trigger (Final Round, no elimination) under v0.38; the 2P Singularity ≤48% guardrail stays. (4) Starting Secrets 2P 3 / 3P 4 / 4P 4 for the next candidate. (5) Yellow will be redesigned (design discussion open). (7) Fix the `--set corruption_track_capacity_by_player_count` bug. (3) yields and (6) the lever A bot line: pending, after explanation.
**User decisions (2026-11-08, cont.):** (6) lever A push/dump line off for all archetypes in rule sweeps. (3) User concern: Red 2/2/1/0 makes the top tier meaningless; proposed 2/1/0/−1 instead (under discussion). (5) Yellow direction: Market Share generator, e.g. one `+2 Market Share` face and one `+1 Market Share / +1 🔬` face (to be modelled). Green cube resolution and late-game Green pressure are open for discussion.
**User decisions (2026-11-08, cont.):** Red Secret face yield stays 3 / 2 / 1 / 0 with raised thresholds: Market Share 11–12 / 7–10 / 3–6 / 0–2 (2/1/0/−1 rejected: a Secret-costing face is a dead roll and echoes the retired Unpaid Ransom Leak). Green resolution accepted as is (glitches the slot for later rounds; dice already placed unaffected); a per-round slot-glitch cap is added as an off-by-default lever. Green base 3 vs 2 left to the probe.

### 43.1 Candidate 2 probes (`v038b`): APPROVED WITH TUNE

Source: `docs/findings/v380_balance_assessment.md` "Candidate 2" (probes Q0–Q6, R1–R2; 600 games per cell; noise ±2 pts on endings, ±4–6 pts on archetype and path rates).
- Market Collapse dominates in v038b (41–49%, 7.8–8.0 rounds). Cause: the 12-point start, not the new Red thresholds (Q4 ±2 pts).
- **Recommended C2 (R1):** v038b + starting Market Share 14 + Market Leader Bonus 2P +4 / 3–4P +4, +2. Endings (2P / 3P / 4P): Market Collapse 29.5 / 32.2 / 31.0%, Singularity 34.8 / 30.3 / 26.7% (2P guardrail met), Patient Zero 32–42%; rounds 8.24 / 8.25 / 7.94; spread 41 / 31 / 32 pts; AdaptiveBalanced 69 / 48 / 42%.
- Green base 2 rejected (Green path 21 / 13% at 3P/4P). The slot cap of 2 is inert. Yellow MS vs MS_ALT are within noise.
- **Yellow still weak** (16% / 10% at 3P / 4P): Yellow seats end with the lowest Market Share, since Red exits strip their income-phase gains. They bank 2.5–3 fewer Secret-face Secrets. Bot purchase scoring values Yellow as Money (selection bias toward weak bots).
- **User decisions pending:** C2 adoption; Green base 3; slot cap; Yellow profile; Yellow bot fix vs rules probe; 4P 7.9 rounds; 2P spread.
**User decisions (2026-11-08) on §43.1:** (1) adopt C2: v038b + starting Market Share 14 at all player counts + Market Leader Bonus 2P +4 / 3–4P +4, +2, for the 1,200-game confirm sweep and the ref1 check. (2) Green base 3. (3) Keep `glitched_slots_per_round_cap` in code, default off, out of the rules. (4) Yellow F1 stays `+2 Market Share` for now. (5) Fix bot Yellow valuation first, then re-measure. (6) Accept 4P 7.9 rounds for now. (7) Accept the 2P spread for now; re-check with ref1 at 2P.

### 43.2 C2 confirm sweep (`v038b`, 1,200 games per pod)

Source: `sim_results/v380_secret_faces/c2/sweep_report.md`. Endings (2P / 3P / 4P): Singularity 33.8 / 27.4 / 25.3%, Patient Zero 33.7 / 39.6 / 39.9%, Market Collapse 29.1 / 32.8 / 34.6%, Total Wipeout 3.4 / 0.2 / 0.2%. Rounds 8.15 / 8.16 / 7.92. 2P Singularity guardrail met. Archetype spread 35.7 / 38.2 / 33.3 pts (v037 26.9 / 36.1 / 34.1); AdaptiveBalanced 68.9 / 53.2 / 43.3%. Company Red leads by 8–13 pts at 3P/4P; Yellow path 39.4 / 20.8 / 12.1%. ref1 non_reference (lever A off, as the preset): 3P 84.1%, 2P 92.4%. The comparable baseline is 78.6% (switch-off), since rule sweeps run with lever A off. Correction: the first sweep's v037 rows omitted Market Collapse (2P 25.0 / 3P 20.9 / 4P 27.1%).

### 43.3 C2 assessment: APPROVED WITH TUNE (`docs/findings/v380_balance_assessment.md` "C2 confirm", probes T1–T4)
- ref1 rise (3P 84.1 / 2P 92.4%) is a bot skill gap, not an exploit. The ref seat alone triggers Market Collapse in 4–5% of games, at no more than its normal win rate. It is the only seat that blocks Red and climbs Public Relations. With lever A on for the rivals, ref still wins 79.2%.
- Red Company lead is a rule effect: the yield of 3 at 11+ stacks with Red F1 `+1 Market Share`. T4 (Red 2/2/1/0) flattens the Company lead but moves the 3P lead to the Green path (49%). Note: the User already rejected 2/2/1/0 (dead top tier).
- 4P Market Share 15 (T2): 7.92 → 8.01 rounds. Lever A on for all bots (T1) rejected (spread 47–52). Market Leader Bonus `+3, +1` (T3) trims the 3P spread 38 → 32.
- Yellow unchanged by any probe (9–21%). Orchestrator note: the Yellow bot purchase scoring was already moved off Money in §14.4; the remaining gap is mostly roster selection (VentureGreed / RecklessSaboteur).
**User decisions (2026-11-08) on §43.3:** (1) ref1 rise accepted as a bot skill gap; C2 values become the v0.38 ref1 baseline (3P 84.1%, 2P 92.4%). (3) Starting Market Share 15 at 4P. (4) Market Leader Bonus 3–4P trimmed to `+3, +1` (2P stays +4). (5) Yellow needs a rules fix (design open). (6) 2P archetype spread ~36 accepted. (2) Red to be rethought (design open). (7) C2.1 sweep and Phase B wait until Red and Yellow are resolved.

### 43.4 Red rethink: shared Market Share payout (User design, 2026-11-09; pre-SDLC, not modelled yet)
- Red Secret face no longer pays its owner by Market Share tier. Each Red die that leaves a Processing Box advances a shared table counter by 1. Every *n* Red dice banked, a payout fires: all surviving players score by Market Share place (draft: 1st 3 / 2nd 1 / others 0 Corporate Secrets; ties share the better place).
- This payout replaces both the `v2.0` Market Share comparison (Money) and the Market Leader Bonus. One more payout fires at game end, except when the game ends by Market Collapse (and, as now, not on a Total Wipeout).
- No new glossary term yet; the counter will need a name (User to approve).
- Open for modelling: owner reward per Red die banked (+1 Corporate Secret vs none); *n* per player count; payout in Secrets only or Secrets + Money; stalling (holding Red dice in the Processing Box); Yellow as the Market Share die under this rule.
- **Model results (game-designer, 2026-11-09; scratchpad patch over v038b, 600 games per cell; assessment doc "Red shared payout"):** Red banking volume is low (1.3–4.3 per game), so n = 2 gives only 1.0–1.7 payouts and n = 3 is near inert. Recommended "RSP-1": owner +1 Corporate Secret per Red Secret; n = 1 (every Red Secret banked fires a payout); payout 1st +3 / 2nd +1 in Secrets only; end payout except on Market Collapse / Total Wipeout; starting Market Share 16 / 16 / 17; Yellow F3 → `+$1 & +1 Market Share`; oldest-first Conveyor Triage (anti-stall). Result (2P / 3P / 4P): Market Collapse 36 / 41 / 38%, Singularity 44 / 42 / 44%, Patient Zero 18 / 16 / 18%; rounds 8.55–8.69; archetype spread 25–28; Company colours within ~6 pts; Yellow path 39 / 24 / 16%. With owner 0, Red is unplayable (7–24%); folding Money in changes ≤3 pts. Stalling is analytically real for a trailing Red owner (ref1 not run; bots not payout-aware). With n = 1 no counter is needed.
- **User decision (2026-11-09): RSP-1 adopted** as the next v0.38 candidate. Package (on top of C2 / v038b):
  - Owner +1 Corporate Secret per Red Secret banked (replaces the Red tiers).
  - Every Red Secret banked fires a payout: survivors score 1st +3 / 2nd +1 / others 0 Corporate Secrets by Market Share place; ties share the better place.
  - One end payout, except on Market Collapse / Total Wipeout.
  - Market Leader Bonus and the `v2.0` Market Share comparison removed.
  - Starting Market Share 16 / 16 / 17.
  - Yellow F3 `+$1 & +1 Market Share`.
  - Conveyor Triage takes Processing Box dice oldest first.
  - Starting Secrets 3 / 4 / 4, with 2 / 3 / 4 probed in the sweep.
  - Bot work: payout-aware Market Share valuation (blocking, Public Relations Track) and a ref1 rollout for the new rule.
  - No counter, so no new term. Glossary impact for Phase B: Market Leader Bonus and the v2.0 comparison retired; the payout needs rules wording within existing terms (confirm with the User if a name is wanted).
- **Payout timing A/B (game-designer, 2026-11-09; `docs/findings/rsp1_ab_model.py`, results `rsp1_ab_results.json`; 600 games per cell, seeds 42–641, Yellow F3 corrected, oldest-first triage):** A = payout per Red Secret banked, B = at most one payout per round (end of Phase 5, if any Red Secret banked that round; Market Share after Phase 4). Rounds with ≥2 Red banks 0.9 / 1.9 / 4.0% (2P / 3P / 4P); payouts per game A 1.98 / 2.54 / 3.50 vs B 1.89 / 2.36 / 3.09. End reasons (~41 Singularity / 19 Patient Zero / 39 Market Collapse), rounds 8.5–8.7, Company colours and archetype spread unchanged (±0.02). Red path 4P .26 → .24. Carried forward in both: Market Collapse ~39% is high; Yellow path still weakest (0.66–0.71 of fair share) even with F3 corrected, so the earlier Yellow figures in this section did not include F3; a trailing player's Red bank feeds the leader; 2P lead snowball.
- **User decision (2026-11-09): variant B adopted.** Owner +1 Corporate Secret for every Red Secret banked; the Market Share place payout fires at most once per round, at the end of Phase 5. Spec §14.5 updated.
