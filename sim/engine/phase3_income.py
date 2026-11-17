"""Phase 3: Income (Simultaneous).

Collects ``$``, ``🔬`` and ``★`` outputs from every die still In Production (Income slot and Shield slots,
including White Contractor dice), then resolves the income-timed Signature Protocols
(Spook *Burn Notice*, Phreaker *Jumper Diagnostics*). Runs after Phase 2 corruption and before
Phase 4 Attack Resolution (INV-SEQ-INCOME-BEFORE-ATTACK-01).
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Tuple, Union

from sim.config import CubeColor, DieColor, EndGameReason
from sim.entities import (
    ArchetypeCode,
    CompanyCode,
    Face,
    WhiteHatCode,
    has_company_override,
    has_signature_protocol,
    legacy_bridge_enabled,
)
from sim.engine.state import IncomeRecord, ProductionRole
from sim.engine import secret_faces

if TYPE_CHECKING:
    from sim.engine.core import GameEngine
    from sim.engine.state import Commitments, GameState, PlayerState
    from sim.entities import Die


_STAR_NOTES = {
    "Y3": "Proprietary Training (+1 Secret → Glitched)",
    "B3": "Air-Gapped Backup (1 Glitched → Scanned)",
    "R1": "Ransom Insurance (+$2)",  # label uses the active Red card's name (see _die_income_row)
    "R2_MKT": "Ad Campaign (Phase 6: pay $2 for +1 Market Share)",
    "R3_MKT": "Customer Poaching (take 1 Market Share)",
    "G1": "Self-Healing Kernel (+1 🔬)",
    "G2": "Universal Sandbox (+2 🔬)",
    "G3": "Live Reboot (+$1, +2 🔬)",
}


def _is_operative(player: PlayerState, wh_code: WhiteHatCode, bridge: bool = False) -> bool:
    """Signature Protocols come only from the White Hat Dossier (legacy bridge aside)."""
    return has_signature_protocol(player, wh_code, bridge)


def _exited_cubes_for_acoustic(state: GameState) -> Dict[Any, int]:
    exited = getattr(state, "last_exited_cubes", None)
    if not exited:
        exited = getattr(state.tower, "last_exited_cubes", {})
    return exited or {}


def _exited_blue_cubes(state: GameState) -> int:
    cr = getattr(state, "last_compile_result", None)
    if cr is not None and getattr(cr, "exited_cubes", None) is not None:
        return int(cr.exited_cubes.get(CubeColor.BLUE, 0))
    exited = getattr(state, "last_exited_cubes", None)
    if not exited:
        exited = getattr(getattr(state, "tower", None), "last_exited_cubes", {}) or {}
    return int(exited.get(CubeColor.BLUE, 0))


def _die_income_row(state: GameState, player: PlayerState, die: Die) -> Optional[Dict[str, Any]]:
    """Pure: the income this die yields in Phase 3 (None for glitch / no face)."""
    eff = die.effective_face or die.current_face
    if not eff or eff.is_glitch:
        return None
    money = eff.money
    research = eff.patches
    secrets = eff.secrets
    protocol_research = 0
    star_note: Optional[str] = None
    is_v044 = getattr(state.config, "variant_profile", None) == "V044"
    if eff.is_star:
        code = eff.star_code
        if is_v044 and code in ("B1", "B2", "B3", "G1", "G2", "G3", "Y1", "Y2", "Y3", "R1", "R2", "R3"):
            cfg = state.config
            if code == "R1":
                star_note = "Brand Protection (+$2, +1 MS)"
            elif code == "R2":
                money = 0
                star_note = "Ad Campaign (modal -$2 -> +2 MS)"
            elif code == "R3":
                money = 0
                star_note = "Customer Poaching (take 1 MS)"
            elif code == "B1":
                blue_exited = _exited_blue_cubes(state)
                if blue_exited == 0:
                    research = cfg.b1_quiet_research
                    money = 0
                    star_note = f"Honeypot Telemetry (+{research} 🔬)"
                else:
                    research = 0
                    money = cfg.b1_threat_cash
                    star_note = f"Honeypot Telemetry (+${money})"
            elif code == "B2":
                money = 0  # Resolved modally in collect_player_production_income
                star_note = "Deep R&D Vault (modal)"
            elif code == "B3":
                shield_count = len(player.shield_dice)
                money = cfg.b3_base_cash + cfg.b3_shield_multiplier * shield_count
                star_note = f"Air-Gapped Backup (+${money})"
            elif code == "G1":
                research = cfg.g1_research
                star_note = f"Self-Healing Kernel (+{research} 🔬, clean {cfg.g1_slots_cleaned} slot)"
            elif code == "G2":
                g = getattr(player, "glitched_shield_slots", 0)
                research = cfg.g2_base_research + g * cfg.g2_glitch_multiplier
                star_note = f"Universal Sandbox (+{research} 🔬)"
            elif code == "G3":
                research = cfg.g3_research
                money = cfg.g3_cash
                star_note = f"Live Reboot (+{research} 🔬, +${money})"
            elif code == "Y1":
                money = 0  # Resolved modally in collect_player_production_income
                star_note = "Algorithmic Trading (modal)"
            elif code == "Y2":
                cm_colors = {
                    d.color for d in player.total_dice
                    if d.color in (DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW)
                }
                money = min(cfg.y2_max_cash, cfg.y2_base_cash + cfg.y2_cm_multiplier * len(cm_colors))
                star_note = f"Cloud Monopoly (+${money})"
            elif code == "Y3":
                secrets = cfg.y3_base_secrets
                gray_count = sum(1 for d in player.total_dice if d.color == DieColor.GRAY)
                money = gray_count * cfg.y3_gray_multiplier
                star_note = f"Proprietary Training (+{secrets} Secret, +${money})"
        elif code == "Y2":
            count = len({d.color for d in player.colored_dice})
            total_payout = min(state.config.y2_max_payout, state.config.y2_base_payout + count)
            bonus = max(0, total_payout - eff.money)
            money += bonus
            star_note = f"Cloud Monopoly (+${bonus} bonus)"
        elif code == "PURPLE_STAR":
            rebalance = getattr(state.config, "white_hat_6f_rebalance", False)
            if _is_operative(player, WhiteHatCode.ACOUSTIC, legacy_bridge_enabled(state)):
                if rebalance:
                    gain = getattr(state, "distinct_exited_colors_this_round", 0)
                else:
                    exited = _exited_cubes_for_acoustic(state)
                    gain = min(4, len({c for c, n in exited.items() if n > 0}))
                money += gain
                star_note = f"Resonance Sensor (+${gain})"
            elif _is_operative(player, WhiteHatCode.PHREAKER, legacy_bridge_enabled(state)) and rebalance:
                money += 1
                star_note = "Jumper Diagnostics (+$1, +1 Bandwidth)"
            elif _is_operative(player, WhiteHatCode.CIPHER, legacy_bridge_enabled(state)):
                money += 2
                research += 1
                protocol_research = 1
                star_note = "Algorithmic Parity (+$2, +1 🔬)"
            elif _is_operative(player, WhiteHatCode.SPOOK, legacy_bridge_enabled(state)):
                money += 2
                star_note = "Burn Notice (+$2)"
            elif _is_operative(player, WhiteHatCode.OPERATOR, legacy_bridge_enabled(state)):
                if rebalance:
                    distinct_count = len({d.color for d in player.scanned_dice})
                    research += distinct_count
                    protocol_research = distinct_count
                    star_note = f"Logistics Bounty (+{distinct_count} 🔬, {distinct_count} colors)"
                elif getattr(state.config, "operator_protocol_mode", "CONTINGENT_STAFFING") == "LOGISTICS_BOUNTY":
                    gain_research = getattr(state.config, "operator_logistics_bounty_research", 1)
                    research += gain_research
                    protocol_research = gain_research
                    star_note = f"Logistics Bounty (+{gain_research} 🔬)"
        elif code == "R1":
            card = (getattr(state, "variant_cards", None) or {}).get(DieColor.RED)
            star_note = f"{card.name} (+$2)" if card is not None and card.code == "R1" else _STAR_NOTES.get(code)
        elif code == "G2":
            is_v038 = (
                getattr(state.config, "variant_profile", None) == "V038_DRAFT"
                or getattr(state.config, "glitched_shield_slots_enabled", False)
            )
            if is_v038:
                g = getattr(player, "glitched_shield_slots", 0)
                bonus = g * getattr(state.config, "g2_glitch_bonus", 1)
                research = getattr(state.config, "g2_base_research", eff.patches) + bonus
                if g > 0:
                    star_note = f"Universal Sandbox (+{research} 🔬, incl. +{bonus} from {g} glitched slots)"
                else:
                    star_note = f"Universal Sandbox (+{research} 🔬)"
            else:
                star_note = f"Universal Sandbox (+{research} 🔬)"
        else:
            star_note = _STAR_NOTES.get(code)
    role = getattr(die, "production_role", None)
    extra = {"market_share": eff.market_share} if eff.market_share else {}  # v0.38 Red F1 / R1 only
    return {
        **extra,
        "die_id": die.die_id,
        "color": die.color.value,
        "face_name": eff.name,
        "money": money,
        "patches": research,
        "research": research,
        "research_source": "star" if eff.is_star and eff.star_code != "PURPLE_STAR" else "income",
        "protocol_research": protocol_research,
        "secrets": secrets,
        "star_note": star_note,
        "role": role.value if hasattr(role, "value") else (role or "INCOME"),
    }


def collect_player_production_income(engine: GameEngine, player: PlayerState, plan: Any = None) -> IncomeRecord:
    """Collect income from ALL dice remaining in in_production_dice (contractors included).

    Returns an IncomeRecord with the deltas and per-die rows (legacy callers ignore it).
    """
    record = IncomeRecord()
    dice_to_glitch: List[Die] = []
    dice_to_scan: List[Die] = []
    v038_cards = engine.config.variant_profile == "V038_DRAFT"
    is_v044 = getattr(engine.config, "variant_profile", None) == "V044"
    v044_modal_stars: List[Tuple[str, Die]] = []

    for die in list(player.in_production_dice):
        row = _die_income_row(engine.state, player, die)
        if row is None:
            continue
        player.money += row["money"]
        base_research = row["research"] - row.get("protocol_research", 0)
        player.gain_research(base_research, row.get("research_source", "income"))
        player.gain_research(row.get("protocol_research", 0), "signature_protocol")
        eff = die.effective_face or die.current_face
        if row["secrets"] > 0:
            source = "blue_face" if die.color == DieColor.BLUE else ("y3" if (eff and eff.star_code == "Y3") or row.get("star_note") == "0-Day Broker" else "face")
            player.gain_secrets(row["secrets"], source)
        record.money += row["money"]
        record.research += row["research"]
        record.protocol_research += row.get("protocol_research", 0)
        record.secrets += row["secrets"]
        record.details.append(row)
        if row.get("market_share") and engine.config.is_market_share:
            # v0.38 Red F1 / R1: Phase 3 income, clamped at the maximum, outside the Public Relations limit
            player.change_market_share(+row["market_share"], "face")

        if eff and eff.is_star:
            if is_v044:
                code = eff.star_code
                if code == "G1":
                    cleaned = secret_faces.clean_slots(player, engine.config.g1_slots_cleaned, "face")
                    player.f6_g1_activations += 1
                    if cleaned > 0 and player.shields_on_glitched_slots > 0:
                        to_promote = min(cleaned, player.shields_on_glitched_slots)
                        promoted = 0
                        for sd in player.in_production_dice:
                            if promoted >= to_promote:
                                break
                            if getattr(sd, "production_role", None) == ProductionRole.PURGING_SHIELD:
                                sd.production_role = ProductionRole.CLEAN_SHIELD
                                promoted += 1
                        player.shields_on_glitched_slots = max(0, player.shields_on_glitched_slots - promoted)
                        player.shields_on_clean_slots += promoted
                        player.f6_g1_shield_promotions += promoted
                elif code == "G3":
                    if player.scanned_dice:
                        target = player.bot.choose_g3_reboot_target(player, list(player.scanned_dice), engine.state)
                        if target is not None and target in player.scanned_dice:
                            player.scanned_dice.remove(target)
                            _reset(target)
                            player.ready_for_release_dice.append(target)
                            player.f6_g3_graduations += 1
                        else:
                            player.f6_g3_fizzles += 1
                    else:
                        player.f6_g3_fizzles += 1
                elif code in ("R3", "R3_MKT") and engine.config.is_market_share:
                    from sim.engine import market_share

                    market_share.queue_poach(engine, player, die.die_id)
                elif code in ("R2", "B2", "Y1"):
                    v044_modal_stars.append((code, die))
            elif eff.star_code == "Y3":
                # Proprietary Training: move die to glitched_dice after collecting secret
                # (v0.38 Variant profile: to the Scanned Box)
                (dice_to_scan if v038_cards else dice_to_glitch).append(die)
            elif eff.star_code == "R2_MKT" and engine.config.is_market_share:
                # Ad Campaign: latch one paid Phase 6 action (INV-MS-R2-01)
                player.r2_actions_available += 1
            elif eff.star_code == "R3_MKT" and engine.config.is_market_share:
                # Customer Poaching: resolved after all players' Income (market_share.resolve_poaches)
                from sim.engine import market_share

                market_share.queue_poach(engine, player, die.die_id)
            elif eff.star_code == "B3" and secret_faces.enabled(engine.config):
                # v0.38 Air-Gapped Backup: 1 die Processing Box -> Scanned Box, banking its Secret (Phase-3 state)
                order = player.bot.choose_triage_order(player, list(player.glitched_dice), engine.state)
                target_die = _first_valid(order, player.glitched_dice)
                if target_die is not None:
                    player.glitched_dice.remove(target_die)
                    _reset(target_die)
                    secret_faces.bank(engine.config, player, target_die, engine.state)
                    player.scanned_dice.append(target_die)
            elif eff.star_code == "B3":
                # Air-Gapped Backup (INV-B3-BACKUP-01): Move 1 die from glitched_dice to scanned_dice
                if player.glitched_dice:
                    target_die = max(
                        player.glitched_dice,
                        key=lambda d: (1 if d.color != DieColor.GRAY else 0, getattr(d, "cost", 0), d.die_id),
                    )
                    player.glitched_dice.remove(target_die)
                    target_die.production_role = None
                    target_die.is_locked = False
                    target_die.chosen_choice_index = None
                    target_die.current_face = None
                    for attr in ("rolled_face_idx", "rolled_effect", "prod_role", "overclock_face"):
                        if hasattr(target_die, attr):
                            setattr(target_die, attr, None)
                    player.scanned_dice.append(target_die)

    if is_v044 and v044_modal_stars:
        cfg = engine.config
        for code, _die in v044_modal_stars:
            if code == "R2":
                if (
                    player.money >= cfg.r2_cost_cash
                    and player.market_share is not None
                    and player.market_share < player.market_share_max
                    and player.bot.choose_r2_ad_campaign(player, engine.state)
                ):
                    player.money -= cfg.r2_cost_cash
                    player.change_market_share(cfg.r2_gain_market_share, "r2")
                    player.f6_r2_activations += 1
                    player.r2_uses += 1
                    record.money -= cfg.r2_cost_cash
            elif code == "B2":
                mode = player.bot.choose_b2_vault_mode(player, engine.state)
                if mode == "market_share" and player.secrets >= cfg.b2_secret_cost:
                    player.gain_secrets(-cfg.b2_secret_cost, "b2")
                    if player.market_share is not None:
                        player.change_market_share(cfg.b2_market_share_gain, "b2")
                    player.f6_b2_secret_activations += 1
                    record.secrets -= cfg.b2_secret_cost
                    if player.secrets <= 0:
                        player.is_patient_zero = True
                        player.elimination_round = engine.state.current_round
                        player.elimination_reason = "Total Breach (<= 0 Secrets)"
                        player.breach_depth = max(0, -player.secrets)
                        player.f6_b2_suicide_breaches += 1
                        if all(p.is_patient_zero for p in engine.state.players):
                            engine.state.game_over = True
                            engine.state.end_reason = EndGameReason.TOTAL_WIPEOUT
                        else:
                            engine.state.is_final_round = True
                            engine.state.end_reason = EndGameReason.PATIENT_ZERO
                            engine.state.final_round_trigger_phase = 3
                else:
                    player.money += cfg.b2_base_cash
                    player.f6_b2_cash_activations += 1
                    record.money += cfg.b2_base_cash
            elif code == "Y1":
                mode = player.bot.choose_y1_algo_mode(player, engine.state)
                if mode == "secret" and player.money >= cfg.y1_secret_cost:
                    player.money -= cfg.y1_secret_cost
                    player.gain_secrets(cfg.y1_secret_gain, "y1")
                    player.f6_y1_secret_activations += 1
                    record.money -= cfg.y1_secret_cost
                    record.secrets += cfg.y1_secret_gain
                else:
                    player.money += cfg.y1_base_cash
                    player.f6_y1_cash_activations += 1
                    record.money += cfg.y1_base_cash

    pre_move_scanned_colors = len({d.color for d in player.scanned_dice})
    for die in dice_to_glitch:
        if die in player.in_production_dice:
            player.in_production_dice.remove(die)
            die.production_role = None
            player.glitched_dice.append(die)
    for die in dice_to_scan:
        if die in player.in_production_dice:
            player.in_production_dice.remove(die)
            _reset(die)
            player.scanned_dice.append(die)

    if getattr(engine.config, "white_hat_6f_rebalance", False):
        if _is_operative(player, WhiteHatCode.OPERATOR, legacy_bridge_enabled(engine)):
            record.operator_scanned_count = pre_move_scanned_colors
            player.operator_scanned_colors_count = pre_move_scanned_colors
            player.operator_research_harvested += record.protocol_research
        if _is_operative(player, WhiteHatCode.ACOUSTIC, legacy_bridge_enabled(engine)):
            record.acoustic_colors_count = getattr(engine.state, "distinct_exited_colors_this_round", 0)

    return record


def _reset(d: Die) -> None:
    d.production_role = None
    d.is_locked = False
    d.chosen_choice_index = None
    d.current_face = None


def _first_valid(order: Any, pool: List[Die]) -> Optional[Die]:
    ids = {id(d) for d in pool}
    for d in order or []:
        if id(d) in ids:
            return d
    return pool[0] if pool else None


collect_production_income = collect_player_production_income


def preview_player_income(state: GameState, player: PlayerState) -> IncomeRecord:
    """Pure (no mutation) preview of this player's Phase 3 production income.

    Single source of truth for web previews and bot expected-income estimates. Signature Protocol
    outcomes (Burn Notice / Jumper Diagnostics) are choice- or dice-dependent and not included.
    """
    record = IncomeRecord()
    for die in player.in_production_dice:
        row = _die_income_row(state, player, die)
        if row is None:
            continue
        record.money += row["money"]
        record.research += row["research"]
        record.protocol_research += row.get("protocol_research", 0)
        record.secrets += row["secrets"]
        record.details.append(row)
    record.purple_star_triggers = len(purple_star_dice_in_production(player))
    if getattr(state.config, "white_hat_6f_rebalance", False):
        if _is_operative(player, WhiteHatCode.OPERATOR, legacy_bridge_enabled(state)):
            record.operator_scanned_count = len({d.color for d in player.scanned_dice})
        if _is_operative(player, WhiteHatCode.ACOUSTIC, legacy_bridge_enabled(state)):
            record.acoustic_colors_count = getattr(state, "distinct_exited_colors_this_round", 0)

    return record


def resolve_operator_logistics_bounty(player: PlayerState, triggers: int) -> int:
    """Awards +1 research per distinct die color currently in the Scanned Box per trigger."""
    if triggers <= 0 or not player.scanned_dice:
        return 0
    distinct_colors = len({d.color for d in player.scanned_dice})
    research_gain = triggers * distinct_colors
    if research_gain > 0:
        player.gain_research(research_gain, "signature_protocol")
        player.operator_scanned_colors_count = distinct_colors
        player.operator_research_harvested += research_gain
    return research_gain


def compute_distinct_exited_colors(exited_cubes: Dict[Any, int], exited_signature_pids: Iterable[int]) -> int:
    """Calculates distinct exited colors from Phase 2 drop (capped at 5)."""
    compiler_colors = sum(
        1 for c, n in exited_cubes.items()
        if n > 0 and c in (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN, CubeColor.BLACK)
    )
    sig_colors = len(set(exited_signature_pids))
    return min(5, compiler_colors + sig_colors)


def resolve_acoustic_resonance_sensor(state: GameState, player: PlayerState, triggers: int) -> int:
    """Awards +$1 cash per distinct exited cube color (max $5) per trigger."""
    unit_cash = getattr(state, "distinct_exited_colors_this_round", 0)
    total_gain = triggers * unit_cash
    player.money += total_gain
    return total_gain


def resolve_cipher_algorithmic_parity(player: PlayerState, triggers: int) -> Tuple[int, int]:
    """Awards +$2 cash and +1 research per trigger unconditionally."""
    cash_gain = triggers * 2
    research_gain = triggers * 1
    player.money += cash_gain
    player.gain_research(research_gain, "signature_protocol")
    return cash_gain, research_gain


def resolve_spook_burn_notice(
    engine: GameEngine,
    player: PlayerState,
    die_id: int,
) -> bool:
    """Spook Face 6 Protocol (Burn Notice):
    v0.43.0: Permanently returns 1 owned Gray Legacy die to the box for +$3 cash.
    Legacy: Permanently returns 1 owned colored die to market to gain +1 Corporate Secret.
    """
    if getattr(engine.config, "white_hat_6f_rebalance", False):
        target_die: Optional[Die] = None
        target_zone: Optional[List[Die]] = None
        for zone in (player.in_production_dice, player.scanned_dice, player.glitched_dice, player.ready_for_release_dice):
            for d in zone:
                if d.die_id == die_id and d.color == DieColor.GRAY:
                    target_die = d
                    target_zone = zone
                    break
            if target_die:
                break

        if not target_die or target_zone is None:
            return False

        target_zone.remove(target_die)
        if target_zone is player.glitched_dice:
            from sim.engine import secret_faces

            secret_faces.lose_pending(player, target_die)

        player.money += 3
        return True

    target_die = None
    for zone in (player.in_production_dice, player.glitched_dice, player.scanned_dice, player.ready_for_release_dice):
        for d in zone:
            if d.die_id == die_id and d.color not in (DieColor.GRAY, DieColor.WHITE):
                target_die = d
                zone.remove(d)
                break
        if target_die:
            break

    if not target_die:
        return False

    if target_die.color in engine.state.market:
        engine.state.market[target_die.color] += 1
    # If Purple, die is scrapped and not returned to market
    from sim.engine import secret_faces

    secret_faces.lose_pending(player, target_die)
    player.gain_secrets(1, "burn_notice")
    return True


def resolve_phreaker_jumper_diagnostics(
    engine: GameEngine,
    player: PlayerState,
    die_id: Optional[int] = None,
    rng: Optional[random.Random] = None,
    forced_face: Optional[Face] = None,
    triggers: int = 1,
) -> Optional[Face]:
    """Phreaker Face 6 Protocol (Jumper Diagnostics):
    v0.43.0: Awards +$1 cash and +1 temporary Release Bandwidth per trigger.
    Legacy: Rolls 1 die currently in Under Development; harvests rolled cash/patches; die remains in place.
    """
    cfg = engine.config
    if getattr(cfg, "white_hat_6f_rebalance", False):
        player.money += triggers * 1
        player.temp_release_bandwidth_bonus += triggers
        return Face(name=f"Jumper Diagnostics (+${triggers}, +{triggers} Bandwidth)")
    if cfg.power_profile == "V038_DRAFT" and player.glitched_dice:
        target = secret_faces.best_pending(cfg, player, die_id)
        player.glitched_dice.remove(target)
        _reset(target)
        secret_faces.bank(cfg, player, target, engine.state)
        player.scanned_dice.append(target)
        return Face(name=f"Processing Box -> Scanned Box (die {target.die_id})")
    if cfg.power_profile == "V038_DRAFT":
        ud_dice = list(player.scanned_dice)
    else:
        ud_dice = player.under_development_dice
    if not ud_dice:
        # Fallback: grant +$1 cash directly to player
        player.money += 1
        return None

    target_die = None
    if die_id is not None:
        target_die = next((d for d in ud_dice if d.die_id == die_id), None)
    if target_die is None:
        target_die = ud_dice[0]

    if forced_face is not None:
        target_die.current_face = forced_face
        face = forced_face
    else:
        roll_rng = rng or engine.rng
        face = target_die.roll(roll_rng)

    if face and not face.is_glitch and not face.is_star:
        player.money += face.money
        player.gain_research(face.patches, "signature_protocol")
    return face


def purple_star_dice_in_production(player: PlayerState) -> List[Die]:
    """Purple ★ dice still In Production (OQ-2: required for any Signature Protocol to fire)."""
    out = []
    for d in player.in_production_dice:
        eff = d.effective_face or d.current_face
        if eff is not None and eff.is_star and eff.star_code == "PURPLE_STAR":
            out.append(d)
    return out


_ASK_BOT = ...  # sentinel: "ask the bot"
DieChoice = Union[int, None, List[Optional[int]], "ellipsis"]


def _nth_choice(choice: Any, n: int) -> Any:
    """Resolves the n-th trigger's explicit choice. A list gives one entry per trigger; a scalar applies
    to the first trigger only (further triggers fall back to the bot hook)."""
    if choice is _ASK_BOT:
        return _ASK_BOT
    if isinstance(choice, (list, tuple)):
        return choice[n] if n < len(choice) else None
    return choice if n == 0 else _ASK_BOT


def _burnable_ids(player: PlayerState, rebalance: bool = False) -> set:
    zones = player.in_production_dice + player.glitched_dice + player.scanned_dice + player.ready_for_release_dice
    if rebalance:
        return {d.die_id for d in zones if d.color == DieColor.GRAY}
    return {d.die_id for d in zones if d.color not in (DieColor.GRAY, DieColor.WHITE)}


def _bot_burn_choice(engine: GameEngine, player: PlayerState, burned: List[int]) -> Optional[int]:
    """Bot Burn Notice target for one trigger. If the bot names a die that was already burned (or is no
    longer burnable), re-ask once, then fall back to the BaseBot default, so a trigger is not wasted."""
    from sim.bots.base import BaseBot

    rebalance = bool(getattr(engine.config, "white_hat_6f_rebalance", False))
    valid = _burnable_ids(player, rebalance=rebalance) - set(burned)
    if rebalance:
        for _ in range(2):
            choice = player.bot.choose_spook_burn_gray(player, engine.state, engine.rng, set(burned))
            if choice is None:
                return None
            if choice in valid:
                return choice
        choice = BaseBot.choose_spook_burn_gray(player.bot, player, engine.state, engine.rng, set(burned))
        return choice if choice in valid else None

    for _ in range(2):
        choice = player.bot.choose_spook_burn_notice(player, engine.state, engine.rng)
        if choice is None:
            return None  # bot declines
        if choice in valid:
            return choice
    choice = BaseBot.choose_spook_burn_notice(player.bot, player, engine.state, engine.rng)
    return choice if choice in valid else None


def resolve_income_signature_protocols(
    engine: GameEngine,
    player: PlayerState,
    *,
    spook_burn_die_id: DieChoice = _ASK_BOT,
    phreaker_die_id: DieChoice = _ASK_BOT,
    trigger_count: Optional[int] = None,
    record: Optional[IncomeRecord] = None,
) -> int:
    """Phase 3 Signature Protocols: fire once per Purple ★ die still In Production at Phase 3 start
    (OQ-2 / OQ-17). ``...`` means ask the bot hook; ``None`` declines (Burn Notice) or lets
    Jumper Diagnostics pick the default target. Returns the number of triggers."""
    triggers = len(purple_star_dice_in_production(player)) if trigger_count is None else trigger_count
    if triggers <= 0:
        return 0
    is_spook = _is_operative(player, WhiteHatCode.SPOOK, legacy_bridge_enabled(engine))
    is_phreaker = _is_operative(player, WhiteHatCode.PHREAKER, legacy_bridge_enabled(engine))
    if not (is_spook or is_phreaker):
        return triggers

    rebalance = bool(getattr(engine.config, "white_hat_6f_rebalance", False))
    if rebalance and is_phreaker:
        # +$1 cash per Purple ★ was already collected in _die_income_row; grant temporary Release Bandwidth here.
        player.temp_release_bandwidth_bonus += triggers
        if record is not None:
            record.phreaker_bandwidth_bonus += triggers
            record.diagnostics_face = f"Jumper Diagnostics (+${triggers}, +{triggers} Bandwidth)"
        return triggers

    burned: List[int] = []
    for n in range(triggers):
        if is_spook:
            choice = _nth_choice(spook_burn_die_id, n)
            if choice is _ASK_BOT:
                choice = _bot_burn_choice(engine, player, burned)
            if choice is not None and choice not in burned:
                if resolve_spook_burn_notice(engine, player, int(choice)):
                    burned.append(int(choice))
        elif is_phreaker:
            choice = _nth_choice(phreaker_die_id, n)
            if choice is _ASK_BOT:
                choice = None
                if player.under_development_dice:
                    choice = player.bot.choose_phreaker_jumper_diagnostics(player, engine.state, engine.rng)
            face = resolve_phreaker_jumper_diagnostics(engine, player, choice, engine.rng)
            if record is not None:
                record.diagnostics_face = face.name if face is not None else "Fallback (+$1)"
    if record is not None and burned:
        record.burned_die_ids.extend(burned)
        record.burned_die_id = burned[0]
        if rebalance:
            record.burned_gray_die_ids.extend(burned)
    return triggers


def resolve_meridian_capital_injection(
    engine: GameEngine,
    player: PlayerState,
    record: Optional[IncomeRecord] = None,
) -> bool:
    """Phase 3 Institutional Override: Meridian Capital Injection (+3 cash once per version)."""
    active_ver = engine.state.active_version.version_str if (engine.state and engine.state.active_version) else None
    is_meridian = (
        has_company_override(player, CompanyCode.MERIDIAN, legacy_bridge_enabled(engine))
        and player.is_ability_available(active_ver)
        and getattr(engine.config, "meridian_override_mode", "REDUNDANT_CREW") == "CAPITAL_INJECTION"
    )
    if not is_meridian:
        return False

    use_injection = player.bot.choose_meridian_capital_injection(
        player_state=player,
        game_state=engine.state,
        rng=engine.rng,
    )
    if use_injection:
        cash = getattr(engine.config, "meridian_capital_injection_cash", 3)
        player.gain_money(cash, "capital_injection")
        player.mark_ability_used(active_ver)
        if record is not None:
            record.capital_injection_used = True
            record.capital_injection_cash = cash
        return True
    return False


def execute_player_income(
    engine: GameEngine,
    player: PlayerState,
    *,
    spook_burn_die_id: DieChoice = _ASK_BOT,
    phreaker_die_id: DieChoice = _ASK_BOT,
) -> IncomeRecord:
    """One player's Phase 3: (a) production income incl. contractors / Acoustic / Cipher / Spook +$2 /
    Y2 / B3 / Y3 (Y3 dice -> Glitched), then (b) Signature Protocols per Purple ★ die."""
    money0, research0, secrets0 = player.money, player.research_tokens, player.secrets
    triggers = len(purple_star_dice_in_production(player))  # latched at Phase 3 start (OQ-2)
    record = collect_player_production_income(engine, player)
    record.purple_star_triggers = triggers
    resolve_income_signature_protocols(
        engine,
        player,
        spook_burn_die_id=spook_burn_die_id,
        phreaker_die_id=phreaker_die_id,
        trigger_count=triggers,
        record=record,
    )
    resolve_meridian_capital_injection(engine, player, record=record)
    record.money = player.money - money0
    record.research = player.research_tokens - research0
    record.secrets = player.secrets - secrets0
    return record


def execute_income(engine: GameEngine, player_commitments: Optional[Commitments] = None) -> Dict[int, IncomeRecord]:
    """Phase 3 for every survivor (simultaneous; player-index order)."""
    results: Dict[int, IncomeRecord] = {}
    if engine.state.game_over:
        return results
    for player in engine.state.players:
        if player.is_patient_zero:
            continue
        results[player.player_id] = execute_player_income(engine, player)
    finalize_income(engine)
    return results


def finalize_income(engine: GameEngine) -> List[Dict[str, Any]]:
    """v0.36.0: closing step of Phase 3, after every player's Income: resolve Customer Poaching (R3).

    The web controller must call this once after all players' Income. No-op under RANSOM.
    """
    from sim.engine import market_share

    return market_share.resolve_poaches(engine)
