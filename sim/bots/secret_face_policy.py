"""v0.38.0 candidate bot policy for Secret faces, Processing Box banking and Glitched Shield Slots
(spec v380 §9). ``[TUNE-BOT]`` heuristics, not rules.

Everything is a pure function of the game state: no RNG is drawn and nothing is cached on the bot (H5), so the
reference bot's rollout clones and the Mixed policy stay valid. Only called when ``config.secret_face_enabled``
(or ``glitched_shield_slots_enabled`` for the slot hooks), so the v0.37 path is untouched.

Archetype flavour comes from the class attribute ``secret_face_color_bias`` (``DieColor -> bonus``) on each bot
and ``follows_company_color`` (AdaptiveBalanced).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sim.config import CubeColor, DieColor
from sim.engine import secret_faces as sf

if TYPE_CHECKING:
    from sim.engine.state import GameState, PlayerState
    from sim.entities import Die, Face

SECRET_VALUE = 3.0  # money-equivalent of 1 Corporate Secret [TUNE-BOT]
RESEARCH_VALUE = 1.0
SHARE_VALUE = 1.0
SHIELD_VALUE = 1.5
MARKET_COLORS = (DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW)


# ---------------------------------------------------------------------------
# Banking expectations
# ---------------------------------------------------------------------------
def bank_probability(player: "PlayerState", state: "GameState", queue_pos: int) -> float:
    """P(a die entering the Processing Box at ``queue_pos`` banks before game end). Uses public state only."""
    p = 1.0 if queue_pos < player.triage_bandwidth else 0.6
    if getattr(state, "is_final_round", False):
        return 1.0 if queue_pos < player.triage_bandwidth else 0.0
    # Singularity risk: last Version near a full Corruption Track (dice rolled this round would strand)
    if state.current_version_index >= len(state.version_deck) - 1:
        left = state.corruption_track_capacity - state.corruption_track
        blacks = int(state.staging_cup.get(CubeColor.BLACK, 0)) + int(state.tower.stuck_cubes.get(CubeColor.BLACK, 0))
        if left <= max(1, blacks):
            p *= 0.4
        elif left <= blacks + 2:
            p *= 0.8
    return p


def expected_bank_value(player: "PlayerState", state: "GameState", color: Any, queue_pos: int) -> float:
    cfg = state.config
    if getattr(cfg, "is_red_secret_payout", False) and DieColor(color) == DieColor.RED:
        return red_secret_face_value(player, state) * bank_probability(player, state, queue_pos) * SECRET_VALUE
    return sf.secret_yield(state.config, player, color) * bank_probability(player, state, queue_pos) * SECRET_VALUE


def red_secret_face_value(player: "PlayerState", state: "GameState") -> float:
    """RSP-1 (spec §14.5.6): owner yield + q x expected payout at the own share, q = P(no other Red bank this
    round) — the marginal payout this die enables. In Corporate Secrets, before the bank probability."""
    from sim.bots import market_share_policy as msp

    sched = state.config.red_secret_payout_schedule(len(state.players))
    rivals = [int(q.market_share or 0) for q in state.players
              if q.player_id != player.player_id and not q.is_patient_zero]
    q = 1.0
    for o in state.players:
        if o.player_id != player.player_id:
            q *= 1.0 - msp.p_red_bank(o, state)
    own = sf.secret_yield(state.config, player, DieColor.RED)
    return own + q * msp.expected_payout_value(int(player.market_share or 0), rivals, sched)


def share_value(player: "PlayerState", state: Optional["GameState"], n: int, share: Optional[int] = None) -> float:
    """Money-equivalent of +n Market Share (clamped at the maximum): base, Red yield tier crossings for owned /
    pending Red dice, Market Collapse risk (when enabled) and the expected Market Leader Bonus."""
    share = int(player.market_share or 0) if share is None else int(share)
    gain = max(0, min(int(n), int(player.market_share_max or 0) - share))
    if gain <= 0:
        return 0.0
    v = SHARE_VALUE * gain
    if state is None or state.config.die_face_profile == "V038_DRAFT":
        return v  # v038() / v038_roster() keep the first-sweep valuation (reproducibility)
    cfg = state.config
    red_w = _pending(player, DieColor.RED) + 0.3 * _owned(player, DieColor.RED)
    for k in range(1, gain + 1):
        v += SECRET_VALUE * red_w * _red_tier_drop(cfg, share + k)
    if getattr(cfg, "market_collapse_enabled", False):
        from sim.bots.market_share_policy import red_pressure

        if share == 0:
            v += 4.0
        elif share <= red_pressure(state) + 2:
            v += 2.0
    from sim.bots import market_share_policy as msp

    pol = msp.DEFAULT_POLICY
    if msp.leader_bonus_active(player, state, pol):
        from sim.engine.market_share import expected_market_leader_bonus

        sched = cfg.market_leader_bonus_schedule(len(state.players))
        rivals = [int(q.market_share or 0) for q in state.players
                  if q.player_id != player.player_id and not q.is_patient_zero]
        d = expected_market_leader_bonus(share + gain, rivals, sched) - expected_market_leader_bonus(share, rivals, sched)
        v += msp.leader_bonus_time_weight(state, pol) * SECRET_VALUE * d
    if msp.payout_active(player, state, pol):
        v += SECRET_VALUE * msp.payout_share_delta(player, state, share, share + gain, None, pol)  # RSP-1 (spec §14.5.6)
    return v


def face_value(player: "PlayerState", face: Optional["Face"], state: Optional["GameState"] = None) -> float:
    """Money-equivalent of a non-Secret face (choice faces: best option)."""
    if face is None or face.is_glitch:
        return 0.0
    if face.is_choice:
        return max(face_value(player, c, state) for c in face.choices)
    v = face.money + RESEARCH_VALUE * face.patches + SECRET_VALUE * face.secrets
    if face.market_share:
        v += share_value(player, state, face.market_share)
    if face.clean_slots and player.glitched_shield_slots > 0:
        v += SHIELD_VALUE
    if face.is_shield:
        v += SHIELD_VALUE * face.block_amount
    if face.is_star:
        v += 1.5
        if getattr(face, "star_code", None) == "G2":
            if state is not None and getattr(state.config, "variant_profile", None) == "V038_DRAFT":
                glitches = getattr(player, "glitched_shield_slots", 0)
                multiplier = getattr(state.config, "g2_glitch_bonus", 1)
                v += RESEARCH_VALUE * glitches * multiplier
    return v


def mean_reroll_value(player: "PlayerState", state: "GameState", die: "Die", queue_pos: int) -> float:
    vals = []
    for f in die.faces:
        if f.secrets_pending:
            vals.append(expected_bank_value(player, state, die.color, queue_pos))
        else:
            vals.append(face_value(player, f, state))
    return sum(vals) / len(vals) if vals else 0.0


def adjust_rerolls(bot: Any, player: "PlayerState", dice: List["Die"], indices: List[int], state: "GameState",
                   rerolls_remaining: int) -> List[int]:
    """Phase 1 reroll post-process: keep a Secret face when its bank value beats a reroll; reroll a Secret face that
    is worth less (e.g. Red at Market Share 0, Green with 3 glitched slots). Archetypes that chase Secret faces
    (``secret_face_chaser``) always keep them."""
    out = [i for i in indices if 0 <= i < len(dice)]
    queue = len(player.glitched_dice)
    chaser = bool(getattr(bot, "secret_face_chaser", False))
    for i, d in enumerate(dice):
        f = d.current_face
        if f is None or not f.secrets_pending:
            continue
        keep_v = expected_bank_value(player, state, d.color, queue)
        roll_v = mean_reroll_value(player, state, d, queue)
        if chaser or keep_v >= roll_v:
            out = [j for j in out if j != i]
            queue += 1
        elif i not in out and not d.is_locked:
            out.append(i)
    return out


# ---------------------------------------------------------------------------
# Phase 1 Step 5
# ---------------------------------------------------------------------------
def adjust_declared_choices(bot: Any, player: "PlayerState", dice: List["Die"], declared: Dict[int, int],
                            state: "GameState") -> Dict[int, int]:
    """Choice faces whose first option is wasted: Clean with no glitched slot -> +$1; +1 Market Share at the
    maximum -> +$1."""
    out = dict(declared or {})
    for i, d in enumerate(dice):
        f = d.current_face
        if f is None or not f.is_choice or not f.choices:
            continue
        first = f.choices[0]
        if first.clean_slots:
            out[i] = 0 if player.glitched_shield_slots > 0 else 1
        elif any(c.market_share for c in f.choices):
            vals = [face_value(player, c, state) for c in f.choices]
            out[i] = max(range(len(vals)), key=lambda k: (vals[k], -k))
    return out


def choose_slot_cleaners(player: "PlayerState", dice: List["Die"], candidates: List[int], slots: int,
                         state: "GameState") -> List[int]:
    """Place shield-icon dice on glitched slots while that does not reduce this round's shields (k > E), plus one
    more when Green Secrets are pending (each slot costs 1 Green Secret). White Contractors first, then Gray,
    then Purple."""
    def key(i: int):
        d = dice[i]
        return (0 if d.color == DieColor.WHITE else (1 if d.color == DieColor.GRAY else 2), d.die_id)

    order = sorted(candidates, key=key)
    k = len(order)
    eff = sf.effective_capacity(player)
    s = int(slots)
    chosen: List[int] = []
    green_pending = sum(1 for d in player.glitched_dice
                        if getattr(d, "secret_pending", False) and d.color == DieColor.GREEN)
    for i in order:
        if s <= 0:
            break
        if k > eff or (green_pending and not chosen and k >= 1):
            chosen.append(i)
            k -= 1
            eff += 1
            s -= 1
        else:
            break
    return chosen


def choose_triage_order(player: "PlayerState", dice: List["Die"], state: "GameState") -> List["Die"]:
    return sf.default_triage_order(state.config, player, dice)


# ---------------------------------------------------------------------------
# Phase 4 Generic shield valuation (called from market_share_policy.marginal_block_value)
# ---------------------------------------------------------------------------
def _pending(player: "PlayerState", color: DieColor) -> int:
    return sum(1 for d in player.glitched_dice if getattr(d, "secret_pending", False) and d.color == color)


def _red_tier_drop(cfg: Any, share: int) -> int:
    """Red yield lost when Market Share drops from ``share`` to ``share - 1``."""
    if getattr(cfg, "red_secret_owner_yield", None) is not None:
        return 0  # RSP-1: flat owner yield, no tiers
    def y(s: int) -> int:
        for m, v in cfg.secret_yield_red_tiers:
            if s >= m:
                return v
        return 0
    return y(share) - y(max(0, share - 1))


def marginal_block_value(color: CubeColor, rem: Dict[CubeColor, int], player: "PlayerState", state: "GameState",
                         attack: Dict[CubeColor, int], base: float) -> float:
    """v0.38 additions on top of the v0.37 marginal value ``base``."""
    cfg = state.config
    r = int(rem.get(color, 0))
    if r <= 0:
        return base
    if color == CubeColor.BLUE:
        # If blue_block_bonus is 0 (v0.38e), no heuristic bonus is added;
        # Blue cubes are blocked solely to prevent immediate secret theft.
        if cfg.secret_yield_blue_block_bonus > 0:
            first_block = r >= int((attack or {}).get(CubeColor.BLUE, r))  # no Blue blocked yet this round
            if player.blocked_blue_this_round == 0 and _pending(player, DieColor.BLUE) and first_block:
                base += SECRET_VALUE * cfg.secret_yield_blue_block_bonus * min(_pending(player, DieColor.BLUE),
                                                                            player.triage_bandwidth)
        return base
    if color == CubeColor.GREEN:
        if player.glitched_shield_slots >= player.defense_capacity:
            return 0.0  # excess Green has no effect
        v = SHIELD_VALUE
        # If green_glitch_penalty is False (v0.38e), glitched slots do NOT reduce
        # Secret yield; Green is blocked solely to defend Shield Capacity.
        if getattr(cfg, "secret_yield_green_glitch_penalty", True) and player.glitched_shield_slots < cfg.secret_yield_green_base:
            v += SECRET_VALUE * min(_pending(player, DieColor.GREEN) + _owned(player, DieColor.GREEN) * 0.2,
                                    player.triage_bandwidth)
        return v
    # Red: the v0.37 value minus the (disabled) Market Collapse premium, plus the Red Secret tier crossing
    v = base
    share = int(player.market_share or 0)
    if not cfg.market_collapse_enabled and share - r <= 0:
        v -= 6.0  # MarketSharePolicy.red_collapse_value: Market Collapse is off under v0.38
        v += 1.0
    drop = _red_tier_drop(cfg, max(0, share - r + 1))
    if drop:
        v += SECRET_VALUE * drop * (_pending(player, DieColor.RED) + 0.3 * _owned(player, DieColor.RED))
    return v


def _owned(player: "PlayerState", color: DieColor) -> int:
    return sum(1 for d in player.total_dice if d.color == color)


# ---------------------------------------------------------------------------
# Phase 6 purchases
# ---------------------------------------------------------------------------
def color_score(bot: Any, player: "PlayerState", state: "GameState", color: DieColor) -> float:
    """Expected money-equivalent per roll of a new die of ``color`` (Secret face weighted by its current yield)."""
    from sim.entities import create_colored_die

    cfg = state.config
    die = create_colored_die(color=color, die_id=-1, variant_card=state.variant_cards.get(color),
                             face_profile=cfg.die_face_profile)
    if color == DieColor.YELLOW and cfg.die_face_profile in ("V038_YELLOW_MS", "V038_YELLOW_MS_ALT", "V038_YELLOW_MS_F3", "V038D"):
        v = yellow_ms_score(player, state, die)
    else:
        v = mean_reroll_value(player, state, die, len(player.glitched_dice))
    if color == DieColor.GREEN:
        v -= 0.3 * player.glitched_shield_slots
    bias = getattr(bot, "secret_face_color_bias", None) or {}
    v += float(bias.get(color, 0.0))
    if getattr(bot, "follows_company_color", False) and player.company_color == color.value:
        v += 0.75
    return v


def projected_share(player: "PlayerState", state: "GameState") -> int:
    """Market Share the die will meet when it is rolled: current share minus the Red pressure expected before then
    (one round of staged + stuck Red split across the survivors, at least 1)."""
    from sim.bots.market_share_policy import red_pressure

    alive = max(1, sum(1 for q in state.players if not q.is_patient_zero))
    return max(0, int(player.market_share or 0) - max(1, red_pressure(state) // alive))


def yellow_ms_score(player: "PlayerState", state: "GameState", die: "Die") -> float:
    """V038_YELLOW_MS purchase value: Market Share faces priced at the projected share (Market Collapse avoidance,
    Market Leader Bonus place, Red tier support via ``share_value``), Money / research faces as usual."""
    at = projected_share(player, state)
    vals = []
    for f in die.faces:
        opts = f.choices if f.is_choice else (f,)
        best = 0.0
        for o in opts:
            v = o.money + RESEARCH_VALUE * o.patches + SECRET_VALUE * o.secrets
            if o.market_share:
                v += share_value(player, state, o.market_share, share=at)
            if o.is_star:
                v += 1.5
            best = max(best, v)
        vals.append(best)
    return sum(vals) / len(vals)


def adjust_purchases(bot: Any, plan: Any, player: "PlayerState", state: "GameState") -> Any:
    """Re-target each planned Central Market colour to the best-scored colour in stock that fits the budget."""
    planned = list(getattr(plan, "market_purchases", []) or [])
    if not planned:
        return plan
    budget = int(player.money)
    if getattr(plan, "use_b2_secret", False) and player.b2_available:
        budget -= int(state.config.b2_secret_cost)
    stock = dict(state.market)
    scores = {c: color_score(bot, player, state, c) for c in MARKET_COLORS}
    out = []
    for c in planned:
        if c not in MARKET_COLORS:
            out.append(c)
            continue
        best = None
        for cand in sorted(MARKET_COLORS, key=lambda x: (-scores[x], x.value)):
            if stock.get(cand, 0) > 0 and state.get_market_die_cost(cand) <= budget:
                best = cand
                break
        pick = best or c
        out.append(pick)
        stock[pick] = stock.get(pick, 0) - 1
        budget -= state.get_market_die_cost(pick)
    plan.market_purchases = out
    return plan


# ---------------------------------------------------------------------------
# Brute-Force Bypass (Helix) face choice
# ---------------------------------------------------------------------------
def helix_face_override(player: "PlayerState", dice: List["Die"], state: "GameState"):
    """Best (index, face) improvement; the Secret face is allowed (OQ-10) and valued at its bank value."""
    best, best_gain = None, 0.0
    queue = len(player.glitched_dice)
    for i, d in enumerate(dice):
        cur = d.current_face
        if cur is None:
            continue
        cur_v = (expected_bank_value(player, state, d.color, queue) if cur.secrets_pending
                 else face_value(player, cur, state))
        for f in d.faces:
            if f.is_star or f.is_glitch:
                continue
            v = expected_bank_value(player, state, d.color, queue) if f.secrets_pending else face_value(player, f, state)
            if v - cur_v > best_gain:
                best, best_gain = (i, f), v - cur_v
    return best
