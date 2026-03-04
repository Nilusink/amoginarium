"""
_utility_classes.py
25. January 2024

defines a few useful classes

Author:
Nilusink, melektron
"""
from time import perf_counter
import typing as tp
import math as m
import asyncio
import inspect


class BetterDict:
    """
    each element is also accessible with instance.element
    """

    def __init__(self, **initial) -> None:
        for key, value in initial.items():
            setattr(self, key, value)

    def __setitem__(self, key: str, value: tp.Any) -> None:
        setattr(self, key, value)

    def __getitem__(self, item: str) -> tp.Any:
        return self.__dict__[item]

    def __delitem__(self, key) -> None:
        delattr(self, key)


class SimpleLock:
    def __init__(self) -> None:
        self.__locked_by: str = ...

    def aquire(
            self,
            timeout: float = 0
    ) -> bool:
        """
        :param timeout: timeout in seconds
        """
        start = perf_counter()

        curframe = inspect.currentframe()
        called_by = inspect.getouterframes(curframe, 2)[1][3]

        while perf_counter() - start > timeout or timeout == 0:
            if self.__locked_by is ...:
                self.__locked_by = called_by
                return True

        return False

    def release(self) -> None:
        """
        release a lock (only works from same function)
        """
        curframe = inspect.currentframe()
        called_by = inspect.getouterframes(curframe, 2)[1][3]

        if called_by != self.__locked_by:
            raise NameError("Lock can't be released from different function!")

        self.__locked_by = ...


class _BaseTimer:
    @staticmethod
    def _run_callback(cb: tp.Union[tp.Callable, None]):
        if cb is not None:
            asyncio.create_task(cb())


class WDTimer(_BaseTimer):
    def __init__(self, timeout: float) -> None:
        """
        Watchdog timer that continuously down from the time
        specified in timeout and but can be reset to the start at any time
        using the refresh() method.
        If the timer reaches zero (timeout) it fires a callback.
        When the timer is restarted the first time after reaching zero using
        refresh() (or the first time it this method is called) a restart
        callback fires.)

        timeout: time to count down for in seconds
        """
        self._timeout: float = timeout
        self._timer_task: asyncio.Task | None = None
        self._on_timeout_cb: tp.Union[tp.Callable, None] = None
        self._on_restart_cb: tp.Union[tp.Callable, None] = None

    def on_timeout(self, cb: tp.Callable):
        """
        Registers a callback handler (must be async) for the timeout event
        (aka. when the timer isn't refreshed before the timeout time.)

        Note: There can only be one callback, registering a second one
        overwrites the first one.
        """
        self._on_timeout_cb = cb

        return self

    def on_restart(self, cb: tp.Callable):
        """
        Registers a callback handler (must be async) for the restart event
        (aka. when the timer restarts counting after a timeout or
        on initial start)

        Note: There can only be one callback, registering a second one
        overwrites the first one.
        """
        self._on_restart_cb = cb

        return self

    def refresh(self):
        """
        Resets the timer so it starts counting all over again if it is already
        counting and starts it if it has finished counting down or is started
        the first time.
        This causes restart callback to run if the timer isn't running
        at the time of calling.
        """

        # first start
        if self._timer_task is None:
            self._run_callback(self._on_restart_cb)
            self._timer_task = asyncio.create_task(self._timer_fn())

        # after timeout
        elif self._timer_task.done():
            self._run_callback(self._on_restart_cb)
            self._timer_task = asyncio.create_task(self._timer_fn())

        # while it is still running
        else:
            self._timer_task.cancel()
            self._timer_task = asyncio.create_task(self._timer_fn())

        return self

    def cancel(self) -> None:
        """
        cancel the timer
        """
        if self._timer_task is not None:
            self._timer_task.cancel()

    async def _timer_fn(self):
        await asyncio.sleep(self._timeout)
        self._run_callback(self._on_timeout_cb)

    def __del__(self):
        if self._timer_task is None:
            return self
        self._timer_task.cancel()
        self._timer_task = None


class Color:
    r: int
    g: int
    b: int
    a: int | None

    def __init__(self, r: int, g: int, b: int, a: int = None) -> None:
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    @classmethod
    def from_255(cls, r: int, g: int, b: int, a: int = None) -> tp.Self:
        return cls(r, g, b, a)

    @classmethod
    def from_1(cls, r: float, g: float, b: float, a: float = None) -> tp.Self:
        return cls(
            m.ceil(r * 255),
            m.ceil(g * 255),
            m.ceil(b * 255),
            m.ceil(a * 255) if a is not None else None
        )

    @classmethod
    def black(cls, alpha: int = None) -> tp.Self:
        """
        :param alpha: alpha in range [0, 255]
        """
        return cls.from_255(0, 0, 0, alpha)

    @classmethod
    def white(cls, alpha: int = None) -> tp.Self:
        """
        :param alpha: alpha in range [0, 255]
        """
        return cls.from_255(255, 255, 255, alpha)

    @classmethod
    def red(cls, alpha: int = None) -> tp.Self:
        """
        :param alpha: alpha in range [0, 255]
        """
        return cls.from_255(255, 0, 0, alpha)

    @property
    def rgb255(self) -> tuple[int, int, int]:
        return (
            int(self.r),
            int(self.g),
            int(self.b)
        )

    @property
    def rgba255(self) -> tuple[int, int, int, int]:
        alpha = 255 if self.a is None else self.a

        return (
            int(self.r),
            int(self.g),
            int(self.b),
            int(alpha)
        )

    @property
    def argb255(self) -> tuple[int, int, int, int]:
        rgba = self.rgba255

        return (rgba[3], *rgba[:3])

    @property
    def auto255(self) -> tuple[int, int, int, int] | tuple[int, int, int]:
        return self.rgb255 if self.a is None else self.rgba255

    @property
    def rgb1(self) -> tuple[float, float, float]:
        return self.to_1(self.r, self.g, self.b)

    @property
    def rgba1(self) -> tuple[float, float, float, float]:
        alpha = 1 if self.a is None else self.a

        return self.to_1(self.r, self.g, self.b, alpha)

    @property
    def argb1(self) -> tuple[int, int, int, int]:
        rgba = self.rgba1

        return (rgba[3], *rgba[:3])

    @property
    def auto1(
            self
    ) -> tuple[float, float, float, float] | tuple[float, float, float]:
        return self.rgb255 if self.a is None else self.rgba255

    @property
    def is_rgba(self) -> bool:
        return self.a is not None

    @staticmethod
    def to_255(
            r: float,
            g: float,
            b: float,
            a: float = None
    ) -> tuple[int, int, int] | tuple[int, int, int, int]:
        # return rgb if alpha is not given
        if a is None:
            return (
                int(r * 255),
                int(g * 255),
                int(b * 255)
            )

        # return rgba if alpha is provided
        return (
            int(r * 255),
            int(g * 255),
            int(b * 255),
            int(a * 255)
        )

    @staticmethod
    def to_1(
            r: int,
            g: int,
            b: int,
            a: int = None
    ) -> tuple[float, float, float] | tuple[float, float, float, float]:
        if a is None:
            return (
                r / 255,
                g / 255,
                b / 255
            )

        return (
            r / 255,
            g / 255,
            b / 255,
            a / 255
        )

    @staticmethod
    def fade(a: "Color", b: "Color", t: float) -> "Color":
        """
        smoothly fade between a and b
        t: 0-1
        """
        return Color.from_255(
            int(a.r + (b.r - a.r) * t),
            int(a.g + (b.g - a.g) * t),
            int(a.b + (b.b - a.b) * t),
            int(a.a + (b.a - a.a) * t) if None not in (a.a, b.a) else None,
        )

    # TEMPORARY
    @staticmethod
    def c_255_to_1(r: float, g: float, b: float) -> tuple[float, float, float]:
        return r / 255.0, g / 255.0, b / 255.0
