"""Web Phase 5: CI/CD Pipeline Shift (v0.34.0 six-phase).

Order: Magnetic Splice -> Production Return (to Scanned Box) -> Scanned Graduation (<= Release Bandwidth, dice of
the player's choice; fewer allowed) -> Conveyor Triage (Processing Box, oldest first, no choice) -> Market Leader
Bonus if a Red Secret face was banked this round (v0.38.0).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sim.config import ROUND_PHASE_NAMES, DieColor, RoundPhase
from sim.engine import phase5_pipeline_shift as p5, secret_faces

if TYPE_CHECKING:
    from web.controller.core import GameController
    from sim.engine.state import PlayerState


def _die_view(d) -> Dict[str, Any]:
    return {"die_id": d.die_id, "color": d.color.value, "cost": getattr(d, "cost", 0),
            "secret_pending": bool(getattr(d, "secret_pending", False)),
            "entry_seq": int(getattr(d, "processing_entry_seq", 0))}


def _processing_view(controller: GameController, player: PlayerState) -> List[Dict[str, Any]]:
    """Processing Box in Conveyor Triage order (oldest first), with each die's current Secret yield."""
    cfg = controller.state.config
    dice = secret_faces.triage_order(cfg, player, player.glitched_dice) if secret_faces.enabled(cfg) else list(player.glitched_dice)
    rows = []
    for i, d in enumerate(dice):
        v = _die_view(d)
        v["yield"] = secret_faces.die_yield(cfg, player, d)
        v["will_triage"] = i < player.triage_bandwidth
        rows.append(v)
    return rows


def _needs_choice(controller: GameController, player: PlayerState) -> Dict[str, Any]:
    n = p5.max_graduates(player)
    splice = p5.splice_available(controller.engine, player)
    return {
        "n": n,
        "release_bandwidth": player.release_bandwidth,
        "triage_bandwidth": player.triage_bandwidth,
        "candidates": [_die_view(d) for d in p5.default_graduate_priority(player.scanned_dice)],
        "default_graduate_ids": [d.die_id for d in p5.default_graduate_priority(player.scanned_dice)[:n]],
        "splice_available": splice,
        "hotfix_available": False,
        "processing_box": _processing_view(controller, player),
        "glitched": [_die_view(d) for d in player.glitched_dice],
        "needs_choice": len(player.scanned_dice) > player.release_bandwidth or splice,
    }


def _log_shift(controller: GameController, pid: int, rec, is_bot: bool) -> None:
    name = controller.player_meta[pid]["name"] + (" (Bot)" if is_bot else "")
    controller.event_log.append(
        f"{name} CI/CD Pipeline Shift: {len(rec.hotfixed_ids)} Magnetic Splice, {len(rec.returned_to_scanned_ids)} In Production -> Scanned, "
        f"{len(rec.graduated_ids)} Scanned -> Ready, {rec.held_in_scanned} held in Scanned, {len(rec.triaged_ids)} Processing Box -> Scanned (Conveyor Triage)."
    )


def enter_phase_5(controller: GameController) -> None:
    controller.phase = int(RoundPhase.CICD_PIPELINE_SHIFT)
    controller.phase_name = ROUND_PHASE_NAMES[controller.phase]
    controller.subphase = "choose_graduates"
    controller.pending_graduation = {}
    controller.last_pipeline_result = {}

    for pid, player in enumerate(controller.state.players):
        meta = controller.player_meta[pid]
        meta["pending_splice_die_id"] = None
        meta["shield_slots"] = {"red": [], "blue": [], "green": [], "any": []}
        if player.is_patient_zero:
            continue
        if not meta.get("is_human"):
            rec = p5.execute_player_pipeline_shift(controller.engine, player)
            controller.last_pipeline_result[pid] = rec.__dict__.copy()
            _log_shift(controller, pid, rec, is_bot=True)
            continue
        # Human: Production Return first (zones are independent of step 1), then decide whether to pause.
        returned = p5.production_return_to_scanned(controller.engine, player)
        meta["returned_to_scanned_ids"] = [d.die_id for d in returned]
        info = _needs_choice(controller, player)
        if info["needs_choice"]:
            controller.pending_graduation[pid] = info
        else:
            rec = p5.execute_player_pipeline_shift(
                controller.engine, player, production_already_returned=True, splice_die_id=None,
            )
            rec.returned_to_scanned_ids = meta["returned_to_scanned_ids"]
            controller.last_pipeline_result[pid] = rec.__dict__.copy()
            _log_shift(controller, pid, rec, is_bot=False)

    if not controller.pending_graduation:
        _finish_phase_5(controller)


def _finish_phase_5(controller: GameController) -> None:
    from web.controller.phase6_operations_actions import enter_phase_6

    controller.pending_graduation = {}
    _fire_market_leader_bonus(controller)
    enter_phase_6(controller)


def _fire_market_leader_bonus(controller: GameController) -> None:
    """Step 5 (v0.38.0): Market Leader Bonus at the end of Phase 5 if a Red Secret face was banked this round."""
    cfg = controller.state.config
    controller.last_round_bonus = None
    if not secret_faces.enabled(cfg):
        return
    before = len(controller.state.red_secret_payouts)
    if not secret_faces.fire_round_payout(cfg, controller.state):
        return
    rec = controller.state.red_secret_payouts[before]
    names = controller.player_meta
    parts = ", ".join(
        f"{names[pid]['name']} {rec['places'][pid]}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(rec['places'][pid], 'th')} +{k}"
        for pid, k in sorted(rec["gains"].items(), key=lambda kv: (rec["places"][kv[0]], kv[0]))
    )
    controller.event_log.append(f"MARKET LEADER BONUS (Red Secret face banked this round): {parts}.")
    controller.last_round_bonus = {
        "round": rec["round"], "places": {str(k): v for k, v in rec["places"].items()},
        "gains": {str(k): v for k, v in rec["gains"].items()}, "shares": {str(k): v for k, v in rec["shares"].items()},
    }


def choose_graduates(
    controller: GameController,
    player_id: int,
    graduate_die_ids: Optional[List[int]],
    splice_die_id: Optional[int] = None,
    hotfix_die_id: Optional[int] = None,
) -> Dict[str, Any]:
    if controller.phase != int(RoundPhase.CICD_PIPELINE_SHIFT) or controller.subphase != "choose_graduates":
        raise ValueError(f"Cannot choose graduates in phase {controller.phase}")
    if player_id not in controller.pending_graduation:
        raise ValueError(f"Player {player_id} has no pending Scanned Graduation choice")
    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]
    info = controller.pending_graduation[player_id]

    ids: List[int] = []
    seen = set()
    for raw in graduate_die_ids or []:
        did = int(raw)
        if did not in seen:
            seen.add(did)
            ids.append(did)
    scanned_ids = {d.die_id for d in player.scanned_dice}
    bad = [i for i in ids if i not in scanned_ids]
    if bad:
        raise ValueError(f"Die ids {bad} are not in the Scanned Box")
    if len(ids) > info["n"]:
        raise ValueError(f"Cannot graduate {len(ids)} dice: Release Bandwidth allows at most {info['n']}")

    splice = splice_die_id if splice_die_id is not None else meta.get("pending_splice_die_id")
    if splice is not None and not any(d.die_id == splice for d in player.glitched_dice):
        raise ValueError(f"Magnetic Splice die {splice} is not in the Processing Box")

    rec = p5.execute_player_pipeline_shift(
        controller.engine,
        player,
        graduate_die_ids=ids,
        splice_die_id=splice,
        production_already_returned=True,
    )
    rec.returned_to_scanned_ids = meta.get("returned_to_scanned_ids", [])
    controller.last_pipeline_result[player_id] = rec.__dict__.copy()
    _log_shift(controller, player_id, rec, is_bot=False)
    del controller.pending_graduation[player_id]
    if not controller.pending_graduation:
        _finish_phase_5(controller)
    return controller.get_full_state()


def record_magnetic_splice(controller: GameController, player_id: int, die_id: Optional[int] = None,
                           die_index: int = 0) -> Dict[str, Any]:
    """Omnidyne Magnetic Splice (Phase 5 step 1): records the Processing Box die to splice."""
    if controller.phase != int(RoundPhase.CICD_PIPELINE_SHIFT) or player_id not in controller.pending_graduation:
        raise ValueError(f"Cannot use Omnidyne Magnetic Splice in phase {controller.phase}")
    player = controller.state.players[player_id]
    if not controller.pending_graduation[player_id].get("splice_available"):
        raise ValueError("Omnidyne/Phreaker ability is not available")
    if die_id is None:
        if not (0 <= die_index < len(player.glitched_dice)):
            raise ValueError(f"Invalid die_index {die_index} in the Processing Box")
        die_id = player.glitched_dice[die_index].die_id
    if not any(d.die_id == die_id for d in player.glitched_dice):
        raise ValueError(f"Die with die_id {die_id} is not in the Processing Box")
    controller.player_meta[player_id]["pending_splice_die_id"] = die_id
    controller.event_log.append(
        f"{controller.player_meta[player_id]['name']} queued Omnidyne Magnetic Splice (Processing Box -> Ready for Release in Phase 5)."
    )
    return controller.get_full_state()
