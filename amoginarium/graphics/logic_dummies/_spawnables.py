"""
_spawnables.py
15.03.2026

collects every spawn-able entity

Author:
Nilusink
"""

from icecream import ic  # noqa: F401
import typing as tp

from amoginarium.shared.param_entities import load_entities_from_files, ProcessType

from ._synced_entities import SyncedGraphicsEntity
from ._player import PlayerDummy
from ._bullet import BulletDummy, Grenade
from ._turrets import BaseTurretDummy, ExactoSniperTurretDummy, RideableTurret
from ._turrets import CalculatedRideableTurretDummy
from ._weapons import HandThrownGrenade, ExactoSniper, WeaponDummy
from ._sensors import SensorHUD, RadarSensorHUD, MagicSensorHUD, VisualSensorHUD
from ._items import Shield, HealingPotion, JetBag
from ._debug_rendering import DebugRectangleEntity, DebugPolygonEntity
from ._debug_rendering import DebugCircleEntity
from ._charged_weapons import RailGunDummy
from ._text_entity import TextEntity
from ._aero import AeroDummy
from ._missiles import (
    MultiStageMissileDummy,
    GuidedMultiStageMissileDummy,
    MultiThrusterMissileDummy,
    PlayerControlledMissileDummy,
)


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
        MultiStageMissileDummy,
        GuidedMultiStageMissileDummy,
        MultiThrusterMissileDummy,
        PlayerControlledMissileDummy,
        RideableTurret,
        CalculatedRideableTurretDummy,
    ]
}

# noinspection PyTypeChecker
GRAPHICS_SPAWNABLES.update(
    load_entities_from_files(ProcessType.base, GRAPHICS_SPAWNABLES)
)
