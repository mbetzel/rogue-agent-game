---
name: sdlc-subagents
description: >-
  Runbook for invoking the 6-subagent SDLC pipeline (game-designer,
  principal-engineer, senior-engineer, staff-engineer, product-owner,
  graphic-designer) in Antigravity using the role definitions and context
  budgets in .claude/agents/*.md. Activate when executing a multi-agent SDLC
  cycle for rule, [TUNE], or balance changes.
---

# Rogue Agent 6-Subagent SDLC in Antigravity

When routing work through the 6-subagent SDLC defined in `PLAN.md` Section 2 and `.claude/agents/*.md`, use Antigravity's `define_subagent` and `invoke_subagent` tools with the role mappings below.

## Role Mapping Table

| Subagent Name | `.claude/agents/` File | `EnableWriteTools` | Recommended `Model` | Scope Summary |
| :--- | :--- | :--- | :--- | :--- |
| `game-designer` | `.claude/agents/game-designer.md` | `true` | `"pro"` | Pre-SDLC math modeling, statistical analysis, and post-telemetry balance validation. |
| `principal-engineer` | `.claude/agents/principal-engineer.md` | `true` | `"pro"` | Writes technical architecture spec under `docs/specs/` only. Does not edit `sim/`. |
| `senior-engineer` | `.claude/agents/senior-engineer.md` | `true` | `"inherit"` | Implements `sim/` features, bots, scripts, and unit tests to spec. Never self-approves. |
| `staff-engineer` | `.claude/agents/staff-engineer.md` | `false` | `"pro"` | Independent code and rules-fidelity review (`APPROVED` or `CHANGES_REQUESTED` with `file:line`). |
| `product-owner` | `.claude/agents/product-owner.md` | `true` | `"inherit"` | Runs Monte Carlo sweeps via WSL and writes compact telemetry reports. Never edits engine code. |
| `graphic-designer` | `.claude/agents/graphic-designer.md` | `true` | `"inherit"` | Updates `pnp/generate_pnp.py` and regenerates PDFs in lockstep with `GLOSSARY.md` and `RULES.md`. |

## Invocation Rules (Token & Context Budget)

1. **Define Once Per Conversation**: Before invoking a role for the first time in a conversation, read its `.claude/agents/<role>.md` file and call `define_subagent` with its system prompt and `EnableWriteTools` setting above.
2. **Short Briefs Only**: Pass a concise `Prompt` to `invoke_subagent` naming the goal, exact file paths, and specific `RULES.md` / `FINDINGS.md` section numbers (`§`) so the subagent does not re-derive context.
3. **Compact Handoffs**: Every subagent must return a compact handoff (`<= 300` words: verdict, changed files, key numbers, open questions) without pasting raw logs or JSON dumps.
4. **Lightweight Path Bypass**: Sim bugfixes with no rules change, script/tooling tweaks, doc syncs, and glossary checks run directly in the main session without launching subagents.
