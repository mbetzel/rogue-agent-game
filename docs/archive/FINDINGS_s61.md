# Rogue Agent — Archived Findings §61 (v0.45.0 baseline)

Moved from `FINDINGS.md` in Phase 73 (2026-11-25). Numbering is unchanged.

---

## 61. Phase 66 Post-Telemetry Balance Assessment: Glitched Shield Slots Rework, 2P SETEC Corp, Starting Secrets, & WS-OPERATOR (`v0.45.0 Baseline`): APPROVED

**Experiments:** `scripts/run_v045_sweep.py` (`sim_results/v045_telemetry_report.md`, 6,000 paired games: 1,000/pod/variant across 2P/3P/4P, seeds `42..1041`).

### Key Changes (`v0.45.0` vs `v0.44.0`)
1. **Glitched Shield Slots Rework (`Defense Grid Overflow`):** Each Shield Slot holds up to `2` Green cubes (distributed evenly); `1` Shield purges all Green cubes in `1` slot in Phase 4; a `3rd` Green cube triggers **Defense Grid Overflow** (`-1` Corporate Secret).
2. **2P SETEC Corp Neutral Black Cube:** Strictly 2P; starts at `0` Market Share, gains `+1` in Phase 4 whenever `>= 1` Red cube exits the tray (cap `20`), and ranks normally in the Market Leader Bonus (`+3`/`+1`), immune to Market Collapse and Patient Zero.
3. **Starting Corporate Secrets:** Unified at **`4`** across all player counts (`2P`, `3P`, `4P`).
4. **The Operator (`WS-OPERATOR`) & Card Text Sync:** `+1 🔬` per different color die in Scanned Box (all colors including Gray, Purple, Yellow; `0` base); `COMP-MERIDIAN` cleaned; all die abilities confirmed in Phase 3.

### Telemetry & Balance Verdict (`PASS`)
- **Pacing & Endings (2P / 3P / 4P):** Mean rounds `7.47 / 6.92 / 6.65` (vs `7.19 / 7.42 / 7.08`); `v1.0` breach rate `11.0% / 20.4% / 24.3%` (2P cut nearly in half from `19.2%`); Total Wipeout `12.6% / 4.8% / 1.1%` (all under `< 15%` guardrail).
- **Defense Grid Overflow:** `55.1%–57.8%` of games trigger overflow (`2.83 / 3.43 / 3.70` events/game), raising final Green slot utilization from `40.1%–41.2%` to **`60.7%–67.2%`**.
- **2P SETEC Corp:** Mean final MS **`6.33`** (1st: `44.0%`, 2nd: `18.1%`, 3rd: `37.9%`); humans retain **`85.9%`** of Market Leader Bonus Secrets while Market Collapse remains active at `34.1%`.
- **WS-OPERATOR Parity:** Win rates `46.9%` (2P), `35.7%` (3P), `23.0%` (4P), yielding `1.11–1.20 🔬` per trigger.
- **Watch Item:** 3P/4P Patient Zero rises to `74.5% / 78.0%` (`6.92 / 6.65` rounds); if physical playtesting feels fragile in 3P/4P, a `[TUNE]` to `5` Starting Secrets (3P/4P only) is a clean follow-up lever.
