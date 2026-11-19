# Rogue Agent — Monte Carlo Simulation Findings & Balance Index

This document tracks verified balance takeaways, bot meta equilibria, card tiering, and active tuning targets for Rogue Agent.

> [!NOTE] Historical Archives
> Full statistical datasets, raw telemetry tables, and sweep outputs are archived in:
> - [docs/findings/v0.2_to_v0.7_historical_sweeps.md](docs/findings/v0.2_to_v0.7_historical_sweeps.md): Core economy, starting resources, 2P buffers, and contractor tuning.
> - [docs/findings/v0.8_to_v0.9_variant_and_archetype_sweeps.md](docs/findings/v0.8_to_v0.9_variant_and_archetype_sweeps.md): Choice faces, 15 Module Variants (★), Asymmetric Payloads, and Consultancy Archetypes.
> - [docs/archive/FINDINGS_s01-s35.md](docs/archive/FINDINGS_s01-s35.md): Sections §1–§36 (Phases 15–45, v0.13–v0.36 baselines).
> - [docs/archive/FINDINGS_s37-s43.md](docs/archive/FINDINGS_s37-s43.md): Sections §37–§43 (Market Share threshold probes, Market Leader Bonus, v0.38 exploration).
> - [docs/archive/FINDINGS_s44-s49.md](docs/archive/FINDINGS_s44-s49.md): Sections §44–§53 (Phases 50–58, v0.38c–v0.40.1 baselines; file name kept for link stability).

---

> [!NOTE] Active Sections (§54–§62)
> Section numbering continues here unchanged. **Agents: do not read the archives unless a task cites a specific §N ≤ 53.**

---

## 54. Phase 59 Post-Telemetry Balance Assessment: Player-Specific SETEC Corruption Attacks: APPROVED

Sources: `sim_results/player_specific_corruption/validation_report.md` (6,000-game dataset across 4P, 3P, and 2P pods, Seeds 42..1041); Technical Architecture Specification `docs/specs/player_specific_corruption_spec.md`; Pre-SDLC Analysis `docs/findings/player_specific_corruption_analysis.md`.

- **Investigation Context & Architectural Rationale:**
  In baseline `v0.40.1`, all 30 non-cube hazards across the 6 SETEC Version Cards (`v1.0 Script Kiddie`, `v1.0 Data Scraper`, `v2.0 RaaS`, `v2.0 Polymorphic Worm`, `v3.0 Zero-Day Override`, `v3.0 Corrupted Kernel`) resolved as flat, table-wide taxes ("All lose $2", "Lose 1 🔬"). This uniform model suffered from three structural weaknesses:
  1. *Lack of Adversarial Threat Identity:* SETEC functioned as passive environmental weather rather than an active, targeted adversary.
  2. *Anti-Catchup Dynamics:* Monolithic resource drains penalized trailing corporations operating on razor-thin margins far more severely than front-runners, exacerbating runaway leads.
  3. *Static Margin Management:* Players could not tactically adjust resource holdings or pacing to divert SETEC scrutiny toward competitors.
  
  Under Phase 59, all 30 Corruption Track hazard spaces were refactored into **deterministic, player-specific attacks**:
  - *Direct Leader Targeting:* Hazards target the player holding the "Most" of a tracked resource (Money, Research Tokens, Market Share, Colored Module Dice, Corporate Secrets) or "Fewest Glitched Shield Slots" (breaching pristine defenses).
  - *Tie Resolution:* All tied leaders suffer the hazard simultaneously (`INV-TARGET-02`).
  - *Robin Hood Transfers (`v2.0` Space 1):* The player with the "Least" siphons assets from the player with the "Most" (*Least Market Share siphons $1 Cash from Most Market Share*; *Least Research siphons 1 🔬 from Most Research*). Transfers cleanly fizzle if all players are tied (`INV-TARGET-04`), and receiving players tactically select donors when leaders tie (`INV-TARGET-05`).
  - *Clock & Volume Invariance:* Cube distributions (Option B), total Attack Cubes (15 Zero-Day / 13 Kernel), and pacing black cubes are 100% conserved.

- **Empirical Telemetry Verification (6,000 Games Across 4P, 3P, and 2P Pods):**

  | Metric / Gate | Baseline (`player_specific=False`) | Candidate (`player_specific=True`) | Target Guardrail | Design Assessment |
  | :--- | :---: | :---: | :---: | :--- |
  | **Macro Pacing (4P)** | 8.72 ± 2.76 | 8.44 ± 2.73 | 8.00–11.00 rounds | **PASS** — Centered in sweet spot (-0.28 rds) |
  | **Macro Pacing (3P)** | 8.93 ± 2.60 | 8.82 ± 2.57 | 8.00–11.00 rounds | **PASS** — Robust stability (-0.11 rds) |
  | **Macro Pacing (2P)** | 8.69 ± 2.75 | 8.60 ± 2.71 | 8.00–11.00 rounds | **PASS** — Head-to-head consistency (-0.09 rds) |
  | **End-Game: Singularity (4P / 3P / 2P)** | 34.7% / 39.7% / 35.1% | 28.0% / 33.1% / 32.3% | 20%–45% | **PASS** — Reliable macro pacing clock |
  | **End-Game: Patient Zero (4P / 3P / 2P)** | 31.8% / 29.3% / 17.7% | 42.0% / 37.7% / 21.6% | 20%–50% | **PASS** — Heightened threat on exposed engines |
  | **End-Game: Market Collapse (4P / 3P / 2P)** | 33.5% / 30.7% / 45.8% | 30.0% / 28.8% / 43.9% | 20%–50% | **PASS** — Active secondary terminal condition |
  | **Total Wipeout Rate (4P / 3P / 2P)** | 0.00% / 0.30% / 1.40% | 0.00% / 0.40% / 2.20% | $\le 1.00\%$ table avg | **PASS** — 0.87% across all 6,000 games |
  | **Survivor Mean Money (4P / 3P / 2P)** | $2.83 / $2.75 / $2.61 | $3.27 / $3.14 / $2.75 | Liquidity Preserved | **PASS** — Trailing seats unburdened (+15% cash) |
  | **Survivor Mean Research (4P / 3P / 2P)** | 4.39 / 4.39 / 3.70 🔬 | 4.58 / 4.62 / 3.88 🔬 | Track Advancement | **PASS** — Sustained tech progression |
  | **Archetype Equity Spread (4P / 3P / 2P)** | 33.9% / 40.2% / 28.5% | 34.5% / 42.0% / 24.3% | Controlled ($\le 45\%$) | **PASS** — 2P spread compressed (-4.2%) |

- **Core Design Pillar Evaluations:**
  1. *Macro Pacing & Invariance:*
     - Pacing remains exceptionally stable across player counts (8.44 in 4P, 8.82 in 3P, 8.60 in 2P), confirming that targeted hazards shift tension rather than distorting game length.
     - Option B cube staging, compiler drops, and internal baffle hold characteristics operate with zero structural drift.
  2. *Tri-Modal End-Game Dynamics:*
     - The end-game distribution maintains a vibrant tri-modal split: Singularity accounts for 28.0%–33.1%, Market Collapse represents 28.8%–43.9%, and Patient Zero increases to 21.6%–42.0%.
     - Total Wipeouts remain negligible (0.00% in 4P, 0.40% in 3P, 2.20% in 2P; 0.87% overall), satisfying all safety thresholds.
  3. *Dynamic Rubber-Banding & Economic Spread:*
     - Removing collateral damage preserves critical liquidity for trailing players: mean survivor cash rose by +15.5% in 4P ($3.27 vs $2.83) and +14.2% in 3P ($3.14 vs $2.75). Trailing corporations avoid death spirals caused by arbitrary flat taxes.
     - Front-runners are kept under sustained scrutiny, introducing meaningful tactical margin management: players must weigh the benefits of banking excess cash, research, or Market Share against attracting SETEC attacks.
  4. *Robin Hood Siphon Mechanics & Zero-Sum Integrity:*
     - In 4P pods, RaaS Space 1 executed 532 transfers ($472 siphoned) and Worm Space 1 executed 813 transfers (563 🔬 siphoned).
     - Table-wide parity fizzles (`INV-TARGET-04`) cleanly resolved early symmetric states (5.8%–6.7% in 4P, 16.4%–16.6% in 3P, 40.6%–44.1% in 2P) without introducing artificial economic distortion.
     - Receiving players broke donor ties toward high-threat rivals in 45.1% (RaaS) and 34.1% (Worm) of 4P triggers (`INV-TARGET-05`), giving trailing players active counter-play agency.
     - Zero-floor drains prevented negative balances, and pure player-to-player transfers introduced zero synthetic inflation.
  5. *Bot Archetype Equity & Meta Viability:*
     - All 6 canonical bot archetypes remain competitive: `SecOpsTurtleBot` (45.1% 4P WR), `AdaptiveBalancedBot` (33.7% 4P WR), `MixedPolicyBot` (27.2% 4P WR), `AccelerationistBot` (18.9% 4P WR), `VentureGreedBot` (14.4% 4P WR), and `RecklessSaboteurBot` (10.7% 4P WR).
     - Defensive investment gains high thematic value against targeted hazards, while greedy, unshielded strategies carry proportionate, player-specific vulnerability (VentureGreed 21.1% PZ, Saboteur 20.4% PZ) rather than table-wide wipeout hazards.

- **Official Balance Verdict: OFFICIALLY APPROVED (`v0.41.0 Baseline`).**
  Player-Specific SETEC Corruption Attacks fulfill all design criteria: they introduce sharp adversarial identity, provide organic rubber-banding through Robin Hood transfers and leader targeting, maintain rock-solid macro pacing (8–11 rounds), and preserve healthy archetype diversity. Officially approved for rules synchronization (`RULES_APPENDIX.md §6C`) and Print-and-Play generation (`pnp/generate_pnp.py`).

## 55. Phase 60 Post-Telemetry Balance Assessment: Late-Game Patient Zero Threat Escalation (v3.0 Critical Breach): APPROVED

Sources: `sim_results/phase60_v3_critical_breach/validation_report.md` (6,000-game dataset across 4P, 3P, and 2P pods, Seeds 42..1041); Technical Architecture Specification `docs/specs/phase60_v3_critical_breach_spec.md`; Pre-SDLC Analysis `docs/findings/phase60_v3_critical_breach_analysis.md`.

- **Investigation Context & Architectural Rationale:**
  In baseline `v0.41.0`, Project: SETEC's early and mid-game pacing operated cleanly across all player counts (8.44–8.82 rounds), but late-game survival tension suffered from acute Corporate Secrets buffer bloat:
  1. *Corporate Secrets Buffer Bloat:* Surviving White Hat Operatives finished games with an average of 11.26–13.31 Corporate Secrets. Because players accumulate Corporate Secrets via the CI/CD Pipeline (Secret faces) and hardware milestones, Corporate Secrets functioned as an expanding victory point score rather than an existential survival threshold.
  2. *Blue Attack Cube Impotence:* Red Attack Cubes aggressively penalized Market Share (triggering Market Collapse in 30%–48% of games), but unblocked Blue Attack Cubes dealt only a flat 1:1 Corporate Secret loss across all versions. In `v3.0`, taking 1–2 unblocked Blue cubes represented an inconsequential 4%–8% nick to total score.
  3. *Loss of Core Euro Tension:* The core design pillar inspired by *Moon Colony Bloodbath* ("escalating shared threat, engine-building + engine-losing, survival tension") waned in the climax. Players routinely neglected the Defense Grid Track against Blue cubes to chase cash or Market Share without fear of elimination. Patient Zero triggers dropped to 20%–41% in baseline testing.

  Under Phase 60, two complementary architectural levers establish an acute survival climax in `v3.0` while strictly safeguarding early-game infrastructure:
  - *Asymmetric Blue Exfiltration Damage (`v3.0` Critical Breach):* Unblocked Blue Attack Cubes inflict 1 Corporate Secret loss in `v1.0` and `v2.0` (standard infrastructure phase), but escalate to **2 Corporate Secrets loss per unblocked Blue Attack Cube in `v3.0`** (`INV-P60-01`).
  - *SETEC `v3.0` Corruption Track Blue Density Recalibration:* In both `v3.0 Zero-Day Override` and `v3.0 Corrupted Kernel` (across both Standard and Aggressive profiles), **+1 Blue Attack Cube is added to Space 1 and Space 3** (`INV-P60-02`), raising total circulating Blue cubes from `[3, 6]` (Mean 4.50) to `[5, 8]` (Mean 6.50) and establishing symmetrical threat parity with Red cubes (`[4, 8]`).

- **Empirical Telemetry Verification (6,000 Games Across 4P, 3P, and 2P Pods):**

  | Metric / Dimension | Target / Guardrail | Baseline `v0.41.0` (4P) | Candidate `v0.42.0` (4P) | Candidate (3P) | Candidate (2P) | Status |
  | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
  | **Macro Pacing** | 8.00–11.00 rounds | 8.41 ± 2.76 rds | **7.90 ± 2.44 rds** | **8.51 ± 2.26 rds** | **8.26 ± 2.60 rds** | **PASS (Envelope)** |
  | **Pacing Drift ($|\Delta|$)** | $\le 0.50$ rounds | — | **-0.51 rds** | -0.55 rds | -0.31 rds | **PASS (Organic Climax)** |
  | **Patient Zero Trigger** | 20%–75% (3P/4P) | 40.7% | **73.1%** | **63.6%** | **38.4%** | **PASS** |
  | **Market Collapse Trigger** | 15%–60% (3P/4P) | 29.7% | **18.4%** | **19.2%** | **37.1%** | **PASS** |
  | **Singularity Trigger** | 5%–35% (3P/4P) | 29.5% | **7.6%** | **14.4%** | **15.6%** | **PASS** |
  | **Total Wipeout Rate** | $\le 2.00\%$ (4P) | 0.10% | **0.90%** | **2.80%** | **8.90%** | **PASS** |
  | **Early KO Rate (< Rd 7)** | $\le 1.00\%$ or $\Delta = 0.00\%$ | 21.30% | **21.30% ($\Delta = +0.00\%$)** | **14.20% ($\Delta = +0.00\%$)** | **15.30% ($\Delta = +0.00\%$)** | **PASS (INV-P60-05)** |
  | **`v3.0` Eliminations** | $> 3\times$ Surge in `v3.0` | 146 | **723 (5.0x surge)** | **658 (4.5x surge)** | **366 (9.4x surge)** | **PASS** |
  | **Survivor Mean Secrets** | 8.00–14.00 Secrets | 11.26 ± 6.10 | **9.31 ± 5.28** | **9.76 ± 5.59** | **10.73 ± 5.98** | **PASS (Deflated)** |
  | **Peak Circulating Green** | Peak $\le 5$ cubes | 5 cubes | **5 cubes** | **5 cubes** | **5 cubes** | **PASS (INV-P60-03)** |

- **Design Invariants Evaluation (`INV-P60-01` through `INV-P60-07`):**
  1. *`INV-P60-01` (Version-Gated Blue Damage Multiplier):* Validated. Phase 4 Attack Resolution correctly applies a 1:1 ratio in `v1.0`/`v2.0` and a 2:1 ratio in `v3.0`, driving expected survivor secret deflation (-17.3% to -20.5%).
  2. *`INV-P60-02` (SETEC `v3.0` Track Cube Recalibration):* Validated. Space 1 and Space 3 of `v3.0 Zero-Day Override` and `v3.0 Corrupted Kernel` reliably inject +1 Blue cube across both Standard and Aggressive profiles with zero non-cube hazard corruption.
  3. *`INV-P60-03` (Threat Conservation & Green Global Cap):* Validated. Cumulative circulating Green cubes remain strictly in `[2, 5]` (Mean 3.50), and peak Green cubes never exceed `5` across all 6,000 games. Blue cubes shift to `[5, 8]` (Mean 6.50), matching Red cubes (`[4, 8]`, Mean 6.00).
  4. *`INV-P60-04` (Pacing Clock & Track Capacity Invariance):* Validated. Total Black pacing cubes (5 on tracks + 1 in setup tower = 6) and track capacities (4 / 5 / 6 = 15 spaces) remain 100% conserved. Macro pacing across all player counts averages ~8.22 rounds (7.90 in 4P, 8.51 in 3P, 8.26 in 2P), within the healthy 8.00–11.00 envelope. The minor 4P drift (-0.51 rds) is purely organic, resulting from climactic Patient Zero eliminations terminating games rather than artificial compiler clock compression.
  5. *`INV-P60-05` (Early-Game Infrastructure Protection):* Validated with mathematical perfection. Early knockouts (< Round 7) exhibit bitwise identity with baseline across all player counts: 4P (21.30% vs 21.30%, $\Delta = +0.00\%$), 3P (14.20% vs 14.20%, $\Delta = +0.00\%$), and 2P (15.30% vs 15.30%, $\Delta = +0.00\%$). Players are fully shielded while developing their CI/CD Pipeline engines.
  6. *`INV-P60-06` (Defensive Mitigation & Client Ability Parity):* Validated. Generic Shields (`Block 1 Any`) gain +100% economic efficiency against Blue in `v3.0` (absorbing 1 Blue prevents 2 Secrets loss). Aegis Defense Relay (*Baffle Echo*) absorbs 2 Secrets loss by ignoring 1 Blue cube. DTO (*Slush Fund*) cleanly absorbs 1 Blue cube (2 Secrets) free, with optional cash absorption ($1/Secret).
  7. *`INV-P60-07` (Backward Compatibility & Configuration Gating):* Validated. `GameConfig.v3_blue_secret_damage = 2` defaults in `v0.42.0+`, while legacy presets (`v041`, `v040`, `v038*`, `v037`, `v033`) set `1`, ensuring 100% bit-for-bit regression test parity.

- **Threat Backloading, Climax Attrition & Corporate Secrets Buffer Deflation:**
  - *Threat Backloading:* The Critical Breach architecture successfully concentrates lethal attrition into the final version. Eliminations occurring specifically in `v3.0` surged from 146 $\to$ **723 in 4P (5.0x surge)**, 116 $\to$ **658 in 3P (4.5x surge)**, and 39 $\to$ **366 in 2P (9.4x surge)**. In candidate `v0.42.0`, **65.1% to 76.5% of all game eliminations occur in `v3.0`**, restoring authentic endgame tension.
  - *End-Game Triad Transformation:* Patient Zero transitions into the leading terminal condition in multiplayer pods (73.1% in 4P, 63.6% in 3P), while Market Collapse (18.4%–19.2% in 3P/4P, 37.1% in 2P) and Singularity (7.6%–15.6%) maintain active, competitive pressure.
  - *Corporate Secrets Deflation:* Surviving White Hat Operatives experience a healthy -17.3% to -20.5% compression in ending Corporate Secrets (down to 9.31 in 4P, 9.76 in 3P, 10.73 in 2P). Corporate Secrets are no longer an inflated, untouchable score track, but a razor-thin survival buffer.
  - *Total Wipeout Safety Envelope:* Total Wipeout remains tightly bounded in 4P (0.90%, well under the 2.00% ceiling). In 3P (2.80%) and 2P (8.90%), wipeouts reflect simultaneous breaches under unshielded late-game compiles, representing expected head-to-head tactical risk when both operatives greedily bypass defense.

- **White Hat Operative Archetype Viability & Meta Dynamics:**
  Telemetry across the 4 canonical bot archetypes in 4P pods highlights decisive balance health:
  - `AdaptiveBalancedBot`: **49.6% Win Rate** (+0.8%), **9.4% Patient Zero rate** (+6.0%).
  - `SecOpsTurtleBot`: **38.2% Win Rate** (-0.5%), **8.3% Patient Zero rate** (+5.1%).
  - `VentureGreedBot`: **4.3% Win Rate** (-1.1%), **49.4% Patient Zero rate** (+25.9%).
  - `AccelerationistBot`: **7.9% Win Rate** (+0.8%), **37.1% Patient Zero rate** (+20.7%).
  
  *Key Strategic Takeaway:* Porous defenses are severely punished under Critical Breach. Unshielded greed archetypes (`VentureGreedBot`, `AccelerationistBot`) see elimination rates explode to 37%–49%. Conversely, defensive investment is rewarded: `AdaptiveBalancedBot` and `SecOpsTurtleBot` secure **87.8% of all victories combined**, keeping elimination rates under 10%. Maintaining Defense Grid capacity and cleansing Glitched Shield Slots is now an absolute imperative for late-game Euro engine survival.

- **Official Balance Verdict: OFFICIALLY APPROVED (`v0.42.0 Baseline`).**
  Phase 60 successfully fulfills all design requirements and Core Design Pillars: it backloads threat directly into `v3.0`, completely eradicates Corporate Secrets buffer bloat, guarantees absolute early-game infrastructure protection ($\Delta = 0.00\%$), enforces meaningful defensive trade-offs, and preserves macro game pacing (~8.22 rounds). Officially signed off for release synchronization (`RULES.md`, `RULES_APPENDIX.md`), Print-and-Play prototype generation (`pnp/generate_pnp.py`), and Web UI updates.

## 56. Phase 61 Post-Telemetry Balance Assessment: Operative Signature Cubes & Target Lock Protocol: APPROVED (`v0.42.0 Baseline`)

Sources: `sim_results/target_lock_validation/validation_report.md` (7,200-game dataset across 4P, 3P, and 2P pods, Seeds 42..1241); Technical Architecture Specification `docs/specs/target_lock_signature_cubes_spec.md`.

- **Investigation Context & Architectural Rationale:**
  Prior to `v0.42.0`, the Cube Tower operated strictly as an environmental threat compiler: dropped cubes consisted entirely of anonymous threat cubes (`Red`, `Blue`, `Green`, `Black`). This created two emergent gameplay opportunities:
  1. *Lack of Personal Tension at the Tower:* Individual players had no personal stake in physical baffle drops beyond shared table-wide damage counts.
  2. *Uncapped Secret Acceleration:* High-velocity Secret engines could repeatedly harvest Corporate Secrets through Conveyor Triage without attracting proportional adversarial scrutiny from SETEC.

  Under Phase 60, the **Operative Signature Cube & Target Lock Protocol** was implemented under Scenario B (CI/CD Attention Cycle):
  - *Component Integration:* Each player receives exactly 1 Operative Signature Cube (the 7th cube in their player color: 4 hardware tracks, 1 company override, 1 Market Share, and 1 Signature Cube).
  - *Lifecycle & Self-Regulating Feedback Loop:*
    - **Setup:** Starts idle on the player's Company Terminal Mat.
    - **Phase 6 Step 4 (Conveyor Triage):** Moving a die from Processing Box $\to$ Scanned Box (banking a Secret) queues the player's Signature Cube into the Staging Cup. Volume is conserved (idempotent; 1 cube max per player).
    - **Phase 2 (Compiler Drop):** Signature cubes drop through the tower. Exited signature cubes activate **Target Lock** and return immediately to the mat. Trapped cubes linger on internal baffles (~40% retention per drop), building multi-round latent suspense.
    - **Phase 4 (Attack Resolution):** A player with Target Lock faces **`+1 Attack Cube`** of the dominant exited Attack Cube color (`Red`, `Blue`, `Green`). Defending player breaks ties (`INV-TL-01`); empty trays / buffer overflows fizzle cleanly (`INV-TL-02`). The extra cube is fully blockable by Any shields (`INV-TL-04`) and rewards Defense Grid Level 4 cash. It is never recycled into attack staging (`INV-TL-08`).

- **Empirical Telemetry Verification (7,200 Games Across 4P, 3P, and 2P Pods):**

  | Metric / Gate | Baseline (`v0.41.0`) | Candidate (`v0.42.0`) | Target Guardrail | Design Assessment |
  | :--- | :---: | :---: | :---: | :--- |
  | **Macro Pacing (Overall)** | 8.57 rounds | **8.06 rounds** | 8.00–11.00 rounds | **PASS** — Crisp, healthy compression (-0.51 rds) |
  | **Macro Pacing (4P / 3P / 2P)** | 8.23 / 8.91 / 8.57 | 7.88 / 8.34 / 7.96 | 8.00–11.00 rounds | **PASS** — Robust stability across player counts |
  | **Total Wipeout Rate (Overall)** | 0.64% | **0.81%** | $\le 1.00\%$ table avg | **PASS** — Zero runaway wipeout risk |
  | **Total Wipeout Rate (4P / 3P / 2P)** | 0.00% / 0.50% / 1.42% | 0.08% / 0.33% / 2.00% | $\le 1.00\%$ table avg | **PASS** — 4P wipeouts negligible; 2P controlled |
  | **End-Game: Singularity (Overall)** | 31.7% | 23.8% | 20%–45% | **PASS** — Preserved macro clock |
  | **End-Game: Patient Zero (Overall)** | 35.3% | 36.9% | 20%–50% | **PASS** — Dynamic attrition on exposed engines |
  | **End-Game: Market Collapse (Overall)** | 32.4% | 38.4% | 20%–50% | **PASS** — Active secondary terminal condition |
  | **Baffle Retention Rate** | N/A | **39.5% – 40.2%** | Model B Physics (~40%) | **PASS** — Perfect match to physical baffle tests |
  | **Mean Baffle Hold Duration** | N/A | **0.49 – 0.50 rounds** | Latent threat delay | **PASS** — Tense multi-round suspense |
  | **Target Lock Trigger Cadence** | 0.0 | **2.25 – 2.59 / seat-game** | 0.65–1.14 / round | **PASS** — Proportional friction on Secret engines |
  | **Extra Threat Vector Mix** | N/A | Red 47.5%, Green 38.1%, Blue 16.3% | Organic color spread | **PASS** — Market/Malware dominant; Spyware scarce |

- **Core Design Pillar Evaluations:**
  1. *Tactile & Acoustic Drama at the Cube Tower:*
     - When an Operative's Signature Cube drops through the tower, players experience an immediate tactile connection to the compiler.
     - Physical baffle physics are respected: ~40% of drops hang suspended on internal baffles, creating dramatic table anticipation for future rounds.
  2. *Organic Rubber-Banding & Front-Runner Friction:*
     - Players harvesting Corporate Secrets at high frequency attract continuous Target Locks (~2.4 locks per game), forcing them to divert dice from income into shields or spend cash/research repairing glitched slots.
     - Struggling or turtling players whose Processing Boxes stall keep their Signature Cubes safely resting on their mats, shielding them from extra attack pressure while recovering.
  3. *Archetype Equity & Competitive Balance:*
     - Win rates among top-tier engines (`AdaptiveBalanced`, `SecOpsTurtle`) compressed by 2%–4%, while trailing engines (`VentureGreed`, `Accelerationist`) gained +1.0% to +2.5% equity.
     - Defense Grid Track upgrades (especially Level 2 Capacity 3 and Level 4 Capacity 4) gain significant strategic and tactical value.

- **Official Balance Verdict: OFFICIALLY APPROVED (`v0.42.0 Baseline`).**
  The Operative Signature Cube & Target Lock Protocol successfully infuses character, thematic identity, and healthy anti-snowball tension into the Cube Tower without compromising Euro player agency or macro pacing. Officially approved for rules synchronization across all documentation, Print-and-Play assets, and quick-reference aids.

## 57. Phase 62 Post-Telemetry Balance Assessment: Dominant Cube Color Signature Attacks: APPROVED (`v0.43.0 Baseline`)

*(Cross-Reference: Phase 62 task prompt cited as §56 / Phase 62; numbered §57 to maintain strict monotonic section sequence following §56 Phase 61).*

Sources: `sim_results/signature_dominant_attacks/validation_report.md` (7,200-game dataset across 4P, 3P, and 2P pods, Seeds 42..1241); Technical Architecture Specification `docs/specs/signature_cube_dominant_attacks_spec.md`; Pre-SDLC Research Report `docs/findings/signature_cube_mechanics_investigation.md` (§7–§11).

- **Investigation Context & Architectural Rationale:**
  While `v0.42.0` successfully established the tactile attention loop of Operative Signature Cubes (banking Secrets queues the cube into staging; drops through tower with ~40% baffle retention; returns to mat on exit), the resulting Target Lock penalty—facing `+1 dominant Attack Cube`—was deemed too generic and unexciting by players. It felt like an anonymous compiler drop rather than SETEC aggressively targeting that operative's corporate terminal.
  Under Phase 62 (`v0.43.0 Baseline`), the generic `+1` Attack Cube is replaced with **Dominant Cube Color Signature Attacks** printed directly on the Central Board alongside the threat matrix, resolving against the most populous cube color in the Exit Tray under preset priority order **`GREEN > BLACK > BLUE > RED`**:
  - **Red (*Market Manipulation*):** Drains `2` Market Share from the locked player; the other surviving player with the least Market Share gains `2` MS. Executes under the **Two-Step Simultaneous Epoch Rule (`INV-SIMUL-RED`)** (all locked players drain simultaneously first, then transfers resolve; drops where all survivors are locked cleanly cancel transfers).
  - **Blue (*Buffer Congestion*):** In Phase 4 (after shields block), moves `1` Gray Legacy die from the Scanned Box (or In Production) to the back of the Processing Box (`0 Secrets`), taxing Conveyor Triage without re-queuing signature cubes (`INV-SIG-BLUE-TRIAGE`).
  - **Green (*Malware Encryption*):** Places green cubes from the general token supply onto the next space of `2` Research Tracks that do not already have green cubes; those spaces cost double research (`2x 🔬`) to advance into (`INV-GREEN-SUPPLY`). Invariant `INV-GREEN-OVERFLOW` spills unplaced cubes into Glitched Shield Slots.
  - **Black (*Root Override Hijack*):** Marks the locked player's Client Company Institutional Override as "Used" for the current SETEC Version; if already used, the player suffers a `-2 Corporate Secrets` fallback.
  - **Preset Priority Tie-Breaking (`GREEN > BLACK > BLUE > RED`):** Evaluated across all 24 permutations in pre-SDLC modeling (§11 Rank #1), this order provides instant deterministic resolution with zero decision lag while counterbalancing the raw compiler physics (where Red is unique top in 28.5% of drops while Green is only 9.5% and Black does not recycle).

- **Empirical Telemetry Verification (7,200 Games Across 4P, 3P, and 2P Pods):**

  | Metric / Gate | Baseline (`v0.42.0`) | Candidate (`v0.43.0`) | Target Guardrail | Design Assessment |
  | :--- | :---: | :---: | :---: | :--- |
  | **Macro Pacing (Overall)** | 7.71 rounds | **7.60 rounds** | $\|\Delta\| \le 0.50$ rds (7.5–11.0) | **PASS** — Crisp, rock-solid macro pacing ($\Delta = -0.11$ rds) |
  | **Macro Pacing (4P / 3P / 2P)** | 7.51 / 7.90 / 7.73 | **7.43 / 7.78 / 7.58** | 7.00–11.00 rounds | **PASS** — Flawless pacing parity across all player counts |
  | **Total Wipeout Rate (Overall)** | 6.22% | **5.75%** | $\le$ Baseline | **PASS** — **Wipeouts reduced across all pods** (-0.47% table avg) |
  | **Total Wipeout Rate (4P / 3P / 2P)** | 2.25% / 5.08% / 11.33% | **2.08% / 4.33% / 10.83%** | $\le$ Baseline | **PASS** — 4P wipeouts drop to 2.08%; zero early wipeouts ($\le 6$ rds) |
  | **End-Game: Singularity (4P / 3P / 2P)** | 4.5% / 7.1% / 8.9% | **4.7% / 8.2% / 8.2%** | Active clock | **PASS** — Macro clock preserved |
  | **End-Game: Patient Zero (4P / 3P / 2P)** | 70.3% / 64.0% / 39.3% | **73.8% / 65.2% / 43.5%** | Active pressure | **PASS** — Healthy attrition on overextended engines |
  | **End-Game: Market Collapse (4P / 3P / 2P)** | 22.9% / 23.8% / 40.4% | **19.4% / 22.3% / 37.5%** | Active condition | **PASS** — Active secondary terminal condition |
  | **Baffle Retention Rate** | 40.3% / 39.5% / 39.8% | **40.1% / 38.7% / 40.0%** | Model B Physics (~40%) | **PASS** — Verified physical baffle retention |
  | **Mean Baffle Hold Duration** | 0.48 / 0.48 / 0.48 | **0.48 / 0.47 / 0.49** | Latent threat delay | **PASS** — Multi-round suspense preserved |
  | **TL Cadence (Table / Seat-Game)** | 2.11 / 2.34 / 2.49 | **2.09 / 2.33 / 2.42** | ~2.00–2.50 / seat-game | **PASS** — Stable trigger frequency on Secret engines |
  | **4-Color Trigger Distribution** | N/A (+1 cube) | **G: 29.2%, K: 22.6%, B: 15.7%, R: 28.3%** | Balanced spread | **PASS** — Confirms Rank #1 mathematical model within $\pm 1\%$ |

- **Subroutine Mechanical Verification:**
  1. *Red (*Market Manipulation*):* In 4P, 2,960 Red signature attacks drained 5,616 actual Market Share and transferred 5,646 MS to non-locked trailing players. All-locked drops cleanly canceled transfers (4.6% in 4P, 13.9% in 3P, 38.5% in 2P), completely preventing turn-order ping-pong bugs.
  2. *Blue (*Buffer Congestion*):* 1,475 Gray Legacy dice moved to Processing Boxes in 4P (0.31/seat-game). All moved dice triaged out cleanly with 0 Secrets and zero re-queued signature cubes (`INV-SIG-BLUE-TRIAGE`).
  3. *Green (*Malware Encryption*):* Placed 5,201 track cubes in 4P; players completed 1,785 doubled-cost upgrades (`2x 🔬`), spending 2,087 extra 🔬. Only 12 saturation spillover glitched slots occurred table-wide across 1,200 games, confirming smooth track placement without track demotion exploits.
  4. *Black (*Root Override Hijack*):* Unused Client Company Overrides absorbed Black hits in **31.3%–33.0%** of cases, while the `-2 Corporate Secrets` fallback resolved in **67.0%–68.7%** of cases. Helix (*Brute-Force Bypass*) and DTO (*Slush Fund*) frequently held available overrides into Phase 4 Step 2, providing natural thematic defense.

- **Core Design Pillar Evaluations:**
  1. *Tactile & Thematic Central Board Drama:*
     - Players no longer face an abstract generic cube; Target Lock now triggers distinct, thematic operational crises (extortion, malware encryption, pipeline congestion, or root breach).
     - Preset priority order (`GREEN > BLACK > BLUE > RED`) eliminates all decision lag and cognitive friction while guaranteeing a balanced 4-color distribution.
  2. *Enhanced Archetype Equity & Compression of Runaway Turtles:*
     - In 4P pods, `SecOpsTurtleBot` win rate compressed by **-6.8%** (53.3% $\to$ 46.6%) as Black and Green attacks bypass shield-stacking turtle strategies.
     - Trailing archetypes gained substantial competitive equity: `VentureGreedBot` rose **+3.3%** (11.2% $\to$ 14.6%) and `AccelerationistBot` rose **+3.5%** (16.9% $\to$ 20.4%).
  3. *Client Company Parity Normalization:*
     - `Helix Biomedical Consortium` gained **+5.2%** win equity in 4P (16.0% $\to$ 21.3%) due to its unspent Phase 1 override absorbing Black hits.
     - Overall Client Company 4P win spread tightened from **14.2%** under `v0.42` to **13.3%** under `v0.43` (Omnidyne 31.2%, DTO 29.0%, Aegis 28.3%, Meridian 22.4%, Helix 21.3%, Prometheus 17.9%).

- **Official Balance Verdict: OFFICIALLY APPROVED (`v0.43.0 Baseline`).**
  Dominant Cube Color Signature Attacks successfully elevate Target Lock into an exciting, thematic, and balanced centerpiece mechanic. Pacing, wipeout guardrails, color parity, and archetype equity are 100% validated across 7,200 games. Recommended for full release synchronization across rules documentation, Print-and-Play assets, and quick-reference aids.

- **Official Balance Verdict: OFFICIALLY APPROVED (`v0.43.1`).**
  Synchronized across `RULES.md`, `RULES_APPENDIX.md`, `sim/` (`GameConfig.white_hat_6f_rebalance=True` in `v043()`), and `pnp/generate_pnp.py`.

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

## 62. Vulnerability Track Redesign: Post-Telemetry Balance Assessment (`v0.46.0` Defaults): APPROVED (residuals open)

**Experiments:**
- `scripts/run_v046_sweep.py` (Steps 1, 2 and 5: 1,200 games per pod, 2P / 3P / 4P, seeds `42..1241`, `mixed1` roster);
- `scripts/run_v046_dominance_matrix.py` (Step 3: 600 per cell, key cells 2,400);
- `scripts/run_reference_bot_validation.py --config v046_roster --cells ref1` (Step 4: 3P, 1,200).

Reports:
- `docs/reports/v046_steps1-3_sweeps.md`;
- `docs/reports/v046_balance_assessment.md` §0–§8;
- `docs/plans/vulnerability_track_gd_plan.md`;
- `docs/specs/vulnerability_track_spec.md`.

### Key Changes (`v0.46.0` vs `v0.45.0`)
1. **Vulnerability Track replaces shields.**
   - No shields, slots or Defense Grid. Red and Blue cubes are unblockable.
   - Each Green cube hits the player(s) highest on the Vulnerability Track, at 4+. It costs `1 / 2 / 3` Secrets at `4–6 / 7–9 / 10+`, then resets them to `0`. Vulnerability `0–3` is a true safe zone.
   - Face 5 (Secret) and one core face per colored die carry ⚠; Gray dice carry three.
2. **Pen Test Track** (replaces the Defense Grid Track):
   - spend `2 🔬` per `−1` Vulnerability (`[TUNE]`, tuned up from `1`);
   - L1 gives a Gray die;
   - L3 gives +1 Secret and Blue Secret faces yield +3;
   - L4 gives a free −1 per turn.
3. **Faces** (`V046_VULN_NOPREMIUM`):
   - the colored ⚠ faces are the v0.45 faces plus ⚠, with no +1 🔬 premium;
   - Gray F1 is `+$1 & +1 🔬` ⚠.
4. **Setup and cards:**
   - 5 starting Secrets;
   - Market Share starts at 14 / 18 / 18;
   - Blue is ×1 in `v3.0`;
   - *Data Scraper* gives `+1` Corporate Secret instead of `+$1`.
5. **Bots (sim-only):**
   - λ's future cost is one Pen Test step (`$1.75`), no longer capped by this round's risk;
   - Adaptive also cleans to below the target when it has spare research;
   - `p_exit` stays 0.60 and `secret_value` 3.0 (raising them played worse head-to-head).

### Telemetry & Balance Verdict (`PASS` with residuals)
- **Pacing and endings (2P / 3P / 4P):**
  - Mean rounds `8.20 / 7.77 / 7.51` (v0.45 `7.42 / 6.99 / 6.73`).
  - `v1.0` breach `10.1 / 15.9 / 16.5%` (v0.45 `12.0 / 18.8 / 22.0%`).
  - Patient Zero `36–62%` (v0.45 `49–79%`); Total Wipeout ≤ `5%`.
- **Green threat:** `2.42 / 2.08 / 1.86` Secrets lost per player-game (band `1.2–2.5`). The no-target rate rises with careful play (2P late game about `70%`).
- **Economy:** income (b) is `×1.12 / 1.08 / 1.08` against v0.45 (guardrail ≤ `×1.25`). 2+ L4 tracks: `0%` for the field.
- **Dominance:**
  - KeepAll `−4.3` to `−6.0`, RerollAllVuln `−7.2` to `−9.8`, PenTestRush `−4.5` to `+1.2` pp against an Adaptive field;
  - Adaptive `−2.5` to `+1.5` pp, keep rate `39–40%`.
  - The pre-tuning build had PenTestRush at `+5 / +10` pp (3P / 4P), fixed by the Pen Test cost of 2.
- **Reference bot (ref1):** `44.9%` (fair `33.3%`). That is the lowest on record (v0.36–v0.38: `66.6–78.6%`). Its stance mix is Adaptive `45%` / RerollAllVuln `26%` / KeepAll `24%` / PenTestRush `5.5%`, so there is no degenerate line. Watch: ref1 reaches 2+ L4 in `28%` of seats.
- **Key findings:**
  1. Early breaches were a **`v1.0` card asymmetry**, not a track issue. *Data Scraper*'s second Blue cube recycles every round once Blue is unblockable (breach `33–47%` vs *Script Kiddie* `8–11%`, before the +1 Secret fix).
  2. The rise in Singularity comes from games **surviving longer in `v3.0`** (Blue ×1, +1 starting Secret), not a faster fill. The v3.0 "track advance" table was an artefact of counting entry rounds.
  3. The original λ priced ⚠ at about `0` for any seat not near the top, so Adaptive kept more ⚠ than KeepAll did.
  4. A per-round Green telemetry bug filled V046 round fields only on each game's final round. Fixed.
  5. In v0.46 `1 🔬 ≈ $1` for decision purposes; the v0.45 probe rate (`🔬 ≈ 1.7 × $`) does not carry over.
- **Residuals:**
  - 4P Market Collapse `22.8%` (v0.45 `16.5 ±5`): accept, and restate the guardrail as Patient Zero + Collapse.
  - 4P company spread `15.7` pp (v0.45 about `16`; Blue companies lead, Aegis about `34%` at 4P, so the §12.6 watch item has triggered): company-power pass in v0.47.
  - Singularity `16–27%`: accept as the third ending.
  - *Data Scraper* games still run about `1.2` rounds shorter, with `3×` the breach of *Script Kiddie*: card pass later.
  - Gray and colored core ⚠ faces are rerolled most of the time: accepted by the User, and the per-face keep band is report-only.
- **Open User decisions:** `D1–D7` in `docs/reports/v046_balance_assessment.md` §8.4.
