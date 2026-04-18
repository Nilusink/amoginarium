"""
_spawnables.py
15.03.2026

collects every spawn-able entity

Author:
Nilusink
"""

import typing as tp

from ._turrets import MinigunTurret, SniperTurret, AkTurret, MortarTurret, FlakTurret, CRAMTurret, SkyShield
from ._sensors import VisualRadarSensor, VisualSensor
from ._base_entities import LogicGameEntity
from ._debug import DebugRenderingEntity
from ._world import TextEntity

# noinspection PyTypeChecker
SPAWNABLES: dict[str, tp.Type[LogicGameEntity]] = {
    e.cid().value: e for e in [
        MinigunTurret,
        SniperTurret,
        AkTurret,
        MortarTurret,
        FlakTurret,
        CRAMTurret,
        SkyShield,
        VisualSensor,
        VisualRadarSensor,
        TextEntity,
        DebugRenderingEntity,
    ]
}
