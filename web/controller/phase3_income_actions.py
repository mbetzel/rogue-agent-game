"""Web Phase 3: Income (v0.34.0 six-phase)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sim.config import ROUND_PHASE_NAMES, DieColor, RoundPhase
from sim.engine.phase3_income import (
    execute_player_income,
    finalize_income,
    preview_player_income,
    purple_star_dice_in_production,
)
from sim.entities import ArchetypeCode, WhiteHatCode, has_signature_protocol

if TYPE_CHECKING:
    from web.controller.core import GameController
    from sim.engine.state import PlayerState


def _is_spook(player: PlayerState) -> bool:
    return has_signature_protocol(player, WhiteHatCode.SPOOK)


def _is_phreaker(player: PlayerState) -> bool:
    return has_signature_protocol(player, WhiteHatCode.PHREAKER)


def _alive_humans(controller: GameController) -> List[int]:
    return [
        pid for pid, m in controller.player_meta.items()
        if m.get("is_human") and not controller.state.players[pid].is_patient_zero
    ]


def _log_income(controller: GameController, pid: int, rec, is_bot: bool) -> None:
    name = controller.player_meta[pid]["name"] + (" (Bot)" if is_bot else "")
    controller.event_log.append(
        f"{name} collected Phase 3 income: +${rec.money}, +{rec.research} 🔬, {rec.secrets:+d} Secrets."
    )
    for burned in rec.burned_die_ids:
        controller.event_log.append(f"{name} executed Spook Burn Notice on die {burned} (+1 Corporate Secret).")
    if rec.diagnostics_face:
        controller.event_log.append(f"{name} executed Phreaker Jumper Diagnostics: {rec.diagnostics_face}.")


def enter_phase_3(controller: GameController) -> None:
    """Bots collect income immediately (simultaneous); humans get a preview and confirm."""
    controller.phase = int(RoundPhase.INCOME)
    controller.phase_name = ROUND_PHASE_NAMES[controller.phase]
    controller.subphase = "confirm_income"
    controller.last_income_result = {}

    for pid, player in enumerate(controller.state.players):
        meta = controller.player_meta[pid]
        meta["income_confirmed"] = False
        meta["pending_spook_burn_ids"] = []
        meta["pending_phreaker_die_id"] = None
        if player.is_patient_zero:
            continue
        if not meta.get("is_human"):
            rec = execute_player_income(controller.engine, player)
            meta["income_confirmed"] = True
            controller.last_income_result[pid] = rec.as_dict()
            _log_income(controller, pid, rec, is_bot=True)
        else:
            preview = preview_player_income(controller.state, player)
            d = preview.as_dict()
            d["preview"] = True
            controller.last_income_result[pid] = d

    if not _alive_humans(controller):
        _finish_phase_3(controller)


def _finish_phase_3(controller: GameController) -> None:
    from web.controller.phase4_attack_actions import enter_phase_4

    # v0.36.0: after every player's Income, resolve Customer Poaching (no carry-over of pending poaches)
    for ev in finalize_income(controller.engine):
        actor = controller.player_meta[ev["actor"]]["name"]
        if ev["target"] is None:
            controller.event_log.append(f"{actor} Customer Poaching: no rival with Market Share to take from.")
        else:
            target = controller.player_meta[ev["target"]]["name"]
            capped = " (own Market Share already at maximum)" if ev["gained"] < ev["moved"] else ""
            controller.event_log.append(
                f"{actor} Customer Poaching: {target} loses {ev['moved']} Market Share, {actor} gains {ev['gained']}{capped}."
            )

    enter_phase_4(controller)


def confirm_income(
    controller: GameController,
    player_id: int,
    spook_burn_die_id: Optional[Any] = None,
    phreaker_die_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Human Phase 3 confirm: collects income, then resolves Burn Notice / Jumper Diagnostics choices."""
    if controller.phase != int(RoundPhase.INCOME) or controller.subphase != "confirm_income":
        raise ValueError(f"Cannot confirm income in phase {controller.phase}")
    if player_id not in controller.player_meta:
        raise ValueError(f"Invalid player_id {player_id}")
    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]
    if player.is_patient_zero:
        raise ValueError(f"Player {player_id} is eliminated")
    if meta.get("income_confirmed"):
        raise ValueError(f"Player {player_id} has already confirmed income this round")

    raw_burn: List[Any]
    if spook_burn_die_id is not None:
        raw_burn = list(spook_burn_die_id) if isinstance(spook_burn_die_id, (list, tuple)) else [spook_burn_die_id]
    else:
        raw_burn = list(meta.get("pending_spook_burn_ids", []))
    burn_ids: List[int] = []
    for b in raw_burn:
        if b is None or (isinstance(b, str) and b.strip() == ""):
            continue  # empty entry = decline that trigger
        if isinstance(b, bool):
            raise ValueError(f"Invalid spook_burn_die_id entry {b!r}: expected a die id")
        try:
            burn_ids.append(int(b))
        except (TypeError, ValueError):
            raise ValueError(f"Invalid spook_burn_die_id entry {b!r}: expected a die id")
    diag_id = phreaker_die_id if phreaker_die_id is not None else meta.get("pending_phreaker_die_id")

    triggers = len(purple_star_dice_in_production(player))
    spook_choice = burn_ids[:triggers] + [None] * max(0, triggers - len(burn_ids))
    phreaker_choice = [diag_id] + [None] * max(0, triggers - 1) if diag_id is not None else [None] * triggers

    rec = execute_player_income(
        controller.engine,
        player,
        spook_burn_die_id=spook_choice,
        phreaker_die_id=phreaker_choice,
    )
    meta["income_confirmed"] = True
    controller.last_income_result[player_id] = rec.as_dict()
    _log_income(controller, player_id, rec, is_bot=False)

    if all(controller.player_meta[pid].get("income_confirmed") for pid in _alive_humans(controller)):
        _finish_phase_3(controller)
    return controller.get_full_state()


def record_spook_burn(controller: GameController, player_id: int, die_id: int) -> Dict[str, Any]:
    """Phase 3 action: records a Burn Notice target (resolved on confirm_income)."""
    if controller.phase != int(RoundPhase.INCOME) or controller.subphase != "confirm_income":
        raise ValueError(f"Burn Notice resolves in Phase 3: Income (current phase {controller.phase})")
    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]
    if player.is_patient_zero:
        raise ValueError("Eliminated players cannot perform operations")
    if not _is_spook(player):
        raise ValueError("Player does not have the Spook white hat dossier or archetype")
    triggers = len(purple_star_dice_in_production(player))
    if triggers <= 0:
        raise ValueError("Burn Notice requires a Purple ★ die still In Production")
    pending = meta.setdefault("pending_spook_burn_ids", [])
    if die_id in pending:
        raise ValueError(f"Die {die_id} is already targeted by Burn Notice this round")
    if len(pending) >= triggers:
        raise ValueError("No Burn Notice triggers remaining this round")
    owned = [d for d in player.total_dice if d.die_id == die_id and d.color not in (DieColor.GRAY, DieColor.WHITE)]
    if not owned:
        raise ValueError(f"Colored die {die_id} not found among owned dice to burn")
    pending.append(die_id)
    controller.event_log.append(f"{meta['name']} queued Spook Burn Notice on die {die_id} (resolves on Phase 3 confirm).")
    return controller.get_full_state()


def record_phreaker_diagnostics(controller: GameController, player_id: int, die_id: Optional[int] = None) -> Dict[str, Any]:
    """Phase 3 action: records a Jumper Diagnostics target (resolved on confirm_income)."""
    if controller.phase != int(RoundPhase.INCOME) or controller.subphase != "confirm_income":
        raise ValueError(f"Jumper Diagnostics resolves in Phase 3: Income (current phase {controller.phase})")
    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]
    if player.is_patient_zero:
        raise ValueError("Eliminated players cannot perform operations")
    if not _is_phreaker(player):
        raise ValueError("Player does not have the Phreaker white hat dossier or archetype")
    if die_id is not None and not any(d.die_id == die_id for d in player.under_development_dice):
        raise ValueError(f"Die {die_id} is not Under Development")
    meta["pending_phreaker_die_id"] = die_id
    controller.event_log.append(f"{meta['name']} selected a Jumper Diagnostics target (resolves on Phase 3 confirm).")
    return controller.get_full_state()


def capital_injection(controller: GameController, player_id: int) -> Dict[str, Any]:
    """Activates Meridian Financial Trust's Capital Injection once per Rogue Agent version during Phase 3."""
    from web.controller.capabilities import has_company_override, legacy_bridge_enabled
    from sim.entities import CompanyCode

    if controller.phase != int(RoundPhase.INCOME):
        raise ValueError(f"Capital Injection resolves in Phase 3: Income (current phase {controller.phase})")
    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]
    if player.is_patient_zero:
        raise ValueError("Eliminated players cannot perform operations")
    is_meridian = has_company_override(player, CompanyCode.MERIDIAN, legacy_bridge_enabled(controller))
    if not is_meridian:
        raise ValueError("Player does not have Meridian Financial Trust Capital Injection override")
    meridian_mode = getattr(controller.state.config, "meridian_override_mode", "REDUNDANT_CREW")
    if meridian_mode != "CAPITAL_INJECTION":
        raise ValueError("Capital Injection is not active under current ruleset")

    active_ver = controller.state.active_version.version_str if controller.state.active_version else None
    if not player.is_ability_available(active_ver):
        raise ValueError("Capital Injection override has already been used for this SETEC version")

    cash_gain = getattr(controller.state.config, "meridian_capital_injection_cash", 3)
    player.money += cash_gain
    player.mark_ability_used(active_ver)
    controller.event_log.append(f"{meta['name']} activated Meridian Financial Trust Capital Injection (+${cash_gain} cash).")
    return controller.get_full_state()

