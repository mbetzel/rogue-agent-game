# Rogue Agent — Rules Draft (v0.8)

**Players:** 2–4 | **Playtime:** ~45–60 min | **Weight:** Medium Euro / Dice-Pool Survival

---

## 1. Theme & Overview

A rogue AI agent has broken loose on the open internet, recompiling itself each round to breach corporate networks, extort cash, and exfiltrate proprietary secrets.

Each player leads a rival corporation racing to upgrade their defensive AI modules (represented by a custom dice pool), patch worn-out software, and survive the escalating threat. Cash-strapped corporations can secretly monetize and corrupt the Rogue Agent for quick capital—feeding corrupted code into the AI and advancing it toward Singularity, while taking on severe technical debt.

When the dust settles, any corporation that suffers a **Total Data Breach** (`<= 0 Secrets`) becomes **Patient Zero** and is eliminated from contention. Among the survivors, the corporation with the highest **Portfolio Value** wins.

> **Note on `[TUNE]` Tags:** Numbers marked `[TUNE]` are prototype baselines verified via Monte Carlo simulation sweeps.

---

## 2. Components

### Central Threat (The Rogue Agent)
* **1 Cube Tower** (the AI's unstable compiler)
* **1 Staging Cup** (open bowl/mat visible to all players showing code queued for the next compile)
* **Rogue Agent Cubes (4 Colors):**
  * **Red Cubes (Ransomware):** Extorts corporate **Money**; unpaid ransom can be absorbed by **Patch Tokens (`🔧`)** or leaks **Secrets**.
  * **Blue Cubes (Spyware):** Directly steals **Corporate Secrets**.
  * **Green Cubes (Malware):** Degrades Ready dice to **Unpatched** (or destroys dice if overwhelmed).
  * **Black Cubes (Corrupted Code):** Advances the active **Version Corruption Track**.
* **Rogue Agent Version Deck (`v1.0`, `v2.0`, `v3.0`):** Setup cards defining the AI's starting code, upgrade payloads, and active directives.

### Player & Market Components
* **4 Player Mats**, each featuring:
  * **Ready Zone** (available dice ready to roll at round start)
  * **Active Pool (Rolled Area)** (rolled dice resolving immediate outputs, hotfixes, or waiting for Phase 3)
  * **Shield Assignment Slots** (`Red`, `Blue`, `Green`)
  * **Unpatched Zone** (worn-down dice offline until patched)
* **16 Gray "Legacy Code" Starter Dice** (4 per player)
* **12 White "Contractor" Dice** (Temporary on-demand staffing available for hire in Phase 1)
* **Colored Software Module Dice (5 Colors, `2 × Players` dice per color):**
  * **Red Dice** — *FinSec / Encryption*
  * **Blue Dice** — *Firewall / Data Vault*
  * **Green Dice** — *Antivirus / Auto-Patcher*
  * **Yellow Dice** — *Commercial AI (High Revenue / Portfolio Greed)*
  * **Purple Dice** — *Black-Hat / Proxy AI (Sabotage & Profiteering)*
* **Software Module Variant Cards:** Multiple cards per die color; **1 card per color** is used each game to define that color's Special (`★`) faces.
* **Money Tokens (`$`)**, **Corporate Secret Tokens**, **Patch Tokens (`🔧`)**, and a **First Player (CISO) Marker**.

---

## 3. Setup

1. **Rogue Agent Roadmap:** Deal **1 `v1.0` card**, **1 `v2.0` card**, and **1 `v3.0` card** face-up in a row next to the Cube Tower. Place the Version Marker on `v1.0`.
   * Each Version card has a **Corruption Track** equal to **`4` spaces** (flat across all player counts) `[TUNE]` (12 total Black cubes to Singularity).
   * Place the starting Attack Cubes listed on the `v1.0` card plus `1 Black Cube` into the **Staging Cup** (baseline: `1 Red, 1 Blue, 1 Green, 1 Black`). The Cube Tower starts empty.
2. **Software Market:** For each of the 5 Colored Dice (**Red, Blue, Green, Yellow, Purple**), shuffle its Variant Cards, place **1 Variant Card** face-up in the center, and stack **`2 × Players`** dice of that color on it.
3. **Corporate Headquarters (Each Player):**
   * Place **4 Gray Legacy Dice** into your **Ready Zone**.
   * Take **`$7` Starting Money** `[TUNE: test $6–$8]`.
   * **Corporate Secrets & Starting Patch Tokens by Player Count:**
     * **2 Players (Resilience Buffer):** Take **`8` Corporate Secrets** and **`2` Patch Tokens (`🔧`)**.
     * **3 Players:** Take **`7` Corporate Secrets** and **`1` Patch Token (`🔧`)**.
     * **4 Players:** Take **`7` Corporate Secrets** and **`1` Patch Token (`🔧`)**.
4. Randomly assign the **First Player Marker** (used only to resolve Market purchase order in Phase 3).

---

## 4. Round Structure

Rogue Agent is played over a series of rounds (~8–11 rounds). Each round consists of **3 Phases**:
1. **Phase 1: Boot & Configure** *(Simultaneous)*
2. **Phase 2: Rogue Agent Compile** *(The Cube Tower Drop — Simultaneous)*
3. **Phase 3: Corporate Operations** *(Clockwise turns starting with First Player)*

---

### Phase 1: Boot & Configure (Simultaneous)

1. **Autonomous AI Corruption Pulse:** The Rogue Agent compiles new malicious subroutines in the background. Take **`1 Black Cube`** from the general supply and place it into the **Staging Cup**.
2. **Temp Staffing (Contractor Dice):** Before rolling, each player may hire temporary White Contractor Dice for this round. Hiring uses **Progressive Contractor Pricing**: **`$1` for the 1st die, `$2` for the 2nd die, and `$3` for the 3rd die** (up to a maximum of **`3` White Dice** per round; hiring all 3 costs **`$6`** total `[TUNE]`). All hired White Contractor dice are added to your Active Pool for this round.
3. **Roll Ready Pool:** Every player simultaneously rolls all dice in their **Ready Zone** plus any hired **White Contractor Dice** into their **Active Pool**. *(Dice in your **Unpatched Zone** are not rolled.)*
4. **Yahtzee Rerolls & Lock Resolution (Simultaneous):**
   * Each player may perform up to **`2` free rerolls** of any subset of their rolled dice (3 rolls total).
   * Between rerolls, players may set aside (keep) any dice, or pick previously kept dice back up for subsequent rerolls.
   * **Locked Dice:** Certain conditions cause dice to be **Locked**:
     * A White Contractor Die that rolls a **`Glitch (Locked)`** face is locked immediately.
     * Active **Rogue Agent Version Directives** may lock specific faces (e.g., Cash in `v2.0 RaaS`, or Shields in `v3.0 Zero-Day Override`).
     * Locked dice **cannot** be rerolled during your free rerolls.
   * **Debug Action (`🔧` Token Utility):** At any time during your reroll sequence, you may spend **`1 🔧` token** from your pool (or permanently set aside and lock a rolled die showing `+1 🔧`) to **Unlock `1` locked die**, allowing it to be rerolled in remaining rerolls.
5. **Assign Dice & Declare Choices (Simultaneous):**
   * Assign rolled Shield dice (and Shield `★` abilities) from your Active Pool to your **Red**, **Blue**, or **Green** Shield slots.
   * **Choice Faces:** Any die showing a **Choice Face** must have its role committed now:
     * If a choice face offers a Shield option (e.g. `Block 1 Blue / +1 🔧` on Blue), the player decides whether to assign it to its Shield slot, or leave it in the Active Pool to generate its alternative resource in Step 6.
     * If a choice face offers alternative resources (e.g. `+$1 / +1 🔧` on Gray or `+1 🔧 / +$1` on Green), the player declares which resource the die will produce.
   * **Generic (`Any`) Shields** (including rolled White Contractor shields) must be committed to a specific color (`Red`, `Blue`, or `Green`) *before* Phase 2 begins.
6. **Gain Resource Outputs (Simultaneous):**
   * For all dice remaining in your Active Pool (unassigned to defense), collect any **`$` Money tokens**, **Patch Tokens (`🔧`)**, and immediate `★` outputs from their final rolled faces into your personal supply.
   * You may hold at most **`3 🔧`** tokens at once `[TUNE]`. Dice showing `Glitch (Locked)` produce 0 outputs.

---

### Phase 2: Rogue Agent Compile (Simultaneous)

Take **all cubes** from the **Staging Cup** and drop them into the **Cube Tower** together. Cubes that remain stuck on the baffles stay inside the tower for future rounds. Group all cubes that exit into the tray by color and resolve in order:

#### Step 2A: Resolve Black (Corruption) Cubes & Version Upgrades
Move exited **Black Cubes** onto the active Version's **Corruption Track** one at a time:
* **Upgrading (`v1.0 → v2.0` or `v2.0 → v3.0`):** When the 4th space fills:
  1. Clear all Black Cubes from the track back to the supply.
  2. Move the Version Marker to the next Version card (`v2.0` or `v3.0`).
  3. Add the new Version card's **Upgrade Payload** cubes to the **Staging Cup** *(they will drop starting next round; in 2-player games, `v2.0` and `v3.0` upgrade payloads are reduced by 1 attack cube each to prevent unscaled late-game cube avalanches: see Section 6C)* `[TUNE]`.
  4. The new Version's **Active Directive** takes effect immediately (including for Step 2B this round).
  5. Place any remaining Black Cubes from this drop onto the new Version's track.
* **Singularity (`v3.0` Track Fills):** If the 4th space of `v3.0` fills, **Singularity is triggered!** Step 2B resolves normally for this drop, and the game enters its final round wrap-up.

#### Step 2B: Resolve Attack Cubes (Red, Blue, Green)
Calculate the total attack strength of **Red**, **Blue**, and **Green** (exited cubes + any active Version Directive modifiers). Each player simultaneously resolves all three colors against their committed Shields:

1. **Dice Wear (Software Adaptation):** Any permanent die assigned as a Shield that **actively blocks at least 1 cube** moves to your **Unpatched Zone**. *(White Contractor dice that block damage return to the general supply at round end; they never move to the Unpatched Zone).* If multiple dice were committed to a color and fewer cubes dropped than total shield strength, the defending player chooses which die absorbs the attack and wears down. *(If 0 cubes of that color dropped, or another die already absorbed all cubes of that color, unused permanent Shield dice remain Ready and return to your Ready Zone!)*
2. **Unblocked Damage:**
   * **Red (Ransomware):** Lose **`$1`** per unblocked Red cube.
     * **Emergency Patch Absorption:** If cash is insufficient to pay the full ransom, each available **`1 🔧` token** automatically absorbs **`$1`** of unpaid ransom before secrets leak.
     * **Unpaid Ransom Leak:** If any ransom remains unpaid after exhausting cash and patch tokens, proprietary source code leaks to the dark web: lose **`1 Corporate Secret` per unpaid `$1`**! Money is strictly non-negative and never drops below `$0`.
   * **Blue (Spyware):** Lose **`1` Corporate Secret** per unblocked Blue cube.
   * **Green (Malware):** For each unblocked Green cube, move **`1` Ready die** (that was not already worn down this round) to your **Unpatched Zone**. **Contractor Sacrifice:** You may choose to **discard `1` active White Contractor die** to the supply instead of demoting a permanent Ready die! *(**Commercial Exposure (Yellow Dice):** Commercial software attracts heavy scrutiny. Contractor Sacrifice cannot be used to prevent Green malware from demoting a Yellow die. When resolving unblocked Green malware, Ready Yellow dice must be demoted to Unpatched first before Contractor Sacrifice or non-Yellow dice can absorb malware).* If you have **no Ready dice or Contractor dice left**, you must instead **Destroy (return to box) `1` Unpatched die** of your choice! *(If you have 0 dice remaining anywhere, track unfulfilled destructions for wipeout scoring).*
   * **Patient Zero Check:** If your Corporate Secrets reach **`0` (or below)**, your network suffers a **Total Data Breach** and you become **Patient Zero** *(track negative Secrets below 0 if needed for total-wipeout tiebreakers)*.
3. **Snowball Recycle & Contractor Expiration:** Place **all exited Red, Blue, and Green cubes** from the tray back into the **Staging Cup** for next round. All White Contractor dice (whether they blocked, sacrificed, or remained unused) return to the general supply.

#### Step 2C: Check End Game Triggers
The current round is declared the **Final Round** if **either**:
* **Singularity** was triggered in Step 2A, **OR**
* **One or more players suffered a Total Data Breach (`<= 0 Secrets`)** in Step 2B.

If triggered, any player who became **Patient Zero** is immediately eliminated and skips Phase 3. **All surviving players proceed to Phase 3 to execute one final operations turn** before game scoring.

*(Exception: If all remaining players suffer a Total Data Breach simultaneously, the game ends immediately. Phase 3 is skipped entirely, and players proceed directly to Total Wipeout Scoring.)*

---

### Phase 3: Corporate Operations (Clockwise Turns)

Starting with the First Player and proceeding clockwise, each surviving player takes a single operations turn, performing any combination of the following actions in any order:

1. **Purchase Software Dice (Limit `2` dice per turn `[TUNE]`):**
   * Pay the `$` cost of any available Colored Die in the Market and place it directly into your **Ready Zone**.
2. **Patch Worn-Out Dice (Unlimited):**
   * Spend **`1 🔧` token** *or* pay **`$2`** `[TUNE: test $1–$3]` to move **1 die** from your **Unpatched Zone** back to your **Ready Zone**.
3. **Corrupt the Rogue Agent ("Dirty Income" — Limit `1×` per turn):**
   * **Prerequisites:** You must have at least **`1` Ready die** to move to Unpatched and at least **`2` Corporate Secrets** (cannot be taken if you have $\le 1$ Secret or 0 Ready dice).
   * Pay **`1 Corporate Secret`**.
   * Gain **`+$3`** `[TUNE: test $2–$4]` from the bank.
   * Place **`1 Black Cube`** from the supply into the **Staging Cup**.
   * **Technical Debt Backlash:** Immediately move **`1 Ready die`** of your choice to your **Unpatched Zone**.

After all players finish Phase 3:
* If the Final Round was triggered, proceed directly to **Section 5: End Game & Victory Scoring**.
* Otherwise:
  * Return all non-worn dice from your Active Pool and un-worn Shield slots to your **Ready Zone**.
  * Keep all Money, Secrets, and up to **`3 🔧`** tokens.
  * Pass the **First Player Marker** clockwise and begin the next round.

---

## 5. End Game & Victory Scoring

Calculate **Portfolio Value** `[TUNE weights]`:
* **`4 VP`** per remaining **Corporate Secret**
* **VP per owned Colored Module Die** as printed on its Market Card (Red: `3 VP`, Blue: `4 VP`, Green: `3 VP`, Yellow: `4 VP`, Purple: `3 VP`; Gray starter dice = `0 VP`, White contractor dice = `0 VP`)
* **`1 VP`** per **`$2`** remaining *(rounded down)*
* Unused **Patch Tokens (`🔧`)** are worth **`0 VP`**.

### Determining the Winner
* **Standard Ending (1+ Corporations Survive):** Any player who became **Patient Zero** (`<= 0 Secrets`) is **eliminated**. The surviving player with the highest **Portfolio Value** wins! *(Tiebreakers: 1. Most Corporate Secrets, 2. Most Money.)*
* **Total Wipeout Ending (All Players Breach):** Narrative victory belongs to the Rogue Agent! To rank the human players, subtract **Overflow Penalties** incurred on the final compile (`-4 VP` per Secret below 0, `-3 VP` per unfulfilled die destruction) from each player's Portfolio Value; highest net score takes top honors.

---

## 6. Prototype Reference Appendix (Dice & Cards)

### A. Software Dice Faces (`d6`) `[TUNE]`

| Die Type | Cost | VP | Face 1 | Face 2 | Face 3 | Face 4 | Face 5 | Face 6 |
| :--- | :---: | :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **Gray (Legacy)** | Starter | `0` | `Block 1 Any` | `Block 1 Any` | `+$1` | `+$1` | `+$1 / +1 🔧` | `+1 🔧` |
| **White (Contractor)** | Prog. `$1/$2/$3` | `0` | `Block 1 Any` | `Block 1 Any` | `Block 1 Any` | `+$1` | `Glitch (Locked)` | `Glitch (Locked)` |
| **Red (FinSec)** | `$4` | `3` | `Block 2 Red` | `Block 2 Red` | `+$2` | `+$2` | `Red ★` | `Red ★` |
| **Blue (Firewall)** | `$5` | `4` | `Block 2 Blue` | `Block 2 Blue` | `+$1` | `Block 1 Blue / +1 🔧` | `Blue ★` | `Blue ★` |
| **Green (Antivirus)** | `$4` | `3` | `Block 2 Green` | `Block 2 Green` | `+2 🔧` | `+1 🔧 / +$1` | `Green ★` | `Green ★` |
| **Yellow (Commercial)**| `$5` | `4` | `+$3` | `+$2` | `+$2` | `+$1 & +1 🔧` | `Yellow ★` | `Yellow ★` |
| **Purple (Black-Hat)** | `$4` | `3` | `Block 1 Any` | `Block 1 Any` | `+$2` | `+$1 & +1 🔧` | `Purple ★` | `Purple ★` |

* **Choice Faces (`/`):** Faces with a slash (`/`) indicate a Choice Face. During Phase 1 Step 5, the player declares which of the two options the die fulfills for this round.
  * **Directive Interactions:** A choice face displaying a Cash option (e.g. `+$1 / +1 🔧` on Gray or `+1 🔧 / +$1` on Green) is treated as a Cash face and is immediately locked by `v2.0 RaaS` Encrypted Memory. A choice face displaying a Shield option (e.g. `Block 1 Blue / +1 🔧` on Blue) is treated as a Shield face and is immediately locked by `v3.0 Zero-Day Override` Kernel Lock. Locked dice can be unlocked using `1 🔧` (Debug Action).

### B. Sample Module Variant Cards (`★` Effects)
* **Red `★` Variants:**
  * *R1 — Ransom Insurance:* `[Phase 2 — Defense]` `Block 1 Red` + `[Phase 1 — Boot]` gain `+$2`.
  * *R2 — Threat Bounty:* `[Phase 2 — Defense]` `Block 2 Red`; if you take `0` unblocked Red damage this round, `[Phase 2 — Damage]` gain `+$2`.
  * *R3 — Short Squeeze:* `[Phase 2 — Compile]` Gain `+$3` (or `+$4` if 3+ Red cubes exit the tower this round).
* **Blue `★` Variants:**
  * *B1 — Honeypot Telemetry:* `[Phase 2 — Defense]` `Block 2 Blue`; if 1+ Blue cubes exit the tower and you take `0` Blue damage, `[Phase 2 — Damage]` gain `+$3`.
  * *B2 — Deep R&D Vault:* `[Phase 2 — Defense]` `Block 1 Blue`, **OR** `[Phase 3 — Operations]` pay `$2` during Phase 3 to gain `+1 Corporate Secret` (max 10).
  * *B3 — Air-Gapped Backup:* `[Phase 2 — Defense]` `Block 1 Blue` and this die does **not** move to Unpatched when blocking.
* **Green `★` Variants:**
  * *G1 — Self-Healing Kernel:* `[Phase 2 — Defense]` `Block 2 Green` + `[Phase 1 — Boot]` gain `+1 🔧`.
  * *G2 — Universal Sandbox:* `[Phase 2 — Defense]` `Block 1 Any` + `[Phase 1 — Boot]` gain `+1 🔧`.
  * *G3 — Live Reboot:* `[Phase 1 — Boot]` Gain `+2 🔧` + `+$1`.
* **Yellow `★` Variants:**
  * *Y1 — Algorithmic Trading:* `[Phase 1 — Boot]` Gain `+$4`, **OR** `[Phase 3 — Operations]` pay `$2` in Phase 3 to gain `+1 Corporate Secret`.
  * *Y2 — Cloud Monopoly:* `[Phase 1 — Boot]` Gain `+$2`, plus `+$1` per Yellow die you own (max `+$5`).
  * *Y3 — Proprietary Training:* `[Phase 1 — Boot]` Gain `+1 Corporate Secret`, then immediately move this die to **Unpatched**.
* **Purple `★` Variants:**
  * *P1 — Zero-Day Injection:* `[Phase 1 — Boot]` Gain `+$2`; `[Phase 3 — Operations]` in Phase 3 you may add `1` Attack Cube (Red/Blue/Green) from the supply to the Staging Cup *(no Black cube added)*.
  * *P2 — Chaos Profiteer:* `[Phase 1 — Boot]` Gain `+$1` now, plus `[Phase 2 — Compile]` `+$2` per Black Cube that exits the tower in Phase 2.
  * *P3 — Packet Deflection:* `[Phase 2 — Defense]` `Block 2` of any single color; `[Phase 3 — Operations]` in Phase 3 add `1` cube of that color from the supply to the Staging Cup.

### C. Sample Rogue Agent Version Cards

| Version | Card Name | Staging Cup Payload | Active Directive |
| :--- | :--- | :--- | :--- |
| **`v1.0`** | *Script Kiddie* | `1 Red, 1 Blue, 1 Green, 1 Black` | None. |
| **`v1.0`** | *Data Scraper* | `2 Blue, 1 Red, 1 Black` | Players start with `+$1` extra Money ($8 total). |
| **`v2.0`** | *Ransomware-as-a-Service* | `+2 Red, +1 Green` *(2P: `+1 Red, +1 Green`)* | **Encrypted Memory:** Any rolled die showing Cash (`+$1` or `+$2`) is **Locked** immediately (cannot be rerolled unless unlocked with `1 🔧`). |
| **`v2.0`** | *Polymorphic Worm* | `+2 Green, +1 Blue` *(2P: `+1 Green, +1 Blue`)* | **Subroutine Throttling:** Players receive only **`1` free reroll** in Phase 1 (instead of 2). |
| **`v3.0`** | *Zero-Day Override* | `+1 Red, +1 Blue, +1 Green` *(2P: `+1 Red, +1 Blue`)* | **Kernel Lock:** Any rolled die showing a Shield (`Block 1` or `Block 2`) is **Locked** immediately (cannot be rerolled unless unlocked with `1 🔧`). |
| **`v3.0`** | *Corrupted Kernel* | `+2 Red, +2 Blue` *(2P: `+1 Red, +1 Blue`)* | Each Black Cube that exits the tower also adds `+1` Strength to the Attack Color with the most exited cubes this round. |
