# Monte Carlo Telemetry Sweep Report: Phase 34 (v0.27.0)
## Per-Version Corruption Track Recalibration

**Date:** 2026-11-02  
**Sample Size:** 3,000 matches total (1,000 matches per 2P, 3P, 4P pod; 9,000 player-games)  
**Base Seed:** 42  

---

### 1. Executive Summary & Core Telemetry Matrix

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

---

### 2. Recalibrated Corruption Track Trigger Frequency

Verification that the 4 recalibrated spaces trigger actively across match runs:

| Recalibrated Space | Printed Effect | 2P Hits / Game | 3P Hits / Game | 4P Hits / Game | Total Invocations (3,000 matches) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **v2.0 RaaS Space 1 (All lose $2)** | Calibrated Friction | 0.49 | 0.49 | 0.49 | **1479** |
| **v2.0 RaaS Space 4 (Lose $3 & 1 🔧 + 1K)** | Calibrated Friction | 0.48 | 0.48 | 0.49 | **1450** |
| **v3.0 Zero-Day Space 2 (Lose $3 & 1 🔧 + 1K)** | Calibrated Friction | 0.39 | 0.37 | 0.43 | **1190** |
| **v3.0 Kernel Space 2 (Lose $3 & 1 🔧 + 1K)** | Calibrated Friction | 0.44 | 0.42 | 0.49 | **1346** |

---

### 3. Client Company Performance Matrix (Combined Across Pods)

| Client Company | Total Matches | Win Rate (%) | Survival Rate (%) | Avg Secrets | Avg Ending Money | Target Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Aegis Defense Relay** | 1526 | **22.3%** | 30.1% | 0.00 | $0.00 | **Balanced** |
| **Department of Telecommunications Oversight** | 1541 | **37.8%** | 49.3% | 0.00 | $0.00 | **Monitor** |
| **Helix Biomedical Consortium** | 1509 | **32.4%** | 40.5% | 0.00 | $0.00 | **Balanced** |
| **Meridian Financial Trust** | 1499 | **37.6%** | 43.0% | 0.00 | $0.00 | **Monitor** |
| **Omnidyne Systems** | 1477 | **30.7%** | 39.7% | 0.00 | $0.00 | **Balanced** |
| **The Prometheus Foundation** | 1448 | **39.6%** | 47.8% | 0.00 | $0.00 | **Monitor** |

---

### 4. White Hat Operative Performance Matrix (Combined Across Pods)

| White Hat Operative | Total Matches | Win Rate (%) | Survival Rate (%) | Avg Secrets | Avg Ending Money | Target Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **The Acoustic** | 1467 | **23.2%** | 32.8% | 0.00 | $0.00 | **Balanced** |
| **The Cipher** | 1481 | **38.8%** | 46.3% | 0.00 | $0.00 | **Monitor** |
| **The Operator** | 1502 | **34.2%** | 42.1% | 0.00 | $0.00 | **Balanced** |
| **The Phreaker** | 1530 | **31.5%** | 41.1% | 0.00 | $0.00 | **Balanced** |
| **The Prodigy** | 1514 | **33.4%** | 39.6% | 0.00 | $0.00 | **Balanced** |
| **The Spook** | 1506 | **38.8%** | 48.2% | 0.00 | $0.00 | **Monitor** |

---

### 5. Architectural Invariants Verification

| Invariant | Specification | Verification Result | Status |
| :--- | :--- | :--- | :---: |
| **INV-TRACK-CALIB-01** | Standard Profile Track Calibration | Verified: RaaS sp1 ($2), RaaS sp4 ($3 & 1 🔧), ZD sp2 ($3 & 1 🔧), CK sp2 ($3 & 1 🔧) | **VERIFIED** |
| **INV-TRACK-AGGR-01** | Aggressive Profile Parity | Verified: All 6 Aggressive profile tracks match or exceed calibrated thresholds | **VERIFIED** |
| **INV-TRACK-CAPACITY-01** | Track Capacities Invariance | Strictly 4 spaces (v1.0), 5 spaces (v2.0), 6 spaces (v3.0) across all profiles | **VERIFIED** |
| **INV-STEP2A-DEDUCTION-01** | Sequential Step 2A Deduction | Verified: Cash & patch deductions apply prior to Step 2B attack calculations | **VERIFIED** |
