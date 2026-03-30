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
# endregion


# region types
class base_entity_t(ctypes.Structure):  # basic changing attributes
    _pack_ = 1
    _fields_ = [
        ("pos_x", ctypes.c_double),
        ("pos_y", ctypes.c_double),
        ("facing_x", ctypes.c_double),
        ("facing_y", ctypes.c_double),
        ("size_x", ctypes.c_double),
        ("size_y", ctypes.c_double),
        ("alive", ctypes.c_bool),

        # misc parameters for sharing data with base process
        ("param0", ctypes.c_float),
        ("param1", ctypes.c_float),
        ("param2", ctypes.c_float),
        ("param3", ctypes.c_float),
    ]
# endregion


# region methods
_shm: SharedMemory = ...
def get_entity_memory() -> SharedMemory:
    global _shm
    if _shm is ...:
        _shm = shared_memory.SharedMemory(
            create=True,
            size=ctypes.sizeof(base_entity_t) * MAX_ENTITIES
        )

    return _shm

_lock: tp.Any | None = None
def get_write_lock() -> Lock:
    global _lock
    if _lock is None:
        _lock = Lock()

    return _lock
# endregion


if __name__ == "__main__":
    print(ctypes.sizeof(base_entity_t))
