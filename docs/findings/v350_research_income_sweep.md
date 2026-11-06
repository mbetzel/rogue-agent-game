# v0.35.0 Research Income Sweep (Phase 43, game-designer)

Status: modeling complete, **awaiting User decisions** (Section 7). No changes were made to `sim/`, `RULES.md`, `web/` or `pnp/`.

Source plan: `docs/explorations/2026_11_research_track_rebalance_plan.md` (locked design). Guardrails: plan Section 4, plus the v0.34.0 D5 table in `docs/explorations/2026_11_six_phase_round_sequence_plan.md`.

## 1. Method

- Script: `scripts/investigate_v350_research_sweep.py`. It's a throwaway prototype that monkeypatches the v0.34.0 engine at runtime:
  - L0–L4 tracks, step costs 1/2/2/3 🔬.
  - Breakthroughs at L1 and L3. L4 capstones for Triage and Defense.
  - Patents rates: L0–L1 2→1, L2–L3 3→2, L4 1→1.
  - Every Client Company at L0. Default capacities 2/2/4. Helix's +2 🔬 and Prometheus's discount removed.
  - Emergency Hotfix and Passive Firewall disabled.
- Setup matches `run_v340_telemetry_sweep.py`: 5-bot rotation, random Client Companies and White Hat Operatives, STANDARD tracks, $6 start, 3 Gray + 1 Purple, 1 Purple in Personal Reserve.
- Runs: 1,000 games per player count per cell, seed 4300 (grids 1–2). Recommendation and company cells use 1,500 games per player count, seed 9100.
- Research income is every 🔬 gained by a player over the game, measured with a property hook on `research_tokens`. It includes the Triage L4 capstone.
- Bot policies:
  - **stock**: the existing v0.34 bots. Their upgrade logic stops at L1–L2, and they put the rest into Patents.
  - **aware**: each bot keeps its own dice, purchase and defense logic. Only the research section is replaced. The bot buys its focus track up to L4, then L1 Breakthroughs on the other tracks, then L2 on its second track, saving toward the next step. It files Patents in the late game (any survivor at ≤ 3 Secrets, or final round) or when it has nothing left to buy. On a "$ / 🔬" choice face it always takes 🔬.
  - Focus tracks by bot: SecOps → Defense, Adaptive → Triage, Accelerationist → Release, Venture → Patents, Reckless → Patents. Cell E1 instead gives each seat a random focus order.
- Not modeled:
  - The Release L4 extra free reroll. Free rerolls are a global config value in the engine.
  - The Defense L4 condition is approximated as "no Secret, $ or die lost in this player's Phase 4".

## 2. Lever comparison: research income per player per game (all player counts)

Face notation is for the Gray die `[Block 1 Any, Block 1 Any, +$1, +$1, +$1 / +1 🔬, +1 🔬]` and the Purple die `[Block 1 Any ×2, +$2, +$1 & +1 🔬, Glitch, ★]`.

| Cell | Lever | 🔬/game mean (med) | 2P Sing. | Rounds 2/3/4P |
|---|---|---|---|---|
| A0 | v0.34.0 baseline | 3.8 (3) | 26.5% | 8.3 / 7.8 / 7.6 |
| A1 | Locked tracks, stock bots | 5.0 (5) | 38.8% | 8.7 / 8.3 / 8.1 |
| A2 | Locked tracks, aware bots | 5.3 (5) | 32.2% | 8.6 / 8.3 / 8.1 |
| B1 / C1 | Gray `+$1/🔬` → `+1 🔬` (stock / aware) | 4.0 / 3.6 | — | — |
| B2 / C2 | Gray one `+$1` → `+$1 / +1 🔬` | 7.3 / 8.3 | 34.4% (C2) | 8.7 / 8.3 / 8.3 |
| B4 | Purple `+$2` → `+$1 & +1 🔬` (stock) | 6.3 | — | — |
| C7 | Gray one `+$1` → `+$1 & +1 🔬` (aware) | 8.5 | 39.4% | — |
| C5 | C2 + Purple change | 10.2 (9) | 35.8% | 8.8 / 8.5 / 8.4 |
| **D1** | **Gray `[B, B, +$1 & +1 🔬, +$1 / +1 🔬, +$1 / +1 🔬, +1 🔬]`, aware** | **12.1 (11)** | **45.3–45.8%** | **9.0 / 8.8 / 8.6** |
| C8 | Gray both `+$1` → `+$1 & +1 🔬`, aware | 12.2 (11) | 51.7% | 9.1 / 8.8 / 8.8 |
| D2 | D1 + Purple change | 14.2 (14) | 49.5% | 9.1 / 8.9 / 8.8 |
| C10 | C8 + Purple change | 14.3 (14) | 56.0% | 9.2 / 9.0 / 8.9 |

Findings:

1. **Face changes are the lever that works. Bot policy alone adds only about 0.3 🔬** (A1 → A2). Policy matters once there is income to spend: it decides whether research goes into tracks or into Patents.
2. **A pure `+1 🔬` face in place of a cash face *lowers* realized income in bot play** (B1/C1). The likely cause is that bot reroll and glitch-choice heuristics undervalue faces with no cash. Human players may behave differently. Combined faces (`+$1 & +1 🔬`) and choice faces (`+$1 / +1 🔬`) both survive the bot heuristics.
3. Both face types already exist in the canonical die set: `+$1 & +1 🔬` on Purple and Yellow, `+$1 / +1 🔬` on Gray. **Neither needs a new glossary term.** A flat per-round 🔬 grant would need one, so it was not modeled.
4. Every package that reaches 12+ 🔬 pushes 2P Singularity to or past the ≤ 45% guardrail. Longer survival (more Secrets) means more games reach v3.0. D1 sits at the edge (45.3% at seed 9100, 45.8% at seed 4300). C8, D2 and C10 breach it.

## 3. Recommended package (D1) and guardrail check

**Gray die `[TUNE]`:** `Block 1 Any`, `Block 1 Any`, `+$1 & +1 🔬`, `+$1 / +1 🔬`, `+$1 / +1 🔬`, `+1 🔬`. Purple is unchanged. Purple `+$2 → +$1 & +1 🔬` is the optional step to 14 🔬 (D2) and needs a Singularity counter-lever.

| Guardrail | Target | D1 (seed 9100, 1,500/pod) | v0.34.0 | Status |
|---|---|---|---|---|
| Research income | 12–14 🔬 | 12.1 mean / 11 median; 4P p10–p90 5–21 | 3.8 | ✅ (low end) |
| Typical player | 1 track at L4 + 2–4 other steps | 50% of seats have exactly 1 L4; mean 4.6 steps total | — | ✅ / ⚠ (half of seats reach no L4) |
| Nobody completes all tracks | 0% | 0.0% | — | ✅ |
| Track-maxing concentration | ≤ ~50% on one track | Bot-biased focus: Patents 58%. Random focus (E1): Release 44%, Patents 31%, Triage 13%, Defense 12% | — | ⚠ / ✅ (see risks) |
| Mean rounds | 8–11 | 9.0 / 8.8 / 8.6 | 8.3 / 7.8 / 7.6 | ✅ (also fixes the 4P short-game watch item) |
| Singularity ending | ≤ 45% | 45.3% / 38.6% / 34.0% | 26.5% / 17.1% / 13.7% | ⚠ 2P at the edge |
| Total Wipeout ending | ≤ 15% | 11.9% / 3.3% / 1.1% | 15.4% / 5.5% / 1.1% | ✅ |
| Patient Zero ending | Informational | 42.9% / 58.1% / 64.9% | 58.1% / 77.4% / 85.2% | — |
| Bot win-rate spread | ≤ 45 pts | 30 pts | 29 pts | ✅ |
| Survivor Secrets at game end | No inflation beyond guardrails | 4.6 / 4.8 / 4.8 | 3.2 / 3.7 / 3.8 | ⚠ +1.0–1.4 (no numeric guardrail exists) |

Secret sources per seat (D1): Patents +2.0 Secrets per game and L3 Breakthroughs +0.27. Leftover 🔬 at game end is 0.7.

## 4. Breakthrough definitions (proposals)

| Item | Proposal | Data / reasoning |
|---|---|---|
| Gray die from Defense / Release L1 | Placed in the **Ready for Release Zone** | Matches how purchases are placed and needs no new rule. The die rolls in the next Phase 1. |
| Patents L3 "Unlock 2nd Purple die" | **Free die**: take the Purple die from your Personal Reserve and place it in Ready for Release. If the Reserve is empty, recommend **+$3** as a fallback (`[TUNE]`). | In v0.34.0 the Reserve Purple can **already be bought for $5**, so "access only" is not an unlock unless baseline Reserve access is removed. That would be a rules change: D5 tested it, with ~0.7 🔬 less income and no Purple Breakthrough. In D1 the free version fires 0.32 times per seat; 0.06 per seat hit an empty Reserve. |
| Triage L3 "Swap a colored die with the Market" | Return 1 colored die you own (not Purple, from any CI/CD Pipeline zone) to the Central Market. Take a Market die of a different color into Ready for Release. Pay the cost difference if the new die costs more; no refund if it costs less. | In the prototype (Ready for Release only), 70% of swaps **fizzled** (0.04 fired vs 0.10 dead per seat). Allowing any zone reduces fizzles. A free swap (D4) changed nothing measurable. It stays a weak Breakthrough; consider a $ fallback if no colored die is owned. |
| Triage L1 (2 White Contractors) | Into Ready for Release. They expire normally at the end of the next Phase 4. | 0.4–0.9 Contractors per seat. |
| Defense L4 `+$1` | As locked. | It paid only 0.004–0.018 $ per seat per game. **The capstone is nearly inert**: Defense L4 is rarely reached and rarely clean. A candidate for retuning. |

## 5. Client Companies (all at L0)

Company win rates, D1, 1,500 games per pod:

| Cell | Aegis | DTO | Helix | Meridian | Omnidyne | Prometheus | Spread |
|---|---|---|---|---|---|---|---|
| v0.34.0 (A0) | 14% | 81% | 34% | 31% | 13% | 27% | 69 pts |
| D1, no replacement | 30% | 68% | 24% | 29% | 26% | 22% | 46 pts |
| F1: Helix +$2, Prometheus +$2 starting cash | 29% | 66% | 26% | 28% | 25% | 26% | 41 pts |
| F2: Helix +1 Secret, Prometheus +1 Secret | 27% | 63% | 30% | 26% | 23% | 31% | 40 pts |
| F4: DTO without its +1 Secret | 32% | 57% | 26% | 31% | 28% | 25% | 32 pts |
| F3: Helix +$1, Prometheus +$2, DTO without +1 Secret | 31% | 56% | 27% | 30% | 28% | 28% | 30 pts |

- Removing everyone's track head-starts mostly levels the non-DTO field (22–30%). Helix and Prometheus need only small bonuses.
- Recommended replacement bonuses are starting cash, the same modifier type Meridian already uses, so no new term is needed:
  - **Helix +$1** `[TUNE]`
  - **Prometheus +$2** `[TUNE]`
- +1 Secret overshoots for both.
- **DTO is still dominant (56–68%).** Slush Fund is the cause, not the starting Secret: removing the +1 Secret only brings DTO to 57%. Carried from Phase 42. A Slush Fund nerf (absorb 1 instead of 2) should be modeled separately.

## 6. Risks

- **2P Singularity at the edge (45%).** Any further income lever (Purple change, 14 🔬) breaches it. A counter-lever is needed if the User wants 14: for example a 2P-only v3.0 timing change, or Patents L0 at 3→1. The second one changes the locked design.
- **Secret inflation**: survivor Secrets rise by about 1.2. Patents L0 at 2:1 supplies about 2 Secrets per seat. No numeric guardrail exists; the User should set one.
- **Patents L4 pull**: the 1→1 rate makes Patents the most attractive track to max for bots focused on Secrets. Concentration passes only under neutral (random) focus.
- **Defense track is the weakest**: 12% of maxed seats under random focus, and an inert capstone.
- **Bot artifact on pure 🔬 faces**: humans may value them differently. Live playtests should check income with the D1 Gray die.
- Release L4 reroll is unmodeled. The Defense L4 condition is approximate.
- The aware policy is a scripted prototype. Engineering would need to port it into `sim/bots` for the real telemetry.

## 7. Decisions requiring User approval

1. Adopt the **D1 Gray die faces** (`Block 1 Any ×2`, `+$1 & +1 🔬`, `+$1 / +1 🔬 ×2`, `+1 🔬`) as the research income lever, accepting ~12 🔬 (low end of target). Or also take the Purple `+$2 → +$1 & +1 🔬` change to reach ~14 🔬 plus a Singularity counter-lever.
2. Accept 2P Singularity at ~45% (edge of guardrail), or commission a counter-lever study.
3. Set a numeric Secret-inflation guardrail (survivor Secrets go from 3.2–3.8 to 4.6–4.8).
4. Patents L3: **free Purple from Personal Reserve**, with a fallback if the Reserve is empty (+$3 proposed).
5. Triage L3 swap: any zone, pay the difference, no refund, new die to Ready for Release. Optionally add a fallback.
6. Gray die from Breakthroughs goes to Ready for Release.
7. Replacement bonuses: **Helix +$1, Prometheus +$2 starting cash**.
8. DTO: commission a separate Slush Fund nerf study (the +1 Secret is not the main driver).
9. Defense L4 capstone retune (currently near-inert). Optional.
10. Bot research policy (focus-track planner + 🔬 on choice faces) is ported into `sim/bots` for the v0.35 telemetry.

No new glossary terms are proposed beyond the already-approved **Breakthrough**. A flat per-round research grant (which would need one) was not adopted.
