# Technical Architecture Specification: Reference Bot (Tier 1 Mixed + Tier 2 Search)
## Mixed Policy Bot, Policy-Portfolio Rollout Search, Fast Engine Clone, Dead-Code Cleanup

**Author:** Principal Engineer / Architect
**Status:** Draft for User review. §14 lists the open questions.
**Target Version:** sim-only tooling; no rules version bump (`RULES.md`, `web/`, `pnp/` unchanged).
**Source of Truth:** [`docs/findings/reference_bot_scoping.md`](../findings/reference_bot_scoping.md) (approved by the User 2026-11-07, two-tier revision).
**Dependencies:** `RULES.md` v0.36.0 §7 glossary, `PLAN.md` §2 (agent roster), [v360 spec](./v360_market_share_red_rework_spec.md), [v370 spec](./v370_market_leader_bonus_spec.md).
**Target Components:**
- New: `sim/bots/mixed_policy.py` (Tier 1), `sim/bots/reference_search.py` (Tier 2), `sim/engine/fast_clone.py` (clone + resumable round tail)
- New: `scripts/run_reference_bot_check.py`, `tests/test_reference_bot.py`
- Cleanup: `sim/bots/base.py` and the 5 archetype files, plus the tests that call removed methods (§11)
- Not touched: every existing `sim/engine/*.py` file, `sim/config.py` (all new constants live in the new modules as `[TUNE-BOT]`)

> Line numbers are from the working tree at HEAD `e1039ae` plus the uncommitted v0.37 diff. Re-check before editing.

---

## 1. Executive Summary

| # | Item | Scoping ref |
|---|---|---|
| D1 | **Tier 1 `MixedPolicyBot`**: each decision type is delegated to one archetype drawn by a pure hash of `(match_seed, bot_id, decision_type[, round])`. Never reads the engine `rng`. | §3 Tier 1 |
| D2 | **Tier 2 `ReferenceSearchBot`**: at Phase 4 Generic shield allocation and the Phase 6 Operations plan, build candidates from a policy portfolio, dedupe, and search only when ≥ 2 distinct candidates remain. Successive halving (4 rollouts each, drop worst half, finish to N = 8) with common random numbers. Everything else delegates to `AdaptiveBalanced`. | §3 Tier 2 |
| D3 | **Phase-start snapshot + replay**: the engine cannot resume mid-phase, so a `ReferenceSearchEngine(GameEngine)` subclass snapshots at the start of Phase 4 and Phase 6. A rollout clones the snapshot, replays the phase prefix with the real RNG state (already-realised past), forces the candidate at the decision, then **reseeds the clone RNG in place** and plays out. | §3 INV-REF-RNG-01 |
| D4 | **`fast_clone`**: hand-written `__dict__` copier. Measured **0.094 ms** vs `copy.deepcopy` **1.92 ms** (3P after 4 rounds), ~20×; 0 mismatches vs deepcopy over 40 seeds × 2/3/4P. | §3 speed levers |
| D5 | Multiprocess runner (8 procs), validation plan, timing gate ≤ ~2 min per 600-game 3P pod. | §4 |
| D6 | Delete 9 dead archetype hooks (none reached by `legacy_v033`). Keep `choose_yahtzee_rerolls` (live), `choose_operator_ability` / `choose_prodigy_ability` (web controller), `take_phase3_actions` (legacy). | §5 |

Unchanged: all game rules, all existing bots' behaviour, `GameEngine` itself. Games with no reference / mixed seat are bit-identical (INV-REF-PARITY-01).

---

## 2. Engine Call Surface (what a wrapper bot must honour)

Inspected call sites. A wrapper (Mixed or Search) must subclass `BaseBot` and implement every hook below, because the engine uses a mix of direct calls, `hasattr`, `getattr`, and MRO lookup.

| Phase | Call | Site | Dispatch style |
|---|---|---|---|
| 1 | `choose_contractor_hires`, `choose_helix_override`, `choose_helix_face_override`, `choose_yahtzee_rerolls` (rng passed), `choose_meridian_override`, `choose_omnidyne_override`, `choose_operator_buy_third_die`, `choose_prodigy_purple_star_override`, `declare_choices`, `commit_shields` | `phase1_roll_deploy.py` 257, 329–360, 422, 433 | direct |
| 2 | `choose_dice_to_glitch`, `choose_colored_dice_to_return` | `phase2_compiler.py` 46, 111 | `hasattr` |
| 3 | `choose_breakthrough`, `choose_scanned_graduates`, `choose_poach_target` | various | `getattr` |
| 4 | `choose_malware_glitch_targets` (122), `choose_aegis_override_market_share` (229), `choose_aegis_override` (243), **`choose_any_shield_allocation` (304)** + attr `any_shield_fill_order` (309), `choose_slush_fund` (411), `choose_malware_sacrifice` (486) | `phase4_attack_resolution.py` | `getattr` / `hasattr` |
| 6 | **`resolve_operations_plan`** (`phase6_operations.py` 26): instance `take_operations_actions` → instance `take_phase3_actions` → MRO; then `apply_research_policy(bot, …, rng)` then `apply_market_share_policy(bot, …)`. Also `choose_phreaker_jumper_diagnostics` (225), `choose_spook_burn_notice`, `choose_purple_reserve_purchase` (called by bots on themselves). | `phase6_operations.py` 404 | MRO + post-processing |

**Attribute reads on the bot** (not methods), which the post-processing uses: `research_focus`, `research_focus_v036`, `research_focus_mode`, `research_aware`, `market_share_policy`, `any_shield_fill_order`, `name`, `bot_id`. `apply_research_policy` *overwrites* `track_upgrades` / `share_regain` from these attributes, and `apply_market_share_policy` may add a Red purchase and sets `use_r2_share`. So the Phase 6 decision is really **(raw plan from `take_operations_actions`) × (attribute profile)**.

### 2.1 Attribute mirroring rule (both tiers)

Before returning from any delegated call, the wrapper copies the delegate's attribute profile (`research_focus`, `research_focus_v036`, `research_aware`, `market_share_policy`, `any_shield_fill_order`) onto itself. The engine then post-processes with the delegate's profile, so the wrapper's result equals the delegate's own `resolve_operations_plan` result. For Phase 6 the wrapper returns the delegate's **raw** plan (from `phase6_operations._resolve_raw_operations_plan`), never the post-processed one, so post-processing runs exactly once. Verified idempotency argument: `apply_research_policy` recomputes from state only; the Red nudge is a no-op when Red is already in the list; `use_r2_share` is recomputed from the same spend. RB-04 tests equality.

`research_focus_mode` on the wrapper and on every delegate instance is forced to `"fixed"` (see H1).

---

## 3. Side-Effect Hazards in Decision Methods

Audit of `sim/bots/*.py` for writes to `self`, `player_state`, `game_state`, dice, or the passed `rng`:

| # | Hazard | Where | Mitigation |
|---|---|---|---|
| H1 | **`policy_for_bot` with `research_focus_mode="random"` shuffles the passed `rng` (the live engine RNG) once and caches `bot._research_focus_random`.** Candidate generation through this path would consume the real RNG and change every seat's future. | `research_policy.py` 145–153 | Delegate / portfolio instances are private and forced to `"fixed"`. Candidate generation always passes a throwaway `random.Random(cand_seed)`, never `engine.rng`. A guard asserts `engine.rng.getstate()` is unchanged across candidate generation (RB-05). |
| H2 | **Phase 6 post-processing reads bot attributes**, so a wrapper that returns a delegate's plan gets the wrapper's own focus / Market Share policy applied on top. | `phase6_operations.py` 30–38 | §2.1 mirroring + raw plan. |
| H3 | `phase1` passes `engine.rng` into `choose_helix_override` / `choose_yahtzee_rerolls`; base `choose_helix_override` forwards it. No archetype calls a method on it today (grep `rng\.` in `sim/bots` = none outside H1). | `phase1_roll_deploy.py` 339; `base.py` 348 | Not searched. INV-REF-DET-01 test catches a future bot that starts drawing from it. |
| H4 | `BaseBot.__init__` sets `use_omnidyne_override` / `prometheus_*` on `self` (68–74). Init-time only. | `base.py` | None needed. |
| H5 | All other `append` / `pop` in bots act on locals (`rerolls`, `upgrades`, `discounted_colors`, `sim_unpatched`). No bot writes `player_state.*`, `game_state.*` or die fields. | grep audit | Bots are effectively stateless: clones may share opponent bot objects. |
| H6 | `GameEngine.rng` and `GameState.rng` are **the same object** (`core.py` 85, 226). Replacing one breaks aliasing. | `core.py` | Reseed **in place** with `rng.seed(s)` (one call fixes both). |
| H7 | String `hash()` is salted per process (`PYTHONHASHSEED`). Any seed derived with `hash()` differs across the 8 workers. | design | All seeds derived with `zlib.crc32` / integer mixing (§4.1). |

No meaningful hidden information exists (scoping §3): stuck Internal Baffle cubes can be deduced, so the clone may carry them.

---

## 4. Tier 1: `sim/bots/mixed_policy.py`

```python
class MixedPolicyBot(BaseBot):
    def __init__(self, bot_id, match_seed, pool=DEFAULT_POOL, granularity="game", name="MixedPolicyBot"): ...
```

- `DEFAULT_POOL` `[TUNE-BOT]` = (`AccelerationistBot`, `AdaptiveBalancedBot`, `RecklessSaboteurBot`, `SecOpsTurtleBot`, `VentureGreedBot`), one private instance each with the same `bot_id`, `research_focus_mode="fixed"`.
- **Decision types** (draw keys): `phase1_roll` (rerolls, Helix, Meridian, Omnidyne, Prodigy), `phase1_deploy` (`declare_choices`, `commit_shields`, contractor hires, Operator third die), `phase2` (glitch / return), `phase4` (Aegis, Generic shields, Slush Fund, malware), `phase6` (Operations plan + Phreaker / Spook Burn Notice / Purple reserve), `misc` (Breakthrough, graduates, Customer Poaching target).
- **Granularity** `[TUNE-BOT]`: `"game"` (default; one draw per decision type per game, as in the scoping doc) or `"round"` (redraw each round, key includes `game_state.current_round`).

### 4.1 Seeding (INV-REF-RNG-02)

```python
def _draw(self, dtype, round_no):
    key = f"{self.match_seed}|{self.bot_id}|{dtype}|{round_no if self.granularity == 'round' else 0}"
    return self.pool[zlib.crc32(key.encode()) % len(self.pool)]
```

Pure function, no RNG stream, no state. Consequences: the Mixed bot never touches `engine.rng`, so other seats are affected only through its choices; a clone may share the same Mixed instance; results are identical across processes. `match_seed` is the seed passed to `GameEngine(seed=…)`; the runner passes it to the bot factory.

### 4.2 Delegation

Each hook calls `self._draw(dtype, round).method(...)` with the original arguments, mirrors attributes (§2.1), and returns the result. `take_operations_actions` returns the delegate's raw plan. Record `self.draw_log[(dtype, round)] = delegate.name` for telemetry (read-only, does not influence play).

---

## 5. Tier 2: `sim/bots/reference_search.py`

### 5.1 Classes

| Class | Role |
|---|---|
| `ReferenceSearchEngine(GameEngine)` | Overrides `_run_phase_4_attack_resolution(commitments, cr)` and `_run_phase_6_operations()` only: before calling `super()`, store `self._snap = fast_clone.snapshot(self, phase, commitments, cr)` (keeps real RNG state). Used only when a reference seat is present. Everything else inherits. |
| `ReferenceSearchBot(BaseBot)` | The seat. Holds `fallback = AdaptiveBalancedBot(bot_id)`, the portfolio, and a back-reference `engine` set by `ReferenceSearchEngine.__init__` (it calls `bot.bind(self)` for each bot that defines `bind`). All non-searched hooks delegate to `fallback` with mirroring. |
| `ForcedChoiceBot(BaseBot)` | Used **inside clones** at the reference seat: replays the decision log for prior searched calls this phase, returns the forced candidate at the target call, then calls `engine.rng.seed(rollout_seed)` and behaves as `fallback` for the rest of the game (INV-REF-NEST-01). |

### 5.2 Searched decisions

| Decision | Hook | Candidate output | Dedup key |
|---|---|---|---|
| Phase 4 Generic shield split | `choose_any_shield_allocation(player_state, remaining, available_any, game_state, attack)` | each portfolio member's hook result, legalised with `validate_any_shield_allocation(raw, remaining, available_any, member.any_shield_fill_order)` | the legal `{RED, BLUE, GREEN}` tuple. The bot returns the legal split, so fill order no longer matters. |
| Phase 6 Operations plan | `take_operations_actions(player_state, state, rng)` | `(raw_plan, profile)` per member; final plan = `resolve_operations_plan(member, …, throwaway_rng)`, run on the live objects (hooks are read-only, H5) with a throwaway rng | `dataclasses.astuple(final_plan)` (Face objects are frozen and hashable) |

Only called under `any_shield_policy == FREE_CHOICE` with shields and cubes left (engine guard, `phase4` 300–303). If only one distinct candidate remains → return it, no rollouts.

### 5.3 Portfolio `[TUNE-BOT]`

`PORTFOLIO` = 5 archetypes (class defaults) + `AdaptiveBalanced` with `research_focus_v036` set to each of the 4 rotations that put a different track first (DEFENSE / TRIAGE / RELEASE / PATENT = Public Relations Track) + `AdaptiveBalanced` with `MarketSharePolicy(red_danger_value=3.0, danger_margin=3)` and with `MarketSharePolicy(leader_bonus_aware=False)`. 11 members, typically 3–6 distinct after dedup. Internal track keys stay as in code (`"PATENT"`).

### 5.4 Rollout loop

```
seeds = [mix(match_seed, bot_id, round, phase, k) for k in range(N)]   # N = 8, shared by all candidates (CRN)
alive = candidates
for stage_rollouts in (4, N - 4):                                       # successive halving
    for c in alive: run seeds[used:used+stage_rollouts] for c
    if stage 1 and len(alive) > 2: keep best ceil(len/2) by mean value
pick argmax mean over all N seeds (ties: portfolio order, fallback first)
```

One rollout: `clone = fast_clone.from_snapshot(engine._snap)`; seat bot → `ForcedChoiceBot(decision_log, target_call_index, candidate, seed)`; other seats keep their live bot objects (stateless, H5; Mixed is pure, §4.1); `clone.resume_round(phase)`; then `clone.run_game()`; score.

### 5.5 Value `[TUNE-BOT]`

```
v = secrets_self - max(secrets_rival over surviving rivals, or 0 if none)
if self is Patient Zero: v = PZ_PENALTY            # -50
if self in winner_ids:  v += WIN_BONUS / len(winner_ids)   # +3
```

Read from `EndGameResult.rankings` and the clone's `PlayerState.is_patient_zero`. Constants: `N_ROLLOUTS=8`, `HALVING_FIRST=4`, `PZ_PENALTY=-50`, `WIN_BONUS=3`.

### 5.6 Resuming a round (`sim/engine/fast_clone.py`)

`resume_round(engine, phase)` re-implements the tail of `GameEngine._run_round_six_phase` (`core.py` 415–467) from Phase 4 or Phase 6, without telemetry snapshots: run the phase (prefix replays exactly), then for Phase 4 the `game_over` check, Phase 5, Phase 6; then the Final Round / `current_round` / `ROUND_LIMIT` logic. It must not import private helpers beyond `_run_phase_*`. Telemetry is not needed for scoring; append a minimal `RoundTelemetry` only if `evaluate_end_game` requires it (it reads `engine.telemetry_history`, `end_game.py` 311; a list copy is enough). Drift guard: RB-07.

---

## 6. Fast Clone (`sim/engine/fast_clone.py`)

Probe: `/tmp/claude-1000/rbprobe/c.py` (scratch, not committed). Results: 0.094 ms per clone, 3.8 ms per clone + full rollout from round 4 (3P), 0 result mismatches vs deepcopy (40 seeds × 2/3/4P, same reseed).

### 6.1 What is copied

| Object | Treatment |
|---|---|
| `GameEngine` | `object.__new__` + `__dict__.copy()`. Share `config`, `variant_cards`, `version_deck`, `archetypes`, `companies`, `white_hats` (frozen dataclasses / never mutated in play). New `state`, `rng` (see below), `telemetry_history` = list copy, `_ms_round_start` / `_research_round_start` = 1-level dict copy. |
| `GameState` | `__dict__` 1-level copy, then: every `dict` / `list` / `set` value copied (`market`, `staging_cup`, `priming_*`, `last_exited_cubes`, `phase4_market_share_start`, `pending_next_phase_locks`, `active_phase1_locks`, `version_comparisons_done`, `market_collapse_pids`, `market_collapse_secret_leaders`, `end_triggers`, `_pending_poaches`); `r3_events` = list of dict copies; `market_collapse_context` = deepcopy (small); `version_comparisons` = list copy (records are append-only). `players` rebuilt. `tower` cloned. `config` shared. |
| `CubeTower` | `__dict__` copy with `stuck_cubes` / `last_exited_cubes` dict copies; `config` shared. |
| `PlayerState` | `__dict__` 1-level copy (it carries ~90 dynamic attributes, so copy generically, never by field list); every `dict` / `list` / `set` value copied; `breakthroughs` = list of dict copies; `last_defense_breakdown` deepcopy; the 5 dice lists rebuilt preserving the list type (`_UnderDevelopmentProxy` if present). `bot`, `company`, `white_hat`, `config` shared. |
| `Die` | `__dict__` copy; `faces` list shared (never mutated; `Face` frozen); `current_face` shared. Memoised by `id()` so a die referenced from two places maps to one clone (none observed: 0 duplicates). |
| Snapshot extras | Phase 4: `commitments` = `[(memo[player], [memo[d] for d in dice], dict(shields))]`; `CompileResult` with dict copies, `breached_pids` set copy. |
| RNG | Snapshot: `random.Random()` with `setstate(engine.rng.getstate())`, assigned to **both** `engine.rng` and `state.rng`. Rollout: same object, `seed(rollout_seed)` in place at the decision point. |

Rule: any **new** mutable attribute added to these classes later is caught by the generic dict/list/set pass. Any new mutable custom object type fails RB-02 (parity vs deepcopy), which is the guard.

### 6.2 Parity test (INV-REF-CLONE-01)

For seeds 0–99 × 2/3/4P × {mixed, setup} (`tests/fixtures/v035_parity/capture.build_engine`), at rounds 1, 3, 5 (if not over): `a = deepcopy(e)`, `b = fast_clone(e)`, reseed both to the same value, run both to completion, assert identical `end_reason`, `total_rounds`, `winner_ids`, full `rankings`, and per-round Phase 4 `[money, secrets, market_share]`. Also assert the original `e` is unchanged (compare a deepcopy taken before cloning, then let `e` finish and match a control run).

---

## 7. Invariants

| ID | Statement | Test |
|---|---|---|
| **INV-REF-RNG-01** (critical) | No rollout ever draws from the real future. Each rollout clone's RNG is reseeded from a rollout seed at the decision point; the phase-prefix replay uses only the snapshot's RNG state (realised past). The real `engine.rng` state is unchanged by any search or candidate generation. | RB-05, RB-06 |
| INV-REF-RNG-02 | The Mixed bot derives all draws from `crc32(match_seed, bot_id, type, round)`; it never reads any RNG. | RB-03 |
| **INV-REF-CRN-01** | All candidates at one decision use the same seed list; candidate `c` rollout `k` uses `seeds[k]`. | RB-08 |
| **INV-REF-NEST-01** | Inside a clone, the reference seat is a `ForcedChoiceBot` → fallback; no `ReferenceSearchBot` exists in any clone; recursion depth is 0. | RB-09 |
| **INV-REF-DET-01** | Same match seed → identical game, in-process and across processes (different `PYTHONHASHSEED`). Audit result below. | RB-10 |
| **INV-REF-PARITY-01** | Games without a Mixed / reference seat are bit-identical to `tests/fixtures/v036_parity/` (run via `GameConfig.v036`, as `tests/test_v370_market_leader_bonus.py` does). `GameEngine` is not edited. | RB-11 |
| INV-REF-REPLAY-01 | `fast_clone.from_snapshot` + `resume_round` with the **un-reseeded** snapshot RNG and the real decision reproduces the real game bit-for-bit. | RB-07 |
| INV-REF-CLONE-01 | §6.2. | RB-02 |

### 7.1 Global `random` audit (INV-REF-DET-01)

`grep` of `sim/`: every `import random` is used only for `random.Random(...)` instances or type hints. No module-level `random.random/randint/choice/shuffle/sample/seed` calls. Seeded instances: `core.py` 85 (`Random(seed)`), `experiments.py` 88 / 545 (`Random(seed * 17)` setup), `research_policy.py` 149 (`Random(bot_id)` fallback, only when `rng is None`). `GameState.rng` default factory is an unseeded `Random()`, always overwritten by the engine (`core.py` 226); the clone must never rely on that default. Iteration over `set[str]` (`pending_next_phase_locks`, `active_phase1_locks`, `version_comparisons_done`) is hash-order dependent across processes: the implementer must confirm these are only used for membership tests (RB-10 runs two subprocesses with different `PYTHONHASHSEED` and compares).

---

## 8. Runner: `scripts/run_reference_bot_check.py`

- `multiprocessing.Pool(8)`; one task = one game `(cell, players, seed)`; workers return a compact summary dict (no telemetry objects).
- Cells: `baseline` (archetype rotation as in v036 fixtures), `mixed1` (1 Mixed seat, rotated across seats), `ref1` (1 reference seat), `ref_all` (all seats reference), plus targeted cells in §9 step 2.
- Seat rotation: the special seat cycles through seat indexes by `seed % P` to cancel first-player effects.
- Output: `sim_results/reference_bot_<cell>.json` + `.txt`, with ms/game, searched decisions/game, distinct-candidate histogram, rollouts/game, win rate by seat type, Patient Zero rate, end-reason split.
- CLI: `--cells`, `--players 2,3,4`, `--games 600`, `--procs 8`, `--smoke` (20 games).

### 8.1 Timing estimate (to confirm in step 0)

~10 searched decisions × ~4 candidates × ~6 effective rollouts × ~2.5–3.8 ms (remaining-game rollout + 0.1 ms clone) ≈ **0.6–0.9 s/game** → 600 games / 8 procs ≈ **45–70 s per 3P pod**, under the ≤ ~2 min target. Tier 1 adds a crc32 per decision type per game: target ≤ 5% over 4.7 ms.

---

## 9. Validation Plan (scoping §4)

| Step | Owner | Pass condition |
|---|---|---|
| 0 Timing | product-owner | Tier 2 `ref1` 3P 600 games ≤ ~2 min on 8 procs; Tier 1 ≤ 5% slower than baseline. Re-run v0.36 baseline with one Mixed seat; record shifts. |
| 1 Strength gate | product-owner → game-designer | `ref1` 3P, 1,200 games: reference win rate ≥ fair share + 10 points (≥ 43.3%). If not, raise N / portfolio before any conclusion. |
| 2 Re-test | game-designer | Blue-first (§36), Market Share relative lock (§37), placement bonus + Public Relations-first (§38) under `ref1` and `ref_all`. |
| 3 Artifact check | game-designer | Release / Public Relations Track concentration: reference vs archetype focus orders, and Mixed vs baseline. |
| 4 Report | game-designer | New `FINDINGS.md` section; `PLAN.md` phase entry updated. |

---

## 10. Implementation Order

1. `fast_clone.py` (clone, snapshot, `resume_round`) + RB-01/02/07.
2. `mixed_policy.py` + RB-03/04/11.
3. `reference_search.py` + RB-05/06/08/09/10/12–14.
4. Runner + `--smoke`.
5. Cleanup §11 (separate commit, after parity green).

---

## 11. Dead-Code Cleanup

`legacy_v033.py` calls only `take_phase3_actions` (316). None of the methods below is reached by any `sim/engine` path, `legacy_v033`, `web/`, or `sim/experiments.py`.

| Method | Defined in | Callers | Action |
|---|---|---|---|
| `choose_debug_unlocks` | `base.py` 193; accelerationist 107, adaptive_balanced 137, reckless_saboteur 113, secops_turtle 117, venture_greed 121 | tests only: `test_v230_rules.py` 79, 428–451; `test_v120_rules.py` 214–229, 452–460; `test_v220_rules.py` 179; `test_engine_phases.py` 22; scripts `analyze_glitches_across_versions.py` 35, `test_fast_patch_only.py` 33 | Delete; delete the direct-call tests; overrides in test stubs become harmless and can be removed |
| `choose_hotfix_rerolls` | `base.py` 158; adaptive_balanced 220, secops_turtle 152, venture_greed 160 | `test_engine_phases.py` 37 (stub) | Delete |
| `choose_fast_patches` | `base.py` 807; adaptive_balanced, secops_turtle | `test_v230_rules.py` 297–471 (stubs + 462/471 direct calls); `test_v220_rules.py` 453; scripts `test_no_fast_patch.py`, `test_fast_patch_only.py`, `analyze_glitches_across_versions.py` | Delete; drop direct-call tests (462–471) |
| `choose_glitch_demotion` | `base.py` 209 | none | Delete |
| `choose_shield_wear_order` | `base.py` 511 | none | Delete |
| `choose_b3_sacrificial_die` | `base.py` 535 | none | Delete |
| `choose_prometheus_override` | `base.py` 400 | none | Delete |
| `choose_acoustic_ability` | base + all 5 archetypes | none | Delete |
| `choose_spook_ability` | base + all 5 archetypes | none | Delete |
| **Keep** `choose_yahtzee_rerolls` | base 180 + 5 archetypes | **live**: `phase1_roll_deploy.py` 350 (free rerolls) | Keep (scoping listed it as dead; it is not) |
| **Keep** `choose_operator_ability`, `choose_prodigy_ability` | base + archetypes | `web/controller/phase1_actions.py` 552, 637 | Keep |
| **Keep** `take_phase3_actions` | `base.py` 827 | `legacy_v033.py` 316, `phase6_operations.py` 46–52, many tests | Keep (legacy parity) |

Old one-off scripts under `scripts/` that subclass bots with these names keep working (extra methods on a subclass are inert). Gate: full `pytest` + v033/v035/v036 parity fixtures green before and after.

---

## 12. Test Matrix (`tests/test_reference_bot.py`)

| ID | Test |
|---|---|
| RB-01 | `fast_clone` independence: mutate every container in the clone; original unchanged (players, dice lists, die fields, tower, staging cup, market, sets). |
| RB-02 | INV-REF-CLONE-01 parity vs deepcopy (§6.2). |
| RB-03 | Mixed draws: same `(match_seed, bot_id)` → same delegates; different seeds cover all 5 pool members over 200 seeds; `engine.rng.getstate()` trajectory identical to a game where that seat is replaced by a bot that replays the Mixed bot's choices. |
| RB-04 | Mirroring: for 200 Phase 6 states, `resolve_operations_plan(mixed)` == `resolve_operations_plan(delegate)`; same for `ReferenceSearchBot` returning a chosen candidate. |
| RB-05 | H1 guard: candidate generation leaves `engine.rng.getstate()` unchanged, including a portfolio member with `research_focus_mode="random"` (forced to fixed). |
| RB-06 | Anti-clairvoyance: a rollout's dice / tower draws after the decision differ from the real game's for the same position (compare first Phase 1 faces next round), and equal those of a fresh `Random(rollout_seed)`. |
| RB-07 | INV-REF-REPLAY-01 at Phase 4 and Phase 6 snapshots, 100 seeds × 2/3/4P. |
| RB-08 | CRN: instrumented rollouts record `(candidate, k, seed)`; seed set per decision identical across candidates. |
| RB-09 | NEST: inside a clone, `isinstance(seat.bot, ReferenceSearchBot)` is false; a counter of search entries stays 1 per real decision. |
| RB-10 | DET: same seed twice in-process → identical results; two subprocesses with `PYTHONHASHSEED=1` / `=2` → identical JSON summary (ref1 + mixed1, 20 games). |
| RB-11 | PARITY: v036 fixtures unchanged with this branch (reuse the v370 parity replay). |
| RB-12 | Single-candidate shortcut: when all candidates dedupe to one, zero rollouts run. |
| RB-13 | Successive halving: 6 candidates → 4 rollouts each, 3 survive, each finishes to 8; total = 6×4 + 3×4 = 36. |
| RB-14 | Value: Patient Zero → `PZ_PENALTY`; shared win splits `WIN_BONUS`; Total Wipeout handled (all Patient Zero → every candidate `PZ_PENALTY`, tie → portfolio order). |
| RB-15 | Legal output: Phase 4 split sums to `min(available_any, sum(remaining))` and never exceeds `remaining` per color. |
| RB-16 | Smoke: runner `--smoke` at 2/3/4P completes, writes JSON, no exceptions. |
| RB-17 | Cleanup: removed methods absent from `BaseBot` and archetypes; kept ones present; parity fixtures v033/v035/v036 green. |

---

## 13. Risks

- **Prefix replay drift**: if a future engine change consumes RNG between the snapshot and the decision in a way that depends on bot state, RB-07 fails loudly. Acceptable.
- **`resume_round` duplicates the round tail** of `core.py`. RB-07 guards it; any edit to `_run_round_six_phase` must be mirrored (note added in a code comment there is *not* in scope, since engine files stay untouched; record it in `PLAN.md`).
- **Rollout policy bias**: rollouts play every seat with its default policy, so the search values options against archetype play. That is the intended "competent player" check, not an equilibrium.

---

## 14. Open Questions for the User

1. **Phase 1 `commit_shields` is not searched.** Shield placement on die faces happens in Phase 1; Phase 4 only splits Generic (`Any`) shields. The scoping doc's "Phase 4 shield allocation (which cubes to block)" maps to the Generic split. Add Phase 1 `commit_shields` as a third searched decision (≈ +40% cost, still inside 2 min by §8.1)?
2. **Mixed granularity default**: per decision type per game (scoping wording) or per round? Spec defaults to per game, with `"round"` as a lever.
3. **Mixed pool**: archetypes only, or also the portfolio variants of §5.3 (focus rotations, Market Share policies)?
4. **Value constants**: `PZ_PENALTY = -50`, `WIN_BONUS = +3` (shared win split). Acceptable as starting `[TUNE-BOT]`?
5. **Strength gate at 2P / 4P**: scoping sets +10 points at 3P only. Same margin at 2P and 4P, or 3P only?
6. **Cleanup scope**: the scoping doc named `choose_yahtzee_rerolls` as dead; it is live (Phase 1 free rerolls) and is kept. Also delete the 6 extra dead hooks found (`choose_glitch_demotion`, `choose_shield_wear_order`, `choose_b3_sacrificial_die`, `choose_prometheus_override`, `choose_acoustic_ability`, `choose_spook_ability`) and the tests that call them directly?

### Open Question Resolutions (User, 2026-11-07)

1. Phase 1 `commit_shields` **is searched** (in addition to Phase 4 Generic split and Phase 6 operations). Snapshot/replay also at the start of Phase 1.
2. Mixed draw is **per game** by default; per round stays a `[TUNE-BOT]` setting.
3. Mixed pool is **archetypes only**; portfolio variants are search-only.
4. `PZ_PENALTY = -50`, `WIN_BONUS = +3` accepted as starting `[TUNE-BOT]` values.
5. Strength gate (+10 points over fair share) applies at **3P**; 2P and 4P are reported, not gated.
6. Delete the 9 dead hooks and the tests that call them; keep `choose_yahtzee_rerolls`, `choose_operator_ability`, `choose_prodigy_ability`, `take_phase3_actions`.
