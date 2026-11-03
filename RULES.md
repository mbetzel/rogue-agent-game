# Too Many Secrets — Rules Draft (v0.26.0)

**Players:** 2–4 | **Playtime:** ~45–60 min | **Weight:** Medium Euro / Dice-Pool Survival  
**Aesthetic:** Tape-Punk / Lo-Fi Cryptography (Early 1990s ARPANET relays, monochrome CRT terminals, reel-to-reel magnetic tape, acoustic couplers)

---

## 1. Theme & Overview

A mysterious autonomous cracking program—codenamed **Project: SETEC** (the "Rogue Agent")—has broken loose across telecommunications relays and university mainframes. Recompiling its malicious subroutines each round through an acoustic mainframe compiler, SETEC aggressively probes commercial networks to extort funds, corrupt system hardware, and exfiltrate proprietary client data.

Each player directs an **independent boutique white-hat security consultancy** hired to defend client infrastructure. Consultancies assemble and upgrade customized hardware and software modules (represented by a custom dice pool), triage glitched subroutines through a CI/CD pipeline, and adapt to the escalating cryptographic threat. As SETEC’s autonomous compiler accelerates across versions, consultancies must balance expanding their revenue streams against patching critical relays before proprietary client data leaks.

When the dust settles, any consultancy that suffers a **Total Data Breach** (`<= 0 Secrets`) has its reputation incinerated, is raided by federal marshals, becomes **Patient Zero**, and is eliminated from contention. Among the surviving firms, the consultancy with the most **Corporate Secrets** wins (with operational capital, ready modules, and patches serving as tiebreakers).

> **Note on `[TUNE]` Tags:** Numbers marked `[TUNE]` are prototype baselines verified via Monte Carlo simulation sweeps.

---

## 2. Components

### Central Threat (Project: SETEC / The Rogue Agent)
* **1 Cube Tower** (the Mainframe Decryption Compiler)
* **1 Staging Cup** (the Relay Queue showing code packets waiting for the next compilation cycle)
* **Compiler Cubes (4 Colors):**
  * **Red Cubes (Ransomware / Financial Wiretaps):** Extorts firm **Money** ($1 per unblocked cube); strictly cash-only ransom (unpaid ransom leaks directly to **Corporate Secrets**).
  * **Blue Cubes (Spyware / Data Exfiltration):** Directly steals **Corporate Secrets**.
  * **Green Cubes (Malware / Logic Bombs):** Infiltrates active systems, **glitching** 1 die from In Production into Under Development per unblocked cube (denying its income, or destroying dice if overwhelmed).
  * **Black Cubes (Corrupted Code / Master Key Search):** Advances the active **Version Corruption Track** toward cryptographic Singularity.
* **SETEC Version Deck (`v1.0`, `v2.0`, `v3.0`):** Setup cards defining the threat's starting payload (`v1.0`) and each version's bespoke **Corruption Track** (where every space triggers a game-wide hazard or injects new cubes into the compiler).

### Player & Market Components
* **4 Consultancy Terminal Mats**, each featuring:
  * **Ready for Release Zone** (online modules staged and ready to roll at round start)
  * **In Production Area** (active deployed modules for the current round):
    * **Income Slot** (modules producing cash and patch revenue)
    * **Shield Slots** (`Red Shields`, `Blue Shields`, `Green Shields`)
  * **Under Development Pipeline** (vulnerability triage conveyor):
    * **Glitched Box** (corrupted modules quarantined for repairs)
    * **Scanned Box** (remediated modules completing verification before release)
  * **Personal Reserve** (2 dedicated holding slots for unpurchased Purple Proprietary Specialist dice)
  * **Institutional Override Track (`v1.0`, `v2.0`, `v3.0`)**: 3 tracking slots for once-per-version Client Company powers
* **6 Client Company Cards** (Enterprise clients contracting the consultancy; provides Once-per-Version Institutional Overrides):
  * **Meridian Financial Trust** (*Banking Infrastructure / Redundant Crew*)
  * **Omnidyne Systems** (*Tech Giant / Magnetic Splice*)
  * **Aegis Defense Relay** (*Security Firm / Baffle Echo*)
  * **Department of Telecommunications Oversight [DTO]** (*Federal Agency / Slush Fund*)
  * **Helix Biomedical Consortium** (*Medical Research / Brute-Force Bypass*)
  * **The Prometheus Foundation** (*Non-Profit / Algorithmic Arbitrage*)
* **6 White Hat Dossier Cards** (Specialist operative leads directing technical protocols; provides Personal Reserve Purple dice & Face 6 Signature Protocols):
  * **The Operator** (*Tactical Staffing & Logistics Lead / Contingent Staffing*)
  * **The Phreaker** (*Hardware Intrusion Specialist / Jumper Diagnostics*)
  * **The Acoustic** (*Side-Channel Cryptanalyst / Resonance Sensor*)
  * **The Spook** (*Covert Intelligence Specialist / Burn Notice*)
  * **The Prodigy** (*Autonomous Exploit Hacker / Arbitrary Code Execution*)
  * **The Cipher** (*Distributed Ledger Architect / Algorithmic Parity*)
* **16 Gray "Legacy Code" Starter Dice** (4 per player; safe baseline: 0 Glitches)
* **12 White "Contractor" Dice** (Temporary freelance phreakers / night-shift operators for hire in Phase 1; high risk: 2 Glitches)
* **Colored Software Module Dice:**
  * **4 Central Market Colors (`2 × Players` dice per color; universal format: 4 core faces, 1 Face 5 Glitch, 1 Face 6 Star `★`):**
    * **Red Dice** — *FinSec / Encryption* (`$5–$6`, determined by face-up Variant Card)
    * **Blue Dice** — *Firewall / Data Vault* (`$5–$7`, determined by face-up Variant Card)
    * **Green Dice** — *Antivirus / Auto-Patcher* (`$5–$6`, determined by face-up Variant Card)
    * **Yellow Dice** — *Commercial AI (High Revenue / Fast Capital)* (`$6–$7`, determined by face-up Variant Card)
  * **Purple Proprietary Specialist Dice (`2` dice per player, 8 total; held in Personal Reserves):**
    * **Purple Dice** — *Proprietary Specialist / Black-Hat AI* (`$4–$6` procurement determined by assigned White Hat Dossier; standardized high-reliability baseline + bespoke Archetype Signature Protocols)
* **Software Module Variant Cards:** Multiple cards per market die color (**Red, Blue, Green, Yellow**); **1 card per color** is used each game to define that color's Special (`★`) Face 6. *(Purple dice do not use market variant cards; their Face 6 triggers the player's bespoke Archetype Signature Protocol).*
* **Money Tokens (`$`)**, **Corporate Secret Tokens**, **Patch Tokens (`🔧`)** *(styled as magnetic tape splice kits / jumper wires)*, and a **First Player (Lead Consultant) Marker**.

---

## 3. Setup

1. **SETEC Roadmap & Compiler Priming:** Deal **1 `v1.0` card**, **1 `v2.0` card**, and **1 `v3.0` card** face-up in a row next to the Cube Tower. Place the Version Marker on `v1.0`.
   * **Per-Version Corruption Tracks (Consistent Across All Player Counts):** Each Version card features its own escalating **Corruption Track** where every space carries a mechanical effect: **`4` spaces on `v1.0`**, **`5` spaces on `v2.0`**, and **`6` spaces on `v3.0`** (`15` total Black Cubes to Singularity across `v1.0 → v2.0 → v3.0`) `[TUNE]`.
   * **Prime the Compiler (Pre-Seed Drop):** Before populating the Staging Cup, take **`1 Red, 1 Blue, 1 Green, and 1 Black Cube`** (4 cubes total) from the supply and drop them into the empty Cube Tower. Any cubes that exit into the tray are **returned to the general supply**. Any cubes that remain stuck on the internal baffles stay inside the tower to prime the compiler for Round 1.
   * Place the starting cubes listed on the `v1.0` card into the **Staging Cup** (baseline: `1 Red, 1 Blue, 1 Green, 0 Black`). *(The first Black Cube enters the Staging Cup during Round 1 Phase 1's Autonomous Protocol Pulse; all subsequent cube injections from SETEC come directly from Corruption Track spaces).*
2. **Software Market & Personal Reserves:** For each of the **4 Central Market Colors** (**Red, Blue, Green, Yellow**), shuffle its Variant Cards, place **1 Variant Card** face-up in the center, and stack **`2 × Players`** dice of that color on it. *(Purple dice are completely removed from the central market supply).* Place **`2` Purple Proprietary Specialist Dice** onto the **Personal Reserve** slot of each player's terminal mat.
3. **Consultancy Setup (Each Player):**
   * **Client Company & White Hat Operative Assignment:** Randomly deal **1 Client Company Card** and **1 White Hat Dossier Card** to each player (drawn without replacement). Place your Company Card beside your terminal mat with all 3 Version slots (`v1.0`, `v2.0`, `v3.0`) toggled to **Ready**. Place your White Hat Dossier Card face-up beside your terminal mat.
     * **Canonical Introductory Presets (Optional for First-Time Play):** Instead of random assignment, tables may deal canonical pairings:
       * **2 Players:** Player 1 (*Meridian Financial Trust* + *The Operator*), Player 2 (*Omnidyne Systems* + *The Phreaker*).
       * **3 Players:** Player 1 (*Meridian* + *The Operator*), Player 2 (*Omnidyne* + *The Phreaker*), Player 3 (*Aegis Defense Relay* + *The Acoustic*).
       * **4 Players:** Player 1 (*Meridian* + *The Operator*), Player 2 (*Omnidyne* + *The Phreaker*), Player 3 (*Aegis* + *The Acoustic*), Player 4 (*DTO* + *The Spook*).
   * Place **4 Gray Legacy Dice** into your **Ready for Release Zone**.
   * Take **`$4` Starting Money** `[TUNE: $4 baseline; test $4–$5]`.
   * **Corporate Secrets & Starting Patch Tokens by Player Count:**
     * **2 Players:** Take **`8` Corporate Secrets** and **`2` Patch Tokens (`🔧`)**.
     * **3 Players:** Take **`8` Corporate Secrets** and **`2` Patch Tokens (`🔧`)**.
     * **4 Players:** Take **`12` Corporate Secrets** and **`2` Patch Tokens (`🔧`)** `[TUNE: v0.21.0 9-round buffer parity]`.
4. Randomly assign the **First Player Marker** (used to resolve Market purchase order in Phase 3).

---

## 4. Round Structure, Client Companies & White Hat Operatives

Too Many Secrets is played over a series of rounds (~8–11 rounds). Each round consists of **3 Streamlined Phases**:
1. **Phase 1: Roll & Deploy** *(Simultaneous)*
2. **Phase 2: Compiler Drop & Defense** *(Simultaneous)*
3. **Phase 3: Operations & Pipeline Prep** *(Clockwise operations followed by simultaneous pipeline shift)*

### Client Company Institutional Overrides ("Once per Version")
Each player’s contracting Client Company provides a powerful Institutional Override that may be activated **once per SETEC Version** (`v1.0`, `v2.0`, and `v3.0`):
* **Use-It-or-Lose-It Timing:** A version's override must be activated before SETEC compiles to the next version. If SETEC advances to a new version in Phase 2 Step 2A and your current version slot has not been used, that charge is **forfeited**.
* **Immediate Version Unlock:** The newly active version's override slot unlocks immediately in the same round SETEC advances, ready for use in Phase 2B, Phase 3, or subsequent rounds.

---

### Phase 1: Roll & Deploy (Simultaneous)

1. **Autonomous Protocol Pulse:** SETEC compiles new intrusion subroutines in the background. Take **`1 Black Cube`** from the general supply across all versions (`v1.0`, `v2.0`, `v3.0`) and place it into the **Staging Cup** `[TUNE: v0.21.0 9-round pacing clock]`.
2. **Temp Staffing (Contractor Dice):** Before rolling, each player may hire temporary White Contractor Dice (freelance phreakers) for this round. Hiring uses **Progressive Contractor Pricing**: **`$1` for the 1st die, `$2` for the 2nd die, and `$3` for the 3rd die** (up to a maximum of **`3` White Dice** per round; hiring all 3 costs **`$6`** total `[TUNE]`). All hired White Contractor dice are added to your rolling pool for this round. *(Institutional Override Timing: Contracting **Meridian Financial Trust** may trigger Redundant Crew here).*
3. **Roll Ready Pool:** Every player simultaneously rolls all dice in their **Ready for Release Zone** plus any hired **White Contractor Dice**. *(Dice in your **Under Development** zone are offline and are not rolled.)*
4. **Yahtzee Rerolls (Simultaneous Pure Rerolls):**
   * Each player may perform up to **`2` free rerolls** of any subset of their rolled dice (3 rolls total).
   * Between rerolls, players may set aside (keep) any dice, or pick previously kept dice back up for subsequent rerolls.
   * **Glitch Faces & Absolute Locks:**
     * Any die that rolls a **`Glitch (Locked)`** face is locked immediately and cannot be rerolled during your free rerolls.
     * If a **Corruption Track Lock Effect** was triggered during the previous round's Phase 2 (e.g., *Cash faces cannot be rerolled next Phase 1*, *Patch faces cannot be rerolled*, or *Shield faces cannot be rerolled*), any rolled die showing that face type is also locked immediately.
     * **Absolute Locks (Zero Wrench Spending in Phase 1):** Locked dice **cannot be unlocked using Patch Tokens**. All patch token spending is strictly consolidated in Phase 3 Part 3B Fast-Patching.
     * *(Institutional Override Timing: Contracting **Helix Biomedical Consortium** may trigger Brute-Force Bypass here to freely reroll locked/glitched dice without spending patches and turn 1 rolled die to any legal non-Star face of choice).*
     * *(Operative Protocol Timing: Rolling Face 6 `Purple ★` triggers **The Operator's** Contingent Staffing to roll 1 free White Contractor die into your active pool, or **The Prodigy's** Arbitrary Code Execution to turn 1 other rolled die to any legal non-Star face).*
5. **Assign Dice to In Production (Simultaneous):**
   * After all rerolls are finished, resolve all remaining dice:
     * **Unresolved Glitches:** Any die still showing an unresolved **`Glitch (Locked)`** face moves **immediately** to the **Glitched Box** in your **Under Development** pipeline. *(A glitch only glitches the specific rolled die that failed; it produces 0 outputs).* **Contractor Sacrifice:** If a White Contractor die rolls an unresolved Glitch, it is immediately discarded to the general supply instead of entering Under Development.
     * **Cryptographic Hash Match:** Inspect all remaining active rolled dice (`Ready + Contractor`). For every set of 3 dice displaying the exact same printed output signature (e.g. 3 of a kind = +1 Secret; 6 of a kind or two distinct triplets = +2 Secrets), gain **`+1 Corporate Secret`** (uncapped). *Note: Glitch faces (`Glitch (Locked)`) are corrupted anomalies and can never form Hash Matches. Choice faces match their declared option.* *(Operative Protocol Timing: Face 6 `Purple ★` for **The Cipher** acts as a wildcard completing any pair into a 3-of-a-kind triplet).*
     * **Assign to In Production:** Place all remaining active dice into the appropriate slots of your **In Production** area:
       * **Shield Slots:** Assign dice showing `Block 1 Red`, `Block 1 Blue`, `Block 1 Green`, or `Block 1 Any` to their corresponding **Red Shields**, **Blue Shields**, or **Green Shields** slots. Any die with a dual output (e.g., Red Star R1 `Block 1 Red` + `+$2`) must be assigned to its matching Shield slot for defense.
       * **Income Slot:** Assign all other dice (producing `$`, `🔧`, or non-shield `★` abilities) to the **Income** slot.
       * **Choice Faces (`/`):** If a die shows a choice between a Shield and Income (e.g. `Block 1 Blue / +1 🔧`), the player commits it now to either Blue Shields or Income.
       * **Generic (`Any`) Shields** (including rolled White Contractor shields) must be committed to a specific color slot (`Red`, `Blue`, or `Green`) *before* Phase 2 begins.

---

### Phase 2: SETEC Compile (Simultaneous)

Take **all cubes** from the **Staging Cup** and drop them into the **Cube Tower** together. Cubes that remain stuck on the baffles stay inside the tower for future rounds. Group all cubes that exit into the tray by color and resolve in order:

#### Step 2A: Resolve Black (Corruption) Cubes, Track Spaces & Version Upgrades
Move exited **Black Cubes** from the tray onto the next empty space(s) of the active Version's **Corruption Track** one at a time from left to right. **Every space covered by a Black Cube immediately triggers its printed effect** (see Section 6C):
* **Corruption Space Effects:**
  * **Add Cubes (`+X Red/Blue/Green/Black`):** Take the specified cubes from the general supply and place into the **Staging Cup** (Mode A — Next Round Priming baseline `[TUNE]`).
  * **All Players Lose `$X`:** Each player loses up to `$X` from their supply (minimum `$0`; unpaid cash loss from a corruption space does *not* drain patches or secrets).
  * **All Players Lose `X 🔧`:** Each player loses up to `X` Patch Tokens from their supply (minimum `0`).
  * **All Players Glitch `X` Dice:** Each player must move `X` dice of their choice from **In Production** to the **Glitched Box** in **Under Development** (prioritizing Income dice; if a Shield die is moved, its shield commitment is removed).
  * **All Players Return `X` Colored Dice:** Each player who owns at least 1 Colored Module Die (across Under Development, In Production, or Ready for Release) must return up to `X` Colored Module Dice of their choice to the Market supply. *(Gray starter dice cannot be returned).*
  * **All Players Lose `X` Corporate Secrets:** Each player immediately loses `X` Corporate Secrets (checking for Patient Zero at `<= 0` Secrets).
  * **Next-Phase Face Lock (`Cash`, `Patch`, or `Shield` Faces Locked Next Phase 1):** During the next round's Phase 1 Step 4 (Rerolls), any rolled die showing that face type (including Choice faces offering that option) is immediately **Locked** and cannot be rerolled (absolute lock; only Helix Biomedical Consortium's override may bypass). *(Each Version card has at most 1 Lock space on its track).*
* **Upgrading (`v1.0 → v2.0` or `v2.0 → v3.0`):** When the final space of `v1.0` (`4th` space) or `v2.0` (`5th` space) is filled and resolved:
  1. Clear all Black Cubes from the completed Version card back to the supply.
  2. Move the Version Marker to the next Version card (`v2.0` or `v3.0`). *(No separate upgrade payload is added; the Corruption Track spaces themselves are the sole source of new cubes).*
  3. **Institutional Override Flip:** Any unused Institutional Override from the previous version is **forfeited**. The newly activated Version's override slot unlocks immediately, becoming available for use starting in Step 2B or Phase 3 of the current round.
  4. Place any remaining exited Black Cubes from this drop one at a time onto the new Version's Corruption Track, triggering each space covered!
* **Singularity (`v3.0` Track Fills):** When the final (`6th`) space of `v3.0` is filled and resolved, **Singularity is triggered!** Step 2B resolves normally for this drop, and the game enters its final round wrap-up.

#### Step 2B: Resolve Attack Cubes (Red, Blue, Green)
Calculate the total attack strength of **Red**, **Blue**, and **Green** from exited cubes in the tray. *(Institutional Override Timing: Defending **Aegis Defense Relay** may trigger Baffle Echo here to ignore 1 Attack Cube of their choice for themselves this round).* Each player simultaneously resolves all three colors against their committed Shields in **In Production**:

1. **Defensive Blocking (Zero Dice Wear):** Each die assigned to a color defense blocks **1 cube** of that color (or 2 cubes if displaying a `Block 2` ability). **Dice assigned to shields DO NOT wear down or move to Under Development when blocking!** They absorb the attack cleanly and remain safely deployed in **In Production**.
2. **Unblocked Damage:**
   * **Red (Ransomware / Financial Wiretaps):** Lose **`$1`** per unblocked Red cube.
     * **Cash-Only Ransom:** Ransom must be paid directly with cash. Held Patch Tokens (`🔧`) **cannot** absorb unpaid ransom!
     * **Unpaid Ransom Leak:** Any unpaid ransom leaks proprietary source code directly to the dark web: lose **`1 Corporate Secret` per unpaid `$1`**! Money is strictly non-negative and never drops below `$0`.
   * **Blue (Spyware / Data Exfiltration):** Lose **`1` Corporate Secret** per unblocked Blue cube.
   * *(Institutional Override Timing: Contracting **Department of Telecommunications Oversight [DTO]** may trigger Slush Fund during damage calculation to absorb up to 2 Secret loss for free).*
   * **Green (Malware / Logic Bombs):** For each unblocked Green cube, move **`1` active die from In Production** to the **Glitched Box** in your **Under Development** pipeline!
     * **Income Forfeiture:** Because this occurs before Phase 3 income collection, a die glitched by Green malware **forfeits its resource collection this round**.
     * **Defensive Shield Sacrifice:** Defending consultancies may choose to glitch a die currently in a Shield slot (one that already blocked this round) to protect an Income die!
     * **Contractor Sacrifice:** You may choose to discard **1 active White Contractor die** to the general supply instead of glitching a permanent module die.
     * **Destruction Fallback:** If you have **no dice in In Production** (or your entire pool is already offline), you must instead **Destroy (return to box) 1 die** from **Under Development**!
   * **Patient Zero Check:** If your Corporate Secrets reach **`0` (or below)**, your consultancy suffers a **Total Data Breach** and you become **Patient Zero** *(track negative Secrets below 0 if needed for total-wipeout tiebreakers)*.
3. **Snowball Recycle & Contractor Expiration:** Place **all exited Red, Blue, and Green cubes** from the tray back into the **Staging Cup** for next round. All White Contractor dice (whether they blocked, sacrificed, or remained unused) return to the general supply.
4. **Empty Tray (Compile Buffer Overflow):** If **`0 cubes of any color`** exit the tower into the tray this phase:
   * No corruption advances and no attacks occur this round (surviving dice in In Production remain safely deployed).
   * The compiler's idle cycle triggers an overflow: take **`1 Red, 1 Blue, and 1 Green Cube`** from the supply and place them into the **Staging Cup** for next round's compile (in addition to the standard Phase 1 Black Cube).

#### Step 2C: Check End Game Triggers
The current round is declared the **Final Round** if **either**:
* **Singularity** was triggered in Step 2A, **OR**
* **One or more players suffered a Total Data Breach (`<= 0 Secrets`)** in Step 2B.

If triggered, any player who became **Patient Zero** is immediately eliminated and skips Phase 3. **All surviving players proceed to Phase 3 to execute one final operations turn** before game scoring.

*(Exception: If all remaining players suffer a Total Data Breach simultaneously, the game ends immediately. Phase 3 is skipped entirely, and players proceed directly to Total Wipeout Scoring.)*

---

### Phase 3: Operations & Pipeline Prep

Phase 3 is executed in two parts: first, surviving consultancies take clockwise operations turns starting with the First Player; then, all players simultaneously prep their dice pipeline for the next round.

#### Part 3A: Operations Turns (Clockwise)
On your turn, perform any of the following operations:
1. **Collect Income & Special Outputs:**
   * Collect all **`$` Money tokens**, **Patch Tokens (`🔧`)**, and trigger any immediate `★` outputs from **all dice remaining in In Production** (both the **Income** slot and the **Shield** slots). *(Dice that were glitched during Phase 1 or by Phase 2 Green malware/corruption produce 0 outputs).*
   * *(Operative Protocol Timing: Rolling Face 6 `Purple ★` triggers **The Phreaker's** Jumper Diagnostics [roll 1 offline die in Under Development], **The Acoustic's** Resonance Sensor [+$1 cash per distinct exit tray color], **The Spook's** Burn Notice [+$2 cash and optional die burn for +1 Secret], or **The Cipher's** Algorithmic Parity [+$2 cash income]).*
2. **Purchase Software Module Dice (Limit `2` dice per turn `[TUNE]`):**
   * **Central Market:** Pay the `$` cost of any available Colored Die (**Red, Blue, Green, Yellow**) as printed on its active face-up **Variant Card** (`$5`–`$7`) and place it directly into your **Ready for Release Zone** (available to roll immediately next round!).
   * **Personal Reserve Procurement:** Alternatively (or in addition), invest the `$` procurement cost printed on your assigned **White Hat Dossier Card** (`$4`–`$6`) to purchase 1 **Purple Proprietary Specialist Die** directly from your **Personal Reserve** and place it into your **Ready for Release Zone**. This purchase counts toward your limit of 2 dice purchases per turn.
   * *(Institutional Override Timing: Contracting **The Prometheus Foundation** may trigger Algorithmic Arbitrage here to purchase 1 Colored Die from the Market or Personal Reserve at a **$2 discount** [min $0], or gain **+$2 cash**).*

#### Part 3B: Pipeline Prep & End-of-Round Staging (Simultaneous)
All consultancies simultaneously update their terminal pipeline:
1. **Fast-Patching:** Any player may spend **`1 🔧` token** per die from their supply to move a die from the **Glitched Box** immediately to the **Scanned Box** in Under Development. *(Institutional Override Timing: Contracting **Omnidyne Systems** may trigger Magnetic Splice here to move 1 die from Glitched directly to Ready for Release for free).*
2. **Scanned Graduation:** Move **all dice** in the **Scanned Box** to your **Ready for Release Zone**. *(Dice fast-patched in Step 1 graduate immediately to Ready for Release for next round!)*
3. **Production Return:** Move **all surviving dice** from **In Production** (Income and Shields) back to your **Ready for Release Zone**.
4. **Conveyor Shift:** Move **all remaining dice** in the **Glitched Box** into the **Scanned Box**. *(These dice will sit offline during the next round, graduating to Ready for Release at the end of next round naturally at zero patch cost).*
5. **Patch Token Cap:** Discard any held Patch Tokens in excess of **`3 🔧`** tokens back to the general supply (End-of-Round Cleanup Cap `[TUNE]`).
6. **Pass Lead Consultant:** If the game did not end, pass the **First Player Marker** clockwise and begin the next round. If the Final Round was triggered, proceed directly to **Section 5: End Game & Victory Scoring**.

---

## 5. End Game & Victory Scoring

### Determining the Winner
When the game ends (via Singularity when `v3.0` fills, or via Patient Zero check):

* **Standard Ending (1+ Consultancies Survive):**
  * Any player who suffered a **Total Data Breach** (`<= 0 Secrets`) is **eliminated** as Patient Zero and cannot win.
  * Surviving consultancies compare their **Corporate Secrets**. **Corporate Secrets are the sole source of victory points (`1 Secret = 1 Point`)**; Money, Patches, and Software Module dice score `0 VP`. The surviving consultancy with the **most Corporate Secrets wins!**
  * **Hierarchical Tiebreakers:** If surviving consultancies are tied for Corporate Secrets, break ties using the following hierarchy:
    1. **Operational Capital:** Most remaining **Money (`$`)**.
    2. **Active Infrastructure:** Most **Active Colored Module Dice** in your **Ready for Release Zone** (Gray starter dice and White contractor dice do not count).
    3. **Hardware Readiness:** Most remaining **Patch Tokens (`🔧`)**.
    4. **Reliability:** Fewest total dice in **Under Development** (least glitched/scanned pipeline debt).
    5. If still tied, victory is shared.

* **Total Wipeout Ending (All Consultancies Breach):**
  * Narrative victory belongs unconditionally to Project: SETEC (The Rogue Agent)!
  * To rank the human consultancies, calculate **Net Wipeout Score**: evaluate **Overflow Penalties** incurred on the fatal compile (`-1` per Secret below 0 [breach depth], `-1` per unfulfilled die destruction); highest net score takes top honors. Zero positive dice or cash bonuses are added.
  * Tied wipeout scores are resolved using the standard operational hierarchy (Secrets / breach depth > Unfulfilled Destructions > Money > Ready Colored Modules > Patches > Fewest Unpatched Dice).

---

## 6. Prototype Reference Appendix (Dice & Cards)

### A. Software Dice Faces (`d6`) `[TUNE]`

| Die Type | Cost | Face 1 | Face 2 | Face 3 | Face 4 | Face 5 | Face 6 |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **Gray (Legacy)** | Starter | `Block 1 Any` | `Block 1 Any` | `+$1` | `+$1` | `+$1 / +1 🔧` | `+1 🔧` |
| **White (Contractor)** | Prog. `$1/$2/$3` | `Block 1 Any` | `Block 1 Any` | `Block 1 Any` | `+$1` | `Glitch (Locked)` | `Glitch (Locked)` |
| **Red (FinSec)** | `$5–$6` (Variant) | `Block 1 Red` | `+$2` | `+$2` | `+$2` | `Glitch (Locked)` | `Red ★` |
| **Blue (Firewall)** | `$5–$7` (Variant) | `Block 1 Blue` | `+1 🔧` | `+$1` | `Block 1 Blue / +1 🔧` | `Glitch (Locked)` | `Blue ★` |
| **Green (Antivirus)** | `$5–$6` (Variant) | `Block 1 Green` | `+1 🔧` | `+2 🔧` | `+1 🔧 / +$1` | `Glitch (Locked)` | `Green ★` |
| **Yellow (Commercial)**| `$6–$7` (Variant) | `+$3` | `+$2` | `+$2` | `+$1 & +1 🔧` | `Glitch (Locked)` | `Yellow ★` |
| **Purple (Specialist)** | `$4–$6` (Dossier) | `Block 1 Any` | `Block 1 Any` | `+$2` | `+$1 & +1 🔧` | `Glitch (Locked)` | `Purple ★ (Signature Protocol)` |

* **Choice Faces (`/`):** Faces with a slash (`/`) indicate a Choice Face. During Phase 1 Step 5, the player declares which of the two options the die fulfills for this round.
  * **Phase 1 Lock Interactions:** A choice face displaying a Cash option (e.g. `+$1 / +1 🔧` on Gray or `+1 🔧 / +$1` on Green) is treated as a Cash face when Cash faces are locked by a Corruption Track effect (e.g. `v2.0 RaaS` Space 3). A choice face displaying a Shield option (e.g. `Block 1 Blue / +1 🔧` on Blue) is treated as a Shield face when Shield faces are locked by a Corruption Track effect (e.g. `v3.0 Zero-Day Override` Space 3). Locked dice cannot be unlocked in Phase 1 (Absolute Locks; only The Prodigy can bypass locks during rerolls).
* **Hardware Glitch Faces (`Glitch (Locked)`):** Face 5 on all 4 Market Module Dice and Purple Specialist dice (and Faces 5 & 6 on White Contractor dice) represents an unstable software glitch. When rolled, the die is locked immediately and cannot be rerolled (Absolute Lock; only The Prodigy may bypass). At the end of Phase 1 rerolls, any unresolved glitch face moves immediately to the Glitched Box in Under Development. Glitch faces produce 0 shields and 0 resource outputs.

### B. Sample Module Variant Cards (`★` Effects)
*(Note: Common market variant cards define Face 6 for Red, Blue, Green, and Yellow module dice. The purchase cost of each colored die is printed directly on its active face-up Variant Card. Purple Proprietary Specialist dice do not use market variant cards; their procurement cost and Face 6 are defined on the player's assigned White Hat Dossier detailed in Section 6D).*
* **Red `★` Variants:**
  * *R1 — Ransom Insurance (`$6`):* `[In Production — Defense]` `Block 1 Red` + `[In Production — Income]` gain `+$2`.
  * *R2 — Threat Bounty (`$6`):* `[In Production — Defense]` `Block 2 Red`; if you take `0` unblocked Red damage this round, gain `+$2`.
  * *R3 — Short Squeeze (`$5`):* `[In Production — Income]` Gain `+$3` (or `+$4` if 3+ Red cubes exit the tower this round).
* **Blue `★` Variants:**
  * *B1 — Honeypot Telemetry (`$6`):* `[In Production — Defense]` `Block 2 Blue`; if 1+ Blue cubes exit the tower and you take `0` Blue damage, gain `+$3`.
  * *B2 — Deep R&D Vault (`$7`):* `[In Production — Defense]` `Block 1 Blue`, **OR** `[Phase 3 — Operations]` pay `$4` during Phase 3 to gain `+1 Corporate Secret` `[TUNE]`.
  * *B3 — Air-Gapped Backup (`$5`):* `[In Production — Defense]` `Block 1 Blue`; when an unblocked Green malware hits, you may sacrifice `1` other Ready die of your choice to **Under Development** instead of this die `[TUNE]`.
* **Green `★` Variants:**
  * *G1 — Self-Healing Kernel (`$6`):* `[In Production — Defense]` `Block 2 Green` + `[In Production — Income]` gain `+1 🔧`.
  * *G2 — Universal Sandbox (`$5`):* `[In Production — Defense]` `Block 1 Any` + `[In Production — Income]` gain `+1 🔧`.
  * *G3 — Live Reboot (`$5`):* `[In Production — Income]` Gain `+2 🔧` + `+$1`.
* **Yellow `★` Variants:**
  * *Y1 — Algorithmic Trading (`$7`):* `[In Production — Income]` Gain `+$4`, **OR** `[Phase 3 — Operations]` pay `$2` in Phase 3 to gain `+1 Corporate Secret`.
  * *Y2 — Cloud Monopoly (`$6`):* `[In Production — Income]` Gain `+$2`, plus `+$1` per different colored module die you own (max `+$5`) `[TUNE]`.
  * *Y3 — Proprietary Training (`$6`):* `[In Production — Income]` Gain `+1 Corporate Secret`, then immediately move this die to **Under Development (Glitched)**.

### C. Sample SETEC Version Cards & Per-Version Corruption Tracks `[TUNE]`

Each Version Card defines its Corruption Track (`4` spaces on `v1.0`, `5` spaces on `v2.0`, `6` spaces on `v3.0`, consistent across all player counts). The Corruption Track is the **sole source of new SETEC cubes** entering the economy after setup. Two intensity profiles (**Standard** and **Aggressive**) are defined below for simulation benchmarking:

#### Profile 1: Standard Escalation Tracks (`4 / 5 / 6` Spaces)

| Version | Card Name | Initial Setup Cup | Space 1 | Space 2 | Space 3 | Space 4 | Space 5 | Space 6 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`v1.0`** (4) | *Script Kiddie* | `1R, 1B, 1G` | Add `1R` | All lose `$2` + Add `1K` | Lose `1 🔧` | **Upgrade:** Lose `1 🔧` | — | — |
| **`v1.0`** (4) | *Data Scraper* | `1R, 2B` (`+$1` start) | Lose `1 🔧` | Lose `$1` + Add `1K` | Add `1G` | **Upgrade:** Demote `1` die | — | — |
| **`v2.0`** (5) | *RaaS* | — | All lose `$1` | Add `1R, 1G` + Add `1K` | **Lock Cash (`$`)** next Phase 1 | Lose `$2` & `1 🔧` + Add `1K` | **Upgrade:** Add `1R` | — |
| **`v2.0`** (5) | *Polymorphic Worm* | — | Lose `2 🔧` | Add `2G` + Add `1K` | **Lock Patch (`🔧`)** next Phase 1 | Demote `1` die + Add `1K` | **Upgrade:** Add `1R` | — |
| **`v3.0`** (6) | *Zero-Day Override* | — | Add `1R, 1B, 1G` | All lose `$2` + Add `1K` | Add `1R, 1B` | **Lock Shields** next Phase 1 + Add `1K` | Return `1` Colored Die | **Singularity:** Add `2R, 2B, 2G` |
| **`v3.0`** (6) | *Corrupted Kernel* | — | Demote `1` die + Add `1R, 1B` | Lose `$2` & `1 🔧` + Add `1K` | Add `1R, 1G` | Lose `1 Secret` + Add `1K` | Return `1` Colored Die | **Singularity:** Lose `1 Secret` + Add `2R, 2B, 1G` |

#### Profile 2: Aggressive Escalation Tracks (`4 / 5 / 6` Spaces — Heightened Economic Friction)

| Version | Card Name | Initial Setup Cup | Space 1 | Space 2 | Space 3 | Space 4 | Space 5 | Space 6 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`v1.0`** (4) | *Script Kiddie* | `1R, 1B, 1G` | Add `1R` | All lose `$3` + Add `1K` | Demote `1` die | **Upgrade:** Lose `1 🔧` | — | — |
| **`v1.0`** (4) | *Data Scraper* | `1R, 2B` (`+$1` start) | Lose `2 🔧` | Lose `$2` + Add `1K` | Add `1G` | **Upgrade:** Demote `2` dice | — | — |
| **`v2.0`** (5) | *RaaS* | — | All lose `$2` | Add `1R, 1G` + Add `1K` | **Lock Cash (`$`)** next Phase 1 | Lose `$3` & `1 🔧` + Add `1K` | **Upgrade:** Add `1R` | — |
| **`v2.0`** (5) | *Polymorphic Worm* | — | Lose `2 🔧` | Add `2G` + Add `1K` | **Lock Patch (`🔧`)** next Phase 1 | Demote `2` dice + Add `1K` | **Upgrade:** Add `1R` | — |
| **`v3.0`** (6) | *Zero-Day Override* | — | Add `1R, 1B, 1G` | Lose `$3` & `1 🔧` + Add `1K` | Add `1R, 1B` | **Lock Shields** next Phase 1 + Add `1K` | Return `1` Colored Die & demote `1` die | **Singularity:** Add `2R, 2B, 2G` |
| **`v3.0`** (6) | *Corrupted Kernel* | — | Demote `2` dice + Add `1R, 1B` | Lose `$3` & `1 🔧` + Add `1K` | Add `1R, 1G` | Lose `2 Secrets` + Add `1K` | Return `1` Colored Die & demote `1` die | **Singularity:** Lose `1 Secret` + Add `2R, 2B, 1G` |

---

### D. Client Companies & White Hat Dossiers Reference Appendix

In `v0.25.0`, consultancy identity is orthogonally split into **6 Client Companies** (providing high-impact Once-per-Version Institutional Overrides) and **6 White Hat Dossiers** (providing private Personal Reserves and Face 6 Signature Protocols).

#### 1. The 6 Client Companies (`Company`) — Institutional Overrides (Once per Version)
Each player contracts with 1 enterprise Client Company for the duration of the match. Your company grants an Institutional Override that may be activated **once per SETEC Version** (`v1.0`, `v2.0`, `v3.0`):

| Company Code | Company Name | Sector | Institutional Override | Timing Window | Description | Flavor Quote |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **MERIDIAN** | **Meridian Financial Trust** | Banking Infrastructure | *Redundant Crew* | Phase 1: Step 2 Staffing | Hire up to **2 White Contractor Dice for free** this round, bypassing progressive contractor costs. | *"When liquidity is limitless, headcount is merely an accounting variable."* |
| **OMNIDYNE** | **Omnidyne Systems** | Tech Giant | *Magnetic Splice* | Phase 3: Part 3B Pipeline Prep | Move **1 die** from your **Glitched Box** directly to your **Ready for Release Zone** for **free** (bypassing Scanned and saving `1 🔧`). | *"Proprietary hardware backplanes allow instantaneous hot-swapping under live load."* |
| **AEGIS** | **Aegis Defense Relay** | Security Firm | *Baffle Echo* | Phase 2: Step 2B Damage | When resolving compiler damage, ignore **1 Attack Cube** (`Red`, `Blue`, or `Green`) of your choice for yourself this round. *(All exited cubes remain in the exit tray and recycle into the Staging Cup as normal).* | *"Multi-layered kinetic dampeners disperse inbound network blast energy."* |
| **DTO** | **Department of Telecommunications Oversight** | Federal Agency | *Slush Fund* | Phase 2: Step 2B Damage | The DTO accesses emergency black budget reserves: **Absorb up to 2 Corporate Secret loss** (from Blue Spyware or unpaid Red Ransom) for free without paying cash. *(Any additional Secret loss is absorbed by paying $1 per Secret as normal).* | *"Classified black budget allocations absorb compliance failures without public oversight."* |
| **HELIX** | **Helix Biomedical Consortium** | Medical Research | *Brute-Force Bypass* | Phase 1: Step 4 Rerolls | During your rerolls this phase, you may include **any number of Locked dice** in your free rerolls without spending 🔧 tokens. In addition, turn **1 of your rolled dice to any legal non-Star face of choice**. | *"Massively parallel quantum sequencing breaks deterministic encryption gates."* |
| **PROMETHEUS** | **The Prometheus Foundation** | Non-Profit | *Algorithmic Arbitrage* | Phase 3: Part 3A Operations Turn | Purchase **1 Colored Die** from the Market or Personal Reserve at a **`$2 discount`** (minimum cost `$0`), **OR** gain an immediate **`+$2` cash payout** from the bank. | *"Open-source cryptographic protocols circumvent proprietary enterprise licensing fees."* |

#### 2. The 6 White Hat Dossiers (`WhiteHat`) — Personal Reserve & Face 6 Signature Protocols
Each player directs 1 specialist operative lead. Your White Hat provides a private **Personal Reserve** (2 Purple Specialist dice, with procurement cost determined by operative) and defines the **Signature Protocol** triggered whenever you roll Face 6 (`Purple ★`) on a Purple Specialist die:

| White Hat Code | Operative Name | Role | Reserve Cost | Signature Protocol | Timing Window | Description | Flavor Quote |
| :--- | :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| **OPERATOR** | **The Operator** | Tactical Staffing & Logistics Lead | **`$5`** | *Contingent Staffing* | Phase 1: Step 4 Rolling | When Face 6 (`Purple ★`) is rolled, immediately roll **1 free White Contractor Die** from the supply directly into your active pool (eligible for all remaining rerolls this phase). | *"Redundant contractor pipelines ready on zero notice."* |
| **PHREAKER** | **The Phreaker** | Hardware Intrusion Specialist | **`$4`** | *Jumper Diagnostics* | Phase 3: Part 3A Operations Turn | When Face 6 (`Purple ★`) is rolled, select and roll **1 offline die** currently in your **Glitched Box** or **Scanned Box**; immediately collect any cash or patches rolled (shields/glitches produce 0). The die remains in Under Development. | *"Raw voltage pulses extract signal from dormant silicon."* |
| **ACOUSTIC** | **The Acoustic** | Side-Channel Cryptanalyst | **`$4`** | *Resonance Sensor* | Phase 3: Part 3A Income | When Face 6 (`Purple ★`) is rolled, gain **`+$1 cash`** per distinct cube color present in the Tower Exit Tray this round (`Red`, `Blue`, `Green`, `Black`; up to **`+$4`** max). | *"Harmonic resonance frequencies decode physical chassis vibrations."* |
| **SPOOK** | **The Spook** | Covert Intelligence Specialist | **`$5`** | *Burn Notice* | Phase 3: Part 3A Operations Turn | When Face 6 (`Purple ★`) is rolled, gain an immediate **`+$2` cash payout**; in addition, you may optionally **permanently return 1 owned colored module die to the market** to gain **`+1 Corporate Secret`**. | *"Scorched-earth protocols ensure zero forensic recovery."* |
| **PRODIGY** | **The Prodigy** | Autonomous Exploit Hacker | **`$5`** | *Arbitrary Code Execution* | Phase 1: Step 4 Rolling | When Face 6 (`Purple ★`) is rolled, turn **1 other rolled die** in your active pool to **any legal non-Star face of that die's color**. | *"Payload injection executes before memory boundaries establish."* |
| **CIPHER** | **The Cipher** | Distributed Ledger Architect | **`$6`** | *Algorithmic Parity* | Phase 1: Step 5 & Phase 3: Part 3A | **Phase 1 Step 5:** Purple Star acts as a **Wildcard** completing any rolled pair into a 3-of-a-kind triplet (**`+1 Corporate Secret`**).<br>**Phase 3A Income:** Purple Star generates an additional **`+$2` cash**. | *"Parity calculations balance zero-knowledge proofs flawlessly."* |

#### 3. Canonical Pairings & 36-Combination Synergy Setup
Players may freely combine any Client Company with any White Hat Operative ($6 \times 6 = 36$ total combinations).

* **Canonical Legacy Pairings:**
  - *Meridian Financial Trust* + *The Operator* (Legacy Operator archetype)
  - *Omnidyne Systems* + *The Phreaker* (Legacy Phreaker archetype)
  - *Aegis Defense Relay* + *The Acoustic* (Legacy Acoustic archetype)
  - *Department of Telecommunications Oversight* + *The Spook* (Legacy Spook archetype)
  - *Helix Biomedical Consortium* + *The Prodigy* (Legacy Prodigy archetype)
  - *The Prometheus Foundation* + *The Cipher* (Legacy Cipher archetype)
* **Canonical Introductory Presets:**
  - **2 Players:** Player 1 (Meridian + Operator), Player 2 (Omnidyne + Phreaker)
  - **3 Players:** Player 1 (Meridian + Operator), Player 2 (Omnidyne + Phreaker), Player 3 (Aegis + Acoustic)
  - **4 Players:** Player 1 (Meridian + Operator), Player 2 (Omnidyne + Phreaker), Player 3 (Aegis + Acoustic), Player 4 (DTO + Spook)
