"""Golden-fixture capture for the v0.33 three-phase round sequence (INV-SEQ-LEGACY-PARITY-01).

The JSON fixtures in this directory were captured at commit ``20e8c80`` *before* the v0.34
six-phase refactor, using ``GameConfig(...)`` (which was the v0.33 default at that commit).
``tests/test_v340_six_phase_sequence.py`` replays the same scenarios with
``GameConfig.legacy_v033(...)`` and compares bit-for-bit.

Regenerate (only when intentionally changing the legacy baseline):
    python3 -m tests.fixtures.v033_parity.capture
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable, Dict, List

FIXTURE_DIR = os.path.dirname(os.path.abspath(__file__))
SEEDS = (11, 2024, 90210)
PLAYER_COUNTS = (2, 3, 4)
SCENARIOS = ("mixed", "asym")

RANKING_KEYS = (
    "player_id", "bot_name", "rank", "portfolio_value", "overflow_penalties", "net_score",
    "is_patient_zero", "elimination_reason", "secrets", "money", "patches", "breach_depth",
    "ready_dice_count", "ready_colored_dice_count", "unpatched_dice_count",
    "total_contractors_hired", "total_rerolls_used", "archetype_code",
    "ability_v1_status", "ability_v2_status", "ability_v3_status",
)


def _cubes(d: Dict[Any, int]) -> Dict[str, int]:
    return {getattr(k, "value", str(k)): int(v) for k, v in sorted(d.items(), key=lambda kv: getattr(kv[0], "value", str(kv[0])))}


def _jsonable(v: Any) -> Any:
    if isinstance(v, dict):
        return {str(getattr(k, "value", k)): _jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    if hasattr(v, "value") and not isinstance(v, (int, float, str, bool)):
        return v.value
    if isinstance(v, (int, float, str, bool)) or v is None:
        return v
    return str(v)


def run_scenario(config_factory: Callable[..., Any], scenario: str, num_players: int, seed: int) -> Dict[str, Any]:
    from sim.bots import (AccelerationistBot, AdaptiveBalancedBot, RecklessSaboteurBot,
                          SecOpsTurtleBot, VentureGreedBot)
    from sim.engine import GameEngine

    bot_classes = [AdaptiveBalancedBot, SecOpsTurtleBot, VentureGreedBot, AccelerationistBot, RecklessSaboteurBot]
    offset = seed % len(bot_classes)
    bots = [bot_classes[(offset + i) % len(bot_classes)](i) for i in range(num_players)]
    if scenario == "asym":
        cfg = config_factory(num_players=num_players, enable_corporate_asymmetry=True)
    else:
        cfg = config_factory(num_players=num_players)
    engine = GameEngine(cfg, bots, seed=seed)
    result = engine.run_game()
    return {
        "end_reason": result.end_reason.value,
        "total_rounds": result.total_rounds,
        "winner_id": result.winner_id,
        "is_total_wipeout": result.is_total_wipeout,
        "singularity_reached": result.singularity_reached,
        "total_buffer_overflows": result.total_buffer_overflows,
        "rankings": [{k: _jsonable(r.get(k)) for k in RANKING_KEYS} for r in result.rankings],
        "telemetry": [
            {
                "round_number": t.round_number,
                "active_version_name": t.active_version_name,
                "corruption_track": t.corruption_track,
                "staged": _cubes(t.staged_cubes),
                "stuck_before": _cubes(t.stuck_cubes_before),
                "exited": _cubes(t.exited_cubes),
                "stuck_after": _cubes(t.stuck_cubes_after),
                "attack": _cubes(t.attack_strengths),
                "buffer_overflow": t.buffer_overflow,
                "player_snapshots": _jsonable(t.player_snapshots),
            }
            for t in result.telemetry_history
        ],
    }


def fixture_path(scenario: str, num_players: int) -> str:
    return os.path.join(FIXTURE_DIR, f"{scenario}_{num_players}p.json")


def capture_all(config_factory: Callable[..., Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for scenario in SCENARIOS:
        for n in PLAYER_COUNTS:
            out[f"{scenario}_{n}p"] = {str(seed): run_scenario(config_factory, scenario, n, seed) for seed in SEEDS}
    return out


def main() -> None:
    from sim.config import GameConfig

    factory = getattr(GameConfig, "legacy_v033", GameConfig)
    for name, data in capture_all(factory).items():
        with open(os.path.join(FIXTURE_DIR, f"{name}.json"), "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=1, sort_keys=True)
    print("captured", FIXTURE_DIR)


if __name__ == "__main__":
    main()
