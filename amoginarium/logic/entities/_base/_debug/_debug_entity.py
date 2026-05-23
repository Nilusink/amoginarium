"""
<Description>.

| ``Path``: amoginarium/logic/entities/_base/_debug/_debug_entity.py
| ``Project``: amoginarium
| ``Created``: 20.05.2026
| ``Authors``: LukasKrah
"""

from __future__ import annotations

import typing as tp

from .._base_entities import PositionedLogicEntity
from .._groups import Updated


class DebugEntity(PositionedLogicEntity):
    @tp.override
    def hide(self) -> None:
        super().hide()
        self.remove(Updated)

    @tp.override
    def show(self) -> None:
        super().show()
        self.add(Updated)
