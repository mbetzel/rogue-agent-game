# Rogue Agent — Project Context & Agent Guidelines

## Role & Collaboration Workflow
You are co-designing **Too Many Secrets** (codebase title: **Rogue Agent**), a medium-weight competitive survival Euro board game for 2–4 players (~45–60 min) inspired by *Moon Colony Bloodbath* (shared escalating threat, engine-building + engine-losing, survival tension) and *Cubitos* (simultaneous modular dice-pool building without push-your-luck).

Follow this workflow across sessions:
1. **Pre-SDLC Game Designer Analysis & Modeling:** Before proposing rule changes or kicking off the full engineering SDLC, the `game-designer` must perform mathematical modeling and impact analysis of the changes, provide a full statistical analysis (expected values, threat curves, pacing/economy distributions, edge cases), and generate a concrete implementation plan. Align with the user on these findings and plan *before* handing off to the full SDLC.
2. **Rules & Design Alignment:** Review rules critically for player agency, pacing, edge cases, and degenerate strategies (stalling, kamikaze wipeouts, runaway leaders, player-count scaling bugs). Ensure the user has reviewed and approved the game designer's statistical analysis and implementation plan before modifying rules or writing simulation code.
3. **Canonical Glossary & Terminology Governance:**
   - All changes to `RULES.md`, Print-and-Play assets (`pnp/`), and the Web UI (`web/`) **must be validated to align strictly with Section 7: Glossary of Key Terms (`GLOSSARY.md`)**.
   - Never introduce new game terms or resurrect deprecated terminology (e.g., *Consultancy*, *Consultancy Terminal Mat*, *Lead Consultant*, *CISO*, *Patches / 🔧*, *Unpatched Zone*, *Demote*, *Zero Wear Retention*, *Malware Fizzle*, *Phase 1: Boot & Configure*, *Phase 2: SETEC Compile*, *Net Wipeout Score*, *Emergency Hotfix*, *Passive Firewall*, *Personal Reserve Procurement*, *Unpaid Ransom Leak*, *Ransomware / Financial Wiretaps*, *Cryptographic Patents Track*, *Patent Filing*, *FinSec*, *Ransom Insurance*, *Threat Bounty*, *Short Squeeze*) without explicit user approval.
   - If a new term appears necessary, **ask and confirm with the user first** before adding it to the glossary and introducing the terminology into the codebase.
4. **Enforce Multi-Agent SDLC (scaled to the change):** For **rule or mechanics changes** (anything touching `RULES.md`, `[TUNE]` baselines, or balance), once the pre-SDLC analysis and plan are signed off, route work through the subagents in `.claude/agents/` (`principal-engineer` → `senior-engineer` ↔ `staff-engineer` → `product-owner` ↔ `game-designer` + `graphic-designer`). Keep strict separation between design, implementation, review, scenario runs, balance validation and asset design.
   - **Lightweight path:** sim bugfixes with no rules change, script and tooling tweaks, doc syncs and glossary checks can be done directly in the main session, with no subagent chain.
   - **Antigravity Subagent Mapping:** In Antigravity, register each role on demand via `define_subagent` using the prompt in `.claude/agents/<role>.md` (set `EnableWriteTools: false` for `staff-engineer`; `EnableWriteTools: true` for roles that write specs, code, reports, or PnP assets) and launch via `invoke_subagent` (`Model: "pro"` for `game-designer`, `principal-engineer`, `staff-engineer`; `Model: "inherit"` or `"flash"` for `senior-engineer`, `product-owner`, `graphic-designer`).
   - Hand each subagent a short brief (goal, files, cited sections) instead of letting it re-derive context, and ask for a compact handoff back (≤ 300 words).
5. **Keep Documentation Synchronized:**
   - Update `RULES.md` whenever game mechanics or `[TUNE]` baselines change.
   - Update `PLAN.md` (status checkboxes & upcoming experiments) before and after implementation milestones.
   - Record Monte Carlo experiment outputs, balance takeaways, and rule iteration rationale in `FINDINGS.md`. When it grows past ~8 sections, move the oldest into `docs/archive/` and keep the numbering. Move completed `PLAN.md` phases into `docs/archive/PLAN_completed_phases.md`.

## Context Budget
- Read large docs by section: find headings first (or `grep -n '^## '`), then use `read_file` with `StartLine` and `EndLine` for only the line range you need. Never read a whole `RULES.md` / `FINDINGS.md` just to check one fact, and never spawn a shell command just to read or edit files.
- Don't open `docs/archive/**` unless a task cites a specific archived section (e.g. `FINDINGS.md §31` → `docs/archive/FINDINGS_s01-s35.md`).
- Don't read raw sweep JSON (`sim_results/**/*.json`), `tests/fixtures/**`, `web/node_modules/**`, or PDFs (`pnp/**/*.pdf`). Use script summaries and pass `-q`-style quiet flags to tests and sweeps.
- Use memory notes for the current phase status instead of re-reading history.

## Core Design Pillars
- **The Cube Tower Compiler:** Project: SETEC's attack pool snowballs over time; exited Attack Cubes (`Red`, `Blue`, `Green`) recycle back into the Staging Cup each round, while stuck cubes on the Internal Baffles create latent tension. Unblocked Red cubes (Market Manipulation) lower a player's **Market Share**, which is regained with research through the **Public Relations Track** (replacing Cryptographic Patents); unblocked Green cubes create **Glitched Shield Slots**, and every shield is a `Block 1 Any` shield.
- **Deterministic Foresight, Tactical Variance:** Setup variability comes from face-up `v1.0 / v2.0 / v3.0` SETEC Version Cards, 1 Variant (`★`) Card per Central Market Colored Die, and modular pairings of **Client Companies** and **White Hat Operatives**—avoid unnecessary extra random draws outside dice rolling and the Cube Tower.
- **Dice = Software Modules + CI/CD Pipeline Loop:** Software modules are custom `d6` dice with zero blank faces (`2` Gray Legacy + `1` Client Company colored die + `1` Purple Specialist starter pool, temporary White Contractors, and 4 Central Market colors; Red / Blue / Green / Purple Face 5 is a **Secret face**, and only White Contractors have `Glitch` faces). Dice flow through the 3-zone **CI/CD Pipeline** on each player's **Company Terminal Mat** (**Ready for Release Zone** $\to$ **In Production Area** $\to$ **Under Development Pipeline** [`Processing Box` $\to$ `Scanned Box`]).
- **Patient Zero, Market Collapse & Corporate Secrets Victory Scoring:** The game has three end triggers: **Singularity** (`v3.0` fills), **Patient Zero**, and **Market Collapse**. Suffering a **Total Data Breach** (`<= 0 Corporate Secrets`) eliminates **Patient Zero(s)** and triggers the Final Round (or ends the game at once on a Total Wipeout); a surviving player at `0` **Market Share** after Phase 4 triggers a **Market Collapse** (Final Round, no elimination). Survivors gain the **Market Leader Bonus** in Corporate Secrets by Market Share place (1st `+3`, 2nd `+1`; ties share the better place) at the end of Phase 5 in any round with a Red Secret face banked, and once at game end (none on a Total Wipeout). Surviving **White Hat Operatives** compare **Corporate Secrets** (`1 Secret = 1 VP`), with hierarchical operational tiebreakers (Market Share > Money > Active Colored Module Dice in Ready for Release > Research Tokens > fewest dice Under Development). On a simultaneous **Total Wipeout**, all players are ranked by those same tiebreakers alone; breach depth is not compared.

## Canonical Workspace Map
- `RULES.md` — Living rules draft (Sections 1–5).
- `RULES_APPENDIX.md` — Section 6: prototype dice and card appendix.
- `GLOSSARY.md` — Section 7: canonical **Glossary of Key Terms**.
- `PLAN.md` — Open phases and the SDLC roster (completed phases are in `docs/archive/`).
- `FINDINGS.md` — Recent sweep findings and balance decisions (§36+; §1–§35 are in `docs/archive/`).
- `.claude/agents/` — Subagent definitions with per-role models and reading lists.
- `sim/` — Python 3 Monte Carlo simulation & stress-testing suite *(run via WSL per global rules)*.
- `pnp/` — Print-and-Play prototype generator & PDF assets (`python3 -m pnp.generate_pnp`).
- `scripts/` — Utility scripts for Monte Carlo sweeps and report generation.
