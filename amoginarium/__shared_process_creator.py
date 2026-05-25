"""
Creates all data used for process sharing.

| ``Path``: amoginarium/__shared_process_creator.py
| ``Project``: amoginarium
| ``Created``: 29.03.2026
| ``Authors``: Nilusink
"""

from __future__ import annotations

from ctypes import addressof, memset, sizeof
from multiprocessing import Pipe, Queue
from queue import Empty
from typing import TYPE_CHECKING

from icecream import ic

from .shared import base_controller_t, base_entity_t, generate_global_vars
from .shared import get_controller_memory, get_debugging_memory, get_entity_memory
from .shared import get_inventory_memory, get_write_lock, GlobalVars, inventory_t
from .shared import MAX_CONTROLLERS, MAX_ENTITIES, MAX_INVENTORIES
from .shared.debugging import SharedHeap
from .shared.utility import Vec2

if TYPE_CHECKING:
    from ctypes import Array
    from multiprocessing import Lock
    from multiprocessing.connection import Connection
    from multiprocessing.shared_memory import SharedMemory


class _ProcessValues:
    global_vars: GlobalVars = ...
    SH: SharedHeap = ...
    SHM: SharedMemory = ...  # entity memory
    C_SHM: SharedMemory = ...  # controller memory
    I_SHM: SharedMemory = ...  # inventory memory
    D_SHM: SharedMemory = ...  # debugging memory
    WRITE_LOCK: Lock = ...
    COQ: Queue = ...
    CIQ: Queue = ...
    BASE_COMM: Connection = ...
    PROCESS_COMM: Connection = ...

    E_BUFF: Array[base_entity_t] = ...
    C_BUFF: Array[base_controller_t] = ...
    I_BUFF: Array[inventory_t] = ...

    audio_observer_pos: Vec2 = Vec2()

    def create_shared_process_values(self) -> None:
        if self.global_vars is not ...:
            msg = "create_shared_process_values called twice!"
            raise RuntimeError(msg)

        self.global_vars = GlobalVars(generate_global_vars())
        self.SHM = get_entity_memory()
        self.C_SHM = get_controller_memory()
        self.I_SHM = get_inventory_memory()
        self.E_BUFF = (base_entity_t * MAX_ENTITIES).from_buffer(self.SHM.buf)
        self.C_BUFF = (base_controller_t * MAX_CONTROLLERS).from_buffer(self.C_SHM.buf)
        self.I_BUFF = (inventory_t * MAX_INVENTORIES).from_buffer(self.I_SHM.buf)

        self.D_SHM = get_debugging_memory()
        self.SH = SharedHeap(self.D_SHM.name)

        # initialize shared memories to all 0s
        memset(addressof(self.E_BUFF), 0, sizeof(self.E_BUFF))
        memset(addressof(self.C_BUFF), 0, sizeof(self.C_BUFF))
        memset(addressof(self.I_BUFF), 0, sizeof(self.I_BUFF))

        self.WRITE_LOCK = get_write_lock()
        self.CIQ = Queue()
        self.COQ = Queue()
        self.BASE_COMM, self.PROCESS_COMM = Pipe()

    def set_shared_process_values(
        self,
        g_vars: GlobalVars,
        command_in_queue: Queue,
        command_out_queue: Queue,
        shared_memory: SharedMemory,
        controller_memory: SharedMemory,
        inventory_memory: SharedMemory,
        debugging_memory: SharedMemory,
        write_lock: Lock,
        base_comm: Connection,
        process_comm: Connection,
    ) -> None:
        if self.global_vars is not ...:
            msg = "set_shared_process_values called twice!"
            raise RuntimeError(msg)

        ic(shared_memory)

        self.global_vars = g_vars

        self.SHM = shared_memory
        self.C_SHM = controller_memory
        self.I_SHM = inventory_memory
        self.E_BUFF = (base_entity_t * MAX_ENTITIES).from_buffer(self.SHM.buf)
        self.C_BUFF = (base_controller_t * MAX_CONTROLLERS).from_buffer(self.C_SHM.buf)
        self.I_BUFF = (inventory_t * MAX_INVENTORIES).from_buffer(self.I_SHM.buf)

        self.D_SHM = debugging_memory
        self.SH = SharedHeap(self.D_SHM.name)

        self.WRITE_LOCK = write_lock
        self.COQ = command_out_queue
        self.CIQ = command_in_queue
        self.BASE_COMM = base_comm
        self.PROCESS_COMM = process_comm

    def reset(self) -> None:
        """Reset everything."""
        # initialize shared memories to all 0s
        memset(addressof(self.E_BUFF), 0, sizeof(self.E_BUFF))
        memset(addressof(self.C_BUFF), 0, sizeof(self.C_BUFF))
        memset(addressof(self.I_BUFF), 0, sizeof(self.I_BUFF))

        # reset globalvars
        self.global_vars.reset()
        self.global_vars.update()

        # reset comms
        while self.BASE_COMM.poll(0):
            self.BASE_COMM.recv()
        while self.PROCESS_COMM.poll(0):
            self.PROCESS_COMM.recv()

        # reset command queues
        while True:
            try:
                self.COQ.get_nowait()

            except Empty:
                break

        while True:
            try:
                self.CIQ.get_nowait()

            except Empty:
                break


pv = _ProcessValues()
