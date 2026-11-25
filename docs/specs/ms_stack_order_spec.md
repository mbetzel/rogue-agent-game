# Technical Specification: Market Share Markers Arrive On Top, Track Maximum 25, Market Leader Bonus `+3 / +2` at 4P (`v0.52.0`)

**Author:** Principal Engineer
**Date:** 2026-11-25 (revised the same day with the User's rulings on the open questions)
**Target:** `v0.52.0`. **Base:** `GameConfig.v051()` / `v051_roster()` (`sim/config.py:1334-1347`).
**Approved design:** `docs/plans/ms_tie_stagnation_probe.md` §7, §8 and §9 (correction). The User signed it off on 2026-11-25:
- D1: on top. A marker that moves onto an occupied space goes on top and ranks ahead of the markers beneath it. Markers that reach a space at the same moment keep their previous order.
- D2: plain rules wording, **no new glossary term**.
- D3: track maximum 20 → 25 at every player count. Starts stay 14 / 18 / 18.
- D4 (re-decided after the §9 correction): the Market Leader Bonus is 2P `+3 / +1`, 3P `+3 / +2`, 4P `+3 / +2 / +1`.
- D6: ship as `v0.52.0` with new `v052` presets.
- Defaults settled in this spec: the setup stack has the last seat on top. In 2P, SETEC Corp stacks like a player when it moves.
- **Amendment A1 (2026-11-25, user rulings after the implementation port check; overrides every conflicting value below):**
  (a) the setup stack has the **First Player on top** (`market_share_stack_setup = "FIRST_SEAT_TOP"` is the v052 default; `"LAST_SEAT_TOP"` remains a sweep arm). Last seat on top gave 4P seat wins 21 / 24 / 26 / 29%. With the first seat on top it was 2.3–3.3 spread (v0.51: 2.9).
  (b) Schedule `V052_RED_SECRET_PAYOUT = {2: (3, 1), 3: (3, 1, 0), 4: (3, 2, 0, 0)}`: only 4P changes from v0.51. With stack-aware bots and first seat on top, 4P `+3 / +2 / +1` was too soft (PZ 64.3 vs 69.5), while `+3 / +2` is about neutral (68.5). At 3P the user kept `+3 / +1` (PZ 65.9 vs 62.4; `+3 / +2` gave 59.5).
- Rulings on the first draft's open questions (2026-11-25):
  - R1: a Patient Zero's marker stays frozen on the track. It is used only for Total Wipeout ranking and takes no Market Leader Bonus place.
  - R2: Customer Poaching "most" and Red Signature "least" read the stack (the highest-ranked / lowest-ranked eligible marker). No actor choice remains.
  - R3: the Section 5 tiebreakers are trimmed to Market Share position (value, then height). Survivor Secrets ties and Total Wipeout ranking both use only that; Money, ready dice, Research and fewest Under Development drop out of the v052 ranking path.
  - R4: in a Customer Poaching, the actor lands on top of the rival.

**Probe being ported:** `scripts/probe_ms_ties.py` (fixed in plan §9), arms `STACKTOP + AWARET + CAP25` with the corrected schedule override of `red_secret_payout_by_player_count`. The probe is a monkeypatch prototype and still differs from this spec in several places (§11). The SDLC sweep, not the probe, is the reference for balance.

---

## 0. Terminology guardrails

- **No new terms** (D2). Player-facing text uses only existing glossary terms (**Market Share**, **Public Relations Track**, **Market Leader Bonus**, **Customer Poaching**, **SETEC Corp**, **Patient Zero**, **Total Wipeout**, **Market Collapse**, **Target Lock**, *Baffle Echo*), plus plain words: "on top", "beneath", "the higher marker ranks ahead".
- Code identifiers are not game terms and must never reach player-facing text (web log, PnP, TTS): `market_share_stacking`, `ms_stack`, `seq`, "stack height", "stack order", "batch", "arrival", "overtake", `STACKTOP`, `S32`, `S321`, `CAP25`. Never write "Stack Order" as a capitalized term (the D2 alternative was rejected).
- Proposed RULES text (product-owner owns the final wording): *"A Market Share marker that moves onto an occupied space goes on top. A higher marker ranks ahead of those beneath it. Markers that reach a space at the same moment keep their order (the one that was higher stays on top)."* Customer Poaching then reads *"the rival ranked highest on the Market Share track"*, and the Red Signature reads *"the surviving rival ranked lowest"*.

## 1. Scope

| # | Change | Kind | Flag (default = v0.51 behaviour) |
|:---|:---|:---|:---|
| 1 | Every Market Share marker (each player, plus SETEC Corp in 2P) has a strict position: (space, height on that space). Sequential moves land on top. Simultaneous moves keep their previous relative order and land above the markers that did not move. | `[RULE]` | `market_share_stacking = False` |
| 2 | Setup stack: every player starts on the same space. The first player (from the First Player) is at the bottom and the last seat is on top. | `[RULE]` `[TUNE]` | `market_share_stack_setup = "LAST_SEAT_TOP"` (read only when 1 is on) |
| 3 | Rankings read Market Share position = (Market Share desc, height desc). This covers the Market Leader Bonus places (per-round and game-end awards), the Customer Poaching target, and the Red Signature recipient (no actor choice remains, R2). There are no Market Share ties. | `[RULE]` | follows 1 |
| 4 | Final ranking (R3): survivors by Corporate Secrets, then Market Share position. Total Wipeout ranks by Market Share position only. Money, ready dice, Research and fewest Under Development are not used. | `[RULE]` | follows 1 |
| 5 | Track maximum 25. Every hard-coded `20` fallback reads the configured maximum. | `[TUNE]` | existing `market_share_max` (v051 = 20, v052 = 25) |
| 6 | Market Leader Bonus schedule `{2: (3, 1), 3: (3, 2, 0), 4: (3, 2, 1, 0)}` (D4). | `[TUNE]` | existing `red_secret_payout_by_player_count` (§11.1) |
| 7 | Bot MLB estimate: matching a rival's space means ranking above them when you move. When you stay put, the bot uses your real height. | sim bot | `bot_ms_stack_aware = None` (resolves to flag 1) |
| 8 | Telemetry: effective MLB ties (must be 0), raw same-space counts, lead changes, arrivals on top and overtakes by source, stack-decided targets, and MLB places by seat. | telemetry | `ms_tie_telemetry = False` (works with 1 off, so the v0.51 baseline can be measured) |
| 9 | Presets `v052()` / `v052_roster()`. | preset | – |

Out of scope for this spec: `RULES.md` / `RULES_QUICKREF.md` text (including the trimmed Section 5 and the Customer Poaching / Red Signature wording), the 25-space track art in PnP / TTS / web, and the web ruleset. These are owned by the product-owner and graphic-designer after the sweep. §10.4 lists the web hooks the web port needs.

**INV-MS-STACK-00 (parity):** while `market_share_stacking = False` and `ms_tie_telemetry = False`, every existing preset (including `v051()` / `v051_roster()`) replays bit-identically against the v0.51 golden fixtures. That includes the full v0.51 tiebreak hierarchy and the actor-choice hooks for Customer Poaching and the Red Signature. No new end-row keys are added. No new RNG draws are made under any flag (**INV-MS-RNG-01** holds: the stack is fully determined by seat order and move order).

## 2. Engine map (current touch points)

| Where | What it does now | Change |
|:---|:---|:---|
| `sim/engine/state.py:600` `PlayerState.change_market_share` | Clamps to `[0, market_share_max]`, updates ledgers | after the clamp, if `actual != 0` and `self.ms_stack is not None`: `self.ms_stack.on_move(self.player_id, before, after, source)` |
| `sim/engine/core.py:247-250, 292-322` | `init_market_share(start, max)`; `first_player_index` drawn; `setec_market_share = 0` | after `setec_corp_active` is set: build `state.ms_stack` (§3.3) and set `p.ms_stack` on each player |
| `sim/engine/phase2_compiler.py:414-416, 480-484` | Corruption Market Share loss, in a player loop | wrap each loop in a simultaneous batch `"corruption"` |
| `sim/engine/phase3_income.py:792-812` `execute_income` / `finalize_income` | Per-player Income, then `resolve_poaches` | batch `"income"` opened before the player loop (and lazily by `execute_player_income` for the web path). It is closed in `finalize_income` **before** `resolve_poaches` |
| `sim/engine/market_share.py:159-205` `resolve_poaches` | Most-share rival; a tie goes to `choose_poach_target` / `default_poach_target`; rival `-1`, then actor `+1` | under stacking: target = the highest-ranked eligible rival by stack key (§4.5); hooks not called; moves stay sequential (§4.1) |
| `sim/engine/phase4_attack_resolution.py:1119-1135` | Per-survivor Red/Blue loop | batch `"red"` around the loop, closed before `resolve_green` |
| `phase4_attack_resolution.py:767-847` `_resolve_signature_red_lowest_rival` | Frozen post-drain snapshot; least-share recipient; a tie goes to `choose_signature_red_recipient` / heuristic; direct writes to `p.market_share` / `state.setec_market_share` | Epoch 1 = batch `"sig_red_drain"`; recipients picked by stack key after it closes (§4.5); Epoch 2 = batch `"sig_red_gain"`. Each direct write calls `state.ms_stack.on_move(...)`. `ms_cap` (L779) reads the configured maximum (§6) |
| `phase4_attack_resolution.py:850-894` (`_resolve_signature_red_v046`, legacy) | Direct writes | hook calls only (not used by v052, kept consistent) |
| `phase4_attack_resolution.py:1315-1320` | SETEC Corp `+1` if any Red exited | sequential `on_move(SETEC_CORP_ID, ...)`. `max_ms` reads the configured maximum (§6) |
| `sim/engine/phase6_operations.py:373` (regain), `389` (legacy R2), `sim/engine/research_tracks.py:485` (PR L4) | Phase 5 Operations Turns, clockwise | no code change: sequential via `change_market_share` |
| `sim/engine/market_share.py:53-81` | `market_share_places`, `market_leader_bonus_awards`, `expected_market_leader_bonus` | optional `order` / stacked arguments (§5, §7) |
| `sim/engine/secret_faces.py:281-290` `red_secret_payout_awards` | Places by share (ties share) | passes the stack order (§5.2). **This is the Market Leader Bonus in v0.51** (§11.1) |
| `sim/engine/end_game.py:19-38, 255-261, 399-429` | Tiebreak keys; classic MLB; places | trimmed stacked keys and order (§5.3) |
| `sim/bots/market_share_policy.py:75-77, 139-147, 264, 322-332, 397-416`; `sim/bots/secret_face_policy.py:61-69, 76, 96-105` | Bot MLB / payout valuation; `or 20` fallbacks | §7 and §6 |

## 3. State representation

### 3.1 Choice: arrival sequence numbers

The stack is not stored as a list per space. Each marker has one integer **arrival sequence** (`seq`). On a given space, a higher `seq` sits higher. A global counter only ever increases. So:

- rank key of marker `m` = `(space(m), seq(m))`, compared descending;
- height of `m` = `1 + #{live markers on space(m) with seq < seq(m)}` (bottom = 1).

This is O(1) per move and needs no per-space bookkeeping. Moving off a space needs no removal step, because the ranking only reads the relative order. It is equivalent to a physical stack: a marker placed on a space is placed on top of every marker already there, and those all have smaller `seq`.

### 3.2 New module `sim/engine/ms_stack.py`

```python
SETEC_CORP_ID = -1  # re-exported from market_share

class MarketShareStack:
    seq: Dict[int, int]          # marker id (player_id, or SETEC_CORP_ID) -> arrival sequence (unique, INV-MS-STACK-01)
    space: Dict[int, int]        # marker id -> space as last reported to the stack (audit, INV-MS-STACK-10)
    counter: int                 # max seq handed out so far
    batch_tag: Optional[str]     # open simultaneous batch, or None
    _batch_start: Dict[int, Tuple[int, int]]  # marker id -> (space, seq) when it first moved in the open batch
    tel: MsStackTelemetry        # §8 counters

    @classmethod
    def setup(cls, seat_order_from_first: List[int], start_space: int, setec_space: Optional[int]) -> "MarketShareStack"
    def on_move(self, mid: int, before: int, after: int, source: str) -> None
    def begin(self, tag: str) -> None          # opens a batch; nested begin with an open batch raises
    def end(self) -> None                       # closes the batch and re-stacks movers (§4.2); no-op if none open
    def key(self, mid: int) -> Tuple[int, int]  # (space, seq); raises if a batch is open (INV-MS-STACK-09)
    def order(self, mids: Iterable[int]) -> List[int]   # top first, by key desc
    def highest(self, mids: Iterable[int]) -> int       # order(mids)[0]
    def lowest(self, mids: Iterable[int]) -> int        # order(mids)[-1]
    def height(self, mid: int, live: Iterable[int]) -> int
    def audit(self, state) -> None              # every marker's space == its real Market Share
```

- `GameState.ms_stack: Optional[MarketShareStack] = None`. `PlayerState.ms_stack` holds a reference to the same object, or `None`. It is excluded from `__eq__` / repr and survives `copy.deepcopy` through the deepcopy memo, which keeps one shared object. No new fields exist when the flag is off (INV-MS-STACK-00).
- `space` is updated on every `on_move`, inside batches too. `seq` changes only on sequential moves and at `end()`.

### 3.3 Setup (`market_share_stack_setup = "LAST_SEAT_TOP"`)

`seat_order_from_first = [players[(first_player_index + k) % n].player_id for k in range(n)]`. Seat `k` gets `seq = k + 1`, so the First Player has `seq 1` (bottom) and the last seat has `seq n` (top). In 2P with SETEC Corp active, SETEC Corp gets `seq 0` on space `0`. `counter = n`. This uses the existing `first_player_index`. **No RNG** (INV-MS-STACK-06).

Accepted option values: `"LAST_SEAT_TOP"` (the default and the rule) and `"FIRST_SEAT_TOP"` (a sweep arm for the seat-skew watch item only, never a preset). Validation: `market_share_stacking` needs `is_market_share`, and the option must be in that set.

## 4. Movement sources and ordering rules

### 4.1 Sequential move (outside a batch)

`on_move(mid, before, after, source)` with `before != after`: `counter += 1; seq[mid] = counter; space[mid] = after`. The mover is on top of its new space (INV-MS-STACK-02). Moving onto an empty space is the same operation.

### 4.2 Simultaneous batch

Inside `begin(tag) … end()`, `on_move` only records `_batch_start[mid] = (before, seq[mid])` the first time `mid` moves, and updates `space`. At `end()`:

1. `movers` = the markers in `_batch_start` whose current space differs from their start space. A net-zero move inside one batch, and a move clamped to `actual = 0` (which never reaches the hook), are **not** moves: those markers keep their `seq`.
2. Sort the movers by their start key `(start_space, start_seq)` **ascending**.
3. In that order: `counter += 1; seq[m] = counter`.

The result: every mover lands above the markers that did not move on its destination space (on-top arrival). Movers that reach the same space keep their previous order, because the one that was higher before gets the larger new `seq` (INV-MS-STACK-03).

### 4.3 Source table

| Phase / step | Source(s) | Timing | Rule | Notes |
|:---|:---|:---|:---|:---|
| Setup | – | – | §3.3 | last seat on top |
| Phase 2 Corruption Track MS loss (both code paths) | `corruption` | simultaneous | batch `"corruption"` | all targets in one batch |
| Phase 3 Income: Red F1 / Yellow MS faces, R1, R2 Ad Campaign, B2 Deep Data Vault | `face`, `r1`, `b2`, `r2` | simultaneous | batch `"income"` | the RULES say Phase 3 is simultaneous; the sim's player-index loop order must not matter (INV-MS-STACK-04) |
| Phase 3 Customer Poaching (after all Income) | `poach_lost`, then `poach_gained` | sequential, clockwise from the First Player, die by die | §4.1 per call; target by §4.5 | within one poach the rival moves first, then the actor. If both land on the same space, **the actor is on top** (R4, confirmed) |
| Phase 4 step 1 Red (each survivor), including Aegis *Baffle Echo* (one marker moves 1 less) and the clamp at 0 | `red` | simultaneous | batch `"red"` | uniform Red moves a whole stack as a unit (INV-MS-STACK-05) |
| Phase 4 step 4 Red Signature, Epoch 1 drain | `sig_red_drain` | simultaneous | batch `"sig_red_drain"` | closed before recipients are picked (§4.5) |
| Phase 4 step 4 Red Signature, Epoch 2 gains (players and SETEC Corp, after per-recipient sums and the cap) | `sig_red_gain` | simultaneous | batch `"sig_red_gain"` | a separate batch after Epoch 1 (the RULES say "first … then"), so a gain that lands on a drained locker's space goes on top of it. A locker who is also a recipient ends on top of its original space |
| Phase 4 step 5 SETEC Corp `+1` (2P) | `setec_advance` | sequential | §4.1 | after all damage, so SETEC Corp lands on top of any player already on that space |
| Phase 5 regain (Public Relations), PR L4 capstone `+2`, legacy Phase 5 R2 | `regain`, `pr_l4`, `r2` | sequential, clockwise Operations Turns | §4.1 per call | a multi-step regain is several `+1` calls; only the last space matters, and the marker ends on top of it |
| Phase 6 | – | – | – | nothing moves Market Share |

Every Market Share write must go through `change_market_share` or an explicit `ms_stack.on_move` call (INV-MS-STACK-10, enforced by `audit`). A future source must be added to this table and given a timing.

### 4.4 Patient Zero (R1)

A Patient Zero's marker **stays frozen on its space**: it never moves and its `seq` never changes after the breach. The Phase 2 corruption loop is the only path that can touch a breached player in the same step, and it does so before elimination. A marker still physically stays on the track, so later arrivals on that space go on top of it. It is left out of every live ranking: the MLB (no place, survivors below move up), the Customer Poaching target and the Red Signature pool. Its height telemetry counts only live markers. It is read only by the Total Wipeout ranking (§5.3), which compares the kept Market Share and then the frozen `seq`.

### 4.5 Targets read the stack (R2)

Under stacking, no tie remains and no actor-choice hook is called (`choose_poach_target`, `choose_signature_red_recipient`, `default_poach_target`, `default_signature_red_recipient_heuristic` are bypassed; they stay for flag-off presets).

- **Customer Poaching:** eligible rivals are unchanged (not the actor, not Patient Zero, Market Share `> 0`). The target is `ms_stack.highest(eligible)`. It is re-read before every poach die, after the previous poach's two sequential moves. "No target" is unchanged.
- **Red Signature (lowest rival):**
  1. Epoch 1 drains every locker in batch `"sig_red_drain"` and closes it.
  2. The pool is the existing `red_signature_recipient_pool` membership: survivors not breached this phase, plus SETEC Corp in 2P when `signature_red_setec_eligible`. Its keys are now the live post-drain stack keys, whose spaces equal the old snapshot values.
  3. Each locker's recipient is `ms_stack.lowest(pool − {locker})`. All lockers read the same post-Epoch-1 order (no re-read between lockers, as today).
  4. The gains are summed per recipient, capped, and applied in batch `"sig_red_gain"`.
  5. Fizzles (empty pool), mutual-cancel and gift-to-locked telemetry are unchanged.
- **Not changed:** Market Collapse reads the space only. Phase 2 Version comparison (off since v038c) would read the space only if re-enabled.

## 5. Ranking

### 5.1 `sim/engine/market_share.py`

```python
def stack_order(state, mids: Iterable[int]) -> Optional[Dict[int, int]]:
    """mid -> seq when state.ms_stack is set, else None. Raises if a batch is open."""

def include_setec_in_order(order: Optional[Dict[int, int]], state) -> Optional[Dict[int, int]]

def market_share_places(shares: Dict[int, int], order: Optional[Dict[int, int]] = None) -> Dict[int, int]:
    """order None: legacy competition ranking (INV-MLB-TIES-01). order given: strict places 1..k by
    (share desc, order[pid] desc) (INV-MS-STACK-08)."""

def market_leader_bonus_awards(shares, schedule, order=None) -> Dict[int, Tuple[int, int]]
```

### 5.2 Per-round Market Leader Bonus (`secret_faces.red_secret_payout_awards`)

Build `shares` as today (survivors only, so Patient Zeros take no place), add SETEC Corp with `include_setec_in_shares`, and pass `order = include_setec_in_order(stack_order(state, shares), state)`. SETEC Corp can hold any paid place on height and deny that award, as today. In 4P a 3rd place `+1` is now paid (D4). `fire_round_payout` is unchanged, apart from new telemetry fields (§8).

### 5.3 Game end (`end_game.evaluate_end_game`) (R3)

- `places` (L260) and both award paths (L261 classic MLB, inert in v052, and L273 end payout) pass the order. Patient Zeros take no MLB place (R1).
- Each ranking row gets `market_share_stack_seq` (int) **only when stacking is on**. For a Patient Zero it is the frozen `seq`.
- New, trimmed keys are used only when stacking is on. `_standard_key_ms` / `_wipeout_key_ms` and the full v0.51 hierarchy stay untouched for every older preset (INV-MS-STACK-00):

```python
def _standard_key_ms_stack(r):  # Corporate Secrets, then Market Share position (value, then height). Nothing else.
    return (r["secrets"], r["market_share"], r["market_share_stack_seq"])

def _wipeout_key_ms_stack(r):   # Market Share position only (breach depth ignored, as before)
    return (r["market_share"], r["market_share_stack_seq"])
```

  `_KEY_FIELDS` maps them to `("secrets", "market_share", "market_share_stack")` and `("market_share", "market_share_stack")`, so `_tiebreak_decided_by` reports `"market_share_stack"` when height decides.
- Selection: `std_key` / `wipe_key` become the `_stack` variants when `cfg.market_share_stacking`. This applies to the survivors sort, the eliminated sort and the Total Wipeout sort. The `tiebreak_order` / `is_six_phase` branch structure is otherwise unchanged.
- **Consequences:**
  - The key is strict, so a winner is always unique; `winner_ids` has length 1 and "victory is shared" cannot happen under v052.
  - Money, ready colored dice, Research and Under Development counts are still recorded in the rows for telemetry but are never compared.
  - `market_leader_bonus_tied_paid_place` must always be `False` (INV-MS-STACK-08).

## 6. Track maximum 25 (INV-MS-CAP-01)

- `v052` sets `market_share_max = 25`. Players read it through `get_market_share_max` → `init_market_share(max_share=…)`, which already works. Starts are unchanged (`V046_MARKET_SHARE_START`).
- Replace every `20` fallback with the configured maximum. Add one helper, `GameConfig.ms_max() -> int` = `self.get_market_share_max(self.num_players)`:
  - `phase4_attack_resolution.py:779` (`ms_cap`) and `:1317` (`max_ms`) → `cfg.ms_max()`;
  - `sim/bots/market_share_policy.py:264` → `state.config.ms_max()`;
  - `sim/bots/secret_face_policy.py:76` `player.market_share_max or 20` → `player.max_market_share`;
  - `state.py:550` `return 20` → `DEFAULT_MARKET_SHARE_MAX` (only reached with no config).
- With 25 set, the PR regain, R2, B2 and PR L4 clamps already read `player.market_share_max`.
- Watch item, not a change: `red_buy_share_frac * market_share_max` (`market_share_policy.py:471`) moves from 10 to 12.5. The probe ran the same way.

## 7. Bots (INV-MS-STACK-BOT-01)

`bot_ms_stack_aware: Optional[bool] = None` resolves to `market_share_stacking` in `__post_init__`. `True` with stacking off is a validation error. `False` with stacking on is an ablation arm.

```python
def expected_market_leader_bonus(share, rival_shares, schedule, *, stacked=False, ahead_on_space=0) -> float:
    """stacked=False: legacy span average (unchanged; existing tests hold).
    stacked=True: idx = #rivals with r > share + ahead_on_space; returns schedule[idx] (0 past the end).
    Matching a rival's space ranks above them unless the caller says otherwise via ahead_on_space."""

def ahead_on_space(player, state, share) -> int:
    """#live rivals (incl. SETEC Corp) on `share` with a higher seq than the player, if share == the player's
    current Market Share (the player stays put); else 0 (a mover arrives on top)."""
```

- `market_share_policy.expected_payout_value(share, rivals, sched, *, stacked=False, ahead_on_space=0)` forwards the arguments.
- `payout_share_delta(player, state, before, after, rivals, pol)`: with stacking aware, each side is evaluated with `stacked=True` and `ahead_on_space(player, state, x)` for `x ∈ {before, after}`. This is used by `urgent_regain` (L402) and `share_value` (secret_face_policy L97). Result: regaining only up to the leader's space now has value, and a player already on top of a shared space sees no gain in passing. With the 4P `+3 / +2 / +1` schedule, the 3rd place now has value too (read from the schedule, no code change).
- `secret_face_policy.py:69` (Red Secret valuation at the current share): `stacked=True`, real `ahead_on_space`.
- `marginal_block_value` (L322-332) and `share_value`'s classic-MLB branch (L98-105) evaluate hypothetical post-Red shares against estimated rivals: `stacked=True`, `ahead_on_space=0`. This is a documented approximation (same as probe `AWARET`).
- The classic-MLB branches (`leader_bonus_active`) are inert in v052, because `market_leader_bonus_by_player_count = {}`. They still pass `stacked` for consistency.
- Targeting hooks (`choose_poach_target`, `choose_signature_red_recipient`) are not called under stacking (§4.5). No bot change is needed for them.
- Bots only read `seq` and never write it. Reads during an open batch see the pre-batch `seq`. That is allowed for bots, but scoring and targeting APIs raise.

## 8. Telemetry (`ms_tie_telemetry`)

Counters live on `GameState.ms_tie_tel` (a `Counter` plus small lists). They are emitted as an `ms_tie` block in the end row / `EndGameResult` only when the flag is on. They are computed with stacking **on or off**, so `v051_roster + ms_tie_telemetry` gives the baseline. Telemetry never changes play (INV-MS-TEL-01: results are identical with the flag on and off).

| Key | Definition | Acceptance |
|:---|:---|:---|
| `mlb_awards` | Per-round + end MLB awards fired | – |
| `mlb_raw_tie_1st` | Awards where the top two participants share a space | indicative (§7 probe) 4P ≈ 28% |
| `mlb_effective_tie_1st` | Awards where >1 participant gets place 1 | **must be 0 with stacking on**; v051 ≈ 32% (4P) |
| `mlb_effective_tie_paid` | Awards where any place with a positive bonus is shared | **0 with stacking on** |
| `mlb_stack_decided_paid` | Awards where two adjacent places share a space and their bonuses differ | – |
| `mlb_first_by_seat[seat]`, `mlb_secrets_by_seat[seat]` | Seat = offset from the starting First Player | seat-skew watch |
| `rounds_obs`, `top_same_space`, `top_same_space_at_max`, `any_same_space` | End-of-round (after Phase 6) board reads over live markers + SETEC Corp | – |
| `lead_changes`, `lead_back`, `lead_changes_same_space` | Sole leader (place 1; under stacking off: unique place 1 or none) changes between round ends; `lead_back` = it returns to the leader before the last one; `_same_space` = the old and new leader share a space | indicative (§7 probe) 4P 2.9/g, 32% |
| `arrivals_occupied[source]`, `overtakes[source]` | Stacking on: a mover lands on a space with ≥1 live marker / ends above a marker that ranked above it before | shows Phase 5 leapfrogging |
| `poach_stack_decided`, `sig_red_stack_decided` | Stacking on: the target / recipient shared its space with another eligible marker (formerly an actor choice). Stacking off: the hook was consulted | R2 impact |
| `tiebreak_by_stack` | Games whose winner was decided by `market_share_stack` (survivor or Total Wipeout) | R3 impact |
| `ms_end_spread`, `ms_end_same_space` | Max − min live Market Share at game end; any shared space at game end | indicative (§7 probe) 4P spread 4.7 |
| `setec_arrivals_on_top` | 2P: SETEC Corp lands on an occupied space | – |

The sweep summary (`scripts/run_v380_secret_faces_sweep.py` summarizer, or a thin `scripts/run_v052_ms_stack_sweep.py`) reports per player count: PZ / MC / Singularity, rounds, the table above, winner Secrets, MLB Secrets per game, company win spread and seat win spread.

**Probe baseline (plan §9, corrected, 3,000 games per pod).** These are the comparison rows for the SDLC sweep. They include neither R2 (stack-read targets) nor R3 (trimmed tiebreak), so small differences are expected.

| Pod | Schedule | Rounds | PZ | MC | Sing | MLB Secrets/g | Winner Secrets | Company spread | Seat spread |
|---|---|---|---|---|---|---|---|---|---|
| 2P v0.51 | +3/+1 | 8.2 | 42.2 | 28.1 | 20.8 | 10.8 | 9.4 | 18.5 | 1.9 |
| 2P v052 | +3/+1 | 8.1 | 45.3 | 27.7 | 18.4 | 9.5 | 9.1 | 14.6 | 3.6 |
| 3P v0.51 | +3/+1 | 8.2 | 61.4 | 12.0 | 24.5 | 17.2 | 11.4 | 15.0 | 2.1 |
| 3P v052 | +3/+2 | 8.1 | 62.7 | 12.2 | 23.2 | 18.4 | 12.0 | 15.0 | 3.0 |
| 4P v0.51 | +3/+1 | 8.1 | 67.0 | 12.3 | 19.7 | 21.9 | 12.5 | 11.4 | 1.9 |
| 4P v052 | +3/+2/+1 | 8.2 | 66.6 | 10.6 | 22.2 | 24.8 | 12.6 | 10.5 | 4.0 |

Watch items carried to the sweep: 2P PZ +3.1pp (stacking and the cap alone); seat spread (2P 3.6, 3P 3.0, 4P 4.0 vs ~2 at v0.51); 4P MLB Secrets +2.9/g. The lead-change / raw-tie / end-spread figures in the table above come from the §7 arms, which used the invalid S32, so treat them as indicative only.

## 9. Config and presets

New fields (`sim/config.py`, near `market_share_max`):

```python
market_share_stacking: bool = False
market_share_stack_setup: str = "LAST_SEAT_TOP"        # [TUNE] "LAST_SEAT_TOP" | "FIRST_SEAT_TOP" (sweep arm only)
bot_ms_stack_aware: Optional[bool] = None              # None -> market_share_stacking
ms_tie_telemetry: bool = False
```

```python
V052_MARKET_SHARE_MAX = 25                                              # [TUNE] D3
V052_RED_SECRET_PAYOUT = {2: (3, 1), 3: (3, 2, 0), 4: (3, 2, 1, 0)}     # [TUNE] D4 (the Market Leader Bonus)

_V052 = (("market_share_stacking", True), ("market_share_stack_setup", "LAST_SEAT_TOP"),
         ("market_share_max", V052_MARKET_SHARE_MAX),
         ("red_secret_payout_by_player_count", dict(V052_RED_SECRET_PAYOUT)),
         ("ms_tie_telemetry", True))

@classmethod
def v052(cls, **overrides):        # v0.52.0 Market Share on-top stacking + max 25 + MLB 3P +3/+2, 4P +3/+2/+1. Inherits v051().
    for k, v in _V052: overrides.setdefault(k, v)
    return cls.v051(**overrides)

@classmethod
def v052_roster(cls, **overrides): # v0.52.0 + the v0.51 roster bots (sweep default). Inherits v051_roster().
    for k, v in _V052: overrides.setdefault(k, v)
    return cls.v051_roster(**overrides)
```

- `market_leader_bonus_by_player_count` stays `{}` (inherited from v038c). The 4P schedule passes `_normalize_place_schedule` (non-increasing, length ≤ n).
- The trimmed tiebreak (§5.3) and the stack-read targets (§4.5) follow `market_share_stacking`. They get no separate flags.
- Validation: `market_share_max >= max(market_share_start_by_player_count.values())`.

## 10. Invariants

| ID | Statement |
|:---|:---|
| INV-MS-STACK-00 | Flags off → bit-identical to v0.51 (§1), including the full tiebreak hierarchy and the targeting hooks. |
| INV-MS-RNG-01 | No RNG is drawn by the stack, the ranking, the targeting, the bots' stacked estimate or telemetry. Under v052, `engine.rng` state after setup equals v051's for the same seed. |
| INV-MS-STACK-01 | `seq` values are unique across all markers (players + SETEC Corp), so the key `(space, seq)` is a strict total order. |
| INV-MS-STACK-02 | After a sequential move, the mover has the maximum `seq` of all markers. |
| INV-MS-STACK-03 | After a batch, for markers m1 above m2 before the batch with actual deltas `d1 >= d2`, m1 is still above m2. Movers land above the non-movers on their destination. Markers that did not move keep their `seq`. |
| INV-MS-STACK-04 | A batch's result does not depend on the order in which its moves are reported. |
| INV-MS-STACK-05 | A uniform Red (same actual loss for all, no clamp, no Baffle Echo) leaves the live ranking unchanged. |
| INV-MS-STACK-06 | Setup: all players on the start space; heights bottom → top follow seat order from the First Player (last seat on top); SETEC Corp alone at 0. |
| INV-MS-STACK-07 | A Patient Zero's marker stays frozen (space and `seq`) after the breach. It takes no MLB place, is never a Customer Poaching target or Red Signature recipient, and is ranked only in a Total Wipeout. |
| INV-MS-STACK-08 | With stacking on, MLB places are exactly `1..k` (k = participants); `mlb_effective_tie_1st == mlb_effective_tie_paid == 0`; `market_leader_bonus_tied_paid_place` is always False. |
| INV-MS-STACK-09 | Scoring and targeting reads (`stack_order`, `key`, `highest` / `lowest`, MLB, end game) raise if a batch is open. Every batch opened in a phase is closed in that phase. |
| INV-MS-STACK-10 | At every phase boundary, `ms_stack.space[m]` equals each marker's Market Share (`audit`). No direct write bypasses the hook. |
| INV-MS-STACK-11 | Final ranking under stacking: survivors by (Secrets, Market Share, `seq`); Total Wipeout by (Market Share, `seq`). No other field is compared, and the winner is unique. |
| INV-MS-STACK-12 | Customer Poaching targets the highest-ranked eligible rival; the Red Signature recipient is the lowest-ranked marker in the post-drain pool. No actor-choice hook is called under stacking. |
| INV-MS-CAP-01 | No `20` literal is used as a Market Share cap in `sim/engine` or `sim/bots`. Every clamp (player, SETEC Corp, Red Signature) uses the configured maximum. |
| INV-MS-MLB-01 | v052 schedule: 2P `(3, 1)`, 3P `(3, 2, 0)`, 4P `(3, 2, 1, 0)` for both the per-round and the end award. |
| INV-MS-STACK-BOT-01 | With stacking aware: matching a rival's space when moving is valued as the better place; staying put uses the real height; legacy mode is unchanged. |
| INV-MS-TEL-01 | Telemetry is passive (identical results with `ms_tie_telemetry` on or off). |

### 10.4 Web port hooks (for the later web follow-up)

The web controller splits Phase 3 (`execute_player_income` + `finalize_income`) and Phase 4 (`resolve_damage=False`). It must open and close the `"income"` and `"red"` batches at the same points. `finalize_income` closes `"income"`. INV-MS-STACK-09 catches any batch left open. Under v052, the web must not prompt for a Customer Poaching target or a Red Signature recipient (§4.5).

## 11. Probe deviations (read before comparing with the plan)

1. **Fixed:** S32 originally overrode the wrong schedule. Plan §9 corrected the probe and re-ran it, and the §8 baseline uses those rows. The plan's §3–§7 S32 / S321 rows are invalid.
2. The probe gave Phase 3 face gains separate ticks in player-index order. The spec treats them as one simultaneous batch.
3. The probe's Red Signature wrote around `change_market_share`, so drains and gains never re-stacked. The spec gives each epoch its own batch.
4. The probe gave `red` and `corruption` no ticks, so markers kept old ticks. That is wrong when a mover lands on a non-mover's space (the clamp at 0, Baffle Echo). The spec puts movers on top.
5. The probe's SETEC Corp ticked lazily, at the next ranking read. The spec ticks at the move.
6. The probe kept the actor choice for Customer Poaching and Red Signature ties (R2), and the full v0.51 tiebreak hierarchy (R3).

## 12. Unit test plan (`tests/test_v052_ms_stack.py`, unittest, `-q`)

1. **Config:** v052 / v052_roster values (4P schedule `(3, 2, 1, 0)`); v051 unchanged (stacking off, max 20, `(3, 1, 0, 0)`); validation errors (stacking without Market Share, bad setup option, `bot_ms_stack_aware=True` with stacking off, max < start); v052_roster keeps the v051_roster bot params.
2. **Setup:** 3P and 4P with `first_player_index = 2`, giving the bottom → top order 2, 3, 0, 1; 2P SETEC Corp `seq 0` at 0; RNG state equal to v051 after setup.
3. **Sequential:** a regain onto an occupied space lands on top; a multi-step regain ends on top; poaching where rival and actor land on the same space puts the actor on top (R4); PR L4; SETEC Corp `+1` onto a player's space lands on top.
4. **Batches:**
   - uniform Red keeps the ranking (05);
   - at the clamp at 0, the marker from 2 lands above the marker from 1, and both land above a marker already at 0;
   - with Baffle Echo, the marker that doesn't move gets covered;
   - Phase 3 gains from two spaces to one keep the previous order, with the same result when the player loop is reversed (04);
   - a mover lands above a non-mover;
   - a clamp at max keeps `seq`, and so does a net-zero move in a batch;
   - a nested `begin` raises, and a scoring or targeting read inside an open batch raises (09).
5. **Targets (R2):**
   - with two rivals tied on the most Market Share, the poach takes the one on top and the hook is never called (mock asserts no call);
   - the target is re-read after a previous poach;
   - the Red Signature recipient is the lowest-ranked post-drain marker, including a drained locker whose new space it shares with another marker;
   - 2P SETEC Corp is the recipient when it ranks lowest;
   - under v051 the hooks are still called.
6. **Red Signature moves:** drain batch then gain batch; a locker who is also a recipient ends on top of its original space; a 2P SETEC Corp recipient lands on top; the gain cap is 25.
7. **Ranking / MLB:** `market_share_places` with order is strict; legacy behaviour without order (the existing `test_v370` cases pass); 3P `(3, 2, 0)` and 4P `(3, 2, 1, 0)` with markers sharing spaces pay by height; 2P SETEC Corp on top of the leader's space takes 1st; `red_secret_payout_awards` and the end payout use height.
8. **End game (R3):**
   - with equal Secrets and equal Market Share, height decides even when the lower marker has more Money (`tiebreak_decided_by == "market_share_stack"`);
   - with equal Secrets, a different Market Share decides;
   - Total Wipeout ranks by Market Share, then the frozen `seq`, and ignores Money, including for a player who breached earlier;
   - `winner_ids` has length 1, and `market_leader_bonus_tied_paid_place` is False;
   - v051 still reaches the Money tiebreak.
9. **Patient Zero (R1):** excluded from MLB places, the poach target and the Red Signature pool; `seq` frozen; a later arrival lands on top of the frozen marker; survivors below move up.
10. **Cap:** player, SETEC Corp and Red Signature clamps at 25; a source-scan test over `sim/engine` and `sim/bots` finds no `or 20` / `, 20)` Market Share fallback (CAP-01).
11. **Bots:** stacked `expected_market_leader_bonus` (matching = above, `ahead_on_space` lowers the place, past the schedule end = 0, 4P 3rd place = 1); `payout_share_delta` > 0 for a regain that only matches the leader, and 0 for passing when already on top of a shared top space; the legacy equality test (`test_v380_secret_faces.py:1303`) still holds with stacked off.
12. **Smoke / audit:** v052_roster at 2 / 3 / 4P × 20 seeds with `audit` at every phase boundary; `mlb_effective_tie_1st == 0`; unique `seq`; a unique winner in every game; the same seed twice gives identical results.
13. **Parity:** the existing v0.51 golden fixtures and the parity suites pass unchanged (00). `v051_roster` with `ms_tie_telemetry=True` gives the same results as without it (TEL-01).

## 13. Open questions

All of the first draft's open questions are resolved (R1–R4, D4 re-decided). No blocking questions remain. Non-blocking items for the SDLC sweep:

- Seat spread is 3.0–4.0 vs ~2 at v0.51 (setup stack plus Phase 5 order). `market_share_stack_setup = "FIRST_SEAT_TOP"` is available as a diagnostic arm.
- 2P PZ is +3.1pp from stacking and the cap alone (the schedule is unchanged at 2P).
- R2 and R3 were not in the probe. Compare the `poach_stack_decided`, `sig_red_stack_decided` and `tiebreak_by_stack` counts against the §8 baseline.
