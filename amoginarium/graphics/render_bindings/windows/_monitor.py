"""
amoginarium/graphics/render_bindings/windows/_monitor.py

Project: amoginarium
Created: 13.04.2026
Authors: LukasKrah
"""

import typing as tp
import ctypes

from amoginarium.shared.utility import Vec2


MONITOR_DEFAULTTONEAREST = 2


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long)
    ]

class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", ctypes.c_ulong)
    ]


class _WindowsMonitorService:
    __slots__ = ("__window", "__user32", "__top_left", "__size")
    __user32: tp.Any
    __window: tp.Any

    __top_left: tp.Final[Vec2]
    __size: tp.Final[Vec2]

    def __init__(self) -> None:
        self.__window = None
        self.__user32 = ctypes.windll.user32

        self.__top_left = Vec2()
        self.__size = Vec2().from_cartesian(1920, 1080)

    def set_window(self, title: str) -> None:
        self.__window = self.__user32.FindWindowW(None, title)

    def get_current_monitor(self) -> tuple[Vec2, Vec2]:
        if not self.__window:
            return self.__top_left, self.__size

        hmonitor = self.__user32.MonitorFromWindow(self.__window, MONITOR_DEFAULTTONEAREST)

        monitor_info = MONITORINFO()
        monitor_info.cbSize = ctypes.sizeof(MONITORINFO)

        if self.__user32.GetMonitorInfoW(hmonitor, ctypes.byref(monitor_info)):
            rect = monitor_info.rcMonitor

            x = rect.left
            y = rect.top
            w = rect.right - rect.left
            h = rect.bottom - rect.top

            self.__top_left.xy = (x, y)
            self.__size.xy = (w, h)

        print(self.__top_left, self.__size)

        return self.__top_left, self.__size

WindowsMonitorService = _WindowsMonitorService()