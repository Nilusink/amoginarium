"""
amoginarium/ui/_base_frame.py

Project: amoginarium
"""
from __future__ import annotations

from typing import Callable, Any

# noinspection PyPackageRequirements
import pygame as pg

from ..audio import SoundEffect
from ._event import AmogusEvent, event_t
from ._event_handler import EventHandler


class BaseFrame:
    """
    Base class for all UI elements
    """
    __visible: bool

    __events: list[AmogusEvent]

    def __init__(self) -> None:
        self.__visible = False

        self.__events = []
        EventHandler.add_check_events_callback(self.__check_event)

    def __check_event(self, event: pg.Event | str) -> None:
        if self._visible:
            for ev in self.__events:
                ev.check_event(event)

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

    def update(self) -> None:
        self.__visible = False

    def gl_draw(self) -> None:
        """
        Draw function
        """
        self.__visible = True

    @property
    def _visible(self) -> bool:
        return self.__visible
