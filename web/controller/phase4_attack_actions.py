"""Web Phase 4: Attack Resolution (v0.46.0, RULES.md Section 4 Phase 4). No cube can be blocked.

Order (same as ``sim.engine.phase4_attack_resolution.execute_attack_resolution``):
1. Red & Blue for every survivor (bots in ``enter_phase_4``, humans in ``confirm_attacks``),
2. Green, table-wide, one cube at a time against the highest Vulnerability at the minimum target or more,
3. the Patient Zero check, 4. Target Lock Signature Attacks, then ``finalize_attack_resolution``
(SETEC Corp, Snowball Recycle, Contractor Expiration, End Game Trigger Check).

Humans declare their Phase 4 choices up front in ``confirm_attacks``: the Aegis *Baffle Echo* (ignore 1 Red or Blue
cube, or save it for a Green hit), the DTO *Slush Fund*, and their Target Lock choices (Green: which 2 Research
Tracks; Red: which tied rival gains Market Share).
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional

from sim.config import ROUND_PHASE_NAMES, CubeColor, RoundPhase
from sim.engine import phase4_attack_resolution as p4
from sim.engine import research_tracks, vulnerability
from sim.entities import CompanyCode, has_company_override, legacy_bridge_enabled
from web.schemas import GameStateSerializer

if TYPE_CHECKING:
    from web.controller.core import GameController

_SIG_TRACKS = ("DEFENSE", "TRIAGE", "RELEASE", "PR")
_SIG_EFFECTS = {
    "green": "Malware Encryption: a green cube on the next space of 2 Research Tracks (2x 🔬 to advance)",
    "black": "Root Override Hijack: Institutional Override marked Used (or lose 2 Corporate Secrets)",
    "blue": "Buffer Congestion: 1 Gray Legacy die to the back of the Processing Box",
    "red": "Market Manipulation: lose 2 Market Share; the non-locked rival with the least Market Share gains 2",
}


# ---------------------------------------------------------------------------
# Previews (pure: no engine state is mutated)
# ---------------------------------------------------------------------------
def green_preview(controller: GameController) -> List[Dict[str, Any]]:
    """Who each exited Green cube will hit, from the current Vulnerability values (``vulnerability.resolve_green``
    without side effects). A Baffle Echo cancels only the Secret loss, so it never changes who is hit."""
    cfg, s = controller.state.config, controller.state
    cr = controller.compile_result
    if cr is None or cr.buffer_overflow:
        return []
    n = int((controller.attack_strengths or {}).get(CubeColor.GREEN, 0))
    floor = vulnerability.min_target(cfg, s)
    seat = {p.player_id: (i - s.first_player_index) % len(s.players) for i, p in enumerate(s.players)}
    v = {p.player_id: p.vulnerability for p in s.players if vulnerability.eligible_for_green(s, cr, p)}
    out = []
    for k in range(n):
        elig = [pid for pid, val in v.items() if val >= floor]
        if not elig:
            out.append({"cube": k, "pids": [], "v": None, "damage": 0, "cancelled": []})
            continue
        top = max(v[pid] for pid in elig)
        hit = sorted((pid for pid in elig if v[pid] == top), key=lambda pid: seat[pid])
        for pid in hit:
            v[pid] = cfg.vuln_hit_reset
        out.append({"cube": k, "pids": hit, "v": top, "damage": vulnerability.band_damage(cfg, top), "cancelled": []})
    return out


def _signature_view(controller: GameController) -> Dict[str, Any]:
    s, cfg, cr = controller.state, controller.state.config, controller.compile_result
    on = getattr(cfg, "signature_attack_mode", "none") == "dominant_color_effects"
    if not on or cr is None:
        return {"enabled": on, "dominant_color": None, "locked_pids": [], "effect": None, "fizzled": False}
    dom = None if cr.buffer_overflow else p4.determine_dominant_tray_color(cr.exited_cubes, cfg.signature_attack_tie_order)
    locked = [p.player_id for p in s.players
              if p.target_locked and not p.is_patient_zero and p.player_id not in cr.breached_pids]
    key = dom.value if dom is not None else None
    return {"enabled": True, "dominant_color": key, "locked_pids": locked if dom is not None else [],
            "effect": _SIG_EFFECTS.get(key), "fizzled": dom is None and bool(locked)}


def _signature_choices(controller: GameController, pid: int, sig: Dict[str, Any]) -> Dict[str, Any]:
    """The Target Lock choices this player can make (only when locked and a real choice exists)."""
    s = controller.state
    player = s.players[pid]
    out: Dict[str, Any] = {"green_tracks": None, "red_recipients": None}
    if pid not in sig["locked_pids"]:
        return out
    if sig["dominant_color"] == "green":
        eligible = [t for t in _SIG_TRACKS
                    if research_tracks.level_of(player, t) < 4 and not research_tracks.is_track_encrypted(player, t)]
        n = int(s.config.signature_green_cube_count)
        if len(eligible) > n:
            out["green_tracks"] = {
                "count": n,
                "options": [{"track": t, "name": research_tracks.track_display_name(s.config, t)} for t in eligible],
            }
    elif sig["dominant_color"] == "red":
        locked = set(sig["locked_pids"])
        elig = [p for p in s.players if not p.is_patient_zero and p.player_id not in locked and p.market_share is not None]
        if elig:
            low = min(p.market_share for p in elig)
            tied = [p.player_id for p in elig if p.market_share == low]
            if len(tied) > 1:
                out["red_recipients"] = tied
    return out


def _threat_summary(controller: GameController, pid: int, resolved: bool,
                    sig: Dict[str, Any], greens: List[Dict[str, Any]]) -> Dict[str, Any]:
    player = controller.state.players[pid]
    cfg = controller.state.config
    cr = controller.compile_result
    attack = controller.attack_strengths or {}
    exited = {c.value: n for c, n in cr.exited_cubes.items()} if cr else {}
    atk = {c.value: int(attack.get(c, 0)) for c in (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN)}
    bd = getattr(player, "last_defense_breakdown", None) if resolved else None
    active_ver = controller.state.active_version.version_str
    blue_mult = int(cfg.v3_blue_secret_damage) if active_ver == "v3.0" else 1

    red = {"cubes": exited.get("red", 0), "attack": atk["red"], "market_share": player.market_share,
           "market_share_max": player.market_share_max,
           "market_share_lost": bd.get("market_share_lost", 0) if bd else min(player.market_share or 0, atk["red"])}
    blue = {"cubes": exited.get("blue", 0), "attack": atk["blue"], "damage_multiplier": blue_mult,
            "secrets_lost": bd.get("blue_secret_loss", 0) if bd else atk["blue"] * blue_mult}
    hits = [g for g in greens if pid in g["pids"]]
    green = {"cubes": exited.get("green", 0), "attack": atk["green"],
             "hits": [{"cube": g["cube"], "v": g["v"], "damage": g["damage"],
                       "cancelled": pid in g.get("cancelled", [])} for g in hits],
             "secrets_at_risk": sum(g["damage"] for g in hits if pid not in g.get("cancelled", []))}

    qualifying: List[str] = []
    green_echo = False
    if not resolved and cr is not None and not cr.buffer_overflow and p4.is_aegis_echo_available(controller.engine, player):
        qualifying = [c.value for c in (CubeColor.RED, CubeColor.BLUE)
                      if attack.get(c, 0) > 0 and cr.exited_cubes.get(c, 0) > 0]
        green_echo = bool(hits)
    is_dto = has_company_override(player, CompanyCode.DTO, legacy_bridge_enabled(controller))
    return {
        "resolved": resolved,
        "aegis": {"available": bool(qualifying or green_echo), "qualifying_colors": qualifying, "green_hit": green_echo},
        "slush_fund": {"available": bool(not resolved and is_dto and atk["blue"] > 0
                                         and player.is_slush_fund_available(active_ver))},
        "aegis_color": bd.get("aegis_color") if bd else None,
        "money": player.money,
        "secrets": player.secrets,
        "market_share": player.market_share,
        "vulnerability": player.vulnerability,
        "target_locked": pid in sig["locked_pids"],
        "signature_choices": _signature_choices(controller, pid, sig) if not resolved else {},
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


def _refresh_attack_result(controller: GameController, final: bool = False,
                           sig: Optional[Dict[str, Any]] = None) -> None:
    s = controller.state
    attack = controller.attack_strengths or {}
    sig = sig or _signature_view(controller)
    if final:
        stats = s.green_round_stats if (s.green_round_stats or {}).get("round") == s.current_round else {}
        greens = [{"cube": e["cube"], "pids": list(e["pids"]), "v": e["v"], "damage": e["damage"],
                   "cancelled": list(e.get("cancelled", []))} for e in stats.get("events", [])]
    else:
        greens = green_preview(controller)
    summaries = {}
    for pid, player in enumerate(s.players):
        if player.is_patient_zero and pid not in controller.attack_resolved_pids:
            continue
        summaries[pid] = _threat_summary(controller, pid, final or pid in controller.attack_resolved_pids, sig, greens)
    controller.last_attack_result = {
        "attack_strengths": {c.value: n for c, n in attack.items()},
        "buffer_overflow": bool(controller.compile_result and controller.compile_result.buffer_overflow),
        "resolved": final,
        "threat_summary": summaries,
        "human_threat": summaries.get(_primary_human(controller), {}),
        "green_hits": greens,
        "vulnerability_track": GameStateSerializer._vulnerability_track(s),
        "signature": sig,
    }


# ---------------------------------------------------------------------------
# Flow
# ---------------------------------------------------------------------------
def enter_phase_4(controller: GameController) -> None:
    controller.phase = int(RoundPhase.ATTACK_RESOLUTION)
    controller.phase_name = ROUND_PHASE_NAMES[controller.phase]
    controller.subphase = "confirm_attacks"
    cr = controller.compile_result
    controller.attack_strengths = p4.compute_attack_strengths(controller.engine, cr)
    controller.attack_resolved_pids = set()
    controller.engine.aegis_green_override = {}

    for meta in controller.player_meta.values():
        meta["attacks_confirmed"] = False
        meta["aegis_green"] = None
        meta["signature_green_tracks"] = None
        meta["signature_red_recipient"] = None

    if not cr.buffer_overflow:
        for player, rolled, commits in controller.round_commitments or []:
            if player.is_patient_zero or player.player_id in cr.breached_pids:
                continue
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


@contextmanager
def _human_signature_hooks(controller: GameController) -> Iterator[None]:
    """Routes the engine's Target Lock choice hooks to each human's declared choice (instance attributes shadow the
    bot class hooks for the duration of ``resolve_signature_attacks`` only)."""
    patched = []
    for pid, meta in controller.player_meta.items():
        if not meta.get("is_human"):
            continue
        bot = controller.state.players[pid].bot
        tracks = meta.get("signature_green_tracks")
        if tracks:
            bot.choose_signature_green_tracks = lambda player, eligible, n, state, _t=list(tracks): list(_t)
            patched.append((bot, "choose_signature_green_tracks"))
        rec = meta.get("signature_red_recipient")
        if rec is not None:
            def _pick(player, tied, state, _r=int(rec)):
                return next((p for p in tied if p.player_id == _r), tied[0])
            bot.choose_signature_red_recipient = _pick
            patched.append((bot, "choose_signature_red_recipient"))
    try:
        yield
    finally:
        for bot, name in patched:
            bot.__dict__.pop(name, None)


def _log_green_and_signature(controller: GameController, sig: Dict[str, Any]) -> None:
    s = controller.state
    names = {pid: m["name"] for pid, m in controller.player_meta.items()}
    stats = s.green_round_stats if (s.green_round_stats or {}).get("round") == s.current_round else {}
    for e in stats.get("events", []):
        if not e["pids"]:
            controller.event_log.append(f"Green cube {e['cube'] + 1}: no player at Vulnerability "
                                        f"{vulnerability.min_target(s.config, s)}+ (no effect).")
            continue
        who = ", ".join(names[p] + (" (Baffle Echo: no Secret loss)" if p in e["cancelled"] else "") for p in e["pids"])
        controller.event_log.append(
            f"Green cube {e['cube'] + 1} hits {who} at Vulnerability {e['v']}: -{e['damage']} Corporate "
            f"Secret{'s' if e['damage'] != 1 else ''}, Vulnerability reset to {s.config.vuln_hit_reset}.")
    if sig.get("dominant_color") and sig.get("locked_pids"):
        who = ", ".join(names[p] for p in sig["locked_pids"])
        controller.event_log.append(
            f"Target Lock ({sig['dominant_color'].capitalize()} dominant): {who} - {sig['effect']}.")
    elif sig.get("fizzled"):
        controller.event_log.append("Target Lock fizzles: no cubes in the Exit Tray.")


def _finish_phase_4(controller: GameController) -> None:
    engine, cr = controller.engine, controller.compile_result
    sig = _signature_view(controller)  # read before finalize clears Target Lock
    if not cr.buffer_overflow:
        vulnerability.resolve_green(engine, cr, controller.attack_strengths)  # Step 2: table-wide Green
        vulnerability.flag_patient_zero(engine)                             # Step 3: the single breach check
        if sig["enabled"]:
            with _human_signature_hooks(controller):
                p4.resolve_signature_attacks(engine, cr)                      # Step 4: Target Lock
    elif sig["enabled"]:
        controller.state.last_dominant_color = None
    for pid in sorted(controller.attack_resolved_pids):
        bd = getattr(controller.state.players[pid], "last_defense_breakdown", None)
        if bd:
            u = bd["unblocked"]
            ms = (f" Market Share {bd['market_share_before']} -> {bd['market_share_after']}."
                  if bd.get("market_share_after") is not None else "")
            echo = f" Baffle Echo ignored 1 {bd['aegis_color'].capitalize()} cube." if bd.get("aegis_color") else ""
            controller.event_log.append(
                f"{controller.player_meta[pid]['name']} Attack Resolution: {u['red']} Red, {u['blue']} Blue "
                f"(-{bd.get('blue_secret_loss', 0)} Corporate Secrets).{ms}{echo}"
            )
    _log_green_and_signature(controller, sig)
    p4.finalize_attack_resolution(engine, cr)  # Green is idempotent here (INV-VULN-07)
    s = controller.state
    if s.market_collapse_triggered and s.market_collapse_round == s.current_round:
        names = ", ".join(controller.player_meta[pid]["name"] for pid in s.market_collapse_pids)
        controller.event_log.append(f"MARKET COLLAPSE: {names} reached 0 Market Share. This is the Final Round.")
    _refresh_attack_result(controller, final=True, sig=sig)
    if controller.last_compile_result is not None:
        controller.last_compile_result["is_final_round"] = controller.state.is_final_round
        controller.last_compile_result["game_over"] = controller.state.game_over

    from web.controller.phase2_actions import enter_game_over

    if controller.state.game_over:
        enter_game_over(controller)
        return
    if controller.state.is_final_round:
        controller.event_log.append("FINAL ROUND: surviving corporations complete Operations and the CI/CD Pipeline Shift.")
    from web.controller.phase5_operations_actions import enter_operations

    enter_operations(controller)


def confirm_attacks(
    controller: GameController,
    player_id: int,
    aegis_color: Optional[str] = None,
    use_slush_fund: Optional[bool] = None,
    aegis_green: Optional[str] = None,
    signature_green_tracks: Optional[List[str]] = None,
    signature_red_recipient: Optional[int] = None,
) -> Dict[str, Any]:
    """A human's Phase 4 choices; resolves their Red & Blue now and the table-wide steps once every human confirmed.

    ``aegis_color``: ``"red"`` / ``"blue"`` (ignore 1 cube), ``"green"`` (save the Baffle Echo for a Green hit) or
    ``"none"`` / ``"decline"``. ``aegis_green``: ``"use"`` / ``"decline"`` the Echo on a Green hit (``None`` with
    ``aegis_color="green"`` means ``"use"``). ``signature_green_tracks`` / ``signature_red_recipient``: Target Lock
    choices (validated against ``threat_summary[pid]["signature_choices"]``)."""
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
    entry = next((e for e in controller.round_commitments or [] if e[0].player_id == player_id), None)
    if entry is None:
        raise ValueError(f"Player {player_id} has no Phase 1 lock-in this round")
    _, rolled, commits = entry
    cr = controller.compile_result

    aegis_override: Any = None
    if aegis_color:
        key = str(aegis_color).lower()
        if key in ("none", "decline"):
            aegis_override = p4.AEGIS_DECLINE
        elif key == "green":
            aegis_override = "green"
        else:
            try:
                aegis_override = CubeColor(key)
            except ValueError:
                raise ValueError(f"Invalid aegis_color {aegis_color!r}")
            qualifying = [c for c in (CubeColor.RED, CubeColor.BLUE)
                          if controller.attack_strengths.get(c, 0) > 0 and cr.exited_cubes.get(c, 0) > 0]
            if aegis_override not in qualifying or not p4.is_aegis_echo_available(controller.engine, player):
                raise ValueError(
                    f"aegis_color {key!r} is not a qualifying Baffle Echo color this round "
                    f"(qualifying: {[c.value for c in qualifying]})"
                )
    key_g = None if aegis_green is None else str(aegis_green).lower()
    if key_g not in (None, "use", "decline"):
        raise ValueError(f"Invalid aegis_green {aegis_green!r}")
    if key_g is None and aegis_override == "green":
        key_g = "use"
    if key_g is None and (isinstance(aegis_override, CubeColor) or aegis_override == p4.AEGIS_DECLINE):
        key_g = "decline"  # the Echo was spent (or refused) on the Red / Blue step

    sig = _signature_view(controller)
    choices = _signature_choices(controller, player_id, sig)
    if signature_green_tracks is not None:
        opt = choices.get("green_tracks")
        if not opt:
            raise ValueError("No Target Lock Green track choice is open to this player")
        tracks = [str(t).upper() for t in signature_green_tracks]
        legal = {o["track"] for o in opt["options"]}
        if len(tracks) != opt["count"] or len(set(tracks)) != opt["count"] or not set(tracks) <= legal:
            raise ValueError(f"Choose {opt['count']} different tracks from {sorted(legal)}")
        meta["signature_green_tracks"] = tracks
    if signature_red_recipient is not None:
        tied = choices.get("red_recipients")
        if not tied or int(signature_red_recipient) not in tied:
            raise ValueError(f"signature_red_recipient must be one of {tied}")
        meta["signature_red_recipient"] = int(signature_red_recipient)

    meta["aegis_green"] = key_g
    controller.engine.aegis_green_override = {
        pid: (m["aegis_green"] == "use") for pid, m in controller.player_meta.items()
        if m.get("aegis_green") is not None
    }
    p4.resolve_player_attack(
        controller.engine, player, rolled, commits, controller.attack_strengths, cr,
        aegis_color_override=aegis_override,
        # Slush Fund is optional and once per game: a human uses it only by explicit choice (OQ-5)
        slush_fund_override=(bool(use_slush_fund) if controller.state.config.slush_fund_once_per_game else None),
    )
    controller.attack_resolved_pids.add(player_id)
    meta["attacks_confirmed"] = True
    controller.event_log.append(f"{meta['name']} confirmed Phase 4 choices.")

    if all(pid in controller.attack_resolved_pids for pid in _alive_humans_in_phase4(controller)):
        _finish_phase_4(controller)
    else:
        _refresh_attack_result(controller)
    return controller.get_full_state()
