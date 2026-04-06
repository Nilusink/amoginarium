"""
_drawable_items.py
06.04.2026

implements items that can be drawn

Author:
Nilusink
"""
from amoginarium.shared import CID_REGISTER

from ._weapons import Minigun, Ak47, Sniper, HandThrownGrenade, WeaponDummy


__items = [Minigun, Ak47, Sniper, HandThrownGrenade]
ITEM_IDS: dict[int, WeaponDummy] = {
    CID_REGISTER.get_id(i.cid()): i for i in __items
}
