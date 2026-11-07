"""v0.35.0 Terminal Hardware Tracks: five levels (L0-L4), Breakthroughs at L1 / L3, Level 4 effects.

Only used when ``config.is_v035_tracks``. The v0.34 track logic lives in ``PlayerState._v034_*``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from sim.config import DieColor
from sim.entities import create_colored_die, create_gray_die, create_white_die

if TYPE_CHECKING:
    from sim.config import GameConfig
    from sim.engine.core import GameEngine
    from sim.engine.state import PlayerState

TRACKS = ("DEFENSE", "TRIAGE", "RELEASE", "PATENT")
LEVEL_ATTR = {
    "DEFENSE": "defense_level",
    "TRIAGE": "triage_level",
    "RELEASE": "release_level",
    "PATENT": "patent_level",
}
CAPACITY_ATTR = {
    "DEFENSE": "defense_capacity",
    "TRIAGE": "triage_bandwidth",
    "RELEASE": "release_bandwidth",
}
MAX_LEVEL = 4
BREAKTHROUGH_LEVELS = (1, 3)
MARKET_COLORS = (DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW)
# Fallback colour preference for the Triage L3 Breakthrough (prototype order)
TRIAGE_L3_COLOR_FALLBACK = (DieColor.YELLOW, DieColor.GREEN, DieColor.RED, DieColor.BLUE)

# Short human-readable Breakthrough descriptions (web previews / logs)
BREAKTHROUGH_TEXT = {
    ("DEFENSE", 1): "Gain 1 Gray Legacy die",
    ("DEFENSE", 3): "Gain 1 Corporate Secret",
    ("TRIAGE", 1): "Gain 2 White Contractor dice",
    ("TRIAGE", 3): "Pay $3: replace 1 Gray Legacy die with a Central Market colored die",
    ("RELEASE", 1): "Gain 1 Gray Legacy die",
    ("RELEASE", 3): "Gain 1 Corporate Secret",
    ("PATENT", 1): "Gain $3",
    ("PATENT", 3): "Gain your 2nd Purple die",
}


@dataclass
class BreakthroughRecord:
    track: str  # "DEFENSE" | "TRIAGE" | "RELEASE" | "PATENT"
    level: int  # 1 or 3
    round_number: int
    outcome: str  # "TAKEN" | "DECLINED" | "FORFEITED"
    detail: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "track": self.track,
            "level": self.level,
            "round_number": self.round_number,
            "outcome": self.outcome,
            "detail": dict(self.detail),
        }


@dataclass
class BreakthroughChoice:
    accept: bool = True  # only meaningful for Triage L3 (the only optional, paid Breakthrough)
    gray_die_id: Optional[int] = None  # Triage L3
    color: Optional[DieColor] = None  # Triage L3


@dataclass
class TriageUpgradeOptions:
    gray_die_ids: List[int]  # bot default order: Glitched, Scanned, Ready (lowest die_id first within zone)
    colors: List[DieColor]  # Market colors with >= 1 die in stock
    cost: int
    affordable: bool

    @property
    def possible(self) -> bool:
        return bool(self.gray_die_ids) and bool(self.colors) and self.affordable

    def as_dict(self) -> Dict[str, Any]:
        return {
            "gray_die_ids": list(self.gray_die_ids),
            "colors": [c.value for c in self.colors],
            "cost": self.cost,
            "affordable": self.affordable,
            "possible": self.possible,
        }


Chooser = Callable[["PlayerState", str, int, Optional[TriageUpgradeOptions]], Optional[BreakthroughChoice]]


# ----------------------------------------------------------------------------------------------
# Costs / levels
# ----------------------------------------------------------------------------------------------
# v0.36.0: the Public Relations Track keeps the internal key "PATENT"
TRACK_ALIASES = {"PUBLIC_RELATIONS": "PATENT", "PR": "PATENT"}


def normalize_track(track: str) -> str:
    t = str(track).upper().strip()
    return TRACK_ALIASES.get(t, t)


def track_display_name(config: Optional[GameConfig], track: str) -> str:
    """Printed track name; the fourth track is the Public Relations Track under ``patents_mode=SHARE_REGAIN``."""
    t = normalize_track(track)
    if t == "PATENT":
        if config is not None and getattr(config, "is_share_regain", False):
            return "Public Relations Track"
        return "Cryptographic Patents Track"
    return {"DEFENSE": "Defense Grid Track", "TRIAGE": "Triage Track", "RELEASE": "Release Track"}.get(t, t.title())


def regain_rate(config: GameConfig, player: PlayerState) -> tuple:
    """(research cost per +1 Market Share, per-Operations-Turn cap) at the current Public Relations level."""
    lvl = max(0, min(MAX_LEVEL, int(player.patent_level)))
    return int(config.share_regain_cost_by_level[lvl]), int(config.share_regain_cap_by_level[lvl])


def level_of(player: PlayerState, track: str) -> int:
    return int(getattr(player, LEVEL_ATTR[normalize_track(track)]))


def step_cost(config: GameConfig, player: PlayerState, track: str) -> Optional[int]:
    t = normalize_track(track)
    if t not in LEVEL_ATTR:
        return None
    lvl = level_of(player, t)
    if lvl >= MAX_LEVEL:
        return None
    return int(config.track_step_costs[lvl])


def capacity_for(config: GameConfig, track: str, level: int) -> Optional[int]:
    t = normalize_track(track)
    table = config.track_capacity_by_level.get(t)
    if table is None:
        return None
    return int(table[max(0, min(level, len(table) - 1))])


def apply_level(config: GameConfig, player: PlayerState, track: str, new_level: int, round_number: int) -> None:
    """Sets the level, the capacity / bandwidth from ``track_capacity_by_level`` and the bookkeeping."""
    t = normalize_track(track)
    setattr(player, LEVEL_ATTR[t], new_level)
    cap = capacity_for(config, t, new_level)
    if cap is not None:
        setattr(player, CAPACITY_ATTR[t], cap)
    player.level_reached_round.setdefault(t, {}).setdefault(new_level, round_number)


def patent_rate(config: GameConfig, player: PlayerState) -> tuple:
    lvl = max(0, min(MAX_LEVEL, int(player.patent_level)))
    cost, gain = config.patent_rate_by_level[lvl]
    return int(cost), int(gain)


# ----------------------------------------------------------------------------------------------
# Breakthroughs
# ----------------------------------------------------------------------------------------------
def _gray_dice_by_zone(player: PlayerState) -> List[int]:
    out: List[int] = []
    for zone in (player.glitched_dice, player.scanned_dice, player.ready_for_release_dice):
        out.extend(sorted(d.die_id for d in zone if d.color == DieColor.GRAY))
    return out


def triage_l3_options(engine: GameEngine, player: PlayerState) -> TriageUpgradeOptions:
    cost = int(engine.config.triage_l3_upgrade_cost)
    return TriageUpgradeOptions(
        gray_die_ids=_gray_dice_by_zone(player),
        colors=[c for c in MARKET_COLORS if engine.state.market.get(c, 0) > 0],
        cost=cost,
        affordable=player.money >= cost,
    )


def breakthrough_options(engine: GameEngine, player: PlayerState, track: str, level: int) -> Optional[TriageUpgradeOptions]:
    if normalize_track(track) == "TRIAGE" and level == 3:
        return triage_l3_options(engine, player)
    return None


def _new_die_id(engine: GameEngine) -> int:
    did = engine.state.next_die_id
    engine.state.next_die_id += 1
    return did


def _resolve_triage_l3(engine: GameEngine, player: PlayerState, choice: Optional[BreakthroughChoice], rec: BreakthroughRecord) -> None:
    opts = triage_l3_options(engine, player)
    if not opts.gray_die_ids:
        rec.outcome, rec.detail = "FORFEITED", {"reason": "no_gray_die"}
        return
    if not opts.colors:
        rec.outcome, rec.detail = "FORFEITED", {"reason": "market_empty"}
        return
    if not opts.affordable:
        rec.outcome, rec.detail = "FORFEITED", {"reason": "unaffordable"}
        return
    if choice is not None and not choice.accept:
        rec.outcome = "DECLINED"
        return
    gray_id = choice.gray_die_id if choice is not None else None
    if gray_id not in opts.gray_die_ids:
        gray_id = opts.gray_die_ids[0]
    color = choice.color if choice is not None else None
    if color is not None and not isinstance(color, DieColor):
        try:
            color = DieColor(str(color).lower())
        except ValueError:
            color = None
    if color not in opts.colors:  # chosen colour empty / illegal -> another colour
        color = next((c for c in TRIAGE_L3_COLOR_FALLBACK if c in opts.colors), opts.colors[0])

    # Atomic replacement (INV-RT-TRIAGE-L3-ATOMIC-01)
    for zone in (player.glitched_dice, player.scanned_dice, player.ready_for_release_dice):
        hit = next((d for d in zone if d.die_id == gray_id), None)
        if hit is not None:
            zone.remove(hit)
            break
    player.money -= opts.cost
    engine.state.market[color] -= 1
    new_die = create_colored_die(
        color=color,
        die_id=_new_die_id(engine),
        variant_card=engine.state.variant_cards.get(color),
    )
    player.ready_for_release_dice.append(new_die)
    player.triage_l3_upgrade_color = color.value
    rec.outcome = "TAKEN"
    rec.detail = {"gray_die_id": gray_id, "new_color": color.value, "new_die_id": new_die.die_id, "paid": opts.cost}


def resolve_breakthrough(
    engine: GameEngine,
    player: PlayerState,
    track: str,
    level: int,
    choice: Optional[BreakthroughChoice] = None,
) -> Optional[BreakthroughRecord]:
    """Resolves the Breakthrough printed at ``level`` of ``track`` (INV-RT-BT-IMMEDIATE-01).

    Returns ``None`` when the level has no Breakthrough, or when this player already resolved it
    (INV-RT-BT-ONCE-01).
    """
    t = normalize_track(track)
    if level not in BREAKTHROUGH_LEVELS:
        return None
    if any(b.track == t and b.level == level for b in player.breakthroughs):
        return None
    cfg = engine.config
    rec = BreakthroughRecord(track=t, level=level, round_number=engine.state.current_round, outcome="TAKEN")
    if t in ("DEFENSE", "RELEASE") and level == 1:
        die = create_gray_die(_new_die_id(engine), cfg.gray_face_profile)
        player.ready_for_release_dice.append(die)
        rec.detail = {"die_id": die.die_id}
    elif t in ("DEFENSE", "RELEASE") and level == 3:
        player.secrets += 1
        rec.detail = {"secrets": 1}
    elif t == "TRIAGE" and level == 1:
        want = int(cfg.triage_l1_contractors)
        n = max(0, min(want, engine.state.contractor_supply))
        ids = []
        for _ in range(n):
            w = create_white_die(_new_die_id(engine))
            player.contractor_dice.append(w)
            ids.append(w.die_id)
        engine.state.contractor_supply -= n
        # Free contractors don't count toward Progressive Contractor Pricing or the hire limit (OQ-6).
        rec.detail = {"contractors": n, "short": want - n, "die_ids": ids}
        if n == 0:
            rec.outcome = "FORFEITED"
    elif t == "TRIAGE" and level == 3:
        _resolve_triage_l3(engine, player, choice, rec)
    elif t == "PATENT" and level == 1:
        player.money += int(cfg.patent_l1_cash)
        rec.detail = {"money": int(cfg.patent_l1_cash)}
    elif t == "PATENT" and level == 3:
        if player.personal_purple_reserve > 0:
            player.personal_purple_reserve -= 1
            die = create_colored_die(color=DieColor.PURPLE, die_id=_new_die_id(engine), cost=0)
            player.ready_for_release_dice.append(die)
            rec.detail = {"die_id": die.die_id}
        else:
            rec.outcome, rec.detail = "FORFEITED", {"reason": "reserve_empty"}
    player.breakthroughs.append(rec)
    return rec


def ask_breakthrough_choice(
    engine: GameEngine,
    player: PlayerState,
    track: str,
    level: int,
    choices: Optional[Dict[Any, BreakthroughChoice]] = None,
) -> Optional[BreakthroughChoice]:
    t = normalize_track(track)
    if choices:
        c = choices.get((t, level))
        if c is not None:
            return c
    opts = breakthrough_options(engine, player, t, level)
    if opts is None:
        return None
    hook = getattr(player.bot, "choose_breakthrough", None)
    if hook is None:
        return None
    return hook(player, engine.state, t, level, opts)


def upgrade_and_resolve(
    engine: GameEngine,
    player: PlayerState,
    track: str,
    chooser: Any = None,
) -> Optional[BreakthroughRecord]:
    """Pays one step of ``track`` and resolves its Breakthrough (if any). ``chooser`` may be a
    ``BreakthroughChoice``, a dict ``{(track, level): BreakthroughChoice}``, or ``None`` (ask the bot).

    Returns the Breakthrough record, ``None`` if the step had no Breakthrough. Raises nothing; returns
    ``False`` when the step could not be paid.
    """
    t = normalize_track(track)
    if not player.upgrade_track(t):
        return False  # type: ignore[return-value]
    lvl = level_of(player, t)
    if lvl not in BREAKTHROUGH_LEVELS:
        return None
    if isinstance(chooser, BreakthroughChoice):
        choice: Optional[BreakthroughChoice] = chooser
    else:
        choice = ask_breakthrough_choice(engine, player, t, lvl, chooser if isinstance(chooser, dict) else None)
    return resolve_breakthrough(engine, player, t, lvl, choice)


# ----------------------------------------------------------------------------------------------
# Level 4 effects
# ----------------------------------------------------------------------------------------------
def defense_l4_cash(config: GameConfig, player: PlayerState, blocked_cubes: int) -> int:
    if not getattr(config, "is_v035_tracks", False) or player.defense_level < MAX_LEVEL:
        return 0
    return max(0, min(int(config.defense_l4_cash_cap), int(config.defense_l4_cash_per_block) * int(blocked_cubes)))


def triage_l4_research(config: GameConfig, player: PlayerState, moved_count: int) -> int:
    if not getattr(config, "is_v035_tracks", False) or player.triage_level < MAX_LEVEL:
        return 0
    return max(0, int(moved_count) - int(config.triage_l4_free_moves))


def free_rerolls_for(config: GameConfig, player: PlayerState, base: int) -> int:
    """Phase 1 free-reroll allowance; Release L4 adds its extra reroll after any throttle (OQ-7)."""
    if getattr(config, "is_v035_tracks", False) and player.release_level >= MAX_LEVEL:
        return int(base) + int(config.release_l4_extra_rerolls)
    return int(base)


def breakthrough_preview(player: PlayerState) -> Dict[str, Dict[str, Any]]:
    """Per-track next-level info for web capabilities."""
    out: Dict[str, Dict[str, Any]] = {}
    cfg = getattr(player, "config", None)
    for t in TRACKS:
        lvl = level_of(player, t)
        nxt = lvl + 1
        out[t] = {
            "level": lvl,
            "next_level": nxt if nxt <= MAX_LEVEL else None,
            "next_upgrade_cost": player.get_track_upgrade_cost(t),
            "breakthrough": BREAKTHROUGH_TEXT.get((t, nxt)) if cfg is not None and cfg.is_v035_tracks else None,
        }
        if t == "PATENT" and cfg is not None and getattr(cfg, "is_share_regain", False):
            cost, cap = regain_rate(cfg, player)
            out[t]["display_name"] = track_display_name(cfg, t)
            out[t]["regain_cost"] = cost
            out[t]["regain_cap"] = cap
    return out
