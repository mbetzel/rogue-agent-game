"""v0.46 parity golden (INV-LOCK-07): one short digest per game.

Keys: ``config|players|seed`` for the archetype-roster games (v046, v046_roster x 2/3/4P x seeds 42..141) and
``config|mixed1|players|seed`` for the Mixed-seat games (v046_roster x 2/3/4P x seeds 42..91).

Capture (on the engine before any v0.47 change):  python3 -m tests.parity_v046.capture
The golden is ``golden.json``; the test is ``tests/test_v470_parity.py``.
(Stored outside ``tests/fixtures/`` because that directory is write-protected in this workspace.)
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict

from tests.parity_v045.capture import build_engine as _build_arch

HERE = os.path.dirname(os.path.abspath(__file__))
GOLDEN_PATH = os.path.join(HERE, "golden.json")
CONFIGS = ("v046", "v046_roster")
PLAYERS = (2, 3, 4)
SEEDS = tuple(range(42, 142))
MIXED_CONFIGS = ("v046_roster",)
MIXED_SEEDS = tuple(range(42, 92))


def _hash(res) -> str:
    payload: Dict[str, Any] = {
        "end": str(getattr(res.end_reason, "value", res.end_reason)),
        "rounds": res.total_rounds,
        "winners": sorted(res.winner_ids),
        "wipeout": bool(res.is_total_wipeout),
        "rankings": res.rankings,
        "snapshots": [t.player_snapshots for t in res.telemetry_history],
    }
    return hashlib.sha1(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:16]


def digest(config_name: str, players: int, seed: int, roster: str = "archetypes") -> str:
    if roster == "mixed1":
        from scripts.run_v380_secret_faces_sweep import build_engine

        return _hash(build_engine(config_name, "mixed1", players, seed, {}).run_game())
    return _hash(_build_arch(config_name, players, seed).run_game())


def keys():
    for c in CONFIGS:
        for p in PLAYERS:
            for s in SEEDS:
                yield f"{c}|{p}|{s}"
    for c in MIXED_CONFIGS:
        for p in PLAYERS:
            for s in MIXED_SEEDS:
                yield f"{c}|mixed1|{p}|{s}"


def digest_for_key(key: str) -> str:
    parts = key.split("|")
    if parts[1] == "mixed1":
        return digest(parts[0], int(parts[2]), int(parts[3]), "mixed1")
    return digest(parts[0], int(parts[1]), int(parts[2]))


def capture() -> Dict[str, str]:
    return {k: digest_for_key(k) for k in keys()}


if __name__ == "__main__":
    out = capture()
    with open(GOLDEN_PATH, "w") as fh:
        json.dump(out, fh, sort_keys=True, separators=(",", ":"))
    print(f"wrote {len(out)} digests -> {GOLDEN_PATH}")
