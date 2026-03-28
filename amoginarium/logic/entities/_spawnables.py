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


# noinspection PyTypeChecker
SPAWNABLES: dict[str, tp.Type[LogicGameEntity]] = {
    e.cid(): e for e in [
        # SniperTurret,
        # AkTurret,
        # MinigunTurret,
        # MortarTurret,
        # FlakTurret,
        # CRAMTurret,
        # Radar,
        # TextEntity,
    ]
}
