"""Phase 5: CI/CD Pipeline Shift (Simultaneous).

D1 order (v0.34.0):
  1. Emergency Hotfix & Magnetic Splice: each moves 1 die Glitched -> Ready for Release.
  2. Production Return: every In Production die -> Scanned Box.
  3. Scanned Graduation: up to ``release_bandwidth`` dice of the player's choice Scanned -> Ready (OQ-1:
     the player may graduate fewer).
  4. Conveyor Triage: up to ``triage_bandwidth`` dice Glitched -> Scanned (FIFO in the sim, OQ-8).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional

from sim.config import DieColor, SignatureCubeLocation
from sim.entities import has_company_override, has_signature_protocol, legacy_bridge_enabled
from sim.entities import ArchetypeCode, CompanyCode
from sim.engine.state import PipelineShiftRecord
from sim.engine import secret_faces

if TYPE_CHECKING:
    from sim.engine.core import GameEngine
    from sim.engine.state import PlayerState
    from sim.entities import Die


_ASK = ...  # sentinel: "use the bot / engine default"


def reset_die_for_pipeline(die: Die) -> None:
    die.production_role = None
    die.is_locked = False
    die.chosen_choice_index = None
    die.current_face = None


def _best_colored_glitched_index(player: PlayerState) -> int:
    return max(
        range(len(player.glitched_dice)),
        key=lambda i: (
            1 if player.glitched_dice[i].color != DieColor.GRAY else 0,
            getattr(player.glitched_dice[i], "cost", 0),
        ),
    )


def _is_omnidyne(engine: GameEngine, player: PlayerState) -> bool:
    """Omnidyne Magnetic Splice comes only from the Client Company (legacy bridge aside)."""
    return has_company_override(player, CompanyCode.OMNIDYNE, legacy_bridge_enabled(engine))


def splice_available(engine: GameEngine, player: PlayerState) -> bool:
    active_ver = engine.state.active_version.version_str
    return _is_omnidyne(engine, player) and player.is_ability_available(active_ver) and bool(player.glitched_dice)


def apply_hotfix_bypass(
    engine: GameEngine,
    player: PlayerState,
    splice_die_id: Any = _ASK,
    hotfix_die_id: Any = _ASK,
) -> List[Die]:
    """Step 1: Emergency Hotfix & Magnetic Splice.

    ``splice_die_id``: ``...`` = bot hook (``choose_omnidyne_override``), ``None`` = decline, int = that die.
    ``hotfix_die_id``: ``...`` / ``None`` = engine default (best colored), int = that die (OQ-9).
    """
    moved: List[Die] = []
    active_ver = engine.state.active_version.version_str

    # Omnidyne Systems (Magnetic Splice)
    if splice_available(engine, player) and splice_die_id is not None:
        target_id = (
            player.bot.choose_omnidyne_override(player, engine.state, engine.rng)
            if splice_die_id is _ASK
            else splice_die_id
        )
        chosen_idx = None
        if target_id is not None:
            for i, d in enumerate(player.glitched_dice):
                if d.die_id == target_id:
                    chosen_idx = i
                    break
        if chosen_idx is None:
            if secret_faces.enabled(engine.config):
                best = secret_faces.best_pending(engine.config, player)
                chosen_idx = next(i for i, d in enumerate(player.glitched_dice) if d is best)
            else:
                chosen_idx = _best_colored_glitched_index(player)
        die = player.glitched_dice.pop(chosen_idx)
        reset_die_for_pipeline(die)
        secret_faces.bank(engine.config, player, die, engine.state)  # v0.38: banks (yield at Phase 5 step 1); no-op otherwise
        player.ready_for_release_dice.append(die)
        player.mark_ability_used(active_ver)
        moved.append(die)

    # Emergency Hotfix (Triage Track Level 2)
    if getattr(player, "has_emergency_hotfix", False) and player.glitched_dice:
        h_idx = None
        if hotfix_die_id is not _ASK and hotfix_die_id is not None:
            h_idx = next((i for i, d in enumerate(player.glitched_dice) if d.die_id == hotfix_die_id), None)
        if h_idx is None:
            h_idx = _best_colored_glitched_index(player)
        die = player.glitched_dice.pop(h_idx)
        reset_die_for_pipeline(die)
        secret_faces.bank(engine.config, player, die, engine.state)
        player.ready_for_release_dice.append(die)
        moved.append(die)
    return moved


def production_return_to_scanned(engine: GameEngine, player: PlayerState) -> List[Die]:
    """Step 2: every In Production die -> Scanned Box (INV-PIPE-PROD-TO-SCANNED-01)."""
    moved = list(player.in_production_dice)
    whites = [d for d in moved if d.color == DieColor.WHITE]
    if whites:
        raise AssertionError(
            f"INV-PIPE-PROD-TO-SCANNED-01: White Contractor dice {[d.die_id for d in whites]} remain In Production "
            "at Phase 5; contractors must expire at the end of Phase 4."
        )
    for die in moved:
        reset_die_for_pipeline(die)
        player.scanned_dice.append(die)
    player.in_production_dice.clear()
    return moved


def production_return_to_ready(player: PlayerState) -> List[Die]:
    """Legacy v0.33: all surviving In Production dice return straight to Ready for Release."""
    moved = list(player.in_production_dice)
    for p_die in player.in_production_dice:
        reset_die_for_pipeline(p_die)
        player.ready_for_release_dice.append(p_die)
    player.in_production_dice.clear()
    return moved


def default_graduate_priority(scanned: Iterable[Die]) -> List[Die]:
    """Default Scanned Graduation priority: Purple, then Colored by descending cost, then Gray; ties by die_id."""
    key = lambda d: (  # noqa: E731
        0 if d.color == DieColor.PURPLE else (1 if d.color != DieColor.GRAY else 2),
        -getattr(d, "cost", 0),
        d.die_id,
    )
    return sorted(scanned, key=key)


def max_graduates(player: PlayerState) -> int:
    return min(len(player.scanned_dice), player.release_bandwidth)


def validate_graduate_ids(player: PlayerState, requested: Optional[Iterable[Any]], n: int) -> List[Die]:
    """INV-PIPE-GRAD-CHOICE-01: dedupe, keep only Scanned dice, cap at ``n``; invalid / duplicate entries
    are replaced by the default priority, but a short list is never back-filled (OQ-1)."""
    if requested is None:
        return []
    raw = list(requested)
    want = min(len(raw), n)
    by_id = {d.die_id: d for d in player.scanned_dice}
    chosen: List[Die] = []
    seen = set()
    for item in raw:
        if len(chosen) >= want:
            break
        did = getattr(item, "die_id", item)
        try:
            did = int(did)
        except (TypeError, ValueError):
            continue
        if did in seen or did not in by_id:
            continue
        seen.add(did)
        chosen.append(by_id[did])
    if len(chosen) < want:
        for d in default_graduate_priority(player.scanned_dice):
            if len(chosen) >= want:
                break
            if d.die_id not in seen:
                seen.add(d.die_id)
                chosen.append(d)
    return chosen


def graduate_scanned(
    engine: GameEngine,
    player: PlayerState,
    chosen_die_ids: Optional[List[int]] = None,
    *,
    use_bot_choice: bool = True,
) -> List[Die]:
    """Step 3: Scanned Graduation (<= release_bandwidth, INV-PIPE-RELEASE-CAP-01)."""
    n = max_graduates(player)
    if n <= 0:
        return []
    if chosen_die_ids is None and not use_bot_choice:
        graduates = list(player.scanned_dice[:n])  # legacy FIFO
    else:
        if chosen_die_ids is None:
            hook = getattr(player.bot, "choose_scanned_graduates", None)
            if hook is not None:
                chosen_die_ids = list(hook(player, n, engine.state, engine.rng))
            else:
                chosen_die_ids = [d.die_id for d in default_graduate_priority(player.scanned_dice)[:n]]
        graduates = validate_graduate_ids(player, chosen_die_ids, n)
    for die in graduates:
        player.scanned_dice.remove(die)
        reset_die_for_pipeline(die)
        player.ready_for_release_dice.append(die)
    return graduates


def conveyor_triage(player: PlayerState) -> List[Die]:
    """Step 4: Conveyor Triage (FIFO, OQ-8) - up to triage_bandwidth Glitched -> Scanned."""
    moved: List[Die] = []
    triage_count = min(len(player.glitched_dice), player.triage_bandwidth)
    for _ in range(triage_count):
        g_die = player.glitched_dice.pop(0)
        reset_die_for_pipeline(g_die)
        player.scanned_dice.append(g_die)
        moved.append(g_die)
    return moved


def graduation_slot_clear(engine: GameEngine, player: PlayerState, graduated: int) -> int:
    """v0.38 step 3b: once per Phase 5, if >= 1 die graduated, clear ``slot_graduation_clear`` slot(s)."""
    player.slot_clear_used_this_phase5 = False
    if graduated <= 0 or player.glitched_shield_slots <= 0 or engine.config.slot_graduation_clear <= 0:
        return 0
    player.slot_clear_used_this_phase5 = True
    return secret_faces.clean_slots(player, engine.config.slot_graduation_clear, "graduation")


def check_and_queue_signature_cube(engine: GameEngine, player: PlayerState) -> bool:
    """Invoked during Conveyor Triage whenever a die banks a Secret (INV-TL-03)."""
    if not getattr(engine.config, "target_lock_enabled", False):
        return False

    if player.signature_cube_location == SignatureCubeLocation.IDLE_ON_MAT:
        player.signature_cube_location = SignatureCubeLocation.STAGING_CUP
        player.baffle_hold_visits += 1
        player.target_lock_baffle_rounds = 0
        engine.state.staging_signature_cubes.add(player.player_id)
        return True

    return False


def conveyor_triage_v038(engine: GameEngine, player: PlayerState) -> List[Die]:
    """v0.38 step 4: up to ``triage_bandwidth`` dice of the player's choice Processing Box -> Scanned Box,
    banking each pending Secret at the current yield (default order: highest yield, then lowest die_id)."""
    n = min(len(player.glitched_dice), player.triage_bandwidth)
    if n <= 0:
        return []
    if engine.config.triage_order_rule == "OLDEST_FIRST":
        # RSP-1 (spec §14.5.4, INV-RSP-06): entry order, the bot hook is not called
        raw = secret_faces.triage_order(engine.config, player, player.glitched_dice)
    else:
        raw = player.bot.choose_triage_order(player, list(player.glitched_dice), engine.state)
    order: List[Die] = []
    for d in list(raw or []) + secret_faces.default_triage_order(engine.config, player, player.glitched_dice):
        if any(d is x for x in player.glitched_dice) and not any(d is x for x in order):
            order.append(d)
    moved = order[:n]
    for d in moved:
        player.glitched_dice.remove(d)
        was_secret = getattr(d, "secret_pending", False) and d.color != DieColor.GRAY
        reset_die_for_pipeline(d)
        banked = secret_faces.bank(engine.config, player, d, engine.state)
        if was_secret and banked > 0:
            check_and_queue_signature_cube(engine, player)
        player.scanned_dice.append(d)
    return moved


def execute_player_pipeline_shift(
    engine: GameEngine,
    player: PlayerState,
    *,
    graduate_die_ids: Optional[List[int]] = None,
    splice_die_id: Any = _ASK,
    hotfix_die_id: Any = _ASK,
    production_already_returned: bool = False,
) -> PipelineShiftRecord:
    rec = PipelineShiftRecord()
    rec.hotfixed_ids = [d.die_id for d in apply_hotfix_bypass(engine, player, splice_die_id, hotfix_die_id)]
    if not production_already_returned:
        rec.returned_to_scanned_ids = [d.die_id for d in production_return_to_scanned(engine, player)]
    rec.graduated_ids = [d.die_id for d in graduate_scanned(engine, player, graduate_die_ids)]
    rec.held_in_scanned = len(player.scanned_dice)
    if secret_faces.slots_enabled(engine.config):
        graduation_slot_clear(engine, player, len(rec.graduated_ids))
    if secret_faces.enabled(engine.config):
        rec.triaged_ids = [d.die_id for d in conveyor_triage_v038(engine, player)]
    else:
        rec.triaged_ids = [d.die_id for d in conveyor_triage(player)]
    pay_triage_l4(engine, player, len(rec.triaged_ids))
    return rec


def pay_triage_l4(engine: GameEngine, player: PlayerState, moved_count: int) -> int:
    """v0.35.0 Triage L4: +1 research per die moved in Conveyor Triage beyond the 2nd (INV-RT-TRIAGE-L4-01)."""
    from sim.engine import research_tracks

    gain = research_tracks.triage_l4_research(engine.config, player, moved_count)
    if gain > 0:
        player.gain_research(gain, "triage_l4")
        player.l4_payouts["triage_research"] = player.l4_payouts.get("triage_research", 0) + gain
    return gain


def execute_pipeline_shift(engine: GameEngine) -> Dict[int, PipelineShiftRecord]:
    """Phase 5 for every survivor (simultaneous). Does not pass the First Player Marker (Phase 6)."""
    out: Dict[int, PipelineShiftRecord] = {}
    if engine.state.game_over:
        return out
    for player in engine.state.players:
        if player.is_patient_zero:
            continue
        out[player.player_id] = execute_player_pipeline_shift(engine, player)
    # RSP-1 Phase 5 end hook (spec §14.5.3 step 2): lives inside the phase function so _run_round_six_phase and
    # fast_clone.resume_round need no change (they call this function).
    if secret_faces.enabled(engine.config):
        secret_faces.fire_round_payout(engine.config, engine.state)
    return out


def execute_pipeline_prep_v033(engine: GameEngine) -> None:
    """Legacy v0.33 Part 3B (verbatim order): Hotfix/Splice -> Scanned->Ready (FIFO) -> Triage -> Production->Ready."""
    for player in engine.state.players:
        if player.is_patient_zero:
            continue

        active_ver = engine.state.active_version.version_str

        # 1. Hotfix Capabilities (Omnidyne Magnetic Splice & Emergency Hotfix)
        is_omnidyne = _is_omnidyne(engine, player) and player.is_ability_available(active_ver)
        if is_omnidyne and player.glitched_dice:
            target_id = player.bot.choose_omnidyne_override(player, engine.state, engine.rng)
            chosen_idx = None
            if target_id is not None:
                for i, d in enumerate(player.glitched_dice):
                    if d.die_id == target_id:
                        chosen_idx = i
                        break
            if chosen_idx is None:
                chosen_idx = _best_colored_glitched_index(player)
            omnidyne_die = player.glitched_dice.pop(chosen_idx)
            reset_die_for_pipeline(omnidyne_die)
            player.ready_for_release_dice.append(omnidyne_die)
            player.mark_ability_used(active_ver)

        if getattr(player, "has_emergency_hotfix", False) and player.glitched_dice:
            h_die = player.glitched_dice.pop(_best_colored_glitched_index(player))
            reset_die_for_pipeline(h_die)
            player.ready_for_release_dice.append(h_die)

        # 2. Scanned Graduation (FIFO)
        graduate_scanned(engine, player, None, use_bot_choice=False)

        # 3. Conveyor Triage
        conveyor_triage(player)

        # 4. Production Return -> Ready
        production_return_to_ready(player)
