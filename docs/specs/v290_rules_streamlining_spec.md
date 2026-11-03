# Technical Architecture Specification: Phase 36 (v0.29.0)
## Rules Streamlining, Decoupled Pipeline Tracks & CI/CD Player Board Wireframe

**Author:** Principal Engineer / Architect  
**Status:** Approved for Implementation  
**Target Version:** `v0.29.0` Baseline  
**Dependencies:** [RULES.md](../../RULES.md), [PLAN.md](../../PLAN.md), [v280_terminal_upgrades_spec.md](./v280_terminal_upgrades_spec.md)  
**Target Components:**
- `sim/config.py`
- `sim/entities.py`
- `sim/engine/state.py`
- `sim/engine/phase1_boot.py`
- `sim/engine/phase2_threat.py`
- `sim/engine/phase3_ops.py`
- `sim/engine/core.py`
- `sim/bots/base.py` & all bot subclasses (`sim/bots/*.py`)
- `web/schemas.py`
- `web/controller/` (`core.py`, `capabilities.py`, `phase1_actions.py`, `phase3_actions.py`, `serializer.py`)
- `web/static/js/` (`components/player_mats.js`, `components/action_dock.js`, `components/modals.js`, `api.js`)
- `tests/test_v290_rules_streamlining.py`
- `pnp/generate_pnp.py` & `pnp/pdf_engine.py`

---

## 1. Executive Summary & Architectural Motivation

### 1.1 Context & Strategic Objectives
Following the successful deployment and Monte Carlo validation of Phase 35 (`v0.28.0`), player terminal agency transitioned from an artificial monetary throttle to physical hardware constraints (Defense Capacity and Pipeline Bandwidth). However, thorough systems analysis and tabletop ergonomics review identified six areas where leftover mechanical legacy burdened play with unnecessary friction:

1. **Mid-Drop Version Upgrades Disrupting Phase 2/3 Ability Timing:**  
   Advancing SETEC mid-drop in Step 2A immediately forfeited the active version's Institutional Override before players could utilize defensive overrides (e.g., Aegis *Baffle Echo* or DTO *Slush Fund* in Step 2B) or Phase 3 operational overrides (Omnidyne *Magnetic Splice* or Prometheus *Algorithmic Arbitrage*). Transitioning version cards at the start of the next round—while allowing Black cube overflow to mark the upcoming track immediately—preserves player foresight and intentionality.
2. **Cryptographic Hash Match Procedural Overhead:**  
   The 3-of-a-kind triplet matching rule in Phase 1 Step 5 generated outsized cognitive load and Yahtzee-style dice-sorting friction without driving thematic strategic decisions. Removing Hash Matches cleanses Phase 1 Step 5 into pure assignment to Shields vs Income, and frees The Cipher's Face 6 to be an intuitive, predictable resource engine.
3. **Phase Lock Spaces & Reroll Friction:**  
   Phase lock spaces (locking Cash, Research, or Shield faces during next Phase 1 rerolls) introduced asymmetric round-to-round state baggage (`LockType`), disproportionately punished unlucky rolls, and required specialized exception code in bots, web UI, and physical cards. Replacing these spaces with direct kinetic and glitch friction restores immediacy to the threat track.
4. **Coupled Pipeline Upgrade Track:**  
   In `v0.28.0`, Triage Bandwidth (Glitched $\to$ Scanned) and Release Bandwidth (Scanned $\to$ Ready) were bound to a single monolithic "Pipeline" track. This coupling masked the distinct physical bottlenecks of quarantine triage versus release deployment, and forced reliance on an ad-hoc "fast-patching" token spending mechanism in Phase 3B. Decoupling the track into dedicated **Triage** and **Release** tracks establishes clean, independent progression and completely eliminates fast-patching.
5. **CI/CD Physical Mat Ergonomics:**  
   Previous player mats arrayed hardware upgrade tracks in an isolated side panel disconnected from the physical dice zones. Embedding upgrade tracks directly inside or between the physical dice zones they govern creates an intuitive, self-documenting CI/CD conveyor loop.

---

## 2. Invariant Specifications

### `INV-VER-SWITCH-01`: Start-of-Round Version Switch & Immediate Spillover
- When the final space of an active Version's Corruption Track (`v1.0` Space 4, `v2.0` Space 5) is covered by a Black cube during Phase 2 Step 2A:
  1. The space's printed effect executes immediately.
  2. Any excess Black cubes dropped in the same compile step **immediately spill over** onto the next Version's Corruption Track (starting at Space 1), triggering each newly covered space's printed effect in sequence.
  3. The **active version card remains the current version** for the remainder of the current round.
  4. Any unused Institutional Override for the current version **remains available and legal** to activate during Phase 2B (defensive overrides) and Phase 3 (operational overrides) of the current round. The new version's Institutional Override is **NOT** unlocked yet.
  5. At the **start of the subsequent round** (in Phase 1 Boot, before contractor staffing or rolling):
     - The game engine officially executes the version switch (`current_version_index += 1`).
     - Any unspent Institutional Override from the old version is forfeited (`mark_ability_forfeited`).
     - The new version's Institutional Override slot unlocks to `AVAILABLE`.
- **Singularity Exception:** When Space 6 of `v3.0` is covered, **Singularity triggers IMMEDIATELY**. Step 2B resolves normally, and the current round is declared the final round.

### `INV-HASH-EXCISE-01`: Excision of Cryptographic Hash Matching
- The Cryptographic Hash Match mechanic (gaining +1 Secret per triplet of identical signatures in Phase 1 Step 5) is completely excised from the rules and engine.
- Dice roll outputs are strictly evaluated for their individual face values. Phase 1 Step 5 consists solely of assigning dice to **Shields** (subject to Defense Grid Capacity) or **Income**.
- State tracking for `hash_matches_secrets` is deprecated and removed.

### `INV-CIPHER-FACE6-01`: The Cipher Signature Protocol (Option A: Algorithmic Parity)
- The Cipher's Face 6 Protocol (*Algorithmic Parity*) is decoupled from Hash Matches.
- When Face 6 (`Purple ★`) is rolled on a Purple Specialist die by a player contracting with The Cipher:
  - **Timing:** Phase 3: Part 3A Operations Turn (Income Collection).
  - **Output:** Yields **`+$2` Cash** AND **`+1 🔬` Research Token**.
  - It does not act as a wildcard in Phase 1 Step 5.

### `INV-CORRUPT-CHOICE-01`: Free Choice of Glitched Dice from In Production
- When a Corruption Track space instructs *"All Players Glitch X Dice"*:
  - Each player chooses any $X$ active dice currently in their **In Production** area (Income or Shields) to move to the **Glitched Box** in **Under Development**.
  - There is **no mandatory priority** forcing Income dice to be glitched before Shields.
  - Players may freely choose to glitch a redundant shield die (e.g., a Blue shield when 0 Blue cubes dropped) while keeping their valuable income dice intact.
  - If a shield die is chosen and moved to Glitched, its defensive block commitment is removed immediately (affecting subsequent Step 2B resolution if glitched prior to defense calculation).

### `INV-LOCK-EXCISE-01`: Complete Excision of Phase Lock Spaces & Next-Round Locks
- All next-phase face locking effects (`Lock Cash`, `Lock Research`, `Lock Shields`) are completely excised.
- The `LockType` enumeration and the `next_phase_lock` attribute on `CorruptionSpace` are eliminated.
- The replaced track spaces across Standard (Profile 1) and Aggressive (Profile 2) tracks are:
  - **`v2.0 RaaS` Space 3:** Replaced with **"All lose $2 & Add 1 Red"** (`lose_money=2, add_cubes={RED: 1}`).
  - **`v2.0 Polymorphic Worm` Space 3:** Replaced with **"All glitch 1 die & Add 1 Green"** (`demote_dice=1, add_cubes={GREEN: 1}`).
  - **`v3.0 Zero-Day Override` Space 4:** Replaced with **"All glitch 1 die & Add 1 Blue, 1 Black"** (`demote_dice=1, add_cubes={BLUE: 1, BLACK: 1}`).
- In Phase 1 Step 4, Yahtzee rerolls are subject only to the standard rule that rolled `Glitch (Locked)` faces cannot be rerolled. No face types are ever locked by corruption tracks.

### `INV-TERMINOLOGY-01`: Terminology Standardization
- The legacy terms *"Zero Dice Wear"* and *"Cash-Only Ransom"* are deprecated from canonical rules documentation, web copy, and print assets:
  - Shields absorb attack cubes cleanly without wear (dice do not degrade when blocking).
  - Ransomware damage is simply paid in cash ($1 per unblocked Red cube; unpaid ransom leaks directly to Corporate Secrets).

### `INV-TRIAGE-TRACK-01`: Decoupled Triage Track Progression
- The terminal mat features an independent **Triage Track** governing Phase 3B Step 4 Conveyor Triage (moving dice from `glitched_dice` to `scanned_dice`):
  - **Level 0 (Baseline):** Bandwidth = **`2` dice / round**.
  - **Level 1:** Bandwidth = **`3` dice / round**. Upgrade Cost: **`2 🔬`**.
  - **Level 2:** Bandwidth = **`4` dice / round** AND unlocks **Emergency Hotfix**. Upgrade Cost: **`3 🔬`**.
  - **Emergency Hotfix Capability:** In Phase 3B Step 1, the player moves **1 die** from `glitched_dice` directly to `ready_for_release_dice` for free.

### `INV-RELEASE-TRACK-01`: Decoupled Release Track Progression
- The terminal mat features an independent **Release Track** governing Phase 3B Step 2 Scanned Graduation (moving dice from `scanned_dice` to `ready_for_release_dice`):
  - **Level 0 (Baseline):** Bandwidth = **`4` dice / round**.
  - **Level 1:** Bandwidth = **`5` dice / round**. Upgrade Cost: **`2 🔬`**.
  - **Level 2:** Bandwidth = **`6` dice / round**. Upgrade Cost: **`3 🔬`**.

### `INV-DEF-GRID-01`: Defense Grid Capacity Track Progression
- The Defense Grid Track on the terminal mat governs Phase 1 Step 5 Shield Commitments:
  - **Level 0 (Baseline):** Capacity = **`2` shields**.
  - **Level 1:** Capacity = **`3` shields**. Upgrade Cost: **`2 🔬`**.
  - **Level 2:** Capacity = **`4` shields** AND grants **Passive Firewall**. Upgrade Cost: **`3 🔬`**.
  - **Passive Firewall Capability:** In Phase 2 Step 2B, absorbs **1 Attack Cube** (`Red`, `Blue`, or `Green`) of choice for free before resolving damage.

### `INV-PATENT-TRACK-01`: Cryptographic Patents Track Progression
- The Patents Track on the terminal mat governs the Phase 3A Patent Filing action:
  - **Level 0 (Baseline):** Patent Cost = **`4 🔬`**. (Generates +1 Secret).
  - **Level 1:** Patent Cost = **`3 🔬`**. Upgrade Cost: **`2 🔬`**. (Generates +1 Secret).
  - **Level 2:** Patent Cost = **`2 🔬`**. Upgrade Cost: **`3 🔬`**. (Generates +1 Secret AND **`+$1` Cash**).

### `INV-FASTPATCH-EXCISE-01`: Excision of Fast-Patching
- Fast-patching (spending `1 🔬` per die to move additional dice from Glitched to Scanned in Phase 3B) is completely excised.
- The `triage_bandwidth` value defined by the player's Triage Track level is the strict, insurmountable hardware throughput limit. Excess glitched dice must remain quarantined in `glitched_dice`.

### `INV-CORP-CONFIG-01`: 4-Track Corporate Starting Configurations
The 6 Client Companies are updated to configure starting baselines across the 4 independent tracks:
1. **Omnidyne Systems (`OMNIDYNE`):**
   - Defense Cap: `1` (Defense Level 0)
   - Triage Bandwidth: `3` (Starts at **Triage Level 1**)
   - Release Bandwidth: `5` (Starts at **Release Level 1**)
   - Patent Cost: `4 🔬` (Patent Level 0)
   - Track Levels: `triage_level=1, release_level=1, defense_level=0, patent_level=0`
   - Bonus: None. Override: *Magnetic Splice* (Phase 3B: move 1 die from Glitched directly to Ready for free).
2. **Aegis Defense Relay (`AEGIS`):**
   - Defense Cap: `3` (Starts at **Defense Level 1**)
   - Triage Bandwidth: `1` (Restricted baseline)
   - Release Bandwidth: `3` (Restricted baseline)
   - Patent Cost: `4 🔬` (Patent Level 0)
   - Track Levels: `triage_level=0, release_level=0, defense_level=1, patent_level=0`
   - Bonus: None. Override: *Baffle Echo* (Phase 2B: ignore 1 attack cube).
3. **Meridian Financial Trust (`MERIDIAN`):**
   - Defense Cap: `2` (Defense Level 0)
   - Triage Bandwidth: `2` (Triage Level 0)
   - Release Bandwidth: `4` (Release Level 0)
   - Patent Cost: `4 🔬` (Patent Level 0)
   - Track Levels: `triage_level=0, release_level=0, defense_level=0, patent_level=0`
   - Bonus: **`+$2` Starting Cash** (`$6` total). Override: *Redundant Crew* (Phase 1: hire 2 contractors free).
4. **Helix Biomedical Consortium (`HELIX`):**
   - Defense Cap: `2` (Defense Level 0)
   - Triage Bandwidth: `2` (Triage Level 0)
   - Release Bandwidth: `4` (Release Level 0)
   - Patent Cost: `3 🔬` (Starts at **Patent Level 1**)
   - Track Levels: `triage_level=0, release_level=0, defense_level=0, patent_level=1`
   - Bonus: **`+2 🔬` Starting Research** (`4 🔬` total). Override: *Brute-Force Bypass* (Phase 1: reroll locked dice, set 1 face).
5. **Department of Telecommunications Oversight (`DTO`):**
   - Defense Cap: `2` (Defense Level 0)
   - Triage Bandwidth: `2` (Triage Level 0)
   - Release Bandwidth: `4` (Release Level 0)
   - Patent Cost: `4 🔬` (Patent Level 0)
   - Track Levels: `triage_level=0, release_level=0, defense_level=0, patent_level=0`
   - Bonus: **`+1` Starting Secret**. Override: *Slush Fund* (Phase 2B: absorb up to 2 Secret loss).
6. **The Prometheus Foundation (`PROMETHEUS`):**
   - Defense Cap: `2` (Defense Level 0)
   - Triage Bandwidth: `2` (Triage Level 0)
   - Release Bandwidth: `4` (Release Level 0)
   - Patent Cost: `4 🔬` (Patent Level 0)
   - Track Levels: `triage_level=0, release_level=0, defense_level=0, patent_level=0`
   - Permanent Trait: **`-1 🔬` Upgrade Discount** on all 4 hardware tracks (min cost `1 🔬`). Override: *Algorithmic Arbitrage* (Phase 3A: $2 discount on die purchase OR +$2 cash).

---

## 3. Data Model Changes & Dataclass Schemas

### 3.1 `sim/entities.py`

#### Updated `CorruptionSpace` Dataclass
Remove `next_phase_lock`:
```python
@dataclass(frozen=True)
class CorruptionSpace:
    """Represents a single space on a Version Corruption Track (RULES.md Section 6C)."""

    index: int  # 1-indexed space number on this version card (1..4, 1..5, or 1..6)
    label: str  # Human-readable summary
    add_cubes: Dict[CubeColor, int] = field(default_factory=dict)
    lose_money: int = 0
    lose_patches: int = 0  # Deducts research_tokens
    demote_dice: int = 0   # Glitches dice from In Production
    return_colored_dice: int = 0
    lose_secrets: int = 0
    is_upgrade: bool = False
    is_singularity: bool = False
```

#### Updated `Company` Dataclass
Decouple pipeline starting fields into separate triage and release fields:
```python
@dataclass(frozen=True)
class Company:
    """Represents a Client Company card contracting the terminal."""

    code: CompanyCode
    name: str
    sector: str
    override_name: str
    timing_window: str
    description: str
    flavor: str
    starting_defense_capacity: int = 2
    starting_triage_bandwidth: int = 2
    starting_release_bandwidth: int = 4
    starting_triage_level: int = 0
    starting_release_level: int = 0
    starting_defense_level: int = 0
    starting_patent_level: int = 0
    starting_cash_bonus: int = 0
    starting_research_bonus: int = 0
    starting_secrets_bonus: int = 0
    upgrade_discount: int = 0
```

### 3.2 `sim/engine/state.py`

#### Updated `PlayerState` Dataclass
Replace `pipeline_level` with `triage_level` and `release_level`. Baseline release bandwidth defaults to 4:
```python
@dataclass
class PlayerState:
    player_id: int
    bot: BaseBot
    money: int
    secrets: int
    research_tokens: int = 0

    # --- CI/CD Pipeline & Hardware Bottlenecks (v0.29.0 Canonical) ---
    defense_capacity: int = 2
    triage_bandwidth: int = 2
    release_bandwidth: int = 4
    triage_level: int = 0       # 0, 1, 2
    release_level: int = 0      # 0, 1, 2
    defense_level: int = 0      # 0, 1, 2
    patent_level: int = 0       # 0, 1, 2
    has_emergency_hotfix: bool = False
    has_passive_firewall: bool = False
    upgrade_discount: int = 0

    # --- CI/CD Pipeline Zones ---
    ready_for_release_dice: List[Die] = field(default_factory=list)
    in_production_dice: List[Die] = field(default_factory=list)
    glitched_dice: List[Die] = field(default_factory=list)
    scanned_dice: List[Die] = field(default_factory=list)
    contractor_dice: List[Die] = field(default_factory=list)
    hired_contractor_count: int = 0

    # --- Personal Reserve ---
    personal_purple_reserve: int = 2
    purple_star_available: bool = False
    purple_star_count: int = 0

    # --- Deprecated & Removed Fields ---
    # hash_matches_secrets is excised
    # total_fast_patches is excised
    # pipeline_level is replaced by triage_level and release_level
```

#### Updated `GameState` Tracking
Track pending version transitions at the start of rounds:
```python
@dataclass
class GameState:
    # Existing fields...
    corruption_track: int = 0
    corruption_track_capacity: int = 4
    pending_version_advance: bool = False
    overflow_black_cubes_on_next_track: int = 0
```

---

## 4. State Machine & Execution Flow Transitions

### 4.1 Phase 1 Boot: Version Switch Execution
In `sim/engine/phase1_boot.py`, immediately at the start of Phase 1 before Contractor dice are hired:
```python
def check_and_execute_start_of_round_version_transition(engine: GameEngine) -> bool:
    """Executes pending version switch from previous round's filled track (INV-VER-SWITCH-01)."""
    if not engine.state.pending_version_advance:
        return False

    old_version_str = engine.state.active_version.version_str
    engine.state.current_version_index += 1
    new_version_str = engine.state.active_version.version_str

    # Forfeit unused old ability, unlock new ability
    for p in engine.state.players:
        p.mark_ability_forfeited(old_version_str)
        p.unlock_version_ability(new_version_str)

    # Initialize new track with spilled-over cubes
    engine.state.corruption_track = engine.state.overflow_black_cubes_on_next_track
    engine.state.corruption_track_capacity = engine.state.active_version.track_capacity
    engine.state.overflow_black_cubes_on_next_track = 0
    engine.state.pending_version_advance = False
    return True
```

### 4.2 Phase 1 Step 4 & 5: Streamlined Rerolls & Deployment
1. **Rerolls (Step 4):**
   - Players roll Ready dice + Contractor dice.
   - Up to 2 rerolls. Only rolled `Glitch (Locked)` faces cannot be rerolled.
   - Zero phase lock checks (Cash, Shield, Research are never locked).
2. **Deployment (Step 5):**
   - Unresolved glitches move immediately to `glitched_dice` (or Contractor dice discarded).
   - Cryptographic Hash Match check is skipped completely.
   - Shield dice are assigned to Red, Blue, Green shields up to `defense_capacity`.
   - Remaining dice are assigned to Income.

### 4.3 Phase 2 Step 2A: Threat Resolution & Immediate Spillover
In `sim/engine/phase2_threat.py`:
```python
black_dropped = exited_cubes.get(CubeColor.BLACK, 0)
for _ in range(black_dropped):
    if not engine.state.pending_version_advance:
        engine.state.corruption_track += 1
        curr_track = engine.state.active_version.corruption_track
        space_idx = engine.state.corruption_track
        if curr_track and 1 <= space_idx <= len(curr_track):
            resolve_corruption_space(engine, curr_track[space_idx - 1], player_commitments, exited_cubes)

        if engine.state.corruption_track >= engine.state.corruption_track_capacity:
            if engine.state.current_version_index >= len(engine.state.version_deck) - 1:
                # Singularity is IMMEDIATE on v3.0 Space 6
                engine.state.singularity_triggered = True
                break
            else:
                # Mark pending advance for next round start; excess cubes spill over
                engine.state.pending_version_advance = True
                engine.state.overflow_black_cubes_on_next_track = 0
    else:
        # Excess cubes spill over onto the upcoming version's track immediately!
        engine.state.overflow_black_cubes_on_next_track += 1
        next_ver = engine.state.version_deck[engine.state.current_version_index + 1]
        spill_idx = engine.state.overflow_black_cubes_on_next_track
        if next_ver.corruption_track and 1 <= spill_idx <= len(next_ver.corruption_track):
            resolve_corruption_space(engine, next_ver.corruption_track[spill_idx - 1], player_commitments, exited_cubes)
```

### 4.4 Phase 2 Step 2A Corruption Space Free Choice Glitching
In `resolve_corruption_space`:
- When `space.demote_dice > 0`:
  - Each player selects $N$ dice from `in_production_dice`.
  - The player may select any die in In Production, whether in Income or in Shields.
  - If a Shield die is selected, its shield block is removed.
  - Selected dice move to `glitched_dice`.

### 4.5 Phase 3 Part 3A: Operations Turns
Surviving players execute in clockwise order:
1. **Income Collection:**
   - Collect Cash and Research from dice in In Production.
   - If The Cipher Face 6 was rolled, collect an additional `+$2` Cash and `+1 🔬` Research.
2. **Hardware Upgrades:**
   - Upgrade any of the 4 tracks (`triage`, `release`, `defense`, `patent`) by spending Research tokens.
   - Base cost: Level 1 costs `2 🔬`, Level 2 costs `3 🔬` (Prometheus receives `-1 🔬` discount).
3. **Patent Filings:**
   - Spend Research tokens equal to current patent cost (`4 / 3 / 2 🔬`) to gain +1 Corporate Secret (and +$1 cash at Level 2).
4. **Dice Purchases:**
   - Buy up to 2 dice (Central Market or Personal Reserve).

### 4.6 Phase 3 Part 3B: Pipeline Prep (Simultaneous)
1. **Emergency Hotfix:** If `has_emergency_hotfix` is True (Triage Track Level 2), move 1 die from `glitched_dice` directly to `ready_for_release_dice`.
2. **Scanned Graduation:** Move up to `release_bandwidth` dice (`4 / 5 / 6`) from `scanned_dice` to `ready_for_release_dice`.
3. **Production Return:** Move all surviving dice from `in_production_dice` to `ready_for_release_dice`.
4. **Conveyor Triage:** Move up to `triage_bandwidth` dice (`2 / 3 / 4`) from `glitched_dice` to `scanned_dice`.
5. *(Fast-patching is completely excised; no tokens can be spent here).*

---

## 5. CI/CD Player Board Physical & Web Wireframe Architecture

### 5.1 Physical Player Mat Layout Specifications
The terminal mat layout physically reflects the software deployment pipeline. Hardware upgrade tracks are directly embedded into the functional areas they modify:

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
|                                      |                                     |  Level 0: 4 dice                      |
|  +--------------------------------+  |                                     |  [ ] Level 1 (2 🔬): 5 dice           |
|  | WHITE HAT OPERATIVE DOSSIER    |  |                                     |  [ ] Level 2 (3 🔬): 6 dice           |
|  | - Operator / Phreaker / Spook  |  |                                     |                                       |
|  |   Acoustic / Prodigy / Cipher  |  |  +-----------------------------------------------------------------------+  |
|  | - Face 6 Signature Protocol    |  |  | 2. IN PRODUCTION (Deployed Dice)                                      |  |
|  | - Personal Reserve (2 Purple): |  |  |  +-----------------------------+  +---------------------------------+  |  |
|  |   [Die 1: $4]   [Die 2: $4]    |  |  |  | INCOME (Cash / Research / ★) |  | DEFENSE GRID (Shield Slots)     |  |  |
|  +--------------------------------+  |  |  |                             |  | [Red]    [Blue]   [Green]        |  |  |
|                                      |  |  |                             |  +---------------------------------+  |  |
|  +--------------------------------+  |  |  |                             |  | [EMBEDDED SHIELD UPGRADE]       |  |  |
|  | CORPORATE SECRETS TRACK (VP)   |  |  |  |                             |  | Cap 2 (Base)                    |  |  |
|  | [12][11][10][9][8][7][6][5]    |  |  |  |                             |  | [ ] Cap 3 (2 🔬)                |  |  |
|  | [ 4][ 3][ 2][ 1][ 0: BREACH! ] |  |  |  |                             |  | [ ] Cap 4 + Firewall (3 🔬)     |  |  |
|  +--------------------------------+  |  |  +-----------------------------+  +---------------------------------+  |  |
|                                      |  +-----------------------------------------------------------------------+  |
|  +--------------------------------+  |                                                                             |
|  | RESEARCH TOKENS (🔬 UNCAPPED)   |  |  +-----------------------------------------------------------------------+  |
|  | (Storage Bank)                 |  |  | 3. UNDER DEVELOPMENT (Offline Pipeline)                               |  |
|  +--------------------------------+  |  |  +-------------------+  [EMBEDDED TRIAGE]     +--------------------+  |  |
|                                      |  |  | GLITCHED BOX      |  Level 0: 2 dice       | SCANNED BOX        |  |  |
|  +--------------------------------+  |  |  | (Quarantined)     |  [ ] Lvl 1 (2 🔬): 3   | (Validated)        |  |  |
|  | LIQUID CASH ($)                |  |  |  |                   |  [ ] Lvl 2 (3 🔬): 4   |                    |  |  |
|  | (Storage Bank)                 |  |  |  |                   |      + Emergency Hotfix|                    |  |  |
|  +--------------------------------+  |  |  |                   |  ----------> --------->|                    |  |  |
|                                      |  |  +-------------------+                        +--------------------+  |  |
|  +--------------------------------+  |  +-----------------------------------------------------------------------+  |
|  | CRYPTOGRAPHIC PATENTS TRACK    |  |                                                                             |
|  | Base: 4 🔬 -> +1 Secret        |  |                                                                             |
|  | [ ] Lvl 1 (2 🔬): 3 🔬 -> +1   |  |                                                                             |
|  | [ ] Lvl 2 (3 🔬): 2 🔬 -> +1+$1|  |                                                                             |
|  +--------------------------------+  +-----------------------------------------------------------------------------+
```

### 5.2 Web UI Integration Architecture
In `web/static/js/components/player_mats.js`:
- The player card component is split into two primary CSS flex columns:
  - `.player-mat-left-col`: Contains Company badge with override button, White Hat badge with personal reserve status, Secrets badge, Research bank, Money bank, and the Patents Upgrade box.
  - `.player-mat-main-col`: Contains:
    - `.zone-ready`: Ready for Release dice container.
    - `.release-bridge-track`: Vertical graduation bridge between Scanned and Ready with progress badges for Release Bandwidth (4 $\to$ 5 $\to$ 6).
    - `.zone-production`: Split into `.production-income` and `.production-shields`. Embedded inside `.production-shields` is `.defense-grid-track` (Cap 2 $\to$ 3 $\to$ 4 + Passive Firewall).
    - `.zone-development`: Split into `.dev-glitched`, `.embedded-triage-track` (2 $\to$ 3 $\to$ 4 + Hotfix), and `.dev-scanned`.

---

## 6. Bot Heuristics & Decision Engine Updates

### 6.1 Excision of Lock Handling
- In `sim/bots/base.py` and bot subclasses:
  - Deprecate and remove all references to `phase_1_locks`, `LockType`, and locked face reroll restrictions.
  - Yahtzee reroll decision logic evaluates dice freely, subject only to `die.current_face.is_glitch`.

### 6.2 Glitch Selection Heuristic (Free Choice from In Production)
In `sim/bots/base.py`:
```python
def choose_dice_to_glitch(
    self,
    player: PlayerState,
    in_production_dice: List[Die],
    count: int,
    threat_strengths: Dict[CubeColor, int],
) -> List[Die]:
    """Selects count dice from In Production to glitch.
    Heuristic Priority:
    1. Redundant Shields: Shield dice where committed color threat is 0 or already over-blocked.
    2. Low-Value Income: Gray or low-cash income dice ($1).
    3. Essential Shields vs High Income: Preserves shields blocking lethal damage (Blue/Red),
       sacrificing non-critical income dice if necessary.
    """
    if len(in_production_dice) <= count:
        return list(in_production_dice)

    def sort_key(die: Die) -> Tuple[int, int]:
        face = die.effective_face
        # Redundant shield check
        if face and face.is_shield:
            color = face.shield_color
            threat = threat_strengths.get(color, 0)
            if threat == 0:
                return (0, 0)  # Redundant shield is prime sacrifice!
        # Low income next
        if face and face.money <= 1 and face.patches == 0 and not face.is_star:
            return (1, face.money)
        # Valuable income next
        if face and not face.is_shield:
            return (2, face.money + face.patches * 2)
        # Critical shield last
        return (3, 0)

    sorted_dice = sorted(in_production_dice, key=sort_key)
    return sorted_dice[:count]
```

### 6.3 Decoupled Track Upgrades
In `sim/bots/base.py`:
- `choose_track_upgrades` is updated to evaluate four independent track options:
  - `"defense"`: Priority increases as round number and attack cube count increase, especially if `defense_capacity <= 2`.
  - `"triage"`: High priority for Omnidyne or bots accumulating 3+ glitched dice.
  - `"release"`: High priority when dice pool exceeds 6 dice to avoid Scanned zone backlogs.
  - `"patent"`: Priority in late game (Rounds 6+) or when research is plentiful ($4+ \ 🔬$).

---

## 7. Web API Schemas & Controller Contracts

### 7.1 Web API Endpoints

#### POST `/api/game/action/upgrade_track`
Request Schema:
```json
{
  "player_id": 0,
  "track_type": "triage" | "release" | "defense" | "patent"
}
```
Validation:
- `track_type` must be one of `"triage"`, `"release"`, `"defense"`, `"patent"`.
- Current track level must be `< 2`.
- Player must possess sufficient `research_tokens` (accounting for Prometheus discount).

#### POST `/api/game/action/patent`
Request Schema:
```json
{
  "player_id": 0
}
```
Validation:
- Player must possess `research_tokens >= patent_cost`.
- Deducts `patent_cost`, increments `secrets` by 1. If `patent_level == 2`, increments `money` by 1.

### 7.2 Deprecated Endpoints & Fields
- Remove `/api/game/action/fast_patch`.
- Remove `phase_1_locks` from game state response.
- Remove `hash_matches_secrets` from player serialization.

---

## 8. Comprehensive Test Matrix

A dedicated test suite `tests/test_v290_rules_streamlining.py` must be authored to verify all architectural invariants:

| Test ID | Method Name | Invariant Covered | Verification Description |
| :--- | :--- | :--- | :--- |
| **TEST-V290-01** | `test_version_switch_start_of_round` | `INV-VER-SWITCH-01` | Verify that filling v1.0 Space 4 marks pending advance, leaves active version at v1.0 for Phase 2B/3, keeps v1 override usable in Phase 3, and transitions at start of next round. |
| **TEST-V290-02** | `test_black_cube_immediate_spillover` | `INV-VER-SWITCH-01` | Drop 3 Black cubes when v1.0 is at 3/4. Space 4 triggers, and 2 excess cubes trigger v2.0 Spaces 1 and 2 immediately. |
| **TEST-V290-03** | `test_v3_singularity_remains_immediate` | `INV-VER-SWITCH-01` | Covering v3.0 Space 6 triggers Singularity immediately in Step 2A without waiting for next round. |
| **TEST-V290-04** | `test_hash_matches_completely_removed` | `INV-HASH-EXCISE-01` | Roll 3 identical faces (e.g. three +$1 faces); verify zero corporate secrets awarded from hash matches. |
| **TEST-V290-05** | `test_cipher_face6_algorithmic_parity` | `INV-CIPHER-FACE6-01` | Roll Cipher Purple Face 6; verify Phase 3A income yields +$2 cash and +1 🔬 Research without hash matching. |
| **TEST-V290-06** | `test_corruption_space_free_choice_glitch` | `INV-CORRUPT-CHOICE-01` | Trigger glitch space; verify player can choose redundant shield die instead of income die. |
| **TEST-V290-07** | `test_replaced_phase_lock_spaces` | `INV-LOCK-EXCISE-01` | Verify v2.0 RaaS Space 3, Worm Space 3, and v3.0 Zero-Day Space 4 execute their new kinetic/glitch effects and zero phase locks occur. |
| **TEST-V290-08** | `test_decoupled_triage_track` | `INV-TRIAGE-TRACK-01` | Verify Triage Track Level 0 (2 dice), Level 1 (3 dice), Level 2 (4 dice + Emergency Hotfix). |
| **TEST-V290-09** | `test_decoupled_release_track` | `INV-RELEASE-TRACK-01` | Verify Release Track Level 0 (4 dice), Level 1 (5 dice), Level 2 (6 dice). |
| **TEST-V290-10** | `test_fast_patching_completely_excised` | `INV-FASTPATCH-EXCISE-01` | Verify that excess glitched dice beyond triage bandwidth cannot be fast-patched with research tokens. |
| **TEST-V290-11** | `test_corporate_starting_configs_4_tracks` | `INV-CORP-CONFIG-01` | Verify starting track levels and bandwidths for all 6 companies (Omnidyne 3/5, Aegis 1/3 with Def 3, Helix Patent 1, etc.). |
| **TEST-V290-12** | `test_web_api_four_track_upgrades` | `INV-UPGRADE-TRACK-01` | Verify web API `/api/game/action/upgrade_track` handles `"triage"` and `"release"` independently. |

---

## 9. Implementation Plan & Next Steps

1. **Senior Engineer Kickoff:**
   - Implement data models in `sim/entities.py`, `sim/config.py`, and `sim/engine/state.py`.
   - Update engine phases (`sim/engine/phase1_boot.py`, `phase2_threat.py`, `phase3_ops.py`).
   - Update bot heuristics in `sim/bots/`.
   - Update web schemas and controllers in `web/`.
   - Implement unit test suite `tests/test_v290_rules_streamlining.py`.
2. **Staff Engineer Code Review:**
   - Audit state machine transitions, version switch boundary conditions, and test coverage.
3. **Product Owner Scenario Sweep:**
   - Execute 3,000-match Monte Carlo sweep (`scripts/run_v290_telemetry_sweep.py`).
4. **Game Designer & Graphic Designer Follow-Through:**
   - Validate pacing and balance in `FINDINGS.md`.
   - Synchronize `RULES.md` and regenerate PnP PDF assets in `pnp/`.
