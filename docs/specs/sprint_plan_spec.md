# Technical Architecture Specification: Sprint Plan & Gray Legacy Rotation (`v0.47.0` candidate, Phase 68)

> **Version note (2026-11-19):** written as `v0.47.0`; renumbered **`v0.48.0` / Phase 69** and rebased onto the `v0.47.0` Red Signature release. Code names: `GameConfig.v048()` / `v048_roster()` (inherit `v047()`), Gray profile `V048_SPRINT`, `scripts/run_v048_sweep.py`, `tests/test_v480_*.py`, parity goldens `tests/parity_v046/` and `tests/parity_v047/`. Text below keeps the original `v047` names.

**Author:** principal-engineer. **Date:** 2026-11-19. **Status:** ready for `senior-engineer`.
**Design source:** `docs/reports/sprint_plan_analysis.md` §0, §4–§9 (User sign-off 2026-11-19: arm **QC** + `6` starting Corporate Secrets; §7 L1 Gray lock; priority reading `A`).
**Baseline:** `GameConfig.v046()` / `v046_roster()` (`sim/config.py:1124-1151`).
**Reference implementation (read-only, scratch):** `sprint_probe5.py` in the session scratchpad (`MODE=A LOCK=gray GRAY=clean2 START7=1 L3THIN=DEFENSE,RELEASE L1R=DEFENSE=sec1,TRIAGE=cash2,RELEASE=bw1 SEC=1`). The engine code must reproduce its QC numbers within noise (§16.2).

Out of scope: `RULES*.md`, `GLOSSARY.md`, `pnp/`, `tts/`, `web/` (web is a follow-up, §19), the colored-die lock (branch `…-4668d8`), the stranding backup rule (§4 item 1), the `STRICT` reading, the Round 2 dip lever (§9.7).

---

## 0. Terminology guardrails

- Sim identifiers keep their legacy names for parity (§13). Every **user-facing** string (log text, Breakthrough preview, record labels exposed to the web, star notes) uses the approved v0.47 terms when `sprint_plan_enabled` is on, and the legacy text when it is off.
- Approved terms used here: **Sprint Plan**, **Current Sprint**, **Next Sprint**, **Research & Development (R&D)**, **R&D face**, **Sprint Review**, **Deep Data Vault**, **Terminal Hardware Tracks**. No other new terms. "Return 1 Gray Legacy die you own to the box" reuses existing wording; "+1 Release Bandwidth this round" reuses *Jumper Diagnostics* wording.
- Do not resurrect any CLAUDE.md deprecated term in code strings, docstrings or test names.

## 1. Scope summary

| # | Change | Lever(s) | v047 value |
|:--|:--|:--|:--|
| 1 | Sprint Plan split of `scanned_dice` into Current / Next; Sprint Review replaces Scanned Graduation | `sprint_plan_enabled` | `True` |
| 2 | Gray table: 1 ⚠ (Face 3); Faces 1–2 clean | `gray_face_profile` | `"V047_SPRINT"` |
| 3 | Gray dice showing ⚠ cannot be rerolled | `vuln_face_lock` | `"GRAY"` |
| 4 | Setup: 3 extra Gray in the Current Sprint | `starting_current_sprint_gray` | `3` |
| 5 | Starting Corporate Secrets | `starting_secrets_by_player_count` | `V047_STARTING_SECRETS = {2: 6, 3: 6, 4: 6}` |
| 6 | Breakthroughs: Pen Test L1 / L3, Triage L1, Release L1 / L3 | §3.1 | QC table |
| 7 | Bot research focus (thinning-aware) + rush stress policy | `bot_research_mode`, `bot_research_rush`, … | `"THINNING_AWARE"` in `v047_roster` only |
| 8 | Telemetry for sweeps | always on when flag on | §12 |

Every lever defaults to the v0.46 behaviour. `v046()` and older presets set none of them, so they stay bit-identical (§16).

## 2. Engine map (touch points)

| Area | File : symbol | Change |
|:--|:--|:--|
| Sprint helpers (new) | `sim/engine/sprint_plan.py` | §5 |
| Production Return | `phase5_pipeline_shift.production_return_to_scanned` (`:112`) | Mark Current when Current empty (§6.1) |
| Sprint Review | `phase5_pipeline_shift.graduate_scanned` (`:184`), `max_graduates`, `validate_graduate_ids` | Branch to `sprint_plan.sprint_review` when flag on (§6.2) |
| Triage | `conveyor_triage_v038` (`:248`) | None (enters Next by construction) |
| Phase 6 orchestration | `execute_player_pipeline_shift` (`:275`) | Telemetry only (§12) |
| Setup | `GameEngine.__init__` player loop (`core.py:176-209`) | Current Sprint Gray after all seats are built (§9) |
| Round loop | `core._run_round_six_phase` (`core.py:557`) | `sprint_plan.prune_all` at phase ends (§5); telemetry |
| Phase 1 lock | `phase1_roll_deploy` reroll loop (`:472-548`) | Filter locked Gray from `valid_rerolls` (§8) |
| Lock predicate | `sim/engine/vulnerability.py` | New `is_reroll_locked(cfg, die)` |
| Gray table | `sim/entities.py:1841-1892` | `"V047_SPRINT"` profile |
| Breakthroughs | `research_tracks.resolve_breakthrough` (`:305`), `BREAKTHROUGH_TEXT`, `breakthrough_preview` | §10 |
| Bots | `sim/bots/base.py`, `sim/bots/mixed_policy.py`, `sim/bots/research_policy.py` | §11 |
| G3, B3, Y3, Logistics Bounty, Burn Notice | `phase3_income.py` | No logic change (§7); labels + thin-source telemetry |
| Blue Signature Attack | `phase4_attack_resolution._resolve_signature_blue` (`:786`) | No logic change (§7, OQ-1) |
| Purchases | `phase6_operations.py:176, :303` | None (enter Next by construction) |
| Tiebreak | `end_game.py:269-272` | None (counts `glitched + scanned`) |
| Telemetry | `state.RoundTelemetry` (`state.py:1210`), `PlayerState` | §12 |

## 3. Configuration and presets

### 3.1 New / extended `GameConfig` fields

| Field | Type / values | Default (= v0.46) | v047 |
|:--|:--|:--|:--|
| `sprint_plan_enabled` | `bool` | `False` | `True` |
| `starting_current_sprint_gray` | `int >= 0` | `0` | `3` |
| `vuln_face_lock` | `"NONE" \| "GRAY"` (`"ALL"` reserved for the 4668d8 branch; reject for now) | `"NONE"` | `"GRAY"` |
| `gray_face_profile` | adds `"V047_SPRINT"` | (v046: `"V046_VULN"`) | `"V047_SPRINT"` |
| `pen_test_l1` | adds `"SECRET"` (existing `"GRAY_DIE"`, `"SET_ZERO"`) | `"GRAY_DIE"` | `"SECRET"` |
| `pen_test_l1_secrets` | `int >= 0` | `1` | `1` |
| `triage_l1_breakthrough` | adds `"CASH"` (existing `"WHITE_CONTRACTORS"`, `"GRAY_DIE"`) | (v046: `"GRAY_DIE"`) | `"CASH"` |
| `triage_l1_cash` | `int >= 0` | `2` | `2` |
| `release_l1_breakthrough` | `"GRAY_DIE" \| "BANDWIDTH"` | `"GRAY_DIE"` | `"BANDWIDTH"` |
| `release_l1_bandwidth` | `int >= 0` | `1` | `1` |
| `pen_test_l3_breakthrough` | `"SECRET" \| "THIN_GRAY"` | `"SECRET"` | `"THIN_GRAY"` |
| `release_l3_breakthrough` | `"SECRET" \| "THIN_GRAY"` | `"SECRET"` | `"THIN_GRAY"` |
| `bot_research_mode` *(sim-only)* | `"LEGACY" \| "THINNING_AWARE"` | `"LEGACY"` | `"THINNING_AWARE"` in `v047_roster` |
| `bot_thin_tracks` *(sim-only)* | tuple ⊆ `("RELEASE", "DEFENSE")`, ordered | `("RELEASE",)` | `("RELEASE",)` (OQ-3) |
| `bot_thin_gray_floor` *(sim-only)* | `int >= 0` | `3` | `3` |
| `bot_research_rush` *(sim-only, stress)* | `"none" \| "p0" \| "p0half" \| "all"` | `"none"` | `"none"` |

`[TUNE]` comments go on `starting_current_sprint_gray`, `V047_STARTING_SECRETS`, `pen_test_l1_secrets`, `triage_l1_cash`, `release_l1_bandwidth`.
Constant: `V047_STARTING_SECRETS: Dict[int, int] = {2: 6, 3: 6, 4: 6}` beside `V046_STARTING_SECRETS` (`config.py:47`).

### 3.2 Presets

```python
@classmethod
def v047(cls, **overrides) -> "GameConfig":
    """v0.47.0 Sprint Plan & Gray Legacy Rotation (docs/specs/sprint_plan_spec.md). Inherits v046()."""
    for k, v in (
        ("sprint_plan_enabled", True), ("starting_current_sprint_gray", 3),
        ("gray_face_profile", "V047_SPRINT"), ("vuln_face_lock", "GRAY"),
        ("starting_secrets_by_player_count", dict(V047_STARTING_SECRETS)),
        ("pen_test_l1", "SECRET"), ("triage_l1_breakthrough", "CASH"),
        ("release_l1_breakthrough", "BANDWIDTH"),
        ("pen_test_l3_breakthrough", "THIN_GRAY"), ("release_l3_breakthrough", "THIN_GRAY"),
    ):
        overrides.setdefault(k, v)
    return cls.v046(**overrides)

@classmethod
def v047_roster(cls, **overrides) -> "GameConfig":
    overrides.setdefault("bot_pr_push", True)
    overrides.setdefault("bot_pr_push_params", PrPushParams())
    overrides.setdefault("bot_research_mode", "THINNING_AWARE")
    return cls.v047(**overrides)
```

Inherited unchanged from v046: `starting_gray_dice=3` (2 Gray in Ready once the company die replaces one), Triage L3 `SECRET`, Triage L4 free swap, Release L4 set-Gray-face, PR L3 Purple to Sprint Plan, `purchased_dice_to_scanned=True`, Data Scraper `+1` Secret.

### 3.3 Validation (`_validate_v047`, called after `_validate_v046`)

- `_validate_v046`: replace `gray_face_profile != "V046_VULN"` / `== "V046_VULN"` with membership in `V046_GRAY_FACE_PROFILES = ("V046_VULN", "V047_SPRINT")`.
- `sprint_plan_enabled` requires `defense_mode == "VULNERABILITY"`, `round_sequence == SIX_PHASE`, `operations_before_pipeline_shift`, `secret_face_enabled`, `purchased_dice_to_scanned`.
- `starting_current_sprint_gray > 0` requires `sprint_plan_enabled`. Non-bool int `>= 0`.
- `vuln_face_lock in ("NONE", "GRAY")`; `"GRAY"` requires `defense_mode == "VULNERABILITY"`.
- Every mode string is checked against its tuple; every int lever is a non-bool int `>= 0`.
- `THIN_GRAY` on either L3 track, and `release_l1_breakthrough == "BANDWIDTH"`, require `is_v035_tracks`.
- `bot_thin_tracks` ⊆ `("RELEASE", "DEFENSE")`, no duplicates; `bot_research_rush` in its tuple.
- `"V047_SPRINT"` requires `defense_mode == "VULNERABILITY"` (inherits the v046 rule).

## 4. Data model

### 4.1 Gray table `"V047_SPRINT"` (`entities._v047_gray_faces`)

| Face | Name (player-facing) | Payout | ⚠ |
|:--|:--|:--|:--|
| 1 | `+$1 & +1 🔬` | `money=1, patches=1` | 0 |
| 2 | `+2 🔬` | `patches=2` | 0 |
| 3 | `+$2 / +2 🔬 ⚠` | choice `+$2` / `+2 🔬` | **1** |
| 4 | `+$1 / +1 🔬` | choice | 0 |
| 5 | `+$1` | `money=1` | 0 |
| 6 | `+1 🔬` | `patches=1` | 0 |

Same payouts as `V046_VULN`; only the `vuln` on F1 and F2 drops (probe `GRAY=clean2`). Add `"V047_SPRINT"` to `create_gray_die` and to `GRAY_FACE_PROFILES`. `_v046_gray_faces` is untouched.

### 4.2 `PlayerState` additions (plain types so `fast_clone` copies them; initialised in `__init__`)

| Field | Type | Meaning |
|:--|:--|:--|
| `current_sprint_ids` | `Set[int]` | die_ids in the Current Sprint. A die in `scanned_dice` whose id is not in the set is in the **Next Sprint**. Empty and unused when the flag is off. |
| `release_l1_bw_bonus_this_round` | `int` | Part of `temp_release_bandwidth_bonus` that came from Release L1 (telemetry split, §12). Reset with `temp_release_bandwidth_bonus` (`core.py:526`). |
| `sprint_wait_streak` | `Dict[int, int]` | die_id → consecutive Sprint Reviews left behind |
| `sprint_max_streak` | `Dict[str, int]` | `{"gray": 0, "colored": 0}` |
| `sprint_wait_hist` | `Dict[str, List[int]]` | per class, 5 buckets (`0,1,2,3,4+` waits at graduation) |
| `gray_removed_by_source` | `Dict[str, int]` | `PEN_TEST_L3`, `RELEASE_L3`, `TRIAGE_L4`, `BURN_NOTICE` |
| `thin_rounds` | `List[int]` | round of each L3 thinning (first / second thin stats) |
| `thin_forfeits` | `int` | L3 thinning with no Gray owned |
| `gray_lock_blocked` | `int` | reroll requests dropped by the Gray lock |

None of these keys may enter `_snapshot_players()` (`core.py:387`) or `rankings` (`end_game.py`) when the flag is off (they are not added to those dicts at all; sweep scripts read them from `PlayerState`).

### 4.3 `RoundTelemetry` additions (`state.py:1210`; populated only when `sprint_plan_enabled`; default empty dicts)

`sprint_current_by_player`, `sprint_next_by_player` (sizes at Sprint Review start, after Production Return), `sprint_current_over_bw_by_player` (bool), `sprint_grad_current_by_player`, `sprint_grad_next_by_player`, `sprint_left_by_player`, `sprint_prod_to_current_by_player` (bool), `gray_owned_by_player`, `gray_ready_by_player` (both after Sprint Review), `gray_rolled_by_player`, `colored_rolled_by_player`, `gray_vuln_kept_by_player`, `colored_vuln_kept_by_player`, `release_l1_bandwidth_graduates`.

## 5. New module `sim/engine/sprint_plan.py` (pure helpers, no RNG)

```python
def enabled(cfg) -> bool                       # cfg.sprint_plan_enabled
def current_sprint(p) -> List[Die]             # [d for d in p.scanned_dice if d.die_id in p.current_sprint_ids], list order
def next_sprint(p) -> List[Die]                # the rest of p.scanned_dice, list order
def prune(p) -> None                           # p.current_sprint_ids &= {d.die_id for d in p.scanned_dice}
def prune_all(state) -> None                   # prune every player
def mark_current(p, dice) -> None              # add ids
def reset_after_review(p) -> None              # p.current_sprint_ids = {d.die_id for d in p.scanned_dice}
def forced_count(p) -> int                     # min(len(current_sprint(p)), p.effective_release_bandwidth)
def owned_gray(p) -> List[Tuple[str, Die]]     # (zone, die) over R&D, Sprint Plan, In Production, Ready
def check_picks(p, cur_ids, next_ids) -> List[str]   # error strings for the web (empty = legal); §6.2 rules
```

**Why prune.** Removal paths (G3, Blue Signature Attack, Triage L4, Burn Notice, corruption returns, thinning) do not touch `current_sprint_ids`. `current_sprint()` filters by membership, so a stale id is harmless until the same die re-enters `scanned_dice` before the next `reset_after_review`. No current path does this, but `prune` makes it impossible:
- `_run_round_six_phase` calls `sprint_plan.prune_all(state)` at the end of Phases 2, 3, 4 and 5 when the flag is on.
- `thin_gray` (§10.3) and `_resolve_triage_replacement` call `prune(p)` on the owner.

## 6. Phase 6: Production Return and Sprint Review

Order is unchanged: Splice / Hotfix bypass → Production Return → Sprint Review → Triage → Triage L4 pay.

### 6.1 Production Return (`production_return_to_scanned`)

Flag on: before moving, `prune(p)`; `was_empty = not current_sprint(p)`. Move dice as today. If `was_empty`, `mark_current(p, moved)`. Otherwise all `moved` dice are Next. Existing Next dice stay Next either way. Record `sprint_prod_to_current_by_player`.
The web path (`web/controller/phase6_pipeline_actions.py:82`, `production_already_returned=True`) calls the same function, so it inherits the rule.

### 6.2 Sprint Review (`graduate_scanned`, flag on → `sprint_plan.sprint_review(engine, p, chosen_die_ids)`)

```
bw     = p.effective_release_bandwidth          # includes Jumper Diagnostics and Release L1 bonus
cur    = current_sprint(p); nxt = next_sprint(p)
forced = min(len(cur), bw)
spare  = bw - forced                             # > 0 only when len(cur) < bw
if chosen_die_ids is None: cur_ids, next_ids = bot.choose_sprint_graduates(p, cur, nxt, bw, state, rng)
else:                      split chosen_die_ids by membership (cur first, then nxt; list order kept)
cur_pick  = validate(cur_ids, pool=cur, n=forced, backfill=True)    # forced: back-filled by default priority
next_pick = validate(next_ids, pool=nxt, n=spare, backfill=False)   # optional: never back-filled (OQ-1 precedent)
graduates = cur_pick + next_pick                 # Ready order: Current picks, then Next picks
move each graduate scanned -> Ready (reset_die_for_pipeline)
update streaks / histograms (§12); reset_after_review(p)
```

- `validate` = `validate_graduate_ids` semantics restricted to `pool`: dedupe, ignore unknown ids and ids from the other sprint, cap at `n`.
- `use_bot_choice=False` (legacy v0.33 FIFO path, `:363`) is unreachable under the flag (validation forbids non-six-phase); assert it.
- `max_graduates(p)` keeps returning `min(|scanned|, bw)` (an upper bound; used by the web).
- `held_in_scanned` stays `len(scanned_dice)` after Sprint Review.

### 6.3 Default bot hook

`BaseBot.choose_sprint_graduates(player, current, next_, bw, game_state=None, rng=None) -> Tuple[List[int], List[int]]`:
- `cur_ids` = `default_graduate_priority(current)[:min(len(current), bw)]`;
- `next_ids` = `default_graduate_priority(next_)[:bw - len(cur_ids)]`. Bots always fill spare bandwidth, as in the probe.
- Priority = `default_graduate_priority` (Purple > colored by descending cost > Gray; ties by die_id).
- Register the hook in `mixed_policy.py` beside `"choose_scanned_graduates": "misc"`.

## 7. Entry and removal paths (no logic change unless stated)

| Path | Where | Sprint effect |
|:--|:--|:--|
| Production Return | §6.1 | Current if Current empty, else Next |
| Triage R&D → Sprint Plan | `conveyor_triage_v038` | Next (runs after `reset_after_review`) |
| B3 *Air-Gapped Backup* | `phase3_income.py:316-324` | Next |
| Y3 *Proprietary Training* (`dice_to_scan`) | `phase3_income.py:401-405` | Next |
| Purchases, Prometheus discount | `phase6_operations.py:176, :303` | Next |
| PR L3 2nd Purple | `research_tracks.py:376` | Next |
| Blue Signature Gray (R&D, later Triage) | `phase4:786` → Triage | Next |
| G3 *Live Reboot* | `phase3_income.py:286-295` | Takes from either sprint (bot hook sees all `scanned_dice`); no change |
| Blue Signature Attack source | `phase4:791` | Either sprint; first Gray in `scanned_dice` list order, else In Production, else Ready (unchanged; OQ-1) |
| Triage L4 swap | `_resolve_triage_replacement` | Either sprint (`_gray_dice_by_zone`); new colored die → Ready; add `prune(p)` |
| Burn Notice | `resolve_spook_burn_notice` | Any zone; count `gray_removed_by_source["BURN_NOTICE"]` |
| Corruption "return colored dice" | Phase 2 | May empty Current; consistent |
| Logistics Bounty | `phase3_income.py:183, 395, 455, 466` | Counts distinct colors over the whole `scanned_dice` = whole Sprint Plan; no change |
| Tiebreak "fewest dice Under Development" | `end_game.py:269-272` | `glitched + scanned` = R&D + both sprints; no change |

## 8. Phase 1: Gray ⚠ lock

- **Predicate** (`vulnerability.is_reroll_locked(cfg, die)`): `cfg.vuln_face_lock == "GRAY" and die.color == GRAY and die.current_face is not None and face_vuln(die.current_face) > 0`. It does **not** set `die.is_locked`. Bots read `is_locked` to decide Helix use (`accelerationist.py:70` and others), and the probe did not change that decision.
- **Where:** in the reroll loop, after `vulnerability_policy.adjust_rerolls` (`:495`) and only in the **non-Helix** branch of the `valid_rerolls` filter (`:505-508`), drop indices with `is_reroll_locked`. Add the dropped count to `player.gray_lock_blocked`. The effect matches the probe's post-filter on `adjust_rerolls`: if nothing is left, the loop `break`s as today.
- **"After any roll":** the predicate is re-read each iteration, so it covers the initial roll and every reroll.
- **Exemptions:**
  - Helix *Brute-Force Bypass* (`helix_active`): no lock filter.
  - Prodigy ACE (`:550-572`), the Helix face override (`:574-597`) and Release L4 set-Gray-face (`:600`) run after rerolls and may still change a locked face.
- **Colored dice are never filtered.**
- **Keep-rate telemetry** (`:509-528`): under the lock, skip locked Gray dice when counting `_ev` (no choice was offered). Flag-off code is unchanged.
- **Roll telemetry** in `vulnerability.lock_in` (flag on): count Gray / colored dice rolled and the ⚠ kept per class into the `RoundTelemetry` fields (§4.3). This mirrors probe `lock()`.

## 9. Setup

- The player loop is unchanged: 2 Gray + company die + Purple in Ready (`starting_gray_dice=3` minus the company die).
- **After all seats are built** and `state.next_die_id` is set: for each player in seat order, create `starting_current_sprint_gray` Gray dice with `research_tracks._new_die_id(engine)` and `cfg.gray_face_profile`, append them to `scanned_dice` and `mark_current`. Seat order and post-setup ids mirror the probe, so die-id tie-breaks match it.
- Starting Secrets come from `starting_secrets_by_player_count` (6), plus the Data Scraper `+1` (`core.py:165-168`, unchanged).
- Round 1 Sprint Review: Current = 3 Gray, so Round 1 Production Return goes to Next. The forced 3 Gray graduate first; spare bandwidth takes Next (bot priority puts Purple first).

## 10. Breakthroughs (`research_tracks.resolve_breakthrough`)

### 10.1 Branch order (flag-off paths must be byte-identical)

Insert the new branches **before** the existing shared `("DEFENSE", "RELEASE") and level == 1` / `level == 3` branches. Each new branch is keyed on its own mode, so the old branches still catch the `GRAY_DIE` / `SECRET` defaults:

| Track, level | Mode | Effect | `rec.detail` |
|:--|:--|:--|:--|
| DEFENSE 1 | `pen_test_l1 == "SECRET"` | `gain_secrets(pen_test_l1_secrets, "breakthrough")` | `{"secrets": n}` |
| TRIAGE 1 | `triage_l1_breakthrough == "CASH"` | `money += triage_l1_cash` | `{"money": n}` |
| RELEASE 1 | `release_l1_breakthrough == "BANDWIDTH"` | `temp_release_bandwidth_bonus += n`; `release_l1_bw_bonus_this_round += n` | `{"release_bandwidth_this_round": n}` |
| DEFENSE 3 | `pen_test_l3_breakthrough == "THIN_GRAY"` | `thin_gray(engine, p, "PEN_TEST_L3", choice)` | `{"gray_die_id": id, "zone": z}` or FORFEITED `{"reason": "no_gray_die"}` |
| RELEASE 3 | `release_l3_breakthrough == "THIN_GRAY"` | `thin_gray(engine, p, "RELEASE_L3", choice)` | same |

- No v047 Breakthrough creates a die: `state.next_die_id` is unchanged by any L1 / L3 resolution.
- The Pen Test L3 "Blue R&D faces yield +3" property stays level-based (`secret_faces.py:56`, `defense_level >= 3`) and needs no change.
- The Release L1 bonus applies to the same round's Sprint Review, because Phase 5 Operations runs before Phase 6. It is cleared at round end with the Jumper bonus (`core.py:526`).

### 10.2 Text (`BREAKTHROUGH_TEXT` / `breakthrough_preview`)

Make the text config-aware for the new modes:
- Pen Test L1 "Gain 1 Corporate Secret".
- Triage L1 "Gain $2".
- Release L1 "+1 Release Bandwidth this round".
- Pen Test L3 "Return 1 Gray Legacy die you own to the box; Blue R&D faces yield +3".
- Release L3 "Return 1 Gray Legacy die you own to the box".

Flag-off text is unchanged.

### 10.3 `thin_gray(engine, p, source, choice=None) -> Optional[Die]`

- **Candidates** = `sprint_plan.owned_gray(p)`, in the default order **R&D → Next Sprint → In Production → Current Sprint → Ready**, in list order within each zone (the probe's `thin()` order).
- **Choice:** the bot hook `choose_thin_gray(player, state, candidates) -> Optional[int]` picks a die_id. An invalid choice or `None` falls back to the first candidate. The effect is mandatory, so the player must return a die when they own one.
- **Removal:**
  - Remove the die from its zone. If the zone is R&D, call `secret_faces.lose_pending(p, die)`.
  - The die goes to the box: it does not return to the Central Market and gives no cash.
  - Then `prune(p)`, `gray_removed_by_source[source] += 1`, `thin_rounds.append(round)`.
- **No Gray owned:** `rec.outcome = "FORFEITED"`, `thin_forfeits += 1`.
- Also count Triage L4 swaps (`TRIAGE_L4`) and Burn Notice (`BURN_NOTICE`) into `gray_removed_by_source` when the flag is on.

## 11. Bots

### 11.1 Hooks (`sim/bots/base.py`)

- `choose_sprint_graduates` (§6.3).
- `choose_thin_gray` (default: first candidate).
- Map both in `mixed_policy.py` as `"misc"`.

### 11.2 Research-focus fix (`research_policy._plan_research_share_regain`, MONEY branch; the RESEARCH branch is untouched)

`bot_research_mode == "LEGACY"` is today's code. The legacy Triage-to-L2 injection (`:117-119`) is the "Triage-first default" that §9.4 identified as the reason the rush stress bot dominated.

`"THINNING_AWARE"` builds `want_order` as follows (all later steps unchanged: PR-L4 push `:120-128`, the `max_ups` cap, save-toward-the-first-unaffordable-step):

```
g = len(sprint_plan.owned_gray(player))
head = []
if lv["TRIAGE"] < 1: head += ["TRIAGE"]                       # Triage L1 (+$2), 1 🔬
for t in config.bot_thin_tracks:                              # default ("RELEASE",)
    if lv[t] < 3 and (g >= config.bot_thin_gray_floor or (t == "RELEASE" and lv[t] < 2)):
        head += [t] * (3 - lv[t])                             # push to the L3 thinning (Release L2 = BW 5)
rest = _want_list(policy, lv)                                  # bot's archetype focus list
if triage_l4_free_die_replacement and lv["TRIAGE"] < 2:        # legacy injection now AFTER the head
    rest = ["TRIAGE"] * (2 - lv["TRIAGE"]) + [x for x in rest if x != "TRIAGE" or lv["TRIAGE"] >= 2]
want_order = merge(head, rest)    # concatenate, then drop entries that would push a track past L4 or that
                                  # repeat steps already counted (count per track against 4 - lv[t])
```

- `merge` must be deterministic and must not reorder `rest`.
- With the flag off, or in `"LEGACY"` mode, the code path is the existing one, verbatim.

### 11.3 Rush stress policy (`bot_research_rush`, sim-only)

Mirror probe `sr()`. At the top of `_plan_research_share_regain`, when the seat rushes:
- `need = RELEASE×(3−lv) + DEFENSE×(3−lv)`, in that order;
- buy in order while affordable, up to `max_hardware_upgrades_per_turn`, stopping at the first unaffordable step;
- return `(ups, 0, 0)`.

Which seats rush:
- `"all"`: every seat.
- `"p0"`: `player_id == 0`.
- `"p0half"`: seat 0 when `hash((state.rush_seed, state.current_round)) & 1`. Int-tuple hashing is deterministic. `GameState.rush_seed: int = 0` is set by the sweep runner to the game seed; it draws no RNG.

The rush runs in either `bot_research_mode`.

## 12. Telemetry (flag on only)

| Need | Source |
|:--|:--|
| Gray roll share | Σ `gray_ready_by_player` / Σ `gray_owned_by_player` (after Sprint Review; probe definition) |
| Owned Gray by round | `gray_owned_by_player` per round |
| Current / Next sizes, Current > BW | `sprint_current_*`, `sprint_next_by_player`, `sprint_current_over_bw_by_player` |
| Graduates by sprint, left behind | `sprint_grad_current/next_by_player`, `sprint_left_by_player` |
| Stranding streaks | `sprint_max_streak` (max per class), `sprint_wait_hist` (probe: pop the streak on graduation into the bucket; +1 for every die left; drop the ids that left the Sprint Plan) |
| Thinning by source, first / second thin round, forfeits | `gray_removed_by_source`, `thin_rounds`, `thin_forfeits` |
| Early cash / 🔬 | existing `income_by_player` (R1–4 sums; no new field) |
| Gray vs colored rolled / ⚠ kept; lock blocks | §8 roll telemetry, `gray_lock_blocked` |
| Phreaker split | `phreaker_bandwidth_graduates` (`core.py:617-621`): under the flag subtract `release_l1_bw_bonus_this_round` from the bonus attribution; Release L1 graduates beyond `release_bandwidth + Jumper bonus` go to `release_l1_bandwidth_graduates` |
| Burn Notice | `spook_gray_dice_burned` is already wired (`core.py:593`); TC-SP-27 pins it |
| Secrets ledger | existing `secrets_by_source`; sweep summary adds the seat-level aggregate |

## 13. Naming map (sim identifier → user-facing text when `sprint_plan_enabled`)

| Sim identifier (unchanged) | User-facing |
|:--|:--|
| `scanned_dice` | Sprint Plan |
| `current_sprint_ids` members / others | Current Sprint / Next Sprint |
| `glitched_dice` | Research & Development (R&D) |
| `Face.secrets_pending` face, "Secret face" | R&D face |
| `graduate_scanned`, "Scanned Graduation" | Sprint Review |
| `production_return_to_scanned` | Production Return (to the Sprint Plan) |
| `conveyor_triage_v038` | Triage (R&D → Next Sprint) |
| `held_in_scanned`, `scanned_held_by_player` | dice left in the Sprint Plan |
| `purchased_dice_to_scanned`, `pr_l3_purple_to_scanned` | "… to the Next Sprint" |
| B2 variant name "Deep R&D Vault" | Deep Data Vault |
| "Terminal Hardware & R&D Upgrade Tracks" | Terminal Hardware Tracks |
| `"DEFENSE"`, `"PATENT"` track keys | Pen Test Track, Public Relations Track (unchanged) |

- **Mechanism:** a new `sim/engine/terms.py` with `label(cfg, key) -> str` and `display_face_name(cfg, name) -> str`.
- **No entity data changes:** die tables and variant names in `entities.py` stay as they are, because face names reach parity-digested snapshots. The rename is applied at display / log time only.
- **Docstrings and comments** may keep the legacy words, but must not add any deprecated term.

## 14. Invariants

| ID | Statement |
|:--|:--|
| INV-SP-01 | After Sprint Review, `current_sprint_ids == {ids in scanned_dice}`. With the flag off, `current_sprint_ids` is always empty. |
| INV-SP-02 | Production Return marks the returned dice Current **iff** the pruned Current Sprint was empty before the step; otherwise every returned die is Next and existing Current membership is unchanged. |
| INV-SP-03 | Current graduates are exactly `min(|Current|, effective BW)`, whatever the hook returns (forced, back-filled). |
| INV-SP-04 | Next graduates appear only when `|Current| < BW`, number at most `BW − |Current|`, and are never back-filled. Total graduates ≤ effective BW. |
| INV-SP-05 | Every non-Production entry (Triage, B3, Y3, purchase, Prometheus, PR L3, Blue Signature via Triage) lands in the Next Sprint. |
| INV-SP-06 | At the end of Phases 2–6, `current_sprint_ids ⊆ {ids in scanned_dice}`. |
| INV-SP-07 | Sprint Review only moves dice Sprint Plan → Ready. The die count over all zones is conserved, and the Ready order is Current picks, then Next picks. |
| INV-SP-08 | Effective BW at Sprint Review = `release_bandwidth + Jumper bonus + Release L1 bonus`, and the bonuses are zero at the start of every round. |
| INV-SP-09 | With `vuln_face_lock="GRAY"` and Helix inactive, no Gray die whose current face has ⚠ is rerolled. Colored dice are never filtered. `is_locked` is never set by the Gray lock. |
| INV-SP-10 | Helix active ⇒ no lock filter. Prodigy ACE, the Helix face override and Release L4 may set a Gray face whether or not it is locked. |
| INV-SP-11 | `V047_SPRINT`: Σ vuln = 1 (Face 3); payouts equal `V046_VULN` face for face. |
| INV-SP-12 | v047 setup: Ready = 2 Gray + company die + Purple; Current = 3 Gray; Next empty; owned Gray = 5; Secrets = 6 (+1 under Data Scraper). |
| INV-SP-13 | `thin_gray` removes exactly one owned Gray (not returned to the market, no payout), prunes Current, calls `lose_pending` for R&D. With no Gray owned it is FORFEITED and the state is unchanged. |
| INV-SP-14 | Under v047, no Breakthrough changes `state.next_die_id`; L1 rewards are exactly +1 Secret / +$2 / +1 BW this round. |
| INV-SP-15 | Blue R&D-face yield bonus at `defense_level >= 3` is unchanged by `pen_test_l3_breakthrough`. |
| INV-SP-16 | Flag-off presets (v035 fixtures, v045 golden, new v046 golden) are bit-identical. |
| INV-SP-17 | Tiebreak "fewest dice Under Development" = `|R&D| + |Sprint Plan|`. Logistics Bounty counts distinct colors over the whole Sprint Plan. |
| INV-SP-18 | `fast_clone` round-trips `current_sprint_ids` as an independent set, so a mutation on the clone does not affect the source. |
| INV-SP-19 | Rush policy is inactive when `bot_research_rush="none"`, respects `max_hardware_upgrades_per_turn`, saves toward the first unaffordable step, and draws no RNG. |
| INV-SP-20 | No new key appears in `_snapshot_players()` or `rankings` when the flag is off. |

Add INV-SP-01/03/04/06/07/09 to the sweep `--assert-invariants` wrapper (pattern: `run_v046_sweep.install_invariant_checks`).

## 15. Unit tests (`tests/test_v470_sprint_plan.py`; run `python3 -m pytest -q`)

| ID | Case |
|:--|:--|
| TC-SP-01 | Config: `v047()` field values; `v046()` leaves every new field at its default; the validation errors of §3.3 (one per rule). |
| TC-SP-02 | `V047_SPRINT` table: names, payouts, vuln per face (INV-SP-11). |
| TC-SP-03 | Setup (2P/3P/4P, with / without Data Scraper): INV-SP-12; the 3 Gray ids are post-setup and in seat order. |
| TC-SP-04 | Production Return with Current empty → all Current; Next keeps its dice (INV-SP-02). |
| TC-SP-05 | Production Return with Current non-empty → all Next. |
| TC-SP-06 | Sprint Review `|Cur| < BW`: forced Cur + Next fill by priority; Ready order Cur then Next (INV-SP-03/04/07). |
| TC-SP-07 | `|Cur| == BW`: no Next graduates even if the hook asks. |
| TC-SP-08 | `|Cur| > BW`: hook chooses which Current dice; leftover Current + all Next become Current (INV-SP-01). |
| TC-SP-09 | Hook returns short / invalid / cross-sprint / duplicate ids: Current back-filled to forced; Next never back-filled. |
| TC-SP-10 | Explicit `chosen_die_ids` (web path) split by membership; `check_picks` reports illegal Next picks when `|Cur| >= BW` and unknown ids. |
| TC-SP-11 | Jumper bonus and Release L1 bonus raise the forced cap (INV-SP-08); both are reset next round. |
| TC-SP-12 | Entry paths land in Next (parametrized: Triage, B3, Y3, purchase, Prometheus, PR L3, Blue Signature → Triage) (INV-SP-05). |
| TC-SP-13 | Removal paths then prune: G3 on a Current die, Blue Signature on a Current Gray, Triage L4 on a Current Gray, Burn Notice, corruption return; INV-SP-06 holds at the phase end. A G3-emptied Current means the Phase 6 Production Return goes to Current. |
| TC-SP-14 | Stale-id guard: remove a Current die, re-insert it via Triage before review; it is Next. |
| TC-SP-15 | Gray lock: a Gray on F3 requested for reroll is dropped; a colored ⚠ die is rerolled; `gray_lock_blocked` increments; the loop breaks when nothing is left (INV-SP-09). |
| TC-SP-16 | Lock exemptions: Helix active rerolls the locked Gray; Release L4 sets a locked Gray to F1; Prodigy override still applies (INV-SP-10). `is_locked` is untouched, so a Helix bot's `choose_helix_override` input is unchanged. |
| TC-SP-17 | Lock after the initial roll and after a reroll that lands on F3. |
| TC-SP-18 | Pen Test L1 SECRET +1 (`secrets_by_source["breakthrough"]`); Triage L1 CASH +$2; Release L1 +1 BW this round only (INV-SP-14). |
| TC-SP-19 | L3 THIN on each track: default zone order R&D → Next → In Production → Current → Ready; hook choice respected; invalid choice → default; pending loss in R&D (INV-SP-13). |
| TC-SP-20 | L3 THIN with no Gray → FORFEITED, `thin_forfeits` = 1, no Secret gained. |
| TC-SP-21 | Pen Test L3 THIN keeps the Blue +3 yield (INV-SP-15). |
| TC-SP-22 | Once-only: re-reaching L3 (clone / re-entry) does not thin twice (existing INV-RT-BT-ONCE-01). |
| TC-SP-23 | Tiebreak counts both sprints; Logistics Bounty counts both sprints (INV-SP-17). |
| TC-SP-24 | `fast_clone` round-trip of `current_sprint_ids` and the new dicts (INV-SP-18); `resume_round` mid-Phase 5 gives the same Sprint Review as the original. |
| TC-SP-25 | THINNING_AWARE want-list: Triage L1 first; Release pushed to L3; legacy Triage-to-L2 after the head; LEGACY mode identical to today (golden list for 3 seeded states). |
| TC-SP-26 | Rush: `p0` only seat 0; `p0half` deterministic for a fixed `rush_seed`; cap and save behaviour (INV-SP-19). |
| TC-SP-27 | Telemetry: one v047 3P game populates every §4.3 field each round; `spook_gray_dice_burned` > 0 in a forced-Spook game; streak histogram sums equal graduations. |
| TC-SP-28 | Snapshot / ranking keys under v046 are identical to before (INV-SP-20). |
| TC-SP-29 | Smoke: 50 games each of v047 / v047_roster at 2P/3P/4P finish with every invariant asserted. |

## 16. Parity plan

### 16.1 Bit-identity (INV-SP-16)

1. **Before any engine edit**, capture `tests/parity_v046/{__init__.py, capture.py, golden.json}`. Copy `tests/parity_v045/capture.py` with `CONFIGS = ("v046", "v046_roster")`, seeds 42..141, 2/3/4P. Commit it alone.
2. Add `tests/test_v470_parity.py`, asserting the v046 golden. Keep `tests/test_v460_parity.py` (v045 golden) and the v035 fixture tests green.
3. Guarding rules:
   - Every new branch tests its own lever.
   - Flag-off code paths are not refactored, only wrapped.
   - No RNG draw is added anywhere: thinning, prune, the hooks' defaults and the rush coin draw none.
   - No new snapshot or ranking keys.
   - New `PlayerState` fields are initialised but not read when the flag is off.
4. Full suite: `python3 -m pytest -q` (WSL).

### 16.2 Probe reproduction (S1 vs probe QC; tolerance ±0.10 rounds, ±2 pp end shares, ±0.03 income ratio)

Expected values, Δ against v0.46:
- rounds −0.14 / +0.14 / +0.10;
- Singularity 71 / 84 / 77% of v0.46;
- income ×1.17 of v0.45;
- Green lost 1.97 / 1.73 / 1.55;
- 4P PZ + Collapse 87.7;
- Gray roll share (3P) 49%;
- seat-0 rush Δ win +5.5 / +8.4 / +6.7 pp.

Small drift is expected: the probe minted (then popped) L1 Gray dice, which advanced `next_die_id`. A miss beyond tolerance blocks S2 until it is explained.

## 17. Sweep arms (product-owner)

**Protocol:**
- New `scripts/run_v047_sweep.py`, modelled on `run_v046_sweep.py`: `--arm`, `--players 2,3,4`, `--games 1200`, `--seed0 42`, `--assert-invariants`, quiet by default.
- 1,200 games per pod; seeds `42..1241`; `mixed1` roster.
- Every arm is paired against S0 on the same seeds. The script prints only summary tables.

| Arm | Config | Purpose |
|:--|:--|:--|
| S0 | `v046_roster` | Control |
| S1 | `v047_roster` + `bot_research_mode="LEGACY"` | Probe QC reproduction (§16.2) |
| **S2** | `v047_roster` | **Candidate** (thinning-aware bots, `bot_thin_tracks=("RELEASE",)`) |
| S2b | S2 + `bot_thin_tracks=("RELEASE","DEFENSE")` | OQ-3 alternative |
| S3 | `v046_roster` + `bot_research_mode="THINNING_AWARE"` | How much of the v0.46 rush gap was a bot gap (informative) |
| R0 | S1 + `bot_research_rush="p0"` | Reproduce the probe rush edge |
| R1 | S2 + `bot_research_rush="p0"` | Rush stress (seat 0 vs S2 seat 0, paired) |
| R2 | S2 + `"p0half"` | Mixed rusher |
| R3 | S2 + `"all"` | All-rush pacing and income |

**Guardrails on S2** (and S2b if chosen):

| Metric | Bar |
|:--|:--|
| Δ mean rounds vs S0 | within ±0.30 at each count |
| Singularity share | report; ≥ 60% of S0 (QC 71–84%) |
| Income ×v0.45 (method b, not only the proxy) | ≤ 1.25 |
| Green Secrets lost per seat | 1.2–2.5 |
| 4P PZ + Collapse | ≤ 95.5% |
| Total Wipeout | ≤ 15 / 5 / 2% |
| Dead turns (Phase 3 $+🔬 ≤ 1) | ≤ S0 (2.3%) |
| Gray roll share | ≥ 45% (OQ-5) |
| Longest stranding run | ≤ 8 (Gray), ≤ 4 (colored) |
| White Hat spread | ≤ 12 pp |
| Rush edge (R1 seat 0 − S2 seat 0) | ≤ +4 pp at each count (QC LEGACY: +5.5 / +8.4 / +6.7) |
| Earliest thin | never before Round 2 Phase 5 |

**Also report:**
- per-card split;
- Spook and Operator win rates (watch: 2P Spook +6 pp in the probe);
- Secret faces per round R1–8 (Round 2 dip);
- thinning by source;
- owned Gray R1→R8.

**Then:**
- the dominance matrix (KeepAll / RerollAllVuln / PenTestRush against Adaptive, 600 per cell) and ref1 under the D5 bar, on the chosen arm;
- a joint arm with the colored-lock branch once it lands.

## 18. Files touched

- **New:** `sim/engine/sprint_plan.py`, `sim/engine/terms.py`, `scripts/run_v047_sweep.py`, `tests/parity_v046/{__init__.py,capture.py,golden.json}`, `tests/test_v470_parity.py`, `tests/test_v470_sprint_plan.py`.
- **Edited:**
  - `sim/config.py` (fields, constant, presets, validation);
  - `sim/entities.py` (`V047_SPRINT`);
  - `sim/engine/state.py` (`PlayerState`, `RoundTelemetry`, `GameState.rush_seed`);
  - `sim/engine/core.py` (setup, prune calls, telemetry, Phreaker split);
  - `sim/engine/phase5_pipeline_shift.py`;
  - `sim/engine/phase1_roll_deploy.py`;
  - `sim/engine/vulnerability.py` (predicate, lock-in telemetry);
  - `sim/engine/research_tracks.py`;
  - `sim/engine/phase3_income.py` (labels, Burn Notice source count);
  - `sim/bots/base.py`, `sim/bots/mixed_policy.py`, `sim/bots/research_policy.py`.
- **Not touched:** `phase4_attack_resolution.py`, `phase6_operations.py`, `end_game.py` (behaviour already correct; covered by tests).

## 19. Open questions (resolved at defaults; marked for the reviewer / game-designer)

1. **OQ-1 Blue Signature Gray source.** Default = first Gray in `scanned_dice` list order, either sprint (unchanged; mirrors the probe). The rules text says "your choice". A `choose_signature_blue_gray` hook is deferred to the web follow-up. *Resolved: default.*
2. **OQ-2 Thinning target.** Mandatory. The bot hook defaults to the probe order (R&D first). *Resolved.*
3. **OQ-3 `bot_thin_tracks`.** Default `("RELEASE",)` keeps the archetype identity; S2b tests `("RELEASE","DEFENSE")`. The game-designer picks after the sweep. *Open, default set.*
4. **OQ-4 Optional Next fill.** Bots always fill spare bandwidth (as in the probe); humans may decline (engine allows a short Next list). *Resolved.*
5. **OQ-5 Gray roll share guardrail.** §6.3 said ≥ 50%, but QC measured 49% (3P). Proposed bar ≥ 45%. *Game-designer to confirm.*
6. **OQ-6 Release L1 bonus.** Uses `temp_release_bandwidth_bonus`, so it stacks with Jumper. *Resolved.*
7. **OQ-7 Labels.** The rename is display-only via `terms.py`; the entity face / variant names are unchanged for parity. *Resolved.*
8. **Not implemented** (reserved, need User approval to add): the stranding backup rule, the `STRICT` reading, the Round 2 company-die priority, `vuln_face_lock="ALL"`, and the Gray F3 `+$1 / +2 🔬` income lever.
9. **Web follow-up (separate):**
   - two Sprint drop zones;
   - forced-pick UI, with a 400 error from `check_picks`;
   - the Phase 1 lock rejection for Gray ⚠ rerolls;
   - a thinning picker;
   - the v047 labels.
