"""
_data_types.py
18.03.2026

Various data types

Author:
Nilusink
"""
from dataclasses import dataclass
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
    reset = 0


@dataclass
class ProcessCommand:
    type: CommandType
    args: tp.Iterable
    kwargs: dict[str, tp.Any]
