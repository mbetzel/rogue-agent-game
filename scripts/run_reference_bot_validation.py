"""Phase 47 reference-bot validation (spec §9 / scoping §4), v0.36 and v0.37.

Mirrors scripts/run_reference_bot_check.py build_engine but takes a config switch and seeds
42 + P*100000 + idx, and adds per-seat telemetry (shield blocks by cube color, Secrets lost to Blue,
Public Relations Track level, Market Share, Market Leader Bonus place, Market Collapse triggers).
Telemetry is captured by wrapping phase4 resolve_player_attack for the top-level engine only
(search rollouts on clones are ignored).

Defaults (FINDINGS §41 roster rule): ``--pr-push on --pr-push-scope non_reference``; pass ``--pr-push off`` /
``--pr-push-scope all`` for the historical roster. Existing outputs are never replaced without ``--overwrite``.

Usage: python3 scripts/run_reference_bot_validation.py --config v037 --cells ref1 --players 3 --games 1200

Lever A (docs/specs/lever_a_roster_upgrade_spec.md §8): ``--pr-push on`` builds the config with
``bot_pr_push=True``; ``--pr-params '{"push_low_gap": 9}'`` overrides ``PrPushParams`` fields. Both are set at
construction only (H-LA-5). ``--pr-push-scope non_reference`` sets ``bot_pr_push_scope`` (file suffix ``_nonref``). Output files get a ``_push`` suffix when the switch is on.
"""
from __future__ import annotations
import argparse, json, os, sys, time
from multiprocessing import Pool

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "sim_results", "reference_bot")
_MAIN = None
_ACC = None


def _install_hook():
    from sim.engine import phase4_attack_resolution as p4
    if getattr(p4, "_val_hooked", False):
        return
    orig = p4.resolve_player_attack

    def wrapped(engine, player, *a, **k):
        if engine is not _MAIN:
            return orig(engine, player, *a, **k)
        s0 = player.secrets
        orig(engine, player, *a, **k)
        b = getattr(player, "last_defense_breakdown", None) or {}
        acc = _ACC[player.player_id]
        for c in ("red", "blue", "green"):
            acc["blocked_" + c] += int(b.get("blocked", {}).get(c, 0))
            acc["incoming_" + c] += int(b.get("effective_attacks", {}).get(c, 0))
        acc["secrets_lost_blue"] += max(0, s0 - player.secrets)  # MS mode: only Blue costs Secrets in P4
    p4.resolve_player_attack = wrapped
    p4._val_hooked = True


def parse_set(set_json, vuln_params_json=None):
    """``--set '{"vuln_band_thresholds":[4,7,10]}'`` / ``--vuln-params '{"secret_value":2.0}'`` -> GameConfig overrides."""
    from scripts.v046_tables import coerce_overrides
    out = coerce_overrides(json.loads(set_json or "{}"))
    if vuln_params_json:
        # kept as a dict: layered onto the preset's own VulnPolicyParams in make_config (never rebuilt from defaults)
        out["vuln_bot_params"] = json.loads(vuln_params_json)
    return out


def make_config(cfg_name, players, pr_push=False, pr_params=None, pr_scope="all", extra=None):
    from sim.config import GameConfig, PrPushParams
    kw = dict(num_players=players)
    kw.update(extra or {})
    if isinstance(kw.get("vuln_bot_params"), dict):
        import dataclasses
        kw["vuln_bot_params"] = dataclasses.replace(getattr(GameConfig, cfg_name)(num_players=players).vuln_bot_params,
                                                    **kw["vuln_bot_params"])
    kw["bot_pr_push"] = bool(pr_push)  # explicit either way: never inherit a roster default silently
    if pr_params:
        kw["bot_pr_push_params"] = PrPushParams(**pr_params)
    if pr_scope != "all":
        kw["bot_pr_push_scope"] = pr_scope
    return getattr(GameConfig, cfg_name)(**kw)


def output_name(cfg_name, cell, players, games, pr_push, pr_params, pr_scope, extra=None):
    """``{config}[_push][_p-<overrides>][_s-<--set>][_nonref]_{cell}_{P}p_{games}.json`` (sim/run_naming.py)."""
    from sim.run_naming import overrides_tag, scope_tag
    ov = overrides_tag(pr_params)
    st = overrides_tag({k: (v if not hasattr(v, "__dataclass_fields__") else "custom") for k, v in (extra or {}).items()})
    tag = ("_push" if pr_push else "") + (f"_p-{ov}" if ov else "") + (f"_s-{st}" if st else "") + scope_tag(pr_scope)
    return f"{cfg_name}{tag}_{cell}_{players}p_{games}.json"


def build_engine(cfg_name, cell, players, seed, pr_push=False, pr_params=None, pr_scope="all", extra=None):
    from sim.engine import GameEngine
    from sim.bots.mixed_policy import MixedPolicyBot
    from sim.bots.reference_search import ReferenceSearchBot, ReferenceSearchEngine
    from tests.fixtures.v035_parity.capture import _bot_classes
    classes = _bot_classes()
    off = seed % len(classes)
    bots = [classes[(off + i) % len(classes)](i) for i in range(players)]
    sp = seed % players
    cfg = make_config(cfg_name, players, pr_push, pr_params, pr_scope, extra)
    if cell == "baseline":
        return GameEngine(cfg, bots, seed=seed), []
    if cell == "mixed1":
        bots[sp] = MixedPolicyBot(sp, seed); return GameEngine(cfg, bots, seed=seed), [sp]
    if cell == "ref1":
        bots[sp] = ReferenceSearchBot(sp, seed); return ReferenceSearchEngine(cfg, bots, seed=seed), [sp]
    if cell == "ref_all":
        bots = [ReferenceSearchBot(i, seed) for i in range(players)]
        return ReferenceSearchEngine(cfg, bots, seed=seed), list(range(players))
    raise ValueError(cell)


def play(task):
    global _MAIN, _ACC
    cfg_name, cell, players, seed = task[:4]
    pr_push, pr_params = (task[4], task[5]) if len(task) > 4 else (False, None)
    pr_scope = task[6] if len(task) > 6 else "all"
    extra = task[7] if len(task) > 7 else None
    try:
        _install_hook()
        t0 = time.perf_counter()
        eng, special = build_engine(cfg_name, cell, players, seed, pr_push, pr_params, pr_scope, extra)
        _MAIN = eng
        _ACC = {i: {k: 0 for k in ("blocked_red", "blocked_blue", "blocked_green", "incoming_red",
                                   "incoming_blue", "incoming_green", "secrets_lost_blue")} for i in range(players)}
        res = eng.run_game()
        ms = 1000 * (time.perf_counter() - t0)
        rk = {r["player_id"]: r for r in res.rankings}
        seats = []
        for p in eng.state.players:
            r = rk.get(p.player_id, {})
            seats.append(dict(_ACC[p.player_id], name=p.bot.name, pr_level=int(p.patent_level),
                              market_share=p.market_share, mlb_place=r.get("market_share_place"),
                              mlb_bonus=r.get("market_leader_bonus"), secrets=r.get("secrets"),
                              patient_zero=p.is_patient_zero,
                              # v0.46.0 Vulnerability Track (spec §14.4 Step 4); empty on earlier configs
                              **({"vuln_keep": [p.vuln_keep_kept, p.vuln_keep_events], "pen_steps": p.pen_test_steps,
                                  "pen_research": p.pen_test_research_spent, "vuln_peak": p.vuln_peak,
                                  "green_lost": p.green_secrets_lost,
                                  "keep_face": {k: list(v) for k, v in p.vuln_keep_by_face.items()},
                                  "levels": [p.defense_level, p.triage_level, p.release_level, p.patent_level],
                                  "stance_hist": dict(getattr(p.bot, "stats", {}).get("stance_hist", {}))}
                                 if eng.config.is_vulnerability else {}),
                              # v0.47.0 Locked ⚠ Faces: ⚠ kept per player-round and Helix bypass timing
                              **({"icons": p.vuln_icons_kept_total, "player_rounds": len(p.vuln_by_round),
                                  "helix_uses": p.helix_bypass_uses, "helix_log": list(p.helix_bypass_use_log),
                                  "lock_events": p.lock_events}
                                 if getattr(eng.config, "colored_vuln_lock", False) else {})))
        return dict(cfg=cfg_name, cell=cell, players=players, seed=seed, ms=ms, special=special,
                    winner_ids=list(res.winner_ids), end_reason=res.end_reason.value,
                    end_triggers=list(res.end_triggers), rounds=res.total_rounds,
                    collapse_pids=list(res.market_collapse_pids), seats=seats, error=None)
    except Exception as e:  # record, don't crash the pod
        import traceback
        return dict(cfg=cfg_name, cell=cell, players=players, seed=seed, error=traceback.format_exc())


def _print_vuln_summary(rows, players):
    """Step 4 (v0.46.0): reference-seat vs field Vulnerability behaviour. Silent on earlier configs."""
    ok = [r for r in rows if not r["error"] and r["seats"] and "vuln_keep" in r["seats"][0]]
    if not ok:
        return
    agg = {"ref": [0, 0, 0, 0, 0.0, 0], "field": [0, 0, 0, 0, 0.0, 0]}  # kept, events, pen steps, seats, wins, games
    stance = {}
    for r in ok:
        for i, sd in enumerate(r["seats"]):
            k = "ref" if i in r["special"] else "field"
            a = agg[k]
            a[0] += sd["vuln_keep"][0]; a[1] += sd["vuln_keep"][1]; a[2] += sd["pen_steps"]; a[3] += 1
            a[4] += (1.0 / len(r["winner_ids"])) if i in r["winner_ids"] else 0.0
            if k == "ref":
                for st, n in sd["stance_hist"].items():
                    stance[st] = stance.get(st, 0) + n
    for k, a in agg.items():
        if a[3]:
            kr = f"{100 * a[0] / a[1]:.1f}%" if a[1] else "n/a"
            print(f"  [{k}] seats {a[3]}  win {100 * a[4] / a[3]:.1f}% (fair {100 / players:.1f}%)  "
                  f"keep rate {kr}  Pen Test steps/seat {a[2] / a[3]:.2f}")
    if stance:
        print("  ref1 stance choices:", dict(sorted(stance.items())))
    # keep rate per ⚠ face and track-level reach, ref vs field
    from scripts import v046_tables as tbl
    faces = {"ref": {}, "field": {}}
    seats = {"ref": [], "field": []}
    for r in ok:
        for i, sd in enumerate(r["seats"]):
            k = "ref" if i in r["special"] else "field"
            seats[k].append({"levels": sd["levels"]})
            for face, (kept, ev) in sd["keep_face"].items():
                a = faces[k].setdefault(face, [0, 0])
                a[0] += kept
                a[1] += ev
    names = tbl._face_names()
    print(f"  {'die:face':10}{'face':26}{'ref keep%':>10}{'field keep%':>12}")
    for face in sorted(set(faces["ref"]) | set(faces["field"]), key=lambda z: (z.split(":")[0], int(z.split(":")[1]))):
        cell = lambda k: ("n/a" if not faces[k].get(face, [0, 0])[1] else f"{100 * faces[k][face][0] / faces[k][face][1]:.1f}")  # noqa: E731
        print(f"  {face:10}{names.get(face, '?'):26}{cell('ref'):>10}{cell('field'):>12}")
    lv = {k: tbl._levels(v) for k, v in seats.items() if v}
    print(f"  track reach, % of seats at level >= k (L1 L2 L3 L4); Pen Test L4 = last column of the first row")
    for k, d in lv.items():
        print(f"  [{k}] 2+ L4: {100 * d['two_plus_l4']:.1f}%")
        for t in tbl.TRACKS:
            print(f"    {tbl.TRACK_LABEL[t]:32}" + "".join(f"{100 * x:>7.1f}" for x in d[t]))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="v036")
    ap.add_argument("--cells", default="ref1")
    ap.add_argument("--players", default="3")
    ap.add_argument("--games", type=int, default=600)
    ap.add_argument("--procs", type=int, default=8)
    ap.add_argument("--pr-push", choices=("off", "on"), default="on",
                    help="roster rule (FINDINGS §41): on by default; 'off' for the historical v0.37 roster")
    ap.add_argument("--pr-params", default=None, help="JSON object of PrPushParams overrides")
    ap.add_argument("--pr-push-scope", choices=("all", "non_reference"), default="non_reference",
                    help="GameConfig.bot_pr_push_scope, default non_reference for the ref1 edge check (non_reference: reference fallback/rollouts keep old behaviour)")
    ap.add_argument("--set", default=None, help="JSON GameConfig overrides (e.g. the v0.46 package levers / arms)")
    ap.add_argument("--vuln-params", default=None, help="JSON VulnPolicyParams overrides (v0.46 bot lambda parameters)")
    ap.add_argument("--overwrite", action="store_true", help="allow replacing existing output files")
    ap.add_argument("--out-dir", default=OUT, help="output directory (default sim_results/reference_bot/)")
    a = ap.parse_args(argv)
    out_dir = a.out_dir
    pr_push = a.pr_push == "on"
    pr_params = json.loads(a.pr_params) if a.pr_params else None
    extra = parse_set(a.set, a.vuln_params)
    make_config(a.config, 3, pr_push, pr_params, a.pr_push_scope, extra)  # fail fast on an illegal cell (ValueError)
    from sim.run_naming import guard_overwrite
    os.makedirs(out_dir, exist_ok=True)
    players_list = [int(x) for x in a.players.split(",")]
    cells = a.cells.split(",")
    for P in players_list:  # check every target up front so a long run never dies (or clobbers) midway
        for cell in cells:
            guard_overwrite(os.path.join(out_dir, output_name(a.config, cell, P, a.games, pr_push, pr_params,
                                                          a.pr_push_scope, extra)), a.overwrite)
    for P in players_list:
        for cell in cells:
            tasks = [(a.config, cell, P, 42 + P * 100000 + i, pr_push, pr_params, a.pr_push_scope, extra) for i in range(a.games)]
            t0 = time.perf_counter()
            with Pool(a.procs) as pool:
                rows = pool.map(play, tasks, chunksize=1)
            wall = time.perf_counter() - t0
            errs = [r for r in rows if r["error"]]
            fn = os.path.join(out_dir, output_name(a.config, cell, P, a.games, pr_push, pr_params, a.pr_push_scope, extra))
            guard_overwrite(fn, a.overwrite)
            with open(fn, "w") as fh:
                json.dump({"wall_s": wall, "pr_push": pr_push, "pr_params": pr_params,
                       "pr_push_scope": a.pr_push_scope, "games": rows}, fh)
            print(f"{os.path.basename(fn)} {cell} {P}P {a.games}g wall {wall:.1f}s errors {len(errs)}", flush=True)
            for e in errs[:3]:
                print(e["seed"], e["error"])
            _print_vuln_summary(rows, P)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
