"""Golden-fixture capture for the v0.35.0 baseline (INV-MS-LEGACY-PARITY-01).

Captured from a clean checkout of commit ``b1b1f11`` (v0.35.0, without the uncommitted Phase 44
levers) *before* the v0.36 Market Share refactor, using ``GameConfig(...)`` (the v0.35 default at
that commit). ``tests/test_v360_market_share.py`` replays the same scenarios with ``GameConfig.legacy_v035`` (``GameConfig()``
is v0.36.0 since Phase B) and compares bit-for-bit.

300 seeds x 2/3/4P x {mixed, asym, setup}:
- ``mixed`` / ``asym``: as in ``tests/fixtures/v034_parity`` (default variant cards).
- ``setup``: seeded ``random.Random(seed)`` -> bot rotation + shuffle, ``get_random_setup(rng, "STANDARD")``,
  ``get_random_companies``, ``get_random_white_hats`` (mirrors ``scripts/run_v360_red_rebalance_sweep.build_engine``),
  so the v0.35 Red R2/R3 Phase 4 bonuses and the Tier 2 ransom check are exercised.

Each record keeps the EndGameResult summary, the rankings, per-round staged / exited / attack cube
counts, and per-round Phase 4 money / secrets per player (catches ransom drift).

Regenerate (only when intentionally changing the legacy baseline):
    python3 -m tests.fixtures.v035_parity.capture
"""

from __future__ import annotations

import json
import os
import random
from typing import Any, Callable, Dict

from tests.fixtures.v033_parity.capture import RANKING_KEYS, _cubes, _jsonable

FIXTURE_DIR = os.path.dirname(os.path.abspath(__file__))
SEEDS = tuple(range(300))
PLAYER_COUNTS = (2, 3, 4)
# "asym" is accepted by run_scenario but not stored: at v0.35 (no company setup bonuses) it is byte-identical
# to "mixed" (verified at capture time, 2026-11-06).
SCENARIOS = ("mixed", "setup")


def _bot_classes():
    from sim.bots import (AccelerationistBot, AdaptiveBalancedBot, RecklessSaboteurBot,
                          SecOpsTurtleBot, VentureGreedBot)

    return [AdaptiveBalancedBot, SecOpsTurtleBot, VentureGreedBot, AccelerationistBot, RecklessSaboteurBot]


def build_engine(config_factory: Callable[..., Any], scenario: str, num_players: int, seed: int):
    from sim.engine import GameEngine

    bot_classes = _bot_classes()
    if scenario == "setup":
        from sim.entities import get_random_companies, get_random_setup, get_random_white_hats

        rng = random.Random(seed)
        bots = [bot_classes[(seed * num_players + i) % len(bot_classes)](i) for i in range(num_players)]
        rng.shuffle(bots)
        for i, b in enumerate(bots):
            b.player_id = i
        variants, version_deck = get_random_setup(rng, profile="STANDARD")
        companies = get_random_companies(num_players, rng)
        white_hats = get_random_white_hats(num_players, rng)
        cfg = config_factory(
            num_players=num_players, starting_money=6, starting_gray_dice=3, starting_purple_dice=1,
            starting_purple_reserve=1, corruption_track_profile="STANDARD", enable_corporate_asymmetry=True,
        )
        return GameEngine(config=cfg, bots=bots, seed=seed, variant_cards=variants, version_deck=version_deck,
                          companies=companies, white_hats=white_hats)
    offset = seed % len(bot_classes)
    bots = [bot_classes[(offset + i) % len(bot_classes)](i) for i in range(num_players)]
    kwargs = {"num_players": num_players}
    if scenario == "asym":
        kwargs["enable_corporate_asymmetry"] = True
    return GameEngine(config_factory(**kwargs), bots, seed=seed)


def run_scenario(config_factory: Callable[..., Any], scenario: str, num_players: int, seed: int) -> Dict[str, Any]:
    engine = build_engine(config_factory, scenario, num_players, seed)
    result = engine.run_game()
    return {
        "end_reason": result.end_reason.value,
        "total_rounds": result.total_rounds,
        "winner_id": result.winner_id,
        "is_total_wipeout": result.is_total_wipeout,
        "rankings": [{k: _jsonable(r.get(k)) for k in RANKING_KEYS} for r in result.rankings],
        "rounds": [
            [_cubes(t.staged_cubes), _cubes(t.exited_cubes), _cubes(t.attack_strengths),
             [[s["money"], s["secrets"]] for s in t.phase_snapshots.get(4, [])]]
            for t in result.telemetry_history
        ],
    }


def fixture_path(scenario: str, num_players: int) -> str:
    return os.path.join(FIXTURE_DIR, f"{scenario}_{num_players}p.json")


def main() -> None:
    from sim.config import GameConfig

    factory = getattr(GameConfig, "legacy_v035", GameConfig)
    for scenario in SCENARIOS:
        for n in PLAYER_COUNTS:
            data = {str(s): run_scenario(factory, scenario, n, s) for s in SEEDS}
            with open(fixture_path(scenario, n), "w", encoding="utf-8") as fh:
                json.dump(data, fh, sort_keys=True, separators=(",", ":"))
    print("captured", FIXTURE_DIR)


if __name__ == "__main__":
    main()
