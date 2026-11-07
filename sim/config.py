"""Configuration, constants, and tunable parameters for Rogue Agent simulation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Dict, Optional, Tuple

_ALL_TRACK_LEVELS = (0, 1, 2, 3, 4)


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
    track_step_costs: Tuple[int, int, int, int] = (1, 2, 2, 3)  # [TUNE] cost to reach L1..L4
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

    def __post_init__(self) -> None:
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
        if self.starting_secrets_by_player_count is None:
            # NOTE: resolved once at construction. Re-assigning round_sequence later does NOT
            # re-resolve this dict; use GameConfig.legacy_v033() or pass round_sequence to __init__.
            if self.round_sequence == RoundSequence.V033_THREE_PHASE:
                self.starting_secrets_by_player_count = {2: 8, 3: 8, 4: 12}
            elif self.red_mode == RedMode.MARKET_SHARE:
                self.starting_secrets_by_player_count = {2: 7, 3: 7, 4: 8}  # v0.36.0 [TUNE] (plan §11)
            else:
                self.starting_secrets_by_player_count = {2: 8, 3: 8, 4: 8}  # v0.34 / v0.35

    @classmethod
    def v036(cls, **overrides) -> "GameConfig":
        """v0.36.0 candidate: Market Share Red, Public Relations Track, Market Collapse, 7/7/8 Secrets.

        Balance iteration 1 (User 2026-11-06): Market Share start 17/18/18; only the v2.0 -> v3.0 comparison ($4).
        Final tune (User, plan §11 / FINDINGS §34): starting Secrets 7/7/8 (2P/3P/4P), replacing 8/10/11.
        """
        overrides.setdefault("red_mode", RedMode.MARKET_SHARE)
        overrides.setdefault("starting_secrets_by_player_count", {2: 7, 3: 7, 4: 8})  # [TUNE]
        overrides.setdefault("market_share_start_by_player_count", {2: 17, 3: 18, 4: 18})
        overrides.setdefault("version_share_payout", {"v2.0": 4})
        return cls(**overrides)

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

    def market_share_start(self, num_players: Optional[int] = None) -> int:
        """Starting (= maximum) Market Share for the player count (or self.num_players)."""
        n = num_players if num_players is not None else self.num_players
        return self.market_share_start_by_player_count.get(n, self.market_share_start_by_player_count.get(4, 18))

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

    def get_max_affordable_contractors(
        self, money: int, already_hired: int = 0, supply: Optional[int] = None
    ) -> int:
        """Calculates the maximum number of contractors that can be afforded given money, already_hired, and supply."""
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
