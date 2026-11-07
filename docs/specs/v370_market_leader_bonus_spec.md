# Technical Architecture Specification: Phase 46 (v0.37.0)
## Market Leader Bonus: End-Game Corporate Secrets by Market Share Placement

**Author:** Principal Engineer / Architect
**Status:** Draft for implementation. The open questions in §14 need an answer, or acceptance of the recommended default, before the `senior-engineer` starts.
**Target Version:** `v0.37.0` candidate
**Source of Truth:** `FINDINGS.md` §38 (design package and implementation plan, User sign-off 2026-11-07); `PLAN.md` Phase 46. Evidence: the probe `scripts/explore_v360_share_placement_probe.py` (hooks only). Its `exp_bonus`, `mbv` and `ur` functions are the **reference behaviour** for the bot valuation in §5. Nothing else in the probe is a reference implementation.
**Dependencies:** `RULES.md` v0.36.0 (§3 Setup, §5 End Game & Victory Scoring, §7 Glossary); [v360 spec](./v360_market_share_red_rework_spec.md) (INV-MS-*, tiebreakers, Market Share bot policy).
**Target Components:**
- `sim/config.py`, `sim/engine/market_share.py`, `sim/engine/end_game.py`, `sim/engine/state.py` (`EndGameResult`, `PlayerState` telemetry counters), `sim/engine/phase4_attack_resolution.py` (telemetry counters only)
- `sim/bots/market_share_policy.py`
- New: `tests/fixtures/v036_parity/`, `tests/test_v370_market_leader_bonus.py`, `scripts/run_v370_market_leader_bonus_sweep.py`
- Phase B, after balance sign-off: `RULES.md`, `web/`, `pnp/`, `CLAUDE.md`, `GameConfig()` default

> Line numbers are from HEAD `e1039ae`. The working tree differs from HEAD only in `FINDINGS.md`, `PLAN.md`, the untracked probe and `sim_results/`; `git diff HEAD -- sim tests` is empty.

---

## 1. Executive Summary

### 1.1 What changes (all behind levers; `GameConfig()` and `GameConfig.v036()` stay v0.36.0)

| # | Change | §38 ref |
|---|---|---|
| C1 | **Market Leader Bonus.** At game end (Singularity, or the end of a Final Round from Patient Zero or Market Collapse), and before Corporate Secrets are compared, surviving players are placed by final **Market Share** and gain bonus Corporate Secrets by place. | Plan 2 |
| C2 | Schedule `[TUNE]`, per player count: **2P** 1st +2, 2nd 0. **3P** 1st +2, 2nd +1, 3rd 0. **4P** 1st +2, 2nd +1, 3rd 0, 4th 0. | Package |
| C3 | **Ties share the better place** (competition ranking: two tied for 1st both gain +2, and the next player is 3rd). No further tiebreakers for the bonus. | Finding 1 |
| C4 | **Survivors only.** Patient Zeros gain nothing and take no place. A sole survivor gains the 1st-place bonus. **No bonus on a Total Wipeout** (ranking unchanged). | Findings 2, package |
| C5 | A player at `0` Market Share after a Market Collapse scores normally and is placed by Market Share like anyone else. | Plan 2 |
| C6 | Then the normal ranking: Corporate Secrets (now including the bonus), then the **Hierarchical Tiebreakers** (Market Share > Money > Active Colored Module Dice in Ready for Release > Research Tokens > fewest dice Under Development > shared). Unchanged. | Package |
| C7 | Starting Corporate Secrets **9 / 8 / 9** (2P / 3P / 4P) `[TUNE]` under `v037()` (v0.36: 7 / 7 / 8). | Finding 7, package |
| C8 | Bonus-aware bot valuation `[TUNE-BOT]` in `marginal_block_value` (Red) and `urgent_regain`, active only when the bonus is enabled. | Plan 3 |
| C9 | Telemetry: per player Secrets before the bonus, the bonus, Market Share place; per game whether the bonus changed the winner and whether a paid place was tied; Generic shield and contested-round counters for the Blue agency watch items. | Plan 3, watch items |

**Not ported from the probe:** the Red purchase nudge (`amsp`, the `deep=True` branch) and the Public Relations Track focus changes (`pr_focus`). §38 finding 5 shows neither helps. The standard-tiebreaker tie mode (`ties="std"`) and all-player placement (`pool="all"`) are also not ported (§14 OQ-2).

### 1.2 Comparison v0.36.0 vs v0.37.0

| Item | v0.36.0 | v0.37.0 candidate |
|---|---|---|
| Score | Corporate Secrets held | Corporate Secrets held + Market Leader Bonus |
| Market Share at game end | First tiebreaker only | Sets the Market Leader Bonus place, and stays the first tiebreaker |
| Starting Corporate Secrets | 7 / 7 / 8 | 9 / 8 / 9 |
| Total Wipeout ranking | Tiebreakers only | Unchanged (no bonus) |
| Everything else | — | Unchanged |

### 1.3 Worked examples (normative)

| Pod | Survivors' final Market Share | Places | Bonus |
|---|---|---|---|
| 2P | A 12, B 9 | A 1st, B 2nd | A +2, B 0 |
| 2P | A 10, B 10 | both 1st | both +2 |
| 3P | A 14, B 11, C 6 | 1st, 2nd, 3rd | +2, +1, 0 |
| 3P | A 14, B 14, C 6 | A, B 1st; C 3rd | +2, +2, 0 |
| 3P | A 14, B 9, C 9 | A 1st; B, C 2nd | +2, +1, +1 |
| 3P | A 7, B 7, C 7 | all 1st | +2 each |
| 4P | A 15, B 15, C 15, D 3 | A, B, C 1st; D 4th | +2, +2, +2, 0 |
| 4P | A 12, B (Patient Zero), C 8, D 0 | A 1st, C 2nd, D 3rd; B no place | +2, 0, +1, 0 |
| 3P | A 5; B, C Patient Zero | A 1st (sole survivor) | +2 (irrelevant to the win) |
| any | everyone Patient Zero (Total Wipeout) | none | none |

---

## 2. Configuration (`sim/config.py`)

### 2.1 New `GameConfig` field (after `market_share_bot_policy`, `config.py:324`)

```python
# --- v0.37.0 Market Leader Bonus (INV-MLB-*). Empty = disabled = v0.36.0 bit-identical. ---
# [TUNE] player count -> bonus Corporate Secrets by Market Share place among survivors (index 0 = 1st place).
# Shorter tuples are padded with 0 up to the player count; extra entries are ignored.
market_leader_bonus_by_player_count: Dict[int, Tuple[int, ...]] = field(default_factory=dict)
```

- **Default `{}`** in both `GameConfig()` and `GameConfig.v036()`. Dataclass equality `GameConfig(num_players=n) == GameConfig.v036(num_players=n)` must still hold (it holds today for n = 2, 3, 4).
- There is no tie-mode lever. Ties always share the better place (C3). See OQ-2.
- There is no config-level bot switch. Bot awareness is a per-bot `MarketSharePolicy` field (§5.1), so the sweep can make one seat aware and the others naive.

### 2.2 Validation (`__post_init__`, after the existing `share_regain_*` key checks)

Raise `ValueError` when any of these holds:
1. A value is not a tuple/list of ints, or an entry is negative.
2. A schedule is not non-increasing (`b[i] >= b[i+1]`). A rising schedule would make "the better place" ambiguous for ties.
3. A schedule has any positive entry and `red_mode != MARKET_SHARE` ("market_leader_bonus requires red_mode=MARKET_SHARE"). This also excludes `V033_THREE_PHASE` and `V034_THREE_LEVEL`, because those cannot run MARKET_SHARE.

Normalise each value to a `tuple` of `int` (so a list passed by a script compares equal).

### 2.3 Accessors

```python
def market_leader_bonus_schedule(self, num_players: Optional[int] = None) -> Tuple[int, ...]:
    """Bonus by place (index 0 = 1st), padded with 0 / truncated to the player count. () when disabled."""

@property
def is_market_leader_bonus(self) -> bool:
    """True when the schedule for self.num_players has any positive entry."""
```

All engine and bot code checks `cfg.is_market_leader_bonus`. A config whose schedule is all zeros behaves exactly like `{}` (INV-MLB-OFF-01).

### 2.4 Factory

```python
@classmethod
def v037(cls, **overrides) -> "GameConfig":
    """v0.37.0 candidate: v0.36.0 + Market Leader Bonus (FINDINGS §38, User 2026-11-07).

    2P 1st +2; 3P 1st +2, 2nd +1; 4P 1st +2, 2nd +1; others 0 [TUNE]. Ties share the better place,
    survivors only, none on a Total Wipeout. Starting Secrets 9 / 8 / 9 [TUNE].
    """
    overrides.setdefault("market_leader_bonus_by_player_count", {2: (2, 0), 3: (2, 1, 0), 4: (2, 1, 0, 0)})
    overrides.setdefault("starting_secrets_by_player_count", {2: 9, 3: 8, 4: 9})  # [TUNE]
    return cls.v036(**overrides)
```

`GameConfig()` is **not** switched to v0.37 here. That is Phase B, after balance sign-off.

### 2.5 Parity fixture (do this first, before any v0.37 code)

1. **Capture `tests/fixtures/v036_parity/` from a clean checkout of HEAD `e1039ae`.** Use `git worktree add ../ra-v036-capture e1039ae` so the untracked probe and dirty docs cannot leak in. Add `capture.py` and `__init__.py` modelled on `tests/fixtures/v035_parity/capture.py`, reusing its `build_engine` and `_bot_classes`, with:
   - factory `GameConfig.v036`;
   - `SEEDS = range(300)`, `PLAYER_COUNTS = (2, 3, 4)`, `SCENARIOS = ("mixed", "setup")`;
   - `RANKING_KEYS_V036 = RANKING_KEYS + ("market_share", "market_share_min", "market_share_regained", "research_spent_regain", "red_blocked_any_total", "red_unblocked_total")`. Use only keys that exist at `e1039ae`;
   - per round: staged / exited / attack cubes (as v035), plus `phase_snapshots[4]` `[money, secrets, market_share]` per player;
   - `EndGameResult` summary: `end_reason`, `total_rounds`, `winner_id`, `winner_ids`, `is_total_wipeout`, `end_triggers`, `tiebreak_decided_by`.
2. Commit the capture script and the JSON files, then copy them into the main working tree.
3. After the change, `GameConfig.v036()` **and** `GameConfig()` must reproduce `v036_parity` exactly (**INV-MLB-PARITY-01**). `v035_parity` (`legacy_v035`), `v034_parity` and `v033_parity` must still pass.
4. The fixture covers the bot hooks too. With the bonus off, the new `marginal_block_value` / `urgent_regain` branches must be unreachable, so any drift there shows up as a parity failure.

---

## 3. Engine: Scoring Math (`sim/engine/market_share.py`)

Add pure helpers with no state mutation and no RNG. They use only stdlib types, so the bot module can import them lazily without a cycle.

```python
def market_share_places(shares: Dict[int, int]) -> Dict[int, int]:
    """Competition ranking (1-based) of player_id -> place by Market Share, highest first.
    place = 1 + number of entries with strictly greater share. Tied players share the better place."""

def market_leader_bonus_awards(shares: Dict[int, int], schedule: Sequence[int]) -> Dict[int, Tuple[int, int]]:
    """player_id -> (place, bonus) for the survivors in ``shares``; bonus = schedule[place - 1] (0 past the end)."""

def expected_market_leader_bonus(share: int, rival_shares: Iterable[int], schedule: Sequence[int]) -> float:
    """Bot estimate (reference: probe exp_bonus). hi = #rivals with share > s, tie = #rivals == s;
    mean of schedule[hi : hi + tie + 1] (0-padded). Used only by bots, never by scoring."""
```

**Note:** `expected_market_leader_bonus` is deliberately **not** the rule's tie outcome (the rule gives every tied player `schedule[hi]`). It averages over the places the tie spans. That is the probe heuristic that produced the §38 numbers, and it acts as a proxy for relative value: breaking a 2P tie at the top moves the rival from +2 to 0. Do not "fix" it to `schedule[hi]` without a new probe run (OQ-3).

---

## 4. Engine: End-Game Scoring (`sim/engine/end_game.py`)

### 4.1 Decision: separate scoring fields; `PlayerState.secrets` is not mutated

**Recommendation:** compute the bonus in `evaluate_end_game` and write it into the ranking rows. **Do not add it to `PlayerState.secrets`.**

Reasons:
1. **Idempotence.** `evaluate_end_game` is public and is called again outside `run_game`: `GameEngine.evaluate_end_game()` (`core.py:479`), `web/controller/phase2_actions.py:33`, and several `scripts/run_v2*_telemetry_sweep.py`. Mutating state would add the bonus twice on a second call.
2. **Ledger clarity.** `PlayerState.secrets` stays "Corporate Secrets held", which matches the physical game: the bonus is scored, not handed out as tokens during play. Every existing Secrets ledger and invariant (Blue loss, Slush Fund, Corruption Track) stays valid.
3. **Reporting.** The ranking row's `"secrets"` is the **final score** (held + bonus), so `_standard_key_ms`, `winner_ids`, competition ranks, `tiebreak_decided_by` and the web end screen (`modals.js:32` reads `r.secrets`) all show the final score with no change. `secrets_before_bonus` keeps the held value.

`_return_held_contractors` is already idempotent, so the whole function becomes idempotent (INV-MLB-SCORE-01).

### 4.2 Algorithm (insert after `all_patient_zero` is computed, `end_game.py:81`)

```text
bonus_on   = cfg.is_market_leader_bonus and not all_patient_zero      # also implies is_six_phase and MARKET_SHARE
survivors  = [p for p in players if not p.is_patient_zero]
places     = market_share_places({p.player_id: int(p.market_share) for p in survivors})
             if cfg.is_market_share and not all_patient_zero else {}   # telemetry even when the bonus is off
awards     = market_leader_bonus_awards(<same shares>, cfg.market_leader_bonus_schedule(len(players))) if bonus_on else {}
```

In the per-player loop (`end_game.py:84-184`):
- `bonus = awards.get(pid, (None, 0))[1]`; `final = p.secrets + bonus`.
- `portfolio_value = max(0, final) * cfg.vp_per_secret` (was `p.secrets`); `net_score = portfolio_value` on the non-wipeout branch.
- Row keys: `"secrets": final`; new `"secrets_before_bonus": p.secrets`, `"market_leader_bonus": bonus`, `"market_share_place": places.get(pid)` (`None` for Patient Zero, under RANSOM and on a Total Wipeout).

The schedule is padded to the **total** player count. Places are computed among survivors only, so a Patient Zero frees its place for survivors below it (worked example 8 in §1.3).

After the survivor sort (`end_game.py:196`) and the existing `winner_ids` computation (`:240`):
- **Pre-bonus winners:** rank `survivors` by the same `std_key` on shallow row copies with `secrets = secrets_before_bonus`, and take every row tied with the top key. `pre_bonus_winner_ids` = those player ids (empty when the bonus is off or on a Total Wipeout).
- `market_leader_bonus_changed_winner = bonus_on and set(pre_bonus_winner_ids) != set(winner_ids)`. A change from a sole winner to a shared victory, or the reverse, counts as a change.
- `market_leader_bonus_tied_paid_place = bonus_on and any(place group of size >= 2 whose schedule[place-1] > 0)`.

**Untouched:** the Total Wipeout branch (`:203-212`), the legacy v0.33 branch, key functions, the Patient Zero sort, shared-victory logic and competition ranks. These all read the row's `"secrets"`, which now carries the final score.

### 4.3 `EndGameResult` additions (`state.py:1007`, all with defaults)

```python
# --- v0.37.0 Market Leader Bonus telemetry (INV-MLB-*) ---
market_leader_bonus_awarded: bool = False          # bonus_on (enabled, not a Total Wipeout)
market_leader_bonus_schedule: List[int] = field(default_factory=list)   # the padded schedule used
pre_bonus_winner_ids: List[int] = field(default_factory=list)
market_leader_bonus_changed_winner: bool = False
market_leader_bonus_tied_paid_place: bool = False
```

### 4.4 Generic shield / contested-round counters (`phase4_attack_resolution.py`, telemetry only)

The §38 Blue agency watch items were measured with a monkeypatch. The sweep must read engine fields instead (as in v0.36 §8). Add these `PlayerState` counters (init next to `red_unblocked_total`, `state.py:245`) and ranking-row keys of the same name:

| Field | Update (immediately after `player.last_defense_breakdown = {...}`, `phase4_attack_resolution.py:436`) |
|---|---|
| `any_shield_allocated_by_color: Dict[str, int]` (`red/blue/green`) | `+= any_allocated[c]` |
| `contested_defense_rounds: int` | `+1` when `any > 0` and `rem_blue > 0` and `rem_red > 0` and `rem_blue + rem_red + rem_green > any`, where `rem_c = max(0, effective_attacks[c] - color_shields[c])` |
| `contested_blue_left_open: int` | in a contested round, `+1` if `any_allocated["blue"] < min(rem_blue, any)` |
| `contested_red_chosen: int` | in a contested round, `+1` if `any_allocated["red"] > 0` |

These definitions match the probe's `res` hook exactly, so V036 cells reproduce the §38 baselines (Any shields on Blue ~63%, Blue left open 6–7%, Red chosen ~22%). Also add the ranking key `dice_owned_final_by_color: Dict[str, int]` (all of `p.total_dice`), for the win-rate-by-Blue-dice metric. Rows and counters are telemetry only: no gameplay read, so parity is unaffected (INV-MLB-OFF-01).

### 4.5 Invariants

| ID | Statement |
|---|---|
| INV-MLB-PARITY-01 | `GameConfig()` and `GameConfig.v036()` reproduce `v036_parity`; `legacy_v035/034/033` reproduce their fixtures. |
| INV-MLB-OFF-01 | With the schedule `{}` or all zeros: no state change, no ranking value change; `market_leader_bonus == 0` and `secrets_before_bonus == secrets` on every row; `market_leader_bonus_awarded is False`. |
| INV-MLB-SCORE-01 | `row["secrets"] == row["secrets_before_bonus"] + row["market_leader_bonus"]`; `evaluate_end_game` never changes `PlayerState.secrets`; calling it twice returns identical rankings. |
| INV-MLB-ELIG-01 | Patient Zero rows: bonus 0, `market_share_place is None`. Places are computed among survivors only. |
| INV-MLB-TIES-01 | `place = 1 + #survivors with strictly greater Market Share`; `bonus = schedule[place-1]`; tied players get identical bonuses. |
| INV-MLB-SOLE-01 | A sole survivor has place 1 and bonus `schedule[0]`. |
| INV-MLB-WIPEOUT-01 | Total Wipeout: no bonus, no place; ranking identical to v0.36 for the same end state. |
| INV-MLB-ORDER-01 | The bonus is added before the Corporate Secrets comparison; the tiebreak order and keys are unchanged; the Market Share tiebreaker uses the same final Market Share as the placement. |
| INV-MLB-COLLAPSE-01 | A survivor at `0` Market Share is placed like any other survivor (can share a place, can earn a bonus if tied at the top). |
| INV-MLB-SETUP-01 | `v037()` = `v036()` + the schedule + starting Secrets 9 / 8 / 9, and nothing else. |
| INV-MLB-SHARED-01 | The bonus never creates or breaks a full-key tie *between two rows*: fully tied rows have equal Market Share, so they get equal bonuses. A third player can still overtake a pre-bonus shared victory (that counts as `changed_winner`). |
| INV-MLB-RNG-01 | No new RNG draws in engine or bot code; same seed + config → identical result. |
| INV-MLB-BOT-01 | The bot valuation is inert unless `cfg.is_market_leader_bonus` and `is_aware(state)` and `pol.leader_bonus_aware` all hold. |
| INV-MLB-BOT-02 | Lethal Blue dominates: the largest possible Red increment, `max(weights) × blue_value × max(schedule)` (= 6.0 at defaults), plus the existing Red terms (≤ 0.5 + 6.0 + 2.0 + 0.5 × 4 = 10.5), stays below `blue_lethal_value` (100). |

---

## 5. Bot Policy (`sim/bots/market_share_policy.py`) `[TUNE-BOT]`

### 5.1 `MarketSharePolicy` additions (frozen dataclass, `market_share_policy.py:25`)

```python
leader_bonus_aware: bool = True                                  # sweep can turn individual seats off
leader_bonus_time_weights: Tuple[float, float, float] = (0.3, 0.6, 1.0)   # current version index 0 / 1 / 2+
leader_bonus_final_round_weight: float = 1.0
```

Helpers:

```python
def leader_bonus_active(player, state, pol) -> bool:
    return bool(state.config.is_market_leader_bonus and is_aware(state) and pol.leader_bonus_aware)

def leader_bonus_time_weight(state, pol) -> float:
    if state.is_final_round: return pol.leader_bonus_final_round_weight
    return pol.leader_bonus_time_weights[min(2, state.current_version_index)]
```

### 5.2 `marginal_block_value`, Red branch (port of probe `mbv`)

At the end of the MARKET_SHARE Red branch, just before `return v` (`market_share_policy.py:~204`). The `r <= 0 → -inf` early return already happened, which matches the probe's `v != -inf` guard:

```python
if leader_bonus_active(player, state, pol):
    sched  = state.config.market_leader_bonus_schedule(len(state.players))
    rivals = list(estimated_rival_shares(player, state, attack.get(CubeColor.RED, 0)).values())
    d = (expected_market_leader_bonus(max(0, share - r + 1), rivals, sched)
         - expected_market_leader_bonus(max(0, share - r), rivals, sched))
    v += leader_bonus_time_weight(state, pol) * pol.blue_value * d
```

- `rivals` uses the same Phase 4 projection as the comparison term (survivors only, each projected once from the start-of-Phase-4 share). In the probe the estimate is computed whether or not a comparison is imminent; keep it that way.
- `choose_aegis_color` calls `marginal_block_value`, so the Aegis *Baffle Echo* choice also becomes bonus-aware. The probe behaved the same way (it patched the module global). Keep it.
- Blue and Green branches are unchanged. Lethal Blue (100) still dominates (INV-MLB-BOT-02).

### 5.3 `urgent_regain` (port of probe `ur`)

Rename the current body to `_urgent_regain_v036` and wrap it:

```python
def urgent_regain(player, state, pol, cap) -> int:
    k0 = _urgent_regain_v036(player, state, pol, cap)
    if (not leader_bonus_active(player, state, pol) or player.market_share is None
            or (state.current_version_index < 1 and not state.is_final_round)):
        return k0
    room = min(cap, player.market_share_max - player.market_share)
    rivals = [int(p.market_share or 0) for p in state.players
              if p.player_id != player.player_id and not p.is_patient_zero]
    if not rivals:
        return k0
    sched = state.config.market_leader_bonus_schedule(len(state.players))
    base = expected_market_leader_bonus(player.market_share, rivals, sched)
    for k in range(1, room + 1):
        if expected_market_leader_bonus(player.market_share + k, rivals, sched) > base:
            return max(k0, k)
    return k0
```

- This uses rivals' **current** Market Share, not the Phase 4 projection, because Phase 6 is after damage. This matches the probe.
- In the Final Round, `_urgent_regain_v036` already returns `room`, so the wrapper changes behaviour only in `v2.0`+ outside the Final Round.
- The caller (`research_policy.py:111`) already caps the result by affordable research and calls it only when `aware`.

### 5.4 Explicitly not changed

- `apply_market_share_policy`: no extra Red purchase nudge (probe `amsp` dropped).
- `research_focus` / `research_focus_v036` on every bot: no Public Relations Track reordering (probe `pr_focus` dropped).
- `place`, `comparison_imminent`, `is_critical`, the Ad Campaign rule: unchanged.

---

## 6. Telemetry Schema

### 6.1 Ranking rows (per player)

| Key | Type | Meaning |
|---|---|---|
| `secrets` | int | **Final score** = held + bonus (unchanged name; meaning widened) |
| `secrets_before_bonus` | int | Corporate Secrets held at game end |
| `market_leader_bonus` | int | Bonus gained (0 if off, Patient Zero or Total Wipeout) |
| `market_share_place` | int / None | Competition place among survivors under MARKET_SHARE (also when the bonus is off, for baselines); `None` for Patient Zero, under RANSOM and on a Total Wipeout |
| `any_shield_allocated_by_color` | dict | §4.4 |
| `contested_defense_rounds`, `contested_blue_left_open`, `contested_red_chosen` | int | §4.4 |
| `dice_owned_final_by_color` | dict | §4.4 |

### 6.2 `EndGameResult` (per game)

See §4.3: `market_leader_bonus_awarded`, `market_leader_bonus_schedule`, `pre_bonus_winner_ids`, `market_leader_bonus_changed_winner`, `market_leader_bonus_tied_paid_place`.

### 6.3 Derived metrics (computed by the sweep; formulas fixed here)

| Metric | Formula |
|---|---|
| Winner changed by the bonus | mean of `market_leader_bonus_changed_winner` over games with `market_leader_bonus_awarded` (also report over all games) |
| Paid place tied | mean of `market_leader_bonus_tied_paid_place` over awarded games |
| Highest / lowest Market Share survivor wins | among games with ≥ 2 survivors: win credit (`1/|winner_ids|`) of survivors with `market_share_place == 1` / with the maximum place value |
| Mean survivor Secrets before bonus / bonus | means over survivor rows |
| Bonus-aware edge (ONE-AWARE cell) | aware seat win credit − fair share (1/n); 95% CI |
| Any shields on Blue / Red | Σ `any_shield_allocated_by_color[c]` / Σ over colors |
| Blue left open / Red chosen in contested rounds | Σ `contested_blue_left_open` / Σ `contested_defense_rounds` (same for Red) |
| Win rate by Blue dice owned 0 / 1 / 2+ | from `dice_owned_final_by_color["blue"]` |
| Patient Zero / Singularity / Market Collapse; Total Wipeout; rounds | as `run_v360_market_share_sweep.py` (`three_way`) |

---

## 7. Edge Cases (normative)

| # | Case | Resolution |
|---|---|---|
| E1 | All survivors tied on Market Share | All are 1st and gain `schedule[0]`. No relative change; the Secrets comparison decides as before. |
| E2 | 3P tie for 2nd (14 / 9 / 9) | Both 2nd gain +1. No 3rd place is paid. |
| E3 | 4P three-way tie for 1st | All three gain +2; the 4th is 4th (0). |
| E4 | Patient Zero between survivors | Not placed; survivors below move up (4P: 12 / PZ / 8 / 0 → 1st / – / 2nd / 3rd). |
| E5 | Sole survivor | 1st, `schedule[0]`; still the winner (`tiebreak_decided_by="sole_survivor"`). |
| E6 | Total Wipeout (Phase 2 or Phase 4) | No bonus; `market_share_place=None`; ranking unchanged from v0.36. |
| E7 | Survivor at `0` after Market Collapse | Placed by Market Share like anyone else. Two survivors at 0 in 2P share 1st and both gain +2. |
| E8 | Market Collapse and Patient Zero in the same round | Patient Zero excluded; the remaining survivors are placed. |
| E9 | Singularity | Bonus applies (Phase 4 did not run that round; Market Share is the end of the previous round's Phase 6). |
| E10 | Bonus lifts a player from ≤ 0 Corporate Secrets | Impossible: a player at ≤ 0 is Patient Zero and gets no bonus. |
| E11 | Shared victory and the bonus | Two fully tied players stay fully tied (equal Market Share → equal bonus, INV-MLB-SHARED-01). A third player can overtake them: 3P A, B at 6 Secrets / share 10, C at 5 / share 12 → C 7, A and B 7 each; Market Share gives C the win; `changed_winner True`. |
| E12 | Market Share regained in the Final Round's Phase 6 | Counts for the place (final Market Share). |
| E13 | Schedule shorter than the player count | Padded with 0. |
| E14 | `market_share_bot_policy="NAIVE"` | The bonus still scores; bots ignore it (`is_aware` is false). |

---

## 8. Product-Owner Sweep Definition

**Script:** `scripts/run_v370_market_leader_bonus_sweep.py`, modelled on `scripts/run_v360_market_share_sweep.py`. Reuse its `build_engine` structure, `BASE_KW`, `BOT_CLASSES`, `ci95`, `quantiles`, `bootstrap_spread_ci`, `three_way` and the CLI (`--games/--scale/--seed/--pods/--cells/--workers/--out`). Import them, or copy them; do not edit the v360 script. Output `sim_results/v370_market_leader_bonus_sweep.json` (and `..._seed7000.json`). Report: `docs/findings/v370_market_leader_bonus_sweep_report.md`.
**Telemetry** comes only from engine fields (§6). No monkeypatched hooks.
**Seeds:** `seed = base + n × 100_000 + idx`. The same seeds go to every cell (paired). Base 42 for the main run; **fresh-seed run with `--seed 7000`** for `V036`, `V037` and `V037-ONE-AWARE`.
**Bot modifier signature:** `bot_mod(bots, match_idx)` (v360's takes `bots` only), so `ONE-AWARE` can pick the seat.

| Cell | Config | Bot modifier | Games per pod (2P/3P/4P) |
|---|---|---|---|
| `V036` (baseline) | `GameConfig.v036` | – | 3,000 |
| `V037` (acceptance) | `GameConfig.v037` | – (all bots bonus-aware) | 3,000 |
| `V037-S036` (ablation) | `v037` + `starting_secrets_by_player_count={2: 7, 3: 7, 4: 8}` | – | 3,000 |
| `V037-NAIVE` | `v037` | every bot `leader_bonus_aware=False` (bonus scores, bots ignore it) | 2,000 |
| `V037-ONE-AWARE` | `v037` | only seat `match_idx % n` (post-shuffle player id) aware | 3,000 |
| Fresh seeds | `V036`, `V037`, `V037-ONE-AWARE` at `--seed 7000` | as above | 3,000 |

Report every metric in §6.3 for each cell, with 95% CIs, and the deltas `V037 − V036` (and `V037-S036 − V036`).

**Guardrails for `V037`** (§34 set, plus the §38 watch items):

| Guardrail | Pass | Watch (game-designer judgement) | Fail |
|---|---|---|---|
| End-reason split (Patient Zero incl. Total Wipeout / Singularity / Market Collapse) | each 25–40% per pod | any 20–25% or 40–46% (OQ-1) | < 20% or > 46% |
| 2P Singularity (§38) | ≤ 43% | 43–46% | > 46% |
| Highest single-setup trigger (v3.0 card, company seat, White Hat seat) | ≤ 43% (§34 level) | 43–55% | > 55% |
| Rounds (mean) | 8.4–9.2 | 9.2–9.4 | outside 8.2–9.4 |
| Total Wipeout | ≤ V036 + 1.0 pt | V036 + 1.0–2.0 pts (2P §38: 7.7–8.4% vs 7.1%) | > V036 + 2.0 pts, or 2P > 16% |
| No Market Collapse in ≤ 5 rounds | 0 games | – | any |
| Red block rate | ≥ V036 | – | < V036 − 1 pt |
| Regain share of research spend | 20–40% | 40–50% | > 50% |
| Winner changed by the bonus | 10–30% per pod (§38: 15–18 / 17–20 / 25–27%) | 30–35% | > 35% (bonus dominates) or < 5% (inert) |
| Bonus-aware edge (`ONE-AWARE`) | ≤ +7 pts over fair | +7–10 pts (§38 2P +9) | > +10 pts |
| Any shields on Blue | ≥ 55% (V036 ~63%, §38 57–60%) | 50–55% | < 50% (Blue stops being the main target) |
| Blue left open in contested rounds | ≤ 25% (V036 6–7%, §38 17–22%) | 25–30% | > 30% |
| Lowest-Market-Share survivor wins | report (§38 31 / 20 / 13%; V036 44 / 33 / 23%) | 2P < 25% | – |
| Company spread (max − min win rate) | ≤ V036 + 3 pts | – | – (report) |
| `V037-NAIVE` Patient Zero | report (§38 18–26%) | < 20% in any pod | – |

The game-designer may add cells (for example a schedule or starting-Secrets grid). The product-owner does not change engine mechanics (PLAN §2).

**Expected magnitudes (reference, not pass criteria):** §38's "all bonus-aware" numbers came from the probe with `deep=True`, which also ran the dropped Red nudge and a Public Relations Track focus change. The non-deep probe cells at +1 Secret differ by ≤ 2 points on endings and Total Wipeout (`sim_results/v360_share_placement_deep.json`, deep False vs True). Expect V037 within ~2–3 points of §38's 2P 27 / 46 / 27, 3P 37 / 41 / 22, 4P 32 / 39 / 28. A larger gap means a porting defect; check §5 against the probe first.

---

## 9. Unit Test Specification (`tests/test_v370_market_leader_bonus.py`)

Use the `MSHarness` pattern from `tests/test_v360_market_share.py` (build an engine, set `is_patient_zero`, `market_share`, `secrets`, `money`, then call `evaluate_end_game`).

| ID | Test |
|---|---|
| MLB-01 | `GameConfig()` / `v036()`: schedule `{}`, `is_market_leader_bonus False`, Secrets 7 / 7 / 8; `GameConfig(num_players=n) == GameConfig.v036(num_players=n)`. `v037()`: schedules `(2,0)`, `(2,1,0)`, `(2,1,0,0)`, Secrets 9 / 8 / 9, every other field equal to `v036()` (compare `dataclasses.replace` with those two fields reset). |
| MLB-02 | Validation: negative entry, increasing schedule, positive schedule under `red_mode=RANSOM` → `ValueError`; list input normalised to tuple; all-zero schedule → `is_market_leader_bonus False`. |
| MLB-03 | `market_leader_bonus_schedule`: padding (`{4: (2,)}` → `(2,0,0,0)`), truncation, `()` when disabled. |
| MLB-04 | Schedule per player count, distinct shares: 2P 12/9 → +2/0; 3P 14/11/6 → +2/+1/0; 4P 15/12/8/3 → +2/+1/0/0. Rows: `secrets == secrets_before_bonus + market_leader_bonus`, places 1..n. |
| MLB-05 | **Two-way tie for 1st**: 2P 10/10 → both +2, both place 1; 3P 14/14/6 → +2/+2/0, places 1/1/3. |
| MLB-06 | **Three-way tie**: 3P 7/7/7 → all +2; 4P 15/15/15/3 → +2/+2/+2/0, D place 4. |
| MLB-07 | **Tie for 2nd**: 3P 14/9/9 → +2/+1/+1; 4P 12/8/8/2 → +2/+1/+1/0 (D place 4). `market_leader_bonus_tied_paid_place` True; False for 14/11/6. |
| MLB-08 | **Patient Zero exclusion and place shifting**: 4P A 12, B Patient Zero (share 16, the highest), C 8, D 0 → A +2 place 1, C +1 place 2, D 0 place 3, B 0 place `None`; B ranked after all survivors. |
| MLB-09 | **Sole survivor** (2P and 3P): bonus `schedule[0]`, place 1, winner, `tiebreak_decided_by == "sole_survivor"`. |
| MLB-10 | **Total Wipeout**: all Patient Zero → no bonus, places `None`, `market_leader_bonus_awarded False`; rankings equal to the same state under `v036()` (except the new keys). |
| MLB-11 | **Market Collapse player at 0**: 3P 10/6/0 after collapse → 0 gets place 3, bonus 0, not eliminated; 2P 0/0 → both +2. |
| MLB-12 | **Bonus changes the winner**: 2P A 5 Secrets / 9 share, B 4 / 12 → pre-bonus winner A, final B (4+2=6 > 5); `pre_bonus_winner_ids == [A]`, `changed_winner True`. Counter-case: 2P A 7/9, B 4/12 → not changed. |
| MLB-13 | **Bonus creates a Secrets tie broken by Market Share**: 3P A held 6 / share 14, B 7 / 9, C 3 / 2 → final A 8, B 8, C 3; A wins on Market Share; pre-bonus winner B; `changed_winner True`; `tiebreak_decided_by == "market_share"`. **Shared victory unchanged**: 2P A and B identical (5 held, share 10, same Money, dice, Research Tokens) → both +2, `is_shared_victory True`, `pre_bonus_winner_ids == winner_ids`, `changed_winner False`. **Shared victory overtaken**: the E11 3P case → winner C, `changed_winner True`. |
| MLB-14 | **Tiebreakers use the final score**: 3P A held 5 / share 9, B held 6 / share 12 / $3, C held 6 / share 12 / $5 → B and C share 1st (+2 → 8 each), A is 3rd (0 → 5); B and C tie on Secrets and Market Share, so Money decides (C); `tiebreak_decided_by == "money"`. |
| MLB-15 | **Idempotence**: calling `evaluate_end_game` twice gives identical rankings; `PlayerState.secrets` unchanged. |
| MLB-16 | **Starting Secrets under `v037()`**: a new engine at 2/3/4P has `p.secrets == 9 / 8 / 9` (no company bonus). |
| MLB-17 | **v036 parity**: `GameConfig.v036` and `GameConfig()` vs `tests/fixtures/v036_parity` (mixed / setup × 300 seeds × 2/3/4P; `GameConfig()` may use a 50-seed subset as MS-03 does). `v035_parity` replay is still in `test_v360_market_share.py`. |
| MLB-18 | **Off-switch parity**: `v036(market_leader_bonus_by_player_count={3: (0, 0, 0)})` reproduces `v036_parity` 3P for 20 seeds. |
| MLB-19 | `expected_market_leader_bonus` values, schedule `(2,1,0)`: s=10 vs [8,5] → 2.0; vs [10,5] → 1.5; vs [10,10] → 1.0; vs [12,10] → 0.5; vs [12,11] → 0.0. Schedule `(2,0)`: 10 vs [10] → 1.0; 11 vs [10] → 2.0; 9 vs [10] → 0.0. |
| MLB-20 | **`marginal_block_value` Red increment**: 2P, `current_version_index=1`, not the Final Round, share 10, `rem[RED]=1`, rival projected at 10 → increment over the bonus-off value = `0.6 × 3.0 × (1.0 − 0.0) = 1.8`. Same state with index 0 → 0.9; Final Round → 3.0; index 2 → 3.0. Rival Patient Zero → excluded (sole rival gone → `exp` vs [] = `schedule[0]` both ways → increment 0). |
| MLB-21 | **Inert when off**: bonus off, or `market_share_bot_policy="NAIVE"`, or `leader_bonus_aware=False` → `marginal_block_value` and `urgent_regain` equal the v0.36 values for a grid of states. |
| MLB-22 | **Lethal Blue dominates**: with the bonus at maximum swing (Final Round, share at a 2P tie boundary), `default_any_shield_allocation` with 1 Generic shield, 1 lethal Blue and 1 Red → Blue. |
| MLB-23 | **Generic shield choice flips to Red when bonus-relevant**: `current_version_index=2`, 2P, Secrets 6, share 10 vs rival projected 10, Red pressure low enough that the danger term is 0, no comparison left, 1 Generic shield, 1 Blue (non-lethal) + 1 Red → Red (0.5 base + 1.0 × 3.0 × 1.0 bonus = 3.5 > Blue 3.0). Bonus-off control → Blue (0.5 < 3.0). |
| MLB-24 | **`urgent_regain`**: v1.0 (index 0), not final → equals v0.36. v2.0, share 9 vs rival 10, cap 2 → 1. Share 9 vs rival 11, cap 2 → 2; cap 1 → v0.36 value. At max share → 0. Final Round → `room` (unchanged). No surviving rival → v0.36 value. |
| MLB-25 | **Determinism**: two `v037()` runs with the same seed (setup scenario, 2/3/4P, 10 seeds) → identical `EndGameResult` rankings and telemetry; `random` state not consumed (patch `random.Random` methods to count calls inside `evaluate_end_game` and the two bot hooks → 0). |
| MLB-26 | **Telemetry counters** (§4.4): a contrived Phase 4 (1 Generic shield, Blue 2 / Red 2 unblocked after color shields) increments `contested_defense_rounds`; a bot Red pick increments `contested_red_chosen` and `contested_blue_left_open`. Off-state parity is covered by MLB-17. |

Every existing test must pass unchanged (`python3 -m pytest -q`).

---

## 10. File-by-File Change List

| File | Change |
|---|---|
| `tests/fixtures/v036_parity/{__init__,capture}.py`, `*.json` | **First**, from the clean `e1039ae` worktree (§2.5). |
| `sim/config.py` | Field, validation, `market_leader_bonus_schedule`, `is_market_leader_bonus`, `v037()`. |
| `sim/engine/market_share.py` | `market_share_places`, `market_leader_bonus_awards`, `expected_market_leader_bonus`. |
| `sim/engine/end_game.py` | §4.2 (bonus before ranking, new row keys, pre-bonus winners, flags). Total Wipeout and legacy paths untouched. |
| `sim/engine/state.py` | `EndGameResult` fields (§4.3); `PlayerState` counters (§4.4). |
| `sim/engine/phase4_attack_resolution.py` | Counter updates after `last_defense_breakdown` (§4.4), telemetry only. |
| `sim/bots/market_share_policy.py` | Policy fields, `leader_bonus_active`, `leader_bonus_time_weight`, Red increment (§5.2), `urgent_regain` wrapper (§5.3). |
| `tests/test_v370_market_leader_bonus.py` | §9. |
| `scripts/run_v370_market_leader_bonus_sweep.py` | §8 (product-owner may write it; the engineer provides it if the PLAN routing says so). |
| `PLAN.md`, `FINDINGS.md` | Checkbox updates by the orchestrator, not by the engineer. |

No change to `phase2_compiler.py`, `phase6_operations.py`, `research_policy.py`, any bot subclass, `web/`, `pnp/` or `RULES.md` in this phase.

---

## 11. RULES.md / Glossary Sections to Update (Phase B; list only)

Use only canonical Section 7 terms. **Market Leader Bonus** is the only new term (User-approved, 2026-11-07).

| Location | Change |
|---|---|
| Title line (`RULES.md:1`) | `v0.36.0` → `v0.37.0`. |
| §1 Theme & Overview (`:14`) | The winner sentence: survivors compare Corporate Secrets **after the Market Leader Bonus**. |
| §2 Player & Market Components, Market Share Track bullet (`:42`) | Add: at game end, survivors' Market Share places earn the Market Leader Bonus. |
| §3 Setup, Corporate Secrets bullet (`:148`) | `9` (2 players) / `8` (3 players) / `9` (4 players) `[TUNE: v0.37.0]`. |
| §4 Phase 6, regain bullet (`:306`) | "final Market Share is the first tiebreaker" → also sets your Market Leader Bonus place. |
| §5 Determining the Winner (`:321-338`) | New first scoring step in the Standard Ending: Market Leader Bonus by place (schedule table per player count, ties share the better place, Patient Zeros excluded and take no place, sole survivor gains 1st). The `:325` line "Market Share … score `0 VP`" becomes: Market Share scores only through the Market Leader Bonus. `:333` Market Collapse note: the player at `0` scores normally and is placed by Market Share like anyone else. Total Wipeout bullet: no Market Leader Bonus. |
| §6D Client Companies intro (`:412`) | Starting Secrets 9 / 8 / 9. |
| §7 Glossary, new entry **Market Leader Bonus** (§7.6 Phase Mechanics & End Game) | End Game Rule: at game end (not a Total Wipeout), surviving players gain bonus Corporate Secrets by Market Share place before Secrets are compared: 2P 1st `+2`; 3–4P 1st `+2`, 2nd `+1`; others `0` `[TUNE]`. Tied players share the better place; Patient Zeros take no place. |
| §7 **Market Share** (`:517`) | "Scores `0 VP`" → "Scores no VP directly; sets the **Market Leader Bonus** at game end." |
| §7 **Corporate Secrets** (`:512`) | Add the Market Leader Bonus as an end-game gain. |
| §7 **Total Wipeout Ending** (`:554`) | Add "no **Market Leader Bonus**". |
| **Market Collapse** entry (`:391`) | "the player at `0` scores normally" → add "including the **Market Leader Bonus** by place". **Note:** this glossary row sits inside the §6C Version Card table (between the two `v3.0` rows), not in Section 7. Phase B should move it into §7.6 (flag for the User; no wording change). |

Phase B, other artifacts (`graphic-designer` / engineer):
- `web/static/index.html:129-131` player-count labels (Secrets 9 / 8 / 9);
- `web/static/js/components/modals.js` end screen: show `secrets_before_bonus`, `market_leader_bonus` and `market_share_place`;
- `web/static/js/components/compiler.js:360` victory goal text;
- `pnp/generate_pnp.py:1397, 1555, 1569, 1572, 1784`: scoring summary, setup line, Total Wipeout line, plus a placement reminder on the Market Share track of the Company Terminal Mat;
- `GameConfig()` default → `v037` values, and `GameConfig.v036()` kept as the frozen baseline (the parity test then uses `v036()` only, as MS-03 does for v0.35);
- `CLAUDE.md` Core Design Pillars: the scoring bullet.

---

## 12. Implementation Sequencing

1. Capture `v036_parity` from the clean worktree; commit (§2.5).
2. Config lever + `v037()` + MLB-01..03.
3. Pure helpers in `market_share.py` + MLB-19.
4. `end_game.py` + `EndGameResult` + MLB-04..18.
5. Phase 4 counters + MLB-26.
6. Bot hooks + MLB-20..25.
7. Full test suite, parity, then hand to the `staff-engineer` review gate.
8. Sweep script; product-owner runs §8; game-designer assessment; User sign-off; Phase B.

---

## 13. Risks / Watch Items

- **2P Singularity 43–46%** and the 2P bonus-aware edge (+9 pts) are already over target in §38. Expect them to remain watch items.
- **3P Market Collapse 22% / Singularity 41%** in §38's all-aware run fall outside the §34 25–40% band (OQ-1).
- **Porting drift:** §38 used `deep=True` bots. Removing the Red nudge and Public Relations Track focus change should move results ≤ 2 points (§8 note). More than that points to a bug.
- **Bot behaviour from higher starting Secrets:** several bots key on `player.secrets` thresholds (e.g. `venture_greed.py:237`, `secrets <= 2`). 9 / 8 / 9 shifts them; the `V037-S036` ablation isolates this.
- **Web second call:** `phase2_actions.py:33` re-evaluates; §4.1 idempotence makes this safe.
- **Tie frequency:** paid-place ties in 19 / 45 / 72% of games (§38). Shared ties make the bonus less decisive at 4P; the "winner changed" band watches this.

---

## 14. Open Questions for Orchestrator / User

| # | Question | Recommendation |
|---|---|---|
| OQ-1 | §34's end-reason band (each 25–40% per pod) conflicts with §38's accepted package (2P Singularity 46%, 3P Market Collapse 22%, 3P Singularity 41%). Which band governs V037? | Use the three-tier table in §8: 2P Singularity pass ≤ 43%, watch 43–46%; other endings pass 25–40%, watch 20–25% / 40–46%, fail beyond. The game-designer decides watch cases; the User signs off. |
| OQ-2 | FINDINGS §38 plan item 3 mentions a "tie mode" lever. Add one (shared vs standard tiebreakers) or not? | **No.** The User locked shared ties, the probe already measured the alternative (§38 finding 1), and a second mode doubles the test matrix. Add it later if the game-designer wants a cell. |
| OQ-3 | The bot estimate averages over the places a tie spans; the rule gives every tied player the better place. Port faithfully or use the exact rule? | **Port faithfully** (as instructed). It is the heuristic behind the §38 numbers, and it captures the relative value of breaking a tie. Revisit only with a new probe. |
| OQ-4 | Mutate `PlayerState.secrets`, or keep the bonus as a separate scoring field? | **Separate field**, with the row `"secrets"` = final score (§4.1). The web end screen gets the final score with no change. |
| OQ-5 | Sole survivor: award the 1st-place bonus? | **Yes**, `schedule[0]`. It is consistent with "survivors are placed", irrelevant to the win, and avoids a special case in the rules text. |
| OQ-6 | Should `market_share_place` be recorded when the bonus is off (V036 baselines)? | **Yes**, under MARKET_SHARE for survivors. It is telemetry only and gives the "highest/lowest Market Share survivor wins" baselines for free. |
| OQ-7 | §38 says the Market Collapse player "places last". | Rules text should say "placed by Market Share like anyone else". A player at `0` can tie others at `0` and share a place (E7). Confirm the wording in Phase B. |
| OQ-8 | The Market Collapse glossary row is misplaced inside the §6C Version Card table (`RULES.md:391`). Move it in Phase B? | **Yes**, move it into §7.6 with no change to its meaning. It is a documentation fix, not a rules change. |
| OQ-9 | Who writes the sweep script: `senior-engineer` or `product-owner`? | The `senior-engineer` writes it with the telemetry (it depends on the §4.4 fields and the `bot_mod(bots, match_idx)` signature); the `product-owner` runs it and owns the report. This matches Phase 45. |

### 14.1 Resolutions (User, 2026-11-07)
All nine recommendations in §14 are accepted as written (OQ-1 three-tier ending bands; OQ-2 no tie-mode lever; OQ-3 port the probe's tie-averaging estimate; OQ-4 separate scoring field, `"secrets"` in rankings = final score; OQ-5 sole survivor gets the 1st-place bonus; OQ-6 record `market_share_place` with the bonus off; OQ-7 Market Collapse player placed by Market Share like anyone else; OQ-8 move the Market Collapse row into §7 in Phase B, wording unchanged; OQ-9 `senior-engineer` writes the sweep script, `product-owner` runs it).
