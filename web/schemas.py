"""Data schemas, serializers, and validation for the Rogue Agent Web API."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from sim.config import ROUND_PHASE_NAMES, CubeColor, DieColor, EndGameReason
from sim.engine import EndGameResult, GameState, PlayerState, RoundTelemetry
from sim.entities import AbilityStatus, ArchetypeCard, Company, Die, effective_company, Face, VariantCard, VersionCard, WhiteHat


ARCHETYPE_FLAVOR: Dict[str, Dict[str, str]] = {
    "ACOUSTIC": {
        "role": "Pattern Genius // Mainframe Resonance",
        "flavor": '"Every mainframe hums before it strikes. Listen to the baffles -- you can hear which packet drops next."',
    },
    "PHREAKER": {
        "role": "Hardware Tinkerer // Emergency Relays",
        "flavor": '"A strip of Mylar splicing tape and a 2600-Hz whistle will fix what ten grand of silicon can\'t."',
    },
    "PRODIGY": {
        "role": "Reckless Hacker // Lock Bypassing",
        "flavor": '"Locked memory is just a polite suggestion from someone who left debug interrupts enabled."',
    },
    "SPOOK": {
        "role": "Ex-Intelligence // OpSec & Slush Funds",
        "flavor": '"Every breach has a price tag. That\'s what non-attributable slush accounts are for."',
    },
    "CIPHER": {
        "role": "Mathematician // Algorithmic Arbitrage",
        "flavor": '"Why pay retail for entropy when SETEC\'s own arbitrage equations subsidize the upgrade?"',
    },
    "OPERATOR": {
        "role": "Master Strategist // Contractor Dispatch",
        "flavor": '"Never burn internal hardware when three night-shift phreakers are waiting by a payphone."',
    },
}


# v0.49.0 card texts (RULES_APPENDIX.md Section 6 D); several simulation entities still carry older wording.
V046_COMPANY_TEXT: Dict[str, str] = {
    "MERIDIAN": "Gain an immediate +$3 cash payout from the bank.",
    "OMNIDYNE": "Move 1 die from your Research & Development directly to your Ready for Release Zone for free "
                "(bypassing the Sprint Plan); it banks its Secret now.",
    "AEGIS": "Ignore the damage of 1 Attack Cube for yourself this round: 1 Red cube (no Market Share loss), 1 Blue "
             "cube (no Secret loss), or 1 Green cube that hits you (no Secret loss; your Vulnerability still resets "
             "to 0). (All exited cubes remain in the exit tray and recycle into the Staging Cup as normal.)",
    "DTO": "Absorb up to 2 Corporate Secret loss from Blue cubes for free (once per game). Any additional Secret loss "
           "applies as normal.",
    "HELIX": "Once per game: for the rest of this phase you may reroll locked dice; after rerolls, turn 1 rolled die "
             "to any legal non-Star face of its color (the R&D face is allowed). Root Override Hijack can't mark an "
             "unused Bypass Used.",
    "PROMETHEUS": "Purchase 1 Colored Die from the Central Market at a $2 discount (minimum cost $0), OR gain an "
                  "immediate +$2 cash payout from the bank.",
}
V046_WHITE_HAT_TEXT: Dict[str, str] = {
    "OPERATOR": "When Face 6 (Purple ★) is rolled, gain +1 🔬 Research Token per different color die currently in "
                "your Sprint Plan (both sprints; all colors including Gray, Purple, and Yellow).",
    "PHREAKER": "When Face 6 (Purple ★) is rolled, gain +$1 cash AND +1 Release Bandwidth this round (applies in "
                "Phase 6 Step 3).",
    "ACOUSTIC": "When Face 6 (Purple ★) is rolled, gain +$1 cash per unique colored cube that exited the Cube Tower "
                "this round (including Operative Signature Cubes), up to +$5 max.",
    "SPOOK": "When Face 6 (Purple ★) is rolled, gain an immediate +$2 cash payout; in addition, you may optionally "
             "permanently return 1 owned Gray Legacy die to the box to gain +$3 cash.",
    "PRODIGY": "After all rerolls are finished (before assigning dice to In Production), turn 1 other rolled die in "
               "your active pool to any legal non-Star face of that die's color other than the R&D face.",
    "CIPHER": "When Face 6 (Purple ★) is rolled, gain an additional +$2 cash income AND +1 🔬 Research Token.",
}


def _patent_track_name(config: Any) -> str:
    from sim.engine import research_tracks

    return research_tracks.track_display_name(config, "PATENT")


def _regain(config: Any, player: Any) -> Tuple[Optional[int], int]:
    """(research per +1 Market Share, per-turn cap) under the Public Relations Track, else (None, 0)."""
    if not getattr(config, "is_share_regain", False):
        return None, 0
    from sim.engine import research_tracks

    return research_tracks.regain_rate(config, player)


class GameStateSerializer:
    """Serializes GameState, PlayerState, Dice, and telemetry objects into JSON-compatible dictionaries."""

    @staticmethod
    def serialize_face(face: Optional[Face]) -> Optional[Dict[str, Any]]:
        if face is None:
            return None
        return {
            "name": face.name,
            "money": face.money,
            "patches": face.patches,
            "secrets": face.secrets,
            "is_star": face.is_star,
            "star_code": face.star_code,
            "is_glitch": getattr(face, "is_glitch", False),
            "is_choice": getattr(face, "is_choice", False),
            "choices": [
                GameStateSerializer.serialize_face(c)
                for c in getattr(face, "choices", ())
            ],
            "has_cash_option": getattr(face, "has_cash_option", False),
            "has_patch_option": getattr(face, "has_patch_option", False),
            # v0.38.0
            "secrets_pending": bool(getattr(face, "secrets_pending", False)),
            "market_share": int(getattr(face, "market_share", 0)),
            "vuln": int(getattr(face, "vuln", 0) or 0),  # v0.49.0 ⚠ icons on this face
        }

    @staticmethod
    def serialize_die(die: Die, include_faces: bool = False) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "die_id": die.die_id,
            "color": die.color.value,
            "cost": die.cost,
            "vp": die.vp,
            "variant_code": die.variant_code,
            "is_locked": getattr(die, "is_locked", False),
            "is_contractor": die.color == DieColor.WHITE,
            "current_face": GameStateSerializer.serialize_face(die.current_face),
            "chosen_choice_index": getattr(die, "chosen_choice_index", None),
            "effective_face": GameStateSerializer.serialize_face(die.effective_face),
            "secret_pending": bool(getattr(die, "secret_pending", False)),
            "processing_entry_seq": int(getattr(die, "processing_entry_seq", 0)),
            "production_role": (
                die.production_role.value
                if hasattr(getattr(die, "production_role", None), "value")
                else getattr(die, "production_role", None)
            ),
        }
        if include_faces:
            data["faces"] = [GameStateSerializer.serialize_face(f) for f in die.faces]
        return data

    @staticmethod
    def serialize_variant_card(card: VariantCard) -> Dict[str, Any]:
        return {
            "code": card.code,
            "name": card.name,
            "die_color": card.die_color.value,
            "description": card.description,
            "star_face": GameStateSerializer.serialize_face(card.star_face),
            "cost": card.cost,  # Added in v0.26.0 (INV-VAR-COST-01)
            "printed_code": getattr(card, "printed_code", card.code),  # v0.36.0: R2_MKT / R3_MKT print as R2 / R3
        }

    @staticmethod
    def serialize_version_card(card: VersionCard) -> Dict[str, Any]:
        return {
            "version_str": card.version_str,
            "name": card.name,
            "staging_payload": {c.value: count for c, count in card.staging_payload.items()},
            "directive_description": card.directive_description,
            "directive_code": card.directive_code,
            "starting_cash_bonus": getattr(card, "starting_cash_bonus", 0),
            "track_capacity": card.track_capacity,
            "corruption_track": [
                {
                    "index": s.index,
                    "label": s.label,
                    "lose_money": s.lose_money,
                    "lose_patches": s.lose_patches,
                    "demote_dice": s.demote_dice,
                    "return_colored_dice": s.return_colored_dice,
                    "lose_secrets": s.lose_secrets,
                    "next_phase_lock": s.next_phase_lock,
                    "is_upgrade": s.is_upgrade,
                    "is_singularity": s.is_singularity,
                }
                for s in card.corruption_track
            ],
            "staging_payload_2p": {c.value: count for c, count in card.staging_payload_2p.items()}
            if card.staging_payload_2p is not None
            else None,
        }

    @staticmethod
    def serialize_company(company: Optional[Company]) -> Optional[Dict[str, Any]]:
        if company is None:
            return None
        return {
            "code": company.code.value if hasattr(company.code, "value") else str(company.code),
            "name": company.name,
            "sector": company.sector,
            "override_name": company.override_name,
            "timing_window": company.timing_window,
            "description": company.description,
            "flavor": company.flavor,
            "starting_setup_desc": "All tracks Level 0",
        }

    @staticmethod
    def serialize_white_hat(white_hat: Optional[WhiteHat]) -> Optional[Dict[str, Any]]:
        if white_hat is None:
            return None
        return {
            "code": white_hat.code.value if hasattr(white_hat.code, "value") else str(white_hat.code),
            "name": white_hat.name,
            "role": white_hat.role,
            "protocol_name": white_hat.protocol_name,
            "timing_window": white_hat.timing_window,
            "description": white_hat.description,
            "flavor": white_hat.flavor,
            "reserve_cost": getattr(white_hat, "reserve_cost", 4),  # Added in v0.26.0 (INV-RES-COST-01)
        }

    @staticmethod
    def serialize_archetype_card(card: Optional[ArchetypeCard]) -> Optional[Dict[str, Any]]:
        if card is None:
            return None
        code_str = card.code.value if hasattr(card.code, "value") else str(card.code)
        flavor_info = ARCHETYPE_FLAVOR.get(code_str.upper(), {
            "role": "White Hat Operative",
            "flavor": '"Information is the only true currency in the network."',
        })
        return {
            "code": code_str,
            "name": card.name,
            "role": flavor_info["role"],
            "flavor": flavor_info["flavor"],
            "timing_window": card.timing_window,
            "ability_name": card.ability_name,
            "description": card.description,
        }

    @staticmethod
    def calculate_player_vp(player: PlayerState, config: Any) -> int:
        """Returns player Corporate Secrets for v0.19.0 Pure Secrets Victory Scoring."""
        return player.secrets

    @staticmethod
    def _company_with_start(company: Optional[Dict[str, Any]], player: PlayerState, config: Any) -> Optional[Dict[str, Any]]:
        """Every Client Company starts identically except the colour of its starting colored die."""
        if company is None:
            return None
        company = dict(company, description=V046_COMPANY_TEXT.get(company["code"], company["description"]))
        if getattr(player, "company_color", None):
            company["starting_setup_desc"] = (
                f"All tracks Level 0; 2 Gray + Purple + {str(player.company_color).capitalize()} starting dice")
        return company

    @staticmethod
    def _secret_yield_now(player: PlayerState, config: Any) -> Dict[str, int]:
        from sim.engine import secret_faces

        if not secret_faces.enabled(config):
            return {}
        return {c.value: secret_faces.secret_yield(config, player, c) for c in secret_faces.SECRET_COLORS}

    @staticmethod
    def _white_hat_text(wh: Optional[Dict[str, Any]], config: Any) -> Optional[Dict[str, Any]]:
        if wh is not None and wh["code"] in V046_WHITE_HAT_TEXT:
            wh = dict(wh, description=V046_WHITE_HAT_TEXT[wh["code"]])
        return wh

    @staticmethod
    def _die_face_names(config: Any) -> Dict[str, List[str]]:
        """Printed face names per die type for the active ruleset (Market board and rules reference)."""
        from sim.entities import create_colored_die, create_gray_die, create_white_die

        out: Dict[str, List[str]] = {}
        profile = getattr(config, "die_face_profile", "V037")
        for color in (DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW, DieColor.PURPLE):
            die = create_colored_die(color=color, die_id=0, face_profile=profile, reserve_cost=4)
            out[color.value] = [("Variant (★)" if f.is_star else f.name) for f in die.faces]
        out["gray"] = [f.name for f in create_gray_die(0, getattr(config, "gray_face_profile", "V035_D1")).faces]
        out["white"] = [f.name for f in create_white_die(0).faces]
        return out

    @classmethod
    def _processing_box(cls, player: PlayerState, config: Any) -> List[Dict[str, Any]]:
        from sim.engine import secret_faces

        on = secret_faces.enabled(config)
        dice = secret_faces.triage_order(config, player, player.glitched_dice) if on else list(player.glitched_dice)
        out = []
        for i, d in enumerate(dice):
            row = cls.serialize_die(d)
            row["secret_yield"] = secret_faces.die_yield(config, player, d) if on else 0
            row["will_triage"] = i < getattr(player, "triage_bandwidth", 2)
            out.append(row)
        return out

    @classmethod
    def serialize_player(
        cls,
        player: PlayerState,
        config: Any,
        is_human: bool,
        name: str,
        bot_archetype: Optional[str] = None,
        rolled_pool: Optional[List[Die]] = None,
        has_rolled: bool = False,
        has_committed: bool = False,
        purchases_this_turn: int = 0,
        dirty_income_taken_this_turn: bool = False,
        locked_reroll_indices: Optional[List[int]] = None,
        hired_contractors: int = 0,
        contractor_dice: Optional[List[Die]] = None,
        rerolls_remaining: int = 0,
        max_rerolls: int = 2,
        rank: Optional[int] = None,
        income_this_round: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        vp = cls.calculate_player_vp(player, config)

        # In Phase 1 or 2, when dice have been rolled into rolled_pool, exclude active rolled dice from ready_dice visual list to avoid visual duplication.
        # Any worn dice (in unpatched_dice) must never appear in rolled_pool or ready_dice.
        unpatched_ids = {d.die_id for d in player.unpatched_dice}
        active_rolled_dice = [
            d for d in (rolled_pool or [])
            if d.die_id not in unpatched_ids
        ]
        rolled_dice = [cls.serialize_die(d, include_faces=True) for d in active_rolled_dice]

        if has_rolled:
            active_rolled_ids = {d.die_id for d in active_rolled_dice}
            visual_ready = [d for d in player.ready_dice if d.die_id not in active_rolled_ids]
        else:
            visual_ready = player.ready_dice

        hired_count = hired_contractors if hired_contractors else getattr(player, "hired_contractor_count", len(player.contractor_dice))
        max_hire = getattr(config, "contractor_max_hire", 3)
        if hired_count < max_hire and hasattr(config, "get_contractor_cost_for_hire"):
            next_contractor_cost = config.get_contractor_cost_for_hire(1, already_hired=hired_count)
        else:
            next_contractor_cost = None

        purple_reserve_cost = player.get_purple_reserve_cost() if hasattr(player, "get_purple_reserve_cost") else (
            getattr(player.white_hat, "reserve_cost", 4) if getattr(player, "white_hat", None) else 4
        )

        return {
            "player_id": player.player_id,
            "name": name,
            "is_human": is_human,
            "bot_archetype": bot_archetype,
            "company": cls._company_with_start(
                cls.serialize_company(effective_company(getattr(player, "company", None), config)), player, config),
            "white_hat": cls._white_hat_text(cls.serialize_white_hat(getattr(player, "white_hat", None)), config),
            "archetype": cls.serialize_archetype_card(getattr(player, "archetype", None)),
            "ability_v1_status": (
                player.ability_v1_status.value
                if hasattr(getattr(player, "ability_v1_status", None), "value")
                else str(getattr(player, "ability_v1_status", "LOCKED"))
            ),
            "ability_v2_status": (
                player.ability_v2_status.value
                if hasattr(getattr(player, "ability_v2_status", None), "value")
                else str(getattr(player, "ability_v2_status", "LOCKED"))
            ),
            "ability_v3_status": (
                player.ability_v3_status.value
                if hasattr(getattr(player, "ability_v3_status", None), "value")
                else str(getattr(player, "ability_v3_status", "LOCKED"))
            ),
            "v1_used": getattr(player, "v1_used", False),
            "v2_used": getattr(player, "v2_used", False),
            "v3_used": getattr(player, "v3_used", False),
            "money": player.money,
            "secrets": player.secrets,
            "patches": player.patches,
            "research_tokens": getattr(player, "research_tokens", player.patches),
            # v0.49.0 Vulnerability Track & Pen Test Track
            **cls._vulnerability(player, config),
            "triage_bandwidth": getattr(player, "triage_bandwidth", 2),
            "release_bandwidth": getattr(player, "release_bandwidth", 4),
            "scanned_over_release": max(0, len(player.scanned_dice) - getattr(player, "release_bandwidth", 4)),
            "income_this_round": income_this_round,
            "triage_level": getattr(player, "triage_level", 0),
            "release_level": getattr(player, "release_level", 0),
            "defense_level": getattr(player, "defense_level", 0),
            "patent_level": getattr(player, "patent_level", 0),
            "max_track_level": 4,
            "research_earned_total": getattr(player, "research_earned_total", 0),
            "breakthroughs": [b.as_dict() for b in getattr(player, "breakthroughs", [])],
            "l4_payouts": dict(getattr(player, "l4_payouts", {})),
            "slush_fund_used_game": bool(getattr(player, "slush_fund_used_game", False)),
            "purple_purchasable": bool(getattr(config, "purple_purchasable", True)),
            # v0.36.0 Market Share / Public Relations Track (None under the v0.35 ruleset)
            "market_share": getattr(player, "market_share", None),
            "market_share_max": getattr(player, "market_share_max", None),
            "patent_track_name": _patent_track_name(config),
            "target_locked": bool(getattr(player, "target_locked", False)),
            "encrypted_research_tracks": sorted(getattr(player, "encrypted_research_tracks", set()) or []),
            "regain_cost": _regain(config, player)[0],
            "regain_cap": _regain(config, player)[1],
            "regain_this_turn": getattr(player, "regain_this_turn", 0),
            "r2_actions_available": getattr(player, "r2_actions_available", 0),
            "is_patient_zero": player.is_patient_zero,
            "elimination_round": player.elimination_round,
            "elimination_reason": player.elimination_reason,
            "debt": player.debt,
            "breach_depth": player.breach_depth,
            "unfulfilled_destructions": player.unfulfilled_destructions,
            "total_dirty_income_taken": player.total_dirty_income_taken,
            "portfolio_value": vp,
            "rank": rank,
            # Canonical CI/CD zones (v0.22.0)
            "ready_for_release_dice": [cls.serialize_die(d) for d in player.ready_for_release_dice],
            "in_production_dice": [cls.serialize_die(d) for d in player.in_production_dice],
            "glitched_dice": [cls.serialize_die(d) for d in player.glitched_dice],
            # Research & Development (same zone as ``glitched_dice``), oldest first, with each die's current yield
            "processing_box_dice": cls._processing_box(player, config),
            "secret_yield_now": cls._secret_yield_now(player, config),
            "company_color": getattr(player, "company_color", None),
            "scanned_dice": [cls.serialize_die(d) for d in player.scanned_dice],
            "under_development_count": len(player.glitched_dice) + len(player.scanned_dice),
            "glitched_count": len(player.glitched_dice),
            "scanned_count": len(player.scanned_dice),
            # v0.48+ Sprint Plan split (``scanned_dice`` = the Sprint Plan): ids in the Current Sprint; the rest are Next
            "sprint_plan_enabled": bool(getattr(config, "sprint_plan_enabled", False)),
            "current_sprint_ids": sorted(d.die_id for d in player.scanned_dice
                                         if d.die_id in getattr(player, "current_sprint_ids", set())),
            # Backward compatibility aliases
            "ready_dice": [cls.serialize_die(d) for d in visual_ready],
            "all_ready_dice": [cls.serialize_die(d) for d in player.ready_dice],
            "unpatched_dice": [cls.serialize_die(d) for d in player.unpatched_dice],
            "rolled_pool": rolled_dice,
            # Phase 1 interaction state
            "has_rolled": has_rolled,
            "has_committed": has_committed,
            "locked_reroll_indices": locked_reroll_indices or [],
            "hired_contractors": hired_count,
            "next_contractor_cost": next_contractor_cost,
            "contractor_dice": [cls.serialize_die(d) for d in (contractor_dice if contractor_dice is not None else getattr(player, "contractor_dice", []))],
            "rerolls_remaining": rerolls_remaining,
            "max_rerolls": max_rerolls,
            "unlocked_dice_indices": [i for i, d in enumerate(active_rolled_dice) if not getattr(d, "is_locked", False)],
            # Personal Reserve (v0.24.0 / v0.26.0)
            "personal_purple_reserve": getattr(player, "personal_purple_reserve", 2),
            "purple_reserve_cost": purple_reserve_cost,
            "can_buy_purple_reserve": (
                bool(getattr(config, "purple_purchasable", True))
                and getattr(player, "personal_purple_reserve", 2) > 0
                and player.money >= purple_reserve_cost
                and purchases_this_turn < getattr(config, "max_market_purchases_per_turn", 2)
            ),
            # Phase 3 interaction state
            "purchases_this_turn": purchases_this_turn,
            "dirty_income_taken_this_turn": dirty_income_taken_this_turn,
            "b2_available": player.b2_available,
            "y1_available": player.y1_available,
            "p1_available": player.p1_available,
            "p3_available": player.p3_available.value if player.p3_available else None,
        }

    @staticmethod
    def _vulnerability(player: PlayerState, config: Any) -> Dict[str, Any]:
        from sim.engine import vulnerability

        v = int(player.vulnerability)
        floor = min(config.vuln_min_target_by_version)
        return {
            "vulnerability": v,
            "vulnerability_band_damage": vulnerability.band_damage(config, v) if v >= floor else 0,
            "pen_test_level": int(player.defense_level),
            "pen_test_limit": vulnerability.pen_test_limit(config, player),
            "pen_test_this_turn": int(getattr(player, "pen_test_this_turn", 0)),
        }

    @staticmethod
    def _vulnerability_track(state: GameState) -> Dict[str, Any]:
        from sim.engine import vulnerability

        cfg = state.config
        floor = vulnerability.min_target(cfg, state)
        th = list(cfg.vuln_band_thresholds)
        bands = []
        for i, (t, d) in enumerate(zip(th, cfg.vuln_band_damage)):
            lo, hi = max(t, floor), ((th[i + 1] - 1) if i + 1 < len(th) else cfg.vuln_track_max)
            if lo <= hi:
                bands.append({"from": lo, "to": hi, "damage": int(d)})
        return {
            "max": int(cfg.vuln_track_max),
            "safe_max": floor - 1,
            "min_target": floor,
            "bands": bands,
            "hit_reset": int(cfg.vuln_hit_reset),
            "pen_test_cost": int(cfg.pen_test_cost),
            "pen_test_limits": list(cfg.pen_test_limits),
            "pen_test_l4_free": int(cfg.pen_test_l4_free),
        }

    @classmethod
    def serialize_game_state(
        cls,
        state: GameState,
        controller_meta: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Serializes complete top-level GameState for REST response."""
        staged = {c.value: state.staging_cup.get(c, 0) for c in CubeColor}
        stuck = {c.value: state.tower.stuck_cubes.get(c, 0) for c in CubeColor}
        total_stuck = sum(stuck.values())

        market_serialized = {
            color.value: {
                "stock": state.market.get(color, 0),
                "cost": state.get_market_die_cost(color) if hasattr(state, "get_market_die_cost") else (4 if color in (DieColor.RED, DieColor.GREEN) else 5),
                "vp": 0,
                "variant": cls.serialize_variant_card(state.variant_cards[color])
                if color in state.variant_cards
                else None,
            }
            for color in [
                DieColor.RED,
                DieColor.BLUE,
                DieColor.GREEN,
                DieColor.YELLOW,
            ]
        }

        # Serialized players using controller metadata
        players_serialized = []
        player_ranks = controller_meta.get("player_ranks", {})

        for p in state.players:
            p_meta = controller_meta["players"].get(p.player_id, {})
            p_data = cls.serialize_player(
                player=p,
                config=state.config,
                is_human=p_meta.get("is_human", False),
                name=p_meta.get("name", f"Player {p.player_id + 1}"),
                bot_archetype=p_meta.get("bot_archetype"),
                rolled_pool=p_meta.get("rolled_pool", []),
                has_rolled=p_meta.get("has_rolled", False),
                has_committed=p_meta.get("has_committed", False),
                purchases_this_turn=p_meta.get("purchases_this_turn", 0),
                dirty_income_taken_this_turn=p_meta.get("dirty_income_taken_this_turn", False),
                locked_reroll_indices=p_meta.get("locked_reroll_indices", []),
                hired_contractors=p_meta.get("hired_contractors", getattr(p, "hired_contractor_count", 0)),
                contractor_dice=getattr(p, "contractor_dice", []),
                rerolls_remaining=p_meta.get("rerolls_remaining", 0),
                max_rerolls=p_meta.get("max_rerolls", 2),
                rank=player_ranks.get(p.player_id),
                income_this_round=(controller_meta.get("last_income_result") or {}).get(p.player_id),
            )
            players_serialized.append(p_data)

        # Active version card
        active_version = cls.serialize_version_card(state.active_version)
        version_deck_serialized = [cls.serialize_version_card(v) for v in state.version_deck]

        return {
            "game_id": controller_meta.get("game_id", "default"),
            "current_round": state.current_round,
            "phase": controller_meta.get("phase", 1),
            "phase_name": controller_meta.get("phase_name", ROUND_PHASE_NAMES[1]),
            "phase_names": controller_meta.get("phase_names", dict(ROUND_PHASE_NAMES)),
            "round_sequence": controller_meta.get("round_sequence", state.config.round_sequence.value),
            "subphase": controller_meta.get("subphase", "waiting_for_roll"),
            "active_player_index": controller_meta.get("active_player_index", 0),
            "first_player_index": state.first_player_index,
            "is_final_round": state.is_final_round,
            "game_over": state.game_over,
            "end_reason": state.end_reason.value if isinstance(state.end_reason, EndGameReason) else str(state.end_reason),
            "singularity_triggered": state.singularity_triggered,
            # v0.36.0 Market Share ruleset
            "red_mode": state.config.red_mode.value,
            "is_market_share": state.config.is_market_share,
            "is_share_regain": state.config.is_share_regain,
            "patent_track_name": _patent_track_name(state.config),
            "version_share_payout": dict(state.config.version_share_payout or {}),
            "version_comparisons": [r.as_dict() for r in getattr(state, "version_comparisons", [])],
            "market_collapse_triggered": getattr(state, "market_collapse_triggered", False),
            "market_collapse_round": getattr(state, "market_collapse_round", None),
            "market_collapse_pids": list(getattr(state, "market_collapse_pids", [])),
            "end_triggers": list(getattr(state, "end_triggers", [])),
            # Starting Corporate Secrets for this player count (before any Client Company bonus)
            "starting_secrets": state.config.get_starting_secrets(len(state.players)),
            # v0.37.0 Market Leader Bonus schedule for this player count ([] when disabled)
            "is_market_leader_bonus": bool(getattr(state.config, "is_market_leader_bonus", False)),
            "rules_version": "v0.49.0",
            "is_secret_faces": bool(getattr(state.config, "secret_face_enabled", False)),
            # v0.49.0 Vulnerability Track (Central SETEC Agent Board) and Pen Test Track
            "vulnerability_track": cls._vulnerability_track(state),
            "is_round_leader_bonus": bool(getattr(state.config, "is_red_secret_payout", False)),
            "round_leader_bonus_schedule": list(state.config.red_secret_payout_schedule(len(state.players))
                                                if getattr(state.config, "is_red_secret_payout", False) else []),
            "red_secret_banked_this_round": bool(getattr(state, "red_secret_banked_this_round", False)),
            "last_round_bonus": controller_meta.get("last_round_bonus"),
            "secret_yields": {
                "red": state.config.red_secret_owner_yield if state.config.red_secret_owner_yield is not None else None,
                "blue_base": state.config.secret_yield_blue_base,
                "blue_grid": state.config.secret_yield_blue_grid_l3_bonus, "blue_cap": state.config.secret_yield_blue_cap,
                "green_base": state.config.secret_yield_green_base,
                "green_vuln_reduction": int(state.config.green_secret_vuln_reduction),
                "purple": state.config.secret_yield_purple,
            },
            "market_leader_bonus_schedule": list(state.config.market_leader_bonus_schedule(len(state.players))
                                                 if hasattr(state.config, "market_leader_bonus_schedule") else []),
            # Temp Staffing & Contractors (v0.6 / v0.7)
            "contractor_supply": getattr(state, "contractor_supply", 12),
            "contractor_hire_cost": getattr(state.config, "contractor_hire_cost", 1),
            "contractor_cost_progression": list(getattr(state.config, "contractor_cost_progression", (1, 2, 3))),
            "contractor_max_hire": getattr(state.config, "contractor_max_hire", 3),
            "next_contractor_cost": controller_meta.get("action_capabilities", {}).get("next_contractor_cost"),
            # Compiler / Tower & Corruption
            "staging_cup": staged,
            "tower_stuck_cubes": stuck,
            "tower_total_stuck": total_stuck,
            "priming_exited_cubes": {c.value: count for c, count in getattr(state, "priming_exited_cubes", {}).items()},
            "priming_stuck_cubes": {c.value: count for c, count in getattr(state, "priming_stuck_cubes", {}).items()},
            "last_round_buffer_overflow": getattr(state, "last_round_buffer_overflow", False),
            "total_buffer_overflows": getattr(state, "total_buffer_overflows", 0),
            "corruption_track": state.corruption_track,
            "corruption_capacity": state.corruption_track_capacity,
            "pending_version_advance": getattr(state, "pending_version_advance", False),
            "overflow_black_cubes_on_next_track": getattr(state, "overflow_black_cubes_on_next_track", 0),
            "pending_extra_version_advances": getattr(state, "pending_extra_version_advances", 0),
            "current_version_index": state.current_version_index,
            "active_version": active_version,
            "version_deck": version_deck_serialized,
            "last_compile_result": controller_meta.get("last_compile_result"),
            # Phase results (3 Income / 4 Attack Resolution / 6 CI/CD Pipeline Shift)
            "last_income_result": controller_meta.get("last_income_result", {}),
            "last_attack_result": controller_meta.get("last_attack_result"),
            "last_pipeline_result": controller_meta.get("last_pipeline_result", {}),
            "pending_graduation": controller_meta.get("pending_graduation", {}),
            # Market
            "market": market_serialized,
            "die_faces": cls._die_face_names(state.config),
            # Players
            "players": players_serialized,
            # Action Dock Capabilities for the active human player
            "action_capabilities": controller_meta.get("action_capabilities", {}),
            # Event Log
            "event_log": controller_meta.get("event_log", []),
            # Final Rankings (if game over)
            "final_result": controller_meta.get("final_result"),
        }


# =============================================================================
# Request Validation & Helpers
# =============================================================================

def parse_request_json(raw_body: bytes | str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Safely decodes and parses JSON request bodies."""
    if not raw_body:
        return {}, None
    try:
        if isinstance(raw_body, bytes):
            raw_body = raw_body.decode("utf-8")
        data = json.loads(raw_body)
        if not isinstance(data, dict):
            return None, "Request body must be a JSON object"
        return data, None
    except json.JSONDecodeError as exc:
        return None, f"Invalid JSON format: {exc.msg}"
    except Exception as exc:
        return None, f"Failed to parse request: {str(exc)}"


def validate_player_id(data: Dict[str, Any], max_player_id: int) -> Tuple[Optional[int], Optional[str]]:
    if "player_id" not in data:
        return None, "Missing required field: 'player_id'"
    pid = data["player_id"]
    if not isinstance(pid, int):
        return None, "'player_id' must be an integer"
    if not (0 <= pid <= max_player_id):
        return None, f"'player_id' out of range: must be between 0 and {max_player_id}"
    return pid, None


def validate_die_index(data: Dict[str, Any], max_index: int) -> Tuple[Optional[int], Optional[str]]:
    if "die_index" not in data:
        return None, "Missing required field: 'die_index'"
    idx = data["die_index"]
    if not isinstance(idx, int):
        return None, "'die_index' must be an integer"
    if not (0 <= idx < max_index):
        return None, f"'die_index' out of range: must be between 0 and {max_index - 1}"
    return idx, None


def validate_color(color_str: str) -> Tuple[Optional[DieColor], Optional[str]]:
    try:
        color = DieColor(color_str.lower())
        return color, None
    except ValueError:
        valid_colors = [c.value for c in DieColor]
        return None, f"Invalid color '{color_str}'. Must be one of: {valid_colors}"


def error_response(message: str, status_code: int = 400) -> Tuple[Dict[str, Any], int]:
    return {"success": False, "error": message}, status_code


def success_response(data: Dict[str, Any], status_code: int = 200) -> Tuple[Dict[str, Any], int]:
    payload = {"success": True}
    payload.update(data)
    return payload, status_code
