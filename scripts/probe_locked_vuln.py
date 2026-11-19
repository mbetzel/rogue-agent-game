"""v0.47 pre-SDLC probe (docs/plans/locked_vuln_faces_gd_plan.md): locks colored dice showing a ⚠ face during Phase 1 rerolls by monkeypatch (no engine edits). ARMS env = JSON {name: overrides}; "_lock" / "_mode" (aware | nocolor | s0_<mode>) are probe keys. Output: OUT env (default probe_out.json) next to this file."""
import os, sys, json, argparse
from collections import Counter, defaultdict
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path: sys.path.insert(0, ROOT)
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0, HERE)
from scripts import run_v046_sweep as sw
from sim.entities import DieColor

_C = Counter()
_LOCK = {"on": False}

def install(lock_on):
    from sim.bots import vulnerability_policy as vp, base
    from sim.engine import vulnerability as vuln
    if getattr(vp, "_probe", False):
        _LOCK["on"] = lock_on; return
    vp._probe = True; _LOCK["on"] = lock_on
    orig_adj, orig_lock, orig_helix = vp.adjust_rerolls, vuln.lock_in, base.BaseBot.choose_helix_override if hasattr(base, "BaseBot") else None
    def adj(bot, player, dice, indices, state, rr):
        out = orig_adj(bot, player, dice, indices, state, rr)
        _C["reroll_calls"] += 1
        if _LOCK["on"] and not getattr(player, "_probe_helix", False):
            keep = []
            for i in out:
                d = dice[i]
                if d.color != DieColor.GRAY and vuln.face_vuln(d.current_face) > 0:
                    _C["blocked_rerolls"] += 1
                    continue
                keep.append(i)
            out = keep
            mode = _LOCK.get("mode")
            if mode and mode.startswith("s0"):
                mode = mode[3:] if player.player_id == min(q.player_id for q in state.players) else "aware"
            if mode == "chase":
                mode = None
            if mode:
                tbl_v = player.vulnerability + sum(vuln.face_vuln(d.current_face) for j, d in enumerate(dice) if j not in out)
                keep = []
                for i in out:
                    d = dice[i]
                    if d.color != DieColor.GRAY and (mode == "nocolor" or (mode == "aware" and tbl_v + 1 in (4, 7, 10))):
                        _C["policy_skips"] += 1; continue
                    keep.append(i)
                out = keep
        _C["dice_rerolled"] += len(out)
        return out
    def lock_in(engine, p, active):
        p._probe_helix = False
        for d in active:
            f = d.current_face
            if f is None: continue
            g = d.color == DieColor.GRAY
            _C["gray_dice" if g else "col_dice"] += 1
            if vuln.face_vuln(f) > 0:
                _C["gray_vuln" if g else ("secret_vuln" if f.secrets_pending else "core_vuln")] += 1
            if getattr(f, "is_star", False):
                _C["stars"] += 1
        _C["pq_at_lockin"] += len(p.glitched_dice); _C["lockins"] += 1
        return orig_lock(engine, p, active)
    vp.adjust_rerolls, vuln.lock_in = adj, lock_in
    cls = base.BaseBot if hasattr(base, "BaseBot") else None
    if cls is None:
        for n in dir(base):
            o = getattr(base, n)
            if isinstance(o, type) and "choose_helix_override" in o.__dict__: cls = o
    oh = cls.choose_helix_override
    def helix(self, *a, **k):
        r = oh(self, *a, **k)
        if r: k.get("player_state", a[0] if a else None)._probe_helix = True; _C["helix_uses"] += 1
        return r
    cls.choose_helix_override = helix

def play(task):
    ov = dict(task[4]); lock_on = ov.pop("_lock", False); mode = ov.pop("_mode", None)
    task = (task[0], task[1], task[2], task[3], ov, task[5])
    install(lock_on); _LOCK["mode"] = mode; _C.clear()
    rec = sw.play(task); rec["probe"] = dict(_C); rec.pop("tbl", None)
    return rec

def summarize(tag, recs, pl):
    m = sw.metrics([dict(r, tbl=None) for r in recs], pl) if False else None
    n = len(recs); P = Counter()
    for r in recs: P.update(r["probe"])
    seats = [s for r in recs for s in r["seats"]]
    ad = [s for s in seats if s["stance"] == "ADAPTIVE"]
    ends = Counter(r["end"] for r in recs)
    alive = sum(s["alive_rounds"] for s in seats)
    byco = defaultdict(list)
    for s in seats: byco[s["company"]].append(s["win"])
    co = {k: round(100*sum(v)/len(v),1) for k, v in sorted(byco.items())}
    li = max(1, P["lockins"])
    out = dict(rounds=sum(r["rounds"] for r in recs)/n, PZ=100*ends["patient_zero"]/n, TW=100*sum(r["wipeout"] for r in recs)/n,
               MC=100*ends["market_collapse"]/n, SING=100*ends["singularity"]/n,
               green_lost=sum(s["green_lost"] for s in ad)/max(1,len(ad)), green_lost_all=sum(s["green_lost"] for s in seats)/len(seats),
               icons_pr=sum(s["icons"] for s in seats)/max(1,alive), pen_steps=sum(s["pen_steps"] for s in seats)/len(seats),
               pen_rsch=sum(s["pen_research"] for s in seats)/len(seats), peak=sum(s["vuln_peak"] for s in seats)/len(seats),
               secrets=sum(s["secrets"] for s in seats)/len(seats),
               core_per_col=P["core_vuln"]/max(1,P["col_dice"]), sec_per_col=P["secret_vuln"]/max(1,P["col_dice"]),
               gray_per=P["gray_vuln"]/max(1,P["gray_dice"]), col_dice_pr=P["col_dice"]/li, star_per_col=P["stars"]/max(1,P["col_dice"]),
               pq=P["pq_at_lockin"]/li, blocked_pr=P["blocked_rerolls"]/li, rerolled_pr=P["dice_rerolled"]/li,
               green_nt=100*sum(r["green_no_target"] for r in recs)/max(1,sum(r["green_resolved"] for r in recs)), win_by_co=co)
    print(tag, json.dumps({k: (round(v,3) if isinstance(v,float) else v) for k, v in out.items()}))
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--games", type=int, default=300); ap.add_argument("--players", default="2,3,4")
    ap.add_argument("--procs", type=int, default=max(1,(os.cpu_count() or 2)-1)); a = ap.parse_args()
    sw.play = play
    res = {}
    arms = json.loads(os.environ["ARMS"]) if os.environ.get("ARMS") else None
    arms = arms or {"base": {}, "A_lock_np": {"_lock": True}, "B_lock_prem": {"_lock": True, "die_face_profile": "V046_VULN"}, "prem_nolock": {"die_face_profile": "V046_VULN"},
            "A_aware": {"_lock": True, "_mode": "aware"}, "B_aware": {"_lock": True, "_mode": "aware", "die_face_profile": "V046_VULN"},
            "A_nocolor": {"_lock": True, "_mode": "nocolor"}}
    for pl in [int(x) for x in a.players.split(",")]:
        for name, ov in arms.items():
            recs = sw.play_all("v046_roster", "mixed1", pl, a.games, 42, dict(ov), a.procs, False)
            res[f"{pl}P_{name}"] = summarize(f"{pl}P {name}", recs, pl)
            res[f"{pl}P_{name}"]["seat0_win"] = 100*sum(r["seats"][0]["win"] for r in recs)/len(recs)
    json.dump(res, open(os.environ.get("OUT", os.path.join(ROOT, "sim_results", "v047_probe.json")), "w"), indent=1)
