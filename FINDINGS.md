# Rogue Agent — Monte Carlo Simulation Findings & Balance Index

This document tracks verified balance takeaways, bot meta equilibria, card tiering, and active tuning targets for Rogue Agent.

> [!NOTE] Historical Archives
> Full statistical datasets, raw telemetry tables, and sweep outputs are archived in:
> - [docs/findings/v0.2_to_v0.7_historical_sweeps.md](docs/findings/v0.2_to_v0.7_historical_sweeps.md): Core economy, starting resources, 2P buffers, and contractor tuning.
> - [docs/findings/v0.8_to_v0.9_variant_and_archetype_sweeps.md](docs/findings/v0.8_to_v0.9_variant_and_archetype_sweeps.md): Choice faces, 15 Module Variants (★), Asymmetric Payloads, and Consultancy Archetypes.

---

## 1. Executive Summary & Active Baseline (`v0.9.0`)

| Parameter | Current Baseline | Healthy Game Target | Balance Status |
| :--- | :--- | :--- | :--- |
| **Match Duration** | 5.8 – 6.6 rounds | 8–11 rounds target / $\ge 5.5$ min | **Healthy** (No Turn 2–4 blowouts; 0.0% sub-4 round collapse). |
| **Singularity Rate** | ~10.0% – 16.0% | 10%–25% | **Healthy** (Acts as an authentic existential clock across all pods). |
| **2P Total Wipeout** | 4.8% – 9.2% | $< 15\%$ | **Resolved** (Reduced from 54.0% via 2P payload scaling & starting 🔧 buffer). |
| **Dominant Archetype** | Pod A: ~34%–44% | $\le 38\%$ ceiling | **Controlled** (VentureGreed checked via progressive contractor pricing). |
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
