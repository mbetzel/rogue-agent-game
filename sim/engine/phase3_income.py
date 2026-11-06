"""Phase 3: Income (Simultaneous).

Collects ``$``, ``🔬`` and ``★`` outputs from every die still In Production (Income slot and Shield slots,
including White Contractor dice), then resolves the income-timed Signature Protocols
(Spook *Burn Notice*, Phreaker *Jumper Diagnostics*). Runs after Phase 2 corruption and before
Phase 4 Attack Resolution (INV-SEQ-INCOME-BEFORE-ATTACK-01).
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Tuple, Union

from sim.config import DieColor
from sim.entities import ArchetypeCode, Face, WhiteHatCode, has_signature_protocol, legacy_bridge_enabled
from sim.engine.state import IncomeRecord

if TYPE_CHECKING:
    from sim.engine.core import GameEngine
    from sim.engine.state import Commitments, GameState, PlayerState
    from sim.entities import Die


_STAR_NOTES = {
    "Y3": "Proprietary Training (+1 Secret → Glitched)",
    "B3": "Air-Gapped Backup (1 Glitched → Scanned)",
    "R1": "Ransom Insurance (+$2)",
    "G1": "Self-Healing Kernel (+1 🔬)",
    "G2": "Universal Sandbox (+1 🔬)",
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


def _die_income_row(state: GameState, player: PlayerState, die: Die) -> Optional[Dict[str, Any]]:
    """Pure: the income this die yields in Phase 3 (None for glitch / no face)."""
    eff = die.effective_face or die.current_face
    if not eff or eff.is_glitch:
        return None
    money = eff.money
    research = eff.patches
    secrets = eff.secrets
    star_note: Optional[str] = None
    if eff.is_star:
        code = eff.star_code
        if code == "Y2":
            count = len({d.color for d in player.colored_dice})
            total_payout = min(state.config.y2_max_payout, state.config.y2_base_payout + count)
            bonus = max(0, total_payout - eff.money)
            money += bonus
            star_note = f"Cloud Monopoly (+${bonus} bonus)"
        elif code == "PURPLE_STAR":
            if _is_operative(player, WhiteHatCode.ACOUSTIC, legacy_bridge_enabled(state)):
                exited = _exited_cubes_for_acoustic(state)
                gain = min(4, len({c for c, n in exited.items() if n > 0}))
                money += gain
                star_note = f"Resonance Sensor (+${gain})"
            elif _is_operative(player, WhiteHatCode.CIPHER, legacy_bridge_enabled(state)):
                money += 2
                research += 1
                star_note = "Algorithmic Parity (+$2, +1 🔬)"
            elif _is_operative(player, WhiteHatCode.SPOOK, legacy_bridge_enabled(state)):
                money += 2
                star_note = "Burn Notice (+$2)"
        else:
            star_note = _STAR_NOTES.get(code)
    role = getattr(die, "production_role", None)
    return {
        "die_id": die.die_id,
        "color": die.color.value,
        "face_name": eff.name,
        "money": money,
        "patches": research,
        "research": research,
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

    for die in list(player.in_production_dice):
        row = _die_income_row(engine.state, player, die)
        if row is None:
            continue
        player.money += row["money"]
        player.patches += row["research"]
        player.secrets += row["secrets"]
        record.money += row["money"]
        record.research += row["research"]
        record.secrets += row["secrets"]
        record.details.append(row)

        eff = die.effective_face or die.current_face
        if eff.is_star:
            if eff.star_code == "Y3":
                # Proprietary Training: move die to glitched_dice after collecting secret
                dice_to_glitch.append(die)
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

    for die in dice_to_glitch:
        if die in player.in_production_dice:
            player.in_production_dice.remove(die)
            die.production_role = None
            player.glitched_dice.append(die)

    return record


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
        record.secrets += row["secrets"]
        record.details.append(row)
    record.purple_star_triggers = len(purple_star_dice_in_production(player))
    return record


def resolve_spook_burn_notice(
    engine: GameEngine,
    player: PlayerState,
    die_id: int,
) -> bool:
    """Spook Face 6 Protocol (Burn Notice):
    Permanently returns 1 owned colored die to market to gain +1 Corporate Secret.
    """
    target_die: Optional[Die] = None
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
    player.secrets += 1
    return True


def resolve_phreaker_jumper_diagnostics(
    engine: GameEngine,
    player: PlayerState,
    die_id: Optional[int] = None,
    rng: Optional[random.Random] = None,
    forced_face: Optional[Face] = None,
) -> Optional[Face]:
    """Phreaker Face 6 Protocol (Jumper Diagnostics):
    Rolls 1 die currently in Under Development; harvests rolled cash/patches; die remains in place.
    INV-PHREAKER-FALLBACK-01: If Under Development is empty, yields +$1 cash fallback immediately.
    """
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
        player.patches += face.patches
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


def _burnable_ids(player: PlayerState) -> set:
    zones = player.in_production_dice + player.glitched_dice + player.scanned_dice + player.ready_for_release_dice
    return {d.die_id for d in zones if d.color not in (DieColor.GRAY, DieColor.WHITE)}


def _bot_burn_choice(engine: GameEngine, player: PlayerState, burned: List[int]) -> Optional[int]:
    """Bot Burn Notice target for one trigger. If the bot names a die that was already burned (or is no
    longer burnable), re-ask once, then fall back to the BaseBot default, so a trigger is not wasted."""
    from sim.bots.base import BaseBot

    valid = _burnable_ids(player) - set(burned)
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
    return triggers


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
    return results
