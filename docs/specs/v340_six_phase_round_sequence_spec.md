# Technical Architecture Specification: Phase 42 (v0.34.0)
## Six-Phase Round Sequence, Release Bandwidth Routing & Flat Starting Secrets

**Author:** Principal Engineer / Architect
**Status:** Draft for Orchestrator Review (open questions in §12 need answers before implementation starts)
**Target Version:** `v0.34.0` Baseline
**Source of Truth:** [`docs/explorations/2026_11_six_phase_round_sequence_plan.md`](../explorations/2026_11_six_phase_round_sequence_plan.md) (Rev 3, signed off 2026-11-05; decisions D1–D5, O1–O3)
**Dependencies:** [RULES.md](../../RULES.md), [PLAN.md](../../PLAN.md), [v330_step2a_agency_and_singularity_spec.md](./v330_step2a_agency_and_singularity_spec.md)
**Target Components:**
- `sim/config.py`, `sim/engine/core.py`, `sim/engine/state.py`
- New: `sim/engine/phase1_roll_deploy.py`, `phase2_compiler.py`, `phase3_income.py`, `phase4_attack_resolution.py`, `phase5_pipeline_shift.py`, `phase6_operations.py`, `legacy_v033.py`
- Shims: `sim/engine/phase1_boot.py`, `phase2_threat.py`, `phase3_ops.py`
- `sim/bots/base.py`, `adaptive_balanced.py`, `secops_turtle.py`, `venture_greed.py`, `accelerationist.py`, `reckless_saboteur.py`
- `web/controller/core.py`, `phase1_actions.py`, `phase2_actions.py`, `phase3_actions.py` (split), `capabilities.py`, `serializer.py`, `web/schemas.py`, `web/server.py`
- `web/static/index.html`, `web/static/js/api.js`, `state.js`, `components/header.js`, `action_dock.js`, `player_mats.js`, `compiler.js`
- `RULES.md`, `pnp/generate_pnp.py`
- New: `tests/test_v340_six_phase_sequence.py`

> Line numbers below are taken from the working tree at commit `20e8c80` (plus the uncommitted `PLAN.md` edit). Re-verify them before editing.

---

## 1. Executive Summary

### 1.1 What changes
The v0.33 round has three phases: Roll & Deploy, Compiler Drop & Defense (Step 2A corruption, Step 2B attacks, Step 2C end check), and Operations & Pipeline Prep (3A clockwise turns that start with income, then the 3B pipeline). v0.34 splits it into six phases. **Income moves between corruption and attack cubes**, and the pipeline shift moves **in front of** Operations:

| # | Phase (canonical name, D2) | Mode | Engine module |
|---|---|---|---|
| 1 | **Roll & Deploy** | Simultaneous | `phase1_roll_deploy.py` (rename of `phase1_boot.py`, no logic change) |
| 2 | **Compiler Drop & Corruption** | Simultaneous | `phase2_compiler.py` (Step 2A part of `phase2_threat.py`) |
| 3 | **Income** | Simultaneous | `phase3_income.py` (income part of `phase3_ops.py`, plus the income-timed Signature Protocols) |
| 4 | **Attack Resolution** | Simultaneous | `phase4_attack_resolution.py` (Step 2B/2C part of `phase2_threat.py`) |
| 5 | **CI/CD Pipeline Shift** | Simultaneous | `phase5_pipeline_shift.py` (Part 3B of `phase3_ops.py`, reordered per D1) |
| 6 | **Operations** | Clockwise from First Player | `phase6_operations.py` (Part 3A of `phase3_ops.py`, without income) |

A `GameConfig.round_sequence` flag keeps the old v0.33 path (`V033_THREE_PHASE`) for regression tests. The default is `SIX_PHASE`.

### 1.2 Comparison table (`v0.33.0` vs `v0.34.0`)

| Feature | v0.33.0 (`V033_THREE_PHASE`) | v0.34.0 (`SIX_PHASE`) |
|---|---|---|
| Income timing | Phase 3A, inside each clockwise turn, **after** attack damage (`phase3_ops.py:182`) | Phase 3, simultaneous, **after** corruption and **before** attack cubes |
| Green Malware vs income | Glitched die forfeits this round's income ("Income Forfeiture", `RULES.md:227`) | Tempo hit only: income was already collected |
| Red Ransomware | Paid from pre-income cash | Paid from post-income cash (a tax on this round's income) |
| Contractor Expiration | End of Step 2B (`phase2_threat.py:228-238`), or in Phase 2 on buffer overflow (`:53-62`) | **End of Phase 4** in every case, so the contractor `+$1` face pays in Phase 3 |
| In Production after the round | → Ready for Release (`phase3_ops.py:462-469`) | → **Scanned Box**, then ≤ `release_bandwidth` Scanned → Ready (player chooses which) |
| Pipeline order | Hotfix/Splice → Scanned→Ready → Glitched→Scanned → Production→Ready | Hotfix/Splice → Production→Scanned → Scanned→Ready (≤ RB, chosen) → Glitched→Scanned (≤ TB) |
| Pipeline vs Operations | Ops (3A) **before** pipeline (3B) | Pipeline (5) **before** Ops (6); Release upgrades bought in Phase 6 apply from next round's Phase 5 |
| Phase-2 Patient Zero | Still takes Step 2B damage, skips Phase 3 | Skips Phases 3–6 (no income, no attacks, no pipeline, no ops) |
| Final Round | Survivors run Phase 3 | Survivors run **every remaining phase** (3–6 if the breach was in Phase 2, 5–6 if in Phase 4) |
| Singularity | Ends at end of Step 2A | Ends at end of Phase 2 (unchanged semantics) |
| Buffer overflow | No attacks; contractors expire in Phase 2 | No attacks; **income still paid**; contractors expire at end of Phase 4 |
| Burn Notice / Jumper Diagnostics / Acoustic / Cipher / Spook +$2 / B3 / Y2 / Y3 | Phase 3A (after damage) | Phase 3 (before damage) |
| Paid `★` (B2, Y1, P1, P3) | Phase 3A | Phase 6 |
| Damage-conditional `★` (R2, R3 bonus, B1) | Step 2B | Phase 4 (unchanged code path) |
| Starting Secrets | 8 / 8 / **12** (DTO +1) | **8 / 8 / 8** (DTO +1) |
| Web phase ints | 1–3, 4 = Game Over | 1–6, **7** = Game Over |

### 1.3 Round flow

```
run_round()
 ├─ round_sequence == V033_THREE_PHASE → legacy_v033.run_round_v033(engine)   (verbatim core.py:259-276)
 └─ SIX_PHASE:
     P1  commitments = phase1_roll_deploy.execute_phase_1(engine)
     P2  cr = phase2_compiler.execute_compiler_drop(engine, commitments)
         phase2_compiler.check_end_triggers_after_compiler(engine, cr)
         └─ game_over (Singularity / Total Wipeout)? → finalize telemetry, RETURN   [skip P3–P6]
     P3  phase3_income.execute_income(engine, commitments)                [survivors only]
     P4  phase4_attack_resolution.execute_attack_resolution(engine, commitments, cr)
         ├─ damage (survivors only) → Snowball Recycle → Contractor Expiration (all players)
         └─ check_end_triggers_after_attacks → game_over (Total Wipeout)? → finalize, RETURN [skip P5–P6]
     P5  phase5_pipeline_shift.execute_pipeline_shift(engine)             [survivors only]
     P6  phase6_operations.execute_operations(engine)                     [survivors, clockwise; pass First Player]
     END is_final_round → game_over ; else current_round += 1 (+ ROUND_LIMIT check)
```

---

## 2. Configuration (`sim/config.py`)

### 2.1 `RoundSequence` and `RoundPhase`
Add these next to `EndGameReason` (`config.py:39-44`):

```python
class RoundSequence(str, Enum):
    V033_THREE_PHASE = "V033_THREE_PHASE"
    SIX_PHASE = "SIX_PHASE"

class RoundPhase(IntEnum):
    ROLL_AND_DEPLOY = 1
    COMPILER_DROP_AND_CORRUPTION = 2
    INCOME = 3
    ATTACK_RESOLUTION = 4
    CICD_PIPELINE_SHIFT = 5
    OPERATIONS = 6
    GAME_OVER = 7          # web state machine only

ROUND_PHASE_NAMES: Dict[int, str] = {
    1: "Roll & Deploy", 2: "Compiler Drop & Corruption", 3: "Income",
    4: "Attack Resolution", 5: "CI/CD Pipeline Shift", 6: "Operations", 7: "Game Over",
}
```
`ROUND_PHASE_NAMES` is the single source for the phase strings used by the web controller (§8) and the PnP aid (§10.2). The plan text writes the flag as `Literal[...]`. A `str` Enum compares equal to those literals, so `config.round_sequence == "SIX_PHASE"` still works. `__post_init__` coerces plain strings with `RoundSequence(value)`.

### 2.2 New / changed fields on `GameConfig` (`config.py:48-60`)

```python
round_sequence: RoundSequence = RoundSequence.SIX_PHASE
starting_secrets_by_player_count: Optional[Dict[int, int]] = None   # was default {2:8, 3:8, 4:12}
```

```python
def __post_init__(self) -> None:          # GameConfig has no __post_init__ today
    self.round_sequence = RoundSequence(self.round_sequence)
    if self.starting_secrets_by_player_count is None:
        self.starting_secrets_by_player_count = (
            {2: 8, 3: 8, 4: 12} if self.round_sequence == RoundSequence.V033_THREE_PHASE
            else {2: 8, 3: 8, 4: 8}
        )

@classmethod
def legacy_v033(cls, **overrides) -> "GameConfig":
    """v0.33.0 baseline: three-phase round + 4P = 12 Secrets."""
    return cls(round_sequence=RoundSequence.V033_THREE_PHASE, **overrides)

@property
def is_six_phase(self) -> bool:
    return self.round_sequence == RoundSequence.SIX_PHASE
```

- `get_starting_secrets` (`config.py:181-190`) is unchanged. It reads the resolved dict, and the `starting_secrets` scalar still takes precedence.
- An explicit `starting_secrets_by_player_count=` argument always wins, so `tests/version_baselines/test_v05_rules.py:61-80` keeps passing.
- **Caveat:** if code sets `cfg.round_sequence = ...` after construction, the secrets dict is **not** re-resolved. Use the `legacy_v033()` factory or pass the field to the constructor.
- DTO's `+1` stays on `Company.starting_secrets_bonus`, applied at `core.py:148,153` (needs `enable_corporate_asymmetry`). Flat 8 gives DTO 9 (INV-START-SECRETS-FLAT-01).

---

## 3. Engine Module Contracts

### 3.0 Shared types (`sim/engine/state.py`)

```python
Commitments = List[Tuple[PlayerState, List[Die], Dict[int, ShieldColor]]]   # as returned by execute_phase_1

@dataclass
class CompileResult:                     # produced by Phase 2, consumed by Phase 4 and telemetry
    staged_before: Dict[CubeColor, int]
    stuck_before: Dict[CubeColor, int]
    exited_cubes: Dict[CubeColor, int]   # mutable: Mode-B corruption cube adds land here (phase2_threat.py:695-699)
    stuck_after: Dict[CubeColor, int]
    buffer_overflow: bool
    black_dropped: int
    breached_pids: Set[int]              # players who became Patient Zero during Phase 2

@dataclass
class IncomeRecord:
    money: int = 0
    research: int = 0
    secrets: int = 0
    details: List[Dict[str, Any]] = field(default_factory=list)   # per-die rows (same shape as phase2_actions.py:109-118)
    burned_die_id: Optional[int] = None
    diagnostics_face: Optional[str] = None

@dataclass
class PipelineShiftRecord:
    hotfixed_ids: List[int]; returned_to_scanned_ids: List[int]
    graduated_ids: List[int]; triaged_ids: List[int]; held_in_scanned: int
```
Add to `RoundTelemetry` (`state.py:670-683`). Every new field has a default, so legacy constructors stay valid:

```python
round_sequence: str = "V033_THREE_PHASE"
phases_executed: List[int] = field(default_factory=list)          # e.g. [1,2,3,4,5,6] or [1,2]
phase_snapshots: Dict[int, List[Dict]] = field(default_factory=dict)  # key = phase that just ended
income_by_player: Dict[int, Dict[str, int]] = field(default_factory=dict)  # {"money","research","secrets"}
scanned_held_by_player: Dict[int, int] = field(default_factory=dict)       # Scanned count after Phase 5
graduated_by_player: Dict[int, int] = field(default_factory=dict)
final_round_trigger_phase: Optional[int] = None                    # 2 or 4
end_phase: Optional[int] = None                                    # phase in which game_over was set
```
`player_snapshots` keeps its v0.33 meaning (post-damage). In SIX_PHASE it is captured at the end of Phase 4, or at the end of Phase 2 on early exit.

### 3.1 `phase1_roll_deploy.py` (rename)
- Move **all** of `phase1_boot.py:1-595` verbatim and fix the module docstring (`phase1_boot.py:1` uses the deprecated "Boot & Configure").
- Public surface: `get_face_signature`, `detect_hash_matches_with_cipher`, `detect_hash_matches`, `resolve_prodigy_purple_star_override`, `check_operator_contingent_staffing`, `check_and_execute_start_of_round_version_transition`, `execute_phase_1(engine) -> Commitments`, `apply_single_die_immediate_output`, `apply_immediate_face_outputs`.
- No behavior change in either sequence. Meridian and Helix overrides stay here (D4).

### 3.2 `phase2_compiler.py`

```python
def execute_compiler_drop(engine: GameEngine, player_commitments: Commitments) -> CompileResult
def resolve_corruption_space(engine, space: CorruptionSpace, player_commitments: Commitments,
                             exited_cubes: Dict[CubeColor, int],
                             expected_income_by_pid: Optional[Dict[int, int]] = None) -> None
def demote_player_dice_step2a(player, rolled_dice, commitments, count, threat_strengths=None, engine=None) -> None
def return_player_colored_dice_step2a(engine, player, rolled_dice, commitments, count,
                                      threat_strengths=None, expected_income: int = 0) -> None
def apply_p2_chaos_profiteer_bonus(engine, player_commitments, black_dropped: int) -> None
def apply_singularity_cleanup(engine: GameEngine) -> None
def check_end_triggers_after_compiler(engine: GameEngine, cr: CompileResult) -> None
```

| New function | Moves from | Notes |
|---|---|---|
| `execute_compiler_drop` | `phase2_threat.py:22-35` (drop, clear cup), `:37-51` (overflow injection, **without** the contractor expiry at `:53-62`), `:64-114` (Black loop), `:116-121` (P2 via helper) | Returns a `CompileResult`. It sets `last_exited_cubes` (`:27`), `last_round_buffer_overflow` and `total_buffer_overflows`. It does **not** compute attack strengths. |
| `apply_singularity_cleanup` | `phase2_threat.py:131-146` | Returns In Production dice to Ready, sends contractors to supply, clears `pending_unblocked_green`. |
| `resolve_corruption_space` | `:686-747` verbatim | New optional `expected_income_by_pid` is forwarded to `return_player_colored_dice_step2a` (§6.5). Legacy passes `None`. |
| `demote_player_dice_step2a` | `:558-616` verbatim | Still bot-chosen through `choose_dice_to_glitch`. Corruption glitches still land **before income**, so the income-aware key stays (see §6.3 and OQ-14). |
| `return_player_colored_dice_step2a` | `:619-683` | Adds the `expected_income` passthrough to `bot.choose_colored_dice_to_return(..., expected_income=...)`. |
| `apply_p2_chaos_profiteer_bonus` | `:116-121` | Stays at the end of Phase 2 in both sequences (OQ-5). |
| `check_end_triggers_after_compiler` | new; mirrors `:148-154` and `:240-253` | See §4.2. |

`execute_compiler_drop` also fills `cr.breached_pids = {p.player_id for p in players if p.is_patient_zero and p.elimination_round == current_round}`, computed after the Black loop.

### 3.3 `phase3_income.py`

```python
def collect_player_production_income(engine, player, plan: Any = None) -> IncomeRecord
collect_production_income = collect_player_production_income
def preview_player_income(state: GameState, player: PlayerState) -> IncomeRecord      # pure, no mutation
def resolve_spook_burn_notice(engine, player, die_id: int) -> bool
def resolve_phreaker_jumper_diagnostics(engine, player, die_id=None, rng=None, forced_face=None) -> Optional[Face]
def resolve_income_signature_protocols(engine, player, *, spook_burn_die_id: Optional[int] = ...,
                                       phreaker_die_id: Optional[int] = ...) -> None
def execute_player_income(engine, player, *, spook_burn_die_id=..., phreaker_die_id=...) -> IncomeRecord
def execute_income(engine, player_commitments: Commitments) -> Dict[int, IncomeRecord]
```

| Function | Moves from | Notes |
|---|---|---|
| `collect_player_production_income` | `phase3_ops.py:18-91` | Same logic. It now **returns** an `IncomeRecord` (deltas plus per-die details). Legacy callers ignore the return value. The `Any` annotation needs `from typing import Any` (missing today; it only works because of `from __future__ import annotations`). |
| `preview_player_income` | new; logic copied from `phase2_actions.py:80-118` and `phase3_ops.py:22-85` | The single source of truth for income previews used by the web (§8) and bots (§6.6). |
| `resolve_spook_burn_notice` | `phase3_ops.py:97-122` verbatim | — |
| `resolve_phreaker_jumper_diagnostics` | `phase3_ops.py:125-158` verbatim | — |
| `resolve_income_signature_protocols` | `phase3_ops.py:302-325` | The sentinel `...` means "ask the bot": `bot.choose_spook_burn_notice` / `bot.choose_phreaker_jumper_diagnostics`. Web humans pass explicit ids. The **eligibility** rule depends on OQ-2. Recommended: a Purple `★` die must still be In Production at the start of Phase 3. Once per round per player, matching legacy (OQ-17). |
| `execute_player_income` | new | Order: (a) `collect_player_production_income` (all In Production dice including contractors, Acoustic, Cipher, Spook `+$2`, Y2, B3 move, Y3 queued); (b) Y3 dice → Glitched (already inside (a), `:87-91`); (c) `resolve_income_signature_protocols` (Burn Notice, then Jumper Diagnostics). |
| `execute_income` | new | Loops over survivors (`not is_patient_zero`) in player-index order (simultaneous, so order is irrelevant). Records `income_by_player` telemetry. Skips everyone when `game_over`. |

### 3.4 `phase4_attack_resolution.py`

```python
MalwareTargetSelector = Callable[[PlayerState, List[Die], int], List[Die]]

def compute_attack_strengths(engine, cr: CompileResult) -> Dict[CubeColor, int]
def sync_commitments_with_production(player, rolled_dice, commitments) -> None
def resolve_player_defense_and_wear(engine, player, rolled_dice, commitments, attack_strengths, exited_cubes,
                                    active_directive, defer_green_malware: bool = False,
                                    any_shield_allocations: Optional[Dict[CubeColor, int]] = None,
                                    malware_target_policy: str = "V033_INCOME_AWARE",
                                    malware_target_selector: Optional[MalwareTargetSelector] = None) -> None
def apply_snowball_recycle(engine, exited_cubes) -> None
def expire_contractors(engine, skip_pids: AbstractSet[int] = frozenset()) -> None
def check_end_triggers_after_attacks(engine) -> None
def execute_attack_resolution(engine, player_commitments: Commitments, cr: CompileResult,
                              any_shield_allocations_by_pid: Optional[Dict[int, Dict[CubeColor, int]]] = None,
                              malware_selectors_by_pid: Optional[Dict[int, MalwareTargetSelector]] = None,
                              ) -> Dict[CubeColor, int]
```

| Function | Moves from | Notes |
|---|---|---|
| `compute_attack_strengths` | `phase2_threat.py:157-186` | Returns all zeros when `cr.buffer_overflow`. |
| `sync_commitments_with_production` | new | Drops every commitment index whose die is no longer in `player.in_production_dice` (Burn Notice, Y3, or any future Phase 3 removal). Today, commitment tallying at `phase2_threat.py:311-315` does not check membership; only corruption helpers pop indices (`:579-581`, `:656-658`). **INV-SEQ-COMMIT-SYNC-01.** |
| `resolve_player_defense_and_wear` | `:291-555` | Unchanged up to Green resolution. New `malware_target_policy` values: `"V033_INCOME_AWARE"`, the legacy engine key at `:499-553` (`choose_malware_sacrifice` + `glitch_sort_key`); and `"SIX_PHASE_BOT_HOOK"`, where targets come from `malware_target_selector(player, in_production_dice, unblocked_green)` or else `player.bot.choose_malware_glitch_targets(...)`. Each chosen White die goes to supply (Contractor Sacrifice); each other die goes to Glitched. Fizzle when In Production is empty. The policy is a **parameter, not read from config**, because the legacy shim `execute_phase_2` must keep the legacy key even under a default `SIX_PHASE` config (INV-SEQ-SHIM-LEGACY-01). |
| `apply_snowball_recycle` | `:222-226` | — |
| `expire_contractors` | `:228-238` (and the duplicate at `:53-62`) | Applies to **all** players, Patient Zero included, to keep supply accounting intact. `skip_pids` exists only for the legacy deferred-green branch at `:230`. |
| `check_end_triggers_after_attacks` | `:240-253` | See §4.2. |
| `execute_attack_resolution` | `:156-253` | Order: `sync_commitments` → per-survivor `resolve_player_defense_and_wear(..., malware_target_policy="SIX_PHASE_BOT_HOOK")` → Snowball Recycle → Contractor Expiration → end-trigger check. Skips players in `cr.breached_pids` and any Patient Zero (INV-SEQ-PZ-SKIP-01). On buffer overflow it skips the damage loop (no R2/R3/B1 payout, no Aegis/Firewall), still recycles (0 cubes), and **still expires contractors**. Aegis *Baffle Echo* and DTO *Slush Fund* stay inside `resolve_player_defense_and_wear` (D4). |

`defer_green_malware` is kept for the legacy path only (§5).

### 3.5 `phase5_pipeline_shift.py`

```python
def reset_die_for_pipeline(die: Die) -> None                     # the 4-line reset repeated in phase3_ops.py
def apply_hotfix_bypass(engine, player, splice_die_id: Optional[int] = None,
                        hotfix_die_id: Optional[int] = None) -> List[Die]
def production_return_to_scanned(engine, player) -> List[Die]
def production_return_to_ready(player) -> List[Die]               # legacy
def graduate_scanned(engine, player, chosen_die_ids: Optional[List[int]] = None, *,
                     use_bot_choice: bool = True) -> List[Die]
def conveyor_triage(player) -> List[Die]
def execute_player_pipeline_shift(engine, player, *, graduate_die_ids=None, splice_die_id=None,
                                  hotfix_die_id=None) -> PipelineShiftRecord
def execute_pipeline_shift(engine) -> Dict[int, PipelineShiftRecord]
def execute_pipeline_prep_v033(engine) -> None                    # legacy 3B, verbatim order
```

| Function | Moves from | Notes |
|---|---|---|
| `apply_hotfix_bypass` | `phase3_ops.py:390-438` | D1 step 1. Omnidyne *Magnetic Splice* (bot: `choose_omnidyne_override`), then Emergency Hotfix (bot default: best colored, `:426-432`). Explicit ids come from web humans. |
| `production_return_to_scanned` | new | D1 step 2. Every In Production die → `scanned_dice`, reset. **Assert** that no `DieColor.WHITE` remains: contractors already expired in Phase 4 (INV-PIPE-PROD-TO-SCANNED-01). |
| `graduate_scanned` | `phase3_ops.py:440-449` | D1 step 3. `n = min(len(scanned), release_bandwidth)`. Choice comes from `chosen_die_ids` (web) or `bot.choose_scanned_graduates(player, n, game_state)`. Validation: dedupe, keep only dice in Scanned, truncate to `n`, and replace invalid ids with the BaseBot default priority. A shorter valid list is honoured, so the player may graduate fewer than `n` (OQ-1 resolution, §12.1). INV-PIPE-RELEASE-CAP-01 / INV-PIPE-GRAD-CHOICE-01. `use_bot_choice=False` gives legacy FIFO `pop(0)`. |
| `conveyor_triage` | `phase3_ops.py:451-460` verbatim | D1 step 4. FIFO (OQ-8). |
| `execute_player_pipeline_shift` | new | Steps 1→2→3→4. Records `held_in_scanned = len(scanned_dice)` after step 3, before triage (the plan's "dice held in Scanned" metric). |
| `execute_pipeline_shift` | new | Survivors only. Simultaneous. Does **not** pass the First Player Marker (that moves to Phase 6). |
| `execute_pipeline_prep_v033` | `phase3_ops.py:384-470` | Verbatim legacy order: Hotfix → Grad → Triage → Production→Ready. |

### 3.6 `phase6_operations.py`

```python
def resolve_operations_plan(bot: BaseBot, player, state, rng) -> Phase3ActionPlan   # §6.1 alias resolver
def execute_player_operations_turn(engine, player, plan, *, collect_income: bool = False,
                                   resolve_signature_protocols: bool = False) -> None
def pass_first_player_marker(engine) -> None
def execute_operations(engine) -> None
```

| Function | Moves from | Notes |
|---|---|---|
| `execute_player_operations_turn` | `phase3_ops.py:179-379` | Both flags `True` reproduce legacy 3A exactly: income at `:182` and protocols at `:302-325`, in their original positions. SIX_PHASE passes `False`/`False`. The rest is unchanged: dirty income (deprecated, config-off), Prometheus *Algorithmic Arbitrage* (D4), B2/Y1/P1/P3 (D3.9), purchases → **Ready** (`:349,:362`, O3), track upgrades, Patent Filings. |
| `pass_first_player_marker` | `phase3_ops.py:473-474` | Fix the "Lead Consultant" comment (deprecated term). |
| `execute_operations` | `phase3_ops.py:163-178` | Clockwise from `first_player_index`. Skips Patient Zero. Calls `resolve_operations_plan` **after** Phases 3–5, so bots plan with post-income, post-damage cash. Ends with `pass_first_player_marker`. Returns immediately if `game_over`. |

### 3.7 `legacy_v033.py` (new) and shims

```python
def run_round_v033(engine: GameEngine) -> RoundTelemetry          # body of core.py:259-276
def execute_phase_2_v033(engine, player_commitments, defer_green_for_pids: Optional[Set[int]] = None) -> RoundTelemetry
def execute_phase_3_v033(engine: GameEngine) -> None
```
- `execute_phase_2_v033` is a **verbatim move** of `phase2_threat.py:17-287`, rewired to import helpers from `phase2_compiler` and `phase4_attack_resolution`. It passes `malware_target_policy="V033_INCOME_AWARE"`. **Do not recompose it from the six-phase functions.** RNG call order, the overflow-branch contractor expiry (`:53-62`) and the deferred-green skip (`:230`) must stay byte-for-byte equivalent (INV-SEQ-LEGACY-PARITY-01).
- `execute_phase_3_v033` = `phase3_ops.py:161-475`. Its loop calls `player.bot.take_phase3_actions(...)` (unchanged name, so instance monkeypatches in `tests/test_cards_and_directives.py:146`, `tests/test_archetypes.py:757,775` and `tests/test_v170_hash_matches.py:85,93` keep working), then `execute_player_operations_turn(..., collect_income=True, resolve_signature_protocols=True)`, then `execute_pipeline_prep_v033`, then `pass_first_player_marker`.

**Shims.** They must keep **v0.33 semantics regardless of `round_sequence`** (INV-SEQ-SHIM-LEGACY-01), because about 60 tests call them directly with default configs (§9.3):

| Old module | Re-exports |
|---|---|
| `phase1_boot.py` | `from sim.engine.phase1_roll_deploy import *` plus an explicit `__all__` with every name in §3.1 |
| `phase2_threat.py` | `resolve_player_defense_and_wear`, `resolve_corruption_space`, `demote_player_dice_step2a`, `return_player_colored_dice_step2a`; `execute_phase_2 = legacy_v033.execute_phase_2_v033` |
| `phase3_ops.py` | `collect_player_production_income`, `collect_production_income`, `resolve_spook_burn_notice`, `resolve_phreaker_jumper_diagnostics`, `create_colored_die` (attribute kept); `execute_phase_3 = legacy_v033.execute_phase_3_v033` |

Known limitation: 8 historical scripts monkeypatch `sim.engine.phase3_ops.create_colored_die` (`scripts/test_no_dirty_income.py:28`, `compare_block1_vs_block2.py:244`, `test_hazard_face.py:331`, `test_archetype_prodigy.py:65`, `run_v260_telemetry_sweep.py`, `detailed_defense_telemetry.py`, `test_wear_glitch_face.py`, `test_lean_diversity.py`). After the split, purchases bind `create_colored_die` inside `phase6_operations`, so those patches silently stop applying. No test does this. Document the issue in each script header, or patch `sim.engine.phase6_operations.create_colored_die`. Do not add runtime indirection for it.

---

## 4. `core.run_round` Dispatch and End-Game Semantics

### 4.1 `GameEngine` (`sim/engine/core.py`)
- Imports (`core.py:47`): replace them with the six new modules plus `legacy_v033`. Add `Set` to the typing import; `core.py:234` uses it today without importing it.
- **Keep** `_execute_phase_1`, `_execute_phase_2(commitments, defer_green_for_pids=None)` and `_execute_phase_3()` as **legacy façades**: `_execute_phase_2` → `legacy_v033.execute_phase_2_v033` and `_execute_phase_3` → `legacy_v033.execute_phase_3_v033`. About 30 tests call them (§9.3). Keep `_resolve_player_defense_and_wear` too.
- Add new private steps: `_run_phase_2_compiler(commitments) -> CompileResult`, `_run_phase_3_income(commitments)`, `_run_phase_4_attack_resolution(commitments, cr)`, `_run_phase_5_pipeline_shift()`, `_run_phase_6_operations()`.

```python
def run_round(self) -> RoundTelemetry:
    if self.state.game_over:
        raise RuntimeError("Cannot run round on an already finished game")
    if not self.config.is_six_phase:
        return legacy_v033.run_round_v033(self)
    return self._run_round_six_phase()

def _run_round_six_phase(self) -> RoundTelemetry:
    s = self.state
    commitments = phase1_roll_deploy.execute_phase_1(self)                       # P1
    cr = phase2_compiler.execute_compiler_drop(self, commitments)                # P2
    phase2_compiler.check_end_triggers_after_compiler(self, cr)
    tel = self._begin_telemetry(cr, phases=[1, 2])
    if s.game_over:
        return self._finalize_telemetry(tel, attack={R:0,B:0,G:0}, end_phase=2)
    tel.income_by_player = phase3_income.execute_income(self, commitments)       # P3
    tel.phases_executed.append(3)
    attack = phase4_attack_resolution.execute_attack_resolution(self, commitments, cr)   # P4
    tel.phases_executed.append(4)
    if s.game_over:
        return self._finalize_telemetry(tel, attack, end_phase=4)
    shift = phase5_pipeline_shift.execute_pipeline_shift(self)                   # P5
    phase6_operations.execute_operations(self)                                   # P6
    tel.phases_executed += [5, 6]
    if s.is_final_round:
        s.game_over = True
    else:
        s.current_round += 1
        if s.current_round > s.config.max_rounds:
            s.game_over = True
            s.end_reason = EndGameReason.ROUND_LIMIT
    return self._finalize_telemetry(tel, attack, end_phase=6 if s.game_over else None)
```
`_finalize_telemetry` appends to `self.telemetry_history` exactly once per round (INV-SEQ-TELEMETRY-01). `run_game`/`evaluate_end_game` are unchanged.

### 4.2 End-trigger checks (exact semantics)

**`check_end_triggers_after_compiler(engine, cr)`**, run at the end of Phase 2:
1. If `singularity_triggered`, call `apply_singularity_cleanup`. Then `game_over = True`, `is_final_round = False`, `end_reason = TOTAL_WIPEOUT if all(p.is_patient_zero) else SINGULARITY`. Phases 3–6 are skipped. This matches `phase2_threat.py:123-154`.
2. Else if `all(p.is_patient_zero)` (every player breached by *Lose X Secrets* corruption): `game_over = True`, `is_final_round = False`, `end_reason = TOTAL_WIPEOUT`, skip 3–6. Contractors in this branch: call `expire_contractors(engine)` before returning, so supply is conserved.
3. Else if `any(p.is_patient_zero)`: `is_final_round = True`, `end_reason = PATIENT_ZERO`, `tel.final_round_trigger_phase = 2`. **Continue.** Survivors run Phases 3, 4, 5 and 6 (INV-SEQ-FINAL-ROUND-COMPLETE-01). Phase-2 Patient Zeros run nothing further (INV-SEQ-PZ-SKIP-01).

**`check_end_triggers_after_attacks(engine)`**, run at the end of Phase 4 after Snowball Recycle and Contractor Expiration:
1. If `all(p.is_patient_zero)`, including Phase-2 Patient Zeros plus every survivor who breached in Phase 4: `game_over = True`, `is_final_round = False`, `end_reason = TOTAL_WIPEOUT`. Phases 5–6 are skipped. Ranking uses the standard hierarchical tiebreakers only; breach depth is not compared (OQ-4 resolution, §12.1).
2. Else if `any(p.is_patient_zero)`: set `is_final_round = True`. Set `end_reason = PATIENT_ZERO` only if it is not already set. If `final_round_trigger_phase is None`, set it to 4. Survivors run Phases 5 and 6.
3. Never sets Singularity: that is impossible here, because Singularity always exits at Phase 2.

**End of round:** `is_final_round` → `game_over`. Patent Filings in a Final-Round Phase 6 can still add Secrets before scoring (D3.5). `evaluate_end_game` already counts `ready_for_release_dice + in_production_dice` for the tiebreakers (`end_game.py:56-63`). After a completed Final Round, In Production is empty and held dice sit in Scanned, so they count against tiebreaker #4 (OQ-10).

### 4.3 Where each timing lands

| Item | SIX_PHASE location | V033 location (unchanged) |
|---|---|---|
| Version Switch, Pulse | Phase 1 (`phase1_roll_deploy.execute_phase_1`, from `phase1_boot.py:171-182`) | same |
| Version Advance / Spillover / Singularity flag | Phase 2 `execute_compiler_drop` | Step 2A |
| Compile Buffer Overflow cube injection | Phase 2 | Step 2A branch |
| Contractor Expiration | **End of Phase 4**, every round including overflow and Final Rounds (`expire_contractors`). Exception: on a Phase 2 early exit (Singularity or Total Wipeout), expire at Phase 2 via `apply_singularity_cleanup` / branch 2. | `phase2_threat.py:53-62`, `:228-238` |
| Snowball Recycle | End of Phase 4, after damage and before Contractor Expiration | `:222-226` |
| End-game trigger check | End of Phase 2 **and** end of Phase 4 | Step 2C `:240-253` |
| Aegis *Baffle Echo*, DTO *Slush Fund*, Passive Firewall | Phase 4 | Step 2B |
| Omnidyne *Magnetic Splice*, Emergency Hotfix | Phase 5 step 1 | 3B step 1 |
| Prometheus *Algorithmic Arbitrage* | Phase 6 | 3A |
| Meridian *Redundant Crew*, Helix *Brute-Force Bypass* | Phase 1 | Phase 1 |
| First Player pass | End of Phase 6 | End of 3B (`phase3_ops.py:474`) |
| Override availability | `active_version` is unchanged from Phase 2 through Phase 6. The switch still happens at the next Phase 1 (`phase1_boot.py:143-166`), so no code change is needed (INV-SEQ-OVERRIDE-WINDOW-01). | same |

---

## 5. Decision on the `defer_green_for_pids` Mechanism

**Callers found:**
- `web/controller/phase2_actions.py:67` (passes `human_pids`)
- `sim/engine/core.py:231-236` (pass-through)
- `phase2_threat.py:190-220,230` (snapshot capture + skipping contractor expiry)
- `web/controller/phase3_actions.py:58-165` (restores `_pre_step2b_snapshot`, re-runs `resolve_player_defense_and_wear` with `any_shield_allocations`, then `defer_green_malware=True`)
- `:167-267` (human glitch choice)
- Monkeypatching sweep scripts: `scripts/run_v3{10,20,30}_telemetry_sweep.py` and `investigate_*`
- One test: `tests/test_v320_blue_variants.py:421-460` (through the web controller)

It does two jobs: (a) let a human pick Generic `Any` shield allocation **after** damage was auto-resolved, using snapshot rollback; and (b) let a human pick Green Malware targets.

**Decision:**
1. The **SIX_PHASE engine API drops it.** `execute_attack_resolution` takes `any_shield_allocations_by_pid` and `malware_selectors_by_pid` **up front**. The web controller pauses *before* Phase 4 resolves for a human (§8.3), so neither the snapshot nor the rollback is needed. `_pre_step2b_snapshot` and `pending_unblocked_green` are never set on the SIX_PHASE path (INV-SEQ-NO-SNAPSHOT-01).
2. **Retain it on the legacy path only.** `legacy_v033.execute_phase_2_v033(..., defer_green_for_pids)` and `GameEngine._execute_phase_2(..., defer_green_for_pids)` keep their signatures so v0.33 regression and parity tests run unchanged. Once the web migrates (§8), there are no production callers, so mark it `# Deprecated v0.34; remove in v0.35`.
3. Keep the `defer_green_malware` kwarg on `resolve_player_defense_and_wear` (legacy web parity tests). New code must not use it.

---

## 6. Bot API Changes (`sim/bots/`)

**Rule:** every heuristic change below is gated on `game_state.config.is_six_phase` (or on a kwarg the SIX_PHASE engine passes) so that `V033_THREE_PHASE` games stay byte-identical (INV-SEQ-LEGACY-PARITY-01).

### 6.1 `take_operations_actions` (alias kept)
In `base.py:770-777`:

```python
OperationsActionPlan = Phase3ActionPlan          # code alias only; dataclass name kept (base.py:18-20)

class BaseBot:
    def take_operations_actions(self, player_state, game_state, rng) -> Phase3ActionPlan:
        """Phase 6: Operations. Called after Income, Attack Resolution and Pipeline Shift."""
        if type(self).take_phase3_actions is not BaseBot.take_phase3_actions:
            return self.take_phase3_actions(player_state, game_state, rng)    # legacy subclass override
        return Phase3ActionPlan()

    def take_phase3_actions(self, player_state, game_state, rng) -> Phase3ActionPlan:
        """Deprecated alias (v0.33 name)."""
        if type(self).take_operations_actions is not BaseBot.take_operations_actions:
            return self.take_operations_actions(player_state, game_state, rng)
        return Phase3ActionPlan()

def resolve_operations_plan(bot, player_state, game_state, rng) -> Phase3ActionPlan:
    inst = vars(bot)                                   # instance monkeypatch (tests assign lambdas)
    if "take_operations_actions" in inst: return inst["take_operations_actions"](player_state, game_state, rng)
    if "take_phase3_actions" in inst:     return inst["take_phase3_actions"](player_state, game_state, rng)
    return bot.take_operations_actions(player_state, game_state, rng)
```
- Rename the five bots' implementations to `take_operations_actions`: `adaptive_balanced.py:346`, `secops_turtle.py:249`, `venture_greed.py:222`, `accelerationist.py:196`, `reckless_saboteur.py:169`.
- Test-local subclasses that override `take_phase3_actions` (about 40 sites, §9.3) keep working through the delegation.
- In SIX_PHASE, `plan.spook_burn_die_id`, `plan.phreaker_diagnostics_die_id` and `plan.use_omnidyne_override` are **ignored** by Phase 6, because those decisions now belong to Phases 3 and 5. Bots must not spend a Phase-6 budget assuming them.
- **Behavioral note:** the legacy engine calls `take_phase3_actions` *before* collecting income (`phase3_ops.py:178` vs `:182`), so v0.33 plans budget pre-income cash. In SIX_PHASE, Phase 6 plans see post-income, post-damage cash, so bots will buy more.

### 6.2 `choose_scanned_graduates` (new, O2)

```python
def choose_scanned_graduates(self, player_state, n: int, game_state: Optional[GameState] = None,
                             rng: Optional[random.Random] = None) -> List[Die]:
    """Phase 5 step 3: choose exactly min(n, len(scanned_dice)) dice to graduate Scanned → Ready.
    Default priority: Purple, then Colored by descending cost, then Gray; ties by die_id ascending."""
    key = lambda d: (0 if d.color == DieColor.PURPLE else 1 if d.color != DieColor.GRAY else 2,
                     -getattr(d, "cost", 0), d.die_id)
    return sorted(player_state.scanned_dice, key=key)[:n]
```
The engine validates the result (§3.5). It replaces invalid ids but honours a shorter list (OQ-1). Bots may override it; for example, SecOps may prefer shield-heavy Blue or Green dice when Blue threat in the Staging Cup plus stuck cubes is ≥ 2. That is optional and not required for v0.34.

### 6.3 Glitch / sacrifice re-keying
- **Phase 4 Green (new hook).** Add `choose_malware_glitch_targets(self, player_state, in_production_dice, count, game_state=None) -> List[Die]`. Income is already collected and shields have already blocked, so the only cost of a glitch is **future** availability. Default key, lowest value first:
  `(0 if WHITE else 1, 0 if GRAY else 1, 0 if not PURPLE else 1, cost, die_id)`.
  White first is a free Contractor Sacrifice, since contractors expire at the end of Phase 4 anyway. Then Gray (lowest roll value, zero Glitch faces), then the cheapest Colored die, with Purple last. Called only by `malware_target_policy="SIX_PHASE_BOT_HOOK"`. `choose_malware_sacrifice` (`base.py:397-404`) stays for the legacy policy only.
- **Phase 2 corruption glitch** (`choose_dice_to_glitch`, `base.py:514-568`). **No change.** The plan's Step 3 says to re-key "Green / corruption" glitches, but corruption still resolves **before** Phase 3 Income, so protecting high-income dice is still correct there (OQ-14). The only adjustment: the "redundant shield" test already uses the `exited_cubes` threat passed in from Phase 2 (`phase2_threat.py:713-717`), which in SIX_PHASE is exactly the Phase 4 attack. That is correct as-is.
- The engine-internal `glitch_sort_key` at `phase2_threat.py:516-535` (duplicated at `web/controller/phase3_actions.py:224-243`) is used only by the legacy policy. The web copy is deleted in §8.

### 6.4 Release Track valuation
Today every bot buys only Release Level 1 (`release_level < 1`): `adaptive_balanced.py:518-526` (gate `len(total_dice) > 6`), `secops_turtle.py:380-382` (`> 5`), `accelerationist.py:328-330` (ungated). `venture_greed.py` and `reckless_saboteur.py` never buy it.

New helper on `BaseBot`:

```python
def release_pressure(self, player_state, planned_purchases: int = 0) -> int:
    permanent = sum(1 for d in player_state.total_dice if d.color != DieColor.WHITE)
    return max(0, permanent + planned_purchases - player_state.release_bandwidth)
```
In SIX_PHASE, each bot's `take_operations_actions` evaluates RELEASE **before** TRIAGE, and before Patent Filings for Adaptive and Venture. It upgrades when `release_pressure(...) >= 1` and `release_level < 2`, using the same research budget walk as today. SecOps puts DEFENSE L1 first, then RELEASE. Reckless keeps its current no-upgrade identity unless pressure ≥ 2. The legacy branch keeps today's code exactly.

### 6.5 Expected-income-aware Red funding
**The plan's location is wrong.** It cites `commit_shields` "around `base.py:736`", but:
- `base.py:736` is in **`choose_colored_dice_to_return`** (Phase 2 corruption *Return Colored Dice*): `s_prio = 4 if player.money < red_threat else 2`.
- No bot's `commit_shields` reads `money` (base `:443-473`, `adaptive_balanced.py:294-344`, and the other three).
- The "funded Red" generic-shield tiering is **engine-side**, at `phase2_threat.py:377-399` (Tier 2: `player.money < rem_red`). In SIX_PHASE that code runs in Phase 4 *after* income, so it sees post-income cash automatically and needs **no change**.

Implementation:
1. Add `BaseBot.expected_income(player_state, game_state=None, exclude_die_ids=()) -> int`. It lazily imports `sim.engine.phase3_income.preview_player_income` and returns `money` (`$` only, since Red is paid in `$`), excluding the listed dice.
2. `choose_colored_dice_to_return(self, player, count, threat_strengths, expected_income: int = 0)`. At `:736`, use `player.money + expected_income < red_threat`. `return_player_colored_dice_step2a` passes `expected_income = preview_player_income(state, player).money` in SIX_PHASE and `0` in legacy. A refinement for the senior engineer: exclude the candidate die's own income when scoring it.
3. `commit_shields` (Phase 1). Optional for v0.34: add a SIX_PHASE-gated tweak in `AdaptiveBalancedBot.commit_shields` that skips committing a Blue choice face (`has_shield_option`) when the Blue threat is already covered. Not required, so it stays out of the invariants.

### 6.6 Other hook signature updates
- `choose_spook_burn_notice` (`base.py:795-813`) and `choose_phreaker_jumper_diagnostics` (`:815-830`) are now called in Phase 3, before attacks. In SIX_PHASE, Burn Notice's Secret is worth more just before Blue, so the `secrets <= 3` guard is the game-designer's to revisit. No code change is required in v0.34. Bots should not burn an In Production die outside the Final Round (OQ-3).
- `choose_omnidyne_override` is called in Phase 5 step 1. Signature unchanged.
- `choose_contractor_hires` is unchanged. Contractor `+$1` now pays, but valuation changes are a balance follow-up (OQ-16).

---

## 7. Edge Cases

| # | Case | Required behavior | Where |
|---|---|---|---|
| E1 | **Compile Buffer Overflow** (0 exited) | Phase 2 injects 1R/1B/1G (`buffer_overflow_cubes`). No corruption (0 Black). Phase 3 **pays income**. Phase 4: zero attack strengths, no Aegis/Firewall/R2/R3/B1, Snowball Recycle of 0, **Contractor Expiration runs**, end check runs. Phases 5–6 normal. | §3.4, INV-SEQ-OVERFLOW-INCOME-01 |
| E2 | **Singularity** (v3.0 Space 6) | Space 6 effect resolves (e.g., Corrupted Kernel *Lose 1 Secret*). `apply_singularity_cleanup` returns In Production non-White dice to Ready and contractors to supply. `game_over`; reason `SINGULARITY`, or `TOTAL_WIPEOUT` if all players are Patient Zero. **No income** (Phase 3 skipped), so Acoustic/Cipher/Spook and contractor `+$1` do not pay. P2 Chaos Profiteer still pays (Phase 2, OQ-5). | §4.2, INV-SEQ-SINGULARITY-SKIP-01 |
| E3 | **Total Wipeout in Phase 4 after a Phase 2 breach** | Phase 2: player A reaches ≤ 0 Secrets through *Lose X Secrets* → Final Round. A skips 3–6 and keeps its Phase-2 `breach_depth`. Phase 4: B and C (all survivors) breach → `all(is_patient_zero)` → `TOTAL_WIPEOUT`, `game_over`, skip 5–6. Ranking ignores breach depth: A, B and C are ranked by Money > Ready Colored dice > Research > fewest Under Development (OQ-4 resolution, §12.1; replaces `end_game.py:33-36` net_score on the six-phase path). | §4.2 |
| E4 | **Y3 Proprietary Training** in Phase 3 | `+1 Secret` is collected, then the die → Glitched at the end of `collect_player_production_income` (`phase3_ops.py:87-91`). It is gone from In Production before Phase 4: it cannot be a Green target, and its commitment entry (if any) is dropped by `sync_commitments_with_production`. It is eligible as a Jumper Diagnostics target later in Phase 3 (legacy ordering). Phase 5: eligible for Hotfix/Splice (step 1) and for triage (step 4, FIFO tail). The Secret now lands **before** Blue, which can prevent a breach. Watch this in the sweep. | §3.3 |
| E5 | **B3 Air-Gapped Backup** vs the Phase 5 queue | In Phase 3, B3 moves the best Glitched die (`phase3_ops.py:44-57`: Colored > Gray, by cost) → Scanned. Only dice glitched in Phase 1/2 (or earlier rounds) are eligible; Phase 4 Green victims are not. In Phase 5 that die **competes** for `release_bandwidth` with the returning In Production dice (including the B3 die itself, a Blue shield). With the default graduate priority, a colored B3-rescued die usually graduates. When the pool exceeds RB, B3's value falls, because a lower-priority die is held instead. | §3.5, game-designer note |
| E6 | **Spook Burn Notice before Blue** | Resolved in Phase 3 after income, once per Purple `★` die still In Production (OQ-17 resolution). `+1 Secret` before Phase 4. If the burned die was In Production (OQ-3), it already paid this round's income and its shield **no longer blocks** in Phase 4 (INV-SEQ-COMMIT-SYNC-01). | §3.3 |
| E7 | **Phreaker Jumper Diagnostics timing** | Phase 3, after income. Under Development then holds Phase 1 glitches, Phase 2 corruption glitches, and dice held in Scanned from the previous Phase 5 (more common under D1), but **not** Phase 4 Green victims. The `+$1` fallback fires only when Under Development is empty. Diagnostics cash is available to pay Phase 4 Red. | §3.3 |
| E8 | **Corruption "Return Colored Dice" / "Glitch X dice" / "Lose $" before income** | All resolve in Phase 2. A returned die is removed from all zones and its commitment popped (`phase2_threat.py:645-666`), so it pays no income. A corruption-glitched die → Glitched and pays nothing. *Lose $X* reduces pre-income cash, and income is then collected **on top** (not lost). | §3.2, test S-03/S-04 |
| E9 | **Corruption *Lose X Secrets* breach + Red in Phase 4** | The breached player skips Phase 4, so no Red or Blue is applied to them. | INV-SEQ-PZ-SKIP-01 |
| E10 | **Release Bandwidth < starting pool** | Aegis starts at Release Bandwidth **3** (`RULES.md:133,378`), so from round 1 one of its four starter dice is held in Scanned. Omnidyne (RB 5) has slack. This contradicts the plan's "starting pool fits exactly" assumption (OQ-6). | §3.5 |
| E11 | **Final Round triggered in Phase 2** | Survivors run Phase 3 income, Phase 4 attacks, Phase 5 and Phase 6, where bots see `is_final_round = True` and switch to final-round heuristics (no purchases, B2/Y1 conversions, Patent Filings). | §4.2 |
| E12 | **Contractor sacrificed in Phase 2 corruption** | Goes to supply immediately (`phase2_threat.py:586-592`) and pays no income. | unchanged |
| E13 | **Mode B corruption cubes** (`corruption_cubes_resolve_immediately=True`) | R/B/G added to `cr.exited_cubes` in Phase 2 are attacked in Phase 4 and recycled. Acoustic still reads `last_exited_cubes` (copied before the Mode-B adds, `phase2_threat.py:27`). | unchanged |
| E14 | **No survivors need Phase 5 choice** | When `len(scanned) ≤ release_bandwidth` after Production Return, graduation is forced and no hook is needed (the web skips the subphase). | §8 |
| E15 | **Max-round cap** | Unchanged. Checked after Phase 6. | §4.1 |

---

## 8. Web Controller and UI

### 8.1 Phase state machine (`web/controller/core.py`)

| `phase` | `phase_name` (`ROUND_PHASE_NAMES`) | `subphase` values | Human interaction | Leaves via |
|---|---|---|---|---|
| 1 | Roll & Deploy | `waiting_for_roll`, `waiting_for_commit` | hire, roll, reroll, commit (unchanged) | all humans committed → 2 |
| 2 | Compiler Drop & Corruption | `ready_for_compile` | `compile` | game over → 7; else → 3 |
| 3 | Income | `confirm_income` | Preview own income (`preview_player_income`); choose optional Burn Notice die / Diagnostics die; `confirm_income` | all alive humans confirmed → 4 |
| 4 | Attack Resolution | `confirm_attacks` | allocate Generic `Any` shields; order Green targets (incl. contractors); optional Aegis color; `confirm_attacks` | all alive humans confirmed → resolve → game over → 7; else → 5 |
| 5 | CI/CD Pipeline Shift | `choose_graduates` (only if some alive human has `scanned_after_return > release_bandwidth`, or has *Magnetic Splice* Available with Glitched dice, or Emergency Hotfix with >1 Glitched die) | pick Splice/Hotfix die; pick exactly `n` graduates | → 6 |
| 6 | Operations | `player_turn` | buy / upgrade / patent / B2 / Y1 / P1 / P3 / Prometheus / end turn (clockwise queue) | queue empty → `complete_round` → 1 or 7 |
| 7 | Game Over | `game_over` | — | — |

- Replace `core.py:64-65` (`# 1: Boot, ... 4: Game Over`, `"Boot & Configure"`), `:275`, `:328-329` with names from `ROUND_PHASE_NAMES`. Do the same for `phase1_actions.py:537-539` (`"Rogue Agent Compile"`), `phase2_actions.py:337-353` (`4/"Game Over"`, `"Corporate Operations"`), `phase3_actions.py:118-120`, and `serializer.py:100-102,118-120` (`phase = 4` → `7`).
- Rename `phase3_turn_queue` to `operations_turn_queue`, and keep a read/write `phase3_turn_queue` property alias, since `tests/test_archetypes.py` and `tests/test_phase20_sync.py` reference it.
- **The web is SIX_PHASE only** (OQ-7). `new_game` builds `GameConfig(num_players=..., enable_corporate_asymmetry=..., round_sequence=SIX_PHASE)` (`core.py:98-101`).
- `core.py:263` emits "Consultancy Archetype", a **deprecated term**, in the event log. Replace it with "White Hat Operative".

### 8.2 Action modules (split to match the engine)

| New file | Contents | Moves from |
|---|---|---|
| `web/controller/phase2_actions.py` | `compile_drop(controller)`: builds commitments (`:39-49`), calls `phase2_compiler.execute_compiler_drop` + `check_end_triggers_after_compiler`, logs, and builds `last_compile_result` with **only** drop/corruption data. Then either Game Over or **enter Phase 3**: for each bot, `phase3_income.execute_player_income(engine, bot_player)` (simultaneous); for humans, store `preview_player_income`. | `:34-377`. **Delete** the income breakdown at `:69-202` (replaced by `preview_player_income`) and the threat summary at `:207-295` (moves to Phase 4). |
| `web/controller/phase3_income_actions.py` (new) | `confirm_income(controller, player_id, spook_burn_die_id=None, phreaker_die_id=None)` → `execute_player_income(...)` with explicit ids. When all alive humans have confirmed → `_enter_phase_4`. Existing `spook_burn` / `phreaker_diagnostics` endpoints (`phase3_actions.py:725-795`) become Phase 3 actions that record the choice in `meta` (they no longer auto-confirm). | `phase3_actions.py:41-307` (income part), `:725-795` |
| `web/controller/phase4_attack_actions.py` (new) | `_enter_phase_4`: computes `attack_strengths`, builds per-player `threat_summary` previews, resolves bots immediately (store results), sets subphase `confirm_attacks`. `confirm_attacks(controller, player_id, any_shield_allocations=None, glitch_die_ids=None, aegis_color=None)` → `resolve_player_defense_and_wear(..., any_shield_allocations=..., malware_target_policy="SIX_PHASE_BOT_HOOK", malware_target_selector=<priority list from glitch_die_ids, back-filled by bot hook>)`. After the last human: Snowball Recycle, `expire_contractors`, `check_end_triggers_after_attacks` → 7 or `_enter_phase_5`. | `phase2_actions.py:204-295` (summary), `phase3_actions.py:58-276` (allocation/glitch, **without** the snapshot/rollback) |
| `web/controller/phase5_pipeline_actions.py` (new) | `_enter_phase_5`: for bots, `execute_player_pipeline_shift`; for humans, run step 2 (Production Return → Scanned) and compute `n`, then pause in `choose_graduates` if any condition in §8.1 holds, else auto. `choose_graduates(controller, player_id, graduate_die_ids, splice_die_id=None, hotfix_die_id=None)`. Afterwards → `_enter_phase_6`. The existing `use_phreaker_ability` (Omnidyne Splice, `phase3_actions.py:942-1004`) is re-pointed to record `splice_die_id` in Phase 5. | `serializer.py:52-95` (pipeline), `phase3_actions.py:357-384` (bot Splice) |
| `web/controller/phase6_operations_actions.py` (renamed from `phase3_actions.py`) | Everything else in `phase3_actions.py` (buy, upgrade, patent, star, Prometheus, dirty income, end turn, `advance_operations_turns`, `execute_bot_operations`). **Remove** income collection at `:328-333` and `:350-355`, and the bot Splice at `:357-384`. Phase guards `controller.phase != 3` → `!= 6` (`:799,838,882,950,1013,1143,1218,1243,1280`). Remove the `subphase == "confirm_income"` auto-confirm shortcuts (`:629,731,765,1215,1240,1277`). | `phase3_actions.py:310-1305` |
| `web/controller/serializer.py` | `complete_round`: **delete** the duplicate pipeline at `:52-95` (now Phase 5). Keep Final Round, First Player, round increment and Game Over (`phase = 7`). The First Player pass stays here for the web; the engine does it in `phase6_operations.pass_first_player_marker`. | — |

Keep `web/controller/phase3_actions.py` as a re-export shim for one release, so `from web.controller.phase3_actions import ...` in tests still resolves.

Pre-existing web/engine drift that this refactor removes (the web now calls engine functions instead of re-implementing them):

| Drift | Web | Engine |
|---|---|---|
| In Production destination | Already → **Scanned** (`phase3_actions.py:285-298`, `compiler.js:323`) | → Ready (`phase3_ops.py:462-469`) |
| Emergency Hotfix target | `glitched_dice.pop(0)` (`serializer.py:58-64`) | Best colored (`phase3_ops.py:425-438`) |
| Bot income collection | In `compile_drop` (`phase2_actions.py:182-193`) and again attempted in `execute_bot_phase3` (`phase3_actions.py:351`) | Once, in 3A |
| Autonomous Protocol Pulse | Hard-coded +1 (`core.py:281-284`) | `autonomous_pulse_by_version` (`phase1_boot.py:177-182`); harmless at the current all-1 baseline, but should call the engine |

There is also a web-only bug: the first human `confirm_income` moves **every** player's In Production dice to Scanned (`phase3_actions.py:286-298`).

### 8.3 Capabilities (`web/controller/capabilities.py`)
- `can_compile`: phase 2 (`:203`), unchanged.
- `can_confirm_income`: `phase == 3 and subphase == "confirm_income" and not meta["income_confirmed"]` (`:205`).
- New: `can_confirm_attacks` (phase 4), `can_choose_graduates` (phase 5, human pending), `can_splice` / `can_hotfix_bypass` (phase 5).
- `can_spook` / `can_phreaker_diagnostics` → phase 3.
- `can_phreaker` (Omnidyne Splice) → phase 5.
- All operations capabilities currently on `controller.phase == 3` (`:101,109,135,145,208,217,227,244,257,267-270,289,298,307,316,325,336`) → phase 6.

### 8.4 API and schema deltas
New POST routes in `web/server.py`, next to `:180`:

| Route | Payload | Phase |
|---|---|---|
| `/api/game/action/confirm_income` (changed) | `{player_id, spook_burn_die_id?, phreaker_die_id?}`. `glitch_die_ids` / `any_shield_allocations` are **removed**; return 400 if present | 3 |
| `/api/game/action/confirm_attacks` (new) | `{player_id, any_shield_allocations?: {red,blue,green}, glitch_die_ids?: [int], aegis_color?: "red"\|"blue"\|"green"}` | 4 |
| `/api/game/action/choose_graduates` (new) | `{player_id, graduate_die_ids: [int], splice_die_id?, hotfix_die_id?}`. 400 if `len != n` after dedupe or ids not in Scanned | 5 |

`web/schemas.py`:
- `:456-458`: default `phase_name` → `ROUND_PHASE_NAMES[1]`.
- Add `controller_meta["round_sequence"]` and `controller_meta["phase_names"] = ROUND_PHASE_NAMES`.
- Add `pending_graduation: {pid: {"n": int, "candidates": [die], "splice_available": bool, "hotfix_available": bool}}`.
- Add `last_income_result: {pid: IncomeRecord-as-dict}` and `last_attack_result` (the `threat_summary` / `human_threat` / `candidate_glitch_dice` keys move here from `last_compile_result`).
- Keep `last_compile_result` for drop/corruption/overflow/singularity/`is_final_round`/`game_over`.
- Player serializer (`:322-358`): add `"scanned_over_release": max(0, len(scanned) - release_bandwidth)` and `"income_this_round"`. `release_bandwidth` is already serialized at `:327`.

### 8.5 JS files to touch

| File | Change |
|---|---|
| `web/static/index.html:129` | "4 Players (… — 12 Secrets)" → "8 Secrets" |
| `js/components/header.js:42-46` | Use `state.phase_names[state.phase]` (fallback `state.phase_name`); drop the hard-coded "Compiler Drop & Defense" / "Operations & Pipeline Prep" |
| `js/components/action_dock.js` | Branches at `:62` (1), `:317` (2), `:396` (3 → split into 3 Income, 4 Attack Resolution [the allocation/glitch UI currently inside the `confirm_income` block], 5 Choose Graduates, 6 Operations), `:1151` (`4` → `7`). Text at `:765` ("Confirming clears In Production … Scanned Box") moves to the Phase 5 panel. |
| `js/state.js:66,75` | `phase === 3` → `phase === 6` (Prometheus discount and patch toggles); `:95` glitch/Any selection reset → `phase !== 4 \|\| subphase !== "confirm_attacks"`; add `selectedGraduateIds` reset for `phase !== 5` |
| `js/api.js:214` | `confirmIncome(spookBurnDieId, phreakerDieId)`; add `confirmAttacks(...)` and `chooseGraduates(...)` |
| `js/components/player_mats.js` | `:299,:343` `phase === 3` → `6` (turn highlight); `:575` "(1 die Glitched -> Ready in P3B)" → "in Phase 5"; `:587`, `:920`, `:932` tooltips re-timed to Phase 5; `:595` Scanned Box header shows `Release Bandwidth: n / release_bandwidth` and highlights overflow; `:46` *Magnetic Splice* description unchanged except timing |
| `js/components/compiler.js:322-323` | Pipeline summary in D1 order: Hotfix/Splice → In Production → Scanned → Scanned → Ready (≤ Release Bandwidth, your choice) → Glitched → Scanned (≤ Triage Bandwidth) |

---

## 9. Invariants

| ID | Statement | Checked by |
|---|---|---|
| **INV-SEQ-INCOME-BEFORE-ATTACK-01** | In SIX_PHASE, income is collected **exactly once** per surviving player per round, strictly after Phase 2 (all corruption resolved) and strictly before any Phase 4 damage. No income is collected in Phases 1, 2, 4, 5 or 6. | S-01, S-02, S-03, S-04 |
| **INV-SEQ-CONTRACTOR-EXPIRY-01** | Contractors hired or rolled in Phase 1 that survive Phase 2 are present (`contractor_dice` and In Production) during Phase 3 and pay their face. After Phase 4, `contractor_dice == []` for every player, no WHITE die is in any zone, and `contractor_supply == contractor_supply_total`. | S-05, S-06 |
| **INV-SEQ-PZ-SKIP-01** | A player who becomes Patient Zero in Phase 2 has no change to money, research, secrets, `breach_depth` or dice zones from Phases 3–6 (contractor return excepted). They are not attacked in Phase 4 and take no Operations Turn. | S-07 |
| **INV-SEQ-FINAL-ROUND-COMPLETE-01** | When a Final Round is flagged in Phase 2 (Phase 4), every survivor executes Phases 3–6 (5–6) before `game_over`, unless a Total Wipeout ends the game at Phase 4. | S-08, S-09 |
| **INV-PIPE-RELEASE-CAP-01** | In Phase 5, the number of dice moving Scanned → Ready ≤ `release_bandwidth` (Hotfix/Splice dice are separate and come from Glitched). **No die moves In Production → Ready directly.** | S-12, S-13 |
| INV-PIPE-PROD-TO-SCANNED-01 | After Phase 5 step 2, `in_production_dice == []` and no WHITE die is in `scanned_dice`. | S-12 |
| INV-PIPE-GRAD-CHOICE-01 | Graduates ⊆ Scanned at the start of step 3, `count ≤ min(len(scanned), release_bandwidth)` (the player may graduate fewer; OQ-1 resolution), and invalid or duplicate ids are replaced by the default priority up to the requested count. A short list is never back-filled. | S-14 |
| INV-PIPE-PURCHASE-READY-01 | Phase 6 purchases (market, reserve, Prometheus) go straight to Ready and do not consume this round's or next round's Release Bandwidth. | S-15 |
| INV-SEQ-SINGULARITY-SKIP-01 | Singularity ends the game at the end of Phase 2. Phases 3–6 do not run, In Production non-White dice return to Ready, and contractors return to supply. | S-10 |
| INV-SEQ-WIPEOUT-01 | If every player is Patient Zero at the end of Phase 2 or Phase 4, `end_reason = TOTAL_WIPEOUT` and the game ends at that phase. | S-09, S-19 |
| INV-SEQ-OVERFLOW-INCOME-01 | On Compile Buffer Overflow: 1R/1B/1G are added in Phase 2, Phase 3 income is paid, Phase 4 applies 0 damage, and contractors expire at the end of Phase 4. | S-11 |
| INV-SEQ-COMMIT-SYNC-01 | Phase 4 counts a shield only if its die is still In Production at Phase 4 start. | S-16 |
| INV-SEQ-OVERRIDE-WINDOW-01 | `active_version` does not change between the start of Phase 2 and the end of Phase 6. Override timings follow D4. | S-21 |
| INV-SEQ-NO-SNAPSHOT-01 | SIX_PHASE never sets `_pre_step2b_snapshot` or a non-zero `pending_unblocked_green`. | S-22 |
| INV-SEQ-SHIM-LEGACY-01 | `phase2_threat.execute_phase_2`, `phase3_ops.execute_phase_3`, `GameEngine._execute_phase_2/_execute_phase_3` keep v0.33 semantics whatever `round_sequence` is. | the existing suite |
| INV-SEQ-LEGACY-PARITY-01 | With `round_sequence=V033_THREE_PHASE` and a fixed seed, `run_game()` yields the same `EndGameResult` (rankings, money, secrets, rounds, end_reason) and per-round `staged/exited/attack` telemetry as commit `20e8c80`. Capture golden fixtures **before** refactoring. | S-23 |
| INV-START-SECRETS-FLAT-01 | SIX_PHASE: 8 Secrets at 2P/3P/4P (DTO 9 with asymmetry). V033: 8/8/12 (DTO 9/9/13). | S-17, S-18 |
| INV-SEQ-TELEMETRY-01 | Exactly one `RoundTelemetry` per executed round. `phases_executed ∈ {[1,2], [1,2,3,4], [1,2,3,4,5,6]}`. `income_by_player` keys equal the survivors entering Phase 3. | S-20 |
| INV-SEQ-MARKER-01 | The First Player Marker passes exactly once per completed six-phase round, at the end of Phase 6. | S-15 |

---

## 10. Documentation and Asset Change Checklist

### 10.1 `RULES.md` (glossary-governed; canonical terms only)
- [ ] `:1` header → `v0.34.0`.
- [ ] `:141-144` Setup secrets → **8 at every player count (DTO 9)**. Delete the 4P `[TUNE: v0.21.0 9-round buffer parity]` line.
- [ ] `:145` First Player resolves **Operations Turn order in Phase 6**.
- [ ] `:151-154` "3 Streamlined Phases" → six phases with the approved names and modes.
- [ ] `:158-159` Override timing: "remains current through Phase 2B and Phase 3" → "through **Phases 3–6**". Defensive overrides in **Phase 4**, operational overrides in **Phase 5** (Magnetic Splice) and **Phase 6** (Algorithmic Arbitrage).
- [ ] `:189-208` Phase 2 → "Phase 2: Compiler Drop & Corruption". Keep the corruption effects. `:206` "usable through Phase 2B … Phase 3" → "Phases 3–6". `:208` Singularity "Step 2B and Phase 3 are skipped" → "Phases 3–6 are skipped".
- [ ] New "Phase 3: Income" section from `:253-255` (Collect Income & Special Outputs + Signature Protocol timing). It explicitly includes White Contractor dice. Burn Notice and Jumper Diagnostics resolve here.
- [ ] `:210-232` → "Phase 4: Attack Resolution". **Delete** "Income Forfeiture" (`:227`). Keep Defensive Shield Sacrifice and Contractor Sacrifice. `:232` Snowball Recycle & Contractor Expiration at the **end of Phase 4**. `:233-235` Buffer Overflow: "no attacks occur this round; income is still collected in Phase 3".
- [ ] `:237-243` Step 2C → End Game Trigger checks at the end of Phase 2 and Phase 4, with Final Round semantics per D3.5 (survivors complete every remaining phase; a Phase-2 Patient Zero skips Phases 3–6; Total Wipeout at either check).
- [ ] `:269-277` 3B → "Phase 5: CI/CD Pipeline Shift" in D1 order (Emergency Hotfix & Magnetic Splice → Production Return to **Scanned Box** → Scanned Graduation ≤ Release Bandwidth, *dice of your choice* → Conveyor Triage ≤ Triage Bandwidth). Move "Uncapped Research Storage" and "Pass First Player" to Phase 6.
- [ ] `:251-267` 3A → "Phase 6: Operations" (Operations Turns, clockwise). Remove "Collect Income". `:265-266` purchases still go directly to Ready for Release ("available to roll next round", O3).
- [ ] §6 card text: `:323` R1, `:325` R3, `:327` B1 (Phase 4 conditional), `:328` B2 "[Phase 3 — Operations]" → "[Phase 6 — Operations]", `:329` B3 (Phase 3), `:331-333` G1–G3, `:335` Y1 → Phase 6, `:336` Y2, `:337` Y3 (Phase 3).
- [ ] §6D timing columns: `:377` Omnidyne → "Phase 5: Step 1"; `:378` Aegis and `:379` DTO → "Phase 4"; `:381` Prometheus → "Phase 6: Operations Turn"; `:389` Phreaker, `:390` Acoustic, `:391` Spook, `:393` Cipher → "Phase 3: Income".
- [ ] §7 Glossary:
  - `:426` First Player → Phase 6.
  - `:432-434` Cube Tower / Staging Cup / Exit Tray → "Phase 2: Compiler Drop & Corruption".
  - `:438-441` Attack/Red/Blue/Green Cubes → "Phase 4".
  - `:442` Black Cubes → "Phase 2".
  - `:446` Version Switch → "through Phases 3–6".
  - `:447` Snowball Recycle → end of Phase 4.
  - `:448` Compile Buffer Overflow → add "income is still collected".
  - `:456` Ready for Release (drop "surviving In Production dice"; add Hotfix/Splice dice).
  - `:457` In Production Area ("deployed through Phases 2–4 … move to the Scanned Box in Phase 5").
  - `:458` Income Slot (Phase 3).
  - `:462` Scanned Box (D1 routing).
  - `:463` Personal Reserve (Phase 6).
  - `:472` Triage Track (Phase 5 Step 4).
  - `:473` Release Track & Release Bandwidth (Phase 5 Step 3; caps all dice returning to Ready from Scanned, including In Production returns).
  - `:475` Patent Filing (Phase 6).
  - `:476` Emergency Hotfix (Phase 5 Step 1).
  - `:477` Passive Firewall (Phase 4).
  - `:485` White Contractor Dice ("expire at the end of Phase 4"; "pay income in Phase 3").
  - `:491` Dual-Output Face (income in Phase 3).
  - `:492-493` shields → Phase 4.
  - `:499-501` replace the three Phase entries with **six**.
  - `:502` Two-Stage Defensive Blocking (Phase 4).
  - `:503` Unpaid Ransom Leak (Phase 4).
  - `:504` Defensive Shield Sacrifice (Phase 4 / Phase 2 corruption).
  - `:505` Contractor Sacrifice (Phase 1 / 2 / 4).
  - `:506` Total Data Breach ("in Phase 2 or Phase 4 … skips the remaining phases").
  - `:507` Singularity ("skipping Phases 3–6").
  - `:508` Total Wipeout ("at the end of Phase 2 or Phase 4; remaining phases are skipped"). Redefine the entry: drop *Net Wipeout Score* and rank by the standard hierarchical tiebreakers only. Update §5 "Total Wipeout Ending" to match (OQ-4).
  - **New entry (approved, OQ-13):** **Final Round** (End Game Rule): the round in which any player becomes Patient Zero. Survivors complete every remaining phase, then go to scoring.
- [ ] **Flag, do not invent:** the glossary has **no "Final Round" entry** although `:238`, `:506` and D3.5 rely on the term (OQ-13). The plan's "Hotfix bypass" label is not a canonical term; use "Emergency Hotfix & Magnetic Splice". "Production Return", "Scanned Graduation" and "Conveyor Triage" appear in §4 (`:272-274`) but not in §7. "Income Forfeiture" disappears (§4 only, never in §7).

### 10.2 `pnp/generate_pnp.py`
- [ ] Player-aid strips `:1288-1306` (Phase 2/3 boxes) → six boxes from `ROUND_PHASE_NAMES`. Remove "In Production -> Ready" (`:1305`). Add D1 routing.
- [ ] Pocket-card cheat sheet `:1677-1680` (P1/P2/P3 lines) → six-phase summary. `:1686` conveyor bar: add "In Production → Scanned".
- [ ] Setup text: `:770` "**12** (4P)" → flat 8; `:1458` "**12 Secrets**" → 8.
- [ ] Re-timed card strings: `:117` (Prometheus "Phase 3 Operations" → Phase 6), `:225` (Cipher → Phase 3 Income), `:256` (contractor "after Phase 2" → "after Phase 4"; add "+$1 pays in Phase 3"), `:321`, `:335`, `:350` (B2 → Phase 6), `:357`, `:365`, `:372`, `:379`, `:387` (Y1: income Phase 3, pay in Phase 6), `:401`, `:667` (Reserve "P3A" → Phase 6), `:685` ("P2B & P3" → "Phases 3–6"), `:780`, `:787`, `:929` (research spend → Phase 6), `:842` ("SCANNED -> READY (P3B)" → Phase 5), `:884` ("RETURNS TO READY IN P3B" → "MOVES TO SCANNED IN PHASE 5"), `:934` (Firewall "P2B" → Phase 4), `:988` and `:1017` (Triage/Hotfix "P3B" → Phase 5), `:1081` ("P2B and P3" → "Phases 3–6"), `:1129` ("Phase 3A Operations" → Phase 6), `:1209` (Phase 2 cube summary: corruption in Phase 2, attacks in Phase 4), `:1577` ("&" outputs "in Phase 3"), `:1030` (Glitched Box sources: Phase 1 glitches, Phase 2 corruption, Phase 4 Green malware).
- [ ] Player mat: add the Scanned Box annotation "In Production → Scanned → Ready (≤ Release Bandwidth)". Graphic-designer layout review, then regenerate the PDFs.

---

## 11. Test Plan

### 11.1 New `tests/test_v340_six_phase_sequence.py`
All tests use `GameConfig(num_players=N, round_sequence=SIX_PHASE)` unless noted. Use stub bots that subclass `BaseBot` with deterministic hooks, and force tower output by monkeypatching `engine.state.tower.drop` to return fixed exits.

| ID | Test | Asserts |
|---|---|---|
| S-01 | `test_green_no_longer_removes_income` | A Red `+$2` income die is glitched by 1 unblocked Green in Phase 4. Player money includes +2. The die is in Glitched after Phase 4. |
| S-02 | `test_income_collected_once_between_phase2_and_phase4` | Spy on `collect_player_production_income` call order relative to `execute_compiler_drop` and `resolve_player_defense_and_wear`. Exactly one call per survivor. |
| S-03 | `test_corruption_cash_loss_lands_before_income` | Space *All lose $2*, money $1, income $3 → final money (pre-attack) = 0 + 3 = 3. |
| S-04 | `test_corruption_glitch_and_return_before_income` | A die glitched or returned by corruption pays 0 in Phase 3. Return pops its commitment. |
| S-05 | `test_contractor_plus1_face_pays_in_phase3` | A White die on `+$1` in Income gives +1 money. |
| S-06 | `test_contractors_expire_end_of_phase4_supply_conserved` | After Phase 4: `contractor_dice == []`, no WHITE in any zone, `contractor_supply == contractor_supply_total`. Includes the overflow round and a Contractor Sacrifice vs Green. |
| S-07 | `test_phase2_patient_zero_skips_phases_3_to_6` | *Lose 1 Secret* at 1 Secret → PZ. Money, research, secrets, breach_depth and zones unchanged by income, attack, pipeline and ops. Bot `take_operations_actions` not called. |
| S-08 | `test_phase2_breach_survivors_run_3_to_6` | Other players collect income, take Phase 4 Red/Blue, shift pipeline, run ops (spy). `is_final_round`, then `game_over` after `run_round`. `end_reason == PATIENT_ZERO`. `final_round_trigger_phase == 2`. |
| S-09 | `test_phase4_wipeout_after_phase2_breach` | E3 → `TOTAL_WIPEOUT`. Phases 5–6 not executed (`phases_executed == [1,2,3,4]`). Ranking by `net_score`. |
| S-10 | `test_singularity_skips_phases_3_to_6` | Space 6 filled → no income. In Production → Ready. Contractors returned. `phases_executed == [1,2]`. Corrupted Kernel *Lose 1 Secret* applied. |
| S-11 | `test_buffer_overflow_still_pays_income` | 0 exits → staging +1R/1B/1G, income paid, 0 damage, contractors expired at end of Phase 4. |
| S-12 | `test_phase5_order_and_production_routes_through_scanned` | Assert after each step: Hotfix die Glitched → Ready; all In Production → Scanned (none → Ready directly); graduates ≤ RB; triage ≤ TB from Glitched. Newly triaged dice do not graduate the same round. |
| S-13 | `test_release_bandwidth_caps_scanned_to_ready` | 6 dice in Scanned after return, RB 4 → exactly 4 Ready, 2 held. `scanned_held_by_player == 2`. |
| S-14 | `test_choose_scanned_graduates_priority_and_validation` | Default order Purple > Colored by cost > Gray. Invalid / duplicate ids are replaced up to the requested count. Returning fewer than `n` (including 0) is honoured, not back-filled (OQ-1). |
| S-15 | `test_purchases_go_to_ready_bypass_cap_and_marker_passes_once` | Buy 2 dice in Phase 6 → in Ready. Next round both roll even if RB is full. `first_player_index` advanced by 1. |
| S-16 | `test_burn_notice_before_blue_and_commit_sync` | Spook Purple `★` → +$2 and Burn Notice +1 Secret before Phase 4. 1 unblocked Blue at 1 Secret → survives. Burning an In Production Blue shield die removes its block (INV-SEQ-COMMIT-SYNC-01). |
| S-17 | `test_flat_8_starting_secrets_all_counts_dto_9` | 2P/3P/4P → 8. DTO with asymmetry → 9. |
| S-18 | `test_legacy_flag_pins_4p_to_12` | `GameConfig.legacy_v033(num_players=4)` → 12 (DTO 13). An explicit dict overrides. |
| S-19 | `test_phase2_all_breach_is_total_wipeout` | *Lose X Secrets* hits everyone → `TOTAL_WIPEOUT` at Phase 2. Contractors returned. |
| S-20 | `test_round_telemetry_six_phase_fields` | `phases_executed`, `income_by_player`, `scanned_held_by_player`, `phase_snapshots` keys, one telemetry per round. |
| S-21 | `test_override_timings_six_phase` | Aegis/DTO in Phase 4, Splice in Phase 5 step 1, Prometheus in Phase 6. A pending version advance does not change `active_version` before the next Phase 1. |
| S-22 | `test_six_phase_never_sets_pre_step2b_snapshot` | — |
| S-23 | `test_legacy_sequence_parity_golden` | V033 config with 3 fixed seeds × 2P/3P/4P, compared against JSON fixtures captured at `20e8c80` (`tests/fixtures/v033_parity/*.json`). |
| S-24 | `test_y3_moves_to_glitched_in_phase3_not_green_target` | E4. |
| S-25 | `test_b3_rescued_die_competes_for_release_bandwidth` | E5 with the pool > RB. |
| S-26 | `test_phreaker_diagnostics_phase3_excludes_phase4_victims_and_fallback` | E7. |
| S-27 | `test_malware_targets_six_phase_default_key` | White → Gray → cheapest Colored → Purple. Fizzle when In Production is empty. |
| S-28 | `test_take_operations_actions_alias_resolution` | Subclass override of the old name, of the new name, an instance lambda for each, all resolved by `resolve_operations_plan` and the legacy shim. |
| S-29 | `test_release_track_valued_when_dice_exceed_bandwidth` | SIX_PHASE bot with 5 permanent dice, RB 4, enough research → `"RELEASE"` in `track_upgrades` before `"TRIAGE"`. The V033 config keeps the old choice. |
| S-30 | `test_web_six_phase_state_machine` | `GameController`: phase walks 1 → 2 → 3 (`confirm_income`) → 4 (`confirm_attacks`) → 5 (`choose_graduates` when overflowing) → 6 → 1. Game over = 7. `phase_name` values equal `ROUND_PHASE_NAMES`. New endpoints validate payloads (400 on bad `graduate_die_ids`). |

### 11.2 Existing tests that will need re-pinning or rewriting
Found by grepping for 4P = 12 Secrets, Phase 3 income timing, In Production → Ready, and the web phase machine.

**A. Re-pin to `GameConfig.legacy_v033(...)`, or update to 8 (4P starting Secrets):**
- `tests/test_v100_rules.py:31-39` (`get_starting_secrets(4) == 12`), `:80` (`player.secrets == 12`)
- `tests/test_v210_rules.py:19-28` (`starting_secrets_by_player_count[4] == 12`, players 12)
- `tests/test_web_api.py:129` (`p0_4p["secrets"] == 12`), `:933` (13 = 12 + DTO). Update to 8 / 9: the web is SIX_PHASE only.

**B. Web phase machine (rewrite for phases 1–6/7 and the new endpoints):**
- `tests/test_web_api.py` (phase asserts `:86,:253,:279,:705`; 25 `compile_drop`/`confirm_income` calls)
- `tests/test_v320_blue_variants.py:421-460` (human B3 + `confirm_income(glitch_die_ids=...)` → `confirm_attacks`; also `:457` sets `pending_unblocked_green`)
- `tests/test_v091_rules.py:383-414` (`compile_drop` overflow log / `last_compile_result`)
- `tests/test_variants_and_web.py` (3 phase asserts; `:320-336` B3/Gray stay Ready, `:402-405` secrets +1)
- `tests/test_phase20_sync.py` (`:14,:201` `execute_phase_3(ctrl.engine)` legacy shim on a web engine; `:184,:202` `ready_dice` assertions; references `phase3_turn_queue`)
- `tests/test_archetypes.py` (`phase3_turn_queue` / `_advance_phase3_turns` references)

**C. Should pass unchanged through the legacy shims (INV-SEQ-SHIM-LEGACY-01). Verify, do not edit:**
- Direct `execute_phase_3` / `_execute_phase_3` callers: `test_v220_rules.py:389-566` (incl. `test_green_glitched_die_forfeits_income` `:389` and production → Ready `:479-490`), `test_v230_rules.py:275-416` (`:278`, `:382` Ready asserts), `test_v250_modular_setup.py:547-575` (`:551`), `test_v240_rules.py:73,559`, `test_v260_variable_dice_costs.py:232-428`, `test_v280_terminal_upgrades.py:59-295`, `test_model_c_patches.py:116-200`, `test_v290_rules_streamlining.py:342`, `test_v170_hash_matches.py:86,94`, `test_engine_phases.py:165`, `test_cards_and_directives.py:149`, `test_scoring_and_wipeout.py:192`, `test_v160_rules.py:89,116`, `test_v130_archetypes.py:45`, `version_baselines/test_v05_rules.py:184,194`
- Direct `execute_phase_2` / `_execute_phase_2` callers in `test_v091_rules.py`, `test_v150_corruption_tracks.py`, `test_v310_threat_defense.py`, `test_v330_step2a_and_singularity.py`, `version_baselines/*`
- Ready-zone assertions after legacy calls: `test_v091_rules.py:233`, `test_v320_blue_variants.py:334-335`, `version_baselines/test_v05_rules.py:364-365,416-417`, `version_baselines/test_v08_rules.py:654`

**D. Calls `run_round()`/`run_game()` under the default (now SIX_PHASE). Re-run, and re-pin to legacy if an assertion is sequence-specific:**
- `tests/test_determinism.py` (self-comparison; expected to pass)
- `tests/test_v160_rules.py:157` (asserts only zero dirty income; expected to pass)
- `tests/version_baselines/test_v05_rules.py:294-321` (`test_total_wipeout_skips_phase3_in_run_round`; TrackingBot overrides `take_phase3_actions`; in SIX_PHASE the wipeout happens in Phase 4 and Phase 6 is skipped, so it is expected to pass through the alias. If the forced setup no longer wipes out because Phase 3 income adds Secrets, pin it to legacy.)

**E. Bot-plan unit tests that call `bot.take_phase3_actions(...)` directly** (`test_scoring_and_wipeout.py:224,264,404`, `test_v260_variable_dice_costs.py:469`, `test_system_reboot.py:155`, `version_baselines/test_v04_rules.py:324,336`): these go through the alias. Expected to pass because the engine is not involved. If they use a default (SIX_PHASE) config, the §6.4 Release valuation can add `"RELEASE"` to `track_upgrades`. Assert on specific fields, or pin to legacy.

---

## 12. Open Questions for Orchestrator

| ID | Question | Recommendation |
|---|---|---|
| OQ-1 | Scanned Graduation is written "up to `release_bandwidth`". May a player graduate **fewer** than the bandwidth allows? | **No.** Graduate exactly `min(len(Scanned), RB)`; the player chooses *which*, not *how many*. Holding back has no benefit and only adds UI. |
| OQ-2 | Do Phase 3 Signature Protocols (Burn Notice, Jumper Diagnostics, Acoustic, Cipher, Spook `+$2`) require the Purple `★` die to **still be In Production** after Phase 2 corruption? Legacy uses a Phase-1 latch (`purple_star_available`, `phase3_ops.py:303-308`), so a corruption-glitched Purple still fires Burn Notice and Diagnostics but not its cash (inconsistent). | **Require In Production at Phase 3 start** for every Purple `★` effect, consistent with "collect … from every die still In Production". |
| OQ-3 | May Burn Notice target a die that is **In Production** during Phase 3, which removes its shield before Phase 4? | **Allow it** (the rules say "1 owned colored module die"), with INV-SEQ-COMMIT-SYNC-01 removing its shield. Bot default: never burn an In Production die outside the Final Round. |
| OQ-4 | A Phase-2 Patient Zero skips Phase 4, so their `breach_depth` is frozen and can outrank deeper Phase-4 breaches in a Total Wipeout. Accept? | **Accept** (follows D3.4 literally). Add one line to the Total Wipeout rule text. |
| OQ-5 | P2 Chaos Profiteer (`+$2` per exited Black, `phase2_threat.py:116-121`; a legacy sim-only star code, not in RULES §6) stays at the end of Phase 2 (pays even on Singularity) or moves to Phase 3? | **Keep at end of Phase 2** for parity. It is outside the canonical card set. |
| OQ-6 | Aegis starts at Release Bandwidth **3** but owns 4 starter dice, so it holds one die in Scanned from round 1. The plan assumes the starting pool fits exactly. | **Accept for v0.34 and measure** Aegis's win rate in the Step 7 sweep. If it is an outlier, model Aegis RB 4 (game-designer, with sign-off). |
| OQ-7 | Should the web keep supporting `V033_THREE_PHASE`? | **No.** The web is SIX_PHASE only; rewrite the web tests (§11.2 B). Two web state machines would double the JS branches. |
| OQ-8 | Conveyor Triage (Glitched → Scanned) choice: legacy FIFO. Under O2's "physical box, not a queue" reasoning, physical players would choose. | **Rules text says "dice of your choice".** The sim keeps FIFO in v0.34 (no new hook), to limit scope. Add `choose_triage_dice` in v0.35 if the designer wants it. |
| OQ-9 | Which Glitched die does Emergency Hotfix take? The engine takes the best colored die; the web takes the first. | **Player's choice** (web humans pick; bots use the engine default). |
| OQ-10 | Phase 5 in the Final Round moves all In Production dice to Scanned and holds overflow. That changes tiebreakers #2 (Ready Colored dice) and #4 (fewest Under Development) compared with v0.33. Run Phase 5 in the Final Round? | **Yes, per D3.5** ("survivors complete every remaining phase"). The game-designer should note the tiebreaker shift in FINDINGS. |
| OQ-11 | Phase 2 corruption glitch / return choices for **web humans** are still auto-chosen by the human's proxy bot (pre-existing). Add human choice now? | **Out of scope for v0.34.** Log it as a follow-up. |
| OQ-12 | Buffer overflow: R2 Threat Bounty ("0 unblocked Red this round → +$2") did not pay in v0.33 because Step 2B was skipped. Keep? | **Keep (no payout).** Phase 4 "resolves nothing" (D3.7). |
| OQ-13 | Glossary gaps: no "Final Round" entry, and no entries for the Phase 5 step names. The plan's "Hotfix bypass" is not canonical. | **Ask the user** to approve a "Final Round" glossary entry. Use the existing §4 names "Production Return", "Scanned Graduation" and "Conveyor Triage" in rules text only, and call step 1 "Emergency Hotfix & Magnetic Splice". No new terms without approval. |
| OQ-14 | Plan Step 3 says to re-key **Green and corruption** glitch choices by future roll value "since income has already been collected". Corruption glitches resolve in Phase 2, **before** income. | **Re-key Phase 4 Green only.** Keep the income-aware key for Phase 2 corruption glitches. |
| OQ-15 | Plan Step 3 places the expected-income Red check in `commit_shields` at `base.py:736`. That line is in `choose_colored_dice_to_return`, and no `commit_shields` reads money. | **Apply it in `choose_colored_dice_to_return`** (Phase 2, pre-income). The engine's Phase 4 generic-shield Tier 2 sees post-income cash automatically. No mandatory `commit_shields` change. |
| OQ-16 | The contractor `+$1` face now pays, but bot hire heuristics are unchanged. | **Unchanged in v0.34.** Measure contractor hires and ROI in the sweep. |
| OQ-17 | Two Purple `★` dice in one round: Burn Notice and Diagnostics fire once (legacy) or once per die? | **Once per round** (legacy parity); cash effects stay per die. |

### 12.1 Resolutions (Orchestrator + User, 2026-11-05) — these override the recommendations above

**User rules decisions**

| ID | Resolution | Implementation impact |
|---|---|---|
| OQ-1 | **Graduate as many as you see fit:** any number from 0 to `min(len(Scanned), release_bandwidth)`, with the player choosing which dice. *(Overrides the recommendation.)* | `choose_scanned_graduates(player, state, max_n) -> List[die_id]` may return fewer than `max_n`. The engine validates `len ≤ max_n` and does **not** back-fill when the bot returns fewer. It back-fills only invalid IDs, up to the count the bot asked for. INV-PIPE-RELEASE-CAP-01 becomes `graduated ≤ RB`. Default bot policy graduates the maximum. The web `choose_graduates` step allows selecting fewer. |
| OQ-2 | **Yes.** The Purple `★` die must still be In Production at the start of Phase 3 for any Signature Protocol to fire. | Retire the `purple_star_available` latch on the six-phase path (`phase3_ops.py:303-308`). |
| OQ-3 | **Yes.** Burn Notice may target an In Production die. Its shield is removed before Phase 4. | As recommended. |
| OQ-4 | **Ignore breach depth.** In a Total Wipeout, players are ranked **only** by the standard hierarchical tiebreakers: Money > Active Colored Module Dice in Ready for Release > Research Tokens > fewest dice Under Development > shared. *(Overrides the recommendation.)* | `end_game.py`: on the six-phase path, Total Wipeout ranking drops the `secrets`/`breach_depth` key; the legacy path keeps Net Wipeout Score. `breach_depth` stays recorded in telemetry only. **Glossary impact:** the canonical term *"Total Wipeout Ending & Net Wipeout Score"* (RULES §7.6, §5) must be redefined, with *Net Wipeout Score* retired from the rules. This is user-approved as part of this decision. `CLAUDE.md` Core Design Pillars still mention Net Wipeout Score; the Orchestrator flags this to the user rather than editing it. |
| OQ-8 | **Rules: "die of your choice"** for Conveyor Triage. The sim stays FIFO in v0.34. | As recommended. |
| OQ-9 | **Player's choice** for the Emergency Hotfix target. | As recommended. |
| OQ-13 | **Approved:** a new **"Final Round"** glossary entry, and naming Phase 5 step 1 **"Emergency Hotfix & Magnetic Splice"**. | Add a Final Round row to RULES §7.6, defined as: the round in which any player becomes Patient Zero; survivors complete every remaining phase, then go to scoring. |
| OQ-17 | **Fire once per Purple `★` die.** Two Purple `★` faces trigger the Signature Protocol twice (e.g., two Burn Notices, two Jumper Diagnostics). *(Overrides the recommendation.)* | Iterate Purple `★` dice still In Production at Phase 3. Each resolves its protocol independently. Burn Notice may not target the same die twice. Telemetry gains `purple_star_triggers_per_round`. **Balance watch:** Spook is already at a 47% win rate, so track Spook and double-trigger frequency in the Step 7 sweep. |

**Engineering questions — the spec's recommendations are adopted as written:** OQ-5, OQ-6, OQ-7, OQ-10, OQ-11, OQ-12, OQ-14, OQ-15, OQ-16.

**Test matrix additions:**
- Graduate fewer than RB (including 0).
- Two Purple `★` → two protocol triggers.
- A glitched Purple fires nothing.
- Total Wipeout ranked purely by tiebreakers. A Phase-2 Patient Zero with shallower depth does **not** automatically outrank.

---

## 13. Known Contradictions Between the Current Code and the Plan's Assumptions

1. **The web already routes In Production → Scanned** (`web/controller/phase3_actions.py:285-298`, `web/static/js/components/compiler.js:323`), while the engine routes to Ready (`sim/engine/phase3_ops.py:462-469`). The v0.33 web and sim disagree today, and the plan's v0.33 metrics are engine-only.
2. **Web bot income is collected inside `compile_drop`** (`phase2_actions.py:182-193`), and `execute_bot_phase3` tries again (`phase3_actions.py:351`). The first human `confirm_income` moves **every** player's dice (`phase3_actions.py:286-298`).
3. **Web Emergency Hotfix takes `glitched_dice[0]`** (`serializer.py:58-64`), while the engine takes the best colored die (`phase3_ops.py:425-438`). The web Pulse is hard-coded +1 (`web/controller/core.py:281-284`), while the engine reads `autonomous_pulse_by_version` (`phase1_boot.py:177-182`).
4. **Legacy bots plan Phase 3 with pre-income cash**, because `take_phase3_actions` (`phase3_ops.py:178`) runs before income (`:182`). In SIX_PHASE they see post-income cash, which is a spending increase on top of the sequence change.
5. **"commit_shields around base.py:736" is mislocated.** Line 736 is in `choose_colored_dice_to_return`. No bot's `commit_shields` reads money. Generic-shield Red tiering is engine-side (`phase2_threat.py:377-399`).
6. **Green Malware target choice is engine-internal** (`phase2_threat.py:515-549`, duplicated in `web/controller/phase3_actions.py:224-259`), not a bot hook. Only the contractor-sacrifice boolean is a hook (`base.py:397-404`). A new hook is required (§6.3).
7. **Corruption glitches precede income**, so the plan's "re-key corruption glitch choice" premise does not hold (OQ-14).
8. **Aegis Release Bandwidth 3** (`RULES.md:133,378`) contradicts "the starting pool fits exactly" (OQ-6).
9. **A legacy Phase-2 Patient Zero still takes Step 2B damage**: `phase2_threat.py:189-220` iterates every Phase-1 commitment. SIX_PHASE changes this per D3.4.
10. **Legacy Signature Protocols fire on a Phase-1 latch** (`phase3_ops.py:303-308`), even when the Purple die was glitched in Phase 2 (OQ-2).
11. **Bots only ever buy Release Level 1** (`adaptive_balanced.py:518-526`, `secops_turtle.py:380-382`, `accelerationist.py:328-330`). Venture and Reckless never buy it.
12. **The investigation model behind the Rev 2 projections differs from the approved sequence** (`scripts/investigate_income_before_defense.py`):
    - it ran Operations (incl. Release upgrades) **before** the pipeline;
    - it kept Burn Notice and Diagnostics after attacks;
    - it collected income for, and attacked, Phase-2 Patient Zeros (`patched_defense` `:94-100`);
    - it graduated previously-Scanned dice first (`:116-136`);
    - it had none of the §6 bot changes.

    Treat the D5 table as approximate until the Step 7 sweep.
13. **Deprecated or stale terminology in live code:**
    - "Consultancy Archetype" (`web/controller/core.py:263`)
    - "Boot & Configure" (`core.py:65,275`; `web/schemas.py:457`; `phase1_boot.py:1`)
    - "Rogue Agent Compile" (`core.py:328`; `phase1_actions.py:538`)
    - "Corporate Operations" (`phase2_actions.py:352`)
    - "Compiler Drop & Defense" / "Operations & Pipeline Prep" (`header.js:44-45`)
    - "Lead Consultant" comment (`phase3_ops.py:473`)
    - "12 Secrets" (`web/static/index.html:129`)
14. `core.py:234` annotates with `Set` but never imports it; this works only because of `from __future__ import annotations`.
15. Eight historical scripts monkeypatch `sim.engine.phase3_ops.create_colored_die`. After the split, those patches stop affecting purchases (§3.7).

---

## 14. Implementation Order (senior-engineer checklist)
1. [ ] Capture V033 golden parity fixtures at `20e8c80` (S-23) **before** any edit.
2. [ ] `config.py`: `RoundSequence`, `RoundPhase`, `ROUND_PHASE_NAMES`, `__post_init__`, `legacy_v033()`, `is_six_phase`.
3. [ ] `state.py`: `CompileResult`, `IncomeRecord`, `PipelineShiftRecord`, `RoundTelemetry` fields.
4. [ ] Create the six phase modules plus `legacy_v033.py` by **moving** code (§3). Turn the old modules into shims. Run the full existing suite: it must be green with zero test edits apart from §11.2 A.
5. [ ] Implement `_run_round_six_phase` (§4) and the new invariants. Write S-01…S-27.
6. [ ] Bots (§6), gated on SIX_PHASE. S-28, S-29. Re-run S-23 parity.
7. [ ] Web (§8): server enum and endpoints plus API tests before any JS; then JS; then S-30 and the §11.2 B rewrites.
8. [ ] RULES.md / glossary (§10.1) after the OQ-13 answer. PnP (§10.2), then graphic-designer review.
9. [ ] Hand off to product-owner scenarios, then the game-designer Step 7 sweep (`scripts/run_v340_telemetry_sweep.py`).
