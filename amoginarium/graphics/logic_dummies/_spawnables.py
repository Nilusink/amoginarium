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
from ._bullet import BulletDummy, MortarShell, Grenade, CRAMBullet
from ._turrets import SniperTurretDummy, AkTurretDummy, MinigunTurretDummy
from ._turrets import MortarTurretDummy, FlakTurretDummy, CRAMTurretDummy
from ._turrets import SkyShieldDummy
from ._weapons import Minigun, Ak47, Sniper, Mortar, Flak, CRAM, HandThrownGrenade
from ._weapons import SkyShieldGun
from ._sensors import SensorHUD
from ._items import Shield, HealingPotion, JetBag
from ._debug_rendering import DebugRenderingEntity, PolyDebugRenderingEntity
from ._charged_weapons import RailGunDummy
from ._text_entity import TextEntity

GRAPHICS_SPAWNABLES: dict[str, tp.Type[SyncedGraphicsEntity]] = {
    e.cid(): e
    for e in [
        PlayerDummy,
        BulletDummy,
        MortarShell,
        Grenade,
        SniperTurretDummy,
        AkTurretDummy,
        MinigunTurretDummy,
        MortarTurretDummy,
        FlakTurretDummy,
        CRAMTurretDummy,
        Minigun,
        Ak47,
        Sniper,
        Mortar,
        Flak,
        CRAM,
        HandThrownGrenade,
        CRAMBullet,
        Shield,
        HealingPotion,
        JetBag,
        RailGunDummy,
        SkyShieldDummy,
        SkyShieldGun,
        SensorHUD,
        TextEntity,
        DebugRenderingEntity,
        PolyDebugRenderingEntity
    ]
}
