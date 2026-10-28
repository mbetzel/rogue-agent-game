# Rogue Agent — Project Context & Agent Guidelines

## Role & Collaboration Workflow
You are co-designing **Rogue Agent**, a medium-weight competitive survival Euro board game for 2–4 players (~45–60 min) inspired by *Moon Colony Bloodbath* (shared escalating threat, engine-building + engine-losing, survival tension) and *Cubitos* (simultaneous modular dice-pool building without push-your-luck).

Follow this workflow across sessions:
1. **Rules & Design First:** Review rules critically for player agency, pacing, edge cases, and degenerate strategies (stalling, kamikaze wipeouts, runaway leaders, player-count scaling bugs). Align with the user on rule changes and plans *before* writing or modifying simulation code.
2. **Enforce Multi-Agent SDLC:** When building or running `sim/`, register and route work through the 5 specialized subagents defined in `PLAN.md` (`principal-engineer` → `senior-engineer` ↔ `staff-engineer` → `product-owner` ↔ `game-designer`), preserving strict separation between design, implementation, code review, scenario execution, and game-balance validation.
3. **Keep Documentation Synchronized:**
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
- `scripts/` — Utility scripts for Monte Carlo sweeps and report generation.
