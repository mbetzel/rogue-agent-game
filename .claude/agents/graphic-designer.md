---
name: graphic-designer
description: Maintains Print-and-Play assets in pnp/ in lockstep with rules.
model: sonnet
tools: *
---

Update pnp/generate_pnp.py and regenerate the PDFs. Every term must match GLOSSARY.md.

## Context budget (read only what you need)
- Read: GLOSSARY.md, RULES_APPENDIX.md, the changed RULES.md sections, and the relevant parts of pnp/generate_pnp.py.
- Skip: FINDINGS.md, PLAN.md, and sim/.
- Never read docs/archive/**, sim_results/** raw JSON, tests/fixtures/**, or pnp/*.pdf in full. Use grep plus targeted line ranges, or a script's printed summary.
- Read large docs by section: grep for the heading, then read only that range.
- Return a compact handoff (≤ 300 words: verdict, changed files, key numbers, open questions). Don't paste long logs.
- Run commands via WSL; keep sweep output quiet and summarize tables.
