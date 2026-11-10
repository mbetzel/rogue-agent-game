# Too Many Secrets — Rules Section 6 (v0.38.0)

Split out of `RULES.md`; this file is canonical for Section 6.

## 6. Prototype Reference Appendix (Dice & Cards)

### A. Software Dice Faces (`d6`) `[TUNE]`

| Die Type | Cost | Face 1 | Face 2 | Face 3 | Face 4 | Face 5 | Face 6 |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **Gray (Legacy)** | Starter (2) / Breakthrough | `Block 1 Any` | `Block 1 Any` | `+$1 & +1 🔬` | `+$1 / +1 🔬` | `+$1 / +1 🔬` | `+1 🔬` `[TUNE]` |
| **White (Contractor)** | Prog. `$1/$2/$3` | `Block 1 Any` | `Block 1 Any` | `Block 1 Any` | `+$1` | `Glitch` | `Glitch` |
| **Red (Marketing)** | `$4–$5` (Variant) | `+1 Market Share / +$1` | `+$2` | `+$2` | `+$2` | **Secret face** | `Red ★` |
| **Blue (Firewall)** | `$4–$6` (Variant) | `+1 🔬` | `+1 🔬` | `+$1` | `+1 🔬 / +$1` | **Secret face** | `Blue ★` |
| **Green (Antivirus)** | `$4–$5` (Variant) | `Clean 1 Glitched Shield Slot / +$1` | `+1 🔬` | `+2 🔬` | `+1 🔬 / +$1` | **Secret face** | `Green ★` |
| **Yellow (Commercial)**| `$5–$6` (Variant) | `+2 Market Share` | `+1 Market Share / +1 🔬` | `+$1 & +1 Market Share` | `+$2 / +1 🔬` | `+$2 / +1 🔬` | `Yellow ★` |
| **Purple (Specialist)** | Starter / Public Relations L3 | `Block 1 Any` | `Block 1 Any` | `+$2` | `+$1 & +1 🔬` | **Secret face** | `Purple ★ (Signature Protocol)` |

* **Choice Faces (`/`):** Faces with a slash (`/`) indicate a Choice Face. During Phase 1 Step 5, the player declares which of the two options the die fulfills for this round (e.g. `+1 Market Share / +$1`).
* **Shields:** Only Gray, White and Purple dice have shield faces, and every shield is `Block 1 Any`. Red, Blue, Green and Yellow dice have no shield faces.
* **Market Share Faces:** Red and Yellow Market Share outputs resolve in Phase 3: Income; they cannot raise Market Share above your maximum and do not count toward your Public Relations limit.
* **Secret Faces:** Face 5 on Red, Blue, Green and Purple dice. A die showing it after rerolls moves to the **Processing Box** with no other output and banks its Secret when it leaves (yields: Red `+2`; Blue `+1` / `+2` / `+3`; Green `3` minus your Glitched Shield Slots; Purple `+1`; see Phase 5 *Secret Face Yields*). It may be rerolled like any face. Yellow dice have no Secret face.
* **Glitch Faces (`Glitch`):** Only on White Contractor dice (Faces 5 & 6). A Contractor showing `Glitch` cannot be rerolled (except with Helix's Brute-Force Bypass) and is discarded to the general supply at the end of Phase 1 rerolls. Glitch faces produce 0 shields and 0 resource outputs.

### B. Sample Module Variant Cards (`★` Effects)
*(Timing: `[In Production — Income]` outputs are collected in **Phase 3: Income**; damage-conditional bonuses resolve in **Phase 4: Attack Resolution**; paid `[Phase 6 — Operations]` options resolve during your Operations Turn.)*
*(Note: Common market variant cards define Face 6 for Red, Blue, Green, and Yellow module dice. The purchase cost of each colored die is printed directly on its active face-up Variant Card. Purple Proprietary Specialist dice do not use market variant cards and cannot be purchased; their Face 6 is defined on the player's assigned White Hat Dossier detailed in Section 6D).*
* **Red `★` Variants:**
  * *R1 — Brand Protection (`$5`):* `[In Production — Income]` gain `+$2 & +1 Market Share` (in Phase 3; not above your maximum; does not count toward your Public Relations limit).
  * *R2 — Ad Campaign (`$4`):* No shield or Income output. `[In Production — Income]` If this die is still In Production in Phase 3, then `[Phase 6 — Operations]` you may pay `$2` `[TUNE]` during your Operations Turn to gain `+1` Market Share (not above your maximum; does not count toward your Public Relations limit; lost if unused by the end of your Operations Turn).
  * *R3 — Customer Poaching (`$5`):* No shield or Income output. `[In Production — Income]` In Phase 3, after all players collect Income, take `1` Market Share from the surviving rival with the most Market Share (you choose among tied rivals). If you are already at your maximum, the rival still loses `1` and you gain nothing (see Phase 3).
* **Blue `★` Variants:**
  * *B1 — Honeypot Telemetry (`$5`):* `[In Production — Income]` gain `+1 🔬`; if 1+ Blue cubes exit the tower and you take `0` Blue damage in Phase 4, gain `+$2` (this die must still be In Production in Phase 4).
  * *B2 — Deep R&D Vault (`$6`):* `[Phase 6 — Operations]` pay `$4` during Phase 6 to gain `+1 Corporate Secret` `[TUNE]`.
  * *B3 — Air-Gapped Backup (`$4`):* `[In Production — Income]` move `1` die from your **Processing Box** to your **Scanned Box** in Phase 3, banking its Secret `[TUNE]`.
* **Green `★` Variants:**
  * *G1 — Self-Healing Kernel (`$5`):* `Clean 1 Glitched Shield Slot` (in Phase 1 Step 5) + `[In Production — Income]` gain `+1 🔬`.
  * *G2 — Universal Sandbox (`$4`):* `Clean 1 Glitched Shield Slot` (in Phase 1 Step 5) + `[In Production — Income]` gain `+1 🔬`. *(Identical to G1 for now `[TUNE]`.)*
  * *G3 — Live Reboot (`$4`):* `[In Production — Income]` Gain `+2 🔬` + `+$1`.
* **Yellow `★` Variants:**
  * *Y1 — Algorithmic Trading (`$6`):* `[In Production — Income]` Gain `+$4`, **OR** `[Phase 6 — Operations]` pay `$2` in Phase 6 to gain `+1 Corporate Secret`.
  * *Y2 — Cloud Monopoly (`$5`):* `[In Production — Income]` Gain `+$2`, plus `+$1` per different colored module die you own (max `+$5`) `[TUNE]`.
  * *Y3 — Proprietary Training (`$5`):* `[In Production — Income]` Gain `+1 Corporate Secret` in Phase 3, then immediately move this die to the **Scanned Box** (before Phase 4 attacks).

### C. Sample SETEC Version Cards & Per-Version Corruption Tracks `[TUNE]`

Each Version Card defines its Corruption Track (`4` spaces on `v1.0`, `5` spaces on `v2.0`, `6` spaces on `v3.0`, consistent across all player counts). The Corruption Track is the **sole source of new SETEC cubes** entering the economy after setup. Two intensity profiles (**Standard** and **Aggressive**) are defined below for simulation benchmarking:

*(`Glitch X die / dice` spaces turn `X` of each affected player's shield slots into **Glitched Shield Slots**; no dice move. See Phase 2.)*

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

In `v0.38.0`, every Client Company starts with identical hardware (all 4 tracks at Level 0) and resources, except the color of its starting colored die; player identity comes from the Institutional Override (Client Company) and the Signature Protocol (White Hat Dossier).

#### 1. The 6 Client Companies (`Company`) — Institutional Overrides
Each player contracts with 1 enterprise Client Company for the duration of the match. Your company grants an Institutional Override that may be activated **once per SETEC Version** (`v1.0`, `v2.0`, `v3.0`); DTO *Slush Fund* is **once per game**. All companies start at Defense Capacity `2`, Triage Bandwidth `2`, Release Bandwidth `4`, all tracks Level 0, `$6`, `3` Secrets (2 players) or `4` (3–4 players), `13` Market Share (2 players), `16` (3 players) or `17` (4 players), `0 🔬`, and 2 Gray Legacy dice + 1 Purple die + 1 starting colored die of the company's color `[TUNE]` (Red: Meridian, Prometheus; Blue: DTO, Aegis; Green: Omnidyne, Helix), taken from that color's Central Market stack:

| Company Code | Company Name | Sector | Institutional Override | Timing Window | Description | Flavor Quote |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **MERIDIAN** | **Meridian Financial Trust** | Banking Infrastructure | *Redundant Crew* | Phase 1: Step 2 Staffing | Hire up to **2 White Contractor Dice for free** this round, bypassing progressive contractor costs. | *"When liquidity is limitless, headcount is merely an accounting variable."* |
| **OMNIDYNE** | **Omnidyne Systems** | Tech Giant | *Magnetic Splice* | Phase 5: Step 1 (Magnetic Splice) | Move **1 die** from your **Processing Box** directly to your **Ready for Release Zone** for **free** (bypassing Scanned); it banks its Secret now. | *"Proprietary hardware backplanes allow instantaneous hot-swapping under live load."* |
| **AEGIS** | **Aegis Defense Relay** | Security Firm | *Baffle Echo* | Phase 4: Attack Resolution | When resolving compiler damage, ignore **1 Attack Cube** (`Red`, `Blue`, or `Green`) of your choice for yourself this round. *(All exited cubes remain in the exit tray and recycle into the Staging Cup as normal).* | *"Multi-layered kinetic dampeners disperse inbound network blast energy."* |
| **DTO** | **Department of Telecommunications Oversight** | Federal Agency | *Slush Fund* | Phase 4: Attack Resolution (**once per game**) | The DTO accesses emergency black budget reserves: **Absorb up to 2 Corporate Secret loss** from unblocked Blue Spyware for free. *(Any additional Secret loss applies as normal).* | *"Classified black budget allocations absorb compliance failures without public oversight."* |
| **HELIX** | **Helix Biomedical Consortium** | Medical Research | *Brute-Force Bypass* | Phase 1: Step 4 Rerolls | Gain **1 extra free reroll** this phase, and you may include **any number of Glitch dice** in your free rerolls. In addition, turn **1 of your rolled dice to any legal non-Star face of its color** (the Secret face is allowed). | *"Massively parallel quantum sequencing breaks deterministic encryption gates."* |
| **PROMETHEUS** | **The Prometheus Foundation** | Non-Profit | *Algorithmic Arbitrage* | Phase 6: Operations Turn | Purchase **1 Colored Die** from the Central Market at a **`$2 discount`** (minimum cost `$0`), **OR** gain an immediate **`+$2` cash payout** from the bank. | *"Open-source cryptographic protocols circumvent proprietary enterprise licensing fees."* |

#### 2. The 6 White Hat Dossiers (`WhiteHat`) — Face 6 Signature Protocols
Each player is a specialist **White Hat Operative**. Your White Hat Dossier defines the **Signature Protocol** triggered whenever you roll Face 6 (`Purple ★`) on a Purple Specialist die. (Your 2nd Purple die waits in your **Personal Reserve** until the Public Relations Level 3 Breakthrough.)

| White Hat Code | Operative Name | Role | Signature Protocol | Timing Window | Description | Flavor Quote |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **OPERATOR** | **The Operator** | Tactical Staffing & Logistics Lead | *Contingent Staffing* | Phase 1: Step 4 Rolling | When Face 6 (`Purple ★`) is rolled, immediately roll **1 free White Contractor Die** from the supply directly into your active pool (eligible for all remaining rerolls this phase). | *"Redundant contractor pipelines ready on zero notice."* |
| **PHREAKER** | **The Phreaker** | Hardware Intrusion Specialist | *Jumper Diagnostics* | Phase 3: Income | When Face 6 (`Purple ★`) is rolled, move **1 die** from your **Processing Box** to your **Scanned Box**, banking its Secret now. If your Processing Box is empty, roll **1 Scanned Box die** and collect its `$` / `🔬` output (die remains in place); if Under Development is empty, collect **`+$1 cash`**. | *"Raw voltage pulses extract signal from dormant silicon."* |
| **ACOUSTIC** | **The Acoustic** | Side-Channel Cryptanalyst | *Resonance Sensor* | Phase 3: Income | When Face 6 (`Purple ★`) is rolled, gain **`+$1 cash`** per distinct cube color present in the Tower Exit Tray this round (`Red`, `Blue`, `Green`, `Black`; up to **`+$4`** max). | *"Harmonic resonance frequencies decode physical chassis vibrations."* |
| **SPOOK** | **The Spook** | Covert Intelligence Specialist | *Burn Notice* | Phase 3: Income | When Face 6 (`Purple ★`) is rolled, gain an immediate **`+$2` cash payout**; in addition, you may optionally **permanently return 1 owned colored module die to the market** to gain **`+1 Corporate Secret`**. | *"Scorched-earth protocols ensure zero forensic recovery."* |
| **PRODIGY** | **The Prodigy** | Autonomous Exploit Hacker | *Arbitrary Code Execution* | Phase 1: Step 4 Rolling | When Face 6 (`Purple ★`) is rolled, turn **1 other rolled die** in your active pool to **any legal non-Star face of that die's color** other than the Secret face. | *"Payload injection executes before memory boundaries establish."* |
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
