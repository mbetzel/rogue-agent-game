"""Pre-SDLC probe: Market Share tie stagnation (v0.51.0). Monkeypatch only, no engine edits.

Diagnostics (every arm): end-of-round tie rates among Market Leader Bonus participants (survivors, plus SETEC Corp
at 2P), ties at the track maximum, tie persistence round to round, pair-gap persistence, sole-leader changes,
Market Share movement by source, plus the usual outcome metrics.

Arms (combine with "+"):
  R0      v0.51.0 as shipped
  TWORSE  MLB: tied players share the WORSE place (two tied for 1st both score 2nd's +1; the next is 3rd)
  TSPLIT  MLB: tied players split the awards of the places they span, rounded down (2-way 1st tie: +2 each)
  STACK   Stacking order: a cube that moves onto an occupied space goes UNDER the cubes already there, and ranks
          below them (MLB and the Market Share tiebreaker). Red moves everyone together and keeps the order.
  CAP25   Track maximum 25 (start values unchanged: 14 at 2P, 18 at 3-4P)
  STAG    Staggered start: 18/17/16/15 (2P: 14/13), last seat highest
  RLOW    Red: each cube costs only the lowest player(s) 1 (feedback-1122 arm, for reference)
  RVULN   Red as today, plus players at Vulnerability 5+ lose 1 more Market Share in a round with any Red
  STACKTOP Like STACK, but the latest arrival goes ON TOP and ranks above (the covered leader must answer)
  VTB     MLB ties broken by lower Vulnerability; still-tied players share the better place (SETEC Corp loses ties)
  AWARET  Bots value matching a rival as the better place (STACKTOP for a mover)
  AWARE   Bots value a tie as the WORSE place (matches STACK for a mover / TWORSE), so they push to pass
  S32     MLB 1st +3 / 2nd +2 at 3P and 4P (2P unchanged)
  S321    MLB 3P +3/+2, 4P +3/+2/+1 (2P unchanged)
Without AWARE, bots are not taught the new rules (their MLB estimate already values breaking ties).

  python3 scripts/probe_ms_ties.py --arms R0,TWORSE,STACK --players 2,3,4 --games 2000
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.run_v380_secret_faces_sweep import build_engine  # noqa: E402

OUT_DIR = os.path.join(ROOT, "sim_results", "ms_ties")
SETEC = -1
_S = {"orig": None, "parts": set(), "tick": {}, "n": 0, "tel": None, "state": None, "setec_last": 0}


def _participants(s):
    sh = {p.player_id: int(p.market_share) for p in s.players if not p.is_patient_zero}
    if getattr(s, "setec_corp_active", False) and sh:
        sh[SETEC] = int(getattr(s, "setec_market_share", 0))
    return sh


def _sync_setec():
    s = _S["state"]
    if s is None or not getattr(s, "setec_corp_active", False):
        return
    v = int(getattr(s, "setec_market_share", 0))
    if v != _S["setec_last"]:
        _S["setec_last"] = v
        _S["n"] += 1
        _S["tick"][SETEC] = _S["n"]


def _places(shares):
    parts = _S["parts"]
    vals = list(shares.values())
    if "STACK" in parts or "STACKTOP" in parts:
        _sync_setec()
        tk = _S["tick"]
        sign = -1 if "STACKTOP" in parts else 1
        key = {pid: (-v, sign * tk.get(pid, 0), pid) for pid, v in shares.items()}
        order = sorted(shares, key=lambda p: key[p])
        return {pid: i + 1 for i, pid in enumerate(order)}, {pid: 1 for pid in shares}
    if "VTB" in parts:
        st = _S["state"]
        vul = {p.player_id: int(p.vulnerability) for p in st.players} if st is not None else {}
        k = {pid: (v, -vul.get(pid, 99)) for pid, v in shares.items()}
        better = {pid: 1 + sum(1 for q in shares if k[q] > k[pid]) for pid in shares}
        span = {pid: sum(1 for q in shares if k[q] == k[pid]) for pid in shares}
        return better, span
    better = {pid: 1 + sum(1 for v in vals if v > s) for pid, s in shares.items()}
    span = {pid: sum(1 for v in vals if v == s) for pid, s in shares.items()}
    return better, span


def _awards(shares, schedule, order=None):  # order: the v0.52 engine passes it; the probe uses its own tick order
    parts = _S["parts"]
    sched = list(schedule)
    at = lambda i: int(sched[i]) if 0 <= i < len(sched) else 0  # noqa: E731
    better, span = _places(shares)
    out = {}
    for pid in shares:
        b, k = better[pid], span[pid]
        if "TWORSE" in parts:
            place = b + k - 1
            out[pid] = (place, at(place - 1))
        elif "TSPLIT" in parts:
            out[pid] = (b, sum(at(i) for i in range(b - 1, b - 1 + k)) // k)
        else:
            out[pid] = (b, at(b - 1))
    t = _S["tel"]
    if t is not None and shares:
        v = sorted(shares.values(), reverse=True)
        t["mlb_awards"] += 1
        t["mlb_tie1"] += int(len(v) > 1 and v[0] == v[1])
        t["mlb_eff_tie1"] += int(sum(1 for pid in out if out[pid][0] == 1) > 1)
        t["mlb_secrets"] += sum(b for pid, (_, b) in out.items() if pid != SETEC)
    return out


def install(arm):
    from sim.engine import market_share as msm
    from sim.engine import end_game as eg
    from sim.engine import phase4_attack_resolution as p4
    from sim.engine.state import PlayerState
    from sim.engine.core import GameEngine
    from sim.config import CubeColor
    if _S["orig"] is None:
        _S["orig"] = (msm.market_leader_bonus_awards, msm.market_share_places, p4.resolve_player_red_blue_v046,
                      PlayerState.change_market_share, GameEngine.run_round)
    o_aw, o_pl, o_rb, o_cms, o_rr = _S["orig"]
    parts = set(arm.split("+"))
    _S["parts"] = parts
    msm.market_leader_bonus_awards = eg.market_leader_bonus_awards = _awards
    if parts & {"STACK", "STACKTOP", "VTB"}:
        def pl(shares, order=None):
            return _places(shares)[0]
        msm.market_share_places = eg.market_share_places = pl
    else:
        msm.market_share_places = eg.market_share_places = o_pl

    def cms(self, delta, source):
        actual = o_cms(self, delta, source)
        t = _S["tel"]
        if t is not None and actual:
            t[f"mv_{source}"] += abs(actual)
        if actual and source not in ("red", "corruption"):
            _S["n"] += 1
            _S["tick"][self.player_id] = _S["n"]
        return actual
    PlayerState.change_market_share = cms

    def rb(engine, player, attack, cr, **kw):
        s = engine.state
        a = dict(attack)
        red = int(a[CubeColor.RED])
        if "RLOW" in parts and red:
            al = [p for p in s.players if not p.is_patient_zero]
            snap = getattr(s, "phase4_market_share_start", None) or {}
            if s.phase4_snapshot_round != s.current_round:
                snap = {p.player_id: p.market_share for p in s.players}
            lo = min(int(snap.get(p.player_id, p.market_share)) for p in al)
            if int(snap.get(player.player_id, player.market_share)) != lo:
                a[CubeColor.RED] = 0
        o_rb(engine, player, a, cr, **kw)
        if "RVULN" in parts and red and int(player.vulnerability) >= 5:
            player.change_market_share(-1, "red")
    p4.resolve_player_red_blue_v046 = rb

    import sim.bots.market_share_policy as msp
    import sim.bots.secret_face_policy as sfp  # noqa: F401  (imports msm.expected_market_leader_bonus lazily)
    if _S.get("o_emlb") is None:
        _S["o_emlb"] = msm.expected_market_leader_bonus
    o_emlb = _S["o_emlb"]
    if "AWARET" in parts:
        def emlb(share, rival_shares, schedule, **_kw):  # v0.52 engine passes stacked= / ahead_on_space=; the probe ignores them
            idx = sum(1 for r in rival_shares if r > share)
            sched = list(schedule)
            return float(sched[idx]) if idx < len(sched) else 0.0
        msm.expected_market_leader_bonus = msp.expected_market_leader_bonus = emlb
    elif "AWARE" in parts:
        def emlb(share, rival_shares, schedule, **_kw):  # v0.52 engine passes stacked= / ahead_on_space=; the probe ignores them
            rivals = list(rival_shares)
            idx = sum(1 for r in rivals if r >= share)
            sched = list(schedule)
            return float(sched[idx]) if idx < len(sched) else 0.0
        msm.expected_market_leader_bonus = msp.expected_market_leader_bonus = emlb
    else:
        msm.expected_market_leader_bonus = msp.expected_market_leader_bonus = o_emlb

    def rr(self):
        _sync_setec()
        tel = o_rr(self)
        _round_diag(self.state)
        return tel
    GameEngine.run_round = rr


def _round_diag(s):
    t = _S["tel"]
    sh = _participants(s)
    if len(sh) < 2:
        return
    cap = max((p.market_share_max for p in s.players), default=20)
    v = sorted(sh.values(), reverse=True)
    t["rounds_obs"] += 1
    top_tie = v[0] == v[1]
    t["top_tie"] += int(top_tie)
    t["top_tie_cap"] += int(top_tie and v[0] >= cap)
    t["any_tie"] += int(len(v) != len(set(v)))
    t["pr_at_cap"] += sum(1 for pid, x in sh.items() if pid != SETEC and x >= cap)
    t["pr_obs"] += sum(1 for pid in sh if pid != SETEC)
    prev = _S.get("prev") or {}
    for a_, b_ in itertools.combinations(sorted(sh), 2):
        if a_ in prev and b_ in prev:
            g0, g1 = prev[a_] - prev[b_], sh[a_] - sh[b_]
            t["pair_obs"] += 1
            t["pair_gap_same"] += int(g0 == g1)
            if g0 == 0:
                t["tie_prev"] += 1
                t["tie_kept"] += int(g1 == 0)
    pl1 = _places(sh)[0]
    leaders = [pid for pid, x in pl1.items() if x == 1]
    solo = leaders[0] if len(leaders) == 1 else None
    if solo is not None and _S.get("solo") is not None and solo != _S["solo"]:
        t["lead_change"] += 1
        t["lead_back"] += int(solo == _S.get("solo_prev"))
        _S["solo_prev"] = _S["solo"]
    if solo is not None:
        _S["solo"] = solo
    _S["prev"] = dict(sh)


def play(task):
    arm, players, seed = task
    install(arm)
    parts = _S["parts"]
    tel = Counter()
    _S.update(tel=tel, tick={}, n=0, prev=None, solo=None, solo_prev=None, setec_last=0)
    ov = {}
    if "CAP25" in parts:
        ov["market_share_max"] = 25
    if "S32" in parts:
        ov["red_secret_payout_by_player_count"] = {2: (3, 1), 3: (3, 2, 0), 4: (3, 2, 0, 0)}
    if "S321" in parts:
        ov["red_secret_payout_by_player_count"] = {2: (3, 1), 3: (3, 2, 0), 4: (3, 2, 1, 0)}
    eng = build_engine("v051_roster", "mixed1", players, seed, ov)
    s = eng.state
    _S["state"] = s
    n = len(s.players)
    if "STAG" in parts:
        top = s.players[0].market_share
        for i, p in enumerate(s.players):
            seat = (i - s.first_player_index) % n
            p.market_share = p.market_share_start = top - (n - 1 - seat)
    # initial stack: last seat on top (mirrors "last seat highest")
    for i, p in enumerate(s.players):
        seat = (i - s.first_player_index) % n
        _S["tick"][p.player_id] = (seat - 100) if "STACKTOP" in parts else -seat
    _S["tick"][SETEC] = 0
    res = eng.run_game()
    nwin = max(1, len(res.winner_ids))
    by_pid = {r["player_id"]: r for r in res.rankings}
    ms_end = [p.market_share for p in s.players if not p.is_patient_zero]
    seats = []
    for i, p in enumerate(s.players):
        r = by_pid[p.player_id]
        seats.append({"win": (1.0 / nwin) if p.player_id in res.winner_ids else 0.0, "secrets": r["secrets"],
                      "pz": bool(p.is_patient_zero), "seat": (i - s.first_player_index) % n,
                      "company": str(r.get("company_code")).lower()})
    return {"end": res.end_reason.value, "rounds": res.total_rounds, "seats": seats, "tel": dict(tel),
            "ms_end_tie": int(len(ms_end) != len(set(ms_end))),
            "ms_end_spread": (max(ms_end) - min(ms_end)) if ms_end else 0}


def summarize(recs):
    n = len(recs)
    m = lambda xs: sum(xs) / max(1, len(xs))  # noqa: E731
    ends = Counter(r["end"] for r in recs)
    seats = [x for r in recs for x in r["seats"]]
    t = Counter()
    for r in recs:
        t.update(r["tel"])
    by_co, by_seat = defaultdict(list), defaultdict(list)
    for x in seats:
        by_co[x["company"]].append(x["win"])
        by_seat[x["seat"]].append(x["win"])
    spread = lambda d: 100 * (max(m(v) for v in d.values()) - min(m(v) for v in d.values()))  # noqa: E731
    pct = lambda a, b: 100 * t[a] / max(1, t[b])  # noqa: E731
    mv = {k[3:]: round(v / max(1, t["pr_obs"]), 3) for k, v in t.items() if k.startswith("mv_")}
    return {
        "games": n, "rounds": m([r["rounds"] for r in recs]),
        "PZ": 100 * ends["patient_zero"] / n, "MC": 100 * ends["market_collapse"] / n,
        "SING": 100 * ends["singularity"] / n, "elim": 100 * m([x["pz"] for x in seats]),
        "win_sec": m([x["secrets"] for x in seats if x["win"] > 0]), "co_spread": spread(by_co),
        "seat_spread": spread(by_seat),
        "top_tie": pct("top_tie", "rounds_obs"), "top_tie_cap": pct("top_tie_cap", "rounds_obs"),
        "any_tie": pct("any_tie", "rounds_obs"), "at_cap": pct("pr_at_cap", "pr_obs"),
        "tie_kept": pct("tie_kept", "tie_prev"), "gap_same": pct("pair_gap_same", "pair_obs"),
        "mlb_tie1": pct("mlb_tie1", "mlb_awards"), "mlb_eff_tie1": pct("mlb_eff_tie1", "mlb_awards"),
        "lead_back_pct": pct("lead_back", "lead_change"), "mlb_sec_pg": t["mlb_secrets"] / n,
        "lead_chg_pg": t["lead_change"] / n,
        "end_tie": 100 * m([r["ms_end_tie"] for r in recs]), "end_spread": m([r["ms_end_spread"] for r in recs]),
        "move_per_player_round": mv, "win_by_seat": {k: round(100 * m(v), 1) for k, v in sorted(by_seat.items())},
    }


KEYS = ("rounds", "PZ", "MC", "SING", "elim", "win_sec", "co_spread", "seat_spread", "top_tie", "top_tie_cap",
        "any_tie", "at_cap", "tie_kept", "gap_same", "mlb_tie1", "mlb_eff_tie1", "mlb_sec_pg", "lead_chg_pg", "lead_back_pct", "end_tie", "end_spread")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", default="R0")
    ap.add_argument("--players", default="2,3,4")
    ap.add_argument("--games", type=int, default=2000)
    ap.add_argument("--seed0", type=int, default=42)
    ap.add_argument("--procs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    a = ap.parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)
    from multiprocessing import Pool
    with Pool(a.procs) as pool:
        for pl in [int(x) for x in a.players.split(",")]:
            for arm in a.arms.split(","):
                tasks = [(arm, pl, s) for s in range(a.seed0, a.seed0 + a.games)]
                recs = pool.map(play, tasks, chunksize=max(1, len(tasks) // (a.procs * 8)))
                sm = summarize(recs)
                with open(os.path.join(OUT_DIR, f"{arm}_{pl}P.json"), "w") as fh:
                    json.dump(sm, fh, indent=1)
                print(f"{pl}P {arm:12s} " + " ".join(f"{k}={sm[k]:.1f}" for k in KEYS), flush=True)
                print(f"     move/pl-rd={sm['move_per_player_round']} seat={sm['win_by_seat']}", flush=True)


if __name__ == "__main__":
    main()
