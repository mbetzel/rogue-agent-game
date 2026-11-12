"""Tier 1 reference bot: ``MixedPolicyBot`` (reference bot spec §4).

Each decision type is delegated to one archetype drawn by a pure hash of ``(match_seed, bot_id, decision_type
[, round])`` (INV-REF-RNG-02). The bot never reads any RNG, so the other seats are affected only through its
choices, and the result is identical across processes (``zlib.crc32``, never the salted ``hash()``).

Attribute mirroring (spec §2.1, hazard H2): before returning from a delegated call the wrapper copies the
delegate's attribute profile onto itself, and ``take_operations_actions`` returns the delegate's **raw** plan,
so the engine's Phase 6 post-processing (``apply_research_policy`` / ``apply_market_share_policy``) runs once
with the delegate's profile and the result equals the delegate's own ``resolve_operations_plan``.
"""

from __future__ import annotations

import copy
import zlib
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Type

from sim.bots.base import BaseBot
from sim.bots.accelerationist import AccelerationistBot
from sim.bots.adaptive_balanced import AdaptiveBalancedBot
from sim.bots.reckless_saboteur import RecklessSaboteurBot
from sim.bots.secops_turtle import SecOpsTurtleBot
from sim.bots.venture_greed import VentureGreedBot

# [TUNE-BOT] Mixed pool: archetypes only (User resolution 3, 2026-11-07); portfolio variants are search-only.
DEFAULT_POOL: Tuple[Type[BaseBot], ...] = (
    AccelerationistBot, AdaptiveBalancedBot, RecklessSaboteurBot, SecOpsTurtleBot, VentureGreedBot,
)
# [TUNE-BOT] "game" (default, User resolution 2): one draw per decision type per game; "round": redraw each round.
DEFAULT_GRANULARITY = "game"

# Bot attributes the engine / post-processing read (spec §2 "Attribute reads on the bot").
PROFILE_ATTRS: Tuple[str, ...] = (
    "research_focus", "research_focus_v036", "research_aware", "market_share_policy", "any_shield_fill_order",
    "market_color_preference", "pr_push_capable",
)

# Hook -> decision type (spec §4 "Decision types"). Helper methods a delegate calls on itself
# (release_pressure, plan_release_upgrade, expected_income) are routed with the Operations plan.
HOOK_DTYPES: Dict[str, str] = {
    # phase1_roll: rerolls, Helix, Meridian, Omnidyne, Prodigy
    "choose_yahtzee_rerolls": "phase1_roll",
    "choose_helix_override": "phase1_roll",
    "choose_helix_face_override": "phase1_roll",
    "choose_prodigy_ability": "phase1_roll",
    "choose_prodigy_face_override": "phase1_roll",
    "choose_prodigy_purple_star_override": "phase1_roll",
    "choose_meridian_override": "phase1_roll",
    "choose_meridian_capital_injection": "phase3_income",
    "choose_operator_ability": "phase1_roll",
    "choose_omnidyne_override": "phase1_roll",
    "choose_phreaker_ability": "phase1_roll",
    # phase1_deploy: declare_choices, commit_shields, contractor hires, Operator third die
    "declare_choices": "phase1_deploy",
    "commit_shields": "phase1_deploy",
    "choose_contractor_hires": "phase1_deploy",
    "choose_operator_buy_third_die": "phase1_deploy",
    "choose_operator_contingent_staffing": "phase1_deploy",
    # phase2: glitch / return
    "choose_dice_to_glitch": "phase2",
    "choose_colored_dice_to_return": "phase2",
    # phase4: Aegis, Generic shields, Slush Fund, malware
    "choose_aegis_override": "phase4",
    "choose_aegis_override_market_share": "phase4",
    "choose_any_shield_allocation": "phase4",
    "choose_slush_fund": "phase4",
    "choose_dto_override": "phase4",
    "choose_malware_glitch_targets": "phase4",
    "choose_malware_sacrifice": "phase4",
    # phase6: Operations plan + Phreaker / Spook Burn Notice / Purple reserve
    "choose_phreaker_jumper_diagnostics": "phase6",
    "choose_spook_burn_notice": "phase6",
    "choose_purple_reserve_purchase": "phase6",
    "release_pressure": "phase6",
    "plan_release_upgrade": "phase6",
    "expected_income": "phase6",
    # misc: Breakthrough, graduates, Customer Poaching target
    "choose_breakthrough": "misc",
    "choose_scanned_graduates": "misc",
    "choose_poach_target": "misc",
}


def force_fixed_focus(bot: BaseBot) -> BaseBot:
    """Hazard H1: ``research_focus_mode="random"`` shuffles the live engine RNG; private delegates never do."""
    bot.research_focus_mode = "fixed"
    bot.__dict__.pop("_research_focus_random", None)
    return bot


def profile_of(bot: Any) -> Dict[str, Any]:
    return {k: getattr(bot, k, None) for k in PROFILE_ATTRS}


def mirror_profile(target: Any, profile: Dict[str, Any]) -> None:
    for k, v in profile.items():
        setattr(target, k, v)
    target.research_focus_mode = "fixed"


def raw_operations_plan(bot: Any, player_state: Any, game_state: Any, rng: Any) -> Any:
    from sim.engine.phase6_operations import _resolve_raw_operations_plan

    return _resolve_raw_operations_plan(bot, player_state, game_state, rng)


def post_process_operations_plan(bot: Any, plan: Any, player_state: Any, game_state: Any, rng: Any) -> Any:
    """The post-processing half of ``phase6_operations.resolve_operations_plan`` (RB-04 guards equality)."""
    from sim.bots.research_policy import apply_research_policy

    plan = apply_research_policy(bot, plan, player_state, game_state, rng)
    if getattr(game_state.config, "is_market_share", False):
        from sim.bots.market_share_policy import apply_market_share_policy

        plan = apply_market_share_policy(bot, plan, player_state, game_state)
    return plan


def _round_of(args: Sequence[Any], kwargs: Dict[str, Any]) -> Optional[int]:
    from sim.engine.state import GameState

    for v in list(args) + list(kwargs.values()):
        if isinstance(v, GameState):
            return v.current_round
    return None


def _make_hook(name: str, dtype: str) -> Callable[..., Any]:
    def hook(self: "MixedPolicyBot", *args: Any, **kwargs: Any) -> Any:
        delegate = self._delegate_for(dtype, args, kwargs)
        out = getattr(delegate, name)(*args, **kwargs)
        mirror_profile(self, profile_of(delegate))
        return out

    hook.__name__ = name
    hook.__doc__ = f"Delegated ({dtype}) to the drawn archetype (spec §4.2)."
    return hook


class MixedPolicyBot(BaseBot):
    """Tier 1: per-decision-type archetype mix, drawn by ``crc32`` (spec §4)."""

    def __init__(
        self,
        bot_id: int,
        match_seed: int,
        pool: Sequence[Type[BaseBot]] = DEFAULT_POOL,
        granularity: str = DEFAULT_GRANULARITY,
        name: str = "MixedPolicyBot",
    ) -> None:
        super().__init__(bot_id, name)
        if granularity not in ("game", "round"):
            raise ValueError(f"granularity must be 'game' or 'round', got {granularity!r}")
        self.match_seed = int(match_seed)
        self.granularity = granularity
        self.pool: List[BaseBot] = [force_fixed_focus(cls(bot_id)) for cls in pool]
        self.engine: Any = None
        self.draw_log: Dict[Tuple[str, int], str] = {}  # telemetry only, never read by play
        mirror_profile(self, profile_of(self.pool[0]))

    # --- seeding (INV-REF-RNG-02) -------------------------------------------------------------
    def _draw(self, dtype: str, round_no: int) -> BaseBot:
        r = round_no if self.granularity == "round" else 0
        key = f"{self.match_seed}|{self.bot_id}|{dtype}|{r}"
        return self.pool[zlib.crc32(key.encode()) % len(self.pool)]

    def bind(self, engine: Any) -> None:
        """Only needed for ``granularity="round"`` (hooks without a ``GameState`` argument read the round here)."""
        self.engine = engine

    def for_clone(self, engine: Any) -> "MixedPolicyBot":
        """Rollout clones (Tier 2): a per-round Mixed bot must read the clone's round, not the live one."""
        if self.granularity == "game":
            return self
        twin = copy.copy(self)
        twin.engine = engine
        twin.draw_log = {}
        return twin

    def _delegate_for(self, dtype: str, args: Sequence[Any], kwargs: Dict[str, Any]) -> BaseBot:
        round_no = 0
        if self.granularity == "round":
            r = _round_of(args, kwargs)
            if r is None:
                if self.engine is None:
                    raise RuntimeError("MixedPolicyBot(granularity='round') must be bound to its engine (bind())")
                r = self.engine.state.current_round
            round_no = r
        delegate = self._draw(dtype, round_no)
        self.draw_log.setdefault((dtype, round_no), delegate.name)
        return delegate

    # --- Phase 6 (raw plan; spec §2.1) --------------------------------------------------------
    def take_operations_actions(self, player_state: Any, game_state: Any, rng: Any) -> Any:
        delegate = self._delegate_for("phase6", (game_state,), {})
        plan = raw_operations_plan(delegate, player_state, game_state, rng)
        mirror_profile(self, profile_of(delegate))
        return plan

    def take_phase3_actions(self, player_state: Any, game_state: Any, rng: Any) -> Any:
        return self.take_operations_actions(player_state, game_state, rng)


for _name, _dtype in HOOK_DTYPES.items():
    setattr(MixedPolicyBot, _name, _make_hook(_name, _dtype))
del _name, _dtype
