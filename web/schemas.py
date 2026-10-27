"""Data schemas, serializers, and validation for the Rogue Agent Web API."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from sim.config import CubeColor, DieColor, EndGameReason, ShieldColor
from sim.engine import EndGameResult, GameState, PlayerState, RoundTelemetry
from sim.entities import Die, Face, VariantCard, VersionCard


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
        }

    @staticmethod
    def serialize_version_card(card: VersionCard) -> Dict[str, Any]:
        return {
            "version_str": card.version_str,
            "name": card.name,
            "staging_payload": {c.value: count for c, count in card.staging_payload.items()},
            "directive_description": card.directive_description,
            "directive_code": card.directive_code,
            "staging_payload_2p": {c.value: count for c, count in card.staging_payload_2p.items()}
            if card.staging_payload_2p is not None
            else None,
        }

    @staticmethod
    def calculate_player_vp(player: PlayerState, config: Any) -> int:
        secret_vp = max(0, player.secrets) * config.vp_per_secret
        dice_vp = sum(config.vp_per_die.get(d.color, 0) for d in player.total_dice)
        cash_vp = max(0, player.money) // config.vp_cash_divisor
        return secret_vp + dice_vp + cash_vp

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

        return {
            "player_id": player.player_id,
            "name": name,
            "is_human": is_human,
            "bot_archetype": bot_archetype,
            "money": player.money,
            "secrets": player.secrets,
            "patches": player.patches,
            "is_patient_zero": player.is_patient_zero,
            "elimination_round": player.elimination_round,
            "elimination_reason": player.elimination_reason,
            "debt": player.debt,
            "breach_depth": player.breach_depth,
            "unfulfilled_destructions": player.unfulfilled_destructions,
            "total_dirty_income_taken": player.total_dirty_income_taken,
            "portfolio_value": vp,
            "rank": rank,
            # Dice zones
            "ready_dice": [cls.serialize_die(d) for d in visual_ready],
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
                "cost": 4 if color in (DieColor.RED, DieColor.GREEN, DieColor.PURPLE) else 5,
                "vp": state.config.vp_per_die.get(color, 0),
                "variant": cls.serialize_variant_card(state.variant_cards[color])
                if color in state.variant_cards
                else None,
            }
            for color in [
                DieColor.RED,
                DieColor.BLUE,
                DieColor.GREEN,
                DieColor.YELLOW,
                DieColor.PURPLE,
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
            )
            players_serialized.append(p_data)

        # Active version card
        active_version = cls.serialize_version_card(state.active_version)
        version_deck_serialized = [cls.serialize_version_card(v) for v in state.version_deck]

        return {
            "game_id": controller_meta.get("game_id", "default"),
            "current_round": state.current_round,
            "phase": controller_meta.get("phase", 1),
            "phase_name": controller_meta.get("phase_name", "Boot & Configure"),
            "subphase": controller_meta.get("subphase", "waiting_for_roll"),
            "active_player_index": controller_meta.get("active_player_index", 0),
            "first_player_index": state.first_player_index,
            "is_final_round": state.is_final_round,
            "game_over": state.game_over,
            "end_reason": state.end_reason.value if isinstance(state.end_reason, EndGameReason) else str(state.end_reason),
            "singularity_triggered": state.singularity_triggered,
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
            "corruption_track": state.corruption_track,
            "corruption_capacity": state.config.corruption_track_capacity,
            "current_version_index": state.current_version_index,
            "active_version": active_version,
            "version_deck": version_deck_serialized,
            "last_compile_result": controller_meta.get("last_compile_result"),
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
