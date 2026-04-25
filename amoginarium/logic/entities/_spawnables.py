"""
_spawnables.py
15.03.2026

collects every spawn-able entity

Author:
Nilusink
"""
import typing as tp
from icecream import ic

from ._turrets import MinigunTurret, SniperTurret, AkTurret, MortarTurret, FlakTurret, CRAMTurret, SkyShield
from ._sensors import VisualRadarSensor, VisualSensor
from ._base_entities import LogicGameEntity
from ._debug import DebugRenderingEntity, PolyDebugRenderingEntity
from ._turrets import ExactoTurret
from ._world import TextEntity
# from ._static_turret import BaseTurret, SniperTurret, AkTurret, MinigunTurret, \
#     MortarTurret, FlakTurret, CRAMTurret
# from ._sensors import Radar
# from ._text_entity import TextEntity
from ._base_entity import LogicGameEntity
from ._static_sensors import VisualRadarSensor, VisualSensor
from ._bullets import Bullet
from ._text_entity import TextEntity
from ._exacto import ExactoTurret
from ._dynamic_entities import DYNAMIC_ENTITIES


# noinspection PyTypeChecker
SPAWNABLES: dict[str, tp.Type[LogicGameEntity]] = {
    e.cid(): e for e in [
        VisualSensor,
        VisualRadarSensor,
        TextEntity,
        DebugRenderingEntity,
        ExactoTurret,
        Bullet
    ]
}
SPAWNABLES.update(DYNAMIC_ENTITIES)
