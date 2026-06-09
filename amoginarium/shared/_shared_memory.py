"""
Shared memory objects.

| ``Path``: amoginarium/shared/_shared_memory.py
| ``Project``: amoginarium
| ``Created``: 28.03.2026
| ``Authors``: Nilusink
"""
# ruff: noqa: T201

from __future__ import annotations

import ctypes
import typing as tp
from multiprocessing import Lock, shared_memory
from types import EllipsisType

from icecream import ic

if tp.TYPE_CHECKING:
    from multiprocessing.shared_memory import SharedMemory

# region constants
MAX_ENTITIES: int = 32_000
MAX_CONTROLLERS: int = 8
MAX_INVENTORIES: int = 64
MAX_INVENTORY_SLOTS: int = 64
DEBUGGING_MAX_MEMORY: int = MAX_ENTITIES * 512  # ca. 512 bytes per entity (NOT EQUAL)
# endregion


# region types
# ruff: disable[ERA001]
class base_entity_t(ctypes.Structure):  # basic changing attributes  # noqa: N801
    _pack_ = 1
    _fields_ = [
        ("pos_x", ctypes.c_double),
        ("pos_y", ctypes.c_double),
        ("facing", ctypes.c_uint16),  # angle (r*10_000)
        ("size_x", ctypes.c_uint16),
        ("size_y", ctypes.c_uint16),
        ("flags", ctypes.c_uint16),  # (
        # 0=alive, 1=visible, 2=highlight,
        # 14=(active (item), active(rideable Turret))
        # 15=(in inventory (player), has parent (item))
        # )
        # misc parameters for sharing data with base process
        ("param0", ctypes.c_float),
        ("param1", ctypes.c_float),
        ("param2", ctypes.c_float),
        ("param3", ctypes.c_uint64),
        ("param4", ctypes.c_uint64),
    ]


# ruff: enable[ERA001]


class base_controller_t(ctypes.Structure):  # noqa: N801
    _pack_ = 1
    _fields_ = [
        ("jump", ctypes.c_bool),
        ("reload", ctypes.c_bool),
        ("shoot", ctypes.c_bool),
        ("inventory", ctypes.c_bool),
        ("drop", ctypes.c_bool),
        ("wpn_f", ctypes.c_bool),
        ("wpn_b", ctypes.c_bool),
        ("ride", ctypes.c_bool),
        ("m_right", ctypes.c_bool),
        ("joy_btn", ctypes.c_float),
        ("joy_x", ctypes.c_float),
        ("joy_y", ctypes.c_float),
        ("mouse_x", ctypes.c_float),
        ("mouse_y", ctypes.c_float),
    ]


class item_slot_t(ctypes.Structure):  # noqa: N801
    _pack_ = 1
    _fields_ = [("item_id", ctypes.c_uint16), ("count", ctypes.c_uint8)]


class inventory_t(ctypes.Structure):  # noqa: N801
    _pack_ = 1
    _fields_ = [
        ("flags", ctypes.c_uint8),  # (0=alive, 1=visible, )
        ("size", ctypes.c_uint8),
        ("hover", ctypes.c_uint8),
        ("selected", ctypes.c_uint8),
        ("slots", item_slot_t * MAX_INVENTORY_SLOTS),
    ]


# endregion


# region methods
_e_shm: SharedMemory | EllipsisType = ...


def get_entity_memory() -> SharedMemory:
    global _e_shm  # noqa: PLW0603
    if isinstance(_e_shm, EllipsisType):
        _e_shm = shared_memory.SharedMemory(
            create=True,
            size=ctypes.sizeof(base_entity_t) * MAX_ENTITIES,
            name="ENTITY",
        )

    return _e_shm  # type: ignore[u-fucking-serious?]


_c_shm: SharedMemory | EllipsisType = ...


def get_controller_memory() -> SharedMemory:
    global _c_shm  # noqa: PLW0603
    if isinstance(_c_shm, EllipsisType):
        _c_shm = shared_memory.SharedMemory(
            create=True,
            size=ctypes.sizeof(base_controller_t) * MAX_CONTROLLERS,
            name="CONTROLLER",
        )

    return _c_shm  # type: ignore[u-fucking-serious?]


_i_shm: SharedMemory | EllipsisType = ...


def get_inventory_memory() -> SharedMemory:
    global _i_shm  # noqa: PLW0603
    if isinstance(_i_shm, EllipsisType):
        _i_shm = shared_memory.SharedMemory(
            create=True,
            size=ctypes.sizeof(inventory_t) * MAX_INVENTORY_SLOTS,
            name="INVENTORY",
        )

    return _i_shm  # type: ignore[u-fucking-serious?]


_d_shm: SharedMemory | EllipsisType = ...


def get_debugging_memory() -> SharedMemory:
    global _d_shm  # noqa: PLW0603
    if isinstance(_d_shm, EllipsisType):
        _d_shm = shared_memory.SharedMemory(
            create=True,
            size=DEBUGGING_MAX_MEMORY,
            name="DEBUGGING",
        )

    return _d_shm  # type: ignore[u-fucking-serious?]


_lock: tp.Any | None = None


def get_write_lock() -> Lock:
    global _lock  # noqa: PLW0603
    if _lock is None:
        _lock = Lock()

    return _lock


# endregion


if __name__ == "__main__":
    print(ctypes.sizeof(base_entity_t) * MAX_ENTITIES)
