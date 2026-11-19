from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from sim.config import CubeColor, DieColor
from sim.engine import research_tracks, vulnerability
from sim.entities import CompanyCode, WhiteHatCode, has_company_override, has_signature_protocol, legacy_bridge_enabled
from web.controller import phases
from web.controller.phase1_actions import release_l4_gray_faces

if TYPE_CHECKING:
    from web.controller.core import GameController


def get_action_capabilities(controller: GameController, player_id: int) -> Dict[str, Any]:
    """Calculates valid action flags for the specified player given current state."""
    if player_id not in controller.player_meta or controller.engine is None:
        return {}

    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]
    is_active = (player_id == controller.active_player_index)
    is_eliminated = player.is_patient_zero

    OPS, PIPE = phases.OPERATIONS, phases.PIPELINE_SHIFT
    can_roll = (controller.phase == 1 and not meta["has_rolled"] and not is_eliminated)
    white_enabled = bool(getattr(controller.state.config, "white_contractor_dice_enabled", True))
    max_contractors = controller.state.config.contractor_max_hire
    active_ver = controller.state.active_version.version_str if (controller.state and controller.state.active_version) else None
    ability_avail = player.is_ability_available(active_ver) if active_ver else player.is_ability_available()

    if not white_enabled or max_contractors <= 0:
        already_hired = meta.get("hired_contractors", 0)
        next_contractor_cost = None
        can_hire_contractors = False
        can_operator = False
    else:
        already_hired = meta.get("hired_contractors", 0)
        if already_hired < max_contractors:
            next_contractor_cost = controller.state.config.get_contractor_cost_for_hire(1, already_hired=already_hired)
        else:
            next_contractor_cost = None

        can_hire_contractors = (
            controller.phase == 1
            and not meta["has_rolled"]
            and not is_eliminated
            and already_hired < max_contractors
            and controller.state.contractor_supply > 0
            and next_contractor_cost is not None
            and player.money >= next_contractor_cost
        )

        # Company Institutional Overrides & Operative Protocol Capabilities
        is_operator = has_company_override(player, CompanyCode.MERIDIAN, legacy_bridge_enabled(controller))
        can_operator = bool(
            controller.phase == 1
            and not meta["has_rolled"]
            and not is_eliminated
            and is_operator
            and ability_avail
            and already_hired < max_contractors
            and controller.state.contractor_supply > 0
        )

    # Phase 3 Meridian Capital Injection
    is_meridian = has_company_override(player, CompanyCode.MERIDIAN, legacy_bridge_enabled(controller))
    meridian_mode = getattr(controller.state.config, "meridian_override_mode", "REDUNDANT_CREW")
    can_capital_injection = bool(
        controller.phase == 3
        and not is_eliminated
        and is_meridian
        and meridian_mode == "CAPITAL_INJECTION"
        and ability_avail
    )

    is_prodigy = has_company_override(player, CompanyCode.HELIX, legacy_bridge_enabled(controller))
    is_phreaker = has_company_override(player, CompanyCode.OMNIDYNE, legacy_bridge_enabled(controller))
    is_phreaker_white_hat = has_signature_protocol(player, WhiteHatCode.PHREAKER, legacy_bridge_enabled(controller))
    pending_grad = (getattr(controller, "pending_graduation", {}) or {}).get(player_id)
    # Omnidyne Magnetic Splice: Phase 6 step 1
    can_phreaker = bool(
        controller.phase == PIPE
        and pending_grad is not None
        and not is_eliminated
        and is_phreaker
        and pending_grad.get("splice_available", False)
    )
    can_splice = can_phreaker
    can_choose_graduates = bool(controller.phase == PIPE and controller.subphase == "choose_graduates" and pending_grad is not None)
    in_income = bool(
        controller.phase == 3 and controller.subphase == "confirm_income"
        and not meta.get("income_confirmed", False) and not is_eliminated
    )
    purple_in_prod = any(
        (d.effective_face or d.current_face) is not None
        and (d.effective_face or d.current_face).is_star
        and (d.effective_face or d.current_face).star_code == "PURPLE_STAR"
        for d in player.in_production_dice
    )
    # Phreaker Jumper Diagnostics / Spook Burn Notice: Phase 3 Income (Purple ★ still In Production, OQ-2)
    can_phreaker_diagnostics = bool(in_income and is_phreaker_white_hat and purple_in_prod)
    is_spook_white_hat = has_signature_protocol(player, WhiteHatCode.SPOOK, legacy_bridge_enabled(controller))
    can_spook_burn = bool(in_income and is_spook_white_hat and purple_in_prod)

    purple_ok = bool(getattr(controller.state.config, "purple_purchasable", True))
    max_track_level = research_tracks.MAX_LEVEL
    pending_bt = (getattr(controller, "pending_breakthrough", {}) or {}).get(player_id)

    is_cipher = has_company_override(player, CompanyCode.PROMETHEUS, legacy_bridge_enabled(controller))
    can_cipher_buy = {}
    for color in [DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW, DieColor.PURPLE]:
        if color == DieColor.PURPLE:
            base_cost = player.get_purple_reserve_cost() if hasattr(player, "get_purple_reserve_cost") else (
                getattr(player.white_hat, "reserve_cost", 4) if getattr(player, "white_hat", None) else 4
            )
            has_stock = purple_ok and getattr(player, "personal_purple_reserve", 0) > 0
        else:
            base_cost = controller.state.get_market_die_cost(color) if hasattr(controller.state, "get_market_die_cost") else (
                4 if color in (DieColor.RED, DieColor.GREEN) else 5
            )
            has_stock = controller.state.market.get(color, 0) > 0

        disc_cost = max(0, base_cost - controller.state.config.cipher_market_discount)
        can_cipher_buy[color.value] = bool(
            controller.phase == OPS
            and is_active
            and not is_eliminated
            and is_cipher
            and ability_avail
            and meta["purchases_this_turn"] < controller.state.config.max_market_purchases_per_turn
            and has_stock
            and player.money >= disc_cost
        )
    can_cipher_cash = bool(
        controller.phase == OPS
        and is_active
        and not is_eliminated
        and is_cipher
        and ability_avail
    )
    can_cipher_dirty = can_cipher_cash

    is_acoustic = has_company_override(player, CompanyCode.AEGIS, legacy_bridge_enabled(controller))
    can_acoustic = bool(
        not is_eliminated
        and is_acoustic
        and ability_avail
        and controller.last_compile_result is not None
        and any(
            controller.last_compile_result.get("exited_cubes", {}).get(c.value, 0) > 0
            for c in [CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN]
        )
    )

    is_spook = has_company_override(player, CompanyCode.DTO, legacy_bridge_enabled(controller))
    slush_avail = player.is_slush_fund_available(active_ver) if active_ver else ability_avail
    can_spook = bool(
        not is_eliminated
        and not controller.state.config.slush_fund_once_per_game  # v0.35: chosen at Phase 4 confirm only
        and is_spook
        and slush_avail
        and controller.last_compile_result is not None
    )

    rolled_pool = meta.get("rolled_pool", [])
    in_roll = bool(controller.phase == 1 and meta["has_rolled"] and not meta["has_committed"] and not is_eliminated)
    purple_stars = [i for i, d in enumerate(rolled_pool)
                    if d.current_face and d.current_face.is_star and d.current_face.star_code == "PURPLE_STAR"]
    can_override_helix = bool(in_roll and is_prodigy and not meta.get("helix_override_used")
                              and (meta.get("prodigy_active", False) or ability_avail))
    can_override_release_l4 = bool(in_roll and not meta.get("release_l4_used")
                                   and release_l4_gray_faces(player, rolled_pool))
    can_override_ace = bool(in_roll and has_signature_protocol(player, WhiteHatCode.PRODIGY, legacy_bridge_enabled(controller))
                            and len(purple_stars) > meta.get("ace_uses", 0))
    can_prodigy = bool(
        controller.phase == 1
        and meta["has_rolled"]
        and not meta["has_committed"]
        and not is_eliminated
        and is_prodigy
        and (meta.get("prodigy_active", False) or ability_avail)
        # Brute-Force Bypass adds a free reroll
        and len(rolled_pool) > 0
    )
    can_reroll = (
        controller.phase == 1
        and meta["has_rolled"]
        and not meta["has_committed"]
        and not is_eliminated
        and meta.get("rerolls_remaining", 0) > 0
        and (
            any(not getattr(d, "is_locked", False) for d in rolled_pool)
            or (is_prodigy and (meta.get("prodigy_active", False) or ability_avail) and len(rolled_pool) > 0)
        )
    )
    can_lock_in = (controller.phase == 1 and meta["has_rolled"] and not meta["has_committed"] and not is_eliminated)
    can_compile = (controller.phase == 2 and controller.subphase == "ready_for_compile")

    can_confirm_income = bool(
        controller.phase == 3 and controller.subphase == "confirm_income"
        and not meta.get("income_confirmed", False) and not is_eliminated
    )
    can_confirm_attacks = bool(
        controller.phase == 4 and controller.subphase == "confirm_attacks" and not is_eliminated
        and player_id not in (getattr(controller, "attack_resolved_pids", set()) or set())
    )
    can_dirty = bool(
        controller.state.config.dirty_income_enabled
        and controller.phase == OPS
        and not can_confirm_income
        and is_active
        and not is_eliminated
        and not meta["dirty_income_taken_this_turn"]
        and player.secrets > controller.state.config.dirty_income_secret_cost
        and len(player.ready_dice) >= 1
    )
    can_end_turn = (controller.phase == OPS and not can_confirm_income and is_active and not is_eliminated)

    # Market purchase availability per color
    can_buy = {}
    for color in [DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW, DieColor.PURPLE]:
        if color == DieColor.PURPLE:
            cost = player.get_purple_reserve_cost() if hasattr(player, "get_purple_reserve_cost") else (
                getattr(player.white_hat, "reserve_cost", 4) if getattr(player, "white_hat", None) else 4
            )
            has_stock = purple_ok and getattr(player, "personal_purple_reserve", 0) > 0
        else:
            cost = controller.state.get_market_die_cost(color) if hasattr(controller.state, "get_market_die_cost") else (
                4 if color in (DieColor.RED, DieColor.GREEN) else 5
            )
            has_stock = controller.state.market.get(color, 0) > 0

        can_buy[color.value] = bool(
            controller.phase == OPS
            and not can_confirm_income
            and is_active
            and not is_eliminated
            and meta["purchases_this_turn"] < controller.state.config.max_market_purchases_per_turn
            and has_stock
            and player.money >= cost
        )
    can_buy_purple_reserve = bool(can_buy.get("purple", False))

    # Star actions
    can_star = {
        "B2": bool(
            controller.phase == OPS
            and not can_confirm_income
            and is_active
            and player.b2_available
            and player.money >= controller.state.config.b2_secret_cost
            and (
                controller.state.config.b2_secret_cap is None
                or player.secrets < controller.state.config.b2_secret_cap
            )
        ),
        "Y1": bool(controller.phase == OPS and not can_confirm_income and is_active and player.y1_available and player.money >= 6),
        "P1": bool(controller.phase == OPS and not can_confirm_income and is_active and player.p1_available),
        "P3": bool(
            controller.phase == OPS
            and not can_confirm_income
            and is_active
            and player.p3_available is not None
            and player.money >= controller.state.config.p3_cube_cash_cost
        ),
    }

    # Research Tracks (Pen Test = internal "DEFENSE", Public Relations = internal "PATENT")
    research_avail = player.research_tokens
    max_upgrades = getattr(controller.state.config, "max_hardware_upgrades_per_turn", 2)
    can_upgrade_limit = meta.get("upgrades_this_turn", 0) < max_upgrades
    upgrade_track_costs = {t.lower(): player.get_track_upgrade_cost(t) for t in research_tracks.TRACKS}
    can_upgrade_track = {
        t.lower(): bool(
            controller.phase == OPS
            and is_active
            and not is_eliminated
            and research_tracks.level_of(player, t) < max_track_level
            and pending_bt is None
            and can_upgrade_limit
            and upgrade_track_costs[t.lower()] is not None
            and research_avail >= upgrade_track_costs[t.lower()]
        )
        for t in research_tracks.TRACKS
    }

    cfg = controller.state.config
    share_regain = bool(getattr(cfg, "is_share_regain", False))
    # v0.36.0 Public Relations Track regain / Ad Campaign
    regain_cost, regain_cap = (research_tracks.regain_rate(cfg, player) if share_regain else (None, 0))
    ms_room = (player.market_share_max - player.market_share) if player.market_share is not None else 0
    regain_left = max(0, regain_cap - getattr(player, "regain_this_turn", 0)) if share_regain else 0
    can_regain = bool(
        share_regain
        and controller.phase == OPS
        and is_active
        and not is_eliminated
        and pending_bt is None
        and ms_room > 0
        and regain_left > 0
        and (player.money if cfg.share_regain_currency == "MONEY" else research_avail) >= regain_cost
    )
    # Pen Test Track: -1 Vulnerability per step, up to the level's limit per Operations Turn
    pen_limit = vulnerability.pen_test_limit(cfg, player)
    pen_left = max(0, pen_limit - int(player.pen_test_this_turn))
    pen_cost = vulnerability.pen_test_step_cost(cfg, player)
    pen_max_now = 0
    if controller.phase == OPS and is_active and not is_eliminated and pending_bt is None:
        pen_max_now = min(pen_left, player.vulnerability, research_avail // max(1, cfg.pen_test_cost))
        if pen_max_now and research_avail < pen_cost:
            pen_max_now = 0
    can_ad_campaign = bool(
        getattr(cfg, "is_market_share", False)
        and controller.phase == OPS
        and is_active
        and not is_eliminated
        and getattr(player, "r2_actions_available", 0) > 0
        and ms_room > 0
        and player.money >= cfg.r2_share_cost
    )
    can_star["R2"] = can_ad_campaign

    if can_confirm_income:
        can_phreaker = False
        can_cipher_buy = {color.value: False for color in [DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW, DieColor.PURPLE]}
        can_cipher_dirty = False

    caps: Dict[str, Any] = {
        "can_roll": can_roll,
        "can_hire_contractors": can_hire_contractors,
        "next_contractor_cost": next_contractor_cost,
        "can_capital_injection": can_capital_injection,
        "can_reroll": can_reroll,
        "can_lock_in": can_lock_in,
        "can_compile": can_compile,
        "can_confirm_income": can_confirm_income,
        "can_confirm_attacks": can_confirm_attacks,
        "can_aegis_echo": bool(
            can_confirm_attacks
            and ((((getattr(controller, "last_attack_result", None) or {}).get("threat_summary") or {}).get(player_id) or {})
                 .get("aegis", {}).get("available", False))
        ),
        "can_choose_graduates": can_choose_graduates,
        "can_splice": can_splice,
        "can_spook_burn": can_spook_burn,
        "can_buy": can_buy,
        "can_buy_purple_reserve": can_buy_purple_reserve,
        "can_dirty_income": can_dirty,
        "can_star": can_star,
        "can_upgrade_track": can_upgrade_track,
        "upgrade_track_costs": upgrade_track_costs,
        # v0.36.0 Market Share
        "is_market_share": bool(getattr(cfg, "is_market_share", False)),
        "is_share_regain": share_regain,
        "can_regain_market_share": can_regain,
        "regain_cost": regain_cost,
        "regain_currency": "money" if cfg.share_regain_currency == "MONEY" else "research",
        "regain_cap": regain_cap,
        "regain_left_this_turn": regain_left,
        "can_ad_campaign": can_ad_campaign,
        "ad_campaign_cost": cfg.r2_share_cost,
        "ad_campaign_actions": getattr(player, "r2_actions_available", 0),
        "track_names": {t.lower(): research_tracks.track_display_name(cfg, t) for t in research_tracks.TRACKS},
        # v0.46.0 Pen Test Track
        "can_pen_test": pen_max_now > 0,
        "pen_test_max_now": pen_max_now,
        "pen_test_limit": pen_limit,
        "pen_test_left_this_turn": pen_left,
        "pen_test_cost": pen_cost,
        "can_end_turn": can_end_turn,
        # Archetype capabilities
        "can_operator": can_operator,
        "can_prodigy": can_prodigy,
        "can_override_face_helix": can_override_helix,
        "can_override_face_prodigy": can_override_ace,
        "can_override_face_release_l4": can_override_release_l4,
        "release_l4_gray_indices": release_l4_gray_faces(player, rolled_pool) if can_override_release_l4 else [],
        "can_phreaker": can_phreaker,
        "can_phreaker_diagnostics": can_phreaker_diagnostics,
        "can_cipher_buy": can_cipher_buy,
        "can_cipher_dirty": can_cipher_dirty,
        "can_acoustic": can_acoustic,
        "can_spook": can_spook,
        "max_track_level": max_track_level,
        "slush_fund_used_game": bool(getattr(player, "slush_fund_used_game", False)),
        "next_upgrade_cost": {t.lower(): player.get_track_upgrade_cost(t) for t in research_tracks.TRACKS},
        "breakthrough_preview": {t.lower(): v for t, v in research_tracks.breakthrough_preview(player).items()},
        "pending_breakthrough": pending_bt,
        "can_resolve_breakthrough": bool(pending_bt is not None and is_active and controller.phase == OPS),
    }
    if not purple_ok:
        caps.pop("can_buy_purple_reserve", None)
        caps["can_buy"].pop("purple", None)
        caps["can_cipher_buy"].pop("purple", None)
    return caps

