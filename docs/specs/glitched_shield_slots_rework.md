# Technical Architecture Specification: Glitched Shield Slots Rework, Defense Grid Overflow & 2P SETEC Black Cube (`v0.45.0`)

**Document ID:** `docs/specs/glitched_shield_slots_rework.md`  
**Author:** Principal Engineer  
**Date:** November 2026  
**Status:** Approved Architecture Specification (Ready for Implementation)  
**Target Baseline:** `v0.45.0` (Inherits `v0.44.0`)  
**Design Reference:** User-Approved 6-Change Architecture Directives  

---

## 1. Executive Summary & Design Scope

This specification formalizes the architecture, module contracts, state representations, invariants, telemetry fields, and unit test specifications for 6 user-approved rule and balance changes:

1. **WS-OPERATOR (*Logistics Bounty*):** Awards strictly `+1 🔬` Research Token per distinct die color currently in the player's **Scanned Box** (evaluating all software module die colors including Gray, Purple, and Yellow; `0 🔬` base).
2. **COMP-MERIDIAN (*Capital Injection*):** Cleans card text to `"Gain **+$3 Cash** from the bank."` (canonical Phase 3 `$3` cash payout confirmed in `sim/`).
3. **Phase 3 Die Ability Alignment:** Enforces the structural invariant that all software module dice abilities trigger strictly in **Phase 3: Income** (preserving core structural exceptions: Shield blocking in Phase 4, The Prodigy reroll/face modification in Phase 1 Step 4, and Secret face banking in Phase 5 Step 4). Audits and purges legacy non-Phase-3 triggers.
4. **Glitched Shield Slots Rework (*Defense Grid Overflow*):** Reworks shield slots to hold up to `2` Green cubes each. Incoming unblocked Green cubes distribute evenly across available slots (allocating to slots with the fewest Green cubes). A single generic shield assigned to a glitched slot purges **all** Green cubes in that slot in Phase 4. If all shield slots hold `2` Green cubes, subsequent unblocked Green cubes trigger **Defense Grid Overflow** (`-1 Corporate Secret` per overflow cube, capable of triggering a **Total Data Breach** / **Patient Zero**).
5. **Unified Starting Corporate Secrets:** Sets starting Corporate Secrets to flat `4` across all player counts (`2P: 4`, `3P: 4`, `4P: 4`), eliminating 2P fragility.
6. **2P SETEC Corp Neutral Black Cube:** Implements a neutral market competitor strictly in 2-player games. Starts at `0` Market Share. In Phase 4, if $\ge 1$ Red cube exits the Cube Tower tray, SETEC Corp advances `+1` Market Share (capped at `20`). Ranks in Market Share for the Market Leader Bonus (`+3 / +1`), absorbing places it achieves without scoring VP or triggering Market Collapse.

---

## 2. Exact Module Contracts & Architectural Specifications

### 2.1 WS-OPERATOR: Logistics Bounty Rework

#### 2.1.1 Rule Contract
- **White Hat Dossier:** The Operator (`WhiteHatCode.OPERATOR`).
- **Signature Protocol:** *Logistics Bounty*.
- **Timing Window:** Phase 3: Income.
- **Trigger:** Rolled Face 6 (`Purple ★`) on an active Purple Specialist die deployed In Production.
- **Output:** Awards strictly `+1 🔬` Research Token per distinct die color present in the player's **Scanned Box** at the time of resolution.
  $$\text{Gain 🔬} = T_{\text{purple\_star}} \times \left| \{ d.\text{color} \mid d \in \text{player.scanned\_dice} \} \right|$$
  where $T_{\text{purple\_star}}$ is the number of Purple ★ triggers resolved.
- **Color Inclusivity:** All software module die colors are valid: `DieColor.GRAY`, `DieColor.PURPLE`, `DieColor.RED`, `DieColor.BLUE`, `DieColor.GREEN`, `DieColor.YELLOW`.
- **Base Payout:** Strictly `0 🔬` base. If `len(player.scanned_dice) == 0`, gain is `0 🔬`.

#### 2.1.2 Module Signatures (`sim/engine/phase3_income.py`)
```python
def resolve_operator_logistics_bounty(player: PlayerState, triggers: int) -> int:
    """Awards +1 research per distinct die color currently in the Scanned Box per trigger."""
    if triggers <= 0 or not player.scanned_dice:
        return 0
    distinct_colors = len({d.color for d in player.scanned_dice})
    research_gain = triggers * distinct_colors
    if research_gain > 0:
        player.gain_research(research_gain, "signature_protocol")
    return research_gain
```

In `_die_income_row` and `preview_player_income`:
```python
elif _is_operative(player, WhiteHatCode.OPERATOR, legacy_bridge_enabled(state)):
    distinct_count = len({d.color for d in player.scanned_dice})
    research += distinct_count
    protocol_research = distinct_count
    star_note = f"Logistics Bounty (+{distinct_count} 🔬, {distinct_count} colors)"
```

---

### 2.2 COMP-MERIDIAN: Capital Injection Card Text Cleanup

#### 2.2.1 Rule & Card Contract
- **Company Dossier:** Meridian Financial Trust (`CompanyCode.MERIDIAN`).
- **Institutional Override:** *Capital Injection*.
- **Card Text Clean:** `"Gain **+$3 Cash** from the bank."`
- **Timing Window:** Phase 3: Income (usable once per SETEC Version: `v1.0`, `v2.0`, `v3.0`).
- **Verification in `sim/`:** Verified in `sim/engine/phase3_income.py` (`resolve_meridian_capital_injection`). The engine already executes `player.gain_money(3, "capital_injection")` guarded by `player.is_ability_available(active_ver)`. Card text in `RULES_APPENDIX.md` and quick reference docs is stripped of trailing `[TUNE]` markers.

---

### 2.3 Phase 3 Die Ability Alignment Audit & Architecture

#### 2.3.1 Architectural Invariant
All module dice abilities (standard faces and Variant Card `★` abilities) must execute within **Phase 3: Income**, with strictly three core structural exceptions:
1. **Generic Shields (`Block 1 Any`):** Resolved during **Phase 4: Attack Resolution** against exited Cube Tower Attack Cubes.
2. **The Prodigy (*Arbitrary Code Execution*):** Resolved during **Phase 1: Step 4 (Post-Rerolls)** to mutate 1 rolled active die face.
3. **Secret Faces (Face 5):** Transferred to the **Processing Box** during Phase 1 Step 4, banking Corporate Secrets upon exiting the Processing Box during **Phase 5: Step 4 / Conveyor Triage** (or via *Magnetic Splice* / *Jumper Diagnostics* / *Live Reboot*).

#### 2.3.2 Audit Findings & Legacy Decommissioning
- **Audit Result:** Module variant cards (Red `R1, R2, R3`, Blue `B1, B2, B3`, Green `G1, G2, G3`, Yellow `Y1, Y2, Y3`) and White Hat Signature Protocols (Operator, Phreaker, Acoustic, Spook, Cipher) resolve in Phase 3.
- **Decommissioning `phase6_operations.py` Legacy Branches:** Lines 226–249 of `sim/engine/phase6_operations.py` housed legacy `v0.33` Phase 6 resolution blocks for Spook *Burn Notice*, Phreaker *Jumper Diagnostics*, and `R2 Ad Campaign`. These legacy blocks are deprecated. All active card mechanics are routed through `sim/engine/phase3_income.py`.

---

### 2.4 Glitched Shield Slots Rework (`Defense Grid Overflow`)

#### 2.4.1 State Representation (`sim/engine/state.py` & `PlayerState`)
The scalar `player.glitched_shield_slots: int` is superseded by a structured slot array:
- `shield_slots: List[int] = field(default_factory=lambda: [1, 0])`
  - Length is strictly equal to `player.defense_capacity` (starts at 2, increases to 3 at Defense Grid L2, and 4 at Defense Grid L4).
  - Each slot index $s \in [0, \text{defense\_capacity} - 1]$ stores an integer count $c_s \in \{0, 1, 2\}$ representing Green cubes currently lodged in that slot.
- **Derived Properties:**
  - `clean_shield_slots_count -> int`: Count of slots with $c_s == 0$.
  - `glitched_shield_slots_count -> int`: Count of slots with $c_s \ge 1$ (preserves API compatibility for `G2 Universal Sandbox` and quick checks).
  - `total_green_cubes -> int`: Sum $\sum c_s$.
  - `max_green_capacity -> int`: $2 \times \text{defense\_capacity}$.

#### 2.4.2 Starting State & Capacity Upgrades
- **Initial Setup (All Players):**
  - Defense Grid Capacity = 2.
  - `shield_slots = [1, 0]` (Slot 0 holds 1 Green cube; Slot 1 holds 0 Green cubes).
  - Exactly 1 Glitched Shield Slot with 1 Green cube; 1 Clean Shield Slot.
- **Defense Grid Hardware Track Upgrades (`sim/engine/research_tracks.py`):**
  - When advancing to Level 2 (Capacity 2 $\to$ 3): Append `0` to `shield_slots` (`shield_slots.append(0)`).
  - When advancing to Level 4 (Capacity 3 $\to$ 4): Append `0` to `shield_slots` (`shield_slots.append(0)`).
  - Invariant: Newly gained Defense Grid shield slots always arrive **Clean** ($c_s = 0$).

#### 2.4.3 Even Cube Distribution Algorithm
When $K \ge 1$ unblocked Green cubes infect the player (from Phase 4 Attack Resolution or Corruption Track hazards):

```python
def apply_green_cube_infections(player: PlayerState, count: int) -> int:
    """Distributes incoming unblocked Green cubes evenly across slots (lowest count first).
    Triggers Defense Grid Overflow when all slots are at 2 cubes.
    Returns the number of overflow cubes."""
    overflow_count = 0
    for _ in range(count):
        min_cubes = min(player.shield_slots)
        if min_cubes < 2:
            # Deterministic: lowest index among slots tied for fewest cubes
            target_idx = player.shield_slots.index(min_cubes)
            player.shield_slots[target_idx] += 1
            player.slots_glitched_this_round += 1
        else:
            # Defense Grid Overflow Trigger
            overflow_count += 1
            trigger_defense_grid_overflow(player)
    return overflow_count
```

#### 2.4.4 Defense Grid Overflow Mechanics
- **Trigger:** An incoming unblocked Green cube arrives when all available shield slots already hold `2` Green cubes ($\min(\text{shield\_slots}) == 2$).
- **Resolution:**
  1. The cube cannot be absorbed by the Defense Grid and spills over.
  2. The player immediately loses `1 Corporate Secret`:
     `player.lose_secrets(1, "defense_grid_overflow")`
  3. If `player.secrets <= 0`: Player suffers an immediate **Total Data Breach** and becomes **Patient Zero** (or triggers a simultaneous **Total Wipeout** if all players breach).
  4. Telemetry fields updated: `player.defense_grid_overflows += 1`, `player.secrets_lost_to_overflow += 1`.

#### 2.4.5 Shield Assignment (Phase 1 Step 4) & Purge Resolution (Phase 4 Step 4.1)
- **Phase 1 Step 4 (Deploy):**
  - Rolled `Block 1 Any` dice can be committed to:
    - **Clean Slots:** Configured as `ProductionRole.CLEAN_SHIELD`. Maximum clean shields = count of clean slots ($c_s == 0$).
    - **Glitched Slots:** Configured as `ProductionRole.PURGING_SHIELD`. Maximum purging shields = count of glitched slots ($c_s \ge 1$).
  - Total committed shields $\le \text{defense\_capacity}$.
- **Phase 4 Step 4.1 (Purge Step):**
  - Before resolving Attack Cubes, each `PURGING_SHIELD` targets 1 glitched slot (prioritizing slots holding 2 Green cubes).
  - **All** Green cubes in that slot are purged ($c_s \to 0$), whether the slot held 1 or 2 Green cubes.
  - The purging shield die is consumed: moves to the **Scanned Box** (or discarded to supply if a temporary die). It does **not** block attack cubes in Phase 4 Step 4.2.
- **Non-Shield Slot Cleaners:**
  - *G1 Self-Healing Kernel* (Phase 3): Cleans 1 Glitched Shield Slot ($c_s \to 0$, targeting 2-cube slots first). If a purging shield was assigned to that slot in Phase 1, it is promoted to a `CLEAN_SHIELD` for Phase 4.
  - *Green Secret Face Banking* (Phase 5 Step 4): Cleans 1 Glitched Shield Slot ($c_s \to 0$, targeting 2-cube slots first).

#### 2.4.6 Bot Heuristics (`sim/bots/market_share_policy.py`)
- Bots prioritize `CLEAN_SHIELD` when expected unblocked Red/Blue attack cubes threaten critical damage.
- Bots prioritize `PURGING_SHIELD` when all shield slots hold $\ge 1$ Green cubes and incoming Green cubes threaten Defense Grid Overflow.
- When assigning purging shields to specific glitched slots, bots always select slots with `2` Green cubes over slots with `1` Green cube.

---

### 2.5 Unified Starting Corporate Secrets

#### 2.5.1 Baseline Configuration
Starting Corporate Secrets are set to flat `4` across all player counts:
```python
# sim/config.py
V045_STARTING_SECRETS: Dict[int, int] = {2: 4, 3: 4, 4: 4}
```
- **2P:** Bumped from `3` to `4`.
- **3P:** Maintained at `4`.
- **4P:** Maintained at `4`.
- Eliminates 2P early-game fragility where early Blue/Overflow damage triggered premature Patient Zero eliminations before engine ramp.

---

### 2.6 2P SETEC Corp Neutral Black Cube

#### 2.6.1 Scope & State Representation
- **Player Count Condition:** Active **strictly** in 2-player games (`num_players == 2`). In 3P and 4P games, this system is inactive.
- **State Field (`GameState`):**
  `setec_market_share: int = 0`
  - Range: `0` to `20` (bounded by `DEFAULT_MARKET_SHARE_MAX = 20`).
  - Represented physically by a neutral Black Cube on the central Public Relations / Market Share track.

#### 2.6.2 Phase 4 Trigger Condition
In **Phase 4: Attack Resolution**, after Cube Tower drop resolution:
- If $\ge 1$ Red Attack Cube exited the Cube Tower into the tray this round:
  $$\text{state.setec\_market\_share} = \min(20, \text{state.setec\_market\_share} + 1)$$
- Triggered solely by the presence of exited Red cubes in the tray ($\ge 1$), regardless of whether players block or suffer the Red damage.
- If `0` Red cubes exited the tray, SETEC Corp gains `0` Market Share.

#### 2.6.3 Market Leader Bonus Integration (`market_leader_bonus_awards`)
When evaluating Market Leader Bonus awards (Phase 5 Red Secret payout and Game End scoring):
- SETEC Corp enters the competition ranking as a participant with identifier `SETEC_CORP_ID = -1` and share `state.setec_market_share`.
- The 2P place schedule is `(3, 1)`.
- Ranking algorithm (Standard competition ranking: $1 + \sum [v > s]$):
  - **SETEC 1st, Player A 2nd, Player B 3rd:** SETEC takes 1st place. The 1st place award (`+3 Secrets`) is absorbed by SETEC Corp (discarded to bank). Player A receives 2nd place award (`+1 Secret`). Player B receives `+0`.
  - **SETEC tied with Player A for 1st:** Both share 1st place. Player A receives `+3 Secrets`. Player B is 3rd place (`+0`).
  - **Player A 1st, SETEC 2nd, Player B 3rd:** Player A receives `+3 Secrets`. SETEC absorbs 2nd place (`+1 Secret`). Player B is 3rd place (`+0`).
  - **Player A 1st, Player B 2nd, SETEC 3rd:** Player A receives `+3 Secrets`. Player B receives `+1 Secret`. SETEC receives `+0`.
- **Invariants:**
  - SETEC Corp never scores Corporate Secrets, never earns VP, and never wins.
  - SETEC Corp reaching `0` Market Share **never** triggers Market Collapse.
  - SETEC Corp cannot become Patient Zero.

---

## 3. Invariants & Guardrails

| Invariant ID | Target Subsystem | Formal Invariant Statement |
| :--- | :--- | :--- |
| `INV-OP-01` | WS-OPERATOR | Logistics Bounty yields strictly $+1 🔬$ per distinct die color in Scanned Box; empty Scanned Box yields $0 🔬$. |
| `INV-MER-01` | COMP-MERIDIAN | Capital Injection grants exactly $+\$3$ Cash once per SETEC Version in Phase 3. |
| `INV-P3-ALIGN-01` | Die Abilities | All module dice abilities resolve in Phase 3, except Shields (Phase 4), Prodigy (Phase 1 Step 4), and Secret banking (Phase 5 Step 4). |
| `INV-DGO-01` | Defense Grid | Each shield slot holds $\in \{0, 1, 2\}$ Green cubes; total capacity equals $2 \times \text{defense\_capacity}$. |
| `INV-DGO-02` | Defense Grid | Incoming Green cubes allocate to an available slot with the minimum Green cubes (lowest index on tie). |
| `INV-DGO-03` | Defense Grid Overflow | An unblocked Green cube arriving when all slots hold 2 Green cubes immediately deducts $1$ Corporate Secret. |
| `INV-DGO-04` | Glitched Slot Purge | Assigning 1 generic shield to a glitched slot purges all (1 or 2) Green cubes in that slot during Phase 4 Step 4.1. |
| `INV-START-SEC-01` | Starting Secrets | Starting Corporate Secrets equal exactly 4 across 2P, 3P, and 4P table counts. |
| `INV-SETEC-2P-01` | 2P SETEC Corp | SETEC Corp is active strictly in 2-player games and starts at 0 Market Share. |
| `INV-SETEC-2P-02` | 2P SETEC Advance | SETEC Corp advances $+1$ Market Share in Phase 4 iff $\ge 1$ Red cube exited the Cube Tower tray (clamped at 20). |
| `INV-SETEC-2P-03` | 2P SETEC Bonus Absorption | SETEC Corp competes for Market Leader Bonus places; any bonus assigned to SETEC is absorbed and not awarded to players. |
| `INV-SETEC-2P-04` | 2P SETEC Immunity | SETEC Corp cannot trigger Market Collapse, cannot suffer Data Breach, and cannot score VP. |

---

## 4. Telemetry & Data Logging

The following telemetry fields are added to `TelemetryData` and `PlayerState`:

```python
# --- sim/engine/state.py ---

# Per-Player Telemetry
operator_scanned_colors_count: int = 0       # Number of distinct scanned colors evaluated by Operator
operator_research_harvested: int = 0         # Total research tokens awarded by Logistics Bounty
defense_grid_overflow_count: int = 0         # Number of Defense Grid Overflow events triggered
secrets_lost_to_overflow: int = 0            # Total Corporate Secrets lost to overflow
slots_purged_by_shields_total: int = 0       # Number of glitched slots completely purged by shields
cubes_purged_by_shields_total: int = 0       # Total Green cubes removed by purging shields

# Global Telemetry (GameState / TelemetryData)
setec_corp_active: bool = False              # True strictly in 2P games
setec_corp_final_market_share: int = 0       # SETEC Corp market share at game end
setec_corp_advances_total: int = 0           # Count of rounds SETEC gained +1 MS
setec_corp_mlb_1st_places: int = 0           # Count of times SETEC took 1st place in MLB
setec_corp_mlb_2nd_places: int = 0           # Count of times SETEC took 2nd place in MLB
setec_corp_mlb_secrets_absorbed: int = 0     # Total Secret VP absorbed by SETEC Corp
```

---

## 5. Unit Test Specifications

| Test ID | Target Function / Invariant | Covered Invariant | Expected Outcome |
| :--- | :--- | :--- | :--- |
| `TEST-OP-01` | `test_operator_empty_scanned_box` | `INV-OP-01` | Scanned Box empty $\implies$ $0 🔬$ awarded. |
| `TEST-OP-02` | `test_operator_duplicate_colors` | `INV-OP-01` | Scanned Box `[Gray, Gray, Purple]` $\implies$ 2 colors $\implies +2 🔬$. |
| `TEST-OP-03` | `test_operator_all_colors_inclusive` | `INV-OP-01` | Scanned Box with Gray, Purple, Red, Blue, Green, Yellow $\implies 6$ colors $\implies +6 🔬$. |
| `TEST-MER-01` | `test_meridian_capital_injection_clean` | `INV-MER-01` | Meridian earns exactly $+\$3$ Cash in Phase 3; card text has no `[TUNE]` tag. |
| `TEST-P3-01` | `test_phase3_die_abilities_exclusive` | `INV-P3-ALIGN-01` | Asserts no variant card or operative protocol triggers outside Phase 3 (except Shield, Prodigy, Secrets). |
| `TEST-DGO-01` | `test_initial_shield_slot_state` | `INV-DGO-01` | Player starts with `[1, 0]` (1 glitched slot with 1 cube, 1 clean slot). |
| `TEST-DGO-02` | `test_even_cube_distribution` | `INV-DGO-02` | Slots `[1, 0]` + 1 Green cube $\implies$ `[1, 1]`. Another Green cube $\implies$ `[2, 1]`. |
| `TEST-DGO-03` | `test_defense_grid_overflow_trigger` | `INV-DGO-03` | Slots `[2, 2]` + 1 Green cube $\implies$ Slots remain `[2, 2]`, player loses 1 Secret. |
| `TEST-DGO-04` | `test_defense_grid_overflow_wipeout` | `INV-DGO-03` | Player at 1 Secret suffering overflow drops to 0 Secrets and becomes Patient Zero. |
| `TEST-DGO-05` | `test_purging_shield_clears_all_cubes` | `INV-DGO-04` | Assigning 1 Shield to a slot with 2 Green cubes clears both cubes to 0. |
| `TEST-DGO-06` | `test_capacity_upgrade_arrives_clean` | `INV-DGO-01` | Defense Grid advancing to Level 2 expands slots from `[c0, c1]` to `[c0, c1, 0]`. |
| `TEST-SEC-01` | `test_starting_secrets_flat_4` | `INV-START-SEC-01` | 2P, 3P, and 4P configurations all initialize players with 4 Corporate Secrets. |
| `TEST-SET-01` | `test_setec_corp_inactive_in_3p_4p` | `INV-SETEC-2P-01` | SETEC Corp is disabled when `num_players >= 3`. |
| `TEST-SET-02` | `test_setec_corp_phase4_red_advance` | `INV-SETEC-2P-02` | 2P: 1+ Red exited $\implies$ SETEC MS $+1$. 0 Red exited $\implies$ SETEC MS $+0$. |
| `TEST-SET-03` | `test_setec_corp_absorbs_mlb_first` | `INV-SETEC-2P-03` | SETEC MS 15, P1 MS 12, P2 MS 10 $\implies$ SETEC takes 1st (+3 absorbed), P1 gets +1, P2 gets +0. |
| `TEST-SET-04` | `test_setec_corp_tied_first_shares_place`| `INV-SETEC-2P-03` | SETEC MS 14, P1 MS 14, P2 MS 10 $\implies$ P1 shares 1st (+3), P2 is 3rd (+0). |
| `TEST-SET-05` | `test_setec_corp_no_market_collapse` | `INV-SETEC-2P-04` | SETEC Corp at 0 Market Share does not trigger Market Collapse. |
