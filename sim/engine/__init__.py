"""Game engine package for Rogue Agent."""

from sim.engine.state import EndGameResult, GameState, PlayerState, ProductionRole, RoundTelemetry
from sim.engine.core import GameEngine
from sim.engine.end_game import evaluate_end_game

__all__ = [
    "GameEngine",
    "PlayerState",
    "ProductionRole",
    "GameState",
    "RoundTelemetry",
    "EndGameResult",
    "evaluate_end_game",
]
