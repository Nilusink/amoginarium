"""
Synced controller controls.

Path: amoginarium/shared/_controlls.py
Project: amoginarium
Created: 31.03.2026
Authors: Nilusink
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from icecream import ic

if TYPE_CHECKING:
    from ctypes import Array

    from ._shared_memory import base_controller_t


class Controls:
    def __init__(self) -> None:
        self._shm_id = -1
        self._shm: Array[base_controller_t] = ...

    def init(
        self, id: int, c_shm: Array[base_controller_t], initialize: bool = False
    ) -> None:
        """
        Setup controller.

        :param id: controller id (for shm)
        :param c_shm: controller shared memory buffer
        :param initialize: whether to initialize all values to default or not
        """
        self._shm_id = id
        self._shm = c_shm

        if initialize:
            self._shm[self._shm_id].jump = False
            self._shm[self._shm_id].reload = False
            self._shm[self._shm_id].shoot = False
            self._shm[self._shm_id].inventory = False
            self._shm[self._shm_id].drop = False
            self._shm[self._shm_id].wpn_f = False
            self._shm[self._shm_id].wpn_b = False
            self._shm[self._shm_id].joy_btn = False
            self._shm[self._shm_id].ride = False
            self._shm[self._shm_id].m_right = False
            self._shm[self._shm_id].joy_x = 0
            self._shm[self._shm_id].joy_y = 0
            self._shm[self._shm_id].mouse_x = 0
            self._shm[self._shm_id].mouse_y = 0

    # region properties
    @property
    def jump(self) -> bool:
        return self._shm[self._shm_id].jump

    @jump.setter
    def jump(self, value: bool) -> None:
        self._shm[self._shm_id].jump = value

    @property
    def reload(self) -> bool:
        return self._shm[self._shm_id].reload

    @reload.setter
    def reload(self, value: bool) -> None:
        self._shm[self._shm_id].reload = value

    @property
    def shoot(self) -> bool:
        return self._shm[self._shm_id].shoot

    @shoot.setter
    def shoot(self, value: bool) -> None:
        self._shm[self._shm_id].shoot = value

    @property
    def inventory(self) -> bool:
        return self._shm[self._shm_id].inventory

    @inventory.setter
    def inventory(self, value: bool) -> None:
        self._shm[self._shm_id].inventory = value

    @property
    def drop(self) -> bool:
        return self._shm[self._shm_id].drop

    @drop.setter
    def drop(self, value: bool) -> None:
        self._shm[self._shm_id].drop = value

    @property
    def wpn_f(self) -> bool:
        return self._shm[self._shm_id].wpn_f

    @wpn_f.setter
    def wpn_f(self, value: bool) -> None:
        self._shm[self._shm_id].wpn_f = value

    @property
    def wpn_b(self) -> bool:
        return self._shm[self._shm_id].wpn_b

    @wpn_b.setter
    def wpn_b(self, value: bool) -> None:
        self._shm[self._shm_id].wpn_b = value

    @property
    def joy_btn(self) -> bool:
        return self._shm[self._shm_id].joy_btn

    @joy_btn.setter
    def joy_btn(self, value: bool) -> None:
        self._shm[self._shm_id].joy_btn = value

    @property
    def ride(self) -> bool:
        return self._shm[self._shm_id].ride

    @ride.setter
    def ride(self, value: bool) -> None:
        self._shm[self._shm_id].ride = value

    @property
    def m_right(self) -> bool:
        return self._shm[self._shm_id].m_right

    @m_right.setter
    def m_right(self, value: bool) -> None:
        self._shm[self._shm_id].m_right = value

    @property
    def joy_x(self) -> float:
        return self._shm[self._shm_id].joy_x

    @joy_x.setter
    def joy_x(self, value: float) -> None:
        self._shm[self._shm_id].joy_x = value

    @property
    def joy_y(self) -> float:
        return self._shm[self._shm_id].joy_y

    @joy_y.setter
    def joy_y(self, value: float) -> None:
        self._shm[self._shm_id].joy_y = value

    @property
    def mouse_x(self) -> float:
        return self._shm[self._shm_id].mouse_x

    @mouse_x.setter
    def mouse_x(self, value: float) -> None:
        self._shm[self._shm_id].mouse_x = value

    @property
    def mouse_y(self) -> float:
        return self._shm[self._shm_id].mouse_y

    @mouse_y.setter
    def mouse_y(self, value: float) -> None:
        self._shm[self._shm_id].mouse_y = value

    # endregion
