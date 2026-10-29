from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from sim.bots import (
    AccelerationistBot,
    AdaptiveBalancedBot,
    BaseBot,
    Phase3ActionPlan,
    RecklessSaboteurBot,
    SecOpsTurtleBot,
    VentureGreedBot,
)
from sim.config import CubeColor, DieColor, EndGameReason, GameConfig, ShieldColor
from sim.engine import EndGameResult, GameEngine, GameState, PlayerState
from sim.entities import (
    AbilityStatus,
    ArchetypeCard,
    ArchetypeCode,
    Die,
    VariantCard,
    VersionCard,
    create_colored_die,
    create_white_die,
)

if TYPE_CHECKING:
    from web.controller.core import GameController


def advance_phase3_turns(controller: GameController) -> None:
    """Processes Phase 3 turns clockwise, automatically executing bots until a human turn or round end."""
    while controller.phase3_turn_queue:
        next_pid = controller.phase3_turn_queue[0]
        player = controller.state.players[next_pid]
        meta = controller.player_meta[next_pid]

        # Skip eliminated players
        if player.is_patient_zero:
            controller.phase3_turn_queue.pop(0)
            controller.event_log.append(f"{meta['name']} is Patient Zero (eliminated, skipping Phase 3).")
            continue

        # If human player's turn: stop and wait for interactive actions
        if meta["is_human"]:
            controller.active_player_index = next_pid
            meta["purchases_this_turn"] = 0
            meta["dirty_income_taken_this_turn"] = False
            return

        # Bot player turn: execute automatically
        controller.active_player_index = next_pid
        controller.phase3_turn_queue.pop(0)
        execute_bot_phase3(controller, player, meta)

    # All players have finished Phase 3 -> complete round cleanup
    controller._complete_round()



def execute_bot_phase3(controller: GameController, player: PlayerState, meta: Dict[str, Any]) -> None:
    """Executes Phase 3 plan for a single bot player."""
    plan: Phase3ActionPlan = player.bot.take_phase3_actions(player, controller.state, controller.engine.rng)

    # Archetype: The Phreaker (Magnetic Splice)
    if (
        plan.use_phreaker_ability
        and player.archetype is not None
        and player.archetype.code == ArchetypeCode.PHREAKER
        and player.is_ability_available()
        and player.unpatched_dice
    ):
        repair_count = min(1, len(player.unpatched_dice))
        for _ in range(repair_count):
            best_idx = max(
                range(len(player.unpatched_dice)),
                key=lambda i: (
                    1 if player.unpatched_dice[i].color != DieColor.GRAY else 0,
                    getattr(player.unpatched_dice[i], "vp", 0),
                    getattr(player.unpatched_dice[i], "cost", 0),
                ),
            )
            repaired = player.unpatched_dice.pop(best_idx)
            player.ready_dice.append(repaired)
            meta["rolled_pool"] = [
                d for d in meta.get("rolled_pool", []) if d.die_id != repaired.die_id
            ]
        player.mark_ability_used()
        controller.event_log.append(
            f"{meta['name']} (Bot) used Phreaker Magnetic Splice: repaired {repair_count} die for free."
        )

    # Archetype: The Cipher (Algorithmic Arbitrage)
    cipher_used = False
    if (
        plan.use_cipher_ability
        and player.archetype is not None
        and player.archetype.code == ArchetypeCode.CIPHER
        and player.is_ability_available()
    ):
        if plan.cipher_mode in ("BUY_FREE_DIE", 1) and plan.cipher_free_die_color is not None:
            free_color = plan.cipher_free_die_color
            normal_cost = 4 if free_color in (DieColor.RED, DieColor.GREEN, DieColor.PURPLE) else 5
            discounted_cost = max(0, normal_cost - controller.state.config.cipher_market_discount)
            if controller.state.market.get(free_color, 0) > 0 and player.money >= discounted_cost:
                player.money -= discounted_cost
                controller.state.market[free_color] -= 1
                meta["purchases_this_turn"] += 1
                new_die = create_colored_die(
                    color=free_color,
                    die_id=controller.state.next_die_id,
                    variant_card=controller.state.variant_cards.get(free_color),
                )
                controller.state.next_die_id += 1
                player.ready_dice.append(new_die)
                player.mark_ability_used()
                cipher_used = True
                controller.event_log.append(
                    f"{meta['name']} (Bot) used Cipher Algorithmic Arbitrage: {free_color.value.capitalize()} Die at ${discounted_cost}."
                )
        elif plan.cipher_mode in ("DIRTY_INCOME", 2):
            if player.secrets > controller.state.config.dirty_income_secret_cost:
                player.secrets -= controller.state.config.dirty_income_secret_cost
                player.money += controller.state.config.dirty_income_cash
                controller.state.staging_cup[CubeColor.BLACK] = (
                    controller.state.staging_cup.get(CubeColor.BLACK, 0)
                    + controller.state.config.dirty_income_black_cubes
                )
                player.total_dirty_income_taken += 1
                player.mark_ability_used()
                cipher_used = True
                controller.event_log.append(
                    f"{meta['name']} (Bot) used Cipher Algorithmic Arbitrage: Backlash-free Dirty Income."
                )

    # 1. Dirty Income
    if (
        not (cipher_used and plan.cipher_mode in ("DIRTY_INCOME", 2))
        and plan.take_dirty_income
        and player.secrets > controller.state.config.dirty_income_secret_cost
        and len(player.ready_dice) >= 1
    ):
        player.secrets -= controller.state.config.dirty_income_secret_cost
        player.money += controller.state.config.dirty_income_cash
        controller.state.staging_cup[CubeColor.BLACK] = (
            controller.state.staging_cup.get(CubeColor.BLACK, 0)
            + controller.state.config.dirty_income_black_cubes
        )
        backlash_idx = plan.dirty_income_backlash_die_index
        if not (0 <= backlash_idx < len(player.ready_dice)):
            backlash_idx = 0
        demoted = player.ready_dice.pop(backlash_idx)
        player.unpatched_dice.append(demoted)
        meta["rolled_pool"] = [
            d for d in meta.get("rolled_pool", []) if d.die_id != demoted.die_id
        ]
        player.total_dirty_income_taken += 1
        controller.event_log.append(f"{meta['name']} (Bot) took Dirty Income: +$3, -1 Secret, +1 Black Cube.")

    # 2. Star Special Actions
    if plan.use_b2_secret and player.b2_available:
        cost = controller.state.config.b2_secret_cost
        cap = controller.state.config.b2_secret_cap
        if player.money >= cost and player.secrets < cap:
            player.money -= cost
            player.secrets = min(cap, player.secrets + 1)
            player.b2_available = False
            controller.event_log.append(f"{meta['name']} (Bot) used B2 Deep R&D: +1 Secret for ${cost}.")

    if plan.use_y1_secret and player.y1_available:
        if player.money >= 6 and player.secrets < 10:
            player.money -= 6
            player.secrets = min(10, player.secrets + 1)
            player.y1_available = False
            controller.event_log.append(f"{meta['name']} (Bot) used Y1 Algorithmic Trading: +1 Secret for $6.")

    if plan.p1_cube_choice in (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN) and player.p1_available:
        controller.state.staging_cup[plan.p1_cube_choice] = controller.state.staging_cup.get(plan.p1_cube_choice, 0) + 1
        player.p1_available = False

    if plan.p3_cube_choice in (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN) and player.p3_available:
        if plan.p3_cube_choice.value == player.p3_available.value:
            p3_cost = controller.state.config.p3_cube_cash_cost
            if player.money >= p3_cost:
                player.money -= p3_cost
                controller.state.staging_cup[plan.p3_cube_choice] = controller.state.staging_cup.get(plan.p3_cube_choice, 0) + 1
                player.p3_available = None

    # 3. Patching
    patch_cash_cost = controller.state.config.patch_cash_cost
    for patch_act in plan.patch_actions:
        if not player.unpatched_dice:
            break
        idx = patch_act.get("die_index", 0)
        if not isinstance(idx, int) or not (0 <= idx < len(player.unpatched_dice)):
            idx = 0
        use_cash = bool(patch_act.get("use_cash", False))

        if use_cash:
            if player.money >= patch_cash_cost:
                player.money -= patch_cash_cost
                patched = player.unpatched_dice.pop(idx)
                player.ready_dice.append(patched)
        else:
            if player.patches >= controller.state.config.patch_token_cost:
                player.patches -= controller.state.config.patch_token_cost
                patched = player.unpatched_dice.pop(idx)
                player.ready_dice.append(patched)

    # 4. Market Purchases
    purchases = 0
    for color in plan.market_purchases:
        if purchases >= controller.state.config.max_market_purchases_per_turn:
            break
        cost = 4 if color in (DieColor.RED, DieColor.GREEN, DieColor.PURPLE) else 5
        if controller.state.market.get(color, 0) > 0 and player.money >= cost:
            player.money -= cost
            controller.state.market[color] -= 1
            purchases += 1
            new_die = create_colored_die(
                color=color,
                die_id=controller.state.next_die_id,
                variant_card=controller.state.variant_cards.get(color),
            )
            controller.state.next_die_id += 1
            player.ready_dice.append(new_die)
            controller.event_log.append(f"{meta['name']} (Bot) bought {color.value.capitalize()} Die.")

    player.patches = min(player.patches, controller.state.config.max_patch_tokens)



def buy_die(
    controller: GameController,
    player_id: int,
    color_str: str,
    use_cipher_ability: bool = False,
) -> Dict[str, Any]:
    if player_id != controller.active_player_index:
        raise ValueError(f"Not player {player_id}'s turn (current: {controller.active_player_index})")

    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]

    if player.is_patient_zero:
        raise ValueError("Eliminated players cannot perform operations")
    if meta["purchases_this_turn"] >= controller.state.config.max_market_purchases_per_turn:
        raise ValueError(f"Purchase limit reached ({controller.state.config.max_market_purchases_per_turn} dice per turn)")

    color = DieColor(color_str.lower())
    cost = 4 if color in (DieColor.RED, DieColor.GREEN, DieColor.PURPLE) else 5

    if use_cipher_ability:
        if not player.archetype or player.archetype.code != ArchetypeCode.CIPHER:
            raise ValueError("Player does not have the Cipher archetype")
        if not player.is_ability_available():
            raise ValueError("Cipher ability is not available")
        cost = max(0, cost - controller.state.config.cipher_market_discount)

    if controller.state.market.get(color, 0) <= 0:
        raise ValueError(f"Market stock for {color.value} is depleted")
    if player.money < cost:
        raise ValueError(f"Insufficient funds: die costs ${cost}, but player only has ${player.money}")

    player.money -= cost
    controller.state.market[color] -= 1
    meta["purchases_this_turn"] += 1

    new_die = create_colored_die(
        color=color,
        die_id=controller.state.next_die_id,
        variant_card=controller.state.variant_cards.get(color),
    )
    controller.state.next_die_id += 1
    player.ready_dice.append(new_die)

    if use_cipher_ability:
        player.mark_ability_used()
        controller.event_log.append(
            f"{meta['name']} used Cipher Algorithmic Arbitrage to acquire a {color.value.capitalize()} Die at a ${controller.state.config.cipher_market_discount} discount (${cost})! (Stock remaining: {controller.state.market[color]})."
        )
    else:
        controller.event_log.append(
            f"{meta['name']} purchased a {color.value.capitalize()} Die for ${cost}. (Stock remaining: {controller.state.market[color]})."
        )
    return controller.get_full_state()



def patch_die(controller: GameController, player_id: int, die_index: int, use_cash: bool) -> Dict[str, Any]:
    """Human action: patches an unpatched die back to the ready zone."""
    if controller.phase != 3:
        raise ValueError(f"Cannot patch dice in phase {controller.phase}")
    if player_id != controller.active_player_index:
        raise ValueError(f"Not player {player_id}'s turn (current: {controller.active_player_index})")

    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]

    if player.is_patient_zero:
        raise ValueError("Eliminated players cannot perform operations")
    if not (0 <= die_index < len(player.unpatched_dice)):
        raise ValueError(f"Invalid die_index {die_index} in unpatched zone (size: {len(player.unpatched_dice)})")

    patch_cash_cost = controller.state.config.patch_cash_cost

    if use_cash:
        if player.money < patch_cash_cost:
            raise ValueError(f"Insufficient cash for patching: costs ${patch_cash_cost}, player has ${player.money}")
        player.money -= patch_cash_cost
        cost_desc = f"${patch_cash_cost} cash"
    else:
        if player.patches < controller.state.config.patch_token_cost:
            raise ValueError(f"Insufficient patch tokens: costs {controller.state.config.patch_token_cost} 🔧, player has {player.patches} 🔧")
        player.patches -= controller.state.config.patch_token_cost
        cost_desc = "1 🔧 token"

    patched_die = player.unpatched_dice.pop(die_index)
    player.ready_dice.append(patched_die)
    meta["rolled_pool"] = [
        d for d in meta.get("rolled_pool", []) if d.die_id != patched_die.die_id
    ]

    controller.event_log.append(
        f"{meta['name']} patched {patched_die.color.value.capitalize()} Die using {cost_desc}."
    )
    return controller.get_full_state()



def take_dirty_income(
    controller: GameController,
    player_id: int,
    backlash_die_index: int = 0,
    use_cipher_ability: bool = False,
    backlash_die_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Human action: corrupts the Rogue Agent ('Dirty Income') for quick cash (or backlash-free via Cipher)."""
    if controller.phase != 3:
        raise ValueError(f"Cannot take dirty income in phase {controller.phase}")
    if player_id != controller.active_player_index:
        raise ValueError(f"Not player {player_id}'s turn (current: {controller.active_player_index})")

    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]

    if player.is_patient_zero:
        raise ValueError("Eliminated players cannot perform operations")
    if meta["dirty_income_taken_this_turn"]:
        raise ValueError("Dirty Income has already been taken this turn (limit 1x per turn)")

    if use_cipher_ability:
        if not player.archetype or player.archetype.code != ArchetypeCode.CIPHER:
            raise ValueError("Player does not have the Cipher archetype")
        if not player.is_ability_available():
            raise ValueError("Cipher ability is not available")

    # Precondition checks per RULES.md Section 4 Phase 3 Step 3:
    # Must have strictly > 1 secret (cannot be taken at <= 1 secret)
    if player.secrets <= controller.state.config.dirty_income_secret_cost:
        raise ValueError(
            f"Cannot take Dirty Income with {player.secrets} Secret(s) (must have strictly > {controller.state.config.dirty_income_secret_cost})"
        )
    if not use_cipher_ability and len(player.ready_dice) < 1:
        raise ValueError("Cannot take Dirty Income: must have at least 1 Ready die for Technical Debt Backlash")

    backlash_die: Optional[Die] = None
    if not use_cipher_ability:
        if backlash_die_id is not None:
            for d in player.ready_dice:
                if d.die_id == backlash_die_id:
                    backlash_die = d
                    break
            if backlash_die is None:
                raise ValueError(f"Die with die_id {backlash_die_id} is not in player's ready pool")
        else:
            if not (0 <= backlash_die_index < len(player.ready_dice)):
                backlash_die_index = 0
            backlash_die = player.ready_dice[backlash_die_index]

    # Execute Dirty Income
    player.secrets -= controller.state.config.dirty_income_secret_cost
    player.money += controller.state.config.dirty_income_cash
    controller.state.staging_cup[CubeColor.BLACK] = (
        controller.state.staging_cup.get(CubeColor.BLACK, 0)
        + controller.state.config.dirty_income_black_cubes
    )

    if use_cipher_ability:
        player.mark_ability_used()
        meta["dirty_income_taken_this_turn"] = True
        player.total_dirty_income_taken += 1
        controller.event_log.append(
            f"{meta['name']} used Cipher Algorithmic Arbitrage: gained +${controller.state.config.dirty_income_cash}, paid 1 Secret, added 1 Black Cube to Staging Cup without Backlash."
        )
        return controller.get_full_state()

    # Technical Debt Backlash: demote chosen ready die to unpatched
    assert backlash_die is not None
    player.ready_dice.remove(backlash_die)
    player.unpatched_dice.append(backlash_die)
    meta["rolled_pool"] = [
        d for d in meta.get("rolled_pool", []) if d.die_id != backlash_die.die_id
    ]

    meta["dirty_income_taken_this_turn"] = True
    player.total_dirty_income_taken += 1

    controller.event_log.append(
        f"{meta['name']} took Dirty Income: gained +${controller.state.config.dirty_income_cash}, paid 1 Secret, added 1 Black Cube to Staging Cup. Backlash demoted {backlash_die.color.value.capitalize()} Die."
    )
    return controller.get_full_state()



def use_phreaker_ability(
    controller: GameController,
    player_id: int,
    count: int = 1,
    die_index: int = 0,
    die_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Human action: repairs 1 unpatched die for free using Phreaker Magnetic Splice (v0.13.0)."""
    if controller.phase != 3:
        raise ValueError(f"Cannot use Phreaker ability in phase {controller.phase}")
    if player_id != controller.active_player_index:
        raise ValueError(f"Not player {player_id}'s turn (current: {controller.active_player_index})")

    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]
    active_ver = controller.state.active_version.version_str if (controller.state and controller.state.active_version) else None

    if player.is_patient_zero:
        raise ValueError("Eliminated players cannot perform operations")
    if not player.archetype or player.archetype.code != ArchetypeCode.PHREAKER:
        raise ValueError("Player does not have the Phreaker archetype")
    if not player.is_ability_available(active_ver):
        raise ValueError("Phreaker ability is not available")
    if count < 1:
        raise ValueError("count must be at least 1")
    if not player.unpatched_dice:
        raise ValueError("No unpatched dice available to repair")

    repaired: Optional[Die] = None
    if die_id is not None:
        for d in player.unpatched_dice:
            if d.die_id == die_id:
                repaired = d
                break
        if repaired is None:
            raise ValueError(f"Die with die_id {die_id} is not in unpatched zone")
        player.unpatched_dice.remove(repaired)
    else:
        if not (0 <= die_index < len(player.unpatched_dice)):
            raise ValueError(f"Invalid die_index {die_index} in unpatched zone")
        repaired = player.unpatched_dice.pop(die_index)

    player.ready_dice.append(repaired)
    meta["rolled_pool"] = [
        d for d in meta.get("rolled_pool", []) if d.die_id != repaired.die_id
    ]

    player.mark_ability_used(active_ver)
    controller.event_log.append(
        f"{meta['name']} activated Phreaker Magnetic Splice: repaired {repaired.color.value.capitalize()} Die for free."
    )
    return controller.get_full_state()



def use_acoustic_ability(controller: GameController, player_id: int, chosen_color_str: str) -> Dict[str, Any]:
    """Human action: activates Acoustic Baffle Echo to remove 1 exited attack cube."""
    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]

    if player.is_patient_zero:
        raise ValueError("Eliminated players cannot use abilities")
    if not player.archetype or player.archetype.code != ArchetypeCode.ACOUSTIC:
        raise ValueError("Player does not have the Acoustic archetype")
    if not player.is_ability_available():
        raise ValueError("Acoustic ability is not available")

    chosen_color = CubeColor(chosen_color_str.lower())
    if chosen_color not in (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN):
        raise ValueError(f"Invalid attack cube color: {chosen_color_str}")

    if not controller.last_compile_result:
        raise ValueError("No compile drop has occurred yet")

    exited = controller.last_compile_result.get("exited_cubes", {})
    if exited.get(chosen_color.value, 0) <= 0:
        raise ValueError(f"No {chosen_color.value} cubes exited in the last compile drop")

    # In v0.13.0: Exited cubes remain in tray and recycle as normal.
    # Player ignores 1 cube of that color (mitigates damage for self)
    if chosen_color == CubeColor.BLUE:
        player.secrets = min(10, player.secrets + 1)
    elif chosen_color == CubeColor.RED:
        player.money += 1
    elif chosen_color == CubeColor.GREEN and player.unpatched_dice:
        restored = player.unpatched_dice.pop()
        player.ready_dice.append(restored)

    player.mark_ability_used()
    controller.event_log.append(
        f"{meta['name']} activated Acoustic Baffle Echo: ignored 1 {chosen_color.value} cube for self."
    )
    return controller.get_full_state()



def use_spook_ability(controller: GameController, player_id: int, dollars: int = 0) -> Dict[str, Any]:
    """Human action: activates Spook Slush Fund (v0.13.0: absorbs up to 2 secrets free + optional cash)."""
    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]

    if player.is_patient_zero:
        raise ValueError("Eliminated players cannot use abilities")
    if not player.archetype or player.archetype.code != ArchetypeCode.SPOOK:
        raise ValueError("Player does not have the Spook archetype")
    if not player.is_ability_available():
        raise ValueError("Spook ability is not available")
    if dollars < 0:
        raise ValueError("dollars must be non-negative")

    # In v0.13.0: Absorb up to 2 secrets free, plus optional extra for $1 each
    free_secrets = 2
    cash_spent = max(0, min(dollars, player.money))
    player.money -= cash_spent
    total_secrets_absorbed = free_secrets + cash_spent
    player.secrets = min(10, player.secrets + total_secrets_absorbed)
    player.mark_ability_used()
    controller.event_log.append(
        f"{meta['name']} activated Spook Slush Fund: absorbed {total_secrets_absorbed} secrets ({free_secrets} free, ${cash_spent} cash)."
    )
    return controller.get_full_state()



def execute_star_action(
    controller: GameController,
    player_id: int,
    action_type: str,
    cube_color: Optional[str] = None,
) -> Dict[str, Any]:
    """Human action: executes rolled Star ability during Phase 3."""
    if controller.phase != 3:
        raise ValueError(f"Cannot execute star actions in phase {controller.phase}")
    if player_id != controller.active_player_index:
        raise ValueError(f"Not player {player_id}'s turn")

    player = controller.state.players[player_id]
    meta = controller.player_meta[player_id]

    if action_type == "B2":
        if not player.b2_available:
            raise ValueError("B2 Deep R&D Vault ability is not available this turn")
        cost = controller.state.config.b2_secret_cost
        cap = controller.state.config.b2_secret_cap
        if player.money < cost:
            raise ValueError(f"B2 requires ${cost} cash")
        if player.secrets >= cap:
            raise ValueError(f"Secrets already at maximum capacity ({cap})")
        player.money -= cost
        player.secrets += 1
        player.b2_available = False
        controller.event_log.append(f"{meta['name']} activated B2 Deep R&D Vault: +1 Corporate Secret for ${cost}.")

    elif action_type == "Y1":
        if not player.y1_available:
            raise ValueError("Y1 Algorithmic Trading ability is not available this turn")
        if player.money < 6:
            raise ValueError("Y1 requires $6 cash ($4 roll refund + $2 secret fee)")
        if player.secrets >= 10:
            raise ValueError("Secrets already at maximum capacity (10)")
        player.money -= 6
        player.secrets += 1
        player.y1_available = False
        controller.event_log.append(f"{meta['name']} activated Y1 Algorithmic Trading: converted $6 into +1 Secret.")

    elif action_type == "P1":
        if not player.p1_available:
            raise ValueError("P1 Zero-Day Injection ability is not available this turn")
        if not cube_color or cube_color.lower() not in ("red", "blue", "green"):
            raise ValueError("P1 requires selecting an attack cube color (red, blue, or green)")
        chosen = CubeColor(cube_color.lower())
        controller.state.staging_cup[chosen] = controller.state.staging_cup.get(chosen, 0) + 1
        player.p1_available = False
        controller.event_log.append(f"{meta['name']} activated P1 Zero-Day: added 1 {chosen.value.capitalize()} Cube to Staging Cup.")

    elif action_type == "P3":
        if not player.p3_available:
            raise ValueError("P3 Packet Deflection ability is not available this turn")
        blocked_color = player.p3_available.value
        if cube_color and cube_color.lower() != blocked_color:
            raise ValueError(f"P3 must add a cube matching the blocked color ({blocked_color})")
        cost = controller.state.config.p3_cube_cash_cost
        if player.money < cost:
            raise ValueError(f"P3 requires ${cost} cash")
        player.money -= cost
        chosen = CubeColor(blocked_color)
        controller.state.staging_cup[chosen] = controller.state.staging_cup.get(chosen, 0) + 1
        player.p3_available = None
        controller.event_log.append(f"{meta['name']} activated P3 Packet Deflection: paid ${cost} to add 1 {chosen.value.capitalize()} Cube to Staging Cup.")

    else:
        raise ValueError(f"Unsupported star action type: {action_type}")

    return controller.get_full_state()



def end_turn(controller: GameController, player_id: int) -> Dict[str, Any]:
    """Human action: finishes Phase 3 operations and advances clockwise."""
    if controller.phase != 3:
        raise ValueError(f"Cannot end turn in phase {controller.phase}")
    if player_id != controller.active_player_index:
        raise ValueError(f"Not player {player_id}'s turn (current: {controller.active_player_index})")

    meta = controller.player_meta[player_id]
    controller.event_log.append(f"{meta['name']} ended operations turn.")

    if controller.phase3_turn_queue and controller.phase3_turn_queue[0] == player_id:
        controller.phase3_turn_queue.pop(0)

    # Advance to next turn (or complete round)
    advance_phase3_turns(controller)
    return controller.get_full_state()

