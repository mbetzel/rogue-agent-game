"""v0.38.0 candidate sweep: Secret faces / Processing Box / Glitched Shield Slots (spec v380 §11).

Runs ``--games`` seeded games per player count with the five-archetype rotation and random Client Companies /
White Hat Operatives / Variant Cards (the ``tests/fixtures/v035_parity`` "setup" scenario). Roster rule (FINDINGS
§40-§41): ``--roster mixed1`` (default) puts one ``MixedPolicyBot`` seat at ``seed % P``; ``--roster archetypes``
keeps the plain rotation. ``--config v037`` / ``v037_roster`` give baselines. ``--procs N`` is deterministic
by seed. Per-game records (seed, end reason, rounds, final Market Share per seat, cube exits by colour, winner
archetype / Company colour / path) are kept in the output for distributions and outlier seeds, and
reports endings, rounds, breach rate, Secrets by source, stranded share, slot dynamics, win rate by Company colour
and by path, and archetype spread.

Path rule (logged in the output): a player's path is the colour holding >= 60% of their owned Red / Blue / Green /
Yellow dice at game end (Purple excluded), else "mixed"; a player with none of those dice is "mixed".

    python3 -m scripts.run_v380_secret_faces_sweep --games 300 --players 3
    python3 -m scripts.run_v380_secret_faces_sweep --games 1200 --players 2 3 4 --procs 8 --out sim_results/v380/sweep.json
    python3 -m scripts.run_v380_secret_faces_sweep --config v037_roster --roster archetypes --games 300
    python3 -m scripts.run_v380_secret_faces_sweep --games 300 --players 2 3 4 --config v038 --set starting_secrets_by_player_count='{"3":4}'
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from sim.config import GameConfig  # noqa: E402
from sim.run_naming import guard_overwrite, overrides_tag  # noqa: E402

PATH_RULE = "majority colour >= 60% of owned Red/Blue/Green/Yellow dice at game end, else mixed"
PATH_COLORS = ("red", "blue", "green", "yellow")


def classify_path(dice_by_color: Dict[str, int]) -> str:
    owned = {c: int(dice_by_color.get(c, 0)) for c in PATH_COLORS}
    total = sum(owned.values())
    if total <= 0:
        return "mixed"
    best = max(PATH_COLORS, key=lambda c: owned[c])
    return best if owned[best] / total >= 0.6 else "mixed"


# GameConfig fields the six-phase engine never reads (Corruption Track size comes from the Version Cards; set
# ``corruption_track_flat_capacity`` instead). Overriding them is refused rather than silently ignored.
INERT_FIELDS = {
    "corruption_track_capacity_by_player_count": "not read by the engine; use corruption_track_flat_capacity",
    "corruption_track_lengths": "not read by the engine (track length = Version Card)",
    "corruption_spaces_per_player": "deprecated in v0.4", "corruption_spaces_base": "deprecated in v0.4",
}
NOOP_CHECK_GAMES = 10


class OverrideError(ValueError):
    pass


def _coerce(val: Any, like: Any, name: str) -> Any:
    """Coerce a JSON value to the type of the field's current value ``like`` (dict keys / values, tuples)."""
    import enum

    if isinstance(like, dict) and isinstance(val, dict):
        sample_k = next(iter(like), None)
        sample_v = next(iter(like.values()), None)
        out = {}
        for k, v in val.items():
            if sample_k is not None and not isinstance(k, type(sample_k)):
                try:
                    k = type(sample_k)(int(k) if isinstance(sample_k, int) else k)
                except (TypeError, ValueError) as e:
                    raise OverrideError(f"--set {name}: key {k!r} is not a {type(sample_k).__name__}") from e
            out[k] = _coerce(v, like.get(k, sample_v), name)
        return out
    if isinstance(like, tuple) and isinstance(val, list):
        sample = like[0] if like else None
        return tuple(_coerce(x, sample, name) for x in val)
    if isinstance(like, enum.Enum) and not isinstance(val, enum.Enum):
        return type(like)(val)
    return val


def _parse_overrides(items: List[str], config_name: str = "v038_roster") -> Dict[str, Any]:
    """``key=JSON`` -> typed GameConfig overrides. Unknown or engine-inert fields raise ``OverrideError``."""
    import dataclasses

    base = getattr(GameConfig, config_name)(num_players=3)
    fields = {f.name for f in dataclasses.fields(GameConfig)}
    out: Dict[str, Any] = {}
    for it in items or []:
        k, sep, v = it.partition("=")
        if not sep:
            raise OverrideError(f"--set expects key=JSON, got {it!r}")
        if k not in fields:
            raise OverrideError(f"--set {k}: unknown GameConfig field")
        if k in INERT_FIELDS:
            raise OverrideError(f"--set {k}: ineffective ({INERT_FIELDS[k]})")
        out[k] = _coerce(json.loads(v), getattr(base, k), k)
    return out


def check_overrides_effective(config_name: str, roster: str, players: int, overrides: Dict[str, Any],
                              seed0: int = 0, games: int = NOOP_CHECK_GAMES) -> None:
    """Raise if the overrides build an identical config or leave the first ``games`` games bit-identical."""
    if not overrides:
        return
    kw = dict(num_players=players)
    if getattr(GameConfig, config_name)(**kw) == getattr(GameConfig, config_name)(**{**kw, **overrides}):
        raise OverrideError(f"--set {sorted(overrides)}: equals the {config_name} default (no-op)")
    for s in range(seed0, seed0 + games):
        if play((config_name, roster, players, s, overrides)) != play((config_name, roster, players, s, {})):
            return
    raise OverrideError(f"--set {sorted(overrides)}: first {games} games bit-identical to the baseline "
                        "(ineffective override; pass --allow-noop to run anyway)")


CONFIGS = ("v038", "v038_roster", "v038b", "v038c", "v038d", "v038e", "v038e_roster", "v038f", "v038f_roster", "v037", "v037_roster")
ROSTERS = ("mixed1", "archetypes")


def build_engine(config_name: str, roster: str, players: int, seed: int, overrides: Dict[str, Any]):
    """The v0.35 parity "setup" scenario (same RNG draws), plus the optional Mixed seat at ``seed % P``."""
    import random

    from sim.bots.mixed_policy import MixedPolicyBot
    from sim.engine import GameEngine
    from sim.entities import get_random_companies, get_random_setup, get_random_white_hats
    from tests.fixtures.v035_parity.capture import _bot_classes

    classes = _bot_classes()
    rng = random.Random(seed)
    bots = [classes[(seed * players + i) % len(classes)](i) for i in range(players)]
    rng.shuffle(bots)
    for i, b in enumerate(bots):
        b.player_id = i
    if roster == "mixed1":
        seat = seed % players
        bots[seat] = MixedPolicyBot(seat, seed)
    elif roster != "archetypes":
        raise ValueError(f"unknown roster {roster!r}")
    variants, version_deck = get_random_setup(rng, profile="STANDARD")
    companies = get_random_companies(players, rng)
    white_hats = get_random_white_hats(players, rng)
    kw = dict(num_players=players, starting_money=6, starting_gray_dice=3, starting_purple_dice=1,
              starting_purple_reserve=1, corruption_track_profile="STANDARD", enable_corporate_asymmetry=True)
    kw.update(overrides)
    cfg = getattr(GameConfig, config_name)(**kw)
    return GameEngine(config=cfg, bots=bots, seed=seed, variant_cards=variants, version_deck=version_deck,
                      companies=companies, white_hats=white_hats)


def _company_color(r: Dict[str, Any]) -> str:
    if r.get("company_color"):
        return r["company_color"]
    from sim.config import V038_COMPANY_STARTING_COLORS

    c = V038_COMPANY_STARTING_COLORS.get(r.get("company_code") or "")
    return c.lower() if c else "none"  # v0.37 baselines: the colour the Company would get under v0.38


def play(task) -> Dict[str, Any]:
    """One game -> per-game record (pure function of the task; safe in a worker process)."""
    config_name, roster, players, seed, overrides = task
    res = build_engine(config_name, roster, players, seed, overrides).run_game()
    exits = {"red": 0, "blue": 0, "green": 0}
    for t in res.telemetry_history:
        for c, n in (t.exited_cubes or {}).items():
            k = getattr(c, "value", str(c))
            if k in exits:
                exits[k] += int(n)
    seats = sorted(res.rankings, key=lambda r: r["player_id"])
    nwin = max(1, len(res.winner_ids))
    rows = []
    for r in seats:
        rows.append({
            "player_id": r["player_id"], "bot_name": r["bot_name"], "secrets": r["secrets"],
            "is_patient_zero": r["is_patient_zero"], "market_share": r.get("market_share"),
            "market_share_min": r.get("market_share_min"), "company_color": _company_color(r),
            "path": classify_path(r.get("dice_owned_final_by_color", {})),
            "win": (1.0 / nwin) if r["player_id"] in res.winner_ids else 0.0,
            "secrets_by_source": dict(r.get("secrets_by_source", {})),
            "secret_faces_rolled": dict(r.get("secret_faces_rolled", {})),
            "secret_faces_banked": dict(r.get("secret_faces_banked", {})),
            "secret_yield_hist": {k: dict(v) for k, v in r.get("secret_yield_hist", {}).items()},
            "stranded_secrets": r.get("stranded_secrets", 0), "stranded_dice": r.get("stranded_dice", 0),
            "slots_glitched_by_source": dict(r.get("slots_glitched_by_source", {})),
            "slots_cleaned": {"die": r.get("slots_cleaned_by_die", 0), "face": r.get("slots_cleaned_by_face", 0),
                              "green_triage": r.get("slots_cleaned_by_green_triage", 0),
                              "graduation": r.get("slots_cleared_by_graduation", 0)},
            "max_glitched_slots": r.get("max_glitched_slots", 0),
            "zero_capacity_rounds": r.get("zero_capacity_rounds", 0),
            "purchases_by_color": dict(r.get("purchases_by_color", {})),
            # RSP-1 (spec §14.5.5); 0 / {} on configs without the RSP-1 levers
            "red_secrets_banked": r.get("red_secrets_banked", 0),
            "red_payout_secrets": r.get("red_payout_secrets", 0),
            "red_payout_places": dict(r.get("red_payout_places", {})),
            "red_wait_rounds": r.get("red_processing_wait_rounds", 0),
            "red_wait_count": r.get("red_processing_wait_count", 0),
        })
    winners = [x for x in rows if x["win"]]
    return {
        "seed": seed, "end_reason": res.end_reason.value, "rounds": res.total_rounds,
        "is_total_wipeout": res.is_total_wipeout, "winner_ids": list(res.winner_ids),
        "final_market_share": [x["market_share"] for x in rows], "cube_exits": exits,
        "winner_archetypes": [x["bot_name"] for x in winners],
        "winner_company_colors": [x["company_color"] for x in winners],
        "winner_paths": [x["path"] for x in winners],
        "winner_secrets": [x["secrets"] for x in winners],
        "red_secret_payouts_fired": getattr(res, "red_secret_payouts_fired", 0),
        "red_secret_payout_end_fired": bool(getattr(res, "red_secret_payout_end_fired", False)),
        "rounds_with_multi_red_banks": getattr(res, "rounds_with_multi_red_banks", 0),
        "red_pending_at_end": getattr(res, "red_pending_at_end", 0),
        "seats": rows,
    }


def play_all(config_name: str, roster: str, players: int, games: int, overrides: Dict[str, Any],
             seed0: int = 0, procs: int = 1) -> List[Dict[str, Any]]:
    tasks = [(config_name, roster, players, s, overrides) for s in range(seed0, seed0 + games)]
    if procs <= 1:
        return [play(t) for t in tasks]
    from multiprocessing import Pool

    with Pool(procs) as pool:
        return pool.map(play, tasks, chunksize=max(1, len(tasks) // (procs * 8)))  # ordered by seed


def _hist(vals) -> Dict[str, int]:
    return {str(k): v for k, v in sorted(Counter(vals).items())}


def _purchases_by_arch(seats_all: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    n, tot = Counter(), defaultdict(Counter)
    for x in seats_all:
        n[x["bot_name"]] += 1
        for c, k in x.get("purchases_by_color", {}).items():
            tot[x["bot_name"]][c] += k
    return {a: {c: round(v / n[a], 3) for c, v in sorted(tot[a].items())} for a in sorted(n)}


def summarise(records: List[Dict[str, Any]], config_name: str, roster: str, players: int,
              overrides: Dict[str, Any]) -> Dict[str, Any]:
    games = len(records)
    seats_all = [x for g in records for x in g["seats"]]
    nseat = len(seats_all) or 1
    rate = lambda w, n: round(w / n, 4) if n else None  # noqa: E731

    def by(key):
        n, w = Counter(), defaultdict(float)
        for x in seats_all:
            n[x[key]] += 1
            w[x[key]] += x["win"]
        return {k: rate(w[k], c) for k, c in sorted(n.items())}, dict(sorted(n.items()))

    def per_seat(field):
        tot = Counter()
        for x in seats_all:
            for k, v in x[field].items():
                tot[k] += v
        return {k: round(v / nseat, 3) for k, v in sorted(tot.items())}

    src = per_seat("secrets_by_source")
    banked = sum(v for x in seats_all for k, v in x["secrets_by_source"].items() if k.startswith("secret_face_"))
    stranded = sum(x["stranded_secrets"] for x in seats_all)
    rounds = [g["rounds"] for g in records]
    col_wr, col_n = by("company_color")
    path_wr, path_n = by("path")
    arch_wr, arch_n = by("bot_name")
    win_secrets = [s for g in records for s in g["winner_secrets"]]
    exits = {c: [g["cube_exits"][c] for g in records] for c in ("red", "blue", "green")}
    by_rounds = sorted(records, key=lambda g: (g["rounds"], g["seed"]))
    # RSP-1 (spec §14.5.5)
    payout_secrets = sum(x["red_payout_secrets"] for x in seats_all)
    face_secrets = banked
    pw_hits = pw_n = 0
    for g in records:
        top = max((x["red_payout_secrets"] for x in g["seats"]), default=0)
        if top > 0:
            pw_n += 1
            leaders = {x["player_id"] for x in g["seats"] if x["red_payout_secrets"] == top}
            pw_hits += bool(leaders & set(g["winner_ids"]))
    wait_n = sum(x["red_wait_count"] for x in seats_all)
    rsp1 = {
        "payouts_per_game": round(sum(g["red_secret_payouts_fired"] for g in records) / games, 3) if games else None,
        "end_payout_rate": rate(sum(1 for g in records if g["red_secret_payout_end_fired"]), games),
        "multi_red_bank_round_share": rate(sum(g["rounds_with_multi_red_banks"] for g in records), sum(rounds)),
        "red_secrets_banked_per_seat": round(sum(x["red_secrets_banked"] for x in seats_all) / nseat, 3),
        "payout_secrets_per_seat": round(payout_secrets / nseat, 3),
        "payout_vs_face_secret_share": (round(payout_secrets / (payout_secrets + face_secrets), 4)
                                        if payout_secrets + face_secrets else 0.0),
        "payout_leader_is_winner_rate": rate(pw_hits, pw_n),
        "red_mean_wait_rounds": round(sum(x["red_wait_rounds"] for x in seats_all) / wait_n, 3) if wait_n else None,
        "red_pending_at_end_per_game": round(sum(g["red_pending_at_end"] for g in records) / games, 3) if games else None,
    }
    yield_hist = defaultdict(Counter)
    for x in seats_all:
        for c, h in x.get("secret_yield_hist", {}).items():
            for y_val, count in h.items():
                yield_hist[c][str(y_val)] += int(count)
    yield_hist_totals = {c: dict(sorted(cnt.items())) for c, cnt in sorted(yield_hist.items())}

    return {
        "rsp1": rsp1,
        "config": config_name, "roster": roster, "overrides": {str(k): v for k, v in overrides.items()},
        "players": players, "games": games, "path_rule": PATH_RULE,
        "endings": {k: round(v / games, 4) for k, v in sorted(Counter(g["end_reason"] for g in records).items())},
        "avg_rounds": round(sum(rounds) / games, 3) if games else None,
        "rounds_hist": _hist(rounds),
        "breach_rate": rate(sum(1 for g in records if any(x["is_patient_zero"] for x in g["seats"])), games),
        "total_wipeout_rate": rate(sum(1 for g in records if g["is_total_wipeout"]), games),
        "secrets_by_source_per_seat": src,
        "secret_faces_rolled_per_seat": per_seat("secret_faces_rolled"),
        "secret_faces_banked_per_seat": per_seat("secret_faces_banked"),
        "secret_yield_hist_totals": yield_hist_totals,
        "stranded_share": round(stranded / (stranded + banked), 4) if stranded + banked else 0.0,
        "stranded_dice_per_seat": round(sum(x["stranded_dice"] for x in seats_all) / nseat, 3),
        "slots_glitched_per_seat": per_seat("slots_glitched_by_source"),
        "slots_cleaned_per_seat": per_seat("slots_cleaned"),
        "max_glitched_slots_avg": round(sum(x["max_glitched_slots"] for x in seats_all) / nseat, 3),
        "zero_capacity_rounds_per_seat": round(sum(x["zero_capacity_rounds"] for x in seats_all) / nseat, 3),
        "market_share_min_avg": round(sum(x["market_share_min"] or 0 for x in seats_all) / nseat, 3),
        "final_market_share_hist": _hist(x["market_share"] for x in seats_all),
        "cube_exits_avg": {c: round(sum(v) / games, 3) for c, v in exits.items()} if games else {},
        "winner_secrets_avg": round(sum(win_secrets) / len(win_secrets), 3) if win_secrets else None,
        "winner_secrets_hist": _hist(win_secrets),
        "win_rate_by_company_color": col_wr, "seats_by_company_color": col_n,
        "win_rate_by_path": path_wr, "seats_by_path": path_n,
        "win_rate_by_archetype": arch_wr, "seats_by_archetype": arch_n,
        "purchases_per_seat_by_archetype": _purchases_by_arch(seats_all),
        "winner_archetype_counts": _hist(a for g in records for a in g["winner_archetypes"]),
        "outliers": {
            "shortest": [g["seed"] for g in by_rounds[:5]],
            "longest": [g["seed"] for g in by_rounds[::-1][:5]],
            "highest_winner_secrets": [g["seed"] for g in sorted(
                records, key=lambda g: (-max(g["winner_secrets"] or [0]), g["seed"]))[:5]],
            "total_wipeout": [g["seed"] for g in records if g["is_total_wipeout"]][:20],
            "round_limit": [g["seed"] for g in records if g["end_reason"] == "round_limit"][:20],
        },
    }


def run(config_name: str, players: int, games: int, overrides: Dict[str, Any], seed0: int = 0,
        roster: str = "mixed1", procs: int = 1, keep_records: bool = False) -> Dict[str, Any]:
    recs = play_all(config_name, roster, players, games, overrides, seed0, procs)
    out = summarise(recs, config_name, roster, players, overrides)
    if keep_records:
        out["records"] = recs
    return out


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--games", type=int, default=300)
    ap.add_argument("--players", type=int, nargs="+", default=[3])
    ap.add_argument("--config", default="v038_roster", choices=CONFIGS)
    ap.add_argument("--roster", default="mixed1", choices=ROSTERS,
                    help="mixed1 (default, roster rule): one MixedPolicyBot seat at seed %% P; archetypes: none")
    ap.add_argument("--seed0", type=int, default=0)
    ap.add_argument("--procs", type=int, default=1, help="worker processes (results identical for any N)")
    ap.add_argument("--set", dest="overrides", action="append", default=[], help="GameConfig override key=JSON")
    ap.add_argument("--out", default=None, help="write JSON (summary + per-game records) here")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--allow-noop", action="store_true", help="skip the ineffective-override check")
    a = ap.parse_args(argv)
    ov = _parse_overrides(a.overrides, a.config)
    if not a.allow_noop:
        for n in a.players:
            check_overrides_effective(a.config, a.roster, n, ov, a.seed0)
    out = [run(a.config, n, a.games, ov, a.seed0, a.roster, a.procs, keep_records=bool(a.out)) for n in a.players]
    print(json.dumps([{k: v for k, v in d.items() if k != "records"} for d in out], indent=2, sort_keys=True))
    if a.out:
        tag = overrides_tag(ov)
        path = a.out if not tag else a.out.replace(".json", f"_{tag}.json")
        guard_overwrite(path, a.overwrite)
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(out, fh, sort_keys=True)


if __name__ == "__main__":
    main()
