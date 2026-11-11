# Phase 52 Validation Report: Secret Simplification (`v0.38e`)

**Date:** 2026-11-11  
**Config Preset:** `v038e_roster` (roster `mixed1`: 1 `MixedPolicyBot` seat at `seed % P` + standard archetype rotation)  
**Spec Reference:** `docs/specs/v380e_secret_simplification_spec.md`  
**Seeds:** 42 – 1241 (1,200 games per player count; 3,600 games total)  

---

## 1. Executive Summary & Guardrail Compliance

| Guardrail / Target | Target Value | 2 Players | 3 Players | 4 Players | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Game Length** | 8.5 – 9.5 rounds | **8.84** | **9.00** | **9.04** | **PASS** |
| **Total Wipeout Rate** | $\le 3.0\%$ | **1.58%** | **0.58%** | **0.25%** | **PASS** |
| **Patient Zero Rate** | 15% – 35% | **17.92%** | **28.67%** | **28.42%** | **PASS** |
| **Singularity Rate** | 30% – 50% | **37.25%** | **44.67%** | **45.92%** | **PASS** |
| **Market Collapse Rate** | 15% – 45% | **43.25%** | **26.08%** | **25.42%** | **PASS** |
| **Red Secret Yield Invariant** | Exactly 2 | **100% (3,878/3,878)** | **100% (4,119/4,119)** | **100% (5,339/5,339)** | **PASS** |
| **Green Secret Yield Invariant** | Exactly 2 | **100% (2,666/2,666)** | **100% (4,090/4,090)** | **100% (5,707/5,707)** | **PASS** |
| **Purple Secret Yield Invariant** | Exactly 1 | **100% (3,687/3,687)** | **100% (5,523/5,523)** | **100% (7,397/7,397)** | **PASS** |
| **Blue Secret Yield Invariant** | Exactly {2, 3} | **100% (1,859/1,859)** | **100% (2,562/2,562)** | **100% (3,625/3,625)** | **PASS** |

All primary balance guardrails and telemetry invariants passed with zero regressions.

---

## 2. Pacing & End Trigger Distribution

| Metric | 2 Players (1,200 games) | 3 Players (1,200 games) | 4 Players (1,200 games) | Aggregate |
| :--- | :--- | :--- | :--- | :--- |
| **Mean Rounds** | 8.844 | 9.000 | 9.037 | **8.960** |
| **Singularity Trigger** | 37.25% (447) | 44.67% (536) | 45.92% (551) | **42.61%** |
| **Market Collapse Trigger** | 43.25% (519) | 26.08% (313) | 25.42% (305) | **31.58%** |
| **Patient Zero Trigger** | 17.92% (215) | 28.67% (344) | 28.42% (341) | **25.00%** |
| **Total Wipeout Trigger** | 1.58% (19) | 0.58% (7) | 0.25% (3) | **0.81%** |
| **Breach Rate (Any PZ)** | 19.50% | 29.92% | 29.25% | **26.22%** |

Pacing sits firmly inside the 8.5–9.5 round target window across all player counts. Total Wipeout frequency is under 1% in 3P and 4P, and safely below the 3.0% threshold in 2P.

---

## 3. Win Rate Dynamics

### 3.1 Company Color Win Rates
| Company Color | 2 Players (Base 50%) | 3 Players (Base 33.3%) | 4 Players (Base 25.0%) |
| :--- | :--- | :--- | :--- |
| **Green** | 56.30% | 40.80% | 31.24% |
| **Red** | 48.55% | 27.54% | 21.11% |
| **Blue** | 45.04% | 31.20% | 22.45% |

### 3.2 Dominant Color Path Win Rates
| Path ($\ge 60\%$ Dice Owned) | 2 Players | 3 Players | 4 Players |
| :--- | :--- | :--- | :--- |
| **Green** | 63.30% | 45.64% | 37.56% |
| **Red** | 54.34% | 31.55% | 20.33% |
| **Blue** | 43.75% | 37.07% | 26.69% |
| **Mixed** | 47.22% | 33.07% | 24.74% |
| **Yellow** | 42.78% | 26.54% | 20.22% |

### 3.3 Archetype Win Rates
| Archetype | 2 Players | 3 Players | 4 Players |
| :--- | :--- | :--- | :--- |
| **AdaptiveBalancedBot** | 68.05% | 54.31% | 40.50% |
| **SecOpsTurtleBot** | 56.10% | 45.65% | 36.11% |
| **MixedPolicyBot** | 50.25% | 31.00% | 24.33% |
| **VentureGreedBot** | 47.06% | 26.10% | 19.97% |
| **AccelerationistBot** | 45.45% | 32.98% | 21.52% |
| **RecklessSaboteurBot** | 31.97% | 13.86% | 7.99% |

---

## 4. Secret Face Banking & Yield Telemetry

### 4.1 Secret Yield Distributions Across All Games
Total banked dice analyzed across all 3,600 games: **40,473 banking events**.

| Color | Banked Events | Yield = 1 | Yield = 2 | Yield = 3 | Invariant Check |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Red** | 13,336 | 0 (0.0%) | **13,336 (100.0%)** | 0 (0.0%) | `INV-V38E-05` **VALIDATED** |
| **Green** | 12,463 | 0 (0.0%) | **12,463 (100.0%)** | 0 (0.0%) | `INV-V38E-04` **VALIDATED** |
| **Purple** | 16,607 | **16,607 (100.0%)** | 0 (0.0%) | 0 (0.0%) | `INV-V38E-06` **VALIDATED** |
| **Blue** | 8,046 | 0 (0.0%) | **7,417 (92.18%)** | **629 (7.82%)** | `INV-V38E-01/02` **VALIDATED** |

### 4.2 Blue Defense Grid L3+ Trigger Frequency
Blue dice yield 2 Corporate Secrets by default, and 3 Corporate Secrets if Defense Grid $\ge \text{Level 3}$:
- **2 Players:** 118 of 1,859 Blue banks (**6.35%**) triggered the L3+ bonus.
- **3 Players:** 211 of 2,562 Blue banks (**8.24%**) triggered the L3+ bonus.
- **4 Players:** 300 of 3,625 Blue banks (**8.28%**) triggered the L3+ bonus.
- **Total:** 629 of 8,046 Blue banks (**7.82%**) achieved Level 3+ grid status at time of banking.

### 4.3 Green Triage Slot Cleaning Telemetry
Under `v0.38e`, every Green bank cleans 1 glitched shield slot:
- **2 Players:** 0.914 slots cleaned per seat via Green triage (vs 1.111 Green banked per seat $\implies$ **82.3%** slot clean efficiency when glitched slots were present).
- **3 Players:** 0.949 slots cleaned per seat via Green triage (vs 1.136 Green banked per seat $\implies$ **83.5%** slot clean efficiency).
- **4 Players:** 1.020 slots cleaned per seat via Green triage (vs 1.189 Green banked per seat $\implies$ **85.8%** slot clean efficiency).

---

## 5. Summary & Sign-off Recommendation

The `v0.38e` Secret Simplification model is fully validated:
1. **Mental Overhead Eliminated:** Players no longer track intra-round Blue cubes blocked, nor calculate Green penalties against glitched shield slots.
2. **Stable Economy:** Average rounds (8.96) remain perfectly locked within the target window (8.5–9.5).
3. **Guardrails Intact:** Total Wipeout rate is minimal (0.81% aggregate), and all 4 color telemetry invariants hold at 100% fidelity across 40,473 banking events.
4. **Recommendation:** Sign off Phase 52 as ready for merge and integration into `RULES.md`.
