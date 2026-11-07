"""Data schemas, serializers, and validation for the Rogue Agent Web API."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from sim.config import ROUND_PHASE_NAMES, CubeColor, DieColor, EndGameReason, ShieldColor
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
            "block_amount": face.block_amount,
            "shield_color": face.shield_color.value if face.shield_color else None,
            "money": face.money,
            "patches": face.patches,
            "secrets": face.secrets,
            "is_star": face.is_star,
            "star_code": face.star_code,
            "is_shield": face.is_shield,
            "is_glitch": getattr(face, "is_glitch", False),
            "is_choice": getattr(face, "is_choice", False),
            "choices": [
                GameStateSerializer.serialize_face(c)
                for c in getattr(face, "choices", ())
            ],
            "has_cash_option": getattr(face, "has_cash_option", False),
            "has_shield_option": getattr(face, "has_shield_option", False),
            "has_patch_option": getattr(face, "has_patch_option", False),
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
        desc_parts = []
        def_cap = getattr(company, "starting_defense_capacity", 2)
        tri_bw = getattr(company, "starting_triage_bandwidth", 2)
        rel_bw = getattr(company, "starting_release_bandwidth", 4)
        tri_lvl = getattr(company, "starting_triage_level", 0)
        rel_lvl = getattr(company, "starting_release_level", 0)
        def_lvl = getattr(company, "starting_defense_level", 0)
        pat_lvl = getattr(company, "starting_patent_level", 0)
        cash_bonus = getattr(company, "starting_cash_bonus", 0)
        res_bonus = getattr(company, "starting_research_bonus", 0)
        sec_bonus = getattr(company, "starting_secrets_bonus", 0)
        up_disc = getattr(company, "upgrade_discount", 0)

        if pat_lvl > 0:
            desc_parts.append(f"Starts at Patent Lvl {pat_lvl} (3 🔬 cost)")
        if res_bonus > 0:
            desc_parts.append(f"+{res_bonus} 🔬 Starting Research")
        if cash_bonus > 0:
            desc_parts.append(f"+${cash_bonus} Starting Cash")
        if sec_bonus > 0:
            desc_parts.append(f"+{sec_bonus} Starting Secret")
        if def_lvl > 0:
            desc_parts.append(f"Defense Lvl {def_lvl} ({def_cap} Shields Cap)")
        if tri_lvl > 0:
            desc_parts.append(f"Triage Lvl {tri_lvl} (Bandwidth {tri_bw})")
        if rel_lvl > 0:
            desc_parts.append(f"Release Lvl {rel_lvl} (Bandwidth {rel_bw})")
        if up_disc > 0:
            desc_parts.append(f"-{up_disc} 🔬 Track Upgrade Discount")
        if not desc_parts:
            desc_parts.append(f"Def Cap {def_cap}, Triage {tri_bw}, Release {rel_bw}")

        return {
            "code": company.code.value if hasattr(company.code, "value") else str(company.code),
            "name": company.name,
            "sector": company.sector,
            "override_name": company.override_name,
            "timing_window": company.timing_window,
            "description": company.description,
            "flavor": company.flavor,
            "starting_setup_desc": ", ".join(desc_parts),
            "starting_defense_capacity": def_cap,
            "starting_triage_bandwidth": tri_bw,
            "starting_release_bandwidth": rel_bw,
            "starting_triage_level": tri_lvl,
            "starting_release_level": rel_lvl,
            "starting_defense_level": def_lvl,
            "starting_patent_level": pat_lvl,
            "starting_cash_bonus": cash_bonus,
            "starting_research_bonus": res_bonus,
            "starting_secrets_bonus": sec_bonus,
            "upgrade_discount": up_disc,
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

    @classmethod
    def serialize_player(
        cls,
        player: PlayerState,
        config: Any,
        is_human: bool,
        name: str,
        bot_archetype: Optional[str] = None,
        rolled_pool: Optional[List[Die]] = None,
        shield_slots: Optional[Dict[str, List[Die]]] = None,
        has_rolled: bool = False,
        has_committed: bool = False,
        commitments: Optional[Dict[int, str]] = None,
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
        rolled_dice = [cls.serialize_die(d) for d in active_rolled_dice]

        if has_rolled:
            active_rolled_ids = {d.die_id for d in active_rolled_dice}
            visual_ready = [d for d in player.ready_dice if d.die_id not in active_rolled_ids]
        else:
            visual_ready = player.ready_dice

        slots_serialized: Dict[str, List[Dict[str, Any]]] = {
            "red": [],
            "blue": [],
            "green": [],
            "any": [],
        }
        if shield_slots:
            for color_key, dice_list in shield_slots.items():
                # Only include shield dice that haven't worn into unpatched
                slots_serialized[color_key] = [
                    cls.serialize_die(d)
                    for d in dice_list
                    if d.die_id not in unpatched_ids
                ]

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
            "company": cls.serialize_company(effective_company(getattr(player, "company", None), config)),
            "white_hat": cls.serialize_white_hat(getattr(player, "white_hat", None)),
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
            "defense_capacity": getattr(player, "defense_capacity", 2),
            "triage_bandwidth": getattr(player, "triage_bandwidth", 2),
            "release_bandwidth": getattr(player, "release_bandwidth", 4),
            "scanned_over_release": max(0, len(player.scanned_dice) - getattr(player, "release_bandwidth", 4)),
            "income_this_round": income_this_round,
            "triage_level": getattr(player, "triage_level", 0),
            "release_level": getattr(player, "release_level", 0),
            "pipeline_level": getattr(player, "pipeline_level", 0),
            "defense_level": getattr(player, "defense_level", 0),
            "patent_level": getattr(player, "patent_level", 0),
            "has_emergency_hotfix": getattr(player, "has_emergency_hotfix", False),
            "has_passive_firewall": getattr(player, "has_passive_firewall", False),
            # v0.35.0 research tracks (levels 0..4)
            "research_track_model": getattr(getattr(config, "research_track_model", None), "value", "V034_THREE_LEVEL"),
            "max_track_level": 4 if getattr(config, "is_v035_tracks", False) else 2,
            "research_earned_total": getattr(player, "research_earned_total", 0),
            "breakthroughs": [b.as_dict() for b in getattr(player, "breakthroughs", [])],
            "l4_payouts": dict(getattr(player, "l4_payouts", {})),
            "patent_cost": player.get_patent_cost() if hasattr(player, "get_patent_cost") else 4,
            "patent_gain": player.get_patent_gain() if hasattr(player, "get_patent_gain") else 1,
            "slush_fund_used_game": bool(getattr(player, "slush_fund_used_game", False)),
            "purple_purchasable": bool(getattr(config, "purple_purchasable", True)),
            # v0.36.0 Market Share / Public Relations Track (None under the v0.35 ruleset)
            "market_share": getattr(player, "market_share", None),
            "market_share_max": getattr(player, "market_share_max", None),
            "patent_track_name": _patent_track_name(config),
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
            "scanned_dice": [cls.serialize_die(d) for d in player.scanned_dice],
            "production_slots": {
                "income": [cls.serialize_die(d) for d in player.income_dice],
                "red_shield": [cls.serialize_die(d) for d in player.red_shield_dice],
                "blue_shield": [cls.serialize_die(d) for d in player.blue_shield_dice],
                "green_shield": [cls.serialize_die(d) for d in player.green_shield_dice],
                "any_shield": [cls.serialize_die(d) for d in player.any_shield_dice],
            },
            "under_development_count": len(player.glitched_dice) + len(player.scanned_dice),
            "glitched_count": len(player.glitched_dice),
            "scanned_count": len(player.scanned_dice),
            # Backward compatibility aliases
            "ready_dice": [cls.serialize_die(d) for d in visual_ready],
            "all_ready_dice": [cls.serialize_die(d) for d in player.ready_dice],
            "unpatched_dice": [cls.serialize_die(d) for d in player.unpatched_dice],
            "rolled_pool": rolled_dice,
            "shield_slots": slots_serialized,
            # Phase 1 interaction state
            "has_rolled": has_rolled,
            "has_committed": has_committed,
            "commitments": commitments or {},
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
                shield_slots=p_meta.get("shield_slots"),
                has_rolled=p_meta.get("has_rolled", False),
                has_committed=p_meta.get("has_committed", False),
                commitments=p_meta.get("commitments"),
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
            "research_track_model": state.config.research_track_model.value,
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
            # Temp Staffing & Contractors (v0.6 / v0.7)
            "contractor_supply": getattr(state, "contractor_supply", 12),
            "contractor_hire_cost": getattr(state.config, "contractor_hire_cost", 1),
            "contractor_cost_progression": list(getattr(state.config, "contractor_cost_progression", (1, 2, 3))),
            "contractor_max_hire": getattr(state.config, "contractor_max_hire", 3),
            "next_contractor_cost": controller_meta.get("action_capabilities", {}).get("next_contractor_cost"),
            "max_patch_tokens": state.config.max_patch_tokens,
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
            # v0.34 six-phase results (Phase 3 Income / Phase 4 Attack Resolution / Phase 5 Pipeline Shift)
            "last_income_result": controller_meta.get("last_income_result", {}),
            "last_attack_result": controller_meta.get("last_attack_result"),
            "last_pipeline_result": controller_meta.get("last_pipeline_result", {}),
            "pending_graduation": controller_meta.get("pending_graduation", {}),
            # Market
            "market": market_serialized,
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


def validate_shield_color(color_str: str) -> Tuple[Optional[ShieldColor], Optional[str]]:
    try:
        color = ShieldColor(color_str.lower())
        if color not in (ShieldColor.RED, ShieldColor.BLUE, ShieldColor.GREEN):
            return None, f"Shield color must be 'red', 'blue', or 'green', got '{color_str}'"
        return color, None
    except ValueError:
        return None, f"Invalid shield color '{color_str}'. Must be 'red', 'blue', or 'green'"


def error_response(message: str, status_code: int = 400) -> Tuple[Dict[str, Any], int]:
    return {"success": False, "error": message}, status_code


def success_response(data: Dict[str, Any], status_code: int = 200) -> Tuple[Dict[str, Any], int]:
    payload = {"success": True}
    payload.update(data)
    return payload, status_code
