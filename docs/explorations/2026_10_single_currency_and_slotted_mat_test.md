# Exploration Archive: Single-Currency (`Secrets` + `🔧`) & Slotted 3-Row Terminal Mat

**Date:** 2026-10-30  
**Status:** Archived Exploration *(Not adopted into active [RULES.md](../../RULES.md) `v0.14.0` baseline)*  
**Prototype Script:** [`proto_single_currency_sim.py`](./proto_single_currency_sim.py)

---

## 1. Hypothesis & Mechanics Tested

Motivated by a 3-player physical playtest of `v0.14.0` where:
1. The Cube Tower escalated too slowly (`+1 Black Cube`/round and 0 Dirty Income taken by rational human players).
2. Money (`$7` start) felt too loose and lacked a late-game sink once Market dice sold out.
3. Red and Green defense had $\le 0$ net value compared to Blue defense (`85.1%` of all shields committed to Blue in `v0.14.0` baseline).

### Experimental Rules Explored
* **Single Currency (`Secrets` + `🔧`, cutting `$`):**
  * `Secrets` acted simultaneously as **Survival Health** (`<= 0` = Patient Zero), **Market Currency** (`3 Secrets` for R/G/P, `4 Secrets` for B/Y), and **VP** (`1 VP` per liquid Secret).
  * **Cold-Storage Archive Sink:** Spend `3` liquid Secrets in Phase 3 $\to$ bank `1` Cold-Storage Tape (`4 VP` safe offsite score).
  * **Backdoor Siphon ("Dirty Secrets"):** Gain `+3 Secrets` $\to$ add `1 Black Cube` to the Staging Cup + move `1 Ready die` to Unpatched.
* **Universal Slotted Terminal Mat (`Phase 1 → Phase 2 → Phase 3 → Unpatched`):**
  * **Row 1 (Boot):** Resource (`+Secret`, `+🔧`) and `Glitch` faces (Glitches demote 1 other slotted die before payouts).
  * **Row 2 (Defense):** Shield faces (`Red / Blue / Green`, with R/B/G dice given a 2nd shield via Choice faces).
  * **Row 3 (Operations):** All `★` faces slotted into Phase 3 (vulnerable to Phase 1 Glitches, `⚡ ON COMPILE` shockwaves, and Phase 2 Green Malware).
* **Escalating Tower & `⚡ ON COMPILE` Shockwaves:**
  * Phase 1 Black Pulse scaled to **`2 / 2 / 3` Black Cubes** across `v1.0 / v2.0 / v3.0` (`tower_ledge_capacity = 6.5`).
  * Incoming Version cards triggered an immediate **`⚡ ON COMPILE`** ability in Step 2A before shields resolved, plus surgical ongoing locks (e.g., locking solo `+1 Secret` faces, solo `+1 🔧` faces, or generic `Any` shields).
* **Recalibrated Attack Cube Triad:**
  * **Blue (Spyware):** Lose `1 Secret` *(ignores `🔧`)*.
  * **Red (Ransomware):** Lose `1 🔧` *(if at `0 🔧`, leak `1 Secret`)*.
  * **Green (Malware):** Unpatch `1` slotted `Phase 3 (★)` die first; if none slotted, unpatch `1` Ready die *(+ a 2nd Ready die if holding `3+` Ready dice)*.

---

## 2. Simulation Results ($N=1,000$ Games per Cell)

### A. 3-Player Comparison (`v0.14.0` Baseline vs. Single-Currency Prototype)

| Metric | `v0.14.0` (3P Human Table — 0 Dirty) | `v0.14.0` (3P Sim Bots) | **Prototype A (Immediate Compile Drop + `⚡ ON COMPILE`)** | **Prototype B (Cup Payload + `⚡ ON COMPILE`)** |
| :--- | :---: | :---: | :---: | :---: |
| **Average Match Rounds** | 9.17 rds | 8.23 rds | **5.97 rds** | **6.27 rds** |
| **`v2.0` Compile Round (% Reached)** | R4.15 (100%) | R3.93 (100%) | **R3.48 (100%)** | **R3.48 (100%)** |
| **`v3.0` Compile Round (% Reached)** | R8.37 (70%) | R6.97 (84%) | **R5.63 (85%)** | **R5.64 (87%)** |
| **Exited Attack Cubes (`v1 → v2 → v3`)** | `2.77 → 4.03 → 4.94` | `2.78 → 4.18 → 5.38` | **`3.11 → 5.18 → 6.84`** | **`2.76 → 4.68 → 6.88`** |
| **Shield Commit Share (`R / B / G`)** | `11.5% / 85.1% / 3.3%` | `11.7% / 85.0% / 3.3%` | **`32.0% / 41.3% / 26.7%`** | **`32.2% / 40.8% / 27.0%`** |
| **Cube Block Rate (`R / B / G`)** | — | — | **`32.4% / 36.2% / 33.0%`** | **`34.6% / 36.9% / 36.0%`** |
| **Phase 2 Shields Knocked Out / Game** | 0.00 | 0.00 | **3.03 dice** | **3.14 dice** |
| **Phase 3 `★` Dice Sniped / Game** | 0.00 | 0.00 | **3.38 dice** | **3.24 dice** |
| **Dirty Siphons Taken / Game** | **0.00** | 2.47 | **2.21** | **2.29** |
| **Singularity / Patient Zero / Wipeout** | `5.5% / 91.0% / 3.5%` | `18.1% / 76.4% / 5.5%` | **`6.3% / 81.1% / 12.6%`** | **`11.1% / 80.4% / 8.5%`** |
| **Early Deaths ($\le$ R4)** | 1.7% | 3.3% | **7.7%** | **6.1%** |
| **Survivor Colored Dice (Unpatched)** | — | — | **3.29 (0.51)** | **3.63 (0.51)** |
| **Survivor End Secrets / Archived Tapes**| `4.52 Secrets` (+`$1.04`) | `4.32 Secrets` (+`$0.91`) | **`1.51 Secrets` / `0.31 Tapes`** | **`1.52 Secrets` / `0.37 Tapes`** |

### B. All Player Counts (`2P / 3P / 4P`) Under Prototype B (`Start Secrets = 11/11/13, Track = 5/6/6`)

| Pod | Avg Rounds | `v2` / `v3` Compile | Exited Cubes (`v1 → v2 → v3`) | Block Rate (`Red / Blue / Green`) | Dirty / Game | Singularity / PZ / Wipeout |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **2P** | **5.76** | `R3.05` / `R4.93` | `2.75 → 4.67 → 7.06` | **`33.9% / 40.0% / 36.4%`** | **1.88** | `22.3% / 48.8% / 28.9%` |
| **3P** | **6.27** | `R3.48` / `R5.64` | `2.76 → 4.68 → 6.88` | **`34.6% / 36.9% / 36.0%`** | **2.29** | `11.1% / 80.4% / 8.5%` |
| **4P** | **5.79** | `R3.28` / `R5.16` | `2.86 → 5.20 → 7.40` | **`36.5% / 37.7% / 40.9%`** | **3.78** | `13.8% / 83.0% / 3.2%` |

---

## 3. Key Findings & Why This Exploration Was Shelved

1. **What Worked Well:**
   * **Defense Parity:** Making each attack color threaten a distinct vulnerability (`Blue = -1 Secret`, `Red = -1 🔧 / leak 1 Secret`, `Green = Snipe Phase 3 ★ / unpatch Ready dice`) balanced cube block rates to `~35% / 37% / 36%` (solving the `85.1%` Blue monopoly).
   * **Pre-Trigger Slotting Tension:** Slotting dice into `Phase 1 / 2 / 3` rows created ~3.1 knocked-out shields and ~3.3 sniped `★` dice per game.
   * **Escalation & `⚡ ON COMPILE`:** Increasing Black cube input and firing an immediate `⚡ ON COMPILE` ability made version transitions feel impactful and compressed match length to ~6 rounds.
2. **Structural Friction Discovered in Single Currency (`Secrets` Only):**
   * **Life Bar vs. Purchasing Budget Coupling:** When `Secrets` serves as both your elimination life bar (`<= 0` = dead) and your market currency (`3–4 Secrets` per die), buying dice in Phase 3 directly lowers your survival buffer right before the next Cube Tower drop. With a tight starting pool (`6–8 Secrets`), buying a single die caused **`89%–96%` Early Deaths ($\le$ R4)** and **3.2-round blowouts**.
   * **Inflated Starting Pool Requirement:** Preventing early blowouts required inflating Starting Secrets to `11–13` (replacing `$7` cash + `8` Secrets in one pool) and enforcing high safety-floor thresholds (`6–8 Secrets`) before players could safely buy a die.
   * **Wrench Double-Dip Risk:** If Phase 2 attacks aggressively drain `🔧` tokens (`-2 🔧` on Red, `-1 🔧` on Green) *and* unpatch dice simultaneously, players enter Phase 3 with `0 🔧` left to repair worn Shield dice, collapsing their dice pool within 3–4 rounds.
