# Technical Architecture Specification: Locked ⚠ Faces on Colored Dice (`v0.47.0`)

**Author:** Principal Engineer
**Date:** 2026-11-19
**Status:** Ready for senior-engineer implementation. The User signed off on the package on 2026-11-19 (`docs/plans/locked_vuln_faces_gd_plan.md` §8, User decisions block).
**Source:** `docs/plans/locked_vuln_faces_gd_plan.md` §1, §4, §8, §9, §10. The probe scripts `scripts/probe_locked_vuln.py` and `scripts/probe_locked_vuln_math.py` are reference only. Nothing in this spec imports them.
**Out of scope:** `RULES.md`, `RULES_QUICKREF.md`, `GLOSSARY.md`, `RULES_APPENDIX.md`, `pnp/`, `tts/`, `web/` and version strings. Those are a later doc-sync step (GD plan §10). The web default rules version does not change.

---

## 0. Terminology guardrails

- Player-facing terms: **locked die** (D4), **Deploy** (Phase 1 Step 4, renamed from "Lock-in & Assign Dice"), ⚠, **Vulnerability**, **Secret face**, **Gray Legacy die**, Helix *Brute-Force Bypass*, Prodigy *Arbitrary Code Execution* (ACE), **Release Track** Level 4, **Pen Test Track**, **Target Lock** / **Target-Locked player** (D4), **Institutional Override**.
- Sim identifiers that say "lock-in" (`vulnerability.lock_in`, the `"lockin"` ledger key, `vuln_by_round[...]["lockin"]`) **keep their names**. Renaming them is optional and must not change any telemetry key that a v0.46 golden digest reads (§12, INV-LOCK-07).
- `Die.is_locked` is the existing engine flag. It is shared by the legacy glitch lock and the new ⚠ lock, and both are written through the one `_evaluate_locks` pass (§4.2).
- No new player-facing strings ship in this step. Bot stance labels (`NO_COLOR_REROLL`, `STAR_CHASE`) are sim-only, like `KEEP_ALL`.

---

## 1. Scope summary (signed-off package)

| # | Change | Where |
|:---|:---|:---|
| 1 | **Locked dice.** In Phase 1 Step 3, a colored die (Red, Blue, Green, Yellow or Purple) showing any ⚠ face is locked and can't be rerolled for the rest of the phase. That covers the core ⚠ face and Secret face F5, which carries ⚠. The check runs after the initial roll and after every reroll. Gray Legacy dice and White Contractor dice never get the ⚠ lock. ACE and any other face-setting override may change a locked die's face. ⚠ counts on the final face. | `phase1_roll_deploy.py`, `vulnerability.py` |
| 2 | **Premium faces.** `die_face_profile = "V046_VULN"` (the existing table; no face edits). | preset |
| 3 | **Safe zone 0–4.** `vuln_band_thresholds = (5, 8, 11)`, `vuln_min_target_by_version = (5, 5, 5)`. | preset |
| 4 | **Helix *Brute-Force Bypass* is replaced** by "You may reroll locked dice this phase". It is **once per game**, with no +1 reroll and no face-set. | `phase1_roll_deploy.py`, `state.py`, `phase4_attack_resolution.py` |
| 5 | **Lock-aware bots.** They price the 1/3 lock risk of each clean colored reroll near band thresholds. The GD probe's "aware" rule is the minimum bar. Helix and ACE choices become lock-aware too. | `vulnerability_policy.py`, `base.py`, `reference_search.py` |
| 6 | **Telemetry.** Locks per player-round, locked ⚠ by face, Helix uses, Helix win rate and per-colour win rates. | `state.py`, `end_game.py`, sweep script |
| 7 | **Preset.** `GameConfig.v046_locked()` / `v047_roster()` inherit `v046()`. Every new flag is off by default, so `v046()` replays byte-identically. | `config.py` |

---

## 2. Engine map (current touch points)

| File | Lines (approx.) | Today | v0.47 change |
|:---|:---|:---|:---|
| `sim/config.py` | `238-254` `VulnPolicyParams` | bot λ params | + lock params (§3.2) |
| `sim/config.py` | `533-562` v0.46 block | Vulnerability fields | + lock / Helix fields (§3.1) |
| `sim/config.py` | `1125-1151` | `v046()`, `v046_roster()` | + `v047()`, `v047_roster()` after them (§3.3) |
| `sim/config.py` | `1257-1319` `_validate_v046` | V046 validation | + `_validate_v047` (§3.4) |
| `sim/engine/phase1_roll_deploy.py` | `413-419` | initial roll, `is_locked = False` | + reset of per-phase lock state |
| | `429-432` | pre-v0.43 ACE on the initial roll | unchanged (not on the v0.46 lineage; `white_hat_6f_rebalance=True` since `v043`) |
| | `440-448` | `_evaluate_locks`: glitch-only | + ⚠ lock rule + telemetry (§4.2) |
| | `450-468` | Helix decision once before the loop; V038 +1 reroll | `LEGACY` mode only (§5) |
| | `471-548` | reroll loop; `helix_active` filter ignores locks | + Helix offer per step; same filter (§4.3, §5) |
| | `550-572` | ACE after rerolls (v0.43+) | + lock-break telemetry |
| | `574-597` | Helix face override | `LEGACY` mode only |
| | `599-607` | Release L4 Gray face set; final `_evaluate_locks`; `vulnerability.lock_in` | + final-face telemetry; + clear locks after `lock_in` |
| `sim/engine/vulnerability.py` | `18-77` | helpers, `lock_in` | + `LOCKABLE_COLORS`, `lock_applies`, `reroll_allowed`, `crossings` (§4.1) |
| `sim/engine/state.py` | `259`, `533-538`, `845-850` | DTO once-per-game flag and accessor | + Helix mirror (§5.1) and lock telemetry fields (§8.1) |
| `sim/engine/phase4_attack_resolution.py` | `845-871` `_resolve_signature_black` | Black burns the Override; DTO game flag | + Helix once-per-game mirror (§5.3) |
| `sim/engine/end_game.py` | `151-185`, `335` | `_v046_row` | + `_v047_row`, emitted only under the lock flag (§8.2) |
| `sim/bots/vulnerability_policy.py` | `108-148`, `169-184`, `192-244` | reroll post-process, Helix face, Pen Test | lock-aware filter, Helix bypass decision, ACE target, floor-relative Pen Test (§6) |
| `sim/bots/base.py` | `282-317`, `1194+` | `choose_helix_override`, ACE target | + `choose_helix_bypass`; ACE routes to the λ policy under lock (§6.4, §6.5) |
| `sim/bots/reference_search.py` | `127-156`, `319-328` | V046 portfolio members | + v0.47-only members (§6.7) |
| `sim/bots/mixed_policy.py` | `42-45` | `HOOK_DTYPES` | + `choose_helix_bypass` → `"phase1_roll"` |

---

## 3. Configuration and presets

### 3.1 New `GameConfig` fields (put them after the v0.46 block; defaults reproduce v0.46)

| Field | Type / default | Meaning |
|:---|:---|:---|
| `colored_vuln_lock` | `bool = False` | `[RULE]` Locks a colored die that shows a ⚠ face during Phase 1 rerolls. |
| `colored_vuln_lock_secret` | `bool = True` | `[RULE]` Lets the Secret face F5 (⚠) lock. Read only while `colored_vuln_lock` is on. `False` is the D5 control arm. |
| `helix_bypass_mode` | `str = "LEGACY"` | `"LEGACY"` keeps today's behaviour: the decision comes once before the loop, it ignores locks, it gives the V038 +1 reroll, and a face-set follows. `"REROLL_LOCKED"` is v0.47: "You may reroll locked dice this phase", with no +1 reroll and no face-set. |
| `helix_bypass_once_per_game` | `bool = False` | `[RULE]` Brute-Force Bypass may be used once per game (the DTO *Slush Fund* model). |

The new rule fields are `[RULE]`, not `[TUNE]`. The only `[TUNE]` values that change are the existing `vuln_band_thresholds` and `vuln_min_target_by_version`, and only inside the v0.47 preset.

### 3.2 New `VulnPolicyParams` fields (sim-only `[TUNE-BOT]`; frozen dataclass; defaults are safe because every bot path checks `cfg.colored_vuln_lock`)

| Field | Default | Meaning |
|:---|:---|:---|
| `lock_policy` | `"LAMBDA_AWARE"` | `"NONE"` (naive: lock-blind, matches probe arms "naive") / `"AWARE"` (the probe heuristic, §6.1) / `"LAMBDA"` (the λ rule, §6.2) / `"LAMBDA_AWARE"` (drop if either rule drops). Read only under `colored_vuln_lock`. |
| `lock_reroll_margin` | `0.0` | Extra money-equivalent a clean colored reroll must clear under the λ rule. |
| `helix_min_gain` | `1.0` | Minimum λ-priced gain (money-equivalent) before the bot spends Brute-Force Bypass (§6.4). |
| `pen_relative_to_floor` | `Optional[bool] = None` | `None` means "follow `cfg.colored_vuln_lock`". When on, the hard-coded Pen Test thresholds move with the safe zone (§6.6). |

Because the defaults are only read under the lock flag, `v047()` does **not** need to override `vuln_bot_params`. That avoids a sweep pitfall: `run_v046_sweep.parse_overrides` builds `VulnPolicyParams(**json)` from scratch (`:315`). The v0.47 script must layer `--vuln-params` with `dataclasses.replace(cfg.vuln_bot_params, **json)` (§11.1).

### 3.3 Presets (after `v046_roster`, `config.py:~1152`)

```python
@classmethod
def v047(cls, **overrides) -> "GameConfig":
    """v0.47.0 Locked ⚠ Faces (docs/specs/locked_vuln_faces_spec.md). Inherits v046()."""
    for k, v in (
        ("colored_vuln_lock", True), ("colored_vuln_lock_secret", True),           # D5
        ("die_face_profile", "V046_VULN"),                                          # D2 premium faces
        ("vuln_band_thresholds", (5, 8, 11)), ("vuln_min_target_by_version", (5, 5, 5)),  # D1 safe zone 0-4
        ("helix_bypass_mode", "REROLL_LOCKED"), ("helix_bypass_once_per_game", True),     # D3 User rule
    ):
        overrides.setdefault(k, v)
    return cls.v046(**overrides)

@classmethod
def v047_roster(cls, **overrides) -> "GameConfig":
    """v0.47.0 + bot autonomous PR push and cash allocation policies enabled."""
    overrides.setdefault("bot_pr_push", True)
    overrides.setdefault("bot_pr_push_params", PrPushParams())
    return cls.v047(**overrides)
```

Inherited values and why they stay valid: `vuln_track_max = 15 ≥ 11`, `vuln_hit_reset = 0 < 5`, `vuln_band_damage = (1, 2, 3)`, `pen_test_cost = 2`, `power_profile = "V038_DRAFT"`, `white_hat_6f_rebalance = True` (ACE resolves after rerolls) and `signature_attack_mode = "dominant_color_effects"` (Black Signature active).

Register `v047` and `v046_locked_roster` anywhere the preset names are listed (the sweep `build_engine` resolves them by `getattr(GameConfig, name)`). Leave the web preset list alone.

### 3.4 Validation (`_validate_v047`, called from `__post_init__` right after `_validate_v046`)

| Condition | Error |
|:---|:---|
| `colored_vuln_lock` and not `is_vulnerability` | `"colored_vuln_lock requires defense_mode='VULNERABILITY'"` |
| `helix_bypass_mode not in ("LEGACY", "REROLL_LOCKED")` | unknown mode |
| `helix_bypass_mode == "REROLL_LOCKED"` and not `colored_vuln_lock` | `"helix_bypass_mode='REROLL_LOCKED' requires colored_vuln_lock"` |
| `helix_bypass_once_per_game` and `helix_bypass_mode != "REROLL_LOCKED"` | `"helix_bypass_once_per_game requires helix_bypass_mode='REROLL_LOCKED'"` |
| `vuln_bot_params.lock_policy not in ("NONE", "AWARE", "LAMBDA", "LAMBDA_AWARE")` | unknown policy |

`colored_vuln_lock_secret=False` with the lock off is allowed, since it is a no-op. The face profile is not tied to the lock, because arm A (NOPREMIUM + lock) must remain constructible.

---

## 4. Lock rule (engine)

### 4.1 Helpers in `sim/engine/vulnerability.py` (pure; no RNG)

```python
LOCKABLE_COLORS = frozenset({DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW, DieColor.PURPLE})

def lock_applies(cfg, die) -> bool:
    """INV-LOCK-02: a colored die showing a ⚠ face is locked (the Secret face per the sub-flag)."""
    if not getattr(cfg, "colored_vuln_lock", False) or die.color not in LOCKABLE_COLORS:
        return False
    f = die.current_face
    if f is None or face_vuln(f) <= 0:
        return False
    return bool(cfg.colored_vuln_lock_secret) or not f.secrets_pending

def reroll_allowed(die, helix_active: bool) -> bool:
    """The single reroll gate (engine filter, bots, web later)."""
    return helix_active or not die.is_locked

def crossings(cfg, state) -> tuple:
    """Vulnerability values where one more ⚠ changes the Green exposure: the band thresholds plus the min target."""
    return tuple(sorted(set(cfg.vuln_band_thresholds) | {min_target(cfg, state)}))

def face_key(die) -> str:
    """'RED:5'-style key (1-based face index); same scheme as vuln_keep_by_face."""
```

`DieColor` import: use `sim.config.DieColor` (the module already imports `CubeColor` from there). Move the face-index lookup at `phase1_roll_deploy.py:517-520` into `face_key` and reuse it there, so the keys are identical.

### 4.2 `_evaluate_locks` (inner function, `phase1_roll_deploy.py:440`)

```python
def _evaluate_locks(dice_list):
    for d in dice_list:
        face = d.current_face
        if not face:
            continue
        if face.is_glitch:
            d.is_locked = True
        elif lock_on and vulnerability.lock_applies(cfg, d) and not d.is_locked:
            d.is_locked = True
            # telemetry (§8.1): lock event, by face; distinct die this phase
            player.lock_events += 1
            k = vulnerability.face_key(d)
            player.lock_events_by_face[k] = player.lock_events_by_face.get(k, 0) + 1
            locked_this_phase.add(d.die_id)
```

- `lock_on = cfg.colored_vuln_lock`. When it is off, the body is exactly today's (INV-LOCK-07).
- **Locks are sticky.** The pass never unlocks a die. A die unlocks only when the engine sets `is_locked = False`, which happens at the initial roll reset, after a die is rerolled (`:536`), on a face-set by ACE (`:124`), Release L4 (`:186`) or the legacy Helix face-set, and at the post-Deploy clear (§4.4). Re-evaluating right after any of these re-locks the die if its new face is ⚠.
- The lock is keyed on the **current printed face**. Choice faces lock like any other face (GD §6). The choice is still declared at Step 5.

### 4.3 Phase 1 ordering for one player (v0.47; the numbers are execution order)

| # | Step | Locks | Notes |
|---:|:---|:---|:---|
| 1 | Reset: `is_locked = False` on every active die (`:416`); `player.helix_bypass_active = False`; `locked_this_phase = set()` | cleared | per player, per round |
| 2 | Initial roll (`:417`) | — | unchanged RNG |
| 3 | Operator *Contingent Staffing* check on the initial roll (`:422-427`) | — | a White die never takes the ⚠ lock |
| 4 | (pre-v0.43 ACE at `:431`: not reached on the v0.46 lineage) | — | no change |
| 5 | `_evaluate_locks(active_dice)` (`:448`) | **first check** | glitch + ⚠ |
| 6 | Legacy Helix decision (`:450-468`) | — | **only** when `helix_bypass_mode == "LEGACY"` |
| 7 | Reroll loop, `while rerolls_remaining > 0`: | | `max_free_rerolls` still includes the Release L4 extra reroll (`research_tracks.free_rerolls_for`) |
| 7a | Helix offer (§5.2), `REROLL_LOCKED` only | — | before the bot picks this step's dice |
| 7b | `choose_yahtzee_rerolls` → `secret_face_policy.adjust_rerolls` → `vulnerability_policy.adjust_rerolls` (lock-aware, §6) | — | bot order unchanged |
| 7c | Filter: `valid = [i for i in reroll_indices if 0 <= i < n and reroll_allowed(active_dice[i], helix_active)]` | **gate** | same as today's two branches (`:499-508`), written once |
| 7d | Keep-rate telemetry (`:509-528`) | — | under lock, count a ⚠ as an event when `reroll_allowed(d, helix_active)` (replacing `not d.is_locked`); with the flag off, unchanged |
| 7e | `if not valid: break` | — | unchanged; a bot whose only picks are locked dice ends its rerolls |
| 7f | Reroll the valid dice; set `is_locked = False` (`:532-536`). If a rerolled die was locked (so `helix_active`), `player.helix_bypass_locked_rerolled += 1` | unlocked | |
| 7g | `_evaluate_locks`; Operator check → `_evaluate_locks` (`:538-543`) | **check after every reroll** | |
| 7h | Counters (`:545-548`) | — | unchanged |
| 8 | ACE after rerolls (`:551-572`) may target a locked die. Before it, record `pre = {i for i, d in enumerate(active_dice) if d.is_locked}`; after it, `ace_lock_breaks += |{i ∈ pre : face changed}|` | face-set clears the lock, then `_evaluate_locks` (`:572`) | ACE still can't set a Secret face (`ace_allows_secret_face=False`) |
| 9 | Helix face-set (`:574-597`) | — | **skipped** when `helix_bypass_mode == "REROLL_LOCKED"` |
| 10 | Release L4 Gray face-set (`:600`) | Gray only; never touches a colored lock | unchanged |
| 11 | Final `_evaluate_locks` (`:603`) + final-face telemetry (§8.1) | final | |
| 12 | `vulnerability.lock_in(...)` (`:607`): +1 Vulnerability per ⚠ on the **final** faces | — | unchanged; **this is the Deploy accounting** |
| 13 | **New:** if `lock_on`, set `d.is_locked = False` for every active die | cleared | nothing leaves Phase 1 locked (INV-LOCK-03) |
| 14 | Step 5 onwards (declare choices, Processing Box, In Production) | — | unchanged |

Why step 13 sits after `lock_in` and before Step 5: no Step 5 code reads `is_locked`, and the bot face-scoring helpers (`base.py:349`) must not see stale locks in later phases. Every downstream phase already resets `is_locked` when a die moves (`phase2_compiler.py:59/81/149/550/569`, `phase3_income.py:334/420`, `phase4_attack_resolution.py:92/620/650`, `phase5_pipeline_shift.py:32`), but Secret faces go to the Processing Box without passing through a reset, so the clear is required.

### 4.4 Interactions (normative)

| Interaction | Rule |
|:---|:---|
| Prodigy ACE | ACE is a face-set, not a reroll. It may target a locked die, and ⚠ counts on the face ACE sets. An ACE-set ⚠ face re-locks at step 8's `_evaluate_locks`. This is moot because no rerolls follow, but it is visible in telemetry. |
| Helix (`REROLL_LOCKED`) | Brute-Force Bypass turns off the gate for the rest of the phase (§5). A die rerolled under the bypass may roll ⚠ again. It re-locks, but it can still be rerolled while the bypass is active. |
| Release L4 | Its extra free reroll counts toward `max_free_rerolls` as today. The Gray face-set only targets Gray dice, which never take the ⚠ lock. `release_rerolls_used` is unchanged. |
| Operator *Contingent Staffing* | The White Contractor die it adds is never ⚠-locked. Its glitch faces still lock through the glitch rule. |
| Secret face, sub-flag off | It never locks and can be rerolled as in v0.46 (D5 control). |
| Choice faces with ⚠ | They lock like any other ⚠ face. The choice is declared at Step 5. |
| Gray dice | Never ⚠-locked. Their three ⚠ faces can always be rerolled. |
| v0.46 `vuln_keep_*` telemetry | With the lock on, colored ⚠ faces are locked, so they are not events unless Helix is active. The colored keep rate reads as "n/a under lock" in reports (GD §9), and the Gray keep rate is still meaningful. |

---

## 5. Helix *Brute-Force Bypass* (`REROLL_LOCKED`)

### 5.1 State and availability (mirror DTO *Slush Fund*)

`PlayerState.__init__` (beside `slush_fund_used_game`, `state.py:259`):

```python
self.helix_bypass_used_game = False   # once-per-game flag (mirror of slush_fund_used_game)
self.helix_bypass_active = False      # transient: this Phase 1 only
```

Add a property pair `helix_bypass_used` ↔ `helix_bypass_used_game`, mirroring `dto_slush_fund_used` (`:533-538`). Add an accessor that mirrors `is_slush_fund_available` (`:845-850`):

```python
def is_helix_bypass_available(self, active_ver=None) -> bool:
    cfg = getattr(self, "config", None)
    if cfg is not None and getattr(cfg, "helix_bypass_once_per_game", False) and self.helix_bypass_used_game:
        return False
    return self.is_ability_available(active_ver)
```

The bypass therefore needs **both** the active Version's Institutional Override status to be `AVAILABLE` and, once per game, the game flag to be unused. This is the same double check DTO uses (`phase4_attack_resolution.py:511-514`, `1091-1094`).

### 5.2 Activation (reroll loop step 7a)

```python
helix_mode = cfg.helix_bypass_mode == "REROLL_LOCKED"
is_helix_co = has_company_override(player, CompanyCode.HELIX, legacy_bridge_enabled(engine))
...
if (helix_mode and is_helix_co and not helix_active
        and player.is_helix_bypass_available(active_ver)
        and any(d.is_locked for d in active_dice)):
    if player.bot.choose_helix_bypass(player, active_dice, rerolls_remaining, engine.state):
        helix_active = True
        player.helix_bypass_active = True
        player.mark_ability_used(active_ver)
        if cfg.helix_bypass_once_per_game:
            player.helix_bypass_used_game = True
        player.helix_bypass_uses += 1
        player.helix_bypass_use_log.append({"round": engine.state.current_round, "version": active_ver,
                                            "step": max_free_rerolls - rerolls_remaining,
                                            "locked": sum(1 for d in active_dice if d.is_locked)})
```

- The bypass is offered **at every reroll step** while it is unused and some die is locked. A lock that appears after the first reroll can still be answered. The bypass is never offered with 0 rerolls left, because it has no effect then; the `while` condition guarantees this.
- There is no `+1` reroll and no face-set (steps 6 and 9 are `LEGACY` only).
- The hook takes no `rng` argument and must consume no RNG (INV-LOCK-08).
- The hook runs only when the bot would actually see a choice. That keeps `ReferenceSearchBot` and `MixedPolicyBot` call counts deterministic.

### 5.3 Black Signature (Target Lock) interaction (`_resolve_signature_black`, `phase4_attack_resolution.py:845-871`)

Mirror the DTO branch exactly:

```python
is_helix_once = (is_helix_company(player) and getattr(engine.config, "helix_bypass_once_per_game", False))
override_available = (
    player.is_ability_available(active_ver)
    and not player.company_ability_used_this_version
    and (not is_dto or not player.dto_slush_fund_used)
    and (not is_helix_once or not player.helix_bypass_used_game)
)
if override_available:
    player.mark_ability_used(active_ver)
    if is_dto:
        player.dto_slush_fund_used = True
    if is_helix_once:
        player.helix_bypass_used_game = True
        player.helix_bypass_lost_to_black += 1
    player.signature_override_hijacks += 1
else:
    ...  # unchanged: lose signature_black_secret_loss (2) Corporate Secrets
```

The normative outcomes are:
- A Black Signature against a Helix player whose bypass is still unused **burns the single use** (no Secret loss).
- Once the bypass has been used (in any Version), the Black Signature **costs 2 Secrets**.
- The same two outcomes hold for DTO's *Slush Fund* today.

Use the same Helix company predicate as the DTO line (`has_company_override(...) or company.code == HELIX`). With `helix_bypass_once_per_game=False` the new clause is inert, so v0.46 is byte-identical.

---

## 6. Bots

### 6.1 `AWARE` rule (the probe heuristic, made config-correct). This is the minimum bar.

For each index `i` the bot still wants to reroll, where die `i` is lockable, its current face is clean (`face_vuln == 0`), and `not helix_active`:

```
tbl_v = player.vulnerability + Σ_{j ∉ out} face_vuln(dice[j].current_face)     # faces staying on the table
drop i  if  (tbl_v + 1) in vulnerability.crossings(cfg, state)
```

This is the probe's rule (`probe_locked_vuln.py:39-44`), with one fix. The probe hard-coded `(4, 7, 10)` even in the "safe 0–4" arms. The engine uses `crossings(cfg, state)`, which is `(5, 8, 11)` under v0.47. See OQ-1.

### 6.2 `LAMBDA` rule (§9 Senior-engineer plan)

The candidates are the same as in §6.1. Process them in index order and keep a running expected table:

```
v_tab = player.vulnerability
        + Σ_{j ∉ chosen} face_vuln(current_j)
        + Σ_{j ∈ chosen, j ≠ i} mean_f face_vuln(f over dice[j].faces)          # expected ⚠ of the other rerolls
lam_v = lam(player, state, round(v_tab), params)                                  # cost of the step v_tab → v_tab+1
keep   = _face_value(player, d, cur, state, queue0)
reroll = mean_f [ _face_value(player, d, f, state, queue0) − lam_v · face_vuln(f) ]
drop i  if  reroll < keep + params.lock_reroll_margin
```

Because λ is evaluated at the **post-roll table Vulnerability**, a step that crosses a band is priced at the crossing cost (GD §9). Under the lock, a ⚠ result can't be undone, so the reroll is priced as a one-shot lottery. If the clean face rolled again, it could be rerolled at the next step, and the bot does not model that option. `lock_reroll_margin` absorbs it.

### 6.3 Where the filter runs (`vulnerability_policy.adjust_rerolls`)

The new code is gated on `cfg.colored_vuln_lock`. With the flag off, the function is byte-identical.

| Stance | v0.47 behaviour |
|:---|:---|
| `KEEP_ALL`, `KAMIKAZE` | unchanged; no lock filter |
| `ADAPTIVE`, `PEN_TEST_RUSH` | Run the existing two-pass ⚠ logic over `rerollable = [i … if reroll_allowed(d, player.helix_bypass_active)]` instead of `unlocked`. Then apply the lock filter for `params.lock_policy`. |
| `REROLL_ALL` | Add every rerollable ⚠ die, as today (under lock that means Gray dice, plus colored dice while Helix is active). Then apply the lock filter. |
| **`NO_COLOR_REROLL`** (new; dominance matrix) | Drop every lockable-colour index. Gray rerolls are kept. |
| **`STAR_CHASE`** (new; dominance matrix) | Reroll every rerollable lockable die not showing ★, plus the base bot's Gray picks. No lock filter. |

Add `NO_COLOR_REROLL` and `STAR_CHASE` to `STRATEGIES`. `choose_vulnerability_stance` never returns them unless `bot.vuln_strategy` is set, the same as `KAMIKAZE` today.

**Decline telemetry.** `adjust_rerolls` gains an optional `stats: Optional[Dict[str, int]] = None` kwarg. The filter adds one count per dropped index to `stats["aware"]`, `stats["lambda"]` or `stats["no_color"]`. The engine passes a local dict and merges it into `player.lock_declined_rerolls` (§8.1). Bots never write to `PlayerState` (fast_clone hazard H5).

### 6.4 Helix decision: `BaseBot.choose_helix_bypass(player, active_dice, rerolls_remaining, state) -> bool`

The default delegates to `vulnerability_policy.helix_bypass_default`, which is pure and uses no RNG:

```
if stance in (KEEP_ALL, KAMIKAZE) or rerolls_remaining <= 0: return False
locked = [i: lockable(d_i) and d_i.is_locked and face_vuln(cur_i) > 0]
if not locked: return False
tab = player.vulnerability + Σ_all face_vuln(current)             # what Deploy would add if nothing changes
L   = Σ_{i ∈ locked} face_vuln(cur_i)
cross = any(tab − L < c <= tab for c in crossings(cfg, state))    # the locked ⚠ push it across a band / into range
lam_v = lam(player, state, tab, params)
gain  = Σ_{i ∈ locked} [ mean_f net(f) − net(cur_i) ]  with net = _face_value − lam_v·face_vuln   # ★ odds included in mean_f
last_chance = state.is_final_round or (version_index(state) == 2 and rounds_left(state) <= 1)
return (cross and gain >= params.helix_min_gain) or (last_chance and gain > 0)
```

- `choose_helix_override` (the legacy hook, `base.py:282`) is **not** called in `REROLL_LOCKED` mode. The archetypes' `choose_prodigy_ability` returns `any(d.is_locked)`, which under the lock would fire on the first roll of the game and waste the single use.
- Mixed seat: add `"choose_helix_bypass": "phase1_roll"` to `HOOK_DTYPES` (`mixed_policy.py:42-45`).
- ref1: not searched; it uses the BaseBot default (the same as the legacy Helix hook today).

### 6.5 ACE target under lock (`BaseBot.choose_prodigy_purple_star_override`, `base.py:1194`)

When `cfg.colored_vuln_lock` is on and `white_hat_6f_rebalance` is on, route the choice to a new pure function, `vulnerability_policy.choose_ace_target(player, active_dice, state, excluded)`:
- **Targets:** any die except the single Purple ★ source and any `excluded_targets`.
- **Legal faces:** non-★ and non-Secret (the engine rule at `phase1_roll_deploy.py:119`).
- **Choice:** maximise `net(f) − net(cur)` with λ at the table Vulnerability.
- **Tie-breaks:** a locked core ⚠ die first, then a locked Secret-face die, then the lowest index.
- Return `None` when the best gain is ≤ 0.

Glitch dice can't occur in v0.46 or v0.47, so the existing glitch priority can stay first.

The engine passes `excluded_targets` today, but the bot hook signature does not take it. Add an optional `excluded_targets=None` kwarg to the hook and pass it from `resolve_prodigy_purple_star_override` **only when** `colored_vuln_lock` is on, so the v0.46 call is unchanged.

### 6.6 Pen Test policy (`apply_pen_test_policy`, `vulnerability_policy.py:192-244`)

The hard-coded `V >= 3`, `V - 2` and `pen_clean_target = 2` / `pen_clean_trigger = 3` were written for the 0–3 safe zone (min target 4). When `pen_relative_to_floor` resolves to True:
- Let `floor = min_target(cfg, state)` and `s = floor − 4`.
- Replace `3` with `floor − 1` and `V − 2` with `V − (floor − 2)`.
- Use `pen_clean_target + s` and `pen_clean_trigger + s`.
- `REROLL_ALL` uses `V >= floor − 1` and `want = V − (floor − 2)`.

When `floor == 4` this is the identity, so v0.46 and its arms with `min_target = 4` are unchanged even when the flag is on. Under v0.47 (`floor = 5`), the bots aim for a Vulnerability of 3 or below and act from 4 up, which mirrors the v0.46 headroom. No other Pen Test change: the GD "λ pulls Pen Test" idea is an optional sweep arm, `pen_lock_headroom` (OQ-5), not a default.

### 6.7 ref1 (`reference_search.py`)

- `build_portfolio(bot_id, vulnerability=False, locked=False)`. When `locked` is True (`cfg.colored_vuln_lock`), append `AdaptiveBalanced[no_color_reroll]` and `AdaptiveBalanced[star_chase]` **after** the three V046 members. Appending them only under v0.47 keeps the v0.46 ref1 candidate sets and the candidate RNG indices unchanged (the same pattern as vulnerability spec §13.6).
- `bind()` (`:319-328`) passes `locked=cfg.colored_vuln_lock`.
- The stance is still the only searched Phase 1 hook. Rerolls, the Helix bypass and ACE use the defaults above inside the rollouts.
- Expected effect (GD §6): ref1 can no longer reroll a Secret face to dodge a band. It did that 20–30% of the time, so its edge should narrow. §11.4 measures this.

### 6.8 Other archetypes

- `choose_yahtzee_rerolls` in the five archetypes may keep proposing locked dice. The engine gate drops them, and that is intended (it is also why step 7e breaks).
- Don't edit the archetype files. `adaptive_balanced.py:194` (`die.is_locked and not is_prodigy`) is harmless, because the engine gate is authoritative.

---

## 7. Seeding and determinism

- **No new RNG draws.** The lock evaluation, the Helix offer, every bot policy and all telemetry consume nothing from `engine.rng`. RNG streams diverge from v0.46 only because fewer or different dice get rerolled (INV-LOCK-08).
- **Common random numbers.** Every sweep arm and preset runs on the same seeds, `42..1241` (1,200 per pod), with the `mixed1` roster rule: one `MixedPolicyBot` seat, rotated by `seed % P` (`run_v380_secret_faces_sweep.build_engine`). Paired-seed bootstrap gives the 95% CIs for the deltas.
- Unit tests use the fixed seeds `42 / 43 / 44` for 2P / 3P / 4P unless noted.
- The `fast_clone` round trip must be identical on `v046_locked_roster`. The new `PlayerState` fields are plain `bool` / `int` / `dict` / `list`, so they clone with the existing generic copy. The transient `helix_bypass_active` is always `False` at a round boundary.

---

## 8. Telemetry

### 8.1 `PlayerState` fields (initialise them in `__init__` beside the v0.46 block; plain types)

| Field | Type | Written at | Meaning |
|:---|:---|:---|:---|
| `lock_events` | int | §4.2 | False→True ⚠-lock transitions (a die re-locked after a Helix reroll counts again) |
| `lock_events_by_face` | `Dict[str, int]` | §4.2 | the same, keyed `"RED:5"` |
| `lock_dice_by_round` | `Dict[int, int]` | step 11 | distinct dice ⚠-locked at any point in this round's Phase 1 (`len(locked_this_phase)`) → **locks per player-round** |
| `locked_vuln_kept_by_face` | `Dict[str, int]` | step 11 | ⚠ on the final face of dice that were ever ⚠-locked this phase → **locked ⚠ by face** |
| `vuln_kept_by_source` | `Dict[str, int]` | step 11 | final-face ⚠ split into `"core"` (colored, not Secret), `"secret"` and `"gray"` |
| `vuln_kept_by_color` | `Dict[str, int]` | step 11 | final-face ⚠ by `die.color.value` |
| `colored_dice_rolled_by_color` | `Dict[str, int]` | step 11 | lockable dice in the active pool |
| `colored_star_by_color` | `Dict[str, int]` | step 11 | of those, final face ★ → **P(★) per colored die** |
| `lock_declined_rerolls` | `Dict[str, int]` | §6.3 merge | `"aware"`, `"lambda"`, `"no_color"` |
| `ace_lock_breaks` | int | step 8 | locked dice whose face ACE changed |
| `helix_bypass_uses` | int | §5.2 | |
| `helix_bypass_use_log` | `List[dict]` | §5.2 | round, version, step, locked count |
| `helix_bypass_locked_rerolled` | int | step 7f | locked dice rerolled under the bypass |
| `helix_bypass_vuln_removed` | int | step 11 | Σ over dice locked when the bypass fired: (⚠ at activation − ⚠ on the final face), floored at 0 |
| `helix_bypass_lost_to_black` | int | §5.3 | single use burnt by a Black Signature |

Write the step-11 fields only when `lock_on`. Write the Helix fields only in `REROLL_LOCKED` mode.

### 8.2 End row `_v047_row(cfg, p)` (`end_game.py`)

- Emit it **only when `cfg.colored_vuln_lock`**: `**(_v047_row(cfg, p) if getattr(cfg, "colored_vuln_lock", False) else {})` beside the `_v046_row` merge at `:335`.
- Keys: every §8.1 field, plus `helix_bypass_used_game`, `company_color` (the Client Company die colour, from the `config.py:17` map) and `purchases_by_color` (existing).
- The rankings dict feeds the v0.46 parity digest, so an unconditional emit would break INV-LOCK-07.

### 8.3 Sweep-derived metrics (`scripts/run_locked_vuln_sweep.py`; per pod)

| Metric | Definition |
|:---|:---|
| Locks per player-round | Σ `lock_dice_by_round` ÷ surviving player-rounds |
| Locked ⚠ by face | Σ `locked_vuln_kept_by_face[k]` ÷ Σ `colored_dice_rolled_by_color[color(k)]`, per key |
| Kept ⚠ per die by colour and source | `vuln_kept_by_color` ÷ rolled; `vuln_kept_by_source` ÷ player-rounds |
| P(★) per colored die | Σ `colored_star_by_color` ÷ Σ `colored_dice_rolled_by_color`, overall and by colour |
| Lock-breaks | Σ `ace_lock_breaks`, Σ `helix_bypass_locked_rerolled` per game |
| Declined near-threshold rerolls | Σ `lock_declined_rerolls` by reason, per player-round |
| Helix uses | share of Helix seats with a use; round histogram from `helix_bypass_use_log`; lost to Black %; mean `helix_bypass_vuln_removed` |
| **Helix win rate** | Win share of Helix-company seats (ties split), per pod, against v0.46 on the same seeds |
| **Per-colour win rates** (balance by win rate) | For C ∈ {Red, Blue, Green, Yellow}: **(a)** win share of seats whose Client Company die is C; **(b)** win share of seats with `purchases_by_color[C] ≥ 1`; **(c)** the purchase-weighted win share Σ win·n_C ÷ Σ n_C. Purple is in every pool, so it is reported only as kept ⚠ / P(★). |
| Colored dice bought / game | Σ `purchases_by_color` over R/B/G/Y ÷ games |
| Release L4 share | seats reaching Release L4 %, `l4_payouts["release_gray_face_sets"]` per game (report only) |
| White Hat win | Prodigy, Operator (and all White Hats) win share against v0.46 |

---

## 9. Invariants

| ID | Statement |
|:---|:---|
| **INV-LOCK-01** | With `colored_vuln_lock` on, no die that has `is_locked == True` at a reroll step is rerolled in that step unless Brute-Force Bypass is active (`helix_active`). ACE, Release L4 and other face-sets are not rerolls. |
| **INV-LOCK-02** | After the initial roll (and the Operator check), after every reroll step, after ACE and at the final pass, every die in `LOCKABLE_COLORS` whose current face has `vuln > 0` is locked (Secret faces only when `colored_vuln_lock_secret`). Gray Legacy and White Contractor dice are never ⚠-locked. The glitch rule is unchanged. |
| **INV-LOCK-03** | Locks are sticky within Phase 1. A die unlocks only when it is rerolled (bypass) or its face is set by an override. Under the flag, no die leaves Phase 1 (In Production, Processing Box or elsewhere) with `is_locked == True`. |
| **INV-LOCK-04** | ⚠ counts on the final face. The `"lockin"` Vulnerability gain equals Σ `face_vuln` over the final faces after ACE and Release L4, whatever the lock history (INV-VULN-01 unchanged). |
| **INV-LOCK-05** | Brute-Force Bypass under `REROLL_LOCKED` grants no extra reroll and no face-set. It is offered only to a Helix player with rerolls left, at least one locked die and `is_helix_bypass_available`. Under `helix_bypass_once_per_game`, `helix_bypass_uses + helix_bypass_lost_to_black ≤ 1` per game. Each use marks the active Version's Institutional Override `USED`. |
| **INV-LOCK-06** | A Black Signature against a Helix player with `helix_bypass_once_per_game` either burns the unused bypass (no Secret loss, `helix_bypass_used_game` set) or, if it is already used, costs `signature_black_secret_loss` Secrets. Never both, never neither. This mirrors INV-SIG-BLACK for DTO. |
| **INV-LOCK-07** | With every v0.47 flag at its default, `v046()` / `v046_roster()` replay byte-identically against a golden captured **before** any v0.47 change. INV-PARITY (v0.45 golden) and all older parity tests still pass. `_v047_row` is absent from pre-v0.47 rankings. |
| **INV-LOCK-08** | v0.47 code consumes no RNG. Bot lock policies are pure and never write to `PlayerState` or bot objects. Same seed means the same result, and the `fast_clone` round trip on `v046_locked_roster` is identical. |
| **INV-LOCK-09** | The §3.4 validation rejects every unsupported combination. |
| **INV-LOCK-10** | Release L4's extra free reroll and the Gray face-set behave as in v0.46. Gray dice can be rerolled at every step. |
| **INV-LOCK-11** | With `colored_vuln_lock_secret=False`, a Secret face never locks, and a die showing it can be rerolled like in v0.46. |
| **INV-LOCK-12** | INV-VULN-08 (face tables) holds for `V046_VULN`: every colored die has exactly two ⚠ faces (core + F5; Yellow F1 + F5), and ★ faces have `vuln == 0`. |

---

## 10. Test list (`tests/test_locked_vuln_faces.py` unless noted; `-q`; fixed seeds)

**Step 0: golden (before any engine edit)**
- `tests/parity_v046_mixed/capture.py`: the same `digest` as `tests/parity_v045/capture.py`. `CONFIGS = ("v046", "v046_roster")` × 2/3/4P × seeds `42..141`, plus `v046_roster|mixed1` × 2/3/4P × seeds `42..91` (built with `run_v380_secret_faces_sweep.build_engine`). Commit `golden.json` first. Store it outside `tests/fixtures/` (write-protected).
- `tests/test_locked_vuln_parity.py::test_v046_replays_golden`: **the v0.46 regression-reproduction test** (INV-LOCK-07).
- `test_v047_flags_off_reproduce_v046`: `GameConfig.v047(colored_vuln_lock=False, helix_bypass_mode="LEGACY", helix_bypass_once_per_game=False, die_face_profile="V046_VULN_NOPREMIUM", vuln_band_thresholds=(4, 7, 10), vuln_min_target_by_version=(4, 4, 4))` gives the same digest as `v046` for 30 seeds × 2/3/4P.
- The existing `tests/test_v460_parity.py` (v0.45 golden) and the v035–RSP-1 parity tests stay green.

**Config**
- `test_v047_preset_values`: the five overrides plus the inherited `power_profile`, `white_hat_6f_rebalance` and `signature_attack_mode`.
- `test_v047_validation`: each §3.4 row raises; `colored_vuln_lock_secret=False` alone is fine; arm A (NOPREMIUM + lock) constructs.
- `test_v046_defaults_unchanged`: `v046()` has the lock off, `LEGACY` and not once-per-game.

**Lock rule (scripted dice; set `current_face` directly, with a stub bot that returns fixed reroll indices)**
- `test_core_vuln_face_locks_after_initial_roll` for R, B, G, Y (F1 and F5), P.
- `test_secret_face_locks` and `test_secret_face_unlocked_when_subflag_off` (INV-LOCK-11).
- `test_gray_never_locks` and `test_white_contractor_never_vuln_locks`.
- `test_lock_after_reroll`: a clean die rerolled onto ⚠ (seeded) is locked at the next step and not rerolled again (INV-LOCK-01, -02).
- `test_locked_die_request_is_dropped_and_breaks_loop`: a bot asking only for locked dice ends its rerolls; faces are unchanged.
- `test_locks_sticky_and_cleared_after_deploy` (INV-LOCK-03): no die is locked in In Production or the Processing Box after Phase 1.
- `test_vuln_counts_final_face_after_ace`: ACE turns a locked core ⚠ clean, so its ⚠ is not counted and `ace_lock_breaks == 1`. ACE setting a ⚠ face counts it (INV-LOCK-04).
- `test_release_l4_unaffected` (INV-LOCK-10): the extra reroll is available, the Gray face-set works, and `release_rerolls_used` increments as in v0.46.
- `test_operator_contingent_die_no_vuln_lock`.
- `test_lock_no_rng`: the RNG state after Phase 1 with every die locked equals the state after a roll with no rerolls (INV-LOCK-08).

**Helix**
- `test_helix_reroll_locked_dice`: after activation, locked dice can be rerolled; there is no +1 reroll (`max_free_rerolls` unchanged) and no face-set call (a spy on `choose_helix_face_override*` sees 0 calls).
- `test_helix_offered_per_step`: a lock that first appears after reroll 1 can be answered at step 2. There is no offer with 0 rerolls left or with no locked die.
- `test_helix_once_per_game`: a use in v1.0 makes the bypass unavailable in v2.0 and v3.0 (Version status `AVAILABLE`, game flag set). The per-version control arm (`once_per_game=False`) allows one use per Version.
- `test_black_burns_unused_helix_bypass` and `test_black_after_helix_use_costs_two` (INV-LOCK-06); DTO behaviour is unchanged (regression).
- `test_legacy_helix_unchanged_under_v046`: the same Helix trace as the golden on a Helix seed.
- `test_helix_bypass_default_triggers_on_band_cross`: V = 3, a locked Blue F3 and a locked Red F5 (tab 5, crossing 5) gives True; V = 0 with one locked die gives False; final round with gain > 0 gives True; `KEEP_ALL` gives False.

**Bots**
- `test_aware_rule_uses_config_crossings`: tab 4 under v0.47 drops a clean colored reroll; tab 3 does not; tab 4 under v0.46 thresholds does not.
- `test_lambda_rule_prices_crossing`: the same pool near a crossing drops it, and far from one keeps it; `lock_reroll_margin` shifts the decision.
- `test_lambda_aware_superset`: the dropped set ⊇ the AWARE dropped set (the minimum bar).
- `test_no_color_reroll_and_star_chase_stances`.
- `test_adjust_rerolls_unchanged_when_lock_off`: v0.46 inputs give the same outputs (property test over 200 random pools).
- `test_ace_prefers_locked_core_vuln`.
- `test_pen_policy_floor_relative`: floor 4 gives identical plans to v0.46; floor 5 shifts the thresholds by +1.
- `test_ref1_portfolio_v046_unchanged` and `test_ref1_portfolio_v047_appends_two`.
- `test_mixed_hook_dtype_helix_bypass`.

**Telemetry and determinism**
- `test_v047_row_only_under_lock` and `test_lock_telemetry_counts` (a scripted round with known locks, ★ and ⚠ by source).
- `test_v047_determinism_and_fast_clone` (pattern of `TestV046Determinism`).
- `test_v047_smoke_invariants`: 20 games per pod with the §11.1 invariant checkers installed.

---

## 11. Sweep outline for the product-owner

All scripts are quiet by default, write JSON to `sim_results/locked_vuln_v046base/` and print summary tables only. Run them via WSL.

### 11.1 `scripts/run_locked_vuln_sweep.py` (new; reuses `run_v046_sweep.play / play_all / metrics / guardrails`)

- **`--step smoke`**:
  - Runs `--assert-invariants` with 300 games per pod on `v046_locked_roster`.
  - Installs the v0.46 checkers plus these:
    - **INV-LOCK-01:** wrap `Die.roll`. The engine sets a module dict `phase1_roll_deploy._ROLL_CTX = {"helix_active": bool}` around each reroll batch (a plain assignment, so no RNG and no behaviour change). The check asserts `not self.is_locked or _ROLL_CTX["helix_active"]`.
    - **INV-LOCK-02:** wrap `vulnerability.lock_in`. Every lockable ⚠ die must be locked, and Gray/White dice must not be ⚠-locked.
    - **INV-LOCK-03:** after Phase 1, no die is locked.
    - **INV-LOCK-05 / -06:** per-game counters.
- **`--step main`**:
  - Runs `v045_roster` (guardrail comparator), `v046_roster` (delta comparator) and `v046_locked_roster`.
  - Roster `mixed1`, seeds `42..1241`, 1,200 games per pod, 2P / 3P / 4P.
  - **Pre-check:** `v046_roster` must reproduce FINDINGS §62:
    - Green lost per player-game 2.42 / 2.08 / 1.86.
    - Rounds 8.20 / 7.77 / 7.51.
    - Market Collapse 35.7 / 21.1 / 22.8.
  - If it does not, stop and report.
- **`--step arm --arm <id>`**: 1,200 games per pod at 2P / 3P / 4P. The arms below are override dicts, not presets:

| Arm | Overrides on `v046_locked_roster` | Purpose |
|:---|:---|:---|
| `A_nopremium` | `die_face_profile="V046_VULN_NOPREMIUM"` | D2 control |
| `B_safe03` | bands `(4,7,10)`, min `(4,4,4)` | D1 control |
| `A_safe03` | both of the above | probe arm A |
| `dmg_112` | `vuln_band_damage=(1,1,2)` | counter-lever |
| `green_yield_3` | `green_secret_vuln_reduction=3` | counter-lever |
| `pen_cost_1` | `pen_test_cost=1` | counter-lever |
| `secret_lock_off` | `colored_vuln_lock_secret=False` | D5 control |
| `helix_per_version` | `helix_bypass_once_per_game=False` | cost of the once-per-game rule |
| `helix_legacy` | `helix_bypass_mode="LEGACY"` | probe semantics (+1 reroll, face-set) |
| `bots_naive` / `bots_aware` / `bots_lambda` | `vuln_bot_params.lock_policy` = `NONE` / `AWARE` / `LAMBDA` | bot sensitivity; `bots_aware` vs the GD probe "B aware + safe 0–4" row (2.23 / 1.93 / 1.76) |
| `pen_lock_headroom` | (only if OQ-5 is implemented) | optional |

  - `--set` and `--vuln-params` are layered onto the preset: `dataclasses.replace(cfg.vuln_bot_params, **json)`, never a fresh `VulnPolicyParams`.
- **Guardrails** (pass/fail table per pod):
  - The v0.46 §8.2 set, unchanged from `run_v046_sweep.guardrails` against v0.45:
    - Mean rounds 6.5–8.5.
    - Patient Zero ≤ v0.45 + 3.
    - Total Wipeout ≤ 15 / 5 / 2 %.
    - Market Collapse within v0.45 ± 5.
    - v1.0 breach ≤ v0.45.
    - Green lost 1.2–2.5 per player-game.
    - Green no-target 25–70 % (2P sits at the edge, about 65 %).
    - Rounds-7+ no-target ≤ 60.
    - Lose-3 rounds ≤ 5 %.
    - Liquid income ≤ v0.45 × 1.25.
    - 4P company spread ≤ 10 pp (a known FAIL; report it).
    - Seat spread ≤ 6 pp.
    - 2+ L4 tracks ≤ 5 %.
    - At cap ≤ 1 %.
    - Back-to-back unaffordable ≤ v0.45.
  - Plus the GD §9 rows against **v0.46**:

| New guardrail | Bar |
|:---|:---|
| Per-colour win-rate parity (§8.3 a/b/c) | Flag any colour more than 5 pp from the colour mean (OQ-4); Yellow is named |
| Helix company win | ≥ v0.46 − 2 pp, per pod |
| Prodigy and Operator win | within ± 3 pp of v0.46 |
| P(★) per colored die | ≥ 0.12 |
| Colored dice bought per game | ≥ v0.46 − 10 % |
| Release L4 share | report only |

- **Report:** the GD §4 columns for each pod (rounds, Patient Zero, Total Wipeout, Market Collapse, Green lost, Pen Test steps, end Secrets, Green no-target), plus every §8.3 metric, with 95% paired CIs on the deltas against v0.46.

### 11.2 Dominance matrix (`scripts/run_v046_dominance_matrix.py`; add `--config` with default `v046_roster`)

- Run with `--config v047_roster`.
- Focal policies: {KeepAll, RerollAllVuln, Adaptive, **NoColorReroll**, **StarChase**, PenTestRush, Kamikaze}. Fields: {Adaptive, KeepAll, RerollAllVuln}.
- 1,200 games per cell at 3P, seeds `42..1241`, with the focal seat rotated. Repeat the Adaptive-field row at 2P and 4P.
- **Flag:** a focal policy whose win share beats the Adaptive control's focal share by more than 3 pp, with the 95% CI excluding 0.
- Report each focal policy's ⚠ kept and P(★).

### 11.3 ref1 check (`scripts/run_reference_bot_validation.py --config v047_roster`)

- 3P, 600 games (seeds `42..641`), plus a 2P / 4P smoke of 100 games each.
- **Report:**
  - ref1 win share against fair share, against the same run on `v046_roster`.
  - ref1 stance choices, including the share of NO_COLOR_REROLL and STAR_CHASE.
  - ref1 Helix bypass timing.
  - ref1 ⚠ kept per player-round.
- **D5 bar:** the ref1 edge over fair share must not grow against v0.46. The expected effect is that it narrows, because ref1 can no longer dodge a band by rerolling a Secret face.

---

## 12. Implementation order (senior-engineer) and touched files

1. **Capture the v0.46 golden** (`tests/parity_v046_mixed/`) on the untouched engine, and commit it.
2. `config.py`: add the fields, `VulnPolicyParams` additions, `_validate_v047`, `v047()` and `v047_roster()`.
3. `vulnerability.py`: add the helpers (§4.1).
4. `state.py`: add the Helix flags and accessor, and the telemetry fields (§5.1, §8.1).
5. `phase1_roll_deploy.py`: make the §4.2–§4.3 and §5.2 edits, plus `_ROLL_CTX`.
6. `phase4_attack_resolution.py`: add the Black mirror (§5.3).
7. `end_game.py`: add `_v047_row`.
8. Bots: `vulnerability_policy.py` (§6.1–§6.6), `base.py` hooks, `mixed_policy.py`, `reference_search.py`.
9. Tests (§10); then run the parity suite (`-q`).
10. Scripts (§11): `run_locked_vuln_sweep.py`, then add `--config` to the dominance matrix and the ref1 script.

Mirror rule (RB-07): `_run_round_six_phase` and `resume_round` stay untouched.

---

## 13. Open questions (defaults let implementation proceed)

1. **OQ-1, probe threshold mismatch.** The GD probe's "aware" rule used `(4, 7, 10)` in the safe-0–4 arms. The spec uses `crossings(cfg)`, which is `(5, 8, 11)`. The `bots_aware` arm may therefore not match the probe row (2.23 / 1.93 / 1.76). The product-owner reports the gap, and the game designer judges it.
2. **OQ-2, Helix offer timing.** The default offers the bypass at every reroll step. The alternative is to offer it once, after the initial roll. RULES wording is later work, but it should read "during your rerolls".
3. **OQ-3, Black Signature against the once-per-game bypass.** The default mirrors DTO: an unused bypass is burnt; a used one costs 2 Secrets. Please confirm this when RULES is synced.
4. **OQ-4, parity bar.** The default flags any colour more than 5 pp from the colour mean. The game designer may tighten it.
5. **OQ-5, Pen Test headroom.** The optional arm `pen_lock_headroom` is the GD idea that "λ near a threshold pulls in Pen Test". It is not specified beyond an arm hook.
6. **OQ-6, glossary collision (doc phase).** The **Institutional Override Track** already uses the status "Locked" (GLOSSARY line 17), alongside the new "locked die". Flag this for the term-approval step in GD §10.
