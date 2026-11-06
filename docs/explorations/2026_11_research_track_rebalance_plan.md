# Research Track Rebalance — Pre-SDLC Design Plan (`v0.35.0` candidate)

Status: design locked with User 2026-11-05. Engineering not started.

## 1. Problem

Measured on the v0.34.0 engine (900 games, 2–4P, Adaptive / SecOps / Venture / Accelerationist bots):

- Research income: **~4 🔬 per player per game** (median 4, p10–p90 1–7), mean 8.7 rounds.
- End-state levels (4P, including company starting levels): Patents L0 90%, Triage L0 96%, Defense L2 0%, Release L2 4%.
- Theoretical ceiling for the 3 Gray + 1 Purple starter pool, all dice to Income: ~1.17 🔬/round (~10/game).

The tracks are under-used because players cannot afford them, not only because the rewards are flat.

## 2. Locked design

### 2.1 Tracks (5 levels, L0–L4, identical for all players)

Step costs (L0→1, 1→2, 2→3, 3→4): **1 / 2 / 2 / 3 🔬** `[TUNE]` (8 🔬 per track, 32 for all four).

| Track | L0 | L1 (Breakthrough) | L2 | L3 (Breakthrough) | L4 |
|---|---|---|---|---|---|
| Defense Grid | Defense Capacity 2 | Gain 1 Gray die | Capacity 3 | Gain 1 Secret | Capacity 4 + `+$1` in Phase 4 if no unblocked Attack Cubes hit you |
| Triage | Triage Bandwidth 2 | 2 White Contractors → Ready for Release | Bandwidth 3 | Swap a colored die with the Market | Bandwidth 4 + `+1 🔬` per die moved in Conveyor Triage beyond the 2nd |
| Release | Release Bandwidth 4 | Gain 1 Gray die | Bandwidth 5 | Gain 1 Secret | Bandwidth 6 + 1 extra free reroll in Phase 1 Step 4 |
| Cryptographic Patents | File 2 🔬 → 1 Secret | Gain $3 | File 3 🔬 → 2 Secrets | Unlock 2nd Purple die | File 1 🔬 → 1 Secret |

- **Breakthrough** (new glossary term, rules-reference only, not printed on the track): a one-time effect gained immediately on reaching L1 or L3.
- "Gain 1 Secret" is a flat +1 Secret.
- The L2 specials Emergency Hotfix and Passive Firewall are **removed** (glossary entries retired).
- Track names stay as in the glossary.

### 2.2 Client Companies

- Every company starts at L0 on all four tracks.
- Removed: Omnidyne Triage/Release L1 and Def Cap 1; Aegis Def Cap 3 and Triage 1 / Release 3; Helix Patent L1 and +2 🔬; Prometheus −1 🔬 upgrade discount.
- Helix and Prometheus are expected to need replacement bonuses that don't involve research. These get sized from sim results and need User approval.

### 2.3 Patents rate check (12 🔬 budget; 14 🔬 in brackets)

| Plan | Secrets | Extras |
|---|---|---|
| Stay L0 | 6 (7) | — |
| L2 (3 🔬) | 6 (7.3) | $3 |
| L4 (8 🔬) | 4 (6) | $3 + 2nd Purple |

## 3. Open items for the game-designer sweep

1. **Research income lever:** the target is 12–14 🔬/game. Levers: more 🔬 faces on Gray/Purple, and research-aware bot policies. A flat per-round grant would need a new term (User approval).
2. **Breakthrough definitions to pin down in the spec:**
   - Gray die placement (Ready for Release assumed).
   - "Unlock 2nd Purple die": a free die, or only access to buy one?
   - Swap mechanics: which die, cost difference, where the swapped die goes.
3. Helix and Prometheus replacement bonuses.

## 4. Guardrails (sweep acceptance)

- Typical player: 1 track at L4 and 2–4 other steps. No player completes all tracks.
- No single track is maxed in more than ~50% of the seats that max a track.
- Round pacing, Singularity rate and Patient Zero rate within the v0.34.0 D5 guardrails.
- Final Secret totals: no inflation beyond what the guardrails allow (risk: Patents L0 at 2:1).

## 5. SDLC routing

game-designer sweep → principal-engineer spec → senior-engineer ↔ staff-engineer → product-owner telemetry ↔ game-designer sign-off → graphic-designer (mat tracks, Breakthrough references). Docs: `RULES.md` (Sections 2/3/6/7, Client Company table), `PLAN.md`, `FINDINGS.md`.

Dependency: Phase 42 (v0.34.0) telemetry and sign-off are still open. The baseline numbers above come from the v0.34.0 engine.

## 6. Sweep decisions (User, 2026-11-05)

Source: [docs/findings/v350_research_income_sweep.md](../findings/v350_research_income_sweep.md). These supersede Sections 2–3 where they differ.

1. **Gray Legacy die faces `[TUNE]`:** `Block 1 Any ×2, +$1 & +1 🔬, +$1 / +1 🔬 ×2, +1 🔬`. Purple faces unchanged. Target ~12 🔬 per player per game.
2. **2P Singularity ~45%:** accepted.
3. **No limit on end-of-game Secrets.** Secrets are how you win. Only clearly broken strategies get addressed (watch item: Patents is 58% of maxed tracks when bots favor certain tracks).
4. **Purple dice can no longer be purchased.** Players start with 1 Purple die. Patents L3 Breakthrough grants the 2nd Purple die, placed in Ready for Release. No fallback needed.
5. **Triage L3 Breakthrough:** pay `$3` `[TUNE]` to replace 1 Gray Legacy die with a Central Market colored die of your choice, placed in Ready for Release. The Market swap is dropped.
6. **Breakthrough Gray die** (Defense L1, Release L1) goes to Ready for Release.
7. **All Client Company setup bonuses are removed** (including Meridian `+$2` cash and DTO `+1` Secret). Every company starts with the same money, Secrets, 🔬 and L0 tracks. Institutional Overrides are unchanged except item 8. Company identity is to be revisited in a later phase.
8. **DTO Slush Fund becomes once per game** (instead of once per version).
9. **Defense L4 capstone:** `+$1` per Attack Cube blocked in Phase 4, max `$3` `[TUNE]` (replaces the "no unblocked cubes" condition).
10. **Research-aware bot policy** from `scripts/investigate_v350_research_sweep.py` is ported into `sim/bots`.
