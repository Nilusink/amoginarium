"""
_spawnables.py
15.03.2026

collects every spawn-able entity

Author:
Nilusink
"""
from icecream import ic
import typing as tp

from ._synced_entities import SyncedGraphicsEntity
from ._player import PlayerDummy
from ._bullet import BulletDummy, MortarShell, Grenade

# noinspection PyTypeChecker
GRAPHICS_SPAWNABLES: dict[str, tp.Type[SyncedGraphicsEntity]] = {
    e.cid(): e for e in [
        PlayerDummy,
        BulletDummy,
        MortarShell,
        Grenade,
        # MortarTurret,
        # FlakTurret,
        # CRAMTurret,
        # Radar,
        # TextEntity,
    ]
}
