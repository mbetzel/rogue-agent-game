"""Golden-fixture capture for the v0.36.0 baseline (INV-MLB-PARITY-01).

Captured from a clean checkout of commit ``e1039ae`` (v0.36.0, before the v0.37.0 Market Leader Bonus levers)
using ``GameConfig.v036``. ``tests/test_v370_market_leader_bonus.py`` replays the same scenarios with
``GameConfig.legacy_v036`` (and its ``v036`` alias; ``GameConfig()`` is v0.37.0 since Phase B) and compares
bit-for-bit.

300 seeds x 2/3/4P x {mixed, setup} (``build_engine`` / bot rotation reused from ``tests/fixtures/v035_parity``).
Each record keeps the EndGameResult summary (incl. ``winner_ids``, ``end_triggers``, ``tiebreak_decided_by``), the
rankings (v0.33 keys plus the v0.36 Market Share keys), per-round staged / exited / attack cube counts, and per-round
Phase 4 ``[money, secrets, market_share]`` per player.

Regenerate (only when intentionally changing the v0.36.0 baseline):
    python3 -m tests.fixtures.v036_parity.capture
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable, Dict

from tests.fixtures.v033_parity.capture import RANKING_KEYS, _cubes, _jsonable
from tests.fixtures.v035_parity.capture import _bot_classes, build_engine  # noqa: F401  (re-exported)

FIXTURE_DIR = os.path.dirname(os.path.abspath(__file__))
SEEDS = tuple(range(300))
PLAYER_COUNTS = (2, 3, 4)
SCENARIOS = ("mixed", "setup")
RANKING_KEYS_V036 = RANKING_KEYS + (
    "market_share", "market_share_min", "market_share_regained", "research_spent_regain",
    "red_blocked_any_total", "red_unblocked_total",
)


def run_scenario(config_factory: Callable[..., Any], scenario: str, num_players: int, seed: int) -> Dict[str, Any]:
    engine = build_engine(config_factory, scenario, num_players, seed)
    result = engine.run_game()
    return {
        "end_reason": result.end_reason.value,
        "total_rounds": result.total_rounds,
        "winner_id": result.winner_id,
        "winner_ids": list(result.winner_ids),
        "is_total_wipeout": result.is_total_wipeout,
        "end_triggers": list(result.end_triggers),
        "tiebreak_decided_by": result.tiebreak_decided_by,
        "rankings": [{k: _jsonable(r.get(k)) for k in RANKING_KEYS_V036} for r in result.rankings],
        "rounds": [
            [_cubes(t.staged_cubes), _cubes(t.exited_cubes), _cubes(t.attack_strengths),
             [[s["money"], s["secrets"], s.get("market_share")] for s in t.phase_snapshots.get(4, [])]]
            for t in result.telemetry_history
        ],
    }


def fixture_path(scenario: str, num_players: int) -> str:
    return os.path.join(FIXTURE_DIR, f"{scenario}_{num_players}p.json")


def main() -> None:
    from sim.config import GameConfig

    for scenario in SCENARIOS:
        for n in PLAYER_COUNTS:
            data = {str(s): run_scenario(GameConfig.legacy_v036, scenario, n, s) for s in SEEDS}
            with open(fixture_path(scenario, n), "w", encoding="utf-8") as fh:
                json.dump(data, fh, sort_keys=True, separators=(",", ":"))
    print("captured", FIXTURE_DIR)


if __name__ == "__main__":
    main()
