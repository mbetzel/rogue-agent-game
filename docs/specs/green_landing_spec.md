# Technical Specification: Green Hits Drop Vulnerability by Band, and One Green Hit per Player per Round (`v0.51.0`, Phase 72)

**Author:** Principal Engineer
**Date:** 2026-11-20
**Target:** `v0.51.0`. **Base:** `GameConfig.v050()` / `v050_roster()` (`sim/config.py:1309-1327`).
**Approved design:** `docs/plans/green_landing_gd_plan.md` §1, §2, §5, §7. The User signed it off on 2026-11-20, and every decision is resolved (§8):
- D1: the PZ + MC bar is waived;
- D2: the 2P Green residual is accepted;
- D3: the flat repeat cost is dropped;
- D4: a cancelled Aegis hit counts as the one hit;
- D5: bump to `v0.51.0`.

**Probe being ported:** `scripts/probe_green_drop_band.py`, arm `S2H1`. That is the `resolve_green` closure with `cap=True`, `flat=False`, `overflow=False` and landing `(2, 5, 8)`, plus the **stock** `loss_if` (`S2H1` is not in `AWARE`). The probe stays as it is and is the reference for the port check (§9.8).

---

## 0. Terminology guardrails

- **No new terms.** Every term used here is already in `GLOSSARY.md`: **Vulnerability** / **Vulnerability Track**, **Green Cubes**, **Corporate Secrets**, **Pen Test Track**, *Baffle Echo* (Aegis), **Patient Zero**, **Total Wipeout**, **Market Collapse**, **Target Lock**. "Band" is already used in `RULES.md`.
- Code identifiers are not game terms and must not appear in player-facing text: `vuln_hit_landing_by_band`, `vuln_one_hit_per_round`, `hit_landing`, "landing", "cap", "capped", `S2H1`.
- Player-facing wording in the web log and panels follows plan §7: "Vulnerability drops to `N`" and "already hit by Green this round". Never write "Landing", "Hit Cap", "Overflow", "Drop a band" or "Immune", whether as capitalized terms or as labels.

## 1. Scope

| # | Change | Kind | Flag (default = v0.50 behaviour) |
|:---|:---|:---|:---|
| 1 | After a Green hit (cancelled or not), Vulnerability is set by the hit's band: `5–7 → 2`, `8–10 → 5`, `11+ → 8`. Secret loss by band is unchanged (`1 / 2 / 3`). | `[RULE]` `[TUNE]` | `vuln_hit_landing_by_band = None` (on: `(2, 5, 8)`) |
| 2 | A player is hit by at most one Green cube per Phase 4 Green resolution. Later cubes skip them. Ties still hit every tied unhit player. If no unhit player is at the min target or above, the cube has no effect and still recycles. | `[RULE]` | `vuln_one_hit_per_round = False` (on: `True`) |
| 3 | The bot Green replay `loss_if` models changes 1 and 2. | sim bot | reads the two flags |
| 4 | Telemetry: unsafe landings, cap skips, cubes with no target because of the cap, hit rounds, and Corruption gains that enter the targeted range. | telemetry | emitted only when flag 1 or 2 is non-default |
| 5 | Presets `v051()` / `v051_roster()`; web ruleset `v0.51.0`. | preset / web | – |

**INV-LAND-00 (parity):** every existing preset, including `v050()` and `v050_roster()`, replays bit-identically against a v0.50 golden. While both flags are at their defaults, no existing code path changes behaviour. The new end-row keys appear only when a flag is non-default.

## 2. Engine map (current touch points)

| Where | What it does now | Change |
|:---|:---|:---|
| `sim/engine/vulnerability.py:68` `band_damage` | Damage by band | none; sibling helpers `band_index` and `hit_landing` are added (§4.1) |
| `sim/engine/vulnerability.py:149-191` `resolve_green` | Per-cube loop; a hit sets `vulnerability = cfg.vuln_hit_reset` | hit set, landing, counters, event keys (§4.2) |
| `sim/engine/phase2_compiler.py:258-268` `_v046_corruption_demote` | `raise_vulnerability(..., "corruption")` | a telemetry counter only (§6.1) |
| `sim/bots/vulnerability_policy.py:50-65` `loss_if` | Replay; a hit seat goes to `vuln_hit_reset` | hit set, cap, landing (§5) |
| `sim/engine/core.py:551-555` | Copies `green_round_stats` into `RoundTelemetry` | one new field (§6.3) |
| `sim/engine/end_game.py:375` | Spreads `_v050_row` | spread `_v051_row` after it (§6.2) |
| `web/controller/phase4_attack_actions.py:40-62` `green_preview` | Pure replay; a hit seat goes to `vuln_hit_reset` | cap, landing, event keys (§7.1) |
| `web/controller/phase4_attack_actions.py:261-273` `_log_green_and_signature` | "Vulnerability reset to {vuln_hit_reset}" | "drops to {land}"; text for a capped no-target cube (§7.2) |
| `web/schemas.py:485-506` vulnerability track view | `hit_reset` | add per-band `land`, `hit_landing_by_band`, `one_hit_per_round` (§7.3) |
| `web/controller/core.py:64, 118-123`, `web/schemas.py:596` | `v0.50.0`, `GameConfig.v050()` | `v0.51.0`, `GameConfig.v051()` (§7.4) |
| `web/static/js/components/action_dock.js:683-684`, `compiler.js:158, 286` | "reset to 0" text | text built from the landing values in the API (§7.5) |

## 3. Configuration and presets

### 3.1 New `GameConfig` fields

Add a v0.51 block right after the v0.50 block (after `gray_vuln_telemetry`, line 637):

```python
    # --- v0.51.0 Green hit landing + one hit per round (docs/specs/green_landing_spec.md); every default = v0.50 behaviour ---
    vuln_hit_landing_by_band: Optional[Tuple[int, ...]] = None  # [TUNE] Vulnerability after a Green hit, per band; None = vuln_hit_reset
    vuln_one_hit_per_round: bool = False           # [RULE] a player is hit by at most one Green cube per Phase 4
```

`vuln_hit_reset` stays and keeps its validation (`0 <= reset < min(vuln_min_target_by_version)`, line 1549). When `vuln_hit_landing_by_band` is not `None`, the engine, the bot and the web never read `vuln_hit_reset`. The web still exposes it.

### 3.2 Validation: `_validate_v051()`

Call it from `__post_init__` right after `self._validate_v050()` (line 809). Each error message names the field. The rules, in this order:

1. `vuln_one_hit_per_round` must be a `bool`, not an int.
2. `vuln_hit_landing_by_band` must be `None` or a `tuple`. A `list` is rejected, as for `bot_gray_aware_seats`.
3. If it is a tuple, let `th = vuln_band_thresholds` and `mt = vuln_min_target_by_version`. Then:
   - `len(land) == len(th)`;
   - every entry is an `int` (not a `bool`) and `>= 0`;
   - the entries are non-decreasing: `land[i] <= land[i + 1]`;
   - `land[0] < min(mt)`, so a band-0 hit can never be re-targeted in the same phase (the same rule as `vuln_hit_reset`);
   - `land[i] < th[i]` for every `i >= 1`, so a hit always leaves its band (INV-LAND-01).
4. A non-default value of either field requires `defense_mode == "VULNERABILITY"`.

Rule 3 also implies `land[i] <= vuln_track_max`, because `th[i] <= max(th) <= vuln_track_max` (checked at line 1544).

A landing at or above the min target is allowed with the cap off. That is the shape of the probe's `DB` arm. The engine and `loss_if` then let a later cube in the same phase hit that player again (TC-LAND-24).

### 3.3 Presets (after `v050_roster`, line 1327)

```python
    @classmethod
    def v051(cls, **overrides) -> "GameConfig":
        """v0.51.0 Green hit landing (2 / 5 / 8 by band) + one Green hit per player per round
        (docs/specs/green_landing_spec.md). Inherits v050()."""
        overrides.setdefault("vuln_hit_landing_by_band", (2, 5, 8))
        overrides.setdefault("vuln_one_hit_per_round", True)
        return cls.v050(**overrides)

    @classmethod
    def v051_roster(cls, **overrides) -> "GameConfig":
        """v0.51.0 + the v0.50 roster bots (PR push, Gray-aware research; sweep default)."""
        overrides.setdefault("vuln_hit_landing_by_band", (2, 5, 8))
        overrides.setdefault("vuln_one_hit_per_round", True)
        return cls.v050_roster(**overrides)
```

`v051_roster` delegates to `v050_roster`. It therefore equals the probe's base config plus the two flags, which TC-LAND-02 checks.

## 4. Engine (`sim/engine/vulnerability.py`)

### 4.1 Pure helpers (after `band_damage`, line 74)

```python
def band_index(cfg: Any, v: float) -> int:
    """Largest i with v >= thresholds[i]; 0 below thresholds[0] (the same rule as band_damage, OQ-4)."""
    idx = 0
    for i, t in enumerate(cfg.vuln_band_thresholds):
        if v >= t:
            idx = i
    return idx


def hit_landing(cfg: Any, v: float) -> int:
    """Vulnerability after a Green hit at ``v`` (cancelled or not). None -> vuln_hit_reset (v0.50)."""
    land = getattr(cfg, "vuln_hit_landing_by_band", None)
    return int(cfg.vuln_hit_reset) if land is None else int(land[band_index(cfg, v)])
```

This matches the probe's `_by_band`. Because the thresholds strictly increase, the probe's `max(1, #{t <= v}) - 1` is the same index.

### 4.2 `resolve_green` (normative; replaces lines 157-190)

The idempotence and buffer-overflow guards (lines 152-156) are unchanged.

```python
    n = int(attack.get(CubeColor.GREEN, 0))
    floor = min_target(cfg, s)
    cap = bool(getattr(cfg, "vuln_one_hit_per_round", False))
    seat = ...                                   # unchanged
    events, lost_by_player = [], {}
    hit_this_phase: set = set()                  # player_ids hit by Green this phase, cancelled hits included (D4)
    cap_no_target = 0
    for k in range(n):
        above = [p for p in s.players if eligible_for_green(s, cr, p) and p.vulnerability >= floor]
        elig = [p for p in above if not (cap and p.player_id in hit_this_phase)]
        if cap:
            for p in above:
                if p.player_id in hit_this_phase:
                    p.green_cap_skips += 1       # telemetry: at floor+ but skipped for this cube
        if not elig:
            capped = bool(above)                 # targets existed at floor+, all already hit
            cap_no_target += int(capped)
            events.append({"round": s.current_round, "cube": k, "pids": [], "v": None, "damage": 0,
                           "cancelled": [], "land": None, "capped": capped})
            continue                             # INV-VULN-04: no effect, the cube still recycles
        top = max(p.vulnerability for p in elig)
        hit = sorted([p for p in elig if p.vulnerability == top], key=seat)
        dmg = band_damage(cfg, top)
        land = hit_landing(cfg, top)
        cancelled = []
        for p in hit:
            # Aegis cancel / lose_secrets / green_secrets_lost / lost_by_player / green_hits /
            # green_hits_by_damage: unchanged (lines 172-181)
            p.vuln_reset_by_hit_total += p.vulnerability - land   # name kept (plan §7)
            p.vulnerability = land               # lands even when cancelled (ruling 1, D4)
            if land >= floor:
                p.green_landing_unsafe += 1
            p.green_hit_rounds.append(s.current_round)
            hit_this_phase.add(p.player_id)      # always recorded; read only when cap is on
        events.append({"round": s.current_round, "cube": k, "pids": [p.player_id for p in hit],
                       "v": top, "damage": dmg, "cancelled": cancelled, "land": land})
    s.green_cap_no_target += cap_no_target
    s.green_hit_events.extend(events)
    s.green_round_stats = {"round": s.current_round, "resolved": n,
                           "no_target": sum(1 for e in events if not e["pids"]),   # capped cubes included
                           "cap_no_target": cap_no_target,
                           "lost_by_player": lost_by_player, "events": events}
    return events
```

Notes:
- The per-hit order is unchanged from today and the probe: the Aegis decision, then the Secret loss, then the counters, then Vulnerability. `_aegis_green_cancel` is called with the same `(p, dmg)` as in the probe, so it makes the same RNG draws and bot calls.
- Every hit player has `vulnerability == top`, so they all share one `land`.
- `land` and `capped` are new event keys. They are always written, even at defaults. The parity digest reads only `rankings` and `player_snapshots`, so it never sees them, and no existing test compares whole event dicts.
- `flag_patient_zero`, the Target Lock Green fallback, Pen Test L4, the Green R&D face and G1 are unchanged (plan §5.3–5.6).

### 4.3 State fields

The new fields are always initialised and use plain types, so `fast_clone` copies them generically.

`PlayerState` (`sim/engine/state.py`, beside `green_secrets_cancelled`, line 384):

```python
        self.green_landing_unsafe: int = 0       # v0.51: hits whose landing is >= the min target
        self.green_cap_skips: int = 0            # v0.51: cubes that skipped this player under the one-hit rule
        self.green_hit_rounds: List[int] = []    # v0.51: round of every Green hit (cancelled included)
        self.corruption_vuln_into_target: Dict[int, int] = {}  # v0.51: Corruption gain -> times it took this player from < min target to >= min target
```

`GameState` (beside `green_round_stats`, line 1548) gains `green_cap_no_target: int = 0`.

## 5. Bot: `loss_if` (`sim/bots/vulnerability_policy.py:50-65`)

```python
def loss_if(v_self: float, rivals_v: Sequence[float], k: int, cfg: Any, floor: int) -> int:
    """Deterministic replay of resolve_green for ``k`` cubes: the Secrets this seat loses (no Aegis)."""
    vals = [float(v_self)] + [float(v) for v in rivals_v]
    cap = bool(getattr(cfg, "vuln_one_hit_per_round", False))
    hit: set = set()
    loss = 0
    for _ in range(k):
        elig = [i for i, v in enumerate(vals) if v >= floor and not (cap and i in hit)]
        if not elig:
            break
        top = max(vals[i] for i in elig)
        dmg = vuln.band_damage(cfg, top)
        land = float(vuln.hit_landing(cfg, top))   # float top: same band rule as band_damage
        for i in elig:
            if vals[i] == top:
                if i == 0:
                    loss += dmg
                vals[i] = land
                hit.add(i)
    return loss
```

- The `break` on no target stays. In the replay the hit set only grows and Vulnerability only falls, so once a cube finds no target, no later cube can find one either.
- `top` can be fractional, because `rivals_v` carries `rival_vuln_per_die` estimates. `band_damage` and `band_index` both compare `v >= t`, so pass the float straight through and don't truncate it with `int(top)`. The probe's aware arms used `int(top)`, but S2H1 used the stock `loss_if`, so this choice does not affect the port check (Q1).
- With `vuln_hit_landing_by_band=None` and the cap off, the function is the stock one.
- **INV-LAND-05:** on `v051` configs this function returns exactly what the stock `loss_if` returns.
  - In the stock replay, a hit seat goes to `0`, which is below the floor, so it is never eligible again.
  - With the cap, the hit seat is skipped instead.
  - Either way the other seats keep the same values, so every later cube picks the same top and the same damage.
  - So the native bot matches the probe's S2H1 run (stock `loss_if`) game for game.
- `lam`, `p_hit`, the stances and `aegis_green_cancel_default` are unchanged (plan §5.1, §5.9). A carry-over term in `lam` is out of scope.

## 6. Telemetry

### 6.1 Corruption watch item (`sim/engine/phase2_compiler.py:267-268`)

```python
    floor = vulnerability.min_target(cfg, engine.state)
    for p in get_targeted_players(...):
        before = p.vulnerability
        vulnerability.raise_vulnerability(cfg, p, gain, "corruption")
        if before < floor <= p.vulnerability:
            p.corruption_vuln_into_target[gain] = p.corruption_vuln_into_target.get(gain, 0) + 1
```

This is telemetry only, with no gameplay or RNG effect. The plan's watch item is the "Corruption +3 landing-at-5 count": a `+3` gain (`corruption_lowest_vuln_gain_double`) that takes a player from `2` to `5`. The sweep reports it as `corruption_vuln_into_target[3]`. The key is kept general, so `+2` entries (from `3` or `4`) are visible too.

### 6.2 End row `_v051_row(cfg, p)` (`sim/engine/end_game.py`, after `_v050_row`)

Spread it at line 375, gated on `getattr(cfg, "vuln_hit_landing_by_band", None) is not None or getattr(cfg, "vuln_one_hit_per_round", False)`.

| Key | Value |
|:---|:---|
| `green_landing_unsafe` | `p.green_landing_unsafe` |
| `green_cap_skips` | `p.green_cap_skips` |
| `green_hit_rounds` | `list(p.green_hit_rounds)` |
| `green_multi_hit_rounds` | number of rounds that appear `>= 2` times in `green_hit_rounds` (`0` with the cap on: INV-LAND-03) |
| `green_back_to_back` | `#{r in set(green_hit_rounds) : r + 1 in set(green_hit_rounds)}` (the probe's `b2b` numerator) |
| `corruption_vuln_into_target` | `dict(p.corruption_vuln_into_target)` |

### 6.3 Per round (`sim/engine/core.py:551-555`, `RoundTelemetry`)

- Add the field `green_cubes_cap_no_target: int = 0` to `RoundTelemetry`, set from `gs.get("cap_no_target", 0)`.
- `green_cubes_no_target` still counts every no-target cube, capped ones included.
- `GameState.green_cap_no_target` is the game total.

## 7. Web

### 7.1 `green_preview` (`web/controller/phase4_attack_actions.py:40-62`)

Mirror §4.2 without side effects:
- Keep a `done` set, and set `cap = cfg.vuln_one_hit_per_round`.
- Build `above = [pid for pid, val in v.items() if val >= floor]` and `elig = [pid for pid in above if not (cap and pid in done)]`.
- No target: append `{"cube", "pids": [], "v": None, "damage": 0, "cancelled": [], "land": None, "capped": bool(above)}`.
- Hit: compute `land = vulnerability.hit_landing(cfg, top)`. For every hit pid, set `v[pid] = land` and `done.add(pid)`. Append the existing keys plus `"land": land`.

The docstring's Baffle Echo sentence stays true: a cancel changes neither who is hit nor where they land.

### 7.2 Log text (`_log_green_and_signature`, lines 266-273)

- Hit: `... -{dmg} Corporate Secret(s), Vulnerability drops to {e['land']}.` Read the value with `e.get('land', s.config.vuln_hit_reset)`, so that old events still render.
- No target with `e.get("capped")` true: `Green cube {k}: every player at Vulnerability {floor}+ was already hit by Green this round (no effect).`
- Other no-target cubes keep the existing text.

### 7.3 Vulnerability track view (`web/schemas.py:485-506`)

- Each `bands[]` entry gains `"land": vulnerability.hit_landing(cfg, t)`, where `t` is that band's threshold.
- Add the top-level keys `"hit_landing_by_band"` (`list(...)` or `None`) and `"one_hit_per_round"` (`bool(cfg.vuln_one_hit_per_round)`).
- Keep `"hit_reset"`.

### 7.4 Ruleset

- `web/controller/core.py:64`: set `WEB_DEFAULT_RULES_VERSION = "v0.51.0"`.
- `_build_config` (lines 118-123): call `GameConfig.v051(...)`, and update the docstring to "v0.51.0 ... Green hits drop Vulnerability to 2 / 5 / 8, one Green hit per player per round ...".
- `web/schemas.py:596`: `"rules_version": "v0.51.0"`.
- `tests/test_v460_web.py:313, 324, 582`: the expected version becomes `v0.51.0`, and `v0.50.0` joins the rejected legacy versions (the test at line 320).

### 7.5 Static text (no logic)

- `action_dock.js:683`: replace `, reset to 0` with `, Vulnerability drops to ${g.land ?? vt.hit_reset}`.
- `action_dock.js:684`: when `g.capped`, show `every player at Vulnerability ${vt.min_target}+ already hit this round (no effect)`.
- `compiler.js:158` and `compiler.js:286`: replace "resets it/them to 0" with text built from `vt.bands` (`${b.from}–${b.to}: −${b.damage}, drops to ${b.land}`). When `vt.one_hit_per_round` is true, add "A player is hit by only one Green cube each round."

## 8. Invariants

| ID | Statement | Checked by |
|:---|:---|:---|
| INV-LAND-00 | Defaults reproduce v0.50: every `v050` / `v050_roster` game digests equal to the v0.50 golden. | TC-LAND-01 |
| INV-LAND-01 | A hit strictly lowers Vulnerability and leaves its band: `land < v_at_hit`, and `band_index(land) < band_index(v)` for hits in band `>= 1`. This follows from §3.2 rule 3. | TC-LAND-04, TC-LAND-20 |
| INV-LAND-02 | **Loss exactness:** for the same Phase 4 starting state and the same Aegis decisions, the per-seat Green Secret loss under `(land=(2,5,8), cap=True)` equals v0.50's under `(None, False)`. Only end Vulnerability differs. | TC-LAND-10 |
| INV-LAND-03 | With the cap on, no player appears in the `pids` of two events in the same round (`green_multi_hit_rounds == 0`). | TC-LAND-11, sweep |
| INV-LAND-04 | A cancelled hit (Baffle Echo) still lands, and still uses up the player's one hit. | TC-LAND-12 |
| INV-LAND-05 | On `v051` configs the new `loss_if` equals the stock v0.50 `loss_if` on every input. On any valid config it equals the per-seat loss from `resolve_green` with no Aegis. | TC-LAND-14, TC-LAND-15 |
| INV-LAND-06 | Per round: `no_target` equals the number of events with empty `pids`; `cap_no_target <= no_target`; and `cap_no_target == 0` when the cap is off. | TC-LAND-13 |
| INV-LAND-07 | When nobody cancels, the `green_preview` events equal the `resolve_green` events on the keys `cube, pids, v, damage, land, capped`. | TC-LAND-16 |
| INV-LAND-08 | The native `v051_roster` matches the probe's `S2H1` game for game on the same seeds (§9.8). | port script |
| INV-LAND-09 | The new telemetry changes no gameplay: `v051_roster` gives the same results with the end-row gate forced off. | TC-LAND-23 |
| INV-VULN-04/06/07/10 | Still hold: a cube with no target has no effect; there is one Patient Zero check; resolution is idempotent; there is no Green on a buffer overflow. | existing tests |

## 9. Tests

New tests go in `tests/test_v510_green_landing.py` and `tests/test_v510_parity.py`. Run them with `python3 -m pytest -q` on fixed seeds.

Unit cases:
- build an engine with the `mk_engine(cfg_name=...)` helper that `tests/test_v500_gray_vuln.py` uses;
- set `p.vulnerability` and `p.secrets` directly;
- build `cr` and `attack` the way `tests/test_v460_vulnerability_track.py` does (`atk(cr)`).

### 9.1 Parity (do this first, before any engine edit)

- **Capture:** add `tests/parity_v050/__init__.py` and `capture.py`.
  - `capture.py` is a copy of `tests/parity_v049/capture.py` with `CONFIGS = ("v050", "v050_roster")`, `PLAYERS = (2, 3, 4)` and `SEEDS = range(42, 142)`.
  - Its docstring points at `tests/test_v510_parity.py`.
  - Run `python3 -m tests.parity_v050.capture` on the untouched v0.50 engine, and commit `golden.json` without opening it.
- **TC-LAND-01:** check that the golden is complete, and that every golden key replays equal (0 mismatches).
- **TC-LAND-02:** `v051_roster(num_players=P)` equals `v050_roster(num_players=P)` field by field, except for the two new fields (a `dataclasses.fields` diff). The same holds for `v051` against `v050`.
- **TC-LAND-03 (neutral):** `v051_roster` with `vuln_hit_landing_by_band=None, vuln_one_hit_per_round=False` digests equal to the `v050_roster` golden at 2P / 3P / 4P, seeds `42..71`.
- **TC-LAND-03b (each rule alone is inert):** run `v050_roster` with `vuln_one_hit_per_round=True`, and separately with `vuln_hit_landing_by_band=(0, 0, 0)`, at 3P on seeds `42..71`.
  - Both must give the same `(end, rounds, winners, per-seat secrets)` as the golden games.
  - Neither rule ever binds alone: reset `0` is below the min target.
  - Only the gated end-row keys differ, so compare that key tuple, not the digest.

### 9.2 Config (TC-LAND-04..07)

- **TC-LAND-04:** `v051()` has `(2, 5, 8)` and `True`. Under the v0.50 thresholds `(5, 8, 11)`:
  - `hit_landing` maps `5, 6, 7 → 2`, `8, 9, 10 → 5` and `11..15 → 8`;
  - on a default config, `hit_landing(cfg, v) == 0` for every `v`.
- **TC-LAND-05:** each of these raises `ValueError`:
  - a landing tuple of length 2 or 4;
  - a `list`;
  - a `bool` or negative entry;
  - `(5, 2, 8)` (decreasing);
  - `(5, 5, 8)` (`land[0]` is not below the min target `5`);
  - `(2, 8, 8)` (`land[1]` is not below `th[1] = 8`);
  - `(2, 5, 11)` (`land[2]` is not below `11`);
  - `vuln_one_hit_per_round=1` (an int);
  - either flag non-default under `defense_mode="SHIELDS"`.
- **TC-LAND-06:** valid edge cases are accepted: `(4, 7, 10)` (the highest allowed landing in each band), `(0, 0, 0)`, and `(2, 5, 8)` with the cap off.
- **TC-LAND-07:** `band_index` returns `0` below `th[0]`, matching the OQ-4 fallback in `band_damage`. This is reachable only if `min_target < th[0]`; build such a config directly.

### 9.3 Engine units: the plan §2.1 / §2.2 tables (TC-LAND-08..13)

Use `v051` at 2–3P with no Aegis seats, and call `resolve_green` once with `k` Green cubes. Assert per-seat Secrets lost, end Vulnerability and the events.

| TC | Start V (seat order) | k | Loss | End V | Extra assertions |
|:---|:---|:---|:---|:---|:---|
| TC-LAND-08a | `[6]` / `[9]` / `[12]`: one player at 5+, the others ≤ 4 | 1 and 3 | `1` / `2` / `3` | `2` / `5` / `8` | with k = 3, cubes 2–3 have no target and `capped=False` for `[6]` (the hit lands at 2, below 5); `capped=True` for `[9]` / `[12]` (landed at 5 / 8 but already hit) |
| TC-LAND-08b | `[8, 6]` | 2 | `2, 1` | `5, 2` | |
| TC-LAND-08c | `[5, 8]` | 2 | `1, 2` | `2, 5` | cube 1 hits P1; cube 2 hits P0 |
| TC-LAND-08d | `[11, 7]` | 2 | `3, 1` | `8, 2` | |
| TC-LAND-08e | `[11, 11]` | 3 | `3, 3` | `8, 8` | one event with both pids; cubes 2–3 have `capped=True`; `cap_no_target == 2` |
| TC-LAND-08f | `[12, 9]` | 4 | `3, 2` | `8, 5` | `cap_no_target == 2`, `no_target == 2` |
| TC-LAND-08g | `[9, 5, 5]` | 3 | `2, 1, 1` | `5, 2, 2` | the tie at 5 takes one cube; cube 3 has `capped=True` |
| TC-LAND-08h | `[3, 4]` | 2 | `0, 0` | unchanged | both events have `capped=False`; `cap_no_target == 0` |

- **TC-LAND-09 (counters):**
  - In 08e, each seat has `green_landing_unsafe == 1` (`8 >= 5`) and `green_cap_skips == 2`.
  - In 08b, P1 has `green_landing_unsafe == 0`.
  - `vuln_reset_by_hit_total` rises by `v - land` (08d: `3` and `5`).
  - `green_hit_rounds == [round]`.
- **TC-LAND-11 (INV-LAND-03):** draw 200 random states with `random.Random(7)`: 2–4 seats, V in `0..15`, k in `0..6`. With the cap on, no pid appears in two events.
- **TC-LAND-12 (Aegis, D4):** an Aegis seat at `9` with `aegis_green_override={pid: True}`, a rival at `6`, and k = 2.
  - The Aegis seat loses `0`, ends at `5`, and has `green_hits_cancelled == 1`.
  - Cube 2 hits the rival, not the Aegis seat again.
- **TC-LAND-12b (≤ 0 Secrets):** a seat at `1` Secret and V `11`, k = 3, with no rivals at 5+.
  - It loses `3` once (Secrets go to `-2`) and is skipped by the other two cubes.
  - `flag_patient_zero` flags it once, after Green.
- **TC-LAND-13 (INV-LAND-06, no target):** k = 2 with every player at ≤ 4.
  - No Secret or Vulnerability changes.
  - The exited Green cubes still recycle: reuse `test_inv_vuln_04_no_target_still_recycles` on `v051`.
  - The round-stats relations of INV-LAND-06 hold.
- **TC-LAND-13b (buffer overflow):** with `cr.buffer_overflow=True`, `resolve_green` returns `[]`, with no landing and no counter change.

### 9.4 INV-LAND-02 property (TC-LAND-10)

Draw 1,000 random states with `random.Random(2026)`: 2–4 seats, V in `0..15`, k in `0..6`, floor 5. For each state, call `resolve_green` once on a `v050` engine and once on a `v051` engine, each from a fresh copy of the same state, with no Aegis.
- Per-seat Secret loss must be equal in every state.
- End V may differ only on seats that were hit.

### 9.5 Bot (TC-LAND-14..15)

- **TC-LAND-14 (INV-LAND-05, first half):** on 2,000 random inputs, the new `loss_if` on `v051` equals the stock v0.50 `loss_if`. Draw `v_self` and `rivals_v` from `0..15` plus fractional values `x + 0.4·j`, and k from `0..6`. Keep a frozen copy of the stock function in the test module.
- **TC-LAND-15 (INV-LAND-05, second half):** on 500 random integer states, `loss_if(V[seat], others, k, cfg, floor)` equals that seat's loss from `resolve_green` with no Aegis. Run it for `v051`, for `v050`, and for `(2, 5, 8)` with the cap off (the TC-LAND-24 shape).

### 9.6 Web (TC-LAND-16..19, in `tests/test_v460_web.py` or a new `tests/test_v510_web.py`)

- **TC-LAND-16 (INV-LAND-07):** play 30 seeded 3P web games to Phase 4. In every round with no cancel, the `green_preview` output before resolution equals the `resolve_green` events on the listed keys.
- **TC-LAND-17:** a hit at 8–10 logs "Vulnerability drops to 5", and a capped cube logs the "already hit by Green this round" line. The string "reset to" does not appear.
- **TC-LAND-18:** the vulnerability track view has `bands[*].land == [2, 5, 8]`, `one_hit_per_round is True` and `hit_landing_by_band == [2, 5, 8]`.
- **TC-LAND-19:** `rules_version == "v0.51.0"`, and `v0.50.0` is rejected.

### 9.7 Other edge cases

- **TC-LAND-20 (INV-LAND-01):** for every valid landing tuple in TC-LAND-06 and every `v` in `floor..15`, `hit_landing(v) < v`.
- **TC-LAND-21 (Target Lock fallback):** after a 5–7 hit (V `2`), the Green Target Lock fallback adds `+2` per unplaceable cube, so two unplaceable cubes give `2 + 4 = 6`. The fallback runs after Green, so it has no effect within the same phase.
- **TC-LAND-22 (Corruption counter):** a seat at `2` gets a `+3` Corruption gain.
  - Afterwards `corruption_vuln_into_target == {3: 1}`.
  - V and Secrets are the same as for the same gain without the counter.
- **TC-LAND-23 (end-row gate, INV-LAND-09):**
  - The `_v051_row` keys are present under `v051_roster` and absent under `v050_roster`.
  - `v051_roster` gives the same `(end, rounds, winners, per-seat secrets)` with the gate patched off, on 3P seeds `42..61`.
- **TC-LAND-24 (cap off, landing in range):** `(2, 5, 8)` with the cap off, state `[9]`, k = 2.
  - Cube 1 hits at 9 (−2, to 5), and cube 2 hits again at 5 (−1, to 2).
  - The total loss is `3`, and `green_multi_hit_rounds == 1`.
  - This documents that the cap, not the landing value, is what prevents repeat hits.

### 9.8 Port check (INV-LAND-08): `scripts/check_green_landing_port.py`

Follow the pattern of `scripts/check_gray_vuln_port.py`, with separate worker pools for native and probe runs.

- **Probe worker:** import `play` from `scripts.probe_green_drop_band` and call `play(("S2H1", P, seed))`.
- **Native worker:** in a fresh process:
  1. Import `scripts.probe_green_drop_band as pg`.
  2. Call `pg.install("R0")`. It restores the original functions, so the native engine code runs.
  3. Replace `pg.build_engine` with a wrapper that swaps the config name `"v050_roster"` for `"v051_roster"`.
  4. Call `pg.play(("R0", P, seed))`.

  Both sides then go through the same `play` and record code.
- **Compare** the whole returned record dict: end, rounds, wipeout, the `g` counters (including `land_unsafe` and `fizzle`), `round_losses`, `multi`, `hit_sr`, `b2b`, `lock`, and every seat dict. Probe events carry an extra `pdmg` key, but `play` falls back to `e["damage"]` without it, so the records are comparable.
- **Flags:** `--games` (default 100), `--players 2,3,4`, `--seed0 42`, `--procs`.
- **Output:**
  - one line per player count, for example `2P: 100/100 identical`;
  - on a mismatch, the first divergent seed and both signatures;
  - then `PASS` or `FAIL`, exiting with status 1 on `FAIL`.
- **Gate:** with `--games 200`, every game must be identical at each of 2P / 3P / 4P (200/200).

## 10. Sweep (product-owner): `scripts/run_green_landing_sweep.py`

The script reuses `scripts.run_v380_secret_faces_sweep.build_engine` and the record and summary code of `scripts/probe_green_drop_band.py` (`play` / `summarize`). It rewrites that code to read native telemetry (events with `land` / `capped`, and the `_v051_row` keys), so it needs no monkeypatches. It also reuses the income and dead-turn code of `scripts/run_gray_vuln_sweep.py` (`income_per_seat_round`, `--income-base`).

**Flags:**
- `--config` (default `v051_roster`);
- `--base` (default `v050_roster`);
- `--income-base` (default `v048_roster`; `""` skips it);
- `--set JSON`;
- `--roster mixed1`, `--players 2,3,4`, `--games 1200`, `--seed0`, `--procs`;
- `--assert-invariants`: on every game, check INV-LAND-03, INV-LAND-06, and that the worst per-seat per-round Green loss is ≤ 3;
- `--quiet` (the default) and `--no-save`.

**Output:**
- one summary line per arm and pod, then the guardrail table;
- JSON summaries to `sim_results/green_landing_v051/`.

Every guardrail row computes its own pass state; no row defaults to PASS (the FINDINGS §65 bug).

**Arms:**

| Arm | Config | Purpose |
|:---|:---|:---|
| M | `v051_roster` | candidate |
| B0 | `v050_roster` | comparator for the deltas and the accepted residual |
| B48 | `v048_roster` | income comparator |

**Seeds:** two blocks, `42..1241` and `1242..2441`. That gives 1,200 games per pod per block and 2,400 pooled. Report each block and the pool. Pass or fail is judged on the pool.

**Guardrails.** These apply to M at each player count (2P / 3P / 4P). The references come from the S2H1 probe (plan §7).

| # | Check | Pass if |
|:---|:---|:---|
| L1 | Patient Zero + Market Collapse % | within `70.6 / 73.5 / 80.0` ± 2 pp |
| L2 | Eliminated seats % | within `30.1 / 26.3 / 23.4` ± 2 pp |
| L3 | Rounds (mean) | within `8.22 / 8.14 / 8.10` ± 0.15 |
| L4 | Green Secrets lost per player-game | within `2.77 / 2.40 / 2.23` ± 0.15 |
| L5 | Back-to-back hits % (`b2b / hit seat-rounds`) | within `24 / 20 / 18` ± 3 |
| L6 | Multi-hit seat-rounds | `== 0` (invariant) |
| L7 | Worst per-seat round Green loss | `<= 3` |
| L8 | Market Collapse %, 3P and 4P | `>= 8` (reference `11.6 / 11.0`) |
| L9 | Total Wipeout %, 2P | `< 15` |
| L10 | Income per seat-round | `<= B48 × 1.20` |
| L11 | `--assert-invariants` | clean |

**Report only (no bar):**
- The PZ + MC delta against B0 (expected `+4.0 / +2.6 / +4.5`), labelled "accepted residual (D1)".
- The 2P Green-lost residual over the `2.5` cap, labelled "accepted residual (D2)".
- Helix, Aegis and Spook win % (Helix 4P reference: `20.5`).
- Company and White Hat win-rate spread (references: 2P `18.6`, 4P `12.2`).
- Unsafe-landing % of hits, capped cubes per game, and band mix.
- Corruption `+3` gains from `2` into 5+, per game (`corruption_vuln_into_target[3]`, §6.1).
- Pen Test L4 reach %, Singularity %, and dead turns.

**Escalation:** if a check misses its band by ≤ 1 SE at one player count, report it to the game-designer with the block split. Don't retune in the sweep.

**Commands (WSL, quiet):**

```
python3 -m tests.parity_v050.capture                     # before engine edits
python3 -m pytest -q tests/test_v510_parity.py tests/test_v510_green_landing.py tests/test_v460_vulnerability_track.py tests/test_v460_web.py
python3 scripts/check_green_landing_port.py --games 200 --players 2,3,4
python3 scripts/run_green_landing_sweep.py --players 2,3,4 --games 1200 --seed0 42,1242 --assert-invariants
```

## 11. Implementation order and file-by-file change list (senior-engineer)

1. `tests/parity_v050/__init__.py` and `tests/parity_v050/capture.py` (new). Capture `golden.json` **before any engine edit**.
2. `sim/config.py`:
   - the §3.1 fields, after line 637;
   - `_validate_v051()`, after `_validate_v050()` (lines 1349-1371), called after line 809;
   - `v051()` / `v051_roster()`, after line 1327.
3. `sim/engine/state.py`: the §4.3 `PlayerState` fields (near line 384) and `GameState.green_cap_no_target` (near line 1548).
4. `sim/engine/vulnerability.py`:
   - `band_index` and `hit_landing` (§4.1);
   - `resolve_green` (§4.2);
   - the `_aegis_green_cancel` docstring: "Vulnerability still resets" becomes "still drops".
5. `sim/engine/phase2_compiler.py:258-268`: the Corruption counter (§6.1).
6. `sim/engine/core.py:551-555` and the `RoundTelemetry` dataclass: `green_cubes_cap_no_target` (§6.3).
7. `sim/engine/end_game.py`: `_v051_row` and its gated spread at line 375 (§6.2).
8. `sim/bots/vulnerability_policy.py:50-65`: `loss_if` (§5).
9. `web/controller/phase4_attack_actions.py`: `green_preview` (§7.1) and the log (§7.2).
10. `web/schemas.py`: the track view (§7.3) and `rules_version` (line 596).
11. `web/controller/core.py`: `WEB_DEFAULT_RULES_VERSION` and `_build_config` (§7.4).
12. `web/static/js/components/action_dock.js` and `compiler.js`: text only (§7.5).
13. `tests/test_v510_parity.py` and `tests/test_v510_green_landing.py` (new); `tests/test_v460_web.py` (version strings, §9.6).
14. `scripts/check_green_landing_port.py` (new, §9.8). It must PASS before the sweep runs.
15. `scripts/run_green_landing_sweep.py` (new, §10).

The doc and asset sync is not part of this spec's code. It comes after the sweep (plan §7 "Docs and assets", D5):
- the `v0.51.0` version bump, following the CLAUDE.md protocol;
- `RULES.md` lines 28 and 262–266, `RULES_QUICKREF.md` line 119, and the GLOSSARY "Green Cubes" entry;
- `pnp/generate_pnp.py` lines 73, 1299 and 1371, plus the band art ("→ 2 / → 5 / → 8"); then `python3 -m tts.build_tts`;
- the CLAUDE.md pillar text;
- `PLAN.md` and `FINDINGS.md`, with the residuals recorded as accepted.

## 12. Open questions (the defaults let implementation proceed)

- **Q1 (fractional `top` in `loss_if`):** §5 passes the float `top` to `hit_landing`, while the probe's aware arms truncated it with `int(top)`. This is a bot-only choice and does not affect S2H1 parity. Default: pass the float.
- **Q2 (scope of the one-hit rule):** in the engine the rule applies per Phase 4 Green resolution, which happens once per round (INV-VULN-07). Player-facing text says "each round" (plan §7). Because there is no other Green resolution, the two agree.
- **Q3 (web scope):** §7.5 includes the JS text strings ("reset to 0" in `action_dock.js` and `compiler.js`), which the brief did not list. If the web follow-up is meant to ship separately, steps 9–12 can move to that PR. The `rules_version` bump must then move with them.

### 12.1 Rulings (Main Agent, 2026-11-20)

- **Q1:** pass the float `top` (the default). The rule is bot-only and does not change S2H1 parity.
- **Q2:** confirmed. Player-facing text says "each round"; the engine applies the rule once per Phase 4 Green resolution.
- **Q3:** steps 9–12 (web controller, schemas, ruleset and JS text) stay in this change, together with the `rules_version` bump to `v0.51.0`. CLAUDE.md keeps the Web UI in sync with the rules.
