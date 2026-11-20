"""Web Phase 6: CI/CD Pipeline Shift (v0.49.0: after Phase 5 Operations).

Order: Magnetic Splice -> Production Return (Current Sprint if empty, else Next Sprint) -> Sprint Review (exactly
Release Bandwidth dice, all of them if fewer: Current Sprint first, then Next Sprint dice of the player's choice)
-> Conveyor Triage (Research & Development, oldest first, no choice) -> Market Leader
Bonus if a Red R&D face was banked this round (v0.38.0).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sim.config import DieColor
from web.controller import phases
from sim.engine import phase5_pipeline_shift as p5, secret_faces, sprint_plan

if TYPE_CHECKING:
    from web.controller.core import GameController
    from sim.engine.state import PlayerState


def _die_view(d) -> Dict[str, Any]:
    return {"die_id": d.die_id, "color": d.color.value, "cost": getattr(d, "cost", 0),
            "secret_pending": bool(getattr(d, "secret_pending", False)),
            "entry_seq": int(getattr(d, "processing_entry_seq", 0))}


def _processing_view(controller: GameController, player: PlayerState) -> List[Dict[str, Any]]:
    """Research & Development in Conveyor Triage order (oldest first), with each die's current Secret yield."""
    cfg = controller.state.config
    dice = secret_faces.triage_order(cfg, player, player.glitched_dice) if secret_faces.enabled(cfg) else list(player.glitched_dice)
    rows = []
    for i, d in enumerate(dice):
        v = _die_view(d)
        v["yield"] = secret_faces.die_yield(cfg, player, d)
        v["will_triage"] = i < player.triage_bandwidth
        rows.append(v)
    return rows


def _sprint_choice(controller: GameController, player: PlayerState) -> Dict[str, Any]:
    """v0.48+ Sprint Review: exactly ``min(Release Bandwidth, |Sprint Plan|)`` dice are released, Current Sprint
    first; the player chooses only which Current Sprint dice (if it holds more than the bandwidth) or which Next
    Sprint dice fill the spare bandwidth."""
    sprint_plan.prune(player)
    bw = player.effective_release_bandwidth
    cur = p5.default_graduate_priority(sprint_plan.current_sprint(player))
    nxt = p5.default_graduate_priority(sprint_plan.next_sprint(player))
    forced = min(len(cur), bw)
    need_next = min(bw - forced, len(nxt))
    splice = p5.splice_available(controller.engine, player)

    def _view(d, sprint):
        v = _die_view(d)
        v["sprint"] = sprint
        return v

    return {
        "sprint_plan": True,
        "n": forced + need_next,
        "current_picks": forced,
        "next_picks": need_next,
        "release_bandwidth": bw,
        "triage_bandwidth": player.triage_bandwidth,
        "candidates": [_view(d, "current") for d in cur] + [_view(d, "next") for d in nxt],
        "default_graduate_ids": [d.die_id for d in cur[:forced]] + [d.die_id for d in nxt[:need_next]],
        "splice_available": splice,
        "processing_box": _processing_view(controller, player),
        "glitched": [_die_view(d) for d in player.glitched_dice],
        "needs_choice": len(cur) > forced or 0 < need_next < len(nxt) or splice,
    }


def _needs_choice(controller: GameController, player: PlayerState) -> Dict[str, Any]:
    if sprint_plan.enabled(controller.state.config):
        return _sprint_choice(controller, player)
    n = p5.max_graduates(player)
    splice = p5.splice_available(controller.engine, player)
    return {
        "n": n,
        "release_bandwidth": player.release_bandwidth,
        "triage_bandwidth": player.triage_bandwidth,
        "candidates": [_die_view(d) for d in p5.default_graduate_priority(player.scanned_dice)],
        "default_graduate_ids": [d.die_id for d in p5.default_graduate_priority(player.scanned_dice)[:n]],
        "splice_available": splice,
        "processing_box": _processing_view(controller, player),
        "glitched": [_die_view(d) for d in player.glitched_dice],
        "needs_choice": len(player.scanned_dice) > player.release_bandwidth or splice,
    }


def _log_shift(controller: GameController, pid: int, rec, is_bot: bool) -> None:
    name = controller.player_meta[pid]["name"] + (" (Bot)" if is_bot else "")
    controller.event_log.append(
        f"{name} CI/CD Pipeline Shift: {len(rec.hotfixed_ids)} Magnetic Splice, {len(rec.returned_to_scanned_ids)} In Production -> Sprint Plan, "
        f"{len(rec.graduated_ids)} Sprint Plan -> Ready, {rec.held_in_scanned} held in the Sprint Plan, {len(rec.triaged_ids)} Research & Development -> Next Sprint (Conveyor Triage)."
    )


def enter_pipeline_shift(controller: GameController) -> None:
    controller.phase = phases.PIPELINE_SHIFT
    controller.phase_name = phases.PHASE_NAMES[controller.phase]
    controller.subphase = "choose_graduates"
    controller.pending_graduation = {}
    controller.last_pipeline_result = {}

    for pid, player in enumerate(controller.state.players):
        meta = controller.player_meta[pid]
        meta["pending_splice_die_id"] = None
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
        _finish_pipeline_shift(controller)


def _finish_pipeline_shift(controller: GameController) -> None:
    """Step 5: Market Leader Bonus, then the end of the round (First Player Marker, next round or Game Over)."""
    controller.pending_graduation = {}
    _fire_market_leader_bonus(controller)
    controller._complete_round()


def _fire_market_leader_bonus(controller: GameController) -> None:
    """Step 5: Market Leader Bonus at the end of Phase 6 if a Red R&D face was banked this round."""
    cfg = controller.state.config
    controller.last_round_bonus = None
    if not secret_faces.enabled(cfg):
        return
    before = len(controller.state.red_secret_payouts)
    if not secret_faces.fire_round_payout(cfg, controller.state):
        return
    rec = controller.state.red_secret_payouts[before]
    def _name(pid: int) -> str:  # pid -1 = the 2P SETEC Corp neutral seat (v0.45.0)
        return controller.player_meta[pid]["name"] if pid in controller.player_meta else "SETEC Corp"

    parts = ", ".join(
        f"{_name(pid)} {rec['places'][pid]}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(rec['places'][pid], 'th')} +{k}"
        for pid, k in sorted(rec["gains"].items(), key=lambda kv: (rec["places"][kv[0]], kv[0]))
    )
    controller.event_log.append(f"MARKET LEADER BONUS (Red R&D face banked this round): {parts}.")
    controller.last_round_bonus = {
        "round": rec["round"], "places": {str(k): v for k, v in rec["places"].items()},
        "gains": {str(k): v for k, v in rec["gains"].items()}, "shares": {str(k): v for k, v in rec["shares"].items()},
    }


def choose_graduates(
    controller: GameController,
    player_id: int,
    graduate_die_ids: Optional[List[int]],
    splice_die_id: Optional[int] = None,
) -> Dict[str, Any]:
    if controller.phase != phases.PIPELINE_SHIFT or controller.subphase != "choose_graduates":
        raise ValueError(f"Cannot make the Sprint Review choice in phase {controller.phase}")
    if player_id not in controller.pending_graduation:
        raise ValueError(f"Player {player_id} has no pending Sprint Review choice")
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
        raise ValueError(f"Die ids {bad} are not in the Sprint Plan")
    if info.get("sprint_plan"):
        cur_set = {d.die_id for d in sprint_plan.current_sprint(player)}
        errs = sprint_plan.check_picks(player, [i for i in ids if i in cur_set], [i for i in ids if i not in cur_set])
        if errs:
            raise ValueError("Illegal Sprint Review: " + "; ".join(errs))
    elif len(ids) > info["n"]:
        raise ValueError(f"Cannot release {len(ids)} dice: Release Bandwidth allows at most {info['n']}")

    splice = splice_die_id if splice_die_id is not None else meta.get("pending_splice_die_id")
    if splice is not None and not any(d.die_id == splice for d in player.glitched_dice):
        raise ValueError(f"Magnetic Splice die {splice} is not in Research & Development")

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
        _finish_pipeline_shift(controller)
    return controller.get_full_state()


def record_magnetic_splice(controller: GameController, player_id: int, die_id: Optional[int] = None,
                           die_index: int = 0) -> Dict[str, Any]:
    """Omnidyne Magnetic Splice (Phase 6 step 1): records the Research & Development die to splice."""
    if controller.phase != phases.PIPELINE_SHIFT or player_id not in controller.pending_graduation:
        raise ValueError(f"Cannot use Omnidyne Magnetic Splice in phase {controller.phase}")
    player = controller.state.players[player_id]
    if not controller.pending_graduation[player_id].get("splice_available"):
        raise ValueError("Omnidyne/Phreaker ability is not available")
    if die_id is None:
        if not (0 <= die_index < len(player.glitched_dice)):
            raise ValueError(f"Invalid die_index {die_index} in Research & Development")
        die_id = player.glitched_dice[die_index].die_id
    if not any(d.die_id == die_id for d in player.glitched_dice):
        raise ValueError(f"Die with die_id {die_id} is not in Research & Development")
    controller.player_meta[player_id]["pending_splice_die_id"] = die_id
    controller.event_log.append(
        f"{controller.player_meta[player_id]['name']} queued Omnidyne Magnetic Splice (Research & Development -> Ready for Release in Phase 6)."
    )
    return controller.get_full_state()
