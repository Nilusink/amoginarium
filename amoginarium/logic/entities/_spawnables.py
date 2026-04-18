"""
_spawnables.py
15.03.2026

collects every spawn-able entity

Author:
Nilusink
"""
import typing as tp

# from ._static_turret import BaseTurret, SniperTurret, AkTurret, MinigunTurret, \
#     MortarTurret, FlakTurret, CRAMTurret
# from ._sensors import Radar
# from ._text_entity import TextEntity
from logic.entities._base._base_logic_entity import LogicGameEntity
from ._static_turrets import MinigunTurret, SniperTurret, AkTurret, MortarTurret
from ._static_turrets import FlakTurret, CRAMTurret, SkyShield
from ._static_sensors import VisualRadarSensor, VisualSensor
from ._text_entity import TextEntity
from ._debug_rendering import DebugRenderingEntity

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
