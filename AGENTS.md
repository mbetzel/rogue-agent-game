# Rogue Agent — Project Context & Agent Guidelines

## Role & Collaboration Workflow
You are co-designing **Rogue Agent**, a medium-weight competitive survival Euro board game for 2–4 players (~45–60 min) inspired by *Moon Colony Bloodbath* (shared escalating threat, engine-building + engine-losing, survival tension) and *Cubitos* (simultaneous modular dice-pool building without push-your-luck).

Follow this workflow across sessions:
1. **Pre-SDLC Game Designer Analysis & Modeling:** Before proposing rule changes or kicking off the full engineering SDLC, the `game-designer` must perform mathematical modeling and impact analysis of the changes, provide a full statistical analysis (expected values, threat curves, pacing/economy distributions, edge cases), and generate a concrete implementation plan. Align with the user on these findings and plan *before* handing off to the full SDLC.
2. **Rules & Design Alignment:** Review rules critically for player agency, pacing, edge cases, and degenerate strategies (stalling, kamikaze wipeouts, runaway leaders, player-count scaling bugs). Ensure the user has reviewed and approved the game designer's statistical analysis and implementation plan before modifying rules or writing simulation code.
3. **Enforce Multi-Agent SDLC:** Once pre-SDLC design analysis and the implementation plan are signed off by the user, route engineering work through the specialized subagents defined in `PLAN.md` (`principal-engineer` → `senior-engineer` ↔ `staff-engineer` → `product-owner` ↔ `game-designer` + `graphic-designer`), preserving strict separation between design, implementation, code review, scenario execution, game-balance validation, and physical asset design.
4. **Keep Documentation Synchronized:**
   - Update `RULES.md` whenever game mechanics or `[TUNE]` baselines change.
   - Update `PLAN.md` (status checkboxes & upcoming experiments) before and after implementation milestones.
   - Record Monte Carlo experiment outputs, balance takeaways, and rule iteration rationale in `FINDINGS.md` (create when running the first test suite).

## Core Design Pillars
- **The Cube Tower Compiler:** The Rogue Agent's attack pool snowballs over time; exited Attack Cubes (`Red`, `Blue`, `Green`) recycle back into the Staging Cup each round, while stuck cubes create latent tension.
- **Deterministic Foresight, Tactical Variance:** Setup variability comes from face-up `v1.0 / v2.0 / v3.0` Rogue Agent cards and 1 Variant (`★`) card per Colored Die—avoid unnecessary extra random draws outside dice rolling and the Cube Tower.
- **Dice = Modules + Wear Loop:** Software modules are custom `d6` dice with zero blank faces (Starter Gray + 5 purchasable colors). Dice that actively block attacks wear down into the player's **Unpatched Zone** until repaired.
- **Patient Zero & Portfolio Scoring:** Hitting Insolvency (`< $0`) or Total Breach (`<= 0 Secrets`) triggers immediate game end and eliminates Patient Zero(s); surviving corporations compare Portfolio Value (with continuous overflow penalties only on a simultaneous total wipeout).

## Canonical Workspace Map
- `RULES.md` — Living rules draft and prototype component/card appendix.
- `PLAN.md` — Active simulation architecture, experiment matrix, and milestone checklist.
- `FINDINGS.md` — Historical log of simulation sweeps and balance decisions *(created once first experiments run)*.
- `sim/` — Python 3 Monte Carlo simulation & stress-testing suite *(run via WSL per global rules)*.
- `pnp/` — Print-and-Play prototype generator & PDF assets (`python3 -m pnp.generate_pnp`).
- `scripts/` — Utility scripts for Monte Carlo sweeps and report generation.
