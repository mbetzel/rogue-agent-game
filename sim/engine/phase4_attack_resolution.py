"""Phase 4: Attack Resolution (Simultaneous).

Passive Firewall, Two-Stage Defensive Blocking, Red / Blue / Green damage (incl. Aegis *Baffle Echo*
and DTO *Slush Fund*), damage-conditional ``★`` faces (R2, R3, B1), Snowball Recycle, Contractor
Expiration and the end-of-Phase-4 End Game Trigger check.

v0.36.0 (``red_mode=MARKET_SHARE``): unblocked Red (Market Manipulation) lowers Market Share instead of
costing Money; Stage 2 Generic shields may be the player's free choice (``any_shield_policy=FREE_CHOICE``);
Market Collapse is checked after the Patient Zero / Total Wipeout logic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, AbstractSet, Callable, Dict, List, Optional, Tuple

from sim.config import AnyShieldPolicy, CubeColor, DieColor, EndGameReason, RedVariantSet, ShieldColor
from sim.entities import has_company_override, has_signature_protocol, legacy_bridge_enabled
from sim.entities import ArchetypeCode, CompanyCode, Die
from sim.engine.state import ProductionRole
from sim.engine import market_share, research_tracks

if TYPE_CHECKING:
    from sim.engine.core import GameEngine
    from sim.engine.state import Commitments, CompileResult, PlayerState


MalwareTargetSelector = Callable[["PlayerState", List[Die], int], List[Die]]

# Web humans may explicitly decline Aegis *Baffle Echo* (``aegis_color_override=AEGIS_DECLINE``).
AEGIS_DECLINE = "DECLINE"

MALWARE_POLICY_V033 = "V033_INCOME_AWARE"
MALWARE_POLICY_SIX_PHASE = "SIX_PHASE_BOT_HOOK"


def is_aegis_echo_available(engine: GameEngine, player: PlayerState) -> bool:
    active_ver = engine.state.active_version.version_str
    return has_company_override(player, CompanyCode.AEGIS, legacy_bridge_enabled(engine)) and player.is_ability_available(active_ver)


def aegis_qualifying_colors(
    engine: GameEngine, player: PlayerState, attack_strengths: Dict[CubeColor, int], exited_cubes: Dict[CubeColor, int]
) -> List[CubeColor]:
    """Colors Aegis *Baffle Echo* may ignore this round (empty if the override is not available)."""
    if not is_aegis_echo_available(engine, player):
        return []
    return [
        c for c in (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN)
        if attack_strengths.get(c, 0) > 0 and exited_cubes.get(c, 0) > 0
    ]


def compute_attack_strengths(engine: GameEngine, cr: CompileResult) -> Dict[CubeColor, int]:
    """Attack strengths for Phase 4 (all zeros on Compile Buffer Overflow)."""
    if cr.buffer_overflow:
        return {CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0}
    exited_cubes = cr.exited_cubes
    red_strength = exited_cubes.get(CubeColor.RED, 0)
    blue_strength = exited_cubes.get(CubeColor.BLUE, 0)
    green_strength = exited_cubes.get(CubeColor.GREEN, 0)

    active_directive = engine.state.active_directive_code
    if active_directive == "CORRUPTED_KERNEL" and not engine.state.active_version.corruption_track:
        # Legacy Corrupted Kernel directive without corruption track
        if cr.black_dropped >= engine.config.corrupted_kernel_black_threshold:
            highest_color = max(
                [CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN],
                key=lambda c: (exited_cubes.get(c, 0), c == CubeColor.RED, c == CubeColor.BLUE),
            )
            bonus = engine.config.corrupted_kernel_strength_bonus
            if highest_color == CubeColor.RED:
                red_strength += bonus
            elif highest_color == CubeColor.BLUE:
                blue_strength += bonus
            elif highest_color == CubeColor.GREEN:
                green_strength += bonus

    return {CubeColor.RED: red_strength, CubeColor.BLUE: blue_strength, CubeColor.GREEN: green_strength}


def sync_commitments_with_production(player: PlayerState, rolled_dice: List[Die], commitments: Dict[int, ShieldColor]) -> None:
    """INV-SEQ-COMMIT-SYNC-01: drop every commitment whose die is no longer In Production
    (Burn Notice, Y3, or any other Phase 3 removal)."""
    in_prod_ids = {id(d) for d in player.in_production_dice}
    for idx in list(commitments.keys()):
        if idx >= len(rolled_dice) or id(rolled_dice[idx]) not in in_prod_ids:
            commitments.pop(idx, None)


def _reset_die(d: Die) -> None:
    d.production_role = None
    d.is_locked = False
    d.chosen_choice_index = None
    d.current_face = None


def default_malware_glitch_targets(in_production_dice: List[Die], count: int) -> List[Die]:
    """Six-phase default Green target key (income already collected; only future availability matters):
    White first (free Contractor Sacrifice), then Gray, then cheapest Colored, Purple last."""
    key = lambda d: (  # noqa: E731
        0 if d.color == DieColor.WHITE else 1,
        0 if d.color == DieColor.GRAY else 1,
        1 if d.color == DieColor.PURPLE else 0,
        getattr(d, "cost", 0),
        d.die_id,
    )
    return sorted(in_production_dice, key=key)[: max(0, count)]


def _resolve_green_six_phase(
    engine: GameEngine,
    player: PlayerState,
    unblocked_green: int,
    selector: Optional[MalwareTargetSelector],
) -> None:
    if unblocked_green <= 0 or not player.in_production_dice:
        return  # Green has no effect when In Production is empty (INV-MALWARE-FIZZLE-01)
    prod = list(player.in_production_dice)
    count = min(unblocked_green, len(prod))
    if selector is not None:
        raw = selector(player, list(prod), count)
    elif hasattr(player.bot, "choose_malware_glitch_targets"):
        raw = player.bot.choose_malware_glitch_targets(player, list(prod), count, game_state=engine.state)
    else:
        raw = default_malware_glitch_targets(prod, count)

    chosen: List[Die] = []
    for d in raw or []:
        if len(chosen) >= count:
            break
        if any(d is c for c in chosen) or not any(d is p for p in prod):
            continue
        chosen.append(d)
    if len(chosen) < count:  # Green damage is mandatory: back-fill with the default key
        rest = [d for d in prod if not any(d is c for c in chosen)]
        chosen.extend(default_malware_glitch_targets(rest, count - len(chosen)))

    for target_die in chosen:
        if target_die in player.in_production_dice:
            player.in_production_dice.remove(target_die)
        _reset_die(target_die)
        if target_die.color == DieColor.WHITE:
            # Contractor Sacrifice: White die returns to supply
            if target_die in player.contractor_dice:
                player.contractor_dice.remove(target_die)
            player.hired_contractor_count = len(player.contractor_dice)
            engine.state.contractor_supply += 1
        else:
            player.glitched_dice.append(target_die)


def _pay_defense_l4(engine: GameEngine, player: PlayerState) -> int:
    """v0.35.0 Defense L4: +$1 per Red / Blue / Green Attack Cube blocked this Phase 4 (max $3), paid after
    damage resolution (OQ-9, INV-RT-DEF-L4-01): under RANSOM it cannot fund this round's Red ransom; under
    MARKET_SHARE blocked Red still counts."""
    if player.is_patient_zero:
        return 0
    blocked = (getattr(player, "last_defense_breakdown", None) or {}).get("blocked", {})
    cash = research_tracks.defense_l4_cash(engine.config, player, sum(int(v) for v in blocked.values()))
    if cash > 0:
        player.money += cash
        player.l4_payouts["defense_cash"] = player.l4_payouts.get("defense_cash", 0) + cash
        player.last_defense_breakdown["defense_l4_cash"] = cash
    return cash


def calculate_target_lock_extra_cube(
    engine: GameEngine,
    player: PlayerState,
    exited_cubes: Dict[CubeColor, int],
    attack_strengths: Dict[CubeColor, int],
) -> Optional[CubeColor]:
    """Determines the color of the +1 Target Lock Attack Cube for a locked player."""
    if not getattr(engine.config, "target_lock_enabled", False):
        return None
    if getattr(engine.config, "signature_attack_mode", "v042_plus_one_cube") == "dominant_color_effects":
        return None
    if not player.target_locked or player.is_patient_zero:
        return None

    # Tally exited Attack Cubes (Red, Blue, Green ONLY; Black excluded)
    threat_counts = {
        c: exited_cubes.get(c, 0)
        for c in (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN)
    }
    max_count = max(threat_counts.values(), default=0)

    # INV-TL-02: Zero exited threat cubes -> Target Lock fizzles cleanly
    if max_count <= 0:
        return None

    dominant_colors = [c for c, count in threat_counts.items() if count == max_count]

    # Unique dominant color
    if len(dominant_colors) == 1:
        return dominant_colors[0]

    # INV-TL-01: Dominant color tie resolution: Defending player chooses
    hook = getattr(player.bot, "choose_target_lock_color", None) if player.bot else None
    if callable(hook):
        return hook(
            player=player,
            tied_colors=dominant_colors,
            game_state=engine.state,
            attack=attack_strengths,
        )
    from sim.bots.base import default_target_lock_color_heuristic
    return default_target_lock_color_heuristic(
        player=player,
        tied_colors=dominant_colors,
        state=engine.state,
        attack=attack_strengths,
    )


def resolve_player_defense_and_wear(
    engine: GameEngine,
    player: PlayerState,
    rolled_dice: List[Die],
    commitments: Dict[int, ShieldColor],
    attack_strengths: Dict[CubeColor, int],
    exited_cubes: Dict[CubeColor, int],
    active_directive: str,
    defer_green_malware: bool = False,
    any_shield_allocations: Optional[Dict[CubeColor, int]] = None,
    malware_target_policy: str = MALWARE_POLICY_V033,
    malware_target_selector: Optional[MalwareTargetSelector] = None,
    aegis_color_override: Optional[CubeColor] = None,
    slush_fund_override: Optional[bool] = None,
) -> None:
    """Resolves one player's shields against the attack.

    ``malware_target_policy``: ``"V033_INCOME_AWARE"`` (legacy engine key) or ``"SIX_PHASE_BOT_HOOK"``
    (``malware_target_selector`` or ``bot.choose_malware_glitch_targets``). ``defer_green_malware`` is a
    legacy-only web hook (deprecated v0.34; remove in v0.35). ``aegis_color_override`` lets a web human
    choose the *Baffle Echo* color (``None`` = ask the bot).
    """
    active_ver = engine.state.active_version.version_str
    six_phase = malware_target_policy == MALWARE_POLICY_SIX_PHASE
    if engine.config.is_market_share and engine.state.phase4_snapshot_round != engine.state.current_round:
        # Snapshot once per Phase 4, before any player's Red resolves (bot rival projections)
        engine.state.phase4_snapshot_round = engine.state.current_round
        engine.state.phase4_market_share_start = {p.player_id: p.market_share for p in engine.state.players}

    # 1. Tally committed shields by color and generic ANY
    color_shields: Dict[ShieldColor, int] = {
        ShieldColor.RED: 0,
        ShieldColor.BLUE: 0,
        ShieldColor.GREEN: 0,
        ShieldColor.ANY: 0,
    }
    for idx, color in commitments.items():
        die = rolled_dice[idx]
        face = die.effective_face or die.current_face
        if face and face.is_shield:
            color_shields[color] += face.block_amount

    player_attacks = dict(attack_strengths)
    base_attacks = dict(attack_strengths)

    # Target Lock: Extra Attack Cube calculation (INV-TL-01, INV-TL-02, INV-TL-04)
    target_lock_extra_color = calculate_target_lock_extra_cube(
        engine, player, exited_cubes, attack_strengths
    )
    if target_lock_extra_color is not None:
        bonus = getattr(engine.config, "target_lock_bonus_attack", 1)
        player_attacks[target_lock_extra_color] = player_attacks.get(target_lock_extra_color, 0) + bonus

    # 2. Pre-Defense Overrides: Aegis Defense Relay / Baffle Echo
    is_aegis = has_company_override(player, CompanyCode.AEGIS, legacy_bridge_enabled(engine)) and player.is_ability_available(active_ver)
    if is_aegis:
        qualifying = [
            c for c in [CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN]
            if player_attacks.get(c, 0) > 0 and exited_cubes.get(c, 0) > 0
        ]
        if aegis_color_override is not None and aegis_color_override != AEGIS_DECLINE \
                and aegis_color_override not in qualifying:
            raise ValueError(
                f"Aegis Baffle Echo color {getattr(aegis_color_override, 'value', aegis_color_override)} is not a "
                f"qualifying color this round (qualifying: {[c.value for c in qualifying]})"
            )
        if qualifying and aegis_color_override != AEGIS_DECLINE:
            if aegis_color_override is not None:
                chosen_color = aegis_color_override
            else:
                chosen_color = None
                ms_hook = getattr(player.bot, "choose_aegis_override_market_share", None)
                if engine.config.is_market_share and callable(ms_hook):
                    # v0.36.0: Market Share-aware Baffle Echo valuation (remaining = after color shields)
                    chosen_color = ms_hook(
                        player_state=player,
                        qualifying_colors=qualifying,
                        game_state=engine.state,
                        remaining={
                            c: max(0, player_attacks.get(c, 0) - color_shields[ShieldColor(c.value)])
                            for c in (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN)
                        },
                        attack=dict(player_attacks),
                    )
                if chosen_color is None:
                    chosen_color = player.bot.choose_aegis_override(
                        player_state=player,
                        qualifying_colors=qualifying,
                        exited_cubes=exited_cubes,
                        active_version_str=active_ver,
                        rng=engine.rng,
                        corruption_track=engine.state.corruption_track,
                    )
            if chosen_color in qualifying:
                player_attacks[chosen_color] = max(0, player_attacks[chosen_color] - 1)
                player.mark_ability_used(active_ver)

    # 3. Passive Firewall (Defense Track Level 2)
    firewall_blocked_color: Optional[CubeColor] = None
    if getattr(player, "has_passive_firewall", False):
        candidates = [c for c in [CubeColor.BLUE, CubeColor.RED, CubeColor.GREEN] if player_attacks.get(c, 0) > 0]
        if candidates:
            best_c = max(candidates, key=lambda c: player_attacks.get(c, 0) - color_shields.get(ShieldColor(c.value), 0))
            player_attacks[best_c] = max(0, player_attacks[best_c] - 1)
            firewall_blocked_color = best_c

    # 4. Stage 1: Color-Specific Shield Absorption
    rem_red = max(0, player_attacks[CubeColor.RED] - color_shields[ShieldColor.RED])
    rem_blue = max(0, player_attacks[CubeColor.BLUE] - color_shields[ShieldColor.BLUE])
    rem_green = max(0, player_attacks[CubeColor.GREEN] - color_shields[ShieldColor.GREEN])

    # 5. Stage 2: Reactive Generic "Block 1 Any" Absorption (INV-FLEX-SHIELD-01)
    avail_any = color_shields[ShieldColor.ANY]
    any_allocated: Dict[CubeColor, int] = {
        CubeColor.RED: 0,
        CubeColor.BLUE: 0,
        CubeColor.GREEN: 0,
    }
    if any_shield_allocations is not None and engine.config.any_shield_policy == AnyShieldPolicy.FREE_CHOICE:
        # v0.36.0 human (web) split: legalised like a bot's (clamp + back-fill; every available shield blocks)
        remaining = {CubeColor.RED: rem_red, CubeColor.BLUE: rem_blue, CubeColor.GREEN: rem_green}
        if avail_any > 0 and sum(remaining.values()) > 0:
            alloc = validate_any_shield_allocation(dict(any_shield_allocations), remaining, avail_any)
            for c_color, used in alloc.items():
                any_allocated[c_color] += used
                avail_any -= used
            rem_red -= alloc[CubeColor.RED]
            rem_blue -= alloc[CubeColor.BLUE]
            rem_green -= alloc[CubeColor.GREEN]
    elif any_shield_allocations is not None:
        for c_color in (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN):
            req = max(0, int(any_shield_allocations.get(c_color, 0)))
            if req > 0 and avail_any > 0:
                used = min(avail_any, req)
                avail_any -= used
                any_allocated[c_color] += used
                if c_color == CubeColor.RED:
                    rem_red = max(0, rem_red - used)
                elif c_color == CubeColor.BLUE:
                    rem_blue = max(0, rem_blue - used)
                elif c_color == CubeColor.GREEN:
                    rem_green = max(0, rem_green - used)
    elif engine.config.any_shield_policy == AnyShieldPolicy.FREE_CHOICE:
        # v0.36.0 free choice: the player picks the split; every available shield must block (INV-MS-ANY-SHIELD-01)
        remaining = {CubeColor.RED: rem_red, CubeColor.BLUE: rem_blue, CubeColor.GREEN: rem_green}
        if avail_any > 0 and sum(remaining.values()) > 0:
            hook = getattr(player.bot, "choose_any_shield_allocation", None)
            raw = hook(
                player_state=player, remaining=dict(remaining), available_any=avail_any,
                game_state=engine.state, attack=dict(player_attacks),
            ) if callable(hook) else {}
            fill_order = tuple(getattr(player.bot, "any_shield_fill_order", None)
                               or (CubeColor.BLUE, CubeColor.RED, CubeColor.GREEN))
            alloc = validate_any_shield_allocation(raw or {}, remaining, avail_any, fill_order)
            for c_color, used in alloc.items():
                any_allocated[c_color] += used
                avail_any -= used
            rem_red -= alloc[CubeColor.RED]
            rem_blue -= alloc[CubeColor.BLUE]
            rem_green -= alloc[CubeColor.GREEN]
    else:
        ms_tiers = engine.config.is_market_share
        while avail_any > 0 and (rem_red + rem_blue + rem_green) > 0:
            # Tier 1: Blue Threat (prevent Secret loss)
            if rem_blue > 0:
                rem_blue -= 1
                avail_any -= 1
                any_allocated[CubeColor.BLUE] += 1
            # Tier 2: Red Threat if Cash < Red (prevent Unpaid Ransom Flat Leak);
            # under MARKET_SHARE: this Red would cause Market Collapse
            elif rem_red > 0 and (
                (player.market_share <= rem_red) if ms_tiers
                else (player.money < rem_red * engine.config.red_ransom_per_cube)
            ):
                rem_red -= 1
                avail_any -= 1
                any_allocated[CubeColor.RED] += 1
            # Tier 3: Green Threat (prevent Glitch to in_production_dice)
            elif rem_green > 0:
                rem_green -= 1
                avail_any -= 1
                any_allocated[CubeColor.GREEN] += 1
            # Tier 4: Red Threat if Cash >= Red (save Cash buffer)
            elif rem_red > 0:
                rem_red -= 1
                avail_any -= 1
                any_allocated[CubeColor.RED] += 1
            else:
                break

    unblocked_red = rem_red
    unblocked_blue = rem_blue
    unblocked_green = rem_green

    if target_lock_extra_color is not None:
        bonus = getattr(engine.config, "target_lock_bonus_attack", 1)
        unblocked_map = {
            CubeColor.RED: unblocked_red,
            CubeColor.BLUE: unblocked_blue,
            CubeColor.GREEN: unblocked_green,
        }
        unblocked_color = unblocked_map[target_lock_extra_color]
        base_incoming = base_attacks.get(target_lock_extra_color, 0)
        total_defense = (base_incoming + bonus) - unblocked_color
        unblocked_without_extra = max(0, base_incoming - total_defense)

        if unblocked_color > unblocked_without_extra:
            player.extra_attacks_unblocked += 1
        else:
            player.extra_attacks_absorbed += 1

    # 6. Star face bonuses dependent on damage (R2, R3, B1). The v0.35 R2 / R3 bonuses exist only in the V035
    # Red set (belt-and-braces: the Marketing cards use distinct codes R2_MKT / R3_MKT).
    v035_red = engine.config.red_variant_set == RedVariantSet.V035
    for die in rolled_dice:
        if six_phase and die not in player.in_production_dice:
            continue  # only dice still In Production at Phase 4 (INV-SEQ-COMMIT-SYNC-01)
        face = die.effective_face or die.current_face
        if not face or not face.is_star:
            continue
        if face.star_code == "R2" and v035_red and unblocked_red == 0:
            player.money += 2
        elif face.star_code == "R3" and v035_red and exited_cubes.get(CubeColor.RED, 0) >= 3:
            player.money += 1
        elif face.star_code == "B1" and exited_cubes.get(CubeColor.BLUE, 0) >= 1 and unblocked_blue == 0:
            player.money += 2

    # Red ledgers (both modes; telemetry only)
    player.red_incoming_total += player_attacks[CubeColor.RED]
    player.red_blocked_color_total += min(color_shields[ShieldColor.RED], player_attacks[CubeColor.RED])
    player.red_blocked_any_total += any_allocated[CubeColor.RED]
    player.red_unblocked_total += unblocked_red

    # 7. Red resolution
    unpaid_ransom = 0
    ms_before = player.market_share
    ms_lost = 0
    if engine.config.is_market_share:
        # v0.36.0 Market Manipulation: -1 Market Share per unblocked Red cube; no Money / Secret change
        # (INV-MS-RED-01); no Unpaid Ransom Leak.
        if unblocked_red > 0:
            ms_lost = -player.change_market_share(-unblocked_red, "red")
    elif unblocked_red > 0:
        # v0.35 Red Ransomware Resolution (INV-RANSOM-FLAT-01)
        ransom_due = unblocked_red * engine.config.red_ransom_per_cube
        cash_paid = min(player.money, ransom_due)
        player.money -= cash_paid
        unpaid_ransom = ransom_due - cash_paid

    # Legacy Patch Ransom Absorption Flag (if explicitly enabled in GameConfig)
    if getattr(engine.state.config, "patch_ransom_absorption", False) and unpaid_ransom > 0 and player.patches > 0:
        patch_paid = min(player.patches, unpaid_ransom)
        player.patches -= patch_paid
        unpaid_ransom -= patch_paid

    # Flat Secret Leak: 1 Secret if any shortfall exists, else 0
    ransom_secret_loss = 1 if unpaid_ransom > 0 else 0

    # Phase 60: Version-gated Blue exfiltration damage multiplier (INV-P60-01)
    blue_damage_multiplier = (
        getattr(engine.config, "v3_blue_secret_damage", 2)
        if active_ver == "v3.0"
        else 1
    )
    blue_secret_loss = unblocked_blue * blue_damage_multiplier
    potential_secret_loss = ransom_secret_loss + blue_secret_loss

    # DTO Slush Fund Interaction
    cfg = engine.config
    once_per_game = bool(getattr(cfg, "slush_fund_once_per_game", False))
    is_dto = has_company_override(player, CompanyCode.DTO, legacy_bridge_enabled(engine)) and (
        player.is_slush_fund_available(active_ver) if once_per_game else player.is_ability_available(active_ver)
    )
    if potential_secret_loss > 0 and is_dto and once_per_game:
        # v0.35.0: Slush Fund is once per game and optional when it triggers (OQ-5)
        if slush_fund_override is not None:  # web human accept / decline
            is_dto = bool(slush_fund_override)
        else:
            hook = getattr(player.bot, "choose_slush_fund", None)
            is_dto = bool(hook(player, engine.state, potential_secret_loss)) if hook is not None else True
    if potential_secret_loss > 0 and is_dto:
        if once_per_game:
            player.slush_fund_used_game = True
        free_absorb = min(2, potential_secret_loss)
        potential_secret_loss -= free_absorb
        player.mark_ability_used(active_ver)
        if potential_secret_loss > 0 and player.money > 0:
            cash_absorb = min(player.money, potential_secret_loss)
            player.money -= cash_absorb
            potential_secret_loss -= cash_absorb

    if potential_secret_loss > 0:
        player.gain_secrets(-potential_secret_loss, "blue_damage")

    player.money = max(0, player.money)

    # Patient Zero Check
    if player.secrets <= 0:
        player.is_patient_zero = True
        player.elimination_round = engine.state.current_round
        player.elimination_reason = "Total Breach (<= 0 Secrets)"
        player.breach_depth = max(0, -player.secrets)

    player.last_defense_breakdown = {
        "color_shields": {
            "red": color_shields[ShieldColor.RED],
            "blue": color_shields[ShieldColor.BLUE],
            "green": color_shields[ShieldColor.GREEN],
            "any": color_shields[ShieldColor.ANY],
        },
        "any_allocated": {
            "red": any_allocated[CubeColor.RED],
            "blue": any_allocated[CubeColor.BLUE],
            "green": any_allocated[CubeColor.GREEN],
        },
        "firewall_blocked": firewall_blocked_color.value if firewall_blocked_color else None,
        "effective_attacks": {
            "red": player_attacks[CubeColor.RED],
            "blue": player_attacks[CubeColor.BLUE],
            "green": player_attacks[CubeColor.GREEN],
        },
        "blocked": {
            "red": player_attacks[CubeColor.RED] - unblocked_red,
            "blue": player_attacks[CubeColor.BLUE] - unblocked_blue,
            "green": player_attacks[CubeColor.GREEN] - unblocked_green,
        },
        "unblocked": {
            "red": unblocked_red,
            "blue": unblocked_blue,
            "green": unblocked_green,
        },
        "unpaid_ransom": unpaid_ransom,
        "flat_ransom_leak": bool(unpaid_ransom > 0),
        "ransom_secret_loss": ransom_secret_loss,
        "market_share_before": ms_before,
        "market_share_after": player.market_share,
        "market_share_lost": ms_lost,
        "malware_fizzled": bool(unblocked_green > 0 and len(player.in_production_dice) == 0 and len(player.contractor_dice) == 0),
        "target_lock_extra_color": target_lock_extra_color.value if target_lock_extra_color else None,
        "blue_damage_multiplier": blue_damage_multiplier,
        "blue_secret_loss": blue_secret_loss,
        "potential_secret_loss": potential_secret_loss,
    }
    _record_generic_shield_telemetry(player, player.last_defense_breakdown)

    # v0.38: Blue cubes blocked this round (Baffle Echo-ignored cubes never count; they are not in player_attacks)
    if getattr(engine.config, "secret_face_enabled", False):
        player.blocked_blue_this_round += player_attacks[CubeColor.BLUE] - unblocked_blue

    # 8. Green Malware Resolution (no effect when In Production is empty, INV-MALWARE-FIZZLE-01)
    if six_phase and getattr(engine.config, "glitched_shield_slots_enabled", False):
        # v0.38: each unblocked Green cube glitches 1 shield slot (capped at capacity); no die moves
        from sim.engine import secret_faces

        secret_faces.glitch_slots(player, unblocked_green, "green_cube")
        _pay_defense_l4(engine, player)
        return
    if six_phase:
        # Six-phase: bot/human-chosen targets; never sets pending_unblocked_green (INV-SEQ-NO-SNAPSHOT-01)
        _resolve_green_six_phase(engine, player, unblocked_green, malware_target_selector)
        _pay_defense_l4(engine, player)
        return

    player.pending_unblocked_green = unblocked_green
    if defer_green_malware:
        return

    for _ in range(unblocked_green):
        sacrifice = player.bot.choose_malware_sacrifice(
            player_state=player,
            unblocked_green=unblocked_green,
            rng=engine.rng,
        )
        if sacrifice and len(player.contractor_dice) > 0:
            c_die = player.contractor_dice.pop(0)
            if c_die in player.in_production_dice:
                player.in_production_dice.remove(c_die)
            c_die.production_role = None
            c_die.is_locked = False
            c_die.chosen_choice_index = None
            c_die.current_face = None
            player.hired_contractor_count = len(player.contractor_dice)
            engine.state.contractor_supply += 1
        elif len(player.in_production_dice) > 0:
            def glitch_sort_key(d: Die) -> Tuple[int, int, int, int, int]:
                is_not_white = 0 if d.color == DieColor.WHITE else 1
                role = getattr(d, "production_role", None)
                is_shield = 0 if role in (
                    ProductionRole.RED_SHIELD,
                    ProductionRole.BLUE_SHIELD,
                    ProductionRole.GREEN_SHIELD,
                    ProductionRole.ANY_SHIELD,
                ) else 1
                face = d.effective_face or d.current_face
                has_phase3_output = 1 if (
                    face is not None and (
                        face.money > 0
                        or face.patches > 0
                        or face.secrets > 0
                        or getattr(face, "star_code", None) in ("B3", "R1", "G1", "G2")
                    )
                ) else 0
                is_gray = 0 if d.color in (DieColor.GRAY, DieColor.WHITE) else 1
                return (is_not_white, is_shield, has_phase3_output, is_gray, getattr(d, "cost", 0))

            target_die = min(player.in_production_dice, key=glitch_sort_key)
            player.in_production_dice.remove(target_die)
            target_die.production_role = None
            target_die.is_locked = False
            target_die.chosen_choice_index = None
            target_die.current_face = None
            if target_die.color == DieColor.WHITE:
                if target_die in player.contractor_dice:
                    player.contractor_dice.remove(target_die)
                player.hired_contractor_count = len(player.contractor_dice)
                engine.state.contractor_supply += 1
            else:
                player.glitched_dice.append(target_die)
        else:
            # MALWARE FIZZLE: in_production_dice is empty.
            # ZERO dice destroyed from glitched, scanned, or ready_for_release. Zero penalty!
            break

    player.pending_unblocked_green = 0
    _pay_defense_l4(engine, player)


def apply_snowball_recycle(engine: GameEngine, exited_cubes: Dict[CubeColor, int]) -> None:
    """Snowball Recycle: exited Red, Blue, Green cubes return to the Staging Cup."""
    for color in [CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN]:
        engine.state.staging_cup[color] = engine.state.staging_cup.get(color, 0) + exited_cubes.get(color, 0)


def expire_contractors(engine: GameEngine, skip_pids: AbstractSet[int] = frozenset()) -> None:
    """Contractor Expiration (six-phase: end of Phase 4) for ALL players, Patient Zero included.

    Every White die (by identity) in contractor_dice or any zone returns to supply exactly once,
    so ``contractor_supply`` is conserved (INV-SEQ-CONTRACTOR-EXPIRY-01).
    """
    if not getattr(engine.config, "white_contractor_dice_enabled", True) or engine.config.contractor_supply_total <= 0:
        return
    for player in engine.state.players:
        if player.player_id in skip_pids:
            continue
        whites: Dict[int, Die] = {}
        for d in player.contractor_dice:
            whites[id(d)] = d
        for zone in (
            player.in_production_dice,
            player.ready_for_release_dice,
            player.glitched_dice,
            player.scanned_dice,
        ):
            for d in list(zone):
                if d.color == DieColor.WHITE:
                    whites[id(d)] = d
                    zone.remove(d)
        for d in whites.values():
            _reset_die(d)
        engine.state.contractor_supply += len(whites)
        player.contractor_dice.clear()
        player.hired_contractor_count = 0


DEFAULT_SIGNATURE_TIE_ORDER: Tuple[CubeColor, ...] = (
    CubeColor.GREEN,
    CubeColor.BLACK,
    CubeColor.BLUE,
    CubeColor.RED,
)


def determine_dominant_tray_color(
    exited_cubes: Dict[CubeColor, int],
    tie_order: Tuple[CubeColor, ...] = DEFAULT_SIGNATURE_TIE_ORDER,
) -> Optional[CubeColor]:
    """Evaluates exited cubes across {Red, Blue, Green, Black} and resolves dominant color.

    INV-SIG-01: Preset tie order Green > Black > Blue > Red.
    INV-SIG-02: 0 total compiler cubes -> returns None.
    """
    all_colors = (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN, CubeColor.BLACK)
    counts = {c: int(exited_cubes.get(c, 0)) for c in all_colors}
    max_count = max(counts.values(), default=0)

    if max_count <= 0:
        return None

    for c in tie_order or DEFAULT_SIGNATURE_TIE_ORDER:
        c = c if isinstance(c, CubeColor) else CubeColor(str(c).lower())
        if counts.get(c, 0) == max_count:
            return c
    return None


def _resolve_signature_red(engine: GameEngine, locked_players: List[PlayerState]) -> None:
    """Simultaneous Two-Epoch Market Share Drain & Transfer (INV-SIG-RED, INV-SIMUL-RED)."""
    cfg = engine.config
    state = engine.state
    locked_pids = {p.player_id for p in locked_players}
    drain_amt = cfg.signature_red_drain_amount
    transfer_amt = cfg.signature_red_transfer_amount

    # Epoch 1: Simultaneous Drain
    for p in locked_players:
        if p.market_share is not None:
            before = p.market_share
            p.market_share = max(0, before - drain_amt)
            actual_lost = before - p.market_share
            p.market_share_lost_red += actual_lost
            if p.market_share_min is None or p.market_share < p.market_share_min:
                p.market_share_min = p.market_share
        p.signature_attacks_suffered["red"] = p.signature_attacks_suffered.get("red", 0) + 1

    # Epoch 2: Transfer to Eligible Non-Locked Survivors
    eligible = [
        p for p in state.players
        if not p.is_patient_zero and p.player_id not in locked_pids and p.market_share is not None
    ]
    if not eligible:
        return  # All-locked or solo-survivor edge case: transfer fizzles cleanly

    min_ms = min(p.market_share for p in eligible)
    tied_recipients = [p for p in eligible if p.market_share == min_ms]

    for p in locked_players:
        if len(tied_recipients) == 1:
            chosen = tied_recipients[0]
        else:
            hook = getattr(p.bot, "choose_signature_red_recipient", None) if p.bot else None
            if callable(hook):
                chosen = hook(p, tied_recipients, state)
            else:
                from sim.bots.base import default_signature_red_recipient_heuristic

                chosen = default_signature_red_recipient_heuristic(p, tied_recipients, state)
        max_ms = chosen.max_market_share
        chosen.market_share = min(max_ms, chosen.market_share + transfer_amt)
        if chosen.market_share_peak is None or chosen.market_share > chosen.market_share_peak:
            chosen.market_share_peak = chosen.market_share
        p.signature_red_transfers_sent += transfer_amt
        chosen.signature_red_transfers_received += transfer_amt


def _resolve_signature_blue(engine: GameEngine, player: PlayerState) -> None:
    """Move 1 Gray die to back of Processing Box; yields 0 Secrets (INV-SIG-BLUE)."""
    source_die = None
    source_list = None

    for candidate_list in (player.scanned_dice, player.in_production_dice, player.ready_for_release_dice):
        grays = [d for d in candidate_list if d.color == DieColor.GRAY]
        if grays:
            source_die = grays[0]
            source_list = candidate_list
            break

    if source_die is not None and source_list is not None:
        source_list.remove(source_die)
        _reset_die(source_die)
        source_die.secret_pending = False
        player.processing_entry_counter += 1
        source_die.processing_entry_seq = player.processing_entry_counter
        player.glitched_dice.append(source_die)


def _resolve_signature_green(engine: GameEngine, player: PlayerState) -> None:
    """Place green cubes on next space of 2 eligible tracks (INV-SIG-GREEN, INV-GREEN-OVERFLOW)."""
    all_tracks = ("DEFENSE", "TRIAGE", "RELEASE", "PR")
    eligible = [
        t for t in all_tracks
        if research_tracks.level_of(player, t) < 4 and not research_tracks.is_track_encrypted(player, t)
    ]

    cfg = engine.config
    count_to_place = cfg.signature_green_cube_count

    if len(eligible) > count_to_place:
        hook = getattr(player.bot, "choose_signature_green_tracks", None) if player.bot else None
        if callable(hook):
            chosen = hook(player, eligible, count_to_place, engine.state)
        else:
            from sim.bots.base import default_signature_green_tracks_heuristic

            chosen = default_signature_green_tracks_heuristic(player, eligible, count_to_place, engine.state)
        # Bot picks first (filtered to eligible), topped up from eligible order.
        placed = list(dict.fromkeys([t for t in chosen or [] if t in eligible] + eligible))[:count_to_place]
    else:
        placed = list(eligible[:count_to_place])

    for t in placed:
        player.encrypted_research_tracks.add(t)

    shortfall = max(0, count_to_place - len(placed))
    if shortfall > 0:
        before_slots = player.glitched_shield_slots
        player.glitched_shield_slots = min(player.defense_capacity, player.glitched_shield_slots + shortfall)
        added_slots = player.glitched_shield_slots - before_slots
        if added_slots > 0:
            player.slots_glitched_this_round += added_slots
            player.slots_glitched_by_source["signature_green"] = (
                player.slots_glitched_by_source.get("signature_green", 0) + added_slots
            )
            player.max_glitched_slots = max(player.max_glitched_slots, player.glitched_shield_slots)


def _resolve_signature_black(engine: GameEngine, player: PlayerState) -> None:
    """Burn Institutional Override or lose 2 Corporate Secrets (INV-SIG-BLACK)."""
    active_ver = engine.state.active_version.version_str if (engine.state and engine.state.version_deck) else "v1.0"
    is_dto = (
        has_company_override(player, CompanyCode.DTO, legacy_bridge_enabled(engine))
        or getattr(getattr(player, "company", None), "code", None) == CompanyCode.DTO
    )
    override_available = (
        player.is_ability_available(active_ver)
        and not player.company_ability_used_this_version
        and (not is_dto or not player.dto_slush_fund_used)
    )

    if override_available:
        player.mark_ability_used(active_ver)
        if is_dto:
            player.dto_slush_fund_used = True
        player.signature_override_hijacks += 1
    else:
        loss = int(getattr(engine.config, "signature_black_secret_loss", 2))
        actual_loss = min(max(0, player.secrets), loss)
        player.secrets = max(0, player.secrets - loss)
        if actual_loss > 0:
            player.secrets_by_source["signature_black"] = (
                player.secrets_by_source.get("signature_black", 0) - actual_loss
            )
        player.signature_black_secrets_lost += loss


def resolve_signature_attacks(engine: GameEngine, cr: CompileResult) -> None:
    """Resolves Dominant Cube Color Signature Attacks in Phase 4 after base shields (INV-SIG-01..03)."""
    cfg = engine.config
    state = engine.state
    if cr.buffer_overflow:
        state.last_dominant_color = None
        return

    dominant_color = determine_dominant_tray_color(cr.exited_cubes, cfg.signature_attack_tie_order)
    state.last_dominant_color = dominant_color

    if dominant_color is None:
        return  # INV-SIG-02: Clean tray fizzle

    state.dominant_color_counts[dominant_color.value] = state.dominant_color_counts.get(dominant_color.value, 0) + 1

    locked_players = [
        p for p in state.players
        if p.target_locked and not p.is_patient_zero and p.player_id not in getattr(cr, "breached_pids", set())
    ]
    if not locked_players:
        return

    if dominant_color == CubeColor.RED:
        _resolve_signature_red(engine, locked_players)
    else:
        for p in locked_players:
            if dominant_color == CubeColor.BLUE:
                _resolve_signature_blue(engine, p)
            elif dominant_color == CubeColor.GREEN:
                _resolve_signature_green(engine, p)
            elif dominant_color == CubeColor.BLACK:
                _resolve_signature_black(engine, p)
            p.signature_attacks_suffered[dominant_color.value] = (
                p.signature_attacks_suffered.get(dominant_color.value, 0) + 1
            )

    state.signature_attack_events.append({
        "round": state.current_round,
        "dominant_color": dominant_color.value,
        "locked_pids": [p.player_id for p in locked_players],
    })


def check_end_triggers_after_attacks(engine: GameEngine) -> None:
    """End-of-Phase-4 trigger check (spec §4.2). Never sets Singularity.

    v0.36.0: Market Collapse is checked after Patient Zero / Total Wipeout (INV-MS-COLLAPSE-PREC-01).
    """
    state = engine.state
    for p in state.players:
        if p.secrets <= 0 and not p.is_patient_zero:
            p.is_patient_zero = True
            p.elimination_round = state.current_round
            p.elimination_reason = "Total Breach (<= 0 Secrets)"
            p.breach_depth = max(0, -p.secrets)
    if all(p.is_patient_zero for p in state.players):
        state.game_over = True
        state.is_final_round = False
        state.end_reason = EndGameReason.TOTAL_WIPEOUT
        market_share.add_end_trigger(state, "patient_zero")
        market_share.add_end_trigger(state, "total_wipeout")
    elif any(p.is_patient_zero for p in state.players):
        market_share.add_end_trigger(state, "patient_zero")
        state.is_final_round = True
        if state.end_reason == EndGameReason.NONE:
            state.end_reason = EndGameReason.PATIENT_ZERO
        if state.final_round_trigger_phase is None:
            state.final_round_trigger_phase = 4
    market_share.check_market_collapse(engine)


def validate_any_shield_allocation(
    raw: Dict[CubeColor, int],
    remaining: Dict[CubeColor, int],
    available_any: int,
    fill_order: Tuple[CubeColor, ...] = (CubeColor.BLUE, CubeColor.RED, CubeColor.GREEN),
) -> Dict[CubeColor, int]:
    """Legalises a free-choice Generic shield split (INV-MS-ANY-SHIELD-01, E25).

    Clamp each color to [0, remaining]; trim to ``available_any`` in Blue, Red, Green order; then back-fill in
    ``fill_order`` until ``min(available_any, sum(remaining))`` shields are used (every available Generic shield
    must block while unblocked cubes remain; the player chooses only the split).
    """
    colors = (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN)
    alloc = {c: max(0, min(int(remaining.get(c, 0)), int((raw or {}).get(c, 0) or 0))) for c in colors}
    budget = max(0, int(available_any))
    for c in (CubeColor.BLUE, CubeColor.RED, CubeColor.GREEN):
        alloc[c] = min(alloc[c], budget)
        budget -= alloc[c]
    target = min(max(0, int(available_any)), sum(max(0, int(remaining.get(c, 0))) for c in colors))
    short = target - sum(alloc.values())
    for c in tuple(fill_order) + colors:
        if short <= 0:
            break
        add = min(short, int(remaining.get(c, 0)) - alloc[c])
        if add > 0:
            alloc[c] += add
            short -= add
    return alloc


def execute_attack_resolution(
    engine: GameEngine,
    player_commitments: Commitments,
    cr: CompileResult,
    any_shield_allocations_by_pid: Optional[Dict[int, Dict[CubeColor, int]]] = None,
    malware_selectors_by_pid: Optional[Dict[int, MalwareTargetSelector]] = None,
    aegis_colors_by_pid: Optional[Dict[int, CubeColor]] = None,
    resolve_damage: bool = True,
    finalize: bool = True,
) -> Dict[CubeColor, int]:
    """Phase 4 for every survivor: damage -> Signature Attacks -> Snowball Recycle -> Contractor Expiration -> end check.

    ``resolve_damage=False`` / ``finalize=False`` let the web controller split per-player damage
    from the closing steps.
    """
    attack = compute_attack_strengths(engine, cr)
    if resolve_damage and not cr.buffer_overflow:
        active_directive = engine.state.active_directive_code
        for player, rolled_dice, commitments in player_commitments:
            if player.is_patient_zero or player.player_id in cr.breached_pids:
                continue  # INV-SEQ-PZ-SKIP-01
            resolve_player_attack(
                engine,
                player,
                rolled_dice,
                commitments,
                attack,
                cr,
                active_directive=active_directive,
                any_shield_allocations=(any_shield_allocations_by_pid or {}).get(player.player_id),
                malware_target_selector=(malware_selectors_by_pid or {}).get(player.player_id),
                aegis_color_override=(aegis_colors_by_pid or {}).get(player.player_id),
            )

        # Phase 62: Dominant Cube Color Signature Attacks (INV-SIG-03)
        if getattr(engine.config, "signature_attack_mode", "none") == "dominant_color_effects":
            resolve_signature_attacks(engine, cr)
    elif resolve_damage and cr.buffer_overflow:
        if getattr(engine.config, "signature_attack_mode", "none") == "dominant_color_effects":
            engine.state.last_dominant_color = None
    if finalize:
        finalize_attack_resolution(engine, cr)
    return attack


def resolve_player_attack(
    engine: GameEngine,
    player: PlayerState,
    rolled_dice: List[Die],
    commitments: Dict[int, ShieldColor],
    attack: Dict[CubeColor, int],
    cr: CompileResult,
    *,
    active_directive: Optional[str] = None,
    any_shield_allocations: Optional[Dict[CubeColor, int]] = None,
    malware_target_selector: Optional[MalwareTargetSelector] = None,
    aegis_color_override: Optional[CubeColor] = None,
    slush_fund_override: Optional[bool] = None,
) -> None:
    """One survivor's Phase 4 damage (six-phase policy)."""
    sync_commitments_with_production(player, rolled_dice, commitments)
    resolve_player_defense_and_wear(
        engine=engine,
        player=player,
        rolled_dice=rolled_dice,
        commitments=commitments,
        attack_strengths=attack,
        exited_cubes=cr.exited_cubes,
        active_directive=active_directive or engine.state.active_directive_code,
        any_shield_allocations=any_shield_allocations,
        malware_target_policy=MALWARE_POLICY_SIX_PHASE,
        malware_target_selector=malware_target_selector,
        aegis_color_override=aegis_color_override,
        slush_fund_override=slush_fund_override,
    )


def finalize_attack_resolution(engine: GameEngine, cr: CompileResult) -> None:
    """Closing steps of Phase 4: Snowball Recycle, Contractor Expiration, End Game Trigger check."""
    apply_snowball_recycle(engine, cr.exited_cubes)
    expire_contractors(engine)
    check_end_triggers_after_attacks(engine)
    for p in engine.state.players:
        p.target_locked = False


def _record_generic_shield_telemetry(player, b) -> None:
    """v0.37.0 Generic shield / contested-round counters (spec §4.4). Telemetry only: nothing reads them in play."""
    cs = b["color_shields"]
    any_n = cs["any"]
    for c in ("red", "blue", "green"):
        player.any_shield_allocated_by_color[c] += b["any_allocated"][c]
    rem = {c: max(0, b["effective_attacks"][c] - cs[c]) for c in ("red", "blue", "green")}
    if any_n > 0 and rem["blue"] > 0 and rem["red"] > 0 and rem["blue"] + rem["red"] + rem["green"] > any_n:
        player.contested_defense_rounds += 1
        if b["any_allocated"]["blue"] < min(rem["blue"], any_n):
            player.contested_blue_left_open += 1
        if b["any_allocated"]["red"] > 0:
            player.contested_red_chosen += 1
