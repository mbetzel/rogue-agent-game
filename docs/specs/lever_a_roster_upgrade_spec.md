# Technical Specification: Lever A (Roster Upgrade)
## Public Relations push and Market Share dump windows in AdaptiveBalanced

**Author:** Principal Engineer
**Status:** Draft for implementation. The open questions in §12 need an answer, or acceptance of the recommended default, before the `senior-engineer` starts.
**Source of truth:** `docs/findings/lever_a_roster_upgrade_scoping.md` (game-designer, 2026-11-07), including both "User decisions" sections, which override the earlier text. FINDINGS §40 and its addendum (`docs/findings/v370_reference_bot_attribution.md`).
**Dependencies:** [reference bot spec](./reference_bot_spec.md) (hazards H1/H2/H5, `fast_clone`, INV-REF-*), [v360 spec](./v360_market_share_red_rework_spec.md) (Market Share bot policy), [v370 spec](./v370_market_leader_bonus_spec.md).
**Scope:** `sim/config.py` (one switch + one parameter dataclass), `sim/bots/`, `tests/`, `scripts/`. **No rule change**: no `RULES.md`, `web/` or `pnp/` edit and no new game term. Everything here is `[TUNE-BOT]`.

**Target components**
- `sim/config.py`: `bot_pr_push: bool = False`, `bot_pr_push_params: PrPushParams` (frozen dataclass), validation in `__post_init__`.
- New leaf module `sim/bots/pr_push_policy.py`: window evaluation, the two line policies (moved from `reference_search.py`), `_ordered_research` (moved, one new parameter), allocation and colour helpers.
- `sim/bots/adaptive_balanced.py`: `pr_push_capable = True`; `choose_any_shield_allocation` override; windowed dice-buying colours.
- `sim/bots/research_policy.py` (`apply_research_policy`), `sim/bots/market_share_policy.py` (`apply_market_share_policy`): one windowed branch each.
- `sim/bots/mixed_policy.py`: `"pr_push_capable"` added to `PROFILE_ATTRS`.
- `sim/bots/reference_search.py`: imports the moved names from `pr_push_policy`; `_ResearchLineBot.pr_push_capable = False`.
- New: `tests/fixtures/v037_push/` (capture + JSON), `tests/test_lever_a_pr_push.py`, `scripts/run_lever_a_sweep.py`; `scripts/run_reference_bot_validation.py` gains `--pr-push` and `--pr-params`.

---

## 1. Executive summary

| # | Change |
|---|---|
| A1 | A GameConfig `[TUNE-BOT]` switch `bot_pr_push` (default **False**). Off = every existing fixture and result byte-identical (INV-LA-PARITY-01). |
| A2 | Ten threshold constants plus one variant selector in a frozen `PrPushParams` dataclass on GameConfig (§2). `PUSH_MIN_SHARE > DUMP_MAX_SHARE` is enforced at config construction. |
| A3 | A pure window function: each AdaptiveBalanced decision (Phase 4 Generic shield split, Phase 6 Operations plan research and regain, dice buying) is in the **dump** window, the **push** window, or neither (§3). |
| A4 | Push window: Generic shields with `PR_PUSH_POLICY` and fill Red → Blue → Green; Phase 6 one Public Relations Track step (cap level 1, ≤ 2 Research Tokens) then Market Share regain; Red bought first, Red purchase nudge up to full Market Share (§4). |
| A5 | Dump window (**Market Share ≤ `DUMP_MAX_SHARE` alone**, User decision §9.1): Generic shields with `DUMP_POLICY` and fill Blue → Green → Red; no Public Relations Track step and no regain; no Red bought for Market Share (§4). The "1st place out of reach or Market Collapse threat" condition exists only as sweep variant `dump_condition="reach_or_threat"`. |
| A6 | The Blue block that prevents a **Total Data Breach** (`blue_lethal_value`) stays first in every window (INV-LA-LETHAL-01). |
| A7 | The switch reaches Mixed's AdaptiveBalanced delegate and the reference bot's fallback and rollout seats through the shared GameConfig, with no per-bot state (§5). |
| A8 | New `v037_push` parity fixtures, a one-at-a-time sweep script, and the scoping §6 validation plan (§7–§8). |

Not in scope (User decisions): the leader-side Phase 6 dump (≥ 9 Market Share skipping the Public Relations Track and regain), other archetypes, Phase 1 shield commits (the dump line's Blue-option override is not adopted).

---

## 2. The switch and the constants

### 2.1 Where the constants live: GameConfig (decision)

`PrPushParams` is a `@dataclass(frozen=True)` defined in `sim/config.py`, held by GameConfig as `bot_pr_push_params`. Reasons:

1. **Sweeps.** `run_lever_a_sweep.py` runs cells in worker processes. Module globals would have to be monkeypatched in every worker, would not be visible in the result JSON, and a missed patch silently runs the default. A config field is pickled into each task, written to the result metadata from `dataclasses.asdict`, and differs per cell by construction.
2. **One pod, one model.** Every seat, the Mixed delegate, the reference fallback and every rollout clone read `state.config`. `fast_clone` shares `config` by reference (reference bot spec §6 table), which is exactly right for a value that must be equal across the live game and its clones. Frozen means sharing cannot leak a mutation from a rollout back into the live game.
3. **Validation at load.** Disjointness (`PUSH_MIN_SHARE > DUMP_MAX_SHARE`) and range checks run once in `GameConfig.__post_init__`, so an illegal sweep cell fails before any game runs.
4. **Precedent.** `market_share_bot_policy` already is a sim-only bot switch on GameConfig. It does not create a rule.

Cost: `sim/config.py` must stay a leaf (it must not import `sim.bots`), so the dataclass lives in `config.py` and the bot module reads it. Bots never cache it (statelessness, §5.3).

The line policies (`PR_PUSH_POLICY`, `DUMP_POLICY`, fill orders, focus tuples) stay **module constants** in `pr_push_policy.py`: they are not swept, and the reference portfolio lines already depend on their exact values.

### 2.2 Fields

```python
# sim/config.py
@dataclass(frozen=True)
class PrPushParams:                       # [TUNE-BOT] lever A (docs/specs/lever_a_roster_upgrade_spec.md)
    push_min_share: int = 6               # PUSH_MIN_SHARE
    push_low_gap: int = 7                 # PUSH_LOW_GAP (User decision §9.3)
    push_top_gap: int = 3                 # PUSH_TOP_GAP
    push_max_version: int = 1             # PUSH_MAX_VERSION (Version index; 1 = v2.0)
    push_secrets_band: int = 2            # PUSH_SECRETS_BAND
    push_pr_cap: int = 1                  # PUSH_PR_CAP (Public Relations Track level)
    push_max_research: int = 2            # PUSH_MAX_RESEARCH (Research Tokens on hand)
    dump_max_share: int = 5               # DUMP_MAX_SHARE
    dump_top_gap: int = 2                 # DUMP_TOP_GAP (variant only)
    dump_threat_margin: int = 2           # DUMP_THREAT_MARGIN (variant only)
    dump_condition: str = "share_only"    # "share_only" (default, User decision §9.1) | "reach_or_threat" (sweep)

# GameConfig
bot_pr_push: bool = False                 # [TUNE-BOT] sim-only, default off
bot_pr_push_params: PrPushParams = field(default_factory=PrPushParams)
```

`__post_init__` (always, whether or not the switch is on, so a bad sweep cell fails even if mis-flagged):
- `push_min_share > dump_max_share`, else `ValueError("PUSH_MIN_SHARE must exceed DUMP_MAX_SHARE (windows must be disjoint)")`. Use `raise`, not `assert` (survives `python -O`).
- `dump_condition in ("share_only", "reach_or_threat")`; all ints ≥ 0 except the gaps (any int).
- `bot_pr_push` and `bot_pr_push_params` are not set by `v036()` / `v037()` / `legacy_*` factories, so `GameConfig() == GameConfig.v037()` (existing tests) still holds. `GameConfig.v037(bot_pr_push=True)` is the "v037_push" configuration; no new factory.

Under RANSOM or `market_share_bot_policy="NAIVE"` the switch is inert (§3.1), so it is legal to set but has no effect.

---

## 3. Window evaluation (pure, no RNG)

### 3.1 Function

```python
# sim/bots/pr_push_policy.py
NONE, PUSH, DUMP = "none", "push", "dump"

def window(bot, player, state) -> str:
    cfg = state.config
    if not (getattr(cfg, "bot_pr_push", False) and getattr(bot, "pr_push_capable", False)
            and msp.is_aware(state) and player.market_share is not None and not player.is_patient_zero):
        return NONE
    p = cfg.bot_pr_push_params
    rivals = [q for q in state.players if q is not player and not q.is_patient_zero and q.market_share is not None]
    ms = int(player.market_share)
    if not rivals:                       # sole survivor: nothing to race for
        return NONE
    lo = min(int(q.market_share) for q in rivals); hi = max(int(q.market_share) for q in rivals)
    if ms <= p.dump_max_share:
        if p.dump_condition == "share_only":
            return DUMP
        threat = ms <= msp.red_pressure(state) + p.dump_threat_margin
        if ms - hi <= -p.dump_top_gap or threat:
            return DUMP
        return NONE                      # variant: low but in reach and not threatened -> default behaviour
    sl = int(player.secrets) - max(int(q.secrets) for q in rivals)
    if (int(state.current_version_index) <= p.push_max_version and ms >= p.push_min_share
            and ms - lo <= p.push_low_gap and ms - hi <= p.push_top_gap and abs(sl) <= p.push_secrets_band):
        return PUSH
    return NONE
```

Rules:
- Reads only `state` / `player` fields; never an RNG, never writes. INV-LA-RNG-01.
- Evaluated **at the call**, from the live values at that moment (Phase 4: after earlier seats' resolution in turn order; Phase 6: the value when the plan is resolved and again when it is post-processed, which is the same state, see §5.1). No caching.
- Dump is tested first; with disjoint thresholds the push test is unreachable for `ms <= dump_max_share` anyway.
- `is_final_round`: no special case (the windows key off Market Share and the race; the existing final-round guards inside AdaptiveBalanced, such as no dice buying, still apply first).

### 3.2 Hazard H-LA-1: "rival" set and Patient Zero

The scoping log used surviving rivals. A Patient Zero keeps a stale Market Share; including it would distort `lo`/`hi`. The filter above is required (test LA-05).

---

## 4. Behaviour per window

Outside both windows, every code path below must reach the existing code unchanged (the window branch is an early `if`, and NONE falls through). This is what makes A1 hold even with the switch on for NONE decisions (INV-LA-NONE-01).

### 4.1 Phase 4 Generic shield split (`AdaptiveBalancedBot.choose_any_shield_allocation`)

New override; the default path is `super()` (i.e. `BaseBot`'s `msp.default_any_shield_allocation` with `msp.policy_for(self)`).

```python
def choose_any_shield_allocation(self, player_state, remaining, available_any, game_state, attack):
    w = prp.window(self, player_state, game_state)
    if w == prp.NONE:
        return super().choose_any_shield_allocation(player_state, remaining, available_any, game_state, attack)
    return prp.windowed_any_shield_allocation(w, player_state, remaining, available_any, game_state, attack)
```

`windowed_any_shield_allocation`:
1. `pol = PR_PUSH_POLICY if PUSH else DUMP_POLICY`; `fill = PR_PUSH_FILL if PUSH else DUMP_FILL`.
2. `raw = msp.default_any_shield_allocation(player, remaining, available_any, state, attack, pol)` (the greedy marginal-value split; `blue_lethal_value` = 100 beats every Red value in both policies: push Red max = 5 + 3 + 6 + leader bonus term, which is < 100 for any reachable Corporate Secrets; dump Red = −10 + leader term 0 because `leader_bonus_aware=False`).
3. Return `validate_any_shield_allocation(raw, remaining, available_any, fill)` (imported lazily from `sim.engine.phase4_attack_resolution`).

Step 3 is the key: the hook returns an allocation that is **already legal and complete**, so the engine's own legalisation (line ~309), which back-fills with `player.bot.any_shield_fill_order`, is a no-op. That keeps the window's fill order in effect even though `any_shield_fill_order` on the seat (and on a Mixed wrapper or reference seat that mirrored it) is the static AdaptiveBalanced value. Hazard H-LA-2: without step 3 a Mixed or reference seat would back-fill with the wrong order (test LA-07 asserts `validate(out) == out`).

Fill order "Red first" is therefore a tie-break and back-fill order; the greedy value still puts a Total Data Breach Blue block first (INV-LA-LETHAL-01, test LA-08). In dump, Red is blocked only when no Blue or Green remains unblocked, because every shield must block (INV-MS-ANY-SHIELD-01).

Aegis (`choose_aegis_override_market_share`) and Phase 1 `commit_shields` are unchanged.

### 4.2 Phase 6 research and Market Share regain (`research_policy.apply_research_policy`)

AdaptiveBalanced is `research_aware=True`, so its research split is set in post-processing, not in `take_operations_actions` (H2). The window branch therefore goes in `apply_research_policy`, inside the existing `if getattr(bot, "research_aware", True):` block, before `plan_research3`:

```python
w = prp.window(bot, player, state)
if w != prp.NONE and getattr(cfg, "is_share_regain", False):
    focus = policy_for_bot(bot, state, rng).focus_order          # the archetype's own order (fixed for AdaptiveBalanced)
    if w == prp.PUSH:
        p = cfg.bot_pr_push_params
        if (player.patent_level < p.push_pr_cap and player.research_tokens <= p.push_max_research
                and player.research_tokens >= cfg.track_step_costs[player.patent_level]):
            ups, regain = prp.ordered_research(player, state, True, focus, pr_cap=p.push_pr_cap)
        else:
            ups = None                                             # archetype's own order: fall through
    else:
        ups, regain = prp.ordered_research(player, state, False, prp.DUMP_FOCUS_FROM(focus))
    if ups is not None:
        plan.track_upgrades, plan.patent_filings, plan.share_regain = ups, 0, regain
        return plan
# existing plan_research3 path
```

(`PATENT` is the internal key of the Public Relations Track.)

- **Push, step affordable:** one Public Relations Track step (`pr_cap=1` stops at level 1), then Market Share regain at the post-step rate with all remaining Research Tokens up to the cap and room, then the archetype's other tracks with what is left. This is the existing push-line split with a level cap; see OQ-2 for the regain-before-other-tracks order.
- **Push, step not taken** (level ≥ cap, or > 2 tokens, or unaffordable): existing `plan_research3`, including urgent regain, but with `ms_pol = prp.effective_policy(bot, player, state)` = `PR_PUSH_POLICY`, so urgent regain uses the push danger margin. Hazard H-LA-3: passing the bot's static policy here would make "push" only half-applied; the spec requires the windowed policy (test LA-11).
- **Dump:** `ordered_research(pr_first=False, focus)`: the research-policy want-list with the Public Relations Track removed, no regain, nothing else changed. `DUMP_FOCUS_FROM(focus)` is just `focus` (the existing function already drops `PATENT`); listed for clarity, no new constant.

`_ordered_research` gains `pr_cap: int = 4`: `while lv["PATENT"] < pr_cap and buy("PATENT")`. Default 4 = today's loop, so the reference portfolio lines are unchanged (RB parity tests).

### 4.3 Dice buying and the Red purchase nudge

Two places, both windowed:

1. **Raw plan colour order** (`AdaptiveBalancedBot.take_operations_actions`, both the Prometheus discount pool at line ~311 and the market purchase loop at ~410): replace the two `preferred_colors = ...` blocks with `preferred_colors = prp.preferred_colors(self, player_state, game_state, threats)`, which returns the existing threat-based list for NONE, `(RED, BLUE, GREEN, YELLOW)` for PUSH and `(BLUE, GREEN, YELLOW)` for DUMP. The Purple reserve purchase and cash cushion are unchanged.
2. **Red purchase nudge** (`market_share_policy.apply_market_share_policy`): `pol = prp.effective_policy(bot, player, state)` instead of `policy_for(bot)`. PUSH → `red_buy_share_frac 1.0` (nudge whenever below max Market Share); DUMP → `-1.0` (never; `is_critical` with `danger_margin=-1000` is false for share ≥ 1). Ad Campaign use is unchanged in every window (OQ-3).

`effective_policy(bot, player, state)` = `PR_PUSH_POLICY` / `DUMP_POLICY` / `msp.policy_for(bot)` by window. `market_color_preference` (Triage L3 colour pick) is not windowed.

Hazard H-LA-4 (import cycle): `market_share_policy` and `research_policy` must import `pr_push_policy` **lazily inside the function**, and `pr_push_policy` imports `market_share_policy` at module level. `pr_push_policy` must not import `adaptive_balanced`, `mixed_policy`, `reference_search` or `sim.engine` at module level (validate is imported lazily in §4.1).

---

## 5. Reaching Mixed and the reference bot without shared mutable state

### 5.1 Mechanism: one static attribute + the shared config

- `AdaptiveBalancedBot.pr_push_capable = True` (class attribute). `BaseBot.pr_push_capable = False`. Other archetypes inherit False.
- `"pr_push_capable"` is appended to `mixed_policy.PROFILE_ATTRS`. Every wrapper that mirrors a delegate's profile (Mixed, `ReferenceSearchBot`, `ForcedChoiceBot`) then carries the delegate's flag, so the post-processing in §4.2 / §4.3 sees the same flag the delegate has. This is the H2 rule applied to one more attribute.
- The window reads `state.config.bot_pr_push`, which is the same object for every seat and every clone.

Paths:

| Seat | Phase 4 split | Phase 6 raw plan (dice colours) | Phase 6 post-processing (research, nudge) |
|---|---|---|---|
| AdaptiveBalanced baseline seat | own override | own `take_operations_actions` | `bot` is the seat, flag True |
| Mixed, AdaptiveBalanced drawn | delegated hook calls the delegate's override | `raw_operations_plan(delegate)` | wrapper mirrored the delegate's profile (flag True) in `take_operations_actions` before returning |
| Mixed, other archetype drawn | archetype code | archetype code | mirrored flag False → NONE |
| Reference seat, unsearched / fallback | `_candidate(fallback)` → fallback override; already legal (§4.1) | `raw_operations_plan(fallback)` | `_materialise` mirrors `profile_of(fallback)` → True |
| Reference candidate generation | each member's own hook; dedup key from `post_process_operations_plan(member, ...)` with the member as `bot` | member | member (portfolio AdaptiveBalanced variants True; push/dump lines False, §5.2) |
| Rollout seats | live bot objects (stateless, H5), config shared → same windows as live | same | same |
| `ForcedChoiceBot` | fallback via `_candidate` | fallback | mirrors source profile, then each materialise re-mirrors |

User decision 4 (fallback and rollout seats use the new behaviour) holds automatically, with no extra code path.

### 5.2 Portfolio members

- `_ResearchLineBot.pr_push_capable = False`. `PublicRelationsPushBot` and `MarketShareDumpBot` are the fixed lines the window imitates; windowing them again would double-apply (their `research_aware=False` already skips §4.2, but §4.1 and §4.3 would still fire). Test LA-14.
- The 4 focus rotations and the 2 Market Share policy variants are plain `AdaptiveBalancedBot` instances, so they inherit the windows. Inside a window, `red_danger3` and `leader_bonus_unaware` lose their own policy (the window's policy replaces it). Recommended as is: they are "AdaptiveBalanced with a tweak", and the fallback must be AdaptiveBalanced too. OQ-1 offers the alternative (set False on those 6).
- Expected side effect: with the switch on, the fallback often equals the push or dump line inside a window, so those lines are deduplicated more often. That is the intended "absorbed by the roster" signal and is reported (§8 step 5).

### 5.3 Statelessness (INV-LA-STATELESS-01)

- No new instance attribute is written by any lever-A code after `__init__`. `window`, `effective_policy`, `preferred_colors`, `windowed_any_shield_allocation` and `ordered_research` are module functions of `(bot attrs, player, state)`.
- `pr_push_capable` is a class attribute; mirroring writes it on wrappers (as it already writes the other profile attributes). That write is idempotent for a given delegate and is not read across games.
- Test LA-15: `vars(bot)` before and after 1 full game is unchanged for an AdaptiveBalanced seat (except attributes existing code already writes), and a rollout with the switch on leaves the live seats' `vars()` unchanged.
- `fast_clone`: no new state on `GameState` or `PlayerState`, so the clone tables need no change. `config` sharing is safe because `PrPushParams` is frozen and nothing writes `bot_pr_push` after construction (H-LA-5: a test or script that flips `config.bot_pr_push` on a live engine mid-game would also flip it in every clone; forbid it in the sweep script and say so in the docstring).

---

## 6. Parity (INV-LA-PARITY-01)

- **Switch off** (default): byte-identical to `tests/fixtures/v033_parity`, `v034_parity`, `v035_parity`, `v036_parity` (and the v0.37 runs reusing them), and to the reference-bot tests RB-01..RB-14. With the flag off `window()` returns NONE at its first check, every branch falls through, `effective_policy` returns `policy_for(bot)`, and `preferred_colors` returns the exact current lists. The new `choose_any_shield_allocation` override returns `super()` unchanged. Adding a key to `PROFILE_ATTRS` adds one mirrored attribute and changes no plan or dedup key.
- **The moved constants**: `reference_search` re-exports `PR_PUSH_POLICY`, `PR_PUSH_FOCUS`, `PR_PUSH_FILL`, `DUMP_POLICY`, `DUMP_FOCUS`, `DUMP_FILL` and `_ordered_research` from `pr_push_policy` (same objects), so the v0.37 13-member attribution runs reproduce (LA-03: rerun 20 games of `v037_ref1_3p` against the recorded `sim_results` choice counts).
- **New fixtures** `tests/fixtures/v037_push/`: `capture.py` reuses `v036_parity.capture.run_scenario` with `config_factory = lambda **kw: GameConfig.v037(bot_pr_push=True, **kw)`, 300 seeds × 2/3/4P × {mixed, setup}, plus a `ref1_3p.json` of 10 seeds (reference seat present; small because rollouts are slow). Old fixtures are not regenerated.
- When the User promotes the switch to the default for rule probes (User decision 3, after validation), the old fixtures stay pinned by passing `bot_pr_push=False` explicitly in their tests. That flip is a separate change.

---

## 7. Tuning sweep script (`scripts/run_lever_a_sweep.py`)

- Baseline pods (scoping §6 step 3): v0.37, 3P, 600 games per cell, seeds `42 + 300000 + idx`, the `_bot_classes` rotation from `tests/fixtures/v035_parity/capture` (same as `run_reference_bot_validation.py --cells baseline`), `--procs 8`.
- Cells: `off` (switch off), `on` (defaults), then **one-at-a-time** over the scoping §3.3 sweep column:
  - `push_min_share` {5, 6, 7} (5 only with `dump_max_share=4`; the script builds that pair and skips any illegal combination by catching the config `ValueError` and logging it);
  - `push_low_gap` {5, 7, 9}; `push_top_gap` {2, 3, 4}; `push_secrets_band` {2, 3};
  - `dump_max_share` {4, 5};
  - **dump-condition variant**: `dump_condition="reach_or_threat"` × `dump_top_gap` {1, 2, 3} × `dump_threat_margin` {2, 3} (6 cells; these two constants are inert under `share_only`, so they are swept only inside the variant).
  - `push_max_version`, `push_pr_cap`, `push_max_research` fixed.
  - Total: 2 + 3 + 3 + 3 + 2 + 2 + 6 = 21 cells (duplicates of `on` collapse; ~19 runs).
- Each task carries a fully built `GameConfig` (pickled); the script never mutates a config after construction (H-LA-5).
- Output: `sim_results/lever_a/sweep_3p_600.json`, one row per cell: `dataclasses.asdict(params)`, `dump_condition`, AdaptiveBalanced win % (with 95% Wilson CI), per-archetype win %, ending mix (Patient Zero / Singularity / Market Collapse %, Total Wipeout %), average rounds, and per-AdaptiveBalanced-seat window telemetry (decisions in PUSH / DUMP / NONE, by hook). Telemetry is counted in the script through a wrapping hook on `pr_push_policy.window` installed per worker (read-only counter, like `run_reference_bot_validation._install_hook`), never in sim code.
- Selection rule: highest AdaptiveBalanced win %, subject to the §8 step 2 guardrails; ties (CI overlap) keep the scoping default. The chosen cell becomes the `PrPushParams` default only after User sign-off (OQ-4).

---

## 8. Validation plan (scoping §6)

Harness `scripts/run_reference_bot_validation.py`, extended with `--pr-push {off,on}` and `--pr-params <json>` (both forwarded into `GameConfig.v037(...)` / `v036(...)` in `build_engine`), seeds `42 + 300000 + idx`.

1. **Parity:** LA-01..LA-03 (off = all old fixtures; on = `v037_push`).
2. **Baseline endings shift**, 2/3/4P, 1,200 games, off vs on: Patient Zero / Singularity / Market Collapse %, average rounds, Total Wipeout %. Guardrail: Patient Zero and Total Wipeout each up by at most 2 points.
3. **Constant sweep** (§7), then rerun step 2 at the chosen cell if it differs from the defaults.
4. **Archetype win spread** (baseline 3P/4P): per-archetype win %, AdaptiveBalanced up, no archetype above ~40% at 3P, and the other four distinct (focus order and Red/Blue/Green block shares do not converge; compare each archetype's block-colour shares with v0.37 off).
5. **ref1 edge** (3P 1,200, 2P/4P 600): 13-member and 11-member portfolios, off vs on. Report ref win %, Market Leader Bonus 1st %, ref at 0 Market Share when Market Collapse triggers, Red share of blocks, push and dump line choice share and distinct share. Expectation (estimate, scoping §7): 78.6% → ~70–75%.
6. **Mixed seat** (mixed1, 2/3/4P 1,200): within ±3 points of 1/N.
7. **v0.36 spot check:** 3P baseline 600 games, off vs on (the switch must also work under `v036()`, where the Market Leader Bonus is off).
8. Record in FINDINGS.md as a new section; update PLAN.md checkboxes. No RULES.md change (bot-only).

---

## 9. Invariants

| ID | Invariant |
|---|---|
| INV-LA-PARITY-01 | `bot_pr_push=False` reproduces every existing parity fixture and RB test byte-for-byte. |
| INV-LA-NONE-01 | With the switch on, a decision in window NONE returns exactly what the switch-off code returns. |
| INV-LA-RNG-01 | Window evaluation and every windowed helper consume no RNG (live `engine.rng.getstate()` unchanged across the call). |
| INV-LA-DISJOINT-01 | `PUSH_MIN_SHARE > DUMP_MAX_SHARE` at config construction; no state is ever in both windows. |
| INV-LA-LETHAL-01 | In every window, if a Generic shield can stop a Total Data Breach from Blue, it is allocated to Blue. |
| INV-LA-LEGAL-01 | The windowed Phase 4 allocation is already legal and complete (`validate(out) == out`). |
| INV-LA-STATELESS-01 | No lever-A code writes bot instance state after `__init__` beyond existing profile mirroring. |
| INV-LA-SCOPE-01 | Only AdaptiveBalanced instances (and wrappers mirroring one) are affected; other archetypes and the push/dump lines are unchanged with the switch on. |

---

## 10. Test matrix (`tests/test_lever_a_pr_push.py`)

| ID | Test |
|---|---|
| LA-01 | Switch off: v033/v034/v035/v036 parity fixtures replay identically (existing tests run unchanged; add one explicit call with `bot_pr_push=False`). |
| LA-02 | Switch on: `v037_push` fixtures (300 seeds × 2/3/4P × {mixed, setup}) and `ref1_3p.json` replay identically. |
| LA-03 | Moved constants: `reference_search.PR_PUSH_POLICY is pr_push_policy.PR_PUSH_POLICY` (all six + `_ordered_research`); `_ordered_research(..., pr_cap=4)` equals the old function on 200 random player states; RB-01..RB-14 pass. |
| LA-04 | Config: `PUSH_MIN_SHARE <= DUMP_MAX_SHARE` raises `ValueError`; `(5, 4)` legal; bad `dump_condition` raises; `GameConfig() == GameConfig.v037()` still true; `PrPushParams` is frozen. |
| LA-05 | `window` table: hand-built states for each condition boundary (share 5/6, low gap 7/8, top gap 3/4, version index 1/2, Secrets lead ±2/±3), Patient Zero rivals excluded, sole survivor → NONE, RANSOM / NAIVE / switch off / `pr_push_capable=False` → NONE. |
| LA-06 | Dump variant: `reach_or_threat` returns DUMP only with gap ≤ −`DUMP_TOP_GAP` or threat; `share_only` returns DUMP for every share ≤ 5. |
| LA-07 | Phase 4 legality: for random `remaining` / `available_any` in PUSH and DUMP, `validate_any_shield_allocation(out, ...) == out` with the seat's static fill order (INV-LA-LEGAL-01). |
| LA-08 | Lethal Blue first: Corporate Secrets 1, Blue 1 + Red 3 remaining, 1 Generic shield, PUSH → Blue 1; DUMP same. |
| LA-09 | Push fill: no lethal Blue, Red and Blue remaining, PUSH → Red receives the shields the greedy values give it, back-fill Red first. DUMP → Red receives shields only when Blue and Green are exhausted. |
| LA-10 | Phase 6 push: level 0, 2 tokens, step cost ≤ 2 → `track_upgrades == ["PATENT"]` then regain; level 1 or 3 tokens → equals switch-off `plan_research3` except `ms_pol` is `PR_PUSH_POLICY`. |
| LA-11 | Phase 6 push fall-through uses `PR_PUSH_POLICY` for urgent regain (H-LA-3). |
| LA-12 | Phase 6 dump: no `PATENT` in `track_upgrades`, `share_regain == 0`; no Red in `market_purchases`; nudge never adds Red. Push: purchase order starts with Red; nudge active below max Market Share. |
| LA-13 | Mixed: with AdaptiveBalanced drawn for phase4 and phase6, every Phase 4 split and final Phase 6 plan equals a plain AdaptiveBalanced seat's on the same state (extends RB-04); with SecOpsTurtle drawn, equals switch-off. |
| LA-14 | Reference: fallback candidate equals AdaptiveBalanced's windowed choice; `PublicRelationsPushBot` / `MarketShareDumpBot` candidates identical with switch on and off (INV-LA-SCOPE-01). |
| LA-15 | Statelessness: `vars()` of AdaptiveBalanced, Mixed and reference seats unchanged by lever-A code over a full game; a rollout with the switch on leaves live seats and live state unchanged (RB-01 style). |
| LA-16 | RNG: H1-style guard: `engine.rng.getstate()` unchanged across `window`, Phase 4 override and Phase 6 post-processing in a windowed state; reference candidate generation guard (RB-05) passes with the switch on. |
| LA-17 | Determinism: switch on, 3P ref1, 3 seeds, 1 proc vs 4 procs identical results. |
| LA-18 | Other archetypes: Accelerationist, RecklessSaboteur, SecOpsTurtle, VentureGreed seats in a 4P game make identical decisions with switch on and off when they are the only non-AdaptiveBalanced seat state differences (compare a pod with no AdaptiveBalanced seat: whole game identical). |
| LA-19 | Sweep script smoke: 2 cells × 4 games runs, writes `asdict(params)` per row, and skips the illegal `(push_min_share=5, dump_max_share=5)` pair with a logged reason. |

---

## 11. Hazards found

| ID | Hazard | Mitigation |
|---|---|---|
| H-LA-1 | Patient Zero rivals keep stale Market Share and would distort `lo` / `hi`. | Survivors-only filter (§3.1, LA-05). |
| H-LA-2 | The engine back-fills Generic shields with the seat's **static** `any_shield_fill_order`; Mixed and reference seats carry the mirrored static value, so a window fill order set by attribute would be lost or would require mutable state. | Windowed hook returns an already-legal allocation (§4.1, LA-07). |
| H-LA-3 | AdaptiveBalanced's Phase 6 research is set in post-processing (H2). Windowing only `take_operations_actions` would be overwritten; windowing only the research split but passing the static policy to `plan_research3` / the nudge would half-apply push. | Window branch in `apply_research_policy` and `effective_policy` in both post-processing functions (§4.2–4.3, LA-10..12). |
| H-LA-4 | Import cycle: `reference_search` imports `adaptive_balanced`; AdaptiveBalanced needs the line constants and `_ordered_research`. | Move them to leaf module `pr_push_policy.py`; re-export from `reference_search`; lazy imports from the policy modules (§4.3). |
| H-LA-5 | `fast_clone` shares `config`; mutating it mid-game changes every clone. | Frozen params; the switch is set only at construction; sweep script builds a new config per cell. |
| H-LA-6 | `PublicRelationsPushBot` / `MarketShareDumpBot` subclass AdaptiveBalanced and would inherit the window (double-apply). | `_ResearchLineBot.pr_push_capable = False` (LA-14). |
| H-LA-7 | Portfolio dedup: with the switch on the fallback equals the push/dump line more often, so per-line choice shares from §40 are not directly comparable. | Report distinct share alongside choice share (§8 step 5). |
| H-LA-8 | Phase 4 window uses mid-phase Market Share (earlier seats' Red already resolved, and the seat's own earlier Red in this resolution), while the scoping log measured state at the Phase 4 snapshot. | Accept (live value is what a player sees); note in FINDINGS; LA-05 fixes the semantics. See OQ-5. |

---

## 12. Open questions for the User

1. **Portfolio AdaptiveBalanced variants** (4 focus rotations, `red_danger3`, `leader_bonus_unaware`): inherit the windows with the switch on (recommended; they are AdaptiveBalanced and the fallback is too), or opt out so the portfolio keeps its §40 meaning?
2. **Push research order:** after the one Public Relations Track step, regain first and then the other tracks (the existing push line's order, recommended, reuses its code), or the archetype's other tracks first and regain from leftovers?
3. **Ad Campaign in the dump window:** keep using it whenever affordable (unchanged, recommended for scope), or stop spending Money on Market Share at ≤ 5 too?
4. **Sweep result adoption:** if the sweep picks a cell other than the scoping defaults, may it become the `PrPushParams` default directly, or does it come back for sign-off first (recommended)?
5. **Phase 4 window timing:** evaluate on live Market Share at the call (recommended, simplest and stateless), or on Market Share at the start of Phase 4 (`state.phase4_market_share_start`), which matches the scoping log more closely?
6. **Prometheus discount colour:** apply the windowed colour order to the Prometheus discounted purchase as well as normal market purchases (recommended, one helper), or only to normal purchases?

## Open Question Resolutions (User, 2026-11-07)

1. The 6 portfolio AdaptiveBalanced variants **inherit** the windows (the line bots `PublicRelationsPushBot` / `MarketShareDumpBot` stay `pr_push_capable = False`, H-LA-6).
2. Push research order: Public Relations Track step (≤ `PUSH_PR_CAP`), then **Market Share regain before other tracks**.
3. Ad Campaign is **unchanged** in the dump window.
4. Sweep-picked constants that differ from the starting values **come back to the User** before becoming defaults.
5. The Phase 4 window reads Market Share **at the start of Phase 4** (snapshot), matching how the thresholds were measured (H-LA-8). This overrides the spec's earlier recommendation of live Market Share.
6. The windowed colour order **also applies** to the Prometheus discounted purchase.
