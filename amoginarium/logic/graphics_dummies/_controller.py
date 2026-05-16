"""
_controller.py
31.03.2026

controller synced to graphics controls

Author:
Nilusink
"""

import typing as tp
from types import EllipsisType

from amoginarium import pv
from amoginarium.shared import Controls
from amoginarium.shared.utility import Vec2


class Controller:
    _keys: Controls

    def __init__(
        self,
        controller_id: int,
    ) -> None:
        self._keys = Controls()
        self._keys.init(controller_id, pv.C_BUFF)
        self.on_rumble: tp.Callable | EllipsisType = ...
        self.on_stop_rumble: tp.Callable | EllipsisType = ...
        self.on_feedback_shoot: tp.Callable | EllipsisType = ...
        self.on_feedback_hit: tp.Callable | EllipsisType = ...
        self.on_feedback_heal_start: tp.Callable | EllipsisType = ...
        self.on_feedback_heal_stop: tp.Callable | EllipsisType = ...
        self._heal_running = False

    @property
    def jump(self) -> bool:
        return self._keys.jump

    @property
    def reload(self) -> bool:
        return self._keys.reload

    @property
    def shoot(self) -> bool:
        return self._keys.shoot

    @property
    def inventory(self) -> bool:
        return self._keys.inventory

    @property
    def drop(self) -> bool:
        return self._keys.drop

    @property
    def wpn_f(self) -> bool:
        return self._keys.wpn_f

    @property
    def wpn_b(self) -> bool:
        return self._keys.wpn_b

    @property
    def joy_btn(self) -> bool:
        return self._keys.joy_btn

    @property
    def ride(self) -> bool:
        return self._keys.ride

    @property
    def m_right(self) -> bool:
        return self._keys.m_right

    @property
    def joy_x(self) -> float:
        return self._keys.joy_x

    @property
    def joy_y(self) -> float:
        return self._keys.joy_y

    @property
    def joy_polar(self) -> Vec2:
        return Vec2().from_cartesian(self.joy_x, self.joy_y)

    @property
    def mouse_x(self) -> float:
        return self._keys.mouse_x

    @property
    def mouse_y(self) -> float:
        return self._keys.mouse_y

    @property
    def controls(self) -> Controls:
        return self._keys

    # @classmethod  # making this a classmethod didn't work for some reason
    @staticmethod
    def joy_curve(
        value: float,
        x_deadzone: float = 0,
        y_deadzone: float = 0,
        x_saturation: float = 1,
        y_saturation: float = 1,
        curve: float = 0,  # TODO: curve
    ) -> float:
        """
        Apply a specific curve for joystick values (rangin from -1 to 1)

        :param value: value to process
        :param x_deadzone: percentage of how much input shuold be ignore
            around 0
        :param y_deadzone: min value for output
        :param x_saturation: how much input should be 100%
        :param y_saturation: max value of output (could theoretically be >1)

        example::

            # raw controller data
            x_raw = controller.get_axis(0)

            # filtered value
            r_processed = joy_curve(
                value=x_raw,
                x_deadzone=.2,  # 20% input deadzone
                y_deadzone=.2,  # 20% output deadzone
                x_saturation=.8 # 80% input saturation
            )

        .. image:: joystick_curve.png
        """
        # get sign (either +1 or -1)
        value_sign = (value / abs(value)) if value != 0 else 1

        # look, I just tried putting the variables in random orders and somehow
        # it workd, I never even knew why
        value = max(0, abs(value) - x_deadzone) * (
            (1 - y_deadzone) / (x_saturation - x_deadzone)
        )

        # input deadzone should habe priority
        if value == 0:
            return 0

        # apply output deadzone
        value = value_sign * min(1, value + y_deadzone)

        # apply y saturation
        return value * y_saturation

    def rumble(self, low_frequency, high_frequency, duration) -> None:
        """
        Start joystick vibration

        :param low_frequency:
        :param high_frequency:
        :param duration: duration in ms (0=inf)
        """
        if self.on_rumble is not ...:
            self.on_rumble(low_frequency, high_frequency, duration)

    def stop_rumble(self) -> None:
        """
        Stop joystick vibration
        """
        if self.on_stop_rumble is not ...:
            self.on_stop_rumble()

    def feedback_collide(self) -> None:
        """
        When the player hits a wall
        """

    def feedback_shoot(self) -> None:
        """
        Controller input on shoot
        """
        if self.on_feedback_shoot is not ...:
            self.on_feedback_shoot()

    def feedback_hit(self) -> None:
        """
        Controller input on hit
        """
        if self.on_feedback_hit is not ...:
            self.on_feedback_hit()

    def feedback_heal_start(self) -> None:
        """
        Controller input on heal start
        """
        if self._heal_running:
            return

        self._heal_running = True

        if self.on_feedback_heal_start is not ...:
            self.on_feedback_heal_start()

    def feedback_heal_stop(self) -> None:
        """
        Controller input on heal stop
        """
        if not self._heal_running:
            return

        self._heal_running = False

        if self.on_feedback_heal_stop is not ...:
            self.on_feedback_heal_stop()

    def __str__(self) -> str:
        return f'<{self.__class__.__name__}, id="{self.controls._shm_id}">'

    def __repr__(self) -> str:
        return self.__str__()
