"""
Manages UI element focus states and event callback registration.

Path: amoginarium/graphics/ui/_base/_focus.py
Project: amoginarium
Created: 11.04.2026
Authors: LukasKrah
"""

from __future__ import annotations

import abc
import typing as tp

if tp.TYPE_CHECKING:
    from ._ui_event_element import UIEventElement


class _SharedFocusStructure(abc.ABC): ...


class Focus(_SharedFocusStructure):
    __ui_entity: UIEventElement | None
    __on_focus_callbacks: tp.Final[list[tp.Callable[[], tp.Any]]]
    __on_unfocus_callbacks: tp.Final[list[tp.Callable[[], tp.Any]]]

    def __init__(self) -> None:
        self.__ui_entity = None
        self.__on_focus_callbacks = []
        self.__on_unfocus_callbacks = []

    def set(self, ui_entity: UIEventElement | None) -> None:
        self.__ui_entity = ui_entity

    def get(self) -> UIEventElement | None:
        return self.__ui_entity

    def is_focused(self, ui_entity: UIEventElement) -> bool:
        return self.__ui_entity is ui_entity

    def add_on_focus(self, callback: tp.Callable[[], tp.Any]) -> None:
        self.__on_focus_callbacks.append(callback)

    def add_on_unfocus(self, callback: tp.Callable[[], tp.Any]) -> None:
        self.__on_unfocus_callbacks.append(callback)


@tp.final
class _FocusHandler(_SharedFocusStructure):
    __focus_list: tp.Final[list[Focus]]

    def __init__(self) -> None:
        self.__focus_list = []

    def new_focus(self, focus: Focus | None) -> Focus:
        new_focus = focus if focus is not None else Focus()
        self.__focus_list.append(new_focus)
        return new_focus


FocusHandler: tp.Final[_FocusHandler] = _FocusHandler()
