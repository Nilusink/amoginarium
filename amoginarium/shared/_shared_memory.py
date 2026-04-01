"""
_shared_memory.py
28.03.2026

shared memory objects

Author:
Nilusink
"""
from multiprocessing.shared_memory import SharedMemory
from multiprocessing import shared_memory, Lock
import typing as tp
import ctypes


# region constants
MAX_ENTITIES: int = 10_000
MAX_CONTROLLERS: int = 8
# endregion


# region types
class base_entity_t(ctypes.Structure):  # basic changing attributes
    _pack_ = 1
    _fields_ = [
        ("pos_x", ctypes.c_double),
        ("pos_y", ctypes.c_double),
        ("facing_x", ctypes.c_float),
        ("facing_y", ctypes.c_float),
        ("size_x", ctypes.c_float),
        ("size_y", ctypes.c_float),
        ("alive", ctypes.c_bool),

        # misc parameters for sharing data with base process
        ("param0", ctypes.c_float),
        ("param1", ctypes.c_float),
        ("param2", ctypes.c_float),
        ("param3", ctypes.c_uint64),
        ("param4", ctypes.c_uint64),
    ]


class base_controller_t(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("jump", ctypes.c_bool),
        ("reload", ctypes.c_bool),
        ("shoot", ctypes.c_bool),
        ("inventory", ctypes.c_bool),
        ("drop", ctypes.c_bool),
        ("wpn_f", ctypes.c_bool),
        ("wpn_b", ctypes.c_bool),
        ("joy_btn", ctypes.c_float),
        ("joy_x", ctypes.c_float),
        ("joy_y", ctypes.c_float),
        ("mouse_x", ctypes.c_float),
        ("mouse_y", ctypes.c_float),
    ]
# endregion


# region methods
_e_shm: SharedMemory = ...
def get_entity_memory() -> SharedMemory:
    global _e_shm
    if _e_shm is ...:
        _e_shm = shared_memory.SharedMemory(
            create=True,
            size=ctypes.sizeof(base_entity_t) * MAX_ENTITIES
        )

    return _e_shm


_c_shm: SharedMemory = ...
def get_controller_memory() -> SharedMemory:
    global _c_shm
    if _c_shm is ...:
        _c_shm = shared_memory.SharedMemory(
            create=True,
            size=ctypes.sizeof(base_controller_t) * MAX_CONTROLLERS
        )

    return _c_shm


_lock: tp.Any | None = None
def get_write_lock() -> Lock:
    global _lock
    if _lock is None:
        _lock = Lock()

    return _lock
# endregion


if __name__ == "__main__":
    print(ctypes.sizeof(base_entity_t) * MAX_ENTITIES)
