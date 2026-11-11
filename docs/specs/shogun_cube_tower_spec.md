# Technical Architecture Specification: Calibrated Shogun Cube Tower Physics (`TowerMode.SHOGUN_BAFFLE`)

**Author:** Principal Engineer / Architect  
**Status:** Approved for Implementation (SDLC Architecture Phase)  
**Target Version:** `v0.38c` Baseline (`TowerMode.SHOGUN_BAFFLE`)  
**Dependencies:** [`docs/findings/shogun_cube_tower_analysis.md`](file:///home/mike/antigravity/rogue-agent/docs/findings/shogun_cube_tower_analysis.md), [`RULES.md`](file:///home/mike/antigravity/rogue-agent/RULES.md), [`GLOSSARY.md`](file:///home/mike/antigravity/rogue-agent/GLOSSARY.md)  
**Target Components:**
- [`sim/config.py`](file:///home/mike/antigravity/rogue-agent/sim/config.py)
- [`sim/tower.py`](file:///home/mike/antigravity/rogue-agent/sim/tower.py)
- [`tests/test_tower.py`](file:///home/mike/antigravity/rogue-agent/tests/test_tower.py)

---

## 1. Executive Summary & Mathematical Motivation

### 1.1 Physical Shogun Cube Tower Baseline
Physical testing with the authentic Shogun Cube Tower across paired drops ($F = 4$ cubes: 1 Red, 1 Blue, 1 Green, 1 Black) revealed a distinct non-monotonic retention and release curve:
1. **Drop 1 (Setup Priming Drop, Empty Tower $S_0 = 0$):**
   - Empirical exited: Mean = `2.80` cubes ($\implies p_{\text{exit,empty}} \approx 0.70$). Mean stuck reservoir $S_1 = 1.20$.
2. **Drop 2 (Round 1 Compiler Drop, Primed Tower):**
   - Empirical exited: Mean = `2.70` cubes (Median = 2.0, Mode = 2).
   - **Conditional on Stuck Reservoir ($S_1$):**
     - $S_1 = 1$ ($M=5$): Exited Mean = `2.33` (Net accumulation $+1.67$).
     - $S_1 = 2$ ($M=6$): Exited Mean = `2.00` (Net accumulation $+2.00$, baffle trapping).
     - $S_1 = 3$ ($M=7$): Exited Mean = `4.50` (Net release $-0.50$, avalanche cascade).

### 1.2 Mathematical Impossibility of Model A (`LEDGE_AVALANCHE`)
The existing `TowerMode.LEDGE_AVALANCHE` combines falling cubes ($F$) and resting stuck cubes ($S$) into an undifferentiated pool of mass $M = F + S$, rolling a monotonic probability $p(M) = \min(0.95, p_{\text{base}} + \max(0, M - \text{cap}) \cdot \text{scale})$.
- Because $p(M)$ is monotonic non-decreasing with mass, $\mathbb{E}[\text{Exited} \mid M] = M \cdot p(M)$ is strictly increasing in $S$ ($3.50$ at $S=1$, $4.20$ at $S=2$).
- This overestimates Round 1 threat by **$+33\%$** (`3.60` vs empirical `2.70`) and cannot model the physical U-shaped curve ($2.80 \to 2.33 \to 2.00 \to 4.50$).

### 1.3 Calibrated Two-State Model B
Distinguishing **falling cubes ($F$)** with downward momentum from **resting stuck cubes ($S$)** resting on internal baffles eliminates this error. Minimum sum of squared errors ($\text{SSE} = 0.0495$, a 40x error reduction) is achieved with:
$$\alpha = 0.15, \quad p_{\text{dislodge,sub}} = 0.21, \quad p_{\text{fall,av}} = 0.60, \quad p_{\text{dislodge,av}} = 0.70$$
Predicting: $\mathbb{E}[\text{Drop 1}] = 2.80$, $\mathbb{E}[\text{Drop 2} \mid S_1=1] = 2.41$, $\mathbb{E}[\text{Drop 2} \mid S_1=2] = 2.02$, $\mathbb{E}[\text{Drop 2} \mid S_1=3] = 4.50$, and overall $\mathbb{E}[\text{Drop 2}] = 2.58$.

---

## 2. Configuration Architecture (`sim/config.py`)

### 2.1 `TowerMode` Enum Expansion
Add `SHOGUN_BAFFLE` to `TowerMode`. Preserve string enum semantics:

```python
class TowerMode(str, Enum):
    LEDGE_AVALANCHE = "ledge_avalanche"
    FLAT_BINOMIAL = "flat_binomial"
    SHOGUN_BAFFLE = "shogun_baffle"
```

### 2.2 Tunable Configuration Parameters on `GameConfig`
Add eight physical parameters to `GameConfig` dataclass:

```python
    # Shogun Cube Tower Two-State Baffle Physics (Calibrated Model B)
    tower_empty_exit_prob: float = 0.70  # Empty tower falling pass-through (S = 0)
    tower_obstruction_alpha: float = 0.15  # Reduction in falling pass-through per stuck cube (sub-avalanche)
    tower_min_fall_prob: float = 0.35  # Floor on sub-avalanche falling pass-through
    tower_trapping_dislodge_prob: float = 0.21  # Dislodge probability for resting cubes when F > 0 (sub-avalanche)
    tower_avalanche_fall_prob: float = 0.60  # Falling pass-through during avalanche
    tower_avalanche_dislodge_prob: float = 0.70  # Resting cube dislodgement probability during avalanche
    tower_avalanche_stuck_threshold: int = 3  # S >= 3 triggers avalanche cascade when F > 0
    tower_avalanche_mass_threshold: int = 7  # F + S >= 7 triggers avalanche cascade when F > 0
```

### 2.3 Preset Factories & Bit-Identical Parity Rules
To protect historical golden fixture tests (`test_v034_parity`, `test_v035_parity`, `test_v036_parity`, `test_v037_parity`, `test_v380_secret_faces`):
1. **Default Field Value:** `GameConfig.tower_mode` remains `TowerMode.LEDGE_AVALANCHE`.
2. **Historical Presets:** `GameConfig()`, `legacy_v033()`, `legacy_v034()`, `legacy_v035()`, `legacy_v036()`, `v037()`, `v038()`, `v038_roster()`, and `v038b()` MUST NOT specify `tower_mode`, defaulting to `TowerMode.LEDGE_AVALANCHE`.
3. **`GameConfig.v038c()` Activation:**
   ```python
   @classmethod
   def v038c(cls, **overrides) -> "GameConfig":
       overrides.setdefault("tower_mode", TowerMode.SHOGUN_BAFFLE)
       # ... remaining v038c overrides ...
       return cls.v038b(**overrides)
   ```
4. **Comparative Analysis Factory:** Provide `GameConfig.v038c_legacy_tower(**overrides)`:
   ```python
   @classmethod
   def v038c_legacy_tower(cls, **overrides) -> "GameConfig":
       """v0.38c rules running on the legacy LEDGE_AVALANCHE tower for comparative sensitivity sweeps."""
       overrides.setdefault("tower_mode", TowerMode.LEDGE_AVALANCHE)
       return cls.v038c(**overrides)
   ```

### 2.4 Validation Invariants (`_validate_tower_config`)
Add a dedicated validation method `_validate_tower_config(self) -> None` invoked in `GameConfig.__post_init__`:
- All probability fields (`tower_empty_exit_prob`, `tower_obstruction_alpha`, `tower_min_fall_prob`, `tower_trapping_dislodge_prob`, `tower_avalanche_fall_prob`, `tower_avalanche_dislodge_prob`, `tower_flat_exit_prob`, `tower_base_exit_prob`) must satisfy $0.0 \le p \le 1.0$ (with $\alpha \ge 0.0$).
- Threshold parameters (`tower_avalanche_stuck_threshold`, `tower_avalanche_mass_threshold`) must be integers $\ge 1$.
- Violations must raise `ValueError` with descriptive diagnostic messages.

---

## 3. Core Tower Mechanics (`sim/tower.py`)

### 3.1 Probability Engine: `calculate_shogun_probabilities`
Define on `CubeTower`:

```python
def calculate_shogun_probabilities(self, falling_count: int, stuck_count: int) -> Tuple[float, float]:
    """Calculates independent exit probabilities for falling cubes and resting stuck cubes.

    Args:
        falling_count (int): Incoming cubes dropped into the tower (F).
        stuck_count (int): Resting cubes settled on internal baffles (S).

    Returns:
        Tuple[float, float]: (p_fall, p_dislodge)
    """
    # Invariant: Resting cubes never spontaneously exit without incoming falling cubes
    if falling_count <= 0:
        return (0.0, 0.0)

    # Empty Tower Regime (S = 0): falling cubes pass through clear baffles, no resting cubes to dislodge
    if stuck_count == 0:
        return (self.config.tower_empty_exit_prob, 0.0)

    # Avalanche Cascade Regime: shelf capacity saturated or drop mass collapses resting shelves
    if (stuck_count >= self.config.tower_avalanche_stuck_threshold or 
            (falling_count + stuck_count) >= self.config.tower_avalanche_mass_threshold):
        return (self.config.tower_avalanche_fall_prob, self.config.tower_avalanche_dislodge_prob)

    # Sub-Avalanche Baffle Trapping Regime: resting cubes obstruct paths and absorb falling kinetic energy
    p_fall = max(
        self.config.tower_min_fall_prob,
        self.config.tower_empty_exit_prob - self.config.tower_obstruction_alpha * stuck_count
    )
    p_dislodge = self.config.tower_trapping_dislodge_prob
    return (p_fall, p_dislodge)
```

### 3.2 Backward-Compatible `calculate_exit_probability`
Preserve `calculate_exit_probability(self, total_cubes_in_drop: int) -> float` for existing callers and bot heuristics:

```python
def calculate_exit_probability(self, total_cubes_in_drop: int) -> float:
    """Calculates the expected per-cube exit probability.

    Under FLAT_BINOMIAL and LEDGE_AVALANCHE, returns the uniform per-cube probability.
    Under SHOGUN_BAFFLE, computes the mass-weighted aggregate expected exit probability
    based on the current stuck reservoir.
    """
    if self.config.tower_mode == TowerMode.FLAT_BINOMIAL:
        return self.config.tower_flat_exit_prob

    if self.config.tower_mode == TowerMode.SHOGUN_BAFFLE:
        falling = total_cubes_in_drop
        stuck = self.total_stuck()
        p_fall, p_dislodge = self.calculate_shogun_probabilities(falling, stuck)
        total = falling + stuck
        if total <= 0:
            return 0.0
        return (falling * p_fall + stuck * p_dislodge) / total

    # Ledge / Avalanche Mode (untouched)
    mass = total_cubes_in_drop
    capacity = self.config.tower_ledge_capacity
    base_p = self.config.tower_base_exit_prob
    scale = self.config.tower_avalanche_scale

    if mass <= capacity:
        return base_p

    extra_mass = mass - capacity
    p = base_p + extra_mass * scale
    return min(0.95, p)
```

### 3.3 Drop Execution & Deterministic RNG Consumption
In `CubeTower.drop(self, staged_cubes: Dict[CubeColor, int], rng: random.Random) -> Dict[CubeColor, int]`:

Branch cleanly on `self.config.tower_mode == TowerMode.SHOGUN_BAFFLE`. Existing `FLAT_BINOMIAL` and `LEDGE_AVALANCHE` logic remains untouched.

#### Deterministic Execution Contract for `SHOGUN_BAFFLE`:
1. Calculate `falling_count = sum(staged_cubes.get(c, 0) for c in CubeColor)` and `stuck_count = self.total_stuck()`.
2. Compute `p_fall, p_dislodge = self.calculate_shogun_probabilities(falling_count, stuck_count)`.
3. If `falling_count == 0`:
   - Consume **0** calls to `rng`.
   - All `exited[color] = 0`.
   - `self.stuck_cubes` remains identical to `stuck_before`.
   - Return `exited`.
4. Initialize `exited = {c: 0 for c in CubeColor}` and `new_stuck = {c: 0 for c in CubeColor}`.
5. **RNG Loop Order (Per-Color Enum Determinism):**
   Iterate through `CubeColor` in canonical enum definition order (`RED`, `BLUE`, `GREEN`, `BLACK`):
   - **Step A (Falling Cubes of Color $c$):**
     For `_ in range(staged_cubes.get(color, 0))`:
     Roll `rng.random() < p_fall`.
     If `True`: `exited[color] += 1`.
     If `False`: `new_stuck[color] += 1`.
   - **Step B (Resting Stuck Cubes of Color $c$):**
     For `_ in range(self.stuck_cubes.get(color, 0))`:
     Roll `rng.random() < p_dislodge`.
     If `True`: `exited[color] += 1`.
     If `False`: `new_stuck[color] += 1`.
6. Update state:
   `self.stuck_cubes = new_stuck`
   `self.last_exited_cubes = dict(exited)`
7. Return `exited`.

---

## 4. Architectural Invariants

| ID | Invariant Statement | Enforcement Mechanism |
| :--- | :--- | :--- |
| `INV-TOWER-CONSERVE-01` | For every color $c \in \text{CubeColor}$: $F_c + S_{\text{before}, c} = E_c + S_{\text{after}, c}$. No cubes vanish or duplicate. | Partition logic in drop loop: every cube lands in either `exited` or `new_stuck`. Verified in unit tests. |
| `INV-TOWER-ZERO-DROP-01` | If $F = 0$, $p_{\text{fall}} = 0, p_{\text{dislodge}} = 0$, yielding $\vec{E} = \vec{0}$ and $\vec{S}' = \vec{S}$. Zero RNG calls consumed. | Early return in `calculate_shogun_probabilities` and `drop()`. |
| `INV-TOWER-EMPTY-01` | If $S = 0$ and $F > 0$, $p_{\text{fall}} = \text{tower\_empty\_exit\_prob}$ ($0.70$) and $p_{\text{dislodge}} = 0.0$. | Empty regime branch in `calculate_shogun_probabilities`. |
| `INV-TOWER-TRAP-01` | When $F > 0, 0 < S < S_{\text{thresh}}$, and $F + S < M_{\text{thresh}}$, $p_{\text{fall}} = \max(p_{\text{min\_fall}}, p_{\text{empty}} - \alpha \cdot S)$, $p_{\text{dislodge}} = p_{\text{trap\_dislodge}}$. | Sub-avalanche branch in `calculate_shogun_probabilities`. |
| `INV-TOWER-AVALANCHE-01` | When $F > 0$ and ($S \ge S_{\text{thresh}}$ or $F + S \ge M_{\text{thresh}}$), $p_{\text{fall}} = p_{\text{av\_fall}}$ ($0.60$) and $p_{\text{dislodge}} = p_{\text{av\_dislodge}}$ ($0.70$). | Avalanche regime branch in `calculate_shogun_probabilities`. |
| `INV-TOWER-PARITY-01` | `TowerMode.LEDGE_AVALANCHE` and `TowerMode.FLAT_BINOMIAL` retain 100% bit-identical RNG replay across all prior configurations and golden test fixtures. | Field default on `GameConfig` remains `LEDGE_AVALANCHE`; legacy code paths left untouched. |

---

## 5. Seeding & Deterministic Telemetry

### 5.1 RNG Consumption Specification
- Under `SHOGUN_BAFFLE`, the exact number of RNG calls consumed in `CubeTower.drop()` is:
  $$N_{\text{rolls}} = \begin{cases} 0 & \text{if } F = 0 \\ F + S & \text{if } F > 0 \end{cases}$$
- The evaluation sequence strictly matches:
  $$\text{Red}_{\text{fall}} \to \text{Red}_{\text{stuck}} \to \text{Blue}_{\text{fall}} \to \text{Blue}_{\text{stuck}} \to \text{Green}_{\text{fall}} \to \text{Green}_{\text{stuck}} \to \text{Black}_{\text{fall}} \to \text{Black}_{\text{stuck}}$$

### 5.2 Phase 2 Telemetry Alignment
In `sim/engine/phase2_compiler.py` and `sim/engine/state.py`:
- `CompileResult` already records `staged_before`, `stuck_before`, `exited_cubes`, and `stuck_after`.
- `buffer_overflow` trigger condition remains:
  `buffer_overflow = (sum(exited_cubes.values()) == 0) and state.config.enable_buffer_overflow`
- Add an optional helper property or method `tower_regime(falling: int, stuck: int) -> str` returning `"empty" | "trapping" | "avalanche"` for experiment telemetry and sweep aggregations.

---

## 6. Test Specifications (`tests/test_tower.py`)

The Senior Engineer must implement the following targeted unit tests in `tests/test_tower.py`:

### 6.1 Deterministic Regime & Probability Tests
1. `test_shogun_probabilities_regimes`:
   - $F=0, S=4 \implies (0.0, 0.0)$
   - $F=4, S=0 \implies (0.70, 0.0)$
   - $F=4, S=1 \implies (0.55, 0.21)$ ($0.70 - 0.15 \times 1 = 0.55$)
   - $F=4, S=2 \implies (0.40, 0.21)$ ($0.70 - 0.15 \times 2 = 0.40$)
   - $F=4, S=3 \implies (0.60, 0.70)$ ($S \ge 3$ triggers avalanche)
   - $F=6, S=1 \implies (0.60, 0.70)$ ($F+S = 7 \ge 7$ triggers mass avalanche)
   - $F=2, S=3 \implies (0.60, 0.70)$ ($S \ge 3$ triggers avalanche)
2. `test_shogun_zero_falling_cubes`:
   - Preload tower with stuck cubes: `{RED: 2, BLACK: 1}` ($S=3$).
   - Drop staged `{}` ($F=0$).
   - Assert `exited == {c: 0 for c in CubeColor}`.
   - Assert `stuck_cubes` is unchanged.
   - Mock `rng.random` and assert `call_count == 0`.

### 6.2 State & Invariant Conservation Tests
3. `test_shogun_cube_conservation`:
   - Stage `{RED: 3, BLUE: 2, GREEN: 1, BLACK: 2}`.
   - Preload `{RED: 1, BLUE: 1, GREEN: 2, BLACK: 0}`.
   - Run `drop()` across 50 seeded iterations.
   - For every iteration and every color, assert $F_c + S_{\text{before}, c} == E_c + S_{\text{after}, c}$.
4. `test_shogun_boundary_floor`:
   - Configure extreme alpha $\alpha = 0.30$, `tower_min_fall_prob = 0.35`.
   - For $S = 2$, $0.70 - 0.60 = 0.10 \implies$ clamped to `0.35`.
   - Assert `calculate_shogun_probabilities(4, 2)[0] == 0.35`.

### 6.3 Configuration Validation Tests
5. `test_shogun_config_validation`:
   - Assert `ValueError` when:
     - `tower_empty_exit_prob = 1.2` or `-0.1`
     - `tower_trapping_dislodge_prob = 1.05`
     - `tower_avalanche_fall_prob = -0.01`
     - `tower_avalanche_stuck_threshold = 0` or `-1`
     - `tower_avalanche_mass_threshold = 0`

### 6.4 Empirical Distribution Verification (Large-N Monte Carlo)
6. `test_shogun_empirical_drop_means`:
   - Initialize tower with `GameConfig.v038c(tower_mode=TowerMode.SHOGUN_BAFFLE)`.
   - Run $N = 20,000$ paired drop trials ($F = 4$: 1 of each color):
     - **Trial Step 1 (Setup Priming Drop):** Start empty ($S_0 = 0$). Drop 4. Record $E_1$ and $S_1 = 4 - E_1$.
     - **Trial Step 2 (Round 1 Compiler Drop):** Keep $S_1$ stuck in tower. Drop 4. Record $E_2$.
   - Assert empirical statistics match calibrated analytical targets within $\pm 0.03$:
     - Drop 1 Mean: $\bar{E}_1 \approx 2.80 \pm 0.03$
     - Drop 2 Overall Mean: $\bar{E}_2 \approx 2.58 \pm 0.03$
     - Drop 2 Conditional on $S_1 = 1$: $\bar{E}_2 \mid (S_1=1) \approx 2.41 \pm 0.04$
     - Drop 2 Conditional on $S_1 = 2$: $\bar{E}_2 \mid (S_1=2) \approx 2.02 \pm 0.04$
     - Drop 2 Conditional on $S_1 = 3$: $\bar{E}_2 \mid (S_1=3) \approx 4.50 \pm 0.06$

### 6.5 Legacy Bit-Identical Regression Test
7. `test_legacy_tower_parity_intact`:
   - Verify that `GameConfig()` has `tower_mode == TowerMode.LEDGE_AVALANCHE`.
   - Execute drops with fixed seeds under `GameConfig.legacy_v035()` and assert exact, identical exit counts as existing baseline.

---

## 7. Implementation Runbook & Handoff Checklist

```
[Phase 1: Config]
[ ] Add TowerMode.SHOGUN_BAFFLE to sim/config.py
[ ] Add 8 physical parameters to GameConfig with defaults and type hints
[ ] Add _validate_tower_config() to GameConfig.__post_init__()
[ ] Update GameConfig.v038c() to set tower_mode = TowerMode.SHOGUN_BAFFLE
[ ] Add GameConfig.v038c_legacy_tower() factory

[Phase 2: Tower Core]
[ ] Implement calculate_shogun_probabilities() in sim/tower.py
[ ] Update calculate_exit_probability() to compute weighted expectation under SHOGUN_BAFFLE
[ ] Implement deterministic SHOGUN_BAFFLE branch in CubeTower.drop() with per-color enum order
[ ] Verify zero-roll handling when falling_count == 0

[Phase 3: Verification]
[ ] Add test cases 6.1 through 6.5 to tests/test_tower.py
[ ] Run pytest tests/test_tower.py
[ ] Run full parity suite: pytest tests/test_v034_parity.py tests/test_v035_parity.py tests/test_v036_parity.py tests/test_v037_parity.py tests/test_v380_secret_faces.py
```
