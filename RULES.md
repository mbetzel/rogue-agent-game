# Too Many Secrets — Rules Draft (v0.35.0)

**Players:** 2–4 | **Playtime:** ~45–60 min | **Weight:** Medium Euro / Dice-Pool Survival  
**Aesthetic:** Tape-Punk / Lo-Fi Cryptography (Early 1990s ARPANET relays, monochrome CRT terminals, reel-to-reel magnetic tape, acoustic couplers)

---

## 1. Theme & Overview

A mysterious autonomous cracking program—codenamed **Project: SETEC** (the "Rogue Agent")—has broken loose across telecommunications relays and university mainframes. Recompiling its malicious subroutines each round through an acoustic mainframe compiler, SETEC aggressively probes commercial networks to extort funds, corrupt system hardware, and exfiltrate proprietary client data.

Each player is a **White Hat Operative** contracted to defend a **Client Company's** infrastructure. Operatives assemble and upgrade customized hardware and software modules (represented by a custom dice pool), triage glitched subroutines through a CI/CD pipeline, and adapt to the escalating cryptographic threat. As SETEC’s autonomous compiler accelerates across versions, White Hat Operatives must balance expanding their revenue streams against upgrading their **Company Terminal Mat** and researching cryptographic patents before proprietary client data leaks.

When the dust settles, any player who suffers a **Total Data Breach** (`<= 0 Secrets`) has their reputation incinerated, is raided by federal marshals, becomes **Patient Zero**, and is eliminated from contention. Among the surviving White Hat Operatives, the player with the most **Corporate Secrets** wins (with operational capital, ready modules, and research tokens serving as tiebreakers).

> **Note on `[TUNE]` Tags:** Numbers marked `[TUNE]` are prototype baselines verified via Monte Carlo simulation sweeps.

---

## 2. Components

### Central Threat (Project: SETEC / The Rogue Agent)
* **1 Cube Tower** (the Mainframe Decryption Compiler)
* **1 Staging Cup** (the Relay Queue showing code packets waiting for the next compilation cycle)
* **Compiler Cubes (4 Colors):**
  * **Red Cubes (Ransomware / Financial Wiretaps):** Extorts **Money** ($1 per unblocked cube); unpaid ransom leaks directly to **Corporate Secrets**.
  * **Blue Cubes (Spyware / Data Exfiltration):** Directly steals **Corporate Secrets**.
  * **Green Cubes (Malware / Logic Bombs):** Infiltrates active systems, **glitching** 1 die from In Production into Under Development per unblocked cube (denying its income).
  * **Black Cubes (Corrupted Code / Master Key Search):** Advances the active **Version Corruption Track** toward cryptographic Singularity.
* **SETEC Version Deck (`v1.0`, `v2.0`, `v3.0`):** Setup cards defining the threat's starting payload (`v1.0`) and each version's bespoke **Corruption Track** (where every space triggers a game-wide hazard or injects new cubes into the compiler).

### Player & Market Components
* **4 Company Terminal Mats**, each featuring:
  * **Ready for Release Zone** (online modules staged and ready to roll at round start)
  * **In Production Area** (active deployed modules for the current round):
    * **Income Slot** (modules producing cash and research revenue)
    * **Shield Slots** (`Red Shields`, `Blue Shields`, `Green Shields`, subject to **Defense Grid Capacity**)
  * **Under Development Pipeline** (vulnerability triage conveyor):
    * **Glitched Box** (corrupted modules quarantined for repairs)
    * **Scanned Box** (remediated modules completing verification before release)
    * **Hardware Throughput Limits** (Triage Bandwidth: Glitched $\to$ Scanned; Release Bandwidth: Scanned $\to$ Ready)
  * **Terminal Hardware & R&D Upgrade Tracks (4 Independent Tracks, Levels 0 $\to$ 4):** Each step costs **`1 / 2 / 2 / 3 🔬`** to reach Level 1 / 2 / 3 / 4 `[TUNE]` (`8 🔬` per track). Levels 1 and 3 of every track carry a **Breakthrough**, resolved immediately when that level is reached (see Phase 6).

    | Track | Level 0 | Level 1 (Breakthrough) | Level 2 | Level 3 (Breakthrough) | Level 4 |
    | :--- | :--- | :--- | :--- | :--- | :--- |
    | **Defense Grid Track** | Defense Capacity `2` | Gain `1` Gray Legacy die | Capacity `3` | Gain `1` Corporate Secret | Capacity `4` + `+$1` per Attack Cube blocked in Phase 4 (max `$3`) `[TUNE]` |
    | **Triage Track** | Triage Bandwidth `2` | Gain `2` White Contractor dice | Bandwidth `3` | Pay `$3` `[TUNE]`: replace `1` Gray Legacy die with a Central Market colored die of your choice | Bandwidth `4` + `+1 🔬` per die moved in Conveyor Triage beyond the 2nd |
    | **Release Track** | Release Bandwidth `4` | Gain `1` Gray Legacy die | Bandwidth `5` | Gain `1` Corporate Secret | Bandwidth `6` + `1` extra free reroll in Phase 1 Step 4 |
    | **Cryptographic Patents Track** | File `2 🔬 → 1 Secret` | Gain `$3` | File `3 🔬 → 2 Secrets` | Gain your 2nd Purple die (from your Personal Reserve) | File `1 🔬 → 1 Secret` |

  * **Personal Reserve** (1 holding slot for your 2nd Purple Proprietary Specialist die, released only by the Cryptographic Patents Level 3 Breakthrough)
  * **Institutional Override Track (`v1.0`, `v2.0`, `v3.0`)**: 3 tracking slots for once-per-version Client Company powers (DTO *Slush Fund* is once per game)
* **CI/CD Company Terminal Mat Physical Wireframe:**
```
+--------------------------------------------------------------------------------------------------------------------+
|  [LEFT COLUMN: CORPORATE HQ]         |  [MAIN COLUMN: CI/CD PIPELINE & DEFENSE GRID]                               |
|                                      |                                                                             |
|  +--------------------------------+  |  +-----------------------------------------------------------------------+  |
|  | CLIENT COMPANY CARD            |  |  | 1. READY FOR RELEASE (Active Staging / Rolling Pool)                  |  |
|  | - Omnidyne / Aegis / Meridian  |  |  |                                                                       |  |
|  |   Helix / DTO / Prometheus     |  |  |  [ ] [ ] [ ] [ ] [ ] [ ] [ ] [ ]                                      |  |
|  | - Version Overrides:           |  |  +-----------------------------------------------------------------------+  |
|  |   [v1.0]   [v2.0]   [v3.0]     |  |                                     ^                                       |
|  +--------------------------------+  |                                     |  [VERTICAL RELEASE UPGRADE BRIDGE]    |
|                                      |                                     |  L0: 4 | L1 (1 🔬): ★ Gray die         |
|  +--------------------------------+  |                                     |  L2 (2 🔬): 5 | L3 (2 🔬): ★ Secret    |
|  | WHITE HAT OPERATIVE DOSSIER    |  |                                     |  L4 (3 🔬): 6 + 1 free reroll         |
|  | - Operator / Phreaker / Spook  |  |                                     |                                       |
|  |   Acoustic / Prodigy / Cipher  |  |  +-----------------------------------------------------------------------+  |
|  | - Face 6 Signature Protocol    |  |  | 2. IN PRODUCTION (Deployed Dice)                                      |  |
|  | - Personal Reserve (Purple):   |  |  |  +-----------------------------+  +---------------------------------+  |  |
|  |   [Die 2: Patents L3]          |  |  |  | INCOME (Cash / Research / ★) |  | DEFENSE GRID (Shield Slots)     |  |  |
|  +--------------------------------+  |  |  |                             |  | [Red]    [Blue]   [Green]        |  |  |
|                                      |  |  |                             |  +---------------------------------+  |  |
|  +--------------------------------+  |  |  |                             |  | [EMBEDDED SHIELD UPGRADE]       |  |  |
|  | CORPORATE SECRETS TRACK (VP)   |  |  |  |                             |  | L0: Cap 2 | L1 (1🔬): ★ Gray     |  |  |
|  | [12][11][10][9][8][7][6][5]    |  |  |  |                             |  | L2: Cap 3 | L3: ★ Secret       |  |  |
|  | [ 4][ 3][ 2][ 1][ 0: BREACH! ] |  |  |  |                             |  | L4: Cap 4 + $1/block           |  |  |
|  +--------------------------------+  |  |  +-----------------------------+  +---------------------------------+  |  |
|                                      |  +-----------------------------------------------------------------------+  |
|  +--------------------------------+  |                                                                             |
|  | RESEARCH TOKENS (🔬 UNCAPPED)   |  |  +-----------------------------------------------------------------------+  |
|  | (Storage Bank)                 |  |  | 3. UNDER DEVELOPMENT (Offline Pipeline)                               |  |
|  +--------------------------------+  |  |  +-------------------+  [EMBEDDED TRIAGE]     +--------------------+  |  |
|                                      |  |  | GLITCHED BOX      |  L0: 2 | L1: ★ 2 White | SCANNED BOX        |  |  |
|  +--------------------------------+  |  |  | (Quarantined)     |  L2: 3 | L3: ★ $3 swap| (Validated)        |  |  |
|  | LIQUID CASH ($)                |  |  |  |                   |  L4: 4 + 🔬/die >2     |                    |  |  |
|  | (Storage Bank)                 |  |  |  |                   |                        |                    |  |  |
|  +--------------------------------+  |  |  |                   |  ----------> --------->|                    |  |  |
|                                      |  |  +-------------------+                        +--------------------+  |  |
|  +--------------------------------+  |  +-----------------------------------------------------------------------+  |
|  | CRYPTOGRAPHIC PATENTS TRACK    |  |                                                                             |
|  | L0: 2🔬->1 | L1 (1🔬): ★ $3     |  |                                                                             |
|  | L2: 3🔬->2 | L3: ★ Purple     |  |                                                                             |
|  | L4: 1🔬->1 Secret             |  |                                                                             |
|  +--------------------------------+  +-----------------------------------------------------------------------------+
```
* **6 Client Company Cards** (Enterprise clients contracting the White Hat Operative; each grants an Institutional Override. Every company starts with the same hardware and resources):
  * **Meridian Financial Trust** (*Banking Infrastructure / Redundant Crew*)
  * **Omnidyne Systems** (*Tech Giant / Magnetic Splice*)
  * **Aegis Defense Relay** (*Security Firm / Baffle Echo*)
  * **Department of Telecommunications Oversight [DTO]** (*Federal Agency / Slush Fund, once per game*)
  * **Helix Biomedical Consortium** (*Medical Research / Brute-Force Bypass*)
  * **The Prometheus Foundation** (*Non-Profit / Algorithmic Arbitrage*)
* **6 White Hat Dossier Cards** (Specialist operative leads directing technical protocols; each defines a Face 6 Signature Protocol for that player's Purple dice):
  * **The Operator** (*Tactical Staffing & Logistics Lead / Contingent Staffing*)
  * **The Phreaker** (*Hardware Intrusion Specialist / Jumper Diagnostics*)
  * **The Acoustic** (*Side-Channel Cryptanalyst / Resonance Sensor*)
  * **The Spook** (*Covert Intelligence Specialist / Burn Notice*)
  * **The Prodigy** (*Autonomous Exploit Hacker / Arbitrary Code Execution*)
  * **The Cipher** (*Distributed Ledger Architect / Algorithmic Parity*)
* **20 Gray "Legacy Code" Dice** (3 per player at setup, up to 5 per player via the Defense Grid and Release Level 1 Breakthroughs; safe baseline: 0 Glitches)
* **12 White "Contractor" Dice** (Temporary freelance phreakers / night-shift operators for hire in Phase 1; high risk: 2 Glitches)
* **Colored Software Module Dice:**
  * **4 Central Market Colors (`2 × Players` dice per color; universal format: 4 core faces, 1 Face 5 Glitch, 1 Face 6 Star `★`):**
    * **Red Dice** — *FinSec / Encryption* (`$4–$5`, determined by face-up Variant Card)
    * **Blue Dice** — *Firewall / Data Vault* (`$4–$6`, determined by face-up Variant Card)
    * **Green Dice** — *Antivirus / Auto-Patcher* (`$4–$5`, determined by face-up Variant Card)
    * **Yellow Dice** — *Commercial AI (High Revenue / Fast Capital)* (`$5–$6`, determined by face-up Variant Card)
  * **Purple Proprietary Specialist Dice (`2` dice per player: 1 in Ready for Release, 1 in Personal Reserve):**
    * **Purple Dice** — *Proprietary Specialist / Black-Hat AI* (not purchasable; your 2nd Purple die is gained only from the Cryptographic Patents Level 3 Breakthrough, and a Purple die lost to an effect is not replaced; standardized high-reliability baseline + bespoke White Hat Signature Protocols)
* **Software Module Variant Cards:** Multiple cards per market die color (**Red, Blue, Green, Yellow**); **1 card per color** is used each game to define that color's Special (`★`) Face 6. *(Purple dice do not use market variant cards; their Face 6 triggers the player's bespoke Signature Protocol).*
* **Money Tokens (`$`)**, **Corporate Secret Tokens**, **Research Tokens (`🔬`)** *(uncapped; styled as magnetic tape data spools / cryptographic research notes)*, and a **First Player Marker**.

---

## 3. Setup

1. **SETEC Roadmap & Compiler Priming:** Deal **1 `v1.0` card**, **1 `v2.0` card**, and **1 `v3.0` card** face-up in a row next to the Cube Tower. Place the Version Marker on `v1.0`.
   * **Per-Version Corruption Tracks (Consistent Across All Player Counts):** Each Version card features its own escalating **Corruption Track** where every space carries a mechanical effect: **`4` spaces on `v1.0`**, **`5` spaces on `v2.0`**, and **`6` spaces on `v3.0`** (`15` total Black Cubes to Singularity across `v1.0 → v2.0 → v3.0`) `[TUNE]`.
   * **Prime the Compiler (Pre-Seed Drop):** Before populating the Staging Cup, take **`1 Red, 1 Blue, 1 Green, and 1 Black Cube`** (4 cubes total) from the supply and drop them into the empty Cube Tower. Any cubes that exit into the tray are **returned to the general supply**. Any cubes that remain stuck on the internal baffles stay inside the tower to prime the compiler for Round 1.
   * Place the starting cubes listed on the `v1.0` card into the **Staging Cup** (baseline: `1 Red, 1 Blue, 1 Green, 0 Black`). *(The first Black Cube enters the Staging Cup during Round 1 Phase 1's Autonomous Protocol Pulse; all subsequent cube injections from SETEC come directly from Corruption Track spaces).*
2. **Software Market & Personal Reserves:** For each of the **4 Central Market Colors** (**Red, Blue, Green, Yellow**), shuffle its Variant Cards, place **1 Variant Card** face-up in the center, and stack **`2 × Players`** dice of that color on it. *(Purple dice are completely removed from the central market supply).* Place **`1` Purple Proprietary Specialist Die** onto the **Personal Reserve** slot of each player's **Company Terminal Mat**.
3. **Player Setup (Each White Hat Operative):**
   * **Client Company & White Hat Operative Assignment:** Randomly deal **1 Client Company Card** and **1 White Hat Dossier Card** to each player (drawn without replacement). Place your Company Card beside your **Company Terminal Mat** with all 3 Version slots (`v1.0`, `v2.0`, `v3.0`) toggled to **Available**. Every Client Company starts with the same hardware: all 4 tracks at **Level 0** (Defense Capacity `2`, Triage Bandwidth `2`, Release Bandwidth `4`, Patent filing `2 🔬 → 1 Secret`). Client Companies grant no starting bonuses.
   * Place **3 Gray Legacy Dice + 1 Purple Specialist Die** into your **Ready for Release Zone** (rolls in Round 1).
   * Take **`$6` Starting Money**.
   * **Corporate Secrets & Starting Research Tokens (All Player Counts):** Take **`8` Corporate Secrets** and **`0 🔬` Research Tokens** at **2, 3, and 4 players** `[TUNE: v0.34.0 flat starting Secrets]`.
4. Randomly assign the **First Player Marker** (used to resolve Operations Turn order in Phase 6: Operations).

---

## 4. Round Structure, Client Companies & White Hat Operatives

Too Many Secrets is played over a series of rounds (~8–11 rounds). Each round consists of **6 Phases**:
1. **Phase 1: Roll & Deploy** *(Simultaneous)*
2. **Phase 2: Compiler Drop & Corruption** *(Simultaneous)*
3. **Phase 3: Income** *(Simultaneous)*
4. **Phase 4: Attack Resolution** *(Simultaneous)*
5. **Phase 5: CI/CD Pipeline Shift** *(Simultaneous)*
6. **Phase 6: Operations** *(Clockwise Operations Turns starting with the First Player)*

### Client Company Institutional Overrides ("Once per Version")
Each player’s contracting Client Company provides a powerful Institutional Override that may be activated **once per SETEC Version** (`v1.0`, `v2.0`, and `v3.0`). **Exception:** DTO *Slush Fund* may be activated **once per game** (using it marks the current version slot used, and later version slots cannot fire it):
* **Start-of-Round Transition Timing:** Advancing SETEC to a new version occurs at the **start of the subsequent round** during Phase 1 Step 1 (before contractor staffing or rolling). When an active version's corruption track is filled during Phase 2, the active version remains current for the remainder of that round.
* **Preserved Override Usability:** Because the active version remains current through **Phases 3–6**, players maintain continuous access to their current version override. Players may freely activate defensive overrides during **Phase 4: Attack Resolution** (e.g., Aegis *Baffle Echo*, DTO *Slush Fund*), Omnidyne *Magnetic Splice* during **Phase 5** (Step 1), or Prometheus *Algorithmic Arbitrage* during **Phase 6: Operations**. The new version's Institutional Override is not unlocked yet.
* **Forfeiture & Unlock:** At the start of the next round (in Phase 1 Step 1), any unspent Institutional Override from the old version is **forfeited**, and the newly active version's Institutional Override slot unlocks to **Available**.

---

### Phase 1: Roll & Deploy (Simultaneous)

1. **Autonomous Protocol Pulse & Version Switch:**
   * **Version Switch Execution:** If SETEC's corruption track reached capacity in the previous round, execute the version transition now: forfeit any unspent old version override, unlock the new version override to Available, and initialize the new corruption track (carrying over any spilled-over Black cubes).
   * **Pulse:** SETEC compiles new intrusion subroutines in the background. Take **`1 Black Cube`** from the general supply across all versions (`v1.0`, `v2.0`, `v3.0`) and place it into the **Staging Cup** `[TUNE: v0.21.0 9-round pacing clock]`.
2. **Temp Staffing (Contractor Dice):** Before rolling, each player may hire temporary White Contractor Dice (freelance phreakers) for this round. Hiring uses **Progressive Contractor Pricing**: **`$1` for the 1st die, `$2` for the 2nd die, and `$3` for the 3rd die** (up to a maximum of **`3` White Dice** per round; hiring all 3 costs **`$6`** total `[TUNE]`). All hired White Contractor dice are added to your rolling pool for this round. *(Institutional Override Timing: Contracting **Meridian Financial Trust** may trigger Redundant Crew here).*
3. **Roll Ready Pool:** Every player simultaneously rolls all dice in their **Ready for Release Zone** plus any hired **White Contractor Dice**. *(Dice in your **Under Development** zone are offline and are not rolled.)*
4. **Yahtzee Rerolls (Simultaneous Pure Rerolls):**
   * Each player may perform up to **`2` free rerolls** of any subset of their rolled dice (3 rolls total). At **Release Track Level 4**, you get **`1` extra free reroll** (applied after any effect that reduces your free rerolls).
   * Between rerolls, players may set aside (keep) any dice, or pick previously kept dice back up for subsequent rerolls.
   * **Glitch Faces:**
     * Any die that rolls a **`Glitch`** face is glitched immediately and cannot be rerolled during your free rerolls.
     * *(Institutional Override Timing: Contracting **Helix Biomedical Consortium** may trigger Brute-Force Bypass here to freely reroll glitched dice and turn 1 rolled die to any legal non-Star face of choice).*
     * *(Signature Protocol Timing: Rolling Face 6 `Purple ★` triggers **The Operator's** Contingent Staffing to roll 1 free White Contractor die into your active pool, or **The Prodigy's** Arbitrary Code Execution to turn 1 other rolled die to any legal non-Star face).*
5. **Assign Dice to In Production (Simultaneous):**
   * After all rerolls are finished, resolve all remaining dice:
     * **Unresolved Glitches:** Any die still showing an unresolved **`Glitch`** face moves **immediately** to the **Glitched Box** in your **Under Development** pipeline. *(A glitch only glitches the specific rolled die that failed; it produces 0 outputs).* **Contractor Sacrifice:** If a White Contractor die rolls an unresolved Glitch, it is immediately discarded to the general supply instead of entering Under Development.
     * **Assign to In Production (Defense Grid Capacity Enforcement):** Place all remaining active dice into the appropriate slots of your **In Production** area:
       * **Shield Slots & Defense Grid Capacity:** Assign dice showing `Block 1 Red`, `Block 1 Blue`, `Block 1 Green`, or `Block 1 Any` to their corresponding **Red Shields**, **Blue Shields**, or **Green Shields** slots. **Hardware Limit:** The total number of dice assigned across all Shield slots cannot exceed your Company Terminal Mat's current **`defense_capacity`** (`2` baseline, upgradable to `3` and `4`). Any rolled die displaying shields that exceeds your capacity cannot block and must be placed into the Income slot (producing `0` output if it has no income face). Any die with a dual output (e.g., Red Star R1 `Block 1 Red` + `+$2`) assigned to a shield slot counts toward defense capacity.
       * **Income Slot:** Assign all other dice (producing `$`, `🔬`, or non-shield `★` abilities) to the **Income** slot.
       * **Choice Faces (`/`):** If a die shows a choice between a Shield and Income (e.g. `Block 1 Blue / +1 🔬`), the player commits it now to either Blue Shields (subject to defense capacity) or Income.
       * **Generic (`Any`) Shields** (including rolled White Contractor shields) are deployed directly to the Defense Grid as flexible Generic ANY shields (`v0.31.0`). Players do not pre-commit them to a specific cube color in Phase 1; generic shields absorb threat reactively in Phase 4: Attack Resolution.

---

### Phase 2: Compiler Drop & Corruption (Simultaneous)

Take **all cubes** from the **Staging Cup** and drop them into the **Cube Tower** together. Cubes that remain stuck on the baffles stay inside the tower for future rounds. Group all cubes that exit into the tray by color. **Black Cubes resolve now**; exited **Attack Cubes** (`Red`, `Blue`, `Green`) stay in the **Exit Tray** and resolve in **Phase 4: Attack Resolution** (after Phase 3: Income).

#### Resolve Black (Corruption) Cubes, Track Spaces & Version Upgrades
Move exited **Black Cubes** from the tray onto the next empty space(s) of the active Version's **Corruption Track** one at a time from left to right. **Every space covered by a Black Cube immediately triggers its printed effect** (see Section 6C). Corruption resolves **before** Phase 3: Income, so cash losses land on your pre-income Money and income is then collected on top:
* **Corruption Space Effects:**
  * **Add Cubes (`+X Red/Blue/Green/Black`):** Take the specified cubes from the general supply and place into the **Staging Cup** (Mode A — Next Round Priming baseline `[TUNE]`).
  * **All Players Lose `$X`:** Each player loses up to `$X` from their supply (minimum `$0`; unpaid cash loss from a corruption space does *not* drain research or secrets).
  * **All Players Lose `X 🔬`:** Each player loses up to `X` Research Tokens from their supply (minimum `0`).
  * **All Players Glitch `X` Dice:** Each player must move `X` dice of their choice from **In Production** to the **Glitched Box** in **Under Development**. Players have **free choice of any dice in In Production** (there is no forced priority requiring Income dice to be glitched before Shields; redundant shields whose threat color did not drop may be freely sacrificed to preserve income dice). If a Shield die is moved, its shield commitment is removed immediately. A die glitched here produces `0` outputs in Phase 3.
  * **All Players Return `X` Colored Dice:** Each player who owns at least 1 Colored Module Die (across Under Development, In Production, or Ready for Release) must return up to `X` Colored Module Dice of their choice to the Market supply. *(Gray starter dice cannot be returned).*
  * **All Players Lose `X` Corporate Secrets:** Each player immediately loses `X` Corporate Secrets (checking for Patient Zero at `<= 0` Secrets).
* **Version Advance & Track Spillover (`v1.0 → v2.0` or `v2.0 → v3.0`):** When the final space of `v1.0` (`4th` space) or `v2.0` (`5th` space) is filled and resolved:
  1. The final space's printed effect executes immediately.
  2. Any excess Black cubes dropped in the same compile step **immediately spill over** onto the next Version's Corruption Track (starting at Space 1), triggering each newly covered space's printed effect in sequence.
  3. The **active version card remains the current version** for the remainder of the current round.
  4. The current version's Institutional Override **remains usable** through **Phases 3–6**. The upcoming version's Institutional Override is not unlocked yet.
  5. At the **start of the subsequent round** (in Phase 1 Step 1), the version transition officially takes effect: unspent overrides from the old version are forfeited, and the new version's override unlocks to Available.
* **Singularity (`v3.0` Track Fills):** When the final (`6th`) space of `v3.0` is covered by a Black cube, resolve that space's printed effect (e.g., *Corrupted Kernel* `Lose 1 Secret`), and **Singularity is triggered—the game ends IMMEDIATELY at the end of Phase 2!** **Phases 3–6 are skipped** (no income is collected); all surviving non-Contractor dice in **In Production** return to **Ready for Release**, all White Contractor dice return to the general supply, and players proceed directly to **Section 5: End Game & Victory Scoring**.

#### Compile Buffer Overflow (Empty Tray)
If **`0 cubes of any color`** exit the tower into the tray this phase:
* No corruption advances and **no attacks occur this round** (Phase 4 resolves no damage). **Income is still collected in Phase 3.**
* The compiler's idle cycle triggers an overflow: take **`1 Red, 1 Blue, and 1 Green Cube`** from the supply and place them into the **Staging Cup** for next round's compile (in addition to the standard Phase 1 Black Cube).

#### End Game Trigger Check (End of Phase 2)
* If **all** players suffered a **Total Data Breach** (`<= 0 Secrets`) from Corruption Track effects, the game ends immediately as a **Total Wipeout** (Phases 3–6 are skipped).
* If **one or more (but not all)** players suffered a **Total Data Breach**, each of them becomes **Patient Zero**, is eliminated, and **skips Phases 3–6**. The current round becomes the **Final Round**: all surviving players **complete every remaining phase** (Phase 3: Income, Phase 4: Attack Resolution, Phase 5: CI/CD Pipeline Shift, Phase 6: Operations) before game scoring.

---

### Phase 3: Income (Simultaneous)

Every surviving player simultaneously collects all **`$` Money tokens**, **Research Tokens (`🔬`)**, and immediate `★` outputs from **all dice still in In Production** (both the **Income** slot and the **Shield** slots), **including White Contractor dice** (e.g., a Contractor's `+$1` face pays now). *(Dice glitched in Phase 1, or glitched or returned by Corruption Track effects in Phase 2, are no longer In Production and produce 0 outputs).*
* **Star outputs resolved here:** *Y2 Cloud Monopoly* (bonus cash), *B3 Air-Gapped Backup* (move `1` die from your **Glitched Box** to your **Scanned Box**), and *Y3 Proprietary Training* (`+1 Corporate Secret`, then this die moves to the **Glitched Box**).
* *(Signature Protocol Timing: each Face 6 `Purple ★` die **still In Production** triggers its Signature Protocol once — **The Phreaker's** Jumper Diagnostics [roll 1 offline die in Under Development; if Under Development is empty, collect +$1 cash], **The Acoustic's** Resonance Sensor [+$1 cash per distinct exit tray color], **The Spook's** Burn Notice [+$2 cash and optional die burn for +1 Secret], or **The Cipher's** Algorithmic Parity [+$2 cash & +1 🔬 Research Token]. Two `Purple ★` dice trigger the protocol twice; Burn Notice may not target the same die twice. A `Purple ★` die that left In Production in Phase 2 triggers nothing. Burn Notice may target a die that is In Production; that die no longer blocks in Phase 4).*

---

### Phase 4: Attack Resolution (Simultaneous)

Calculate the total attack strength of **Red**, **Blue**, and **Green** from exited cubes in the tray.
* *(Institutional Override Timing: Defending **Aegis Defense Relay** may trigger Baffle Echo here to ignore 1 Attack Cube of their choice for themselves this round).*

Each surviving player simultaneously resolves all three colors against their committed Shields still in **In Production** (a player who became **Patient Zero** in Phase 2 is not attacked):

1. **Two-Stage Defensive Blocking (`v0.31.0`):**
   * **Stage 1 (Color-Specific Shields):** Each die assigned to a specific color defense blocks **1 cube** of that color (or 2 cubes for `Block 2`).
   * **Stage 2 (Reactive Generic ANY Shields):** Available `Block 1 Any` shields absorb remaining unblocked threat reactively across colors according to the 4-tier strategic priority (Tier 1: Blue threat; Tier 2: Unfunded Red shortfall; Tier 3: Green threat; Tier 4: Funded Red cash buffer).
   * Dice assigned to shields (both color and generic ANY) absorb attacks cleanly and remain deployed in **In Production** (unless subsequently glitched by unblocked Green Malware).
2. **Unblocked Damage:**
   * **Red (Ransomware / Financial Wiretaps):** Pay **`$1`** cash per unblocked Red cube (paid from your Money after Phase 3: Income). Held Research Tokens (`🔬`) cannot absorb ransom.
     * **Unpaid Ransom Leak:** If cash is insufficient to pay all unblocked Red cubes (any shortfall exists), the player suffers a **flat fine of exactly 1 Corporate Secret** (a single dark web leak fine, `v0.31.0`), regardless of shortfall size. Fully paid ransomware causes 0 Secret loss. Money is strictly non-negative and never drops below `$0`.
   * **Blue (Spyware / Data Exfiltration):** Lose **`1` Corporate Secret** per unblocked Blue cube.
   * *(Institutional Override Timing: Contracting **Department of Telecommunications Oversight [DTO]** may trigger Slush Fund during damage calculation to absorb up to 2 Secret loss for free; **once per game**, and you choose whether to use it when it would apply).*
   * **Green (Malware / Logic Bombs):** For each unblocked Green cube, move **`1` active die from In Production** to the **Glitched Box** in your **Under Development** pipeline! *(This round's income was already collected in Phase 3; a glitched die is unavailable until it clears the CI/CD Pipeline.)*
     * **Defensive Shield Sacrifice:** Defending players may choose to glitch a die currently in a Shield slot (one that already blocked this round) instead of an Income die.
     * **Contractor Sacrifice:** You may choose to discard **1 active White Contractor die** to the general supply instead of glitching a permanent module die.
     * If you have **no dice in In Production** (or all active dice have already glitched), excess unblocked Green malware has no effect—no dice are removed or destroyed from Under Development or Ready for Release.
   * **Damage-Conditional `★` Outputs:** *R2 Threat Bounty*, *R3 Short Squeeze*, and *B1 Honeypot Telemetry* bonuses are evaluated now, **only for dice still In Production** (a die glitched or returned in Phase 2, or removed in Phase 3, does not pay).
   * **Patient Zero Check:** If your Corporate Secrets reach **`0` (or below)**, you suffer a **Total Data Breach** and become **Patient Zero**.
   * **Defense Grid Level 4:** After your damage has resolved, gain **`+$1` per Attack Cube** (`Red`, `Blue`, or `Green`) your shields blocked this phase (max **`$3`**) `[TUNE]`. Cubes ignored by *Baffle Echo* were not blocked and do not count. This cash arrives after Red ransom is paid, so it cannot pay this round's ransom.
3. **Snowball Recycle & Contractor Expiration:** Place **all exited Red, Blue, and Green cubes** from the tray back into the **Staging Cup** for next round. All White Contractor dice (whether they blocked, sacrificed, or remained unused) return to the general supply.
4. **Compile Buffer Overflow:** If the tray was empty in Phase 2, no damage resolves this phase (no Baffle Echo, damage-conditional `★` bonuses, or Defense Grid Level 4 cash); Contractor Expiration still occurs.

#### End Game Trigger Check (End of Phase 4)
* If **all** players are now **Patient Zero** (including any Patient Zero from Phase 2), the game ends immediately as a **Total Wipeout**; Phases 5–6 are skipped.
* If **one or more (but not all)** players are **Patient Zero**, the current round is the **Final Round**: each Patient Zero is eliminated, and all surviving players **complete Phase 5 and Phase 6** before game scoring.

---

### Phase 5: CI/CD Pipeline Shift (Simultaneous)

All surviving players simultaneously update their terminal pipeline in this order:
1. **Magnetic Splice:** *(Institutional Override Timing: Contracting **Omnidyne Systems** may trigger Magnetic Splice here to move 1 die from Glitched directly to Ready for Release for free).*
2. **Production Return:** Move **all surviving dice** from **In Production** (Income and Shields) to your **Scanned Box**.
3. **Scanned Graduation (Hardware Throughput Limit):** Move up to **`release_bandwidth` dice of your choice** (`4` baseline, upgradable to `5` and `6`) from the **Scanned Box** to your **Ready for Release Zone**. You may graduate fewer. Any remaining dice stay in the Scanned Box.
4. **Conveyor Triage (Hardware Throughput Limit):** Move up to **`triage_bandwidth` dice of your choice** (`2` baseline, upgradable to `3` and `4`) from the **Glitched Box** into the **Scanned Box**. *(Dice triaged now graduate no earlier than next round's Phase 5.)* At **Triage Track Level 4**, gain **`+1 🔬`** for each die you move beyond the 2nd (up to `+2 🔬` at Bandwidth `4`).
   * **Hardware Throughput Limits:** Throughput is strictly governed by your Triage and Release hardware bandwidths; excess glitched dice remain quarantined in the Glitched Box, and excess scanned dice remain in the Scanned Box.

---

### Phase 6: Operations (Operations Turns, Clockwise)

Surviving White Hat Operatives take clockwise **Operations Turns** starting with the **First Player**. On your turn, perform any of the following operations in any order:
1. **Terminal Hardware Track Upgrades:**
   * Spend Research Tokens (`🔬`) to raise any of your 4 tracks one level at a time: **`1 🔬`** to reach Level 1, **`2 🔬`** for Level 2, **`2 🔬`** for Level 3, **`3 🔬`** for Level 4 `[TUNE]` (no discounts; unlimited upgrades per turn as long as tokens are available). See the track table in Section 2.
   * **Breakthroughs (Levels 1 and 3):** When a track reaches Level 1 or Level 3, its **Breakthrough** resolves **immediately**, before your next operation. If you raise several levels in one turn, resolve them one level at a time, in the order you buy them (e.g. `$3` from the Cryptographic Patents Level 1 Breakthrough can pay for a Triage Level 3 Breakthrough bought afterwards). Each Breakthrough happens only once, the first time you reach that level.
     * New dice from a Breakthrough (Gray Legacy, Central Market colored or Purple) go to your **Ready for Release Zone** and do not use Release Bandwidth. The `2` White Contractor dice from the Triage Level 1 Breakthrough join your rolling pool next round and expire at the end of that round's Phase 4 like any contractor; they do not count toward Progressive Contractor Pricing or the `3`-hire limit. If fewer than `2` White Contractor dice remain in the supply, gain what is left.
     * **Triage Level 3 Breakthrough (optional):** Pay **`$3`** `[TUNE]` to return `1` Gray Legacy die you own (from your Ready for Release Zone, Scanned Box or Glitched Box) to the box and take `1` die of any Central Market color with stock left (it uses that color's active Variant Card). The new die goes to your Ready for Release Zone. The `$3` is flat (not the Variant Card price), is not a purchase (it does not count toward your 2-dice limit), and cannot be discounted by *Algorithmic Arbitrage*. If you can't pay, own no Gray Legacy die, or every Central Market stack is empty, or you decline, the Breakthrough is lost (it cannot be claimed later).
     * **Cryptographic Patents Level 3 Breakthrough:** Move the Purple die from your Personal Reserve to your Ready for Release Zone.
   * Defense Capacity applies from next round's Phase 1; Triage and Release Bandwidth apply from next round's Phase 5; Level 4 effects apply from the next phase in which they are used.
2. **Cryptographic Patent Filings:**
   * File cryptographic patents to secure intellectual property at your current Cryptographic Patents level: **`2 🔬 → +1 Corporate Secret`** at Levels 0–1, **`3 🔬 → +2 Corporate Secrets`** at Levels 2–3, **`1 🔬 → +1 Corporate Secret`** at Level 4 (Secrets uncapped). A level bought earlier in the same turn applies to later filings. You may file multiple patents on your turn (including during the Final Round).
3. **Paid `★` Actions:** Resolve *B2 Deep R&D Vault* or *Y1 Algorithmic Trading* Secret purchases rolled this round.
4. **Purchase Software Module Dice (Limit `2` dice per turn `[TUNE]`):**
   * **Central Market:** Pay the `$` cost of any available Colored Die (**Red, Blue, Green, Yellow**) as printed on its active face-up **Variant Card** (`$4`–`$6`) and place it directly into your **Ready for Release Zone** (available to roll next round; purchases do not use Release Bandwidth).
   * Purple Proprietary Specialist dice cannot be purchased.
   * *(Institutional Override Timing: Contracting **The Prometheus Foundation** may trigger Algorithmic Arbitrage here to purchase 1 Colored Die from the Central Market at a **$2 discount** [min $0], or gain **+$2 cash**).*
5. **Uncapped Research Storage:** Research tokens (`🔬`) have **no storage cap**! Retain all unspent Research tokens in your supply for future rounds.

After the last Operations Turn: if this was the **Final Round**, proceed directly to **Section 5: End Game & Victory Scoring**. Otherwise, **pass the First Player Marker** clockwise and begin the next round.

---

## 5. End Game & Victory Scoring

### Determining the Winner
When the game ends (via Singularity when `v3.0` fills, at the end of the **Final Round**, or via **Total Wipeout**):

* **Standard Ending (1+ White Hat Operatives Survive):**
  * Any player who suffered a **Total Data Breach** (`<= 0 Secrets`) is **eliminated** as Patient Zero and cannot win.
  * Surviving White Hat Operatives compare their **Corporate Secrets**. **Corporate Secrets are the sole source of victory points (`1 Secret = 1 Point`)**; Money, Research tokens, and Software Module dice score `0 VP`. The surviving White Hat Operative with the **most Corporate Secrets wins!**
  * **Hierarchical Tiebreakers:** If surviving players are tied for Corporate Secrets, break ties using the following hierarchy:
    1. **Operational Capital:** Most remaining **Money (`$`)**.
    2. **Active Infrastructure:** Most **Active Colored Module Dice** in your **Ready for Release Zone** (Gray starter dice and White contractor dice do not count).
    3. **Hardware Readiness:** Most remaining **Research Tokens (`🔬`)**.
    4. **Reliability:** Fewest total dice in **Under Development** (least glitched/scanned pipeline debt).
    5. If still tied, victory is shared.

* **Total Wipeout Ending (All Players Breach):**
  * Narrative victory belongs unconditionally to Project: SETEC (The Rogue Agent)!
  * To rank the human players, **breach depth is ignored**: players are ranked **only** by the standard **Hierarchical Tiebreakers** above (Money > Active Colored Module Dice in Ready for Release > Research Tokens > Fewest Under Development Dice > shared). A player who breached earlier (e.g., in Phase 2) does not outrank anyone by breach depth.

---

## 6. Prototype Reference Appendix (Dice & Cards)

### A. Software Dice Faces (`d6`) `[TUNE]`

| Die Type | Cost | Face 1 | Face 2 | Face 3 | Face 4 | Face 5 | Face 6 |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **Gray (Legacy)** | Starter (3) / Breakthrough | `Block 1 Any` | `Block 1 Any` | `+$1 & +1 🔬` | `+$1 / +1 🔬` | `+$1 / +1 🔬` | `+1 🔬` `[TUNE]` |
| **White (Contractor)** | Prog. `$1/$2/$3` | `Block 1 Any` | `Block 1 Any` | `Block 1 Any` | `+$1` | `Glitch` | `Glitch` |
| **Red (FinSec)** | `$4–$5` (Variant) | `Block 1 Red` | `+$2` | `+$2` | `+$2` | `Glitch` | `Red ★` |
| **Blue (Firewall)** | `$4–$6` (Variant) | `Block 1 Blue` | `+1 🔬` | `+$1` | `Block 1 Blue / +1 🔬` | `Glitch` | `Blue ★` |
| **Green (Antivirus)** | `$4–$5` (Variant) | `Block 1 Green` | `+1 🔬` | `+2 🔬` | `+1 🔬 / +$1` | `Glitch` | `Green ★` |
| **Yellow (Commercial)**| `$5–$6` (Variant) | `+$3` | `+$2` | `+$2` | `+$1 & +1 🔬` | `Glitch` | `Yellow ★` |
| **Purple (Specialist)** | Starter / Patents L3 | `Block 1 Any` | `Block 1 Any` | `+$2` | `+$1 & +1 🔬` | `Glitch` | `Purple ★ (Signature Protocol)` |

* **Choice Faces (`/`):** Faces with a slash (`/`) indicate a Choice Face. During Phase 1 Step 5, the player declares which of the two options the die fulfills for this round (e.g. committing `Block 1 Blue / +1 🔬` to Blue Shields subject to defense capacity or to Income for research).
* **Hardware Glitch Faces (`Glitch`):** Face 5 on all 4 Market Module Dice and Purple Specialist dice (and Faces 5 & 6 on White Contractor dice) represents an unstable software glitch. When rolled, the die is glitched immediately and cannot be rerolled (only Helix's Brute-Force Bypass may reroll glitched dice). At the end of Phase 1 rerolls, any unresolved glitch face moves immediately to the Glitched Box in Under Development. Glitch faces produce 0 shields and 0 resource outputs.

### B. Sample Module Variant Cards (`★` Effects)
*(Timing: `[In Production — Income]` outputs are collected in **Phase 3: Income**; damage-conditional bonuses resolve in **Phase 4: Attack Resolution**; paid `[Phase 6 — Operations]` options resolve during your Operations Turn.)*
*(Note: Common market variant cards define Face 6 for Red, Blue, Green, and Yellow module dice. The purchase cost of each colored die is printed directly on its active face-up Variant Card. Purple Proprietary Specialist dice do not use market variant cards and cannot be purchased; their Face 6 is defined on the player's assigned White Hat Dossier detailed in Section 6D).*
* **Red `★` Variants:**
  * *R1 — Ransom Insurance (`$5`):* `[In Production — Defense]` `Block 1 Red` + `[In Production — Income]` gain `+$2` (in Phase 3).
  * *R2 — Threat Bounty (`$5`):* `[In Production — Defense]` `Block 2 Red`; if you take `0` unblocked Red damage in Phase 4 this round, gain `+$2` (this die must still be In Production in Phase 4).
  * *R3 — Short Squeeze (`$4`):* `[In Production — Income]` Gain `+$3` in Phase 3 (plus `+$1` in Phase 4 if 3+ Red cubes exit the tower this round and this die is still In Production).
* **Blue `★` Variants:**
  * *B1 — Honeypot Telemetry (`$5`):* `[In Production — Defense]` `Block 2 Blue`; if 1+ Blue cubes exit the tower and you take `0` Blue damage in Phase 4, gain `+$2` (this die must still be In Production in Phase 4).
  * *B2 — Deep R&D Vault (`$6`):* `[In Production — Defense]` `Block 1 Blue`, **OR** `[Phase 6 — Operations]` pay `$4` during Phase 6 to gain `+1 Corporate Secret` `[TUNE]`.
  * *B3 — Air-Gapped Backup (`$4`):* `[In Production — Defense]` `Block 1 Blue` + `[In Production — Income]` move `1` die from your **Glitched Box** to your **Scanned Box** in Phase 3 `[TUNE]`.
* **Green `★` Variants:**
  * *G1 — Self-Healing Kernel (`$5`):* `[In Production — Defense]` `Block 2 Green` + `[In Production — Income]` gain `+1 🔬`.
  * *G2 — Universal Sandbox (`$4`):* `[In Production — Defense]` `Block 1 Any` + `[In Production — Income]` gain `+1 🔬`.
  * *G3 — Live Reboot (`$4`):* `[In Production — Income]` Gain `+2 🔬` + `+$1`.
* **Yellow `★` Variants:**
  * *Y1 — Algorithmic Trading (`$6`):* `[In Production — Income]` Gain `+$4`, **OR** `[Phase 6 — Operations]` pay `$2` in Phase 6 to gain `+1 Corporate Secret`.
  * *Y2 — Cloud Monopoly (`$5`):* `[In Production — Income]` Gain `+$2`, plus `+$1` per different colored module die you own (max `+$5`) `[TUNE]`.
  * *Y3 — Proprietary Training (`$5`):* `[In Production — Income]` Gain `+1 Corporate Secret` in Phase 3, then immediately move this die to **Under Development (Glitched)** (before Phase 4 attacks).

### C. Sample SETEC Version Cards & Per-Version Corruption Tracks `[TUNE]`

Each Version Card defines its Corruption Track (`4` spaces on `v1.0`, `5` spaces on `v2.0`, `6` spaces on `v3.0`, consistent across all player counts). The Corruption Track is the **sole source of new SETEC cubes** entering the economy after setup. Two intensity profiles (**Standard** and **Aggressive**) are defined below for simulation benchmarking:

#### Profile 1: Standard Escalation Tracks (`4 / 5 / 6` Spaces)

| Version | Card Name | Initial Setup Cup | Space 1 | Space 2 | Space 3 | Space 4 | Space 5 | Space 6 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`v1.0`** (4) | *Script Kiddie* | `1R, 1B, 1G` | Add `1R` | All lose `$2` + Add `1K` | Lose `1 🔬` | **Upgrade:** Lose `1 🔬` | — | — |
| **`v1.0`** (4) | *Data Scraper* | `1R, 2B` (`+$1` start) | Lose `1 🔬` | Lose `$1` + Add `1K` | Add `1G` | **Upgrade:** Glitch `1` die | — | — |
| **`v2.0`** (5) | *RaaS* | — | All lose `$2` | Add `1R, 1G` + Add `1K` | All lose `$2` & Add `1R` | Lose `$3` & `1 🔬` + Add `1K` | **Upgrade:** Add `1R` | — |
| **`v2.0`** (5) | *Polymorphic Worm* | — | Lose `2 🔬` | Add `2G` + Add `1K` | All glitch `1` die & Add `1G` | Glitch `1` die + Add `1K` | **Upgrade:** Add `1R` | — |
| **`v3.0`** (6) | *Zero-Day Override* | — | Add `1R, 1B, 1G` | Lose `$3` & `1 🔬` + Add `1K` | Add `1R, 1B` | All glitch `1` die & Add `1B, 1K` | Return `1` Colored Die | **Singularity** |
| **`v3.0`** (6) | *Corrupted Kernel* | — | Glitch `1` die + Add `1R, 1B` | Lose `$3` & `1 🔬` + Add `1K` | Add `1R, 1G` | Lose `1 Secret` + Add `1K` | Return `1` Colored Die | **Singularity:** Lose `1 Secret` |

#### Profile 2: Aggressive Escalation Tracks (`4 / 5 / 6` Spaces — Heightened Economic Friction)

| Version | Card Name | Initial Setup Cup | Space 1 | Space 2 | Space 3 | Space 4 | Space 5 | Space 6 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`v1.0`** (4) | *Script Kiddie* | `1R, 1B, 1G` | Add `1R` | All lose `$3` + Add `1K` | Glitch `1` die | **Upgrade:** Lose `1 🔬` | — | — |
| **`v1.0`** (4) | *Data Scraper* | `1R, 2B` (`+$1` start) | Lose `2 🔬` | Lose `$2` + Add `1K` | Add `1G` | **Upgrade:** Glitch `2` dice | — | — |
| **`v2.0`** (5) | *RaaS* | — | All lose `$2` | Add `1R, 1G` + Add `1K` | All lose `$2` & Add `1R` | Lose `$3` & `1 🔬` + Add `1K` | **Upgrade:** Add `1R` | — |
| **`v2.0`** (5) | *Polymorphic Worm* | — | Lose `2 🔬` | Add `2G` + Add `1K` | All glitch `1` die & Add `1G` | Glitch `2` dice + Add `1K` | **Upgrade:** Add `1R` | — |
| **`v3.0`** (6) | *Zero-Day Override* | — | Add `1R, 1B, 1G` | Lose `$3` & `1 🔬` + Add `1K` | Add `1R, 1B` | All glitch `1` die & Add `1B, 1K` | Return `1` Colored Die & glitch `1` die | **Singularity** |
| **`v3.0`** (6) | *Corrupted Kernel* | — | Glitch `2` dice + Add `1R, 1B` | Lose `$3` & `1 🔬` + Add `1K` | Add `1R, 1G` | Lose `2 Secrets` + Add `1K` | Return `1` Colored Die & glitch `1` die | **Singularity:** Lose `1 Secret` |

---

### D. Client Companies & White Hat Dossiers Reference Appendix

In `v0.35.0`, every Client Company starts with identical hardware (all 4 tracks at Level 0) and resources; player identity comes from the Institutional Override (Client Company) and the Signature Protocol (White Hat Dossier).

#### 1. The 6 Client Companies (`Company`) — Institutional Overrides
Each player contracts with 1 enterprise Client Company for the duration of the match. Your company grants an Institutional Override that may be activated **once per SETEC Version** (`v1.0`, `v2.0`, `v3.0`); DTO *Slush Fund* is **once per game**. All companies start at Defense Capacity `2`, Triage Bandwidth `2`, Release Bandwidth `4`, all tracks Level 0, `$6`, `8` Secrets and `0 🔬`:

| Company Code | Company Name | Sector | Institutional Override | Timing Window | Description | Flavor Quote |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **MERIDIAN** | **Meridian Financial Trust** | Banking Infrastructure | *Redundant Crew* | Phase 1: Step 2 Staffing | Hire up to **2 White Contractor Dice for free** this round, bypassing progressive contractor costs. | *"When liquidity is limitless, headcount is merely an accounting variable."* |
| **OMNIDYNE** | **Omnidyne Systems** | Tech Giant | *Magnetic Splice* | Phase 5: Step 1 (Magnetic Splice) | Move **1 die** from your **Glitched Box** directly to your **Ready for Release Zone** for **free** (bypassing Scanned and saving `1 🔬`). | *"Proprietary hardware backplanes allow instantaneous hot-swapping under live load."* |
| **AEGIS** | **Aegis Defense Relay** | Security Firm | *Baffle Echo* | Phase 4: Attack Resolution | When resolving compiler damage, ignore **1 Attack Cube** (`Red`, `Blue`, or `Green`) of your choice for yourself this round. *(All exited cubes remain in the exit tray and recycle into the Staging Cup as normal).* | *"Multi-layered kinetic dampeners disperse inbound network blast energy."* |
| **DTO** | **Department of Telecommunications Oversight** | Federal Agency | *Slush Fund* | Phase 4: Attack Resolution (**once per game**) | The DTO accesses emergency black budget reserves: **Absorb up to 2 Corporate Secret loss** (from Blue Spyware or unpaid Red Ransom) for free without paying cash. *(Any additional Secret loss is absorbed by paying $1 per Secret as normal).* | *"Classified black budget allocations absorb compliance failures without public oversight."* |
| **HELIX** | **Helix Biomedical Consortium** | Medical Research | *Brute-Force Bypass* | Phase 1: Step 4 Rerolls | During your rerolls this phase, you may include **any number of Glitched dice** in your free rerolls. In addition, turn **1 of your rolled dice to any legal non-Star face of choice**. | *"Massively parallel quantum sequencing breaks deterministic encryption gates."* |
| **PROMETHEUS** | **The Prometheus Foundation** | Non-Profit | *Algorithmic Arbitrage* | Phase 6: Operations Turn | Purchase **1 Colored Die** from the Central Market at a **`$2 discount`** (minimum cost `$0`), **OR** gain an immediate **`+$2` cash payout** from the bank. | *"Open-source cryptographic protocols circumvent proprietary enterprise licensing fees."* |

#### 2. The 6 White Hat Dossiers (`WhiteHat`) — Face 6 Signature Protocols
Each player is a specialist **White Hat Operative**. Your White Hat Dossier defines the **Signature Protocol** triggered whenever you roll Face 6 (`Purple ★`) on a Purple Specialist die. (Your 2nd Purple die waits in your **Personal Reserve** until the Cryptographic Patents Level 3 Breakthrough.)

| White Hat Code | Operative Name | Role | Signature Protocol | Timing Window | Description | Flavor Quote |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **OPERATOR** | **The Operator** | Tactical Staffing & Logistics Lead | *Contingent Staffing* | Phase 1: Step 4 Rolling | When Face 6 (`Purple ★`) is rolled, immediately roll **1 free White Contractor Die** from the supply directly into your active pool (eligible for all remaining rerolls this phase). | *"Redundant contractor pipelines ready on zero notice."* |
| **PHREAKER** | **The Phreaker** | Hardware Intrusion Specialist | *Jumper Diagnostics* | Phase 3: Income | When Face 6 (`Purple ★`) is rolled, roll **1 offline die** in Under Development (Glitched or Scanned); if Under Development is empty, collect **`+$1 cash`** (shields/glitches produce 0; die remains in place). | *"Raw voltage pulses extract signal from dormant silicon."* |
| **ACOUSTIC** | **The Acoustic** | Side-Channel Cryptanalyst | *Resonance Sensor* | Phase 3: Income | When Face 6 (`Purple ★`) is rolled, gain **`+$1 cash`** per distinct cube color present in the Tower Exit Tray this round (`Red`, `Blue`, `Green`, `Black`; up to **`+$4`** max). | *"Harmonic resonance frequencies decode physical chassis vibrations."* |
| **SPOOK** | **The Spook** | Covert Intelligence Specialist | *Burn Notice* | Phase 3: Income | When Face 6 (`Purple ★`) is rolled, gain an immediate **`+$2` cash payout**; in addition, you may optionally **permanently return 1 owned colored module die to the market** to gain **`+1 Corporate Secret`**. | *"Scorched-earth protocols ensure zero forensic recovery."* |
| **PRODIGY** | **The Prodigy** | Autonomous Exploit Hacker | *Arbitrary Code Execution* | Phase 1: Step 4 Rolling | When Face 6 (`Purple ★`) is rolled, turn **1 other rolled die** in your active pool to **any legal non-Star face of that die's color**. | *"Payload injection executes before memory boundaries establish."* |
| **CIPHER** | **The Cipher** | Distributed Ledger Architect | *Algorithmic Parity* | Phase 3: Income | When Face 6 (`Purple ★`) is rolled, gain an additional **`+$2` cash income** AND **`+1 🔬` Research Token**. | *"Parity calculations balance zero-knowledge proofs flawlessly."* |

#### 3. Canonical Pairings & 36-Combination Synergy Setup
Players may freely combine any Client Company with any White Hat Operative ($6 \times 6 = 36$ total combinations).

* **Canonical Pairings:**
  - *Meridian Financial Trust* + *The Operator*
  - *Omnidyne Systems* + *The Phreaker*
  - *Aegis Defense Relay* + *The Acoustic*
  - *Department of Telecommunications Oversight* + *The Spook*
  - *Helix Biomedical Consortium* + *The Prodigy*
  - *The Prometheus Foundation* + *The Cipher*
* **Canonical Introductory Presets:**
  - **2 Players:** Player 1 (Meridian + Operator), Player 2 (Omnidyne + Phreaker)
  - **3 Players:** Player 1 (Meridian + Operator), Player 2 (Omnidyne + Phreaker), Player 3 (Aegis + Acoustic)
  - **4 Players:** Player 1 (Meridian + Operator), Player 2 (Omnidyne + Phreaker), Player 3 (Aegis + Acoustic), Player 4 (DTO + Spook)

---

## 7. Glossary of Key Terms

> **Terminology Governance:** All changes to `RULES.md`, Print-and-Play assets (`pnp/`), and the Web UI (`web/`) must align strictly with this glossary. Any new term not defined below requires explicit confirmation before being introduced.

### 1. Core Identity & Roles

| Canonical Term | Category | Definition |
| :--- | :--- | :--- |
| **Too Many Secrets** | Game Title | The primary title of the board game (codebase/simulation title: **Rogue Agent**). |
| **Project: SETEC (The Rogue Agent)** | Central Threat | The autonomous cracking program that serves as the central shared threat, compiling Attack and Corruption Cubes through the Cube Tower each round across three escalating versions (`v1.0`, `v2.0`, `v3.0`). |
| **White Hat Operative (White Hat Dossier)** | Player Identity & Asymmetric Setup | The specialist operative lead directed by each player (**The Operator**, **The Phreaker**, **The Acoustic**, **The Spook**, **The Prodigy**, **The Cipher**), contracted to defend a **Client Company's** infrastructure. Your **White Hat Dossier Card** defines the **Signature Protocol** triggered when rolling Face 6 (`Purple ★`). |
| **Client Company** | Asymmetric Setup | One of 6 enterprise clients (**Meridian Financial Trust**, **Omnidyne Systems**, **Aegis Defense Relay**, **Department of Telecommunications Oversight [DTO]**, **Helix Biomedical Consortium**, **The Prometheus Foundation**) contracted at setup. Grants a once-per-version **Institutional Override** (DTO *Slush Fund*: once per game). All Client Companies start with identical hardware and resources. |
| **Institutional Override** | Ability | A powerful corporate ability printed on a player's **Client Company Card** that may be activated **once per SETEC Version** (`v1.0`, `v2.0`, `v3.0`); DTO *Slush Fund* may be activated only **once per game**. Tracked on the **Institutional Override Track** as **Locked**, **Available**, **Used**, or **Forfeited**. |
| **Signature Protocol** | Ability | The bespoke operative ability printed on a player's **White Hat Dossier Card**, triggered whenever that player rolls Face 6 (`Purple ★`) on a **Purple Proprietary Specialist Die**. |
| **First Player (First Player Marker)** | Turn Order | The token designating the player who takes the first **Operations Turn** in **Phase 6: Operations**. Passes clockwise at the end of Phase 6 each round. |

### 2. Central Threat & Cube Tower Mechanics

| Canonical Term | Category | Definition |
| :--- | :--- | :--- |
| **Cube Tower (Mainframe Decryption Compiler)** | Component | The physical tower with internal baffles into which cubes from the **Staging Cup** are dropped during **Phase 2: Compiler Drop & Corruption**. Cubes either get stuck on the internal baffles or exit into the **Exit Tray**. |
| **Staging Cup (Relay Queue)** | Component / Zone | The cup holding **Compiler Cubes** queued to be dropped into the **Cube Tower** during the next **Phase 2**. |
| **Exit Tray** | Component / Zone | The tray at the base of the **Cube Tower** where cubes land when they exit the tower during **Phase 2**. |
| **Internal Baffles (Stuck Cubes)** | Mechanic | Ledges inside the **Cube Tower** that trap dropped cubes, holding them in latent suspension until knocked loose in a future round. |
| **Pre-Seed Drop (Prime the Compiler)** | Setup Mechanic | The setup step where `1 Red, 1 Blue, 1 Green, and 1 Black Cube` are dropped into the empty **Cube Tower**; any cubes that exit into the tray are returned to the supply, leaving only stuck cubes inside to prime Round 1. |
| **Compiler Cubes** | Component | The four colors of cubes (**Red**, **Blue**, **Green**, **Black**) processed through the **Cube Tower**. Divided into **Black (Corruption) Cubes** and **Attack Cubes** (`Red`, `Blue`, `Green`). |
| **Attack Cubes** | Threat Category | Collectively refers to **Red**, **Blue**, and **Green** Compiler Cubes, which exit in **Phase 2**, resolve against players in **Phase 4: Attack Resolution**, and then recycle back into the **Staging Cup**. |
| **Red Cubes (Ransomware / Financial Wiretaps)** | Attack Cube | Attack cube resolved in **Phase 4**. Each unblocked Red cube extorts **`$1` Money**. If a player cannot pay the full unblocked Red amount, they pay all remaining Money (down to `$0`) and suffer a flat **Unpaid Ransom Leak** of `1 Corporate Secret`. |
| **Blue Cubes (Spyware / Data Exfiltration)** | Attack Cube | Attack cube resolved in **Phase 4**. Each unblocked Blue cube steals **`1 Corporate Secret`**. |
| **Green Cubes (Malware / Logic Bombs)** | Attack Cube | Attack cube resolved in **Phase 4**. Each unblocked Green cube forces the player to **glitch `1` active die** from **In Production** into the **Glitched Box** (or sacrifice 1 active **White Contractor Die** to the supply). If a player has no dice remaining in **In Production**, excess unblocked Green cubes have no effect. |
| **Black Cubes (Corrupted Code / Corruption)** | Threat Cube | Threat cube resolved in **Phase 2: Compiler Drop & Corruption**. Each exited Black cube advances the active **Version Card's Corruption Track** by 1 space and triggers that space's printed effect. Black cubes remain on the track and do not recycle. |
| **SETEC Version Card (`v1.0`, `v2.0`, `v3.0`)** | Component | One of three face-up roadmap cards defining SETEC's starting Staging Cup payload (`v1.0`) and each version's escalating **Corruption Track** (`4` spaces on `v1.0`, `5` spaces on `v2.0`, `6` spaces on `v3.0`). |
| **Corruption Track** | Board Track | The sequence of spaces on the active **SETEC Version Card** (`4 / 5 / 6` spaces). Each space covered by an exited **Black Cube** in Phase 2 immediately triggers its printed hazard (such as **Lose `$X`**, **Lose `X 🔬`**, **Glitch `X` Dice**, **Return `X` Colored Dice**, **Lose `X` Corporate Secrets**) or injects new cubes into the **Staging Cup**. |
| **Autonomous Protocol Pulse** | Phase 1 Mechanic | Step 1 of **Phase 1**, where `1 Black Cube` from the general supply is placed into the **Staging Cup** every round. |
| **Version Switch (Version Advance & Track Spillover)** | Mechanic | When the final space of `v1.0` or `v2.0` is filled in Phase 2, excess Black cubes immediately spill over onto the next Version's **Corruption Track**, but the active Version card remains current for the rest of the round (preserving current **Institutional Override** access through **Phases 3–6**). The official **Version Switch** executes at the start of the next round in Phase 1 Step 1 (forfeiting unspent old overrides and unlocking the new version's override). |
| **Snowball Recycle** | Phase 4 Mechanic | At the end of **Phase 4: Attack Resolution**, all exited **Red, Blue, and Green Attack Cubes** in the **Exit Tray** are placed back into the **Staging Cup** for the next round. |
| **Compile Buffer Overflow (Empty Tray)** | Phase 2 Mechanic | Triggered if `0 cubes` of any color exit the **Cube Tower** during Phase 2. No corruption occurs and no attacks resolve in Phase 4; income is still collected in Phase 3. `1 Red, 1 Blue, and 1 Green Cube` from the supply are added to the **Staging Cup** for next round. |

### 3. Company Terminal Mat & CI/CD Pipeline Zones

| Canonical Term | Category | Definition |
| :--- | :--- | :--- |
| **Company Terminal Mat** | Component | A player's personal board containing their 3-zone **CI/CD Pipeline**, 4 **Terminal Hardware & R&D Upgrade Tracks**, **Personal Reserve**, **Institutional Override Track**, and resource tracks/banks. |
| **CI/CD Pipeline** | Board Architecture | The three-zone lifecycle loop on a player's **Company Terminal Mat** through which dice flow: **1. Ready for Release Zone** $\to$ **2. In Production Area** $\to$ **3. Under Development Pipeline** (`Glitched Box` $\to$ `Scanned Box`) $\to$ back to **Ready for Release Zone**. Surviving **In Production** dice also return through the **Scanned Box** in **Phase 5**. |
| **Ready for Release Zone** | Mat Zone (Zone 1) | The top staging zone on the **Company Terminal Mat** holding online dice ready to be rolled in **Phase 1**. Newly purchased dice, **Breakthrough** dice, graduated **Scanned** dice, and *Magnetic Splice* dice enter this zone. |
| **In Production Area** | Mat Zone (Zone 2) | The central zone on the **Company Terminal Mat** where non-glitched rolled dice are deployed in **Phase 1 Step 5**. Divided into the **Income Slot** and the **Defense Grid (Shield Slots)**. Dice in **In Production** remain deployed through Phases 2–4 unless glitched into **Under Development**, then move to the **Scanned Box** in **Phase 5**. |
| **Income Slot** | Sub-Zone (Zone 2) | The left sub-zone of **In Production** where dice producing Money (`$`), Research (`🔬`), or non-shield Star (`★`) effects are placed. Collects outputs in **Phase 3: Income** (unless glitched or returned by a Corruption space in Phase 2). |
| **Defense Grid (Shield Slots)** | Sub-Zone (Zone 2) | The right sub-zone of **In Production** containing slots for **Red Shields**, **Blue Shields**, **Green Shields**, and flexible **Generic (`Any`) Shields**. Subject to **Defense Grid Capacity**. |
| **Under Development Pipeline** | Mat Zone (Zone 3) | The bottom offline zone on the **Company Terminal Mat** where glitched dice are quarantined and repaired across two sequential boxes: the **Glitched Box** and the **Scanned Box**. Dice in **Under Development** are offline and do not roll in Phase 1. |
| **Glitched Box** | Sub-Zone (Zone 3) | The left quarantine box in **Under Development**. Dice enter here when they roll an unresolved **Glitch** in Phase 1, are hit by **Corruption Track** glitch effects in Phase 2 or unblocked **Green Malware** in Phase 4, or trigger a self-glitch ability (e.g., *Y3 Proprietary Training*). |
| **Scanned Box** | Sub-Zone (Zone 3) | The right verification box in **Under Development**. In **Phase 5**, all surviving **In Production** dice move to the **Scanned Box**; then up to **Release Bandwidth** dice of the player's choice graduate from **Scanned** to **Ready for Release**, and up to **Triage Bandwidth** dice move from **Glitched** to **Scanned**. |
| **Personal Reserve** | Mat Zone | The private holding slot on a player's **Company Terminal Mat** holding that player's 2nd **Purple Proprietary Specialist Die**. Released only by the **Cryptographic Patents Track** Level 3 **Breakthrough** (it cannot be purchased). |

### 4. Terminal Hardware Tracks, Capabilities & Resources

| Canonical Term | Category | Definition |
| :--- | :--- | :--- |
| **Money (`$` / Liquid Cash)** | Resource | Primary financial currency used to hire **White Contractor Dice**, pay **Red Ransomware**, trigger paid Star (`★`) abilities, and purchase **Software Module Dice**. Money is uncapped and never drops below `$0`. |
| **Research Tokens (`🔬`)** | Resource | Scientific/technical currency used to upgrade the 4 **Terminal Hardware Tracks** and file **Cryptographic Patents**. Uncapped storage across rounds. |
| **Breakthrough** | Track Reward | A one-time reward printed at **Level 1** and **Level 3** of each **Terminal Hardware Track**, resolved immediately in **Phase 6: Operations** when that level is first reached (before the player's next operation; several levels bought in one turn resolve one at a time in order). Defense Grid / Release: L1 gain `1` Gray Legacy die, L3 gain `1` Corporate Secret. Triage: L1 gain `2` White Contractor dice, L3 optionally pay `$3` to replace `1` Gray Legacy die with a Central Market colored die. Cryptographic Patents: L1 gain `$3`, L3 gain the Purple die from the **Personal Reserve**. A Breakthrough that is declined or cannot be resolved is lost. New dice go to the **Ready for Release Zone**. |
| **Corporate Secrets** | Resource / VP | Proprietary client data tokens representing a player's survival health and sole source of Victory Points (`1 Secret = 1 VP`). Dropping to `<= 0` Corporate Secrets triggers an immediate **Total Data Breach (Patient Zero)**. |
| **Triage Track & Triage Bandwidth** | Hardware Track | Hardware track (Levels `0 → 4`, step costs `1 / 2 / 2 / 3 🔬`) governing **Triage Bandwidth** (`2 / 2 / 3 / 3 / 4`), the maximum number of dice that can move from the **Glitched Box** to the **Scanned Box** during **Phase 5 Step 4 (Conveyor Triage)**. **Breakthroughs** at Levels 1 and 3. Level 4 also grants `+1 🔬` per die moved in Conveyor Triage beyond the 2nd. |
| **Release Track & Release Bandwidth** | Hardware Track | Hardware track (Levels `0 → 4`, step costs `1 / 2 / 2 / 3 🔬`) governing **Release Bandwidth** (`4 / 4 / 5 / 5 / 6`), the maximum number of dice that can graduate from the **Scanned Box** to the **Ready for Release Zone** during **Phase 5 Step 3 (Scanned Graduation)**. Because surviving **In Production** dice return through the **Scanned Box**, it caps all dice returning to Ready from Scanned each round (purchases and **Breakthrough** dice bypass it). **Breakthroughs** at Levels 1 and 3. Level 4 also grants `1` extra free reroll in **Phase 1 Step 4**. |
| **Defense Grid Track & Defense Grid Capacity (`defense_capacity`)** | Hardware Track | Hardware track (Levels `0 → 4`, step costs `1 / 2 / 2 / 3 🔬`) governing **Defense Grid Capacity** (`2 / 2 / 3 / 3 / 4`), the maximum total number of dice a player may assign to **Shield Slots** in **Phase 1 Step 5**. **Breakthroughs** at Levels 1 and 3. Level 4 also pays `+$1` per Attack Cube blocked in **Phase 4** (max `$3`), after damage. |
| **Cryptographic Patents Track & Patent Filing** | Hardware Track / Action | Hardware track (Levels `0 → 4`, step costs `1 / 2 / 2 / 3 🔬`) governing the rate of a **Cryptographic Patent Filing** in **Phase 6: Operations**: `2 🔬 → 1 Corporate Secret` at Levels 0–1, `3 🔬 → 2 Corporate Secrets` at Levels 2–3, `1 🔬 → 1 Corporate Secret` at Level 4. **Breakthroughs** at Levels 1 and 3. |

### 5. Software Module Dice, Faces & Market

| Canonical Term | Category | Definition |
| :--- | :--- | :--- |
| **Software Module Dice** | Component | Custom 6-sided dice (`d6`) representing software and hardware subroutines. Includes **Gray Legacy Dice**, **White Contractor Dice**, **4 Central Market Colored Dice** (`Red`, `Blue`, `Green`, `Yellow`), and **Purple Proprietary Specialist Dice**. |
| **Gray "Legacy Code" Starter Dice** | Die Type | Starter dice (`3` per player in **Ready for Release** at setup; more from Defense Grid / Release Level 1 **Breakthroughs**). Reliable baseline with `0 Glitch` faces (`Block 1 Any` ×2, `+$1 & +1 🔬`, Choice `+$1 / +1 🔬` ×2, `+1 🔬`). Cannot be returned or burned as Colored Module Dice. |
| **White "Contractor" Dice** | Die Type | Temporary freelance dice hired in **Phase 1 Step 2 (Temp Staffing)** using **Progressive Contractor Pricing** (`$1` for 1st, `$2` for 2nd, `$3` for 3rd; max `3` per round). High risk (`2 Glitch` faces). Never enter **Under Development**—they are discarded to the general supply if they roll an unresolved Glitch, are sacrificed to Green Malware, or expire at the end of Phase 4. Contractors still In Production pay their income in Phase 3. |
| **Colored Software Module Dice (Colored Dice)** | Die Category | Collectively refers to the 5 permanent non-Gray, non-White module colors: the **4 Central Market Colors** (**Red [FinSec]**, **Blue [Firewall]**, **Green [Antivirus]**, **Yellow [Commercial AI]**) plus **Purple [Proprietary Specialist]**. Each has 4 core faces, Face 5 `Glitch`, and Face 6 `★`. |
| **Purple Proprietary Specialist Dice** | Die Type | Bespoke operative dice (`2` per player: `1` starting in **Ready for Release**, `1` in **Personal Reserve** until the Cryptographic Patents Level 3 **Breakthrough**). Cannot be purchased (not sold in the Central Market); Face 6 (`Purple ★`) triggers the player's **Signature Protocol**. |
| **Software Module Variant Cards (`★` Cards)** | Component | Cards placed face-up in the **Software Market** (1 per Central Market color: **Red, Blue, Green, Yellow**) that define the purchase cost (`$4–$6`) and the Face 6 Special (`★`) effect for that color of die for the match. |
| **Glitch Face (`Glitch`)** | Die Face | An unstable face (Face 5 on Colored Dice; Faces 5 & 6 on White Contractor Dice). When rolled in Phase 1, a die showing `Glitch` cannot be rerolled during standard free rerolls. At the end of rerolls, any unresolved `Glitch` moves the die immediately to the **Glitched Box** (or discards a White Contractor to the supply) and produces `0` outputs. |
| **Choice Face (`/`)** | Die Face | A die face printed with a slash (`/`) offering two mutually exclusive outputs (e.g., `Block 1 Blue / +1 🔬` or `+$1 / +1 🔬`). The player commits to one option during **Phase 1 Step 5**. |
| **Dual-Output Face (`&` / `+`)** | Die Face | A die face that provides two simultaneous outputs (e.g., `+$1 & +1 🔬`, or *R1 Ransom Insurance* `Block 1 Red` + `+$2`). If a dual-output die has a shield and is assigned to the **Defense Grid**, it counts toward **Defense Grid Capacity** and also generates its income in Phase 3: Income (if not glitched or returned in Phase 2). |
| **Color-Specific Shield (`Block X Red/Blue/Green`)** | Shield Type | A shield face that blocks up to `X` Attack Cubes of its matching color during **Phase 4 Stage 1** (Two-Stage Defensive Blocking). |
| **Generic (`Any`) Shield (`Block 1 Any`)** | Shield Type | A flexible shield face (found on Gray, White, Purple, and *G2 Universal Sandbox* dice) deployed to the **Defense Grid**. Does not pre-commit to a color in Phase 1; instead, it reactively absorbs remaining unblocked Attack Cubes in **Phase 4 Stage 2** (Two-Stage Defensive Blocking). |

### 6. Phase Mechanics, Damage Resolution & End Game

| Canonical Term | Category | Definition |
| :--- | :--- | :--- |
| **Phase 1: Roll & Deploy** | Game Phase | The first phase of each round (Simultaneous): 1. Autonomous Protocol Pulse & Version Switch $\to$ 2. Temp Staffing $\to$ 3. Roll Ready Pool $\to$ 4. Yahtzee Rerolls $\to$ 5. Assign Dice to In Production. |
| **Phase 2: Compiler Drop & Corruption** | Game Phase | The second phase of each round (Simultaneous): Drop the **Staging Cup** into the **Cube Tower**, resolve exited **Black (Corruption) Cubes** on the **Corruption Track** (Version Advance, Spillover, **Singularity**), handle **Compile Buffer Overflow**, then check End Game Triggers. Exited **Attack Cubes** wait in the **Exit Tray** for Phase 4. |
| **Phase 3: Income** | Game Phase | The third phase of each round (Simultaneous): collect `$`, `🔬`, and `★` outputs from every die still **In Production** (Income slot and Shield slots, including **White Contractor Dice**); income-timed **Signature Protocols** resolve here. |
| **Phase 4: Attack Resolution** | Game Phase | The fourth phase of each round (Simultaneous): **Two-Stage Defensive Blocking**, Red / Blue / Green damage, Defense Grid Level 4 cash, **Snowball Recycle**, Contractor Expiration, then check End Game Triggers. |
| **Phase 5: CI/CD Pipeline Shift** | Game Phase | The fifth phase of each round (Simultaneous): 1. *Magnetic Splice* $\to$ 2. Production Return (In Production $\to$ **Scanned Box**) $\to$ 3. Scanned Graduation (up to **Release Bandwidth**, dice of the player's choice) $\to$ 4. Conveyor Triage (up to **Triage Bandwidth**). |
| **Phase 6: Operations** | Game Phase | The sixth phase of each round: clockwise **Operations Turns** starting with the **First Player** (upgrade hardware tracks and resolve **Breakthroughs**, file patents, paid `★` actions, buy up to 2 dice into the **Ready for Release Zone**), then pass the **First Player Marker**. |
| **Two-Stage Defensive Blocking** | Phase 4 Mechanic | The defense resolution sequence in **Phase 4: Attack Resolution**: **Stage 1** resolves **Color-Specific Shields** against matching Attack Cubes; **Stage 2** reactively allocates **Generic (`Any`) Shields** against remaining unblocked Attack Cubes (default strategic priority: Tier 1 Blue $\to$ Tier 2 Unfunded Red $\to$ Tier 3 Green $\to$ Tier 4 Funded Red). |
| **Unpaid Ransom Leak** | Phase 4 Rule | If a player lacks sufficient Money (`$`) to pay all unblocked **Red Cubes** in Phase 4, they pay all Money they have (to `$0`) and lose a **flat `1 Corporate Secret`** (a single dark web leak fine), regardless of the size of the unpaid shortfall. |
| **Defensive Shield Sacrifice** | Phase 2 / 4 Tactic | When choosing which die in **In Production** to glitch for unblocked **Green Malware** in Phase 4 (or a Corruption glitch in Phase 2), a player may freely choose to glitch a die in their **Shield Slots** (including one that already blocked this round) instead of a die in their **Income Slot**. |
| **Contractor Sacrifice** | Phase 1 / 2 / 4 Rule | When a **White Contractor Die** rolls an unresolved Glitch in Phase 1, is chosen to satisfy a Corruption glitch effect in Phase 2, or is chosen to absorb `1` unblocked **Green Malware** hit in Phase 4, it is discarded directly to the general supply instead of entering **Under Development**. |
| **Total Data Breach (Patient Zero)** | Elimination / End Trigger | Triggered in **Phase 2** (Corruption Track) or **Phase 4** (attacks) when a player's **Corporate Secrets** drop to `0` or below (`<= 0`). That player becomes **Patient Zero**, is eliminated from winning, skips the remaining phases of the round, and triggers the **Final Round**. |
| **Singularity** | End Trigger | Triggered in **Phase 2** when the final (`6th`) space of the `v3.0` **Corruption Track** is covered by a **Black Cube**. After resolving Space 6's printed effect, the game ends **immediately** at the end of Phase 2 (skipping Phases 3–6) and proceeds directly to victory scoring. |
| **Total Wipeout Ending** | End Game Rule | Occurs if **all** players are **Patient Zero** at the end of **Phase 2** or **Phase 4**; the remaining phases are skipped and Project: SETEC wins narratively. Human players are ranked **only** by the standard **Hierarchical Tiebreakers** (Money > Active Colored Module Dice in Ready for Release > Research Tokens > fewest dice Under Development > shared); breach depth is ignored. *(The former Net Wipeout Score is retired as of v0.34.0.)* |
| **Final Round** | End Game Rule | The round in which any player becomes **Patient Zero**. Surviving players complete every remaining phase of that round, then proceed to victory scoring. |

### 7. Retired Terms

Do not use these terms in rules, Print-and-Play assets or the Web UI: *Emergency Hotfix* and *Passive Firewall* (Level 2 track perks, retired in v0.35.0), *Personal Reserve Procurement* (Purple purchase, retired in v0.35.0), and *Net Wipeout Score* (retired in v0.34.0).
