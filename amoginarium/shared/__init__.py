"""
Exposes shared data types, memory structures, and entity protocols.

Path: amoginarium/shared/__init__.py
Project: amoginarium
Created: 01.03.2026
Authors: Nilusink, LukasKrah
"""

from ._controlls import Controls
from ._data_types import (
    CID_REGISTER,
    BaseCommandType,
    CIDType,
    CurrentView,
    DummyCIDs,
    GraphicsCIDs,
    IslandCIDs,
    ItemCIDs,
    ItemSlot,
    MissileCIDs,
    ProcessCommand,
    ProcessCommandType,
    SensorCIDs,
    TurretCIDs,
    VehicleCIDs,
    WeaponCIDs,
    WeaponSensorCIDs,
    item_t,
)
from ._entity_counter import ENTITY_COUNTER, INVENTORY_COUNTER
from ._entity_hints import (
    BaseEntityLike,
    DynamicEntityParentViable,
    GameEntityLike,
    HasFacing,
    HasPosition,
    IslandLike,
    ItemLike,
    PlayerLike,
    VisibleGameEntityLike,
    WeaponLike,
)
from ._linked import Coalitions, GlobalVars, generate_global_vars
from ._logic_entity_hints import (
    BaseLogicEntityLike,
    CollisionLogicEntityLike,
    LogicGameEntityLike,
    PositionedLogicEntityLike,
)
from ._shared_memory import (
    MAX_CONTROLLERS,
    MAX_ENTITIES,
    MAX_INVENTORIES,
    MAX_INVENTORY_SLOTS,
    base_controller_t,
    base_entity_t,
    get_controller_memory,
    get_entity_memory,
    get_inventory_memory,
    get_write_lock,
    inventory_t,
    item_slot_t,
)
