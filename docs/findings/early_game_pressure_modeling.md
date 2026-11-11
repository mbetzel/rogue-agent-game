# Pre-SDLC Modeling Analysis: Early-Game Tutorializing Pressure under the Shogun Baffle Tower

**Author:** Game Designer (Pre-SDLC Exploration)  
**Status:** Pre-SDLC Analysis & Recommendations Complete (Ready for User Review)  
**Reference Candidates:** Baseline (`v038c` with `SHOGUN_BAFFLE`), Options A1/A2/A3, Options B1/B2, Options C1/C2  
**Validation Suite:** 400,000 Monte Carlo Tower Drops (50,000/candidate) + 12,000 Full-Game `GameEngine` Matches (500 runs $\times$ 3 player counts [3P, 2P, 4P] $\times$ 8 candidates)

---

## 1. Executive Summary & Core Design Verdict

### The Design Challenge
Under the physical `SHOGUN_BAFFLE` tower, the current baseline setup (`4` priming cubes `1R, 1B, 1G, 1K` + `3` starting `v1.0` cubes `1R, 1B, 1G` + `2` starting Shield Slots) produces an overly calm opening:
- In Round 1, only **1.93 Attack Cubes exit** the tower on average.
- With 2 active Shield Slots and 4 starting dice, players face a mere **28.4% probability of taking any damage**, with an expected unblocked damage of only **0.36 cubes**. Over **71.6% of players take zero damage** on Turn 1.
- Because early rounds exert virtually no existential pressure, players effortlessly tech up without compromise. Games routinely drag out to **10.06 rounds (3P) / 9.87 rounds (2P)**, and endings are overwhelmingly monopolized by **Singularity (73.0% in 3P / 63.4% in 2P)**, while Patient Zero eliminations wither to just 12–17%.

The User requested an early-game mechanism that **tutorializes players right from Round 1** by applying **just a little extra pressure—a bit more than they can comfortably handle**—forcing meaningful decisions between defense/cleaning vs. economy/Secret banking, while returning full-game pacing to the **8.5–9.5 round design target**.

### The Verdict: Rank-Ordered Recommendations

```
+-------------------------------------------------------------------------------------------------------------------------+
| Rank | Candidate | Mechanics                                      | R1 Unb (2 sh) | Mean Rds (3P) | Sing % | Verdict    |
+-------------------------------------------------------------------------------------------------------------------------+
|  1   |    C2     | 4 Prime + 4 Cup (2R,1B,1G) + 1 Start Glitch    | 1.02 cubes    |  9.48 rounds  | 52.4%  | RECOMMENDED|
|  2   |    A1     | 7 Prime (2R,2B,2G,1K) + 4 Cup (2R,1B,1G)       | 1.62 cubes    |  8.77 rounds  | 40.0%  | RUNNER-UP  |
|  3   |    B1     | 4 Prime + 5 Cup (2R,2B,1G)                     | 1.78 cubes    |  8.62 rounds  | 38.0%  | VIABLE     |
|  4   |    C1     | 4 Prime + 3 Cup (1R,1B,1G) + 1 Start Glitch    | 0.36 (1.01/1s)|  9.98 rounds  | 69.8%  | UNDERPOWER |
|  5   |    B2     | 4 Prime + 6 Cup (2R,2B,2G)                     | 2.38 cubes    |  8.83 rounds  | 39.0%  | HARSH      |
|  6   |    A2     | 7 Prime + 5 Cup (2R,2B,1G)                     | 2.32 cubes    |  7.66 rounds  | 23.4%  | REJECTED   |
|  7   |    A3     | 8 Prime (2R,2B,2G,2K) + 5 Cup (2R,2B,1G)       | 2.30 cubes    |  7.85 rounds  | 28.2%  | REJECTED   |
+-------------------------------------------------------------------------------------------------------------------------+
```

1. **PRIMARY RECOMMENDATION: Candidate C2 (Hybrid: `4` Prime + `4` Cup [`2R, 1B, 1G`] + `1` Starting Glitched Shield Slot)**
   - **Perfect Tutorialization:** Starting with 1 Glitched Shield Slot immediately teaches both flagship mechanics of v0.38 on Turn 1: spending a shield die in Phase 1 Step 5 to clean the slot vs. waiting for a die to graduate out of the CI/CD Pipeline in Phase 5 Step 3b to repair it for free.
   - **Triage Pressure Without Trauma:** Exits **2.88 Attack Cubes** in Round 1. A player committing 2 shields (1 cleaning + 1 blocking) expects **1.02 unblocked cubes** (62.1% leak chance). A player saving dice for income expects **1.90 unblocked cubes** (87.6% leak chance). The player *must* prioritize which threat color (Red Market Share, Blue Secrets, Green Glitches) to absorb.
   - **Pacing & Triggers Restored:** Mean game length drops to **9.48 rounds (3P) / 9.06 rounds (2P) / 9.25 rounds (4P)**, resting squarely inside the **8.5–9.5 round target**. End triggers achieve healthy, dramatic balance: Singularity **52.4%**, Patient Zero **20.0%**, Market Collapse **27.4%**, Total Wipeout **0.2%**.
   - **Preserves Shogun Baffle Physics:** Maintains a 41.3% Trapping Trough, 34.7% Avalanche, and 24.0% Empty distribution.

2. **RUNNER-UP: Candidate A1 (`7` Prime + `4` Cup)**
   - If starting the game with a pre-glitched slot is deemed undesirable by the User, **A1 is the best pure cube-pool tuning option**.
   - Pre-saturating the tower with 7 cubes leaves $\sim 2.1$ stuck cubes, allowing 4 starting attack cubes to produce **3.54 exited attack cubes** in Round 1 and pacing of **8.77 rounds (3P) / 8.40 rounds (2P)** with 40.0% Singularity and 27.6% PZ.
   - Trade-off: Requires players to count out and drop 7 priming cubes at setup instead of 4, and exerts slightly heavier Turn 1 blunt trauma (1.62 unblocked damage).

3. **DEFINITIVELY REJECTED: Candidates A2, A3, B1, B2**
   - **The Avalanche Cliff Catastrophe:** As proven mathematically in Section 2, dropping 5 or 6 attack cubes (+1 pulse) causes the Shogun mass threshold ($F + S \ge 7$) to trigger an immediate Avalanche on Round 1 in 76%–94% of games.
   - **Zero Trapping:** In A2, A3, B1, and B2, the tower's signature **Baffle Trapping Trough is completely wiped out (0.0% probability)**.
   - **Pacing Collapse:** In A2 and A3, game length collapses to **7.42–7.66 rounds**, Patient Zero eliminations spike to **42%–51%**, and breach rates surge past 17%, turning the tutorial opening into an unplayable meat-grinder.

---

## 2. Mathematical Modeling & Physics of the Shogun Baffle Tower

### 2.1 The Shogun Baffle State Equations
Under `SHOGUN_BAFFLE`, the tower state is governed by falling mass $F$ (incoming cubes) and resting reservoir $S$ (settled cubes on internal baffles):

$$\text{Regime}(F, S) = \begin{cases} 
\text{Empty} & \text{if } S = 0 \\
\text{Avalanche} & \text{if } S \ge 3 \text{ or } (F + S) \ge 7 \\
\text{Trapping} & \text{if } 1 \le S \le 2 \text{ and } (F + S) < 7 
\end{cases}$$

The corresponding exit probabilities $(p_{\text{fall}}, p_{\text{dislodge}})$ are:
- **Empty ($S=0$):** $p_{\text{fall}} = 0.70$, $p_{\text{dislodge}} = 0.0$ (no resting cubes to dislodge).
- **Sub-Avalanche Trapping ($1 \le S \le 2, F+S < 7$):**
  $$p_{\text{fall}} = \max(0.35, 0.70 - 0.15 \times S), \quad p_{\text{dislodge}} = 0.21$$
  - At $S=1$: $p_{\text{fall}} = 0.55, p_{\text{dislodge}} = 0.21$. Expected exits: $0.55 F + 0.21$.
  - At $S=2$: $p_{\text{fall}} = 0.40, p_{\text{dislodge}} = 0.21$. Expected exits: $0.40 F + 0.42$.
- **Avalanche Cascade ($S \ge 3$ or $F+S \ge 7$):**
  $$p_{\text{fall}} = 0.60, \quad p_{\text{dislodge}} = 0.70$$
  - Dislodgement probability jumps **3.33-fold** (from $0.21 \to 0.70$), cascading resting cubes into the tray.

### 2.2 Analytical Priming Reservoir Distributions ($S_1$)
At Setup Step 1, $N_{\text{prime}}$ cubes drop through an empty tower ($S_0=0$). Because each cube exits with probability $p=0.70$, the stuck reservoir $S_1$ follows a pure Binomial distribution: $S_1 \sim \text{Binomial}(N_{\text{prime}}, 0.30)$.

$$\begin{array}{|c|c|c|c|c|c|c|c|c|c|}
\hline
\textbf{Prime Size} & E[S_1] & P(S_1=0) & P(S_1=1) & P(S_1=2) & P(S_1=3) & P(S_1 \ge 1) & P(S_1 \ge 2) & P(S_1 \ge 3) \\
\hline
\mathbf{N=4 \text{ (Base, B, C)}} & \mathbf{1.20} & 24.01\% & 41.16\% & 26.46\% & 7.56\% & \mathbf{75.99\%} & \mathbf{34.83\%} & \mathbf{8.37\%} \\
\mathbf{N=7 \text{ (A1, A2)}} & \mathbf{2.10} & 8.24\% & 24.71\% & 31.77\% & 22.69\% & \mathbf{91.76\%} & \mathbf{67.06\%} & \mathbf{35.29\%} \\
\mathbf{N=8 \text{ (A3)}} & \mathbf{2.40} & 5.76\% & 19.77\% & 29.65\% & 25.41\% & \mathbf{94.24\%} & \mathbf{74.47\%} & \mathbf{44.82\%} \\
\hline
\end{array}$$

### 2.3 Proof of the Round 1 Avalanche Cliff Interaction ($F \ge 6$)
In Round 1, Phase 1 adds 1 Black pulse cube to the active version card's cup payload ($F = N_{\text{cup}} + 1$).
Consider the mass threshold condition $(F + S_1) \ge 7$:

1. **When $N_{\text{cup}} = 5$ (Option B1, A2, A3):**
   - Falling mass is $F = 5 + 1 = 6$ cubes.
   - The avalanche condition becomes:
     $$(F + S_1) \ge 7 \iff (6 + S_1) \ge 7 \iff S_1 \ge 1$$
   - Therefore, **any game where at least one priming cube stuck to the baffles triggers an immediate Avalanche!**
   - For a 4-cube prime (Option B1): $P(S_1 \ge 1) = 1 - (0.70)^4 = \mathbf{75.99\%}$.
   - What happens to the Trapping regime?
     $$\text{Trapping} \iff (1 \le S_1 \le 2) \land (F + S_1 < 7) \iff (1 \le S_1 \le 2) \land (6 + S_1 < 7) \iff S_1 < 1$$
     This is a strict contradiction ($S_1 \ge 1 \land S_1 < 1 = \emptyset$).
   - **Mathematical Conclusion:** In Option B1, the Trapping Trough probability is **identically 0.00%**. Option B completely breaks the tower's intended physical spectrum, converting it into a binary flip between Empty ($24.01\%$) and Avalanche ($75.99\%$).

2. **When $N_{\text{cup}} = 4$ (Candidate C2, Option A1):**
   - Falling mass is $F = 4 + 1 = 5$ cubes.
   - Avalanche condition: $(5 + S_1) \ge 7 \iff S_1 \ge 2$ (or $S_1 \ge 3$).
   - For Candidate C2 (4-cube prime):
     - $P(\text{Avalanche}) = P(S_1 \ge 2) = \mathbf{34.83\%}$.
     - $P(\text{Trapping}) = P(S_1 = 1) = \mathbf{41.16\%}$.
     - $P(\text{Empty}) = P(S_1 = 0) = \mathbf{24.01\%}$.
   - **Mathematical Conclusion:** Candidate C2 is the only elevated-cup option that **preserves the Trapping Trough as the modal outcome (41.16%)**, producing genuine kinetic variety rather than an inevitable avalanche.

---

## 3. High-Precision Round 1–4 Threat & Defense Curves

Data compiled from 400,000 Monte Carlo drops (50,000 drops per candidate).

### 3.1 Mean Exited Threat & Stuck Reservoir Across Rounds 1–4

$$\begin{array}{|l|cccc|cccc|}
\hline
\textbf{Candidate} & \multicolumn{4}{c|}{\textbf{Mean Exited Attack Cubes (R+B+G)}} & \multicolumn{4}{c|}{\textbf{Mean Stuck Reservoir } (S_t)} \\
& \textbf{R1} & \textbf{R2} & \textbf{R3} & \textbf{R4} & \textbf{R1} & \textbf{R2} & \textbf{R3} & \textbf{R4} \\
\hline
\text{Baseline} & 1.93 & 2.40 & 2.37 & 2.39 & 2.62 & 2.51 & 2.56 & 2.55 \\
\text{Option A1 (7p, 4c)} & 3.54 & 3.83 & 3.84 & 3.82 & 2.78 & 2.89 & 2.90 & 2.92 \\
\text{Option A2 (7p, 5c)} & 4.29 & 4.52 & 4.53 & 4.54 & 2.99 & 3.17 & 3.18 & 3.18 \\
\text{Option A3 (8p, 5c)} & 4.28 & 4.54 & 4.55 & 4.55 & 3.10 & 3.21 & 3.20 & 3.20 \\
\text{Option B1 (4p, 5c)} & 3.74 & 3.90 & 3.93 & 3.92 & 2.62 & 2.89 & 2.89 & 2.90 \\
\text{Option B2 (4p, 6c)} & 4.37 & 4.62 & 4.62 & 4.62 & 3.00 & 3.17 & 3.19 & 3.20 \\
\text{Option C1 (4p, 3c, 1g)} & 1.93 & 2.40 & 2.37 & 2.39 & 2.62 & 2.51 & 2.56 & 2.55 \\
\mathbf{\text{Option C2 (4p, 4c, 1g)}} & \mathbf{2.88} & \mathbf{3.13} & \mathbf{3.16} & \mathbf{3.15} & \mathbf{2.56} & \mathbf{2.72} & \mathbf{2.70} & \mathbf{2.73} \\
\hline
\end{array}$$

### 3.2 Round 1 Threat Regimes & Defense Leakage

$$\begin{array}{|l|cc|cc|cc|c|}
\hline
\textbf{Candidate} & \textbf{R1 Avalanche} & \textbf{R1 Trapping} & \mathbf{P(\text{Dmg} > 2)} & \mathbf{E[\text{Unb } | \text{ 2sh}]} & \mathbf{P(\text{Dmg} > 1)} & \mathbf{E[\text{Unb } | \text{ 1sh}]} & \mathbf{E[\text{Unb R2 } | \text{ 2sh}]} \\
\hline
\text{Baseline} & 8.4\% & 67.8\% & 28.4\% & 0.36 & 65.4\% & 1.01 & 0.72 \\
\text{Option A1} & 67.4\% & 24.6\% & 75.5\% & 1.62 & 92.6\% & 2.55 & 1.91 \\
\text{Option A2} & 91.9\% & 0.0\% & 89.6\% & 2.32 & 97.8\% & 3.30 & 2.55 \\
\text{Option A3} & 94.4\% & 0.0\% & 89.4\% & 2.30 & 97.7\% & 3.28 & 2.56 \\
\text{Option B1} & 75.8\% & 0.0\% & 84.5\% & 1.78 & 96.6\% & 2.75 & 1.95 \\
\text{Option B2} & 76.2\% & 0.0\% & 92.0\% & 2.38 & 98.5\% & 3.37 & 2.63 \\
\text{Option C1} & 8.4\% & 67.8\% & 28.4\% & 0.36 & \mathbf{65.4\%} & \mathbf{1.01} & 0.72 \\
\mathbf{\text{Option C2}} & \mathbf{34.7\%} & \mathbf{41.3\%} & \mathbf{62.1\%} & \mathbf{1.02} & \mathbf{87.6\%} & \mathbf{1.90} & \mathbf{1.29} \\
\hline
\end{array}$$

### 3.3 Round 1 Attack Cubes Exited Distribution (PMF %)

$$\begin{array}{|l|ccccccc|}
\hline
\textbf{Candidate} & \mathbf{k = 0} & \mathbf{k = 1} & \mathbf{k = 2} & \mathbf{k = 3} & \mathbf{k = 4} & \mathbf{k = 5} & \mathbf{k \ge 6} \\
\hline
\text{Baseline / C1} & 6.2\% & 28.4\% & 37.0\% & 23.8\% & 4.6\% & 0.0\% & 0.0\% \\
\text{Option C2} & \mathbf{1.6\%} & \mathbf{10.8\%} & \mathbf{25.5\%} & \mathbf{34.4\%} & \mathbf{20.9\%} & \mathbf{6.8\%} & \mathbf{0.0\%} \\
\text{Option A1} & 0.6\% & 6.8\% & 17.1\% & 28.2\% & 27.9\% & 16.3\% & 3.1\% \\
\text{Option B1} & 0.6\% & 2.8\% & 12.1\% & 27.8\% & 32.8\% & 19.3\% & 4.6\% \\
\text{Option A2} & 0.1\% & 1.3\% & 9.0\% & 21.6\% & 31.4\% & 24.2\% & 12.4\% \\
\text{Option B2} & 0.1\% & 1.4\% & 6.5\% & 19.7\% & 29.8\% & 26.2\% & 16.3\% \\
\hline
\end{array}$$

*Key Takeaway:* In Baseline, $k \le 2$ occurs in $71.6\%$ of drops (zero damage against 2 shields). In Candidate C2, $k \ge 3$ occurs in $62.1\%$ of drops, with modal exit at exactly $k=3$ ($34.4\%$). This delivers precisely the intended **"1 unblocked cube past a 2-shield defense"** tension.

---

## 4. Full-Game Balance Probes (12,000 Simulated Games)

Simulations executed on `v038c` using `mixed1` policy roster across seeds 3000..3499 (3P), 5000..5499 (2P), and 7000..7499 (4P).

### 4.1 3-Player Match Dynamics (500 games / candidate)

$$\begin{array}{|l|c|cccc|c|c|}
\hline
\textbf{Candidate} & \textbf{Mean Rds} & \textbf{Singularity} & \textbf{Patient Zero} & \textbf{Market Col} & \textbf{Total Wipe} & \textbf{Breach Rate} & \textbf{Win Secrets} \\
\hline
\text{Baseline} & 10.06 & 73.0\% & 17.6\% & 9.4\% & 0.0\% & 6.6\% & 18.71 \\
\text{Option A1} & 8.77 & 40.0\% & 27.6\% & 32.2\% & 0.2\% & 11.4\% & 16.07 \\
\text{Option A2} & 7.66 & 23.4\% & 42.2\% & 33.4\% & 1.0\% & 17.6\% & 13.05 \\
\text{Option A3} & 7.85 & 28.2\% & 38.4\% & 32.2\% & 1.2\% & 15.7\% & 13.46 \\
\text{Option B1} & 8.62 & 38.0\% & 32.4\% & 29.4\% & 0.2\% & 12.4\% & 14.96 \\
\text{Option B2} & 8.83 & 39.0\% & 31.2\% & 29.8\% & 0.0\% & 11.9\% & 14.67 \\
\text{Option C1} & 9.98 & 69.8\% & 19.6\% & 10.6\% & 0.0\% & 7.5\% & 18.21 \\
\mathbf{\text{Option C2}} & \mathbf{9.48} & \mathbf{52.4\%} & \mathbf{20.0\%} & \mathbf{27.4\%} & \mathbf{0.2\%} & \mathbf{7.7\%} & \mathbf{17.81} \\
\hline
\end{array}$$

### 4.2 2-Player Match Dynamics (500 games / candidate)

$$\begin{array}{|l|c|cccc|c|c|}
\hline
\textbf{Candidate} & \textbf{Mean Rds} & \textbf{Singularity} & \textbf{Patient Zero} & \textbf{Market Col} & \textbf{Total Wipe} & \textbf{Breach Rate} & \textbf{Win Secrets} \\
\hline
\text{Baseline} & 9.87 & 63.4\% & 12.6\% & 23.2\% & 0.8\% & 7.5\% & 18.36 \\
\text{Option A1} & 8.40 & 31.6\% & 18.8\% & 48.2\% & 1.4\% & 11.0\% & 16.16 \\
\text{Option A2} & 7.43 & 15.6\% & 31.2\% & 50.4\% & 2.8\% & 18.6\% & 13.07 \\
\text{Option A3} & 7.22 & 14.6\% & 30.6\% & 52.6\% & 2.2\% & 17.7\% & 12.71 \\
\text{Option B1} & 8.05 & 23.2\% & 25.2\% & 49.4\% & 2.2\% & 15.0\% & 14.70 \\
\text{Option B2} & 8.05 & 23.4\% & 23.6\% & 49.8\% & 3.2\% & 15.1\% & 14.17 \\
\text{Option C1} & 9.81 & 63.4\% & 13.8\% & 22.0\% & 0.8\% & 7.9\% & 18.06 \\
\mathbf{\text{Option C2}} & \mathbf{9.06} & \mathbf{43.0\%} & \mathbf{14.8\%} & \mathbf{41.2\%} & \mathbf{1.0\%} & \mathbf{8.6\%} & \mathbf{17.18} \\
\hline
\end{array}$$

### 4.3 4-Player Match Dynamics (500 games / candidate)

$$\begin{array}{|l|c|cccc|c|c|}
\hline
\textbf{Candidate} & \textbf{Mean Rds} & \textbf{Singularity} & \textbf{Patient Zero} & \textbf{Market Col} & \textbf{Total Wipe} & \textbf{Breach Rate} & \textbf{Win Secrets} \\
\hline
\text{Baseline} & 9.93 & 71.0\% & 19.6\% & 9.4\% & 0.0\% & 6.0\% & 19.71 \\
\text{Option A1} & 8.70 & 40.6\% & 29.4\% & 30.0\% & 0.0\% & 8.8\% & 16.61 \\
\text{Option A2} & 7.42 & 25.0\% & 49.4\% & 25.6\% & 0.0\% & 15.0\% & 13.76 \\
\text{Option A3} & 7.21 & 25.4\% & 51.0\% & 23.4\% & 0.2\% & 16.7\% & 13.27 \\
\text{Option B1} & 8.62 & 35.2\% & 38.2\% & 26.6\% & 0.0\% & 11.0\% & 15.23 \\
\text{Option B2} & 8.36 & 35.2\% & 40.0\% & 24.6\% & 0.2\% & 12.5\% & 14.06 \\
\text{Option C1} & 9.76 & 68.8\% & 22.6\% & 8.6\% & 0.0\% & 6.6\% & 19.43 \\
\mathbf{\text{Option C2}} & \mathbf{9.25} & \mathbf{49.4\%} & \mathbf{24.8\%} & \mathbf{25.8\%} & \mathbf{0.0\%} & \mathbf{7.5\%} & \mathbf{17.99} \\
\hline
\end{array}$$

---

## 5. Qualitative & Pedagogical Assessment ("Tutorializing Round 1")

| Core Game Mechanism | Baseline (`v038c`) | Options A2 / A3 / B1 / B2 | Candidate C1 | **Candidate C2 (Recommended)** |
| :--- | :--- | :--- | :--- | :--- |
| **1. Tri-Color Threat Triage** | **Fail:** 71.6% zero-damage rate. Players block everything; never learn damage priority. | **Fail (Overload):** 3.7–4.4 cubes hit. Players take damage everywhere; feels punitive and uncontrollable. | **Marginal:** 1.93 cubes hit 1 shield. 65% chance of 1 unblocked cube, but quickly decays by Round 2. | **Ideal:** 2.88 cubes exit against 1–2 shields. Players routinely face 1–2 leaks and actively choose which color to block. |
| **2. Glitched Slot Mechanic** | **Invisible:** Glitched slots remain at 0 in 82% of rounds. Players rarely interact with the system. | **Indirect:** Glitches only occur if Green cubes leak; confusing when compounded by heavy Red/Blue loss. | **Explicit:** Starts on board! Player sees 1 glitch on Turn 1; must read cleaning rules. | **Explicit & Integrated:** Starts on board! Player sees 1 glitch on Turn 1; immediately grasps Phase 1 cleaning vs Phase 5 graduation. |
| **3. Phase 1 Cleaning vs Phase 5 Graduation** | **Dormant:** Graduation slot clear is almost never triggered in Round 1 because no slots are glitched. | **Dormant:** Players take too much damage in R1 to safely graduate dice; forced into full defense. | **Active:** Player learns Phase 1 cleaning, but lack of ongoing threat makes graduation repair feel redundant. | **High Value:** Player chooses whether to spend a shield die in Phase 1 to clean now, or rush a die through the CI/CD Pipeline to graduate in Phase 5 for free repair. |
| **4. Pacing & Game Length** | **Lagging:** 9.9–10.1 rounds; 73% Singularity dominance. | **Over-Corrected:** 7.2–7.7 rounds; 42–51% PZ; games cut prematurely short. | **Lagging:** 9.8–10.0 rounds; 70% Singularity. | **Target-Hit:** 9.06–9.48 rounds across all player counts; balanced triad of end triggers. |
| **5. Cognitive Load for Novices** | Low, but gives false sense of safety. | Extreme; induces early analysis paralysis and feels unfair. | Moderate; clear physical focus on 1 slot. | **Smooth:** 1 visible token on mat + 1 moderate tower drop. Perfect pedagogical step. |

---

## 6. Implementation Spec & [TUNE] Parameters for SDLC Hand-Off

When approved by the User for implementation across `RULES.md`, `sim/`, and `pnp/`:

### 6.1 Setup & Component Changes
1. **RULES.md Section 3 (Setup):**
   - **Step 1 (Compiler Priming):** Keep priming drop at **4 cubes (`1R, 1B, 1G, 1K`)**. Discard exited cubes as normal.
   - **Step 2 (Company Terminal Mat Setup):**
     > *"Place 1 Glitch Token on your lowest-numbered Shield Slot (Slot 1). Your Defense Capacity is 2, but only 1 Shield Slot is currently active. You may clean this slot in Phase 1 Step 5 by committing a shield-icon die, or repair it in Phase 5 Step 3b when your first software module graduates from the CI/CD Pipeline."*
   - **Step 3 (v1.0 Starting Staging Cup Payload):**
     - Update *Script Kiddie* Starting Payload: **`2 Red, 1 Blue, 1 Green`** (4 Attack Cubes total).
     - Update *Data Scraper* Starting Payload: **`1 Red, 2 Blue, 1 Green`** (4 Attack Cubes total).

### 6.2 Simulation Configuration Updates (`sim/config.py` & `sim/entities.py`)
- Set `starting_glitched_shield_slots: int = 1` in `GameConfig.v038c()`.
- Update `staging_payload` on `v1.0` cards in `get_all_version_cards()`:
  - *Script Kiddie*: `{CubeColor.RED: 2, CubeColor.BLUE: 1, CubeColor.GREEN: 1}`
  - *Data Scraper*: `{CubeColor.RED: 1, CubeColor.BLUE: 2, CubeColor.GREEN: 1}`

---

## 7. Open Questions for the User

1. **Sign-off on Candidate C2 vs A1:**
   - Does the User prefer Candidate C2 (starting with 1 Glitched Shield Slot on the mat + 4 starting cup cubes), or Candidate A1 (pure tower priming change: 7 prime cubes + 4 starting cup cubes with clean mats)?
2. **First-Round Teaching Script:**
   - Does the User agree that introducing the Glitched Shield Slot at setup provides the ideal physical anchor to explain both Phase 1 shield-spending and Phase 5 pipeline graduation during the Round 1 teach?
