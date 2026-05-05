"""
_spawnables.py
15.03.2026

collects every spawn-able entity

Author:
Nilusink
"""
from icecream import ic
import typing as tp

from amoginarium.shared.param_entities import load_entities_from_files, ProcessType

from ._synced_entities import SyncedGraphicsEntity
from ._player import PlayerDummy
from ._bullet import BulletDummy, Grenade
from ._turrets import BaseTurretDummy, ExactoSniperTurretDummy
from ._weapons import HandThrownGrenade, ExactoSniper, WeaponDummy
from ._sensors import SensorHUD, RadarSensorHUD, MagicSensorHUD, VisualSensorHUD
from ._items import Shield, HealingPotion, JetBag
from ._debug_rendering import DebugRectangleEntity, DebugPolygonEntity, DebugCircleEntity
from ._charged_weapons import RailGunDummy
from ._text_entity import TextEntity
from ._aero import AeroDummy
from ._missiles import MultiStageMissileDummy


GRAPHICS_SPAWNABLES: dict[str, tp.Type[SyncedGraphicsEntity]] = {
    e.cid(): e
    for e in [
        WeaponDummy,
        PlayerDummy,
        BulletDummy,
        Grenade,
        BaseTurretDummy,
        HandThrownGrenade,
        Shield,
        HealingPotion,
        JetBag,
        RailGunDummy,
        SensorHUD,
        TextEntity,
        AeroDummy,
        ExactoSniper,
        ExactoSniperTurretDummy,
        DebugRectangleEntity,
        DebugPolygonEntity,
        DebugCircleEntity,
        RadarSensorHUD,
        MagicSensorHUD,
        VisualSensorHUD,
        MultiStageMissileDummy
    ]
}

# noinspection PyTypeChecker
GRAPHICS_SPAWNABLES.update(
    load_entities_from_files(ProcessType.base, GRAPHICS_SPAWNABLES)
)
