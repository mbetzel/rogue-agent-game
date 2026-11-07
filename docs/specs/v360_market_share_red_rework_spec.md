# Technical Architecture Specification: Phase 45 (v0.36.0)
## Red Rework: Market Share, Market Collapse, Public Relations Track, Marketing ★ Variants & Free-Choice Generic Shields

**Author:** Principal Engineer / Architect
**Status:** Approved for implementation. The §15 open questions were resolved by the User on 2026-11-06 (see §15.1).
**Target Version:** `v0.36.0` candidate
**Source of Truth:** [`docs/explorations/2026_11_market_share_red_rework_plan.md`](../explorations/2026_11_market_share_red_rework_plan.md). Sections 3, 5, 6, 7 and 8 were locked by the User on 2026-11-06. Evidence: `FINDINGS.md` §31 and §32, and the probe `scripts/explore_v360_market_collapse_probe.py`, which is hooks only and not a reference implementation.
**Dependencies:** `RULES.md` v0.35.0 (§2, §3 Phases 2/3/4/6, §5, §6A/6B/6D, §7), `PLAN.md` Phase 45 and §2, [v350 spec](./v350_research_track_rebalance_spec.md).
**Target Components:**
- `sim/config.py`, `sim/entities.py`, `sim/engine/state.py`, `sim/engine/core.py`, `sim/engine/end_game.py`
- `sim/engine/phase2_compiler.py` (Version comparison), `phase3_income.py` (R2/R3 latch, R3 resolution), `phase4_attack_resolution.py` (Red → Market Share, Stage 2 free choice, Market Collapse check), `phase6_operations.py` (regain replaces Patent Filing, R2, purchase counters), `research_tracks.py` (Public Relations Track)
- New: `sim/engine/market_share.py`, `sim/bots/market_share_policy.py`
- `sim/bots/base.py`, `sim/bots/research_policy.py`, all 5 bot subclasses (attributes only)
- `sim/experiments.py`
- New: `tests/test_v360_market_share.py`, `tests/fixtures/v035_parity/`, `scripts/run_v360_market_share_sweep.py`
- Phase B, after balance sign-off: `web/`, `pnp/`, `RULES.md`, `CLAUDE.md`

> Line numbers are from the current working tree: HEAD `b1b1f11` plus the uncommitted Phase 44 diff. §2.6 changes `phase6_operations.py` and `research_tracks.py`, so re-check line numbers before editing.

---

## 1. Executive Summary

### 1.1 What changes (all behind levers; defaults stay v0.35.0)

| # | Change | Plan ref |
|---|---|---|
| C1 | Each **unblocked Red cube** (Market Manipulation) lowers that player's **Market Share** by 1. Red no longer costs Money or Secrets. The Unpaid Ransom Leak is removed. | §3.1 |
| C2 | A Market Share track per player. **Start = max = 19 / 20 / 20** (2P / 3P / 4P) `[TUNE]`. Floor 0. | §3.2 |
| C3 | The **Public Relations Track** replaces Cryptographic Patents. Same step costs 1/2/2/3 🔬. L1 Breakthrough is `$3`; L3 Breakthrough is the 2nd Purple die. In Phase 6, regain Market Share at `2 🔬` per +1, with a per-round cap of 1/1/2/2/3 by level `[TUNE]`. The L4 rate is a lever. **Patent Filing is removed.** | §3.3 |
| C4 | A **Version comparison** in Phase 2, right after the final space of `v1.0` (`$2`) or `v2.0` (`$4`) is covered and resolved. The highest Market Share gains the payout from the bank. The lowest pays the bank what they can, and any shortfall is forgiven. Ties share places. No comparison at `v3.0` or at game end. | §3.4 |
| C5 | **Market Collapse**: checked at the end of Phase 4. Any surviving player at 0 Market Share makes this round the Final Round. Nobody is eliminated and there is no penalty. New `EndGameReason.MARKET_COLLAPSE`. | §3.5 |
| C6 | Tiebreakers: **Market Share > Money > Active Colored Module Dice in Ready for Release > Research Tokens > fewest Under Development > shared**. The same order ranks a Total Wipeout. | §3.4, §8.3 |
| C7 | **Stage 2 Generic (`Any`) shields are the player's free choice.** The printed 4-tier priority is removed. Bots get a policy hook. | §3.1, §8.6 |
| C8 | The Red die becomes **Marketing** (faces unchanged). New Red ★ set: R1 Block 1 Red + `$2` (renamed), R2 pay `$2` → +1 Market Share, R3 move 1 Market Share from the rival with the most. Threat Bounty and Short Squeeze are retired from this set. | §3.6, §8.7 |
| C9 | Starting Secrets **8 / 10 / 11** (existing lever `starting_secrets_by_player_count`). | §3.7 |
| C10 | DTO *Slush Fund* absorbs Blue Secret loss only. Under `MARKET_SHARE` this follows automatically, because Red causes no Secret loss. | §3.8 |
| C11 | Red-aware bot policy: Generic shield allocation, regain, Public Relations focus, R2/R3 use, and a Red purchase nudge. | §5 |
| C12 | Telemetry: Market Share curves, regain spend, comparisons, Red block rate, Red purchases, end-reason split by setup, `end_triggers`, tiebreak attribution. | §5, §6 |

Unchanged: Red die faces (`Block 1 Red`, `+$2` ×3, `Glitch`, `Red ★`), Snowball Recycle, Defense Grid L4 (`+$1` per blocked cube, Red included), all other tracks and Breakthroughs, Blue/Green/Yellow variants, Purple faces, the six-phase round, `$6` start, purchase limit 2.

### 1.2 Public Relations Track (replaces Cryptographic Patents; internal key stays `"PATENT"`)

| Level | Step cost to reach | Effect `[TUNE]` |
|---|---|---|
| L0 | – | Phase 6: regain up to **+1** Market Share at **2 🔬** each |
| L1 (Breakthrough) | 1 🔬 | Gain `$3`; cap +1 |
| L2 | 2 🔬 | Cap **+2** |
| L3 (Breakthrough) | 2 🔬 | Gain your 2nd Purple die from the Personal Reserve; cap +2 |
| L4 | 3 🔬 | Cap **+3** at 2 🔬 each (default). Cost is a lever; see sweep cells L4-RATE / L4-BOTH. |

### 1.3 Comparison v0.35.0 vs v0.36.0

| Item | v0.35.0 | v0.36.0 |
|---|---|---|
| Unblocked Red | `$1` per cube; any shortfall → 1 Secret | −1 Market Share per cube |
| 4th track | Cryptographic Patents (filing for Secrets) | Public Relations Track (regain Market Share) |
| Money from Version changes | none | `$2` / `$4` bank payout/charge at v1.0 / v2.0 fill |
| End triggers | Patient Zero, Singularity, Total Wipeout | + Market Collapse |
| First tiebreaker | Money | Market Share |
| Stage 2 `Any` | fixed 4 tiers | player's free choice |
| Red ★ | R1 Ransom Insurance, R2 Threat Bounty, R3 Short Squeeze | R1 (renamed), R2 buy back share, R3 poach share |
| Starting Secrets | 8 / 8 / 8 | 8 / 10 / 11 |

---

## 2. Configuration (`sim/config.py`)

### 2.1 New enums

```python
class EndGameReason(str, Enum):      # add one member (config.py:38-43)
    ...
    MARKET_COLLAPSE = "market_collapse"

class RedMode(str, Enum):            # master switch
    RANSOM = "RANSOM"                # v0.35.0 (default)
    MARKET_SHARE = "MARKET_SHARE"    # v0.36.0

class PatentsMode(str, Enum):
    PATENTS = "PATENTS"              # v0.35 Cryptographic Patents + Patent Filing
    SHARE_REGAIN = "SHARE_REGAIN"    # Public Relations Track

class RedVariantSet(str, Enum):
    V035 = "V035"                    # R1 Ransom Insurance, R2 Threat Bounty, R3 Short Squeeze
    MARKETING = "MARKETING"          # R1 / R2 / R3 per §3.3

class TiebreakOrder(str, Enum):
    V035 = "V035"                    # Secrets > Money > ...
    MARKET_SHARE_FIRST = "MARKET_SHARE_FIRST"

class AnyShieldPolicy(str, Enum):
    V035_TIERS = "V035_TIERS"        # engine 4-tier priority (phase4:265-288)
    FREE_CHOICE = "FREE_CHOICE"      # bot hook / web allocation
```

### 2.2 New `GameConfig` fields (after `config.py:248`)

| Field | Type / default | Resolves (when `None`) from `red_mode` | v036 value |
|---|---|---|---|
| `red_mode` | `RedMode = RANSOM` | master | `MARKET_SHARE` |
| `market_share_start_by_player_count` | `Dict[int,int] = {2:19, 3:20, 4:20}` `[TUNE]` | – (not read under RANSOM) | same |
| `market_collapse_enabled` | `Optional[bool] = None` | `red_mode == MARKET_SHARE` | `True` |
| `version_share_payout` | `Optional[Dict[str,int]] = None` | `{}` (RANSOM) / `{"v1.0": 2, "v2.0": 4}` | `{"v1.0": 2, "v2.0": 4}` `[TUNE]` |
| `patents_mode` | `Optional[PatentsMode] = None` | `PATENTS` / `SHARE_REGAIN` | `SHARE_REGAIN` |
| `share_regain_cost_by_level` | `Dict[int,int] = {0:2,1:2,2:2,3:2,4:2}` `[TUNE]` | – | same (L4 cost is the open lever) |
| `share_regain_cap_by_level` | `Dict[int,int] = {0:1,1:1,2:2,3:2,4:3}` `[TUNE]` | – | same |
| `red_variant_set` | `Optional[RedVariantSet] = None` | `V035` / `MARKETING` | `MARKETING` |
| `r2_share_cost` / `r2_share_gain` | `int = 2` / `int = 1` `[TUNE]` | – | same |
| `r3_poach_amount` | `int = 1` | – | same |
| `tiebreak_order` | `Optional[TiebreakOrder] = None` | `V035` / `MARKET_SHARE_FIRST` | `MARKET_SHARE_FIRST` |
| `any_shield_policy` | `Optional[AnyShieldPolicy] = None` | `V035_TIERS` / `FREE_CHOICE` | `FREE_CHOICE` |
| `starting_secrets_by_player_count` | existing | not tied to `red_mode` | `{2:8, 3:10, 4:11}` `[TUNE]` |
| `market_share_bot_policy` | `str = "AWARE"` (sim-only) | – | `"AWARE"`; `"NAIVE"` is the ablation cell |

`__post_init__` changes:
1. Coerce `red_mode` and the four enum sub-flags, like `research_track_model`.
2. Resolve each `None` sub-flag once. As in v0.35, re-assigning `red_mode` later does **not** re-resolve.
3. **Validation** (raise `ValueError`):
   - `red_mode == MARKET_SHARE` with `round_sequence == V033_THREE_PHASE` (not supported on the legacy path).
   - `patents_mode == SHARE_REGAIN`, `market_collapse_enabled`, non-empty `version_share_payout`, or `tiebreak_order == MARKET_SHARE_FIRST` under `red_mode == RANSOM` (meaningless without Market Share).
   - `share_regain_*` maps missing any level 0–4.

   `any_shield_policy = FREE_CHOICE` is allowed under RANSOM (useful to isolate the bot heuristic). `red_variant_set = MARKETING` is allowed under RANSOM only for the R1 rename (R2/R3 are inert without Market Share). Document this and do not raise.
4. `red_ransom_per_cube` (Phase 44, kept per §2.6) is read only under RANSOM.

### 2.3 Constructors and properties

```python
@classmethod
def v036(cls, **overrides) -> "GameConfig":
    """v0.36.0 candidate: Market Share Red, Public Relations Track, Market Collapse, 8/10/11 Secrets."""
    overrides.setdefault("red_mode", RedMode.MARKET_SHARE)
    overrides.setdefault("starting_secrets_by_player_count", {2: 8, 3: 10, 4: 11})
    return cls(**overrides)

@classmethod
def legacy_v035(cls, **overrides) -> "GameConfig":
    """v0.35.0 baseline (today's defaults). Exists now so the parity test survives a later default flip."""
    overrides.setdefault("red_mode", RedMode.RANSOM)
    overrides.setdefault("starting_secrets_by_player_count", {2: 8, 3: 8, 4: 8})
    return cls(**overrides)
```

- `legacy_v034()` and `legacy_v033()` add `overrides.setdefault("red_mode", RedMode.RANSOM)`.
- Properties: `is_market_share` (`red_mode == MARKET_SHARE`), `is_share_regain` (`patents_mode == SHARE_REGAIN`).
- `market_share_start(n=None) -> int`: lookup with fallback `.get(4, 20)`.
- **Defaults are not flipped in this phase.** `GameConfig()` stays v0.35.0 until the game-designer and User sign off. Flipping is a one-line follow-up, and `legacy_v035()` is already in place for it.

### 2.4 Lever-to-plan mapping (plan §5)

All plan §5 levers are covered: `red_mode`, `market_share_start_by_player_count`, `market_collapse_enabled`, `version_share_payout`, `share_regain_cost_by_level` / `share_regain_cap_by_level`, `patents_mode`, `starting_secrets_by_player_count`, `red_variant_set`, `tiebreak_order`, `any_shield_policy`. Added levers: `r2_share_cost`, `r2_share_gain`, `r3_poach_amount`, `market_share_bot_policy`.

### 2.5 Parity fixtures (do this first, before any v0.36 code)

1. **Capture `tests/fixtures/v035_parity/` from a clean checkout of HEAD `b1b1f11`.** Use `git worktree`; the working tree has the Phase 44 diff. Use the v034 harness (`tests/fixtures/v034_parity/capture.py`): 300 seeds × 2/3/4P, factory `GameConfig`.
2. Scenarios: `mixed` and `asym` (as in v034), plus a new **`setup`** scenario. The v034 scenarios use the default variant cards (Red = R1 only), so they never exercise the V035 R2/R3 Phase 4 bonuses or the Tier 2 ransom check. `setup` does:
   - seeded `random.Random(seed)` → `get_random_setup(rng, "STANDARD")`, `get_random_companies`, `get_random_white_hats`;
   - the same bot rotation as `scripts/run_v360_red_rebalance_sweep.py::build_engine`.
3. Record what v034 records: `EndGameResult` summary, rankings with `RANKING_KEYS`, and per-round staged/exited/attack cubes. Also record per-round `phase_snapshots[4]` money/secrets, which catches ransom drift.
4. After the refactor, both `GameConfig()` and `GameConfig.legacy_v035()` must reproduce `v035_parity` exactly (**INV-MS-LEGACY-PARITY-01**). `v034_parity` (`legacy_v034`) and `v033_parity` (`legacy_v033`) must still pass.
5. Also verify that the working tree *with* the kept `red_ransom_per_cube` lever (default 1) matches the clean-HEAD capture. This proves the Phase 44 lever is bit-identical.

### 2.6 Decision on the uncommitted Phase 44 levers

| Lever | Decision | Reason |
|---|---|---|
| `red_ransom_per_cube` (config.py:247; phase4:273, 311-314) | **Keep (build on it).** Commit as a RANSOM-only experiment lever, default `1`. | Bit-identical at default. `scripts/explore_v360_market_collapse_probe.py` (the §32 evidence) needs `red_ransom_per_cube=0` to reproduce. Ignored under `MARKET_SHARE`. |
| `red_die_profile` / `V036_RED` faces (config.py:248; entities.py:1225, 1260-1276; phase6:142, 254; research_tracks.py:214) | **Revert.** Remove the field, the `red_profile` kwarg, and the `V036_RED` branch. | §31 was not adopted, and v0.36 keeps the Red faces unchanged (plan §3.6). Keeping a dead face profile risks confusion with the Marketing die. |
| `scripts/run_v360_red_rebalance_sweep.py` | Delete the `REDDIE` / `PACKAGE` configs. Add a header note: "archived; §31 results in `sim_results/v360_red_rebalance_sweep.json`". | It would otherwise break once `red_die_profile` is gone. The probe imports its `build_engine` / `_resolve_hook`, which still work. |
| `PLAN.md` Experiment 8 row and `FINDINGS.md` §31/§32 edits | Keep (docs). | |

---

## 3. Entities (`sim/entities.py`)

### 3.1 Red ★ Marketing variants (proposed defaults; names and costs are open, OQ-1)

Add three cards to `get_all_variant_cards()` (entities.py:242-468). **Internal codes are distinct** so that no star-code-keyed branch (phase4:301-305, phase3 `_STAR_NOTES`, bots, web) can fire a retired effect by accident. Add `display_code: Optional[str] = None` to the frozen `VariantCard` (entities.py:184-193) for the printed label.

| Internal code | Printed | Proposed name | Cost | Star face | Timing |
|---|---|---|---|---|---|
| `R1` (unchanged object, new name under MARKETING) | R1 | *Brand Protection* | `$5` | `Block 1 Red` + `+$2` (identical to today) | Defense + Phase 3 income |
| `R2_MKT` | R2 | *Ad Campaign* | `$4` | no Phase 3 output; earns one paid action: **pay `$2` in Phase 6 → +1 Market Share** | Phase 3 latch (die must be In Production in Phase 3), Phase 6 spend |
| `R3_MKT` | R3 | *Customer Poaching* | `$5` | Phase 3: **move 1 Market Share from the rival with the most Market Share to you** | Phase 3, after all income (§4.4) |

- The R1 rename is display-only: `name` / `description` come from `red_variant_set`. Under MARKETING, build R1 as a new `VariantCard` with the same `code="R1"`, the same `star_face` fields, and a new name.
- `get_all_variant_cards(red_variant_set="V035")` returns the 15 v0.35 cards. `"MARKETING"` returns them with the Red trio replaced, keeping list order `R1, R2_MKT, R3_MKT`.
- **RNG-preserving mapping (INV-MS-RNG-02).** Add `resolve_variant_cards(variant_cards, red_variant_set) -> Dict[DieColor, VariantCard]`, called in `GameEngine.__init__` (core.py:86). Under MARKETING it maps a Red card by code: `R1→R1 (renamed)`, `R2→R2_MKT`, `R3→R3_MKT`. Existing sweep scripts that draw with `get_random_setup(rng)` therefore get the same draws in every cell, so the cells stay seed-paired. `get_random_variant_cards` itself is unchanged: 3 Red candidates means the same `rng.choice` consumption.
- `sim/experiments.py:387` / `:415`: the code lists accept `R2_MKT` / `R3_MKT` under MARKETING.

### 3.2 Static descriptions

- The DTO *Slush Fund* description strings (entities.py:842, 941) say "from Blue Spyware or unpaid Red Ransom". Under MARKETING / MARKET_SHARE the web shows "from Blue Spyware". Implement this as a description function, or update the text at Phase B when RULES changes; the sim does not read it.
- The `_STAR_NOTES["R1"]` label (phase3_income.py:27) uses the card's `name`.

### 3.3 Red die label

There is no sim attribute for the Red die label. The "Marketing" subtitle is a web/PnP/RULES change only (Phase B).

---

## 4. State and Engine Module Contracts

### 4.1 `PlayerState` additions (`state.py:208-221` init block)

```python
# v0.36.0 Market Share (None under RedMode.RANSOM)
market_share: Optional[int] = None
market_share_max: Optional[int] = None
market_share_lost_red: int = 0           # actual decrease from Red (after floor clamp)
market_share_red_overflow: int = 0       # unblocked Red beyond the floor (telemetry only)
market_share_lost_poach: int = 0         # R3 taken from this player
market_share_gained_poach: int = 0
market_share_regained: int = 0           # +1 steps bought with research
market_share_gained_r2: int = 0
market_share_min: Optional[int] = None   # lowest value seen
research_spent_regain: int = 0
regain_this_turn: int = 0                # reset at the start of each Operations Turn
r2_actions_available: int = 0            # earned in Phase 3, spent/cleared in Phase 6
r2_uses: int = 0
comparison_money_gained: int = 0
comparison_money_paid: int = 0
comparison_shortfall_forgiven: int = 0
red_incoming_total: int = 0              # effective Red attack after Baffle Echo
red_blocked_color_total: int = 0
red_blocked_any_total: int = 0
purchases_by_color: Dict[str, int]       # Central Market purchases incl. Algorithmic Arbitrage; excl. Triage L3
```

- **Initialisation (core.py:164-188).** If `config.is_market_share`: `market_share = market_share_max = market_share_min = config.market_share_start(n)`.
- `purchases_by_color` and the `red_*` totals are recorded under **both** modes. They are telemetry-only and do not change behaviour, so a v0.35 baseline comparison is possible.
- Helper `PlayerState.change_market_share(delta: int, source: str) -> int` applies the delta, clamps to `[0, market_share_max]`, updates the ledgers and `market_share_min`, and returns the actual change. All Market Share changes go through it (**INV-MS-LEDGER-01**).
- **Research ledger** (INV-RT-RESEARCH-LEDGER-01 extended): `starting + earned − lost − spent_tracks − spent_patents − spent_regain == research_tokens`.
- **`file_patent()` (state.py:440).** Return `False` without changing state when `config.is_share_regain` (**INV-MS-NO-PATENT-01**). `get_patent_cost()` keeps working for old callers.

### 4.2 `GameState` additions (`state.py:911-962`)

```python
version_comparisons: List[VersionComparisonRecord]
version_comparisons_done: Set[str]          # completed version strings ("v1.0", "v2.0"); once-guard
market_collapse_triggered: bool = False
market_collapse_round: Optional[int] = None
market_collapse_pids: List[int]
end_triggers: List[str]                     # ordered, e.g. ["patient_zero", "market_collapse"]
r3_events: List[Dict[str, Any]]             # {"round","actor","target","moved","reason"}
double_version_fill_events: int = 0         # see §4.3 note
```

```python
@dataclass
class VersionComparisonRecord:
    version: str                  # completed version: "v1.0" | "v2.0"
    round_number: int
    payout: int
    during_spillover: bool
    eligible_pids: List[int]
    shares: Dict[int, int]
    money_before: Dict[int, int]
    top_pids: List[int]
    bottom_pids: List[int]
    gains: Dict[int, int]         # bank → player
    paid: Dict[int, int]          # player → bank
    forgiven: Dict[int, int]
    all_tied: bool
    def as_dict(self) -> Dict[str, Any]: ...
```

Also add `end_triggers.append(...)` calls to the existing Patient Zero, Singularity and Total Wipeout sites (phase2_compiler.py:387-405, phase4:501-513). These are telemetry only, so parity holds.

### 4.3 Phase 2: Version comparison (`phase2_compiler.py`, new `sim/engine/market_share.py`)

```python
def resolve_version_comparison(engine, completed_version: str, during_spillover: bool) -> Optional[VersionComparisonRecord]
```

**Hook points in `execute_compiler_drop`:**
- **Normal branch (phase2_compiler.py:340-347).** In the `else:` arm (not the last version), after `_resolve(curr_track[space_idx - 1])` has run for the final space and **before** `state.pending_version_advance = True`, call `resolve_version_comparison(engine, state.active_version.version_str, False)`.
- **Spillover branch (phase2_compiler.py:348-361).** After `_resolve(next_ver.corruption_track[spill_idx - 1])`, if `next_ver_idx < len(deck) - 1 and spill_idx == next_ver.track_capacity`, call `resolve_version_comparison(engine, next_ver.version_str, True)` and `state.double_version_fill_events += 1`.
- Never for the last version (Singularity) and never at game end (**INV-MS-CMP-TIMING-01**).

**Contract** (no-op unless `config.is_market_share` and `version_share_payout.get(version)`):
1. **Once-guard.** If `version in state.version_comparisons_done`, return `None`. Otherwise add it.
2. **Eligible players:** not `is_patient_zero` at this moment. That excludes anyone breached earlier in this Phase 2, including by the final space itself, since that space resolves first (**INV-MS-CMP-ELIG-01**).
3. If fewer than 2 eligible, or all eligible shares are equal: `all_tied=True`, no Money moves (**INV-MS-CMP-TIES-01**).
4. Otherwise `hi = max(shares)`, `lo = min(shares)`. Each player at `hi` gets `money += payout` from the bank. Each player at `lo` pays `paid = min(money, payout)` and `forgiven = payout − paid`. Players never pay each other, Money never goes below 0, and no Secrets are lost (**INV-MS-CMP-BANK-01**).
5. Process players in seat order. The order cannot change outcomes, but it keeps logs stable. No RNG.
6. Append the record, update the player ledgers, and stash it on `CompileResult.version_comparisons` (new field) for web/telemetry.

**Ordering versus other Phase 2 effects (normative):**
1. The final space's printed effect (Lose `$`, Glitch, Return Colored Dice, Lose Secrets, Add Cubes) and any Patient Zero marking it causes.
2. The comparison, using **pre-income Money** and current Market Share. Market Share cannot change in Phase 2.
3. Spillover spaces, in order.
4. The legacy P2 Chaos Profiteer bonus (phase2:363).
5. `check_end_triggers_after_compiler`.

If Singularity fires later in the same compile (only possible on the last version), the comparison already paid stays paid.

**Two versions filled in one compile.** The rules allow two comparisons in sequence: `$2` after v1.0's final space, then v2.0's spillover spaces, then `$4` when v2.0's final space is covered. The hooks above deliver exactly that.
- **Known pre-existing engine limitation (out of scope, parity):** when spillover fills v2.0 completely, today's engine neither advances to v3.0 nor spills further cubes onto v3.0. Cubes past v2.0's capacity are counted but not resolved, and the v3.0 advance waits for a later Black cube.
- Do not fix this under defaults. The once-guard stops a second v2.0 comparison when that delayed advance later hits `corruption_track >= capacity` in the normal branch. `double_version_fill_events` is reported in the sweep; if it exceeds ~0.1% of games, open a separate fix.

Buffer Overflow means no Black cubes and therefore no comparison.

### 4.4 Phase 3: R2 latch and R3 poach (`phase3_income.py`)

- **`collect_player_production_income` (phase3_income.py:96-150).** For each In Production die whose effective face has star code `R2_MKT`: `player.r2_actions_available += 1`. For `R3_MKT`, append `(player_id, die_id)` to a pending list on `engine.state` (`_pending_poaches`). Do not resolve it here.
- **`execute_income` (phase3_income.py:351-360).** After the per-player loop, call `market_share.resolve_poaches(engine)`. Add a public `finalize_income(engine)` that wraps it; the web controller (`web/controller/phase3_income_actions.py:61, 120`) must call it once after all players' income.
- **`resolve_poaches` contract (INV-MS-R3-01):**
  - Resolve pending poaches in **clockwise order starting with the First Player**; within a player, in die order. For each one:
    - Candidates: surviving rivals (not Patient Zero) with `market_share > 0`.
    - If the actor is at `market_share_max`, or there are no candidates, record `moved=0` with a reason and stop (OQ-3).
    - Otherwise the target is the candidate with the highest `market_share`. Ties: call the bot hook `choose_poach_target(player_state, game_state, tied_pids) -> int`. Default: the most Corporate Secrets, then the first clockwise from the actor. A human or web choice may override this.
    - The target loses `min(r3_poach_amount, target.share)`. The actor gains the same amount, capped at max. If the actor is at max, the target still loses (§15.1 #3), so the total is not conserved in that case (logged `reason="actor_at_max"`).
  - "Most" is re-evaluated before each poach, so several R3 faces in one round chain correctly.
  - A poach can take a rival to 0. The Market Collapse check at the end of Phase 4 sees it.
- Singularity skips Phase 3, so no poach happens. On a Buffer Overflow round, income (including R3) still resolves.
- `r2_actions_available` resets in Phase 1 next to `b2_available` (phase1_roll_deploy.py:279-280) and after the Phase 6 turn. Unused actions are lost.

### 4.5 Phase 4: Red damage, Stage 2 and Market Collapse (`phase4_attack_resolution.py`)

1. **Stage 2 (phase4:245-288).**
   - If `any_shield_allocations is not None` (web): unchanged.
   - Else if `any_shield_policy == FREE_CHOICE`: `alloc = player.bot.choose_any_shield_allocation(player_state=player, remaining={R: rem_red, B: rem_blue, G: rem_green}, available_any=avail_any, game_state=engine.state, attack=player_attacks)`.
   - Validate the result (**INV-MS-ANY-SHIELD-01**): clamp each color to `[0, remaining]`, then trim to `avail_any` in B, R, G order. If the total is below `min(avail_any, Σ remaining)`, **back-fill** in the bot's `any_shield_fill_order` (default B, R, G). Generic shields must be used while any cube remains; the player chooses only the split (OQ-4). A bot without the hook uses `BaseBot`'s default.
   - Else: the existing tiers. Under MARKET_SHARE + V035_TIERS (isolation experiments only), Tier 2's condition becomes `player.market_share <= rem_red` ("this Red would cause Market Collapse"), and Tier 4 stays "remaining Red".
2. **Conditional ★ (phase4:294-306).** The old `R2` / `R3` bonuses run only when `red_variant_set == V035`, as a belt-and-braces guard; the codes already differ.
3. **Red resolution (phase4:308-323).** Under MARKET_SHARE:
   - `lost = player.change_market_share(-unblocked_red, "red")` and `market_share_red_overflow += unblocked_red − (−lost)`.
   - `unpaid_ransom = 0` and `ransom_secret_loss = 0`. Neither Money nor Secrets is touched (**INV-MS-RED-01**).
   - So `potential_secret_loss = unblocked_blue`, and Slush Fund absorbs Blue only (**INV-MS-SLUSH-01**).
   - Under RANSOM the existing code is unchanged (**INV-MS-RANSOM-PARITY-01**).
4. **Ledgers.** `red_incoming_total += player_attacks[RED]`, `red_blocked_color_total += min(color_shields[RED], player_attacks[RED])`, `red_blocked_any_total += any_allocated[RED]`. Both modes.
5. **Breakdown (phase4:362-394).** Add `market_share_before`, `market_share_after` and `market_share_lost`. Keep the ransom keys (zeroed under MARKET_SHARE) so the schema stays stable.
6. **Defense L4 (phase4:148-159).** Unchanged. Blocked Red counts. Fix the docstring's ransom wording.
7. **Market Collapse check.** `check_end_triggers_after_attacks` (phase4:501-513) calls `market_share.check_market_collapse(engine)` **after** the existing Patient Zero / Total Wipeout logic:

```python
def check_market_collapse(engine) -> bool:
    s = engine.state
    if s.game_over or not s.config.is_market_share or not s.config.market_collapse_enabled:
        return False
    hit = [p.player_id for p in s.players if not p.is_patient_zero and p.market_share <= 0]
    if not hit:
        return False
    s.market_collapse_triggered = True
    s.market_collapse_round = s.current_round
    s.market_collapse_pids = hit
    s.end_triggers.append("market_collapse")
    s.is_final_round = True
    if s.final_round_trigger_phase is None:
        s.final_round_trigger_phase = 4
    if s.end_reason == EndGameReason.NONE:
        s.end_reason = EndGameReason.MARKET_COLLAPSE
    return True
```

- **Precedence (INV-MS-COLLAPSE-PREC-01):** `TOTAL_WIPEOUT` (Phase 2/4, `game_over`) > `SINGULARITY` (Phase 2; Phase 4 never runs) > `PATIENT_ZERO` (Phase 2 or this Phase 4; it is checked first and sets `end_reason`) > `MARKET_COLLAPSE`. `end_reason` names the highest-precedence trigger. `end_triggers` lists every trigger that fired, in order, for telemetry.
- Nobody is eliminated and nothing else changes (**INV-MS-COLLAPSE-01**). Regaining Market Share in that round's Phase 6 does **not** cancel the Final Round (**INV-MS-COLLAPSE-STICKY-01**).
- With Collapse enabled, every survivor starts each round with Market Share ≥ 1 (**INV-MS-COLLAPSE-02**).
- The check runs in `finalize_attack_resolution`, so it also runs on Buffer Overflow rounds (where only R3 can change Market Share) and on the web path (`web/controller/phase4_attack_actions.py:193`).

### 4.6 Phase 6: regain, R2 and counters (`phase6_operations.py`)

Fixed Operations Turn order (unchanged sim simplification):
1. Track upgrades, each step followed by its Breakthrough (phase6:70-71).
2. **Under SHARE_REGAIN: `execute_share_regain(engine, player, plan.share_regain)` replaces `execute_patent_filings`** (phase6:72, 306-312). Under PATENTS: unchanged.
3. Paid ★ (phase6:159-195), plus R2.
4. Purchases (phase6:216-257).
5. Algorithmic Arbitrage (as today).

```python
def execute_share_regain(engine, player, wanted: int) -> int:
    player.regain_this_turn = 0
    done = 0
    while done < wanted:
        lvl = player.patent_level                      # post-upgrade level (same rule as Patent filing)
        cap = cfg.share_regain_cap_by_level[lvl]
        cost = cfg.share_regain_cost_by_level[lvl]
        if player.regain_this_turn >= cap or player.market_share >= player.market_share_max \
                or player.research_tokens < cost:
            break
        player.research_tokens -= cost
        player.research_spent_regain += cost
        player.change_market_share(+1, "regain")
        player.regain_this_turn += 1
        done += 1
    return done
```

- **INV-MS-REGAIN-01:** per turn, Market Share regained ≤ the cap at the Public Relations level in effect, each step costs that level's rate, it never goes above the max, and it happens only in Phase 6. Allowed in the Final Round, where it matters because Market Share is the first tiebreaker.
- **R2 (paid ★, step 3).** `while plan.use_r2_share > 0 and player.r2_actions_available > 0`: if `money >= r2_share_cost and market_share < max`, pay, `change_market_share(+r2_share_gain, "r2")`, and `r2_uses += 1`. Then decrement both counters. R2 does **not** count toward the regain cap (OQ-5). At max it is atomic: no payment.
- **Counters.** In both purchase paths (phase6:135-147 Arbitrage, 244-257 Market): `player.purchases_by_color[color.value] += 1`.
- **Plan under SHARE_REGAIN.** `plan.patent_filings` is ignored and logged as `rejected_patent_filings`; it never raises. That matches the Purple-purchase pattern.

### 4.7 `research_tracks.py`

- Keep `TRACKS` and the internal key `"PATENT"` / `patent_level` so bots, web and fixtures don't break. `normalize_track` also accepts `"PUBLIC_RELATIONS"` and `"PR"`.
- `track_display_name(config, track) -> str` returns "Public Relations Track" under SHARE_REGAIN and "Cryptographic Patents Track" otherwise. The `BREAKTHROUGH_TEXT` entries for PATENT L1/L3 (research_tracks.py:45-46) are unchanged.
- New: `regain_rate(config, player) -> (cost, cap)`. `breakthrough_preview` (:346) adds the regain cost/cap under SHARE_REGAIN.
- Telemetry `final_track_levels` keeps the key `"PATENT"` and adds `"track_names"` for display.

### 4.8 `end_game.py`: tiebreakers

- Add `_standard_key_ms(r) = (secrets, market_share, money, ready_colored_dice_count, patches, -unpatched)` and `_wipeout_key_ms(r) = (market_share, money, ready_colored, patches, -unpatched)`.
- Choose the key by `tiebreak_order`. Replace the inline lambdas at end_game.py:128-147 and 161-169 with the chosen key functions, keeping V035 key behaviour byte-for-byte. `win_pool, win_key` (:155, :174) must use the same key, and competition ranking (:205-211) follows it.
- Total Wipeout: Patient Zero players keep the Market Share they had when breached (they skip Phase 4). The legacy v0.33 path is unchanged.
- Ranking rows add:
  - `market_share` (`None` under RANSOM), `market_share_min`;
  - `market_share_lost_red`, `market_share_red_overflow`, `market_share_lost_poach`, `market_share_gained_poach`, `market_share_regained`, `market_share_gained_r2`;
  - `research_spent_regain`, `r2_uses`;
  - `comparison_money_gained`, `comparison_money_paid`, `comparison_shortfall_forgiven`;
  - `purchases_by_color`, `red_incoming_total`, `red_blocked_color_total`, `red_blocked_any_total`;
  - `company_code`, `white_hat_code`, `seat`.
- `EndGameResult` adds:
  - `end_triggers`, `market_collapse_pids`, `market_collapse_round`;
  - `version_comparisons` (list of dicts);
  - `tiebreak_decided_by` (name of the first key field that separated the winner from the runner-up: `"secrets"`, `"market_share"`, `"money"`, …, `"shared"`, or `"sole_survivor"`);
  - `setup` = `{"version_cards": [directive_code×3], "variant_cards": {color: code}, "companies": [...], "white_hats": [...], "first_player_index_start": int}`;
  - `collapse_trigger_pids_were_secret_leaders` (bool list, for kamikaze watch).
- **INV-MS-TIEBREAK-01.**

### 4.9 `core.py`

- Player init (core.py:164-188): Market Share fields per §4.1.
- `GameEngine.__init__`: `self.variant_cards = resolve_variant_cards(variant_cards or get_default_variant_cards(), config.red_variant_set)` (core.py:86). Store `self.state.first_player_index_start`.
- `_snapshot_players` (core.py:292-309): add `"market_share"` **only when `is_market_share`**, so default snapshots are byte-identical.
- `_begin_research_telemetry` / `_record_research_telemetry` (core.py:327-344): also snapshot and diff the Market Share ledgers into the new `RoundTelemetry` fields (§6.1).

### 4.10 Invariants

| ID | Statement |
|---|---|
| INV-MS-LEGACY-PARITY-01 | `GameConfig()` and `legacy_v035()` reproduce `v035_parity`; `legacy_v034()` and `legacy_v033()` reproduce their fixtures. |
| INV-MS-RANSOM-PARITY-01 | Under RANSOM / PATENTS / V035 / V035_TIERS, no new code path changes state; new fields are telemetry-only. |
| INV-MS-RANGE-01 | `0 ≤ market_share ≤ market_share_max` at every phase boundary (MARKET_SHARE). |
| INV-MS-LEDGER-01 | `start − lost_red − lost_poach + gained_poach + regained + gained_r2 == market_share`. |
| INV-MS-RED-01 | Under MARKET_SHARE, Red changes only Market Share (−min(share, unblocked)); no Money or Secret change from Red; no Unpaid Ransom Leak. |
| INV-MS-SLUSH-01 | Under MARKET_SHARE, Slush Fund only ever absorbs Blue loss. |
| INV-MS-ANY-SHIELD-01 | FREE_CHOICE: per-color allocation ≤ remaining; Σ = min(available, Σ remaining). |
| INV-MS-CMP-TIMING-01 | Comparisons happen only in Phase 2, right after the final space of a non-last version resolves and before any later space; at most once per version per game. |
| INV-MS-CMP-ELIG-01 | Patient Zero players are never part of a comparison. |
| INV-MS-CMP-TIES-01 | Fewer than 2 eligible, or all tied → no Money moves. |
| INV-MS-CMP-BANK-01 | Each top player +payout; each bottom player −min(money, payout); forgiven = remainder; no player-to-player transfer; Money ≥ 0; no Secret change. |
| INV-MS-COLLAPSE-01 | Market Collapse only at the end of Phase 4; sets the Final Round; never eliminates; never sets `game_over`. |
| INV-MS-COLLAPSE-02 | With Collapse enabled, every survivor has Market Share ≥ 1 at the start of every round. |
| INV-MS-COLLAPSE-PREC-01 | `end_reason` precedence TOTAL_WIPEOUT > SINGULARITY > PATIENT_ZERO > MARKET_COLLAPSE; `end_triggers` lists all. |
| INV-MS-COLLAPSE-STICKY-01 | A triggered Final Round is never cancelled by regaining Market Share. |
| INV-MS-REGAIN-01 | Per Operations Turn: count ≤ cap[level], cost = rate[level], never above max. |
| INV-MS-NO-PATENT-01 | Under SHARE_REGAIN, `patent_secrets_gained == 0` and `research_spent_patents == 0`. |
| INV-MS-R2-01 | R2: at most one +1 per R2 face In Production in Phase 3; atomic; outside the regain cap. |
| INV-MS-R3-01 | Target = surviving rival with the most (> 0) loses up to `r3_poach_amount`; actor gains the same up to max and never goes above it. The total is conserved except when the actor is capped (§15.1 #3). |
| INV-MS-TIEBREAK-01 | MARKET_SHARE_FIRST order per C6 for survivors, for eliminated players, and for Total Wipeout ranking. |
| INV-MS-RNG-01 | v0.36 engine and bot code makes **no** RNG draws. All ties are broken by seat/clockwise order. Same seed + config → identical result. |
| INV-MS-RNG-02 | `resolve_variant_cards` keeps setup draws identical across `red_variant_set` cells. |
| INV-MS-SETUP-01 | `v036()` starting Secrets are 8 / 10 / 11 and Market Share starts at 19 / 20 / 20. |

---

## 5. Bot Policy (`sim/bots/market_share_policy.py`, new)

v0.35 bots ignore Red, so telemetry would be invalid without these policies. Everything here is deterministic (INV-MS-RNG-01). It is active when `config.is_market_share` and `config.market_share_bot_policy == "AWARE"`. `"NAIVE"` keeps the bot hooks at their v0.35-equivalent behaviour (Generic shields B > R > G, no regain beyond leftovers, no Red purchase nudge) for the ablation cell.

### 5.1 Policy object and shared signals

```python
@dataclass(frozen=True)
class MarketSharePolicy:
    blue_value: float = 3.0            # per Secret saved
    blue_lethal_value: float = 100.0   # block that prevents a Total Data Breach
    green_value: float = 1.0           # per die kept In Production (0.2 if a White Contractor can be sacrificed; 0 if In Production empty)
    red_base_value: float = 0.5
    red_danger_value: float = 2.0      # share after this round <= next-round Red pressure + danger_margin
    red_collapse_value: float = 6.0    # this cube would take share to 0
    comparison_weight: float = 1.0     # x payout when blocking changes my comparison place
    danger_margin: int = 2
    red_buy_share_frac: float = 0.5    # Red purchase nudge below this fraction of max
    collapse_seeking: bool = False     # stress slice only (kamikaze watch), never on in acceptance cells
```

All weights are `[TUNE-BOT]`, not rules.

Signals, as pure functions of `GameState`:
- `red_pressure(state) = staging_cup[RED] + tower.stuck_cubes[RED]`. This matches how the bots already read threats.
- `next_comparison(state) -> Optional[(version, payout, blacks_needed)]`:
  - `blacks_needed = capacity − corruption_track` on the active non-last version.
  - If `pending_version_advance` is set, use the next version (`capacity − overflow`).
  - Returns `None` when no comparison is left.
- `comparison_imminent(state) = blacks_needed <= staging_cup[BLACK] + stuck[BLACK] + 1`. The `+1` is the Phase 1 Pulse.
- `place(player, state, my_share) -> "top" | "bottom" | "middle" | "tied_all"` against surviving rivals' shares.

### 5.2 Generic shield allocation hook (Phase 4)

`BaseBot.choose_any_shield_allocation(player_state, remaining, available_any, game_state, attack) -> Dict[CubeColor, int]`

Greedy. For each Generic shield, compute the marginal value of blocking one more cube of each color that still has cubes; give the shield to the highest. Ties go Blue > Red > Green.
- **Blue:** `blue_lethal_value` if `secrets − rem_blue ≤ 0`, else `blue_value` (+1 if secrets ≤ 3).
- **Red, MARKET_SHARE:**
  - start at `red_base_value`;
  - add `red_collapse_value` if `share − rem_red ≤ 0`. If `collapse_seeking` is set and the player currently leads in Secrets, this term is negative instead;
  - add `red_danger_value` if `share − rem_red ≤ red_pressure + danger_margin`;
  - add `comparison_weight × payout` if a comparison is imminent and blocking this cube changes `place()` from bottom (or tied bottom) or into sole top. Rivals' end-of-phase shares are estimated as `share − max(0, red_attack − their committed Red color shields)`.
- **Red, RANSOM:** 2.5 if `money < rem_red`, else 0.8. This mirrors v0.35 intent under FREE_CHOICE.
- **Green:** as in `MarketSharePolicy.green_value`.

`any_shield_fill_order = (BLUE, RED, GREEN)` is the engine back-fill.

The same valuation drives `choose_aegis_override` under MARKET_SHARE (base.py:279-295 currently prefers Blue, then Red): ignore the color with the highest single-cube marginal value.

### 5.3 Regain and Public Relations Track focus (`research_policy.py`)

`plan_research` (research_policy.py:37-69) returns `(track_upgrades, patent_filings, share_regain)`. Keep a 2-tuple wrapper for old callers. Under SHARE_REGAIN:

1. **Urgent regain** `u` (0..cap at the current Public Relations level):
   - critical: `share ≤ red_pressure + danger_margin`;
   - **or** a comparison is imminent and +k changes my place (out of bottom, or into sole top);
   - **or** the Final Round (spend everything up to the cap while below max).

   Reserve `u × cost` research first.
2. Run the existing want-list (focus to L4 → L1 on the others → L2 on the 2nd track) with the remaining research, stopping at the first unaffordable step. If the Public Relations Track is in the want-list, re-read cap/cost after that upgrade.
3. **Leftovers.** Where v0.35 filed Patents (focus at L4 and research ≥ `reserve_floor`, or late game), put the leftover research into regain up to the cap and below max. `is_late_game` (research_policy.py:29-34) also counts as late when any survivor's share ≤ `red_pressure + danger_margin`.
4. `apply_research_policy` (research_policy.py:87-105) sets `plan.share_regain` and forces `plan.patent_filings = 0`.

**Focus orders.** The `"PATENT"` slot *is* the Public Relations Track, so every bot already includes it. Keep the current `research_focus` tuples (base.py:141; each bot at line 19). Add an optional class attribute `research_focus_v036` that defaults to `research_focus`. The game-designer may re-order it after the first sweep if Public Relations is over-picked. `research_focus_mode="random"` still works.

### 5.4 R2 / R3 / purchases

- **R2:** `plan.use_r2_share = n`, where `n` = available R2 actions, wanted while below max and `(critical or comparison_imminent or final_round)`, and `money − 2 × n ≥ cash_cushion` (0 in the Final Round). This mirrors the B2/Y1 cushion pattern (adaptive_balanced.py:433-440).
- **R3 tie hook:** `choose_poach_target`, as in §4.4.
- **Red purchase nudge.** `apply_market_share_policy(bot, plan, player, state)` is called in `resolve_operations_plan` after `apply_research_policy` (phase6_operations.py:23-31). If `share ≤ red_buy_share_frac × max` or critical, and Red stock > 0, and the player owns < 2 Red dice, and Red is affordable after the planned purchases:
  - replace the last non-Red planned purchase with Red, or append Red if under the limit;
  - at most 1 Red per turn from this rule.
- **Per-bot overrides (class attribute `market_share_policy`):**
  - `SecOpsTurtleBot`: `red_danger_value=3.0, danger_margin=3`.
  - `VentureGreedBot`: `red_base_value=0.3`.
  - All others use the default.
  - `collapse_seeking=True` applies only in the stress slice (§8).

### 5.5 New `BaseBot` hooks and plan fields

- Hooks: `choose_any_shield_allocation`, `choose_poach_target`, and `market_share_policy` (attribute).
- `Phase3ActionPlan` (base.py:18-61) adds `share_regain: int = 0` and `use_r2_share: int = 0`.

---

## 6. Telemetry Schema

### 6.1 `RoundTelemetry` additions (state.py:805-832)

| Field | Type | Meaning |
|---|---|---|
| `market_share_after_p4` | `Dict[int, Optional[int]]` | per player, after Phase 4 |
| `market_share_end_of_round` | `Dict[int, Optional[int]]` | after Phase 6 (or at end phase) |
| `red_by_player` | `Dict[int, Dict[str,int]]` | `incoming`, `blocked_color`, `blocked_any`, `unblocked`, `share_lost`, `overflow` |
| `regain_by_player` | `Dict[int, Dict[str,int]]` | `count`, `research`, `cap`, `level` |
| `r2_by_player` | `Dict[int,int]` | |
| `r3_events` | `List[Dict]` | this round's poaches |
| `version_comparisons` | `List[Dict]` | `VersionComparisonRecord.as_dict()` |
| `purchases_by_player` | `Dict[int, Dict[str,int]]` | colors bought this round |
| `end_triggers_this_round` | `List[str]` | |

All are empty or `None` under RANSOM, except `red_by_player` and `purchases_by_player`, which are filled in both modes so the baseline can be compared.

### 6.2 Game-level fields (`EndGameResult`; ranking keys per §4.8)

`end_reason`, `end_triggers`, `total_rounds`, `is_total_wipeout`, `market_collapse_round`, `market_collapse_pids`, `version_comparisons`, `tiebreak_decided_by`, `setup`, `double_version_fill_events`.

### 6.3 Derived metrics (computed by the sweep script; formulas fixed here)

| Metric | Formula |
|---|---|
| End-reason split | `end_reason` share per pod. **The 3-way split counts TOTAL_WIPEOUT inside Patient Zero** (as in the probe); it is also reported separately. Splits by `setup.version_cards[i]`, company seat, White Hat seat. |
| Market Share curve | mean / p10 / p50 / p90 `market_share_end_of_round` by round and by seat rank |
| Red block rate | Σ(`blocked_color` + `blocked_any`) / Σ `incoming` over survivor resolutions, excluding Buffer Overflow |
| Red purchase share | Red purchases / all Central Market purchases (Triage L3 excluded) |
| Regain share of research | Σ `research_spent_regain` / Σ(`research_spent_tracks` + `research_spent_regain`) |
| Comparison stats | per version: payout events, total paid, total forgiven, % all-tied, % top-tie, % bottom-tie, % any tie |
| Collapse context | % of Collapse games where a collapsing player led in Secrets (kamikaze watch); rounds-to-collapse |
| Tiebreak attribution | distribution of `tiebreak_decided_by` |
| Pacing | mean / median rounds; % games ≤ 5 rounds |
| Economy | end Money, purchases per seat by color, Money from comparisons per seat |
| Tracks | % reaching L4 per track (maxed-track share), Breakthrough counts |
| Company spread | max − min company win rate (shared wins split) |

---

## 7. Edge Cases (normative)

| # | Case | Resolution |
|---|---|---|
| E1 | Bottom player has `$0` | Pays `$0`, forgiven = payout; no Secret loss. |
| E2 | All eligible tied (incl. 2P tie) | Nothing happens; `all_tied=True`. |
| E3 | 3P shares 10/10/5 | Both 10s gain payout; the 5 pays. |
| E4 | One eligible player (rival breached earlier this Phase 2) | Nothing happens. |
| E5 | Final space is "Lose `$X`" or "Lose Secrets" | The effect resolves first; anyone breached by it is excluded; the comparison uses the reduced Money. |
| E6 | One compile fills v1.0 and spills to fill v2.0 | `$2` comparison, then v2.0 spaces, then `$4` comparison; `double_version_fill_events += 1`; once-guard blocks a later duplicate (§4.3 note). |
| E7 | v3.0 fills (Singularity) | No comparison; Phase 4 never runs, so no Collapse check. |
| E8 | Market Collapse and Patient Zero in the same Phase 4 | `end_reason = PATIENT_ZERO`; `end_triggers = ["patient_zero", "market_collapse"]`; breached players eliminated; survivors (including those at 0) finish Phases 5–6. |
| E9 | Patient Zero in Phase 2, then a survivor hits 0 in Phase 4 | `end_reason` stays PATIENT_ZERO; Collapse recorded. |
| E10 | Only one survivor, at 0 | Same as E8/E9; that survivor wins (`tiebreak_decided_by="sole_survivor"`). |
| E11 | All survivors reach 0 together, no breach | MARKET_COLLAPSE; ranked by Secrets, then Market Share (all 0), then Money… |
| E12 | All players breach in Phase 4 while some are at 0 | TOTAL_WIPEOUT (game over); Collapse not checked; ranked Market Share > Money > … |
| E13 | Regain to above 0 in the Final Round's Phase 6 | Final Round stands; the final Market Share counts for tiebreaks. |
| E14 | Regain at max | No research spent. |
| E15 | Regain cap reached, or upgrade to L2/L4 mid-turn | Cap and cost re-read per step at the current level; an L2 upgrade bought before regain gives cap 2 that turn. |
| E16 | R2 at max, or `< $2` | Not paid; action lost at end of turn. |
| E17 | Two R2 faces | Two separate actions. |
| E18 | R3 with tied top rivals | Bot or human chooses; default: most Secrets, then first clockwise. |
| E19 | R3 actor at max | Target still loses 1; actor stays at max (§15.1 #3). |
| E20 | R3 where every rival is at 0, or every rival is Patient Zero | No transfer. |
| E21 | R3 takes a rival to 0 | Collapse at the end of Phase 4 unless something restores it (nothing can in Phase 4). |
| E22 | Two R3 in one round | Clockwise from the First Player; "most" re-evaluated each time. |
| E23 | Red beyond the floor | Clamped to 0; overflow logged; no other effect. |
| E24 | Aegis ignores Red | Not counted as blocked (unchanged Defense L4 rule); Red incoming is counted after Aegis. |
| E25 | Bot returns an illegal Generic allocation | Clamped, then back-filled (§4.5). |
| E26 | `market_collapse_enabled=False` (experiment) | Shares may sit at 0; INV-MS-COLLAPSE-02 not asserted. |
| E27 | Web human omits Generic allocations under FREE_CHOICE | Engine asks the bot hook (Phase B adds a UI prompt). |

---

## 8. Product-Owner Sweep Definition (plan §6 guardrails)

**Script:** `scripts/run_v360_market_share_sweep.py`. Output: `sim_results/v360_market_share_sweep.json`. Report: `docs/findings/v360_telemetry_sweep_report.md`.
**Match setup:** mirror `run_v360_red_rebalance_sweep.build_engine`:
- seeded `random.Random(seed)` → bot rotation (5 bots, `(idx × n + i) % 5`, then shuffle);
- `get_random_setup(rng, "STANDARD")`, `get_random_companies`, `get_random_white_hats`.

Telemetry comes only from engine fields (§6), not monkeypatched hooks.
**Seeds:** base `42`; `seed = 42 + n × 100_000 + idx`. **The same seeds go to every cell** (paired). Log seeds for games ≤ 5 rounds, ≥ 12 rounds, Total Wipeouts in rounds ≤ 5, and Collapses in rounds ≤ 5.

| Cell | Config | Games per pod (2P/3P/4P) |
|---|---|---|
| C0 `V035` | `GameConfig()` | 3,000 |
| C1 `V036` (acceptance) | `GameConfig.v036()` | 3,000 |
| T1 `L4-RATE` | v036 + `cap[4]=2, cost[4]=1` | 1,000 |
| T2 `L4-BOTH` | v036 + `cap[4]=3, cost[4]=1` | 1,000 |
| T3 `PAYOUT-LOW` / `PAYOUT-HIGH` | payouts `{1,2}` / `{3,6}` | 1,000 each |
| T4 `NO_PAYOUT` | `version_share_payout={}` (with MARKET_SHARE) | 1,000 (isolates dice-buy inflation) |
| T5 `MS±2` | start −2 and +2 per pod | 1,000 each |
| T6 `NAIVE` | v036 + `market_share_bot_policy="NAIVE"` | 1,000 (bot-policy effect) |
| T7 `RANDOM_FOCUS` | v036 + `research_focus_mode="random"` | 1,000 |
| T8 `KAMIKAZE` (stress) | v036 + `collapse_seeking=True` on RecklessSaboteur | 1,000 |
| T9 `TIERS` | v036 + `any_shield_policy=V035_TIERS` | 1,000 (free-choice effect) |

Report guardrails for C1 with 95% CIs, and the deltas against C0:

| Guardrail (plan §6) | Metric (§6.3) | Pass |
|---|---|---|
| End-reason split | PZ (incl. Total Wipeout) / Singularity / Market Collapse | each 25–40% in every pod; no single setup (v3.0 card, company seat, White Hat seat) has any trigger > ~55% |
| Rounds | mean | 8.4–9.0 |
| Total Wipeout | rate | ≤ C0 (2P ≤ 16%) |
| Red blocking | Red block rate | clearly above C0 (~10%); game-designer judges |
| Red dice | Red purchase share | rises vs C0, ≤ ~35% of market buys |
| Ties | % comparisons with any tie | well below ~50% |
| Research | regain share of research spend | 20–40%; no track > ~50% of maxed tracks |
| Company spread | max − min win rate | ≤ C0 (~15 pts) |
| Money | end Money, purchases per seat | reported vs C0; C1 purchases ≤ 1.2 × T4 |

The game-designer may add cells. The product-owner does not change engine mechanics (PLAN §2C).

---

## 9. Unit Test Specification (`tests/test_v360_market_share.py`)

| ID | Test |
|---|---|
| MS-01 | `GameConfig()` resolves RANSOM / PATENTS / V035 / V035 / V035_TIERS, collapse off, payouts `{}`. `v036()` resolves all v0.36 values, 8/10/11 Secrets and 19/20/20 Market Share. |
| MS-02 | Invalid combos raise (SHARE_REGAIN + RANSOM, MARKET_SHARE + V033, missing level keys). |
| MS-03 | v0.35 parity: `GameConfig()` and `legacy_v035()` vs `v035_parity` (mixed/asym/setup × 300 seeds × 2/3/4P). |
| MS-04 | `v034_parity` and `v033_parity` still pass. |
| MS-05 | Red: 3 unblocked → −3 Market Share; Money and Secrets unchanged; breakdown ransom keys zeroed. |
| MS-06 | Red floor: share 2, 5 unblocked → 0, overflow 3. |
| MS-07 | Slush Fund under MARKET_SHARE sees only Blue loss (DTO, 2 Blue + 4 Red unblocked → absorbs 2 Blue; Red irrelevant). |
| MS-08 | FREE_CHOICE: bot allocation honoured; illegal allocation clamped and back-filled; Σ invariant. |
| MS-09 | Default heuristic: lethal Blue first; Red that would collapse beats Green; comparison-imminent Red beats Green when it changes place. |
| MS-10 | V035_TIERS under MARKET_SHARE: Tier 2 uses the "would collapse" check. |
| MS-11 | Comparison happy path 2P: top +$2 from bank, bottom −$2. |
| MS-12 | **Shortfall at $0**: bottom pays 0, forgiven 2; Secrets unchanged. |
| MS-13 | Partial shortfall: $1 → pays 1, forgiven 1 ($2 payout). |
| MS-14 | **All tied** (2P and 4P) → no Money moves; `all_tied`. |
| MS-15 | Shared places 3P 10/10/5 and 4P 9/7/7/7: all tied top gain, all tied bottom pay. |
| MS-16 | Comparison timing: after the final space's "Lose $" (pre-income Money), before spillover spaces; exactly once per version. |
| MS-17 | **Spillover filling two versions in one compile**: `$2` then v2.0 spaces then `$4`; once-guard stops a later duplicate; `double_version_fill_events == 1`. |
| MS-18 | No comparison on v3.0 fill (Singularity) and none at game end. |
| MS-19 | Patient Zero from an earlier space in the same Phase 2 (or from the final space) excluded; single eligible → nothing. |
| MS-20 | Buffer Overflow round: no comparison. |
| MS-21 | Collapse: survivor at 0 after Phase 4 → `is_final_round`, `end_reason=MARKET_COLLAPSE`, `final_round_trigger_phase=4`, nobody eliminated, Phases 5–6 run. |
| MS-22 | **Collapse + Patient Zero in the same Phase 4** → PATIENT_ZERO; `end_triggers` has both; breached players eliminated. |
| MS-23 | Patient Zero in Phase 2, Collapse in Phase 4 → PATIENT_ZERO. |
| MS-24 | **Collapse when only one survivor** (2P and 3P variants) → sole survivor wins; `tiebreak_decided_by="sole_survivor"`. |
| MS-25 | Total Wipeout in Phase 4 with players at 0 → TOTAL_WIPEOUT; Collapse not recorded. |
| MS-26 | Singularity pre-empts: a game ending in Phase 2 never calls the Collapse check. |
| MS-27 | Collapse on a Buffer Overflow round via R3 only. |
| MS-28 | Sticky Final Round: regain to above 0 in Phase 6 does not cancel. |
| MS-29 | Regain: L0 cap 1 @2; L2 cap 2; L4 cap 3; research exactly debited; ledger holds. |
| MS-30 | **Regain cap**: wants 3 at L0 → 1; upgrade to L2 earlier in the same turn → 2. |
| MS-31 | **Market Share at max**: regain spends 0; R2 not paid; R3 no transfer; comparison unaffected. |
| MS-32 | Regain allowed in the Final Round; Patent Filing ignored under SHARE_REGAIN (`rejected_patent_filings`). |
| MS-33 | Public Relations Breakthroughs: L1 `$3`, L3 Purple from Personal Reserve (unchanged mechanics under SHARE_REGAIN). |
| MS-34 | R2: earned only if In Production in Phase 3; pay $2 → +1; outside the cap; two faces → two uses; reset next Phase 1. |
| MS-35 | R3 basic: takes from the rival with the most; the total is conserved when the actor is below max. |
| MS-36 | **R3 with tied rivals**: hook called with the tied pids; default most Secrets, then clockwise. |
| MS-37 | R3 skips Patient Zero rivals; all rivals at 0 → nothing; two R3 chain clockwise from the First Player. |
| MS-38 | R3 takes a rival to 0 → Collapse at the end of Phase 4. |
| MS-39 | Variant mapping: under MARKETING, `get_random_setup` Red draws map R1/R2/R3 → R1/R2_MKT/R3_MKT; identical RNG state after setup across sets. |
| MS-40 | Old R2/R3 Phase 4 bonuses never fire under MARKETING; R1 face identical in both sets. |
| MS-41 | **Tiebreak ordering**: Secrets tie broken by Market Share before Money; full key chain; shared victory when all equal; V035 order unchanged under defaults. |
| MS-42 | **Total Wipeout ranking** under MARKET_SHARE_FIRST: Market Share first; breach depth ignored. |
| MS-43 | Ledger invariants (Market Share and research) over 300 random v036 games, all pods; INV-MS-RANGE-01 checked at each phase boundary via snapshots. |
| MS-44 | Determinism: 2 runs × 100 seeds identical (v036, aware and naive bots). |
| MS-45 | No-RNG: patch `random.Random` methods to raise while calling `market_share.*` and `market_share_policy.*` functions on a mid-game state. |
| MS-46 | Bot regain policy: critical → reserves research before upgrades; comparison imminent and +1 moves off bottom → regain; otherwise leftovers only. |
| MS-47 | Red purchase nudge: triggers below 50% max, max 1 per turn, respects stock/affordability/limit. |
| MS-48 | Telemetry: all §6 fields present; Σ per-round deltas equal end totals; `setup` populated; `end_triggers` ordered. |
| MS-49 | Starting Secrets 8/10/11 and Market Share 19/20/20 per pod under `v036()`. |
| MS-50 | Slow, skipped by default: 600-game v036 smoke per pod; reports the end-reason split vs probe §32 (no hard gate, since bots differ from the probe). |

All existing tests must pass. Tests needing v0.35 behaviour keep using defaults; none are rewritten.

---

## 10. File-by-File Change List

| File | Change |
|---|---|
| `sim/config.py` | Enums (§2.1), fields (§2.2), `__post_init__` resolution/validation, `v036()`, `legacy_v035()`, `red_mode` default in `legacy_v034/v033`, properties, `market_share_start()`; remove `red_die_profile`; keep `red_ransom_per_cube`. |
| `sim/entities.py` | `VariantCard.display_code`; MARKETING Red cards; `get_all_variant_cards(red_variant_set)`; `resolve_variant_cards`; remove the `red_profile` kwarg and `V036_RED` branch (1225, 1260-1276); DTO description variant. |
| `sim/engine/market_share.py` (new) | `resolve_version_comparison`, `resolve_poaches`, `check_market_collapse`, `VersionComparisonRecord`, helpers. |
| `sim/engine/state.py` | `PlayerState` fields and `change_market_share`; `file_patent` guard; `RoundTelemetry` / `EndGameResult` / `GameState` / `CompileResult` fields. |
| `sim/engine/phase2_compiler.py` | Comparison hooks at :340-347 and :348-361; `end_triggers` at :387-405. |
| `sim/engine/phase3_income.py` | R2/R3 latch in `collect_player_production_income`; `finalize_income` / `resolve_poaches` after the `execute_income` loop; `_STAR_NOTES` R1 name. |
| `sim/engine/phase4_attack_resolution.py` | Stage 2 policy (:245-288), conditional-★ gate (:294-306), Red → Market Share (:308-323), ledgers and breakdown (:362-394), Collapse in `check_end_triggers_after_attacks` (:501-513), docstrings. |
| `sim/engine/phase1_roll_deploy.py` | Reset `r2_actions_available` with the B2/Y1 flags (:279-280). |
| `sim/engine/phase6_operations.py` | `execute_share_regain` replaces filings under SHARE_REGAIN (:72); R2 in paid ★; `purchases_by_color`; remove `red_profile` kwargs (:142, :254); call `apply_market_share_policy` in `resolve_operations_plan`. |
| `sim/engine/research_tracks.py` | Aliases, `track_display_name`, `regain_rate`, preview; remove `red_profile` (:214). |
| `sim/engine/end_game.py` | Tiebreak keys by `tiebreak_order`; ranking and result fields; `tiebreak_decided_by`; `setup`. |
| `sim/engine/core.py` | Market Share init, `resolve_variant_cards`, snapshots (conditional), round telemetry, `first_player_index_start`. |
| `sim/bots/market_share_policy.py` (new) | §5. |
| `sim/bots/research_policy.py` | 3-tuple `plan_research`, regain integration, late-game rule. |
| `sim/bots/base.py` | Hooks `choose_any_shield_allocation`, `choose_poach_target`; Aegis under MARKET_SHARE; plan fields; `market_share_policy` attribute. |
| `sim/bots/{adaptive_balanced,secops_turtle,venture_greed,accelerationist,reckless_saboteur}.py` | `market_share_policy` / `research_focus_v036` attributes; R2 use in `take_operations_actions` next to B2/Y1. |
| `sim/experiments.py` | Variant code lists (:387, :415). |
| `tests/fixtures/v035_parity/{__init__,capture}.py` + JSON | §2.5. |
| `tests/test_v360_market_share.py` | §9. |
| `scripts/run_v360_market_share_sweep.py` (new) | §8. |
| `scripts/run_v360_red_rebalance_sweep.py` | Drop REDDIE/PACKAGE; archived header (§2.6). |
| Phase B (after sign-off): `web/controller/{capabilities,serializer,phase2_actions,phase3_income_actions,phase4_attack_actions,phase6_operations_actions}.py`, `web/schemas.py`, `web/static/js/components/{player_mats,action_dock,market,compiler,header}.js` | Market Share track display, Public Relations Track label and regain action (cap/cost), R2 action, R3 tie prompt, Generic allocation prompt under FREE_CHOICE, comparison event log, `market_collapse` end screen, `finalize_income` call, Marketing label. |
| Phase B: `pnp/generate_pnp.py`, `pnp/illustrations.py`, `pnp/pdf_engine.py` | graphic-designer: Market Share track and Public Relations Track on the Company Terminal Mat, Red Variant Cards, Marketing die label, player aids. |
| Docs | `PLAN.md` Phase 45 checkboxes; `FINDINGS.md` §33 after the sweep; `CLAUDE.md` Core Pillars tiebreaker line (line 24) and the Market Collapse end trigger. |

---

## 11. RULES.md / Glossary Sections to Update (Phase B; list only)

- Header → `v0.36.0`.
- §1 Theme (line 12, "researching cryptographic patents"; line 9, "extort funds").
- §2 Components: Red Cubes bullet (Market Manipulation); track table row (Cryptographic Patents → Public Relations Track); Personal Reserve bullet; new Market Share track on the Company Terminal Mat; mat wireframe.
- §3 Setup: starting Secrets by player count; Market Share marker; Client Company start text (line 135, "Patent filing").
- Phase 2: Version Advance & Track Spillover (add the comparison step and its ordering); End Game Trigger Check (Singularity pre-empts Collapse).
- Phase 3: R3 resolution and R2 timing.
- Phase 4: Two-Stage Defensive Blocking Stage 2 (free choice); Unblocked Damage, Red (remove the ransom and the Unpaid Ransom Leak); damage-conditional ★ list; DTO Slush Fund wording; Defense Grid Level 4 ransom sentence; End Game Trigger Check (Market Collapse and precedence).
- Phase 6: Step 1 Breakthrough examples (Public Relations L1/L3); Step 2 Patent Filings → Market Share regain; Step 3 paid ★ (+R2).
- §5 End Game: trigger list (+Market Collapse); Hierarchical Tiebreakers; Total Wipeout ranking.
- §6A die table: Red label "Marketing"; Purple cost cell "Starter / Patents L3".
- §6B Red ★ Variants.
- §6D: DTO row; White Hat intro (Personal Reserve reference).
- §7 Glossary:
  - Update: Red Cubes; Money; Research Tokens; Breakthrough; Personal Reserve; Purple Proprietary Specialist Dice; Colored Software Module Dice ("Red [FinSec]"); Dual-Output Face (R1 name); Two-Stage Defensive Blocking; Version Switch; Phase 4; Phase 6; Total Wipeout Ending; Final Round.
  - Replace Cryptographic Patents Track & Patent Filing with **Public Relations Track**.
  - Add **Market Share**, **Market Collapse**, **Marketing**, **Market Manipulation**.
  - Remove Unpaid Ransom Leak.
- §7 Retired Terms: add *Unpaid Ransom Leak*, *Ransomware / Financial Wiretaps*, *Cryptographic Patents Track*, *Patent Filing*, *FinSec*, *Ransom Insurance*, *Threat Bounty*, *Short Squeeze*.
- Grep for leftovers: `Ransom`, `Patent`, `FinSec`, `Threat Bounty`, `Short Squeeze`, `Unfunded Red`, `4-tier`.

"Version comparison", "regain" and "poach" are engineering shorthand in this spec only. RULES text should describe these steps without introducing new terms (OQ-6).

---

## 12. Implementation Sequencing

1. Capture `v035_parity` from a clean HEAD worktree (§2.5).
2. Apply the §2.6 cleanup (revert `red_die_profile`, keep `red_ransom_per_cube`); confirm parity.
3. Config, entities and state fields (no behaviour change); parity green.
4. `market_share.py` plus the Phase 4 Red / Collapse / Stage 2 hooks; tests MS-05..10, 21..28.
5. Phase 2 comparison; MS-11..20.
6. Phase 3 R2/R3 and Phase 6 regain/R2; MS-29..40.
7. End-game tiebreaks and telemetry; MS-41..43, 48.
8. Bot policy; MS-44..47.
9. Sweep script, then hand off to staff-engineer review, then product-owner.

Web and PnP wait until after game-designer sign-off. The sweep does not need them, and payout, cap and start values may still change.

---

## 13. Risks / Watch Items

- **Kamikaze Market Collapse:** a Secrets leader could choose to hit 0 to end the game early. Required Generic-shield use (OQ-4) blunts this. The T8 slice and the "collapsing player led in Secrets" metric measure it.
- **Synchronized decline:** every player faces the same Red cubes, so Collapse may cluster. The regain policy and the Red purchase nudge are the counter; watch the comparison tie rate.
- **Public Relations over-pick** by the VentureGreed and RecklessSaboteur focus orders (v0.35 Patents artifact). T7 measures the bot-roster effect.
- **Double version fill** (pre-existing engine limitation): reported, not fixed (§4.3).

---

## 15. Open Questions for Orchestrator / User

1. **Red ★ names and costs.** Proposed: R1 *Brand Protection* `$5` (Block 1 Red + `$2`); R2 *Ad Campaign* `$4` (Phase 6: pay `$2` → +1 Market Share); R3 *Customer Poaching* `$5` (Phase 3: take 1 Market Share from the rival with the most). Accept or rename/re-price.
2. **Public Relations L4 default for `v036()`:** cap +3 at 2 🔬 (proposed). L4-RATE (cap 2 at 1 🔬) and L4-BOTH (cap 3 at 1 🔬) run as sweep cells.
3. **R3 when you are already at max Market Share:** no effect, so the rival keeps it (proposed, "move" semantics). The alternative is that the rival still loses 1.
4. **Free-choice Generic shields:** must every available `Any` shield block while unblocked cubes remain, with the player choosing only the split (proposed)? Or may a player leave shields unused, which allows deliberately taking Red?
5. **R2 and the regain cap:** R2's +1 does not count toward the Public Relations per-round cap (proposed).
6. **Terminology:** no printed names for the Version-change Money comparison or the Phase 6 Market Share regain action (proposed: describe them in rules prose; no new glossary terms). Confirm.


### 15.1 Resolutions (User, 2026-11-06)

These override any proposal above where they differ.

1. **Red ★ cards: accepted as proposed.** R1 *Brand Protection* `$5`, R2 *Ad Campaign* `$4`, R3 *Customer Poaching* `$5`. Costs stay `[TUNE]`.
2. **Public Relations L4 default:** cap +3 at 2 🔬. L4-RATE and L4-BOTH stay as sweep cells.
3. **Customer Poaching at max Market Share: the rival still loses 1.** This differs from the proposal. The poaching player's own Market Share stays capped at max. Update the R3 contract, edge cases and tests to match.
4. **Free-choice Generic shields:** every available `Any` shield must block while unblocked cubes remain. The player chooses only how the shields are split across colors.
5. **Ad Campaign (R2):** its +1 does not count toward the Public Relations per-round cap.
6. **Terminology:** no new names for the Version-change comparison or the regain action. The new card names (*Brand Protection*, *Ad Campaign*, *Customer Poaching*) are approved glossary additions.
