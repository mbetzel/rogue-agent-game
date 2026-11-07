"""Phase 47 reference-bot validation (spec §9 / scoping §4), v0.36 and v0.37.

Mirrors scripts/run_reference_bot_check.py build_engine but takes a config switch and seeds
42 + P*100000 + idx, and adds per-seat telemetry (shield blocks by cube color, Secrets lost to Blue,
Public Relations Track level, Market Share, Market Leader Bonus place, Market Collapse triggers).
Telemetry is captured by wrapping phase4 resolve_player_attack for the top-level engine only
(search rollouts on clones are ignored).

Usage: python3 scripts/run_reference_bot_validation.py --config v037 --cells ref1 --players 3 --games 1200
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


def build_engine(cfg_name, cell, players, seed):
    from sim.config import GameConfig
    from sim.engine import GameEngine
    from sim.bots.mixed_policy import MixedPolicyBot
    from sim.bots.reference_search import ReferenceSearchBot, ReferenceSearchEngine
    from tests.fixtures.v035_parity.capture import _bot_classes
    classes = _bot_classes()
    off = seed % len(classes)
    bots = [classes[(off + i) % len(classes)](i) for i in range(players)]
    sp = seed % players
    cfg = getattr(GameConfig, cfg_name)(num_players=players)
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
    cfg_name, cell, players, seed = task
    try:
        _install_hook()
        t0 = time.perf_counter()
        eng, special = build_engine(cfg_name, cell, players, seed)
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
                              patient_zero=p.is_patient_zero))
        return dict(cfg=cfg_name, cell=cell, players=players, seed=seed, ms=ms, special=special,
                    winner_ids=list(res.winner_ids), end_reason=res.end_reason.value,
                    end_triggers=list(res.end_triggers), rounds=res.total_rounds,
                    collapse_pids=list(res.market_collapse_pids), seats=seats, error=None)
    except Exception as e:  # record, don't crash the pod
        import traceback
        return dict(cfg=cfg_name, cell=cell, players=players, seed=seed, error=traceback.format_exc())


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="v036")
    ap.add_argument("--cells", default="ref1")
    ap.add_argument("--players", default="3")
    ap.add_argument("--games", type=int, default=600)
    ap.add_argument("--procs", type=int, default=8)
    a = ap.parse_args(argv)
    os.makedirs(OUT, exist_ok=True)
    for P in [int(x) for x in a.players.split(",")]:
        for cell in a.cells.split(","):
            tasks = [(a.config, cell, P, 42 + P * 100000 + i) for i in range(a.games)]
            t0 = time.perf_counter()
            with Pool(a.procs) as pool:
                rows = pool.map(play, tasks, chunksize=1)
            wall = time.perf_counter() - t0
            errs = [r for r in rows if r["error"]]
            fn = os.path.join(OUT, f"{a.config}_{cell}_{P}p_{a.games}.json")
            with open(fn, "w") as fh:
                json.dump({"wall_s": wall, "games": rows}, fh)
            print(f"{a.config} {cell} {P}P {a.games}g wall {wall:.1f}s errors {len(errs)}", flush=True)
            for e in errs[:3]:
                print(e["seed"], e["error"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
