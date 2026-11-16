# Technical Architecture Specification: Research Tracks, Capstone Parity & Reroll Modernization (`v0.44.0`)

**Document ID:** `docs/specs/v440_research_tracks_spec.md`  
**Author:** Principal Engineer Subagent  
**Date:** November 2026  
**Status:** Approved Architecture Specification (Ready for Implementation)  
**Target Release:** `v0.44.0` Baseline (Inherits `v0.43.0`)  
**Design Reference:** `docs/findings/research_tracks_balance_review.md`  

---

## 1. System Overview & Mathematical Rationale

### 1.1 The Capstone Asymmetry Problem
In the `v0.43.0` baseline, the four Terminal Hardware Upgrade Tracks on each player's **Company Terminal Mat** suffered from structural asymmetries, dead rule text, and throughput leaks:
1. **Defense Grid Track:** Reaching Level 4 granted Defense Capacity 4 and paid `+$1 Cash per Attack Cube blocked in Phase 4`, but placed an artificial cap at `max $3`. Because Defense Capacity physically bounds blocked cubes to 4, capping cash at `$3` penalized defensive builds absorbing 4-cube drops in late rounds. Additionally, the Level 3 passive bonus (+1 Secret yield on Blue Secret faces, max +3) was documented in Phase 6 rules text (`RULES.md:331`) but omitted from the Section 2 track table (`RULES.md:47`).
2. **Triage Track:** Option A left Triage Bandwidth at 1 until Level 4, while Level 4 contained dead rules text (`+1 🔬 per die moved in Conveyor Triage beyond the 2nd`) that was physically impossible to trigger under a Bandwidth cap of 2. Furthermore, Triage L3 carried a complex dual-currency ($3 Cash + 2 🔬) requirement to replace a starter Gray die.
3. **Release Track & Reroll Pacing:** Analysis confirmed that 2 base rerolls (3 rolls total) are mathematically essential to prevent early-game vulnerability cliffs (zero-shield failure rates drop from 8.78% under 1 reroll to 2.60% under 2 rerolls, keeping 4P Total Wipeouts under the 2.0% guardrail). However, Release L4 granting a 3rd reroll created an over-centralizing rolling engine. Replacing the 3rd reroll with a deterministic tactical override (**set 1 rolled Gray Legacy die to any face**) restores strategic distinctiveness and synergy with Gray legacy code.
4. **Public Relations Track:** Central Market purchased dice enter the **Scanned Box** to respect CI/CD Release Bandwidth (`v0.40.0`), but the 2nd Purple Specialist die from PR Level 3 bypassed Scanned and dropped directly into Ready for Release. At Level 4, PR offered only an incremental regain ceiling boost without any immediate milestone payout.

### 1.2 The `v0.44.0` Strategic Playstyle Parity Matrix
Under `v0.44.0`, each Level 4 Capstone rewards and differentiates a specific strategic archetype:

| Track | Level 1 (Breakthrough) | Level 2 (Stat Boost) | Level 3 (Breakthrough) | Level 4 Capstone (Immediate + Passive) | Distinct Strategic Archetype Rewarded |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Defense Grid** | Gain `1` Gray Legacy die | Capacity `3` | Gain `1` Corporate Secret *(+ Blue Secret passive +1)* | Capacity `4` + **`+$1` per Blocked Attack Cube** (naturally capped at `$4`) | **SecOps Defensive Engine:** Fully absorbing large attacks converts threat directly into operational cash. |
| **Triage Track (Option B)** | Gain `1` Gray Legacy die | **Bandwidth `2`** | Gain `1` Corporate Secret | **Replace `1` Gray die with Market colored die of choice (`$0` free, to Ready)**; dead text purged | **Rapid Modular Modernization:** Unlocks high pipeline throughput early (L2), then retires legacy code for top-tier market tech. |
| **Release Track** | Gain `1` Gray Legacy die | Bandwidth `5` | Gain `1` Corporate Secret | Bandwidth `6` + **Set `1` rolled Gray Legacy die to any face** in Phase 1 Step 3 | **Tactical CI/CD Precision:** High rolling pool capacity coupled with deterministic control over starter legacy code. |
| **Public Relations** | Gain `+$3` Liquid Cash | Regain up to `2` MS/turn | Gain 2nd Purple die (to **Scanned Box**) | **Gain `+2` Market Share immediately** (clamped at `20`) + Regain up to `3` MS/turn | **Corporate Market Monopolist:** Instant buffer against Market Collapse and direct push for the `+3 Secrets` Market Leader Bonus. |

---

## 2. Configuration Architecture (`sim/config.py`)

### 2.1 Configuration Field Additions & Defaults
```python
# --- sim/config.py ---

# Triage Track Capacity by Level (v0.44 Option B)
V044_TRIAGE_CAPACITY: Tuple[int, ...] = (1, 1, 2, 2, 2)  # Levels 0..4

@dataclass
class GameConfig:
    # Defense Grid L4 natural cash clamp
    defense_l4_cash_cap: int = 4  # [TUNE: v0.44.0 natural clamp matching defense_capacity 4]

    # Triage Track Option B
    triage_l4_free_die_replacement: bool = True  # Gray -> Market colored die at $0
    triage_l3_breakthrough: str = "SECRET"       # "SECRET" (Option B) vs legacy "UPGRADE"

    # Release Track L4 Tactical Face Override
    release_l4_extra_rerolls: int = 0            # Replaces 3rd reroll with Gray die face override
    release_l4_set_gray_face: bool = True        # Permits setting 1 rolled Gray die to any face

    # Public Relations Track Option B & CI/CD Integrity
    pr_l3_purple_to_scanned: bool = True         # Routes 2nd Purple die to Scanned Box
    pr_l4_instant_market_share: int = 2          # One-time Market Share grant on reaching PR L4
```

### 2.2 Factory Preset Definition: `GameConfig.v044()`
```python
@classmethod
def v044(cls, **overrides) -> "GameConfig":
    """v0.44.0 canonical baseline:
    - Inherits v043 (Dominant Color Signature Attacks, Target Lock, Critical Breach).
    - Defense Grid L4: naturally capped at $4 cash per Phase 4 (drop $3 cap).
    - Triage Track Option B: L1 Gray die, L2 Bandwidth 2, L3 +1 Secret, L4 Free Market die replacement.
    - Release Track L4: retains 2 base rerolls; L4 grants Bandwidth 6 + set 1 rolled Gray die to any face.
    - Public Relations Track: L3 Purple die to Scanned Box; L4 grants +2 Market Share immediately (clamped at 20).
    - Purged dead +1 🔬 Conveyor Triage text; fixed $3 PR regain cash typo.
    """
    for k, v in (
        ("defense_l4_cash_cap", 4),
        ("triage_l4_free_die_replacement", True),
        ("triage_l3_breakthrough", "SECRET"),
        ("triage_l2_milestone_secrets", 0),
        ("release_l4_extra_rerolls", 0),
        ("release_l4_set_gray_face", True),
        ("pr_l3_purple_to_scanned", True),
        ("pr_l4_instant_market_share", 2),
    ):
        overrides.setdefault(k, v)

    # Configure track capacity override for TRIAGE: (1, 1, 2, 2, 2)
    capacities = dict(cls().track_capacity_by_level)
    capacities["TRIAGE"] = V044_TRIAGE_CAPACITY
    overrides.setdefault("track_capacity_by_level", capacities)

    return cls.v043(**overrides)

@classmethod
def v044_roster(cls, **overrides) -> "GameConfig":
    """v0.44.0 + bot autonomous PR push and cash allocation policies enabled."""
    overrides.setdefault("bot_pr_push", True)
    overrides.setdefault("bot_pr_push_params", PrPushParams())
    return cls.v044(**overrides)
```

---

## 3. Module Contracts & Mechanics Architecture

### 3.1 Defense Grid Track Architecture
- **Level 3 Documentation Fix:** In `RULES.md:47`, the track summary table cell for Level 3 must explicitly state: `Gain 1 Corporate Secret. Passive: Blue Secret face yields +1 (max +3)`.
- **Level 4 Cash Payout Calculation (`sim/engine/research_tracks.py` & `phase4_attack_resolution.py`):**
  - **Module:** `sim/engine/research_tracks.py:defense_l4_cash()`
  - **Contract:**
    ```python
    def defense_l4_cash(config: GameConfig, player: PlayerState, blocked_cubes: int) -> int:
        if not getattr(config, "is_v035_tracks", False) or player.defense_level < MAX_LEVEL:
            return 0
        cap = int(getattr(config, "defense_l4_cash_cap", 4))
        payout = int(config.defense_l4_cash_per_block) * int(blocked_cubes)
        return max(0, min(cap, payout))
    ```
  - **Invariants:**
    - `INV-DEF-L4-01`: Cash is paid *after* attack damage resolves. Cubes ignored via *Baffle Echo* (Aegis Defense Relay) were not blocked by shields and do not generate cash.
    - `INV-DEF-L4-02`: Glitched Shield Slots cannot hold shields and cannot block; maximum blocked cubes cannot exceed `defense_capacity - glitched_shield_slots` (physical upper bound `4`).

### 3.2 Triage Track Option B Architecture
- **Track Progression & Breakthroughs:**
  - **Level 1 Breakthrough:** Gain `1 Gray Legacy die` to `ready_for_release_dice`.
  - **Level 2 Stat Upgrade:** `triage_bandwidth = 2`. No milestone secret is awarded (`triage_l2_milestone_secrets = 0`).
  - **Level 3 Breakthrough:** Gain `1 Corporate Secret` (`player.gain_secrets(1, "breakthrough")`). Symmetrical with Defense and Release L3.
  - **Level 4 Capstone Resolution (`sim/engine/research_tracks.py`):**
    - Triggered immediately when Level 4 is reached in Phase 5 Operations.
    - Replaces `1 Gray Legacy die` owned by the player with `1 Central Market colored die` of the player's choice at `$0 Cash` (free).
    - The new die enters `ready_for_release_dice` immediately (bypassing Scanned graduation).
    - Eligible Gray dice zones: `glitched_dice` (Processing Box), `scanned_dice` (Scanned Box), `ready_for_release_dice` (Ready for Release).
    - If player owns 0 Gray Legacy dice, or all Central Market colored dice stacks are empty, the replacement cleanly forfeits with outcome `"FORFEITED"`.
- **Phase 6 Cleanup:**
  - In `RULES.md:323`, purge dead text: `At Triage Track Level 4, gain +1 🔬 for each die you move beyond the 2nd`.
  - In `sim/engine/phase5_pipeline_shift.py`, deprecate `pay_triage_l4()` / set return value to 0.

### 3.3 Release Track & Post-Reroll Face Modification Pass
- **Rerolls Baseline:**
  - `max_free_rerolls` remains strictly `2` in Phase 1 Step 3 across all players.
  - Release Level 4 does *not* grant a 3rd reroll (`release_l4_extra_rerolls = 0`).
- **Post-Reroll Face Modification Sequence & Timing:**
  Phase 1 Step 3 concludes after rerolls are completed. Before dice are triaged into the Processing Box (Secret faces), Glitched Shield Slot cleaning, or In Production assignment (Step 4), any eligible face modifications are resolved strictly in the following 3-tier sequence:

```
[Phase 1 Step 3: Pure Rerolls (up to 2 rerolls)]
                      │
                      ▼
 ┌─────────────────────────────────────────────────────────┐
 │ Tier 1: The Prodigy (Arbitrary Code Execution)          │
 │ - Condition: Purple Face 6 (★) in active_dice           │
 │ - Target: 1 other rolled die in active_dice             │
 │ - Effect: Change to any legal non-Star, non-Secret face │
 └────────────────────────────┬────────────────────────────┘
                              │
                              ▼
 ┌─────────────────────────────────────────────────────────┐
 │ Tier 2: Helix Biomedical Consortium (Brute-Force Bypass)│
 │ - Condition: Helix Override activated this round        │
 │ - Target: 1 rolled die in active_dice                   │
 │ - Effect: Change to any legal non-Star face (+ Secret)  │
 └────────────────────────────┬────────────────────────────┘
                              │
                              ▼
 ┌─────────────────────────────────────────────────────────┐
 │ Tier 3: Release Track Level 4 Capstone                  │
 │ - Condition: release_level >= 4 AND >= 1 Gray die rolled│
 │ - Target: 1 rolled Gray Legacy die in active_dice       │
 │ - Effect: Change to any printed face of that Gray die   │
 └────────────────────────────┬────────────────────────────┘
                              │
                              ▼
[Phase 1 Step 4: Production Assignment & Secret Face Triage]
```

#### Precedence, Conflict & Targeting Invariants
1. `INV-REL-L4-TARGET-01` (Rolled Gray Die Only): Release L4 can only target a die that was rolled this round in `active_dice` and has `color == DieColor.GRAY`. If 0 Gray Legacy dice were rolled, the capstone action no-ops cleanly.
2. `INV-REL-L4-FACE-01` (Printed Gray Faces Only): The chosen face must be one of the 6 printed faces of a Gray Legacy die:
   - `Block 1 Any` (Faces 1, 2)
   - `+$1 & +1 🔬` (Face 3)
   - `+$1 / +1 🔬` Choice (Faces 4, 5)
   - `+1 🔬` (Face 6)
   Gray dice have no Star (`★`) and no Secret faces. Release L4 cannot produce a Star or Secret face.
3. `INV-REL-L4-ORDER-01` (Deterministic Precedence):
   - Tier 1 (*The Prodigy*) executes first because it is an outcome of rolled Purple Star dice.
   - Tier 2 (*Helix*) executes second as an active Client Company Institutional Override.
   - Tier 3 (*Release L4*) executes third as the terminal operating system's final baseline firmware patch.
   - If a player holds both Helix and Release L4, they may target different dice or the same Gray die. If targeting the same Gray die, Tier 3 executes last and overwrites earlier modifications. Bots and rational players will prioritize targeting separate dice to maximize total pool EV.

### 3.4 Public Relations Track Architecture
- **Breakthrough Level 3 (CI/CD Pipeline Routing):**
  - Upon reaching Level 3, the 2nd Purple Specialist die is transferred from `personal_purple_reserve` into **`player.scanned_dice`** (Scanned Box), NOT `ready_for_release_dice`.
  - The player must graduate the die from Scanned to Ready during Phase 6 using Release Bandwidth.
  - If `personal_purple_reserve <= 0`, the Breakthrough forfeits cleanly.
- **Capstone Level 4 (Immediate +2 Market Share Grant):**
  - Upon advancing to Level 4 in Phase 5 Operations (spending `3 🔬`), the player immediately gains **`+2 Market Share`**.
  - **Headroom Clamping:** Clamped at `config.market_share_max` (`20`). If the player is at 19, they advance to 20 (+1). If at 20, they remain at 20 (+0). The uncredited gain does not convert to cash or research.
  - This grant does *not* cost cash, does *not* consume the Operations Turn regain limit, and does *not* count toward the 2-hardware-upgrades-per-turn limit.
  - **Recurring Passive:** The per-turn Market Share regain limit increases to **`3 Market Share per turn`** (at `$3 Cash` each).
- **Rulebook Typo Correction:** In `RULES.md:52`, update text to read: `always at $3 Cash per +1 Market Share` (replacing erroneous `3 🔬`).

---

## 4. Bot Decision Architecture & Heuristics

### 4.1 Release Track L4 Gray Face Selection (`sim/bots/base.py`)
Add `choose_release_l4_gray_face()` hook on `BaseBot`:
```python
def choose_release_l4_gray_face(
    self,
    player: PlayerState,
    active_dice: List[Die],
    game_state: GameState,
) -> Optional[Tuple[int, Face]]:
    """Selects 1 rolled Gray Legacy die to set to any printed face.
    
    Heuristic:
    1. Scan rolled Gray dice in active_dice. If none, return None.
    2. Assess threat: Calculate incoming threat from staging cup + tower baffles.
       - Effective shield capacity = defense_capacity - glitched_shield_slots.
       - Committed shields = count of active dice currently showing shields.
    3. If committed shields < effective shield capacity AND incoming threat exceeds committed shields:
       - Target any Gray die currently showing an income face.
       - Set face to Face("Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY).
    4. Otherwise (threat safely covered or defense capacity full):
       - Target any Gray die showing a low-value face (e.g. choice face or shield that exceeds capacity).
       - Set face to Face("+$1 & +1 🔬", money=1, patches=1) [Face 3, highest dual EV].
    """
```

### 4.2 Triage Track L4 Die Replacement Selection (`sim/bots/base.py`)
Add `choose_triage_l4_upgrade()` hook on `BaseBot`:
```python
def choose_triage_l4_upgrade(
    self,
    player: PlayerState,
    game_state: GameState,
    options: TriageUpgradeOptions,
) -> BreakthroughChoice:
    """Selects 1 Gray die to retire and 1 Central Market colored die to acquire for free ($0).
    
    Heuristic:
    1. Target Gray Die Order: Glitched (Processing Box) > Scanned Box > Ready for Release.
       Within each zone, choose lowest die_id.
    2. Target Color Selection:
       - Primary: Archetype market_color_preference (if in options.colors and in stock).
       - Secondary: Fallback order (YELLOW > GREEN > RED > BLUE).
    3. Return BreakthroughChoice(accept=True, gray_die_id=chosen_id, color=chosen_color).
    """
```

### 4.3 Research Planning & Valuations (`sim/bots/research_policy.py`)
- **Triage Track Revaluation:** In `research_policy.py`, bots evaluate Triage Level 2 with high priority because Bandwidth 2 arrives at L2 (2 🔬) instead of L4.
- **Public Relations L4 Valuation:** Bots trailing in Market Share or facing Market Collapse evaluate PR L4 highly because the `+2 Market Share` immediate grant directly defends against defeat and positions the bot for the `+3 Secrets` Market Leader Bonus.

---

## 5. Explicit System Invariants

| Invariant Code | Category | Precise Formal Statement |
| :--- | :--- | :--- |
| `INV-RT-DEF-L4-01` | Defense L4 Cash | In Phase 4, a player at Defense Grid Level 4 collects `$1` per Attack Cube blocked by their committed shields, capped at `min(4, defense_capacity)`. Cubes ignored by *Baffle Echo* or stopped by Glitched Shield Slots pay `$0`. |
| `INV-RT-TRIAGE-L2-BW-01` | Triage L2 Bandwidth | Reaching Triage Track Level 2 immediately sets `player.triage_bandwidth = 2`. No milestone Corporate Secrets are awarded at Level 2. |
| `INV-RT-TRIAGE-L3-BT-01` | Triage L3 Breakthrough | Reaching Triage Track Level 3 resolves an automatic, non-optional Breakthrough awarding `+1 Corporate Secret` to the player's VP pool. |
| `INV-RT-TRIAGE-L4-FREE-01`| Triage L4 Replacement | Reaching Triage Track Level 4 permits the player to retire 1 owned Gray Legacy die (from Processing, Scanned, or Ready) and gain 1 Central Market colored die with stock left for `$0` free. The new die enters `ready_for_release_dice`. |
| `INV-RT-TRIAGE-L4-NOOP-01`| Triage L4 Forfeit | If a player reaching Triage L4 owns 0 Gray Legacy dice or all Central Market colored stacks have 0 stock, the replacement forfeits cleanly with outcome `"FORFEITED"` without error. |
| `INV-RT-REL-BASE-01` | Base Reroll Floor | All players receive up to `2` free rerolls in Phase 1 Step 3. Release Track Level 4 does not increase free rerolls beyond `2`. |
| `INV-REL-L4-TARGET-01` | Release L4 Eligibility | Release Track Level 4 face override applies strictly to 1 die in `active_dice` that was rolled this phase and has `color == DieColor.GRAY`. It cannot target unrolled dice or non-Gray dice. |
| `INV-REL-L4-FACES-01` | Release L4 Face Domain | The target face for Release L4 must be chosen strictly from the printed faces of the Gray Legacy die profile (`Block 1 Any`, `+$1 & +1 🔬`, `+$1 / +1 🔬`, `+1 🔬`). It cannot be set to a Star (`★`) or Secret face. |
| `INV-REL-ORDER-01` | Post-Reroll Sequence | In Phase 1 Step 3, post-reroll face modifications execute strictly in sequence: Tier 1 (*The Prodigy*) $\to$ Tier 2 (*Helix Biomedical Consortium*) $\to$ Tier 3 (*Release Level 4*). |
| `INV-RT-PR-L3-SCANNED-01` | PR L3 CI/CD Routing | The 2nd Purple Specialist die unlocked by the Public Relations Level 3 Breakthrough enters `player.scanned_dice`, requiring Release Bandwidth in Phase 6 to enter Ready for Release. |
| `INV-RT-PR-L4-INSTANT-01` | PR L4 Instant Bonus | Advancing to Public Relations Level 4 immediately grants `+2 Market Share`, clamped at `config.market_share_max` (`20`). It costs `$0 Cash`, requires no Operations Turn action, and does not consume the per-turn regain limit. |

---

## 6. Telemetry, State Models & Metrics

### 6.1 State Model Updates (`PlayerState`)
- `player.l4_payouts["defense_cash"]`: Lifetime cash collected from Defense Grid L4 blocks (now supporting values up to `$4` per round).
- `player.l4_payouts["release_gray_face_sets"]`: Count of rounds in which Release L4 set a Gray die face.
- `player.l4_payouts["pr_instant_market_share"]`: Cumulative Market Share gained via PR L4 (0 or 2).
- `player.triage_l4_upgrade_color`: String record of the Central Market color acquired via Triage L4 (or `None`).
- Deprecate: `player.l4_payouts["triage_research"]` (recorded as 0, dead text removed).

### 6.2 Telemetry Summary Fields (`sim_results`)
Each Monte Carlo simulation sweep summary will record:
- `defense_l4_achievement_rate`: Percentage of games where Defense L4 was reached.
- `triage_l4_achievement_rate`: Percentage of games where Triage L4 was reached.
- `release_l4_achievement_rate`: Percentage of games where Release L4 was reached.
- `pr_l4_achievement_rate`: Percentage of games where PR L4 was reached.
- `triage_l4_replacements_taken`: Count of free Gray $\to$ Market die replacements executed.
- `release_l4_gray_faces_set`: Count of tactical Gray face overrides executed.
- `pr_l4_instant_market_share_awarded`: Total Market Share awarded directly via PR L4.

---

## 7. Test Specifications & Verification Plan

### 7.1 Unit Test Suite (`tests/test_v440_research_tracks.py`)

#### Group 1: Defense Grid Track
- `test_defense_l4_natural_four_cap`: Verify player at Defense L4 blocking 4 Attack Cubes in Phase 4 collects `$4` cash.
- `test_defense_l4_baffle_echo_ignored`: Verify cube ignored by Aegis *Baffle Echo* does not count toward Defense L4 payout.
- `test_defense_l4_glitched_slot_restriction`: Verify a player with 1 Glitched Shield Slot at Defense Capacity 4 can block at most 3 cubes and collects at most `$3`.

#### Group 2: Triage Track Option B
- `test_triage_l1_breakthrough_gray_die`: Verify reaching Triage L1 grants 1 Gray Legacy die into `ready_for_release_dice`.
- `test_triage_l2_bandwidth_two_no_milestone`: Verify reaching Triage L2 sets `triage_bandwidth = 2` and grants 0 Corporate Secrets.
- `test_triage_l3_breakthrough_secret`: Verify reaching Triage L3 grants 1 Corporate Secret with no cash cost or die replacement.
- `test_triage_l4_free_replacement_ready_die`: Verify reaching Triage L4 retires 1 Gray die from `ready_for_release_dice`, decrements Market stock, and places a new colored die into `ready_for_release_dice` at `$0` cost.
- `test_triage_l4_free_replacement_scanned_die`: Verify retiring a Gray die from `scanned_dice`.
- `test_triage_l4_free_replacement_processing_die`: Verify retiring a Gray die from `glitched_dice` (Processing Box).
- `test_triage_l4_forfeit_no_gray`: Verify clean forfeit when player owns 0 Gray dice.
- `test_triage_l4_forfeit_empty_market`: Verify clean forfeit when all Central Market colored stacks are empty.
- `test_phase6_triage_bandwidth_two_no_dead_research`: Verify Phase 6 Conveyor Triage moves 2 dice without paying extra research.

#### Group 3: Release Track & Post-Reroll Sequence
- `test_release_base_two_rerolls`: Verify Phase 1 Step 3 grants exactly 2 free rerolls to all players, including those at Release L4.
- `test_release_l4_set_gray_face_shield`: Verify a player at Release L4 can set a rolled Gray die from an income face to `Block 1 Any`.
- `test_release_l4_set_gray_face_income`: Verify setting a rolled Gray die to `+$1 & +1 🔬`.
- `test_release_l4_noop_zero_gray_rolled`: Verify clean no-op when player rolled 0 Gray dice.
- `test_post_reroll_override_sequence`:
  - Player with The Prodigy (rolls Purple Face 6), Helix override active, and Release L4.
  - Verify sequence executes Tier 1 (*Prodigy*) $\to$ Tier 2 (*Helix*) $\to$ Tier 3 (*Release L4*).
  - Verify Release L4 can target a Gray die modified earlier and overrides it cleanly to a printed Gray face.

#### Group 4: Public Relations Track Option B
- `test_pr_l3_purple_die_to_scanned_box`: Verify 2nd Purple die from PR L3 arrives in `player.scanned_dice` (not ready).
- `test_pr_l4_instant_market_share_unclamped`: Verify advancing to PR L4 when at Market Share 15 grants +2 MS, resulting in 17 MS.
- `test_pr_l4_instant_market_share_clamped`: Verify advancing to PR L4 when at Market Share 19 grants +1 MS (clamped at 20).
- `test_pr_l4_regain_cap_three`: Verify regain cap increases to 3 MS/turn at `$3 Cash` each.

---

## 8. Canonical Terminology & Governance Audit

All documentation, simulation modules, and PnP assets must comply strictly with `GLOSSARY.md`. The following table audits compliance for `v0.44.0`:

| Entity / Concept | Approved Canonical Term | Strictly Forbidden / Deprecated Term |
| :--- | :--- | :--- |
| Track 1 | **Defense Grid Track** | *Defense Hardware Track*, *Security Grid* |
| Track 2 | **Triage Track** | *Conveyor Track*, *Triage Hardware Track* |
| Track 3 | **Release Track** | *Deployment Track*, *Throughput Track* |
| Track 4 | **Public Relations Track** | *Cryptographic Patents Track*, *Patent Filing*, *FinSec Track* |
| Mat Zone 1 | **Ready for Release Zone** | *Active Pool*, *Ready Queue*, *Staging Pool* |
| Mat Zone 2 | **In Production** (Income Slot, Shield Slots) | *Deployed Area*, *Active Zone* |
| Mat Zone 3 (Left) | **Processing Box** | *Glitched Box*, *Unpatched Zone*, *Quarantine* |
| Mat Zone 3 (Right) | **Scanned Box** | *Patch Queue*, *Staging Area* |
| Currency 1 | **Money (`$` / Liquid Cash)** | *Credits*, *Capital*, *Budget* |
| Currency 2 | **Research Tokens (`🔬`)** | *Patches*, *🔧*, *Patch Tokens*, *Tech Points* |
| Victory Points | **Corporate Secrets** | *Victory Points*, *Data Fragments*, *Net Wipeout Score* |
| Eliminated Player | **Patient Zero** | *Demoted Player*, *Breached Operative* |

---

## 9. Implementation Phasing & SDLC Hand-off Roadmap

1. **Phase 1: Architecture Specification Sign-Off (`principal-engineer`):**
   - Completed: `docs/specs/v440_research_tracks_spec.md` generated.
2. **Phase 2: Core Engine & Bot Implementation (`senior-engineer`):**
   - Update `sim/config.py` with `v044()` factory preset and new configuration attributes.
   - Update `sim/engine/research_tracks.py`: Option B Breakthroughs, Triage L4 replacement, PR L3 scanned placement, PR L4 immediate bonus, Defense L4 natural $4 cap.
   - Update `sim/engine/phase1_roll_deploy.py`: Release L4 Gray face setting and 3-tier post-reroll sequence.
   - Update `sim/engine/phase4_attack_resolution.py` and `phase5_pipeline_shift.py`: Purge dead triage research text.
   - Implement unit test suite `tests/test_v440_research_tracks.py`.
3. **Phase 3: Independent Verification & Audit (`staff-engineer`):**
   - Verify all unit tests pass (`pytest tests/ -q`).
   - Run 7,200-game validation sweep across 4P, 3P, and 2P pods to confirm bit-parity and balance stability.
   - Audit invariants (`INV-RT-*`).
4. **Phase 4: Documentation, Rulebook & PnP Sync (`product-owner` + `graphic-designer`):**
   - Synchronize `RULES.md` (§2 table, §4 Phase 1/4/5/6, §5 scoring), `RULES_APPENDIX.md`, `GLOSSARY.md`, `RULES_QUICKREF.md`.
   - Update `pnp/generate_pnp.py` with updated Terminal Mat labels and bump pack version to `v0.44.0`.
   - Update `PLAN.md` with completed milestones.
