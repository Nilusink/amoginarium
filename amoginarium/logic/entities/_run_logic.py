"""
_run_logic.py
28.03.2026

runs the logic process

Author:
Nilusink
"""
from multiprocessing.shared_memory import SharedMemory
from multiprocessing import Queue, Lock, Event
from time import perf_counter

import numpy as np
import ctypes

from .._sharing import base_entity_t, MAX_ENTITIES
from ._logic_groups import *


class LogicProcess:
    def __init__(
            self,
            shm: SharedMemory,
            command_queue: Queue,
            write_lock: Lock
    ):
        self._write_lock = write_lock
        self._cq = command_queue

        local_buffer = bytearray(ctypes.sizeof(base_entity_t) * MAX_ENTITIES)

        self.__entity_buffer = (base_entity_t * MAX_ENTITIES).from_buffer(shm.buf)
        self._runtime_buffer = (base_entity_t * MAX_ENTITIES).from_buffer(local_buffer)

        # copy once to make sure starting value is the same
        self._runtime_buffer[:] = self.__entity_buffer

    @staticmethod
    def update_entities(delta: float) -> None:
        """
        update all entities
        """
        for entity in Updated.sprites():
            entity.update(delta)

    def update_memory(self) -> None:
        """
        copy runtime buffer to memory buffer
        """
        self._write_lock.acquire()
        self.__entity_buffer[:] = self._runtime_buffer
        self._write_lock.release()


def run_continuous(
        shm: SharedMemory,
        command_queue: Queue,
        write_lock: Lock,
        quit_event: Event
) -> None:
    """
    run the logic process continuously
    """
    lp = LogicProcess(shm, command_queue, write_lock)

    last_run = perf_counter()
    while not quit_event.is_set():
        now = perf_counter()
        delta = last_run - now

        # check for commands

        # update entities
        lp.update_entities(delta)

        # copy buffer
        lp.update_memory()

        last_run = now
