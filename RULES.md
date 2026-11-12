# Too Many Secrets — Rules Draft (v0.38.0)

**Players:** 2–4 | **Playtime:** ~45–60 min | **Weight:** Medium Euro / Dice-Pool Survival  
**Aesthetic:** Tape-Punk / Lo-Fi Cryptography (Early 1990s ARPANET relays, monochrome CRT terminals, reel-to-reel magnetic tape, acoustic couplers)

---

## 1. Theme & Overview

A mysterious autonomous cracking program—codenamed **Project: SETEC** (the "Rogue Agent")—has broken loose across telecommunications relays and university mainframes. Recompiling its malicious subroutines each round through an acoustic mainframe compiler, SETEC aggressively probes commercial networks to manipulate markets, corrupt system hardware, and exfiltrate proprietary client data.

Each player is a **White Hat Operative** contracted to defend a **Client Company's** infrastructure. Operatives assemble and upgrade customized hardware and software modules (represented by a custom dice pool), process recovered secrets through a CI/CD pipeline, and adapt to the escalating cryptographic threat. As SETEC’s autonomous compiler accelerates across versions, White Hat Operatives must balance expanding their revenue streams against upgrading their **Company Terminal Mat** and defending their **Market Share** before proprietary client data leaks.

When the dust settles, any player who suffers a **Total Data Breach** (`<= 0 Secrets`) has their reputation incinerated, is raided by federal marshals, becomes **Patient Zero**, and is eliminated from contention. If any surviving player's **Market Share** falls to `0`, a **Market Collapse** makes the current round the last. Among the surviving White Hat Operatives, the player with the most **Corporate Secrets** wins; Secret faces on your dice and the **Market Leader Bonus** (by Market Share place) are the main ways to gain them (with Market Share, operational capital, ready modules, and research tokens serving as tiebreakers).

> **Note on `[TUNE]` Tags:** Numbers marked `[TUNE]` are prototype baselines verified via Monte Carlo simulation sweeps.

---

## 2. Components

### Central Threat (Project: SETEC / The Rogue Agent)
* **1 Cube Tower** (the Mainframe Decryption Compiler)
* **1 Staging Cup** (the Relay Queue showing code packets waiting for the next compilation cycle)
* **Compiler Cubes (4 Colors):**
  * **Red Cubes (Market Manipulation):** Lowers your **Market Share** by `1` per unblocked cube (no Money or Corporate Secrets are lost).
  * **Blue Cubes (Spyware / Data Exfiltration):** Directly steals **Corporate Secrets**.
  * **Green Cubes (Malware / Logic Bombs):** Infiltrates your Defense Grid, turning 1 shield slot into a **Glitched Shield Slot** per unblocked cube (it cannot hold a shield until cleaned).
  * **Black Cubes (Corrupted Code / Master Key Search):** Advances the active **Version Corruption Track** toward cryptographic Singularity.
* **SETEC Version Deck (`v1.0`, `v2.0`, `v3.0`):** Setup cards defining the threat's starting payload (`v1.0`) and each version's bespoke **Corruption Track** (where every space triggers a game-wide hazard or injects new cubes into the compiler).

### Player & Market Components
* **4 Company Terminal Mats**, each featuring:
  * **Ready for Release Zone** (online modules staged and ready to roll at round start)
  * **In Production Area** (active deployed modules for the current round):
    * **Income Slot** (modules producing cash and research revenue)
    * **Shield Slots** (`Block 1 Any` shields only, subject to **Defense Grid Capacity**; a **Glitched Shield Slot** cannot hold a shield)
  * **Under Development Pipeline** (secret-processing conveyor):
    * **Processing Box** (dice that rolled a **Secret face**, waiting to bank their Secret)
    * **Scanned Box** (modules completing verification before release)
    * **Hardware Throughput Limits** (Triage Bandwidth: Processing $\to$ Scanned; Release Bandwidth: Scanned $\to$ Ready)
  * **Central Market Share Track** (on the Central SETEC Agent Board, numbered `0` to `20` `[TUNE: v0.38e]`). Starting value is `13` at 2 players and `16` at 3 and 4 players (allowing `+7` or `+4` spaces of headroom to grow up to the track maximum of `20`). Lowered by unblocked **Red Cubes** and *Customer Poaching*; raised by Red and Yellow Market Share faces, *Brand Protection* and *Ad Campaign*, and regained with research through the **Public Relations Track**. A surviving player at `0` triggers a **Market Collapse** (see Phase 4). Market Share places earn the **Market Leader Bonus** (see Phase 5 and Section 5).
  * **Terminal Hardware & R&D Upgrade Tracks (4 Independent Tracks, Levels 0 $\to$ 4):** Each step costs **`1 / 2 / 2 / 3 🔬`** to reach Level 1 / 2 / 3 / 4 `[TUNE]` (`8 🔬` per track). Levels 1 and 3 of every track carry a **Breakthrough**, resolved immediately when that level is reached (see Phase 6).

    | Track | Level 0 | Level 1 (Breakthrough) | Level 2 | Level 3 (Breakthrough) | Level 4 |
    | :--- | :--- | :--- | :--- | :--- | :--- |
    | **Defense Grid Track** | Defense Capacity `2` | Gain `1` Gray Legacy die | Capacity `3` | Gain `1` Corporate Secret | Capacity `4` + `+$1` per Attack Cube blocked in Phase 4 (max `$3`) `[TUNE]` |
    | **Triage Track** | Triage Bandwidth `2` | Gain `1` Gray Legacy die | Bandwidth `3` | Pay `$3` `[TUNE]`: replace `1` Gray Legacy die with a Central Market colored die of your choice | Bandwidth `4` + `+1 🔬` per die moved in Conveyor Triage beyond the 2nd |
    | **Release Track** | Release Bandwidth `4` | Gain `1` Gray Legacy die | Bandwidth `5` | Gain `1` Corporate Secret | Bandwidth `6` + `1` extra free reroll in Phase 1 Step 4 |
    | **Public Relations Track** | Regain up to `1` Market Share per round at `3 🔬` each `[TUNE]` | Gain `$3` | Regain up to `2` per round `[TUNE]` | Gain your 2nd Purple die (from your Personal Reserve) | Regain up to `3` per round `[TUNE]` |

    *(As on the other tracks, a Breakthrough level keeps the value of the level below it: the Public Relations limit is `1` at Levels 0–1, `2` at Levels 2–3 and `3` at Level 4, always at `3 🔬` per `+1` Market Share. See Phase 6.)*

  * **Personal Reserve** (1 outline space on Public Relations Track Level 3 for your 2nd Purple Proprietary Specialist die, unlocked upon reaching Level 3)
  * **Institutional Override Track (`v1.0`, `v2.0`, `v3.0`)**: 3 tracking slots on each Client Company Card (which sits alongside your mat) for once-per-version Client Company powers (DTO *Slush Fund* is once per game)
* **CI/CD Company Terminal Mat Physical Wireframe:**
*(Client Company Cards and White Hat Dossier Cards are dealt at setup and sit alongside the mat).*
```
+--------------------------------------------------------------------------------------------------------------------+
|  [LEFT COLUMN: CORPORATE HQ]         |  [MAIN COLUMN: CI/CD PIPELINE & DEFENSE GRID]                               |
|                                      |                                                                             |
|  +--------------------------------+  |  +-----------------------------------------------------------------------+  |
|  | CORPORATE SECRETS (VP HOLDER)  |  |  | 1. READY FOR RELEASE (Active Staging / Rolling Pool)                  |  |
|  | - Start: 3 (2P) / 4 (3-4P)      |  |  |                                                                       |  |
|  | - 1 Secret = 1 VP (Uncapped)   |  |  |  [GRAY] [GRAY] [COMP] [PURP] [ ] [ ] [ ] [ ] [ ] [ ]                   |  |
|  | - <= 0 = Total Data Breach     |  |  +-----------------------------------------------------------------------+  |
|  +--------------------------------+  |                                     ^                                       |
|                                      |                                     |  [VERTICAL RELEASE TRACK]             |
|  +--------------------------------+  |                                     |  L0: 4 dice                           |
|  | LIQUID CASH ($ HOLDER)         |  |                                     |  L1 (1 🔬): ★ Gray die [DIE OUTLINE]   |
|  | - Start: $6 (Uncapped)         |  |                                     |  L2 (2 🔬): 5 dice                     |
|  | - Contractors ($3) / Market    |  |                                     |  L3 (2 🔬): ★ 1 Secret                 |
|  +--------------------------------+  |                                     |  L4 (3 🔬): 6 dice + 1 free reroll    |
|                                      |                                     |                                       |
|  +--------------------------------+  |  +-----------------------------------------------------------------------+  |
|  | RESEARCH TOKENS (🔬 HOLDER)     |  |  | 2. IN PRODUCTION (Deployed Dice)                                      |  |
|  | - Start: 0 🔬 (Uncapped)        |  |  |  +-----------------------------+  +---------------------------------+  |  |
|  | - Upgrades (1/2/2/3 🔬) & PR   |  |  |  | INCOME (Cash / Research / ★) |  | DEFENSE GRID (Shield Slots)     |  |  |
|  +--------------------------------+  |  |  |                             |  | [Slot 1] [Slot 2] [Slot 3] [Slot 4]  |  |
|                                      |  |  |                             |  +---------------------------------+  |  |
|  +--------------------------------+  |  |  |                             |  | DEFENSE GRID TRACK               |  |  |
|  | PUBLIC RELATIONS TRACK (EXPAND)|  |  |                             |  | L0: Cap 2                        |  |  |
|  | 3 🔬 = +1 Market Share (P6)    |  |  |  |                             |  | L1 (1 🔬): ★ Gray [DIE OUTLINE]  |  |  |
|  | - L0: Regain up to 1/rnd       |  |  |  |                             |  | L2: Cap 3 | L3: ★ 1 Secret       |  |  |
|  | - L1: ★ +$3 Liquid Cash        |  |  |  |                             |  | L4: Cap 4 + $1/block             |  |  |
|  | - L2: Regain up to 2/rnd       |  |  |  +-----------------------------+  +---------------------------------+  |  |
|  | - L3: ★ 2nd Purple Specialist  |  |  +-----------------------------------------------------------------------+  |
|  |   Die Reserve [DIE OUTLINE]    |  |                                                                             |
|  | - L4: Regain up to 3/rnd       |  |  +-----------------------------------------------------------------------+  |
|  +--------------------------------+  |  | 3. UNDER DEVELOPMENT (CI/CD Pipeline)                                 |  |
|                                      |  |  +-------------------+  +------------------------------------------+  |  |
|                                      |  |  | SCANNED BOX       |  | TRIAGE TRACK (Conveyor Bandwidth)        |  |  |
|                                      |  |  | (Unbounded Tray)  |  | L0: 2 | L1 (1🔬): ★ Gray [DIE OUTLINE]   |  |  |
|                                      |  |  |                   |  | L2: 3 | L3 (2🔬): ★ $3 swap | L4: 4 + 🔬  |  |  |
|                                      |  |  | ^ Graduates to    |  +------------------------------------------+  |  |
|                                      |  |  |   Ready for       |  | PROCESSING BOX (Elongated FIFO Queue)    |  |  |
|                                      |  |  |   Release (P5)    |  | <-- [OLDEST] <== FIFO FLOW <== [NEWEST]  |  |  |
|                                      |  |  |                   |  | Bank on Exit: Purple +1, Red/Blue/Grn +2 |  |  |
|                                      |  |  +-------------------+  +------------------------------------------+  |  |
|                                      |  +-----------------------------------------------------------------------+  |
+--------------------------------------+-----------------------------------------------------------------------------+
```
* **6 Client Company Cards** (Enterprise clients contracting the White Hat Operative; each grants an Institutional Override and names the color of your starting colored die — Red, Blue or Green, see Section 6D. Every company starts with the same hardware and resources):
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
* **20 Gray "Legacy Code" Dice** (2 per player at setup, more via the Defense Grid, Triage and Release Level 1 Breakthroughs; safe baseline: no Glitch or Secret face)
* **12 White "Contractor" Dice** (Temporary freelance phreakers / night-shift operators for hire in Phase 1; high risk: 2 Glitches)
* **Colored Software Module Dice:**
  * **4 Central Market Colors (`2 × Players` dice per color; Red, Blue and Green: 4 core faces, Face 5 **Secret face**, Face 6 Star `★`; Yellow: 5 core faces and Face 6 Star `★`, no Secret face):**
    * **Red Dice** — *Marketing* (`$4–$5`, determined by face-up Variant Card)
    * **Blue Dice** — *Firewall / Data Vault* (`$4–$6`, determined by face-up Variant Card; provides direct Corporate Secrets on Faces 1 & 2, cash/research choices, and hardware-synergized Secret banking on Face 5)
    * **Green Dice** — *Antivirus / Auto-Patcher* (`$4–$5`, determined by face-up Variant Card)
    * **Yellow Dice** — *Commercial AI (High Revenue / Fast Capital)* (`$5–$6`, determined by face-up Variant Card)
  * **Purple Proprietary Specialist Dice (`2` dice per player: 1 in Ready for Release, 1 in Personal Reserve):**
    * **Purple Dice** — *Proprietary Specialist / Black-Hat AI* (not purchasable; your 2nd Purple die is gained only from the Public Relations Level 3 Breakthrough, and a Purple die lost to an effect is not replaced; standardized high-reliability baseline with a Face 5 **Secret face** + bespoke White Hat Signature Protocols)
* **Software Module Variant Cards:** Multiple cards per market die color (**Red, Blue, Green, Yellow**); **1 card per color** is used each game to define that color's Special (`★`) Face 6. *(Purple dice do not use market variant cards; their Face 6 triggers the player's bespoke Signature Protocol).*
* **Money Tokens (`$`)**, **Corporate Secret Tokens**, **Research Tokens (`🔬`)** *(uncapped; styled as magnetic tape data spools / cryptographic research notes)*, **1 Market Share Marker per player**, and a **First Player Marker**.

---

## 3. Setup

1. **SETEC Roadmap & Compiler Priming:** Deal **1 `v1.0` card**, **1 `v2.0` card**, and **1 `v3.0` card** face-up in a row next to the Cube Tower. Place the Version Marker on `v1.0`.
   * **Per-Version Corruption Tracks (Consistent Across All Player Counts):** Each Version card features its own escalating **Corruption Track** where every space carries a mechanical effect: **`4` spaces on `v1.0`**, **`5` spaces on `v2.0`**, and **`6` spaces on `v3.0`** (`15` total Black Cubes to Singularity across `v1.0 → v2.0 → v3.0`) `[TUNE]`.
   * **Prime the Compiler (Pre-Seed Drop):** Before populating the Staging Cup, take **`1 Red, 1 Blue, 1 Green, and 1 Black Cube`** (4 cubes total) from the supply and drop them into the empty Cube Tower. Any cubes that exit into the tray are **returned to the general supply**. Any cubes that remain stuck on the internal baffles stay inside the tower to prime the compiler for Round 1.
   * Place the starting cubes listed on the `v1.0` card into the **Staging Cup** (baseline: `2 Red, 1 Blue, 1 Green, 0 Black` on *Script Kiddie*; `1 Red, 2 Blue, 1 Green, 0 Black` on *Data Scraper*). *(The first Black Cube enters the Staging Cup during Round 1 Phase 1's Autonomous Protocol Pulse; all subsequent cube injections from SETEC come directly from Corruption Track spaces).*
2. **Software Market & Personal Reserves:** For each of the **4 Central Market Colors** (**Red, Blue, Green, Yellow**), shuffle its Variant Cards, place **1 Variant Card** face-up in the center, and stack **`2 × Players`** dice of that color on it. *(Purple dice are completely removed from the central market supply).* Place **`1` Purple Proprietary Specialist Die** onto the **Personal Reserve** slot of each player's **Company Terminal Mat**.
3. **Player Setup (Each White Hat Operative):**
   * **Client Company & White Hat Operative Assignment:** Randomly deal **1 Client Company Card** and **1 White Hat Dossier Card** to each player (drawn without replacement). Place your Company Card beside your **Company Terminal Mat** with all 3 Version slots (`v1.0`, `v2.0`, `v3.0`) toggled to **Available**. Every Client Company starts with the same hardware: all 4 tracks at **Level 0** (Defense Capacity `2`, Triage Bandwidth `2`, Release Bandwidth `4`, Public Relations: regain up to `1` Market Share per round at `3 🔬`). Each player starts with **`1` Glitched Shield Slot** on their **Company Terminal Mat** (leaving `1` clean Shield Slot and `1` Glitched Shield Slot available to block at defense capacity 2). Apart from the color of your starting colored die (below), Client Companies grant no starting bonuses.
   * Place **2 Gray Legacy Dice + 1 starting colored die + 1 Purple Specialist Die** into your **Ready for Release Zone** (rolls in Round 1). The starting colored die is the color named by your Client Company (Red: Meridian, Prometheus; Blue: DTO, Aegis; Green: Omnidyne, Helix `[TUNE]`); take it from that color's Central Market stack (it uses that color's face-up Variant Card).
   * Take **`$6` Starting Money**.
   * **Corporate Secrets & Starting Research Tokens:** Take **`3` Corporate Secrets** at **2 players**, **`4`** at **3 players**, or **`4`** at **4 players** `[TUNE: v0.38.0]`, and **`0 🔬` Research Tokens**.
   * **Market Share:** Place your Market Share Marker on **`13`** at **2 players**, **`16`** at **3 players**, or **`17`** at **4 players** `[TUNE: v0.38.0]`. This starting value is also your maximum Market Share for the game.
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
   * **Glitch Faces (White Contractor dice only):** A White Contractor die that rolls a **`Glitch`** face cannot be rerolled during your free rerolls.
   * **Secret Faces:** A **Secret face** (Face 5 on Red, Blue, Green and Purple dice) is a normal face during rerolls: you may keep it or reroll it.
     * *(Institutional Override Timing: Contracting **Helix Biomedical Consortium** may trigger Brute-Force Bypass here: gain `1` extra free reroll this phase, you may include Glitch dice in your free rerolls, and turn 1 rolled die to any legal non-Star face of its color, including the Secret face).*
     * *(Signature Protocol Timing: Rolling Face 6 `Purple ★` triggers **The Operator's** Contingent Staffing to roll 1 free White Contractor die into your active pool, or **The Prodigy's** Arbitrary Code Execution to turn 1 other rolled die to any legal non-Star face of its color other than the Secret face).*
5. **Assign Dice to In Production (Simultaneous):**
   * After all rerolls are finished, resolve all remaining dice:
     * **Unresolved Glitches (Contractor Sacrifice):** A White Contractor die still showing **`Glitch`** is discarded to the general supply (it produces 0 outputs).
     * **Secret Faces $\to$ Processing Box:** Any die showing a **Secret face** moves **immediately** to the **Processing Box** in your **Under Development** pipeline and produces no other output. It banks its Secret when it leaves the Processing Box (see Phase 5 and *Secret Face Yields* below).
     * **Clean Glitched Shield Slots:** First, each die showing a `Clean 1 Glitched Shield Slot` face (*G1 Self-Healing Kernel*) cleans 1 of your **Glitched Shield Slots** and stays In Production (*G1* still pays its `+1 🔬` in Phase 3; a die showing Face 1 of Green is `+2 🔬` and does not clean slots). Then you may place any die showing a `Block 1 Any` face on a Glitched Shield Slot to clean it: that die produces no output and moves at once to your **Scanned Box** (a White Contractor die is discarded to the general supply instead). Dice showing a `★`, a Secret face or a face without a shield cannot clean a slot this way.
     * **Assign to In Production (Defense Grid Capacity Enforcement):** Place all remaining active dice into the appropriate slots of your **In Production** area:
       * **Shield Slots & Defense Grid Capacity:** Assign dice showing `Block 1 Any` to your Shield slots. **Hardware Limit:** The number of dice assigned to Shield slots cannot exceed your current **`defense_capacity`** (`2` baseline, upgradable to `3` and `4`) minus your **Glitched Shield Slots** (minimum `0`). Any rolled die displaying a shield that exceeds this cannot block and must be placed into the Income slot (producing `0` output if it has no income face).
       * **Income Slot:** Assign all other dice (producing `$`, `🔬`, Market Share, or non-shield `★` abilities) to the **Income** slot.
       * **Choice Faces (`/`):** If a die shows a choice (e.g. `+1 Market Share / +$1`), the player commits it now to one option.
       * **Generic (`Any`) Shields** (including rolled White Contractor shields) are not pre-committed to a cube color in Phase 1; they absorb threat reactively in Phase 4: Attack Resolution. No shield is tied to a single cube color.

---

### Phase 2: Compiler Drop & Corruption (Simultaneous)

Take **all cubes** from the **Staging Cup** and drop them into the **Cube Tower** together. Cubes that remain stuck on the baffles stay inside the tower for future rounds. Group all cubes that exit into the tray by color. **Black Cubes resolve now**; exited **Attack Cubes** (`Red`, `Blue`, `Green`) stay in the **Exit Tray** and resolve in **Phase 4: Attack Resolution** (after Phase 3: Income).

#### Resolve Black (Corruption) Cubes, Track Spaces & Version Upgrades
Move exited **Black Cubes** from the tray onto the next empty space(s) of the active Version's **Corruption Track** one at a time from left to right. **Every space covered by a Black Cube immediately triggers its printed effect** (see Section 6C). Corruption resolves **before** Phase 3: Income, so cash losses land on your pre-income Money and income is then collected on top:
* **Corruption Space Effects:**
  * **Add Cubes (`+X Red/Blue/Green/Black`):** Take the specified cubes from the general supply and place into the **Staging Cup** (Mode A — Next Round Priming baseline `[TUNE]`).
  * **All Players Lose `$X`:** Each player loses up to `$X` from their supply (minimum `$0`; unpaid cash loss from a corruption space does *not* drain research or secrets).
  * **All Players Lose `X 🔬`:** Each player loses up to `X` Research Tokens from their supply (minimum `0`).
  * **(All Players) Glitch `X` Dice:** Each affected player turns `X` of their shield slots into **Glitched Shield Slots** (up to their Defense Grid Capacity; excess has no effect). No dice move. Shields already placed this round still block in Phase 4; a Glitched Shield Slot reduces your capacity from your next Phase 1.
  * **All Players Return `X` Colored Dice:** Each player who owns at least 1 Colored Module Die (across Under Development, In Production, or Ready for Release) must return up to `X` Colored Module Dice of their choice to the Market supply. *(Gray starter dice cannot be returned).* A returned die in the **Processing Box** loses its Secret.
  * **All Players Lose `X` Corporate Secrets:** Each player immediately loses `X` Corporate Secrets (checking for Patient Zero at `<= 0` Secrets).
* **Version Advance & Track Spillover (`v1.0 → v2.0` or `v2.0 → v3.0`):** When the final space of `v1.0` (`4th` space) or `v2.0` (`5th` space) is filled and resolved:
  1. The final space's printed effect executes immediately (including any **Total Data Breach** it causes).
  2. Any excess Black cubes dropped in the same compile step **immediately spill over** onto the next Version's Corruption Track (starting at Space 1), triggering each newly covered space's printed effect in sequence.
  3. The **active version card remains the current version** for the remainder of the current round.
  4. The current version's Institutional Override **remains usable** through **Phases 3–6**. The upcoming version's Institutional Override is not unlocked yet.
  5. At the **start of the subsequent round** (in Phase 1 Step 1), the version transition officially takes effect: unspent overrides from the old version are forfeited, and the new version's override unlocks to Available.
  6. There is no Market Share comparison for Money when a version fills (removed in v0.38.0).
* **Singularity (`v3.0` Track Fills):** When the final (`6th`) space of `v3.0` is covered by a Black cube, resolve that space's printed effect (e.g., *Corrupted Kernel* `Lose 1 Secret`), and **Singularity is triggered—the game ends IMMEDIATELY at the end of Phase 2!** **Phases 3–6 are skipped** (no income is collected and no Secrets leave the Processing Box); all surviving non-Contractor dice in **In Production** return to **Ready for Release**, all White Contractor dice return to the general supply, and players proceed directly to **Section 5: End Game & Victory Scoring** (the game-end **Market Leader Bonus** is awarded).

#### Compile Buffer Overflow (Empty Tray)
If **`0 cubes of any color`** exit the tower into the tray this phase:
* No corruption advances and **no attacks occur this round** (Phase 4 resolves no damage). **Income is still collected in Phase 3.**
* The compiler's idle cycle triggers an overflow: take **`1 Red, 1 Blue, and 1 Green Cube`** from the supply and place them into the **Staging Cup** for next round's compile (in addition to the standard Phase 1 Black Cube).

#### End Game Trigger Check (End of Phase 2)
* **Singularity** ends the game at the end of Phase 2 (see above), so a **Market Collapse** cannot also be checked that round.
* If **all** players suffered a **Total Data Breach** (`<= 0 Secrets`) from Corruption Track effects, the game ends immediately as a **Total Wipeout** (Phases 3–6 are skipped).
* If **one or more (but not all)** players suffered a **Total Data Breach**, each of them becomes **Patient Zero**, is eliminated, and **skips Phases 3–6**. The current round becomes the **Final Round**: all surviving players **complete every remaining phase** (Phase 3: Income, Phase 4: Attack Resolution, Phase 5: CI/CD Pipeline Shift, Phase 6: Operations) before game scoring.

---

### Phase 3: Income (Simultaneous)

Every surviving player simultaneously collects all **`$` Money tokens**, **Research Tokens (`🔬`)**, **Corporate Secrets** (Blue Faces 1 & 2), and immediate `★` outputs from **all dice still in In Production** (both the **Income** slot and the **Shield** slots), **including White Contractor dice** (e.g., a Contractor's `+$1` face pays now). *(Dice that went to the Processing Box or the Scanned Box in Phase 1, or were returned by Corruption Track effects in Phase 2, are no longer In Production and produce 0 outputs).*
* **Market Share faces resolve here:** Red Face 1 (`+1 Market Share` option) and Yellow Market Share faces raise your Market Share now. They cannot raise it above your maximum and do not count toward your Public Relations limit.
* **Star outputs resolved here:** *R1 Brand Protection* (`+$2 & +1 Market Share`, same limits), *Y2 Cloud Monopoly* (bonus cash), *B3 Air-Gapped Backup* (move `1` die from your **Processing Box** to your **Scanned Box**; it banks its Secret now, see *Secret Face Yields*), and *Y3 Proprietary Training* (`+1 Corporate Secret`, then this die moves to the **Scanned Box**). Each *R2 Ad Campaign* die still In Production now earns you `1` use of its paid action in this round's Phase 6.
* **Customer Poaching (after all players' Income):** Once every player has collected Income, resolve each *R3 Customer Poaching* die still In Production, going clockwise from the **First Player** (one die at a time if a player has several):
  * Take **`1` Market Share** from the surviving rival with the **most Market Share** (not Patient Zero, and above `0`). If several rivals are tied for the most, you choose among them. If no rival has Market Share above `0`, nothing happens.
  * That rival loses `1` Market Share and you gain `1`. Your Market Share cannot go above your maximum: if you are already at your maximum, the rival still loses `1` and you gain nothing.
  * Re-check which rival has the most Market Share before each Customer Poaching die. A rival taken to `0` causes a **Market Collapse** at the end of Phase 4.
* *(Signature Protocol Timing: each Face 6 `Purple ★` die **still In Production** triggers its Signature Protocol once — **The Phreaker's** Jumper Diagnostics [move 1 die from your Processing Box to your Scanned Box, banking its Secret now; if your Processing Box is empty, roll 1 Scanned Box die and collect only its `$` and `🔬` output (it stays in place); if Under Development is empty, collect +$1 cash], **The Acoustic's** Resonance Sensor [+$1 cash per distinct exit tray color], **The Spook's** Burn Notice [+$2 cash and optional die burn for +1 Secret], or **The Cipher's** Algorithmic Parity [+$2 cash & +1 🔬 Research Token]. Two `Purple ★` dice trigger the protocol twice; Burn Notice may not target the same die twice. A `Purple ★` die that left In Production in Phase 2 triggers nothing. Burn Notice may target a die that is In Production; that die no longer blocks in Phase 4).*

---

### Phase 4: Attack Resolution (Simultaneous)

Calculate the total attack strength of **Red**, **Blue**, and **Green** from exited cubes in the tray.
* *(Institutional Override Timing: Defending **Aegis Defense Relay** may trigger Baffle Echo here to ignore 1 Attack Cube of their choice for themselves this round).*

Each surviving player simultaneously resolves all three colors against their committed Shields still in **In Production** (a player who became **Patient Zero** in Phase 2 is not attacked):

1. **Blocking:**
   * Every shield is a `Block 1 Any` shield. You choose how your available shields are split across the Red, Blue and Green cubes. **Every available `Any` shield must block while any unblocked cube remains**: you choose only the split, and you cannot hold a shield back.
   * Dice assigned to shields absorb attacks cleanly and remain deployed in **In Production**.
2. **Unblocked Damage:**
   * **Red (Market Manipulation):** Lower your **Market Share** by **`1`** per unblocked Red cube (Market Share cannot drop below `0`; any excess has no further effect). Red cubes never cost Money or Corporate Secrets.
   * **Blue (Spyware / Data Exfiltration):** Lose **`1` Corporate Secret** per unblocked Blue cube.
   * *(Institutional Override Timing: Contracting **Department of Telecommunications Oversight [DTO]** may trigger Slush Fund during damage calculation to absorb up to 2 Corporate Secret loss from Blue cubes for free; **once per game**, and you choose whether to use it when it would apply).*
   * **Green (Malware / Logic Bombs):** For each unblocked Green cube, turn **`1` of your shield slots** into a **Glitched Shield Slot**. No die moves. You cannot have more Glitched Shield Slots than your Defense Grid Capacity; excess unblocked Green has no effect. Glitched Shield Slots stay glitched until cleaned (Phase 1 Step 5, Phase 5 Step 3); a new slot gained from the Defense Grid Track arrives clean.
   * **Damage-Conditional `★` Outputs:** *B1 Honeypot Telemetry* bonuses are evaluated now, **only for dice still In Production** (a die returned in Phase 2, or removed in Phase 3, does not pay).
   * **Patient Zero Check:** If your Corporate Secrets reach **`0` (or below)**, you suffer a **Total Data Breach** and become **Patient Zero**.
   * **Defense Grid Level 4:** After your damage has resolved, gain **`+$1` per Attack Cube** (`Red`, `Blue`, or `Green`) your shields blocked this phase (max **`$3`**) `[TUNE]`. Cubes ignored by *Baffle Echo* were not blocked and do not count. Blocked Red cubes count.
3. **Snowball Recycle & Contractor Expiration:** Place **all exited Red, Blue, and Green cubes** from the tray back into the **Staging Cup** for next round. All White Contractor dice (whether they blocked, sacrificed, or remained unused) return to the general supply.
4. **Compile Buffer Overflow:** If the tray was empty in Phase 2, no damage resolves this phase (no Baffle Echo, damage-conditional `★` bonuses, or Defense Grid Level 4 cash); Contractor Expiration and the End Game Trigger Check (including **Market Collapse**, since *Customer Poaching* may have lowered Market Share in Phase 3) still occur.

#### End Game Trigger Check (End of Phase 4)
* If **all** players are now **Patient Zero** (including any Patient Zero from Phase 2), the game ends immediately as a **Total Wipeout**; Phases 5–6 are skipped and Market Collapse is not checked.
* If **one or more (but not all)** players are **Patient Zero**, the current round is the **Final Round**: each Patient Zero is eliminated, and all surviving players **complete Phase 5 and Phase 6** before game scoring.
* **Market Collapse:** Then, if any surviving player has **`0` Market Share**, the current round becomes the **Final Round** (if it is not already). **No one is eliminated and there is no other penalty**: every surviving player, including any at `0`, completes Phase 5 and Phase 6 before game scoring. Regaining Market Share in Phase 6 does not cancel the Final Round.
  * If a player also became **Patient Zero** this round (in Phase 2 or Phase 4), the Patient Zero rules above apply as well: each breached player is eliminated, and the round is the Final Round either way.

---

### Phase 5: CI/CD Pipeline Shift (Simultaneous)

All surviving players simultaneously update their terminal pipeline in this order:
1. **Magnetic Splice:** *(Institutional Override Timing: Contracting **Omnidyne Systems** may trigger Magnetic Splice here to move 1 die of your choice from your Processing Box directly to Ready for Release for free; it banks its Secret now).*
2. **Production Return:** Move **all surviving dice** from **In Production** (Income and Shields) to your **Scanned Box**.
3. **Scanned Graduation (Hardware Throughput Limit):** Move up to **`release_bandwidth` dice of your choice** (`4` baseline, upgradable to `5` and `6`) from the **Scanned Box** to your **Ready for Release Zone**. You may graduate fewer. Any remaining dice stay in the Scanned Box.
4. **Conveyor Triage (Hardware Throughput Limit):** Move up to **`triage_bandwidth` dice** (`2` baseline, upgradable to `3` and `4`) from the **Processing Box** into the **Scanned Box**, **oldest first**: dice leave in the order they entered the Processing Box (any color; dice that entered together leave in roll order). You do not choose. Each die banks its Secret as it moves (see *Secret Face Yields*). When a **Green** die leaves the Processing Box and banks its Secret, it cleans `1` of your **Glitched Shield Slots**. *(Dice triaged now graduate no earlier than next round's Phase 5.)* At **Triage Track Level 4**, gain **`+1 🔬`** for each die you move beyond the 2nd (up to `+2 🔬` at Bandwidth `4`).
   * **Hardware Throughput Limits:** Throughput is strictly governed by your Triage and Release hardware bandwidths; excess dice remain in the Processing Box (keeping their Secret for a later round), and excess scanned dice remain in the Scanned Box.
5. **Market Leader Bonus (end of Phase 5):** If at least `1` Secret face on a **Red** die was banked this round (by any player, in Phase 3 or Phase 5), award the **Market Leader Bonus** once (see below). Several Red Secret faces in one round still give one award.

#### Secret Face Yields `[TUNE]`
A die showing a **Secret face** banks its Secret when it leaves the **Processing Box** (Conveyor Triage, *Magnetic Splice*, *Jumper Diagnostics*, *B3 Air-Gapped Backup*): its owner gains **Corporate Secrets** by the die's color, using the game state at that moment:
* **Red:** `+2`.
* **Blue:** `+2`, plus `1` if your Defense Grid Track is at Level 3 or higher (maximum `+3`).
* **Green:** `+2`; then clean `1` of your **Glitched Shield Slots**.
* **Purple:** `+1`.

A die returned to the supply from the Processing Box, or still in the Processing Box when the game ends, banks nothing.

#### Market Leader Bonus
Place every player who is not **Patient Zero** by their **Market Share** at that moment (highest first). Each gains **Corporate Secrets** by place `[TUNE: v0.38.0]`: **1st `+3`, 2nd `+1`, other places `0`** at every player count. Tied players share the better place and each gain its award (e.g., two players tied for 1st both gain `+3`; the next player is 3rd). Patient Zeros gain nothing and take no place; a sole survivor takes 1st; a player at `0` Market Share is placed like anyone else. It is awarded at the end of Phase 5 in any round with a Red Secret face banked (including the Final Round) and once more at game end (Section 5).

---

### Phase 6: Operations (Operations Turns, Clockwise)

Surviving White Hat Operatives take clockwise **Operations Turns** starting with the **First Player**. On your turn, perform any of the following operations in any order:
1. **Terminal Hardware Track Upgrades:**
   * Spend Research Tokens (`🔬`) to raise any of your 4 tracks one level at a time: **`1 🔬`** to reach Level 1, **`2 🔬`** for Level 2, **`2 🔬`** for Level 3, **`3 🔬`** for Level 4 `[TUNE]` (no discounts; unlimited upgrades per turn as long as tokens are available). See the track table in Section 2.
   * **Breakthroughs (Levels 1 and 3):** When a track reaches Level 1 or Level 3, its **Breakthrough** resolves **immediately**, before your next operation. If you raise several levels in one turn, resolve them one level at a time, in the order you buy them (e.g. `$3` from the Public Relations Level 1 Breakthrough can pay for a Triage Level 3 Breakthrough bought afterwards). Each Breakthrough happens only once, the first time you reach that level.
     * New dice from a Breakthrough (Gray Legacy, Central Market colored or Purple) go to your **Ready for Release Zone** and do not use Release Bandwidth.
     * **Triage Level 3 Breakthrough (optional):** Pay **`$3`** `[TUNE]` to return `1` Gray Legacy die you own (from your Ready for Release Zone, Scanned Box or Processing Box) to the box and take `1` die of any Central Market color with stock left (it uses that color's active Variant Card). The new die goes to your Ready for Release Zone. The `$3` is flat (not the Variant Card price), is not a purchase (it does not count toward your 2-dice limit), and cannot be discounted by *Algorithmic Arbitrage*. If you can't pay, own no Gray Legacy die, or every Central Market stack is empty, or you decline, the Breakthrough is lost (it cannot be claimed later).
     * **Public Relations Level 3 Breakthrough:** Move the Purple die from your Personal Reserve to your Ready for Release Zone.
   * Defense Capacity applies from next round's Phase 1; Triage and Release Bandwidth apply from next round's Phase 5; Level 4 effects apply from the next phase in which they are used.
2. **Regain Market Share (Public Relations Track):**
   * Spend **`3 🔬`** `[TUNE]` for each **`+1` Market Share**, up to your current Public Relations limit this turn: **`1`** at Levels 0–1, **`2`** at Levels 2–3, **`3`** at Level 4 `[TUNE]`. A level bought earlier in the same turn applies to later regains.
   * Market Share can never exceed the track maximum (`20`); you cannot spend research while at the track maximum.
   * You may regain Market Share during the Final Round (final Market Share sets your game-end **Market Leader Bonus** place and is the first tiebreaker), but doing so does not cancel a Final Round already triggered.
3. **Paid `★` Actions:** Resolve *B2 Deep R&D Vault* (pay `$4` → `+1` Corporate Secret) or *Y1 Algorithmic Trading* Secret purchases rolled this round, and *R2 Ad Campaign* (pay `$2` → `+1` Market Share, once per *Ad Campaign* die that was In Production in Phase 3). *Ad Campaign* does not count toward your Public Relations limit, cannot raise Market Share above the track maximum of `20` (you do not pay while at maximum), and any unused *Ad Campaign* is lost at the end of your Operations Turn.
4. **Purchase Software Module Dice (Limit `2` dice per turn `[TUNE]`):**
   * **Central Market:** Pay the `$` cost of any available Colored Die (**Red, Blue, Green, Yellow**) as printed on its active face-up **Variant Card** (`$4`–`$6`) and place it directly into your **Ready for Release Zone** (available to roll next round; purchases do not use Release Bandwidth).
   * Purple Proprietary Specialist dice cannot be purchased.
   * *(Institutional Override Timing: Contracting **The Prometheus Foundation** may trigger Algorithmic Arbitrage here to purchase 1 Colored Die from the Central Market at a **$2 discount** [min $0], or gain **+$2 cash**).*
5. **Uncapped Research Storage:** Research tokens (`🔬`) have **no storage cap**! Retain all unspent Research tokens in your supply for future rounds.

After the last Operations Turn: if this was the **Final Round**, proceed directly to **Section 5: End Game & Victory Scoring**. Otherwise, **pass the First Player Marker** clockwise and begin the next round.

---

## 5. End Game & Victory Scoring

### Determining the Winner
When the game ends (via Singularity when `v3.0` fills, at the end of the **Final Round** triggered by **Patient Zero** or **Market Collapse**, or via **Total Wipeout**):

* **Standard Ending (1+ White Hat Operatives Survive):**
  * Any player who suffered a **Total Data Breach** (`<= 0 Secrets`) is **eliminated** as Patient Zero and cannot win.
  * **Processing Box at game end:** Dice still in your **Processing Box** bank nothing (their Secrets are lost).
  * **Market Leader Bonus (game end):** First, award the **Market Leader Bonus** once more by final **Market Share** (see Phase 5): 1st `+3`, 2nd `+1`, other places `0` `[TUNE: v0.38.0]` at every player count. It is awarded on every ending except a **Total Wipeout** (Singularity, Patient Zero and Market Collapse endings all award it), in addition to any award at the end of the last round's Phase 5.
    * Tied players share the better place and each gain its award (e.g., two players tied for 1st both gain `+3`; the next player is 3rd). There is no further tiebreak for the bonus.
    * Patient Zeros gain nothing and take no place; survivors below them move up. A sole survivor takes 1st.
  * Surviving White Hat Operatives then compare their **Corporate Secrets**. **Corporate Secrets are the sole source of victory points (`1 Secret = 1 Point`)**; Market Share scores only through the Market Leader Bonus, and Money, Research tokens, and Software Module dice score `0 VP`. The surviving White Hat Operative with the **most Corporate Secrets wins!**
  * **Hierarchical Tiebreakers:** If surviving players are tied for Corporate Secrets, break ties using the following hierarchy:
    1. **Market Position:** Most final **Market Share**.
    2. **Operational Capital:** Most remaining **Money (`$`)**.
    3. **Active Infrastructure:** Most **Active Colored Module Dice** in your **Ready for Release Zone** (Gray starter dice and White contractor dice do not count).
    4. **Hardware Readiness:** Most remaining **Research Tokens (`🔬`)**.
    5. **Reliability:** Fewest total dice in **Under Development** (Processing Box + Scanned Box).
    6. If still tied, victory is shared.
  * A player at `0` Market Share after a **Market Collapse** is not eliminated, scores normally, and is placed by Market Share for the Market Leader Bonus like anyone else (players tied at `0` share a place).

* **Total Wipeout Ending (All Players Breach):**
  * Narrative victory belongs unconditionally to Project: SETEC (The Rogue Agent)! No **Market Leader Bonus** is awarded.
  * To rank the human players, **breach depth is ignored**: players are ranked **only** by the standard **Hierarchical Tiebreakers** above (Market Share > Money > Active Colored Module Dice in Ready for Release > Research Tokens > Fewest Under Development Dice > shared). A player who breached earlier (e.g., in Phase 2) keeps the Market Share they had when they breached and does not outrank anyone by breach depth.

---

## 6. Prototype Reference Appendix (Dice & Cards)

Moved to [RULES_APPENDIX.md](RULES_APPENDIX.md) (dice faces, Variant ★ cards, Version cards, Client Companies, White Hat Operatives).

## 7. Glossary of Key Terms

Moved to [GLOSSARY.md](GLOSSARY.md). It is the canonical terminology source.
