# Technical Architecture Specification: Dominant Cube Color Signature Attacks

**Document Version:** 1.0.0  
**Status:** Approved for Implementation (SDLC Architecture Phase)  
**Author:** Principal Engineer (`principal-engineer`)  
**Target Release:** `v0.43.0` (Phase 62: Dominant Cube Color Signature Attacks)  
**Dependencies:**
- [`GLOSSARY.md`](file:///home/mike/.gemini/antigravity/worktrees/rogue-agent/signature_cube_mechanics_balance/GLOSSARY.md)
- [`RULES.md`](file:///home/mike/.gemini/antigravity/worktrees/rogue-agent/signature_cube_mechanics_balance/RULES.md)
- [`RULES_APPENDIX.md`](file:///home/mike/.gemini/antigravity/worktrees/rogue-agent/signature_cube_mechanics_balance/RULES_APPENDIX.md)
- [`docs/specs/target_lock_signature_cubes_spec.md`](file:///home/mike/.gemini/antigravity/worktrees/rogue-agent/signature_cube_mechanics_balance/docs/specs/target_lock_signature_cubes_spec.md)
- [`docs/findings/signature_cube_mechanics_investigation.md`](file:///home/mike/.gemini/antigravity/worktrees/rogue-agent/signature_cube_mechanics_balance/docs/findings/signature_cube_mechanics_investigation.md)

**Target Codebase Modules:**
- `sim/config.py` (Configuration flags, preset tie order, candidate presets `v043()` / `v043_roster()`)
- `sim/engine/state.py` (New state fields: `PlayerState.encrypted_research_tracks`, telemetry dictionaries)
- `sim/engine/phase2_compiler.py` (Exited cube color evaluation, Compiler Drop signature detection)
- `sim/engine/phase4_attack_resolution.py` (Dominant color determination, Phase 4 timing, 4 color signature attacks)
- `sim/engine/research_tracks.py` (Research step cost doubling for encrypted tracks, clearance on upgrade)
- `sim/engine/phase5_operations.py` / `sim/engine/phase6_operations.py` (Track upgrade execution and encryption clearing)
- `sim/engine/phase5_pipeline_shift.py` (Gray Legacy die triage handling, 0-secret triage isolation)
- `sim/engine/fast_clone.py` (State synchronization, MCTS/search clone parity)
- `sim/bots/base.py` (Bot decision hooks: `choose_signature_red_recipient`, `choose_signature_green_tracks`, triage valuation)
- `tests/test_signature_dominant_attacks.py` (Comprehensive unit & integration test suite `TC-SIG-01`..`TC-SIG-14`)

---

## 1. Executive Summary & Architectural Motivation

### 1.1 Problem Statement & Background
In `v0.42.0` (Phase 61: Operative Signature Cube & Target Lock Protocol), a player's Signature Cube dropped through the physical Cube Tower during Phase 2 whenever they banked a Corporate Secret during Conveyor Triage (Phase 6 Step 4). If the cube exited into the Exit Tray, Project: SETEC established **Target Lock** on that player. In Phase 4, the locked player faced **`+1 dominant Attack Cube`** (`Red`, `Blue`, or `Green`), with ties broken by defending player choice (`INV-TL-01`).

While `v0.42.0` successfully linked secret-banking velocity to mainframe attention, empirical testing identified three core limitations:
1. **Color Monotony & Shield Redundancy:** Adding a `+1 Attack Cube` simply scaled numeric damage against standard `Block 1 Any` shields. At Defense Grid Level 4, players routinely over-defended to harvest cash (`+$1` cash per blocked cube, capped at `$3`), turning Target Lock into an economic asset rather than a palpable operational threat.
2. **Black Cube Physics Blind Spot:** In `v0.42.0`, Black (Corruption) Cubes in the Exit Tray were completely ignored for Target Lock calculations. Because Black Cubes do not recycle via Snowball Recycle and exit at high rates early in the game (16.0% unique top in Rounds 2–4), ignoring them squandered a prime thematic vector for Project: SETEC threat escalation.
3. **Absence of Differentiated Corporate Penalties:** Every extra cube resolved as generic damage (lost Market Share, lost Corporate Secrets, or glitched slots). The game lacked qualitative, color-specific subroutine attacks printed cleanly on the Central Board.

### 1.2 Approved Architecture: Dominant Cube Color Signature Attacks (`v0.43.0`)
Under `v0.43.0`, Target Lock replaces the generic `+1 Attack Cube` with **Dominant Cube Color Signature Attacks** printed directly on the Central Board reference matrix:
- **Attention Cycle Preserved (`INV-TL-03`):** Players start with `1` Operative Signature Cube (`IDLE_ON_MAT`). Banking $\ge 1$ Secret queues it to the `STAGING_CUP`. Phase 2 drop physics remain Model B (`SHOGUN_BAFFLE`). Exiting sets `player.target_locked = True` and returns the cube to `IDLE_ON_MAT`.
- **Full 4-Color Tray Evaluation (`INV-SIG-01`, `INV-SIG-02`):** When Target Lock resolves, the engine evaluates **all 4 Compiler Cube colors that exited into the Exit Tray in Phase 2** (`Red`, `Blue`, `Green`, `Black` from `cr.exited_cubes`).
- **Deterministic Preset Priority Order (`INV-SIG-01`):** Ties for the highest exited count are resolved deterministically via the Central Board top-to-bottom priority order:
  $$\mathbf{GREEN > BLACK > BLUE > RED}$$
- **Post-Defense Phase 4 Timing (`INV-SIG-03`):** Normal compiler attack cubes (`Red`, `Blue`, `Green`) and shields resolve first. Then, all surviving Target-Locked players resolve the dominant color Signature Attack **before** end-of-Phase-4 End Game Trigger checks.
- **The 4 Differentiated Signature Attacks:**
  1. **RED (`Market Manipulation` — `INV-SIG-RED`, `INV-SIMUL-RED`):** Two-Epoch simultaneous wealth transfer. Locked players lose `2` Market Share; eligible non-locked players with least Market Share gain `2`. All-locked drops cancel transfer cleanly.
  2. **BLUE (`Buffer Congestion` — `INV-SIG-BLUE`, `INV-SIG-BLUE-TRIAGE`):** Moves `1` Gray Legacy die from Scanned Box (or In Production / Ready) to the back of the Processing Box. Consumes triage bandwidth but produces `0 Secrets` and never re-queues the Signature Cube.
  3. **GREEN (`Malware Encryption` — `INV-SIG-GREEN`, `INV-GREEN-SUPPLY`, `INV-GREEN-OVERFLOW`):** Places `2` green cubes from general supply on the next spaces of different Research Tracks ($< \text{Level } 4$). Those spaces cost double research ($2\times \🔬$) to advance into. Unplaced cubes spill over to glitch clean shield slots.
  4. **BLACK (`Root Override Hijack` — `INV-SIG-BLACK`):** Marks the player's Client Company Institutional Override as "Used" for the current SETEC Version. If already used, the player loses `2 Corporate Secrets` (which can trigger Patient Zero).

```mermaid
flowchart TD
    subgraph P2 ["Phase 2: Compiler Drop & Dominant Color Evaluation"]
        STAGED["Staging Cup: Threat Cubes + Staged Signature Cubes"] --> DROP["Tower Drop (Shogun Baffle Physics)"]
        DROP --> TRAY["Exit Tray: cr.exited_cubes (Red, Blue, Green, Black)"]
        DROP --> SIG_OUT{"Signature Cube Exited?"}
        SIG_OUT -->|Yes| SET_LOCK["player.target_locked = True\nReturn Signature Cube to IDLE_ON_MAT"]
        SIG_OUT -->|No (Stuck on Baffle)| IN_TOWER["Cube Remains IN_TOWER\nIncrement Baffle Hold Rounds"]
        
        TRAY --> EVAL_DOM{"cr.exited_cubes Total == 0?"}
        EVAL_DOM -->|Yes (Buffer Overflow)| FIZZLE["Dominant Color = None (Clean Fizzle)"]
        EVAL_DOM -->|No| FIND_MAX["Identify Max Exited Count in {R, B, G, K}"]
        FIND_MAX --> TIE_CHECK{"Ties for Max Count?"}
        TIE_CHECK -->|No (Unique Max)| DOM_COLOR["Dominant Color = Unique Color"]
        TIE_CHECK -->|Yes (2-way, 3-way, 4-way)| PRIORITY["Resolve via Preset Priority Order:\nGREEN > BLACK > BLUE > RED"]
        PRIORITY --> DOM_COLOR
    end

    subgraph P4 ["Phase 4: Attack Resolution & Signature Subroutine"]
        BASE_DEF["Resolve Base Attacks & Shields (Red, Blue, Green)\nDefense Grid L4 Cash Payouts"] --> TL_CHECK{"Surviving Player Target-Locked?"}
        TL_CHECK -->|No| P4_CLEANUP
        TL_CHECK -->|Yes| APPLY_SIG{"Dominant Color?"}
        
        APPLY_SIG -->|GREEN| SIG_G["Malware Encryption:\nMark 2 Tracks with Green Cubes (2x Research Cost)\nShortfall Glitches Shield Slots"]
        APPLY_SIG -->|BLACK| SIG_K["Root Override Hijack:\nMark Institutional Override Used\nFallback: Lose 2 Corporate Secrets"]
        APPLY_SIG -->|BLUE| SIG_B["Buffer Congestion:\nMove 1 Gray Die to Processing Box (0 Secrets)"]
        APPLY_SIG -->|RED| SIG_R["Market Manipulation (Two-Epoch Transfer):\nEpoch 1: All Locked Lose 2 MS\nEpoch 2: Non-Locked Least MS Gain 2 MS"]
        
        SIG_G --> P4_CLEANUP["Phase 4 End Trigger Checks:\nTotal Wipeout / Patient Zero / Market Collapse"]
        SIG_K --> P4_CLEANUP
        SIG_B --> P4_CLEANUP
        SIG_R --> P4_CLEANUP
        
        P4_CLEANUP --> RECYCLE["Snowball Recycle (R, B, G only)\nClear player.target_locked = False"]
    end

    SET_LOCK -.-> TL_CHECK
    DOM_COLOR -.-> APPLY_SIG
```

---

## 2. Formal System Invariants

### `INV-SIG-01`: Dominant Cube Color Determination & Preset Priority Order
Target Lock evaluates **all 4 Compiler Cube colors that exited into the Exit Tray in Phase 2** (`Red`, `Blue`, `Green`, `Black` as recorded in `cr.exited_cubes`).
1. Let $C = \{\texttt{RED}, \texttt{BLUE}, \texttt{GREEN}, \texttt{BLACK}\}$ and let $N_c$ be the number of exited cubes of color $c \in C$.
2. Let $M = \max_{c \in C} N_c$.
3. If $M \le 0$ (all $N_c = 0$), the dominant color is `None` (see `INV-SIG-02`).
4. Let $T = \{c \in C \mid N_c = M\}$.
5. If $|T| = 1$, the unique color in $T$ is the dominant color.
6. If $|T| > 1$, ties are resolved strictly and deterministically using the Central Board top-to-bottom priority order:
   $$\mathbf{GREEN > BLACK > BLUE > RED}$$
   Formally: $\text{dominant\_color} = \arg\min_{c \in T} \text{priority\_rank}(c)$, where:
   $$\text{priority\_rank}(\texttt{GREEN}) = 0, \quad \text{priority\_rank}(\texttt{BLACK}) = 1, \quad \text{priority\_rank}(\texttt{BLUE}) = 2, \quad \text{priority\_rank}(\texttt{RED}) = 3$$
7. **Configurability:** The priority tuple is defined on `GameConfig` as:
   ```python
   signature_attack_tie_order: Tuple[CubeColor, ...] = (
       CubeColor.GREEN,
       CubeColor.BLACK,
       CubeColor.BLUE,
       CubeColor.RED,
   )
   ```
   Alternative permutations evaluated in §11 of the investigation doc (e.g., Rank #2 `GREEN > BLUE > BLACK > RED` or Rank #8 `BLUE > GREEN > BLACK > RED`) can be instantiated dynamically without modifying engine logic.

### `INV-SIG-02`: Clean Tray Fizzle on Zero Exited Cubes (Buffer Overflow)
If zero total Compiler Cubes exit into the Exit Tray during Phase 2 ($\sum_{c \in C} N_c = 0$, e.g., during a Compile Buffer Overflow where all cubes are caught on baffles):
- Target Lock **fizzles cleanly without effect** (`dominant_color = None`).
- No surviving player suffers any Signature Attack.
- `PlayerState.target_locked` remains `True` for the round duration but triggers zero penalty in Phase 4.

### `INV-SIG-03`: Phase 4 Resolution Timing & Sequencing
Dominant Color Signature Attacks resolve strictly within **Phase 4 (Attack Resolution)**:
1. **Pre-Signature Step:** All surviving players resolve standard incoming compiler attack cubes (`Red`, `Blue`, `Green`), assign shields (`Block 1 Any`), suffer unblocked damage, resolve star faces, and collect Defense Grid Level 4 cash payouts.
2. **Signature Step:** After standard damage is fully applied, all surviving players (`not player.is_patient_zero`) who have `player.target_locked == True` simultaneously resolve the Dominant Color Signature Attack corresponding to the round's dominant color.
3. **Post-Signature Step:** Immediately following Signature Attack resolution, the engine executes end-of-Phase-4 End Game Trigger checks:
   - **Total Wipeout Check:** All surviving players at $\le 0$ Secrets.
   - **Patient Zero Check:** Individual players reduced to $\le 0$ Secrets by Black Signature Attack fallback are eliminated as Patient Zero.
   - **Market Collapse Check:** Surviving players reduced to $0$ Market Share by Red Signature Attack trigger the Final Round.
4. **Closing Step:** Physical Attack Cubes in the tray are recycled via Snowball Recycle (`INV-TL-08`), and `player.target_locked` is reset to `False`.

### `INV-SIG-RED`: Red Signature Attack (Market Manipulation) & Simultaneous Two-Epoch Transfer (`INV-SIMUL-RED`)
Rule: *"You lose 2 Market Share; the other surviving player with the least Market Share gains 2 (if tied, you choose)."*
To eliminate turn-order bias and ping-pong anomalies when multiple players are locked (`INV-SIMUL-RED`), Red resolution executes across two discrete epochs:
- **Epoch 1 (Simultaneous Drain):** Every Target-Locked surviving player simultaneously loses `2` Market Share:
  $$\text{player.market\_share} = \max(0, \text{player.market\_share} - 2)$$
- **Epoch 2 (Simultaneous Transfer):**
  1. Evaluate the post-drain Market Share of all surviving players (`not p.is_patient_zero`).
  2. Identify **eligible recipient players**: surviving players who were **NOT Target-Locked** on this drop:
     $$\text{Eligible} = \{p \in \text{surviving\_players} \mid \text{not } p\text{.target\_locked}\}$$
  3. **All-Locked Edge Case:** If all surviving players were Target-Locked on this drop ($\text{Eligible} = \emptyset$), the transfer fizzles completely ($+0$ MS transferred). All players suffer the $-2$ MS drain equally without distortion.
  4. **Solo Survivor Edge Case:** If only one player survives and is Target-Locked, $\text{Eligible} = \emptyset$, and the transfer fizzles cleanly.
  5. If $\text{Eligible} \ne \emptyset$, find the minimum Market Share among eligible players:
     $$MS_{\min} = \min_{p \in \text{Eligible}} p\text{.market\_share}$$
     $$\text{TiedRecipients} = \{p \in \text{Eligible} \mid p\text{.market\_share} = MS_{\min}\}$$
  6. For each Target-Locked player:
     - If $|\text{TiedRecipients}| = 1$, the unique player receives $+2$ Market Share (capped at `p.max_market_share`).
     - If $|\text{TiedRecipients}| > 1$, the locked player invokes bot hook `choose_signature_red_recipient(player, TiedRecipients, state)` to select the recipient.
     - Each locked player transfers $+2$ MS independently (multiple locked players may award their $+2$ to the same trailing player).

### `INV-SIG-BLUE`: Blue Signature Attack (Buffer Congestion) & Source Precedence
Rule: *"After shield blocking, move 1 Gray Legacy die from your Scanned Box (or In Production if Scanned Box is empty; or Ready for Release if both are empty) to the back of your Processing Box. It produces 0 Secrets when triaged."*
1. **Source Precedence:**
   - Primary: `player.scanned_dice`
   - Secondary (if primary has no Gray die): `player.in_production_dice`
   - Tertiary (if primary & secondary have no Gray die): `player.ready_for_release_dice`
   - If all three zones contain zero Gray dice, the movement cleanly fizzles.
2. **Die State Mutation:**
   - The selected Gray die is removed from its source zone and appended to `player.glitched_dice` (Processing Box).
   - Its attributes are reset: `die.production_role = None`, `die.is_locked = False`, `die.secret_pending = False`.
   - Telemetry tracks entry: `player.processing_entry_counter += 1`, `die.processing_entry_seq = player.processing_entry_counter`.

### `INV-SIG-BLUE-TRIAGE`: Zero-Secret & Triage Bandwidth Consumption Isolation
1. When a Gray Legacy die (`DieColor.GRAY`) is moved out of the Processing Box via Conveyor Triage (Phase 6 Step 4), Omnidyne *Magnetic Splice*, Phreaker *Jumper Diagnostics*, or B3 *Air-Gapped Backup*:
   - It consumes `1` unit of Triage Bandwidth (during Phase 6 Conveyor Triage) as normal.
   - It yields strictly **`0` Corporate Secrets** (`secret_faces.bank` returns 0 because `die.secret_pending == False`).
   - It **NEVER triggers** `check_and_queue_signature_cube`. Only dice that actually bank $\ge 1$ Corporate Secret move the Signature Cube from `IDLE_ON_MAT` to `STAGING_CUP` (`INV-TL-03`).

### `INV-SIG-GREEN`: Green Signature Attack (Malware Encryption) & Step Cost Doubling
Rule: *"Place a green cube from the general supply on the next space of 2 different Research Tracks that do not already have a green cube (you choose). Those spaces cost double Research (2× 🔬) to advance into. When researched, return the green cube to the supply. For each green cube that cannot be placed (because fewer than 2 tracks are below Level 4 without a green cube), turn 1 clean shield slot into a Glitched Shield Slot."*
1. **State Container:** `PlayerState.encrypted_research_tracks: Set[str] = field(default_factory=set)`. Normalized track keys are `"DEFENSE"`, `"TRIAGE"`, `"RELEASE"`, `"PR"`.
2. **Track Eligibility:** A track $T$ is eligible if and only if:
   $$\text{level\_of}(T) < 4 \quad \land \quad T \notin \text{player.encrypted\_research\_tracks}$$
3. **Allocation:**
   - Let $E$ be the set of eligible tracks.
   - If $|E| > 2$: player invokes bot hook `choose_signature_green_tracks(player, E, count=2, state)` to select 2 tracks. Both selected tracks are added to `player.encrypted_research_tracks`.
   - If $|E| \le 2$: all tracks in $E$ are added to `player.encrypted_research_tracks`. The shortfall $S = 2 - |E|$ is resolved via Saturation Spillover (`INV-GREEN-OVERFLOW`).
4. **Step Cost Doubling (`sim/engine/research_tracks.py`):**
   When `step_cost(config, player, track)` is evaluated:
   $$\text{cost}(T) = \begin{cases} 2 \times \text{base\_cost}(T) & \text{if } T \in \text{player.encrypted\_research\_tracks} \\ \text{base\_cost}(T) & \text{otherwise} \end{cases}$$
5. **Clearance on Research:**
   When a player successfully pays the research cost and advances track $T$ from Level $L$ to $L+1$ via `player.upgrade_track(T)`:
   - $T$ is immediately removed from `player.encrypted_research_tracks` (`player.encrypted_research_tracks.discard(T)`).
   - The subsequent step $L+1 \to L+2$ is completely clean and unencrypted until struck by a future Green Signature Attack.

### `INV-GREEN-SUPPLY`: Component Supply Isolation
Green cubes placed on Research Tracks are physical markers drawn from a dedicated general token pool. **They are strictly isolated from Project: SETEC's 5-cube compiler Green Cube pool**. They never enter the Cube Tower, Staging Cup, or Exit Tray, and their placement/clearance has zero effect on `state.staging_cup` or `state.tower`.

### `INV-GREEN-OVERFLOW`: Saturation Spillover
For each green cube that cannot be placed because $|E| < 2$:
- Turn `1` clean shield slot into a **Glitched Shield Slot**:
  $$\text{player.glitched\_shield\_slots} = \min(\text{player.defense\_capacity}, \text{player.glitched\_shield\_slots} + 1)$$
- If `player.glitched_shield_slots == player.defense_capacity` (all shield slots already glitched), excess spillover fizzles cleanly without further penalty.

### `INV-SIG-BLACK`: Black Signature Attack (Root Override Hijack) & Patient Zero Fallback
Rule: *"Mark your Client Company's Institutional Override as 'Used' for this SETEC Version. If already used, lose 2 Corporate Secrets."*
1. **Primary Effect (Burn Override):**
   Check if the player's Institutional Override is currently available for the active SETEC Version:
   - For standard companies: `not player.company_ability_used_this_version`.
   - For `Company.DTO` (*Slush Fund*): `not player.dto_slush_fund_used`.
   If available:
   - Mark `player.company_ability_used_this_version = True`.
   - If `player.company == Company.DTO`: mark `player.dto_slush_fund_used = True`.
   - Telemetry increments `player.signature_override_hijacks += 1`.
2. **Fallback Effect (Corporate Secret Loss):**
   If the Institutional Override was already used:
   - The player loses `2` Corporate Secrets:
     $$\text{player.secrets} = \max(0, \text{player.secrets} - 2)$$
   - Telemetry increments `player.signature_black_secrets_lost += 2`.
   - If `player.secrets <= 0`, the player suffers a Total Data Breach and is flagged as Patient Zero in the subsequent Phase 4 end trigger check (`check_end_triggers_after_attacks`).

### `INV-SIG-COMPAT`: Backward Compatibility & Mode Preset Governance
The engine supports three operational modes governed by `GameConfig.signature_attack_mode: str`:
1. `"none"`: Target Lock and Signature Cubes completely inactive (`GameConfig.v040()`, `GameConfig.v041()`).
2. `"v042_plus_one_cube"`: The `v0.42.0` architecture (`+1 dominant Attack Cube` absorbed by shields, Defending Agency tie-break `INV-TL-01`). Default for `GameConfig.v042()`.
3. `"dominant_color_effects"`: The `v0.43.0` architecture (Dominant Color Signature Attacks, preset priority order `INV-SIG-01`, Two-Epoch Red transfer `INV-SIMUL-RED`, Double-Cost Green `INV-SIG-GREEN`, Override Burn Black `INV-SIG-BLACK`). Default for `GameConfig.v043()` and `GameConfig.v043_roster()`.

---

## 3. Component Architecture & Physical Baseline

### 3.1 Central Board Reference Matrix Printing
The Dominant Cube Color Signature Attacks are printed prominently on the Central Board adjacent to the Threat Reference Matrix and Cube Tower Exit Tray:

```
+========================================================================================================================+
| PROJECT: SETEC MAINFRAME — DOMINANT COLOR SIGNATURE ATTACKS                                                           |
| When your Operative Signature Cube exits the Cube Tower in Phase 2, you are TARGET-LOCKED.                             |
| In Phase 4 (after shields), suffer the Signature Attack of the most populous cube color in the Exit Tray:              |
+========+========================+======================================================================================+
| TIE #1 | GREEN (Malware Encrypt)| Place a green cube from supply on the next space of 2 different Research Tracks that |
|        |                        | do not have one. Those spaces cost double Research (2x 🔬). Researching clears the  |
|        |                        | cube. For each cube that cannot be placed, turn 1 clean shield slot into a Glitched. |
+--------+------------------------+--------------------------------------------------------------------------------------+
| TIE #2 | BLACK (Root Override)  | Mark your Client Company Institutional Override as "Used" for this SETEC Version.   |
|        |                        | If already used, lose 2 Corporate Secrets.                                           |
+--------+------------------------+--------------------------------------------------------------------------------------+
| TIE #3 | BLUE (Buffer Congest)  | Move 1 Gray Legacy die from Scanned Box (or In Production / Ready) to the back of    |
|        |                        | your Processing Box. It produces 0 Secrets when triaged.                             |
+--------+------------------------+--------------------------------------------------------------------------------------+
| TIE #4 | RED (Market Manipulate)| You lose 2 Market Share. Then the other surviving player with the least Market Share |
|        |                        | gains 2 (if tied, you choose). (Simultaneous; all-locked transfers cancel).          |
+========+========================+======================================================================================+
| TIE-BREAKER: In case of ties for highest count, resolve top-to-bottom: GREEN > BLACK > BLUE > RED.                     |
| TRAY OVERFLOW: If 0 total compiler cubes exit into the tray, Target Lock fizzles cleanly (no attack).                  |
+========================================================================================================================+
```

### 3.2 Physical Wireframe Integration: Research Tracks
On each player's **Company Terminal Mat**, the 4 Research Tracks (Defense Grid, Triage, Release, Public Relations) feature standard track spaces ($L0 \to L1 \to L2 \to L3 \to L4$).
- A physical green marker cube rests directly on the circular boundary icon of the next unresearched step (e.g., resting on the $L1 \to L2$ pip).
- When a player spends the doubled $2\times \🔬$ cost, their corporate marker moves onto $L2$, and the green marker cube is returned to the general supply box.

---

## 4. Concrete Data Model & Module Contracts

### 4.1 Configuration Contracts (`sim/config.py`)

```python
class SignatureAttackMode(str, Enum):
    NONE = "none"
    V042_PLUS_ONE_CUBE = "v042_plus_one_cube"
    DOMINANT_COLOR_EFFECTS = "dominant_color_effects"

@dataclass
class GameConfig:
    # --- Existing Signature Cube & Target Lock Fields ---
    target_lock_enabled: bool = False
    target_lock_bonus_attack: int = 1

    # --- Phase 62: Dominant Color Signature Attacks (v0.43.0) ---
    signature_attack_mode: str = "none"  # "none" | "v042_plus_one_cube" | "dominant_color_effects"
    signature_attack_tie_order: Tuple[CubeColor, ...] = (
        CubeColor.GREEN,
        CubeColor.BLACK,
        CubeColor.BLUE,
        CubeColor.RED,
    )
    signature_red_drain_amount: int = 2
    signature_red_transfer_amount: int = 2
    signature_black_secret_loss: int = 2
    signature_green_cube_count: int = 2
```

#### Preset Constructors:
```python
@classmethod
def v043(cls, **overrides) -> "GameConfig":
    """v0.43.0 canonical baseline:
    - Inherits v042 (Critical Breach, Signature Cubes, Target Lock)
    - Dominant Cube Color Signature Attacks active
    - Top-to-bottom tie-breaking order: Green > Black > Blue > Red
    """
    overrides.setdefault("target_lock_enabled", True)
    overrides.setdefault("signature_attack_mode", "dominant_color_effects")
    overrides.setdefault("signature_attack_tie_order", (
        CubeColor.GREEN,
        CubeColor.BLACK,
        CubeColor.BLUE,
        CubeColor.RED,
    ))
    return cls.v042(**overrides)

@classmethod
def v043_roster(cls, **overrides) -> "GameConfig":
    """v0.43.0 + bot autonomous PR push and cash allocation policies enabled."""
    overrides.setdefault("bot_pr_push", True)
    overrides.setdefault("bot_pr_push_params", PrPushParams())
    return cls.v043(**overrides)
```

### 4.2 State Container Contracts (`sim/engine/state.py`)

#### Updates to `PlayerState`:
```python
@dataclass
class PlayerState:
    # --- Existing Target Lock Fields ---
    signature_cube_location: SignatureCubeLocation = SignatureCubeLocation.IDLE_ON_MAT
    target_locked: bool = False
    target_lock_baffle_rounds: int = 0
    target_locks_triggered: int = 0
    extra_attacks_absorbed: int = 0
    extra_attacks_unblocked: int = 0
    baffle_hold_rounds_total: int = 0

    # --- Phase 62 State Fields ---
    encrypted_research_tracks: Set[str] = field(default_factory=set)
    signature_attacks_suffered: Dict[str, int] = field(
        default_factory=lambda: {"red": 0, "blue": 0, "green": 0, "black": 0}
    )
    signature_override_hijacks: int = 0
    signature_black_secrets_lost: int = 0
    signature_red_transfers_sent: int = 0
    signature_red_transfers_received: int = 0
```

#### Updates to `GameState`:
```python
@dataclass
class GameState:
    # --- Dominant Color Round Tracking ---
    last_dominant_color: Optional[CubeColor] = None
    signature_attack_events: List[Dict[str, Any]] = field(default_factory=list)
```

---

## 5. Algorithmic Specifications by Phase

### 5.1 Dominant Tray Color Determination (`sim/engine/phase4_attack_resolution.py`)

```python
def determine_dominant_tray_color(
    exited_cubes: Dict[CubeColor, int],
    tie_order: Tuple[CubeColor, ...],
) -> Optional[CubeColor]:
    """Evaluates exited cubes across {Red, Blue, Green, Black} and resolves dominant color.
    
    INV-SIG-01: Preset tie order Green > Black > Blue > Red.
    INV-SIG-02: 0 total compiler cubes -> returns None.
    """
    all_colors = (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN, CubeColor.BLACK)
    counts = {c: int(exited_cubes.get(c, 0)) for c in all_colors}
    max_count = max(counts.values(), default=0)
    
    if max_count <= 0:
        return None
        
    tied_colors = [c for c in tie_order if counts.get(c, 0) == max_count]
    return tied_colors[0] if tied_colors else None
```

### 5.2 Phase 4 Signature Attack Resolution Orchestration

In `execute_attack_resolution(engine, player_commitments, cr, ...)`:
```python
attack = compute_attack_strengths(engine, cr)
if resolve_damage and not cr.buffer_overflow:
    active_directive = engine.state.active_directive_code
    for player, rolled_dice, commitments in player_commitments:
        if player.is_patient_zero or player.player_id in cr.breached_pids:
            continue
        resolve_player_attack(...)

    # Phase 62: Dominant Cube Color Signature Attacks (INV-SIG-03)
    if engine.config.signature_attack_mode == "dominant_color_effects":
        resolve_signature_attacks(engine, cr)

if finalize:
    finalize_attack_resolution(engine, cr)
return attack
```

### 5.3 Concrete Subroutine Algorithms

#### Subroutine `resolve_signature_attacks(engine: GameEngine, cr: CompileResult)`:
```python
def resolve_signature_attacks(engine: GameEngine, cr: CompileResult) -> None:
    cfg = engine.config
    state = engine.state
    dominant_color = determine_dominant_tray_color(cr.exited_cubes, cfg.signature_attack_tie_order)
    state.last_dominant_color = dominant_color
    
    if dominant_color is None:
        return  # INV-SIG-02: Clean tray fizzle
        
    locked_players = [
        p for p in state.players
        if p.target_locked and not p.is_patient_zero
    ]
    if not locked_players:
        return

    if dominant_color == CubeColor.RED:
        _resolve_signature_red(engine, locked_players)
    else:
        for p in locked_players:
            if dominant_color == CubeColor.BLUE:
                _resolve_signature_blue(engine, p)
            elif dominant_color == CubeColor.GREEN:
                _resolve_signature_green(engine, p)
            elif dominant_color == CubeColor.BLACK:
                _resolve_signature_black(engine, p)
            p.signature_attacks_suffered[dominant_color.value] += 1
```

#### Subroutine `_resolve_signature_red(engine: GameEngine, locked_players: List[PlayerState])`:
```python
def _resolve_signature_red(engine: GameEngine, locked_players: List[PlayerState]) -> None:
    """Simultaneous Two-Epoch Market Share Drain & Transfer (INV-SIG-RED, INV-SIMUL-RED)."""
    cfg = engine.config
    state = engine.state
    locked_pids = {p.player_id for p in locked_players}
    drain_amt = cfg.signature_red_drain_amount
    transfer_amt = cfg.signature_red_transfer_amount
    
    # Epoch 1: Simultaneous Drain
    for p in locked_players:
        p.market_share = max(0, p.market_share - drain_amt)
        p.signature_attacks_suffered["red"] += 1
        
    # Epoch 2: Transfer to Eligible Non-Locked Survivors
    eligible = [
        p for p in state.players
        if not p.is_patient_zero and p.player_id not in locked_pids
    ]
    if not eligible:
        return  # All-locked or solo-survivor edge case: transfer fizzles cleanly
        
    min_ms = min(p.market_share for p in eligible)
    tied_recipients = [p for p in eligible if p.market_share == min_ms]
    
    for p in locked_players:
        if len(tied_recipients) == 1:
            chosen = tied_recipients[0]
        else:
            hook = getattr(p.bot, "choose_signature_red_recipient", None)
            if callable(hook):
                chosen = hook(player=p, tied_recipients=tied_recipients, game_state=state)
            else:
                chosen = tied_recipients[0]
        chosen.market_share = min(chosen.max_market_share, chosen.market_share + transfer_amt)
        p.signature_red_transfers_sent += transfer_amt
        chosen.signature_red_transfers_received += transfer_amt
```

#### Subroutine `_resolve_signature_blue(engine: GameEngine, player: PlayerState)`:
```python
def _resolve_signature_blue(engine: GameEngine, player: PlayerState) -> None:
    """Move 1 Gray die to back of Processing Box; yields 0 Secrets (INV-SIG-BLUE)."""
    source_die = None
    source_list = None
    
    for candidate_list in (player.scanned_dice, player.in_production_dice, player.ready_for_release_dice):
        grays = [d for d in candidate_list if d.color == DieColor.GRAY]
        if grays:
            source_die = grays[0]
            source_list = candidate_list
            break
            
    if source_die is not None and source_list is not None:
        source_list.remove(source_die)
        source_die.production_role = None
        source_die.is_locked = False
        source_die.secret_pending = False
        player.processing_entry_counter += 1
        source_die.processing_entry_seq = player.processing_entry_counter
        player.glitched_dice.append(source_die)
```

#### Subroutine `_resolve_signature_green(engine: GameEngine, player: PlayerState)`:
```python
def _resolve_signature_green(engine: GameEngine, player: PlayerState) -> None:
    """Place green cubes on next space of 2 eligible tracks (INV-SIG-GREEN, INV-GREEN-OVERFLOW)."""
    from sim.engine import research_tracks
    
    all_tracks = ("DEFENSE", "TRIAGE", "RELEASE", "PR")
    eligible = [
        t for t in all_tracks
        if research_tracks.level_of(player, t) < 4 and t not in player.encrypted_research_tracks
    ]
    
    count_to_place = engine.config.signature_green_cube_count  # 2
    
    if len(eligible) > count_to_place:
        hook = getattr(player.bot, "choose_signature_green_tracks", None)
        if callable(hook):
            chosen = hook(player=player, eligible_tracks=eligible, count=count_to_place, game_state=engine.state)
        else:
            from sim.bots.base import default_signature_green_tracks_heuristic
            chosen = default_signature_green_tracks_heuristic(player, eligible, count_to_place, engine.state)
        placed = chosen[:count_to_place]
    else:
        placed = list(eligible)
        
    for t in placed:
        player.encrypted_research_tracks.add(t)
        
    shortfall = count_to_place - len(placed)
    if shortfall > 0:
        player.glitched_shield_slots = min(player.defense_capacity, player.glitched_shield_slots + shortfall)
```

#### Subroutine `_resolve_signature_black(engine: GameEngine, player: PlayerState)`:
```python
def _resolve_signature_black(engine: GameEngine, player: PlayerState) -> None:
    """Burn Institutional Override or lose 2 Corporate Secrets (INV-SIG-BLACK)."""
    from sim.entities import Company
    
    is_dto = (player.company == Company.DTO)
    override_available = (
        not player.company_ability_used_this_version and
        (not is_dto or not getattr(player, "dto_slush_fund_used", False))
    )
    
    if override_available:
        player.company_ability_used_this_version = True
        if is_dto:
            player.dto_slush_fund_used = True
        player.signature_override_hijacks += 1
    else:
        loss = engine.config.signature_black_secret_loss  # 2
        player.secrets = max(0, player.secrets - loss)
        player.signature_black_secrets_lost += loss
```

### 5.4 Research Track Step Cost Doubling & Clearing (`sim/engine/research_tracks.py`)

In `step_cost(config: GameConfig, player: PlayerState, track: str) -> Optional[int]`:
```python
def step_cost(config: GameConfig, player: PlayerState, track: str) -> Optional[int]:
    t = normalize_track(track)
    if t not in LEVEL_ATTR:
        return None
    lvl = level_of(player, t)
    if lvl >= MAX_LEVEL:
        return None
    base_cost = int(config.track_step_costs[lvl])
    if t in getattr(player, "encrypted_research_tracks", set()):
        return base_cost * 2
    return base_cost
```

In `PlayerState.upgrade_track(track: str, round_number: Optional[int] = None) -> bool`:
```python
cost = research_tracks.step_cost(self.config, self, t)
if cost is None or self.research_tokens < cost:
    return False
self.research_tokens -= cost
self.research_spent_tracks[t] = self.research_spent_tracks.get(t, 0) + cost
new_level = research_tracks.level_of(self, t) + 1
rnd = round_number if round_number is not None else getattr(self, "_current_round", 0)
research_tracks.apply_level(self.config, self, t, new_level, rnd)

# Clear encryption marker upon successful upgrade (INV-SIG-GREEN)
if hasattr(self, "encrypted_research_tracks"):
    self.encrypted_research_tracks.discard(t)
return True
```

---

## 6. Bot Decision Heuristics & Policy Contracts (`sim/bots/`)

### 6.1 `choose_signature_red_recipient`
When multiple eligible surviving players tie for least Market Share:
```python
def choose_signature_red_recipient(
    self,
    player: PlayerState,
    tied_recipients: List[PlayerState],
    game_state: GameState,
) -> PlayerState:
    """Selects which tied recipient gains +2 Market Share.
    
    Default Heuristic: Selects the tied player with the fewest Corporate Secrets,
    minimizing VP boost to competitive leaders.
    """
    return min(tied_recipients, key=lambda p: (p.secrets, p.money, p.player_id))
```

### 6.2 `choose_signature_green_tracks`
When $> 2$ Research Tracks are eligible for Green encryption:
```python
def choose_signature_green_tracks(
    self,
    player: PlayerState,
    eligible_tracks: List[str],
    count: int,
    game_state: GameState,
) -> List[str]:
    """Selects which eligible tracks receive green encryption cubes.
    
    Default Strategic Heuristic:
    1. Prefer tracks with lowest next-step base cost (L0 -> L1 = 1 🔬 extra vs L3 -> L4 = 3 🔬 extra).
    2. Prefer secondary tracks not targeted for near-term upgrades.
    """
    from sim.engine import research_tracks
    
    def track_penalty_score(t: str) -> Tuple[int, int]:
        lvl = research_tracks.level_of(player, t)
        base = player.config.track_step_costs[lvl] if lvl < 4 else 99
        # Lower base cost = smaller 1x extra penalty
        return (base, lvl)
        
    sorted_tracks = sorted(eligible_tracks, key=track_penalty_score)
    return sorted_tracks[:count]
```

### 6.3 Triage & Special Ability Valuation of Gray Processing Dice
Bots possessing queue manipulation abilities (Omnidyne *Magnetic Splice*, Phreaker *Jumper Diagnostics*, Blue *B3 Air-Gapped Backup*) recognize that a Gray Legacy die in `player.glitched_dice` yields `0 Corporate Secrets`:
- When prioritizing triage order, bots rank colored dice (`secret_pending == True`) strictly above Gray dice.
- However, when the Processing Box is congested ($\ge 2$ dice) and bandwidth is constrained, bots will splice or triage Gray dice to unblock pipeline flow.

---

## 7. Fast Clone & MCTS Parity (`sim/engine/fast_clone.py`)

1. **State Copying:**
   In `fast_clone._cp`:
   - `encrypted_research_tracks` is a `set`, which is deep-copied recursively via `return t(v)` (preserving state encapsulation).
   - `signature_attacks_suffered` is a `dict`, copied via dictionary comprehension.
2. **Resume Round Synchronization:**
   In `resume_round(engine, phase, commitments, cr)`:
   - When resuming from Phase 4, `resolve_signature_attacks` executes within Phase 4 attack resolution, ensuring MCTS rollout state transitions remain 100% bit-identical to the live game loop.

---

## 8. Telemetry & Experimentation Schema

The following telemetry counters are captured per player and across game aggregates:
- `signature_attacks_suffered[color]`: Count of Red, Blue, Green, Black signature attacks suffered.
- `signature_override_hijacks`: Institutional Overrides burned by Black attack.
- `signature_black_secrets_lost`: Corporate Secrets lost to Black fallback.
- `signature_red_transfers_sent`: Net Market Share transferred away via Red attack.
- `signature_red_transfers_received`: Net Market Share received from other players via Red attack.
- `last_dominant_color`: Dominant color recorded per round.
- `dominant_color_counts`: Table-wide frequency distribution of realized dominant colors.

---

## 9. Comprehensive Test Specification

The test suite is implemented in `tests/test_signature_dominant_attacks.py` and validates test cases `TC-SIG-01` through `TC-SIG-14`:

| Test ID | Test Category | Scenario / Conditions | Expected Behavior / Assertions | Invariants Covered |
| :--- | :--- | :--- | :--- | :--- |
| `TC-SIG-01` | Dominant Color | Unique maximum count in Exit Tray (e.g. 3 Black, 1 Red, 1 Blue, 0 Green) | `determine_dominant_tray_color` returns `CubeColor.BLACK` | `INV-SIG-01` |
| `TC-SIG-02` | Priority Order | 4-way tie for highest count (e.g. 1 Red, 1 Blue, 1 Green, 1 Black) | Preset priority order selects `CubeColor.GREEN` | `INV-SIG-01` |
| `TC-SIG-03` | Priority Order | 2-way and 3-way ties across various color pairs (e.g. 2 Black & 2 Blue $\to$ Black; 2 Blue & 2 Red $\to$ Blue; 2 Green & 2 Black $\to$ Green) | Evaluates strictly per `GREEN > BLACK > BLUE > RED` | `INV-SIG-01` |
| `TC-SIG-04` | Configurable Order | Custom `signature_attack_tie_order` specified on `GameConfig` (e.g. `BLUE > GREEN > BLACK > RED`) | 2-way tie between Blue and Green selects Blue | `INV-SIG-01` |
| `TC-SIG-05` | Tray Fizzle | Compile Buffer Overflow (0 total exited cubes in tray) | Dominant color is `None`; Target Lock fizzles cleanly with zero penalties | `INV-SIG-02` |
| `TC-SIG-06` | Phase 4 Timing | Locked player faces normal compiler attack and Black signature attack | Standard shields block base attack; Defense L4 cash collected; then Black burns Override before end triggers | `INV-SIG-03` |
| `TC-SIG-07` | RED Solo Attack | 1 locked player at 10 MS; 3 non-locked players at 12, 8, 6 MS | Locked loses 2 MS (to 8); unique trailing non-locked (6 MS) gains 2 MS (to 8) | `INV-SIG-RED`, `INV-SIMUL-RED` |
| `TC-SIG-08` | RED Tied Recipient | Locked player loses 2 MS; two non-locked players tie for least MS (both at 6 MS) | Calls `choose_signature_red_recipient` hook; selected recipient receives +2 MS | `INV-SIG-RED` |
| `TC-SIG-09` | RED Multi-Locked | 4 players all locked (Quad exit); MS values 14, 12, 10, 8 | Epoch 1 drains all by -2 MS; Epoch 2 eligible set is empty; transfers fizzle cleanly (net -2 to all) | `INV-SIMUL-RED` |
| `TC-SIG-10` | BLUE Congestion | Locked player has 1 Gray die in Scanned Box; Blue dominant | Gray die moves from Scanned to Processing Box; `secret_pending=False` | `INV-SIG-BLUE` |
| `TC-SIG-11` | BLUE Triage Zero | Gray die in Processing Box triaged during Phase 6 Conveyor Triage | Consumes 1 bandwidth; yields 0 Secrets; does NOT queue Signature Cube into Staging Cup | `INV-SIG-BLUE-TRIAGE`, `INV-TL-03` |
| `TC-SIG-12` | GREEN Encryption | Locked player has tracks at L0; Green dominant | 2 tracks marked in `encrypted_research_tracks`; next step costs double ($2\times \🔬$); clears on upgrade | `INV-SIG-GREEN` |
| `TC-SIG-13` | GREEN Saturation | Locked player has 3 tracks at L4 and 1 at L2; Green dominant | Marks the 1 eligible track; remaining 1 cube spills over to glitch 1 clean shield slot | `INV-GREEN-OVERFLOW`, `INV-GREEN-SUPPLY` |
| `TC-SIG-14` | BLACK Override/PZ | Player 1 override unused $\to$ burned. Player 2 override used, 3 Secrets $\to$ drops to 1. Player 3 override used, 2 Secrets $\to$ drops to 0, triggers Patient Zero | Override burned if available; -2 Secrets fallback if used; triggers Patient Zero at $\le 0$ Secrets | `INV-SIG-BLACK` |

---

## 10. SDLC Implementation & Review Gate Plan

### 10.1 Multi-Agent SDLC Handoff Flow
1. **Principal Engineer (`principal-engineer`) — [CURRENT STEP]:** Deliver technical architecture specification (`docs/specs/signature_cube_dominant_attacks_spec.md`).
2. **Senior Engineer (`senior-engineer`):** Implement configuration levers, data model fields, Phase 4 orchestration, research track step-cost doubling, bot hooks, and test suite `tests/test_signature_dominant_attacks.py`.
3. **Staff Engineer (`staff-engineer`):** Strict verification of invariants (`INV-SIG-01`..`INV-SIG-03`, `INV-SIG-RED`..`INV-SIG-BLACK`, `INV-GREEN-SUPPLY`), backward compatibility parity, and test execution.
4. **Product Owner (`product-owner`):** Validate documentation synchronization (`RULES.md`, `RULES_APPENDIX.md`, `GLOSSARY.md`, `PLAN.md`, version bump to `v0.43.0`).
5. **Game Designer (`game-designer`):** Validate Monte Carlo sweep balance metrics (PZ rate $\le 80\%$, wipeout $\le 4\%$, pacing $7.5 \pm 2.5$ rounds, fair-share color distribution).
6. **Graphic Designer (`graphic-designer`):** Update Central Board PNP layout to incorporate the 4-color Signature Attack matrix and priority order.
