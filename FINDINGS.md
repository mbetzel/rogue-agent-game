# Rogue Agent — Monte Carlo Simulation Findings & Balance Index

This document tracks verified balance takeaways, bot meta equilibria, card tiering, and active tuning targets for Rogue Agent.

> [!NOTE] Historical Archives
> Full statistical datasets, raw telemetry tables, and sweep outputs are archived in:
> - [docs/findings/v0.2_to_v0.7_historical_sweeps.md](docs/findings/v0.2_to_v0.7_historical_sweeps.md): Core economy, starting resources, 2P buffers, and contractor tuning.
> - [docs/findings/v0.8_to_v0.9_variant_and_archetype_sweeps.md](docs/findings/v0.8_to_v0.9_variant_and_archetype_sweeps.md): Choice faces, 15 Module Variants (★), Asymmetric Payloads, and Consultancy Archetypes.

---

## 1. Executive Summary & Active Baseline (`v0.12.0`)

| Parameter | Current Baseline | Healthy Game Target | Balance Status |
| :--- | :--- | :--- | :--- |
| **Match Duration** | 7.2 – 8.7 rounds | ~8.0 rounds across all pods | **Pacing Parity** (2P: 7.6 rds, 3P: 8.7 rds, 4P: 7.2 rds; 0.0% stalls). |
| **Singularity Rate** | 21.4% – 29.8% | 10%–40% | **Healthy Existential Clock** across all pods. |
| **2P Total Wipeout** | 20.9% | $\le 20\%$ | **Controlled Duel Risk** (High-intensity late-game finish). |
| **4P Total Wipeout** | 3.8% | $< 5\%$ | **Safe** (Multi-player simultaneous wipeouts rare in 4P). |
| **Early Deaths ($\le$ R4)** | 0.6% – 3.8% | $< 5.0\%$ | **Zero Opening Blowouts** across all player counts. |
| **Zero-Total-Exit Rounds** | 0.32% – 0.40% | $< 1.0\%$ | **Breakthrough** (Tower Priming virtually eliminates empty drops). |
| **Buffer Overflows / Game** | 0.01 – 0.02 | $\le 0.05$ | **Ideal Backstop** (Invisible emergency safety valve). |
| **Active Infrastructure Valuation** | 0 VP for Unpatched | Technical debt penalty | **Resolved Stranded Cash** (Maintenance conversion active across 39%–43% of survivors). |
| **Push-Your-Luck Glitch Risk** | Face 5 Glitch on Red/Blue/Green | Broken block saturation | **Calibrated Risk** (Contractor sacrifice & Phase 1 Debug unlock utility). |
| **Consultancy Parity** | 6 / 6 balanced | $16.7\% \pm 6\%$ win rate | **Balanced** (Prodigy at 14.8%, Operator at 33.5%, Phreaker at 45.1%). |

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
