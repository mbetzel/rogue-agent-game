# Technical Architecture Specification: Operative Signature Cube & Target Lock Protocol

**Document Version:** 1.0.0  
**Status:** Approved for Implementation (SDLC Architecture Phase)  
**Author:** Principal Engineer (`principal-engineer`)  
**Target Release:** `v0.41.1` / `v0.42.0 Candidate` (Phase 60: Operative Signature & Target Lock Protocol)  
**Dependencies:**
- [`GLOSSARY.md`](file:///home/mike/.gemini/antigravity/worktrees/rogue-agent/cube_tower_character_effects/GLOSSARY.md)
- [`RULES.md`](file:///home/mike/.gemini/antigravity/worktrees/rogue-agent/cube_tower_character_effects/RULES.md)
- [`RULES_APPENDIX.md`](file:///home/mike/.gemini/antigravity/worktrees/rogue-agent/cube_tower_character_effects/RULES_APPENDIX.md)
- [`docs/specs/shogun_cube_tower_spec.md`](file:///home/mike/.gemini/antigravity/worktrees/rogue-agent/cube_tower_character_effects/docs/specs/shogun_cube_tower_spec.md)
- [`docs/specs/v400_gameplay_balance_spec.md`](file:///home/mike/.gemini/antigravity/worktrees/rogue-agent/cube_tower_character_effects/docs/specs/v400_gameplay_balance_spec.md)
- [`docs/specs/player_specific_corruption_spec.md`](file:///home/mike/.gemini/antigravity/worktrees/rogue-agent/cube_tower_character_effects/docs/specs/player_specific_corruption_spec.md)

**Target Codebase Modules:**
- `sim/config.py` (Configuration levers, feature flags, candidate presets)
- `sim/tower.py` (Signature cube mass integration and baffle dislodgement mechanics)
- `sim/engine/state.py` (Signature cube location enum, tracking fields on `PlayerState` and `GameState`)
- `sim/engine/phase2_compiler.py` (Phase 2 compiler drop, signature exit detection, Target Lock activation)
- `sim/engine/phase4_attack_resolution.py` (Dominant color calculation, tie handling, +1 attack resolution, shield absorption)
- `sim/engine/phase5_pipeline_shift.py` (Phase 6 Step 4 Conveyor Triage signature cube queuing)
- `sim/engine/core.py` (Telemetry capture and phase lifecycle coordination)
- `sim/engine/fast_clone.py` (State synchronization for MCTS and heuristic search bots)
- `sim/bots/base.py` (Bot hook `choose_target_lock_color` and default valuation heuristics)
- `tests/test_target_lock_signature_cubes.py` (Comprehensive unit & integration test suite)

---

## 1. Executive Summary & Architectural Motivation

### 1.1 Problem Statement & Game Design Rationale
In the `v0.41.0` baseline, the physical **Cube Tower Compiler** processes exclusively system threat cubes: **Attack Cubes** (`Red`, `Blue`, `Green`) and **Black (Corruption) Cubes**. Dropped cubes are completely anonymous; every Attack Cube exiting the tower threatens every surviving player identically, irrespective of individual engine velocity, secret-banking aggression, or network footprint.

While Phase 59 introduced player-specific targeted attacks on Corruption Track spaces, the physical Cube Tower drop itself lacked a tactile, organic player connection. Specifically:
1. **Unchecked Secret Banking Velocity:** Players who aggressively prioritize banking Corporate Secrets through Conveyor Triage generate high VP without incurring proportionate real-time threat heat from Project: SETEC.
2. **Latent Tower Baffle Under-utilization:** Physical baffle retention creates suspense primarily around collective threat accumulation. It does not create individual player suspense regarding *when* an operative's unique digital footprint will emerge from the compiler.
3. **Passive Defensive Stagnation:** Without asymmetric incoming attack spikes, defensive shield planning can settle into static formulas ($2$ shields baseline).

### 1.2 Approved Architecture: The Operative Signature Cube & Target Lock Protocol
Under **Scenario B (The Attention Cycle)**, each White Hat Operative receives exactly **one physical Operative Signature Cube** in their player color:
- **Digital Footprint Leakage (Phase 6 Step 4):** When an operative processes and banks a Corporate Secret during **Conveyor Triage** (moving a die from the **Processing Box** to the **Scanned Box**), their terminal emits a distinctive cryptographic signature. If their Signature Cube is idle on their **Company Terminal Mat**, it is immediately transferred into the **Staging Cup**.
- **Mainframe Detection (Phase 2):** During the **Compiler Drop**, all cubes in the Staging Cup tumble through the Cube Tower.
  - If an operative's Signature Cube **exits into the Exit Tray**, Project: SETEC identifies the intrusion and establishes **Target Lock** on that operative for the round! The Signature Cube is immediately returned to the player's mat.
  - If the Signature Cube **remains stuck on internal baffles**, it lingers in latent suspension inside the mainframe compiler, evading detection this round but remaining poised to drop in future rounds.
- **Targeted Subroutine Strike (Phase 4):** During **Attack Resolution**, an operative under Target Lock faces **`+1 Attack Cube`** matching the **most common exited Attack Cube color** (`Red`, `Blue`, `Green`) in the tray.
- **Defensive Counterplay:** The extra attack cube is completely blockable using standard `Block 1 Any` shields. If blocked, it rewards the operative through standard mechanisms (e.g., Defense Grid Level 4 `+$1` payout).

```mermaid
flowchart TD
    subgraph P6 ["Phase 6: CI/CD Pipeline Shift (Step 4: Conveyor Triage)"]
        TB["Processing Box -> Scanned Box (Die Banks Secret)"] --> CHK_SIG{"Signature Cube on Mat?"}
        CHK_SIG -->|Yes (IDLE_ON_MAT)| QUEUE["Move Signature Cube to Staging Cup (STAGING_CUP)"]
        CHK_SIG -->|No (Already Staged / In Tower)| NO_DUP["No Action: Volume Conserved (INV-TL-03)"]
    end

    subgraph P2 ["Phase 2: Compiler Drop & Corruption"]
        DROP["Drop Staging Cup + Stuck Baffle Cubes into Tower"] --> TOWER_RUN{"Tower Physics Resolution"}
        TOWER_RUN -->|Signature Exits into Tray| LOCK["Trigger Target Lock for Player\nReturn Signature Cube to Mat (IDLE_ON_MAT)"]
        TOWER_RUN -->|Signature Trapped on Baffle| STUCK["Cube Remains in Tower (IN_TOWER)\nIncrement Baffle Hold Rounds"]
    end

    subgraph P4 ["Phase 4: Attack Resolution"]
        TL_EVAL{"Is Player Target Locked?"}
        TL_EVAL -->|No| BASE_ATTACK["Face Baseline Attack Strengths (Red, Blue, Green)"]
        TL_EVAL -->|Yes| CHECK_TRAY{"Exited Attack Cubes in Tray?"}
        
        CHECK_TRAY -->|0 Attack Cubes (Empty / Only Black)| FIZZLE["Target Lock Fizzles Cleanly (+0 Cubes) (INV-TL-02)"]
        CHECK_TRAY -->|Unique Dominant Color| ADD_DOM["Incoming Attack: +1 Dominant Color Cube"]
        CHECK_TRAY -->|Tied Dominant Colors| TIE_CHOICE["Defending Player Chooses Tied Color (INV-TL-01)"]
        TIE_CHOICE --> ADD_DOM
        
        ADD_DOM --> RESOLVE_BLOCK{"Assign Shields (Block 1 Any)"}
        RESOLVE_BLOCK -->|Shield Blocks Extra Cube| ABSORBED["extra_attacks_absorbed += 1\nCounts for Defense L4 (+$1)"]
        RESOLVE_BLOCK -->|Extra Cube Unblocked| UNBLOCKED["extra_attacks_unblocked += 1\nInflicts Color Damage (Red: -1 MS, Blue: -1 Sec, Green: Glitch)"]
    end

    QUEUE -.-> DROP
    LOCK -.-> TL_EVAL
```

---

## 2. Formal System Invariants

### `INV-TL-01`: Dominant Color Tie Resolution (Defending Player Agency)
If two or more Attack Cube colors (`Red`, `Blue`, `Green`) tie for the highest exited count in the Exit Tray during Phase 2 (e.g., 2 Red and 2 Blue; or 1 Red, 1 Blue, and 1 Green), **the defending player chooses which one of the tied colors is added to their incoming attack load**.
- *Example:* Exited tray contains 2 Red, 2 Blue, 1 Green. Red and Blue tie with count 2. The defending locked player selects whether they face +1 Red (total 3 Red) or +1 Blue (total 3 Blue).
- Non-tied lower colors cannot be selected (Green cannot be selected in the example above).

### `INV-TL-02`: Non-Attack Tray Fizzle (Buffer Overflow / Zero Threat Cubes)
If zero Attack Cubes (`Red`, `Blue`, `Green`) exit into the tray during Phase 2 (e.g., Compile Buffer Overflow with 0 total exited cubes, or a compilation cycle where exclusively Black Corruption Cubes exit into the tray):
- Target Lock **fizzles cleanly without effect**.
- The locked player suffers **`+0` extra attack cubes**.
- No damage is dealt, no tie selection is prompted, and no shield allocation is required for the Target Lock.

### `INV-TL-03`: Signature Cube Volume Conservation (Strictly 1 Cube per Player)
Each player has strictly **one physical Operative Signature Cube** in circulation across all game zones.
- At all times, a player's Signature Cube resides in exactly one of three states:
  $$\text{Location} \in \{\texttt{IDLE\_ON\_MAT}, \texttt{STAGING\_CUP}, \texttt{IN\_TOWER}\}$$
- Triaging multiple dice in a single Conveyor Triage step (e.g., moving 2 dice at Triage Level 4 Bandwidth 2) moves the Signature Cube on the first banked die; subsequent dice find the cube already off the mat and perform no cube movement.
- A player whose Signature Cube is already in the Staging Cup or stuck inside the Cube Tower never places an additional cube.

### `INV-TL-04`: Clean Shield Integration & Blockability (`Block 1 Any`)
The +1 Target Lock Attack Cube functions identically to a normal compiler Attack Cube during Phase 4:
- It is assigned against available `Block 1 Any` shields subject to Defense Grid Capacity (`INV-ANY-01`).
- Every available `Block 1 Any` shield must block while any unblocked cube remains.
- If blocked, it is counted as a blocked Attack Cube for **Defense Grid Level 4** cash payouts (`+$1` cash per blocked cube, capped at `$3`).
- Aegis Defense Relay (*Baffle Echo*) can ignore it if that color qualifies.
- DTO (*Slush Fund*) can absorb the resulting Secret loss if the color is Blue and unblocked.

### `INV-TL-05`: Telemetry & State Tracking Ledger
The engine and state containers must track full lifecycle metrics for the Operative Signature Cube:
- `target_locks_triggered`: Total number of times Target Lock activated for the player upon cube exit.
- `extra_attacks_absorbed`: Number of Target Lock attacks successfully absorbed by shields.
- `extra_attacks_unblocked`: Number of Target Lock attacks that penetrated defenses and dealt damage.
- `baffle_hold_rounds`: Continuous rounds the cube has remained resting on internal baffles without exiting.
- `baffle_hold_rounds_total`: Lifetime cumulative rounds spent resting on internal baffles across the entire game.

### `INV-TL-06`: Deterministic Bot Heuristics
Autonomous bots must resolve Target Lock decisions via deterministic, stateless evaluation functions:
- When breaking ties among dominant attack colors (`INV-TL-01`), the bot evaluates the marginal survival and victory impact of each tied color, selecting the color minimizing net harm.
- In Phase 4 shield allocation, bots must account for the enlarged incoming attack load to optimize survival.

### `INV-TL-07`: Configuration Isolation & Parity Preservation
The protocol is gated by `target_lock_enabled: bool = False` on `GameConfig`.
- When `target_lock_enabled is False` (the default across all historical baselines `v0.33` through `v0.41.0`), no Signature Cubes enter the Staging Cup, no Target Locks trigger, and simulation outputs are 100% bit-identical to existing golden baselines.
- The feature is active only when `target_lock_enabled=True` is explicitly specified or instantiated via candidate presets.

### `INV-TL-08`: Snowball Recycle Purity (Zero Threat Inflation)
The +1 Target Lock Attack Cube is an operational threat amplification resolving against the locked player's terminal in Phase 4. **It does not represent a physical threat cube in the Exit Tray**:
- In Phase 4 Step 3 (**Snowball Recycle**), only the physical Attack Cubes actually in the Exit Tray (`cr.exited_cubes`) are placed back into the Staging Cup.
- The +1 virtual/amplified Target Lock attack cube is **NEVER** recycled into the Staging Cup. Threat cube volume and pacing clocks remain strictly conserved.

---

## 3. Component Architecture & Physical Baseline

### 3.1 The 7th Player Cube
Each player set in *Too Many Secrets* physically consists of custom wooden cubes in that player's corporate color (e.g., Player 1 = Amber/Yellow, Player 2 = Cyan/Blue, Player 3 = Violet/Purple, Player 4 = White/Gray):
- **4 Track Cubes:** Track progression on the 4 upgrade tracks (Defense Grid, Triage, Release, Public Relations).
- **1 Institutional Override Cube:** Tracks once-per-version Client Company override availability (`v1.0`, `v2.0`, `v3.0`).
- **1 Market Share Marker Cube:** Tracks current position on the shared 0–20 Market Share Track.
- **1 Operative Signature Cube:** The new 7th player cube, placed on the player's Company Terminal Mat at setup to track the Target Lock Attention Cycle.

### 3.2 Physical Wireframe Integration: Company Terminal Mat
The Operative Signature Cube rests in a dedicated graphic cradle on the **Company Terminal Mat** adjacent to the CI/CD Pipeline Under Development section:

```
+--------------------------------------------------------------------------------------------------------------------+
|  [LEFT COLUMN: CORPORATE HQ]         |  [MAIN COLUMN: CI/CD PIPELINE & DEFENSE GRID]                               |
|                                      |                                                                             |
|  +--------------------------------+  |  +-----------------------------------------------------------------------+  |
|  | CORPORATE SECRETS (VP HOLDER)  |  |  | 1. READY FOR RELEASE (Active Staging / Rolling Pool)                  |  |
|  | - Start: 3 (2P) / 4 (3-4P)      |  |  |                                                                       |  |
|  +--------------------------------+  |  +-----------------------------------------------------------------------+  |
|                                      |                                                                             |
|  +--------------------------------+  |  +-----------------------------------------------------------------------+  |
|  | LIQUID CASH & RESEARCH HOLDERS |  |  | 2. IN PRODUCTION (Income & Defense Grid)                             |  |
|  +--------------------------------+  |  +-----------------------------------------------------------------------+  |
|                                      |                                                                             |
|  +--------------------------------+  |  +-----------------------------------------------------------------------+  |
|  | OPERATIVE SIGNATURE CRADLE     |  |  | 3. UNDER DEVELOPMENT (CI/CD Pipeline)                                 |  |
|  | [ SIGNATURE CUBE IDLE ]        |  |  |  +-------------------+  +------------------------------------------+  |  |
|  | * Moves to Staging Cup when    |  |  |  | SCANNED BOX       |  | TRIAGE TRACK & PROCESSING BOX             |  |  |
|  |   banking a Secret in Phase 6  |  |  |  | (Unbounded Tray)  |  | Dice bank Secrets on exit                |  |  |
|  | * Exiting tower = TARGET LOCK! |  |  |  +-------------------+  +------------------------------------------+  |  |
|  +--------------------------------+  |  +-----------------------------------------------------------------------+  |
+--------------------------------------+-----------------------------------------------------------------------------+
```

---

## 4. Concrete Data Model & Module Contracts

### 4.1 State Enumeration: `SignatureCubeLocation`
Define under `sim/config.py` or `sim/engine/state.py`:

```python
from enum import Enum

class SignatureCubeLocation(str, Enum):
    """Physical location of an Operative Signature Cube in the Attention Cycle."""
    IDLE_ON_MAT = "idle_on_mat"       # Resting in cradle on Company Terminal Mat
    STAGING_CUP = "staging_cup"       # Queued in central Staging Cup for Phase 2 compiler drop
    IN_TOWER = "in_tower"             # Trapped on internal baffles inside the Cube Tower
```

### 4.2 Extensions to `PlayerState` (`sim/engine/state.py`)
Add tracking fields to `PlayerState`:

```python
@dataclass
class PlayerState:
    # ... existing fields ...

    # --- Operative Signature Cube & Target Lock Protocol (Phase 60) ---
    signature_cube_location: SignatureCubeLocation = SignatureCubeLocation.IDLE_ON_MAT
    target_locked: bool = False
    target_lock_baffle_rounds: int = 0
    target_locks_triggered: int = 0
    extra_attacks_absorbed: int = 0
    extra_attacks_unblocked: int = 0
    baffle_hold_rounds_total: int = 0
    baffle_hold_visits: int = 0
```

### 4.3 Extensions to `GameState` (`sim/engine/state.py`)
Add global registry of staged and trapped signature cubes:

```python
@dataclass
class GameState:
    # ... existing fields ...
    
    # Signature cube player IDs currently queued in the staging cup
    staging_signature_cubes: Set[int] = field(default_factory=set)
```

### 4.4 Extensions to `CompileResult` (`sim/engine/state.py`)
Record signature cube exit telemetry in Phase 2:

```python
@dataclass
class CompileResult:
    # ... existing fields ...
    exited_signature_pids: Set[int] = field(default_factory=set)
    stuck_signature_pids: Set[int] = field(default_factory=set)
```

### 4.5 Configuration Levers on `GameConfig` (`sim/config.py`)
Add configuration flags and preset defaults:

```python
@dataclass
class GameConfig:
    # ... existing fields ...

    # Operative Signature Cube & Target Lock Protocol
    target_lock_enabled: bool = False
    target_lock_bonus_attack: int = 1  # Standard +1 Attack Cube
```

Factory candidate preset:

```python
    @classmethod
    def v042(cls, **overrides) -> "GameConfig":
        """Candidate preset enabling Operative Signature Cubes and Target Lock Protocol."""
        overrides.setdefault("target_lock_enabled", True)
        return cls.v041(**overrides)
```

---

## 5. Cube Tower Physics Integration (`sim/tower.py`)

### 5.1 Mass Inclusion in Two-State Calibrated Model B (`SHOGUN_BAFFLE`)
Under the physical *Shogun* Cube Tower physics calibrated in `v0.38c`, exit probability depends on falling mass $F$ and resting stuck mass $S$:
- **Falling Mass ($F$):** Staged threat compiler cubes (`Red`, `Blue`, `Green`, `Black`) PLUS all staged Signature Cubes entering the top funnel.
- **Resting Stuck Mass ($S$):** Threat compiler cubes trapped on internal baffles PLUS all Signature Cubes currently resting on internal baffles.

Because Signature Cubes have identical dimensions and mass ($10\text{ mm}$ wooden cubes) to threat cubes, **they participate fully in the physical mass equations**:
$$F = \sum_{c} \text{staged}[c] + |\text{staged\_signatures}|$$
$$S = \sum_{c} \text{stuck}[c] + |\text{stuck\_signatures}|$$

This preserves the physical property that dropping a Signature Cube adds downward momentum to the compiler drop, increasing the likelihood of triggering an avalanche cascade ($S \ge 3$ or $F + S \ge 7$).

### 5.2 Tower Drop Interface & Contract (`CubeTower.drop`)
To preserve 100% backward compatibility with existing tests and mocks that return `Dict[CubeColor, int]`, the tower method signature is extended via an optional parameter, while storing exited signatures on the instance:

```python
class CubeTower:
    def __init__(self, config: GameConfig) -> None:
        # ... existing initialization ...
        self.stuck_signatures: Dict[int, int] = {}  # pid -> consecutive rounds stuck
        self.last_exited_signatures: Set[int] = set()

    def total_stuck(self) -> int:
        """Returns total cubes (threat + signatures) stuck inside the tower."""
        return sum(self.stuck_cubes.values()) + len(self.stuck_signatures)

    def load_stuck_signatures(self, signatures: Dict[int, int]) -> None:
        """Loads stuck signatures into the tower (for deterministic testing)."""
        self.stuck_signatures = dict(signatures)

    def drop(
        self,
        staged_cubes: Dict[CubeColor, int],
        rng: random.Random,
        staged_signatures: Optional[Set[int]] = None,
    ) -> Dict[CubeColor, int]:
        """Drops threat cubes and optional signature cubes through the compiler.
        
        Returns:
            Dict[CubeColor, int]: Exited threat cubes by color (preserves existing contract).
            Exited signature cube player IDs are accessible via `self.last_exited_signatures`.
        """
        staged_sigs = set(staged_signatures or set())
        self.last_exited_signatures = set()

        if self.config.tower_mode == TowerMode.SHOGUN_BAFFLE:
            falling_count = sum(staged_cubes.get(c, 0) for c in CubeColor) + len(staged_sigs)
            stuck_count = self.total_stuck()
            p_fall, p_dislodge = self.calculate_shogun_probabilities(falling_count, stuck_count)

            exited: Dict[CubeColor, int] = {color: 0 for color in CubeColor}
            if falling_count <= 0:
                self.last_exited_cubes = dict(exited)
                return exited

            new_stuck: Dict[CubeColor, int] = {color: 0 for color in CubeColor}
            
            # 1. Threat Cubes: Falling
            for color in CubeColor:
                for _ in range(staged_cubes.get(color, 0)):
                    if rng.random() < p_fall:
                        exited[color] += 1
                    else:
                        new_stuck[color] += 1

            # 2. Threat Cubes: Resting
            for color in CubeColor:
                for _ in range(self.stuck_cubes.get(color, 0)):
                    if rng.random() < p_dislodge:
                        exited[color] += 1
                    else:
                        new_stuck[color] += 1

            # 3. Signature Cubes: Falling
            new_stuck_sigs: Dict[int, int] = {}
            for pid in staged_sigs:
                if rng.random() < p_fall:
                    self.last_exited_signatures.add(pid)
                else:
                    new_stuck_sigs[pid] = 1  # First round stuck

            # 4. Signature Cubes: Resting
            for pid, rounds in self.stuck_signatures.items():
                if rng.random() < p_dislodge:
                    self.last_exited_signatures.add(pid)
                else:
                    new_stuck_sigs[pid] = rounds + 1

            self.stuck_cubes = new_stuck
            self.stuck_signatures = new_stuck_sigs
            self.last_exited_cubes = dict(exited)
            return exited

        # Legacy / Flat Binomial / Ledge Avalanche fallback ...
        # (Evaluates uniform exit probability for all cubes in mass pool)
        # ...
```

---

## 6. Algorithmic Specifications by Phase

### 6.1 Phase 6 Step 4: Conveyor Triage Activation (`sim/engine/phase5_pipeline_shift.py`)
In `conveyor_triage_v038(engine, player)`:
When a die successfully moves from `player.glitched_dice` (Processing Box) to `player.scanned_dice` (Scanned Box) and executes `secret_faces.bank(...)`:

```python
def check_and_queue_signature_cube(engine: GameEngine, player: PlayerState) -> bool:
    """Invoked during Conveyor Triage whenever a die banks a Secret (INV-TL-03)."""
    if not getattr(engine.config, "target_lock_enabled", False):
        return False

    if player.signature_cube_location == SignatureCubeLocation.IDLE_ON_MAT:
        player.signature_cube_location = SignatureCubeLocation.STAGING_CUP
        player.baffle_hold_visits += 1
        player.target_lock_baffle_rounds = 0
        engine.state.staging_signature_cubes.add(player.player_id)
        return True

    return False
```

- **Execution Timing:** Evaluated on the first die moved in Conveyor Triage.
- **Volume Safeguard:** If multiple dice move, subsequent evaluations observe `player.signature_cube_location == SignatureCubeLocation.STAGING_CUP` and return `False`.

### 6.2 Phase 2: Compiler Drop & Target Lock Activation (`sim/engine/phase2_compiler.py`)
In `execute_compiler_drop(engine, player_commitments)`:

```python
    # Staging Cup Drop
    staged_sigs = set(state.staging_signature_cubes)
    exited_cubes = state.tower.drop(state.staging_cup, engine.rng, staged_signatures=staged_sigs)
    state.staging_signature_cubes.clear()

    # Process Signature Cube Exits and Baffle Holds
    exited_sigs = getattr(state.tower, "last_exited_signatures", set())
    cr.exited_signature_pids = set(exited_sigs)
    cr.stuck_signature_pids = set(getattr(state.tower, "stuck_signatures", {}).keys())

    if engine.config.target_lock_enabled:
        for player in state.players:
            pid = player.player_id
            if pid in exited_sigs:
                # Signature exited into tray: Target Lock established!
                player.target_locked = True
                player.target_locks_triggered += 1
                player.signature_cube_location = SignatureCubeLocation.IDLE_ON_MAT
                player.target_lock_baffle_rounds = 0
            elif pid in cr.stuck_signature_pids:
                # Signature remains trapped on baffles
                player.target_locked = False
                player.signature_cube_location = SignatureCubeLocation.IN_TOWER
                player.target_lock_baffle_rounds = state.tower.stuck_signatures.get(pid, 1)
                player.baffle_hold_rounds_total += 1
```

### 6.3 Phase 4: Attack Resolution & Dominant Color Targeting (`sim/engine/phase4_attack_resolution.py`)
In `resolve_player_defense_and_wear`:
Before shield evaluation, calculate whether Target Lock applies to this player:

```python
def calculate_target_lock_extra_cube(
    engine: GameEngine,
    player: PlayerState,
    exited_cubes: Dict[CubeColor, int],
    attack_strengths: Dict[CubeColor, int],
) -> Optional[CubeColor]:
    """Determines the color of the +1 Target Lock Attack Cube for a locked player."""
    if not getattr(engine.config, "target_lock_enabled", False):
        return None
    if not player.target_locked or player.is_patient_zero:
        return None

    # Tally exited Attack Cubes (Red, Blue, Green ONLY; Black excluded)
    threat_counts = {
        c: exited_cubes.get(c, 0)
        for c in (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN)
    }
    max_count = max(threat_counts.values(), default=0)

    # INV-TL-02: Zero exited threat cubes -> Target Lock fizzles cleanly
    if max_count <= 0:
        return None

    dominant_colors = [c for c, count in threat_counts.items() if count == max_count]

    # Unique dominant color
    if len(dominant_colors) == 1:
        return dominant_colors[0]

    # INV-TL-01: Dominant color tie resolution: Defending player chooses
    return player.bot.choose_target_lock_color(
        player=player,
        tied_colors=dominant_colors,
        game_state=engine.state,
        attack=attack_strengths,
    )
```

Integrating the Extra Cube into Player Defense:

```python
    extra_color = calculate_target_lock_extra_cube(engine, player, exited_cubes, attack_strengths)
    if extra_color is not None:
        player_attacks[extra_color] = player_attacks.get(extra_color, 0) + engine.config.target_lock_bonus_attack
```

Evaluating Absorption vs Unblocked Damage:

```python
    if extra_color is not None:
        # Calculate baseline unblocked damage without the +1 extra cube
        base_incoming = attack_strengths.get(extra_color, 0)
        allocated_shields = color_shields.get(extra_color, 0)  # Total shields dedicated to this color
        
        # Marginal damage comparison
        unblocked_without_extra = max(0, base_incoming - allocated_shields)
        unblocked_with_extra = max(0, (base_incoming + 1) - allocated_shields)
        
        if unblocked_with_extra > unblocked_without_extra:
            player.extra_attacks_unblocked += 1
        else:
            player.extra_attacks_absorbed += 1
```

Resetting Target Lock Status:
At the conclusion of Phase 4 (in `finalize_attack_resolution` or at round close):

```python
    for p in engine.state.players:
        p.target_locked = False
```

---

## 7. Bot Decision Heuristics & Policy Contracts (`sim/bots/`)

### 7.1 Bot Hook Contract: `choose_target_lock_color`
Add to `BaseBot` in `sim/bots/base.py`:

```python
    def choose_target_lock_color(
        self,
        player: PlayerState,
        tied_colors: List[CubeColor],
        state: GameState,
        attack: Dict[CubeColor, int],
    ) -> CubeColor:
        """Selects which tied dominant attack color hits this player under Target Lock (INV-TL-01, INV-TL-06).

        Default Strategic Heuristic:
        Minimizes marginal operational damage based on corporate survivability margins.
        """
        return default_target_lock_color_heuristic(player, tied_colors, state, attack)
```

### 7.2 Default Heuristic Specification (`default_target_lock_color_heuristic`)
The autonomous decision calculates a shadow cost for suffering an extra attack of each tied color:

1. **Defense Capacity Buffer Evaluation:**
   - Let $S_{\text{available}}$ be the player's total active shields (`defense_capacity - glitched_shield_slots`).
   - Let $A_{\text{total}}$ be the total incoming attack cubes facing the player.
   - If $S_{\text{available}} \ge A_{\text{total}} + 1$: The player can block all attacks including the extra cube.
     - **Decision:** Pick the color that maximizes Defense Grid Level 4 benefits or tie-break order `[Green, Red, Blue]`.

2. **Unblocked Marginal Damage Cost Ranking:**
   If the extra attack will penetrate shields and deal unblocked damage:
   - **Blue Attack (+1 Secret Loss):**
     - If `player.secrets <= 2`: Existential threat of Patient Zero elimination! Cost = $100.0$.
     - Otherwise: High cost (VP loss) = $5.0$.
   - **Red Attack (+1 Market Share Loss):**
     - If `player.market_share <= 2`: Existential threat of triggering Market Collapse or dropping out of Market Leader Bonus contention! Cost = $25.0$.
     - Otherwise: Moderate cost (recoverable via PR Track at $3 cash) = $2.5$.
   - **Green Attack (+1 Glitched Shield Slot):**
     - If `player.glitched_shield_slots >= player.defense_capacity`: Grid is already fully saturated; extra Green deals 0 incremental damage! Cost = $0.0$ (clean soak).
     - Otherwise: Low cost (manageable via Green Secret triage or Phase 1 shield placement) = $1.8$.

3. **Deterministic Selection:**
   $$\text{chosen\_color} = \arg\min_{c \in \text{tied\_colors}} \text{Cost}(c)$$
   Ties broken by fixed priority: `CubeColor.GREEN` $\to$ `CubeColor.RED` $\to$ `CubeColor.BLUE`.

---

## 8. State Transitions & Lifecycle Invariants

| Step | Location Before | Trigger / Event | Location After | Target Locked | Telemetry Action |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **Setup** | — | Game Initialization | `IDLE_ON_MAT` | `False` | Initialized |
| **P6 Step 4** | `IDLE_ON_MAT` | Die banks Secret in Conveyor Triage | `STAGING_CUP` | `False` | Queued in Staging Cup |
| **P6 Step 4** | `STAGING_CUP` | Subsequent die banks Secret in same triage | `STAGING_CUP` | `False` | No-op (`INV-TL-03`) |
| **P6 Step 4** | `IN_TOWER` | Die banks Secret while cube trapped in tower | `IN_TOWER` | `False` | No-op (`INV-TL-03`) |
| **P2 Drop** | `STAGING_CUP` | Cube exits into tray ($p < p_{\text{fall}}$) | `IDLE_ON_MAT` | `True` | `target_locks_triggered += 1` |
| **P2 Drop** | `STAGING_CUP` | Cube trapped on baffle ($p \ge p_{\text{fall}}$) | `IN_TOWER` | `False` | `target_lock_baffle_rounds = 1` |
| **P2 Drop** | `IN_TOWER` | Cube dislodged by drop ($p < p_{\text{dislodge}}$) | `IDLE_ON_MAT` | `True` | `target_locks_triggered += 1` |
| **P2 Drop** | `IN_TOWER` | Cube remains trapped ($p \ge p_{\text{dislodge}}$) | `IN_TOWER` | `False` | `target_lock_baffle_rounds += 1` |
| **P4 Resolution**| `IDLE_ON_MAT` | +1 Extra Cube blocked by shield | `IDLE_ON_MAT` | `False` | `extra_attacks_absorbed += 1` |
| **P4 Resolution**| `IDLE_ON_MAT` | +1 Extra Cube unblocked | `IDLE_ON_MAT` | `False` | `extra_attacks_unblocked += 1` |
| **P4 End** | Any | Target Lock reset for next round | Unchanged | `False` | Target lock cleared |

---

## 9. Telemetry & Experimentation Schema

### 9.1 Per-Round Telemetry Extensions (`RoundTelemetry`)
Record Target Lock activity per round:

```python
@dataclass
class RoundTelemetry:
    # ... existing fields ...
    target_locks_by_player: Dict[int, bool] = field(default_factory=dict)
    target_lock_extra_colors: Dict[int, Optional[str]] = field(default_factory=dict)
    target_lock_absorbed_by_player: Dict[int, int] = field(default_factory=dict)
    target_lock_unblocked_by_player: Dict[int, int] = field(default_factory=dict)
    signature_cube_locations: Dict[int, str] = field(default_factory=dict)
```

### 9.2 Game-End Aggregate Telemetry (`sim_results/**`)
Include summary metrics across Monte Carlo sweeps:
- `target_lock_trigger_rate_per_game`: Mean Target Locks triggered per player per game.
- `target_lock_baffle_retention_rate`: Percentage of dropped Signature Cubes that remain trapped on baffles $\ge 1$ round.
- `target_lock_absorption_efficiency`: $\frac{\text{absorbed}}{\text{absorbed} + \text{unblocked}}$ ratio across archetypes.
- `mean_baffle_hold_rounds`: Average rounds a Signature Cube spends resting before exiting.

---

## 10. Comprehensive Test Specification

The test suite must be implemented under `tests/test_target_lock_signature_cubes.py`:

### `TEST-TL-01`: Volume Conservation (`INV-TL-03`)
- **Setup:** Player at Triage Track Level 4 (Bandwidth 2). Processing Box has 3 dice showing Secret faces.
- **Execution:** Execute `conveyor_triage_v038`.
- **Assertion:** Exactly 1 Signature Cube is moved to `STAGING_CUP`. `player.signature_cube_location == SignatureCubeLocation.STAGING_CUP`. Length of `state.staging_signature_cubes` is exactly 1.

### `TEST-TL-02`: No Duplication on Successive Banking (`INV-TL-03`)
- **Setup:** Player's Signature Cube is already `IN_TOWER` (stuck on baffles).
- **Execution:** Move a die from Processing Box to Scanned Box.
- **Assertion:** Signature Cube location remains `IN_TOWER`. `state.staging_signature_cubes` remains empty.

### `TEST-TL-03`: Clean Exit & Target Lock Activation (`INV-TL-05`)
- **Setup:** Signature Cube in `STAGING_CUP`. Mock tower drop such that the signature exits.
- **Execution:** Execute `execute_compiler_drop`.
- **Assertion:** `player.target_locked is True`. `player.signature_cube_location == SignatureCubeLocation.IDLE_ON_MAT`. `player.target_locks_triggered == 1`. Cube is returned to player mat.

### `TEST-TL-04`: Baffle Trapping & Hold Round Incrementation
- **Setup:** Signature Cube in `STAGING_CUP`. Mock tower drop such that the signature gets stuck.
- **Execution:** Execute `execute_compiler_drop`.
- **Assertion:** `player.target_locked is False`. `player.signature_cube_location == SignatureCubeLocation.IN_TOWER`. `player.target_lock_baffle_rounds == 1`.

### `TEST-TL-05`: Dominant Color Single Max Attack Resolution (`INV-TL-04`)
- **Setup:** Exited threat cubes: 3 Blue, 1 Red, 0 Green. Player is `target_locked=True`.
- **Execution:** Run `resolve_player_defense_and_wear`.
- **Assertion:** Player faces 4 Blue Attack Cubes (3 baseline + 1 extra). Red remains 1, Green remains 0.

### `TEST-TL-06`: Dominant Color Tie Resolution Agency (`INV-TL-01`)
- **Setup:** Exited threat cubes: 2 Red, 2 Green, 0 Blue. Player is `target_locked=True`. Mock bot `choose_target_lock_color` returning `CubeColor.GREEN`.
- **Execution:** Run `resolve_player_defense_and_wear`.
- **Assertion:** Player faces 2 Red and 3 Green (2 + 1). Bot hook was called with `tied_colors = [CubeColor.RED, CubeColor.GREEN]`.

### `TEST-TL-07`: Empty Tray Fizzle (`INV-TL-02`)
- **Setup:** Compile Buffer Overflow (0 exited cubes). Player is `target_locked=True`.
- **Execution:** Run `resolve_player_defense_and_wear`.
- **Assertion:** Target Lock fizzles cleanly. Extra attack is `+0`. Player suffers 0 damage.

### `TEST-TL-08`: Only Black Cubes Fizzle (`INV-TL-02`)
- **Setup:** Exited cubes: 2 Black, 0 Red, 0 Blue, 0 Green. Player is `target_locked=True`.
- **Execution:** Run `resolve_player_defense_and_wear`.
- **Assertion:** Exited Attack Cubes count is 0. Target Lock fizzles cleanly. Extra attack is `+0`.

### `TEST-TL-09`: Shield Absorption & Defense L4 Payout Integration (`INV-TL-04`)
- **Setup:** Player has Defense Grid Level 4. Exited cubes: 1 Red. Player Target Locked (+1 Red $\implies$ 2 Red incoming). Player commits 2 shields.
- **Execution:** Run `resolve_player_defense_and_wear`.
- **Assertion:** Both Red cubes blocked. `player.extra_attacks_absorbed == 1`. Player receives $2 cash payout from Defense Grid Level 4 ($1 per blocked cube).

### `TEST-TL-10`: Snowball Recycle Purity (`INV-TL-08`)
- **Setup:** 2 Blue cubes exit. Player Target Locked (faces 3 Blue).
- **Execution:** Complete Phase 4 Attack Resolution including `finalize_attack_resolution`.
- **Assertion:** Exactly 2 Blue cubes recycle into the Staging Cup. Threat cube volume does not inflate to 3.

### `TEST-TL-11`: Backward Compatibility & Flag Parity (`INV-TL-07`)
- **Setup:** Run 10 rounds under `GameConfig(target_lock_enabled=False)`.
- **Assertion:** Output is identical to canonical baseline. Zero Signature Cubes queued; zero Target Locks triggered.

---

## 11. SDLC Implementation & Review Gate Plan

1. **Phase 1: Architecture Specification (`principal-engineer`)** $\to$ *Current Document*.
2. **Phase 2: Senior Engineer Implementation (`senior-engineer`):**
   - Implement `SignatureCubeLocation`, config flags, and `PlayerState` fields.
   - Update `sim/tower.py` to support signature cube mass and baffle retention.
   - Wire Phase 6 Step 4 triage queuing in `sim/engine/phase5_pipeline_shift.py`.
   - Wire Phase 2 drop and Target Lock activation in `sim/engine/phase2_compiler.py`.
   - Wire Phase 4 dominant color calculation, bot tie hook, and absorption tracking in `sim/engine/phase4_attack_resolution.py`.
   - Implement comprehensive test suite `tests/test_target_lock_signature_cubes.py`.
3. **Phase 3: Code Review Gate (`staff-engineer`):**
   - Independent verification of test coverage, zero leakages, bit-identical backward parity, and strict invariant adherence (`INV-TL-01` through `INV-TL-08`).
4. **Phase 4: Telemetry Validation & Balance Sweep (`product-owner` & `game-designer`):**
   - Run 3,600-game comparative sweep (`target_lock_enabled=False` vs `True`) across 2P/3P/4P pods.
   - Evaluate macro pacing (8–11 round guardrail), baffle retention distributions, and archetype equity.
5. **Phase 5: Asset & Rules Synchronization (`graphic-designer` & Main Agent):**
   - Synchronize `RULES.md`, `GLOSSARY.md`, and regenerate PnP assets with the 7th player cube in `pnp/generate_pnp.py`.
