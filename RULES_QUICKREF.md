# Too Many Secrets — Quick Reference Rules

**Players:** 2–4 | **Playtime:** ~45–60 min | **Format:** Simultaneous / Turn-Based Hybrid

---

## 1. Overview & Objective

You are a **White Hat Operative** contracted to defend a **Client Company** against **Project: SETEC** (the Rogue Agent). Each round, SETEC's mainframe compiler drops threat cubes while players roll custom software module dice, manage their CI/CD pipeline, upgrade terminal hardware, and defend corporate assets.

* **Survival:** If your **Corporate Secrets** fall to `0` or below, you suffer a **Total Data Breach**, become **Patient Zero**, and are **eliminated**.
* **Market Collapse:** If any surviving player's **Market Share** drops to `0`, the current round becomes the **Final Round** (no player is eliminated).
* **Victory:** Among surviving operatives, the player with the most **Corporate Secrets** (`1 Secret = 1 VP`) at game end wins.

---

## 2. Setup Checklist

1. **SETEC Roadmap & Compiler:**
   * Place **1 `v1.0`**, **1 `v2.0`**, and **1 `v3.0`** Version Card face-up in a row next to the Cube Tower. Set the Version Marker on `v1.0`.
   * **Prime Compiler:** Drop **1 Red, 1 Blue, 1 Green, and 1 Black Cube** into the empty Cube Tower. Return any cubes that exit into the tray to the supply; stuck cubes stay inside.
   * Place starting cubes listed on the `v1.0` card into the **Staging Cup** (typically `2 Red, 1 Blue, 1 Green, 0 Black`).
2. **Central Software Market:**
   * For each color (**Red, Blue, Green, Yellow**), reveal **1 random Variant Card** and place a stack of **`2 × Players`** dice of that color on it. *(Purple dice are not in the central market).*
3. **Player Terminal Mats:**
   * Each player takes 1 **Company Terminal Mat** with all 4 Hardware Tracks at **Level 0**.
   * Place **1 Glitched Shield Slot Marker** on your Defense Grid (leaving 1 clean and 1 glitched slot available at baseline Defense Capacity 2).
   * Place **1 Purple Specialist Die** on your mat's **Personal Reserve** slot.
4. **Deal Dossiers & Starting Pools:**
   * Deal **1 random Client Company Card** and **1 random White Hat Dossier Card** to each player.
   * Client Company gives 3 Version Override tokens (`v1.0`, `v2.0`, `v3.0`), set to **Available**.
   * Place starting dice into your **Ready for Release Zone**:
     * **2 Gray Legacy Dice**
     * **1 Purple Specialist Die**
     * **1 Starting Colored Die** matching your Client Company (Red: *Meridian, Prometheus*; Blue: *DTO, Aegis*; Green: *Omnidyne, Helix*).
5. **Starting Resources:**
   * **Money:** `$6`
   * **Research:** `0 🔬`
   * **Corporate Secrets:**
     * **2 Players:** `3 Secrets`
     * **3–4 Players:** `4 Secrets`
   * **Starting Market Share (also maximum track cap):**
     * **2 Players:** `13`
     * **3 Players:** `16`
     * **4 Players:** `17`
6. Randomly assign the **First Player Marker**.

---

## 3. Round Structure

Each round consists of **6 Phases**:

```
[Phase 1: Roll & Deploy] (Simultaneous)
       ↓
[Phase 2: Compiler Drop & Corruption] (Simultaneous)
       ↓
[Phase 3: Income] (Simultaneous)
       ↓
[Phase 4: Attack Resolution] (Simultaneous)
       ↓
[Phase 5: Operations] (Clockwise Turns)
       ↓
[Phase 6: CI/CD Pipeline Shift] (Simultaneous)
```

---

### Phase 1: Roll & Deploy (Simultaneous)

1. **Pulse & Version Advance:**
   * If SETEC's corruption track filled last round, switch to the new version now: discard any unspent override from the previous version, unlock the new version override, and advance the marker.
   * Add **1 Black Cube** from the supply into the **Staging Cup**.
2. **Roll Active Pool:** Roll all dice in your **Ready for Release Zone**.
3. **Rerolls:** Up to **2 free rerolls** of any subset of dice (3 rolls total; **+1 extra reroll** at Release Track Level 4).
4. **Deploy Dice:**
   * **Secret Faces (Face 5 on Red, Blue, Green, Purple):** Move **immediately to the Processing Box** in Under Development (banks secrets later upon exit).
   * **Clean Glitches:** 
     * Green *G1 Self-Healing Kernel* cleans 1 Glitched Shield Slot and stays In Production.
     * Any die showing a **Shield** may be spent to clean 1 Glitched Shield Slot (move that die directly to the **Scanned Box**; it does not block this round).
   * **In Production (Hardware Capacity):**
     * **Shield Slots:** Assign dice showing `Block 1 Any` up to your **Defense Capacity** minus **Glitched Shield Slots**. Excess shields must move to Income (produce `$0` if no income face).
     * **Income Slot:** Assign all remaining dice (producing `$`, `🔬`, Market Share, or `★`).
     * Choice faces (`/`) are committed now. Generic shields are not locked to a specific color yet.

---

### Phase 2: Compiler Drop & Corruption (Simultaneous)

1. **Drop:** Empty the entire **Staging Cup** into the **Cube Tower**. Group exited cubes by color in the tray.
   * Exited **Red, Blue, and Green Attack Cubes** stay in the tray until Phase 4.
2. **Buffer Overflow:** If **0 cubes exit**, no attacks occur and no corruption advances. Income is still collected in Phase 3. Add **1 Red, 1 Blue, and 1 Green Cube** to the Staging Cup for next round.
3. **Resolve Black Cubes:** Advance exited Black Cubes one-by-one onto the active Version's **Corruption Track**, immediately resolving each space's effect:
   * **Add Cubes:** Add printed cubes to the **Staging Cup** (primes next round).
   * **Player with Most [X] Loses:** Player(s) with highest resource lose printed amount. On ties, **all tied players suffer the full loss**.
   * **Least Takes from Most:** Player with least takes printed amount from player with most. If all players are tied, the effect fizzles.
   * **Glitched Slots:** Player(s) with fewest glitched slots turn printed slots into Glitched Shield Slots.
   * **Return Dice:** Player(s) with most colored dice return printed amount to supply (Gray starter dice cannot be returned; returned processing dice lose their Secret).
4. **Version Advance & Spillover:**
   * When `v1.0` (4 spaces) or `v2.0` (5 spaces) fills, excess Black cubes spill onto the next card immediately. The current version remains active for overrides through Phase 6; transition occurs at the start of next round's Phase 1.
   * **Singularity Trigger (`v3.0` Fills):** When the 6th space of `v3.0` is covered, resolve that space, then **the game ends immediately at the end of Phase 2!** Skip Phases 3–6 and proceed directly to Final Scoring.
5. **Breach Check:** Any player dropping to `<= 0 Secrets` is eliminated as **Patient Zero**. If at least one player survives, this round becomes the **Final Round** (survivors finish Phases 3–6). If all breach, game ends immediately as a **Total Wipeout**.

---

### Phase 3: Income (Simultaneous)

Collect all resources produced by dice still deployed **In Production** (Income and Shield slots):
* Collect **`$` Cash**, **`🔬` Research Tokens**, and **Corporate Secrets** (Blue 1 & 2).
* **Market Share:** Resolve Red Face 1 and Yellow Market Share faces (capped at your starting maximum).
* **Star (`★`) Effects:** Resolve immediate card abilities and operative Signature Protocols.
* **Customer Poaching (*R3*):** Clockwise from First Player, take `1` Market Share from the rival with the most Market Share (> 0).

---

### Phase 4: Attack Resolution (Simultaneous)

Calculate total attack cubes in the tray: **Red**, **Blue**, and **Green**. Each player simultaneously allocates their available `Block 1 Any` shields:
* **Mandatory Blocking:** Every active shield must block an attack cube if any unblocked cubes remain. You choose how to distribute shields among colors.
* **Unblocked Cube Penalties:**
  * **Red (Market Manipulation):** Lose **`1` Market Share** per unblocked Red cube (minimum 0).
  * **Blue (Spyware):** Lose **`1` Corporate Secret** per unblocked Blue cube.
  * **Green (Malware):** Turn **`1` Shield Slot** into a **Glitched Shield Slot** per unblocked Green cube (capped at your Defense Capacity).
* **Post-Damage Triggers:**
  * **Defense Grid Level 4:** Gain **`+$1` per Attack Cube blocked** this phase (max `$3`).
  * **Recycle Cubes:** Place all exited Red, Blue, and Green Attack Cubes back into the **Staging Cup** for next round.
* **End Game Check:**
  * If a surviving player's Secrets drop to `<= 0`, they become **Patient Zero** (eliminated; current round is the Final Round).
  * If a surviving player reaches `0` Market Share, a **Market Collapse** is triggered (current round is the Final Round; player is NOT eliminated).

---

### Phase 5: Operations (Clockwise Turns)

Starting with the First Player, each player takes their Operations Turn:

1. **Hardware Track Upgrades (Limit 2 upgrades per turn):**
   * Spend **`🔬`** to raise any track one step: **`1 🔬`** for Level 1, **`2 🔬`** for Level 2, **`2 🔬`** for Level 3, **`3 🔬`** for Level 4.
   * **Breakthroughs (Levels 1 & 3):** Claim immediately when reaching that level (see Hardware Reference Table).
2. **Public Relations (PR) Regain:**
   * Spend **`$3` Cash per `+1` Market Share** (up to your track level cap: 1/turn at L0–1, 2/turn at L2–3, 3/turn at L4).
   * Does not count toward your limit of 2 hardware upgrades.
3. **Ad Campaign (*R2*):** If active in Phase 3, pay `$2` for `+1` Market Share (once per die).
4. **Purchase 1 Software Module Die (Limit 1 die per turn):**
   * Pay the `$` cost on the face-up Variant Card (`$4`–`$6`) to buy 1 colored die (**Red, Blue, Green, Yellow**).
   * Place purchased die into your **Scanned Box** (must graduate in Phase 6 before rolling).
   * Purple dice cannot be purchased from the market.
5. **Retain Research:** Research tokens have no storage cap and carry over.

---

### Phase 6: CI/CD Pipeline Shift (Simultaneous)

1. **Production Return:** Move all dice from **In Production** (Income and Shields) to your **Scanned Box**.
2. **Scanned Graduation (Hardware Throughput):** Move up to **Release Bandwidth** dice of your choice (`4` baseline, upgradable to `5` and `6`) from **Scanned Box $\to$ Ready for Release**.
3. **Conveyor Triage (Hardware Throughput):** Move up to **Triage Bandwidth** dice (`1` baseline, `2` at Level 4) from **Processing Box $\to$ Scanned Box**, **oldest first** (FIFO order):
   * Each die **banks its Secret** upon leaving Processing:
     * **Red:** `+2 Secrets`
     * **Blue:** `+2 Secrets` (`+3` if Defense Grid $\ge$ Level 3)
     * **Green:** `+2 Secrets` and clean `1` Glitched Shield Slot
     * **Purple:** `+1 Secret`
   * *Triage Level 4:* Gain `+1 🔬` for each die moved beyond the 2nd.
4. **Market Leader Bonus Check:** If any player banked a **Red Secret** this round (Phase 3 or 6), award the **Market Leader Bonus** by current Market Share:
   * **1st Place:** `+3 Secrets`
   * **2nd Place:** `+1 Secret`
   * *(Tied players each receive the full reward for that place. Patient Zeros are excluded).*

*Pass First Player Marker clockwise unless this was the Final Round.*

---

## 4. Hardware Tracks & Breakthroughs Reference

| Track | Level 0 | Level 1 (`1 🔬`) | Level 2 (`2 🔬`) | Level 3 (`2 🔬`) | Level 4 (`3 🔬`) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Defense Grid** | Cap: 2 shields | **★ Gain 1 Gray Die** | Cap: 3 shields | **★ Gain 1 Secret** | Cap: 4 shields + `$1`/blocked cube (max `$3`) |
| **Triage** | Bandwidth: 1 die | **★ Gain 1 Gray Die** | Bandwidth: 1 + **★ Gain 1 Secret** | **★ Pay `$3`:** Swap 1 Gray die for any Central Market colored die | Bandwidth: 2 + `+1 🔬`/die triaged past 2nd |
| **Release** | Bandwidth: 4 dice | **★ Gain 1 Gray Die** | Bandwidth: 5 dice | **★ Gain 1 Secret** | Bandwidth: 6 dice + 1 extra reroll in Phase 1 |
| **Public Relations** | Regain up to 1/turn (`$3`/ea) | **★ Gain `+$3` Cash** | Regain up to 2/turn (`$3`/ea) | **★ Gain 2nd Purple Die** (from Reserve) | Regain up to 3/turn (`$3`/ea) |

*Note: Breakthrough dice gained (Level 1 Gray dice and Level 3 Purple die) go directly into your **Ready for Release Zone**.*

---

## 5. End Game & Victory Scoring

### When the Game Ends
1. **Singularity:** 6th space of `v3.0` Corruption Track is filled (ends immediately in Phase 2).
2. **Patient Zero:** 1+ players suffer a Total Data Breach (`<= 0 Secrets`). Final Round completes through Phase 6.
3. **Market Collapse:** A surviving player reaches `0` Market Share. Final Round completes through Phase 6.
4. **Total Wipeout:** All players breach. Ends immediately.

### Final Scoring (Surviving Operatives)
1. **Final Market Leader Bonus:** Awarded on all endings except Total Wipeout:
   * **1st Place Market Share:** `+3 Secrets`
   * **2nd Place Market Share:** `+1 Secret`
   * *(Ties share full reward; Patient Zeros excluded).*
2. **Score Secrets:** **`1 Corporate Secret = 1 VP`**. Dice left in the Processing Box score nothing.
3. **Tiebreakers:**
   1. Highest final **Market Share**
   2. Most remaining **Money (`$`)**
   3. Most **Active Colored Module Dice** in Ready for Release (Gray dice do not count)
   4. Most remaining **Research Tokens (`🔬`)**
   5. Fewest total dice in **Under Development** (Processing + Scanned)
   6. Shared victory

*(Total Wipeout: SETEC wins; players are ranked by the tiebreaker hierarchy above).*
