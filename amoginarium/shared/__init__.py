"""
amoginarium/shared/__init__.py

Project: amoginarium
"""

from ._linked import GlobalVars, Coalitions, generate_global_vars
from ._entity_hints import BaseEntityLike, GameEntityLike, PlayerLike, \
    IslandLike, HasPosition, VisibleGameEntityLike, ItemLike, WeaponLike
from ._data_types import ItemSlot, item_t, ProcessCommand, ProcessCommandType, \
    DummyCIDs, BaseCommandType
from ._logic_entity_hints import BaseLogicEntityLike
from ._entity_counter import ENTITY_COUNTER
from ._shared_memory import MAX_ENTITIES, base_entity_t, get_entity_memory, \
    get_write_lock