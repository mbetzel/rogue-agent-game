"""Golden-fixture capture for the v0.38 C2 baseline (spec §14.5.8 test 1, INV-RSP-07).

Captured from commit ``11297a4`` (Phase 49 C2 HEAD) *before* any RSP-1 edit.
``tests/test_v380_secret_faces.py::TestRSP1`` replays the scenarios with ``GameConfig.v038`` and
``GameConfig.v038b`` and compares bit-for-bit.

50 seeds x 2/3/4P x {mixed} x {v038, v038b}. Record format = ``tests/fixtures/v037_parity`` (full end-game
record, per-round cube counts, every per-phase snapshot).

Regenerate (only when intentionally changing the v0.38 C2 baseline):
    python3 -m tests.fixtures.v038b_parity.capture
"""

from __future__ import annotations

import json
import os

from tests.fixtures.v037_parity.capture import config_factory, run_scenario

FIXTURE_DIR = os.path.dirname(os.path.abspath(__file__))
SEEDS = tuple(range(50))
PLAYER_COUNTS = (2, 3, 4)
SCENARIOS = ("mixed",)
CONFIGS = ("v038", "v038b")


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
