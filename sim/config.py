"""Configuration, constants, and tunable parameters for Rogue Agent simulation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Dict, Optional, Tuple

_ALL_TRACK_LEVELS = (0, 1, 2, 3, 4)
# v0.37.0 [TUNE] (FINDINGS §38 / §39): Market Leader Bonus by Market Share place, and starting Corporate Secrets
V037_MARKET_LEADER_BONUS = {2: (2, 0), 3: (2, 1, 0), 4: (2, 1, 0, 0)}
V037_STARTING_SECRETS = {2: 9, 3: 8, 4: 9}
# --- v0.38.0 candidate (docs/specs/v380_secret_faces_processing_box_spec.md) ---
V038_COMPANY_STARTING_COLORS = {  # [TUNE] OQ-4 (User 2026-11-07)
    "MERIDIAN": "RED", "PROMETHEUS": "RED",
    "DTO": "BLUE", "AEGIS": "BLUE",
    "OMNIDYNE": "GREEN", "HELIX": "GREEN",
}
V038_STARTING_SECRETS = {2: 5, 3: 5, 4: 5}  # [TUNE] OQ-1 (User 2026-11-07)
V038_MARKET_SHARE_START = {2: 12, 3: 12, 4: 12}
V038_PR_REGAIN_COST = 3  # [TUNE] OQ-9 follow-up: 3 research per +1 Market Share (v0.37: 2)
_FACE_PROFILES = ("V037", "V038_DRAFT")
# die_face_profile only: V038_DRAFT with the candidate-2 Yellow table (spec §14.3); _ALT = F1 "+$1 & +1 Market Share"
# _F3 = V038_YELLOW_MS with Yellow F3 "+$1 & +1 Market Share" (spec §14.5.1, RSP-1)
V038_DIE_FACE_PROFILES = ("V038_DRAFT", "V038_YELLOW_MS", "V038_YELLOW_MS_ALT", "V038_YELLOW_MS_F3", "V038D", "V038F")
_DIE_FACE_PROFILES = ("V037",) + V038_DIE_FACE_PROFILES
V038B_STARTING_SECRETS = {2: 3, 3: 4, 4: 4}  # [TUNE] §14.3
V038B_RED_TIERS = ((11, 3), (7, 2), (3, 1), (0, 0))  # [TUNE] §14.3
V038B_MARKET_SHARE_START = {2: 14, 3: 14, 4: 14}  # [TUNE] §14.4 (start = max)
V038B_MARKET_LEADER_BONUS = {2: (4, 0), 3: (4, 2, 0), 4: (4, 2, 0, 0)}  # [TUNE] §14.4
V038C_MARKET_SHARE_START = {2: 13, 3: 16, 4: 17}  # [TUNE] §14.5.2 / FINDINGS §43.5 (start = max)
V038C_RED_SECRET_PAYOUT = {2: (3, 1), 3: (3, 1, 0), 4: (3, 1, 0, 0)}  # [TUNE] §14.5.2
# --- Tunable Defaults for Headroom Architecture (spec: market_share_headroom_spec.md) ---
V038E_MARKET_SHARE_START: Dict[int, int] = {2: 13, 3: 16, 4: 16}  # Unified 3P and 4P at 16
DEFAULT_MARKET_SHARE_MAX: int = 20
_TRIAGE_ORDER_RULES = ("BOT", "OLDEST_FIRST")
_TRIAGE_L1_MODES = ("WHITE_CONTRACTORS", "GRAY_DIE")
_GREEN_TRIAGE_CLEAN_MODES = ("NONE", "COUNT_THEN_CLEAN", "CLEAN_THEN_COUNT")
_MERIDIAN_OVERRIDE_MODES = ("REDUNDANT_CREW", "CAPITAL_INJECTION")
_OPERATOR_PROTOCOL_MODES = ("CONTINGENT_STAFFING", "LOGISTICS_BOUNTY")


class CubeColor(str, Enum):
    RED = "red"
    BLUE = "blue"
    GREEN = "green"
    BLACK = "black"


class DieColor(str, Enum):
    GRAY = "gray"
    WHITE = "white"
    RED = "red"
    BLUE = "blue"
    GREEN = "green"
    YELLOW = "yellow"
    PURPLE = "purple"


class ShieldColor(str, Enum):
    RED = "red"
    BLUE = "blue"
    GREEN = "green"
    ANY = "any"


class TowerMode(str, Enum):
    LEDGE_AVALANCHE = "ledge_avalanche"
    FLAT_BINOMIAL = "flat_binomial"
    SHOGUN_BAFFLE = "shogun_baffle"


class EndGameReason(str, Enum):
    NONE = "none"
    SINGULARITY = "singularity"
    PATIENT_ZERO = "patient_zero"
    TOTAL_WIPEOUT = "total_wipeout"
    ROUND_LIMIT = "round_limit"
    MARKET_COLLAPSE = "market_collapse"  # v0.36.0: a survivor at 0 Market Share after Phase 4 -> Final Round


class RoundSequence(str, Enum):
    """Round structure selector (v0.34.0).

    V033_THREE_PHASE: legacy v0.33 round (Roll & Deploy / Compiler Drop & Defense / Operations & Pipeline Prep),
    kept for regression and parity tests. SIX_PHASE: the canonical v0.34 six-phase round.
    """

    V033_THREE_PHASE = "V033_THREE_PHASE"
    SIX_PHASE = "SIX_PHASE"


class ResearchTrackModel(str, Enum):
    """Research track / company setup ruleset selector (v0.35.0).

    V034_THREE_LEVEL: v0.34.0 tracks (L0-L2, Emergency Hotfix / Passive Firewall, purchasable Purple,
    Client Company setup bonuses, old Gray faces, Slush Fund once per version). Kept for regression and parity.
    V035_FIVE_LEVEL: canonical v0.35.0 (L0-L4 tracks with Breakthroughs at L1 / L3).
    """

    V034_THREE_LEVEL = "V034_THREE_LEVEL"
    V035_FIVE_LEVEL = "V035_FIVE_LEVEL"


class RedMode(str, Enum):
    """Red attack ruleset master switch (v0.36.0).

    RANSOM: v0.35.0 (each unblocked Red cube costs Money; shortfall -> Unpaid Ransom Leak).
    MARKET_SHARE: v0.36.0 Market Manipulation (each unblocked Red cube lowers Market Share by 1).
    """

    RANSOM = "RANSOM"
    MARKET_SHARE = "MARKET_SHARE"


class PatentsMode(str, Enum):
    """Fourth research track ruleset (internal key stays ``"PATENT"``).

    PATENTS: v0.35 Cryptographic Patents Track + Patent Filing.
    SHARE_REGAIN: v0.36 Public Relations Track (Phase 6: spend research to regain Market Share).
    """

    PATENTS = "PATENTS"
    SHARE_REGAIN = "SHARE_REGAIN"


class RedVariantSet(str, Enum):
    """Red Variant (★) Card set. V035: R1/R2/R3 of v0.35. MARKETING: Brand Protection / Ad Campaign / Customer Poaching."""

    V035 = "V035"
    MARKETING = "MARKETING"


class TiebreakOrder(str, Enum):
    """V035: Secrets > Money > ... ; MARKET_SHARE_FIRST: Secrets > Market Share > Money > ..."""

    V035 = "V035"
    MARKET_SHARE_FIRST = "MARKET_SHARE_FIRST"


class AnyShieldPolicy(str, Enum):
    """Stage 2 Generic (Any) shield allocation. V035_TIERS: engine 4-tier priority. FREE_CHOICE: player/bot split."""

    V035_TIERS = "V035_TIERS"
    FREE_CHOICE = "FREE_CHOICE"


class RoundPhase(IntEnum):
    """Canonical six-phase round (v0.34.0). GAME_OVER is used by the web state machine only."""

    ROLL_AND_DEPLOY = 1
    COMPILER_DROP_AND_CORRUPTION = 2
    INCOME = 3
    ATTACK_RESOLUTION = 4
    CICD_PIPELINE_SHIFT = 5
    OPERATIONS = 6
    GAME_OVER = 7


# Single source of truth for phase display names (web controller, PnP aid).
ROUND_PHASE_NAMES: Dict[int, str] = {
    1: "Roll & Deploy",
    2: "Compiler Drop & Corruption",
    3: "Income",
    4: "Attack Resolution",
    5: "CI/CD Pipeline Shift",
    6: "Operations",
    7: "Game Over",
}


@dataclass(frozen=True)
class PrPushParams:
    """[TUNE-BOT] Lever A thresholds (docs/specs/lever_a_roster_upgrade_spec.md §2). Sim-only, not a rule.

    Read by ``sim/bots/pr_push_policy.py`` when ``GameConfig.bot_pr_push`` is on. Frozen because rollout
    clones share ``config`` by reference (H-LA-5)."""

    push_min_share: int = 6  # PUSH_MIN_SHARE
    push_low_gap: int = 7  # PUSH_LOW_GAP
    push_top_gap: int = 3  # PUSH_TOP_GAP
    push_max_version: int = 1  # PUSH_MAX_VERSION (Version index; 1 = v2.0)
    push_secrets_band: int = 2  # PUSH_SECRETS_BAND
    push_pr_cap: int = 1  # PUSH_PR_CAP (Public Relations Track level)
    push_max_research: int = 2  # PUSH_MAX_RESEARCH (Research Tokens on hand)
    dump_max_share: int = 5  # DUMP_MAX_SHARE
    dump_top_gap: int = 2  # DUMP_TOP_GAP (variant only)
    dump_threat_margin: int = 2  # DUMP_THREAT_MARGIN (variant only)
    dump_condition: str = "share_only"  # "share_only" (default) | "reach_or_threat" (sweep variant)
    push_blue_slack: int = 0  # PUSH_BLUE_SLACK: Blue blocks the push split may give up vs the default (0 = Blue-safe)

    def validate(self) -> None:
        if self.dump_condition not in ("share_only", "reach_or_threat"):
            raise ValueError(f"dump_condition must be 'share_only' or 'reach_or_threat', got {self.dump_condition!r}")
        for name in ("push_min_share", "push_max_version", "push_secrets_band", "push_pr_cap",
                     "push_max_research", "dump_max_share", "dump_threat_margin", "push_blue_slack"):
            v = getattr(self, name)
            if not isinstance(v, int) or v < 0:
                raise ValueError(f"PrPushParams.{name} must be an int >= 0, got {v!r}")
        for name in ("push_low_gap", "push_top_gap", "dump_top_gap"):
            if not isinstance(getattr(self, name), int):
                raise ValueError(f"PrPushParams.{name} must be an int")
        if not self.push_min_share > self.dump_max_share:
            raise ValueError("PUSH_MIN_SHARE must exceed DUMP_MAX_SHARE (windows must be disjoint)")


@dataclass
class GameConfig:
    """Tunable game parameters with baselines from RULES.md."""

    # Player count & setup
    num_players: int = 4
    starting_money: int = 6  # [v0.30.0 Baseline: Calibrated from $4 to $6 (INV-START-CASH-01)]
    # [v0.34.0 Baseline: Flat 8 Secrets at every player count (INV-START-SECRETS-FLAT-01).
    #  None resolves in __post_init__: SIX_PHASE -> {2: 8, 3: 8, 4: 8}; V033_THREE_PHASE -> {2: 8, 3: 8, 4: 12}]
    starting_secrets_by_player_count: Optional[Dict[int, int]] = None
    starting_patches_by_player_count: Dict[int, int] = field(
        default_factory=lambda: {2: 0, 3: 0, 4: 0}  # [v0.30.0 Baseline: Calibrated from 2 to 0 (INV-START-RES-01)]
    )
    starting_secrets: Optional[int] = None  # Optional scalar override for backwards compatibility
    starting_patches: Optional[int] = None  # Optional scalar override for backwards compatibility
    max_patch_tokens: int = 3  # [TUNE: 3] Maximum unspent patch tokens retained across rounds during End-of-Round Cleanup (Model C)
    starting_gray_dice: int = 3   # [v0.30.0 Baseline: Calibrated from 4 to 3 (INV-START-POOL-01)]
    starting_purple_dice: int = 1 # [v0.30.0 Baseline: 1 starter Purple die (INV-START-POOL-01)]
    starting_purple_reserve: int = 1 # [v0.30.0 Baseline: Option A 1 die in reserve (INV-PURPLE-RES-01)]
    dice_per_color_multiplier: int = 2  # 2 * num_players dice per colored die type

    # Corruption track (v0.15.0 Per-Version Escalating Tracks)
    corruption_track_profile: str = "STANDARD"  # "STANDARD" (Profile 1) or "AGGRESSIVE" (Profile 2)
    corruption_cubes_resolve_immediately: bool = False  # Mode A (False): Staging Cup; Mode B (True): immediate tray attack for R/B/G
    corruption_track_lengths: Dict[str, int] = field(
        default_factory=lambda: {"v1.0": 4, "v2.0": 5, "v3.0": 6}
    )
    corruption_track_capacity_by_player_count: Dict[int, int] = field(
        default_factory=lambda: {2: 4, 3: 5, 4: 6}
    )
    corruption_track_flat_capacity: Optional[int] = None  # Scalar override for backwards compatibility / tests
    corruption_spaces_per_player: int = 1  # Deprecated in v0.4
    corruption_spaces_base: int = 1  # Deprecated in v0.4

    # Autonomous AI Pulse by Version (v0.21.0 Baseline: 1 Black cube/round across all versions)
    autonomous_pulse_by_version: Dict[str, int] = field(
        default_factory=lambda: {"v1.0": 1, "v2.0": 1, "v3.0": 1}
    )

    # Operations & Economy
    cipher_arbitrage_cash: int = 2  # [TUNE: v0.16.0] Cipher Phase 3 alternate cash arbitrage payout
    patch_ransom_absorption: bool = False  # Deprecated in v0.21.0 (Emergency patch absorption eliminated; Red ransom is strictly cash-only)
    dirty_income_enabled: bool = False  # Deprecated in v0.16.0 (Dirty income eliminated)
    dirty_income_cash: int = 3  # Deprecated
    dirty_income_secret_cost: int = 1  # Deprecated
    dirty_income_attack_cubes: int = 0  # Deprecated
    dirty_income_black_cubes: int = 1  # Deprecated
    patch_cash_cost: int = 2  # [TUNE: $1–$3]
    patch_token_cost: int = 1
    max_market_purchases_per_turn: int = 2  # [TUNE: 2]
    max_rounds: int = 30  # Safety cap for simulation termination

    # Temp Staffing & Yahtzee Rerolls (v0.6 / v0.7)
    contractor_hire_cost: int = 1
    contractor_cost_progression: Tuple[int, ...] = (1, 2, 3)
    contractor_max_hire: int = 3
    contractor_supply_total: int = 12
    default_free_rerolls: int = 2
    throttled_free_rerolls: int = 1

    # Corporate Asymmetry & Hardware Tracks (v0.28.0)
    enable_corporate_asymmetry: bool = False  # When True, applies Company-specific hardware and starting resource modifiers

    # Variant & Boss Tunables (Phase 10)
    y2_base_payout: int = 2
    y2_max_payout: int = 5
    b2_secret_cost: int = 4
    b2_secret_cap: Optional[int] = None
    p3_cube_cash_cost: int = 1
    corrupted_kernel_black_threshold: int = 2
    corrupted_kernel_strength_bonus: int = 2
    cipher_market_discount: int = 2  # [TUNE: v0.9.1] $2 discount on 1 colored die purchase

    # Cube Tower mechanics
    tower_mode: TowerMode = TowerMode.LEDGE_AVALANCHE
    tower_flat_exit_prob: float = 0.70  # [0.60–0.80]
    tower_ledge_capacity: float = 5.0
    tower_base_exit_prob: float = 0.60
    tower_avalanche_scale: float = 0.05  # Extra exit probability per cube above capacity
    # Shogun Cube Tower Two-State Baffle Physics (Calibrated Model B)
    tower_empty_exit_prob: float = 0.70  # Empty tower falling pass-through (S = 0)
    tower_obstruction_alpha: float = 0.15  # Reduction in falling pass-through per stuck cube (sub-avalanche)
    tower_min_fall_prob: float = 0.35  # Floor on sub-avalanche falling pass-through
    tower_trapping_dislodge_prob: float = 0.21  # Dislodge probability for resting cubes when F > 0 (sub-avalanche)
    tower_avalanche_fall_prob: float = 0.60  # Falling pass-through during avalanche
    tower_avalanche_dislodge_prob: float = 0.70  # Resting cube dislodgement probability during avalanche
    tower_avalanche_stuck_threshold: int = 3  # S >= 3 triggers avalanche cascade when F > 0
    tower_avalanche_mass_threshold: int = 7  # F + S >= 7 triggers avalanche cascade when F > 0

    # Compiler Priming & Buffer Overflow (v0.9.1 Baseline)
    enable_compiler_priming: bool = True
    compiler_priming_cubes: Dict[CubeColor, int] = field(
        default_factory=lambda: {
            CubeColor.RED: 1,
            CubeColor.BLUE: 1,
            CubeColor.GREEN: 1,
            CubeColor.BLACK: 1,
        }
    )
    enable_buffer_overflow: bool = True
    buffer_overflow_cubes: Dict[CubeColor, int] = field(
        default_factory=lambda: {
            CubeColor.RED: 1,
            CubeColor.BLUE: 1,
            CubeColor.GREEN: 1,
        }
    )

    # Scoring weights (Portfolio Value - v0.19.0 Pure Corporate Secrets Victory Scoring)
    vp_per_secret: int = 1
    vp_per_die: Dict[DieColor, int] = field(
        default_factory=lambda: {
            DieColor.GRAY: 0,
            DieColor.WHITE: 0,
            DieColor.RED: 0,
            DieColor.BLUE: 0,
            DieColor.GREEN: 0,
            DieColor.YELLOW: 0,
            DieColor.PURPLE: 0,
        }
    )
    vp_cash_divisor: int = 0  # Deprecated in v0.19.0 (Cash is Tiebreaker #1, not direct VP)

    # Total Wipeout Overflow Penalties (v0.19.0: Elimination of Fictitious Wipeout Bonuses)
    overflow_penalty_per_secret_debt: int = -1  # -1 VP per Secret breach depth below 0
    overflow_penalty_per_cash_debt: int = 0  # Obsolete in v0.3 (cash >= 0)
    overflow_penalty_per_unfulfilled_destroyed_die: int = 0  # Deprecated in v0.31.0 (INV-MALWARE-FIZZLE-01)

    # Round structure (v0.34.0): SIX_PHASE (canonical) or V033_THREE_PHASE (legacy regression path)
    round_sequence: RoundSequence = RoundSequence.SIX_PHASE
    # v0.33 bug kept only for legacy parity: White Hats also granted their paired company's Institutional
    # Override (and companies the paired Signature Protocol). True only via GameConfig.legacy_v033().
    legacy_archetype_override_bridge: bool = False

    # --- v0.35.0 Research Tracks (INV-RT-*) ---
    research_track_model: ResearchTrackModel = ResearchTrackModel.V035_FIVE_LEVEL
    track_step_costs: Tuple[int, int, int, int] = (1, 1, 2, 2)  # [TUNE] cost to reach L1..L4 (total 6 🔬 per track)
    max_hardware_upgrades_per_turn: int = 2  # [TUNE: 2] max hardware track upgrades per Operations Turn
    track_capacity_by_level: Dict[str, Tuple[int, ...]] = field(
        default_factory=lambda: {
            "DEFENSE": (2, 2, 3, 3, 4),
            "TRIAGE": (2, 2, 3, 3, 4),
            "RELEASE": (4, 4, 5, 5, 6),
        }
    )
    # Patents level -> (research cost, Secrets gained) per filing
    patent_rate_by_level: Dict[int, Tuple[int, int]] = field(
        default_factory=lambda: {0: (2, 1), 1: (2, 1), 2: (3, 2), 3: (3, 2), 4: (1, 1)}
    )
    patent_l1_cash: int = 3
    triage_l1_contractors: int = 2
    triage_l3_upgrade_cost: int = 3  # [TUNE]
    defense_l4_cash_per_block: int = 1  # [TUNE]
    defense_l4_cash_cap: int = 3  # [TUNE]
    triage_l4_free_moves: int = 2
    release_l4_extra_rerolls: int = 1
    # Lever sub-flags: None resolves once in __post_init__ from research_track_model.
    gray_face_profile: Optional[str] = None  # "V035_D1" | "V034"
    purple_purchasable: Optional[bool] = None
    company_setup_bonuses: Optional[bool] = None
    slush_fund_once_per_game: Optional[bool] = None
    level2_perks_enabled: Optional[bool] = None  # Emergency Hotfix + Passive Firewall (v0.34 only)
    # v0.36 Phase 44 Red experiment lever (RANSOM only; default = v0.35 behavior).
    red_ransom_per_cube: int = 1  # [TUNE] $ extorted per unblocked Red cube (read only under RedMode.RANSOM)

    # --- v0.36.0 Market Share Red rework (INV-MS-*). Defaults reproduce v0.35.0 bit-identically. ---
    # v0.36.0 is the default (Phase B, User-approved). None resolves in __post_init__: MARKET_SHARE, except
    # RANSOM for the legacy round / track models (V033_THREE_PHASE, V034_THREE_LEVEL), which never supported it.
    # GameConfig.legacy_v035() reproduces v0.35.0 bit-identically.
    red_mode: Optional[RedMode] = None
    market_share_start_by_player_count: Dict[int, int] = field(
        # [TUNE] start = max; not read under RANSOM. Balance iteration 1 (User 2026-11-06): 19/20/20 -> 17/18/18
        default_factory=lambda: {2: 17, 3: 18, 4: 18}
    )
    # NEW FIELD: Unified maximum Market Share across player counts (decoupled from start)
    market_share_max: Optional[int] = None
    # Sub-flags: None resolves once in __post_init__ from red_mode (re-assigning red_mode later does NOT re-resolve).
    market_collapse_enabled: Optional[bool] = None
    # [TUNE] Version -> payout. Under MARKET_SHARE resolves to {"v2.0": 4}: the v1.0 -> v2.0 comparison was dropped
    # (User 2026-11-06). A version absent from the map (or mapped to 0) has no comparison at all (no event recorded).
    version_share_payout: Optional[Dict[str, int]] = None
    patents_mode: Optional[PatentsMode] = None
    share_regain_cost_by_level: Dict[int, int] = field(
        default_factory=lambda: {0: 2, 1: 2, 2: 2, 3: 2, 4: 2}  # [TUNE] research per +1 Market Share
    )
    share_regain_cap_by_level: Dict[int, int] = field(
        default_factory=lambda: {0: 1, 1: 1, 2: 2, 3: 2, 4: 3}  # [TUNE] +Market Share per Operations Turn
    )
    # MARKETING is allowed under RANSOM only for the R1 rename (R2/R3 are inert without Market Share).
    red_variant_set: Optional[RedVariantSet] = None
    r2_share_cost: int = 2  # [TUNE] Ad Campaign: $ paid in Phase 6
    r2_share_gain: int = 1  # [TUNE] Ad Campaign: Market Share gained
    r3_poach_amount: int = 1  # [TUNE] Customer Poaching: Market Share taken from the rival with the most
    tiebreak_order: Optional[TiebreakOrder] = None
    # FREE_CHOICE is allowed under RANSOM (isolates the bot heuristic).
    any_shield_policy: Optional[AnyShieldPolicy] = None
    market_share_bot_policy: str = "AWARE"  # sim-only: "AWARE" | "NAIVE" (ablation)
    # --- v0.37.0 Market Leader Bonus (INV-MLB-*). Empty = disabled = v0.36.0 bit-identical. ---
    # [TUNE] player count -> bonus Corporate Secrets by Market Share place among survivors (index 0 = 1st place).
    # Shorter tuples are padded with 0 up to the player count; extra entries are ignored.
    # None resolves once in __post_init__: MARKET_SHARE -> the v0.37.0 schedule, RANSOM -> {} (disabled).
    market_leader_bonus_by_player_count: Optional[Dict[int, Tuple[int, ...]]] = None
    # --- Lever A (docs/specs/lever_a_roster_upgrade_spec.md). [TUNE-BOT] sim-only, default off = bit-identical. ---
    # Set only at construction: rollout clones share this config (H-LA-5); never flip it mid-game.
    bot_pr_push: bool = False
    bot_pr_push_params: PrPushParams = field(default_factory=PrPushParams)
    # "all" (default): every capable seat windows. "non_reference" (measurement mode, spec amendment 3): the
    # reference bot's fallback / portfolio members and every rollout clone keep the old AdaptiveBalanced behaviour.
    bot_pr_push_scope: str = "all"
    # --- v0.38.0 Secret faces / Processing Box (INV-SF-*). Defaults reproduce v0.37.0 bit-identically. ---
    secret_face_enabled: bool = False
    die_face_profile: str = "V037"  # "V037" | "V038_DRAFT" | "V038_YELLOW_MS" | "V038_YELLOW_MS_ALT" | "V038_YELLOW_MS_F3" (spec §4, §14.3, §14.5)
    variant_profile: str = "V037"  # "V037" | "V038_DRAFT" (Variant Card texts, spec §5)
    power_profile: str = "V037"  # "V037" | "V038_DRAFT" (Magnetic Splice, Jumper Diagnostics, Brute-Force Bypass, §6)
    # [TUNE] Red Secret yield by Market Share: (min_share, yield), highest first, last threshold 0.
    secret_yield_red_tiers: Tuple[Tuple[int, int], ...] = ((9, 3), (5, 2), (1, 1), (0, 0))
    secret_yield_blue_base: int = 1  # [TUNE]
    secret_yield_blue_block_bonus: int = 1  # [TUNE] owner blocked >= 1 Blue cube in the banking round
    secret_yield_blue_grid_l3_bonus: int = 1  # [TUNE] Defense Grid Level >= 3
    secret_yield_blue_cap: int = 3  # [TUNE]
    secret_yield_green_base: int = 3  # [TUNE] minus the owner's Glitched Shield Slots, min 0
    secret_yield_purple: int = 1  # [TUNE]
    secret_yield_green_glitch_penalty: bool = True  # If False (v0.38e), Green Secret yield is flat secret_yield_green_base unconditionally.
    glitched_shield_slots_enabled: bool = False
    slot_graduation_clear: int = 1  # [TUNE] slots cleared once per Phase 5 if >= 1 die graduates
    company_starting_die_enabled: bool = False
    company_starting_colors: Dict[str, str] = field(default_factory=dict)  # CompanyCode -> "RED"|"BLUE"|"GREEN"
    triage_l1_breakthrough: str = "WHITE_CONTRACTORS"  # "WHITE_CONTRACTORS" (v0.37) | "GRAY_DIE"
    ace_allows_secret_face: bool = False
    # [TUNE] §14.3: max Glitched Shield Slots a player can receive per round from all sources (None = uncapped)
    glitched_slots_per_round_cap: Optional[int] = None  # Arbitrary Code Execution may target the Secret face (OQ-10: no)
    # --- RSP-1 (spec §14.5, FINDINGS §43.4). All off by default = v038b bit-identical. ---
    # None = Red yield from secret_yield_red_tiers; an int = flat Red Secret yield to the owner.
    red_secret_owner_yield: Optional[int] = None
    # [TUNE] player count -> Corporate Secrets by Market Share place; the "Red Secret payout" (provisional sim label)
    # fires at most once per round at the end of Phase 5 if >= 1 Red Secret was banked that round. None/{} = off.
    red_secret_payout_by_player_count: Optional[Dict[int, Tuple[int, ...]]] = None
    red_secret_payout_at_end: bool = False  # one more payout at game end (not on a Total Wipeout; see next lever)
    # spec §14.5.10: True (default, parity) skips the end payout on a Market Collapse end too; v038c() sets False.
    red_secret_payout_skip_on_collapse: bool = True
    triage_order_rule: str = "BOT"  # "BOT" (choose_triage_order hook) | "OLDEST_FIRST" (Processing Box entry order)
    # --- Green G2 Universal Sandbox [TUNE] (Phase 50) ---
    g2_base_research: int = 2   # Base Phase 3 research output on G2 Universal Sandbox face
    g2_glitch_bonus: int = 1    # Phase 3 research bonus per active Glitched Shield Slot
    # v0.38d: C2 setup & Green-Clean package levers
    starting_glitched_shield_slots: int = 0  # v038d sets to 1 (INV-V38D-02)
    green_triage_clean_mode: str = "NONE"   # "NONE" | "COUNT_THEN_CLEAN" | "CLEAN_THEN_COUNT"
    green_bank_cleans_slot: bool = False
    v1_staging_payload_override: Optional[Dict[str, Dict[CubeColor, int]]] = None
    # --- v0.39.1 / v0.40.0 White Contractor Removal & Meridian/Operator Rework (INV-RCD-*). ---
    # Defaults reproduce v0.38f bit-identically.
    white_contractor_dice_enabled: bool = True
    meridian_override_mode: str = "REDUNDANT_CREW"          # "REDUNDANT_CREW" | "CAPITAL_INJECTION"
    meridian_capital_injection_cash: int = 3                # [TUNE] +3 $ in Phase 3
    operator_protocol_mode: str = "CONTINGENT_STAFFING"     # "CONTINGENT_STAFFING" | "LOGISTICS_BOUNTY"
    operator_logistics_bounty_research: int = 1             # [TUNE] +1 🔬 per Purple ★ in Phase 3

    def __post_init__(self) -> None:
        if not (isinstance(self.track_step_costs, tuple) and len(self.track_step_costs) == 4 and all(isinstance(c, int) and c >= 0 for c in self.track_step_costs)):
            raise ValueError("track_step_costs must be a 4-tuple of non-negative integers")
        if not (isinstance(self.max_hardware_upgrades_per_turn, int) and self.max_hardware_upgrades_per_turn > 0):
            raise ValueError("max_hardware_upgrades_per_turn must be an integer > 0")
        if not isinstance(self.bot_pr_push_params, PrPushParams):
            raise ValueError("bot_pr_push_params must be a PrPushParams")
        self.bot_pr_push_params.validate()
        if self.bot_pr_push_scope not in ("all", "non_reference"):
            raise ValueError(f"bot_pr_push_scope must be 'all' or 'non_reference', got {self.bot_pr_push_scope!r}")
        self.round_sequence = RoundSequence(self.round_sequence)
        if self.red_mode is None:
            legacy_model = (
                self.round_sequence == RoundSequence.V033_THREE_PHASE
                or ResearchTrackModel(self.research_track_model) != ResearchTrackModel.V035_FIVE_LEVEL
            )
            self.red_mode = RedMode.RANSOM if legacy_model else RedMode.MARKET_SHARE
        self.red_mode = RedMode(self.red_mode)
        ms = self.red_mode == RedMode.MARKET_SHARE
        # NOTE: resolved once at construction; re-assigning red_mode later does NOT re-resolve.
        self.patents_mode = PatentsMode(self.patents_mode) if self.patents_mode is not None else (
            PatentsMode.SHARE_REGAIN if ms else PatentsMode.PATENTS)
        self.red_variant_set = RedVariantSet(self.red_variant_set) if self.red_variant_set is not None else (
            RedVariantSet.MARKETING if ms else RedVariantSet.V035)
        self.tiebreak_order = TiebreakOrder(self.tiebreak_order) if self.tiebreak_order is not None else (
            TiebreakOrder.MARKET_SHARE_FIRST if ms else TiebreakOrder.V035)
        self.any_shield_policy = AnyShieldPolicy(self.any_shield_policy) if self.any_shield_policy is not None else (
            AnyShieldPolicy.FREE_CHOICE if ms else AnyShieldPolicy.V035_TIERS)
        if self.market_collapse_enabled is None:
            self.market_collapse_enabled = ms
        if self.version_share_payout is None:
            self.version_share_payout = {"v2.0": 4} if ms else {}
        if self.market_share_bot_policy not in ("AWARE", "NAIVE"):
            raise ValueError(f"market_share_bot_policy must be 'AWARE' or 'NAIVE', got {self.market_share_bot_policy!r}")
        if ms and self.round_sequence == RoundSequence.V033_THREE_PHASE:
            raise ValueError("red_mode=MARKET_SHARE is not supported with round_sequence=V033_THREE_PHASE")
        if ms and self.research_track_model != ResearchTrackModel.V035_FIVE_LEVEL:
            raise ValueError("red_mode=MARKET_SHARE requires research_track_model=V035_FIVE_LEVEL "
                             "(the Public Relations Track regain needs the five-level tracks)")
        if not ms:
            bad = []
            if self.patents_mode == PatentsMode.SHARE_REGAIN:
                bad.append("patents_mode=SHARE_REGAIN")
            if self.market_collapse_enabled:
                bad.append("market_collapse_enabled=True")
            if self.version_share_payout:
                bad.append("version_share_payout non-empty")
            if self.tiebreak_order == TiebreakOrder.MARKET_SHARE_FIRST:
                bad.append("tiebreak_order=MARKET_SHARE_FIRST")
            if bad:
                raise ValueError(f"{', '.join(bad)} requires red_mode=MARKET_SHARE (no Market Share under RANSOM)")
        for name in ("share_regain_cost_by_level", "share_regain_cap_by_level"):
            missing = [lvl for lvl in _ALL_TRACK_LEVELS if lvl not in getattr(self, name)]
            if missing:
                raise ValueError(f"{name} is missing levels {missing}")
        if self.market_leader_bonus_by_player_count is None:
            self.market_leader_bonus_by_player_count = dict(V037_MARKET_LEADER_BONUS) if ms else {}
        self._validate_market_leader_bonus(ms)
        self.research_track_model = ResearchTrackModel(self.research_track_model)
        v035 = self.research_track_model == ResearchTrackModel.V035_FIVE_LEVEL
        # NOTE: resolved once at construction; re-assigning research_track_model later does NOT re-resolve.
        if self.gray_face_profile is None:
            self.gray_face_profile = "V035_D1" if v035 else "V034"
        if self.purple_purchasable is None:
            self.purple_purchasable = not v035
        if self.company_setup_bonuses is None:
            self.company_setup_bonuses = not v035
        if self.slush_fund_once_per_game is None:
            self.slush_fund_once_per_game = v035
        if self.level2_perks_enabled is None:
            self.level2_perks_enabled = not v035
        self._validate_tower_config()
        self._validate_v038()
        if self.starting_secrets_by_player_count is None:
            # NOTE: resolved once at construction. Re-assigning round_sequence later does NOT
            # re-resolve this dict; use GameConfig.legacy_v033() or pass round_sequence to __init__.
            if self.round_sequence == RoundSequence.V033_THREE_PHASE:
                self.starting_secrets_by_player_count = {2: 8, 3: 8, 4: 12}
            elif self.red_mode == RedMode.MARKET_SHARE:
                self.starting_secrets_by_player_count = dict(V037_STARTING_SECRETS)  # v0.37.0 [TUNE] (FINDINGS §39)
            else:
                self.starting_secrets_by_player_count = {2: 8, 3: 8, 4: 8}  # v0.34 / v0.35

    @classmethod
    def v036(cls, **overrides) -> "GameConfig":
        """Alias of ``legacy_v036()`` (kept for the v0.36-era scripts and tests)."""
        return cls.legacy_v036(**overrides)

    @classmethod
    def legacy_v036(cls, **overrides) -> "GameConfig":
        """v0.36.0 baseline: Market Share Red, Public Relations Track, Market Collapse, 7/7/8 Secrets, no Market
        Leader Bonus. Bit-identical to the v0.36.0 default (tests/fixtures/v036_parity).

        Balance iteration 1 (User 2026-11-06): Market Share start 17/18/18; only the v2.0 -> v3.0 comparison ($4).
        Final tune (User, plan §11 / FINDINGS §34): starting Secrets 7/7/8 (2P/3P/4P), replacing 8/10/11.
        """
        overrides.setdefault("red_mode", RedMode.MARKET_SHARE)
        overrides.setdefault("starting_secrets_by_player_count", {2: 7, 3: 7, 4: 8})  # [TUNE]
        overrides.setdefault("market_share_start_by_player_count", {2: 17, 3: 18, 4: 18})
        overrides.setdefault("version_share_payout", {"v2.0": 4})
        overrides.setdefault("market_leader_bonus_by_player_count", {})
        return cls(**overrides)

    @classmethod
    def v037(cls, **overrides) -> "GameConfig":
        """v0.37.0 (the ``GameConfig()`` default): v0.36.0 + Market Leader Bonus (FINDINGS §38 / §39).

        2P 1st +2; 3P 1st +2, 2nd +1; 4P 1st +2, 2nd +1; others 0 [TUNE]. Ties share the better place,
        survivors only, none on a Total Wipeout. Starting Secrets 9 / 8 / 9 [TUNE].
        """
        overrides.setdefault("market_leader_bonus_by_player_count", dict(V037_MARKET_LEADER_BONUS))
        overrides.setdefault("starting_secrets_by_player_count", dict(V037_STARTING_SECRETS))  # [TUNE]
        return cls.legacy_v036(**overrides)

    @classmethod
    def v037_roster(cls, **overrides) -> "GameConfig":
        """Default roster for rule probes and routine sweeps (FINDINGS §41): v0.37 + ``bot_pr_push=True``
        with default ``PrPushParams``. ``GameConfig()`` / ``v037()`` keep ``bot_pr_push=False`` for parity."""
        overrides.setdefault("bot_pr_push", True)
        overrides.setdefault("bot_pr_push_params", PrPushParams())
        return cls.v037(**overrides)

    @classmethod
    def v038(cls, **overrides) -> "GameConfig":
        """v0.38.0 candidate (FINDINGS §42, spec v380): Secret faces, Processing Box banking, Glitched Shield Slots,
        12-point Market Share without Market Collapse, Company starting die, Triage L1 Gray die, 5/5/5 Secrets,
        Public Relations regain 3 research per +1 Market Share. On top of ``v037()``."""
        for k, v in (
            ("secret_face_enabled", True), ("die_face_profile", "V038_DRAFT"), ("variant_profile", "V038_DRAFT"),
            ("power_profile", "V038_DRAFT"), ("glitched_shield_slots_enabled", True),
            ("company_starting_die_enabled", True), ("company_starting_colors", dict(V038_COMPANY_STARTING_COLORS)),
            ("triage_l1_breakthrough", "GRAY_DIE"), ("market_share_start_by_player_count", dict(V038_MARKET_SHARE_START)),
            ("market_collapse_enabled", False), ("any_shield_policy", AnyShieldPolicy.FREE_CHOICE),
            ("starting_secrets_by_player_count", dict(V038_STARTING_SECRETS)),
            ("share_regain_cost_by_level", {lvl: V038_PR_REGAIN_COST for lvl in _ALL_TRACK_LEVELS}),
        ):
            overrides.setdefault(k, v)
        return cls.v037(**overrides)

    @classmethod
    def v038b(cls, **overrides) -> "GameConfig":
        """v0.38 candidate 2 (spec §14.3, FINDINGS §43): ``v038()`` + Market Collapse on, starting Secrets 3/4/4,
        Red tiers 11/7/3, Yellow profile ``V038_YELLOW_MS``; §14.4: Market Share 14 (start = max), Market Leader
        Bonus 2P +4 / 3-4P +4, +2; no lever A bot switches (``bot_pr_push=False``).
        ``v038()`` / ``v038_roster()`` are unchanged so the first sweep reproduces."""
        for k, v in (("market_collapse_enabled", True), ("starting_secrets_by_player_count", dict(V038B_STARTING_SECRETS)),
                     ("secret_yield_red_tiers", V038B_RED_TIERS), ("die_face_profile", "V038_YELLOW_MS"),
                     ("bot_pr_push", False),
                     ("market_share_start_by_player_count", dict(V038B_MARKET_SHARE_START)),
                     ("market_leader_bonus_by_player_count", dict(V038B_MARKET_LEADER_BONUS))):
            overrides.setdefault(k, v)
        return cls.v038(**overrides)

    @classmethod
    def v038c(cls, **overrides) -> "GameConfig":
        """v0.38 candidate 3, RSP-1 (spec §14.5, FINDINGS §43.4): ``v038b()`` + Red Secret owner yield +2 (User, 2026-11-09, §43.5), the Red
        Secret payout (at most once per round at the end of Phase 5; 1st +3 / 2nd +1) plus one end payout, Market
        Leader Bonus and v2.0 comparison removed, Market Share 13 / 16 / 17 (start = max), Yellow F3
        ``+$1 & +1 Market Share``, oldest-first Conveyor Triage, Shogun Baffle tower physics. Starting Secrets 3 / 4 / 4."""
        overrides.setdefault("tower_mode", TowerMode.SHOGUN_BAFFLE)
        for k, v in (("red_secret_owner_yield", 2),
                     ("red_secret_payout_by_player_count", dict(V038C_RED_SECRET_PAYOUT)),
                     ("red_secret_payout_at_end", True), ("red_secret_payout_skip_on_collapse", False),
                     ("market_leader_bonus_by_player_count", {}), ("version_share_payout", {}),
                     ("market_share_start_by_player_count", dict(V038C_MARKET_SHARE_START)),
                     ("die_face_profile", "V038_YELLOW_MS_F3"), ("triage_order_rule", "OLDEST_FIRST"),
                     ("starting_secrets_by_player_count", dict(V038B_STARTING_SECRETS))):
            overrides.setdefault(k, v)
        return cls.v038b(**overrides)

    @classmethod
    def v038c_legacy_tower(cls, **overrides) -> "GameConfig":
        """v0.38c rules running on the legacy LEDGE_AVALANCHE tower for comparative sensitivity sweeps."""
        overrides.setdefault("tower_mode", TowerMode.LEDGE_AVALANCHE)
        return cls.v038c(**overrides)

    @classmethod
    def v038d(cls, **overrides) -> "GameConfig":
        """v0.38 candidate 4 (C2 + Green-Clean Package, Variant B): ``v038c()`` + Candidate C2 setup (4 priming cubes,
        4 starting attack cubes in staging cup, 1 starting Glitched Shield Slot), elimination of passive graduation
        auto-clean (slot_graduation_clear = 0), Green Face 1 = +2 🔬 (die_face_profile = 'V038D'), and Green banking
        triage cleans 1 Glitched Shield Slot (COUNT_THEN_CLEAN). Preserves Shogun Baffle tower physics."""
        from sim.entities import V038D_V1_STAGING_PAYLOAD
        for k, v in (
            ("starting_glitched_shield_slots", 1),
            ("slot_graduation_clear", 0),
            ("green_triage_clean_mode", "COUNT_THEN_CLEAN"),
            ("green_bank_cleans_slot", True),
            ("die_face_profile", "V038D"),
            ("v1_staging_payload_override", dict(V038D_V1_STAGING_PAYLOAD)),
            ("market_share_start_by_player_count", dict(V038E_MARKET_SHARE_START)),
            ("market_share_max", DEFAULT_MARKET_SHARE_MAX),
        ):
            overrides.setdefault(k, v)
        return cls.v038c(**overrides)

    @classmethod
    def v038e(cls, **overrides) -> "GameConfig":
        """v0.38 candidate 5 (Phase 52: Secret Face Simplification & Processing Triggers).
        Inherits all v0.38d rules (C2 setup, 1 starting glitched slot, Shogun Baffle physics,
        Green triage clean, Headroom Architecture max 20), and applies the simplified 4-color Secret architecture:
        - Red: flat +2 + Market Leader Bonus trigger
        - Blue: flat +2 (+1 if Defense Grid >= L3, cap 3; block bonus eliminated)
        - Green: flat +2 + clean 1 Glitched Shield Slot (glitch yield penalty eliminated)
        - Purple: flat +1 (no trigger)
        """
        for k, v in (
            ("secret_yield_blue_base", 2),
            ("secret_yield_blue_block_bonus", 0),
            ("secret_yield_blue_grid_l3_bonus", 1),
            ("secret_yield_blue_cap", 3),
            ("secret_yield_green_base", 2),
            ("secret_yield_green_glitch_penalty", False),
            ("green_bank_cleans_slot", True),
            ("green_triage_clean_mode", "COUNT_THEN_CLEAN"),
        ):
            overrides.setdefault(k, v)
        return cls.v038d(**overrides)

    @classmethod
    def v038e_roster(cls, **overrides) -> "GameConfig":
        """``v038e()`` + the ``v037_roster()`` bot switches (lever A push on, default params)."""
        overrides.setdefault("bot_pr_push", True)
        overrides.setdefault("bot_pr_push_params", PrPushParams())
        return cls.v038e(**overrides)

    @classmethod
    def v038f(cls, **overrides) -> "GameConfig":
        """v0.38 candidate 6 (Blue Module Die Rebalance: Direct Corporate Secrets on Faces 1 & 2).
        Inherits all v0.38e rules (C2 setup, 1 starting glitched slot, Shogun Baffle physics,
        Green triage clean, Red owner yield +2 + Market Leader Bonus trigger, Blue Defense Grid L3 trigger,
        Headroom Architecture max 20),
        and introduces die_face_profile="V038F":
        - Blue Face 1: +1 Corporate Secret
        - Blue Face 2: +1 Corporate Secret
        - Blue Face 3: +$1
        - Blue Face 4: +1 🔬 / +$1
        - Blue Face 5: Secret face (+2 baseline, +1 if Defense Grid >= L3)
        - Blue Face 6: Blue ★ (Variant Card)
        """
        overrides.setdefault("die_face_profile", "V038F")
        return cls.v038e(**overrides)

    @classmethod
    def v038f_roster(cls, **overrides) -> "GameConfig":
        """``v038f()`` + the ``v037_roster()`` bot switches (lever A push on, default params)."""
        overrides.setdefault("bot_pr_push", True)
        overrides.setdefault("bot_pr_push_params", PrPushParams())
        return cls.v038f(**overrides)

    @classmethod
    def v040(cls, **overrides) -> "GameConfig":
        """v0.40.0 (Phase 56: Remove White Contractor Dice & Glitch Faces).
        Inherits all v0.38f rules and removes White Contractor dice:
        - white_contractor_dice_enabled = False (contractor_max_hire = 0, contractor_supply_total = 0)
        - meridian_override_mode = 'CAPITAL_INJECTION' (+3 $ in Phase 3 once per Rogue Agent Version)
        - operator_protocol_mode = 'LOGISTICS_BOUNTY' (+1 🔬 per Purple ★ face still In Production in Phase 3)
        """
        for k, v in (
            ("white_contractor_dice_enabled", False),
            ("contractor_max_hire", 0),
            ("contractor_supply_total", 0),
            ("meridian_override_mode", "CAPITAL_INJECTION"),
            ("meridian_capital_injection_cash", 3),
            ("operator_protocol_mode", "LOGISTICS_BOUNTY"),
            ("operator_logistics_bounty_research", 1),
        ):
            overrides.setdefault(k, v)
        return cls.v038f(**overrides)

    @classmethod
    def v040_roster(cls, **overrides) -> "GameConfig":
        """``v040()`` + the ``v037_roster()`` bot switches (lever A push on, default params)."""
        overrides.setdefault("bot_pr_push", True)
        overrides.setdefault("bot_pr_push_params", PrPushParams())
        return cls.v040(**overrides)

    # Aliases for v0.39.1 / v0.39 transition naming
    v0391 = v040
    v0391_roster = v040_roster
    v039 = v040
    v039_roster = v040_roster

    @classmethod
    def v038_roster(cls, **overrides) -> "GameConfig":
        """``v038()`` + the ``v037_roster()`` bot switches (lever A push on, default params)."""
        overrides.setdefault("bot_pr_push", True)
        overrides.setdefault("bot_pr_push_params", PrPushParams())
        return cls.v038(**overrides)

    def _validate_tower_config(self) -> None:
        """Validates Cube Tower physics parameters (spec §2.4)."""
        self.tower_mode = TowerMode(self.tower_mode)
        prob_fields = (
            "tower_empty_exit_prob",
            "tower_obstruction_alpha",
            "tower_min_fall_prob",
            "tower_trapping_dislodge_prob",
            "tower_avalanche_fall_prob",
            "tower_avalanche_dislodge_prob",
            "tower_flat_exit_prob",
            "tower_base_exit_prob",
        )
        for name in prob_fields:
            val = getattr(self, name)
            if isinstance(val, bool) or not isinstance(val, (int, float)) or not (0.0 <= float(val) <= 1.0):
                raise ValueError(f"{name} must be a probability in [0.0, 1.0], got {val!r}")
        for name in ("tower_avalanche_stuck_threshold", "tower_avalanche_mass_threshold"):
            val = getattr(self, name)
            if isinstance(val, bool) or not isinstance(val, int) or val < 1:
                raise ValueError(f"{name} must be an integer >= 1, got {val!r}")

    def _validate_v038(self) -> None:
        """spec §2.2. Called from __post_init__ after red_mode / any_shield_policy resolve."""
        if self.die_face_profile not in _DIE_FACE_PROFILES:
            raise ValueError(f"die_face_profile must be one of {_DIE_FACE_PROFILES}, got {self.die_face_profile!r}")
        cap = self.glitched_slots_per_round_cap
        if cap is not None and (isinstance(cap, bool) or not isinstance(cap, int) or cap < 0):
            raise ValueError("glitched_slots_per_round_cap must be None or an int >= 0")
        for name in ("variant_profile", "power_profile"):
            if getattr(self, name) not in _FACE_PROFILES:
                raise ValueError(f"{name} must be one of {_FACE_PROFILES}, got {getattr(self, name)!r}")
        if self.triage_l1_breakthrough not in _TRIAGE_L1_MODES:
            raise ValueError(f"triage_l1_breakthrough must be one of {_TRIAGE_L1_MODES}")
        if self.secret_face_enabled:
            bad = []
            if self.die_face_profile not in V038_DIE_FACE_PROFILES:
                bad.append(f"die_face_profile in {V038_DIE_FACE_PROFILES}")
            if self.red_mode != RedMode.MARKET_SHARE:
                bad.append("red_mode=MARKET_SHARE")
            if self.round_sequence != RoundSequence.SIX_PHASE:
                bad.append("round_sequence=SIX_PHASE")
            if not self.glitched_shield_slots_enabled:
                bad.append("glitched_shield_slots_enabled=True")
            if self.dirty_income_enabled:
                bad.append("dirty_income_enabled=False")
            if bad:
                raise ValueError(f"secret_face_enabled requires {', '.join(bad)}")
        elif self.die_face_profile in V038_DIE_FACE_PROFILES:
            raise ValueError("die_face_profile='V038_DRAFT' requires secret_face_enabled (Face 5 would be dead)")
        if self.glitched_shield_slots_enabled and self.round_sequence != RoundSequence.SIX_PHASE:
            raise ValueError("glitched_shield_slots_enabled requires round_sequence=SIX_PHASE")
        tiers = tuple(tuple(t) for t in self.secret_yield_red_tiers)
        if (not tiers or any(len(t) != 2 for t in tiers)
                or any(tiers[i][0] <= tiers[i + 1][0] for i in range(len(tiers) - 1))
                or tiers[-1][0] != 0 or any(y < 0 for _, y in tiers)):
            raise ValueError("secret_yield_red_tiers: strictly descending thresholds ending at 0, yields >= 0")
        self.secret_yield_red_tiers = tiers
        for name in ("secret_yield_blue_base", "secret_yield_blue_block_bonus", "secret_yield_blue_grid_l3_bonus",
                     "secret_yield_blue_cap", "secret_yield_green_base", "secret_yield_purple", "slot_graduation_clear"):
            if int(getattr(self, name)) < 0:
                raise ValueError(f"{name} must be >= 0")
        for name in ("g2_base_research", "g2_glitch_bonus"):
            val = getattr(self, name)
            if isinstance(val, bool) or not isinstance(val, int) or val < 0:
                raise ValueError(f"{name} must be an int >= 0, got {val!r}")
        if self.secret_yield_blue_cap < self.secret_yield_blue_base:
            raise ValueError("secret_yield_blue_cap must be >= secret_yield_blue_base")
        if not isinstance(self.secret_yield_green_glitch_penalty, bool):
            raise ValueError(f"secret_yield_green_glitch_penalty must be a bool, got {self.secret_yield_green_glitch_penalty!r}")
        if self.company_starting_die_enabled:
            missing = [c for c in ("MERIDIAN", "OMNIDYNE", "AEGIS", "DTO", "HELIX", "PROMETHEUS")
                       if self.company_starting_colors.get(c) not in ("RED", "BLUE", "GREEN")]
            if missing:
                raise ValueError(f"company_starting_colors must map every Client Company to RED/BLUE/GREEN: {missing}")
            if self.starting_gray_dice < 1:
                raise ValueError("company_starting_die_enabled requires starting_gray_dice >= 1")
        self._validate_rsp1()
        self._validate_v038d()
        self._validate_rcd()

    def _validate_rcd(self) -> None:
        """spec remove_contractor_dice_spec §3.1 validation."""
        if not isinstance(self.white_contractor_dice_enabled, bool):
            raise ValueError(
                f"white_contractor_dice_enabled must be a bool, got {self.white_contractor_dice_enabled!r}"
            )
        if not self.white_contractor_dice_enabled:
            self.contractor_max_hire = 0
            self.contractor_supply_total = 0
        if self.meridian_override_mode not in _MERIDIAN_OVERRIDE_MODES:
            raise ValueError(
                f"meridian_override_mode must be one of {_MERIDIAN_OVERRIDE_MODES}, got {self.meridian_override_mode!r}"
            )
        if self.operator_protocol_mode not in _OPERATOR_PROTOCOL_MODES:
            raise ValueError(
                f"operator_protocol_mode must be one of {_OPERATOR_PROTOCOL_MODES}, got {self.operator_protocol_mode!r}"
            )
        for name in ("meridian_capital_injection_cash", "operator_logistics_bounty_research"):
            val = getattr(self, name)
            if isinstance(val, bool) or not isinstance(val, int) or val < 0:
                raise ValueError(f"{name} must be an int >= 0, got {val!r}")

    def _validate_v038d(self) -> None:
        """spec v0.38d §3.1.2 validation."""
        if self.green_bank_cleans_slot and self.green_triage_clean_mode == "NONE":
            self.green_triage_clean_mode = "COUNT_THEN_CLEAN"
        elif self.green_triage_clean_mode in ("COUNT_THEN_CLEAN", "CLEAN_THEN_COUNT"):
            self.green_bank_cleans_slot = True
        if self.green_triage_clean_mode not in _GREEN_TRIAGE_CLEAN_MODES:
            raise ValueError(
                f"green_triage_clean_mode must be one of {_GREEN_TRIAGE_CLEAN_MODES}, got {self.green_triage_clean_mode!r}"
            )
        if self.starting_glitched_shield_slots < 0:
            raise ValueError("starting_glitched_shield_slots must be >= 0")

    def _validate_rsp1(self) -> None:
        """spec §14.5.1 validation."""
        y = self.red_secret_owner_yield
        if y is not None:
            if isinstance(y, bool) or not isinstance(y, int) or y < 0:
                raise ValueError("red_secret_owner_yield must be None or an int >= 0")
            if not self.secret_face_enabled:
                raise ValueError("red_secret_owner_yield requires secret_face_enabled")
        raw = self.red_secret_payout_by_player_count
        self.red_secret_payout_by_player_count = self._normalize_place_schedule(
            {} if raw is None else raw, "red_secret_payout", max_len_is_n=True)
        if self.red_secret_payout_by_player_count:
            if not self.secret_face_enabled or not self.is_market_share:
                raise ValueError("red_secret_payout_by_player_count requires secret_face_enabled and red_mode=MARKET_SHARE")
        if self.red_secret_payout_at_end and not self.is_red_secret_payout:
            raise ValueError("red_secret_payout_at_end requires a non-empty red_secret_payout_by_player_count")
        if self.triage_order_rule not in _TRIAGE_ORDER_RULES:
            raise ValueError(f"triage_order_rule must be one of {_TRIAGE_ORDER_RULES}, got {self.triage_order_rule!r}")
        if self.triage_order_rule == "OLDEST_FIRST" and not self.secret_face_enabled:
            raise ValueError("triage_order_rule='OLDEST_FIRST' requires secret_face_enabled")

    def red_secret_payout_schedule(self, num_players: Optional[int] = None) -> Tuple[int, ...]:
        """Red Secret payout by place (index 0 = 1st), padded with 0 / truncated to the player count; () when off."""
        n = num_players if num_players is not None else self.num_players
        sched = self.red_secret_payout_by_player_count.get(n, ())
        if not any(b > 0 for b in sched):
            return ()
        return tuple(sched[:n]) + (0,) * max(0, n - len(sched))

    @property
    def is_red_secret_payout(self) -> bool:
        return any(any(b > 0 for b in s) for s in self.red_secret_payout_by_player_count.values())

    @property
    def is_secret_faces(self) -> bool:
        return bool(self.secret_face_enabled)

    @classmethod
    def legacy_v035(cls, **overrides) -> "GameConfig":
        """v0.35.0 baseline (today's defaults). Exists now so the parity test survives a later default flip."""
        overrides.setdefault("red_mode", RedMode.RANSOM)
        # Starting Secrets resolve in __post_init__ under RANSOM: 8/8/8 (six-phase), 8/8/12 (v0.33 round).
        return cls(**overrides)

    @classmethod
    def legacy_v033(cls, **overrides) -> "GameConfig":
        """v0.33.0 baseline: three-phase round + 4P = 12 Secrets."""
        overrides.setdefault("red_mode", RedMode.RANSOM)
        overrides.setdefault("legacy_archetype_override_bridge", True)
        overrides.setdefault("research_track_model", ResearchTrackModel.V034_THREE_LEVEL)
        return cls(round_sequence=RoundSequence.V033_THREE_PHASE, **overrides)

    @classmethod
    def legacy_v034(cls, **overrides) -> "GameConfig":
        """v0.34.0 baseline: six-phase round with the v0.34 three-level research tracks."""
        overrides.setdefault("red_mode", RedMode.RANSOM)
        overrides.setdefault("research_track_model", ResearchTrackModel.V034_THREE_LEVEL)
        return cls(**overrides)

    @property
    def is_v035_tracks(self) -> bool:
        return self.research_track_model == ResearchTrackModel.V035_FIVE_LEVEL

    @property
    def is_market_share(self) -> bool:
        return self.red_mode == RedMode.MARKET_SHARE

    @property
    def is_share_regain(self) -> bool:
        return self.patents_mode == PatentsMode.SHARE_REGAIN

    def get_market_share_max(self, num_players: Optional[int] = None) -> int:
        """Returns the maximum Market Share ceiling (unified 20 across all player counts)."""
        if self.market_share_max is not None:
            return self.market_share_max
        return self.market_share_start(num_players)

    def market_share_start(self, num_players: Optional[int] = None) -> int:
        """Starting Market Share for the player count (or self.num_players)."""
        n = num_players if num_players is not None else self.num_players
        return self.market_share_start_by_player_count.get(n, self.market_share_start_by_player_count.get(4, 16))

    def _validate_market_leader_bonus(self, ms: bool) -> None:
        norm = self._normalize_place_schedule(self.market_leader_bonus_by_player_count, "market_leader_bonus")
        if not ms and any(any(b > 0 for b in sched) for sched in norm.values()):
            raise ValueError("market_leader_bonus requires red_mode=MARKET_SHARE")
        self.market_leader_bonus_by_player_count = norm

    @staticmethod
    def _normalize_place_schedule(raw: Any, label: str, max_len_is_n: bool = False) -> Dict[int, Tuple[int, ...]]:
        """Shape rules shared by the Market Leader Bonus and the Red Secret payout schedules."""
        if not isinstance(raw, dict):
            raise ValueError(f"{label}_by_player_count must be a dict of player count -> schedule")
        norm: Dict[int, Tuple[int, ...]] = {}
        for n, sched in raw.items():
            if isinstance(n, bool) or not isinstance(n, int) or not 2 <= n <= 4:
                raise ValueError(f"{label} player-count keys must be 2..4, got {n!r}")
            if not isinstance(sched, (tuple, list)) or any(
                    isinstance(b, bool) or not isinstance(b, int) for b in sched):
                raise ValueError(f"{label} schedule for {n}P must be a tuple/list of ints, got {sched!r}")
            if any(b < 0 for b in sched):
                raise ValueError(f"{label} schedule for {n}P has a negative entry: {sched!r}")
            if any(sched[i] < sched[i + 1] for i in range(len(sched) - 1)):
                raise ValueError(f"{label} schedule for {n}P must be non-increasing: {sched!r}")
            if max_len_is_n and len(sched) > n:
                raise ValueError(f"{label} schedule for {n}P is longer than the player count: {sched!r}")
            norm[int(n)] = tuple(int(b) for b in sched)
        return norm

    def market_leader_bonus_schedule(self, num_players: Optional[int] = None) -> Tuple[int, ...]:
        """Bonus by place (index 0 = 1st), padded with 0 / truncated to the player count. () when disabled."""
        n = num_players if num_players is not None else self.num_players
        sched = self.market_leader_bonus_by_player_count.get(n, ())
        if not any(b > 0 for b in sched):
            return ()
        return tuple(sched[:n]) + (0,) * max(0, n - len(sched))

    @property
    def is_market_leader_bonus(self) -> bool:
        """True when the schedule for self.num_players has any positive entry."""
        return bool(self.market_leader_bonus_schedule())

    @property
    def is_six_phase(self) -> bool:
        return self.round_sequence == RoundSequence.SIX_PHASE

    @property
    def corruption_track_capacity(self) -> int:
        """Returns corruption track capacity from player-count mapping or flat capacity override."""
        if self.corruption_track_flat_capacity is not None:
            return self.corruption_track_flat_capacity
        return self.corruption_track_capacity_by_player_count.get(self.num_players, 4)

    @property
    def corruption_cube_resolve_immediate(self) -> bool:
        return self.corruption_cubes_resolve_immediately

    @corruption_cube_resolve_immediate.setter
    def corruption_cube_resolve_immediate(self, val: bool) -> None:
        self.corruption_cubes_resolve_immediately = val

    def get_starting_secrets(self, num_players: Optional[int] = None) -> int:
        """Returns starting secrets for the specified player count (or self.num_players).

        Scalar override starting_secrets takes precedence if provided.
        """
        if self.starting_secrets is not None:
            return self.starting_secrets
        n = num_players if num_players is not None else self.num_players
        fallback = self.starting_secrets_by_player_count.get(4, 8)
        return self.starting_secrets_by_player_count.get(n, fallback)

    def get_starting_patches(self, num_players: Optional[int] = None) -> int:
        """Returns starting patch tokens for the specified player count (or self.num_players).

        Scalar override starting_patches takes precedence if provided.
        """
        if self.starting_patches is not None:
            return self.starting_patches
        n = num_players if num_players is not None else self.num_players
        fallback = self.starting_patches_by_player_count.get(4, 0)
        return self.starting_patches_by_player_count.get(n, fallback)

    def get_contractor_cost_for_hire(self, count: int, already_hired: int = 0) -> int:
        """Returns the total cost to hire `count` additional contractors given `already_hired` in the current round."""
        if count <= 0:
            return 0
        total_cost = 0
        for i in range(already_hired, already_hired + count):
            if i < len(self.contractor_cost_progression):
                total_cost += self.contractor_cost_progression[i]
            else:
                total_cost += self.contractor_cost_progression[-1]
        return total_cost

    @property
    def white_contractors_enabled(self) -> bool:
        return self.white_contractor_dice_enabled

    @white_contractors_enabled.setter
    def white_contractors_enabled(self, val: bool) -> None:
        self.white_contractor_dice_enabled = bool(val)

    def get_max_affordable_contractors(
        self, money: int, already_hired: int = 0, supply: Optional[int] = None
    ) -> int:
        """Calculates the maximum number of contractors that can be afforded given money, already_hired, and supply."""
        if not self.white_contractor_dice_enabled:
            return 0
        max_possible = self.contractor_max_hire - already_hired
        if supply is not None:
            max_possible = min(max_possible, supply)
        if max_possible <= 0 or money <= 0:
            return 0

        affordable = 0
        for c in range(1, max_possible + 1):
            if self.get_contractor_cost_for_hire(c, already_hired) <= money:
                affordable = c
            else:
                break
        return affordable
