# Technical Architecture Specification: Phase 33 (v0.26.0)
## Variable Module Dice Costs & Turn-1 Economic Calibration

**Author:** Principal Engineer / Architect  
**Status:** Approved for Implementation  
**Target Version:** `v0.26.0`  
**Dependencies:** [RULES.md](../../RULES.md), [PLAN.md](../../PLAN.md), [v250_technical_architecture_spec.md](./v250_technical_architecture_spec.md), [v240_technical_architecture_spec.md](./v240_technical_architecture_spec.md)  
**Target Components:**
- `sim/config.py`
- `sim/entities.py`
- `sim/engine/state.py`
- `sim/engine/phase3_ops.py`
- `sim/bots/base.py`
- `sim/bots/adaptive_balanced.py`
- `sim/bots/secops_turtle.py`
- `sim/bots/venture_greed.py`
- `sim/bots/accelerationist.py`
- `sim/bots/reckless_saboteur.py`
- `web/schemas.py`
- `web/controller/capabilities.py`
- `web/controller/phase3_actions.py`
- `web/static/js/components/market.js`
- `web/static/js/components/player_mats.js`
- `tests/test_v260_variable_dice_costs.py`

---

## 1. Executive Summary & Architectural Motivation

### 1.1 The Turn-1 Cash Glut & Snowball Anomaly
In physical and simulation playtesting of `v0.25.0`, players and bot agents experienced a notable economic distortion during early rounds. Under the legacy baseline, every corporation initialized with **$7 starting cash** (`GameConfig.starting_money = 7`). 

When combining this endowment with the expected monetary yield of the starting Gray (Legacy Code) dice pool (4 dice rolled during Phase 1 Boot):
- Gray Face 3: `+$1`
- Gray Face 4: `+$1`
- Gray Face 5: Choice `+$1 / +1 🔧` (EV: `+$0.50` when cash is prioritized)
- Starting Gray Cash EV: $4 \times \frac{1 + 1 + 0.5}{6} = 4 \times \frac{2.5}{6} \approx \$1.67$.
- With temporary contractor hiring and early hash matches (3-of-a-kind), average Turn-1 purchasing power reached **$8.50 to $9.50**.

Because Central Market software modules had static, flat prices (**$4** for Red/Green, **$5** for Blue/Yellow) and Personal Reserve Purple dice cost a flat **$4**:
1. **Turn-1 Double-Buys:** Players routinely purchased two colored dice on Round 1 (e.g., Red + Green for $\$4 + \$4 = \$8$, or Purple Reserve + Red for $\$4 + \$4 = \$8$).
2. **Prometheus Arbitrage Hyper-Escalation:** The Prometheus Foundation (*Algorithmic Arbitrage*) applied a flat $2 discount, enabling a discounted $2 die plus a full $4 die for only $6, leaving leftover cash even on bad rolls.
3. **Pacing & Survival Collapse:** Bypassing early-game financial scarcity enabled players to immediately erect dual shields and engine infrastructure, muting the escalating tension of Rogue Agent Version `v1.0` and causing runaway economic snowballing into `v2.0`.

### 1.2 Approved Architectural Decisions
Following design analysis and mathematical modeling signed off by the Game Designer and Product Owner, `v0.26.0` implements three structural calibrations:
1. **Starting Cash Recalibration (INV-START-CASH-01):** Default starting cash is calibrated from **$7 down to $4**.
2. **Dynamic Central Market Variant Costs (INV-VAR-COST-01):** Each purchasable colored die in the Central Market derives its cost directly from its active face-up `VariantCard` (`cost: int`):
   - **Red Modules:**
     - `R1` (*Packet Sniffer*): **$6**
     - `R2` (*Threat Bounty*): **$6**
     - `R3` (*Short Squeeze*): **$5**
   - **Blue Modules:**
     - `B1` (*Honeypot Telemetry*): **$6**
     - `B2` (*Deep R&D Vault*): **$7**
     - `B3` (*Air-Gapped Backup*): **$5**
   - **Green Modules:**
     - `G1` (*Self-Healing Kernel*): **$6**
     - `G2` (*Universal Sandbox*): **$5**
     - `G3` (*Live Reboot*): **$5**
   - **Yellow Modules:**
     - `Y1` (*Algorithmic Trading*): **$7**
     - `Y2` (*Venture Subvention*): **$6**
     - `Y3` (*Yield Farm*): **$6**
3. **Dynamic Purple Personal Reserve Procurement Costs (INV-RES-COST-01):** The procurement cost of private Purple Specialist dice is decoupled from flat market costs and assigned directly to the player's active `WhiteHat` operative dossier (`reserve_cost: int`):
   - **The Acoustic** (*Mainframe Resonance*): **$4**
   - **The Phreaker** (*Emergency Relays*): **$4**
   - **The Operator** (*Contractor Dispatch*): **$5**
   - **The Prodigy** (*Lock Bypassing*): **$5**
   - **The Spook** (*OpSec & Slush Funds*): **$5**
   - **The Cipher** (*Algorithmic Parity*): **$6**
4. **Dynamic Algorithmic Arbitrage (INV-PROMETHEUS-01):** Prometheus Foundation's Once-per-Version override applies its $2 discount dynamically against the target die's variant cost or operative reserve cost: $\max(0, \text{cost} - 2)$.
5. **Entity Cost Binding (INV-DIE-COST-01):** When any colored die is instantiated via `create_colored_die`, its `die.cost` property must match the active variant or operative reserve cost.

```
+-----------------------------------------------------------------------------------------+
|                               PHASE 33 ECONOMIC RECALIBRATION                           |
+-----------------------------------------------------------------------------------------+
|  Starting Cash: $7  -->  $4 (INV-START-CASH-01)                                          |
|                                                                                         |
|  [Central Market Variants]               [White Hat Personal Reserves]                 |
|  • Red:    R1 ($6), R2 ($6), R3 ($5)     • The Acoustic: $4   • The Prodigy: $5         |
|  • Blue:   B1 ($6), B2 ($7), B3 ($5)     • The Phreaker: $4   • The Spook:   $5         |
|  • Green:  G1 ($6), G2 ($5), G3 ($5)     • The Operator: $5   • The Cipher:  $6         |
|  • Yellow: Y1 ($7), Y2 ($6), Y3 ($6)                                                    |
|                                                                                         |
|  Turn 1 Capital EV: $4 starting + ~$1.67 Gray EV = ~$5.67                               |
|  --> Guarantees 1 high-value die purchase, eliminating degenerate Round 1 double-buys.   |
+-----------------------------------------------------------------------------------------+
```

### 1.3 Architectural Goals & Core Pillars
1. **Zero Hardcoded Cost Constants:** Eliminate all occurrences of hardcoded constants (such as `4 if color in (RED, GREEN) else 5` or `cost = 4`) across the simulation engine, bot heuristics, and web controllers. All pricing must resolve dynamically from `VariantCard` or `WhiteHat`.
2. **Turn-1 Pacing Protection:** Ensure Turn-1 purchasing behavior requires strategic prioritization between single high-cost modules ($6–$7), budget modules ($4–$5), contractor hiring ($1), or cash conservation for upcoming compiler threats.
3. **Strict Invariant Governance:** All purchase operations, discount calculations, entity initializations, and UI representations are validated against formal invariant codes (`INV-START-CASH-01`, `INV-VAR-COST-01`, `INV-RES-COST-01`, `INV-PROMETHEUS-01`, `INV-DIE-COST-01`).
4. **Clean Decoupled Orthogonality:** Market variant cards govern central stacks; White Hat operative dossiers govern private purple reserves. Neither entity couples to the other, preserving the modular architecture established in Phase 32.
5. **Seamless Backward Compatibility:** Provide explicit fallbacks in `create_colored_die` and serializers so that unadorned calls or legacy tests lacking explicit variant bindings default safely to baseline variant costs without exceptions.

---

## 2. Formal System Invariants & Mathematical Guarantees

### 2.1 Formal Invariant Definitions

The following formal system invariants govern Phase 33 variable costs, starting resources, market transactions, and entity state:

| Invariant ID | Subsystem | Formal Invariant Specification |
| :--- | :--- | :--- |
| **INV-START-CASH-01** | Setup & Configuration | **Default Starting Cash Calibration:** Every player terminal MUST initialize with exactly `$4` starting cash (`GameConfig.starting_money == 4`), unless explicitly overridden by an active Version Card starting bonus (e.g., `Data Scraper +$1` yielding `$5`) or explicit test configuration. |
| **INV-VAR-COST-01** | Entities & Market | **Dynamic Variant Die Pricing:** Every `VariantCard` instance MUST possess an immutable integer property `cost: int` strictly $> 0$. The procurement cost of any Central Market die color $C \in \{\text{RED}, \text{BLUE}, \text{GREEN}, \text{YELLOW}\}$ in `GameState` MUST equal `state.variant_cards[C].cost`. |
| **INV-RES-COST-01** | Entities & Reserve | **Dynamic Operative Reserve Pricing:** Every `WhiteHat` operative dossier MUST possess an immutable integer property `reserve_cost: int` strictly $> 0$. The procurement cost of a Purple Specialist die from a player's Personal Reserve MUST equal `player.white_hat.reserve_cost`. |
| **INV-PROMETHEUS-01** | Operations Engine | **Dynamic Arbitrage Discount:** When activating the Prometheus Foundation Once-per-Version override (*Algorithmic Arbitrage*), the effective purchase price of target die $D$ MUST be computed dynamically as $\max(0, \text{Cost}(D) - \text{cipher\_market\_discount})$, where $\text{cipher\_market\_discount} = 2$. This applies identically whether $D$ is a Central Market die or a Personal Reserve Purple die. |
| **INV-DIE-COST-01** | Entity Construction | **Die Entity Cost Synchronization:** When instantiating any `Die` instance via `create_colored_die(color, ...)`, `die.cost` MUST accurately reflect the active pricing: for market colors, the active `variant_card.cost`; for Purple, the operative's `reserve_cost`; for Gray starter dice, `0`; for White contractor dice, `1`. |
| **INV-MARKET-01** | Operations Engine | **Market Purchasing Validation:** Purchasing a Central Market die of color $C$ is valid if and only if: (1) `player.is_patient_zero is False`, (2) `purchases_this_turn < max_market_purchases_per_turn`, (3) `state.market[C] > 0`, and (4) `player.money >= effective_cost`. Upon successful execution, `player.money` decrements by `effective_cost`, `state.market[C]` decrements by 1, `purchases_this_turn` increments by 1, and the created `Die` is appended directly to `player.ready_for_release_dice`. |
| **INV-PURPLE-02** | Operations Engine | **Personal Reserve Procurement Validation:** Procuring a Purple die from Personal Reserve is valid if and only if: (1) `player.is_patient_zero is False`, (2) `purchases_this_turn < max_market_purchases_per_turn`, (3) `player.personal_purple_reserve > 0`, and (4) `player.money >= effective_cost`. Upon successful execution, `player.money` decrements by `effective_cost`, `player.personal_purple_reserve` decrements by 1, `purchases_this_turn` increments by 1, and the created `Die` is appended directly to `player.ready_for_release_dice`. |

---

### 2.2 Mathematical Calibration & Turn-1 Affordability Analysis

Under the calibrated baseline ($4 starting cash):
- **Starting Cash:** $4.00
- **Phase 1 Gray Dice Roll Expected Value:**
  $$E[\text{Cash}] = 4 \times \left( \frac{0 + 0 + 1 + 1 + 0.5 + 0}{6} \right) = 4 \times \frac{2.5}{6} \approx \$1.67$$
- **Mean Available Capital in Phase 3 Operations (Round 1):**
  $$\overline{M}_1 = \$4.00 + \$1.67 = \$5.67$$

#### Purchasing Scenarios Under Calibrated Costs:
1. **Single Module Purchase ($5–$7):**
   - High-tier variants (`B2` at $7, `Y1` at $7, `R1` at $6, `B1` at $6, `G1` at $6, `The Cipher` Purple at $6) require rolling at least one or two cash faces on Gray dice.
   - Standard variants (`R3` at $5, `B3` at $5, `G2` at $5, `G3` at $5, `The Operator` Purple at $5, `The Prodigy` Purple at $5, `The Spook` Purple at $5) require rolling at least one cash face ($4 + $1 = $5).
   - Budget variants (`The Acoustic` Purple at $4, `The Phreaker` Purple at $4) are 100% affordable on Turn 1 even with 0 cash rolled.
2. **Double Module Purchases:**
   - The absolute minimum cost for two dice without abilities is two $4 dice (e.g. Acoustic Purple $4 + Phreaker Purple $4, which is impossible since a player only has one operative reserve; or Acoustic Purple $4 + budget $5 variant = $9).
   - Two market dice minimum cost is $\$5 + \$5 = \$10$ (`R3` + `G2` or `B3` + `G3`).
   - To achieve $10 on Turn 1, a player would need $4 starting + maximum possible roll ($4 from 4 cash faces) + 3-of-a-kind hash match or contractor bonus ($2), which occurs in $< 0.8\%$ of games.
3. **Prometheus Algorithmic Arbitrage Double Buy:**
   - With Prometheus $2 discount, the cheapest pairing is a $4 Purple die (discounted to $2) + a $5 market die = $\$2 + \$5 = \$7$.
   - Achieving $7 requires $4 starting + $3 from rolls/contractors. This turns what was previously an effortless turn-1 double buy into an intentional, risk-weighted tactical achievement.

---

### 2.3 Master Dynamic Cost Reference Matrix

#### Table 1: Central Market Software Modules (`VariantCard.cost`)

| Die Color | Variant Code | Variant Card Name | Calibrated Cost | Mechanical Rationale & Power Budget |
| :--- | :--- | :--- | :--- | :--- |
| **RED** | `R1` | Packet Sniffer | **$6** | High offense/defense: 2 Red Shields + potential +$2 bonus. Premium threat dampener. |
| **RED** | `R2` | Threat Bounty | **$6** | Economy + Defense: 2 Red Shields + conditional +$2 bounty. High snowball potential. |
| **RED** | `R3` | Short Squeeze | **$5** | Pure cash engine: Flat +$3 (or +$4 if 3+ Red exit). Fast payback, baseline cost. |
| **BLUE** | `B1` | Honeypot Telemetry | **$6** | 2 Blue Shields + conditional +$3 cash payout. Premium defense against Blue leaks. |
| **BLUE** | `B2` | Deep R&D Vault | **$7** | Game-winning late-game Secret engine: Pay $4 for +1 Corporate Secret. Most powerful engine card. |
| **BLUE** | `B3` | Air-Gapped Backup | **$5** | Wear-loop redirection: 1 Blue Shield that deflects wear to sacrificial dice. Highly accessible defense. |
| **GREEN** | `G1` | Self-Healing Kernel | **$6** | 2 Green Shields + 1 Wrench token. Premium defense against malware. |
| **GREEN** | `G2` | Universal Sandbox | **$5** | 1 Wildcard (ANY) Shield + 1 Wrench token. Extremely versatile baseline defense. |
| **GREEN** | `G3` | Live Reboot | **$5** | Fast triage: +2 Wrench tokens + +$1 cash. Essential repair booster. |
| **YELLOW** | `Y1` | Algorithmic Trading | **$7** | Massive +$4 cash injection OR direct +1 Corporate Secret purchase ($2 net). Top-tier market engine. |
| **YELLOW** | `Y2` | Venture Subvention | **$6** | Escalating dirty dividend: +$2 to +$5 cash based on unblocked damage. Strong early-to-mid capital. |
| **YELLOW** | `Y3` | Yield Farm | **$6** | Steady compound interest: +$3 cash + 1 Wrench token. Solid dual-resource yield. |

#### Table 2: White Hat Operative Personal Reserves (`WhiteHat.reserve_cost`)

| Operative Code | Operative Dossier Name | Face 6 Signature Protocol | Reserve Cost | Balance Rationale & Protocol Strength |
| :--- | :--- | :--- | :--- | :--- |
| `ACOUSTIC` | The Acoustic | *Resonance Sensor* | **$4** | Passive threat forecasting and tower echo detection; baseline entry pricing. |
| `PHREAKER` | The Phreaker | *Jumper Diagnostics* | **$4** | Hardware triage harvesting cash/patches from Under Development dice. |
| `OPERATOR` | The Operator | *Contingent Staffing* | **$5** | Immediate tempo: rolls 1 free White Contractor die during Phase 1 Boot. |
| `PRODIGY` | The Prodigy | *Arbitrary Code Execution*| **$5** | Unconditional face manipulation: alters any rolled die to any legal non-Star face. |
| `SPOOK` | The Spook | *Burn Notice* | **$5** | Secret generation: burns owned dice directly for +1 Corporate Secret. |
| `CIPHER` | The Cipher | *Algorithmic Parity* | **$6** | Unrivaled economy: Wildcard 3-of-a-kind Secret parity + Phase 3A +$2 cash injection. Premium tier. |

---

## 3. Data Model & Schema Architecture

### 3.1 Configuration Updates (`sim/config.py`)

In `sim/config.py`, line 53, update `starting_money` default to `4`:

```python
@dataclass
class GameConfig:
    """Tunable game parameters with baselines from RULES.md."""

    # Player count & setup
    num_players: int = 4
    starting_money: int = 4  # [v0.26.0 Calibration: Calibrated from $7 to $4 (INV-START-CASH-01)]
    starting_secrets_by_player_count: Dict[int, int] = field(
        default_factory=lambda: {2: 8, 3: 8, 4: 12}
    )
    ...
```

---

### 3.2 Entity Updates (`sim/entities.py`)

#### 3.2.1 `VariantCard` Dataclass
Add immutable integer field `cost: int` to `VariantCard` (line 167):

```python
@dataclass(frozen=True)
class VariantCard:
    """Defines the Special (★) face behavior and dynamic cost for a colored die type."""

    code: str  # e.g., "R1", "B3"
    name: str
    die_color: DieColor
    description: str
    star_face: Face
    cost: int = 4  # [v0.26.0 Baseline: Dynamic market cost per variant card (INV-VAR-COST-01)]
```

#### 3.2.2 `VariantCard` Registry Updates in `get_all_variant_cards()`
Update each card instantiation with its explicit calibrated cost:
- `R1`: `cost=6`
- `R2`: `cost=6`
- `R3`: `cost=5`
- `B1`: `cost=6`
- `B2`: `cost=7`
- `B3`: `cost=5`
- `G1`: `cost=6`
- `G2`: `cost=5`
- `G3`: `cost=5`
- `Y1`: `cost=7`
- `Y2`: `cost=6`
- `Y3`: `cost=6`
- *(Legacy Purple variants P1, P2, P3 retained with `cost=4` for backward compatibility).*

#### 3.2.3 `WhiteHat` Dataclass
Add immutable integer field `reserve_cost: int` to `WhiteHat` (line 80):

```python
@dataclass(frozen=True)
class WhiteHat:
    """Represents a White Hat Operative dossier card assigned to the terminal."""

    code: WhiteHatCode
    name: str
    role: str
    protocol_name: str
    timing_window: str
    description: str
    flavor: str
    reserve_cost: int = 4  # [v0.26.0 Baseline: Personal Reserve Purple die cost (INV-RES-COST-01)]
```

#### 3.2.4 `WHITE_HATS` Registry Updates
Update `WHITE_HATS` dictionary definitions with calibrated operative reserve costs:
- `ACOUSTIC`: `reserve_cost=4`
- `PHREAKER`: `reserve_cost=4`
- `OPERATOR`: `reserve_cost=5`
- `PRODIGY`: `reserve_cost=5`
- `SPOOK`: `reserve_cost=5`
- `CIPHER`: `reserve_cost=6`

#### 3.2.5 `create_colored_die` Function Signature & Implementation
Refactor `create_colored_die` (line 1093) to dynamically assign `die.cost` from the active `variant_card` or `reserve_cost`:

```python
def create_colored_die(
    color: DieColor,
    die_id: int,
    variant_card: Optional[VariantCard] = None,
    reserve_cost: Optional[int] = None,
) -> Die:
    """Creates a colored die of the specified color with dynamic cost (v0.26.0 Baseline)."""
    if color == DieColor.GRAY:
        return create_gray_die(die_id)
    if color == DieColor.WHITE:
        return create_white_die(die_id)

    star_face = variant_card.star_face if variant_card else Face(name=f"{color.value} ★", is_star=True)
    var_code = variant_card.code if variant_card else None
    glitch_face = Face(name="Glitch (Locked)", is_glitch=True)

    # Derive dynamic cost with safe default fallbacks
    if color == DieColor.PURPLE:
        die_cost = reserve_cost if reserve_cost is not None else (
            variant_card.cost if variant_card is not None else 4
        )
    else:
        if variant_card is not None:
            die_cost = variant_card.cost
        else:
            # Fallback default costs if variant card is omitted:
            # Red default R1: $6, Blue default B1: $6, Green default G1: $6, Yellow default Y1: $7
            default_costs = {
                DieColor.RED: 6,
                DieColor.BLUE: 6,
                DieColor.GREEN: 6,
                DieColor.YELLOW: 7,
            }
            die_cost = default_costs.get(color, 4)

    if color == DieColor.RED:
        faces = [
            Face(name="Block 1 Red", block_amount=1, shield_color=ShieldColor.RED),
            Face(name="+$2", money=2),
            Face(name="+$2", money=2),
            Face(name="+$2", money=2),
            glitch_face,
            star_face,
        ]
        return Die(die_id=die_id, color=color, cost=die_cost, vp=0, faces=faces, variant_code=var_code)

    elif color == DieColor.BLUE:
        faces = [
            Face(name="Block 1 Blue", block_amount=1, shield_color=ShieldColor.BLUE),
            Face(name="+1 🔧", patches=1),
            Face(name="+$1", money=1),
            Face(
                name="Block 1 Blue / +1 🔧",
                is_choice=True,
                choices=(
                    Face("Block 1 Blue", block_amount=1, shield_color=ShieldColor.BLUE),
                    Face("+1 🔧", patches=1),
                ),
            ),
            glitch_face,
            star_face,
        ]
        return Die(die_id=die_id, color=color, cost=die_cost, vp=0, faces=faces, variant_code=var_code)

    elif color == DieColor.GREEN:
        faces = [
            Face(name="Block 1 Green", block_amount=1, shield_color=ShieldColor.GREEN),
            Face(name="+1 🔧", patches=1),
            Face(name="+2 🔧", patches=2),
            Face(
                name="+1 🔧 / +$1",
                is_choice=True,
                choices=(
                    Face("+1 🔧", patches=1),
                    Face("+$1", money=1),
                ),
            ),
            glitch_face,
            star_face,
        ]
        return Die(die_id=die_id, color=color, cost=die_cost, vp=0, faces=faces, variant_code=var_code)

    elif color == DieColor.YELLOW:
        faces = [
            Face(name="+$3", money=3),
            Face(name="+$2", money=2),
            Face(name="+$2", money=2),
            Face(name="+$1 & +1 🔧", money=1, patches=1),
            glitch_face,
            star_face,
        ]
        return Die(die_id=die_id, color=color, cost=die_cost, vp=0, faces=faces, variant_code=var_code)

    elif color == DieColor.PURPLE:
        star_face = Face(
            name="Purple ★",
            is_star=True,
            star_code="PURPLE_STAR",
        )
        faces = [
            Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY),
            Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY),
            Face(name="+$2", money=2),
            Face(name="+$1 & +1 🔧", money=1, patches=1),
            glitch_face,
            star_face,
        ]
        return Die(die_id=die_id, color=color, cost=die_cost, vp=0, faces=faces, variant_code="PURPLE_STAR")

    raise ValueError(f"Unsupported die color: {color}")
```

---

### 3.3 State Model Updates (`sim/engine/state.py`)

#### 3.3.1 `GameState.get_market_die_cost(color: DieColor) -> int`
Add a canonical lookup method on `GameState` to safely extract dynamic market pricing:

```python
def get_market_die_cost(self, color: DieColor) -> int:
    """Returns the dynamic cost of a Central Market die based on the active variant card."""
    if color in self.variant_cards:
        return self.variant_cards[color].cost
    # Fallback default costs if variant cards not registered:
    default_costs = {
        DieColor.RED: 6,
        DieColor.BLUE: 6,
        DieColor.GREEN: 6,
        DieColor.YELLOW: 7,
    }
    return default_costs.get(color, 4)
```

#### 3.3.2 `PlayerState.get_purple_reserve_cost() -> int`
Add a canonical lookup method on `PlayerState` to safely extract dynamic operative reserve pricing:

```python
def get_purple_reserve_cost(self) -> int:
    """Returns the dynamic procurement cost for this player's Personal Purple Reserve."""
    if self.white_hat is not None:
        return getattr(self.white_hat, "reserve_cost", 4)
    return 4
```

---

## 4. Simulation Engine Lifecycle Integration

### 4.1 Phase 3 Part 3A Operations Refactoring (`sim/engine/phase3_ops.py`)

All hardcoded pricing checks in `sim/engine/phase3_ops.py` must be completely replaced by dynamic calls to `get_market_die_cost` and `get_purple_reserve_cost`.

#### 4.1.1 Prometheus Algorithmic Arbitrage Resolution
In `execute_phase_3` (around lines 200–226):

```python
# 2. Prometheus Foundation Institutional Override: Algorithmic Arbitrage
if use_prom and prom_mode in ("BUY_FREE_DIE", "DISCOUNT_DIE") and is_prometheus and free_color is not None:
    # Derive target cost dynamically based on die target
    if free_color == DieColor.PURPLE:
        target_cost = player.get_purple_reserve_cost()
    else:
        target_cost = engine.state.get_market_die_cost(free_color)

    discounted_cost = max(0, target_cost - engine.state.config.cipher_market_discount)

    if free_color == DieColor.PURPLE:
        if player.personal_purple_reserve > 0 and player.money >= discounted_cost:
            player.money -= discounted_cost
            player.personal_purple_reserve -= 1
            new_die = create_colored_die(
                color=DieColor.PURPLE,
                die_id=engine.state.next_die_id,
                reserve_cost=player.get_purple_reserve_cost(),
            )
            engine.state.next_die_id += 1
            player.ready_for_release_dice.append(new_die)
            player.mark_ability_used(active_ver)
            prometheus_discount_applied = True
    elif engine.state.market.get(free_color, 0) > 0 and player.money >= discounted_cost:
        player.money -= discounted_cost
        engine.state.market[free_color] -= 1
        new_die = create_colored_die(
            color=free_color,
            die_id=engine.state.next_die_id,
            variant_card=engine.state.variant_cards.get(free_color),
        )
        engine.state.next_die_id += 1
        player.ready_for_release_dice.append(new_die)
        player.mark_ability_used(active_ver)
        prometheus_discount_applied = True
```

#### 4.1.2 Standard Market & Personal Reserve Purchases
In `execute_phase_3` (around lines 300–335):

```python
# 4. Market Purchases (Limit 2 dice per turn; deliver directly to ready_for_release_dice)
purchased_count = 1 if prometheus_discount_applied else 0
purchases_list = list(plan.market_purchases)
if plan.buy_purple_reserve and DieColor.PURPLE not in purchases_list:
    purchases_list.append(DieColor.PURPLE)

for color in purchases_list:
    if purchased_count >= engine.state.config.max_market_purchases_per_turn:
        break

    if color == DieColor.PURPLE:
        cost = player.get_purple_reserve_cost()
        if player.personal_purple_reserve > 0 and player.money >= cost:
            player.money -= cost
            player.personal_purple_reserve -= 1
            purchased_count += 1
            new_die = create_colored_die(
                color=DieColor.PURPLE,
                die_id=engine.state.next_die_id,
                reserve_cost=cost,
            )
            engine.state.next_die_id += 1
            player.ready_for_release_dice.append(new_die)
    else:
        cost = engine.state.get_market_die_cost(color)
        if engine.state.market.get(color, 0) > 0 and player.money >= cost:
            player.money -= cost
            engine.state.market[color] -= 1
            purchased_count += 1
            new_die = create_colored_die(
                color=color,
                die_id=engine.state.next_die_id,
                variant_card=engine.state.variant_cards.get(color),
            )
            engine.state.next_die_id += 1
            player.ready_for_release_dice.append(new_die)
```

---

## 5. Bot AI Heuristics & Decision Engine

### 5.1 Abstract Base Bot Updates (`sim/bots/base.py`)

#### 5.1.1 Dynamic Purple Reserve Decision
In `BaseBot.choose_purple_reserve_purchase` (lines 571–584):

```python
def choose_purple_reserve_purchase(
    self,
    player_state: PlayerState,
    game_state: GameState,
    rng: random.Random,
) -> bool:
    """Determines whether to purchase a Purple die from Personal Reserve using dynamic operative cost."""
    if getattr(player_state, "personal_purple_reserve", 0) <= 0:
        return False
    reserve_cost = player_state.get_purple_reserve_cost()
    if player_state.money < reserve_cost:
        return False
    # Baseline heuristic: Buy if cash reserves allow and ready dice pool is small
    return len(player_state.ready_for_release_dice) < 5 or player_state.money >= (reserve_cost * 2)
```

### 5.2 Bot Subclass Updates (`sim/bots/`)

The 5 bot subclasses (`adaptive_balanced.py`, `secops_turtle.py`, `venture_greed.py`, `accelerationist.py`, `reckless_saboteur.py`) must be updated to query `game_state.get_market_die_cost(c)` and `player_state.get_purple_reserve_cost()` rather than relying on hardcoded constants.

#### 5.2.1 Prometheus Arbitrage Selection Pattern
Across all bot subclasses, update Prometheus discount candidate evaluation:

```python
# Dynamic Prometheus Evaluation
discounted_colors = []
candidate_pool = preferred_colors + [DieColor.BLUE, DieColor.RED, DieColor.GREEN, DieColor.YELLOW]
for c in candidate_pool:
    if c not in [dc[0] for dc in discounted_colors] and game_state.market.get(c, 0) > 0:
        base_cost = game_state.get_market_die_cost(c)
        cost = max(0, base_cost - game_state.config.cipher_market_discount)
        if current_money - cost >= cash_cushion:
            discounted_colors.append((c, cost))

# Check Purple Reserve candidate for Prometheus discount
if getattr(player_state, "personal_purple_reserve", 0) > 0:
    base_purple_cost = player_state.get_purple_reserve_cost()
    disc_purple_cost = max(0, base_purple_cost - game_state.config.cipher_market_discount)
    if current_money - disc_purple_cost >= cash_cushion:
        discounted_colors.append((DieColor.PURPLE, disc_purple_cost))
```

#### 5.2.2 Market Purchase Decision Loop Pattern
Across all bot subclasses, update the Phase 3 purchase loop:

```python
# 4. Market Purchases with Dynamic Costs
if not is_final_round:
    purchases = 0
    purple_cost = player_state.get_purple_reserve_cost()
    if (
        purchases < game_state.config.max_market_purchases_per_turn
        and self.choose_purple_reserve_purchase(player_state, game_state, rng)
        and (current_money - purple_cost >= cash_cushion)
    ):
        plan.market_purchases.append(DieColor.PURPLE)
        plan.buy_purple_reserve = True
        current_money -= purple_cost
        purchases += 1

    for color in preferred_colors:
        if purchases >= game_state.config.max_market_purchases_per_turn:
            break
        cost = game_state.get_market_die_cost(color)
        if game_state.market.get(color, 0) > 0 and (current_money - cost >= cash_cushion):
            plan.market_purchases.append(color)
            current_money -= cost
            purchases += 1
```

---

## 6. Web API, Controller, & Frontend Architecture

### 6.1 Schema Serializers (`web/schemas.py`)

#### 6.1.1 `serialize_variant_card`
Expose `cost: card.cost` in `serialize_variant_card` (line 93):

```python
@staticmethod
def serialize_variant_card(card: VariantCard) -> Dict[str, Any]:
    return {
        "code": card.code,
        "name": card.name,
        "die_color": card.die_color.value,
        "description": card.description,
        "star_face": GameStateSerializer.serialize_face(card.star_face),
        "cost": card.cost,  # Added in v0.26.0 (INV-VAR-COST-01)
    }
```

#### 6.1.2 `serialize_white_hat`
Expose `reserve_cost: white_hat.reserve_cost` in `serialize_white_hat` (line 147):

```python
@staticmethod
def serialize_white_hat(white_hat: Optional[WhiteHat]) -> Optional[Dict[str, Any]]:
    if white_hat is None:
        return None
    return {
        "code": white_hat.code.value if hasattr(white_hat.code, "value") else str(white_hat.code),
        "name": white_hat.name,
        "role": white_hat.role,
        "protocol_name": white_hat.protocol_name,
        "timing_window": white_hat.timing_window,
        "description": white_hat.description,
        "flavor": white_hat.flavor,
        "reserve_cost": getattr(white_hat, "reserve_cost", 4),  # Added in v0.26.0 (INV-RES-COST-01)
    }
```

#### 6.1.3 `serialize_player`
Expose `purple_reserve_cost` and dynamic `can_buy_purple_reserve` in `serialize_player` (lines 314–319):

```python
# Personal Reserve (v0.24.0 / v0.26.0)
purple_reserve_cost = player.get_purple_reserve_cost() if hasattr(player, "get_purple_reserve_cost") else (
    getattr(player.white_hat, "reserve_cost", 4) if player.white_hat else 4
)
data["personal_purple_reserve"] = getattr(player, "personal_purple_reserve", 2)
data["purple_reserve_cost"] = purple_reserve_cost
data["can_buy_purple_reserve"] = (
    getattr(player, "personal_purple_reserve", 2) > 0
    and player.money >= purple_reserve_cost
    and purchases_this_turn < getattr(config, "max_market_purchases_per_turn", 2)
)
```

#### 6.1.4 `serialize_game_state` Market Payload
Extract market cost dynamically in `serialize_game_state` (lines 340–355):

```python
market_serialized = {
    color.value: {
        "stock": state.market.get(color, 0),
        "cost": state.get_market_die_cost(color),  # Dynamic lookup per INV-VAR-COST-01
        "vp": 0,
        "variant": cls.serialize_variant_card(state.variant_cards[color])
        if color in state.variant_cards
        else None,
    }
    for color in [
        DieColor.RED,
        DieColor.BLUE,
        DieColor.GREEN,
        DieColor.YELLOW,
    ]
}
```

---

### 6.2 Controller Capabilities (`web/controller/capabilities.py`)

#### 6.2.1 `can_buy` & `can_cipher_buy` Resolution
Refactor capability evaluation (lines 109–127 and 220–237) to determine affordability dynamically:

```python
# Market purchase availability per color
can_buy = {}
can_cipher_buy = {}
for color in [DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW, DieColor.PURPLE]:
    if color == DieColor.PURPLE:
        base_cost = player.get_purple_reserve_cost()
        has_stock = getattr(player, "personal_purple_reserve", 0) > 0
    else:
        base_cost = controller.state.get_market_die_cost(color)
        has_stock = controller.state.market.get(color, 0) > 0

    disc_cost = max(0, base_cost - controller.state.config.cipher_market_discount)

    can_buy[color.value] = bool(
        controller.phase == 3
        and not can_confirm_income
        and is_active
        and not is_eliminated
        and meta["purchases_this_turn"] < controller.state.config.max_market_purchases_per_turn
        and has_stock
        and player.money >= base_cost
    )

    can_cipher_buy[color.value] = bool(
        controller.phase == 3
        and not can_confirm_income
        and is_active
        and not is_eliminated
        and is_cipher
        and ability_avail
        and meta["purchases_this_turn"] < controller.state.config.max_market_purchases_per_turn
        and has_stock
        and player.money >= disc_cost
    )

can_buy_purple_reserve = bool(can_buy.get("purple", False))
```

---

### 6.3 Controller Action Execution (`web/controller/phase3_actions.py`)

In `buy_module` (lines 516–585):

```python
color = DieColor(color_str.lower())
if color == DieColor.PURPLE:
    base_cost = player.get_purple_reserve_cost()
else:
    base_cost = controller.state.get_market_die_cost(color)

cost = base_cost
use_discount = use_cipher_ability or use_prometheus_override
if use_discount:
    has_prometheus = bool(
        (player.company and player.company.code == CompanyCode.PROMETHEUS)
        or (player.archetype and player.archetype.code == ArchetypeCode.CIPHER)
    )
    if not has_prometheus:
        raise ValueError("Player does not have the Prometheus company override or Cipher archetype")
    if not player.is_ability_available():
        raise ValueError("Prometheus/Cipher ability is not available")
    cost = max(0, base_cost - controller.state.config.cipher_market_discount)

if color == DieColor.PURPLE:
    if player.personal_purple_reserve <= 0:
        raise ValueError(f"Personal Purple Reserve is depleted (remaining: {player.personal_purple_reserve})")
    if player.money < cost:
        raise ValueError(f"Insufficient funds: Purple Reserve die costs ${cost}, but player only has ${player.money}")

    player.money -= cost
    player.personal_purple_reserve -= 1
    meta["purchases_this_turn"] += 1

    new_die = create_colored_die(
        color=DieColor.PURPLE,
        die_id=controller.state.next_die_id,
        reserve_cost=player.get_purple_reserve_cost(),
    )
    controller.state.next_die_id += 1
    player.ready_for_release_dice.append(new_die)
    ...
```

---

### 6.4 Web Frontend UI Updates

#### 6.4.1 Software Module Market Card (`web/static/js/components/market.js`)
The market component already computes `effectiveCost` as:
```javascript
const effectiveCost = cipherDiscountSelected ? Math.max(0, item.cost - 2) : item.cost;
```
Because `item.cost` will now be derived dynamically from `state.market[color].cost`, the market slot UI automatically displays `$5`, `$6`, or `$7` according to the active variant card. Add a variant cost pill `.variant-cost-badge` inside the variant slot header to highlight the active pricing to human players.

#### 6.4.2 Player Terminal Personal Reserve Badge (`web/static/js/components/player_mats.js`)
Update lines 684, 688, and 692 to bind directly to `p.purple_reserve_cost || 4` rather than hardcoding `$4`:
```javascript
const reserveCost = p.purple_reserve_cost !== undefined ? p.purple_reserve_cost : 4;
...
<span class="slot-wrench-icon" style="color: #c084fc;">
  ${(p.personal_purple_reserve !== undefined ? p.personal_purple_reserve : 2) >= 1 ? `▼ $${reserveCost}` : '✓'}
</span>
...
${p.can_buy_purple_reserve ? `<strong style="color: #c084fc;">CLICK TO PROCURE ($${reserveCost})</strong>` : 'Private Reserve | Dual-Shield & Face 6 Protocol'}
```

---

## 7. Comprehensive Verification Matrix & Unit Test Plan

A dedicated, comprehensive unit test suite MUST be authored at `tests/test_v260_variable_dice_costs.py`. The suite must contain at least 25 distinct unit tests verifying all invariants, pricing tables, discount arithmetic, entity states, bot decisions, and API responses.

### 7.1 Test Matrix Specification

| Test ID | Method Name | Target Invariant | Assertion Requirements |
| :--- | :--- | :--- | :--- |
| **TEST-VAR-01** | `test_default_starting_cash_is_four` | `INV-START-CASH-01` | Instantiate `GameEngine()`; verify `player.money == 4` for all players. Verify `GameConfig().starting_money == 4`. |
| **TEST-VAR-02** | `test_version_cash_bonus_stacks_on_four` | `INV-START-CASH-01` | Initialize engine with Data Scraper (`starting_cash_bonus=1`); verify players start with `$5`. |
| **TEST-VAR-03** | `test_all_variants_have_positive_costs` | `INV-VAR-COST-01` | Iterate `get_all_variant_cards()`; assert `isinstance(v.cost, int)` and `v.cost > 0` for all 12 market variants. |
| **TEST-VAR-04** | `test_red_variant_costs` | `INV-VAR-COST-01` | Assert `R1.cost == 6`, `R2.cost == 6`, `R3.cost == 5`. |
| **TEST-VAR-05** | `test_blue_variant_costs` | `INV-VAR-COST-01` | Assert `B1.cost == 6`, `B2.cost == 7`, `B3.cost == 5`. |
| **TEST-VAR-06** | `test_green_variant_costs` | `INV-VAR-COST-01` | Assert `G1.cost == 6`, `G2.cost == 5`, `G3.cost == 5`. |
| **TEST-VAR-07** | `test_yellow_variant_costs` | `INV-VAR-COST-01` | Assert `Y1.cost == 7`, `Y2.cost == 6`, `Y3.cost == 6`. |
| **TEST-VAR-08** | `test_all_white_hats_have_reserve_costs` | `INV-RES-COST-01` | Iterate `get_all_white_hats()`; assert `isinstance(w.reserve_cost, int)` and `w.reserve_cost > 0` for all 6 operatives. |
| **TEST-VAR-09** | `test_operative_reserve_cost_calibration` | `INV-RES-COST-01` | Assert `ACOUSTIC.reserve_cost == 4`, `PHREAKER.reserve_cost == 4`, `OPERATOR.reserve_cost == 5`, `PRODIGY.reserve_cost == 5`, `SPOOK.reserve_cost == 5`, `CIPHER.reserve_cost == 6`. |
| **TEST-VAR-10** | `test_game_state_get_market_die_cost` | `INV-VAR-COST-01` | Set active variant cards to `R3`, `B2`, `G1`, `Y1`; verify `get_market_die_cost` returns `5, 7, 6, 7`. |
| **TEST-VAR-11** | `test_player_state_get_purple_reserve_cost` | `INV-RES-COST-01` | Pair player with `The Cipher`; assert `get_purple_reserve_cost() == 6`. Pair with `The Acoustic`; assert `== 4`. |
| **TEST-VAR-12** | `test_create_colored_die_binds_variant_cost`| `INV-DIE-COST-01` | Call `create_colored_die` with `B2`; assert `die.cost == 7`. Call with `R3`; assert `die.cost == 5`. |
| **TEST-VAR-13** | `test_create_colored_die_binds_reserve_cost`| `INV-DIE-COST-01` | Call `create_colored_die` for PURPLE with `reserve_cost=6`; assert `die.cost == 6`. |
| **TEST-VAR-14** | `test_create_colored_die_fallback_defaults` | `INV-DIE-COST-01` | Call `create_colored_die` with `variant_card=None`; assert Red=6, Blue=6, Green=6, Yellow=7, Gray=0, White=1. |
| **TEST-VAR-15** | `test_phase3_market_purchase_deducts_exact_cost` | `INV-MARKET-01` | Set active Blue to `B2` ($7). Player has $7; buy Blue; assert `player.money == 0`, `stock == stock - 1`, die in `ready_for_release`. |
| **TEST-VAR-16** | `test_phase3_market_purchase_rejects_insufficient_funds` | `INV-MARKET-01` | Set active Blue to `B2` ($7). Player has $6; assert purchase fails / die not bought. |
| **TEST-VAR-17** | `test_phase3_purple_purchase_deducts_operative_cost` | `INV-PURPLE-02` | Player with `The Prodigy` ($5) has $5; procure purple; assert `player.money == 0`, `personal_purple_reserve == 1`. |
| **TEST-VAR-18** | `test_phase3_purple_purchase_rejects_insufficient_funds` | `INV-PURPLE-02` | Player with `The Cipher` ($6) has $5; assert purple procurement fails; reserve remains 2. |
| **TEST-VAR-19** | `test_prometheus_discount_on_high_tier_market_die` | `INV-PROMETHEUS-01`| Active `B2` ($7). Prometheus activates discount; assert purchase price is `max(0, 7 - 2) = $5`. |
| **TEST-VAR-20** | `test_prometheus_discount_on_budget_market_die` | `INV-PROMETHEUS-01`| Active `R3` ($5). Prometheus activates discount; assert purchase price is `max(0, 5 - 2) = $3`. |
| **TEST-VAR-21** | `test_prometheus_discount_on_purple_reserve` | `INV-PROMETHEUS-01`| Player with Prometheus + `The Cipher` ($6); procure Purple; assert cost is `max(0, 6 - 2) = $4`. |
| **TEST-VAR-22** | `test_prometheus_discount_on_budget_purple_reserve` | `INV-PROMETHEUS-01`| Player with Prometheus + `The Acoustic` ($4); procure Purple; assert cost is `max(0, 4 - 2) = $2`. |
| **TEST-VAR-23** | `test_bot_base_purple_reserve_heuristic` | Bot AI | Assert `choose_purple_reserve_purchase` returns `False` if cash < operative reserve cost. |
| **TEST-VAR-24** | `test_adaptive_balanced_bot_respects_variant_costs` | Bot AI | Run bot Phase 3 planning with $5 cash and $6 Red market die; assert bot does not plan purchase. |
| **TEST-VAR-25** | `test_web_serializer_variant_card_cost` | Web API | Call `GameStateSerializer.serialize_variant_card(B2)`; assert output dictionary contains `"cost": 7`. |
| **TEST-VAR-26** | `test_web_serializer_white_hat_reserve_cost` | Web API | Call `GameStateSerializer.serialize_white_hat(CIPHER)`; assert output contains `"reserve_cost": 6`. |
| **TEST-VAR-27** | `test_web_serializer_game_state_market_costs` | Web API | Call `serialize_game_state`; assert `market["blue"]["cost"]` reflects active variant cost. |
| **TEST-VAR-28** | `test_web_serializer_player_purple_reserve_cost` | Web API | Call `serialize_player`; assert `purple_reserve_cost` matches operative and `can_buy_purple_reserve` checks dynamic cost. |
| **TEST-VAR-29** | `test_web_controller_buy_action_dynamic_cost` | Web Controller | Execute `/api/game/action/buy` with Blue `B2` ($7); verify `$7` deducted from player cash. |
| **TEST-VAR-30** | `test_web_controller_purple_buy_action_dynamic_cost` | Web Controller | Execute `/api/game/action/buy` with `purple` under `The Spook` ($5); verify `$5` deducted. |

---

## 8. Multi-Agent SDLC Gate & Execution Sequence

Following sign-off of this technical specification, implementation proceeds through the multi-agent SDLC pipeline:

```
[Principal Engineer] Author Technical Architecture Spec (Phase 33, v0.26.0)  <-- CURRENT
        |
        v
[Senior Engineer] Implement Dynamic Costs across Entities, Engine, Bots, Web, and Unit Suite
        |
        v
[Staff Engineer] Line-by-Line Code Review & WSL Test Gate Verification
        |
        v
[Product Owner] Execute Comparative Monte Carlo Verification Sweeps & Pacing Telemetry
        |
        v
[Game Designer] Pacing Evaluation, Early Scarcity Confirmation, RULES.md & FINDINGS.md Log
        |
        v
[Graphic Designer] Synchronize PnP Component Card Rendering (pnp/generate_pnp.py)
```

1. **Gate 1 (`principal-engineer`):** Deliver comprehensive technical architecture specification `docs/specs/v260_variable_dice_costs_spec.md` with explicit invariants, data models, and verification matrix — **COMPLETED**.
2. **Gate 2 (`senior-engineer`):**
   - Calibrate `starting_money = 4` in `sim/config.py`.
   - Update `VariantCard` and `WhiteHat` dataclasses and registries in `sim/entities.py`.
   - Update `create_colored_die` and entity cost properties.
   - Refactor `sim/engine/state.py` and `sim/engine/phase3_ops.py` to remove hardcoded cost constants.
   - Update bot heuristics across `sim/bots/` to evaluate dynamic pricing.
   - Synchronize `web/schemas.py`, `web/controller/capabilities.py`, `web/controller/phase3_actions.py`, and frontend JavaScript.
   - Implement dedicated unit test suite `tests/test_v260_variable_dice_costs.py`.
3. **Gate 3 (`staff-engineer`):** Perform strict line-by-line code review, verify zero hardcoded cost constants, audit Prometheus discount edge cases, and confirm 100% test pass via WSL.
4. **Gate 4 (`product-owner`):** Execute a 3,000-match Monte Carlo sweep across 2P, 3P, and 4P pods comparing `v0.25.0` vs `v0.26.0`, measuring Turn-1 purchase distribution, pacing stability, and survival rates.
5. **Gate 5 (`game-designer`):** Verify that Turn-1 double-buys are eradicated, early-game economic tension is restored, update `RULES.md` Section 6 and log Section 21 in `FINDINGS.md`.
6. **Gate 6 (`graphic-designer`):** Update `pnp/generate_pnp.py` to reflect variable costs on variant cards and White Hat dossier reserve badges, regenerating all Print-and-Play assets.
