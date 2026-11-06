"""Golden-fixture capture for the v0.34 research tracks / company setup (INV-RT-LEGACY-PARITY-01).

Captured at commit ``9a46982`` *before* the v0.35 research-track refactor, using ``GameConfig(...)``
(the v0.34 default at that commit). ``tests/test_v350_research_tracks.py`` replays the same scenarios
with ``GameConfig.legacy_v034(...)`` and compares bit-for-bit.

300 seeds x 2/3/4P x {mixed, asym}. Each record keeps the EndGameResult summary, the rankings, and
per-round staged / exited / attack cube counts.

Regenerate (only when intentionally changing the legacy baseline):
    python3 -m tests.fixtures.v034_parity.capture
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable, Dict

from tests.fixtures.v033_parity.capture import RANKING_KEYS, _cubes, _jsonable

FIXTURE_DIR = os.path.dirname(os.path.abspath(__file__))
SEEDS = tuple(range(300))
PLAYER_COUNTS = (2, 3, 4)
SCENARIOS = ("mixed", "asym")


def run_scenario(config_factory: Callable[..., Any], scenario: str, num_players: int, seed: int) -> Dict[str, Any]:
    from sim.bots import (AccelerationistBot, AdaptiveBalancedBot, RecklessSaboteurBot,
                          SecOpsTurtleBot, VentureGreedBot)
    from sim.engine import GameEngine

    bot_classes = [AdaptiveBalancedBot, SecOpsTurtleBot, VentureGreedBot, AccelerationistBot, RecklessSaboteurBot]
    offset = seed % len(bot_classes)
    bots = [bot_classes[(offset + i) % len(bot_classes)](i) for i in range(num_players)]
    kwargs = {"num_players": num_players}
    if scenario == "asym":
        kwargs["enable_corporate_asymmetry"] = True
    engine = GameEngine(config_factory(**kwargs), bots, seed=seed)
    result = engine.run_game()
    return {
        "end_reason": result.end_reason.value,
        "total_rounds": result.total_rounds,
        "winner_id": result.winner_id,
        "is_total_wipeout": result.is_total_wipeout,
        "rankings": [{k: _jsonable(r.get(k)) for k in RANKING_KEYS} for r in result.rankings],
        "rounds": [
            [_cubes(t.staged_cubes), _cubes(t.exited_cubes), _cubes(t.attack_strengths)]
            for t in result.telemetry_history
        ],
    }


def fixture_path(scenario: str, num_players: int) -> str:
    return os.path.join(FIXTURE_DIR, f"{scenario}_{num_players}p.json")


def main() -> None:
    from sim.config import GameConfig

    factory = getattr(GameConfig, "legacy_v034", GameConfig)
    for scenario in SCENARIOS:
        for n in PLAYER_COUNTS:
            data = {str(s): run_scenario(factory, scenario, n, s) for s in SEEDS}
            with open(fixture_path(scenario, n), "w", encoding="utf-8") as fh:
                json.dump(data, fh, sort_keys=True, separators=(",", ":"))
    print("captured", FIXTURE_DIR)


if __name__ == "__main__":
    main()
