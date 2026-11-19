"""v0.45 parity golden (INV-PARITY): one short digest per game, 100 seeds x 2/3/4P x {v045, v045_roster}.

Capture (on the untouched engine):  python3 -m tests.parity_v045.capture
The golden is ``golden.json`` ({"config|players|seed": digest}); the test is ``tests/test_v460_parity.py``.
(Stored outside ``tests/fixtures/`` because that directory is write-protected in this workspace.)
"""

from __future__ import annotations

import hashlib
import json
import os
import random
from typing import Any, Dict

from sim.config import GameConfig
from sim.engine import GameEngine
from sim.entities import get_random_companies, get_random_setup, get_random_white_hats
from tests.fixtures.v035_parity.capture import _bot_classes

HERE = os.path.dirname(os.path.abspath(__file__))
GOLDEN_PATH = os.path.join(HERE, "golden.json")
CONFIGS = ("v045", "v045_roster")
PLAYERS = (2, 3, 4)
SEEDS = tuple(range(42, 142))


def build_engine(config_name: str, players: int, seed: int) -> GameEngine:
    classes = _bot_classes()
    rng = random.Random(seed)
    bots = [classes[(seed * players + i) % len(classes)](i) for i in range(players)]
    rng.shuffle(bots)
    for i, b in enumerate(bots):
        b.player_id = i
    variants, version_deck = get_random_setup(rng, profile="STANDARD")
    companies = get_random_companies(players, rng)
    white_hats = get_random_white_hats(players, rng)
    cfg = getattr(GameConfig, config_name)(
        num_players=players, starting_money=6, starting_gray_dice=3, starting_purple_dice=1,
        starting_purple_reserve=1, corruption_track_profile="STANDARD", enable_corporate_asymmetry=True,
    )
    return GameEngine(config=cfg, bots=bots, seed=seed, variant_cards=variants, version_deck=version_deck,
                      companies=companies, white_hats=white_hats)


def digest(config_name: str, players: int, seed: int) -> str:
    res = build_engine(config_name, players, seed).run_game()
    payload: Dict[str, Any] = {
        "end": str(getattr(res.end_reason, "value", res.end_reason)),
        "rounds": res.total_rounds,
        "winners": sorted(res.winner_ids),
        "wipeout": bool(res.is_total_wipeout),
        "rankings": res.rankings,
        "snapshots": [t.player_snapshots for t in res.telemetry_history],
    }
    return hashlib.sha1(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:16]


def capture() -> Dict[str, str]:
    return {f"{c}|{p}|{s}": digest(c, p, s) for c in CONFIGS for p in PLAYERS for s in SEEDS}


if __name__ == "__main__":
    out = capture()
    with open(GOLDEN_PATH, "w") as fh:
        json.dump(out, fh, sort_keys=True, separators=(",", ":"))
    print(f"wrote {len(out)} digests -> {GOLDEN_PATH}")
