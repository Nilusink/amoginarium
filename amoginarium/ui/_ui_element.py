"""
amoginarium/ui/_ui_element.py

Project: amoginarium
"""
from __future__ import annotations

from typing import Callable, Any

# noinspection PyPackageRequirements
import pygame as pg

from ..audio import SoundEffect
from ._event import AmogusEvent, event_t
from ._event_handler import EventHandler


class UIElement:
    """
    Base class for all UI elements
    """
    __visible: bool

    __events: list[AmogusEvent]

    _children: list[UIElement]

    def __init__(self) -> None:
        self.__visible = False

        self.__events = []
        self._children = []
        EventHandler.add_check_events_callback(self.__check_event)

    def __check_event(self, event: pg.Event | str) -> list[Callable[[], None]]:
        callbacks: list[Callable[[], None]] = []
        if self._visible:
            for ev in self.__events:
                if ev.check_event(event):
                    callbacks.append(lambda arg_ev=event, amogus_event=ev: amogus_event.raise_event(arg_ev))
        return callbacks

    def add_fullscreen_event(
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

    def hide(self) -> None:
        """
        Hide element
        """
        self.__visible = False
        for child in self._children:
            child.hide()

    def show(self) -> None:
        """
        Show element
        """
        self.__visible = True
        for child in self._children:
            child.show()

    def draw_if_visible(self) -> None:
        if self.__visible:
            self.gl_draw()

    def gl_draw(self) -> None:
        """
        Draw function
        """
        for widget in self._children:
            widget.gl_draw()

    @property
    def _visible(self) -> bool:
        return self.__visible
