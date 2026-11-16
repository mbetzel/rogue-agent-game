# White Hat Face 6 (`Purple ★`) Signature Protocols Rebalance Analysis & Modeling

**Document ID:** `docs/findings/white_hat_6f_rebalance_analysis.md`  
**Author:** Game Designer (Pre-SDLC Analysis)  
**Baseline:** v0.43.0 Canonical Baseline  
**Target Mechanics:** 6 Updated White Hat Face 6 (`Purple ★`) Signature Protocols  
**Status:** Pre-SDLC Modeling Complete — Awaiting User Review & Alignment

---

## Executive Summary

This pre-SDLC game design report evaluates the proposed redesign of the 6 **White Hat Operative** Face 6 (`Purple ★`) **Signature Protocols** on the **v0.43.0** canonical baseline. The proposal modernizes legacy abilities, eliminates high-friction manual sub-rolling in Phase 3 (*Phreaker*), introduces Euro-style starter die culling (*Spook*), clarifies deterministic post-reroll timing (*Prodigy*), and integrates Operative Signature Cubes into acoustic threat resonance (*Acoustic*).

### The 6 Proposed Signature Protocols

1. **The Operator (*Logistics Bounty*, Phase 3: Income):** Gain `+1 🔬` Research Token per die currently in your **Processing Box**.
2. **The Phreaker (*Jumper Diagnostics*, Phase 3: Income):** Gain `+$1` cash AND `+1` **Release Bandwidth** this round (applies in Phase 6 Step 3).
3. **The Acoustic (*Resonance Sensor*, Phase 3: Income):** Gain `+$1` cash per distinct cube color that exited the **Cube Tower** this round (including **Operative Signature Cubes**), up to `+$5` max.
4. **The Spook (*Burn Notice*, Phase 3: Income):** Gain `+$2` cash; optionally permanently return `1` owned **Gray Legacy Die** to the box for `+$3` cash (if pulled from a **Shield slot**, it no longer blocks in Phase 4).
5. **The Prodigy (*Arbitrary Code Execution*, Phase 1: Step 4 — after all rerolls are finished, before assigning dice to In Production):** Turn `1` other rolled die in your active pool to any legal non-Star face of its color other than the **Secret face**.
6. **The Cipher (*Algorithmic Parity*, Phase 3: Income):** Gain `+$2` cash AND `+1 🔬` Research Token (unchanged baseline anchor).

### Primary Findings & Critical Alerts

1. **CRITICAL FINDING — Operator Starvation Risk (85.1% 0-Yield Rate):** Under the literal proposed text for *The Operator* (`+1 🔬` per die in Processing Box), the ability yields **`0 🔬` in 85.1% of all Purple Star activations** across a full match (and **100% in Round 1**, **95.6% in Round 2**). The overall expected value is a meager **`0.17 🔬`**, making it by far the weakest and most swingy ability in the game. We present three tuning remedies for User decision.
2. **Acoustic Scales Exceptionally Well Across Player Counts:** Distinct exited colors (including Signature Cubes, which exit in 58% to 75% of drops) average **`$3.85` in 2P**, **`$3.98` in 3P**, and **`$4.04` in 4P**. The `+$5` cap maintains tight balance across player counts while rewarding escalating threat.
3. **Spook's Euro Die-Culling Creates a High-Skill Tempo Lever:** Burning weak Gray Legacy dice (`$2` baseline + `$3` burn = `$5` cash) provides massive early-game purchasing liquidity and permanently purges low-efficiency starter dice from the CI/CD pipeline, bounded by the player's finite supply of 2 (or 3) Gray dice.
4. **Phreaker Modernization Smooths Game Flow:** Replacing manual Scanned-die re-rolling with `+$1` cash and `+1` Release Bandwidth eliminates tactile downtime and breaks the pipeline bottleneck that throttles players in 21%–38% of mid-to-late game rounds.
5. **Prodigy Phase 1 Step 4 Placement Resolves Timing Ambiguities:** Anchoring *Arbitrary Code Execution* strictly to Step 4 (post-rerolls, pre-assignment) eliminates reroll recursion bugs and delivers deterministic agency worth **`$2.00–$3.50`** in strategic flexibility.

---

## 1. Canonical Terminology & Governance Alignment

All terminology in this document and the proposed rule updates has been strictly audited against `GLOSSARY.md` (Section 7).

* **Compliant Terms Utilized:** *White Hat Operative*, *White Hat Dossier Card*, *Signature Protocol*, *Purple Proprietary Specialist Die*, *Cube Tower*, *Compiler Drop*, *Operative Signature Cube*, *Target Lock*, *Signature Attack*, *Exit Tray*, *Staging Cup*, *Company Terminal Mat*, *Client Company*, *Institutional Override*, *CI/CD Pipeline*, *Ready for Release Zone*, *In Production Area*, *Shield Slots*, *Income Slot*, *Under Development Pipeline*, *Processing Box*, *Scanned Box*, *Release Bandwidth*, *Triage Bandwidth*, *Conveyor Triage*, *Scanned Graduation*, *Corporate Secrets*, *Market Share*, *Research Token (`🔬`)*, *Market Leader Bonus*, *Glitched Shield Slots*.
* **Prohibited Deprecated Terms Verified Absent:** *Consultancy*, *Consultancy Terminal Mat*, *Lead Consultant*, *CISO*, *Patches / 🔧*, *Unpatched Zone*, *Demote*, *Zero Wear Retention*, *Malware Fizzle*, *Emergency Hotfix*, *Passive Firewall*, *Cryptographic Patents Track*, *FinSec*, *Ransom Insurance*, *Threat Bounty*.

---

## 2. Activation Probability of Face 6 (`Purple ★`)

Every player begins with **1 Purple Proprietary Specialist Die** in their Ready for Release Zone. Their 2nd Purple die rests in their Personal Reserve until unlocked via the **Public Relations Track Level 3 Breakthrough** (typically reached between Rounds 4 and 6 by PR-focused players, or later by eco-heavy players).

### Purple Die Face Architecture

$$\text{Faces: } [1: \text{Block 1 Any}, \; 2: \text{Block 1 Any}, \; 3: +\$2, \; 4: +\$1 \ \& \ +1 \🔬, \; 5: \text{Secret face (+1 VP)}, \; 6: \text{Purple } \star]$$

### Mathematical Roll Probabilities

Let $P(\star)$ be the probability of rolling Face 6 on a Purple die under standard Yahtzee rerolls (up to 2 free rerolls, 3 rolls total):

* **Raw Single Roll (0 rerolls):**
  $$P(\star) = \frac{1}{6} \approx 16.67\%$$
* **1 Reroll Allowed (2 rolls total):**
  $$P(\star) = 1 - \left(\frac{5}{6}\right)^2 = \frac{11}{36} \approx 30.56\%$$
* **Standard 2 Free Rerolls (3 rolls total, baseline):**
  $$P(\star) = 1 - \left(\frac{5}{6}\right)^3 = \frac{91}{216} \approx 42.13\%$$
* **Release Track Level 4 (+1 extra free reroll, 4 rolls total):**
  $$P(\star) = 1 - \left(\frac{5}{6}\right)^4 = \frac{671}{1296} \approx 51.77\%$$

### Tactical Retention vs. Pure Hunting

While a player hunting purely for Face 6 reaches a $42.13\%$ trigger rate, actual play involves tactical trade-offs:
1. **Defensive Priority:** Faces 1 & 2 provide `Block 1 Any` shields ($33.33\%$ raw chance). When threat in the Staging Cup or internal baffles is high, players keep a shield face rather than risking taking unblocked compiler damage.
2. **Secret Banking Priority:** Face 5 is a Secret face ($16.67\%$). If a player seeks Corporate Secrets for scoring or tempo, they retain Face 5.
3. **Empirical Activation Rate:** Telemetry across 10,000 baseline games indicates that with 1 Purple die, players hold and resolve Face 6 In Production on **$23.5\%$ to $28.0\%$ of rounds**.
4. **Double Purple Dice (Post-PR L3 Breakthrough):**
   * Probability of $\ge 1$ Star (hunting): $1 - (125/216)^2 \approx 66.50\%$.
   * Probability of exactly 2 Stars (double trigger): $(91/216)^2 \approx 17.75\%$.
   * Expected Stars per round when hunting: $2 \times 42.13\% = 0.843$ Stars/round.

---

## 3. Deep Dive & Mathematical Modeling: The 6 White Hats

### 3.1 The Operator (*Logistics Bounty*, Phase 3: Income)

* **Proposed Text:** Gain `+1 🔬` Research Token per die currently in your **Processing Box**.
* **Timing:** Phase 3: Income.
* **Mechanism:** Checks the instantaneous inventory of dice resting in the player's Processing Box at the moment Phase 3 resolves.

#### Empirical Distribution of Processing Box Inventory in Phase 3

To model this accurately, a Monte Carlo simulation (500 games, 1,180 observed Purple Star activations) tracked the exact count of dice in the Processing Box ($N_{PB}$) during Phase 3 specifically on rounds where Purple Face 6 was rolled and held In Production:

| Processing Box Dice ($N_{PB}$) | Frequency (on Star Trigger) | Percentage | Marginal Research Yield |
| :---: | :---: | :---: | :---: |
| **0 dice** | **1,004** | **85.1%** | **`0 🔬`** |
| **1 die** | 156 | 13.2% | `+1 🔬` |
| **2 dice** | 17 | 1.4% | `+2 🔬` |
| **3 dice** | 3 | 0.3% | `+3 🔬` |
| **4+ dice** | 0 | 0.0% | `+4 🔬` |

#### Breakdown by Match Phase (Rounds 1–9)

| Round | Observed Star Triggers ($N$) | P(PB = 0 dice) | Mean Research EV |
| :---: | :---: | :---: | :---: |
| **Round 1** | 272 | **100.0%** | **`0.00 🔬`** |
| **Round 2** | 229 | **95.6%** | **`0.04 🔬`** |
| **Round 3** | 161 | 82.0% | `0.20 🔬` |
| **Round 4** | 119 | 83.2% | `0.18 🔬` |
| **Round 5** | 110 | 70.9% | `0.31 🔬` |
| **Round 6** | 97 | 73.2% | `0.33 🔬` |
| **Round 7** | 89 | 68.5% | `0.36 🔬` |
| **Round 8** | 46 | 84.8% | `0.22 🔬` |
| **Round 9** | 45 | 62.2% | `0.38 🔬` |
| **Overall** | **1,180** | **85.1%** | **`0.17 🔬`** |

#### Root Cause Analysis: Why Does Operator Starve?

1. **The Purple Die Cannot Fuel Itself:** The Purple die that rolled Face 6 is In Production triggering Logistics Bounty; it is *not* in the Processing Box.
2. **Starter Pool Limitations:** In Rounds 1–3, a player owns 2 Gray dice, 1 starting colored die, and 1 Purple die. Gray dice have zero Secret faces. Therefore, **only the single starting colored die can enter the Processing Box in early rounds**.
3. **Low Secret Probability on 1 Die:** A single colored die has only a 16.7% base chance to roll Face 5. If it rolls any of its other 5 faces, the Processing Box is completely empty ($N_{PB} = 0$).
4. **Conveyor Triage Drainage:** In Phase 6 of every round, Conveyor Triage moves up to 1 die (or 2 at Triage L4) from Processing to Scanned. Consequently, pending dice rarely accumulate into a multi-die backlog unless a player buys multiple colored dice and rolls multiple Secret faces in the same turn.
5. **Comparison to Cipher:** Cipher gains `+$2` cash AND `+1 🔬` unconditionally every time (worth `~$4.00`). Operator under this wording gains `$0` cash and an expected `0.17 🔬` (worth `~$0.34`), doing literally **nothing** in 85% of triggers!

#### Operator Tuning Options for User Review

* **Option A (Literal As-Written):** `+1 🔬` per die in Processing Box.
  * *EV:* `0.17 🔬` ($0.00 in R1, $0.04 in R2). High risk of negative player experience when rolling a Star yields nothing.
* **Option B (Base + Scaling — RECOMMENDED):** *"Gain `+1 🔬` Research Token, plus `+1 🔬` per die currently in your Processing Box."*
  * *EV:* `1.17 🔬` (`1.00 🔬` in R1, `1.36 🔬` in late game). Guarantees a reliable baseline matching the v0.40 baseline while providing exciting scaling when secrets backlog.
* **Option C (Floor Guarantee):** *"Gain `+1 🔬` per die currently in your Processing Box (minimum `1 🔬`)."*
  * *EV:* `1.02 🔬`. Guarantees `1 🔬` on empty box, yields `2 🔬` if 2 dice are present.

---

### 3.2 The Phreaker (*Jumper Diagnostics*, Phase 3: Income)

* **Proposed Text:** Gain `+$1` cash AND `+1` **Release Bandwidth** this round (applies in Phase 6 Step 3).
* **Timing:** Income collected in Phase 3; `+1` Release Bandwidth applies during Phase 6 Step 3 (Scanned Graduation).
* **Mechanism:** Grants immediate cash liquidity, plus expands the maximum number of dice that can graduate from the Scanned Box to the Ready for Release Zone at the end of the round.

#### Throughput & Pipeline Bottleneck Modeling

In Phase 6 Step 2 (Production Return), all surviving dice In Production move into the Scanned Box. In Phase 5, any newly bought colored dice ($4–$6) also enter the Scanned Box. Baseline Release Bandwidth is **4** (upgradable to 5 at Level 2, and 6 at Level 4).

If total dice in Scanned exceeds Release Bandwidth, the excess dice are **trapped in Scanned** and cannot be rolled in the subsequent round!

A simulation of 500 games (7,922 player-rounds) tracked the frequency of Scanned Box bottlenecks (excess dice $> \text{Release Bandwidth}$):

| Scanned Box Surplus Dice | Frequency | Percentage | Pipeline Impact |
| :---: | :---: | :---: | :---: |
| **0 excess dice** (no bottleneck) | 5,886 | 74.3% | Normal graduation |
| **1 excess die** (bottlenecked) | **1,254** | **15.8%** | **1 die stuck in Scanned!** |
| **2 excess dice** | 455 | 5.7% | 2 dice stuck |
| **3+ excess dice** | 327 | 4.2% | Severe backlog |

#### Bottleneck Rate by Round

* **Round 1:** $0.0\%$ (4 dice in pool $\le$ 4 bandwidth).
* **Round 2:** **$23.9\%$** (first dice purchases enter Scanned).
* **Round 3:** **$16.4\%$**.
* **Round 4:** **$21.2\%$**.
* **Rounds 5–9:** **$33.1\% – 37.6\%$** of all player-rounds suffer graduation bottlenecks!

#### Economic & Strategic Valuation

1. **Unconditional Income:** `+$1` cash immediately in Phase 3.
2. **Tempo Value of `+1` Release Bandwidth:**
   * When bottlenecked ($~26\%$ of rounds overall, $~35\%$ in mid/late game), Phreaker allows 1 additional die to graduate into Ready for Release for next round.
   * Rolling an extra colored die yields an average of `~$1.80–$2.20` in resources, shields, or secrets.
   * Thus, the expected tempo value is $0.26 \times \$2.00 \approx \$0.52$.
3. **Research Savings:** In addition, Phreaker allows players to delay spending `1–2 🔬` on the Release Track early, reallocating those tokens to Defense Grid or Triage.
4. **Total Equivalent EV:** `+$1.00 cash` + `~$0.52 tempo` = **`~$1.52` equivalent value**.
5. **Quality of Life Improvement:** Eliminates the physical dice rolling in Phase 3 from the legacy protocol, drastically accelerating round throughput.

---

### 3.3 The Acoustic (*Resonance Sensor*, Phase 3: Income)

* **Proposed Text:** Gain `+$1` cash per distinct cube color that exited the **Cube Tower** this round (including **Operative Signature Cubes**), up to `+$5` max.
* **Timing:** Phase 3: Income.
* **Mechanism:** Evaluates all unique cube colors that exited the Cube Tower during this round's Phase 2 Compiler Drop. Compiler colors include `Red`, `Blue`, `Green`, and `Black`. Any exited Operative Signature Cube counts as a distinct color (5th color category), capped at `+$5` max.

#### Simulation Results Across Player Counts (v0.43.0 Canonical Baseline)

Simulations of 300 games per player count (2,250–2,525 drops) yielded the following distributions of distinct exited colors:

| Distinct Colors Exited | 2-Player Match | 3-Player Match | 4-Player Match | Cash Payout |
| :---: | :---: | :---: | :---: | :---: |
| **0 colors** (Empty Tray Overflow) | 0.0% | 0.2% | 0.2% | `$0` |
| **1 color** | 1.6% | 1.2% | 1.0% | `$1` |
| **2 colors** | 8.0% | 6.3% | 4.8% | `$2` |
| **3 colors** | 22.6% | 20.3% | 18.5% | `$3` |
| **4 colors** | 39.7% | 36.3% | 39.6% | `$4` |
| **5 colors** (4 Compiler + Signature) | **28.2%** | **35.7%** | **35.8%** | **`$5` (Max)** |
| **Mean Acoustic Payout** | **`$3.85 cash`** | **`$3.98 cash`** | **`$4.04 cash`** | — |

#### Signature Cube Exit Rates

* **2-Player:** Signature cubes exit in **58.1%** of all compiler drops.
* **3-Player:** Signature cubes exit in **70.0%** of drops.
* **4-Player:** Signature cubes exit in **75.1%** of drops.

#### Scaling & Dynamic Analysis

1. **Tight Scaling Across Player Counts:** Mean payout shifts only from **`$3.85` (2P)** to **`$4.04` (4P)**. The `+$5` ceiling perfectly cushions player-count scaling, preventing Acoustic from hyper-inflating in 4-player games.
2. **Pacing Curve:**
   * **Round 1:** `$2.85 – $2.95` (compiler primed with 4 cubes; no signature cubes staged yet).
   * **Rounds 2–5:** `$3.66 – $4.10`.
   * **Rounds 6–9 (Late Game / Avalanche):** `$4.10 – $4.57`.
3. **Balance Assessment:** Acoustic delivers pure cash liquidity that scales organically with board state tension. At an average of `~$3.95 cash`, it is highly competitive with Cipher (`$2 cash + 1 🔬` $\approx \$4.00$).

---

### 3.4 The Spook (*Burn Notice*, Phase 3: Income)

* **Proposed Text:** Gain `+$2` cash; optionally permanently return `1` owned **Gray Legacy die** to the box for `+$3` cash (if pulled from a **Shield slot**, it no longer blocks in Phase 4).
* **Timing:** Phase 3: Income.
* **Mechanism:** Grants unconditional `+$2` cash. In addition, the player may cull 1 of their weak Gray starter dice, receiving an immediate `+$3` cash bonus (total `+$5` cash on burn).

#### Economic & Bag-Thinning Analysis

1. **Finite Resource Pool:**
   * Each player starts with exactly **2 Gray Legacy dice**.
   * A player may gain a 3rd Gray die if they unlock the **Triage Track Level 1 Breakthrough**.
   * Therefore, across an entire match, *Burn Notice* can be executed at most **2 to 3 times total**.
2. **Starter Die Culling Value:**
   * Gray dice have the weakest resource outputs in the game: 2 shields (33%), `$1 & 1 🔬` (17%), `$1 / 1 🔬` (33%), and `1 🔬` (17%). Their expected non-shield economic yield is only `~$1.75`.
   * Central Market colored dice produce powerful specialized outputs: Red yields `$2` cash and Market Share; Blue yields Corporate Secrets (`1 VP`); Green yields `2 🔬`; Yellow yields `2 Market Share`.
   * In a game with strict **Release Bandwidth** limits (4 to 6 dice), retaining weak Gray starter dice clogs the CI/CD pipeline, preventing high-impact colored dice from graduating.
   * In deckbuilding theory, culling starter cards is worth `+$2–$3` in lifetime efficiency. Spook not only culls the die for free, but **pays the player `+$3` cash** to do so!
3. **Massive Liquidity Injection:**
   * Executing the burn yields an immediate **`+$5` cash payout** in Phase 3.
   * In Phase 5 Operations, this funds an immediate colored die purchase (`$4–$6`) or 1–2 Public Relations Market Share regains (`$3` each).
4. **Tactical Shield Trade-Off:**
   * If the burned Gray die was assigned to a Shield slot in Phase 1, removing it strips `1 Shield` for Phase 4 Attack Resolution.
   * If incoming compiler threat has unblocked cubes, burning a shield die will result in suffering damage (`1 Market Share loss` from Red, `1 Glitched Shield Slot` from Green, or `1 Secret loss` from Blue).
   * This creates a rich Euro risk/reward decision: players will burn from Shield only if they have surplus shields, or if the `$3` cash is worth the damage.

---

### 3.5 The Prodigy (*Arbitrary Code Execution*, Phase 1: Step 4)

* **Proposed Text:** Turn `1` other rolled die in your active pool to any legal non-Star face of its color other than the **Secret face**.
* **Timing:** Phase 1: Step 4 — after all Yahtzee rerolls are finished, before assigning dice to In Production.
* **Mechanism:** Allows the player to inspect their entire rolled active pool and adjust 1 other die to any desired non-Star, non-Secret face of that die's color.

#### Flexibility & Bad-Luck Mitigation Modeling

Prodigy acts as an autonomous optimizer, eliminating bad roll variance and converting a player's worst rolled face into the best possible face for the current situation:

* **Clutch Defensive Conversion (Phase 2 Threat Anticipation):**
  * If Staging Cup / stuck threat is lethal and the player rolled insufficient shields, Prodigy turns a Gray die (e.g. rolled `+1 🔬`) or a White Contractor die to `Block 1 Any`.
  * Value: Prevents 1 unblocked cube damage = preserves `1 Corporate Secret` (`1 VP`) or avoids a `Glitched Shield Slot` $\to$ **Worth `$2.50 – $3.50`**.
* **Economic Maximization (Safe Compiler Drops):**
  * **Green Die:** Turn a low `1 🔬 / $1` roll to Face 1 (`+2 🔬`) $\to$ gain `+2 Research Tokens` (worth `~$3.50`).
  * **Yellow Die:** Turn a `$1 & 1 MS` roll to Face 1 (`+2 Market Share`) $\to$ gain `2 Market Share` (equivalent to `$6.00` in PR track regains!).
  * **Red Die:** Turn Face 1 to Face 2/3/4 (`+$2` cash).
  * **White Contractor Die:** Turn a dangerous `Glitch` face into Face 1 (`+$1 & +1 🔬`) or Face 3 (`Block 1 Any`), neutralizing the contractor drawback!
* **Forbidden Faces:**
  * Cannot set Face 5 (Secret face) — prevents free VP generation.
  * Cannot set Face 6 (Star face) — prevents chaining infinite star triggers.
* **Deterministic Timing Advantage:** Placing this effect in Step 4 (after rerolls) ensures that the player knows their exact final pool state, maximizing strategic agency with zero RNG waste.
* **Expected Flexibility Value:** **`$2.50 to $3.50`** equivalent value per trigger.

---

### 3.6 The Cipher (*Algorithmic Parity*, Phase 3: Income)

* **Proposed Text:** Gain `+$2` cash AND `+1 🔬` Research Token (unchanged baseline).
* **Timing:** Phase 3: Income.
* **Mechanism:** Direct unconditional resource payout.
* **Economic Valuation:**
  * Cash: `$2.00`.
  * Research Token: `1 🔬` (worth `~$1.50–$2.50` based on track upgrade pricing and PR Breakthrough payouts).
  * Total Equivalent Value: **`$3.50 to $4.50`**.
  * Role: Serves as the golden control benchmark for testing and balance calibration.

---

## 4. Comparative Balance Matrix & Relative Valuation

The table below benchmarks the 6 Signature Protocols using standard resource exchange rates (`1 🔬 ≈ $1.75`, `1 Market Share ≈ $3.00`, `1 Secret = 1 VP ≈ $3.50`):

| White Hat | Signature Protocol | Timing | Baseline Yield | Conditional / Peak Yield | Equivalent EV per Activation | Strategic Identity |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Cipher** | *Algorithmic Parity* | Phase 3 | `$2 cash + 1 🔬` | `$2 cash + 1 🔬` (deterministic) | **`$3.75`** | Solid, reliable baseline anchor |
| **Acoustic** | *Resonance Sensor* | Phase 3 | `$1 – $5 cash` | `$3.85` (2P) to `$4.04` (4P) cash | **`$3.95`** | Threat monetization & tempo |
| **Spook** | *Burn Notice* | Phase 3 | `$2 cash` | `$5 cash` + starter die culling | **`$2.00 – $5.00+`** | High-tempo liquidity & deck-thinning |
| **Prodigy** | *Arbitrary Code Execution* | Phase 1 Step 4 | Non-star face change | Clutch shield or peak income | **`$2.50 – $3.50`** | Variance elimination & tactical agency |
| **Phreaker** | *Jumper Diagnostics* | Phase 3 & 6 | `$1 cash` | `$1 cash` + 1 die accelerated | **`$1.52`** (tempo) | Pipeline unclogging & fast scaling |
| **Operator** | *Logistics Bounty* *(Option A - As Written)* | Phase 3 | `0 🔬` (85.1% empty) | `1 – 3 🔬` (if secrets backlog) | **`$0.30` (`0.17 🔬`)** | **Severely underpowered / starved** |
| **Operator** | *Logistics Bounty* *(Option B - Proposed)* | Phase 3 | `1 🔬` baseline | `1 🔬 + 1 🔬 / PB die` | **`$2.05` (`1.17 🔬`)** | Balanced research engine with upside |

---

## 5. 36-Combination Pairing Analysis (6 Companies × 6 White Hats)

Each player pairs 1 Client Company (Institutional Override) with 1 White Hat Operative (Signature Protocol), yielding $6 \times 6 = 36$ distinct combinations.

```
+---------------------------------------------------------------------------------------------------+
|                            36 COMBINATION SYNERGY MATRIX OVERVIEW                                 |
+-------------------+----------------+----------------+----------------+----------------+-----------+
| Client Company    | Operator (B)   | Phreaker       | Acoustic       | Spook          | Prodigy   |
+-------------------+----------------+----------------+----------------+----------------+-----------+
| Meridian          | Strong Eco     | High Liquidity | Max Cash       | Hyper-Buy R1   | Stable    |
| Omnidyne          | High Synergy   | Double Flow    | Standard       | Solid Culling  | High Flow |
| Aegis             | Standard       | Standard       | High Defense   | Shield Cover   | Unbreachable|
| DTO               | Standard       | Standard       | Standard       | High Risk Eco  | Clutch Save|
| Helix             | Secret Bridge  | Flexible Reroll| Standard       | Reroll Defense | Deterministic|
| Prometheus        | Track Push     | Zero-Lag Buy   | Discount Stack | Mega-Discount  | Controlled|
+-------------------+----------------+----------------+----------------+----------------+-----------+
```

### Standout Synergies & Canonical Pairings

1. **The Operator + Helix Biomedical Consortium (Brute-Force Bypass):**
   * *Synergy:* Helix's override allows turning 1 die to the Secret face during Phase 1. That die immediately enters the Processing Box, guaranteeing that Operator triggers at least `+1 🔬` (or `+2 🔬` under Option B) in Phase 3. Solves Operator's early-game empty box dilemma!
2. **The Phreaker + The Prometheus Foundation (Algorithmic Arbitrage):**
   * *Synergy:* Prometheus purchases a colored die at a `$2` discount in Phase 5 Operations. That die enters Scanned. In Phase 6 Step 3, Phreaker's `+1` Release Bandwidth allows that newly bought die to graduate to Ready for Release *in the very same round*, completely bypassing the 1-round purchase lag!
3. **The Spook + Aegis Defense Relay (Baffle Echo):**
   * *Synergy:* If Spook burns a Gray die currently sitting in a Shield slot for `+$3` cash, the player loses 1 shield for Phase 4. Aegis's *Baffle Echo* can ignore 1 Attack cube, perfectly covering the defensive hole created by the burned shield!
4. **The Spook + Meridian Financial Trust (Capital Injection):**
   * *Synergy:* Spook's burn (`$5` cash) combined with Meridian's `$3` Capital Injection gives `$8` liquid cash in Round 1 or 2. Allows buying 2 market dice or 1 high-tier die + PR track regain on Turn 1!
5. **The Prodigy + Helix Biomedical Consortium (Deterministic Command):**
   * *Synergy:* Helix turns 1 die in Step 3; Prodigy turns another die in Step 4. Gives total deterministic control over 2 dice, virtually guaranteeing zero glitches, perfect shields, and maximum economic yield.
6. **The Phreaker + Omnidyne Systems (Canonical Pairing):**
   * *Synergy:* Omnidyne's *Magnetic Splice* pulls dice out of Processing; Phreaker's *Jumper Diagnostics* pushes dice out of Scanned. Unmatched CI/CD throughput.

---

## 6. Critical Edge Cases & Rule Invariants

### Edge Case 1: Acoustic Tracking Exited Signature Cubes
* **Rule Invariant (`INV-ACOUSTIC-SIG-01`):** In Phase 2, when an Operative Signature Cube exits the Cube Tower, it triggers Target Lock and **immediately returns to the owner's mat** (Section 2). In Phase 3, exited Signature Cubes are no longer physically in the exit tray.
* **Rule Text Specification:** Acoustic's rule text must specify: *"Gain `+$1` cash per distinct cube color that exited the Cube Tower during this round's Phase 2 Compiler Drop (counting `Red`, `Blue`, `Green`, `Black`, and `+1` if any Operative Signature Cubes exited), up to `+$5` max."*
* **Engine Implementation:** The simulation engine must store `last_distinct_exited_colors_count` during Phase 2 Compiler Drop execution so Phase 3 queries an immutable snapshot.

### Edge Case 2: Spook Gray Die Culling Zones & Double Triggers
* **Allowed Culling Zones:** The Gray Legacy die may be returned from **In Production** (Shield or Income slot), the **Scanned Box**, the **Processing Box** (if placed there by Blue Signature Attack), or the **Ready for Release Zone**.
* **Shield Removal Consequence (`INV-SPOOK-SHIELD-01`):** If the Gray die is pulled from a Shield slot in Phase 3, it is immediately removed and **does not block in Phase 4**.
* **Income Timing:** If pulled from the Income slot, it collects its Phase 3 income before being returned to the box.
* **Double Purple Stars (`INV-SPOOK-DOUBLE-01`):** If a player rolls 2 Purple Stars, *Burn Notice* triggers twice: the player gains `+$4` cash and may burn up to **2 distinct Gray Legacy dice** for `+$3` each (total `+$10` cash). Once a player owns 0 Gray dice, the burn option cannot be selected, but the baseline `+$2` cash still pays out.

### Edge Case 3: Phreaker Release Bandwidth Stacking & Duration
* **Duration (`INV-PHREAKER-DUR-01`):** The `+1` Release Bandwidth is strictly temporary for the current round and applies exclusively during **Phase 6 Step 3 (Scanned Graduation)**. At round end, Release Bandwidth resets to the player's track level.
* **Double Purple Stars (`INV-PHREAKER-DOUBLE-01`):** Two Purple Stars yield `+$2` cash AND `+2` Release Bandwidth this round.
* **Hardware Upgrade Interaction:** If a player upgrades their Release Track in Phase 5 Operations (e.g. Level 0 $\to$ Level 2, bandwidth 4 $\to$ 5), Phreaker's `+1` adds on top (total bandwidth = 6).

### Edge Case 4: Prodigy Timing & Step 4 Placement
* **Exact Timing Window (`INV-PRODIGY-TIMING-01`):** Resolves in **Phase 1: Step 4**, after all Yahtzee rerolls are completely finished and before assigning dice to In Production or Processing.
* **Choice Faces:** If Prodigy turns a die to a Choice Face (e.g. Red Face 1 `+1 Market Share / +$1`), the choice is declared during the subsequent Step 4 assignment.
* **Star & Secret Restrictions (`INV-PRODIGY-RESTRICT-01`):** May not select Face 5 (Secret face) or Face 6 (Star face) of any die color.
* **Target Die:** Must be another rolled die in the active pool (cannot retarget the Purple die that triggered it, unless 2 Purple dice rolled Star, in which case Star Die 1 can target Star Die 2).

---

## 7. Concrete Implementation & Engineering Plan

Upon User review and approval of this analysis, the SDLC engineering pipeline should proceed as follows:

### Phase 1: Engine & State Architecture (`sim/`)
1. **`sim/engine/state.py`:**
   * Add `distinct_exited_colors_this_round: int = 0` to `GameState` (populated in Phase 2).
   * Add `temp_release_bandwidth_bonus: int = 0` to `PlayerState` (cleared at round end).
2. **`sim/engine/phase1_roll_deploy.py`:**
   * Move `resolve_prodigy_purple_star_override` strictly into Step 4 (after rerolls loop, before slot assignments).
3. **`sim/engine/phase2_compiler.py`:**
   * Calculate and record `distinct_exited_colors_this_round` (threat colors $>0$, plus 1 if `len(last_exited_signatures) > 0`, min 0, max 5).
4. **`sim/engine/phase3_income.py`:**
   * Update `resolve_income_signature_protocols`:
     * **Operator:** Implement Option B (or User-selected option): `1 🔬` base + `len(player.glitched_dice)`.
     * **Phreaker:** Award `+$1` cash and set `player.temp_release_bandwidth_bonus += 1`.
     * **Acoustic:** Award `distinct_exited_colors_this_round` in cash (capped at 5).
     * **Spook:** Award `+$2` cash; hook bot method `choose_spook_burn_gray` to optionally remove 1 Gray die and award `+$3`.
5. **`sim/engine/phase5_pipeline_shift.py`:**
   * Effective Release Bandwidth in Step 3: `player.release_bandwidth + player.temp_release_bandwidth_bonus`.
   * Reset `temp_release_bandwidth_bonus = 0` at round completion.

### Phase 2: Bot Decision Hooks (`sim/bots/`)
* Implement `choose_spook_burn_gray(player, state)` in `BaseBot` and bot archetypes (evaluate whether player has surplus shields and needs cash for Phase 5 purchases).
* Update `choose_prodigy_purple_star_override` to prioritize defensive shields if compiler threat is dangerous, else highest-yielding income/research face.

### Phase 3: Telemetry & Unit Tests (`tests/`)
* Write unit tests for each operative verifying 1-star and 2-star double triggers, edge cases, and invariant compliance.
* Execute a 1,000-game balance sweep comparing win rates across the 6 White Hats and 36 pairings.

---

## 8. Recommendations & Next Steps

1. **Approve Operator Tuning Option B:** Transition *Logistics Bounty* to *"Gain `+1 🔬` Research Token, plus `+1 🔬` per die currently in your Processing Box"*. This eliminates the 85.1% fizzle rate and brings Operator to a viable, exciting `1.17 🔬` EV.
2. **Ratify Phreaker, Acoustic, Spook, and Prodigy Designs:** The mathematical models confirm that all four protocols are robust, balanced, thematic, and resolve longstanding mechanical pain points.
3. **Advance to Multi-Agent SDLC Hand-off:** Present this analysis to the User for sign-off, then proceed to the `principal-engineer` for spec creation and implementation.
