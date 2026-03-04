"""
amoginarium/ui/_base_widget.py

Project: amoginarium
"""

##################################################
#                    Imports                     #
##################################################

from __future__ import annotations

from typing import Any, Callable, Optional
# noinspection PyPackageRequirements
import pygame as pg

from ._event_handler import EventHandler
from ..audio import SoundEffect
from ..logic import coord_t, convert_coord, Vec2
from ..shared import global_vars
from ._event import AmogusEvent, event_t

from ._ui_element import UIElement
from ._types import anchor_t


##################################################
#                     Code                       #
##################################################

class BaseWidget(UIElement):
    __abs_position: Vec2  # Absolute position - anchor not factored in
    __abs_size: Vec2  # Absolute size
    __rel_position: Vec2  # Relative position - anchor not factored in
    __rel_size: Vec2  # Relative size
    __anchor: anchor_t  # Placement anchor

    __absolute: bool
    __scaling: bool

    __width: float  # Absolute width
    __height: float  # Absolute height
    __top_left: Vec2  # Absolute top left
    __top_right: Vec2  # Absolute top right
    __bottom_left: Vec2  # Absolute bottom left
    __bottom_right: Vec2  # Absolute bottom right

    __hover: bool
    __last_hover: bool

    __events: list[AmogusEvent]

    def __init__(
            self,
            position: coord_t,
            size: coord_t,
            *_args: Any,
            anchor: anchor_t = "center",
            absolute: bool = False,
            scaling: bool = True
    ) -> None:
        super().__init__()
        self.__absolute = absolute
        self.__scaling = scaling
        self.__anchor = anchor

        self.__last_hover = False
        self.__hover = False

        if self.__absolute:
            if self.__scaling:  # Absolute positioning with scaling
                self.__rel_position, self.__abs_position = self.__absolute_to_relative(position, size)
            else:  # Absolute positioning without scaling
                self.__abs_position = convert_coord(position, Vec2)
                self.__abs_size = convert_coord(size, Vec2)
        else:
            if self.__scaling:  # Relative positioning with scaling
                self.__rel_position = convert_coord(position, Vec2)
                self.__rel_size = convert_coord(size, Vec2)
            else:  # Relative positioning without scaling
                self.__abs_position, self.__abs_size = self.__relative_to_absolute(position, size)

        self.__events = []
        EventHandler.add_check_events_callback(self.__check_event)

    @staticmethod
    def __relative_to_absolute(
            relative_position: coord_t,
            relative_size: coord_t
    ) -> tuple[Vec2, Vec2]:

        return (
            convert_coord(
                (
                    int(relative_position.x * 1920),
                    int(relative_position.y * 1080)
                ),
                Vec2
            ),
            convert_coord(
                (
                    int(relative_size.x * 1920),
                    int(relative_size.y * 1080)
                ),
                Vec2
            )
        )

    @staticmethod
    def __absolute_to_relative(
            absolute_position: Vec2,
            absolute_size: Vec2
    ) -> tuple[Vec2, Vec2]:
        return (
            convert_coord(
                (
                    int(absolute_position.x / 1920),
                    int(absolute_position.y / 1080)
                ),
                Vec2
            ),
            convert_coord(
                (
                    int(absolute_size.x / 1920),
                    int(absolute_size.y / 1080)
                ),
                Vec2
            )
        )

    def __check_event(self, event: pg.Event | str) -> list[Callable[[], None]]:
        callbacks: list[Callable[[], None]] = []
        if self.__hover and self._visible or event == "mouse-leave" and self._visible:
            for ev in self.__events:
                if ev.check_event(event):
                    callbacks.append(lambda arg_ev=event, amogus_event=ev: amogus_event.raise_event(arg_ev))
        return callbacks

    def add_event(
            self,
            event_type: event_t,
            *_args: Any,
            button: int | None = None,
            key: int | None = None,
            callback: Callable[[pg.Event], Any] | None = None,
            sound: SoundEffect | None = None
    ) -> None:
        self.__events.append(AmogusEvent(event_type, *_args, button=button,
                                         key=key, callback=callback, sound=sound))

    def gl_draw(self) -> None:
        super().gl_draw()
        if self.__scaling:
            self.__abs_position, self.__abs_size = self.__relative_to_absolute(
                self.__rel_position,
                self.__rel_size
            )
        else:
            self.__rel_position, self.__rel_size = (
                self.__absolute_to_relative(self.__abs_position, self.__abs_size))

        self.__width = self.__abs_size.x
        self.__height = self.__abs_size.y

        if self.__anchor == "nw":
            self.__top_left = self.__abs_position
            self.__top_right = self.__abs_position + convert_coord((self.__abs_size.x, 0), Vec2)
            self.__bottom_left = self.__abs_position + convert_coord((0, self.__abs_size.y), Vec2)
            self.__bottom_right = self.__abs_position + self.__abs_size.y
        elif self.__anchor == "center":
            self.__top_left = self.__abs_position - self.__abs_size / 2
            self.__top_right = self.__abs_position + convert_coord((self.__abs_size.x / 2, -self.__abs_size.y / 2),
                                                                   Vec2)
            self.__bottom_left = self.__abs_position + convert_coord((-self.__abs_size.x / 2, self.__abs_size.y / 2),
                                                                     Vec2)
            self.__bottom_right = self.__abs_position + self.__abs_size / 2

        mouse_pos = pg.mouse.get_pos()
        mouse_pos = (mouse_pos[0] * 1920 / global_vars.screen_size_real.x,
                     mouse_pos[1] * 1080 / global_vars.screen_size_real.y)
        self.__hover = all([
            self._top_left.x <= mouse_pos[0] <= self._bottom_right.x,
            self._top_left.y <= mouse_pos[1] <= self._bottom_right.y
        ])

        callbacks = []
        if not self.__last_hover and self.__hover:
            callbacks = self.__check_event("mouse-enter")
        elif self.__last_hover and not self.__hover:
            callbacks = self.__check_event("mouse-leave")
        for cb in callbacks:
            cb()

        self.__last_hover = self.__hover

    @property
    def _abs_position(self) -> Vec2:
        """:return: Absolute position - anchor not factored in"""
        return self.__abs_position

    @property
    def _abs_size(self) -> Vec2:
        """:return: Absolute size"""
        return self.__abs_size

    @property
    def _rel_position(self) -> Vec2:
        """:return: Relative position - anchor not factored in"""
        return self.__rel_position

    @property
    def _rel_size(self) -> Vec2:
        """:return: Relative size"""
        return self.__rel_size

    @property
    def _width(self) -> float:
        """:return: Absolute width"""
        return self.__width

    @property
    def _height(self) -> float:
        """:return: Absolute height"""
        return self.__width

    @property
    def _anchor(self) -> anchor_t:
        """:return: Placement anchor"""
        return self.__anchor

    @property
    def _top_left(self) -> Vec2:
        """:return: Absolute top left"""
        return self.__top_left

    @property
    def _top_right(self) -> Vec2:
        """:return: Absolute top right"""
        return self.__top_right

    @property
    def _bottom_left(self) -> Vec2:
        """:return: Absolute bottom left"""
        return self.__bottom_left

    @property
    def _bottom_right(self) -> Vec2:
        """:return: Absolute bottom right"""
        return self.__bottom_right

    @property
    def _hover(self) -> bool:
        """:return: Is mouse hovering over this widget"""
        return self.__hover

    @property
    def _last_hover(self) -> bool:
        """:return: Was mouse hovering over this widget last frame"""
        return self.__last_hover


"""
        # check if mouse down
        mouse_left, *_ = pg.mouse.get_pressed()
        if self._hover and not self.__last_mouse and mouse_left and self.__command is not None:
            self.__command()

        self.__last_mouse = mouse_left
"""
