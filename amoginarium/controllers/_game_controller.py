"""
_game_controller.py
26. January 2024

uses the keyboard as a controller

Author:
Nilusink
"""
from dataclasses import dataclass
# from icecream import ic
import pygame as pg

from ._base_controller import Controller


# switch controller
@dataclass(frozen=True)
class ControllerKeymap:
    y: int = 0
    b: int = 1
    a: int = 2
    x: int = 3
    l1: int = 4
    r1: int = 5
    l2: int = 6
    r2: int = 7
    lopt: int = 8
    ropt: int = 9
    ljoy: int = 10
    rjoy: int = 11
    menu: int = 12


# PS4 controller
@dataclass(frozen=True)
class ControllerKeybmap:
    y: int = 0
    b: int = 3
    a: int = 0
    x: int = 3
    l1: int = 4
    r1: int = 10
    r2_axis: int = 5
    l2: int = 6
    r2: int = 7
    lopt: int = 8
    ropt: int = 9
    ljoy: int = 10
    rjoy: int = 11
    menu: int = 12


class GameController(Controller):
    x_dead_zone: float = .1
    y_dead_zone: float = .1

    def __init__(
            self,
            id: str,
            pygame_joystick: pg.joystick.JoystickType
    ) -> None:
        if not pygame_joystick.get_init():
            pygame_joystick.init()

        self._joystick = pygame_joystick

        super().__init__(id)

    def set_joystick(self, joystick: pg.joystick.JoystickType) -> None:
        """
        re-assign the pygame joystick
        """
        self._joystick = joystick

    def btn(self, n_button: int) -> bool:
        """
        get a joystick button
        """
        return self._joystick.get_button(n_button)

    def update(self, delta):
        # read controls
        self._keys.shoot = self.btn(ControllerKeybmap.r2) or self.btn(ControllerKeybmap.r1) or self._joystick.get_axis(ControllerKeybmap.r2_axis) > 0
        self._keys.reload = self.btn(ControllerKeybmap.b)
        self._keys.jump = self.btn(ControllerKeybmap.a)
        self._keys.idk = self.btn(ControllerKeybmap.x)

        # set joystick position
        self._keys.joy_x = self.joy_curve(
            self._joystick.get_axis(0),
            x_deadzone=self.x_dead_zone
        )
        self._keys.joy_y = self.joy_curve(
            self._joystick.get_axis(1),
            x_deadzone=self.y_dead_zone
        )

        self._keys.joy_btn = self.btn(ControllerKeybmap.ljoy)

    def rumble(
            self,
            low_frequency,
            high_frequency,
            duration
    ) -> None:
        self._joystick.rumble(low_frequency, high_frequency, duration)

    def feedback_collide(self) -> None:
        """
        when the player hits a wall
        """
        self.rumble(1000, 2000, 150)

    def feedback_shoot(self) -> None:
        """
        controller input on shoot
        """
        self.rumble(2000, 3000, 100)

    def feedback_hit(self) -> None:
        """
        controller input on hit
        """
        self.rumble(300, 2200, 300)

    def stop_rumble(self) -> None:
        self._joystick.stop_rumble()

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}, name={self._joystick.get_name()}>"
