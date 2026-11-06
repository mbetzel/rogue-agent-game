# Technical Architecture Specification: Phase 43 (v0.35.0)
## Research Track Rebalance: 5-Level Tracks, Breakthroughs, Flat Company Setup & New Gray Legacy Faces

**Author:** Principal Engineer / Architect
**Status:** Draft for Orchestrator Review (the open questions in §13 need answers before implementation starts)
**Target Version:** `v0.35.0` candidate
**Source of Truth:** [`docs/explorations/2026_11_research_track_rebalance_plan.md`](../explorations/2026_11_research_track_rebalance_plan.md). **Section 6 (User decisions 2026-11-05) supersedes Sections 2–3 where they differ.** Modeling evidence: [`docs/findings/v350_research_income_sweep.md`](../findings/v350_research_income_sweep.md) (package D1), prototype [`scripts/investigate_v350_research_sweep.py`](../../scripts/investigate_v350_research_sweep.py).
**Dependencies:** [RULES.md](../../RULES.md) (§2, §3, §4, §6, §7), [PLAN.md](../../PLAN.md) (Phase 43, §2), [v340_six_phase_round_sequence_spec.md](./v340_six_phase_round_sequence_spec.md)
**Target Components:**
- `sim/config.py`, `sim/entities.py`, `sim/engine/state.py`, `sim/engine/core.py`, `sim/engine/end_game.py`
- `sim/engine/phase1_roll_deploy.py` (Release L4 reroll), `phase3_income.py` (research accounting), `phase4_attack_resolution.py` (Passive Firewall gate, Slush Fund, Defense L4), `phase5_pipeline_shift.py` (Emergency Hotfix gate, Triage L4), `phase6_operations.py` (upgrades, Breakthroughs, Patents, Purple purchase removal, Prometheus)
- New: `sim/engine/research_tracks.py`, `sim/bots/research_policy.py`
- `sim/bots/base.py` and all 5 bot subclasses
- `web/controller/phase6_operations_actions.py`, `phase1_actions.py`, `phase3_income_actions.py`, `capabilities.py`, `serializer.py`, `web/schemas.py`, `web/static/js/components/{market,action_dock,player_mats}.js`
- `RULES.md`, `pnp/generate_pnp.py`, `pnp/illustrations.py`, `pnp/pdf_engine.py`
- New: `tests/test_v350_research_tracks.py`, `tests/fixtures/v034_parity/`

> Line numbers below are from the working tree at commit `9a46982` (plus uncommitted `FINDINGS.md` / `PLAN.md` edits). Re-verify them before editing.

---

## 1. Executive Summary

### 1.1 What changes

| # | Change | Source |
|---|---|---|
| C1 | All four Terminal Hardware Tracks become **L0–L4**, step costs **1 / 2 / 2 / 3 🔬** `[TUNE]` (8 🔬 per track). | Plan §2.1 |
| C2 | Fixed **Breakthroughs** at L1 and L3 of each track, resolved immediately when the level is reached. | Plan §2.1, §6.4–6.6 |
| C3 | L4 effects: Defense `+$1` per blocked Attack Cube (max `$3`); Triage `+1 🔬` per die moved beyond the 2nd in Conveyor Triage; Release `+1` free reroll in Phase 1 Step 4; Patents filing rate `1 🔬 → 1 Secret`. | Plan §2.1, §6.9 |
| C4 | Patent filing rates: L0–L1 `2 🔬 → 1 Secret`, L2–L3 `3 🔬 → 2 Secrets`, L4 `1 🔬 → 1 Secret`. The old Patents L2 `+$1` per filing is removed. | Plan §2.1 |
| C5 | **Emergency Hotfix** and **Passive Firewall** are retired. | Plan §2.1 |
| C6 | **Purple dice can no longer be purchased.** The 2nd Purple die comes only from the Patents L3 Breakthrough. | Plan §6.4 |
| C7 | **Triage L3 Breakthrough:** pay `$3` `[TUNE]` to replace 1 Gray Legacy die with a Central Market colored die of your choice, placed in Ready for Release. | Plan §6.5 |
| C8 | **All Client Company setup bonuses removed.** Every company starts at `$6`, 8 Secrets, 0 🔬, L0 on every track, Defense Capacity 2 / Triage Bandwidth 2 / Release Bandwidth 4. | Plan §6.7 |
| C9 | **DTO Slush Fund is once per game.** All other Institutional Overrides stay once per version. | Plan §6.8 |
| C10 | **New Gray Legacy faces** `[TUNE]`: `Block 1 Any`, `Block 1 Any`, `+$1 & +1 🔬`, `+$1 / +1 🔬`, `+$1 / +1 🔬`, `+1 🔬`. Purple unchanged. | Plan §6.1 |
| C11 | Research-aware bot policy ported from the prototype into `sim/bots`. | Plan §6.10 |
| C12 | Telemetry for 🔬 earned, track levels, Breakthroughs and L4 payouts. | This spec |

Unchanged: the six-phase round, starting Secrets (8), starting money (`$6`), the 3 Gray + 1 Purple starter pool, Market purchase limit (2/turn), all Variant Cards, all Signature Protocols, every Institutional Override except Slush Fund frequency and Algorithmic Arbitrage's Purple option.

### 1.2 Track table (v0.35.0)

Step cost to reach L1 / L2 / L3 / L4: `1 / 2 / 2 / 3 🔬` `[TUNE]`.

| Track | L0 | L1 (Breakthrough) | L2 | L3 (Breakthrough) | L4 |
|---|---|---|---|---|---|
| Defense Grid | Defense Capacity 2 | Gain 1 Gray Legacy die → Ready for Release | Capacity 3 | Gain 1 Corporate Secret | Capacity 4 + `+$1` per Attack Cube blocked in Phase 4 (max `$3`) `[TUNE]` |
| Triage | Triage Bandwidth 2 | Gain 2 White Contractor dice → Ready for Release | Bandwidth 3 | Pay `$3`: replace 1 Gray Legacy die with a Central Market colored die of your choice → Ready for Release | Bandwidth 4 + `+1 🔬` per die moved in Conveyor Triage beyond the 2nd |
| Release | Release Bandwidth 4 | Gain 1 Gray Legacy die → Ready for Release | Bandwidth 5 | Gain 1 Corporate Secret | Bandwidth 6 + 1 extra free reroll in Phase 1 Step 4 |
| Cryptographic Patents | File `2 🔬 → 1 Secret` | Gain `$3` | File `3 🔬 → 2 Secrets` | Gain your 2nd Purple die (from Personal Reserve) → Ready for Release | File `1 🔬 → 1 Secret` |

### 1.3 Comparison (`v0.34.0` vs `v0.35.0`)

| Item | v0.34.0 | v0.35.0 |
|---|---|---|
| Track levels | L0–L2, cost 2 / 3 🔬 | L0–L4, cost 1 / 2 / 2 / 3 🔬 |
| Level 2 perks | Emergency Hotfix (Triage), Passive Firewall (Defense) | none (retired) |
| Patent cost | 4 / 3 / 2 🔬 per Secret (+`$1` at L2) | 2.0 / 1.5 / 1.0 🔬 per Secret |
| Purple purchase | Personal Reserve `$4–$6` (Dossier), Prometheus discount | not purchasable; Patents L3 Breakthrough |
| Company setup | Meridian `+$2`, DTO `+1` Secret, Helix Patents L1 + 2 🔬, Omnidyne/Aegis track & capacity shifts, Prometheus `-1 🔬` discount | none |
| Slush Fund | once per version | once per game |
| Gray faces | `B, B, $1, $1, $1/🔬, 🔬` | `B, B, $1&🔬, $1/🔬, $1/🔬, 🔬` |
| 🔬 per player per game (bots) | 3.8 | ~12 (D1) |

---

## 2. Configuration (`sim/config.py`)

### 2.1 `ResearchTrackModel`

```python
class ResearchTrackModel(str, Enum):
    """Research track / company setup ruleset selector (v0.35.0).
    V034_THREE_LEVEL: v0.34.0 tracks (L0-L2, Hotfix/Firewall, purchasable Purple, company bonuses,
    old Gray faces, Slush Fund per version). Kept for regression and parity.
    V035_FIVE_LEVEL: canonical v0.35.0."""
    V034_THREE_LEVEL = "V034_THREE_LEVEL"
    V035_FIVE_LEVEL = "V035_FIVE_LEVEL"
```

### 2.2 New / changed `GameConfig` fields

| Field | Type / default | Notes |
|---|---|---|
| `research_track_model` | `ResearchTrackModel = V035_FIVE_LEVEL` | The single master switch. Coerced in `__post_init__` like `round_sequence`. |
| `track_step_costs` | `Tuple[int, int, int, int] = (1, 2, 2, 3)` | `[TUNE]`. Cost to reach L1..L4. V035 only. |
| `track_capacity_by_level` | `Dict[str, Tuple[int, ...]]` | `DEFENSE: (2,2,3,3,4)`, `TRIAGE: (2,2,3,3,4)`, `RELEASE: (4,4,5,5,6)`. |
| `patent_rate_by_level` | `Dict[int, Tuple[int, int]]` | `{0:(2,1), 1:(2,1), 2:(3,2), 3:(3,2), 4:(1,1)}` = (🔬 cost, Secrets gained). |
| `patent_l1_cash` | `int = 3` | Patents L1 Breakthrough. |
| `triage_l1_contractors` | `int = 2` | Triage L1 Breakthrough. |
| `triage_l3_upgrade_cost` | `int = 3` | `[TUNE]` Triage L3 Breakthrough. |
| `defense_l4_cash_per_block` / `defense_l4_cash_cap` | `int = 1` / `int = 3` | `[TUNE]`. |
| `triage_l4_free_moves` | `int = 2` | 🔬 paid per die beyond this count. |
| `release_l4_extra_rerolls` | `int = 1` | |
| `gray_face_profile` | `Optional[str] = None` | Resolves to `"V035_D1"` (V035) or `"V034"`. Sweep cells may override. |
| `purple_purchasable` | `Optional[bool] = None` | Resolves to `False` (V035) / `True` (V034). |
| `company_setup_bonuses` | `Optional[bool] = None` | Resolves to `False` (V035) / `True` (V034). |
| `slush_fund_once_per_game` | `Optional[bool] = None` | Resolves to `True` (V035) / `False` (V034). |
| `level2_perks_enabled` | `Optional[bool] = None` | Emergency Hotfix + Passive Firewall. `False` (V035) / `True` (V034). |

The `Optional` sub-flags exist so that experiments can isolate one lever. They resolve once in `__post_init__` from `research_track_model` when `None` (same rule as `starting_secrets_by_player_count`: re-assigning the model later does **not** re-resolve). Tests must not mix a V034 model with V035 sub-flags except in explicitly named lever tests.

### 2.3 Constructors

- `GameConfig.legacy_v034(**overrides)` → `research_track_model=V034_THREE_LEVEL`, everything else default (SIX_PHASE).
- `GameConfig.legacy_v033(**overrides)` additionally does `overrides.setdefault("research_track_model", V034_THREE_LEVEL)` so v0.33 parity stays bit-identical (INV-SEQ-LEGACY-PARITY-01 must keep passing).
- Property `is_v035_tracks` → `research_track_model == V035_FIVE_LEVEL`.
- `starting_purple_reserve` stays `1`. Under V035 the reserve die is reachable only by the Patents L3 Breakthrough.

### 2.4 Parity fixtures (do this first)

Before any edit, capture `tests/fixtures/v034_parity/` from HEAD `9a46982`: 300 seeds × 2/3/4P (same harness as `v033_parity`), recording `EndGameResult` (rankings, money, secrets, research, rounds, end_reason) plus per-round `RoundTelemetry` staged/exited/attack counts. After the refactor, `GameConfig.legacy_v034()` must reproduce them exactly (INV-RT-LEGACY-PARITY-01). The v0.33 fixtures must also still match.

---

## 3. Entities (`sim/entities.py`)

### 3.1 Gray Legacy die

`create_gray_die(die_id: int, profile: str = "V035_D1") -> Die`. Profiles:

| Profile | Faces |
|---|---|
| `V034` | `Block 1 Any`, `Block 1 Any`, `+$1`, `+$1`, `+$1 / +1 🔬` (choice), `+1 🔬` |
| `V035_D1` | `Block 1 Any`, `Block 1 Any`, `+$1 & +1 🔬` (`money=1, patches=1`), `+$1 / +1 🔬` (choice), `+$1 / +1 🔬` (choice), `+1 🔬` |

All callers (`state.py` setup, Breakthrough grants, web controller, tests) pass `config.gray_face_profile`. The internal attribute stays `patches` (the 🔬 field) and existing face *names* keep the current string convention so bot string matches don't break. Renaming the legacy `🔧` glyph in sim face names is out of scope (see OQ-14).

### 3.2 `Company`

The fields stay so V034 still works. Add a helper `effective_company(company, config) -> Company`: under `company_setup_bonuses=False` it returns `dataclasses.replace(c, starting_defense_capacity=2, starting_triage_bandwidth=2, starting_release_bandwidth=4, starting_*_level=0, starting_cash_bonus=0, starting_research_bonus=0, starting_secrets_bonus=0, upgrade_discount=0)`. `PlayerState.__init__` reads through this helper only. Card data is unchanged (V034 needs it).

### 3.3 `WhiteHat.reserve_cost`

Kept for V034. Under V035 it is never read (INV-RT-NO-PURPLE-BUY-01).

---

## 4. State (`sim/engine/state.py`)

### 4.1 `PlayerState` additions

```python
# v0.35.0 research tracks
research_earned_total: int = 0                    # every 🔬 gained (never decremented)
research_earned_by_source: Dict[str, int]         # "income", "signature_protocol", "star", "triage_l4", "corruption", "other"
research_spent_tracks: Dict[str, int]             # per track
research_spent_patents: int = 0
patent_secrets_gained: int = 0
level_reached_round: Dict[str, Dict[int, int]]    # track -> level -> round number
breakthroughs: List[BreakthroughRecord]
l4_payouts: Dict[str, int]                        # "defense_cash", "triage_research", "release_rerolls_used", "patent_secrets"
slush_fund_used_game: bool = False
```

```python
@dataclass
class BreakthroughRecord:
    track: str                 # "DEFENSE" | "TRIAGE" | "RELEASE" | "PATENT"
    level: int                 # 1 or 3
    round_number: int
    outcome: str               # "TAKEN" | "DECLINED" | "FORFEITED"
    detail: Dict[str, Any]     # e.g. {"die_id": 41}, {"gray_die_id": 3, "new_color": "yellow", "paid": 3}, {"contractors": 1, "short": 1}
```

### 4.2 Research accounting

Add `PlayerState.gain_research(amount: int, source: str) -> None` which adds to `research_tokens`, `research_earned_total` and `research_earned_by_source[source]`. Every 🔬 gain in `phase3_income.py` (dice income, Cipher Algorithmic Parity, `★` outputs), corruption-track effects, and the Triage L4 payout must go through it (INV-RT-RESEARCH-LEDGER-01). Spending stays a direct decrement inside `upgrade_track` / `file_patent`. Do **not** use the prototype's `property` monkeypatch.

### 4.3 `get_track_upgrade_cost(track)` / `upgrade_track(track)`

Under V034 the current bodies (`state.py:333-430`) run unchanged (move them into `_v034_*` helpers). Under V035 they delegate to `sim/engine/research_tracks.py`:

- Cost: `None` if level ≥ 4, else `config.track_step_costs[level]`. No company discount (Prometheus discount removed with C8).
- `upgrade_track` under V035 **only** pays and raises the level, updates capacity/bandwidth from `track_capacity_by_level`, and records `level_reached_round`. It returns `True`/`False`. It does **not** resolve the Breakthrough. That is done by the Phase 6 caller (§5.6) so that bot/web choices can be supplied. A unit-test helper `research_tracks.upgrade_and_resolve(engine, player, track, chooser)` wraps both.
- `has_emergency_hotfix` / `has_passive_firewall` are forced `False` when `level2_perks_enabled=False`, at init and after every upgrade.

### 4.4 `get_patent_cost()` / `file_patent()`

V035: cost and gain from `patent_rate_by_level[patent_level]`. `file_patent` adds `gain` Secrets (uncapped, decision §6.3), increments `patent_secrets_gained`, `research_spent_patents`, and, at L4, `l4_payouts["patent_secrets"]`. No `+$1` per filing. Add `get_patent_gain()` for bots and web.

### 4.5 Slush Fund

`PlayerState.is_slush_fund_available(active_ver)`: under `slush_fund_once_per_game` it is `not slush_fund_used_game and is_ability_available(active_ver)`. Using it sets `slush_fund_used_game=True` **and** marks the current version slot used. Later version slots still unlock normally but cannot fire Slush Fund (DTO has no other override). See OQ-5 for the trigger choice.

### 4.6 `EndGameResult` / per-player telemetry

Add to each player's final record: `research_earned_total`, `research_earned_by_source`, `research_spent_tracks`, `research_spent_patents`, `patent_secrets_gained`, `final_track_levels` (`{track: level}`), `level_reached_round`, `breakthroughs` (list of dicts), `l4_payouts`, `purple_dice_owned_final`, `gray_dice_owned_final`, `triage_l3_upgrade_color`. Add to `RoundTelemetry`: `research_gained_by_player`, `track_upgrades_by_player` (list of `(track, new_level)`), `breakthroughs_by_player`. Existing fields are unchanged so old scripts keep running.

---

## 5. Engine Module Contracts

### 5.1 New `sim/engine/research_tracks.py`

```python
TRACKS = ("DEFENSE", "TRIAGE", "RELEASE", "PATENT")

def step_cost(config, player, track) -> Optional[int]
def apply_level(config, player, track, new_level, round_number) -> None      # capacity/bandwidth + bookkeeping
def resolve_breakthrough(engine, player, track, level, choice: BreakthroughChoice | None) -> BreakthroughRecord
def triage_l3_options(engine, player) -> TriageUpgradeOptions               # legal Gray dice, legal colors, affordable?
def defense_l4_cash(config, player, blocked_cubes: int) -> int
def triage_l4_research(config, player, moved_count: int) -> int
def free_rerolls_for(config, player, base: int) -> int
```

```python
@dataclass
class BreakthroughChoice:
    accept: bool = True                    # only meaningful for Triage L3 (the only optional, paid Breakthrough)
    gray_die_id: Optional[int] = None      # Triage L3
    color: Optional[DieColor] = None       # Triage L3
```

### 5.2 Breakthrough resolution rules

All Breakthroughs resolve **immediately** when the level is reached, during the player's own Phase 6 Operations Turn, before the next operation of that turn. New dice go to **Ready for Release** and do not use Release Bandwidth (same as purchases, INV-PIPE-PURCHASE-READY-01). They roll from next round's Phase 1.

| Breakthrough | Resolution | Shortfall rule (proposed defaults, flagged) |
|---|---|---|
| Defense L1 / Release L1: Gain 1 Gray Legacy die | Create `create_gray_die(next_die_id, profile)`; append to Ready for Release. | No component limit in sim. PnP needs 2 extra Gray per player (OQ-8). |
| Defense L3 / Release L3: Gain 1 Corporate Secret | `secrets += 1` (uncapped). | — |
| Triage L1: Gain 2 White Contractor dice | `n = min(2, contractor_supply)`; create White dice into Ready for Release; `contractor_supply -= n`; add to `contractor_dice` so they expire at the end of next round's Phase 4. | Short supply → gain fewer; record `short`. Interaction with next round's Temp Staffing pricing: OQ-6. |
| Triage L3: `$3` Gray → Market colored die | See §5.3. | |
| Patents L1: Gain `$3` | `money += 3`. Usable later in the same turn. | — |
| Patents L3: Gain 2nd Purple die | If `personal_purple_reserve > 0`: decrement, create Purple die (bound to the player's White Hat), append to Ready for Release. | Reserve empty (only possible via test setup) → `FORFEITED`. |

**Multiple levels in one turn (INV-RT-BT-ORDER-01).** Upgrades are applied one step at a time in the order the plan lists them. Each step's Breakthrough fully resolves before the next step is paid for. So buying Patents L0→L1 and then Triage L2→L3 in one turn lets the `$3` from Patents L1 fund the Triage L3 cost. Buying Defense L0→L1→L2→L3 in one turn resolves L1 (Gray die), then L2 (capacity), then L3 (Secret), in that order. A plan whose step isn't affordable at its turn in the sequence stops there; later steps are skipped (not reordered).

**Timing of level effects.** Defense Capacity applies from next round's Phase 1. Triage/Release Bandwidth apply from next round's Phase 5 (unchanged rule). Release L4's reroll applies from next round's Phase 1. Defense L4 from next round's Phase 4. Patents rate applies to filings made later in the same turn (an upgrade bought earlier in the turn is in effect).

**Final Round.** Breakthroughs still resolve. Gained Secrets count. Gained dice have no further effect but count for the "Active Colored Module Dice in Ready for Release" tiebreaker (a Triage L3 die or Patents L3 Purple die counts; a Gray die doesn't).

### 5.3 Triage L3 contract (proposed defaults; each is flagged in §13)

- **Optional.** The player may decline. A declined or impossible Breakthrough is recorded `DECLINED` / `FORFEITED` and is **not** deferred: reaching L3 is the only trigger (OQ-1).
- **Can't afford `$3`:** `FORFEITED` (OQ-1). Bots/web see `affordable=False` from `triage_l3_options` before buying the level, so a bot can choose to wait.
- **Gray die eligibility:** any Gray Legacy die the player owns in **Ready for Release, Scanned Box or Glitched Box** (In Production and the Defense Grid are empty in Phase 6). Player's choice; the bot default picks Glitched first, then Scanned, then Ready (removes the die furthest from rolling). The removed Gray die leaves the game (returns to the box). The new die always goes to Ready for Release, whatever zone the Gray die was in (OQ-2).
- **No Gray die owned:** `FORFEITED`.
- **Color choice:** any of Red / Blue / Green / Yellow with ≥1 die in the Central Market. It takes that color's die and active Variant Card (`★` face). If all four stacks are empty: `FORFEITED`, no payment (OQ-3).
- **Cost:** flat `$3` regardless of the Variant Card's printed price. It does **not** count toward the 2-dice purchase limit (it isn't a purchase), and Algorithmic Arbitrage's discount can't apply (OQ-4).
- **Payment happens only if the replacement succeeds** (atomic).

### 5.4 Phase 1 (`phase1_roll_deploy.py:307`)

Replace `max_free_rerolls = engine.config.default_free_rerolls` with `research_tracks.free_rerolls_for(config, player, base)`, where `base` is the existing value (including any throttle). Release L4 adds `+1` **after** the throttle (proposed; OQ-7). Count the extra reroll as `l4_payouts["release_rerolls_used"]` only if the player actually uses more rerolls than `base`. Helix Brute-Force Bypass receives the adjusted count.

### 5.5 Phase 3 (`phase3_income.py`)

Route every 🔬 gain through `gain_research(...)`. No rule change.

### 5.6 Phase 4 (`phase4_attack_resolution.py`)

- `:216-222` Passive Firewall: run only when `level2_perks_enabled` (V034).
- `:309-318` Slush Fund: gate with `is_slush_fund_available`; on use set `slush_fund_used_game`. Under V035 the bot decides (`choose_slush_fund`, §7.4) instead of auto-firing on the first loss (OQ-5).
- **Defense L4:** after the player's damage has resolved (after Red ransom, Blue and Green), if `defense_level >= 4`: `cash = min(cap, per_block × blocked)`, where `blocked` = Red + Blue + Green Attack Cubes absorbed by this player's shields this phase (the existing `"blocked"` dict at `:350`). Cubes ignored by Aegis Baffle Echo and Black cubes are not "blocked". On Compile Buffer Overflow the payout is 0. The cash cannot fund this round's Red ransom (proposed; OQ-9). Record `l4_payouts["defense_cash"]`.

### 5.7 Phase 5 (`phase5_pipeline_shift.py`)

- `:92` Emergency Hotfix: gated by `level2_perks_enabled`. Under V035, Step 1 is Magnetic Splice only.
- `conveyor_triage` (`:205`): after moving, if `triage_level >= 4`: `gain_research(max(0, moved - 2), "triage_l4")`. Max `+2 🔬` per round at Bandwidth 4.

### 5.8 Phase 6 (`phase6_operations.py`)

Rewrite the `execute_player_operations_turn` order so the turn is deterministic:

1. Track upgrades in plan order, each step followed by its Breakthrough (§5.2). Bot/web Breakthrough choices come from `plan.breakthrough_choices: Dict[(track, level), BreakthroughChoice]`; if a choice is missing the engine calls `bot.choose_breakthrough(...)`.
2. Patent filings (rate re-read after each upgrade).
3. Paid `★` actions (unchanged).
4. Purchases (≤ 2). **Under `purple_purchasable=False`:** `DieColor.PURPLE` in `market_purchases` and `plan.buy_purple_reserve=True` are ignored (logged as `rejected_purple_purchase` in telemetry; never raise in sim).
5. Prometheus Algorithmic Arbitrage (`:84-136`): the `free_color == PURPLE` branch is unreachable under V035 (Market colors only). The `+$2` cash mode is unchanged.

> Note: v0.34 RULES says "any of the following operations in any order". The sim already fixes an order; this spec keeps a fixed order for the sim and lets the web UI allow any order within the turn. The Breakthrough-immediacy rule is the same either way.

---

## 6. Purple no longer purchasable: every affected rule

| Location | Current text / code | v0.35.0 |
|---|---|---|
| `RULES.md:47` Components, mat | "Personal Reserve (2 dedicated holding slots for unpurchased Purple…)" | Holds the 2nd Purple die, gained by the Patents L3 Breakthrough. (Also fix the "2 slots" vs 1-die mismatch.) |
| `RULES.md:67` mat diagram | "Personal Reserve (2 Purple)" | "Personal Reserve (Purple: Patents L3)" |
| `RULES.md:101` White Hat Dossier cards | "provides Personal Reserve Purple dice" | Remove the procurement-cost wording. |
| `RULES.md:116-117` Purple dice component | "`$4–$6` procurement cost printed on White Hat Dossier" | "Not purchasable; 2nd die from Patents L3 Breakthrough." |
| `RULES.md:286` Phase 6 Step 4 **Personal Reserve Procurement** | Pay Dossier cost to buy Purple | **Delete the bullet.** |
| `RULES.md:287` and `:394` **Prometheus Algorithmic Arbitrage** | "from the Market or Personal Reserve at a `$2` discount" | "from the Central Market at a `$2` discount" |
| `RULES.md:327` die table, Purple row Cost column | "`$4–$6` (Dossier)" | "Starter / Patents L3" |
| `RULES.md:396-397` Dossier appendix header + intro | Personal Reserve with procurement cost | Remove cost. |
| `RULES.md:399-406` Dossier table | Cost column (`$4`/`$5`/`$6`) | Delete the column. |
| `RULES.md:476` Glossary **Personal Reserve** | "available for purchase … in Phase 6" | "Released only by the Patents L3 Breakthrough." |
| `RULES.md:500` Glossary **Purple Proprietary Specialist Dice** | "1 in Personal Reserve" (purchase implied) | Add "cannot be purchased". |
| Signature Protocols (Operator, Phreaker, Acoustic, Spook, Prodigy, Cipher) | none reference buying Purple | No text change. **Note:** Spook *Burn Notice* (`phase3_income.py:253`) and v3.0 Space 5 *Return Colored Die* (`phase2_compiler.py:149`) can still remove a Purple die, which is scrapped (INV-PURPLE-02). With no purchase path, that loss is permanent. Flagged OQ-10. |
| `sim/engine/phase6_operations.py:97-115, 199-218` | Purple purchase via Prometheus and via `buy_purple_reserve` | Gated by `purple_purchasable`. |
| `sim/bots/base.py:33` `buy_purple_reserve`; `accelerationist.py:233,298-311`; `reckless_saboteur.py:202,257-270` | Purple buy candidates | Skip when `not config.purple_purchasable`. |
| `web/controller/phase6_operations_actions.py`, `capabilities.py`, `schemas.py`, `static/js/components/market.js`, `action_dock.js`, `player_mats.js` | Reserve buy action/button, reserve cost display | Hide/disable under V035; show reserve as "Patents L3". |
| `pnp/generate_pnp.py`, `pnp/illustrations.py` | Dossier cost, mat Personal Reserve label | Update. |

---

## 7. Bot API (`sim/bots/`)

### 7.1 `sim/bots/research_policy.py` (port of `aware_research`)

```python
@dataclass(frozen=True)
class ResearchPolicy:
    focus_order: Tuple[str, str, str, str]
    late_secret_threshold: int = 3      # "late" when any survivor <= 3 Secrets, or Final Round
    reserve_floor: int = 4              # file Patents with leftover research only when focus is at L4 or research >= this

def plan_research(policy, player, state, config) -> Tuple[List[str], int]:   # (track_upgrades, patent_filings)
```

Behavior (identical to the prototype so D1 results reproduce):
1. If not late: want-list = focus track up to L4, then L1 on each other track, then L2 on the 2nd track. Walk it, buying while affordable, **stop at the first unaffordable step** (save toward it).
2. If the focus track is below L4 and research < `reserve_floor`, stop (no filings).
3. Otherwise / late: `patent_filings = research // patent_cost` at the (simulated) current Patents level. (Fix vs prototype: use the post-upgrade Patents level and `get_patent_gain`.)

Focus orders as class attributes `research_focus`:

| Bot | Focus order |
|---|---|
| AdaptiveBalancedBot | TRIAGE, DEFENSE, RELEASE, PATENT |
| SecOpsTurtleBot | DEFENSE, TRIAGE, RELEASE, PATENT |
| VentureGreedBot | PATENT, RELEASE, DEFENSE, TRIAGE |
| AccelerationistBot | RELEASE, PATENT, TRIAGE, DEFENSE |
| RecklessSaboteurBot | PATENT, TRIAGE, RELEASE, DEFENSE |

`BaseBot.research_focus_mode: str = "fixed"`; `"random"` reproduces sweep cell E1 using `rng` from the engine (seeded, not `hash(id(...))`).

### 7.2 Integration

`BaseBot.take_operations_actions` (and each subclass override) calls `plan_research` at the end **only when `config.is_v035_tracks`**, replacing `plan.track_upgrades` and `plan.patent_filings`. V034 keeps the current per-bot research logic untouched (parity).

### 7.3 Choice faces

Under V035, `declare_choices` takes 🔬 on any choice face that has no shield option (the prototype rule). Shield-or-🔬 faces (Blue `Block 1 Blue / +1 🔬`) keep existing logic.

### 7.4 New hooks (defaults in `BaseBot`)

- `choose_breakthrough(player_state, game_state, track, level, options) -> BreakthroughChoice`. Default for Triage L3: accept if affordable; Gray die Glitched > Scanned > Ready (lowest `die_id` within zone); color = the bot's existing Market preference among available colors, falling back Yellow > Green > Red > Blue (prototype order).
- `choose_slush_fund(player_state, game_state, potential_secret_loss) -> bool`. Default: use when `potential_secret_loss >= 2` or the loss would cause a Total Data Breach.
- Purple removed from all purchase candidate lists under V035.

---

## 8. Edge Cases

| # | Case | Resolution |
|---|---|---|
| E1 | Player buys several levels of one track in a turn | Step-by-step, each Breakthrough resolves in order (INV-RT-BT-ORDER-01). |
| E2 | Patents L1 `$3` funds Triage L3 in the same turn | Allowed if Patents was upgraded first in plan order. |
| E3 | Triage L3 with `< $3` | `FORFEITED` (OQ-1). |
| E4 | Triage L3 with no Gray die (all upgraded / scrapped) | `FORFEITED`. |
| E5 | Triage L3 with all Market colors empty | `FORFEITED`, no payment. |
| E6 | Triage L3 Gray die is in the Glitched Box | Allowed; new die goes to Ready for Release (OQ-2). |
| E7 | Triage L1 with contractor supply < 2 | Gain what's left. |
| E8 | Triage L1 contractors in the Final Round | Created; expire unused; no tiebreaker value (White isn't a colored die). |
| E9 | Patents L3 with empty Personal Reserve | `FORFEITED` (test-only state). |
| E10 | Defense L4 with Buffer Overflow, or only Black cubes | `$0`. |
| E11 | Defense L4 blocks 5 cubes | `$3` (cap). |
| E12 | Triage L4 moves exactly 2 / 3 / 4 dice | `0 / +1 / +2 🔬`. |
| E13 | Release L4 under a reroll throttle hazard | throttle then `+1` (OQ-7). |
| E14 | Slush Fund used in v1.0 | Unavailable in v2.0 and v3.0. |
| E15 | Patient Zero mid-turn | Not possible in Phase 6 (no damage). |
| E16 | Upgrade beyond L4 | `get_track_upgrade_cost` returns `None`; plan step skipped. |
| E17 | Old `pipeline_level` setter used by tests | Kept in both models. It sets triage/release levels directly and never resolves Breakthroughs. Tests that need Breakthroughs use `upgrade_and_resolve`. |

---

## 9. Web Controller and UI

- `phase6_operations_actions.py`: upgrade action accepts tracks up to L4, returns a pending `breakthrough_prompt` for Triage L3 (Gray die list, colors, cost, affordable flag) and resolves the rest automatically; Patents filing uses rate + gain; Purple reserve purchase removed under V035; Prometheus Purple option removed.
- `phase1_actions.py`: reroll counter uses `free_rerolls_for`.
- `capabilities.py`: drop `can_buy_purple_reserve`, `has_emergency_hotfix`, `has_passive_firewall` under V035; add `slush_fund_used_game`, `next_upgrade_cost` per track, `breakthrough_preview` per track.
- `serializer.py` / `schemas.py`: track levels `0..4`, `breakthroughs`, `research_earned_total`, `l4_payouts`.
- JS: `player_mats.js` 5-step track strips with L1/L3 Breakthrough markers; `action_dock.js` Triage L3 modal (pick Gray die, pick color, confirm `$3` / decline); `market.js` remove Purple reserve buy.
- Web defaults to V035; an existing `?ruleset=` / config path may expose V034 for comparison (optional).

---

## 10. Invariants

| ID | Statement | Checked by |
|---|---|---|
| **INV-RT-LEVELS-01** | Under V035 every track level ∈ {0..4}; capacity/bandwidth always equal `track_capacity_by_level[track][level]`. | R-01, R-02 |
| **INV-RT-COST-01** | Each upgrade step costs exactly `track_step_costs[level]` 🔬 with no company discount; research never goes negative. | R-01 |
| **INV-RT-BT-IMMEDIATE-01** | A Breakthrough resolves within the same Operations Turn, immediately after its level is paid, before any later upgrade, filing or purchase. | R-04 |
| **INV-RT-BT-ORDER-01** | Multiple levels bought in one turn resolve in plan order, one step at a time; later steps see earlier Breakthrough effects. | R-05, R-06 |
| **INV-RT-BT-ONCE-01** | Each (player, track, level∈{1,3}) produces exactly one `BreakthroughRecord`, and only when the level is first reached. | R-07 |
| **INV-RT-BT-READY-01** | Every Breakthrough die (Gray, White, Market colored, Purple) is placed in Ready for Release and consumes no Release Bandwidth. | R-08 |
| **INV-RT-TRIAGE-L3-ATOMIC-01** | Triage L3 either (pays `$3`, removes exactly 1 owned Gray die, takes exactly 1 die of an available Market color, adds it to Ready for Release) or changes nothing. Market stock of that color decrements by 1. | R-09..R-13 |
| **INV-RT-NO-PURPLE-BUY-01** | Under V035 no Purple die is ever gained except the starter and the Patents L3 Breakthrough; `personal_purple_reserve` only decrements via that Breakthrough. | R-14, R-15 |
| **INV-RT-NO-L2-PERKS-01** | Under V035 `has_emergency_hotfix` and `has_passive_firewall` are always `False`; no Hotfix move or Firewall absorption occurs. | R-16 |
| **INV-RT-FLAT-SETUP-01** | Under V035 every player starts with `$6`, 8 Secrets, 0 🔬, all levels 0, capacity 2 / 2 / 4, whatever Client Company. | R-17 |
| **INV-RT-SLUSH-ONCE-01** | Under V035 Slush Fund fires at most once per DTO player per game. | R-18 |
| **INV-RT-DEF-L4-01** | Defense L4 cash per Phase 4 = `min(3, blocked R/B/G cubes)`; 0 below L4 or on Buffer Overflow. | R-19, R-20 |
| **INV-RT-TRIAGE-L4-01** | Triage L4 🔬 per round = `max(0, moved − 2)` for dice moved in Conveyor Triage. | R-21 |
| **INV-RT-RELEASE-L4-01** | At Release L4 the player's Phase 1 free-reroll allowance is base + 1. | R-22 |
| **INV-RT-PATENT-RATE-01** | Each filing spends and gains exactly `patent_rate_by_level[level]`; no cash. | R-23 |
| **INV-RT-GRAY-FACES-01** | Under V035 every Gray Legacy die (starter and Breakthrough) has the `V035_D1` faces. | R-24 |
| **INV-RT-RESEARCH-LEDGER-01** | For every player at game end: `starting 🔬 + research_earned_total − research_spent_tracks − research_spent_patents == research_tokens`. | R-25 |
| **INV-RT-LEGACY-PARITY-01** | `GameConfig.legacy_v034()` reproduces `tests/fixtures/v034_parity/` exactly; `legacy_v033()` still reproduces `v033_parity`. | R-26, R-27 |
| **INV-RT-DETERMINISM-01** | Same seed + config → identical results, including Breakthrough choices and `research_focus_mode="random"`. | R-28 |

---

## 11. Test Matrix (`tests/test_v350_research_tracks.py`)

| ID | Test |
|---|---|
| R-01 | Cost sequence 1/2/2/3 per track; L4 → `None`; insufficient 🔬 → no change. |
| R-02 | Capacity/bandwidth per level for Defense/Triage/Release. |
| R-03 | Level effects apply from the stated next phase (Defense Capacity next Phase 1; bandwidth next Phase 5). |
| R-04 | Breakthrough immediacy: Patents L1 `$3` visible before a same-turn purchase. |
| R-05 | Defense L0→L3 in one turn: Gray die then capacity then Secret, in order. |
| R-06 | Patents L1 `$3` funds Triage L3 in the same turn; reverse plan order forfeits. |
| R-07 | No double Breakthrough on re-reaching a level (e.g. via test setters). |
| R-08 | Defense L1 / Release L1 Gray die and Patents L3 Purple placed in Ready; Release Bandwidth use unchanged. |
| R-09 | Triage L3 happy path for each color; Variant Card bound; Market stock −1; `$3` paid. |
| R-10 | Triage L3 can't afford → `FORFEITED`, no state change. |
| R-11 | Triage L3 no Gray die → `FORFEITED`. |
| R-12 | Triage L3 Market empty (all colors) → `FORFEITED`; one color empty → that color illegal. |
| R-13 | Triage L3 Gray die from Glitched / Scanned / Ready; decline path. |
| R-14 | Purple in `market_purchases` / `buy_purple_reserve` ignored under V035; purchase limit not consumed. |
| R-15 | Prometheus Purple discount rejected under V035; Market discount and cash mode still work. |
| R-16 | No Hotfix move in Phase 5 and no Firewall absorption in Phase 4 at Triage/Defense L2+. |
| R-17 | Flat setup for all 6 companies (parametrized). |
| R-18 | DTO Slush Fund once per game across v1.0→v3.0; bot hook decides. |
| R-19 | Defense L4: 0/1/3/5 blocked → `$0/$1/$3/$3`. |
| R-20 | Defense L4 on Buffer Overflow and with Baffle Echo-ignored cubes → not counted. |
| R-21 | Triage L4: 2/3/4 moved → 0/1/2 🔬, logged under `triage_l4`. |
| R-22 | Release L4 reroll count, including under throttle and with Helix. |
| R-23 | Patent rates at L0–L4; multiple filings; filing after same-turn Patents upgrade uses new rate. |
| R-24 | Gray faces V035 vs V034 profile. |
| R-25 | Research ledger invariant over 300 random games. |
| R-26 | v0.34 parity fixtures (300 seeds × 2/3/4P). |
| R-27 | v0.33 parity fixtures still pass. |
| R-28 | Determinism: 2 runs × 100 seeds identical, fixed and random focus. |
| R-29 | Bot policy: focus to L4, then L1 secondaries, then L2 of 2nd track; saves when short; late-game filing. |
| R-30 | Telemetry fields present and consistent (`breakthroughs` count = levels 1/3 reached; `final_track_levels` matches state). |
| R-31 | Web: Triage L3 prompt round-trip; Purple buy action absent; 5-level serialization. |
| R-32 | Sweep reproduction (non-blocking, marked slow): 600 games, V035 + aware bots, mean 🔬/player within ±1.0 of D1 (12.1), 2P Singularity within ±4 pp of 45.5%. Release L4 reroll was not modeled in the prototype, so drift is expected and is reported, not failed. |

All existing tests must pass. Tests that rely on v0.34 track/company behavior must set `GameConfig.legacy_v034()` rather than being rewritten.

---

## 12. Documentation and Asset Change Checklist

### 12.1 `RULES.md` (glossary-governed)
- [ ] `:1` header → `v0.35.0`.
- [ ] `:43-46` Components, track descriptions → the §1.2 table, five levels.
- [ ] `:47`, `:67`, `:84` mat: Personal Reserve text; remove "Emergency Hotfix" from the diagram; 5-step strips.
- [ ] `:95-100`, `:132-137`, `:139-141` Client Companies and setup: delete every setup bonus (Meridian `+$2`, Omnidyne levels/capacity, Aegis levels/capacity, DTO `+1` Secret, Helix Patents L1 + `2 🔬`, Prometheus discount). Setup: `$6`, 8 Secrets, 0 🔬, L0 on all tracks for everyone.
- [ ] `:156-159` Override section: "Once per Version" header gains the Slush Fund exception (once per game).
- [ ] `:232`, `:253` Phase 4: delete Passive Firewall; add Defense L4 payout; Buffer Overflow parenthetical drops Passive Firewall.
- [ ] `:245`, `:392` DTO Slush Fund → once per game.
- [ ] `:264` Phase 5 Step 1 → "Magnetic Splice" only.
- [ ] Phase 5 Step 4: Triage L4 `+1 🔬` per die beyond the 2nd.
- [ ] Phase 1 Step 4: Release L4 extra free reroll.
- [ ] `:276-281` Phase 6 Step 1: new costs, no Prometheus discount, Breakthrough rule (immediate; in order).
- [ ] `:283-284` Phase 6 Step 2: new Patent rates; remove `+$1`.
- [ ] `:286-287` delete Personal Reserve Procurement; Algorithmic Arbitrage Market-only.
- [ ] `:318` Gray row → new faces `[TUNE]`; Purple Cost column.
- [ ] `:389-394` Company table: drop the Def Cap/Triage/Release/Patent Cost/Bonus column contents (all identical now); Slush Fund once per game; Arbitrage Market-only.
- [ ] `:396-406` Dossier appendix: drop procurement cost.
- [ ] §7 Glossary: **add Breakthrough**; update Triage Track, Release Track, Defense Grid Track, Cryptographic Patents Track (levels 0–4), Personal Reserve, Purple Proprietary Specialist Dice, Ready for Release Zone (`:469` drops Emergency Hotfix), Phase 4 (`:515`) and Phase 5 (`:516`) entries; **retire Emergency Hotfix (`:489`) and Passive Firewall (`:490`)** and add both to the deprecated-terms list.
- [ ] Grep for leftovers: `Emergency Hotfix`, `Passive Firewall`, `Personal Reserve Procurement`, `Starting Cash`, `Starting Research`, `Upgrade Discount`, `Dossier` cost.

### 12.2 `web/`
- [ ] Files in §9. Glossary terms only. No Hotfix/Firewall labels. Version string `v0.35.0`.

### 12.3 `pnp/` (graphic-designer)
- [ ] Terminal Mat: 5-level track strips with L1/L3 Breakthrough icons and L4 effects.
- [ ] Player aid: Breakthrough reference, new Patent rates, six-phase aid updated (Phase 5 Step 1, Phase 6).
- [ ] Gray Legacy die face sheet.
- [ ] Client Company cards: no setup bonuses; DTO "once per game".
- [ ] White Hat Dossier cards: no procurement cost.
- [ ] Component count: Gray dice (OQ-8).
- [ ] Regenerate all PnP PDFs (`python3 -m pnp.generate_pnp`).

### 12.4 Project docs
- [ ] `PLAN.md` Phase 43 checkboxes.
- [ ] `FINDINGS.md` Phase 43 entry after telemetry.
- [ ] Mark `scripts/investigate_v350_research_sweep.py` as superseded (header comment) once the port lands; keep it runnable against `legacy_v034()`.

---

## 13. Open Questions for the User

1. **Triage L3 when you can't pay `$3` (or decline):** is the Breakthrough lost (proposed), or can it be claimed in a later Operations Turn?
2. **Triage L3 Gray die zone:** may the replaced Gray die come from any zone (Ready for Release, Scanned Box, Glitched Box; proposed), or only Ready for Release? Does the new die always go to Ready for Release (proposed), even when the Gray die was in the Glitched Box?
3. **Triage L3 with an empty Market:** forfeited with no payment (proposed)?
4. **Triage L3 and other rules:** confirm it doesn't count toward the 2-dice purchase limit and Algorithmic Arbitrage can't discount it (proposed). Is the flat `$3` paid regardless of the Variant Card's printed price (proposed)?
5. **Slush Fund once per game:** the sim auto-fires it on the first Secret loss today. Should it be optional when it would trigger (proposed, with the bot using it at 2+ Secrets or to avoid a Total Data Breach)?
6. **Triage L1 White Contractors:** do the 2 free contractors count toward next round's Progressive Contractor Pricing (proposed: no) and the 3-hire limit (proposed: no)?
7. **Release L4 reroll under a reroll-throttle hazard:** throttle first, then `+1` (proposed)?
8. **Gray die components:** Defense L1 and Release L1 can each add a Gray die (up to 5 per player). Is 5 Gray per player the PnP component count?
9. **Defense L4 cash timing:** paid after damage resolution, so it can't fund the same round's Red ransom (proposed)?
10. **Losing a Purple die** to Spook *Burn Notice* or v3.0 *Return Colored Die* is now permanent (no purchase path). Accept, or exclude Purple from those effects?
11. **Helix and Prometheus** lose their setup bonuses with no replacement this phase (plan §6.7 says identity is revisited later). Confirm that v0.35.0 ships with no replacement.
12. **Operations Turn order:** RULES says "any order"; the sim uses a fixed order (upgrades → Patents → paid `★` → purchases → Arbitrage). OK to keep that sim-only simplification?
13. **Terminology:** this spec uses "L4 effect / capstone" and "Breakthrough die" only as engineering shorthand. RULES text would say "Level 4" and describe the effect, so no new glossary terms. Do you want a printed name for the Level 4 effects (it would be a new term)?
14. **Sim face-name glyph:** sim face names still use the legacy `🔧` string internally (e.g. `+1 🔧`). Rename to `🔬` in this phase (touches bot string matches and fixtures) or defer?
15. **Release L4 extra reroll** was not modeled in the sweep. Accept a re-check during product-owner telemetry, not as a pre-implementation gate?

## Open Question Resolutions (User, 2026-11-06)

All 15 accepted as recommended:
1. Triage L3 unaffordable or declined → forfeited.
2. Gray die may come from any zone; the new colored die goes to Ready for Release.
3. Chosen color empty → choose another color; Market fully empty → forfeited, nothing paid.
4. Flat `$3`, outside the 2-die purchase limit, not discountable by Algorithmic Arbitrage.
5. Slush Fund is optional when it triggers (once per game).
6. Triage L1 free White Contractors don't count toward contractor pricing or hire limit.
7. Release L4: apply reroll throttle first, then +1.
8. PnP: up to 5 Gray dice per player.
9. Defense L4 cash paid after damage (cannot fund that round's Red ransom).
10. Purple die lost to Burn Notice / Return Colored Die is permanently lost; watch in telemetry.
11. Helix and Prometheus get no replacement bonus.
12. Keep the fixed Operations Turn order.
13. No printed name for L4 effects.
14. Rename internal `🔧` face names to `🔬` now.
15. Release L4 validated during product-owner telemetry.
