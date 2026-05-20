"""
Exposes shared data types, memory structures, and entity protocols.

Path: amoginarium/shared/__init__.py
Project: amoginarium
Created: 01.03.2026
Authors: Nilusink, LukasKrah
"""

from ._controlls import Controls
from ._data_types import BaseCommandType, CID_REGISTER, CIDType, CurrentView, DummyCIDs
from ._data_types import GraphicsCIDs, IslandCIDs, item_t, ItemCIDs, ItemSlot
from ._data_types import MissileCIDs, ProcessCommand, ProcessCommandType, SensorCIDs
from ._data_types import TurretCIDs, WeaponCIDs, WeaponSensorCIDs
from ._debug_vars import DebugVarsEnum
from ._entity_counter import ENTITY_COUNTER, INVENTORY_COUNTER
from ._entity_hints import BaseEntityLike, DynamicEntityParentViable
from ._entity_hints import GameEntityLike, HasFacing, HasPosition, IslandLike
from ._entity_hints import ItemLike, PlayerLike, VisibleGameEntityLike, WeaponLike
from ._linked import Coalitions, generate_global_vars, GlobalVars
from ._logic_entity_hints import BaseLogicEntityLike, CollisionLogicEntityLike
from ._logic_entity_hints import EntityChildViable, LogicGameEntityLike
from ._logic_entity_hints import MurderViable, PositionedLogicEntityLike
from ._shared_memory import base_controller_t, base_entity_t, get_controller_memory
from ._shared_memory import get_entity_memory, get_inventory_memory, get_write_lock
from ._shared_memory import inventory_t, item_slot_t, MAX_CONTROLLERS, MAX_ENTITIES
from ._shared_memory import MAX_INVENTORIES, MAX_INVENTORY_SLOTS
