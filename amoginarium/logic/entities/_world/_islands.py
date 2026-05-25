"""
An island in the sky.

| ``Path``: amoginarium/logic/entities/_world/_islands.py
| ``Project``: amoginarium
| ``Created``: 28.04.2026
| ``Authors``: Nilusink, LukasKrah
"""

from __future__ import annotations

import typing as tp

from amoginarium.shared import IslandCIDs

from ._base_island import Island

if tp.TYPE_CHECKING:
    from amoginarium.shared import CIDType


class GrassIsland(Island):
    __slots__ = ()
    _block_size: tp.ClassVar[tuple[int, int]] = (64, 64)
    _CID: tp.ClassVar[CIDType] = IslandCIDs.grass_island


class GrayBrickIsland(Island):
    __slots__ = ()
    _block_size: tp.ClassVar[tuple[int, int]] = (24 * 3, 24 * 3)
    _CID: tp.ClassVar[CIDType] = IslandCIDs.gray_brick_island


class GreenBrickIsland(Island):
    __slots__ = ()
    _block_size: tp.ClassVar[tuple[int, int]] = (24 * 3, 24 * 3)
    _CID: tp.ClassVar[CIDType] = IslandCIDs.green_brick_island


__islands: tp.Iterable[type[Island]] = [
    GrassIsland,
    GrayBrickIsland,
    GreenBrickIsland,
]

Island.ISLANDS: dict[CIDType, type[Island]] = {c.cid(): c for c in __islands}

Island._islands_reverse = {v: k for k, v in Island.ISLANDS.items()}  # noqa: SLF001
