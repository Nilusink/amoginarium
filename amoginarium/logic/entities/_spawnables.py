"""
_spawnables.py
15.03.2026

collects every spawn-able entity

Author:
Nilusink
"""
from icecream import ic
import typing as tp

# from ._static_turret import BaseTurret, SniperTurret, AkTurret, MinigunTurret, \
#     MortarTurret, FlakTurret, CRAMTurret
# from ._sensors import Radar
# from ._text_entity import TextEntity
from ._base_entity import LogicGameEntity
from ._static_turrets import MinigunTurret, SniperTurret, AkTurret, MortarTurret
from ._static_turrets import FlakTurret, CRAMTurret
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
        # Radar,
        TextEntity,
        DebugRenderingEntity,
    ]
}
