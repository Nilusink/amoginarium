"""
Uses the keyboard as a controller.

Path: amoginarium/graphics/controllers/_keyboard_controller.py
Project: amoginarium
Created: 25.01.2024
Authors: Nilusink, LukasKrah
"""

import typing as tp
from dataclasses import dataclass

import pygame as pg

from amoginarium import pv

from ._base_controller import Controller


@dataclass(frozen=True)
class Keyboardcontrols:
    up: str = pg.K_w
    down: str = pg.K_s
    left: str = pg.K_a
    right: str = pg.K_d
    press: str = pg.K_SPACE


class KeyboardController(Controller):
    @classmethod
    def get(cls) -> tp.Self:
        return super().get("0")

    def __init__(self, *_, **__) -> None:
        super().__init__("0")

        self._controls = Keyboardcontrols()

    def update(self, delta):
        pressed_keys = pg.key.get_pressed()
        mouse_buttons = pg.mouse.get_pressed(5)
        pos = pg.mouse.get_pos()
        screen_size_offset = pv.global_vars.get_screen_size_offset()
        pos = ((pos[0] - screen_size_offset.x), (pos[1] - screen_size_offset.y))

        # read controls
        up = pressed_keys[self._controls.up]
        down = pressed_keys[self._controls.down]
        left = pressed_keys[self._controls.left]
        right = pressed_keys[self._controls.right]
        self._keys.jump = pressed_keys[self._controls.press]

        self._keys.shoot = mouse_buttons[0]
        self._keys.inventory = pressed_keys[pg.K_e]
        self._keys.drop = pressed_keys[pg.K_q]
        self._keys.reload = pressed_keys[pg.K_r]

        self._keys.wpn_f = pressed_keys[pg.K_TAB]
        self._keys.wpn_b = False

        self._keys.ride = pressed_keys[pg.K_f]
        self._keys.m_right = mouse_buttons[2]

        # set joystick position (using wasd keys)
        self._keys.joy_x = -left + right
        self._keys.joy_y = -down + up

        self._keys.mouse_x = pos[0]
        self._keys.mouse_y = pos[1]
