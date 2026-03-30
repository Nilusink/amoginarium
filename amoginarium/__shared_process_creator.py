"""
__shared_process_creator.py
29.03.2026

creates all data used for process sharing.

Author:
Nilusink
"""
from multiprocessing.shared_memory import SharedMemory
from multiprocessing.connection import Connection
from multiprocessing import Queue, Lock, Pipe
from ctypes import Array, memset, sizeof, addressof
from icecream import ic

from .shared import generate_global_vars, get_write_lock, get_entity_memory
from .shared import GlobalVars, base_entity_t, MAX_ENTITIES
from .shared.debugging import run_with_debug


class _ProcessValues:
    global_vars: GlobalVars = ...
    SHM: SharedMemory = ...
    WRITE_LOCK: Lock = ...
    COQ: Queue = ...
    CIQ: Queue = ...
    BASE_COMM: Connection = ...
    PROCESS_COMM: Connection = ...

    E_BUFF: Array[base_entity_t] = ...

    def create_shared_process_values(self) -> None:
        if self.global_vars is not ...:
            raise RuntimeError("create_shared_process_values called twice!")

        self.global_vars = GlobalVars(generate_global_vars())
        self.SHM = get_entity_memory()
        self.E_BUFF = (base_entity_t * MAX_ENTITIES).from_buffer(self.SHM.buf)

        # initialize shared memory to all 0s
        memset(
            addressof(self.E_BUFF),
            0,
            sizeof(self.E_BUFF)
        )

        self.WRITE_LOCK = get_write_lock()
        self.CIQ = Queue()
        self.COQ = Queue()
        self.BASE_COMM, self.PROCESS_COMM = Pipe()

    @run_with_debug(show_args=True)
    def set_shared_process_values(
            self,
            g_vars: GlobalVars,
            command_in_queue: Queue,
            command_out_queue: Queue,
            shared_memory: SharedMemory,
            write_lock: Lock,
            base_comm: Connection,
            process_comm: Connection
    ) -> None:
        if self.global_vars is not ...:
            raise RuntimeError("set_shared_process_values called twice!")

        ic(shared_memory)

        self.global_vars = g_vars
        self.SHM = shared_memory
        self.E_BUFF = (base_entity_t * MAX_ENTITIES).from_buffer(self.SHM.buf)
        self.WRITE_LOCK = write_lock
        self.COQ = command_out_queue
        self.CIQ = command_in_queue
        self.BASE_COMM = base_comm
        self.PROCESS_COMM = process_comm


pv = _ProcessValues()
