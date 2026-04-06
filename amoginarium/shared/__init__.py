"""
amoginarium/shared/__init__.py

Project: amoginarium
"""

from ._linked import GlobalVars, Coalitions, generate_global_vars
from ._entity_hints import BaseEntityLike, GameEntityLike, PlayerLike, \
    IslandLike, HasPosition, VisibleGameEntityLike, ItemLike, WeaponLike
from ._data_types import ItemSlot, item_t, ProcessCommand, ProcessCommandType, \
    DummyCIDs, BaseCommandType, IslandCIDs, TurretCIDs, WeaponCIDs, CIDType, \
    CID_REGISTER
from ._logic_entity_hints import BaseLogicEntityLike
from ._entity_counter import ENTITY_COUNTER, INVENTORY_COUNTER
from ._shared_memory import MAX_ENTITIES, base_entity_t, get_entity_memory, \
    get_write_lock, base_controller_t, MAX_CONTROLLERS, get_controller_memory, \
    item_slot_t, inventory_t, MAX_INVENTORY_SLOTS, MAX_INVENTORIES, get_inventory_memory
from ._controlls import Controls
