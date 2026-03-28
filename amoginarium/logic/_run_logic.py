"""
_run_logic.py
28.03.2026

runs the logic process

Author:
Nilusink
"""
from multiprocessing.shared_memory import SharedMemory
from multiprocessing import Queue, Lock, Value
from time import perf_counter
from icecream import ic
from queue import Empty
import ctypes
import os

from ..shared import base_entity_t, MAX_ENTITIES, GlobalVars, ProcessCommand, \
    CommandType
from .radar import DETECTION_GROUP_MANAGER
from .audio import sound_effects
from .entities import *


class LogicProcess:
    def __init__(
            self,
            shm: SharedMemory,
            command_in_queue: Queue,
            command_out_queue: Queue,
            write_lock: Lock,
            global_vars: GlobalVars
    ):
        self._start = perf_counter()
        self._write_lock = write_lock
        self._ciq = command_in_queue
        self._coq = command_out_queue
        self._global_vars = global_vars

        local_buffer = bytearray(ctypes.sizeof(base_entity_t) * MAX_ENTITIES)

        self.__entity_buffer = (base_entity_t * MAX_ENTITIES).from_buffer(shm.buf)
        self._runtime_buffer = (base_entity_t * MAX_ENTITIES).from_buffer(local_buffer)

        # copy once to make sure starting value is the same
        self._runtime_buffer[:] = self.__entity_buffer

        self._running = True

    def get_ic_prefix(self) -> str:
        t = round(perf_counter() - self._start, 4)

        t1, t2 = str(t).split(".")
        return f"(logic: {os.getpid()}) {t1: >4}.{t2: <4} |> "

    def update_entities(self, delta: float) -> None:
        """
        update all entities
        """
        start = perf_counter()

        # update commands
        while True:
            try:
                item: ProcessCommand = self._ciq.get_nowait()

            except Empty:
                break

            if item.type == CommandType.reset:
                self._running = False
                return

            else:
                ic(item)

        # check for new controllers
        # if len(self._new_controllers) > 0:
        #     self._new_controllers_lock.aquire()
        #     tmp = self._new_controllers.copy()
        #     self._new_controllers.clear()
        #     self._new_controllers_lock.release()
        #
        #     for new_controller in tmp:
        #         # spawn new player
        #         Player(coalition=Coalitions.blue, controller=new_controller)
        #         ic(new_controller, Player)

        # update sounds
        sound_effects.update()

        # reset and update detection Groups
        DETECTION_GROUP_MANAGER.reset()

        # update entities
        GravityAffected.calculate_gravity(delta)
        FrictionXAffected.calculate_friction(delta)
        WallBouncer.update()

        Bullets.update(delta)
        DETECTION_GROUP_MANAGER.update_detection()
        Updated.update(delta)

        CollisionDestroyed.update()

    def update_memory(self) -> None:
        """
        copy runtime buffer to memory buffer
        """
        self._write_lock.acquire()
        self.__entity_buffer[:] = self._runtime_buffer
        self._write_lock.release()

    def reset_game(self) -> None:
        Updated.kill()

        # reset entity buffer
        self._write_lock.acquire()
        self.__entity_buffer[:] = 0
        self._runtime_buffer[:] = self.__entity_buffer
        self._write_lock.release()

        # reset global vars
        self._global_vars.reset()

        for player in Players.sprites():
            player.respawn()


def run_continuous(
        shm: SharedMemory,
        command_in_queue: Queue,
        command_out_queue: Queue,
        write_lock: Lock,
        global_vars_values: dict[str, Value]
) -> None:
    """
    run the logic process continuously
    """
    global_vars = GlobalVars(global_vars_values)
    global_vars.update()

    lp = LogicProcess(shm, command_in_queue, command_out_queue, write_lock, global_vars)

    ic.configureOutput(prefix=lp.get_ic_prefix)

    last_run = perf_counter()
    while lp.running:
        # calculate time since last loop
        now = perf_counter()
        delta = last_run - now

        # update entities
        lp.update_entities(delta)

        # copy buffer
        lp.update_memory()

        # update from buffer
        global_vars.update()

        last_run = now

    ic("logic quit")
