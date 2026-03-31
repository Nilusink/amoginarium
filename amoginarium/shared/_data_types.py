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

from ._entity_hints import VisibleItemLike


type item_t = VisibleItemLike | None  # ItemLike | WeaponLike | None


@dataclass
class ItemSlot:
    item: item_t
    count: int
    parent: tp.Any
    id: int


class DummyCIDs(Enum):
    player = "dummy.player"
    base_bullet = "dummy.bullet.base"  # {"spawn_time": float, "visibility_offset": float}
    mortar_bullet = "dummy.bullet.mortar"  # -- "" --
    grenade = "dummy.bullet.grenade"  # -- "" --


class IslandCIDs(Enum):
    grass_island = "island.grass"
    gray_brick_island = "island.brick.gray"
    green_brick_island = "island.brick.green"


class ProcessCommandType(Enum):
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
    spawn_dummy = 0  # {"id": <sync id>, "cid": DummyCIDs, **kwargs}
    spawn_island = 1  # {"id": <sync id>, "cid": IslandCIDs, "size" OR "form"}


@dataclass
class ProcessCommand:
    type: ProcessCommandType | BaseCommandType
    args: tp.Iterable = field(default_factory=list)
    kwargs: dict[str, tp.Any] = field(default_factory=dict)
