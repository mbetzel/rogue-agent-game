"""v0.52.0 Market Share position (docs/specs/ms_stack_order_spec.md).

Every Market Share marker (each player, plus SETEC Corp in 2P) has one integer arrival sequence (``seq``). On a
space a higher ``seq`` sits higher, so the rank key of a marker is ``(space, seq)`` compared descending and there
are no ties (INV-MS-STACK-01). A marker that moves on its own lands on top of its new space (``seq`` becomes the
new global maximum). Markers that move in the same simultaneous batch keep their previous relative order and land
above the markers that did not move (``begin`` / ``end``). The stack is fully determined by seat order and move
order: **no RNG is drawn anywhere** (INV-MS-RNG-01). Telemetry is passive (INV-MS-TEL-01).

Code identifiers here are never player-facing terms (spec section 0).
"""

from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

SETEC_CORP_ID = -1  # same value as sim.engine.market_share.SETEC_CORP_ID (no import cycle)

if TYPE_CHECKING:
    from sim.engine.state import GameState


# ---------------------------------------------------------------------------
# Telemetry (spec section 8)
# ---------------------------------------------------------------------------
class MsTieTelemetry:
    """Counters for the ``ms_tie`` end block. Plain dicts / ints so ``fast_clone`` copies them."""

    SCALARS = (
        "mlb_awards", "mlb_raw_tie_1st", "mlb_effective_tie_1st", "mlb_effective_tie_paid", "mlb_stack_decided_paid",
        "rounds_obs", "top_same_space", "top_same_space_at_max", "any_same_space",
        "lead_changes", "lead_back", "lead_changes_same_space",
        "poach_stack_decided", "sig_red_stack_decided", "setec_arrivals_on_top",
    )
    BY_KEY = ("mlb_first_by_seat", "mlb_secrets_by_seat", "arrivals_occupied", "overtakes")

    def __init__(self) -> None:
        self.c: Dict[str, int] = {k: 0 for k in self.SCALARS}
        self.by: Dict[str, Dict[Any, int]] = {k: {} for k in self.BY_KEY}
        self.leader: Optional[int] = None
        self.leader_prev: Optional[int] = None

    def add(self, key: str, n: int = 1) -> None:
        self.c[key] = self.c.get(key, 0) + n

    def add_by(self, group: str, k: Any, n: int = 1) -> None:
        d = self.by[group]
        d[k] = d.get(k, 0) + n

    def snapshot(self) -> "MsTieTelemetry":
        t = MsTieTelemetry()
        t.c = dict(self.c)
        t.by = {k: dict(v) for k, v in self.by.items()}
        t.leader, t.leader_prev = self.leader, self.leader_prev
        return t

    def as_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = dict(self.c)
        for k, v in self.by.items():
            out[k] = dict(sorted(v.items(), key=lambda kv: str(kv[0])))
        return out


def _ms_places_by_share(shares: Dict[int, int]) -> Dict[int, int]:
    vals = list(shares.values())
    return {pid: 1 + sum(1 for v in vals if v > s) for pid, s in shares.items()}


def record_mlb_award(tel: Optional[MsTieTelemetry], state: Any, shares: Dict[int, int],
                     awards: Dict[int, Tuple[int, int]], schedule: Sequence[int]) -> None:
    """One Market Leader Bonus award fired (per-round or end). ``shares`` includes SETEC Corp; ``awards`` is
    pid -> (place, bonus). Pure bookkeeping, computed identically with stacking on or off."""
    if tel is None or not shares:
        return
    n = len(state.players)
    first = getattr(state, "first_player_index_start", getattr(state, "first_player_index", 0))
    seat_of = {p.player_id: (i - first) % n for i, p in enumerate(state.players)}
    tel.add("mlb_awards")
    v = sorted(shares.values(), reverse=True)
    if len(v) > 1 and v[0] == v[1]:
        tel.add("mlb_raw_tie_1st")
    places = [pl for pl, _ in awards.values()]
    if places.count(1) > 1:
        tel.add("mlb_effective_tie_1st")
    groups: Dict[int, int] = {}
    for pl, bonus in awards.values():
        groups.setdefault(pl, 0)
        groups[pl] += 1
    sched = list(schedule)
    if any(sz >= 2 and 0 <= pl - 1 < len(sched) and sched[pl - 1] > 0 for pl, sz in groups.items()):
        tel.add("mlb_effective_tie_paid")
    at = lambda i: int(sched[i]) if 0 <= i < len(sched) else 0  # noqa: E731
    if any(v[i] == v[i + 1] and at(i) != at(i + 1) for i in range(len(v) - 1)):
        tel.add("mlb_stack_decided_paid")
    for pid, (pl, bonus) in awards.items():
        if pid == SETEC_CORP_ID or pid not in seat_of:
            continue
        if pl == 1:
            tel.add_by("mlb_first_by_seat", seat_of[pid])
        if bonus > 0:
            tel.add_by("mlb_secrets_by_seat", seat_of[pid], int(bonus))


# ---------------------------------------------------------------------------
# The stack
# ---------------------------------------------------------------------------
class MarketShareStack:
    """Arrival-sequence stack (spec section 3). ``seq`` is unique per marker; ``space`` mirrors Market Share."""

    def __init__(self) -> None:
        self.seq: Dict[int, int] = {}
        self.space: Dict[int, int] = {}
        self.counter: int = 0
        self.batch_tag: Optional[str] = None
        self._batch_start: Dict[int, Tuple[int, int]] = {}
        self.tel: Optional[MsTieTelemetry] = None
        self._players: Dict[int, Any] = {}  # marker id -> PlayerState (liveness reads only)

    # -- construction ---------------------------------------------------
    @classmethod
    def setup(cls, seat_order_from_first: List[int], start_space: int, setec_space: Optional[int]) -> "MarketShareStack":
        """Seat k (0 = the First Player) gets ``seq = k + 1`` (bottom -> top); SETEC Corp (2P) ``seq 0`` alone."""
        st = cls()
        for k, mid in enumerate(seat_order_from_first):
            st.seq[mid] = k + 1
            st.space[mid] = int(start_space)
        st.counter = len(seat_order_from_first)
        if setec_space is not None:
            st.seq[SETEC_CORP_ID] = 0
            st.space[SETEC_CORP_ID] = int(setec_space)
        return st

    def is_live(self, mid: int) -> bool:
        p = self._players.get(mid)
        return p is None or not p.is_patient_zero

    def live_ids(self) -> List[int]:
        return [m for m in self.seq if self.is_live(m)]

    # -- moves ----------------------------------------------------------
    def on_move(self, mid: int, before: int, after: int, source: str) -> None:
        if before == after or mid not in self.seq:
            return
        if self.batch_tag is not None:
            if mid not in self._batch_start:
                self._batch_start[mid] = (int(before), self.seq[mid])
            self.space[mid] = int(after)
            return
        t = self.tel
        if t is not None:
            occupied = [m for m in self.live_ids() if m != mid and self.space[m] == after]
            if occupied:
                t.add_by("arrivals_occupied", source)
                if mid == SETEC_CORP_ID:
                    t.add("setec_arrivals_on_top")
            old = (before, self.seq[mid])
            above = [m for m in self.live_ids() if m != mid and (self.space[m], self.seq[m]) > old]
        self.counter += 1
        self.seq[mid] = self.counter
        self.space[mid] = int(after)
        if t is not None:
            n_over = sum(1 for m in above if (self.space[m], self.seq[m]) < (after, self.counter))
            if n_over:
                t.add_by("overtakes", source, n_over)

    def begin(self, tag: str) -> None:
        if self.batch_tag is not None:
            raise RuntimeError(f"Market Share batch {self.batch_tag!r} is open; cannot begin {tag!r} (INV-MS-STACK-09)")
        self.batch_tag = tag
        self._batch_start = {}

    def ensure(self, tag: str) -> None:
        """Opens ``tag`` unless it is already open (lazy opener for the web path)."""
        if self.batch_tag == tag:
            return
        self.begin(tag)

    def end(self) -> None:
        if self.batch_tag is None:
            return
        tag = self.batch_tag
        movers = [(start, m) for m, start in self._batch_start.items() if self.space[m] != start[0]]
        movers.sort()  # by start key (start_space, start_seq) ascending; seq values are unique
        t = self.tel
        pre: Dict[int, Tuple[int, int]] = {}
        if t is not None:
            for m in self.seq:
                pre[m] = self._batch_start[m] if m in self._batch_start else (self.space[m], self.seq[m])
        self.batch_tag = None
        self._batch_start = {}
        for _, m in movers:
            self.counter += 1
            self.seq[m] = self.counter
        if t is not None and movers:
            live = self.live_ids()
            for _, m in movers:
                if any(x != m and self.space[x] == self.space[m] for x in live):
                    t.add_by("arrivals_occupied", tag)
                post_m = (self.space[m], self.seq[m])
                n_over = sum(1 for x in live if x != m and pre[x] > pre[m] and (self.space[x], self.seq[x]) < post_m)
                if n_over:
                    t.add_by("overtakes", tag, n_over)

    # -- reads (raise while a batch is open: INV-MS-STACK-09) -------------
    def _check_closed(self) -> None:
        if self.batch_tag is not None:
            raise RuntimeError(f"Market Share batch {self.batch_tag!r} is open; ranking reads are not allowed (INV-MS-STACK-09)")

    def key(self, mid: int) -> Tuple[int, int]:
        self._check_closed()
        return (self.space[mid], self.seq[mid])

    def order(self, mids: Iterable[int]) -> List[int]:
        self._check_closed()
        return sorted(mids, key=lambda m: (self.space[m], self.seq[m]), reverse=True)

    def highest(self, mids: Iterable[int]) -> int:
        return self.order(mids)[0]

    def lowest(self, mids: Iterable[int]) -> int:
        return self.order(mids)[-1]

    def height(self, mid: int, live: Iterable[int]) -> int:
        """1 = bottom of its space among ``live`` markers."""
        self._check_closed()
        sp, sq = self.space[mid], self.seq[mid]
        return 1 + sum(1 for m in live if m != mid and self.space[m] == sp and self.seq[m] < sq)

    def audit(self, state: Any) -> None:
        """INV-MS-STACK-10 / -01: every marker's space equals its real Market Share; seq values are unique."""
        for p in state.players:
            if p.market_share is not None and self.space.get(p.player_id) != p.market_share:
                raise AssertionError(
                    f"Market Share stack out of sync for player {p.player_id}: stack {self.space.get(p.player_id)} "
                    f"vs real {p.market_share} (a direct write bypassed the hook)")
        if SETEC_CORP_ID in self.seq and self.space[SETEC_CORP_ID] != int(state.setec_market_share):
            raise AssertionError("Market Share stack out of sync for SETEC Corp")
        if len(set(self.seq.values())) != len(self.seq):
            raise AssertionError("Market Share stack sequence numbers are not unique (INV-MS-STACK-01)")


# ---------------------------------------------------------------------------
# State-level helpers (all no-ops when ``state.ms_stack is None``)
# ---------------------------------------------------------------------------
def build_for_state(state: "GameState", config: Any) -> Optional[MarketShareStack]:
    """Setup (spec 3.3): called once from the engine after ``setec_corp_active`` is set. No RNG."""
    if not getattr(config, "market_share_stacking", False):
        return None
    n = len(state.players)
    order = [state.players[(state.first_player_index + k) % n].player_id for k in range(n)]
    if config.market_share_stack_setup == "FIRST_SEAT_TOP":
        order = list(reversed(order))
    start = int(state.players[0].market_share)
    st = MarketShareStack.setup(order, start, 0 if state.setec_corp_active else None)
    st._players = {p.player_id: p for p in state.players}
    state.ms_stack = st
    for p in state.players:
        p.ms_stack = st
    return st


def on_move(state: Any, mid: int, before: int, after: int, source: str) -> None:
    st = getattr(state, "ms_stack", None)
    if st is not None:
        st.on_move(mid, before, after, source)


@contextmanager
def batch(state: Any, tag: str) -> Iterator[None]:
    """Simultaneous batch; a no-op when stacking is off."""
    st = getattr(state, "ms_stack", None)
    if st is None:
        yield
        return
    st.begin(tag)
    try:
        yield
    finally:
        st.end()


def ensure_batch(state: Any, tag: str) -> None:
    st = getattr(state, "ms_stack", None)
    if st is not None:
        st.ensure(tag)


def end_batch(state: Any, tag: Optional[str] = None) -> None:
    """Closes the open batch (only when it carries ``tag`` if one is given)."""
    st = getattr(state, "ms_stack", None)
    if st is not None and st.batch_tag is not None and (tag is None or st.batch_tag == tag):
        st.end()


def audit(state: Any) -> None:
    st = getattr(state, "ms_stack", None)
    if st is not None:
        st.audit(state)


# ---------------------------------------------------------------------------
# End-of-round board read (telemetry; stacking on or off)
# ---------------------------------------------------------------------------
def observe_round_end(state: Any) -> None:
    tel = getattr(state, "ms_tie_tel", None)
    if tel is None or not state.config.is_market_share:
        return
    sh = {p.player_id: int(p.market_share or 0) for p in state.players if not p.is_patient_zero}
    if getattr(state, "setec_corp_active", False) and sh:
        sh[SETEC_CORP_ID] = int(state.setec_market_share)
    if len(sh) < 2:
        return
    st = getattr(state, "ms_stack", None)
    cap = state.config.ms_max()
    v = sorted(sh.values(), reverse=True)
    tel.add("rounds_obs")
    if v[0] == v[1]:
        tel.add("top_same_space")
        if v[0] >= cap:
            tel.add("top_same_space_at_max")
    if len(v) != len(set(v)):
        tel.add("any_same_space")
    if st is not None:
        top = sorted(sh, key=lambda m: (sh[m], st.seq[m]), reverse=True)
        leader: Optional[int] = top[0]
    else:
        lead = [m for m, x in sh.items() if x == v[0]]
        leader = lead[0] if len(lead) == 1 else None
    if leader is not None and tel.leader is not None and leader != tel.leader:
        tel.add("lead_changes")
        if leader == tel.leader_prev:
            tel.add("lead_back")
        if sh.get(tel.leader) == sh[leader]:
            tel.add("lead_changes_same_space")
        tel.leader_prev = tel.leader
    if leader is not None:
        tel.leader = leader


def end_block(state: Any, tel: Optional[MsTieTelemetry], tiebreak_decided_by: Optional[str]) -> Optional[Dict[str, Any]]:
    """The ``ms_tie`` block for the end row (None when telemetry is off). ``tel`` is a snapshot, so repeated
    ``evaluate_end_game`` calls give the same block. ``ms_end_*`` read live players only (not SETEC Corp)."""
    if tel is None:
        return None
    out = tel.as_dict()
    live = [int(p.market_share or 0) for p in state.players if not p.is_patient_zero]
    out["tiebreak_by_stack"] = int(tiebreak_decided_by == "market_share_stack")
    out["ms_end_spread"] = (max(live) - min(live)) if live else 0
    out["ms_end_same_space"] = int(len(live) != len(set(live)))
    return out
