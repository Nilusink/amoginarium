"""
Python functions for the map generator.

| Path: amoginarium/logic/map/_generator.py
| Project: amoginarium
| Created: 18.05.2026
| Authors: Nilusink
"""

from __future__ import annotations

import typing as tp

import numpy as np

if tp.TYPE_CHECKING:
    from numpy.typing import NDArray

_RNG: tp.Final[np.random.Generator] = np.random.default_rng()
LEFT: tp.Final[int] = 0
RIGHT: tp.Final[int] = 1
TOP: tp.Final[int] = 2
BOTTOM: tp.Final[int] = 3


def generate_chunk_noise(
    size: tuple[int, int],
    *,
    interfaces: list[int],
    slice_multiplier: float = 1.4,
    spawn_chunk: bool = False,
    x_stretch: int = 4,
) -> tuple[NDArray[np.float64], NDArray[np.bool_]]:
    """
    Generate chunk noise with interface positions.

    :param size: chunk size
    :param interfaces: interface directions
    :param slice_multiplier: multiplier for interface slices
    :param spawn_chunk: if set, center of chunk will always be cleared
    :param x_stretch: noise stretch in x-axis
    :return: white noise, spawn mask
    """
    mask = np.ones(size, dtype=np.bool)

    small: np.ndarray = _RNG.random((size[0] // x_stretch, size[1]))
    chunk = np.repeat(small, x_stretch, axis=0)

    # interface multiplier sizes
    x_start = int(size[0] / 5)
    x_mid = size[0] // 2
    x_end = size[0] - x_start

    y_start = int(size[1] / 5)
    y_mid = size[1] // 2
    y_end = size[1] - y_start

    # wall multiplier sizes
    x_wall_start = int(size[0] * 0.05)
    x_wall_end = size[0] - x_wall_start

    y_wall_start = int(size[1] * 0.05)
    y_wall_end = size[1] - y_wall_start

    # check which sides should be open
    if LEFT in interfaces:
        chunk[:x_mid, y_start:y_end] *= slice_multiplier

    else:
        chunk[:x_wall_start, :] = 0

    if RIGHT in interfaces:
        chunk[x_mid:, y_start:y_end] *= slice_multiplier

    else:
        chunk[x_wall_end:, :] = 0

    if TOP in interfaces:
        chunk[x_start:x_end, :y_mid] *= slice_multiplier

    else:
        chunk[:, :y_wall_start] = 0
        mask[:, : int(size[1] / 3)] = 0

    if BOTTOM in interfaces:
        chunk[x_start:x_end, y_mid:] *= slice_multiplier

    else:
        chunk[:, y_wall_end:] = 0

    # if spawn chunk, make sure the center is free of islands and turrets
    if spawn_chunk:
        chunk[x_mid - 5 : x_mid + 5, y_mid - 5 : y_mid + 5] = 1
        mask[x_start:x_end, y_start:y_end] = 0

    return chunk, mask
