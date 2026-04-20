"""
_data_types.py
18.03.2026

Various data types

Author:
Nilusink
"""

from dataclasses import dataclass, field
from enum import Enum
import typing as tp

from ._entity_hints import ItemLike


type item_t = ItemLike | None  # ItemLike | WeaponLike | None


@dataclass
class ItemSlot:
    """
    A slot in a players inventory
    """
    item: item_t
    count: int
    parent: tp.Any
    id: int


class DummyCIDs(Enum):
    """
    Component IDs for Graphics dummies
    """
    player = "dummy.player"
    base_bullet = "dummy.bullet.base"  # {"spawn_time": float, "visibility_offset": float}
    mortar_bullet = "dummy.bullet.mortar"  # -- "" --
    grenade = "dummy.bullet.grenade"  # -- "" --
    cram = "dummy.bullet.cram"
    aero = "dummy.bullet.aero"


class IslandCIDs(Enum):
    """
    Component IDs for Graphics islands
    """
    grass_island = "island.grass"
    gray_brick_island = "island.brick.gray"
    green_brick_island = "island.brick.green"


class TurretCIDs(Enum):
    """
    Component IDs for Graphics turrets
    """
    minigun = "turret.static.minigun"
    sniper = "turret.static.sniper"
    ak47 = "turret.static.ak47"
    mortar = "turret.static.mortar"
    flak = "turret.static.flak"
    cram = "turret.static.cram"
    base = "turret.static.base"
    sky_shield = "turret.static.sky_shield"
    exacto_sniper = "turret.static.exacto_sniper"


class WeaponCIDs(Enum):
    """
    Component IDs for Graphics weapons
    """
    minigun = "weapon.minigun"
    sniper = "weapon.sniper"
    ak47 = "weapon.ak47"
    mortar = "weapon.mortar"
    flak = "weapon.flak"
    cram = "weapon.cram"
    h_grenade = "weapon.grenade.hand"
    base = "weapon.base"
    railgun = "weapon.railgun"
    sky_shield = "weapon.sky_shield"
    exacto_sniper = "weapon.exacto_sniper"


class SensorCIDs(Enum):
    """Component IDs for graphics sensors"""
    radar = "sensor.static.radar"
    visual = "sensor.static.visual"
    magic = "sensor.static.magic"
    hud = "sensor.static.hud"


class ItemCIDs(Enum):
    """Component IDs for items"""
    shield = "item.shield"
    healing_potion = "item.healing_potion"
    jetbag = "item.jetbag"


class GraphicsCIDs(Enum):
    """
    Component IDs for other Graphics
    """
    static_text = "static.text"


class _CIDRegister:
    """represent all item CIDs as ints"""

    __slots__ = ["_cids"]
    
    def __init__(self, *enums: tp.Iterable[Enum]) -> None:
        self._cids: dict[str, int] = {}

        i = 1  # start with 1 because 0 is no item
        for enum in enums:
            for name in getattr(enum, "_value2member_map_").keys():
                self._cids[name] = i
                i += 1

    def get_id(self, cid: str | tp.Any) -> int:
        """
        get the corresponding ID from n CID

        :param cid: original CID
        :returns: corresponding ID, 0 if not found
        """
        if not isinstance(cid, str):
            cid: str = cid.value

        if cid in self._cids:
            return self._cids[cid]

        return 0


CID_REGISTER = _CIDRegister(WeaponCIDs)  #, TurretCIDs, IslandCIDs, DummyCIDs)
type CIDType = DummyCIDs | WeaponCIDs | TurretCIDs | IslandCIDs | GraphicsCIDs


class ProcessCommandType(Enum):
    """
    Commands sent from base to process
    """
    # process control
    quit = 0
    reset = 1
    pause = 2
    unpause = 3

    # logic control
    load_map = 4  # {"map_path": <path to map file>}

    # sound stuff
    play_sound = 5  # {"loops": int, "maxtime": float, "fade_ms": float, "sound_name": <name of sound>}

    # entity spawning
    spawn_player = 6  # {"controller_id": int}


class BaseCommandType(Enum):
    """
    commands sent from process to base
    """
    spawn_dummy = 0  # {"id": <sync id>, "cid": DummyCIDs, **kwargs}
    spawn_island = 1  # {"id": <sync id>, "cid": IslandCIDs, "size" OR "form"}
    confirm_reset = 2


@dataclass
class ProcessCommand:
    """
    Base command type (all commands)
    """
    type: ProcessCommandType | BaseCommandType
    args: tp.Iterable = field(default_factory=list)
    kwargs: dict[str, tp.Any] = field(default_factory=dict)
