"""
amoginarium/ui/_event_handler.py

Project: amoginarium
"""
from __future__ import annotations

from typing import Callable, Tuple, Any
# noinspection PyPackageRequirements
import pygame as pg

from amoginarium.audio import SoundEffect
from amoginarium.ui._event import AmogusEvent, event_t


##################################################
#                     Code                       #
##################################################

class _EventHandler:
    __check_events_callbacks: list[Callable[[pg.Event], None]]

    __events: list[AmogusEvent]

    def __init__(self) -> None:
        self.__check_events_callbacks = []
        self.__last_events = []
        self.__events = []

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

    def add_check_events_callback(self, callback: Callable[[pg.Event], None]) -> None:
        self.__check_events_callbacks.append(callback)

    def check_events(self) -> None:
        for event in pg.event.get():
            for ev in self.__events:
                ev.check_event(event)
            for callback in self.__check_events_callbacks:
                callback(event)


EventHandler = _EventHandler()
