# Technical Architecture Specification: Phase 49 (v0.38.0 candidate)
## Secret Faces, Processing Box, Glitched Shield Slots & Company Starting Die

**Author:** Principal Engineer / Architect
**Status:** Draft for implementation. The Open Questions in §14 need an answer, or acceptance of the recommended default, before the `senior-engineer` starts.
**Target Version:** `v0.38.0` candidate (sim only; RULES.md / PnP / web are Phase B after balance sign-off)
**Source of Truth:** `FINDINGS.md` §42 (locked package, implementation plan, User glossary decisions 2026-11-07); `PLAN.md` Phase 49. The scratchpad probes named in §42 (`yield_model.py`, `grid_probe.py`, etc.) are evidence only, not reference implementations.
**Dependencies:** `RULES.md` v0.37.0 (§4 Phases 1–6, §5, §6A–6D, §7 Glossary); [v370 spec](./v370_market_leader_bonus_spec.md) (Market Leader Bonus, INV-MLB-*); [v360 spec](./v360_market_share_red_rework_spec.md) (INV-MS-*); [reference bot spec](./reference_bot_spec.md) (fast_clone, RB-07 drift guard); [lever A spec](./lever_a_roster_upgrade_spec.md) (roster rule, `v037_roster()`).

**Target Components:**
- `sim/config.py` (levers, `GameConfig.v038()` / `v038_roster()`), `sim/entities.py` (Face, die factories, Variant Cards, Company starting colour, Corruption space semantics)
- `sim/engine/state.py` (PlayerState fields, telemetry), `phase1_roll_deploy.py`, `phase2_threat.py` / `phase2_compiler.py` (Corruption "glitch X dice"), `phase3_income.py` (B3, Y3, Jumper Diagnostics), `phase4_attack_resolution.py`, `phase5_pipeline_shift.py`, `phase6_operations.py` (B2, dirty income backlash), `research_tracks.py` (Triage L1, Defense Grid L3 flag), `market_share.py` (Market Collapse gate), `end_game.py` (stranded Secrets), `core.py` (setup), `fast_clone.py`
- `sim/bots/*` (base, market_share_policy, adaptive_balanced, mixed_policy, reference_search and the archetypes)
- New: `tests/fixtures/v037_parity/`, `tests/test_v380_secret_faces.py`, `scripts/run_v380_secret_faces_sweep.py`

**Terminology.** Only RULES.md §7 terms plus the three User-approved terms: **Secret face**, **Processing Box**, **Glitched Shield Slot**. "Glitched Box" is retired under v0.38 (the sim attribute `glitched_dice` is kept as an internal name only, §3.1). The `Glitch` face survives only on White Contractor dice. "Color-Specific Shield", "Red / Blue / Green Shields", "Two-Stage Defensive Blocking" and Market Collapse (as an end trigger) remain valid for the v0.37 path and are retired only in Phase B. Code identifiers such as `secret_yield`, `slot_clear` are implementation names, not game terms, and must not appear in player-facing text.

---

## 1. Executive Summary

### 1.1 Changes (all behind levers; `GameConfig()` and `GameConfig.v037()` stay v0.37.0 bit-identical)

| # | Change | Lever(s) (§2) |
|---|---|---|
| C1 | **Secret face** = Face 5 on Red, Blue, Green and Purple dice (replaces their `Glitch` face). A die showing it after rerolls goes to the **Processing Box** and produces no other output. | `secret_face_enabled`, `die_face_profile` |
| C2 | **Processing Box** replaces the Glitched Box: Under Development = Processing Box → Scanned Box. The Secret is **banked when the die leaves the Processing Box** (Phase 5 Conveyor Triage, Magnetic Splice, Jumper Diagnostics, B3). Dice still in the Processing Box at game end **lose** their Secret. Free rerolls unchanged; the Secret face may be rerolled. | `secret_face_enabled` |
| C3 | **Colour yields** at banking time: Red 3/2/1/0 at Market Share 9+/5–8/1–4/0; Blue 1, +1 if the owner blocked ≥1 Blue cube that round, +1 at Defense Grid Level 3 (max 3); Green 3 − owner's Glitched Shield Slots (min 0); Purple 1. | `secret_yield_*` |
| C4 | **12-point Market Share track** (start = max = 12 at all player counts). **Market Collapse off** as an end trigger. | `market_share_start_by_player_count`, `market_collapse_enabled` |
| C5 | **No colored shields.** All shields are `Block 1 Any` from Gray, White and Purple dice. Phase 4 Stage 1 is empty; only the Stage 2 Any split remains. | `colored_shields_enabled` (via `die_face_profile`) |
| C6 | **Yellow fuel die**: choice faces (`$` / 🔬), no Secret face, no shields. | `die_face_profile` |
| C7 | **Glitched Shield Slots.** Each unblocked Green cube glitches 1 shield slot (instead of glitching an In Production die); Corruption "glitch X dice" spaces glitch X slots. A glitched slot cannot hold a shield. A die placed on a glitched slot in Phase 1 cleans it and goes to the Scanned Box. Once per Phase 5, if ≥1 die graduates to Ready for Release, clear 1 slot. | `glitched_shield_slots_enabled`, `slot_graduation_clear` |
| C8 | **White Contractor `Glitch`** faces discard the die (unchanged behaviour at Phase 1 Step 5; under v0.38 there is no other Glitch path). | — (already v0.37 behaviour) |
| C9 | **Company starting die**: each Client Company names a Red, Blue or Green starting die (two Companies per colour); it replaces 1 starting Gray. | `company_starting_die_enabled`, `company_starting_colors` |
| C10 | **Triage Level 1 Breakthrough** gives 1 Gray Legacy die instead of 2 White Contractor dice. | `triage_l1_breakthrough` |
| C11 | **Starting Corporate Secrets** lever: 3P 4–5 for the probe; 2P / 4P fitted by the sweep. | `starting_secrets_by_player_count` (existing) |
| C12 | **Draft face / Variant Card / power retargets** (§42 "Draft") as a named, switchable profile so the sweep can A/B them. | `die_face_profile`, `variant_profile`, `power_profile` |

### 1.2 v0.37 vs v0.38 at a glance

| Item | v0.37.0 | v0.38.0 candidate |
|---|---|---|
| Face 5 (R/B/G/Purple) | `Glitch` → Glitched Box | Secret face → Processing Box, Secret banked on exit |
| Face 5 (Yellow) | `Glitch` | Fuel face (§4.2) |
| Shields | Colour-specific + Any (two stages) | Any only (Gray, White, Purple; G2 if kept) |
| Unblocked Green | Glitch 1 In Production die | Glitch 1 shield slot |
| Corruption "glitch X dice" | Glitch X In Production dice | Glitch X shield slots |
| Market Share | 17 / 18 / 18, Market Collapse on | 12 / 12 / 12, Market Collapse off |
| Starting pool | 3 Gray + 1 Purple | 2 Gray + 1 Purple + 1 Company starting die |
| Triage L1 | 2 White Contractors | 1 Gray Legacy die |
| Starting Secrets | 9 / 8 / 9 | `[TUNE]` default 5 / 5 / 5 (OQ-1) |

---

## 2. Configuration (`sim/config.py`)

### 2.1 New fields (append after `market_leader_bonus_by_player_count`)

```python
# --- v0.38.0 Secret faces / Processing Box (INV-SF-*). Defaults reproduce v0.37.0 bit-identically. ---
secret_face_enabled: bool = False
die_face_profile: str = "V037"           # "V037" | "V038_DRAFT"  (Red/Blue/Green/Yellow/Purple face tables, §4)
variant_profile: str = "V037"            # "V037" | "V038_DRAFT"  (Variant Card texts, §5)
power_profile: str = "V037"              # "V037" | "V038_DRAFT"  (Magnetic Splice, Jumper Diagnostics,
                                         #  Brute-Force Bypass, Arbitrary Code Execution, §6)
# [TUNE] Red Secret yield by Market Share: list of (min_share, yield), highest first.
secret_yield_red_tiers: Tuple[Tuple[int, int], ...] = ((9, 3), (5, 2), (1, 1), (0, 0))
secret_yield_blue_base: int = 1          # [TUNE]
secret_yield_blue_block_bonus: int = 1   # [TUNE] if the owner blocked >= 1 Blue cube this round
secret_yield_blue_grid_l3_bonus: int = 1 # [TUNE] Defense Grid Level >= 3
secret_yield_blue_cap: int = 3           # [TUNE]
secret_yield_green_base: int = 3         # [TUNE] minus owner's Glitched Shield Slots, min 0
secret_yield_purple: int = 1             # [TUNE]
glitched_shield_slots_enabled: bool = False
slot_graduation_clear: int = 1           # [TUNE] slots cleared once per Phase 5 if >= 1 die graduates
company_starting_die_enabled: bool = False
company_starting_colors: Dict[str, str] = field(default_factory=dict)  # CompanyCode -> "RED"|"BLUE"|"GREEN"
triage_l1_breakthrough: str = "WHITE_CONTRACTORS"  # "WHITE_CONTRACTORS" (v0.37) | "GRAY_DIE"
```

Existing levers reused: `market_collapse_enabled` (set `False`), `market_share_start_by_player_count` (`{2:12,3:12,4:12}`), `starting_secrets_by_player_count`, `any_shield_policy` (must be `FREE_CHOICE` under v0.38, §7.4).

### 2.2 Validation (`__post_init__`)
- `secret_face_enabled` requires `die_face_profile == "V038_DRAFT"`, `red_mode == MARKET_SHARE`, six-phase round sequence and `glitched_shield_slots_enabled` (the Green yield reads slots). Raise `ValueError` otherwise.
- `die_face_profile == "V038_DRAFT"` requires `secret_face_enabled` (the draft table has no Glitch face; a V038 table without banking would make Face 5 a dead face).
- `secret_yield_red_tiers` strictly descending thresholds, last threshold `0`; all yields ≥ 0. Blue cap ≥ base.
- `company_starting_die_enabled` requires every `CompanyCode` mapped to RED/BLUE/GREEN and `starting_gray_dice ≥ 1`.
- `market_collapse_enabled=True` with a 12-point track is allowed (for ablation) but not in presets.
- Equality `GameConfig(num_players=n) == GameConfig.v037(num_players=n)` must still hold for n = 2, 3, 4.

### 2.3 Presets
```python
V038_COMPANY_STARTING_COLORS = {  # [TUNE] OQ-4
    "MERIDIAN": "RED", "PROMETHEUS": "RED",
    "DTO": "BLUE", "AEGIS": "BLUE",
    "OMNIDYNE": "GREEN", "HELIX": "GREEN",
}
@classmethod
def v038(cls, **overrides):  # on top of v037()
    secret_face_enabled=True, die_face_profile="V038_DRAFT", variant_profile="V038_DRAFT",
    power_profile="V038_DRAFT", glitched_shield_slots_enabled=True, company_starting_die_enabled=True,
    company_starting_colors=V038_COMPANY_STARTING_COLORS, triage_l1_breakthrough="GRAY_DIE",
    market_share_start_by_player_count={2:12,3:12,4:12}, market_collapse_enabled=False,
    any_shield_policy=FREE_CHOICE, starting_secrets_by_player_count={2:5,3:5,4:5}  # [TUNE] OQ-1
@classmethod
def v038_roster(cls, **overrides):  # v038() + the v037_roster() bot switches (push on, non_reference scope)
```
Each part stays individually switchable from `v037()` so the sweep can ablate (e.g. `v037(glitched_shield_slots_enabled=True, …)` where validation allows). Unchanged from v0.37: Market Leader Bonus schedule, `version_share_payout {"v2.0": 4}`, Public Relations Track costs/caps (re-check caps against max 12, OQ-9), tiebreak order.

---

## 3. State (`sim/engine/state.py`)

### 3.1 Processing Box
- The Processing Box **is** `PlayerState.glitched_dice` (keep the attribute; add read-only alias property `processing_box`). Renaming would break v0.37 fixtures, web and `_UnderDevelopmentProxy`. Telemetry keys under v0.38 use `processing_box_*`; v0.37 keys (`glitched_dice_count`) are still emitted unchanged.
- New per-die marker: `Die.secret_pending: bool = False`. Set when a die enters the Processing Box from a Secret face; cleared when it leaves. A die can enter the Processing Box without a Secret only via a legacy path still active under v0.38 (dirty-income backlash, §8.3; Y3 under V037 variants); it then yields nothing on exit. `Die` stays atomic-field-only (fast_clone shares `__dict__` copies, §10).
- Yield is computed **at banking time**, not at roll time (INV-SF-03).

### 3.2 New PlayerState fields
`glitched_shield_slots: int = 0`; `blocked_blue_this_round: int = 0` (reset at Phase 1 start; set in Phase 4); `slot_clear_used_this_phase5: bool`; telemetry counters (§11).

### 3.3 Effective shield capacity
`effective_defense_capacity = max(0, defense_capacity - glitched_shield_slots)`. `glitched_shield_slots` is capped at `defense_capacity` (excess glitches have no effect, mirroring v0.37 "excess Green has no effect"). If Defense Grid capacity rises, existing glitched slots stay glitched (count unchanged). OQ-6 asks whether a floor of 1 is wanted.

---

## 4. Dice (`sim/entities.py`)

### 4.1 Face model
Add `Face.secrets_pending: bool = False` (the Secret face) — **not** `secrets` (that field is Y3's immediate Phase 3 Secret). Add `Face.market_share: int = 0` and `Face.clean_slots: int = 0`. `is_shield` unchanged (Any only exists under V038). `has_*_option` helpers ignore Secret faces.

### 4.2 `die_face_profile = "V038_DRAFT"` `[TUNE]` (draft; OQ-3 confirms Faces 2–4)

| Die | F1 | F2 | F3 | F4 | F5 | F6 |
|---|---|---|---|---|---|---|
| Gray | unchanged (`Block 1 Any` ×2, `+$1 & +1 🔬`, `+$1 / +1 🔬` ×2, `+1 🔬`) | | | | | |
| White | unchanged (`Block 1 Any` ×3, `+$1`, `Glitch` ×2) | | | | | |
| Red | `+1 Market Share / +$1` | `+$2` | `+$2` | `+$2` | Secret face | `Red ★` |
| Blue | `+1 🔬` | `+1 🔬` | `+$1` | `+1 🔬 / +$1` | Secret face | `Blue ★` |
| Green | `Clean 1 Glitched Shield Slot / +$1` | `+1 🔬` | `+2 🔬` | `+1 🔬 / +$1` | Secret face | `Green ★` |
| Yellow | `+$3` | `+$2 / +1 🔬` | `+$2 / +1 🔬` | `+$1 & +1 🔬` | `+$2 / +1 🔬` | `Yellow ★` |
| Purple | `Block 1 Any` | `Block 1 Any` | `+$2` | `+$1 & +1 🔬` | Secret face | `Purple ★` |

Notes: Red F1 Market Share is Phase 3 income, not above max 12, and does not count toward the Public Relations limit (same as R2's gain). Green F1 clean resolves in Phase 1 Step 5 (§7.2). The v0.37 table is untouched under `"V037"`.

### 4.3 Company starting die
In `core.py` setup, when `company_starting_die_enabled`: create `starting_gray_dice - 1` Gray dice, then 1 colored die of `company_starting_colors[company.code]` using that colour's face-up Variant Card (Face 6) and place it in Ready for Release. It **does not** draw from the Central Market supply count (OQ-5). Die id assignment must be deterministic (after Grays, before Purple) so RNG draw order is fixed.

---

## 5. Variant Cards (`variant_profile = "V038_DRAFT"`) `[TUNE]`
Costs unchanged. Every colour-specific `Block` is removed.

| Code | v0.38 draft text |
|---|---|
| R1 | `[Income]` `+$2 & +1 Market Share` |
| R2 / R3 | unchanged |
| B1 | `[Income]` `+1 🔬`; Phase 4: `+$2` if ≥1 Blue cube exited and you took 0 Blue damage (die still In Production) |
| B2 | `[Phase 6]` pay `$4` → `+1 Corporate Secret` (no shield option) |
| B3 | `[Income]` move 1 die Processing Box → Scanned Box in Phase 3 (banks its Secret, §7.5) |
| G1 | `[Income]` Clean 1 Glitched Shield Slot + `+1 🔬` (OQ-7: was "Block 2 Green") |
| G2 | `[Income]` Clean 1 Glitched Shield Slot + `+1 🔬` (OQ-7: G1 / G2 now identical — differentiate) |
| G3 | unchanged |
| Y1 / Y2 | unchanged |
| Y3 | `+1 Corporate Secret` in Phase 3, then move this die to the **Scanned Box** |

---

## 6. Powers (`power_profile = "V038_DRAFT"`)
- **Magnetic Splice (Omnidyne, Phase 5 Step 1):** move 1 die Processing Box → Ready for Release; banks its Secret (yield evaluated at that moment, §7.5).
- **Jumper Diagnostics (Phreaker, Phase 3):** move 1 die out of the Processing Box to the Scanned Box, banking its Secret; if the Processing Box is empty, `+$1` (OQ-8 destination).
- **Brute-Force Bypass (Helix, Phase 1 Step 4):** +1 free reroll this phase, and set 1 rolled die to any legal non-Star face of its colour. Setting it to the Secret face is allowed (OQ-10).
- **Arbitrary Code Execution (Prodigy):** as v0.37, but the target face may not be the Secret face under `V038_DRAFT` (lever `ace_allows_secret_face: bool = False`; OQ-10).
- Burn Notice, Contingent Staffing, Resonance Sensor, Algorithmic Parity, Redundant Crew, Baffle Echo, Slush Fund, Algorithmic Arbitrage: unchanged.

---

## 7. Phase-by-phase engine changes (v0.38 path only)

### 7.1 Phase 1
- Secret face is a normal face during rerolls (can be kept or rerolled; it is not locked). There is no colored-die Glitch.
- Step 5 assignment order: (a) White `Glitch` → discard (unchanged); (b) **Secret face** → Processing Box, `secret_pending=True`, `secret_faces_rolled[colour] += 1`; (c) slot cleaning (§7.2); (d) Any shields up to `effective_defense_capacity`; (e) Income.
- Hash Matches: Secret faces never form a Hash Match (treated like Glitch in `_hash_key`; OQ-11).
- Reset `blocked_blue_this_round = 0`.

### 7.2 Cleaning a Glitched Shield Slot
- Any rolled die (including White Contractors? — OQ-2) may be **placed on a glitched slot**: the slot is cleared, the die produces no output and moves to the **Scanned Box** at once (a White Contractor is discarded instead). Bot hook `choose_slot_cleaners`.
- Green F1 / G1 / G2 "Clean 1 Glitched Shield Slot" clear a slot on assignment in Phase 1 Step 5 (step c, before shields fill the effective capacity), without the die leaving In Production, so the freed slot can take a shield this round. G1 / G2 still pay their `+1 🔬` in Phase 3. (User approved 2026-11-08; see §14.2.)

### 7.3 Phase 2
Corruption spaces with `demote_dice = X` glitch X shield slots for each affected player under `glitched_shield_slots_enabled` (the "All …" spaces hit every survivor, the others the same targets as v0.37). Dice are not moved. "Return 1 Colored Die" unchanged; a returned die in the Processing Box loses its pending Secret (stranded-equivalent; counted as `secrets_lost_returned`). Singularity / Patient Zero checks unchanged.

### 7.4 Phase 4
- Stage 1 has no shields; every shield is Any, allocated by `choose_any_shield_allocation` under `FREE_CHOICE` (all available Any shields must block while unblocked cubes remain, unchanged).
- Record `blocked_blue_this_round` = Blue cubes blocked (Baffle Echo-ignored cubes are not blocked).
- Unblocked Red: −1 Market Share each (floor 0). Unblocked Blue: −1 Secret each (Slush Fund unchanged). **Unblocked Green: +1 `glitched_shield_slots` each** (cap §3.3); no die moves; Defensive Shield Sacrifice / Contractor Sacrifice options do not exist on this path.
- Market Collapse check skipped when `market_collapse_enabled=False`. Total Wipeout / Patient Zero checks unchanged.

### 7.5 Phase 5 (order is normative)
1. Magnetic Splice (banks).
2. Production Return.
3. Scanned Graduation.
3b. **Graduation slot clear:** if ≥1 die graduated in step 3 and `glitched_shield_slots > 0`, clear `slot_graduation_clear` slot(s). Once per Phase 5.
4. **Conveyor Triage:** up to `triage_bandwidth` dice of the player's choice (`choose_triage_order`; default highest current yield first, then lowest die_id) Processing Box → Scanned Box. For each with `secret_pending`, gain `secret_yield(player, die.color)` Corporate Secrets (`gain_secrets(n, "secret_face_<colour>")`). Triage L4 research unchanged.

`secret_yield(p, colour)` (pure, `sim/engine/secret_faces.py`, new module):
- RED: first tier with `p.market_share >= min_share` → yield.
- BLUE: `min(cap, base + block_bonus*(p.blocked_blue_this_round>0) + grid_bonus*(defense_level>=3))`.
- GREEN: `max(0, green_base - p.glitched_shield_slots)` (after step 3b).
- PURPLE: `secret_yield_purple`. Others: 0.
Because 3b precedes 4, a graduation clear raises this Phase 5's Green yield. Banking via B3 / Jumper Diagnostics (Phase 3) uses the Phase-3 state (Blue's block bonus is then 0 this round, since Phase 4 has not happened — OQ-12).

### 7.6 Phase 6
B2 pay-only; Red F1 / R1 Market Share already applied. Dirty-income backlash (if enabled) moves a die to the Processing Box with `secret_pending=False` (OQ-13). Purchases unchanged in rules; bot policy changes §9.

### 7.7 End game (`end_game.py`)
Before the Market Leader Bonus and ranking, for each player count `stranded_secrets` = sum of yields the pending dice **would** have had (telemetry only) and `stranded_dice` = count; they score nothing. This covers Singularity (Phase 2, dice rolled this round are stranded), Total Wipeout (after Phase 4) and the round limit. A Final Round from Patient Zero still runs Phase 5, so survivors bank normally. Tiebreaker "fewest dice Under Development" counts Processing Box + Scanned Box (unchanged formula).

---

## 8. Research Tracks (`research_tracks.py`)
1. `("TRIAGE", 1)` under `GRAY_DIE`: gain 1 Gray Legacy die into Ready for Release (same helper as Defense / Release L1). Text "Gain 1 Gray Legacy die".
2. Defense Grid Level 3: no new action; the Blue yield reads `defense_level >= 3` (the Level 3 Breakthrough "Gain 1 Corporate Secret" is unchanged).
3. Gray-die enumeration helpers that walk `glitched_dice` keep working (Processing Box).
4. Public Relations Track regain caps may exceed a 12 track; clamp at max (already the case via `change_market_share`).

---

## 9. Bot policy contracts `[TUNE-BOT]`
All new decisions go through `BaseBot` hooks with defaults so every archetype works; specialised logic in `AdaptiveBalanced`, `MixedPolicy`, `ReferenceSearch` (via simulation, needs nothing extra beyond legal-move enumeration) and the archetype bots where noted.

| Hook | Contract |
|---|---|
| `choose_yahtzee_rerolls` | Value of keeping a Secret face = `expected_bank_value(colour)` = current `secret_yield` × P(banked before game end) (triage queue position vs `triage_bandwidth`, rounds left estimate). Keep if ≥ value of the die's best alternative face + its expected reroll value. Never chase on a die needed for a shield when Blue lethal risk is high (reuse the Blue-safe logic, `push_blue_slack`). |
| `choose_slot_cleaners` (new) | Clean when the slot is worth more than the die's output: next-round shield need, or Green yield (each slot = −1 per Green pending/expected Secret). |
| `choose_any_shield_allocation` | Colour-aware split: Blue cube = 1 Secret (+ Blue block bonus if ≥1 Blue Secret pending/expected this Phase 5 and none blocked yet); Red cube = Market Share loss valued by tier crossings for owned/pending Red dice, PR regain cost and Market Leader Bonus (existing `marginal_block_value`); Green cube = slot value (shield capacity loss + Green yield). Blue-lethal protection first. |
| `choose_triage_order` (new) | Highest current yield first; tie lowest die_id. |
| Purchases | Score colours by expected Secret yield per remaining round given Market Share, owned Defense Grid level, slots, and Company starting colour; Yellow scored as Money. Mixed policy samples from the same scored menu (pure, no per-game state on `self`, H5). |
| `choose_breakthrough` | Triage L1 now a Gray die; Defense Grid push value includes the L3 Blue bonus for Blue owners. |
| Helix / Prodigy face hooks | May target the Secret face (Helix only, if allowed) when its bank value beats alternatives. |

Archetype flavour: SecOpsTurtle → Blue/Purple; VentureGreed → Yellow/Red; Accelerationist → Green; RecklessSaboteur → chases any Secret face; AdaptiveBalanced → follows Company colour first. Bots must not read hidden information (tower internals) beyond what v0.37 bots read.

---

## 10. Parity & fast_clone
- **INV-SF-PARITY-01:** `GameConfig()`, `GameConfig.v037()` and `v037_roster()` produce bit-identical games to HEAD `0b80154`. Capture `tests/fixtures/v037_parity/` (seeds × 2/3/4P × roster) **from HEAD before any code edit**, compare full end-game records and per-round telemetry; existing v033–v036 and `v037_push` fixtures must also pass.
- No new RNG draws on the v0.37 path; on v0.38 every new choice is deterministic or via bot hooks (no extra RNG beyond die rolls and the tower).
- **fast_clone mirror obligation:** any edit to `GameEngine._run_round_six_phase` (e.g. new Phase 5 sub-step, Phase 1 reset, end-game stranded pass) must be mirrored in `fast_clone.resume_round`; RB-07 drift guard must be extended. New PlayerState fields must be plain ints/bools/lists so `_cp` copies them; `Die.secret_pending` is atomic so the `Die` fast path stays valid. Add a clone-equivalence test on a v038 game (clone at Phase 1/4/6, resume, compare to live).

---

## 11. Telemetry
Per player (end-game record and `PlayerState`):
- `secrets_by_source`: `secret_face_red|blue|green|purple`, `y3`, `b2`, `y1`, `burn_notice`, `breakthrough`, `market_leader_bonus`, starting — plus losses `blue_damage`, `corruption`.
- `secret_faces_rolled[colour]`, `secret_faces_banked[colour]`, `secret_yield_hist[colour][yield]`, `stranded_dice`, `stranded_secrets`, `secrets_lost_returned`.
- `slots_glitched_by_source` (`green_cube`, `corruption`), `slots_cleaned_by_die`, `slots_cleaned_by_face` (F1/G1/G2), `slots_cleared_by_graduation`, `max_glitched_slots`, rounds with 0 effective capacity.
- `company_color`, `colored_dice_owned_by_colour` per round, `path` classification at game end (Red/Blue/Green/Yellow/Mixed by owned-colour majority ≥ 60%, else Mixed) — exact rule in the sweep script, logged alongside.
Per game: end reason (Singularity / Patient Zero / Total Wipeout / round limit), rounds, Market Share min per player.
Sweep script: win rate by Company colour and by path, Secrets by source, stranded share, slot dynamics, guardrails (2P Singularity ≤ 48% per §39, Total Wipeout, rounds, archetype spread, ref1 non_reference edge).

---

## 12. Invariants
- INV-SF-01 Secret banked only when a `secret_pending` die leaves the Processing Box; at most once per die visit.
- INV-SF-02 Dice in the Processing Box at game end score 0.
- INV-SF-03 Yield computed at banking time from current state.
- INV-SF-04 No colored shield faces exist under V038; Stage 1 blocks 0.
- INV-SF-05 `0 ≤ glitched_shield_slots ≤ defense_capacity`; at most one graduation clear per Phase 5.
- INV-SF-06 Market Share in [0, 12]; no Market Collapse end trigger when disabled.
- INV-SF-07 Starting pool size unchanged (4 permanent dice) with the Company starting die.

---

## 13. Edge-case test list (`tests/test_v380_secret_faces.py`)
1. Parity: `GameConfig()` / `v037()` / `v037_roster()` match `v037_parity` fixtures (2/3/4P).
2. Secret face rolled → Processing Box, no Phase 3 output, `secret_pending` set.
3. Secret face can be rerolled away during free rerolls (not locked).
4. Banking at triage: bandwidth 2, three pending dice → two bank, third stays pending; banks next round.
5. Triage order hook respected; default highest-yield first.
6. Red tiers at Market Share 12, 9, 8, 5, 4, 1, 0 → 3,3,2,2,1,1,0.
7. Red yield read after Phase 4 Red damage of the same round (damage that crosses a tier lowers the bank).
8. Blue: 1 base; +1 with ≥1 Blue blocked this round; +1 at Defense Grid L3; cap 3; Baffle Echo-ignored Blue cube does not count as blocked.
9. Blue die pending from an earlier round uses the banking round's block flag.
10. Green: 3 − slots; 0 at ≥3 slots; graduation clear in step 3b applies before triage.
11. Purple Secret face yields 1.
12. Stranded on Singularity: die rolled Secret in Phase 1, Singularity in Phase 2 → 0 Secrets, `stranded_secrets` = would-be yield.
13. Stranded on Total Wipeout and on the round limit; Patient Zero Final Round survivors still bank in Phase 5.
14. Unblocked Green glitches a slot, never a die; capped at `defense_capacity`; excess has no effect.
15. Corruption "Glitch 2 dice" → 2 slots; "All glitch 1 die" → every survivor.
16. Effective capacity: shields beyond `defense_capacity − slots` go to Income.
17. Placing a die on a glitched slot clears it and the die goes to Scanned Box (White Contractor discarded).
18. Green F1 clean in Phase 1 frees the slot for a shield this round.
19. Graduation clear: 0 graduates → no clear; 3 graduates → 1 clear only.
20. White Contractor Glitch discards the die; no colored die has a Glitch face under V038.
21. Company starting die: correct colour per Company, uses face-up Variant Card, 2 Gray remain, Market supply unchanged, deterministic die ids.
22. Triage L1 under `GRAY_DIE` gives 1 Gray die into Ready for Release, no White dice.
23. Arbitrary Code Execution cannot set the Secret face (lever off); can with lever on.
24. Brute-Force Bypass: +1 free reroll and face-set; allowed to set Secret face.
25. Magnetic Splice from the Processing Box banks (yield at Phase 5 step 1, before 3b).
26. Jumper Diagnostics moves a pending die to Scanned and banks in Phase 3 (Blue block bonus 0); empty Processing Box → +$1.
27. B3 banks; Y3 goes to Scanned Box (not Processing).
28. "Return 1 Colored Die" on a pending die → Secret lost, counted.
29. Hash Matches never form from Secret faces.
30. Market Collapse disabled: a survivor at 0 Market Share does not trigger the Final Round; Red yield 0.
31. Red F1 / R1 Market Share gain clamps at 12 and does not consume the PR limit.
32. Yellow V038 faces: no shields, no Secret face; choice faces resolve.
33. Market Leader Bonus still applied after stranded pass; Total Wipeout ranking unchanged.
34. Validation errors for each illegal lever combination in §2.2.
35. fast_clone: clone at Phase 1/4/6 of a v038 game, `resume_round`, equals live round; RB-07 extended.
36. Determinism: same seed → same v038 game; no extra RNG draws vs a run with all bots' new hooks at default.
37. A die in the Processing Box without a pending Secret (`secret_pending=False`) yields 0 when it leaves (triage moves it to the Scanned Box). Dirty income is rejected by validation under v0.38 (§14.1 OQ-13).

---

## 14. Open Questions for the User

1. **Starting Secrets:** default `v038()` to 5 at all player counts (3P probe 4 and 5)? Or 4 at 3P with 2P / 4P left for the sweep to fit?
2. **Cleaning a Glitched Shield Slot by placement:** may *any* rolled die (including a White Contractor, which would then be discarded) be placed on a glitched slot to clean it, or only dice showing a clean face (Green F1 / G1 / G2)? And does the cleaning die give up its face output?
3. **Draft faces 2–4:** confirm the face tables in §4.2 — especially Blue (no shields: `+1 🔬`, `+1 🔬`, `+$1`, `+1 🔬 / +$1`), Green F2–F4 (kept research faces although "Blue takes the research faces"), and Yellow (Face 5 `+$2 / +1 🔬`).
4. **Company → colour mapping:** accept Red = Meridian, Prometheus; Blue = DTO, Aegis; Green = Omnidyne, Helix?
5. **Company starting die supply:** does it come out of the Central Market's supply of that colour (reducing purchasable dice), and does it start in Ready for Release?
6. **Glitched Shield Slot floor:** may slots glitch a player down to 0 usable shield slots, or is the last slot protected (§42 takeaway 2 observed it never happens with the graduation clear, but it is not a rule)? What happens to glitched slots when Defense Grid capacity increases?
7. **G1 / G2:** both become "Clean 1 Glitched Shield Slot + `+1 🔬`" — should they differ (e.g. G1 cleans 2), and does a Phase 3 clean help this round (shields were placed in Phase 1) or only next round?
8. **Jumper Diagnostics destination:** Processing Box → Scanned Box (proposed) or → Ready for Release? Does it still allow rolling a Scanned Box die when the Processing Box is empty?
9. **Public Relations Track regain caps** were tuned for an 18 track: keep them or scale for the 12 track?
10. **Arbitrary Code Execution / Brute-Force Bypass vs Secret face:** exclude the Secret face from Arbitrary Code Execution (proposed default) and allow it for Brute-Force Bypass?
11. **Hash Matches:** do three Secret faces form a Hash Match? Proposed: no.
12. **Banking outside Phase 5** (B3, Jumper Diagnostics in Phase 3; Magnetic Splice before the graduation clear): use the state at that moment (Blue block bonus then 0; Green yield before the clear) as proposed?
13. **Dirty-income backlash** (if enabled under v0.38): send the die to the Processing Box without a Secret (proposed), or to the Scanned Box?
14. **Yield timing for "that round"** (Blue): confirm it is the round in which the die is banked, not the round it was rolled.

## 14.1 Open Question Resolutions (User, 2026-11-07)

1. **Starting Secrets:** `v038()` = 5 at 2P / 3P / 4P for now; balance later.
2. **Cleaning a Glitched Shield Slot:** any die showing a face with a shield icon (`Block 1 Any` on Gray / White / Purple) may be placed on a glitched slot to clean it. Special faces (`★`, Secret face, choice faces without a shield) cannot.
3. **Draft faces 2–4:** spec §4.2 proposal adopted for now.
4. **Company → colour:** Red = Meridian, Prometheus; Blue = DTO, Aegis; Green = Omnidyne, Helix.
5. **Company starting die:** taken from that colour's Central Market supply; starts in Ready for Release.
6. **Slot floor:** slots may glitch a player down to 0 usable shield slots (one round with no defence, then the graduation clear frees one). No last-slot protection; balance later. *(Defense Grid capacity increase: pending, see §14.2.)*
7. **G1 / G2:** identical for now. A Phase 3 clean helps this round, because shields resolve in Phase 4.
8. **Jumper Diagnostics:** pending, see §14.2.
9. **Public Relations Track caps:** scale for the 12-point track (method pending, see §14.2).
10. **Arbitrary Code Execution / Brute-Force Bypass:** proposal adopted (ACE excludes the Secret face; Brute-Force Bypass allows it).
11. **Hash Match:** removed from the game. It is already absent from RULES.md; the dead sim code (`detect_hash_matches*`, `hash_matches_secrets`, `scripts/sweep_v170_hash_matches.py`) may be deleted, and nothing under v0.38 forms Hash Matches.
12. **Banking outside Phase 5:** proposal adopted (state at that moment).
13. **Dirty income:** no longer in the game; `v038()` must keep it disabled, and validation rejects enabling it with v0.38 levers.
14. **Blue "that round":** the round the die is banked.

## 14.2 Follow-up Resolutions (User, 2026-11-07)

- **OQ-6 (capacity increase):** glitched slots stay glitched; a new Defense Grid slot arrives clean.
- **OQ-8 (Jumper Diagnostics, `V038_DRAFT`):** move 1 die from the Processing Box to the Scanned Box, banking its Secret (Phase-3 state, per OQ-12). If the Processing Box is empty, roll 1 Scanned Box die for its output (v0.37 behaviour; the die stays in place; shields produce 0). If Under Development is empty, `+$1`.
- **OQ-9 (Public Relations Track):** limits stay `1 / 2 / 3` (Levels 0–1 / 2–3 / 4); under v0.38 each `+1` Market Share costs `3 🔬` (lever, e.g. `pr_regain_cost`; v0.37 stays `2 🔬`).
- **OQ-7 amendment (User, 2026-11-08):** G1 / G2 (like Green F1) clean their Glitched Shield Slot immediately on assignment in Phase 1 Step 5, freeing that slot for a shield die in the same step. Their `+1 🔬` is still paid in Phase 3. Supersedes "a Phase 3 clean helps this round".

## 14.3 Candidate 2 Amendments (User, 2026-11-08; FINDINGS §43)

- **Market Collapse returns** under v0.38 (`market_collapse_enabled=True` allowed and default in the candidate preset; v0.36 rules: a survivor at 0 Market Share after Phase 4 triggers the Final Round, no elimination).
- **Starting Secrets** 2P 3 / 3P 4 / 4P 4.
- **Red yield tiers** `((11, 3), (7, 2), (3, 1), (0, 0))`.
- **Lever A push/dump line off** for all archetypes in rule sweeps (a `v038` candidate with no `v037_roster` bot switches).
- **Yellow face profile `V038_YELLOW_MS`:** F1 `+2 Market Share`, F2 `+1 Market Share / +1 🔬`, F3 `+$3`, F4 `+$2 / +1 🔬`, F5 `+$2 / +1 🔬`, F6 `Yellow ★`. Yellow Market Share faces resolve in Phase 3 like Red F1 (not above max 12, not counted toward the Public Relations limit). Alternate F1 `+$1 & +1 Market Share` as a profile option for the probe.
- **New lever `glitched_slots_per_round_cap`** (default `None` = uncapped): the maximum number of Glitched Shield Slots a player can receive per round from all sources.
- Green base yield stays 3 in the preset; 2 is probed.

## 14.4 Candidate 2 Tune (User, 2026-11-08; FINDINGS §43.1)

`v038b()` adds starting Market Share 14 at all player counts (also the maximum) and Market Leader Bonus 2P `+4` / 3–4P `+4, +2`. Green base 3, slot cap off, Yellow `V038_YELLOW_MS`. Bot purchase scoring values Yellow by its Market Share faces (Market Collapse avoidance, Market Leader Bonus, Red tier support), not as Money.

## 14.5 RSP-1 (User, 2026-11-09; FINDINGS §43.4)

Scope: the User-adopted RSP-1 package as a new candidate preset on top of `v038b()`. Reference for intended behaviour: `docs/findings/rsp1_model.py` (monkeypatch model; not code to copy). Sim prose calls the new scoring event **"the Red Secret payout"** — *provisional sim label only, not a glossary term, pending User* (§14.5.9 Q1). Rules wording in Phase B must use existing RULES.md §7 terms only.

### 14.5.1 New GameConfig levers (all off by default → `GameConfig()`, `v037()`, `v038()`, `v038b()` unchanged)

| Lever | Type | Default | Meaning |
|---|---|---|---|
| `red_secret_owner_yield` | `Optional[int]` | `None` | `None` = Red yield from `secret_yield_red_tiers` (v038b). An int = flat Red Secret yield to the owner, ignoring tiers. Validation: `≥ 0`; requires `secret_face_enabled`. |
| `red_secret_payout_by_player_count` | `Optional[Dict[int, Tuple[int, ...]]]` | `None` (→ `{}`) | Corporate Secrets by Market Share place, fired at most once per round at the end of Phase 5 if ≥ 1 Red Secret was banked that round (§14.5.3; per-round is the only mode — User variant B, 2026-11-09). Empty = off. Validation: same shape rules as `market_leader_bonus_by_player_count` (non-negative, non-increasing, length ≤ n; shorter tuples pad with 0); requires `secret_face_enabled` and `is_market_share`. |
| `red_secret_payout_at_end` | `bool` | `False` | One more Red Secret payout at game end (§14.5.3). Requires a non-empty payout schedule. |
| `triage_order_rule` | `str` | `"BOT"` | `"BOT"` = `choose_triage_order` hook (v038b). `"OLDEST_FIRST"` = Conveyor Triage takes Processing Box dice in entry order; the bot hook is not called. Validation: one of the two; `OLDEST_FIRST` requires `secret_face_enabled`. |
| `die_face_profile = "V038_YELLOW_MS_F3"` | new profile value | — | `V038_YELLOW_MS` with Yellow F3 `+$3` → `+$1 & +1 Market Share` (resolves in Phase 3 like Yellow F1: clamps at max, not counted toward the Public Relations limit). F1 stays `+2 Market Share`. Add to `V038_DIE_FACE_PROFILES`. |

Reused levers: `market_leader_bonus_by_player_count={}` and `version_share_payout={}` (both removed under RSP-1), `market_share_start_by_player_count`, `starting_secrets_by_player_count`.

Validation additions: `red_secret_payout_by_player_count` non-empty **and** a non-empty `market_leader_bonus_by_player_count` is allowed (ablation) but not in presets; same for `version_share_payout`. Market Share max follows the start value as in v038b (start = max), i.e. 16 / 16 / 17 (§14.5.9 Q3).

### 14.5.2 Preset `v038c()`
Name: `v038c` — follows the candidate letter sequence (`v038b` = C2); RSP-1 is candidate 3. Docstring cites §14.5 / FINDINGS §43.4.
(User, 2026-11-09: owner yield 2; 2P starting Market Share 13 — FINDINGS §43.5.) The code block below shows the original §43.4 values; the locked preset is `red_secret_owner_yield=2`, `V038C_MARKET_SHARE_START = {2: 13, 3: 16, 4: 17}`.
```python
V038C_MARKET_SHARE_START = {2: 16, 3: 16, 4: 17}     # [TUNE] §43.4 (start = max)
V038C_RED_SECRET_PAYOUT  = {2: (3, 1), 3: (3, 1, 0), 4: (3, 1, 0, 0)}  # [TUNE]
@classmethod
def v038c(cls, **overrides):  # on top of v038b()
    red_secret_owner_yield=1, red_secret_payout_by_player_count=dict(V038C_RED_SECRET_PAYOUT),
    red_secret_payout_at_end=True, market_leader_bonus_by_player_count={}, version_share_payout={},
    market_share_start_by_player_count=dict(V038C_MARKET_SHARE_START),
    die_face_profile="V038_YELLOW_MS_F3", triage_order_rule="OLDEST_FIRST",
    starting_secrets_by_player_count=dict(V038B_STARTING_SECRETS)  # 3/4/4; 2/3/4 via override
```
`setdefault` pattern as `v038b()`; `bot_pr_push=False` inherited. The sweep probes starting Secrets `{2:2,3:3,4:4}` via `--set starting_secrets_by_player_count` (the §43 `--set` dict bug must be confirmed fixed for this lever; add a test that the override reaches `GameConfig`).

### 14.5.3 Red Secret payout: timing and ordering (normative; User variant B, 2026-11-09)
1. **Owner yield at bank time.** `secret_faces.bank()` credits `red_secret_owner_yield` (+1) for each Red die with `secret_pending=True` at every banking point (Phase 3 B3 / Jumper Diagnostics, Phase 5 Magnetic Splice, Conveyor Triage). `bank()` does **not** fire the payout; it sets `state.red_secret_banked_this_round = True` and increments `state.red_secrets_banked_this_round` (needs the `GameState`: new optional `state` arg, all call sites pass it). Both are reset at round start (Phase 1 entry). Dice lost via `lose_pending` and stranded dice set nothing (INV-SF-02).
2. **Per-round payout.** A new Phase 5 end hook (after the last banking point and the rest of Phase 5) fires **at most one** payout per round iff the flag is set. Recipients: players with `is_patient_zero == False` at that moment. Market Share read at that moment (post-Phase 4 and any Phase 5 effects). Place by `market_share_places` (ties share the better place, as the Market Leader Bonus). Schedule indexed by *starting* player count; places beyond the tuple score 0; a sole survivor takes 1st; players at 0 Market Share still score by place. Credit `gain_secrets(k, "red_secret_payout")`; no Money. Several Red Secrets in one round (any players, Phase 3 and/or 5) still give one payout.
3. **Patient Zero.** Set in Phase 2 or Phase 4, so before the hook: a player eliminated this round does not score, even if they banked a Red Secret in Phase 3 (their owner +1 stays, for telemetry; they are out of ranking anyway).
4. **Final Round.** The hook runs normally in the Final Round (any trigger), including a Market Collapse Final Round.
5. **Singularity.** Ends the game in Phase 2: no Phase 3/5 banking, no in-round payout; the end payout fires.
6. **Game ends in Phase 4 after a Phase 3 Red bank.** No in-round payout (Phase 5 not reached). Only reachable when everyone is eliminated (Total Wipeout), so no end payout either.
7. **End payout** (`red_secret_payout_at_end`): in `evaluate_end_game`, after `_return_held_contractors` and the stranded pass, before ranking; same award rules with final Market Share; source `red_secret_payout_end`. **Skipped when** `end_reason == MARKET_COLLAPSE` or Total Wipeout. Fires on Singularity, Patient Zero (with survivors) and the round limit. Independent of the per-round payout of the last round (both may fire).
8. **Total Wipeout.** No end payout; ranking unchanged.
9. The Market Leader Bonus and `resolve_version_comparison` become no-ops via their empty schedules; no code removed.
10. **fast_clone mirror:** the Phase 5 end hook and the Phase 1 flag reset are edits to `_run_round_six_phase` and must be mirrored in `fast_clone.resume_round` (RB-07).

**Model note (A/B, game-designer 2026-11-09):** rounds with ≥ 2 Red banks are only 0.9 / 1.9 / 4.0% (2P / 3P / 4P); payouts per game under B 1.89 / 2.36 / 3.09; balance unchanged vs per-Secret firing (A).

### 14.5.4 Conveyor Triage oldest first
`triage_order_rule="OLDEST_FIRST"`: order = Processing Box entry order. `glitched_dice` is append-on-entry, so list order is the key; ties (same step) keep append order (die roll order, then die_id). Add an explicit `processing_entry_seq` int on `Die` (set in `enter_processing_box` from a per-player counter) so order survives any list rebuild; plain int for `fast_clone`. Applies to all colours. Magnetic Splice / Jumper Diagnostics target choice is unchanged (still bot choice) — §14.5.9 Q4.

### 14.5.5 Telemetry
- Per player: `secrets_by_source` adds `red_secret_payout`, `red_secret_payout_end`; `market_leader_bonus` stays 0. `red_secrets_banked` (Red Secrets this player banked), `red_payout_places` histogram `{place: count}`, `red_payout_secrets` total.
- Per game (`GameState` / end record): `red_secret_payouts` list of `{round, red_banks_this_round, banker_pids, shares, places, gains}` (one per round fired); `red_secret_payouts_fired` int (payouts fired per game); `rounds_with_multi_red_banks` int (rounds with ≥ 2 Red banks); `red_banks_by_round` list; `red_secret_payout_end_fired` bool; `red_pending_at_end` / `other_pending_at_end` (stall diagnostic, as the model).
- Sweep script (`run_v380_secret_faces_sweep.py`): payouts/game, share of rounds with ≥ 2 Red banks, share of Secrets from payouts vs own faces, payout-winner = game-winner rate, Red stall diagnostic (mean rounds a Red die sits in the Processing Box), plus existing guardrails.

### 14.5.6 Bot valuation contract `[TUNE-BOT]`
Pure functions in `market_share_policy.py` / `secret_face_policy.py`; no RNG; gated on `cfg.red_secret_payout_by_player_count` non-empty (v038b paths byte-identical otherwise).
- `expected_red_payouts_remaining(state) -> float`: `E_in` (expected remaining rounds with ≥ 1 Red bank: Σ over remaining rounds of `1 − Π_seats (1 − p_red_bank)`, with `p_red_bank` from Red dice owned × 1/6 × bank probability, remaining rounds from the existing Version-track pacing helper) + `P_end` (1 − estimated Market Collapse probability; use 1.0 unless a survivor is at ≤ 2 Market Share, then 0.5).
- `expected_payout_value(share, rival_shares, schedule)`: generalises `expected_market_leader_bonus` to any schedule (same tie handling).
- **Market Share marginal value** (Red block in `marginal_block_value`, `urgent_regain` / Public Relations Track, `share_value` for Yellow / Red F1 faces): `Δ expected_payout_value × (E_in + P_end)` replaces the Market Leader Bonus term. Rival-denial term: blocking Red does not lower rivals, so no denial term.
- **Red Secret face value** (rerolls, purchases): `(red_secret_owner_yield + q × expected_payout_value(own share, rivals)) × bank_probability`, where `q` = probability no other Red bank happens this round (the marginal payout this die enables; ≈ 1 at 2P/3P).
- Triage hook not consulted under `OLDEST_FIRST` (no stalling choice). Rerolling a Red Secret face away is still allowed; bots value it per the line above.
- Purchase scoring of Yellow uses the same Market Share marginal value.

### 14.5.7 ref1 rollout support
- Payout logic lives in `bank()` / `evaluate_end_game`, so `fast_clone` rollouts get it with no search-code change. New `GameState` / `PlayerState` / `Die` fields are plain ints/bools/lists/dicts copied by `_cp`; `red_secret_payouts` list copied shallow-per-record. RB-07 drift guard extended to the new `bank(state=…)` signature.
- `rollout_value` unchanged (uses final Secrets, which include payouts).
- Required runs: ref1 3P and 2P under `v038c()` (1,200 games), reporting non_reference win rate, Red-banking volume of the ref seat, and the stall diagnostic for the ref seat vs others (FINDINGS §43.4 flagged stalling as analytically real; oldest-first should remove it — ref1 is the check).
- Tests RB-xx: clone at Phase 1/4/6 of a v038c game with a pending Red die → `resume_round` equals live, including payout logs.

### 14.5.8 Invariants and tests
- **INV-RSP-01** A round fires exactly one payout iff ≥ 1 Red Secret was banked in its Phase 3 or Phase 5 and Phase 5 completed; else none. `bank()` never awards payout Secrets. Lost / stranded Red dice set no flag.
- **INV-RSP-01b** The per-round flag is reset at round start; payouts per game ≤ rounds played + 1.
- **INV-RSP-02** Payout recipients = non-Patient-Zero players at the end of Phase 5; awards equal `schedule[place-1]` with shared-better-place ties.
- **INV-RSP-03** Owner gains exactly `red_secret_owner_yield` from the face itself, independent of Market Share.
- **INV-RSP-04** End payout fires iff enabled, `end_reason != MARKET_COLLAPSE` and not Total Wipeout; at most once.
- **INV-RSP-05** Under `v038c`: Market Leader Bonus = 0 and no version comparison record for any player.
- **INV-RSP-06** `OLDEST_FIRST` triage banks in `processing_entry_seq` order; bandwidth unchanged.
- **INV-RSP-07** No new RNG draws; levers off ⇒ byte-identical to HEAD.
- **INV-RSP-08** Market Share stays in `[0, max]` (16/16/17) under Yellow F1/F2/F3 and Red F1.

Test matrix (`tests/test_v380_secret_faces.py`, new class `TestRSP1`):
1. Parity: `v037_parity` fixtures; plus new `v038b_parity` fixtures captured **from HEAD before code edits** (2/3/4P × mixed1 seeds) must match bit-identically.
2. Owner yield 1 at Market Share 16, 5, 0.
3. Single Red bank, 3P shares (10, 7, 7) at end of Phase 5 → awards 3 / 1 / 1, regardless of banker; owner +1 credited at bank time.
4. Ties at top (9, 9, 4) → 3 / 3 / 0; 4P (8, 6, 6, 2) → 3 / 1 / 1 / 0.
5. Two Red banks in one round (same player; different players; one in Phase 3 + one in Phase 5) → exactly one payout; owners +1 each.
5b. Phase 3 Red bank then Phase 4 Red damage changes places → payout uses post-Phase 4 Market Share.
5c. No Red bank in a round → no payout; flag reset next round.
6. Phase 3 Red banker becomes Patient Zero in Phase 4 → payout still fires for the survivors, banker excluded.
7. Phase 3 B3 / Jumper Diagnostics Red bank sets the flag; payout at end of Phase 5. Game ending in Phase 4 (Total Wipeout) → no payout.
8. Sole survivor gets +3.
9. End payout on Singularity, Patient Zero, round limit; none on Market Collapse; none on Total Wipeout; Market Collapse Final Round Phase 5 payouts still fire.
10. Stranded Red at end and `lose_pending` → no payout.
11. Oldest-first: dice entering rounds 3, 4, 4 with bandwidth 2 → round-3 die and first round-4 die bank; hook not called.
12. Yellow F3 face `+$1 & +1 Market Share`, clamps at max, not counted to the Public Relations limit.
13. Validation errors: negative owner yield; bad schedule shape; `red_secret_payout_at_end` with empty schedule; unknown `triage_order_rule`; RSP levers without `secret_face_enabled`.
14. `--set starting_secrets_by_player_count={2:2,3:3,4:4}` reaches the config.
15. fast_clone equivalence on v038c (Phase 1/4/6, incl. a clone taken with the flag set), determinism (same seed → same game).
16. Bot valuation: `expected_payout_value` equals `expected_market_leader_bonus` for the same schedule; levers off ⇒ bot outputs identical to HEAD.

Parity fixtures that must still match: `tests/fixtures/v037_parity/` (`GameConfig()`, `v037()`, `v037_roster()`), the existing v033–v036 and `v037_push` fixtures, and the new `v038b_parity` (also covers `v038()`).

### 14.5.9 Open questions (each with recommended default; implementation proceeds on the default)
**Resolved (User, 2026-11-09):** payout timing = variant B, at most once per round at the end of Phase 5 (§14.5.3).

Still pending User:
1. **Name / rules wording** for the payout. *Default:* no name; sim label "Red Secret payout" (provisional); Phase B wording "each player still in the game scores Corporate Secrets by Market Share place".
2. **End payout when Market Collapse is a secondary trigger** (e.g. Patient Zero and a survivor at 0 Market Share in the same round). *Default:* skip only when `end_reason == MARKET_COLLAPSE` (primary reason; matches the model).
3. **Market Share maximum** under 16/16/17 start. *Default:* max = start (as v038b), Public Relations Track caps unchanged.
4. **Oldest first for Magnetic Splice / Jumper Diagnostics targets.** *Default:* no — only Conveyor Triage is forced; those powers keep player choice.
5. **Recipients and schedule.** *Default:* survivors at the end of Phase 5; schedule by starting player count.
6. **Oldest first ignores die colour.** *Default:* yes, all dice by entry order.

**§14.5.9 resolution (User, 2026-11-09):** all remaining open questions accepted at their recommended defaults — Q1 no name (sim prose "Red Secret payout", provisional; confirm before Phase B rules wording); Q2 end payout skipped only when Market Collapse is the primary `end_reason`; Q3 Market Share maximum = start (16 / 16 / 17); Q4 Magnetic Splice / Jumper Diagnostics keep player choice; Q5 survivors at end of Phase 5, schedule by starting player count; Q6 oldest-first ignores die colour.
