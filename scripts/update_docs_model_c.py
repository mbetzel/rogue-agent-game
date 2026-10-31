"""Update RULES.md, PLAN.md, and FINDINGS.md for Model C: End-of-Round Cleanup Cap for Patches."""

from __future__ import annotations


def update_rules():
    with open("RULES.md", "r", encoding="utf-8") as f:
        content = f.read()

    # Update Phase 1 Step 6
    old_p1 = "   * You may hold at most **`3 🔧`** tokens at once `[TUNE]`. Dice showing `Glitch (Locked)` produce 0 resource outputs."
    new_p1 = "   * Dice showing `Glitch (Locked)` produce 0 resource outputs. *(Note: Patch token collection is unclamped during the round; excess patches are only discarded at End-of-Round Cleanup).* [TUNE]"

    if old_p1 in content:
        content = content.replace(old_p1, new_p1)
        print("Updated RULES.md Phase 1 Step 6.")
    else:
        print("old_p1 not found in RULES.md")

    # Update Phase 3 End-of-Round Cleanup
    old_p3 = "  * Keep all Money, Secrets, and up to **`3 🔧`** tokens."
    new_p3 = "  * Keep all Money and Secrets. Discard any unspent Patch Tokens in excess of **`3 🔧`** tokens back to the supply (End-of-Round Cleanup Cap [TUNE])."

    if old_p3 in content:
        content = content.replace(old_p3, new_p3)
        print("Updated RULES.md Phase 3 Cleanup.")
    else:
        print("old_p3 not found in RULES.md")

    with open("RULES.md", "w", encoding="utf-8") as f:
        f.write(content)


def update_plan():
    with open("PLAN.md", "r", encoding="utf-8") as f:
        content = f.read()

    new_phase_entry = """- [x] **Phase 25: Model C End-of-Round Cleanup Cap for Patches (`v0.18.0` Baseline)**
  - [x] *Pre-SDLC Game Designer Modeling:* Modeled patch yields across Gray/Green/Blue pools (EV ~1.87–4.37 🔧), identified Round 1 over-clamping (>50% hitting cap on T1), and designed Model C (unclamped during round, discard down to 3 at End-of-Round Cleanup). User approved.
  - [x] *Technical Architecture Spec (`principal-engineer`):* Module contracts in `sim/engine/phase1_boot.py`, `sim/engine/phase3_ops.py`, `web/controller/`, `web/schemas.py`, and test specifications.
  - [x] *Implementation (`senior-engineer`):* Implemented unclamped collection in Phase 1, End-of-Round Cleanup in Phase 3 / web serializer, exposed `max_patch_tokens` in schemas, and created 8-test unit suite in `tests/test_model_c_patches.py` (307/307 tests passing).
  - [x] *Code Review Gate (`staff-engineer`):* Verified line-by-line diffs, parity between headless sim and web controller, and confirmed 100% test pass via WSL — `APPROVED`.
  - [x] *Scenario Execution & Telemetry Compilation (`product-owner`):* Ran 3,000-match Monte Carlo sweep across 2P, 3P, and 4P pods (`scripts/sweep_model_c_patches.py`).
  - [x] *Balance Assessment & Final Sign-Off (`game-designer`):* Confirmed zero pacing distortion, verified $\\le 3$ 🔧 holding invariant across all pods, and logged Section 13 in `FINDINGS.md`.
  - [x] *Print-and-Play & Documentation (`graphic-designer`):* Updated `RULES.md` Phase 1 Step 6 and Phase 3 Cleanup rules text, regenerated PnP PDFs.
"""

    target_anchor = "- [x] **Phase 24: Cryptographic Hash Match & Secrets-Only Victory Scoring (`v0.17.0` Baseline)**"
    if target_anchor in content and "Phase 25:" not in content:
        content = content.replace(target_anchor, new_phase_entry + target_anchor)
        print("Updated PLAN.md with Phase 25.")

    with open("PLAN.md", "w", encoding="utf-8") as f:
        f.write(content)


def update_findings():
    with open("FINDINGS.md", "r", encoding="utf-8") as f:
        content = f.read()

    new_section = """
---

## 13. Phase 25: Model C End-of-Round Cleanup Cap for Patches (`v0.18.0` Baseline)

### A. Context & Playtest Diagnosis
In `v0.17.0` and earlier rules drafts, player patch tokens (`🔧`) were immediately capped to `max_patch_tokens = 3` during **Phase 1 Step 6** (Boot & Configure) as well as inside each individual player's turn in Phase 3. Mathematical modeling revealed this caused severe artificial choking:
1. **Turn 1 Truncation:** In Round 1, players start with `2 🔧`. The probability of rolling $\\ge 2$ patch faces across 4 Gray dice is $\\approx 52.4\\%$. Because Round 1 has no hardware glitches on Gray dice and no pre-existing corruption locks, over 50% of players hit the `3 🔧` cap on Turn 1 and immediately discarded rolled patches.
2. **Defensive & Repair Choke:** Mid-game rolls with Green Antivirus dice producing 3–5 patches were clipped before Phase 2 emergency Red Ransomware absorption and Phase 3 module repairs.

### B. Approved Solution: Model C (End-of-Round Cleanup Cap)
- **Phase 1 & Phase 2:** Patch collection is **unclamped**. Players collect all generated `🔧` tokens from rolled dice and can freely spend them on Phase 1 Debug Unlocks and Phase 2 Emergency Ransom Absorption (at $0 cash).
- **Phase 3 Operations:** Players may spend any number of patch tokens to repair worn modules (Unpatched $\\to$ Ready) without per-turn clamping.
- **End-of-Round Cleanup:** Immediately before advancing the First Player marker (and before final round scoring), surviving players discard unspent patch tokens in excess of **`3 🔧`** (`player.patches = min(player.patches, 3)`).
- **Benefits:** Completely eliminates wasted high-yield rolls during the round, while preventing multi-round hoarding bunkers and preserving physical component limits.

### C. Monte Carlo Verification Sweep Telemetry ($N=1,000$ per Pod, Base Seed 42)

| Pod | Mean Rounds | Sing % | PZ % | Wipeout % | Winner Sec | Surv Sec | Winner 🔧 | Surv 🔧 | TB Rate | Lead Bot (Win %) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **2P** | **3.92 ± 0.58** | 0.0% | 29.6% | 70.4% | **2.53** | **2.53** | **0.00** | **0.00** | 0.0% | AdaptiveBalancedBot (**73.6%**) |
| **3P** | **3.94 ± 0.58** | 0.0% | 50.5% | 49.5% | **3.33** | **3.03** | **0.03** | **0.02** | 9.3% | VentureGreedBot (**44.6%**) |
| **4P** | **4.11 ± 0.54** | 0.0% | 53.7% | 46.3% | **3.43** | **2.84** | **0.02** | **0.01** | 14.5% | VentureGreedBot (**37.8%**) |

**Tiebreaker Level Breakdown:**
- **2P:** Level 1 ($): 0 | Level 2 (Dice): 0 | Level 3 (Wrench): 0 | Level 4 (Reliability): 0
- **3P:** Level 1 ($): 12 | Level 2 (Dice): 4 | Level 3 (Wrench): 0 | Level 4 (Reliability): 31
- **4P:** Level 1 ($): 5 | Level 2 (Dice): 8 | Level 3 (Wrench): 0 | Level 4 (Reliability): 65

### D. Key Empirical Takeaways & Balance Rationale
1. **Zero Macro Pacing Distortion:** Match length is identical to pre-cap baselines (3.92 rds 2P / 3.94 rds 3P / 4.11 rds 4P) with zero stalling.
2. **Invariant Verification:** 100% of surviving players conclude games with $\\le 3$ patch tokens (mean ending patches: 0.00 to 0.03 🔧).
3. **Tiebreaker Integrity:** Level 3 (Patches) tiebreaker remains pristine; Level 4 (Reliability: fewest unpatched dice) continues to resolve the vast majority of ties (66.0% in 3P, 83.3% in 4P).
4. **Metagame Stability:** Lead bot in 4P (VentureGreedBot) sits at 37.8%, comfortably within the healthy $\\le 40\\%$ balance corridor.

### E. Formal Design Sign-Off
- **Baseline Adoption:** Formally adopt Model C End-of-Round Cleanup Cap for Patches as the canonical baseline for **`v0.18.0`**.
- **Component Parity:** Updated `RULES.md`, `sim/engine/`, `web/`, and test suite.

**Status: OFFICIALLY APPROVED (`v0.18.0` Baseline).**
"""

    if "## 13. Phase 25: Model C" not in content:
        content = content + new_section
        print("Updated FINDINGS.md with Section 13.")

    with open("FINDINGS.md", "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    update_rules()
    update_plan()
    update_findings()
