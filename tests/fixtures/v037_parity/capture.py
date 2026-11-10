"""Golden-fixture capture for the v0.37.0 baseline (INV-SF-PARITY-01).

Captured from commit ``0b80154`` (Phase 48 HEAD) *before* any Phase 49 (v0.38 Secret faces) edit.
``tests/test_v380_secret_faces.py`` replays the scenarios with ``GameConfig()``, ``GameConfig.v037`` and
``GameConfig.v037_roster`` and compares bit-for-bit.

100 seeds x 2/3/4P x {mixed, setup} x {v037, v037_roster} (``build_engine`` / bot rotation from
``tests/fixtures/v035_parity``). Each record keeps the EndGameResult summary, every ranking key (full
end-game record), per-round cube counts and every per-phase snapshot (money, secrets, Market Share, zone counts).

Regenerate (only when intentionally changing the v0.37.0 baseline):
    python3 -m tests.fixtures.v037_parity.capture
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable, Dict

from tests.fixtures.v033_parity.capture import _cubes, _jsonable
from tests.fixtures.v035_parity.capture import build_engine

FIXTURE_DIR = os.path.dirname(os.path.abspath(__file__))
SEEDS = tuple(range(100))
PLAYER_COUNTS = (2, 3, 4)
SCENARIOS = ("mixed", "setup")
CONFIGS = ("v037", "v037_roster")


def config_factory(name: str) -> Callable[..., Any]:
    from sim.config import GameConfig

    return getattr(GameConfig, name)


def _snap(s: Dict[str, Any]):
    return [s["money"], s["secrets"], s.get("market_share"), s["ready_dice_count"], s["in_production_dice_count"],
            s["glitched_dice_count"], s["scanned_dice_count"], s["contractor_dice_count"], s["is_patient_zero"]]


def run_scenario(factory: Callable[..., Any], scenario: str, num_players: int, seed: int) -> Dict[str, Any]:
    result = build_engine(factory, scenario, num_players, seed).run_game()
    return {
        "end_reason": result.end_reason.value,
        "total_rounds": result.total_rounds,
        "winner_ids": list(result.winner_ids),
        "is_total_wipeout": result.is_total_wipeout,
        "end_triggers": list(result.end_triggers),
        "tiebreak_decided_by": result.tiebreak_decided_by,
        "rankings": [{k: _jsonable(v) for k, v in sorted(r.items())} for r in result.rankings],
        "rounds": [
            [_cubes(t.staged_cubes), _cubes(t.exited_cubes), _cubes(t.attack_strengths),
             {str(ph): [_snap(s) for s in snaps] for ph, snaps in sorted(t.phase_snapshots.items())}]
            for t in result.telemetry_history
        ],
    }


def fixture_path(config_name: str, scenario: str, num_players: int) -> str:
    return os.path.join(FIXTURE_DIR, f"{config_name}_{scenario}_{num_players}p.json")


def main() -> None:
    for name in CONFIGS:
        for scenario in SCENARIOS:
            for n in PLAYER_COUNTS:
                data = {str(s): run_scenario(config_factory(name), scenario, n, s) for s in SEEDS}
                with open(fixture_path(name, scenario, n), "w", encoding="utf-8") as fh:
                    json.dump(data, fh, sort_keys=True, separators=(",", ":"))
    print("captured", FIXTURE_DIR)


if __name__ == "__main__":
    main()
