# Rogue Agent — Rules Draft (v0.2)

**Players:** 2–4 | **Playtime:** ~45–60 min | **Weight:** Medium Euro / Dice-Pool Survival

---

## 1. Theme & Overview

A rogue AI agent has broken loose on the open internet, recompiling itself each round to breach corporate networks, extort cash, and exfiltrate proprietary secrets.

Each player leads a rival corporation racing to upgrade their defensive AI modules (represented by a custom dice pool), patch worn-out software, and survive the escalating threat. Cash-strapped corporations can secretly monetize and corrupt the Rogue Agent for quick capital—permanently feeding new attack code into the AI and pushing it toward Singularity.

When the dust settles, any corporation that goes **Insolvent** or suffers a **Total Data Breach** becomes **Patient Zero** and is eliminated from contention. Among the survivors, the corporation with the highest **Portfolio Value** wins.

> **Note on `[TUNE]` Tags:** Numbers marked `[TUNE]` are initial prototype baselines scheduled for Monte Carlo stress-testing.

---

## 2. Components

### Central Threat (The Rogue Agent)
* **1 Cube Tower** (the AI's unstable compiler)
* **1 Staging Cup** (open bowl/mat visible to all players showing code queued for the next compile)
* **Rogue Agent Cubes (4 Colors):**
  * **Red Cubes (Ransomware):** Drains corporate **Money**.
  * **Blue Cubes (Spyware):** Steals **Corporate Secrets**.
  * **Green Cubes (Malware):** Degrades Ready dice to **Unpatched** (or destroys dice if overwhelmed).
  * **Black Cubes (Corrupted Code):** Advances the active **Version Corruption Track**.
* **Rogue Agent Version Deck (`v1.0`, `v2.0`, `v3.0`):** Setup cards defining the AI's starting code, upgrade payloads, and active directives.

### Player & Market Components
* **4 Player Mats**, each featuring:
  * **Ready Zone** (dice available to roll this round)
  * **Unpatched Zone** (worn-down dice offline until patched)
  * **Shield Assignment Slots** (`Red`, `Blue`, `Green`)
* **16 Gray "Legacy Code" Starter Dice** (4 per player)
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
   * Each Version card has a **Corruption Track** equal to **`Players + 1` spaces** (`3 / 4 / 5` spaces for `2 / 3 / 4` players) `[TUNE]`.
   * Place the starting Attack Cubes listed on the `v1.0` card into the **Staging Cup** (baseline: `1 Red, 1 Blue, 1 Green`). The Cube Tower starts empty.
2. **Software Market:** For each of the 5 Colored Dice (**Red, Blue, Green, Yellow, Purple**), shuffle its Variant Cards, place **1 Variant Card** face-up in the center, and stack **`2 × Players`** dice of that color on it.
3. **Corporate Headquarters (Each Player):**
   * Place **4 Gray Legacy Dice** into your **Ready Zone**.
   * Take **`$5` Starting Money** `[TUNE: test $3–$9]`.
   * Take **`6` Corporate Secrets** `[TUNE: test 4–10]`.
   * Take **`1` Patch Token (`🔧`)** `[TUNE: test 0–2]`.
4. Randomly assign the **First Player Marker** (used only to resolve Market purchase order in Phase 3).

---

## 4. Round Structure

Rogue Agent is played over a series of rounds (~8–11 rounds). Each round consists of **3 Phases**:
1. **Phase 1: Boot & Configure** *(Simultaneous)*
2. **Phase 2: Rogue Agent Compile** *(The Cube Tower Drop — Simultaneous)*
3. **Phase 3: Corporate Operations** *(Clockwise turns starting with First Player)*

---

### Phase 1: Boot & Configure (Simultaneous)

Players inspect the cubes currently waiting in the **Staging Cup** (and recall what remained stuck inside the Cube Tower), then configure their defenses:

1. **Roll Ready Pool:** Every player simultaneously rolls all dice in their **Ready Zone**. *(Dice in your **Unpatched Zone** are not rolled.)*
2. **Gain Immediate Outputs & Hotfix Rerolls:**
   * Collect any **`$`** and **Patch Tokens (`🔧`)** rolled on non-shield faces immediately (you may hold at most **`3 🔧`** tokens at once `[TUNE]`).
   * **Hotfix (Luck Mitigation):** Before dropping cubes into the tower, you may spend **`1 🔧` token** to reroll any **1** of your dice (repeatable).
3. **Commit Defenses:**
   * Assign any rolled Shield dice (and Shield `★` abilities) to your **Red**, **Blue**, or **Green** Shield slots.
   * **Generic (`Any`) Shields** must be committed to a specific color (`Red`, `Blue`, or `Green`) *before* Phase 2 begins.

---

### Phase 2: Rogue Agent Compile (Simultaneous)

Take **all cubes** from the **Staging Cup** and drop them into the **Cube Tower** together. Cubes that remain stuck on the baffles stay inside the tower for future rounds. Group all cubes that exit into the tray by color and resolve in order:

#### Step 2A: Resolve Black (Corruption) Cubes & Version Upgrades
Move exited **Black Cubes** onto the active Version's **Corruption Track** one at a time:
* **Upgrading (`v1.0 → v2.0` or `v2.0 → v3.0`):** When the `Players + 1`th space fills:
  1. Clear all Black Cubes from the track back to the supply.
  2. Move the Version Marker to the next Version card (`v2.0` or `v3.0`).
  3. Add the new Version card's **Upgrade Payload** cubes to the **Staging Cup** *(they will drop starting next round)*.
  4. The new Version's **Active Directive** takes effect immediately (including for Step 2B this round).
  5. Place any remaining Black Cubes from this drop onto the new Version's track.
* **Singularity (`v3.0` Track Fills):** If the `Players + 1`th space of `v3.0` fills, **Singularity is triggered!** Finish resolving **Step 2B** for this final compile, after which the game immediately ends.

#### Step 2B: Resolve Attack Cubes (Red, Blue, Green)
Calculate the total attack strength of **Red**, **Blue**, and **Green** (exited cubes + any active Version Directive modifiers). Each player simultaneously resolves all three colors against their committed Shields:

1. **Dice Wear (Software Adaptation):** Any die assigned as a Shield that **actively blocks at least 1 cube** moves to your **Unpatched Zone**. *(If 0 cubes of that color dropped, or another die already absorbed all cubes of that color, unused Shield dice remain Ready!)*
2. **Unblocked Damage:**
   * **Red (Ransomware):** Lose **`$1`** per unblocked Red cube. If you must lose `$1` while at `$0`, you become **Insolvent (Patient Zero)** *(track negative `$` debt if needed for total-wipeout tiebreakers)*.
   * **Blue (Spyware):** Lose **`1` Corporate Secret** per unblocked Blue cube. If your Secrets reach **`0` (or below)**, you suffer a **Total Breach (Patient Zero)** *(track negative Secrets below 0 if needed for total-wipeout tiebreakers)*.
   * **Green (Malware):** For each unblocked Green cube, move **`1` Ready die** (that was not already worn down this round) to your **Unpatched Zone**. If you have **no Ready dice left**, you must instead **Destroy (return to box) `1` Unpatched die** of your choice!
3. **Snowball Recycle:** Place **all exited Red, Blue, and Green cubes** from the tray back into the **Staging Cup** for next round.

#### Step 2C: Check End Game Triggers
The game ends **immediately** (skipping Phase 3) if **either**:
* **Singularity** was triggered in Step 2A, **OR**
* **One or more players became Patient Zero** (Insolvent `< $0` or Breached `<= 0 Secrets`) in Step 2B.

---

### Phase 3: Corporate Operations (Clockwise Turns)

Starting with the First Player and proceeding clockwise, each player takes a single operations turn, performing any combination of the following actions in any order:

1. **Purchase Software Dice (Limit `2` dice per turn `[TUNE]`):**
   * Pay the `$` cost of any available Colored Die in the Market and place it directly into your **Ready Zone**.
2. **Patch Worn-Out Dice (Unlimited):**
   * Spend **`1 🔧` token** *or* pay **`$2`** `[TUNE: test $1–$3]` to move **1 die** from your **Unpatched Zone** back to your **Ready Zone**.
3. **Corrupt / Monetize the Rogue Agent ("Dirty Income" — Limit `1×` per turn):**
   * Gain **`$3`** `[TUNE: test $2–$4]` from the bank.
   * Take **`1 Black Cube`** + **`1 Attack Cube of your choice (Red, Blue, or Green)`** from the general supply and place both visibly into the **Staging Cup**.

After all players finish Phase 3:
* Return all non-worn dice to your **Ready Zone**.
* Keep all Money, Secrets, and up to **`3 🔧`** tokens.
* Pass the **First Player Marker** clockwise and begin the next round.

---

## 5. End Game & Victory Scoring

Calculate **Portfolio Value** `[TUNE weights]`:
* **`4 VP`** per remaining **Corporate Secret**
* **`3–5 VP`** per owned **Colored Module Die** *(Ready or Unpatched; Gray starter dice = `0 VP`)*
* **`1 VP`** per **`$2`** remaining *(rounded down)*

### Determining the Winner
* **Standard Ending (1+ Corporations Survive):** Any player who became **Patient Zero** (`< $0` debt or `<= 0` Secrets) is **eliminated**. The surviving player with the highest **Portfolio Value** wins! *(Tiebreakers: 1. Most Corporate Secrets, 2. Most Money.)*
* **Total Wipeout Ending (All Players Bust on the Same Drop):** Narrative victory belongs to the Rogue Agent! To rank the human players, subtract **Overflow Penalties** incurred on the final drop (`-4 VP` per Secret below 0, `-1 VP` per `$1` of unpaid debt, `-3 VP` per unfulfilled die destruction) from each player's Portfolio Value; highest net score takes top honors.

---

## 6. Prototype Reference Appendix (Dice & Cards)

### A. Software Dice Faces (`d6`) `[TUNE]`

| Die Type | Cost | VP | Face 1 | Face 2 | Face 3 | Face 4 | Face 5 | Face 6 |
| :--- | :---: | :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **Gray (Legacy)** | Starter | `0` | `Block 1 Any` | `Block 1 Any` | `+$1` | `+$1` | `+1 🔧` | `Idle (0)` |
| **Red (FinSec)** | `$4` | `3` | `Block 2 Red` | `Block 2 Red` | `+$2` | `+$2` | `Red ★` | `Red ★` |
| **Blue (Firewall)** | `$5` | `4` | `Block 2 Blue` | `Block 2 Blue` | `+$1` | `+1 🔧` | `Blue ★` | `Blue ★` |
| **Green (Antivirus)** | `$4` | `3` | `Block 2 Green` | `Block 2 Green` | `+2 🔧` | `+2 🔧` | `Green ★` | `Green ★` |
| **Yellow (Commercial)**| `$5` | `5` | `+$3` | `+$3` | `+$2` | `+$1 & +1 🔧` | `Yellow ★` | `Yellow ★` |
| **Purple (Black-Hat)** | `$4` | `3` | `Block 1 Any` | `Block 1 Any` | `+$2` | `+$1 & +1 🔧` | `Purple ★` | `Purple ★` |

### B. Sample Module Variant Cards (`★` Effects)
* **Red `★` Variants:**
  * *R1 — Ransom Insurance:* `Block 1 Red` + gain `+$2`.
  * *R2 — Threat Bounty:* `Block 2 Red`; if you take `0` unblocked Red damage this round, gain `+$2`.
  * *R3 — Short Squeeze:* Gain `+$3` (or `+$4` if 3+ Red cubes exit the tower this round).
* **Blue `★` Variants:**
  * *B1 — Honeypot Telemetry:* `Block 2 Blue`; if 1+ Blue cubes exit the tower and you take `0` Blue damage, gain `+$3`.
  * *B2 — Deep R&D Vault:* `Block 1 Blue`, **OR** pay `$2` during Phase 3 to gain `+1 Corporate Secret` (max 10).
  * *B3 — Air-Gapped Backup:* `Block 1 Blue` and this die does **not** move to Unpatched when blocking.
* **Green `★` Variants:**
  * *G1 — Self-Healing Kernel:* `Block 2 Green` + gain `+1 🔧`.
  * *G2 — Universal Sandbox:* `Block 1 Any` + gain `+1 🔧`.
  * *G3 — Live Reboot:* Gain `+2 🔧` + `+$1`.
* **Yellow `★` Variants:**
  * *Y1 — Algorithmic Trading:* Gain `+$4`, **OR** pay `$2` in Phase 3 to gain `+1 Corporate Secret`.
  * *Y2 — Cloud Monopoly:* Gain `+$2`, plus `+$1` per Yellow die you own (max `+$5`).
  * *Y3 — Proprietary Training:* Gain `+1 Corporate Secret`, then move this die to **Unpatched**.
* **Purple `★` Variants:**
  * *P1 — Zero-Day Injection:* Gain `+$2`; in Phase 3 you may add `1` Attack Cube (Red/Blue/Green) to the Staging Cup *(no Black cube added)*.
  * *P2 — Chaos Profiteer:* Gain `+$1` now, plus `+$2` per Black Cube that exits the tower in Phase 2.
  * *P3 — Packet Deflection:* `Block 2` of any single color; in Phase 3 add `1` cube of that color from the supply to the Staging Cup.

### C. Sample Rogue Agent Version Cards

| Version | Card Name | Staging Cup Payload | Active Directive |
| :--- | :--- | :--- | :--- |
| **`v1.0`** | *Script Kiddie* | `1 Red, 1 Blue, 1 Green` | None. |
| **`v1.0`** | *Data Scraper* | `2 Blue, 1 Red` | Players start with `+$1` extra Money. |
| **`v2.0`** | *Ransomware-as-a-Service* | `+2 Red, +1 Green` | If `1+` Red cubes exit the tower, Red Strength gets `+1`. |
| **`v2.0`** | *Polymorphic Worm* | `+2 Green, +1 Blue` | Cash Patching in Phase 3 costs `$3` instead of `$2` (`🔧` tokens unaffected). |
| **`v3.0`** | *Zero-Day Override* | `+1 Red, +1 Blue, +1 Green` | Each player's total Shield value in each active color is reduced by `1` (min 0). |
| **`v3.0`** | *Corrupted Kernel* | `+2 Red, +2 Blue` | Each Black Cube that exits the tower also adds `+1` Strength to the Attack Color with the most exited cubes this round. |
