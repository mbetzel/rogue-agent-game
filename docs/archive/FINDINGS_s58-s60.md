# Rogue Agent — Archived Findings §58 and §60 (v0.44.0 baselines)

Moved from `FINDINGS.md` in Phase 72 (2026-11-20). Numbering is unchanged; §59 was never assigned.

---

## 60. Phase 65 Post-Telemetry Balance Assessment: Colored Die F6 Variant Overhaul & Glitched Shield Slot Flow: APPROVED (`v0.44.0 Baseline`)

Sources: `docs/findings/v044_f6_overhaul_sweep.md` (1,800-game v0.44.0 vs v0.43.0 sweep across 2P/3P/4P, seeds `42..341`); `docs/specs/f6_variant_overhaul_spec.md`; `docs/plans/f6_overhaul_gd_plan.md`.

- **Design Changes (`v0.44.0 Baseline`):**
  1. **Unified Phase 3 Resolution:** All 12 Central Market Colored Die F6 (`★`) abilities resolve in **Phase 3: Income** (zero Phase 5 paid `★` actions, zero Phase 4 damage-conditional `★` tracking, legacy phrasing removed):
     - *R1 Brand Protection (`$5`):* `+$2 & +1 Market Share`.
     - *R2 Ad Campaign (`$4`):* Pay `$2` → `+2 Market Share`.
     - *R3 Customer Poaching (`$5`):* Clockwise from First Player, take `1` Market Share from the rival with the most Market Share.
     - *B1 Honeypot Telemetry (`$5`):* `+2 🔬` if `0` Blue cubes in Exit Tray, or `+$3` if `1+` Blue cubes in Exit Tray.
     - *B2 Deep R&D Vault (`$5`, down from `$6`):* `+$2`, or spend `1` Corporate Secret → `+3 Market Share` (spending a last Secret immediately triggers Total Data Breach / Patient Zero).
     - *B3 Air-Gapped Backup (`$4`):* `+$1`, plus `+$1` per Shield In Production (clean or glitched).
     - *G1 Self-Healing Kernel (`$5`):* Clean `1` Glitched Shield Slot + `+1 🔬` (frees an assigned shield on that slot to block in Phase 4).
     - *G2 Universal Sandbox (`$5`, up from `$4`):* `+2 🔬`, plus `+1 🔬` per Glitched Shield Slot.
     - *G3 Live Reboot (`$4`):* `+1 🔬 & +$1`, and move `1` die from Scanned Box to Ready for Release.
     - *Y1 Algorithmic Trading (`$6`):* `+$4`, or pay `$2` → `+1 Corporate Secret`.
     - *Y2 Cloud Monopoly (`$5`):* `+$2`, plus `+$1` per different Central Market die color owned (`Red`, `Blue`, `Green`, `Yellow`; excludes `Purple`; max `+$6`).
     - *Y3 Proprietary Training (`$5`):* `+1 Corporate Secret`, plus `+$1` per Gray Legacy die owned.
  2. **Streamlined Glitched Shield Slot Flow:** In Phase 1 Step 4, players assign `Block 1 Any` shields to *any* Shield Slot (clean or glitched) up to `defense_capacity`. In Phase 4, shields on glitched slots purge the green cube and move to **Scanned Box** (no tower block, no Defense L4 cash); shields on clean slots block tower cubes.

- **Empirical Telemetry (`v0.44.0` vs `v0.43.0`, N=900 each):**
  - **Pacing & Endings:** `7.32` mean rounds (`v0.43.0`: `7.59`); Patient Zero `63.4%`, Market Collapse `23.3%`, Total Wipeout `7.1%` (2P: `13.3%`), Singularity `6.1%`.
  - **4P Seat Fairness:** `25.7% / 24.3% / 22.7% / 27.3%` (tightened to a `4.6pp` spread vs `8.0pp` in `v0.43.0`).
  - **F6 & Purge Telemetry:** `10,077` glitched slot purges (`0.513/player-round`); `0` B2 suicide breaches (`255` cash vs `122` secret activations); G1 promoted an assigned shield in `33.7%` of activations (`172/511`); G3 fizzled cleanly in `21.9%` (`123/562`).
  - **Inherited Guardrails Noted for Follow-Up `[TUNE]`:** 2P Total Wipeout rate (`13.3%` vs `11.7%` in `v0.43.0`) and Red-starter equity lag (Prometheus `25.1%`, Meridian `28.9%` vs Omnidyne `42.0%`) are inherited from `v0.43.0` and flagged for a dedicated follow-up `[TUNE]` pass.

- **Official Balance Verdict: APPROVED (`v0.44.0 Baseline`).**






---

## 58. Phase 63 Post-Telemetry Balance Assessment: Research Tracks & Capstones (`v0.44.0 Baseline`): APPROVED

Sources: `docs/findings/research_tracks_balance_review.md` (Pre-SDLC modeling), `docs/specs/v440_research_tracks_spec.md` (Technical Architecture Spec), `sim_results/v440_research_tracks/validation_report.md` (7,200 games across 4P, 3P, 2P pods, Seeds 42..1241).

- **Changes Approved for `v0.44.0`:**
  1. **Defense Grid:** L4 drops `$3` cap (`+$1` per Attack Cube blocked, naturally capped at `$4` by Defense Capacity `4`); L3 notes Blue Secret `+1` passive in Section 2 track table.
  2. **Triage Track (Option B):** L1 ★ `1` Gray die → L2 `Bandwidth 2` → L3 ★ `+1 Corporate Secret` → L4 `Replace 1 Gray die with a Central Market colored die ($0 free, to Ready for Release)`. Removed dead `+1 🔬 per die beyond 2nd` text from Phase 6.
  3. **Release Track:** Retained `2` base rerolls (1-reroll sweep breached 4P wipeout guardrail at `3.17%`); **L4** grants `Bandwidth 6` + **set `1` rolled Gray Legacy die to any printed face** in Phase 1 Step 3 (strictly after *Prodigy* and *Helix*).
  4. **Public Relations:** L3 ★ 2nd Purple Specialist die routes to **Scanned Box**; **L4** grants **`+2` Market Share immediately** (clamped at `20`) + regain up to `3`/turn at `$3` Cash; fixed `3 🔬` → `$3` typo in `RULES.md:52`.

- **Telemetry Highlights (`v0.43.0` → `v0.44.0`, 7,200 games):**
  - **Pacing & Wipeouts:** 4P `7.43` → `7.30` rds, Total Wipeout `2.08%` → **`2.00%`** ($\le 2.0\%$ guardrail); 3P `7.61` rds (`4.50%`); 2P `7.49` rds (`11.00%`). Zero stalls ($\ge 13$ rds).
  - **Capstones & Engagement:** Triage L2+ surged `39.4%` → **`93.4%`** (4P); Triage L4 `21.81%` (96.3% replacement rate); Release L4 `26.31%` (`2.19` Gray sets/L4 seat); Defense L4 `4.19%` (`$1.82`/L4 seat). Anti-snowballing (`2+` L4 tracks): **`0.00%`**. *(Note: PR L3/L4 `0.00%` reflects bot `_want_list` priorities in `sim/bots/research_policy.py`, not a rules defect.)*
  - **Client Company Parity (4P):** Spread narrowed from `13.30` pts (`17.90%–31.20%`) to **`9.75` pts** (**`20.46%–30.21%`**).
