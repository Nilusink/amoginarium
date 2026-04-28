"""
amoginarium/logic/entities/_world/_islands.py
26. January 2024

an island in the sky

Author:
Nilusink, Lukas
"""

from __future__ import annotations

import typing as tp

from amoginarium.shared import IslandCIDs, CIDType

from ._base_island import Island


class GrassIsland(Island):
    _block_size = (64, 64)
    _CID = IslandCIDs.grass_island


class GrayBrickIsland(Island):
    _block_size = (24 * 3, 24 * 3)
    _CID = IslandCIDs.gray_brick_island


class GreenBrickIsland(Island):
    _block_size = (24 * 3, 24 * 3)
    _CID = IslandCIDs.green_brick_island


# class PillarIsland(Island):
#     _block_size = (64 * 3, 112 * 3)
#
#
# class PlatformIsland1(Island):
#     _block_size = (46 * 3, 13 * 3)
#
#
# class PlatformIsland2(Island):
#     _block_size = (44 * 3, 11 * 3)


__islands: tp.Iterable[tp.Type[Island]] = [
    GrassIsland,
    GrayBrickIsland,
    GreenBrickIsland
]

Island.ISLANDS: dict[CIDType, tp.Type[Island]] = {
    c.cid(): c for c in __islands
}
Island.ISLANDS_REVERSE = {v: k for k, v in Island.ISLANDS.items()}
