# Rogue Agent — Project Context & Agent Guidelines

## Role & Collaboration Workflow
You are co-designing **Too Many Secrets** (codebase title: **Rogue Agent**), a medium-weight competitive survival Euro board game for 2–4 players (~45–60 min) inspired by *Moon Colony Bloodbath* (shared escalating threat, engine-building + engine-losing, survival tension) and *Cubitos* (simultaneous modular dice-pool building without push-your-luck).

Follow this workflow across sessions:
1. **Pre-SDLC Game Designer Analysis & Modeling:** Before proposing rule changes or kicking off the full engineering SDLC, the `game-designer` must perform mathematical modeling and impact analysis of the changes, provide a full statistical analysis (expected values, threat curves, pacing/economy distributions, edge cases), and generate a concrete implementation plan. Align with the user on these findings and plan *before* handing off to the full SDLC.
2. **Rules & Design Alignment:** Review rules critically for player agency, pacing, edge cases, and degenerate strategies (stalling, kamikaze wipeouts, runaway leaders, player-count scaling bugs). Ensure the user has reviewed and approved the game designer's statistical analysis and implementation plan before modifying rules or writing simulation code.
3. **Canonical Glossary & Terminology Governance:**
   - All changes to `RULES.md`, Print-and-Play assets (`pnp/`), and the Web UI (`web/`) **must be validated to align strictly with Section 7: Glossary of Key Terms in `RULES.md`**.
   - Never introduce new game terms or resurrect deprecated terminology (e.g., *Consultancy*, *Consultancy Terminal Mat*, *Lead Consultant*, *CISO*, *Patches / 🔧*, *Unpatched Zone*, *Demote*, *Zero Wear Retention*, *Malware Fizzle*, *Phase 1: Boot & Configure*, *Phase 2: SETEC Compile*) without explicit user approval.
   - If a new term appears necessary, **ask and confirm with the user first** before adding it to the glossary and introducing the terminology into the codebase.
4. **Enforce Multi-Agent SDLC:** Once pre-SDLC design analysis and the implementation plan are signed off by the user, route engineering work through the specialized subagents defined in `PLAN.md` (`principal-engineer` → `senior-engineer` ↔ `staff-engineer` → `product-owner` ↔ `game-designer` + `graphic-designer`), preserving strict separation between design, implementation, code review, scenario execution, game-balance validation, and physical asset design.
5. **Keep Documentation Synchronized:**
   - Update `RULES.md` whenever game mechanics or `[TUNE]` baselines change.
   - Update `PLAN.md` (status checkboxes & upcoming experiments) before and after implementation milestones.
   - Record Monte Carlo experiment outputs, balance takeaways, and rule iteration rationale in `FINDINGS.md`.

## Core Design Pillars
- **The Cube Tower Compiler:** Project: SETEC's attack pool snowballs over time; exited Attack Cubes (`Red`, `Blue`, `Green`) recycle back into the Staging Cup each round, while stuck cubes on the Internal Baffles create latent tension.
- **Deterministic Foresight, Tactical Variance:** Setup variability comes from face-up `v1.0 / v2.0 / v3.0` SETEC Version Cards, 1 Variant (`★`) Card per Central Market Colored Die, and modular pairings of **Client Companies** and **White Hat Operatives**—avoid unnecessary extra random draws outside dice rolling and the Cube Tower.
- **Dice = Software Modules + CI/CD Pipeline Loop:** Software modules are custom `d6` dice with zero blank faces (`3` Gray Legacy + `1` Purple Specialist starter pool, temporary White Contractors, and 4 Central Market colors). Dice flow through the 3-zone **CI/CD Pipeline** on each player's **Company Terminal Mat** (**Ready for Release Zone** $\to$ **In Production Area** $\to$ **Under Development Pipeline** [`Glitched Box` $\to$ `Scanned Box`]).
- **Patient Zero & Corporate Secrets Victory Scoring:** Suffering a **Total Data Breach** (`<= 0 Corporate Secrets`) triggers immediate game end and eliminates **Patient Zero(s)**; surviving **White Hat Operatives** compare **Corporate Secrets** (`1 Secret = 1 VP`), with hierarchical operational tiebreakers (or **Net Wipeout Score** based on least negative breach depth on a simultaneous total wipeout).

## Canonical Workspace Map
- `RULES.md` — Living rules draft, prototype component/card appendix, and canonical **Section 7: Glossary of Key Terms**.
- `PLAN.md` — Active simulation architecture, experiment matrix, and milestone checklist.
- `FINDINGS.md` — Historical log of simulation sweeps and balance decisions.
- `sim/` — Python 3 Monte Carlo simulation & stress-testing suite *(run via WSL per global rules)*.
- `pnp/` — Print-and-Play prototype generator & PDF assets (`python3 -m pnp.generate_pnp`).
- `scripts/` — Utility scripts for Monte Carlo sweeps and report generation.
