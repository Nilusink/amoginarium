"""
Collects every spawn-able entity.

| ``Path``: amoginarium/logic/entities/_spawnables.py
| ``Project``: amoginarium
| ``Created``: 28.03.2026
| ``Authors``: Nilusink, LukasKrah
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from icecream import ic

from ._dynamic_entities import DYNAMIC_ENTITIES
from ._weaponry import ExactoTurret, VisualRadarSensor, VisualSensor

# from ._static_turret import BaseTurret, SniperTurret, AkTurret, MinigunTurret, \
#     MortarTurret, FlakTurret, CRAMTurret
# from ._sensors import Radar
# from ._text_entity import TextEntity
from ._weaponry.templates import Bullet
from ._world import TextEntity

if TYPE_CHECKING:
    from ._base import LogicGameEntity

# noinspection PyTypeChecker
SPAWNABLES: dict[str, type[LogicGameEntity]] = {
    e.cid(): e
    for e in [VisualSensor, VisualRadarSensor, TextEntity, ExactoTurret, Bullet]
}
SPAWNABLES.update(DYNAMIC_ENTITIES)
