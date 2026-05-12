"""
amoginarium/logic/entities/_base/_debug/_debug_entity.py

Project: amoginarium
Created: 12.05.2026
Authors: LukasKrah
"""

from __future__ import annotations

from .._base_entities import PositionedLogicEntity
from .._groups import Updated


class DebugEntity(PositionedLogicEntity):
    def hide(self) -> None:
        super().hide()
        self.remove(Updated)

    def show(self) -> None:
        super().show()
        self.add(Updated)
