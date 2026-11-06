"""Web Phase 4: Attack Resolution (v0.34.0 six-phase).

Humans choose Generic ``Any`` shield allocation, Green Malware targets and the Aegis *Baffle Echo*
color BEFORE damage resolves (no snapshot / rollback, INV-SEQ-NO-SNAPSHOT-01).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sim.config import ROUND_PHASE_NAMES, CubeColor, DieColor, RoundPhase, ShieldColor
from sim.engine import phase4_attack_resolution as p4
from sim.engine.state import ProductionRole
from sim.entities import ArchetypeCode, CompanyCode, has_company_override, legacy_bridge_enabled

if TYPE_CHECKING:
    from web.controller.core import GameController
    from sim.engine.state import PlayerState

_SHIELD_ROLES = (
    ProductionRole.RED_SHIELD,
    ProductionRole.BLUE_SHIELD,
    ProductionRole.GREEN_SHIELD,
    ProductionRole.ANY_SHIELD,
)


def _commitment_for(controller: GameController, pid: int):
    for entry in controller.round_commitments or []:
        if entry[0].player_id == pid:
            return entry
    return None


def _candidate_dice(player: PlayerState, income_rows: Dict[int, Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for d in player.in_production_dice:
        eff = d.effective_face or d.current_face
        role = getattr(d, "production_role", None)
        is_shield = role in _SHIELD_ROLES
        row = income_rows.get(d.die_id, {})
        out.append({
            "die_id": d.die_id,
            "color": d.color.value,
            "face_name": eff.name if eff else "Module",
            "role": "Contractor" if d.color == DieColor.WHITE else (
                role.value.replace("_", " ").title() if is_shield else "Income"),
            "money": row.get("money", 0),
            "patches": row.get("patches", 0),
            "secrets": row.get("secrets", 0),
            "star_note": row.get("star_note"),
            "is_contractor": d.color == DieColor.WHITE,
            "is_shield": is_shield,
            "is_income": not is_shield,
            "is_fallback": False,
        })
    return out


def _threat_summary(controller: GameController, pid: int, attack: Dict[CubeColor, int],
                    resolved: bool) -> Dict[str, Any]:
    player = controller.state.players[pid]
    cr = controller.compile_result
    exited = {c.value: n for c, n in cr.exited_cubes.items()} if cr else {}
    entry = _commitment_for(controller, pid)
    rolled, commits = (entry[1], entry[2]) if entry else ([], {})
    shields = {"red": 0, "blue": 0, "green": 0, "any": 0}
    any_dice = []
    for idx, color in commits.items():
        if idx >= len(rolled):
            continue
        d = rolled[idx]
        eff = d.effective_face or d.current_face
        if eff and eff.is_shield:
            shields[color.value] += eff.block_amount
            if color == ShieldColor.ANY:
                any_dice.append({"die_id": d.die_id, "color": d.color.value, "face_name": eff.name,
                                 "block_amount": eff.block_amount})
    atk = {c.value: attack.get(c, 0) for c in (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN)}
    bd = getattr(player, "last_defense_breakdown", None) if resolved else None
    income_rows = {r["die_id"]: r for r in (controller.last_income_result.get(pid, {}) or {}).get("details", [])}

    def _col(c: str) -> Dict[str, Any]:
        if bd:
            blocked, unblocked = bd["blocked"][c], bd["unblocked"][c]
        else:
            blocked = min(shields[c], atk[c])
            unblocked = max(0, atk[c] - shields[c])
        return {"cubes": exited.get(c, 0), "attack": atk[c], "shields": shields[c],
                "blocked": blocked, "unblocked": unblocked}

    red, blue, green = _col("red"), _col("blue"), _col("green")
    red.update(unpaid_ransom=bd.get("unpaid_ransom", 0) if bd else 0,
               flat_leak=bd.get("flat_ransom_leak", False) if bd else False)
    green.update(fizzled=bd.get("malware_fizzled", False) if bd else (green["unblocked"] > 0 and not player.in_production_dice),
                 pending_glitches=0 if resolved else green["unblocked"],
                 candidate_dice=[] if resolved else _candidate_dice(player, income_rows))
    qualifying = [] if resolved or not cr else [
        c.value for c in p4.aegis_qualifying_colors(controller.engine, player, attack, cr.exited_cubes)
    ]
    return {
        "resolved": resolved,
        "aegis": {"available": bool(qualifying), "qualifying_colors": qualifying},
        "slush_fund": {"available": bool(
            has_company_override(player, CompanyCode.DTO, legacy_bridge_enabled(controller))
            and player.is_slush_fund_available(controller.state.active_version.version_str)
        )},
        "any": {
            "shields": shields["any"],
            "allocated": bd.get("any_allocated", {"red": 0, "blue": 0, "green": 0}) if bd else {"red": 0, "blue": 0, "green": 0},
            "dice": any_dice,
        },
        "effective_attacks": bd.get("effective_attacks", atk) if bd else atk,
        "firewall_blocked": bd.get("firewall_blocked") if bd else None,
        "money": player.money,
        "secrets": player.secrets,
        "r2_count": sum(1 for d in rolled if (d.effective_face or d.current_face) and (d.effective_face or d.current_face).star_code == "R2"),
        "r3_count": sum(1 for d in rolled if (d.effective_face or d.current_face) and (d.effective_face or d.current_face).star_code == "R3"),
        "b1_count": sum(1 for d in rolled if (d.effective_face or d.current_face) and (d.effective_face or d.current_face).star_code == "B1"),
        "red": red,
        "blue": blue,
        "green": green,
        "black": {"cubes": exited.get("black", 0), "corruption_track": controller.state.corruption_track},
    }


def _alive_humans_in_phase4(controller: GameController) -> List[int]:
    cr = controller.compile_result
    breached = cr.breached_pids if cr else set()
    return [
        pid for pid, m in controller.player_meta.items()
        if m.get("is_human") and not controller.state.players[pid].is_patient_zero and pid not in breached
    ]


def _primary_human(controller: GameController) -> int:
    for pid, m in controller.player_meta.items():
        if m.get("is_human"):
            return pid
    return 0


def _refresh_attack_result(controller: GameController) -> None:
    attack = controller.attack_strengths or {}
    summaries = {}
    for pid, player in enumerate(controller.state.players):
        if player.is_patient_zero and pid not in controller.attack_resolved_pids:
            continue
        summaries[pid] = _threat_summary(controller, pid, attack, resolved=pid in controller.attack_resolved_pids)
    hp = _primary_human(controller)
    human_ts = summaries.get(hp, {})
    controller.last_attack_result = {
        "attack_strengths": {c.value: n for c, n in attack.items()},
        "buffer_overflow": bool(controller.compile_result and controller.compile_result.buffer_overflow),
        "threat_summary": summaries,
        "human_threat": human_ts,
        "candidate_glitch_dice": human_ts.get("green", {}).get("candidate_dice", []) if human_ts else [],
        "pending_glitches": human_ts.get("green", {}).get("pending_glitches", 0) if human_ts else 0,
    }


def enter_phase_4(controller: GameController) -> None:
    controller.phase = int(RoundPhase.ATTACK_RESOLUTION)
    controller.phase_name = ROUND_PHASE_NAMES[controller.phase]
    controller.subphase = "confirm_attacks"
    cr = controller.compile_result
    controller.attack_strengths = p4.compute_attack_strengths(controller.engine, cr)
    controller.attack_resolved_pids = set()

    for pid, meta in controller.player_meta.items():
        meta["attacks_confirmed"] = False

    if not cr.buffer_overflow:
        for player, rolled, commits in controller.round_commitments or []:
            if player.is_patient_zero or player.player_id in cr.breached_pids:
                continue
            p4.sync_commitments_with_production(player, rolled, commits)
            meta = controller.player_meta[player.player_id]
            if not meta.get("is_human"):
                p4.resolve_player_attack(controller.engine, player, rolled, commits, controller.attack_strengths, cr)
                controller.attack_resolved_pids.add(player.player_id)
                meta["attacks_confirmed"] = True
    else:
        controller.event_log.append("Phase 4: Compile Buffer Overflow - no attacks resolve this round.")

    _refresh_attack_result(controller)
    if cr.buffer_overflow or not _alive_humans_in_phase4(controller):
        _finish_phase_4(controller)


def _finish_phase_4(controller: GameController) -> None:
    cr = controller.compile_result
    p4.finalize_attack_resolution(controller.engine, cr)
    for pid in controller.attack_resolved_pids:
        bd = getattr(controller.state.players[pid], "last_defense_breakdown", None)
        if bd:
            u = bd["unblocked"]
            controller.event_log.append(
                f"{controller.player_meta[pid]['name']} Attack Resolution: unblocked {u['red']} Red, {u['blue']} Blue, {u['green']} Green."
            )
    _refresh_attack_result(controller)
    if controller.last_compile_result is not None:
        controller.last_compile_result["is_final_round"] = controller.state.is_final_round
        controller.last_compile_result["game_over"] = controller.state.game_over

    from web.controller.phase2_actions import enter_game_over

    if controller.state.game_over:
        enter_game_over(controller)
        return
    if controller.state.is_final_round:
        controller.event_log.append("FINAL ROUND: surviving corporations complete the CI/CD Pipeline Shift and Operations.")
    from web.controller.phase5_pipeline_actions import enter_phase_5

    enter_phase_5(controller)


def confirm_attacks(
    controller: GameController,
    player_id: int,
    any_shield_allocations: Optional[Dict[str, int]] = None,
    glitch_die_ids: Optional[List[int]] = None,
    aegis_color: Optional[str] = None,
    use_slush_fund: Optional[bool] = None,
) -> Dict[str, Any]:
    if controller.phase != int(RoundPhase.ATTACK_RESOLUTION) or controller.subphase != "confirm_attacks":
        raise ValueError(f"Cannot confirm attacks in phase {controller.phase}")
    if player_id not in controller.player_meta:
        raise ValueError(f"Invalid player_id {player_id}")
    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]
    if player.is_patient_zero:
        raise ValueError(f"Player {player_id} is eliminated")
    if player_id in controller.attack_resolved_pids:
        raise ValueError(f"Player {player_id} has already confirmed attacks this round")

    entry = _commitment_for(controller, player_id)
    if entry is None:
        raise ValueError(f"Player {player_id} has no Phase 1 commitments this round")
    _, rolled, commits = entry

    allocs = None
    if any_shield_allocations is not None:
        allocs = {
            CubeColor.RED: int(any_shield_allocations.get("red", 0)),
            CubeColor.BLUE: int(any_shield_allocations.get("blue", 0)),
            CubeColor.GREEN: int(any_shield_allocations.get("green", 0)),
        }
    selector = None
    if glitch_die_ids is not None:
        wanted = [int(x) for x in glitch_die_ids]

        def selector(p, prod, count, _wanted=wanted):
            by_id = {d.die_id: d for d in prod}
            return [by_id[i] for i in _wanted if i in by_id][:count]

    aegis_override = None
    if aegis_color:
        key = str(aegis_color).lower()
        if key in ("none", "decline"):
            aegis_override = p4.AEGIS_DECLINE
        else:
            try:
                aegis_override = CubeColor(key)
            except ValueError:
                raise ValueError(f"Invalid aegis_color {aegis_color!r}")
            cr = controller.compile_result
            qualifying = p4.aegis_qualifying_colors(
                controller.engine, player, controller.attack_strengths, cr.exited_cubes if cr else {}
            )
            if aegis_override not in qualifying:
                raise ValueError(
                    f"aegis_color {key!r} is not a qualifying Baffle Echo color this round "
                    f"(qualifying: {[c.value for c in qualifying]})"
                )

    p4.resolve_player_attack(
        controller.engine, player, rolled, commits, controller.attack_strengths, controller.compile_result,
        any_shield_allocations=allocs, malware_target_selector=selector, aegis_color_override=aegis_override,
        # v0.35 Slush Fund is optional and once per game: a human uses it only by explicit choice (OQ-5)
        slush_fund_override=(bool(use_slush_fund) if controller.state.config.slush_fund_once_per_game else None),
    )
    controller.attack_resolved_pids.add(player_id)
    meta["attacks_confirmed"] = True
    controller.event_log.append(f"{meta['name']} confirmed Phase 4 defensive allocations.")

    if all(pid in controller.attack_resolved_pids for pid in _alive_humans_in_phase4(controller)):
        _finish_phase_4(controller)
    else:
        _refresh_attack_result(controller)
    return controller.get_full_state()
