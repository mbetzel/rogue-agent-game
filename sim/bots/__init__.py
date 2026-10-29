"""Bot archetypes and AI decision heuristics for Rogue Agent simulation."""

from sim.bots.base import BaseBot, Phase3ActionPlan, choose_backlash_die_index, plan_final_round_repairs
from sim.bots.adaptive_balanced import AdaptiveBalancedBot
from sim.bots.secops_turtle import SecOpsTurtleBot
from sim.bots.venture_greed import VentureGreedBot
from sim.bots.accelerationist import AccelerationistBot
from sim.bots.reckless_saboteur import RecklessSaboteurBot

__all__ = [
    "BaseBot",
    "Phase3ActionPlan",
    "choose_backlash_die_index",
    "plan_final_round_repairs",
    "AdaptiveBalancedBot",
    "SecOpsTurtleBot",
    "VentureGreedBot",
    "AccelerationistBot",
    "RecklessSaboteurBot",
]
