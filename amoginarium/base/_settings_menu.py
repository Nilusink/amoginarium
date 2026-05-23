"""
UI component for managing display scaling and engine settings.

| Path: amoginarium/base/_settings_menu.py
| Project: amoginarium
| Created: 01.03.2026
| Authors: LukasKrah
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from amoginarium import pv
from amoginarium.graphics.render_bindings import renderer
from amoginarium.graphics.ui import UIButton, UIEntity, UIRectangle

if TYPE_CHECKING:
    from collections.abc import Callable


class SettingsMenu(UIEntity):
    __close_settings_callback: Callable[[], None]

    def __init__(self, close_settings_callback: Callable[[], None]) -> None:
        super().__init__()

        self.__close_settings_callback = close_settings_callback

        current_parent = UIRectangle(
            (0.5, 0.5),
            (0.2, 0.5),
            parent=self,
            bg_color=(70, 70, 70, 150),
            border_width=0,
        )

        padding = 0.06
        but_width = 1 - padding * 2
        but_height = (1 - padding * 5) / 4
        step = padding + but_height

        UIButton(
            (0.5, padding + but_height / 2),
            (but_width, but_height),
            "Bars",
            parent=current_parent,
            command=lambda: self.__set_scaling(0),
        )

        UIButton(
            (0.5, padding + but_height / 2 + step),
            (but_width, but_height),
            "Fixed ratio",
            parent=current_parent,
            command=lambda: self.__set_scaling(1),
        )

        UIButton(
            (0.5, padding + but_height / 2 + step * 2),
            (but_width, but_height),
            "Stretching",
            parent=current_parent,
            command=lambda: self.__set_scaling(2),
        )

        UIButton(
            (0.5, 1 - (padding + but_height / 2)),
            (but_width, but_height),
            "Back",
            parent=current_parent,
            command=self.__close_settings_callback,
        )

    def __set_scaling(self, value: int) -> None:
        pv.global_vars.set_scaling(value)
        renderer.display_update()
