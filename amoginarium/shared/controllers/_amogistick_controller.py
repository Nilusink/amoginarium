"""
_ws_controller.py
01. February 2024

interfaces with an amogistick controller client

Author:
Nilusink
"""

from icecream import ic
from ._base_controller import Controller


class AmogistickController(Controller):
    x_dead_zone: float = .1
    y_dead_zone: float = .1
    joy_thresh: float = 5e3

    def __init__(self, controller_id: str) -> None:
        super().__init__(controller_id)

    def update(self, delta):
        """
        updates are provided by the communications thread,
        so the default update funcion is ignored
        """
        pass

    def update_controls(
            self,
            trigger_btn: bool = ...,
            aux_l_btn: bool = ...,
            aux_r_btn: bool = ...,
            joy_btn: bool = ...,
            joy_x: float = ...,
            joy_y: float = ...
    ) -> None:
        """
        controls updates provided by the server
        """
        # apply a curve to the controller values
        self._keys.joy_x = self.joy_curve(
            (joy_x - self.joy_thresh) / self.joy_thresh,
            self.x_dead_zone
        )
        self._keys.joy_y = self.joy_curve(
            (joy_y - self.joy_thresh) / self.joy_thresh,
            self.y_dead_zone
        )
        #ic(self._keys.joy_x, self._keys.joy_y)
        #ic(joy_x, joy_y)

        # write button
        self._keys.jump = self._keys.joy_y > .3 or aux_r_btn or aux_l_btn
        self._keys.shoot = trigger_btn
        self._keys.reload = joy_btn  # map joy click to reload
