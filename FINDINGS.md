# Rogue Agent — Monte Carlo Simulation Findings & Balance Index

This document tracks verified balance takeaways, bot meta equilibria, card tiering, and active tuning targets for Rogue Agent.

> [!NOTE] Historical Archives
> Full statistical datasets, raw telemetry tables, and sweep outputs are archived in:
> - [docs/findings/v0.2_to_v0.7_historical_sweeps.md](docs/findings/v0.2_to_v0.7_historical_sweeps.md): Core economy, starting resources, 2P buffers, and contractor tuning.
> - [docs/findings/v0.8_to_v0.9_variant_and_archetype_sweeps.md](docs/findings/v0.8_to_v0.9_variant_and_archetype_sweeps.md): Choice faces, 15 Module Variants (★), Asymmetric Payloads, and Consultancy Archetypes.

---

## 1. Executive Summary & Active Baseline (`v0.9.1`)

| Parameter | Current Baseline | Healthy Game Target | Balance Status |
| :--- | :--- | :--- | :--- |
| **Match Duration** | 4.8 – 7.8 rounds | 4.5–9.0 rounds target | **Healthy** (Zero 20+ round stalls; 0.0% round-limit timeouts). |
| **Singularity Rate** | 16.2% – 35.1% | 10%–40% | **Healthy** (Acts as an authentic existential clock across all pods). |
| **2P Total Wipeout** | 17.1% | $< 20\%$ | **Controlled** (High-intensity late-game duels). |
| **Zero-Total-Exit Rounds** | 0.32% – 0.40% | $< 1.0\%$ | **Breakthrough** (Tower Priming virtually eliminates empty drops). |
| **Buffer Overflows / Game** | 0.01 – 0.02 | $\le 0.05$ | **Ideal Backstop** (Invisible emergency safety valve). |
| **Consultancy Parity** | 5 / 6 balanced | $16.7\% \pm 6\%$ win rate | **Balanced** (Cipher retuned with $2 discount ceiling; Operator, Prodigy, Phreaker, Acoustic, Spook within target). |

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
