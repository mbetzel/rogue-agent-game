"""v0.38.0 candidate: Secret faces, Processing Box banking and Glitched Shield Slots (spec v380 §3, §7).

Pure helpers shared by the phase modules. Nothing here draws from the RNG. Every function is a no-op (or is
never called) unless ``config.secret_face_enabled`` / ``config.glitched_shield_slots_enabled`` is on, so the
v0.37 path is untouched.

Terminology: the Processing Box is ``PlayerState.glitched_dice`` (attribute kept for v0.37 fixtures / web).
``secret_yield`` / ``slot`` are implementation names, not game terms.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterable, List, Optional

from sim.config import DieColor

if TYPE_CHECKING:
    from sim.config import GameConfig
    from sim.engine.state import PlayerState
    from sim.entities import Die

SECRET_COLORS = (DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.PURPLE)


def enabled(cfg: Any) -> bool:
    return bool(getattr(cfg, "secret_face_enabled", False))


def slots_enabled(cfg: Any) -> bool:
    return bool(getattr(cfg, "glitched_shield_slots_enabled", False))


def _ckey(color: Any) -> str:
    return getattr(color, "value", str(color))


# ---------------------------------------------------------------------------
# Yields (INV-SF-03: computed at banking time from current state)
# ---------------------------------------------------------------------------
def secret_yield(cfg: "GameConfig", p: "PlayerState", color: Any) -> int:
    """Corporate Secrets a pending die of ``color`` would bank right now (spec §7.5)."""
    color = DieColor(color) if not isinstance(color, DieColor) else color
    if color == DieColor.RED:
        share = int(p.market_share or 0)
        for min_share, y in cfg.secret_yield_red_tiers:
            if share >= min_share:
                return int(y)
        return 0
    if color == DieColor.BLUE:
        y = int(cfg.secret_yield_blue_base)
        if int(getattr(p, "blocked_blue_this_round", 0)) > 0:
            y += int(cfg.secret_yield_blue_block_bonus)
        if int(p.defense_level) >= 3:
            y += int(cfg.secret_yield_blue_grid_l3_bonus)
        return min(int(cfg.secret_yield_blue_cap), y)
    if color == DieColor.GREEN:
        return max(0, int(cfg.secret_yield_green_base) - int(getattr(p, "glitched_shield_slots", 0)))
    if color == DieColor.PURPLE:
        return int(cfg.secret_yield_purple)
    return 0


def die_yield(cfg: "GameConfig", p: "PlayerState", die: "Die") -> int:
    return secret_yield(cfg, p, die.color) if getattr(die, "secret_pending", False) else 0


def default_triage_order(cfg: "GameConfig", p: "PlayerState", dice: Iterable["Die"]) -> List["Die"]:
    """Highest current yield first; ties lowest die_id (spec §9 ``choose_triage_order``)."""
    return sorted(dice, key=lambda d: (-die_yield(cfg, p, d), d.die_id))


# ---------------------------------------------------------------------------
# Processing Box entry / exit
# ---------------------------------------------------------------------------
def enter_processing_box(p: "PlayerState", die: "Die") -> None:
    """A die showing the Secret face after rerolls (Phase 1 Step 5b)."""
    die.secret_pending = True
    k = _ckey(die.color)
    p.secret_faces_rolled[k] = p.secret_faces_rolled.get(k, 0) + 1
    p.glitched_dice.append(die)


def bank(cfg: "GameConfig", p: "PlayerState", die: "Die") -> int:
    """Banks the Secret of a die leaving the Processing Box (INV-SF-01: once per visit). Returns Secrets gained.
    Call *after* removing the die from ``glitched_dice``; a die without ``secret_pending`` yields 0."""
    if not getattr(die, "secret_pending", False):
        return 0
    y = secret_yield(cfg, p, die.color)
    die.secret_pending = False
    k = _ckey(die.color)
    p.secret_faces_banked[k] = p.secret_faces_banked.get(k, 0) + 1
    hist = p.secret_yield_hist.setdefault(k, {})
    hist[str(y)] = hist.get(str(y), 0) + 1
    if y > 0:
        p.gain_secrets(y, f"secret_face_{k}")
    return y


def lose_pending(p: "PlayerState", die: "Die") -> bool:
    """A pending die removed from the Processing Box without banking (Return Colored Die, Burn Notice)."""
    if not getattr(die, "secret_pending", False):
        return False
    die.secret_pending = False
    p.secrets_lost_returned += 1
    return True


def stranded(cfg: "GameConfig", p: "PlayerState") -> tuple:
    """(dice, would-be Secrets) still pending in the Processing Box (INV-SF-02; telemetry only, pure)."""
    pend = [d for d in p.glitched_dice if getattr(d, "secret_pending", False)]
    return len(pend), sum(secret_yield(cfg, p, d.color) for d in pend)


# ---------------------------------------------------------------------------
# Glitched Shield Slots (INV-SF-05)
# ---------------------------------------------------------------------------
def effective_capacity(p: "PlayerState") -> int:
    return max(0, int(p.defense_capacity) - int(getattr(p, "glitched_shield_slots", 0)))


def glitch_slots(p: "PlayerState", n: int, source: str) -> int:
    """Glitches up to ``n`` shield slots, capped at Defense Grid capacity (excess has no effect)."""
    n = max(0, int(n))
    cap = getattr(getattr(p, "config", None), "glitched_slots_per_round_cap", None)
    if cap is not None:
        n = min(n, max(0, int(cap) - int(p.slots_glitched_this_round)))
    room = max(0, int(p.defense_capacity) - int(p.glitched_shield_slots))
    done = min(n, room)
    if done:
        p.glitched_shield_slots += done
        p.slots_glitched_this_round += done
        p.slots_glitched_by_source[source] = p.slots_glitched_by_source.get(source, 0) + done
        p.max_glitched_slots = max(p.max_glitched_slots, p.glitched_shield_slots)
    return done


def clean_slots(p: "PlayerState", n: int, how: str) -> int:
    """Cleans up to ``n`` glitched slots. ``how``: ``"die"`` (placement), ``"face"`` (Green F1 / G1 / G2),
    ``"graduation"`` (Phase 5 step 3b)."""
    done = min(max(0, int(n)), int(p.glitched_shield_slots))
    if done:
        p.glitched_shield_slots -= done
        attr = {"die": "slots_cleaned_by_die", "face": "slots_cleaned_by_face",
                "graduation": "slots_cleared_by_graduation"}[how]
        setattr(p, attr, getattr(p, attr) + done)
    return done


def record_round_start(p: "PlayerState") -> None:
    """Phase 1 start (survivors): reset the Blue block flag and log per-round ownership / slot telemetry."""
    p.blocked_blue_this_round = 0
    p.slots_glitched_this_round = 0
    owned = {}
    for d in p.total_dice:
        if d.color in (DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW, DieColor.PURPLE):
            owned[_ckey(d.color)] = owned.get(_ckey(d.color), 0) + 1
    p.colored_dice_owned_by_round.append(owned)


def best_pending(cfg: "GameConfig", p: "PlayerState", prefer_id: Optional[int] = None) -> Optional["Die"]:
    if not p.glitched_dice:
        return None
    if prefer_id is not None:
        hit = next((d for d in p.glitched_dice if d.die_id == prefer_id), None)
        if hit is not None:
            return hit
    return default_triage_order(cfg, p, p.glitched_dice)[0]
