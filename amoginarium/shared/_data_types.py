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


class CommandType(Enum):
    # process control
    quit = 0
    reset = 1
    pause = 2
    unpause = 3

    # logic control
    load_map = 4

    # sound stuff
    play_sound = 5


@dataclass
class ProcessCommand:
    type: CommandType
    args: tp.Iterable = field(default_factory=list)
    kwargs: dict[str, tp.Any] = field(default_factory=dict)
