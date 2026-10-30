"""Prototype Monte Carlo comparison: v0.14.0 Baseline vs Calibrated v0.15.0 Overhaul."""

from __future__ import annotations

import random
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from sim.config import CubeColor, DieColor, EndGameReason, GameConfig, ShieldColor
from sim.tower import CubeTower
from sim.engine.core import GameEngine
from sim.bots import (
    AdaptiveBalancedBot,
    SecOpsTurtleBot,
    VentureGreedBot,
    AccelerationistBot,
)
from sim.entities import get_random_setup


# =====================================================================
# 1. Run Current v0.14.0 Engine (With Rational Human-Like Dirty Income)
# =====================================================================

def run_v014_baseline(num_players: int = 3, num_games: int = 1000, rational_dirty: bool = True) -> Dict:
    rng_master = random.Random(42)
    rounds_list = []
    singularity_count = 0
    pz_count = 0
    wipeout_count = 0
    early_death_count = 0
    v2_rounds = []
    v3_rounds = []
    dirty_per_game = []
    exited_rbg_by_ver = {0: [], 1: [], 2: []}
    shield_commits = {ShieldColor.RED: 0, ShieldColor.BLUE: 0, ShieldColor.GREEN: 0}
    ending_cash_survivors = []
    ending_secrets_survivors = []

    for g in range(num_games):
        seed = rng_master.randint(1, 10**9)
        cfg = GameConfig(num_players=num_players)
        if rational_dirty:
            cfg.dirty_income_secret_cost = 99
        setup_rng = random.Random(seed)
        variants, versions = get_random_setup(setup_rng)
        pod = [
            AdaptiveBalancedBot(0),
            SecOpsTurtleBot(1),
            VentureGreedBot(2),
            AccelerationistBot(3),
        ][:num_players]
        engine = GameEngine(cfg, pod, seed=seed, variant_cards=variants, version_deck=versions)

        prev_ver = 0
        while not engine.state.game_over:
            cur_ver_before = engine.state.current_version_index
            commitments = engine._execute_phase_1()
            for _, rolled, comm in commitments:
                for idx, scol in comm.items():
                    if scol in shield_commits:
                        shield_commits[scol] += 1
            tel = engine._execute_phase_2(commitments)
            rbg = sum(tel.exited_cubes.get(c, 0) for c in (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN))
            exited_rbg_by_ver[cur_ver_before].append(rbg)

            cur_ver_after = engine.state.current_version_index
            if prev_ver == 0 and cur_ver_after >= 1:
                v2_rounds.append(engine.state.current_round)
            if prev_ver <= 1 and cur_ver_after >= 2:
                v3_rounds.append(engine.state.current_round)
            prev_ver = cur_ver_after

            if not engine.state.game_over:
                engine._execute_phase_3()
                if engine.state.is_final_round:
                    engine.state.game_over = True
                else:
                    engine.state.current_round += 1
                    if engine.state.current_round > engine.state.config.max_rounds:
                        engine.state.game_over = True
                        engine.state.end_reason = EndGameReason.ROUND_LIMIT

        res = engine.evaluate_end_game()
        rounds_list.append(res.total_rounds)
        if res.total_rounds <= 4 and res.end_reason in (EndGameReason.PATIENT_ZERO, EndGameReason.TOTAL_WIPEOUT):
            early_death_count += 1
        if res.end_reason == EndGameReason.SINGULARITY:
            singularity_count += 1
        elif res.end_reason == EndGameReason.PATIENT_ZERO:
            pz_count += 1
        elif res.end_reason == EndGameReason.TOTAL_WIPEOUT:
            wipeout_count += 1

        dirty_per_game.append(sum(p.total_dirty_income_taken for p in engine.state.players))
        for p in engine.state.players:
            if not p.is_patient_zero:
                ending_cash_survivors.append(p.money)
                ending_secrets_survivors.append(p.secrets)

    tot_shields = max(1, sum(shield_commits.values()))
    return {
        "avg_rounds": statistics.mean(rounds_list),
        "v2_compile_round": statistics.mean(v2_rounds) if v2_rounds else None,
        "v2_compile_rate": len(v2_rounds) / num_games,
        "v3_compile_round": statistics.mean(v3_rounds) if v3_rounds else None,
        "v3_compile_rate": len(v3_rounds) / num_games,
        "singularity_pct": 100.0 * singularity_count / num_games,
        "pz_pct": 100.0 * pz_count / num_games,
        "wipeout_pct": 100.0 * wipeout_count / num_games,
        "early_death_pct": 100.0 * early_death_count / num_games,
        "dirty_per_game": statistics.mean(dirty_per_game),
        "rbg_v1": statistics.mean(exited_rbg_by_ver[0]) if exited_rbg_by_ver[0] else 0.0,
        "rbg_v2": statistics.mean(exited_rbg_by_ver[1]) if exited_rbg_by_ver[1] else 0.0,
        "rbg_v3": statistics.mean(exited_rbg_by_ver[2]) if exited_rbg_by_ver[2] else 0.0,
        "shield_share_red": 100.0 * shield_commits[ShieldColor.RED] / tot_shields,
        "shield_share_blue": 100.0 * shield_commits[ShieldColor.BLUE] / tot_shields,
        "shield_share_green": 100.0 * shield_commits[ShieldColor.GREEN] / tot_shields,
        "survivor_cash": statistics.mean(ending_cash_survivors) if ending_cash_survivors else 0.0,
        "survivor_secrets": statistics.mean(ending_secrets_survivors) if ending_secrets_survivors else 0.0,
    }


# =====================================================================
# 2. v0.15.0 Prototype Engine (Calibrated Single-Currency + Slotted Mat)
# =====================================================================

@dataclass
class V15Face:
    name: str
    slot: int  # 1 = Boot (Resources/Glitch), 2 = Defense (Shield), 3 = Star (Phase 3)
    secrets: int = 0
    patches: int = 0
    block: int = 0
    shield_color: Optional[ShieldColor] = None
    is_glitch: bool = False
    is_star: bool = False
    star_code: Optional[str] = None
    is_choice: bool = False
    choices: Tuple["V15Face", ...] = ()


@dataclass
class V15Die:
    die_id: int
    color: DieColor
    cost: int  # In Secrets
    vp: int
    faces: List[V15Face]
    current_face: Optional[V15Face] = None
    effective_face: Optional[V15Face] = None
    is_locked: bool = False


def make_v15_die(color: DieColor, die_id: int, star_code: str = "") -> V15Die:
    glitch = V15Face("Glitch", slot=1, is_glitch=True)
    if color == DieColor.GRAY:
        faces = [
            V15Face("Block 1 Any", slot=2, block=1, shield_color=ShieldColor.ANY),
            V15Face("Block 1 Any", slot=2, block=1, shield_color=ShieldColor.ANY),
            V15Face("+1 Secret", slot=1, secrets=1),
            V15Face("+1 Secret", slot=1, secrets=1),
            V15Face(
                "+1 Secret / +1 🔧",
                slot=1,
                is_choice=True,
                choices=(
                    V15Face("+1 Secret", slot=1, secrets=1),
                    V15Face("+1 🔧", slot=1, patches=1),
                ),
            ),
            V15Face("+1 🔧", slot=1, patches=1),
        ]
        return V15Die(die_id, color, cost=0, vp=0, faces=faces)
    elif color == DieColor.WHITE:
        faces = [
            V15Face("Block 1 Any", slot=2, block=1, shield_color=ShieldColor.ANY),
            V15Face("Block 1 Any", slot=2, block=1, shield_color=ShieldColor.ANY),
            V15Face("Block 1 Any", slot=2, block=1, shield_color=ShieldColor.ANY),
            V15Face("+1 Secret", slot=1, secrets=1),
            glitch,
            glitch,
        ]
        return V15Die(die_id, color, cost=1, vp=0, faces=faces)
    elif color == DieColor.RED:
        faces = [
            V15Face("Block 1 Red", slot=2, block=1, shield_color=ShieldColor.RED),
            V15Face(
                "Block 1 Red / +1 Secret",
                slot=2,
                is_choice=True,
                choices=(
                    V15Face("Block 1 Red", slot=2, block=1, shield_color=ShieldColor.RED),
                    V15Face("+1 Secret", slot=1, secrets=1),
                ),
            ),
            V15Face("+2 Secrets", slot=1, secrets=2),
            V15Face("+1 Secret & +1 🔧", slot=1, secrets=1, patches=1),
            glitch,
            V15Face(f"Red ★ ({star_code})", slot=3, is_star=True, star_code=star_code),
        ]
        return V15Die(die_id, color, cost=3, vp=3, faces=faces)
    elif color == DieColor.BLUE:
        faces = [
            V15Face("Block 1 Blue", slot=2, block=1, shield_color=ShieldColor.BLUE),
            V15Face(
                "Block 1 Blue / +1 🔧",
                slot=2,
                is_choice=True,
                choices=(
                    V15Face("Block 1 Blue", slot=2, block=1, shield_color=ShieldColor.BLUE),
                    V15Face("+1 🔧", slot=1, patches=1),
                ),
            ),
            V15Face("+1 Secret", slot=1, secrets=1),
            V15Face("+1 Secret & +1 🔧", slot=1, secrets=1, patches=1),
            glitch,
            V15Face(f"Blue ★ ({star_code})", slot=3, is_star=True, star_code=star_code),
        ]
        return V15Die(die_id, color, cost=4, vp=4, faces=faces)
    elif color == DieColor.GREEN:
        faces = [
            V15Face("Block 1 Green", slot=2, block=1, shield_color=ShieldColor.GREEN),
            V15Face(
                "Block 1 Green / +1 🔧",
                slot=2,
                is_choice=True,
                choices=(
                    V15Face("Block 1 Green", slot=2, block=1, shield_color=ShieldColor.GREEN),
                    V15Face("+1 🔧", slot=1, patches=1),
                ),
            ),
            V15Face("+2 🔧", slot=1, patches=2),
            V15Face("+1 Secret & +1 🔧", slot=1, secrets=1, patches=1),
            glitch,
            V15Face(f"Green ★ ({star_code})", slot=3, is_star=True, star_code=star_code),
        ]
        return V15Die(die_id, color, cost=3, vp=3, faces=faces)
    elif color == DieColor.YELLOW:
        faces = [
            V15Face("+2 Secrets", slot=1, secrets=2),
            V15Face("+2 Secrets", slot=1, secrets=2),
            V15Face("+1 Secret & +1 🔧", slot=1, secrets=1, patches=1),
            V15Face("+1 Secret", slot=1, secrets=1),
            V15Face(f"Yellow ★ ({star_code})", slot=3, is_star=True, star_code=star_code),
            V15Face(f"Yellow ★ ({star_code})", slot=3, is_star=True, star_code=star_code),
        ]
        return V15Die(die_id, color, cost=4, vp=4, faces=faces)
    elif color == DieColor.PURPLE:
        faces = [
            V15Face("Block 1 Any", slot=2, block=1, shield_color=ShieldColor.ANY),
            V15Face("Block 1 Any", slot=2, block=1, shield_color=ShieldColor.ANY),
            V15Face("+2 Secrets", slot=1, secrets=2),
            V15Face("+1 Secret & +1 🔧", slot=1, secrets=1, patches=1),
            V15Face(f"Purple ★ ({star_code})", slot=3, is_star=True, star_code=star_code),
            V15Face(f"Purple ★ ({star_code})", slot=3, is_star=True, star_code=star_code),
        ]
        return V15Die(die_id, color, cost=3, vp=3, faces=faces)
    raise ValueError(color)


@dataclass
class V15Player:
    pid: int
    bot_style: str  # "BALANCED", "TURTLE", "GREED", "ACCEL"
    archetype: str
    secrets: int
    patches: int = 2
    archived_tapes: int = 0
    ready_dice: List[V15Die] = field(default_factory=list)
    unpatched_dice: List[V15Die] = field(default_factory=list)
    contractors: List[V15Die] = field(default_factory=list)
    slot1_dice: List[V15Die] = field(default_factory=list)
    slot2_dice: List[Tuple[V15Die, ShieldColor]] = field(default_factory=list)
    slot3_dice: List[V15Die] = field(default_factory=list)
    is_patient_zero: bool = False
    breach_depth: int = 0
    unfulfilled_destructions: int = 0
    system_reboot_used: bool = False
    ability_avail: Dict[int, bool] = field(default_factory=lambda: {0: True, 1: False, 2: False})
    dirty_siphons: int = 0
    tapes_archived: int = 0
    phase3_stars_sniped: int = 0
    phase2_shields_knocked: int = 0


@dataclass
class V15SimParams:
    num_players: int = 3
    starting_secrets: Dict[int, int] = field(default_factory=lambda: {2: 8, 3: 8, 4: 10})
    vault_cap: int = 12
    max_patches: int = 3
    track_capacity: Dict[int, int] = field(default_factory=lambda: {2: 6, 3: 7, 4: 8})
    black_pulse_by_ver: Tuple[int, int, int] = (2, 2, 3)
    dirty_siphon_secrets: int = 3
    dirty_siphon_adds_attack_cube: bool = False
    archive_cost: int = 3
    archive_vp: int = 4
    liquid_secret_vp: int = 1
    immediate_compile_drop: bool = True
    on_compile_abilities: bool = True
    # Capped 1-Secret leak per Red cube (costs 2 🔧; if <2 🔧, lose remaining 🔧 and 1 Secret!)
    capped_red_secret_leak: bool = True
    # Green = Unpatch 1 die (Slot 3 ★ first) + Lose 1 🔧 (vs 2 dice)
    green_unpatch_one_plus_wrench: bool = True


def run_v015_prototype(params: V15SimParams, num_games: int = 1000) -> Dict:
    rng_master = random.Random(42)

    rounds_list = []
    v2_rounds = []
    v3_rounds = []
    singularity_count = 0
    pz_count = 0
    wipeout_count = 0
    early_death_count = 0

    exited_rbg_by_ver = {0: [], 1: [], 2: []}
    shield_commits = {ShieldColor.RED: 0, ShieldColor.BLUE: 0, ShieldColor.GREEN: 0}
    cubes_dropped_color = {CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0}
    cubes_blocked_color = {CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0}

    dirty_per_game = []
    tapes_per_survivor = []
    colored_dice_per_survivor = []
    secrets_per_survivor = []
    unpatched_colored_per_survivor = []
    stars_sniped_per_game = []
    shields_knocked_per_game = []
    bot_wins = {"BALANCED": 0, "TURTLE": 0, "GREED": 0, "ACCEL": 0}
    bot_appearances = {"BALANCED": 0, "TURTLE": 0, "GREED": 0, "ACCEL": 0}

    styles_pool = ["BALANCED", "TURTLE", "GREED", "ACCEL"]
    archetypes_pool = ["ACOUSTIC", "PHREAKER", "PRODIGY", "SPOOK", "CIPHER", "OPERATOR"]

    for g in range(num_games):
        rng = random.Random(rng_master.randint(1, 10**9))
        n = params.num_players
        t_cfg = GameConfig(num_players=n, tower_ledge_capacity=6.5)
        tower = CubeTower(t_cfg)

        # Prime compiler (1R, 1B, 1G, 1K)
        tower.drop({CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 1, CubeColor.BLACK: 1}, rng)

        # Setup Roadmap
        v1_card = rng.choice(["SCRIPT_KIDDIE", "DATA_SCRAPER"])
        v2_card = rng.choice(["RAAS", "POLYMORPHIC_WORM"])
        v3_card = rng.choice(["ZERO_DAY_OVERRIDE", "CORRUPTED_KERNEL"])
        roadmap = [v1_card, v2_card, v3_card]

        star_map = {
            DieColor.RED: rng.choice(["R1", "R2", "R3"]),
            DieColor.BLUE: rng.choice(["B1", "B2", "B3"]),
            DieColor.GREEN: rng.choice(["G1", "G2", "G3"]),
            DieColor.YELLOW: rng.choice(["Y1", "Y2", "Y3"]),
            DieColor.PURPLE: rng.choice(["P1", "P2", "P3"]),
        }

        staging = {CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 1, CubeColor.BLACK: 0}
        if v1_card == "DATA_SCRAPER":
            staging = {CubeColor.RED: 1, CubeColor.BLUE: 2, CubeColor.GREEN: 0, CubeColor.BLACK: 0}

        market = {
            DieColor.RED: 2 * n,
            DieColor.BLUE: 2 * n,
            DieColor.GREEN: 2 * n,
            DieColor.YELLOW: 2 * n,
            DieColor.PURPLE: 2 * n,
        }

        chosen_archs = rng.sample(archetypes_pool, n)
        players: List[V15Player] = []
        next_die_id = 1
        start_sec = params.starting_secrets[n] + (1 if v1_card == "DATA_SCRAPER" else 0)
        for i in range(n):
            style = styles_pool[i % len(styles_pool)]
            bot_appearances[style] += 1
            grays = [make_v15_die(DieColor.GRAY, next_die_id + j) for j in range(4)]
            next_die_id += 4
            players.append(
                V15Player(
                    pid=i,
                    bot_style=style,
                    archetype=chosen_archs[i],
                    secrets=min(params.vault_cap, start_sec),
                    patches=2,
                    ready_dice=grays,
                )
            )

        cur_ver = 0
        corruption = 0
        track_cap = params.track_capacity[n]
        first_player = rng.randrange(n)
        round_num = 1
        game_over = False
        is_final_round = False
        singularity = False
        end_reason = EndGameReason.NONE

        while not game_over:
            ver_at_start = cur_ver
            active_card = roadmap[cur_ver]

            # --- PHASE 1: BOOT & CONFIGURE ---
            pulse_black = params.black_pulse_by_ver[cur_ver]
            staging[CubeColor.BLACK] += pulse_black

            stuck = tower.get_stuck_copy()
            exp_threat = {
                c: (staging.get(c, 0) + stuck.get(c, 0)) * 0.70
                for c in (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN)
            }

            for p in players:
                if p.is_patient_zero:
                    continue
                p.contractors.clear()
                p.slot1_dice.clear()
                p.slot2_dice.clear()
                p.slot3_dice.clear()

                # 2. Contractor Staffing
                if p.archetype == "OPERATOR" and p.ability_avail.get(cur_ver, False) and len(p.ready_dice) <= 3:
                    p.ability_avail[cur_ver] = False
                    for _ in range(2):
                        p.contractors.append(make_v15_die(DieColor.WHITE, next_die_id))
                        next_die_id += 1
                elif len(p.ready_dice) <= 2 and p.secrets >= 5:
                    p.secrets -= 1
                    p.contractors.append(make_v15_die(DieColor.WHITE, next_die_id))
                    next_die_id += 1

                # 3. Roll Ready + Contractors
                pool = list(p.ready_dice) + list(p.contractors)
                for d in pool:
                    d.is_locked = False
                    d.current_face = rng.choice(d.faces)
                    d.effective_face = d.current_face

                def eval_locks(dice_pool: List[V15Die]) -> None:
                    for d in dice_pool:
                        f = d.current_face
                        if not f:
                            continue
                        if f.is_glitch:
                            d.is_locked = True
                        elif active_card == "RAAS":
                            if not f.is_choice and f.secrets == 1 and f.patches == 0 and f.block == 0:
                                d.is_locked = True
                        elif active_card == "POLYMORPHIC_WORM":
                            if not f.is_choice and f.patches == 1 and f.secrets == 0 and f.block == 0:
                                d.is_locked = True
                        elif active_card == "ZERO_DAY_OVERRIDE":
                            if not f.is_choice and f.block > 0 and f.shield_color == ShieldColor.ANY:
                                d.is_locked = True
                        elif active_card == "CORRUPTED_KERNEL":
                            if f.is_star:
                                d.is_locked = True

                eval_locks(pool)

                prodigy_used = False
                if p.archetype == "PRODIGY" and p.ability_avail.get(cur_ver, False):
                    glitches = sum(1 for d in pool if d.current_face and d.current_face.is_glitch)
                    if glitches >= 1 or p.secrets <= 3:
                        prodigy_used = True
                        p.ability_avail[cur_ver] = False

                for _ in range(2):
                    for d in pool:
                        if d.is_locked and d.current_face and d.current_face.is_glitch:
                            if prodigy_used:
                                d.is_locked = False
                            elif p.patches >= (2 if exp_threat[CubeColor.RED] >= 1.2 else 1):
                                p.patches -= 1
                                d.is_locked = False

                    reroll_list = []
                    shields_have = sum(
                        1 for d in pool
                        if d.current_face and (d.current_face.block > 0 or (d.current_face.is_choice and d.current_face.choices[0].block > 0))
                    )
                    rb_exp_dmg = exp_threat[CubeColor.RED] + exp_threat[CubeColor.BLUE]
                    total_exp_dmg = sum(exp_threat.values())
                    need_shields = (
                        shields_have < total_exp_dmg
                        if p.secrets <= 6 or cur_ver >= 1
                        else shields_have < rb_exp_dmg
                    )
                    for d in pool:
                        if d.is_locked and not prodigy_used:
                            continue
                        f = d.current_face
                        if not f:
                            continue
                        if f.is_glitch:
                            reroll_list.append(d)
                        elif need_shields and f.block == 0 and not (f.is_choice and f.choices[0].block > 0) and not f.is_star and f.secrets < 2:
                            reroll_list.append(d)
                        elif p.bot_style == "GREED" and not need_shields and f.patches == 1 and f.secrets == 0 and len(p.unpatched_dice) == 0:
                            reroll_list.append(d)

                    if not reroll_list:
                        break
                    for d in reroll_list:
                        d.current_face = rng.choice(d.faces)
                        d.effective_face = d.current_face
                        d.is_locked = False
                    eval_locks(pool)

                if prodigy_used:
                    for d in pool:
                        if d.current_face and d.current_face.is_glitch:
                            non_star = [f for f in d.faces if not f.is_star and not f.is_glitch]
                            if non_star:
                                d.current_face = non_star[0]
                                d.effective_face = non_star[0]
                                d.is_locked = False
                            break

                # 4. Universal Slotting into Row 1, Row 2, Row 3
                def color_urgency(c: CubeColor, cur_shields: Dict[ShieldColor, int], stars_count: int) -> float:
                    sc = ShieldColor(c.value)
                    unblocked_est = max(0.0, exp_threat[c] - cur_shields[sc])
                    if unblocked_est <= 0.15:
                        return 0.1
                    if c == CubeColor.BLUE:
                        base = 3.2 if p.secrets <= 4 else (2.2 if p.secrets <= 6 else 1.7)
                        return base * unblocked_est
                    elif c == CubeColor.RED:
                        if p.patches == 0:
                            base = 3.5 if p.secrets <= 4 else 2.4
                        elif p.patches == 1:
                            base = 2.8 if p.secrets <= 4 else 2.1
                        else:
                            base = 1.5 + 0.3 * len(p.unpatched_dice)
                        return base * unblocked_est
                    else:  # GREEN
                        if stars_count > 0:
                            base = 3.1 + 0.5 * stars_count
                        elif len(p.ready_dice) <= 2:
                            base = 2.9
                        else:
                            base = 1.8 + 0.25 * len(p.unpatched_dice)
                        return base * unblocked_est

                cur_shields = {ShieldColor.RED: 0, ShieldColor.BLUE: 0, ShieldColor.GREEN: 0}
                stars_rolled = sum(1 for d in pool if d.current_face and d.current_face.is_star)

                choice_dice = []
                any_shield_dice = []
                for d in pool:
                    f = d.current_face
                    if not f:
                        continue
                    if f.is_glitch:
                        p.slot1_dice.append(d)
                    elif f.is_star:
                        p.slot3_dice.append(d)
                    elif f.is_choice:
                        choice_dice.append(d)
                    elif f.block > 0:
                        if f.shield_color == ShieldColor.ANY:
                            any_shield_dice.append(d)
                        else:
                            p.slot2_dice.append((d, f.shield_color))
                            cur_shields[f.shield_color] += f.block
                    else:
                        p.slot1_dice.append(d)

                for d in choice_dice:
                    f = d.current_face
                    c0, c1 = f.choices[0], f.choices[1]
                    if c0.block > 0 and c0.shield_color is not None:
                        col = CubeColor(c0.shield_color.value)
                        urg = color_urgency(col, cur_shields, stars_rolled)
                        if urg >= 1.1:
                            d.effective_face = c0
                            p.slot2_dice.append((d, c0.shield_color))
                            cur_shields[c0.shield_color] += c0.block
                        else:
                            d.effective_face = c1
                            p.slot1_dice.append(d)
                    else:
                        if p.patches <= 1 and (exp_threat[CubeColor.RED] >= 0.8 or len(p.unpatched_dice) >= 1):
                            d.effective_face = c1
                        elif p.secrets < params.vault_cap:
                            d.effective_face = c0
                        else:
                            d.effective_face = c1
                        p.slot1_dice.append(d)

                for d in any_shield_dice:
                    best_c = max(
                        (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN),
                        key=lambda c: color_urgency(c, cur_shields, stars_rolled),
                    )
                    sc = ShieldColor(best_c.value)
                    p.slot2_dice.append((d, sc))
                    cur_shields[sc] += d.effective_face.block

                for _, sc in p.slot2_dice:
                    shield_commits[sc] += 1

                # 5. Execute Phase 1 (Row 1):
                # Each unresolved Glitch die produces 0 output and forces 1 OTHER slotted die (or itself if none) to Unpatched!
                glitches_in_s1 = [d for d in list(p.slot1_dice) if d.effective_face and d.effective_face.is_glitch]
                for gd in glitches_in_s1:
                    if gd in p.slot1_dice:
                        p.slot1_dice.remove(gd)

                    if p.contractors:
                        sac = p.contractors.pop(0)
                        if sac in p.slot1_dice:
                            p.slot1_dice.remove(sac)
                        p.slot2_dice = [(x, sc) for (x, sc) in p.slot2_dice if x.die_id != sac.die_id]
                    else:
                        non_glitch_s1 = [x for x in p.slot1_dice if not (x.effective_face and x.effective_face.is_glitch)]
                        if non_glitch_s1:
                            victim = non_glitch_s1[0]
                            p.slot1_dice.remove(victim)
                            if victim in p.ready_dice:
                                p.ready_dice.remove(victim)
                                p.unpatched_dice.append(victim)
                        elif p.slot3_dice:
                            victim = p.slot3_dice.pop(0)
                            p.phase3_stars_sniped += 1
                            if victim in p.ready_dice:
                                p.ready_dice.remove(victim)
                                p.unpatched_dice.append(victim)
                        elif p.slot2_dice:
                            victim, _ = p.slot2_dice.pop(0)
                            p.phase2_shields_knocked += 1
                            if victim in p.ready_dice:
                                p.ready_dice.remove(victim)
                                p.unpatched_dice.append(victim)
                        elif gd in p.ready_dice:
                            p.ready_dice.remove(gd)
                            p.unpatched_dice.append(gd)

                for d in p.slot1_dice:
                    ef = d.effective_face
                    if ef and not ef.is_glitch:
                        p.secrets = min(params.vault_cap, p.secrets + ef.secrets)
                        p.patches = min(params.max_patches, p.patches + ef.patches)
                p.slot1_dice.clear()

            # --- PHASE 2: SETEC COMPILE (THE CUBE TOWER DROP) ---
            exited = tower.drop(staging, rng)
            for c in staging:
                staging[c] = 0

            if sum(exited.values()) == 0:
                staging[CubeColor.RED] += 1
                staging[CubeColor.BLUE] += 1
                staging[CubeColor.GREEN] += 1
            else:
                black_out = exited.get(CubeColor.BLACK, 0)
                for _ in range(black_out):
                    corruption += 1
                    if corruption >= track_cap:
                        if cur_ver >= 2:
                            singularity = True
                            break
                        else:
                            corruption = 0
                            cur_ver += 1
                            if cur_ver == 1:
                                v2_rounds.append(round_num)
                            elif cur_ver == 2:
                                v3_rounds.append(round_num)

                            for p in players:
                                p.ability_avail[cur_ver - 1] = False
                                p.ability_avail[cur_ver] = True

                            new_card = roadmap[cur_ver]
                            payload = {
                                "RAAS": {CubeColor.RED: 1, CubeColor.GREEN: 1},
                                "POLYMORPHIC_WORM": {CubeColor.GREEN: 1, CubeColor.BLUE: 1},
                                "ZERO_DAY_OVERRIDE": {CubeColor.RED: 1, CubeColor.GREEN: 1},
                                "CORRUPTED_KERNEL": {CubeColor.BLUE: 1, CubeColor.RED: 1},
                            }[new_card]

                            if params.immediate_compile_drop:
                                # Roll only the new payload cubes through the tower (without re-dropping already-stuck cubes!)
                                exit_p = tower.calculate_exit_probability(tower.total_stuck() + sum(payload.values()))
                                for col_k, cnt_k in payload.items():
                                    for _ in range(cnt_k):
                                        if rng.random() < exit_p:
                                            exited[col_k] = exited.get(col_k, 0) + 1
                                        else:
                                            tower.stuck_cubes[col_k] = tower.stuck_cubes.get(col_k, 0) + 1
                            else:
                                for col_k, cnt_k in payload.items():
                                    staging[col_k] = staging.get(col_k, 0) + cnt_k

                            if params.on_compile_abilities:
                                for p in players:
                                    if p.is_patient_zero:
                                        continue
                                    if new_card == "RAAS":
                                        if p.patches > 0:
                                            p.patches -= 1
                                        elif p.slot2_dice:
                                            vd, _ = p.slot2_dice.pop(0)
                                            p.phase2_shields_knocked += 1
                                            if vd in p.ready_dice:
                                                p.ready_dice.remove(vd)
                                                p.unpatched_dice.append(vd)
                                    elif new_card == "POLYMORPHIC_WORM":
                                        if p.slot2_dice:
                                            vd, old_sc = p.slot2_dice.pop(0)
                                            nf = rng.choice(vd.faces)
                                            vd.current_face = nf
                                            vd.effective_face = nf.choices[0] if nf.is_choice else nf
                                            if vd.effective_face.block > 0:
                                                new_sc = (
                                                    old_sc if vd.effective_face.shield_color == ShieldColor.ANY
                                                    else vd.effective_face.shield_color
                                                )
                                                p.slot2_dice.append((vd, new_sc))
                                            elif vd.effective_face.is_star:
                                                p.phase2_shields_knocked += 1
                                                p.slot3_dice.append(vd)
                                            elif vd.effective_face.is_glitch:
                                                p.phase2_shields_knocked += 1
                                                if vd in p.ready_dice:
                                                    p.ready_dice.remove(vd)
                                                    p.unpatched_dice.append(vd)
                                            else:
                                                p.phase2_shields_knocked += 1
                                                p.secrets = min(params.vault_cap, p.secrets + vd.effective_face.secrets)
                                                p.patches = min(params.max_patches, p.patches + vd.effective_face.patches)
                                    elif new_card == "ZERO_DAY_OVERRIDE":
                                        if p.slot2_dice:
                                            vd, _ = p.slot2_dice.pop(0)
                                            p.phase2_shields_knocked += 1
                                            if vd in p.ready_dice:
                                                p.ready_dice.remove(vd)
                                                p.unpatched_dice.append(vd)
                                    elif new_card == "CORRUPTED_KERNEL":
                                        if len(p.unpatched_dice) >= 2:
                                            p.secrets -= 1

                r_atk = exited.get(CubeColor.RED, 0)
                b_atk = exited.get(CubeColor.BLUE, 0)
                g_atk = exited.get(CubeColor.GREEN, 0)
                exited_rbg_by_ver[ver_at_start].append(r_atk + b_atk + g_atk)

                if roadmap[cur_ver] == "CORRUPTED_KERNEL" and black_out >= 2:
                    if r_atk >= b_atk and r_atk >= g_atk:
                        r_atk += 1
                    elif b_atk >= g_atk:
                        b_atk += 1
                    else:
                        g_atk += 1

                for p in players:
                    if p.is_patient_zero:
                        continue
                    cubes_dropped_color[CubeColor.RED] += r_atk
                    cubes_dropped_color[CubeColor.BLUE] += b_atk
                    cubes_dropped_color[CubeColor.GREEN] += g_atk

                    p_atk = {CubeColor.RED: r_atk, CubeColor.BLUE: b_atk, CubeColor.GREEN: g_atk}

                    if p.archetype == "ACOUSTIC" and p.ability_avail.get(cur_ver, False):
                        if sum(p_atk.values()) >= 3 or p.secrets <= 3:
                            best_ignore = max(
                                (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN),
                                key=lambda c: p_atk[c],
                            )
                            if p_atk[best_ignore] > 0:
                                p_atk[best_ignore] -= 1
                                p.ability_avail[cur_ver] = False

                    s_map = {ShieldColor.RED: [], ShieldColor.BLUE: [], ShieldColor.GREEN: []}
                    for d, sc in p.slot2_dice:
                        s_map[sc].append(d)

                    unblocked = {}
                    for col, sc in (
                        (CubeColor.RED, ShieldColor.RED),
                        (CubeColor.BLUE, ShieldColor.BLUE),
                        (CubeColor.GREEN, ShieldColor.GREEN),
                    ):
                        inc = p_atk[col]
                        dice_for_col = sorted(s_map[sc], key=lambda x: (0 if x.color == DieColor.WHITE else 1, x.vp))
                        blocked = 0
                        for d in dice_for_col:
                            if blocked >= inc:
                                break
                            blk = d.effective_face.block if d.effective_face else 1
                            blocked += blk
                            if d.color != DieColor.WHITE and d in p.ready_dice:
                                p.ready_dice.remove(d)
                                p.unpatched_dice.append(d)
                        actual_blk = min(inc, blocked)
                        cubes_blocked_color[col] += actual_blk
                        unblocked[col] = inc - actual_blk

                    p.slot2_dice.clear()

                    # Unblocked Damage Resolution:
                    # 1. RED: Each unblocked Red cube drains 1 🔧; if you have 0 🔧, leak 1 Secret!
                    red_secret_leak = 0
                    for _ in range(unblocked[CubeColor.RED]):
                        if p.patches >= 1:
                            p.patches -= 1
                        else:
                            red_secret_leak += 1

                    # 2. BLUE: Lose 1 Secret per unblocked Blue (ignores 🔧!)
                    blue_secret_loss = unblocked[CubeColor.BLUE]
                    total_secret_loss = red_secret_leak + blue_secret_loss

                    if total_secret_loss > 0 and p.archetype == "SPOOK" and p.ability_avail.get(cur_ver, False):
                        if total_secret_loss >= 2 or p.secrets - total_secret_loss <= 1:
                            total_secret_loss = max(0, total_secret_loss - 2)
                            p.ability_avail[cur_ver] = False

                    p.secrets -= total_secret_loss

                    # 3. GREEN:
                    # Unpatch 1 die (Slot 3 ★ first, then Contractors, then Ready; excess Destroys 1 Unpatched) + drain 1 🔧!
                    for _ in range(unblocked[CubeColor.GREEN]):
                        if not params.green_unpatch_one_plus_wrench:
                            # 2 unpatches mode
                            for _ in range(2):
                                if p.slot3_dice:
                                    sniped = p.slot3_dice.pop(0)
                                    p.phase3_stars_sniped += 1
                                    if sniped in p.ready_dice:
                                        p.ready_dice.remove(sniped)
                                        p.unpatched_dice.append(sniped)
                                elif p.contractors:
                                    p.contractors.pop(0)
                                elif p.ready_dice:
                                    p.ready_dice.sort(key=lambda x: (0 if x.color == DieColor.GRAY else 1, x.vp))
                                    dem = p.ready_dice.pop(0)
                                    p.unpatched_dice.append(dem)
                                elif p.unpatched_dice:
                                    p.unpatched_dice.sort(key=lambda x: (0 if x.color == DieColor.GRAY else 1, x.vp))
                                    p.unpatched_dice.pop(0)
                                else:
                                    p.unfulfilled_destructions += 1
                        else:
                            # 1 unpatch (Slot 3 ★ first, else Ready) + if no Slot 3 ★ was sniped, also unpatch a 2nd Ready die ONLY if player has 3+ Ready dice!
                            if p.slot3_dice:
                                sniped = p.slot3_dice.pop(0)
                                p.phase3_stars_sniped += 1
                                if sniped in p.ready_dice:
                                    p.ready_dice.remove(sniped)
                                    p.unpatched_dice.append(sniped)
                            elif p.contractors:
                                p.contractors.pop(0)
                            elif p.ready_dice:
                                p.ready_dice.sort(key=lambda x: (0 if x.color == DieColor.GRAY else 1, x.vp))
                                dem = p.ready_dice.pop(0)
                                p.unpatched_dice.append(dem)
                                if len(p.ready_dice) >= 3:
                                    dem2 = p.ready_dice.pop(0)
                                    p.unpatched_dice.append(dem2)
                            elif p.unpatched_dice:
                                p.unpatched_dice.sort(key=lambda x: (0 if x.color == DieColor.GRAY else 1, x.vp))
                                p.unpatched_dice.pop(0)
                            else:
                                p.unfulfilled_destructions += 1

                    if p.secrets <= 0:
                        p.is_patient_zero = True
                        p.breach_depth = -p.secrets

                for col in (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN):
                    staging[col] += exited.get(col, 0)

                for p in players:
                    p.contractors.clear()

                if all(p.is_patient_zero for p in players):
                    game_over = True
                    end_reason = EndGameReason.TOTAL_WIPEOUT
                elif any(p.is_patient_zero for p in players):
                    is_final_round = True
                    end_reason = EndGameReason.PATIENT_ZERO
                elif singularity:
                    is_final_round = True
                    end_reason = EndGameReason.SINGULARITY

            # --- PHASE 3: OPERATIONS & SURVIVING ★ DICE ---
            if not game_over:
                for off in range(n):
                    p = players[(first_player + off) % n]
                    if p.is_patient_zero:
                        continue

                    for sd in list(p.slot3_dice):
                        sc = sd.effective_face.star_code if sd.effective_face else ""
                        if sc in ("R1", "R2", "R3"):
                            p.secrets = min(params.vault_cap, p.secrets + 2)
                            if p.unpatched_dice:
                                p.unpatched_dice.sort(key=lambda x: x.vp, reverse=True)
                                p.ready_dice.append(p.unpatched_dice.pop(0))
                            else:
                                p.patches = min(params.max_patches, p.patches + 1)
                        elif sc in ("B1", "B2", "B3"):
                            if p.secrets >= 6:
                                p.secrets -= 2
                                p.archived_tapes += 1
                                p.tapes_archived += 1
                            else:
                                p.secrets = min(params.vault_cap, p.secrets + 2)
                        elif sc in ("G1", "G2", "G3"):
                            for _ in range(min(2, len(p.unpatched_dice))):
                                p.unpatched_dice.sort(key=lambda x: x.vp, reverse=True)
                                p.ready_dice.append(p.unpatched_dice.pop(0))
                            p.patches = min(params.max_patches, p.patches + 1)
                        elif sc in ("Y1", "Y2", "Y3"):
                            colored_cnt = sum(1 for d in p.ready_dice + p.unpatched_dice if d.color != DieColor.GRAY)
                            bonus = 3 if colored_cnt >= 3 else 2
                            p.secrets = min(params.vault_cap, p.secrets + bonus)
                        elif sc == "P1":
                            p.secrets = min(params.vault_cap, p.secrets + 2)
                            if p.secrets >= 7 and cur_ver <= 1:
                                inj = rng.choice([CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN])
                                staging[inj] += 1
                        elif sc in ("P2", "P3"):
                            p.secrets = min(params.vault_cap, p.secrets + 2)
                            p.patches = min(params.max_patches, p.patches + 1)
                    p.slot3_dice.clear()

                    if len(p.ready_dice) == 0 and not p.system_reboot_used:
                        p.system_reboot_used = True
                        restored = [d for d in p.unpatched_dice if d.color == DieColor.GRAY]
                        p.unpatched_dice = [d for d in p.unpatched_dice if d.color != DieColor.GRAY]
                        p.ready_dice.extend(restored)

                    if p.archetype == "PHREAKER" and p.ability_avail.get(cur_ver, False) and p.unpatched_dice:
                        p.unpatched_dice.sort(key=lambda x: x.vp, reverse=True)
                        p.ready_dice.append(p.unpatched_dice.pop(0))
                        p.ability_avail[cur_ver] = False

                    # Backdoor Siphon ("Dirty Secrets")
                    want_siphon = False
                    if not is_final_round:
                        if p.secrets <= 5 and len(p.ready_dice) >= 2:
                            want_siphon = True
                        elif p.bot_style == "ACCEL" and len(p.ready_dice) >= 3 and p.secrets <= params.vault_cap - 3:
                            want_siphon = True
                        elif p.bot_style in ("GREED", "BALANCED") and p.secrets <= 7 and len(p.ready_dice) >= 3 and len(p.unpatched_dice) <= 1:
                            want_siphon = True

                    if want_siphon:
                        cipher_no_demote = (
                            p.archetype == "CIPHER" and p.ability_avail.get(cur_ver, False)
                        )
                        if cipher_no_demote or len(p.ready_dice) >= 1:
                            p.secrets = min(params.vault_cap, p.secrets + params.dirty_siphon_secrets)
                            staging[CubeColor.BLACK] += 1
                            if params.dirty_siphon_adds_attack_cube:
                                inj_col = rng.choice([CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN])
                                staging[inj_col] += 1
                            p.dirty_siphons += 1
                            if cipher_no_demote:
                                p.ability_avail[cur_ver] = False
                            else:
                                p.ready_dice.sort(key=lambda x: (0 if x.color == DieColor.GRAY else 1, x.vp))
                                p.unpatched_dice.append(p.ready_dice.pop(0))

                    # Patch Worn Dice with 🔧
                    reserve_wrenches = 0 if is_final_round else 1
                    while p.unpatched_dice and p.patches > reserve_wrenches:
                        p.unpatched_dice.sort(key=lambda x: (1 if x.color != DieColor.GRAY else 0, x.vp), reverse=True)
                        p.patches -= 1
                        p.ready_dice.append(p.unpatched_dice.pop(0))
                    # Also spend last 🔧 if >=2 dice are unpatched!
                    if not is_final_round and len(p.unpatched_dice) >= 2 and p.patches > 0:
                        p.unpatched_dice.sort(key=lambda x: (1 if x.color != DieColor.GRAY else 0, x.vp), reverse=True)
                        p.patches -= 1
                        p.ready_dice.append(p.unpatched_dice.pop(0))

                    if is_final_round:
                        while p.unpatched_dice and p.patches > 0:
                            p.unpatched_dice.sort(key=lambda x: x.vp, reverse=True)
                            p.patches -= 1
                            p.ready_dice.append(p.unpatched_dice.pop(0))
                        while p.unpatched_dice and p.secrets >= 2:
                            p.unpatched_dice.sort(key=lambda x: x.vp, reverse=True)
                            if p.unpatched_dice[0].vp > params.liquid_secret_vp:
                                p.secrets -= 1
                                p.ready_dice.append(p.unpatched_dice.pop(0))
                            else:
                                break
                    elif len(p.ready_dice) <= 2 and p.unpatched_dice and p.secrets >= 6:
                        p.unpatched_dice.sort(key=lambda x: x.vp, reverse=True)
                        p.secrets -= 1
                        p.ready_dice.append(p.unpatched_dice.pop(0))

                    # Buy Colored Module Dice (Keep safe survival buffer scaled by version threat!)
                    base_floor = (7 if p.bot_style == "TURTLE" else 6) + cur_ver
                    safety_floor = 1 if is_final_round else base_floor
                    bought = 0
                    pref_order = {
                        "BALANCED": [DieColor.BLUE, DieColor.GREEN, DieColor.RED, DieColor.PURPLE, DieColor.YELLOW],
                        "TURTLE": [DieColor.BLUE, DieColor.GREEN, DieColor.RED, DieColor.PURPLE, DieColor.YELLOW],
                        "GREED": [DieColor.YELLOW, DieColor.RED, DieColor.BLUE, DieColor.PURPLE, DieColor.GREEN],
                        "ACCEL": [DieColor.PURPLE, DieColor.RED, DieColor.GREEN, DieColor.BLUE, DieColor.YELLOW],
                    }[p.bot_style]

                    for col in pref_order:
                        if bought >= 2:
                            break
                        if market[col] <= 0:
                            continue
                        base_cost = 3 if col in (DieColor.RED, DieColor.GREEN, DieColor.PURPLE) else 4
                        use_cipher_disc = (
                            p.archetype == "CIPHER" and p.ability_avail.get(cur_ver, False)
                        )
                        cost = max(1, base_cost - (1 if use_cipher_disc else 0))
                        if p.secrets - cost >= safety_floor:
                            p.secrets -= cost
                            market[col] -= 1
                            bought += 1
                            if use_cipher_disc:
                                p.ability_avail[cur_ver] = False
                            p.ready_dice.append(make_v15_die(col, next_die_id, star_map[col]))
                            next_die_id += 1

                    # Cold-Storage Archiving (Late-game sink & Final Round conversion!)
                    archive_floor = 1 if is_final_round else (7 if p.bot_style == "TURTLE" else 6) + cur_ver
                    while p.secrets - params.archive_cost >= archive_floor:
                        p.secrets -= params.archive_cost
                        p.archived_tapes += 1
                        p.tapes_archived += 1

                if is_final_round:
                    game_over = True
                else:
                    round_num += 1
                    first_player = (first_player + 1) % n
                    if round_num > 30:
                        game_over = True
                        end_reason = EndGameReason.ROUND_LIMIT

        rounds_list.append(round_num)
        if round_num <= 4 and end_reason in (EndGameReason.PATIENT_ZERO, EndGameReason.TOTAL_WIPEOUT):
            early_death_count += 1
        if end_reason == EndGameReason.SINGULARITY:
            singularity_count += 1
        elif end_reason == EndGameReason.PATIENT_ZERO:
            pz_count += 1
        elif end_reason == EndGameReason.TOTAL_WIPEOUT:
            wipeout_count += 1

        dirty_per_game.append(sum(p.dirty_siphons for p in players))
        stars_sniped_per_game.append(sum(p.phase3_stars_sniped for p in players))
        shields_knocked_per_game.append(sum(p.phase2_shields_knocked for p in players))

        all_pz = all(p.is_patient_zero for p in players)
        scored = []
        for p in players:
            ready_vp = sum(d.vp for d in p.ready_dice)
            tape_vp = p.archived_tapes * params.archive_vp
            sec_vp = max(0, p.secrets) * params.liquid_secret_vp
            port_vp = ready_vp + tape_vp + sec_vp
            pen = (-4 * p.breach_depth - 3 * p.unfulfilled_destructions) if all_pz else 0
            scored.append((port_vp + pen, p.secrets, p))

            if not p.is_patient_zero:
                tapes_per_survivor.append(p.tapes_archived)
                colored_dice_per_survivor.append(
                    sum(1 for d in p.ready_dice + p.unpatched_dice if d.color != DieColor.GRAY)
                )
                secrets_per_survivor.append(p.secrets)
                unpatched_colored_per_survivor.append(
                    sum(1 for d in p.unpatched_dice if d.color != DieColor.GRAY)
                )

        survivors = [x for x in scored if not x[2].is_patient_zero]
        if survivors:
            survivors.sort(key=lambda x: (x[0], x[1]), reverse=True)
            winner = survivors[0][2]
        else:
            scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
            winner = scored[0][2]
        bot_wins[winner.bot_style] += 1

    tot_shields = max(1, sum(shield_commits.values()))
    return {
        "avg_rounds": statistics.mean(rounds_list),
        "v2_compile_round": statistics.mean(v2_rounds) if v2_rounds else None,
        "v2_compile_rate": len(v2_rounds) / num_games,
        "v3_compile_round": statistics.mean(v3_rounds) if v3_rounds else None,
        "v3_compile_rate": len(v3_rounds) / num_games,
        "singularity_pct": 100.0 * singularity_count / num_games,
        "pz_pct": 100.0 * pz_count / num_games,
        "wipeout_pct": 100.0 * wipeout_count / num_games,
        "early_death_pct": 100.0 * early_death_count / num_games,
        "dirty_per_game": statistics.mean(dirty_per_game),
        "rbg_v1": statistics.mean(exited_rbg_by_ver[0]) if exited_rbg_by_ver[0] else 0.0,
        "rbg_v2": statistics.mean(exited_rbg_by_ver[1]) if exited_rbg_by_ver[1] else 0.0,
        "rbg_v3": statistics.mean(exited_rbg_by_ver[2]) if exited_rbg_by_ver[2] else 0.0,
        "shield_share_red": 100.0 * shield_commits[ShieldColor.RED] / tot_shields,
        "shield_share_blue": 100.0 * shield_commits[ShieldColor.BLUE] / tot_shields,
        "shield_share_green": 100.0 * shield_commits[ShieldColor.GREEN] / tot_shields,
        "block_rate_red": 100.0 * cubes_blocked_color[CubeColor.RED] / max(1, cubes_dropped_color[CubeColor.RED]),
        "block_rate_blue": 100.0 * cubes_blocked_color[CubeColor.BLUE] / max(1, cubes_dropped_color[CubeColor.BLUE]),
        "block_rate_green": 100.0 * cubes_blocked_color[CubeColor.GREEN] / max(1, cubes_dropped_color[CubeColor.GREEN]),
        "survivor_tapes": statistics.mean(tapes_per_survivor) if tapes_per_survivor else 0.0,
        "survivor_colored_dice": statistics.mean(colored_dice_per_survivor) if colored_dice_per_survivor else 0.0,
        "survivor_secrets": statistics.mean(secrets_per_survivor) if secrets_per_survivor else 0.0,
        "survivor_unpatched_colored": statistics.mean(unpatched_colored_per_survivor) if unpatched_colored_per_survivor else 0.0,
        "stars_sniped_per_game": statistics.mean(stars_sniped_per_game),
        "shields_knocked_per_game": statistics.mean(shields_knocked_per_game),
        "bot_win_pct": {
            k: 100.0 * bot_wins[k] / max(1, (bot_appearances[k] / params.num_players))
            for k in bot_wins
        },
    }


def main() -> None:
    print("=== 1. CURRENT v0.14.0 BASELINE (3P Table Behavior vs Sim Bots, N=1000) ===")
    b_table = run_v014_baseline(num_players=3, num_games=1000, rational_dirty=True)
    b_bots = run_v014_baseline(num_players=3, num_games=1000, rational_dirty=False)
    for label, d in [("v0.14.0 (3P Human Table - No Bad Dirty Trade)", b_table), ("v0.14.0 (3P Sim Bots)", b_bots)]:
        print(f"\n[{label}]")
        print(f"  Avg Rounds: {d['avg_rounds']:.2f} | v2 Compile: R{d['v2_compile_round']:.2f} ({d['v2_compile_rate']*100:.0f}%) | v3 Compile: R{d['v3_compile_round']:.2f} ({d['v3_compile_rate']*100:.0f}%)")
        print(f"  Endings: Singularity {d['singularity_pct']:.1f}% | Patient Zero {d['pz_pct']:.1f}% | Wipeout {d['wipeout_pct']:.1f}% | Early Death (<=R4) {d['early_death_pct']:.1f}%")
        print(f"  Exited Attack Cubes/Drop: v1={d['rbg_v1']:.2f} -> v2={d['rbg_v2']:.2f} -> v3={d['rbg_v3']:.2f} | Dirty/Game: {d['dirty_per_game']:.2f}")
        print(f"  Shield Commit Share: Red {d['shield_share_red']:.1f}% | Blue {d['shield_share_blue']:.1f}% | Green {d['shield_share_green']:.1f}%")
        print(f"  Survivor End Cash: ${d['survivor_cash']:.2f} | Survivor End Secrets: {d['survivor_secrets']:.2f}")

    print("\n=== 2. CALIBRATED v0.15.0 OVERHAUL SWEEP (2P, 3P, 4P, N=1000 each) ===")
    profiles = [
        ("Target Baseline A (Immediate Compile Drop + ⚡ ON COMPILE, Start Secrets 11/11/13, Track 5/6/6, Pulse 2/2/3)", {2: 11, 3: 11, 4: 13}, {2: 5, 3: 6, 4: 6}, True, True, (2, 2, 3)),
        ("Target Baseline B (Payload to Cup + Immediate ⚡ ON COMPILE, Start Secrets 11/11/13, Track 5/6/6, Pulse 2/2/3)", {2: 11, 3: 11, 4: 13}, {2: 5, 3: 6, 4: 6}, True, False, (2, 2, 3)),
    ]
    for prof_name, s_map, t_map, g_one, imm_drop, pulse in profiles:
        print(f"\n--- {prof_name} ---")
        for np in (2, 3, 4):
            p = V15SimParams(
                num_players=np,
                starting_secrets=s_map,
                vault_cap=14,
                track_capacity=t_map,
                black_pulse_by_ver=pulse,
                dirty_siphon_adds_attack_cube=False,
                green_unpatch_one_plus_wrench=g_one,
                immediate_compile_drop=imm_drop,
            )
            r = run_v015_prototype(p, num_games=1000)
            print(f"\n[v0.15.0 — {np}P (Start Secrets={p.starting_secrets[np]}, Track={p.track_capacity[np]}, Pulse=2/2/3)]")
            v2r = f"R{r['v2_compile_round']:.2f}" if r['v2_compile_round'] else "N/A"
            v3r = f"R{r['v3_compile_round']:.2f}" if r['v3_compile_round'] else "N/A"
            print(f"  Avg Rounds: {r['avg_rounds']:.2f} | v2 Compile: {v2r} ({r['v2_compile_rate']*100:.0f}%) | v3 Compile: {v3r} ({r['v3_compile_rate']*100:.0f}%)")
            print(f"  Endings: Singularity {r['singularity_pct']:.1f}% | Patient Zero {r['pz_pct']:.1f}% | Wipeout {r['wipeout_pct']:.1f}% | Early Death (<=R4) {r['early_death_pct']:.1f}%")
            print(f"  Exited Attack Cubes/Drop: v1={r['rbg_v1']:.2f} -> v2={r['rbg_v2']:.2f} -> v3={r['rbg_v3']:.2f} | Dirty Siphons/Game: {r['dirty_per_game']:.2f}")
            print(f"  Shield Commit Share: Red {r['shield_share_red']:.1f}% | Blue {r['shield_share_blue']:.1f}% | Green {r['shield_share_green']:.1f}%")
            print(f"  Cube Block Rate:     Red {r['block_rate_red']:.1f}% | Blue {r['block_rate_blue']:.1f}% | Green {r['block_rate_green']:.1f}%")
            print(f"  Pre-Trigger Knockouts/Game: Phase 2 Shields Knocked={r['shields_knocked_per_game']:.2f} | Phase 3 ★ Sniped={r['stars_sniped_per_game']:.2f}")
            print(f"  Survivor End State: Secrets={r['survivor_secrets']:.2f} | Colored Dice={r['survivor_colored_dice']:.2f} (Unpatched={r['survivor_unpatched_colored']:.2f}) | Archived Tapes={r['survivor_tapes']:.2f}")


if __name__ == "__main__":
    main()
