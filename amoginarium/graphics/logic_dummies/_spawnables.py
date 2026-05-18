"""
Collects every spawn-able entity.

Path: amoginarium/graphics/logic_dummies/_spawnables.py
Project: amoginarium
Created: 28.03.2026
Authors: Nilusink, LukasKrah
"""

import typing as tp

from icecream import ic  # noqa: F401

from amoginarium.shared.param_entities import load_entities_from_files, ProcessType

from ._aero import AeroDummy
from ._bullet import BulletDummy, Grenade
from ._charged_weapons import RailGunDummy
from ._debug_rendering import DebugCircleEntity, DebugPolygonEntity
from ._debug_rendering import DebugRectangleEntity
from ._items import HealingPotion, JetBag, Shield
from ._missiles import GuidedMultiStageMissileDummy, MultiStageMissileDummy
from ._missiles import MultiThrusterMissileDummy, PlayerControlledMissileDummy
from ._player import PlayerDummy
from ._sensors import MagicSensorHUD, RadarSensorHUD, SensorHUD, VisualSensorHUD
from ._synced_entities import SyncedGraphicsEntity
from ._text_entity import TextEntity
from ._turrets import BaseTurretDummy, CalculatedRideableTurretDummy
from ._turrets import ExactoSniperTurretDummy, RideableTurret
from ._weapons import ExactoSniper, HandThrownGrenade, WeaponDummy

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
