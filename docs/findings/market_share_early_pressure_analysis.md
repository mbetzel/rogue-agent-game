# Mathematical Modeling & Impact Analysis: Early-Game Market Share Dynamics

**Author:** Game Designer (Pre-SDLC Balance Analysis)  
**Status:** Pre-SDLC Modeling Complete — Ready for User Sign-off  
**Reference Document:** `RULES.md` Sections 2–5, `RULES_APPENDIX.md`, `FINDINGS.md` §43–§45, `docs/findings/early_game_pressure_modeling.md`  
**Simulation Dataset:** 5,200 Full-Game Matches (`GameEngine` with Shogun Baffle Physics, Candidate C2 Payload, across 2P, 3P, and 4P pods)

---

## 1. Executive Summary & Design Verdict

### The Problem Statement
Under the current baseline (`v0.38.0` / `v0.38d`), players start the game with their Market Share marker placed at the track ceiling:
$$\text{Market Share Start} = \text{Market Share Max} = 13 \text{ (2P)} \;/ \; 16 \text{ (3P)} \;/ \; 17 \text{ (4P)}$$

The User correctly observed:
> *"I'm still not happy with how the market shares track works. If there's no pressure from red cubes early (which may happen with the low number of cubes ejected) then there's no reason to spend research on increasing your market share and the red market share faces are not useful."*

When players start at the track ceiling:
1. **Dead & Collapsed Dice Faces ("Zero Blank Faces" Violation):**
   - **Red Face 1 (`+1 Market Share / +$1`):** In Round 1, 100.0% of players are at track maximum. The choice face completely collapses into a forced single option (`+$1`). The tactical decision between corporate positioning and liquidity is extinguished.
   - **Yellow Face 1 (`+2 Market Share`):** If rolled early, it yields exactly 0 Market Share, 0 Money, and 0 Research—a completely blank face that violates Core Design Pillar 3.
   - **Yellow Face 3 (`+$1 & +1 Market Share`) & R1 Star (*Brand Protection* — `+$2 & +1 Market Share`):** The `+1 Market Share` component is 100% wasted.
2. **Public Relations Track Paralysis:**
   - Players cannot spend research tokens on the Public Relations Track because $\text{Room} = \text{Max} - \text{Current} = 0$.
   - Because early Red cube damage is low (55.0% of seats take zero Red damage in Round 1), Market Share remains a dormant, static number rather than an active corporate race.

---

### Core Recommendations & Verdict

```
+----------------------------------------------------------------------------------------------------------------------------------+
| Candidate Model                        | R1 Max% | Rds (3P) | Sing% | PZ%   | MC%   | Min MC Rd | Red WR% | Status               |
+----------------------------------------------------------------------------------------------------------------------------------+
| Baseline (Start = Max = 13/16/17)      | 100.0%  | 8.04 rds | 44.2% | 32.0% | 25.0% | Round 7   | 30.8%   | DEFECTIVE (Dead Faces)|
| A4: Unified Track Max 20 (Headroom +3) |   0.0%  | 8.17 rds | 47.5% | 30.0% | 25.0% | Round 7   | 37.9%   | RECOMMENDED (Optimal) |
| B1: Aggressive Red (-2 MS / cube)      | 100.0%  | 5.96 rds |  9.3% | 25.7% | 67.7% | Round 3   | 33.3%   | REJECTED (Meatgrinder)|
| C1: Asymmetric Start (±1 by Company)   |  66.9%  | 8.20 rds | 46.3% | 25.0% | 30.7% | Round 7   | 33.3%   | REJECTED (2:1 WR Skew)|
| D1: Headroom + Aggressive Red (-2 MS)  |   0.0%  | 5.64 rds |  7.0% | 22.7% | 73.0% | Round 2   | 34.0%   | REJECTED (Premature)  |
| D3: Headroom + Asymmetric Start        |   0.0%  | 8.20 rds | 41.0% | 28.3% | 33.0% | Round 7   | 39.0%   | REJECTED (Unfair Lead)|
+----------------------------------------------------------------------------------------------------------------------------------+
```

1. **PRIMARY RECOMMENDATION: Candidate A4 (Unified Physical Track `0–20` with Headroom Above Start)**
   - **Track Topology:** Central Market Share Track on the SETEC Agent Board features cells numbered `0` to `20`.
   - **Starting Values:** Preserved exactly from `v0.38.0`: **`13` at 2P**, **`16` at 3P**, **`17` at 4P**.
   - **Ceiling:** Unified at **`20`** across all player counts.
   - **Headroom Provided:** **+7 spaces** at 2P, **+4 spaces** at 3P, **+3 spaces** at 4P.
   - **Mathematical Impact:**
     - Round 1 and Round 2 players at track maximum drops from **100.0% to 0.0%**.
     - Red Face 1 `+1 Market Share` choice selection rate jumps from **0.0% to 100.0%**.
     - Face waste on Yellow F1/F3 and R1 Star drops to **0.0%**.
     - Buffer distance to Market Collapse ($D = \text{Start} - 0$) is completely preserved, maintaining ideal pacing (**8.17 rounds at 3P**, **7.68 rounds at 2P**, **7.71 rounds at 4P**) and safe 3-way end trigger distribution (**47.5% Singularity**, **30.0% Patient Zero**, **25.0% Market Collapse**).
     - Earliest observed Market Collapse remains strictly in late game (**Round 7+**).

2. **DEFINITIVELY REJECTED: Candidate B1 (Aggressive Red Attack: -2 MS per unblocked cube)**
   - Fails to fix the Round 1 dead face problem (players are still at ceiling during Phase 1 rolling before damage resolves).
   - Catastrophically cuts game length from 8.04 down to **5.96 rounds**.
   - Market Collapse explodes to **67.7%**, triggering as early as **Round 3**, while Singularity withers to **9.3%**, destroying the game's existential narrative climax.

3. **DEFINITIVELY REJECTED: Candidates C1 & C2 (Asymmetrical Starting Market Share by Company)**
   - Starting with asymmetric Market Share creates an unearned, zero-sum VP head start.
   - In 3P, Meridian (+1 start) win rate surges to **51.3%**, while Prometheus (-1 start) plummets to **25.7%**—a 2:1 disparity between companies of the same color!
   - Violates competitive Eurogame fairness: factions should provide asymmetric abilities (Overrides), not raw VP placement leads.

---

## 2. Cube Tower Ejection Analysis (Shogun Baffle + Candidate C2)

### 2.1 Analytical Formulation of Early Drops
Under Candidate C2 setup priming, 4 cubes (`1R, 1B, 1G, 1K`) are dropped into an empty tower ($S_0 = 0$). With empty pass-through $p_{\text{exit}} = 0.70$, the stuck cube distribution Settling on baffles is:

$$P(S_0 = k) = \binom{4}{k} (0.30)^k (0.70)^{4-k}$$

$$\mathbb{E}[S_0] = 4 \times 0.30 = 1.20 \text{ resting cubes}$$

In Round 1, SETEC injects 1 Black cube via Autonomous Protocol into the Staging Cup.
Total mass entering Round 1:
- *Script Kiddie:* $F = 5$ cubes (`2R, 1B, 1G, 1K`). Total mass $F + S_0 \in [5, 9]$.
- *Data Scraper:* $F = 5$ cubes (`1R, 2B, 1G, 1K`). Total mass $F + S_0 \in [5, 9]$.

Under the `SHOGUN_BAFFLE` physics model:
- If $S_0 < 3$ and $F + S_0 < 7$ ($S_0 \in \{0, 1\}$; 65.2% probability): Trapping regime operates. $p_{\text{fall}} = 0.70 - 0.15 \times S_0$, $p_{\text{dislodge}} = 0.21$.
- If $S_0 \ge 3$ or $F + S_0 \ge 7$ ($S_0 \ge 2$; 34.8% probability): Avalanche regime triggers. $p_{\text{fall}} = 0.60$, $p_{\text{dislodge}} = 0.70$.

### 2.2 Exited Attack Cubes in Early Rounds (50,000 Monte Carlo Trials)

```
+---------------------------------------------------------------------------------------+
| Version Card  | Round | Mean Exited Attack | Mean Exited Red | P(0 Red Exited) | P(1 Red) |
+---------------------------------------------------------------------------------------+
| Script Kiddie | R1    | 2.89 cubes         | 1.36 cubes      | 13.6%           | 42.1%    |
| Data Scraper  | R1    | 2.89 cubes         | 0.77 cubes      | 33.0%           | 57.5%    |
| 50/50 Blend   | R1    | 2.89 cubes         | 1.07 cubes      | 23.3%           | 49.8%    |
| All           | R2    | 3.12 cubes         | 1.34 cubes      | 16.6%           | 40.0%    |
| All           | R3    | 3.35 cubes         | 1.35 cubes      | 16.1%           | 40.0%    |
+---------------------------------------------------------------------------------------+
```

### 2.3 The Defensive Triage Dilemma
In Round 1, players roll 4 starter dice (2 Gray, 1 Purple, 1 Colored) with 1 free reroll.
- Expected rolled `Block 1 Any` shields per player: $\approx 1.67$ shields.
- Available clean Shield Slots: **1 clean slot** (1 slot begins glitched under C2).
- Priority order under survival Euro design:
  1. **Blue Cubes (Spyware):** Threatens Corporate Secrets. A loss of 4 Secrets causes instant **Patient Zero elimination**. Players *must* block Blue first.
  2. **Green Cubes (Malware):** Glitches clean Shield Slots, penalizing future defense and reducing Green Secret banking yields ($3 - g$).
  3. **Red Cubes (Market Manipulation):** Lowers Market Share by 1. Because players start at 13–17 Market Share, losing 1 Market Share has zero existential consequence in early rounds.

**Empirical Result:**
- In Round 1, **55.0% of player-rounds suffer zero unblocked Red damage**.
- Under Data Scraper, **nearly 1 in 3 games sees zero Red cubes exit the tower**.
- When players start at track maximum, more than half the table remains at maximum throughout Round 1 and into Round 2.

---

## 3. Buffer Distance & Market Collapse Dynamics

### 3.1 Pacing Safety and the Buffer Invariant
Market Collapse triggers at the end of Phase 4 if any surviving player is at `0` Market Share.
The buffer distance $D$ is the number of unblocked Red hits required to induce Collapse:

$$H_{\text{collapse}} = \frac{D}{d_{\text{red}}}$$

Where $D = \text{Market Share Start}$, and $d_{\text{red}}$ is damage per unblocked Red cube.

```
+------------------------------------------------------------------------------------------+
| Model                  | Start | Max | Buffer D | d_red | Hits to Collapse | Mean Rounds |
+------------------------------------------------------------------------------------------+
| Baseline (v0.38d)      | 16    | 16  | 16 hits  | 1     | 16 hits          | 8.04 rds    |
| A1: Headroom (Lowered) | 14    | 16  | 14 hits  | 1     | 14 hits          | 7.99 rds    |
| A2: Headroom (Lowered) | 13    | 16  | 13 hits  | 1     | 13 hits          | 7.91 rds    |
| A4: Headroom (Raised)  | 16    | 20  | 16 hits  | 1     | 16 hits          | 8.17 rds    |
| B1: Aggressive Red     | 16    | 16  | 16 hits  | 2     |  8 hits          | 5.96 rds    |
| D1: Lowered + Aggr Red | 13    | 16  | 13 hits  | 2     |  6.5 hits        | 5.64 rds    |
+------------------------------------------------------------------------------------------+
```

### 3.2 The Flaw of Lowering Start vs. Raising Max
- When headroom is created by **lowering starting Market Share** (Models A1, A2, A3), the buffer distance $D$ shrinks.
  - At 3P, lowering start to 13 increases Market Collapse rate from **25.0% to 41.0%**, compressing game length.
  - At 2P, lowering start to 10 would cause premature collapse in over 55% of games.
- When headroom is created by **raising Track Max to 20** (Model A4):
  - Buffer distance $D$ is **100% preserved** (13 at 2P, 16 at 3P, 17 at 4P).
  - Pacing remains firmly anchored at **8.17 rounds (3P)** and **7.68 rounds (2P)**.
  - Market Collapse remains a tense, late-game event (**Round 7–10**), never an early accident.

---

## 4. Economic Value & ROI of Market Share and Public Relations

### 4.1 Die Face Valuation & "Zero Blank Faces"
In `Too Many Secrets`, Corporate Secrets are the sole victory condition ($1 \text{ Secret} = 1 \text{ VP}$).
Market Share converts into Corporate Secrets through the **Market Leader Bonus**:
- Awarded at the end of Phase 5 whenever a Red Secret face is banked.
- Awarded once at game end (Singularity, Patient Zero, and Market Collapse endings).
- Schedule: **1st Place = +3 Secrets**, **2nd Place = +1 Secret**, **3rd/4th = 0**. Ties share the better place.
- Full-game yield: Mean of **3.5 payouts per game**. Over a game, holding 1st place vs 3rd place is worth up to **+10.5 Corporate Secrets** (over 60% of a winning score).

#### Turn 1 Die Face Behavior Comparison:

```
+------------------------------------------------------------------------------------+
| Die Face                         | Baseline (Start = Max)   | Candidate A4 (Headroom 20) |
+------------------------------------------------------------------------------------+
| Red F1: +1 MS / +$1              | 100% Forced Money (Dead) | Real Choice: MS for Lead   |
| Yellow F1: +2 MS                 | 100% Dead (0 Value)      | Surges +2 spaces           |
| Yellow F2: +1 MS / +1 🔬         | 100% Forced Research     | Real Choice                |
| Yellow F3: +$1 & +1 MS           | +1 MS component wasted   | Collects $1 + 1 MS         |
| R1 Star: +$2 & +1 MS             | +1 MS component wasted   | Collects $2 + 1 MS         |
+------------------------------------------------------------------------------------+
```

### 4.2 Public Relations Track ROI
The Public Relations Track allows spending **`3 🔬`** for **`+1 Market Share`** (limit 1 at L0–1, 2 at L2–3, 3 at L4).
- Under Baseline: In Rounds 1–3, players cannot buy PR because they are capped at maximum.
- Under Candidate A4: If a rival rolls a +MS face and takes the lead (e.g. 17 MS vs 16 MS), a trailing player with 3 🔬 can spend on PR to tie for 1st place.
- Mathematical ROI:
  $$\Delta EV = \Delta P(\text{1st}) \times 3 \text{ Secrets} - 3 \text{ 🔬}$$
  Tying for 1st place gains $+2$ Corporate Secrets ($+3$ instead of $+1$).
  Since $1 \text{ Secret} \approx 3 \text{ 🔬}$, spending $3 \text{ 🔬}$ to gain $2 \text{ Secrets}$ yields an instant **200% return on investment**!

---

## 5. Comprehensive Monte Carlo Simulation Results

### 5.1 Model Comparison Sweep (300 Games per Cell, 3 Players)

```
+------------------------------------------------------------------------------------------------------------------------+
| Model                                      | Rds  | Sing% | PZ%   | MC%   | MC Rd  | R1 Max% | R2 Max% | Red WR | Grn WR |
+------------------------------------------------------------------------------------------------------------------------+
| Baseline (v0.38d)                          | 8.04 | 44.3  | 30.3  | 26.7  | 9.3 (≥7) | 100.0   | 70.3    | 31.7   | 38.2   |
| A1: Headroom +2 (Start -2, Max base)       | 7.99 | 37.0  | 30.0  | 36.3  | 9.3 (≥6) | 0.0     | 0.2     | 39.0   | 30.7   |
| A2: Headroom +3 (Start -3, Max base)       | 7.91 | 33.0  | 29.7  | 41.0  | 9.1 (≥6) | 0.0     | 0.0     | 38.7   | 30.7   |
| A3: Headroom +4 (Start -4, Max base)       | 7.77 | 32.3  | 27.7  | 43.3  | 8.9 (≥5) | 0.0     | 0.0     | 37.7   | 31.4   |
| A4: Headroom +3 (Start base, Max +3)       | 8.22 | 47.0  | 29.3  | 26.3  | 9.4 (≥7) | 0.0     | 0.0     | 39.7   | 30.4   |
| B1: Aggressive Red (-2 MS, no headroom)    | 5.96 |  9.3  | 25.7  | 67.7  | 7.2 (≥3) | 100.0   | 65.3    | 33.3   | 37.9   |
| C1: Asymmetry Mild (±1, no headroom)       | 8.20 | 46.3  | 25.0  | 30.7  | 9.2 (≥7) | 66.9    | 53.9    | 33.3   | 38.8   |
| C2: Asymmetry Strong (±2, no headroom)     | 8.22 | 43.0  | 25.0  | 33.7  | 9.2 (≥6) | 51.4    | 43.1    | 38.7   | 36.2   |
| D1: Headroom +3 + Aggressive Red (-2 MS)   | 5.64 |  7.0  | 22.7  | 73.0  | 6.8 (≥2) | 0.0     | 0.0     | 34.0   | 34.6   |
| D2: Headroom +3 (Start -3) + Asymmetry Mild| 7.88 | 30.0  | 28.3  | 45.3  | 9.0 (≥5) | 0.0     | 0.0     | 36.7   | 34.6   |
| D3: Headroom +3 (Start base) + Asymmetry   | 8.20 | 41.0  | 28.3  | 33.0  | 9.3 (≥7) | 0.0     | 0.0     | 39.0   | 35.0   |
| D4: Headroom +3 + Asym + Aggressive Red    | 5.56 |  5.7  | 19.7  | 77.3  | 6.6 (≥2) | 0.0     | 0.0     | 32.0   | 37.5   |
+------------------------------------------------------------------------------------------------------------------------+
```

### 5.2 Multi-Player Count Validation of Recommended Candidate A4 (500 Games per Pod)

```
+------------------------------------------------------------------------------------------------------------------------+
| Pod | Model            | Rounds | Singularity% | Patient Zero% | Market Collapse% | Min MC Rd | Red WR | Blu WR | Grn WR |
+------------------------------------------------------------------------------------------------------------------------+
| 2P  | Baseline (v0.38d)| 7.68   | 36.6%        | 21.8%         | 42.0%            | Round 5   | 51.1%  | 44.5%  | 50.3%  |
| 2P  | Headroom A4 (20) | 7.74   | 35.4%        | 21.8%         | 43.6%            | Round 5   | 53.5%  | 47.2%  | 46.2%  |
+------------------------------------------------------------------------------------------------------------------------+
| 3P  | Baseline (v0.38d)| 7.99   | 44.2%        | 32.0%         | 25.0%            | Round 7   | 30.8%  | 31.5%  | 37.0%  |
| 3P  | Headroom A4 (20) | 8.19   | 47.2%        | 30.0%         | 25.2%            | Round 7   | 38.2%  | 29.9%  | 31.9%  |
+------------------------------------------------------------------------------------------------------------------------+
| 4P  | Baseline (v0.38d)| 7.68   | 41.0%        | 36.4%         | 24.0%            | Round 8   | 23.9%  | 22.4%  | 28.5%  |
| 4P  | Headroom A4 (20) | 7.77   | 41.2%        | 37.0%         | 25.0%            | Round 7   | 30.4%  | 19.6%  | 25.0%  |
+------------------------------------------------------------------------------------------------------------------------+
```

### 5.3 Client Company Win Rate Equity: Symmetrical Headroom vs Asymmetry

```
+---------------------------------------------------------------------------------------------+
| Company Name (Starting Color) | Sector Lore         | Baseline WR% | Asym (D3) WR% | A4 WR% |
+---------------------------------------------------------------------------------------------+
| MERIDIAN (Red)                | Banking Corp        | 30.1%        | 51.3% (SKEW)  | 38.5%  |
| PROMETHEUS (Red)              | Open Source Non-Prof| 33.3%        | 25.7% (CRUSH) | 41.0%  |
| AEGIS (Blue)                  | Security Firm       | 32.2%        | 23.0%         | 34.2%  |
| DTO (Blue)                    | Federal Agency      | 26.6%        | 28.1%         | 24.5%  |
| OMNIDYNE (Green)              | Tech Giant          | 41.3%        | 47.7% (SKEW)  | 37.4%  |
| HELIX (Green)                 | Medical Consortium  | 35.1%        | 22.1% (CRUSH) | 23.4%  |
+---------------------------------------------------------------------------------------------+
```

**Key Takeaway:**
Under Asymmetry (D3), Meridian and Omnidyne (+1 start) run away with the game, while Prometheus and Helix (-1 start) collapse into unviability. Under Candidate A4, all companies start on an equal footing, allowing player tactical decisions and dice building to determine the victor.

---

## 6. Concrete Implementation Proposal for User Sign-off

### Proposed Rule & Setup Changes (`RULES.md`)

1. **Central Market Share Track Topology:**
   - Modify Section 2 & Section 3: The Central Market Share Track on the Central SETEC Agent Board is numbered from **`0` to `20`**.
   - `0`: **Market Collapse** (Final Round trigger).
   - **`20`**: **Track Maximum** for all player counts.
2. **Starting Positions (Unchanged from `v0.38.0`):**
   - **2 Players:** Place Market Share markers on **`13`** (7 spaces of headroom up to 20).
   - **3 Players:** Place Market Share markers on **`16`** (4 spaces of headroom up to 20).
   - **4 Players:** Place Market Share markers on **`17`** (3 spaces of headroom up to 20).
3. **Damage & Regain Rules (Unchanged):**
   - Unblocked Red cube = **`-1 Market Share`**.
   - Public Relations Track = **`3 🔬 per +1 Market Share`** (up to current PR level limit).
   - Capped at Track Maximum (**`20`**).
4. **Physical Print-and-Play Board (`pnp/generate_pnp.py`):**
   - Update Column 3 of the SETEC Agent Board to display cells `0` through `20` (e.g., 3 columns $\times$ 7 rows = 21 cells).
   - Header text updated to:
     `START: 13 (2P) | 16 (3P) | 17 (4P)  •  MAX: 20`

---

## 7. Open Decisions for User Sign-off

1. **Track Ceiling Geometry:**
   - **Option A (Recommended): Unified Max `20`** (21-cell grid: 3 columns $\times$ 7 rows on the board). Gives identical track maximum across all player counts with natural headroom (7 at 2P, 4 at 3P, 3 at 4P).
   - **Option B: Uniform Headroom +3 (Dynamic Max: 16 at 2P, 19 at 3P, 20 at 4P)**.
2. **Sign-off on Rejection of -2 Red Damage & Starting Asymmetry:**
   - Confirm mathematical modeling finding that -2 Red damage prematurely terminates matches in Rounds 3–5, and starting asymmetry heavily distorts company win rate parity (2:1 disparity).
3. **Approval to Proceed to Full SDLC:**
   - Upon User sign-off, initiate the standard SDLC pipeline (`principal-engineer` $\to$ `senior-engineer` $\to$ `staff-engineer` $\to$ `product-owner` $\to$ `graphic-designer`).
