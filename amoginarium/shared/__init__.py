"""
amoginarium/shared/__init__.py

Project: amoginarium
"""

from ._shared_memory import (base_controller_t, base_entity_t, get_controller_memory, get_entity_memory,
                             get_inventory_memory, get_write_lock, inventory_t, item_slot_t, MAX_CONTROLLERS,
                             MAX_ENTITIES, MAX_INVENTORIES, MAX_INVENTORY_SLOTS)
from ._data_types import (BaseCommandType, CID_REGISTER, CIDType, DummyCIDs, GraphicsCIDs, IslandCIDs, item_t, ItemCIDs,
                          ItemSlot, ProcessCommand, ProcessCommandType, SensorCIDs, TurretCIDs, WeaponCIDs)
from ._entity_hints import (BaseEntityLike, GameEntityLike, HasPosition, IslandLike, ItemLike, PlayerLike,
                            VisibleGameEntityLike, WeaponLike)
from ._logic_entity_hints import (BaseLogicEntityLike, CollisionLogicEntityLike, LogicGameEntityLike,
                                  PositionedLogicEntityLike)
from ._linked import Coalitions, generate_global_vars, GlobalVars
from ._entity_counter import ENTITY_COUNTER, INVENTORY_COUNTER
from ._controlls import Controls
