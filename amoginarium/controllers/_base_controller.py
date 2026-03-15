"""
_base_controller.py
25. January 2024

all controller types should inherit from this

Author:
Nilusink
"""
from dataclasses import dataclass
from icecream import ic
import typing as tp

from ..logic import Vec2


@dataclass
class controls:
    jump: bool = False
    reload: bool = False
    shoot: bool = False
    wpn_f: bool = False
    wpn_b: bool = False
    joy_btn: bool = False
    joy_x: float = 0
    joy_y: float = 0


class _Controllers:
    """
    a collection of all controllers
    """
    _controllers: list["Controller"]
    _callbacks: dict[int, tp.Callable]

    def __init__(self) -> None:
        self._controllers = []
        self._callbacks = {}

    @property
    def controllers(self) -> list["Controller"]:
        return self._controllers.copy()

    def exists(self, cid: str) -> bool:
        """
        checks if a controller already exists
        """
        return cid in [c.id for c in self._controllers]

    def get_by_id(self, cid: str) -> tp.Union["Controller", None]:
        if not self.exists(cid):
            raise ValueError(f"No controller with id \"{cid}\" exists!")

        for controller in self._controllers:
            if controller.id == cid:
                return controller

        return None

    def append(self, controller: "Controller") -> None:
        """
        add a new controller to the group
        """
        self._controllers.append(controller)
        self._on_new_controller(controller)

    def _on_new_controller(self, controller: "Controller") -> None:
        """
        actual callback method
        """
        for callback in self._callbacks.values():
            callback(controller)

    def on_new_controller(
        self,
        callback: tp.Callable[["Controller"], tp.Any]
    ) -> int:
        """
        add a callback for adding new controllers
        """
        if len(self._callbacks) == 0:
            new_id = 0

        else:
            new_id = max(list(self._callbacks.keys())) + 1

        self._callbacks[new_id] = callback

        return new_id

    def remove_callback(self, cid: int) -> None:
        """
        remove a callback with it's callback-id
        """
        if cid in self._callbacks:
            self._callbacks.pop(cid)
            return

        raise ValueError(f"Invalid cid: {cid}")


Controllers = _Controllers()


class Controller:
    _keys: controls

    def __new__(cls, *args, **kwargs):
        return super(Controller, cls).__new__(cls)

    @classmethod
    def get(cls, cid: str, *args, **kwargs) -> "Controller":
        ic("base get")
        ic("called base cls.get with id ", cid)
        if Controllers.exists(cid):
            ic("re-linking already existing controller", cid)
            return Controllers.get_by_id(cid)

        ic("create instance in cls.get()")
        ic(cid, args, kwargs)
        new_instance = cls(cid, *args, **kwargs)

        # append every new instance to controllers
        Controllers.append(new_instance)

        return new_instance

    def __init__(self, id: str) -> None:
        self._keys = controls()
        self._id = id
        self.on_rumble: tp.Callable = ...
        self.on_stop_rumble: tp.Callable = ...
        self.on_feedback_shoot: tp.Callable = ...
        self.on_feedback_hit: tp.Callable = ...
        self.on_feedback_heal_start: tp.Callable = ...
        self.on_feedback_heal_stop: tp.Callable = ...
        self._heal_running = False

    @property
    def id(self) -> str:
        """
        unique id
        """
        return self._id

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
    def wpn_f(self) -> bool:
        return self._keys.wpn_f

    @property
    def wpn_b(self) -> bool:
        return self._keys.wpn_b

    @property
    def joy_btn(self) -> bool:
        return self._keys.joy_btn

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
    def controls(self) -> controls:
        return self._keys.copy()

    # @classmethod  # making this a classmethod didn't work for some reason
    @staticmethod
    def joy_curve(
        value: float,
        x_deadzone: float = 0,
        y_deadzone: float = 0,
        x_saturation: float = 1,
        y_saturation: float = 1,
        curve: float = 0  # TODO: curve
    ) -> float:
        """
        apply a specific curve for joystick values (rangin from -1 to 1)

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
        value = max(
            0,
            abs(value) - x_deadzone
        ) * (
            (1 - y_deadzone) / (x_saturation - x_deadzone)
        )

        # input deadzone should habe priority
        if value == 0:
            return 0

        # apply output deadzone
        value = value_sign * min(1, value + y_deadzone)

        # apply y saturation
        return value * y_saturation

    def update(self, delta: float) -> None:
        """
        update the control inputs
        """
        raise NotImplementedError("tried to call base-controller update")

    def rumble(
        self,
        low_frequency,
        high_frequency,
        duration
    ) -> None:
        """
        start joystick vibration

        :param low_frequency:
        :param high_frequency:
        :param duration: duration in ms (0=inf)
        """
        if self.on_rumble is not ...:
            self.on_rumble(low_frequency, high_frequency, duration)

    def stop_rumble(self) -> None:
        """
        stop joystick vibration
        """
        if self.on_stop_rumble is not ...:
            self.on_stop_rumble()

    def feedback_collide(self) -> None:
        """
        when the player hits a wall
        """

    def feedback_shoot(self) -> None:
        """
        controller input on shoot
        """
        if self.on_feedback_shoot is not ...:
            self.on_feedback_shoot()

    def feedback_hit(self) -> None:
        """
        controller input on hit
        """
        if self.on_feedback_hit is not ...:
            self.on_feedback_hit()

    def feedback_heal_start(self) -> None:
        """
        controller input on heal start
        """
        if self._heal_running:
            return

        self._heal_running = True

        if self.on_feedback_heal_start is not ...:
            self.on_feedback_heal_start()

    def feedback_heal_stop(self) -> None:
        """
        controller input on heal stop 
        """
        if not self._heal_running:
            return

        self._heal_running = False

        if self.on_feedback_heal_stop is not ...:
            self.on_feedback_heal_stop()

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}, id=\"{self.id}\">"

    def __repr__(self) -> str:
        return self.__str__()
