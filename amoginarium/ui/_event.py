"""
amoginarium/ui/_event.py

Project: amoginarium
"""

from __future__ import annotations

from typing import Callable, Any, Union
# noinspection PyPackageRequirements
import pygame as pg
from typing_extensions import Literal

from ..audio import SoundEffect

##################################################
#                     Code                       #
##################################################

event_t = Union[int, Literal["mouse-enter", "mouse-leave"]]


class AmogusEvent:
    __event_type: event_t
    __button: int
    __key: int

    __callback: Callable[[pg.Event | str], None] | None
    __sound: SoundEffect | None

    def __init__(
            self,
            event_type: event_t,
            *_args: Any,
            button: int | None = None,
            key: int | None = None,
            callback: Callable[[pg.Event | str], Any] | None = None,
            sound: SoundEffect | None = None
    ) -> None:
        self.__event_type = event_type
        self.__button = button
        self.__key = key
        self.__callback = callback
        self.__sound = sound

    def check_event(
            self,
            event: pg.Event | str
    ) -> bool:
        if isinstance(event, str):
            if event != self.__event_type:
                return False
        else:
            if self.__event_type != event.type:
                return False
            if self.__button is not None and self.__button != event.button:
                return False
            if self.__key is not None and self.__key != event.key:
                return False
        return True

    def raise_event(self, event: pg.Event | str) -> None:
        if self.__sound is not None:
            self.__sound.play()

        if self.__callback is not None:
            self.__callback(event)
