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

from .shared import generate_global_vars, get_write_lock, get_entity_memory
from .shared.debugging import run_with_debug
from .shared import GlobalVars


class _ProcessValues:
    global_vars: GlobalVars = ...
    SHM: SharedMemory = ...
    WRITE_LOCK: Lock = ...
    COQ: Queue = ...
    CIQ: Queue = ...
    BASE_COMM: Connection = ...
    PROCESS_COMM: Connection = ...

    def create_shared_process_values(self) -> None:
        if self.global_vars is not ...:
            raise RuntimeError("create_shared_process_values called twice!")

        self.global_vars = GlobalVars(generate_global_vars())
        self.SHM = get_entity_memory()
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
            write_lock: Lock,
            base_comm: Connection,
            process_comm: Connection
    ) -> None:
        if self.global_vars is not ...:
            raise RuntimeError("set_shared_process_values called twice!")

        self.global_vars = g_vars
        self.SHM = shared_memory
        self.WRITE_LOCK = write_lock
        self.COQ = command_out_queue
        self.CIQ = command_in_queue
        self.BASE_COMM = base_comm
        self.PROCESS_COMM = process_comm


pv = _ProcessValues()
