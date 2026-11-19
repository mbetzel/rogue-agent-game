# Technical Spec: Red Target Lock Signature, "Lowest Rival Gains +2" (`v0.47.0`)

**Author:** principal-engineer
**Date:** 2026-11-19
**Status:** Approved for implementation (User decisions D-1..D-6, 2026-11-19).
**Source analysis:** `docs/findings/red_signature_lowest_rival_analysis.md` §1, §3, §7, §9.
**Amends:** `docs/specs/signature_cube_dominant_attacks_spec.md` `INV-SIG-RED`, `INV-SIMUL-RED` (the `v0.43`–`v0.46` text stays valid for the `"non_locked"` rule).
**Files touched (sim phase):** `sim/config.py`, `sim/engine/phase4_attack_resolution.py`, `sim/engine/state.py`, `sim/bots/base.py`, `tests/test_signature_dominant_attacks.py`. Phase B (docs, PnP, TTS, web) per §8.

---

## 1. Rule (D-1, D-3, D-4)

Card text: **"-2 Market Share; lowest rival gains +2 (2P: SETEC Corp counts)"**. No new glossary terms. SETEC Corp is named explicitly because it is not a "rival".

| | `v0.46.0` (`"non_locked"`) | `v0.47.0` (`"lowest_rival"`) |
|---|---|---|
| Locker | `-2` Market Share, floored at `0` | same |
| Recipient pool | surviving **non-locked** players | every surviving player **except the locker** (locked players are eligible), plus **SETEC Corp at 2P** |
| Recipient basis | post-drain | post-drain snapshot, one pool per locker |
| Gain | `+2`, cap `max_market_share` | `+2` per gift, summed per recipient, cap `20`. SETEC Corp gets `signature_red_setec_gain` (default `+2`, reserve `+1` = arm D1) |
| Fizzle | every survivor locked | only when the locker has no surviving rival and SETEC Corp is not active |
| Ties | locker chooses (bot hook) | same. The hook can now receive a SETEC sentinel. The default prefers SETEC |

Patient Zero players cannot receive a gift. They are also excluded from locking, as today.

## 2. Config contract (`sim/config.py`)

Add these after `signature_red_transfer_amount`:

```python
signature_red_recipient_rule: str = "non_locked"      # "non_locked" (v0.43-v0.46) | "lowest_rival" (v0.47)
signature_red_setec_eligible: bool = False            # 2P SETEC Corp joins the recipient pool (only if setec_corp_active)
signature_red_setec_gain: Optional[int] = None        # None -> signature_red_transfer_amount; 1 = arm D1 reserve
```

- **Validation (`__post_init__`):** `signature_red_recipient_rule` must be in `{"non_locked", "lowest_rival"}`, otherwise raise `ValueError`. `signature_red_setec_gain` must be `None` or an `int >= 0`. `signature_red_setec_eligible=True` combined with `"non_locked"` raises `ValueError`, because arm B is not a supported configuration.
- **Presets:**
  - `GameConfig.v047(**overrides)`: `setdefault("signature_red_recipient_rule", "lowest_rival")` and `setdefault("signature_red_setec_eligible", True)`, then `return cls.v046(**overrides)`.
  - `GameConfig.v047_roster(**overrides)`: the same `bot_pr_push` / `PrPushParams()` defaults as `v046_roster`, then `return cls.v047(**overrides)`.
- **Parity (INV-RSL-PARITY):** `v046()`, `v046_roster()` and every older preset keep the defaults above. Their code path and outputs must be byte-identical, with the same seeds giving the same game results and the same telemetry for pre-existing keys.

## 3. Algorithm (`_resolve_signature_red`, `phase4_attack_resolution.py:737`)

The signature gains an optional third argument: `_resolve_signature_red(engine, locked_players, breached_pids=frozenset())` (the call site passes `cr.breached_pids`; 2-arg callers still work). Wrappers must forward it. Dispatch on the rule:

```python
if cfg.signature_red_recipient_rule != "lowest_rival":
    return _resolve_signature_red_v046(engine, locked_players)   # current body, moved verbatim
```

`"lowest_rival"` path:

1. **Epoch 1, drain.** This is identical to the current Epoch 1, including `market_share_lost_red`, `market_share_min` and `signature_attacks_suffered["red"]`.
2. **Snapshot.** `snap = {p.player_id: p.market_share for p in survivors}`, where `survivors = [p for p in state.players if not p.is_patient_zero and p.market_share is not None]`. If `cfg.signature_red_setec_eligible and state.setec_corp_active`, also set `snap[SETEC_CORP_ID] = state.setec_market_share` (`SETEC_CORP_ID = -1` from `sim/engine/market_share.py`). The snapshot is taken once and is **not** updated between lockers.
3. **Per locker**, in `state.players` order (the order cannot affect results, because the snapshot is frozen and gains are applied in step 4):
   - `pool = [k for k in snap if k != locker.player_id]`. If the pool is empty, record a fizzle and `continue`.
   - `low = min(snap[k] for k in pool)` and `tied = [k for k in pool if snap[k] == low]`.
   - If `len(tied) == 1`, `chosen = tied[0]`. Otherwise call the hook (§4) with the `PlayerState` objects and the `SETEC_RECIPIENT` sentinel for the tied keys. If the hook returns an object that is not in the tied list, fall back to `default_signature_red_recipient_heuristic`.
   - `pending[chosen] += setec_gain if chosen == SETEC_CORP_ID else transfer_amt`.
   - `locker.signature_red_transfers_sent += <same amount>`.
4. **Epoch 2, apply.** For each `k` in `pending`:
   - Players: `p.market_share = min(p.max_market_share, p.market_share + pending[k])`. Update `market_share_peak` and increase `signature_red_transfers_received` by `pending[k]`, the uncapped nominal amount as today.
   - SETEC Corp: `state.setec_market_share = min(cfg.market_share_max or 20, state.setec_market_share + pending[k])`.
5. There are **no RNG draws** on either path. Phase 4 Step 5 (the SETEC `+1` on a Red exit) still runs afterwards with the same cap. `check_end_triggers_after_attacks` runs after both steps, so a gift that lifts a player off `0` prevents that round's Market Collapse.

Implementation notes (deviations from the draft above): `SETEC_CORP_ID = -1` is duplicated as a literal in `sim/bots/base.py` (importing `sim.engine.market_share` is circular; a test asserts they match). The pool helper runs before the drain and computes post-drain values itself. The v046 path adds `signature_red_events` and `signature_red_fizzles += len(locked_players)` only. Recipient eligibility also excludes `cr.breached_pids` (Phase 2 Patient Zeros); the v046 branch does not (parity).

## 4. Bot hook contract (`sim/bots/base.py`)

Add a module-level sentinel in `sim/bots/base.py` (or `sim/engine/market_share.py`, re-exported):

```python
@dataclass(frozen=True)
class SetecRecipient:
    player_id: int = SETEC_CORP_ID   # -1
    market_share: int = 0            # post-drain snapshot value
    secrets: int = 0                 # SETEC Corp scores no VP
    money: int = 0
    is_setec_corp: bool = True
```

Create one instance per call with the snapshot `market_share`. `SetecRecipient` exposes `player_id`, `market_share`, `secrets` and `money`, so legacy overrides that sort tied recipients by those attributes keep working. One example is the test bot in `tests/test_signature_dominant_attacks.py:47`.

- **`choose_signature_red_recipient(player, tied_recipients, game_state=None, **kwargs)`:** the signature is unchanged. The annotation widens to `List[Union[PlayerState, SetecRecipient]]` and the return type widens the same way. The docstring notes the sentinel and the D-3 default.
- **`default_signature_red_recipient_heuristic`:** if any tied entry has `is_setec_corp`, return it. Otherwise keep the existing `min(key=(secrets, money, player_id))`. With no sentinel present, the output is identical to `v046`, which preserves parity.
- **Snapshot read:** under `"lowest_rival"`, `tied_recipients` holds live `PlayerState`s whose `market_share` equals the snapshot value. Pending gifts have not been applied yet, so the live and snapshot values agree.

## 5. State and telemetry (`sim/engine/state.py`)

Add these to `GameState` (default `0`). `fast_clone` deep-copies them generically:

| Field | Meaning |
|---|---|
| `signature_red_events` | number of Red Signature resolutions, one per round in which it fires |
| `signature_red_gifts_to_locked` | gifts whose recipient was also locked |
| `signature_red_mutual_cancels` | locker pairs in which each gave the other its gift |
| `signature_red_fizzles` | lockers with an empty pool |
| `signature_red_setec_gifts` / `signature_red_setec_ms_gained` | gifts to SETEC Corp, and the Market Share it actually gained after the cap |
| `signature_red_capped_gains` | recipients whose gain was reduced by the cap |
| `signature_red_zero_rescues` | recipients at `0` in the snapshot who ended above `0` |

Existing per-player `signature_red_transfers_sent` / `_received` are unchanged. The `v046` path must also increment `signature_red_events` and `signature_red_fizzles`, so both arms report the same metrics. These are new keys, and pre-existing keys stay identical. `scripts/run_v046_sweep.py` (or the `v047` sweep wrapper) should print the counters per pod and the fizzle rate in its summary table.

## 6. Clone and web touchpoints

- **`sim/engine/fast_clone.py`:** this file contains no Phase 4 logic, only a generic copy (`_cp`, `clone_engine`). The RB-07 mirror is therefore **not needed**. The only check is a clone round-trip test showing that the new `GameState` fields survive.
- **`web/controller/phase4_attack_actions.py`** (Phase B, after the sweep):
  - `_SIG_EFFECTS["red"]` (`:33`): "lose 2 Market Share; the rival with the least Market Share gains 2 (2P: SETEC Corp counts)".
  - `_signature_choices` (`:94-101`): under `"lowest_rival"`, apply the same rule as the engine. Compute a post-drain preview (`max(0, ms - drain)` for each locked pid, keeping `pid != self`, and add `SETEC_CORP_ID` when it is eligible), then expose `red_recipients` only when more than one entry ties. Move the preview into a pure helper in `phase4_attack_resolution.py`, for example `red_signature_recipient_pool(state, cfg, locked_pids, breached_pids=frozenset()) -> Dict[int, int]` (pure; returns the post-drain snapshot of all recipients incl. the locker and SETEC when eligible; a locker's pool is that dict minus its own id), which both the engine and the web layer call. This prevents drift between them.
  - `_human_signature_hooks._pick` (`:248`): match on `getattr(p, "player_id", None) == _r`, so `-1` selects the sentinel.
  - The submit validation at `:394-398` accepts `-1` when it is offered. `web/static/js/components/action_dock.js:708` labels pid `-1` as "SETEC Corp".

## 7. Invariants (v2)

- **INV-SIG-RED v2:** Under `"lowest_rival"`, each surviving Target-Locked player loses `min(2, MS)`. Then exactly one recipient per locker is drawn from `{surviving players} \ {locker}`, plus `{SETEC Corp}` when `setec_eligible && setec_corp_active`. That recipient has the least snapshot Market Share. If several tie, the locker chooses, and the default chooses SETEC. The recipient gains `transfer_amt` (or `setec_gain`), capped at `20`. Patient Zero is never a recipient. A gift fizzles only when the pool is empty. At 2P with SETEC active, the pool is never empty.
- **INV-SIMUL-RED v2:** Every drain happens before any recipient is chosen. Every recipient is chosen from one frozen post-drain snapshot. All gains are summed and then applied together, with a single cap per recipient. Results do not depend on seat order or on the order of `locked_players`. Two lockers that are each other's lowest rival both end at net `0` (mutual cancel).
- **INV-RSL-PARITY:** With `signature_red_recipient_rule == "non_locked"`, behaviour matches `v0.46.0` bit for bit, including when the default heuristic is called with no sentinel.
- **INV-RSL-ORDER:** Red Signature gains are applied before Phase 4 Step 5 (SETEC `+1`) and before the Market Collapse check.

## 8. Test specification (`tests/test_signature_dominant_attacks.py`)

TC-SIG-07, -08 and -09 stay as they are, pinned to `v046` (`"non_locked"`). The new cases use `GameConfig.v047()` and set state directly.

| ID | Setup | Expected | Invariant |
|---|---|---|---|
| TC-SIG-07b | 3P. A and B locked. MS: A 10, B 5, C 6 | Post-drain A 8, B 3, C 6. A's lowest rival is B, so B gets +2 and ends at 5. B's lowest rival is C (6) rather than A (8), so C ends at 8. Final MS: A 8, B 5, C 8 | INV-SIG-RED v2 |
| TC-SIG-07c | 3P. A and B locked. MS: A 6, B 6, C 12 | Post-drain 4 / 4 / 12. Each locker's lowest rival is the other, so A ends at 6, B at 6 and C at 12. `mutual_cancels == 1` | INV-SIMUL-RED v2 |
| TC-SIG-07d | 3P. A locked at MS 0. B 7, C 9 | A stays at 0, `market_share_lost_red += 0`, and B gets +2 to reach 9 | INV-SIG-RED v2 |
| TC-SIG-07e | The case from 07b with `locked_players` reversed | Identical final state | INV-SIMUL-RED v2 |
| TC-SIG-08b | 2P, SETEC active at MS 6. A locked at 8, B 6 | Post-drain: A 6. The tie is {B, SETEC}. The hook receives a `SetecRecipient` (pid -1, MS 6). The default picks SETEC, so SETEC goes to 8 and B stays at 6. A spy hook that picks B gives B 8 | INV-SIG-RED v2 |
| TC-SIG-08c | 2P. SETEC at MS 19, the lowest. A locked | SETEC ends at 20 (capped), `capped_gains == 1`. With `signature_red_setec_gain=1`, starting from SETEC at 3, SETEC reaches 4 | INV-SIG-RED v2 |
| TC-SIG-08d | 3P. A and B locked. MS: A 2, B 8, C 9. Full Phase 4 run | A drains to 0, then B's gift lifts A to 2. There is no Market Collapse that round and `zero_rescues == 1` | INV-RSL-ORDER |
| TC-SIG-08e | 3P. B is Patient Zero (MS 1). A locked at 9, C 12 | C gets +2 and B is never chosen. Variant: with both rivals Patient Zero, A drains, there is no gift, and `fizzles == 1` | INV-SIG-RED v2 |
| TC-SIG-08f | Parity: fixed seeds 42..61, 2P/3P/4P with `v046_roster` | Results and pre-existing telemetry equal the recorded `v046` digests | INV-RSL-PARITY |
| TC-SIG-08g | Config: `"lowest_rival"` with `v047()` defaults. Also `"non_locked"` with `setec_eligible=True`, and an unknown rule | Preset fields set correctly. The second and third raise `ValueError` | §2 |

Run the full suite quietly (`python3 -m pytest -q`) through WSL.

## 9. Acceptance criteria

1. All tests pass, including TC-SIG-07..09 unchanged and the new cases above. `v046` parity digests are unchanged.
2. **Confirm sweep (D-6):** 4,000 games per pod (2P/3P/4P), `v047_roster` vs `v046_roster`, `mixed1` roster, seeds `42..`. Results should fall within the analysis bands, at about `±1.4×CI`:
   - 2P fizzle rate `0%` and SETEC share of gifts about `56%`;
   - 3P/4P Market Collapse rate `13–15%` and Singularity `23–27%`;
   - about `+0.3` rounds;
   - 2P archetype spread about `16.3`.
3. **Watch item (D-6):** the 4P archetype spread rises by about `+2.7` (SecOps / Reckless). Report it, but it does not block release unless the rise exceeds `+4`.
4. game-designer sign-off and **FINDINGS §63**, then the Phase B sync:
   - Docs: `RULES.md:279`, `RULES_QUICKREF.md:129`, `GLOSSARY.md:33`.
   - PnP: `pnp/generate_pnp.py:1412,:1913`.
   - Web: §6.
   - Rebuild: `python3 -m tts.build_tts` and `--check`.
   - Version: the full `v0.47.0` version-sync list from CLAUDE.md.
