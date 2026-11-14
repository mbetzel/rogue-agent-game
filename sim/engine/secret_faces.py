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
        flat = getattr(cfg, "red_secret_owner_yield", None)
        if flat is not None:  # RSP-1 (spec §14.5.1): flat owner yield, Market Share tiers ignored
            return int(flat)
        share = int(p.market_share or 0)
        for min_share, y in cfg.secret_yield_red_tiers:
            if share >= min_share:
                return int(y)
        return 0
    if color == DieColor.BLUE:
        y = int(cfg.secret_yield_blue_base)
        if cfg.secret_yield_blue_block_bonus > 0 and int(getattr(p, "blocked_blue_this_round", 0)) > 0:
            y += int(cfg.secret_yield_blue_block_bonus)
        if int(p.defense_level) >= 3:
            y += int(cfg.secret_yield_blue_grid_l3_bonus)
        return min(int(cfg.secret_yield_blue_cap), y)
    if color == DieColor.GREEN:
        if getattr(cfg, "secret_yield_green_glitch_penalty", True):
            return max(0, int(cfg.secret_yield_green_base) - int(getattr(p, "glitched_shield_slots", 0)))
        return int(cfg.secret_yield_green_base)
    if color == DieColor.PURPLE:
        return int(cfg.secret_yield_purple)
    return 0


def die_yield(cfg: "GameConfig", p: "PlayerState", die: "Die") -> int:
    return secret_yield(cfg, p, die.color) if getattr(die, "secret_pending", False) else 0


def default_triage_order(cfg: "GameConfig", p: "PlayerState", dice: Iterable["Die"]) -> List["Die"]:
    """Highest current yield first; colored dice before Gray; ties lowest die_id (spec §9 ``choose_triage_order``)."""
    return sorted(
        dice,
        key=lambda d: (-die_yield(cfg, p, d), 0 if d.color != DieColor.GRAY else 1, d.die_id),
    )


# ---------------------------------------------------------------------------
# Processing Box entry / exit
# ---------------------------------------------------------------------------
def triage_order(cfg: "GameConfig", p: "PlayerState", dice: Iterable["Die"]) -> List["Die"]:
    """RSP-1 ``triage_order_rule="OLDEST_FIRST"`` (spec §14.5.4): Processing Box entry order (stable on ties)."""
    return sorted(dice, key=lambda d: int(getattr(d, "processing_entry_seq", 0)))


def enter_processing_box(p: "PlayerState", die: "Die", round_no: int = 0) -> None:
    """A die showing the Secret face after rerolls (Phase 1 Step 5b)."""
    die.secret_pending = True
    p.processing_entry_counter += 1
    die.processing_entry_seq = p.processing_entry_counter
    die.processing_entry_round = int(round_no)
    k = _ckey(die.color)
    p.secret_faces_rolled[k] = p.secret_faces_rolled.get(k, 0) + 1
    p.glitched_dice.append(die)


def bank(cfg: "GameConfig", p: "PlayerState", die: "Die", state: Any = None) -> int:
    """Banks the Secret of a die leaving the Processing Box (INV-SF-01: once per visit). Returns Secrets gained.
    Call *after* removing the die from ``glitched_dice``; a die without ``secret_pending`` yields 0.

    Under v0.38d (Variant B: COUNT_THEN_CLEAN), Green calculates yield on current glitched slots, awards Secrets,
    and then cleans 1 Glitched Shield Slot (INV-V38D-05)."""
    if not getattr(die, "secret_pending", False) or die.color == DieColor.GRAY:
        die.secret_pending = False
        return 0

    clean_mode = getattr(cfg, "green_triage_clean_mode", "NONE")
    if clean_mode == "NONE" and getattr(cfg, "green_bank_cleans_slot", False):
        clean_mode = "COUNT_THEN_CLEAN"

    # Variant A support (for sensitivity/comparison testing)
    if clean_mode == "CLEAN_THEN_COUNT" and die.color == DieColor.GREEN:
        clean_slots(p, 1, "green_triage")
        y = secret_yield(cfg, p, die.color)
    else:
        # Variant B (Standard approved rule) and NONE
        y = secret_yield(cfg, p, die.color)
        if clean_mode == "COUNT_THEN_CLEAN" and die.color == DieColor.GREEN:
            clean_slots(p, 1, "green_triage")

    if die.color == DieColor.RED:
        p.red_secrets_banked += 1
        if die.processing_entry_round and state is not None:
            p.red_processing_wait_rounds += int(state.current_round) - int(die.processing_entry_round)
            p.red_processing_wait_count += 1
        if state is not None:
            state.red_secret_banked_this_round = True
            state.red_secrets_banked_this_round += 1
            state.red_bankers_this_round.append(p.player_id)
            rb = state.red_banks_by_round
            while len(rb) < int(state.current_round):
                rb.append(0)
            rb[int(state.current_round) - 1] += 1
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
    """Cleans up to ``n`` glitched slots. ``how``: ``"die"`` (placement), ``"face"`` (Green F1 / G1),
    ``"graduation"`` (Phase 5 step 3b), ``"green_triage"`` (Phase 5 step 1 Green banking)."""
    done = min(max(0, int(n)), int(p.glitched_shield_slots))
    if done:
        p.glitched_shield_slots -= done
        attr = {
            "die": "slots_cleaned_by_die",
            "face": "slots_cleaned_by_face",
            "graduation": "slots_cleared_by_graduation",
            "green_triage": "slots_cleaned_by_green_triage",
        }[how]
        setattr(p, attr, getattr(p, attr) + done)
    return done


def reset_round_flags(state: Any) -> None:
    """RSP-1 Phase 1 entry (spec §14.5.3 step 1, INV-RSP-01b)."""
    state.red_secret_banked_this_round = False
    state.red_secrets_banked_this_round = 0
    state.red_bankers_this_round = []


def red_secret_payout_awards(cfg: "GameConfig", state: Any) -> dict:
    """player_id -> (place, Secrets) for the non-Patient-Zero players by current Market Share (ties share the better
    place; schedule by starting player count). Pure; {} when the payout is off or nobody survives."""
    from sim.engine.market_share import market_leader_bonus_awards

    sched = cfg.red_secret_payout_schedule(len(state.players))
    shares = {q.player_id: int(q.market_share or 0) for q in state.players if not q.is_patient_zero}
    if not sched or not shares:
        return {}
    return market_leader_bonus_awards(shares, sched)


def fire_round_payout(cfg: "GameConfig", state: Any) -> bool:
    """RSP-1 Phase 5 end hook (spec §14.5.3 step 2): at most one Red Secret payout per round, iff a Red Secret
    was banked this round. Credits ``gain_secrets(k, "red_secret_payout")``."""
    if not cfg.is_red_secret_payout or not state.red_secret_banked_this_round:
        return False
    awards = red_secret_payout_awards(cfg, state)
    if not awards:
        return False
    by_pid = {q.player_id: q for q in state.players}
    shares, places, gains = {}, {}, {}
    for pid, (place, k) in sorted(awards.items()):
        q = by_pid[pid]
        shares[pid], places[pid], gains[pid] = int(q.market_share or 0), place, k
        q.red_payout_places[str(place)] = q.red_payout_places.get(str(place), 0) + 1
        if k > 0:
            q.gain_secrets(k, "red_secret_payout")
            q.red_payout_secrets += k
    state.red_secret_payouts.append({
        "round": int(state.current_round), "red_banks_this_round": int(state.red_secrets_banked_this_round),
        "banker_pids": sorted(set(state.red_bankers_this_round)),
        "shares": shares, "places": places, "gains": gains,
    })
    state.red_secret_payouts_fired += 1
    return True


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
