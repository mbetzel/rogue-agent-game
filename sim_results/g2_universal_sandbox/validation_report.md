# Phase 50 Monte Carlo Validation Report: `G2 — Universal Sandbox`

- **Baseline Config:** `GameConfig.v038c` (`V038_DRAFT` variant profile, `mixed1` roster rule with `MixedPolicyBot` at `seed % P`)
- **Sweep Matrix:** 24 cells (`2P / 3P / 4P` $\times$ `STANDARD / AGGRESSIVE` corruption profiles $\times$ `RANDOM / G1 / G2 / G3` Green market variant modes)
- **Sample Size:** `600` games per cell (`14,400` total games), explicit synchronized base seed `seed=42` (`seeds 42..641`)

---

## 1. End Trigger Distribution & Pacing (`v038c`, `seed=42..641`)

*Note: `PZ (Surv)` = Patient Zero with $\ge 1$ surviving operative; `TW` = simultaneous Total Wipeout (`is_total_wipeout=True`); `MC` = Market Collapse; `Sing` = Singularity (`v3.0` fills). Zero games hit the round limit (`0.0%`).*

| Profile | Pod | Green Card | Mean Rounds | Singularity | PZ (Surv) | Market Collapse | Total Wipeout |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **STANDARD** | **2P** | `RANDOM` | 8.41 | 42.0% | 18.7% | 36.3% | 3.0% |
| **STANDARD** | **2P** | `G1 ($5)` | 8.34 | 39.0% | 20.0% | 37.5% | 3.5% |
| **STANDARD** | **2P** | `G2 ($4)` | 8.39 | 42.7% | 18.5% | 35.5% | 3.3% |
| **STANDARD** | **2P** | `G3 ($4)` | 8.36 | 41.2% | 19.5% | 36.3% | 3.0% |
| **STANDARD** | **3P** | `RANDOM` | 8.29 | 44.3% | 34.3% | 20.8% | 0.5% |
| **STANDARD** | **3P** | `G1 ($5)` | 8.27 | 43.2% | 37.2% | 18.8% | 0.8% |
| **STANDARD** | **3P** | `G2 ($4)` | 8.32 | 45.8% | 33.0% | 21.0% | 0.2% |
| **STANDARD** | **3P** | `G3 ($4)` | 8.32 | 44.3% | 36.0% | 19.5% | 0.2% |
| **STANDARD** | **4P** | `RANDOM` | 8.31 | 48.3% | 35.2% | 16.5% | 0.0% |
| **STANDARD** | **4P** | `G1 ($5)` | 8.22 | 46.2% | 36.2% | 17.7% | 0.0% |
| **STANDARD** | **4P** | `G2 ($4)` | 8.38 | 49.5% | 33.5% | 17.0% | 0.0% |
| **STANDARD** | **4P** | `G3 ($4)` | 8.32 | 50.2% | 33.8% | 16.0% | 0.0% |
| **AGGRESSIVE** | **2P** | `RANDOM` | 8.31 | 40.7% | 22.5% | 35.0% | 1.8% |
| **AGGRESSIVE** | **2P** | `G1 ($5)` | 8.23 | 38.7% | 24.3% | 35.3% | 1.7% |
| **AGGRESSIVE** | **2P** | `G2 ($4)` | 8.30 | 39.7% | 23.0% | 35.2% | 2.2% |
| **AGGRESSIVE** | **2P** | `G3 ($4)` | 8.32 | 40.5% | 21.7% | 36.0% | 1.8% |
| **AGGRESSIVE** | **3P** | `RANDOM` | 8.19 | 43.2% | 36.3% | 19.8% | 0.7% |
| **AGGRESSIVE** | **3P** | `G1 ($5)` | 8.17 | 41.8% | 38.3% | 18.7% | 1.2% |
| **AGGRESSIVE** | **3P** | `G2 ($4)` | 8.24 | 45.3% | 35.3% | 18.7% | 0.7% |
| **AGGRESSIVE** | **3P** | `G3 ($4)` | 8.30 | 45.0% | 34.8% | 19.3% | 0.8% |
| **AGGRESSIVE** | **4P** | `RANDOM` | 8.30 | 45.8% | 37.3% | 16.8% | 0.0% |
| **AGGRESSIVE** | **4P** | `G1 ($5)` | 8.26 | 43.3% | 38.8% | 17.5% | 0.3% |
| **AGGRESSIVE** | **4P** | `G2 ($4)` | 8.33 | 46.5% | 38.3% | 15.2% | 0.0% |
| **AGGRESSIVE** | **4P** | `G3 ($4)` | 8.27 | 46.8% | 36.7% | 16.5% | 0.0% |

---

## 2. Green Die Purchase Rate, Buyer Win Rate & Starting Company Parity

| Profile | Pod | Green Card | Green Buys / Seat | Seats Buying $\ge 1$ Green | Green Buyer Win Rate | Starting Company Win Rate (Red / Blue / Green) | Omnidyne / Helix Win Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **STANDARD** | **2P** | `RANDOM` | 0.35 | 21.2% | 51.2% | 54.4% / 47.2% / 48.6% | 45.0% / 52.2% |
| **STANDARD** | **2P** | `G1 ($5)` | 0.20 | 12.6% | 46.4% | 51.8% / 49.9% / 48.4% | 44.5% / 52.2% |
| **STANDARD** | **2P** | `G2 ($4)` | **0.40** | **24.2%** | **49.1%** | 55.1% / 45.9% / **49.1%** | **48.0% / 50.2%** |
| **STANDARD** | **2P** | `G3 ($4)` | 0.44 | 25.4% | 51.1% | 54.1% / 44.9% / 51.1% | 48.5% / 53.7% |
| **STANDARD** | **3P** | `RANDOM` | 0.39 | 22.6% | 35.7% | 33.3% / 33.4% / 33.2% | 31.8% / 34.8% |
| **STANDARD** | **3P** | `G1 ($5)` | 0.25 | 15.2% | 32.5% | 32.6% / 34.9% / 32.4% | 31.1% / 33.8% |
| **STANDARD** | **3P** | `G2 ($4)` | **0.44** | **25.6%** | **35.4%** | 32.5% / 33.1% / **34.4%** | **34.3% / 34.4%** |
| **STANDARD** | **3P** | `G3 ($4)` | 0.51 | 28.4% | 36.1% | 32.3% / 32.8% / 34.8% | 34.0% / 35.8% |
| **STANDARD** | **4P** | `RANDOM` | 0.49 | 26.9% | 26.5% | 25.4% / 21.8% / 27.7% | 26.7% / 28.7% |
| **STANDARD** | **4P** | `G1 ($5)` | 0.29 | 17.0% | 20.4% | 24.7% / 23.9% / 26.3% | 26.2% / 26.4% |
| **STANDARD** | **4P** | `G2 ($4)` | **0.54** | **29.9%** | **27.1%** | 24.7% / 24.2% / **26.1%** | **26.2% / 25.9%** |
| **STANDARD** | **4P** | `G3 ($4)` | 0.64 | 34.1% | 26.9% | 24.9% / 23.5% / 26.5% | 26.5% / 26.4% |
| **AGGRESSIVE** | **2P** | `RANDOM` | 0.32 | 19.8% | 51.0% | 53.8% / 46.7% / 49.6% | 48.5% / 50.7% |
| **AGGRESSIVE** | **2P** | `G1 ($5)` | 0.18 | 11.7% | 50.0% | 53.8% / 49.4% / 46.9% | 45.5% / 48.3% |
| **AGGRESSIVE** | **2P** | `G2 ($4)` | **0.36** | **23.1%** | **48.4%** | 52.8% / 47.4% / **49.9%** | **51.0% / 48.8%** |
| **AGGRESSIVE** | **2P** | `G3 ($4)` | 0.41 | 24.8% | 51.3% | 53.1% / 46.2% / 50.9% | 51.0% / 50.7% |
| **AGGRESSIVE** | **3P** | `RANDOM` | 0.36 | 21.4% | 35.3% | 31.8% / 35.1% / 33.1% | 31.8% / 34.4% |
| **AGGRESSIVE** | **3P** | `G1 ($5)` | 0.22 | 13.3% | 35.0% | 30.7% / 37.4% / 31.8% | 30.5% / 33.1% |
| **AGGRESSIVE** | **3P** | `G2 ($4)` | **0.41** | **25.3%** | **34.7%** | 31.1% / 36.1% / **32.7%** | **34.3% / 31.1%** |
| **AGGRESSIVE** | **3P** | `G3 ($4)` | 0.48 | 28.4% | 37.5% | 31.1% / 33.8% / 35.0% | 34.9% / 35.1% |
| **AGGRESSIVE** | **4P** | `RANDOM` | 0.44 | 24.9% | 23.1% | 26.1% / 23.3% / 25.6% | 23.8% / 27.5% |
| **AGGRESSIVE** | **4P** | `G1 ($5)` | 0.25 | 15.2% | 17.8% | 25.3% / 23.9% / 25.7% | 23.8% / 27.7% |
| **AGGRESSIVE** | **4P** | `G2 ($4)` | **0.50** | **29.2%** | **24.5%** | 24.6% / 24.7% / **25.7%** | **26.2% / 25.2%** |
| **AGGRESSIVE** | **4P** | `G3 ($4)` | 0.57 | 31.9% | 26.1% | 25.7% / 24.2% / 25.1% | 23.3% / 27.0% |

---

## 3. Phase 3 `G2 — Universal Sandbox` Yield Telemetry (`2 + g` 🔬)

| Profile | Pod | Mode | Total `G2` Activations | `G2` Activations / Game | Mean Research / Activation | Mean Active Glitch Slots ($g$) | PMF: $g=0$ (`2 🔬`) | PMF: $g=1$ (`3 🔬`) | PMF: $g=2$ (`4 🔬`) | PMF: $g \ge 3$ (`5+ 🔬`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **STANDARD** | **2P** | `RANDOM` | 257 | 0.43 | **2.60 🔬** | 0.60 | 55.6% | 30.4% | 12.1% | 1.9% |
| **STANDARD** | **2P** | `G2` | 644 | 1.07 | **2.61 🔬** | 0.61 | 55.6% | 29.8% | 13.0% | 1.6% |
| **STANDARD** | **3P** | `RANDOM` | 375 | 0.63 | **2.51 🔬** | 0.51 | 60.0% | 30.7% | 7.5% | 1.9% |
| **STANDARD** | **3P** | `G2` | 1,101 | 1.84 | **2.56 🔬** | 0.56 | 57.5% | 30.6% | 10.5% | 1.4% |
| **STANDARD** | **4P** | `RANDOM` | 584 | 0.97 | **2.61 🔬** | 0.61 | 55.3% | 30.3% | 12.8% | 1.5% |
| **STANDARD** | **4P** | `G2` | 1,655 | 2.76 | **2.60 🔬** | 0.60 | 55.1% | 30.7% | 13.1% | 1.1% |
| **AGGRESSIVE** | **2P** | `RANDOM` | 235 | 0.39 | **2.84 🔬** | 0.84 | 50.6% | 20.0% | 24.7% | 4.7% |
| **AGGRESSIVE** | **2P** | `G2` | 616 | 1.03 | **2.83 🔬** | 0.83 | 48.9% | 23.7% | 23.1% | 4.4% |
| **AGGRESSIVE** | **3P** | `RANDOM` | 366 | 0.61 | **2.77 🔬** | 0.77 | 51.4% | 25.1% | 19.4% | 4.1% |
| **AGGRESSIVE** | **3P** | `G2` | 1,047 | 1.75 | **2.81 🔬** | 0.81 | 47.4% | 27.5% | 22.0% | 3.2% |
| **AGGRESSIVE** | **4P** | `RANDOM` | 536 | 0.89 | **2.81 🔬** | 0.81 | 47.0% | 28.7% | 20.9% | 3.4% |
| **AGGRESSIVE** | **4P** | `G2` | 1,603 | 2.67 | **2.85 🔬** | 0.85 | 45.7% | 27.8% | 23.1% | 3.4% |

*Key Insight:* Empirical `G2` activations yield **2.56–2.61 🔬** in Standard and **2.81–2.85 🔬** in Aggressive (exceeding the unconditional round average of `2.21 / 2.35 🔬` because Green market dice accumulate by mid/late game and bots preferentially keep `G2` on rerolls when $g \ge 1$). At the same time, **$45.7\%–60.0\%$ of all realized `G2` triggers occur at $g=0$**, confirming that the `+2 🔬` base is indispensable to prevent blank-face rolls.

---

## 4. Outlier Seeds (`seed=42..641`)

- **Shortest Games:**
  - **2P (1 Round, `patient_zero`):** `seed=87`, `seed=494`, `seed=579`
  - **3P (2 Rounds, `patient_zero`):** `seed=52`, `seed=57`, `seed=72`
  - **4P (2 Rounds, `patient_zero`):** `seed=72`, `seed=148`, `seed=239`
- **Longest Games (11 Rounds, `singularity`, zero round-limit timeouts):**
  - **2P:** `seed=572`, `seed=588`, `seed=622` (Standard); `seed=576`, `seed=578`, `seed=588` (Aggressive)
  - **3P:** `seed=610`, `seed=617`, `seed=627`, `seed=638` (Standard); `seed=599`, `seed=617`, `seed=638` (Aggressive)
  - **4P:** `seed=583`, `seed=591`, `seed=630` (Standard); `seed=597`, `seed=627`, `seed=630` (Aggressive)
- **Representative Total Wipeout Seeds:**
  - **2P (`G2` Standard):** `seed=45`, `seed=64`, `seed=87`, `seed=108`, `seed=179`
  - **3P (`G2` Standard):** `seed=282` (only 1 game in 600, `0.2%`)
  - **4P (`G2` Standard & Aggressive):** `0` Total Wipeouts across 1,200 games (`0.0%`)
