# Too Many Secrets — Rules Draft (v0.17.0)

**Players:** 2–4 | **Playtime:** ~45–60 min | **Weight:** Medium Euro / Dice-Pool Survival  
**Aesthetic:** Tape-Punk / Lo-Fi Cryptography (Early 1990s ARPANET relays, monochrome CRT terminals, reel-to-reel magnetic tape, acoustic couplers)

---

## 1. Theme & Overview

A mysterious autonomous cracking program—codenamed **Project: SETEC** (the "Rogue Agent")—has broken loose across telecommunications relays and university mainframes. Recompiling its malicious subroutines each round through an acoustic mainframe compiler, SETEC aggressively probes commercial networks to extort funds, corrupt system hardware, and exfiltrate proprietary client data.

Each player directs an **independent boutique white-hat security consultancy** hired to defend client infrastructure. Consultancies assemble and upgrade customized hardware and software modules (represented by a custom dice pool), patch degraded relays, and adapt to the escalating cryptographic threat. As SETEC’s autonomous compiler accelerates across versions, consultancies must balance expanding their revenue streams against patching critical relays before proprietary client data leaks.

When the dust settles, any consultancy that suffers a **Total Data Breach** (`<= 0 Secrets`) has its reputation incinerated, is raided by federal marshals, becomes **Patient Zero**, and is eliminated from contention. Among the surviving firms, the consultancy with the most **Corporate Secrets** wins (with operational capital, ready modules, and patches serving as tiebreakers).

> **Note on `[TUNE]` Tags:** Numbers marked `[TUNE]` are prototype baselines verified via Monte Carlo simulation sweeps.

---

## 2. Components

### Central Threat (Project: SETEC / The Rogue Agent)
* **1 Cube Tower** (the Mainframe Decryption Compiler)
* **1 Staging Cup** (the Relay Queue showing code packets waiting for the next compilation cycle)
* **Compiler Cubes (4 Colors):**
  * **Red Cubes (Ransomware / Financial Wiretaps):** Extorts firm **Money**; unpaid ransom can be absorbed by **Splice/Patch Tokens (`🔧`)** or leaks **Corporate Secrets**.
  * **Blue Cubes (Spyware / Data Exfiltration):** Directly steals **Corporate Secrets**.
  * **Green Cubes (Malware / Logic Bombs):** Degrades Ready dice to **Unpatched** (or destroys dice if overwhelmed).
  * **Black Cubes (Corrupted Code / Master Key Search):** Advances the active **Version Corruption Track** toward cryptographic Singularity.
* **SETEC Version Deck (`v1.0`, `v2.0`, `v3.0`):** Setup cards defining the threat's starting payload (`v1.0`) and each version's bespoke **Corruption Track** (where every space triggers a game-wide hazard or injects new cubes into the compiler).

### Player & Market Components
* **4 Consultancy Terminal Mats**, each featuring:
  * **Ready Zone** (online modules ready to roll at round start)
  * **Active Pool (Rolled Area)** (rolled dice resolving outputs, debug actions, or awaiting Phase 3)
  * **Shield Assignment Slots** (`Red`, `Blue`, `Green`)
  * **Unpatched Zone** (worn-down modules and burnt relays offline until repaired)
  * **Version Ability Track (`v1.0`, `v2.0`, `v3.0`)**: 3 tracking slots for once-per-version archetype powers
  * **System Reboot Track (`[ ] Ready / [X] Used`)**: Once-per-game emergency firmware restore slot
* **6 Consultancy Archetype Cards:**
  * **The Acoustic** (*Pattern Genius / Mainframe Resonance*)
  * **The Phreaker** (*Hardware Tinkerer / Emergency Relays*)
  * **The Prodigy** (*Reckless Hacker / Lock Bypassing*)
  * **The Spook** (*Ex-Intelligence / Operational Security & Slush Funds*)
  * **The Cipher** (*Mathematician / Algorithmic Arbitrage*)
  * **The Operator** (*Master Strategist / Contractor Coordination*)
* **16 Gray "Legacy Code" Starter Dice** (4 per player)
* **12 White "Contractor" Dice** (Temporary freelance phreakers / night-shift operators for hire in Phase 1)
* **Colored Software Module Dice (5 Colors, `2 × Players` dice per color):**
  * **Red Dice** — *FinSec / Encryption*
  * **Blue Dice** — *Firewall / Data Vault*
  * **Green Dice** — *Antivirus / Auto-Patcher*
  * **Yellow Dice** — *Commercial AI (High Revenue / Portfolio Greed)*
  * **Purple Dice** — *Black-Hat / Proxy AI (Sabotage & Profiteering)*
* **Software Module Variant Cards:** Multiple cards per die color; **1 card per color** is used each game to define that color's Special (`★`) faces.
* **Money Tokens (`$`)**, **Corporate Secret Tokens**, **Patch Tokens (`🔧`)** *(styled as magnetic tape splice kits / jumper wires)*, and a **First Player (Lead Consultant) Marker**.

---

## 3. Setup

1. **SETEC Roadmap & Compiler Priming:** Deal **1 `v1.0` card**, **1 `v2.0` card**, and **1 `v3.0` card** face-up in a row next to the Cube Tower. Place the Version Marker on `v1.0`.
   * **Per-Version Corruption Tracks (Consistent Across All Player Counts):** Each Version card features its own escalating **Corruption Track** where every space carries a mechanical effect: **`4` spaces on `v1.0`**, **`5` spaces on `v2.0`**, and **`6` spaces on `v3.0`** (`15` total Black Cubes to Singularity across `v1.0 → v2.0 → v3.0`) `[TUNE]`.
   * **Prime the Compiler (Pre-Seed Drop):** Before populating the Staging Cup, take **`1 Red, 1 Blue, 1 Green, and 1 Black Cube`** (4 cubes total) from the supply and drop them into the empty Cube Tower. Any cubes that exit into the tray are **returned to the general supply**. Any cubes that remain stuck on the internal baffles stay inside the tower to prime the compiler for Round 1.
   * Place the starting cubes listed on the `v1.0` card into the **Staging Cup** (baseline: `2 Red, 2 Blue, 2 Green, 1 Black`). *(All subsequent cube injections from SETEC come directly from Corruption Track spaces).*
2. **Software Market:** For each of the 5 Colored Dice (**Red, Blue, Green, Yellow, Purple**), shuffle its Variant Cards, place **1 Variant Card** face-up in the center, and stack **`2 × Players`** dice of that color on it.
3. **Consultancy Setup (Each Player):**
   * Choose or randomly deal **1 Consultancy Archetype Card** to each player. Place it beside your terminal mat with all 3 Version slots (`v1.0`, `v2.0`, `v3.0`) toggled to **Ready**.
   * Place **4 Gray Legacy Dice** into your **Ready Zone**.
   * Take **`$7` Starting Money** `[TUNE: test $6–$8]`.
   * **Corporate Secrets & Starting Patch Tokens by Player Count:**
     * **2 Players:** Take **`8` Corporate Secrets** and **`2` Patch Tokens (`🔧`)**.
     * **3 Players:** Take **`8` Corporate Secrets** and **`2` Patch Tokens (`🔧`)**.
     * **4 Players:** Take **`10` Corporate Secrets** and **`2` Patch Tokens (`🔧`)** `[TUNE: v0.10.0 buffer parity]`.
4. Randomly assign the **First Player Marker** (used to resolve Market purchase order in Phase 3).

---

## 4. Round Structure & Consultancy Archetypes

Too Many Secrets is played over a series of rounds (~8–11 rounds). Each round consists of **3 Phases**:
1. **Phase 1: Boot & Configure** *(Simultaneous)*
2. **Phase 2: SETEC Compile** *(The Cube Tower Drop — Simultaneous)*
3. **Phase 3: Operations & Retainers** *(Clockwise turns starting with First Player)*

### Consultancy Archetype Special Abilities ("Once per Version")
Each player’s consultancy archetype provides a powerful, specialized capability that may be activated **once per SETEC Version** (`v1.0`, `v2.0`, and `v3.0`):
* **Use-It-or-Lose-It Timing:** A version's ability must be activated before SETEC compiles to the next version. If SETEC advances to a new version in Phase 2 Step 2A and your current version slot has not been used, that charge is **forfeited**.
* **Immediate Version Unlock:** The newly active version's ability slot unlocks immediately in the same round SETEC advances, ready for use in Phase 2B, Phase 3, or subsequent rounds.

---

### Phase 1: Boot & Configure (Simultaneous)

1. **Autonomous Protocol Pulse:** SETEC compiles new intrusion subroutines in the background. Take Black Cubes from the general supply based on the active Version card and place them into the **Staging Cup** (**`v1.0`:** `1 Black Cube`; **`v2.0`:** `2 Black Cubes`; **`v3.0`:** `2 Black Cubes`) `[TUNE]`.
2. **Temp Staffing (Contractor Dice):** Before rolling, each player may hire temporary White Contractor Dice (freelance phreakers) for this round. Hiring uses **Progressive Contractor Pricing**: **`$1` for the 1st die, `$2` for the 2nd die, and `$3` for the 3rd die** (up to a maximum of **`3` White Dice** per round; hiring all 3 costs **`$6`** total `[TUNE]`). All hired White Contractor dice are added to your Active Pool for this round. *(Archetype Timing: **The Operator** may trigger Redundant Crew here).*
3. **Roll Ready Pool:** Every player simultaneously rolls all dice in their **Ready Zone** plus any hired **White Contractor Dice** into their **Active Pool**. *(Dice in your **Unpatched Zone** are not rolled.)*
4. **Yahtzee Rerolls & Lock Resolution (Simultaneous):**
   * Each player may perform up to **`2` free rerolls** of any subset of their rolled dice (3 rolls total).
   * Between rerolls, players may set aside (keep) any dice, or pick previously kept dice back up for subsequent rerolls.
   * **Locked Dice:** Certain conditions cause dice to be **Locked**:
     * A die (White Contractor or Colored Red/Blue/Green) that rolls a **`Glitch (Locked)`** face is locked immediately.
     * If a **Corruption Track Lock Effect** was triggered during the previous round's Phase 2 (e.g., *Cash faces cannot be rerolled next Phase 1*, *Patch faces cannot be rerolled next Phase 1*, or *Shield faces cannot be rerolled next Phase 1*), any rolled die showing that face type is locked immediately for this Phase 1.
     * Locked dice **cannot** be rerolled during your free rerolls.
   * **Debug Action (`🔧` Token Utility):** At any time during your reroll sequence, you may spend **`1 🔧` token** from your pool (or permanently set aside and lock a rolled die showing `+1 🔧`) to **Unlock `1` locked die**, allowing it to be rerolled in remaining rerolls. *(Archetype Timing: **The Prodigy** may trigger Brute-Force Bypass here to reroll locked dice freely and turn 1 rolled die to any non-Star face of choice).*
5. **Assign Dice & Declare Choices (Simultaneous):**
   * Assign rolled Shield dice (and Shield `★` abilities) from your Active Pool to your **Red**, **Blue**, or **Green** Shield slots.
   * **Choice Faces:** Any die showing a **Choice Face** must have its role committed now:
     * If a choice face offers a Shield option (e.g. `Block 1 Blue / +1 🔧` on Blue), the player decides whether to assign it to its Shield slot, or leave it in the Active Pool to generate its alternative resource in Step 6.
     * If a choice face offers alternative resources (e.g. `+$1 / +1 🔧` on Gray or `+1 🔧 / +$1` on Green), the player declares which resource the die will produce.
   * **Generic (`Any`) Shields** (including rolled White Contractor shields) must be committed to a specific color (`Red`, `Blue`, or `Green`) *before* Phase 2 begins.
6. **Gain Resource Outputs, Cryptographic Hash Matches & Glitch Backlash (Simultaneous):**
   * **Cryptographic Hash Match:** Inspect all your active dice (`Ready + Contractor`) after resolving rerolls and declaring choice options. For every set of 3 dice displaying the exact same printed output signature (e.g. 3 of a kind = +1 Secret; 6 of a kind or two distinct triplets = +2 Secrets), gain **`+1 Corporate Secret`** (uncapped). *Note: Glitch faces (`Glitch (Locked)`) are corrupted anomalies and can never form Hash Matches. Choice faces match their declared option.*
   * **Hardware Glitch Backlash:** For each active die showing an unresolved **`Glitch (Locked)`** face at the conclusion of rerolls, local hardware burns out:
     * You must move **`1 active die`** from your roll to your **Unpatched Zone** (if this die was committed to a shield in Step 5, its shield commitment is removed).
     * **Contractor Sacrifice:** If you have an active White Contractor die in your roll, you may choose to **discard `1` White Contractor die** back to the central supply instead of demoting a permanent Ready die!
   * For all dice remaining in your Active Pool (unassigned to defense and not demoted), collect any **`$` Money tokens**, **Patch Tokens (`🔧`)**, and immediate `★` outputs from their final rolled faces into your personal supply.
   * Dice showing `Glitch (Locked)` produce 0 resource outputs. *(Note: Patch token collection is unclamped during the round; excess patches are only discarded at End-of-Round Cleanup).* [TUNE]

---

### Phase 2: SETEC Compile (Simultaneous)

Take **all cubes** from the **Staging Cup** and drop them into the **Cube Tower** together. Cubes that remain stuck on the baffles stay inside the tower for future rounds. Group all cubes that exit into the tray by color and resolve in order:

#### Step 2A: Resolve Black (Corruption) Cubes, Track Spaces & Version Upgrades
Move exited **Black Cubes** from the tray onto the next empty space(s) of the active Version's **Corruption Track** one at a time from left to right. **Every space covered by a Black Cube immediately triggers its printed effect** (see Section 6C):
* **Corruption Space Effects:**
  * **Add Cubes (`+X Red/Blue/Green/Black`):** Take the specified cubes from the general supply.
    * *Mode A (Next-Round Priming — Baseline `[TUNE]`):* Place newly added cubes into the **Staging Cup** (or aside in the tray) so they do **not** apply to this round's Step 2B attack, and are primed to drop into the Cube Tower next round.
    * *Mode B (Immediate Tray Resolution — Variant `[TUNE]`):* Place newly added Attack Cubes directly into the active **Tray** so they apply to this round's Step 2B attack and then recycle into the Staging Cup (any newly added Black Cubes go to the Staging Cup for next round).
  * **All Players Lose `$X`:** Each player loses up to `$X` from their supply (minimum `$0`; unpaid cash loss from a corruption space does *not* drain patches or secrets).
  * **All Players Lose `X 🔧`:** Each player loses up to `X` Patch Tokens from their supply (minimum `0`).
  * **All Players Demote `X` Dice to Unpatched:** Each player must move `X` non-worn permanent dice of their choice from their Active Pool / Ready Zone to their **Unpatched Zone** (preferring unassigned dice; if a die committed to a Shield slot in Phase 1 must be demoted, its shield commitment is removed before Step 2B).
  * **All Players Return `X` Colored Dice:** Each player who owns at least 1 Colored Module Die (across Unpatched, Active, or Ready zones) must return up to `X` Colored Module Dice of their choice to the Market supply. *(Gray starter dice cannot be returned).*
  * **All Players Lose `X` Corporate Secrets:** Each player immediately loses `X` Corporate Secrets (checking for Patient Zero at `<= 0` Secrets).
  * **Next-Phase Face Lock (`Cash`, `Patch`, or `Shield` Faces Locked Next Phase 1):** During the next round's Phase 1 Step 4 (Rerolls), any rolled die showing that face type (including Choice faces offering that option) is immediately **Locked** and cannot be rerolled unless unlocked with `1 🔧` (Debug Action). *(Each Version card has at most 1 Lock space on its track).*
* **Upgrading (`v1.0 → v2.0` or `v2.0 → v3.0`):** When the final space of `v1.0` (`4th` space) or `v2.0` (`5th` space) is filled and resolved:
  1. Clear all Black Cubes from the completed Version card back to the supply.
  2. Move the Version Marker to the next Version card (`v2.0` or `v3.0`). *(No separate upgrade payload is added; the Corruption Track spaces themselves are the sole source of new cubes).*
  3. **Archetype Ability Flip:** Any unused Archetype Ability from the previous version is **forfeited**. The newly activated Version's ability slot unlocks immediately, becoming available for use starting in Step 2B or Phase 3 of the current round.
  4. Place any remaining exited Black Cubes from this drop one at a time onto the new Version's Corruption Track, triggering each space covered!
* **Singularity (`v3.0` Track Fills):** When the final (`6th`) space of `v3.0` is filled and resolved, **Singularity is triggered!** Step 2B resolves normally for this drop, and the game enters its final round wrap-up.

#### Step 2B: Resolve Attack Cubes (Red, Blue, Green)
Calculate the total attack strength of **Red**, **Blue**, and **Green** from exited cubes in the tray. *(Archetype Timing: **The Acoustic** may trigger Baffle Echo here to ignore 1 Attack Cube of their choice for themselves this round).* Each player simultaneously resolves all three colors against their committed Shields:

1. **Dice Wear (Software Adaptation):** Any permanent die assigned as a Shield that **actively blocks at least 1 cube** moves to your **Unpatched Zone**. *(White Contractor dice that block damage return to the general supply at round end; they never move to the Unpatched Zone).* If multiple dice were committed to a color and fewer cubes dropped than total shield strength, the defending player chooses which die absorbs the attack and wears down. *(If 0 cubes of that color dropped, or another die already absorbed all cubes of that color, unused permanent Shield dice remain Ready and return to your Ready Zone!)*
2. **Unblocked Damage:**
   * **Red (Ransomware / Financial Wiretaps):** Lose **`$1`** per unblocked Red cube.
     * **Emergency Patch Absorption:** If cash is insufficient to pay the full ransom, each available **`1 🔧` token** automatically absorbs **`$1`** of unpaid ransom before secrets leak.
     * **Unpaid Ransom Leak:** If any ransom remains unpaid after exhausting cash and patch tokens, proprietary source code leaks to the dark web: lose **`1 Corporate Secret` per unpaid `$1`**! Money is strictly non-negative and never drops below `$0`.
   * **Blue (Spyware / Data Exfiltration):** Lose **`1` Corporate Secret** per unblocked Blue cube.
   * *(Archetype Timing: **The Spook** may trigger Slush Fund during damage calculation to absorb up to 2 Secret loss for free).*
   * **Green (Malware / Logic Bombs):** For each unblocked Green cube, move **`1` Ready die** (that was not already worn down this round) to your **Unpatched Zone**. **Contractor Sacrifice:** You may choose to **discard `1` active White Contractor die** to the supply instead of demoting a permanent Ready die! *(**Commercial Exposure (Yellow Dice):** Commercial software attracts heavy scrutiny. Contractor Sacrifice cannot be used to prevent Green malware from demoting a Yellow die. When resolving unblocked Green malware, Ready Yellow dice must be demoted to Unpatched first before Contractor Sacrifice or non-Yellow dice can absorb malware).* If you have **no Ready dice or Contractor dice left**, you must instead **Destroy (return to box) `1` Unpatched die** of your choice! *(If you have 0 dice remaining anywhere, track unfulfilled destructions for wipeout scoring).*
   * **Patient Zero Check:** If your Corporate Secrets reach **`0` (or below)**, your consultancy suffers a **Total Data Breach** and you become **Patient Zero** *(track negative Secrets below 0 if needed for total-wipeout tiebreakers)*.
3. **Snowball Recycle & Contractor Expiration:** Place **all exited Red, Blue, and Green cubes** from the tray back into the **Staging Cup** for next round. All White Contractor dice (whether they blocked, sacrificed, or remained unused) return to the general supply.
4. **Empty Tray (Compile Buffer Overflow):** If **`0 cubes of any color`** exit the tower into the tray this phase:
   * No corruption advances and no attacks occur this round (unused permanent Shield dice return to your Ready Zone as normal).
   * The compiler's idle cycle triggers an overflow: take **`1 Red, 1 Blue, and 1 Green Cube`** from the supply and place them into the **Staging Cup** for next round's compile (in addition to the standard Phase 1 Black Cube).

#### Step 2C: Check End Game Triggers
The current round is declared the **Final Round** if **either**:
* **Singularity** was triggered in Step 2A, **OR**
* **One or more players suffered a Total Data Breach (`<= 0 Secrets`)** in Step 2B.

If triggered, any player who became **Patient Zero** is immediately eliminated and skips Phase 3. **All surviving players proceed to Phase 3 to execute one final operations turn** before game scoring.

*(Exception: If all remaining players suffer a Total Data Breach simultaneously, the game ends immediately. Phase 3 is skipped entirely, and players proceed directly to Total Wipeout Scoring.)*

---

### Phase 3: Operations & Retainers (Clockwise Turns)

Starting with the First Player and proceeding clockwise, each surviving player takes a single operations turn, performing any combination of the following actions in any order:

1. **Purchase Software Module Dice (Limit `2` dice per turn `[TUNE]`):**
   * Pay the `$` cost of any available Colored Die in the Market and place it directly into your **Ready Zone**. *(Archetype Timing: **The Cipher** may trigger Algorithmic Arbitrage here to purchase 1 Colored Die at a **$2 discount**).*
2. **Patch Worn-Out Modules (Unlimited):**
   * Spend **`1 🔧` token** *or* pay **`$2`** `[TUNE: test $1–$3]` to move **1 die** from your **Unpatched Zone** back to your **Ready Zone**. *(Crucial for End Game: unpatched dice score `0 VP`; patching a colored die to Ready earns its full printed 3–4 VP!).* *(Archetype Timing: **The Phreaker** may trigger Magnetic Splice here to patch 1 die for free).*
3. **Emergency Reboot: System Reboot (Once per Game):**
   * If you enter or reach Phase 3 with **`0 Ready dice`** and have not yet used your once-per-game System Reboot, you may execute an emergency reboot:
   * Move **all Gray Starter Dice** from your **Unpatched Zone** back to your **Ready Zone**.
   * *(Any Colored Module dice in your Unpatched Zone represent damaged custom hardware and remain unpatched; they must still be repaired normally with `1 🔧` or `$2`).*
   * Mark the **System Reboot** slot on your terminal mat as used.

After all players finish Phase 3:
* If the Final Round was triggered, proceed directly to **Section 5: End Game & Victory Scoring**.
* Otherwise:
  * Return all non-worn dice from your Active Pool and un-worn Shield slots to your **Ready Zone**.
  * Keep all Money and Secrets. Discard any unspent Patch Tokens in excess of **`3 🔧`** tokens back to the supply (End-of-Round Cleanup Cap [TUNE]).
  * Pass the **First Player Marker** clockwise and begin the next round.

---

## 5. End Game & Victory Scoring

### Determining the Winner
When the game ends (via Singularity when `v3.0` fills, or via Patient Zero check):

* **Standard Ending (1+ Consultancies Survive):**
  * Any player who suffered a **Total Data Breach** (`<= 0 Secrets`) is **eliminated** as Patient Zero and cannot win.
  * Surviving consultancies compare their **Corporate Secrets**. The surviving consultancy with the **most Corporate Secrets wins!**
  * **Hierarchical Tiebreakers:** If surviving consultancies are tied for Corporate Secrets, break ties using the following hierarchy:
    1. **Operational Capital:** Most remaining **Money (`$`)**.
    2. **Active Infrastructure:** Most **Active Colored Module Dice** in your **Ready Zone** (Gray starter dice and White contractor dice do not count).
    3. **Hardware Readiness:** Most remaining **Patch Tokens (`🔧`)**.
    4. **Reliability:** Fewest **Unpatched Dice** (least worn hardware).
    5. If still tied, victory is shared.

* **Total Wipeout Ending (All Consultancies Breach):**
  * Narrative victory belongs to the Rogue Agent!
  * To rank the human consultancies, calculate **Net Breach Score**: subtract **Overflow Penalties** incurred on the final compile (`-4 VP` per Secret below 0, `-3 VP` per unfulfilled die destruction) from nominal portfolio value; highest net score takes top honors.

---

## 6. Prototype Reference Appendix (Dice & Cards)

### A. Software Dice Faces (`d6`) `[TUNE]`

| Die Type | Cost | VP | Face 1 | Face 2 | Face 3 | Face 4 | Face 5 | Face 6 |
| :--- | :---: | :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **Gray (Legacy)** | Starter | `0` | `Block 1 Any` | `Block 1 Any` | `+$1` | `+$1` | `+$1 / +1 🔧` | `+1 🔧` |
| **White (Contractor)** | Prog. `$1/$2/$3` | `0` | `Block 1 Any` | `Block 1 Any` | `Block 1 Any` | `+$1` | `Glitch (Locked)` | `Glitch (Locked)` |
| **Red (FinSec)** | `$4` | `3` | `Block 1 Red` | `+$2` | `+$2` | `+$2` | `Glitch (Locked)` | `Red ★` |
| **Blue (Firewall)** | `$5` | `4` | `Block 1 Blue` | `+1 🔧` | `+$1` | `Block 1 Blue / +1 🔧` | `Glitch (Locked)` | `Blue ★` |
| **Green (Antivirus)** | `$4` | `3` | `Block 1 Green` | `+1 🔧` | `+2 🔧` | `+1 🔧 / +$1` | `Glitch (Locked)` | `Green ★` |
| **Yellow (Commercial)**| `$5` | `4` | `+$3` | `+$2` | `+$2` | `+$1 & +1 🔧` | `Yellow ★` | `Yellow ★` |
| **Purple (Black-Hat)** | `$4` | `3` | `Block 1 Any` | `Block 1 Any` | `+$2` | `+$1 & +1 🔧` | `Purple ★` | `Purple ★` |

* **Choice Faces (`/`):** Faces with a slash (`/`) indicate a Choice Face. During Phase 1 Step 5, the player declares which of the two options the die fulfills for this round.
  * **Phase 1 Lock Interactions:** A choice face displaying a Cash option (e.g. `+$1 / +1 🔧` on Gray or `+1 🔧 / +$1` on Green) is treated as a Cash face when Cash faces are locked by a Corruption Track effect (e.g. `v2.0 RaaS` Space 3). A choice face displaying a Shield option (e.g. `Block 1 Blue / +1 🔧` on Blue) is treated as a Shield face when Shield faces are locked by a Corruption Track effect (e.g. `v3.0 Zero-Day Override` Space 3). Locked dice can be unlocked using `1 🔧` (Debug Action).
* **Hardware Glitch Faces (`Glitch (Locked)`):** Face 5 on Red, Blue, and Green represents a push-your-luck hardware glitch. When rolled, the die is locked immediately. In Step 6, each unresolved glitch face requires the player to move 1 active die to their Unpatched Zone (or sacrifice an active White Contractor die to the central supply). Glitch faces produce 0 shields and 0 resource outputs.

### B. Sample Module Variant Cards (`★` Effects)
* **Red `★` Variants:**
  * *R1 — Ransom Insurance:* `[Phase 2 — Defense]` `Block 1 Red` + `[Phase 1 — Boot]` gain `+$2`.
  * *R2 — Threat Bounty:* `[Phase 2 — Defense]` `Block 2 Red`; if you take `0` unblocked Red damage this round, `[Phase 2 — Damage]` gain `+$2`.
  * *R3 — Short Squeeze:* `[Phase 2 — Compile]` Gain `+$3` (or `+$4` if 3+ Red cubes exit the tower this round).
* **Blue `★` Variants:**
  * *B1 — Honeypot Telemetry:* `[Phase 2 — Defense]` `Block 2 Blue`; if 1+ Blue cubes exit the tower and you take `0` Blue damage, `[Phase 2 — Damage]` gain `+$3`.
  * *B2 — Deep R&D Vault:* `[Phase 2 — Defense]` `Block 1 Blue`, **OR** `[Phase 3 — Operations]` pay `$4` during Phase 3 to gain `+1 Corporate Secret` `[TUNE]`.
  * *B3 — Air-Gapped Backup:* `[Phase 2 — Defense]` `Block 1 Blue`; when this die actively blocks, you may move `1` other Ready die of your choice to **Unpatched** instead of this die (if you have no other Ready dice, this die moves to Unpatched) `[TUNE]`.
* **Green `★` Variants:**
  * *G1 — Self-Healing Kernel:* `[Phase 2 — Defense]` `Block 2 Green` + `[Phase 1 — Boot]` gain `+1 🔧`.
  * *G2 — Universal Sandbox:* `[Phase 2 — Defense]` `Block 1 Any` + `[Phase 1 — Boot]` gain `+1 🔧`.
  * *G3 — Live Reboot:* `[Phase 1 — Boot]` Gain `+2 🔧` + `+$1`.
* **Yellow `★` Variants:**
  * *Y1 — Algorithmic Trading:* `[Phase 1 — Boot]` Gain `+$4`, **OR** `[Phase 3 — Operations]` pay `$2` in Phase 3 to gain `+1 Corporate Secret`.
  * *Y2 — Cloud Monopoly:* `[Phase 1 — Boot]` Gain `+$2`, plus `+$1` per different colored module die you own (max `+$5`) `[TUNE]`.
  * *Y3 — Proprietary Training:* `[Phase 1 — Boot]` Gain `+1 Corporate Secret`, then immediately move this die to **Unpatched**.
* **Purple `★` Variants:**
  * *P1 — Zero-Day Injection:* `[Phase 1 — Boot]` Gain `+$2`; `[Phase 3 — Operations]` in Phase 3 you may add `1` Attack Cube (Red/Blue/Green) from the supply to the Staging Cup *(no Black cube added)*.
  * *P2 — Chaos Profiteer:* `[Phase 1 — Boot]` Gain `+$1` now, plus `[Phase 2 — Compile]` `+$2` per Black Cube that exits the tower in Phase 2.
  * *P3 — Packet Deflection:* `[Phase 2 — Defense]` `Block 2` of any single color; `[Phase 3 — Operations]` in Phase 3 you may pay `$1` to add `1` cube of that color from the supply to the Staging Cup `[TUNE]`.

### C. Sample SETEC Version Cards & Per-Version Corruption Tracks `[TUNE]`

Each Version Card defines its Corruption Track (`4` spaces on `v1.0`, `5` spaces on `v2.0`, `6` spaces on `v3.0`, consistent across all player counts). The Corruption Track is the **sole source of new SETEC cubes** entering the economy after setup. Two intensity profiles (**Standard** and **Aggressive**) are defined below for simulation benchmarking:

#### Profile 1: Standard Escalation Tracks (`4 / 5 / 6` Spaces)

| Version | Card Name | Initial Setup Cup | Space 1 | Space 2 | Space 3 | Space 4 | Space 5 | Space 6 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`v1.0`** (4) | *Script Kiddie* | `2R, 2B, 2G, 1K` | Add `1R, 1G` | All lose `$2` | Add `1B` | **Upgrade:** Lose `1 🔧` + Add `1R, 1B` | — | — |
| **`v1.0`** (4) | *Data Scraper* | `2R, 3B, 2G, 1K` (`+$1` start) | Lose `1 🔧` + Add `1B` | All demote `1` die | Add `1R, 1G` | **Upgrade:** Lose `$2` + Add `1B, 1G` | — | — |
| **`v2.0`** (5) | *RaaS* | — | All lose `$3` | Add `1R, 1G` | **Lock Cash (`$`)** next Phase 1 | Lose `$3` & `1 🔧` | **Upgrade:** Add `1R, 1B, 1K` | — |
| **`v2.0`** (5) | *Polymorphic Worm* | — | Lose `2 🔧` + Add `1G` | All demote `1` die | Add `1B, 1G` | **Lock Patch (`🔧`)** next Phase 1 | **Upgrade:** Demote `1` die + Add `1R, 1G, 1K` | — |
| **`v3.0`** (6) | *Zero-Day Override* | — | Add `1R, 1B, 1G` | All lose `$4` | **Lock Shields** next Phase 1 | Return `1` Colored Die | Lose `1 Secret` & demote `1` die | **Singularity:** Add `1R, 1B, 1G` |
| **`v3.0`** (6) | *Corrupted Kernel* | — | Demote `1` die + Add `1R, 1B` | Lose `$4` & `1 🔧` | Add `1R, 1B, 1G` | **Lock Shields** next Phase 1 | Lose `1 Secret` & return `1` Colored Die | **Singularity:** Add `2R, 2B` |

#### Profile 2: Aggressive Escalation Tracks (`4 / 5 / 6` Spaces — Heavy `v2.0` & `v3.0` Ramp)

| Version | Card Name | Initial Setup Cup | Space 1 | Space 2 | Space 3 | Space 4 | Space 5 | Space 6 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`v1.0`** (4) | *Script Kiddie* | `2R, 2B, 2G, 1K` | Add `1R, 1G` | All lose `$3` | Demote `1` die + Add `1B` | **Upgrade:** Lose `1 🔧` + Add `1R, 1B, 1G` | — | — |
| **`v1.0`** (4) | *Data Scraper* | `2R, 3B, 2G, 1K` (`+$1` start) | Lose `2 🔧` + Add `1B` | All demote `1` die | Add `1R, 1B, 1G` | **Upgrade:** Lose `$3` + Add `1R, 1G` | — | — |
| **`v2.0`** (5) | *RaaS* | — | All lose `$4` | Add `2R, 1G` | **Lock Cash (`$`)** next Phase 1 | Lose `$5` & `1 🔧` | **Upgrade:** Demote `1` die + Add `1R, 1B, 1K` | — |
| **`v2.0`** (5) | *Polymorphic Worm* | — | Lose `2 🔧` + Add `1B, 1G` | All demote `2` dice | Add `1R, 2G` | **Lock Patch (`🔧`)** next Phase 1 | **Upgrade:** Demote `1` die + Add `1B, 1G, 1K` | — |
| **`v3.0`** (6) | *Zero-Day Override* | — | Add `2R, 1B, 1G` | Lose `$5` & `2 🔧` | **Lock Shields** next Phase 1 | Return `1` Colored Die & demote `1` die | All lose `2 Secrets` | **Singularity:** Add `2R, 2B, 2G` |
| **`v3.0`** (6) | *Corrupted Kernel* | — | Demote `2` dice + Add `1R, 1B` | Lose `$5` & `2 🔧` | Add `2R, 2B, 1G` | **Lock Shields** next Phase 1 | Return `1` Colored Die & lose `1 Secret` | **Singularity:** Lose `1 Secret` + Add `2R, 2B, 1G` |

---

### D. Consultancy Archetype Reference Dossier

Each archetype features a unique special ability that may be activated **once per SETEC Version** (`v1.0`, `v2.0`, `v3.0`).

| Archetype | Timing Window | Ability Name | Ability Effect |
| :--- | :--- | :--- | :--- |
| **The Acoustic** | **Phase 2:** Step 2B Damage | *Baffle Echo* | When resolving compiler damage, ignore **1 Attack Cube** (`Red`, `Blue`, or `Green`) of your choice for yourself this round. *(All exited cubes remain in the exit tray and recycle into the Staging Cup as normal).* |
| **The Phreaker** | **Phase 3:** Operations Turn | *Magnetic Splice* | Move **1 worn die** from your Unpatched Zone back to your Ready Zone for **free** (without spending `🔧` or `$`). |
| **The Prodigy** | **Phase 1:** Step 4 Rerolls | *Brute-Force Bypass* | During your rerolls this phase, you may include **any number of Locked dice** (including Glitch dice) in your free rerolls without spending `🔧` tokens. In addition, you may turn **1 of your rolled dice to any non-Star face of your choice**. |
| **The Spook** | **Phase 2:** Step 2B Damage | *Slush Fund* | The Spook accesses emergency black budget reserves: **Absorb up to 2 Corporate Secret loss** (from Blue Spyware or unpaid Red Ransom) for free without paying cash. *(Any additional Secret loss may be absorbed by paying `$1` per Secret as normal).* |
| **The Cipher** | **Phase 3:** Operations Turn | *Algorithmic Arbitrage* | Purchase **1 Colored Die** from the Market at a **`$2 discount`** (minimum cost `$0`), **OR** gain an immediate **`+$2` cash payout** from the bank. |
| **The Operator** | **Phase 1:** Step 2 Staffing | *Redundant Crew* | Hire up to **2 White Contractor Dice for free** this round (bypassing progressive contractor costs). |
