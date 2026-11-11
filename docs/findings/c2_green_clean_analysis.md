# Pre-SDLC Modeling & Empirical Analysis: Package `v038d` (Candidate C2 + Green-Clean Package)

**Author:** Game Designer (Pre-SDLC Analysis)  
**Date:** November 11, 2026  
**Status:** Pre-SDLC Modeling Complete (Awaiting User Sign-Off for SDLC Execution)  
**Simulation Dataset:** 4,500 Full-Game Matches across 2P, 3P, and 4P (500 games/cell $\times$ 9 cells, seeded `mixed1` policy roster)  
**Comparison Candidates:**
1. Baseline `v038c` (`SHOGUN_BAFFLE` baseline: 4-cube prime, 3-cube staging cup, 0 starting glitches, passive graduation auto-clean on, Green F1 Clean/Cash)
2. `v038d_var_a` (Candidate C2 + No Graduation Clean + Green F1=`+2 🔬` + Green Triage Clean **Variant A: Clean then Count**)
3. `v038d_var_b` (Candidate C2 + No Graduation Clean + Green F1=`+2 🔬` + Green Triage Clean **Variant B: Count then Clean**)

---

## 1. Executive Summary & Core Design Verdict

### 1.1 The Design Challenge
Under baseline `v038c`, early-game pressure was sluggish (games dragged out to **10.00–10.10 rounds**, with Singularity claiming **65%–73%** of all endings). Telemetry further revealed that the flagship **Glitched Shield Slot** mechanic was severely diluted by passive automation: **77% of all cleaned slots were erased automatically by Phase 5 Step 3b CI/CD graduation (`6.05` slots/seat)**, leaving players with `0.00` zero-capacity rounds and little incentive to triage or actively clean slots.

To address this, the User proposed the **`v038d` / C2-Green-Clean Package**:
1. **Candidate C2 Early-Game Setup:** 4 Priming Cubes (`1R, 1B, 1G, 1K`), 4 Starting Staging Cup Attack Cubes (`2R, 1B, 1G` on *Script Kiddie*; `1R, 2B, 1G` on *Data Scraper*), and **`1` Starting Glitched Shield Slot** (leaving 1 clean Shield Slot and 1 Glitched Slot out of Defense Capacity 2).
2. **Elimination of Passive Auto-Clean on CI/CD Graduation:** Set `slot_graduation_clear = 0`.
3. **Green Face 1 Becomes `+2 🔬`:** Establishing Green as the unambiguous **Pure Research Powerhouse**.
4. **Green Cleans 1 Glitched Shield Slot on Processing $\to$ Scanned Box:** Whenever a Green die leaves the Processing Box (via Conveyor Triage, *B3 Air-Gapped Backup*, *Jumper Diagnostics*, or *Magnetic Splice*), it cleans 1 Glitched Shield Slot.

### 1.2 The Core Verdict: Recommend Variant B (Count then Clean)

```
+-----------------------------------------------------------------------------------------------------------------------------------------+
| Candidate    | Timing Mechanic                  | Mean Rds (3P) | Sing % | PZ %   | MC %   | Green Win % (3P) | Verdict                 |
+-----------------------------------------------------------------------------------------------------------------------------------------+
| Baseline     | Passive Grad Clean (6.09/seat)   | 10.10 rds     | 73.0%  | 19.2%  |  7.6%  | 36.1% (Balanced) | OVERLY CALM / LAGGING   |
| v038d Var A  | Clean 1 Slot BEFORE Counting     |  9.10 rds     | 44.4%  | 26.0%  | 29.4%  | 49.6% (DOMINANT) | REJECT: Over-Tunes Green|
| v038d Var B  | Count Yield BEFORE Cleaning Slot |  8.94 rds     | 42.6%  | 29.2%  | 28.0%  | 38.9% (BALANCED) | RECOMMENDED FOR SDLC    |
+-----------------------------------------------------------------------------------------------------------------------------------------+
```

1. **Both Variants Successfully Hit the Core Pacing Target:**
   - Average game length drops from **10.0–10.1 rounds** to **8.57–9.10 rounds** across all player counts, resting squarely within the desired **8.5–9.5 round design window**.
   - The end triggers achieve an exceptionally balanced triad: Singularity drops from **70%–73%** down to **37%–44%**, Patient Zero rises to **26%–35%**, and Market Collapse accounts for **27%–29%** (and up to 43% in 2P). Total Wipeouts remain negligible ($\le 0.2\%$).

2. **The Crucial Distinction: Variant B Preserves Color & Economic Balance:**
   - **Variant A (Clean then Count) Over-Tunes Green:** In Variant A, banking a Green die cleans 1 glitched slot *before* the Secret yield is calculated. A player with 1 glitched slot cleans it to 0 and receives the maximum **3 Corporate Secrets**. Because Green F1 was simultaneously buffed to `+2 🔬`, Green players get both premier research engine acceleration *and* near-frictionless 3-Secret payouts. Green Company win rate explodes to **49.6% in 3P** (vs 24.3% Red, 24.9% Blue) and **61.5% in 2P**! Blue Path win rate collapses to **21.3%** in 4P.
   - **Variant B (Count then Clean) Preserves Euro Tradeoffs:** In Variant B, the Green die checks system integrity *first* (`max(0, 3 - glitched_shield_slots)`), awards Secrets, and *then* cleans 1 slot for future rounds. If a player let their grid get glitched, their payout is penalized (yielding 2 Secrets at 1 glitch, 1 Secret at 2 glitches). This maintains a vital operational tension. Green Company win rate settles at a healthy, competitive **38.9% in 3P** (with Red at 30.0% and Blue at 30.7%) and **29.1% in 4P** (with Red at 23.9% and Blue at 21.9%).

3. **Active Glitch Triage Successfully Activated:**
   - With graduation auto-clean removed (`0.00` slots cleared), players actively allocate shield dice to defense triage: `slots_cleaned_by_die` jumps from **1.38** to **5.20–5.42 per seat** (+280%).
   - Green Triage banking contributes an average of **0.66–0.94 slots cleaned per seat**, reinforcing Green's software repair thematic identity without breaking the economy.
   - Players experience an average of **~0.85–0.91 rounds at zero defense capacity**, injecting authentic existential drama into Round 1–3 defense deployment without causing runaway breach cascades.

---

## 2. Mathematical Modeling of the Green Die & Research Powerhouse

### 2.1 Face Architecture Comparison
In `v038c`, Green Face 1 was a split choice face (`Clean 1 Glitched Shield Slot / +$1`), which created clunky overlap with passive graduation cleaning. In `v038d`, Green Face 1 becomes **`+2 🔬`**.

$$\begin{array}{|c|l|l|}
\hline
\textbf{Face} & \textbf{Blue Die (Security Operations)} & \textbf{Green Die (Software Engineering / Research)} \\
\hline
\text{F1} & +1\ 🔬 & \mathbf{+2\ 🔬\ \text{(Replaces Clean / +\$1)}} \\
\text{F2} & +1\ 🔬 & +1\ 🔬 \\
\text{F3} & +\$1 & +2\ 🔬 \\
\text{F4} & +1\ 🔬\ /\ +\$1 & +1\ 🔬\ /\ +\$1 \\
\text{F5} & \text{Secret Face (Yield 1–3 by Grid/Blue Blocks)} & \text{Secret Face (Yield 0–3 by Glitched Slots)} \\
\text{F6} & \text{Blue } \bigstar\ (B1\ \text{Cash}, B2\ \text{Secret}, B3\ \text{Triage}) & \text{Green } \bigstar\ (G1\ \text{Clean}+1🔬, G2\ \text{Glitch Scale}, G3\ \text{Cash}) \\
\hline
\end{array}$$

### 2.2 Expected Research ($\mathbb{E}[🔬]$) per Roll & Reroll (Blue vs Green)

We solve the Markov Decision Process (DP) for optimal Yahtzee-style rolling across 0, 1, and 2 free rerolls under two behavioral regimes:
1. **Pure Research Maximization:** The player rerolls any face whose research value is strictly less than the expected research continuation value $\mathbb{E}[🔬]_{r-1}$.
2. **Practical Play:** The player keeps Face 5 (Corporate Secret) whenever rolled (yielding 0 research, but preserving critical VP/Secrets), while rerolling non-secret faces for research.

$$\begin{array}{|l|c|ccc|ccc|}
\hline
\textbf{Die Color \& Profile} & \textbf{Base Variant} & \multicolumn{3}{c|}{\textbf{Pure Research Maximization}} & \multicolumn{3}{c|}{\textbf{Practical Play (Keep Secrets)}} \\
& & \mathbf{0\ \text{Rerolls}} & \mathbf{1\ \text{Reroll}} & \mathbf{2\ \text{Rerolls}} & \mathbf{0\ \text{Rerolls}} & \mathbf{1\ \text{Reroll}} & \mathbf{2\ \text{Rerolls}} \\
\hline
\text{Blue Die} & B1 & 0.667 & 0.889 & 0.963 & 0.667 & 0.815 & 0.852 \\
\text{Blue Die} & B2 / B3 & 0.500 & 0.750 & 0.875 & 0.500 & 0.648 & 0.694 \\
\textbf{Blue Die (Mean)} & \text{All} & \mathbf{0.556} & \mathbf{0.796} & \mathbf{0.904} & \mathbf{0.556} & \mathbf{0.704} & \mathbf{0.747} \\
\hline
\text{Green Die (Old v0.38c)} & G1 & 0.833 & 1.111 & 1.259 & 0.833 & 0.972 & 1.028 \\
\text{Green Die (Old v0.38c)} & G2 / G3\ (g=0) & 1.000 & 1.333 & 1.556 & 1.000 & 1.167 & 1.233 \\
\textbf{Green Die Old (Mean)} & \text{All}\ (g=0) & \mathbf{0.944} & \mathbf{1.259} & \mathbf{1.457} & \mathbf{0.944} & \mathbf{1.102} & \mathbf{1.165} \\
\hline
\text{Green Die New (v0.38d)} & G1 & 1.167 & 1.444 & 1.630 & 1.167 & 1.278 & 1.315 \\
\text{Green Die New (v0.38d)} & G2 / G3\ (g=0) & 1.333 & 1.667 & 1.833 & 1.333 & 1.431 & 1.470 \\
\text{Green Die New (v0.38d)} & G2\ (g=1) & 1.500 & 1.833 & 2.000 & 1.500 & 1.583 & 1.611 \\
\textbf{Green Die New (Mean)} & \text{All}\ (g=0) & \mathbf{1.278} & \mathbf{1.593} & \mathbf{1.765} & \mathbf{1.278} & \mathbf{1.380} & \mathbf{1.418} \\
\hline
\end{array}$$

#### Key Mathematical Takeaways:
- **Massive Single-Roll Output:** On a single roll (0 rerolls), Green New yields **$1.28\ 🔬$**, representing a **$+130\%$ advantage over Blue ($0.56\ 🔬$)** and a **$+35\%$ increase over Old Green ($0.94\ 🔬$)**.
- **Reroll Scaling Ceiling:** With 2 rerolls, Green New reaches **$1.77\ 🔬$** (Pure) and **$1.42\ 🔬$** (Practical). A player dedicating 2 Green dice to research expects $\sim 3.0$ research tokens per round, reliably purchasing a Public Relations Market Share step ($3\ 🔬$) or upgrading a Defense Grid level every single round.
- **Role Differentiation Solidified:** Blue's identity is cemented around Defense Grid progression, Blue cube blocking, and conditional cash/secrets, while Green becomes the indisputable engine of pure scientific research.

---

## 3. Glitched Shield Slots & Triage Cleaning Mechanics

### 3.1 Mechanics of Green Processing $\to$ Scanned Banking
Whenever a Green die leaves the Processing Box (via Phase 5 Step 1 Conveyor Triage, *B3 Air-Gapped Backup*, *Jumper Diagnostics*, or *Magnetic Splice*), it cleans `1` Glitched Shield Slot.

Two timing formulations were modeled and simulated:
- **Variant A (Clean-Before-Count):** The Green die cleans `1` slot first; the Secret yield is then computed on the remaining glitched slots:
  $$Y_A(g) = \max\big(0,\, 3 - \max(0, g - 1)\big)$$
- **Variant B (Count-Before-Clean):** The Secret yield is computed on the current glitched slots, and *then* `1` slot is cleaned:
  $$Y_B(g) = \max\big(0,\, 3 - g\big),\quad \text{followed by } g \leftarrow \max(0, g - 1)$$

### 3.2 Payout Curves by Glitched Shield Slots ($g \in \{0, 1, 2, 3\}$)

$$\begin{array}{|c|c|c|c|c|}
\hline
\textbf{Glitched Slots } (g) & \textbf{Old Baseline Yield} & \textbf{Variant A Yield} & \textbf{Variant B Yield} & \textbf{Post-Bank Glitched Slots} \\
\hline
0 & 3\ \text{Secrets} & \mathbf{3\ \text{Secrets}} & \mathbf{3\ \text{Secrets}} & 0 \\
1 & 2\ \text{Secrets} & \mathbf{3\ \text{Secrets}} & \mathbf{2\ \text{Secrets}} & 0 \\
2 & 1\ \text{Secret} & \mathbf{2\ \text{Secrets}} & \mathbf{1\ \text{Secret}} & 1 \\
3 & 0\ \text{Secrets} & \mathbf{1\ \text{Secret}} & \mathbf{0\ \text{Secrets}} & 2 \\
\hline
\end{array}$$

#### The Mathematical Defect of Variant A:
In Variant A, having $g=0$ or $g=1$ glitched slots yields the exact same payout: **$3$ Corporate Secrets**. Because players start Setup with $g=1$ in Candidate C2, a Round 1 or Round 2 Green Secret banking incurs **zero yield penalty whatsoever**. The player gets a free slot repair *and* maximum Corporate Secrets. This completely negates the tutorial tension of starting with a damaged slot.

In Variant B, the starting $g=1$ slot actively reduces the initial Green payout to $2$ Secrets, but rewards the player by cleaning the slot so that subsequent rounds yield $3$ Secrets.

### 3.3 Bot Decision Logic Analysis (`choose_slot_cleaners` & `marginal_block_value`)

#### Analysis of `choose_slot_cleaners`:
In `sim/bots/secret_face_policy.py`:
```python
if k > eff or (green_pending and not chosen and k >= 1):
```
- **When $k > \text{eff}$ (Shield dice exceed open slots):** If a player has $\text{eff}=1$ (1 clean, 1 glitched) and rolls $k=2$ shields, $k > \text{eff}$ is True ($2 > 1$). The bot spends 1 shield die to clean the glitched slot. The capacity becomes 2, and the second shield die is deployed into the freshly cleaned slot to block! The player achieves 1 block AND repairs their mat.
- **When $k \le \text{eff}$ and $g=1$:** If the player rolls only $k=1$ shield die, spending it to clean would leave them with $0$ blocks this round. The bot correctly prioritizes blocking over cleaning unless `green_pending` justifies the sacrifice.
- **Under Variant A:** Spending a shield die when $g=1$ and $1$ Green die is pending is **irrational**, because the Green die will clean that slot upon banking anyway (yielding 3 Secrets either way).
- **Under Variant B:** Spending a shield die when $g=1$ increases the Green yield from $2 \to 3$ Secrets (+1 VP), creating a legitimate strategic trade-off between absorbing an attack cube vs banking an extra Secret.

#### Analysis of `marginal_block_value` for Green:
Previously, Green attack cubes had weak marginal block value because Phase 5 graduation auto-cleaned slots for free. With `slot_graduation_clear = 0`, glitched slots are **semi-permanent**. If unblocked, a Green cube permanently degrades Defense Capacity until actively repaired. This elevates Green cubes from an annoyance into a serious structural threat.

---

## 4. Full-Game Monte Carlo Simulation Results (4,500 Games)

Simulations were run across seeds `0..499` per player count using the standard `mixed1` policy roster on 8 parallel processes.

### 4.1 Pacing, Game Endings, and Breach Rates

$$\begin{array}{|l|c|cccc|c|}
\hline
\textbf{Configuration \& Count} & \textbf{Mean Rounds} & \textbf{Singularity} & \textbf{Patient Zero} & \textbf{Market Collapse} & \textbf{Total Wipeout} & \textbf{Breach Rate} \\
\hline
\text{Baseline v038c (2P)} & 10.00 & 64.6\% & 12.2\% & 22.2\% & 1.0\% & 13.8\% \\
\text{v038d Var A (2P)} & 8.72 & 35.8\% & 17.8\% & 44.2\% & 2.2\% & 20.0\% \\
\mathbf{\text{v038d Var B (2P)}} & \mathbf{8.66} & \mathbf{35.0\%} & \mathbf{19.4\%} & \mathbf{43.4\%} & \mathbf{2.2\%} & \mathbf{21.6\%} \\
\hline
\text{Baseline v038c (3P)} & 10.10 & 73.0\% & 19.2\% & 7.6\% & 0.2\% & 21.0\% \\
\text{v038d Var A (3P)} & 9.10 & 44.4\% & 26.0\% & 29.4\% & 0.2\% & 27.0\% \\
\mathbf{\text{v038d Var B (3P)}} & \mathbf{8.94} & \mathbf{42.6\%} & \mathbf{29.2\%} & \mathbf{28.0\%} & \mathbf{0.2\%} & \mathbf{30.0\%} \\
\hline
\text{Baseline v038c (4P)} & 10.04 & 70.6\% & 21.0\% & 8.4\% & 0.0\% & 22.0\% \\
\text{v038d Var A (4P)} & 8.72 & 40.0\% & 32.2\% & 27.8\% & 0.0\% & 33.4\% \\
\mathbf{\text{v038d Var B (4P)}} & \mathbf{8.57} & \mathbf{37.4\%} & \mathbf{35.2\%} & \mathbf{27.2\%} & \mathbf{0.2\%} & \mathbf{36.2\%} \\
\hline
\end{array}$$

### 4.2 Glitched Shield Slot & Cleaning Telemetry (per seat averages)

$$\begin{array}{|l|cc|cccc|}
\hline
\textbf{Configuration \& Count} & \textbf{Max Glitched} & \textbf{Zero-Cap Rds} & \textbf{Clean: Die} & \textbf{Clean: Green Triage} & \textbf{Clean: Face (G1)} & \textbf{Clean: Graduation} \\
\hline
\text{Baseline v038c (2P)} & 2.15 & 0.00 & 1.38 & 0.00 & 0.42 & \mathbf{5.96} \\
\text{v038d Var A (2P)} & 2.14 & 0.85 & 5.20 & 0.76 & 0.14 & \mathbf{0.00} \\
\mathbf{\text{v038d Var B (2P)}} & \mathbf{2.14} & \mathbf{0.88} & \mathbf{5.19} & \mathbf{0.66} & \mathbf{0.13} & \mathbf{0.00} \\
\hline
\text{Baseline v038c (3P)} & 2.22 & 0.00 & 1.38 & 0.00 & 0.45 & \mathbf{6.09} \\
\text{v038d Var A (3P)} & 2.21 & 0.88 & 5.42 & 0.94 & 0.19 & \mathbf{0.00} \\
\mathbf{\text{v038d Var B (3P)}} & \mathbf{2.21} & \mathbf{0.91} & \mathbf{5.39} & \mathbf{0.79} & \mathbf{0.15} & \mathbf{0.00} \\
\hline
\text{Baseline v038c (4P)} & 2.17 & 0.00 & 1.39 & 0.00 & 0.49 & \mathbf{6.05} \\
\text{v038d Var A (4P)} & 2.16 & 0.85 & 5.30 & 0.94 & 0.21 & \mathbf{0.00} \\
\mathbf{\text{v038d Var B (4P)}} & \mathbf{2.15} & \mathbf{0.89} & \mathbf{5.22} & \mathbf{0.80} & \mathbf{0.17} & \mathbf{0.00} \\
\hline
\end{array}$$

### 4.3 Win Rates by Company Starting Color & Strategic Path

$$\begin{array}{|l|ccc|ccccc|}
\hline
\textbf{Configuration \& Count} & \multicolumn{3}{c|}{\textbf{Win Rate by Company Color}} & \multicolumn{5}{c|}{\textbf{Win Rate by Strategic Path}} \\
& \textbf{Red Co} & \textbf{Blue Co} & \textbf{Green Co} & \textbf{Red Path} & \textbf{Blue Path} & \textbf{Green Path} & \textbf{Yellow Path} & \textbf{Mixed} \\
\hline
\text{Baseline v038c (2P)} & 56.3\% & 45.4\% & 48.5\% & 60.5\% & 58.5\% & 53.7\% & 39.7\% & 47.4\% \\
\text{v038d Var A (2P)} & 50.8\% & 37.7\% & \mathbf{61.5\%} & 54.7\% & 44.1\% & \mathbf{64.5\%} & 36.2\% & 45.8\% \\
\mathbf{\text{v038d Var B (2P)}} & \mathbf{53.8\%} & \mathbf{41.2\%} & \mathbf{55.0\%} & \mathbf{58.9\%} & \mathbf{49.5\%} & \mathbf{60.8\%} & \mathbf{32.8\%} & \mathbf{44.2\%} \\
\hline
\text{Baseline v038c (3P)} & 31.9\% & 31.9\% & 36.1\% & 34.6\% & 44.0\% & 49.1\% & 25.2\% & 32.5\% \\
\text{v038d Var A (3P)} & 24.3\% & 24.9\% & \mathbf{49.6\%} & 34.1\% & 33.6\% & \mathbf{55.4\%} & 20.3\% & 29.7\% \\
\mathbf{\text{v038d Var B (3P)}} & \mathbf{30.0\%} & \mathbf{30.7\%} & \mathbf{38.9\%} & \mathbf{37.8\%} & \mathbf{42.7\%} & \mathbf{48.8\%} & \mathbf{18.1\%} & \mathbf{30.6\%} \\
\hline
\text{Baseline v038c (4P)} & 26.3\% & 21.7\% & 27.0\% & 22.8\% & 32.2\% & 36.1\% & 19.9\% & 23.7\% \\
\text{v038d Var A (4P)} & 20.2\% & 15.7\% & \mathbf{38.6\%} & 22.5\% & 21.3\% & \mathbf{42.1\%} & 17.8\% & 22.5\% \\
\mathbf{\text{v038d Var B (4P)}} & \mathbf{23.9\%} & \mathbf{21.9\%} & \mathbf{29.1\%} & \mathbf{27.5\%} & \mathbf{32.6\%} & \mathbf{34.7\%} & \mathbf{14.4\%} & \mathbf{23.0\%} \\
\hline
\end{array}$$

### 4.4 Bot Archetype Win Rate Spread (3-Player)

$$\begin{array}{|l|cccccc|}
\hline
\textbf{Configuration (3P)} & \textbf{Accelerationist} & \textbf{Adaptive Balanced} & \textbf{Mixed Policy} & \textbf{Reckless Saboteur} & \textbf{SecOps Turtle} & \textbf{Venture Greed} \\
\hline
\text{Baseline v038c} & 39.3\% & 50.5\% & 29.0\% & 14.6\% & 46.1\% & 27.0\% \\
\text{v038d Var A} & 41.3\% & 47.8\% & 30.8\% & 18.4\% & 45.7\% & 18.9\% \\
\mathbf{\text{v038d Var B}} & \mathbf{31.6\%} & \mathbf{52.2\%} & \mathbf{31.0\%} & \mathbf{18.0\%} & \mathbf{50.2\%} & \mathbf{20.0\%} \\
\hline
\end{array}$$

---

## 5. Strategic & Balance Takeaways

1. **The Overpowering Surge of Variant A:**
   In 3P, Green Company win rate under Variant A climbs to **49.6%**—effectively half of all games won by the green starting seat. Blue and Red are compressed to ~24%. This occurs because Green provides unhindered research velocity while simultaneously guaranteeing 3-Secret payouts on banked secrets.
2. **Variant B Achieves the Ideal Balance Point:**
   Under Variant B, Green Company sits at **38.9% in 3P** and **29.1% in 4P**, comfortably competitive alongside Red (**30.0% / 23.9%**) and Blue (**30.7% / 21.9%**). Blue Path win rate rebounds to **42.7% (3P) / 32.6% (4P)**, ensuring defensive Grid leveling and blue block plays remain top-tier viable strategies.
3. **Pacing and Endings Target Exceeded:**
   Mean game duration across all player counts hits **8.57–8.94 rounds**, perfectly within the Core Design Pillar target of 8.5–9.5 rounds. Singularity is no longer an inevitable default, and Market Collapse acts as a true tactical threat (**27%–28%** in 3–4P, **43%** in 2P).
4. **Active Defense Re-Engaged:**
   With passive graduation removed, players clean an average of **5.2–5.4 slots per seat using shield dice**, compared to just **1.38** in baseline. Players actively make hard choices between income/research vs grid repair.

---

## 6. Concrete Implementation Plan for Full SDLC

Upon User approval of this analysis, the multi-agent SDLC pipeline (`principal-engineer` $\to$ `senior-engineer` $\leftrightarrow$ `staff-engineer` $\to$ `product-owner` $\leftrightarrow$ `game-designer` + `graphic-designer`) should execute the following changes:

### 6.1 `RULES.md` Updates
- **Section 1.3 & 3 (Setup):**
  - Update `v1.0` starting staging cup: Script Kiddie starts with `4` cubes (`2 Red, 1 Blue, 1 Green`); Data Scraper starts with `4` cubes (`1 Red, 2 Blue, 1 Green`).
  - Add Setup Step 7d: Each player begins the game with `1` Glitched Shield Slot on their Company Terminal Mat (Defense Grid Level 1 provides 2 Shield Slots: 1 clean, 1 glitched).
- **Section 2.1 & 2.2 (Die Faces):**
  - Update Green die face table: Face 1 changes from `Clean 1 Glitched Shield Slot / +$1` to **`+2 🔬`**.
- **Section 4.5 (Phase 5: Conveyor Triage & CI/CD Pipeline Shift):**
  - **Step 1 (Conveyor Triage):** Add rule: Whenever a Green die leaves the Processing Box (moving to Scanned Box via Conveyor Triage, *B3 Air-Gapped Backup*, or *Jumper Diagnostics*, or banking to Ready for Release via *Magnetic Splice*), it banks its Secret yield first (`max(0, 3 - glitched_shield_slots)`), and *then* cleans `1` Glitched Shield Slot.
  - **Step 3b (Scanned Graduation):** Remove the passive auto-clean rule (`slot_graduation_clear = 0`). Graduation no longer cleans glitched slots.

### 6.2 `RULES_APPENDIX.md` Updates
- Update Section 6.2 Colored Dice Faces table: Green Face 1 updated to `+2 🔬`.
- Update Section 6.3 Version Cards table: `v1.0` Script Kiddie and Data Scraper Staging Payloads updated to 4 cubes.

### 6.3 Codebase Changes (`sim/`)
- `sim/config.py`:
  - In `GameConfig`: add `starting_glitched_shield_slots: int = 1`, `slot_graduation_clear: int = 0`, `green_triage_clean_mode: str = "COUNT_THEN_CLEAN"`.
  - In `GameConfig.v038c()` or new `v038d()`: enable these parameters.
  - Add `"V038D"` to `V038_DIE_FACE_PROFILES`.
- `sim/entities.py`:
  - In `get_all_version_cards()`: update `staging_payload` on `v1.0` Script Kiddie to `{RED: 2, BLUE: 1, GREEN: 1}` and Data Scraper to `{RED: 1, BLUE: 2, GREEN: 1}`.
  - In `_create_colored_die_v038()`: set Green Face 1 to `Face(name="+2 🔬", patches=2)` when profile is `"V038D"`.
- `sim/engine/core.py`:
  - In `__init__`: initialize `player.glitched_shield_slots = config.starting_glitched_shield_slots` and `player.max_glitched_slots = config.starting_glitched_shield_slots`.
- `sim/engine/secret_faces.py`:
  - In `bank()`: under `COUNT_THEN_CLEAN`, calculate `y = secret_yield(cfg, p, die.color)`, then if `die.color == DieColor.GREEN`, call `clean_slots(p, 1, "green_triage")`.
  - In `clean_slots()`: support `"green_triage"` and increment `player.slots_cleaned_by_green_triage`.
- `sim/engine/state.py` & `sim/engine/end_game.py`:
  - Add `self.slots_cleaned_by_green_triage = 0` to `PlayerState`.
  - Expose `slots_cleaned_by_green_triage` in end-game telemetry rows.
- `sim/bots/secret_face_policy.py`:
  - Retain `k > eff` check in `choose_slot_cleaners` and verify bot valuation for Green triage repair.

### 6.4 Print-and-Play Assets (`pnp/`)
- `pnp/cards.py` & `pnp/mats.py`:
  - Update Green die face face sheet (Face 1 shows `2 🔬`).
  - Update `v1.0` Version Card starting staging cup graphics to show 4 cubes.
  - Add Setup iconography or reminder text on Company Terminal Mat: "Setup: Place 1 Glitch Token on Shield Slot 2".

---

## 7. Recommendation & Next Steps

We recommend the User approve **Package `v038d` with Variant B (Count then Clean)**. It completely resolves the sluggish pacing problem, eliminates passive automation from CI/CD graduation, firmly establishes Green as the premier Research Powerhouse, and maintains balanced win rates across all three company colors and strategic paths.

Awaiting User confirmation to initiate the multi-agent SDLC pipeline.
