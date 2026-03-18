"""
_data_types.py
18.03.2026

Various data types

Author:
Nilusink
"""
from dataclasses import dataclass

from ._entity_hints import VisibleItemLike


type item_t = VisibleItemLike | None  # ItemLike | WeaponLike | None


@dataclass
class ItemSlot:
    item: item_t
    count: int
