"""v0.48 Sprint Plan (docs/specs/sprint_plan_spec.md §5-§6): pure helpers and the Sprint Review.

Sim identifiers keep their legacy names (``scanned_dice`` = the Sprint Plan). A die in ``scanned_dice`` whose
id is in ``PlayerState.current_sprint_ids`` is in the Current Sprint; every other die there is in the Next Sprint.
Nothing here draws from the RNG. Every entry point is gated on ``config.sprint_plan_enabled`` by its caller.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Tuple

from sim.config import DieColor

if TYPE_CHECKING:
    from sim.engine.core import GameEngine
    from sim.engine.state import GameState, PlayerState
    from sim.entities import Die


def enabled(cfg: Any) -> bool:
    return bool(getattr(cfg, "sprint_plan_enabled", False))


def current_sprint(p: "PlayerState") -> List["Die"]:
    return [d for d in p.scanned_dice if d.die_id in p.current_sprint_ids]


def next_sprint(p: "PlayerState") -> List["Die"]:
    return [d for d in p.scanned_dice if d.die_id not in p.current_sprint_ids]


def prune(p: "PlayerState") -> None:
    p.current_sprint_ids &= {d.die_id for d in p.scanned_dice}


def prune_all(state: "GameState") -> None:
    for p in state.players:
        prune(p)


def mark_current(p: "PlayerState", dice: Iterable["Die"]) -> None:
    p.current_sprint_ids.update(d.die_id for d in dice)


def reset_after_review(p: "PlayerState") -> None:
    p.current_sprint_ids = {d.die_id for d in p.scanned_dice}


def forced_count(p: "PlayerState") -> int:
    return min(len(current_sprint(p)), p.effective_release_bandwidth)


def owned_gray(p: "PlayerState") -> List[Tuple[str, "Die"]]:
    """(zone, die) over R&D, Sprint Plan (Next, then Current), In Production, Ready: the default thinning order
    R&D -> Next Sprint -> In Production -> Current Sprint -> Ready, list order within each zone."""
    out: List[Tuple[str, "Die"]] = []
    zones = (("glitched", p.glitched_dice), ("next", next_sprint(p)), ("in_production", p.in_production_dice),
             ("current", current_sprint(p)), ("ready", p.ready_for_release_dice))
    for name, dice in zones:
        out.extend((name, d) for d in dice if d.color == DieColor.GRAY)
    return out


def _by_id(dice: Iterable["Die"]) -> Dict[int, "Die"]:
    return {d.die_id: d for d in dice}


def _validate(pool: List["Die"], requested: Optional[Iterable[Any]], n: int, backfill: bool) -> List["Die"]:
    """``validate_graduate_ids`` semantics restricted to ``pool``: dedupe, ignore unknown / other-sprint ids, cap at n."""
    from sim.engine.phase5_pipeline_shift import default_graduate_priority

    n = max(0, n)
    by_id = _by_id(pool)
    chosen: List["Die"] = []
    seen = set()
    for item in list(requested or []):
        if len(chosen) >= n:
            break
        did = getattr(item, "die_id", item)
        try:
            did = int(did)
        except (TypeError, ValueError):
            continue
        if did in seen or did not in by_id:
            continue
        seen.add(did)
        chosen.append(by_id[did])
    if backfill:
        for d in default_graduate_priority(pool):
            if len(chosen) >= n:
                break
            if d.die_id not in seen:
                seen.add(d.die_id)
                chosen.append(d)
    return chosen


def check_picks(p: "PlayerState", cur_ids: Iterable[int], next_ids: Iterable[int]) -> List[str]:
    """Error strings for a human's Sprint Review picks (empty list = legal)."""
    cur, nxt = current_sprint(p), next_sprint(p)
    bw = p.effective_release_bandwidth
    forced = min(len(cur), bw)
    spare = bw - forced
    cur_ids, next_ids = list(cur_ids), list(next_ids)
    errs: List[str] = []
    cur_set, next_set = {d.die_id for d in cur}, {d.die_id for d in nxt}
    for label, ids, own, other in (("Current Sprint", cur_ids, cur_set, next_set),
                                   ("Next Sprint", next_ids, next_set, cur_set)):
        if len(set(ids)) != len(ids):
            errs.append(f"duplicate die ids in {label} picks")
        for did in ids:
            if did in own:
                continue
            errs.append(f"die {did} is not in the {label}" if did in other else f"unknown die id {did}")
    if len(cur_ids) != forced:
        errs.append(f"must graduate exactly {forced} Current Sprint dice, got {len(cur_ids)}")
    need = min(spare, len(nxt))
    if len(next_ids) > spare:
        errs.append("no spare Release Bandwidth for Next Sprint picks" if spare <= 0
                    else f"at most {spare} Next Sprint dice may graduate, got {len(next_ids)}")
    elif len(next_ids) < need:
        errs.append(f"must graduate exactly {need} Next Sprint dice to fill Release Bandwidth, got {len(next_ids)}")
    return errs


def _tel(engine: "GameEngine", key: str) -> Dict[int, Any]:
    return engine.state.sprint_round.setdefault(key, {})


def sprint_review(engine: "GameEngine", p: "PlayerState", chosen_die_ids: Optional[List[int]] = None) -> List["Die"]:
    """Phase 6 Sprint Review (spec §6.2; User ruling 2026-11-19): exactly ``min(bw, |Sprint Plan|)`` dice graduate,
    Current Sprint first, then Next Sprint dice to fill the rest (both back-filled when a pick list is short)."""
    from sim.engine.phase5_pipeline_shift import reset_die_for_pipeline

    prune(p)
    bw = p.effective_release_bandwidth
    cur, nxt = current_sprint(p), next_sprint(p)
    forced = min(len(cur), bw)
    spare = bw - forced
    pid = p.player_id
    _tel(engine, "sprint_current_by_player")[pid] = len(cur)
    _tel(engine, "sprint_next_by_player")[pid] = len(nxt)
    _tel(engine, "sprint_current_over_bw_by_player")[pid] = len(cur) > bw

    cur_ids: List[int]
    next_ids: List[int]
    if chosen_die_ids is None:
        hook = getattr(p.bot, "choose_sprint_graduates", None)
        if hook is not None:
            cur_ids, next_ids = hook(p, list(cur), list(nxt), bw, engine.state, engine.rng)
        else:
            from sim.engine.phase5_pipeline_shift import default_graduate_priority

            cur_ids = [d.die_id for d in default_graduate_priority(cur)[:forced]]
            next_ids = [d.die_id for d in default_graduate_priority(nxt)[:spare]]
    else:
        cset = {d.die_id for d in cur}
        nset = {d.die_id for d in nxt}
        raw = list(chosen_die_ids)
        ids = [int(getattr(x, "die_id", x)) for x in raw]
        cur_ids = [i for i in ids if i in cset]
        next_ids = [i for i in ids if i in nset]
    cur_pick = _validate(cur, cur_ids, forced, backfill=True)
    next_pick = _validate(nxt, next_ids, spare, backfill=True)  # full throughput is mandatory
    graduates = cur_pick + next_pick

    for die in graduates:
        p.scanned_dice.remove(die)
        reset_die_for_pipeline(die)
        p.ready_for_release_dice.append(die)

    # streaks / histograms (probe definition): pop on graduation, drop ids that left, +1 for each die left behind
    sk = p.sprint_wait_streak
    for d in graduates:
        w = sk.pop(d.die_id, 0)
        p.sprint_wait_hist["gray" if d.color == DieColor.GRAY else "colored"][min(w, 4)] += 1
    left = list(p.scanned_dice)
    live = {d.die_id for d in left}
    for k in [k for k in sk if k not in live]:
        sk.pop(k)
    for d in left:
        sk[d.die_id] = sk.get(d.die_id, 0) + 1
        cls = "gray" if d.color == DieColor.GRAY else "colored"
        p.sprint_max_streak[cls] = max(p.sprint_max_streak[cls], sk[d.die_id])

    reset_after_review(p)
    _tel(engine, "sprint_grad_current_by_player")[pid] = len(cur_pick)
    _tel(engine, "sprint_grad_next_by_player")[pid] = len(next_pick)
    _tel(engine, "sprint_left_by_player")[pid] = len(left)
    _tel(engine, "gray_ready_by_player")[pid] = sum(d.color == DieColor.GRAY for d in p.ready_for_release_dice)
    _tel(engine, "gray_owned_by_player")[pid] = len(owned_gray(p))
    return graduates


def record_roll(engine: "GameEngine", p: "PlayerState", active_dice: List["Die"]) -> None:
    """Phase 1 roll telemetry (spec §8): Gray / colored dice rolled and ⚠ kept per class."""
    from sim.engine.vulnerability import face_vuln

    pid = p.player_id
    for key in ("gray_rolled_by_player", "colored_rolled_by_player", "gray_vuln_kept_by_player",
                "colored_vuln_kept_by_player"):
        _tel(engine, key).setdefault(pid, 0)
    for d in active_dice:
        gray = d.color == DieColor.GRAY
        rolled = _tel(engine, "gray_rolled_by_player" if gray else "colored_rolled_by_player")
        rolled[pid] += 1
        v = face_vuln(d.current_face)
        if v:
            _tel(engine, "gray_vuln_kept_by_player" if gray else "colored_vuln_kept_by_player")[pid] += v
