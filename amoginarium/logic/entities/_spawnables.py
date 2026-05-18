"""
Collects every spawn-able entity.

Path: amoginarium/logic/entities/_spawnables.py
Project: amoginarium
Created: 28.03.2026
Authors: Nilusink, LukasKrah
"""

import typing as tp

from icecream import ic

from ._base import LogicGameEntity
from ._dynamic_entities import DYNAMIC_ENTITIES
from ._weaponry import ExactoTurret, VisualRadarSensor, VisualSensor

# from ._static_turret import BaseTurret, SniperTurret, AkTurret, MinigunTurret, \
#     MortarTurret, FlakTurret, CRAMTurret
# from ._sensors import Radar
# from ._text_entity import TextEntity
from ._weaponry.templates import Bullet
from ._world import TextEntity

# noinspection PyTypeChecker
SPAWNABLES: dict[str, tp.Type[LogicGameEntity]] = {
    e.cid(): e
    for e in [VisualSensor, VisualRadarSensor, TextEntity, ExactoTurret, Bullet]
}
SPAWNABLES.update(DYNAMIC_ENTITIES)
