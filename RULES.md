# Too Many Secrets — Rules Draft (v0.50.0)

**Players:** 2–4 | **Playtime:** ~45–60 min | **Weight:** Medium Euro / Dice-Pool Survival  
**Aesthetic:** Tape-Punk / Lo-Fi Cryptography (Early 1990s ARPANET relays, monochrome CRT terminals, reel-to-reel magnetic tape, acoustic couplers)

---

## 1. Theme & Overview

A mysterious autonomous cracking program—codenamed **Project: SETEC** (the "Rogue Agent")—has broken loose across telecommunications relays and university mainframes. Recompiling its malicious subroutines each round through an acoustic mainframe compiler, SETEC aggressively probes commercial networks to manipulate markets, corrupt system hardware, and exfiltrate proprietary client data.

Each player is a **White Hat Operative** contracted to defend a **Client Company's** infrastructure. Operatives assemble and upgrade customized hardware and software modules (represented by a custom dice pool), process recovered secrets through a CI/CD pipeline, and adapt to the escalating cryptographic threat. The most lucrative die faces carry a **Vulnerability** icon (⚠): keeping them raises your **Vulnerability**, and SETEC's Green malware attacks the most vulnerable operatives first. As SETEC’s autonomous compiler accelerates across versions, White Hat Operatives must balance expanding their revenue streams against upgrading their **Company Terminal Mat** and defending their **Market Share** before proprietary client data leaks.

When the dust settles, any player who suffers a **Total Data Breach** (`<= 0 Secrets`) has their reputation incinerated, is raided by federal marshals, becomes **Patient Zero**, and is eliminated from contention. If any surviving player's **Market Share** falls to `0`, a **Market Collapse** makes the current round the last. Among the surviving White Hat Operatives, the player with the most **Corporate Secrets** wins; R&D faces on your dice and the **Market Leader Bonus** (by Market Share place) are the main ways to gain them (with Market Share, operational capital, ready modules, and research tokens serving as tiebreakers).

> **Note on `[TUNE]` Tags:** Numbers marked `[TUNE]` are prototype baselines verified via Monte Carlo simulation sweeps.

---

## 2. Components

### Central Threat (Project: SETEC / The Rogue Agent)
* **1 Cube Tower** (the Mainframe Decryption Compiler)
* **1 Staging Cup** (the Relay Queue showing code packets waiting for the next compilation cycle). **Its contents are public:** any player may look into the Staging Cup at any time. Cubes stuck inside the Cube Tower stay hidden.
* **Compiler Cubes (4 Colors):**
  * **Red Cubes (Market Manipulation):** Lowers your **Market Share** by `1` per cube (Red cubes cannot be blocked; no Money or Corporate Secrets are lost).
  * **Blue Cubes (Spyware / Data Exfiltration):** Steals `1` **Corporate Secret** per cube in every version (Blue cubes cannot be blocked).
  * **Green Cubes (Malware / Logic Bombs):** Hunts the most vulnerable operative. Each Green cube, one at a time, hits the surviving player(s) highest on the **Vulnerability Track** at `5` or more (all tied players are hit). Each hit player loses Corporate Secrets by band (`5–7`: `1`; `8–10`: `2`; `11+`: `3`) `[TUNE: v0.49.0]` and resets their Vulnerability to `0`. A Green cube with no player at `5` or more has no effect (see Phase 4).
  * **Black Cubes (Corrupted Code / Master Key Search):** Advances the active **Version Corruption Track** toward cryptographic Singularity.
* **Vulnerability Track** (on the Central SETEC Agent Board, numbered `0` to `15` `[TUNE: v0.46.0]`, with 1 Vulnerability marker per player): spaces `0–4` are the **safe zone** (Green never targets them) `[TUNE: v0.49.0]`; the bands `5–7`, `8–10` and `11–15` are printed with their Green damage (`−1 / −2 / −3` Secrets). Your Vulnerability rises by `1` per ⚠ on your kept dice in Phase 1 and can't go above `15` (excess is lost). It falls through the **Pen Test Track** and some `★` and R&D-face effects (never below `0`).
* **SETEC Version Deck (`v1.0`, `v2.0`, `v3.0`):** Setup cards defining the threat's starting payload (`v1.0`) and each version's bespoke **Corruption Track** (where every space triggers a game-wide hazard or injects new cubes into the compiler).

### Player & Market Components
* **4 Company Terminal Mats**, each featuring:
  * **Ready for Release Zone** (online modules staged and ready to roll at round start)
  * **In Production Area** (active deployed modules producing cash, research, Market Share and `★` outputs for the current round)
  * **Under Development Pipeline** (secret-processing conveyor):
    * **Research & Development** (dice that rolled an **R&D face**, waiting to bank their Secret)
    * **Sprint Plan** (modules waiting for release), split into the **Current Sprint** (dice that must be released first) and the **Next Sprint** (dice queued behind them)
    * **Hardware Throughput Limits** (Triage Bandwidth: Research & Development $\to$ Sprint Plan; Release Bandwidth: Sprint Plan $\to$ Ready)
  * **Central Market Share Track** (on the Central SETEC Agent Board, numbered `0` to `20` `[TUNE: v0.38e]`). Starting value is `14` at 2 players and `18` at 3 and 4 players `[TUNE: v0.46.0]` (allowing `+6` or `+2` spaces of headroom to grow up to the track maximum of `20`). In **2-player games**, a neutral **SETEC Corp Black Cube** also tracks Market Share starting at `0`. Lowered by **Red Cubes** and *Customer Poaching*; raised by Red and Yellow Market Share faces, *Brand Protection* and *Ad Campaign*, and regained with cash through the **Public Relations Track**. A surviving player at `0` triggers a **Market Collapse** (see Phase 4; SETEC Corp never triggers Market Collapse). Market Share places earn the **Market Leader Bonus** (see Phase 6 and Section 5).
  * **Terminal Hardware Tracks (4 Independent Tracks, Levels 0 $\to$ 4):** Each step costs **`1 / 2 / 2 / 3 🔬`** to reach Level 1 / 2 / 3 / 4 `[TUNE]` (`8 🔬` per track). Levels 1 and 3 of every track carry a **Breakthrough**, and so does Pen Test Level 2 `[TUNE: v0.50.0]`. Each resolves immediately when that level is reached (see Phase 5).

    | Track | Level 0 | Level 1 (Breakthrough) | Level 2 | Level 3 (Breakthrough) | Level 4 |
    | :--- | :--- | :--- | :--- | :--- | :--- |
    | **Pen Test Track** | Pen Test limit `1` per turn | Gain `1` Corporate Secret | Limit `2` + **Breakthrough:** return `1` Gray Legacy die you own to the box `[TUNE: v0.50.0]` | Return `1` Gray Legacy die you own to the box *(+Blue R&D faces yield `+3`)* `[TUNE: v0.48.0]` | Limit `3` + lower your Vulnerability by `1` for free at the start of each Operations Turn `[TUNE]` |
    | **Triage Track** | Triage Bandwidth `1` | Gain `+$2` Liquid Cash `[TUNE: v0.48.0]` | Bandwidth `2` | Gain `1` Corporate Secret | Bandwidth `2` + replace `1` Gray Legacy die with a Central Market colored die (`$0`, to Ready) |
    | **Release Track** | Release Bandwidth `4` | `+1` Release Bandwidth this round | Bandwidth `5` | Return `1` Gray Legacy die you own to the box | Bandwidth `6` + set `1` rolled Gray Legacy die to any face in Phase 1 Step 3 |
    | **Public Relations Track** | Regain up to `1` Market Share per turn at `$3` cash each `[TUNE]` | Gain `+$3` Liquid Cash | Regain up to `2` per turn `[TUNE]` | Gain your 2nd Purple die (from your Personal Reserve, to the Next Sprint) | Regain up to `3` per turn `[TUNE]` + gain `+2` Market Share immediately |

    *(A Level 1 or Level 3 Breakthrough level keeps the value of the level below it; Pen Test Level 2 raises the limit to `2` **and** carries its Breakthrough: the Public Relations limit is `1` at Levels 0–1, `2` at Levels 2–3 and `3` at Level 4, always at `$3` Cash per `+1` Market Share; the Pen Test limit is `1` at Levels 0–1, `2` at Levels 2–3 and `3` at Level 4, always at `2 🔬` per `−1` Vulnerability `[TUNE: v0.46.0]`. See Phase 5. Returning a Gray Legacy die removes it from the game from any zone of your mat; if you own none, that Breakthrough is lost.)*

  * **Personal Reserve** (1 outline space on Public Relations Track Level 3 for your 2nd Purple Proprietary Specialist die, unlocked upon reaching Level 3)
  * **Institutional Override Track (`v1.0`, `v2.0`, `v3.0`)**: 3 tracking slots on each Client Company Card (which sits alongside your mat) for once-per-version Client Company powers (DTO *Slush Fund* is once per game)
* **CI/CD Company Terminal Mat Physical Wireframe:**
*(Client Company Cards and White Hat Dossier Cards are dealt at setup and sit alongside the mat).*
```
+--------------------------------------------------------------------------------------------------------------------+
|  [LEFT COLUMN: CORPORATE HQ]         |  [MAIN COLUMN: CI/CD PIPELINE & PEN TEST]                                   |
|                                      |                                                                             |
|  +--------------------------------+  |  +-----------------------------------------------------------------------+  |
|  | CORPORATE SECRETS (VP HOLDER)  |  |  | 1. READY FOR RELEASE (Active Staging / Rolling Pool)                  |  |
|  | - Start: 6 (2-4P)              |  |  |                                                                       |  |
|  | - 1 Secret = 1 VP (Uncapped)   |  |  |  [GRAY] [GRAY] [COMP] [PURP] [ ] [ ] [ ] [ ] [ ] [ ]                   |  |
|  | - <= 0 = Total Data Breach     |  |  +-----------------------------------------------------------------------+  |
|  +--------------------------------+  |                                     ^                                       |
|                                      |                                     |  [VERTICAL RELEASE TRACK]             |
|  +--------------------------------+  |                                     |  L0: 4 dice                           |
|  | LIQUID CASH ($ HOLDER)         |  |                                     |  L1 (1 🔬): ★ +1 Release this round    |
|  | - Start: $6 (Uncapped)         |  |                                     |  L2 (2 🔬): 5 dice                     |
|  | - Software Market / ★ Actions  |  |                                     |  L3 (2 🔬): ★ Return 1 Gray die        |
|  +--------------------------------+  |                                     |  L4 (3 🔬): 6 dice + set 1 Gray face   |
|                                      |                                     |                                       |
|  +--------------------------------+  |  +-----------------------------------------------------------------------+  |
|  | RESEARCH TOKENS (🔬 HOLDER)     |  |  | 2. IN PRODUCTION (Deployed Dice)                                      |  |
|  | - Start: 0 🔬 (Uncapped)        |  |  |  +-----------------------------+  +---------------------------------+  |  |
|  | - Upgrades (1/2/2/3 🔬; <= 2/turn) |  | DEPLOYED ($ / 🔬 / MS / ★)    |  | PEN TEST TRACK (Phase 5)        |  |  |
|  +--------------------------------+  |  |  |                             |  | 2 🔬 = -1 Vulnerability         |  |  |
|                                      |  |  | Each kept ⚠ =               |  | Limit = steps per turn          |  |  |
|  +--------------------------------+  |  |  | +1 Vulnerability (Phase 1)  |  | L0: Limit 1                     |  |  |
|  | PUBLIC RELATIONS TRACK (EXPAND)|  |  |                             |  | L1 (1 🔬): ★ 1 Secret           |  |  |
|  | $3 Cash = +1 Market Share (P5)    |  |  |  |                             |  | L2 (2 🔬): Limit 2               |  |  |
|  | - L0: Regain up to 1/rnd       |  |  |  |                             |  | L3 (2 🔬): ★ -1 Gray (+Blue +1) |  |  |
|  | - L1: ★ +$3 Liquid Cash        |  |  |  |                             |  | L4 (3 🔬): Limit 3               |  |  |
|  | - L2: Regain up to 2/rnd       |  |  |  +-----------------------------+  |   + free -1 Vulnerability/turn  |  |  |
|  | - L3: ★ 2nd Purple Specialist  |  |  +-----------------------------------------------------------------------+  |
|  |   Die Reserve [DIE OUTLINE]    |  |                                                                             |
|  | - L4: Regain up to 3/rnd       |  |  +-----------------------------------------------------------------------+  |
|  +--------------------------------+  |  | 3. UNDER DEVELOPMENT (CI/CD Pipeline)                                 |  |
|                                      |  |  +-------------------+  +------------------------------------------+  |  |
|                                      |  |  | SPRINT PLAN       |  | TRIAGE TRACK (Conveyor Bandwidth)        |  |  |
|                                      |  |  | CURRENT | NEXT    |  | L0: 1 | L1 (1🔬): ★ +$2 Cash               |  |  |
|                                      |  |  |                   |  | L2 (2🔬): 2 | L3 (2🔬): ★ 1 Secret        |  |  |
|                                      |  |  | ^ Sprint Review:  |  | L4 (3🔬): 2 + Swap Gray->Colored ($0)     |  |  |
|                                      |  |  |   Current first,  |  | RESEARCH & DEVELOPMENT (FIFO Queue)      |  |  |
|                                      |  |  |   then Next (P6)  |  | <-- [OLDEST] <== FIFO FLOW <== [NEWEST]  |  |  |
|                                      |  |  |                   |  | Bank on Exit: Purple +1, Red/Blue/Grn +2 |  |  |
|                                      |  |  +-------------------+  +------------------------------------------+  |  |
|                                      |  +-----------------------------------------------------------------------+  |
+--------------------------------------+-----------------------------------------------------------------------------+
```
* **6 Client Company Cards** (Enterprise clients contracting the White Hat Operative; each grants an Institutional Override and names the color of your starting colored die — Red, Blue or Green, see Section 6D. Every company starts with the same hardware and resources):
  * **Meridian Financial Trust** (*Banking Infrastructure / Capital Injection*)
  * **Omnidyne Systems** (*Tech Giant / Magnetic Splice*)
  * **Aegis Defense Relay** (*Security Firm / Baffle Echo*)
  * **Department of Telecommunications Oversight [DTO]** (*Federal Agency / Slush Fund, once per game*)
  * **Helix Biomedical Consortium** (*Medical Research / Brute-Force Bypass, once per game*)
  * **The Prometheus Foundation** (*Non-Profit / Algorithmic Arbitrage*)
* **6 White Hat Dossier Cards** (Specialist operative leads directing technical protocols; each defines a Face 6 Signature Protocol for that player's Purple dice):
  * **The Operator** (*Tactical Staffing & Logistics Lead / Logistics Bounty*)
  * **The Phreaker** (*Hardware Intrusion Specialist / Jumper Diagnostics*)
  * **The Acoustic** (*Side-Channel Cryptanalyst / Resonance Sensor*)
  * **The Spook** (*Covert Intelligence Specialist / Burn Notice*)
  * **The Prodigy** (*Autonomous Exploit Hacker / Arbitrary Code Execution*)
  * **The Cipher** (*Distributed Ledger Architect / Algorithmic Parity*)
* **20 Gray "Legacy Code" Dice** (5 per player at setup: 2 in Ready for Release and 3 in the Current Sprint; no Gray dice are gained later, and the Pen Test Level 2 and 3 and Release Level 3 Breakthroughs return them to the box; no R&D face; two of its six faces carry ⚠) `[TUNE: v0.50.0]`
* **Colored Software Module Dice:**
  * **4 Central Market Colors (`2 × Players` dice per color; Red, Blue and Green: 4 core faces, Face 5 **R&D face**, Face 6 Star `★`; Yellow: 5 core faces and Face 6 Star `★`, no R&D face; every R&D face and one high-output core face carry ⚠ (Yellow: Faces 1 and 5), and `★` faces never do):**
    * **Red Dice** — *Marketing* (`$4–$5`, determined by face-up Variant Card)
    * **Blue Dice** — *Firewall / Data Vault* (`$4–$6`, determined by face-up Variant Card; provides a direct Corporate Secret on Face 3, cash/research outputs and choices, and hardware-synergized Secret banking on Face 5)
    * **Green Dice** — *Antivirus / Auto-Patcher* (`$4–$5`, determined by face-up Variant Card)
    * **Yellow Dice** — *Commercial AI (High Revenue / Fast Capital)* (`$5–$6`, determined by face-up Variant Card)
  * **Purple Proprietary Specialist Dice (`2` dice per player: 1 in Ready for Release, 1 in Personal Reserve):**
    * **Purple Dice** — *Proprietary Specialist / Black-Hat AI* (not purchasable; your 2nd Purple die is gained only from the Public Relations Level 3 Breakthrough, and a Purple die lost to an effect is not replaced; standardized high-reliability baseline with a Face 5 **R&D face** + bespoke White Hat Signature Protocols)
* **Software Module Variant Cards:** Multiple cards per market die color (**Red, Blue, Green, Yellow**); **1 card per color** is used each game to define that color's Special (`★`) Face 6. *(Purple dice do not use market variant cards; their Face 6 triggers the player's bespoke Signature Protocol).*
* **Player Tracking & Signature Cubes (`8` cubes per player in their player color):**
  * `4` Hardware Track Tracking Cubes (Pen Test, Triage, Release, Public Relations)
  * `1` Institutional Override Marker Cube (tracks Client Company ability usage)
  * `1` Market Share Marker Cube (tracks position on the Central Market Share Track)
  * `1` Vulnerability marker (tracks position on the Vulnerability Track)
  * `1` **Operative Signature Cube** (network handshake signature cycling through the Cube Tower)
* **Money Tokens (`$`)**, **Corporate Secret Tokens**, **Research Tokens (`🔬`)** *(uncapped; styled as magnetic tape data spools / cryptographic research notes)*, and a **First Player Marker**.

---

## 3. Setup

1. **SETEC Roadmap & Compiler Priming:** Deal **1 `v1.0` card**, **1 `v2.0` card**, and **1 `v3.0` card** face-up in a row next to the Cube Tower. Place the Version Marker on `v1.0`.
   * **Per-Version Corruption Tracks (Consistent Across All Player Counts):** Each Version card features its own escalating **Corruption Track** where every space carries a mechanical effect: **`4` spaces on `v1.0`**, **`5` spaces on `v2.0`**, and **`6` spaces on `v3.0`** (`15` total Black Cubes to Singularity across `v1.0 → v2.0 → v3.0`) `[TUNE]`.
   * **Prime the Compiler (Pre-Seed Drop):** Before populating the Staging Cup, take **`1 Red, 1 Blue, 1 Green, and 1 Black Cube`** (4 cubes total) from the supply and drop them into the empty Cube Tower. Any cubes that exit into the tray are **returned to the general supply**. Any cubes that remain stuck on the internal baffles stay inside the tower to prime the compiler for Round 1.
   * Place the starting cubes listed on the `v1.0` card into the **Staging Cup** (baseline: `2 Red, 1 Blue, 1 Green, 0 Black` on *Script Kiddie*; `1 Red, 2 Blue, 1 Green, 0 Black` on *Data Scraper*). *(The first Black Cube enters the Staging Cup during Round 1 Phase 1's Autonomous Protocol Pulse; all subsequent cube injections from SETEC come directly from Corruption Track spaces).*
2. **Software Market & Personal Reserves:** For each of the **4 Central Market Colors** (**Red, Blue, Green, Yellow**), shuffle its Variant Cards, place **1 Variant Card** face-up in the center, and stack **`2 × Players`** dice of that color on it. *(Purple dice are completely removed from the central market supply).* Place **`1` Purple Proprietary Specialist Die** onto the **Personal Reserve** slot of each player's **Company Terminal Mat**.
3. **Player Setup (Each White Hat Operative):**
   * **Client Company & White Hat Operative Assignment:** Randomly deal **1 Client Company Card** and **1 White Hat Dossier Card** to each player (drawn without replacement). Place your Company Card beside your **Company Terminal Mat** with all 3 Version slots (`v1.0`, `v2.0`, `v3.0`) toggled to **Available**. Every Client Company starts with the same hardware: all 4 tracks at **Level 0** (Pen Test limit `1`, Triage Bandwidth `1`, Release Bandwidth `4`, Public Relations: regain up to `1` Market Share per turn at `$3` cash). Place your Vulnerability marker on **`0`** on the Vulnerability Track. Total circulating Green cubes across setup and all Version cards combined are capped at `5` `[TUNE]`. Apart from the color of your starting colored die (below), Client Companies grant no starting bonuses.
   * Place **2 Gray Legacy Dice + 1 starting colored die + 1 Purple Specialist Die** into your **Ready for Release Zone** (rolls in Round 1), and **3 Gray Legacy Dice** into the **Current Sprint** of your **Sprint Plan** `[TUNE: v0.48.0]` (they must be released first in Round 1's Sprint Review). The starting colored die is the color named by your Client Company (Red: Meridian, Prometheus; Blue: DTO, Aegis; Green: Omnidyne, Helix `[TUNE]`); take it from that color's Central Market stack (it uses that color's face-up Variant Card).
   * Take **`$6` Starting Money**.
   * **Corporate Secrets & Starting Research Tokens:** Take **`6` Corporate Secrets** at **all player counts (`2`, `3`, or `4` players)** `[TUNE: v0.48.0]` (`+1` more when *Data Scraper* is the `v1.0` card; see Section 6C), and **`0 🔬` Research Tokens**.
   * **Market Share:** Place your Market Share Marker on **`14`** at **2 players**, **`18`** at **3 players**, or **`18`** at **4 players** `[TUNE: v0.46.0]`. Your maximum Market Share is the track maximum (`20`). In **2-player games only**, also place the neutral **SETEC Corp Black Cube** on **`0`** on the Central Market Share Track.
   * **Operative Signature Cube:** Place your **Operative Signature Cube** onto its cradle on your **Company Terminal Mat** (adjacent to your Research & Development box). It remains idle on your mat until queued into the Staging Cup by your first banked Secret.
4. Randomly assign the **First Player Marker** (used to resolve Operations Turn order in Phase 5: Operations).

---

## 4. Round Structure, Client Companies & White Hat Operatives

Too Many Secrets is played over a series of rounds (~7–9 rounds). Each round consists of **6 Phases**:
1. **Phase 1: Roll & Deploy** *(Simultaneous)*
2. **Phase 2: Compiler Drop & Corruption** *(Simultaneous)*
3. **Phase 3: Income** *(Simultaneous)*
4. **Phase 4: Attack Resolution** *(Simultaneous)*
5. **Phase 5: Operations** *(Clockwise Operations Turns starting with the First Player)*
6. **Phase 6: CI/CD Pipeline Shift** *(Simultaneous)*

### Client Company Institutional Overrides ("Once per Version")
Each player’s contracting Client Company provides a powerful Institutional Override that may be activated **once per SETEC Version** (`v1.0`, `v2.0`, and `v3.0`). **Exceptions:** DTO *Slush Fund* and Helix *Brute-Force Bypass* may each be activated **once per game** (using it marks the current version slot used, and later version slots cannot fire it):
* **Start-of-Round Transition Timing:** Advancing SETEC to a new version occurs at the **start of the subsequent round** during Phase 1 Step 1 (before rolling). When an active version's corruption track is filled during Phase 2, the active version remains current for the remainder of that round.
* **Preserved Override Usability:** Because the active version remains current through **Phases 3–6**, players maintain continuous access to their current version override. Players may freely activate overrides during **Phase 3: Income** (Meridian *Capital Injection*), **Phase 4: Attack Resolution** (e.g., Aegis *Baffle Echo*, DTO *Slush Fund*), **Phase 5: Operations** (Prometheus *Algorithmic Arbitrage*), or **Phase 6** Step 1 (Omnidyne *Magnetic Splice*). The new version's Institutional Override is not unlocked yet.
* **Forfeiture & Unlock:** At the start of the next round (in Phase 1 Step 1), any unspent Institutional Override from the old version is **forfeited**, and the newly active version's Institutional Override slot unlocks to **Available**.

---

### Phase 1: Roll & Deploy (Simultaneous)

1. **Autonomous Protocol Pulse & Version Switch:**
   * **Version Switch Execution:** If SETEC's corruption track reached capacity in the previous round, execute the version transition now: forfeit any unspent old version override, unlock the new version override to Available, and initialize the new corruption track (carrying over any spilled-over Black cubes).
   * **Pulse:** SETEC compiles new intrusion subroutines in the background. Take **`1 Black Cube`** from the general supply across all versions (`v1.0`, `v2.0`, `v3.0`) and place it into the **Staging Cup** `[TUNE: v0.21.0 9-round pacing clock]`.
2. **Roll Ready Pool:** Every player simultaneously rolls all dice in their **Ready for Release Zone**. *(Dice in your **Under Development** zone are offline and are not rolled.)*
3. **Yahtzee Rerolls (Simultaneous Pure Rerolls):**
   * Each player may perform up to **`2` free rerolls** of any subset of their rolled dice (3 rolls total).
   * Between rerolls, players may set aside (keep) any dice, or pick previously kept dice back up for subsequent rerolls.
   * **Vulnerability (⚠):** Faces marked ⚠ pay well but raise your Vulnerability (see Step 4).
   * **⚠ faces lock:** Any die that shows a ⚠ face after any roll is **locked**: set it aside; it can't be rerolled this phase `[TUNE: v0.49.0]`. This includes colored dice on their ⚠ core face, **R&D faces** (Face 5 on Red, Blue, Green and Purple dice, which always carry ⚠), and Gray Legacy dice on either ⚠ face (`+$2 / +2 🔬` or `+2 🔬`) `[TUNE: v0.50.0]`. Every ⚠ face is printed on **Face 1 or Face 5** `[TUNE: v0.49.1]`, so a rolled `1` or `5` is a ⚠ at a glance. Every reroll of a clean die risks locking it on a ⚠ face; that is your main risk decision each round, sharpest when you are just below a Vulnerability band. The Staging Cup is public, so you can see how many Green cubes may drop.
   * Locked dice still produce their output: locking never costs you income. *Arbitrary Code Execution*, *Brute-Force Bypass* and Release Track Level 4 may still change a locked die's face, and ⚠ is counted on the final face.
   * **Post-Reroll Die-Face Overrides (in strict order):**
     1. *(Signature Protocol Timing: Each Face 6 `Purple ★` die triggers **The Prodigy's** Arbitrary Code Execution to turn `1` other rolled die in your active pool to any legal non-Star face of its color other than the R&D face).*
     2. *(Institutional Override Timing: Contracting **Helix Biomedical Consortium** may trigger Brute-Force Bypass, **once per game**, at any point during this phase's rerolls: for the rest of this phase you may reroll **locked** dice, and after rerolls you turn `1` rolled die to any legal non-Star face of its color, including the R&D face `[TUNE: v0.49.0]`).*
     3. **Release Track Level 4:** After any rerolls and overrides above, if you have at least `1` rolled **Gray Legacy die**, you may set `1` rolled Gray Legacy die to any printed face of its die (`+$2 / +2 🔬` ⚠, `+2 🔬`, `+$1 & +1 🔬`, `+$1 / +1 🔬`, `+$1`, or `+1 🔬`). This can turn a ⚠ face into a clean face, or the reverse. If you rolled `0` Gray Legacy dice, this effect does not apply this round.
4. **Deploy Dice (Simultaneous):**
   * After all rerolls and overrides are finished, resolve all rolled dice (all locks end now):
     * **Gain Vulnerability:** Count the ⚠ icons on the final faces of all your rolled dice, including R&D faces. Move your Vulnerability marker up `1` space per ⚠ (not above `15`; excess is lost). Vulnerability gained now stays even if the die later leaves In Production (Corruption returns, *Burn Notice*, Signature Attacks).
     * **R&D Faces $\to$ Research & Development:** Any die showing an **R&D face** moves **immediately** to the **Research & Development** box in your **Under Development** pipeline and produces no other output. It banks its Secret when it leaves Research & Development (see Phase 6 and *R&D Face Yields* below).
     * **In Production:** Place all remaining rolled dice into your **In Production** area. They produce their outputs in Phase 3: Income.
     * **Choice Faces (`/`):** If a die shows a choice (e.g. `+1 Market Share / +$1`), the player commits it now to one option. A ⚠ on a choice face counts whichever option you choose.

---

### Phase 2: Compiler Drop & Corruption (Simultaneous)

Take **all cubes** from the **Staging Cup** and drop them into the **Cube Tower** together. Cubes that remain stuck on the baffles stay inside the tower for future rounds. Group all cubes that exit into the tray by color. **Black Cubes resolve now**; exited **Attack Cubes** (`Red`, `Blue`, `Green`) stay in the **Exit Tray** and resolve in **Phase 4: Attack Resolution** (after Phase 3: Income).

#### Resolve Black (Corruption) Cubes, Track Spaces & Version Upgrades
Move exited **Black Cubes** from the tray onto the next empty space(s) of the active Version's **Corruption Track** one at a time from left to right. **Every space covered by a Black Cube immediately triggers its printed effect** (see Section 6C). Corruption resolves **before** Phase 3: Income, so cash losses land on your pre-income Money and income is then collected on top:
* **Corruption Space Effects & Deterministic Targeting:**
  * **Add Cubes (`+X Red/Blue/Green/Black`):** Take the specified cubes from the general supply and place into the **Staging Cup** (Mode A — Next Round Priming baseline `[TUNE]`).
  * **Player with Most [Resource] Loses X:** The player holding the highest amount of the specified resource (Money, Research Tokens, Market Share, Colored Module Dice, or Corporate Secrets) suffers the printed loss. If multiple players tie for Most, **all tied players suffer the printed loss simultaneously** (`INV-TARGET-02`). Unpaid cash or research losses do not drain secondary resources (minimum `$0` / `0 🔬`).
  * **Player with Lowest Vulnerability Gains `+X` Vulnerability:** The surviving player(s) with the lowest Vulnerability move their Vulnerability marker up `X` spaces (`+2` on Standard spaces, `+3` on Aggressive spaces `[TUNE: v0.46.0]`; not above `15`). If tied, all tied players gain it. It lands before Phase 4, so it can draw a Green hit this round.
  * **Player with Most Colored Module Dice Returns `X` Dice:** The player(s) with the most Colored Module Dice across their mat must return up to `X` Colored Module Dice of their choice to the Market supply. *(Gray starter dice cannot be returned).* A returned die in **Research & Development** loses its Secret. If tied, all tied players return `X` dice.
  * **Robin Hood Transfers ("Least Takes from Most"):** The player with the *least* of the specified resource takes the printed amount from the player with the *most* (`$1` Cash or `1 🔬` Research). If multiple players tie for Most, the receiving player chooses which tied leader to take from. If all players across the table are tied at an identical value, the transfer **fizzles** (no transfer occurs; `INV-TARGET-04`). Net table drain is `$0`.
  * **Lose Corporate Secrets:** Directly reduces Corporate Secrets (checking for Patient Zero at `<= 0` Secrets).
* **Version Advance & Track Spillover (`v1.0 → v2.0` or `v2.0 → v3.0`):** When the final space of `v1.0` (`4th` space) or `v2.0` (`5th` space) is filled and resolved:
  1. The final space's printed effect executes immediately (including any **Total Data Breach** it causes).
  2. Any excess Black cubes dropped in the same compile step **immediately spill over** onto the next Version's Corruption Track (starting at Space 1), triggering each newly covered space's printed effect in sequence.
  3. The **active version card remains the current version** for the remainder of the current round.
  4. The current version's Institutional Override **remains usable** through **Phases 3–6**. The upcoming version's Institutional Override is not unlocked yet.
  5. At the **start of the subsequent round** (in Phase 1 Step 1), the version transition officially takes effect: unspent overrides from the old version are forfeited, and the new version's override unlocks to Available.
  6. There is no Market Share comparison for Money when a version fills (removed in v0.38.0).
* **Singularity (`v3.0` Track Fills):** When the final (`6th`) space of `v3.0` is covered by a Black cube, resolve that space's printed effect (e.g., *Corrupted Kernel* `Lose 1 Secret`), and **Singularity is triggered—the game ends IMMEDIATELY at the end of Phase 2!** **Phases 3–6 are skipped** (no income is collected and no Secrets leave Research & Development); all surviving dice in **In Production** return to **Ready for Release**, and players proceed directly to **Section 5: End Game & Victory Scoring** (the game-end **Market Leader Bonus** is awarded).

#### Compile Buffer Overflow (Empty Tray)
If **`0 cubes of any color`** exit the tower into the tray this phase:
* No corruption advances and **no attacks occur this round** (Phase 4 resolves no damage). **Income is still collected in Phase 3.**
* The compiler's idle cycle triggers an overflow: take **`1 Red, 1 Blue, and 1 Green Cube`** from the supply and place them into the **Staging Cup** for next round's compile (in addition to the standard Phase 1 Black Cube).

#### Operative Signature Cubes & Target Lock Trigger
If any **Operative Signature Cubes** exit into the tray during Phase 2:
* Each player whose Signature Cube exited triggers **Target Lock** for this round (see Phase 4).
* Return the exited Signature Cube from the tray immediately to its idle cradle on the owner's **Company Terminal Mat**.
* Any Signature Cubes that remain stuck on the internal baffles stay inside the Cube Tower for future rounds, building latent threat until knocked loose.

#### End Game Trigger Check (End of Phase 2)
* **Singularity** ends the game at the end of Phase 2 (see above), so a **Market Collapse** cannot also be checked that round.
* If **all** players suffered a **Total Data Breach** (`<= 0 Secrets`) from Corruption Track effects, the game ends immediately as a **Total Wipeout** (Phases 3–6 are skipped).
* If **one or more (but not all)** players suffered a **Total Data Breach**, each of them becomes **Patient Zero**, is eliminated, and **skips Phases 3–6**. The current round becomes the **Final Round**: all surviving players **complete every remaining phase** (Phase 3: Income, Phase 4: Attack Resolution, Phase 5: Operations, Phase 6: CI/CD Pipeline Shift) before game scoring.

---

### Phase 3: Income (Simultaneous)

Every surviving player simultaneously collects all **`$` Money tokens**, **Research Tokens (`🔬`)**, **Corporate Secrets** (Blue Face 3), and immediate `★` outputs from **every die still In Production**. *(Dice that went to Research & Development or the Sprint Plan in Phase 1, or were returned by Corruption Track effects in Phase 2, are no longer In Production and produce 0 outputs).*
* *(Institutional Override Timing: Contracting **Meridian Financial Trust** may trigger Capital Injection here to gain an immediate **`+$3` cash payout** from the bank `[TUNE]`).*
* **Market Share faces resolve here:** Red Face 1 (`+1 Market Share` option) and Yellow Market Share faces raise your Market Share now. They cannot raise it above the track maximum (`20`) and do not count toward your Public Relations limit.
* **Star outputs resolved here:** All Colored Die `★` abilities resolve in Phase 3: *R1 Brand Protection* (`+$2 & +1 Market Share`), *R2 Ad Campaign* (pay `$2` → `+2 Market Share`), *B1 Honeypot Telemetry* (`+2 🔬` if `0` Blue in Exit Tray, or `+$3` if `1+` Blue in Exit Tray), *B2 Deep Data Vault* (`+$2`, or spend `1` Secret → `+3 Market Share`; if spending a Secret drops you to `0` Secrets, you immediately suffer a **Total Data Breach** and become **Patient Zero**), *B3 Air-Gapped Backup* (`+$2` and lower your Vulnerability by `1`), *G1 Self-Healing Kernel* (lower your Vulnerability by `2` and `+1 🔬`), *G2 Universal Sandbox* (`+1 🔬`, plus `+1 🔬` per Green cube in the Exit Tray, max `+3`), *G3 Live Reboot* (`+1 🔬 & +$1`, and move `1` die from either sprint of your Sprint Plan to Ready for Release), *Y1 Algorithmic Trading* (`+$4`, or pay `$2` → `+1 Secret`), *Y2 Cloud Monopoly* (`+$2`, plus `+$1` per different Central Market color owned, max `+$6`), and *Y3 Proprietary Training* (`+1 Secret`, plus `+$1` per Gray Legacy die owned).
* **Customer Poaching (after all players' Income):** Once every player has collected Income, resolve each *R3 Customer Poaching* die still In Production, going clockwise from the **First Player** (one die at a time if a player has several):
  * Take **`1` Market Share** from the rival with the **most Market Share** (not Patient Zero, and above `0`). If several rivals are tied for the most, you choose among them. If no rival has Market Share above `0`, nothing happens.
  * That rival loses `1` Market Share and you gain `1`. Your Market Share cannot go above the track maximum (`20`): if you are already at `20`, the rival still loses `1` and you gain nothing.
  * Re-check which rival has the most Market Share before each Customer Poaching die. A rival taken to `0` causes a **Market Collapse** at the end of Phase 4.
* *(Signature Protocol Timing: each Face 6 `Purple ★` die **still In Production** triggers its Signature Protocol once — **The Operator's** Logistics Bounty [+1 🔬 Research Token per different color die currently in your Sprint Plan (both sprints), including Gray, Purple, and Yellow], **The Phreaker's** Jumper Diagnostics [+$1 cash and +1 Release Bandwidth this round, applying in Phase 6 Step 3], **The Acoustic's** Resonance Sensor [+$1 cash per unique colored cube that exited the Cube Tower this round, including Operative Signature Cubes, up to +$5 max], **The Spook's** Burn Notice [+$2 cash, plus optionally permanently return 1 owned Gray Legacy die to the box for +$3 cash], or **The Cipher's** Algorithmic Parity [+$2 cash & +1 🔬 Research Token]. Two `Purple ★` dice trigger the protocol twice; Burn Notice may not target the same Gray die twice. A `Purple ★` die that left In Production in Phase 2 triggers nothing. A Gray die returned by Burn Notice produces nothing more, and Vulnerability it already gave you stays).*

---

### Phase 4: Attack Resolution (Simultaneous)

Calculate the total attack strength of **Red**, **Blue**, and **Green** from exited cubes in the tray. **No cube can be blocked.** A player who became **Patient Zero** in Phase 2 or Phase 3 is not attacked. Resolve in this order:

1. **Red & Blue (each surviving player, simultaneously):**
   * **Red (Market Manipulation):** Lower your **Market Share** by **`1`** per exited Red cube (Market Share cannot drop below `0`; any excess has no further effect). Red cubes never cost Money or Corporate Secrets.
   * **Blue (Spyware / Data Exfiltration):** Lose **`1` Corporate Secret** per exited Blue cube, in every version.
   * *(Institutional Override Timing: Contracting **Department of Telecommunications Oversight [DTO]** may trigger Slush Fund here to absorb up to 2 Corporate Secret loss from Blue cubes for free; **once per game**, and you choose whether to use it when it would apply).*
   * *(Institutional Override Timing: Defending **Aegis Defense Relay** may trigger Baffle Echo here to ignore `1` exited Red or Blue cube for themselves this round, or save it for a Green hit in Step 2).*
2. **Green (whole table, one cube at a time):** For each exited Green cube in turn:
   * Find the surviving player(s) with the **highest Vulnerability**, counting only players at **`5` or more**. Every player tied for highest is hit.
   * Each hit player loses Corporate Secrets by their band: **`5–7`: `1`**, **`8–10`: `2`**, **`11+`: `3`** `[TUNE: v0.49.0]`. Then they **reset their Vulnerability to `0`**.
   * The next Green cube checks again from the new positions, so a second cube usually hits a different player.
   * If no surviving player is at `5` or more, the cube has no effect (players in the safe zone `0–4` are never hit). It still recycles in Step 5.
   * A player taken to `0` Secrets by Blue this phase can still be hit by Green.
   * *(Institutional Override Timing: **Aegis Defense Relay** may use Baffle Echo, if still unused this version, to cancel the Secret loss of `1` Green hit. Their Vulnerability still resets to `0`).*
3. **Patient Zero Check:** If your Corporate Secrets are now **`0` (or below)**, you suffer a **Total Data Breach** and become **Patient Zero**.
4. **Target Lock:** Resolve any **Target Lock** Signature Attacks (see below).
5. **Snowball Recycle & SETEC Corp (2-Player Only):** Place **all exited Red, Blue, and Green cubes** from the tray back into the **Staging Cup** for next round, including Green cubes that hit no one. In **2-player games**, if **any Red cubes (`>= 1`) exited the Cube Tower tray** this round, move the neutral **SETEC Corp Black Cube** up **`+1` Market Share** (capped at `20`).
6. **Compile Buffer Overflow:** If the tray was empty in Phase 2, no damage resolves this phase (no Green hits, no Baffle Echo and no damage-conditional `★` bonuses), and every Vulnerability carries over unchanged. The End Game Trigger Check (including **Market Collapse**, since *Customer Poaching* may have lowered Market Share in Phase 3) still occurs.

#### Target Lock Signature Attack Resolution
If you triggered a **Target Lock** in Phase 2 (and are not **Patient Zero**), after Red, Blue and Green damage and the Patient Zero check have resolved, you suffer the **Signature Attack** matching the **most populous Compiler Cube color** (`Green`, `Black`, `Blue`, or `Red`) that exited into the tray in Phase 2 (`INV-SIG-01`):
* **Tie-Breaking Priority Order (Central Board Top-to-Bottom):** If multiple colors tie for the highest exited cube count in the tray, resolve the highest-priority tied color in the order **`Green > Black > Blue > Red`** `[TUNE: v0.43.0]`.
* **Buffer Overflow (Empty Tray):** If `0` total cubes exited in Phase 2, Target Lock **fizzles cleanly** with no effect (`INV-SIG-02`).
* **The 4 Dominant Color Signature Attacks (Printed on Central Board):**
  * **Green (Malware Encryption):** Place a green cube from the general supply onto the next space of **`2` different Research Tracks** that do not already have a green cube (and are below Level 4; you choose which eligible tracks). **A space holding a green cube costs double Research (`2× 🔬`) to advance into**; when researched, return the green cube to the general supply (never to the Staging Cup). The Pen Test Track is an eligible track. For each green cube that cannot be placed (because fewer than 2 tracks are eligible), **gain `+2` Vulnerability** `[TUNE: v0.46.0]` instead (`INV-SIG-GREEN`); it can only draw a Green hit from next round.
  * **Black (Root Override Hijack):** Mark your Client Company's **Institutional Override** as **`Used`** for the current SETEC Version (for **DTO** *Slush Fund*, mark it used for the game). If your Institutional Override is already used, lose **`2` Corporate Secrets** instead (`INV-SIG-BLACK`). **Helix** *Brute-Force Bypass* can't be marked Used this way: if it is unused, Root Override Hijack has no effect on Helix `[TUNE: v0.49.0]`.
  * **Blue (Buffer Congestion):** Move **`1` Gray Legacy die** from your **Sprint Plan** (either sprint, your choice; or **In Production** if your Sprint Plan has no Gray die; or **Ready for Release** if neither has one) to the back of your **Research & Development** queue (it enters the **Next Sprint** when it leaves). When a Gray Legacy die leaves Research & Development (via Conveyor Triage or *Magnetic Splice*), it yields **`0` Corporate Secrets** and does **not** queue your Operative Signature Cube into the Staging Cup (`INV-SIG-BLUE`).
  * **Red (Market Manipulation):** You lose **`2` Market Share** (not below `0`), and the **surviving rival with the least Market Share gains `2` Market Share** (not above the track maximum of `20`). Rivals who also triggered Target Lock this round are eligible. In **2-player games**, the **SETEC Corp Black Cube** also counts as a possible recipient. If several eligible recipients tie for the least Market Share, you choose which one gains `2`. If multiple players resolve a Red Signature Attack in the same round, all Target-Locked players lose `2` Market Share simultaneously first; then each Target-Locked player's lowest rival is read from those new values, and all `+2` gains are applied together (gains to the same recipient add up before the cap). A Patient Zero never gains. If you have no surviving rival (and there is no SETEC Corp), no one gains Market Share `[TUNE: v0.47.0]` (`INV-SIG-RED`, `INV-SIMUL-RED`).
* Target Lock status then clears before the End Game Trigger Check. Corporate Secrets lost to a Target Lock are checked for **Patient Zero** at the End Game Trigger Check.

#### End Game Trigger Check (End of Phase 4)
* If **all** players are now **Patient Zero** (including any Patient Zero from Phase 2), the game ends immediately as a **Total Wipeout**; Phases 5–6 are skipped and Market Collapse is not checked.
* If **one or more (but not all)** players are **Patient Zero**, the current round is the **Final Round**: each Patient Zero is eliminated, and all surviving players **complete Phase 5 and Phase 6** before game scoring.
* **Market Collapse:** Then, if any surviving player has **`0` Market Share**, the current round becomes the **Final Round** (if it is not already). **No one is eliminated and there is no other penalty**: every surviving player, including any at `0`, completes Phase 5 and Phase 6 before game scoring. Regaining Market Share in Phase 5 does not cancel the Final Round.
  * If a player also became **Patient Zero** this round (in Phase 2 or Phase 4), the Patient Zero rules above apply as well: each breached player is eliminated, and the round is the Final Round either way.

---

### Phase 5: Operations (Operations Turns, Clockwise)

Surviving White Hat Operatives take clockwise **Operations Turns** starting with the **First Player**. On your turn, perform any of the following operations in any order:
1. **Terminal Hardware Track Upgrades (Limit `2` upgrades per turn `[TUNE]`):**
   * Spend Research Tokens (`🔬`) to raise any of your 4 tracks one level at a time: **`1 🔬`** to reach Level 1, **`2 🔬`** for Level 2, **`2 🔬`** for Level 3, **`3 🔬`** for Level 4 `[TUNE]` (no discounts; limit 2 hardware upgrades per turn `[TUNE]`, across all tracks combined). If the space you are advancing into holds a green cube (from a **Green Signature Attack**), that step costs **double Research (`2× 🔬`: `2 / 4 / 4 / 6 🔬`)** and clears the green cube back to the general supply. See the track table in Section 2.
   * **Breakthroughs (Levels 1 and 3, plus Pen Test Level 2):** When a track reaches a Breakthrough level, its **Breakthrough** resolves **immediately**, before your next operation. If you execute 2 upgrades in one turn, resolve them one level at a time, in the order you buy them (e.g. `$3` from the Public Relations Level 1 Breakthrough can pay for a Triage Level 3 Breakthrough bought afterwards, or fund dice purchases in the same turn). Each Breakthrough happens only once, the first time you reach that level.
     * **Level 1 Breakthroughs** `[TUNE: v0.48.0]`: **Pen Test** gain `1` Corporate Secret; **Triage** gain `+$2` Liquid Cash; **Release** gain `+1` Release Bandwidth for this round's Sprint Review (like *Jumper Diagnostics*); **Public Relations** gain `+$3` Liquid Cash.
     * **Pen Test Level 2, Pen Test Level 3 and Release Level 3 Breakthroughs (Gray thinning)** `[TUNE: v0.50.0]`: Return `1` Gray Legacy die you own (from your Ready for Release Zone, Sprint Plan or Research & Development) to the box. It leaves the game and banks nothing. If you own no Gray Legacy die, the Breakthrough is lost. *(Pen Test Level 3+ still adds `+1` to Blue R&D face yields.)*
     * **Public Relations Level 3 Breakthrough:** Move the 2nd Purple die from your Personal Reserve to the **Next Sprint** of your **Sprint Plan** (it is released at a later Sprint Review, gated by Release Bandwidth).
     * **Triage Level 4 Capstone (optional):** Return `1` Gray Legacy die you own (from your Ready for Release Zone, Sprint Plan, or Research & Development) to the box for **`$0` (free)** and take `1` die of any Central Market color with stock left (it uses that color's active Variant Card). The new die goes to your **Ready for Release Zone**. This is not a purchase (it does not count toward your dice purchase limit). If you own no Gray Legacy die, every Central Market stack is empty, or you decline, the replacement is forfeited.
     * **Public Relations Level 4 Capstone:** Immediately gain **`+2` Market Share** (clamped at the track maximum of `20`, without paying cash or consuming your per-turn regain limit).
     * **Pen Test Level 4 Capstone:** Your Pen Test limit becomes `3`, and from your next Operations Turn on you lower your Vulnerability by `1` for free at the start of each Operations Turn (not below `0`; it does not count toward your Pen Test limit).
   * A Pen Test limit bought earlier in the turn applies to later Pen Tests that turn; Triage and Release Bandwidth apply immediately in Phase 6 of the same round; other Level 4 effects apply from the next phase in which they are used.
2. **Regain Market Share (Public Relations Track):**
   * Spend **`$3` Cash** `[TUNE]` for each **`+1` Market Share**, up to your current Public Relations limit this turn: **`1`** at Levels 0–1, **`2`** at Levels 2–3, **`3`** at Level 4 `[TUNE]`. A level bought earlier in the same turn applies to later regains. Market Share regain is an operational resource conversion, not a hardware track upgrade, and does not count toward or consume your limit of 2 hardware upgrades per turn.
   * Market Share can never exceed the track maximum (`20`); you cannot spend cash while at the track maximum.
   * You may regain Market Share during the Final Round (final Market Share sets your game-end **Market Leader Bonus** place and is the first tiebreaker), but doing so does not cancel a Final Round already triggered.
3. **Pen Test (Pen Test Track):**
   * Spend **`2 🔬`** `[TUNE: v0.46.0]` for each **`−1` Vulnerability**, up to your current Pen Test limit this turn: **`1`** at Levels 0–1, **`2`** at Levels 2–3, **`3`** at Level 4 `[TUNE]`. Your Vulnerability can't go below `0`.
   * A Pen Test is a resource conversion, not a hardware track upgrade: it does not count toward your limit of 2 hardware upgrades per turn.
   * Vulnerability you remove now is safe from next round's Green cubes; the ⚠ faces you keep in Phase 1 raise it again.
4. **Purchase Software Module Dice (Limit `1` die per turn `[TUNE]`):**
   * **Central Market:** Pay the `$` cost of any available Colored Die (**Red, Blue, Green, Yellow**) as printed on its active face-up **Variant Card** (`$4`–`$6`) and place it into the **Next Sprint** of your **Sprint Plan** in Under Development (it must pass through a Sprint Review in Phase 6, gated by your Release Bandwidth, before entering your active rolling pool).
   * Purple Proprietary Specialist dice cannot be purchased.
   * *(Institutional Override Timing: Contracting **The Prometheus Foundation** may trigger Algorithmic Arbitrage here to purchase 1 Colored Die from the Central Market at a **$2 discount** [min $0], or gain **+$2 cash**).*
5. **Uncapped Research Storage:** Research tokens (`🔬`) have **no storage cap**! Retain all unspent Research tokens in your supply for future rounds.

After all surviving players complete their Operations Turns, proceed directly to **Phase 6: CI/CD Pipeline Shift**.

---

---

### Phase 6: CI/CD Pipeline Shift (Simultaneous)

All surviving players simultaneously update their terminal pipeline in this order:
1. **Magnetic Splice:** *(Institutional Override Timing: Contracting **Omnidyne Systems** may trigger Magnetic Splice here to move 1 die of your choice from your Research & Development directly to Ready for Release for free; it banks its Secret now).*
2. **Production Return:** Move **all surviving dice** from **In Production** to your **Sprint Plan**: into the **Current Sprint** if it is empty, otherwise into the **Next Sprint** `[TUNE: v0.48.0]`.
3. **Sprint Review (Hardware Throughput Limit):** Your Release Bandwidth this round is **`release_bandwidth`** (`4` baseline, upgradable to `5` and `6`, plus any temporary bonus from *Jumper Diagnostics* or the Release Level 1 Breakthrough this round).
   * **Full throughput:** You **must** move dice from the Sprint Plan to your **Ready for Release Zone** until you reach your Release Bandwidth or the Sprint Plan is empty. You may not release fewer.
   * **Current Sprint first:** Take those dice from the **Current Sprint** until it is empty. If the Current Sprint holds more dice than your Release Bandwidth, you choose which ones move.
   * **Then the Next Sprint:** Fill any Release Bandwidth left with dice of your choice from the **Next Sprint**.
   * **End of the Sprint Review:** Every die left in the Sprint Plan (in either sprint) becomes the new **Current Sprint**. *(Whatever you hold back this round must be released first next round.)*
   * **New arrivals:** Dice that leave Research & Development (Step 4), newly purchased dice, the Public Relations Level 3 Purple die and any other die placed into the Sprint Plan go to the **Next Sprint**. Effects that take a die from the Sprint Plan (*G3 Live Reboot*, the Triage Level 4 Capstone, the Blue Signature Attack) may take it from either sprint.
4. **Conveyor Triage (Hardware Throughput Limit):** Move up to **`triage_bandwidth` dice** (`1` baseline at Levels 0–1, upgradable to `2` at Level 2+) from **Research & Development** into the **Next Sprint**, **oldest first**: dice leave in the order they entered Research & Development (any color; dice that entered together leave in roll order). You do not choose. Each die banks its Secret as it moves (see *R&D Face Yields*). When a **Green** die leaves Research & Development and banks its Secret, you also lower your Vulnerability by `2`. *(Dice triaged now enter the Next Sprint and may be released in a later round's Sprint Review.)*
   * **Hardware Throughput Limits:** Throughput is strictly governed by your Triage and Release hardware bandwidths; excess dice remain in Research & Development (keeping their Secret for a later round), and dice not released remain in the Sprint Plan.
   * **Operative Signature Cube Staging:** When at least `1` die moves from your Research & Development to your Sprint Plan and banks its Secret: if your **Operative Signature Cube** is currently resting on your Company Terminal Mat, move it to the **Staging Cup** to be compiled in next round's Phase 2 drop (`INV-TL-03`). Triaging multiple dice in the same turn moves the cube once. If your Signature Cube is already in the Staging Cup or trapped on the internal baffles inside the Cube Tower, banking additional secrets does not add another cube (exactly 1 Signature Cube per player exists).
5. **Market Leader Bonus (end of Phase 6):** If at least `1` R&D face on a **Red** die was banked this round (by any player, in Phase 3 or Phase 6 Conveyor Triage), award the **Market Leader Bonus** once evaluating final Market Share positions from Phase 5 (see below). Several Red R&D faces in one round still give one award.

#### R&D Face Yields `[TUNE]`
A die showing an **R&D face** banks its Secret when it leaves **Research & Development** (Conveyor Triage or *Magnetic Splice*): its owner gains **Corporate Secrets** by the die's color, using the game state at that moment:
* **Red:** `+2`.
* **Blue:** `+2`, plus `1` if your Pen Test Track is at Level 3 or higher (maximum `+3`).
* **Green:** `+2`; then lower your Vulnerability by `2` `[TUNE: v0.46.0]` (not below `0`).
* **Purple:** `+1`.
* **Gray (placed via Blue Signature Attack):** `0` (does not queue your Operative Signature Cube into the Staging Cup).

A die returned to the supply from Research & Development, or still in Research & Development when the game ends, banks nothing.

#### Market Leader Bonus
Place every player who is not **Patient Zero** (plus **SETEC Corp** in **2-player games**) by their **Market Share** at that moment (highest first). Each gains **Corporate Secrets** by place `[TUNE: v0.38.0]`: **1st `+3`, 2nd `+1`, other places `0`** at every player count. Tied participants share the better place and each gain its award (e.g., two tied for 1st both gain `+3`; the next is 3rd). In 2-player games, **SETEC Corp** can take 1st or 2nd place and deny that bonus to human players (SETEC Corp itself scores no VP). Patient Zeros gain nothing and take no place; a sole survivor (plus SETEC Corp in 2P) ranks normally; a player at `0` Market Share is placed like anyone else. It is awarded at the end of Phase 6 in any round with a Red R&D face banked (including the Final Round) and once more at game end (Section 5).

---

After Phase 6: if this was the **Final Round**, proceed directly to **Section 5: End Game & Victory Scoring**. Otherwise, **pass the First Player Marker** clockwise and begin the next round.


---

## 5. End Game & Victory Scoring

### Determining the Winner
When the game ends (via Singularity when `v3.0` fills, at the end of the **Final Round** triggered by **Patient Zero** or **Market Collapse**, or via **Total Wipeout**):

* **Standard Ending (1+ White Hat Operatives Survive):**
  * Any player who suffered a **Total Data Breach** (`<= 0 Secrets`) is **eliminated** as Patient Zero and cannot win.
  * **Research & Development at game end:** Dice still in your **Research & Development** bank nothing (their Secrets are lost).
  * **Market Leader Bonus (game end):** First, award the **Market Leader Bonus** once more by final **Market Share** (see Phase 6): 1st `+3`, 2nd `+1`, other places `0` `[TUNE: v0.38.0]` at every player count. It is awarded on every ending except a **Total Wipeout** (Singularity, Patient Zero and Market Collapse endings all award it), in addition to any award at the end of the last round's Phase 6.
    * Tied players share the better place and each gain its award (e.g., two players tied for 1st both gain `+3`; the next player is 3rd). There is no further tiebreak for the bonus.
    * Patient Zeros gain nothing and take no place; survivors below them move up. A sole survivor takes 1st.
  * Surviving White Hat Operatives then compare their **Corporate Secrets**. **Corporate Secrets are the sole source of victory points (`1 Secret = 1 Point`)**; Market Share scores only through the Market Leader Bonus, and Money, Research tokens, and Software Module dice score `0 VP`. The surviving White Hat Operative with the **most Corporate Secrets wins!**
  * **Hierarchical Tiebreakers:** If surviving players are tied for Corporate Secrets, break ties using the following hierarchy:
    1. **Market Position:** Most final **Market Share**.
    2. **Operational Capital:** Most remaining **Money (`$`)**.
    3. **Active Infrastructure:** Most **Active Colored Module Dice** in your **Ready for Release Zone** (Gray starter dice do not count).
    4. **Hardware Readiness:** Most remaining **Research Tokens (`🔬`)**.
    5. **Reliability:** Fewest total dice in **Under Development** (Research & Development + Sprint Plan).
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
