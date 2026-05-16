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
        ("bottom", ctypes.c_long),
    ]


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", ctypes.c_ulong),
    ]


MonitorEnumProc = ctypes.WINFUNCTYPE(
    ctypes.c_int,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.POINTER(RECT),
    ctypes.c_void_p,
)


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
        """Returns the bounds of the single monitor housing the majority of the window."""
        if not self.__window:
            return self.__top_left, self.__size

        hmonitor = self.__user32.MonitorFromWindow(
            self.__window, MONITOR_DEFAULTTONEAREST
        )

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

        return self.__top_left, self.__size

    def get_current_monitor_combined(self) -> tuple[Vec2, Vec2, bool]:
        """
        Calculates a bounding box encompassing ALL monitors the window intersects.
        Automatically bridges gaps in odd arrangements.
        Only expands if the window penetrates at least 1/3 of the target screen.
        :returns: (top_left, size, whether its a combined monitor)
        """
        if not self.__window:
            return self.__top_left, self.__size, False

        win_rect = RECT()
        if not self.__user32.GetWindowRect(self.__window, ctypes.byref(win_rect)):
            top_left, size = self.get_current_monitor()
            return top_left, size, False

        wx, wy = win_rect.left, win_rect.top
        wr, wb = win_rect.right, win_rect.bottom

        all_monitors: list[tuple[int, int, int, int]] = []

        def enum_callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
            r = lprcMonitor.contents
            all_monitors.append((r.left, r.top, r.right, r.bottom))
            return 1

        cb_func = MonitorEnumProc(enum_callback)
        self.__user32.EnumDisplayMonitors(None, None, cb_func, 0)

        intersecting = []
        for mx1, my1, mx2, my2 in all_monitors:
            ix1 = max(wx, mx1)
            iy1 = max(wy, my1)
            ix2 = min(wr, mx2)
            iy2 = min(wb, my2)

            if ix1 < ix2 and iy1 < iy2:
                ix_w = ix2 - ix1
                ix_h = iy2 - iy1

                mon_w = mx2 - mx1
                mon_h = my2 - my1

                if ix_w >= (mon_w / 3.0) and ix_h >= (mon_h / 3.0):
                    intersecting.append((mx1, my1, mx2, my2))

        if len(intersecting) <= 1:
            top_left, size = self.get_current_monitor()
            return top_left, size, False

        min_x = min(m[0] for m in intersecting)
        min_y = min(m[1] for m in intersecting)
        max_x = max(m[2] for m in intersecting)
        max_y = max(m[3] for m in intersecting)

        w = max_x - min_x
        h = max_y - min_y

        self.__top_left.xy = (min_x, min_y)
        self.__size.xy = (w, h)
        return self.__top_left, self.__size, True


WindowsMonitorService = _WindowsMonitorService()
