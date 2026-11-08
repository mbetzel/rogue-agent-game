"""Golden-fixture capture for v0.37 with the lever A switch on (``GameConfig.v037(bot_pr_push=True)``).

docs/specs/lever_a_roster_upgrade_spec.md §6. 300 seeds x 2/3/4P x {mixed, setup} via
``tests.fixtures.v036_parity.capture.run_scenario``, plus ``ref1_3p.json``: 10 seeds, 3P, one
``ReferenceSearchBot`` seat (seat ``seed % 3``) in the v0.35 ``_bot_classes`` rotation.

Regenerate (only when intentionally changing lever A behaviour):
    python3 -m tests.fixtures.v037_push.capture
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict

from tests.fixtures.v033_parity.capture import _cubes, _jsonable
from tests.fixtures.v036_parity.capture import PLAYER_COUNTS, RANKING_KEYS_V036, SCENARIOS, SEEDS, run_scenario

FIXTURE_DIR = os.path.dirname(os.path.abspath(__file__))
REF_SEEDS = tuple(range(10))


def config_factory(**kw: Any):
    from sim.config import GameConfig

    return GameConfig.v037(bot_pr_push=True, **kw)


def fixture_path(scenario: str, num_players: int) -> str:
    return os.path.join(FIXTURE_DIR, f"{scenario}_{num_players}p.json")


def run_ref1(seed: int, num_players: int = 3) -> Dict[str, Any]:
    from sim.bots.reference_search import ReferenceSearchBot, ReferenceSearchEngine
    from tests.fixtures.v035_parity.capture import _bot_classes

    classes = _bot_classes()
    off = seed % len(classes)
    bots = [classes[(off + i) % len(classes)](i) for i in range(num_players)]
    sp = seed % num_players
    bots[sp] = ReferenceSearchBot(sp, seed)
    eng = ReferenceSearchEngine(config_factory(num_players=num_players), bots, seed=seed)
    result = eng.run_game()
    return {
        "end_reason": result.end_reason.value,
        "total_rounds": result.total_rounds,
        "winner_ids": list(result.winner_ids),
        "end_triggers": list(result.end_triggers),
        "rankings": [{k: _jsonable(r.get(k)) for k in RANKING_KEYS_V036} for r in result.rankings],
        "rounds": [
            [_cubes(t.staged_cubes), _cubes(t.exited_cubes),
             [[s["money"], s["secrets"], s.get("market_share")] for s in t.phase_snapshots.get(4, [])]]
            for t in result.telemetry_history
        ],
        "searched": bots[sp].stats["searched"],
        "rollouts": bots[sp].stats["rollouts"],
    }


def main() -> None:
    for scenario in SCENARIOS:
        for n in PLAYER_COUNTS:
            data = {str(s): run_scenario(config_factory, scenario, n, s) for s in SEEDS}
            with open(fixture_path(scenario, n), "w", encoding="utf-8") as fh:
                json.dump(data, fh, sort_keys=True, separators=(",", ":"))
    data = {str(s): run_ref1(s) for s in REF_SEEDS}
    with open(os.path.join(FIXTURE_DIR, "ref1_3p.json"), "w", encoding="utf-8") as fh:
        json.dump(data, fh, sort_keys=True, separators=(",", ":"))
    print("captured", FIXTURE_DIR)


if __name__ == "__main__":
    main()
