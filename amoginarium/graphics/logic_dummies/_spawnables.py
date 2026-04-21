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
from ._bullet import BulletDummy, MortarShell, Grenade
from ._turrets import SniperTurretDummy, AkTurretDummy, MinigunTurretDummy
from ._turrets import MortarTurretDummy, FlakTurretDummy, BaseTurretDummy
from ._turrets import SkyShieldDummy, ExactoSniperTurretDummy
from ._weapons import Minigun, Ak47, Mortar, Flak, CRAM, HandThrownGrenade
from ._weapons import SkyShieldGun, ExactoSniper, WeaponDummy
from ._sensors import SensorHUD, RadarSensorHUD, MagicSensorHUD, VisualSensorHUD
from ._items import Shield, HealingPotion, JetBag
from ._charged_weapons import RailGunDummy
from ._text_entity import TextEntity
from ._aero import AeroDummy


GRAPHICS_SPAWNABLES: dict[str, tp.Type[SyncedGraphicsEntity]] = {
    e.cid(): e
    for e in [
        WeaponDummy,
        PlayerDummy,
        BulletDummy,
        MortarShell,
        Grenade,
        BaseTurretDummy,
        SniperTurretDummy,
        AkTurretDummy,
        MinigunTurretDummy,
        MortarTurretDummy,
        FlakTurretDummy,
        Minigun,
        Ak47,
        Mortar,
        Flak,
        CRAM,
        HandThrownGrenade,
        Shield,
        HealingPotion,
        JetBag,
        RailGunDummy,
        SkyShieldDummy,
        SkyShieldGun,
        SensorHUD,
        TextEntity,
        AeroDummy,
        ExactoSniper,
        ExactoSniperTurretDummy,
        RadarSensorHUD,
        MagicSensorHUD,
        VisualSensorHUD,
    ]
}


# noinspection PyTypeChecker
GRAPHICS_SPAWNABLES.update(
    load_entities_from_files(ProcessType.base, GRAPHICS_SPAWNABLES)
)
