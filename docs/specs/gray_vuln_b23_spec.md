# Technical Specification: Gray Legacy ⚠ on Faces 2 and 3 (B23), Pen Test Level 2 Gray Thinning (a1) and the Gray-Aware Research Bot (`v0.50.0`)

**Author:** Principal Engineer
**Date:** 2026-11-19
**Target:** `v0.50.0`. **Base:** `GameConfig.v049()` / `v049_roster()` (`sim/config.py:1245-1265`).
**Approved design:** `docs/plans/gray_vulnerability_gd_plan.md` §6, §7, §9 (the User picked B23 and approved a1 and the Gray-aware bot on 2026-11-19; see §9.5 U1–U2).
**Guardrails:** `FINDINGS.md` §65 (re-based guardrails) and plan §9.
**Probe being ported:** `scripts/probe_gray_vuln_mitigation.py` (monkeypatches only). After this spec is implemented, the probe stays as it is. It is the reference for the port-fidelity check (§10.4).

---

## 0. Terminology guardrails

- **No new terms.** Every term used here is already in `GLOSSARY.md`: **Breakthrough**, **Locked Die**, **Pen Test Track**, **Gray Legacy Code Dice**, **Vulnerability**, **Sprint Plan** / **Current Sprint** / **Next Sprint**, **Research & Development**, **Ready for Release Zone**, **In Production Area**, *Brute-Force Bypass*, *Arbitrary Code Execution*, **Release Track** (Level 4 Capstone).
- "Return `1` Gray Legacy die you own to the box" is the existing wording of the Pen Test and Release Level 3 Breakthroughs (`RULES.md:46`, `:298`). a1 reuses that wording exactly.
- Code-only identifiers are not game terms and must not appear in player-facing text: `V050_GRAY2`, `GRAY_AWARE`, `pen_test_l2_breakthrough`, `PEN_TEST_L2`, "thin value", "hot".
- **Definition edit (not a new term):** the GLOSSARY **Breakthrough** entry and `RULES.md:42` / `:296` say Breakthroughs sit at "Levels 1 and 3". Under a1, the Pen Test Track also has a Breakthrough at Level 2. The doc sync (§12 step 9) must reword these lines; the term itself does not change. This is open question Q1.

## 1. Scope (signed-off package)

| # | Change | Kind | Flag (default = v0.49 behaviour) |
|:---|:---|:---|:---|
| 1 | **B23 Gray table:** ⚠ on Face 2 `+2 🔬` and Face 3 `+$2 / +2 🔬`. Payouts are unchanged from `_v048_gray_faces`. Under v0.49 every ⚠ face locks, so both faces are Locked Die faces. | `[RULE]` `[TUNE: v0.50.0]` | `gray_face_profile = "V050_GRAY2"` |
| 2 | **a1:** reaching Pen Test Level 2 is a Breakthrough: return `1` Gray Legacy die you own to the box. The Pen Test limit `2` at Level 2 is kept. Selection, fallback and zones mirror the Level 3 `THIN_GRAY` Breakthrough exactly. | `[RULE]` | `pen_test_l2_breakthrough = "NONE"` (on: `"THIN_GRAY"`) |
| 3 | **Gray-aware research bot** (sim-only): the probe's GA policy becomes a `bot_research_mode`. | sim-only `[TUNE-BOT]` | `bot_research_mode = "GRAY_AWARE"`; params `bot_gray_aware_params`; seat filter `bot_gray_aware_seats` |
| 4 | Presets `v050()` / `v050_roster()` inherit `v049()` / `v049_roster()` and turn on 1–3, plus telemetry. | preset | – |
| 5 | Telemetry: Gray held per round, Gray removed by source, round reaching ≤ 3 Gray, Gray ⚠ kept per roll, bot "hot" rounds. | telemetry | `gray_vuln_telemetry = False` |

**Invariant zero (INV-GV-PARITY-01):** every existing preset, including `v049()` and `v049_roster()`, replays bit-identically. All new fields default to v0.49 behaviour. No existing code path reads a new field unless that field is non-default. New end-row keys are emitted only under `gray_vuln_telemetry`.

## 2. Engine map (current touch points)

| Concern | File:function (line ≈) | Change |
|:---|:---|:---|
| Gray face tables | `sim/entities.py: _v048_gray_faces` (1857), `create_gray_die` (1870), `GRAY_FACE_PROFILES` (1841) | add `_v050_gray_faces` and the `"V050_GRAY2"` branch |
| Gray die creation (all go through `cfg.gray_face_profile`) | `sim/engine/core.py:186` (setup), `:314`; `research_tracks.py:422, :429` (L1 Gray-die modes) | none: they pick up the profile automatically |
| Lock rule | `sim/engine/vulnerability.py: lock_applies` (21), `is_reroll_locked` (101), `face_vuln` (51) | none: both are face-driven (`face.vuln > 0`), so F2 locks automatically under `vuln_lock_gray` / `vuln_face_lock="GRAY"` |
| Deploy ⚠ count + roll telemetry | `vulnerability.py: lock_in` (110) → `sprint_plan.record_roll` (195) | extend `record_roll` (§8) |
| Breakthrough levels | `research_tracks.py: BREAKTHROUGH_LEVELS = (1, 3)` (33), `has_level_effect` (220), `resolve_breakthrough` (372), `breakthrough_text` (51), `breakthrough_preview` (552) | a1 branch (§5) |
| Thinning primitive | `research_tracks.py: _thin_gray` (334), `thin_gray` (365); order from `sprint_plan.owned_gray` (53) | reuse unchanged; new source tag `"PEN_TEST_L2"` |
| Bot thin pick | `sim/bots/base.py: BaseBot.choose_thin_gray` (812) | none |
| Operations research purchase | `sim/engine/phase6_operations.py` (~413-430): `upgrade_track` → `has_level_effect` → `ask_breakthrough_choice` → `resolve_breakthrough` | none: it picks up L2 through `has_level_effect` |
| Web upgrade path | `web/controller/phase5_operations_actions.py:684-697` | none for the sim; L2 auto-resolves through the same `resolve_breakthrough(..., None)` call. The log label is a web follow-up (§12 step 10) |
| Bot research order | `sim/bots/research_policy.py: _thinning_aware_want_order` (130), `_plan_research_share_regain` (155, MONEY branch line 176) | add `_gray_aware_want_order` + dispatch (§6) |
| Release L4 Gray face-set | `phase1_roll_deploy.py: resolve_release_l4_gray_face_override` (182); bot `vulnerability_policy.choose_release_l4_face` (226) | none (edge case §7.2) |
| ACE / Helix | `phase1_roll_deploy.py: resolve_prodigy_purple_star_override` (~120-179), Helix loop (~500-680) | none (edge cases §7.3–7.4) |
| End row | `sim/engine/end_game.py` rankings dict (~351-353) | add `_v050_row` (§8.2) |
| PlayerState | `sim/engine/state.py` (~490, beside `gray_removed_by_source` / `thin_rounds` / `thin_forfeits`) | new telemetry fields (§8.1) |

## 3. Configuration and presets

### 3.1 New module constants (`sim/config.py`, near line 50)

```python
V046_GRAY_FACE_PROFILES = ("V046_VULN", "V048_SPRINT", "V050_GRAY2")   # extend (the _validate_v046 vuln gate reads it)
_PEN_TEST_L2_MODES = ("NONE", "THIN_GRAY")
_BOT_RESEARCH_MODES = ("LEGACY", "THINNING_AWARE", "GRAY_AWARE")       # extend
```

`sim/entities.py:1841`: `GRAY_FACE_PROFILES = ("V034", "V035_D1", "V048_SPRINT", "V050_GRAY2")`. Leave `V046_VULN` out of that tuple, as now; it is not read for validation.

### 3.2 `GrayAwareParams` (sim-only `[TUNE-BOT]`; frozen dataclass next to `PrPushParams` / `VulnPolicyParams`, ~line 211-260)

Every default equals the probe's `GA_PARAMS` (`probe_gray_vuln_mitigation.py:52`), plus the hard-coded `g >= 2` gate.

```python
@dataclass(frozen=True)
class GrayAwareParams:
    rolls_per_round: float = 0.56   # Gray rolls per owned Gray die per round (plan §4)
    rp_per_vuln: float = 2.0        # research per -1 Vulnerability (kept constant, not read from pen_test_cost, for probe fidelity; Q4)
    near_vuln: int = 3              # Vulnerability at or above this adds near_bonus
    near_bonus: float = 1.0
    v_thin: float = 1.5             # "hot" threshold: push thinning tracks
    v_rel4: float = 2.5             # also push Release to L4 (set-Gray-face)
    last_round: int = 9             # rounds left = max(1, last_round - current_round)
    min_gray: int = 2               # only hot while owning >= min_gray Gray dice
```

### 3.3 New `GameConfig` fields (one v0.50 block after the v0.49 block, ~line 600; all defaults reproduce v0.49)

```python
# --- v0.50.0 Gray ⚠ B23 + Pen Test L2 thinning (docs/specs/gray_vuln_b23_spec.md); every default = v0.49 behaviour ---
pen_test_l2_breakthrough: str = "NONE"         # [RULE] "NONE" | "THIN_GRAY": reaching Pen Test L2 returns 1 owned Gray die to the box
bot_gray_aware_params: GrayAwareParams = field(default_factory=GrayAwareParams)  # sim-only [TUNE-BOT]
bot_gray_aware_seats: Optional[Tuple[int, ...]] = None  # sim-only: GRAY_AWARE seats (None = all); other seats use THINNING_AWARE
gray_vuln_telemetry: bool = False              # sim-only: emit the _v050_row end-row keys (no gameplay effect)
```

`gray_face_profile` already exists (line 434). It gains the value `"V050_GRAY2"`. `bot_research_mode` (line 570) gains `"GRAY_AWARE"`; update its comment.

### 3.4 Validation: `_validate_v050()`, called from `__post_init__` right after `_validate_locked_vuln()` (line 770)

1. `pen_test_l2_breakthrough in _PEN_TEST_L2_MODES`, else `ValueError`.
2. `pen_test_l2_breakthrough == "THIN_GRAY"` requires `is_v035_tracks` (mirrors line 1530) **and** `defense_mode == "VULNERABILITY"`. Without the Vulnerability Track, "DEFENSE" is not the Pen Test Track.
3. `gray_face_profile == "V050_GRAY2"` requires `defense_mode == "VULNERABILITY"`. This mirrors line 1510. `_validate_v046` also enforces it through `V046_GRAY_FACE_PROFILES`; keep the explicit message anyway.
4. `bot_research_mode` membership is already checked in `_validate_v048` (line 1503) once the tuple is extended. Add: `GRAY_AWARE` requires `share_regain_currency == "MONEY"`, because the policy is only dispatched in that branch (§6.3). Otherwise raise, so a silent no-op can't happen.
5. `bot_gray_aware_seats` is `None` or a duplicate-free tuple of ints in `[0, num_players)`. A non-`None` value with `bot_research_mode != "GRAY_AWARE"` raises: the seats would be ignored.
6. `GrayAwareParams`: all floats `>= 0`, `near_vuln` and `min_gray` are ints `>= 0`, `last_round >= 1`, and `v_rel4 >= v_thin`.
7. `gray_vuln_telemetry` is a bool.

Don't require `V050_GRAY2` to have `vuln_lock_gray`. Arms may sweep B23 without the lock. The v0.50 preset gets the lock from v0.49.

### 3.5 Presets (after `v049_roster`, ~line 1266)

```python
@classmethod
def v050(cls, **overrides) -> "GameConfig":
    """v0.50.0 Gray ⚠ B23 + Pen Test L2 Gray thinning (docs/specs/gray_vuln_b23_spec.md). Inherits v049()."""
    for k, v in (
        ("gray_face_profile", "V050_GRAY2"),          # B23: ⚠ on F2 +2 🔬 and F3 +$2 / +2 🔬
        ("pen_test_l2_breakthrough", "THIN_GRAY"),    # a1
        ("gray_vuln_telemetry", True),
    ):
        overrides.setdefault(k, v)
    return cls.v049(**overrides)

@classmethod
def v050_roster(cls, **overrides) -> "GameConfig":
    """v0.50.0 + the roster bots with the Gray-aware research focus (sweep default)."""
    for k, v in (
        ("bot_pr_push", True), ("bot_pr_push_params", PrPushParams()),   # v0.49 roster defaults
        ("bot_research_mode", "GRAY_AWARE"),
    ):
        overrides.setdefault(k, v)
    return cls.v050(**overrides)
```

Note: `v049_roster` calls `cls.v049(...)`, so `v050_roster` must not delegate to it; copy the v0.49 roster defaults (check `v049_roster` for the full list) and return `cls.v050(**overrides)`. Test T-CFG-3 asserts that `v050_roster()` equals `v049_roster(gray_face_profile="V050_GRAY2", pen_test_l2_breakthrough="THIN_GRAY", gray_vuln_telemetry=True, bot_research_mode="GRAY_AWARE")` field by field.

Leave `bot_thin_tracks=("RELEASE",)` and `bot_thin_gray_floor=3` unchanged. GRAY_AWARE uses them through its THINNING_AWARE base order.

## 4. B23 Gray table (`sim/entities.py`)

```python
def _v050_gray_faces() -> List[Face]:
    """``V050_GRAY2`` Gray table (docs/specs/gray_vuln_b23_spec.md §4): V048_SPRINT payouts, ⚠ on Face 2 and Face 3."""
    return [
        Face(name="+$1 & +1 🔬", money=1, patches=1),
        Face(name="+2 🔬 ⚠", patches=2, vuln=1),
        Face(name="+$2 / +2 🔬 ⚠", is_choice=True, vuln=1,
             choices=(Face("+$2", money=2), Face("+2 🔬", patches=2))),
        Face(name="+$1 / +1 🔬", is_choice=True, choices=(Face("+$1", money=1), Face("+1 🔬", patches=1))),
        Face(name="+$1", money=1),
        Face(name="+1 🔬", patches=1),
    ]
```

`create_gray_die`: add `elif profile == "V050_GRAY2": faces = _v050_gray_faces()` before the `else`. Face order and count stay the same (6 faces, same indices). So `Die.roll` uses the same RNG draws, and `face_key` stays `"GRAY:1".."GRAY:6"`.

- **INV-GV-FACE-01:** under `V050_GRAY2`, a Gray die has `face_vuln > 0` on exactly indices 1 and 2 (F2, F3). Money / research / choice payouts equal `_v048_gray_faces()` face by face (compare every field except `name` and `vuln`).
- **INV-GV-FACE-02:** under `v050()`, `lock_applies(cfg, gray_die)` is True iff the current face is F2 or F3, and `is_reroll_locked` gives the same result. Both need no code change.
- Leave `_v048_gray_faces` untouched (parity).

## 5. a1: Pen Test Level 2 Breakthrough (`sim/engine/research_tracks.py`)

### 5.1 `has_level_effect`

Add this before the `level == MAX_LEVEL` block:

```python
if (level == 2 and config is not None and normalize_track(track) == "DEFENSE"
        and getattr(config, "pen_test_l2_breakthrough", "NONE") == "THIN_GRAY"):
    return True
```

Leave `BREAKTHROUGH_LEVELS` as `(1, 3)`. Changing it would turn on L2 effects for every track and every preset.

### 5.2 `resolve_breakthrough`: a new branch before the L3 `THIN_GRAY` branch (line 414)

```python
elif t == "DEFENSE" and level == 2 and cfg.pen_test_l2_breakthrough == "THIN_GRAY":
    hit = _thin_gray(engine, player, "PEN_TEST_L2", choice)
    if hit is None:
        rec.outcome, rec.detail = "FORFEITED", {"reason": "no_gray_die"}
    else:
        rec.detail = {"gray_die_id": hit[1].die_id, "zone": hit[0]}
```

This branch is byte-for-byte the L3 branch with its own source tag. Everything else is inherited:

- **Selection order (INV-GV-L2-ORDER-01):** an explicit `BreakthroughChoice.gray_die_id`, if it names an owned Gray die. Otherwise `player.bot.choose_thin_gray(player, state, candidates)`. Otherwise `candidates[0]`. The candidates come from `sprint_plan.owned_gray`: **R&D → Next Sprint → In Production → Current Sprint → Ready**, in list order within each zone.
- **Zones:** the die leaves whichever list holds it (`_THIN_ZONE_ATTR`). A Gray die in R&D calls `secret_faces.lose_pending`; Gray has no R&D face, so in practice this is a no-op. `sprint_plan.prune(player)` drops a removed Current Sprint id, so the Sprint Review's forced count `min(|Current Sprint|, bw)` shrinks by one. The die goes **to the box**: not to the Central Market, no payout, and no `Corruption` / market stock change.
- **No-Gray fallback (INV-GV-L2-FORFEIT-01):** `player.thin_forfeits += 1`, the record is `FORFEITED` with `reason="no_gray_die"`, and **the Pen Test limit `2` still applies**. The limit comes from `pen_test_limits[level]` and is not part of the Breakthrough.
- **Once only (INV-GV-L2-ONCE-01):** the existing `any(b.track == t and b.level == level ...)` guard makes it once per player per game. A level can't be lost, so it can never re-fire.
- **Telemetry:** `gray_removed_by_source["PEN_TEST_L2"] += 1` and `thin_rounds.append(round)`, both inside `_thin_gray`.
- **Ordering within a turn (INV-GV-L2-SEQ-01):** buying L2 and L3 in one Operations Turn resolves L2, then L3, one level at a time (the existing loop in `phase6_operations.py:413-430`). A player with exactly 1 Gray die thins it at L2. L3 then forfeits its thin, but Blue R&D faces still yield `+3` from L3 (level-based, `RULES.md:343`).
- `ask_breakthrough_choice`: `breakthrough_options` returns `None` for DEFENSE L2, so bots go through `choose_thin_gray`, the same as L3. Don't add a DEFENSE L2 option object. The web prompts for no thin choice today at L3 either (§12 step 10).

### 5.3 Text

- `breakthrough_text`: if `t == "DEFENSE" and level == 2 and cfg.pen_test_l2_breakthrough == "THIN_GRAY"`, return `"Return 1 Gray Legacy die you own to the box"`.
- `breakthrough_preview` (the DEFENSE `txt` dict, ~line 570): add key `2`. When the flag is on, the value is `"Pen Test limit 2; return 1 Gray Legacy die you own to the box"`. When it is off, leave key 2 absent, so the current output stays bit-identical.

## 6. Gray-aware research bot (`sim/bots/research_policy.py`)

### 6.1 Interface

```python
def gray_vuln_face_share(config: GameConfig) -> float:
    """P(a Gray face carries ⚠) for config.gray_face_profile: (#faces with face_vuln > 0) / #faces. Cached per profile."""

def gray_thin_value(player: PlayerState, state: GameState, config: GameConfig) -> float:
    """V = rp_per_vuln x P(⚠ face) x rolls_per_round x max(1, last_round - current_round)
         + (near_bonus if player.vulnerability >= near_vuln else 0)."""

def is_gray_aware_seat(config: GameConfig, player: PlayerState) -> bool:
    """bot_research_mode == "GRAY_AWARE" and (bot_gray_aware_seats is None or player.player_id in it)."""

def _gray_aware_want_order(policy: ResearchPolicy, player: PlayerState, state: GameState,
                           config: GameConfig, lv: Dict[str, int]) -> List[str]:
    """Ported verbatim from probe_gray_vuln_mitigation.ga_order (§6.2)."""
```

All four are pure and deterministic: **no RNG and no state mutation**, apart from the telemetry counter in §6.2 step 3. `state.current_round` is read directly. The probe captured `state` through a wrapper; here it is passed in.

### 6.2 Algorithm (normative; it must reproduce the probe)

1. `base = _thinning_aware_want_order(policy, player, config, lv)`. This is the stock v0.49 order and stays unchanged.
2. `g = len(sprint_plan.owned_gray(player))`, `rnd = int(state.current_round)` (1 if `state` is None), and `V = gray_thin_value(...)`. `P(⚠ face)` comes from the configured table: `1/6` for `V048_SPRINT`, `2/6` for `V050_GRAY2`.
3. `hot = V >= v_thin and g >= min_gray`. If hot, add the round to `player.gray_aware_hot_rounds` (a set; see §8.1). The probe counted calls, so the telemetry differs by design. It does not affect play.
4. If not hot, return `base`.
5. Thinning targets:
   - `pen_t = 2` if `pen_test_l2_breakthrough == "THIN_GRAY"`, else `3`.
   - `tri_t = 3` if `triage_l3_breakthrough == "UPGRADE"`, else `4`.
   - For each `(t, tgt)` in `(("DEFENSE", pen_t), ("TRIAGE", tri_t))` with `lv[t] < tgt`, collect `(sum(track_step_costs[lv[t]:tgt]), t, tgt)`.
6. `head = (["TRIAGE"] if lv["TRIAGE"] < 1 else []) + ["RELEASE"] * max(0, 3 - lv["RELEASE"])`. Then, for each option sorted ascending (ties break by track name, through tuple sort, as in the probe), add `[t] * (tgt - lv[t])`.
7. If `V >= v_rel4 and lv["RELEASE"] >= 3`: append `"RELEASE"`.
8. Return `head + base`, de-duplicated with the per-track cap `count[t] < 4 - lv[t]`, in order.

**Port notes (must match the probe):**
- Under a1, `pen_t = 2`. Once Pen Test is at L2, Pen Test L3 is no longer a head target; it comes only from `base` / the want-list. This is the probe's behaviour (it produced "Pen Test L3 reached 84–86%" under the no-a1 arm only). Keep it; flag Q3.
- `tri_t = 4` (Triage L4 replacement) is used whether or not `triage_l4_free_die_replacement` is on. It is on in v0.49, so this is safe.
- Encryption (double cost) and affordability are handled by the caller's purchase loop, not here, as in the probe.

### 6.3 Dispatch (`_plan_research_share_regain`, MONEY branch, line 176)

```python
if config.bot_research_mode == "GRAY_AWARE" and is_gray_aware_seat(config, player):
    want_order = _gray_aware_want_order(policy, player, state, config, lv)
elif config.bot_research_mode in ("THINNING_AWARE", "GRAY_AWARE"):
    want_order = _thinning_aware_want_order(policy, player, config, lv)
elif ...  # unchanged legacy Triage-L4 injection
```

- Under GRAY_AWARE, a seat outside `bot_gray_aware_seats` uses THINNING_AWARE. This is the probe's GA0 arm.
- Unchanged and out of scope, as in the probe: the `bot_research_rush` path (line 167), the PR-push window path in `apply_research_policy` (`prp.ordered_research`, ~line 285-308), and the RESEARCH-currency path. GRAY_AWARE needs MONEY, which validation rule 4 enforces.
- **INV-GV-BOT-01:** with `bot_research_mode != "GRAY_AWARE"`, `_gray_aware_want_order` is never called, so `gray_aware_hot_rounds` stays empty.
- **INV-GV-BOT-02:** when a seat is not hot, its want order equals `_thinning_aware_want_order(...)` exactly.

### 6.4 Other bot hooks: no change

- `choose_thin_gray` keeps the default first candidate.
- The Pen Test spend policy (`vulnerability_policy.apply_pen_test_policy`) is unchanged.
- The reroll / lock filter is λ-aware and face-driven, so it picks up F2's ⚠ automatically.
- `choose_release_l4_face` / `choose_helix_face` / `choose_ace_target` evaluate `face_net_value` with λ, so a locked F2 / F3 is now a candidate for override. That is intended.
- `ref1` (`reference_search.py`) clones the config and inherits the policy. Check it in §11.3 and leave it unmodified.

## 7. Edge cases (normative)

| # | Case | Rule / expected engine behaviour | Test |
|:---|:---|:---|:---|
| 7.1 | **Player with no Gray dice left** | a1 and the L3 thin both forfeit: `FORFEITED/no_gray_die`, `thin_forfeits += 1`. The Pen Test limit and the Blue `+3` still apply. The GRAY_AWARE seat is never hot (`g < min_gray`), so its order is THINNING_AWARE. `gray_le3_round` / `gray_le2_round` are set at the first Sprint Review at or below the threshold. A Release L4 set-face finds no Gray in `active_dice` and returns False. No exceptions anywhere. | T-L2-3, T-BOT-4 |
| 7.2 | **Release L4 set-Gray-face** | It can target a **locked** F2 / F3 Gray die. `resolve_release_l4_gray_face_override` sets `is_locked=False` and the chosen face. ⚠ is counted on the final face at Deploy. Setting a locked `+2 🔬 ⚠` to F1 `+$1 & +1 🔬` removes 1 ⚠ for an equal 2-value payout. Setting a die *to* F2 / F3 is legal (it is a printed face), and the λ bot just won't choose it unless it gains. `l4_payouts["release_gray_face_sets"]` counts uses. No code change. | T-EDGE-2 |
| 7.3 | **Prodigy *Arbitrary Code Execution*** | ACE may target a locked Gray F2 / F3 die and set any non-★, non-Secret face (Gray has neither). That breaks the lock (`ace_lock_breaks += 1`), and ⚠ is counted on the final face. ACE gets more valuable targets under B23. No code change. Watch the Prodigy win % (§11). | T-EDGE-3 |
| 7.4 | **Helix *Brute-Force Bypass*** (once per game, H1B) | With the Bypass active, locked Gray F2 / F3 dice may be rerolled (`reroll_allowed(..., helix_active)`); the v0.48 `is_reroll_locked` filter is skipped while `helix_active` (`phase1_roll_deploy.py:578`). A rerolled Gray die landing on ⚠ re-locks (`_evaluate_locks`) but stays rerollable during the Bypass. The H1B face-set can set a Gray die to any non-★ face. `helix_bypass_locked_rerolled` / `helix_bypass_face_sets` count it. More locked Gray means more Bypass triggers per game; the once-per-game limit is unchanged. No code change. | T-EDGE-4 |
| 7.5 | **2P SETEC Corp** | The SETEC Corp Black Cube is state-level (`state.setec_corp_*`), not a `PlayerState`. It owns no dice, has no Pen Test Track and no Vulnerability. Thinning, telemetry loops and GRAY_AWARE iterate `state.players` only. Red Signature "lowest rival" (which counts SETEC Corp at 2P) is unaffected. Green targeting is unaffected, because SETEC Corp has no Vulnerability. | T-EDGE-5 |
| 7.6 | **L2 and L3 in one turn; L2 with Current Sprint Gray** | Covered in §5.2. If the thinned die was in the Current Sprint, that round's Sprint Review forces one fewer graduate, and spare bandwidth back-fills from the Next Sprint (`sprint_review`, `_validate(..., backfill=True)`). | T-L2-4, T-L2-5 |
| 7.7 | **Gray gained after setup** | Under v0.48+, L1 Breakthroughs give no Gray dice (`pen_test_l1="SECRET"`, `release_l1_breakthrough="BANDWIDTH"`, `triage_l1_breakthrough="CASH"`). If an arm re-enables a Gray-die L1, the new die uses `V050_GRAY2`. No special case. | – |
| 7.8 | **Patient Zero mid-round** | An eliminated player takes no Operations Turn, so it gets no L2. It keeps its last `gray_owned_by_round` entry. Its `gray_le3_round` stays `None` if it never got there. | – |
| 7.9 | **Spook *Burn Notice*** | Burn Notice is an independent thin source (`"BURN_NOTICE"`). Its relative value rises a little. Telemetry only. | §11 |

## 8. Telemetry

### 8.1 `PlayerState` fields (`state.py`, beside line 490; always initialised, plain types)

| Field | Type | Written by | Definition |
|:---|:---|:---|:---|
| `gray_owned_by_round` | `Dict[int, int]` | `sprint_plan.sprint_review` (after line 191) | Owned Gray at the end of that round's Sprint Review. This is the "held entering round r+1" convention of the probe's `gray_owned_by_player`. |
| `gray_le3_round` / `gray_le2_round` | `Optional[int]` | the same | The first round whose value is ≤ 3 / ≤ 2. This is the probe's `reach()`. |
| `gray_rolled_total` | `int` | `sprint_plan.record_roll` | Gray dice rolled (active at Deploy) |
| `gray_vuln_kept_total` | `int` | the same | ⚠ on the final Gray faces at Deploy |
| `gray_vuln_kept_by_face` | `Dict[str, int]` | the same | `face_key` (`"GRAY:2"`, `"GRAY:3"`) → kept ⚠ |
| `gray_rolls_by_round` | `Dict[int, List[int]]` | the same | `round → [gray_rolled, gray_vuln_kept]` (per-roll ⚠ rate by round, including the round-2 spike) |
| `gray_aware_hot_rounds` | `Set[int]` (emit as a sorted list) | `_gray_aware_want_order` | Rounds in which this seat was hot |

The existing fields stay as they are and are reused: `gray_removed_by_source` (new key `"PEN_TEST_L2"`, plus `RELEASE_L3`, `PEN_TEST_L3`, `TRIAGE_L3`, `TRIAGE_L4`, `BURN_NOTICE`), `thin_rounds`, `thin_forfeits`, `level_reached_round`, `l4_payouts["release_gray_face_sets"]`, the `helix_bypass_*` fields, `ace_lock_breaks`, `lock_events_by_face`, and the per-round `state.sprint_round` keys `gray_owned_by_player` / `gray_rolled_by_player` / `gray_vuln_kept_by_player`.

These writes run on the existing `cfg.sprint_plan_enabled` branches. They mutate only the new fields, which are not in `_snapshot_players` or the end row, so the v0.49 digest is unaffected (INV-GV-PARITY-01).

### 8.2 End row `_v050_row(cfg, p)` (`end_game.py`; spread after `_v047_row`; emitted only when `cfg.gray_vuln_telemetry`)

Keys: `gray_owned_by_round`, `gray_le3_round`, `gray_le2_round`, `gray_removed_by_source`, `gray_removed_total`, `thin_rounds`, `thin_forfeits`, `gray_rolled_total`, `gray_vuln_kept_total`, `gray_vuln_kept_by_face`, `gray_rolls_by_round`, `gray_aware_hot_rounds`, `release_gray_face_sets`, `pen_test_l2_round` (= `level_reached_round["DEFENSE"].get(2)`). Use JSON-safe copies (`dict(...)`, `sorted(...)`).

### 8.3 Sweep-derived metrics (per pod; §11 script)

- Gray held per seat at R1–R8.
- Gray removed per seat by source.
- `gray_le3_round` mean, and the % of seats that never reach ≤ 3.
- % of seats ever at ≤ 2.
- Gray ⚠ per Gray rolled, Gray ⚠ per seat-round, and R2 Gray ⚠ per seat.
- Pen Test L2 / L3, Triage L4 and Release L4 reach % and mean round.
- Hot rounds per seat.
- Win % for `gray_le3_round ≤ 4` against later (the plan §9.2 timing gap).
- Helix / Spook / Prodigy / Operator win %.
- Release L4 face-sets, Helix face-sets and Bypass locked-rerolled per seat.

## 9. Invariants (summary)

| ID | Statement |
|:---|:---|
| INV-GV-PARITY-01 | `v049()` / `v049_roster()` (and every older preset) digests equal the golden captured before any v0.50 edit. |
| INV-GV-PARITY-02 | `v050_roster(gray_face_profile="V048_SPRINT", pen_test_l2_breakthrough="NONE", bot_research_mode="THINNING_AWARE", gray_vuln_telemetry=False)` gives the same digest as `v049_roster()`. |
| INV-GV-TEL-01 | `gray_vuln_telemetry` changes no gameplay: the end reason, rounds, winners and per-seat Secrets are identical with it on and off. |
| INV-GV-FACE-01/02 | §4 |
| INV-GV-L2-ORDER-01, -FORFEIT-01, -ONCE-01, -SEQ-01 | §5.2 |
| INV-GV-BOT-01/02 | §6.3 |
| INV-GV-RNG-01 | Neither a1 nor GRAY_AWARE draws from `engine.rng` or any other RNG. B23 draws exactly as many RNG values per roll as `V048_SPRINT`. |
| INV-GV-CONS-01 | Gray conservation per player: `5 (setup) + gained − Σ gray_removed_by_source = len(owned_gray(p))` at every Sprint Review (`--assert-invariants`). |

## 10. Tests (`tests/test_v500_gray_vuln.py` unless noted; `python3 -m pytest -q`; fixed seeds)

### 10.1 Parity (do this first, before any engine edit)

- **T-PAR-0 (capture):** `tests/parity_v049/capture.py` is a copy of `tests/parity_v047/capture.py` with `CONFIGS = ("v049", "v049_roster")`, seeds `42..141`, and 2/3/4P. Run `python3 -m tests.parity_v049.capture` on the untouched engine and commit `tests/parity_v049/golden.json`. Store it outside `tests/fixtures/`, which is write-protected.
- **T-PAR-1** `tests/test_v500_parity.py`: the golden is complete and `v049` / `v049_roster` replay it (INV-GV-PARITY-01).
- **T-PAR-2:** the existing parity suites stay green: `test_v480_parity.py` (v047), `test_locked_vuln_parity.py` (v046), `test_v460_parity.py`.
- **T-PAR-3:** INV-GV-PARITY-02 on 30 seeds × 2/3/4P.
- **T-PAR-4:** INV-GV-TEL-01, `v050_roster` with telemetry on and off, on 20 seeds × 3P.

### 10.2 Config

- **T-CFG-1:** `v050()` has `gray_face_profile == "V050_GRAY2"`, `pen_test_l2_breakthrough == "THIN_GRAY"` and `gray_vuln_telemetry`. Every other field equals `v049()`.
- **T-CFG-2:** each validation rule in §3.4 raises: L2 THIN_GRAY with `defense_mode="SHIELDS"`; V050_GRAY2 without VULNERABILITY; GRAY_AWARE with RESEARCH currency; seats out of range, duplicated, or set without GRAY_AWARE; bad params.
- **T-CFG-3:** `v050_roster()` equals the composed `v049_roster(...)` field by field (§3.5).

### 10.3 Engine

- **T-FACE-1:** INV-GV-FACE-01 (face-by-face payout equality with `_v048_gray_faces`; ⚠ indices == {1, 2}).
- **T-FACE-2:** under `v050()`, a Gray die set to F2 → `lock_applies` and `is_reroll_locked` are True. F1 / F4–F6 → False. A bot reroll request for a locked F2 is filtered out (`gray_lock_blocked` +1).
- **T-FACE-3:** Deploy with Gray dice showing F2 + F3 + F5 → `lock_in` adds +2 Vulnerability. `gray_vuln_kept_by_face == {"GRAY:2": 1, "GRAY:3": 1}`.
- **T-L2-1:** with a1 on, `has_level_effect(cfg, "DEFENSE", 2)` is True. With a1 off, or for any other track at L2, it is False.
- **T-L2-2:** order. Put Gray in R&D, Next, In Production, Current and Ready, then resolve L2 repeatedly through fresh players: the picks follow R&D → Next → In Production → Current → Ready. An explicit `BreakthroughChoice(gray_die_id=…)` wins. A bot `choose_thin_gray` override wins over the default (reuse the `test_v480_sprint_plan.py:67` stub).
- **T-L2-3:** no Gray → `FORFEITED/no_gray_die`, `thin_forfeits == 1`, and the Pen Test limit is 2 afterwards.
- **T-L2-4:** one Gray die, buy L2 + L3 in one Operations Turn (via `phase6_operations` with `track_upgrades=["DEFENSE","DEFENSE"]` from L1) → L2 TAKEN, L3 FORFEITED, `gray_removed_by_source == {"PEN_TEST_L2": 1}`, and Blue R&D yield `+3`.
- **T-L2-5:** thinning a Current Sprint Gray die → `current_sprint_ids` is pruned, and the next `sprint_review` forces `min(|cur|, bw)` with the smaller set, back-filling from the Next Sprint.
- **T-L2-6:** once only. Calling `resolve_breakthrough(e, p, "DEFENSE", 2)` a second time returns `None`. A cloned state does not re-fire (mirror `test_v480_sprint_plan.py:647-653`).
- **T-L2-7:** text. `breakthrough_text` / `breakthrough_preview` show the L2 text only with the flag on. The flag-off preview dict equals the v0.49 output.
- **T-CONS-1:** INV-GV-CONS-01 over 30 games of `v050_roster` at 2/3/4P.

### 10.4 Bot

- **T-BOT-1:** `gray_vuln_face_share` is `1/6` for V048_SPRINT and `1/3` for V050_GRAY2.
- **T-BOT-2:** `gray_thin_value` reproduces hand values: round 2, Vulnerability 3, B23 → `2 × 1/3 × 0.56 × 7 + 1 = 3.613`. Round 7, Vulnerability 0 → `0.747` (not hot).
- **T-BOT-3:** a table-driven `_gray_aware_want_order` against a **verbatim copy** of the probe's `ga_order` (inline it in the test and do not import the probe) on about 200 random `(lv, g, round, vuln, flags)` tuples. The lists must be identical.
- **T-BOT-4:** INV-GV-BOT-02. With `g < 2` or `V < 1.5`, the order equals THINNING_AWARE.
- **T-BOT-5:** with `bot_gray_aware_seats=(0,)`, seat 1 never accrues `gray_aware_hot_rounds`, and its orders equal THINNING_AWARE.
- **T-BOT-6:** INV-GV-RNG-01. Patch `engine.rng` with a counting wrapper; one Operations Turn under GRAY_AWARE and under THINNING_AWARE consumes the same number of draws.
- **T-FID-1 (port fidelity; slow, marked `@slow`; also runnable as `scripts/check_gray_vuln_port.py`):** native `v050_roster` against the probe (`play(("B23","GA","a1_penL2",P,seed))`), and native `v050_roster(bot_research_mode="THINNING_AWARE")` against the probe (`"B23","S","a1_penL2"`), on 50 seeds × 2/3/4P. End reason, rounds, winners and per-seat Secrets must be identical. If they differ, report the first divergent seed before you accept it. The only expected source of difference is a face `name`, and no engine path reads face names for decisions. Confirm this.

### 10.5 Edge cases

- **T-EDGE-2 (Release L4):** a locked Gray F2 at Release L4 → the override to F1 succeeds, `is_locked=False`, the Deploy ⚠ count excludes it, and `release_gray_face_sets == 1`.
- **T-EDGE-3 (ACE):** a Prodigy with a Purple ★ and a locked Gray F3 → ACE sets F1 and `ace_lock_breaks == 1`. ACE can't set a ★ face.
- **T-EDGE-4 (Helix):** with the Bypass active, a locked Gray F2 is rerolled (not blocked by `is_reroll_locked`) and `helix_bypass_locked_rerolled` +1. A second Bypass in a later round is unavailable (once per game).
- **T-EDGE-5 (2P SETEC Corp):** 20 seeds of 2P `v050_roster` → no exceptions, `setec_corp_active` is True, and the telemetry keys exist only for the 2 seats.

## 11. Sweep plan (product-owner)

### 11.1 Script

Add `scripts/run_gray_vuln_sweep.py`. It reuses `run_v380_secret_faces_sweep.build_engine` and the metric code of `probe_gray_vuln.summarize` + `probe_gray_vuln_mitigation.extra`, rewritten to read the native §8 telemetry (no monkeypatches). Flags: `--config`, `--base`, `--set JSON`, `--players 2,3,4`, `--games 1200`, `--seed0`, `--procs`, `--assert-invariants`, `--quiet` (default; one summary line per pod; JSON summaries to `sim_results/gray_vuln_v050/`). It prints a PASS / FAIL guardrail table. **The bug fix noted in §65 applies:** every guardrail row must compute its own pass state; don't reuse a default PASS.

### 11.2 Arms (mixed1 roster; two seed blocks `42..1241` and `1242..2441`, 1,200 games per pod per block; pooled 2,400)

| Arm | Config | Purpose |
|:---|:---|:---|
| **B0** | `v049_roster` (+ `gray_vuln_telemetry=True`, gameplay-neutral) | comparator: PZ + MC, Collapse, Green, rounds, Helix |
| **B48** | `v048_roster` | income comparator (bar ×1.20) |
| **M** | `v050_roster` | **candidate** (B23 + a1 + GRAY_AWARE all seats) |
| A-stock | `v050_roster` with `bot_research_mode="THINNING_AWARE"` | does a1 hold with stock bots (plan: +1.0 / +0.7 / +0.9) |
| A-noL2 | `v050_roster` with `pen_test_l2_breakthrough="NONE"` | B23 + GA only (plan: +0.9 / +0.3 / −0.9) |
| A-GA0 | `v050_roster` with `bot_gray_aware_seats=(0,)` | paired-seed payoff of the policy, against A-stock (plan: +1.4 / +3.4 / −0.5) |
| B0-GA | `v049_roster` with `bot_research_mode="GRAY_AWARE"` | the GA effect on G1, separated from the rule change |

Also run `scripts/run_v046_dominance_matrix.py --config v050_roster` (600 per cell) and `scripts/run_reference_bot_validation.py --config v050_roster --cells ref1` (3P, 1,200).

### 11.3 Guardrails (M against B0 on the same seeds, per player count 2P / 3P / 4P; pooled 2,400 unless noted)

| # | Guardrail | Bar | Plan §9 expectation (M) |
|:---|:---|:---|:---|
| G1 | Patient Zero + Market Collapse | ≤ B0 + 3 pp at **each** of 2P / 3P / 4P | +0.3 / −1.0 / −3.5 vs G1 stock |
| G2 | Market Collapse | ≥ 8% at 3P and 4P | 29.6 / 11.5 / 11.9 |
| G3 | Green Secrets lost per player-game, 2P | ≤ 2.5 (also report 3P / 4P) | 2.20 / 1.98 / 1.82 |
| G4 | Income (money + research per seat-round) | ≤ B48 × 1.20 | about ×0.93–0.94 vs G1 ≈ ×1.10 vs v0.48 |
| G5 | Dead turns (seat-rounds with money + research ≤ 1, the probe definition) | ≤ 0.5% (flag above 0.4%; Q5) | 0.27–0.29% |
| G6 | `--assert-invariants` | clean, including INV-GV-CONS-01 | – |

**Watch rows (report only, no bar):**
- rounds and Singularity %;
- Total Wipeout %;
- Helix win (par 50 / 33 / 25; v0.49 4P 19.2) and Spook (v0.49 4P 30.9);
- Prodigy and Operator win %;
- company and White Hat spread;
- Gray removed per seat by source (plan: 2.77);
- `gray_le3_round` (plan: 3.3);
- the early-vs-late ≤ 3 Gray win gap (plan: +5 / +7.5 / +7 pp under stock bots);
- Pen Test L2 / L3 reach %;
- Release L4 face-sets, Helix face-sets and locked-rerolled;
- Gray ⚠ per seat-round (plan: about 0.58–0.60);
- R2 Gray ⚠ per seat;
- ref1 win %;
- dominance-matrix stances (PenTestRush, KeepAll, Kamikaze).

**Escalation:** if G1 fails at one player count by ≤ 0.6 pp with SE ≈ 1.3, report it to the game-designer with the block split, as in plan §9.3. Don't retune in the sweep. The fallback is plan §9.5 b2 (Triage L3 free replacement); it needs User approval.

### 11.4 Commands (WSL; quiet)

```
python3 -m tests.parity_v049.capture                     # before engine edits
python3 -m pytest -q tests/test_v500_parity.py tests/test_v500_gray_vuln.py
python3 scripts/run_gray_vuln_sweep.py --config v050_roster --base v049_roster --players 2,3,4 --games 1200 --seed0 42   --assert-invariants
python3 scripts/run_gray_vuln_sweep.py --config v050_roster --base v049_roster --players 2,3,4 --games 1200 --seed0 1242 --assert-invariants
python3 scripts/run_gray_vuln_sweep.py --config v050_roster --set '{"bot_research_mode":"THINNING_AWARE"}' ...   # A-stock (likewise A-noL2, A-GA0, B0-GA)
```

## 12. Implementation order (senior-engineer) and touched files

1. Capture the v0.49 parity golden (T-PAR-0). Commit it alone.
2. `sim/config.py`: constants, `GrayAwareParams`, fields, `_validate_v050`, and the `v050` / `v050_roster` presets.
3. `sim/entities.py`: `_v050_gray_faces`, the `create_gray_die` branch, and `GRAY_FACE_PROFILES`.
4. `sim/engine/research_tracks.py`: `has_level_effect`, `resolve_breakthrough` L2 branch, `breakthrough_text`, `breakthrough_preview`.
5. `sim/engine/state.py` (PlayerState fields), `sim/engine/sprint_plan.py` (`sprint_review` / `record_roll` writes), `sim/engine/end_game.py` (`_v050_row`).
6. `sim/bots/research_policy.py`: helpers, `_gray_aware_want_order`, and dispatch.
7. Tests (§10) and `scripts/run_gray_vuln_sweep.py` (+ `scripts/check_gray_vuln_port.py`).
8. Run the full `pytest -q` and T-FID-1, then hand off to the staff-engineer.
9. **After the sweep passes (product-owner / doc sync, not the senior-engineer):**
   - `RULES.md:42`, `:46` (the Pen Test L2 cell gets "Limit `2` + return `1` Gray Legacy die you own to the box"), `:51`, `:116` ("two of its six faces carry ⚠"), `:296-298`, and the Release L4 face list (~187);
   - `RULES_APPENDIX.md` §6.A Gray row;
   - the GLOSSARY entries for **Breakthrough**, **Pen Test Track** and **Vulnerability** (the Gray ⚠ count);
   - `RULES_QUICKREF.md`;
   - the `CLAUDE.md` pillar text ("Gray dice carry one, on Face 3");
   - `pnp/` (Gray die art F2 ⚠; the Pen Test track art at L2 as a Breakthrough, where `pnp/generate_pnp.py:679, :865` hard-code `lv in (1, 3)`);
   - rebuild `tts/` (`python3 -m tts.build_tts`);
   - bump the version to `v0.50.0` across the files in the CLAUDE.md protocol;
   - record the result in a `FINDINGS.md` §66.
10. **Web follow-up:** the `web/controller/phase5_operations_actions.py` breakthrough label map (~150-164) needs `("DEFENSE", 2)`; the die tables need Gray F2 ⚠; and the default preset becomes `v050`. Humans get the default thin order at L2, the same as L3 today (no die prompt).

## 13. Open questions (the defaults let implementation proceed)

- **Q1 (User, doc wording):** "Breakthroughs at Levels 1 and 3" becomes "Levels 1 and 3 (Pen Test also Level 2)". Is that acceptable, or should the Pen Test L2 effect be described as part of the level reward without calling it a Breakthrough? Default: call it a Breakthrough, as approved in plan §9.5 U1. It has the same once-only and forfeit rules.
- **Q2 (User / game-designer):** a1 gives the Pen Test Track two thins (L2 and L3). Should the PnP mark both with the Breakthrough ★? Default: yes.
- **Q3 (game-designer):** under a1, GRAY_AWARE targets Pen Test L2, not L3 (a probe artefact, kept for fidelity). Should a v0.50.1 bot tune aim at L3 while 2 or more Gray remain? Default: keep it as ported.
- **Q4 (senior / game-designer):** `rp_per_vuln` is the constant `2.0`, not `cfg.pen_test_cost`. They are equal in every v0.46+ preset. Default: the constant, for fidelity.
- **Q5 (User):** the dead-turn bar. The plan gives no numeric bar. Is the proposed ≤ 0.5% (flag above 0.4%) acceptable?
- **Q6 (product-owner):** is the G1 bar against B0 = `v049_roster` (stock bots) as written, or against B0-GA? Default: B0 stock, which is what the User asked for ("≤ v0.49 + 3 pp").
