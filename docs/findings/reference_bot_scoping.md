# Reference Bot — Pre-SDLC Scoping (game-designer)

Date: 2026-11-07 · Status: **approved by User 2026-11-07** · Scope: `sim/` only (no `RULES.md`, `web/`, `pnp/` changes; no new game terms)

## 1. Problem

The archetype bots (`Accelerationist`, `AdaptiveBalanced`, `RecklessSaboteur`, `SecOpsTurtle`, `VentureGreed`) are scripted. Recent work shows the cost:

- Repeated false flags later traced to bot behavior (`FINDINGS.md` §33–§34: broken VentureGreed, Release Track 68–72% vs 33–35% random focus, Public Relations 60% focus artifact).
- Every rule probe needs a hand-written "aware" heuristic (top-off-aware §36, "never be last" §37, bonus time weights 0.3/0.6/1.0 §38). Results measure the heuristic as much as the rule; §37 says so explicitly.
- "Blue-first always" (§36) and "Public Relations-first loses" (§38) are stated as design facts but were never challenged by a player that searches.

Goal: one **reference bot** that plays reasonably well without hand-coding for each mechanic, used as the "competent player" check on every balance question.

## 2. Measured engine cost (this session, WSL, 8 cores)

| Pod | ms / full game | Avg rounds |
|---|---|---|
| 2P | 3.5 | 9.2 |
| 3P | 4.7 | 8.7 |
| 4P | 6.1 | 8.8 |

`copy.deepcopy(GameEngine)` mid-game: ~2.3 ms, and the clone runs to completion without touching the original. Rollout search is affordable without engine changes.

## 3. Proposed design: two tiers

**Revision 2026-11-07 (User):** 15 min/pod was too slow. The plan is now two tiers. Timings below are estimates from §2 costs and still need confirming.

| Tier | Bot | Cost | Used for |
|---|---|---|---|
| 1 | **Mixed bot** — each decision handed to a randomly drawn archetype policy (seeded, per decision type) | ~5 ms/game (normal speed) | Every sweep, as a roster seat; breaks fixed focus orders (§33–§34 artifacts) |
| 2 | **Fast search bot** — policy-portfolio rollouts, below | ~1.2 s/game, **~1.5 min per 600-game pod** | Strength gate and targeted questions (§36 Blue-first, §37 lock, §38 Public Relations-first) |

Later option: if the search bot keeps winning with a recognizable pattern, write that pattern into a fixed policy that runs at normal speed.

### Tier 2 search

At each key decision the reference seat:

1. **Builds candidates** from what each existing policy would do in this state (the 5 archetypes + `MarketSharePolicy` + `ResearchPolicy` variants), deduplicated. Typically 3–6 distinct options. This avoids enumerating the full action space and reuses legal-move logic already tested.
2. **Rolls out** each candidate N times on a deep-copied engine, with every seat (including itself) played by its default policy from then on.
3. **Scores** each rollout as its final Corporate Secrets minus the best rival's (Patient Zero = large negative), plus a small win bonus. Picks the best mean.

Searched decisions: Phase 4 shield allocation (which cubes to block) and Phase 6 operations spending (dice, tracks, Public Relations regain), **only when candidates disagree**. Everything else falls back to `AdaptiveBalanced`.

### Speed levers (all `[TUNE-BOT]`)

| Lever | Speed-up |
|---|---|
| Search only disagreeing Phase 4 / Phase 6 decisions (~26 → ~10 per game) | ~2.5× |
| Drop weak candidates early: 4 rollouts each, drop worst half, finish the rest | ~2× |
| N = 8 rollouts with shared seeds across candidates | ~2× |
| Hand-written state clone in place of `deepcopy` (parity-tested) | ~1.5–2× |

Budget: ~10 decisions × ~4 candidates × ~6 effective rollouts × ~5 ms ≈ **1.2 s/game**, ~1.5 min per 600-game pod on 8 processes (was 10–13 s/game, ~15 min).

Held in reserve: stop rollouts at the end of the current Version and score the position (~3× more, ~30 s/pod). Needs a position-scoring function, which adds hand-tuning back, so use it only if Tier 2 is still too slow.

### Correctness requirements (invariants for the spec)

- **INV-REF-RNG-01 (no clairvoyance):** each clone's `rng` is reseeded from a rollout seed. A plain deepcopy carries the live RNG and would reveal the real future dice and tower drops. This is the main correctness trap.
- **INV-REF-CRN-01:** all candidates at one decision share the same rollout seeds (common random numbers) to cut noise.
- **INV-REF-NEST-01:** the reference seat inside a rollout uses its fallback policy (no recursive search).
- **INV-REF-DET-01:** same match seed gives an identical game. Needs an audit for any bot or engine use of the global `random` module.
- **INV-REF-PARITY-01:** games without a reference seat stay bit-identical (v0.36 parity fixtures in `tests/fixtures/v036_parity/`).
- Hidden info: no meaningful hidden state found. Stuck tower cubes can be deduced from cubes in minus exited, so the clone may see them.

## 4. Validation plan

0. **Timing check:** confirm Tier 2 ≤ ~2 min per 600-game pod and Tier 1 at normal speed. Re-run the v0.36 baseline with one Mixed seat and record shifts.
1. **Strength gate:** one reference seat vs archetypes must beat fair share clearly (target ≥ +10 points at 3P, 1,200 games). If it fails, raise N / candidates before trusting any conclusion.
2. **Re-test open conclusions:** Blue-first (§36), the Market Share relative lock (§37), the placement bonus and Public Relations-first (§38), against 1 and all-reference seats.
3. **Artifact check:** compare Release / Public Relations concentration under the reference bot vs the archetype focus orders.
4. Report in `FINDINGS.md` as a new section.

## 5. Cleanup (in scope, low risk)

Delete archetype methods for removed mechanics (`choose_debug_unlocks`, `choose_hotfix_rerolls`, `choose_fast_patches` and others; `choose_yahtzee_rerolls` is live, see spec) where only `legacy_v033` paths still call them. Verify with parity fixtures first; keep them if legacy parity needs them.

## 6. Out of scope

Parameterizing archetype focus orders with self-play tuning (follow-up, once the reference bot exists to tune against). Any rules change.

## 7. Decisions for the User

1. ~~Value function~~ — resolved: Secrets margin + win bonus.
2. ~~Compute budget~~ — resolved: two tiers, Tier 2 target ~1.5 min/pod.
3. ~~Cleanup~~ — resolved: include, guarded by parity fixtures.

## 8. Implementation plan (after sign-off)

`principal-engineer` spec (`docs/specs/reference_bot_spec.md`) → `senior-engineer` builds `sim/bots/mixed_policy.py` (Tier 1), `sim/bots/reference_search.py` (Tier 2), a fast state clone, and a multiprocess sweep runner `scripts/run_reference_bot_check.py` + tests → `staff-engineer` review → `product-owner` runs §4 → `game-designer` assessment. Update `PLAN.md` with a new phase entry.
